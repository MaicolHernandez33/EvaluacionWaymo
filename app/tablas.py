"""El componente único de tabla de la página (F34): lo usan Validación y Puntuar datos nuevos. El formato y la paginación viven en ``waymo_evaluacion.ep3.tablas_estandar`` (funciones puras);
aquí solo se dibuja: título opcional, «Responde: …», la tabla HTML (sin desplazamiento vertical interno; con más de 25 filas se pagina de 25 en 25), el conteo de filas y «Descargar CSV» con todas las
columnas y los valores sin redondear.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

import estilos as E
from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.tablas_estandar import POR_PAGINA, Tabla, pagina, paginas, texto_filas, texto_rango


def _ir(clave: str, delta: int, total: int) -> None:
    st.session_state[f"pag_{clave}"] = min(max(1, st.session_state.get(f"pag_{clave}", 1) + delta), total)


def mostrar_tabla(t: Tabla, clave: str | None = None, por_pagina: int = POR_PAGINA, titulo: bool = False, nombre_csv: str | None = None) -> None:
    """Dibuja ``t``. ``clave`` identifica sus controles (único por tabla en la página); ``titulo`` pone el título arriba (dentro de un desplegable ya lo lleva el desplegable)."""
    clave = clave or t.clave
    total = paginas(t.n_filas, por_pagina)
    n = min(max(1, st.session_state.get(f"pag_{clave}", 1)), total)
    if titulo:
        st.markdown(f'<p class="aud-card-t">{E._e(t.titulo)}</p>', unsafe_allow_html=True)
    if t.responde:
        st.markdown(f'<p class="tstd-resp">Responde: {E._e(t.responde)}</p>', unsafe_allow_html=True)
    encabezados = [(c.encabezado, c.tip or c.encabezado, t.derecha(i)) for i, c in enumerate(t.columnas)]
    st.markdown(E.tabla_estandar(encabezados, pagina(t.filas, n, por_pagina), f"{t.titulo}. {texto_filas(t, por_pagina)}"), unsafe_allow_html=True)
    if t.nota:
        st.markdown(f'<p class="tstd-nota">{E._e(F.texto_visible(t.nota))}</p>', unsafe_allow_html=True)
    pie = texto_rango(t, n, por_pagina) if total > 1 else texto_filas(t, por_pagina)
    if t.columnas_en_csv:
        pie += f" · {F.entero(t.columnas_en_csv)} {'columna más' if t.columnas_en_csv == 1 else 'columnas más'} en la descarga"
    if total > 1:
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1.4], vertical_alignment="center")
        c1.markdown(f'<p class="tstd-pie">{E._e(pie)} · página {F.entero(n)} de {F.entero(total)}</p>', unsafe_allow_html=True)
        c2.button("Anterior", key=f"pagtab_ant_{clave}", on_click=_ir, args=(clave, -1, total), disabled=n <= 1, width="stretch")
        c3.button("Siguiente", key=f"pagtab_sig_{clave}", on_click=_ir, args=(clave, 1, total), disabled=n >= total, width="stretch")
        c4.download_button("Descargar CSV", t.csv, f"{nombre_csv or clave}.csv", "text/csv", key=f"csv_{clave}", icon=":material/download:", width="stretch")
    else:
        c1, c2 = st.columns([3, 1.4], vertical_alignment="center")
        c1.markdown(f'<p class="tstd-pie">{E._e(pie)}</p>', unsafe_allow_html=True)
        c2.download_button("Descargar CSV", t.csv, f"{nombre_csv or clave}.csv", "text/csv", key=f"csv_{clave}", icon=":material/download:", width="stretch")


def tablas_de_apoyo(tablas: list[Tabla], etiqueta: str = "Tablas de apoyo", extra: Any = None) -> None:
    """«Tablas de apoyo (N)»: un desplegable cerrado y, dentro, una tabla por sub-desplegable con su título. ``extra`` es una función opcional que dibuja algo más al final (una descarga)."""
    n = len(tablas)
    if n == 0 and extra is None:
        return
    with st.expander(f"{etiqueta} ({F.entero(n)})"):
        for t in tablas:
            with st.expander(t.titulo):
                mostrar_tabla(t)
        if extra is not None:
            extra()
