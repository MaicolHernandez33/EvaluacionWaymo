"""F24: escribe el tema nativo de Streamlit en los DOS ``config.toml`` (``.streamlit/config.toml`` y ``app/.streamlit/config.toml``) desde ``TOKENS`` de ``app/estilos.py``.

Solo reemplaza el bloque ``[theme]`` / ``[theme.sidebar]`` (y ``[[theme.fontFaces]]`` si ``app/static/fonts/Inter-Variable.woff2`` existe). Las claves de seguridad (``server.address``, ``headless``,
``gatherUsageStats``, ``toolbarMode``) no se tocan; solo si Inter está en el repo se agrega ``server.enableStaticServing = true`` (hace falta para servir la fuente).
``--comprobar`` no escribe: sale con error si algún archivo difiere de lo que generaría. Uso: .venv\\Scripts\\python scripts/ep3/generar_config_tema.py [--comprobar]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
import estilos as E  # noqa: E402

ARCHIVOS = [RAIZ / ".streamlit/config.toml", RAIZ / "app/.streamlit/config.toml"]
ENCABEZADO = "# Tema (F24): oscuro, generado desde TOKENS de app/estilos.py con scripts/ep3/generar_config_tema.py (no editar a mano); tipografia del sistema, sin fuentes externas.\n"


def generar(texto: str) -> str:
    i = re.search(r"^(# Tema[^\n]*\n)?\[theme\]", texto, flags=re.M)
    previo = texto[:i.start()] if i else texto.rstrip("\n") + "\n\n"
    if E.ARCHIVO_INTER.exists() and "enableStaticServing" not in previo:
        previo = previo.replace("[server]\n", "[server]\nenableStaticServing = true\n", 1)
    return previo + ENCABEZADO + E.tema_toml()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--comprobar", action="store_true")
    a = ap.parse_args()
    distintos = []
    for ruta in ARCHIVOS:
        actual = ruta.read_text(encoding="utf-8")
        nuevo = generar(actual)
        if nuevo != actual:
            distintos.append(ruta)
            if not a.comprobar:
                ruta.write_text(nuevo, encoding="utf-8")
    if a.comprobar:
        print("difieren:", [r.relative_to(RAIZ).as_posix() for r in distintos] or "ninguno")
        return 1 if distintos else 0
    print("escritos:", [r.relative_to(RAIZ).as_posix() for r in distintos] or "sin cambios")
    return 0


if __name__ == "__main__":
    sys.exit(main())
