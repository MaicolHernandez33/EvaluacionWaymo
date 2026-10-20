"""
Pipeline 'ingesta_waymo' (EP2).

Carga los segmentos reales de Waymo listados en parameters_ingesta_waymo.yml
(bloque segmentos_ep2), arma el target binario tiene_camara y filtra los
frames sin etiquetas de camara.

Reglas que aplica este pipeline (ver docs/seleccion_segmentos/):
- Solo se leen los segmentos de la lista del YAML, no todo lo que haya en la
  carpeta: los archivos viejos de EP1 que el criterio de etiquetado denso
  rechazo (p. ej. 11017034...) se ignoran.
- Segmentos "supervisado": tienen target tiene_camara (0/1).
- Segmentos "solo_clustering" (lluvia): NO tienen target (queda en NA). Sus
  asociaciones estan vacias o con ~1 etiqueta por frame, asi que un 0 no
  significaria "la camara no lo vio" sino "no hay etiqueta".
- Dentro de un segmento supervisado, un frame sin ningun positivo se
  considera sin etiquetar y se descarta de waymo_supervisado.
"""

import glob
import logging
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from ..preprocesamiento.nodes import crear_variables_derivadas

logger = logging.getLogger(__name__)

# Llave del join estricto por frame: exige que la camara haya visto el
# mismo objeto, en el mismo segmento, en el mismo instante exacto.
LLAVE_JOIN = ["key.segment_context_name", "key.frame_timestamp_micros", "key.laser_object_id"]
COL_SEGMENTO, COL_FRAME = LLAVE_JOIN[0], LLAVE_JOIN[1]

# Modo anterior (EP1) de construir_target_binario: sin argumentos de asociacion, lee todos los parquet de esta carpeta.
RUTA_ASOCIACION = Path("data/01_raw/waymo/camera_to_lidar_box_association")
TYPE_CYCLIST = 4

USO_SUPERVISADO = "supervisado"
USO_CLUSTERING = "solo_clustering"

# [LiDARBoxComponent].type: 1=vehicle, 2=pedestrian, 3=sign, 4=cyclist
# (ver notebooks/02_exploracion_waymo.ipynb, seccion 2).
TIPOS_OBJETO = {1: "VEHICLE", 2: "PEDESTRIAN", 3: "SIGN", 4: "CYCLIST"}

# Balance reportado en la exploracion original de Colab, calculado con un
# join POR OBJETO (key.laser_object_id, ignorando el frame): si el objeto fue
# visto por camara en cualquier instante del segmento, todas sus filas quedan
# positivas. Es un join laxo, con fuga de informacion entre frames: se deja
# solo como referencia documentada. Las cifras del README deben usar el join
# estricto por frame que implementa construir_target_binario.
BALANCE_COLAB_REFERENCIA_POR_OBJETO = {
    "10023947602400723454_1120_000_1140_000": 0.324,
    "10206293520369375008_2796_800_2816_800": 0.101,
    "11017034898130016754_697_830_717_830": 0.061,
    "6791933003490312185_2607_000_2627_000": 0.024,
}


def _id_segmento(nombre_particion: str) -> str:
    """El id de particion de un PartitionedDataset es el nombre del archivo (con o sin .parquet)."""
    return Path(nombre_particion).stem


def _columna(df: pd.DataFrame, sufijo: str, obligatoria: bool = True) -> str | None:
    """
    Busca la unica columna que termina en `sufijo`.

    Las columnas de lidar_box llevan prefijo '[LiDARBoxComponent].'; se buscan
    por sufijo para no depender de el. Si no la encuentra (o hay mas de una),
    el error dice que columnas hay, para corregirlo rapido.
    """
    candidatas = [c for c in df.columns if c.endswith(sufijo)]
    if len(candidatas) == 1:
        return candidatas[0]
    if not candidatas and not obligatoria:
        return None
    raise KeyError(
        f"Se esperaba 1 columna que termine en '{sufijo}' y hay {candidatas}. "
        f"Columnas disponibles: {list(df.columns)}"
    )


def _inventario_a_df(inventario) -> pd.DataFrame:
    """Acepta el inventario como DataFrame o como dict {segment_id: {weather, time_of_day, location}}."""
    if isinstance(inventario, pd.DataFrame):
        return inventario
    return pd.DataFrame.from_dict(inventario, orient="index").rename_axis("segment_id").reset_index()


def _cargar_todas_las_particiones(waymo_lidar_box_raw, inventario_segmentos) -> pd.DataFrame:
    """Modo anterior: concatena todas las particiones y adjunta el metadato por segment_id."""
    inventario = _inventario_a_df(inventario_segmentos).set_index("segment_id")
    segmentos = []
    for _, cargar in sorted(waymo_lidar_box_raw.items()):
        df = cargar()
        segment_id = df[COL_SEGMENTO].iloc[0]
        fila = inventario.loc[segment_id] if segment_id in inventario.index else {}
        segmentos.append(
            df.assign(
                segment_id=segment_id,
                weather=fila.get("weather"),
                time_of_day=fila.get("time_of_day"),
                location=fila.get("location"),
            )
        )
    lidar_box = pd.concat(segmentos, ignore_index=True)
    print(f"Segmentos encontrados: {len(segmentos)} | filas totales: {len(lidar_box):,}")
    return lidar_box


def cargar_segmentos_waymo(
    waymo_lidar_box_raw: dict[str, Callable[[], pd.DataFrame]],
    inventario_segmentos: pd.DataFrame | dict[str, dict[str, str]],
    segmentos_supervisado: list[str] | None = None,
    segmentos_solo_clustering: list[str] | None = None,
) -> pd.DataFrame:
    """
    Carga y concatena SOLO los lidar_box listados en el YAML.

    waymo_lidar_box_raw es un PartitionedDataset: {id_particion: funcion_de_carga}.
    Como la carga es perezosa, los archivos que no estan en la lista (p. ej.
    segmentos de EP1 ya descartados) nunca se leen. Falla con un mensaje claro
    si un segmento listado no tiene archivo.

    weather, time_of_day y location no existen en los archivos de Waymo: se
    adjuntan desde inventario_segmentos (docs/seleccion_segmentos/
    inventario_segmentos.csv, generado por el notebook 00b a partir de 'stats').
    Se agrega ademas la columna 'uso' (supervisado / solo_clustering).

    Compatibilidad con el comportamiento anterior (EP1): si NO se pasa ninguna de las
    dos listas (valores por defecto None), se cargan todas las particiones que haya, el
    segment_id se toma de la columna key.segment_context_name y no se agrega la columna
    'uso'. En ese modo `inventario_segmentos` puede ser un dict {segment_id: {weather,
    time_of_day, location}} (como el antiguo metadata_segmentos) o un DataFrame.
    """
    if segmentos_supervisado is None and segmentos_solo_clustering is None:
        return _cargar_todas_las_particiones(waymo_lidar_box_raw, inventario_segmentos)
    segmentos_supervisado = list(segmentos_supervisado or [])
    segmentos_solo_clustering = list(segmentos_solo_clustering or [])
    repetidos = sorted(set(segmentos_supervisado) & set(segmentos_solo_clustering))
    if repetidos:
        raise ValueError(f"Segmentos presentes en ambas listas del YAML: {repetidos}")

    uso = {s: USO_SUPERVISADO for s in segmentos_supervisado}
    uso.update({s: USO_CLUSTERING for s in segmentos_solo_clustering})

    particiones = {_id_segmento(nombre): cargar for nombre, cargar in waymo_lidar_box_raw.items()}

    faltantes = sorted(set(uso) - set(particiones))
    if faltantes:
        raise FileNotFoundError(
            f"Faltan {len(faltantes)} archivos de lidar_box listados en el YAML "
            f"(revisar data/01_raw/waymo/lidar_box/): {faltantes}"
        )
    ignorados = sorted(set(particiones) - set(uso))
    if ignorados:
        logger.warning(
            "Se ignoran %d archivos de lidar_box que no estan en la lista de segmentos: %s",
            len(ignorados), ignorados,
        )

    metadata = _inventario_a_df(inventario_segmentos).set_index("segment_id")
    sin_metadata = sorted(set(uso) - set(metadata.index))
    if sin_metadata:
        raise KeyError(f"Segmentos sin weather/time_of_day/location en el inventario: {sin_metadata}")

    segmentos = []
    for segment_id in sorted(uso):
        df = particiones[segment_id]()
        ids_en_archivo = list(df[COL_SEGMENTO].unique())
        if ids_en_archivo != [segment_id]:
            raise ValueError(
                f"El archivo '{segment_id}' contiene segmentos {ids_en_archivo}: no coincide con su nombre."
            )
        segmentos.append(
            df.assign(
                segment_id=segment_id,
                uso=uso[segment_id],
                weather=metadata.at[segment_id, "weather"],
                time_of_day=metadata.at[segment_id, "time_of_day"],
                location=metadata.at[segment_id, "location"],
            )
        )

    lidar_box = pd.concat(segmentos, ignore_index=True)

    print(f"Segmentos cargados: {len(segmentos)} "
          f"({len(segmentos_supervisado)} supervisado, {len(segmentos_solo_clustering)} solo_clustering)")
    print(f"Filas totales: {len(lidar_box):,} | columnas: {lidar_box.shape[1]}")
    return lidar_box


def crear_variables_waymo(waymo_lidar_box_con_metadata: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega nombres estandar y variables derivadas, sin quitar columnas.

    Los nombres estandar (box_center_x, box_length, num_lidar_points, ...) son
    los mismos del CSV sintetico de EP1, para poder reutilizar
    crear_variables_derivadas del pipeline preprocesamiento (distancia_m,
    volumen_caja, densidad_puntos) y comparar ambas fuentes.

    Ninguna variable proviene de la camara ni del target: no hay fuga.
    key.laser_object_id y key.frame_timestamp_micros son identificadores, no
    deben usarse como features del modelo.
    """
    df = waymo_lidar_box_con_metadata.copy()

    estandar = {
        "box_center_x": "box.center.x",
        "box_center_y": "box.center.y",
        "box_center_z": "box.center.z",
        "box_length": "box.size.x",
        "box_width": "box.size.y",
        "box_height": "box.size.z",
        "num_lidar_points": "num_lidar_points_in_box",
    }
    for nombre, sufijo in estandar.items():
        df[nombre] = df[_columna(df, sufijo)]

    col_tipo = _columna(df, "].type")
    df["object_type"] = df[col_tipo].map(TIPOS_OBJETO)
    n_desconocidos = int(df["object_type"].isna().sum())
    if n_desconocidos:
        logger.warning("%d filas con un codigo de tipo fuera de %s", n_desconocidos, TIPOS_OBJETO)

    # Velocidad: opcional (depende de las columnas del parquet).
    vel_x, vel_y = _columna(df, "speed.x", False), _columna(df, "speed.y", False)
    if vel_x and vel_y:
        df["speed_mps"] = np.hypot(df[vel_x], df[vel_y])

    df = crear_variables_derivadas(df)
    df["densidad_puntos"] = df["densidad_puntos"].replace([np.inf, -np.inf], np.nan)
    return df


def _construir_target_todas_las_asociaciones(waymo_con_variables: pd.DataFrame) -> pd.DataFrame:
    """Modo anterior: lee todos los parquet de asociacion de RUTA_ASOCIACION y cruza por frame."""
    rutas = sorted(glob.glob(str(RUTA_ASOCIACION / "*.parquet")))
    asociacion = pd.concat((pd.read_parquet(ruta) for ruta in rutas), ignore_index=True)
    asociacion_dedup = asociacion.drop_duplicates(subset=LLAVE_JOIN)
    df = waymo_con_variables.merge(asociacion_dedup[LLAVE_JOIN].assign(tiene_camara=1), on=LLAVE_JOIN, how="left")
    df["tiene_camara"] = df["tiene_camara"].fillna(0).astype(int)
    print(f"tiene_camara (modo anterior, join estricto por frame): {int(df['tiene_camara'].sum()):,} positivos de {len(df):,} filas")
    return df


def construir_target_binario(
    waymo_con_variables: pd.DataFrame,
    waymo_asociacion_raw: dict[str, Callable[[], pd.DataFrame]] | None = None,
    segmentos_supervisado: list[str] | None = None,
) -> pd.DataFrame:
    """
    Arma tiene_camara cruzando lidar_box con camera_to_lidar_box_association.

    - Solo lee las asociaciones de los segmentos supervisados.
    - Deduplica por LLAVE_JOIN: una misma deteccion puede ser vista por mas de
      una camara.
    - Left join estricto por frame: tiene_camara=1 si hubo match, 0 si no.
    - Segmentos solo_clustering: tiene_camara queda en NA (no hay etiquetas
      confiables; un 0 seria falso).
    - frame_etiquetado=True en los frames de un segmento supervisado que tienen
      al menos un positivo. Un frame sin ningun positivo se considera sin
      etiquetar (con decenas de objetos por frame es muy improbable que la
      camara no confirme ninguno).

    Compatibilidad con el comportamiento anterior (EP1): si `waymo_asociacion_raw` es
    None (valor por defecto), se leen todos los parquet de RUTA_ASOCIACION, se
    deduplica por LLAVE_JOIN y se hace el left join sobre todas las filas, sin columnas
    'uso' ni 'frame_etiquetado'. Si se pasa `waymo_asociacion_raw` pero no
    `segmentos_supervisado`, se consideran supervisados todos los segmentos de la tabla.
    """
    if waymo_asociacion_raw is None:
        return _construir_target_todas_las_asociaciones(waymo_con_variables)
    if segmentos_supervisado is None:
        segmentos_supervisado = sorted(waymo_con_variables["segment_id"].unique())
    df = waymo_con_variables

    particiones = {_id_segmento(nombre): cargar for nombre, cargar in waymo_asociacion_raw.items()}
    faltantes = sorted(set(segmentos_supervisado) - set(particiones))
    if faltantes:
        raise FileNotFoundError(
            f"Faltan {len(faltantes)} archivos de asociacion de segmentos supervisados "
            f"(revisar data/01_raw/waymo/camera_to_lidar_box_association/): {faltantes}"
        )

    asociacion = pd.concat(
        (particiones[s]()[LLAVE_JOIN] for s in sorted(segmentos_supervisado)),
        ignore_index=True,
    )
    asociacion_dedup = asociacion.drop_duplicates(subset=LLAVE_JOIN).assign(tiene_camara=1.0)

    es_supervisado = df["segment_id"].isin(segmentos_supervisado)
    supervisado = df[es_supervisado].merge(asociacion_dedup, on=LLAVE_JOIN, how="left")
    supervisado["tiene_camara"] = supervisado["tiene_camara"].fillna(0.0)
    clustering = df[~es_supervisado].assign(tiene_camara=np.nan)
    resultado = pd.concat([supervisado, clustering], ignore_index=True)

    positivos_por_frame = resultado.groupby(["segment_id", COL_FRAME])["tiene_camara"].transform("max")
    resultado["frame_etiquetado"] = positivos_por_frame.fillna(0.0) > 0
    resultado["tiene_camara"] = resultado["tiene_camara"].astype("Int8")

    print("Balance de tiene_camara por segmento supervisado (join estricto por frame):")
    for segment_id, grupo in resultado[resultado["uso"] == USO_SUPERVISADO].groupby("segment_id"):
        con_camara = int(grupo["tiene_camara"].sum())
        linea = f"  {segment_id}: positivos={con_camara:,} de {len(grupo):,} ({con_camara / len(grupo):.1%})"
        referencia = BALANCE_COLAB_REFERENCIA_POR_OBJETO.get(segment_id)
        if referencia is not None:
            linea += f" | referencia Colab (join por objeto, laxo): {referencia:.1%}"
        print(linea)
        if con_camara == 0:
            logger.warning("El segmento supervisado %s no tiene ningun positivo tras el cruce", segment_id)

    return resultado


def filtrar_frames_etiquetados(waymo_con_target: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Deja solo los frames etiquetados de los segmentos supervisados.

    En varios segmentos las etiquetas de camara existen solo en parte de los
    frames (p. ej. el primer tercio del segmento no tiene ninguna). Los objetos
    de esos frames quedarian con tiene_camara=0 por falta de etiqueta y no
    porque la camara no los viera. Se descartan; todos los positivos se
    conservan por construccion.

    Devuelve (waymo_supervisado, reporte_filtro_frames). El reporte incluye
    la tasa de positivos antes y despues del filtro: la tasa 'despues' debe
    coincidir con tasa_frames_etiq de segmentos_ep2.csv (notebook 00b).
    """
    supervisado = waymo_con_target[waymo_con_target["uso"] == USO_SUPERVISADO].copy()
    supervisado["tiene_camara"] = supervisado["tiene_camara"].astype(int)
    conservado = supervisado[supervisado["frame_etiquetado"]].copy()

    antes = supervisado.groupby("segment_id").agg(
        filas_antes=("tiene_camara", "size"),
        positivos=("tiene_camara", "sum"),
        frames_antes=(COL_FRAME, "nunique"),
    )
    despues = conservado.groupby("segment_id").agg(
        filas_despues=("tiene_camara", "size"),
        frames_despues=(COL_FRAME, "nunique"),
    )
    reporte = antes.join(despues).fillna(0).astype(int)
    reporte["pct_filas_conservadas"] = (reporte["filas_despues"] / reporte["filas_antes"] * 100).round(1)
    reporte["tasa_antes_pct"] = (reporte["positivos"] / reporte["filas_antes"] * 100).round(2)
    reporte["tasa_despues_pct"] = (
        reporte["positivos"] / reporte["filas_despues"].where(reporte["filas_despues"] > 0) * 100
    ).round(2)
    reporte = reporte.reset_index()

    total_antes, total_despues = len(supervisado), len(conservado)
    positivos = int(supervisado["tiene_camara"].sum())
    print(f"Filas supervisadas: {total_antes:,} -> {total_despues:,} tras filtrar frames sin etiquetas "
          f"({total_despues / total_antes:.1%} conservadas)")
    print(f"Positivos: {positivos:,} (todos conservados) | tasa antes {positivos / total_antes:.2%} "
          f"-> despues {positivos / total_despues:.2%}")

    return conservado.reset_index(drop=True), reporte


def _es_ciclista(df: pd.DataFrame) -> pd.Series:
    """CYCLIST segun object_type (si existe) o segun el codigo crudo de [LiDARBoxComponent].type (4)."""
    if "object_type" in df.columns:
        return df["object_type"] == "CYCLIST"
    return df[_columna(df, "].type")] == TYPE_CYCLIST


def resumen_ingesta_waymo(waymo_con_target: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla resumen por segmento: metadato, uso, volumen, target y clase CYCLIST.

    Para segmentos solo_clustering, n_positivos y pct_positivos quedan en NaN
    (no hay target). pct_frames_etiquetados mide la cobertura de etiquetas
    dentro de cada segmento supervisado.
    """
    filas = []
    for segment_id, grupo in waymo_con_target.groupby("segment_id"):
        es_supervisado = ("uso" not in grupo.columns) or grupo["uso"].iloc[0] == USO_SUPERVISADO
        n_detecciones = len(grupo)
        n_frames = grupo[COL_FRAME].nunique() if COL_FRAME in grupo.columns else np.nan
        n_positivos = int(grupo["tiene_camara"].sum()) if es_supervisado else np.nan
        filas.append(
            {
                "segment_id": segment_id,
                "uso": grupo["uso"].iloc[0] if "uso" in grupo.columns else USO_SUPERVISADO,
                "weather": grupo["weather"].iloc[0],
                "time_of_day": grupo["time_of_day"].iloc[0],
                "location": grupo["location"].iloc[0],
                "n_frames": n_frames,
                "n_detecciones": n_detecciones,
                "n_positivos": n_positivos,
                "pct_positivos": n_positivos / n_detecciones if es_supervisado else np.nan,
                "pct_frames_etiquetados": (
                    grupo.loc[grupo["frame_etiquetado"], COL_FRAME].nunique() / n_frames
                    if es_supervisado and "frame_etiquetado" in grupo.columns and COL_FRAME in grupo.columns else np.nan
                ),
                "pct_cyclist": _es_ciclista(grupo).mean(),
            }
        )

    resumen = pd.DataFrame(filas)
    print("Resumen de ingesta Waymo:")
    print(resumen.to_string(index=False))
    return resumen
