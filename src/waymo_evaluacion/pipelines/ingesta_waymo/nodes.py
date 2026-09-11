"""
This is a boilerplate pipeline 'ingesta_waymo'
generated using Kedro 1.5.0
"""

import glob
from pathlib import Path
from typing import Callable

import pandas as pd

# Carpeta de camera_to_lidar_box_association: no tiene entrada propia en el
# catalogo (a diferencia de waymo_lidar_box_raw), asi que se lee con glob
# directo, tal como se lee lidar_box a traves del PartitionedDataset: sin
# asumir de antemano cuantos segmentos hay ni sus segment_id.
RUTA_ASOCIACION = Path("data/01_raw/waymo/camera_to_lidar_box_association")

# Llave del join estricto por frame: exige que la camara haya visto el
# mismo objeto, en el mismo segmento, en el mismo instante exacto.
LLAVE_JOIN = ["key.segment_context_name", "key.frame_timestamp_micros", "key.laser_object_id"]

# [LiDARBoxComponent].type: 1=vehicle, 2=pedestrian, 3=sign, 4=cyclist
# (ver notebooks/02_exploracion_waymo.ipynb, seccion 2).
TYPE_CYCLIST = 4

# Balance reportado en la exploracion original de Colab, calculado con un
# join por objeto (key.laser_object_id, ignorando el frame): si el objeto
# fue visto por camara en CUALQUIER instante del segmento, todas sus filas
# quedan marcadas como positivas. Se deja como referencia documentada, no
# como verdad de terreno. El join estricto por frame que implementa
# construir_target_binario dara numeros mas bajos a proposito: exige que la
# camara haya visto ese objeto en ese instante exacto, no en cualquier
# instante del segmento, para no filtrar informacion de otros frames hacia
# el target de un frame puntual (ver notebooks/02_exploracion_waymo.ipynb,
# seccion 3, "Nota importante").
BALANCE_COLAB_REFERENCIA_POR_OBJETO = {
    "10023947602400723454_1120_000_1140_000": 0.324,
    "10206293520369375008_2796_800_2816_800": 0.101,
    "11017034898130016754_697_830_717_830": 0.061,
    "6791933003490312185_2607_000_2627_000": 0.024,
}


def cargar_segmentos_waymo(
    waymo_lidar_box_raw: dict[str, Callable[[], pd.DataFrame]],
    metadata_segmentos: dict[str, dict[str, str]],
) -> pd.DataFrame:
    """
    Carga y concatena los parquet de lidar_box descubiertos por Kedro.

    waymo_lidar_box_raw llega como un PartitionedDataset: un diccionario
    {nombre_de_archivo: funcion_de_carga}, uno por cada parquet que Kedro
    encontro en data/01_raw/waymo/lidar_box/, sin que este nodo (ni el
    catalogo) tengan que enumerar los segment_id a mano. Por cada partición
    se identifica el segmento a partir de la propia columna
    key.segment_context_name (no del nombre de archivo) y se le adjuntan
    weather, time_of_day y location desde metadata_segmentos: esos 3
    atributos no existen en los archivos de Waymo, son metadato de
    segmento completo documentado aparte (ver
    notebooks/02_exploracion_waymo.ipynb, seccion 1).
    """
    segmentos = []
    for nombre_particion, cargar in sorted(waymo_lidar_box_raw.items()):
        df = cargar()
        segment_id = df["key.segment_context_name"].iloc[0]
        metadata = metadata_segmentos.get(segment_id, {})
        df = df.assign(
            segment_id=segment_id,
            weather=metadata.get("weather"),
            time_of_day=metadata.get("time_of_day"),
            location=metadata.get("location"),
        )
        segmentos.append(df)

    lidar_box = pd.concat(segmentos, ignore_index=True)

    print(f"Segmentos encontrados: {len(segmentos)}")
    print(f"Filas totales: {len(lidar_box):,}")
    print("Filas por segmento:")
    for segment_id, grupo in lidar_box.groupby("segment_id"):
        print(f"  {segment_id}: {len(grupo):,}")
    print(f"Columnas ({lidar_box.shape[1]}): {list(lidar_box.columns)}")

    return lidar_box


def construir_target_binario(waymo_lidar_box_con_metadata: pd.DataFrame) -> pd.DataFrame:
    """
    Cruza lidar_box con camera_to_lidar_box_association y arma tiene_camara.

    Lee dinamicamente todos los parquet de
    data/01_raw/waymo/camera_to_lidar_box_association/ (sin asumir cuantos
    segmentos hay), deduplica esa tabla por LLAVE_JOIN porque una misma
    detección puede haber sido vista por mas de una camara, y hace un left
    join contra lidar_box usando esas mismas 3 columnas como llave: mismo
    segmento, mismo instante, mismo objeto. tiene_camara queda en 1 donde
    hubo match y en 0 donde no.

    El balance resultante no coincide con el que se habia reportado como
    validado en la exploracion de Colab (ver
    BALANCE_COLAB_REFERENCIA_POR_OBJETO): esa referencia usa un join mas
    laxo, solo por objeto, que tiene fuga de informacion hacia otros
    instantes del mismo objeto. La funcion imprime ambos numeros lado a
    lado para dejar la diferencia documentada en cada corrida, no oculta.
    """
    rutas_asociacion = sorted(glob.glob(str(RUTA_ASOCIACION / "*.parquet")))
    asociacion = pd.concat((pd.read_parquet(ruta) for ruta in rutas_asociacion), ignore_index=True)
    asociacion_dedup = asociacion.drop_duplicates(subset=LLAVE_JOIN)

    df = waymo_lidar_box_con_metadata.merge(
        asociacion_dedup[LLAVE_JOIN].assign(tiene_camara=1),
        on=LLAVE_JOIN,
        how="left",
    )
    df["tiene_camara"] = df["tiene_camara"].fillna(0).astype(int)

    print("Balance de tiene_camara por segmento (join estricto por frame):")
    for segment_id, grupo in df.groupby("segment_id"):
        con_camara = int(grupo["tiene_camara"].sum())
        total = len(grupo)
        pct = con_camara / total
        referencia = BALANCE_COLAB_REFERENCIA_POR_OBJETO.get(segment_id)
        linea = f"  {segment_id}: con_camara={con_camara} sin_camara={total - con_camara} pct={pct:.1%}"
        if referencia is not None:
            linea += f" | referencia Colab (join por objeto): {referencia:.1%}"
        print(linea)

    total_con_camara = int(df["tiene_camara"].sum())
    print(f"TOTAL: filas={len(df):,} con_camara={total_con_camara:,} pct={total_con_camara / len(df):.1%}")

    return df


def resumen_ingesta_waymo(waymo_con_target: pd.DataFrame) -> pd.DataFrame:
    """
    Arma la tabla resumen por segmento de la ingesta de datos reales de Waymo.

    Por cada segment_id junta su metadato (weather, time_of_day, location)
    con el volumen de detecciones, el balance del target tiene_camara y la
    proporcion de detecciones de tipo CYCLIST ([LiDARBoxComponent].type=4),
    la clase mas vulnerable y la mas minoritaria (ver
    notebooks/02_exploracion_waymo.ipynb, seccion 2).
    """
    filas = []
    for segment_id, grupo in waymo_con_target.groupby("segment_id"):
        n_detecciones = len(grupo)
        n_positivos = int(grupo["tiene_camara"].sum())
        filas.append(
            {
                "segment_id": segment_id,
                "weather": grupo["weather"].iloc[0],
                "time_of_day": grupo["time_of_day"].iloc[0],
                "location": grupo["location"].iloc[0],
                "n_detecciones": n_detecciones,
                "n_positivos": n_positivos,
                "pct_positivos": n_positivos / n_detecciones,
                "pct_cyclist": (grupo["[LiDARBoxComponent].type"] == TYPE_CYCLIST).mean(),
            }
        )

    resumen = pd.DataFrame(filas)

    print("Resumen de ingesta Waymo:")
    print(resumen.to_string(index=False))

    return resumen
