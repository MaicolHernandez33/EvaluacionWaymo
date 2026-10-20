"""Pruebas del README generado por scripts/generar_readme.py.

Usan los archivos de salida de los notebooks (data/08_reporting, docs/); como `data/` no esta en git, se omiten si faltan.
"""
import importlib.util
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import pandas as pd
import pytest

R = Path(__file__).resolve().parent.parent
HAY_DATOS = all((R / p).exists() for p in ("data/08_reporting/10_resumen_cifras.json", "data/08_reporting/pytest_resumen.json", "data/08_reporting/ep1_pruebas_cobertura.json", "docs/informe_tecnico_EP2.md"))
pytestmark = pytest.mark.skipif(not HAY_DATOS, reason="faltan los archivos de salida de los notebooks o del informe (data/ no esta en git)")
BASE = "Regla: menos puntos top"


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, R / "scripts" / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _generar():
    r = subprocess.run([sys.executable, "-X", "utf8", str(R / "scripts" / "generar_readme.py")], cwd=R, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, f"el generador fallo:\n{r.stdout}\n{r.stderr}"
    return (R / "README.md").read_text(encoding="utf-8")


def _sin_hora(txt):
    return "\n".join(l for l in txt.splitlines() if not l.startswith(("*Generado por", "**Curso:**")))      # la hora y la fecha cambian entre corridas


def _sec(readme, n):
    m = re.search(rf"^## {n}\. .*?(?=^## {n + 1}\. |\Z)", readme, flags=re.S | re.M)
    assert m, f"no se encontro la seccion {n} del README"
    return m.group(0)


@pytest.fixture(scope="module")
def readme():
    return _generar()


def _slug(t):
    t = unicodedata.normalize("NFC", t.lower())
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", t).strip())


def test_generador_dos_veces_misma_salida_salvo_la_hora(readme):
    segunda = _generar()
    assert _sin_hora(readme) == _sin_hora(segunda)


def test_enlaces_e_imagenes_relativos_existen(readme):
    faltan = []
    for m in re.finditer(r"!?\[[^\]]*\]\(([^)\s]+)\)", readme):
        destino = m.group(1)
        if destino.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if not (R / destino.split("#")[0]).exists():
            faltan.append(destino)
    assert not faltan, f"enlaces o imagenes que no existen: {faltan}"


def test_anclas_del_indice_existen(readme):
    heads = {_slug(l[3:]) for l in readme.splitlines() if l.startswith("## ")}
    for a in re.findall(r"\]\(#([^)]+)\)", readme):
        assert a in heads, f"ancla sin encabezado: {a}"


def test_tablas_con_celdas_parejas(readme):
    ver = _cargar("verificar_tablas_markdown")
    total, malas = ver.analizar(R / "README.md")
    assert total >= 12 and not malas, f"tablas desiguales: {malas}"


def test_longitud_y_figuras(readme):
    assert len(readme.splitlines()) <= 520
    figs = re.findall(r"!\[[^\]]*\]\(images/[^)]+\)", readme)
    assert 8 <= len(figs) <= 10
    assert readme.count("*Figura:") == len(figs)                       # todas con pie de figura
    for obligatoria in ("08_tasa_por_puntos_clase_distancia", "08_tasa_por_azimut", "09_comparacion_modelos", "10_resultado_principal", "10_puntos_de_operacion", "10_influencia", "10_M_mapa_calor"):
        assert obligatoria in readme, f"falta la figura {obligatoria}"
    assert "08_clusters_tasa" in readme or "08_clusters_pca" in readme


def test_estructura_y_una_frase_por_seccion(readme):
    titulos = [l for l in readme.splitlines() if l.startswith("## ")]
    assert [int(t.split(".")[0][3:]) for t in titulos] == list(range(1, 16))
    for bloque in re.split(r"^## ", readme, flags=re.M)[1:]:
        lineas = [l for l in bloque.splitlines()[1:] if l.strip()]
        assert lineas[0].startswith("> "), f"la seccion '{bloque.splitlines()[0]}' no abre con una frase-resumen"
    assert "```" in readme and "Mermaid" not in readme and "mermaid" not in readme   # diagrama ASCII, no Mermaid


def test_resumen_coincide_con_los_csv(readme):
    pct = lambda x: (f"{x * 100:.1f}".replace(".", ",") + " %")
    n3 = lambda x: f"{x:.3f}".replace(".", ",")
    punto = lambda t: float(str(t).split()[0])
    resumen = readme.split("## 1. Resumen")[1].split("## 2.")[0]
    rep = pd.read_csv(R / "data/08_reporting/09_comparacion_modelos.csv").set_index("modelo")
    assert n3(punto(rep.loc[BASE, "AUC"])) in resumen and pct(punto(rep.loc[BASE, "Fraccion para 80%"])) in resumen
    t10 = pd.read_csv(R / "data/08_reporting/10_resultado_principal.csv").set_index("metodo")
    assert n3(punto(t10.loc[BASE, "AUC"])) in resumen and pct(punto(t10.loc[BASE, "Fraccion para 80%"])) in resumen
    o10 = pd.read_csv(R / "data/08_reporting/10_puntos_de_operacion.csv")
    fila = o10[(o10["metodo"] == BASE) & o10["punto"].str.startswith("A")].iloc[0]
    assert n3(punto(fila["recall"])) in resumen and pct(punto(fila["pct_revisar"])) in resumen
    o9 = pd.read_csv(R / "data/08_reporting/09_puntos_operacion.csv")
    f9 = o9[(o9["metodo"] == BASE) & o9["punto"].str.startswith("A")].iloc[0]
    assert n3(punto(f9["recall"])) in resumen and pct(punto(f9["pct_revisar"])) in resumen
    sp = pd.read_csv(R / "data/08_reporting/10_L_sin_segmento_principal.csv")
    s = sp[(sp["metodo"] == BASE) & sp["resultado"].str.startswith("sin")].iloc[0]
    assert n3(punto(s["AUC"])) in resumen and pct(punto(s["Fraccion para 80%"])) in resumen
    so = pd.read_csv(R / "data/08_reporting/10_L_sin_segmento_operacion.csv")
    f = so[(so["metodo"] == BASE) & (so["punto"] == "A")].iloc[0]
    assert n3(punto(f["recall sin el segmento"])) in resumen and pct(punto(f["% a revisar sin el segmento"])) in resumen


def test_resultados_post_hoc_etiquetados_y_datos_de_ep1(readme):
    for parrafo in re.split(r"\n\s*\n", readme):
        if re.search(r"(?i)sin el segmento", parrafo) and "tabla" not in parrafo[:0]:
            assert "post hoc" in parrafo.lower(), f"parrafo con resultado sin el segmento y sin etiqueta post hoc: {parrafo[:90]}"
    s3 = readme.split("## 3. Qué hicimos en EP1")[1].split("## 4.")[0]
    ep1 = pd.read_json(R / "data/08_reporting/ep1_pruebas_cobertura.json", typ="series")
    assert f"{ep1['nodos_total']} nodos" in s3 and f"{ep1['pruebas_pasadas']} pruebas" in s3
    assert "34.098" in s3 and "15,7 %" in s3


# ----------------------------------------------------------------------------------------- correcciones al README (ronda 1)
def test_seccion_14_comandos_sin_contradiccion(readme):
    s14 = _sec(readme, 14)
    bloques = re.findall(r"```\n(.*?)```", s14, flags=re.S)
    con_nbconvert = [b for b in bloques if "-m nbconvert" in b]
    assert len(con_nbconvert) == 2                                                    # Windows y Linux/Mac
    for b in con_nbconvert:
        assert "10_evaluacion_final_sin_camara.ipynb" in b
        assert "09_modelos" not in b and "09b_" not in b and "08_analisis" not in b    # el bloque principal no reentrena
    assert any(".venv/bin/python" in b for b in bloques) and any(".venv/Scripts/python.exe" in b for b in bloques)
    assert "entrega_EP2.zip" in s14 and ".gitignore" in s14 and "No está en git" in s14
    assert "sha256" in s14.split("Reentrenar")[1]                                      # la advertencia vive junto al reentrenamiento


def test_seccion_6_logaritmos_coinciden_con_la_tabla(readme):
    hip = json.loads((R / "data/06_models/hiperparametros_B.json").read_text(encoding="utf-8"))
    s6 = _sec(readme, 6)
    assert "solo en el no supervisado" not in s6
    for v in hip["preprocesamiento_lr"]["log1p_y_estandarizacion"]:
        assert re.search(rf"\| `{v}` \|[^\n]*\| log1p y estandarización \|", s6), f"{v} deberia decir log1p en la tabla"
    for v in hip["preprocesamiento_lr"]["estandarizacion"]:
        assert re.search(rf"\| `{v}` \|[^\n]*\| estandarización \|", s6)
    assert "`log1p`" in s6.split("Logaritmo y escalado")[1].split("\n")[0]


def test_seccion_8_nota_de_reglas_e_hiperparametros(readme):
    s8 = _sec(readme, 8)
    c09 = pd.read_csv(R / "data/08_reporting/09_comparacion_modelos.csv").set_index("modelo")
    geo = [i for i in c09.index if i.startswith("Regla geometrica")][0]
    assert c09.loc[geo].tolist() == c09.loc["Regla: menos puntos LiDAR"].tolist()   # la nota explica algo que sigue siendo cierto
    assert "Por qué dos filas son idénticas" in s8 and "1e6*(azimut_abs_deg > 105) - num_lidar_points" in s8
    hip = json.loads((R / "data/06_models/hiperparametros_B.json").read_text(encoding="utf-8"))
    coma = lambda x: str(x).replace(".", ",")
    assert "| Regresión logística | C (regularización) |" in s8 and f"| {coma(hip['final']['LR']['cfg']['C'])} |" in s8
    assert "| Random Forest | max_depth |" in s8 and f"| {hip['final']['RF']['cfg']['max_depth']} |" in s8 and f"| {hip['final']['HGB']['cfg']['max_iter']} |" in s8
    assert "Por qué `distancia_m` tiene un odds ratio menor que 1" in s8 and "correlación de Spearman" in s8
    assert "post hoc, no pre-declarado" in s8.split("distancia_m` tiene")[1].split("Calibración")[0]


def test_seccion_9_titular_describe_el_cluster_de_k2(readme):
    s9 = _sec(readme, 9)
    titular = [l for l in s9.splitlines() if l.startswith("> ")][0]
    per = pd.read_csv(R / "data/08_reporting/08_clusters_perfil.csv", index_col=0)
    for _, f in per.iterrows():
        assert f["nombre"] in titular and (f"{f['tasa'] * 100:.1f}".replace(".", ",") + " %") in titular
    assert "Usamos k = 4, que es una exploración y no el k elegido" in s9


def test_seccion_15_pauta_real_y_equipo(readme):
    s15 = _sec(readme, 15)
    assert "puede tener otros" not in readme
    for ie, p in (("IE5", 20), ("IE6", 30), ("IE7", 30), ("IE8", 20)):
        assert re.search(rf"\| {ie}: [^|]+ \| {p} % \|", s15), f"falta {ie} con su ponderacion {p} %"
    assert "`models/` equivale a `data/06_models` por la convención de Kedro" in s15
    assert "Maicol Hernández" in s15 and "Francis Moya" in s15
    for entregable in ("Informe técnico en Markdown", "Notebook .ipynb", "Datos y archivos complementarios", "Carpeta organizada"):
        assert entregable in s15


def test_unidad_de_revision_es_la_caja(readme):
    fb = pd.read_parquet(R / "data/05_model_input/features_B.parquet")
    fb = fb[fb["en_zona_principal"].astype(bool)]
    n_fr = fb.drop_duplicates(["segment_id", "key.frame_timestamp_micros"]).shape[0]
    miles = lambda x: f"{x:,}".replace(",", ".")
    assert "Unidad de revisión: la caja, no el frame" in readme and f"{miles(len(fb))} cajas repartidas en {miles(n_fr)} frames" in readme
    assert "% de cajas revisadas" in readme and "% de frames revisados" not in readme
    assert "no se calcularon ni se midieron" in readme and "SEGUNDOS_POR_REVISION" in readme


def test_tildes_en_etiquetas_de_tablas(readme):
    for sin in ("Regresion logistica", "Regla geometrica", "Isotonica", "Modelo minimo"):
        assert sin not in readme, f"etiqueta sin tilde en el README: {sin}"
    assert "| Regresión logística |" in readme and "| Isotónica |" in readme and "| Regla geométrica (azimut > 105 primero) |" in readme


def test_cabecera_ruta_de_lectura_y_vocabulario(readme):
    cabecera = "\n".join(readme.splitlines()[:16])
    assert "MLY1101" in cabecera and "Fecha:" in cabecera and "Waymo Open Dataset v2" in cabecera
    ruta = [l for l in cabecera.splitlines() if l.startswith("**Lectura rápida:**")][0]
    assert re.findall(r"\[(\d+)\]\(#", ruta) == ["1", "5", "8", "10", "11", "12"]
    assert "recalibrar el corte" in readme and "reponer el corte" not in readme
    assert "secciones [1](#1-resumen)," in ruta and "[Resumen](#1-resumen)" in readme and "\n## 1. Resumen\n" in readme       # el ancla sigue al título «1. Resumen»
    for viejo in ("30 segundos", "Ruta de lectura", "10 minutos de lectura", "1-resumen-en-30-segundos"):
        assert viejo not in readme, f"quedó una referencia a duración de lectura o al ancla antigua: {viejo}"


def test_aclaraciones_de_cifras_y_etiquetas(readme):
    inf_ = pd.read_csv(R / "data/08_reporting/10_influencia.csv")
    reg = pd.read_csv(R / "docs/seleccion_segmentos/registro_verificacion_ep2.csv")
    s1, s10, s11, s4 = _sec(readme, 1), _sec(readme, 10), _sec(readme, 11), _sec(readme, 4)
    assert f"Son {len(inf_)} cálculos sobre los {int(inf_.loc[0, 'segmentos'])} segmentos de test" in s10
    assert "es una lectura post hoc, no pre-declarada" in [l for l in s10.splitlines() if l.startswith("> ")][0]
    assert "criterios escritos después de ver el segmento y antes de calcular la auditoría" in s11
    assert "La diferencia (modelo menos regla)" in s1 and "IC 95 % por bootstrap de segmentos" in s1
    assert readme.count("las brechas por momento del día y por ubicación estaban confundidas con ese segmento") == 1     # el párrafo de equidad no se repite en la sección 13
    desc = reg[reg["resultado"] == "descartado"]
    assert f"los otros {len(desc)} se descartaron" in s4 and "no forman parte de esos" in s4
    assert "Notebook 06 (de EP1, prepara EP2)" in readme and "00 a 05 (EP1), 06 (de EP1, prepara EP2)" in readme
