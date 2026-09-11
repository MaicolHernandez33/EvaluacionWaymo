"""
Tests del pipeline 'ingesta_waymo'.

Usan DataFrames sinteticos pequenos, sin leer los parquet reales de
data/01_raw/waymo/. construir_target_binario lee esa carpeta por dentro
(glob + pd.read_parquet), asi que esos dos se reemplazan con monkeypatch
para devolver una tabla de asociacion sintetica en vez de tocar el disco.
"""

import pandas as pd
import pytest

import waymo_evaluacion.pipelines.ingesta_waymo.nodes as nodes

METADATA_SEGMENTOS = {
    "seg_a": {"weather": "sunny", "time_of_day": "Day", "location": "location_sf"},
    "seg_b": {"weather": "sunny", "time_of_day": "Night", "location": "location_phx"},
    "seg_c": {"weather": "sunny", "time_of_day": "Dawn/Dusk", "location": "location_other"},
    "seg_d": {"weather": "rain", "time_of_day": "Dawn/Dusk", "location": "location_phx"},
}


def _lidar_box_sintetico(segment_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "key.segment_context_name": [segment_id, segment_id],
            "key.frame_timestamp_micros": [100, 200],
            "key.laser_object_id": [f"{segment_id}_obj_0", f"{segment_id}_obj_1"],
            "[LiDARBoxComponent].type": [1, 4],
        }
    )


@pytest.fixture
def particiones_lidar_box():
    """Simula el dict {particion: funcion_de_carga} que entrega un
    PartitionedDataset de Kedro, con 4 segmentos sinteticos."""
    return {
        f"{segment_id}.parquet": (lambda seg=segment_id: _lidar_box_sintetico(seg))
        for segment_id in METADATA_SEGMENTOS
    }


def test_cargar_segmentos_waymo_agrega_columnas_de_metadata(particiones_lidar_box):
    """El resultado debe tener segment_id, weather, time_of_day y location,
    con los valores correctos tomados de metadata_segmentos."""
    resultado = nodes.cargar_segmentos_waymo(particiones_lidar_box, METADATA_SEGMENTOS)

    for columna in ["segment_id", "weather", "time_of_day", "location"]:
        assert columna in resultado.columns

    fila_seg_d = resultado.loc[resultado["segment_id"] == "seg_d"].iloc[0]
    assert fila_seg_d["weather"] == "rain"
    assert fila_seg_d["time_of_day"] == "Dawn/Dusk"
    assert fila_seg_d["location"] == "location_phx"


def test_cargar_segmentos_waymo_retorna_4_segmentos_unicos(particiones_lidar_box):
    """Cada particion del PartitionedDataset debe convertirse en un
    segmento distinto tras la concatenacion, sin perder ni duplicar
    ninguno."""
    resultado = nodes.cargar_segmentos_waymo(particiones_lidar_box, METADATA_SEGMENTOS)

    assert resultado["segment_id"].nunique() == 4
    assert set(resultado["segment_id"].unique()) == set(METADATA_SEGMENTOS)


def test_construir_target_binario_crea_columna_binaria(monkeypatch):
    """tiene_camara solo puede tomar los valores 0 o 1, y debe marcar en 1
    exactamente la fila que matchea con la tabla de asociacion."""
    lidar_box = pd.DataFrame(
        {
            "key.segment_context_name": ["seg_a", "seg_a", "seg_b"],
            "key.frame_timestamp_micros": [100, 200, 100],
            "key.laser_object_id": ["obj_1", "obj_2", "obj_3"],
            "segment_id": ["seg_a", "seg_a", "seg_b"],
        }
    )
    asociacion_sintetica = pd.DataFrame(
        {
            "key.segment_context_name": ["seg_a"],
            "key.frame_timestamp_micros": [100],
            "key.laser_object_id": ["obj_1"],
        }
    )
    monkeypatch.setattr(nodes.glob, "glob", lambda patron: ["asociacion_falsa.parquet"])
    monkeypatch.setattr(nodes.pd, "read_parquet", lambda ruta: asociacion_sintetica)

    resultado = nodes.construir_target_binario(lidar_box)

    assert set(resultado["tiene_camara"].unique()) <= {0, 1}
    assert resultado.loc[resultado["key.laser_object_id"] == "obj_1", "tiene_camara"].iloc[0] == 1
    assert resultado.loc[resultado["key.laser_object_id"] == "obj_2", "tiene_camara"].iloc[0] == 0
    assert resultado.loc[resultado["key.laser_object_id"] == "obj_3", "tiene_camara"].iloc[0] == 0


def test_construir_target_binario_no_pierde_ni_duplica_filas(monkeypatch):
    """El left join debe preservar exactamente las filas de lidar_box, aun
    cuando un mismo objeto fue visto por mas de una camara en el mismo
    instante (la deduplicacion de la tabla de asociacion tiene que evitar
    que el join infle filas)."""
    lidar_box = pd.DataFrame(
        {
            "key.segment_context_name": ["seg_a", "seg_a"],
            "key.frame_timestamp_micros": [100, 200],
            "key.laser_object_id": ["obj_1", "obj_2"],
            "segment_id": ["seg_a", "seg_a"],
        }
    )
    # obj_1 fue visto por 2 camaras distintas en el mismo instante.
    asociacion_sintetica = pd.DataFrame(
        {
            "key.segment_context_name": ["seg_a", "seg_a"],
            "key.frame_timestamp_micros": [100, 100],
            "key.laser_object_id": ["obj_1", "obj_1"],
            "key.camera_name": [1, 2],
        }
    )
    monkeypatch.setattr(nodes.glob, "glob", lambda patron: ["asociacion_falsa.parquet"])
    monkeypatch.setattr(nodes.pd, "read_parquet", lambda ruta: asociacion_sintetica)

    resultado = nodes.construir_target_binario(lidar_box)

    assert len(resultado) == len(lidar_box)


@pytest.fixture
def waymo_con_target_sintetico():
    return pd.DataFrame(
        {
            "segment_id": ["seg_a", "seg_a", "seg_b", "seg_b", "seg_b"],
            "weather": ["sunny", "sunny", "rain", "rain", "rain"],
            "time_of_day": ["Day", "Day", "Dawn/Dusk", "Dawn/Dusk", "Dawn/Dusk"],
            "location": ["location_sf", "location_sf", "location_phx", "location_phx", "location_phx"],
            "tiene_camara": [1, 0, 0, 0, 1],
            "[LiDARBoxComponent].type": [1, 4, 1, 1, 2],
        }
    )


def test_resumen_ingesta_waymo_retorna_una_fila_por_segmento(waymo_con_target_sintetico):
    """El resumen debe tener exactamente un registro por segment_id
    distinto de la entrada, ni mas ni menos."""
    resumen = nodes.resumen_ingesta_waymo(waymo_con_target_sintetico)

    assert len(resumen) == waymo_con_target_sintetico["segment_id"].nunique()
    assert set(resumen["segment_id"]) == {"seg_a", "seg_b"}


def test_resumen_ingesta_waymo_porcentajes_entre_0_y_1(waymo_con_target_sintetico):
    """pct_positivos y pct_cyclist son proporciones: deben quedar siempre
    en el rango [0, 1], y coincidir con el calculo manual esperado."""
    resumen = nodes.resumen_ingesta_waymo(waymo_con_target_sintetico)

    assert resumen["pct_positivos"].between(0, 1).all()
    assert resumen["pct_cyclist"].between(0, 1).all()

    # seg_a: 1 de 2 filas tiene tiene_camara=1, y 1 de 2 es CYCLIST (type=4)
    fila_seg_a = resumen.loc[resumen["segment_id"] == "seg_a"].iloc[0]
    assert fila_seg_a["pct_positivos"] == pytest.approx(0.5)
    assert fila_seg_a["pct_cyclist"] == pytest.approx(0.5)
