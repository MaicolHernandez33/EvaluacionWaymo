"""Pruebas de la fábrica de modelos y del ajuste de los 11 candidatos con datos sintéticos (sin escribir archivos)."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from waymo_evaluacion.ep3 import modelos as M
from waymo_evaluacion.ep3.candidatos import CANDIDATOS, NIVEL_SIMPLICIDAD, ajustar, entrada_calibrador
from waymo_evaluacion.ep3.datos import V_MIN3, V_OBS, V_OBS_TAM, V_POSICION, V_TAMANO
from waymo_evaluacion.ep3.inferencia import V16

CJ = {"V16": V16, "V_OBS": V_OBS, "V_OBS_TAM": V_OBS_TAM, "VISTA_OBS": V_OBS, "VISTA_TAMANO": V_TAMANO, "VISTA_POSICION": V_POSICION, "V_MIN3": V_MIN3}


@pytest.fixture(scope="module")
def datos() -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    n = 900
    X = pd.DataFrame({c: np.abs(rng.normal(size=n)) * 20 + 1 for c in V16})
    X["num_top_lidar_points"] = X["num_lidar_points"]            # la regla top usa esta columna
    seg = np.repeat([f"s{i}" for i in range(9)], 100)
    y = (rng.random(n) < X["num_lidar_points"].rsub(60).clip(0, 60) / 60 * 0.8 + 0.05).astype(int)
    return X, y, seg


@pytest.mark.parametrize("candidato", CANDIDATOS)
def test_cada_candidato_se_ajusta_y_puntua(datos, candidato: str, tmp_path, monkeypatch) -> None:
    monkeypatch.setitem(M.DEFECTOS, "RF", {"n_estimators": 25, "max_depth": 6})      # solo en la prueba: RF liviano
    X, y, seg = datos
    p = ajustar(candidato, X, y, seg, CJ)
    s = p.puntuar(X)
    assert s.shape == (len(X),) and np.isfinite(s).all()
    assert roc_auc_score(y, s) > 0.6
    joblib.dump(p, tmp_path / "p.joblib")
    assert np.allclose(joblib.load(tmp_path / "p.joblib").puntuar(X), s)


def test_simplicidad_ordena_los_candidatos_como_el_plan() -> None:
    n = NIVEL_SIMPLICIDAD
    assert n["Regla top"] < n["LR3"] < n["LR"] < n["RF"] < n["HGB"] < n["XGB"] == n["LGBM"] < n["E1"] < n["E3"]
    assert set(n) == set(CANDIDATOS)
    assert {entrada_calibrador(c) for c in CANDIDATOS} == {"log_conteo", "identidad", "logit"}


def test_espacios_incluyen_valores_mas_regularizados_que_ep2() -> None:
    assert 2 in M.ESPACIOS["HGB"]["max_leaf_nodes"] and 3 in M.ESPACIOS["HGB"]["max_leaf_nodes"] and min(M.ESPACIOS["HGB"]["max_leaf_nodes"]) < 4
    assert max(M.ESPACIOS["HGB"]["min_samples_leaf"]) > 800 and max(M.ESPACIOS["RF"]["min_samples_leaf"]) > 200
    assert 1 in M.ESPACIOS["RF"]["max_features"] and 2 in M.ESPACIOS["RF"]["max_features"]
    lr = M.configuraciones("LR")
    assert len(lr) == 8 * 2 * 3 and min(c["C"] for c in lr) == 1e-5 and max(c["C"] for c in lr) == 100.0


def test_configuraciones_son_reproducibles_y_separables() -> None:
    a, b = M.configuraciones("HGB", 30), M.configuraciones("HGB", 30)
    assert M.a_json(a[0]) == M.a_json(b[0]) and len(a) == 30
    vname, params = M.separar(a[0])
    assert vname in M.VARIABLES_OPCIONES and "variables" not in params


def test_seleccion_de_columnas_por_conjunto(datos) -> None:
    X, y, _ = datos
    for modelo in M.MODELOS:
        est = M.construir(modelo, {}, V_OBS).fit(X[V_OBS], y)
        assert M.predecir(est, X[V_OBS]).shape == (len(X),)
