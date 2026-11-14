"""Fase 12 (post hoc, no pre-declarado): analisis en muestra sobre los 41 segmentos.

12.1 AUC por fold y brazos A/B/C (Regla top, LR3, XGB) y diferencia pareada C - A con IC por segmentos.
12.2 Sensibilidad del detector de huecos.  12.3 Equidad descriptiva de la regla en el punto A.  12.4 EDA y calidad de datos.
Escribe en data/08_reporting_ep3 (f12_*.csv, f12_resumen.json) e images/ep3 (2 figuras). Solo lectura sobre EP2 y v3.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.detector_huecos import tasa_por_celda  # noqa: E402
from waymo_evaluacion.ep3.metricas import Ranking, RankingDosPasos, desempate, ic95, pesos_bootstrap  # noqa: E402
from waymo_evaluacion.ep3.plan import verificar_plan_v3  # noqa: E402

REP, IMG = RAIZ / "data/08_reporting_ep3", RAIZ / "images/ep3"
NB = 1000
EP2_HUECOS = {("911012534050", 5), ("257766998801", 3)}


def datos():
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    h = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41_hueco.parquet").set_index("fila_id")["en_hueco"]
    pp = dev[dev["en_zona_principal"]].reset_index(drop=True)
    pp["en_hueco"] = h.loc[pp["fila_id"]].to_numpy().astype(bool)
    oof = pd.read_parquet(RAIZ / "data/07_model_output_ep3/f4_oof.parquet")
    par = json.loads((RAIZ / "data/06_models_ep3/detector_params_v3.json").read_text(encoding="utf-8"))
    return dev, pp, oof, {int(k): tuple(v) for k, v in par["rangos"].items()}, par


def r_a12_1(pp, oof, rangos):
    lista = pd.read_csv(REP / "lista_A_huecos.csv", dtype={"segmento": str})
    celdas = []
    for r in lista.itertuples():
        cam = int(r.camara.split()[0])
        m = ((pp["seg"] == r.segmento) & pp["az_signed"].between(*rangos[cam])).to_numpy()
        celdas.append({"seg": r.segmento, "cam": cam, "mask": m, "nombre": f"{r.segmento} camara {cam}"})
    aud_all = np.any([c["mask"] for c in celdas], axis=0)
    assert np.array_equal(aud_all, pp["en_hueco"].to_numpy()), "las celdas de la Lista A no coinciden con la marca por fila"
    y, f, seg = pp["sin_camara"].to_numpy(), pp["fold_s42"].to_numpy(), pp["seg"].to_numpy()
    cand = {"Regla top": oof["Regla top"].to_numpy(), "LR3": oof["LR3"].to_numpy(), "XGB": oof["XGB"].to_numpy()}
    filas = []
    for nombre, s in cand.items():
        for k in list(range(5)) + ["global"]:
            m = np.ones(len(y), bool) if k == "global" else f == k
            sanos = m & ~aud_all
            tb = desempate(int(m.sum()))
            ra = Ranking(y[m], s[m], tb).metricas()
            rb = Ranking(y[sanos], s[sanos], desempate(int(sanos.sum()))).metricas()
            rc = RankingDosPasos(y[m], s[m], tb, aud_all[m]).metricas()
            en = [c["nombre"] for c in celdas if (c["mask"] & m).any()]
            filas.append({"candidato": nombre, "fold": k, "segmentos": int(pd.Series(seg[m]).nunique()), "cajas": int(m.sum()), "positivos": int(y[m].sum()), "prevalencia": float(y[m].mean()),
                          "celdas_con_hueco": len(en), "hueco_contenido": "; ".join(en) if en else "ninguno", "cajas_en_hueco": int((aud_all & m).sum()),
                          "AUC_A": ra[0], "AUC_B_celdas_sanas": rb[0], "Fraccion80_A": ra[3], "Fraccion80_B_celdas_sanas": rb[3], "Fraccion80_C": rc[1],
                          "Captura20_A": ra[2], "Captura20_C": rc[0], "dif_C_menos_A_Fraccion80": rc[1] - ra[3]})
    tab = pd.DataFrame(filas)
    tab.to_csv(REP / "f12_auc_por_fold_brazos.csv", index=False)

    # ---- diferencia pareada C - A (bootstrap por segmentos)
    def boot(score, aud, sub, etiqueta, nombre):
        yy, ss, au, sg = y[sub], score[sub], aud[sub], seg[sub]
        cod = pd.factorize(sg)[0]
        tb = desempate(len(yy))
        ra, rc = Ranking(yy, ss, tb), RankingDosPasos(yy, ss, tb, au)
        w = pesos_bootstrap(cod, NB, 42)[:, cod]
        d = np.array([rc.metricas(w[b])[1] - ra.metricas(w[b])[3] for b in range(NB)])
        A, C = ra.metricas()[3], rc.metricas()[1]
        lo, hi = ic95(d)
        return {"candidato": nombre, "variante": etiqueta, "Fraccion80_A": A, "Fraccion80_C": C, "dif_C_menos_A": C - A, "ic_lo": lo, "ic_hi": hi, "excluye_0": bool(hi < 0 or lo > 0),
                "prop_replicas_C_mejor": float((d < 0).mean()), "segmentos": int(len(np.unique(cod))), "celdas_auditadas": int((np.unique(sg[au]).size) if au.any() else 0), "replicas": NB}
    todos = np.ones(len(y), bool)
    dif = []
    for nombre, s in cand.items():
        dif.append(boot(s, aud_all, todos, "global: ambas celdas auditadas", nombre))
        for c in celdas:
            dif.append(boot(s, c["mask"], todos, f"solo se audita {c['nombre']} (la otra celda queda en la cola)", nombre))
            sin = seg != c["seg"]
            dif.append(boot(s, aud_all & ~c["mask"], sin, f"se excluye el segmento {c['seg']} del analisis (queda solo la otra celda)", nombre))
    dif = pd.DataFrame(dif)
    dif.to_csv(REP / "f12_diferencia_C_menos_A.csv", index=False)
    return tab, dif, celdas


def r_12_2(dev, rangos, par):
    cam = sorted(rangos)
    tasa, nrango = tasa_por_celda(dev, rangos, cam)
    filas = []
    loo = pd.DataFrame(index=tasa.index, columns=tasa.columns, dtype=float)
    for s in tasa.index:
        loo.loc[s] = tasa.drop(index=s).median()
    for modo, med in (("con los 41 segmentos", None), ("sin el segmento candidato", loo)):
        for frac in (0.15, 0.20, 0.25, 0.30, 0.35):
            for minc in (50, 100, 200):
                marc = []
                for s in tasa.index:
                    for c in cam:
                        m = tasa[f"c{c}"].median() if med is None else med.loc[s, f"c{c}"]
                        n = nrango.loc[s, f"c{c}"]
                        if n >= minc and tasa.loc[s, f"c{c}"] < frac * m:
                            marc.append((s, c))
                suf = int((nrango >= minc).to_numpy().sum())
                falsas = [x for x in marc if x not in EP2_HUECOS]
                filas.append({"frac": frac, "min_cajas": minc, "mediana": modo, "celdas_totales": int(nrango.size), "celdas_con_n_suficiente": suf, "marcadas": len(marc),
                              "detecta_911012534050_cam5": ("911012534050", 5) in marc, "detecta_257766998801_cam3": ("257766998801", 3) in marc,
                              "detecta_los_2": EP2_HUECOS <= set(marc), "falsas_alarmas": len(falsas), "tasa_falsas_alarmas_sobre_celdas_con_n": len(falsas) / max(suf, 1),
                              "marcadas_lista": "; ".join(f"{s}|cam{c}" for s, c in marc), "es_la_configuracion_de_EP2": bool(frac == 0.25 and minc == 100 and med is None)})
    t = pd.DataFrame(filas)
    t.to_csv(REP / "f12_sensibilidad_detector.csv", index=False)
    return t


def r_12_3(pp, oof):
    umb = json.loads((RAIZ / "data/06_models_ep3/umbrales_v3.json").read_text(encoding="utf-8"))["A"]
    s = oof["Regla top"].to_numpy()
    flag = s >= umb
    pp = pp.assign(flag=flag, score=s, clase=np.where(pp["es_ciclista"] == 1, "CYCLIST", "PEDESTRIAN"))
    filas = []
    for var, col in (("ubicacion", "location"), ("momento_del_dia", "time_of_day"), ("clase", "clase"), ("todas", None)):
        niveles = [("todas", pp)] if col is None else [(v, g) for v, g in pp.groupby(col)]
        for nivel, g in niveles:
            for modo, gg in (("incluidas", g), ("excluidas", g[~g["en_hueco"]])):
                if len(gg) == 0:
                    continue
                y = gg["sin_camara"].to_numpy()
                pos, neg = int(y.sum()), int((1 - y).sum())
                filas.append({"variable": var, "grupo": nivel, "celdas_con_hueco": modo, "segmentos": int(gg["seg"].nunique()), "cajas": len(gg), "positivos": pos,
                              "recall_A": float((gg["flag"] & (y == 1)).sum() / max(pos, 1)), "pct_revisado_A": float(gg["flag"].mean()),
                              "precision_A": float((gg["flag"] & (y == 1)).sum() / max(gg["flag"].sum(), 1)),
                              "AUC": float(roc_auc_score(y, gg["score"])) if pos >= 200 and neg >= 200 else np.nan, "nota_AUC": "" if pos >= 200 and neg >= 200 else "menos de 200 cajas en alguna clase: no se calcula"})
    t = pd.DataFrame(filas)
    t.to_csv(REP / "f12_equidad.csv", index=False)
    return t, umb


def tasa_ic(pp, serie, orden):
    """Tasa de sin_camara por tramo con IC por segmentos (bootstrap con pesos)."""
    cod, segs = pd.factorize(pp["seg"])
    S = len(segs)
    w = pesos_bootstrap(cod, NB, 42)
    filas = []
    tot = np.zeros((S, len(orden)))
    pos = np.zeros((S, len(orden)))
    for j, t in enumerate(orden):
        m = (serie == t).to_numpy()
        tot[:, j] = np.bincount(cod[m], minlength=S)
        pos[:, j] = np.bincount(cod[m], weights=pp["sin_camara"].to_numpy()[m], minlength=S)
    num, den = w @ pos, w @ tot
    with np.errstate(invalid="ignore", divide="ignore"):
        tb = num / den
    for j, t in enumerate(orden):
        lo, hi = (ic95(tb[:, j]) if np.isfinite(tb[:, j]).any() else (np.nan, np.nan))
        filas.append({"tramo": str(t), "cajas": int(tot[:, j].sum()), "positivos": int(pos[:, j].sum()), "tasa": float(pos[:, j].sum() / max(tot[:, j].sum(), 1)), "ic_lo": lo, "ic_hi": hi,
                      "segmentos": int((tot[:, j] > 0).sum())})
    return pd.DataFrame(filas)


def r_12_4(pp):
    V16 = json.loads((RAIZ / "data/05_model_input_ep3/conjuntos_variables.json").read_text(encoding="utf-8"))["V16"]
    top = pd.cut(pp["num_top_lidar_points"], [-1, 5, 10, 20, 50, 100, np.inf], labels=["0-5", "6-10", "11-20", "21-50", "51-100", ">100"])
    az = pd.cut(pp["azimut_abs_deg"], [-0.001, 20, 40, 60, 80, 100.001], labels=["0-20", "20-40", "40-60", "60-80", "80-100"])
    dist = pd.qcut(pp["distancia_m"], 5)
    clase = pd.Series(np.where(pp["es_ciclista"] == 1, "CYCLIST", "PEDESTRIAN"), index=pp.index)
    tablas = []
    for nombre, serie, orden in (("puntos_top", top, list(top.cat.categories)), ("azimut_abs_deg", az, list(az.cat.categories)), ("distancia_m_quintiles", dist, list(dist.cat.categories)),
                                 ("clase", clase, ["PEDESTRIAN", "CYCLIST"])):
        t = tasa_ic(pp, serie, orden)
        t.insert(0, "variable", nombre)
        tablas.append(t)
    tasas = pd.concat(tablas, ignore_index=True)
    tasas.to_csv(REP / "f12_eda_tasas.csv", index=False)
    # ---- calidad
    full = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    filas = []
    for v in V16:
        x = pp[v]
        q1, q3 = x.quantile(0.25), x.quantile(0.75)
        iqr = q3 - q1
        bajo, alto = int((x < q1 - 1.5 * iqr).sum()), int((x > q3 + 1.5 * iqr).sum())
        filas.append({"variable": v, "nulos": int(x.isna().sum()), "pct_nulos": float(x.isna().mean()), "q1": q1, "q3": q3, "iqr": iqr, "atipicos_bajos": bajo, "atipicos_altos": alto,
                      "pct_atipicos": (bajo + alto) / len(x), "minimo": x.min(), "maximo": x.max()})
    cal = pd.DataFrame(filas)
    cal.to_csv(REP / "f12_eda_calidad.csv", index=False)
    llave = ["segment_id", "key.frame_timestamp_micros", "key.laser_object_id"]
    resumen = {"cajas_principal": int(len(pp)), "cajas_total_120": int(len(full)), "duplicados_por_llave_principal": int(pp.duplicated(llave).sum()), "duplicados_por_llave_total_120": int(full.duplicated(llave).sum()),
               "cajas_con_0_puntos_lidar": int((pp["num_lidar_points"] == 0).sum()), "pct_cajas_con_0_puntos_lidar": float((pp["num_lidar_points"] == 0).mean()),
               "cajas_con_0_puntos_top": int((pp["num_top_lidar_points"] == 0).sum()), "pct_cajas_con_0_puntos_top": float((pp["num_top_lidar_points"] == 0).mean()),
               "tasa_sin_camara_en_cajas_con_0_puntos_top": float(pp.loc[pp["num_top_lidar_points"] == 0, "sin_camara"].mean()), "nulos_total": int(pp[V16].isna().sum().sum())}
    (REP / "f12_eda_calidad_resumen.json").write_text(json.dumps(resumen, indent=1), encoding="utf-8")
    # ---- figuras
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.8), sharey=True)
    for ax, (nombre, tit) in zip(axes, (("puntos_top", "puntos del LiDAR superior"), ("azimut_abs_deg", "azimut (grados)"), ("distancia_m_quintiles", "distancia (quintiles, m)"))):
        d = tasas[tasas["variable"] == nombre]
        ax.errorbar(range(len(d)), d["tasa"], yerr=[d["tasa"] - d["ic_lo"], d["ic_hi"] - d["tasa"]], fmt="o-", color="#2a78d6", capsize=3)
        ax.set_xticks(range(len(d)), d["tramo"], rotation=30, ha="right", fontsize=8); ax.set_title(tit, fontsize=10); ax.grid(alpha=0.25)
        ax.axhline(pp["sin_camara"].mean(), color="k", ls="--", lw=1)
    axes[0].set_ylabel("tasa de sin_camara (IC 95 % por segmentos)")
    fig.suptitle("EDA en muestra (41 segmentos): tasa de sin_camara por tramo; linea: prevalencia global"); fig.tight_layout()
    fig.savefig(IMG / "12_eda_tasas.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    axes[0].barh(cal["variable"], 100 * cal["pct_atipicos"], color="#e07b39"); axes[0].set_xlabel("% de cajas fuera de 1,5 IQR"); axes[0].set_title("Atipicos por variable (regla de 1,5 IQR)"); axes[0].tick_params(axis="y", labelsize=7)
    axes[1].bar(["nulos (todas las variables)", "0 puntos LiDAR", "0 puntos top", "llaves duplicadas"],
                [100 * resumen["nulos_total"] / (len(pp) * len(V16)), 100 * resumen["pct_cajas_con_0_puntos_lidar"], 100 * resumen["pct_cajas_con_0_puntos_top"], 100 * resumen["duplicados_por_llave_principal"] / len(pp)], color="#8a8a8a")
    axes[1].set_ylabel("% de cajas"); axes[1].set_title("Calidad de datos"); axes[1].tick_params(axis="x", labelsize=7, rotation=15)
    fig.tight_layout(); fig.savefig(IMG / "12_eda_calidad.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    return tasas, cal, resumen


def main() -> None:
    verificar_plan_v3(RAIZ)
    dev, pp, oof, rangos, par = datos()
    tab, dif, celdas = r_a12_1(pp, oof, rangos)
    sens = r_12_2(dev, rangos, par)
    eq, umb = r_12_3(pp, oof)
    tasas, cal, cres = r_12_4(pp)
    reg = tab[tab["candidato"] == "Regla top"].set_index("fold")
    glob_ = dif[(dif["candidato"] == "Regla top") & dif["variante"].str.startswith("global")].iloc[0]
    razonables = sens[(sens["frac"].between(0.20, 0.30)) & (sens["min_cajas"].isin([50, 100]))]
    res = {
        "B_AUC_min_fold": {c: float(tab[(tab["candidato"] == c) & (tab["fold"] != "global")]["AUC_B_celdas_sanas"].min()) for c in ("Regla top", "LR3", "XGB")},
        "B_cumple_AUC_min_fold_0_75": {c: bool(tab[(tab["candidato"] == c) & (tab["fold"] != "global")]["AUC_B_celdas_sanas"].min() >= 0.75) for c in ("Regla top", "LR3", "XGB")},
        "A_AUC_min_fold": {c: float(tab[(tab["candidato"] == c) & (tab["fold"] != "global")]["AUC_A"].min()) for c in ("Regla top", "LR3", "XGB")},
        "C_en_fold_1_regla": {"Fraccion80_A": float(reg.loc[1, "Fraccion80_A"]), "Fraccion80_C": float(reg.loc[1, "Fraccion80_C"]), "hueco": reg.loc[1, "hueco_contenido"]},
        "C_en_fold_0_regla": {"Fraccion80_A": float(reg.loc[0, "Fraccion80_A"]), "Fraccion80_C": float(reg.loc[0, "Fraccion80_C"]), "hueco": reg.loc[0, "hueco_contenido"]},
        "dif_C_menos_A_global_regla": {k: (float(glob_[k]) if k != "excluye_0" else bool(glob_[k])) for k in ("dif_C_menos_A", "ic_lo", "ic_hi", "excluye_0", "prop_replicas_C_mejor")},
        "detector_combinaciones": int(len(sens)), "detector_combinaciones_que_detectan_los_2": int(sens["detecta_los_2"].sum()),
        "detector_razonables_que_detectan_los_2": [int(razonables["detecta_los_2"].sum()), int(len(razonables))],
        "detector_falsas_alarmas_rango": [int(sens["falsas_alarmas"].min()), int(sens["falsas_alarmas"].max())],
        "detector_ep2": {k: (int(v) if isinstance(v, (np.integer,)) else v) for k, v in sens[sens["es_la_configuracion_de_EP2"]].iloc[0][["marcadas", "falsas_alarmas", "celdas_con_n_suficiente"]].items()},
        "umbral_A_regla": umb, "equidad_filas": int(len(eq)), "eda": cres,
    }
    (REP / "f12_resumen.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(tab[tab["candidato"] == "Regla top"][["fold", "segmentos", "cajas", "celdas_con_hueco", "AUC_A", "AUC_B_celdas_sanas", "Fraccion80_A", "Fraccion80_B_celdas_sanas", "Fraccion80_C", "hueco_contenido"]].round(3).to_string(index=False))
    print(dif[dif["candidato"] == "Regla top"][["variante", "Fraccion80_A", "Fraccion80_C", "dif_C_menos_A", "ic_lo", "ic_hi", "excluye_0", "segmentos"]].round(3).to_string(index=False))
    print(json.dumps(res, indent=1, ensure_ascii=False)[:2600])


if __name__ == "__main__":
    main()
