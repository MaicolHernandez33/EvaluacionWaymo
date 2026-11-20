"""F21 (P1 a P7): última ronda de pulido de la página. Nota del empate calculada de la cola, orden y ancho de las columnas, Explica una caja (puntaje, escala de los controles, cómo se calcula),
Resumen (alineación, «en muestra» a lo más dos veces), redacción sin términos internos y las seis pestañas de Validación. Las cifras no cambian: solo disposición, textos y formato."""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.app_logica import (
    COLUMNA_FOTOGRAMAS, EJEMPLOS_CAJA, ESCALA_PUNTOS, PASOS_DEL_CALCULO, SECCIONES, empate_inicial, nota_empate, texto_puntaje,
)
from tests.ep3.test_app import ir_a, textos

R = Path(__file__).resolve().parents[2]
REAL = R / "data/09_app_ep3"
REP = R / "data/08_reporting_ep3"
IMG = R / "images/ep3/pagina"
sys.path.insert(0, str(R / "app"))
HAY_REAL = (REAL / "kpis.json").exists()
ORDEN_COLUMNAS = ["Posición", "Prob. sin pareja", "Puntos sensor sup.", "Clase", COLUMNA_FOTOGRAMAS, "Cámara", "Tipo de caso", "Distancia", "Segmento"]
ANCHO_CONTENIDO_1366 = 1062          # ancho medido del área de contenido a 1366 px (capturas de F21); la columna de selección de la tabla ocupa 37 px


def _abrir_real(monkeypatch: pytest.MonkeyPatch, seccion: str | None = None):
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.delenv("WAYMO_APP_DATA", raising=False)
    monkeypatch.delenv("WAYMO_APP_MODELOS", raising=False)
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=180).run()
    if seccion:
        ir_a(at, seccion)
    assert not at.exception, at.exception
    return at


def _texto_visible(at) -> str:
    """Todo el texto que ve la persona en la página actual: markdown, leyendas, tablas, tablas HTML, acordeones y pestañas (sin el CSS ni las etiquetas HTML)."""
    partes = [textos(at)]
    partes += [e.label for e in at.expander] + [t.label for t in at.tabs]
    for d in at.dataframe:
        partes += [str(c) for c in d.value.columns] + d.value.astype(str).to_numpy().ravel().tolist()
    for t in at.table:
        partes += [str(c) for c in t.value.columns] + t.value.astype(str).to_numpy().ravel().tolist()
    s = re.sub(r"<style>.*?</style>", " ", " ".join(partes), flags=re.S)
    return re.sub(r"<[^>]+>", " ", s).replace("\xa0", " ")


def _a_la_vista(at) -> str:
    """Texto de markdown y leyendas que está a la vista: recorre el árbol y salta lo que vive dentro de un popover (no se ve hasta abrirlo)."""
    partes: list[str] = []

    def recorrer(bloque) -> None:
        for hijo in getattr(bloque, "children", {}).values():
            tipo = getattr(hijo, "type", "")
            if tipo == "popover":
                continue
            if tipo in ("markdown", "caption", "title"):
                partes.append(hijo.value)
            recorrer(hijo)

    recorrer(at.main)
    return re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", " ", " ".join(partes), flags=re.S)).replace(" ", " ")


# ------------------------------------------------------------------------------------------------------------ P1: nota del empate y columnas de la cola
def test_la_nota_del_empate_se_calcula_de_la_cola_y_desaparece_sin_empate() -> None:
    top = pd.DataFrame({"score": [0.0, 0.0, 0.0, -5.0], "num_top_lidar_points": [0, 0, 0, 5], "prob_cal": [0.878, 0.80, 0.904, 0.5]})
    n = nota_empate(top)
    assert n == "Las primeras 3 cajas empatan (0 puntos del sensor superior; 87,8 % en la primera y de 80,0 % a 90,4 % en el grupo); el orden entre ellas no es informativo."
    assert nota_empate(top.assign(prob_cal=0.878)) == "Las primeras 3 cajas empatan (0 puntos del sensor superior; 87,8 %); el orden entre ellas no es informativo."
    assert nota_empate(top.iloc[:3]).startswith("Las 3 cajas de la cola empatan")                  # toda la cola empata
    assert nota_empate(top.iloc[[3]]) is None and nota_empate(top.iloc[[0]]) is None and nota_empate(top.iloc[0:0]) is None
    assert nota_empate(top.assign(score=[-1.0, -2.0, -3.0, -4.0])) is None                            # sin empate al inicio no hay nota
    e = empate_inicial(top)
    assert e["n"] == 3 and e["puntos"] == 0.0 and e["prob_primera"] == pytest.approx(0.878) and e["prob_min"] == pytest.approx(0.80)


def test_las_columnas_de_la_cola_caben_a_1366_sin_cortar_el_tipo_de_caso() -> None:
    peor = pd.DataFrame({"Posición": [78626], "Prob. sin pareja": ["87,8 %"], "Puntos sensor sup.": ["1.000"], "Clase": ["Ciclista: poco confiable"], COLUMNA_FOTOGRAMAS: [63],
                         "Cámara": ["4 (lateral izq.)"], "Tipo de caso": ["lejanos y poco densos"], "Distancia": ["77,3 m"], "Segmento": ["100239476024"]})
    assert list(peor.columns) == ORDEN_COLUMNAS
    anchos = F.anchos_columnas(peor)
    assert sum(anchos.values()) + 37 <= ANCHO_CONTENIDO_1366 - 12, (anchos, sum(anchos.values()))     # las nueve columnas visibles sin desplazamiento (y sin la barra vertical)
    for c, w in anchos.items():
        assert w >= len(c) * F.PX_POR_CARACTER + F.PX_MARGEN_ENCABEZADO - 1, (c, w)                      # el encabezado completo cabe


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_la_cola_real_tiene_el_orden_pedido_la_nota_y_el_panel_debajo(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Cola de revisión")
    cols = list(at.dataframe[0].value.columns)
    assert cols[:9] == ORDEN_COLUMNAS and "Prioridad" not in cols
    t = textos(at).replace(" ", " ")
    assert re.search(r"Las primeras [\d.]+ cajas empatan \(0 puntos del sensor superior; [\d,]+ % en la primera y de [\d,]+ % a [\d,]+ % en el grupo\); el orden entre ellas no es informativo\.", t), t[:300]
    assert t.index("el orden entre ellas no es informativo") < t.index("Detalle de la caja")             # la nota va sobre la tabla y el panel de detalle debajo
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert fuente.index('st.dataframe(mostrada, key="tabla_cola"') < fuente.index("_panel_detalle(ctx, r, int(") and 'key="panel_detalle"' in fuente
    at.session_state["tabla_cola"] = {"selection": {"rows": [0], "columns": [], "cells": []}}
    at.run()
    assert not at.exception and "Detalle de la caja en la posición 1" in textos(at).replace(" ", " ")


# ------------------------------------------------------------------------------------------------------------ P2: Explica una caja
def test_la_escala_de_los_puntos_no_es_lineal_e_incluye_los_umbrales_a_y_b() -> None:
    assert ESCALA_PUNTOS == sorted(set(ESCALA_PUNTOS)) and 11 in ESCALA_PUNTOS and 32 in ESCALA_PUNTOS and ESCALA_PUNTOS[0] == 0 and ESCALA_PUNTOS[-1] >= 1000
    pasos = np.diff(ESCALA_PUNTOS)
    assert pasos[-1] > 20 * pasos[0] and len(ESCALA_PUNTOS) <= 20                              # fina cerca de cero y gruesa lejos: casi todas las cajas tienen pocos puntos
    assert len(PASOS_DEL_CALCULO) == 3 and not [p for p in PASOS_DEL_CALCULO if re.search(r"_|score|prob_cal|calibrador\b|PuntuadorRegla|\.py", p)]
    assert texto_puntaje(-50.0) == "Puntaje: -50 (menos los puntos del sensor superior)"


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_explica_no_muestra_menos_50_000_y_dice_que_control_mueve_la_probabilidad(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Explica una caja")
    t = _texto_visible(at)
    assert "-50,000" not in t and "Puntaje: -50 (menos los puntos del sensor superior)" in t
    assert at.select_slider[0].label == "Puntos del sensor superior (este control mueve la probabilidad)"
    assert at.select_slider[1].label == "Puntos del LiDAR en la caja (solo afecta al tipo de caso)" and at.slider[0].label == "Distancia al sensor, en m (solo afecta al tipo de caso)"
    assert at.radio[0].label == "Clase (solo agrega la advertencia de ciclista)"
    assert "11 (punto B)" in at.select_slider[0].options and "32 (punto A)" in at.select_slider[0].options
    assert "Cómo se calcula" in t and all(p in t for p in PASOS_DEL_CALCULO) and "1. " in textos(at)
    assert [b.label for b in at.button] == list(EJEMPLOS_CAJA) and len(at.button) == 3
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "b1, b2, b3, _ = st.columns([1, 1, 1, 1.5])" in fuente                                # los tres ejemplos en una sola fila
    assert '"Punto B"' in fuente and '"Punto A"' in fuente and "mark_rule(" in fuente.split("def explica")[1].split("def _mapa_calor")[0]   # líneas finas en los puntos B (11) y A (32)


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_el_control_de_puntos_del_lidar_no_mueve_la_probabilidad_y_el_de_sensor_superior_si(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Explica una caja")
    def prob(a) -> str:
        return re.search(r'aud-probabilidad">([\d,]+ %)', " ".join(m.value for m in a.markdown)).group(1)

    p0 = prob(at)
    at.select_slider[1].set_value(1000).run()
    assert not at.exception and prob(at) == p0                                                     # los puntos del LiDAR solo cambian el tipo de caso
    at.select_slider[0].set_value(5).run()
    assert not at.exception and prob(at) != p0                                                     # los del sensor superior sí mueven la probabilidad


# ------------------------------------------------------------------------------------------------------------ P3: Resumen
@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_resumen_dice_en_muestra_a_lo_mas_dos_veces_y_la_nota_del_grafico_no_nombra_archivos(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Resumen")
    visible = _texto_visible(at)
    spec = " ".join(c.proto.spec for c in at.get("vega_lite_chart"))                                   # las etiquetas del gráfico también se ven
    a_la_vista = _a_la_vista(at)                                                                        # sin el contenido de los popovers (chip y «Fuente»), que no se ve hasta abrirlos
    etiquetas = set(re.findall(r'"([^"]*en muestra[^"]*)"', spec))                                       # el gráfico repite cada etiqueta en su escala y sus datos, pero se ve una vez
    assert len(re.findall(r"en muestra", a_la_vista, flags=re.I)) + len(etiquetas) <= 2, (re.findall(r".{20}en muestra.{20}", a_la_vista, flags=re.I), etiquetas)
    notas = [c.value for c in at.caption if c.value.startswith("Estimación en muestra")]
    assert len(notas) == 1 and re.fullmatch(r"Estimación en muestra: [\d.]+ cajas × fracción para el 80 % × \d+ s por caja \(supuesto, no medido\)\.", notas[0])
    assert not re.search(r"\.(csv|json|parquet)\b|\bf\d+[a-z]?_", visible), re.findall(r".{20}\.(?:csv|json|parquet).{10}", visible)
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert 'popover("Fuente")' in fuente and 'st.container(key=f"alerta_{a[\'clave\']}")' in fuente and "page_link(ARCHIVO_PAGINA[a[\"seccion\"]]" in fuente   # enlace en la misma fila que su alerta


def test_el_chip_y_los_enlaces_de_las_alertas_quedan_alineados_en_las_capturas() -> None:
    res = REP / "capturas_resultado.json"
    if not res.exists():
        pytest.skip("todavía no se generaron las capturas")
    r = json.loads(res.read_text(encoding="utf-8"))
    medidas = [x for x in r if x.get("geometria")]
    assert medidas, "las capturas de F21 guardan la geometría (chip y alertas)"
    for x in medidas:
        g = x["geometria"]
        assert g["chip_derecha"] is not None and abs(g["chip_derecha"] - g["contenido_derecha"]) <= 1.5, (x["archivo"], g["chip_derecha"], g["contenido_derecha"])      # chip al borde derecho del contenido
        assert g["scroll_horizontal_px"] <= 0, (x["archivo"], g["scroll_horizontal_px"])                    # ninguna página se desplaza en horizontal
        assert all(a["dy"] <= 5 for a in g["alertas"]), (x["archivo"], g["alertas"])                          # cada enlace a la altura de su alerta
    assert any(x["seccion"] == "Resumen" and x["geometria"]["alertas"] for x in medidas)


# ------------------------------------------------------------------------------------------------------------ P4: redacción
def _cadenas_app() -> list[tuple[str, str]]:
    archivos = [R / "app" / "secciones.py", R / "app" / "app.py", R / "app" / "contexto.py", *sorted((R / "app" / "paginas").glob("*.py")),
                R / "src/waymo_evaluacion/ep3/app_logica.py", R / "src/waymo_evaluacion/ep3/formato.py"]
    out: list[tuple[str, str]] = []
    for ruta in archivos:
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        omitidos = {id(n.body[0].value) for n in ast.walk(arbol) if isinstance(n, (ast.FunctionDef, ast.Module, ast.ClassDef)) and ast.get_docstring(n, clean=False) is not None}
        out += [(ruta.name, n.value) for n in ast.walk(arbol) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in omitidos]
    return out


def test_los_textos_de_la_pagina_no_dicen_fuera_de_pliegue_ni_nombran_archivos_internos() -> None:
    cadenas = _cadenas_app()
    for nombre, c in cadenas:
        assert "fuera de pliegue" not in c.lower(), (nombre, c[:80])
        assert not re.search(r"\bf\d+[a-z]?_[a-z0-9_]+\.(csv|json|py)\b", c), (nombre, c[:80])           # «f5_metricas_candidatos.csv» y similares son internos


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_ninguna_pagina_muestra_terminos_internos(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch)
    prohibido = {"pliegue": r"\bpliegues?\b", "fold": r"\bfolds?\b", "OOF": r"\bOOF\b", "brazo": r"\bbrazos?\s+[ABC]\b", "archivo interno": r"\b[\w-]+\.(csv|json|parquet|joblib)\b",
                 "snake_case": r"\b[a-z]{3,}(?:_[a-z0-9]{2,})+\b"}
    permitido_snake = {"lidar_box", "camera_to_lidar_box_association", "num_lidar_points_in_box", "num_top_lidar_points_in_box"}      # nombres de columnas del dataset que la persona lleva en su archivo (tabla «Archivos de entrada»)
    for s in SECCIONES:
        ir_a(at, s)
        t = _texto_visible(at)
        for nombre, patron in prohibido.items():
            hallados = [h for h in re.findall(patron, t, flags=re.I if nombre in ("pliegue", "fold", "brazo") else 0)]
            if nombre == "snake_case":
                hallados = [m.group(0) for m in re.finditer(patron, t) if m.group(0) not in permitido_snake and not re.search(r"(key|box|speed)\.[\w.]*" + re.escape(m.group(0)), t)]
            assert not hallados, (s, nombre, hallados[:5])


# ------------------------------------------------------------------------------------------------------------ P5: Validación
def test_las_marcas_de_los_ejes_de_efectos_no_repiten_etiquetas() -> None:
    import secciones as S

    for datos in ([-0.04, -0.02, 0.005, 0.02], [-0.0805, 0.0, 0.0855], [-0.0015, 0.002], [0.1, 0.9]):
        marcas, dec = S._marcas_eje(datos)
        etiquetas = [f"{m:.{dec}f}" for m in marcas]
        assert len(set(etiquetas)) == len(etiquetas) and marcas[0] <= min(min(datos), 0) and marcas[-1] >= max(max(datos), 0) and len(marcas) <= 12, (datos, etiquetas)
    assert F.nombre_componente("vista_obs") == "vista de observación" and F.nombre_componente("Regla_top") == "Regla top"


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_validacion_tiene_seis_pestanas_sin_columna_de_archivos_y_con_tablas_legibles(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Validación")
    assert [t.label for t in at.tabs] == ["Hiperparámetros", "Ensambles", "Generalización", "Selección", "No supervisado", "En muestra"]
    assert not [c for d in at.dataframe for c in d.value.columns if str(c).startswith("Fuente")]                  # los nombres de archivo no se muestran
    assert len(at.get("vega_lite_chart")) == 5                                                                  # un gráfico por pestaña; «Selección» muestra tablas
    t = _texto_visible(at)
    assert "En validación cruzada por segmentos" in t or "AUC en validación cruzada por segmentos" in t
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "labelLimit=420" in fuente and "alt.Step(70)" in fuente                                              # leyenda completa y barras sin superponer


def test_las_capturas_f21_incluyen_las_seis_pestanas_y_la_cola_sin_seleccion() -> None:
    if not IMG.exists() or not list(IMG.glob("05_validacion_*_1366.png")):
        pytest.skip("todavía no se generaron las capturas")
    for ancho in (1366, 1920):
        nombres = {p.name for p in IMG.glob(f"*_{ancho}.png")}
        for esperado in ("02_cola_de_revision_sin_seleccion", "05_validacion_hiperparametros", "05_validacion_ensambles", "05_validacion_generalizacion", "05_validacion_seleccion",
                         "05_validacion_no_supervisado", "05_validacion_en_muestra", "09_resumen_modo_presentacion"):
            assert f"{esperado}_{ancho}.png" in nombres, (ancho, esperado)
        assert len(nombres) == 15
