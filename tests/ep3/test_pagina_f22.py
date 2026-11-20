"""F22 (DEC-82 a DEC-85): sistema visual «mesa de luz de sensores». Anillo de cámaras, estados vacíos, barra lateral de tinta, movimiento que respeta `prefers-reduced-motion` y contraste de los tokens nuevos.
Solo presentación: las cifras y los textos sellados no cambian (los cubren las pruebas de F20 y F21, que siguen vigentes)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from tests.ep3.test_app import _datos_sinteticos, _modelos_sinteticos, ir_a, textos

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))


@pytest.fixture(scope="module")
def entorno(tmp_path_factory):
    base = tmp_path_factory.mktemp("f22")
    _datos_sinteticos(base / "datos")
    _modelos_sinteticos(base / "modelos")
    (base / "datos" / "evidencia" / "ie12__brazo_C_y_equilibrio.csv").write_text("candidato,Fraccion_80_C,Fraccion_80_A\nRegla top,0.3,0.45\n", encoding="utf-8")
    return base


def _abrir(entorno: Path, monkeypatch: pytest.MonkeyPatch, seccion: str | None = None):
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.setenv("WAYMO_APP_DATA", str(entorno / "datos"))
    monkeypatch.setenv("WAYMO_APP_MODELOS", str(entorno / "modelos"))
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=90).run()
    if seccion:
        ir_a(at, seccion)
    assert not at.exception, at.exception
    return at


# ------------------------------------------------------------------------------------------------------------ tokens
def test_los_tokens_nuevos_cumplen_el_contraste_y_la_barra_lateral_es_oscura() -> None:
    import estilos as E

    pares = set(E.PARES_CONTRASTE)
    assert {("tinta_texto", "tinta"), ("tinta_suave", "tinta"), ("tinta_texto", "tinta_2"), ("tinta_acento", "tinta"), ("sano", "tarjeta"), ("primario", "tarjeta")} <= pares
    for fg, bg in E.PARES_CONTRASTE:
        assert E.contraste(E.TOKENS[fg], E.TOKENS[bg]) >= 4.5, (fg, bg)
    assert E.contraste(E.TOKENS["tinta"], "#FFFFFF") > 10                                                    # la barra lateral es realmente oscura frente al lienzo
    assert E.contraste(E.CURVAS_COLORES[0], E.TOKENS["tarjeta"]) >= 4.5                                          # la curva principal se lee sobre las tarjetas blancas


def test_el_css_declara_transiciones_foco_y_respeta_el_movimiento_reducido() -> None:
    import estilos as E

    css = E.css()
    assert "prefers-reduced-motion: reduce" in css and "animation: none !important" in css and "transition: none !important" in css
    assert css.count("transition:") >= 8 and "--t: 150ms" in css                                           # transiciones de 150 ms en botones, navegación, selectores, filas y paneles
    assert "@keyframes aud-entra" in css and ".st-key-panel_detalle { animation" in css                     # un solo movimiento propio: el panel de detalle aparece al elegir una fila
    assert css.count("animation:") == 2                                                                      # el del panel y la regla de movimiento reducido
    assert "stSidebar" in css and "var(--tinta)" in css and ":focus-visible" in css and "tinta-acento" in css
    assert not re.search(r"@\w+@", css)


# ------------------------------------------------------------------------------------------------------------ anillo de cámaras
def test_el_anillo_dibuja_cinco_cunas_y_el_hueco_lleva_x_ademas_del_rojo() -> None:
    import estilos as E

    svg = E.anillo_camaras({1: "sana", 2: "sana", 3: "hueco", 4: "sana", 5: "hueco"})
    assert svg.startswith("<svg") and svg.count('class="cu ') == 5 and svg.count('class="cu hueco"') == 2
    assert svg.count('class="xx"') == 2                                                                      # el rojo nunca va solo: cada hueco lleva una X
    assert 'role="img"' in svg and "3 (frontal derecha)" in svg and "5 (lateral derecha)" in svg           # texto alternativo para lectores de pantalla
    assert "http" not in svg and "<image" not in svg and "url(" not in svg
    for n in "12345":
        assert f">{n}</text>" in svg


def test_el_anillo_marca_la_camara_activa_y_apaga_las_demas() -> None:
    import estilos as E

    svg = E.anillo_camaras({c: ("activa" if c == 1 else "apagada") for c in range(1, 6)}, 128, "Cámara de la caja: 1 (frontal)")
    assert svg.count('class="cu activa"') == 1 and svg.count('class="cu apagada"') == 4 and 'aria-label="Cámara de la caja: 1 (frontal)"' in svg and 'width="128"' in svg
    assert 'class="xx"' not in svg
    assert "ninguna" in E.anillo_camaras({c: "sana" for c in range(1, 6)})                                   # sin huecos, el texto alternativo lo dice
    with pytest.raises(ValueError):
        E.anillo_camaras({1: "rosa"})


def test_los_estados_vacios_dicen_que_falta_y_que_hacer() -> None:
    import estilos as E

    h = E.vacio("Ninguna caja cumple los filtros", "Quite una clase o una cámara para volver a ver la cola.")
    assert 'class="aud-vacio"' in h and "Ninguna caja cumple los filtros" in h and "Quite una clase" in h
    assert "&lt;" in E.vacio("<b>", "x") and "<b>" not in E.vacio("<b>", "x")                               # el texto se escapa
    t = E.tarjeta_anillo("Celdas marcadas por cámara", "Cámara 3: 1 celda marcada.", {c: "sana" for c in range(1, 6)})
    assert 'class="aud-tarjeta-anillo"' in t and "<svg" in t


# ------------------------------------------------------------------------------------------------------------ en la página
def test_el_resumen_muestra_el_anillo_con_las_celdas_marcadas_por_camara(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Resumen")
    t = textos(at)
    assert 'class="aud-anillo"' in t and 'class="cu hueco"' in t and "Cámara 3 (frontal der.): 1 celda marcada." in t     # la Lista A sintética tiene una celda en la cámara 3
    assert t.count('class="cu hueco"') == 1 and "Impacto estimado" in t and "Alertas" in t


def test_la_auditoria_muestra_el_anillo(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Auditoría de cámaras")
    assert 'class="aud-anillo"' in textos(at) and "Celdas marcadas por cámara" in textos(at)


def test_la_cola_usa_estado_vacio_y_el_detalle_ilumina_la_camara(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    t = textos(at)
    assert "Seleccione una fila" in t and 'class="aud-vacio"' in t and 'class="cu apagada"' in t and 'class="cu activa"' not in t
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert 'key="panel_vacio"' in fuente and 'key="panel_detalle"' in fuente                                  # claves distintas: el detalle se monta de nuevo y su aparición se anima
    assert "activa" in fuente and "Ninguna caja cumple los filtros" in fuente


def test_puntuar_sin_archivos_muestra_el_estado_vacio(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    t = textos(at)
    assert "Sin archivos cargados" in t and 'class="aud-vacio"' in t and "Todavía no hay archivos" not in t


def test_los_graficos_comparten_un_solo_tema() -> None:
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert fuente.count(".configure(") == 1 and "domain=False" in fuente and 'gridColor="#E3E9F1"' in fuente    # una sola función ``_grafico`` configura todos
    assert "cornerRadiusEnd=" in fuente and 'range=["#E6F3F4", E.TOKENS["sano"]]' in fuente                     # barras redondeadas y mapa en verde azulado (sano)
