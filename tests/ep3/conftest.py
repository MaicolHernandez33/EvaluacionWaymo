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
