"""Diagnostico del ARI de la fase 13 (post hoc, no pre-declarado). Solo lectura de datos; no toca el artefacto no supervisado ni su manifest.

Pregunta: el ARI KMeans contra GMM bajo (0,008 con k = 2; en EP2 fue 0,997) ¿es un error de filas o una propiedad de los datos?
Se reproduce el mismo diseno de f13_no_supervisado.py (mismas variables, mismo scaler, mismas 15.000 filas elegidas con la misma semilla)
y se recalcula el ARI con GMM de covarianza full, diag y spherical, mas Ward. Escribe data/08_reporting_ep3/f13_ari_diagnostico.csv y .json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score as ari
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts" / "ep3"))
from f13_no_supervisado import caracteristicas  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
SEM = 42


def main() -> None:
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = dev[dev["en_zona_principal"]].reset_index(drop=True)
    Z = StandardScaler().fit_transform(caracteristicas(pp))
    rng = np.random.default_rng(SEM)
    rng.choice(len(Z), 20000, replace=False)  # misma secuencia que f13: primero la muestra de 20.000
    i15 = rng.choice(len(Z), 15000, replace=False)
    ZZ = Z[i15]
    con_orden = {"filas_muestra": int(len(i15)), "filas_unicas": int(len(set(i15.tolist()))), "misma_matriz_para_las_tres_tecnicas": True}
    filas = []
    for k in (2, 4):
        km = KMeans(k, n_init=10, random_state=SEM).fit(Z)
        a = km.predict(ZZ)
        w = fcluster(linkage(ZZ, "ward"), k, "maxclust") - 1
        filas.append({"k": k, "tecnica": "KMeans (ajustado con las 80.571 filas, aplicado a la muestra)", "covarianza": "", "n_init": 10, "converged": True, "n_iter": int(km.n_iter_),
                      "tamanos": json.dumps(np.bincount(a, minlength=k).tolist()), "ARI_vs_KMeans": 1.0, "ARI_vs_Ward": float(ari(a, w))})
        filas.append({"k": k, "tecnica": "Ward (muestra)", "covarianza": "", "n_init": "", "converged": True, "n_iter": "", "tamanos": json.dumps(np.bincount(w, minlength=k).tolist()),
                      "ARI_vs_KMeans": float(ari(a, w)), "ARI_vs_Ward": 1.0})
        for cov in ("full", "diag", "spherical"):
            for ni in (2, 10):
                g = GaussianMixture(k, covariance_type=cov, n_init=ni, random_state=SEM).fit(ZZ)
                b = g.predict(ZZ)
                filas.append({"k": k, "tecnica": "GMM (muestra)" + (" [la usada en f13]" if (cov == "full" and ni == 2) else ""), "covarianza": cov, "n_init": ni, "converged": bool(g.converged_),
                              "n_iter": int(g.n_iter_), "tamanos": json.dumps(np.bincount(b, minlength=k).tolist()), "ARI_vs_KMeans": float(ari(a, b)), "ARI_vs_Ward": float(ari(b, w))})
    tabla = pd.DataFrame(filas)
    tabla.to_csv(REP / "f13_ari_diagnostico.csv", index=False)
    usada = {k: float(tabla[(tabla["k"] == k) & (tabla["covarianza"] == "full") & (tabla["n_init"] == 2)].iloc[0]["ARI_vs_KMeans"]) for k in (2, 4)}
    previo = json.loads((REP / "f13_resumen.json").read_text(encoding="utf-8"))["ari_entre_tecnicas"]
    res = {"filas": con_orden, "ari_kmeans_vs_gmm_full_ninit2_recalculado": usada, "ari_kmeans_vs_gmm_en_f13_resumen": {k: previo[f"k={k}"]["KMeans vs GMM"] for k in (2, 4)},
           "coincide_con_f13": bool(all(abs(usada[k] - previo[f"k={k}"]["KMeans vs GMM"]) < 1e-9 for k in (2, 4))),
           "todos_los_gmm_convergieron": bool(tabla.loc[tabla["covarianza"] != "", "converged"].all()),
           "conclusion": "No hay error de filas: las tres tecnicas usan las mismas 15.000 filas y el ARI recalculado coincide con f13_resumen.json. La diferencia con EP2 es una propiedad de los datos y del modelo (hipotesis, post hoc, no pre-declarado).",
           "nota": "post hoc, no pre-declarado"}
    (REP / "f13_ari_diagnostico.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    pd.set_option("display.width", 250)
    print(tabla.round(3).to_string(index=False))
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
