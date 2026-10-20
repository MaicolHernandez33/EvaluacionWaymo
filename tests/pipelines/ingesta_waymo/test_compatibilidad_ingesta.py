"""
Pruebas de los argumentos opcionales de los nodos de ingesta_waymo.

Los argumentos nuevos (listas de segmentos supervisado / solo_clustering en cargar_segmentos_waymo, y
waymo_asociacion_raw / segmentos_supervisado en construir_target_binario) son opcionales: sin ellos los nodos se
comportan como en EP1 (ver tests/pipelines/ingesta_waymo/test_pipeline.py). Estas pruebas ejercen ambos modos.
"""

import numpy as np
import pandas as pd
import pytest

import waymo_evaluacion.pipelines.ingesta_waymo.nodes as nodes

LLAVE = ["key.segment_context_name", "key.frame_timestamp_micros", "key.laser_object_id"]
INVENTARIO = pd.DataFrame(
    {
        "segment_id": ["seg_a", "seg_b", "seg_c", "seg_x"],
        "weather": ["sunny", "sunny", "rain", "sunny"],
        "time_of_day": ["Day", "Night", "Day", "Day"],
        "location": ["location_sf", "location_phx", "location_sf", "location_sf"],
    }
)


def _lidar(seg: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "key.segment_context_name": [seg] * 4,
            "key.frame_timestamp_micros": [100, 100, 200, 200],
            "key.laser_object_id": ["o1", "o2", "o1", "o2"],
            "[LiDARBoxComponent].type": [2, 4, 2, 1],
        }
    )


@pytest.fixture
def lidar_raw():
    return {f"{s}.parquet": (lambda s=s: _lidar(s)) for s in ["seg_a", "seg_b", "seg_c", "seg_x"]}


@pytest.fixture
def asociacion_raw():
    # seg_a: el frame 100 tiene un par (o1 visto por 2 camaras: duplicado); seg_b: sin pares
    a = pd.DataFrame({"key.segment_context_name": ["seg_a", "seg_a"], "key.frame_timestamp_micros": [100, 100], "key.laser_object_id": ["o1", "o1"]})
    b = pd.DataFrame({"key.segment_context_name": [], "key.frame_timestamp_micros": [], "key.laser_object_id": []})
    return {"seg_a.parquet": lambda: a, "seg_b.parquet": lambda: b}


# ----------------------------------------------------------------------------------------- cargar_segmentos_waymo
def test_cargar_sin_listas_carga_todo_con_inventario_dataframe(lidar_raw):
    r = nodes.cargar_segmentos_waymo(lidar_raw, INVENTARIO)
    assert set(r["segment_id"]) == {"seg_a", "seg_b", "seg_c", "seg_x"}
    assert "uso" not in r.columns
    assert r.loc[r["segment_id"] == "seg_b", "time_of_day"].iloc[0] == "Night"


def test_cargar_sin_listas_acepta_inventario_como_dict(lidar_raw):
    metadata = {"seg_a": {"weather": "sunny", "time_of_day": "Day", "location": "location_sf"}}
    r = nodes.cargar_segmentos_waymo(lidar_raw, metadata)
    assert r.loc[r["segment_id"] == "seg_a", "weather"].iloc[0] == "sunny"
    assert r.loc[r["segment_id"] == "seg_c", "weather"].isna().all()      # sin metadato: queda vacio, como en EP1


def test_cargar_con_listas_restringe_y_marca_el_uso(lidar_raw):
    r = nodes.cargar_segmentos_waymo(lidar_raw, INVENTARIO, ["seg_a", "seg_b"], ["seg_c"])
    assert set(r["segment_id"]) == {"seg_a", "seg_b", "seg_c"}               # seg_x se ignora
    assert r.groupby("segment_id")["uso"].first().to_dict() == {"seg_a": "supervisado", "seg_b": "supervisado", "seg_c": "solo_clustering"}


def test_cargar_con_una_sola_lista_la_otra_cuenta_como_vacia(lidar_raw):
    r = nodes.cargar_segmentos_waymo(lidar_raw, INVENTARIO, segmentos_supervisado=["seg_a"])
    assert set(r["segment_id"]) == {"seg_a"}
    r2 = nodes.cargar_segmentos_waymo(lidar_raw, INVENTARIO, segmentos_solo_clustering=["seg_c"])
    assert set(r2["segment_id"]) == {"seg_c"} and (r2["uso"] == "solo_clustering").all()


def test_cargar_con_listas_acepta_inventario_dict(lidar_raw):
    metadata = INVENTARIO.set_index("segment_id").to_dict("index")
    r = nodes.cargar_segmentos_waymo(lidar_raw, metadata, ["seg_a"], [])
    assert r["location"].iloc[0] == "location_sf"


# ----------------------------------------------------------------------------------------- construir_target_binario
def _con_variables(lidar_raw, listas=True):
    cargado = nodes.cargar_segmentos_waymo(lidar_raw, INVENTARIO, ["seg_a", "seg_b"], ["seg_c"]) if listas else nodes.cargar_segmentos_waymo(lidar_raw, INVENTARIO)
    return cargado


def test_target_con_asociacion_sin_lista_trata_todos_como_supervisados(lidar_raw, asociacion_raw):
    cargado = nodes.cargar_segmentos_waymo(lidar_raw, INVENTARIO, ["seg_a", "seg_b"], [])
    r = nodes.construir_target_binario(cargado, asociacion_raw)
    assert len(r) == len(cargado)                                               # el duplicado de la asociacion no infla filas
    assert r["tiene_camara"].notna().all()
    a = r[r["segment_id"] == "seg_a"].set_index([nodes.COL_FRAME, "key.laser_object_id"])["tiene_camara"]
    assert a.loc[(100, "o1")] == 1 and a.loc[(100, "o2")] == 0


def test_target_con_lista_deja_na_en_clustering(lidar_raw, asociacion_raw):
    cargado = _con_variables(lidar_raw)
    r = nodes.construir_target_binario(cargado, asociacion_raw, ["seg_a", "seg_b"])
    assert r.loc[r["segment_id"] == "seg_c", "tiene_camara"].isna().all()
    assert r.loc[r["segment_id"] != "seg_c", "tiene_camara"].notna().all()
    # solo el frame 100 de seg_a tiene un positivo: es el unico frame etiquetado
    etiquetados = r[r["frame_etiquetado"]][["segment_id", nodes.COL_FRAME]].drop_duplicates()
    assert etiquetados.to_dict("records") == [{"segment_id": "seg_a", nodes.COL_FRAME: 100}]


def test_target_sin_asociacion_usa_el_modo_anterior(monkeypatch, lidar_raw):
    cargado = _con_variables(lidar_raw, listas=False)
    asoc = pd.DataFrame({"key.segment_context_name": ["seg_a"], "key.frame_timestamp_micros": [100], "key.laser_object_id": ["o2"]})
    monkeypatch.setattr(nodes.glob, "glob", lambda patron: ["falsa.parquet"])
    monkeypatch.setattr(nodes.pd, "read_parquet", lambda ruta: asoc)
    r = nodes.construir_target_binario(cargado)
    assert len(r) == len(cargado)
    assert "frame_etiquetado" not in r.columns and "uso" not in r.columns
    assert int(r["tiene_camara"].sum()) == 1
    fila = r[(r["segment_id"] == "seg_a") & (r["key.laser_object_id"] == "o2") & (r[nodes.COL_FRAME] == 100)]
    assert fila["tiene_camara"].iloc[0] == 1


# ----------------------------------------------------------------------------------------- resumen_ingesta_waymo
def test_resumen_con_columnas_nuevas_y_sin_ellas(lidar_raw, asociacion_raw):
    cargado = _con_variables(lidar_raw)
    completo = nodes.construir_target_binario(cargado, asociacion_raw, ["seg_a", "seg_b"])
    completo["object_type"] = completo["[LiDARBoxComponent].type"].map(nodes.TIPOS_OBJETO)
    r = nodes.resumen_ingesta_waymo(completo)
    assert set(r["segment_id"]) == {"seg_a", "seg_b", "seg_c"}
    fila_c = r.set_index("segment_id").loc["seg_c"]
    assert np.isnan(fila_c["n_positivos"]) and np.isnan(fila_c["pct_frames_etiquetados"])      # sin target en clustering
    assert r.set_index("segment_id").loc["seg_a", "pct_cyclist"] == pytest.approx(0.25)

    # tabla del modo anterior: sin 'uso', 'frame_etiquetado' ni 'object_type'
    anterior = completo[completo["uso"] == "supervisado"].drop(columns=["uso", "frame_etiquetado", "object_type"])
    anterior["tiene_camara"] = anterior["tiene_camara"].astype(int)
    r2 = nodes.resumen_ingesta_waymo(anterior)
    assert r2.set_index("segment_id").loc["seg_a", "n_positivos"] == 1
    assert r2.set_index("segment_id").loc["seg_a", "pct_cyclist"] == pytest.approx(0.25)
