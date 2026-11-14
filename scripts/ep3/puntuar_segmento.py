"""CLI: puntua un segmento con la solucion congelada v3 y arma las listas A y B (todo local).

Uso:
  python scripts/ep3/puntuar_segmento.py --lidar-box RUTA_lidar_box.parquet [--asociacion RUTA_asoc.parquet]
         [--artefactos data/06_models_ep3] [--salida CARPETA]

Sin --salida solo imprime el resumen. Con --salida escribe lista_A.csv, lista_B.csv y cajas.csv en esa carpeta.
Los datos de Waymo no salen de este equipo: el script no usa la red.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.inferencia import cargar_artefactos, puntuar_segmento  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lidar-box", required=True, type=Path)
    ap.add_argument("--asociacion", type=Path)
    ap.add_argument("--artefactos", type=Path, default=RAIZ / "data/06_models_ep3")
    ap.add_argument("--salida", type=Path)
    ap.add_argument("--ocultar-ids", action="store_true", help="modo presentacion: no escribe laser_object_id ni marcas de tiempo")
    a = ap.parse_args()
    art = cargar_artefactos(a.artefactos)
    asoc = pd.read_parquet(a.asociacion) if a.asociacion else None
    r = puntuar_segmento(pd.read_parquet(a.lidar_box), asoc, art)
    print(json.dumps(r.resumen, ensure_ascii=False, indent=1))
    for adv in r.advertencias:
        print("ADVERTENCIA:", adv)
    print("\nLista A (celdas con hueco):")
    print(r.lista_A.round(3).to_string(index=False) if len(r.lista_A) else "  (ninguna)")
    if a.salida:
        a.salida.mkdir(parents=True, exist_ok=True)
        ids = ["key.frame_timestamp_micros", "key.laser_object_id"]
        quitar = ids if a.ocultar_ids else []
        r.lista_A.to_csv(a.salida / "lista_A.csv", index=False)
        r.lista_B.drop(columns=quitar).to_csv(a.salida / "lista_B.csv", index=False)
        r.cajas.drop(columns=quitar).to_csv(a.salida / "cajas.csv", index=False)
        print("\nEscrito en", a.salida)


if __name__ == "__main__":
    main()
