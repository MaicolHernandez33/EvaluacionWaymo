"""Ingesta de segmentos nuevos (P9). NO se ejecuta hasta que existan los segmentos y la lista este congelada.

Uso:  python scripts/ep3/ingesta_nuevos.py --entrada CARPETA_DESCOMPRIMIDA --lista segmentos_nuevos_ep3.csv

CARPETA_DESCOMPRIMIDA contiene lidar_box/ y camera_to_lidar_box_association/ (salida del notebook 00b en Colab).
Escribe data/05_model_input_ep3/nuevos.parquet y data/08_reporting_ep3/nuevos_resumen.csv. Se niega a sobrescribir un nuevos.parquet existente (salvo --forzar).
Para un ENSAYO (F19-A3) use --salida y --resumen con rutas alternativas: asi no se toca el nuevos.parquet real.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.ingesta_nuevos import ingestar_directorio  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", required=True, type=Path)
    ap.add_argument("--lista", required=True, type=Path)
    ap.add_argument("--salida", type=Path, default=RAIZ / "data/05_model_input_ep3/nuevos.parquet", help="parquet de salida (por defecto el real)")
    ap.add_argument("--resumen", type=Path, default=RAIZ / "data/08_reporting_ep3/nuevos_resumen.csv", help="CSV de resumen por segmento (por defecto el real)")
    ap.add_argument("--forzar", action="store_true", help="sobrescribir un nuevos.parquet existente")
    a = ap.parse_args(argv)
    if a.salida.exists() and not a.forzar:
        sys.exit(f"DETENIDO: ya existe {a.salida}; no se sobrescribe (use --forzar solo si sabe lo que hace).")
    t = ingestar_directorio(a.entrada, a.lista)
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.resumen.parent.mkdir(parents=True, exist_ok=True)
    t.to_parquet(a.salida, index=False)
    res = t.groupby("seg").agg(filas=("sin_camara", "size"), filas_principal=("en_zona_principal", "sum"), time_of_day=("time_of_day", "first"), location=("location", "first"))
    res.to_csv(a.resumen)
    print(res.to_string())
    print(f"{len(t):,} filas en {t['seg'].nunique()} segmentos -> {a.salida}")


if __name__ == "__main__":
    main()
