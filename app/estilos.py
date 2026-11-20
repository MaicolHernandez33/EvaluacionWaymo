"""Estilos y componentes HTML de la página (CSS propio y estático: sin fuentes externas, sin CDN, sin imágenes remotas).

Sistema visual de F22: «mesa de luz de sensores». Barra lateral de tinta oscura, lienzo gris azulado muy claro con tarjetas blancas elevadas, cobalto como acento principal,
verde azulado para lo sano (celdas con pareja) y color semántico reservado: rojo = hueco, ámbar = «en muestra». La pieza propia de la página es el anillo de cámaras
(``anillo_camaras``): un vehículo visto desde arriba con una cuña por cámara. Tipografía del sistema con «Segoe UI» primero y cifras tabulares.

Los colores son TOKENS: cualquier color de la página sale de ``TOKENS``. ``contraste()`` calcula el contraste WCAG y la prueba de ``tests/ep3`` exige >= 4,5:1 en cada par de texto y fondo.
La guía ``docs/ep3/guia_estilo_pagina.md`` se genera desde aquí.
"""
from __future__ import annotations

import html
import math
import re

TOKENS = {
    "primario": "#2457D6",         # acento principal: cobalto (títulos de página, enlaces, selección, barras de datos, cuña activa)
    "primario_oscuro": "#1B3F9E",
    "primario_fondo": "#E8EEFC",   # fondo de apoyo del cobalto (resultado, selección)
    "texto": "#14202F",
    "texto_suave": "#4B586B",
    "fondo": "#F6F8FB",            # lienzo de la página
    "superficie": "#EAEFF6",       # controles, encabezados de tabla y paneles tenues
    "tarjeta": "#FFFFFF",          # tarjetas elevadas
    "borde": "#D8E0EB",
    "sano": "#0B6B74",             # verde azulado: celdas con pareja
    "sano_fondo": "#E3F3F4",
    "tinta": "#0F1B2D",            # barra lateral
    "tinta_2": "#1B2D4A",          # elemento activo y controles de la barra lateral
    "tinta_texto": "#E8EEF7",
    "tinta_suave": "#A8B7CC",
    "tinta_acento": "#8DB0FF",     # cobalto claro sobre la tinta
    "aviso_fondo": "#FFF4D6",      # ámbar: SOLO la etiqueta «en muestra» y el chip de estado
    "aviso_texto": "#5C3D00",
    "aviso_borde": "#C98A00",
    "hueco": "#B42318",            # rojo: SOLO huecos de cámara
    "hueco_fondo": "#FDECEA",
}
# pares (texto, fondo) que deben tener contraste >= 4,5:1
PARES_CONTRASTE = [("texto", "fondo"), ("texto", "tarjeta"), ("texto", "superficie"), ("texto_suave", "fondo"), ("texto_suave", "tarjeta"), ("texto_suave", "superficie"),
                   ("primario", "fondo"), ("primario", "tarjeta"), ("primario", "superficie"), ("primario_oscuro", "primario_fondo"), ("primario", "primario_fondo"), ("tarjeta", "primario"),
                   ("sano", "tarjeta"), ("sano", "sano_fondo"), ("tinta_texto", "tinta"), ("tinta_suave", "tinta"), ("tinta_texto", "tinta_2"), ("tinta_suave", "tinta_2"), ("tinta_acento", "tinta"),
                   ("aviso_texto", "aviso_fondo"), ("hueco", "tarjeta"), ("hueco", "fondo"), ("hueco", "hueco_fondo")]
# curvas de la cola (F19-B7): colores y trazos distinguibles en la linea y en la leyenda, tambien en daltonismo (azul continuo / naranja quemado discontinuo / ...)
CURVAS_NOMBRES = ["Dos pasos", "Un paso", "Regla de puntos, un paso", "XGBoost (referencia)", "Ensamble E2 (referencia)"]
CURVAS_COLORES = ["#2457D6", "#B45309", "#6B7280", "#0B6E69", "#7C3AED"]       # F22: «Un paso» pasa a un ocre quemado (contraste 1,23 con el cobalto y distinto del rojo de hueco)
CURVAS_RAYAS = [[1, 0], [7, 4], [2, 3], [4, 2], [1, 0]]
ESPACIADO = {"xs": "0.25rem", "s": "0.5rem", "m": "1rem", "l": "1.5rem", "xl": "2rem"}
PILA_TIPOGRAFICA = '"Segoe UI Variable Text", "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif'
PILA_SVG = "Segoe UI, system-ui, Arial, sans-serif"
RADIO = "10px"
RADIO_CONTROL = "8px"
TAMANO_TITULO = "1.65rem"
TAMANO_METRICA = "1.75rem"
SOMBRA = "0 1px 2px rgba(15, 27, 45, .06), 0 6px 16px rgba(15, 27, 45, .05)"
SVG_NS = "http://www.w3.org/2000/svg"       # declaracion de espacio de nombres del SVG propio: no es una peticion de red


def _lum(hex_: str) -> float:
    h = hex_.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(fg: str, bg: str) -> float:
    """Razón de contraste WCAG entre dos colores hexadecimales (1 a 21)."""
    a, b = sorted((_lum(fg), _lum(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def wordmark(version: str = "") -> str:
    """Wordmark SVG propio (sin URL ni fuentes externas) para ``st.logo``, claro sobre la tinta de la barra lateral: un cuadro con una caja 3D estilizada, el nombre y, en pequeño, la versión."""
    t = TOKENS
    version = version.replace("congelada el ", "· ")             # «Solución v3 · 2026-11-14»: la línea completa no cabe en el ancho de la barra lateral
    sub = f'<text x="36" y="29" font-family="{PILA_SVG}" font-size="10" fill="{t["tinta_suave"]}">{html.escape(version)}</text>' if version else ""
    return (f'<svg xmlns="{SVG_NS}" width="196" height="34" viewBox="0 0 196 34">'
            f'<rect x="0" y="4" width="26" height="26" rx="7" fill="{t["primario"]}"/>'
            f'<rect x="7" y="11" width="12" height="12" rx="2.5" fill="none" stroke="#FFFFFF" stroke-width="2"/>'
            f'<path d="M19 11 L22 8 M19 23 L22 20 M7 11 L10 8" stroke="#FFFFFF" stroke-width="1.4" stroke-linecap="round" fill="none" opacity=".7"/>'
            f'<text x="36" y="16" font-family="{PILA_SVG}" font-size="14" font-weight="600" fill="{t["tinta_texto"]}">Auditor de etiquetas 3D</text>{sub}</svg>')


_CSS_BASE = """
<style>
:root { --escala: @ESCALA@; --primario: @primario@; --po: @primario_oscuro@; --pf: @primario_fondo@; --texto: @texto@; --suave: @texto_suave@; --fondo: @fondo@; --superficie: @superficie@;
        --tarjeta: @tarjeta@; --borde: @borde@; --sano: @sano@; --sano-fondo: @sano_fondo@; --tinta: @tinta@; --tinta2: @tinta_2@; --tinta-texto: @tinta_texto@; --tinta-suave: @tinta_suave@;
        --tinta-acento: @tinta_acento@; --aviso-fondo: @aviso_fondo@; --aviso-texto: @aviso_texto@; --aviso-borde: @aviso_borde@; --hueco: @hueco@; --hueco-fondo: @hueco_fondo@;
        --radio: @RADIO@; --radio-ctl: @RADIO_CONTROL@; --sombra: @SOMBRA@; --fuente: @FUENTE@; --t: 150ms cubic-bezier(.2, .7, .3, 1); }
html, body, [data-testid="stAppViewContainer"] { font-size: calc(15px * var(--escala)); }
html, body, .stApp, .stApp :is(p, label, li, a, button, input, textarea, th, td, h1, h2, h3, h4, h5, h6, summary, div) { font-family: var(--fuente) !important; font-variant-numeric: tabular-nums; }
[data-testid="stMainBlockContainer"], .block-container { padding: 1.5rem 2.2rem 2.2rem 2.2rem; max-width: 1480px; }
[data-testid="stHeader"] { background: transparent; height: 2.4rem; }
h1, h2, h3, h4 { color: var(--texto); }
[data-testid="stMainBlockContainer"] h1 { font-size: @TITULO@; font-weight: 680; line-height: 1.15; letter-spacing: -.012em; padding: 0; margin: 0; }
[data-testid="stMainBlockContainer"] h2, [data-testid="stMainBlockContainer"] h3 { font-size: 1.08rem; font-weight: 650; padding: .2rem 0 .1rem 0; }
[data-testid="stMainBlockContainer"] h4 { font-size: .98rem; font-weight: 650; letter-spacing: -.005em; padding: .35rem 0 .15rem 0; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--suave); }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { font-size: .8rem; color: var(--suave); font-weight: 600; }
hr { margin: .8rem 0; border-color: var(--borde); }

/* barra lateral de tinta: wordmark arriba, navegacion agrupada, rol y modo presentacion al pie */
[data-testid="stSidebar"] { background: var(--tinta); border-right: 0; width: 248px !important; min-width: 248px !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { overflow-x: hidden; }
[data-testid="stSidebarContent"] { display: flex; flex-direction: column; min-height: 100%; }
[data-testid="stSidebarUserContent"] { margin-top: auto; padding-top: 1rem; border-top: 1px solid rgba(255, 255, 255, .10); }
[data-testid="stSidebarHeader"] { padding: 1.1rem 1rem .6rem 1rem; }
[data-testid="stSidebarHeader"] img { width: 196px !important; max-width: none !important; height: 34px !important; }
[data-testid="stSidebar"] :is(p, label, span, summary) { color: var(--tinta-texto); }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: var(--tinta-suave); }
[data-testid="stSidebarNavLink"] { border-radius: var(--radio-ctl); padding: .38rem .65rem; font-size: .92rem; color: var(--tinta-suave); transition: background var(--t), color var(--t); }
[data-testid="stSidebarNavLink"] :is(span, p) { color: inherit; }
[data-testid="stSidebarNavLink"]:hover { background: rgba(255, 255, 255, .07); color: var(--tinta-texto); }
[data-testid="stSidebarNavLink"][aria-current="page"] { background: var(--tinta2); font-weight: 650; color: #FFFFFF; box-shadow: inset 3px 0 0 var(--tinta-acento); }
[data-testid="stSidebarNavSeparator"], [data-testid="stNavSectionHeader"], [data-testid="stSidebarNav"] header { font-size: .76rem; font-weight: 600; color: var(--tinta-suave); letter-spacing: .01em; }
[data-baseweb="select"] > div, [data-baseweb="select"] input { font-size: .88rem; }

/* encabezado de pagina: titulo, una linea y el chip de estado a la derecha */
[data-testid="stMarkdownContainer"] .aud-descripcion { color: var(--suave); font-size: .94rem; margin: .2rem 0 .8rem 0; }
[data-testid="stColumn"]:has(.st-key-chip_estado) { display: flex; flex-direction: column; align-items: flex-end; }
.st-key-chip_estado { display: flex; justify-content: flex-end; margin-left: auto; }
.st-key-chip_estado button { background: var(--aviso-fondo); color: var(--aviso-texto); border: 1px solid var(--aviso-borde); border-radius: var(--radio-ctl); font-size: .8rem; font-weight: 600; padding: .2rem .7rem; min-height: 0; transition: background var(--t), border-color var(--t); }
.st-key-chip_estado button:hover { background: #FFEDB8; border-color: var(--aviso-texto); color: var(--aviso-texto); }
.aud-muestra { display: inline-block; vertical-align: middle; margin-left: .4rem; padding: 0 .35rem; border: 1px solid var(--aviso-borde); border-radius: 4px; background: var(--aviso-fondo); color: var(--aviso-texto);
               font-size: .68rem; font-weight: 600; line-height: 1.25rem; white-space: nowrap; font-variant-numeric: normal; }

/* tarjetas: lienzo claro y tarjetas blancas elevadas */
[data-testid="stVerticalBlockBorderWrapper"] { background: var(--tarjeta); border-radius: var(--radio); box-shadow: var(--sombra); }
.aud-metricas { display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin: .5rem 0 1rem 0; }
.aud-metricas.pres { grid-template-columns: repeat(2, 1fr); }
@media (max-width: 900px) { .aud-metricas { grid-template-columns: repeat(2, 1fr); } }
.aud-metrica { background: var(--tarjeta); border: 1px solid var(--borde); border-radius: var(--radio); box-shadow: var(--sombra); padding: .7rem .9rem .65rem .9rem; display: flex; flex-direction: column; justify-content: space-between; min-height: 5.6rem; }
.aud-metrica .ca { display: flex; align-items: center; gap: .5rem; }
.aud-metrica .gl { flex: 0 0 1.5rem; width: 1.5rem; height: 1.5rem; border-radius: 7px; background: var(--pf); display: inline-flex; align-items: center; justify-content: center; }
.aud-metrica.hueco .gl { background: var(--hueco-fondo); }
.aud-metrica .gl svg { width: 1rem; height: 1rem; }
.aud-metrica .et { color: var(--suave); font-size: .8rem; font-weight: 600; margin: 0; }
.aud-metrica .va { color: var(--texto); font-size: @METRICA@; font-weight: 680; line-height: 1.15; letter-spacing: -.015em; white-space: nowrap; margin: .35rem 0 0 0; }
.aud-metrica .no { color: var(--suave); font-size: .78rem; margin: .1rem 0 0 0; }
.aud-metrica.hueco .va { color: var(--hueco); }

/* filas de alerta y bloques de ficha */
.aud-fila { display: flex; gap: .6rem; align-items: baseline; padding: .15rem 0; }
.aud-punto { flex: 0 0 .6rem; width: .6rem; height: .6rem; border-radius: 50%; background: var(--primario); display: inline-block; }
.aud-punto.hueco { background: var(--hueco); }
.aud-punto.aviso { background: var(--aviso-borde); }
.aud-fila .tt { font-weight: 650; }
.aud-fila .tx { color: var(--suave); }
/* F21-P3b: el markdown de Streamlit lleva margen inferior negativo; sin quitarlo, la columna del texto queda mas baja que su contenido y el enlace se centra 8 px mas arriba que la alerta */
[class*="st-key-alerta_"] [data-testid="stMarkdown"], [class*="st-key-alerta_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
[class*="st-key-alerta_"] [data-testid="stElementContainer"] { margin-bottom: 0 !important; }
[data-testid="stMarkdownContainer"] .aud-ficha { background: var(--tarjeta); border: 1px solid var(--borde); border-radius: var(--radio); box-shadow: var(--sombra); padding: .85rem 1.1rem .75rem 1.1rem; margin: 0 0 .9rem 0; }
[data-testid="stMarkdownContainer"] .aud-ficha h4 { margin: 0 0 .3rem 0; padding: 0; font-size: .95rem; color: var(--po); }
[data-testid="stMarkdownContainer"] .aud-ficha p { margin: 0; }
.aud-resultado { background: var(--pf); border: 1px solid #C9D7F7; border-radius: var(--radio); padding: .75rem 1.05rem; margin: .5rem 0 .55rem 0; font-size: calc(1.04rem * var(--escala)); color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-esfuerzo { color: var(--suave); font-size: .9rem; margin: 0 0 .6rem 0; }
.aud-aviso { background: var(--aviso-fondo); color: var(--aviso-texto); border: 1px solid var(--aviso-borde); border-radius: var(--radio-ctl); padding: .5rem .85rem; margin: .5rem 0; font-size: .9rem; }
[data-testid="stMarkdownContainer"] .aud-probabilidad { font-size: 2.1rem; font-weight: 700; color: var(--primario); line-height: 1.1; letter-spacing: -.02em; margin: 0; white-space: nowrap; }
[data-testid="stMarkdownContainer"] .aud-nota { font-size: .86rem; color: var(--suave); background: var(--superficie); border-radius: var(--radio-ctl); padding: .3rem 7.5rem .3rem .7rem; margin: .1rem 0 .55rem 0; }   /* a la derecha queda libre el sitio de la barra de herramientas de la tabla (F21) */
.st-key-panel_detalle, .st-key-panel_vacio { margin-top: .6rem; }
.st-key-panel_detalle { animation: aud-entra 240ms cubic-bezier(.2, .7, .3, 1) both; }
@keyframes aud-entra { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.aud-pie { margin-top: 1.8rem; padding-top: .7rem; border-top: 1px solid var(--borde); color: var(--suave); font-size: .8rem; }

/* anillo de camaras y estados vacios */
.aud-anillo { display: block; }
.aud-anillo .cu { stroke-width: 1.5; transition: fill var(--t), stroke var(--t); }
.aud-anillo .cu.sana { fill: #CFE9EC; stroke: var(--sano); }
.aud-anillo .cu.hueco { fill: var(--hueco-fondo); stroke: var(--hueco); stroke-width: 2.5; }
.aud-anillo .cu.activa { fill: var(--primario); stroke: var(--po); }
.aud-anillo .cu.apagada { fill: #DDE5F0; stroke: #BFCCDF; }
.aud-anillo .nu { font-size: 12.5px; font-weight: 650; fill: var(--suave); text-anchor: middle; dominant-baseline: central; }
.aud-anillo .nu.hueco { fill: var(--hueco); }
.aud-anillo .nu.activa { fill: var(--po); }
.aud-anillo .xx { stroke: var(--hueco); stroke-width: 2.5; stroke-linecap: round; }
.aud-anillo .auto { fill: var(--tarjeta); stroke: var(--borde); stroke-width: 1.5; }
.aud-anillo .parabrisas { stroke: var(--borde); stroke-width: 1.5; stroke-linecap: round; }
.aud-tarjeta-anillo > div { flex: 1 1 10rem; }
.aud-tarjeta-anillo svg { flex: 0 0 auto; }
.aud-tarjeta-anillo { display: flex; flex-wrap: wrap; gap: .6rem 1rem; align-items: center; background: var(--tarjeta); border: 1px solid var(--borde); border-radius: var(--radio); box-shadow: var(--sombra); padding: .8rem 1rem; }
.aud-tarjeta-anillo .tt { margin: 0 0 .25rem 0; font-weight: 650; }
.aud-tarjeta-anillo .tx { margin: 0; color: var(--suave); font-size: .88rem; }
.aud-vacio { display: flex; gap: 1rem; align-items: center; padding: .4rem .2rem; }
.aud-vacio .tt { margin: 0 0 .2rem 0; font-weight: 650; }
.aud-vacio .tx { margin: 0; color: var(--suave); font-size: .9rem; }
.aud-leyenda { display: flex; flex-wrap: wrap; gap: .3rem 1.2rem; margin: .1rem 0 .6rem 0; font-size: .82rem; color: var(--texto); }
.aud-ley { display: inline-flex; align-items: center; gap: .4rem; }
.aud-sw { display: inline-block; width: 2rem; height: .9rem; border: 1px solid var(--borde); border-radius: 3px; text-align: center; font-weight: 800; line-height: .9rem; font-size: .75rem; }
.aud-sw.escala { background: linear-gradient(90deg, @escala_ini@, @sano@); }
.aud-sw.rayado { background: repeating-linear-gradient(45deg, #D5DAE2 0 3px, #7A8494 3px 4px); }
.aud-sw.hueco { border: 3px solid var(--hueco); color: var(--hueco); background: #FFFFFF; line-height: .5rem; }

/* interaccion: foco y hover visibles, transiciones suaves; botones y tablas con bordes de 1 px */
:focus-visible { outline: 2px solid var(--primario) !important; outline-offset: 2px; }
[data-testid="stSidebar"] :focus-visible { outline-color: var(--tinta-acento) !important; }
.stButton > button, .stDownloadButton > button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-tertiary"] { border-radius: var(--radio-ctl); font-weight: 600; border: 1px solid var(--borde);
        transition: background var(--t), border-color var(--t), color var(--t), box-shadow var(--t); }
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--primario); color: var(--primario); background: var(--pf); box-shadow: 0 1px 2px rgba(15, 27, 45, .08); }
.stButton > button:active, .stDownloadButton > button:active { background: #D9E4FA; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"] { transition: border-color var(--t), box-shadow var(--t); }
[data-testid="stDataFrame"] { border: 1px solid var(--borde); border-radius: var(--radio); box-shadow: var(--sombra); overflow: hidden; }
[data-testid="stExpander"] details { background: var(--tarjeta); border: 1px solid var(--borde); border-radius: var(--radio); box-shadow: var(--sombra); }
[data-testid="stExpander"] summary { border-radius: var(--radio); transition: background var(--t); }
[data-testid="stExpander"] summary:hover { background: var(--superficie); }
[data-testid="stTabs"] button { font-size: .92rem; font-weight: 600; transition: color var(--t), background var(--t); }
[data-testid="stTabs"] button:hover { background: var(--pf); }
[data-testid="stTable"] table { background: var(--tarjeta); border: 1px solid var(--borde); border-radius: var(--radio); font-size: .9rem; }
[data-testid="stTable"] th { background: var(--superficie); color: var(--suave); font-weight: 650; text-align: left; white-space: nowrap; }
[data-testid="stTable"] td { vertical-align: top; }
[data-testid="stTable"] th, [data-testid="stTable"] td { padding: .35rem .6rem; font-size: .84rem; }
[data-testid="stTable"] tbody tr { transition: background var(--t); }
[data-testid="stTable"] tbody tr:hover { background: var(--pf); }
.aud-tabla { width: 100%; border-collapse: separate; border-spacing: 0; background: var(--tarjeta); border: 1px solid var(--borde); border-radius: var(--radio); box-shadow: var(--sombra); overflow: hidden; font-size: .9rem; }
.aud-tabla th { background: var(--superficie); color: var(--suave); font-weight: 650; text-align: left; padding: .45rem .7rem; border-bottom: 1px solid var(--borde); }
.aud-tabla td { padding: .45rem .7rem; border-bottom: 1px solid var(--borde); vertical-align: top; }
.aud-tabla tbody tr:last-child td { border-bottom: 0; }
.aud-tabla tbody tr { transition: background var(--t); }
.aud-tabla tbody tr:hover { background: var(--pf); }
.aud-tabla td:first-child { font-weight: 650; white-space: nowrap; width: 12rem; }
/* cargador de archivos en espanol (F19-B6): se oculta el texto en ingles del cargador y se muestra el equivalente; si una version de Streamlit cambia estos atributos,
   el texto en ingles reaparece (la prueba de contenido lo documenta) pero la pagina sigue funcionando */
[data-testid="stFileUploaderDropzone"] { background: var(--tarjeta); border: 1.5px dashed #9DB5EA; border-radius: var(--radio); transition: background var(--t), border-color var(--t); }
[data-testid="stFileUploaderDropzone"]:hover { background: var(--pf); border-color: var(--primario); }
[data-testid="stFileUploaderDropzoneInstructions"] span { font-size: 0 !important; line-height: 0; }
[data-testid="stFileUploaderDropzoneInstructions"] span::before { content: "Arrastre el archivo aquí · Parquet, hasta 500 MB"; font-size: .9rem; line-height: 1.4; }
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p { font-size: 0 !important; }
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p::before { content: "Elegir archivo"; font-size: .9rem; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
"""


def css(presentacion: bool = False) -> str:
    """Hoja de estilos de la página. En modo presentación se agranda la tipografía y las métricas pasan a 2 x 2."""
    reemplazos = {**TOKENS, "ESCALA": "1.18" if presentacion else "1", "RADIO": RADIO, "RADIO_CONTROL": RADIO_CONTROL, "SOMBRA": SOMBRA, "FUENTE": PILA_TIPOGRAFICA,
                  "TITULO": TAMANO_TITULO, "METRICA": TAMANO_METRICA, "escala_ini": "#E6F3F4"}
    return re.sub(r"@(\w+)@", lambda m: reemplazos[m.group(1)], _CSS_BASE)


def _e(x: object) -> str:
    """Escapa para HTML y une cada «%» con su número con un espacio de no separación (F21): «79,8 %» no se parte entre dos líneas."""
    return re.sub(r"(?<=\d) %", " %", html.escape(str(x), quote=True))


def etiqueta_muestra() -> str:
    """Etiqueta pequeña «en muestra» que va al lado de cada cifra del flujo en dos pasos."""
    return '<span class="aud-muestra">en muestra</span>'


def _glifo(tono: str) -> str:
    """Glifo de 16 px de una métrica: caja 3D en cobalto, o caja con una X en rojo si es de hueco (nunca solo color)."""
    if tono == "hueco":
        return '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="11" height="11" rx="2.5" fill="none" stroke="#B42318" stroke-width="1.6"/><path d="M6 6 L10 10 M10 6 L6 10" stroke="#B42318" stroke-width="1.6" stroke-linecap="round"/></svg>'
    return '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="11" height="11" rx="2.5" fill="none" stroke="#2457D6" stroke-width="1.6"/><rect x="5.5" y="5.5" width="5" height="5" rx="1" fill="#2457D6"/></svg>'


def metricas(items: list[tuple[str, str, str, str]], presentacion: bool = False) -> str:
    """Franja de métricas. ``items``: lista de (etiqueta, valor, nota, tono); tono '' o 'hueco'. En modo presentación van 2 x 2 (nunca una tarjeta huérfana)."""
    celdas = "".join(f'<div class="aud-metrica {tono}"><div class="ca"><span class="gl">{_glifo(tono)}</span><p class="et">{_e(et)}</p></div><p class="va">{_e(va)}</p><p class="no">{_e(no) if no else "&nbsp;"}</p></div>'
                     for et, va, no, tono in items)
    return f'<div class="aud-metricas{" pres" if presentacion else ""}">{celdas}</div>'


def fila_alerta(titulo: str, texto: str, tono: str = "") -> str:
    """Fila compacta de alerta: punto de color de estado, título y texto."""
    return f'<div class="aud-fila"><span class="aud-punto {tono}"></span><div><span class="tt">{_e(titulo)}.</span> <span class="tx">{_e(texto)}</span></div></div>'


def ficha(titulo: str, texto: str) -> str:
    """Bloque de la ficha del sistema (Ética y límites): título y texto en una tarjeta."""
    return f'<div class="aud-ficha"><h4>{_e(titulo)}</h4><p>{_e(texto)}</p></div>'


# ------------------------------------------------------------------------------------------------------------ anillo de cámaras
# Cada cámara cubre una cuña del anillo (ángulos desde el frente, en grados, positivo = derecha). La parte trasera no tiene cámara.
ANGULOS_CAMARA = {1: (-22, 22), 2: (-78, -22), 3: (22, 78), 4: (-138, -78), 5: (78, 138)}
NOMBRES_CAMARA = {1: "frontal", 2: "frontal izquierda", 3: "frontal derecha", 4: "lateral izquierda", 5: "lateral derecha"}
ESTADOS_ANILLO = ("sana", "hueco", "activa", "apagada")


def _punto(r: float, grados: float, c: float = 90.0) -> tuple[float, float]:
    a = math.radians(grados)
    return c + r * math.sin(a), c - r * math.cos(a)


def anillo_camaras(estados: dict[int, str], tamano: int = 150, descripcion: str = "") -> str:
    """Anillo de las 5 cámaras: un vehículo visto desde arriba con una cuña por cámara.

    ``estados``: {número de cámara: 'sana' | 'hueco' | 'activa' | 'apagada'}. El hueco lleva contorno rojo grueso y una «X» (el rojo nunca va solo); la cámara activa es cobalto
    sólido (la que ve una caja). SVG inline, sin URL ni fuentes. ``descripcion`` es el texto alternativo.
    """
    r0, r1, hueco = 33.0, 66.0, 2.0
    partes = ['<rect class="auto" x="75" y="62" width="30" height="56" rx="9"/><path class="parabrisas" d="M80 78 L100 78"/>']
    for cam, (a0, a1) in ANGULOS_CAMARA.items():
        est = estados.get(cam, "apagada")
        if est not in ESTADOS_ANILLO:
            raise ValueError(f"estado de cámara desconocido: {est}")
        a0, a1 = a0 + hueco, a1 - hueco
        p1, p2, p3, p4 = _punto(r1, a0), _punto(r1, a1), _punto(r0, a1), _punto(r0, a0)
        d = f"M{p1[0]:.1f} {p1[1]:.1f} A{r1} {r1} 0 0 1 {p2[0]:.1f} {p2[1]:.1f} L{p3[0]:.1f} {p3[1]:.1f} A{r0} {r0} 0 0 0 {p4[0]:.1f} {p4[1]:.1f} Z"
        medio = (a0 + a1) / 2
        partes.append(f'<path class="cu {est}" d="{d}"/>')
        if est == "hueco":
            x, y = _punto((r0 + r1) / 2, medio)
            partes.append(f'<path class="xx" d="M{x - 4:.1f} {y - 4:.1f} L{x + 4:.1f} {y + 4:.1f} M{x + 4:.1f} {y - 4:.1f} L{x - 4:.1f} {y + 4:.1f}"/>')
        nx, ny = _punto(r1 + 12, medio)
        partes.append(f'<text class="nu {est}" x="{nx:.1f}" y="{ny:.1f}">{cam}</text>')
    if not descripcion:
        con = [f"{c} ({NOMBRES_CAMARA[c]})" for c in ANGULOS_CAMARA if estados.get(c) == "hueco"]
        descripcion = "Cámaras con celdas marcadas: " + (", ".join(con) if con else "ninguna")
    alto = round(tamano * 150 / 156)                                                  # sin la parte trasera (no tiene cámaras) la caja del dibujo es más baja que ancha
    return f'<svg class="aud-anillo" width="{tamano}" height="{alto}" viewBox="12 6 156 150" role="img" aria-label="{html.escape(descripcion, quote=True)}">{"".join(partes)}</svg>'


def tarjeta_anillo(titulo: str, texto: str, estados: dict[int, str], tamano: int = 132) -> str:
    """Tarjeta con el anillo de cámaras a la izquierda, un título y una línea de texto."""
    return f'<div class="aud-tarjeta-anillo">{anillo_camaras(estados, tamano)}<div><p class="tt">{_e(titulo)}</p><p class="tx">{_e(texto).replace(chr(10), "<br>")}</p></div></div>'


def vacio(titulo: str, texto: str, anillo: str = "") -> str:
    """Estado vacío: un dibujo opcional, qué falta (título) y qué hacer (texto)."""
    return f'<div class="aud-vacio">{anillo}<div><p class="tt">{_e(titulo)}</p><p class="tx">{_e(texto)}</p></div></div>'


def leyenda_mapa(min_cajas: int) -> str:
    """UNA sola leyenda en palabras del mapa de calor: escala de pares, celda sin datos (gris rayado) y hueco (rojo con X)."""
    return ('<div class="aud-leyenda">'
            '<span class="aud-ley"><span class="aud-sw escala"></span>Cajas con pareja: de 0 % (casi blanco) a 100 % (verde azulado oscuro)</span>'
            f'<span class="aud-ley"><span class="aud-sw rayado"></span>Sin cajas o menos de {min_cajas} en el rango: no se evalúa (no es lo mismo que 0 %)</span>'
            f'<span class="aud-ley"><span class="aud-sw hueco">X</span>Hueco: menos del 25 % de lo normal de esa cámara con al menos {min_cajas} cajas</span>'
            '<span class="aud-ley">Cámaras: 1 frontal · 2 frontal izq. · 3 frontal der. · 4 lateral izq. · 5 lateral der.</span>'
            '</div>')


def resultado(markdown_html: str, tono: str = "") -> str:
    """Bloque de resultado (el contenido ya viene como HTML seguro construido por la página)."""
    return f'<div class="aud-resultado {tono}">{markdown_html}</div>'


def pie(version: str, segmentos: int | None = None) -> str:
    """Pie único y discreto: versión y fuente de datos."""
    datos = f"Datos de desarrollo ({segmentos} segmentos)" if segmentos else "Datos de desarrollo"
    return f'<div class="aud-pie">{_e(version)} · Waymo Open Dataset v2, uso académico · {_e(datos)}</div>'


def tabla_html(filas: list[tuple[str, str]], encabezados: tuple[str, str]) -> str:
    """Tabla de dos columnas (término, definición) con el texto ajustado a la celda: sin desplazamiento ni acordeones."""
    cuerpo = "".join(f"<tr><td>{_e(a)}</td><td>{_e(b)}</td></tr>" for a, b in filas)
    return f'<table class="aud-tabla"><thead><tr><th>{_e(encabezados[0])}</th><th>{_e(encabezados[1])}</th></tr></thead><tbody>{cuerpo}</tbody></table>'


def md_a_html(texto: str) -> str:
    """Escapa el texto y convierte **negrita** en <strong> (lo único de Markdown que usan los textos de resultado)."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _e(texto))
