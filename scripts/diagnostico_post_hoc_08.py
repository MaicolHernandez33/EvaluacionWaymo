"""Diagnosticos post hoc (no pre-declarados) del aprendizaje no supervisado del notebook 08.

Uso (desde la raiz del repositorio):

    .venv/Scripts/python.exe -X utf8 scripts/diagnostico_post_hoc_08.py

Hace dos cosas, sin tocar features_B.parquet ni usar el target:
1. BIC del GMM: reproduce el ajuste del 08 (mismas variables FEAT_D, RobustScaler, covarianza completa, semilla 42) y mira
   si la caida brusca del BIC entre k = 2 y k = 3 se explica por covarianzas casi degeneradas en las variables discretas.
2. Segmentos de lluvia (reservados en EP2): asigna sus peatones y ciclistas a los clusters de KMeans con k = 2 y k = 4
   (reajustados con la misma semilla en train, que reproducen los tamanos de 08_clusters_perfil.csv) y compara la
   composicion con la de train.

Escribe data/08_reporting/08_post_hoc_gmm_bic.json, 08_post_hoc_lluvia_clusters.csv y 08_post_hoc_lluvia_resumen.json.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import RobustScaler

R = Path(__file__).resolve().parent.parent
REP = R / "data" / "08_reporting"
SEMILLA = 42
FEAT_D = ["distancia_m", "azimut_abs_deg", "log_pts", "log_dens", "log_vol", "n_ocl", "frac_cub", "dist_ocl_f"]
DISCRETAS = ["n_ocl", "frac_cub", "dist_ocl_f"]


def preparar(df):
    d = df.copy()
    d["dist_ocl_f"] = d["dist_ocl"].fillna(100.0)
    d["log_pts"], d["log_dens"], d["log_vol"] = np.log1p(d["num_lidar_points"]), np.log1p(d["densidad_puntos"]), np.log1p(d["volumen_caja"])
    return d


def oclusion(frame_boxes, objetivos):
    """Misma logica que la celda de oclusion del notebook 08: cajas mas cercanas del mismo frame que tapan el intervalo angular."""
    wrap = lambda a: (a + np.pi) % (2 * np.pi) - np.pi
    n_ocl, frac_cub, dist_ocl = np.zeros(len(objetivos)), np.zeros(len(objetivos)), np.full(len(objetivos), np.nan)
    pos_de = {k: i for i, k in enumerate(objetivos)}
    for _, g in frame_boxes.groupby(["segment_id", "key.frame_timestamp_micros"], sort=False):
        ids = g["key.laser_object_id"].values
        tgt = np.array([i for i, k in enumerate(zip(g["segment_id"].values, g["key.frame_timestamp_micros"].values, ids)) if k in pos_de], dtype=int)
        if len(tgt) == 0:
            continue
        cx, cy, L, W, H = (g[c].values for c in ["box_center_x", "box_center_y", "box_length", "box_width", "_h"])
        c_, s_ = np.cos(H), np.sin(H)
        lx, ly = np.array([1, 1, -1, -1]) * (L[:, None] / 2), np.array([1, -1, 1, -1]) * (W[:, None] / 2)
        X, Y = cx[:, None] + lx * c_[:, None] - ly * s_[:, None], cy[:, None] + lx * s_[:, None] + ly * c_[:, None]
        th = np.arctan2(cy, cx)
        dl = wrap(np.arctan2(Y, X) - th[:, None])
        lo, hi = dl.min(1), dl.max(1)
        r = np.hypot(cx, cy)
        d = wrap(th[None, :] - th[tgt][:, None])
        ov = np.clip(np.minimum(hi[tgt][:, None], d + hi[None, :]) - np.maximum(lo[tgt][:, None], d + lo[None, :]), 0, None)
        occ = (r[None, :] < r[tgt][:, None]) & (ov > 0)
        occ[np.arange(len(tgt)), tgt] = False
        ancho = np.maximum(hi[tgt] - lo[tgt], 1e-6)
        dd = np.where(occ, np.hypot(cx[None, :] - cx[tgt][:, None], cy[None, :] - cy[tgt][:, None]), np.inf).min(1)
        for j, t in enumerate(tgt):
            p = pos_de[(g["segment_id"].values[t], g["key.frame_timestamp_micros"].values[t], ids[t])]
            n_ocl[p] = occ[j].sum()
            frac_cub[p] = min(1.0, (ov[j] * occ[j]).sum() / ancho[j])
            dist_ocl[p] = np.nan if np.isinf(dd[j]) else dd[j]
    return n_ocl, frac_cub, dist_ocl


def main():
    t0 = time.time()
    fb = pd.read_parquet(R / "data" / "05_model_input" / "features_B.parquet")
    bz = preparar(fb)
    esc = RobustScaler().fit(bz[FEAT_D].values)
    Zr = esc.transform(bz[FEAT_D].values)

    # ---------------------------------------------------------- 1) BIC del GMM
    diag = {"fuente": "reproduccion del ajuste del notebook 08 (FEAT_D, RobustScaler, covarianza completa, semilla 42)", "filas": int(len(Zr)), "gmm_completo": {}, "gmm_solo_continuas": {}}
    for k in (2, 3, 4):
        gm = GaussianMixture(k, covariance_type="full", random_state=SEMILLA, max_iter=200).fit(Zr)
        varmin = float(min(np.diag(c).min() for c in gm.covariances_))
        eigmin = float(min(np.linalg.eigvalsh(c).min() for c in gm.covariances_))
        lab = gm.predict(Zr)
        unicos = {c: [int(len(np.unique(bz.loc[lab == i, c]))) for i in range(k)] for c in ("frac_cub", "n_ocl")}
        diag["gmm_completo"][f"k{k}"] = {"bic": float(gm.bic(Zr)), "convergio": bool(gm.converged_), "iteraciones": int(gm.n_iter_), "varianza_minima": varmin, "autovalor_minimo": eigmin,
                                         "valores_distintos_por_componente": unicos, "peso_minimo": float(gm.weights_.min())}
    cont = [c for c in FEAT_D if c not in DISCRETAS]
    Zc = RobustScaler().fit_transform(bz[cont].values)
    for k in (2, 3, 4):
        gm = GaussianMixture(k, covariance_type="full", random_state=SEMILLA, max_iter=200).fit(Zc)
        diag["gmm_solo_continuas"][f"k{k}"] = {"bic": float(gm.bic(Zc)), "varianza_minima": float(min(np.diag(c).min() for c in gm.covariances_))}
    reg_covar = 1e-6
    v3 = diag["gmm_completo"]["k3"]["varianza_minima"]
    diag["lectura"] = ("covarianzas casi degeneradas en las variables discretas" if v3 < 100 * reg_covar else "no se observan covarianzas degeneradas") + f" (varianza minima del GMM completo con k = 3: {v3:.2e}; reg_covar por defecto {reg_covar:.0e})"
    (REP / "08_post_hoc_gmm_bic.json").write_text(json.dumps(diag, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BIC GMM completo:", {k: round(v["bic"], 1) for k, v in diag["gmm_completo"].items()}, "| solo continuas:", {k: round(v["bic"], 1) for k, v in diag["gmm_solo_continuas"].items()})
    print(diag["lectura"])

    # ---------------------------------------------------------- 2) segmentos de lluvia
    perfil = pd.read_csv(REP / "08_clusters_perfil.csv")
    k34 = pd.read_csv(REP / "08_clusters_k3_k4.csv")
    comp = pd.read_parquet(R / "data" / "02_intermediate" / "waymo_con_target.parquet")
    ll = comp[comp["uso"] == "solo_clustering"].copy()
    ll["_h"] = ll["[LiDARBoxComponent].box.heading"]
    ll["azimut_abs_deg"] = np.abs(np.degrees(np.arctan2(ll["box_center_y"], ll["box_center_x"])))
    pob = ll[ll["object_type"].isin(["PEDESTRIAN", "CYCLIST"]) & (ll["azimut_abs_deg"] <= 120)].reset_index(drop=True)
    objetivos = list(zip(pob["segment_id"], pob["key.frame_timestamp_micros"], pob["key.laser_object_id"]))
    n_ocl, frac_cub, dist_ocl = oclusion(ll, objetivos)
    pob["n_ocl"], pob["frac_cub"], pob["dist_ocl"] = n_ocl, frac_cub, dist_ocl
    pob = preparar(pob)
    Zl = esc.transform(pob[FEAT_D].values)
    filas, ok = [], {}
    for k in (2, 4):
        km = KMeans(k, n_init=10, random_state=SEMILLA).fit(Zr)
        tam = np.sort(np.bincount(km.labels_))
        esperado = np.sort((perfil["filas"].values if k == 2 else k34[k34["k"] == "k4"]["filas"].values).astype(int))
        ok[f"k{k}"] = bool(np.array_equal(tam, esperado))
        lab_l = km.predict(Zl)
        for c in range(k):
            filas.append({"k": k, "cluster": c, "filas_train": int((km.labels_ == c).sum()), "% train": float((km.labels_ == c).mean()),
                          "filas_lluvia": int((lab_l == c).sum()), "% lluvia": float((lab_l == c).mean()),
                          "mediana puntos train": float(bz.loc[km.labels_ == c, "num_lidar_points"].median()), "mediana distancia train (m)": float(bz.loc[km.labels_ == c, "distancia_m"].median()),
                          "mediana puntos lluvia": float(pob.loc[lab_l == c, "num_lidar_points"].median()) if (lab_l == c).any() else np.nan,
                          "mediana distancia lluvia (m)": float(pob.loc[lab_l == c, "distancia_m"].median()) if (lab_l == c).any() else np.nan})
    tabla = pd.DataFrame(filas)
    tabla.to_csv(REP / "08_post_hoc_lluvia_clusters.csv", index=False)
    resumen = {"segmentos_lluvia": int(ll["segment_id"].nunique()), "filas_lluvia_todas_las_clases": int(len(ll)), "cajas_peatones_ciclistas_<=120": int(len(pob)),
               "cajas_ciclistas": int((pob["object_type"] == "CYCLIST").sum()), "clusters_reproducen_08": ok,
               "nota": "post hoc; no usa el target ni toca features_B.parquet; los segmentos de lluvia no tienen frames etiquetados, por eso se usan todos los frames"}
    (REP / "08_post_hoc_lluvia_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(tabla.round(3).to_string(index=False))
    print(resumen)
    print(f"({time.time() - t0:.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
