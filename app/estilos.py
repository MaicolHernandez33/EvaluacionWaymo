"""Estilos y componentes HTML de la página (CSS propio y estático: sin fuentes externas, sin CDN, sin imágenes remotas).

Los colores son TOKENS: cualquier color de la página sale de ``TOKENS``. ``contraste()`` calcula el contraste WCAG y la prueba
``tests/ep3/test_estilos.py`` exige >= 4,5:1 en cada par de texto y fondo. La guía ``docs/ep3/guia_estilo_pagina.md`` se genera desde aquí.
"""
from __future__ import annotations

import html

TOKENS = {
    "primario": "#1D4E89",         # azul profundo: títulos, botones, enlaces
    "primario_oscuro": "#14365F",
    "acento": "#0B6E69",           # verde azulado: datos positivos y pasos
    "texto": "#1B2430",
    "texto_suave": "#4A5568",
    "fondo": "#FFFFFF",
    "superficie": "#F2F5F9",       # tarjetas y barra lateral
    "borde": "#D5DCE6",
    "aviso_fondo": "#FFF4D6",      # ámbar: avisos
    "aviso_texto": "#5C3D00",
    "aviso_borde": "#C98A00",
    "hueco": "#B42318",            # rojo: huecos de cámara
    "hueco_fondo": "#FDECEA",
}
# pares (texto, fondo) que deben tener contraste >= 4,5:1
PARES_CONTRASTE = [("texto", "fondo"), ("texto", "superficie"), ("texto_suave", "fondo"), ("texto_suave", "superficie"), ("primario", "fondo"), ("primario", "superficie"),
                   ("fondo", "primario"), ("fondo", "primario_oscuro"), ("acento", "fondo"), ("acento", "superficie"), ("aviso_texto", "aviso_fondo"), ("hueco", "fondo"), ("hueco", "hueco_fondo")]
ESPACIADO = {"xs": "0.25rem", "s": "0.5rem", "m": "1rem", "l": "1.5rem", "xl": "2rem"}


def _lum(hex_: str) -> float:
    h = hex_.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(fg: str, bg: str) -> float:
    """Razón de contraste WCAG entre dos colores hexadecimales (1 a 21)."""
    a, b = sorted((_lum(fg), _lum(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def css(presentacion: bool = False) -> str:
    """Hoja de estilos de la página. En modo presentación se agranda la tipografía y las tarjetas."""
    t = TOKENS
    escala = "1.18" if presentacion else "1"
    return f"""
<style>
:root {{ --escala: {escala}; --primario: {t['primario']}; --acento: {t['acento']}; --texto: {t['texto']}; --suave: {t['texto_suave']}; --superficie: {t['superficie']};
        --borde: {t['borde']}; --aviso-fondo: {t['aviso_fondo']}; --aviso-texto: {t['aviso_texto']}; --aviso-borde: {t['aviso_borde']}; --hueco: {t['hueco']}; --hueco-fondo: {t['hueco_fondo']}; }}
html, body, [data-testid="stAppViewContainer"] {{ font-size: calc(16px * var(--escala)); }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }}
h1, h2, h3 {{ color: var(--primario); letter-spacing: -0.01em; }}
.aud-cabecera {{ display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: .5rem; border-bottom: 2px solid var(--borde); padding-bottom: .6rem; margin-bottom: 1rem; }}
.aud-producto {{ font-size: calc(1.7rem * var(--escala)); font-weight: 700; color: var(--primario); margin: 0; }}
.aud-eslogan {{ color: var(--suave); margin: 0; font-size: 1.02rem; }}
.aud-insignia {{ display: inline-block; padding: .15rem .65rem; border-radius: 999px; font-size: .85rem; font-weight: 600; border: 1px solid var(--borde); background: var(--superficie); color: var(--texto); white-space: nowrap; }}
.aud-insignia.primaria {{ background: var(--primario); color: #FFFFFF; border-color: var(--primario); }}
.aud-insignia.aviso {{ background: var(--aviso-fondo); color: var(--aviso-texto); border-color: var(--aviso-borde); }}
.aud-insignia.hueco {{ background: var(--hueco-fondo); color: var(--hueco); border-color: var(--hueco); }}
.aud-tarjetas {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin: .6rem 0 1.2rem 0; }}
.aud-tarjeta {{ background: var(--superficie); border: 1px solid var(--borde); border-top: 4px solid var(--primario); border-radius: 10px; padding: 1rem 1.1rem; }}
.aud-tarjeta.aviso {{ border-top-color: var(--aviso-borde); }}
.aud-tarjeta.hueco {{ border-top-color: var(--hueco); }}
.aud-tarjeta.acento {{ border-top-color: var(--acento); }}
.aud-tarjeta .titulo {{ color: var(--suave); font-size: .92rem; font-weight: 600; margin: 0 0 .2rem 0; min-height: 2.5em; }}
.aud-tarjeta .valor {{ color: var(--texto); font-size: calc(2rem * var(--escala)); font-weight: 700; line-height: 1.15; white-space: nowrap; margin: 0; }}
.aud-tarjeta .nota {{ color: var(--suave); font-size: .85rem; margin: .25rem 0 0 0; }}
.aud-pasos {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin: .6rem 0 1.2rem 0; }}
.aud-paso {{ position: relative; background: #FFFFFF; border: 1px solid var(--borde); border-radius: 10px; padding: 1rem 1.1rem 1rem 3.2rem; }}
.aud-paso .num {{ position: absolute; left: .9rem; top: .9rem; width: 1.7rem; height: 1.7rem; border-radius: 50%; background: var(--primario); color: #FFFFFF; font-weight: 700; display: flex; align-items: center; justify-content: center; }}
.aud-paso .titulo {{ color: var(--primario); font-weight: 700; margin: 0 0 .2rem 0; }}
.aud-paso .texto {{ color: var(--texto); margin: 0; font-size: .95rem; }}
.aud-resultado {{ background: var(--superficie); border-left: 6px solid var(--primario); border-radius: 8px; padding: 1rem 1.2rem; margin: .6rem 0 1rem 0; font-size: calc(1.15rem * var(--escala)); }}
.aud-resultado.aviso {{ border-left-color: var(--aviso-borde); background: var(--aviso-fondo); color: var(--aviso-texto); }}
.aud-caja-advertencia {{ background: var(--aviso-fondo); color: var(--aviso-texto); border: 1px solid var(--aviso-borde); border-radius: 8px; padding: .7rem 1rem; margin: .5rem 0; }}
.aud-bloque p.aud-grande {{ font-size: calc(3rem * var(--escala)); font-weight: 800; color: var(--primario); line-height: 1.1; white-space: nowrap; margin: 0; }}
.aud-pie {{ margin-top: 2.2rem; padding-top: .8rem; border-top: 1px solid var(--borde); color: var(--suave); font-size: .85rem; display: flex; flex-wrap: wrap; gap: .4rem 1.4rem; }}
[data-testid="stSidebar"] {{ background: var(--superficie); }}
[data-testid="stSidebar"] .aud-producto {{ font-size: 1.25rem; }}
:focus-visible {{ outline: 3px solid var(--primario) !important; outline-offset: 2px; }}
.stButton > button, .stDownloadButton > button {{ border-radius: 8px; font-weight: 600; }}
[data-testid="stDataFrame"] {{ border: 1px solid var(--borde); border-radius: 8px; }}
</style>
"""


def _e(x: object) -> str:
    return html.escape(str(x), quote=True)


def cabecera(producto: str, eslogan: str, perfil: str) -> str:
    return (f'<div class="aud-cabecera"><div><p class="aud-producto">{_e(producto)}</p><p class="aud-eslogan">{_e(eslogan)}</p></div>'
            f'<span class="aud-insignia primaria">Perfil: {_e(perfil)}</span></div>')


def tarjeta(titulo: str, valor: str, nota: str = "", tono: str = "") -> str:
    """Tarjeta de cifra. ``tono``: '', 'aviso', 'hueco' o 'acento'."""
    return (f'<div class="aud-tarjeta {tono}"><p class="titulo">{_e(titulo)}</p><p class="valor">{_e(valor)}</p>' + (f'<p class="nota">{_e(nota)}</p>' if nota else "") + "</div>")


def tarjetas(items: list[tuple[str, str, str, str]]) -> str:
    """Fila de tarjetas: lista de (titulo, valor, nota, tono)."""
    return '<div class="aud-tarjetas">' + "".join(tarjeta(*i) for i in items) + "</div>"


def pasos(items: list[tuple[str, str]]) -> str:
    """Los pasos de «Cómo funciona», dibujados con HTML y CSS propios."""
    return '<div class="aud-pasos">' + "".join(f'<div class="aud-paso"><span class="num">{i}</span><p class="titulo">{_e(t)}</p><p class="texto">{_e(x)}</p></div>' for i, (t, x) in enumerate(items, 1)) + "</div>"


def insignia(texto: str, tono: str = "") -> str:
    return f'<span class="aud-insignia {tono}">{_e(texto)}</span>'


def resultado(markdown_html: str, tono: str = "") -> str:
    """Bloque de resultado destacado (el contenido ya viene como HTML seguro construido por la página)."""
    return f'<div class="aud-resultado {tono}">{markdown_html}</div>'


def pie(version: str) -> str:
    return (f'<div class="aud-pie"><span>{_e(version)}</span><span>Datos: Waymo Open Dataset v2, uso académico</span><span>Una persona revisa y decide</span>'
            "<span>Nada se guarda ni se envía</span></div>")


def md_a_html(texto: str) -> str:
    """Escapa el texto y convierte **negrita** en <strong> (lo único de Markdown que usan los textos de resultado)."""
    import re

    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _e(texto))
