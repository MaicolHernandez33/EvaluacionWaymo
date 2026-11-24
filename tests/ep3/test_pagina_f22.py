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
def test_la_auditoria_muestra_el_anillo(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Auditoría de cámaras")
    assert 'class="aud-anillo"' in textos(at) and "Celdas marcadas por cámara" in textos(at)


def test_puntuar_sin_archivos_muestra_el_estado_vacio(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    t = textos(at)
    assert "Todavía no hay un segmento cargado" in t and 'aud-vacio' in t and "Todavía no hay archivos" not in t


def test_los_graficos_comparten_un_solo_tema() -> None:
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert fuente.count(".configure(") == 1 and "domain=False" in fuente and 'gridColor=t["panel_borde"]' in fuente    # una sola función ``_grafico`` configura todos
    assert "cornerRadiusEnd=" in fuente and "range=E.RAMPA_SANA" in fuente                     # barras redondeadas y mapa en teal (sano)
