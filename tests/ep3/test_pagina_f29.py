"""F29: Resumen para uso diario (a partir de la referencia visual del usuario): indicadores, alertas de cámara con su anillo, cola de revisión con segmentos prioritarios, pie con la divulgación.
Cubre: la lógica (indicadores, cola determinista y sin filas idénticas, segmentos prioritarios, celdas marcadas), los textos como constantes, el orden de los bloques, lo que salió del Resumen
(cifras de apoyo, alertas duplicadas, impacto estimado fuera del modo presentación), los botones «Auditar» y «Abrir» con el contexto elegido y el modo presentación. Escribe solo en ``tmp_path``."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import pytest

from tests.ep3.test_app import textos
from tests.ep3.test_pagina_f24 import _abrir, _sin_css, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))


@pytest.fixture(scope="module")
def entorno2(entorno: Path, tmp_path_factory):
    """El entorno sintético con una segunda celda marcada (otro segmento y otra cámara), para probar la elección de fila."""
    import shutil

    base = tmp_path_factory.mktemp("f29b")
    shutil.copytree(entorno / "datos", base / "datos")
    shutil.copytree(entorno / "modelos", base / "modelos")
    la = pd.read_csv(base / "datos" / "lista_A.csv", dtype={"segmento": str})
    fila = la.iloc[[0]].copy()
    fila["segmento"], fila["camara"], fila["cajas_afectadas_poblacion_principal"] = "bbbbbbbbbbbb", "2 (frontal izq.)", 5
    pd.concat([la, fila], ignore_index=True).to_csv(base / "datos" / "lista_A.csv", index=False)
    return base


def _datos(entorno: Path):
    from waymo_evaluacion.ep3.app_logica import cargar_datos

    return cargar_datos(entorno / "datos")


# ------------------------------------------------------------------------------------------------------------ lógica
def test_los_indicadores_salen_de_los_datos_y_omiten_el_cambio_de_ayer_si_no_hay_corte(entorno: Path) -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    D = _datos(entorno)
    r = A.inicio_resumen(D)
    ind = A.indicadores_resumen(D, r, 1234)
    assert [i["clave"] for i in ind] == ["segmentos", "camaras", "cola", "prevalencia"]
    assert ind[0]["valor"] == str(A.segmentos_sin_revisar(D)) and ind[1]["valor"] == str(r["celdas_marcadas"]) and ind[2]["valor"] == "1.234"
    assert ind[1]["tono"] == ("hueco" if r["celdas_marcadas"] else "") and "ayer" not in " ".join(i["nota"] for i in ind)           # sin corte anterior no se inventa nada
    assert A.cambio_respecto_de_ayer(D) is None


def test_si_existe_un_corte_anterior_el_cambio_se_muestra(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    D = _datos(entorno)
    monkeypatch.setattr(A, "cambio_respecto_de_ayer", lambda d: 0.014)
    nota = A.indicadores_resumen(D, A.inicio_resumen(D), 10)[3]["nota"].replace("\xa0", " ")
    assert nota == "+1,4 puntos respecto de ayer"


def test_la_cola_prioritaria_es_la_misma_de_la_cola_en_un_orden_determinista_sin_filas_identicas(entorno: Path) -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    D = _datos(entorno)
    top, info = A.cola_segmento(D["cajas"], "Todos", A.PRESUPUESTO_VISTA_RESUMEN, "dos")
    t, total = A.cola_prioritaria(D["cajas"], {})
    assert total == info["cajas_cola_total"] and len(t) == len(top)                                                              # mismas cajas, mismo total
    clave = ["seg", "key.laser_object_id", "key.frame_timestamp_micros"]
    assert set(map(tuple, t[clave].to_numpy())) == set(map(tuple, top[clave].to_numpy()))
    esperado = top.sort_values(["prob_cal", "seg", "key.laser_object_id", "key.frame_timestamp_micros"], ascending=[False, True, True, True], kind="stable")
    assert list(t["key.laser_object_id"]) == list(esperado["key.laser_object_id"]) and list(t["prob_cal"]) == sorted(t["prob_cal"], reverse=True)
    assert not t.duplicated(["seg", "caja"]).any()                                                                                # ninguna fila idéntica
    otra, _ = A.cola_prioritaria(D["cajas"].sample(frac=1, random_state=3), {})
    assert list(otra["caja"]) == list(t["caja"])                                                                                  # el orden no depende del orden de los datos


def test_filtrar_y_segmentos_prioritarios(entorno: Path) -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    D = _datos(entorno)
    t, _ = A.cola_prioritaria(D["cajas"], A.cargar_rangos(R / "data/06_models_ep3") if (R / "data/06_models_ep3").exists() else {})
    assert len(A.filtrar_cola_resumen(t)) == len(t)
    solo = A.filtrar_cola_resumen(t, clase="Ciclista")
    assert set(solo["clase"]) <= {"Ciclista"} and list(solo.index) == sorted(solo.index)                                          # no cambia el orden
    seg = str(t["seg"].iloc[0])
    assert set(A.filtrar_cola_resumen(t, segmento=seg)["seg"]) == {seg}
    top = A.segmentos_prioritarios(t, n=3)
    assert len(top) <= 3 and [n for _, n in top] == sorted([n for _, n in top], reverse=True) and sum(n for _, n in A.segmentos_prioritarios(t, n=999)) == len(t)


def test_las_celdas_marcadas_van_con_mas_cajas_afectadas_primero_y_con_numero_y_nombre_de_camara() -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    la = pd.DataFrame({"segmento": ["111111111111", "222222222222"], "camara": ["5 (lateral der.)", "3 (frontal der.)"], "cajas_afectadas_poblacion_principal": [268, 1677]})
    f = A.celdas_marcadas_lista(la)
    assert [x["seg_corto"] for x in f] == ["222222", "111111"] and f[0]["camara_num"] == 3 and f[0]["camara_nombre"] == "frontal der." and f[0]["estado"] == "Hueco" and f[0]["cajas_afectadas"] == 1677


# ------------------------------------------------------------------------------------------------------------ textos y redacción
def test_los_textos_del_resumen_son_constantes_y_la_redaccion_es_prudente() -> None:
    from waymo_evaluacion.ep3 import app_logica as A

    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    for texto in (A.TITULAR_SIN_ALERTAS, A.ACCION_AUDITAR, A.SUBTITULO_COLA_RESUMEN, A.ENLACE_COLA, A.ACCION_ABRIR, A.ETIQUETA_CICLISTA,
                  A.NOTA_ORDEN_COLA, A.TITULO_SEGMENTOS_PRIORITARIOS, A.SUBTITULO_SEGMENTOS_PRIORITARIOS):
        assert (f'"{texto}"' if len(texto) < 12 else texto) not in fuente, texto                                                 # ningún texto del Resumen escrito a mano en la página
    assert "{huecos}" in A.TITULAR_ALERTAS and "{n}" in A.SUBTITULO_ALERTAS and A.TITULAR_SIN_ALERTAS == "Todas las cámaras sanas."
    assert f"### {{TITULO_COLA_RESUMEN}}" in fuente and A.TITULO_COLA_RESUMEN == "Cola de revisión"
    assert A.ACCION_AUDITAR == "Auditar" and A.ACCION_ABRIR == "Abrir"


def test_el_titular_dice_cuantos_huecos_y_en_cero_dice_todas_sanas() -> None:
    import secciones as S

    assert S._titular_alertas(2) == ('<p class="aud-titular">Hay <span class="alerta">2 posibles huecos de cámara</span> en los últimos datos sin revisar.</p>')
    assert "1 posible hueco de cámara" in S._titular_alertas(1) and "posibles" not in S._titular_alertas(1)
    assert S._titular_alertas(0) == '<p class="aud-titular">Todas las cámaras sanas.</p>'


# ------------------------------------------------------------------------------------------------------------ la página
def test_el_resumen_tiene_los_bloques_en_orden_y_lo_que_salio_ya_no_esta(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3 import app_logica as A

    at = _abrir(entorno, monkeypatch, "Resumen")
    t = _sin_css(textos(at))
    k = A.inicio_resumen(_datos(entorno))["celdas_marcadas"]
    assert len(re.findall(r'class="aud-kpi(?: hueco)?"', t)) == 4 and 'class="aud-kpi hueco"' in t                                                       # franja de 4 indicadores; «Cámaras con alerta» en rojo si hay alertas
    assert f'<span class="alerta">{k} ' in t and "en los últimos datos sin revisar" in t
    orden = [t.index(x) for x in ("aud-kpis", "Alertas de cámara", A.TITULO_COLA_RESUMEN, A.TITULO_SEGMENTOS_PRIORITARIOS)]
    assert orden == sorted(orden)
    for salio in ("Cifras de apoyo", "Impacto estimado", "Celdas marcadas.", "Ciclistas: regla poco confiable", "Validación externa pendiente.", "aud-afirmacion", "Datos de ejemplo", "mockup"):
        assert salio not in t, salio
    assert not re.search(r"\ben (la )?muestra\b", t) and not re.search(r"defectuos", t, re.I)                                   # sin «en muestra»; la hipótesis sigue siendo «posible hueco»
    assert "Hueco" in t and "cajas afectadas" in t                                                                               # el estado va en palabras, no solo en color
    assert at.title[0].value == "Estado de las cámaras"


def test_la_primera_fila_viene_elegida_y_elegir_otra_cambia_el_anillo(entorno2: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno2, monkeypatch, "Resumen")
    assert [b.key for b in at.button if b.key and b.key.startswith("sel_celda_")] == ["sel_celda_0", "sel_celda_1"]
    assert at.session_state["celda_resumen"] == 0 if "celda_resumen" in at.session_state else True                                # la primera fila viene elegida por defecto
    assert [b.proto.type for b in at.button if b.key in ("auditar_0", "auditar_1")] == ["primary", "secondary"]                          # solo la fila elegida lleva el botón destacado
    antes = re.search(r"Cámaras del segmento ([^<]*)<", _sin_css(textos(at))).group(1)
    at.button(key="sel_celda_1").click().run()
    assert not at.exception and at.session_state["celda_resumen"] == 1
    assert [b.proto.type for b in at.button if b.key in ("auditar_0", "auditar_1")] == ["secondary", "primary"]
    despues = re.search(r"Cámaras del segmento ([^<]*)<", _sin_css(textos(at))).group(1)
    assert antes != despues


def test_auditar_abre_la_auditoria_con_la_fila_de_esa_celda_elegida(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3 import app_logica as A

    at = _abrir(entorno, monkeypatch, "Resumen")
    celdas = A.celdas_marcadas_lista(_datos(entorno)["lista_A"])
    assert celdas, "los datos sintéticos traen al menos una celda marcada"
    at.button(key="auditar_0").click().run()
    assert not at.exception and at.title[0].value == "Auditoría de cámaras"
    assert at.session_state["aud_idx"] == 0 and at.session_state["aud_desde_resumen"] is True
    t = textos(at)
    assert "Celda resaltada en el mapa" in t and f"…{celdas[0]['segmento'][-6:]}" in t and A.AUD_ORIGEN_RESUMEN in t


def test_abrir_lleva_a_explica_una_caja_con_los_valores_de_esa_caja(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Resumen")
    if not any(b.key == "abrir_0" for b in at.button):
        pytest.skip("la cola de los datos sintéticos está vacía")
    at.button(key="abrir_0").click().run()
    assert not at.exception and at.title[0].value == "Explica una caja"
    t = textos(at)
    assert "Valores cargados desde el Resumen: caja " in t and "puntos del sensor superior" in t.lower()                      # F33: aviso de dónde vienen los valores
    assert at.radio(key="ex_clase").value in ("Peatón", "Ciclista")


def test_los_filtros_de_la_cola_filtran_y_el_vacio_dice_que_hacer(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Resumen")
    at.selectbox(key="res_clase").set_value("Ciclista").run()
    t = _sin_css(textos(at))
    assert not at.exception
    if 'class="aud-cola-fila"' in t:
        assert t.count("Regla poco confiable") == t.count('class="aud-cola-fila"') and "Peatón" not in t.split("Segmentos con más cajas")[0].split('class="aud-cola-fila cab"')[-1]
    else:
        assert "Ninguna caja cumple los filtros" in t


def test_las_filas_de_ciclista_llevan_la_etiqueta_con_punto_ambar_y_las_de_peaton_no() -> None:
    import estilos as E

    ciclista = E.cola_fila("1", "…123456", "AbCd-01", "1 (frontal)", "Ciclista", "87,8 %", "Regla poco confiable")
    peaton = E.cola_fila("2", "…123456", "AbCd-02", "1 (frontal)", "Peatón", "87,8 %")
    assert "Regla poco confiable" in ciclista and "aud-punto aviso" in ciclista and "etq" not in peaton and "Regla" not in peaton


def test_validacion_recibe_las_cifras_de_apoyo(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Validación")
    t = _sin_css(textos(at))
    assert "Cifras de apoyo" not in t and "Cajas analizadas" in t and "sin pareja" in t                                  # F34: las cifras de apoyo son las cuatro tarjetas de la cabecera (mismas fuentes)


def test_el_impacto_estimado_ya_no_esta_en_el_resumen(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Resumen")
    t = _sin_css(textos(at))
    assert "Impacto estimado" not in t and "Estimación:" not in t and "Informe técnico de EP3" not in t                              # F30: pasó a Validación › En muestra (ver test_pagina_f30.py)


def test_el_pie_del_resumen_conserva_la_atribucion_y_la_version(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    from waymo_evaluacion.ep3.app_logica import ATRIBUCION_WAYMO

    t = _sin_css(textos(_abrir(entorno, monkeypatch, "Resumen")))
    assert ATRIBUCION_WAYMO in t and "Solución v3 congelada" in t and "Datos de desarrollo" in t                                    # F30: el pie global sigue; la línea de validación pendiente salió del Resumen


def test_el_rol_ya_no_ordena_alertas_y_el_menu_ya_no_lo_promete() -> None:
    from waymo_evaluacion.ep3.app_logica import PERFILES

    assert all(set(p) == {"pregunta", "seccion", "mensaje"} for p in PERFILES.values())
    assert "ordena primero" not in (R / "app" / "app.py").read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------------------------------ estilo
def test_el_estilo_del_resumen_respeta_la_piel_oscura_y_sus_reglas() -> None:
    import estilos as E

    css = E.css()
    assert "font-weight: 700" not in css and "999px" not in css and not re.search(r"#[0-9A-Fa-f]{6}", css[css.index("F29: Resumen para uso diario"):css.index("F29: Resumen para uso diario") + 6000].split("[data-testid=\"stFileUploader")[0])   # sin hex sueltos: todo sale de los tokens
    assert "grid-template-columns: repeat(var(--n, 4), minmax(0, 1fr))" in css and ".aud-kpi.hueco { background: var(--hueco-fondo); border-color: var(--hueco); }" in css
    assert "aud-afirmacion" not in css and "aud-etapa" not in css and "aud-apoyo" not in css and "aud-camaras" not in css            # el CSS de lo que salió no queda
    assert E.TAMANO_TITULAR == "1.75rem"
