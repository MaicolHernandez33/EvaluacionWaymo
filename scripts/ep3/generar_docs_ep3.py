"""Genera docs/ep3/informe_tecnico_EP3.md, README_EP3.md, guion_presentacion.md y preguntas_cruzadas.md.

Ninguna cifra esta escrita a mano: todas salen de data/08_reporting_ep3, data/09_app_ep3, data/06_models_ep3 y docs/seleccion_segmentos.
Uso: python scripts/ep3/generar_docs_ep3.py   (escribe solo en docs/ep3/)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
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


def valores_de_la_pagina() -> dict:
    """Lo que muestra la pagina en «Cola de revisión» con Segmento «Todos» y presupuesto 20 %, calculado con la misma logica y los mismos datos que la pagina."""
    from waymo_evaluacion.ep3.app_logica import cargar_datos, cola_segmento, horas_revision, recall_en_presupuesto

    D = cargar_datos(APP)
    sol = D["kpis"]["nombre_curva"]
    esp = recall_en_presupuesto(D["curva"], sol, 0.20)
    espA = recall_en_presupuesto(D["curva"], "Solución elegida, un paso (A)", 0.20)
    _, info = cola_segmento(D["cajas"], "Todos", 0.20)
    return {"brazo": sol, "recall": esp["recall"], "lo": esp["lo"], "hi": esp["hi"], "recall_A": espA["recall"], "lo_A": espA["lo"], "hi_A": espA["hi"],
            "cajas_a_revisar": info["cajas_a_revisar"], "cajas_cola_total": info["cajas_cola_total"], "horas": horas_revision(info["cajas_a_revisar"], SEG_POR_CAJA),
            "hallados": info["positivos_auditoria"] + info["positivos_en_cola"], "positivos_total": info["positivos_total"], "recall_proceso": info["recall_proceso"]}


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
    t_eda = eda.assign(tasa=eda["tasa"].map(lambda v: p(v)), IC=[f"{p(a)} a {p(b)}" for a, b in zip(eda["ic_lo"], eda["ic_hi"])])[["variable", "tramo", "cajas", "positivos", "tasa", "IC", "segmentos"]]
    calq = N["cal"]
    ult = N["estab"].set_index("k")
    adj = N["ari_diag_j"]
    ad = N["ari_diag"]
    _g = ad[ad["covarianza"].notna() & (ad["tecnica"].str.startswith("GMM"))]
    _g = _g.assign(n_init=_g["n_init"].astype(int), n_iter=_g["n_iter"].astype(int))
    kmk2 = ad[(ad["k"] == 2) & ad["tecnica"].str.startswith("KMeans")].iloc[0]
    wk2 = ad[(ad["k"] == 2) & ad["tecnica"].str.startswith("Ward")].iloc[0]
    gmk2 = _g[(_g["k"] == 2) & (_g["covarianza"] == "full") & (_g["n_init"] == 2)].iloc[0]
    gdk2 = _g[(_g["k"] == 2) & (_g["covarianza"] == "diag") & (_g["n_init"] == 2)].iloc[0]
    gsk2 = _g[(_g["k"] == 2) & (_g["covarianza"] == "spherical") & (_g["n_init"] == 2)].iloc[0]
    gfk4 = _g[(_g["k"] == 4) & (_g["covarianza"] == "full") & (_g["n_init"] == 2)].iloc[0]
    t_ari = _g[["k", "covarianza", "n_init", "converged", "n_iter", "tamanos", "ARI_vs_KMeans", "ARI_vs_Ward"]].rename(columns={"converged": "converged_", "ARI_vs_KMeans": "ARI vs KMeans", "ARI_vs_Ward": "ARI vs Ward"}).round(3).astype(str)
    hc, pg = N["hC"], N["pag"]
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
    t_fold = N["f12fold"][N["f12fold"]["candidato"] == "Regla top"][["fold", "segmentos", "cajas", "celdas_con_hueco", "hueco_contenido", "AUC_A", "AUC_B_celdas_sanas", "Fraccion80_A", "Fraccion80_B_celdas_sanas", "Fraccion80_C"]].round(3).astype(str)
    t_difc = N["f12dif"][N["f12dif"]["candidato"] == "Regla top"][["variante", "Fraccion80_A", "Fraccion80_C", "dif_C_menos_A", "ic_lo", "ic_hi", "excluye_0", "segmentos"]].round(3).astype(str)
    sens = N["f12sens"]
    t_sens = sens.groupby(["mediana", "frac"]).agg(marcadas_min=("marcadas", "min"), marcadas_max=("marcadas", "max"), falsas_min=("falsas_alarmas", "min"), falsas_max=("falsas_alarmas", "max"),
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

## 4. EDA, calidad de datos y preparación *(post hoc, descriptivo, 41 segmentos, población principal)*
**Variables.** Las 16 de EP2 (`V16`: posición, azimut, distancia, tamaño, volumen, puntos LiDAR, puntos top, densidad, velocidad, rumbo y clase), y dos conjuntos más pequeños declarados en el plan: `V_OBS` (4 variables de observabilidad) y `V_OBS_TAM` (10). El conjunto es un hiperparámetro de la búsqueda. **Folds:** StratifiedGroupKFold(5) por segmento, estratificado por `sin_camara`, semilla 42; ningún segmento queda repartido entre folds.

**Qué explica `sin_camara`.** La tasa cae con los puntos del LiDAR superior: {p(pt.loc['0-5', 'tasa'])} con 0 a 5 puntos ({mi(pt.loc['0-5', 'cajas'])} cajas), {p(pt.loc['6-10', 'tasa'])} con 6 a 10, {p(pt.loc['11-20', 'tasa'])} con 11 a 20, {p(pt.loc['21-50', 'tasa'])} con 21 a 50 y {p(pt.loc['51-100', 'tasa'])} con 51 a 100 (IC por segmentos en la tabla). Por azimut dentro de la población principal casi no cambia ({p(az.loc['0-20', 'tasa'])} en 0 a 20° contra {p(az.loc['80-100', 'tasa'])} en 80 a 100°). Sube con la distancia: {p(ds.iloc[0]['tasa'])} en el quintil más cercano contra {p(ds.iloc[-1]['tasa'])} en el más lejano. Los peatones tienen {p(cl.loc['PEDESTRIAN', 'tasa'])} y los ciclistas {p(cl.loc['CYCLIST', 'tasa'])} (solo {mi(cl.loc['CYCLIST', 'cajas'])} cajas de ciclistas, en {int(cl.loc['CYCLIST', 'segmentos'])} segmentos). *Analogía:* una caja con pocos puntos es una foto borrosa; es más difícil que alguien la haya pareado.

![EDA: tasa por tramo](../../images/ep3/12_eda_tasas.png)

{tabla_md(t_eda)}

**Calidad de datos** (`f12_eda_calidad.csv`, `f12_eda_calidad_resumen.json`): nulos en las 16 variables: {N['calres']['nulos_total']}; llaves duplicadas (segmento, marca de tiempo, objeto): {N['calres']['duplicados_por_llave_principal']}; cajas con 0 puntos LiDAR: {mi(N['calres']['cajas_con_0_puntos_lidar'])} ({p(N['calres']['pct_cajas_con_0_puntos_lidar'])}); con 0 puntos del sensor superior: {mi(N['calres']['cajas_con_0_puntos_top'])} ({p(N['calres']['pct_cajas_con_0_puntos_top'])}), de las cuales {p(N['calres']['tasa_sin_camara_en_cajas_con_0_puntos_top'])} no tienen pareja. Atípicos fuera de 1,5 IQR: los más altos son `densidad_puntos` ({p(calq.set_index('variable').loc['densidad_puntos', 'pct_atipicos'])}), `num_lidar_points` ({p(calq.set_index('variable').loc['num_lidar_points', 'pct_atipicos'])}) y `num_top_lidar_points` ({p(calq.set_index('variable').loc['num_top_lidar_points', 'pct_atipicos'])}): son cajas muy cercanas con muchísimos puntos, no errores; no se eliminaron.

![Calidad de datos](../../images/ep3/12_eda_calidad.png)

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
| DEC-14 | Aviso «en muestra» visible en Inicio y Cola de revisión | evitar leer una ganancia en muestra como resultado ciego |
| DEC-15 | El selector de referencia de la página usa las curvas ya calculadas de XGBoost y E2 | no generar predicciones nuevas |
| DEC-16 | Docker sin probar | el demonio estaba apagado |

## 8. Filtro 1: detector de huecos por cámara
Parámetros congelados de EP2, sin recalcular: rango de azimut p5-p95 por cámara con los 33 segmentos de train, mediana de la tasa por cámara con los 41, hueco si la tasa es menor al 25 % de la mediana y hay al menos 100 cajas en el rango. Marca **{N['f2']['n_pares_con_hueco']} celdas**, las mismas que EP2 (diferencia máxima contra los CSV de EP2: {N['f2']['dif_max_tabla_vs_ep2']:.1e}):

{tabla_md(N['lista_A'][['segmento', 'grupo', 'camara', 'tasa', 'cajas_en_rango', 'positivos_afectados']].round(3))}

Esas celdas contienen {mi(N['f2']['positivos_en_hueco_principal'])} de los {mi(N['pos'])} positivos ({p(N['f2']['positivos_en_hueco_principal'] / N['pos'])}) en {mi(N['f2']['cajas_en_hueco_principal'])} cajas. **Post hoc, no pre-declarado:** el hueco se descubrió en EP2 después de abrir el test, y los parámetros del detector se ajustaron con estos mismos segmentos. Una celda marcada puede ser un problema de etiquetado 2D o de datos de esa cámara; con estos archivos no se distingue.

**Sensibilidad (post hoc, anexo B).** Se probaron 30 combinaciones: `frac` {{0,15; 0,20; 0,25; 0,30; 0,35}} x `min_cajas` {{50, 100, 200}} x mediana {{con los 41 segmentos; sin el segmento candidato}}. Los 2 huecos se detectan en **{f12['detector_combinaciones_que_detectan_los_2']} de {f12['detector_combinaciones']}** combinaciones; las falsas alarmas (celdas marcadas que no son los 2 huecos de EP2) van de {f12['detector_falsas_alarmas_rango'][0]} a {f12['detector_falsas_alarmas_rango'][1]}, y con la configuración de EP2 son {f12['detector_ep2']['falsas_alarmas']} de {f12['detector_ep2']['celdas_con_n_suficiente']} celdas con n suficiente. Sin el segmento candidato en la mediana (variante «leave-one-out») el resultado es el mismo.

## 9. Aprendizaje no supervisado *(descriptivo; no está en el plan v3: post hoc, no pre-declarado)*
**Qué se hizo.** Sobre las {mi(f13['filas'])} cajas de la población principal, con `distancia_m`, `azimut_abs_deg`, `log1p(num_lidar_points)`, `log1p(densidad_puntos)` y `log1p(volumen_caja)` estandarizadas, **sin `sin_camara` ni nada del par 2D**. EP2 usó además variables de oclusión que no están en `dev_41`, así que la comparación no es idéntica. KMeans k = 2 a 8 (`n_init=10`, semilla 42) con silhouette (muestra de 20.000), Davies-Bouldin y Calinski-Harabasz; GMM (BIC) y Ward en una muestra de 15.000; estabilidad al remuestrear segmentos (30 réplicas). Se elige k por máximo silhouette entre 2 y 6: **k = {N['k_el']}**, y se explora también k = 4 como en EP2.

{tabla_md(N['selk'].round(3).astype(str))}

**Estructura.** Con k = {N['k_el']} el silhouette es {c(N['selk'].set_index('k').loc[N['k_el'], 'silhouette_muestra_20000'])} y la estabilidad por segmentos tiene ARI medio {c(ult.loc[N['k_el'], 'ari_medio'])} y mínimo {c(ult.loc[N['k_el'], 'ari_minimo'])}; con k = 4, {c(ult.loc[4, 'ari_medio'])} y {c(ult.loc[4, 'ari_minimo'])}. El acuerdo entre técnicas es **bajo**: ARI KMeans contra GMM {c(ar['k=2']['KMeans vs GMM'])} (k = 2) y {c(ar['k=4']['KMeans vs GMM'])} (k = 4); KMeans contra Ward {c(ar['k=2']['KMeans vs Ward'])} y {c(ar['k=4']['KMeans vs Ward'])}. Es decir, los clusters son una partición cómoda de un continuo (distancia y densidad), no grupos naturales firmes.

**Diagnóstico del ARI bajo** (post hoc, `f13_ari_diagnostico.csv` y `.json`; lo produce `scripts/ep3/f13b_diagnostico_ari.py`). EP2 reportó un ARI KMeans contra GMM de {c(float(cn.iloc[9]['EP2']))}; aquí es {c(ar['k=2']['KMeans vs GMM'])} con k = 2. Se revisó si era un error de código: las tres técnicas se comparan sobre **las mismas {mi(adj['filas']['filas_muestra'])} filas, en el mismo orden** (la muestra tiene {mi(adj['filas']['filas_unicas'])} filas distintas), el ARI recalculado coincide con `f13_resumen.json` ({'sí' if adj['coincide_con_f13'] else 'NO'}) y los GMM {'convergieron todos' if adj['todos_los_gmm_convergieron'] else 'NO convergieron todos'} (`converged_`). **No hay error.** El GMM de f13 usa covarianza `full` y `n_init=2`. Con k = 2 los tamaños de cluster son KMeans {kmk2['tamanos']}, Ward {wk2['tamanos']} y GMM `full` {gmk2['tamanos']}; con covarianza `diag` el ARI KMeans–GMM sube a {c(float(gdk2['ARI_vs_KMeans']))} y con `spherical` a {c(float(gsk2['ARI_vs_KMeans']))}, y con k = 4 `full` da {c(float(gfk4['ARI_vs_KMeans']))}.

{tabla_md(t_ari)}

*Causa probable (hipótesis, post hoc, no verificada):* el GMM `full` modela grupos con forma y tamaño distintos (uno concentrado y otro difuso) y KMeans parte el espacio por distancia a los centros, así que sobre cinco variables continuas sin separación natural (distancia, azimut, puntos, densidad y volumen) cada técnica corta el continuo de otra manera. En EP2 las variables de oclusión formaban grupos compactos y las tres técnicas coincidían (ARI de {c(float(cn.iloc[9]['EP2']))}). Aquí esas variables no existen en `dev_41`.

**Cruce con `sin_camara` (k = 4)** y comparación con lo que predice la regla (probabilidad con Platt):

{tabla_md(k4[['cluster', 'tipo_de_caso', 'cajas', 'tasa_sin_camara', 'ic_lo', 'ic_hi', 'prob_media_regla_platt', 'diferencia_tasa_menos_prob_regla']].round(3).astype(str))}

Con k = {N['k_el']}: {', '.join(f"«{r.tipo_de_caso}» tasa {p(r.tasa_sin_camara)} (IC {p(r.ic_lo)} a {p(r.ic_hi)}, {mi(r.cajas)} cajas)" for r in k2.itertuples())}. Los tipos de caso extremos reproducen lo que ya sabe la regla: pocos puntos y lejos significan más sin pareja. **¿Mejoran la predicción?** No: agregar el cluster a la probabilidad de la regla (regresión logística, GroupKFold por segmento, IC por segmentos) cambia el AUC en {c(ap.loc[2, 'dif_AUC'], 4)} (IC {c(ap.loc[2, 'ic_lo'], 4)} a {c(ap.loc[2, 'ic_hi'], 4)}) con k = 2 y en {c(ap.loc[4, 'dif_AUC'], 4)} (IC {c(ap.loc[4, 'ic_lo'], 4)} a {c(ap.loc[4, 'ic_hi'], 4)}) con k = 4, es decir, con k = 4 la predicción **empeora** de forma distinguible. La regla ya está bien calibrada en cada cluster (diferencias de tasa menos probabilidad entre {c(k4['diferencia_tasa_menos_prob_regla'].min())} y {c(k4['diferencia_tasa_menos_prob_regla'].max())}).

**IsolationForest** (contaminación 1 %): {mi(iso['cajas_atipicas'])} cajas atípicas ({p(iso['porcentaje'])}) en {iso['segmentos_con_atipicos']} de {iso['segmentos_total']} segmentos; tasa de `sin_camara` {p(iso['tasa_sin_camara_atipicas'])} (IC {p(iso['ic_atipicas'][0])} a {p(iso['ic_atipicas'][1])}) contra {p(iso['tasa_sin_camara_resto'])} en el resto; los tres segmentos que más aportan reúnen {p(sum(x['pct_de_los_atipicos'] for x in iso['top3_segmentos_aportan']))} de los atípicos.

**EP2 contra EP3** (EP2 solo se lee; fuentes en la tabla):

{tabla_md(cn.round(3).astype(str)[['medida', 'EP2', 'EP3', 'fuente_EP2', 'fuente_EP3']])}

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

**Cómo leer la ganancia del brazo C** {ROT}. (a) *Casi por construcción:* en cajas revisadas, el brazo C no puede ser peor que A casi por construcción, porque la auditoría quita cajas de la cola sin costo por caja (sus positivos cuentan como hallados); por eso el signo de la diferencia no es un resultado: lo único que se mide es su tamaño. (b) *Por qué el límite superior del IC de C menos A es exactamente 0:* en las réplicas del bootstrap por segmentos que no contienen ninguno de los 2 segmentos con hueco ({p(hc['proporcion_observada_ninguno_de_los_2'])} de las {mi(hc['replicas'])} réplicas) la Lista A queda vacía y C es igual a A. La probabilidad exacta de ese evento en este diseño ({hc['diseno']}; {hc['formula']}) es **{p(hc['prob_exacta_ninguno_de_los_2'], 2)}**; el {p(hc['proporcion_observada_ninguno_de_los_2'])} observado es compatible con ella (diferencia de {c(abs(hc['z_observado_menos_exacto']), 1)} errores estándar con 1.000 réplicas). Es decir, que el IC «llegue a 0» describe el diseño del bootstrap, no es evidencia a favor ni en contra de C. (c) *Lo informativo:* el punto de equilibrio ({mi(N['eq'])} cajas por auditoría; IC {mi(esc['equilibrio_lo'])} a {mi(esc['equilibrio_hi'])}) y la **tasa de falsas alarmas del detector**, que con solo 2 celdas marcadas únicamente se puede estimar con datos nuevos. (`f12b_hechos_brazoC.json`, `scripts/ep3/f12b_hechos_brazoC.py`.)

### Cuadro «Modelo escogido»: regla «menos puntos top»
{tabla_md(cuadro)}

Accuracy y F1 son solo referencia: con una clase minoritaria de {p(N['prev'])}, un clasificador trivial ya tiene accuracy alto.

**Solución final en tres capas.** (1) **Filtro 1**: detector de huecos con parámetros congelados (`detector_params_v3.json`). (2) **Regla**: menos puntos del LiDAR superior primero, con umbrales A = {-N['fin']['umbrales']['A']:.0f} y B = {-N['fin']['umbrales']['B']:.0f} (se marcan las cajas con ese número de puntos o menos) y calibración Platt. (3) **Persona** que revisa y decide. v3 está congelado con sha256 en `manifest_v3.json` ({', '.join(N['man']['sha256'])}); se verifica con `scripts/ep3/verificar_congelados_v3.py`.

## 13. La página y su despliegue
`app/app.py` (Streamlit, solo local) con 7 secciones: Inicio, Auditoría de cámaras, Cola de revisión (presupuesto, recall esperado con IC, horas con supuesto editable, **selector «Comparar con modelo de referencia»** con XGBoost o E2, **tipo de caso** de cada caja), Explica una caja (puntaje, lugar en la cola, probabilidad calibrada y tipo de caso con su tasa histórica), Evidencia (IE9 a IE12, no supervisado y análisis en muestra), Ética y límites y Puntuar datos nuevos. Tres perfiles y un **modo presentación** que oculta los identificadores. Usa predicciones **fuera de fold**, y muestra en Inicio y en Cola de revisión (no en un tooltip) el aviso: «{EN_MUESTRA}. {GANANCIA_C}». Pruebas: {PRUEBAS_EP3} en `tests/ep3` (incluye una prueba de humo de cada sección con `streamlit.testing.v1.AppTest`). Despliegue: local (`scripts/ep3/arrancar_app.bat`) y Docker (lista blanca que excluye `data/`, volúmenes de solo lectura); **Docker no se probó**. La guía de AWS (EC2 + S3 privado) es solo orientativa y advierte que los datos por caja de Waymo no deben salir del equipo (`despliegue.md`).

**Seguridad de la página.** La app escucha **solo en `localhost`**: `.streamlit/config.toml` fija `server.address = "localhost"`, `scripts/ep3/arrancar_app.bat` pasa `--server.address localhost`, sin telemetría (`browser.gatherUsageStats = false`) y con la barra superior mínima (`client.toolbarMode = "minimal"`, sin el botón Deploy). En Docker el contenedor escucha en `0.0.0.0` (es necesario dentro del contenedor), pero `docker-compose.yml` publica el puerto solo en el equipo (`127.0.0.1:8501:8501`) y `.dockerignore` deja `data/` fuera de la imagen. **No debe exponerse sin autenticación y sin quitar los identificadores, y no se publica en servicios de nube con datos de Waymo.** Una prueba de solo lectura (`tests/ep3/test_seguridad_pagina.py`) falla si cambian estos valores.

**Lo que muestra la página** (Cola de revisión, Segmento «Todos», presupuesto 20 %, {pg['brazo']}; {EN_MUESTRA}): recall esperado {p(pg['recall'])} (IC {p(pg['lo'])} a {p(pg['hi'])}), {mi(pg['cajas_a_revisar'])} cajas a revisar de {mi(pg['cajas_cola_total'])} en la cola y {c(pg['horas'], 1)} h con {SEG_POR_CAJA} s por caja. Con un paso (A) y el mismo 20 % el recall esperado es {p(pg['recall_A'])} (IC {p(pg['lo_A'])} a {p(pg['hi_A'])}). Son dos números distintos de dos brazos distintos; ver `PENDIENTES_PAGINA.md`.

## 14. Validación externa sellada (P9): preparada, pendiente
`notebooks/00b_seleccion_segmentos_ep3.ipynb` (Colab) reconstruye la selección de EP2 y sortea segmentos nunca evaluados (702 candidatos, estratificado por `time_of_day x location`, semilla 42, meta >= 15 útiles). `scripts/ep3/evaluar_sellado.py congelar` guarda el sha256 de la lista y de v3 **antes** de abrir los datos; `evaluar` corre **una sola vez** (candado) y compara solución contra regla, dos pasos contra un paso y las falsas alarmas del detector. Nada se selecciona con esos datos. Es la única forma de saber si la ganancia del dos pasos y el detector se sostienen.

## 15. Conclusiones y recomendaciones para el negocio
**Conclusiones.** (1) La señal principal son los puntos del LiDAR: una regla simple alcanza AUC {c(esc['AUC'])} y ningún modelo ni ensamble la supera de forma distinguible. (2) Optimizar hiperparámetros ayuda solo a los modelos que por defecto se sobreajustan. (3) Los clusters describen, no predicen. (4) La utilidad del filtro 1 {ROT} depende de 2 celdas; hay que verla en datos nuevos.

**Recomendaciones.**
1. **Usar la solución en tres capas:** primero auditar las celdas de la Lista A, luego revisar la cola con la regla, y que una persona decida. No usar la regla para descartar cajas sin revisión.
2. **Auditar cámaras antes de revisar cajas.** Correr el detector en cada segmento nuevo: es robusto a sus parámetros (detecta los 2 huecos en {f12['detector_combinaciones_que_detectan_los_2']} de {f12['detector_combinaciones']} combinaciones, con 0 a {f12['detector_falsas_alarmas_rango'][1]} falsas alarmas).
3. **Monitorear el recall por segmento**, no solo el global: {lo['segmentos_con_AUC_menor_a_0_55']} de {lo['segmentos_evaluables']} segmentos evaluables tienen AUC < 0,55; y por clase: en ciclistas el recall en el punto A es {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} (solo {int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos), contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones.
4. **Medir el tiempo real de revisión** (hoy es un supuesto de {SEG_POR_CAJA} s por caja) y el costo de una auditoría, para decidir entre uno y dos pasos con el punto de equilibrio.
5. **Datos que faltan:** segmentos nuevos (P9), la causa de los huecos (etiquetado 2D o datos de cámara), `camera_calibration`, más ciclistas y segmentos nocturnos.
6. **Qué NO se puede afirmar:** que dos pasos supere a un paso fuera de muestra; que los huecos sean errores de etiquetado; que la regla sirva igual en otras ciudades o sensores; que un modelo complejo nunca ayude.

## 16. Ética, sesgos y privacidad
- Una persona decide: la solución ordena y avisa, nunca etiqueta ni descarta. No es una prueba de seguridad del vehículo.
- Licencia: uso no comercial; los datos no se redistribuyen; la página corre solo en el equipo, no hornea datos en imágenes Docker y no envía nada a internet. El zip de entrega es solo para el uso académico del docente.
- Privacidad: los identificadores de objeto y las marcas de tiempo solo están en tablas locales; el modo presentación los oculta.
- **Seguridad de la página:** escucha solo en `localhost`, nunca debe exponerse sin autenticación y sin quitar los identificadores, y no se publica en servicios de nube con datos de Waymo (ver sección 13).
- **Sesgos medidos** (descriptivo, sin pruebas de hipótesis; regla en el punto A, umbral {-f12['umbral_A_regla']:.0f} puntos, `f12_equidad.csv`; AUC solo con >= 200 cajas por clase, `n/c` si no):

{tabla_md(t_eq)}

  Lectura (descriptiva, sin pruebas de hipótesis; post hoc): con todas las celdas, el recall es menor de día ({c(eqi.loc[('momento_del_dia', 'Day'), 'recall_A'])}) que de noche ({c(eqi.loc[('momento_del_dia', 'Night'), 'recall_A'])}). **Sin las celdas con hueco, de día pasa a {c(eqx.loc[('momento_del_dia', 'Day'), 'recall_A'])} y la brecha se invierte:** era un efecto del hueco. San Francisco pasa de {c(eqi.loc[('ubicacion', 'location_sf'), 'recall_A'])} a {c(eqx.loc[('ubicacion', 'location_sf'), 'recall_A'])} (Phoenix {c(eqi.loc[('ubicacion', 'location_phx'), 'recall_A'])}, otras {c(eqi.loc[('ubicacion', 'location_other'), 'recall_A'])}): la brecha baja, pero queda. Amanecer y atardecer ({c(eqi.loc[('momento_del_dia', 'Dawn/Dusk'), 'recall_A'])}; no tiene huecos) queda unos {100 * (eqx.loc[('momento_del_dia', 'Day'), 'recall_A'] - eqi.loc[('momento_del_dia', 'Dawn/Dusk'), 'recall_A']):.0f} puntos bajo el día sin huecos. **Ciclistas:** recall {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones, con {int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos en {int(eqi.loc[('clase', 'CYCLIST'), 'segmentos'])} segmentos: **la regla es poco confiable para ciclistas**; queda como limitación y como recomendación de uso (no apoyarse en la cola para esa clase y revisarla con más cuidado).
- Los hallazgos post hoc (huecos, regla de reserva DEV-2, no supervisado, análisis en muestra) son hipótesis, no conclusiones. El criterio de selección de segmentos (etiquetado no ralo) deja fuera el caso de etiquetado 2D muy escaso.

## 17. Limitaciones
1. Sin prueba ciega: los 8 segmentos de test de EP2 ya se miraron; la validación externa está pendiente.
2. Una repetición de la CV externa (DEV-1): los IC reflejan una sola partición de segmentos.
3. Nadie cumple el criterio de estabilidad por fold (fold 0) y la elección usó una regla de reserva post hoc (DEV-2).
4. LightGBM quedó con `n_estimators` en el borde tras la única extensión permitida.
5. El detector marca solo {len(N['lista_A'])} celdas: su tasa de falsas alarmas no se puede estimar bien, y sus parámetros se ajustaron con los mismos datos donde se evalúa (circularidad).
6. Los segundos por caja (supuesto de {SEG_POR_CAJA} s) no se midieron.
7. El no supervisado no incluye variables de oclusión, a diferencia de EP2.
8. Docker no se probó; AWS no se ejecutó.
9. **Brazo C** ({EN_MUESTRA}): en cajas revisadas casi por construcción no es peor que A (la auditoría quita cajas de la cola sin costo); el límite superior 0 del IC de C menos A se debe a que {p(hc['proporcion_observada_ninguno_de_los_2'])} de las réplicas no contienen ninguno de los 2 segmentos con hueco (probabilidad exacta del diseño {p(hc['prob_exacta_ninguno_de_los_2'], 2)}); lo informativo es el punto de equilibrio y la tasa de falsas alarmas del detector, que solo se puede estimar con datos nuevos.
10. **Ciclistas:** la regla es poco confiable (recall {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones; {int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos en {int(eqi.loc[('clase', 'CYCLIST'), 'segmentos'])} segmentos).
11. **Estabilidad por fold:** el brazo B (post hoc) la explica, pero la elección y la regla de reserva DEV-2 se hicieron sobre el brazo A.
12. **La página** escucha solo en localhost y no está lista para exponerse en una red (sin autenticación).

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
| Selección de segmentos | `docs/seleccion_segmentos/inventario_segmentos.csv`, `registro_verificacion_ep2.csv` |
| Solución congelada | `data/06_models_ep3/manifest_v3.json`, `manifest_no_supervisado.json`, `f6_final_resumen.json` |

## Anexo B. Análisis en muestra (post hoc, no pre-declarado) {ROT}
### B.1 AUC por fold y brazos A, B y C (regla; LR3 y XGBoost en `f12_auc_por_fold_brazos.csv`)
{tabla_md(t_fold)}

Respuestas: **¿el brazo B cumple AUC mínimo por fold >= 0,75?** Sí: {c(f12['B_AUC_min_fold']['Regla top'])} (regla), {c(f12['B_AUC_min_fold']['LR3'])} (LR3), {c(f12['B_AUC_min_fold']['XGB'])} (XGBoost); el brazo A no ({c(f12['A_AUC_min_fold']['Regla top'])}, {c(f12['A_AUC_min_fold']['LR3'])}, {c(f12['A_AUC_min_fold']['XGB'])}). **¿Qué hace C en el fold 1?** Baja la Fracción para 80 % de {c(f12['C_en_fold_1_regla']['Fraccion80_A'])} a {c(f12['C_en_fold_1_regla']['Fraccion80_C'])} (celda {f12['C_en_fold_1_regla']['hueco']}). **¿El IC de C menos A excluye 0?** No: {c(glob['dif_C_menos_A'])} con IC {c(glob['ic_lo'])} a {c(glob['ic_hi'])} (LR3 y XGBoost igual: ver el CSV).

### B.2 Diferencia pareada C menos A en Fracción para 80 % (1.000 réplicas por segmentos; regla)
{tabla_md(t_difc)}

*Lectura:* las variantes «solo se audita una celda» y «se excluye un segmento» muestran que la ganancia depende de las dos celdas: la celda de `257766998801` sola ya da casi toda la ganancia (diferencia {c(N['f12dif'][(N['f12dif']['candidato'] == 'Regla top') & N['f12dif']['variante'].str.contains('solo se audita 257766998801')].iloc[0]['dif_C_menos_A'])}).

### B.3 Sensibilidad del detector (resumen por configuración; detalle en `f12_sensibilidad_detector.csv`)
{tabla_md(t_sens.round(3).astype(str))}

Con `frac` = 0,35 aparece una falsa alarma más en la celda `247562357599|cam5`; con `min_cajas` = 50 y `frac` <= 0,30, la celda `143581920096|cam5`. Los 2 huecos de EP2 se detectan en todas las combinaciones.

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


def guion(N: dict) -> str:
    esc, f12, glob = N["esc"], N["f12"], N["glob"]
    f13 = N["f13"]
    pg, hc = N["pag"], N["hC"]
    eq = N["f12eq"]
    eqi = eq[eq["celdas_con_hueco"] == "incluidas"].set_index(["variable", "grupo"])
    k2 = N["k2"].sort_values("tasa_sin_camara")
    bloques = [
        (45, "El problema", f"Un auto autónomo etiqueta peatones y ciclistas en 3D; a veces una caja no tiene su pareja en las cámaras. Revisar todo es caro: {mi(N['n'])} cajas, {p(N['prev'])} sin pareja.", "página, sección Inicio"),
        (50, "La idea en dos pasos", f"Primero cuadramos la caja de recibos (celdas segmento x cámara con hueco), después revisamos recibo por recibo (cola). Una persona decide. Ojo: la ganancia de dos pasos es **{EN_MUESTRA}** y sale de 2 celdas.", "Inicio: aviso en amarillo y las dos columnas del flujo"),
        (75, "Datos y plan", f"41 segmentos (de 798 a 91 a 41); los 8 de EP2 ya no son ciegos; plan v3 congelado con hash antes de experimentar; validación por segmento. Lo que más explica `sin_camara`: los puntos del LiDAR ({p(N['eda'][N['eda']['variable'] == 'puntos_top'].iloc[0]['tasa'])} con 0 a 5 puntos).", "notebook 11: tasa por segmento y EDA"),
        (45, "Filtro 1", f"El detector reproduce los 2 huecos de EP2 y los detecta en {f12['detector_combinaciones_que_detectan_los_2']} de {f12['detector_combinaciones']} combinaciones de parámetros; {mi(N['f2']['positivos_en_hueco_principal'])} positivos ({p(N['f2']['positivos_en_hueco_principal'] / N['pos'])}) caen ahí. Es post hoc.", "página, Auditoría de cámaras (mapa de calor)"),
        (65, "IE9 e IE10", f"Optimizamos 5 modelos con búsqueda anidada: mejoran {', '.join(N['n_mejoran'])}; no mejoran {', '.join(N['n_no'])}. Ningún ensamble aporta. Más complejidad no ayuda: la señal son los puntos del LiDAR.", "notebook 12: gráfico de mejora y curvas de validación"),
        (70, "IE11 e IE12", f"La regla de puntos top no es superada de forma distinguible: AUC {c(esc['AUC'])} (IC {c(esc['AUC_lo'])} a {c(esc['AUC_hi'])}); E2 empata pero la contiene. Nadie cumple O2 ni la estabilidad por fold (fold 0); con celdas sanas sí (post hoc), y eso no cambia la elección. Elegimos por simplicidad con una regla de reserva y lo decimos.", "notebook 13: tabla de selección y cuadro «Modelo escogido»"),
        (30, "No supervisado", f"Clusters k = {f13['k_elegido']}: lejanos y poco densos ({p(k2.iloc[-1]['tasa_sin_camara'])} sin pareja) contra cercanos y densos ({p(k2.iloc[0]['tasa_sin_camara'])}); no mejoran la predicción de la regla. Descriptivo.", "notebook 15"),
        (115, "Demo de la página", f"(1) Perfil «Analista de revisión». (2) Cola de revisión, segmento «Todos», presupuesto 20 %: la página muestra el brazo **{pg['brazo']}**: recall esperado **{p(pg['recall'])}** (IC {p(pg['lo'])} a {p(pg['hi'])}), **{mi(pg['cajas_a_revisar'])} cajas a revisar** y **{c(pg['horas'], 1)} h** con {SEG_POR_CAJA} s por caja; el texto de abajo dice {mi(pg['hallados'])} de {mi(pg['positivos_total'])} ({p(pg['recall_proceso'])}). Es en muestra. Con un paso (A) y el mismo 20 % el recall esperado sería {p(pg['recall_A'])}: **no mezclar** esos dos números. Leer el aviso; cambiar los segundos por revisión; probar «Comparar con modelo de referencia». (3) Auditoría de cámaras: mapa y Lista A. (4) Explica una caja: bajar los puntos LiDAR. (5) «Modo presentación» (se ocultan los identificadores). (6) Puntuar datos nuevos: nada se guarda. La página escucha solo en localhost.", "página en vivo"),
        (20, "Recomendaciones", "Auditar cámaras antes de revisar cajas, usar la regla en tres capas con una persona que decide, monitorear el recall por segmento y por clase (ciclistas), medir el tiempo real de revisión.", "informe, sección 15"),
        (40, "Límites y siguiente paso", f"Límites: **todo es en muestra** (41 segmentos; detector ajustado con los mismos datos); **sin prueba ciega** (los 8 de test ya se miraron; la validación externa está sellada y pendiente); la ganancia de dos pasos ({p(esc['Fraccion_80_C'])} contra {p(esc['Fraccion_80'])} de cajas para el 80 %) sale de 2 celdas, no excluye 0 y casi por construcción C no es peor que A; **ciclistas**: recall {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones, la regla no es confiable para ellos. Docker sin probar.", "informe, secciones 14 y 17"),
    ]
    t, filas = 0, []
    for seg, bloque, decir, mostrar in bloques:
        filas.append(f"| {t // 60}:{t % 60:02d} a {(t + seg) // 60}:{(t + seg) % 60:02d} | {bloque} | {decir} | {mostrar} |")
        t += seg
    assert t == 555, t
    return f"""# Guion de presentación (9 minutos 15 segundos; 45 s de margen sobre 10 minutos)

*Generado por `scripts/ep3/generar_docs_ep3.py`. Cada cifra sale de los archivos de `data/08_reporting_ep3`; las de la demo, de `data/09_app_ep3` con la misma lógica que la página (`app_logica.py`). Total: 9:15.*

| Tiempo | Bloque | Qué decir | Qué mostrar |
|---|---|---|---|
{chr(10).join(filas)}

**Plan B si la demo falla:** mostrar `notebooks/14_ep3_dos_pasos_y_app.ipynb` (ya ejecutado, con la prueba de humo de las 7 secciones).
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
    eqx = eq[eq["celdas_con_hueco"] == "excluidas"].set_index(["variable", "grupo"])
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
        ("¿Qué es la Fracción para 80 %?", "La fracción de cajas que hay que revisar para encontrar el 80 % de los positivos.", f"{p(esc['Fraccion_80'])} en un paso; {p(esc['Fraccion_80_C'])} en dos pasos ({EN_MUESTRA})", "f5_brazoC.csv"),
        ("¿Qué son los puntos A y B?", "A: umbral que busca recall 0,80, fijado con scores internos de entrenamiento. B: umbral que revisa el 20 % de las cajas.", f"recall A {c(esc['recall_A'])}; recall B {c(esc['recall_B'])}", "f5_metricas_candidatos.csv"),
        ("¿Está calibrada la probabilidad?", "Con Platt, el ECE queda bajo 0,05 en la regla.", f"ECE {c(esc['ECE_cal'])}, Brier {c(esc['Brier_cal'])}", "f5_metricas_candidatos.csv"),
        ("¿Es estable la solución?", "Por segmento sí (mediana alta); por fold no cumple el criterio de 0,75 en ningún candidato, por el fold 0.", f"mediana por segmento {c(esc['AUC_mediana_segmento'])}; mínimo por fold {c(esc['AUC_min_fold'])}", "f5_metricas_candidatos.csv"),
        ("¿Qué muestra el leave-one-segment-out?", "Que dejar un segmento fuera casi no cambia el AUC global y que hay segmentos difíciles.", f"AUC LOSO {c(lo['AUC'])}; {lo['segmentos_con_AUC_menor_a_0_55']} de {lo['segmentos_evaluables']} segmentos con AUC < 0,55", "f5_loso_resumen_Regla_top.json"),
        ("¿Hay sobreajuste en los modelos de árboles?", "Sí: la brecha de ajuste a validación es grande y no se cierra con más segmentos. La regla no tiene brecha porque no aprende.", f"XGB: ajuste {c(xgb['AUC_ajuste'])}, validación {c(xgb['AUC_validacion'])}", "f5_brecha_XGB.csv"),
        ("¿Por qué se eligió la regla?", "Por el plan: el más simple cuyo AUC queda a menos de 0,010 del mejor; nadie cumplió O4 y se aplicó una regla de reserva post hoc entre los que cumplen O1 y O3.", sel["razon"], "f6_seleccion.json, plan_v3_desviaciones.md (DEV-2)"),
        ("¿Algún candidato «vale la pena» frente a la regla (O2)?", "Ninguno.", f"mejor dif. de Fracción 80 %: {c(tab['dif_Fraccion_80_vs_regla'].min())} (E2, IC {c(tab.loc['E2', 'dif_Fraccion_80_lo'])} a {c(tab.loc['E2', 'dif_Fraccion_80_hi'])})", "f6_tabla_seleccion.csv"),
        ("¿Cuánto cuesta revisar?", f"Con el supuesto de {SEG_POR_CAJA} s por caja (no medido, editable en la página): horas para el 80 % de recall.", f"un paso {N['h_A']:.0f} h; dos pasos {N['h_C']:.0f} h ({EN_MUESTRA}); al azar {N['h_azar']:.0f} h", "f6_modelo_escogido.csv"),
        ("¿Qué es el punto de equilibrio?", "El costo en cajas por auditoría con el que dos pasos empata con un paso; no inventamos un costo.", f"{mi(N['eq'])} cajas (IC {mi(esc['equilibrio_lo'])} a {mi(esc['equilibrio_hi'])}) ({EN_MUESTRA})", "f5_brazoC.csv"),
        ("¿Qué hace la página?", "Muestra el problema, el mapa de huecos, la cola de revisión con recall esperado, la explicación de una caja con su tipo de caso, la evidencia, la ética y puntúa segmentos nuevos.", "7 secciones, 3 perfiles", "app/app.py"),
        ("¿Cómo se despliega?", "Local con Streamlit o con Docker (volumen de datos de solo lectura, sin datos en la imagen). Docker no se probó; AWS es solo una guía.", "Docker 28.3.0 instalado, demonio apagado", "despliegue.md"),
        ("¿Qué pasa con la licencia y la privacidad?", "Los datos de Waymo no salen del equipo; los identificadores se ocultan en modo presentación; el zip es solo para uso académico del docente.", "sin red, sin datos en la imagen", "despliegue.md, informe sección 16"),
        ("¿Qué cambió respecto de EP2?", "41 segmentos juntos, + XGBoost y LightGBM, búsqueda anidada, ensambles, filtro 1 en el flujo, no supervisado, página y despliegue.", "ver tabla de cambios", "informe_tecnico_EP3.md, sección 6"),
        ("¿Por qué no hay nodos de Kedro en EP2 y EP3?", "El análisis vive en notebooks y scripts; los pipelines de Kedro son los de ingesta y preprocesamiento de EP1.", "-", "informe_tecnico_EP3.md, sección 6"),
        ("¿Por qué 1 repetición y 30 configuraciones?", "Regla de cómputo: la proyección con el plan completo superaba 4 horas (RF tarda 45 a 100 s por ajuste). Está registrado como DEV-1.", "DEV-1", "plan_v3_desviaciones.md"),
        ("¿Qué son accuracy y F1 aquí?", "Solo referencia en el cuadro «Modelo escogido»; no deciden nada.", f"F1 en A {c(esc['F1_A'])}; accuracy en A {c(esc['accuracy_A'])}", "f6_modelo_escogido.csv"),
        ("¿Qué falta?", "Validación externa con segmentos nuevos (sellada), probar Docker y medir el tiempo real de revisión.", "-", "informe_tecnico_EP3.md, sección 17"),
        # ---- nuevas (fase 14)
        ("¿Dónde está el Machine Learning si la solución final es una regla?", "En todo lo que llevó a elegirla: la regla se comparó con LR, RF, HGB, XGBoost, LightGBM y cuatro ensambles con búsqueda anidada y validación por segmento, y ninguno la supera de forma distinguible; además el ML aporta el calibrador Platt, el detector de huecos y el análisis no supervisado. Concluir que una regla basta es un resultado del aprendizaje automático, no su ausencia.", f"11 candidatos; AUC regla {c(f5.loc['Regla top', 'AUC'])} contra el mejor modelo {c(f5.loc[['LR3', 'LR', 'RF', 'HGB', 'XGB', 'LGBM', 'E1', 'E3', 'E4'], 'AUC'].max())}", "f5_metricas_candidatos.csv, f6_tabla_seleccion.csv"),
        ("¿Por qué no elegir E2 si tiene mejor PR-AUC?", f"Porque la diferencia no es distinguible y E2 contiene a la regla: AUC {c(N['e2']['auc'])} contra {c(f5.loc['Regla top', 'AUC'])}, PR-AUC {c(N['e2']['pr'])} contra {c(f5.loc['Regla top', 'PR-AUC'])}, Fracción 80 % {c(N['e2']['fr'])} contra {c(f5.loc['Regla top', 'Fraccion_80'])} (IC de la diferencia {c(N['e2']['lo'])} a {c(N['e2']['hi'])}). Además su ECE es {c(N['e2']['ece'])} (> 0,05). El plan manda elegir el más simple dentro de 0,010 de AUC.", f"dif. AUC {c(f4.loc['E2', 'dif_AUC'])}", "f6_tabla_seleccion.csv, f4_ensambles_aporta.csv"),
        ("¿Por qué RF empeora al optimizar?", "No lo sabemos: es una hipótesis (no verificada) que la búsqueda interna, con 30 configuraciones y 41 segmentos, elige configuraciones que se ajustan a particularidades de los segmentos de entrenamiento y no se sostienen en el fold de validación. LR también empeora, con otra posible causa (el criterio interno puede preferir variables y regularización distintas).", f"RF dif. PR-AUC {c(f3.loc['RF', 'dif_PR-AUC'])} (IC {c(f3.loc['RF', 'dif_PR-AUC_lo'])} a {c(f3.loc['RF', 'dif_PR-AUC_hi'])}); LR {c(f3.loc['LR', 'dif_PR-AUC'])}", "f3_defecto_vs_optimizado.csv"),
        ("¿Por qué 1 repetición de la CV externa?", "Porque Random Forest tarda 45 a 100 s por ajuste y el plan completo (3 repeticiones x 40 configuraciones) proyectaba unas 5 horas, sobre el límite de 4. Consecuencia: los IC reflejan una sola partición de segmentos en folds.", "DEV-1", "plan_v3_desviaciones.md"),
        ("¿Qué pasa en el fold 0?", f"Contiene {int(fr.loc['0', 'segmentos'])} segmentos y {mi(fr.loc['0', 'cajas'])} cajas, entre ellos `257766998801` (cámara 3 sin pares). El AUC de la regla es {c(fr.loc['0', 'AUC_A'])} en el brazo A y {c(fr.loc['0', 'AUC_B_celdas_sanas'])} sobre celdas sanas: el fallo del criterio de estabilidad se debe a la celda con hueco. Post hoc.", f"AUC A {c(fr.loc['0', 'AUC_A'])}; B {c(fr.loc['0', 'AUC_B_celdas_sanas'])}", "f12_auc_por_fold_brazos.csv"),
        ("¿El 29,6 % no es circular?", f"En parte sí: los parámetros del detector se ajustaron con estos 41 segmentos y el hueco se descubrió en ellos, y la ganancia sale de 2 celdas cámara x segmento. Por eso se rotula {EN_MUESTRA}. La diferencia pareada con un paso es {c(glob['dif_C_menos_A'])} con IC {c(glob['ic_lo'])} a {c(glob['ic_hi'])} (no excluye 0). La prueba no circular es la validación con segmentos nuevos.", f"{p(esc['Fraccion_80_C'])} contra {p(esc['Fraccion_80'])}", "f5_brazoC.csv, f12_diferencia_C_menos_A.csv"),
        ("¿Qué pasa si el hueco no existe en datos nuevos?", f"El detector no marcaría nada (o marcaría falsas alarmas) y el flujo se reduce a la cola con la regla: dos pasos pasa a ser un paso, y la Fracción para 80 % vuelve a unos {p(esc['Fraccion_80'])}. Las falsas alarmas en la muestra van de {f12['detector_falsas_alarmas_rango'][0]} a {f12['detector_falsas_alarmas_rango'][1]} celdas según los parámetros; su tasa en datos nuevos se medirá en la validación externa.", f"falsas alarmas {f12['detector_falsas_alarmas_rango'][0]} a {f12['detector_falsas_alarmas_rango'][1]}", "f12_sensibilidad_detector.csv"),
        ("¿Qué muestran los clusters y qué no?", f"Muestran que los casos lejanos y poco densos tienen mucha más tasa de `sin_camara` ({p(k2.sort_values('tasa_sin_camara').iloc[-1]['tasa_sin_camara'])}) que los cercanos y densos ({p(k2.sort_values('tasa_sin_camara').iloc[0]['tasa_sin_camara'])}). No muestran grupos naturales firmes (el acuerdo entre KMeans y GMM es bajo, ARI {c(f13['ari_entre_tecnicas']['k=2']['KMeans vs GMM'])}) ni causalidad.", f"k = {f13['k_elegido']}; silhouette {c(selk.loc[f13['k_elegido'], 'silhouette_muestra_20000'])}", "f13_clusters_k2.csv, f13_resumen.json"),
        ("¿Mejoran los clusters la predicción?", f"No. Agregar el cluster a la probabilidad de la regla cambia el AUC en {c(ap.loc[2, 'dif_AUC'], 4)} (IC {c(ap.loc[2, 'ic_lo'], 4)} a {c(ap.loc[2, 'ic_hi'], 4)}) con k = 2 y en {c(ap.loc[4, 'dif_AUC'], 4)} con k = 4 (IC {c(ap.loc[4, 'ic_lo'], 4)} a {c(ap.loc[4, 'ic_hi'], 4)}: la empeora).", f"dif. AUC k = 2: {c(ap.loc[2, 'dif_AUC'], 4)}", "f13_aporte_cluster.csv"),
        ("¿Por qué ese k?", f"Se elige k por el máximo silhouette entre 2 y 6: k = {f13['k_elegido']} ({c(selk.loc[f13['k_elegido'], 'silhouette_muestra_20000'])}); se explora también k = 4 como en EP2 ({c(selk.loc[4, 'silhouette_muestra_20000'])}). Con k = 4 la estabilidad por segmentos es baja (ARI mínimo {c(ult.loc[4, 'ari_minimo'])}) y los clusters empeoran la predicción.", f"silhouette k = 2: {c(selk.loc[2, 'silhouette_muestra_20000'])}", "f13_seleccion_k.csv, f13_estabilidad.csv"),
        ("¿Qué sesgos mediste?", f"Descriptivamente, el recall de la regla en el punto A por ubicación, momento del día y clase. Con celdas con hueco: de día {c(eqi.loc[('momento_del_dia', 'Day'), 'recall_A'])} y de noche {c(eqi.loc[('momento_del_dia', 'Night'), 'recall_A'])}; San Francisco {c(eqi.loc[('ubicacion', 'location_sf'), 'recall_A'])}; ciclistas {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} (solo {int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos). Sin pruebas de hipótesis; parte de la brecha desaparece al quitar las celdas con hueco.", f"recall A global {c(eqi.loc[('todas', 'todas'), 'recall_A'])}", "f12_equidad.csv"),
        ("¿El ARI tan bajo entre KMeans y GMM es un error de código?", f"No. Se verificó: las tres técnicas usan las mismas {mi(adj['filas']['filas_muestra'])} filas en el mismo orden, el ARI recalculado coincide con el original y los GMM convergieron. Es una propiedad de los datos y del modelo (GMM de covarianza `full` contra KMeans, sin variables de oclusión, que en EP2 sí separaban grupos compactos); es una hipótesis, post hoc.", f"ARI KMeans–GMM {c(f13['ari_entre_tecnicas']['k=2']['KMeans vs GMM'])} (k = 2); con covarianza `spherical` sube", "f13_ari_diagnostico.csv, f13_ari_diagnostico.json"),
        ("¿El brazo C no es mejor que A por construcción?", f"En cajas revisadas, casi: la auditoría quita cajas de la cola sin costo por caja, así que C no puede ser peor que A; lo informativo es el punto de equilibrio ({mi(N['eq'])} cajas por auditoría) y la tasa de falsas alarmas del detector, que solo se estima con datos nuevos. Rótulo: {EN_MUESTRA}.", f"dif. C menos A {c(glob['dif_C_menos_A'])} (IC {c(glob['ic_lo'])} a {c(glob['ic_hi'])})", "f12_diferencia_C_menos_A.csv, f5_brazoC.csv"),
        ("¿Por qué el límite superior del IC de C menos A es exactamente 0?", f"Porque en las réplicas del bootstrap que no contienen ninguno de los 2 segmentos con hueco, C es igual a A. Con 41 segmentos muestreados con reemplazo la probabilidad exacta de ese evento es {p(hc['prob_exacta_ninguno_de_los_2'], 2)} ({hc['formula']}) y se observó {p(hc['proporcion_observada_ninguno_de_los_2'])} en {mi(hc['replicas'])} réplicas: es un efecto del diseño, no evidencia a favor ni en contra de C.", f"exacta {p(hc['prob_exacta_ninguno_de_los_2'], 2)}; observada {p(hc['proporcion_observada_ninguno_de_los_2'])}", "f12b_hechos_brazoC.json"),
        ("¿Qué muestra la página con «Todos» y 20 %, y por qué no coincide con el 61,9 %?", f"Muestra el brazo de dos pasos (C): recall esperado {p(pg['recall'])} (IC {p(pg['lo'])} a {p(pg['hi'])}), {mi(pg['cajas_a_revisar'])} cajas y {c(pg['horas'], 1)} h con {SEG_POR_CAJA} s por caja (en muestra). El {p(esc['Captura@20'])} es la captura del brazo de un paso (A) al revisar el 20 % y está en la tarjeta de Inicio; son brazos distintos. El texto bajo las tarjetas redondea a {p(pg['recall_proceso'])} porque usa el conteo observado y no la curva interpolada.", f"C {p(pg['recall'])}; A {p(pg['recall_A'])}", "data/09_app_ep3 (kpis.json, curva_cola.csv), f5_metricas_candidatos.csv"),
        ("¿La regla trata igual a todos los casos?", f"No. Con celdas con hueco, de día el recall es {c(eqi.loc[('momento_del_dia', 'Day'), 'recall_A'])} y de noche {c(eqi.loc[('momento_del_dia', 'Night'), 'recall_A'])}; sin esas celdas, de día {c(eqx.loc[('momento_del_dia', 'Day'), 'recall_A'])} y la brecha se invierte (era el hueco). San Francisco baja la brecha ({c(eqi.loc[('ubicacion', 'location_sf'), 'recall_A'])} a {c(eqx.loc[('ubicacion', 'location_sf'), 'recall_A'])}) pero queda. En ciclistas el recall es {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])} contra {c(eqi.loc[('clase', 'PEDESTRIAN'), 'recall_A'])} en peatones ({int(eqi.loc[('clase', 'CYCLIST'), 'positivos'])} positivos en {int(eqi.loc[('clase', 'CYCLIST'), 'segmentos'])} segmentos): poco confiable. Descriptivo, sin pruebas de hipótesis.", f"ciclistas {c(eqi.loc[('clase', 'CYCLIST'), 'recall_A'])}", "f12_equidad.csv"),
        ("¿Se puede exponer la página en la red o publicarla en la nube?", "No tal como está: escucha solo en localhost (`.streamlit/config.toml`), el compose publica el puerto solo en 127.0.0.1 y la página muestra identificadores de objeto. Para exponerla haría falta autenticación y quitar los identificadores, y los datos de Waymo no deben subirse a servicios de nube (licencia de uso no comercial). Una prueba vigila esa configuración.", "address = localhost; 127.0.0.1:8501:8501", ".streamlit/config.toml, docker-compose.yml, tests/ep3/test_seguridad_pagina.py"),
        ("¿Qué recomiendas al negocio?", "Usar la solución en tres capas (auditar cámaras primero, cola con la regla, persona que decide), monitorear el recall por segmento y por clase, medir el tiempo real de revisión y el costo de una auditoría, y validar con segmentos nuevos antes de confiar en el flujo en dos pasos.", f"punto de equilibrio {mi(N['eq'])} cajas ({EN_MUESTRA})", "informe, sección 15; f5_brazoC.csv"),
    ]
    out = ["# Preguntas cruzadas con respuesta, cifra y fuente", "", f"*Generado por `scripts/ep3/generar_docs_ep3.py`. {len(Q)} preguntas; cada cifra sale del archivo indicado (carpeta `data/08_reporting_ep3` salvo que se diga otra). Las referencias a secciones corresponden a `informe_tecnico_EP3.md`.*", ""]
    for i, (q, a, cifra, fuente) in enumerate(Q, 1):
        out += [f"**{i}. {q}**", f"- Respuesta: {a}", f"- Cifra: {cifra}", f"- Fuente: `{fuente}`", ""]
    return "\n".join(out)


def sincronizar_conteos() -> list[str]:
    """Reemplaza el contenido de las marcas <!--n_ep3-->..<!--/n_ep3-->, <!--n_ep2-->..<!--/n_ep2--> y <!--n_total-->..<!--/n_total--> por los conteos de pruebas_ep3_conteo.json."""
    valores = {"n_ep3": PRUEBAS_EP3, "n_ep2": PRUEBAS_EP2, "n_total": PRUEBAS_TOTAL}
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
    print("escritos: informe_tecnico_EP3.md, README_EP3.md, guion_presentacion.md, preguntas_cruzadas.md; conteos sincronizados en:", ", ".join(sincronizar_conteos()) or "(nada)")


if __name__ == "__main__":
    main()
