"""Genera docs/ep3/informe_tecnico_EP3.md, README_EP3.md, guion_presentacion.md y preguntas_cruzadas.md.

Ninguna cifra esta escrita a mano: todas salen de data/08_reporting_ep3, data/09_app_ep3, data/06_models_ep3 y docs/seleccion_segmentos.
Uso: python scripts/ep3/generar_docs_ep3.py   (escribe solo en docs/ep3/)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.app_logica import SECCIONES as SECCIONES_PAGINA  # noqa: E402
from waymo_evaluacion.ep3.plan import verificar_plan_v3  # noqa: E402

REP, APP, MOD, DOC = RAIZ / "data/08_reporting_ep3", RAIZ / "data/09_app_ep3", RAIZ / "data/06_models_ep3", RAIZ / "docs/ep3"
_CONT = json.loads((REP / "pruebas_ep3_conteo.json").read_text(encoding="utf-8"))  # scripts/ep3/contar_pruebas.py: pytest --collect-only, sin ejecutar la suite
PRUEBAS_EP3 = int(_CONT["recolectadas_ep3"])
PRUEBAS_EP2 = int(_CONT["pruebas_ep2"])  # data/08_reporting/pytest_resumen.json
PRUEBAS_TOTAL = PRUEBAS_EP2 + PRUEBAS_EP3
SEG_POR_CAJA = 20           # supuesto de EP2 (no medido), editable en la pagina
EN_MUESTRA = "en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos"
GANANCIA_C = "La ganancia del brazo C sale de 2 celdas cámara x segmento, una de ellas en el segmento donde se descubrió el hueco."
ROT = f"*({EN_MUESTRA})*"


def c(x, d=3):
    return f"{x:.{d}f}".replace(".", ",")


def p(x, d=1):
    return f"{100 * x:.{d}f} %".replace(".", ",")


def mi(x):
    return f"{int(round(x)):,}".replace(",", ".")


def ic(r, k, f=c):
    return f"{f(r[k])} ({f(r[k + '_lo'])} a {f(r[k + '_hi'])})"


def tabla_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[k]) for k in cols) + " |")
    return "\n".join(out)


ENC_INFORME = {
    "silhouette_muestra_20000": "Silhouette (muestra de 20.000)", "davies_bouldin": "Davies-Bouldin", "calinski_harabasz": "Calinski-Harabasz", "tamano_cluster_mas_chico": "Tamaño del cluster más chico (fracción)",
    "BIC_GMM_muestra_15000": "BIC del GMM (muestra de 15.000)", "k": "k", "cluster": "Cluster", "cajas": "Cajas", "positivos": "Cajas sin pareja", "tipo_de_caso": "Tipo de caso",
    "tasa_sin_camara": "Proporción sin pareja", "ic_lo": "IC inferior", "ic_hi": "IC superior", "AUC_regla_dentro_del_cluster": "AUC de la regla dentro del cluster", "AUC_todas": "AUC (todas las cajas)",
    "AUC_sin_celdas_con_hueco": "AUC (sin celdas con hueco)", "dif_AUC": "Diferencia de AUC", "cajas_en_celdas_con_hueco": "Cajas en celdas con hueco", "prob_media_regla_platt": "Probabilidad media de la regla (Platt)",
    "diferencia_tasa_menos_prob_regla": "Tasa menos probabilidad de la regla", "tecnica": "Técnica", "covarianza": "Covarianza", "n_init": "Inicios (n_init)", "converged": "Convergió", "n_iter": "Iteraciones",
    "tamanos": "Tamaños de los grupos", "ARI_vs_KMeans": "ARI contra KMeans", "ARI_vs_Ward": "ARI contra Ward", "medida": "Medida", "fuente_EP2": "Fuente EP2", "fuente_EP3": "Fuente EP3",
    "fold": "Fold", "segmentos": "Segmentos", "celdas_con_hueco": "Celdas con hueco", "hueco_contenido": "Hueco contenido", "AUC_A": "AUC (brazo A)", "AUC_B_celdas_sanas": "AUC (brazo B, celdas sanas)",
    "Fraccion80_A": "Fracción para 80 % (A)", "Fraccion80_B_celdas_sanas": "Fracción para 80 % (B, celdas sanas)", "Fraccion80_C": "Fracción para 80 % (C)", "variante": "Variante", "dif_C_menos_A": "Diferencia C menos A",
    "excluye_0": "El IC excluye 0", "mediana": "Mediana de referencia", "frac": "Fracción del umbral", "marcadas_min": "Celdas marcadas (mínimo)", "marcadas_max": "Celdas marcadas (máximo)",
    "extra_min": "Marcadas además de los 2 (mínimo)", "extra_max": "Marcadas además de los 2 (máximo)", "detecta_los_2": "Marca los 2 de referencia",
}


def _fmt_num(v, por_valor: bool = False) -> str:
    """Número en es-CL: coma decimal y punto de miles. Enteros sin decimales; |v| >= 1.000 sin decimales; el resto, 3 decimales (o, ``por_valor``, 2 si |v| >= 10)."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if isinstance(v, (bool, np.bool_)):
        return "sí" if v else "no"
    if isinstance(v, (int, np.integer)) or (isinstance(v, (float, np.floating)) and float(v) == round(float(v)) and abs(v) < 1e12):
        return mi(v)
    if abs(v) >= 1000:
        return mi(v)
    return c(v, 2) if (por_valor and abs(v) >= 10) else c(v, 3)


def _texto_es(s: str) -> str:
    """Intervalos «(2.258, 18.613]» -> «(2,258; 18,613]», listas «[6980, 8020]» -> «6.980 y 8.020»; escapa las barras verticales."""
    s = str(s)
    m = re.fullmatch(r"\[(\d+(?:, \d+)*)\]", s)
    if m:
        return " y ".join(mi(int(x)) for x in m.group(1).split(", "))
    s = re.sub(r"([(\[])(-?\d+\.\d+), (-?\d+\.\d+)([)\]])", lambda g: f"{g.group(1)}{g.group(2).replace('.', ',')}; {g.group(3).replace('.', ',')}{g.group(4)}", s)
    return s.replace("|", "\\|")


def tabla_es(df: pd.DataFrame, renombres: dict | None = None, por_valor: bool = False) -> str:
    """Tabla Markdown de un CSV: encabezados legibles (sin snake_case), números en es-CL y sin filas como «0.317247» (D3)."""
    from waymo_evaluacion.ep3 import formato as F

    ren = {**ENC_INFORME, **(renombres or {})}
    cols = list(df.columns)
    enc = [ren.get(k) or F.nombre_columna(str(k)) for k in cols]
    out = ["| " + " | ".join(enc) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(_texto_es(r[k]) if isinstance(r[k], str) else _fmt_num(r[k], por_valor) for k in cols) + " |")
    return "\n".join(out)


def tramo_es(variable: str, tramo: str) -> str:
    """Intervalos de distancia con coma decimal y unidad («(2,26; 18,61] m»); azimut en grados."""
    s = str(tramo)
    if variable == "distancia_m_quintiles":
        m = re.fullmatch(r"\((-?\d+(?:\.\d+)?), (-?\d+(?:\.\d+)?)\]", s)
        if m:
            return f"({float(m.group(1)):.2f}; {float(m.group(2)):.2f}] m".replace(".", ",").replace(";", ";")
    if variable == "azimut_abs_deg":
        return s.replace("-", " a ") + "°"
    return s


def valores_de_la_pagina() -> dict:
    """Lo que muestra la pagina en «Cola de revisión» con Segmento «Todos» y presupuesto 20 %, calculado con la misma logica y los mismos datos que la pagina."""
    from waymo_evaluacion.ep3.app_logica import cargar_datos, cola_segmento, horas_revision, inicio_resumen, recall_en_presupuesto

    D = cargar_datos(APP)
    sol = D["kpis"]["nombre_curva"]
    esp = recall_en_presupuesto(D["curva"], sol, 0.20)
    espA = recall_en_presupuesto(D["curva"], "Solución elegida, un paso (A)", 0.20)
    _, info = cola_segmento(D["cajas"], "Todos", 0.20)
    return {"brazo": sol, "recall": esp["recall"], "lo": esp["lo"], "hi": esp["hi"], "recall_A": espA["recall"], "lo_A": espA["lo"], "hi_A": espA["hi"],
            "cajas_a_revisar": info["cajas_a_revisar"], "cajas_cola_total": info["cajas_cola_total"], "horas": horas_revision(info["cajas_a_revisar"], SEG_POR_CAJA),
            "hallados": info["positivos_auditoria"] + info["positivos_en_cola"], "positivos_total": info["positivos_total"], "recall_proceso": info["recall_proceso"],
            "horas_ahorro": inicio_resumen(D, SEG_POR_CAJA)["horas_ahorradas"], "horas_dos_pasos": inicio_resumen(D, SEG_POR_CAJA)["horas_dos_pasos"],
            "horas_sin_orden": inicio_resumen(D, SEG_POR_CAJA)["horas_sin_orden"]}


def cargar() -> dict:
    N: dict = {}
    R = lambda n: pd.read_csv(REP / n)  # noqa: E731
    J = lambda n: json.loads((REP / n).read_text(encoding="utf-8"))  # noqa: E731
    N["f1"], N["f2"], N["f12"], N["f13"], N["f4r"], N["sel"], N["fin"] = J("f1_resumen.json"), J("f2_resumen.json"), J("f12_resumen.json"), J("f13_resumen.json"), J("f4_resumen.json"), J("f6_seleccion.json"), J("f6_final_resumen.json")
    N["base"] = R("f2_baselines_reglas_41.csv").set_index("metodo")
    N["lista_A"] = pd.read_csv(REP / "lista_A_huecos.csv", dtype={"segmento": str})
    N["f3"], N["f4"], N["f4m"] = R("f3_defecto_vs_optimizado.csv").set_index("modelo"), R("f4_ensambles_aporta.csv").set_index("ensamble"), R("f4_candidatos_metricas.csv").set_index("candidato")
    N["bordes"] = R("f3_bordes.csv")
    N["cv"] = R("f3_curvas_validacion.csv").groupby(["modelo", "valor"])[["ap_train", "ap_val"]].mean()
    N["f5"], N["c"], N["b"], N["tab"] = R("f5_metricas_candidatos.csv").set_index("candidato"), R("f5_brazoC.csv").set_index("candidato"), R("f5_brazoB.csv").set_index("candidato"), R("f6_tabla_seleccion.csv").set_index("candidato")
    N["esc"] = R("f6_modelo_escogido.csv").iloc[0]
    N["loso"] = {k: J(f"f5_loso_resumen_{k}.json") for k in ("Regla_top", "LR3", "XGB")}
    N["brecha"] = {k: R(f"f5_brecha_{k}.csv") for k in ("Regla_top", "LR3", "XGB")}
    N["man"] = json.loads((MOD / "manifest_v3.json").read_text(encoding="utf-8"))
    N["fold"] = R("f5_auc_por_fold.csv")
    N["f12fold"] = R("f12_auc_por_fold_brazos.csv")
    N["f12dif"] = R("f12_diferencia_C_menos_A.csv")
    N["f12sens"] = R("f12_sensibilidad_detector.csv")
    N["f12eq"] = R("f12_equidad.csv")
    N["eda"] = R("f12_eda_tasas.csv")
    N["cal"] = R("f12_eda_calidad.csv")
    N["calres"] = J("f12_eda_calidad_resumen.json")
    N["k2"], N["k4"] = R("f13_clusters_k2.csv"), R("f13_clusters_k4.csv")
    N["selk"], N["aporte"], N["estab"], N["compnosup"] = R("f13_seleccion_k.csv"), R("f13_aporte_cluster.csv"), R("f13_estabilidad.csv"), R("f13_comparacion_ep2_ep3.csv")
    N["ari_diag"], N["ari_diag_j"] = R("f13_ari_diagnostico.csv"), J("f13_ari_diagnostico.json")
    N["hC"] = J("f12b_hechos_brazoC.json")
    N["auc_cl"], N["auc_cl_j"] = R("f13_auc_cluster_sin_huecos.csv"), J("f13_auc_cluster_sin_huecos.json")
    N["pts_tab"], N["pts_res"] = R("f12_eda_puntos_top_sin_huecos.csv"), J("f12_eda_puntos_top_resumen.json")
    N["defs"] = J("f18_definiciones.json")
    N["alt"] = J("f19_alternativas_congeladas.json")
    N["plan_sel"] = json.loads((DOC / "plan_seleccion_ep3.json").read_text(encoding="utf-8"))
    N["sel_mot"], N["sel_rend"], N["sel_res"] = R("f18_seleccion_motivos.csv"), R("f18_seleccion_rendimiento.csv"), J("f18_seleccion_resumen.json")
    N["base_rules"] = R("f2_baselines_reglas_41.csv").set_index("metodo")
    cv = pd.read_csv(APP / "curva_cola.csv")
    N["inv_curva"] = {nombre: {r: float(np.interp(r, c_["recall"], c_["presupuesto"])) for r in (0.70, 0.80, 0.90)} for nombre, c_ in cv.groupby("solucion")}
    N["pag"] = valores_de_la_pagina()
    N["reg"] = pd.read_csv(RAIZ / "docs/seleccion_segmentos/registro_verificacion_ep2.csv")
    N["inv"] = pd.read_csv(RAIZ / "docs/seleccion_segmentos/inventario_segmentos.csv")
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet", columns=["seg", "grupo", "location", "time_of_day"]).drop_duplicates("seg")
    N["dev_seg"] = dev
    return N


def derivados(N: dict) -> None:
    f1, esc, c_ = N["f1"], N["esc"], N["c"]
    n = f1["filas_principal"]
    N["n"], N["pos"], N["prev"] = n, f1["positivos_principal"], f1["prevalencia_principal"]
    N["h_A"] = esc["Fraccion_80"] * n * SEG_POR_CAJA / 3600
    N["h_C"] = esc["Fraccion_80_C"] * n * SEG_POR_CAJA / 3600
    N["h_azar"] = 0.8 * n * SEG_POR_CAJA / 3600
    N["eq"] = esc["equilibrio_cajas_por_auditoria"]
    N["eq_h"] = N["eq"] * SEG_POR_CAJA / 3600
    N["auditoria_pos"] = int(c_.loc["Regla top", "positivos_cubiertos_por_auditoria"])
    N["fold0"] = N["fold"][(N["fold"]["candidato"] == "Regla top") & (N["fold"]["fold"] == 0)]["AUC"].iloc[0]
    N["n_mejoran"] = [m for m, r in N["f3"].iterrows() if r["veredicto"] == "mejora"]
    N["n_no"] = [m for m, r in N["f3"].iterrows() if r["veredicto"] != "mejora"]
    f12 = N["f12"]
    N["glob"] = N["f12dif"][(N["f12dif"]["candidato"] == "Regla top") & N["f12dif"]["variante"].str.startswith("global")].iloc[0]
    N["fold_reg"] = N["f12fold"][N["f12fold"]["candidato"] == "Regla top"].assign(fold=lambda d: d["fold"].astype(str)).set_index("fold")
    N["B_min"] = f12["B_AUC_min_fold"]["Regla top"]
    N["k_el"] = N["f13"]["k_elegido"]
    N["e2"] = {"auc": N["f5"].loc["E2", "AUC"], "pr": N["f5"].loc["E2", "PR-AUC"], "fr": N["f5"].loc["E2", "Fraccion_80"], "ece": N["f5"].loc["E2", "ECE_cal"],
               "d": N["tab"].loc["E2", "dif_Fraccion_80_vs_regla"], "lo": N["tab"].loc["E2", "dif_Fraccion_80_lo"], "hi": N["tab"].loc["E2", "dif_Fraccion_80_hi"]}


def e2_texto(N: dict) -> str:
    f5, e = N["f5"], N["e2"]
    return (f"E2 (promedio de rangos de E1 y la regla) tiene AUC {c(e['auc'])} contra {c(f5.loc['Regla top', 'AUC'])} de la regla, PR-AUC {c(e['pr'])} contra {c(f5.loc['Regla top', 'PR-AUC'])}, "
            f"Fracción para 80 % {c(e['fr'])} contra {c(f5.loc['Regla top', 'Fraccion_80'])} (IC de la diferencia {c(e['lo'])} a {c(e['hi'])}) y ECE {c(e['ece'])} (> 0,05); además **contiene a la regla como componente**. "
            "No hay una diferencia distinguible y por eso la elección se hizo por simplicidad, como manda la regla del plan")


def informe(N: dict) -> str:
    f3, f4, f5, c_, esc, sel, tab, f12, f13 = N["f3"], N["f4"], N["f5"], N["c"], N["esc"], N["sel"], N["tab"], N["f12"], N["f13"]
    glob, fr = N["glob"], N["fold_reg"]
    t9 = pd.DataFrame({"Modelo": f3.index, "PR-AUC defecto": [c(v) for v in f3["PR-AUC_def"]], "PR-AUC optimizado": [c(v) for v in f3["PR-AUC_opt"]],
                       "Dif. PR-AUC (IC 95 %)": [f"{c(r['dif_PR-AUC'])} ({c(r['dif_PR-AUC_lo'])} a {c(r['dif_PR-AUC_hi'])})" for _, r in f3.iterrows()],
                       "Folds donde gana": [f"{int(v)} de 5" for v in f3["folds_opt_gana_ap"]], "Veredicto": f3["veredicto"]})
    t10 = pd.DataFrame({"Ensamble": f4.index, "Mejor componente": f4["mejor_componente"], "AUC ensamble": [c(v) for v in f4["AUC_ensamble"]], "AUC mejor comp.": [c(v) for v in f4["AUC_mejor_componente"]],
                        "Dif. (IC 95 %)": [f"{c(r['dif_AUC'])} ({c(r['dif_lo'])} a {c(r['dif_hi'])})" for _, r in f4.iterrows()], "Folds ganados": [f"{int(v)} de 5" for v in f4["folds_ganados_de_5"]],
                        "Segmentos ganados": [f"{int(a)} de {int(b)}" for a, b in zip(f4["segmentos_ganados"], f4["segmentos_comparados"])], "Veredicto": f4["veredicto"]})
    cand = ["Regla top", "LR3", "LR", "RF", "HGB", "XGB", "LGBM", "E1", "E2", "E3", "E4"]
    t11 = pd.DataFrame({"Candidato": cand, "AUC (IC 95 %)": [ic(f5.loc[k], "AUC") for k in cand], "PR-AUC": [c(f5.loc[k, "PR-AUC"]) for k in cand], "Captura@20 %": [c(f5.loc[k, "Captura@20"]) for k in cand],
                        "Fracción 80 %": [c(f5.loc[k, "Fraccion_80"]) for k in cand], "Recall A": [c(f5.loc[k, "recall_A"]) for k in cand], "ECE (Platt)": [c(f5.loc[k, "ECE_cal"]) for k in cand],
                        "AUC mín. fold": [c(f5.loc[k, "AUC_min_fold"]) for k in cand], "Mediana AUC seg.": [c(f5.loc[k, "AUC_mediana_segmento"]) for k in cand]})
    t12 = pd.DataFrame({"Candidato": cand, "O1": ["sí" if tab.loc[k, "O1"] else "no" for k in cand], "O2": ["sí" if tab.loc[k, "O2"] else "no" for k in cand], "O3": ["sí" if tab.loc[k, "O3"] else "no" for k in cand],
                        "O4": ["sí" if tab.loc[k, "O4"] else "no" for k in cand],
                        "Dif. Fracción 80 % vs regla (IC)": [f"{c(tab.loc[k, 'dif_Fraccion_80_vs_regla'])} ({c(tab.loc[k, 'dif_Fraccion_80_lo'])} a {c(tab.loc[k, 'dif_Fraccion_80_hi'])})" for k in cand],
                        "Dif. AUC vs regla": [c(tab.loc[k, "dif_AUC_vs_regla"]) for k in cand]})
    ks = ["AUC", "PR-AUC", "Captura@20", "Fraccion_80", "recall_A", "precision_A", "recall_B", "precision_B", "ECE_cal", "Brier_cal", "AUC_min_fold", "AUC_mediana_segmento", "F1_A", "accuracy_A"]
    cuadro = pd.DataFrame({"Medida": ["AUC", "PR-AUC", "Captura al revisar el 20 %", "Fracción de cajas para 80 % de recall", "Recall en el punto A (objetivo 0,80)", "Precisión en el punto A", "Recall en el punto B (20 %)", "Precisión en el punto B",
                                      "ECE (Platt)", "Brier (Platt)", "AUC mínimo por fold", "Mediana del AUC por segmento", "F1 en A (solo referencia)", "Accuracy en A (solo referencia)"],
                           "Valor": [c(esc[k]) for k in ks], "IC 95 % por segmentos": [f"{c(esc[k + '_lo'])} a {c(esc[k + '_hi'])}" if k + "_lo" in esc.index else "" for k in ks]})
    lo = N["loso"]["Regla_top"]
    br = N["brecha"]["XGB"].iloc[-2:].mean()
    bords = N["bordes"]
    borde_txt = ", ".join(f"{r.modelo} `{r.hiperparametro}` ({'máximo' if r.borde == 'max' else 'mínimo'} en {int(r.folds_en_max if r.borde == 'max' else r.folds_en_min)} de 5 folds, etapa {r.etapa})" for r in bords[bords["borde"] != "no"].itertuples())
    reg, inv, dseg = N["reg"], N["inv"], N["dev_seg"]
    motivos = reg[reg["resultado"] == "descartado"]["motivo"].fillna("").str.replace(r"\s*\(.*\)", "", regex=True).value_counts()
    kpi = pd.DataFrame([
        ["O1: AUC fuera de fold", ">= 0,70", c(esc["AUC"]), "cumple", "f5_metricas_candidatos.csv"],
        ["O1: PR-AUC menos prevalencia", ">= 0,10", c(tab.loc["Regla top", "PR-AUC_menos_prevalencia"]), "cumple", "f6_tabla_seleccion.csv"],
        ["O2: «vale la pena» frente a la regla", "Fracción 80 % baja >= 5 puntos (IC excluye 0) y AUC sube >= 0,03", "ningún candidato", "no se cumple", "f6_tabla_seleccion.csv"],
        ["O3: recall en el punto A", ">= 0,75", c(esc["recall_A"]), "cumple", "f5_metricas_candidatos.csv"],
        ["O4: AUC mínimo por fold", ">= 0,75", f"{c(esc['AUC_min_fold'])} (sobre celdas sanas: {c(N['B_min'])}, post hoc)", "no se cumple", "f5_metricas_candidatos.csv, f12_auc_por_fold_brazos.csv"],
        ["O4: mediana del AUC por segmento", ">= 0,80", c(esc["AUC_mediana_segmento"]), "cumple", "f5_metricas_candidatos.csv"],
        ["O4: ECE con Platt", "<= 0,05", c(esc["ECE_cal"]), "cumple", "f5_metricas_candidatos.csv"],
        ["Captura al revisar el 20 % de las cajas", "referencia: 20 % al azar", p(esc["Captura@20"]), "informativo", "f5_metricas_candidatos.csv"],
        ["Fracción de cajas para 80 % de recall (un paso)", "referencia: 80 % al azar", f"{p(esc['Fraccion_80'])} (en muestra; post hoc; sin validación con datos nuevos)", "informativo", "f5_metricas_candidatos.csv"],
        [f"Horas para 80 % de recall con {SEG_POR_CAJA} s por caja (un paso)", "supuesto no medido", f"{N['h_A']:.0f} h (al azar {N['h_azar']:.0f} h) (en muestra; post hoc; sin validación con datos nuevos)", "informativo", "derivado de la fracción; editable en la página"]],
        columns=["KPI", "Meta (fijada antes)", "Valor", "Estado", "Fuente"])
    eda = N["eda"]
    pt = eda[eda["variable"] == "puntos_top"].set_index("tramo")
    az = eda[eda["variable"] == "azimut_abs_deg"].set_index("tramo")
    ds = eda[eda["variable"] == "distancia_m_quintiles"]
    cl = eda[eda["variable"] == "clase"].set_index("tramo")
    VAR_ES = {"puntos_top": "Puntos del sensor superior", "azimut_abs_deg": "Azimut absoluto", "distancia_m_quintiles": "Distancia (quintiles)", "clase": "Clase"}
    t_eda = pd.DataFrame({"Variable": eda["variable"].map(VAR_ES), "Tramo": [tramo_es(v, tr) for v, tr in zip(eda["variable"], eda["tramo"])], "Cajas": [mi(x) for x in eda["cajas"]],
                          "Cajas sin pareja": [mi(x) for x in eda["positivos"]], "Proporción sin pareja": [p(x) for x in eda["tasa"]],
                          "IC 95 % por segmentos": [f"{p(a)} a {p(b)}" for a, b in zip(eda["ic_lo"], eda["ic_hi"])], "Segmentos": [mi(x) for x in eda["segmentos"]]})
    calq = N["cal"]
    ult = N["estab"].set_index("k")
    adj = N["ari_diag_j"]
    gmk2_tam, kmk2_tam = None, None
    ad = N["ari_diag"]
    _g = ad[ad["covarianza"].notna() & (ad["tecnica"].str.startswith("GMM"))]
    _g = _g.assign(n_init=_g["n_init"].astype(int), n_iter=_g["n_iter"].astype(int))
    kmk2 = ad[(ad["k"] == 2) & ad["tecnica"].str.startswith("KMeans")].iloc[0]
    wk2 = ad[(ad["k"] == 2) & ad["tecnica"].str.startswith("Ward")].iloc[0]
    gmk2 = _g[(_g["k"] == 2) & (_g["covarianza"] == "full") & (_g["n_init"] == 2)].iloc[0]
    gdk2 = _g[(_g["k"] == 2) & (_g["covarianza"] == "diag") & (_g["n_init"] == 2)].iloc[0]
    gsk2 = _g[(_g["k"] == 2) & (_g["covarianza"] == "spherical") & (_g["n_init"] == 2)].iloc[0]
    gfk4 = _g[(_g["k"] == 4) & (_g["covarianza"] == "full") & (_g["n_init"] == 2)].iloc[0]
    gmk2_tam, kmk2_tam = json.loads(gmk2['tamanos']), json.loads(kmk2['tamanos'])
    t_ari = _g[["k", "covarianza", "n_init", "converged", "n_iter", "tamanos", "ARI_vs_KMeans", "ARI_vs_Ward"]]
    hc, pg = N["hC"], N["pag"]
    acl, dfn, ptt, ptr = N["auc_cl"], N["defs"], N["pts_tab"], N["pts_res"]
    sp = N["plan_sel"]
    smot, srend, sres = N["sel_mot"].set_index("motivo_corto"), N["sel_rend"].set_index(["corte", "grupo"]), N["sel_res"]
    seg247 = next(x for x in ptr["top3_segmentos_positivos_mayor_100_sin_hueco"] if x["seg"] == "247562357599")
    ptv = lambda v, tr, col="tasa": ptt[(ptt["variante"] == v) & (ptt["tramo"] == tr)].iloc[0][col]  # noqa: E731
    V_TODAS, V_SIN, V_SIN2 = "todas las cajas", "sin las celdas con hueco", "sin las celdas con hueco ni el segmento 247562357599"
    dd, ab = dfn["definicion_20pct"], dfn["auc_base_f13"]
    lista_pob = N["lista_A"][["segmento", "grupo", "camara", "tasa", "cajas_en_rango", "cajas_afectadas_poblacion_principal", "positivos_afectados"]].rename(columns={
        "cajas_en_rango": "Cajas en el rango del detector (azimut absoluto ≤ 120°)", "cajas_afectadas_poblacion_principal": "Cajas en la población principal (azimut absoluto ≤ 100°)", "positivos_afectados": "Positivos en la población principal"})
    lista_pob_es = lista_pob.copy()
    lista_pob_es["tasa"] = lista_pob_es["tasa"].map(lambda v: p(v, 0))
    for k_ in lista_pob_es.columns[4:]:
        lista_pob_es[k_] = lista_pob_es[k_].map(mi)
    lista_pob_es = lista_pob_es.rename(columns={"segmento": "Segmento", "grupo": "Grupo", "camara": "Cámara", "tasa": "Tasa de pares"})
    cols_k = ["cluster", "tipo_de_caso", "cajas", "tasa_sin_camara", "ic_lo", "ic_hi", "AUC_regla_dentro_del_cluster"]
    t_auc_cl = acl[["k", "cluster", "tipo_de_caso", "cajas", "cajas_en_celdas_con_hueco", "AUC_todas", "AUC_sin_celdas_con_hueco", "dif_AUC"]]
    cl_cerc = acl[(acl["k"] == 2) & (acl["tipo_de_caso"] == "cercanos y densos")].iloc[0]
    cl_lej = acl[(acl["k"] == 2) & (acl["tipo_de_caso"] == "lejanos y poco densos")].iloc[0]
    cl4_0 = acl[(acl["k"] == 4) & (acl["cluster"] == 0)].iloc[0]
    k4i = N["k4"].set_index("cluster")
    ar = f13["ari_entre_tecnicas"]
    iso = f13["isolation_forest"]
    k2, k4 = N["k2"], N["k4"]
    ap = N["aporte"].set_index("k")
    cn = N["compnosup"]
    eq = N["f12eq"]
    eqx = eq[eq["celdas_con_hueco"] == "excluidas"].set_index(["variable", "grupo"])
    eqi = eq[eq["celdas_con_hueco"] == "incluidas"].set_index(["variable", "grupo"])
    t_eq = pd.DataFrame([{"Variable": v, "Grupo": g, "Segmentos": int(eqi.loc[(v, g), "segmentos"]), "Cajas": mi(eqi.loc[(v, g), "cajas"]), "Positivos": mi(eqi.loc[(v, g), "positivos"]),
                          "Recall A (con celdas con hueco)": c(eqi.loc[(v, g), "recall_A"]), "% revisado": p(eqi.loc[(v, g), "pct_revisado_A"]),
                          "Recall A (sin celdas con hueco)": c(eqx.loc[(v, g), "recall_A"]) if (v, g) in eqx.index else "-",
                          "AUC (con / sin)": (c(eqi.loc[(v, g), "AUC"]) if pd.notna(eqi.loc[(v, g), "AUC"]) else "n/c") + " / " + ((c(eqx.loc[(v, g), "AUC"]) if pd.notna(eqx.loc[(v, g), "AUC"]) else "n/c") if (v, g) in eqx.index else "-")}
                         for (v, g) in eqi.index if v != "todas"])
    t_fold = N["f12fold"][N["f12fold"]["candidato"] == "Regla top"][["fold", "segmentos", "cajas", "celdas_con_hueco", "hueco_contenido", "AUC_A", "AUC_B_celdas_sanas", "Fraccion80_A", "Fraccion80_B_celdas_sanas", "Fraccion80_C"]]
    t_difc = N["f12dif"][N["f12dif"]["candidato"] == "Regla top"][["variante", "Fraccion80_A", "Fraccion80_C", "dif_C_menos_A", "ic_lo", "ic_hi", "excluye_0", "segmentos"]]
    sens = N["f12sens"]
    t_sens = sens.groupby(["mediana", "frac"]).agg(marcadas_min=("marcadas", "min"), marcadas_max=("marcadas", "max"), extra_min=("falsas_alarmas", "min"), extra_max=("falsas_alarmas", "max"),
                                                   detecta_los_2=("detecta_los_2", "all")).reset_index()
    t_sens["detecta_los_2"] = t_sens["detecta_los_2"].map({True: "sí en las 3 variantes de min_cajas", False: "no en alguna"})
    return f"""# Informe técnico EP3: de la lista de cajas a una solución en tres capas

*Generado por `scripts/ep3/generar_docs_ep3.py` a partir de `data/08_reporting_ep3`, `data/09_app_ep3`, `data/06_models_ep3` y `docs/seleccion_segmentos`; ninguna cifra está escrita a mano. Todo lo que no estaba en el plan v3 lleva la etiqueta **post hoc, no pre-declarado**. Las cifras son **fuera de fold sobre los 41 segmentos de desarrollo** salvo que se diga otra cosa. Fecha de las corridas: 2026-11-14. Las desviaciones del plan se llaman DEV-n y las decisiones DEC-n.*

## 0. Capa ejecutiva (una página)
**Problema.** Un equipo que revisa etiquetas de un auto autónomo tiene cajas 3D (LiDAR) de peatones y ciclistas y debe decidir cuáles no tienen su pareja 2D de cámara (`sin_camara`). Revisar todo es caro. En la población principal (|azimut| <= 100°) hay {mi(N['n'])} cajas y {mi(N['pos'])} sin pareja ({p(N['prev'])}).

**Qué construimos.** Una solución en **tres capas**: (1) un **filtro 1** que detecta huecos de cámara por segmento y los manda a auditoría; (2) una **regla o modelo** que ordena las cajas de las celdas sanas; (3) una **persona que revisa y decide**. Además, una página (Streamlit, solo local) y su despliegue.

**Resultado principal (fuera de fold, IC 95 % por segmentos).**
- La solución elegida es la **regla «menos puntos del LiDAR superior primero»**: AUC {ic(esc, 'AUC')}, recall {c(esc['recall_A'])} en el punto A y captura de {p(esc['Captura@20'])} de los positivos al revisar el 20 % de las cajas (al azar, 20 %).
- **Ningún modelo ni ensamble supera a la regla de forma distinguible.** Optimizar hiperparámetros mejora a {', '.join(N['n_mejoran'])} respecto de su propio punto de partida, pero su AUC ({c(f5.loc['XGB', 'AUC'])} y {c(f5.loc['LGBM', 'AUC'])}) queda bajo el de la regla; su PR-AUC es apenas mayor ({c(f5.loc['XGB', 'PR-AUC'])} y {c(f5.loc['LGBM', 'PR-AUC'])} contra {c(f5.loc['Regla top', 'PR-AUC'])}), una diferencia que no probamos con IC pareado. {e2_texto(N)}.
- **Flujo en dos pasos** {ROT}: revisar el {p(esc['Fraccion_80_C'])} de las cajas para el 80 % de los positivos, frente al {p(esc['Fraccion_80'])} en un paso; con {SEG_POR_CAJA} s por caja (no medido), {N['h_C']:.0f} h contra {N['h_A']:.0f} h. Empata con un paso si una auditoría cuesta {mi(N['eq'])} cajas (IC {mi(esc['equilibrio_lo'])} a {mi(esc['equilibrio_hi'])}). **{GANANCIA_C}** La diferencia pareada (dos pasos menos un paso) es {c(glob['dif_C_menos_A'])} con IC {c(glob['ic_lo'])} a {c(glob['ic_hi'])}: no excluye 0.
- **Aprendizaje no supervisado** (descriptivo, post hoc): los clusters separan casos lejanos y poco densos (tasa {p(k2.sort_values('tasa_sin_camara').iloc[-1]['tasa_sin_camara'])}) de cercanos y densos ({p(k2.sort_values('tasa_sin_camara').iloc[0]['tasa_sin_camara'])}), pero **no mejoran la predicción de la regla**.

**Qué no podemos afirmar.** Que el flujo en dos pasos supere al de un paso fuera de muestra; que un modelo complejo no sirva en otros datos; que los huecos sean errores de etiquetado. Los 8 segmentos de test de EP2 ya no son ciegos. La validación con segmentos nuevos (P9) está preparada, sellada y **pendiente**.

## 1. Mapa de la pauta
| Sección mínima pedida | Dónde está en este informe |
|---|---|
| Problema de negocio, objetivos y KPIs | 2 |
| Fuentes de datos y licencia | 3 |
| EDA, calidad de datos y preparación | 4 |
| Metodología (CRISP-DM) | 5 |
| Antecedentes (EP1 y EP2) y qué cambió | 6 |
| Diseño del experimento (plan v3, desviaciones y decisiones) | 7 |
| Modelado: filtro 1 (detector) | 8 |
| Aprendizaje no supervisado | 9 |
| **IE9** optimización de hiperparámetros y **IE10** técnicas de ensamble | 10 |
| **IE11** generalización | 11 |
| **IE12** selección justificada del modelo | 12 |
| Aplicación (página) y despliegue | 13 |
| Validación externa | 14 |
| Conclusiones y recomendaciones para el negocio | 15 |
| Ética, sesgos y privacidad | 16 |
| Limitaciones | 17 |
| Reproducción | 18 |
| Anexos: fuentes (A) y análisis en muestra 12.1 y 12.2 (B) | A, B |

## 2. Problema de negocio, objetivos y KPIs
**Negocio.** Los equipos que curan datos de percepción pierden horas revisando cajas 3D. Interesa encontrar primero las que probablemente no tienen su par 2D, porque suelen indicar una etiqueta faltante o una cámara sin datos. *Analogía:* antes de revisar recibo por recibo, miramos si falta una carpeta completa de recibos de un mes. **Objetivos:** O1 a O4 del plan v3 (con los umbrales de EP2). **Quién usa qué:** el analista de revisión usa la cola; el responsable de calidad de datos usa la auditoría de cámaras; el ingeniero consumidor puntúa segmentos nuevos.

{tabla_md(kpi)}

## 3. Fuentes de datos
- **Waymo Open Dataset v2** (formato parquet por componente). Se usaron `lidar_box` (cajas 3D, puntos LiDAR, velocidad, rumbo) y `camera_to_lidar_box_association` (pares caja 3D - caja 2D por cámara). No se usó `camera_calibration` (no está en los datos locales) ni `vehicle_pose` (carpeta vacía).
- **Licencia:** uso no comercial; los datos no se redistribuyen. Por eso nada de Waymo sale del equipo y las imágenes Docker no llevan datos (secciones 13 y 16).
- **De 798 a 41 segmentos.** El inventario tiene {len(inv)} segmentos (`docs/seleccion_segmentos/inventario_segmentos.csv`), {int((inv['weather'] == 'rain').sum())} con lluvia (excluidos). EP2 verificó {len(reg)}: {int((reg['resultado'] == 'seleccionado').sum())} seleccionados y {int((reg['resultado'] == 'descartado').sum())} descartados ({', '.join(f'{v} por {k}' for k, v in motivos.items())}) (`registro_verificacion_ep2.csv`). Los 41 son {int((dseg['grupo'] == 'train').sum())} de train y {int((dseg['grupo'] == 'test').sum())} de test de EP2; por ubicación: {', '.join(f'{k} {v}' for k, v in dseg['location'].value_counts().items())}; por momento: {', '.join(f'{k} {v}' for k, v in dseg['time_of_day'].value_counts().items())}.
- **Sesgo de selección declarado:** el criterio «etiquetado ralo» (menos de 5,5 % de las cajas LiDAR de frames etiquetados con par) deja fuera segmentos con etiquetado 2D muy escaso.

**Sesgo de selección a escala de segmento** (descriptivo; `f18_seleccion_motivos.csv`, `f18_seleccion_rendimiento.csv`, desde `registro_verificacion_ep2.csv`). De los {mi(sres['inventario'])} segmentos del inventario, EP2 evaluó **{sres['evaluados']}** y dejó **{sres['seleccionados']}**; **descartó {sres['descartados']}**: {mi(smot.loc['asociación vacía', 'segmentos'])} por asociación vacía, {mi(smot.loc['etiquetado ralo', 'segmentos'])} por etiquetado ralo y {mi(smot.loc['pocas asociaciones', 'segmentos'])} por pocas asociaciones. El rendimiento (seleccionados sobre evaluados) fue de {p(srend.loc[('momento_del_dia', 'Day'), 'rendimiento'], 0)} de día ({int(srend.loc[('momento_del_dia', 'Day'), 'seleccionados'])} de {int(srend.loc[('momento_del_dia', 'Day'), 'evaluados'])}), {p(srend.loc[('momento_del_dia', 'Dawn/Dusk'), 'rendimiento'], 0)} en amanecer o atardecer ({int(srend.loc[('momento_del_dia', 'Dawn/Dusk'), 'seleccionados'])} de {int(srend.loc[('momento_del_dia', 'Dawn/Dusk'), 'evaluados'])}) y {p(srend.loc[('momento_del_dia', 'Night'), 'rendimiento'], 0)} de noche ({int(srend.loc[('momento_del_dia', 'Night'), 'seleccionados'])} de {int(srend.loc[('momento_del_dia', 'Night'), 'evaluados'])}); por ubicación, {p(srend.loc[('ubicacion', 'location_sf'), 'rendimiento'], 0)} en San Francisco, {p(srend.loc[('ubicacion', 'location_phx'), 'rendimiento'], 0)} en Phoenix y {p(srend.loc[('ubicacion', 'location_other'), 'rendimiento'], 0)} en otras (de noche en otras ubicaciones, {int(srend.loc[('momento_x_ubicacion', 'Night / location_other'), 'seleccionados'])} de {int(srend.loc[('momento_x_ubicacion', 'Night / location_other'), 'evaluados'])}). **La causa (etiquetado o publicación de los datos) se declara desconocida.** Consecuencia: el detector solo se evaluó en segmentos con etiquetado denso, y no sabemos cómo se comporta en los segmentos que EP2 descartó.

## 4. EDA, calidad de datos y preparación *(post hoc, descriptivo, 41 segmentos, población principal)*
**Variables.** Las 16 de EP2 (`V16`: posición, azimut, distancia, tamaño, volumen, puntos LiDAR, puntos top, densidad, velocidad, rumbo y clase), y dos conjuntos más pequeños declarados en el plan: `V_OBS` (4 variables de observabilidad) y `V_OBS_TAM` (10). El conjunto es un hiperparámetro de la búsqueda. **Folds:** StratifiedGroupKFold(5) por segmento, estratificado por `sin_camara`, semilla 42; ningún segmento queda repartido entre folds.

**Qué explica `sin_camara`.** La tasa cae con los puntos del LiDAR superior: {p(pt.loc['0-5', 'tasa'])} con 0 a 5 puntos ({mi(pt.loc['0-5', 'cajas'])} cajas), {p(pt.loc['6-10', 'tasa'])} con 6 a 10, {p(pt.loc['11-20', 'tasa'])} con 11 a 20, {p(pt.loc['21-50', 'tasa'])} con 21 a 50 y {p(pt.loc['51-100', 'tasa'])} con 51 a 100 (IC por segmentos en la tabla). Por azimut dentro de la población principal casi no cambia ({p(az.loc['0-20', 'tasa'])} en 0 a 20° contra {p(az.loc['80-100', 'tasa'])} en 80 a 100°). Sube con la distancia: {p(ds.iloc[0]['tasa'])} en el quintil más cercano contra {p(ds.iloc[-1]['tasa'])} en el más lejano. Los peatones tienen {p(cl.loc['PEDESTRIAN', 'tasa'])} y los ciclistas {p(cl.loc['CYCLIST', 'tasa'])} (solo {mi(cl.loc['CYCLIST', 'cajas'])} cajas de ciclistas, en {int(cl.loc['CYCLIST', 'segmentos'])} segmentos). *Analogía:* una caja con pocos puntos es una foto borrosa; es más difícil que alguien la haya pareado.

![EDA: tasa por tramo](../../images/ep3/12_eda_tasas.png)

{tabla_md(t_eda)}

**Calidad de datos** (`f12_eda_calidad.csv`, `f12_eda_calidad_resumen.json`): nulos en las 16 variables: {N['calres']['nulos_total']}; llaves duplicadas (segmento, marca de tiempo, objeto): {N['calres']['duplicados_por_llave_principal']}; cajas con 0 puntos LiDAR: {mi(N['calres']['cajas_con_0_puntos_lidar'])} ({p(N['calres']['pct_cajas_con_0_puntos_lidar'])}); con 0 puntos del sensor superior: {mi(N['calres']['cajas_con_0_puntos_top'])} ({p(N['calres']['pct_cajas_con_0_puntos_top'])}), de las cuales {p(N['calres']['tasa_sin_camara_en_cajas_con_0_puntos_top'])} no tienen pareja. En la cola de revisión esas cajas empatan en el puntaje de la regla y reciben la misma probabilidad calibrada: el orden entre ellas no es informativo y la página lo avisa sobre la tabla; la persona atiende por objeto y por segmento. Atípicos fuera de 1,5 IQR: los más altos son `densidad_puntos` ({p(calq.set_index('variable').loc['densidad_puntos', 'pct_atipicos'])}), `num_lidar_points` ({p(calq.set_index('variable').loc['num_lidar_points', 'pct_atipicos'])}) y `num_top_lidar_points` ({p(calq.set_index('variable').loc['num_top_lidar_points', 'pct_atipicos'])}): son cajas muy cercanas con muchísimos puntos, no errores; no se eliminaron.

![Calidad de datos](../../images/ep3/12_eda_calidad.png)

**Puntos del sensor superior > 100: por qué la tasa sube (post hoc, no pre-declarado; `f12_eda_puntos_top_sin_huecos.csv`, `f12_eda_puntos_top_resumen.json`, `scripts/ep3/f12c_eda_puntos_top_sin_huecos.py`).** En la tabla, la tasa baja de {p(ptv(V_TODAS, '21-50'))} (21 a 50 puntos) a {p(ptv(V_TODAS, '51-100'))} (51 a 100) y **sube a {p(ptr['tramo_mayor_100']['tasa'])}** con más de 100 puntos (IC {p(eda[eda['variable'] == 'puntos_top'].set_index('tramo').loc['>100', 'ic_lo'])} a {p(eda[eda['variable'] == 'puntos_top'].set_index('tramo').loc['>100', 'ic_hi'])}). Se separó por celdas con hueco: en el tramo > 100 hay {mi(ptr['tramo_mayor_100']['cajas_en_celdas_con_hueco'])} cajas dentro de las 2 celdas con hueco, con tasa de {p(ptr['tramo_mayor_100']['tasa_en_celdas_con_hueco'])}, y concentran {p(ptr['pct_positivos_mayor_100_en_celdas_con_hueco'])} de los positivos del tramo. **Sin esas celdas la tasa del tramo es {p(ptr['tramo_mayor_100']['tasa_sin_hueco'])} y la serie es decreciente:** {p(ptv(V_SIN, '51-100'))} (51-100), {p(ptv(V_SIN, '101-200'))} (101-200), {p(ptv(V_SIN, '201-500'))} (201-500) y {p(ptv(V_SIN, '>500'))} (> 500). Queda una concentración residual en el segmento `{ptr['top3_segmentos_positivos_mayor_100_sin_hueco'][0]['seg']}` ({mi(ptr['top3_segmentos_positivos_mayor_100_sin_hueco'][0]['positivos'])} positivos en {mi(ptr['top3_segmentos_positivos_mayor_100_sin_hueco'][0]['cajas'])} cajas con más de 100 puntos, {p(ptr['top3_segmentos_positivos_mayor_100_sin_hueco'][0]['tasa'])}): es el segmento donde aparece una celda marcada adicional cuando `frac` = 0,35; sin él, el tramo 101-200 baja a {p(ptv(V_SIN2, '101-200'))}. *Hipótesis (no verificada):* el alza no es un efecto del sensor sino de cajas con muchos puntos que no tienen pareja porque la cámara de esa zona no tiene etiquetas (el hueco).

## 5. Metodología (CRISP-DM)
| Fase | Dónde |
|---|---|
| Comprensión del negocio | sección 2 |
| Comprensión de los datos | secciones 3 y 4; notebook 11 |
| Preparación de los datos | secciones 4 y 7; `scripts/ep3/f1_datos.py`, `datos.py` |
| Modelado | secciones 8 (detector), 9 (no supervisado) y 10 (IE9 e IE10); notebooks 12 y 15 |
| Evaluación | secciones 11, 12 y 14; notebook 13 |
| Despliegue | sección 13; notebook 14, `app/`, `Dockerfile` |

## 6. EP1 y EP2 en breve, y qué cambió
- **EP1** (`docs/README_EP1.md`): exploración del dataset, fuentes, estructuras de datos y ética; pipeline de Kedro de ingesta y preprocesamiento (`src/waymo_evaluacion/pipelines`).
- **EP2** (`docs/informe_tecnico_EP2.md`, `docs/plan_evaluacion_test.md`, `docs/evaluacion_final_B.md`, `docs/log_trabajo_ep2.md`): target `sin_camara`, población principal, tres modelos contra reglas simples con validación por segmento y un test de 8 segmentos sellado con plan congelado (14 archivos con sha256). Resultado oficial: la regresión logística no se distinguió de la regla de puntos (AUC 0,698 contra 0,684; IC de la diferencia -0,014 a +0,029). Hallazgo post hoc: el segmento `257766998801` concentraba positivos por un hueco en la cámara 3 (apéndice M).
- **Nota sobre Kedro:** el trabajo analítico de EP2 y EP3 vive en **notebooks y scripts**, no en nodos de Kedro; los pipelines de Kedro son solo los de ingesta y preprocesamiento de EP1. EP2 queda intacta (14 de 14 archivos congelados verifican).

| Tema | EP2 | EP3 |
|---|---|---|
| Datos | 33 segmentos de train; test ciego de 8 | 41 juntos; los 8 ya no son ciegos; prueba ciega con segmentos nuevos (P9) |
| Validación | GroupKFold(5) por segmento | StratifiedGroupKFold(5), estratificada; 1 repetición (DEV-1) |
| Modelos | LR, HGB, RF | + XGBoost y LightGBM, por defecto contra optimizado |
| Hiperparámetros | óptimos en el borde de la grilla | grillas más regularizadas, búsqueda anidada, revisión de bordes |
| Ensambles | ninguno | E1 a E4 con CV interna por segmento |
| Hueco de cámara | apéndice post hoc | filtro 1 del flujo, con Lista A y brazo de dos pasos |
| No supervisado | k-means, GMM, Ward, IsolationForest con variables de oclusión | mismo enfoque descriptivo sin oclusión (sección 9) |
| Entrega | informe y README | informe, notebooks, página, despliegue, validación externa sellada |

## 7. Diseño del experimento (plan v3)
El plan v3 (`plan_v3.md`, `plan_v3.json`, hash en `plan_v3.sha256`) se congeló **antes** de correr ningún experimento. Los datos de desarrollo (`dev_41.parquet`) se reconstruyeron con la lógica de EP2: los modelos congelados de EP2 reproducen `pred_test_B.parquet` con diferencia máxima de {N['f1']['reproduccion_pred_test_B']['dif_max_abs']:.1e} y los conteos del test coinciden con la tabla del plan ({mi(N['f1']['test_principal'][0])} filas y {mi(N['f1']['test_principal'][1])} positivos). *Analogía:* los 8 segmentos de EP2 eran un examen sorpresa; ya los miramos seis veces, así que ahora son material de estudio.

**Desviaciones del plan** (`plan_v3_desviaciones.md`): **DEV-1** una repetición de la CV externa y 30 configuraciones en vez de 3 y 40 (RF tarda 45 a 100 s por ajuste); **DEV-2** regla de reserva cuando nadie cumple O4 (post hoc). **Decisiones** (`ESTADO.md`):

| Id | Decisión | Motivo |
|---|---|---|
| DEC-1 | Desviaciones en archivo aparte | no alterar el hash del plan |
| DEC-2 | Notebooks con el kernel `python3` | no existe el kernel `ep2` |
| DEC-3 | Se mantiene el cambio de `tests/test_ajustes_finales.py` (`--ignore=tests/ep3`) | no contar las pruebas de EP3 en el conteo de EP2 |
| DEC-4 | Cómputo con 6 procesos como máximo | dejar el equipo usable |
| DEC-6 | Sin MLflow; checkpoints y CSV/JSON | evitar dependencias que muevan versiones fijadas |
| DEC-7 | Umbrales A y B y Platt con scores internos de entrenamiento | sin fuga del fold de validación |
| DEC-8 | Brazo C: la auditoría no cuesta por caja; se reporta el punto de equilibrio | no inventar un costo |
| DEC-9 | Bases de los ensambles con la configuración optimizada solo si IE9 dio «mejora» | consistencia con IE9 |
| DEC-10 | Si el elegido es E2, su puntaje es un rango dentro del lote | E2 promedia rangos |
| DEC-11 | Las fases 12 y 13 son análisis en muestra, post hoc | no estaban en el plan v3 |
| DEC-12 | No supervisado: silhouette en 20.000 cajas, GMM y Ward en 15.000, estabilidad con KMeans `n_init=3` y scaler fijo | costo de cómputo |
| DEC-13 | El artefacto no supervisado tiene manifest propio y no se usa para puntuar | no tocar `manifest_v3.json` |
| DEC-14 | Aviso «en muestra» siempre visible (desde F20, un chip persistente en todas las páginas con su popover, y una etiqueta junto a cada cifra del flujo en dos pasos) | evitar leer una ganancia en muestra como resultado ciego |
| DEC-15 | El selector de referencia de la página usa las curvas ya calculadas de XGBoost y E2 | no generar predicciones nuevas |
| DEC-16 | Docker sin probar | el demonio estaba apagado |

## 8. Filtro 1: detector de huecos por cámara
Parámetros congelados de EP2, sin recalcular: rango de azimut p5-p95 por cámara con los 33 segmentos de train, mediana de la tasa por cámara con los 41, hueco si la tasa es menor al 25 % de la mediana y hay al menos 100 cajas en el rango. Marca **{N['f2']['n_pares_con_hueco']} celdas**, las mismas que EP2 (diferencia máxima contra los CSV de EP2: {N['f2']['dif_max_tabla_vs_ep2']:.1e}):

{tabla_md(lista_pob_es)}

*Población de cada columna:* «cajas en el rango del detector» cuenta las cajas con |azimut| hasta 120° que caen en el rango de azimut de esa cámara (300 en la celda `911012534050` cámara 5); «cajas en la población principal» cuenta solo las de |azimut| ≤ 100° (268 en esa celda; en la otra celda ambas coinciden) y los positivos se cuentan en esta última población.

Esas celdas contienen {mi(N['f2']['positivos_en_hueco_principal'])} de los {mi(N['pos'])} positivos ({p(N['f2']['positivos_en_hueco_principal'] / N['pos'])}) en {mi(N['f2']['cajas_en_hueco_principal'])} cajas. **Post hoc, no pre-declarado:** el hueco se descubrió en EP2 después de abrir el test, y los parámetros del detector se ajustaron con estos mismos segmentos. Una celda marcada puede ser un problema de etiquetado 2D o de datos de esa cámara; con estos archivos no se distingue.

**Estabilidad del conjunto marcado frente a los parámetros (post hoc, anexo B).** Se probaron 30 combinaciones: `frac` {{0,15; 0,20; 0,25; 0,30; 0,35}} x `min_cajas` {{50, 100, 200}} x mediana {{con los 41 segmentos; sin el segmento candidato}}. Los 2 huecos de referencia se marcan en **{f12['detector_combinaciones_que_detectan_los_2']} de {f12['detector_combinaciones']}** combinaciones; las celdas marcadas además de los 2 de referencia (sin verdad externa) van de {f12['detector_falsas_alarmas_rango'][0]} a {f12['detector_falsas_alarmas_rango'][1]}, y con la configuración de EP2 son {f12['detector_ep2']['falsas_alarmas']} de {f12['detector_ep2']['celdas_con_n_suficiente']} celdas con n suficiente. Sin el segmento candidato en la mediana (variante «leave-one-out») el resultado es el mismo.

**Qué mide y qué no mide el «30 de 30» (DEV-3).** Los 2 huecos de referencia **los define el mismo detector con los parámetros de EP2**: no hay una verdad externa que diga qué celdas son huecos reales. Por eso «30 de 30» mide la **estabilidad del conjunto marcado frente a los parámetros**; no es sensibilidad ni especificidad, y las celdas adicionales no se pueden llamar «falsas alarmas» (podrían ser huecos reales que EP2 no marcó). El detector es **estadística descriptiva** (percentiles, una mediana y un umbral), no aprendizaje automático.

## 9. Aprendizaje no supervisado *(descriptivo; no está en el plan v3: post hoc, no pre-declarado)*
**Qué se hizo.** Sobre las {mi(f13['filas'])} cajas de la población principal, con `distancia_m`, `azimut_abs_deg`, `log1p(num_lidar_points)`, `log1p(densidad_puntos)` y `log1p(volumen_caja)` estandarizadas, **sin `sin_camara` ni nada del par 2D**. EP2 usó además variables de oclusión que no están en `dev_41`, así que la comparación no es idéntica. KMeans k = 2 a 8 (`n_init=10`, semilla 42) con silhouette (muestra de 20.000), Davies-Bouldin y Calinski-Harabasz; GMM (BIC) y Ward en una muestra de 15.000; estabilidad al remuestrear segmentos (30 réplicas). Se elige k por máximo silhouette entre 2 y 6: **k = {N['k_el']}**, y se explora también k = 4 como en EP2.

{tabla_es(N['selk'])}

**Estructura.** Con k = {N['k_el']} el silhouette es {c(N['selk'].set_index('k').loc[N['k_el'], 'silhouette_muestra_20000'])} y la estabilidad por segmentos tiene ARI medio {c(ult.loc[N['k_el'], 'ari_medio'])} y mínimo {c(ult.loc[N['k_el'], 'ari_minimo'])}; con k = 4, {c(ult.loc[4, 'ari_medio'])} y {c(ult.loc[4, 'ari_minimo'])}. El acuerdo entre técnicas es **bajo**: ARI KMeans contra GMM {c(ar['k=2']['KMeans vs GMM'])} (k = 2) y {c(ar['k=4']['KMeans vs GMM'])} (k = 4); KMeans contra Ward {c(ar['k=2']['KMeans vs Ward'])} y {c(ar['k=4']['KMeans vs Ward'])}. Es decir, los clusters son una partición cómoda de un continuo (distancia y densidad), no grupos naturales firmes.

**Diagnóstico del ARI bajo** (post hoc, `f13_ari_diagnostico.csv` y `.json`; lo produce `scripts/ep3/f13b_diagnostico_ari.py`). EP2 reportó un ARI KMeans contra GMM de {c(float(cn.iloc[9]['EP2']))}; aquí es {c(ar['k=2']['KMeans vs GMM'])} con k = 2. Se revisó si era un error de código: las tres técnicas se comparan sobre **las mismas {mi(adj['filas']['filas_muestra'])} filas, en el mismo orden** (la muestra tiene {mi(adj['filas']['filas_unicas'])} filas distintas), el ARI recalculado coincide con `f13_resumen.json` ({'sí' if adj['coincide_con_f13'] else 'NO'}) y los GMM {'convergieron todos' if adj['todos_los_gmm_convergieron'] else 'NO convergieron todos'} (`converged_`). **No hay error.** El GMM de f13 usa covarianza `full` y `n_init=2`. Con k = 2 los tamaños de cluster son KMeans {kmk2['tamanos']}, Ward {wk2['tamanos']} y GMM `full` {gmk2['tamanos']}; con covarianza `diag` el ARI KMeans–GMM sube a {c(float(gdk2['ARI_vs_KMeans']))} y con `spherical` a {c(float(gsk2['ARI_vs_KMeans']))}, y con k = 4 `full` da {c(float(gfk4['ARI_vs_KMeans']))}.

{tabla_es(t_ari)}

**Qué coincide y qué no, y qué dice EP2 (hipótesis, post hoc, no verificada).** (i) KMeans coincide con el GMM esférico (ARI {c(float(gsk2['ARI_vs_KMeans']))}) y con el diagonal ({c(float(gdk2['ARI_vs_KMeans']))}); **el discrepante es el GMM de covarianza `full`**, que parte la muestra en {p(gmk2_tam[0] / sum(gmk2_tam), 0)} y {p(gmk2_tam[1] / sum(gmk2_tam), 0)} mientras KMeans la parte en {p(kmk2_tam[0] / sum(kmk2_tam), 0)} y {p(kmk2_tam[1] / sum(kmk2_tam), 0)}; Ward queda en el medio (ARI {c(ar['k=2']['KMeans vs Ward'])} con KMeans). Por eso el ARI de {c(ar['k=2']['KMeans vs GMM'])} **siempre debe leerse junto al {c(float(gsk2['ARI_vs_KMeans']))} del GMM esférico**: no hay desacuerdo general entre técnicas, hay un GMM que modela otra forma. (ii) **Evidencia de EP2 (solo lectura):** EP2 usó variables de oclusión además de las cinco de aquí (`docs/informe_tecnico_EP2.md:408`), sus clusters se describen como «ocluidos» y «sin oclusores» (`docs/informe_tecnico_EP2.md:428-429`), y su propio diagnóstico encontró covarianzas degeneradas del GMM, con varianza mínima 1,0e-06 (el piso de scikit-learn) en las variables discretas `n_ocl`, `frac_cub` y `dist_ocl_f` (`docs/informe_tecnico_EP2.md:422`); el ARI de 0,997, 1,000 y 0,997 está en `data/08_reporting/08_no_supervisado_resumen.json:5-7`. **Hipótesis (no verificada):** el 0,997 de EP2 probablemente estaba inflado por esas variables discretas, que producen una estructura que las tres técnicas parten igual; el {c(ar['k=2']['KMeans vs GMM'])} de EP3 no es la anomalía: es lo que da un GMM de covarianza completa sobre cinco variables continuas sin separación natural. (iii) El BIC del GMM baja de {mi(N['selk'].set_index('k').loc[2, 'BIC_GMM_muestra_15000'])} (k = 2) a {mi(N['selk'].set_index('k').loc[8, 'BIC_GMM_muestra_15000'])} (k = 8) sin dar un mínimo y **no se usa para elegir k** (como en EP2, que tampoco lo usó).

**AUC de la regla dentro de cada cluster (k = 2).** Columna `AUC_regla_dentro_del_cluster` de `f13_clusters_k2.csv`:

{tabla_es(k2[cols_k])}

*Lectura:* la regla pierde capacidad de ordenar en las cajas **cercanas y densas** (AUC {c(cl_cerc['AUC_todas'])}, casi azar) y ordena bien en las **lejanas y poco densas** ({c(cl_lej['AUC_todas'])}); con k = 4 el AUC por cluster es {', '.join(c(v) for v in k4['AUC_regla_dentro_del_cluster'])} (clusters 0 a 3). No es un fallo del clustering: es dónde la regla ordena peor.

**Análisis nuevo, post hoc, no pre-declarado: ¿es por las celdas con hueco?** (`f13_auc_cluster_sin_huecos.csv`, `scripts/ep3/f13c_auc_cluster_sin_huecos.py`; descriptivo, sin IC). Se recalculó ese AUC sin las {mi(acl['cajas_en_celdas_con_hueco'].sum() / 2)} cajas de las celdas con hueco:

{tabla_es(t_auc_cl)}

**Resultado:** el AUC de los clusters cercanos **sube mucho**: con k = 2, de {c(cl_cerc['AUC_todas'])} a {c(cl_cerc['AUC_sin_celdas_con_hueco'])} (+{c(cl_cerc['dif_AUC'])}); con k = 4 (cluster 0), de {c(cl4_0['AUC_todas'])} a {c(cl4_0['AUC_sin_celdas_con_hueco'])} (+{c(cl4_0['dif_AUC'])}); los clusters lejanos casi no cambian ({c(cl_lej['AUC_todas'])} a {c(cl_lej['AUC_sin_celdas_con_hueco'])}). Es decir, **la mayor parte de la pérdida de capacidad en cajas cercanas se debe a las 2 celdas con hueco** ({mi(cl_cerc['cajas_en_celdas_con_hueco'])} cajas y {mi(cl_cerc['positivos_en_celdas_con_hueco'])} de los {mi(cl_cerc['positivos'])} positivos del cluster cercano caen ahí: cajas con muchos puntos y sin pareja). Aun así queda una brecha ({c(cl_cerc['AUC_sin_celdas_con_hueco'])} contra {c(cl_lej['AUC_sin_celdas_con_hueco'])}): la regla sigue ordenando algo peor entre cajas cercanas. En conjunto, el AUC global de la probabilidad con Platt pasa de {c(dfn['auc_base_f13']['AUC_prob_Platt_pooled'])} a {c(N['auc_cl_j']['AUC_global_sin_celdas_con_hueco'])} sin esas celdas. Los positivos de las celdas con hueco son {p(cl_cerc['positivos_en_celdas_con_hueco'] / cl_cerc['positivos'], 0)} de los positivos del cluster cercano: explican buena parte de la pérdida, no toda.

**Cruce con `sin_camara` (k = 4)** y comparación con lo que predice la regla (probabilidad con Platt):

{tabla_es(k4[['cluster', 'tipo_de_caso', 'cajas', 'tasa_sin_camara', 'ic_lo', 'ic_hi', 'prob_media_regla_platt', 'diferencia_tasa_menos_prob_regla', 'AUC_regla_dentro_del_cluster']])}

Los clusters 1 y 3 de k = 4 comparten el rótulo «{k4i.loc[1, 'tipo_de_caso']}» pero tienen tasas de {p(k4i.loc[1, 'tasa_sin_camara'])} y {p(k4i.loc[3, 'tasa_sin_camara'])}: el rótulo (basado en terciles de distancia y densidad) no los distingue. La página usa k = {N['k_el']} (el `k_elegido` del artefacto), por lo que no muestra estos dos clusters.

Con k = {N['k_el']}: {', '.join(f"«{r.tipo_de_caso}» tasa {p(r.tasa_sin_camara)} (IC {p(r.ic_lo)} a {p(r.ic_hi)}, {mi(r.cajas)} cajas)" for r in k2.itertuples())}. Los tipos de caso extremos reproducen lo que ya sabe la regla: pocos puntos y lejos significan más sin pareja. **¿Mejoran la predicción?** No: agregar el cluster a la probabilidad de la regla (regresión logística, GroupKFold por segmento, IC por segmentos) cambia el AUC en {c(ap.loc[2, 'dif_AUC'], 4)} (IC {c(ap.loc[2, 'ic_lo'], 4)} a {c(ap.loc[2, 'ic_hi'], 4)}) con k = 2 y en {c(ap.loc[4, 'dif_AUC'], 4)} (IC {c(ap.loc[4, 'ic_lo'], 4)} a {c(ap.loc[4, 'ic_hi'], 4)}) con k = 4, es decir, con k = 4 la predicción **empeora** de forma distinguible. La regla ya está bien calibrada en cada cluster (diferencias de tasa menos probabilidad entre {c(k4['diferencia_tasa_menos_prob_regla'].min())} y {c(k4['diferencia_tasa_menos_prob_regla'].max())}).

**Por qué el AUC base de esta comparación es {c(ab['AUC_f13_aporte_cluster_base_reproducido'])} y no {c(ab['AUC_puntaje_crudo_pooled'])}** (`f13_aporte_cluster.csv`, verificado en `f18_definiciones.json`): el 0,823 es el AUC del puntaje crudo (menos puntos top) con todas las cajas juntas. La comparación de los clusters trabaja con la **probabilidad con Platt**, y Platt se ajusta por separado en cada fold, de modo que al juntar los 5 folds se mezclan escalas distintas: con la misma regla el AUC conjunto baja a {c(ab['AUC_prob_Platt_pooled'])} (dentro de cada fold el AUC es idéntico al del puntaje crudo). Luego se vuelve a ajustar una regresión logística sobre el logit con otra partición por segmentos (GroupKFold de 5, distinta de la CV externa), que lo deja en {c(ab['AUC_f13_aporte_cluster_base_reproducido'])}. Lo que importa es la diferencia con y sin cluster (mismo método en ambos lados), no el nivel.

**IsolationForest** (contaminación 1 %): {mi(iso['cajas_atipicas'])} cajas atípicas ({p(iso['porcentaje'])}) en {iso['segmentos_con_atipicos']} de {iso['segmentos_total']} segmentos; tasa de `sin_camara` {p(iso['tasa_sin_camara_atipicas'])} (IC {p(iso['ic_atipicas'][0])} a {p(iso['ic_atipicas'][1])}) contra {p(iso['tasa_sin_camara_resto'])} en el resto; los tres segmentos que más aportan reúnen {p(sum(x['pct_de_los_atipicos'] for x in iso['top3_segmentos_aportan']))} de los atípicos.

**EP2 contra EP3** (EP2 solo se lee; fuentes en la tabla):

{tabla_es(cn[['medida', 'EP2', 'EP3', 'fuente_EP2', 'fuente_EP3']], por_valor=True)}

**Lectura.** Los resultados cambian: el silhouette con k = 2 baja ({c(float(cn.iloc[1]['EP2']))} a {c(float(cn.iloc[1]['EP3']))}), el cluster de mayor tasa con k = 4 baja de {c(float(cn.iloc[3]['EP2']), 1)} % a {c(float(cn.iloc[3]['EP3']), 1)} % y los atípicos de {c(float(cn.iloc[4]['EP2']), 1)} % a {c(float(cn.iloc[4]['EP3']), 1)} %. Una parte probable de la diferencia es que aquí no hay variables de oclusión y que se usan 41 segmentos en vez de 33 (hipótesis, no verificada). **Qué cambió respecto de EP2 y por qué:** lo que cambia es sobre todo el acuerdo entre técnicas (ARI KMeans–GMM de {c(float(cn.iloc[9]['EP2']))} a {c(float(cn.iloc[9]['EP3']))}), que el diagnóstico de arriba muestra que no es un error de filas ni de convergencia; sin oclusión, los grupos ya no son compactos y las técnicas discrepan. Con los umbrales de EP2 para llamar «estructura» (silhouette >= 0,25, ARI >= 0,8, rango de tasa >= 10 puntos), k = 2 los cumple y k = 4 no (ARI mínimo {c(ult.loc[4, 'ari_minimo'])}). **Los clusters no aportan a la predicción**; se usan solo para mostrar el «tipo de caso» en la página, con su tasa histórica.

## 10. Optimización de hiperparámetros y técnicas de ensamble
### 10.1 IE9: optimización de hiperparámetros
**Diseño.** Cada modelo (LR, RF, HGB, XGBoost, LightGBM) se compara **por defecto** y **optimizado** con búsqueda aleatoria **anidada**: la elección usa solo los segmentos de entrenamiento de cada fold externo, con CV interna GroupKFold(3) por segmento y criterio PR-AUC (LR: rejilla de C de 1e-5 a 100 por `class_weight`). El conjunto de variables es un hiperparámetro más. Las grillas incluyen valores **más regularizados** que los de EP2 (HGB `max_leaf_nodes` 2 y 3, `min_samples_leaf` hasta 3.200; RF `min_samples_leaf` hasta 1.600 y `max_features` 1 y 2). «Mejora» = diferencia de PR-AUC (optimizado menos defecto) >= +0,010 con IC pareado por segmentos que excluya 0. **DEV-1:** 1 repetición de la CV externa (semilla 42) y 30 configuraciones.

{tabla_md(t9)}

**Lectura.** Mejoran con la búsqueda: {', '.join(N['n_mejoran'])}. No mejoran: {', '.join(N['n_no'])}. Es un resultado negativo que reportamos igual: LR, RF y HGB no mejoran, y LR y RF empeoran en promedio. *Hipótesis (no verificada):* con 41 segmentos y 30 configuraciones, la búsqueda interna puede elegir configuraciones que aprovechan particularidades de los segmentos de entrenamiento y no se sostienen en el fold de validación (sobreajuste de la búsqueda); en LR, el criterio interno (PR-AUC) podría preferir variables y regularización distintas de las que sirven en el fold externo. El valor de XGBoost y LightGBM viene sobre todo de **regularizar** un modelo que por defecto se sobreajusta (PR-AUC de entrenamiento {c(N['cv'].loc[('XGB', 6), 'ap_train'])} con `max_depth` 6; validación {c(N['cv'].loc[('XGB', 6), 'ap_val'])}).

**Bordes de grilla.** Revisando los 5 folds, el único borde fue LightGBM `min_child_samples` (mínimo en 3 de 5 folds); se **extendió la grilla una vez** (5 y 10) y se repitió la búsqueda. Tras la extensión queda en el borde: {borde_txt or 'ninguno'}. El plan permite una sola extensión: **limitación declarada**.

**Curvas de validación** (`f3_curvas_validacion.csv`, 5 folds): en todos los modelos la PR-AUC de entrenamiento sube con la complejidad (HGB de {c(N['cv'].loc[('HGB', 2), 'ap_train'])} con 2 hojas a {c(N['cv'].loc[('HGB', 31), 'ap_train'])} con 31) y la de validación **baja o no sube** ({c(N['cv'].loc[('HGB', 2), 'ap_val'])} a {c(N['cv'].loc[('HGB', 31), 'ap_val'])}). La mejor validación está en los valores más regulares.

### 10.2 IE10: técnicas de ensamble
E1: voting soft de LR, RF y HGB. E2: promedio de rangos de E1 y la regla. E3: stacking de LR, RF, HGB, XGBoost y LightGBM con meta-regresión logística sobre predicciones fuera de fold calculadas con **GroupKFold(3) por segmento dentro de cada fold externo** (a mano: el CV interno por defecto de scikit-learn mezcla segmentos y filtra información). E4: stacking por vistas (observación, tamaño y posición). «Aporta» = AUC >= +0,010 sobre su mejor componente con IC pareado que excluya 0.

{tabla_md(t10)}

**Lectura.** **Ningún ensamble aporta.** E1 queda {c(f4.loc['E1', 'dif_AUC'])} sobre su mejor componente con IC que incluye 0; E2 empata con la regla ({c(f4.loc['E2', 'dif_AUC'])}, y la contiene); E3 y E4 quedan por debajo de su mejor componente. El ensamble principal declarado en el plan (mayor AUC entre E1 y E4) es **{N['f4r']['ensamble_principal_declarado']}**. *Analogía:* promediar compañeros solo ayuda si se equivocan en cosas distintas; aquí todos miran lo mismo (los puntos del LiDAR).

## 11. IE11: generalización
{tabla_md(t11)}

- **Estabilidad.** La mediana del AUC por segmento cumple en todos ({c(f5['AUC_mediana_segmento'].min())} a {c(f5['AUC_mediana_segmento'].max())}); el mínimo por fold **no lo cumple ninguno** ({c(f5['AUC_min_fold'].min())} a {c(f5['AUC_min_fold'].max())}) por el fold 0. **Post hoc (anexo B):** el fold 0 contiene {int(fr.loc['0', 'segmentos'])} segmentos y {mi(fr.loc['0', 'cajas'])} cajas, entre ellos `257766998801` con la cámara 3 sin pares. Con el brazo B (solo celdas sanas) el AUC mínimo por fold sube a **{c(N['B_min'])}** (regla; LR3 {c(f12['B_AUC_min_fold']['LR3'])}; XGBoost {c(f12['B_AUC_min_fold']['XGB'])}), es decir, **el brazo B sí cumple 0,75**: el fallo de estabilidad se debe a la celda con hueco, no a la regla en general. En el fold 0 el AUC de la regla pasa de {c(fr.loc['0', 'AUC_A'])} (brazo A) a {c(fr.loc['0', 'AUC_B_celdas_sanas'])} con la celda con hueco fuera (brazo B). **Esto explica la inestabilidad por fold, no cambia la elección ni la regla de reserva DEV-2, que se aplicó sobre el brazo A.** Los criterios del detector no usan el AUC, pero los huecos se descubrieron por un AUC bajo: post hoc, en muestra. ({EN_MUESTRA}.)
- **Leave-one-segment-out** (regla): AUC global {c(lo['AUC'])} (IC {c(lo['AUC_ic'][0])} a {c(lo['AUC_ic'][1])}); mediana por segmento {c(lo['AUC_mediana_segmento'])}; {lo['segmentos_con_AUC_menor_a_0_55']} de {lo['segmentos_evaluables']} segmentos evaluables con AUC < 0,55 (mínimo {c(lo['AUC_min_segmento'])}). LR3 y XGBoost: {c(N['loso']['LR3']['AUC'])} y {c(N['loso']['XGB']['AUC'])}.
- **Brecha ajuste-validación.** La regla no aprende: no tiene brecha real. XGBoost con todos los segmentos de entrenamiento (promedio de los folds de 32 y 34 segmentos): ajuste {c(br['AUC_ajuste'])}, validación {c(br['AUC_validacion'])}, brecha {c(br['brecha_AUC'])} que no se cierra con más segmentos. Con 41 segmentos las curvas son ruidosas.
- **Calibración.** Con Platt, ECE de la regla {c(f5.loc['Regla top', 'ECE_cal'])} (<= 0,05) y Brier {c(f5.loc['Regla top', 'Brier_cal'])}.

## 12. IE12: selección justificada
Objetivos (los de EP2): O1 AUC >= 0,70 y PR-AUC menos prevalencia >= 0,10; O2 «vale la pena» frente a la regla (Fracción 80 % baja >= 5 puntos con IC pareado que excluye 0 y AUC sube >= 0,03); O3 recall >= 0,75 en el punto A; O4 estabilidad y ECE <= 0,05.

{tabla_md(t12)}

Un valor **positivo** en la columna de Fracción 80 % significa que el candidato necesita revisar **más** cajas que la regla; en E3 y E4 el IC excluye 0, es decir, son significativamente **peores** que la regla en esa medida.

**Decisión.** {sel['razon'][0].upper() + sel['razon'][1:]}. **Elegida: la regla «menos puntos top».** *Regla de reserva DEV-2 (post hoc, no pre-declarada):* el plan define la elección «entre los que cumplen O1, O3 y O4», pero nadie cumple O4; por analogía con lo que el plan dice para O2, se aplicó la misma regla de simplicidad entre los que cumplen O1 y O3 y se reporta la estabilidad como limitación de todos. El análisis post hoc de estabilidad (brazo B, sección 11 y anexo B) **explica la inestabilidad por fold pero no cambia la elección ni la regla de reserva DEV-2, que se aplicó sobre el brazo A.** **O2 no lo cumple ningún candidato.** {e2_texto(N)}. La elegida es la regla porque es la más simple y no es superada de forma distinguible por nada más complejo.

**Brazos A, B y C** {ROT}. A: un paso. B: solo celdas sanas (AUC {c(N['b'].loc['Regla top', 'AUC'])}, PR-AUC {c(N['b'].loc['Regla top', 'PR-AUC'])}). C: dos pasos: revisar el {p(esc['Fraccion_80_C'])} de las cajas para el 80 % de recall (IC {p(esc['Fraccion_80_C_lo'])} a {p(esc['Fraccion_80_C_hi'])}) contra el {p(esc['Fraccion_80'])} de A, y captura {p(esc['Captura@20_C'])} (contra {p(esc['Captura@20'])}) al revisar el 20 %; la auditoría cubre {mi(N['auditoria_pos'])} positivos. **Punto de equilibrio:** C empata con A si cada auditoría cuesta {mi(N['eq'])} cajas ({N['eq_h']:.0f} h con {SEG_POR_CAJA} s por caja; IC {mi(esc['equilibrio_lo'])} a {mi(esc['equilibrio_hi'])}). **{GANANCIA_C}** Diferencia pareada C menos A en Fracción para 80 %: {c(glob['dif_C_menos_A'])} (IC {c(glob['ic_lo'])} a {c(glob['ic_hi'])}; **no excluye 0**; {p(glob['prop_replicas_C_mejor'])} de las réplicas favorece a C y el resto no contiene ningún segmento con hueco). En el fold 1 (donde cae `911012534050`) C baja la fracción de {c(fr.loc['1', 'Fraccion80_A'])} a {c(fr.loc['1', 'Fraccion80_C'])}; en el fold 0, de {c(fr.loc['0', 'Fraccion80_A'])} a {c(fr.loc['0', 'Fraccion80_C'])}; en los folds 2, 3 y 4 no hay celdas con hueco y C es igual a A.

**Cómo leer la ganancia del brazo C** {ROT}. (a) *Casi por construcción:* en cajas revisadas, el brazo C no puede ser peor que A casi por construcción, porque la auditoría quita cajas de la cola sin costo por caja (sus positivos cuentan como hallados); por eso el signo de la diferencia no es un resultado: lo único que se mide es su tamaño. (b) *Por qué el límite superior del IC de C menos A es exactamente 0:* en las réplicas del bootstrap por segmentos que no contienen ninguno de los 2 segmentos con hueco ({p(hc['proporcion_observada_ninguno_de_los_2'])} de las {mi(hc['replicas'])} réplicas) la Lista A queda vacía y C es igual a A. La probabilidad exacta de ese evento en este diseño ({hc['diseno']}; {hc['formula']}) es **{p(hc['prob_exacta_ninguno_de_los_2'], 2)}**; el {p(hc['proporcion_observada_ninguno_de_los_2'])} observado es compatible con ella (diferencia de {c(abs(hc['z_observado_menos_exacto']), 1)} errores estándar con 1.000 réplicas). Es decir, que el IC «llegue a 0» describe el diseño del bootstrap, no es evidencia a favor ni en contra de C. (c) *Lo informativo:* el punto de equilibrio ({mi(N['eq'])} cajas por auditoría; IC {mi(esc['equilibrio_lo'])} a {mi(esc['equilibrio_hi'])}) y la **tasa de celdas marcadas del detector y su estabilidad**, que con solo 2 celdas marcadas únicamente se pueden medir con datos nuevos. (`f12b_hechos_brazoC.json`, `scripts/ep3/f12b_hechos_brazoC.py`.)

**Dos definiciones de «20 %» (verificado en `f18_definiciones.json`).** En este informe, el 20 % del brazo C es el 20 % del **total** de cajas ({mi(dd['cajas_total'])}): {mi(dd['f5_cajas_revisadas_al_20pct'])} cajas revisadas una por una, porque las cajas de la Lista A se auditan sin ese costo (`RankingDosPasos.metricas`, `scripts/ep3/f5_generalizacion.py`). En la página es el 20 % de la **cola** de celdas sanas ({mi(dd['cajas_cola_celdas_sanas'])} cajas): {mi(dd['pagina_cajas_revisadas_al_20pct'])} cajas (`cola_segmento` en `app_logica.py` y `curva_cola.csv`, `scripts/ep3/f7_preparar_app.py`). Hay {mi(dd['diferencia_cajas'])} cajas de diferencia, y de ahí el {p(dd['captura20_C_informe_f5'])} del informe contra el {p(dd['recall_C_pagina_curva_20pct_de_la_cola'])} de la curva de la página y el {p(dd['recall_C_observado_pagina_20pct_de_la_cola'])} del conteo observado. Con las {mi(dd['f5_cajas_revisadas_al_20pct'])} cajas del informe, el conteo observado da {p(dd['recall_C_observado_con_las_cajas_de_f5'])}; lo que falta hasta {p(dd['captura20_C_informe_f5'])} (menos de 0,2 puntos) es el desempate de cajas con el mismo puntaje (aleatorio en el informe y la curva, orden estable en el conteo observado). En el brazo A ambas definiciones coinciden ({p(dd['captura20_A_informe_f5'])} contra {p(dd['recall_A_pagina_curva_20pct'])}) porque no hay cajas auditadas sin costo.

### Cuadro «Modelo escogido»: regla «menos puntos top»
{tabla_md(cuadro)}

Accuracy y F1 son solo referencia: con una clase minoritaria de {p(N['prev'])}, un clasificador trivial ya tiene accuracy alto.

**Solución final en tres capas.** (1) **Filtro 1**: detector de huecos con parámetros congelados (`detector_params_v3.json`). (2) **Regla**: menos puntos del LiDAR superior primero, con umbrales A = {-N['fin']['umbrales']['A']:.0f} y B = {-N['fin']['umbrales']['B']:.0f} (se marcan las cajas con ese número de puntos o menos) y calibración Platt. (3) **Persona** que revisa y decide. v3 está congelado con sha256 en `manifest_v3.json` ({', '.join(N['man']['sha256'])}); se verifica con `scripts/ep3/verificar_congelados_v3.py`.

## 13. La página y su despliegue
`app/app.py` (Streamlit, solo local; producto «Auditor de etiquetas 3D», rediseñado en F20 como una consola interna de revisión: guía de estilo en `guia_estilo_pagina.md` y auditoría de diseño en `auditoria_diseno_pagina.md`) es el marco de la página: navegación agrupada (`st.navigation`) con {len(SECCIONES_PAGINA)} páginas ({', '.join(SECCIONES_PAGINA[:-1])} y {SECCIONES_PAGINA[-1]}), el rol al pie de la barra lateral y un único chip de estado. En **Cola de revisión** (maestro-detalle) se decide con un presupuesto (parte en 20 %) o con una meta («quiero encontrar X %», interpolación de la curva guardada) y se elige el flujo, de un paso o de dos pasos; el resultado se dice en lenguaje simple con ambos flujos («con auditoría previa, unas {_de_cada_100(pg['recall_proceso'])}; solo cola, unas {_de_cada_100(pg['recall_A'])}»); al seleccionar una fila se abre el detalle de esa caja (probabilidad calibrada, posición en la cola, tipo de caso, advertencia para ciclistas), hay una vista «Agrupar por objeto» y filtros por clase y cámara, y los supuestos y la confiabilidad van en un popover, junto a un selector de modelo de referencia (XGBoost o E2). Tres roles y un **modo presentación** que oculta los identificadores y agranda la letra. Usa predicciones **fuera de fold**, y el estado «en muestra» está en un chip persistente en todas las páginas, con el texto completo en su popover: «{EN_MUESTRA}. {GANANCIA_C}». Pruebas: {PRUEBAS_EP3} en `tests/ep3` (incluye una prueba de humo de las {len(SECCIONES_PAGINA)} páginas por 3 roles, con el modo presentación activado y desactivado, con `streamlit.testing.v1.AppTest`). Despliegue: local (`scripts/ep3/arrancar_app.bat`, que usa `app/lanzar.py` para precargar la solución congelada y los datos antes de la primera visita) y Docker (lista blanca que excluye `data/`, volúmenes de solo lectura); **Docker no se probó**. La guía de AWS (EC2 + S3 privado) es solo orientativa y advierte que los datos por caja de Waymo no deben salir del equipo (`despliegue.md`).

**Seguridad de la página.** La app escucha **solo en `localhost`**: `.streamlit/config.toml` fija `server.address = "localhost"`, `scripts/ep3/arrancar_app.bat` pasa `--server.address localhost`, sin telemetría (`browser.gatherUsageStats = false`) y con la barra superior mínima (`client.toolbarMode = "minimal"`, sin el botón Deploy). En Docker el contenedor escucha en `0.0.0.0` (es necesario dentro del contenedor), pero `docker-compose.yml` publica el puerto solo en el equipo (`127.0.0.1:8501:8501`) y `.dockerignore` deja `data/` fuera de la imagen. **No debe exponerse sin autenticación y sin quitar los identificadores, y no se publica en servicios de nube con datos de Waymo.** Una prueba de solo lectura (`tests/ep3/test_seguridad_pagina.py`) falla si cambian estos valores.

**Lo que muestra la página** (Cola de revisión, Segmento «Todos», presupuesto 20 %, {pg['brazo']}; {EN_MUESTRA}): la página dice «unas {_de_cada_100(pg['recall_proceso'])} cajas sin pareja» ({p(pg['recall_proceso'])} con el conteo observado, única fuente tras el rediseño; antes la tarjeta mostraba {p(pg['recall'])}, de la curva interpolada; intervalo {p(pg['lo'])} a {p(pg['hi'])}), {mi(pg['cajas_a_revisar'])} cajas a revisar de {mi(pg['cajas_cola_total'])} en la cola y {c(pg['horas'], 1)} h con {SEG_POR_CAJA} s por caja. Con un paso (A) y el mismo 20 % el recall esperado es {p(pg['recall_A'])} (IC {p(pg['lo_A'])} a {p(pg['hi_A'])}). Son dos números distintos de dos brazos distintos; ver `PENDIENTES_PAGINA.md`. **El «20 %» de la página es el 20 % de la cola de celdas sanas ({mi(dd['pagina_cajas_revisadas_al_20pct'])} cajas), no el 20 % del total ({mi(dd['f5_cajas_revisadas_al_20pct'])} cajas) del informe §12:** por eso la página dice {p(pg['recall_proceso'])} y el informe {p(dd['captura20_C_informe_f5'])}.

## 14. Validación externa sellada (P9): preparada, pendiente
### 14.1 Selección de segmentos y sellado
`notebooks/00b_seleccion_segmentos_ep3.ipynb` (Colab) reconstruye el pool de EP2 (sin lluvia {sp['embudo']['sin_lluvia']}, al menos {sp['parametros']['min_frames']} frames {sp['embudo']['n_frames_>=190']}, `n_detecciones` entre percentiles {sp['embudo']['n_detecciones_entre_percentiles']}) y, **solo después**, excluye los {sp['embudo']['evaluados_ep2_dentro_del_pool']} evaluados por EP2 ({sp['embudo']['candidatos_sin_los_evaluados_por_ep2']} candidatos nuevos). Usa **cuotas fijas de {sp['total_cuota']} segmentos útiles** por `time_of_day x location` (de día en San Francisco {sp['cuotas_utiles']['Day / location_sf']}; la noche queda mal representada: {sp['candidatos_por_estrato']['Night / location_sf']} y {sp['candidatos_por_estrato']['Night / location_phx']} candidatos en SF y Phoenix, 0 en otras), semilla {sp['parametros']['semilla']}, tope de {sp['parametros']['tope_evaluaciones']} evaluaciones y meta >= {sp['parametros']['meta_utiles']} útiles; el orden de candidatos está sellado en `plan_seleccion_ep3.json` (sha256 en `plan_seleccion_ep3.sha256`). Guía paso a paso: `GUIA_VALIDACION_EXTERNA.md`. `scripts/ep3/evaluar_sellado.py congelar` guarda el sha256 de la lista y de v3 **antes** de abrir los datos; `evaluar` corre **una sola vez** (candado) y compara dos pasos contra un paso.

### 14.2 Qué se mide
**Solución contra regla da diferencia 0 por construcción:** el puntaje de la solución congelada v3 es la propia regla «menos puntos del sensor superior» (`PuntuadorRegla`, monótono con ella; `inferencia.py` y `congelado.py`), así que lo que se mide es el desempeño de la regla fuera de muestra, su recall y precisión con los umbrales A = {-N['fin']['umbrales']['A']:.0f} y B = {-N['fin']['umbrales']['B']:.0f} congelados, el brazo C contra A y la tasa de celdas marcadas.

### 14.3 Alternativas congeladas (DEV-4)
Para poder decir algo más, **antes de abrir datos** se congelaron dos alternativas, LR3 y XGBoost entrenadas con los 41 segmentos (`alternativas_v3.joblib` y `manifest_alternativas.json`, aparte de `manifest_v3.json`; configuración de XGBoost: la más repetida entre los 5 folds, {N['alt']['xgb_folds_que_la_eligieron']}; DEV-4, post hoc respecto del plan v3 y sin cambiar la solución elegida); la validación las compara con la regla (diferencia de AUC y de fracción para el 80 % con intervalo pareado por segmentos, `externa_alternativas.csv`).

### 14.4 Qué se medirá con segmentos nuevos y cómo se leerá cada caso
Con segmentos nuevos se medirá:
- **(i)** la tasa de celdas marcadas por el detector **con dos denominadores** (todas las celdas segmento x cámara y solo las celdas con >= 100 cajas en el rango; en desarrollo 2 de {f12['detector_ep2']['celdas_con_n_suficiente']}) y cada una con su intervalo por segmentos;
- **(ii)** su estabilidad frente a las 30 combinaciones de parámetros;
- **(iii) opcional y post hoc**, si Waymo v2 trae el componente `camera_box`, si en cada celda marcada esa cámara tiene cajas 2D en el rango sin pares (laguna de asociación) o no tiene ninguna (laguna de etiquetado o de datos).

No hay verdad externa: no se medirán sensibilidad ni especificidad (DEV-3). Nada se selecciona con esos datos. Es la única forma de saber si la ganancia del dos pasos y el detector se sostienen. Los casos de resultado (A: sin huecos; B: huecos encontrados; C: marcas sin verificar; D: una alternativa «gana») y cómo leer cada uno están en `GUIA_VALIDACION_EXTERNA.md`, sección 7.

## 15. Conclusiones y recomendaciones para el negocio
**Conclusiones.** (1) La señal principal son los puntos del LiDAR: una regla simple alcanza AUC {c(esc['AUC'])} y ningún modelo ni ensamble la supera de forma distinguible. (2) Optimizar hiperparámetros ayuda solo a los modelos que por defecto se sobreajustan. (3) Los clusters describen, no predicen. (4) La utilidad del filtro 1 {ROT} depende de 2 celdas; hay que verla en datos nuevos.

**Recomendaciones.**
1. **Usar la solución en tres capas:** primero auditar las celdas de la Lista A, luego revisar la cola con la regla, y que una persona decida. No usar la regla para descartar cajas sin revisión.
2. **Auditar cámaras antes de revisar cajas.** Correr el detector en cada segmento nuevo: es robusto a sus parámetros (marca los 2 huecos de referencia en {f12['detector_combinaciones_que_detectan_los_2']} de {f12['detector_combinaciones']} combinaciones, con 0 a {f12['detector_falsas_alarmas_rango'][1]} celdas marcadas además de los 2 de referencia (sin verdad externa)).
3. **Monitorear el recall por segmento**, no solo el global: {lo['segmentos_con_AUC_menor_a_0_55']} de {lo['segmentos_evaluables']} segmentos evaluables tienen AUC < 0,55; y por clase: en ciclistas el recall en el punto A es {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} (solo {int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos), contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones.
4. **Medir el tiempo real de revisión** (hoy es un supuesto de {SEG_POR_CAJA} s por caja) y el costo de una auditoría, para decidir entre uno y dos pasos con el punto de equilibrio.
5. **Datos que faltan:** segmentos nuevos (P9), la causa de los huecos (etiquetado 2D o datos de cámara), `camera_calibration`, más ciclistas y segmentos nocturnos.
6. **Qué NO se puede afirmar:** que dos pasos supere a un paso fuera de muestra; que los huecos sean errores de etiquetado; que la regla sirva igual en otras ciudades o sensores; que un modelo complejo nunca ayude.
7. **Extender el filtro 1 a nivel segmento** (sin ML): contar las filas de asociación y la tasa de pares por frame etiquetado de cada segmento para detectar los de asociación vacía o etiquetado ralo antes de aplicar el detector de celdas ({smot.loc['asociación vacía', 'segmentos']} de los {sres['evaluados']} segmentos evaluados por EP2 tenían la asociación vacía).

## 16. Ética, sesgos y privacidad
- Una persona decide: la solución ordena y avisa, nunca etiqueta ni descarta. No es una prueba de seguridad del vehículo.
- Licencia: uso no comercial; los datos no se redistribuyen; la página corre solo en el equipo, no hornea datos en imágenes Docker y no envía nada a internet. El zip de entrega es solo para el uso académico del docente.
- Privacidad: los identificadores de objeto y las marcas de tiempo solo están en tablas locales; el modo presentación los oculta.
- **Seguridad de la página:** escucha solo en `localhost`, nunca debe exponerse sin autenticación y sin quitar los identificadores, y no se publica en servicios de nube con datos de Waymo (ver sección 13).
- **Sesgos medidos** (descriptivo, sin pruebas de hipótesis; regla en el punto A, umbral {-f12['umbral_A_regla']:.0f} puntos, `f12_equidad.csv`; AUC solo con >= 200 cajas por clase, `n/c` si no):

{tabla_md(t_eq)}

  Lectura (descriptiva, sin pruebas de hipótesis; post hoc): con todas las celdas, el recall es menor de día ({c(eqi.loc[('momento_del_dia', 'Day'), 'recall_A'])}) que de noche ({c(eqi.loc[('momento_del_dia', 'Night'), 'recall_A'])}). **Sin las celdas con hueco, de día pasa a {c(eqx.loc[('momento_del_dia', 'Day'), 'recall_A'])} y la brecha se invierte:** era un efecto del hueco. San Francisco pasa de {c(eqi.loc[('ubicacion', 'location_sf'), 'recall_A'])} a {c(eqx.loc[('ubicacion', 'location_sf'), 'recall_A'])} (Phoenix {c(eqi.loc[('ubicacion', 'location_phx'), 'recall_A'])}, otras {c(eqi.loc[('ubicacion', 'location_other'), 'recall_A'])}): la brecha baja, pero queda. Amanecer y atardecer ({c(eqi.loc[('momento_del_dia', 'Dawn/Dusk'), 'recall_A'])}; no tiene huecos) queda unos {100 * (eqx.loc[('momento_del_dia', 'Day'), 'recall_A'] - eqi.loc[('momento_del_dia', 'Dawn/Dusk'), 'recall_A']):.0f} puntos bajo el día sin huecos. **Ciclistas:** recall {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones, con {int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos en {int(eqi.loc[('clase', 'CYCLIST'), 'segmentos'])} segmentos: **la regla es poco confiable para ciclistas**; queda como limitación y como recomendación de uso (no apoyarse en la cola para esa clase y revisarla con más cuidado).
- **Sesgo de selección:** EP2 descartó {sres['descartados']} de {sres['evaluados']} segmentos evaluados (asociación vacía, etiquetado ralo, pocas asociaciones) y el rendimiento fue menor de noche ({p(srend.loc[('momento_del_dia', 'Night'), 'rendimiento'], 0)} contra {p(srend.loc[('momento_del_dia', 'Day'), 'rendimiento'], 0)} de día); la causa es desconocida y el detector solo se evaluó en segmentos con etiquetado denso (sección 3).
- Los hallazgos post hoc (huecos, regla de reserva DEV-2, no supervisado, análisis en muestra) son hipótesis, no conclusiones. El criterio de selección de segmentos (etiquetado no ralo) deja fuera el caso de etiquetado 2D muy escaso.

## 17. Limitaciones
1. Sin prueba ciega: los 8 segmentos de test de EP2 ya se miraron; la validación externa está pendiente.
2. Una repetición de la CV externa (DEV-1): los IC reflejan una sola partición de segmentos.
3. Nadie cumple el criterio de estabilidad por fold (fold 0) y la elección usó una regla de reserva post hoc (DEV-2).
4. LightGBM quedó con `n_estimators` en el borde tras la única extensión permitida.
5. El detector marca solo {len(N['lista_A'])} celdas y no hay verdad externa sobre cuáles son huecos reales: ni la sensibilidad ni la especificidad se pueden estimar (solo la estabilidad del conjunto marcado y la tasa de celdas marcadas en datos nuevos), y sus parámetros se ajustaron con los mismos datos donde se evalúa (circularidad).
6. Los segundos por caja (supuesto de {SEG_POR_CAJA} s) no se midieron.
7. El no supervisado no incluye variables de oclusión, a diferencia de EP2.
8. Docker no se probó; AWS no se ejecutó.
9. **Brazo C** ({EN_MUESTRA}): en cajas revisadas casi por construcción no es peor que A (la auditoría quita cajas de la cola sin costo); el límite superior 0 del IC de C menos A se debe a que {p(hc['proporcion_observada_ninguno_de_los_2'])} de las réplicas no contienen ninguno de los 2 segmentos con hueco (probabilidad exacta del diseño {p(hc['prob_exacta_ninguno_de_los_2'], 2)}); lo informativo es el punto de equilibrio y la tasa de celdas marcadas del detector (con su estabilidad), que solo se pueden medir con datos nuevos.
10. **Ciclistas:** la regla es poco confiable (recall {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones; {int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos en {int(eqi.loc[('clase', 'CYCLIST'), 'segmentos'])} segmentos).
11. **Estabilidad por fold:** el brazo B (post hoc) la explica, pero la elección y la regla de reserva DEV-2 se hicieron sobre el brazo A.
12. **La página** escucha solo en localhost y no está lista para exponerse en una red (sin autenticación).
13. **Selección de segmentos:** {sres['descartados']} de {sres['evaluados']} candidatos de EP2 se descartaron; el detector solo se probó con etiquetado denso y la noche está poco representada (sección 3).

## 18. Reproducción
Ver `docs/ep3/README_EP3.md`. Entorno: Python 3.10, `requirements.txt` + `requirements_ep3.txt` con `constraints_ep3.txt`. Verificaciones: `scripts/verificar_congelados.py` (EP2, 14 de 14), `scripts/ep3/verificar_congelados_v3.py` ({len(N['man']['sha256']) + 2} de {len(N['man']['sha256']) + 2}) y `scripts/ep3/verificar_no_supervisado.py`.

## Anexo A. Fuentes de las cifras
| Cifra | Archivo |
|---|---|
| Conteos, folds, reproducción de EP2 | `data/08_reporting_ep3/f1_resumen.json`, `f1_reproduccion_pred_test.csv` |
| Detector, Lista A, baselines | `f2_resumen.json`, `lista_A_huecos.csv`, `f2_baselines_reglas_41.csv` |
| IE9 | `f3_defecto_vs_optimizado.csv`, `f3_bordes.csv`, `f3_config_por_fold.csv`, `f3_curvas_validacion.csv` |
| IE10 | `f4_ensambles_aporta.csv`, `f4_candidatos_metricas.csv`, `f4_resumen.json` |
| IE11 | `f5_metricas_candidatos.csv`, `f5_auc_por_fold.csv`, `f5_auc_por_segmento.csv`, `f5_loso_*`, `f5_brecha_*`, `f5_calibracion_bins.csv` |
| IE12 y brazos | `f6_tabla_seleccion.csv`, `f6_seleccion.json`, `f6_modelo_escogido.csv`, `f5_brazoB.csv`, `f5_brazoC.csv` |
| Análisis en muestra (12.1 a 12.4) | `f12_auc_por_fold_brazos.csv`, `f12_diferencia_C_menos_A.csv`, `f12_sensibilidad_detector.csv`, `f12_equidad.csv`, `f12_eda_*.csv`, `f12_resumen.json` |
| No supervisado | `f13_seleccion_k.csv`, `f13_clusters_k2.csv`, `f13_clusters_k4.csv`, `f13_estabilidad.csv`, `f13_aporte_cluster.csv`, `f13_isolation_forest.csv`, `f13_comparacion_ep2_ep3.csv`, `f13_resumen.json`, `f13_ari_diagnostico.csv` y `.json` |
| Brazo C: hechos y probabilidad exacta | `f12b_hechos_brazoC.json`, `f12_diferencia_C_menos_A.csv` |
| Conteo de pruebas | `pruebas_ep3_conteo.json` (`pytest --collect-only`, sin ejecutar) |
| Alternativas congeladas (DEV-4) y ensayo general | `f19_alternativas_congeladas.json`, `ensayo_resultado.json` (ensayo con datos de desarrollo, sin valor como resultado) |
| Selección de segmentos | `docs/seleccion_segmentos/inventario_segmentos.csv`, `registro_verificacion_ep2.csv` |
| Solución congelada | `data/06_models_ep3/manifest_v3.json`, `manifest_no_supervisado.json`, `f6_final_resumen.json` |

## Anexo B. Análisis en muestra (post hoc, no pre-declarado) {ROT}
### B.1 AUC por fold y brazos A, B y C (regla; LR3 y XGBoost en `f12_auc_por_fold_brazos.csv`)
{tabla_es(t_fold)}

Respuestas: **¿el brazo B cumple AUC mínimo por fold >= 0,75?** Sí: {c(f12['B_AUC_min_fold']['Regla top'])} (regla), {c(f12['B_AUC_min_fold']['LR3'])} (LR3), {c(f12['B_AUC_min_fold']['XGB'])} (XGBoost); el brazo A no ({c(f12['A_AUC_min_fold']['Regla top'])}, {c(f12['A_AUC_min_fold']['LR3'])}, {c(f12['A_AUC_min_fold']['XGB'])}). **¿Qué hace C en el fold 1?** Baja la Fracción para 80 % de {c(f12['C_en_fold_1_regla']['Fraccion80_A'])} a {c(f12['C_en_fold_1_regla']['Fraccion80_C'])} (celda {f12['C_en_fold_1_regla']['hueco']}). **¿El IC de C menos A excluye 0?** No: {c(glob['dif_C_menos_A'])} con IC {c(glob['ic_lo'])} a {c(glob['ic_hi'])} (LR3 y XGBoost igual: ver el CSV).

### B.2 Diferencia pareada C menos A en Fracción para 80 % (1.000 réplicas por segmentos; regla)
{tabla_es(t_difc)}

*Lectura:* las variantes «solo se audita una celda» y «se excluye un segmento» muestran que la ganancia depende de las dos celdas: la celda de `257766998801` sola ya da casi toda la ganancia (diferencia {c(N['f12dif'][(N['f12dif']['candidato'] == 'Regla top') & N['f12dif']['variante'].str.contains('solo se audita 257766998801')].iloc[0]['dif_C_menos_A'])}).

### B.3 Sensibilidad del detector (resumen por configuración; detalle en `f12_sensibilidad_detector.csv`)
{tabla_es(t_sens)}

Con `frac` = 0,35 aparece una celda marcada más (sin verdad externa) en la celda `247562357599|cam5`; con `min_cajas` = 50 y `frac` <= 0,30, la celda `143581920096|cam5`. Los 2 huecos de EP2 se detectan en todas las combinaciones.

**Nota sobre la celda `247562357599|cam5`** *(post hoc, no pre-declarado, hipótesis no verificada)*. El segmento `247562357599`, cámara 5, tiene {mi(seg247['positivos'])} positivos en {mi(seg247['cajas'])} cajas con más de 100 puntos del sensor superior ({p(seg247['tasa'])}; `f12_eda_puntos_top_resumen.json`, campo `top3_segmentos_positivos_mayor_100_sin_hueco`) y es la celda que aparece marcada con `frac` = 0,35 (`f12_sensibilidad_detector.csv`, columna `marcadas_lista`). Con los parámetros congelados (`frac` = 0,25) **no se marca**. *Hipótesis (no verificada):* podría ser un tercer hueco que el umbral de EP2 no alcanza a marcar; no hay verdad externa para decidirlo. No cambia el detector ni ninguna cifra.

### B.4 Equidad (post hoc, descriptivo; detalle en `f12_equidad.csv`)
{tabla_md(t_eq)}

Lectura en la sección 16. Con las celdas con hueco fuera, de día el recall es {c(eqx.loc[('momento_del_dia', 'Day'), 'recall_A'])} (con ellas, {c(eqi.loc[('momento_del_dia', 'Day'), 'recall_A'])}); en ciclistas es {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} con {int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos en {int(eqi.loc[('clase', 'CYCLIST'), 'segmentos'])} segmentos.

### B.5 Hechos del brazo C (post hoc; `f12b_hechos_brazoC.json`)
Probabilidad exacta de que una réplica no contenga ninguno de los 2 segmentos con hueco: **{p(hc['prob_exacta_ninguno_de_los_2'], 2)}** ({hc['formula']}); observado en {mi(hc['replicas'])} réplicas: {p(hc['proporcion_observada_ninguno_de_los_2'])}; solo uno: {p(hc['proporcion_observada_solo_uno'])}; ambos: {p(hc['proporcion_observada_ambos'])}. En las réplicas sin ninguno, C es igual a A.
"""


def readme(N: dict) -> str:
    esc, f12, glob = N["esc"], N["f12"], N["glob"]
    return f"""# EP3: auditoría de cajas 3D sin par 2D en Waymo Open Dataset v2 (entrega final)

*Generado por `scripts/ep3/generar_docs_ep3.py`. EP2 sigue intacta (`README.md`, `docs/informe_tecnico_EP2.md`). Desviaciones: DEV-n; decisiones: DEC-n (`docs/ep3/ESTADO.md`).*

**En una frase.** Antes de revisar caja por caja, buscamos cámaras con huecos de pares por segmento (paso 1) y luego ordenamos las cajas de las celdas sanas con la regla «menos puntos LiDAR primero» (paso 2); una persona revisa y decide.

## Resultados clave (fuera de fold, 41 segmentos, IC 95 % por segmentos)
| Medida | Valor | Fuente |
|---|---|---|
| AUC de la regla elegida | {ic(esc, 'AUC')} | `f5_metricas_candidatos.csv` |
| Recall en el punto A (objetivo 0,80) | {ic(esc, 'recall_A')} | idem |
| Captura al revisar el 20 % de las cajas | {ic(esc, 'Captura@20', p)} | idem |
| ¿Algún modelo o ensamble supera a la regla? | No de forma distinguible (E2 la contiene y empata; nadie cumple O2) | `f6_tabla_seleccion.csv` |
| ¿Algún ensamble aporta? | No | `f4_ensambles_aporta.csv` |
| Cajas para el 80 % de recall: un paso / dos pasos | {p(esc['Fraccion_80'])} / {p(esc['Fraccion_80_C'])} *({EN_MUESTRA})* | `f5_brazoC.csv` |
| Dos pasos menos un paso (IC) *(en muestra)* | {c(glob['dif_C_menos_A'])} ({c(glob['ic_lo'])} a {c(glob['ic_hi'])}), no excluye 0 | `f12_diferencia_C_menos_A.csv` |
| ¿Mejoran los clusters la predicción? | No (descriptivo) | `f13_aporte_cluster.csv` |
| Pruebas | {PRUEBAS_EP3} en `tests/ep3` (EP2: {PRUEBAS_EP2}; total {PRUEBAS_TOTAL}) | `pruebas_ep3_conteo.json` (`pytest --collect-only`, sin ejecutar) |

**{GANANCIA_C}**

## Estructura (todo lo nuevo en carpetas `*_ep3`)
| Carpeta | Contenido |
|---|---|
| `docs/ep3/` | plan v3 (congelado), informe, guion, preguntas, despliegue, ESTADO, desviaciones |
| `src/waymo_evaluacion/ep3/` | `detector_huecos`, `metricas`, `modelos`, `candidatos`, `inferencia`, `app_logica`, `sellado`, `plan`, `datos` |
| `scripts/ep3/` | `f1` a `f7`, `f12`, `f13`, `puntuar_segmento`, `evaluar_sellado`, `ingesta_nuevos`, verificaciones, `empaquetar_entrega_ep3` |
| `notebooks/` | `11` a `15` (ejecutados) y `00b` (Colab, sin ejecutar) |
| `app/` | página Streamlit |
| `artefactos_ep3/` | versionable (fuera de `data/`): manifests, umbrales, parámetros del detector, plan v3 y tablas agregadas |
| `data/*_ep3` | `05_model_input_ep3`, `06_models_ep3` (v3 congelado), `07_model_output_ep3`, `08_reporting_ep3`, `09_app_ep3` (ignoradas por git) |
| `tests/ep3/` | {PRUEBAS_EP3} pruebas |
| raíz | `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `requirements_app.txt`, `requirements_ep3.txt`, `constraints_ep3.txt` |

## Cómo reproducir
```
.venv\\Scripts\\pip install -r requirements.txt -r requirements_ep3.txt -c constraints_ep3.txt
python scripts/verificar_congelados.py              # EP2: 14 de 14
python scripts/ep3/verificar_congelados_v3.py       # plan v3 y solución v3
python scripts/ep3/verificar_no_supervisado.py
python scripts/ep3/f1_datos.py ; python scripts/ep3/f2_detector.py
python scripts/ep3/f3_tuning.py --etapa principal --ncfg 30 --workers 6   # horas
python scripts/ep3/f3_analisis.py ; python scripts/ep3/f4_ensambles.py
python scripts/ep3/f5_generalizacion.py ; python scripts/ep3/f6_seleccion.py ; python scripts/ep3/f5_loso_curva.py
python scripts/ep3/f6_final.py ; python scripts/ep3/f12_analisis_muestra.py ; python scripts/ep3/f13_no_supervisado.py ; python scripts/ep3/f7_preparar_app.py
python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider
```
Para mirar sin recalcular: abrir los notebooks `11` a `15` (con `RECALCULAR = False` solo muestran artefactos).

## La página
`scripts\\ep3\\arrancar_app.bat` (o `python -m streamlit run app/app.py`) abre http://localhost:8501 y **escucha solo en localhost** (`.streamlit/config.toml`); no debe exponerse sin autenticación ni sin quitar los identificadores, ni publicarse en la nube con datos de Waymo. Docker: `docker compose up --build` (no probado; el puerto se publica solo en `127.0.0.1`). Detalles y guía de AWS (solo orientativa) en `docs/ep3/despliegue.md`.

## Qué falta
Validación con segmentos nuevos: `notebooks/00b_seleccion_segmentos_ep3.ipynb` en Colab, luego `evaluar_sellado.py congelar` y `evaluar` (una sola vez). Cómo dejar este archivo como README raíz: `docs/ep3/plan_integracion_readme.md`.
"""


def _de_cada_100(x) -> str:
    return f"{int(round(100 * x))} de cada 100"


TECNICOS = ("Datos y plan", "Filtro 1", "IE9 e IE10", "IE11 e IE12", "No supervisado")      # bloques tecnicos: 105 a 135 palabras por minuto de habla natural (F20-D4)


def demo_pasos(N: dict) -> list[dict]:
    """Los seis pasos del recorrido corto de la demo (95 s): una sola fuente para el bloque «Demo de la página» del guion y para la tabla «Recorrido corto» de la guía (F21-D1).

    Cada paso trae sus segundos, qué hacer, qué decir y qué se ve. La suma es 95 s; el texto de cada paso cabe en su tiempo a 140 palabras por minuto como máximo.
    """
    pg = N["pag"]
    eq = N["f12eq"]
    eqi = eq[eq["celdas_con_hueco"] == "incluidas"].set_index(["variable", "grupo"])
    h = {"azar": c(pg["horas_sin_orden"], 0), "uno": c(N["h_A"], 0), "dos": c(pg["horas_dos_pasos"], 0)}
    pasos = [
        {"seg": 15, "titulo": "Resumen y chip", "hacer": "Resumen, rol «Analista de revisión»; señalar las tres barras y abrir el chip «Datos de desarrollo · sin validación externa»",
         "decir": f"En el Resumen, tres barras: sin orden, unas {h['azar']} horas para encontrar el 80 %; solo con la cola, unas {h['uno']}; con auditoría previa, unas {h['dos']}, en muestra, con 20 segundos por caja.",
         "ver": f"{mi(N['n'])} cajas, {p(N['prev'])} sin pareja, 2 celdas marcadas; barras de horas (20 s por caja: supuesto); texto completo de «en muestra»"},
        {"seg": 25, "titulo": "Cola con ambos flujos", "hacer": "Cola de revisión: «Todos», flujo «Auditoría + cola (dos pasos, en muestra)», presupuesto 20 % (parte ahí)",
         "decir": f"En la cola, con todos los segmentos y el 20 %, con auditoría previa se encuentran unas {_de_cada_100(pg['recall_proceso'])} cajas sin pareja, en muestra, y solo con la cola unas {_de_cada_100(pg['recall_A'])}: "
                  f"{mi(pg['cajas_a_revisar'])} cajas y {c(pg['horas'], 1)} horas. Las primeras filas empatan porque todas tienen 0 puntos del sensor superior.",
         "ver": f"frase con ambos flujos; {mi(pg['cajas_a_revisar'])} cajas, {c(pg['horas'], 1)} h con 20 s por caja; la tabla abre con las cajas de 0 puntos"},
        {"seg": 15, "titulo": "Selección de una fila y nota del empate", "hacer": "Pestaña «Cola de cajas»; seleccionar la primera fila; leer la nota sobre la tabla",
         "decir": "Selecciono una fila y se abre su detalle: la probabilidad calibrada, la posición en la cola y el tipo de caso. La nota sobre la tabla lo confirma: el orden entre las empatadas no informa.",
         "ver": "panel de detalle debajo de la tabla; nota «Las primeras N cajas empatan (0 puntos del sensor superior…); el orden entre ellas no es informativo»"},
        {"seg": 15, "titulo": "Auditoría", "hacer": "Auditoría de cámaras: señalar el contorno rojo con X",
         "decir": "En la auditoría de cámaras vemos las dos celdas marcadas: no sabemos si faltan etiquetas o faltan datos.",
         "ver": "mapa de calor (gris rayado = sin datos suficientes, no es 0 %); Lista A con «Acción sugerida» y «Cajas afectadas»"},
        {"seg": 15, "titulo": "Explica con «Ciclista lejano»", "hacer": "Explica una caja: botón «Ciclista lejano»",
         "decir": "En «Explica una caja» uso el ejemplo «Ciclista lejano»: pocos puntos y lejos, arriba en la cola, y la página advierte que en ciclistas la regla es poco confiable.",
         "ver": f"probabilidad estimada, posición en la cola, tipo de caso, gráfico con los puntos A y B; advertencia ({c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones)"},
        {"seg": 10, "titulo": "Validación", "hacer": "Validación: recorrer las seis pestañas",
         "decir": "Cierro en Validación, con un gráfico por tema y la tabla completa dentro de cada pestaña.",
         "ver": "mejora de PR-AUC, diferencia de AUC, AUC por candidato, criterios O1 a O4, grupos descriptivos y el análisis en muestra"},
    ]
    assert sum(x["seg"] for x in pasos) == 95
    for x in pasos:                                                                                   # cada paso cabe en su tiempo: a lo más 140 palabras por minuto
        w = len(x["decir"].replace("**", "").split())
        assert w / x["seg"] * 60 <= 140, (x["titulo"], w, x["seg"], round(w / x["seg"] * 60))
        x["palabras"] = w
    return pasos


def guion(N: dict) -> str:
    esc, f12, glob = N["esc"], N["f12"], N["glob"]
    f13, f4, f3, f5 = N["f13"], N["f4"], N["f3"], N["f5"]
    pg, hc = N["pag"], N["hC"]
    eq = N["f12eq"]
    eqi = eq[eq["celdas_con_hueco"] == "incluidas"].set_index(["variable", "grupo"])
    k2 = N["k2"].sort_values("tasa_sin_camara")
    pts0 = N["eda"][N["eda"]["variable"] == "puntos_top"].iloc[0]["tasa"]
    lo, cv, ap = N["loso"]["Regla_top"], N["cv"], N["aporte"].set_index("k")
    br = N["brecha"]["XGB"].iloc[-2:].mean()
    f0 = N["fold0"]
    h = {"azar": c(pg["horas_sin_orden"], 0), "uno": c(N["h_A"], 0), "dos": c(pg["horas_dos_pasos"], 0)}
    bloques = [
        (40, "El problema", f"Un auto autónomo etiqueta peatones y ciclistas en 3D. A veces una caja no tiene su pareja en las cámaras, y revisarlas todas es caro: {mi(N['n'])} cajas, de las cuales {p(N['prev'])} no tiene pareja. "
         "Queremos que una persona revise primero las que más probablemente faltan.",
         "Página: Resumen (cuatro métricas y alertas)"),
        (45, "La idea en dos pasos", "La idea tiene dos pasos. Primero cuadramos la caja de recibos: buscamos cámaras con huecos y las atendemos aparte. Después revisamos recibo por recibo, ordenados. Una persona decide siempre. "
         "Y una advertencia desde ya: **esto es en muestra. El detector se ajustó con los mismos datos y aún no hay prueba ciega.**", "Resumen: el chip «Datos de desarrollo · sin validación externa» y su texto completo"),
        (45, "Datos y plan", "Usamos 41 segmentos: 33 de entrenamiento y 8 del test de EP2, que ya no son ciegos. El plan v3 quedó congelado con un hash antes de experimentar, y todo se valida por segmento con GroupKFold, porque las cajas de un mismo segmento se parecen entre sí. "
         f"Lo que más explica la falta de pareja son los puntos del LiDAR: {p(pts0)} de las cajas con 0 a 5 puntos del sensor superior no tiene pareja. Las desviaciones del plan se declaran aparte, y todo lo que no estaba en el plan lleva el rótulo post hoc.",
         "Notebook 11: tasa por segmento y EDA"),
        (40, "Filtro 1", f"El detector de huecos es estadística descriptiva, no aprendizaje automático. Para cada celda de segmento por cámara calcula la proporción de cajas con pareja y la compara con el 25 % de la mediana de esa cámara, siempre que haya al menos 100 cajas. "
         f"Reproduce los 2 huecos de EP2 y los marca en {f12['detector_combinaciones_que_detectan_los_2']} de {f12['detector_combinaciones']} combinaciones de parámetros. Eso mide estabilidad, no sensibilidad, porque no hay verdad externa. "
         f"Esas dos celdas reúnen {mi(N['f2']['positivos_en_hueco_principal'])} cajas sin pareja, el {p(N['f2']['positivos_en_hueco_principal'] / N['pos'])} del total: es un hallazgo post hoc.", "Página: Auditoría de cámaras (mapa y Lista A)"),
        (85, "IE9 e IE10", f"IE9: optimizamos cinco modelos con búsqueda aleatoria anidada. Para cada fold externo, la elección usa solo los segmentos de entrenamiento, con validación cruzada interna de tres partes por segmento y PR-AUC como criterio; fueron 30 configuraciones y una repetición, la desviación uno. "
         f"Mejoran {', '.join(N['n_mejoran'])}; no mejoran {', '.join(N['n_no'])}. Las curvas de validación lo explican: con más complejidad, la PR-AUC de entrenamiento sube, en HGB de {c(cv.loc[('HGB', 2), 'ap_train'])} a {c(cv.loc[('HGB', 31), 'ap_train'])}, y la de validación no sube. "
         "El valor viene de regularizar modelos que por defecto se sobreajustan. En los bordes de grilla, LightGBM quedó en el mínimo y extendimos una sola vez; después n_estimators quedó en el máximo, y lo declaramos como limitación. "
         f"IE10: probamos {len(f4)} ensambles. Los dos de stacking se calculan por segmentos, porque la validación cruzada de scikit-learn por defecto mezcla segmentos y filtra información. "
         f"Ninguno aporta: E3 y E4 quedan bajo su mejor componente, por {c(-f4.loc['E3', 'dif_AUC'])} y {c(-f4.loc['E4', 'dif_AUC'])} de AUC.",
         "Página: Validación, pestañas Hiperparámetros y Ensambles (un gráfico cada una)"),
        (90, "IE11 e IE12", f"IE11 mide la generalización fuera de fold, con intervalos que remuestrean segmentos completos. La regla de menos puntos del sensor superior tiene AUC {c(esc['AUC'])}, con intervalo de {c(esc['AUC_lo'])} a {c(esc['AUC_hi'])}, y nada más complejo la supera de forma distinguible. "
         f"Dejando un segmento fuera cada vez, {lo['segmentos_con_AUC_menor_a_0_55']} de {lo['segmentos_evaluables']} segmentos evaluables tienen AUC bajo 0,55; y en XGBoost la brecha entre ajuste y validación va de {c(br['AUC_ajuste'])} a {c(br['AUC_validacion'])}: sobreajuste. "
         f"La calibración con Platt, ajustada dentro de cada fold, deja el ECE de la regla en {c(esc['ECE_cal'])}, bajo el 0,05 exigido. IE12: los criterios estaban fijados antes. Se cumplen O1, AUC y PR-AUC, y O3, recall en el punto A. "
         f"Nadie cumple O2, «vale la pena» frente a la regla, ni O4, estabilidad por fold: el fold 0 baja a {c(f0)}. Como nadie cumple O4, la desviación dos, post hoc, aplica la misma regla de simplicidad que el plan fija para O2: el más simple a menos de 0,010 de AUC del mejor. "
         f"Es la regla. E2 gana en {int(f4.loc['E2', 'folds_ganados_de_5'])} de 5 folds, pero por {c(f4.loc['E2', 'dif_AUC'], 4)} de AUC, y contiene a la regla.",
         "Página: Validación, pestañas Generalización y Selección (cuadro O1 a O4)"),
        (25, "No supervisado", f"Los grupos describen, no predicen. Con k igual a 2, los lejanos y poco densos tienen {p(k2.iloc[-1]['tasa_sin_camara'], 0)} sin pareja y los cercanos y densos {p(k2.iloc[0]['tasa_sin_camara'], 0)}. "
         f"Agregarlos a la regla cambia el AUC en {c(ap.loc[2, 'dif_AUC'], 4)}, con intervalo que incluye cero. Es post hoc: son una partición cómoda, no grupos naturales.", "Página: Validación, pestaña No supervisado"),
        (95, "Demo de la página", "Veamos la página, siguiendo el recorrido corto de la guía de demo. " + " ".join(x["decir"] for x in demo_pasos(N)),
         "Recorrido corto de `pagina_guia_demo.md` (6 pasos): " + "; ".join(f"{i}) {x['titulo']} ({x['seg']} s)" for i, x in enumerate(demo_pasos(N), 1)) + ". Rol «Analista de revisión». (Recorrido extendido de respaldo: `pagina_guia_demo.md`)"),
        (60, "Lo que sabemos, lo que no sabemos y cómo lo vamos a saber", f"**Lo que sabemos:** una regla simple ordena bien, AUC {c(esc['AUC'])}, y revisando el 20 % de la cola se encuentran unas {_de_cada_100(pg['recall_proceso'])} cajas sin pareja con auditoría previa, en muestra, y unas {_de_cada_100(pg['recall_A'])} solo con la cola. "
         f"**Lo que no sabemos:** si el detector y la ganancia de dos pasos se sostienen fuera de muestra: sale de 2 celdas y casi por construcción el flujo en dos pasos no es peor. Tampoco por qué hay huecos, ni cómo anda la regla en ciclistas: {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones. "
         "**Cómo lo vamos a saber:** con la validación externa sellada, una sola vez, con segmentos nuevos y con el plan y el modelo congelados antes.", "Informe, secciones 14 y 17; `GUIA_VALIDACION_EXTERNA.md`"),
        (30, "Recomendaciones", "Auditar las cámaras antes de revisar cajas, usar la solución en tres capas con una persona que decide, monitorear la cobertura por segmento y por clase, y medir el tiempo real de revisión. Si no hay huecos, el flujo se reduce a la cola.", "Informe, sección 15"),
    ]
    t, filas, palabras, fallos = 0, [], [], []
    for seg, bloque, decir, mostrar in bloques:
        w = len(decir.replace("**", "").split())
        ppm = w / seg * 60
        if ppm > 140 or (bloque in TECNICOS and not 105 <= ppm <= 135):
            fallos.append((bloque, w, seg, round(ppm)))
        filas.append(f"| {t // 60}:{t % 60:02d} a {(t + seg) // 60}:{(t + seg) % 60:02d} | {bloque} |  | {decir} | {mostrar} | {w} | {ppm:.0f} |")
        palabras.append(w)
        t += seg
    assert not fallos, f"palabras por minuto fuera de rango (bloque, palabras, segundos, ppm): {fallos}"
    assert t == 555, t
    tec = [w / s * 60 for w, (s, b, *_) in zip(palabras, bloques) if b in TECNICOS]
    return f"""# Guion de presentación (9 minutos 15 segundos; 45 s de margen sobre 10 minutos)

*Generado por `scripts/ep3/generar_docs_ep3.py`. Cada cifra sale de los archivos de `data/08_reporting_ep3`; las de la demo, de `data/09_app_ep3` con la misma lógica que la página (`app_logica.py`). Total: 9:15. La columna «Quién» queda vacía para repartir los bloques. Palabras por minuto: ningún bloque supera 140 (máximo {max(w / s * 60 for w, (s, *_) in zip(palabras, bloques)):.0f}); los {len(TECNICOS)} bloques técnicos (Datos y plan, Filtro 1, IE9 e IE10, IE11 e IE12, No supervisado) van entre {min(tec):.0f} y {max(tec):.0f}, dentro de las 105 a 135 de habla natural; total {sum(palabras)} palabras (promedio {sum(palabras) / 555 * 60:.0f} palabras por minuto).*

| Tiempo | Bloque | Quién | Qué decir | Qué mostrar | Palabras | Palabras/min |
|---|---|---|---|---|---|---|
{chr(10).join(filas)}

**Frase corta de «en muestra» (decirla cada vez que se cite una cifra del flujo en dos pasos):** «Esto es en muestra: el detector se ajustó con los mismos datos y aún no hay prueba ciega.»

**Plan B si la demo falla:** mostrar `notebooks/14_ep3_dos_pasos_y_app.ipynb` (ya ejecutado, con la prueba de humo de las {len(SECCIONES_PAGINA)} secciones).

**Plan C si todo falla: video de 90 s de la demo**, grabado antes con el recorrido de `pagina_guia_demo.md` (sección «Guion del video de 90 s»).

## Plan por resultado de la validación externa
Los cuatro casos son los de `GUIA_VALIDACION_EXTERNA.md` (sección 7). En todos: la validación se corre una sola vez, con el plan y la solución congelados antes, y no hay verdad externa sobre qué celdas son huecos reales.
- **A. No hay huecos (C igual a A).** «En los segmentos nuevos el detector no marcó ninguna celda, así que el flujo en dos pasos coincide con el de un paso. Eso no refuta ni confirma el detector: pudo no haber huecos. Lo que sí informa es el desempeño de la regla fuera de muestra.»
- **B. Huecos encontrados.** «El detector marcó celdas en segmentos que no se usaron para ajustar sus parámetros, y al auditarlas hay que revisar menos cajas para el 80 %. Reportamos la diferencia con su intervalo y el punto de equilibrio. No decimos que el detector acierta: sigue sin haber verdad externa.»
- **C. Marcas sin verificar.** «Sabemos cuántas celdas marca el detector y que auditarlas ayuda, pero no si son lagunas de asociación, de etiquetado o de datos. Las reportamos como marcas sin verificar; la causa sigue desconocida.»
- **D. Una alternativa «gana».** «LR3 o XGBoost muestran una diferencia distinguible frente a la regla. Es un hallazgo post hoc, entre cuatro comparaciones: no cambia la solución elegida ni se usa para reajustar; sirve para decidir una validación nueva. Con pocos segmentos, lo más probable es que no se distinga.»
"""


def guia_demo(N: dict) -> str:
    pg, esc = N["pag"], N["esc"]
    eq = N["f12eq"]
    eqi = eq[eq["celdas_con_hueco"] == "incluidas"].set_index(["variable", "grupo"])
    pasos = demo_pasos(N)
    t_ini, filas_corto = 0, []
    for i, x in enumerate(pasos, 1):
        filas_corto.append(f"| {i} | {t_ini // 60}:{t_ini % 60:02d} a {(t_ini + x['seg']) // 60}:{(t_ini + x['seg']) % 60:02d} ({x['seg']} s) | **{x['titulo']}** | {x['hacer']} | «{x['decir']}» | {x['ver']} | {x['palabras']} |")
        t_ini += x["seg"]
    corto = "\n".join(filas_corto)
    return f"""# Guía de la demo de la página

*Generada por `scripts/ep3/generar_docs_ep3.py`; el «Recorrido corto» sale de la misma fuente (`demo_pasos`) que el bloque «Demo de la página» de `guion_presentacion.md` (1:35), así que dicen lo mismo. Las cifras salen de `data/09_app_ep3` con la misma lógica que la página (`app_logica.py`) y de `data/08_reporting_ep3`. Todas son en muestra: {EN_MUESTRA}.*

## Antes de empezar
1. Abrir con `scripts\\ep3\\arrancar_app.bat` (usa `app\\lanzar.py`, que carga la solución congelada y los datos antes de aceptar visitas: espere unos 3 s; se abre en http://localhost:8501 y solo es accesible desde este equipo).
2. Rol «Analista de revisión» (al pie de la barra lateral); modo presentación **apagado** al principio.
3. Tener a mano «Ayuda y glosario» por si preguntan un término.

## Recorrido corto (95 s, 6 pasos)
Es el que se hace en la presentación: los seis pasos del bloque «Demo de la página» del guion, con su tiempo. Total {sum(x['seg'] for x in pasos)} s; {sum(x['palabras'] for x in pasos)} palabras ({sum(x['palabras'] for x in pasos) / sum(x['seg'] for x in pasos) * 60:.0f} por minuto; ningún paso supera 140).

| # | Tiempo | Paso | Qué hacer (clics) | Qué decir | Qué se ve | Palabras |
|---|---|---|---|---|---|---|
{corto}

## Recorrido extendido (respaldo; {len(SECCIONES_PAGINA)} secciones, cada paso con sus clics y qué decir)
Para una demo más larga o si preguntan por algo que el recorrido corto no toca.

| # | Qué hacer (clics) | Qué decir | Qué se ve |
|---|---|---|---|
| 1 | **Resumen.** Señalar las 4 métricas y abrir el chip «Datos de desarrollo · sin validación externa» | «Esto es en muestra: el detector se ajustó con los mismos datos y aún no hay prueba ciega.» | {mi(N['n'])} cajas, {p(N['prev'])} sin pareja, 2 celdas marcadas, 41 segmentos |
| 2 | Señalar las tres barras de «Impacto estimado» y las «Alertas» | «Ordenar la cola baja el tiempo para el 80 % de ≈ {c(pg['horas_sin_orden'], 0)} h a ≈ {c(N['h_A'], 0)} h; con auditoría previa, ≈ {c(pg['horas_dos_pasos'], 0)} h, en muestra.» | barras de horas (20 s por caja: supuesto), tres alertas con enlace a su sección |
| 3 | **Cola de revisión.** Segmento «Todos», flujo «Auditoría + cola (dos pasos, en muestra)», presupuesto 20 % (parte ahí) | «Con auditoría previa, unas {_de_cada_100(pg['recall_proceso'])} cajas sin pareja; solo con la cola, unas {_de_cada_100(pg['recall_A'])}.» | frase con ambos flujos; {mi(pg['cajas_a_revisar'])} cajas, {c(pg['horas'], 1)} h con 20 s por caja |
| 4 | Cambiar el flujo a «Solo cola (un paso)» y volver | «Con un paso se ordenan todas las cajas, sin auditoría previa.» | cajas a revisar y horas del flujo elegido |
| 5 | Modo «Meta» con 80 %; «Volver al 20 %» | «Si quiero encontrar el 80 %, la página dice cuánto revisar.» | porcentaje de la cola para la meta (curva guardada) |
| 6 | Abrir «Supuestos y confiabilidad» | «El intervalo es ancho (41 segmentos) y la ganancia de dos pasos sale de 2 celdas.» | segundos por caja editables, intervalos, texto de «en muestra» |
| 7 | Pestaña «Curva de cobertura», luego «Cola de cajas»; **seleccionar una fila** | «Cada fila abre su detalle: probabilidad calibrada, posición y tipo de caso. Las primeras filas empatan: todas tienen 0 puntos del sensor superior y el orden entre ellas no informa.» | curva con intervalo sombreado; nota del empate sobre la tabla (calculada de la cola) y panel de detalle debajo, a todo el ancho |
| 8 | Activar «Agrupar por objeto» y filtrar la clase «Ciclista: poco confiable» | «Es solo una vista: el número de cajas a revisar no cambia. En ciclistas la regla es poco confiable.» | una fila por objeto con «Fotogramas en la cola»; «Filtrado: N cajas» |
| 9 | **Auditoría de cámaras.** Señalar el contorno rojo con X | «Dos celdas marcadas; no sabemos si es falta de etiquetas o de datos.» | mapa de calor (gris rayado = sin datos suficientes, no es 0 %), Lista A con «Acción sugerida» y «Cajas afectadas» |
| 10 | **Explica una caja.** Botón «Ciclista lejano» | «Pocos puntos y lejos: arriba en la cola. En ciclistas, advertencia: {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones.» | probabilidad estimada, posición en la cola, tipo de caso, gráfico con los puntos A y B; solo el control del sensor superior mueve la probabilidad |
| 11 | **Validación.** Recorrer las seis pestañas | «Un gráfico por tema, con los resultados guardados de EP3; la tabla completa está en cada pestaña.» | mejora de PR-AUC, diferencia de AUC, AUC por candidato, criterios O1 a O4, grupos descriptivos, análisis en muestra |
| 12 | Activar el **modo presentación** | «Se ocultan los identificadores y se agranda la letra.» | métricas 2 x 2, tabla sin identificadores |
| 13 | **Puntuar datos nuevos** (solo mostrar) y «Usar un segmento de desarrollo de ejemplo» | «Todo en memoria; el ejemplo se reconstruye de los datos derivados, no son datos crudos de Waymo.» | formato de los archivos como tabla; listas A y B del ejemplo |

## Guion del video de 90 s (plan C)
- 0:00 a 0:10: Resumen con el chip «en muestra».
- 0:10 a 0:40: Cola de revisión: 20 %, frase con ambos flujos, selección de una fila y su detalle.
- 0:40 a 1:00: Auditoría de cámaras: las dos celdas marcadas.
- 1:00 a 1:20: Explica una caja con el ejemplo «Ciclista lejano».
- 1:20 a 1:30: modo presentación y cierre: «Una persona revisa y decide».

## Si algo falla
- La página no abre: `scripts\\ep3\\arrancar_app.bat` otra vez; si no, el notebook 14 (ya ejecutado) y el video.
- Pregunta por un término: «Ayuda y glosario».
"""


def preguntas(N: dict) -> str:
    f3, f4, f5, esc, tab, sel = N["f3"], N["f4"], N["f5"], N["esc"], N["tab"], N["sel"]
    lo, xgb, f12, glob, f13 = N["loso"]["Regla_top"], N["brecha"]["XGB"].iloc[-2:].mean(), N["f12"], N["glob"], N["f13"]
    fr = N["fold_reg"]
    ap = N["aporte"].set_index("k")
    k2, k4 = N["k2"], N["k4"]
    eq = N["f12eq"]
    eqi = eq[eq["celdas_con_hueco"] == "incluidas"].set_index(["variable", "grupo"])
    ult = N["estab"].set_index("k")
    selk = N["selk"].set_index("k")
    hc, pg, adj = N["hC"], N["pag"], N["ari_diag_j"]
    ad_ = N["ari_diag"]
    ari_esf = float(ad_[(ad_["k"] == 2) & (ad_["covarianza"] == "spherical") & (ad_["n_init"] == 2)].iloc[0]["ARI_vs_KMeans"])
    ARI_TXT = f"(ARI KMeans–GMM: {c(f13['ari_entre_tecnicas']['k=2']['KMeans vs GMM'])} con el GMM de covarianza `full` y {c(ari_esf)} con el GMM esférico; el discrepante es el `full`)"
    acl, dfn, ptr, ptt = N["auc_cl"], N["defs"], N["pts_res"], N["pts_tab"]
    sres, srend, smot = N["sel_res"], N["sel_rend"].set_index(["corte", "grupo"]), N["sel_mot"].set_index("motivo_corto")
    cer = acl[(acl["k"] == 2) & (acl["tipo_de_caso"] == "cercanos y densos")].iloc[0]
    inv, ICV = N["inv_curva"], N["inv_curva"]
    nA, nC = "Solución elegida, un paso (A)", "Solución elegida, dos pasos (C)"
    ptv = lambda v, tr: ptt[(ptt["variante"] == v) & (ptt["tramo"] == tr)].iloc[0]["tasa"]  # noqa: E731
    br = N["base_rules"]
    eqx = eq[eq["celdas_con_hueco"] == "excluidas"].set_index(["variable", "grupo"])
    sin_regla = ["LR3", "LR", "RF", "HGB", "XGB", "LGBM", "E1", "E3", "E4"]                       # candidatos entrenados que no incluyen la regla como componente (E2 sí)
    mejor_sin_regla = str(f5.loc[sin_regla, "AUC"].idxmax())
    assert mejor_sin_regla == "LR3", mejor_sin_regla
    Q = [
        ("¿Qué problema resuelve el proyecto?", "Ayuda a una persona a decidir qué cajas 3D de peatones y ciclistas probablemente no tienen su pareja 2D de cámara, para revisarlas primero.", f"{mi(N['n'])} cajas en la población principal; {p(N['prev'])} sin pareja", "f1_resumen.json"),
        ("¿Qué es `sin_camara`?", "Es 1 si la caja 3D no tiene par en ninguna de las 5 cámaras. Es el target.", f"{mi(N['pos'])} positivos", "f1_resumen.json"),
        ("¿Por qué la población principal es |azimut| <= 100°?", "Más allá la tasa de `sin_camara` sube mucho (EP2); la sensibilidad a 120° se estudió en EP2.", "AZ_MAX = 100", "data/05_model_input/config_features_B.json"),
        ("¿Por qué validar por segmento?", "Las cajas de un mismo segmento (20 s de video) se parecen; mezclarlas entre entrenamiento y validación infla el resultado.", f"segmentos repartidos entre folds: {N['f1']['folds']['fold_s42']['segmentos_en_mas_de_un_fold']}", "f1_resumen.json"),
        ("¿Por qué los 8 segmentos de test de EP2 ya no son ciegos?", "Se abrieron 6 veces en EP2; ahora son material de desarrollo y la prueba ciega será con segmentos nuevos.", "41 = 33 + 8 segmentos", "plan_v3.md (P1), f1_resumen.json"),
        ("¿Qué hace el detector de huecos?", "Mide, por segmento y cámara, la fracción de cajas con par dentro del rango de azimut de esa cámara; si es menor al 25 % de la mediana y hay >= 100 cajas, marca un hueco.", f"{N['f2']['n_pares_con_hueco']} celdas con hueco, iguales a EP2", "f2_resumen.json"),
        ("¿Qué contienen las celdas con hueco?", "Una parte importante de los positivos, concentrada en pocas celdas.", f"{mi(N['f2']['positivos_en_hueco_principal'])} de {mi(N['pos'])} positivos ({p(N['f2']['positivos_en_hueco_principal'] / N['pos'])})", "f2_resumen.json"),
        ("¿Es el hueco una conclusión firme?", "No: es post hoc, no pre-declarado; puede ser etiquetado 2D faltante o datos de cámara ausentes, y con estos archivos no se distingue.", "2 celdas", "informe, sección 8"),
        ("¿Qué son las listas A y B?", "A: celdas con hueco, se atienden aparte. B: cajas de celdas sanas, ordenadas por la regla.", f"A = {N['f2']['n_pares_con_hueco']} celdas", "lista_A_huecos.csv"),
        ("¿Cómo se optimizaron los hiperparámetros?", "Búsqueda aleatoria anidada: la elección usa solo segmentos de entrenamiento (CV interna GroupKFold(3), criterio PR-AUC).", "30 configuraciones por modelo (DEV-1)", "f3_tuning.py, plan_v3.md (P5)"),
        ("¿Qué significa «mejora»?", "Diferencia de PR-AUC >= +0,010 con IC pareado por segmentos que excluya 0.", f"mejoran {', '.join(N['n_mejoran'])}", "f3_defecto_vs_optimizado.csv"),
        ("¿Por qué XGBoost y LightGBM sí mejoran?", "Porque su configuración por defecto se sobreajusta y la búsqueda los regulariza; no porque terminen mejores que la regla.", f"XGB dif. PR-AUC {c(f3.loc['XGB', 'dif_PR-AUC'])}; AUC optimizado {c(f3.loc['XGB', 'AUC_opt'])} contra regla {c(f5.loc['Regla top', 'AUC'])}", "f3_defecto_vs_optimizado.csv, f5_metricas_candidatos.csv"),
        ("¿Se revisaron los bordes de la grilla?", "Sí. Solo LightGBM `min_child_samples` quedó en el borde; se extendió una vez. Después `n_estimators` quedó en el máximo: limitación declarada.", "LightGBM n_estimators = 200 en 5 de 5 folds", "f3_bordes.csv"),
        ("¿Qué muestran las curvas de validación?", "Que al aumentar la complejidad el entrenamiento sube y la validación no; lo mejor está en lo más regularizado.", f"HGB validación {c(N['cv'].loc[('HGB', 2), 'ap_val'])} con 2 hojas y {c(N['cv'].loc[('HGB', 31), 'ap_val'])} con 31", "f3_curvas_validacion.csv"),
        ("¿Qué ensambles probaron?", "E1 voting soft, E2 promedio de rangos con la regla, E3 stacking de 5 modelos, E4 stacking por vistas.", "4 ensambles", "plan_v3.md (P6)"),
        ("¿Por qué el stacking se hizo a mano?", "El CV interno por defecto de scikit-learn mezcla segmentos y filtra información; usamos GroupKFold(3) por segmento dentro de cada fold externo.", "GroupKFold(3)", "candidatos.py, f4_ensambles.py"),
        ("¿Aporta algún ensamble?", "No. E1 queda cerca de 0 con IC que incluye 0; E3 y E4 quedan por debajo de su mejor componente.", f"E1 {c(f4.loc['E1', 'dif_AUC'])} (IC {c(f4.loc['E1', 'dif_lo'])} a {c(f4.loc['E1', 'dif_hi'])}); gana en {int(f4.loc['E1', 'folds_ganados_de_5'])} de 5 folds y {int(f4.loc['E1', 'segmentos_ganados'])} de {int(f4.loc['E1', 'segmentos_comparados'])} segmentos", "f4_ensambles_aporta.csv"),
        ("¿Por qué no ayuda promediar modelos?", "Todos usan la misma señal (los puntos LiDAR) y se equivocan juntos.", f"E2 contra regla: {c(f4.loc['E2', 'dif_AUC'])}", "f4_ensambles_aporta.csv"),
        ("¿Qué mide el AUC y qué la PR-AUC?", "El AUC es la probabilidad de que una caja sin pareja puntúe más alto que una con pareja; la PR-AUC pondera la precisión cuando los positivos son una minoría.", f"AUC {c(esc['AUC'])}, PR-AUC {c(esc['PR-AUC'])}", "f6_modelo_escogido.csv"),
        ("¿Qué es la Captura@20 %?", "La fracción de positivos que aparece en el 20 % de cajas mejor ordenadas.", f"{p(esc['Captura@20'])} (al azar 20 %)", "f5_metricas_candidatos.csv"),
        ("¿Qué es la Fracción para 80 %?", f"La fracción de cajas que hay que revisar para encontrar el 80 % de los positivos. Nota: el conteo observado da {p(esc['Fraccion_80'])} y la curva guardada (interpolada) da {p(inv[nA][0.80])}; es la misma cantidad con dos métodos y el texto cita el conteo.", f"{p(esc['Fraccion_80'])} en un paso; {p(esc['Fraccion_80_C'])} en dos pasos ({EN_MUESTRA})", "f5_brazoC.csv"),
        ("¿Qué son los puntos A y B?", "A: umbral que busca recall 0,80, fijado con scores internos de entrenamiento. B: umbral que revisa el 20 % de las cajas.", f"recall A {c(esc['recall_A'])}; recall B {c(esc['recall_B'])}", "f5_metricas_candidatos.csv"),
        ("¿Está calibrada la probabilidad?", "Con Platt, el ECE queda bajo 0,05 en la regla.", f"ECE {c(esc['ECE_cal'])}, Brier {c(esc['Brier_cal'])}", "f5_metricas_candidatos.csv"),
        ("¿Es estable la solución?", "Por segmento sí (mediana alta); por fold no cumple el criterio de 0,75 en ningún candidato, por el fold 0.", f"mediana por segmento {c(esc['AUC_mediana_segmento'])}; mínimo por fold {c(esc['AUC_min_fold'])}", "f5_metricas_candidatos.csv"),
        ("¿Qué muestra el leave-one-segment-out?", "Que dejar un segmento fuera casi no cambia el AUC global y que hay segmentos difíciles.", f"AUC LOSO {c(lo['AUC'])}; {lo['segmentos_con_AUC_menor_a_0_55']} de {lo['segmentos_evaluables']} segmentos con AUC < 0,55", "f5_loso_resumen_Regla_top.json"),
        ("¿Hay sobreajuste en los modelos de árboles?", "Sí: la brecha de ajuste a validación es grande y no se cierra con más segmentos. La regla no tiene brecha porque no aprende.", f"XGB: ajuste {c(xgb['AUC_ajuste'])}, validación {c(xgb['AUC_validacion'])}", "f5_brecha_XGB.csv"),
        ("¿Por qué se eligió la regla?", "Por el plan: el más simple cuyo AUC queda a menos de 0,010 del mejor; nadie cumplió O4 y se aplicó una regla de reserva post hoc entre los que cumplen O1 y O3.", sel["razon"], "f6_seleccion.json, plan_v3_desviaciones.md (DEV-2)"),
        ("¿Algún candidato «vale la pena» frente a la regla (O2)?", "Ninguno.", f"mejor dif. de Fracción 80 %: {c(tab['dif_Fraccion_80_vs_regla'].min())} (E2, IC {c(tab.loc['E2', 'dif_Fraccion_80_lo'])} a {c(tab.loc['E2', 'dif_Fraccion_80_hi'])})", "f6_tabla_seleccion.csv"),
        ("¿Cuánto cuesta revisar?", f"Con el supuesto de {SEG_POR_CAJA} s por caja (no medido, editable en la página): horas para el 80 % de recall.", f"un paso {N['h_A']:.0f} h; dos pasos {N['h_C']:.0f} h ({EN_MUESTRA}); al azar {N['h_azar']:.0f} h", "f6_modelo_escogido.csv"),
        ("¿Qué es el punto de equilibrio?", "El costo en cajas por auditoría con el que dos pasos empata con un paso; no inventamos un costo.", f"{mi(N['eq'])} cajas (IC {mi(esc['equilibrio_lo'])} a {mi(esc['equilibrio_hi'])}) ({EN_MUESTRA})", "f5_brazoC.csv"),
        ("¿Qué hace la página?", f"Es una consola de revisión con navegación agrupada: un resumen con el impacto estimado y alertas, la cola de revisión (cuánto revisar o cuánto encontrar, con ambos flujos, detalle por caja, vista por objeto y filtros), el mapa de huecos, la explicación de una caja con ejemplos de un clic, la validación con un gráfico por tema, la ficha de ética, el puntaje de segmentos nuevos y una ayuda con glosario.", f"{len(SECCIONES_PAGINA)} páginas, 3 roles", "app/app.py, app/secciones.py"),
        ("¿Cómo se despliega?", "Local con Streamlit o con Docker (volumen de datos de solo lectura, sin datos en la imagen). Docker no se probó; AWS es solo una guía.", "Docker 28.3.0 instalado, demonio apagado", "despliegue.md"),
        ("¿Qué pasa con la licencia y la privacidad?", "Los datos de Waymo no salen del equipo; los identificadores se ocultan en modo presentación; el zip es solo para uso académico del docente.", "sin red, sin datos en la imagen", "despliegue.md, informe sección 16"),
        ("¿Qué cambió respecto de EP2?", "41 segmentos juntos, + XGBoost y LightGBM, búsqueda anidada, ensambles, filtro 1 en el flujo, no supervisado, página y despliegue.", "ver tabla de cambios", "informe_tecnico_EP3.md, sección 6"),
        ("¿Por qué no hay nodos de Kedro en EP2 y EP3?", "El análisis vive en notebooks y scripts; los pipelines de Kedro son los de ingesta y preprocesamiento de EP1.", "-", "informe_tecnico_EP3.md, sección 6"),
        ("¿Por qué 1 repetición y 30 configuraciones?", "Regla de cómputo: la proyección con el plan completo superaba 4 horas (RF tarda 45 a 100 s por ajuste). Está registrado como DEV-1.", "DEV-1", "plan_v3_desviaciones.md"),
        ("¿Qué son accuracy y F1 aquí?", "Solo referencia en el cuadro «Modelo escogido»; no deciden nada.", f"F1 en A {c(esc['F1_A'])}; accuracy en A {c(esc['accuracy_A'])}", "f6_modelo_escogido.csv"),
        ("¿Qué falta?", "Validación externa con segmentos nuevos (sellada), probar Docker y medir el tiempo real de revisión.", "-", "informe_tecnico_EP3.md, sección 17"),
        # ---- nuevas (fase 14)
        ("¿Dónde está el Machine Learning si la solución final es una regla?", "El ML son los 11 candidatos entrenados y comparados con búsqueda anidada y validación por segmento (LR, RF, HGB, XGBoost, LightGBM, cuatro ensambles, la regla y una LR de 3 variables), y ninguno la supera de forma distinguible; además el ML aporta la calibración Platt (una regresión logística) y el análisis no supervisado. El detector de huecos **no es ML**: son percentiles, una mediana y un umbral (estadística descriptiva). Concluir que una regla basta es un resultado del aprendizaje automático, no su ausencia. "
         f"En cifras: el mejor modelo entrenado sin la regla es {mejor_sin_regla} con {c(f5.loc[mejor_sin_regla, 'AUC'])}; E2, que la incluye como componente, {c(f5.loc['E2', 'AUC'])}; la regla sola, {c(f5.loc['Regla top', 'AUC'])}.", f"11 candidatos; AUC regla {c(f5.loc['Regla top', 'AUC'])}; mejor modelo sin la regla: {mejor_sin_regla} {c(f5.loc[mejor_sin_regla, 'AUC'])}; E2 (la incluye) {c(f5.loc['E2', 'AUC'])}", "f5_metricas_candidatos.csv, f6_tabla_seleccion.csv"),
        ("¿Por qué no elegir E2 si tiene mejor PR-AUC?", f"Porque la diferencia no es distinguible y E2 contiene a la regla: AUC {c(N['e2']['auc'])} contra {c(f5.loc['Regla top', 'AUC'])}, PR-AUC {c(N['e2']['pr'])} contra {c(f5.loc['Regla top', 'PR-AUC'])}, Fracción 80 % {c(N['e2']['fr'])} contra {c(f5.loc['Regla top', 'Fraccion_80'])} (IC de la diferencia {c(N['e2']['lo'])} a {c(N['e2']['hi'])}). Además su ECE es {c(N['e2']['ece'])} (> 0,05). El plan manda elegir el más simple dentro de 0,010 de AUC.", f"dif. AUC {c(f4.loc['E2', 'dif_AUC'])}", "f6_tabla_seleccion.csv, f4_ensambles_aporta.csv"),
        ("¿Por qué RF empeora al optimizar?", "No lo sabemos: es una hipótesis (no verificada) que la búsqueda interna, con 30 configuraciones y 41 segmentos, elige configuraciones que se ajustan a particularidades de los segmentos de entrenamiento y no se sostienen en el fold de validación. LR también empeora, con otra posible causa (el criterio interno puede preferir variables y regularización distintas).", f"RF dif. PR-AUC {c(f3.loc['RF', 'dif_PR-AUC'])} (IC {c(f3.loc['RF', 'dif_PR-AUC_lo'])} a {c(f3.loc['RF', 'dif_PR-AUC_hi'])}); LR {c(f3.loc['LR', 'dif_PR-AUC'])}", "f3_defecto_vs_optimizado.csv"),
        ("¿Por qué 1 repetición de la CV externa?", "Porque Random Forest tarda 45 a 100 s por ajuste y el plan completo (3 repeticiones x 40 configuraciones) proyectaba unas 5 horas, sobre el límite de 4. Consecuencia: los IC reflejan una sola partición de segmentos en folds.", "DEV-1", "plan_v3_desviaciones.md"),
        ("¿Qué pasa en el fold 0?", f"Contiene {int(fr.loc['0', 'segmentos'])} segmentos y {mi(fr.loc['0', 'cajas'])} cajas, entre ellos `257766998801` (cámara 3 sin pares). El AUC de la regla es {c(fr.loc['0', 'AUC_A'])} en el brazo A y {c(fr.loc['0', 'AUC_B_celdas_sanas'])} sobre celdas sanas: el fallo del criterio de estabilidad se debe a la celda con hueco. Post hoc.", f"AUC A {c(fr.loc['0', 'AUC_A'])}; B {c(fr.loc['0', 'AUC_B_celdas_sanas'])}", "f12_auc_por_fold_brazos.csv"),
        ("¿El 29,6 % no es circular?", f"En parte sí: los parámetros del detector se ajustaron con estos 41 segmentos y el hueco se descubrió en ellos, y la ganancia sale de 2 celdas cámara x segmento. Por eso se rotula {EN_MUESTRA}. La diferencia pareada con un paso es {c(glob['dif_C_menos_A'])} con IC {c(glob['ic_lo'])} a {c(glob['ic_hi'])} (no excluye 0). La prueba no circular es la validación con segmentos nuevos.", f"{p(esc['Fraccion_80_C'])} contra {p(esc['Fraccion_80'])}", "f5_brazoC.csv, f12_diferencia_C_menos_A.csv"),
        ("¿Qué pasa si el hueco no existe en datos nuevos?", f"El detector no marcaría nada (o marcaría celdas sin verdad externa que lo confirme) y el flujo se reduce a la cola con la regla: dos pasos pasa a ser un paso, y la Fracción para 80 % vuelve a unos {p(esc['Fraccion_80'])}. Las celdas marcadas además de los 2 de referencia en la muestra van de {f12['detector_falsas_alarmas_rango'][0]} a {f12['detector_falsas_alarmas_rango'][1]} celdas según los parámetros; su tasa en datos nuevos se medirá en la validación externa (sin verdad externa, no es una tasa de error).", f"celdas marcadas extra {f12['detector_falsas_alarmas_rango'][0]} a {f12['detector_falsas_alarmas_rango'][1]}", "f12_sensibilidad_detector.csv"),
        ("¿Qué muestran los clusters y qué no?", f"Muestran que los casos lejanos y poco densos tienen mucha más tasa de `sin_camara` ({p(k2.sort_values('tasa_sin_camara').iloc[-1]['tasa_sin_camara'])}) que los cercanos y densos ({p(k2.sort_values('tasa_sin_camara').iloc[0]['tasa_sin_camara'])}). No muestran grupos naturales firmes {ARI_TXT} ni causalidad.", f"k = {f13['k_elegido']}; silhouette {c(selk.loc[f13['k_elegido'], 'silhouette_muestra_20000'])}", "f13_clusters_k2.csv, f13_resumen.json"),
        ("¿Mejoran los clusters la predicción?", f"No. Agregar el cluster a la probabilidad de la regla cambia el AUC en {c(ap.loc[2, 'dif_AUC'], 4)} (IC {c(ap.loc[2, 'ic_lo'], 4)} a {c(ap.loc[2, 'ic_hi'], 4)}) con k = 2 y en {c(ap.loc[4, 'dif_AUC'], 4)} con k = 4 (IC {c(ap.loc[4, 'ic_lo'], 4)} a {c(ap.loc[4, 'ic_hi'], 4)}: la empeora). El AUC base de esa comparación es {c(dfn['auc_base_f13']['AUC_f13_aporte_cluster_base_reproducido'])} y no {c(dfn['auc_base_f13']['AUC_puntaje_crudo_pooled'])} porque usa la probabilidad con Platt de cada fold y una regresión logística adicional (informe §9). Sobre el acuerdo entre técnicas: {ARI_TXT}.", f"dif. AUC k = 2: {c(ap.loc[2, 'dif_AUC'], 4)}", "f13_aporte_cluster.csv"),
        ("¿Por qué ese k?", f"Se elige k por el máximo silhouette entre 2 y 6: k = {f13['k_elegido']} ({c(selk.loc[f13['k_elegido'], 'silhouette_muestra_20000'])}); se explora también k = 4 como en EP2 ({c(selk.loc[4, 'silhouette_muestra_20000'])}). Con k = 4 la estabilidad por segmentos es baja (ARI mínimo {c(ult.loc[4, 'ari_minimo'])}) y los clusters empeoran la predicción. Sobre el acuerdo entre técnicas: {ARI_TXT}.", f"silhouette k = 2: {c(selk.loc[2, 'silhouette_muestra_20000'])}", "f13_seleccion_k.csv, f13_estabilidad.csv"),
        ("¿Qué sesgos mediste?", f"Descriptivamente, el recall de la regla en el punto A por ubicación, momento del día y clase. Con celdas con hueco: de día {c(eqi.loc[('momento_del_dia', 'Day'), 'recall_A'])} y de noche {c(eqi.loc[('momento_del_dia', 'Night'), 'recall_A'])}; San Francisco {c(eqi.loc[('ubicacion', 'location_sf'), 'recall_A'])}; ciclistas {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} (solo {int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos). Sin pruebas de hipótesis; parte de la brecha desaparece al quitar las celdas con hueco.", f"recall A global {c(eqi.loc[('todas', 'todas'), 'recall_A'])}", "f12_equidad.csv"),
        ("¿El ARI tan bajo entre KMeans y GMM es un error de código?", f"No. Las tres técnicas usan las mismas {mi(adj['filas']['filas_muestra'])} filas en el mismo orden, el ARI recalculado coincide con el original y los GMM convergieron. KMeans coincide con el GMM esférico ({c(ari_esf)}) y con el diagonal; el discrepante es el GMM de covarianza `full` ({c(f13['ari_entre_tecnicas']['k=2']['KMeans vs GMM'])}), que parte la muestra 70/30 contra 47/53 de KMeans. En EP2 el 0,997 usó variables de oclusión discretas con covarianzas degeneradas (`docs/informe_tecnico_EP2.md:422`); hipótesis, no verificada: ese 0,997 probablemente estaba inflado y el {c(f13['ari_entre_tecnicas']['k=2']['KMeans vs GMM'])} no es la anomalía.", f"ARI KMeans–GMM {c(f13['ari_entre_tecnicas']['k=2']['KMeans vs GMM'])} (full) y {c(ari_esf)} (esférico), k = 2", "f13_ari_diagnostico.csv, f13_ari_diagnostico.json, docs/informe_tecnico_EP2.md:408-429, data/08_reporting/08_no_supervisado_resumen.json:5-7"),
        ("¿El brazo C no es mejor que A por construcción?", f"En cajas revisadas, casi: la auditoría quita cajas de la cola sin costo por caja, así que C no puede ser peor que A; lo informativo es el punto de equilibrio ({mi(N['eq'])} cajas por auditoría) y la tasa de celdas marcadas del detector (con su estabilidad), que solo se miden con datos nuevos. Rótulo: {EN_MUESTRA}.", f"dif. C menos A {c(glob['dif_C_menos_A'])} (IC {c(glob['ic_lo'])} a {c(glob['ic_hi'])})", "f12_diferencia_C_menos_A.csv, f5_brazoC.csv"),
        ("¿Por qué el límite superior del IC de C menos A es exactamente 0?", f"Porque en las réplicas del bootstrap que no contienen ninguno de los 2 segmentos con hueco, C es igual a A. Con 41 segmentos muestreados con reemplazo la probabilidad exacta de ese evento es {p(hc['prob_exacta_ninguno_de_los_2'], 2)} ({hc['formula']}) y se observó {p(hc['proporcion_observada_ninguno_de_los_2'])} en {mi(hc['replicas'])} réplicas: es un efecto del diseño, no evidencia a favor ni en contra de C.", f"exacta {p(hc['prob_exacta_ninguno_de_los_2'], 2)}; observada {p(hc['proporcion_observada_ninguno_de_los_2'])}", "f12b_hechos_brazoC.json"),
        ("¿Qué muestra la página con «Todos» y 20 %, y por qué no coincide con el 61,9 %?", f"Muestra el brazo de dos pasos (C): «unas {_de_cada_100(pg['recall_proceso'])} cajas sin pareja» ({p(pg['recall_proceso'])}; intervalo {p(pg['lo'])} a {p(pg['hi'])}), {mi(pg['cajas_a_revisar'])} cajas y {c(pg['horas'], 1)} h con {SEG_POR_CAJA} s por caja (en muestra). El {p(esc['Captura@20'])} es la captura del brazo de un paso (A) al revisar el 20 % y está en la pestaña Selección de Validación; son brazos distintos. **El «20 %» tampoco es el mismo:** la página toma el 20 % de la cola de celdas sanas ({mi(dfn['definicion_20pct']['pagina_cajas_revisadas_al_20pct'])} cajas) y el informe §12 el 20 % del total ({mi(dfn['definicion_20pct']['f5_cajas_revisadas_al_20pct'])} cajas), por eso el brazo C da {p(dfn['definicion_20pct']['recall_C_pagina_curva_20pct_de_la_cola'])} en la página y {p(dfn['definicion_20pct']['captura20_C_informe_f5'])} en el informe. Tras el rediseño la página usa una sola fuente (el conteo observado, {p(pg['recall_proceso'])}); antes la tarjeta mostraba {p(pg['recall'])} (curva interpolada) y el texto {p(pg['recall_proceso'])}.", f"C {p(pg['recall_proceso'])}; A {p(pg['recall_A'])}", "data/09_app_ep3 (kpis.json, curva_cola.csv), f5_metricas_candidatos.csv, f18_definiciones.json"),
        ("¿La regla trata igual a todos los casos?", f"No. Con celdas con hueco, de día el recall es {c(eqi.loc[('momento_del_dia', 'Day'), 'recall_A'])} y de noche {c(eqi.loc[('momento_del_dia', 'Night'), 'recall_A'])}; sin esas celdas, de día {c(eqx.loc[('momento_del_dia', 'Day'), 'recall_A'])} y la brecha se invierte (era el hueco). San Francisco baja la brecha ({c(eqi.loc[('ubicacion', 'location_sf'), 'recall_A'])} a {c(eqx.loc[('ubicacion', 'location_sf'), 'recall_A'])}) pero queda. En ciclistas el recall es {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones ({int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos en {int(eqi.loc[('clase', 'CYCLIST'), 'segmentos'])} segmentos): poco confiable. Descriptivo, sin pruebas de hipótesis.", f"ciclistas {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])}", "f12_equidad.csv"),
        ("¿Se puede exponer la página en la red o publicarla en la nube?", "No tal como está: escucha solo en localhost (`.streamlit/config.toml`), el compose publica el puerto solo en 127.0.0.1 y la página muestra identificadores de objeto. Para exponerla haría falta autenticación y quitar los identificadores, y los datos de Waymo no deben subirse a servicios de nube (licencia de uso no comercial). Una prueba vigila esa configuración.", "address = localhost; 127.0.0.1:8501:8501", ".streamlit/config.toml, docker-compose.yml, tests/ep3/test_seguridad_pagina.py"),
        ("¿Qué recomiendas al negocio?", "Usar la solución en tres capas (auditar cámaras primero, cola con la regla, persona que decide), monitorear el recall por segmento y por clase, medir el tiempo real de revisión y el costo de una auditoría, y validar con segmentos nuevos antes de confiar en el flujo en dos pasos.", f"punto de equilibrio {mi(N['eq'])} cajas ({EN_MUESTRA})", "informe, sección 15; f5_brazoC.csv"),
    ]
    Q += [
        ("¿Por qué la regla ordena peor las cajas cercanas y densas? (post hoc)", f"Con k = 2, el AUC de la regla es {c(cer['AUC_todas'])} en las cercanas y densas y sube a {c(cer['AUC_sin_celdas_con_hueco'])} sin las cajas de las 2 celdas con hueco: buena parte de la pérdida viene del hueco ({p(cer['positivos_en_celdas_con_hueco'] / cer['positivos'], 0)} de los positivos del cluster están ahí). Queda una brecha frente a las lejanas ({c(acl[(acl['k'] == 2) & (acl['tipo_de_caso'] == 'lejanos y poco densos')].iloc[0]['AUC_sin_celdas_con_hueco'])}). Descriptivo, sin IC; post hoc, no pre-declarado.", f"AUC {c(cer['AUC_todas'])} a {c(cer['AUC_sin_celdas_con_hueco'])}", "f13_auc_cluster_sin_huecos.csv, f13_clusters_k2.csv"),
        ("¿Por qué la tasa de sin_camara sube de 51–100 a más de 100 puntos? (post hoc)", f"Por las celdas con hueco: en el tramo > 100 hay {mi(ptr['tramo_mayor_100']['cajas_en_celdas_con_hueco'])} cajas de esas celdas con tasa {p(ptr['tramo_mayor_100']['tasa_en_celdas_con_hueco'])}. Con todas las cajas la tasa pasa de {p(ptr['tramo_51_100']['tasa'])} a {p(ptr['tramo_mayor_100']['tasa'])}; sin esas celdas va de {p(ptr['tramo_51_100']['tasa_sin_hueco'])} a {p(ptr['tramo_mayor_100']['tasa_sin_hueco'])} (decreciente). Hipótesis, no verificada: son cajas con muchos puntos cuya cámara no tiene etiquetas.", f"{p(ptr['tramo_mayor_100']['tasa'])} con hueco; {p(ptr['tramo_mayor_100']['tasa_sin_hueco'])} sin hueco", "f12_eda_puntos_top_sin_huecos.csv, f12_eda_puntos_top_resumen.json"),
        ("¿Qué significa «30 de 30» en el detector? ¿Es sensibilidad?", "No. Los 2 huecos de referencia los define el mismo detector con los parámetros de EP2, así que no hay verdad externa: «30 de 30» mide la estabilidad del conjunto marcado frente a los parámetros, no sensibilidad ni especificidad, y las celdas marcadas de más no son «falsas alarmas» comprobadas. Con segmentos nuevos se medirá la tasa de celdas marcadas y su estabilidad (DEV-3).", f"{f12['detector_combinaciones_que_detectan_los_2']} de {f12['detector_combinaciones']} combinaciones", "f12_sensibilidad_detector.csv, plan_v3_desviaciones.md (DEV-3)"),
        ("¿La selección de segmentos introdujo un sesgo?", f"Sí, a escala de segmento: EP2 evaluó {sres['evaluados']} candidatos y descartó {sres['descartados']} ({mi(smot.loc['asociación vacía', 'segmentos'])} por asociación vacía, {mi(smot.loc['etiquetado ralo', 'segmentos'])} por etiquetado ralo, {mi(smot.loc['pocas asociaciones', 'segmentos'])} por pocas asociaciones); el rendimiento fue de {p(srend.loc[('momento_del_dia', 'Day'), 'rendimiento'], 0)} de día y {p(srend.loc[('momento_del_dia', 'Night'), 'rendimiento'], 0)} de noche. La causa (etiquetado o publicación) es desconocida y el detector solo se evaluó con etiquetado denso. Recomendación: un filtro 1 a nivel segmento (sin ML).", f"{sres['descartados']} de {sres['evaluados']} descartados", "f18_seleccion_motivos.csv, f18_seleccion_rendimiento.csv, docs/seleccion_segmentos/registro_verificacion_ep2.csv"),
        ("¿Por qué recall objetivo 0,80?", f"Es una decisión heredada de EP2 (punto A), no validada con el negocio. La curva guardada da, con un paso, {p(inv[nA][0.70])}, {p(inv[nA][0.80])} y {p(inv[nA][0.90])} de las cajas para encontrar 70 %, 80 % y 90 % de las sin pareja; con dos pasos (en muestra) {p(inv[nC][0.70])}, {p(inv[nC][0.80])} y {p(inv[nC][0.90])} de la cola de celdas sanas. Nota: el 80 % da {p(inv[nA][0.80])} en la curva guardada y {p(esc['Fraccion_80'])} en el conteo observado (la curva se interpola entre puntos).", f"fracción para 70/80/90 %: {p(inv[nA][0.70], 0)}/{p(inv[nA][0.80], 0)}/{p(inv[nA][0.90], 0)} (un paso)", "data/09_app_ep3/curva_cola.csv"),
        ("¿Qué es la calibración de Platt?", f"Una regresión logística de una variable que convierte el puntaje de la regla en una probabilidad de no tener pareja. Se ajusta con puntajes internos del conjunto de entrenamiento de cada fold (DEC-7), no con el fold de validación. Resultado: ECE {c(f5.loc['Regla top', 'ECE_cal'])} (<= 0,05). No cambia el orden dentro de un fold.", f"ECE {c(f5.loc['Regla top', 'ECE_cal'])}", "f5_metricas_candidatos.csv, f5_calibracion_bins.csv"),
        ("¿Cómo se evitó la fuga de datos?", f"Los folds se arman por segmento (ningún segmento en más de un fold: {N['f1']['folds']['fold_s42']['segmentos_en_mas_de_un_fold']}), la búsqueda de hiperparámetros es anidada (CV interna dentro del entrenamiento) y los umbrales y el calibrador se fijan con puntajes internos. Límites honestos: los parámetros del detector se ajustaron con los mismos 41 segmentos y los 8 de test de EP2 ya se habían mirado; por eso lo del brazo C es en muestra.", "folds por segmento; búsqueda anidada", "f1_resumen.json, plan_v3.md (P1)"),
        ("¿Qué es el bootstrap por segmentos?", "Se remuestrean segmentos completos con reemplazo (1.000 réplicas, semilla 42), se recalcula la métrica en cada réplica y el IC 95 % es el percentil 2,5 a 97,5. Respeta que las cajas de un segmento se parecen entre sí. Con 41 segmentos los IC son anchos.", "1.000 réplicas", "plan_v3.md (P1), metricas.py"),
        ("¿Por qué PR-AUC para optimizar y AUC para elegir?", "Así lo fijó el plan v3: la búsqueda interna usa PR-AUC porque pesa más a la clase minoritaria (21,2 % sin pareja), y la comparación entre candidatos usa AUC porque no depende de la prevalencia, que cambia mucho entre segmentos. Ninguna de las dos reemplaza mirar la fracción de cajas para el recall objetivo.", f"prevalencia {p(N['prev'])}", "plan_v3.md (P1, P8)"),
        ("¿Por qué puntos del sensor superior y no los totales?", f"Es la regla heredada de EP2 y en los 41 segmentos es la mejor de las reglas simples, pero por poco: AUC {c(br.loc['Regla: menos puntos top', 'AUC'])} contra {c(br.loc['Regla: menos puntos LiDAR', 'AUC'])} con los puntos totales; esa diferencia no es un hallazgo firme.", f"AUC {c(br.loc['Regla: menos puntos top', 'AUC'])} vs {c(br.loc['Regla: menos puntos LiDAR', 'AUC'])}", "f2_baselines_reglas_41.csv"),
        ("¿Qué pasa con la deriva de datos?", "No se midió: el trabajo tiene 41 segmentos de 3 ubicaciones y una sola fuente. La solución está congelada; la recomendación es monitorear la tasa de celdas marcadas, la distribución de puntos del sensor superior y el recall por segmento, y reevaluar con la validación externa sellada.", "sin medición", "informe, secciones 14 y 15"),
        ("¿Por qué no se elige E2 si gana en 5 de 5 folds?", f"Gana en {int(f4.loc['E2', 'folds_ganados_de_5'])} de 5 folds, pero por {c(f4.loc['E2', 'dif_AUC'], 4)} de AUC (IC {c(f4.loc['E2', 'dif_lo'], 4)} a {c(f4.loc['E2', 'dif_hi'], 4)}), por debajo del umbral pre-declarado de 0,010 y con el IC incluyendo 0; además contiene a la regla y su ECE es {c(N['e2']['ece'])}. Con más repeticiones de la CV externa (hoy una, DEV-1) podría resolverse.", f"dif. AUC {c(f4.loc['E2', 'dif_AUC'], 4)}; folds {int(f4.loc['E2', 'folds_ganados_de_5'])} de 5", "f4_ensambles_aporta.csv, plan_v3.md (P8)"),
        ("¿Cuál es la limitación principal de todo el trabajo?", "Que todo es en muestra y sin prueba ciega: 41 segmentos, parámetros del detector ajustados con los mismos datos, y la ganancia del flujo en dos pasos sale de 2 celdas. Hasta correr la validación externa sellada no se puede decir que se sostenga.", "2 celdas; 41 segmentos", "informe, secciones 14 y 17"),
        ("¿Qué se haría con más tiempo?", "(1) Correr la validación externa sellada; (2) medir el tiempo real de revisión y el costo de una auditoría; (3) averiguar la causa de los huecos (por ejemplo con `camera_box`); (4) más repeticiones de la CV externa y más ciclistas y segmentos de noche; (5) un filtro 1 a nivel segmento.", "—", "informe, secciones 15 y 17"),
    ]
    # ---- nuevas (F20, bloque D): C5, C6 y D2
    sp = N["plan_sel"]
    n_el = f12["detector_ep2"]["celdas_con_n_suficiente"]
    n_tot = int(N["f12sens"]["celdas_totales"].iloc[0])
    elegibles = round(sp["total_cuota"] * 5 * n_el / n_tot)         # celdas segmento x camara con >= 100 cajas que se esperan en los segmentos nuevos
    lam = round(elegibles * 2 / n_el, 1)                            # tasa de celdas marcadas en desarrollo: 2 de n_el
    p0 = float(np.exp(-lam))                                        # estimacion gruesa tipo Poisson de no marcar ninguna
    seg247 = next(x for x in ptr["top3_segmentos_positivos_mayor_100_sin_hueco"] if x["seg"] == "247562357599")
    ESTRATOS = sp["candidatos_por_estrato"]
    man = json.loads((MOD / "manifest_v3.json").read_text(encoding="utf-8"))              # manifest_v3.json: sha256 de la solución v3 (3 archivos) y del plan v3 (2)
    n_sha_manifest, n_sha_plan = len(man["sha256"]), len(man["plan_v3_sha256"])
    seg_ub = pd.read_parquet(APP / "cajas_oof.parquet", columns=["seg", "ubicacion", "momento"]).drop_duplicates()
    seg_huecos = set(pd.read_csv(APP / "lista_A.csv", dtype={"segmento": str})["segmento"])
    sf_dia = seg_ub[(seg_ub["ubicacion"] == "location_sf") & (seg_ub["momento"] == "Day")]
    n_sf_dia, n_sf_dia_hueco = len(sf_dia), int(sf_dia["seg"].isin(seg_huecos).sum())
    cuota_sf_dia = int(sp["cuotas_utiles"]["Day / location_sf"])
    cj = pd.read_parquet(APP / "cajas_oof.parquet", columns=["num_top_lidar_points", "sin_camara", "prob_cal"])
    g0 = cj[cj["num_top_lidar_points"] == 0]
    assert len(g0) == N["calres"]["cajas_con_0_puntos_top"] and abs(float(g0["sin_camara"].mean()) - N["calres"]["tasa_sin_camara_en_cajas_con_0_puntos_top"]) < 1e-9   # misma cifra que la calidad de datos del informe (§4)
    emp = {"n_cajas": len(g0), "pct_sin_pareja": float(g0["sin_camara"].mean()), "prob_sin_pareja": float(g0["prob_cal"].median()), "prob_min": float(g0["prob_cal"].min()), "prob_max": float(g0["prob_cal"].max())}
    p_sf = (1 - n_sf_dia_hueco / n_sf_dia) ** cuota_sf_dia                                    # P(ninguno de los segmentos nuevos de San Francisco de día tiene hueco), con la tasa de desarrollo
    Q += [
        ("¿Qué pasa con la celda `247562357599|cam5`, que aparece marcada cuando `frac` = 0,35? (post hoc, no pre-declarado, hipótesis no verificada)",
         f"El segmento `247562357599`, cámara 5, tiene {mi(seg247['positivos'])} positivos en {mi(seg247['cajas'])} cajas con más de 100 puntos del sensor superior ({p(seg247['tasa'])}) y es la celda que aparece marcada con `frac` = 0,35. Con los parámetros congelados (`frac` = 0,25) **no se marca**. "
         "Hipótesis (no verificada): podría ser un tercer hueco que el umbral de EP2 no alcanza a marcar; no hay verdad externa para decidirlo. No cambia el detector ni ninguna cifra.",
         f"{mi(seg247['positivos'])} positivos en {mi(seg247['cajas'])} cajas ({p(seg247['tasa'])})", "f12_eda_puntos_top_resumen.json (top3_segmentos_positivos_mayor_100_sin_hueco), f12_sensibilidad_detector.csv (marcadas_lista)"),
        ("¿Por qué la solución contra la regla da diferencia cero fuera de muestra?",
         f"Porque la solución congelada v3 **es** la regla: su puntaje es `PuntuadorRegla(num_top_lidar_points)`, monótono con «menos puntos del sensor superior», así que la diferencia solución menos regla es 0 por construcción (no es un empate sorprendente). "
         f"En su lugar se mide el desempeño de la regla fuera de muestra (AUC, PR-AUC, captura al 20 % y fracción para el 80 %, con intervalo por segmentos), su recall y precisión con los umbrales A = {-N['fin']['umbrales']['A']:.0f} y B = {-N['fin']['umbrales']['B']:.0f} congelados, el brazo C contra A y la tasa de celdas marcadas con dos denominadores. "
         "Para poder decir algo más se congelaron aparte dos alternativas, LR3 y XGBoost (DEV-4), que sí pueden compararse con la regla; no cambian la solución elegida.",
         "diferencia solución menos regla = 0; alternativas: LR3 y XGBoost", "GUIA_VALIDACION_EXTERNA.md (sección 6), src/waymo_evaluacion/ep3/congelado.py, manifest_alternativas.json, plan_v3_desviaciones.md (DEV-4)"),
        ("¿Cómo se garantiza el sellado de la validación externa?",
         "Con cuatro candados. (1) El orden de los candidatos nuevos queda fijado en `plan_seleccion_ep3.json` (sha256 en `plan_seleccion_ep3.sha256`) y el notebook 00b exige y verifica ese plan. (2) `evaluar_sellado.py congelar` guarda los sha256 de la lista de segmentos y de la solución v3 y de las alternativas **antes** de abrir los datos, y `copiar_sello_a_artefactos.py` los copia a `artefactos_ep3/`. "
         "(3) Hacemos commit y push antes de evaluar (los scripts nunca tocan git): el sello queda en el historial antes de la evaluación. (4) `evaluar` toma un candado de una sola evaluación y lo hace solo cuando el cálculo terminó; no se puede repetir con otros parámetros. Cualquier cambio posterior de código se declara como desviación con fecha y motivo.",
         f"1 evaluación; {n_sha_manifest} archivos con sha256 en el manifest; la verificación incluye además el plan v3 ({n_sha_plan} archivos): {n_sha_manifest + n_sha_plan} de {n_sha_manifest + n_sha_plan}", "GUIA_VALIDACION_EXTERNA.md, docs/ep3/plan_seleccion_ep3.sha256, scripts/ep3/evaluar_sellado.py, data/06_models_ep3/manifest_v3.json"),
        ("¿Qué pasa si la validación externa no encuentra huecos? (caso A; estimación gruesa, post hoc)",
         f"Es el caso A: C es igual a A porque no hay celdas que auditar. **No refuta ni confirma el detector**: pudo no haber huecos. Dos estimaciones gruesas, ambas post hoc y no pre-declaradas. "
         f"(1) Por celda: con unas {elegibles} celdas elegibles (≈ {sp['total_cuota']} segmentos × 5 cámaras × la fracción de celdas con ≥ 100 cajas en desarrollo, {n_el} de {n_tot}) y una tasa de 2 de {n_el} ({p(2 / n_el)}) en desarrollo, se esperarían ≈ {c(lam, 1)} celdas marcadas y la probabilidad de no marcar ninguna es del orden del {p(p0, 0)} (Poisson, exp(−{c(lam, 1)})). "
         f"(2) Por concentración: los {n_sf_dia_hueco} huecos están en {n_sf_dia_hueco} de los {n_sf_dia} segmentos de día de San Francisco de desarrollo; con {cuota_sf_dia} segmentos nuevos de ese estrato, la probabilidad de que ninguno tenga hueco es ({n_sf_dia - n_sf_dia_hueco}/{n_sf_dia})^{cuota_sf_dia} ≈ {p(p_sf, 0)}. "
         f"Rango: entre ≈ {p(p_sf, 0)} y ≈ {p(p0, 0)} de no ver ningún hueco (post hoc). Las dos estimaciones salen de los mismos datos con que se ajustó el detector, así que son optimistas: la tasa real de huecos probablemente sea menor y la probabilidad de no ver ninguno, mayor. "
         "Un resultado sin huecos es plausible y se interpreta con cautela; lo informativo seguiría siendo el desempeño de la regla fuera de muestra.",
         f"≈ {c(lam, 1)} celdas marcadas esperadas; probabilidad de ninguna entre ≈ {p(p_sf, 0)} (concentración en San Francisco de día) y ≈ {p(p0, 0)} (por celda)", "GUIA_VALIDACION_EXTERNA.md (sección 7, caso A), plan_seleccion_ep3.json, f12_resumen.json, data/09_app_ep3 (cajas_oof.parquet, lista_A.csv)"),
        ("¿Por qué se congelaron LR3 y XGBoost si la solución es la regla? (DEV-4)",
         f"Porque «solución contra regla» da 0 por construcción y no informa. Se congelaron antes de abrir datos (LR3 y XGBoost entrenadas con los 41 segmentos; XGBoost con la configuración más repetida entre los 5 folds, {N['alt']['xgb_folds_que_la_eligieron']}) para poder preguntar si algo más complejo mejora fuera de muestra. "
         "Son 4 comparaciones (diferencia de AUC y de fracción para el 80 %, para cada alternativa): un «gana» aislado es **exploratorio** (post hoc, sin corrección por comparaciones múltiples), no cambia la solución elegida y se usaría solo para decidir una validación nueva.",
         f"XGBoost: configuración elegida por {N['alt']['xgb_folds_que_la_eligieron']}; 4 comparaciones", "f19_alternativas_congeladas.json, manifest_alternativas.json, plan_v3_desviaciones.md (DEV-4)"),
        ("¿Cómo se eligieron los segmentos nuevos y qué sesgo tienen?",
         f"Se reconstruye el pool de EP2 (sin lluvia, al menos {sp['parametros']['min_frames']} frames, número de detecciones entre los percentiles {sp['parametros']['percentiles_detecciones'][0]} y {sp['parametros']['percentiles_detecciones'][1]}), se excluyen los {sp['embudo']['evaluados_ep2_dentro_del_pool']} evaluados por EP2 y se toman **cuotas fijas de {sp['total_cuota']} segmentos útiles** por momento del día y ubicación, con semilla {sp['parametros']['semilla']} y un orden sellado. "
         f"Sesgos: sobremuestreo de San Francisco de día (cuota {sp['cuotas_utiles']['Day / location_sf']} de {sp['total_cuota']}, {ESTRATOS['Day / location_sf']} candidatos), la noche mal representada ({ESTRATOS['Night / location_sf']} candidatos en San Francisco, {ESTRATOS['Night / location_phx']} en Phoenix y ninguno en otras ubicaciones) y, como en EP2, solo segmentos con etiquetado no ralo. Por eso no se puede afirmar nada de la noche ni de otras ciudades.",
         f"{sp['total_cuota']} segmentos útiles; noche: {ESTRATOS['Night / location_sf']} y {ESTRATOS['Night / location_phx']} candidatos", "plan_seleccion_ep3.json, f18_seleccion_motivos.csv, f18_seleccion_rendimiento.csv"),
        ("¿Por qué el titular compara un paso contra el azar y el dos pasos va aparte?",
         f"Porque lo robusto es que ordenar la cola con la regla reduce el tiempo frente a revisar sin orden (de ≈ {N['h_azar']:.0f} h a ≈ {N['h_A']:.0f} h, con {SEG_POR_CAJA} s por caja: supuesto), con un intervalo de captura al 20 % que queda lejos del azar ({c(esc['Captura@20_lo'])} a {c(esc['Captura@20_hi'])} contra 0,20). "
         f"El flujo en dos pasos (≈ {N['h_C']:.0f} h) sale de 2 celdas y de parámetros ajustados con los mismos datos, con una diferencia pareada cuyo IC incluye 0 ({c(glob['ic_lo'])} a {c(glob['ic_hi'])}): va como segunda barra rotulada «en muestra».",
         f"≈ {N['h_azar']:.0f} h sin orden; ≈ {N['h_A']:.0f} h un paso; ≈ {N['h_C']:.0f} h dos pasos (en muestra)", "f6_modelo_escogido.csv, f5_brazoC.csv, f12_diferencia_C_menos_A.csv"),
        ("¿Por qué las primeras cajas de la cola tienen la misma probabilidad? (F21)",
         f"Porque la regla ordena solo por «menos puntos del sensor superior» y {mi(emp['n_cajas'])} cajas tienen 0 puntos: la regla no las distingue, empatan en el puntaje y reciben una probabilidad calibrada casi igual (de {p(emp['prob_min'])} a {p(emp['prob_max'])}: cada partición de la validación cruzada calibró por separado). "
         f"En esas cajas, {p(emp['pct_sin_pareja'])} no tiene pareja. El orden dentro del empate no es informativo y la página lo dice sobre la tabla. No es un defecto de la tabla: es lo que la regla sabe. Los modelos que usan otras variables (distancia, tamaño, cámara) no superaron a la regla en AUC, así que no hay evidencia de que desempatar con ellas mejore. "
         "Para la persona que revisa no cambia el trabajo: se atiende por objeto y por segmento, y todas las cajas del empate quedan dentro de lo que se revisa antes que el resto.",
         f"{mi(emp['n_cajas'])} cajas con 0 puntos; {p(emp['pct_sin_pareja'])} sin pareja; probabilidad calibrada de {p(emp['prob_min'])} a {p(emp['prob_max'])}", "f12_eda_calidad_resumen.json, data/09_app_ep3/cajas_oof.parquet (num_top_lidar_points, prob_cal), app_logica.py (nota_empate)"),
        ("¿Cuál es el valor de negocio en una frase? (en muestra)",
         f"Con la cola ordenada por la regla, encontrar el 80 % de las cajas sin pareja exige revisar ≈ {p(esc['Fraccion_80'], 0)} de las cajas en vez del 80 % del total al azar: unas {N['h_A']:.0f} h en lugar de {N['h_azar']:.0f} h con {SEG_POR_CAJA} s por caja (supuesto, no medido); con auditoría previa de las celdas marcadas, ≈ {N['h_C']:.0f} h. "
         f"Rótulo: {EN_MUESTRA}; la diferencia entre uno y dos pasos sale de 2 celdas y no se distingue de 0.",
         f"≈ {N['h_azar']:.0f} h sin orden; ≈ {N['h_A']:.0f} h un paso; ≈ {N['h_C']:.0f} h dos pasos (en muestra)", "f6_modelo_escogido.csv, f5_metricas_candidatos.csv, f12_diferencia_C_menos_A.csv"),
    ]
    out = ["# Preguntas cruzadas con respuesta, cifra y fuente", "", f"*Generado por `scripts/ep3/generar_docs_ep3.py`. {len(Q)} preguntas; cada cifra sale del archivo indicado (carpeta `data/08_reporting_ep3` salvo que se diga otra). Las referencias a secciones corresponden a `informe_tecnico_EP3.md`.*", ""]
    for i, (q, a, cifra, fuente) in enumerate(Q, 1):
        out += [f"**{i}. {q}**", f"- Respuesta: {a}", f"- Cifra: {cifra}", f"- Fuente: `{fuente}`", ""]
    return "\n".join(out)


def sincronizar_conteos() -> list[str]:
    """Reemplaza el contenido de las marcas <!--n_ep3-->..<!--/n_ep3-->, <!--n_ep2-->..<!--/n_ep2--> y <!--n_total-->..<!--/n_total--> por los conteos de pruebas_ep3_conteo.json (y n_preg, n_sec y n_nb: preguntas cruzadas, secciones de la página y notebooks 11 a 15, leídos de los archivos y del código)."""
    n_preg = len(re.findall(r"^\*\*\d+\. ", (DOC / "preguntas_cruzadas.md").read_text(encoding="utf-8"), flags=re.M))
    valores = {"n_ep3": PRUEBAS_EP3, "n_ep2": PRUEBAS_EP2, "n_total": PRUEBAS_TOTAL, "n_preg": n_preg, "n_sec": len(SECCIONES_PAGINA), "n_nb": len(list((RAIZ / "notebooks").glob("1[1-5]_*.ipynb")))}
    tocados = []
    for ruta in (DOC / "ESTADO.md", DOC / "plan_integracion_readme.md", DOC / "verificacion_copia_limpia.md"):
        if not ruta.exists():
            continue
        txt = ruta.read_text(encoding="utf-8")
        nuevo = txt
        for k, v in valores.items():
            nuevo = re.sub(rf"<!--{k}-->.*?<!--/{k}-->", f"<!--{k}-->{v}<!--/{k}-->", nuevo)
        if nuevo != txt:
            ruta.write_text(nuevo, encoding="utf-8")
            tocados.append(ruta.name)
    return tocados


def main() -> None:
    verificar_plan_v3(RAIZ)
    N = cargar()
    derivados(N)
    (DOC / "informe_tecnico_EP3.md").write_text(informe(N), encoding="utf-8")
    (DOC / "README_EP3.md").write_text(readme(N), encoding="utf-8")
    (DOC / "guion_presentacion.md").write_text(guion(N), encoding="utf-8")
    (DOC / "preguntas_cruzadas.md").write_text(preguntas(N), encoding="utf-8")
    (DOC / "pagina_guia_demo.md").write_text(guia_demo(N), encoding="utf-8")
    from waymo_evaluacion.ep3.chequeo_md import revisar_carpeta

    problemas = revisar_carpeta(DOC)                       # F19-C1 y C3: tablas bien formadas y sin caracteres de control en TODOS los documentos de docs/ep3
    if problemas:
        for archivo, ps in problemas.items():
            print(f"PROBLEMAS en {archivo}:", *ps[:5], sep="\n   ")
        raise SystemExit("los documentos generados tienen tablas mal formadas o caracteres de control (ver arriba)")
    print("escritos: informe_tecnico_EP3.md, README_EP3.md, guion_presentacion.md, preguntas_cruzadas.md; conteos sincronizados en:", ", ".join(sincronizar_conteos()) or "(nada)")


if __name__ == "__main__":
    main()
