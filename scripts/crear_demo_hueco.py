#!/usr/bin/env python
"""
crear_demo_hueco.py (F37)
-------------------------
Fabrica, a partir de un segmento REAL de Waymo (v2), una variante con un "hueco de cámara" SIMULADO para la demostración en vivo de Lente.

Qué hace: borra al azar una fracción de las filas de una cámara en el archivo camera_to_lidar_box_association. El archivo lidar_box NO se toca (si el archivo trae un solo
segmento, se copia byte a byte; si trae varios, se escribe solo el segmento elegido). Así, esa cámara queda con muchas cajas sin pareja 2D, como si hubiera fallado.

IMPORTANTE (honestidad en la presentación): el archivo resultante está modificado a propósito. En la demo hay que decirlo: «esto es una falla de cámara simulada sobre un segmento real».

Cambios de F37 respecto del script recibido (probado antes solo con tablas en memoria): el lidar_box se copia sin releerlo (idéntico byte a byte, con su sha256 en el LEEME), se quitó una
variable sin uso, y el LEEME guarda también el sha256 del archivo original de asociación.

Uso (PowerShell, dentro del .venv del proyecto):

  .venv\\Scripts\\python scripts\\crear_demo_hueco.py ^
      --lidar-box datos_demo\\candidatos\\<segmento>\\lidar_box.parquet ^
      --asociacion datos_demo\\candidatos\\<segmento>\\camera_to_lidar_box_association.parquet ^
      --camara 3 --fraccion 0.95 --semilla 7 ^
      --salida datos_demo\\C_hueco

Si el archivo trae varios segmentos, indique uno con --segmento <context_name>. Requiere pandas y pyarrow (ya los usa el proyecto).
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

NOMBRES_CAMARA = {1: "frontal", 2: "frontal izq.", 3: "frontal der.", 4: "lateral izq.", 5: "lateral der."}


def _col(df: pd.DataFrame, fragmento: str) -> str:
    """Encuentra la columna cuyo nombre contiene `fragmento` (p. ej. 'camera_name')."""
    candidatas = [c for c in df.columns if fragmento in c]
    if not candidatas:
        raise KeyError(f"No encontré una columna con '{fragmento}'. Columnas: {list(df.columns)}")
    candidatas.sort(key=lambda c: (not c.startswith("key."), len(c)))      # prefiere la que empieza con 'key.'
    return candidatas[0]


def quitar_camara(asoc: pd.DataFrame, camara: int, fraccion: float, semilla: int) -> pd.DataFrame:
    """Devuelve `asoc` sin una fracción al azar de las filas de `camara`."""
    if not 0 < fraccion <= 1:
        raise ValueError("--fraccion debe estar entre 0 (exclusivo) y 1")
    asoc = asoc.reset_index(drop=True)                    # F37: con un índice no único (como el que traen algunos parquet crudos) ``drop(index=...)`` borraba filas de todas las cámaras
    c_cam = _col(asoc, "camera_name")
    filas_cam = asoc.index[asoc[c_cam] == camara]
    if len(filas_cam) == 0:
        raise ValueError(f"La cámara {camara} no tiene filas en este archivo.")
    rng = np.random.default_rng(semilla)
    n_quitar = int(round(len(filas_cam) * fraccion))
    quitar = rng.choice(filas_cam.to_numpy(), size=n_quitar, replace=False)
    return asoc.drop(index=quitar).reset_index(drop=True)


def resumen(lidar: pd.DataFrame, asoc: pd.DataFrame, etiqueta: str) -> pd.DataFrame:
    """Filas de asociación por cámara y por caja (todas las cajas del lidar_box, no solo peatones y ciclistas). En ``attrs``: cajas y cajas con alguna pareja 2D (llave fotograma + objeto)."""
    c_cam = _col(asoc, "camera_name")
    n_cajas = len(lidar)
    filas = []
    for cam in sorted(asoc[c_cam].unique()):
        n = int((asoc[c_cam] == cam).sum())
        filas.append({"estado": etiqueta, "camara": int(cam), "nombre": NOMBRES_CAMARA.get(int(cam), "?"), "filas_asociacion": n,
                      "filas_por_caja": round(n / n_cajas, 3) if n_cajas else np.nan})
    df = pd.DataFrame(filas)
    llaves = [_col(lidar, "frame_timestamp_micros"), _col(lidar, "laser_object_id")]
    pares = asoc[[_col(asoc, "frame_timestamp_micros"), _col(asoc, "laser_object_id")]].drop_duplicates()
    pares.columns = llaves
    df.attrs["cajas"] = n_cajas
    df.attrs["cajas_con_pareja"] = int(len(lidar[llaves].drop_duplicates().merge(pares, on=llaves)))
    return df


def sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def main(argv=None, leer=pd.read_parquet, escribir=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lidar-box", required=True)
    ap.add_argument("--asociacion", required=True)
    ap.add_argument("--camara", type=int, required=True, help="1..5")
    ap.add_argument("--fraccion", type=float, default=0.95)
    ap.add_argument("--semilla", type=int, default=7)
    ap.add_argument("--segmento", default=None)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args(argv)

    lidar_completo = leer(a.lidar_box)
    asoc_completo = leer(a.asociacion)
    c_seg_l = _col(lidar_completo, "segment_context_name")
    c_seg_a = _col(asoc_completo, "segment_context_name")
    segs = sorted(set(lidar_completo[c_seg_l]) & set(asoc_completo[c_seg_a]))
    if a.segmento is None:
        if len(segs) != 1:
            print("El archivo trae varios segmentos; use --segmento con uno de:")
            for s in segs:
                print("  ", s)
            return 2
        a.segmento = segs[0]
    un_solo_segmento = lidar_completo[c_seg_l].nunique() == 1
    lidar = lidar_completo[lidar_completo[c_seg_l] == a.segmento].reset_index(drop=True)
    asoc = asoc_completo[asoc_completo[c_seg_a] == a.segmento].reset_index(drop=True)

    antes = resumen(lidar, asoc, "antes")
    asoc2 = quitar_camara(asoc, a.camara, a.fraccion, a.semilla)
    despues = resumen(lidar, asoc2, "despues")
    sin_antes = 100 * (1 - antes.attrs["cajas_con_pareja"] / antes.attrs["cajas"])
    sin_desp = 100 * (1 - despues.attrs["cajas_con_pareja"] / despues.attrs["cajas"])
    print(f"Segmento: {a.segmento}")
    print(f"Cajas: {antes.attrs['cajas']}")
    print(pd.concat([antes, despues]).to_string(index=False))
    print(f"\nCajas sin ninguna pareja 2D (todas las cajas del archivo, no solo peatones y ciclistas) {sin_antes:.1f} % -> {sin_desp:.1f} %")

    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    f_lidar = out / "lidar_box.parquet"
    f_asoc = out / f"camera_to_lidar_box_association__SIMULADO_hueco_cam{a.camara}.parquet"
    if escribir is None:
        if un_solo_segmento:
            shutil.copyfile(a.lidar_box, f_lidar)             # idéntico byte a byte al original
        else:
            lidar.to_parquet(f_lidar, index=False)
        asoc2.to_parquet(f_asoc, index=False)
    else:
        escribir(lidar, f_lidar)
        escribir(asoc2, f_asoc)

    copia = "copia byte a byte del original" if (escribir is None and un_solo_segmento) else "reescrito (solo el segmento elegido)"
    (out / "LEEME_SIMULADO.txt").write_text(
        "ARCHIVO MODIFICADO A PROPOSITO (falla de camara simulada)\n"
        f"Segmento real: {a.segmento}\n"
        f"Camara afectada: {a.camara} ({NOMBRES_CAMARA.get(a.camara, '?')})\n"
        f"Fraccion de filas borradas: {a.fraccion}\n"
        f"Semilla: {a.semilla}\n"
        f"lidar_box.parquet: sin cambios ({copia})\n"
        + (f"sha256 lidar_box.parquet: {sha256(f_lidar)}\n" if escribir is None else "")
        + (f"sha256 asociacion original: {sha256(Path(a.asociacion))}\n" if escribir is None else "")
        + f"Cajas sin ninguna pareja 2D (todas las cajas): {sin_antes:.1f} % -> {sin_desp:.1f} %\n",
        encoding="utf-8",
    )
    print(f"\nListo. Archivos en: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
