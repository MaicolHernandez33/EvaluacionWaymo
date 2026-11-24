"""Estilos y componentes HTML de la página (CSS propio y estático: sin fuentes externas, sin CDN, sin imágenes remotas).

Sistema visual de F24: tema oscuro tipo consola de control. La estructura es la de F23 (afirmación y anillo en el Resumen, una sola superficie elevada, tablas planas); F24 cambia la piel:
lienzo azul noche, barra lateral un tono más claro con una línea derecha, panel y panel alto como únicas superficies, **una sola familia sans** (Inter si está en el repo; si no, Segoe UI),
acento azul claro, teal para lo sano, rojo coral solo para el hueco (siempre con «X» y texto) y ámbar solo para advertencias reales de fiabilidad (F25: el punto de «Ciclistas»).

``TOKENS`` es la ÚNICA fuente de verdad de los colores: de aquí salen el CSS (``css()``), el tema nativo de Streamlit de los dos ``config.toml`` (``tema_toml()``, escrito por
``scripts/ep3/generar_config_tema.py``) y los gráficos. ``contraste()`` calcula el contraste WCAG y la prueba de ``tests/ep3`` exige >= 4,5:1 en cada par de ``PARES_CONTRASTE``.
La guía ``docs/ep3/guia_estilo_pagina.md`` se genera desde aquí.
"""
from __future__ import annotations

import html
import math
import re
from pathlib import Path

TOKENS = {
    "fondo": "#0B1220",            # lienzo de la página
    "barra": "#0E1729",            # barra lateral (con una línea derecha ``barra_borde``)
    "barra_borde": "#1E2B45",
    "panel": "#121C30",            # superficie principal (panel del Resumen, detalle de la cola, tablas)
    "panel_borde": "#22314D",
    "panel_alto": "#18253D",       # controles, encabezados de tabla, fila elegida
    "panel_alto_borde": "#2A3A57",
    "texto": "#E8EEF8",            # principal
    "texto_2": "#A9B8CF",          # secundario
    "texto_3": "#8696B0",          # notas: el mínimo permitido (ningún texto queda por debajo)
    "acento": "#6FA0FF",           # enlaces, selección, ítem activo, relleno del botón primario
    "acento_fondo": "#1A2B4F",     # tinte del acento: ítem activo de la barra, hover de botones
    "acento_activo": "#223A66",    # botón pulsado
    "acento_hover": "#8CB4FF",     # botón primario con el cursor encima
    "sano": "#3CC9B8",             # trazo de lo sano y extremo claro de la rampa del mapa
    "sano_relleno": "#14535A",     # relleno de la cuña sana del anillo
    "hueco": "#FF7A6B",            # SOLO hueco de cámara (trazo y X), siempre con «X» y con texto
    "hueco_fondo": "#3A1A22",
    "sin_datos": "#1B2740",        # relleno plano y neutro: «sin datos» no es una alerta
    "sin_datos_borde": "#3A4B6B",
    "aviso_texto": "#F5B73B",      # ámbar de interfaz: SOLO advertencias reales (el punto de «Ciclistas: regla poco confiable»); ya no es «en muestra» (F25)
}
# pares (texto, fondo) que deben tener contraste >= 4,5:1
PARES_CONTRASTE = [("texto", "panel"), ("texto_2", "panel"), ("texto_3", "panel"), ("acento", "panel"), ("sano", "panel"), ("hueco", "panel"),
                   ("texto", "panel_alto"), ("texto_2", "panel_alto"), ("texto_3", "panel_alto"), ("acento", "panel_alto"), ("sano", "panel_alto"),
                   ("texto", "fondo"), ("texto_2", "fondo"), ("texto_3", "fondo"), ("acento", "fondo"), ("sano", "fondo"), ("hueco", "fondo"),
                   ("texto", "barra"), ("texto_2", "barra"), ("texto_3", "barra"), ("acento", "barra"),
                   ("texto", "acento_fondo"), ("acento", "acento_fondo"), ("fondo", "acento"),
                   ("aviso_texto", "panel"), ("aviso_texto", "panel_alto"), ("hueco", "hueco_fondo"), ("fondo", "acento_hover"), ("texto", "acento_activo")]
# rampa del mapa de calor de la Auditoría: un solo tono teal, MÁS CLARO = MÁS proporción de cajas con pareja (validada con validate_palette.js --ordinal contra el panel)
RAMPA_SANA = ["#15655C", "#187F74", "#289A8C", "#32B1A2", TOKENS["sano"]]
# F25: UN concepto, UN color en todas las vistas (barras de horas del Resumen, barras de «En muestra» de Validación y curvas de la cola). El mapa entidad -> color es este;
# las curvas lo leen de aquí. Validado con validate_palette.js (modo oscuro, sobre el panel, todos los pares): f25_paleta_validacion.json. El gris es la línea base neutra (revisión sin orden).
SERIE_GRIS = TOKENS["texto_3"]
FLUJOS_COLORES = {"Revisión sin orden": SERIE_GRIS, "Solo cola (un paso)": "#C77B1E", "Auditoría + cola (dos pasos)": "#4C82F2", "Solo celdas sanas, sin auditoría": "#B0508A"}
# curvas de la cola: paleta validada con validate_palette.js en modo oscuro sobre el panel (CVD >= 8 y visión normal >= 15 entre TODOS los pares; ver f24_paleta_validacion.json).
# El trazo sigue distinto (discontinuo en XGBoost y en la regla) y las curvas de referencia llevan etiqueta directa.
CURVAS_NOMBRES = ["Dos pasos", "Un paso", "Regla de puntos, un paso", "XGBoost (referencia)", "Ensamble E2 (referencia)"]
CURVAS_COLORES = [FLUJOS_COLORES["Auditoría + cola (dos pasos)"], FLUJOS_COLORES["Solo cola (un paso)"], "#0F7C55", "#8F4AB4", "#D75893"]
CURVAS_RAYAS = [[1, 0], [7, 4], [2, 3], [4, 2], [1, 0]]
ESPACIADO = {"xs": "0.25rem", "s": "0.5rem", "m": "1rem", "l": "1.5rem", "xl": "2rem"}
ARCHIVO_INTER = Path(__file__).resolve().parent / "static" / "fonts" / "Inter-Variable.woff2"      # opcional (licencia OFL con su archivo): si está, el tema lo carga
PILA_TIPOGRAFICA = '"Inter", "Segoe UI Variable Text", "Segoe UI", system-ui, -apple-system, Arial, sans-serif'      # una sola familia sans para todo, títulos incluidos
PILA_SVG = "Inter, Segoe UI, system-ui, Arial, sans-serif"
# escala tipográfica (rem sobre una base de 15 px); pesos 400 y 600
ESCALA_TIPOGRAFICA = {"nota": "0.78rem", "secundario": "0.86rem", "cuerpo": "1rem", "destacado": "1.12rem", "titulo_pagina": "1.6rem", "titular": "1.75rem"}
# radios según el papel: tablas 0, controles 8 px, mayor solo en el panel
RADIO_PANEL = "14px"
RADIO_CONTROL = "8px"
RADIO_TABLA = "0"
TAMANO_TITULO = ESCALA_TIPOGRAFICA["titulo_pagina"]
TAMANO_TITULAR = ESCALA_TIPOGRAFICA["titular"]
TAMANO_CIFRA = "1.5rem"
SOMBRA_PANEL = "0 10px 28px rgba(0, 0, 0, .35)"      # la única sombra de la página
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


def tema_toml(raiz_fuente: Path | None = None) -> str:
    """Bloque ``[theme]`` y ``[theme.sidebar]`` de los dos ``config.toml``, generado desde ``TOKENS`` (nada de hex sueltos en otros archivos).

    Si ``app/static/fonts/Inter-Variable.woff2`` existe se agrega ``[[theme.fontFaces]]`` y se usa «Inter»; si no, la pila de sistema (que fija el CSS). Escribe ``scripts/ep3/generar_config_tema.py``.
    """
    t = TOKENS
    hay_inter = (raiz_fuente if raiz_fuente is not None else ARCHIVO_INTER).exists()
    lineas = ["[theme]", 'base = "dark"', f'primaryColor = "{t["acento"]}"', f'backgroundColor = "{t["fondo"]}"', f'secondaryBackgroundColor = "{t["panel_alto"]}"', f'textColor = "{t["texto"]}"',
              'font = "Inter"' if hay_inter else 'font = "sans serif"', f'baseRadius = "0.5rem"', f'buttonRadius = "0.5rem"', f'borderColor = "{t["panel_alto_borde"]}"',
              f'linkColor = "{t["acento"]}"', "linkUnderline = true", f'dataframeBorderColor = "{t["panel_borde"]}"', f'dataframeHeaderBackgroundColor = "{t["panel_alto"]}"',
              f'dataframeHeaderTextColor = "{t["texto_2"]}"', "showWidgetBorder = true", "showSidebarBorder = true", "",
              "[theme.sidebar]", f'backgroundColor = "{t["barra"]}"', f'secondaryBackgroundColor = "{t["panel_alto"]}"', f'textColor = "{t["texto"]}"', f'primaryColor = "{t["acento"]}"',
              f'borderColor = "{t["barra_borde"]}"']
    if hay_inter:
        lineas += ["", "[[theme.fontFaces]]", 'family = "Inter"', 'url = "app/static/fonts/Inter-Variable.woff2"', 'weight = "100 900"']
    return "\n".join(lineas) + "\n"


# F26: símbolo propio y original (sin relación con el logo ni los colores de marca de Waymo): un cuadro redondeado en panel alto con un mini anillo de cinco cuñas en acento (la idea del anillo del Resumen)
# alrededor de la silueta de un auto visto desde arriba. La geometría vive aquí y la usan el SVG de la barra lateral y el PNG del favicon (scripts/ep3/generar_icono.py).
SIMBOLO_LADO = 28.0
SIMBOLO_AUTO = (11.0, 8.4, 6.0, 11.2, 2.3)      # x, y, ancho, alto, radio de la silueta del auto (celda de 28 x 28)


def cunas_simbolo(centro: float = SIMBOLO_LADO / 2, r0: float = 6.4, r1: float = 10.7, hueco_grados: float = 3.2, paso: float = 5.0) -> list[list[tuple[float, float]]]:
    """Cinco polígonos (uno por cámara, con los ángulos de ``ANGULOS_CAMARA``) del mini anillo del símbolo, en coordenadas de la celda de 28 x 28."""
    cunas = []
    for a0, a1 in ANGULOS_CAMARA.values():
        a0, a1 = a0 + hueco_grados / 2, a1 - hueco_grados / 2
        n = max(2, int((a1 - a0) / paso) + 1)
        grados = [a0 + (a1 - a0) * k / (n - 1) for k in range(n)]
        cunas.append([_punto(r1, g, centro) for g in grados] + [_punto(r0, g, centro) for g in reversed(grados)])
    return cunas


def simbolo_interior() -> str:
    """Elementos SVG del símbolo en una celda de 28 x 28 (sin la etiqueta ``svg``)."""
    t = TOKENS
    cunas = "".join(f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in c)}" fill="{t["acento"]}"/>' for c in cunas_simbolo())
    x, y, w, h, rx = SIMBOLO_AUTO
    return (f'<rect x=".5" y=".5" width="27" height="27" rx="7" fill="{t["panel_alto"]}" stroke="{t["panel_alto_borde"]}"/>{cunas}'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{t["texto"]}"/>'
            f'<path d="M{x + 1.1} {y + 3.2} H{x + w - 1.1}" stroke="{t["panel_alto"]}" stroke-width="1" stroke-linecap="round"/>')


def simbolo_svg(lado: int = 28) -> str:
    """El símbolo solo, como SVG autónomo de ``lado`` px (se lee a 28 y a 16 px)."""
    return f'<svg xmlns="{SVG_NS}" width="{lado}" height="{lado}" viewBox="0 0 28 28" role="img" aria-label="Símbolo de la página">{simbolo_interior()}</svg>'


def wordmark(nombre: str, sublinea: str = "") -> str:
    """Marca de la barra lateral (``st.logo``): símbolo de 28 px, el nombre (14 px, 600) y debajo la sublínea (11 px, Texto 2). SVG propio, sin URL ni fuentes externas."""
    t = TOKENS
    sub = f'<text x="38" y="29" font-family="{PILA_SVG}" font-size="11" fill="{t["texto_2"]}">{html.escape(sublinea)}</text>' if sublinea else ""
    return (f'<svg xmlns="{SVG_NS}" width="196" height="34" viewBox="0 0 196 34"><g transform="translate(0 3)">{simbolo_interior()}</g>'
            f'<text x="38" y="15" font-family="{PILA_SVG}" font-size="14" font-weight="600" fill="{t["texto"]}">{html.escape(nombre)}</text>{sub}</svg>')


_CSS_BASE = """
<style>
:root { --escala: @ESCALA@; --acento: @acento@; --acento-fondo: @acento_fondo@; --acento-activo: @acento_activo@; --acento-hover: @acento_hover@; --texto: @texto@; --texto-2: @texto_2@; --texto-3: @texto_3@; --fondo: @fondo@; --barra: @barra@; --barra-borde: @barra_borde@;
        --panel: @panel@; --panel-borde: @panel_borde@; --panel-alto: @panel_alto@; --panel-alto-borde: @panel_alto_borde@; --sano: @sano@; --sano-relleno: @sano_relleno@;
        --sin-datos: @sin_datos@; --sin-datos-borde: @sin_datos_borde@; --aviso-texto: @aviso_texto@; --hueco: @hueco@; --hueco-fondo: @hueco_fondo@;
        --radio-panel: @RADIO_PANEL@; --radio-ctl: @RADIO_CONTROL@; --radio-tabla: @RADIO_TABLA@; --sombra-panel: @SOMBRA_PANEL@; --fuente: @FUENTE@; --t: 150ms cubic-bezier(.2, .7, .3, 1); }
html, body, [data-testid="stAppViewContainer"] { font-size: calc(15px * var(--escala)); }
html, body, .stApp, .stApp :is(p, label, li, a, button, input, textarea, th, td, h1, h2, h3, h4, h5, h6, summary, div) { font-family: var(--fuente) !important; font-variant-numeric: tabular-nums; }
[data-testid="stMainBlockContainer"], .block-container { padding: 1.5rem 2rem 2.2rem 2rem; max-width: 1480px; }
[data-testid="stHeader"] { background: transparent; height: 2.4rem; }
h1, h2, h3, h4 { color: var(--texto); }
[data-testid="stMainBlockContainer"] h1 { font-size: @TITULO@; font-weight: 600; line-height: 1.15; letter-spacing: -.01em; padding: 0; margin: 0; }
[data-testid="stMainBlockContainer"] h2, [data-testid="stMainBlockContainer"] h3 { font-size: 1.08rem; font-weight: 600; padding: .2rem 0 .1rem 0; }
[data-testid="stMainBlockContainer"] h4 { font-size: 1.1rem; font-weight: 600; line-height: 1.25; padding: .8rem 0 .1rem 0; margin-top: .5rem; border-top: 1px solid var(--panel-borde); }
b, strong { font-weight: 600; }
/* notas: Texto 3 como mínimo y sin opacidad (Streamlit pinta los captions con opacidad: se anula) */
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * , .stCaption { color: var(--texto-3) !important; opacity: 1 !important; }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { font-size: .8rem; color: var(--texto-2); font-weight: 600; }
hr { margin: .8rem 0; border-color: var(--panel-borde); }

/* barra lateral: un tono sobre el lienzo, con una linea derecha */
[data-testid="stSidebar"] { background: var(--barra); border-right: 1px solid var(--barra-borde); width: 236px !important; min-width: 236px !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { overflow-x: hidden; }
[data-testid="stSidebarContent"] { display: flex; flex-direction: column; min-height: 100%; }
[data-testid="stSidebarUserContent"] { margin-top: auto; padding-top: 1rem; padding-bottom: 1rem; border-top: 1px solid var(--barra-borde); }      /* F25: Streamlit deja 6 rem vacíos debajo del interruptor; con ellos la barra se desplazaba sola */
[data-testid="stSidebarHeader"] { padding: 1.1rem 1rem .6rem 1rem; }
[data-testid="stSidebarHeader"] img { width: 196px !important; max-width: none !important; height: 34px !important; }
[data-testid="stSidebarNavLink"] { border-radius: var(--radio-ctl); padding: .38rem .65rem; font-size: .92rem; color: var(--texto-2); transition: background var(--t), color var(--t); }
[data-testid="stSidebarNavLink"] :is(span, p) { color: inherit; }
[data-testid="stSidebarNavLink"]:hover { background: var(--panel-alto); color: var(--texto); }
[data-testid="stSidebarNavLink"][aria-current="page"] { background: var(--acento-fondo); font-weight: 600; color: var(--acento); }
[data-testid="stSidebarNavSeparator"], [data-testid="stNavSectionHeader"], [data-testid="stSidebarNav"] header { font-size: .78rem; font-weight: 600; color: var(--texto-3); }
[data-baseweb="select"] > div, [data-baseweb="select"] input { font-size: .88rem; }

/* controles activos: fondo panel alto, texto en Texto (nada que parezca deshabilitado) */
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"] { background: var(--panel-alto); border-color: var(--panel-alto-borde); color: var(--texto); }
[data-baseweb="select"] input::placeholder, [data-baseweb="select"] [data-baseweb="base-input"] input::placeholder, input::placeholder { color: var(--texto) !important; opacity: 1 !important; -webkit-text-fill-color: var(--texto); }
[data-baseweb="select"] svg { fill: var(--texto-2); }
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul { background: var(--panel-alto); }
[data-baseweb="popover"] li { color: var(--texto); }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] { background: var(--acento-fondo); }
[data-baseweb="tag"] { background: var(--acento-fondo); border: 1px solid var(--acento); color: var(--texto); }
[data-baseweb="tag"] span { color: var(--texto); }
[data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child { background: var(--panel-borde); }
[data-testid="stSliderThumbValue"], [data-testid="stSlider"] [data-testid="stTickBarMin"], [data-testid="stSlider"] [data-testid="stTickBarMax"] { color: var(--texto-2); }

/* F26-B2: sin lineas huerfanas: titulos, subtitulos y frases de resumen se equilibran; parrafos y notas evitan la palabra suelta al final */
[data-testid="stMainBlockContainer"] :is(h1, h2, h3, h4) , .aud-descripcion, .aud-resultado, .aud-vacio h4 { text-wrap: balance; }
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] :is(p, li), [data-testid="stMainBlockContainer"] td, .aud-nota, .aud-esfuerzo, .aud-ficha p, .aud-pie p, [data-testid="stCaptionContainer"] { text-wrap: pretty; }
[data-testid="stSliderThumbValue"], [data-testid="stSliderThumbValue"] * { white-space: nowrap !important; text-wrap: nowrap; }                 /* el valor del control deslizante («20») no se parte en dos líneas */
/* encabezado de pagina: titulo y una linea (F26: sin chip de estado; la divulgacion de rigor esta en las oraciones, en la alerta del Resumen y en el pie) */
[data-testid="stMarkdownContainer"] .aud-descripcion { color: var(--texto-2); font-size: .94rem; margin: .2rem 0 .8rem 0; }
/* «en muestra» suelto (solo donde ninguna oración vecina lo dice): texto simple en Texto 3, 12 px, sin caja, sin borde y sin color de aviso */
.aud-muestra { margin-left: .4rem; color: var(--texto-3); font-size: .8rem; font-weight: 400; white-space: nowrap; font-variant-numeric: normal; }

/* F25: la barra de herramientas de Streamlit (tabla, descarga, copiar, pantalla completa) aparece al pasar el cursor y tapaba el final de la oración de referencia de las curvas.
   Se oculta SOLO en los gráficos (el contenedor que tiene un stVegaLiteChart); la de las tablas (st.dataframe) no cambia. Selector por data-testid, no por clases generadas. */
div:has(> [data-testid="stVegaLiteChart"]) > [data-testid="stElementToolbar"] { display: none !important; }

/* superficies: panel (principal y detalle de la cola, con la unica sombra) y panel alto; el resto es plano, con lineas finas */
.st-key-panel_principal, .st-key-panel_detalle, .st-key-panel_vacio, .st-key-panel_segmentos { background: var(--panel); border: 1px solid var(--panel-borde); border-radius: var(--radio-panel); box-shadow: var(--sombra-panel); padding: 1rem 1.4rem 1rem 1.4rem; }
.st-key-panel_detalle, .st-key-panel_vacio, .st-key-panel_segmentos { padding: 20px 20px 24px 20px; }
.st-key-panel_detalle { position: sticky; top: 3.4rem; animation: aud-entra 240ms cubic-bezier(.2, .7, .3, 1) both; }
@keyframes aud-entra { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
[data-testid="stVerticalBlockBorderWrapper"] { background: transparent; border-radius: var(--radio-tabla); }
.st-key-filtros_cola { border-bottom: 1px solid var(--panel-borde); padding-bottom: .5rem; margin-bottom: .5rem; }
.st-key-mapa_calor { border: 1px solid var(--panel-borde); border-radius: var(--radio-tabla); background: var(--panel); padding: .4rem .6rem; }
.st-key-como_se_calcula { border-top: 1px solid var(--panel-borde); padding-top: .4rem; }
.st-key-alertas { border-bottom: 1px solid var(--panel-borde); }
[class*="st-key-alerta_"] { border-top: 1px solid var(--panel-borde); padding: .7rem 0 .75rem 0; }


/* tira de cifras (Auditoria y Puntuar): una fila con lineas finas, sin fichas */
.aud-metricas { display: flex; border-top: 1px solid var(--panel-borde); border-bottom: 1px solid var(--panel-borde); margin: .5rem 0 1rem 0; }
@media (max-width: 900px) { .aud-metricas { display: grid; grid-template-columns: repeat(2, 1fr); } }
.aud-metrica { flex: 1 1 0; padding: .65rem .9rem .6rem .9rem; border-left: 1px solid var(--panel-borde); display: flex; flex-direction: column; justify-content: space-between; min-height: 4.6rem; }
.aud-metrica:first-child { border-left: 0; padding-left: 0; }
.aud-metrica .et { color: var(--texto-2); font-size: .8rem; font-weight: 600; margin: 0; }
.aud-metrica .va { color: var(--texto); font-size: @CIFRA@; font-weight: 600; line-height: 1.15; letter-spacing: -.01em; white-space: nowrap; margin: .3rem 0 0 0; }
.aud-metrica .no { color: var(--texto-3); font-size: .78rem; margin: .1rem 0 0 0; }
.aud-metrica.hueco .va { color: var(--hueco); }

/* cifras de apoyo del Resumen: tabla pequena con una barra de 10 px por fila */
[data-testid="stMarkdownContainer"] .aud-cifras { width: 100%; border-collapse: collapse; font-size: .92rem; margin: .2rem 0 .3rem 0; }
[data-testid="stMarkdownContainer"] .aud-cifras td { padding: .42rem 0; border: 0; border-bottom: 1px solid var(--panel-borde); vertical-align: middle; background: transparent; }
[data-testid="stMarkdownContainer"] .aud-cifras td.k { color: var(--texto); padding-right: 1rem; }
[data-testid="stMarkdownContainer"] .aud-cifras td.k small { display: block; color: var(--texto-3); font-size: .78rem; }
[data-testid="stMarkdownContainer"] .aud-cifras td.v { text-align: right; font-weight: 600; white-space: nowrap; padding-left: .6rem; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-cifras td.b { width: 34%; padding-left: 1rem; }
[data-testid="stMarkdownContainer"] .aud-barra { display: block; height: 10px; border-radius: 5px; background: var(--panel-alto); overflow: hidden; }
[data-testid="stMarkdownContainer"] .aud-barra > i { display: block; height: 100%; border-radius: 5px; }

/* alertas: titulo, texto y debajo un enlace visible en acento y con linea inferior */
.aud-fila { display: flex; gap: .6rem; align-items: baseline; padding: .15rem 0; }
.aud-punto { flex: 0 0 .6rem; width: .6rem; height: .6rem; border-radius: 50%; background: var(--acento); display: inline-block; }
.aud-punto.hueco { background: var(--hueco); }
.aud-punto.aviso { background: var(--aviso-texto); }

/* F29: Resumen para uso diario: indicadores, alertas de cámara, cola y segmentos prioritarios */
.aud-kpis { display: grid; grid-template-columns: repeat(var(--n, 4), minmax(0, 1fr)); gap: 1rem; margin: 0 0 1.1rem 0; }
.aud-kpi { background: var(--panel); border: 1px solid var(--panel-borde); border-radius: var(--radio-panel); padding: .8rem 1.1rem .85rem 1.1rem; min-width: 0; }
[data-testid="stMarkdownContainer"] .aud-kpi p { margin: 0; }
.aud-kpi .et { font-size: .87rem; color: var(--texto-2); }
.aud-kpi .va { font-size: 2.1rem; font-weight: 600; line-height: 1.15; letter-spacing: -.02em; color: var(--texto); font-variant-numeric: tabular-nums; margin: .1rem 0 .05rem 0; }
.aud-kpi .no { font-size: .87rem; color: var(--texto-2); }
.aud-kpi .va small { font-size: .9rem; font-weight: 400; color: var(--texto-2); letter-spacing: 0; }
.aud-kpi.hueco { background: var(--hueco-fondo); border-color: var(--hueco); }
.aud-kpi.hueco .va { color: var(--hueco); }
[data-testid="stMarkdownContainer"] .aud-kicker { margin: 0; font-size: .8rem; letter-spacing: .05em; text-transform: uppercase; color: var(--texto-2); }
[data-testid="stMarkdownContainer"] .aud-titular { margin: .2rem 0 .2rem 0; font-size: @TITULAR@; font-weight: 600; line-height: 1.22; letter-spacing: -.01em; color: var(--texto); text-wrap: balance; }
[data-testid="stMarkdownContainer"] .aud-titular .alerta { color: var(--hueco); }
[class*="st-key-enlace_"] [data-testid="stElementContainer"] { width: 100% !important; }
[class*="st-key-enlace_"] [data-testid="stPageLink"] { display: flex !important; justify-content: flex-end !important; }
[class*="st-key-enlace_"] a { color: var(--acento) !important; text-decoration: underline; text-underline-offset: 3px; background: transparent !important; font-size: .9rem; font-weight: 600; white-space: nowrap; width: auto !important; justify-content: flex-end !important; margin-left: auto; }
[class*="st-key-enlace_"] a:hover { color: var(--texto) !important; }
[class*="st-key-enlace_"] a p, [class*="st-key-enlace_"] a span { color: inherit !important; font-weight: 600; }
.st-key-aud_celdas, .st-key-aud_anillo, .st-key-aud_mapa, .st-key-plan_revision, .st-key-ex_datos, .st-key-ex_resultado, .st-key-ex_pasos, .st-key-ex_curva, .st-key-ex_tipo { background: var(--panel); border: 1px solid var(--panel-borde); border-radius: var(--radio-panel); padding: 1rem 1.2rem; }
[data-testid="stMarkdownContainer"] .aud-card-t { margin: 0; font-size: 1.07rem; font-weight: 600; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-card-a { margin: .1rem 0 .6rem 0; font-size: .87rem; color: var(--texto-2); }
[data-testid="stMarkdownContainer"] .aud-banner { margin: 0 0 .6rem 0; padding: .5rem .8rem; font-size: .87rem; color: var(--texto); background: var(--acento-fondo); border: 1px solid var(--acento-activo); border-radius: var(--radio-ctl); }
.aud-anillo-vertical { display: flex; flex-direction: column; align-items: center; gap: .4rem; }
[data-testid="stMarkdownContainer"] .aud-anillo-vertical p { margin: 0; text-align: center; }
[data-testid="stMarkdownContainer"] .aud-anillo-vertical .tt { font-size: 1.02rem; font-weight: 600; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-anillo-vertical .tx { font-size: .87rem; color: var(--texto-2); }
/* F33: Explica una caja */
[data-testid="stMarkdownContainer"] .aud-rotulo { margin: .2rem 0 .1rem 0; font-size: .92rem; font-weight: 600; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-rotulo .tag { margin-left: .6rem; font-size: .75rem; font-weight: 400; color: var(--acento); }
[data-testid="stMarkdownContainer"] .aud-rotulo .tag.m { color: var(--texto-3); }
[data-testid="stMarkdownContainer"] .aud-prob-grande { margin: 0; font-size: 2.9rem; font-weight: 600; color: var(--acento); line-height: 1.05; letter-spacing: -.02em; white-space: nowrap; }
[data-testid="stMarkdownContainer"] .aud-veredicto { display: inline-block; margin: 0; padding: .4rem .9rem; font-size: .92rem; font-weight: 600; border-radius: var(--radio-ctl); }
[data-testid="stMarkdownContainer"] .aud-veredicto.no { color: var(--hueco); background: var(--hueco-fondo); border: 1px solid var(--hueco); }
[data-testid="stMarkdownContainer"] .aud-veredicto.si { color: var(--sano); background: var(--sano-relleno); border: 1px solid var(--sano); }
[data-testid="stMarkdownContainer"] .aud-lugar-t { display: flex; justify-content: space-between; margin: 0; font-size: .92rem; font-weight: 600; color: var(--texto); }
.aud-lugar { position: relative; height: 16px; margin: .7rem 0 .4rem 0; background: var(--panel-alto); border-radius: 8px; }
.aud-lugar .zona { position: absolute; left: 0; top: 0; height: 16px; background: var(--sano-relleno); border-right: 2px solid var(--sano); border-radius: 8px 0 0 8px; }
.aud-lugar .marca { position: absolute; top: -6px; width: 4px; height: 28px; background: var(--texto); border-radius: 2px; transform: translateX(-2px); }
.aud-lugar-leyenda { display: flex; justify-content: space-between; gap: .6rem; font-size: .8rem; color: var(--texto-2); }
.aud-calculo { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .7rem; margin-top: .5rem; }
.aud-calculo > div { background: var(--panel-alto); border: 1px solid var(--panel-borde); border-radius: var(--radio-ctl); padding: .6rem .8rem; min-width: 0; }
[data-testid="stMarkdownContainer"] .aud-calculo p { margin: 0; }
[data-testid="stMarkdownContainer"] .aud-calculo .n { font-size: .78rem; color: var(--texto-2); }
[data-testid="stMarkdownContainer"] .aud-calculo .v { font-size: 1.35rem; font-weight: 600; color: var(--texto); line-height: 1.25; }
[data-testid="stMarkdownContainer"] .aud-calculo .c { font-size: .8rem; color: var(--texto-2); }
@media (max-width: 900px) { .aud-calculo { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.st-key-ex_datos .stButton > button { min-height: 2.4rem; }
/* F33: un botón deshabilitado (p. ej. «Anterior» en la primera página) se distingue por el borde punteado y el cursor, no por un texto apagado: el texto sigue a 4,5:1 */
.st-key-pag_anterior button:disabled, .st-key-pag_siguiente button:disabled { opacity: 1; color: var(--texto-3); border-style: dashed; cursor: not-allowed; }
/* F36: Ética y límites, Ayuda y glosario */
.aud-hero { display: flex; flex-wrap: wrap; gap: 1.2rem; align-items: center; background: var(--sano-relleno); border: 1px solid var(--sano); border-radius: var(--radio-panel); padding: 1.3rem 1.5rem; }
.aud-hero > div { min-width: 0; }
.aud-hero .izq { flex: 1 1 320px; }
.aud-hero .avisos { flex: 1 1 280px; display: flex; flex-direction: column; gap: .5rem; }
[data-testid="stMarkdownContainer"] .aud-hero p { margin: 0; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-hero .grande { margin: .5rem 0 .3rem 0; font-size: 1.7rem; font-weight: 600; line-height: 1.2; text-wrap: balance; }
.aud-hero .aviso { display: flex; gap: .6rem; align-items: flex-start; background: var(--fondo); border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); padding: .55rem .8rem; font-size: .9rem; color: var(--texto); }
.aud-hero .aviso .x { flex: none; width: 1.3rem; height: 1.3rem; margin-top: .1rem; border-radius: 50%; border: 1px solid var(--hueco); background: var(--hueco-fondo); display: inline-flex; align-items: center; justify-content: center; }
.aud-hero .aviso .x svg { width: .7rem; height: .7rem; stroke: var(--hueco); fill: none; stroke-width: 2.4; stroke-linecap: round; }
.aud-ic { flex: none; display: inline-flex; align-items: center; justify-content: center; width: 2.1rem; height: 2.1rem; border-radius: var(--radio-ctl); background: var(--acento-fondo); border: 1px solid var(--acento-activo); }
.aud-ic svg { width: 1.1rem; height: 1.1rem; stroke: var(--acento); fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.aud-ic.t { background: var(--sano-relleno); border-color: var(--sano); }
.aud-ic.t svg { stroke: var(--sano); }
.aud-ic.g { width: 2.6rem; height: 2.6rem; }
.aud-tf { background: var(--panel); border: 1px solid var(--panel-borde); border-radius: var(--radio-panel); padding: 1.1rem 1.3rem; height: 100%; }
.aud-tf h4, [data-testid="stMarkdownContainer"] .aud-tf h4 { display: flex; align-items: center; gap: .6rem; margin: 0 0 .5rem 0; padding: 0; border: 0; font-size: 1.07rem; font-weight: 600; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-tf p { margin: 0; font-size: .92rem; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-tf ul { margin: .3rem 0 0 0; padding-left: 1.2rem; font-size: .92rem; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-tf li { margin: .25rem 0; }
.aud-etq { margin-left: .4rem; padding: .05rem .6rem; font-size: .78rem; font-weight: 400; color: var(--texto-2); border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); }
.aud-etq.bor { color: var(--texto); border-style: dashed; }
.st-key-et_desempeno, .st-key-et_limites, .st-key-ay_paso_1, .st-key-ay_paso_2, .st-key-ay_paso_3 { background: var(--panel); border: 1px solid var(--panel-borde); border-radius: var(--radio-panel); padding: 1.1rem 1.3rem; }
.aud-stats { display: flex; flex-wrap: wrap; gap: .7rem; margin: .6rem 0; }
.aud-stats > div { flex: 1 1 140px; background: var(--panel-alto); border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); padding: .6rem .8rem; min-width: 0; }
[data-testid="stMarkdownContainer"] .aud-stats p { margin: 0; }
[data-testid="stMarkdownContainer"] .aud-stats .k { font-size: .78rem; color: var(--texto-2); }
[data-testid="stMarkdownContainer"] .aud-stats .v { font-size: 1.7rem; font-weight: 600; line-height: 1.2; color: var(--texto); }
.aud-cmp { margin: .6rem 0 .4rem 0; }
.aud-cmp .f { display: flex; align-items: center; gap: .8rem; padding: .25rem 0; font-size: .9rem; color: var(--texto); }
.aud-cmp .l { flex: 0 0 6rem; display: inline-flex; align-items: center; gap: .45rem; }
.aud-cmp .barra { flex: 1; height: .9rem; background: var(--panel-alto); border-radius: var(--radio-ctl); overflow: hidden; }
.aud-cmp .barra i { display: block; height: .9rem; border-radius: var(--radio-ctl); }
.aud-cmp .v { flex: 0 0 4.5rem; text-align: right; font-weight: 600; }
.aud-flecha { position: relative; }
.st-key-ay_paso_1::after, .st-key-ay_paso_2::after { content: ""; position: absolute; right: -1.15rem; top: 50%; width: 0; height: 0; margin-top: -.45rem; border-top: .45rem solid transparent; border-bottom: .45rem solid transparent; border-left: .6rem solid var(--acento-activo); }
.st-key-ay_paso_1, .st-key-ay_paso_2, .st-key-ay_paso_3 { position: relative; }
[data-testid="stMarkdownContainer"] .aud-guia3 .n { display: inline-flex; align-items: center; justify-content: center; width: 1.9rem; height: 1.9rem; border-radius: 50%; background: var(--acento); color: var(--fondo); font-weight: 600; margin-bottom: .5rem; }
[data-testid="stMarkdownContainer"] .aud-guia3 h4 { margin: 0 0 .3rem 0; padding: 0; border: 0; font-size: 1.07rem; font-weight: 600; }
[data-testid="stMarkdownContainer"] .aud-guia3 p { margin: 0; font-size: .92rem; color: var(--texto); }
.aud-pgs { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: .8rem; }
.aud-pgs > div { background: var(--panel); border: 1px solid var(--panel-borde); border-radius: var(--radio-ctl); padding: .75rem 1rem; }
.aud-pgs > div.nueva { border-style: dashed; }
[data-testid="stMarkdownContainer"] .aud-pgs p { margin: 0; font-size: .88rem; color: var(--texto-2); }
[data-testid="stMarkdownContainer"] .aud-pgs b { display: block; margin-bottom: .15rem; font-size: .92rem; color: var(--texto); }
.aud-gl { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: .7rem; margin-top: .6rem; }
.aud-gl > div { background: var(--panel); border: 1px solid var(--panel-borde); border-radius: var(--radio-ctl); padding: .75rem 1rem; }
.aud-gl .h { display: flex; justify-content: space-between; gap: .6rem; align-items: baseline; }
[data-testid="stMarkdownContainer"] .aud-gl p { margin: 0; }
[data-testid="stMarkdownContainer"] .aud-gl b { font-size: .95rem; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-gl .c { font-size: .78rem; color: var(--texto-2); letter-spacing: .04em; }
[data-testid="stMarkdownContainer"] .aud-gl .d { margin-top: .3rem; font-size: .9rem; color: var(--texto); }
.aud-hero { margin-bottom: .9rem; }
.st-key-et_desempeno h4, .st-key-et_limites h4 { display: flex; align-items: center; gap: .6rem; margin: 0 0 .5rem 0; padding: 0; border: 0; font-size: 1.07rem; font-weight: 600; color: var(--texto); }
[data-testid="stMarkdownContainer"] .st-key-et_desempeno p, [data-testid="stMarkdownContainer"] .st-key-et_limites p { margin: 0 0 .3rem 0; font-size: .92rem; color: var(--texto); }
.st-key-et_desempeno, .st-key-et_limites { margin-bottom: .6rem; }
.st-key-et_desempeno a, .st-key-et_limites a, .st-key-ay_paso_1 a, .st-key-ay_paso_2 a, .st-key-ay_paso_3 a { color: var(--acento); font-weight: 600; text-decoration: underline; text-underline-offset: .2rem; }
.st-key-ay_paso_1, .st-key-ay_paso_2, .st-key-ay_paso_3 { min-height: 11.5rem; }
[data-testid="stHorizontalBlock"]:has(.aud-tf) { align-items: stretch; margin-bottom: .6rem; }
[data-testid="stHorizontalBlock"]:has(.aud-tf) > [data-testid="stColumn"] > div, [data-testid="stHorizontalBlock"]:has(.aud-tf) [data-testid="stMarkdownContainer"] { height: 100%; }
[data-testid="stHorizontalBlock"]:has(.aud-tf) [data-testid="stMarkdown"] { height: 100%; }
[data-testid="stMarkdownContainer"] .aud-gl-vacio { margin: .6rem 0; font-size: .9rem; color: var(--texto-2); }
/* F35: Puntuar datos nuevos (tres pasos, entradas, encabezado del resultado) */
.aud-flujo { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .7rem; margin: .2rem 0 .8rem 0; }
.aud-flujo > div { display: flex; align-items: center; gap: .7rem; background: var(--panel-alto); border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); padding: .6rem .85rem; color: var(--texto-2); font-size: .85rem; min-width: 0; }
.aud-flujo > div.activo { background: var(--acento-fondo); border-color: var(--acento-activo); }
.aud-flujo .num { flex: none; display: inline-flex; align-items: center; justify-content: center; width: 1.7rem; height: 1.7rem; border-radius: 50%; border: 2px solid var(--acento-activo); color: var(--acento); font-weight: 600; font-size: .85rem; }
.aud-flujo .activo .num { background: var(--acento); color: var(--fondo); border-color: var(--acento); }
.aud-flujo .hecho .num { background: var(--sano-relleno); color: var(--texto); border-color: var(--sano); }
.aud-flujo .omitido .num { background: transparent; color: var(--texto-2); border: 2px dashed var(--panel-alto-borde); }
[data-testid="stMarkdownContainer"] .aud-flujo p { margin: 0; }
[data-testid="stMarkdownContainer"] .aud-flujo .t { display: block; color: var(--texto); font-weight: 600; font-size: .9rem; }
[data-testid="stMarkdownContainer"] .aud-flujo .e { display: block; font-size: .78rem; color: var(--texto-2); }
@media (max-width: 800px) { .aud-flujo { grid-template-columns: 1fr; } }
[data-testid="stMarkdownContainer"] .aud-dz-t { margin: 0; font-size: .95rem; font-weight: 600; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-dz-t .etq { margin-left: .5rem; padding: .05rem .55rem; font-size: .75rem; font-weight: 400; color: var(--texto-2); border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); }
[data-testid="stMarkdownContainer"] .aud-dz-t .etq.obl { color: var(--sano); border-color: var(--sano); }
[data-testid="stMarkdownContainer"] .aud-dz-a { margin: 0 0 .4rem 0; font-size: .82rem; color: var(--texto-2); min-height: 4.2rem; }                  /* los dos cargadores quedan parejos aunque el texto del 2 sea más largo */
[data-testid="stMarkdownContainer"] .aud-ayuda-flujo { margin: .35rem 0 0 0; font-size: .85rem; color: var(--texto-2); }
.st-key-pt_ejemplo { align-items: flex-end; }
.st-key-pt_ejemplo [data-testid="stMarkdownContainer"] p { margin: 0 0 .25rem 0; font-size: .78rem; color: var(--texto-2); text-align: right; }
.st-key-pt_ejemplo button { min-height: 0; padding: .2rem .7rem; font-size: .8rem; }
.st-key-pt_resultado, .st-key-pt_celdas, .st-key-pt_cola { background: var(--panel); border: 1px solid var(--panel-borde); border-radius: var(--radio-panel); padding: 1rem 1.2rem; }
[data-testid="stMarkdownContainer"] .aud-seg-t { margin: 0; font-size: 1.07rem; font-weight: 600; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-seg-t .etq { margin-left: .6rem; padding: .05rem .6rem; font-size: .78rem; font-weight: 400; color: var(--texto-2); border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); }
[data-testid="stMarkdownContainer"] .aud-seg-a { margin: 0; font-size: .82rem; color: var(--texto-2); }
/* F34: Validación (cabecera, criterios, tabla estándar) */
.st-key-val_veredicto, .st-key-val_apoyo_wrap { background: var(--panel); border: 1px solid var(--panel-borde); border-radius: var(--radio-panel); padding: 1rem 1.2rem; }
[data-testid="stMarkdownContainer"] .aud-vt { margin: 0 0 .7rem 0; font-size: 1.2rem; font-weight: 600; line-height: 1.35; color: var(--texto); text-wrap: balance; }
.aud-chips { display: flex; flex-wrap: wrap; gap: .5rem; margin: .9rem 0 1.1rem 0; }
[data-testid="stMarkdownContainer"] .aud-chip { margin: 0; display: inline-flex; align-items: center; gap: .45rem; padding: .2rem .7rem; font-size: .8rem; color: var(--texto-2); border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); }
.aud-crit { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .8rem; margin: .2rem 0 .4rem 0; }
.aud-crit > div { background: var(--panel-alto); border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); padding: .75rem .9rem; min-width: 0; }
[data-testid="stMarkdownContainer"] .aud-crit p { margin: 0; }
[data-testid="stMarkdownContainer"] .aud-crit .c { font-size: .78rem; color: var(--texto-2); }
[data-testid="stMarkdownContainer"] .aud-crit .n { font-size: .95rem; font-weight: 600; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-crit .r { margin: .25rem 0 !important; font-size: 1.25rem; font-weight: 600; }
[data-testid="stMarkdownContainer"] .aud-crit .r.si { color: var(--sano); }
[data-testid="stMarkdownContainer"] .aud-crit .r.no { color: var(--hueco); }
[data-testid="stMarkdownContainer"] .aud-crit .d { font-size: .8rem; color: var(--texto-2); }
@media (max-width: 1000px) { .aud-crit { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
[data-testid="stMarkdownContainer"] .aud-clave { margin: 0 0 .5rem 0; padding: .55rem .85rem; font-size: .9rem; color: var(--texto); background: var(--panel-alto); border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); }
.aud-claves { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: .7rem; margin: .3rem 0 .6rem 0; }
[data-testid="stMarkdownContainer"] .aud-clave b { color: var(--texto); }
.tstd-wrap { margin-bottom: .7rem; overflow-x: auto; border: 1px solid var(--panel-borde); border-radius: var(--radio-tabla); max-width: 100%;
  background: conic-gradient(var(--panel), var(--panel)) 0 0 / 30px 100% no-repeat local, conic-gradient(var(--panel), var(--panel)) 100% 0 / 30px 100% no-repeat local,
              radial-gradient(farthest-side at 0 50%, var(--acento-activo), transparent) 0 0 / 16px 100% no-repeat scroll, radial-gradient(farthest-side at 100% 50%, var(--acento-activo), transparent) 100% 0 / 16px 100% no-repeat scroll; }      /* sombras en los bordes solo si hay más columnas */
.tstd-wrap:focus-visible { outline: 2px solid var(--acento); outline-offset: 2px; }
table.tstd { width: 100%; border-collapse: collapse; font-size: .85rem; font-variant-numeric: tabular-nums; line-height: 1.35; }
table.tstd th { text-align: left; font-weight: 600; font-size: .78rem; color: var(--texto-2); padding: .55rem .7rem; background: var(--panel-alto); border-bottom: 1px solid var(--panel-borde); white-space: nowrap; vertical-align: bottom; }
table.tstd td { padding: .5rem .7rem; border-bottom: 1px solid var(--panel-borde); color: var(--texto); vertical-align: top; }
table.tstd tr:last-child td { border-bottom: 0; }
table.tstd th.r, table.tstd td.r { text-align: right; white-space: nowrap; }
table.tstd td:first-child, table.tstd th:first-child { position: sticky; left: 0; z-index: 1; background: var(--panel); min-width: 9.5rem; }
table.tstd td.si, table.tstd td.no { white-space: nowrap; }
table.tstd th:first-child { background: var(--panel-alto); }
table.tstd td.si { color: var(--sano); font-weight: 600; }
table.tstd td.no { color: var(--hueco); font-weight: 600; }
[data-testid="stMarkdownContainer"] .tstd-resp { margin: 0 0 .5rem 0; font-size: .85rem; color: var(--texto-2); }
[data-testid="stMarkdownContainer"] .tstd-pie { margin: 0; font-size: .8rem; color: var(--texto-2); }
[data-testid="stMarkdownContainer"] .tstd-nota { margin: .4rem 0 0 0; font-size: .8rem; color: var(--texto-2); }
[class*="st-key-pagtab_"] button:disabled { opacity: 1; color: var(--texto-3); border-style: dashed; cursor: not-allowed; }
/* el recuadro de foco de los desplegables aparece solo con el teclado (F34), no en reposo ni al hacer clic */
[data-testid="stExpander"] summary:focus:not(:focus-visible), [data-testid="stExpander"] details:focus:not(:focus-visible) { outline: 0; }
[data-testid="stExpander"] summary:focus-visible { outline: 2px solid var(--acento); outline-offset: 2px; }
.st-key-ir_cola { background: var(--acento-fondo); border: 1px solid var(--acento); border-radius: var(--radio-panel); min-height: 6.4rem; display: flex; align-items: center; justify-content: center; }
.st-key-ir_cola [data-testid="stElementContainer"] { width: 100% !important; margin: 0 !important; }
.st-key-ir_cola [data-testid="stPageLink"] { display: flex !important; justify-content: center !important; }
.st-key-ir_cola a { color: var(--texto) !important; font-weight: 600; font-size: 1rem; text-decoration: none; justify-content: center; text-align: center; white-space: normal; width: 100%; min-height: 6.4rem; }
.st-key-ir_cola a p, .st-key-ir_cola a span { color: inherit !important; font-weight: 600; }
.st-key-ir_cola:hover { background: var(--acento-activo); }
[data-testid="stMarkdownContainer"] .aud-rotulo-anillo { text-align: center; margin: 0 0 .1rem 0; }
[class*="st-key-celda_"], [class*="st-key-celdasel_"] { border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); background: var(--fondo); padding: .4rem .6rem .4rem .3rem; margin-bottom: .5rem; }
[class*="st-key-celdasel_"] { border: 1.5px solid var(--hueco); background: var(--hueco-fondo); }
[class*="st-key-celda_"], [class*="st-key-celdasel_"], [class*="st-key-celda_"] [data-testid="stVerticalBlock"], [class*="st-key-celdasel_"] [data-testid="stVerticalBlock"] { gap: 0; }
[class*="st-key-celda_"] button[kind="tertiary"], [class*="st-key-celdasel_"] button[kind="tertiary"] { justify-content: flex-start; text-align: left; border: 0 !important; background: transparent !important; padding: .1rem .35rem; min-height: 0; color: var(--texto); }
[class*="st-key-celda_"] button[kind="tertiary"] > div, [class*="st-key-celdasel_"] button[kind="tertiary"] > div { justify-content: flex-start !important; width: 100%; }
[class*="st-key-celda_"] button[kind="tertiary"] p, [class*="st-key-celdasel_"] button[kind="tertiary"] p { font-size: 1rem; font-weight: 600; color: var(--texto); text-align: left !important; }
[class*="st-key-celda_"] [data-testid="stIconMaterial"], [class*="st-key-celdasel_"] [data-testid="stIconMaterial"] { color: var(--hueco); }
[class*="st-key-celdasel_"] .stButton > button[kind="primary"] { background: var(--hueco) !important; border-color: var(--hueco) !important; color: var(--fondo) !important; }
[class*="st-key-celdasel_"] .stButton > button[kind="primary"] p { color: var(--fondo) !important; }
[class*="st-key-celdasel_"] .stButton > button[kind="primary"]:hover { border-color: var(--texto) !important; }
[data-testid="stMarkdownContainer"] .aud-celda-estado { margin: 0 0 0 2.05rem; font-size: .87rem; color: var(--texto-2); }
.st-key-cola_resumen { border: 1px solid var(--panel-borde); border-radius: var(--radio-tabla); background: var(--panel); overflow: visible; padding-bottom: .15rem; }
.st-key-cola_resumen, .st-key-cola_resumen [data-testid="stVerticalBlock"] { gap: 0; }
.st-key-cola_resumen [data-testid="stMarkdownContainer"], [class*="st-key-celda_"] [data-testid="stMarkdownContainer"], [class*="st-key-celdasel_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
.st-key-cola_resumen [data-testid="stElementContainer"] { margin: 0 !important; }
.st-key-cola_cabecera { background: var(--panel-alto); padding: .15rem .9rem; }
[class*="st-key-filacola_"] { border-top: 1px solid var(--panel-borde); padding: .1rem .9rem; }
[class*="st-key-filacola_"] button { background: transparent !important; border: 0 !important; color: var(--acento) !important; text-decoration: underline; text-underline-offset: 3px; min-height: 0; padding: .2rem .3rem; }
[class*="st-key-filacola_"] button p { color: inherit !important; font-weight: 600; }
.aud-cola-fila { display: grid; grid-template-columns: .9fr 1fr .95fr 1.4fr 1.6fr 1.25fr; gap: .6rem; align-items: center; min-height: 2.75rem; font-size: .92rem; color: var(--texto); font-variant-numeric: tabular-nums; }
.aud-cola-fila.cab { min-height: 2rem; white-space: nowrap; font-size: .72rem; letter-spacing: .04em; text-transform: uppercase; font-weight: 500; color: var(--texto-2); }
.aud-cola-fila.cab.accion { display: block; }
.st-key-aud_celda_elegida { border: 1px solid var(--panel-alto-borde); border-radius: var(--radio-ctl); background: var(--panel-alto); padding: .55rem .85rem .35rem .85rem; margin-bottom: .6rem; }
.aud-cola-fila .etq { display: inline-flex; align-items: center; gap: .35rem; margin-left: .45rem; color: var(--texto-2); font-size: .8rem; white-space: nowrap; }
.aud-segs { display: flex; flex-direction: column; gap: .7rem; margin-top: .6rem; }
.aud-segs .t { display: flex; justify-content: space-between; font-size: .92rem; margin-bottom: .25rem; font-variant-numeric: tabular-nums; }
.aud-segs .t b { font-weight: 600; }
.aud-fila .tt { font-weight: 600; color: var(--texto); }
.aud-fila .tx { color: var(--texto-2); }
[class*="st-key-alerta_"] [data-testid="stMarkdown"], [class*="st-key-alerta_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
[class*="st-key-alerta_"] [data-testid="stElementContainer"] { margin-bottom: 0 !important; }
[class*="st-key-alerta_"] a { color: var(--acento) !important; text-decoration: underline; text-underline-offset: 3px; padding: 0 0 0 1.2rem; background: transparent !important; font-size: .9rem; font-weight: 600; }
[class*="st-key-alerta_"] a:hover { color: var(--texto) !important; }
[class*="st-key-alerta_"] a p, [class*="st-key-alerta_"] a span { color: inherit !important; font-weight: 600; }

[data-testid="stSidebarNavItems"] > div + div { margin-top: .7rem !important; }                      /* F27: seis grupos en el menú; se reduce su separación para que el interruptor siga a la vista a 1366 x 768 */
[data-testid="stMarkdownContainer"] .aud-ficha { border-top: 1px solid var(--panel-borde); padding: .7rem 0 .4rem 0; margin: 0 0 .3rem 0; }
[data-testid="stMarkdownContainer"] .aud-ficha h4 { margin: 0 0 .25rem 0; padding: 0; border-top: 0; font-size: 1.05rem; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-ficha p { margin: 0; color: var(--texto-2); }
.aud-resultado { font-size: 1.12rem; line-height: 1.45; color: var(--texto); padding: .15rem 0 .1rem 0; margin: .3rem 0 .2rem 0; max-width: 60em; }
[data-testid="stMarkdownContainer"] .aud-esfuerzo { color: var(--texto-2); font-size: .9rem; margin: 0 0 .6rem 0; }
.aud-aviso { position: relative; background: var(--panel-alto); color: var(--texto); border: 1px solid var(--sin-datos-borde); border-radius: var(--radio-ctl); padding: .5rem .85rem .5rem 1.9rem; margin: .5rem 0; font-size: .9rem; }
.aud-aviso::before { content: ""; position: absolute; left: .85rem; top: .85rem; width: .6rem; height: .6rem; border-radius: 50%; background: var(--aviso-texto); }      /* el único ámbar de la página: advertencia de fiabilidad de los ciclistas */
[data-testid="stMarkdownContainer"] .aud-probabilidad { font-size: 2.1rem; font-weight: 600; color: var(--acento); line-height: 1.1; letter-spacing: -.02em; margin: 0; white-space: nowrap; }
/* nota del empate: importante, en Texto 2 con un filete neutro a la izquierda (F25: ya no ámbar) */
[data-testid="stMarkdownContainer"] .aud-nota { font-size: .86rem; color: var(--texto-2); border-left: 2px solid var(--sin-datos-borde); padding: .15rem 0 .15rem .75rem; margin: .1rem 0 .7rem 0; }
.st-key-panel_detalle, .st-key-panel_vacio { margin-top: 0; }
.st-key-panel_principal [data-testid="stVerticalBlock"] { gap: .6rem; }
.st-key-panel_principal [data-testid="stMarkdown"], .st-key-panel_principal [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }       /* sin el margen negativo de Streamlit: el relleno inferior del panel es el real */
[data-testid="stMarkdownContainer"] .aud-datos { display: grid; grid-template-columns: minmax(0, 44%) minmax(0, 1fr); gap: .2rem .8rem; margin: 0; font-size: .88rem; }
[data-testid="stMarkdownContainer"] .aud-datos dt { color: var(--texto-3); }
[data-testid="stMarkdownContainer"] .aud-datos dd { margin: 0; font-weight: 600; overflow-wrap: anywhere; color: var(--texto); }
[data-testid="stMarkdownContainer"] .aud-detalle-cabeza { display: flex; flex-direction: column; align-items: flex-start; gap: .55rem; margin-bottom: .2rem; }
[data-testid="stMarkdownContainer"] .aud-detalle-datos { border-top: 1px solid var(--panel-borde); padding-top: .7rem; margin-top: .8rem; }
.aud-pie { margin-top: 1.8rem; padding-top: .7rem; border-top: 1px solid var(--panel-borde); color: var(--texto-3); font-size: .8rem; }
.aud-pie p { margin: 0 0 .2rem 0; color: var(--texto-3); font-size: .8rem; line-height: 1.45; }

/* anillo de camaras: tres estados (sana, hueco, sin datos) mas activa y apagada; trazos de ancho fijo en pixeles */
.aud-anillo { display: block; max-width: 100%; }
.aud-anillo .cu { stroke-width: 1.5px; vector-effect: non-scaling-stroke; transition: fill var(--t), stroke var(--t); }
.aud-anillo .cu.sana { fill: var(--sano-relleno); stroke: var(--sano); }
.aud-anillo .cu.hueco { fill: var(--hueco-fondo); stroke: var(--hueco); stroke-width: 3px; }
.aud-anillo .cu.sin_datos { fill: var(--sin-datos); stroke: var(--sin-datos-borde); }
.aud-anillo .cu.sel { stroke: var(--texto); stroke-width: 3.2; }
.aud-anillo .cu.activa { fill: var(--acento); stroke: var(--texto); }
.aud-anillo .cu.apagada { fill: none; stroke: var(--sin-datos-borde); stroke-dasharray: 3 3; }
.aud-anillo .nu { font-size: var(--nu, 12.5px); font-weight: 600; fill: var(--texto-2); text-anchor: middle; dominant-baseline: central; }
.aud-anillo .nu.hueco { fill: var(--hueco); }
.aud-anillo .nu.activa { fill: var(--acento); }
.aud-anillo .xx { stroke: var(--hueco); stroke-width: 3px; stroke-linecap: round; vector-effect: non-scaling-stroke; }
.aud-anillo .auto { fill: var(--panel-alto); stroke: var(--sin-datos-borde); stroke-width: 1.5px; vector-effect: non-scaling-stroke; }
.aud-anillo .parabrisas { stroke: var(--sin-datos-borde); stroke-width: 1.5px; stroke-linecap: round; vector-effect: non-scaling-stroke; }
.aud-anillo-bloque { display: flex; flex-direction: column; align-items: center; gap: .6rem; }
.aud-tarjeta-anillo { display: flex; flex-wrap: wrap; gap: .6rem 1rem; align-items: center; border-top: 1px solid var(--panel-borde); padding: .7rem 0 .2rem 0; margin: .3rem 0 .4rem 0; }
.aud-tarjeta-anillo > div { flex: 1 1 10rem; }
.aud-tarjeta-anillo svg { flex: 0 0 auto; }
.aud-tarjeta-anillo .tt { margin: 0 0 .25rem 0; font-weight: 600; color: var(--texto); }
.aud-tarjeta-anillo .tx { margin: 0; color: var(--texto-2); font-size: .88rem; }
.aud-vacio { display: flex; gap: 1rem; align-items: center; padding: .4rem .2rem; }
.aud-vacio.columna { flex-direction: column; text-align: center; padding: 1rem .2rem; }
.aud-vacio .tt { margin: 0 0 .2rem 0; font-weight: 600; font-size: 1.05rem; color: var(--texto); }
.aud-vacio .tx { margin: 0; color: var(--texto-2); font-size: .9rem; }
.aud-leyenda { display: flex; flex-direction: row; flex-wrap: wrap; align-items: center; gap: .3rem; margin: .1rem 0 .7rem 0; font-size: .82rem; color: var(--texto-2); }
.aud-leyenda.fila { flex-direction: row; flex-wrap: wrap; gap: .3rem 1.2rem; }
.aud-ley { display: inline-flex; align-items: center; gap: .5rem; }
.aud-sw { display: inline-block; width: 1.6rem; height: .9rem; border: 1px solid var(--panel-alto-borde); border-radius: 0; text-align: center; font-weight: 600; line-height: .9rem; font-size: .75rem; flex: 0 0 auto; }
.aud-sw.escala { background: linear-gradient(90deg, @rampa_ini@, @sano@); border-color: var(--sano); }
.aud-sw.sana { background: var(--sano-relleno); border-color: var(--sano); }
.aud-sw.sin-datos { background: var(--sin-datos); border-color: var(--sin-datos-borde); }
.aud-sw.hueco { background: var(--hueco-fondo); border: 2px solid var(--hueco); color: var(--hueco); line-height: .6rem; }

/* interaccion: foco y hover visibles, transiciones suaves; controles de 8 px, tablas de 0 px */
:focus-visible { outline: 2px solid var(--acento) !important; outline-offset: 2px; }
.stButton > button, .stDownloadButton > button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-tertiary"] { border-radius: var(--radio-ctl); font-weight: 600; border: 1px solid var(--panel-alto-borde); background: var(--panel-alto); color: var(--texto);
        transition: background var(--t), border-color var(--t), color var(--t); }
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--acento); color: var(--acento); background: var(--acento-fondo); }
.stButton > button:active, .stDownloadButton > button:active { background: var(--acento-activo); color: var(--texto); }
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] { background: var(--acento); border-color: var(--acento); color: var(--fondo); }
.stButton > button[kind="primary"] p, [data-testid="stBaseButton-primary"] p { color: var(--fondo); }
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { background: var(--acento-hover); border-color: var(--acento-hover); color: var(--fondo); }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"] { transition: border-color var(--t), box-shadow var(--t); }
[data-testid="stDataFrame"] { border: 1px solid var(--panel-borde); border-radius: var(--radio-tabla); overflow: hidden; }
[data-testid="stExpander"] details { background: transparent; border: 0; border-top: 1px solid var(--panel-borde); border-bottom: 1px solid var(--panel-borde); border-radius: var(--radio-tabla); }
[data-testid="stExpander"] summary { transition: background var(--t); }
[data-testid="stExpander"] summary:hover { background: var(--panel-alto); }
[data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom: 1px solid var(--panel-borde); }
[data-testid="stTabs"] button[role="tab"] { font-size: .92rem; font-weight: 400; color: var(--texto-2); transition: color var(--t), background var(--t); }
[data-testid="stTabs"] button[role="tab"] p { color: inherit; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: var(--acento); font-weight: 600; }
[data-testid="stTabs"] button[role="tab"]:hover { background: var(--acento-fondo); color: var(--texto); }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { height: 2px; background: var(--acento); }
[data-testid="stTabs"] [data-baseweb="tab-border"] { height: 1px; background: var(--panel-borde); }
[data-testid="stTable"] table { background: var(--panel); border: 1px solid var(--panel-borde); border-radius: var(--radio-tabla); font-size: .9rem; color: var(--texto); }
[data-testid="stTable"] th { background: var(--panel-alto); color: var(--texto-2); font-weight: 600; text-align: left; white-space: nowrap; }
[data-testid="stTable"] td { vertical-align: top; color: var(--texto); }
[data-testid="stTable"] th, [data-testid="stTable"] td { padding: .35rem .6rem; font-size: .84rem; border-color: var(--panel-borde); }
[data-testid="stTable"] tbody tr { transition: background var(--t); }
[data-testid="stTable"] tbody tr:hover { background: var(--acento-fondo); }
[data-testid="stMarkdownContainer"] .aud-tabla { width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--panel-borde); font-size: .9rem; }
[data-testid="stMarkdownContainer"] .aud-tabla th { background: var(--panel-alto); color: var(--texto-2); font-weight: 600; text-align: left; padding: .45rem .7rem; border: 0; border-bottom: 1px solid var(--panel-borde); vertical-align: bottom; }
[data-testid="stMarkdownContainer"] .aud-tabla td { padding: .45rem .7rem; border: 0; border-bottom: 1px solid var(--panel-borde); vertical-align: top; color: var(--texto); background: transparent; }
[data-testid="stMarkdownContainer"] .aud-tabla tbody tr:last-child td { border-bottom: 0; }
[data-testid="stMarkdownContainer"] .aud-tabla tbody tr { transition: background var(--t); }
[data-testid="stMarkdownContainer"] .aud-tabla tbody tr:hover { background: var(--acento-fondo); }
[data-testid="stMarkdownContainer"] .aud-tabla td:first-child { font-weight: 600; white-space: nowrap; width: 12rem; }
[data-testid="stMarkdownContainer"] .aud-tabla.criterios td, [data-testid="stMarkdownContainer"] .aud-tabla.criterios th { text-align: left; }
[data-testid="stMarkdownContainer"] .aud-tabla.criterios td:first-child { width: auto; }
[data-testid="stMarkdownContainer"] .aud-tabla.criterios tr.elegida td { background: var(--panel-alto); }
.aud-tabla.criterios .elegida-marca { display: inline-block; margin-left: .45rem; font-size: .72rem; font-weight: 600; color: var(--acento); border: 1px solid var(--acento); padding: 0 .3rem; }
.aud-tabla.criterios .cumple, .aud-tabla.criterios .no-cumple { white-space: nowrap; }
.aud-tabla.criterios .cumple { color: var(--sano); font-weight: 600; }
.aud-tabla.criterios .no-cumple { color: var(--texto); }
.aud-tabla.criterios .ico { display: inline-block; width: .95em; height: .95em; vertical-align: -.12em; margin-right: .35em; }
.aud-tabla.criterios .ico svg { display: block; width: 100%; height: 100%; }
[data-testid="stMarkdownContainer"] .aud-criterios-def { margin: .6rem 0 1rem 0; padding: 0; list-style: none; font-size: .86rem; color: var(--texto-2); }
[data-testid="stMarkdownContainer"] .aud-criterios-def li { margin: 0 0 .15rem 0; }
[data-testid="stMarkdownContainer"] .aud-criterios-def b { color: var(--texto); }
/* cargador de archivos en espanol (F19-B6): se oculta el texto en ingles del cargador y se muestra el equivalente; si una version de Streamlit cambia estos atributos,
   el texto en ingles reaparece (la prueba de contenido lo documenta) pero la pagina sigue funcionando */
[data-testid="stFileUploaderDropzone"] { background: var(--panel); border: 1.5px dashed var(--sin-datos-borde); border-radius: var(--radio-ctl); transition: background var(--t), border-color var(--t); }
[data-testid="stFileUploaderDropzone"]:hover { background: var(--panel-alto); border-color: var(--acento); }
[data-testid="stFileUploaderDropzoneInstructions"] span { font-size: 0 !important; line-height: 0; }
[data-testid="stFileUploaderDropzoneInstructions"] span::before { content: "Arrastre el archivo aquí. Formato parquet, hasta 500 MB"; font-size: .9rem; line-height: 1.4; color: var(--texto-2); }
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p { font-size: 0 !important; }
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p::before { content: "Elegir archivo"; font-size: .9rem; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
"""


def css() -> str:
    """Hoja de estilos de la página."""
    reemplazos = {**TOKENS, "ESCALA": "1", "RADIO_PANEL": RADIO_PANEL, "RADIO_CONTROL": RADIO_CONTROL, "RADIO_TABLA": RADIO_TABLA, "SOMBRA_PANEL": SOMBRA_PANEL,
                  "FUENTE": PILA_TIPOGRAFICA, "TITULO": TAMANO_TITULO, "TITULAR": TAMANO_TITULAR, "CIFRA": TAMANO_CIFRA, "rampa_ini": RAMPA_SANA[0]}
    hoja = re.sub(r"@(\w+)@", lambda m: reemplazos[m.group(1)], _CSS_BASE)
    return hoja


def _e(x: object) -> str:
    """Escapa para HTML y une cada «%» con su número con un espacio de no separación (F21): «79,8 %» no se parte entre dos líneas."""
    return re.sub(r"(?<=\d) %", " %", html.escape(str(x), quote=True))


def etiqueta_muestra() -> str:
    """Etiqueta pequeña «en muestra» que va al lado de una cifra del flujo en dos pasos o de un resultado del detector."""
    return '<span class="aud-muestra">en muestra</span>'


def rotulo_control(texto: str, etiqueta: str = "", tono: str = "") -> str:
    """Rótulo de un control con una etiqueta corta al lado en texto simple (F33: «decide la cola» en el acento; «no cambia el lugar» en gris, ``tono`` ``m``)."""
    et = f'<span class="tag {tono}">{_e(etiqueta)}</span>' if etiqueta else ""
    return f'<p class="aud-rotulo">{_e(texto)}{et}</p>'


def veredicto(texto: str, entra: bool) -> str:
    """Veredicto de una caja: con texto y color (verde si entra, rojo si no); el color nunca va solo."""
    return f'<p class="aud-veredicto {"si" if entra else "no"}" role="status">{_e(texto)}</p>'


def barra_lugar(titulo: str, valor: str, zona: float, marca: float, leyenda_zona: str) -> str:
    """Barra «Lugar en la cola»: la zona que se revisa sombreada (``zona``, fracción de 0 a 1) y una marca donde cae la caja (``marca``, fracción de 0 a 1). Con un valor en texto a la derecha del título."""
    z, m = max(0.0, min(1.0, zona)) * 100, max(0.0, min(1.0, marca)) * 100
    return (f'<p class="aud-lugar-t"><span>{_e(titulo)}</span><span>{_e(valor)}</span></p>'
            f'<div class="aud-lugar" role="img" aria-label="{_e(titulo)}: {_e(valor)}"><div class="zona" style="width:{z:.1f}%"></div><div class="marca" style="left:{m:.1f}%"></div></div>'
            f'<div class="aud-lugar-leyenda"><span>0 % · primera caja</span><span>{_e(leyenda_zona)}</span><span>100 % · última</span></div>')


def pasos_calculo(pasos: list[tuple[str, str, str]]) -> str:
    """Los pasos de «Cómo se calcula» como tarjetas con valores vivos: (nombre del paso, valor, explicación corta)."""
    celdas = "".join(f'<div><p class="n">{_e(n)}</p><p class="v">{_e(v)}</p><p class="c">{_e(c)}</p></div>' for n, v, c in pasos)
    return f'<div class="aud-calculo">{celdas}</div>'


_ICONOS_TARJETA = {
    "persona": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>',
    "objetivo": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".6"/>',
    "datos": '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "medidor": '<path d="M4 18a8 8 0 1 1 16 0"/><path d="M12 18l4-6"/>',
    "alerta": '<path d="M12 3l10 18H2z"/><path d="M12 10v5"/><circle cx="12" cy="18" r=".6"/>',
    "escudo": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "servidor": '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><circle cx="7" cy="7.5" r=".6"/><circle cx="7" cy="16.5" r=".6"/>',
}


def icono_tarjeta(nombre: str, grande: bool = False, tono: str = "") -> str:
    """Icono decorativo de una tarjeta (SVG propio, ``aria-hidden``): el significado va siempre en el texto."""
    clase = "aud-ic" + (" g" if grande else "") + (f" {tono}" if tono else "")
    return f'<span class="{clase}" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false">{_ICONOS_TARJETA[nombre]}</svg></span>'


def cabecera_tarjeta(titulo: str, icono: str, etiqueta: str = "", borrador: str = "") -> str:
    """Título de una tarjeta con su icono, una etiqueta opcional («en muestra») y la marca de borrador si el texto de la variante publicada todavía no está comprobado."""
    et = f'<span class="aud-etq">{_e(etiqueta)}</span>' if etiqueta else ""
    bo = f'<span class="aud-etq bor">{_e(borrador)}</span>' if borrador else ""
    return f'<h4>{icono_tarjeta(icono)}<span>{_e(titulo)}</span>{et}{bo}</h4>'


def tarjeta_icono(titulo: str, cuerpo_html: str, icono: str, etiqueta: str = "", borrador: str = "") -> str:
    """Tarjeta de la ficha: icono, título y un cuerpo que arma quien llama (el texto ya viene escapado)."""
    return f'<div class="aud-tf">{cabecera_tarjeta(titulo, icono, etiqueta, borrador)}{cuerpo_html}</div>'


def lista_puntos(puntos: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{_e(p)}</li>" for p in puntos) + "</ul>"


def hero_decide(titulo: str, texto: str, avisos: tuple[str, ...]) -> str:
    """El bloque de arriba de «Ética y límites»: la regla de uso («Decide siempre una persona») y, al lado, lo que nunca debe hacerse; cada aviso lleva un ícono y su texto."""
    x = '<span class="x" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M6 6l12 12M18 6L6 18"/></svg></span>'
    av = "".join(f'<div class="aviso">{x}<span>{_e(a)}</span></div>' for a in avisos)
    return (f'<section class="aud-hero" aria-label="Regla de uso"><div class="izq">{icono_tarjeta("persona", True, "t")}<p class="grande">{_e(titulo)}</p><p>{_e(texto)}</p></div>'
            f'<div class="avisos">{av}</div></section>')


def estadisticas(items: list[tuple[str, str]]) -> str:
    """Tarjetitas con una cifra grande y su etiqueta (Desempeño)."""
    return '<div class="aud-stats">' + "".join(f'<div><p class="k">{_e(k)}</p><p class="v">{_e(v)}</p></div>' for k, v in items) + "</div>"


def barra_comparacion(filas: list[tuple[str, float, str, bool]], descripcion: str) -> str:
    """Barra de comparación de peatones y ciclistas con el número escrito en cada fila (el color no es lo único). ``filas``: (etiqueta, fracción 0 a 1, texto, es_advertencia); la advertencia lleva el punto ámbar."""
    def fila(e: str, f: float, txt: str, aviso: bool) -> str:
        punto = '<span class="aud-punto aviso" aria-hidden="true"></span>' if aviso else ""
        color = SERIE_GRIS if aviso else "var(--acento)"
        return f'<div class="f"><span class="l">{punto}{_e(e)}</span><span class="barra"><i style="width:{max(0.0, min(1.0, f)) * 100:.1f}%;background:{color}"></i></span><span class="v">{_e(txt)}</span></div>'

    return f'<div class="aud-cmp" role="img" aria-label="{_e(descripcion)}">' + "".join(fila(*f) for f in filas) + "</div>"


def paso_ayuda(numero: int, titulo: str, texto: str) -> str:
    return f'<div class="aud-guia3"><p class="n" aria-hidden="true">{numero}</p><h4>{_e(titulo)}</h4><p>{_e(texto)}</p></div>'


def tarjetas_paginas(items: list[tuple[str, str, bool]]) -> str:
    """«Qué hace cada página»: una tarjeta por página con una línea; las nuevas llevan el borde punteado. ``items``: (página, texto, nueva)."""
    return '<div class="aud-pgs">' + "".join(f'<div{" class=" + chr(34) + "nueva" + chr(34) if n else ""}><p><b>{_e(t)}</b>{_e(x)}</p></div>' for t, x, n in items) + "</div>"


def tarjetas_glosario(items: list[dict[str, str]]) -> str:
    """Las tarjetas del glosario (término, grupo y definición, con la redacción de siempre)."""
    return '<div class="aud-gl">' + "".join(f'<div><p class="h"><b>{_e(i["termino"])}</b><span class="c">{_e(i["grupo"])}</span></p><p class="d">{_e(i["definicion"])}</p></div>' for i in items) + "</div>"


def chips(items: list[tuple[str, bool]]) -> str:
    """Etiquetas siempre visibles de Validación: (texto, es_advertencia). La advertencia real lleva el punto ámbar; las demás son neutras (el ámbar no se usa como decoración)."""
    return '<div class="aud-chips">' + "".join(f'<p class="aud-chip">{"<span class=" + chr(34) + "aud-punto aviso" + chr(34) + "></span>" if av else ""}{_e(t)}</p>' for t, av in items) + "</div>"


def criterios_tarjetas(items: list[dict]) -> str:
    """Las tarjetas O1 a O4: clave, nombre, «marca X de N» con símbolo y texto además del color y la definición corta."""
    return '<div class="aud-crit">' + "".join(
        f'<div><p class="c">{_e(i["clave"])}</p><p class="n">{_e(i["nombre"])}</p><p class="r {"si" if i["ok"] else "no"}">{_e(i["texto"])}</p><p class="d">{_e(i["definicion"])}</p></div>' for i in items) + "</div>"


def tabla_estandar(encabezados: list[tuple[str, str, bool]], filas: list[list[str]], descripcion: str) -> str:
    """La tabla estándar de Validación y Puntuar: encabezados cortos con su nombre completo en ``title``, números a la derecha con cifras tabulares, primera columna fija y un contenedor
    con desplazamiento horizontal (enfocable con el teclado) solo si las columnas no caben. ``encabezados`` son (texto, nombre completo, a la derecha)."""
    cab = "".join(f'<th scope="col"{" class=" + chr(34) + "r" + chr(34) if der else ""} title="{_e(tip)}">{_e(txt)}</th>' for txt, tip, der in encabezados)

    def celda(txt: str, der: bool) -> str:
        clases = ("r " if der else "") + ("si" if txt[:1] == "\u2713" else "no" if txt[:1] == "\u2715" else "")
        return f'<td{" class=" + chr(34) + clases.strip() + chr(34) if clases.strip() else ""}>{_e(txt)}</td>'

    cuerpo = "".join("<tr>" + "".join(celda(c, encabezados[i][2]) for i, c in enumerate(f)) + "</tr>" for f in filas)
    return f'<div class="tstd-wrap" role="region" aria-label="{_e(descripcion)}" tabindex="0"><table class="tstd"><thead><tr>{cab}</tr></thead><tbody>{cuerpo}</tbody></table></div>'


def pasos_flujo(pasos: list[tuple[str, str, str, str]]) -> str:
    """Los tres pasos de «Puntuar datos nuevos»: (número, título, detalle, estado). El estado va en texto (hecho / paso actual) además del color; el actual lleva ``aria-current``."""
    def paso(n: str, t: str, d: str, e: str) -> str:
        marca = {"hecho": "hecho", "activo": "paso actual", "pendiente": "", "omitido": "omitido: falta el archivo 2"}[e]
        actual = ' aria-current="step"' if e == "activo" else ""
        clase = {"activo": "activo", "hecho": "hecho", "omitido": "omitido"}.get(e, "pend")
        numero = "\u2713" if e == "hecho" else "\u2013" if e == "omitido" else _e(n)                  # el omitido lleva un guion neutro, nunca el check de «hecho»
        detalle = _e(d) + (" · " + marca if marca else "")
        return f'<div class="{clase}" role="listitem"{actual}><span class="num">{numero}</span><p><span class="t">{_e(t)}</span><span class="e">{detalle}</span></p></div>'

    return '<div class="aud-flujo" role="list" aria-label="Pasos">' + "".join(paso(*p) for p in pasos) + "</div>"


def indicadores(items: list[dict[str, str]]) -> str:
    """Franja de indicadores del Resumen: una tarjeta por cifra (etiqueta, valor, nota). ``tono`` ``hueco`` pinta la tarjeta de alerta (el valor y la palabra siguen en el texto)."""
    def valor(i: dict[str, str]) -> str:
        return _e(i["valor"]) + (f' <small>{_e(i["sufijo"])}</small>' if i.get("sufijo") else "")

    def etiqueta(i: dict[str, str]) -> str:
        return _e(i["etiqueta"]) + (f' {etiqueta_muestra()}' if i.get("en_muestra") else "")

    tarjetas = "".join(f'<div class="aud-kpi{" " + i["tono"] if i.get("tono") else ""}"><p class="et">{etiqueta(i)}</p><p class="va">{valor(i)}</p><p class="no">{_e(i["nota"])}</p></div>' for i in items)
    return f'<div class="aud-kpis" style="--n:{len(items)}">{tarjetas}</div>'


def kicker(texto: str) -> str:
    return f'<p class="aud-kicker">{_e(texto)}</p>'


def titular(html_seguro: str) -> str:
    """Titular del bloque de alertas; el llamador arma el HTML (el número y «posibles huecos» en ``<span class="alerta">``)."""
    return f'<p class="aud-titular">{html_seguro}</p>'


def celda_estado(estado: str, detalle: str) -> str:
    """Segunda línea de una fila de alerta: el estado en palabras (el color nunca va solo) y un detalle."""
    return f'<p class="aud-celda-estado"><b>{_e(estado)}</b> · {_e(detalle)}</p>'


def cola_cabecera() -> str:
    celdas = "".join(f"<span>{_e(c)}</span>" for c in ("Prioridad", "Segmento", "Caja", "Cámara", "Clase", "Prob. sin pareja"))
    return f'<div class="aud-cola-fila cab">{celdas}</div>'


def cola_fila(prioridad: str, segmento: str, caja: str, camara: str, clase: str, probabilidad: str, advertencia: str = "") -> str:
    """Una fila de la cola del Resumen. En ciclistas, ``advertencia`` agrega la etiqueta «Regla poco confiable» con un punto ámbar (la advertencia real) y el texto."""
    etq = f'<span class="etq"><span class="aud-punto aviso"></span>{_e(advertencia)}</span>' if advertencia else ""
    return (f'<div class="aud-cola-fila"><span>{_e(prioridad)}</span><span>{_e(segmento)}</span><span>{_e(caja)}</span><span>{_e(camara)}</span>'
            f'<span>{_e(clase)}{etq}</span><span>{_e(probabilidad)}</span></div>')


def barras_segmentos(items: list[tuple[str, str, int]]) -> str:
    """Barras horizontales del panel «Segmentos con más cajas prioritarias». ``items``: (rótulo del segmento, texto de la cifra, cajas); la barra más larga es la del primero."""
    mayor = max((n for _, _, n in items), default=1) or 1
    filas = "".join(f'<div><div class="t"><span>{_e(rotulo)}</span><b>{_e(cifra)}</b></div><span class="aud-barra"><i style="width:{n / mayor * 100:.1f}%;background:var(--acento)"></i></span></div>' for rotulo, cifra, n in items)
    return f'<div class="aud-segs">{filas}</div>'


def metricas(items: list[tuple[str, str, str, str]]) -> str:
    """Tira de cifras en una fila con líneas finas. ``items``: lista de (etiqueta, valor, nota, tono); tono '' o 'hueco'."""
    celdas = "".join(f'<div class="aud-metrica {tono}"><p class="et">{_e(et)}</p><p class="va">{_e(va)}</p><p class="no">{_e(no) if no else "&nbsp;"}</p></div>' for et, va, no, tono in items)
    return f'<div class="aud-metricas">{celdas}</div>'


def tabla_cifras(filas: list[tuple[str, str, str, float | None, str]]) -> str:
    """Tabla pequeña de cifras de apoyo. Cada fila: (rótulo, valor, nota o '', fracción 0 a 1 de la barra o None, color de la barra). Las barras son proporciones de cifras ya calculadas."""
    cuerpo = []
    for rotulo, valor, nota, fraccion, color in filas:
        sub = f"<small>{_e(nota)}</small>" if nota else ""
        barra = f'<td class="b"><span class="aud-barra"><i style="width:{max(0.0, min(1.0, fraccion)) * 100:.1f}%;background:{color}"></i></span></td>' if fraccion is not None else ""
        cuerpo.append(f'<tr><td class="k">{_e(rotulo)}{sub}</td><td class="v">{_e(valor)}</td>{barra}</tr>')
    return f'<table class="aud-cifras"><tbody>{"".join(cuerpo)}</tbody></table>'


def fila_alerta(titulo: str, texto: str, tono: str = "") -> str:
    """Alerta: punto de color de estado, título y texto (el enlace a la sección va debajo, en la página)."""
    return f'<div class="aud-fila"><span class="aud-punto {tono}"></span><div><span class="tt">{_e(titulo)}.</span> <span class="tx">{_e(texto)}</span></div></div>'


def ficha(titulo: str, texto: str) -> str:
    """Bloque de la ficha del sistema (Ética y límites): título y texto separados por una línea fina."""
    return f'<div class="aud-ficha"><h4>{_e(titulo)}</h4><p>{_e(texto)}</p></div>'


# ------------------------------------------------------------------------------------------------------------ anillo de cámaras
# Cada cámara cubre una cuña del anillo (ángulos desde el frente, en grados, positivo = derecha). La parte trasera no tiene cámara.
ANGULOS_CAMARA = {1: (-22, 22), 2: (-78, -22), 3: (22, 78), 4: (-138, -78), 5: (78, 138)}
NOMBRES_CAMARA = {1: "frontal", 2: "frontal izquierda", 3: "frontal derecha", 4: "lateral izquierda", 5: "lateral derecha"}
NOMBRES_CORTOS = {1: "frontal", 2: "frontal izq.", 3: "frontal der.", 4: "lateral izq.", 5: "lateral der."}
ESTADOS_ANILLO = ("sana", "hueco", "sin_datos", "activa", "apagada")
ROTULO_ESTADO = {"sana": "Sana", "hueco": "Hueco", "sin_datos": "Sin datos"}


def _punto(r: float, grados: float, c: float = 90.0) -> tuple[float, float]:
    a = math.radians(grados)
    return c + r * math.sin(a), c - r * math.cos(a)


def anillo_camaras(estados: dict[int, str], tamano: int = 150, descripcion: str = "", resaltar: int | None = None) -> str:
    """Anillo de las 5 cámaras: un vehículo visto desde arriba con una cuña por cámara.

    ``estados``: {número de cámara: 'sana' | 'hueco' | 'sin_datos' | 'activa' | 'apagada'}. Los tres primeros son los del mapa de calor: sana (teal), hueco (contorno coral grueso y una «X»: el rojo
    nunca va solo) y sin datos (plano y neutro). ``activa`` es el acento sólido (la cámara que ve una caja) y ``apagada`` un contorno punteado (sin selección). SVG inline, sin URL ni fuentes.
    ``descripcion`` es el texto alternativo; ``tamano`` es el ancho en px y el dibujo conserva sus proporciones. ``resaltar`` es el número de una cámara a la que se le dibuja un contorno claro (F31: la de la fila elegida).
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
        partes.append(f'<path class="cu {est}{" sel" if resaltar == cam else ""}" d="{d}"/>')
        if est == "hueco":
            x, y = _punto((r0 + r1) / 2, medio)
            partes.append(f'<path class="xx" d="M{x - 4:.1f} {y - 4:.1f} L{x + 4:.1f} {y + 4:.1f} M{x + 4:.1f} {y - 4:.1f} L{x - 4:.1f} {y + 4:.1f}"/>')
        nx, ny = _punto(r1 + 12, medio)
        partes.append(f'<text class="nu {est}" x="{nx:.1f}" y="{ny:.1f}">{cam}</text>')
    if not descripcion:
        con = [f"{c} ({NOMBRES_CAMARA[c]})" for c in ANGULOS_CAMARA if estados.get(c) == "hueco"]
        descripcion = "Cámaras con celdas marcadas: " + (", ".join(con) if con else "ninguna")
    alto = round(tamano * 150 / 156)                                                  # sin la parte trasera (no tiene cámaras) la caja del dibujo es más baja que ancha
    letra = round(13 * 156 / tamano, 2)                                               # tamaño de los números en unidades del dibujo: unos 13 px en pantalla a cualquier tamaño
    return (f'<svg class="aud-anillo" width="{tamano}" height="{alto}" viewBox="12 6 156 150" style="--nu:{letra}px" role="img" aria-label="{html.escape(descripcion, quote=True)}">'
            f'{"".join(partes)}</svg>')


def leyenda_estados() -> str:
    """Leyenda del anillo con las mismas tres muestras y palabras de la leyenda del mapa de calor (en una fila)."""
    return ('<div class="aud-leyenda fila"><span class="aud-ley"><span class="aud-sw sana"></span>Sana</span><span class="aud-ley"><span class="aud-sw hueco">X</span>Hueco</span>'
            '<span class="aud-ley"><span class="aud-sw sin-datos"></span>Sin datos</span></div>')


def tarjeta_anillo_vertical(titulo: str, texto: str, estados: dict[int, str], tamano: int = 190, resaltar: int | None = None) -> str:
    """Anillo pequeño con un título arriba y un texto debajo, centrado (F31). ``resaltar`` marca la cámara de la fila elegida."""
    return (f'<div class="aud-anillo-vertical"><p class="tt">{_e(titulo)}</p>{anillo_camaras(estados, tamano, resaltar=resaltar)}'
            f'<p class="tx">{_e(texto).replace(chr(10), "<br>")}</p></div>')


def bloque_anillo(estados: dict[int, str], tamano: int, descripcion: str = "") -> str:
    """El anillo grande con su leyenda debajo, centrado."""
    return f'<div class="aud-anillo-bloque">{anillo_camaras(estados, tamano, descripcion)}{leyenda_estados()}</div>'


def tarjeta_anillo(titulo: str, texto: str, estados: dict[int, str], tamano: int = 132) -> str:
    """Bloque plano con el anillo a la izquierda, un título y un texto (separado por una línea fina; sin ficha)."""
    return f'<div class="aud-tarjeta-anillo">{anillo_camaras(estados, tamano)}<div><p class="tt">{_e(titulo)}</p><p class="tx">{_e(texto).replace(chr(10), "<br>")}</p></div></div>'


def vacio(titulo: str, texto: str, anillo: str = "", columna: bool = False) -> str:
    """Estado vacío: un dibujo opcional, qué falta (título) y qué hacer (texto)."""
    return f'<div class="aud-vacio{" columna" if columna else ""}">{anillo}<div><p class="tt">{_e(titulo)}</p><p class="tx">{_e(texto)}</p></div></div>'


def leyenda_mapa(min_cajas: int) -> str:
    """UNA sola leyenda del mapa de calor, en una línea (F31): escala de «cajas con par 2D» de 0 % a 100 % con un degradé, hueco (con X) y sin datos (plano).

    Los textos son cortos; la explicación de cada estado va en el atributo ``title`` (se ve al pasar el cursor).
    """
    return ('<div class="aud-leyenda fila">'
            '<span class="aud-ley" title="Proporción de cajas con pareja en esa cámara y segmento: cuanto más claro, mayor proporción">Cajas con par 2D: 0 %<span class="aud-sw escala"></span>100 %</span>'
            f'<span class="aud-ley" title="Menos de la fracción de lo normal de esa cámara, con al menos {min_cajas} cajas"><span class="aud-sw hueco">X</span>Hueco</span>'
            f'<span class="aud-ley" title="Sin cajas o menos de {min_cajas} en el rango: no se evalúa; no es lo mismo que 0 %"><span class="aud-sw sin-datos"></span>Sin datos (menos de {min_cajas} cajas)</span>'
            '</div>')


def resultado(markdown_html: str, tono: str = "") -> str:
    """Bloque de resultado (el contenido ya viene como HTML seguro construido por la página): una frase, sin caja."""
    return f'<div class="aud-resultado {tono}">{markdown_html}</div>'


def pie(atribucion: str, version: str, segmentos: int | None = None) -> str:
    """Pie único (F26), dos líneas de 12 px en Texto 3: la atribución del conjunto de datos (en inglés, tal cual la pide la licencia) y la versión de la solución con los datos de desarrollo."""
    datos = f"Datos de desarrollo, {segmentos} segmentos" if segmentos else "Datos de desarrollo"
    return f'<div class="aud-pie"><p>{_e(atribucion)}</p><p>{_e(version)}. {_e(datos)}.</p></div>'


def tabla_html(filas: list[tuple[str, str]], encabezados: tuple[str, str]) -> str:
    """Tabla de dos columnas (término, definición) con el texto ajustado a la celda: sin desplazamiento ni acordeones."""
    cuerpo = "".join(f"<tr><td>{_e(a)}</td><td>{_e(b)}</td></tr>" for a, b in filas)
    return f'<table class="aud-tabla"><thead><tr><th>{_e(encabezados[0])}</th><th>{_e(encabezados[1])}</th></tr></thead><tbody>{cuerpo}</tbody></table>'


ICONO_CUMPLE = '<span class="ico" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8.5 L6.5 12 L13 4.5"/></svg></span>'
ICONO_NO_CUMPLE = '<span class="ico" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 4 L12 12 M12 4 L4 12"/></svg></span>'


def tabla_criterios(encabezados: list[str], filas: list[list[str]], elegida: int | None = None, columnas_cumple: tuple[int, ...] = ()) -> str:
    """Tabla de los criterios de selección: la fila elegida va destacada (panel alto) y marcada con la palabra «Elegida»; las columnas de criterios dicen «Cumple» (icono de visto, en el color de lo sano)
    o «No cumple» (icono de cruz, en el color del texto: ni rojo ni ámbar, que están reservados). El icono es un SVG propio, nunca solo color."""
    cabeza = "".join(f"<th>{_e(h)}</th>" for h in encabezados)
    cuerpo = []
    for i, fila in enumerate(filas):
        celdas = []
        for j, v in enumerate(fila):
            if j in columnas_cumple:
                si = v == "Cumple"
                celdas.append(f'<td class="{"cumple" if si else "no-cumple"}">{ICONO_CUMPLE if si else ICONO_NO_CUMPLE}{_e(v)}</td>')
            elif j == 0 and i == elegida:
                celdas.append(f'<td>{_e(v)}<span class="elegida-marca">Elegida</span></td>')
            else:
                celdas.append(f"<td>{_e(v)}</td>")
        clase = ' class="elegida"' if i == elegida else ""
        cuerpo.append(f"<tr{clase}>{''.join(celdas)}</tr>")
    return f'<table class="aud-tabla criterios"><thead><tr>{cabeza}</tr></thead><tbody>{"".join(cuerpo)}</tbody></table>'


def md_a_html(texto: str) -> str:
    """Escapa el texto y convierte **negrita** en <strong> (lo único de Markdown que usan los textos de resultado)."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _e(texto))
