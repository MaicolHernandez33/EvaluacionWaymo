"""Estilos y componentes HTML de la página (CSS propio y estático: sin fuentes externas, sin CDN, sin imágenes remotas).

Sistema visual de F20: consola interna de revisión. Bordes de 1 px, radio de 6 px, fondo blanco y gris muy claro, UN solo acento (azul oscuro) y color semántico solo para estado
(rojo = hueco, ámbar = «en muestra»). Tipografía del sistema con «Segoe UI» primero y cifras tabulares. Sin sombras, sin bordes superiores de color, sin píldoras.

Los colores son TOKENS: cualquier color de la página sale de ``TOKENS``. ``contraste()`` calcula el contraste WCAG y la prueba de ``tests/ep3`` exige >= 4,5:1 en cada par de texto y fondo.
La guía ``docs/ep3/guia_estilo_pagina.md`` se genera desde aquí.
"""
from __future__ import annotations

import html

TOKENS = {
    "primario": "#1D4E89",         # el único acento: azul oscuro (títulos, enlaces, selección, celdas sanas del mapa)
    "primario_oscuro": "#14365F",
    "texto": "#1B2430",
    "texto_suave": "#4A5568",
    "fondo": "#FFFFFF",
    "superficie": "#F2F5F9",       # barra lateral, encabezados de tabla y paneles
    "borde": "#D5DCE6",
    "aviso_fondo": "#FFF4D6",      # ámbar: SOLO la etiqueta «en muestra» y el chip de estado
    "aviso_texto": "#5C3D00",
    "aviso_borde": "#C98A00",
    "hueco": "#B42318",            # rojo: SOLO huecos de cámara
    "hueco_fondo": "#FDECEA",
}
# pares (texto, fondo) que deben tener contraste >= 4,5:1
PARES_CONTRASTE = [("texto", "fondo"), ("texto", "superficie"), ("texto_suave", "fondo"), ("texto_suave", "superficie"), ("primario", "fondo"), ("primario", "superficie"),
                   ("fondo", "primario"), ("fondo", "primario_oscuro"), ("aviso_texto", "aviso_fondo"), ("hueco", "fondo"), ("hueco", "hueco_fondo")]
# curvas de la cola (F19-B7): colores y trazos distinguibles en la linea y en la leyenda, tambien en daltonismo (azul continuo / naranja quemado discontinuo / ...)
CURVAS_NOMBRES = ["Dos pasos", "Un paso", "Regla de puntos, un paso", "XGBoost (referencia)", "Ensamble E2 (referencia)"]
CURVAS_COLORES = ["#1D4E89", "#C2410C", "#6B7280", "#0B6E69", "#7C3AED"]
CURVAS_RAYAS = [[1, 0], [7, 4], [2, 3], [4, 2], [1, 0]]
ESPACIADO = {"xs": "0.25rem", "s": "0.5rem", "m": "1rem", "l": "1.5rem", "xl": "2rem"}
PILA_TIPOGRAFICA = '"Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif'
PILA_SVG = "Segoe UI, system-ui, Arial, sans-serif"
RADIO = "6px"
TAMANO_TITULO = "1.5rem"
TAMANO_METRICA = "1.5rem"
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
    """Wordmark SVG propio (sin URL ni fuentes externas) para ``st.logo``: un cuadro con una caja 3D estilizada, el nombre y, en pequeño, la versión."""
    t = TOKENS
    version = version.replace("congelada el ", "· ")             # «Solución v3 · 2026-11-14»: la línea completa no cabe en el ancho de la barra lateral
    sub = f'<text x="34" y="28" font-family="{PILA_SVG}" font-size="10" fill="{t["texto_suave"]}">{html.escape(version)}</text>' if version else ""
    return (f'<svg xmlns="{SVG_NS}" width="190" height="32" viewBox="0 0 190 32">'
            f'<rect x="0" y="4" width="24" height="24" rx="5" fill="{t["primario"]}"/>'
            f'<rect x="6" y="10" width="12" height="12" rx="2" fill="none" stroke="#FFFFFF" stroke-width="2"/>'
            f'<text x="34" y="15" font-family="{PILA_SVG}" font-size="14" font-weight="600" fill="{t["texto"]}">Auditor de etiquetas 3D</text>{sub}</svg>')


def css(presentacion: bool = False) -> str:
    """Hoja de estilos de la página. En modo presentación se agranda la tipografía y las métricas pasan a 2 x 2."""
    t = TOKENS
    escala = "1.18" if presentacion else "1"
    return f"""
<style>
:root {{ --escala: {escala}; --primario: {t['primario']}; --texto: {t['texto']}; --suave: {t['texto_suave']}; --superficie: {t['superficie']}; --borde: {t['borde']};
        --aviso-fondo: {t['aviso_fondo']}; --aviso-texto: {t['aviso_texto']}; --aviso-borde: {t['aviso_borde']}; --hueco: {t['hueco']}; --hueco-fondo: {t['hueco_fondo']};
        --radio: {RADIO}; --fuente: {PILA_TIPOGRAFICA}; }}
html, body, [data-testid="stAppViewContainer"] {{ font-size: calc(15px * var(--escala)); }}
html, body, .stApp, .stApp :is(p, label, li, a, button, input, textarea, th, td, h1, h2, h3, h4, h5, h6, summary, div) {{ font-family: var(--fuente) !important; font-variant-numeric: tabular-nums; }}
[data-testid="stMainBlockContainer"], .block-container {{ padding: 1.4rem 2rem 2rem 2rem; max-width: 1480px; }}
[data-testid="stHeader"] {{ background: transparent; height: 2.4rem; }}
h1, h2, h3, h4 {{ color: var(--texto); letter-spacing: 0; }}
[data-testid="stMainBlockContainer"] h1 {{ font-size: {TAMANO_TITULO}; font-weight: 650; line-height: 1.2; padding: 0; margin: 0; }}
[data-testid="stMainBlockContainer"] h2, [data-testid="stMainBlockContainer"] h3 {{ font-size: 1.05rem; font-weight: 650; padding: .2rem 0 .1rem 0; }}
[data-testid="stMainBlockContainer"] h4 {{ font-size: .95rem; font-weight: 650; padding: .2rem 0 .1rem 0; }}
[data-testid="stCaptionContainer"], .stCaption {{ color: var(--suave); }}
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {{ font-size: .8rem; color: var(--suave); font-weight: 600; }}
hr {{ margin: .8rem 0; border-color: var(--borde); }}
/* barra lateral: wordmark arriba, navegacion agrupada, rol y modo presentacion al pie */
[data-testid="stSidebar"] {{ background: var(--superficie); border-right: 1px solid var(--borde); width: 244px !important; min-width: 244px !important; }}
[data-baseweb="select"] > div, [data-baseweb="select"] input {{ font-size: .86rem; }}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{ overflow-x: hidden; }}
[data-testid="stSidebarContent"] {{ display: flex; flex-direction: column; min-height: 100%; }}
[data-testid="stSidebarUserContent"] {{ margin-top: auto; padding-top: 1rem; border-top: 1px solid var(--borde); }}
[data-testid="stSidebarHeader"] {{ padding: 1rem 1rem .4rem 1rem; }}
[data-testid="stSidebarHeader"] img {{ width: 190px !important; max-width: none !important; height: 32px !important; }}
[data-testid="stSidebarNavLink"] {{ border-radius: var(--radio); padding: .3rem .6rem; font-size: .92rem; }}
[data-testid="stSidebarNavLink"]:hover {{ background: #E4EAF2; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{ background: #DCE5F1; font-weight: 650; color: var(--primario); }}
[data-testid="stSidebarNavSeparator"], [data-testid="stNavSectionHeader"], [data-testid="stSidebarNav"] header {{ font-size: .7rem; text-transform: uppercase; letter-spacing: .06em; color: var(--suave); }}
/* encabezado de pagina: titulo pequeno, una linea y el chip de estado a la derecha */
[data-testid="stMarkdownContainer"] .aud-descripcion {{ color: var(--suave); font-size: .92rem; margin: .15rem 0 .7rem 0; }}
.st-key-chip_estado {{ display: flex; justify-content: flex-end; }}
.st-key-chip_estado button {{ background: var(--aviso-fondo); color: var(--aviso-texto); border: 1px solid var(--aviso-borde); border-radius: var(--radio); font-size: .8rem; font-weight: 600; padding: .2rem .7rem; min-height: 0; }}
.st-key-chip_estado button:hover {{ background: #FFEDB8; border-color: var(--aviso-texto); color: var(--aviso-texto); }}
.aud-muestra {{ display: inline-block; vertical-align: middle; margin-left: .4rem; padding: 0 .35rem; border: 1px solid var(--aviso-borde); border-radius: 4px; background: var(--aviso-fondo); color: var(--aviso-texto);
               font-size: .68rem; font-weight: 600; line-height: 1.25rem; white-space: nowrap; font-variant-numeric: normal; }}
/* franja de metricas compactas: misma altura, sin bordes de color, sin sombras */
.aud-metricas {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: .6rem; margin: .5rem 0 .8rem 0; }}
.aud-metricas.pres {{ grid-template-columns: repeat(2, 1fr); }}
@media (max-width: 900px) {{ .aud-metricas {{ grid-template-columns: repeat(2, 1fr); }} }}
.aud-metrica {{ background: var(--superficie); border: 1px solid var(--borde); border-radius: var(--radio); padding: .55rem .8rem; display: flex; flex-direction: column; justify-content: space-between; min-height: 4.6rem; }}
.aud-metrica .et {{ color: var(--suave); font-size: .78rem; font-weight: 600; margin: 0; }}
.aud-metrica .va {{ color: var(--texto); font-size: {TAMANO_METRICA}; font-weight: 650; line-height: 1.2; white-space: nowrap; margin: .1rem 0 0 0; }}
.aud-metrica .no {{ color: var(--suave); font-size: .76rem; margin: 0; }}
.aud-metrica.hueco .va {{ color: var(--hueco); }}
/* filas de alerta y bloques de ficha */
.aud-fila {{ display: flex; gap: .6rem; align-items: baseline; padding: .15rem 0; }}
.aud-punto {{ flex: 0 0 .6rem; width: .6rem; height: .6rem; border-radius: 50%; background: var(--primario); display: inline-block; }}
.aud-punto.hueco {{ background: var(--hueco); }}
.aud-punto.aviso {{ background: var(--aviso-borde); }}
.aud-fila .tt {{ font-weight: 650; }}
.aud-fila .tx {{ color: var(--suave); }}
[data-testid="stMarkdownContainer"] .aud-ficha h4 {{ margin: .9rem 0 .15rem 0; font-size: .86rem; text-transform: uppercase; letter-spacing: .04em; color: var(--suave); }}
[data-testid="stMarkdownContainer"] .aud-ficha p {{ margin: 0 0 .3rem 0; }}
.aud-resultado {{ background: var(--superficie); border: 1px solid var(--borde); border-left: 3px solid var(--primario); border-radius: var(--radio); padding: .6rem .9rem; margin: .4rem 0 .5rem 0; font-size: calc(1.02rem * var(--escala)); }}
[data-testid="stMarkdownContainer"] .aud-esfuerzo {{ color: var(--suave); font-size: .9rem; margin: 0 0 .5rem 0; }}
.aud-aviso {{ background: var(--aviso-fondo); color: var(--aviso-texto); border: 1px solid var(--aviso-borde); border-radius: var(--radio); padding: .45rem .8rem; margin: .4rem 0; font-size: .9rem; }}
[data-testid="stMarkdownContainer"] .aud-probabilidad {{ font-size: {TAMANO_METRICA}; font-weight: 650; color: var(--primario); line-height: 1.2; margin: 0; white-space: nowrap; }}
.aud-pie {{ margin-top: 1.6rem; padding-top: .6rem; border-top: 1px solid var(--borde); color: var(--suave); font-size: .8rem; }}
.aud-leyenda {{ display: flex; flex-wrap: wrap; gap: .3rem 1.2rem; margin: .1rem 0 .5rem 0; font-size: .82rem; color: var(--texto); }}
.aud-ley {{ display: inline-flex; align-items: center; gap: .4rem; }}
.aud-sw {{ display: inline-block; width: 2rem; height: .9rem; border: 1px solid var(--borde); border-radius: 3px; text-align: center; font-weight: 800; line-height: .9rem; font-size: .75rem; }}
.aud-sw.escala {{ background: linear-gradient(90deg, #F2F5F9, #1D4E89); }}
.aud-sw.rayado {{ background: repeating-linear-gradient(45deg, #D5DAE2 0 3px, #7A8494 3px 4px); }}
.aud-sw.hueco {{ border: 3px solid var(--hueco); color: var(--hueco); background: #FFFFFF; line-height: .5rem; }}
/* interaccion: foco y hover visibles; botones y tablas con bordes de 1 px */
:focus-visible {{ outline: 2px solid var(--primario) !important; outline-offset: 2px; }}
.stButton > button, .stDownloadButton > button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-tertiary"] {{ border-radius: var(--radio); font-weight: 600; border: 1px solid var(--borde); }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color: var(--primario); color: var(--primario); background: #EAF0F7; }}
[data-testid="stDataFrame"] {{ border: 1px solid var(--borde); border-radius: var(--radio); }}
[data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: var(--radio); }}
[data-testid="stExpander"] details {{ border: 1px solid var(--borde); border-radius: var(--radio); }}
[data-testid="stTabs"] button {{ font-size: .9rem; }}
[data-testid="stTable"] table {{ border: 1px solid var(--borde); border-radius: var(--radio); font-size: .9rem; }}
[data-testid="stTable"] th {{ background: var(--superficie); color: var(--suave); font-weight: 650; text-align: left; }}
[data-testid="stTable"] td {{ vertical-align: top; }}
[data-testid="stTable"] th, [data-testid="stTable"] td {{ padding: .3rem .55rem; font-size: .84rem; }}
[data-testid="stTable"] th {{ white-space: nowrap; }}
.aud-tabla {{ width: 100%; border-collapse: collapse; border: 1px solid var(--borde); font-size: .9rem; }}
.aud-tabla th {{ background: var(--superficie); color: var(--suave); font-weight: 650; text-align: left; padding: .35rem .6rem; border-bottom: 1px solid var(--borde); }}
.aud-tabla td {{ padding: .35rem .6rem; border-bottom: 1px solid var(--borde); vertical-align: top; }}
.aud-tabla td:first-child {{ font-weight: 650; white-space: nowrap; width: 12rem; }}
/* cargador de archivos en espanol (F19-B6): se oculta el texto en ingles del cargador y se muestra el equivalente; si una version de Streamlit cambia estos atributos,
   el texto en ingles reaparece (la prueba de contenido lo documenta) pero la pagina sigue funcionando */
[data-testid="stFileUploaderDropzoneInstructions"] span {{ font-size: 0 !important; line-height: 0; }}
[data-testid="stFileUploaderDropzoneInstructions"] span::before {{ content: "Arrastre el archivo aquí · Parquet, hasta 500 MB"; font-size: .9rem; line-height: 1.4; }}
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p {{ font-size: 0 !important; }}
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p::before {{ content: "Elegir archivo"; font-size: .9rem; }}
</style>
"""


def _e(x: object) -> str:
    return html.escape(str(x), quote=True)


def etiqueta_muestra() -> str:
    """Etiqueta pequeña «en muestra» que va al lado de cada cifra del flujo en dos pasos."""
    return '<span class="aud-muestra">en muestra</span>'


def metricas(items: list[tuple[str, str, str, str]], presentacion: bool = False) -> str:
    """Franja de métricas compactas. ``items``: lista de (etiqueta, valor, nota, tono); tono '' o 'hueco'. En modo presentación van 2 x 2 (nunca una tarjeta huérfana)."""
    celdas = "".join(f'<div class="aud-metrica {tono}"><p class="et">{_e(et)}</p><p class="va">{_e(va)}</p><p class="no">{_e(no) if no else "&nbsp;"}</p></div>' for et, va, no, tono in items)
    return f'<div class="aud-metricas{" pres" if presentacion else ""}">{celdas}</div>'


def fila_alerta(titulo: str, texto: str, tono: str = "") -> str:
    """Fila compacta de alerta: punto de color de estado, título y texto."""
    return f'<div class="aud-fila"><span class="aud-punto {tono}"></span><div><span class="tt">{_e(titulo)}.</span> <span class="tx">{_e(texto)}</span></div></div>'


def ficha(titulo: str, texto: str) -> str:
    """Bloque de la ficha del sistema (Ética y límites): título pequeño y texto."""
    return f'<div class="aud-ficha"><h4>{_e(titulo)}</h4><p>{_e(texto)}</p></div>'


def leyenda_mapa(min_cajas: int) -> str:
    """UNA sola leyenda en palabras del mapa de calor: escala de pares, celda sin datos (gris rayado) y hueco (rojo con X)."""
    return ('<div class="aud-leyenda">'
            '<span class="aud-ley"><span class="aud-sw escala"></span>Cajas con pareja: de 0 % (casi blanco) a 100 % (azul oscuro)</span>'
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
    import re

    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _e(texto))
