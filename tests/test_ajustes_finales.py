"""Pruebas de los ajustes finales del README y del informe: archivos congelados, ejecuciones de verificación, IC bimodal, balance de objetivos,
línea EP1 a EP2, sección 14 y número de pruebas. Los valores esperados se calculan aquí desde los archivos, no se escriben a mano."""
import importlib.util as iu
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

R = Path(__file__).resolve().parent.parent
HAY_DATOS = all((R / p).exists() for p in ("data/08_reporting/10_resumen_cifras.json", "data/08_reporting/pytest_resumen.json", "data/08_reporting/ep1_pruebas_cobertura.json", "data/05_model_input/features_B.parquet"))
pytestmark = pytest.mark.skipif(not HAY_DATOS, reason="faltan los archivos de salida de los notebooks (data/ no esta en git)")
TOP = "Regla: menos puntos top"


def _correr(script):
    r = subprocess.run([sys.executable, "-X", "utf8", str(R / "scripts" / script)], cwd=R, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, f"{script} fallo:\n{r.stdout}\n{r.stderr}"


@pytest.fixture(scope="module")
def docs():
    _correr("generar_informe_tecnico.py")
    _correr("generar_readme.py")
    return (R / "README.md").read_text(encoding="utf-8"), (R / "docs" / "informe_tecnico_EP2.md").read_text(encoding="utf-8")


def _sec(texto, n):
    m = re.search(rf"^## {n}\. .*?(?=^## {n + 1}\. |\Z)", texto, flags=re.S | re.M)
    assert m, f"no se encontro la seccion {n}"
    return m.group(0)


def _punto(t):
    return float(str(t).split()[0])


def _n3(x):
    return f"{x:.3f}".replace(".", ",")


def _pct(x):
    return f"{float(x) * 100:.1f}".replace(".", ",") + " %"


def test_archivos_congelados_mismo_numero_en_los_tres_lugares(docs):
    readme, informe = docs
    r = subprocess.run([sys.executable, "-X", "utf8", str(R / "scripts" / "verificar_congelados.py")], cwd=R, capture_output=True, text=True, encoding="utf-8")
    m = re.search(r"coinciden (\d+) de (\d+) archivos", r.stdout)
    assert r.returncode == 0 and m and m.group(1) == m.group(2)
    n = int(m.group(1))
    plan = json.loads((R / "data/06_models/plan_evaluacion_test.json").read_text(encoding="utf-8"))
    nombres = list(plan["sha256"]["archivos"]) + ["features_B.parquet", "plan_evaluacion_test_v1.json"]
    assert n == len(nombres)                                                              # 12 del plan más features_B y el plan v1
    s4 = _sec(informe, 4)
    tabla = s4.split("Archivos congelados (sha256 verificado al inicio del notebook 10)")[1]
    filas = [l for l in tabla.splitlines() if l.startswith("| ") and not l.startswith(("| Archivo", "|---"))]
    assert [l.split("|")[1].strip() for l in filas] == nombres                           # la tabla del informe lista los reales
    assert f": son {n}," in s4 and f"comprueba los mismos {n}" in s4
    assert f"({n} archivos con sha256)" in readme                                         # diagrama de la sección 7 del README


def test_ejecuciones_de_verificacion_en_copias_en_el_informe(docs):
    _, informe = docs
    log = (R / "docs/log_trabajo_ep2.md").read_text(encoding="utf-8").splitlines()
    fechas = []
    for marca in ("VERIFICACION DE REPRODUCIBILIDAD EN COPIA LIMPIA", "VERIFICACION DEL PASO PRINCIPAL DE LA SECCION 14"):
        linea = next(l for l in log if marca in l)
        fechas.append(re.match(r"- \[(\d{4}-\d{2}-\d{2}) ", linea).group(1))
    s12 = _sec(informe, 12)
    assert f"hubo 2 ejecuciones de verificación del notebook 10 en copias fuera del repositorio ({fechas[0]} y {fechas[1]}, fechas del log)" in s12
    assert "con los 15 CSV idénticos por sha256" in s12 and "no cambian el conteo oficial" in s12
    assert "se ejecutó 6 veces sobre el test" in s12                                      # el conteo oficial sigue en 6


def test_readme_resumen_titular_y_nota_del_ic_bimodal(docs):
    readme, _ = docs
    s1 = _sec(readme, 1)
    titular = [l for l in s1.splitlines() if l.startswith("> ")][0]
    assert "en la comparación principal" in titular.lower() and "menos puntos del LiDAR superior (puntos top)" in titular
    r10 = pd.read_csv(R / "data/08_reporting/10_resultado_principal.csv").set_index("metodo")
    _, lo, hi = re.match(r"\s*([\d.]+) \(([\d.]+) a ([\d.]+)\)", r10.loc[TOP, "Fraccion para 80%"]).groups()
    k2 = json.loads((R / "data/08_reporting/10_resumen_cifras.json").read_text(encoding="utf-8"))["K2"]
    miles = lambda x: f"{x:,}".replace(",", ".")
    nota = [l for l in s1.splitlines() if l.startswith("**Nota sobre el IC de la Fracción para 80 %")][0]
    assert f"({_pct(lo)} a {_pct(hi)})" in nota and "bimodal" in nota and "257766998801" in nota
    assert f"en las {miles(k2['n_con_foco'])} réplicas" in nota and f"la mediana es {_pct(k2['mediana_con_foco'])}" in nota
    assert f"en las {miles(k2['n_sin_foco'])} que no lo incluyen es {_pct(k2['mediana_sin_foco'])}" in nota
    assert "diferencias pareadas" in nota and "post hoc" in nota
    assert s1.index(nota) > s1.index("| % de cajas revisadas en el punto A |")             # la nota va bajo la tabla


def test_balance_de_objetivos_en_el_readme(docs):
    readme, _ = docs
    s12 = _sec(readme, 12)
    assert "**Balance de objetivos**" in s12
    filas = [l for l in s12.split("**Balance de objetivos**")[1].split("**Qué esperar.**")[0].splitlines() if re.match(r"\| [1-4]\. ", l)]
    assert len(filas) == 4
    for f in filas:
        celda = f.split("|")[-2].strip()
        assert re.match(r"(sí\. Pasa: |no\. No pasa: |parcial\. Pasa: .+; no pasa: )", celda) and celda.endswith("."), f"formato de ¿Se cumple? incorrecto: {celda[:90]}"
        assert "no no" not in celda.lower() and "ningún" not in celda.split("no pasa:")[0]       # sin dobles negaciones en lo que sí pasa
    c09 = pd.read_csv(R / "data/08_reporting/09_comparacion_modelos.csv").set_index("modelo")
    r10 = pd.read_csv(R / "data/08_reporting/10_resultado_principal.csv").set_index("metodo")
    assert _n3(_punto(c09.loc[TOP, "AUC"])) in filas[0] and _n3(_punto(r10.loc[TOP, "AUC"])) in filas[0]
    assert _punto(r10.loc[TOP, "AUC"]) < 0.70 and "no pasa: en test el AUC queda bajo la meta de 0,70" in filas[0]       # el AUC del test no llega a la meta y la tabla lo dice
    po9 = pd.read_csv(R / "data/08_reporting/09_puntos_operacion.csv")
    po10 = pd.read_csv(R / "data/08_reporting/10_puntos_de_operacion.csv")
    a9 = _punto(po9[(po9["metodo"] == TOP) & po9["punto"].str.startswith("A")].iloc[0]["recall"])
    a10 = _punto(po10[(po10["metodo"] == TOP) & po10["punto"].str.startswith("A")].iloc[0]["recall"])
    estado3 = filas[2].split("|")[-2].strip()
    assert _n3(a9) in filas[2] and _n3(a10) in filas[2] and a10 < 0.75 and not estado3.startswith("sí") and "en test el recall del punto A queda bajo el mínimo de 0,75" in estado3.split("no pasa:")[1]
    cal9 = pd.read_csv(R / "data/08_reporting/09_calibracion.csv").set_index("version")
    cal10 = pd.read_csv(R / "data/08_reporting/10_calibracion.csv", index_col=0)
    assert _n3(float(cal9.loc["Platt", "ECE"])) in filas[3] and _n3(float(cal10.loc["calibrado (Platt)", "ECE"])) in filas[3]
    assert float(cal10.loc["calibrado (Platt)", "ECE"]) > 0.05 and "en test el ECE con Platt es 0,080, sobre el máximo de 0,05" in filas[3].split("no pasa:")[1]


def test_balance_fila_2_ningun_modelo_vale_la_pena_y_ic_de_la_regla(docs):
    readme, _ = docs
    fila = [l for l in _sec(readme, 12).splitlines() if re.match(r"\| 2\. ", l)][0]
    celda = fila.split("|")[-2].strip()
    c9 = json.loads((R / "data/08_reporting/09_resumen_cifras.json").read_text(encoding="utf-8"))
    c10 = json.loads((R / "data/08_reporting/10_resumen_cifras.json").read_text(encoding="utf-8"))
    assert not any(c9["vale_la_pena_principal"].values()) and not any(c10["C"]["vlp_vs_top"].values())     # lo que la fila afirma sale de los JSON
    assert "ningún modelo cumple «vale la pena» frente a la regla, ni en train" in celda and " ni en test (" in celda
    r10 = pd.read_csv(R / "data/08_reporting/10_resultado_principal.csv").set_index("metodo")
    _, lo, hi = re.match(r"\s*([\d.]+) \(([\d.]+) a ([\d.]+)\)", r10.loc[TOP, "Fraccion para 80%"]).groups()
    azar = float(pd.read_csv(R / "data/08_reporting/09_comparacion_modelos.csv").set_index("modelo").loc["Prevalencia (trivial)", "Fraccion para 80%"].split()[0])
    assert float(hi) >= azar                                                                          # el IC del test no queda por debajo del azar
    assert f"en test el IC de la regla top ({_pct(lo)} a {_pct(hi)}) no queda por debajo del {round(azar * 100)} % del azar" in celda


def test_linea_de_ep1_a_ep2_solo_con_hechos_de_los_archivos(docs):
    readme, _ = docs
    linea = [l for l in _sec(readme, 8).splitlines() if l.startswith("**De EP1 a EP2.**")][0]
    ep1 = (R / "docs/README_EP1.md").read_text(encoding="utf-8")
    assert "Random Forest o XGBoost como líneas base, con SMOTE" in ep1 and "Random Forest o XGBoost con SMOTE para `tiene_camara`" in linea
    assert iu.find_spec("xgboost") is None and iu.find_spec("imblearn") is None
    assert "xgboost" not in (R / "requirements.txt").read_text(encoding="utf-8").lower()
    for nb in ("07_decision_target_ep2", "08_analisis_observabilidad_sin_camara", "09_modelos_supervisados_sin_camara", "09b_enmiendas_plan_test_v2", "10_evaluacion_final_sin_camara"):
        celdas = json.loads((R / f"notebooks/{nb}.ipynb").read_text(encoding="utf-8"))["cells"]
        assert "xgboost" not in "".join("".join(c["source"]) for c in celdas if c["cell_type"] == "code").lower()
    assert "XGBoost no se entrenó" in linea and "HistGradientBoostingClassifier" in linea and "`imbalanced-learn` no está instalado" in linea and "20,7 %" in linea
    cw = pd.read_csv(R / "data/08_reporting/09_class_weight.csv", keep_default_na=False).set_index(["modelo", "class_weight"])["mejor PR-AUC interno (promedio de folds)"]
    assert _n3(float(cw[("HGB", "None")])) in linea and _n3(float(cw[("LR", "balanced")])) in linea


def test_seccion_14_python_licencia_y_canal(docs):
    readme, _ = docs
    s14 = _sec(readme, 14)
    version = re.match(r"Python (\S+)", (R / "docs/entorno_ep2.txt").read_text(encoding="utf-8")).group(1)
    frase = f"Python {version} (probado); con otras versiones puede haber diferencias."
    assert frase in s14 and s14.index(frase) < s14.index("```", s14.index("Reproducir el resultado oficial"))      # antes del bloque de comandos
    legal = ("El zip incluye datos derivados y las tablas `camera_to_lidar_box_association` y `waymo_con_target.parquet`, solo para uso académico del docente, "
             "y no debe redistribuirse ni publicarse (licencia no comercial de Waymo).")
    assert legal in s14 and "sin los `lidar_box` crudos" not in s14


def test_frase_de_lidar_box_originales_en_las_secciones_14_y_15(docs):
    readme, _ = docs
    frase = ("los archivos `lidar_box` originales de Waymo no se distribuyen; el zip lleva solo el subconjunto derivado y las tablas de asociación, "
             "para uso académico del docente")
    assert frase in _sec(readme, 14) and frase in _sec(readme, 15)
    assert "los datos crudos de Waymo no se distribuyen" not in readme
    assert "**Desde datos crudos:**" in _sec(readme, 14)                                              # el resto de la sección no cambia


def test_readme_e_informe_dicen_el_numero_actual_de_pruebas_y_la_cobertura(docs):
    readme, informe = docs
    r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "--no-cov"], cwd=R, capture_output=True, text=True, encoding="utf-8")
    n = len([l for l in r.stdout.splitlines() if "::" in l])
    m = re.search(r"(\d+) pasadas, (\d+) falladas, (\d+) omitidas", readme)
    assert m and int(m.group(1)) + int(m.group(2)) + int(m.group(3)) == n, f"el README dice {m.groups() if m else None} y pytest recoge {n} pruebas: correr scripts/medir_pruebas.py y regenerar el README"
    pj = json.loads((R / "data/08_reporting/pytest_resumen.json").read_text(encoding="utf-8"))
    cob = f"{pj['cobertura_total_pct']:.1f}".replace(".", ",")
    frase = f"{pj['pasadas']} pasadas, {pj['falladas']} falladas, {pj['omitidas']} omitidas; cobertura total {cob} %"
    assert frase in readme and frase in informe, "README e informe deben decir lo mismo que pytest_resumen.json (orden: medir_pruebas, informe, README)"
    assert pj["pasadas"] + pj["falladas"] + pj["omitidas"] == n


def test_recomendacion_en_dos_pasos_igual_en_readme_e_informe(docs):
    readme, informe = docs
    L = json.loads((R / "data/08_reporting/10_resumen_cifras.json").read_text(encoding="utf-8"))["L"]
    sp = pd.read_csv(R / "data/08_reporting/10_L_sin_segmento_principal.csv")
    auc_sin = _punto(sp[(sp["metodo"] == TOP) & sp["resultado"].str.startswith("sin")].iloc[0]["AUC"])
    bloque = readme.split("**Recomendación (en una frase).**")[1].split("| Métrica")[0]
    assert "revisar cámara por cámara; recién después, ordenar las cajas con la regla de puntos LiDAR. Siempre con una persona que revisa y decide." in bloque
    for paso in ("- **Paso 1: buscar cámaras con hueco.**", "- **Paso 2: ordenar las cajas de las cámaras sanas.**", "- **Por qué en ese orden.**", "- **Alcance.**"):
        assert paso in bloque
    assert f"donde el AUC de la regla es {_n3(L['auc_foco']['top'])}" in bloque and f"(AUC {_n3(auc_sin)} sin ese segmento; post hoc, no pre-declarado)" in bloque
    assert bloque.strip() in informe                                                                  # mismo texto en el informe
    s12 = _sec(readme, 12)
    assert "1. **Nivel 1 (paso 1): auditar por segmento y cámara.**" in s12 and "2. **Nivel 2 (paso 2): priorizar cajas con la regla por puntos top.**" in s12
    assert "hipótesis post hoc, no pre-declarada; requiere validación con `camera_calibration`" in s12
    assert "Se hace en ese orden porque en una cámara con hueco la regla se equivoca." in s12 and "Se hace en ese orden porque en una cámara con hueco la regla se equivoca." in informe
    for texto in (readme, informe):
        assert "auditar cada segmento por cámara" not in texto and "Dos niveles con una persona" not in texto and "Recomendación en dos niveles" not in texto
    assert "cámara por cámara primero, luego cajas por puntos top" in readme and "cámara por cámara primero, luego cajas por puntos top" in informe


def test_parrafo_por_que_importa_a_escala_coincide_con_los_csv(docs):
    readme, informe = docs
    inv = pd.read_csv(R / "docs/seleccion_segmentos/inventario_segmentos.csv", dtype={"segment_id": str})
    ids = inv["segment_id"].str.extract(r"_(\d+)_(\d+)_(\d+)_(\d+)$").astype(int)           # inicio y fin en segundos y milisegundos
    duraciones = ((ids[2] * 1000 + ids[3]) - (ids[0] * 1000 + ids[1])) / 1000
    assert duraciones.nunique() == 1 and len(ids) == len(inv)                                     # los 798 identificadores
    dur = int(round(duraciones.iloc[0]))
    assert dur == 20
    c9 = json.loads((R / "data/08_reporting/09_resumen_cifras.json").read_text(encoding="utf-8"))
    nb07 = json.loads((R / "notebooks/07_decision_target_ep2.ipynb").read_text(encoding="utf-8"))
    s = next(int(m.group(1)) for c in nb07["cells"] if c["cell_type"] == "code" for m in [re.search(r"^SEGUNDOS_POR_REVISION\s*=\s*(\d+)", "".join(c["source"]), flags=re.M)] if m)
    split = pd.read_csv(R / "data/05_model_input/split_segmentos.csv")
    n_seg = int((split["conjunto"] == "train").sum())
    po9 = pd.read_csv(R / "data/08_reporting/09_puntos_operacion.csv")
    a = po9[(po9["metodo"] == TOP) & po9["punto"].str.startswith("A")].iloc[0]
    recall, pct = _punto(a["recall"]), _punto(a["pct_revisar"])
    n = c9["filas_principal"]
    horas_todo = n * s / 3600
    coma = lambda x: f"{x:.1f}".replace(".", ",")
    miles = lambda x: f"{x:,}".replace(",", ".")
    cifras = [f"Un segmento dura {dur} segundos", f"tiene {miles(len(inv))} segmentos", f"unas {coma(len(inv) * dur / 3600)} horas de video ({miles(len(inv))} × {dur} s)",
              f"({miles(n)} cajas ÷ {n_seg} segmentos) tomaría unas {coma(horas_todo / n_seg)} h", f"ahorraría unas {coma(horas_todo * (recall - pct) / n_seg)} h por segmento"]
    m = json.loads((R / "data/08_reporting/10_resumen_cifras.json").read_text(encoding="utf-8"))["M"]["pos"]["test"]["% de los positivos"]
    cifras.append(f"reúne el {_pct(m)} de los positivos del test")
    for doc in (readme, informe):
        par = [l for l in doc.splitlines() if l.startswith("**Por qué importa a escala.**")]
        assert len(par) == 1
        for c in cifras:
            assert c in par[0], f"falta o difiere en el párrafo de escala: {c}"
        assert "no medido" in par[0] and "no se sostuvo en el test oficial" in par[0] and "miles" not in par[0]
    assert readme.index("**Costo de no usarlo.**") < readme.index("**Por qué importa a escala.**") < readme.index("**Objetivo general.**")
