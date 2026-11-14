"""Ajuste de los 11 candidatos de P8 sobre un subconjunto de filas, devolviendo un ``Puntuador`` congelable.

Candidatos: ``Regla top``, ``LR3``, ``LR``, ``RF``, ``HGB``, ``XGB``, ``LGBM``, ``E1`` (voting soft LR+RF+HGB),
``E2`` (promedio de rangos de E1 y la regla), ``E3`` (stacking de las 5 bases) y ``E4`` (stacking por vistas).
Los stackings arman sus predicciones de meta-entrenamiento con GroupKFold(3) por segmento dentro del
conjunto de entrenamiento (sin fuga entre segmentos).
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from . import modelos as M
from .congelado import PuntuadorModelo, PuntuadorPromedio, PuntuadorRangos, PuntuadorRegla, PuntuadorStacking

CANDIDATOS = ("Regla top", "LR3", "LR", "RF", "HGB", "XGB", "LGBM", "E1", "E2", "E3", "E4")
BASE = ("LR", "RF", "HGB", "XGB", "LGBM")
NIVEL_SIMPLICIDAD = {"Regla top": 0, "LR3": 1, "LR": 2, "RF": 3, "HGB": 4, "XGB": 5, "LGBM": 5, "E1": 6, "E2": 6, "E3": 7, "E4": 7}
# HGB de las vistas de E4: la regularizacion fuerte que dejo EP2 (hiperparametros_B.json, final.HGB)
CFG_VISTA = {"max_iter": 90, "max_leaf_nodes": 4, "min_samples_leaf": 100, "learning_rate": 0.0305, "l2_regularization": 9.6098}
VISTAS = {"obs": "VISTA_OBS", "tam": "VISTA_TAMANO", "pos": "VISTA_POSICION"}


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p)).reshape(-1, 1)


def _modelo(nombre: str, cfg: tuple[str, dict[str, Any]] | None, X: pd.DataFrame, y: np.ndarray, cj: dict[str, list[str]], n_jobs: int) -> PuntuadorModelo:
    vname, params = cfg if cfg else ("V16", dict(M.DEFECTOS[nombre]))
    cols = cj[vname]
    return PuntuadorModelo(M.construir(nombre, params, cols, n_jobs=n_jobs).fit(X[cols], y), cols)


def _oof_interno(nombre: str, cfg: tuple[str, dict[str, Any]], X: pd.DataFrame, y: np.ndarray, seg: np.ndarray, cj: dict, n_jobs: int) -> np.ndarray:
    oof = np.zeros(len(X))
    for a, b in GroupKFold(n_splits=3).split(np.zeros(len(X)), y, seg):
        oof[b] = _modelo(nombre, cfg, X.iloc[a], y[a], cj, n_jobs).puntuar(X.iloc[b])
    return oof


def ajustar(candidato: str, X: pd.DataFrame, y: np.ndarray, seg: np.ndarray, cj: dict[str, list[str]],
            cfgs: dict[str, tuple[str, dict[str, Any]] | None] | None = None, n_jobs: int = 1) -> Any:
    """Ajusta ``candidato`` con las filas ``X`` (etiqueta ``y``, segmentos ``seg``).

    Args:
        candidato: uno de ``CANDIDATOS``.
        X: tabla con todas las columnas de ``conjuntos_variables.json``.
        cj: conjuntos de variables.
        cfgs: ``{modelo: (conjunto_de_variables, hiperparametros)}`` para las bases; ``None`` o ausente = defecto con V16.
        n_jobs: hilos de los estimadores que los admiten.

    Returns:
        Un ``Puntuador`` con método ``puntuar(DataFrame)``.
    """
    cfgs = cfgs or {}
    if candidato == "Regla top":
        return PuntuadorRegla("num_top_lidar_points")
    if candidato == "LR3":
        return PuntuadorModelo(M.construir("LR", {}, cj["V_MIN3"]).fit(X[cj["V_MIN3"]], y), cj["V_MIN3"])
    if candidato in BASE:
        return _modelo(candidato, cfgs.get(candidato), X, y, cj, n_jobs)
    if candidato in ("E1", "E2"):
        e1 = PuntuadorPromedio([_modelo(m, cfgs.get(m), X, y, cj, n_jobs) for m in ("LR", "RF", "HGB")])
        return e1 if candidato == "E1" else PuntuadorRangos([e1, PuntuadorRegla("num_top_lidar_points")])
    if candidato == "E3":
        bases = [_modelo(m, cfgs.get(m), X, y, cj, n_jobs) for m in BASE]
        Z = np.hstack([_logit(_oof_interno(m, cfgs.get(m) or ("V16", dict(M.DEFECTOS[m])), X, y, seg, cj, n_jobs)) for m in BASE])
        return PuntuadorStacking(bases, LogisticRegression(C=1.0, max_iter=1000).fit(Z, y))
    if candidato == "E4":
        bases, oofs = [], []
        for vn in VISTAS.values():
            cols = cj[vn]
            bases.append(PuntuadorModelo(M.construir("HGB", CFG_VISTA, cols).fit(X[cols], y), cols))
            oof = np.zeros(len(X))
            for a, b in GroupKFold(n_splits=3).split(np.zeros(len(X)), y, seg):
                oof[b] = PuntuadorModelo(M.construir("HGB", CFG_VISTA, cols).fit(X.iloc[a][cols], y[a]), cols).puntuar(X.iloc[b])
            oofs.append(_logit(oof))
        return PuntuadorStacking(bases, LogisticRegression(C=1.0, max_iter=1000).fit(np.hstack(oofs), y))
    raise ValueError(f"candidato desconocido: {candidato}")


def entrada_calibrador(candidato: str) -> str:
    """Transformación del puntaje para la calibración Platt de cada candidato."""
    if candidato == "Regla top":
        return "log_conteo"
    if candidato == "E2":
        return "identidad"
    return "logit"
