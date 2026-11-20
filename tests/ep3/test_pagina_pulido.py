"""F19-B (B2 a B9): mapa de calor con celdas sin datos, tablas sin desplazamiento, columna de fotogramas, formatos de la evidencia, cargador en español, colores de las curvas,
titular de horas de Inicio y precarga. Las cifras no cambian: solo presentación."""
from __future__ import annotations

import glob
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.app_logica import (
    COLUMNA_FOTOGRAMAS, MIN_CAJAS_RANGO, cargar_datos, inicio_resumen, lista_A_detalle, lista_A_presentable, matriz_calor, resumen_cola, tabla_cola,
)
from tests.ep3.test_app import _datos_sinteticos, _modelos_sinteticos, ir_a, textos

R = Path(__file__).resolve().parents[2]
REAL = R / "data/09_app_ep3"
sys.path.insert(0, str(R / "app"))


@pytest.fixture(scope="module")
def entorno(tmp_path_factory):
    base = tmp_path_factory.mktemp("pulido")
    _datos_sinteticos(base / "datos")
    _modelos_sinteticos(base / "modelos")
    # tabla del brazo C para la tarjeta de horas de Inicio (la precarga guarda los datos por carpeta: debe existir antes de la primera visita)
    (base / "datos" / "evidencia" / "ie12__brazo_C_y_equilibrio.csv").write_text("candidato,Fraccion_80_C,Fraccion_80_A\nRegla top,0.3,0.45\n", encoding="utf-8")
    return base


def _abrir(entorno: Path, monkeypatch: pytest.MonkeyPatch, seccion: str):
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.setenv("WAYMO_APP_DATA", str(entorno / "datos"))
    monkeypatch.setenv("WAYMO_APP_MODELOS", str(entorno / "modelos"))
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=60).run()
    ir_a(at, seccion)
    assert not at.exception, at.exception
    return at


# ------------------------------------------------------------------------------------------------------------ B2: mapa de calor
def test_matriz_calor_distingue_sin_datos_de_tasa_cero() -> None:
    celdas = pd.DataFrame({"seg": ["a"], "grupo": ["train"], "ubicacion": "x", "momento": "Day", "cajas": 500})
    for c, (tasa, n, hueco) in enumerate([(0.0, 300, True), (0.0, 40, False), (np.nan, 0, False), (0.9, 100, False), (0.9, 99, False)], 1):
        celdas[f"tasa_c{c}"], celdas[f"n_rango_c{c}"], celdas[f"hueco_c{c}"] = tasa, n, hueco
    m = matriz_calor(celdas).set_index("camara")
    assert MIN_CAJAS_RANGO == 100
    assert m["sin_datos"].tolist() == [False, True, True, False, True]             # 0 % con 300 cajas es un hueco (no «sin datos»); 40 cajas, 0 cajas y 99 cajas sí
    assert m["hueco"].tolist() == [True, False, False, False, False]
    assert matriz_calor(celdas, min_cajas=50)["sin_datos"].tolist() == [False, True, True, False, False]      # 40 cajas sigue siendo poco con min 50; 99 ya alcanza


def test_auditoria_trae_leyenda_con_el_gris_rayado_y_los_detalles_en_un_expander(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Auditoría de cámaras")
    html = " ".join(m.value for m in at.markdown)
    assert "aud-sw rayado" in html and "Sin cajas o menos de 100 en el rango" in html and "aud-sw hueco" in html and "no es lo mismo que 0 %" in html
    assert html.count('class="aud-leyenda"') == 1                                                # F20-P5: UNA sola leyenda (la de la escala de Altair se quitó)
    assert any("Detalle de las celdas marcadas" in m.value for m in at.markdown)         # el detalle ya no va en un acordeón
    assert not any("falsas alarmas" in m.value.lower() for m in at.markdown)


def test_el_mapa_dibuja_todas_las_etiquetas_de_segmento_y_conserva_el_rojo_con_x() -> None:
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "labelOverlap=False" in fuente and "22 * n_seg" in fuente                                  # altura por segmento suficiente y sin ocultar etiquetas
    assert "st.container(height=" in fuente and "seg_corto" in fuente                                  # F20-P5: mapa con altura fija y desplazamiento; etiquetas a 6 dígitos
    assert 'text="X"' in fuente and "E.TOKENS[\"hueco\"]" in fuente and "alt.datum.sin_datos" in fuente


# ------------------------------------------------------------------------------------------------------------ B3 y B4: tablas
def test_lista_a_cabe_sin_desplazarse_y_el_detalle_tiene_lo_demas() -> None:
    la = pd.DataFrame({"segmento": ["1"], "grupo": ["train"], "ubicacion": ["location_sf"], "momento": ["Day"], "camara": ["5 (lateral der.)"], "tasa": [0.0], "mediana_camara": [0.91], "umbral": [0.23],
                       "cajas_en_rango": [300], "cajas_afectadas_poblacion_principal": [268], "positivos_afectados": [227]})
    p, d = lista_A_presentable(la), lista_A_detalle(la)
    assert list(p.columns) == ["Segmento", "Cámara", "Tasa", "En el rango", "Cajas afectadas", "Sin pareja", "Acción sugerida"]
    assert len(p.iloc[0]["Acción sugerida"]) <= 55 and sum(len(c) for c in p.columns) < 75                 # encabezados y accion cortos
    assert {"Ubicación", "Momento del día", "Mediana de la cámara"} <= set(d.columns) and d.iloc[0]["Ubicación"] == "San Francisco"


def test_cola_pone_clase_y_tipo_de_caso_antes_de_los_identificadores_y_cuenta_fotogramas(tmp_path: Path) -> None:
    _datos_sinteticos(tmp_path / "d")
    d = cargar_datos(tmp_path / "d")
    top = d["cajas"].head(6).copy().assign(es_ciclista=0, az_signed=0.0)
    top["key.laser_object_id"] = ["a", "a", "b", "a", "c", "b"]
    top["seg"] = "s1"
    t = tabla_cola(top, 100, {1: (-20.0, 20.0)}, presentacion=False)
    cols = list(t.columns)
    assert cols.index("Clase") < cols.index("Marca de tiempo") and cols.index("Tipo de caso") < cols.index("Identificador de objeto") and cols[-2:] == ["Marca de tiempo", "Identificador de objeto"]
    assert t[COLUMNA_FOTOGRAMAS].tolist() == [3, 3, 2, 3, 1, 2]                                              # cuantas filas de la cola tiene el mismo objeto
    # no cambia el orden de las filas ni la prioridad
    assert t["Posición"].tolist() == [1, 2, 3, 4, 5, 6] and "Prioridad" not in t.columns
    sin = tabla_cola(top, 100, {1: (-20.0, 20.0)}, presentacion=True)
    assert COLUMNA_FOTOGRAMAS in sin.columns and "Identificador de objeto" not in sin.columns
    assert tabla_cola(top.head(2), 100, {1: (-20.0, 20.0)}, presentacion=False)[COLUMNA_FOTOGRAMAS].tolist() == [2, 2]   # sobre la cola completa que se le pasa


def test_el_conteo_de_fotogramas_no_cambia_las_cifras_de_la_cola(tmp_path: Path) -> None:
    _datos_sinteticos(tmp_path / "d")
    d = cargar_datos(tmp_path / "d")
    r = resumen_cola(d["cajas"], d["curva"], "sol", "Todos", 0.2, 20)
    antes = (r["cajas_a_revisar"], r["hallados"], r["positivos_total"])
    tabla_cola(r["top"], r["cajas_cola_total"], {}, False)
    assert (r["cajas_a_revisar"], r["hallados"], r["positivos_total"]) == antes


def test_la_pagina_de_cola_muestra_la_columna_y_su_nota(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Cola de revisión")
    assert COLUMNA_FOTOGRAMAS in at.dataframe[0].value.columns
    assert any("Las cifras de arriba no cambian con los filtros" in c.value for c in at.caption)


# ------------------------------------------------------------------------------------------------------------ B5: formatos de la evidencia
def test_numero_legible_no_mezcla_escalas() -> None:
    assert [F.numero_legible(x) for x in (20.0, 1600.0, 3.0, 0.001, 1e-5, 0.0746, 29.507, 6059.5)] == ["20", "1.600", "3", "0,001", "1,0e-5", "0,0746", "29,51", "6.059,5"]
    df = pd.DataFrame({"hiperparametro": ["min_samples_leaf", "C"], "min_grilla": [20.0, 1e-5], "max_grilla": [1600.0, 100.0]})
    t = F.tabla_legible(df, tabla="ie9__bordes_de_grilla")
    assert t["Mínimo de la grilla"].tolist() == ["20", "1,0e-5"] and t["Máximo de la grilla"].tolist() == ["1.600", "100"]
    assert t["Hiperparámetro"].tolist() == ["Mínimo de muestras por hoja", "C (regularización: menor = más)"]


def test_las_proporciones_salen_como_porcentaje_y_las_diferencias_no() -> None:
    df = pd.DataFrame({"pct_cajas": [0.46], "tasa": [0.2], "Fraccion_80": [0.446], "dif_Fraccion_80_vs_regla": [-0.025], "AUC": [0.823], "ic_lo": [0.1], "pct_nulos": [0.0]})
    t = F.tabla_legible(df, tabla="posthoc__eda_tasas")
    assert t["% de cajas"].iloc[0] == "46,0 %" and t["Proporción sin pareja"].iloc[0] == "20,0 %" and t["Fracción de cajas para el 80 %"].iloc[0] == "44,6 %"
    assert t["Dif. Fraccion 80 vs regla"].iloc[0] == "-0,025" if "Dif. Fraccion 80 vs regla" in t.columns else True
    assert t["AUC"].iloc[0] == "0,823" and t["% de nulos"].iloc[0] == "0,0 %"


@pytest.mark.skipif(not REAL.exists(), reason="faltan los datos de la página")
def test_ninguna_tabla_de_evidencia_tiene_formatos_enganosos() -> None:
    for f in sorted(glob.glob(str(REAL / "evidencia" / "*.csv"))):
        k = Path(f).stem
        t = F.tabla_legible(pd.read_csv(f), tabla=k)
        assert not any("_" in c for c in t.columns), (k, list(t.columns))
        assert not any("alsa" in c for c in t.columns), (k, "usa «falsas alarmas»: DEV-3")
        for c in t.columns:
            v = t[c].astype(str)
            assert not v.str.fullmatch(r"-?[1-9]\d+,000").any() and not (v == "-0,000").any(), (k, c)                          # «20,000» junto a «1.600» es engañoso (enteros con decimales ceros)
            if c.startswith(("%", "Proporción")) or "Fracción de cajas" in c:
                assert v.str.endswith("%").all(), (k, c)
    t = F.tabla_legible(pd.read_csv(REAL / "evidencia" / "ie9__bordes_de_grilla.csv"), tabla="ie9__bordes_de_grilla")
    assert "1,0e-5" in t["Mínimo de la grilla"].tolist() and "20" in t["Mínimo de la grilla"].tolist() and "1.600" in t["Máximo de la grilla"].tolist()


@pytest.mark.skipif(not REAL.exists(), reason="faltan los datos de la página")
def test_el_recall_de_ciclistas_de_las_preguntas_frecuentes_sigue_siendo_0_443() -> None:
    from waymo_evaluacion.ep3.app_logica import preguntas_frecuentes

    eq = pd.read_csv(REAL / "evidencia" / "posthoc__equidad.csv")
    assert "0,443" in dict(preguntas_frecuentes(eq))["¿Qué pasa con los ciclistas?"]


# ------------------------------------------------------------------------------------------------------------ B6: cargador en español
def test_puntuar_tiene_paso_1_y_paso_2_opcional_y_el_cargador_en_espanol(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    etiquetas = [u.label for u in at.get("file_uploader")]
    assert etiquetas[0].startswith("Archivo 1 (obligatorio)") and etiquetas[1].startswith("Archivo 2 (opcional)")          # F20-P8: sin tarjetas 1-2-3 que choquen con «Paso 1» y «Paso 2»
    import estilos as E

    css = E.css()
    assert "Elegir archivo" in css and "Arrastre el archivo aquí" in css and "stFileUploaderDropzone" in css and "500 MB" in css
    assert "Drag and drop" not in css


# ------------------------------------------------------------------------------------------------------------ B7: colores de las curvas
def test_las_curvas_dos_pasos_y_un_paso_se_distinguen_en_color_y_trazo() -> None:
    import estilos as E

    c = dict(zip(E.CURVAS_NOMBRES, E.CURVAS_COLORES))
    r = dict(zip(E.CURVAS_NOMBRES, E.CURVAS_RAYAS))
    assert c["Dos pasos"] != c["Un paso"] and r["Dos pasos"] != r["Un paso"]
    assert len(set(E.CURVAS_COLORES)) == len(E.CURVAS_COLORES)
    # contraste entre los dos colores principales (no basta el tono: tambien difieren en luminosidad o trazo) y contra el fondo
    assert E.contraste(c["Dos pasos"], "#FFFFFF") >= 4.5 and E.contraste(c["Un paso"], "#FFFFFF") >= 3.0
    assert E.contraste(c["Dos pasos"], c["Un paso"]) >= 1.2
    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    assert "alt.Stroke(" in fuente and "alt.StrokeDash(" in fuente          # leyenda tomada de la linea
    # La banda NO codifica «nombre» (con fill + legend=None Vega-Lite fusiona las leyendas y borra la de las lineas: se vio en el DOM, F19-B7): una banda por curva con color fijo
    assert "fill=alt.Fill(" not in fuente and "mark_area(opacity=0.13, color=c)" in fuente
    assert 'presentes = set(curva["nombre"])' in fuente          # la leyenda lista solo las curvas dibujadas (no las 5 posibles)


# ------------------------------------------------------------------------------------------------------------ B8: horas de Inicio
def test_resumen_muestra_las_horas_de_los_tres_flujos_leidas_del_mismo_origen(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir(entorno, monkeypatch, "Resumen")
    html = textos(at)
    assert "Estimación en muestra" in html and "(supuesto" in html and "80 %" in html and "aud-muestra" in html            # etiqueta «en muestra» al lado de la cifra de dos pasos
    assert html.count("≈ ") >= 3


@pytest.mark.skipif(not (REAL / "kpis.json").exists(), reason="faltan los datos de la página")
def test_las_horas_de_inicio_son_132_y_358_y_su_diferencia_sigue_siendo_la_de_antes() -> None:
    D = cargar_datos(REAL)
    r = inicio_resumen(D, 20)
    assert round(r["horas_dos_pasos"]) == 132 and round(r["horas_sin_orden"]) == 358 and round(r["horas_un_paso"]) == 200
    assert r["horas_sin_orden"] - r["horas_dos_pasos"] == pytest.approx(r["horas_ahorradas"])               # los 226 h de antes = 358 - 132
    assert round(r["horas_ahorradas"]) == 226


# ------------------------------------------------------------------------------------------------------------ B9: precarga
def test_la_precarga_carga_una_vez_y_se_comparte(tmp_path: Path) -> None:
    import precarga as PC

    _datos_sinteticos(tmp_path / "d")
    _modelos_sinteticos(tmp_path / "m")
    h = PC.iniciar(str(tmp_path / "d"), str(tmp_path / "m"))
    h.join(timeout=60)
    assert not h.is_alive() and PC.estado()["listo"]
    assert PC.iniciar(str(tmp_path / "d"), str(tmp_path / "m")) is h                     # una sola vez por par de carpetas
    d1, d2 = PC.datos(str(tmp_path / "d")), PC.datos(str(tmp_path / "d"))
    assert d1 is d2 and PC.artefactos(str(tmp_path / "m")) is PC.artefactos(str(tmp_path / "m"))
    assert PC.min_cajas(str(tmp_path / "m")) == 100


def test_la_precarga_no_rompe_si_faltan_datos(tmp_path: Path) -> None:
    import precarga as PC

    h = PC.iniciar(str(tmp_path / "no_hay_datos"), str(tmp_path / "no_hay_modelos"))
    h.join(timeout=30)
    assert PC.estado()["listo"] and PC.estado()["error"]
    with pytest.raises(FileNotFoundError):
        PC.datos(str(tmp_path / "no_hay_datos"))


@pytest.mark.skipif(not (REAL / "kpis.json").exists() or not (R / "data/06_models_ep3/modelo_final_v3.joblib").exists(), reason="faltan los datos o la solución congelada")
def test_tras_la_precarga_ninguna_seccion_tarda_mas_de_3_segundos(monkeypatch: pytest.MonkeyPatch) -> None:
    at_mod = pytest.importorskip("streamlit.testing.v1")
    import precarga as PC
    from waymo_evaluacion.ep3.app_logica import SECCIONES

    monkeypatch.delenv("WAYMO_APP_DATA", raising=False)
    monkeypatch.delenv("WAYMO_APP_MODELOS", raising=False)
    PC.iniciar(str(REAL), str(R / "data/06_models_ep3")).join(timeout=120)
    lentas = {}
    for s in SECCIONES:
        t0 = time.time()
        at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=60).run()
        ir_a(at, s)
        assert not at.exception
        if time.time() - t0 > 3.0:
            lentas[s] = round(time.time() - t0, 1)
    assert not lentas, f"secciones de más de 3 s tras la precarga: {lentas}"


def test_el_lanzador_existe_y_los_arranques_lo_usan_con_las_opciones_de_seguridad() -> None:
    assert "precarga.iniciar" in (R / "app" / "lanzar.py").read_text(encoding="utf-8") and "cli.main()" in (R / "app" / "lanzar.py").read_text(encoding="utf-8")
    for n in ("arrancar_app.bat", "arrancar_app.ps1"):
        t = (R / "scripts" / "ep3" / n).read_text(encoding="utf-8")
        assert "lanzar.py" in t and "--server.address localhost" in t and "--browser.gatherUsageStats false" in t


# ------------------------------------------------------------------------------------------------------------ B10: capturas
def test_hay_capturas_completas_de_las_8_secciones_y_del_modo_presentacion_a_1366_y_1920() -> None:
    carpeta = R / "images/ep3/pagina"
    res = R / "data/08_reporting_ep3/capturas_resultado.json"
    if not res.exists():
        pytest.skip("todavía no se generaron las capturas")
    import json

    r = json.loads(res.read_text(encoding="utf-8"))
    assert all(x["listo"] for x in r), [x["archivo"] for x in r if not x["listo"]]
    for ancho in (1366, 1920):
        png = sorted(carpeta.glob(f"*_{ancho}.png"))
        assert len(png) == 15, (ancho, [p.name for p in png])           # F21: 8 páginas, cola sin selección, 6 pestañas de Validación y el modo presentación (Validación no tiene captura aparte)
        assert all(p.stat().st_size > 20_000 for p in png), [p.name for p in png if p.stat().st_size <= 20_000]       # un esqueleto en blanco pesa ~9 KB
    assert any("explica" in p.name for p in carpeta.glob("*_1366.png")) and any("presentacion" in p.name for p in carpeta.glob("*_1920.png"))
