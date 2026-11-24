"""Datos sintéticos para probar que la página escala a cientos de segmentos (F31 y F32). Se generan en memoria o en un directorio temporal: no se guardan en el repositorio ni tocan los datos reales.

``celdas_sinteticas`` imita el formato de ``celdas.csv`` y ``lista_A.csv``; ``cajas_sinteticas`` imita las columnas de ``cajas_oof.parquet`` que usa la Cola de revisión.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CAMARAS = {1: "1 (frontal)", 2: "2 (frontal izq.)", 3: "3 (frontal der.)", 4: "4 (lateral izq.)", 5: "5 (lateral der.)"}


def _ids(n: int, rng: np.random.Generator) -> list[str]:
    """``n`` identificadores de segmento distintos de 12 dígitos, todos con distintos 6 últimos dígitos (como en los datos reales)."""
    vistos: set[str] = set()
    out: list[str] = []
    while len(out) < n:
        s = str(int(rng.integers(10 ** 11, 10 ** 12)))
        if s[-6:] not in vistos:
            vistos.add(s[-6:])
            out.append(s)
    return out


def celdas_sinteticas(n_segmentos: int = 300, fraccion_marcada: float = 0.015, semilla: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """``(celdas, lista_A)``: ``n_segmentos`` segmentos con 5 cámaras cada uno y una fracción de celdas marcadas como hueco (al menos 2). La Lista A trae las columnas de la real."""
    rng = np.random.default_rng(semilla)
    seg = _ids(n_segmentos, rng)
    celdas = pd.DataFrame({"seg": seg, "grupo": np.where(rng.random(n_segmentos) < 0.8, "train", "test"), "ubicacion": rng.choice(["location_sf", "location_phx", "location_other"], n_segmentos),
                           "momento": rng.choice(["Day", "Night", "Dawn/Dusk"], n_segmentos), "cajas": rng.integers(300, 1500, n_segmentos)})
    for c in CAMARAS:
        celdas[f"tasa_c{c}"] = rng.uniform(0.45, 1.0, n_segmentos)
        celdas[f"n_rango_c{c}"] = rng.integers(40, 500, n_segmentos)
        celdas[f"hueco_c{c}"] = False
    k = max(2, int(round(n_segmentos * 5 * fraccion_marcada)))
    marcadas = rng.choice(n_segmentos * 5, size=k, replace=False)
    filas = []
    for celda in marcadas:
        i, c = int(celda) // 5, int(celda) % 5 + 1
        celdas.loc[i, f"hueco_c{c}"], celdas.loc[i, f"tasa_c{c}"], celdas.loc[i, f"n_rango_c{c}"] = True, 0.0, int(rng.integers(150, 400))
        afectadas = int(celdas.loc[i, f"n_rango_c{c}"] * rng.uniform(0.8, 0.95))
        filas.append({"segmento": celdas.loc[i, "seg"], "grupo": celdas.loc[i, "grupo"], "ubicacion": celdas.loc[i, "ubicacion"], "momento": celdas.loc[i, "momento"], "camara": CAMARAS[c], "tasa": 0.0,
                      "mediana_camara": 0.9, "umbral": 0.225, "cajas_en_rango": int(celdas.loc[i, f"n_rango_c{c}"]), "cajas_afectadas_poblacion_principal": afectadas,
                      "positivos_afectados": int(afectadas * rng.uniform(0.6, 0.9))})
    celdas["algun_hueco"] = celdas[[f"hueco_c{c}" for c in CAMARAS]].any(axis=1)
    return celdas, pd.DataFrame(filas)


def cajas_sinteticas(n_segmentos: int = 300, cajas_por_segmento: int = 40, semilla: int = 42) -> pd.DataFrame:
    """Cajas con las columnas que usa la Cola de revisión (puntaje, probabilidad calibrada, azimut, identificadores y marca de hueco), ``n_segmentos`` × ``cajas_por_segmento`` filas."""
    rng = np.random.default_rng(semilla)
    seg = np.repeat(_ids(n_segmentos, rng), cajas_por_segmento)
    n = len(seg)
    puntos = rng.integers(0, 400, n)
    prob = np.clip(0.9 * np.exp(-puntos / 40.0) + rng.normal(0, 0.02, n), 0.002, 0.95)
    largo, ancho, alto = rng.uniform(0.4, 1.0, n), rng.uniform(0.4, 1.0, n), rng.uniform(1.4, 2.0, n)
    rumbo = rng.uniform(-np.pi, np.pi, n)
    num_lidar = puntos + rng.integers(0, 50, n)
    return pd.DataFrame({"seg": seg, "grupo": "train", "ubicacion": "location_sf", "momento": "Day", "key.frame_timestamp_micros": rng.integers(10 ** 15, 10 ** 15 + 10 ** 9, n),
                         "box_center_x": rng.uniform(-60, 60, n), "box_center_y": rng.uniform(-60, 60, n), "box_center_z": rng.uniform(0, 2, n), "box_length": largo, "box_width": ancho,
                         "box_height": alto, "volumen_caja": largo * ancho * alto, "densidad_puntos": num_lidar / (largo * ancho * alto), "speed_mps": rng.uniform(0, 3, n),
                         "heading_sin": np.sin(rumbo), "heading_cos": np.cos(rumbo),
                         "key.laser_object_id": [f"obj{int(x):08d}" for x in rng.integers(0, 10 ** 7, n)], "sin_camara": (rng.random(n) < prob).astype(int), "az_signed": rng.uniform(-100, 100, n),
                         "azimut_abs_deg": rng.uniform(0, 100, n), "distancia_m": rng.uniform(2, 80, n), "num_lidar_points": puntos + rng.integers(0, 50, n), "num_top_lidar_points": puntos,
                         "es_ciclista": (rng.random(n) < 0.05).astype(int), "prob_cal": prob, "score": -puntos.astype(float), "en_hueco": rng.random(n) < 0.02, "tipo_caso": "lejanos y poco densos"})
