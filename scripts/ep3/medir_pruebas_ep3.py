"""F38: corre SOLO las pruebas de EP3 (``pytest tests/ep3``, el comando permitido) con cobertura de ``src/waymo_evaluacion/ep3`` y escribe ``data/08_reporting_ep3/pruebas_ep3_resultado.json``.

El README lo cita. No toca nada de EP2 (``scripts/medir_pruebas.py`` es el de EP2 y excluye ``tests/ep3``). Uso: .venv\Scripts\python scripts/ep3/medir_pruebas_ep3.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "data/08_reporting_ep3/pruebas_ep3_resultado.json"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cov_ep3_") as tmp:
        cov = Path(tmp) / "cov.json"
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/ep3", "-q", "-p", "no:cacheprovider", "--cov=src/waymo_evaluacion/ep3", f"--cov-report=json:{cov}"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
        resumen = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        n = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped)", resumen)}
        total = json.loads(cov.read_text(encoding="utf-8"))["totals"]["percent_covered"] if cov.exists() else None
    out = {"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "pasadas": n.get("passed", 0), "falladas": n.get("failed", 0), "omitidas": n.get("skipped", 0), "cobertura_total_pct": total,
           "comando": "python -m pytest tests/ep3 -q -p no:cacheprovider --cov=src/waymo_evaluacion/ep3", "resumen_pytest": resumen}
    SALIDA.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
