"""Fase 13 (descriptivo; NO esta en el plan v3: post hoc, no pre-declarado): aprendizaje no supervisado sobre la poblacion principal.

Variables: distancia_m, azimut_abs_deg, log1p(num_lidar_points), log1p(densidad_puntos), log1p(volumen_caja), estandarizadas.
No usa sin_camara ni nada del par 2D. EP2 uso ademas variables de oclusion que no estan en dev_41.
Escribe data/08_reporting_ep3/f13_*.csv|json, data/07_model_output_ep3/f13_clusters.parquet y data/06_models_ep3/no_supervisado_v3.joblib (+ manifest aparte).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import adjusted_rand_score, brier_score_loss, calinski_harabasz_score, davies_bouldin_score, roc_auc_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.metricas import ConjuntoOOF, ic95, pesos_bootstrap  # noqa: E402
from waymo_evaluacion.ep3.plan import leer_hashes, verificar_plan_v3  # noqa: E402

REP, MOD, OUT = RAIZ / "data/08_reporting_ep3", RAIZ / "data/06_models_ep3", RAIZ / "data/07_model_output_ep3"
SEM = 42
COLS = ["distancia_m", "azimut_abs_deg", "log_puntos", "log_densidad", "log_volumen"]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def caracteristicas(pp: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"distancia_m": pp["distancia_m"].to_numpy(), "azimut_abs_deg": pp["azimut_abs_deg"].to_numpy(), "log_puntos": np.log1p(pp["num_lidar_points"].to_numpy(float)),
                         "log_densidad": np.log1p(pp["densidad_puntos"].to_numpy(float)), "log_volumen": np.log1p(pp["volumen_caja"].to_numpy(float))})


def tasa_por_grupo(pp: pd.DataFrame, etiqueta: np.ndarray, nb: int = 1000) -> pd.DataFrame:
    cod, segs = pd.factorize(pp["seg"])
    S = len(segs)
    w = pesos_bootstrap(cod, nb, SEM)
    niv = sorted(set(etiqueta))
    y = pp["sin_camara"].to_numpy()
    tot = np.stack([np.bincount(cod[etiqueta == g], minlength=S) for g in niv], 1).astype(float)
    pos = np.stack([np.bincount(cod[etiqueta == g], weights=y[etiqueta == g], minlength=S) for g in niv], 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        tb = (w @ pos) / (w @ tot)
    filas = []
    for j, g in enumerate(niv):
        lo, hi = ic95(tb[:, j])
        filas.append({"cluster": g, "cajas": int(tot[:, j].sum()), "pct_cajas": float(tot[:, j].sum() / tot.sum()), "positivos": int(pos[:, j].sum()), "tasa_sin_camara": float(pos[:, j].sum() / tot[:, j].sum()),
                      "ic_lo": lo, "ic_hi": hi, "segmentos": int((tot[:, j] > 0).sum())})
    return pd.DataFrame(filas)


def nombrar(perfil: pd.DataFrame, glob: pd.DataFrame) -> list[str]:
    q = glob[["distancia_m", "densidad_puntos"]].quantile([1 / 3, 2 / 3])
    nom = []
    for _, r in perfil.iterrows():
        d = "cercanos" if r["distancia_m"] < q.loc[1 / 3, "distancia_m"] else ("lejanos" if r["distancia_m"] > q.loc[2 / 3, "distancia_m"] else "a distancia media")
        e = "poco densos" if r["densidad_puntos"] < q.loc[1 / 3, "densidad_puntos"] else ("densos" if r["densidad_puntos"] > q.loc[2 / 3, "densidad_puntos"] else "de densidad media")
        nom.append(f"{d} y {e}")
    return nom


def main() -> None:
    verificar_plan_v3(RAIZ)
    t0 = time.time()
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = dev[dev["en_zona_principal"]].reset_index(drop=True)
    pcal = pd.read_parquet(OUT / "f5_pcal.parquet")["pcal_Regla top"].to_numpy()
    X = caracteristicas(pp)
    sc = StandardScaler().fit(X)
    Z = sc.transform(X)
    rng = np.random.default_rng(SEM)
    i20 = rng.choice(len(Z), 20000, replace=False)
    i15 = rng.choice(len(Z), 15000, replace=False)

    # ---- 13.2 seleccion de k
    sel, km = [], {}
    for k in range(2, 9):
        m = KMeans(k, n_init=10, random_state=SEM).fit(Z)
        km[k] = m
        sel.append({"k": k, "silhouette_muestra_20000": float(silhouette_score(Z[i20], m.labels_[i20])), "davies_bouldin": float(davies_bouldin_score(Z, m.labels_)),
                    "calinski_harabasz": float(calinski_harabasz_score(Z, m.labels_)), "tamano_cluster_mas_chico": float(np.bincount(m.labels_).min() / len(Z))})
    gm = {k: GaussianMixture(k, covariance_type="full", n_init=2, random_state=SEM).fit(Z[i15]) for k in range(2, 9)}
    for r in sel:
        r["BIC_GMM_muestra_15000"] = float(gm[r["k"]].bic(Z[i15]))
    selt = pd.DataFrame(sel)
    selt.to_csv(REP / "f13_seleccion_k.csv", index=False)
    k_el = int(selt[selt["k"] <= 6].sort_values("silhouette_muestra_20000", ascending=False).iloc[0]["k"])
    ks = sorted({k_el, 4})
    ward = linkage(Z[i15], "ward")
    ari = {}
    for k in ks:
        a = km[k].predict(Z[i15])
        b = gm[k].predict(Z[i15])
        c = fcluster(ward, k, "maxclust")
        ari[f"k={k}"] = {"KMeans vs GMM": adjusted_rand_score(a, b), "KMeans vs Ward": adjusted_rand_score(a, c), "GMM vs Ward": adjusted_rand_score(b, c)}
    # estabilidad al remuestrear segmentos
    cod, segs = pd.factorize(pp["seg"])
    idx_seg = [np.flatnonzero(cod == s) for s in range(len(segs))]
    estab = []
    for k in ks:
        ref = km[k].labels_
        aris = []
        for r in range(30):
            rr = np.random.default_rng(SEM + 1000 + r)
            filas = np.concatenate([idx_seg[j] for j in rr.integers(0, len(segs), len(segs))])
            m = KMeans(k, n_init=3, random_state=SEM + r).fit(Z[filas])
            aris.append(adjusted_rand_score(ref, m.predict(Z)))
        estab.append({"k": k, "remuestreos": 30, "ari_medio": float(np.mean(aris)), "ari_minimo": float(np.min(aris)), "ari_p5": float(np.quantile(aris, 0.05)), "nota": "KMeans n_init=3 en cada remuestreo (el modelo de referencia usa n_init=10); scaler fijo"})
    pd.DataFrame(estab).to_csv(REP / "f13_estabilidad.csv", index=False)

    # ---- 13.3 cruce con sin_camara, perfil y aporte sobre la regla
    glob = pd.DataFrame({"distancia_m": pp["distancia_m"], "densidad_puntos": pp["densidad_puntos"]})
    aporte = []
    etiquetas = {}
    for k in ks:
        lab = km[k].labels_
        etiquetas[k] = lab
        t = tasa_por_grupo(pp, lab)
        per = pp.assign(cl=lab).groupby("cl")[["distancia_m", "azimut_abs_deg", "num_lidar_points", "num_top_lidar_points", "densidad_puntos", "volumen_caja"]].median()
        per.columns = ["mediana_" + c for c in per.columns]
        t = t.merge(per, left_on="cluster", right_index=True)
        t["tipo_de_caso"] = nombrar(per.rename(columns=lambda c: c.replace("mediana_", "")), pp)
        t["prob_media_regla_platt"] = [float(pcal[lab == g].mean()) for g in t["cluster"]]
        t["diferencia_tasa_menos_prob_regla"] = t["tasa_sin_camara"] - t["prob_media_regla_platt"]
        t["AUC_regla_dentro_del_cluster"] = [float(roc_auc_score(pp["sin_camara"].to_numpy()[lab == g], pcal[lab == g])) if (pp["sin_camara"].to_numpy()[lab == g].sum() >= 200 and (1 - pp["sin_camara"].to_numpy()[lab == g]).sum() >= 200) else np.nan for g in t["cluster"]]
        t.insert(0, "k", k)
        t.to_csv(REP / f"f13_clusters_k{k}.csv", index=False)
        # aporta algo que la regla no tenga? regresion logistica por segmento (GroupKFold 5): logit(pcal) con y sin clusters
        lg = np.log(np.clip(pcal, 1e-6, 1 - 1e-6) / (1 - np.clip(pcal, 1e-6, 1 - 1e-6)))
        D = np.eye(k)[lab][:, 1:]
        y = pp["sin_camara"].to_numpy()
        o1, o2 = np.zeros(len(y)), np.zeros(len(y))
        for tr, va in GroupKFold(5).split(lg, y, pp["seg"]):
            o1[va] = LogisticRegression(C=1e6, max_iter=500).fit(lg[tr, None], y[tr]).predict_proba(lg[va, None])[:, 1]
            o2[va] = LogisticRegression(C=1e6, max_iter=500).fit(np.c_[lg[tr], D[tr]], y[tr]).predict_proba(np.c_[lg[va], D[va]])[:, 1]
        conj = ConjuntoOOF(y, pp["seg"].to_numpy(), {"regla": [o1], "regla_mas_cluster": [o2]})
        bt = conj.bootstrap(["regla", "regla_mas_cluster"], 1000, SEM)
        dif = bt["regla_mas_cluster"][:, 0] - bt["regla"][:, 0]
        lo, hi = ic95(dif)
        aporte.append({"k": k, "AUC_regla": float(roc_auc_score(y, o1)), "AUC_regla_mas_cluster": float(roc_auc_score(y, o2)), "dif_AUC": float(roc_auc_score(y, o2) - roc_auc_score(y, o1)), "ic_lo": lo, "ic_hi": hi,
                       "Brier_regla": float(brier_score_loss(y, o1)), "Brier_regla_mas_cluster": float(brier_score_loss(y, o2)), "excluye_0": bool(lo > 0 or hi < 0),
                       "metodo": "regresion logistica sobre logit(prob. de la regla) con y sin indicadoras de cluster; GroupKFold(5) por segmento; IC por segmentos (1000 replicas)"})
    pd.DataFrame(aporte).to_csv(REP / "f13_aporte_cluster.csv", index=False)

    # ---- 13.4 IsolationForest
    iso = IsolationForest(contamination=0.01, random_state=SEM, n_jobs=6).fit(Z)
    at = iso.predict(Z) == -1
    y = pp["sin_camara"].to_numpy()
    por_seg = pd.Series(pp["seg"].to_numpy()[at]).value_counts()
    ti = tasa_por_grupo(pp, at.astype(int))
    iso_res = {"cajas_atipicas": int(at.sum()), "porcentaje": float(at.mean()), "segmentos_con_atipicos": int(por_seg.size), "segmentos_total": int(len(segs)),
               "tasa_sin_camara_atipicas": float(y[at].mean()), "tasa_sin_camara_resto": float(y[~at].mean()), "ic_atipicas": [float(ti.loc[ti["cluster"] == 1, "ic_lo"].iloc[0]), float(ti.loc[ti["cluster"] == 1, "ic_hi"].iloc[0])],
               "ic_resto": [float(ti.loc[ti["cluster"] == 0, "ic_lo"].iloc[0]), float(ti.loc[ti["cluster"] == 0, "ic_hi"].iloc[0])],
               "top3_segmentos_aportan": [{"seg": s, "atipicos": int(n), "pct_de_los_atipicos": float(n / at.sum())} for s, n in por_seg.head(3).items()]}
    pd.DataFrame([iso_res]).drop(columns=["top3_segmentos_aportan", "ic_atipicas", "ic_resto"]).to_csv(REP / "f13_isolation_forest.csv", index=False)
    lab_df = pd.DataFrame({"fila_pp": np.arange(len(pp)), **{f"cluster_k{k}": etiquetas[k] for k in ks}, "atipico_iforest": at})
    lab_df.to_parquet(OUT / "f13_clusters.parquet", index=False)

    # ---- 13.5 guardar y sellar
    art = {"scaler": sc, "columnas": COLS, "k_elegido": k_el, f"kmeans_k{k_el}": km[k_el], "kmeans_k4": km[4], "isolation_forest": iso,
           "nombres": {f"k{k}": json.loads(pd.read_csv(REP / f"f13_clusters_k{k}.csv").set_index("cluster")["tipo_de_caso"].to_json()) for k in ks},
           "descripcion": "Descriptivo (post hoc, no pre-declarado). No se usa para puntuar: solo para etiquetar el tipo de caso en la pagina. Sin sin_camara; sin variables de oclusion."}
    ruta = MOD / "no_supervisado_v3.joblib"
    joblib.dump(art, ruta)
    man = {"version": "no_supervisado_v3", "creado": time.strftime("%Y-%m-%dT%H:%M:%S"), "sha256": {"no_supervisado_v3.joblib": sha256(ruta)}, "k_elegido": k_el, "semilla": SEM,
           "columnas": COLS, "plan_v3_sha256": leer_hashes(RAIZ / "docs/ep3"), "nota": "independiente de manifest_v3.json; descriptivo, post hoc, no pre-declarado"}
    (MOD / "manifest_no_supervisado.json").write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding="utf-8")

    # ---- 13.6 comparacion con EP2 (EP2 solo se lee)
    e2k = pd.read_csv(RAIZ / "data/08_reporting/08_clusters_seleccion_k.csv").set_index("k")
    e2v = pd.read_csv(RAIZ / "data/08_reporting/08_clusters_vs_franja.csv")
    e2r = json.loads((RAIZ / "data/08_reporting/08_no_supervisado_resumen.json").read_text(encoding="utf-8"))
    f4 = e2v[(e2v["k"] == "k = 4") & e2v["nombre"].str.contains("lejanos")].iloc[0]
    c4 = pd.read_csv(REP / "f13_clusters_k4.csv")
    mas_alto = c4.sort_values("tasa_sin_camara", ascending=False).iloc[0]
    est = {e["k"]: e for e in estab}
    comp = pd.DataFrame([
        {"medida": "k elegido (maximo silhouette)", "EP2": int(e2r["k_elegido"]), "EP3": k_el, "fuente_EP2": "08_no_supervisado_resumen.json", "fuente_EP3": "f13_seleccion_k.csv"},
        {"medida": "silhouette con k=2", "EP2": float(e2k.loc[2, "silhouette"]), "EP3": float(selt.set_index("k").loc[2, "silhouette_muestra_20000"]), "fuente_EP2": "08_clusters_seleccion_k.csv", "fuente_EP3": "f13_seleccion_k.csv"},
        {"medida": "silhouette con k=4", "EP2": float(e2k.loc[4, "silhouette"]), "EP3": float(selt.set_index("k").loc[4, "silhouette_muestra_20000"]), "fuente_EP2": "08_clusters_seleccion_k.csv", "fuente_EP3": "f13_seleccion_k.csv"},
        {"medida": "tasa sin_camara del cluster de mayor tasa con k=4 (%)", "EP2": float(f4["tasa con franja (%)"]), "EP3": float(100 * mas_alto["tasa_sin_camara"]), "fuente_EP2": "08_clusters_vs_franja.csv (cluster 'lejanos, poco densos y ocluidos', 13.584 filas)", "fuente_EP3": f"f13_clusters_k4.csv (cluster {int(mas_alto['cluster'])}: {mas_alto['tipo_de_caso']}, {int(mas_alto['cajas'])} cajas)"},
        {"medida": "IsolationForest: tasa sin_camara de atipicas (%)", "EP2": 100 * e2r["isolation_forest"]["tasa_sin_camara_atipicas"], "EP3": 100 * iso_res["tasa_sin_camara_atipicas"], "fuente_EP2": "08_no_supervisado_resumen.json", "fuente_EP3": "f13_isolation_forest.csv"},
        {"medida": "IsolationForest: tasa de las no atipicas (%)", "EP2": 100 * e2r["isolation_forest"]["tasa_sin_camara_resto"], "EP3": 100 * iso_res["tasa_sin_camara_resto"], "fuente_EP2": "08_no_supervisado_resumen.json", "fuente_EP3": "f13_isolation_forest.csv"},
        {"medida": "IsolationForest: segmentos que aportan atipicos", "EP2": e2r["isolation_forest"]["segmentos"], "EP3": iso_res["segmentos_con_atipicos"], "fuente_EP2": "08_no_supervisado_resumen.json", "fuente_EP3": "f13_isolation_forest.csv"},
        {"medida": "estabilidad: ARI medio al remuestrear segmentos (k elegido)", "EP2": e2r["estabilidad_por_segmento"]["ari_medio"], "EP3": est[k_el]["ari_medio"], "fuente_EP2": "08_no_supervisado_resumen.json", "fuente_EP3": "f13_estabilidad.csv"},
        {"medida": "estabilidad: ARI minimo (k elegido)", "EP2": e2r["estabilidad_por_segmento"]["ari_minimo"], "EP3": est[k_el]["ari_minimo"], "fuente_EP2": "08_no_supervisado_resumen.json", "fuente_EP3": "f13_estabilidad.csv"},
        {"medida": "ARI KMeans vs GMM (k elegido)", "EP2": e2r["ari_entre_tecnicas"]["KMeans vs GMM"], "EP3": ari[f"k={k_el}"]["KMeans vs GMM"], "fuente_EP2": "08_no_supervisado_resumen.json", "fuente_EP3": "f13_resumen.json"},
    ])
    comp.to_csv(REP / "f13_comparacion_ep2_ep3.csv", index=False)
    resumen = {"filas": int(len(pp)), "variables": COLS, "k_elegido": k_el, "ks_analizados": ks, "ari_entre_tecnicas": ari, "estabilidad": estab, "isolation_forest": iso_res, "aporte_sobre_regla": aporte,
               "muestras": {"silhouette": 20000, "gmm_y_ward": 15000}, "segundos": time.time() - t0, "sha256_no_supervisado_v3": man["sha256"]["no_supervisado_v3.joblib"]}
    (REP / "f13_resumen.json").write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(selt.round(3).to_string(index=False))
    for k in ks:
        print(pd.read_csv(REP / f"f13_clusters_k{k}.csv")[["k", "cluster", "cajas", "pct_cajas", "tasa_sin_camara", "ic_lo", "ic_hi", "tipo_de_caso", "prob_media_regla_platt", "diferencia_tasa_menos_prob_regla", "AUC_regla_dentro_del_cluster"]].round(3).to_string(index=False))
    print(pd.DataFrame(aporte).drop(columns=["metodo"]).round(4).to_string(index=False)); print(json.dumps({k: resumen[k] for k in ("ari_entre_tecnicas", "estabilidad", "isolation_forest")}, indent=1, ensure_ascii=False)[:2200]); print(comp.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
