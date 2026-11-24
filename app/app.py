"""Lente: página de EP3 (el nombre y los textos de marca son constantes de ``app_logica``) para revisar primero las cajas 3D de peatones y ciclistas que probablemente no tienen su par 2D de cámara. Solo local: ningún dato sale del equipo.

Ejecutar:  streamlit run app/app.py   (o scripts/ep3/arrancar_app.bat, que precarga los datos)
Variables de entorno opcionales: WAYMO_APP_DATA (por defecto data/09_app_ep3) y WAYMO_APP_MODELOS (por defecto data/06_models_ep3).

Este archivo es el MARCO de la página (F20-P1): configuración, estilos, wordmark, navegación agrupada (``st.navigation``), rol al pie de la barra lateral y pie único.
Cada sección es un archivo corto de ``app/paginas/`` que llama a ``secciones.py``; la lógica probada está en ``src/waymo_evaluacion/ep3/app_logica.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
for _ruta in (str(RAIZ / "src"), str(AQUI)):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import contexto as C  # noqa: E402
import estilos as E  # noqa: E402
import precarga as PC  # noqa: E402
from waymo_evaluacion.ep3.app_logica import (  # noqa: E402
    ARCHIVO_PAGINA, ATRIBUCION_WAYMO, GRUPOS_NAV, ICONOS, NOMBRE_PRODUCTO, PERFILES, SECCIONES, SUBLINEA_MARCA, URL_PAGINA, version_pagina,
)

ICONO = AQUI / "assets" / "icono.png"
PC.iniciar(str(C.carpeta_datos()), str(C.carpeta_modelos()))        # carga y calienta los datos y la solución congelada en un hilo (una vez por proceso)

st.set_page_config(page_title=NOMBRE_PRODUCTO, page_icon=str(ICONO) if ICONO.exists() else None, layout="wide")


def al_cambiar_rol() -> None:
    """Cambiar el rol lleva a la página que sugiere ese rol (se resuelve más abajo: ``st.switch_page`` no es fiable dentro de un callback)."""
    st.session_state["_ir"] = PERFILES[st.session_state["perfil"]]["seccion"]


if "perfil" not in st.session_state:
    st.session_state["perfil"] = list(PERFILES)[0]

_version = version_pagina(C.carpeta_modelos())
st.logo(E.wordmark(NOMBRE_PRODUCTO, SUBLINEA_MARCA), size="large")
pg = st.navigation({grupo: [st.Page(ARCHIVO_PAGINA[s], title=s, icon=ICONOS[s], url_path=URL_PAGINA[s], default=(s == SECCIONES[0])) for s in secciones] for grupo, secciones in GRUPOS_NAV.items()})

st.sidebar.selectbox("Rol", list(PERFILES), key="perfil", on_change=al_cambiar_rol, help="Cada rol abre la página que le corresponde.")
st.markdown(E.css(), unsafe_allow_html=True)

# enlace directo antiguo (?seccion=Cola de revisión): se atiende una sola vez por sesión y redirige a la página
if not st.session_state.get("_url_atendida"):
    st.session_state["_url_atendida"] = True
    _pedida = st.query_params.get("seccion")
    if _pedida in SECCIONES:
        st.switch_page(ARCHIVO_PAGINA[_pedida])

_destino = st.session_state.pop("_ir", None)
if _destino in SECCIONES:
    st.switch_page(ARCHIVO_PAGINA[_destino])

pg.run()

try:
    _segmentos = int(PC.datos(str(C.carpeta_datos()))["celdas"]["seg"].nunique())
except Exception:  # noqa: BLE001 - sin datos no hay recuento; el pie sigue
    _segmentos = None
st.markdown(E.pie(ATRIBUCION_WAYMO, _version, _segmentos), unsafe_allow_html=True)
