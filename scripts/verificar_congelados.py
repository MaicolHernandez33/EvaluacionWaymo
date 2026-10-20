"""Verifica que los archivos congelados coinciden con los sha256 del plan de evaluacion v2, antes de ejecutar el notebook 10.

Uso: .venv/Scripts/python.exe -X utf8 scripts/verificar_congelados.py
Sale con codigo 1 si algun archivo cambio. Si reejecutaste el 09 o el 09b, restaura data/06_models/ y data/05_model_input/features_B.parquet
desde el paquete original (entrega_EP2.zip): el 09 reescribe plan_evaluacion_test.json con el plan v1 y puede cambiar un decimal de un umbral.
"""
import hashlib
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
plan = json.loads((R / "data" / "06_models" / "plan_evaluacion_test.json").read_text(encoding="utf-8"))
if plan.get("version") != "v2":
    sys.exit("ERROR: data/06_models/plan_evaluacion_test.json no es el plan v2 (el 09 lo sobrescribe con el v1). Restaura los archivos congelados desde el paquete original.")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
filas = []
for n, esperado in plan["sha256"]["archivos"].items():
    p = R / ("data/05_model_input" if n == "config_features_B.json" else "data/06_models") / n
    filas.append((n, p.exists() and sha(p) == esperado))
filas.append(("features_B.parquet", sha(R / "data/05_model_input/features_B.parquet") == plan["sha256"]["features_B.parquet"]))
filas.append(("plan_evaluacion_test_v1.json", sha(R / "data/06_models/plan_evaluacion_test_v1.json") == plan["sha256"]["plan_v1_json"]))
for n, ok in filas:
    print(f"{'IGUAL   ' if ok else 'DISTINTO'} {n}")
print(f"Plan {plan['version']} congelado el {plan['congelado']}: coinciden {sum(ok for _, ok in filas)} de {len(filas)} archivos")
sys.exit(0 if all(ok for _, ok in filas) else 1)
