"""F18-B4: calcula, SIN descargar nada, el plan de seleccion de segmentos nuevos (parametros, cuotas, embudo y orden de candidatos por estrato).

Lee docs/seleccion_segmentos/inventario_segmentos.csv y registro_verificacion_ep2.csv (solo lectura) y escribe docs/ep3/plan_seleccion_ep3.json
y docs/ep3/plan_seleccion_ep3.sha256. El embudo debe dar 793, 786 y 746 (como en EP2); si no coincide, se detiene.
Para que la garantia de sellado valga, el plan y el manifest v3 deben quedar commiteados ANTES de ejecutar el Colab.
Uso: .venv\Scripts\python scripts/ep3/plan_seleccion_ep3.py            (escribe)   |   ... --verificar   (solo comprueba que el JSON coincide con el calculo)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.seleccion_nuevos import construir_plan  # noqa: E402

CSV = RAIZ / "docs/seleccion_segmentos"
SALIDA = RAIZ / "docs/ep3/plan_seleccion_ep3.json"
HASH = RAIZ / "docs/ep3/plan_seleccion_ep3.sha256"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def calcular() -> dict:
    inv = pd.read_csv(CSV / "inventario_segmentos.csv", dtype={"segment_id": str})
    reg = pd.read_csv(CSV / "registro_verificacion_ep2.csv", dtype={"segment_id": str})
    assert len(inv) == 798 and len(reg) == 91, (len(inv), len(reg))
    plan = construir_plan(inv, reg["segment_id"], {n: sha(CSV / n) for n in ("inventario_segmentos.csv", "registro_verificacion_ep2.csv", "diagnostico_lluvia_ep2.csv")})
    e = plan["embudo"]
    if (e["sin_lluvia"], e["n_frames_>=190"], e["n_detecciones_entre_percentiles"]) != (793, 786, 746):
        raise SystemExit(f"DETENIDO: el embudo no coincide con EP2 (793, 786, 746): {e}")
    return plan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verificar", action="store_true")
    a = ap.parse_args()
    plan = calcular()
    if a.verificar:
        previo = json.loads(SALIDA.read_text(encoding="utf-8"))
        ok = previo == plan and HASH.read_text(encoding="utf-8").split()[0] == sha(SALIDA)
        print("plan de seleccion:", "coincide" if ok else "NO COINCIDE")
        sys.exit(0 if ok else 1)
    if SALIDA.exists():
        raise SystemExit("el plan ya existe (esta pensado para declararse una sola vez); use --verificar")
    SALIDA.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    HASH.write_text(f"{sha(SALIDA)}  {SALIDA.name}\n", encoding="utf-8")
    print(json.dumps({k: plan[k] for k in ("cuotas_utiles", "total_cuota", "embudo", "candidatos_por_estrato")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
