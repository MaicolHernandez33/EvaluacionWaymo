"""Lanzador de la pagina con precarga (F19-B9): ``python app/lanzar.py [opciones de streamlit run]``.

Carga los datos y la solucion congelada en un hilo ANTES de abrir el servidor, y luego ejecuta ``streamlit run app/app.py`` en el mismo proceso (asi la precarga queda
compartida con la pagina). Las opciones de seguridad (``--server.address localhost``, telemetria apagada) las siguen poniendo ``scripts/ep3/arrancar_app.bat`` y el
``.streamlit/config.toml``. ``python -m streamlit run app/app.py`` sigue funcionando: la precarga empieza entonces con la primera visita.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(AQUI))

import precarga  # noqa: E402

if __name__ == "__main__":
    precarga.iniciar(str(Path(os.environ.get("WAYMO_APP_DATA", RAIZ / "data/09_app_ep3"))), str(Path(os.environ.get("WAYMO_APP_MODELOS", RAIZ / "data/06_models_ep3"))))
    from streamlit.web import cli

    sys.argv = ["streamlit", "run", str(AQUI / "app.py"), *sys.argv[1:]]
    cli.main()
