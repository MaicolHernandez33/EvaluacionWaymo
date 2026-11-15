"""F18-A4 (post hoc): verifica con los datos (1) como se define «20 %» en el informe (f5_generalizacion.py) y en la pagina (curva_cola.csv, app_logica.py)
y (2) por que el AUC base de f13_aporte_cluster.csv es 0,798 y no 0,823. Solo lee; escribe data/08_reporting_ep3/f18_definiciones.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.app_logica import cargar_datos, cola_segmento, recall_en_presupuesto  # noqa: E402

REP, OUT = RAIZ / "data/08_reporting_ep3", RAIZ / "data/07_model_output_ep3"


def main() -> None:
    D = cargar_datos(RAIZ / "data/09_app_ep3")
    cajas = D["cajas"]
    N, Nq = len(cajas), int((~cajas["en_hueco"]).sum())
    f5 = pd.read_csv(REP / "f5_brazoC.csv").set_index("candidato").loc["Regla top"]
    f5m = pd.read_csv(REP / "f5_metricas_candidatos.csv").set_index("candidato").loc["Regla top"]
    k_f5 = int(np.ceil(0.20 * N))            # f5: 20 % del TOTAL de cajas (el costo del brazo C cuenta solo las cajas de la cola; la auditoria no cuesta)
    k_pag = int(np.ceil(0.20 * Nq))          # pagina: 20 % de la COLA (cajas de celdas sanas)
    sol = D["kpis"]["nombre_curva"]
    curva_pag = recall_en_presupuesto(D["curva"], sol, 0.20)["recall"]
    curva_A = recall_en_presupuesto(D["curva"], "Solución elegida, un paso (A)", 0.20)["recall"]
    _, i_pag = cola_segmento(cajas, "Todos", 0.20)
    _, i_f5 = cola_segmento(cajas, "Todos", k_f5 / Nq)
    # (2) AUC base de f13_aporte_cluster.csv
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = dev[dev["en_zona_principal"]].reset_index(drop=True)
    y = pp["sin_camara"].to_numpy()
    s = pd.read_parquet(OUT / "f4_oof.parquet")["Regla top"].to_numpy()
    p = pd.read_parquet(OUT / "f5_pcal.parquet")["pcal_Regla top"].to_numpy()
    lg = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    o1 = np.zeros(len(y))
    for tr, va in GroupKFold(5).split(lg, y, pp["seg"]):
        o1[va] = LogisticRegression(C=1e6, max_iter=500).fit(lg[tr, None], y[tr]).predict_proba(lg[va, None])[:, 1]
    por_fold = {int(k): [float(roc_auc_score(y[pp["fold_s42"] == k], s[pp["fold_s42"] == k])), float(roc_auc_score(y[pp["fold_s42"] == k], p[pp["fold_s42"] == k]))] for k in range(5)}
    res = {"nota": "post hoc, no pre-declarado",
           "definicion_20pct": {"cajas_total": N, "cajas_cola_celdas_sanas": Nq, "cajas_en_celdas_con_hueco": N - Nq,
                                "f5_cajas_revisadas_al_20pct": k_f5, "pagina_cajas_revisadas_al_20pct": k_pag, "diferencia_cajas": k_f5 - k_pag,
                                "captura20_C_informe_f5": float(f5["Captura@20_C"]), "captura20_A_informe_f5": float(f5m["Captura@20"]),
                                "recall_C_pagina_curva_20pct_de_la_cola": float(curva_pag), "recall_A_pagina_curva_20pct": float(curva_A),
                                "recall_C_observado_pagina_20pct_de_la_cola": float(i_pag["recall_proceso"]), "recall_C_observado_con_las_cajas_de_f5": float(i_f5["recall_proceso"]),
                                "cajas_a_revisar_pagina": int(i_pag["cajas_a_revisar"]), "cajas_a_revisar_con_la_definicion_de_f5": int(i_f5["cajas_a_revisar"])},
           "auc_base_f13": {"AUC_puntaje_crudo_pooled": float(roc_auc_score(y, s)), "AUC_prob_Platt_pooled": float(roc_auc_score(y, p)), "AUC_f13_aporte_cluster_base_reproducido": float(roc_auc_score(y, o1)),
                            "AUC_por_fold_[crudo,Platt]": por_fold}}
    (REP / "f18_definiciones.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))
    print("f13_aporte_cluster AUC_regla:", float(pd.read_csv(REP / "f13_aporte_cluster.csv")["AUC_regla"].iloc[0]))


if __name__ == "__main__":
    main()
