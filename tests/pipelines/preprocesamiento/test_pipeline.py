"""
Tests del pipeline 'preprocesamiento'.

Usan DataFrames sinteticos pequenos, sin leer archivos reales de data/.
"""

import pandas as pd

from waymo_evaluacion.pipelines.preprocesamiento.nodes import (
    convertir_nulos_ocultos,
    eliminar_columnas_sin_varianza,
    eliminar_duplicados_logicos,
    filtrar_valores_imposibles,
)
from waymo_evaluacion.pipelines.preprocesamiento.pipeline import create_pipeline


def test_pipeline_no_tiene_ciclos():
    """create_pipeline() no debe lanzar CircularDependencyError, y el
    orden topologico de sus 7 nodos debe poder calcularse sin errores."""
    pipeline = create_pipeline()

    # Pipeline.__init__ ya valida el DAG (kedro.pipeline.pipeline.Pipeline
    # lanza CircularDependencyError en la construccion si hay un ciclo).
    # Ademas forzamos el calculo del orden topologico accediendo a .nodes,
    # que es donde kedro ordena el grafo con TopologicalSorter.
    nodos_ordenados = pipeline.nodes

    assert len(nodos_ordenados) == 7
    assert len(pipeline.grouped_nodes) > 0


def test_filtrar_valores_imposibles_elimina_box_length_no_positivo():
    """Filas con box_length <= 0 deben desaparecer del resultado."""
    df = pd.DataFrame(
        {
            "box_length": [-5.0, 0.0, 4.0],
            "box_height": [1.5, 1.5, 1.5],
            "speed_mps": [5.0, 5.0, 5.0],
        }
    )

    resultado = filtrar_valores_imposibles(df, altura_max=6.0, velocidad_max=50.0)

    assert len(resultado) == 1
    assert (resultado["box_length"] > 0).all()


def test_filtrar_valores_imposibles_preserva_buses_legitimos():
    """box_length > 10 (buses/camiones reales) no debe filtrarse: el
    filtro solo elimina valores imposibles (<= 0), no valores grandes."""
    df = pd.DataFrame(
        {
            "box_length": [4.0, 15.0],
            "box_height": [1.6, 3.3],
            "speed_mps": [8.0, 9.0],
        }
    )

    resultado = filtrar_valores_imposibles(df, altura_max=6.0, velocidad_max=50.0)

    assert len(resultado) == 2
    assert 15.0 in resultado["box_length"].values


def test_eliminar_duplicados_logicos_elimina_por_llave_compuesta():
    """Dos filas con el mismo segment_id + timestamp_micros + id_interno
    cuentan como una sola deteccion, aunque otras columnas difieran."""
    df = pd.DataFrame(
        {
            "segment_id": ["seg_1", "seg_1", "seg_2"],
            "timestamp_micros": [100, 100, 200],
            "id_interno": ["det_1", "det_1", "det_2"],
            "speed_mps": [5.0, 5.5, 7.0],
        }
    )

    resultado = eliminar_duplicados_logicos(df)

    assert len(resultado) == 2
    assert resultado["id_interno"].tolist() == ["det_1", "det_2"]


def test_eliminar_columnas_sin_varianza_no_elimina_columnas_protegidas():
    """weather y time_of_day no deben borrarse aunque tengan un solo
    valor unico, si estan en columnas_protegidas."""
    df = pd.DataFrame(
        {
            "sensor_version": ["v1", "v1", "v1"],
            "weather": ["sunny", "sunny", "sunny"],
            "time_of_day": ["Day", "Day", "Day"],
            "object_type": ["VEHICLE", "PEDESTRIAN", "VEHICLE"],
        }
    )

    resultado = eliminar_columnas_sin_varianza(df, columnas_protegidas=["weather", "time_of_day"])

    assert "sensor_version" not in resultado.columns
    assert "weather" in resultado.columns
    assert "time_of_day" in resultado.columns
    assert "object_type" in resultado.columns


def test_convertir_nulos_ocultos_convierte_nd_en_nan():
    """El texto 'N/D' en timestamp_micros debe quedar como NaN, y la
    columna debe terminar en un dtype numerico."""
    df = pd.DataFrame(
        {
            "timestamp_micros": ["100", "N/D", "300"],
            "num_lidar_points": [10, 20, 30],
        }
    )

    resultado = convertir_nulos_ocultos(df)

    assert resultado["timestamp_micros"].isna().sum() == 1
    assert pd.isna(resultado.loc[1, "timestamp_micros"])
    assert pd.api.types.is_numeric_dtype(resultado["timestamp_micros"])


def test_convertir_nulos_ocultos_convierte_centinela_negativo_en_nan():
    """El centinela -1 en num_lidar_points debe quedar como NaN."""
    df = pd.DataFrame(
        {
            "timestamp_micros": ["100", "200", "300"],
            "num_lidar_points": [10, -1, 30],
        }
    )

    resultado = convertir_nulos_ocultos(df)

    assert resultado["num_lidar_points"].isna().sum() == 1
    assert pd.isna(resultado.loc[1, "num_lidar_points"])
