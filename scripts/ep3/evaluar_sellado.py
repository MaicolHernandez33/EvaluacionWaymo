"""Evaluacion externa sellada (P9). Se ejecuta UNA sola vez; se niega a correr una segunda.

Dos pasos:
  1) congelar:  python scripts/ep3/evaluar_sellado.py congelar --lista segmentos_nuevos_ep3.csv
     Verifica el manifest v3 y escribe data/06_models_ep3/manifest_nuevos.json con el sha256 de la lista y del manifest.
     Debe hacerse ANTES de ingerir u abrir los segmentos nuevos.
  2) evaluar:   python scripts/ep3/evaluar_sellado.py evaluar --lista segmentos_nuevos_ep3.csv
     Verifica todos los hashes, toma el candado (data/08_reporting_ep3/evaluacion_externa.lock) y escribe
     data/08_reporting_ep3/externa_*.csv. Nada de lo que salga se usa para elegir ni reajustar.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.inferencia import cargar_artefactos  # noqa: E402
from waymo_evaluacion.ep3.plan import verificar_plan_v3  # noqa: E402
from waymo_evaluacion.ep3.sellado import CandadoError, congelar_lista, evaluar_externo, tomar_candado, verificar_sellado  # noqa: E402

MOD = RAIZ / "data/06_models_ep3"
REP = RAIZ / "data/08_reporting_ep3"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["congelar", "evaluar"])
    ap.add_argument("--lista", required=True, type=Path)
    a = ap.parse_args()
    verificar_plan_v3(RAIZ)
    try:
        if a.accion == "congelar":
            man = congelar_lista(a.lista, MOD, MOD / "manifest_nuevos.json")
            print("Lista congelada:", man)
            return
        verificar_sellado(a.lista, MOD, MOD / "manifest_nuevos.json")
        tomar_candado(REP / "evaluacion_externa.lock", {"lista": a.lista.name})
    except CandadoError as e:
        sys.exit(f"DETENIDO: {e}")
    nuevos = pd.read_parquet(RAIZ / "data/05_model_input_ep3/nuevos.parquet")
    res = evaluar_externo(nuevos, cargar_artefactos(MOD))
    for k, v in res.items():
        v.to_csv(REP / f"externa_{k}.csv", index=False)
        print(f"\n== {k}\n{v.round(4).to_string(index=False)}")


if __name__ == "__main__":
    main()
