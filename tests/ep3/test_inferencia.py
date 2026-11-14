"""Pruebas de inferencia, objetos congelados, métricas, folds y plan v3 (EP3). Escriben solo en tmp_path."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

from waymo_evaluacion.ep3.congelado import (
    CalibradorPlatt, PuntuadorModelo, PuntuadorPromedio, PuntuadorRangos, PuntuadorRegla, PuntuadorStacking,
)
from waymo_evaluacion.ep3.datos import V_OBS, crear_folds
from waymo_evaluacion.ep3.detector_huecos import ParametrosDetector
from waymo_evaluacion.ep3.inferencia import (
    V16, Artefactos, agregar_asociacion, cargar_artefactos, construir_variables, percentil_en_referencia, puntuar_segmento,
)
from waymo_evaluacion.ep3.metricas import (
    ConjuntoOOF, Ranking, RankingDosPasos, confusion, desempate, ece_cuantiles, ic95, umbral_para_recall, umbral_para_revision,
)
from waymo_evaluacion.ep3.modelos import construir
from waymo_evaluacion.ep3.plan import cargar_plan_v3, verificar_plan_v3

R = Path(__file__).resolve().parents[2]
P = "[LiDARBoxComponent]."


def _lidar_box(n_frames: int = 10, por_frame: int = 100, seg: str = "S" * 12 + "_0_000_20_000") -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = n_frames * por_frame
    az = np.radians(rng.uniform(-50, 50, n))
    dist = rng.uniform(5, 30, n)
    return pd.DataFrame({
        "key.segment_context_name": seg, "key.frame_timestamp_micros": np.repeat(1000 + np.arange(n_frames), por_frame),
        "key.laser_object_id": [f"id{i}" for i in range(n)], P + "box.center.x": dist * np.cos(az), P + "box.center.y": dist * np.sin(az),
        P + "box.center.z": 1.0, P + "box.size.x": 0.8, P + "box.size.y": 0.8, P + "box.size.z": 1.7, P + "box.heading": 0.3, P + "type": 2,
        P + "num_lidar_points_in_box": rng.integers(5, 400, n), P + "num_top_lidar_points_in_box": rng.integers(5, 300, n),
        P + "speed.x": 0.5, P + "speed.y": 0.5,
    })


def _asociacion(lb: pd.DataFrame, camaras_con_par: dict[int, tuple[float, float]]) -> pd.DataFrame:
    """Todas las cajas tienen par en la cámara 1; las demás solo dentro del rango dado."""
    az = np.degrees(np.arctan2(lb[P + "box.center.y"], lb[P + "box.center.x"]))
    filas = []
    for cam, (lo, hi) in camaras_con_par.items():
        m = (az >= lo) & (az <= hi) if cam != 1 else np.ones(len(lb), bool)
        filas.append(pd.DataFrame({"key.frame_timestamp_micros": lb.loc[m, "key.frame_timestamp_micros"], "key.camera_name": cam, "key.laser_object_id": lb.loc[m, "key.laser_object_id"]}))
    return pd.concat(filas, ignore_index=True)


def _artefactos() -> Artefactos:
    det = ParametrosDetector(rangos={1: (-30.0, 30.0), 2: (10.0, 60.0), 3: (-60.0, -10.0), 4: (50.0, 100.0), 5: (-100.0, -50.0)},
                             medianas_ref={f"c{c}": 0.9 for c in range(1, 6)})
    return Artefactos(PuntuadorRegla("num_top_lidar_points"), None, {"A": -50.0, "B": -20.0}, det, {"nombre": "regla"})


def test_construir_variables_formulas() -> None:
    v = construir_variables(_lidar_box(1, 5))
    assert set(V16) <= set(v.columns)
    assert np.allclose(v["volumen_caja"], 0.8 * 0.8 * 1.7)
    assert np.allclose(v["distancia_m"], np.hypot(v["box_center_x"], v["box_center_y"]))
    assert np.allclose(v["speed_mps"], np.hypot(0.5, 0.5)) and (v["es_ciclista"] == 0).all()
    assert np.allclose(v["heading_sin"] ** 2 + v["heading_cos"] ** 2, 1)


def test_puntuar_segmento_detecta_hueco_y_ordena_la_cola() -> None:
    lb = _lidar_box()
    asoc = _asociacion(lb, {1: (0, 0), 2: (10, 60), 4: (50, 100), 5: (-100, -50)})        # la cámara 3 no tiene ningún par
    r = puntuar_segmento(lb, asoc, _artefactos())
    assert list(r.lista_A["camara"]) == ["3 (frontal der.)"]
    assert r.lista_A.loc[0, "tasa"] == 0.0 and r.lista_A.loc[0, "cajas_en_rango"] >= 100
    assert r.resumen["celdas_con_hueco"] == 1 and r.resumen["cajas_en_celdas_con_hueco"] > 100
    assert not r.lista_B["en_hueco"].any() and r.lista_B["score"].is_monotonic_decreasing
    assert len(r.lista_B) + r.resumen["cajas_en_celdas_con_hueco"] == r.resumen["cajas_vru_poblacion_principal"]


def test_puntuar_sin_asociacion_advierte_y_no_marca_huecos() -> None:
    r = puntuar_segmento(_lidar_box(), None, _artefactos())
    assert r.lista_A.empty and any("sin archivo de asociación" in a for a in r.advertencias)
    assert not r.cajas["en_hueco"].any() and len(r.lista_B) == len(r.cajas)


def test_puntuar_sin_peatones_falla() -> None:
    lb = _lidar_box(1, 5)
    lb[P + "type"] = 1
    with pytest.raises(ValueError):
        puntuar_segmento(lb, None, _artefactos())


def test_agregar_asociacion_descarta_frames_sin_etiquetas() -> None:
    lb = _lidar_box(4, 10)
    v = construir_variables(lb)
    asoc = _asociacion(lb[lb["key.frame_timestamp_micros"] < 1002], {1: (0, 0)})            # solo 2 de 4 frames etiquetados
    out = agregar_asociacion(v, asoc)
    assert set(out["key.frame_timestamp_micros"]) == {1000, 1001} and (out["sin_camara"] == 0).all()


def test_artefactos_ida_y_vuelta_en_tmp_path(tmp_path: Path) -> None:
    rng = np.random.default_rng(0)
    X = pd.DataFrame(np.abs(rng.normal(size=(200, 4))) * 50 + 1, columns=V_OBS)
    y = (X["num_lidar_points"] < 40).astype(int)
    lr = construir("LR", {"C": 1.0}, V_OBS).fit(X, y)
    pm = PuntuadorModelo(lr, V_OBS)
    s = pm.puntuar(X)
    cal = CalibradorPlatt(LogisticRegression(C=1e6).fit(np.log(s / (1 - s)).reshape(-1, 1), y), "logit")
    art = Artefactos(pm, cal, {"A": 0.3, "B": 0.5}, ParametrosDetector(rangos={1: (-1.0, 1.0)}, medianas_ref={"c1": 0.9}))
    art.guardar(tmp_path / "v3")
    art2 = cargar_artefactos(tmp_path / "v3")
    assert np.allclose(art2.puntuador.puntuar(X), s) and np.allclose(art2.calibrador.calibrar(s), cal.calibrar(s))
    assert art2.detector == art.detector and art2.umbrales == art.umbrales


def test_puntuadores_compuestos(tmp_path: Path) -> None:
    rng = np.random.default_rng(1)
    X = pd.DataFrame(np.abs(rng.normal(size=(300, 4))) * 50 + 1, columns=V_OBS)
    y = (X.iloc[:, 0] + rng.normal(size=300) * 20 > 50).astype(int)
    a = PuntuadorModelo(construir("LR", {}, V_OBS).fit(X, y), V_OBS)
    b = PuntuadorModelo(construir("HGB", {"max_iter": 20}, V_OBS).fit(X, y), V_OBS)
    prom = PuntuadorPromedio([a, b]).puntuar(X)
    assert np.allclose(prom, (a.puntuar(X) + b.puntuar(X)) / 2)
    rang = PuntuadorRangos([a, b]).puntuar(X)
    assert 0 < rang.min() and rang.max() <= 1
    Z = np.hstack([np.log(c.puntuar(X) / (1 - c.puntuar(X))).reshape(-1, 1) for c in (a, b)])
    st = PuntuadorStacking([a, b], LogisticRegression().fit(Z, y))
    assert roc_auc_score(y, st.puntuar(X)) > 0.7
    joblib.dump(st, tmp_path / "st.joblib")
    assert np.allclose(joblib.load(tmp_path / "st.joblib").puntuar(X), st.puntuar(X))


def test_percentil_en_referencia() -> None:
    assert percentil_en_referencia(0.9, np.array([0.1, 0.5, 0.9, 0.95])) == 0.5


# ------------------------------------------------------------------------------------ metricas
def test_ranking_coincide_con_sklearn_incluso_con_empates_y_pesos() -> None:
    rng = np.random.default_rng(0)
    y = (rng.random(3000) < 0.25).astype(int)
    s = np.round(rng.normal(size=3000) + y, 1)
    w = rng.integers(0, 3, 3000).astype(float)
    r = Ranking(y, s, desempate(3000))
    assert r.metricas()[0] == pytest.approx(roc_auc_score(y, s)) and r.metricas()[1] == pytest.approx(average_precision_score(y, s))
    assert r.metricas(w)[0] == pytest.approx(roc_auc_score(y, s, sample_weight=w))
    assert r.metricas(w)[1] == pytest.approx(average_precision_score(y, s, sample_weight=w))


def test_bootstrap_pareado_y_umbrales() -> None:
    rng = np.random.default_rng(0)
    seg = np.repeat(np.arange(20), 100)
    y = (rng.random(2000) < 0.3).astype(int)
    bueno, malo = y + rng.normal(size=2000), rng.normal(size=2000)
    c = ConjuntoOOF(y, seg, {"bueno": [bueno], "malo": [malo]})
    b = c.bootstrap(["bueno", "malo"], 200)
    lo, hi = ic95(b["bueno"][:, 0] - b["malo"][:, 0])
    assert lo > 0 and hi > lo
    u = umbral_para_recall(y, bueno, 0.8)
    assert confusion(bueno >= u, y)["recall"] >= 0.8
    assert abs((bueno >= umbral_para_revision(bueno, 0.2)).mean() - 0.2) < 0.01
    p = rng.uniform(0.05, 0.95, 40000)
    e, _ = ece_cuantiles((rng.random(40000) < p).astype(int), p)       # probabilidades calibradas por construccion
    assert e < 0.02


def test_ranking_dos_pasos_la_auditoria_no_cuesta() -> None:
    y = np.array([1, 1, 0, 0, 1, 0, 0, 0, 0, 0])
    aud = np.array([True, True, False, False, False, False, False, False, False, False])
    s = np.array([0.0, 0.0, 0.9, 0.1, 0.8, 0.2, 0.3, 0.4, 0.5, 0.6])
    cap20, frac80 = RankingDosPasos(y, s, desempate(10), aud).metricas()
    assert cap20 >= 2 / 3                    # los 2 positivos auditados ya cuentan con costo 0
    assert frac80 <= 0.2 + 1e-9              # el tercero se encuentra revisando 1 o 2 cajas de la cola


# ------------------------------------------------------------------------------------ datos y plan
def test_folds_son_por_segmento_y_estratificados() -> None:
    rng = np.random.default_rng(0)
    seg = np.repeat([f"s{i}" for i in range(20)], 50)
    dev = pd.DataFrame({"seg": seg, "sin_camara": (rng.random(1000) < 0.25).astype(int), "en_zona_principal": True})
    dev.loc[:49, "en_zona_principal"] = False
    f = crear_folds(dev, (42, 43), k=5)
    for col in f.columns:
        ok = f.loc[dev["en_zona_principal"]]
        assert (ok[col] >= 0).all() and (f.loc[~dev["en_zona_principal"], col] == -1).all()
        assert (dev.loc[dev["en_zona_principal"]].assign(f=ok[col]).groupby("seg")["f"].nunique() == 1).all()
    assert not f["fold_s42"].equals(f["fold_s43"])


def test_plan_v3_verificado_y_cargable() -> None:
    assert set(verificar_plan_v3(R)) == {"plan_v3.md", "plan_v3.json"}
    p = cargar_plan_v3(R)
    assert p["P1"]["cv_externa"]["semillas"] == [42, 43, 44] and p["P8"]["objetivos"]["O4"]["ece_max"] == 0.05


def test_plan_v3_detecta_cambios(tmp_path: Path) -> None:
    d = tmp_path / "docs" / "ep3"
    d.mkdir(parents=True)
    for n in ("plan_v3.md", "plan_v3.json", "plan_v3.sha256"):
        (d / n).write_bytes((R / "docs" / "ep3" / n).read_bytes())
    verificar_plan_v3(tmp_path)
    (d / "plan_v3.json").write_text(json.dumps({"cambiado": True}), encoding="utf-8")
    with pytest.raises(RuntimeError):
        verificar_plan_v3(tmp_path)


@pytest.mark.skipif(not (R / "data/05_model_input_ep3/dev_41.parquet").exists(), reason="faltan datos de desarrollo de EP3")
def test_variables_reales_coinciden_con_dev41() -> None:
    seg = "10023947602400723454_1120_000_1140_000"
    ruta = R / "data/01_raw/waymo"
    if not (ruta / "lidar_box" / f"{seg}.parquet").exists():
        pytest.skip("falta el parquet crudo")
    dev = pd.read_parquet(R / "data/05_model_input_ep3/dev_41.parquet")
    dev = dev[dev["segment_id"] == seg]
    v = construir_variables(pd.read_parquet(ruta / "lidar_box" / f"{seg}.parquet"))
    v = agregar_asociacion(v[v["object_type"].isin(["PEDESTRIAN", "CYCLIST"]) & (v["azimut_abs_deg"] <= 120)], pd.read_parquet(ruta / "camera_to_lidar_box_association" / f"{seg}.parquet"))
    m = v.merge(dev, on=["segment_id", "key.frame_timestamp_micros", "key.laser_object_id"], suffixes=("", "_d"))
    assert len(m) == len(dev) == len(v)
    for c in V16:
        assert np.allclose(m[c].astype(float), m[c + "_d"].astype(float), equal_nan=True), c
    assert (m["sin_camara"] == m["sin_camara_d"]).all()
