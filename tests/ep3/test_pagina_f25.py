"""F25: la página como producto (sin avisos naranjas) y un color por concepto en todas las vistas.
Cubre: el chip neutro del encabezado, las etiquetas «en muestra» sin caja, el ámbar solo en la advertencia de los ciclistas, el mapa único entidad -> color (y su validación),
la barra lateral compacta del modo presentación y la barra de herramientas de los gráficos. Escribe solo en ``tmp_path``."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from tests.ep3.test_app import textos
from tests.ep3.test_pagina_f24 import _abrir, _sin_css, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))
AMBAR = "#F5B73B"


def _css() -> str:
    import estilos as E

    return E.css()


# ------------------------------------------------------------------------------------------------------------ 3: el ámbar solo en la advertencia de los ciclistas
def test_el_ambar_solo_existe_como_color_del_punto_de_advertencia() -> None:
    import estilos as E

    for p in sorted((R / "app").rglob("*.py")):
        n = p.read_text(encoding="utf-8").upper().count(AMBAR)
        assert n == (1 if p.name == "estilos.py" else 0), (p.name, n)                         # un solo lugar: la tabla de tokens
    assert E.TOKENS["aviso_texto"] == AMBAR and not any(k in E.TOKENS for k in ("aviso_fondo", "aviso_borde", "aviso_hover"))
    css = _css()
    assert not re.search(r"--aviso-(fondo|borde|hover)|aviso_(fondo|borde|hover)", css)
    usos = re.findall(r"[^{}\n]*\{[^}]*var\(--aviso-texto\)[^}]*\}", css)
    assert len(usos) == 2 and any(".aud-punto.aviso" in u for u in usos) and any(".aud-aviso::before" in u for u in usos), usos      # solo puntos (el de la alerta y el del aviso del ciclista)
    assert "color: var(--aviso-texto)" not in css and "border: 1px solid var(--aviso-" not in css
    assert re.search(r"\.aud-nota \{[^}]*border-left: 2px solid var\(--sin-datos-borde\)", css)             # filete neutro #3A4B6B
    assert E.TOKENS["sin_datos_borde"] == "#3A4B6B"


def test_el_resumen_no_tiene_alertas_con_punto_de_color_y_el_ambar_solo_va_en_la_etiqueta_del_ciclista(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    t = _sin_css(textos(_abrir(entorno, monkeypatch, "Resumen")))
    assert 'class="aud-fila"' not in t and "Ciclistas: regla poco confiable" not in t and "Celdas marcadas." not in t         # F29: las alertas duplicadas salieron del Resumen


# ------------------------------------------------------------------------------------------------------------ 1: chip (F26: ya no existe)
def test_el_chip_de_estado_se_quito_y_su_texto_no_se_perdio(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    css = _css()
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "chip_estado" not in css and "chip_estado" not in fuente and "CHIP_" not in fuente                      # sin CSS ni código muerto del chip
    at = _abrir(entorno, monkeypatch, "Resumen")
    assert "Datos de desarrollo, sin validación externa" not in textos(at)
    ayuda = _abrir(entorno, monkeypatch, "Ayuda y glosario")
    t = textos(ayuda)
    assert "no deben leerse como una prueba ciega" in t and "preparada y sellada" in t and "donde se descubrió el hueco" in t        # lo que decía el menú del chip está en «¿Qué significa «en muestra»?»


# ------------------------------------------------------------------------------------------------------------ 2: «en muestra» sin caja
def test_en_muestra_es_texto_simple_y_ninguna_vista_lo_pone_en_una_etiqueta(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    import estilos as E

    regla = re.search(r"\.aud-muestra \{[^}]*\}", _css()).group(0)
    assert "color: var(--texto-3)" in regla and "font-size: .8rem" in regla                                # 12 px sobre la base de 15 px
    assert not re.search(r"border|background|padding|aviso", regla), regla
    assert E.etiqueta_muestra() == '<span class="aud-muestra">en muestra</span>'
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "etiqueta_muestra()" not in fuente                                                             # el Resumen y la Cola ya lo dicen en la oración
    at = _abrir(entorno, monkeypatch, "Resumen")
    assert 'class="aud-muestra"' not in _sin_css(textos(at))
    assert not re.search(r"\ben (la )?muestra\b", _sin_css(textos(at)))                                    # F28/F29: el Resumen no dice «en muestra» ni «en la muestra»
    cola = _abrir(entorno, monkeypatch, "Cola de revisión")
    t = _sin_css(textos(cola))
    assert t.count('class="aud-muestra"') == 1 and "(en muestra)" in t                                  # F32: la segunda tarjeta de la Cola lleva «en muestra» (texto simple, sin caja); el Resumen no


# ------------------------------------------------------------------------------------------------------------ 4: un concepto, un color
def test_un_concepto_un_color_en_las_tres_vistas() -> None:
    import estilos as E
    from waymo_evaluacion.ep3.app_logica import FLUJO_BRAZO_A, FLUJO_BRAZO_B, FLUJO_BRAZO_C

    f = E.FLUJOS_COLORES
    assert set(f) == {"Revisión sin orden", FLUJO_BRAZO_A, FLUJO_BRAZO_B, FLUJO_BRAZO_C}                      # los nombres son los del módulo de lógica
    assert f["Revisión sin orden"] == E.TOKENS["texto_3"] and f[FLUJO_BRAZO_A] == "#C77B1E" and f[FLUJO_BRAZO_C] == "#4C82F2"
    assert len(set(f.values())) == 4 and f[FLUJO_BRAZO_B] not in E.CURVAS_COLORES and f[FLUJO_BRAZO_B] not in (E.TOKENS["hueco"], E.TOKENS["sano"], E.TOKENS["acento"], AMBAR)
    assert E.CURVAS_COLORES[0] == f[FLUJO_BRAZO_C] and E.CURVAS_COLORES[1] == f[FLUJO_BRAZO_A]                # «dos pasos» y «un paso» de la curva son los mismos colores
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "E.SERIE_MEDIA" not in fuente and not hasattr(E, "SERIE_MEDIA") and not hasattr(E, "SERIE_ACENTO")
    assert 'E.FLUJOS_COLORES["Solo cola (un paso)"]' in fuente and 'E.FLUJOS_COLORES["Auditoría + cola (dos pasos)"]' in fuente and 'E.FLUJOS_COLORES["Revisión sin orden"]' in fuente
    assert "range=[E.FLUJOS_COLORES[b] for b in brazos]" in fuente                                          # Validación > En muestra


def test_validacion_pinta_las_barras_de_horas_con_el_color_de_cada_flujo(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    import estilos as E

    at = _abrir(entorno, monkeypatch, "Validación")                                                        # F30: el impacto estimado (las barras de horas) es una sección fija de Validación › En muestra
    t = _sin_css(textos(at))
    colores = re.findall(r'<i style="width:[\d.]+%;background:(#[0-9A-Fa-f]{6})"', t)
    assert E.FLUJOS_COLORES["Revisión sin orden"] in colores and E.FLUJOS_COLORES["Solo cola (un paso)"] in colores and E.FLUJOS_COLORES["Auditoría + cola (dos pasos)"] in colores


def test_la_paleta_de_los_flujos_esta_validada() -> None:
    p = R / "docs/ep3/f25_paleta_validacion.json"
    assert p.exists(), "falta f25_paleta_validacion.json (scripts/ep3/f25_validar_paleta.py)"
    d = json.loads(p.read_text(encoding="utf-8"))
    import estilos as E

    assert d["modo"] == "dark" and d["superficie"] == E.TOKENS["panel"] and d["mapa_entidad_color"] == E.FLUJOS_COLORES
    for clave in ("flujos_cromaticos", "curvas_de_la_cola_sin_cambios"):
        salida = d[clave]["todos_los_pares"]
        assert "ALL CHECKS PASS" in salida and "FAIL" not in salida, (clave, salida)
    assert d["gris_linea_base"]["contraste_contra_el_panel"] >= 4.5


# ------------------------------------------------------------------------------------------------------------ 5: barra lateral compacta
def test_la_barra_lateral_queda_compacta_y_el_selector_de_rol_a_la_vista() -> None:
    import estilos as E

    assert re.search(r'\[data-testid="stSidebarUserContent"\] \{[^}]*padding-bottom: 1rem', E.css())      # Streamlit deja 6 rem vacíos debajo del último control
    assert not hasattr(E, "PRESENTACION") and "Modo presentación" not in (R / "app" / "app.py").read_text(encoding="utf-8")         # F30: el interruptor se quitó; queda «Rol»
    assert 'st.sidebar.selectbox("Rol"' in (R / "app" / "app.py").read_text(encoding="utf-8")
    p = R / "docs/ep3/f25_barra_lateral.json"
    if not p.exists():
        pytest.skip("todavía no se midió la barra lateral")
    medidas = json.loads(p.read_text(encoding="utf-8"))
    assert {m["modo"] for m in medidas} == {"normal"}
    for m in medidas:
        assert m["alto_ventana"] == 768 and m["rol_visible"] and m["rol"]["abajo"] <= 768 - 8, m                  # el selector de rol se ve sin desplazar la barra
        assert m["desborde_px"] <= 0 and m["enlaces"] == 8 and m["scroll_horizontal_px"] <= 0, m


# ------------------------------------------------------------------------------------------------------------ 6: barra de herramientas de los gráficos
def test_la_barra_de_herramientas_se_oculta_solo_en_los_graficos_con_un_selector_estable() -> None:
    css = _css()
    m = re.search(r"([^\n{]*)\{ display: none !important; \}", css[css.index("F25: la barra de herramientas"):])
    assert m and m.group(1).strip() == 'div:has(> [data-testid="stVegaLiteChart"]) > [data-testid="stElementToolbar"]'      # data-testid, no clases generadas
    assert "stDataFrame" not in m.group(0)                                                                 # las tablas conservan su barra
