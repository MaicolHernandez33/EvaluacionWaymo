"""
Pruebas de los nodos del pipeline ingesta_waymo con datos sinteticos pequenos.

Ejecutar desde la raiz del proyecto:   pytest tests/pipelines/ingesta_waymo/test_ingesta_waymo.py -q
(si falla el import: pip install -e .)
"""

import numpy as np
import pandas as pd
import pytest

from waymo_evaluacion.pipelines.ingesta_waymo.nodes import (
    LLAVE_JOIN,
    construir_target_binario,
    cargar_segmentos_waymo,
    crear_variables_waymo,
    filtrar_frames_etiquetados,
    resumen_ingesta_waymo,
)

P = "[LiDARBoxComponent]."
N_FRAMES, N_OBJ = 10, 6
SUP_A, SUP_B, CLU, EXTRA = "segA_1_000_2_000", "segB_1_000_2_000", "segC_1_000_2_000", "segX_1_000_2_000"


def _lidar(segment_id: str) -> pd.DataFrame:
    filas = []
    for f in range(N_FRAMES):
        for o in range(N_OBJ):
            filas.append(
                {
                    "key.segment_context_name": segment_id,
                    "key.frame_timestamp_micros": 1000 * f,
                    "key.laser_object_id": f"obj{o}",
                    P + "type": 1 + (o % 4),
                    P + "box.center.x": 10.0 + o, P + "box.center.y": 5.0, P + "box.center.z": 1.0,
                    P + "box.size.x": 4.0, P + "box.size.y": 2.0, P + "box.size.z": 1.5,
                    P + "num_lidar_points_in_box": 30 + o,
                    P + "speed.x": 3.0, P + "speed.y": 4.0,
                }
            )
    return pd.DataFrame(filas)


def _asociacion(segment_id: str, frames: range, objetos: range) -> pd.DataFrame:
    filas = [
        {"key.segment_context_name": segment_id, "key.frame_timestamp_micros": 1000 * f,
         "key.laser_object_id": f"obj{o}"}
        for f in frames for o in objetos
    ]
    df = pd.DataFrame(filas)
    return pd.concat([df, df.head(5)], ignore_index=True)   # duplicados: objeto visto por 2 camaras


@pytest.fixture
def inventario():
    ids = [SUP_A, SUP_B, CLU, EXTRA]
    return pd.DataFrame({
        "segment_id": ids, "weather": ["sunny", "sunny", "rain", "sunny"],
        "time_of_day": ["Day", "Night", "Day", "Day"], "location": ["location_sf"] * 4,
    })


@pytest.fixture
def lidar_raw():
    # EXTRA existe en la carpeta pero no esta en el YAML: no debe cargarse.
    return {f"{s}.parquet": (lambda s=s: _lidar(s)) for s in [SUP_A, SUP_B, CLU, EXTRA]}


@pytest.fixture
def asociacion_raw():
    # SUP_A: etiquetado solo en los frames 5-9 (3 objetos); SUP_B: todos los frames (2 objetos).
    # EXTRA tiene asociaciones en la carpeta pero no esta en el YAML.
    return {
        f"{SUP_A}.parquet": lambda: _asociacion(SUP_A, range(5, 10), range(3)),
        f"{SUP_B}.parquet": lambda: _asociacion(SUP_B, range(10), range(2)),
        f"{EXTRA}.parquet": lambda: _asociacion(EXTRA, range(10), range(6)),
    }


def _cargar(lidar_raw, inventario):
    return cargar_segmentos_waymo(lidar_raw, inventario, [SUP_A, SUP_B], [CLU])


def test_cargar_ignora_segmentos_fuera_de_la_lista(lidar_raw, inventario):
    df = _cargar(lidar_raw, inventario)
    assert set(df["segment_id"]) == {SUP_A, SUP_B, CLU}
    assert len(df) == 3 * N_FRAMES * N_OBJ
    assert dict(df.groupby("segment_id")["uso"].first()) == {
        SUP_A: "supervisado", SUP_B: "supervisado", CLU: "solo_clustering"}
    assert df.loc[df["segment_id"] == SUP_B, "time_of_day"].iloc[0] == "Night"


def test_cargar_falla_si_falta_un_archivo(lidar_raw, inventario):
    del lidar_raw[f"{SUP_B}.parquet"]
    with pytest.raises(FileNotFoundError, match=SUP_B):
        _cargar(lidar_raw, inventario)


def test_cargar_falla_si_segmento_esta_en_ambas_listas(lidar_raw, inventario):
    with pytest.raises(ValueError):
        cargar_segmentos_waymo(lidar_raw, inventario, [SUP_A, CLU], [CLU])


def test_variables_waymo(lidar_raw, inventario):
    df = crear_variables_waymo(_cargar(lidar_raw, inventario))
    assert set(df["object_type"].dropna()) == {"VEHICLE", "PEDESTRIAN", "SIGN", "CYCLIST"}
    assert np.allclose(df["speed_mps"], 5.0)                      # hipot(3, 4)
    assert np.allclose(df["volumen_caja"], 4.0 * 2.0 * 1.5)
    assert df["distancia_m"].between(0, 100).all()
    assert np.isfinite(df["densidad_puntos"]).all()


def test_variables_waymo_error_claro_si_falta_columna(lidar_raw, inventario):
    df = _cargar(lidar_raw, inventario).drop(columns=[P + "box.size.z"])
    with pytest.raises(KeyError, match="box.size.z"):
        crear_variables_waymo(df)


def _con_target(lidar_raw, inventario, asociacion_raw):
    df = crear_variables_waymo(_cargar(lidar_raw, inventario))
    return construir_target_binario(df, asociacion_raw, [SUP_A, SUP_B])


def test_target_es_na_en_clustering_y_binario_en_supervisados(lidar_raw, inventario, asociacion_raw):
    df = _con_target(lidar_raw, inventario, asociacion_raw)
    assert df.loc[df["segment_id"] == CLU, "tiene_camara"].isna().all()
    sup = df[df["uso"] == "supervisado"]
    assert set(sup["tiene_camara"].unique()) == {0, 1}
    # SUP_A: 5 frames x 3 objetos = 15 positivos; SUP_B: 10 frames x 2 objetos = 20 (duplicados no cuentan)
    assert sup.loc[sup["segment_id"] == SUP_A, "tiene_camara"].sum() == 15
    assert sup.loc[sup["segment_id"] == SUP_B, "tiene_camara"].sum() == 20
    assert len(df) == 3 * N_FRAMES * N_OBJ                       # el join no duplica ni pierde filas


def test_target_no_usa_asociaciones_de_segmentos_fuera_de_la_lista(lidar_raw, inventario, asociacion_raw):
    df = _con_target(lidar_raw, inventario, asociacion_raw)
    assert EXTRA not in set(df["segment_id"])


def test_target_falla_si_falta_asociacion_de_un_supervisado(lidar_raw, inventario, asociacion_raw):
    del asociacion_raw[f"{SUP_B}.parquet"]
    with pytest.raises(FileNotFoundError, match=SUP_B):
        _con_target(lidar_raw, inventario, asociacion_raw)


def test_frame_etiquetado(lidar_raw, inventario, asociacion_raw):
    df = _con_target(lidar_raw, inventario, asociacion_raw)
    a = df[df["segment_id"] == SUP_A]
    assert a.loc[a["frame_etiquetado"], "key.frame_timestamp_micros"].nunique() == 5   # frames 5-9
    assert not df.loc[df["segment_id"] == CLU, "frame_etiquetado"].any()


def test_filtro_de_frames(lidar_raw, inventario, asociacion_raw):
    df = _con_target(lidar_raw, inventario, asociacion_raw)
    sup, reporte = filtrar_frames_etiquetados(df)
    assert set(sup["segment_id"]) == {SUP_A, SUP_B}              # clustering fuera
    assert sup["tiene_camara"].isin([0, 1]).all()
    fila_a = reporte.set_index("segment_id").loc[SUP_A]
    assert fila_a["filas_antes"] == N_FRAMES * N_OBJ and fila_a["filas_despues"] == 5 * N_OBJ
    assert fila_a["positivos"] == 15                              # los positivos se conservan todos
    assert fila_a["tasa_despues_pct"] == pytest.approx(15 / 30 * 100)
    assert reporte.set_index("segment_id").loc[SUP_B, "pct_filas_conservadas"] == 100.0


def test_resumen(lidar_raw, inventario, asociacion_raw):
    resumen = resumen_ingesta_waymo(_con_target(lidar_raw, inventario, asociacion_raw)).set_index("segment_id")
    assert np.isnan(resumen.loc[CLU, "pct_positivos"])
    assert resumen.loc[SUP_A, "pct_frames_etiquetados"] == pytest.approx(0.5)
    assert resumen.loc[SUP_B, "pct_frames_etiquetados"] == pytest.approx(1.0)
    assert len(LLAVE_JOIN) == 3
