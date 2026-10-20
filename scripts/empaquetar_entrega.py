"""Arma entrega_EP2.zip: el repositorio mas los datos derivados minimos para re-ejecutar los notebooks 08 a 10 y los generadores.

Uso (desde la raiz del repositorio):

    .venv/Scripts/python.exe -X utf8 scripts/empaquetar_entrega.py

Incluye: codigo (src, scripts, tests, conf), notebooks ejecutados, docs, images, README, pyproject y requirements, y de data/:
  - 01_raw/waymo/camera_to_lidar_box_association y metadatos_ep2 (los lee el apendice L.2 y M del notebook 10 y el 08);
  - 02_intermediate/waymo_con_target.parquet (entrada del notebook 08);
  - 05_model_input, 06_models (modelos y plan congelados), 08_reporting;
  - 07_model_output/oof_B.parquet y pred_test_B.parquet (sin las caches _cache_09_*, para que el 09 reentrene de verdad).
Excluye .venv, .git, .ipynb_checkpoints, caches de Python/pytest, logs y los datos crudos de lidar_box (licencia no comercial de Waymo).
Imprime el tamano por carpeta (sin comprimir y comprimido).
"""
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

R = Path(__file__).resolve().parent.parent
SALIDA = R / "entrega_EP2.zip"
RAIZ_ZIP = "waymo-evaluacion-EP2"

EXCLUIR_DIRS = {".venv", ".git", ".ipynb_checkpoints", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".idea", ".vscode", "htmlcov", ".telemetry"}
EXCLUIR_SUFIJOS = {".log", ".pyc", ".pyo"}
EXCLUIR_ARCHIVOS = {"entrega_EP2.zip", ".coverage", "info.log"}

DATA_INCLUIR = [
    "data/01_raw/waymo/camera_to_lidar_box_association",
    "data/01_raw/waymo/metadatos_ep2",
    "data/02_intermediate/waymo_con_target.parquet",
    "data/05_model_input",
    "data/06_models",
    "data/07_model_output/oof_B.parquet",
    "data/07_model_output/pred_test_B.parquet",
    "data/08_reporting",
]
CARPETAS_CODIGO = ["src", "scripts", "tests", "conf", "notebooks", "docs", "images"]


def archivos_de(ruta):
    p = R / ruta
    if p.is_file():
        yield p
        return
    for f in sorted(p.rglob("*")):
        if f.is_file():
            yield f


def permitido(f):
    partes = set(f.relative_to(R).parts)
    return not (partes & EXCLUIR_DIRS) and f.suffix not in EXCLUIR_SUFIJOS and f.name not in EXCLUIR_ARCHIVOS


def main():
    candidatos = []
    for c in CARPETAS_CODIGO:
        candidatos += list(archivos_de(c))
    for nombre in ("README.md", "pyproject.toml", "requirements.txt", ".gitignore"):
        if (R / nombre).exists():
            candidatos.append(R / nombre)
    for d in DATA_INCLUIR:
        if not (R / d).exists():
            sys.exit(f"ERROR: falta {d}; ejecuta antes los notebooks que lo generan.")
        candidatos += list(archivos_de(d))
    # carpetas data/* vacias con .gitkeep para conservar la estructura
    for gk in sorted((R / "data").rglob(".gitkeep")):
        candidatos.append(gk)
    vistos, archivos = set(), []
    for f in candidatos:
        if f not in vistos and permitido(f):
            vistos.add(f)
            archivos.append(f)
    tam_crudo, tam_comp = defaultdict(int), defaultdict(int)
    if SALIDA.exists():
        SALIDA.unlink()
    with zipfile.ZipFile(SALIDA, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in archivos:
            rel = f.relative_to(R)
            z.write(f, f"{RAIZ_ZIP}/{rel.as_posix()}")
            clave = "/".join(rel.parts[:2]) if rel.parts[0] == "data" else (rel.parts[0] if len(rel.parts) > 1 else "(raiz)")
            tam_crudo[clave] += f.stat().st_size
        info = {i.filename: i.compress_size for i in z.infolist()}
    for nombre, c in info.items():
        rel = Path(nombre).relative_to(RAIZ_ZIP)
        clave = "/".join(rel.parts[:2]) if rel.parts[0] == "data" else (rel.parts[0] if len(rel.parts) > 1 else "(raiz)")
        tam_comp[clave] += c
    mb = lambda b: f"{b / 1e6:8.2f} MB"
    print(f"{'carpeta':45s} {'sin comprimir':>12s} {'comprimido':>12s}")
    for k in sorted(tam_crudo):
        print(f"{k:45s} {mb(tam_crudo[k])} {mb(tam_comp[k])}")
    print(f"{'TOTAL (' + str(len(archivos)) + ' archivos)':45s} {mb(sum(tam_crudo.values()))} {mb(sum(tam_comp.values()))}")
    print(f"Paquete: {SALIDA.name} ({SALIDA.stat().st_size / 1e6:.2f} MB), carpeta raiz dentro del zip: {RAIZ_ZIP}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
