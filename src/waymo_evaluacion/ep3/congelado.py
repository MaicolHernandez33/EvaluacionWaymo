"""Objetos de puntuación serializables (joblib) para congelar la solución final de EP3.

Cada ``Puntuador`` recibe un ``DataFrame`` con las columnas de EP2 (las 16 variables) y devuelve un
puntaje por fila (mayor = más probable que la caja no tenga su par de cámara). Se importan por su
ruta de módulo, así que este archivo no debe renombrarse después de congelar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


@dataclass
class PuntuadorRegla:
    """Regla simple: menos puntos LiDAR primero (puntaje = -valor de ``columna``)."""

    columna: str = "num_top_lidar_points"
    tipo: str = "regla"

    def puntuar(self, X: pd.DataFrame) -> np.ndarray:
        return -X[self.columna].to_numpy(dtype=float)


@dataclass
class PuntuadorModelo:
    """Un ``Pipeline`` de scikit-learn con su lista de columnas de entrada."""

    modelo: Pipeline
    columnas: list[str]
    tipo: str = "modelo"

    def puntuar(self, X: pd.DataFrame) -> np.ndarray:
        return self.modelo.predict_proba(X[self.columnas])[:, 1]


@dataclass
class PuntuadorPromedio:
    """Voting soft: promedio de las probabilidades de varios puntuadores (E1)."""

    componentes: list[Any]
    tipo: str = "promedio"

    def puntuar(self, X: pd.DataFrame) -> np.ndarray:
        return np.mean([c.puntuar(X) for c in self.componentes], axis=0)


@dataclass
class PuntuadorRangos:
    """Promedio de los rangos percentiles (dentro del lote que se puntúa) de varios puntuadores (E2)."""

    componentes: list[Any]
    tipo: str = "rangos"

    def puntuar(self, X: pd.DataFrame) -> np.ndarray:
        n = len(X)
        return np.mean([rankdata(c.puntuar(X)) for c in self.componentes], axis=0) / max(n, 1)


@dataclass
class PuntuadorStacking:
    """Stacking: los puntuadores base alimentan a un meta-modelo logístico (E3 y E4)."""

    bases: list[Any]
    meta: LogisticRegression
    tipo: str = "stacking"

    def puntuar(self, X: pd.DataFrame) -> np.ndarray:
        Z = np.hstack([_logit(b.puntuar(X)).reshape(-1, 1) for b in self.bases])
        return self.meta.predict_proba(Z)[:, 1]


@dataclass
class CalibradorPlatt:
    """Calibración Platt: regresión logística sobre una transformación del puntaje.

    ``entrada``: ``"logit"`` (puntaje en (0,1)), ``"log_conteo"`` (regla de puntos: -log1p(conteo)) o ``"identidad"``.
    """

    lr: LogisticRegression
    entrada: str = "logit"
    nota: str = field(default="ajustado con scores internos (OOF por segmento) del conjunto de desarrollo")

    def _feat(self, s: np.ndarray) -> np.ndarray:
        s = np.asarray(s, dtype=float)
        if self.entrada == "logit":
            return _logit(s).reshape(-1, 1)
        if self.entrada == "log_conteo":
            return (-np.log1p(-s)).reshape(-1, 1)
        return s.reshape(-1, 1)

    def calibrar(self, s: np.ndarray) -> np.ndarray:
        return self.lr.predict_proba(self._feat(s))[:, 1]
