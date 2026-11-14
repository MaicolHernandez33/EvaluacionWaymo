"""F5 (IE11, parte 1): metricas de generalizacion de todos los candidatos, brazos A, B y C.

Lee los checkpoints de F4 (predicciones de validacion y scores internos de entrenamiento por fold).
Umbrales de los puntos A (recall objetivo 0,80) y B (20 % de revision) y calibracion Platt se fijan SOLO con
los scores internos (OOF interno por segmento) de las filas de entrenamiento de cada fold externo.
Salidas en data/08_reporting_ep3: f5_metricas_candidatos.csv, f5_brazoC.csv, f5_brazoB.csv,
f5_auc_por_fold.csv, f5_auc_por_segmento.csv, f5_calibracion_bins.csv, f5_resumen.json.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import brier_score_loss, roc_auc_score  # noqa: E402

from waymo_evaluacion.ep3.metricas import (  # noqa: E402
    METRICAS, ConjuntoOOF, RankingDosPasos, desempate, ece_cuantiles, f1_accuracy, ic95, pesos_bootstrap, umbral_para_recall, umbral_para_revision,
)
from waymo_evaluacion.ep3.plan import cargar_plan_v3  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
SEM = 42
# nombre del candidato -> clave en F4
CANDIDATOS = {"Regla top": "regla_top", "LR3": "LR3", "LR": "base_LR", "RF": "base_RF", "HGB": "base_HGB", "XGB": "base_XGB", "LGBM": "base_LGBM",
              "E1": "E1", "E2": "E2", "E3": "E3", "E4": "E4"}
ES_PROBABILIDAD = {"LR3", "LR", "RF", "HGB", "XGB", "LGBM", "E1", "E3", "E4"}


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def caracteristica(nombre: str, s: np.ndarray) -> np.ndarray:
    """Variable de entrada de la calibracion Platt: logit para probabilidades; log del conteo para la regla; el rango tal cual para E2."""
    if nombre in ES_PROBABILIDAD:
        return _logit(s).reshape(-1, 1)
    if nombre == "Regla top":
        return (-np.log1p(-s)).reshape(-1, 1)
    return np.asarray(s, dtype=float).reshape(-1, 1)


def conf_ponderada(flag, y, w):
    tp, fp, fn = (w * (flag & (y == 1))).sum(), (w * (flag & (y == 0))).sum(), (w * (~flag & (y == 1))).sum()
    return tp / max(tp + fn, 1e-12), tp / max(tp + fp, 1e-12)


def main() -> None:
    plan = cargar_plan_v3(RAIZ)
    pp = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    hueco = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41_hueco.parquet").set_index("fila_id")["en_hueco"]
    pp = pp[pp["en_zona_principal"]].reset_index(drop=True)
    aud = hueco.loc[pp["fila_id"]].to_numpy().astype(bool)
    y, seg, fold = pp["sin_camara"].to_numpy(), pp["seg"].to_numpy(), pp[f"fold_s{SEM}"].to_numpy()
    n = len(pp)
    res = [joblib.load(p) for p in sorted(glob.glob(str(REP / "f4_ckpt/f4_f?.pkl")))]
    assert len(res) == 5, "faltan folds de F4"

    punt, flagA, flagB, pcal, flagC_A, flagC_B = {}, {}, {}, {}, {}, {}
    for nom, k in CANDIDATOS.items():
        vp, fa, fb, pc, ca, cb = np.zeros(n), np.zeros(n, bool), np.zeros(n, bool), np.zeros(n), np.zeros(n, bool), np.zeros(n, bool)
        for r in res:
            va, tr = r["idx_val"], r["idx_tr"]
            s_va, s_tr = r["pred"][k], r["inner"][k]
            vp[va] = s_va
            fa[va] = s_va >= umbral_para_recall(y[tr], s_tr, 0.80)
            fb[va] = s_va >= umbral_para_revision(s_tr, 0.20)
            platt = LogisticRegression(C=1e6, max_iter=1000).fit(caracteristica(nom, s_tr), y[tr])
            pc[va] = platt.predict_proba(caracteristica(nom, s_va))[:, 1]
            # brazo C, punto A: la cola B debe aportar lo que falta para 0,80 de recall del proceso (auditoria + cola)
            sana_tr = ~aud[tr]
            falta = 0.80 * y[tr].sum() - y[tr][~sana_tr].sum()
            sana_va = ~aud[va]
            if falta <= 0:
                ca[va] = False
            else:
                o = np.argsort(-s_tr[sana_tr], kind="stable")
                cum = np.cumsum(y[tr][sana_tr][o])
                kk = min(int(np.searchsorted(cum, falta)), len(o) - 1)
                ca[va] = sana_va & (s_va >= s_tr[sana_tr][o][kk])
            # brazo C, punto B: 20 % de las cajas del total revisadas individualmente (cola B)
            presup = int(np.ceil(0.20 * len(tr)))
            s_sana = np.sort(s_tr[sana_tr])[::-1]
            thr = s_sana[min(presup, len(s_sana)) - 1]
            cb[va] = sana_va & (s_va >= thr)
        punt[nom], flagA[nom], flagB[nom], pcal[nom], flagC_A[nom], flagC_B[nom] = vp, fa, fb, pc, ca, cb

    conj = ConjuntoOOF(y, seg, {k: [v] for k, v in punt.items()})
    nb = 1000
    pesos = pesos_bootstrap(conj.seg_codes, nb, 42)
    W_rows = pesos[:, conj.seg_codes]                           # (nb, n)
    boot = conj.bootstrap(list(punt), nb, 42)
    tb = conj.tb

    # ---- tabla principal (brazo A)
    filas, bins_rows, por_fold, por_seg = [], [], [], []
    for nom in CANDIDATOS:
        m = conj.metricas(nom)
        f = {"candidato": nom}
        for j, k in enumerate(METRICAS):
            lo, hi = ic95(boot[nom][:, j])
            f.update({k: m[j], f"{k}_lo": lo, f"{k}_hi": hi})
        for etiqueta, fl in (("A", flagA[nom]), ("B", flagB[nom])):
            rb, pb = zip(*[conf_ponderada(fl, y, W_rows[b]) for b in range(nb)])
            r0, p0 = conf_ponderada(fl, y, np.ones(n))
            f.update({f"recall_{etiqueta}": r0, f"recall_{etiqueta}_lo": ic95(np.array(rb))[0], f"recall_{etiqueta}_hi": ic95(np.array(rb))[1],
                      f"precision_{etiqueta}": p0, f"pct_revisar_{etiqueta}": float(fl.mean())})
            f.update({f"F1_{etiqueta}": f1_accuracy(fl, y)["F1"], f"accuracy_{etiqueta}": f1_accuracy(fl, y)["accuracy"]})
        e_cal, g = ece_cuantiles(y, pcal[nom])
        f.update({"ECE_cal": e_cal, "Brier_cal": float(brier_score_loss(y, pcal[nom]))})
        if nom in ES_PROBABILIDAD:
            f["ECE_crudo"] = ece_cuantiles(y, punt[nom])[0]
        g = g.reset_index().assign(candidato=nom)
        bins_rows.append(g)
        aucs_fold = [roc_auc_score(y[fold == k], punt[nom][fold == k]) for k in range(5)]
        for k, a in enumerate(aucs_fold):
            por_fold.append({"candidato": nom, "fold": k, "AUC": a, "positivos": int(y[fold == k].sum()), "filas": int((fold == k).sum())})
        sa = {}
        for g_, idx in pd.Series(np.arange(n)).groupby(seg):
            ii = idx.to_numpy()
            if y[ii].sum() >= 100 and (1 - y[ii]).sum() >= 100:
                sa[g_] = roc_auc_score(y[ii], punt[nom][ii])
        for g_, a in sa.items():
            por_seg.append({"candidato": nom, "segmento": g_, "AUC": a})
        f.update({"AUC_min_fold": float(min(aucs_fold)), "AUC_mediana_segmento": float(np.median(list(sa.values()))), "segmentos_en_mediana": len(sa)})
        filas.append(f)
    tabla = pd.DataFrame(filas)
    p7 = plan["P7"]["estabilidad"]
    tabla["estable"] = (tabla["AUC_min_fold"] >= p7["auc_min_fold"]) & (tabla["AUC_mediana_segmento"] >= p7["mediana_auc_segmento"])
    tabla["prevalencia"] = float(y.mean())
    tabla.to_csv(REP / "f5_metricas_candidatos.csv", index=False)
    pd.DataFrame(por_fold).to_csv(REP / "f5_auc_por_fold.csv", index=False)
    pd.DataFrame(por_seg).to_csv(REP / "f5_auc_por_segmento.csv", index=False)
    pd.concat(bins_rows).to_csv(REP / "f5_calibracion_bins.csv", index=False)

    # ---- brazo C (dos pasos) y punto de equilibrio
    celdas_por_seg = pd.read_csv(REP / "lista_A_huecos.csv", dtype={"segmento": str})["segmento"].value_counts()
    cel = np.array([celdas_por_seg.get(s, 0) for s in conj.segmentos])        # celdas con hueco por segmento (indice = codigo)
    cfilas = []
    for nom in CANDIDATOS:
        rc = RankingDosPasos(y, punt[nom], tb, aud)
        m = rc.metricas()
        ra = conj.metricas(nom)
        bc, be = [], []
        for b in range(nb):
            w = W_rows[b]
            mm = rc.metricas(w)
            bc.append(mm)
            celdas = (pesos[b] * cel).sum()
            be.append(w.sum() * (conj.metricas(nom, pesos[b])[3] - mm[1]) / celdas if celdas > 0 else np.nan)
        bc, be = np.array(bc), np.array(be)
        celdas0 = cel.sum()
        eq = float(n * (ra[3] - m[1]) / celdas0)
        found = aud | flagC_A[nom]
        cfilas.append({
            "candidato": nom, "Captura@20_C": m[0], "Captura@20_C_lo": ic95(bc[:, 0])[0], "Captura@20_C_hi": ic95(bc[:, 0])[1],
            "Fraccion_80_C": m[1], "Fraccion_80_C_lo": ic95(bc[:, 1])[0], "Fraccion_80_C_hi": ic95(bc[:, 1])[1],
            "Captura@20_A": ra[2], "Fraccion_80_A": ra[3],
            "equilibrio_cajas_por_auditoria": eq, "equilibrio_lo": ic95(be)[0], "equilibrio_hi": ic95(be)[1], "celdas_auditadas": int(celdas0),
            "recall_A_proceso_C": float((found & (y == 1)).sum() / y.sum()), "pct_cajas_revisadas_A_C": float(flagC_A[nom].mean()),
            "recall_B_proceso_C": float(((aud | flagC_B[nom]) & (y == 1)).sum() / y.sum()), "positivos_cubiertos_por_auditoria": int((aud & (y == 1)).sum()),
        })
    pd.DataFrame(cfilas).to_csv(REP / "f5_brazoC.csv", index=False)

    # ---- brazo B: solo celdas sanas (sensibilidad)
    sana = ~aud
    cb = ConjuntoOOF(y[sana], seg[sana], {k: [v[sana]] for k, v in punt.items()})
    pd.DataFrame([{"candidato": k, **dict(zip(METRICAS, cb.metricas(k)))} for k in punt]).assign(filas=int(sana.sum()), positivos=int(y[sana].sum())).to_csv(REP / "f5_brazoB.csv", index=False)

    resumen = {"filas": n, "positivos": int(y.sum()), "prevalencia": float(y.mean()), "filas_auditoria": int(aud.sum()), "positivos_auditoria": int((aud & (y == 1)).sum()),
               "bootstrap_replicas": nb, "repeticiones_cv": 1}
    (REP / "f5_resumen.json").write_text(json.dumps(resumen, indent=1), encoding="utf-8")
    pd.DataFrame({"fila_pp": np.arange(n), **{f"pcal_{k}": v for k, v in pcal.items()}}).to_parquet(RAIZ / "data/07_model_output_ep3/f5_pcal.parquet", index=False)
    cols = ["candidato", "AUC", "PR-AUC", "Captura@20", "Fraccion_80", "recall_A", "precision_A", "ECE_cal", "AUC_min_fold", "AUC_mediana_segmento", "estable"]
    print(tabla[cols].round(3).to_string(index=False))
    print(pd.DataFrame(cfilas)[["candidato", "Captura@20_C", "Fraccion_80_C", "Fraccion_80_A", "equilibrio_cajas_por_auditoria", "equilibrio_lo", "equilibrio_hi", "recall_A_proceso_C"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
