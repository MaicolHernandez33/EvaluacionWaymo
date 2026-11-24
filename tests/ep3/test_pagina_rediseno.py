"""Pruebas del rediseño de la página (F18-C): formato es-CL, control inverso, textos, fuente única de cifras, regresión de cifras, estilos y seguridad de contenido."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.app_logica import (
    COLUMNA_FOTOGRAMAS, GLOSARIO, PERFILES, ATRIBUCION_WAYMO, SECCIONES, TITULO_RESUMEN, cargar_datos, camara_de_azimut, curva_inversa, datos_ciclistas, formatear_kpi, nombre_curva_legible, preguntas_frecuentes, recall_en_presupuesto,
    resumen_cola, tabla_cola, texto_resultado_cola, validar_asociacion, validar_lidar_box,
)
from tests.ep3.test_app import _datos_sinteticos, _modelos_sinteticos, ir_a, textos

R = Path(__file__).resolve().parents[2]
REAL = R / "data/09_app_ep3"
ANTES = R / "data/08_reporting_ep3/pagina_numeros_antes.json"
sys.path.insert(0, str(R / "app"))


# ------------------------------------------------------------------------------------------------------------ formato es-CL
def test_formatos_es_cl() -> None:
    assert F.entero(80571) == "80.571" and F.entero(999) == "999" and F.entero(1234567) == "1.234.567"
    assert F.decimal(87.4) == "87,4" and F.decimal(1234.567, 2) == "1.234,57" and F.decimal(-50, 3) == "-50,000"
    assert F.porcentaje(0.7034) == "70,3 %" and F.porcentaje(0.2, 0) == "20 %" and F.porcentaje_valor(12.4) == "12,4 %"
    assert F.horas(87.37) == "87,4 h" and F.de_cada_100(0.7034) == "70 de cada 100"
    assert F.entero(float("nan")) == "—" and F.porcentaje(None) == "—" and F.decimal("x") == "—"
    assert formatear_kpi("6059 cajas") == "6.059 cajas" and formatear_kpi("IC 0,725 a 0,900") == "IC 0,725 a 0,900"


def test_nombres_legibles_sin_snake_case() -> None:
    df = pd.DataFrame({"tasa_sin_camara": [0.2123], "AUC_min_fold": [0.65], "cajas_en_celdas_con_hueco": [1945], "es_estable": [True], "modelo": ["XGB"], "dif_AUC_lo": [-0.1]})
    out = F.tabla_legible(df)
    assert not any("_" in c for c in out.columns), list(out.columns)
    assert out.iloc[0, 0] == "21,2 %" and out["Cajas en celdas con hueco"].iloc[0] == "1.945" and out["Es estable"].iloc[0] == "sí"


# ------------------------------------------------------------------------------------------------------------ lógica de la cola
def _curva_sintetica() -> pd.DataFrame:
    g = np.round(np.arange(0.01, 1.0001, 0.01), 2)
    return pd.DataFrame({"solucion": "sol", "presupuesto": g, "recall": np.sqrt(g), "lo": np.sqrt(g) - 0.05, "hi": np.minimum(np.sqrt(g) + 0.05, 1)})


def test_control_inverso_es_consistente_con_la_curva() -> None:
    c = _curva_sintetica()
    for objetivo in (0.2, 0.5, 0.8, 0.95):
        presup = curva_inversa(c, "sol", objetivo)
        assert recall_en_presupuesto(c, "sol", presup)["recall"] == pytest.approx(objetivo, abs=2e-3)   # ida y vuelta sobre la misma curva
    assert curva_inversa(c, "sol", 0.0001) == pytest.approx(0.01) and curva_inversa(c, "sol", 1.5) == pytest.approx(1.0)
    assert curva_inversa(c, "sol", 0.9) > curva_inversa(c, "sol", 0.8) > curva_inversa(c, "sol", 0.5)   # más meta, más revisión
    with pytest.raises(KeyError):
        curva_inversa(c, "otra", 0.5)


def test_textos_distintos_para_todos_y_un_segmento(tmp_path: Path) -> None:
    _datos_sinteticos(tmp_path / "d")
    d = cargar_datos(tmp_path / "d")
    todos = resumen_cola(d["cajas"], d["curva"], "sol", "Todos", 0.2, 20)
    uno = resumen_cola(d["cajas"], d["curva"], "sol", "aaaaaaaaaaaa", 0.2, 20)
    tt, tu = texto_resultado_cola(todos), texto_resultado_cola(uno)
    assert todos["todos"] and not uno["todos"] and tt != tu
    assert "Con auditoría previa (en muestra)" in tt and "Solo cola" in tt and "en los 3 segmentos" in tt and "no hay intervalo de confianza" not in tt          # F20-P4b: SIEMPRE ambos flujos
    assert "En el segmento aaaaaaaaaaaa" in tu and "no hay intervalo de confianza por segmentos" in tu and "en los" not in tu.split("(")[0]
    assert np.isnan(uno["ic_lo"]) and not np.isnan(todos["ic_lo"])


def test_fuente_unica_de_la_cobertura(tmp_path: Path) -> None:
    """La frase principal y la cobertura salen del mismo valor (el conteo observado); ya no hay tarjeta con la curva interpolada y texto con otro valor."""
    _datos_sinteticos(tmp_path / "d")
    d = cargar_datos(tmp_path / "d")
    for presup in (0.2, 0.68):
        r = resumen_cola(d["cajas"], d["curva"], "sol", "Todos", presup, 20)
        assert r["cobertura"] == pytest.approx(r["hallados"] / r["positivos_total"])
        assert F.de_cada_100(r["cobertura"]) in texto_resultado_cola(r) and F.de_cada_100(r["cobertura_uno"]) in texto_resultado_cola(r)


def test_tabla_de_la_cola_lleva_identificadores_y_avisa_de_ciclistas(tmp_path: Path) -> None:
    _datos_sinteticos(tmp_path / "d")
    d = cargar_datos(tmp_path / "d")
    top = d["cajas"].head(5).assign(es_ciclista=[1, 0, 0, 0, 0], az_signed=[0.0, 30.0, -40.0, 90.0, 150.0])
    rg = {1: (-20.0, 20.0), 2: (20.4, 63.0), 3: (-60.0, -19.5)}
    con = tabla_cola(top, 100, rg)
    assert {"Segmento", "Marca de tiempo", "Identificador de objeto"} <= set(con.columns) and COLUMNA_FOTOGRAMAS in con.columns
    assert con["Clase"].iloc[0].startswith("Ciclista") and con["Clase"].iloc[1] == "Peatón"
    assert con["Cámara"].tolist() == ["1 (frontal)", "2 (frontal izq.)", "3 (frontal der.)", "—", "—"]
    assert "Prioridad" not in con.columns and con["Prob. sin pareja"].iloc[0] == "30,0 %"          # F20-P4e: la probabilidad calibrada reemplaza a la barra «Prioridad» saturada en 100
    assert not any("_" in c for c in con.columns)


def test_camara_de_azimut_elige_el_centro_mas_cercano_en_los_solapes() -> None:
    rg = {1: (-21.0, 20.0), 3: (-60.5, -19.5)}
    s = camara_de_azimut(pd.Series([-20.0, -10.0, -50.0]), rg)
    assert s.tolist() == ["1 (frontal)", "1 (frontal)", "3 (frontal der.)"]   # -20: dentro de ambas; centro de la 1 a 19,5 y de la 3 a 20,0


def test_validaciones_amigables_de_archivos() -> None:
    assert "faltan las columnas" in validar_lidar_box(pd.DataFrame({"a": [1]}))
    assert validar_lidar_box(pd.DataFrame({c: [1] for c in ["[LiDARBoxComponent].box.center.x", "box.center.y", "box.size.x", "num_lidar_points_in_box", "num_top_lidar_points_in_box", "box.heading",
                                                           "key.segment_context_name", "key.frame_timestamp_micros", "key.laser_object_id"]})) is None
    assert "camera_to_lidar_box_association" in validar_asociacion(pd.DataFrame({"x": [1]}))


def test_textos_de_ayuda_y_ciclistas() -> None:
    eq = pd.DataFrame({"grupo": ["CYCLIST", "PEDESTRIAN"], "celdas_con_hueco": ["incluidas"] * 2, "recall_A": [0.4435, 0.806], "positivos": [115, 16987], "segmentos": [14, 40]})
    c = datos_ciclistas(eq)
    assert c["positivos"] == 115 and c["segmentos"] == 14
    assert "115 casos en 14 segmentos" in dict(preguntas_frecuentes(eq))["¿Qué pasa con los ciclistas?"]
    assert len(preguntas_frecuentes()) == 5 and {t for t, _ in GLOSARIO} >= {"Caja", "Par 2D", "Celda", "Hueco", "Cola", "Presupuesto", "Cobertura", "Intervalo de confianza", "Post hoc", "En muestra", "Sin prueba ciega"}
    assert nombre_curva_legible("Solución elegida, dos pasos (C)").startswith("Dos pasos") and len(SECCIONES) == 8 and SECCIONES[0] == "Resumen" and "Validación" in SECCIONES


# ------------------------------------------------------------------------------------------------------------ humo: 8 secciones x 3 perfiles x modo presentación
@pytest.fixture(scope="module")
def entorno(tmp_path_factory):
    base = tmp_path_factory.mktemp("pagina")
    _datos_sinteticos(base / "datos")
    _modelos_sinteticos(base / "modelos")
    return base


@pytest.mark.parametrize("perfil", list(PERFILES))
def test_humo_8_secciones_x_3_perfiles(entorno: Path, monkeypatch: pytest.MonkeyPatch, perfil: str) -> None:
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.setenv("WAYMO_APP_DATA", str(entorno / "datos"))
    monkeypatch.setenv("WAYMO_APP_MODELOS", str(entorno / "modelos"))
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=60).run()
    at.sidebar.selectbox[0].set_value(perfil).run()                                   # el rol está al pie de la barra lateral
    esperada = TITULO_RESUMEN if perfil == list(PERFILES)[0] else PERFILES[perfil]["seccion"]          # el rol por defecto ya está en la página de inicio (Resumen)
    assert at.title[0].value == esperada                                              # cambiar de rol lleva a la página que ese rol sugiere
    for s in SECCIONES:
        ir_a(at, s)
        assert not at.exception, (perfil, s, at.exception)
        assert at.title[0].value == (TITULO_RESUMEN if s == "Resumen" else s)
        assert not at.warning, (perfil, s)                                             # sin banners ámbar por pantalla
        assert ATRIBUCION_WAYMO in textos(at) and "Datos de desarrollo, sin validación externa" not in textos(at), (perfil, s)                  # F26: el pie lleva la atribución en todas las vistas y ya no hay chip


def test_la_tabla_de_la_cola_de_la_pagina_no_lleva_identificadores_pero_el_csv_si(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.setenv("WAYMO_APP_DATA", str(entorno / "datos"))
    monkeypatch.setenv("WAYMO_APP_MODELOS", str(entorno / "modelos"))
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=60).run()
    ir_a(at, "Cola de revisión")
    assert len(at.dataframe[0].value.columns) == 7 and not (set(at.dataframe[0].value.columns) & {"Marca de tiempo", "Identificador de objeto"})         # F32: el segmento va abreviado (…123456); la marca de tiempo y el identificador completo van en el CSV
    from waymo_evaluacion.ep3.app_logica import cargar_datos, resumen_cola, tabla_cola

    d = cargar_datos(entorno / "datos")
    r = resumen_cola(d["cajas"], d["curva"], "sol", "Todos", 0.2, 20)
    assert {"Segmento", "Marca de tiempo", "Identificador de objeto"} <= set(tabla_cola(r["top"], r["cajas_cola_total"], {}).columns)       # el CSV los lleva siempre (F30: ya no hay modo que los oculte)


def test_cola_control_inverso_y_boton_volver_al_20(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.setenv("WAYMO_APP_DATA", str(entorno / "datos"))
    monkeypatch.setenv("WAYMO_APP_MODELOS", str(entorno / "modelos"))
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=60).run()
    ir_a(at, "Cola de revisión")
    assert at.slider[0].value == 20                                                   # el presupuesto parte en 20 %
    at.slider[0].set_value(55).run()
    assert at.slider[0].value == 55
    next(b for b in at.button if b.label == "Volver al 20 %").click().run()
    assert at.slider[0].value == 20
    at.radio[0].set_value("Meta").run()
    assert at.slider[0].label.startswith("Meta")
    assert any("Para encontrar" in c.value for c in at.caption) and "de cada 100" in " ".join(m.value for m in at.markdown if 'class="aud-kpis"' in m.value)


# ------------------------------------------------------------------------------------------------------------ regresión de cifras contra pagina_numeros_antes.json
@pytest.mark.skipif(not (REAL / "kpis.json").exists() or not ANTES.exists(), reason="faltan los datos de la página o pagina_numeros_antes.json")
def test_las_cifras_no_cambian_salvo_el_redondeo_unificado(monkeypatch: pytest.MonkeyPatch) -> None:
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.delenv("WAYMO_APP_DATA", raising=False)
    monkeypatch.delenv("WAYMO_APP_MODELOS", raising=False)
    antes = json.loads(ANTES.read_text(encoding="utf-8"))["secciones"]

    def abrir(s: str):
        a = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=180).run()
        ir_a(a, s)
        assert not a.exception
        return a

    def texto(a) -> str:
        return " ".join(re.sub(r"<[^>]+>", " ", m.value) for m in a.markdown)

    # las 5 cifras de siempre (antes en «Resultados técnicos» de Inicio) siguen visibles, ahora en la pestaña Selección de Validación (con separador de miles es-CL)
    val = abrir("Validación")
    celdas = " ".join(" ".join(map(str, d.value.to_numpy().ravel())) for d in val.dataframe) + " " + " ".join(re.sub(r"<[^>]+>", " ", m.value) for m in val.markdown)       # F34: las tablas son HTML
    celdas = celdas.replace("\xa0", " ")
    for t in antes["Inicio"]["tarjetas"]:
        assert formatear_kpi(t["valor"]) in celdas, t
    # el Resumen muestra las cifras del titular nuevo, leídas de su origen (ie12__brazo_C_y_equilibrio): 358 h sin orden, 200 h un paso, 132 h dos pasos
    res = texto(abrir("Resumen")).replace("\xa0", " ").replace("**", "")
    assert "21,2" in res and "78.626" in res, res[-1500:]                                                    # F29: los indicadores (la cola de 78.626 cajas y el 21,2 % sin pareja)
    horas = texto(val).replace("\xa0", " ").replace("**", "")
    assert "≈ 358 h" in horas and "≈ 200 h" in horas and "≈ 132 h" in horas, horas[-1500:]                    # F30: las horas (impacto estimado) están en Validación › En muestra, con las mismas cifras
    assert "80.571" in " ".join(" ".join(map(str, d.value.to_numpy().ravel())) for d in val.dataframe) or "80.571" in texto(val).replace("\xa0", " ")        # F29: «Cajas analizadas» pasó a Validación
    # Cola: cajas y horas idénticas; hallados idénticos; la cobertura pasa a una sola fuente (observada) y la tarjeta antigua difiere en <= 0,1 punto
    for clave, presup in (("presupuesto_20", 20), ("presupuesto_68", 68)):
        a = abrir("Cola de revisión")
        a.slider[0].set_value(presup).run()
        txt = " ".join(texto(a).split())                                                   # F32: «70 de cada 100» queda en una tarjeta con la cifra y su unidad en elementos distintos
        old = antes["Cola de revisión"][clave]
        assert old["metricas"]["Cajas a revisar en este segmento"] in txt
        assert old["metricas"]["Horas con 20 s por caja"] + " h" in txt                  # el flujo por defecto sigue siendo el de dos pasos: mismas cajas y horas
        tarjeta_vieja = float(old["metricas"]["Recall esperado (todos los segmentos)"].replace(" %", "").replace(",", "."))
        texto_viejo = float(old["recall_texto"].replace(" %", "").replace(",", "."))
        assert abs(tarjeta_vieja - texto_viejo) <= 0.1 + 1e-9                           # la inconsistencia que se unificó
        assert f"{round(texto_viejo)} de cada 100" in txt or f"{int(texto_viejo)} de cada 100" in txt
        assert len(a.dataframe[0].value) == min(50, old["filas_tabla"])                   # F32: la tabla se pagina de a 50 (antes mostraba hasta 500 con desplazamiento interno)
    # Auditoría y Evidencia: mismas filas / tablas
    aud = abrir("Auditoría de cámaras")
    assert len(aud.dataframe[0].value) == antes["Auditoría de cámaras"]["tablas"][0]["filas"]                  # F31: las mismas filas (2 celdas marcadas) en la única tabla de celdas marcadas
    from collections import Counter

    pies = re.findall(r'class="tstd-pie">([^<]*)<', " ".join(m.value for m in val.markdown))                                    # F34: cada tabla HTML trae su conteo de filas («N filas» o «Filas 1 a 25 de N»)

    def n_filas(pie: str) -> int:
        m = re.search(r"de ([\d.]+)", pie) if pie.startswith("Filas") else re.match(r"([\d.]+) fila", pie)
        return int(m.group(1).replace(".", ""))

    filas_val = Counter(n_filas(p) for p in pies)
    faltan = Counter(antes["Evidencia"]["filas_por_tabla"]) - filas_val
    assert set(faltan) <= {175}                                                                    # las tablas de antes siguen con las mismas filas; solo «Curvas de validación» (175 filas) salió de pantalla y queda en la descarga CSV
    assert len(pies) >= antes["Evidencia"]["tablas"] - 1                                           # F34: 25 tablas de evidencia en pantalla (la 26.ª, las curvas, solo en la descarga) más candidatos, resultados y variantes
    # Explica una caja con los valores por defecto: puntaje, lugar en la cola y probabilidad idénticos
    ex = abrir("Explica una caja")
    t = texto(ex) + " " + " ".join(e.value for e in ex.markdown) + " " + " ".join(c.value for c in ex.caption)
    m = antes["Explica una caja"]["metricas"]
    assert m["Probabilidad calibrada de no tener pareja"].replace("\xa0", " ") in t.replace("\xa0", " ") and "El 59 % de las cajas de la cola queda antes que esta" in t.replace("\xa0", " ") and "2 · Puntaje" in t                      # antes: «entre el 59 % primero» (el mismo 59 %)
    assert m["Puntaje"].replace("-", "") .replace(",000", "") in t or m["Puntaje"] in t


# ------------------------------------------------------------------------------------------------------------ estilos y contenido seguro
def test_tokens_cumplen_contraste_y_coinciden_con_el_tema() -> None:
    import estilos as E

    for fg, bg in E.PARES_CONTRASTE:
        assert E.contraste(E.TOKENS[fg], E.TOKENS[bg]) >= 4.5, (fg, bg)
    for ruta in (R / ".streamlit/config.toml", R / "app/.streamlit/config.toml"):
        t = ruta.read_text(encoding="utf-8")
        for clave, token in (("primaryColor", "acento"), ("backgroundColor", "fondo"), ("secondaryBackgroundColor", "panel_alto"), ("textColor", "texto")):
            assert f'{clave} = "{E.TOKENS[token]}"' in t, (ruta.name, clave)
        assert "[theme]" in t and 'base = "dark"' in t and ('font = "sans serif"' in t or 'font = "Inter"' in t)
        lateral = t.split("[theme.sidebar]")[1]                                                          # F22: barra lateral de tinta, con el tema nativo de Streamlit
        for clave, token in (("backgroundColor", "barra"), ("secondaryBackgroundColor", "panel_alto"), ("textColor", "texto"), ("primaryColor", "acento"), ("borderColor", "barra_borde")):
            assert f'{clave} = "{E.TOKENS[token]}"' in lateral, (ruta.name, clave)


def _archivos_de_la_pagina() -> list[Path]:
    return [p for p in (R / "app").rglob("*") if p.is_file() and p.suffix in {".py", ".toml", ".css", ".html", ".js", ".json"}] + [R / ".streamlit/config.toml"]


def test_la_pagina_no_hace_peticiones_externas() -> None:
    for p in _archivos_de_la_pagina():
        txt = p.read_text(encoding="utf-8").replace("http://www.w3.org/2000/svg", "")        # el espacio de nombres del SVG propio (wordmark) no es una petición de red
        assert not re.search(r"https?://", txt), f"{p.relative_to(R)} contiene una URL"
        assert "@import" not in txt and "googleapis" not in txt and "cdn." not in txt, p.name


def test_la_pagina_no_usa_emojis() -> None:
    emoji = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆✅❌]")
    for p in _archivos_de_la_pagina():
        assert not emoji.search(p.read_text(encoding="utf-8")), f"{p.relative_to(R)} contiene un emoji"
    for s, ic in __import__("waymo_evaluacion.ep3.app_logica", fromlist=["ICONOS"]).ICONOS.items():
        assert ic.startswith(":material/"), s
