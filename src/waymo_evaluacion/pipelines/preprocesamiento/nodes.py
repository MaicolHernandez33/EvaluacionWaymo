"""
This is a boilerplate pipeline 'preprocesamiento'
generated using Kedro 1.5.0
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def convertir_nulos_ocultos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte a NaN explicito los dos nulos ocultos de la seccion 3 del
    notebook 01_exploracion_csv.

    timestamp_micros: el texto "N/D" (60 filas, 0,15%) pasa a NaN y la
    columna queda casteada a numerico.
    num_lidar_points: el centinela -1 (1.198 filas, 2,94%) pasa a NaN.
    """
    df = df.copy()
    df["timestamp_micros"] = df["timestamp_micros"].replace("N/D", np.nan)
    df["timestamp_micros"] = pd.to_numeric(df["timestamp_micros"], errors="coerce")
    df["num_lidar_points"] = df["num_lidar_points"].replace(-1, np.nan)
    return df


def normalizar_categorias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza las etiquetas inconsistentes de object_type y weather.

    object_type: 2.343 filas con variantes de mayuscula o en espanol (Ped,
    Pedestrian, PEATON) se unifican en PEDESTRIAN.
    weather: 10.806 filas con variantes de mayuscula, espacio inicial o en
    espanol (Sunny, SUNNY, soleado, RAIN, " rain", lluvia, Fog, niebla) se
    normalizan a minuscula sin espacios. fog se mantiene como categoria
    propia: no se fuerza a sunny ni a rain (ver seccion 7 del notebook).
    """
    df = df.copy()
    object_type_map = {"PED": "PEDESTRIAN", "PEATON": "PEDESTRIAN"}
    df["object_type"] = df["object_type"].str.strip().str.upper().replace(object_type_map)

    weather_map = {"soleado": "sunny", "lluvia": "rain", "niebla": "fog"}
    df["weather"] = df["weather"].str.strip().str.lower().replace(weather_map)
    return df


def eliminar_columnas_sin_varianza(
    df: pd.DataFrame,
    columnas_protegidas: list[str] | None = None,
) -> pd.DataFrame:
    """
    Elimina columnas con un solo valor unico en todo el dataset.

    Generica: no asume que la columna se llama sensor_version, detecta
    cualquier columna sin varianza. En detecciones_crudas afecta a 1 columna
    (sensor_version, un unico valor v2.0.1 en las 40.680 filas).

    columnas_protegidas existe porque esta funcion se va a reutilizar sobre
    los datos reales de Waymo, donde weather puede venir 100% sunny para un
    segmento asoleado real, no por un defecto. Sin proteccion, la funcion
    borraria esa columna en silencio solo porque en ese subconjunto no varia.
    Se pasan ["weather", "time_of_day"] para que nunca se eliminen aunque su
    varianza caiga a 0 en algun corte de datos.
    """
    df = df.copy()
    protegidas = set(columnas_protegidas or [])
    sin_varianza = [
        c for c in df.columns
        if c not in protegidas and df[c].nunique(dropna=True) <= 1
    ]
    if sin_varianza:
        logger.info("Columnas sin varianza eliminadas: %s", sin_varianza)
    return df.drop(columns=sin_varianza)


def eliminar_duplicados_logicos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina las filas duplicadas segun el criterio logico de la seccion 4
    del notebook 01_exploracion_csv.

    subset=[segment_id, timestamp_micros, id_interno], keep="first". Afecta
    a 680 filas (480 duplicados exactos mas 200 pares con lecturas de sensor
    levemente distintas bajo el mismo identificador).
    """
    df = df.copy()
    subset = ["segment_id", "timestamp_micros", "id_interno"]
    return df.drop_duplicates(subset=subset, keep="first")


def filtrar_valores_imposibles(
    df: pd.DataFrame,
    altura_max: float,
    velocidad_max: float,
) -> pd.DataFrame:
    """
    Elimina dimensiones imposibles y marca velocidades imposibles.

    Elimina box_length <= 0 (80 filas) y box_height <= 0 (122 filas), sin
    superposicion entre ambos grupos. Elimina box_height > altura_max (0
    filas hoy, filtro preventivo). Convierte speed_mps > velocidad_max a NaN
    (157 filas), sin eliminar la fila: el resto de esas detecciones es
    valido.
    No aplica ningun filtro por IQR ni por desviacion estandar sobre
    box_length: las 608 filas de VEHICLE con box_length > 10 m son buses y
    camiones reales, con ancho y alto coherentes, y se conservan (ver
    seccion 5 y seccion 7 del notebook).
    """
    df = df.copy()
    df = df[df["box_length"] > 0]
    df = df[df["box_height"] > 0]
    df = df[df["box_height"] <= altura_max]
    df = df.copy()
    df.loc[df["speed_mps"] > velocidad_max, "speed_mps"] = np.nan
    return df


def crear_variables_derivadas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega 3 variables derivadas, sin eliminar ni modificar columnas
    existentes.

    distancia_m: distancia euclidiana al sensor, la misma que se usa en la
    seccion 6 del notebook para explicar la caida de num_lidar_points con la
    distancia.
    volumen_caja: box_length x box_width x box_height.
    densidad_puntos: num_lidar_points / volumen_caja, puntos LiDAR por metro
    cubico de caja.

    Debe ejecutarse despues de filtrar_valores_imposibles: densidad_puntos
    divide por volumen_caja, y esa division solo es segura si ya se
    eliminaron las filas con box_height en cero (y por lo tanto
    volumen_caja en cero).
    """
    df = df.copy()
    df["distancia_m"] = np.sqrt(df["box_center_x"] ** 2 + df["box_center_y"] ** 2)
    df["volumen_caja"] = df["box_length"] * df["box_width"] * df["box_height"]
    df["densidad_puntos"] = df["num_lidar_points"] / df["volumen_caja"]
    return df


def resumen_calidad(df_crudo: pd.DataFrame, df_limpio: pd.DataFrame) -> pd.DataFrame:
    """
    Arma la tabla comparativa de calidad entre el dataset crudo y el limpio.

    Reproduce las metricas de la seccion 9 del notebook 01_exploracion_csv:
    filas, columnas, categorias de object_type y weather, duplicados
    logicos, nulos totales y filas con box_length > 10 m (buses y camiones
    reales que deben seguir presentes despues de la limpieza).
    """

    def _duplicados_logicos(df: pd.DataFrame) -> int:
        subset = [c for c in ["segment_id", "timestamp_micros", "id_interno"] if c in df.columns]
        return int(df.duplicated(subset=subset).sum())

    metricas = {
        "filas": (len(df_crudo), len(df_limpio)),
        "columnas": (df_crudo.shape[1], df_limpio.shape[1]),
        "categorias_object_type": (
            int(df_crudo["object_type"].nunique(dropna=True)),
            int(df_limpio["object_type"].nunique(dropna=True)),
        ),
        "categorias_weather": (
            int(df_crudo["weather"].nunique(dropna=True)),
            int(df_limpio["weather"].nunique(dropna=True)),
        ),
        "duplicados_logicos": (
            _duplicados_logicos(df_crudo),
            _duplicados_logicos(df_limpio),
        ),
        "nulos_totales": (
            int(df_crudo.isnull().sum().sum()),
            int(df_limpio.isnull().sum().sum()),
        ),
        "filas_box_length_mayor_10m": (
            int((df_crudo["box_length"] > 10).sum()),
            int((df_limpio["box_length"] > 10).sum()),
        ),
    }

    resumen = pd.DataFrame(
        [(metrica, crudo, limpio) for metrica, (crudo, limpio) in metricas.items()],
        columns=["metrica", "crudo", "limpio"],
    )
    logger.info("Resumen de calidad calculado para %s filas crudas y %s filas limpias",
                len(df_crudo), len(df_limpio))
    return resumen
