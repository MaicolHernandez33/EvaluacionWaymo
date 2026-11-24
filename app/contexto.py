"""Contexto compartido de las páginas (F20-P1): carpetas de datos y modelos, y el diccionario ``ctx`` que reciben las secciones.

Las carpetas se leen de las variables de entorno en CADA llamada (no al importar), para que una prueba pueda cambiarlas entre ejecuciones. Los datos y la solución congelada salen de
``precarga`` (se cargan una vez por proceso). Sin conexiones externas.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import streamlit as st

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent


def carpeta_datos() -> Path:
    """``WAYMO_APP_DATA`` o ``data/09_app_ep3``."""
    return Path(os.environ.get("WAYMO_APP_DATA", RAIZ / "data/09_app_ep3"))


def carpeta_modelos() -> Path:
    """``WAYMO_APP_MODELOS`` o ``data/06_models_ep3``."""
    return Path(os.environ.get("WAYMO_APP_MODELOS", RAIZ / "data/06_models_ep3"))


def contexto() -> dict[str, Any]:
    """Diccionario que reciben las secciones: datos, cifras clave, rol y cachés de la solución congelada. ``falta`` trae el motivo si no hay datos."""
    import precarga as PC
    from waymo_evaluacion.ep3.app_logica import cargar_fraccion_hueco, datos_ciclistas, hora_de_los_datos, version_pagina

    datos, modelos = str(carpeta_datos()), str(carpeta_modelos())
    try:
        D, falta = PC.datos(datos), None
    except FileNotFoundError as e:
        D, falta = None, str(e)
    ctx = {"D": D, "K": D["kpis"] if D else {}, "perfil": st.session_state.get("perfil"),
           "artefactos": lambda: PC.artefactos(modelos), "no_sup": lambda: PC.no_sup(modelos), "rangos": PC.rangos(modelos), "min_cajas": PC.min_cajas(modelos),
           "ciclistas": datos_ciclistas(D["evidencia"].get("posthoc__equidad") if D else None), "version": version_pagina(carpeta_modelos()), "hora_datos": hora_de_los_datos(carpeta_datos()), "frac_hueco": cargar_fraccion_hueco(carpeta_modelos()), "falta": falta}
    if D is None:      # las secciones que funcionan sin los datos de la página (Puntuar, Ética, Ayuda) siguen disponibles
        ctx["D"] = {"evidencia": {}, "cajas": None}
    return ctx
