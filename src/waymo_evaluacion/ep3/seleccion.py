"""Utilidades de selección de F3 a F6: veredictos de IE9 y configuración final de cada modelo base."""
from __future__ import annotations

import glob
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from . import modelos as M


def veredictos(rep: Path) -> dict[str, str]:
    """Veredicto «mejora» o «no mejora» de IE9 por modelo (vacío si F3 aún no se analizó)."""
    f = rep / "f3_defecto_vs_optimizado.csv"
    if not f.exists():
        return {}
    return dict(pd.read_csv(f)[["modelo", "veredicto"]].itertuples(index=False, name=None))


def config_final(rep: Path, modelo: str, ver: dict[str, str], semilla: int = 42) -> tuple[str, dict[str, Any]] | None:
    """Configuración del modelo base para el ajuste final.

    Si F3 dio «mejora», la de mayor PR-AUC interno medio entre los 5 folds externos (la etapa ``ext`` reemplaza a la
    principal cuando existe). Si no, ``None`` (hiperparámetros por defecto con V16).
    """
    if ver.get(modelo) != "mejora":
        return None
    for etapa in ("ext", "principal"):
        res = [joblib.load(p) for p in sorted(glob.glob(str(rep / "f3_ckpt" / f"{etapa}_{modelo}_s{semilla}_f*.pkl")))]
        if len(res) == 5:
            media = np.mean([r["ap_interno_todas"] for r in res], axis=0)
            return M.separar(res[0]["cfgs"][int(np.argmax(media))])
    return None
