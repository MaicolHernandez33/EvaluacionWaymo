"""Ingesta de segmentos nuevos (P9) desde una carpeta con ``lidar_box/`` y ``camera_to_lidar_box_association/``.

Construye la misma tabla que ``dev_41.parquet`` (16 variables, pares por cámara, ``sin_camara``) para
peatones y ciclistas dentro de 120 grados en frames etiquetados. No abre ningún dato por sí sola:
solo se usa cuando existan segmentos nuevos y la lista esté congelada.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .inferencia import CAMARAS, VRU, agregar_asociacion, construir_variables


def ingestar_segmento(lidar_box: pd.DataFrame, asociacion: pd.DataFrame, az_max: float = 100.0) -> pd.DataFrame:
    """Tabla de un segmento: VRU con |azimut| <= 120, frames etiquetados, ``c1``..``c5`` y ``sin_camara``."""
    v = construir_variables(lidar_box)
    v = v[v["object_type"].isin(VRU) & (v["azimut_abs_deg"] <= 120)].reset_index(drop=True)
    v = agregar_asociacion(v, asociacion, CAMARAS)
    v["seg"] = v["segment_id"].str[:12]
    v["en_zona_principal"] = v["azimut_abs_deg"] <= az_max
    return v


def ingestar_directorio(entrada: Path, lista_csv: Path) -> pd.DataFrame:
    """Ingesta todos los segmentos de ``lista_csv`` (columnas ``segment_id``, ``time_of_day``, ``location``).

    Raises:
        FileNotFoundError: si falta algún parquet de la lista (no se ingiere nada a medias).
    """
    lista = pd.read_csv(lista_csv, dtype=str)
    faltan = [f"{carpeta}/{s}.parquet" for s in lista["segment_id"] for carpeta in ("lidar_box", "camera_to_lidar_box_association")
              if not (entrada / carpeta / f"{s}.parquet").exists()]
    if faltan:
        raise FileNotFoundError("faltan archivos: " + ", ".join(faltan[:6]) + (" ..." if len(faltan) > 6 else ""))
    partes = []
    for r in lista.itertuples(index=False):
        t = ingestar_segmento(pd.read_parquet(entrada / "lidar_box" / f"{r.segment_id}.parquet"),
                              pd.read_parquet(entrada / "camera_to_lidar_box_association" / f"{r.segment_id}.parquet"))
        t["time_of_day"], t["location"], t["grupo"] = getattr(r, "time_of_day", None), getattr(r, "location", None), "nuevo"
        partes.append(t)
    return pd.concat(partes, ignore_index=True)
