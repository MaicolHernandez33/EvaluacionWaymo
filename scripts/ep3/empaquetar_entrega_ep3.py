"""Arma artefactos_ep3/ (versionable, fuera de data/) y entrega_EP3.zip (carpeta interior waymo-evaluacion-EP3/).

Uso (desde la raiz):  .venv/Scripts/python.exe -X utf8 scripts/ep3/empaquetar_entrega_ep3.py
Politica de EP2: no se incluyen los lidar_box originales de Waymo (licencia no comercial); si las tablas de asociacion y los
datos derivados minimos para re-ejecutar. artefactos_ep3/ solo lleva tablas AGREGADAS (por candidato, fold, cluster o segmento),
nunca tablas por caja ni identificadores de objeto. Escribe solo artefactos_ep3/ y entrega_EP3.zip.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[2]
SALIDA = R / "entrega_EP3.zip"
RAIZ_ZIP = "waymo-evaluacion-EP3"
ART = R / "artefactos_ep3"
REP = R / "data/08_reporting_ep3"
PROHIBIDAS = {"key.laser_object_id", "key.frame_timestamp_micros", "laser_object_id", "fila_id", "fila_pp"}     # columnas por caja

EXCLUIR_DIRS = {".venv", ".git", ".ipynb_checkpoints", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".idea", ".vscode", "htmlcov", ".telemetry", "revision"}
EXCLUIR_SUFIJOS = {".log", ".pyc", ".pyo"}
EXCLUIR_ARCHIVOS = {"entrega_EP2.zip", "entrega_EP3.zip", ".coverage", "info.log"}
CARPETAS_CODIGO = ["src", "scripts", "tests", "conf", "notebooks", "docs", "images", "app", "artefactos_ep3", ".streamlit"]
ARCHIVOS_RAIZ = ["README.md", "CLAUDE.md", "pyproject.toml", "requirements.txt", "requirements_ep3.txt", "requirements_app.txt", "constraints_ep3.txt", "Dockerfile", ".dockerignore", "docker-compose.yml", ".gitignore"]
DATA_INCLUIR = [
    "data/01_raw/waymo/camera_to_lidar_box_association", "data/01_raw/waymo/metadatos_ep2",          # EP2 (tablas de asociacion; sin lidar_box originales)
    "data/05_model_input", "data/06_models", "data/07_model_output/oof_B.parquet", "data/07_model_output/pred_test_B.parquet", "data/08_reporting",
    "data/05_model_input_ep3", "data/06_models_ep3", "data/07_model_output_ep3", "data/08_reporting_ep3", "data/09_app_ep3",
]
# train.parquet de EP2 solo lo usan los notebooks de EP2 (no EP3); checkpoints que se regeneran en minutos (f4, f5) o que no hacen falta; f3_ckpt se incluye (la busqueda tarda cerca de una hora)
DATA_EXCLUIR_PREFIJOS = ["data/05_model_input/train.parquet", "data/08_reporting_ep3/f4_ckpt", "data/08_reporting_ep3/f5_ckpt", "data/08_reporting_ep3/mlruns"]

# archivos de artefactos_ep3 -> origen (todos agregados)
ARTEFACTOS = {
    "manifest_v3.json": "data/06_models_ep3/manifest_v3.json", "manifest_no_supervisado.json": "data/06_models_ep3/manifest_no_supervisado.json",
    "umbrales_v3.json": "data/06_models_ep3/umbrales_v3.json", "detector_params_v3.json": "data/06_models_ep3/detector_params_v3.json",
    "plan_v3.md": "docs/ep3/plan_v3.md", "plan_v3.json": "docs/ep3/plan_v3.json", "plan_v3.sha256": "docs/ep3/plan_v3.sha256", "plan_v3_desviaciones.md": "docs/ep3/plan_v3_desviaciones.md",
    "lista_A_huecos.csv": "data/08_reporting_ep3/lista_A_huecos.csv", "pruebas_ep3_conteo.json": "data/08_reporting_ep3/pruebas_ep3_conteo.json",
}
PREFIJOS_TABLAS = ("f1_", "f2_", "f3_", "f4_", "f5_", "f6_", "f12_", "f12b_", "f13_")
SUFIJOS_TABLAS = (".csv", ".json")
EXCLUIR_TABLAS = {"f3_bordes_extension.json"}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def construir_artefactos() -> list[tuple[str, str, int]]:
    if ART.exists():
        shutil.rmtree(ART)
    ART.mkdir()
    fuentes = dict(ARTEFACTOS)
    for p in sorted(REP.iterdir()):
        if p.is_file() and p.name.startswith(PREFIJOS_TABLAS) and p.suffix in SUFIJOS_TABLAS and p.name not in EXCLUIR_TABLAS:
            fuentes[p.name] = p.relative_to(R).as_posix()
    for destino, origen in fuentes.items():
        src = R / origen
        if src.suffix == ".csv":                                  # guarda: ninguna tabla por caja
            cols = set(pd.read_csv(src, nrows=1).columns)
            if cols & PROHIBIDAS:
                raise SystemExit(f"DETENIDO: {origen} tiene columnas por caja {sorted(cols & PROHIBIDAS)}; no va a artefactos_ep3")
        shutil.copy2(src, ART / destino)
    filas = [(n, fuentes[n], (ART / n).stat().st_size) for n in sorted(fuentes)]
    sums = {n: sha(ART / n) for n, _, _ in filas}
    tabla = "\n".join(f"| `{n}` | `{o}` | {t:,} | `{sums[n][:16]}...` |".replace(",", ".") for n, o, t in filas)
    (ART / "README_artefactos.md").write_text(f"""# artefactos_ep3: lo versionable de EP3

Carpeta fuera de `data/` (que git ignora) con lo liviano y **agregado** de EP3: manifests con sha256, umbrales, parámetros del detector, el plan v3 congelado y las tablas de resultados por candidato, fold, cluster o segmento. **No hay tablas por caja ni identificadores de objeto.** Se regenera con `scripts/ep3/empaquetar_entrega_ep3.py`.

## Qué es cada archivo
- `manifest_v3.json`: sha256 de `modelo_final_v3.joblib`, `umbrales_v3.json` y `detector_params_v3.json` (la solución congelada v3: regla «menos puntos top», umbrales A y B, detector de huecos). `manifest_no_supervisado.json`: sha256 del scaler y KMeans descriptivos (post hoc).
- `umbrales_v3.json`, `detector_params_v3.json`: copia legible de esos parámetros (el verificador mira los de `data/06_models_ep3`, no estas copias).
- `plan_v3.md`, `plan_v3.json`, `plan_v3.sha256`: el plan congelado antes de experimentar (no se editan). `plan_v3_desviaciones.md`: DEV-1 y DEV-2.
- `lista_A_huecos.csv`: las 2 celdas (segmento x cámara) con hueco.
- `f1_` a `f6_`, `f12_`, `f12b_`, `f13_`: tablas y resúmenes de cada fase (F1 datos, F2 detector, F3 IE9, F4 IE10, F5 IE11, F6 IE12, F12 análisis en muestra, F13 no supervisado).

## Cómo verificarlo
1. Con el repositorio completo y `data/`: `python scripts/ep3/verificar_congelados_v3.py` y `python scripts/ep3/verificar_no_supervisado.py`.
2. Solo con esta carpeta: comparar el sha256 de cada archivo con la columna de abajo (por ejemplo `certutil -hashfile manifest_v3.json SHA256`), y el de los 3 archivos de la solución con `manifest_v3.json`.

## Qué falta para correr la página
Esta carpeta no alcanza: la página necesita `data/09_app_ep3/` (predicciones por caja fuera de fold) y `data/06_models_ep3/` (modelo y artefacto no supervisado). Van en `entrega_EP3.zip` (solo uso académico del docente, no redistribuir) o se regeneran con `scripts/ep3/f7_preparar_app.py`.

## Archivos
| Archivo | Origen | Bytes | sha256 (16 primeros) |
|---|---|---|---|
{tabla}
""", encoding="utf-8")
    return filas


def incluida(rel: str) -> bool:
    if any(rel.startswith(x) for x in DATA_EXCLUIR_PREFIJOS) or rel.endswith(".parcial.json"):
        return False
    return True


def recolectar() -> list[Path]:
    archivos: list[Path] = []

    def anadir(p: Path) -> None:
        if p.is_file():
            if p.name not in EXCLUIR_ARCHIVOS and p.suffix not in EXCLUIR_SUFIJOS and not (set(p.relative_to(R).parts) & EXCLUIR_DIRS):
                if incluida(p.relative_to(R).as_posix()):
                    archivos.append(p)
        elif p.is_dir():
            for q in sorted(p.rglob("*")):
                anadir(q)

    for c in CARPETAS_CODIGO:
        anadir(R / c)
    for a in ARCHIVOS_RAIZ:
        anadir(R / a)
    for d in DATA_INCLUIR:
        anadir(R / d)
    return sorted(set(archivos))


LEEME = """# Entrega EP3: auditoría de cajas 3D sin par 2D (Waymo Open Dataset v2)
Descomprima, abra una consola en esta carpeta y siga los comandos (Windows, Python 3.10).

Verificar (3 comandos):
1. `python -m venv .venv` y luego `.venv\\Scripts\\pip install -r requirements.txt -r requirements_ep3.txt -c constraints_ep3.txt`
2. `.venv\\Scripts\\python scripts\\verificar_congelados.py` y `.venv\\Scripts\\python scripts\\ep3\\verificar_congelados_v3.py` (EP2: 14 de 14; v3: 5 de 5)
3. `.venv\\Scripts\\python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider` (no ejecute `pytest` sin ruta: reescribe archivos de EP2)

Abrir la página (3 comandos):
1. `.venv\\Scripts\\pip install -r requirements_app.txt -c constraints_ep3.txt`
2. `scripts\\ep3\\arrancar_app.bat`
3. Abrir http://localhost:8501 (solo escucha en su equipo; active «Modo presentación» para ocultar identificadores). Informe: `docs/ep3/informe_tecnico_EP3.md`; guía: `docs/ep3/README_EP3.md`.

AVISO DE LICENCIA: contiene datos derivados del Waymo Open Dataset (uso no comercial). Solo para uso académico del docente; no redistribuir ni publicar.
Integridad: `SHA256SUMS` lista el sha256 de cada archivo (formato `hash  ruta`).
"""


def main() -> None:
    filas = construir_artefactos()
    print(f"artefactos_ep3: {len(filas)} archivos + README_artefactos.md")
    archivos = recolectar()
    sumas: list[str] = []
    tam = defaultdict(lambda: [0, 0])
    with zipfile.ZipFile(SALIDA, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in archivos:
            rel = p.relative_to(R).as_posix()
            sumas.append(f"{sha(p)}  {rel}")
            z.write(p, f"{RAIZ_ZIP}/{rel}")
            top = "/".join(rel.split("/")[:2]) if rel.startswith("data/") else rel.split("/")[0]
            tam[top][0] += p.stat().st_size
        assert len(LEEME.strip().splitlines()) <= 15, "LEEME de mas de 15 lineas"
        z.writestr(f"{RAIZ_ZIP}/LEEME_ENTREGA.md", LEEME)
        z.writestr(f"{RAIZ_ZIP}/SHA256SUMS", "\n".join(sumas) + "\n")
    with zipfile.ZipFile(SALIDA) as z:
        for i in z.infolist():
            rel = i.filename.split("/", 1)[1] if "/" in i.filename else i.filename
            top = "/".join(rel.split("/")[:2]) if rel.startswith("data/") else rel.split("/")[0]
            tam[top][1] += i.compress_size
    print(f"{'carpeta':50s} {'sin comprimir':>14s} {'comprimido':>12s}")
    for k, (a, b) in sorted(tam.items()):
        print(f"{k:50s} {a / 1e6:12.1f} MB {b / 1e6:10.1f} MB")
    print(f"TOTAL: {len(archivos) + 2} archivos, {SALIDA.stat().st_size / 1e6:.1f} MB comprimido -> {SALIDA.name}")
    resumen = {"archivos": len(archivos) + 2, "bytes_zip": SALIDA.stat().st_size, "sha256_zip": sha(SALIDA)}
    (R / "entrega_EP3.sha256").write_text(f"{resumen['sha256_zip']}  {SALIDA.name}\n", encoding="utf-8")
    print(json.dumps(resumen))


if __name__ == "__main__":
    sys.exit(main())
