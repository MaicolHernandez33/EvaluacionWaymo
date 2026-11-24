"""Hace importable `waymo_evaluacion` en una copia limpia sin instalar el paquete (solo agrega `src` al camino de busqueda).

En el entorno de desarrollo el paquete esta instalado en modo editable y apunta al mismo `src`; en una copia limpia (venv nuevo con
`requirements*.txt`) no estaria instalado y las pruebas no encontrarian el modulo. No escribe nada.
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = str(Path(__file__).resolve().parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


import pytest  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def _sin_escaneo_de_componentes_de_streamlit():
    """Cada ``AppTest`` de Streamlit 1.65 escanea los metadatos de todos los paquetes instalados para registrar componentes de terceros (``discover_and_register_components``).

    Con ``altair`` importado ese escaneo tarda de 1,3 a 2 s por cada ``AppTest`` (medido: 0,25 s sin altair). Es un costo del arnés de pruebas y no de la página, que no usa componentes
    de terceros; sumado a la página dejaba a «Validación» por encima de los 3 s de ``test_tras_la_precarga_ninguna_seccion_tarda_mas_de_3_segundos`` y alargaba la suite de 70 a casi 280 s.
    Solo afecta a las pruebas de ``tests/ep3``; no cambia la página ni sus resultados (F24, DEC-102).
    """
    try:
        from streamlit.components.v2.component_manager import BidiComponentManager
    except Exception:  # noqa: BLE001  (otra versión de Streamlit: no hay nada que parchear)
        yield
        return
    original = BidiComponentManager.discover_and_register_components
    BidiComponentManager.discover_and_register_components = lambda self, *args, **kwargs: None
    try:
        yield
    finally:
        BidiComponentManager.discover_and_register_components = original


@pytest.fixture(autouse=True)
def _entorno_local_por_defecto(monkeypatch):
    """F26: los textos de la página dependen de ``EP3_ENTORNO``. Las pruebas parten del valor por defecto (``local``) aunque el shell de quien las corre la tenga puesta; las que prueban la
    variante ``servidor`` la fijan ellas mismas con ``monkeypatch.setenv``."""
    monkeypatch.delenv("EP3_ENTORNO", raising=False)
