"""Mide las pruebas y la cobertura de EP1 sobre el commit que cerro EP1 (03436b1), sin tocar el arbol de trabajo.

Uso: .venv/Scripts/python.exe -X utf8 scripts/medir_pruebas_ep1.py
Exporta ese commit con `git archive` a una carpeta temporal, copia ahi data/01_raw (los datos crudos que usa la prueba de integracion),
ejecuta pytest con cobertura sobre ese codigo y escribe data/08_reporting/ep1_pruebas_cobertura.json.
Requiere el historial de git (en una copia sin .git el JSON ya generado se conserva y el README lo lee).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

R = Path(__file__).resolve().parent.parent
COMMIT = "03436b1"      # "feat: cierre EP1 - seccion conclusiones y hoja de ruta EP2 en notebook etica"
SALIDA = R / "data" / "08_reporting" / "ep1_pruebas_cobertura.json"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        arch = subprocess.run(["git", "archive", COMMIT], cwd=R, capture_output=True)
        if arch.returncode != 0:
            sys.exit(f"ERROR: git archive {COMMIT} fallo: {arch.stderr.decode(errors='replace')}")
        subprocess.run(["tar", "-x", "-C", str(tmp)], input=arch.stdout, check=True)
        (tmp / "data").mkdir(exist_ok=True)
        shutil.copytree(R / "data" / "01_raw", tmp / "data" / "01_raw", dirs_exist_ok=True)
        env = {**os.environ, "PYTHONPATH": str(tmp / "src"), "KEDRO_DISABLE_TELEMETRY": "1"}
        cov = tmp / "cov.json"
        r = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "--cov=src/waymo_evaluacion", f"--cov-report=json:{cov}"], cwd=tmp, env=env, capture_output=True, text=True)
        resumen = re.findall(r"(\d+) (passed|failed|skipped|error)", r.stdout)
        cuentas = {k: int(v) for v, k in resumen}
        datos = json.loads(cov.read_text(encoding="utf-8"))
        nodos = {p.parent.name: len(re.findall(r"\bnode\(", p.read_text(encoding="utf-8"))) for p in sorted((tmp / "src").rglob("pipeline.py")) if p.parent.name != "waymo_evaluacion"}
        t = datos["totals"]
        salida = {"commit": COMMIT, "pruebas_pasadas": cuentas.get("passed", 0), "pruebas_falladas": cuentas.get("failed", 0) + cuentas.get("error", 0), "pruebas_omitidas": cuentas.get("skipped", 0),
                  "cobertura_pct": round(t["percent_covered"], 1), "sentencias": t["num_statements"], "sentencias_sin_cubrir": t["missing_lines"], "nodos_por_pipeline": nodos, "nodos_total": sum(nodos.values()),
                  "fuente": "pytest con cobertura sobre el commit de cierre de EP1, exportado con git archive"}
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(salida, ensure_ascii=False))


if __name__ == "__main__":
    main()
