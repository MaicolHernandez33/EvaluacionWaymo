"""Auditor de etiquetas 3D: página de EP3 para revisar primero las cajas 3D que probablemente no tienen su par 2D de cámara. Solo local: ningún dato sale del equipo.

Ejecutar:  streamlit run app/app.py
Variables de entorno opcionales: WAYMO_APP_DATA (por defecto data/09_app_ep3) y WAYMO_APP_MODELOS (por defecto data/06_models_ep3).
Las secciones están en secciones.py, los estilos en estilos.py y la lógica probada en src/waymo_evaluacion/ep3/app_logica.py.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(AQUI))

import estilos as E  # noqa: E402
import secciones as S  # noqa: E402
from waymo_evaluacion.ep3.app_logica import (  # noqa: E402
    ESLOGAN, ICONOS, PERFILES, PRODUCTO, SECCIONES, cargar_datos, cargar_no_supervisado, cargar_rangos, datos_ciclistas, version_pagina,
)

CARPETA_DATOS = Path(os.environ.get("WAYMO_APP_DATA", RAIZ / "data/09_app_ep3"))
CARPETA_MODELOS = Path(os.environ.get("WAYMO_APP_MODELOS", RAIZ / "data/06_models_ep3"))
ICONO = AQUI / "assets" / "icono.png"

st.set_page_config(page_title=PRODUCTO, page_icon=str(ICONO) if ICONO.exists() else None, layout="wide")


@st.cache_data(show_spinner=False)
def datos(carpeta: str) -> dict:
    return cargar_datos(Path(carpeta))


@st.cache_resource(show_spinner=False)
def artefactos(carpeta: str):
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos

    return cargar_artefactos(Path(carpeta))


@st.cache_resource(show_spinner=False)
def no_sup(carpeta: str):
    return cargar_no_supervisado(Path(carpeta))


@st.cache_data(show_spinner=False)
def rangos(carpeta: str) -> dict:
    return cargar_rangos(Path(carpeta))


def al_cambiar_perfil() -> None:
    st.session_state["seccion"] = PERFILES[st.session_state["perfil"]]["seccion"]


# ----------------------------------------------------------------------------------------------- estado inicial y barra lateral
if "perfil" not in st.session_state:
    st.session_state["perfil"] = list(PERFILES)[0]
if "seccion" not in st.session_state:
    st.session_state["seccion"] = PERFILES[st.session_state["perfil"]]["seccion"]
    _pedida = st.query_params.get("seccion")            # enlace directo a una sección (por ejemplo ?seccion=Cola de revisión); sirve para las capturas
    if _pedida in SECCIONES:
        st.session_state["seccion"] = _pedida

st.sidebar.markdown(f'<p class="aud-producto">{PRODUCTO}</p>', unsafe_allow_html=True)
perfil = st.sidebar.selectbox("Perfil", list(PERFILES), key="perfil", on_change=al_cambiar_perfil, help="Cambia la sección que se le sugiere y las acciones de Inicio.")
presentacion = st.sidebar.toggle("Modo presentación", key="presentacion", help="Oculta los identificadores (marca de tiempo e identificador de objeto) y agranda la letra y las tarjetas.")
seccion = st.sidebar.radio("Menú", SECCIONES, key="seccion", format_func=lambda s: f"{ICONOS[s]} {s}")
st.sidebar.caption("Waymo Open Dataset v2, uso académico. Nada se guarda ni se envía.")
st.markdown(E.css(presentacion), unsafe_allow_html=True)

try:
    D = datos(str(CARPETA_DATOS))
except FileNotFoundError as e:
    D = None
    falta = str(e)
K = D["kpis"] if D else {}

st.markdown(E.cabecera(PRODUCTO, ESLOGAN, perfil), unsafe_allow_html=True)
st.title(seccion)

if D is None and seccion not in ("Ética y límites", "Puntuar datos nuevos", "Ayuda y glosario"):
    st.error(f"No encuentro los datos de la página ({falta}). Genérelos con: python scripts/ep3/f7_preparar_app.py")
else:
    ctx = {"D": D, "K": K, "perfil": perfil, "presentacion": presentacion, "artefactos": lambda: artefactos(str(CARPETA_MODELOS)), "no_sup": lambda: no_sup(str(CARPETA_MODELOS)),
           "rangos": rangos(str(CARPETA_MODELOS)), "ciclistas": datos_ciclistas(D["evidencia"].get("posthoc__equidad") if D else None), "version": version_pagina(CARPETA_MODELOS)}
    if D is None:  # secciones que funcionan sin los datos de la página
        ctx["D"] = {"evidencia": {}, "cajas": None}
    {"Inicio": S.inicio, "Auditoría de cámaras": S.auditoria, "Cola de revisión": S.cola, "Explica una caja": S.explica, "Evidencia": S.evidencia, "Ética y límites": S.etica,
     "Puntuar datos nuevos": S.puntuar, "Ayuda y glosario": S.ayuda}[seccion](ctx)

st.markdown(E.pie(version_pagina(CARPETA_MODELOS)), unsafe_allow_html=True)
