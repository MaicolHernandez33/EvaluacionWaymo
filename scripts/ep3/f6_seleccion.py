"""F6 (IE12), parte 1: tabla de seleccion con los objetivos O1 a O4 y regla de eleccion del plan v3 (P8).

Entradas: f5_metricas_candidatos.csv, f5_brazoC.csv y f4_oof.parquet (predicciones fuera de fold).
Salidas en data/08_reporting_ep3: f6_tabla_seleccion.csv, f6_seleccion.json, f6_modelo_escogido.csv.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.candidatos import NIVEL_SIMPLICIDAD  # noqa: E402
from waymo_evaluacion.ep3.metricas import ConjuntoOOF, ic95  # noqa: E402
from waymo_evaluacion.ep3.plan import cargar_plan_v3  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
NOMBRES = ["Regla top", "LR3", "LR", "RF", "HGB", "XGB", "LGBM", "E1", "E2", "E3", "E4"]


def main() -> None:
    plan = cargar_plan_v3(RAIZ)
    o = plan["P8"]["objetivos"]
    f5 = pd.read_csv(REP / "f5_metricas_candidatos.csv").set_index("candidato")
    c5 = pd.read_csv(REP / "f5_brazoC.csv").set_index("candidato")
    pp = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = pp[pp["en_zona_principal"]].reset_index(drop=True)
    oof = pd.read_parquet(RAIZ / "data/07_model_output_ep3/f4_oof.parquet")
    conj = ConjuntoOOF(pp["sin_camara"].to_numpy(), pp["seg"].to_numpy(), {k: [oof[k].to_numpy()] for k in NOMBRES})
    boot = conj.bootstrap(NOMBRES, 1000, 42)
    prev = float(pp["sin_camara"].mean())
    filas = []
    for n in NOMBRES:
        r = f5.loc[n]
        d_frac = boot[n][:, 3] - boot["Regla top"][:, 3]
        d_auc = boot[n][:, 0] - boot["Regla top"][:, 0]
        frac_dif = float(r["Fraccion_80"] - f5.loc["Regla top", "Fraccion_80"])
        auc_dif = float(r["AUC"] - f5.loc["Regla top", "AUC"])
        lo_f, hi_f = ic95(d_frac)
        lo_a, hi_a = ic95(d_auc)
        o1 = bool(r["AUC"] >= o["O1"]["auc_min"] and (r["PR-AUC"] - prev) >= o["O1"]["pr_auc_menos_prevalencia_min"])
        o2 = bool(n != "Regla top" and -frac_dif * 100 >= o["O2"]["fraccion_80_baja_min_puntos"] and hi_f < 0 and auc_dif >= o["O2"]["auc_sube_min"])
        o3 = bool(r["recall_A"] >= o["O3"]["recall_punto_A_min"])
        o4 = bool(r["estable"] and r["ECE_cal"] <= o["O4"]["ece_max"])
        filas.append({"candidato": n, "nivel_simplicidad": NIVEL_SIMPLICIDAD[n], "AUC": r["AUC"], "AUC_lo": r["AUC_lo"], "AUC_hi": r["AUC_hi"], "PR-AUC": r["PR-AUC"],
                      "PR-AUC_menos_prevalencia": r["PR-AUC"] - prev, "Fraccion_80": r["Fraccion_80"], "recall_A": r["recall_A"], "ECE_cal": r["ECE_cal"],
                      "AUC_min_fold": r["AUC_min_fold"], "AUC_mediana_segmento": r["AUC_mediana_segmento"], "estable": bool(r["estable"]),
                      "dif_Fraccion_80_vs_regla": frac_dif, "dif_Fraccion_80_lo": lo_f, "dif_Fraccion_80_hi": hi_f, "dif_AUC_vs_regla": auc_dif, "dif_AUC_lo": lo_a, "dif_AUC_hi": hi_a,
                      "O1": o1, "O2": o2, "O3": o3, "O4": o4, "cumple_O1_O3_O4": o1 and o3 and o4,
                      "Fraccion_80_C": c5.loc[n, "Fraccion_80_C"], "equilibrio_cajas_por_auditoria": c5.loc[n, "equilibrio_cajas_por_auditoria"],
                      "recall_A_proceso_C": c5.loc[n, "recall_A_proceso_C"]})
    tab = pd.DataFrame(filas)
    tab.to_csv(REP / "f6_tabla_seleccion.csv", index=False)

    elegibles = tab[tab["cumple_O1_O3_O4"]]
    fallback = False
    if elegibles.empty:                      # DEV-2 (plan_v3_desviaciones.md): nadie cumple O4 -> misma regla entre los que cumplen O1 y O3
        elegibles, fallback = tab[tab["O1"] & tab["O3"]], True
    if elegibles.empty:
        elegido, razon = None, "ningún candidato cumple O1 y O3"
        cerca = pd.DataFrame()
    else:
        mejor = float(elegibles["AUC"].max())
        cerca = elegibles[elegibles["AUC"] >= mejor - plan["P8"]["objetivos"].get("tolerancia_auc", 0.010)]
        elegido_fila = cerca.sort_values(["nivel_simplicidad", "AUC"], ascending=[True, False]).iloc[0]
        elegido = str(elegido_fila["candidato"])
        razon = (f"{'ningún candidato cumple O4 (regla de reserva DEV-2); ' if fallback else ''}entre los {len(elegibles)} candidatos que cumplen {'O1 y O3' if fallback else 'O1, O3 y O4'}, el mejor AUC OOF es {f'{mejor:.3f}'.replace('.', ',')}; los que quedan a menos de 0,010 son "
                 f"{', '.join(cerca['candidato'])}; el más simple es {elegido}")
    o2_cumplen = tab.loc[tab["O2"], "candidato"].tolist()
    ensamble = "E1" if tab.set_index("candidato").loc["E1", "AUC"] >= tab.set_index("candidato").loc["E4", "AUC"] else "E4"
    res = {"elegido": elegido, "razon": razon, "fallback_O4": fallback, "elegibles": elegibles["candidato"].tolist(), "candidatos_que_cumplen_O4": tab.loc[tab["O4"], "candidato"].tolist(), "cerca_del_mejor": cerca["candidato"].tolist() if len(cerca) else [],
           "candidatos_que_cumplen_O2": o2_cumplen, "O2_lo_cumple_alguien": bool(o2_cumplen), "ensamble_principal_declarado_P6": ensamble, "prevalencia": prev}
    (REP / "f6_seleccion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    if elegido:
        full = f5.loc[elegido]
        cuadro = {k: full[k] for k in ["AUC", "AUC_lo", "AUC_hi", "PR-AUC", "PR-AUC_lo", "PR-AUC_hi", "Captura@20", "Captura@20_lo", "Captura@20_hi", "Fraccion_80", "Fraccion_80_lo", "Fraccion_80_hi",
                                        "recall_A", "recall_A_lo", "recall_A_hi", "precision_A", "pct_revisar_A", "recall_B", "recall_B_lo", "recall_B_hi", "precision_B", "pct_revisar_B",
                                        "ECE_cal", "Brier_cal", "AUC_min_fold", "AUC_mediana_segmento", "F1_A", "accuracy_A", "F1_B", "accuracy_B"] if k in full.index}
        cuadro.update({k: c5.loc[elegido, k] for k in ["Fraccion_80_C", "Fraccion_80_C_lo", "Fraccion_80_C_hi", "Captura@20_C", "equilibrio_cajas_por_auditoria", "equilibrio_lo", "equilibrio_hi", "recall_A_proceso_C"]})
        cuadro = {"candidato": elegido, **cuadro, "nota": "F1 y accuracy son solo referencia; no deciden nada (P7)"}
        pd.DataFrame([cuadro]).to_csv(REP / "f6_modelo_escogido.csv", index=False)
    pd.set_option("display.width", 250)
    print(tab[["candidato", "AUC", "PR-AUC_menos_prevalencia", "Fraccion_80", "recall_A", "ECE_cal", "estable", "O1", "O2", "O3", "O4", "dif_Fraccion_80_vs_regla", "dif_Fraccion_80_lo", "dif_Fraccion_80_hi", "dif_AUC_vs_regla"]].round(3).to_string(index=False))
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
