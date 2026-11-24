"""F33: Explica una caja rediseñada (ejemplos como botones, un solo control decide, resultado y veredicto primero, lugar en una barra, cuatro pasos con valores vivos, llegada desde la Cola).
Cubre la lógica pura (umbral del presupuesto, veredicto, lugar con empate, opciones del control) y la página con los datos de prueba y con los reales. Escribe solo en ``tmp_path``."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.ep3.test_app import textos
from tests.ep3.test_pagina_f21 import HAY_REAL, _abrir_real
from tests.ep3.test_pagina_f24 import _abrir, _sin_css, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))


def _t(at) -> str:
    return _sin_css(textos(at)).replace("\xa0", " ")


def _prob(at) -> str:
    return re.search(r'aud-prob-grande">([\d,]+) ?%', " ".join(m.value for m in at.markdown).replace("\xa0", " ")).group(1)


# ------------------------------------------------------------------------------------------------------------ lógica
def test_el_umbral_del_presupuesto_sale_de_la_cola_y_el_veredicto_respeta_el_corte() -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    ref = np.array([-0.0, -0.0, -3.0, -5.0, -10.0, -20.0, -50.0, -100.0, -200.0, -400.0])               # 10 cajas: la cola ordena por puntaje (menos puntos, más arriba)
    u = A.umbral_presupuesto(ref, 0.3)
    assert u["cajas_a_revisar"] == 3 and u["score"] == -3.0 and u["puntos"] == 3                       # se revisan ceil(0,3 × 10) = 3
    assert A.veredicto_caja(-0.0, ref, 0.3)["entra"] and A.veredicto_caja(-3.0, ref, 0.3)["entra"] and not A.veredicto_caja(-5.0, ref, 0.3)["entra"]
    assert A.veredicto_caja(-400.0, ref, 1.0)["entra"]                                                 # con todo el presupuesto entra hasta la última
    assert A.umbral_presupuesto(ref, 0.0001)["cajas_a_revisar"] == 1                                    # nunca cero cajas


def test_la_prioridad_maxima_empatada_no_inventa_un_lugar_exacto() -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    ref = np.array([0.0] * 5 + [-10.0] * 5)
    v = A.veredicto_caja(0.0, ref, 0.2)
    valor, frase = A.texto_lugar(v)
    assert v["empatada"] and v["empatadas"] == 5 and valor.replace("\xa0", " ") == "0 a 50 %" and "5" in frase and "0 puntos" in frase and "empatan" in frase
    v2 = A.veredicto_caja(-10.0, ref, 0.2)
    valor2, frase2 = A.texto_lugar(v2)
    assert not v2["empatada"] and valor2.replace("\xa0", " ") == "50 %" and "50" in frase2 and not v2["entra"]


def test_el_veredicto_cambia_con_el_presupuesto_y_los_textos_lo_dicen() -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    ref = np.linspace(-1000, 0, 200)
    score = -400.0
    chico, grande = A.veredicto_caja(score, ref, 0.1), A.veredicto_caja(score, ref, 0.9)
    assert not chico["entra"] and grande["entra"]
    t1, d1 = A.textos_veredicto(chico, 0.1)
    t2, d2 = A.textos_veredicto(grande, 0.9)
    assert t1.startswith("No se revisaría") and t2.startswith("Se revisaría") and "10" in t1 and "90" in t2 and "Entraría si" in d1 and "dentro del" in d2


def test_las_opciones_del_control_son_unicas_ordenadas_e_incluyen_umbrales_y_ejemplos() -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    o = A.opciones_puntos((32, 10))
    assert o == sorted(set(o)) and o[0] == 0 and o[-1] >= 1000 and 32 in o and 10 in o
    assert {e[k] for e in A.EJEMPLOS_CAJA.values() for k in ("pts", "top")} <= set(o) and len(o) <= 120          # los ejemplos exactos caben; el control sigue siendo manejable


def test_la_referencia_de_la_cola_sigue_el_flujo(entorno: Path) -> None:   # noqa: F811
    from waymo_evaluacion.ep3.app_logica import cargar_datos, referencia_cola

    cajas = cargar_datos(entorno / "datos")["cajas"]
    assert len(referencia_cola(cajas, "uno")) == len(cajas) and len(referencia_cola(cajas, "dos")) == int((~cajas["en_hueco"]).sum())


# ------------------------------------------------------------------------------------------------------------ página
def test_la_pagina_abre_sin_ejemplo_elegido_y_con_resultado_veredicto_y_pasos(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Explica una caja")
    t = _t(at)
    assert at.pills[0].value is None and not at.exception
    assert 'class="aud-prob-grande"' in " ".join(m.value for m in at.markdown) and 'class="aud-veredicto' in " ".join(m.value for m in at.markdown)
    assert "Cómo se calcula" in t and all(p in t for p in ("1 · Entrada", "2 · Puntaje", "3 · Probabilidad", "4 · Lugar")) and "Lugar en la cola" in t
    assert "Cajas parecidas" in t and "Notas del modelo" in [e.label for e in at.expander]
    assert not [b for b in at.button if b.label in ("Caja cercana y densa",)]                                      # los ejemplos ya no son botones sueltos: son una selección


def test_el_control_que_decide_cambia_el_lugar_y_los_que_describen_no(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Explica una caja")
    p0 = _prob(at)
    at.select_slider(key="ex_pts").set_value("1.000").run() if "1.000" in at.select_slider(key="ex_pts").options else at.select_slider(key="ex_pts").set_value(at.select_slider(key="ex_pts").options[-1]).run()
    at.slider(key="ex_dist").set_value(90.0).run()
    assert not at.exception and _prob(at) == p0                                                                    # puntos del LiDAR y distancia no mueven la probabilidad ni el lugar
    at.select_slider(key="ex_top").set_value("0").run()
    assert not at.exception and _prob(at) != p0                                                                    # los del sensor superior sí


def test_restablecer_vuelve_a_los_valores_de_siempre_y_suelta_el_ejemplo(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Explica una caja")
    at.pills[0].set_value("Ciclista lejano").run()
    assert at.radio[0].value == "Ciclista"
    at.button(key="ex_restablecer").click().run()
    assert not at.exception and at.pills[0].value is None and (at.select_slider(key="ex_top").value, at.select_slider(key="ex_pts").value, at.slider[0].value, at.radio[0].value) == (50, 60, 25.0, "Peatón")


def test_mover_un_control_suelta_el_ejemplo_elegido(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Explica una caja")
    at.pills[0].set_value("Caja lejana con pocos puntos").run()
    assert at.pills[0].value == "Caja lejana con pocos puntos"
    at.select_slider(key="ex_top").set_value("20").run()
    assert not at.exception and at.pills[0].value is None


def _plan_en_cola(at, presupuesto: int) -> None:
    from tests.ep3.test_app import ir_a

    ir_a(at, "Cola de revisión")
    at.slider[0].set_value(presupuesto).run()
    ir_a(at, "Explica una caja")


def test_el_presupuesto_de_la_cola_cambia_el_veredicto_de_explica_una_caja(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    from tests.ep3.test_app import ir_a

    at.slider[0].set_value(5).run()
    ir_a(at, "Explica una caja")
    assert not at.exception and "con un presupuesto del 5 %" in _t(at)
    ir_a(at, "Cola de revisión")
    at.slider[0].set_value(95).run()
    ir_a(at, "Explica una caja")
    t = _t(at)
    assert not at.exception and "con un presupuesto del 95 %" in t and "Se revisaría con un presupuesto del 95 %" in t                    # con casi todo el presupuesto la caja de siempre entra


def test_llegar_desde_la_cola_carga_los_valores_avisa_y_mover_un_control_quita_el_aviso(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from tests.ep3.test_app import ir_a

    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    at.session_state["tabla_cola"] = {"selection": {"rows": [1], "columns": [], "cols": [], "cells": []}}
    at.run()
    at.button(key="explicar_caja").click().run()
    assert not at.exception and at.title[0].value == "Explica una caja"
    origen = at.session_state["_explica_origen"]
    assert origen["prioridad"] == 2 and at.pills[0].value == f"De la cola · caja {origen['caja']}"
    t = _t(at)
    assert f"Valores cargados desde la Cola de revisión: caja {origen['caja']}, prioridad 2." in t
    assert at.radio[0].value == origen["clase"]
    ir_a(at, "Explica una caja")                                                                                       # AppTest vuelve a la página por defecto tras el cambio de página del botón: el estado sigue
    assert at.pills[0].value == f"De la cola · caja {origen['caja']}" and "Valores cargados desde" in _t(at)
    at.select_slider(key="ex_top").set_value("500").run()
    assert not at.exception and "Valores cargados desde" not in _t(at) and at.pills[0].value is None                   # al mover un control deja de ser «la caja de la cola»
    ir_a(at, "Resumen")
    ir_a(at, "Explica una caja")
    assert not at.exception and "Valores cargados desde" not in _t(at)


def test_el_texto_de_la_pagina_no_usa_jerga_ni_colores_sueltos() -> None:
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def explica("):fuente.index("# ----", fuente.index("def explica("))]
    assert not re.search(r"#[0-9A-Fa-f]{6}\b", cuerpo) and "score" not in re.sub(r'art\.puntuador|dep\["score"\]|"score"|\bs = float', "", cuerpo.replace("float(art.puntuador.puntuar(fila)[0])", ""))   # sin hex sueltos; «score» solo como variable interna


# ------------------------------------------------------------------------------------------------------------ datos reales: el valor registrado no cambia
@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_con_los_datos_reales_los_valores_registrados_siguen_y_el_cero_dice_que_empata(monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3.app_logica import EJEMPLOS_CAJA

    at = _abrir_real(monkeypatch, "Explica una caja")
    t = _t(at)
    assert _prob(at) == "10,1" and "El 59 % de las cajas de la cola queda antes que esta" in t + " " + " ".join(c.value for c in at.caption).replace("\xa0", " ")      # los valores de siempre
    assert "No se revisaría con un presupuesto del 20 %" in t
    p = {}
    for nombre in EJEMPLOS_CAJA:
        at.pills[0].set_value(nombre).run()
        p[nombre] = _prob(at)
    assert p["Caja cercana y densa"] == "2,8" and p["Caja lejana con pocos puntos"] == "48,9"
    at.select_slider(key="ex_top").set_value("0").run()
    t0 = _t(at) + " " + " ".join(c.value for c in at.caption).replace("\xa0", " ")
    assert "Está entre las primeras 4.742 cajas de la cola" in t0 and "0 puntos del sensor superior" in t0 and "0 a 6 %" in t0 and "Se revisaría con un presupuesto del 20 %" in t0
