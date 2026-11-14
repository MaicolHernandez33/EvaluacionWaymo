"""Construcción de la tabla de desarrollo de EP3 (41 segmentos) y de sus folds.

Todo se lee de EP2 en modo solo lectura. La tabla replica la lógica del notebook 10
(``pop120``) para los 8 segmentos de test y toma las filas de train de ``features_B.parquet``.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from .detector_huecos import agregar_pares_camara, azimut_con_signo

VRU = ["PEDESTRIAN", "CYCLIST"]
SEMILLAS_CV = (42, 43, 44)
COLS_ID = ["segment_id", "key.frame_timestamp_micros", "key.laser_object_id"]

V_OBS = ["num_lidar_points", "num_top_lidar_points", "densidad_puntos", "distancia_m"]
V_OBS_TAM = V_OBS + ["box_length", "box_width", "box_height", "volumen_caja", "es_ciclista", "speed_mps"]
V_POSICION = ["box_center_x", "box_center_y", "box_center_z", "azimut_abs_deg", "distancia_m", "heading_sin", "heading_cos"]
V_TAMANO = ["box_length", "box_width", "box_height", "volumen_caja", "es_ciclista", "speed_mps"]
V_MIN3 = ["num_lidar_points", "num_top_lidar_points", "azimut_abs_deg"]


def leer_config(raiz: Path) -> dict:
    """Lee ``config_features_B.json`` (solo lectura)."""
    return json.loads((raiz / "data/05_model_input/config_features_B.json").read_text(encoding="utf-8"))


def variables_v16(raiz: Path) -> list[str]:
    """Las 16 variables de EP2, en el orden de ``hiperparametros_B.json``."""
    h = json.loads((raiz / "data/06_models/hiperparametros_B.json").read_text(encoding="utf-8"))
    return list(h["variables"])


def conjuntos_variables(raiz: Path) -> dict[str, list[str]]:
    """Los tres conjuntos declarados en P2 más las vistas de E4 y el modelo mínimo."""
    return {
        "V16": variables_v16(raiz),
        "V_OBS": V_OBS,
        "V_OBS_TAM": V_OBS_TAM,
        "VISTA_OBS": V_OBS,
        "VISTA_TAMANO": V_TAMANO,
        "VISTA_POSICION": V_POSICION,
        "V_MIN3": V_MIN3,
    }


def poblacion_test_120(raiz: Path) -> pd.DataFrame:
    """Reconstruye ``pop120`` del notebook 10 desde ``test.parquet`` (solo lectura)."""
    test = pd.read_parquet(raiz / "data/05_model_input/test.parquet")
    vru = test[test["object_type"].isin(VRU)].copy()
    vru["es_ciclista"] = (vru["object_type"] == "CYCLIST").astype(int)
    vru["sin_camara"] = 1 - vru["tiene_camara"]
    pop = vru[vru["azimut_abs_deg"] <= 120].reset_index(drop=True)
    az_max = leer_config(raiz).get("AZ_MAX", 100)
    pop["en_zona_principal"] = pop["azimut_abs_deg"] <= az_max
    return pop


def construir_dev41(raiz: Path, con_pares: bool = True) -> pd.DataFrame:
    """Tabla de desarrollo con los 41 segmentos (train de EP2 + test de EP2).

    Columnas: identificadores, las 16 variables, ``time_of_day``, ``location``, ``sin_camara``,
    ``en_zona_principal``, ``grupo`` (train o test de EP2), ``fold_ep2`` (-1 en test),
    ``seg`` (12 caracteres), ``az_signed`` y, si ``con_pares``, ``c1`` a ``c5``.
    """
    v16 = variables_v16(raiz)
    cols = COLS_ID + v16 + ["time_of_day", "location", "sin_camara", "en_zona_principal"]
    tr = pd.read_parquet(raiz / "data/05_model_input/features_B.parquet", columns=cols + ["fold"])
    tr = tr.rename(columns={"fold": "fold_ep2"})
    tr["en_zona_principal"] = tr["en_zona_principal"].astype(bool)
    tr["grupo"] = "train"
    te = poblacion_test_120(raiz)[cols].copy()
    te["fold_ep2"] = -1
    te["grupo"] = "test"
    dev = pd.concat([tr, te], ignore_index=True)
    dev["es_ciclista"] = dev["es_ciclista"].astype(int)
    dev["sin_camara"] = dev["sin_camara"].astype(int)
    dev["seg"] = dev["segment_id"].str[:12]
    dev["az_signed"] = azimut_con_signo(dev["box_center_x"], dev["box_center_y"])
    if con_pares:
        cam = pd.read_csv(raiz / "data/08_reporting/08_azimut_por_camara_empirico.csv")
        camaras = sorted(int(str(n).split()[0]) for n in cam["camara"])
        dev = agregar_pares_camara(dev, raiz / "data/01_raw/waymo/camera_to_lidar_box_association", camaras)
    return dev


def crear_folds(dev: pd.DataFrame, semillas: tuple[int, ...] = SEMILLAS_CV, k: int = 5) -> pd.DataFrame:
    """Folds externos StratifiedGroupKFold(k, shuffle) sobre la población principal.

    Estratifica por ``sin_camara`` y agrupa por segmento. Devuelve una tabla indexada como
    ``dev`` con una columna ``fold_s{semilla}`` por repetición (-1 fuera de la población principal).
    """
    ppal = dev["en_zona_principal"].to_numpy()
    idx = np.flatnonzero(ppal)
    y = dev["sin_camara"].to_numpy()[idx]
    g = dev["seg"].to_numpy()[idx]
    salida = pd.DataFrame(index=dev.index)
    for s in semillas:
        f = np.full(len(dev), -1, dtype=int)
        cv = StratifiedGroupKFold(n_splits=k, shuffle=True, random_state=s)
        for n, (_, va) in enumerate(cv.split(np.zeros(len(idx)), y, g)):
            f[idx[va]] = n
        salida[f"fold_s{s}"] = f
    return salida
