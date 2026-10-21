"""Genera README.md (presentacion del proyecto EP2) a partir de los archivos de salida del proyecto.

Uso (desde la raiz del repositorio, despues de generar el informe):

    .venv/Scripts/python.exe -X utf8 scripts/generar_informe_tecnico.py
    .venv/Scripts/python.exe -X utf8 scripts/generar_readme.py

Reutiliza las funciones y los datos de scripts/generar_informe_tecnico.py (CSV, JSON, .md y notebooks ejecutados) y extrae bloques del informe
ya generado (docs/informe_tecnico_EP2.md). Ninguna cifra esta escrita a mano. El README de EP1 se conserva en docs/README_EP1.md.
Las pruebas y la cobertura se leen de data/08_reporting/pytest_resumen.json (lo escribe scripts/medir_pruebas.py) y las de EP1 de
data/08_reporting/ep1_pruebas_cobertura.json (lo escribe scripts/medir_pruebas_ep1.py).
"""
import ast
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar_informe_tecnico as inf  # noqa: E402  (carga los mismos archivos que el informe)

R, REP, DOCS = inf.R, inf.REP, inf.DOCS
es, n3, n1, pc, miles = inf.es, inf.n3, inf.n1, inf.pc, inf.miles
BASE_N, MOD_N = inf.BASE_N, inf.MOD_N
C9, C10, PLAN, HIP, M, L, B = inf.C9, inf.C10, inf.PLAN, inf.HIP, inf.M, inf.L, inf.B
REGLA = "regla por puntos top"
INFORME_MD = (DOCS / "informe_tecnico_EP2.md").read_text(encoding="utf-8") if (DOCS / "informe_tecnico_EP2.md").exists() else ""

# Etiquetas con tilde, encabezados y frases compartidas con el informe: se definen en scripts/generar_informe_tecnico.py para que los dos documentos digan lo mismo.
acentuar, tabla, fb_principal, num_es, n2_ = inf.acentuar, inf.tabla, inf.fb_principal, inf.num_es, inf.n2
PY_VERSION = next((x.split()[1] for x in HIP.get('versiones', []) if x.startswith('Python ')), None) or inf.fallar('falta la version de Python en hiperparametros_B.json')
CANAL_ENTREGA = "AVA / Moodle del curso MLY1101 (DuoC UC)"          # canal de entrega indicado por el equipo
SIN_LIDAR_BOX = "los archivos `lidar_box` originales de Waymo no se distribuyen; el zip lleva solo el subconjunto derivado y las tablas de asociación, para uso académico del docente"
PUENTE_06 = "de EP1, prepara EP2"          # una sola redacción para el notebook 06 (EDA de `tiene_camara` sobre los 41 segmentos de EP2)

# Pauta de EP2 de MLY1101 (tabla de indicadores del PDF «EP2_Instrucciones y Pauta PRESENTACIÓN_Estudiante.pdf»): indicador, nombre, ponderación (%), dónde está.
PAUTA_FUENTE = "«Evaluación Parcial N°2» de MLY1101 Machine Learning (archivo «EP2_Instrucciones y Pauta PRESENTACIÓN_Estudiante.pdf»)"
PAUTA_PESO = 40
PAUTA_IE = [
    ("IE5", "Aplicación de la metodología para el desarrollo del modelo", 20, "Secciones 2 a 7", "2 a 6 (CRISP-DM en la 4)", "06 a 08"),
    ("IE6", "Construcción de modelos de aprendizaje supervisado", 30, "Secciones 8 y 10", "8 y 9", "09, 09b y 10"),
    ("IE7", "Implementación de modelos de aprendizaje no supervisado", 30, "Sección 9", "7", "08"),
    ("IE8", "Interpretación del desempeño del modelo", 20, "Secciones 10 a 13", "10 a 12", "10 y 05"),
]


# --------------------------------------------------------------------------------------------- utilidades
def fig(nombre, pie):
    return inf.figura(nombre, pie, prefijo="images")


def slug(titulo):
    t = unicodedata.normalize("NFC", titulo.lower())
    t = re.sub(r"[^\w\s-]", "", t)
    return re.sub(r"\s", "-", t.strip())


def tabla_en(texto, encabezado):
    """Primera tabla Markdown de `texto` cuya primera linea empieza con `encabezado`."""
    lineas = texto.splitlines()
    for i, l in enumerate(lineas):
        if l.startswith(encabezado):
            j = i
            while j < len(lineas) and lineas[j].startswith("|"):
                j += 1
            return "\n".join(lineas[i:j])
    inf.fallar(f"el informe no contiene una tabla que empiece con '{encabezado}'; ejecutar antes scripts/generar_informe_tecnico.py")


def bloque_en(texto, ini, fin):
    if ini not in texto:
        inf.fallar(f"el informe no contiene '{ini}'")
    t = texto[texto.index(ini) + len(ini):]
    return t[: t.index(fin)].strip() if fin in t else t.strip()


def v(df, col_a, val_a, col_b=None, val_b=None, col=None):
    d = df[df[col_a] == val_a]
    if col_b:
        d = d[d[col_b] == val_b]
    return d.iloc[0][col] if col else d.iloc[0]


def punto(txt):
    """Primer numero de una celda tipo '0.862 (0.814 a 0.906)'."""
    return float(str(txt).split()[0])


def ci_txt(txt, como_pct=False):
    m = re.match(r"\s*([\d.\-]+)(?: \(([\d.\-]+) a ([\d.\-]+)\))?", str(txt))
    f = pc if como_pct else n3
    a, b, c = (float(x) if x is not None else None for x in m.groups())
    return f(a) + (f" (IC {f(b)} a {f(c)})" if b is not None else "")


# --------------------------------------------------------------------------------------------- datos comunes
c09 = inf.leer_csv("09_comparacion_modelos.csv")
r10 = inf.leer_csv("10_resultado_principal.csv")
po9 = inf.leer_csv("09_puntos_operacion.csv")
po10 = inf.leer_csv("10_puntos_de_operacion.csv")
sin_p = inf.leer_csv("10_L_sin_segmento_principal.csv")
sin_o = inf.leer_csv("10_L_sin_segmento_operacion.csv")
FOCO = L.get("foco", "?")
SEG_REV = inf.segundos_por_revision()          # verifica 07 (texto y código), 09 y 10
PREV = C9.get("principal", {}).get("Prevalencia (trivial)", {})


def fila_resumen():
    """Valores de la regla top en train, test oficial y test sin el segmento (todos desde CSV)."""
    tr = {"AUC": c09[c09["modelo"] == BASE_N]["AUC"].iloc[0], "F80": c09[c09["modelo"] == BASE_N]["Fraccion para 80%"].iloc[0]}
    pa = po9[(po9["metodo"] == BASE_N) & po9["punto"].str.startswith("A")].iloc[0]
    tr["recall"], tr["pct"] = pa["recall"], pa["pct_revisar"]
    te = {"AUC": r10[r10["metodo"] == BASE_N]["AUC"].iloc[0], "F80": r10[r10["metodo"] == BASE_N]["Fraccion para 80%"].iloc[0]}
    pa = po10[(po10["metodo"] == BASE_N) & po10["punto"].str.startswith("A")].iloc[0]
    te["recall"], te["pct"] = pa["recall"], pa["pct_revisar"]
    sg = sin_p[(sin_p["metodo"] == BASE_N) & sin_p["resultado"].str.startswith("sin")].iloc[0]
    so = sin_o[(sin_o["metodo"] == BASE_N) & (sin_o["punto"] == "A")].iloc[0]
    sn = {"AUC": sg["AUC"], "F80": sg["Fraccion para 80%"], "recall": so["recall sin el segmento"], "pct": so["% a revisar sin el segmento"]}
    return tr, te, sn


TR, TE, SN = fila_resumen()


def encabezados():
    return [
        ("1. Resumen", "resumen"), ("2. Contexto, valor de negocio, objetivos y KPIs", "contexto"), ("3. Qué hicimos en EP1", "ep1"), ("4. Datos", "datos"),
        ("5. EDA y calidad de datos", "eda"), ("6. Preparación y transformación", "preparacion"), ("7. Metodología (CRISP-DM)", "metodologia"), ("8. Modelos supervisados", "supervisados"),
        ("9. Aprendizaje no supervisado", "no_supervisado"), ("10. Evaluación final en el test", "test"), ("11. Hallazgo post hoc: el segmento anómalo y la auditoría por cámara", "posthoc"),
        ("12. Interpretación y recomendaciones", "recomendaciones"), ("13. Ética, sesgos y privacidad", "etica"), ("14. Estructura del repositorio, reproducción y pruebas", "repo"),
        ("15. Mapa de la pauta, referencias, equipo y limitaciones", "pauta")]


TIT = dict((k, t) for t, k in encabezados())
RUTA_RAPIDA = ["resumen", "eda", "supervisados", "test", "posthoc", "recomendaciones"]       # secciones 1, 5, 8, 10, 11 y 12


def h(k):
    return f"## {TIT[k]}"


# --------------------------------------------------------------------------------------------- 0 y 1
def cabecera():
    indice = " · ".join(f"[{t.split('. ', 1)[1].split(',')[0].split(':')[0]}](#{slug(t)})" for t, _ in encabezados())
    ruta = ", ".join(f"[{TIT[k].split('.')[0]}](#{slug(TIT[k])})" for k in RUTA_RAPIDA)
    ruta = ", ".join(ruta.split(", ")[:-1]) + " y " + ruta.split(", ")[-1]
    return f"""# Auditoría de cajas 3D sin par 2D de cámara en Waymo Open Dataset v2

*Una lista priorizada para que una persona revise primero las cajas 3D etiquetadas de peatones y ciclistas que probablemente no tienen su par 2D de cámara.*

**Curso:** MLY1101 Machine Learning · **Evaluación:** Parcial N°2 (EP2) · **Caso:** Waymo Open Dataset v2, target `sin_camara` · **Fecha:** {datetime.now().strftime('%Y-%m-%d')}

[Informe técnico](docs/informe_tecnico_EP2.md) · [Plan de evaluación congelado](docs/plan_evaluacion_test.md) · [Log de trabajo](docs/log_trabajo_ep2.md) · [README de EP1](docs/README_EP1.md)

**Índice:** {indice}

**Lectura rápida:** secciones {ruta}.

*Generado por `scripts/generar_readme.py` el {datetime.now().strftime('%Y-%m-%d %H:%M')}. Cada cifra sale de los CSV, JSON y notebooks ejecutados (`data/08_reporting/`); los resultados post hoc llevan la etiqueta «post hoc, no pre-declarado».*"""


def sec_resumen():
    foco_pos = L["grupos"]["foco"]["sin_camara"] / (L["grupos"]["foco"]["sin_camara"] + L["grupos"]["otros 7 de test"]["sin_camara"])
    par_test = next((p for p in M.get("pares", []) if p.get("grupo") == "test"), {})
    sm = C10.get("J", {}).get("recall_sin_foco", float("nan"))
    ic = B.get("ic", {})
    tabla_res = pd.DataFrame([
        {"Métrica de la regla por puntos top": "AUC", "Train (fuera de fold)": ci_txt(TR["AUC"]), "Test oficial": ci_txt(TE["AUC"]), "Test sin el segmento 257766998801 (post hoc, no pre-declarado)": ci_txt(SN["AUC"])},
        {"Métrica de la regla por puntos top": "Fracción para 80 %", "Train (fuera de fold)": ci_txt(TR["F80"], True), "Test oficial": ci_txt(TE["F80"], True), "Test sin el segmento 257766998801 (post hoc, no pre-declarado)": ci_txt(SN["F80"], True)},
        {"Métrica de la regla por puntos top": "Recall en el punto A", "Train (fuera de fold)": ci_txt(TR["recall"]), "Test oficial": ci_txt(TE["recall"]), "Test sin el segmento 257766998801 (post hoc, no pre-declarado)": ci_txt(SN["recall"])},
        {"Métrica de la regla por puntos top": "% de cajas revisadas en el punto A", "Train (fuera de fold)": ci_txt(TR["pct"], True), "Test oficial": ci_txt(TE["pct"], True), "Test sin el segmento 257766998801 (post hoc, no pre-declarado)": ci_txt(SN["pct"], True)},
    ])
    return f"""{h('resumen')}

> En la comparación principal, la regla de una línea «menos puntos del LiDAR superior (puntos top) primero» ordena bien las cajas sin par en train; en el test oficial ese resultado no se sostiene y ningún modelo supera a la regla.

- **Problema.** Algunas cajas 3D etiquetadas (`lidar_box`) de peatones y ciclistas no tienen su par 2D de cámara, y hoy solo se sabe cuáles son revisándolas una por una. Es como un archivo de expedientes al que a algunos les falta el anexo.
- **Qué hicimos.** Predecimos `sin_camara` ({pc(PREV.get('PR-AUC', float('nan')))} de las cajas de la población principal de train), con validación por segmento, tres modelos contra reglas simples y un test de {len(inf.SPLIT_TEST)} segmentos sellado con un plan congelado (sha256).
- **Resultado oficial (pre-declarado).** Regresión logística frente a la regla: AUC {n3(B['punto'][MOD_N]['AUC'])} contra {n3(B['punto'][BASE_N]['AUC'])}. La diferencia (modelo menos regla) es {n3(B['dA'][0], True)} y su IC 95 % por bootstrap de segmentos, {n3(B['dA'][1], True)} a {n3(B['dA'][2], True)}, incluye 0: el modelo no se distingue de la regla. El punto A (recall objetivo 0,80) dio un recall de {ci_txt(TE['recall'])} y no se sostiene.
- **Hallazgo (post hoc, no pre-declarado).** El segmento `{FOCO}` aporta el {pc(foco_pos)} de los positivos del test; sin él, el AUC de la regla es {ci_txt(SN['AUC'])} y el recall del punto A {n3(sm)}. En ese segmento la cámara {par_test.get('camara', '?')} no tiene pares.
- **Recomendación.** Dos niveles con una persona en el circuito: auditar cada segmento por cámara y, después, priorizar las cajas con la {REGLA}. No reemplaza la revisión.

{tabla(tabla_res)}

{nota_ic_f80()}"""


# --------------------------------------------------------------------------------------------- 2
def sec_contexto():
    n = C9.get("filas_principal", 0)
    horas_todo = n * SEG_REV / 3600
    r_tr = punto(TR["recall"])
    p_tr = punto(TR["pct"])
    hd = C10.get("D", {}).get("horas", {}).get(BASE_N, {})
    obj = bloque_en(INFORME_MD, "### 2.1 Objetivos", "### 2.2 KPIs")
    obj = "\n".join(l for l in obj.splitlines() if not l.startswith("### "))
    kpi = tabla_en(INFORME_MD, "| KPI |")
    valor = pd.DataFrame([
        {"Escenario (train, población principal)": "Revisar todo", "Cajas a revisar": f"{miles(n)} (100 %)", f"Horas con {SEG_REV} s por revisión": n1(horas_todo)},
        {"Escenario (train, población principal)": f"Al azar, hasta el mismo recall ({n3(r_tr)})", "Cajas a revisar": f"{miles(n * r_tr)} ({pc(r_tr)})", f"Horas con {SEG_REV} s por revisión": n1(horas_todo * r_tr)},
        {"Escenario (train, población principal)": f"Regla por puntos top, punto A (recall {n3(r_tr)})", "Cajas a revisar": f"{miles(n * p_tr)} ({pc(p_tr)})", f"Horas con {SEG_REV} s por revisión": n1(horas_todo * p_tr)},
    ])
    return f"""{h('contexto')}

> Quien revisa y valida las etiquetas de percepción gana tiempo si revisa primero las cajas que probablemente no tienen par 2D, pero esa ganancia fue clara en train y no se sostuvo en el test oficial.

**Quién lo usaría.** Un equipo que revisa y audita los datos etiquetados de percepción y necesita saber qué cajas 3D quedaron sin su par 2D antes de entrenar o de comparar métricas por cámara.

**Qué cuesta no hacerlo.** Revisar al azar: para encontrar el 80 % de las cajas sin par hay que revisar {pc(PREV.get('Fraccion para 80%', float('nan')), 0)} de las cajas (valor del azar en `09_comparacion_modelos.csv`). Es como buscar un expediente incompleto abriendo carpetas sin orden.

{obj}

{kpi}

**Valor cuantificado (ilustración con supuestos).** {inf.frase_20s()}

{tabla(valor, raw=True)}

{inf.parrafo_unidad()}

**Lectura honesta en el test.** En el resultado oficial la ganancia no se sostiene: la regla necesita revisar el {pc(punto(TE['F80']), 1)} de las cajas para encontrar el 80 % de las cajas sin par, frente a {pc(PREV.get('Fraccion para 80%', float('nan')), 0)} al azar, y el punto A queda en recall {ci_txt(TE['recall'])}. En el test, el punto A cuesta {n1(hd.get('horas al punto A', float('nan')))} h frente a {n1(hd.get('horas revisando todo', float('nan')))} h de revisar todo, pero con menos recall del prometido. El motivo (un segmento) está en la [sección 11](#{slug(TIT['posthoc'])})."""


# --------------------------------------------------------------------------------------------- 3 EP1
def sec_ep1():
    ep1 = json.loads((REP / "ep1_pruebas_cobertura.json").read_text(encoding="utf-8")) if (REP / "ep1_pruebas_cobertura.json").exists() else {}
    epr = (DOCS / "README_EP1.md").read_text(encoding="utf-8")
    m_nodos = re.search(r"implementa (\d+) nodos", epr)
    n02 = " ".join(inf.celdas_md("02_exploracion_waymo"))
    m_filas = re.search(r"Concatenados dan ([\d.]+) filas en (\d+) segmentos", n02)
    m_pos = re.search(r"balance global es ([\d.]+) positivos de ([\d.]+)", n02)
    if not (m_nodos and m_filas and m_pos and ep1):
        inf.fallar("faltan datos de EP1 (README_EP1.md, notebook 02 o ep1_pruebas_cobertura.json; ejecutar scripts/medir_pruebas_ep1.py)")
    pos, tot = int(m_pos.group(1).replace(".", "")), int(m_pos.group(2).replace(".", ""))
    filas_tabla = {}
    for l in epr.splitlines():
        m = re.match(r"\| \[`(0\d)_[^`]*\.ipynb`\]\([^)]*\) \| (.*) \|$", l)
        if m:
            filas_tabla[m.group(1)] = m.group(2)
    lineas = []
    for p in sorted(inf.NBS.glob("0[0-5]_*.ipynb")):
        pref = p.stem[:2]
        tit = next((l.lstrip("# ").strip() for c in inf.celdas_md(p.stem) for l in c.splitlines() if l.startswith("# ")), p.stem)
        desc = filas_tabla.get(pref, tit)
        desc = re.sub(r"^Desarrollo en detalle de la sección \d+:\s*", "", desc)       # la sección es la del README de EP1, que aquí sería ambigua
        desc = desc[:1].upper() + desc[1:]
        lineas.append(f"- `{p.name}`: {desc.split('. ')[0].rstrip('.')}.")
    return f"""{h('ep1')}

> En EP1 construimos y probamos el pipeline de datos y descubrimos que `tiene_camara` mezclaba la clase del objeto con la cobertura de cámaras; por eso EP2 cambió el target.

**Pipeline de Kedro.** {ep1['nodos_total']} nodos ({ep1['nodos_por_pipeline'].get('preprocesamiento', '?')} de limpieza del CSV sintético y {ep1['nodos_por_pipeline'].get('ingesta_waymo', '?')} de ingesta de Waymo) y {ep1['pruebas_pasadas']} pruebas, todas pasan, con {n1(ep1['cobertura_pct'])} % de cobertura medida en el commit de cierre de EP1 (`scripts/medir_pruebas_ep1.py`). El README de EP1 declara {m_nodos.group(1)} nodos de preprocesamiento (coincide).

**Notebooks 00 a 05 (EP1):**

{chr(10).join(lineas)}

**Notebook 06 ({PUENTE_06}):** `06_eda_y_preparacion_modelamiento.ipynb` repite el EDA de EP1 (target `tiene_camara`) con los {len(inf.SEG[inf.SEG['uso'] == 'supervisado'])} segmentos de EP2 y deja el split por segmento; el cambio de target lo decide el 07.

**Datos de EP1.** {m_filas.group(2)} segmentos reales de Waymo elegidos por contraste, {m_filas.group(1)} detecciones y {pc(pos / tot)} de positivos de `tiene_camara` ({miles(pos)} de {miles(tot)}). La selección de segmentos, la ética y los benchmarks de almacenamiento (Parquet frente a CSV) quedaron en los notebooks 00, 03, 04 y 05.

**Qué aprendimos y qué cambió.** `tiene_camara` en todos los objetos queda dominado por la clase: en train, los vehículos y las señales nunca son positivos {inf.SIN_ARCHIVO.replace('[', '(').replace(']', ')')}. La pregunta con incertidumbre es qué peatones y ciclistas no tienen par: ese es `sin_camara`, el target de EP2 (notebook 07). El detalle de EP1 está en [docs/README_EP1.md](docs/README_EP1.md)."""


# --------------------------------------------------------------------------------------------- 4 y 5
def sec_datos():
    sup = inf.SEG[inf.SEG["uso"] == "supervisado"]
    clus = inf.SEG[inf.SEG["uso"] == "solo_clustering"]
    fb, fbp, folds = inf.tasas_por_fold()
    cont = inf.leer_csv("07_conteos_test.csv")
    pob = pd.DataFrame([
        {"Población": "Principal (azimut absoluto <= 100°)", "Train: filas": len(fbp), "Train: sin_camara": int(fbp["sin_camara"].sum()), "Test: filas": int(cont["filas_B_principal"].sum()), "Test: sin_camara": int(cont["sin_camara_principal"].sum())},
        {"Población": "120° (principal más franja 100-120°)", "Train: filas": len(fb), "Train: sin_camara": int(fb["sin_camara"].sum()), "Test: filas": int(cont["filas_B_120"].sum()), "Test: sin_camara": int(cont["sin_camara_120"].sum())},
    ])
    lluvia = inf.notebooks_que_usan_lluvia()
    desc = inf.REG[inf.REG["resultado"] == "descartado"]
    por_motivo = desc["motivo"].str.extract(r"^([a-z]+ [a-z]+)")[0].value_counts()
    m_ralo = re.search(r"< ([\d.]+)% en frames etiquetados", " ".join(desc["motivo"]))
    m_poca = re.search(r"< (\d+)\)", " ".join(desc["motivo"]))
    if set(inf.REG["resultado"]) != {"seleccionado", "descartado"} or len(desc) + len(sup) != len(inf.REG) or set(clus["segment_id"]) & set(inf.REG["segment_id"]):
        inf.fallar("el registro de verificacion no tiene la forma esperada (41 seleccionados + descartados, y los segmentos de lluvia fuera del registro)")
    seleccion = (f"De {len(inf.REG)} segmentos evaluados (`registro_verificacion_ep2.csv`), {len(sup)} cumplen etiquetado denso y asociación cámara-LiDAR no vacía; los otros {len(desc)} se descartaron: "
                 f"{por_motivo.get('asociacion vacia', 0)} por asociación vacía, {por_motivo.get('etiquetado ralo', 0)} por etiquetado ralo (menos de {es(m_ralo.group(1)) if m_ralo else '?'} % de frames etiquetados) y {por_motivo.get('pocas asociaciones', 0)} por pocas asociaciones (menos de {m_poca.group(1) if m_poca else '?'}). "
                 f"{inf.frase_lluvia()} y "
                 + ("no se usaron en el modelado; solo en un análisis descriptivo post hoc (sección 9)" if not lluvia else "se usaron como se explica en el informe") + ".")
    return f"""{h('datos')}

> Evaluamos {len(inf.REG)} segmentos, usamos {len(sup)} y dejamos {len(inf.SPLIT_TEST)} sellados como test; la población principal excluye la franja de 100 a 120° porque ahí la ausencia de par es geométrica.

- **Selección.** {seleccion}
- **Split por segmento.** {len(inf.SPLIT_TRAIN)} segmentos de train y {len(inf.SPLIT_TEST)} de test: un segmento es una escena de 20 segundos, y si fotogramas vecinos cayeran en lados distintos el modelo «reconocería» la escena. Los 5 folds se estratificaron por `tiene_camara` (el target de EP1), no por `sin_camara`, así que su tasa por fold varía de {pc(folds['tasa de sin_camara'].min())} a {pc(folds['tasa de sin_camara'].max())}.
- **Test sellado.** Los {len(cont)} segmentos de test no se abrieron hasta el notebook 10; antes solo se contaron filas y positivos.

{tabla(pob)}

La población principal tiene {miles(C9.get('filas_principal', 0))} de {miles(C9.get('filas_120', 0))} filas de train. `train.parquet` y `test.parquet` incluyen todas las clases de objeto; el target solo existe para peatones y ciclistas."""


def sec_eda():
    pts = inf.leer_csv("08_tasa_por_puntos.csv").rename(columns={"Unnamed: 0": "puntos"})
    az = inf.leer_csv("08_tasa_por_azimut.csv")
    az = az[az["grupo"] == "todos"]
    fbp = pd.read_parquet(inf.INP / "features_B.parquet")
    fbp = fbp[fbp["en_zona_principal"].astype(bool)]
    tr_prin, tr_fran = fbp["sin_camara"].mean(), float(az.iloc[-1]["tasa"])
    q = pd.qcut(fbp["distancia_m"], 5)
    t_dist = fbp.groupby(q, observed=True)["sin_camara"].mean()
    t_cl = fbp.groupby("es_ciclista")["sin_camara"].agg(["mean", "size"])
    m_obj = re.search(r"el ([\d,]+) % de los objetos mixtos tiene más puntos en los frames con par 2D \(Wilcoxon p = ([\d.e\-]+)\)", inf.RES08)
    if not m_obj:
        inf.fallar("no se encontro en el resumen del 08 la frase de objetos mixtos")
    vars_ = [c for c in inf.CFGB["conjuntos"]["TODAS_B"] if fbp[c].nunique() > 2]
    atip = {}
    for c in vars_:
        q1, q3 = fbp[c].quantile(0.25), fbp[c].quantile(0.75)
        atip[c] = float(((fbp[c] < q1 - 1.5 * (q3 - q1)) | (fbp[c] > q3 + 1.5 * (q3 - q1))).mean())
    cal = pd.DataFrame([
        {"Chequeo": "Nulos en las 16 variables (población principal de train)", "Resultado": str(int(fbp[inf.CFGB['conjuntos']['TODAS_B']].isna().sum().sum()))},
        {"Chequeo": "Duplicados por llave (segmento, frame, objeto)", "Resultado": str(int(fbp.duplicated(['segment_id', 'key.frame_timestamp_micros', 'key.laser_object_id']).sum()))},
        {"Chequeo": "Cajas con cero puntos LiDAR (reales: objetos que el LiDAR casi no vio)", "Resultado": pc(float((fbp['num_lidar_points'] == 0).mean()))},
        {"Chequeo": "Filas conservadas al filtrar frames sin etiquetas (06)", "Resultado": pc(float(inf.leer_csv('reporte_filtro_frames.csv')['filas_despues'].sum() / inf.leer_csv('reporte_filtro_frames.csv')['filas_antes'].sum()))},
        {"Chequeo": "Atípicos (fuera de 1,5 IQR): rango entre variables no binarias", "Resultado": f"de {pc(min(atip.values()))} a {pc(max(atip.values()))} según la variable; no se eliminan"},
    ])
    return f"""{h('eda')}

> Cuatro hallazgos explican casi todo: pocos puntos LiDAR, el borde de 100° del azimut, la distancia y la clase, y que dentro de un mismo objeto el par aparece cuando hay más puntos.

1. **Puntos LiDAR.** La tasa de `sin_camara` baja de {pc(float(pts.iloc[0]['tasa']))} con 0-5 puntos a {pc(float(pts.iloc[-1]['tasa']))} con más de 100. Es como una persona que casi no aparece en la foto: no recibe recuadro.
2. **Azimut y franja 100-120°.** La tasa es {pc(tr_prin)} dentro de 100° y {pc(tr_fran)} entre 100° y 120°: ahí la ausencia de par es en buena parte geométrica y no una laguna de etiquetado.
3. **Distancia y clase.** La tasa va de {pc(float(t_dist.iloc[0]))} en el quintil más cercano a {pc(float(t_dist.iloc[-1]))} en el más lejano (calculado con train). Los ciclistas son pocos: {miles(t_cl.loc[1, 'size'])} filas, con tasa {pc(float(t_cl.loc[1, 'mean']))}.
4. **Dentro de un mismo objeto.** El {m_obj.group(1)} % de los objetos que a veces tienen par y a veces no tienen más puntos en los frames con par (Wilcoxon p = {m_obj.group(2).replace('.', ',')}): el efecto no es solo del tipo de objeto.

{fig('08_tasa_por_puntos_clase_distancia.png', 'Tasa de sin_camara por puntos LiDAR, clase y distancia (08, población de 120°)')}

{fig('08_tasa_por_azimut.png', 'Tasa de sin_camara por azimut: el salto está entre 100° y 120° (08)')}

{fig('08_pareado_objetos_mixtos.png', 'Dentro de los objetos que a veces tienen par: más puntos en los frames con par (08)')}

**Calidad de datos.**

{tabla(cal)}"""


# --------------------------------------------------------------------------------------------- 6 y 7
def sec_prep():
    tv = tabla_en(INFORME_MD, "| Variable |")
    filas = []
    for l in tv.splitlines()[2:]:
        c = [x.strip() for x in l.strip("|").split("|")]
        filas.append({"Variable": c[0], "Definición": c[1], "Tratamiento en la regresión logística": c[4]})
    pre = HIP.get("preprocesamiento_lr", {})
    con_log = [f"`{c}`" for c in pre.get("log1p_y_estandarizacion", [])]
    sin_log = pre.get("estandarizacion", [])
    if not con_log or not sin_log or not all(f["Tratamiento en la regresión logística"].startswith("log1p") == (f"`{f['Variable'].strip('`')}`" in con_log) for f in filas):
        inf.fallar("el tratamiento de la regresion logistica de la tabla del informe no coincide con preprocesamiento_lr de hiperparametros_B.json")
    logs = inf.frase_logaritmos()
    return f"""{h('preparacion')}

> Dieciséis variables de la caja 3D, ninguna del par 2D, escaladas solo con datos de entrenamiento de cada fold.

{tabla(pd.DataFrame(filas))}

- **Variables creadas:** densidad (puntos por volumen), volumen, distancia, azimut y rumbo (seno y coseno). Las variables de oclusión y temporales se probaron en el 08 y no mejoraron el resultado.
- **Logaritmo y escalado:** {logs[:1].upper() + logs[1:]}. El escalado es parte del `Pipeline` de cada fold. No eliminamos atípicos: son objetos reales (cajas lejanas, cajas grandes).
- **Prevención de fuga:** ninguna variable viene del par 2D ni de la asociación; los identificadores (`key.laser_object_id`, marca de tiempo) no son variables; el split es por segmento; el notebook 08 lo comprueba con un `assert`. Más detalle en el [informe](docs/informe_tecnico_EP2.md#3-datos-preparación-y-calidad)."""


def sec_metodo():
    cr = PLAN.get("criterios", {}).get("parametros", {})
    vl, es_, op, ca = cr.get("vale_la_pena", {}), cr.get("estabilidad", {}), cr.get("operacion", {}), cr.get("calibracion", {})
    crisp = inf.tabla_crisp()
    crisp = crisp[["fase", "qué se hizo", "sección y notebook"]].copy()
    crisp["sección y notebook"] = crisp["sección y notebook"].str.replace("Secciones", "Secciones del informe:", regex=False)
    sha = PLAN.get("sha256", {}).get("archivos", {})
    return f"""{h('metodologia')}

> Fijamos los criterios antes de mirar resultados, validamos por segmento y congelamos modelos y umbrales con sha256 antes de abrir el test.

{tabla(crisp)}

```
 Waymo v2 ({len(inf.SPLIT_TRAIN) + len(inf.SPLIT_TEST)} segmentos)           split por segmento ({len(inf.SPLIT_TRAIN)} train / {len(inf.SPLIT_TEST)} test sellado)
         |                                      |
 filtros y variables  ------>  5 folds por segmento (train) ------>  baselines + LR/HGB/RF
 (sin variables del par 2D)         (búsqueda anidada por segmento)           |
                                                                             v
                   criterios fijados antes  ------>  plan de evaluación congelado ({len(inf.archivos_congelados())} archivos con sha256)
                                                                             |
                                                                             v
                                       test ({len(inf.SPLIT_TEST)} segmentos) -> resultado oficial pre-declarado -> apéndices post hoc
```

**Criterios fijados antes.** «Vale la pena»: la fracción para 80 % baja al menos {int(round(abs(vl.get('delta_fraccion80_max', 0)) * 100))} puntos con IC pareado que excluya 0 y el AUC sube al menos {inf.n2(vl.get('delta_auc_min', 0))}. Estabilidad: AUC mínimo por fold de {inf.n2(es_.get('auc_fold_min', 0))} y mediana por segmento de {inf.n2(es_.get('auc_segmento_mediana_min', 0))}. Punto A: recall objetivo {inf.n2(op.get('recall_objetivo', 0))}, sostenido en test si es al menos {inf.n2(C10.get('D', {}).get('tol', 0))}. Calibración: ECE de a lo sumo {inf.n2(ca.get('ece_max', 0))}. Los intervalos son bootstrap por segmentos.

**Por qué baselines simples.** Un modelo complejo solo se justifica si supera a una regla que se explica en una línea; es como justificar un instrumento nuevo frente a medir a ojo. Los baselines son menos puntos LiDAR, menos puntos de la parte alta (la {REGLA}), una regla geométrica y un modelo mínimo de 3 variables."""


# --------------------------------------------------------------------------------------------- 8 y 9
def valores_es(v, f=num_es):
    """Una grilla (lista o muestreo log-uniforme) como texto, con « / » entre valores (la coma es el separador decimal)."""
    if isinstance(v, tuple) and v and v[0] == "log":
        return f"log-uniforme de {num_es(v[1])} a {num_es(v[2])}"
    return " / ".join(dict.fromkeys(f(x) for x in v))


def grillas_09():
    """Grillas y espacios de busqueda leidos del codigo del notebook 09 (GRID_LR, ESPACIO_HGB, ESPACIO_RF, CAP_ITER, folds internos)."""
    nb = json.loads((inf.NBS / "09_modelos_supervisados_sin_camara.ipynb").read_text(encoding="utf-8"))
    celda = next(("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code" and "GRID_LR =" in "".join(c["source"])), None)
    if celda is None:
        inf.fallar("no se encontro en el notebook 09 la celda con GRID_LR")
    env = {}
    for nodo in ast.parse(celda).body:
        if isinstance(nodo, ast.Assign) and isinstance(nodo.targets[0], ast.Name) and nodo.targets[0].id in ("GRID_LR", "ESPACIO_HGB", "ESPACIO_RF", "CAP_ITER"):
            env[nodo.targets[0].id] = eval(compile(ast.Expression(nodo.value), "<nb09>", "eval"), {"__builtins__": {}}, {"loguniform": lambda a, b: ("log", a, b)})
    m_in = re.search(r"GroupKFold\(n_splits=(\d+)\)", celda)
    if len(env) != 4 or not m_in:
        inf.fallar("no se pudieron leer las grillas del notebook 09")
    env["folds_internos"] = int(m_in.group(1))
    return env


def tabla_hiperparametros():
    g = grillas_09()
    fin = HIP["final"]
    peso = lambda v: "sin peso" if v is None else num_es(v)
    filas = []
    cw_lr = [c["class_weight"] for c in g["GRID_LR"]]
    c_lr = sorted({c["C"] for c in g["GRID_LR"]})
    filas += [("Regresión logística", "C (regularización)", valores_es(c_lr), num_es(fin["LR"]["cfg"]["C"])),
              ("Regresión logística", "class_weight", valores_es(cw_lr, peso), peso(fin["LR"]["cfg"]["class_weight"]))]
    eh, ch = g["ESPACIO_HGB"], fin["HGB"]["cfg"]
    rot = {"learning_rate": "learning_rate (tasa de aprendizaje)", "max_leaf_nodes": "max_leaf_nodes (hojas)", "min_samples_leaf": "min_samples_leaf (muestras por hoja)", "l2_regularization": "l2_regularization", "mono": "mono (monotonía)"}
    for k in ("learning_rate", "max_depth", "max_leaf_nodes", "min_samples_leaf", "l2_regularization", "class_weight", "mono"):
        txt = valores_es(eh[k], peso if k == "class_weight" else num_es)
        filas.append(("HGB", rot.get(k, k), txt, peso(ch[k]) if k == "class_weight" else (num_es(ch[k], 3) if isinstance(ch[k], float) else num_es(ch[k]))))
    filas.append(("HGB", "max_iter (iteraciones)", f"de 10 en 10 hasta {g['CAP_ITER']}, por la curva interna", num_es(ch["max_iter"])))
    er, cr_ = g["ESPACIO_RF"], fin["RF"]["cfg"]
    for k in ("max_depth", "min_samples_leaf", "max_features"):
        filas.append(("Random Forest", k, valores_es(er[k]), num_es(cr_[k])))
    conf = {m: sorted({v["configuraciones_evaluadas"] for v in HIP["por_fold"][m].values()}) for m in ("LR", "HGB", "RF")}
    n_cfg = {m: (str(v[0]) if len(v) == 1 else "-".join(str(x) for x in v)) for m, v in conf.items()}
    df = pd.DataFrame(filas, columns=["Modelo", "Hiperparámetro", "Valores buscados", "Elegido (ajuste final en todo train)"])
    pie = (f"Configuraciones evaluadas por fold: regresión logística {n_cfg['LR']} (grilla completa), HGB {n_cfg['HGB']} y Random Forest {n_cfg['RF']} (muestras aleatorias fijas); "
           f"se elige la de mayor PR-AUC con {g['folds_internos']} folds internos por segmento. Los Random Forest usan 200 árboles y sin `class_weight`.")
    return df, pie


def linea_distancia():
    fb = fb_principal()
    coef = inf.leer_csv("09_coeficientes_lr.csv").set_index("variable").loc["distancia_m"]
    rho = fb["distancia_m"].corr(fb["num_lidar_points"], method="spearman")
    q = pd.qcut(fb["distancia_m"], 5)
    t_q = fb.groupby(q, observed=True)["sin_camara"].mean()
    pocos = fb[pd.qcut(fb["num_lidar_points"].rank(method="first"), 3, labels=False) == 0]
    d3 = pd.qcut(pocos["distancia_m"], 3, labels=False)
    cerca, lejos = float(pocos[d3 == 0]["sin_camara"].mean()), float(pocos[d3 == 2]["sin_camara"].mean())
    if not (coef["odds ratio (+1 DE)"] < 1 and rho < -0.5 and cerca > lejos and t_q.iloc[-1] > t_q.iloc[0]):
        inf.fallar("la explicacion de distancia_m (colinealidad con los puntos) ya no se sostiene con los archivos: revisar el README")
    orr, olo, ohi = (es(f"{float(coef[c]):.2f}") for c in ("odds ratio (+1 DE)", "OR lo", "OR hi"))
    return (f"**Por qué `distancia_m` tiene un odds ratio menor que 1.** Vale {orr} (IC {olo} a {ohi}), pero en el EDA (sección 5) la tasa de `sin_camara` sube con la distancia, de {pc(float(t_q.iloc[0]))} a {pc(float(t_q.iloc[-1]))}.\n\n"
            f"La distancia y los puntos LiDAR están muy correlacionados (correlación de Spearman {n3(rho, True)} entre `distancia_m` y `num_lidar_points`): lo lejano tiene pocos puntos. Con los puntos ya en el modelo, la distancia suma en sentido contrario: "
            f"en el tercio de cajas con menos puntos, la tasa baja de {pc(cerca)} entre las más cercanas a {pc(lejos)} entre las más lejanas (cálculo hecho para este README con train, post hoc, no pre-declarado). "
            "Por eso cada coeficiente se lee con las demás variables fijas, no como efecto aislado.")


def sec_modelos():
    comp = c09.rename(columns={"modelo": "Método", "Fraccion para 80%": "Fracción para 80 %"})
    coef = inf.leer_csv("09_coeficientes_lr.csv").head(5)
    coef = coef.assign(**{"OR (+1 DE)": [f"{es(f'{a:.2f}')} ({es(f'{b:.2f}')} a {es(f'{c:.2f}')})" for a, b, c in zip(coef['odds ratio (+1 DE)'], coef['OR lo'], coef['OR hi'])]})[["variable", "OR (+1 DE)", "significativa"]].assign(significativa=lambda d: d["significativa"].map({True: "sí", False: "no"})).rename(columns={"variable": "Variable", "significativa": "Significativa"})
    cal = inf.leer_csv("09_calibracion.csv")[["version", "ECE", "Brier"]]
    d = inf.leer_csv("09_diagnostico_agrupado.csv")
    dl = d[(d["modelo"] == MOD_N) & (d["referencia"] == BASE_N)]
    f_auc = dl[(dl["parte"] == "por fold") & (dl["metrica"] == "AUC")].iloc[0]
    s_auc = dl[dl["parte"] == "por segmento"].iloc[0]
    hip, pie_hip = tabla_hiperparametros()
    return f"""{h('supervisados')}

> En la comparación principal (población principal, fuera de fold), ningún modelo supera a la regla por puntos top con el criterio fijado antes; la regresión logística es el modelo más interpretable y queda como comparación, y la sensibilidad a 120° se resume en la sección 10.

{tabla(comp)}

{inf.nota_regla_geometrica()}

{fig('09_comparacion_modelos.png', 'Comparación de modelos y baselines en train, fuera de fold, con IC por segmentos (09)')}

**Por qué estos algoritmos.** La regresión logística es la referencia lineal; el HGB captura interacciones; el Random Forest da robustez. Elegimos hiperparámetros con búsqueda anidada por segmento y no usamos SMOTE (la prevalencia de {pc(PREV.get('PR-AUC', float('nan')))} no es extrema). Detalle en el [informe](docs/informe_tecnico_EP2.md#8-modelos-supervisados).

{linea_ep1_a_ep2()}

**Hiperparámetros** (valores buscados, tomados del código del notebook 09, y valor elegido, de `hiperparametros_B.json`):

{tabla(hip, raw=True)}

{pie_hip}

**Qué pesa en la regresión logística** (odds ratio por desviación estándar; menos de 1 significa menos probabilidad de `sin_camara`):

{tabla(coef)}

{linea_distancia()}

**Calibración (fuera de fold):**

{tabla(cal)}

{fig('09_calibracion.png', 'Curva de confiabilidad de la regresión logística, cruda y calibrada (09)')}

**Diagnóstico agrupado frente a por fold y por segmento.** El AUC agrupado mezcla las predicciones de cinco modelos (uno por fold) y puede castigar a los modelos más que a las reglas. Por fold, la diferencia de AUC de la regresión logística frente a la regla va de {es(f_auc['rango por fold'])} (IC por segmentos {es(f_auc['IC95% (segmentos)'])}); por segmento, la mediana de la diferencia es {n3(float(s_auc['mediana dif AUC']), True)} (IC {es(s_auc['IC95% mediana'])}). Los IC incluyen 0: el modelo no se distingue de la regla."""


def sec_nosup():
    ns = inf.NS
    sel = inf.leer_csv("08_clusters_seleccion_k.csv").head(4)[["k", "silhouette", "Davies-Bouldin"]]
    per = inf.leer_csv("08_clusters_perfil.csv").rename(columns={"Unnamed: 0": "cluster"})[["cluster", "filas", "tasa", "lo", "hi", "nombre"]].rename(columns={"cluster": "Cluster", "filas": "Filas", "tasa": "Tasa de sin_camara", "lo": "IC inferior", "hi": "IC superior", "nombre": "Perfil"})
    k34 = inf.leer_csv("08_clusters_k3_k4.csv").rename(columns={"Unnamed: 1": "cluster"})
    k4 = k34[k34["k"] == "k4"]
    alto = k4.loc[k4["tasa"].idxmax()]
    iso, est = ns["isolation_forest"], ns["estabilidad_por_segmento"]
    gde, chi = per.sort_values("Filas", ascending=False).iloc[0], per.sort_values("Filas", ascending=False).iloc[1]
    p_gde = float(gde["Filas"]) / float(per["Filas"].sum())
    return f"""{h('no_supervisado')}

> Con k = 2, el {pc(p_gde)} de las cajas cae en un cluster «{gde['Perfil']}» (tasa de `sin_camara` {pc(float(gde['Tasa de sin_camara']))}) y el resto en uno «{chi['Perfil']}» (tasa {pc(float(chi['Tasa de sin_camara']))}); las tasas son muy distintas, pero los clusters no mejoran la predicción.

**Técnicas.** KMeans, mezcla gaussiana (GMM) y agrupamiento jerárquico sobre distancia, azimut, puntos (en logaritmo), densidad, volumen y oclusión. Elegimos k = {ns['k_elegido']} por máximo silhouette de KMeans; el BIC del GMM no se usó porque no es una curva interpretable (covarianzas degeneradas en las variables discretas, confirmado post hoc en el informe).

{tabla(sel)}

**Estabilidad.** ARI medio {n3(est['ari_medio'])} al remuestrear segmentos (mínimo {n3(est['ari_minimo'])}); las tres técnicas coinciden (ARI entre {n3(min(ns['ari_entre_tecnicas'].values()))} y {n3(max(ns['ari_entre_tecnicas'].values()))}).

**Perfiles y cruce con el target (k = 2, IC 95 % por segmentos):**

{tabla(per)}

{fig('08_clusters_tasa.png', 'Tasa de sin_camara por cluster con IC 95 % por segmentos (08)')}

**IsolationForest** marca {miles(iso['cajas_atipicas'])} cajas atípicas ({iso['porcentaje']} %) en {iso['segmentos']} segmentos, con tasa de `sin_camara` de {pc(iso['tasa_sin_camara_atipicas'])} frente a {pc(iso['tasa_sin_camara_resto'])} en el resto.

**Lectura de negocio.** Usamos k = 4, que es una exploración y no el k elegido (el k elegido es {ns['k_elegido']}): con k = 2 el cluster mayoritario promedia una tasa de {pc(float(gde['Tasa de sin_camara']))} y esconde un tramo mucho más alto, que solo aparece al separar más clusters. Con k = 4, el cluster «{alto['nombre']}» reúne {pc(float(alto['filas']) / float(k4['filas'].sum()))} de las cajas y tiene una tasa de {pc(float(alto['tasa']))}: es el tramo de la cola de revisión donde cerca de {round(float(alto['tasa']) * 10)} de cada 10 cajas no tienen par. Los clusters ayudan a explicar y comunicar, no a predecir: la probabilidad media del modelo en ese cluster ({n3(float(alto['prob_media_modelo']))}) ya sigue su tasa.

**Límites.** Los clusters se calcularon con la población de 120°; el análisis con los segmentos de lluvia (post hoc, no pre-declarado) compara cajas con todos los frames contra train con solo los etiquetados y no es una comparación pareja (ver el [informe](docs/informe_tecnico_EP2.md#7-aprendizaje-no-supervisado-notebook-08-sección-d-y-exploración-con-k--3-y-4))."""


# --------------------------------------------------------------------------------------------- 10 y 11
def sensibilidad_120():
    """Párrafo y tabla de la sensibilidad a 120° desde 10_comparacion_120.csv y el apartado H de 10_resumen_cifras.json."""
    c = inf.leer_csv("10_comparacion_120.csv")
    h_ = C10.get("H", {})
    geo = next((b for b in c["base"].unique() if b.startswith("Regla geometrica")), None)
    top = BASE_N
    if geo is None or h_.get("base120_test") != geo:
        inf.fallar("la base de la sensibilidad a 120 grados ya no es la regla geometrica: revisar el parrafo del README")
    vlp = lambda m, b: c[(c["modelo"] == m) & (c["base"] == b)]["vale la pena"].iloc[0].replace("si", "sí")
    cumple_top = [m for m in ("HGB", "Random Forest", MOD_N) if vlp(m, top) == "sí"]
    cumple_geo = [m for m in ("HGB", "Random Forest", MOD_N) if vlp(m, geo) == "sí"]
    robustos = [m for m, v in h_.get("robusto_literal", {}).items() if v]
    if cumple_top != ["HGB", "Random Forest"] or cumple_geo or robustos:
        inf.fallar("la sensibilidad a 120 grados cambio (quien cumple vale la pena frente a cada regla o el criterio robusto): revisar el parrafo del README")
    vista = c.rename(columns={"modelo": "Método", "base": "Frente a", "dFraccion80 (puntos)": "Dif. de Fracción para 80 % (puntos)", "vale la pena": "¿Vale la pena?"}).copy()
    vista["¿Vale la pena?"] = vista["¿Vale la pena?"].str.replace("si", "sí")
    return (f"**Sensibilidad a 120° (secundaria, en el test).** Con la población ampliada (principal más la franja de 100 a 120°) el baseline adecuado es la regla geométrica, que ahí sí se distingue de la de puntos. "
            f"El HGB y el Random Forest cumplen «vale la pena» frente a la regla por puntos top, pero no frente a la regla geométrica; la regresión logística no lo cumple frente a ninguna de las dos. "
            f"El criterio «robusto» del plan (vale la pena en la población principal y en la de 120° frente al mejor baseline de cada una) da ninguno. Es una sensibilidad: no cambia el resultado principal.\n\n"
            f"{tabla(vista)}")


def sec_test():
    res = r10.rename(columns={"metodo": "Método", "Fraccion para 80%": "Fracción para 80 %"})
    pa = po10[po10["punto"].str.startswith("A") & po10["metodo"].isin([BASE_N, MOD_N])][["metodo", "umbral", "recall", "precision", "pct_revisar"]]
    pa = pa.assign(pct_revisar=pa["pct_revisar"].map(lambda x: ci_txt(x, True)), recall=pa["recall"].map(ci_txt), precision=pa["precision"].map(ci_txt)).rename(columns={"metodo": "Método", "pct_revisar": "% de cajas revisadas", "recall": "Recall", "precision": "Precisión", "umbral": "Umbral"})
    inf_ = inf.leer_csv("10_influencia.csv")
    var = inf_["variante"]
    cuenta = {"todos": int((var == "todos los segmentos").sum()), "ambos": int((var == "sin los dos mas grandes").sum()), "loo": int(var.str.startswith("leave-one-out").sum())}
    cuenta["uno"] = int(var.str.startswith("sin ").sum()) - cuenta["ambos"]
    n_seg = int(inf_.loc[var == "todos los segmentos", "segmentos"].iloc[0])
    if sum(cuenta.values()) != len(inf_) or cuenta["loo"] != n_seg:
        inf.fallar("la tabla 10_influencia.csv no tiene la forma esperada (todos, dos 'sin', ambos y leave-one-out)")
    rng = C10.get("F", {})
    l7 = inf.leer_csv("10_L_equidad_sin_segmento.csv")
    l7 = l7[(l7["metodo"] == BASE_N) & (l7["variable"] != "object_type")]
    eq = pd.DataFrame({"Grupo": l7["grupo"], "Segmentos (oficial)": l7["segmentos (oficial)"], "Recall A oficial": l7["recall A (oficial)"], "Recall A sin el segmento (post hoc, no pre-declarado)": l7["recall A (sin el segmento)"]})
    ref = TR
    return f"""{h('test')}

> El resultado oficial pre-declarado es que el modelo no se distingue de la regla y que el punto A no se sostiene; que la caída frente a train se concentra en un segmento es una lectura post hoc, no pre-declarada.

{tabla(res)}

Diferencia de {acentuar(MOD_N)} menos la {REGLA}: AUC {n3(B['dA'][0], True)} (IC {n3(B['dA'][1], True)} a {n3(B['dA'][2], True)}) y Fracción para 80 % {n1(B['dF'][0] * 100, True)} puntos (IC {n1(B['dF'][1] * 100, True)} a {n1(B['dF'][2] * 100, True)}): ambos IC incluyen 0 y «vale la pena» {'no se cumple' if not B.get('vlp') else 'se cumple'}.

{fig('10_resultado_principal.png', 'Resultado principal en test: modelo frente a regla, con IC por segmentos de test (10)')}

**Punto A** (corte fijado con train para un recall de 0,80; sostenido si el recall es al menos {es(C10.get('D', {}).get('tol', 0))}): {sum(C10.get('D', {}).get('sostenido', {}).values())} de {len(C10.get('D', {}).get('sostenido', {}))} métodos lo sostienen.

{tabla(pa)}

{fig('10_puntos_de_operacion.png', 'Puntos de operación A y B de los siete métodos en test (10)')}

**Influencia.** Son {len(inf_)} cálculos sobre los {n_seg} segmentos de test: {cuenta['todos']} con todos, {cuenta['uno']} quitando cada uno de los dos más grandes, {cuenta['ambos']} quitando ambos y {cuenta['loo']} quitando un segmento a la vez (los dos más grandes figuran también entre estos {cuenta['loo']}). La diferencia de AUC entre modelo y regla va de {n3(rng['rng_auc'][0], True)} a {n3(rng['rng_auc'][1], True)} y la de fracción para 80 % de {n1(rng['rng_f80'][0], True)} a {n1(rng['rng_f80'][1], True)} puntos; {'ningún segmento cambia el veredicto' if not rng.get('cambian') else 'cambia al quitar ' + ', '.join(rng['cambian'])}.

{fig('10_influencia.png', 'Influencia de cada segmento en la comparación principal (10)')}

{sensibilidad_120()}

**Equidad descriptiva** (regla top, sin pruebas de hipótesis; Night y Dawn/Dusk tienen un solo segmento de test). {inf.frase_l7()}

{tabla(eq)}

**Por qué el test cae respecto de train.** El AUC de la regla pasa de {n3(punto(ref['AUC']))} en train a {n3(punto(TE['AUC']))} en el test oficial. El AUC agrupado del test mezcla segmentos muy distintos; sin el segmento {FOCO} (post hoc, no pre-declarado) es {n3(punto(SN['AUC']))}. En los modelos únicos del test no hay la penalización de mezclar cinco modelos de los folds, de modo que la comparación con train debe leerse con cuidado."""


def sec_posthoc():
    g = L["grupos"]
    mu = L.get("muchos", {})
    pares = M.get("pares", [])
    pos = M.get("pos", {})
    ptest = next((p for p in pares if p.get("grupo") == "test"), {})
    ptrain = next((p for p in pares if p.get("grupo") == "train"), {})
    return f"""{h('posthoc')}

> *Post hoc, no pre-declarado:* un segmento de San Francisco de día concentra el problema y su cámara {ptest.get('camara', '?')} no tiene pares; la auditoría por cámara encuentra otro caso en train, pero con pocos casos no podemos estimar su frecuencia.

- **El segmento.** `{FOCO}` tiene {miles(g['foco']['filas'])} filas y {miles(g['foco']['sin_camara'])} positivos ({pc(g['foco']['sin_camara'] / (g['foco']['sin_camara'] + g['otros 7 de test']['sin_camara']))} de los del test). El AUC de la regla dentro del segmento es {n3(L['auc_foco']['top'])} y el de la regresión logística {n3(L['auc_foco']['lr'])}.
- **Cajas bien observadas sin par.** {miles(mu['foco']['sin par con >= 100 puntos'])} de {miles(mu['foco']['cajas sin par'])} cajas sin par tienen al menos 100 puntos LiDAR, frente a {miles(mu['otros 7 de test']['sin par con >= 100 puntos'])} de {miles(mu['otros 7 de test']['cajas sin par'])} en los otros 7 segmentos de test: la regla las ordena como si tuvieran par.
- **Cámaras.** La cámara {ptest.get('camara', '?')} tiene una tasa de pares de {n3(ptest.get('tasa', float('nan')))} dentro de su rango de azimut en ese segmento. La auditoría por cámara en {M.get('n_seg', '?')} segmentos (criterios escritos después de ver el segmento y antes de calcular la auditoría) halla {M.get('n_pares', '?')} pares (segmento, cámara) con hueco: uno en train (cámara {ptrain.get('camara', '?')}) y uno en test; las celdas con hueco reúnen el {pc(pos['test']['% de los positivos'])} de los positivos del test y el {pc(pos['train']['% de los positivos'])} de train.
- **Sin el segmento (post hoc, no pre-declarado).** AUC de la regla {ci_txt(SN['AUC'])}, recall del punto A {ci_txt(SN['recall'])}.

{fig('10_M_mapa_calor.png', 'Tasa de pares por segmento y cámara; X marca los pares con hueco (post hoc, no pre-declarado, 10)')}

**Advertencias.** Los criterios del apéndice se escribieron después de ver el segmento, así que no confirman el hallazgo de forma independiente; los dos casos son de San Francisco de día; el hueco puede ser de etiquetado o de los datos de esa cámara y con estos archivos no se distingue; los rangos de azimut por cámara son empíricos."""


# --------------------------------------------------------------------------------------------- 12 y 13
def lo_hi(txt):
    """(punto, inferior, superior) de una celda tipo '0.790 (0.148 a 0.883)'."""
    m = re.match(r"\s*([\d.\-]+) \(([\d.\-]+) a ([\d.\-]+)\)", str(txt))
    return tuple(float(x) for x in m.groups())


def nota_ic_f80():
    """Nota bajo la tabla del resumen: el IC de la Fracción para 80 % del test es bimodal (celdas K.2 del notebook 10)."""
    _, lo, hi = lo_hi(TE["F80"])
    k2 = C10.get("K2", {})
    m_ic = re.search(r"\(([\d,]+ % a [\d,]+ %)\)", k2.get("texto", ""))
    if not k2 or not m_ic or "bimodal" not in k2["texto"]:
        inf.fallar("falta la lectura K2 del notebook 10 (IC bimodal de la Fracción para 80 %) en 10_resumen_cifras.json")
    return (f"**Nota sobre el IC de la Fracción para 80 % del test ({pc(lo)} a {pc(hi)}).** Es muy ancho y bimodal: depende de si la réplica del bootstrap por segmentos incluye el segmento `{FOCO}`. "
            f"El notebook 10 (K.2) lo midió para la regresión logística (IC {m_ic.group(1)}): en las {miles(k2['n_con_foco'])} réplicas que incluyen el segmento la mediana es {pc(k2['mediana_con_foco'])} y en las {miles(k2['n_sin_foco'])} que no lo incluyen es {pc(k2['mediana_sin_foco'])}. "
            f"Para la regla top el notebook no desglosa las réplicas; la tabla muestra una separación del mismo tipo: {ci_txt(TE['F80'], True).split(' (')[0]} con el segmento y {ci_txt(SN['F80'], True).split(' (')[0]} sin él (post hoc, no pre-declarado). "
            "Por eso las conclusiones se apoyan en las diferencias pareadas modelo menos regla y no en el IC de un método solo.")


def linea_ep1_a_ep2():
    """Reconcilia la propuesta de EP1 (README_EP1.md, sección 6) con lo hecho en EP2; solo afirma lo que está en los archivos."""
    import importlib.util as iu
    epr = (DOCS / "README_EP1.md").read_text(encoding="utf-8")
    m = re.search(r"Random Forest o XGBoost como líneas base, con SMOTE[^|]*?\((\d+,\d)% de positivos\)", epr)
    if not m:
        inf.fallar("no se encontro en docs/README_EP1.md la propuesta de Random Forest o XGBoost con SMOTE")
    codigo_07_10 = ""
    for nb in ("07_decision_target_ep2", "08_analisis_observabilidad_sin_camara", "09_modelos_supervisados_sin_camara", "09b_enmiendas_plan_test_v2", "10_evaluacion_final_sin_camara"):
        d = json.loads((inf.NBS / f"{nb}.ipynb").read_text(encoding="utf-8"))
        codigo_07_10 += "\n".join("".join(c["source"]) for c in d["cells"] if c["cell_type"] == "code")
    reqs = (R / "requirements.txt").read_text(encoding="utf-8").lower()
    nb06 = json.loads((inf.NBS / "06_eda_y_preparacion_modelamiento.ipynb").read_text(encoding="utf-8"))
    spw = next((x.group(1) for c in nb06["cells"] if c["cell_type"] == "code" for o in c.get("outputs", []) for x in [re.search(r"scale_pos_weight para XGBoost: ([\d.]+)", "".join(o.get("text", [])))] if x), None)
    if "xgboost" in codigo_07_10.lower() or "xgboost" in reqs or iu.find_spec("xgboost") or iu.find_spec("imblearn") or spw is None:
        inf.fallar("XGBoost o imbalanced-learn aparecen en el entorno o en los notebooks 07 a 10, o falta el scale_pos_weight del 06: revisar la linea EP1 a EP2 del README")
    cw = inf.leer_csv("09_class_weight.csv", keep_default_na=False).set_index(["modelo", "class_weight"])["mejor PR-AUC interno (promedio de folds)"]
    return (f"**De EP1 a EP2.** El README de EP1 (sección 6) proponía Random Forest o XGBoost con SMOTE para `tiene_camara` ({m.group(1)} % de positivos). En EP2 el target pasó a `sin_camara`, con una prevalencia de {pc(PREV.get('PR-AUC', float('nan')))} en la población principal, "
            f"y comparamos regresión logística, HGB (`HistGradientBoostingClassifier`, el boosting de árboles de scikit-learn) y Random Forest. No usamos SMOTE: evaluamos `class_weight` en vez de sobremuestrear "
            f"(HGB {n3(float(cw[('HGB', 'None')]))} sin peso frente a {n3(float(cw[('HGB', 'balanced')]))} balanceado; regresión logística {n3(float(cw[('LR', 'None')]))} frente a {n3(float(cw[('LR', 'balanced')]))}) e `imbalanced-learn` no está instalado en el entorno. "
            f"XGBoost no se entrenó: no está instalado, no figura en `requirements.txt` ni en el código de los notebooks 07 a 10; el 06 solo imprime un `scale_pos_weight` de {es(spw)} para `tiene_camara`.")


def balance_objetivos():
    """Tabla de los 4 objetivos de la sección 2: resultado en train (fuera de fold), en el test oficial y si se cumple, todo leído de CSV y JSON."""
    v, cal9, cal10, fold, seg9, seg10 = inf._kpi_celdas()
    dec = {r["criterio"]: r for _, r in inf.DEC[inf.DEC["target"] == "B"].iterrows()}
    num = lambda x: float(str(x).replace(">= ", "").split()[0])
    meta_auc, meta_pr = num(dec["AUC (todas las variables)"]["umbral"]), num(dec["PR-AUC - prevalencia"]["umbral"])
    cr = PLAN["criterios"]["parametros"]
    est, ope, cal = cr["estabilidad"], cr["operacion"], cr["calibracion"]
    tol = C10["D"]["tol"]
    prev = {"train": PREV["PR-AUC"], "test": float(cal10["prevalencia"].iloc[0])}
    azar = PREV["Fraccion para 80%"]
    ms = (BASE_N, MOD_N)
    p = lambda tabla_, m, col: punto(v[(tabla_, m)][col])
    f80 = {"train": lo_hi(v[("c9", BASE_N)]["Fraccion para 80%"]), "test": lo_hi(v[("r10", BASE_N)]["Fraccion para 80%"])}
    seg_te = {BASE_N: float(seg10["AUC regla top"].median()), MOD_N: float(seg10["AUC regresion logistica"].median())}
    brechas = inf.leer_json(REP / "09_equidad_brechas.json").get("brechas", [])
    eq10 = inf.leer_csv("10_equidad.csv")
    ece = {"train": float(cal9.loc["Platt", "ECE"]), "test": float(cal10.loc["calibrado (Platt)", "ECE"])}
    dF = B["dF"]
    vlp_train, vlp_test = C9.get("vale_la_pena_principal", {}), C10.get("C", {}).get("vlp_vs_top", {})
    vlp_ok = any(vlp_train.values()) or any(vlp_test.values())
    extra_test = ", incluido el modelo mínimo" if any(k.startswith("Modelo minimo") for k in vlp_test) else ""
    vlp_txt = (f"ningún modelo cumple «vale la pena» frente a la regla, ni en train ({len(vlp_train)} modelos) ni en test ({len(vlp_test)} modelos{extra_test})" if not vlp_ok
               else "algún modelo cumple «vale la pena» frente a la regla (revisar 09_resumen_cifras.json y 10_resumen_cifras.json)")
    n_br = sum(1 for b in brechas if not (b["auc_incluye_0"] and b["recall_incluye_0"]))
    tabla_pop = {"train": "c9", "test": "r10"}
    en = {"train": "en train", "test": "en test"}
    par = lambda a, b: f"regla top {n3(a)}; LR {n3(b)}"
    ent = lambda ok, si, no: (bool(ok), si if ok else no)          # (cumple, frase que dice qué pasa o qué no pasa, con las cifras)
    chequeos = {1: [], 2: [], 3: [], 4: []}
    for pop in ("train", "test"):
        aucs = [p(tabla_pop[pop], m, "AUC") for m in ms]
        prs = [p(tabla_pop[pop], m, "PR-AUC") - prev[pop] for m in ms]
        chequeos[1].append(ent(all(a >= meta_auc for a in aucs), f"{en[pop]} el AUC alcanza la meta de {n2_(meta_auc)} ({par(*aucs)})", f"{en[pop]} el AUC queda bajo la meta de {n2_(meta_auc)} ({par(*aucs)})"))
        chequeos[1].append(ent(all(x >= meta_pr for x in prs), f"{en[pop]} la diferencia entre PR-AUC y prevalencia alcanza la meta de {n2_(meta_pr)} ({par(*prs)})",
                               f"{en[pop]} la diferencia entre PR-AUC y prevalencia queda bajo la meta de {n2_(meta_pr)} ({par(*prs)})"))
        punto_f, inf_f, sup_f = f80[pop]
        chequeos[2].append(ent(sup_f < azar, f"{en[pop]} la regla top necesita revisar el {pc(punto_f)} de las cajas (IC {pc(inf_f)} a {pc(sup_f)}), por debajo del {pc(azar, 0)} del azar",
                               f"{en[pop]} el IC de la regla top ({pc(inf_f)} a {pc(sup_f)}) no queda por debajo del {pc(azar, 0)} del azar"))
    chequeos[2].append((vlp_ok, vlp_txt))
    rec9, rec10 = [p("po9", m, "recall") for m in ms], [p("po10", m, "recall") for m in ms]
    chequeos[3] = [ent(all(r >= ope["recall_objetivo"] for r in rec9), f"en train el corte A se fijó con un recall sobre el objetivo de {n2_(ope['recall_objetivo'])} ({par(*rec9)})",
                       f"en train el recall del corte A queda bajo el objetivo de {n2_(ope['recall_objetivo'])} ({par(*rec9)})"),
                   ent(all(r >= tol for r in rec10), f"en test el recall del punto A alcanza el mínimo de {n2_(tol)} ({par(*rec10)})", f"en test el recall del punto A queda bajo el mínimo de {n2_(tol)} ({par(*rec10)})")]
    minimos = [float(fold[m].min()) for m in ms]
    chequeos[4].append(ent(all(x >= est["auc_fold_min"] for x in minimos), f"en train el AUC mínimo por fold alcanza {n2_(est['auc_fold_min'])} ({par(*minimos)})", f"en train el AUC mínimo por fold queda bajo {n2_(est['auc_fold_min'])} ({par(*minimos)})"))
    for pop in ("train", "test"):
        medianas = [float(seg9.loc[m, "mediana"]) if pop == "train" else seg_te[m] for m in ms]
        chequeos[4].append(ent(all(x >= est["auc_segmento_mediana_min"] for x in medianas), f"{en[pop]} la mediana del AUC por segmento alcanza {n2_(est['auc_segmento_mediana_min'])} ({par(*medianas)})",
                               f"{en[pop]} la mediana del AUC por segmento queda bajo {n2_(est['auc_segmento_mediana_min'])} ({par(*medianas)})"))
    for pop in ("train", "test"):
        chequeos[4].append(ent(ece[pop] <= cal["ece_max"], f"{en[pop]} el ECE con Platt es {n3(ece[pop])}, dentro del máximo de {n2_(cal['ece_max'])}", f"{en[pop]} el ECE con Platt es {n3(ece[pop])}, sobre el máximo de {n2_(cal['ece_max'])}"))
    ic_test = any(("IC" in c or c in ("lo", "hi")) for c in eq10.columns)
    chequeos[4].append(ent(len(brechas) > 0, f"en train las brechas por momento del día y ubicación se calcularon con su IC ({len(brechas)} brechas; " + ("ninguna excluye 0)" if n_br == 0 else f"{n_br} excluyen 0)"),
                           "en train las brechas por momento del día y ubicación no se calcularon con su IC"))
    chequeos[4].append(ent(ic_test, "en test las brechas se calculan con su IC", "en test las brechas son descriptivas y no llevan IC"))

    def estado(k):
        res = [ok for ok, _ in chequeos[k]]
        pasa, falla = [t for ok, t in chequeos[k] if ok], [t for ok, t in chequeos[k] if not ok]
        if all(res):
            return "sí. Pasa: " + "; ".join(pasa) + "."
        if not any(res):
            return "no. No pasa: " + "; ".join(falla) + "."
        return "parcial. Pasa: " + "; ".join(pasa) + "; no pasa: " + "; ".join(falla) + "."

    filas = [
        {"Objetivo (sección 2)": "1. Predecir `sin_camara`", "Train (fuera de fold)": f"AUC: regla top {n3(p('c9', BASE_N, 'AUC'))}, LR {n3(p('c9', MOD_N, 'AUC'))}; PR-AUC menos prevalencia: {n3(p('c9', BASE_N, 'PR-AUC') - prev['train'])}, {n3(p('c9', MOD_N, 'PR-AUC') - prev['train'])}",
         "Test oficial": f"AUC: regla top {n3(p('r10', BASE_N, 'AUC'))}, LR {n3(p('r10', MOD_N, 'AUC'))}; PR-AUC menos prevalencia: {n3(p('r10', BASE_N, 'PR-AUC') - prev['test'])}, {n3(p('r10', MOD_N, 'PR-AUC') - prev['test'])}", "¿Se cumple?": estado(1)},
        {"Objetivo (sección 2)": "2. Reducir la fracción para 80 % frente al azar y a la regla", "Train (fuera de fold)": f"Regla top {pc(f80['train'][0])} (IC {pc(f80['train'][1])} a {pc(f80['train'][2])}) frente a {pc(azar, 0)} al azar; LR {pc(p('c9', MOD_N, 'Fraccion para 80%'))}",
         "Test oficial": f"Regla top {pc(f80['test'][0])} (IC {pc(f80['test'][1])} a {pc(f80['test'][2])}); LR menos regla {n1(dF[0] * 100, True)} puntos (IC {n1(dF[1] * 100, True)} a {n1(dF[2] * 100, True)})", "¿Se cumple?": estado(2)},
        {"Objetivo (sección 2)": "3. Punto de operación con recall objetivo", "Train (fuera de fold)": f"Regla top: recall {n3(p('po9', BASE_N, 'recall'))} con {pc(p('po9', BASE_N, 'pct_revisar'))} de las cajas; LR {n3(p('po9', MOD_N, 'recall'))}",
         "Test oficial": f"Regla top: recall {n3(p('po10', BASE_N, 'recall'))} con {pc(p('po10', BASE_N, 'pct_revisar'))} de las cajas; LR {n3(p('po10', MOD_N, 'recall'))}", "¿Se cumple?": estado(3)},
        {"Objetivo (sección 2)": "4. Estabilidad, calibración y equidad", "Train (fuera de fold)": (f"AUC mínimo por fold: {n3(float(fold[BASE_N].min()))} (regla), {n3(float(fold[MOD_N].min()))} (LR); mediana por segmento: {n3(float(seg9.loc[BASE_N, 'mediana']))}, {n3(float(seg9.loc[MOD_N, 'mediana']))}; "
                                                                           f"ECE con Platt {n3(ece['train'])}; {len(brechas)} brechas con IC, {'ninguna excluye 0' if n_br == 0 else str(n_br) + ' excluyen 0'}"),
         "Test oficial": f"Sin folds; mediana por segmento: {n3(seg_te[BASE_N])}, {n3(seg_te[MOD_N])}; ECE con Platt congelado {n3(ece['test'])}; brechas descriptivas, sin IC", "¿Se cumple?": estado(4)},
    ]
    return pd.DataFrame(filas)


def sec_reco():
    ob = C10.get("D", {}).get("OP", {}).get(f"{BASE_N} | B", {})
    rb = ob.get("recall", [float("nan")] * 3)
    recall_b = f"{n3(rb[0])} (IC {n3(rb[1])} a {n3(rb[2])})"
    return f"""{h('recomendaciones')}

> Usar la {REGLA} para priorizar la revisión humana, precedida de una auditoría por segmento y cámara, y no como reemplazo de la revisión.

1. **Nivel 1: auditar por segmento y cámara.** Para cada segmento nuevo, calcular la tasa de pares de cada cámara dentro de su rango de azimut y marcar las que caen muy por debajo de su mediana. Detecta lo que la regla no ve (hipótesis post hoc, no pre-declarada; requiere validación con `camera_calibration`).
2. **Nivel 2: priorizar cajas con la {REGLA}** en los segmentos sin hueco, con una persona en el circuito.

**Balance de objetivos** (metas de la [sección 2](#{slug(TIT['contexto'])}); «sí» si pasan todos los chequeos, «no» si no pasa ninguno y «parcial» si pasan algunos; las metas de AUC y PR-AUC son las de train y se aplican también al test como referencia):

{tabla(balance_objetivos(), raw=True)}

**Qué esperar.** Con el corte A: en train, recall {ci_txt(TR['recall'])} revisando {pc(punto(TR['pct']))} de las cajas; en el test oficial, recall {ci_txt(TE['recall'])} revisando {pc(punto(TE['pct']))}. Con el corte B (20 % de revisión): recall {recall_b} en test.

- **Monitoreo.** Vigilar el recall por segmento (no solo el promedio), la tasa de `sin_camara` y la tasa de pares de cada cámara; recalibrar el corte si el recall por segmento baja de {es(C10.get('D', {}).get('tol', 0))}.
- **Datos que ayudarían.** `camera_calibration` (validar el borde de 100° y los rangos por cámara), más segmentos, más ciclistas y etiquetas por cámara.

> **Lo que NO afirmamos.** Que `sin_camara` mida visibilidad física; que el resultado generalice más allá de {len(inf.SPLIT_TEST)} segmentos de test; nada sólido sobre ciclistas ni sobre Night y Dawn/Dusk (un segmento cada uno); que el hueco de cámara sea de etiquetado y no de los datos de esa cámara; ni que un modelo supere a la regla, porque con el criterio fijado antes no ocurrió."""


def sec_etica():
    e9 = inf.leer_csv("09_equidad.csv")
    sf = n3(float(e9[e9["grupo"] == "location_sf"]["recall_A"].iloc[0]))
    phx = n3(float(e9[e9["grupo"] == "location_phx"]["recall_A"].iloc[0]))
    return f"""{h('etica')}

> Usamos solo cajas 3D y tablas de pares, con licencia que prohíbe redistribuir, y el principal riesgo ético no es la privacidad sino el uso: esto no es una alerta de seguridad.

- **Privacidad.** Usamos `lidar_box` y `camera_to_lidar_box_association`, sin imágenes. Según el notebook 05 no hay identificadores directos; el riesgo es la reidentificación indirecta (`key.laser_object_id` más la marca de tiempo), por eso esos campos no son variables del modelo. El 05 indica que la licencia es no comercial y prohíbe redistribuir, y por eso `data/` está en `.gitignore`.
- **Sesgos medidos.** Ubicación, momento del día y ciclistas (informe, secciones 9 y 11; en train el recall del punto A de la regresión logística es {sf} en San Francisco y {phx} en Phoenix). Las brechas por momento del día y por ubicación del test oficial estaban confundidas con un solo segmento (post hoc, no pre-declarado); las cifras están en la [sección 10](#{slug(TIT['test'])}).
- **Riesgo de uso.** `sin_camara` es cobertura de etiquetado, no visibilidad física: una persona revisa; nunca se decide nada dentro de un vehículo con esto."""


# --------------------------------------------------------------------------------------------- 14 y 15
def sec_repo():
    pj = json.loads((REP / "pytest_resumen.json").read_text(encoding="utf-8")) if (REP / "pytest_resumen.json").exists() else {}
    if not pj:
        inf.fallar("falta data/08_reporting/pytest_resumen.json; ejecutar scripts/medir_pruebas.py")
    ign = [l for l in inf.GITIGNORE.splitlines() if l.startswith("data/") or l.startswith("entrega_EP2")]
    zip_ = R / "entrega_EP2.zip"
    paquete_mb = f", unos {int(round(zip_.stat().st_size / 1e7)) * 10} MB" if zip_.exists() else ""
    return f"""{h('repo')}

> Todo se regenera con scripts desde datos derivados; {SIN_LIDAR_BOX}.

```
waymo-evaluacion/
├── README.md                    este archivo (lo genera scripts/generar_readme.py)
├── requirements.txt             entorno (versiones de docs/entorno_ep2.txt más kedro, pytest y nbconvert)
├── conf/                        catálogo y parámetros de Kedro
├── src/waymo_evaluacion/        pipelines de ingesta_waymo y preprocesamiento
├── notebooks/                   00 a 05 (EP1), 06 ({PUENTE_06}), 07 target, 08 datos y no supervisado, 09 modelos, 09b plan v2, 10 evaluación
├── scripts/                     generar_informe_tecnico, generar_readme, extracciones del 08 y del 09, diagnóstico post hoc, empaquetar_entrega
├── tests/                       pruebas de pipelines, del informe y del README
├── docs/                        informe técnico, plan de evaluación congelado (v1 y v2), log de trabajo, README de EP1
├── images/                      figuras, con el número del notebook que las genera
└── data/                        (fuera de git) 01_raw a 08_reporting; 06_models hace de models/
```

**El paquete `entrega_EP2.zip`.** Lo arma `scripts/empaquetar_entrega.py` y queda en la raíz del repositorio (carpeta interior `waymo-evaluacion-EP2/`){paquete_mb}. No está en git, porque figura en `.gitignore` (es un archivo grande y `data/` se ignora por la licencia no comercial de Waymo), así que se entrega aparte del repositorio, por el {CANAL_ENTREGA}.

Trae el código, los notebooks ejecutados, `docs/`, `images/` y los datos derivados mínimos para re-ejecutar (`data/05_model_input`, `data/06_models`, `data/08_reporting` y las predicciones). El zip incluye datos derivados y las tablas `camera_to_lidar_box_association` y `waymo_con_target.parquet`, solo para uso académico del docente, y no debe redistribuirse ni publicarse (licencia no comercial de Waymo).

**Reproducir el resultado oficial: ejecutar el notebook 10 con los modelos congelados.** Python {PY_VERSION} (probado); con otras versiones puede haber diferencias. Se crea un kernel propio dentro del entorno para que Jupyter no use otro Python de la máquina. Windows (Git Bash o PowerShell):

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m ipykernel install --prefix .venv --name ep2
.venv/Scripts/python.exe -X utf8 scripts/verificar_congelados.py
.venv/Scripts/python.exe -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=ep2 notebooks/10_evaluacion_final_sin_camara.ipynb
.venv/Scripts/python.exe -X utf8 scripts/generar_informe_tecnico.py
.venv/Scripts/python.exe -X utf8 scripts/generar_readme.py
```

Linux y Mac (no los probamos; son los mismos pasos con el ejecutable del entorno):

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m ipykernel install --prefix .venv --name ep2
.venv/bin/python scripts/verificar_congelados.py
.venv/bin/python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=ep2 notebooks/10_evaluacion_final_sin_camara.ipynb
.venv/bin/python scripts/generar_informe_tecnico.py
.venv/bin/python scripts/generar_readme.py
```

`verificar_congelados.py` comprueba los sha256 del plan v2 antes de ejecutar el 10, que hace la misma comprobación. En la verificación en copia limpia, el 10 dio los 15 CSV idénticos por sha256 a los de la primera ejecución; repetirlo es una re-ejecución sobre el test, no una evaluación nueva.

**Reentrenar (opcional; no hace falta para el resultado oficial).** Los notebooks 08 (variables), 09 (modelos) y 09b (plan v2) se pueden volver a ejecutar, pero **sobrescriben** `data/05_model_input` y `data/06_models`, incluidos los modelos y el plan congelados. Hay que hacerlo en una copia (descomprimir el zip en otra carpeta), con los mismos comandos `nbconvert` sobre `notebooks/08_analisis_observabilidad_sin_camara.ipynb`, `notebooks/09_modelos_supervisados_sin_camara.ipynb` y `notebooks/09b_enmiendas_plan_test_v2.ipynb`, en ese orden.

**Advertencia sobre el sha256:** en la verificación en copia limpia, el 09 reentrenó los modelos con archivos idénticos, pero un umbral del Random Forest cambió en el último decimal; el sha256 de `hiperparametros_B.json` dejó de coincidir con el del plan y el 09b y el 10 se detuvieron. Si se reentrena, hay que devolver los archivos congelados antes del 10.

**Desde datos crudos:** descargar los segmentos de Waymo (licencia no comercial) y ejecutar `kedro run`, como se explica en el [README de EP1](docs/README_EP1.md).

**Pruebas y cobertura** (`scripts/medir_pruebas.py`): {pj['pasadas']} pasadas, {pj['falladas']} falladas, {pj['omitidas']} omitidas; cobertura total {n1(pj['cobertura_total_pct'])} %. Se ejecutan con `.venv/Scripts/python.exe -m pytest -q` (Linux y Mac: `.venv/bin/python -m pytest -q`); las del informe y del README se omiten si faltan los archivos de `data/`. Cubren los nodos de ingesta y preprocesamiento, el informe y este README. **Ignorado por git:** {', '.join('`' + l + '`' for l in ign)}."""


def sec_pauta():
    refs = bloque_en(INFORME_MD, "### 14.5 Referencias", "\n\n---") if "### 14.5 Referencias" in INFORME_MD else ""
    refs = "\n".join(l for l in refs.splitlines() if l.startswith("- "))
    if sum(p for _, _, p, _, _, _ in PAUTA_IE) != 100:
        inf.fallar("las ponderaciones de los indicadores de la pauta no suman 100 %")
    indicadores = pd.DataFrame([
        {"Indicador de la pauta": f"{ie}: {nombre}", "Ponderación": f"{p} %", "README": rd, "Informe": ii, "Notebooks": nb}
        for ie, nombre, p, rd, ii, nb in PAUTA_IE
    ])
    entregables = pd.DataFrame([
        {"Entregable de la pauta": "Informe técnico en Markdown (.md), como un README reproducible, con problema de negocio, objetivos, KPIs, fuentes de datos, preparación y EDA, y metodología CRISP-DM",
         "Dónde está": "[`docs/informe_tecnico_EP2.md`](docs/informe_tecnico_EP2.md) (problema, objetivos y KPIs: sección 2; fuentes, preparación y EDA: 3 y 6; CRISP-DM: 4) y este README (secciones 2 a 7)"},
        {"Entregable de la pauta": "Notebook .ipynb documentado, organizado y ejecutable, que reproduce las etapas del informe",
         "Dónde está": "[`notebooks/`](notebooks): una serie numerada (00 a 10) y no un único archivo; el 10 reproduce el resultado oficial (sección 14)"},
        {"Entregable de la pauta": "Datos y archivos complementarios para ejecutar de nuevo sin modificaciones",
         "Dónde está": f"`entrega_EP2.zip` (sección 14); {SIN_LIDAR_BOX}"},
        {"Entregable de la pauta": "Carpeta organizada (`data/`, `notebooks/`, `models/`, `images/`, `README.md`)",
         "Dónde está": "`data/`, `notebooks/`, `images/` y `README.md` en la raíz; `models/` equivale a `data/06_models` por la convención de Kedro; además `conf/`, `src/`, `scripts/`, `tests/` y `docs/`"},
    ])
    return f"""{h('pauta')}

> Cada indicador de la pauta de EP2 tiene su lugar en el README, el informe y los notebooks, y cada entregable tiene su archivo.

La pauta es la de {PAUTA_FUENTE}: actividad grupal con defensa individual, ponderación de {PAUTA_PESO} % y presentación de 10 minutos; la defensa no es un archivo, así que no aparece en las tablas.

{tabla(indicadores, raw=True)}

{tabla(entregables, raw=True)}

**Referencias.**

{refs}

**Equipo.** Maicol Hernández (rama `maicolhernandez`) y Francis Moya (rama `francismoya`). **Curso:** MLY1101.

**Limitaciones.** {len(inf.SPLIT_TEST)} segmentos de test, pocos ciclistas, un segmento concentra el problema, rangos de azimut por cámara empíricos y causa del hueco de cámara no distinguible; más en la [sección 12 del informe](docs/informe_tecnico_EP2.md#12-limitaciones-y-desviaciones-del-plan)."""


def main():
    cuerpo = [cabecera(), sec_resumen(), sec_contexto(), sec_ep1(), sec_datos(), sec_eda(), sec_prep(), sec_metodo(), sec_modelos(), sec_nosup(), sec_test(), sec_posthoc(), sec_reco(), sec_etica(), sec_repo(), sec_pauta()]
    texto = "\n\n".join(c.strip() for c in cuerpo) + "\n"
    (R / "README.md").write_text(texto, encoding="utf-8")
    n_fig = len(re.findall("!" + chr(92) + "[", texto))
    print(f"README escrito: {len(texto.splitlines())} lineas, {n_fig} figuras. Cifras o archivos faltantes: {len(set(inf.FALTAN))}")
    for f in sorted(set(inf.FALTAN)):
        print("  falta:", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
