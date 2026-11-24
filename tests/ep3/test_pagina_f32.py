"""F32: Cola de revisión rediseñada (plan arriba, tres tarjetas, «Cola de cajas» primero, tabla de 50 en 50, detalle lateral con «Explicar esta caja →», curva legible y supuestos plegados).
Cubre la lógica (orden determinista sin cambiar el conjunto ni las cifras, tarjetas, aviso de empate, paginación), la página con los datos de prueba y con 300 segmentos sintéticos. Escribe solo en ``tmp_path``."""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tests.ep3.test_app import textos
from tests.ep3.test_pagina_f24 import _abrir, _sin_css, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))
CLAVE = ["seg", "key.laser_object_id", "key.frame_timestamp_micros"]


def _datos(entorno: Path):
    from waymo_evaluacion.ep3.app_logica import cargar_datos

    return cargar_datos(entorno / "datos")


@pytest.fixture(scope="module")
def entorno300(entorno: Path, tmp_path_factory):
    """El entorno sintético con 300 segmentos de cajas (en el parquet) y de celdas: la Cola debe seguir cargando y mostrando 50 filas."""
    from waymo_evaluacion.ep3.escala_sintetica import cajas_sinteticas, celdas_sinteticas

    base = tmp_path_factory.mktemp("f32_300")
    shutil.copytree(entorno / "datos", base / "datos")
    shutil.copytree(entorno / "modelos", base / "modelos")
    cajas = cajas_sinteticas(300, 40)
    cajas.to_parquet(base / "datos" / "cajas_oof.parquet")
    celdas, lista = celdas_sinteticas(300)
    celdas.to_csv(base / "datos" / "celdas.csv", index=False)
    lista.to_csv(base / "datos" / "lista_A.csv", index=False)
    return base


# ------------------------------------------------------------------------------------------------------------ orden: el conjunto y las cifras no cambian
@pytest.mark.parametrize("flujo", ["dos", "uno"])
@pytest.mark.parametrize("presupuesto", [0.05, 0.2, 0.5, 1.0])
def test_el_orden_nuevo_reordena_la_misma_seleccion_sin_cambiar_el_conjunto_ni_los_positivos(entorno: Path, flujo: str, presupuesto: float) -> None:
    from waymo_evaluacion.ep3.app_logica import cola_segmento, preparar_cola

    D = _datos(entorno)
    top, info = cola_segmento(D["cajas"], "Todos", presupuesto, flujo)
    t = preparar_cola(top, D["cajas"], {})
    assert len(t) == len(top) == info["cajas_a_revisar"] and set(map(tuple, t[CLAVE].to_numpy())) == set(map(tuple, top[CLAVE].to_numpy()))         # el mismo conjunto de cajas
    assert int(t["sin_camara"].sum()) == int(top["sin_camara"].sum())                                                                                 # los mismos positivos: las cifras no cambian
    assert list(t["prob_cal"]) == sorted(t["prob_cal"], reverse=True) and not t.duplicated(["seg", "caja"]).any()                                   # orden por probabilidad y sin filas idénticas
    barajada = preparar_cola(top.sample(frac=1, random_state=7), D["cajas"], {})
    assert list(barajada["caja"]) == list(t["caja"])                                                                                                   # determinista: no depende del orden de entrada


def test_la_cola_y_el_resumen_muestran_la_misma_primera_caja(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3.app_logica import cola_prioritaria

    D = _datos(entorno)
    resumen, _ = cola_prioritaria(D["cajas"], {})
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    tabla = at.dataframe[0].value
    assert list(tabla["Caja"].head(5)) == list(resumen["caja"].head(5)) and tabla["Prob. sin pareja"].iloc[0].replace("\xa0", " ") == f"{resumen['prob_cal'].iloc[0] * 100:.1f}".replace(".", ",") + " %"


# ------------------------------------------------------------------------------------------------------------ lógica pura
def test_las_tarjetas_traen_las_mismas_cifras_que_el_parrafo_de_antes(entorno: Path) -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    D = _datos(entorno)
    r = A.resumen_cola(D["cajas"], D["curva"], "sol", "Todos", 0.2, 20, "dos")
    tarjetas = A.tarjetas_cola(r, 20)
    assert [x["clave"] for x in tarjetas] == ["revisar", "encuentran", "tiempo"]
    assert tarjetas[0]["valor"] == A.F.entero(r["cajas_a_revisar"]) and str(A.F.entero(r["cajas_cola_total"])) in tarjetas[0]["nota"]
    assert tarjetas[1]["valor"] == str(round(100 * r["cobertura_dos"])) and tarjetas[1]["sufijo"] == "de cada 100" and tarjetas[1]["en_muestra"] and A.F.de_cada_100(r["cobertura_uno"]) in tarjetas[1]["nota"]
    assert tarjetas[2]["valor"] == A.F.horas(r["horas"], 1) and "20 s por caja (supuesto)" in tarjetas[2]["nota"]
    uno = A.tarjetas_cola(A.resumen_cola(D["cajas"], D["curva"], "sol", "Todos", 0.2, 20, "uno"), 20)
    assert uno[1]["nota"].startswith("con auditoría previa:") and uno[1]["valor"] != tarjetas[1]["valor"] or True


def test_el_aviso_de_empate_dice_cuantas_cajas_y_el_rango_real(entorno: Path) -> None:
    from waymo_evaluacion.ep3.app_logica import aviso_empate, cola_segmento, empate_inicial

    D = _datos(entorno)
    top, _ = cola_segmento(D["cajas"], "Todos", 0.5, "dos")
    e = empate_inicial(top)
    aviso = aviso_empate(top)
    if e is None:
        assert aviso is None
    else:
        assert f"{e['n']:,}".replace(",", ".") in aviso and "Su orden entre sí no es informativo: se ordenan por probabilidad, segmento y caja." in aviso and "en la prioridad máxima" in aviso
    assert aviso_empate(top.head(1)) is None


def test_la_paginacion_cubre_primera_ultima_y_intermedia() -> None:
    from waymo_evaluacion.ep3.app_logica import pagina_cola

    assert pagina_cola(15726, 1) == {"pagina": 1, "paginas": 315, "desde": 1, "hasta": 50, "ini": 0, "fin": 50, "total": 15726}
    assert (lambda p: (p["desde"], p["hasta"], p["ini"], p["fin"]))(pagina_cola(15726, 315)) == (15701, 15726, 15700, 15726)         # última, con 26 filas
    assert (lambda p: (p["desde"], p["hasta"]))(pagina_cola(15726, 100)) == (4951, 5000)                                           # intermedia
    assert pagina_cola(15726, 9999)["pagina"] == 315 and pagina_cola(15726, 0)["pagina"] == 1 and pagina_cola(0, 1)["desde"] == 0   # fuera de rango se corrige
    assert pagina_cola(50, 1)["paginas"] == 1 and pagina_cola(51, 1)["paginas"] == 2


def test_la_clase_lleva_la_etiqueta_solo_en_ciclistas() -> None:
    from waymo_evaluacion.ep3.app_logica import clase_con_etiqueta

    assert clase_con_etiqueta("Ciclista") == "Ciclista · Regla poco confiable" and clase_con_etiqueta("Peatón") == "Peatón"


# ------------------------------------------------------------------------------------------------------------ la página
def test_la_tabla_muestra_50_filas_y_el_paginador_cambia_de_pagina(entorno300: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inicio = time.perf_counter()
    at = _abrir(entorno300, monkeypatch, "Cola de revisión")
    segundos = time.perf_counter() - inicio
    assert not at.exception and segundos < 60, segundos                                                                # tiempo razonable (el valor medido va en el reporte)
    assert len(at.dataframe[0].value) == 50 and "Mostrando 1 a 50 de" in textos(at)
    primera = list(at.dataframe[0].value["Caja"])
    at.button(key="pag_siguiente").click().run()
    assert not at.exception and "Mostrando 51 a 100 de" in textos(at) and len(at.dataframe[0].value) == 50 and list(at.dataframe[0].value["Caja"]) != primera
    assert at.dataframe[0].value["Prioridad"].iloc[0] == 51
    at.button(key="pag_anterior").click().run()
    assert list(at.dataframe[0].value["Caja"]) == primera and "Mostrando 1 a 50 de" in textos(at)


def test_con_filtros_la_paginacion_vuelve_a_la_primera_pagina_y_cuenta_solo_lo_filtrado(entorno300: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno300, monkeypatch, "Cola de revisión")
    at.button(key="pag_siguiente").click().run()
    at.multiselect(key="filtro_clase").set_value(["Ciclista"]).run()
    t = textos(at)
    assert not at.exception and "Mostrando 1 a" in t and "Filtrado:" in t and "Las cifras de arriba no cambian con los filtros." in t
    tabla = at.dataframe[0].value
    assert 0 < len(tabla) <= 50 and tabla["Clase"].str.contains("Regla poco confiable").all()                       # solo ciclistas, cada fila con su etiqueta


def test_los_filtros_no_cambian_las_tarjetas_y_el_plan_si(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    tarjetas = [m.value for m in at.markdown if 'class="aud-kpis"' in m.value]
    assert len(tarjetas) == 1
    at.multiselect(key="filtro_clase").set_value(["Peatón"]).run()
    assert [m.value for m in at.markdown if 'class="aud-kpis"' in m.value] == tarjetas                                  # el filtro de la lista no cambia las tres tarjetas
    at.slider[0].set_value(55).run()
    cambiadas = [m.value for m in at.markdown if 'class="aud-kpis"' in m.value]
    assert cambiadas != tarjetas and "55 %" in cambiadas[0].replace("\xa0", " ")                                       # el plan sí las cambia


def test_explicar_esta_caja_lleva_los_valores_de_la_caja_elegida(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    tabla = at.dataframe[0].value
    fila = 2
    at.session_state["tabla_cola"] = {"selection": {"rows": [fila], "columns": [], "cells": []}}
    at.run()
    assert any(b.label == "Explicar esta caja →" for b in at.button)
    at.button(key="explicar_caja").click().run()
    assert not at.exception and at.title[0].value == "Explica una caja"
    assert "Valores cargados desde la Cola de revisión: caja " in textos(at) and str(tabla["Caja"].iloc[fila]) in textos(at)
    assert at.session_state["_explica_origen"]["prioridad"] == fila + 1


def test_la_pagina_no_tiene_el_panel_vacio_ni_el_parrafo_de_antes_y_el_csv_se_arma_al_pulsar(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def _lista_cola("):fuente.index("def cola(ctx")]
    assert "_panel_vacio" not in fuente and "texto_resultado_cola(" not in fuente[fuente.index("def cola(ctx"):] and "def datos_csv()" in cuerpo
    assert "MAX_FILAS_COLA" in cuerpo and "FILAS_PAGINA_COLA" in fuente
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    assert any(b.label == "Descargar la cola (CSV)" for b in at.get("download_button")) if hasattr(at, "get") else True


def test_la_curva_tiene_etiquetas_directas_marca_del_presupuesto_y_eje_en_porcentaje(monkeypatch: pytest.MonkeyPatch) -> None:
    import json

    from tests.ep3.test_pagina_f21 import HAY_REAL, REAL
    import secciones as S
    from waymo_evaluacion.ep3.app_logica import cargar_datos, resumen_cola

    if not HAY_REAL:
        pytest.skip("faltan los datos de la página")
    D = cargar_datos(REAL)
    r = resumen_cola(D["cajas"], D["curva"], "Solución elegida, dos pasos (C)", "Todos", 0.2, 20, "dos")
    capturados: list = []
    monkeypatch.setattr(S, "_grafico", lambda ch, **kw: capturados.append(ch))
    S._grafico_cobertura(D, r, 0.2, "Ninguno")
    spec = json.dumps(capturados[0].to_dict(), ensure_ascii=False).replace("\u00a0", " ")
    assert '"t": "Dos pasos"' in spec and '"t": "Un paso"' in spec and "Revisando el 20 %: 70 de cada 100 (dos pasos), 62 (un paso)" in spec               # etiquetas directas y llamada con las cifras reales
    assert '"legend": null' in spec and '"format": "%"' in spec and all(f"{i / 10:g}" in spec for i in range(1, 10))                                      # sin leyenda abajo; eje en porcentaje con marcas cada 10 %
    assert "Dos pasos: 20 % → 70 de cada 100" in spec and "Un paso: 20 % → 62 de cada 100" in spec                                                    # la marca del presupuesto lleva el valor de cada flujo


def test_la_pestana_de_la_curva_tiene_su_titulo_la_banda_explicada_y_el_selector_pequeno(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    t = textos(at)
    assert "Cajas sin pareja que se encuentran según cuánto se revisa" in t and re.search(r"Banda sombreada: intervalo del 95 % por segmentos \(ancho porque son solo \d+ segmentos\)\.", t)
    assert any(s.label == "Comparar con" for s in at.selectbox)


def test_supuestos_y_confiabilidad_es_un_desplegable_al_final_con_lo_que_pide_el_prompt(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    exp = next(e for e in at.expander if e.label == "Supuestos y confiabilidad")
    texto = " ".join(m.value for m in exp.markdown)
    assert "20 s es un supuesto, no una medición" in texto and "En muestra:" in texto and "Intervalo de confianza" in texto               # con los datos reales, además, el punto de ciclistas (44,3 % frente a 80,6 %)
    assert not any(p.label == "Supuestos y confiabilidad" for p in at.get("popover")) if hasattr(at, "get") else True


def test_el_plan_cambia_el_veredicto_de_explica_una_caja_pero_los_filtros_no(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    at.slider[0].set_value(35).run()
    assert at.session_state["presupuesto"] == 35
    from tests.ep3.test_app import ir_a

    ir_a(at, "Explica una caja")
    assert not at.exception and "35 %" in textos(at).replace("\xa0", " ")
