"""F18-A3(b) (post hoc, no pre-declarado): AUC de la regla dentro de cada cluster, con todas las cajas y sin las cajas de las celdas con hueco (Lista A).

Pregunta: en las cajas cercanas y densas la regla casi no ordena (AUC 0,531 con k = 2). ¿Sube ese AUC cuando se sacan las celdas con hueco?
Usa la probabilidad con Platt de la regla fuera de fold (f5_pcal.parquet), los clusters de f13_clusters.parquet y la marca de hueco por fila (dev_41_hueco.parquet).
Descriptivo: sin IC. Solo lee datos y escribe data/08_reporting_ep3/f13_auc_cluster_sin_huecos.csv y .json (no toca el artefacto no supervisado).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

RAIZ = Path(__file__).resolve().parents[2]
REP, OUT = RAIZ / "data/08_reporting_ep3", RAIZ / "data/07_model_output_ep3"
MIN_POR_CLASE = 200  # mismo criterio que f13_no_supervisado.py


def auc(y: np.ndarray, s: np.ndarray) -> float:
    return float(roc_auc_score(y, s)) if (y.sum() >= MIN_POR_CLASE and (1 - y).sum() >= MIN_POR_CLASE) else float("nan")


def main() -> None:
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    h = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41_hueco.parquet").set_index("fila_id")["en_hueco"]
    pp = dev[dev["en_zona_principal"]].reset_index(drop=True)
    hueco = h.loc[pp["fila_id"]].to_numpy().astype(bool)
    pcal = pd.read_parquet(OUT / "f5_pcal.parquet")["pcal_Regla top"].to_numpy()
    cl = pd.read_parquet(OUT / "f13_clusters.parquet")
    y = pp["sin_camara"].to_numpy()
    assert len(cl) == len(pp) == len(pcal)
    prev = {k: pd.read_csv(REP / f"f13_clusters_k{k}.csv") for k in (2, 4)}
    filas = []
    for k in (2, 4):
        lab = cl[f"cluster_k{k}"].to_numpy()
        for g in sorted(set(lab)):
            m = lab == g
            ms = m & ~hueco
            a_todas, a_sin = auc(y[m], pcal[m]), auc(y[ms], pcal[ms])
            previo = float(prev[k].set_index("cluster").loc[g, "AUC_regla_dentro_del_cluster"])
            filas.append({"k": k, "cluster": int(g), "tipo_de_caso": prev[k].set_index("cluster").loc[g, "tipo_de_caso"], "cajas": int(m.sum()), "cajas_en_celdas_con_hueco": int((m & hueco).sum()),
                          "positivos": int(y[m].sum()), "positivos_en_celdas_con_hueco": int(y[m & hueco].sum()), "tasa_sin_camara": float(y[m].mean()), "tasa_sin_camara_sin_huecos": float(y[ms].mean()),
                          "AUC_todas": a_todas, "AUC_sin_celdas_con_hueco": a_sin, "dif_AUC": a_sin - a_todas, "AUC_en_f13_clusters_csv": previo, "coincide_con_f13": bool(abs(previo - a_todas) < 1e-9 or (np.isnan(previo) and np.isnan(a_todas)))})
    t = pd.DataFrame(filas)
    t.to_csv(REP / "f13_auc_cluster_sin_huecos.csv", index=False)
    res = {"nota": "post hoc, no pre-declarado; descriptivo (sin IC); regla con Platt fuera de fold", "AUC_global_todas": auc(y, pcal), "AUC_global_sin_celdas_con_hueco": auc(y[~hueco], pcal[~hueco]),
           "cajas_en_celdas_con_hueco": int(hueco.sum()), "todas_coinciden_con_f13_clusters_csv": bool(t["coincide_con_f13"].all())}
    (REP / "f13_auc_cluster_sin_huecos.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
    print(t.round(3).drop(columns=["tipo_de_caso"]).to_string(index=False)); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
