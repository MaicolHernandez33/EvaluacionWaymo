"""F43: arma ``despliegue_lente.zip``, el paquete que se sube por ``scp`` a la instancia EC2 para correr Lente.

Lleva solo lo que la aplicación necesita para arrancar y puntuar (se midió con un gancho de auditoría de ``open`` sobre la aplicación real: ver ``docs`` del reporte F43): el código (``app/``,
``src/waymo_evaluacion/ep3``), ``artefactos_ep3/``, la configuración de Streamlit, el contenedor, los requisitos y los datos MÍNIMOS (``data/09_app_ep3``, cinco archivos de
``data/06_models_ep3`` y ``docs/ep3/plan_v3.json``). Los archivos de la prueba en vivo no viajan: los sube la persona desde su computador por el navegador.

Falla (sin escribir el zip) si encuentra algo prohibido: parquet crudo de Waymo (``lidar_box``, ``camera_to_lidar_box_association``), ``datos_demo/``, ``.venv``, ``.git``, otros zips,
cualquier archivo de ``data/`` fuera de la lista mínima, o si ``cajas_oof.parquet`` trae columnas de un ``lidar_box`` crudo. Imprime el contenido, el tamaño y el sha256.
No modifica nada del repositorio (solo escribe el zip). Uso: .venv\\Scripts\\python scripts/ep3/empaquetar_despliegue.py [--salida despliegue_lente.zip]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = "despliegue_lente.zip"

# Lo único que viaja de ``data/``: lo que la aplicación abre al arrancar y al recorrer sus 8 páginas (auditoría de ``open``). Un archivo nuevo en estas carpetas NO viaja si no está aquí.
DATOS_09 = "data/09_app_ep3"
MODELOS_06 = ("detector_params_v3.json", "manifest_v3.json", "modelo_final_v3.joblib", "no_supervisado_v3.joblib", "umbrales_v3.json")
ARCHIVOS_SUELTOS = ("Dockerfile", ".dockerignore", "docker-compose.yml", "requirements_app.txt", "constraints_ep3.txt", "docs/despliegue.json", "docs/ep3/plan_v3.json")
CARPETAS_DE_CODIGO = ("app", "artefactos_ep3", ".streamlit")          # se recorren enteras (menos __pycache__): lo que se cuele ahí también se valida
PAQUETE_EP3 = ("src/waymo_evaluacion/__init__.py", "src/waymo_evaluacion/ep3")
CARPETAS_PROHIBIDAS = {"datos_demo", ".venv", ".git", "__pycache__", ".pytest_cache", "notebooks", "tests", "images"}
NOMBRES_CRUDOS = ("lidar_box", "camera_to_lidar_box_association")
COLUMNAS_CRUDAS = ("[LiDARBoxComponent]",)
LEEME = """LENTE: paquete de despliegue (generado por scripts/ep3/empaquetar_despliegue.py)

Contenido: codigo de la aplicacion (app/, src/waymo_evaluacion/ep3), artefactos_ep3/, configuracion de Streamlit, Dockerfile y los datos minimos que la aplicacion abre al arrancar
(data/09_app_ep3 y cinco archivos de data/06_models_ep3). NO trae datos crudos de Waymo ni los segmentos de la demostracion: esos los sube la persona desde su computador por el navegador.

Con Docker (en la carpeta donde se descomprimio):
  docker build -t lente:ec2 .
  docker run -d --name lente --restart unless-stopped -p 8501:8501 -e EP3_ENTORNO=publicado -v "$PWD/data:/app/data:ro" -e WAYMO_APP_DATA=/app/data/09_app_ep3 -e WAYMO_APP_MODELOS=/app/data/06_models_ep3 lente:ec2

Sin Docker:
  python3 -m venv .venv && .venv/bin/pip install -r requirements_app.txt -c constraints_ep3.txt
  PYTHONPATH=src EP3_ENTORNO=publicado .venv/bin/streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501 --browser.gatherUsageStats false

EP3_ENTORNO=publicado activa los textos del modo publicado; sin esa variable la pagina dice que corre solo en el equipo local.
"""


class DespliegueError(Exception):
    """El paquete no se arma: algo prohibido o faltante."""


def _es_crudo(ruta: str) -> bool:
    nombre = ruta.rsplit("/", 1)[-1].lower()
    return nombre.endswith(".parquet") and any(nombre.startswith(c) for c in NOMBRES_CRUDOS)


def _recorrer(raiz: Path, rel: str) -> list[str]:
    base = raiz / rel
    if base.is_file():
        return [rel]
    if not base.is_dir():
        raise DespliegueError(f"falta {rel}")
    salida = []
    for p in sorted(base.rglob("*")):
        partes = p.relative_to(raiz).parts
        if "__pycache__" in partes or p.suffix == ".pyc":
            continue
        if p.is_file():
            salida.append("/".join(partes))
    return salida


def lista_minima(raiz: Path = RAIZ) -> list[str]:
    """Rutas (relativas, con ``/``) que entran al zip; falla si falta algo de la lista."""
    rutas: list[str] = []
    for rel in ARCHIVOS_SUELTOS:
        rutas += _recorrer(raiz, rel)
    for rel in CARPETAS_DE_CODIGO + PAQUETE_EP3 + (DATOS_09,):
        rutas += _recorrer(raiz, rel)
    for nombre in MODELOS_06:
        rutas += _recorrer(raiz, f"data/06_models_ep3/{nombre}")
    return sorted(set(rutas))


def validar(rutas: list[str], raiz: Path = RAIZ) -> None:
    """Rechaza cualquier ruta prohibida. No escribe nada."""
    permitidas_data = {f"data/06_models_ep3/{n}" for n in MODELOS_06}
    problemas: list[str] = []
    for r in rutas:
        partes = r.split("/")
        nombre = partes[-1]
        if _es_crudo(r):
            problemas.append(f"parquet crudo de Waymo: {r}")
        if CARPETAS_PROHIBIDAS & set(partes):
            problemas.append(f"carpeta prohibida: {r}")
        if nombre.lower().endswith((".zip", ".pem")) or nombre.lower().startswith(("entrega_", ".env")):
            problemas.append(f"zip, llave o entorno: {r}")
        if partes[0] == "data" and not (r.startswith(DATOS_09 + "/") or r in permitidas_data):
            problemas.append(f"data/ fuera de la lista mínima: {r}")
        if nombre.lower().endswith(".parquet") and r != f"{DATOS_09}/cajas_oof.parquet":
            problemas.append(f"parquet no previsto (solo viaja cajas_oof.parquet): {r}")
    cajas = raiz / DATOS_09 / "cajas_oof.parquet"
    if f"{DATOS_09}/cajas_oof.parquet" in rutas and cajas.exists():
        import pyarrow.parquet as pq

        crudas = [c for c in pq.read_schema(cajas).names if c.startswith(COLUMNAS_CRUDAS)]
        if crudas:
            problemas.append(f"cajas_oof.parquet trae columnas de un lidar_box crudo: {crudas}")
    if problemas:
        raise DespliegueError("El paquete NO se arma:\n  - " + "\n  - ".join(sorted(set(problemas))))


def armar(raiz: Path = RAIZ, salida: Path | None = None) -> Path:
    """Valida y escribe el zip (carpeta interior ``lente/``); devuelve su ruta."""
    rutas = lista_minima(raiz)
    validar(rutas, raiz)
    destino = salida or raiz / SALIDA
    if destino.exists():
        destino.unlink()
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for r in rutas:
            z.write(raiz / r, f"lente/{r}")
        z.writestr("lente/LEEME_DESPLIEGUE.txt", LEEME)
    return destino


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=SALIDA)
    a = ap.parse_args()
    try:
        destino = armar(RAIZ, RAIZ / a.salida)
    except DespliegueError as e:
        print(e, file=sys.stderr)
        return 1
    with zipfile.ZipFile(destino) as z:
        infos = z.infolist()
        print(f"Contenido de {destino.name}: {len(infos)} archivos")
        por_carpeta: dict[str, list[int]] = {}
        for i in infos:
            partes = i.filename.split("/")
            clave = "/".join(partes[1:3]) if partes[1] in ("data", "src") else partes[1]
            por_carpeta.setdefault(clave, [0, 0])
            por_carpeta[clave][0] += 1
            por_carpeta[clave][1] += i.file_size
        for clave, (n, tam) in sorted(por_carpeta.items()):
            print(f"  {clave:32s} {n:4d} archivos {tam / 1024:10.1f} KB")
    print(f"Tamaño del zip: {destino.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"sha256: {sha256(destino)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
