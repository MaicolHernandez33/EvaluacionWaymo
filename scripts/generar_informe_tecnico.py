"""Genera docs/informe_tecnico_EP2.md a partir de los archivos de salida del proyecto.

Uso (desde la raiz del repositorio):

    .venv/Scripts/python.exe -X utf8 scripts/generar_informe_tecnico.py

Lee solo archivos ya generados (CSV y JSON de data/08_reporting y data/06_models, los .md de docs/ y
data/08_reporting, los notebooks ejecutados y la configuracion del repositorio). No entrena nada ni abre
datos nuevos: cada cifra del informe sale de esos archivos. Si falta una cifra, la seccion lo dice.
"""
import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constantes_ep2 import EJECUCIONES_TEST  # noqa: E402

R = Path(__file__).resolve().parent.parent
REP, DOCS, IMG, MOD, NBS, INP = R / "data" / "08_reporting", R / "docs", R / "images", R / "data" / "06_models", R / "notebooks", R / "data" / "05_model_input"
FALTAN = []          # cifras o archivos que no se encontraron (se listan en la seccion 11)


# --------------------------------------------------------------------------------------------- utilidades
def es(s):
    return re.sub(r"(?<=\d)\.(?=\d)", ",", str(s))


def n3(x, signo=False):
    return es(f"{x:+.3f}" if signo else f"{x:.3f}")


def n1(x, signo=False):
    return es(f"{x:+.1f}" if signo else f"{x:.1f}")


def pc(x, d=1):
    return es(f"{x * 100:.{d}f}") + " %"


def miles(x):
    return f"{int(round(float(x))):,}".replace(",", ".")


def leer_csv(nombre, **kw):
    p = REP / nombre
    if not p.exists():
        FALTAN.append(f"data/08_reporting/{nombre}")
        return pd.DataFrame()
    df = pd.read_csv(p, **kw)
    for c in df.columns:
        if str(c) in ("segment_id", "segmento", "seg"):           # identificadores: texto, no numeros con separador de miles
            df[c] = df[c].astype(str)
    return df


def leer_json(p):
    p = Path(p)
    if not p.exists():
        FALTAN.append(str(p.relative_to(R)))
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def leer_txt(p):
    p = Path(p)
    if not p.exists():
        FALTAN.append(str(p.relative_to(R)))
        return ""
    return p.read_text(encoding="utf-8")


_MET = re.compile(r"auc|recall|precision|tasa|prob|pct|%|f1|ece|brier|captura|fraccion|fracción|^lo$|^hi$|odds|^or |coef|silhouette|davies|dif|prev", re.I)


def fmt_celda(v, col=""):
    """Enteros con separador de miles; flotantes enteros (umbrales, conteos) sin decimales salvo en columnas de metricas."""
    if isinstance(v, (bool, np.bool_)):
        return str(v)
    if isinstance(v, (int, np.integer)):
        return miles(v)
    if isinstance(v, (float, np.floating)):
        if v != v:
            return ""
        if float(v).is_integer() and not _MET.search(str(col)):
            return miles(v)
        return f"{v:,.3f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return es(v)


# Las etiquetas de los CSV salen sin tilde (las escriben los notebooks 09 y 10, que no se tocan); en el informe y en el README se muestran con tilde.
ACENTOS = {"Regresion logistica": "Regresión logística", "Regla geometrica": "Regla geométrica", "Modelo minimo": "Modelo mínimo", "Isotonica": "Isotónica"}

# Nombres de pantalla de columnas crudas de los CSV (el CSV no cambia; solo el encabezado de la tabla Markdown).
ENCABEZADOS = {
    "lo": "IC inferior", "hi": "IC superior", "segment_id": "Segmento", "seg": "Segmento", "location": "Ubicación", "time_of_day": "Momento del día", "metodo": "Método", "metrica": "Métrica",
    "version": "Versión", "versión": "Versión", "camara": "Cámara", "nombre": "Perfil", "precision": "Precisión", "algun_hueco": "Algún hueco", "caida_auc": "Caída del AUC",
    "Fraccion para 80%": "Fracción para 80 %", "Captura@20%": "Captura@20 %", "dFraccion para 80%": "Dif. de Fracción para 80 %", "dFraccion80 (puntos)": "Dif. de Fracción para 80 % (puntos)",
    "dAUC": "Dif. de AUC", "dif AUC": "Dif. de AUC", "dif F80": "Dif. de F80", "IC dAUC": "IC de la dif. de AUC", "IC dF80": "IC de la dif. de F80", "base": "Baseline",
    "pct_revisar": "% de cajas revisadas", "pct_revisar_A": "% de cajas revisadas (A)", "recall_A": "Recall (A)", "precision_A": "Precisión (A)", "pct_ciclistas": "% de ciclistas",
    "distancia_m": "Distancia (m)", "num_lidar_points": "Puntos LiDAR", "prob_media_modelo": "Probabilidad media del modelo", "filas_train": "Filas de train", "filas_lluvia": "Filas de lluvia",
    "distancia_med": "Distancia mediana (m)", "azimut_med": "Azimut mediano (°)", "puntos_med": "Puntos LiDAR (mediana)", "puntos_top_med": "Puntos top (mediana)", "pct_franja_100_120": "% en la franja 100-120°",
    "filas_B_120": "Filas (120°)", "sin_camara_120": "Positivos (120°)", "filas_B_principal": "Filas (principal)", "sin_camara_principal": "Positivos (principal)",
    "filas_en_franja": "Filas en la franja", "sin_en_franja": "Positivos en la franja", "OR lo": "OR inferior", "OR hi": "OR superior",
    "ubicacion": "Ubicación", "precision A": "Precisión (A)", "precision oficial": "Precisión oficial", "precision sin el segmento": "Precisión sin el segmento", "recall A": "Recall (A)",
    "proporcion donde el modelo supera": "Proporción donde el modelo supera", "tamano cluster mas chico": "Tamaño del cluster más chico", "AUC regresion logistica": "AUC regresión logística",
}


def acentuar(x):
    if isinstance(x, str):
        for sin, con in ACENTOS.items():
            x = x.replace(sin, con)
    return x


def encabezado(c):
    """Nombre de pantalla de una columna: mapa explícito y, para nombres de una palabra o con espacios, mayúscula inicial."""
    c = str(c)
    c = ENCABEZADOS.get(c, c)
    if len(c) > 1 and c[0].islower() and (" " in c or c.isalpha()):
        c = c[0].upper() + c[1:]
    return acentuar(c)


def tabla(df, indice=False, cols=None, raw=False):
    d = df.reset_index() if indice else df.copy()
    if cols:
        d = d[cols]
    esc = lambda x: str(x).replace("|", chr(92) + "|")
    cab = "| " + " | ".join(esc(encabezado(c)) for c in d.columns) + " |\n|" + "---|" * len(d.columns) + "\n"
    nombres = list(d.columns)                     # fmt_celda decide el formato con el nombre crudo de la columna
    filas = []
    for fila in d.itertuples(index=False):
        celdas = [esc(acentuar(str(v) if raw else fmt_celda(v, nombres[k]))) for k, v in enumerate(fila)]
        filas.append("| " + " | ".join(celdas) + " |")
    return cab + "\n".join(filas)


def figura(nombre, texto, prefijo="../images"):
    if not (IMG / nombre).exists():
        FALTAN.append(f"images/{nombre}")
        return f"*(Falta la figura images/{nombre}.)*"
    return f"![{texto}]({prefijo}/{nombre})\n\n*Figura: {texto}. Archivo: `images/{nombre}`.*"


TEXTOS = []          # (fuente, texto) de todo texto que proviene de notebooks o de resumenes generados por notebooks


def registrar(fuente, texto):
    if fuente:
        TEXTOS.append((fuente, texto))
    return texto


def bloque(texto, ini, fin=None, fuente=None):
    if ini not in texto:
        FALTAN.append(f"bloque '{ini[:40]}'")
        return ""
    t = texto[texto.index(ini):]
    if fin and fin in t[len(ini):]:
        t = t[: len(ini) + t[len(ini):].index(fin)]
    return registrar(fuente, t.strip())


def celdas_md(nb):
    p = NBS / f"{nb}.ipynb"
    if not p.exists():
        FALTAN.append(f"notebooks/{nb}.ipynb")
        return []
    return [("".join(c["source"])) for c in json.loads(p.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "markdown"]


def salidas_nb(nb):
    p = NBS / f"{nb}.ipynb"
    out = []
    if not p.exists():
        return ""
    for c in json.loads(p.read_text(encoding="utf-8"))["cells"]:
        if c["cell_type"] != "code":
            continue
        for o in c.get("outputs", []):
            if o["output_type"] == "stream":
                out.append("".join(o["text"]))
            elif "data" in o and "text/markdown" in o["data"]:
                out.append("".join(o["data"]["text/markdown"]))
    return "\n".join(out)


def buscar(texto, patron, nombre):
    m = re.search(patron, texto)
    if not m:
        FALTAN.append(f"salida de notebook: {nombre}")
        return None
    return m


def ci_str(txt, como_pct=False):
    m = re.match(r"\s*([\d.]+)(?: \(([\d.]+) a ([\d.]+)\))?", str(txt))
    if not m:
        return "(sin dato)"
    v = [float(x) for x in m.groups() if x is not None]
    f = pc if como_pct else n3
    return f(v[0]) + (f" (IC 95 % {f(v[1])} a {f(v[2])})" if len(v) == 3 else "")


def cita(texto, fuente=None):
    registrar(fuente, texto)
    return "\n".join("> " + l if l.strip() else ">" for l in texto.strip().splitlines())


def fallar(msg):
    sys.exit("ERROR (generar_informe_tecnico): " + msg)


SIN_ARCHIVO = "[cifra del notebook 07, sin archivo de salida]"
PREVIA = "[cifras de una versión previa del análisis (población de 120°); ver la nota 'Actualización posterior al 08 y 09' del 07]"


def rotular_previa(texto):
    """Rotula como version previa las cifras del 07 que la nota de actualizacion dejo desactualizadas."""
    pares = [
        ("brechas Day/Night de 0,000", "brechas Day/Night de 0,000 " + PREVIA),
        ("modelo menos regla: -11.4 puntos, IC 95 % -19.0 a -6.1)", "modelo menos regla: -11.4 puntos, IC 95 % -19.0 a -6.1 " + PREVIA + ")"),
        ("hay que revisar el 39,1 % de los frames con el modelo, el 50,5 % con la regla simple", "hay que revisar el 39,1 % de los frames con el modelo, el 50,5 % con la regla simple " + PREVIA),
        ("265.377 filas", "265.377 filas " + SIN_ARCHIVO),
        ("2,09 % ciclistas en 12 segmentos", "2,09 % ciclistas en 12 segmentos " + SIN_ARCHIVO),
    ]
    for a, b in pares:
        if a in texto:
            texto = texto.replace(a, b, 1)
    return texto


# --------------------------------------------------------------------------------------------- carga
C9 = leer_json(REP / "09_resumen_cifras.json")
C10 = leer_json(REP / "10_resumen_cifras.json")
PLAN = leer_json(MOD / "plan_evaluacion_test.json")
HIP = leer_json(MOD / "hiperparametros_B.json")
CFGB = leer_json(INP / "config_features_B.json")
SEG = pd.read_csv(DOCS / "seleccion_segmentos" / "segmentos_ep2.csv")
REG = pd.read_csv(DOCS / "seleccion_segmentos" / "registro_verificacion_ep2.csv")
SPL = pd.read_csv(INP / "split_segmentos.csv")
DEC = leer_csv("decision_target_ep2.csv")
ENTORNO = leer_txt(DOCS / "entorno_ep2.txt")
LOG = leer_txt(DOCS / "log_trabajo_ep2.md")
RES07 = leer_txt(REP / "resumen_ejecutivo_ep2.md")
RES08 = leer_txt(REP / "resumen_ejecutivo_08.md")
RES09 = leer_txt(REP / "resumen_ejecutivo_09.md")
DOC07 = leer_txt(DOCS / "decision_target_ep2.md")
GITIGNORE = leer_txt(R / ".gitignore")

OPD = C10.get("D", {}).get("OP", {})
B = C10.get("B", {})
M = C10.get("M", {})
L = C10.get("L", {})
MOD_N, BASE_N = B.get("mod", "Regresion logistica"), B.get("base", "Regla: menos puntos top")
OPA_M, OPA_B = OPD.get(f"{MOD_N} | A", {}), OPD.get(f"{BASE_N} | A", {})
OPB_B = OPD.get(f"{BASE_N} | B", {})
P9 = C9.get("principal", {})
SPLIT_TRAIN = SPL[SPL["conjunto"] == "train"]
SPLIT_TEST = SPL[SPL["conjunto"] == "test"]
NS = leer_json(REP / "08_no_supervisado_resumen.json")
_CLAVES_NS = ["k_elegido", "ari_entre_tecnicas", "estabilidad_por_segmento", "isolation_forest", "diferencia_con_signo_clusters"]
_faltan_ns = [k for k in _CLAVES_NS if k not in NS]
if _faltan_ns:
    fallar("a data/08_reporting/08_no_supervisado_resumen.json le faltan las claves " + ", ".join(_faltan_ns) + ". Ejecuta scripts/extraer_no_supervisado_08.py (lee las salidas del notebook 08 ya ejecutado).")


def ic3(lista):
    return f"{n3(lista[0])} (IC 95 % {n3(lista[1])} a {n3(lista[2])})" if lista else "(sin dato)"


def fmt_bic(x):
    return f"{x:+,.0f}".replace(",", ".")


def sin_titulo(txt):
    """Quita la primera linea si es un encabezado Markdown (los notebooks traen su propio titulo)."""
    lineas = txt.strip().splitlines()
    while lineas and (lineas[0].startswith("#") or not lineas[0].strip()):
        lineas = lineas[1:]
    return "\n".join(lineas)


def tasas_por_fold():
    fb = pd.read_parquet(INP / "features_B.parquet", columns=["segment_id", "sin_camara", "fold", "en_zona_principal"])
    fbp = fb[fb["en_zona_principal"].astype(bool)]
    t = fbp.groupby("fold").agg(segmentos=("segment_id", "nunique"), filas=("sin_camara", "size"), positivos=("sin_camara", "sum")).reset_index()
    t["fold"] = t["fold"].astype(int)
    t["tasa de sin_camara"] = t["positivos"] / t["filas"]
    return fb, fbp, t


def notebooks_que_usan_lluvia():
    usan = []
    for p in sorted(NBS.glob("*.ipynb")):
        if p.stem[:2] not in ("07", "08", "09", "10"):
            continue
        for c in json.loads(p.read_text(encoding="utf-8"))["cells"]:
            if c["cell_type"] == "code" and re.search(r"solo_clustering|lluvia", "".join(c["source"])):
                usan.append(p.stem)
                break
    return usan


def l7(metodo, variable, grupo):
    d = leer_csv("10_L_equidad_sin_segmento.csv")
    if not len(d):
        return float("nan"), float("nan")
    r = d[(d["metodo"] == metodo) & (d["variable"] == variable) & (d["grupo"] == grupo)]
    return (float(r["recall A (oficial)"].iloc[0]), float(r["recall A (sin el segmento)"].iloc[0])) if len(r) else (float("nan"), float("nan"))


def frase_l7():
    d_o, d_s = l7(BASE_N, "time_of_day", "Day")
    s_o, s_s = l7(BASE_N, "location", "location_sf")
    foco = L.get("foco", "?")
    return (f"Sin el segmento {foco} (post hoc, no pre-declarado), el recall al punto A de la regla top pasa de {n3(d_o)} a {n3(d_s)} en Day y de {n3(s_o)} a {n3(s_s)} en San Francisco; "
            "las brechas por momento del día y por ubicación estaban confundidas con ese segmento (de día y de San Francisco).")


def prosa_segmentos():
    g = C10.get("G", {})
    mom = ", ".join(f"{k}: {v}" for k, v in g.get("seg_momento", {}).items())
    ubi = ", ".join(f"{k}: {v}" for k, v in g.get("seg_ubic", {}).items())
    unicos = ", ".join(g.get("unico", []))
    return f"Segmentos de test por momento del día ({mom}) y por ubicación ({ubi}). Con un solo segmento: {unicos or 'ninguno'}"


def archivos_congelados():
    """Los archivos con sha256 del plan v2, en el orden en que los verifican el notebook 10 y scripts/verificar_congelados.py: los de sha256.archivos, features_B.parquet y el plan v1."""
    sh = PLAN.get("sha256", {})
    if not sh or "features_B.parquet" not in sh or "plan_v1_json" not in sh:
        fallar("plan_evaluacion_test.json no tiene los sha256 esperados (archivos, features_B.parquet, plan_v1_json)")
    return list(sh["archivos"].items()) + [("features_B.parquet", sh["features_B.parquet"]), ("plan_evaluacion_test_v1.json", sh["plan_v1_json"])]


def verificaciones_en_copia():
    """Fechas (del log) de las ejecuciones de verificación del notebook 10 hechas en copias fuera del repositorio."""
    marcas = ("VERIFICACION DE REPRODUCIBILIDAD EN COPIA LIMPIA", "VERIFICACION DEL PASO PRINCIPAL DE LA SECCION 14")
    fechas = []
    for marca in marcas:
        for linea in LOG.splitlines():
            if marca in linea:
                m = re.match(r"- \[(\d{4}-\d{2}-\d{2}) ", linea)
                fechas.append(m.group(1) if m else None)
                break
    if len(fechas) != 2 or None in fechas:
        fallar("el log no registra con fecha las 2 ejecuciones de verificacion en copias fuera del repositorio")
    return fechas


def frase_pruebas():
    """Resultado de la última medición de pruebas y cobertura (data/08_reporting/pytest_resumen.json, lo escribe scripts/medir_pruebas.py)."""
    pj = leer_json(REP / "pytest_resumen.json")
    if not pj:
        return "(sin dato: ejecutar scripts/medir_pruebas.py)"
    return f"{pj['pasadas']} pasadas, {pj['falladas']} falladas, {pj['omitidas']} omitidas; cobertura total {n1(pj['cobertura_total_pct'])} %"


def frase_hueco_100():
    m = leer_csv("10_M_positivos_en_huecos.csv")
    if not len(m) or "train" not in set(m["grupo"]):
        return ""
    r = m[m["grupo"] == "train"].iloc[0]
    return (f"En train las celdas con hueco reúnen solo el {pc(r['% de los positivos con >= 100 puntos'])} de los positivos con 100 puntos o más ({miles(r['de ellos en celdas con hueco'])} de {miles(r['positivos con >= 100 puntos'])}); "
            "la auditoría por cámara no explica todas las cajas bien observadas sin par.")


# --------------------------------------------------------------------------------------------- frases y datos compartidos con el README
_FB = {}


def fb_principal():
    """features_B de la población principal (solo train), leído una vez."""
    if "p" not in _FB:
        f = pd.read_parquet(INP / "features_B.parquet")
        _FB["p"] = f[f["en_zona_principal"].astype(bool)]
    return _FB["p"]


def num_es(x, cifras=None):
    """Número con coma decimal y sin notación científica."""
    if x is None:
        return "sin tope"
    if isinstance(x, bool):
        return "sí" if x else "no"
    if isinstance(x, str):
        return {"balanced": "balanceado"}.get(x, x)
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return es(f"{x:.{cifras}g}" if cifras else np.format_float_positional(x, trim="-"))


def _constante_nb(nb, nombre):
    d = json.loads((NBS / f"{nb}.ipynb").read_text(encoding="utf-8"))
    for c in d["cells"]:
        if c["cell_type"] == "code":
            m = re.search(rf"^{nombre}\s*=\s*(\d+)", "".join(c["source"]), flags=re.M)
            if m:
                return int(m.group(1))
    fallar(f"no se encontro la constante {nombre} en el notebook {nb}")


def segundos_por_revision():
    """Supuesto de segundos por revisión: lo fija el 07 (texto y código) y el 09 y el 10 repiten el mismo valor como constante."""
    m = re.search(r"supuesto de (\d+) s por revisi", DOC07)
    if not m:
        fallar("no se encontro en docs/decision_target_ep2.md el supuesto de segundos por revision")
    v07, v09, v10 = (_constante_nb("07_decision_target_ep2", "SEGUNDOS_POR_REVISION"), _constante_nb("09_modelos_supervisados_sin_camara", "SEGUNDOS_POR_REVISION"),
                     _constante_nb("10_evaluacion_final_sin_camara", "SEG_REV"))
    if not (int(m.group(1)) == v07 == v09 == v10):
        fallar("el supuesto de segundos por revision no coincide entre docs/decision_target_ep2.md y los notebooks 07, 09 y 10")
    return v07


def frase_20s():
    s = segundos_por_revision()
    return (f"Las horas son cajas × {s} s ÷ 3.600. Los {s} s por revisión no se calcularon ni se midieron: son un supuesto editable que fijamos en el notebook 07 (`SEGUNDOS_POR_REVISION`), "
            f"sin fuente citada, y que el 09 y el 10 repiten como constante; las horas son solo una ilustración.")


def parrafo_unidad():
    fb = fb_principal()
    n_fr = fb.drop_duplicates(["segment_id", "key.frame_timestamp_micros"]).shape[0]
    return (f"**Unidad de revisión: la caja, no el frame.** Las fracciones y las horas se calculan por fila de la tabla de modelado, es decir, por **caja** (un peatón o ciclista etiquetado en un frame): "
            f"{miles(len(fb))} cajas repartidas en {miles(n_fr)} frames de train de la población principal. Los notebooks 07, 09 y 10 y sus CSV llaman «frame» a esa fila (en el 07, «frame (caja 3D etiquetada)»); "
            "aquí decimos caja. Revisar una caja no equivale a revisar un frame completo, y el esfuerzo por frame no se midió.")


def detalle_lluvia():
    """Segmentos de lluvia: cuántos tienen la asociación vacía y cuántos etiquetado ralo (segmentos_ep2.csv y diagnostico_lluvia_ep2.csv)."""
    clus = SEG[SEG["uso"] == "solo_clustering"]
    if set(clus["segment_id"]) & set(REG["segment_id"]):
        fallar("los segmentos de lluvia estan en el registro de verificacion: revisar las frases sobre lluvia")
    mot = clus["motivo"].str.extract(r"^([a-z]+ [a-z]+)")[0].value_counts()
    diag = pd.read_csv(DOCS / "seleccion_segmentos" / "diagnostico_lluvia_ep2.csv", dtype={"segment_id": str})
    ralo = diag[diag["motivo"].str.startswith("etiquetado ralo")]
    vacia = diag[diag["motivo"].str.startswith("asociacion vacia")]
    if int(mot.get("asociacion vacia", 0)) != len(vacia) or int(mot.get("etiquetado ralo", 0)) != len(ralo) or int(vacia["frames_etiquetados"].sum()) != 0:
        fallar("segmentos_ep2.csv y diagnostico_lluvia_ep2.csv no coinciden en los motivos de los segmentos de lluvia")
    return {"n": len(clus), "vacia": len(vacia), "ralo": len(ralo), "frames_ralo": int(ralo["frames_etiquetados"].sum()), "asoc_ralo": int(ralo["asoc_filas"].sum())}


def frase_lluvia():
    d = detalle_lluvia()
    return (f"Los {d['n']} segmentos de lluvia no forman parte de esos {len(REG)}: son un estrato aparte ({d['vacia']} con asociación vacía y {d['ralo']} con etiquetado ralo)")


def frase_lluvia_frames():
    d = detalle_lluvia()
    return (f"{d['vacia']} de los {d['n']} segmentos de lluvia no tienen frames etiquetados (asociación vacía) y {d['ralo']} tiene {d['frames_ralo']} frames etiquetados, pero con etiquetado ralo ({d['asoc_ralo']} filas de asociación)")


def frase_logaritmos():
    pre = HIP.get("preprocesamiento_lr", {})
    con = [f"`{c}`" for c in pre.get("log1p_y_estandarizacion", [])]
    sin = pre.get("estandarizacion", [])
    if not con or not sin:
        fallar("falta preprocesamiento_lr en hiperparametros_B.json")
    return (f"la regresión logística aplica `log1p` y luego estandariza {len(con)} variables ({', '.join(con)}) y solo estandariza las otras {len(sin)}; los árboles (HGB y Random Forest) usan las variables sin transformar; "
            "el aprendizaje no supervisado usa los logaritmos de puntos, densidad y volumen")


def nota_regla_geometrica():
    c09 = leer_csv("09_comparacion_modelos.csv")
    reglas = PLAN.get("reglas_en_120", {})
    clave = next((k for k in reglas if k.startswith("Regla geometrica")), None)
    if clave is None:
        fallar("el plan no describe la regla geometrica en reglas_en_120")
    umbral = HIP["baseline_simple"]["regla_geometrica_umbral_deg"]
    az_max = float(fb_principal()["azimut_abs_deg"].max())
    f_geo = c09[c09["modelo"].str.startswith("Regla geometrica")].drop(columns="modelo").reset_index(drop=True)
    f_pts = c09[c09["modelo"] == "Regla: menos puntos LiDAR"].drop(columns="modelo").reset_index(drop=True)
    if az_max > umbral or not f_geo.equals(f_pts):
        fallar("la regla geometrica y la de menos puntos LiDAR ya no son identicas en la poblacion principal: revisar la nota")
    return (f"**Por qué dos filas son idénticas.** «Regla geométrica» y «Regla: menos puntos LiDAR» dan las mismas métricas porque el puntaje de la geométrica es `{reglas[clave]['puntaje']}`: pone primero las cajas con azimut mayor que {umbral}°, "
            f"y la población principal solo tiene cajas hasta {num_es(az_max, 4)}° (máximo en train), así que su orden queda igual al de menos puntos LiDAR. Las dos reglas solo se distinguen en la población de 120° (sensibilidad), "
            "donde la geométrica es el mejor baseline simple.")


def n2(x):
    return es(f"{float(str(x).replace('>= ', '').replace('<= ', '')):.2f}")


def _ci(txt):
    return es(str(txt))


def _kpi_celdas():
    """Valores de los KPI en train (fuera de fold) y en el test oficial, leidos de los CSV."""
    c9 = leer_csv("09_comparacion_modelos.csv")
    r10 = leer_csv("10_resultado_principal.csv")
    po9, po10 = leer_csv("09_puntos_operacion.csv"), leer_csv("10_puntos_de_operacion.csv")
    cal9, cal10 = leer_csv("09_calibracion.csv"), leer_csv("10_calibracion.csv").rename(columns={"Unnamed: 0": "version"})
    fold = pd.read_csv(REP / "09_auc_por_fold.csv", index_col=0)
    seg9 = pd.read_csv(REP / "09_auc_por_segmento.csv", index_col=0)
    seg10 = leer_csv("10_L_auc_segmentos_test.csv")
    v = {}
    for m in (BASE_N, MOD_N):
        v[("c9", m)] = c9[c9["modelo"] == m].iloc[0]
        v[("r10", m)] = r10[r10["metodo"] == m].iloc[0]
        v[("po9", m)] = po9[(po9["metodo"] == m) & po9["punto"].str.startswith("A")].iloc[0]
        v[("po10", m)] = po10[(po10["metodo"] == m) & po10["punto"].str.startswith("A")].iloc[0]
    return v, cal9.set_index("version"), cal10.set_index("version"), fold, seg9, seg10


def tabla_kpis():
    v, cal9, cal10, fold, seg9, seg10 = _kpi_celdas()
    cr = PLAN.get("criterios", {}).get("parametros", {})
    vlp, est, ope, cal = cr.get("vale_la_pena", {}), cr.get("estabilidad", {}), cr.get("operacion", {}), cr.get("calibracion", {})
    tol = C10.get("D", {}).get("tol", ope.get("recall_segmento_min", float("nan")))
    dec = {r["criterio"]: r for _, r in DEC[DEC["target"] == "B"].iterrows()} if len(DEC) else {}
    a_min = dec.get("AUC (todas las variables)", {}).get("umbral", "?")
    pr_min = dec.get("PR-AUC - prevalencia", {}).get("umbral", "?")
    dos = lambda tabla_, col: f"Regla top {_ci(v[(tabla_, BASE_N)][col])}; LR {_ci(v[(tabla_, MOD_N)][col])}"
    s10 = seg10[["AUC regla top", "AUC regresion logistica"]] if len(seg10) else None
    filas = [
        {"KPI": "AUC", "Definición": "Probabilidad de que una caja sin par reciba un puntaje mayor que una con par", "Por qué importa al negocio": "Dice si la lista ordena bien, sin depender de un corte",
         "Meta fijada antes": f"AUC >= {n2(a_min)} (criterio de B en el 07, `decision_target_ep2.csv`)", "Train (fuera de fold)": dos("c9", "AUC"), "Test oficial": dos("r10", "AUC")},
        {"KPI": "PR-AUC", "Definición": "Área bajo la curva precisión-recall", "Por qué importa al negocio": "Mide cuántas de las cajas marcadas son realmente sin par, con una clase minoritaria",
         "Meta fijada antes": f"PR-AUC menos prevalencia >= {n2(pr_min)} (07)", "Train (fuera de fold)": dos("c9", "PR-AUC") + f" (prevalencia {n3(C9.get('principal', {}).get('Prevalencia (trivial)', {}).get('PR-AUC', float('nan')))})",
         "Test oficial": dos("r10", "PR-AUC") + f" (prevalencia {n3(float(cal10['prevalencia'].iloc[0]))})"},
        {"KPI": "Fracción para 80 %", "Definición": "Fracción de cajas a revisar, en el orden del puntaje, para encontrar el 80 % de las cajas sin par", "Por qué importa al negocio": "Es el esfuerzo de revisión: menos es mejor (al azar sería ~80 %)",
         "Meta fijada antes": f"Un modelo se recomienda solo si baja al menos {int(round(abs(vlp.get('delta_fraccion80_max', float('nan'))) * 100))} puntos frente al baseline con IC pareado que excluya 0 y su AUC sube al menos {n2(vlp.get('delta_auc_min', float('nan')))} (plan v2)",
         "Train (fuera de fold)": dos("c9", "Fraccion para 80%"), "Test oficial": dos("r10", "Fraccion para 80%")},
        {"KPI": "Recall en el punto A", "Definición": "Fracción de las cajas sin par que quedan dentro de lo que se revisa con el corte fijado en train", "Por qué importa al negocio": "Cuántas lagunas se encuentran con el presupuesto de revisión elegido",
         "Meta fijada antes": f"Objetivo {n2(ope.get('recall_objetivo', float('nan')))}; sostenido en test si el recall es al menos {n2(tol)}", "Train (fuera de fold)": dos("po9", "recall"), "Test oficial": dos("po10", "recall")},
        {"KPI": "% de cajas revisadas en el punto A", "Definición": "Fracción de las cajas que quedan por encima del corte", "Por qué importa al negocio": "Es el costo de revisión del punto A",
         "Meta fijada antes": f"Sin meta numérica para A; el punto B usa un presupuesto de {pc(ope.get('presupuesto_revision', float('nan')), 0)}", "Train (fuera de fold)": dos("po9", "pct_revisar"), "Test oficial": dos("po10", "pct_revisar")},
        {"KPI": "ECE (calibración)", "Definición": "Diferencia media entre la probabilidad predicha y la frecuencia observada, en 10 grupos por cuantiles", "Por qué importa al negocio": "Si se publican probabilidades, tienen que significar lo que dicen",
         "Meta fijada antes": f"ECE <= {n2(cal.get('ece_max', float('nan')))} tras calibrar (09)", "Train (fuera de fold)": f"LR crudo {n3(float(cal9.loc['Crudo', 'ECE']))}; con Platt {n3(float(cal9.loc['Platt', 'ECE']))}",
         "Test oficial": f"LR crudo {n3(float(cal10.loc['crudo', 'ECE']))}; con Platt congelado {n3(float(cal10.loc['calibrado (Platt)', 'ECE']))}"},
        {"KPI": "Estabilidad por fold", "Definición": "AUC mínimo entre los 5 folds de train", "Por qué importa al negocio": "Un resultado que depende de un fold no se puede esperar en datos nuevos",
         "Meta fijada antes": f"AUC mínimo por fold >= {n2(est.get('auc_fold_min', float('nan')))} (09)", "Train (fuera de fold)": f"Regla top {n3(fold[BASE_N].min())}; LR {n3(fold[MOD_N].min())}", "Test oficial": "No aplica: el test no tiene folds"},
        {"KPI": "Estabilidad por segmento", "Definición": "Mediana del AUC dentro de cada segmento", "Por qué importa al negocio": "Los segmentos son escenas distintas; el promedio puede esconder segmentos donde falla",
         "Meta fijada antes": f"Mediana >= {n2(est.get('auc_segmento_mediana_min', float('nan')))} (09)", "Train (fuera de fold)": f"Regla top {n3(seg9.loc[BASE_N, 'mediana'])}; LR {n3(seg9.loc[MOD_N, 'mediana'])} ({int(seg9.loc[BASE_N, 'segmentos'])} segmentos)",
         "Test oficial": (f"Regla top {n3(s10['AUC regla top'].median())}; LR {n3(s10['AUC regresion logistica'].median())} (mediana de {len(s10)} segmentos con al menos 50 positivos; mínimo {n3(s10['AUC regla top'].min())} y {n3(s10['AUC regresion logistica'].min())})" if s10 is not None else "(sin dato)")},
    ]
    cumple_train = {m: bool(float(str(v[('c9', m)]['AUC']).split()[0]) >= float(str(a_min).replace('>= ', '')) and float(fold[m].min()) >= est.get('auc_fold_min', 9) and float(seg9.loc[m, 'mediana']) >= est.get('auc_segmento_mediana_min', 9)) for m in (BASE_N, MOD_N)}
    rec_test = {m: float(str(v[('po10', m)]['recall']).split()[0]) for m in (BASE_N, MOD_N)}
    f80_test = {m: float(str(v[('r10', m)]['Fraccion para 80%']).split()[0]) for m in (BASE_N, MOD_N)}
    texto = (f"Lectura (generada): en train, {'la regla y la LR cumplen' if all(cumple_train.values()) else 'no todos los métodos cumplen'} las metas de AUC y de estabilidad por fold y por segmento; "
             f"en el test oficial el recall del punto A ({n3(rec_test[BASE_N])} con la regla y {n3(rec_test[MOD_N])} con la LR) {'queda bajo' if max(rec_test.values()) < tol else 'alcanza'} la meta de {n2(tol)}, "
             f"y la fracción para 80 % es {pc(f80_test[BASE_N])} con la regla y {pc(f80_test[MOD_N])} con la LR, frente a {pc(C9.get('principal', {}).get('Prevalencia (trivial)', {}).get('Fraccion para 80%', float('nan')), 0)} al azar; las razones se analizan en las secciones 9 y 10.")
    return pd.DataFrame(filas), texto


DEFINICIONES = {
    "box_center_x": "Coordenada x del centro de la caja 3D (m), en el marco del vehículo", "box_center_y": "Coordenada y del centro de la caja 3D (m)", "box_center_z": "Coordenada z del centro de la caja 3D (m)",
    "azimut_abs_deg": "Valor absoluto del ángulo del centro de la caja respecto del eje x, en grados (derivada de x e y)", "distancia_m": "Distancia euclidiana al sensor: raíz de x al cuadrado más y al cuadrado",
    "box_length": "Largo de la caja (m)", "box_width": "Ancho de la caja (m)", "box_height": "Alto de la caja (m)", "volumen_caja": "Largo por ancho por alto",
    "num_lidar_points": "Puntos LiDAR dentro de la caja", "num_top_lidar_points": "Puntos dentro de la caja captados por el LiDAR superior", "densidad_puntos": "Puntos LiDAR divididos por el volumen de la caja",
    "speed_mps": "Norma de la velocidad horizontal (x, y) de la etiqueta (m/s)", "heading_sin": "Seno del rumbo de la caja", "heading_cos": "Coseno del rumbo de la caja", "es_ciclista": "1 si la clase es ciclista, 0 si es peatón"}


def bloque_calidad():
    fb = pd.read_parquet(INP / "features_B.parquet")
    fbp = fb[fb["en_zona_principal"].astype(bool)]
    variables = CFGB.get("conjuntos", {}).get("TODAS_B", [])
    rf = leer_csv("reporte_filtro_frames.csv")
    pre = HIP.get("preprocesamiento_lr", {})
    log_std, std = set(pre.get("log1p_y_estandarizacion", [])), set(pre.get("estandarizacion", []))
    filas = []
    for var in variables:
        x = fbp[var]
        if x.nunique() <= 2:
            at = "no aplica (binaria)"
        else:
            q1, q3 = x.quantile(0.25), x.quantile(0.75)
            iqr = q3 - q1
            at = pc(float(((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)).mean()))
        trat = "log1p y estandarización" if var in log_std else ("estandarización" if var in std else "sin transformar")
        filas.append({"variable": f"`{var}`", "definición": DEFINICIONES.get(var, "(sin definición)"), "nulos": int(x.isna().sum()), "% fuera de 1,5 IQR (train)": at, "tratamiento en la regresión logística": trat})
    tv = pd.DataFrame(filas)
    dup = int(fbp.duplicated(["segment_id", "key.frame_timestamp_micros", "key.laser_object_id"]).sum()) if "key.laser_object_id" in fbp.columns else None
    ceros = float((fbp["num_lidar_points"] == 0).mean())
    out06 = salidas_nb("06_eda_y_preparacion_modelamiento")
    m_dup, m_cero, m_tam = (re.search(p_, out06) for p_ in (r"Filas duplicadas por llave \(segmento, frame, objeto\): (\d+)", r"Cero puntos LiDAR en la caja: ([\d,]+)", r"Tamanos <= 0: (\d+)"))
    if not (m_dup and m_cero and m_tam):
        fallar("no se encontraron en las salidas del notebook 06 las lineas de duplicados / cero puntos / tamaños <= 0 (seccion A.2).")
    fa, fd = int(rf["filas_antes"].sum()), int(rf["filas_despues"].sum())
    ta, td = float(rf["positivos"].sum() / fa), float(rf["positivos"].sum() / fd)
    n06 = next((c for c in celdas_md("06_eda_y_preparacion_modelamiento") if "Tratamiento de nulos y escalas" in c), "")
    trat06 = registrar("06", bloque(n06, "**Tratamiento de nulos y escalas:**", "\n\n")) if n06 else ""
    ocl = salidas_nb("08_analisis_observabilidad_sin_camara")
    m_fuga = re.search(r"Control anti-fuga OK: [^\n]+", ocl)
    return f"""### Preparación y calidad de los datos

**Filtros aplicados, en este orden.** (1) Solo los {len(SEG[SEG['uso'] == 'supervisado'])} segmentos supervisados. (2) Solo frames etiquetados: en cada segmento se descartan los frames sin ningún positivo de `tiene_camara`, porque sus objetos quedarían en 0 por falta de etiqueta y no porque la cámara no los viera; las filas pasan de {miles(fa)} a {miles(fd)} ({pc(fd / fa)} conservadas) y la tasa de `tiene_camara` de {pc(ta)} a {pc(td)} (`reporte_filtro_frames.csv`, notebook 06). (3) Solo peatones y ciclistas, porque `sin_camara` solo es una pregunta para ellos: en train, los vehículos y las señales nunca son positivos (sección 5). (4) La población principal, |azimut| <= {C9.get('AZ_MAX', '?')}° (sección 3).

**Nulos, duplicados y valores atípicos.** El notebook 06 revisó los {miles(fa)} registros de los segmentos supervisados antes del filtro de frames y no encontró nulos ni infinitos en las variables de entrada; las filas duplicadas por llave (segmento, frame, objeto) son {m_dup.group(1)}, los tamaños menores o iguales a cero {m_tam.group(1)} y las cajas con cero puntos LiDAR {miles(int(m_cero.group(1).replace(',', '')))} (esas cajas son reales: objetos que el LiDAR casi no vio). Con la población principal de train ({miles(len(fbp))} filas, calculado al generar este informe) los nulos son {int(tv['nulos'].sum())} en las {len(tv)} variables{f', los duplicados por llave {dup}' if dup is not None else ''} y {pc(ceros)} de las cajas tienen cero puntos. No eliminamos atípicos: son objetos reales (cajas lejanas con pocos puntos, cajas grandes); los árboles no se afectan por la escala y la regresión logística usa `log1p` y estandarización (columna de tratamiento).

**Variables.** Las {len(tv)} variables del modelo (conjunto `TODAS_B`) y su tratamiento. Las variables nuevas que se probaron en el 08 (temporales y de oclusión: `n_ocl`, `frac_cub`, `dist_ocl`, puntos en frames anteriores) no mejoraron el resultado con el criterio fijado antes y no entraron en los modelos (sección 6). Logaritmos y escalado: {frase_logaritmos()} (sección 7).

{tabla(tv)}

**Escalado y fuga.** El escalado y la imputación se ajustan solo con los datos de entrenamiento de cada fold (son parte del `Pipeline`), nunca con el fold de validación ni con el test. El notebook 06 dejó escrito el tratamiento previsto para el 09:

{cita(trat06) if trat06 else ''}

Para evitar la fuga, ninguna variable proviene del par 2D ni de la tabla de asociación cámara-LiDAR; los identificadores (`key.laser_object_id`, `key.frame_timestamp_micros`) no son variables del modelo y los segmentos nunca se reparten entre train y test. {('El notebook 08 lo comprueba con un `assert`: ' + m_fuga.group(0)) if m_fuga else ''}
"""


S = []     # secciones del informe


# --------------------------------------------------------------------------------------------- 1. Resumen
def sec1():
    pr = C9.get("principal", {})
    top, lr = pr.get(BASE_N, {}), pr.get(MOD_N, {})
    par_test = next((p for p in M.get("pares", []) if p.get("grupo") == "test"), {})
    par_train = next((p for p in M.get("pares", []) if p.get("grupo") == "train"), {})
    ic_ = B.get("ic", {})
    pun = B.get("punto", {})
    sf = L.get("sin_foco", {})
    foco_pos = L["grupos"]["foco"]["sin_camara"] / (L["grupos"]["foco"]["sin_camara"] + L["grupos"]["otros 7 de test"]["sin_camara"])

    def con_ic(n, met):
        a, b_ = ic_.get(n, {}).get(met, [float("nan")] * 2)
        return f"{n3(pun.get(n, {}).get(met, float('nan')))} (IC 95 % {n3(a)} a {n3(b_)})"

    def con_ic_pct(n, met):
        a, b_ = ic_.get(n, {}).get(met, [float("nan")] * 2)
        return f"{pc(pun.get(n, {}).get(met, float('nan')))} (IC 95 % {pc(a)} a {pc(b_)})"

    t = f"""## 1. Resumen ejecutivo

**Problema y target.** Algunas cajas 3D etiquetadas (`lidar_box`) de peatones y ciclistas de Waymo Open Dataset v2 no tienen su par 2D de cámara, y solo se sabe cuáles son revisándolas una por una. Es como un archivo de expedientes en el que a algunos les falta el anexo. Predecimos `sin_camara` para ordenar la revisión humana; en la población principal (|azimut| <= {C9.get('AZ_MAX', '?')}°) la tasa de positivos en train es {pc(pr.get('Prevalencia (trivial)', {}).get('PR-AUC', float('nan')))}. Comparamos tres modelos con reglas simples de puntos LiDAR, con validación por segmento.

**Resultado oficial en el test (pre-declarado, {C10.get('A', {}).get('segmentos', '?')} segmentos).** {MOD_N} frente a la `{BASE_N}`: AUC {con_ic(MOD_N, 'AUC')} contra {con_ic(BASE_N, 'AUC')}; Fracción para 80 % {con_ic_pct(MOD_N, 'Fraccion para 80%')} contra {con_ic_pct(BASE_N, 'Fraccion para 80%')}. Las diferencias son {n3(B.get('dA', [float('nan')])[0], True)} de AUC (IC {n3(B.get('dA', [0, float('nan'), float('nan')])[1], True)} a {n3(B.get('dA', [0, 0, float('nan')])[2], True)}) y {n1(B.get('dF', [float('nan')])[0] * 100, True)} puntos de Fracción para 80 % (IC {n1(B.get('dF', [0, float('nan'), 0])[1] * 100, True)} a {n1(B.get('dF', [0, 0, float('nan')])[2] * 100, True)}): {'ambos IC incluyen 0, el modelo no se distingue de la regla' if B.get('no_dist') else 'al menos un IC excluye 0'} y {'no cumple' if not B.get('vlp') else 'cumple'} el criterio "vale la pena". En train (fuera de fold) la regla tuvo AUC {n3(top.get('AUC', float('nan')))}; en test cae a {n3(pun.get(BASE_N, {}).get('AUC', float('nan')))}.

**El punto A no se sostiene.** El corte fijado con train para un recall de 0,80 dio en test un recall de {ic3(OPA_B.get('recall'))} con la regla, revisando el {pc(OPA_B.get('pct_revisar', [float('nan')])[0])} de las cajas; la tolerancia del plan era {es(C10.get('D', {}).get('tol', ''))}. Ninguno de los {len(C10.get('D', {}).get('sostenido', {}))} métodos lo sostiene.

**Sin el segmento anómalo (post hoc, no pre-declarado).** El segmento `{L.get('foco', '?')}` aporta el {pc(foco_pos)} de los positivos del test y en él el AUC de la regla es {n3(L.get('auc_foco', {}).get('top', float('nan')))}. Sin él ({C10.get('A', {}).get('segmentos', 8) - 1} segmentos), el AUC es {n3(sf.get('auc', {}).get(MOD_N, float('nan')))} para el modelo y {n3(sf.get('auc', {}).get(BASE_N, float('nan')))} para la regla, el recall del punto A de la regla es {n3(C10.get('J', {}).get('recall_sin_foco', float('nan')))} y {sum(sf.get('sostenido', {}).values())} de {len(sf.get('sostenido', {}))} métodos sostienen el punto A. Esto describe cuánto depende el resultado de un segmento y no reemplaza el resultado oficial.

**Hallazgo del apéndice M (post hoc, no pre-declarado), con su advertencia.** En ese segmento la cámara {par_test.get('camara', '?')} tiene una tasa de pares de {n3(par_test.get('tasa', float('nan')))} dentro de su rango; la auditoría por cámara en {M.get('n_seg', '?')} segmentos halló {M.get('n_pares', '?')} pares (segmento, cámara) con hueco, uno en train (cámara {par_train.get('camara', '?')}) y uno en test. Advertencia: los criterios se escribieron después de ver el segmento anómalo, los dos casos son de San Francisco de día, no hay base para estimar su frecuencia en datos nuevos y el hueco puede ser de etiquetado o de los datos de esa cámara (no se distingue con los archivos disponibles).

**Recomendación en dos niveles (interpretación).** (1) Auditar cada segmento por cámara (tasa de pares de cada cámara dentro de su rango de azimut) para detectar huecos que la regla de puntos no ve. (2) Priorizar las cajas con la `{BASE_N}` para la revisión humana, con una persona en el circuito y sin reemplazarla, y monitorear el recall por segmento. Con 8 segmentos y pocos ciclistas, no afirmamos que `sin_camara` mida visibilidad física ni que el resultado generalice.
"""
    return t


# --------------------------------------------------------------------------------------------- 2. Problema
def sec2():
    pr = C9.get("principal", {})
    top, lr = pr.get(BASE_N, {}), pr.get(MOD_N, {})
    perm = leer_csv("09_importancia_permutacion.csv").rename(columns={"Unnamed: 0": "variable"})
    p0 = perm.iloc[0] if len(perm) else None
    _dec = DEC[DEC["target"] == "B"].set_index("criterio") if len(DEC) else pd.DataFrame()
    meta_auc = _dec.loc["AUC (todas las variables)", "umbral"] if len(_dec) else "?"
    meta_pr = _dec.loc["PR-AUC - prevalencia", "umbral"] if len(_dec) else "?"
    _cr = PLAN.get("criterios", {}).get("parametros", {})
    vlp_, ope_, est_, cal_ = _cr.get("vale_la_pena", {}), _cr.get("operacion", {}), _cr.get("estabilidad", {}), _cr.get("calibracion", {})
    tol_ = C10.get("D", {}).get("tol", ope_.get("recall_segmento_min", float("nan")))
    kpi_df, kpi_txt = tabla_kpis()
    t = f"""## 2. Problema, contexto, objetivos y KPIs

**Qué se audita.** Las cajas 3D etiquetadas (`lidar_box`) de peatones y ciclistas que no tienen su par 2D de cámara en la tabla de asociación cámara-LiDAR. No auditamos un detector: son etiquetas hechas por personas. La pregunta es cuáles etiquetas 3D quedaron sin su par 2D, y no si el auto "ve" al peatón.

**Por qué importa.** Las etiquetas 2D de cámara y las 3D de LiDAR se usan juntas para entrenar y evaluar modelos de percepción. Si una parte de las cajas no tiene par, conviene saber dónde están antes de entrenar o de comparar métricas por cámara. El contexto externo que citamos en el notebook 07 es de seguridad vial de peatones (ver referencias, sección 14); es contexto y no una cifra del proyecto.

**Cómo se usaría.** Como una lista priorizada para revisión humana, en dos niveles (sección 10): una auditoría por segmento y cámara, y después una regla de priorización de cajas. No reemplaza la revisión.

**Declaración del problema (con las cifras vigentes de la población principal).** **Problema.** El {pc(pr.get('Prevalencia (trivial)', {}).get('PR-AUC', float('nan')))} de las cajas 3D etiquetadas de peatones y ciclistas con |azimut| <= {C9.get('AZ_MAX', '?')}° (train) no tiene su par 2D de cámara, y hoy no se sabe cuáles son sin revisarlas. **Objetivo.** Estimar, con solo atributos de la caja 3D etiquetada, la probabilidad de que no tenga su par 2D y entregar una lista priorizada para revisión humana. **Métrica de éxito.** AUC y PR-AUC fuera de fold (regla `{BASE_N}`: {n3(top.get('AUC', float('nan')))} y {n3(top.get('PR-AUC', float('nan')))}; {MOD_N}: {n3(lr.get('AUC', float('nan')))} y {n3(lr.get('PR-AUC', float('nan')))}) y la fracción de cajas que hay que revisar para cubrir el 80 % de las cajas sin par ({pc(top.get('Fraccion para 80%', float('nan')))} con la regla, {pc(lr.get('Fraccion para 80%', float('nan')))} con la regresión logística y {pc(pr.get('Prevalencia (trivial)', {}).get('Fraccion para 80%', float('nan')))} al azar). **Alcance.** {len(SPLIT_TRAIN)} segmentos de train de Waymo Open Dataset v2, frames con etiquetas de cámara. **Limitación principal.** El puntaje depende sobre todo de los puntos LiDAR de la caja ({p0['variable'] if p0 is not None else '?'} domina la importancia por permutación del HGB, con una caída de AUC de {n3(p0.iloc[1]) if p0 is not None else '?'} en el notebook 09, población principal; el 08 reporta otra cifra con la población de 120°, ver sección 6): captura cobertura de etiquetado y calidad de observación, no visibilidad física de la cámara.

### 2.1 Objetivos

**Objetivo general.** Construir y evaluar, con validación por segmento y un test sellado, una lista priorizada de las cajas 3D etiquetadas de peatones y ciclistas, para encontrar las que no tienen par 2D de cámara revisando menos que al azar, y decir con intervalos de confianza si un modelo aporta algo frente a una regla simple.

**Objetivos específicos (medibles).**

1. Predecir `sin_camara` en la población principal con un AUC fuera de fold de al menos {n2(meta_auc)} y una diferencia entre PR-AUC y prevalencia de al menos {n2(meta_pr)} (metas del 07).
2. Reducir la fracción de cajas que hay que revisar para encontrar el 80 % de las cajas sin par frente al azar ({pc(pr.get('Prevalencia (trivial)', {}).get('Fraccion para 80%', float('nan')), 0)}) y frente a la regla más simple. Un modelo solo se recomienda si baja esa fracción al menos {int(round(abs(vlp_.get('delta_fraccion80_max', float('nan'))) * 100))} puntos con IC pareado que excluya 0 y su AUC sube al menos {n2(vlp_.get('delta_auc_min', float('nan')))}.
3. Fijar con train un punto de operación para un recall de {n2(ope_.get('recall_objetivo', float('nan')))} y comprobar en el test que el recall es al menos {n2(tol_)}.
4. Medir estabilidad, calibración y equidad: AUC mínimo por fold de al menos {n2(est_.get('auc_fold_min', float('nan')))}, mediana del AUC por segmento de al menos {n2(est_.get('auc_segmento_mediana_min', float('nan')))}, ECE de a lo sumo {n2(cal_.get('ece_max', float('nan')))} tras calibrar, y las brechas por momento del día y ubicación con su IC.

### 2.2 KPIs

Cada KPI tiene su meta fijada antes de mirar resultados. Los valores salen de los CSV de los notebooks 09 (train, fuera de fold) y 10 (test oficial pre-declarado); se muestra la regla recomendada (`{BASE_N}`) y la regresión logística (LR).

{tabla(kpi_df)}

{kpi_txt}

{parrafo_unidad()}

**Horas ilustrativas.** {frase_20s()}

*El notebook 07 contiene una declaración del problema con cifras de una versión previa del análisis (población de 120°: AUC 0,854 con todas las variables, prevalencia 23,2 %, 39,1 % de las cajas con el modelo; el 07 las llama frames). Esas cifras no se usan acá como vigentes; la sección 5 las compara con las vigentes.*
"""
    return t


# --------------------------------------------------------------------------------------------- 3. Datos
def sec3():
    sup, clus = SEG[SEG["uso"] == "supervisado"], SEG[SEG["uso"] == "solo_clustering"]
    por_split = SPL.groupby("conjunto").agg(segmentos=("segment_id", "size"), filas=("filas", "sum"), positivos=("positivos", "sum"), ciclistas=("ciclistas", "sum"))
    fb, fbp, folds = tasas_por_fold()
    cont = leer_csv("07_conteos_test.csv")
    pob = pd.DataFrame([
        {"población": "principal (azimut absoluto <= 100°)", "train: filas": len(fbp), "train: positivos de sin_camara": int(fbp["sin_camara"].sum()),
         "test: filas": int(cont["filas_B_principal"].sum()), "test: positivos de sin_camara": int(cont["sin_camara_principal"].sum())},
        {"población": "120° (principal más la franja 100-120°)", "train: filas": len(fb), "train: positivos de sin_camara": int(fb["sin_camara"].sum()),
         "test: filas": int(cont["filas_B_120"].sum()), "test: positivos de sin_camara": int(cont["sin_camara_120"].sum())},
    ])
    band = leer_csv("08_tasa_por_azimut.csv")
    todos = band[band["grupo"] == "todos"].copy() if len(band) else pd.DataFrame()
    if len(todos):
        todos = todos.rename(columns={todos.columns[1]: "tramo de azimut", "filas": "filas", "tasa": "tasa de sin_camara"})[["tramo de azimut", "filas", "tasa de sin_camara", "lo", "hi"]]
    lluvia_usada = notebooks_que_usan_lluvia()
    texto_lluvia = (f"{frase_lluvia()}, y **no se usaron en el modelado; solo en un análisis descriptivo post hoc (sección 7)**. No sirven para entrenar un target que depende del par 2D: {frase_lluvia_frames()}. "
                    "Ningún código de los notebooks 07 a 10 los usa (búsqueda de texto al generar este informe); la sección 7 incluye un análisis descriptivo post hoc con ellos." if not lluvia_usada else
                    f"{frase_lluvia()}; {frase_lluvia_frames()}; los notebooks que los mencionan en código son: {', '.join(lluvia_usada)}.")
    t = f"""## 3. Datos, preparación y calidad

**Fuente.** Waymo Open Dataset v2. Evaluamos {len(REG)} segmentos (`registro_verificacion_ep2.csv`) y seleccionamos {len(sup)} para el análisis supervisado (etiquetado denso y asociación cámara-LiDAR no vacía), que suman {miles(sup['n_detecciones'].sum())} detecciones. {texto_lluvia}

**Split por segmento.** Un segmento es una escena continua de 20 segundos; si dos fotogramas vecinos cayeran en lados distintos del split, el modelo "reconocería" la escena. Por eso todo el split es por segmento: {int(por_split.loc['train', 'segmentos'])} segmentos de train y {int(por_split.loc['test', 'segmentos'])} de test. `train.parquet` ({miles(por_split.loc['train', 'filas'])} filas) y `test.parquet` ({miles(por_split.loc['test', 'filas'])} filas) contienen **todas las clases de objeto** (vehículos, señales, peatones y ciclistas) de los frames etiquetados; el target de EP2 solo existe para peatones y ciclistas, que forman estas poblaciones:

{tabla(pob)}

**Folds.** El train se divide en 5 folds por segmento (`StratifiedGroupKFold`) estratificados por `tiene_camara` (el target de EP1), **no por `sin_camara`**; por eso la tasa de `sin_camara` por fold no se controló y va de {pc(folds['tasa de sin_camara'].min())} a {pc(folds['tasa de sin_camara'].max())}. Filas y positivos de la población principal por fold:

{tabla(folds)}

**Población principal y franja 100-120.** La población principal es |azimut| <= {C9.get('AZ_MAX', '?')}° ({miles(C9.get('filas_principal', 0))} de {miles(C9.get('filas_120', 0))} filas de train). En la franja 100-120° la tasa de `sin_camara` es mucho mayor, y en el último tramo de 5° llega casi al 100 %: ahí la ausencia de par es en buena parte geométrica (ninguna cámara mira hacia atrás) y no una laguna de etiquetado. Es como pedir el anexo de una foto que nadie pudo sacar. El borde de {C9.get('AZ_MAX', '?')}° es empírico: `camera_calibration` no está en los datos locales, y no verificamos el yaw de montaje de las cámaras (ver la sección 6 y Sun et al. (2020) en la sección 14).

{tabla(todos) if len(todos) else '(sin datos)'}

{figura('08_tasa_por_azimut.png', 'Tasa de sin_camara por azimut')}

**Test sellado.** Los {len(cont)} segmentos de test no se abrieron hasta el notebook 10. Solo se contaron filas y positivos por segmento para el plan (archivo `07_conteos_test.csv`):

{tabla(cont)}

{bloque_calidad()}
"""
    return t


# --------------------------------------------------------------------------------------------- 4. Metodologia
def tabla_crisp():
    filas = [
        ("1. Entendimiento del negocio", "Problema (auditar cajas 3D sin par 2D), objetivos, KPIs con metas fijadas antes, elección del target entre cinco candidatas", "Secciones 2 y 5; notebook 07", ["data/08_reporting/decision_target_ep2.csv", "docs/decision_target_ep2.md"]),
        ("2. Entendimiento de los datos", "Selección de segmentos, EDA, tasa de `sin_camara` por puntos, azimut, distancia y clase; geometría de cámaras; franja 100-120°", "Secciones 3 y 6; notebooks 00, 02, 06 y 08", ["docs/seleccion_segmentos/segmentos_ep2.csv", "data/08_reporting/08_tasa_por_puntos.csv", "data/08_reporting/08_tasa_por_azimut.csv"]),
        ("3. Preparación de los datos", "Ingesta con Kedro, filtro de frames etiquetados, población principal, variables derivadas, split por segmento con 5 folds", "Secciones 3 y 6; ingesta (Kedro) y notebooks 06 y 08", ["data/05_model_input/split_segmentos.csv", "data/05_model_input/features_B.parquet", "data/05_model_input/config_features_B.json"]),
        ("4. Modelado", "Baselines simples, regresión logística, HGB y Random Forest con búsqueda anidada por segmento; aprendizaje no supervisado", "Secciones 7 y 8; notebooks 08 y 09", ["data/08_reporting/09_comparacion_modelos.csv", "data/06_models/hiperparametros_B.json", "data/08_reporting/08_clusters_seleccion_k.csv"]),
        ("5. Evaluación", "Criterios fijados antes, plan de evaluación congelado con sha256, test sellado, influencia, equidad y sensibilidad", "Secciones 4 y 9; notebooks 09b y 10", ["data/06_models/plan_evaluacion_test.json", "data/08_reporting/10_resultado_principal.csv", "data/08_reporting/10_hashes_ejecucion1.json"]),
        ("6. Despliegue", "Recomendación de uso en dos niveles con una persona en el circuito, monitoreo y reproducibilidad (scripts, pruebas, paquete de entrega)", "Secciones 10 a 13", ["docs/evaluacion_final_B.md", "scripts/generar_informe_tecnico.py", "docs/informe_tecnico_EP2.md"]),
    ]
    out = []
    for fase, hecho, donde, archivos in filas:
        faltan = [a for a in archivos if not (R / a).exists()]
        if faltan:
            FALTAN.extend(faltan)
        out.append({"fase": fase, "qué se hizo": hecho, "sección y notebook": donde, "evidencia (archivo)": "; ".join(f"`{a}`" for a in archivos)})
    return pd.DataFrame(out)


def sec4():
    cr = PLAN.get("criterios", {}).get("parametros", {})
    vlp, est, ope, cal = cr.get("vale_la_pena", {}), cr.get("estabilidad", {}), cr.get("operacion", {}), cr.get("calibracion", {})
    cambios = PLAN.get("cambios_v1_v2", [])
    cambios_txt = "\n".join(f"{i}. **{c['cambio']}.** {c['por_que']}" for i, c in enumerate(cambios, 1))
    cong = archivos_congelados()
    tsha = pd.DataFrame({"archivo": [n for n, _ in cong], "sha256 (primeros 16 caracteres)": [v[:16] for _, v in cong]})
    t = f"""## 4. Metodología (CRISP-DM)

Seguimos las seis fases de CRISP-DM. Cada fila dice qué se hizo, dónde está y qué archivo lo respalda.

{tabla(tabla_crisp())}

**Criterios fijados antes de mirar resultados.** Cada notebook fija sus criterios en una celda antes de calcular y no los cambia al ver los números. Los de la evaluación final, tomados del plan congelado:

- "Vale la pena": la Fracción para 80 % del modelo baja al menos {pc(abs(vlp.get('delta_fraccion80_max', 0)), 0)} puntos frente al baseline, con IC 95 % pareado que excluya 0, y el AUC sube al menos {n3(vlp.get('delta_auc_min', 0))}.
- Elección entre modelos: ΔAUC >= {n3(cr.get('eleccion', {}).get('delta_auc_min', 0))} y ambos IC excluyen 0.
- Estabilidad: AUC mínimo por fold >= {n3(est.get('auc_fold_min', 0))} y mediana del AUC por segmento >= {n3(est.get('auc_segmento_mediana_min', 0))}.
- Operación: recall objetivo {n3(ope.get('recall_objetivo', 0))}, presupuesto de revisión {pc(ope.get('presupuesto_revision', 0), 0)} de las cajas; el punto A se considera sostenido en test si el recall puntual es >= {n3(ope.get('recall_segmento_min', 0))}.
- Calibración aceptable: ECE <= {n3(cal.get('ece_max', 0))}.

**Validación por segmento y prevención de fuga.** `StratifiedGroupKFold` por segmento; la búsqueda de hiperparámetros es anidada (`GroupKFold(3)` interno por segmento, criterio PR-AUC) dentro de cada fold externo; los umbrales de operación se fijan solo con predicciones internas de entrenamiento; el preprocesamiento se ajusta dentro de cada fold. Los intervalos son bootstrap por segmentos (remuestreo de segmentos completos, diferencias pareadas), porque las filas de un mismo segmento no son independientes. Con 8 segmentos de test los intervalos son anchos y así se reportan.

**Por qué comparar contra baselines simples.** Un modelo complejo solo se justifica si supera a una regla que se explica en una línea. Es como justificar un instrumento nuevo: hay que mostrar que mide mejor que la regla de medir a ojo. Los baselines son: menos puntos LiDAR, menos puntos de la parte alta (`{BASE_N}`), la regla geométrica (azimut > 105° primero, luego menos puntos) y un modelo mínimo de 3 variables.

**Plan de evaluación del test congelado.** Antes de abrir el test se congelaron modelos, umbrales, calibrador y criterios con sha256 (`data/06_models/plan_evaluacion_test.json`, plan en `docs/plan_evaluacion_test.md`). Hubo una versión v1 y una v2 (v1 conservada); la v2 se congeló el {PLAN.get('congelado', '?')}. Cambios de la v2 respecto de la v1:

{cambios_txt}

Archivos congelados (sha256 verificado al inicio del notebook 10): son {len(cong)}, los {len(cong) - 2} de `sha256.archivos` de `plan_evaluacion_test.json` (modelos, calibrador, hiperparámetros y configuración de variables, también los de 120°) más `features_B.parquet` y `plan_evaluacion_test_v1.json`. `plan_evaluacion_test.json` no se incluye porque guarda los sha256 y no se hashea a sí mismo. `scripts/verificar_congelados.py` comprueba los mismos {len(cong)}.

{tabla(tsha)}
"""
    return t


# --------------------------------------------------------------------------------------------- 5. Target
def sec5():
    cand = rotular_previa(bloque(DOC07, "**Candidatas descartadas**", "**Valor práctico", fuente="07"))
    dec = DEC.copy()
    cond = DEC[(DEC["target"] == "B") & DEC["criterio"].str.startswith("AUC (todas")]["valor"].iloc[0] if len(DEC) else "?"
    conteos = leer_csv("07_conteos_test.csv")
    cmp = leer_csv("08_comparacion_sin_franja.csv")
    s120 = leer_csv("09_sensibilidad_120.csv")
    pr = C9.get("principal", {})
    top, lr = pr.get(BASE_N, {}), pr.get(MOD_N, {})
    fila = lambda poblacion, metodo: cmp[(cmp["poblacion"] == poblacion) & (cmp["metodo"] == metodo)].iloc[0] if len(cmp) else None
    hgb120, regla120 = fila("B completa", "HGB"), fila("B completa", "Regla: menos puntos LiDAR primero")
    dif = C9.get("dif_f80_120_vs_regla_geometrica", {}).get("HGB", [float("nan")] * 3)
    dif_pts = C9.get("dif_f80_120_vs_regla_puntos", {}).get("HGB", [float("nan")] * 3)
    vig = pd.DataFrame([
        {"cifra del 07": "Prevalencia de sin_camara", "valor en el 07 (versión previa, 120°)": es(DEC[DEC['criterio'].str.startswith('prevalencia')]['valor'].iloc[0]) if len(DEC) else "?", "valor vigente": f"{n3(pr.get('Prevalencia (trivial)', {}).get('PR-AUC', float('nan')))} (población principal, train)", "fuente del valor vigente": "09_resumen_cifras.json"},
        {"cifra del 07": "AUC con todas las variables", "valor en el 07 (versión previa, 120°)": es(cond), "valor vigente": f"{MOD_N} {n3(lr.get('AUC', float('nan')))}; {BASE_N} {n3(top.get('AUC', float('nan')))}", "fuente del valor vigente": "09_comparacion_modelos.csv"},
        {"cifra del 07": "AUC mínimo por fold", "valor en el 07 (versión previa, 120°)": es(DEC[DEC['criterio'].str.startswith('AUC minimo')]['valor'].iloc[0]) if len(DEC) else "?", "valor vigente": f"{MOD_N} {n3(pd.read_csv(REP / '09_auc_por_fold.csv', index_col=0)[MOD_N].min())}", "fuente del valor vigente": "09_auc_por_fold.csv"},
        {"cifra del 07": "Fracción para 80 % con el modelo", "valor en el 07 (versión previa, 120°)": pc(float(hgb120['Fraccion para 80%'].split()[0])) + " (HGB)" if hgb120 is not None else "?", "valor vigente": f"{MOD_N} {pc(lr.get('Fraccion para 80%', float('nan')))}; {BASE_N} {pc(top.get('Fraccion para 80%', float('nan')))} (población principal)", "fuente del valor vigente": "09_comparacion_modelos.csv"},
        {"cifra del 07": "Fracción para 80 % con la regla de puntos", "valor en el 07 (versión previa, 120°)": pc(float(regla120['Fraccion para 80%'].split()[0])) if regla120 is not None else "?", "valor vigente": f"{BASE_N} {pc(top.get('Fraccion para 80%', float('nan')))} (principal)", "fuente del valor vigente": "09_comparacion_modelos.csv"},
        {"cifra del 07": "Diferencia modelo menos regla (Fracción para 80 %)", "valor en el 07 (versión previa, 120°)": "-11,4 puntos (HGB menos regla de puntos, IC 95 % -19,0 a -6,1)", "valor vigente": f"HGB menos regla de puntos en 120°: {n1(dif_pts[0] * 100, True)} puntos (IC {n1(dif_pts[1] * 100, True)} a {n1(dif_pts[2] * 100, True)}); HGB menos regla geométrica en 120°: {n1(dif[0] * 100, True)} puntos (IC {n1(dif[1] * 100, True)} a {n1(dif[2] * 100, True)})", "fuente del valor vigente": "09_resumen_cifras.json"},
        {"cifra del 07": "Conteos del test (filas / positivos)", "valor en el 07 (versión previa, 120°)": f"{miles(conteos['filas_B_120'].sum())} / {miles(conteos['sin_camara_120'].sum())}" if len(conteos) else "?", "valor vigente": f"{miles(conteos['filas_B_principal'].sum())} / {miles(conteos['sin_camara_principal'].sum())} (población principal)" if len(conteos) else "?", "fuente del valor vigente": "07_conteos_test.csv"},
    ])
    t = f"""## 5. Elección del target (notebook 07)

Antes de modelar comparamos cinco candidatas con criterios fijados antes de calcular (`decision_target_ep2.csv`):

- A: `tiene_camara` en todos los objetos.
- B: `sin_camara` en peatones y ciclistas dentro de la zona de cámaras.
- C: desplazamiento a 2 segundos (regresión).
- D: peatón frente a ciclista.
- E: conflicto con el corredor del auto a 2 segundos.

**Decisión: B.** Resumen generado por el notebook 07. Las cifras de B (AUC, prevalencia, fracciones de revisión, diferencia modelo menos regla) son de una versión previa del análisis con la población de 120°, y se rotularon así; la tabla siguiente las compara con las vigentes.

{cita(rotular_previa(RES07.split('Detalle del problema')[0]), '07')}

**Cifras del 07 que la nota "Actualización posterior al 08 y 09" dejó desactualizadas, y su valor vigente** (cada valor vigente sale de los archivos indicados):

{tabla(vig, raw=True)}

Tabla de descarte (generada por el notebook 07; las cifras de A, C, D y E no dependen del borde de azimut):

{cand}

Tabla de criterios (cada fila es un criterio fijado antes; los valores de B son de la versión previa, población de 120°). Leyenda de las columnas: `umbral` es el valor fijado antes; `valor` es lo observado; `cumple` dice si el valor cumple el umbral; `decide` dice si el criterio cuenta para el veredicto del target (`False` significa que solo es informativo y no decide):

{tabla(dec) if len(dec) else '(sin datos)'}

{figura('07_A_modelo_vs_reglas.png', 'Candidata A: modelo frente a reglas')}

La analogía: A es como medir si una pelota es una pelota; el modelo acierta porque los vehículos nunca tienen el problema, no porque entienda las cámaras. B es la pregunta que sí tiene incertidumbre.

Nota de actualización que el propio 07 conserva (generada por el notebook; sus cifras antiguas están rotuladas como versión previa):

{cita(rotular_previa(leer_txt(REP / 'actualizacion_07.md')), '07')}
"""
    return t


# --------------------------------------------------------------------------------------------- 6. Analisis
FOV08 = next((c for c in celdas_md("08_analisis_observabilidad_sin_camara") if "Campo de visión de las cámaras" in c), "")
FOV08 = FOV08[FOV08.index("**Campo de visión"):].strip() if FOV08 else "(el notebook 08 no contiene el párrafo sobre campo de visión)"


def sec6():
    _c = leer_csv("08_comparacion_sin_franja.csv")
    cmp08_120 = _c[(_c["poblacion"] == "B completa") & (_c["metodo"] == "HGB")].iloc[0] if len(_c) else None
    _fov = re.search(r"±(\d+,\d+)", FOV08)
    fov_txt = _fov.group(1) if _fov else "?"
    _az = leer_csv("08_tasa_azimut_5grados.csv").rename(columns={"Unnamed: 0": "tramo"})
    tz = {k: (pc(float(_az[_az["tramo"] == v]["tasa"].iloc[0])) if len(_az) and (_az["tramo"] == v).any() else "?") for k, v in {"105": "(105, 110]", "110": "(110, 115]", "115": "(115, 120]"}.items()}
    pts = leer_csv("08_tasa_por_puntos.csv").rename(columns={"Unnamed: 0": "puntos LiDAR"})
    cv = leer_csv("08_conjuntos_variables.csv")
    cvv = cv[["conjunto", "AUC", "Fraccion para 80%", "dAUC", "dFraccion para 80%", "ayuda"]] if len(cv) else cv
    imp = leer_csv("08_importancia_permutacion.csv").rename(columns={"Unnamed: 0": "variable"})
    segs = leer_csv("08_auc_por_segmento.csv")
    minf = PLAN.get("criterios", {}).get("parametros", {}).get("estabilidad", {}).get("min_filas_clase_segmento", 200)
    if len(segs):
        ev = segs[(segs["sin"] >= minf) & (segs["con"] >= minf)]
        mm = ["HGB", "Regresion logistica", "Regla: menos puntos LiDAR primero"]
        resseg = pd.DataFrame({"segmentos evaluables": len(ev), "mediana": ev[mm].median(), "Q1": ev[mm].quantile(0.25), "Q3": ev[mm].quantile(0.75)}).reset_index().rename(columns={"index": "método"})
    else:
        ev, minf = pd.DataFrame(), minf
        resseg = pd.DataFrame()
    t = f"""## 6. Análisis de datos (notebook 08)

**Qué determina `sin_camara`.** La variable dominante son los puntos LiDAR: cuanto menos puntos tiene la caja, más probable es que no tenga par. La analogía: una persona que casi no aparece en la foto no recibe su recuadro. El efecto es gradual (tasa por tramo de puntos en la población de 120°, {miles(pts['filas'].sum()) if len(pts) else '?'} filas de train):

{tabla(pts)}

{figura('08_tasa_por_puntos_clase_distancia.png', 'Tasa de sin_camara por puntos, clase y distancia')}

Resumen generado por el notebook 08. **Las cifras de este resumen se calcularon con la población de 120° completa** (por ejemplo, el AUC del HGB de {es(cmp08_120['AUC'].split()[0]) if cmp08_120 is not None else '?'} coincide con la fila "B completa" de `08_comparacion_sin_franja.csv`); en la población principal las cifras vigentes son las de la sección 8.

{cita(RES08.split('**Qué llevar al 09.**')[0], '08')}

{figura('08_pareado_objetos_mixtos.png', 'Comparación pareada dentro de objetos mixtos (más puntos en los frames con par)')}

**Importancia por permutación (caída de AUC del HGB en el notebook 08, población de 120°; no es comparable con la del notebook 09, que usa la población principal).**

{tabla(imp.head(8))}

**Robustez por segmento.** AUC por segmento en train (08), solo segmentos evaluables (al menos {minf} cajas de cada clase):

{tabla(resseg) if len(resseg) else '(sin datos)'}

{figura('08_auc_por_segmento.png', 'AUC por segmento')}

**Variables nuevas (temporales y de oclusión).** Se evaluaron con un criterio fijado antes (descrito en el resumen del 08 citado arriba) y con la población de 120° completa. La columna `ayuda` dice si el conjunto lo cumplió:

{tabla(cvv) if len(cvv) else '(sin datos)'}

{figura('08_conjuntos_variables.png', 'Conjuntos de variables')}

**Geometría de cámaras.** `camera_calibration` no está en los datos locales; el 08 usa la tabla de asociación (`key.camera_name`) para describir el azimut de las cajas asociadas por cámara. Eso no es calibración: no da yaw ni campo de visión. La Tabla 3 de Sun et al. (2020) da un campo de visión horizontal de ±{fov_txt}° para las cinco cámaras. No verificamos el yaw de montaje de cada una. Los rangos empíricos del 08 (tabla siguiente) son consistentes con cámaras laterales centradas cerca de ±90°, cuya cobertura llegaría hasta unos 115°, y con que la tasa de `sin_camara` pase de {tz['105']} en 105-110° a {tz['110']} en 110-115° y {tz['115']} en 115-120° (`08_tasa_azimut_5grados.csv`). Es una hipótesis geométrica que debe validarse con `camera_calibration`; no cambia la población principal, cuyo corte de 100° es conservador.

{tabla(leer_csv('08_azimut_por_camara_empirico.csv'))}

{figura('08_geometria_camaras.png', 'Azimut de las cajas asociadas por cámara')}
"""
    return t


# --------------------------------------------------------------------------------------------- 7. No supervisado
def sec7():
    sel = leer_csv("08_clusters_seleccion_k.csv")
    perfil = leer_csv("08_clusters_perfil.csv").rename(columns={"Unnamed: 0": "cluster"})
    k34 = leer_csv("08_clusters_k3_k4.csv").rename(columns={"Unnamed: 1": "cluster"})
    franja = leer_csv("08_clusters_vs_franja.csv")
    ari, est, iso, dif = NS["ari_entre_tecnicas"], NS["estabilidad_por_segmento"], NS["isolation_forest"], NS["diferencia_con_signo_clusters"]
    bic = leer_json(REP / "08_post_hoc_gmm_bic.json")
    if len(sel) and bic:
        b = sel["BIC GMM"]
        sc = bic["gmm_solo_continuas"]
        var_min = '%.1e' % bic['gmm_completo']['k3']['varianza_minima']
        var_min = var_min.replace('.', ',')
        texto_bic = (f"El BIC del GMM no se usó para elegir k: pasa de {fmt_bic(float(b.iloc[0]))} (k = 2) a {fmt_bic(float(b.iloc[1]))} (k = 3) y sigue bajando hasta {fmt_bic(float(b.iloc[-1]))} (k = {int(sel['k'].iloc[-1])}), lo que no es una curva interpretable. "
                     f"Un diagnóstico post hoc, no pre-declarado (`scripts/diagnostico_post_hoc_08.py`), reprodujo el ajuste y encontró la causa más probable: en k = 3 la varianza mínima de un componente es {var_min}, igual al piso de regularización de scikit-learn, es decir, covarianzas degeneradas en las variables discretas (`n_ocl`, `frac_cub`, `dist_ocl_f`), que disparan la verosimilitud. "
                     f"Sin esas variables el BIC es {fmt_bic(sc['k2']['bic'])} (k = 2), {fmt_bic(sc['k3']['bic'])} (k = 3) y {fmt_bic(sc['k4']['bic'])} (k = 4). No lo usamos para elegir k en ningún caso.")
    else:
        texto_bic = "El BIC del GMM no se usó para elegir k (falta `08_post_hoc_gmm_bic.json`; ejecutar `scripts/diagnostico_post_hoc_08.py`)."
    nom_k2 = str(perfil[perfil["cluster"] == 1]["nombre"].iloc[0]) if len(perfil) else "?"
    nom_k4 = str(k34[(k34["k"] == "k4") & (k34["cluster"] == 3)]["nombre"].iloc[0]) if len(k34) else "?"
    if len(k34):
        k4_ = k34[k34["k"] == "k4"]
        c_alto = k4_.loc[k4_["tasa"].idxmax()]
        n_tot = float(k4_["filas"].sum())
        texto_negocio7 = (f"""### Lectura de negocio

1. Los clusters se pueden leer como tramos de la cola de revisión: grupos de cajas que se parecen en distancia, densidad y oclusión y que la persona que revisa vería como "tipos de caso".
2. El cluster «{c_alto['nombre']}» (k = 4) reúne {pc(float(c_alto['filas']) / n_tot)} de las cajas y tiene una tasa de `sin_camara` de {pc(float(c_alto['tasa']))} (IC {pc(float(c_alto['lo']))} a {pc(float(c_alto['hi']))}): ahí cerca de {round(float(c_alto['tasa']) * 10)} de cada 10 cajas no tienen par.
3. Los otros tres clusters están entre {pc(float(k4_['tasa'].min()))} y {pc(float(k4_[k4_['nombre'] != c_alto['nombre']]['tasa'].max()))}: son la parte de la cola donde revisar rinde menos.
4. Los clusters no mejoran la predicción: la probabilidad media del modelo en ese cluster ({n3(float(c_alto['prob_media_modelo']))}) ya sigue su tasa ({n3(float(c_alto['tasa']))}), así que no aportan información que el modelo no tenga.
5. Sí ayudan a explicar y a comunicar: permiten decirle a quien revisa "estas cajas son lejanas, con pocos puntos y detrás de otras, por eso suelen no tener par", y a elegir cuándo cortar la revisión.""")
    else:
        texto_negocio7 = ""
    ll_t = leer_csv("08_post_hoc_lluvia_clusters.csv")
    ll_r = leer_json(REP / "08_post_hoc_lluvia_resumen.json")
    if len(ll_t) and ll_r:
        vista_ll = ll_t[["k", "cluster", "filas_train", "% train", "filas_lluvia", "% lluvia"]].copy()
        texto_lluvia7 = (f"### Segmentos de lluvia (post hoc, no pre-declarado)\n\nLos {ll_r['segmentos_lluvia']} segmentos de lluvia no se usaron en EP2 (sección 3). Como análisis descriptivo, asignamos sus {miles(ll_r['cajas_peatones_ciclistas_<=120'])} peatones y ciclistas con |azimut| <= 120° ({ll_r['cajas_ciclistas']} ciclistas) a los clusters de KMeans con k = 2 y k = 4, reajustados con la misma semilla en train (reproducen los tamaños de `08_clusters_perfil.csv` y `08_clusters_k3_k4.csv`: "
                         f"{'sí' if all(ll_r['clusters_reproducen_08'].values()) else 'no'}) y con el mismo escalador. No usa el target, no toca `features_B.parquet`, y, como {frase_lluvia_frames()}, se usan todos los frames de los {ll_r['segmentos_lluvia']} segmentos. Con tan pocas cajas es solo una descripción de composición:\n\n{tabla(vista_ll)}\n\n"
                         f"Con k = 2, el {pc(float(ll_t[(ll_t['k'] == 2) & (ll_t['cluster'] == 1)]['% lluvia'].iloc[0]))} de las cajas de lluvia cae en el cluster «{nom_k2}», frente al {pc(float(ll_t[(ll_t['k'] == 2) & (ll_t['cluster'] == 1)]['% train'].iloc[0]))} en train; con k = 4, el {pc(float(ll_t[(ll_t['k'] == 4) & (ll_t['cluster'] == 3)]['% lluvia'].iloc[0]))} cae en el cluster «{nom_k4}» (train: {pc(float(ll_t[(ll_t['k'] == 4) & (ll_t['cluster'] == 3)]['% train'].iloc[0]))}). "
                         "La comparación no es pareja: los segmentos de lluvia usan todos sus frames y train usa solo los etiquetados. La composición es distinta, pero con 109 cajas, sin ciclistas y sin etiquetas no sacamos conclusiones sobre `sin_camara` en lluvia.".replace("109 cajas", f"{miles(ll_r['cajas_peatones_ciclistas_<=120'])} cajas"))
    else:
        texto_lluvia7 = "*(Falta el análisis de lluvia: ejecutar `scripts/diagnostico_post_hoc_08.py`.)*"
    t = f"""## 7. Aprendizaje no supervisado (notebook 08, sección D, y exploración con k = 3 y 4)

**Para qué.** El no supervisado no entrena nada contra `sin_camara`: pregunta si las cajas se agrupan solas en tipos de observación y si esos tipos se parecen a los grupos con más o menos pares. Es como ordenar las fotos por parecido sin mirar la etiqueta, y recién después ver cuántas tienen anexo.

**Técnicas y métricas.** KMeans, mezcla gaussiana (GMM) y agrupamiento jerárquico (Ward) sobre variables de distancia, azimut, puntos (en logaritmo), densidad, volumen y oclusión; para elegir k: silhouette, Davies-Bouldin, Calinski-Harabasz y BIC del GMM.

{tabla(sel) if len(sel) else '(sin datos)'}

El k elegido por máximo silhouette de KMeans es {NS['k_elegido']}. Concordancia entre técnicas (ARI): {', '.join(f'{k} {n3(v)}' for k, v in ari.items())}. Estabilidad por segmento ({est['remuestreos']} remuestreos): ARI medio {n3(est['ari_medio'])} y mínimo {n3(est['ari_minimo'])}. Diferencia con signo entre los dos clusters en la tasa de `sin_camara`: {n1(dif['puntos'])} puntos (IC 95 % por segmentos {n1(dif['ic_lo'])} a {n1(dif['ic_hi'])}; {'excluye' if dif['excluye_0'] else 'incluye'} 0). Estas cifras vienen de `data/08_reporting/08_no_supervisado_resumen.json`, extraído una vez del notebook 08 con `scripts/extraer_no_supervisado_08.py`.

{texto_bic}

**Perfiles con k = 2 (el elegido) y su cruce con `sin_camara`.** La tasa de cada cluster tiene IC 95 % por segmentos:

{tabla(perfil[['cluster', 'filas', 'tasa', 'lo', 'hi', 'prob_media_modelo', '% ciclistas', 'distancia_m', 'num_lidar_points', 'nombre']]) if len(perfil) else '(sin datos)'}

{figura('08_clusters_tasa.png', 'Tasa de sin_camara por cluster')}

**Exploración con k = 3 y 4.** Con más clusters aparece uno de objetos lejanos, con pocos puntos y oclusores, donde la tasa de `sin_camara` es la más alta (en k = 4):

{tabla(k34[['k', 'cluster', 'filas', 'tasa', 'lo', 'hi', 'distancia_m', 'num_lidar_points', 'nombre']]) if len(k34) else '(sin datos)'}

**Cruce con la franja 100-120°** (los clusters se calcularon con la población completa de 120°):

{tabla(franja) if len(franja) else '(sin datos)'}

**Detección de atípicos.** IsolationForest marca {miles(iso['cajas_atipicas'])} cajas atípicas ({iso['porcentaje']} %) en {iso['segmentos']} segmentos, con tasa de `sin_camara` {pc(iso['tasa_sin_camara_atipicas'])} frente a {pc(iso['tasa_sin_camara_resto'])} en el resto.

{figura('08_clusters_pca.png', 'Clusters sobre PCA')}

{texto_lluvia7}

{texto_negocio7}

**Qué se concluye.** Hay una estructura útil según el criterio fijado antes (silhouette, estabilidad por segmento y rango de tasas con IC que excluye 0; ver el resumen del 08): los clusters se parecen a las zonas de pocos y muchos puntos. **Qué no se concluye.** Los clusters no agregan información predictiva: las probabilidades del modelo ya siguen esas tasas (columna `prob_media_modelo`). Describen, no predicen mejor.
"""
    return t


# --------------------------------------------------------------------------------------------- 8. Supervisado
def _explicar_class_weight(cwt, m_cfg):
    """Texto de 09_class_weight.csv por modelo y, si la tabla da ganador distinto del peso final, la explicación con la selección anidada por fold."""
    if not len(cwt):
        return "(sin dato)", ""
    partes, gana = [], {}
    for m_, r_ in cwt.iterrows():
        a, b = float(r_.get("None", float("nan"))), float(r_.get("balanced", float("nan")))
        gana[m_] = "sin peso" if a >= b else "balanced"
        veredicto = f"empate a 3 decimales; gana {gana[m_]} por {es(f'{abs(a - b):.4f}')}" if round(a, 3) == round(b, 3) else f"gana {gana[m_]}"
        partes.append(f"{m_}: sin peso {n3(a)} frente a balanced {n3(b)} ({veredicto})")
    hpf = leer_csv("09_hiperparametros_por_fold.csv", keep_default_na=False)
    fin = HIP.get("final", {})
    peso_fin = {m_: ("sin peso" if fin.get(m_, {}).get("cfg", {}).get("class_weight") is None else fin[m_]["cfg"]["class_weight"]) for m_ in ("LR", "HGB")}
    cuenta = {m_: hpf[hpf["modelo"] == m_]["class_weight"].map(lambda v: "balanced" if v == "balanced" else "sin peso").value_counts() for m_ in ("LR", "HGB")}
    if any(gana.get(m_) != peso_fin[m_] for m_ in ("LR", "HGB")):
        h = cuenta["HGB"]
        dif_h = es(f"{abs(float(cwt.loc['HGB', 'None']) - float(cwt.loc['HGB', 'balanced'])):.4f}")
        exp = (f" **Por qué el HGB quedó {peso_fin['HGB']} aunque la tabla dé como ganador a {gana['HGB']}:** esa tabla promedia la mejor configuración de cada fold y la diferencia es de "
               f"{dif_h}, que no separa una opción de la otra. En la selección anidada por fold (`09_hiperparametros_por_fold.csv`) el HGB eligió balanced en "
               f"{int(h.get('balanced', 0))} de {int(h.sum())} folds y sin peso en {int(h.get('sin peso', 0))} (LR: balanced en {int(cuenta['LR'].get('balanced', 0))} y sin peso en {int(cuenta['LR'].get('sin peso', 0))}); "
               f"el ajuste final repite la búsqueda con todo el train y su mejor configuración de {m_cfg.get('HGB', '?')} quedó {peso_fin['HGB']} (PR-AUC interno {n3(fin['HGB']['pr_auc_interno'])}).")
    else:
        exp = ""
    return "; ".join(partes), exp


def sec8():
    comp = leer_csv("09_comparacion_modelos.csv")
    fin = HIP.get("final", {})
    cfg = pd.DataFrame([{"modelo": k, "configuración final": json.dumps({a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.get("cfg", {}).items()}, ensure_ascii=False), "PR-AUC interno": v.get("pr_auc_interno", float("nan"))} for k, v in fin.items()])
    cw = leer_csv("09_class_weight.csv", keep_default_na=False)
    m_cfg = {m_.group(1): m_.group(2) for m_ in re.finditer(r"(Regresion logistica|HGB|Random Forest): [\d, ]+ configuraciones reales por fold \(ajuste final: (\d+)\)", RES09)}
    if len(m_cfg) < 3:
        fallar("no se encontraron en el resumen del 09 las cantidades de configuraciones por modelo.")
    import importlib.util as _iu
    imblearn = _iu.find_spec("imblearn") is not None
    prev = C9.get("principal", {}).get("Prevalencia (trivial)", {}).get("PR-AUC", float("nan"))
    cwt = cw.pivot_table(index="modelo", columns="class_weight", values="mejor PR-AUC interno (promedio de folds)", aggfunc="max") if len(cw) else pd.DataFrame()
    cw_txt, cw_exp = _explicar_class_weight(cwt, m_cfg)
    cfg_fin = HIP.get("final", {})
    texto_algoritmos = f"""### Por qué estos algoritmos y esta configuración

1. **Regresión logística:** es la referencia lineal e interpretable (coeficientes y odds ratios en la tabla de abajo) y es el modelo que el 09 eligió para la comparación principal con la regla.
2. **HGB:** captura interacciones y relaciones no lineales sin transformar las variables; **Random Forest:** es robusto y poco sensible a los hiperparámetros, y sirve de contraste a un modelo de árboles de otro tipo.
3. **Hiperparámetros buscados** (búsqueda anidada por segmento, criterio PR-AUC): en la LR, la regularización `C` y el `class_weight` ({m_cfg.get('Regresion logistica', '?')} configuraciones); en el HGB, hojas, mínimo de muestras por hoja, regularización L2, tasa de aprendizaje, iteraciones y monotonía ({m_cfg.get('HGB', '?')} configuraciones); en el RF, profundidad, mínimo de muestras por hoja y variables por división ({m_cfg.get('Random Forest', '?')} configuraciones). Con solo {len(SPLIT_TRAIN)} segmentos de train, controlan el sobreajuste.
4. **`class_weight`** se evaluó (`09_class_weight.csv`, mejor PR-AUC interno promedio de los folds): {cw_txt}.{cw_exp} En los modelos finales, el peso de clases quedó en: LR {'sin peso' if cfg_fin.get('LR', {}).get('cfg', {}).get('class_weight') is None else cfg_fin.get('LR', {}).get('cfg', {}).get('class_weight')} y HGB {'sin peso' if cfg_fin.get('HGB', {}).get('cfg', {}).get('class_weight') is None else cfg_fin.get('HGB', {}).get('cfg', {}).get('class_weight')}.
5. **No usamos SMOTE:** `imbalanced-learn` {'está instalado' if imblearn else 'no está instalado en el entorno del proyecto (comprobado al generar este informe)'} y la prevalencia de `sin_camara` es {pc(prev)}, que no es un desbalance extremo; con ese nivel, el peso de clases y las métricas de ranking (AUC, PR-AUC, fracción para 80 %) bastan para comparar."""
    diag = leer_csv("09_diagnostico_agrupado.csv")
    _mods = [MOD_N, "HGB", "Random Forest", "Modelo minimo (LR 3 variables)"]
    _d = diag[(diag["referencia"] == BASE_N) & diag["modelo"].isin(_mods)] if len(diag) else diag
    dif_fold = _d[(_d["parte"] == "por fold") & _d["metrica"].isin(["AUC", "Fraccion para 80%"])][["modelo", "metrica", "rango por fold", "folds donde el modelo supera", "IC95% (segmentos)"]] if len(_d) else _d
    dif_seg = _d[_d["parte"] == "por segmento"][["modelo", "segmentos", "mediana dif AUC", "IQR", "proporcion donde el modelo supera", "IC95% mediana"]] if len(_d) else _d
    br = leer_json(REP / "09_equidad_brechas.json").get("brechas", [])
    if br:
        texto_brechas = "Brechas de equidad en train con IC 95 % por segmentos (09): " + "; ".join(
            f"{b_['grupo']} menos {b_['referencia']}: AUC {n3(b_['auc_dif'], True)} (IC {n3(b_['auc_lo'], True)} a {n3(b_['auc_hi'], True)}; {'incluye 0' if b_['auc_incluye_0'] else 'excluye 0'}) y recall al punto A {n3(b_['recall_dif'], True)} (IC {n3(b_['recall_lo'], True)} a {n3(b_['recall_hi'], True)}; {'incluye 0' if b_['recall_incluye_0'] else 'excluye 0'})"
            for b_ in br) + ". Los intervalos son anchos y ninguno permite afirmar una brecha. Las cifras vienen de `09_equidad_brechas.json`, extraído una vez del notebook 09 con `scripts/extraer_equidad_09.py`."
    else:
        texto_brechas = "El IC de las brechas de equidad no se calculó o no se pudo leer (falta `09_equidad_brechas.json`)."
    cal = leer_csv("09_calibracion.csv")
    coef = leer_csv("09_coeficientes_lr.csv")
    perm = leer_csv("09_importancia_permutacion.csv").rename(columns={"Unnamed: 0": "variable"})
    err = leer_csv("09_perfil_errores.csv")
    eq = leer_csv("09_equidad.csv")
    po = leer_csv("09_puntos_operacion.csv")
    po = po[po["punto"].str.startswith("A") | po["punto"].str.startswith("B")] if len(po) else po
    t = f"""## 8. Modelos supervisados (notebook 09)

**Modelos y baselines.** Regresión logística (LR), `HistGradientBoosting` (HGB) y Random Forest (RF), contra cuatro baselines simples. Ajuste de hiperparámetros anidado (por segmento) con búsqueda acotada (la cantidad de configuraciones por modelo está en las limitaciones del resumen del 09, citado más abajo). Semilla {HIP.get('semilla', '?')}. Configuraciones finales (entrenadas con todo el train):

{tabla(cfg)}

{texto_algoritmos}

**Resultados en train, fuera de fold, población principal** (IC 95 % por bootstrap de segmentos):

{tabla(comp) if len(comp) else '(sin datos)'}

{nota_regla_geometrica()}

{figura('09_comparacion_modelos.png', 'Comparación de modelos y baselines')}

Resumen generado por el notebook 09:

{cita(RES09.split('Este notebook no abre el test')[0], '09')}

**Diagnóstico de la métrica agrupada frente a por fold y por segmento.** El AUC agrupado mezcla las predicciones de cinco modelos distintos (uno por fold), lo que puede castigar a los modelos más que a las reglas, que no cambian entre folds. Por eso comparamos también por fold y por segmento (archivo completo: `data/08_reporting/09_diagnostico_agrupado.csv`):

Frente a la `{BASE_N}`, por fold (AUC y Fracción para 80 %):

{tabla(dif_fold) if len(dif_fold) else '(sin datos)'}

Frente a la `{BASE_N}`, por segmento (diferencia de AUC por segmento, modelo menos regla):

{tabla(dif_seg) if len(dif_seg) else '(sin datos)'}

**Calibración (modelo recomendado, fuera de fold).**

{tabla(cal) if len(cal) else '(sin datos)'}

{figura('09_calibracion.png', 'Curva de confiabilidad')}

**Interpretación.** Coeficientes de la regresión logística (por desviación estándar) y permutación del HGB:

{tabla(coef[['variable', 'coeficiente', 'odds ratio (+1 DE)', 'OR lo', 'OR hi', 'significativa']].head(8)) if len(coef) else '(sin datos)'}

Importancia por permutación del HGB en el notebook 09 (caída de AUC, población principal):

{tabla(perm.head(6)) if len(perm) else ''}

{figura('09_coeficientes_lr.png', 'Coeficientes de la regresión logística')}

{figura('09_dependencia_parcial.png', 'Dependencia parcial')}

**Análisis de errores.** Perfil de aciertos y errores del punto A:

{tabla(err) if len(err) else '(sin datos)'}

**Puntos de operación en train (A: recall objetivo 0,80; B: revisar 20 %):**

{tabla(po[['metodo', 'punto', 'recall', 'precision', 'pct_revisar']]) if len(po) else '(sin datos)'}

**Equidad en train (fuera de fold), punto A:**

{tabla(eq[['variable', 'grupo', 'segmentos', 'filas', 'sin_camara', 'AUC', 'recall_A', 'precision_A', 'pct_revisar_A']].assign(variable=lambda d: d['variable'].str.rstrip('_'))) if len(eq) else '(sin datos)'}

{texto_brechas}
"""
    return t


# --------------------------------------------------------------------------------------------- 9. Test
def sec9():
    rp = leer_csv("10_resultado_principal.csv")
    mp = leer_csv("10_metodos_poblacion_principal.csv")
    po = leer_csv("10_puntos_de_operacion.csv")
    po = po[po["punto"].str.startswith("A") | po["punto"].str.startswith("B")] if len(po) else po
    inf = leer_csv("10_influencia.csv")
    eq = leer_csv("10_equidad.csv")
    c120 = leer_csv("10_comparacion_120.csv")
    m120 = leer_csv("10_metodos_poblacion_120.csv")
    ttv = leer_csv("10_test_vs_train.csv")
    cal = leer_csv("10_calibracion.csv").rename(columns={"Unnamed: 0": "versión"})
    sens = leer_csv("10_sensibilidad_mejor_baseline_test.csv")
    # L
    taucs = leer_csv("10_L_auc_segmentos_test.csv")
    muchos = leer_csv("10_L_sin_par_bien_observadas.csv").rename(columns={"grupo": "grupo"})
    camr = leer_csv("10_L_camaras_en_rango.csv")
    l5 = leer_csv("10_L_sin_segmento_principal.csv")
    l5op = leer_csv("10_L_sin_segmento_operacion.csv")
    ltr = leer_csv("10_L_train_segmentos.csv")
    l7t = leer_csv("10_L_equidad_sin_segmento.csv")
    # M
    mpar = leer_csv("10_M_pares_con_hueco.csv")
    mrang = leer_csv("10_M_rangos_camara.csv")
    mpos = leer_csv("10_M_positivos_en_huecos.csv")
    m22 = leer_csv("10_M_tabla_2x2.csv")
    m_seg = leer_csv("10_M_tasa_segmento_camara.csv", dtype={"seg": str})
    gp = M.get("pos", {})
    sufijo120, sufijo100 = " (<= 120°)", " (<= 100°)"
    camcols = [c for c in m_seg.columns if c.startswith("tasa_c")] if len(m_seg) else []
    cam_rows = pd.DataFrame()
    if len(m_seg):
        cam_rows = m_seg[m_seg["seg"].isin(["257766998801", "911012534050"])][["seg", "grupo", "ubicacion", "momento"] + camcols + [c.replace("tasa_", "n_rango_") for c in camcols]]
    if len(cam_rows):
        cam_rows = cam_rows.rename(columns={c: (f"tasa cámara {c[-1]}" + sufijo120 if c.startswith("tasa_c") else f"cajas en rango cámara {c[-1]}" + sufijo120) for c in cam_rows.columns if c.startswith(("tasa_c", "n_rango_c"))})
    mpar_v = mpar.rename(columns={"tasa": "tasa" + sufijo120, "mediana_camara": "mediana de la cámara" + sufijo120, "umbral": "umbral" + sufijo120, "cajas_en_rango": "cajas en rango" + sufijo120}) if len(mpar) else mpar
    mrang_v = mrang.rename(columns={"az_p5": "azimut p5" + sufijo120, "az_p95": "azimut p95" + sufijo120, "mediana_tasa": "mediana de la tasa" + sufijo120}) if len(mrang) else mrang
    mpos_v = mpos.rename(columns={c: c + sufijo100 for c in mpos.columns if c != "grupo"}) if len(mpos) else mpos
    ubic_hueco = sorted({f"{p['ubicacion'].replace('location_', '')} ({p['momento']})" for p in M.get("pares", [])})
    todos_sf_dia = all(p.get("ubicacion") == "location_sf" and p.get("momento") == "Day" for p in M.get("pares", []))
    t = f"""## 9. Evaluación final en el test (notebook 10)

**Lo oficial es lo pre-declarado.** El notebook 10 aplicó el plan congelado v2 sin cambiar modelos, umbrales, criterios ni métricas, y se ejecutó sobre el test {EJECUCIONES_TEST} veces (la primera fue la evaluación pre-declarada; las siguientes corrigieron textos o agregaron los apéndices L, M y L.7, ver K.1 en la sección 11); los 15 CSV de resultados de la primera ejecución son idénticos por sha256 en todas (celda de verificación del notebook). Las secciones 9.1 a 9.7 son el resultado oficial. Los apéndices 9.8 (L) y 9.9 (M) son **diagnósticos post hoc, no pre-declarados**, y no cambian la recomendación formal.

### 9.1 Resultado principal (pre-declarado)

Modelo elegido en train ({MOD_N}) frente a la {BASE_N}, población principal ({miles(C10.get('A', {}).get('filas_p', 0))} filas, {C10.get('A', {}).get('segmentos', '?')} segmentos de test, {miles(C10.get('A', {}).get('pos_p', 0))} positivos):

{tabla(rp) if len(rp) else '(sin datos)'}

{B.get('texto', '')}

{figura('10_resultado_principal.png', 'Resultado principal en test')}

### 9.2 Todos los métodos (secundario) y sensibilidad al baseline de test

{tabla(mp) if len(mp) else '(sin datos)'}

Qué baseline habría sido el mejor en test (análisis aparte, no entra en el criterio principal):

{tabla(sens) if len(sens) else '(sin datos)'}

### 9.3 Puntos de operación con los umbrales congelados

{tabla(po[['metodo', 'punto', 'umbral', 'recall', 'precision', 'pct_revisar', '% revisado en train (OOF)']]) if len(po) else '(sin datos)'}

El punto A se consideraba sostenido en test si el recall puntual era >= {es(C10.get('D', {}).get('tol', ''))}. Métodos que lo sostienen: {sum(C10.get('D', {}).get('sostenido', {}).values())} de {len(C10.get('D', {}).get('sostenido', {}))}.

{figura('10_puntos_de_operacion.png', 'Puntos A y B en test')}

### 9.4 Calibración (descriptiva, calibrador congelado)

{tabla(cal) if len(cal) else '(sin datos)'}

{figura('10_calibracion.png', 'Confiabilidad en test')}

### 9.5 Análisis de influencia

Se repitió la comparación principal quitando segmentos (cada uno de los dos más grandes, ambos, y dejando uno afuera a la vez):

{tabla(inf) if len(inf) else '(sin datos)'}

Rango de ΔAUC: {n3(C10.get('F', {}).get('rng_auc', [float('nan')] * 2)[0], True)} a {n3(C10.get('F', {}).get('rng_auc', [float('nan')] * 2)[1], True)}; rango de Δ Fracción para 80 %: {n1(C10.get('F', {}).get('rng_f80', [float('nan')] * 2)[0], True)} a {n1(C10.get('F', {}).get('rng_f80', [float('nan')] * 2)[1], True)} puntos. Variantes que cambian el veredicto: {', '.join(C10.get('F', {}).get('cambian', [])) or 'ninguna'}.

{figura('10_influencia.png', 'Influencia por segmento')}

### 9.6 Equidad descriptiva (sin pruebas de hipótesis)

{tabla(eq.round(3)) if len(eq) else '(sin datos)'}

{prosa_segmentos()}; las brechas de esos grupos son las de un solo segmento. {frase_l7()}

### 9.7 Sensibilidad a 120° y test frente a train

Con los modelos congelados entrenados en la población de 120°:

{tabla(m120) if len(m120) else '(sin datos)'}

{tabla(c120) if len(c120) else ''}

Robusto (criterio del plan, lectura literal): {', '.join(k for k, v in C10.get('H', {}).get('robusto_literal', {}).items() if v) or 'ningún modelo'}.

Test frente a train (referencia fuera de fold de train):

{tabla(ttv.round(3)) if len(ttv) else '(sin datos)'}

{figura('10_test_vs_train.png', 'AUC de train (OOF) frente a test')}

### 9.8 Apéndice L (post hoc, no pre-declarado): el segmento {L.get('foco', '?')}

*Diagnóstico post hoc, no pre-declarado. No cambia el plan ni los resultados de 9.1 a 9.7.*

En la sección 9.5 ningún segmento cambia el veredicto, pero un segmento concentra el problema: aporta el {pc(L['grupos']['foco']['sin_camara'] / (L['grupos']['foco']['sin_camara'] + L['grupos']['otros 7 de test']['sin_camara']))} de los positivos del test y en él todos los métodos ordenan peor que el azar. AUC por segmento de test (segmentos con al menos 50 positivos):

{tabla(taucs.round(3)) if len(taucs) else '(sin datos)'}

Cajas sin par bien observadas (con 100 puntos LiDAR o más):

{tabla(muchos.round(3)) if len(muchos) else '(sin datos)'}

Dentro del rango de azimut de cada cámara (rangos empíricos):

{tabla(camr.T.reset_index().rename(columns={'index': 'indicador'}).round(3)) if len(camr) else '(sin datos)'}

{figura('10_L_tasas.png', 'Tasa de sin_camara por azimut, puntos y distancia: segmento foco, otros 7 y train')}

{figura('10_L_azimut_con_signo.png', 'Tasa de sin_camara por azimut con signo')}

Sin el segmento (7 segmentos), junto al resultado oficial (no reemplaza el pre-declarado):

{tabla(l5) if len(l5) else '(sin datos)'}

{tabla(l5op) if len(l5op) else ''}

{figura('10_L_sin_segmento.png', 'Punto A con y sin el segmento')}

L.7 (post hoc): recall al punto A por momento del día y ubicación, oficial y sin el segmento (`10_L_equidad_sin_segmento.csv`). {frase_l7()}

{tabla(l7t) if len(l7t) else '(sin datos)'}

Conclusión del apéndice L (generada por el notebook, rotulada como hipótesis):

{cita(L.get('conclusion', '(sin texto)'), '10')}

### 9.9 Apéndice M (post hoc, no pre-declarado): auditoría por cámara en los 41 segmentos

*Diagnóstico post hoc, no pre-declarado. Los criterios se fijaron antes de calcular el apéndice, pero después de ver el apéndice L, así que no es una confirmación independiente.*

Criterios: rango de azimut de cada cámara = percentil 5 a 95 del azimut de las cajas con par de esa cámara, calculado solo con los 33 segmentos de train; tasa de una cámara en un segmento = fracción de las cajas dentro de su rango con par de esa cámara; "con hueco" si la tasa es menor que el 25 % de la mediana de la cámara entre los 41 segmentos y hay al menos 100 cajas en el rango.

Poblaciones: los rangos y las tasas por cámara usan peatones y ciclistas con |azimut| <= 120° (las cámaras laterales llegan más allá de 100°); los positivos y el AUC usan la población principal, |azimut| <= 100°. Cada encabezado lo indica.

{tabla(mrang_v) if len(mrang_v) else '(sin datos)'}

Pares (segmento, cámara) con hueco:

{tabla(mpar_v.round(3)) if len(mpar_v) else '(sin datos)'}

Tasa por cámara en los dos segmentos con hueco (el mapa de calor completo está en la figura):

{tabla(cam_rows.round(3)) if len(cam_rows) else '(sin datos)'}

{figura('10_M_mapa_calor.png', 'Tasa por segmento y cámara (X = con hueco)')}

{frase_hueco_100()}

Positivos de la población principal que caen en celdas con hueco:

{tabla(mpos_v.T.reset_index().rename(columns={'index': 'indicador'}).round(3)) if len(mpos_v) else '(sin datos)'}

Tabla 2x2 (hueco frente a AUC de la regla top menor que 0,55, con el AUC calculado en la población <= 100°, segmentos con al menos 50 positivos, n = {M.get('n_base', '?')}). **Se presenta como descriptiva y circular en esta muestra:** los criterios del apéndice M se escribieron después de ver el apéndice L, y los dos segmentos con AUC bajo ya estaban identificados. Que los dos segmentos con hueco coincidan con los dos de AUC bajo no es evidencia a favor de la hipótesis. El test exacto de Fisher (p = {es(round(M.get('fisher_p', float('nan')), 4))}) se informa solo por completitud y no se usa como evidencia:

{tabla(m22) if len(m22) else '(sin datos)'}

{figura('10_M_auc_hueco.png', 'Segmentos con y sin hueco: AUC de la regla y % de positivos con 100 puntos o más')}

Conclusión del apéndice M (generada por el notebook, rotulada como hipótesis; el valor p que menciona es el descriptivo de arriba):

{cita(M.get('conclusion', '(sin texto)'), '10')}

**Cómo leer este apéndice.**

- El hueco de una cámara puede ser de etiquetado o de los datos de esa cámara (por ejemplo, una cámara sin imágenes o sin etiquetas 2D en el segmento). Con los archivos disponibles no se distingue.
- {'Los ' + str(len(M.get('pares', []))) + ' casos son de San Francisco de día' if todos_sf_dia else 'Los casos son de: ' + ', '.join(ubic_hueco)}. Con {len(M.get('pares', []))} casos en {M.get('n_seg', '?')} segmentos no hay base para estimar su frecuencia en datos nuevos.
- Los rangos de azimut por cámara son empíricos (percentil 5 a 95 en train) y los criterios se escribieron después de ver el apéndice L.
"""
    return t


# --------------------------------------------------------------------------------------------- 10. Recomendaciones
def sec10():
    rec = C10.get("J", {})
    segj = rec.get("matices", "")
    po9 = leer_csv("09_puntos_operacion.csv")
    fila9 = po9[(po9["metodo"] == BASE_N) & po9["punto"].str.startswith("A")] if len(po9) else po9
    tr_rec = ci_str(fila9["recall"].iloc[0]) if len(fila9) else "(sin dato)"
    tr_pct = ci_str(fila9["pct_revisar"].iloc[0], True) if len(fila9) else "(sin dato)"
    eq10 = leer_csv("10_equidad.csv")
    fc = eq10[(eq10["metodo"] == MOD_N) & (eq10["grupo"] == "CYCLIST")] if len(eq10) else eq10
    n_cic = miles(fc["filas"].iloc[0]) if len(fc) else "(sin dato)"
    cam_h = next((p_.get("camara", "?") for p_ in M.get("pares", []) if p_.get("grupo") == "test"), "?")
    t = f"""## 10. Interpretación y recomendaciones

*Esta sección es interpretación de las cifras de las secciones anteriores. Lo único oficial del test es lo pre-declarado (9.1 a 9.7).*

**Uso en dos niveles.** La analogía es la de un control de calidad en una fábrica: primero se revisa la máquina (si una de las cámaras dejó de producir pares en un segmento), y después se revisan las piezas dudosas (qué cajas auditar primero).

1. **Auditoría por segmento y cámara.** Calcular, para cada segmento nuevo, la tasa de pares de cada cámara dentro de su rango de azimut y marcar las cámaras con hueco. En los {M.get('n_seg', '?')} segmentos auditados encontramos {M.get('n_pares', '?')} pares con hueco, y las celdas con hueco reúnen el {pc(M['pos']['train']['% de los positivos'])} de los positivos de train y el {pc(M['pos']['test']['% de los positivos'])} de los de test. Esa auditoría detecta lo que la regla por puntos no detecta: los huecos afectan a objetos bien observados. {frase_hueco_100()} Es una hipótesis post hoc; hay que validarla con `camera_calibration` y con más segmentos.
2. **Priorización de cajas con la regla por puntos top** (humano en el circuito). En los segmentos sin hueco, ordenar las cajas por puntos LiDAR de la parte alta (menos puntos primero) y revisar hasta el corte elegido. Es una regla de una línea, se explica sola y en train no fue peor que ningún modelo.

**Qué fracción de revisión y qué recall esperar.** Con el corte A (fijado con train para un recall de 0,80): en train (fuera de fold) la {BASE_N} dio recall {tr_rec} revisando {tr_pct} de las cajas; en test dio recall {ic3(OPA_B.get('recall'))} revisando {pc(OPA_B.get('pct_revisar', [float('nan')])[0])} de las cajas (IC {pc(OPA_B.get('pct_revisar', [float('nan')] * 3)[1])} a {pc(OPA_B.get('pct_revisar', [float('nan')] * 3)[2])}). Con el corte B (20 % de revisión): recall {ic3(OPB_B.get('recall'))} en test. {segj}

**Riesgos de equidad medidos.** {frase_l7()} Night y Dawn/Dusk tienen un solo segmento de test cada uno.

**Monitoreo.** Vigilar la deriva de la tasa de `sin_camara` y el recall por segmento (no solo el promedio), la tasa de pares por cámara dentro de su rango, y reponer el corte si el recall por segmento baja de {es(C10.get('D', {}).get('tol', ''))}.

**Datos que mejorarían el resultado.** `camera_calibration` (validar el borde de {C9.get('AZ_MAX', '?')}° y los rangos por cámara), más segmentos de test, más ciclistas (hoy {n_cic} filas de ciclistas en la población principal del test), y etiquetas por cámara para separar cobertura de etiquetado de visibilidad física.

**Trabajo futuro.** Repetir la evaluación con más segmentos; validar la auditoría por cámara con los datos de calibración; estimar la precisión real con una muestra revisada manualmente; probar si un modelo por segmento y cámara mejora donde la regla no funciona.

**Qué NO se puede afirmar.**

- Que `sin_camara` sea invisibilidad física: es falta de etiqueta 2D de cámara.
- Que el resultado generalice más allá de 8 segmentos de test.
- Nada sólido sobre ciclistas, ni sobre Night y Dawn/Dusk (un segmento de test cada uno).
- Que el hueco de cámara encontrado en el test ({cam_h}) sea de etiquetado y no de los datos de esa cámara.
- Que un modelo supere a la regla por puntos: con el criterio fijado antes, no ocurrió.
"""
    return t


# --------------------------------------------------------------------------------------------- 11. Etica
def sec11e():
    n05 = celdas_md("05_etica_sesgos_privacidad")
    lic = registrar("05", bloque(next((c for c in n05 if "licencia de Waymo prohíbe redistribuir" in c), ""), "**¿Por qué la licencia de Waymo prohíbe redistribuir los datos?**", "\n\n**")) if n05 else ""
    eq9 = leer_csv("09_equidad.csv")
    g9 = lambda var, grupo, col: float(eq9[(eq9["variable"].str.rstrip("_") == var) & (eq9["grupo"] == grupo)][col].iloc[0]) if len(eq9) else float("nan")
    e10 = leer_csv("10_equidad.csv")
    g10 = lambda var, grupo, col: float(e10[(e10["metodo"] == BASE_N) & (e10["variable"] == var) & (e10["grupo"] == grupo)][col].iloc[0]) if len(e10) else float("nan")
    brech = leer_json(REP / "09_equidad_brechas.json").get("brechas", [])
    t = f"""## 11. Ética, sesgos y privacidad

*Resumen de lo que desarrolla el notebook 05 (EP1), actualizado con lo medido en EP2.*

**Privacidad.** Usamos solo `lidar_box` y `camera_to_lidar_box_association`: coordenadas 3D y metadatos de cajas etiquetadas y una tabla de pares cámara-LiDAR; no usamos imágenes. Según el README de EP1 y el notebook 05, esas tablas no contienen información directamente identificable de personas, y el 05 establece que no hay identificadores directos (nombres, patentes sin difuminar ni biometría) en las columnas del proyecto; el riesgo que señala es la reidentificación indirecta: `key.laser_object_id` más la marca de tiempo identifican cada detección y, encadenadas, la trayectoria de un objeto. Por minimización, esos identificadores no son variables de ningún modelo (sección 3). El 05 dice que la licencia del Waymo Open Dataset es no comercial y prohíbe redistribuir los datos, y que por eso `data/01_raw/waymo/` está en `.gitignore`; el repositorio guarda solo código, documentos y figuras, y los datos derivados se regeneran con los notebooks (sección 13). Lo que dice el 05 sobre el porqué de la licencia:

{cita(lic, '05') if lic else '(sin texto)'}

**Sesgos medidos.** (1) *Ubicación:* en train el recall al punto A de la regresión logística es {n3(g9('location', 'location_sf', 'recall_A'))} en San Francisco, {n3(g9('location', 'location_phx', 'recall_A'))} en Phoenix y {n3(g9('location', 'location_other', 'recall_A'))} en el resto (`09_equidad.csv`); en el test oficial, con la regla top, {n3(g10('location', 'location_sf', 'recall A'))} en San Francisco y {n3(g10('location', 'location_other', 'recall A'))} en `location_other`. (2) *Momento del día:* en train, {n3(g9('time_of_day', 'Dawn/Dusk', 'recall_A'))} en Dawn/Dusk frente a {n3(g9('time_of_day', 'Day', 'recall_A'))} de día; {('la brecha de AUC Dawn/Dusk menos Day es ' + n3(brech[0]['auc_dif'], True) + ' (IC ' + n3(brech[0]['auc_lo'], True) + ' a ' + n3(brech[0]['auc_hi'], True) + ', incluye 0)') if brech else ''}. En el test, Night y Dawn/Dusk tienen un solo segmento cada uno, así que no se puede separar el efecto del momento del día del efecto del segmento. (3) *Ciclistas:* en train son {miles(g9('object_type', 'CYCLIST', 'filas'))} filas y {miles(g9('object_type', 'CYCLIST', 'sin_camara'))} positivos, con recall al punto A de {n3(g9('object_type', 'CYCLIST', 'recall_A'))}; en el test hay muy pocos positivos y no hay conclusión por clase. (4) *Post hoc, no pre-declarado:* sin el segmento `{L.get('foco', '?')}`, las brechas por momento del día y ubicación del test cambian mucho (sección 9, L.7), lo que muestra que estaban confundidas con un segmento.

**Riesgo de uso.** Esto no es una alerta de seguridad ni mide qué ve una cámara: `sin_camara` es la ausencia de una etiqueta 2D de cámara, es decir, cobertura de etiquetado. Se usa para ordenar una revisión con una persona en el circuito, nunca para reemplazarla ni para decidir nada dentro de un vehículo. Un puntaje bajo no prueba que la caja tenga par: en el segmento anómalo, la regla ordena como "con par" cajas bien observadas que no lo tienen (sección 9, apéndices L y M).
"""
    return t


# --------------------------------------------------------------------------------------------- 12. Limitaciones
def sec11():
    nb10 = celdas_md("10_evaluacion_final_sin_camara")
    k1 = next((c for c in nb10 if c.startswith("# K. Limitaciones")), "")
    k1 = bloque(k1, "## K.1", "## K.2")
    k2 = next((c for c in nb10 if c.startswith("# K. Limitaciones")), "")
    k2 = bloque(k2, "## K.2")
    lim_ic = C10.get("K2", {}).get("texto", "(sin dato: falta K2 en 10_resumen_cifras.json)")
    lecturas = next((c for c in nb10 if "## Lecturas tomadas" in c), "")
    lecturas = bloque(lecturas, "## Lecturas tomadas")
    lm = next((c for c in nb10 if c.startswith("# M. Apéndice")), "")
    lm = bloque(lm, "**Criterios fijados antes de calcular nada**")
    ncorr = LOG.count("EJECUCION REAL")
    fechas_ver = verificaciones_en_copia()
    tf = tasas_por_fold()[2]
    _fb, _fbp, _ = tasas_por_fold()
    tr_seg = _fbp.groupby("segment_id")["sin_camara"].mean()
    _c = leer_csv("07_conteos_test.csv")
    te_seg = _c["sin_camara_principal"] / _c["filas_B_principal"]
    t = f"""## 12. Limitaciones y desviaciones del plan

**Desviaciones declaradas en el notebook 10 (sección K.1, copiadas del notebook).**

{sin_titulo(k1)}

**Limitaciones del notebook 10 (sección K.2, copiadas del notebook).**

{sin_titulo(k2)}

**Límite del intervalo de la Fracción para 80 % (generado por el notebook 10).** {lim_ic}

**Lecturas tomadas sin consulta (notebook 10).** Son decisiones de interpretación que se escribieron en el notebook:

{sin_titulo(lecturas)}

**Criterios y lecturas del apéndice M (post hoc).**

{lm}

**Lo que no se verificó.**

- La calibración de cámaras (`camera_calibration`) no está en los datos locales: el borde de {C9.get('AZ_MAX', '?')}° y los rangos de azimut por cámara son empíricos.
- No se distinguió si el hueco de una cámara es de etiquetado o de los datos de esa cámara.
- Las horas de revisión usan un supuesto de {segundos_por_revision()} s por caja, fijado en el notebook 07, que no es un dato medido.
- El etiquetado varía mucho entre segmentos: la tasa de `sin_camara` de la población principal va de {pc(tr_seg.min())} a {pc(tr_seg.max())} por segmento en train y de {pc(te_seg.min())} a {pc(te_seg.max())} en test, y no se estudió por qué.
- Los folds del split no se estratificaron por el target nuevo (`sin_camara`) sino por `tiene_camara`, el target de EP1: la tasa de `sin_camara` por fold va de {pc(tf['tasa de sin_camara'].min())} a {pc(tf['tasa de sin_camara'].max())} (sección 3).
- El notebook 10 se ejecutó {EJECUCIONES_TEST} veces sobre el test (constante `EJECUCIONES_TEST` en `scripts/constantes_ep2.py`; el log registra {ncorr} ejecuciones reales, `docs/log_trabajo_ep2.md`).
- Además de esas {EJECUCIONES_TEST} ejecuciones en el repositorio, hubo 2 ejecuciones de verificación del notebook 10 en copias fuera del repositorio ({fechas_ver[0]} y {fechas_ver[1]}, fechas del log), con los 15 CSV idénticos por sha256 a los de la ejecución 1; no se cuentan entre las del repositorio y no cambian el conteo oficial.

**Archivos o cifras que no se encontraron al generar este informe:** {', '.join(sorted(set(FALTAN))) if FALTAN else 'ninguno'}.
"""
    return t


# --------------------------------------------------------------------------------------------- 12. Reproducibilidad
def sec12():
    nbs = sorted(NBS.glob("*.ipynb"))
    filas = []
    for p in nbs:
        celdas = celdas_md(p.stem)
        tit = next((l.lstrip("# ").strip() for c in celdas for l in c.splitlines() if l.startswith("# ")), "")
        filas.append({"notebook": f"`notebooks/{p.name}`", "título": tit[:110]})
    outs = {}
    for pref in ("06", "07", "08", "09", "10"):
        outs[pref] = (len(list(REP.glob(f"{pref}_*.csv"))), len(list(IMG.glob(f"{pref}_*.png"))))
    tout = pd.DataFrame([{"notebook": k, "CSV en data/08_reporting": v[0], "figuras en images/": v[1]} for k, v in outs.items()])
    ign = [l for l in GITIGNORE.splitlines() if l.startswith("data/")]
    import importlib.metadata as _im

    def _v(p):
        try:
            return _im.version(p)
        except Exception:
            return "?"

    t = f"""## 13. Reproducibilidad

**Entorno.** `docs/entorno_ep2.txt` (generado por el notebook 09):

```
{ENTORNO.strip()}
```

**Versiones instaladas al generar este informe** (de `importlib.metadata`): kedro {_v('kedro')}, pytest {_v('pytest')}, pytest-cov {_v('pytest-cov')}, nbformat {_v('nbformat')}.

**Orden de ejecución de los notebooks.** Se ejecutan en el orden numérico (00 a 10, y 09b entre el 09 y el 10); el 00 solo en Google Colab. Los notebooks 07 a 10 leen archivos que producen los anteriores:

{tabla(pd.DataFrame(filas))}

**Cómo se ejecuta un notebook.** Con un kernel propio del entorno, para que Jupyter no use otro Python de la máquina (en el repositorio original se usó el kernel `kedro_waymo_evaluacion` de `kedro jupyter`):

```
.venv/Scripts/python.exe -m ipykernel install --prefix .venv --name ep2
.venv/Scripts/python.exe -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=ep2 notebooks/09_modelos_supervisados_sin_camara.ipynb
```

**Orden y advertencia sobre el plan congelado.** El 08 escribe `features_B.parquet`, el 09 reentrena los modelos y el 09b reescribe el plan v2; el 10 verifica los sha256 del plan. Para reproducir el resultado oficial, ejecutar el 10 con los modelos y el plan incluidos en `data/06_models/` sin reejecutar antes el 09 ni el 09b (`scripts/verificar_congelados.py` lo comprueba; el resultado de la prueba en copia limpia está en el log de trabajo).

**Pruebas.** Desde la raíz del repositorio (usa la configuración de cobertura de `pyproject.toml`):

```
.venv/Scripts/python.exe -m pytest
```

Última medición (`scripts/medir_pruebas.py`): {frase_pruebas()}.

**Ingesta con Kedro.** Los pipelines registrados son `ingesta_waymo` y `preprocesamiento` (comprobado con `kedro registry list`). La ingesta se ejecuta con:

```
kedro run --pipeline ingesta_waymo
```

Este comando no se reejecutó al generar este informe (reescribiría `data/02_intermediate/`); solo se verificó que el pipeline está registrado y que sus pruebas pasan.

**Cómo se regenera este informe.** Un solo comando, desde la raíz del repositorio; reescribe `docs/informe_tecnico_EP2.md` y el bloque "EP2 en breve" del README:

```
.venv/Scripts/python.exe -X utf8 scripts/generar_informe_tecnico.py
```

El script necesita los CSV y JSON de `data/08_reporting/`, los modelos y el plan de `data/06_models/` y los notebooks ejecutados, que no están en el repositorio (`data/` está en `.gitignore`). En un clon limpio solo se puede leer el informe ya generado (`docs/informe_tecnico_EP2.md`); para regenerarlo hay que ejecutar antes los notebooks en orden. Los archivos `08_no_supervisado_resumen.json` y `09_equidad_brechas.json` se extraen una sola vez de los notebooks ejecutados con `scripts/extraer_no_supervisado_08.py` y `scripts/extraer_equidad_09.py`, y los diagnósticos post hoc del 08 salen de `scripts/diagnostico_post_hoc_08.py`.

**Semillas.** Semilla {HIP.get('semilla', '?')} en todo el proyecto (folds, bootstrap, desempates de las curvas de captura, modelos).

**Dónde está cada cosa.** Datos de entrada del modelado en `data/05_model_input/`; modelos y el plan de evaluación congelado con sha256 en `data/06_models/`; predicciones en `data/07_model_output/`; tablas en `data/08_reporting/` y figuras en `images/`; documentos generados en `docs/`. Cantidad de tablas y figuras por notebook:

{tabla(tout)}

**Cómo regenerar cada tabla y figura.** Cada CSV y cada figura lleva como prefijo el número del notebook que la genera (`08_*.csv` e `images/08_*.png` salen del notebook 08, y así para el 07, 09 y 10); volver a ejecutar ese notebook las reescribe. El notebook 10 verifica con sha256 que los resultados de la ejecución 1 no cambian al reejecutarlo (`data/08_reporting/10_hashes_ejecucion1.json`).

**Archivos ignorados por git y cómo se obtienen.** El `.gitignore` excluye todo lo que hay bajo `data/` ({', '.join('`' + l + '`' for l in ign)}). Por eso los datos, los modelos (`.joblib`), el plan congelado y todas las tablas de `data/08_reporting/` no están en el repositorio: se regeneran ejecutando los notebooks en orden, a partir de los parquet de Waymo Open Dataset v2 que se descargan con el notebook 00 (`data/01_raw/waymo/`). El informe y las figuras (`docs/`, `images/`) sí están en el repositorio.
"""
    return t


# --------------------------------------------------------------------------------------------- 13. Anexos
def sec13():
    c7 = celdas_md("07_decision_target_ep2")
    urls = []
    for c in c7 + celdas_md("08_analisis_observabilidad_sin_camara"):
        urls += re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", c)
    vistos, refs = {"https://arxiv.org/abs/1912.04838"}, []
    enlaces_nhtsa = []
    for tit, u in urls:
        if u not in vistos:
            vistos.add(u)
            if "nhtsa" in u.lower():
                enlaces_nhtsa.append(u)
            else:
                refs.append(f"- {tit}: {u}")
    if enlaces_nhtsa:
        refs.append("- NHTSA, publicaciones 813727 y 813818 (2023), usadas en el 07 solo como contexto: " + "; ".join(enlaces_nhtsa))
    refs.insert(0, "- Sun, P., et al. (2020). Scalability in Perception for Autonomous Driving: Waymo Open Dataset. CVPR 2020. arXiv:1912.04838. https://arxiv.org/abs/1912.04838")
    ctx = next((c for c in c7 if "Contexto externo" in c), "")
    ctx = bloque(ctx, "Contexto externo", "**")
    ctx = ctx.split("\n")[0]
    plan_ts = PLAN.get("congelado", "?")
    mtime = lambda p: datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d") if p.exists() else "?"
    dec = pd.DataFrame([
        {"decisión": "Target EP2 = `sin_camara` (candidata B)", "evidencia": f"criterios de `decision_target_ep2.csv`; AUC de B {es(DEC.loc[(DEC['target'] == 'B') & DEC['criterio'].str.startswith('AUC (todas'), 'valor'].iloc[0]) if len(DEC) else '?'} (versión previa, 120°)", "fecha de la evidencia (modificación del archivo)": mtime(REP / "decision_target_ep2.csv")},
        {"decisión": f"Población principal |azimut| <= {C9.get('AZ_MAX', '?')}°", "evidencia": "tasa por tramo de azimut y cruce de clusters con la franja (08)", "fecha de la evidencia (modificación del archivo)": mtime(REP / "08_tasa_por_azimut.csv")},
        {"decisión": f"Modelo a comparar: {HIP.get('recomendado_modelo', '?')}", "evidencia": "prueba de elección del 09 (ΔAUC >= 0,01 con ambos IC excluyendo 0)", "fecha de la evidencia (modificación del archivo)": mtime(MOD / "hiperparametros_B.json")},
        {"decisión": f"Baseline principal: {HIP.get('mejor_baseline_simple', '?')}", "evidencia": f"AUC {n3(P9.get(HIP.get('mejor_baseline_simple', ''), {}).get('AUC', float('nan')))} en train (OOF)", "fecha de la evidencia (modificación del archivo)": mtime(MOD / "hiperparametros_B.json")},
        {"decisión": "Recomendación del 09", "evidencia": f"{C9.get('recomendacion', '?')}; robustos: {C9.get('robustos', [])}", "fecha de la evidencia (modificación del archivo)": mtime(REP / "09_resumen_cifras.json")},
        {"decisión": "Congelar el plan de evaluación v2 antes de abrir el test", "evidencia": f"`plan_evaluacion_test.json`, congelado {plan_ts}", "fecha de la evidencia (modificación del archivo)": mtime(MOD / "plan_evaluacion_test.json")},
        {"decisión": "Recomendación formal tras el test", "evidencia": f"{C10.get('J', {}).get('rec', '?')}; 'vale la pena' del modelo: {'sí' if B.get('vlp') else 'no'}", "fecha de la evidencia (modificación del archivo)": mtime(REP / "10_resumen_cifras.json")},
        {"decisión": "Auditoría por cámara como primer nivel de uso (hipótesis)", "evidencia": f"{M.get('n_pares', '?')} pares con hueco en {M.get('n_seg', '?')} segmentos (descriptivo, circular)", "fecha de la evidencia (modificación del archivo)": mtime(REP / "10_M_pares_con_hueco.csv")},
    ])
    figs = sorted(p.name for p in IMG.glob("*.png") if re.match(r"(07|08|09|10)_", p.name))
    tabs = sorted(p.name for p in REP.glob("*.csv") if re.match(r"(07|08|09|10)_", p.name) or p.name.startswith("decision"))
    t = f"""## 14. Anexos

### 14.1 Tabla de decisiones

La fecha es la de la última modificación del archivo que contiene la evidencia (no la fecha de la decisión).

{tabla(dec)}

### 14.2 Glosario breve

- **AUC (ROC):** probabilidad de que una caja sin par reciba un puntaje mayor que una caja con par, elegidas al azar. 0,5 es azar y 1 es ordenar perfecto.
- **PR-AUC:** área bajo la curva precisión-recall; depende de la tasa de positivos, por eso se compara con la prevalencia.
- **Captura@k:** fracción de las cajas sin par que quedan dentro del k % mejor puntuado (por ejemplo, Captura@20 %).
- **Fracción para 80 %:** fracción de cajas que hay que revisar, siguiendo el orden del puntaje, para encontrar el 80 % de las cajas sin par. Menos es mejor.
- **Bootstrap por segmentos:** se remuestrean segmentos completos (y no filas) para obtener intervalos de confianza, porque las filas de un mismo segmento se parecen entre sí.
- **ECE:** error de calibración esperado; promedio de la diferencia entre la probabilidad predicha y la frecuencia observada, en 10 grupos por cuantiles.
- **Punto A / punto B:** cortes de operación; A busca un recall de 0,80 con el corte fijado en train y B revisa el 20 % mejor puntuado.

### 14.3 Lista de figuras

{chr(10).join('- `images/' + f + '`' for f in figs)}

### 14.4 Lista de tablas (CSV generados por los notebooks)

{chr(10).join('- `data/08_reporting/' + f + '`' for f in tabs)}

### 14.5 Referencias

Fuentes citadas en los notebooks 07 y 08 y en este informe:

{chr(10).join(refs) if refs else '(sin referencias en el 07)'}

El 07 usa datos de la NHTSA sobre peatones fallecidos en EE. UU. en 2023 (publicaciones 813727 y 813818) solo como contexto. No repetimos las cifras en este informe: el 07 no da el nombre del documento y ninguna cifra tiene archivo de salida en el proyecto.

El artículo de Sun et al. (2020) se usa para el campo de visión horizontal de las cámaras (Tabla 3: ±25,2° para las cinco cámaras; secciones 3 y 6). El artículo no entrega el yaw de montaje de cada cámara y no lo verificamos; por eso este informe usa rangos de azimut empíricos y no afirma qué rango cubre cada cámara.
"""
    return t


# --------------------------------------------------------------------------------------------- auditoria de cifras
NUM = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*(?![\w])")


def _limpio(texto):
    t = re.sub(r"```.*?```", "", texto, flags=re.S)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"`[^`]*`", "", t)
    t = re.sub(r"(?i)\b(?:secci[oó]n(?:es)?|figura|fig\.)\s+[\d.]+(?:\s+(?:a|y|al)\s+[\d.]+)?", "", t)
    t = re.sub(r"arXiv:\d+\.\d+|CVPR \d{4}|\(\d{4}\)|\b(?:19|20)\d{2}\b", "", t)
    lineas = []
    for l in t.splitlines():
        if l.startswith("#") or re.match(r"^\s*\|[-| ]+\|\s*$", l) or re.search(r"\| [0-9a-f]{16} \|", l) or "|---|" in l:
            continue
        lineas.append(re.sub(r"^\s*(?:>\s*)?(?:\d+\.|-|\*)\s+", "", l))
    return "\n".join(lineas)


def _tokens(texto):
    return NUM.findall(_limpio(texto))


def _valor(tok):
    """(valor, decimales) de un token en formato es (coma decimal, punto de miles)."""
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", tok):
        return float(tok.replace(".", "")), 0
    t = tok.replace(",", ".")
    if t.count(".") > 1:
        return None, 0
    d = len(t.split(".")[1]) if "." in t else 0
    return float(t), d


def _valores_de_archivos():
    import numpy as np
    vals = []
    for p in list(REP.glob("*.csv")) + [R / "data" / "05_model_input" / "split_segmentos.csv"] + list((DOCS / "seleccion_segmentos").glob("*.csv")):
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        for c in df.columns:
            col = pd.to_numeric(df[c], errors="coerce").dropna()
            vals.append(col.values.astype(float))
            if len(col):
                vals.append(np.array([float(col.sum())]))                 # sumas de columna (totales derivados)
            for g in ("conjunto", "uso", "fold", "grupo"):
                if g in df.columns and len(col):
                    vals.append(pd.to_numeric(df.groupby(g)[c].sum(), errors="coerce").dropna().values.astype(float))
            if df[c].dtype == object:                      # celdas del tipo "0.698 (0.503 a 0.961)"
                for x in df[c].dropna().astype(str).head(100000):
                    nums = re.findall(r"-?\d+\.?\d*", x)
                    vals.append(np.array([float(n) for n in nums[:6]])) if nums else None
    def aplanar(o):
        if isinstance(o, dict):
            for v in o.values():
                yield from aplanar(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                yield from aplanar(v)
        elif isinstance(o, bool):
            return
        elif isinstance(o, (int, float)):
            yield float(o)
    for p in list(REP.glob("*.json")) + list(MOD.glob("*.json")) + [INP / "config_features_B.json"]:
        try:
            vals.append(np.array(list(aplanar(json.loads(p.read_text(encoding="utf-8")))), dtype=float))
        except Exception:
            continue
    v = np.concatenate([x for x in vals if len(x)])
    return v[np.isfinite(v)]


def auditar(texto_informe):
    """Cuenta las cifras por origen y busca las que no aparecen en ningun CSV/JSON de salida."""
    import numpy as np
    V = _valores_de_archivos()
    conj = {}
    for d in range(0, 5):
        conj[d] = set(np.round(V, d).tolist()) | set(np.round(np.abs(V), d).tolist()) | set(np.round(V * 100, d).tolist()) | set(np.round(np.abs(V) * 100, d).tolist())
    def en_archivos(tok):
        v, d = _valor(tok)
        if v is None:
            return True
        return round(v, d) in conj[min(d, 4)] or round(abs(v), d) in conj[min(d, 4)]
    por_fuente = {}
    for fuente, txt in TEXTOS:
        por_fuente.setdefault(fuente, []).extend(_tokens(txt))
    total = _tokens(texto_informe)
    n_nb = {f: len(t) for f, t in por_fuente.items()}
    triviales = lambda tok: (_valor(tok)[0] is not None and _valor(tok)[1] == 0 and _valor(tok)[0] <= 12)
    sin_ubicar = {}
    for f, toks in por_fuente.items():
        malos = sorted({t for t in toks if not triviales(t) and not en_archivos(t)})
        sin_ubicar[f] = malos
    resto = [t for t in total]
    rep_ = {
        "cifras_totales_en_el_informe": len(total),
        "cifras_en_textos_citados_de_notebooks_07_08_09": sum(v for k, v in n_nb.items() if k in ("07", "08", "09")),
        "cifras_en_textos_generados_por_el_notebook_10_citados": n_nb.get("10", 0),
        "cifras_restantes_calculadas_por_el_script_desde_archivos_o_texto_fijo": len(total) - sum(n_nb.values()),
        "detalle_por_fuente": n_nb,
        "cifras_citadas_que_no_se_ubicaron_en_ningun_csv_json": sin_ubicar,
        "criterio": "cifra = token numerico fuera de bloques de codigo, encabezados, enlaces, codigo en linea y numeracion de listas; se considera ubicada si su valor (con sus decimales, o multiplicado por 100) aparece en algun CSV o JSON de salida; se ignoran los enteros <= 12",
    }
    # cifras del texto del script que no estan en ningun archivo (fuera de los textos citados)
    citado = "\n".join(t for _, t in TEXTOS)
    propias = [t for t in total if not triviales(t) and not en_archivos(t)]
    cuenta_cit = {}
    for t in _tokens(citado):
        cuenta_cit[t] = cuenta_cit.get(t, 0) + 1
    exceso = []
    for t in propias:
        if cuenta_cit.get(t, 0) > 0:
            cuenta_cit[t] -= 1
        else:
            exceso.append(t)
    rep_["cifras_propias_del_script_que_no_se_ubicaron_en_ningun_csv_json"] = sorted(set(exceso))
    return rep_

# --------------------------------------------------------------------------------------------- ensamblado
RUBRICA = """### Mapa de la rúbrica

| Indicador | Qué se evalúa | Dónde está |
|---|---|---|
| IE5 | Metodología | Secciones 2 a 6: objetivos y KPIs (2), datos, preparación y calidad (3), CRISP-DM (4), elección del target (5) y análisis de datos (6) |
| IE6 | Aprendizaje supervisado | Secciones 8 y 9 |
| IE7 | Aprendizaje no supervisado | Sección 7 |
| IE8 | Interpretación y recomendaciones | Secciones 10, 11 (ética, sesgos y privacidad) y 12 (limitaciones) |
"""


def main():
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    cab = f"""# Informe técnico EP2: auditoría de cajas 3D etiquetadas sin par 2D de cámara (Waymo Open Dataset v2)

*Generado automáticamente por `scripts/generar_informe_tecnico.py` el {ahora}. Cada cifra sale de los archivos de salida del proyecto; los resultados post hoc llevan siempre la etiqueta "post hoc, no pre-declarado" y el resultado oficial del test es el pre-declarado.*

**Contenido:** 1 Resumen ejecutivo · 2 Problema, contexto, objetivos y KPIs · 3 Datos, preparación y calidad · 4 Metodología (CRISP-DM) · 5 Elección del target · 6 Análisis de datos · 7 Aprendizaje no supervisado · 8 Modelos supervisados · 9 Evaluación final en test · 10 Interpretación y recomendaciones · 11 Ética, sesgos y privacidad · 12 Limitaciones y desviaciones · 13 Reproducibilidad · 14 Anexos
"""
    cuerpo = [sec1(), RUBRICA, sec2(), sec3(), sec4(), sec5(), sec6(), sec7(), sec8(), sec9(), sec10(), sec11e(), sec11(), sec12(), sec13()]
    texto = cab + "\n" + "\n\n".join(c.strip() for c in cuerpo) + "\n"
    s_ = segundos_por_revision()
    for a, b in ((f"el supuesto de {s_} s por revisión viene del 09; no es un dato medido", f"el supuesto de {s_} s por revisión viene del 09, que lo copia del 07, donde se fijó; no es un dato medido"),
                 (f"ilustración con {s_} s por revisión (supuesto del 09), calculada como en el 09", f"ilustración con {s_} s por revisión (supuesto fijado en el 07 y repetido en el 09), calculada como en el 09")):
        texto = texto.replace(a, b)             # el texto del 10 dice que el supuesto viene del 09; el 09 lo copia del 07
    texto = texto.replace("| candidata | motivo | evidencia |", "| Candidata | Motivo | Evidencia |")      # tabla copiada del 07
    texto = acentuar(texto)                      # nombres de pantalla con tilde (Regresión logística, Regla geométrica, Isotónica)
    (DOCS / "informe_tecnico_EP2.md").write_text(texto, encoding="utf-8")
    aud = auditar(texto)
    (REP / "informe_auditoria_cifras.json").write_text(json.dumps(aud, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Auditoria de cifras: {aud['cifras_totales_en_el_informe']} cifras; {aud['cifras_en_textos_citados_de_notebooks_07_08_09']} en textos citados de los notebooks 07/08/09; "
          f"{aud['cifras_en_textos_generados_por_el_notebook_10_citados']} en textos generados por el notebook 10; "
          f"sin ubicar en archivos: {sum(len(v) for v in aud['cifras_citadas_que_no_se_ubicaron_en_ningun_csv_json'].values())} citadas y {len(aud['cifras_propias_del_script_que_no_se_ubicaron_en_ningun_csv_json'])} propias (detalle en data/08_reporting/informe_auditoria_cifras.json)")
    print(f"Informe escrito: docs/informe_tecnico_EP2.md ({len(texto):,} caracteres). Cifras o archivos faltantes: {len(set(FALTAN))}")
    for f in sorted(set(FALTAN)):
        print("  falta:", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
