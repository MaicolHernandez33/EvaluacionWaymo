"""F23: corre la suite de EP3 con el comando permitido y registra el resultado en docs/ep3/f23_resultado_suite.json (lo lee generar_reporte_f23.py).

Solo corre ``python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider`` (nunca ``pytest`` sin ruta: reescribe README, informe y parquets de EP2). La línea base de antes de F23
(200 aprobadas, medida en el paso 0 con el mismo comando) se pasa con ``--antes``.
Uso: .venv\\Scripts\\python scripts/ep3/f23_registrar_suite.py --antes 200 --antes-segundos 76.9
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "docs/ep3/f23_resultado_suite.json"
COMANDO = "python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider"


def correr(args: list[str]) -> str:
    r = subprocess.run([sys.executable, "-m", "pytest", *args], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    return (r.stdout or "") + (r.stderr or "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--antes", type=int, required=True)
    ap.add_argument("--antes-segundos", type=float, default=0.0)
    a = ap.parse_args()
    salida = correr(["tests/ep3", "-q", "--no-cov", "-p", "no:cacheprovider"])
    resumen = re.findall(r"(\d+) (passed|failed|skipped|error|errors)", salida.splitlines()[-1] if salida.strip() else "")
    cuenta = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "errors": 0}
    for n, k in resumen:
        cuenta[k] += int(n)
    dur = re.search(r"in ([\d.]+)s", salida)
    colecta = correr(["tests/ep3/test_pagina_f23.py", "--collect-only", "-q", "--no-cov", "-p", "no:cacheprovider"])
    nuevas = len([l for l in colecta.splitlines() if "::test_" in l])
    datos = {"comando": COMANDO, "antes": {"pasaron": a.antes, "duracion_s": a.antes_segundos},
             "despues": {"pasaron": cuenta["passed"], "fallaron": cuenta["failed"] + cuenta["error"] + cuenta["errors"], "omitidas": cuenta["skipped"], "duracion_s": float(dur.group(1)) if dur else None, "nuevas_f23": nuevas}}
    SALIDA.write_text(json.dumps(datos, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(datos, ensure_ascii=False))
    if datos["despues"]["fallaron"]:
        print(salida[-3000:])
        sys.exit(1)


if __name__ == "__main__":
    main()
