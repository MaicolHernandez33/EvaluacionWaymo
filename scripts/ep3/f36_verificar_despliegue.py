"""F36, sección 3: reúne la evidencia para decidir el despliegue. SOLO LEE Y REPORTA: no cambia nada del código, de los datos ni de la licencia (esa decisión es de quien publica).

Responde, con archivo y línea cuando corresponde:
1. ¿La página escribe algo fuera de memoria? (escrituras a disco, cachés persistentes, registros, carpetas temporales, en ``app/`` y en el paquete ``src/waymo_evaluacion/ep3`` que viaja en la imagen).
2. ¿Cómo guarda Streamlit los archivos subidos? (se lee su propio código instalado).
3. ¿Qué archivos formarían parte de un despliegue? (lo que copia el ``Dockerfile`` y lo que ``docker-compose.yml`` monta como volúmenes: ``data/09_app_ep3`` y ``data/06_models_ep3``), con su tamaño y, para las tablas, sus columnas.
4. ¿Hay datos derivados del Waymo Open Dataset entre esos archivos? Solo se lista qué hay (columnas y número de filas); no se decide si pueden publicarse.
5. ¿Hay rutas del equipo, nombres de usuario o credenciales en esos archivos? (texto y bytes).
Escribe ``docs/ep3/f36_verificacion_despliegue.json``. Uso: .venv\\Scripts\\python scripts/ep3/f36_verificar_despliegue.py
"""
from __future__ import annotations

import getpass
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "docs/ep3/f36_verificacion_despliegue.json"
PATRON_ESCRITURA = re.compile(r"st\.cache_data|st\.cache_resource|st\.cache\b|lru_cache|shelve|pickle|joblib\.dump|\.to_parquet\(|\.to_csv\(\s*[\"'A-Za-z_/\\][^)]*[\"']|tempfile|shutil|write_bytes|write_text|"
                              r"open\([^)]*[\"'][wax]b?\+?[\"']|FileHandler|logging\.basicConfig|\.save\(|os\.makedirs|mkdir\(")
COMENTARIO = re.compile(r"^\s*#")


def escrituras() -> list[dict]:
    """Líneas de ``app/`` y de ``src/waymo_evaluacion/ep3/`` que podrían escribir fuera de memoria. Las del lector de archivos de la página no figuran porque no existen; las que aparecen se explican."""
    hallazgos = []
    for base in (RAIZ / "app", RAIZ / "src/waymo_evaluacion/ep3"):
        for p in sorted(base.rglob("*.py")):
            for n, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if COMENTARIO.match(linea):
                    continue
                m = PATRON_ESCRITURA.search(linea)
                if m:
                    hallazgos.append({"archivo": str(p.relative_to(RAIZ)).replace("\\", "/"), "linea": n, "coincidencia": m.group(0)[:60], "codigo": linea.strip()[:150]})
    return hallazgos


def streamlit_guarda_en_memoria() -> dict:
    """Cómo guarda Streamlit los archivos subidos: se lee el código instalado (``uploaded_file_manager`` y el almacenamiento por defecto)."""
    import streamlit

    base = Path(streamlit.__file__).parent / "runtime"
    out: dict = {"version": streamlit.__version__}
    for nombre in ("memory_uploaded_file_manager.py", "uploaded_file_manager.py", "memory_media_file_storage.py"):
        f = base / nombre
        if f.exists():
            t = f.read_text(encoding="utf-8")
            out[nombre] = {"existe": True, "escribe_a_disco": bool(re.search(r"open\(|tempfile|write_bytes|\.write\(|shutil", t)), "usa_diccionario_en_memoria": "Dict[" in t or "dict[" in t or "self._files" in t}
    return out


def archivos_del_despliegue() -> dict:
    """Lo que formaría parte de la imagen (código) y de los volúmenes (datos), con tamaños."""
    def listar(carpeta: Path, patron: str = "*") -> list[dict]:
        return [{"archivo": str(p.relative_to(RAIZ)).replace("\\", "/"), "bytes": p.stat().st_size} for p in sorted(carpeta.rglob(patron)) if p.is_file() and "__pycache__" not in p.parts]

    return {"imagen_codigo_app": listar(RAIZ / "app"), "imagen_codigo_ep3": listar(RAIZ / "src/waymo_evaluacion/ep3", "*.py"), "volumen_datos_09_app_ep3": listar(RAIZ / "data/09_app_ep3"),
            "volumen_modelos_06_models_ep3": listar(RAIZ / "data/06_models_ep3")}


def contenido_de_tablas() -> dict:
    """Columnas y filas de las tablas de datos que viajarían (para que quien revise la licencia vea qué hay)."""
    import pandas as pd

    out = {}
    for p in sorted((RAIZ / "data/09_app_ep3").glob("*.parquet")):
        df = pd.read_parquet(p)
        out[p.name] = {"filas": int(len(df)), "columnas": list(map(str, df.columns))}
    for p in sorted((RAIZ / "data/09_app_ep3").glob("*.csv")):
        df = pd.read_csv(p, nrows=5)
        out[p.name] = {"filas": int(sum(1 for _ in open(p, "rb")) - 1), "columnas": list(map(str, df.columns))}
    return out


def rutas_y_credenciales(archivos: dict) -> dict:
    """Busca en los archivos que se publicarían el nombre de usuario del equipo, rutas de disco, correos y palabras de credenciales (en texto y dentro de los binarios)."""
    usuario = getpass.getuser()
    patrones = {"nombre_de_usuario_del_equipo": usuario.encode(), "ruta_Users": b"C:\\Users", "ruta_Users_barra": b"C:/Users", "correo": rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}"}
    palabras = rb"(?i)(password|passwd|secret|api[_-]?key|token|credential|authorization: bearer)"
    hallazgos: list[dict] = []
    for grupo, lista in archivos.items():
        for f in lista:
            ruta = RAIZ / f["archivo"]
            if ruta.suffix in (".pyc",) or f["bytes"] > 60 * 1024 * 1024:
                continue
            datos = ruta.read_bytes()
            for nombre, pat in patrones.items():
                ok = re.search(pat, datos) if nombre == "correo" else (pat in datos)
                if ok:
                    hallazgos.append({"archivo": f["archivo"], "tipo": nombre})
            m = re.search(palabras, datos)
            if m and ruta.suffix in (".py", ".toml", ".json", ".csv", ".txt", ".md"):
                n = datos[:m.start()].count(b"\n") + 1
                hallazgos.append({"archivo": f["archivo"], "tipo": "palabra de credencial", "palabra": m.group(0).decode("utf-8", "replace"), "linea": n,
                                  "texto": datos.splitlines()[n - 1][:120].decode("utf-8", "replace")})
    return {"usuario_buscado": "(el del equipo; no se escribe aquí)", "hallazgos": hallazgos}


def main() -> None:
    archivos = archivos_del_despliegue()
    out = {"escrituras_o_caches_en_el_codigo_que_viaja": escrituras(), "streamlit_y_archivos_subidos": streamlit_guarda_en_memoria(), "archivos": archivos, "tablas_de_datos": contenido_de_tablas(),
           "rutas_y_credenciales": rutas_y_credenciales(archivos), "dockerfile_copia": [l.strip() for l in (RAIZ / "Dockerfile").read_text(encoding="utf-8").splitlines() if l.startswith("COPY")],
           "compose_volumenes": [l.strip() for l in (RAIZ / "docker-compose.yml").read_text(encoding="utf-8").splitlines() if "./data" in l]}
    SALIDA.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    resumen = {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in out.items()}
    print(json.dumps(resumen, ensure_ascii=False))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
