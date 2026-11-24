"""F34: Validación rediseñada (veredicto calculado, cinco pestañas con la misma plantilla, criterios O1 a O4 en tarjetas, tablas de apoyo con un componente único).

Cubre la lógica pura (titular con sus dos ramas, conteos «X de N», avisos calculados, puntos clave), el componente de tabla (paginación, decimales, signo menos, intervalos en una columna, CSV sin
redondear), la regresión de cifras (todo lo que mostraba Validación antes sigue igual) y la página con los datos reales. Escribe solo en ``tmp_path``.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tests.ep3.test_app import textos
from tests.ep3.test_pagina_f21 import HAY_REAL, REAL, _abrir_real

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))
ANTES = R / "tests/ep3/datos_f34/valores_antes_validacion.json"


def _seleccion(o: dict[str, list[bool]], candidatos: list[str] | None = None) -> pd.DataFrame:
    c = candidatos or ["Regla top", "LR3", "XGB"]
    return pd.DataFrame({"candidato": c, "O1": o["O1"], "O2": o["O2"], "O3": o["O3"], "O4": o["O4"], "AUC_min_fold": [0.6, 0.7, 0.8, 0.8, 0.8][:len(c)], "ECE_cal": [0.04, 0.06, 0.03, 0.03, 0.03][:len(c)]})


# ------------------------------------------------------------------------------------------------------------ titular
def test_el_titular_afirma_la_regla_solo_si_ninguna_alternativa_cumple_o2() -> None:
    from waymo_evaluacion.ep3 import validacion as V

    t = _seleccion({"O1": [True] * 3, "O2": [False, False, False], "O3": [True] * 3, "O4": [False] * 3})
    r = V.titular_validacion(t, "Regla top")
    assert r["rama"] == "ninguna" and r["n"] == 2 and r["texto"] == "La regla simple se mantiene: ninguna de las 2 alternativas probadas «vale la pena» frente a ella."


def test_si_alguna_alternativa_cumple_o2_el_titular_es_neutro_y_dice_cuantas_y_cuales() -> None:
    from waymo_evaluacion.ep3 import validacion as V

    t = _seleccion({"O1": [True] * 3, "O2": [False, True, True], "O3": [True] * 3, "O4": [False] * 3})
    r = V.titular_validacion(t, "Regla top")
    assert r["rama"] == "alguna" and r["cumplen"] == ["LR3", "XGB"] and "se mantiene" not in r["texto"] and r["texto"].startswith("2 de las 2 alternativas") and "LR3, XGB" in r["texto"]
    t["O2"] = [True, False, False]                                                                      # que la propia regla cumpla O2 no cuenta: solo las alternativas
    assert V.titular_validacion(t, "Regla top")["rama"] == "ninguna"


def test_el_numero_de_alternativas_sale_de_la_tabla_y_no_es_fijo() -> None:
    from waymo_evaluacion.ep3 import validacion as V

    t = _seleccion({"O1": [True] * 5, "O2": [False] * 5, "O3": [True] * 5, "O4": [False] * 5}, ["Regla top", "A", "B", "C", "D"])
    assert V.titular_validacion(t, "Regla top")["n"] == 4 and "las 4 alternativas" in V.titular_validacion(t, "Regla top")["texto"]


# ------------------------------------------------------------------------------------------------------------ criterios O1 a O4
def test_los_conteos_x_de_n_salen_de_la_tabla_con_otros_datos() -> None:
    from waymo_evaluacion.ep3 import validacion as V

    t = _seleccion({"O1": [True, True, False], "O2": [False, False, False], "O3": [True, True, True], "O4": [True, False, False]})
    c = {x["clave"]: x for x in V.conteos_criterios(t)}
    assert (c["O1"]["texto"], c["O2"]["texto"], c["O3"]["texto"], c["O4"]["texto"]) == ("✓ 2 de 3", "✕ 0 de 3", "✓ 3 de 3", "✓ 1 de 3")
    assert c["O2"]["ok"] is False and c["O4"]["ok"] is True and all(x["definicion"] for x in c.values())


def test_el_aviso_de_o4_aparece_solo_si_la_regla_no_cumple_y_usa_el_minimo_del_plan() -> None:
    from waymo_evaluacion.ep3 import validacion as V

    ev = {"posthoc__auc_por_fold_y_brazos": pd.DataFrame({"candidato": ["Regla top"] * 3, "fold": ["0", "1", "2"], "AUC_A": [0.647, 0.83, 0.85]})}
    t = _seleccion({"O1": [True] * 3, "O2": [False] * 3, "O3": [True] * 3, "O4": [False, False, False]})
    plan = {"P7": {"estabilidad": {"auc_min_fold": 0.8}}, "P8": {"objetivos": {"O4": {"ece_max": 0.05}}}}
    a = V.aviso_o4(t, "Regla top", ev, plan)
    assert a and "partición 0" in a and "0,600" in a and "0,80" in a and "0,75" not in a                  # el mínimo exigido sale del plan, no de un 0,75 escrito a mano
    t["O4"] = [True, False, False]
    assert V.aviso_o4(t, "Regla top", ev, plan) is None                                                   # si la regla cumple O4, no hay aviso


def test_los_datos_reales_dan_11_alternativas_menos_la_regla_y_ningun_aviso_inventado() -> None:
    if not HAY_REAL:
        pytest.skip("faltan los datos de la página")
    from waymo_evaluacion.ep3 import validacion as V
    from waymo_evaluacion.ep3.app_logica import cargar_datos

    ev = cargar_datos(REAL)["evidencia"]
    t = ev["ie12__tabla_de_seleccion"]
    assert V.titular_validacion(t, "Regla top")["texto"] == "La regla simple se mantiene: ninguna de las 10 alternativas probadas «vale la pena» frente a ella."
    assert [c["texto"] for c in V.conteos_criterios(t)] == ["✓ 11 de 11", "✕ 0 de 11", "✓ 11 de 11", "✕ 0 de 11"]
    a = V.aviso_o4(t, "Regla top", ev)
    assert a and "partición 0" in a and "0,647" in a and "0,75" in a
    assert V.aviso_bordes(ev).startswith("Único hiperparámetro que termina en el borde") and "LGBM" in V.aviso_bordes(ev) and "Los otros 12 no" in V.aviso_bordes(ev)
    g = V.puntos_generalizacion(ev, "Regla top")
    assert len(g) == 2 and "−0,047" in g[0] and "+0,060" in g[0] and "0,647" in g[1] and "0,685" in g[1] and "XGB" in g[1]
    assert V.puntos_tipos_de_caso(ev)[-1].startswith("Son los tipos de caso que muestra Explica una caja")
    f = V.frase_auditoria(ev, "Regla top")
    assert f and "12,7 de los 15,0 puntos" in f and "2,1 puntos" in f and "…998801" in f


def test_la_regla_de_mejora_de_hiperparametros_coincide_con_el_veredicto_guardado() -> None:
    """«Mejora» = cambio de PR-AUC de al menos la diferencia mínima del plan y límite inferior sobre 0 (la regla de ``f3_analisis.py``): se comprueba contra los datos."""
    if not HAY_REAL:
        pytest.skip("faltan los datos de la página")
    from waymo_evaluacion.ep3 import validacion as V
    from waymo_evaluacion.ep3.app_logica import cargar_datos

    t = cargar_datos(REAL)["evidencia"]["ie9__defecto_vs_optimizado"]
    esperado = np.where((t["dif_PR-AUC"] >= 0.010) & (t["dif_PR-AUC_lo"] > 0), "mejora", "no mejora")
    assert list(t["veredicto"]) == list(esperado)
    assert "0,010" in V.regla_mejora_hiperparametros()


def test_los_puntos_clave_de_tipos_de_caso_omiten_explica_si_la_pagina_no_existe(monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3 import validacion as V

    ev = {"nosup__clusters_k2": pd.DataFrame({"tipo_de_caso": ["a", "b"], "cajas": [10, 20], "pct_cajas": [1 / 3, 2 / 3], "tasa_sin_camara": [0.1, 0.3]})}
    assert V.puntos_tipos_de_caso(ev)[-1].startswith("Son los tipos de caso")
    monkeypatch.setattr(V, "SECCIONES", [s for s in V.SECCIONES if s != "Explica una caja"])
    assert not [p for p in V.puntos_tipos_de_caso(ev) if "Explica una caja" in p]


# ------------------------------------------------------------------------------------------------------------ componente de tabla
def _df_prueba(n: int = 60) -> pd.DataFrame:
    return pd.DataFrame({"k": np.arange(n), "AUC": np.linspace(0.5, 0.9, n), "AUC_lo": np.linspace(0.4, 0.8, n), "AUC_hi": np.linspace(0.6, 1.0, n), "dif": np.linspace(-0.0126, 0.0074, n), "p": np.linspace(0.0, 1.0, n), "n": np.linspace(1000, 90000, n)})


def _columnas_prueba():
    from waymo_evaluacion.ep3.tablas_estandar import Col

    return [Col("k", "Grupo", "plain"), Col("AUC", "AUC (IC 95 %)", "auc", "AUC con su intervalo", "AUC_lo", "AUC_hi"), Col("dif", "Diferencia", "dif"), Col("p", "Proporción", "pct"), Col("n", "Cajas", "int")]


def test_la_tabla_formatea_decimales_signo_menos_e_intervalo_en_una_columna() -> None:
    from waymo_evaluacion.ep3.tablas_estandar import construir_tabla

    t = construir_tabla("x", _df_prueba(), _columnas_prueba(), "Título", "¿Responde?")
    assert [c.encabezado for c in t.columnas] == ["Grupo", "AUC (IC 95 %)", "Diferencia", "Proporción", "Cajas"]               # el orden de las columnas es el de la especificación
    primera, ultima = t.filas[0], t.filas[-1]
    assert primera == ["0", "0,500 (0,400–0,600)", "−0,013", "0,0 %", "1.000"] or primera[:3] == ["0", "0,500 (0,400–0,600)", "−0,013"]
    assert ultima[2] == "+0,007" and ultima[3].replace("\xa0", " ") == "100,0 %" and ultima[4] == "90.000"                           # «+» en las diferencias positivas y punto de miles
    texto = " ".join(" ".join(f) for f in t.filas)
    assert not re.search(r"(?<![\w)])-\d", texto) and "−" in texto                                                           # un solo signo menos
    assert all(len(c.encabezado.split()) <= 4 for c in t.columnas)


def test_la_tabla_pagina_de_25_en_25_y_el_csv_trae_todo_sin_redondear() -> None:
    from waymo_evaluacion.ep3.tablas_estandar import construir_tabla, pagina, paginas, texto_filas, texto_rango

    df = _df_prueba(60)
    t = construir_tabla("x", df, _columnas_prueba(), "Título", "¿Responde?")
    assert t.n_filas == 60 and paginas(60) == 3 and paginas(25) == 1 and paginas(26) == 2 and paginas(0) == 1
    assert [len(pagina(t.filas, n)) for n in (1, 2, 3)] == [25, 25, 10] and pagina(t.filas, 99) == pagina(t.filas, 3) and pagina(t.filas, 0) == pagina(t.filas, 1)
    assert texto_filas(t) == "60 filas" and texto_rango(t, 3) == "Filas 51 a 60 de 60"
    csv = pd.read_csv(pd.io.common.BytesIO(t.csv))
    assert list(csv.columns) == list(df.columns) and np.allclose(csv["AUC"], df["AUC"], atol=0, rtol=1e-12) and np.allclose(csv["AUC_lo"], df["AUC_lo"], atol=0, rtol=1e-12)    # todas las columnas y sin redondear


def test_una_tabla_de_25_filas_o_menos_muestra_todas_y_no_pagina() -> None:
    from waymo_evaluacion.ep3.tablas_estandar import construir_tabla, paginas

    t = construir_tabla("x", _df_prueba(25), _columnas_prueba(), "T", "R")
    assert t.n_filas == 25 and paginas(t.n_filas) == 1


def test_las_columnas_que_faltan_en_los_datos_se_omiten_sin_romper() -> None:
    from waymo_evaluacion.ep3.tablas_estandar import construir_tabla

    df = _df_prueba(3).drop(columns=["AUC_lo", "AUC_hi", "dif"])
    t = construir_tabla("x", df, _columnas_prueba(), "T", "R")
    assert [c.encabezado for c in t.columnas] == ["Grupo", "AUC (IC 95 %)", "Proporción", "Cajas"] and t.filas[0][1] == "0,500"


def test_los_tipos_de_formato_y_los_textos_visibles() -> None:
    from waymo_evaluacion.ep3 import formato as F
    from waymo_evaluacion.ep3.tablas_estandar import Col, _un

    assert F.texto_visible("ARI minimo (maximo silhouette)") == "ARI mínimo (máximo silhouette)" and F.texto_visible("tasa sin_camara de atipicas") == "tasa sin pareja de atípicas"
    assert F.segmento_corto("257766998801 camara 3") == "…998801 camara 3" and F.segmento_corto("1554139633239016") == "1554139633239016"
    assert F.nombre_visible("vista obs") == "vista de observación" and F.nombre_visible("vista_pos") == "vista de posición" and F.nombre_visible("vista tam") == "vista de tamaño"
    assert F.menos("-0,011 y 2-5") == "−0,011 y 2-5" and F.decimal_signado(0.0004, 3) == "0,000" and F.decimal_signado(0.0049, 3) == "+0,005"
    assert _un("pts", -0.15) == "−15,0 puntos" and _un("entrunc", 6059.5) == "6.059" and _un("seg", 257766998801.0) == "…998801" and _un("bool", True).startswith("✓") and _un("bool", False).startswith("✕")


# ------------------------------------------------------------------------------------------------------------ regresión de cifras (regla 6)
def _numeros(textos_: list[str]) -> list[tuple[float, int]]:
    out = []
    for t in textos_:
        t = t.replace("\xa0", " ").replace("−", "-")
        for m in re.finditer(r"(?<![\w])-?\d{1,3}(?:\.\d{3})+(?:,\d+)?(?!\d)|(?<![\w])-?\d+(?:,\d+)?(?!\d)", t):
            s = m.group(0).replace(".", "").replace(",", ".")
            out.append((float(s), len(s.split(".")[1]) if "." in s else 0))
    return out


def _celdas_crudas(df: pd.DataFrame) -> list[float]:
    num = df.select_dtypes(include="number")
    return [float(x) for x in num.to_numpy().ravel() if not np.isnan(x)]


@pytest.mark.skipif(not (HAY_REAL and ANTES.exists()), reason="faltan los datos de la página o el archivo de valores de antes")
def test_regresion_de_cifras_todo_lo_que_mostraba_validacion_antes_sigue_igual() -> None:
    from waymo_evaluacion.ep3 import formato as F
    from waymo_evaluacion.ep3 import validacion as V
    from waymo_evaluacion.ep3.app_logica import cargar_datos, datos_validacion, lectura_evidencia, tabla_resultados_clave

    antes = json.loads(ANTES.read_text(encoding="utf-8"))
    D = cargar_datos(REAL)
    ev = D["evidencia"]
    faltan: list[str] = []
    for k, viejo in antes["tablas"].items():
        if k == "ie9__curvas_de_validacion":
            continue                                                                                   # sale de pantalla: queda en la descarga CSV (se comprueba abajo contra los datos)
        t = V.tabla_apoyo(k, ev)
        assert t is not None, k
        assert t.n_filas == len(viejo["filas"]), (k, t.n_filas, len(viejo["filas"]))                   # mismas filas
        pantalla = _numeros([c for f in t.filas for c in f] + [t.nota])
        crudos = _celdas_crudas(ev[k])
        texto_nuevo = " ".join(c for f in t.filas for c in f)
        for valor, d in _numeros([c for f in viejo["filas"] for c in f]):
            if valor >= 1e11:                                                                          # identificador de segmento: ahora «…534050» (los 6 últimos dígitos), igual que el resto de las páginas
                if str(int(valor))[-6:] not in texto_nuevo and str(int(valor)) not in t.csv.decode("utf-8"):
                    faltan.append(f"{k}: segmento {int(valor)}")
                continue
            en_pantalla = any(abs(round(v, d) - valor) < 1e-9 or abs(round(v / 100, d) - valor) < 1e-9 or abs(round(v * 100, d) - valor) < 1e-9 for v, _ in pantalla)
            en_csv = any(abs(round(v, d) - valor) < 1e-9 or abs(round(v * 100, d) - valor) < 1e-9 or abs(round(v / 100, d) - valor) < 1e-9 for v in crudos)
            if not (en_pantalla or en_csv):
                faltan.append(f"{k}: {valor}")
    assert not faltan, faltan[:10]                                                                     # ningún número de antes se perdió: o se ve igual o está sin redondear en la descarga
    csv = ev["ie9__curvas_de_validacion"]
    assert len(csv) == 175 and list(pd.read_csv(REAL / "evidencia/ie9__curvas_de_validacion.csv").columns) == list(csv.columns)
    # los datos de cada gráfico, las lecturas, los resultados clave y las cifras del Resumen son las mismas funciones de antes
    nuevo_graf = {k: json.loads(v.to_json(orient="records")) for k, v in datos_validacion(ev).items()}
    assert nuevo_graf == antes["graficos"] and lectura_evidencia(ev) == antes["lecturas"]
    assert tabla_resultados_clave(D["kpis"]).drop(columns="Fuente").astype(str).to_numpy().tolist() == antes["resultados_clave"]
    rc = V.tabla_resultados(tabla_resultados_clave(D["kpis"]))
    esperado = [[F.menos(str(x)) for x in (F.texto_visible(F.nombre_visible(a)), F.nombre_visible(b), F.texto_visible(F.nombre_visible(c)))] for a, b, c in antes["resultados_clave"]]
    assert rc.filas == esperado and rc.n_filas == 5                                                       # las 5 filas de «Resultados de la solución elegida», con los mismos valores


# ------------------------------------------------------------------------------------------------------------ la página con los datos reales
@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_la_pagina_tiene_cinco_pestanas_cabecera_y_tablas_de_apoyo_cerradas(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Validación")
    assert [t.label for t in at.tabs] == ["Modelo elegido", "Generalización", "Alternativas", "Tipos de caso", "En muestra"]
    html = " ".join(m.value for m in at.markdown).replace("\xa0", " ")
    assert "La regla simple se mantiene: ninguna de las 10 alternativas probadas «vale la pena» frente a ella." in html
    for esperado in ("0,823", "80.571", "80,6 %", "44,3 %", "intervalo 95 %: 0,725 a 0,900", "En muestra: 41 segmentos de desarrollo", "Sin validación con datos nuevos", "Ciclistas: regla poco confiable"):
        assert esperado in html, esperado
    apoyo = [e.label for e in at.expander if e.label.startswith("Tablas de apoyo")]
    assert apoyo == ["Tablas de apoyo (5)", "Tablas de apoyo (5)", "Tablas de apoyo (3)", "Tablas de apoyo (7)", "Tablas de apoyo (6)"]
    assert "Cifras de apoyo" not in html and "Ver tabla completa" not in html


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_la_pagina_no_muestra_identificadores_de_12_digitos_ni_guiones_como_signo_menos(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Validación")
    visible = re.sub(r"<style>.*?</style>", " ", " ".join(m.value for m in at.markdown), flags=re.S)
    visible = re.sub(r"<[^>]+>", " ", visible)
    assert not re.search(r"(?<!\d)\d{12}(?!\d)", visible)                                              # solo «…534050»
    tablas = " ".join(re.findall(r"<td[^>]*>([^<]*)</td>", " ".join(m.value for m in at.markdown)))
    assert not re.search(r"(?<![\w)])-\d", tablas) and "maximo" not in visible and "minimo" not in visible
    assert "vista obs" not in visible and "vista tam" not in visible and "vista pos" not in visible
    assert "regla top" not in visible.lower()


@pytest.mark.skipif(not HAY_REAL, reason="faltan los datos de la página")
def test_la_comparacion_ep2_ep3_muestra_el_ari_con_tres_decimales_y_su_nota(monkeypatch: pytest.MonkeyPatch) -> None:
    from waymo_evaluacion.ep3 import validacion as V
    from waymo_evaluacion.ep3.app_logica import cargar_datos

    ev = cargar_datos(REAL)["evidencia"]
    t = V.tabla_apoyo("nosup__comparacion_ep2_ep3", ev)
    fila = next(f for f in t.filas if f[0].startswith("ARI KMeans vs GMM"))
    assert fila[1:] == ["0,997", "0,008"] and "0.00793217" in t.csv.decode("utf-8")                       # el valor no cambia: sin redondear en la descarga (la copia de la evidencia trae 8 decimales)
    assert "no es un error" in t.nota and "mismas 15.000 filas" in t.nota


def test_cada_pestana_nombrada_en_un_texto_existe() -> None:
    """Regla 10: cualquier texto de la página que nombre una pestaña de Validación usa uno de los cinco nombres vigentes."""
    from waymo_evaluacion.ep3 import validacion as V

    fuentes = [R / "app" / "secciones.py", R / "src/waymo_evaluacion/ep3/app_logica.py", R / "src/waymo_evaluacion/ep3/validacion.py"]
    vistos = set()
    for f in fuentes:
        for m in re.finditer(r"pestaña[s]? «([^»]+)»", f.read_text(encoding="utf-8")):
            vistos.add(m.group(1))
    permitidos = set(V.PESTANAS) | {"Cola de cajas", "Curva de priorización"}                                 # las dos de la Cola
    assert vistos <= permitidos, vistos - permitidos


def test_el_css_de_f34_respeta_los_minimos_de_accesibilidad() -> None:
    import estilos as E

    css = E.css()
    bloque = css[css.index("F34: Validación"):css.index(".st-key-ir_cola {")]
    tamanos = [float(x) for x in re.findall(r"font-size: ([\d.]+)rem", bloque)]
    assert tamanos and min(tamanos) >= 0.75                                                              # nada bajo 12 px
    assert "outline: 0" in bloque and ":focus-visible" in bloque and "pagtab_" in bloque               # el foco azul solo con teclado; los botones deshabilitados con texto legible
    assert not re.search(r"#[0-9A-Fa-f]{6}", bloque) and "999px" not in bloque and "font-weight: 700" not in bloque
