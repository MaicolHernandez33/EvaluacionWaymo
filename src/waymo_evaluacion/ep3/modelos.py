"""Fábrica de modelos de EP3: LR, RF, HGB, XGBoost y LightGBM, con conjunto de variables como hiperparámetro.

Cada modelo es un ``Pipeline`` que primero selecciona las columnas del conjunto de variables
elegido (V16, V_OBS o V_OBS_TAM). Todos usan semilla 42 y un solo hilo por defecto; el paralelismo
se hace por tareas (procesos), no dentro del modelo, para dejar el equipo usable.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import loguniform
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import ParameterSampler
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

SEMILLA = 42
MODELOS = ("LR", "RF", "HGB", "XGB", "LGBM")
COLS_LOG = ("num_lidar_points", "num_top_lidar_points", "densidad_puntos", "volumen_caja")


def _log1p(x: np.ndarray) -> np.ndarray:
    return np.log1p(x)


def preprocesador_lr(cols: list[str]) -> ColumnTransformer:
    """log1p + estandarización para conteos y volumen; estandarización para el resto (igual que EP2)."""
    con_log = [c for c in cols if c in COLS_LOG]
    sin_log = [c for c in cols if c not in COLS_LOG]
    pasos = []
    if con_log:
        pasos.append(("log", make_pipeline(FunctionTransformer(_log1p, feature_names_out="one-to-one"), StandardScaler()), con_log))
    if sin_log:
        pasos.append(("std", StandardScaler(), sin_log))
    return ColumnTransformer(pasos)


def construir(modelo: str, params: dict[str, Any] | None, columnas: list[str], n_jobs: int = 1) -> Pipeline:
    """Crea el modelo ``modelo`` con los hiperparámetros ``params`` (o por defecto si es None).

    Args:
        modelo: uno de ``MODELOS``.
        params: hiperparámetros del estimador (sin la clave ``variables``).
        columnas: columnas de entrada (el conjunto de variables).
        n_jobs: hilos del estimador.
    """
    p = dict(params or {})
    if modelo == "LR":
        est = LogisticRegression(max_iter=1000, random_state=SEMILLA, **p)
        return Pipeline([("pre", preprocesador_lr(columnas)), ("est", est)])
    sel = ColumnTransformer([("sel", "passthrough", columnas)])
    if modelo == "RF":
        est = RandomForestClassifier(**{"n_estimators": 200, **p}, n_jobs=n_jobs, random_state=SEMILLA)
    elif modelo == "HGB":
        est = HistGradientBoostingClassifier(**{"early_stopping": False, **p}, random_state=SEMILLA)
    elif modelo == "XGB":
        from xgboost import XGBClassifier

        est = XGBClassifier(**{"tree_method": "hist", "eval_metric": "logloss", **p}, n_jobs=n_jobs, random_state=SEMILLA, verbosity=0)
    elif modelo == "LGBM":
        from lightgbm import LGBMClassifier

        est = LGBMClassifier(**p, n_jobs=n_jobs, random_state=SEMILLA, verbose=-1)
    else:
        raise ValueError(f"modelo desconocido: {modelo}")
    return Pipeline([("pre", sel), ("est", est)])


# ----------------------------------------------------------------------------- espacios de busqueda
VARIABLES_OPCIONES = ["V16", "V_OBS", "V_OBS_TAM"]

ESPACIOS: dict[str, dict[str, Any]] = {
    # LR: rejilla completa (C de 1e-5 a 100 x class_weight), mas el conjunto de variables
    "LR": {"C": [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0], "class_weight": [None, "balanced"], "variables": VARIABLES_OPCIONES},
    # HGB: incluye valores mas regularizados que EP2 (hojas 2 y 3; min_samples_leaf hasta 3200; l2 hasta 1000)
    "HGB": {
        "learning_rate": loguniform(0.01, 0.2), "max_iter": [30, 60, 100, 200], "max_leaf_nodes": [2, 3, 4, 6, 8, 15],
        "min_samples_leaf": [20, 50, 100, 200, 400, 800, 1600, 3200], "l2_regularization": loguniform(1e-2, 1e3),
        "max_depth": [2, 3, 4, None], "class_weight": [None, "balanced"], "variables": VARIABLES_OPCIONES,
    },
    # RF: min_samples_leaf hasta 1600 (EP2 llegaba a 200 y quedo en el borde); max_features mas bajos que sqrt
    "RF": {
        "max_depth": [3, 4, 6, 8, 12], "min_samples_leaf": [20, 50, 100, 200, 400, 800, 1600],
        "max_features": [1, 2, "sqrt", 0.3, 0.5], "class_weight": [None, "balanced"], "variables": VARIABLES_OPCIONES,
    },
    "XGB": {
        "learning_rate": loguniform(0.01, 0.3), "n_estimators": [30, 60, 100, 200], "max_depth": [1, 2, 3, 4, 6],
        "min_child_weight": [1, 10, 50, 100, 300], "subsample": [0.5, 0.7, 1.0], "colsample_bytree": [0.5, 0.8, 1.0],
        "reg_lambda": loguniform(1e-1, 1e3), "variables": VARIABLES_OPCIONES,
    },
    "LGBM": {
        "learning_rate": loguniform(0.01, 0.3), "n_estimators": [30, 60, 100, 200], "num_leaves": [2, 3, 4, 7, 15, 31],
        "min_child_samples": [20, 50, 100, 200, 400, 800, 1600], "subsample": [0.5, 0.7, 1.0], "subsample_freq": [1],
        "colsample_bytree": [0.5, 0.8, 1.0], "reg_lambda": loguniform(1e-1, 1e3), "variables": VARIABLES_OPCIONES,
    },
}

# hiperparametros ordenados: para detectar optimos en el borde de la grilla
ORDENADOS = {
    "LR": ["C"], "HGB": ["max_leaf_nodes", "min_samples_leaf", "max_iter", "max_depth"],
    "RF": ["max_depth", "min_samples_leaf"], "XGB": ["max_depth", "min_child_weight", "n_estimators"],
    "LGBM": ["num_leaves", "min_child_samples", "n_estimators"],
}

DEFECTOS: dict[str, dict[str, Any]] = {"LR": {}, "RF": {}, "HGB": {}, "XGB": {}, "LGBM": {}}


def configuraciones(modelo: str, n: int = 40, semilla: int = SEMILLA, espacio: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Configuraciones de búsqueda: rejilla completa para LR; muestreo aleatorio (``n``) para el resto."""
    esp = espacio or ESPACIOS[modelo]
    if modelo == "LR":
        from sklearn.model_selection import ParameterGrid

        return list(ParameterGrid(esp))
    return list(ParameterSampler(esp, n, random_state=semilla))


def separar(cfg: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Separa el nombre del conjunto de variables del resto de hiperparámetros."""
    c = dict(cfg)
    return c.pop("variables", "V16"), c


def a_json(cfg: dict[str, Any]) -> dict[str, Any]:
    """Configuración con tipos de numpy convertidos a tipos de Python (para guardar en JSON)."""
    salida = {}
    for k, v in cfg.items():
        if isinstance(v, (np.floating,)):
            v = float(v)
        elif isinstance(v, (np.integer,)):
            v = int(v)
        salida[k] = v
    return salida


def predecir(modelo: Pipeline, X: pd.DataFrame) -> np.ndarray:
    """Probabilidad de la clase positiva."""
    return modelo.predict_proba(X)[:, 1]
