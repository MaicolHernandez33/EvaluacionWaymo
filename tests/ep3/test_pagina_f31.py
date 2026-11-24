"""F31: Auditoría de cámaras rediseñada (franja de resumen, UNA tabla de celdas marcadas con el anillo al lado, mapa con las filas peores y definición plegada).
Cubre la lógica (resumen, orden por gravedad, filas visibles del mapa, tabla, umbral), la página con los datos de prueba y con 300 segmentos sintéticos (solo en memoria o en ``tmp_path``). Escribe solo en ``tmp_path``."""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

import pandas as pd
import pytest

from tests.ep3.test_app import textos
from tests.ep3.test_pagina_f24 import _abrir, _sin_css, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))


@pytest.fixture(scope="module")
def entorno300(entorno: Path, tmp_path_factory):
    """El entorno sintético con 300 segmentos en las celdas y en la Lista A (las cajas siguen siendo las de siempre: la Auditoría no las usa)."""
    from waymo_evaluacion.ep3.escala_sintetica import celdas_sinteticas

    base = tmp_path_factory.mktemp("f31_300")
    shutil.copytree(entorno / "datos", base / "datos")
    shutil.copytree(entorno / "modelos", base / "modelos")
    celdas, lista = celdas_sinteticas(300)
    celdas.to_csv(base / "datos" / "celdas.csv", index=False)
    lista.to_csv(base / "datos" / "lista_A.csv", index=False)
    return base


# ------------------------------------------------------------------------------------------------------------ lógica
def test_el_resumen_de_la_auditoria_cuenta_celdas_cajas_y_sin_pareja() -> None:
    from waymo_evaluacion.ep3.app_logica import matriz_calor, resumen_auditoria
    from waymo_evaluacion.ep3.escala_sintetica import celdas_sinteticas

    celdas, lista = celdas_sinteticas(300)
    r = resumen_auditoria(matriz_calor(celdas, 100), lista)
    assert r["celdas_total"] == 1500 and r["segmentos"] == 300 and r["celdas_marcadas"] == len(lista) == int(celdas[[f"hueco_c{c}" for c in range(1, 6)]].to_numpy().sum())
    assert r["cajas_afectadas"] == int(lista["cajas_afectadas_poblacion_principal"].sum()) and r["sin_pareja"] == int(lista["positivos_afectados"].sum())
    assert r["pct_sin_pareja"] == pytest.approx(r["sin_pareja"] / r["cajas_afectadas"])


def test_el_titular_usa_singular_y_plural() -> None:
    from waymo_evaluacion.ep3.app_logica import titular_auditoria

    assert titular_auditoria(1) == "1 posible hueco de cámara en los últimos datos sin revisar."
    assert titular_auditoria(2) == "2 posibles huecos de cámara en los últimos datos sin revisar." and titular_auditoria(0).startswith("Ninguna cámara")


def test_el_orden_por_gravedad_pone_primero_los_segmentos_con_celdas_marcadas() -> None:
    from waymo_evaluacion.ep3.app_logica import matriz_calor, orden_gravedad
    from waymo_evaluacion.ep3.escala_sintetica import celdas_sinteticas

    celdas, lista = celdas_sinteticas(300)
    m = matriz_calor(celdas, 100)
    orden = orden_gravedad(m)
    marcados = set(lista["segmento"])
    assert len(orden) == len(set(orden)) == 300 and set(orden[:len(marcados)]) == marcados            # los marcados van primero y ningún segmento se repite
    resto = m[~m["seg"].isin(marcados) & ~m["sin_datos"]].groupby("seg")["tasa"].min()
    primeros = [resto[s] for s in orden[len(marcados):len(marcados) + 20] if s in resto.index]
    assert primeros == sorted(primeros)                                                               # entre los demás, de menor a mayor tasa mínima
    assert orden == orden_gravedad(m.sample(frac=1, random_state=1))                                   # determinista: no depende del orden de las filas


def test_los_botones_del_mapa_muestran_todo_con_pocos_segmentos_y_de_a_50_con_muchos() -> None:
    from waymo_evaluacion.ep3.app_logica import PASO_MAPA, rotulo_boton_mapa, siguiente_filas_mapa

    assert rotulo_boton_mapa(10, 41) == "Ver los 41 segmentos" and siguiente_filas_mapa(10, 41) == 41 and rotulo_boton_mapa(41, 41) == "Ver solo las primeras filas" and siguiente_filas_mapa(41, 41) == 10
    assert rotulo_boton_mapa(10, 300) == "Mostrar 50 más (10 de 300)"
    pasos, actual = [], 10
    while True:
        pasos.append(actual)
        actual = siguiente_filas_mapa(actual, 300)
        if actual == 10:
            break
    assert pasos == [10, 60, 110, 160, 210, 260, 300] and all(b - a <= PASO_MAPA for a, b in zip(pasos, pasos[1:]))      # nunca más de 50 filas nuevas por clic; al final, vuelve al inicio


def test_la_tabla_de_celdas_marcadas_es_unica_y_trae_las_columnas_de_la_referencia() -> None:
    from waymo_evaluacion.ep3.app_logica import celdas_marcadas_lista, tabla_celdas_auditoria
    from waymo_evaluacion.ep3.escala_sintetica import celdas_sinteticas

    _, lista = celdas_sinteticas(300)
    t = tabla_celdas_auditoria(celdas_marcadas_lista(lista))
    assert list(t.columns) == ["Segmento", "Cámara", "Cajas afectadas", "Sin pareja", "Cajas con par 2D (normal)", "Contexto"]
    assert t["Cajas afectadas"].is_monotonic_decreasing                                               # ordenadas por cajas afectadas
    assert t["Segmento"].str.fullmatch(r"…\d{6}").all() and t["Cámara"].str.fullmatch(r"\d · [a-zé. ]+").all() and t["Cajas con par 2D (normal)"].eq("0 % (normal 90 %)").all()


def test_el_umbral_del_desplegable_sale_de_los_datos() -> None:
    from waymo_evaluacion.ep3.app_logica import texto_umbral_hueco

    lista = pd.DataFrame({"umbral": [0.2284, 0.2284]})
    assert texto_umbral_hueco(lista, 0.25, 100) == "El umbral es el 25 % de lo normal de esa cámara, con al menos 100 cajas en el rango. En las celdas marcadas equivale a 23 % de pares 2D."
    assert "En la celda marcada" in texto_umbral_hueco(lista.head(1), 0.25, 100) or "la celda marcada" in texto_umbral_hueco(lista.head(1), 0.25, 100)


# ------------------------------------------------------------------------------------------------------------ la página
def test_la_auditoria_tiene_la_franja_el_titular_la_tabla_el_anillo_el_mapa_y_el_desplegable(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3 import app_logica as A

    at = _abrir(entorno, monkeypatch, "Auditoría de cámaras")
    t = _sin_css(textos(at)).replace(" ", " ")
    assert len(re.findall(r'class="aud-kpi(?: hueco)?"', t)) == 3 and 'class="aud-kpi hueco"' in t and "Celdas marcadas" in t and "Cajas afectadas" in t and "Sin pareja entre ellas" in t
    assert "posible hueco de cámara en los últimos datos sin revisar." in t and "Las cifras salen de los 2 segmentos de desarrollo." in t                                           # los datos de prueba traen 2 segmentos en las celdas
    assert A.AUD_AYUDA_TABLA in t and A.AUD_TITULO_ANILLO in t and A.AUD_TITULO_MAPA in t and A.AUD_AYUDA_MAPA in t and "Hueco: cámara que, en un segmento, tiene menos del 25 %" in t
    tabla = next(d.value for d in at.dataframe if "Cajas afectadas" in d.value.columns)
    assert list(tabla.columns)[:4] == ["Segmento", "Cámara", "Cajas afectadas", "Sin pareja"]
    assert [e.label for e in at.expander] == [A.AUD_QUE_ES] and "El umbral es el 25 %" in " ".join(m.value for m in at.expander[0].markdown)
    assert [s.label for s in at.selectbox if s.label != "Rol"] == ["Grupo de segmentos", "Orden"]       # F31: se quitaron los filtros «Segmento» y «Cámara»
    assert any(b.label == "Descargar CSV" for b in at.get("download_button")) if hasattr(at, "get") else True


def test_la_primera_fila_viene_elegida_y_el_anillo_marca_su_camara(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3 import app_logica as A

    at = _abrir(entorno, monkeypatch, "Auditoría de cámaras")
    t = textos(at)
    assert "Celda resaltada en el mapa: segmento …" in t and A.AUD_ORIGEN_FILA in t and A.AUD_ORIGEN_RESUMEN not in t
    assert t.count('class="cu hueco sel"') == 1 and "aria-label" in t                                    # la cámara de la fila elegida lleva el contorno claro
    assert "Un clic en otra fila" in t and not re.search(r"\b(elija|haga clic)\b", t, re.I)


def test_el_enlace_a_la_cola_esta_arriba(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3.app_logica import ENLACE_COLA_DESDE_AUDITORIA

    at = _abrir(entorno, monkeypatch, "Auditoría de cámaras")
    enlaces = [e for e in at.get("page_link")] if hasattr(at, "get") else []
    assert any(getattr(e.proto, "label", "") == ENLACE_COLA_DESDE_AUDITORIA for e in enlaces)


def test_con_300_segmentos_la_auditoria_carga_pronto_y_solo_dibuja_las_filas_visibles(entorno300: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3.app_logica import FILAS_MAPA_INICIO

    inicio = time.perf_counter()
    at = _abrir(entorno300, monkeypatch, "Auditoría de cámaras")
    segundos = time.perf_counter() - inicio
    assert not at.exception and segundos < 30, segundos                                                    # tiempo razonable (el valor medido va en el reporte)
    spec = [c.proto.spec for c in at.get("vega_lite_chart")]
    assert spec and sum(s.count('"seg":') for s in spec) <= FILAS_MAPA_INICIO * 5 * 1.0 + 0 or sum(s.count('"seg"') for s in spec) < 300 * 5
    assert re.search(r"Se ven 10 de 300 segmentos", textos(at)) and any(b.label == "Mostrar 50 más (10 de 300)" for b in at.button)
    at.button(key="mapa_mas").click().run()
    assert not at.exception and re.search(r"Se ven 60 de 300 segmentos", textos(at))
    tabla = next(d.value for d in at.dataframe if "Cajas afectadas" in d.value.columns)
    assert len(tabla) < 60                                                                                # las celdas marcadas son pocas frente a los segmentos


def test_el_resumen_y_la_auditoria_dan_las_mismas_cifras(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3 import app_logica as A

    D = A.cargar_datos(entorno / "datos")
    r = A.inicio_resumen(D)
    res = A.resumen_auditoria(A.matriz_calor(D["celdas"], 100), D["lista_A"])
    assert r["celdas_marcadas"] == res["celdas_marcadas"]
    at = _abrir(entorno, monkeypatch, "Resumen")
    assert f'<p class="va">{res["celdas_marcadas"]}</p>' in textos(at)                                      # «Cámaras con alerta» del Resumen = celdas marcadas de la Auditoría
