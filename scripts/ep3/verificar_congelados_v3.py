"""Verifica la solucion congelada v3: sha256 de modelos, umbrales y detector (manifest_v3.json) y del plan v3.

Uso: python scripts/ep3/verificar_congelados_v3.py        (sale con codigo 1 si algo no coincide)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.plan import verificar_plan_v3  # noqa: E402
from waymo_evaluacion.ep3.sellado import verificar_manifest  # noqa: E402

MOD = RAIZ / "data/06_models_ep3"


def main() -> None:
    total, mal = 0, []
    try:
        planes = verificar_plan_v3(RAIZ)
        total += len(planes)
        print(f"IGUAL    plan v3 ({', '.join(planes)})")
    except RuntimeError as e:
        mal.append(str(e))
        total += 2
    man_ruta = MOD / "manifest_v3.json"
    if not man_ruta.exists():
        sys.exit("FALTA data/06_models_ep3/manifest_v3.json: la solucion v3 aun no se congelo (scripts/ep3/f6_final.py)")
    man = json.loads(man_ruta.read_text(encoding="utf-8"))
    total += len(man["sha256"])
    mal += verificar_manifest(MOD, man)
    for n in man["sha256"]:
        print(("DISTINTO " if any(n in m for m in mal) else "IGUAL    ") + n)
    print(f"v3 congelado el {man['creado']} (candidato {man.get('candidato')}): coinciden {total - len(mal)} de {total} archivos")
    if mal:
        print("DISCREPANCIAS:", "; ".join(mal))
        sys.exit(1)


if __name__ == "__main__":
    main()
