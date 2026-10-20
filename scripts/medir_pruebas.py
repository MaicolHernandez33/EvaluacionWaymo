"""Ejecuta pytest con cobertura sobre el repositorio actual y guarda el resumen para el README.

Uso: .venv/Scripts/python.exe -X utf8 scripts/medir_pruebas.py
Escribe data/08_reporting/pytest_resumen.json (pruebas pasadas, falladas, omitidas y cobertura total y por archivo).
Aparte de generar_readme.py a proposito: el README lee este JSON y no ejecuta pytest (evita que pytest ejecute el generador que ejecuta pytest).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
SALIDA = R / "data" / "08_reporting" / "pytest_resumen.json"


def main():
    cov = R / "data" / "08_reporting" / "_cov_tmp.json"
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--cov-report=json:{cov}"], cwd=R, capture_output=True, text=True, encoding="utf-8", errors="replace")
    cuentas = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|error)", r.stdout.splitlines()[-1] if r.stdout else "")}
    datos = json.loads(cov.read_text(encoding="utf-8"))
    cov.unlink()
    por_archivo = {k.replace("\\", "/"): round(v["summary"]["percent_covered"], 1) for k, v in datos["files"].items()}
    out = {"pasadas": cuentas.get("passed", 0), "falladas": cuentas.get("failed", 0) + cuentas.get("error", 0), "omitidas": cuentas.get("skipped", 0), "codigo_de_salida": r.returncode,
           "cobertura_total_pct": round(datos["totals"]["percent_covered"], 1), "cobertura_por_archivo": por_archivo, "ultima_linea": r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""}
    SALIDA.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "cobertura_por_archivo"}, ensure_ascii=False))
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
