"""Alternativas congeladas ANTES de abrir los segmentos nuevos (F19-A4b; DEV-4: post hoc respecto del plan v3, no cambia la solución elegida).

La solución v3 es la propia regla «menos puntos del sensor superior», así que «solución contra regla» da diferencia 0 por construcción. Para que la validación
externa pueda decir algo más, se congelan dos alternativas ya evaluadas en desarrollo, LR3 (regresión logística de 3 variables) y XGBoost, entrenadas con los 41
segmentos. Se guardan aparte (``alternativas_v3.joblib`` y ``manifest_alternativas.json``): NO se toca ``manifest_v3.json``.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from .plan import sha256_archivo

ARCHIVO = "alternativas_v3.joblib"
MANIFEST = "manifest_alternativas.json"
COLUMNAS_FIJAS = ("modelo", "etapa", "fold", "variables")


def config_mas_frecuente(config_por_fold: pd.DataFrame, modelo: str, etapa: str = "principal") -> tuple[str, dict[str, Any], int, int, str]:
    """Configuración (conjunto de variables e hiperparámetros) que más folds externos eligieron en F3 para ``modelo``.

    Regla: se cuentan las configuraciones idénticas entre los folds de la etapa dada; gana la más repetida. Si hay empate, la del fold de menor índice entre las empatadas
    (regla de desempate fijada aquí, antes de abrir datos). Devuelve ``(variables, hiperparametros, folds_que_la_eligieron, folds_totales, regla_aplicada)``.
    """
    d = config_por_fold[(config_por_fold["modelo"] == modelo) & (config_por_fold["etapa"] == etapa)]
    if d.empty:
        raise ValueError(f"no hay configuraciones de {modelo} en la etapa {etapa}")
    d = d.dropna(axis=1, how="all").sort_values("fold")
    cols = [c for c in d.columns if c not in COLUMNAS_FIJAS]
    claves = d[["variables", *cols]].astype(str).agg("|".join, axis=1)
    cuenta = claves.value_counts()
    mejores = cuenta[cuenta == cuenta.max()].index
    elegida = d[claves.isin(mejores)].iloc[0]                       # empate: el fold de menor indice
    params: dict[str, Any] = {}
    for c in cols:
        v = elegida[c]
        params[c] = int(v) if float(v).is_integer() and c in {"max_depth", "n_estimators", "min_child_weight", "max_iter", "max_leaf_nodes", "min_samples_leaf", "min_child_samples", "num_leaves"} else float(v)
    regla = "la más repetida entre los folds externos" + ("" if len(mejores) == 1 else "; empate resuelto con el fold de menor índice")
    return str(elegida["variables"]), params, int(cuenta.max()), int(len(d)), regla


def guardar_alternativas(alternativas: dict[str, Any], carpeta: Path, extras: dict[str, Any]) -> dict[str, Any]:
    """Escribe ``alternativas_v3.joblib`` y ``manifest_alternativas.json`` (con sha256). Se niega a sobrescribir."""
    if (carpeta / ARCHIVO).exists() or (carpeta / MANIFEST).exists():
        raise FileExistsError("las alternativas ya están congeladas; no se sobrescriben")
    carpeta.mkdir(parents=True, exist_ok=True)
    joblib.dump(alternativas, carpeta / ARCHIVO)
    man = {"version": "alternativas_v3", "creado": time.strftime("%Y-%m-%dT%H:%M:%S"), "sha256": {ARCHIVO: sha256_archivo(carpeta / ARCHIVO)}, "alternativas": sorted(alternativas),
           "nota": "independiente de manifest_v3.json; post hoc respecto del plan v3 (DEV-4); no cambia la solución elegida", **extras}
    import json

    (carpeta / MANIFEST).write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding="utf-8")
    return man


def verificar_alternativas(carpeta: Path, manifest: Path | None = None) -> list[str]:
    """Discrepancias entre ``manifest_alternativas.json`` y el archivo actual (vacía si coincide)."""
    import json

    m = json.loads((manifest or carpeta / MANIFEST).read_text(encoding="utf-8"))
    mal = []
    for n, h in m["sha256"].items():
        ruta = carpeta / n
        if not ruta.exists():
            mal.append(f"falta {n}")
        elif sha256_archivo(ruta) != h:
            mal.append(f"{n} cambió")
    return mal


def cargar_alternativas(carpeta: Path) -> dict[str, Any]:
    """Puntuadores alternativos (nombre -> objeto con ``puntuar``)."""
    return joblib.load(carpeta / ARCHIVO)
