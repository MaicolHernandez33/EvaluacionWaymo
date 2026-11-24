"""F25: corre la suite de EP3 con el comando permitido y registra el resultado en docs/ep3/f25_resultado_suite.json (lo lee generar_reporte_f25.py).

Solo corre ``python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider`` (nunca ``pytest`` sin ruta). La línea base de antes de F25 (240 aprobadas, de la suite de cierre de F24) se pasa con ``--antes``.
Uso: .venv\Scripts\python scripts/ep3/f25_registrar_suite.py --antes 240
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from f23_registrar_suite import COMANDO, correr  # noqa: E402

SALIDA = RAIZ / "docs/ep3/f25_resultado_suite.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--antes", type=int, required=True)
    a = ap.parse_args()
    salida = correr(["tests/ep3", "-q", "--no-cov", "-p", "no:cacheprovider"])
    resumen = re.findall(r"(\d+) (passed|failed|skipped|error|errors)", salida.splitlines()[-1] if salida.strip() else "")
    cuenta = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "errors": 0}
    for n, k in resumen:
        cuenta[k] += int(n)
    dur = re.search(r"in ([\d.]+)s", salida)
    colecta = correr(["tests/ep3/test_pagina_f25.py", "--collect-only", "-q", "--no-cov", "-p", "no:cacheprovider"])
    nuevas = len([linea for linea in colecta.splitlines() if "::test_" in linea])
    datos = {"comando": COMANDO, "antes": {"pasaron": a.antes},
             "despues": {"pasaron": cuenta["passed"], "fallaron": cuenta["failed"] + cuenta["error"] + cuenta["errors"], "omitidas": cuenta["skipped"],
                         "duracion_s": float(dur.group(1)) if dur else None, "nuevas_f25": nuevas}}
    SALIDA.write_text(json.dumps(datos, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(datos, ensure_ascii=False))
    if datos["despues"]["fallaron"]:
        print(salida[-3000:])
        sys.exit(1)


if __name__ == "__main__":
    main()
