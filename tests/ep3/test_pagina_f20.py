"""F20 (P1 a P12): navegación agrupada, rol y chip de estado, Resumen, Cola de revisión como maestro-detalle (dos flujos, selección de fila, vista por objeto, filtros), Auditoría,
Explica una caja, Validación, Puntuar, Ética, Ayuda, frases prohibidas, estilos y la espera de las capturas. Las cifras no cambian: solo presentación y qué cifra va primero."""
from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.app_logica import (
    ARCHIVO_PAGINA, COLUMNA_FOTOGRAMAS, CURVA_UN_PASO, EJEMPLOS_CAJA, GRUPOS_NAV, ICONOS, PERFILES, SECCIONES, URL_PAGINA, cargar_datos, datos_validacion, detalle_caja,
    ejemplo_lidar_box, filtrar_cola, inicio_resumen, matriz_calor, orden_segmentos, percentil_en_cola, resumen_cola, tabla_cola, tabla_por_objeto, texto_posicion, validar_lidar_box,
)
from tests.ep3.test_app import _datos_sinteticos, _modelos_sinteticos, ir_a, textos

R = Path(__file__).resolve().parents[2]
REAL = R / "data/09_app_ep3"
REP = R / "data/08_reporting_ep3"
sys.path.insert(0, str(R / "app"))
HAY_REAL = (REAL / "kpis.json").exists()


@pytest.fixture(scope="module")
def entorno(tmp_path_factory):
    base = tmp_path_factory.mktemp("f20")
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


def _abrir_real(monkeypatch: pytest.MonkeyPatch, seccion: str | None = None):
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.delenv("WAYMO_APP_DATA", raising=False)
    monkeypatch.delenv("WAYMO_APP_MODELOS", raising=False)
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=180).run()
    if seccion:
        ir_a(at, seccion)
    assert not at.exception, at.exception
    return at


# ------------------------------------------------------------------------------------------------------------ P1: marco y navegación
def test_la_navegacion_esta_agrupada_como_se_pidio_y_las_paginas_existen() -> None:
    assert GRUPOS_NAV == {"Visión general": ["Resumen"], "1 · Filtro": ["Auditoría de cámaras"], "2 · Priorización": ["Cola de revisión"], "Análisis": ["Validación"],
                          "Herramientas": ["Explica una caja", "Puntuar datos nuevos"], "Ayuda": ["Ética y límites", "Ayuda y glosario"]}          # F27: el menú sigue el orden del proceso (filtro, luego priorización)
    assert len(SECCIONES) == 8 and "Inicio" not in SECCIONES and "Evidencia" not in SECCIONES                    # solo se renombran Inicio -> Resumen y Evidencia -> Validación
    assert len(set(URL_PAGINA.values())) == 8 and all(ICONOS[s].startswith(":material/") for s in SECCIONES)
    for s in SECCIONES:
        assert (R / "app" / ARCHIVO_PAGINA[s]).exists(), s
        assert f'S.ejecutar("{s}")' in (R / "app" / ARCHIVO_PAGINA[s]).read_text(encoding="utf-8")
    app = (R / "app" / "app.py").read_text(encoding="utf-8")
    assert "st.navigation(" in app and "st.Page(" in app and "url_path=" in app and "st.logo(" in app and '"Rol"' in app


def test_el_rol_va_al_pie_sin_pildora_y_no_hay_chip_de_estado(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    assert [s.label for s in at.sidebar.selectbox] == ["Rol"] and [t.label for t in at.sidebar.toggle] == []                                                      # F30: el interruptor «Modo presentación» se quitó
    assert "Perfil:" not in textos(at) and "aud-insignia" not in textos(at)
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "chip_estado" not in fuente and "CHIP_" not in fuente and "popover(" in fuente                                # F26: ya no hay chip de estado (el popover «Fuente» y el de la cola sí)
    for s in SECCIONES:                                                                                        # sin chip en NINGUNA página
        ir_a(at, s)
        assert "Datos de desarrollo, sin validación externa" not in textos(at) and not at.warning, s
        if s == "Ayuda y glosario":                                                                           # lo que traía el menú del chip quedó en la pregunta «¿Qué significa «en muestra»?»
            assert "2 celdas cámara x segmento" in textos(at) and "no deben leerse como una prueba ciega" in textos(at), s
        assert not any(e.label.strip() == "¿Qué significa?" for e in at.expander), s            # el acordeón de cada pantalla desapareció (la pregunta frecuente «¿Qué significa «en muestra»?» es otra cosa)


def test_cambiar_de_rol_lleva_a_su_pagina(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch)
    assert at.title[0].value == "Estado de las cámaras"
    for rol, pagina in (("Responsable de calidad de datos", "Auditoría de cámaras"), ("Ingeniero consumidor de datos", "Puntuar datos nuevos")):
        at.sidebar.selectbox[0].set_value(rol).run()
        assert at.title[0].value == pagina
    assert all("alerta" not in v for v in PERFILES.values())                                            # F29: el rol ya no reordena alertas (el Resumen no tiene la lista de alertas por rol)


def test_el_enlace_antiguo_con_seccion_sigue_funcionando(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.setenv("WAYMO_APP_DATA", str(entorno / "datos"))
    monkeypatch.setenv("WAYMO_APP_MODELOS", str(entorno / "modelos"))
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=60)
    at.query_params["seccion"] = "Ética y límites"
    at.run()
    assert not at.exception and at.title[0].value == "Ética y límites"


# ------------------------------------------------------------------------------------------------------------ P2: sistema visual
def test_el_css_cumple_el_sistema_visual_de_la_consola() -> None:
    import estilos as E

    css = E.css()
    # F23 (DEC-87): radios según el papel (panel 14 px, controles 6 px, tablas 0) y UNA sola sombra en toda la hoja (la del panel principal); siguen sin bordes superiores de color ni píldoras
    assert "Segoe UI" in css and "tabular-nums" in css and "border-radius: var(--radio-ctl)" in css and "--radio-panel: 14px" in css and "--radio-ctl: 8px" in css and "--radio-tabla: 0" in css
    assert css.count("box-shadow:") == 1 and "box-shadow: var(--sombra-panel)" in css and "border-top: 4px" not in css and "999px" not in css and "border-top-color" not in css
    assert "font-size: 1.6rem" in css and E.TAMANO_TITULO == "1.6rem" and E.TAMANO_CIFRA == "1.5rem"
    assert ":focus-visible" in css and ":hover" in css and "stSidebarNavLink" in css                                                      # estados hover y foco visibles
    assert "repeat(2, 1fr)" in css and "aud-metricas.pres" not in css                                                                     # 2 x 2 en pantallas angostas; ya no hay variante de modo presentación (F30)
    assert "--escala: 1;" in css and "1.18" not in css
    assert not re.search(r"https?://|@import|url\(", css)
    assert "@" not in re.sub(r"@(keyframes|media)", "", css)                                                                               # ningún marcador @token@ quedó sin reemplazar
    assert set(E.TOKENS) >= {"acento", "hueco", "aviso_texto", "sano", "sin_datos", "panel", "panel_alto", "barra"}                                                  # cobalto = acción; teal = sano; gris plano = sin datos; rojo = hueco; ámbar = solo advertencias reales (F25)
    svg = E.wordmark("Lente", "Waymo Open Dataset v2")
    assert svg.startswith("<svg") and "http" not in svg.replace(E.SVG_NS, "") and "<image" not in svg


def test_el_resumen_no_tiene_fichas_de_la_tira_de_cifras_y_la_tira_ya_no_tiene_variante_de_presentacion(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import estilos as E

    at = _abrir(entorno, monkeypatch, "Resumen")
    assert "aud-metrica" not in re.sub(r"<style>.*?</style>", "", textos(at), flags=re.S)                  # F23: el Resumen ya no abre con cuatro fichas de indicadores
    items = [("a", "1", "", ""), ("b", "2", "", ""), ("c", "3", "", "hueco"), ("d", "4", "", "")]
    assert 'class="aud-metricas"' in E.metricas(items) and "pres" not in E.metricas(items) and E.metricas(items).count("aud-metrica ") == 4


# ------------------------------------------------------------------------------------------------------------ P3: Resumen
def test_el_resumen_no_tiene_portada_de_marketing(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Resumen")
    t = textos(at)
    for prohibida in ("Cómo funciona", "Empiece por aquí", "aud-paso", "Primeros pasos", "Resultados técnicos"):
        assert prohibida not in t, prohibida
    assert {b.label for b in at.button if b.proto.type == "primary"} <= {"Auditar"}                                    # F29: el único botón destacado es «Auditar» de la fila elegida (sin llamadas a la acción de marketing)
    assert "Alertas de cámara" in t and "Cola de revisión" in t and "Segmentos con más cajas prioritarias" in t and "Impacto estimado" not in t      # F29: el impacto estimado solo va en modo presentación


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_las_horas_del_resumen_se_leen_de_su_origen_y_el_titular_es_un_paso_contra_el_azar() -> None:
    D = cargar_datos(REAL)
    r = inicio_resumen(D, 20)
    n = len(D["cajas"])
    m = pd.read_csv(REP / "f6_modelo_escogido.csv").iloc[0]
    assert r["horas_un_paso"] == pytest.approx(float(m["Fraccion_80"]) * n * 20 / 3600)                       # 200 h = fracción un paso × cajas × 20 s
    assert r["horas_dos_pasos"] == pytest.approx(float(m["Fraccion_80_C"]) * n * 20 / 3600)                   # 132 h
    assert r["horas_sin_orden"] == pytest.approx(0.8 * n * 20 / 3600)                                         # 358 h
    assert (round(r["horas_sin_orden"]), round(r["horas_un_paso"]), round(r["horas_dos_pasos"])) == (358, 200, 132)
    assert r["horas_dos_pasos"] < r["horas_un_paso"] < r["horas_sin_orden"]


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_las_cifras_de_ciclistas_usan_las_cifras_de_f12_equidad() -> None:
    D = cargar_datos(REAL)
    eq = pd.read_csv(REP / "f12_equidad.csv")
    c = eq[(eq["grupo"] == "CYCLIST") & (eq["celdas_con_hueco"] == "incluidas")].iloc[0]
    from waymo_evaluacion.ep3.app_logica import datos_ciclistas

    cic = datos_ciclistas(D["evidencia"]["posthoc__equidad"])
    assert F.porcentaje(c["recall_A"]) == F.porcentaje(cic["ciclista"]) and int(c["positivos"]) == int(cic["positivos"]) and int(c["segmentos"]) == int(cic["segmentos"])             # F29: la alerta salió del Resumen; el dato sigue siendo el mismo


# ------------------------------------------------------------------------------------------------------------ P4: Cola de revisión
def test_la_cola_calcula_los_dos_flujos_y_el_de_dos_pasos_sigue_por_defecto(tmp_path: Path) -> None:
    _datos_sinteticos(tmp_path / "d")
    d = cargar_datos(tmp_path / "d")
    r2 = resumen_cola(d["cajas"], d["curva"], "sol", "Todos", 0.2, 20)
    r1 = resumen_cola(d["cajas"], d["curva"], "sol", "Todos", 0.2, 20, "uno")
    assert r2["flujo"] == "dos" and r1["flujo"] == "uno"
    assert r2["cajas_cola_total"] == int((~d["cajas"]["en_hueco"]).sum()) and r1["cajas_cola_total"] == len(d["cajas"])      # un paso ordena TODAS las cajas; dos pasos, solo las celdas sanas
    assert r2["cobertura_dos"] == r1["cobertura_dos"] and r2["cobertura_uno"] == r1["cobertura_uno"] and r2["cobertura"] == r2["cobertura_dos"] and r1["cobertura"] == r1["cobertura_uno"]
    assert r1["horas"] == pytest.approx(r1["cajas_a_revisar"] * 20 / 3600) and "en_hueco" in r2["top"].columns and not r2["top"]["en_hueco"].any()


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_las_cifras_del_flujo_de_un_paso_coinciden_con_su_curva_guardada() -> None:
    D = cargar_datos(REAL)
    sol = D["kpis"]["nombre_curva"]
    for presup, dos, uno in ((0.2, 70, 62), (0.68, 97, None)):
        r = resumen_cola(D["cajas"], D["curva"], sol, "Todos", presup, 20)
        assert round(100 * r["cobertura_dos"]) == dos
        if uno:
            assert round(100 * r["cobertura_uno"]) == uno                                                                   # «unas 62 de cada 100»
        curva = D["curva"][D["curva"]["solucion"] == CURVA_UN_PASO].set_index("presupuesto")["recall"]
        assert abs(r["cobertura_uno"] - float(np.interp(presup, curva.index, curva.values))) < 0.006                      # el conteo observado y la curva guardada difieren menos de 0,6 puntos
    assert r["cajas_a_revisar_dos"] == r["cajas_a_revisar"] and r["cajas_a_revisar_uno"] > r["cajas_a_revisar_dos"] - 1


def test_la_cola_tiene_el_plan_arriba_tres_tarjetas_y_la_lista_en_la_primera_pestana(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    flujo = next(s for s in at.selectbox if s.label == "Flujo")
    assert flujo.value == "Auditoría + cola (dos pasos, en muestra)" and flujo.options == ["Solo cola (un paso)", "Auditoría + cola (dos pasos, en muestra)"]      # visible; valor por defecto actual
    assert [r.label for r in at.radio] == ["Decidir por"] and next(r for r in at.radio).options == ["Presupuesto", "Meta"]
    assert next(s for s in at.slider).label == "Presupuesto (% de la cola)" and any(b.label == "Volver al 20 %" for b in at.button)
    assert [t.label for t in at.tabs] == ["Cola de cajas", "Curva de priorización"]          # F32: la lista es la primera pestaña
    t = textos(at)
    assert all(x in t for x in ("Cajas a revisar", "Cajas sin pareja que se encuentran", "Tiempo estimado", "solo cola:")) and t.count('class="aud-muestra"') == 1       # tres tarjetas; «en muestra» visible en la segunda
    assert "Revisando" not in t and any("Supuestos y confiabilidad" == e.label for e in at.expander)
    flujo.set_value("Solo cola (un paso)").run()
    assert "con auditoría previa:" in textos(at)


def test_seleccionar_una_fila_abre_el_panel_de_detalle(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    assert "Explicar esta caja" not in " ".join(b.label for b in at.button) and "Prioridad 3 de" not in textos(at)                 # F32: sin selección el panel no ocupa espacio
    at.session_state["tabla_cola"] = {"selection": {"rows": [2], "columns": [], "cells": []}}
    at.run()
    t = textos(at)
    assert not at.exception and "**Caja " in t and "Prioridad 3 de" in t and "probabilidad de no tener par en ninguna cámara" in t
    assert any(f"<dt>Segmento</dt><dd>…{s[-6:]}</dd>" in t for s in ("aaaaaaaaaaaa", "bbbbbbbbbbbb", "cccccccccccc"))                # el segmento va en los datos del panel
    assert any(b.label == "Explicar esta caja →" for b in at.button) and all(x in t for x in ("Distancia", "Tipo de caso", "Fotogramas del objeto en la cola"))


def test_el_detalle_usa_la_logica_de_explica_una_caja_y_el_significado_exacto_de_la_posicion(tmp_path: Path) -> None:
    _datos_sinteticos(tmp_path / "d")
    d = cargar_datos(tmp_path / "d")
    r = resumen_cola(d["cajas"], d["curva"], "sol", "Todos", 0.5, 20)
    top = r["top"].assign(es_ciclista=0, az_signed=0.0)
    top.loc[1, "es_ciclista"] = 1
    det = detalle_caja(top, 2, r["cajas_cola_total"], {1: (-20.0, 20.0)})
    assert det["percentil"] == pytest.approx(1 / r["cajas_cola_total"]) and det["advertencia_ciclista"] and det["prob"] == pytest.approx(0.3) and det["camara"] == "1 (frontal)"
    assert "Es un ciclista" in det["texto"] and not detalle_caja(top, 3, r["cajas_cola_total"], {})["advertencia_ciclista"]
    # 0 % es la PRIMERA caja y 100 % la última (fracción de la cola que queda antes de la caja)
    assert percentil_en_cola(d["cajas"]["score"].max() + 1, d["cajas"]) == 0.0 and percentil_en_cola(d["cajas"]["score"].min() - 1, d["cajas"]) == 1.0
    assert texto_posicion(0.59).replace("\xa0", " ") == "Posición en la cola: 59 % (0 % es la primera caja; 100 %, la última)"


def test_la_vista_agrupada_por_objeto_no_cambia_el_conteo_de_cajas(tmp_path: Path, entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _datos_sinteticos(tmp_path / "d")
    d = cargar_datos(tmp_path / "d")
    r = resumen_cola(d["cajas"], d["curva"], "sol", "Todos", 0.5, 20)
    top = r["top"].assign(**{"key.laser_object_id": ["obj" + str(i % 7) for i in range(len(r["top"]))], "es_ciclista": 0, "az_signed": 0.0})
    g = tabla_por_objeto(top, {1: (-20.0, 20.0)}, max_filas=10_000)
    assert len(g) == 7 * top["seg"].nunique() or len(g) == top.groupby(["seg", "key.laser_object_id"]).ngroups
    assert g[COLUMNA_FOTOGRAMAS].sum() == len(top)                                                                # cada caja de la cola cuenta una vez: el conteo total no cambia
    assert g["Mejor posición"].is_monotonic_increasing and "Objeto" in g.columns and "Segmento" in g.columns
    assert all(str(o).startswith("obj") for o in g["Objeto"])                                                       # F30: los identificadores siempre se muestran (ya no hay modo presentación)
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    antes = [m.value for m in at.markdown if 'class="aud-kpis"' in m.value]
    assert len(antes) == 1
    next(t for t in at.toggle if t.label == "Agrupar por objeto").set_value(True).run()
    assert not at.exception and {"Prioridad", "Prob. sin pareja máxima", "Fotogramas"} <= set(at.dataframe[0].value.columns)          # la vista agrupada cambia las columnas, no el conteo
    assert [m.value for m in at.markdown if 'class="aud-kpis"' in m.value] == antes                  # ni el resultado ni las cajas a revisar cambian
    assert any("Vista agrupada" in c.value and "no cambia" in c.value for c in at.caption)


def test_los_filtros_de_clase_y_camara_solo_filtran_la_vista(entorno: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    t = pd.DataFrame({"Clase": ["Peatón", "Ciclista: poco confiable", "Peatón"], "Cámara": ["1 (frontal)", "1 (frontal)", "4 (lateral izq.)"], "Posición": [1, 2, 3]})
    assert filtrar_cola(t, ["Peatón"], None)["Posición"].tolist() == [1, 3] and filtrar_cola(t, None, ["1 (frontal)"])["Posición"].tolist() == [1, 2]
    assert filtrar_cola(t, ["Peatón"], ["4 (lateral izq.)"])["Posición"].tolist() == [3] and len(filtrar_cola(t, [], [])) == 3
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    antes = [m.value for m in at.markdown if 'class="aud-kpis"' in m.value]
    assert len(antes) == 1
    at.multiselect[0].set_value(["Peatón"]).run()
    assert not at.exception and any("Filtrado:" in c.value for c in at.caption)
    assert [m.value for m in at.markdown if 'class="aud-kpis"' in m.value] == antes                      # las cifras globales no cambian


def test_los_encabezados_de_la_tabla_de_la_cola_no_se_cortan() -> None:
    top = pd.DataFrame({"seg": ["100239476024"] * 3, "az_signed": [0.0, 30.0, -40.0], "num_top_lidar_points": [0, 12, 3], "distancia_m": [77.3, 35.0, 12.0], "prob_cal": [0.878, 0.4, 0.1],
                        "es_ciclista": [1, 0, 0], "tipo_caso": ["lejanos y poco densos"] * 3, "key.laser_object_id": ["a", "b", "a"], "key.frame_timestamp_micros": [1, 2, 3]})
    t = tabla_cola(top, 3, {1: (-20.0, 20.0)})
    anchos = F.anchos_columnas(t)
    assert list(t.columns)[:9] == ["Posición", "Prob. sin pareja", "Puntos sensor sup.", "Clase", COLUMNA_FOTOGRAMAS, "Cámara", "Tipo de caso", "Distancia", "Segmento"] and "Prioridad" not in t.columns
    for c, w in anchos.items():
        assert w >= len(c) * F.PX_POR_CARACTER + 10, (c, w)                                                    # el ancho calculado siempre cubre el encabezado completo
    assert anchos["Posición"] >= 70 and anchos[COLUMNA_FOTOGRAMAS] >= len(COLUMNA_FOTOGRAMAS) * F.PX_POR_CARACTER and "Posició" not in " ".join(t.columns).replace("Posición", "")
    assert F.anchos_columnas(pd.DataFrame({"a": []}))["a"] >= 56


# ------------------------------------------------------------------------------------------------------------ P5: Auditoría de cámaras
@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_el_mapa_usa_etiquetas_de_6_digitos_unicas_y_ordena_las_celdas_marcadas_primero() -> None:
    D = cargar_datos(REAL)
    m = matriz_calor(D["celdas"], 100)
    assert m["seg_corto"].str.len().eq(6).all() and m["seg_corto"].nunique() == m["seg"].nunique() == 41                # ningún par de segmentos comparte los 6 últimos dígitos
    orden = orden_segmentos(m, True)
    marcados = {s for s in m.loc[m["hueco"], "seg_corto"]}
    assert set(orden[:len(marcados)]) == marcados and len(marcados) == 2 and orden_segmentos(m, False) == list(dict.fromkeys(m["seg_corto"]))
    assert int(m["hueco"].sum()) == 2 and int(m["sin_datos"].sum()) == 94                                                 # los dos huecos y las 94 celdas sin datos suficientes de siempre


def test_la_auditoria_tiene_una_leyenda_en_una_linea_la_tabla_de_celdas_y_los_controles_del_mapa(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Auditoría de cámaras")
    t = textos(at)
    assert t.count('class="aud-leyenda fila"') == 1 and "Cajas con par 2D: 0 %" in t                                         # F31: una sola leyenda, en una línea, con degradé
    assert any("Cajas afectadas" in list(d.value.columns) for d in at.dataframe)                                            # F31: UNA tabla de celdas marcadas (reemplaza la Lista A y su detalle)
    assert [s.label for s in at.selectbox if s.label in ("Grupo de segmentos", "Orden")] == ["Grupo de segmentos", "Orden"] and any(x.label == "Solo celdas con datos suficientes" for x in at.toggle)
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "legend=None" in fuente and 'st.container(key="mapa_calor")' in fuente and "height=560" not in fuente          # F24: sin desplazamiento interno
    next(x for x in at.toggle if x.label == "Solo celdas con datos suficientes").set_value(True).run()
    assert not at.exception


# ------------------------------------------------------------------------------------------------------------ P6: Explica una caja
def test_los_ejemplos_de_un_clic_cambian_los_controles_y_la_probabilidad(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Explica una caja")
    assert list(at.pills[0].options) == list(EJEMPLOS_CAJA) and at.pills[0].value is None and (at.select_slider(key="ex_top").value, at.select_slider(key="ex_pts").value, at.slider[0].value) == (50, 60, 25.0)       # valores por defecto de siempre; F33: ningún ejemplo elegido al abrir
    probs = {}
    for nombre, e in EJEMPLOS_CAJA.items():
        at.pills[0].set_value(nombre).run()
        assert not at.exception and (at.select_slider(key="ex_pts").value, at.select_slider(key="ex_top").value, at.slider[0].value, at.radio[0].value) == (e["pts"], e["top"], e["dist"], e["clase"])
        m = next(x.value for x in at.markdown if 'class="aud-prob-grande"' in x.value)
        probs[nombre] = float(re.search(r">([\d,]+)\s?%", m).group(1).replace(",", "."))
        assert "de las cajas de la cola queda antes que esta" in textos(at).replace("\xa0", " ") or "Está entre las primeras" in textos(at)
    assert probs["Caja cercana y densa"] <= probs["Caja lejana con pocos puntos"]                                      # más puntos del sensor y menos distancia: menos probable que no tenga pareja
    assert at.radio[0].value == "Ciclista" and any('class="aud-aviso"' in m.value for m in at.markdown)                          # el último ejemplo es un ciclista: lleva la advertencia


# ------------------------------------------------------------------------------------------------------------ P7: Validación
@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_los_graficos_de_validacion_se_leen_de_los_csv_de_origen() -> None:
    ev = cargar_datos(REAL)["evidencia"]
    d = datos_validacion(ev)
    assert set(d) == {"ie9", "ie10", "ie11", "ie11_particiones", "brazos", "nosup"}
    f3 = pd.read_csv(REP / "f3_defecto_vs_optimizado.csv")
    assert d["ie9"]["Mejora"].tolist() == pytest.approx(f3["dif_PR-AUC"].tolist(), abs=1e-6) and d["ie9"]["lo"].tolist() == pytest.approx(f3["dif_PR-AUC_lo"].tolist(), abs=1e-6)
    f4 = pd.read_csv(REP / "f4_ensambles_aporta.csv")
    assert d["ie10"]["Mejora"].tolist() == pytest.approx(f4["dif_AUC"].tolist(), abs=1e-6) and d["ie10"]["Ensamble"].tolist() == f4["ensamble"].tolist()      # la copia de la página trae 8 decimales
    f5 = pd.read_csv(REP / "f5_metricas_candidatos.csv").set_index("candidato")
    assert d["ie11"].set_index("Candidato")["AUC"].to_dict() == pytest.approx(f5["AUC"].to_dict(), abs=1e-6) and d["ie11"].set_index("Candidato")["lo"].to_dict() == pytest.approx(f5["AUC_lo"].to_dict(), abs=1e-6)
    fp = pd.read_csv(REP / "f5_auc_por_fold.csv")
    pl = d["ie11_particiones"]
    for c in pl["Candidato"].unique():                                                                                   # la copia de la página trae 3 candidatos: coinciden con f5_auc_por_fold.csv
        esperado = fp[fp["candidato"] == c].set_index(fp[fp["candidato"] == c]["fold"].astype(str))["AUC"]
        assert pl[pl["Candidato"] == c].set_index("Partición")["AUC"].to_dict() == pytest.approx(esperado.to_dict(), abs=1e-6)
    assert sorted(pl["Candidato"].unique()) == ["LR3", "Regla top", "XGB"] and len(d["brazos"]) == 9 and len(d["nosup"]) == 2
    assert d["brazos"]["Fraccion"].between(0, 1).all() and d["nosup"]["Tasa"].between(0, 1).all()


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_validacion_abre_cada_pestana_con_un_grafico_sin_folds_en_ingles_ni_columnas_cortadas(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Validación")
    assert [t.label for t in at.tabs] == ["Modelo elegido", "Generalización", "Alternativas", "Tipos de caso", "En muestra"]               # F34: cinco pestañas (Alternativas junta hiperparámetros y ensambles)
    assert len(at.get("vega_lite_chart")) == 5                                                                       # Generalización, dos en Alternativas, Tipos de caso y En muestra (Modelo elegido abre con las tarjetas O1 a O4)
    assert sum(1 for e in at.expander if e.label.startswith("Tablas de apoyo")) == 5                                  # F34: «Tablas de apoyo (N)» reemplaza a «Ver tabla completa»
    columnas = re.findall(r"<th[^>]*>([^<]*)</th>", " ".join(m.value for m in at.markdown))                           # F34: las tablas son HTML (componente único)
    assert not [c for c in columnas if re.search(r"\bfolds?\b|\bpliegues?\b", c, re.I)] and "Partición" in columnas and "Particiones en mínimo" in columnas
    assert "Folds" not in textos(at) and "fuera de fold" not in textos(at).lower() and "pliegue" not in textos(at).lower()
    assert not [c for c in columnas if "_" in c]                                                                           # sin snake_case
    html = " ".join(m.value for m in at.markdown)
    assert html.count("\u2715 0 de 11") == 2 and html.count("\u2713 11 de 11") == 2 and html.count("\u2715 No<") >= 22                  # F34: nadie cumple O2 ni O4 (tarjetas y tabla «Criterios por candidato», como en el informe)
    assert F.traducir_folds("AUC fuera de fold; Folds en el máximo") == "AUC en validación cruzada por segmentos; Particiones en el máximo"


# ------------------------------------------------------------------------------------------------------------ P8: Puntuar datos nuevos
def test_puntuar_muestra_el_formato_como_tabla_y_ofrece_un_segmento_de_ejemplo(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    t = textos(at)
    assert "Todavía no hay un segmento cargado" in t and "aud-paso" not in t and "Todavía no hay archivos" not in t and "Sin archivos cargados" not in t          # F35: estado vacío más corto
    assert [u.label for u in at.get("file_uploader")] == ["Archivo 1 (obligatorio): lidar_box", "Archivo 2 (opcional): camera_to_lidar_box_association"]
    assert any("<th" in m.value and "Para qué sirve" in m.value and "Columnas" in m.value and "Archivo" in m.value for m in at.markdown)             # F35: el formato es una tabla estándar (Archivo, Columnas, Para qué sirve)
    ejemplo = next(b for b in at.button if b.label == "Usar un segmento de desarrollo de ejemplo")
    ejemplo.click().run()
    assert not at.exception and "Ejemplo: segmento de desarrollo" in textos(at)
    assert {"Cajas puntuadas", "Cajas en la cola"} <= {m for x in at.markdown for m in re.findall(r'class="et">([^<]+)<', x.value)}
    assert not [x for x in at.get("json")]                                                                                  # sin volcados crudos de JSON


def test_el_ejemplo_reconstruido_pasa_la_validacion_y_conserva_el_orden_de_la_cola() -> None:
    if not HAY_REAL or not (R / "data/06_models_ep3/modelo_final_v3.joblib").exists():
        pytest.skip("faltan los datos o la solución congelada")
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos, puntuar_segmento

    D = cargar_datos(REAL)
    seg = str(D["lista_A"]["segmento"].iloc[0])
    lidar = ejemplo_lidar_box(D["cajas"], seg)
    assert validar_lidar_box(lidar) is None and not lidar.isna().any().any()
    res = puntuar_segmento(lidar, None, cargar_artefactos(R / "data/06_models_ep3"))
    esperado = D["cajas"][D["cajas"]["seg"] == seg].sort_values("score", ascending=False, kind="stable")
    assert len(res.lista_B) == len(esperado) and res.lista_B["num_top_lidar_points"].to_numpy().tolist() == esperado["num_top_lidar_points"].to_numpy().tolist()
    assert res.resumen["tiene_asociacion"] is False and any("sin archivo de asociación" in a for a in res.advertencias)


# ------------------------------------------------------------------------------------------------------------ P9: Ética y Ayuda
@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_etica_es_una_ficha_de_6_bloques_con_las_mismas_cifras_de_siempre(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Ética y límites")
    t = textos(at).replace("\xa0", " ")
    assert t.count('class="aud-tf"') == 4 and 'class="aud-hero"' in t and len(at.get("columns") if hasattr(at, "get") else []) >= 0
    for titulo in ("Propósito", "Datos y licencia", "Desempeño", "Límites conocidos", "Consideraciones éticas", "Dónde corre"):
        assert f"<span>{titulo}</span>" in t, titulo                                                              # F36: cada tarjeta lleva su icono y su título
    assert "115 casos en 14 segmentos" in t and "80,6 %" in t and "44,3 %" in t and "0,823" in t and "79,8 %" in t and "61,9 %" in t       # las mismas cifras, ahora en tarjetas y en la barra
    assert "Nada se guarda ni se envía" in t and "localhost" in t and "uso no comercial" in t


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_ayuda_tiene_el_flujo_en_una_linea_el_glosario_en_tabla_y_preguntas_en_acordeones(monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3.app_logica import GLOSARIO, preguntas_frecuentes

    at = _abrir_real(monkeypatch, "Ayuda y glosario")
    t = textos(at)
    assert t.count("Cómo funciona, en tres pasos") == 1 and "Detector de huecos" in t and "Una persona revisa y decide" in t         # F36: el flujo son tres tarjetas con su enlace
    assert t.count('class="d"') == len(GLOSARIO) == 11 and all(term in t for term, _ in GLOSARIO)                              # F36: el glosario son tarjetas con buscador y grupos
    assert [e.label for e in at.expander] == [q for q, _ in preguntas_frecuentes()] and len(at.expander) == 5                  # solo las preguntas frecuentes son acordeones
    assert "Versión" not in [m.value for m in at.markdown]


# ------------------------------------------------------------------------------------------------------------ P10: redacción
FRASES_PROHIBIDAS = ["Empiece por aquí", "Cómo funciona", "la página se lo dice", "Mueva los controles", "vea qué pasa", "¿Qué significa?", "Primeros pasos", "Resultados técnicos", "Pase el cursor", "Fuera de pliegue"]
FRASE_UNICA = "Nada se guarda ni se envía"


def _cadenas(ruta: Path, excluir_funciones: tuple[str, ...] = ()) -> list[str]:
    """Todas las cadenas de un módulo, salvo las dentro de las funciones indicadas y los docstrings."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    omitidos: set[int] = set()
    for n in ast.walk(arbol):
        if isinstance(n, (ast.FunctionDef, ast.Module, ast.ClassDef)) and ast.get_docstring(n, clean=False) is not None:
            omitidos.add(id(n.body[0].value))
        if isinstance(n, ast.FunctionDef) and n.name in excluir_funciones:
            omitidos.update(id(x) for x in ast.walk(n))
    return [n.value for n in ast.walk(arbol) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in omitidos]


def test_ninguna_frase_prohibida_en_los_textos_de_la_pagina() -> None:
    archivos = [R / "app" / "secciones.py", R / "app" / "estilos.py", R / "app" / "app.py", R / "app" / "contexto.py", *sorted((R / "app" / "paginas").glob("*.py")),
                R / "src/waymo_evaluacion/ep3/app_logica.py", R / "src/waymo_evaluacion/ep3/formato.py"]
    for ruta in archivos:
        textos_ = _cadenas(ruta)
        for frase in FRASES_PROHIBIDAS:
            assert not [c for c in textos_ if frase.lower() in c.lower()], (ruta.name, frase)
        assert not [c for c in textos_ if re.search(r"\b(mueva|vea|pruebe|haga clic|suba|abra|elija)\b", c, re.I) and len(c) > 25 and "Streamlit" not in c], (ruta.name, [c for c in textos_ if re.search(r"\b(mueva|vea|pruebe|haga clic|suba|abra|elija)\b", c, re.I)][:2])


def test_nada_se_guarda_ni_se_envia_solo_aparece_en_ayuda_y_etica() -> None:
    assert not [c for c in _cadenas(R / "app" / "secciones.py", ("etica", "ayuda")) if FRASE_UNICA.lower() in c.lower()]
    assert not [c for c in _cadenas(R / "app" / "estilos.py") if FRASE_UNICA.lower() in c.lower()]                                         # tampoco en el pie ni en el CSS
    from waymo_evaluacion.ep3.app_logica import TEXTOS_ENTORNO

    propios = {v for d in TEXTOS_ENTORNO.values() for v in d.values()}                                                                      # F26-B1: la frase vive en TEXTOS_ENTORNO y solo se usa en Ética y Ayuda
    assert not [c for c in _cadenas(R / "src/waymo_evaluacion/ep3/app_logica.py", ("preguntas_frecuentes",)) if FRASE_UNICA.lower() in c.lower() and c not in propios]
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert fuente.count('texto_entorno("consideracion_etica")') == 1 and fuente.count('texto_entorno("donde_corre")') == 1 and 'texto_entorno("faq_archivos")' not in fuente


def test_la_frase_unica_se_ve_solo_en_las_dos_paginas_permitidas(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch)
    con = []
    for s in SECCIONES:
        ir_a(at, s)
        t = textos(at) + " " + " ".join(e.label for e in at.expander)
        if FRASE_UNICA.lower() in t.lower():
            con.append(s)
    assert set(con) <= {"Ética y límites", "Ayuda y glosario"} and "Ética y límites" in con          # en Ayuda está dentro de la respuesta de una pregunta frecuente


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_los_numeros_visibles_usan_es_cl_y_no_hay_snake_case(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch)
    for s in ("Resumen", "Cola de revisión", "Auditoría de cámaras", "Ética y límites", "Ayuda y glosario"):
        ir_a(at, s)
        t = re.sub(r"<style>.*?</style>", " ", textos(at), flags=re.S)
        t = re.sub(r"<[^>]+>", " ", t).replace("\xa0", " ")
        assert not re.findall(r"\b\d+\.\d{1,2}\s?%", t), (s, re.findall(r"\b\d+\.\d{1,2}\s?%", t))                                     # nunca «21.2 %»
        assert not [c for d in at.dataframe for c in d.value.columns if "_" in str(c)], s


# ------------------------------------------------------------------------------------------------------------ P11: espera de las capturas
def _cargar_capturador():
    spec = importlib.util.spec_from_file_location("capturar_pagina", R / "scripts/ep3/capturar_pagina.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_la_espera_de_las_capturas_no_da_por_lista_una_pagina_a_medias() -> None:
    c = _cargar_capturador()
    ok = {"estado": "notRunning", "spinner": False, "esqueleto": False, "tiene_clave": True, "tiene_pie": True, "conteos_ok": True, "cuentas": [6], "alto": 700, "nodos": 400}
    assert c.listo(ok, "Ética y límites", 2.5) == (True, "")
    # el caso de «Ética y límites»: aparece el primer elemento, pero el script sigue ejecutándose y faltan bloques
    assert not c.listo({**ok, "estado": "running"}, "Ética y límites", 5)[0]
    assert not c.listo({**ok, "conteos_ok": False, "cuentas": [1]}, "Ética y límites", 5)[0] and not c.listo({**ok, "tiene_clave": False}, "Ética y límites", 5)[0]
    assert not c.listo({**ok, "tiene_pie": False}, "Ética y límites", 5)[0] and not c.listo({**ok, "alto": 200}, "Ética y límites", 5)[0]
    assert not c.listo(ok, "Ética y límites", 1.2)[0] and not c.listo({**ok, "spinner": True}, "Ética y límites", 5)[0]                     # el DOM debe llevar 2 s estable
    assert set(c.CLAVE) == set(c.ALTO_MIN) == set(SECCIONES) and dict(c.CLAVE["Ética y límites"]["conteos"])[".aud-tf"] == 4
    assert c.url(8512, "Resumen") == "http://localhost:8512/" and c.url(8512, "Cola de revisión") == "http://localhost:8512/cola"        # la página por defecto se sirve en la raíz


def test_las_capturas_registradas_estan_completas() -> None:
    res = REP / "capturas_resultado.json"
    if not res.exists():
        pytest.skip("todavía no se generaron las capturas")
    r = json.loads(res.read_text(encoding="utf-8"))
    assert all(x["listo"] for x in r) and {x["ancho"] for x in r} == {1366, 1920}
    for x in r:
        assert x["estado_final"]["estado"] == "notRunning" and x["estado_final"]["conteos_ok"] and x["estado_final"]["tiene_pie"], x["archivo"]
        assert not x["errores_consola"], (x["archivo"], x["errores_consola"])
    etica = [x for x in r if x["seccion"] == "Ética y límites"]
    assert etica and all(x["estado_final"]["cuentas"] == [6] for x in etica)                                          # los 6 bloques de la ficha, no 1
    carpeta = R / "images/ep3/pagina"
    for ancho in (1366, 1920):
        assert len(list(carpeta.glob(f"*_{ancho}.png"))) == 13 and all(p.stat().st_size > 20_000 for p in carpeta.glob(f"*_{ancho}.png"))
