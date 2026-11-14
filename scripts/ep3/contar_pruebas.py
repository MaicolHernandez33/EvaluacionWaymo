"""Cuenta las pruebas de EP3 SIN ejecutarlas: `python -m pytest tests/ep3 --collect-only -q --no-cov -p no:cacheprovider`.

Escribe data/08_reporting_ep3/pruebas_ep3_conteo.json (recolectadas, por archivo, total EP2 + EP3). Los documentos leen de ahi; nada se escribe a mano.
El conteo de EP2 (81) sale de data/08_reporting/pytest_resumen.json (solo lectura).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "data/08_reporting_ep3/pruebas_ep3_conteo.json"
CMD = ["-m", "pytest", "tests/ep3", "--collect-only", "-q", "--no-cov", "-p", "no:cacheprovider"]


def main() -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run([sys.executable, *CMD], cwd=RAIZ, capture_output=True, text=True, env=env, timeout=600)
    ids = [l.strip() for l in r.stdout.splitlines() if re.match(r"tests[/\\]ep3[/\\]\S+\.py::", l.strip())]
    if r.returncode != 0 or not ids:
        raise SystemExit(f"no se pudo recolectar (codigo {r.returncode}):\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    por_archivo = Counter(i.split("::")[0].replace("\\", "/") for i in ids)
    ep2 = int(json.loads((RAIZ / "data/08_reporting/pytest_resumen.json").read_text(encoding="utf-8"))["pasadas"]) if (RAIZ / "data/08_reporting/pytest_resumen.json").exists() else None
    res = {"comando": "python -m pytest tests/ep3 --collect-only -q --no-cov -p no:cacheprovider", "fecha": time.strftime("%Y-%m-%d"), "recolectadas_ep3": len(ids),
           "por_archivo": dict(sorted(por_archivo.items())), "pruebas_ep2": ep2, "total_ep2_mas_ep3": (ep2 + len(ids)) if ep2 is not None else None,
           "nota": "recolectar no ejecuta las pruebas; el resultado de ejecutar (pasadas/omitidas) esta en docs/ep3/verificacion_copia_limpia.md"}
    SALIDA.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
