"""F4 (IE10): ensambles E1 a E4 con CV externa por segmento y OOF interno por segmento (sin fuga).

E1 voting soft LR+RF+HGB (promedio de probabilidades); E2 promedio de rangos de E1 y la regla
"menos puntos top"; E3 stacking (meta-LR) sobre OOF interno GroupKFold(3) de LR, RF, HGB, XGB, LGBM;
E4 stacking por vistas (observacion, tamano, posicion) con meta-LR. Los modelos base usan la
configuracion optimizada de F3 solo si F3 dio veredicto "mejora" para ese modelo; si no, el defecto.
Reutiliza las predicciones de validacion de F3 para los modelos base (deterministas: semilla 42, un hilo).

Uso: python scripts/ep3/f4_ensambles.py [--workers 5] [--prueba] [--solo-analisis]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import joblib
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from scipy.stats import rankdata  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import GroupKFold  # noqa: E402
from threadpoolctl import threadpool_limits  # noqa: E402

from waymo_evaluacion.ep3 import modelos as M  # noqa: E402
from waymo_evaluacion.ep3.metricas import METRICAS, ConjuntoOOF, ic95  # noqa: E402
from waymo_evaluacion.ep3.plan import cargar_plan_v3  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
CK4 = REP / "f4_ckpt"
SEMILLA_CV = 42
BASE = ("LR", "RF", "HGB", "XGB", "LGBM")
# modelo de las vistas de E4: HGB con la regularizacion fuerte que dejo EP2 (hiperparametros_B.json, final.HGB)
CFG_VISTA = {"max_iter": 90, "max_leaf_nodes": 4, "min_samples_leaf": 100, "learning_rate": 0.0305, "l2_regularization": 9.6098}


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p)).reshape(-1, 1)


def veredictos() -> dict[str, str]:
    f = REP / "f3_defecto_vs_optimizado.csv"
    if not f.exists():
        return {}
    return dict(pd.read_csv(f)[["modelo", "veredicto"]].itertuples(index=False, name=None))


def config_fold(modelo: str, fold: int, ver: dict[str, str]) -> tuple[str, dict]:
    """(conjunto de variables, hiperparametros) del modelo base en el fold externo."""
    if ver.get(modelo) == "mejora":
        for etapa in ("ext", "principal"):
            ruta = REP / "f3_ckpt" / f"{etapa}_{modelo}_s{SEMILLA_CV}_f{fold}.pkl"
            if ruta.exists():
                return M.separar(joblib.load(ruta)["mejor_cfg"])
    return "V16", dict(M.DEFECTOS[modelo])


def pred_base_f3(modelo: str, fold: int, ver: dict[str, str]) -> tuple[np.ndarray, np.ndarray] | None:
    """(idx_val, prediccion) del modelo base en el fold, tomadas de F3 (variante segun el veredicto)."""
    var = "opt" if ver.get(modelo) == "mejora" else "def"
    for etapa in ("ext", "principal"):
        ruta = REP / "f3_ckpt" / f"{etapa}_{modelo}_s{SEMILLA_CV}_f{fold}.pkl"
        if ruta.exists():
            r = joblib.load(ruta)
            return r["idx_val"], r[f"pred_{var}"]
    return None


def oof_interno(pp: pd.DataFrame, tr: np.ndarray, modelo: str, vname: str, params: dict, cj: dict) -> np.ndarray:
    cols = cj[vname]
    ytr = pp["sin_camara"].to_numpy()[tr]
    cv = GroupKFold(n_splits=3).split(np.zeros(len(tr)), ytr, pp["seg"].to_numpy()[tr])
    oof = np.zeros(len(tr))
    X = pp.iloc[tr]
    for a, b in cv:
        est = M.construir(modelo, params, cols).fit(X.iloc[a][cols], ytr[a])
        oof[b] = M.predecir(est, X.iloc[b][cols])
    return oof


def tarea(fold: int, prueba: bool) -> str:
    destino = CK4 / f"f4_f{fold}{'_prueba' if prueba else ''}.pkl"
    if destino.exists():
        return f"[omitida] {destino.name}"
    t0 = time.time()
    with threadpool_limits(1):
        pp = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
        pp = pp[pp["en_zona_principal"]].reset_index(drop=True)
        cj = json.loads((RAIZ / "data/05_model_input_ep3/conjuntos_variables.json").read_text(encoding="utf-8"))
        ver = veredictos()
        f = pp[f"fold_s{SEMILLA_CV}"].to_numpy()
        tr, va = np.flatnonzero(f != fold), np.flatnonzero(f == fold)
        ytr = pp["sin_camara"].to_numpy()[tr]
        if prueba:                                     # modo prueba: submuestra de segmentos, solo para verificar el codigo
            segs = np.array(sorted(pp["seg"].unique()))[:10]
            tr = tr[np.isin(pp["seg"].to_numpy()[tr], segs)]
            va = va[np.isin(pp["seg"].to_numpy()[va], np.array(sorted(pp["seg"].unique()))[10:20])]
            ytr = pp["sin_camara"].to_numpy()[tr]
        out: dict[str, np.ndarray] = {}
        # --- base: val de F3 (o ajuste directo en modo prueba)
        base_va, base_oof = {}, {}
        for m in BASE:
            vname, params = config_fold(m, fold, ver)
            if prueba:
                est = M.construir(m, params, cj[vname]).fit(pp.iloc[tr][cj[vname]], ytr)
                base_va[m] = M.predecir(est, pp.iloc[va][cj[vname]])
            else:
                idx, pr = pred_base_f3(m, fold, ver)
                assert np.array_equal(idx, va), "las filas de validacion no coinciden con las de F3"
                base_va[m] = pr
            base_oof[m] = oof_interno(pp, tr, m, vname, params, cj)
        # --- E1 y E2
        e1 = np.mean([base_va[m] for m in ("LR", "RF", "HGB")], axis=0)
        e2 = (rankdata(e1) + rankdata(-pp["num_top_lidar_points"].to_numpy(float)[va])) / (2 * len(va))
        # --- E3: stacking con las 5 bases
        meta3 = LogisticRegression(C=1.0, max_iter=1000).fit(np.hstack([_logit(base_oof[m]) for m in BASE]), ytr)
        e3 = meta3.predict_proba(np.hstack([_logit(base_va[m]) for m in BASE]))[:, 1]
        # --- E4: vistas
        vistas = {"obs": "VISTA_OBS", "tam": "VISTA_TAMANO", "pos": "VISTA_POSICION"}
        v_oof, v_va = {}, {}
        for k, vn in vistas.items():
            cols = cj[vn]
            v_oof[k] = oof_interno(pp, tr, "HGB", vn, CFG_VISTA, cj)
            est = M.construir("HGB", CFG_VISTA, cols).fit(pp.iloc[tr][cols], ytr)
            v_va[k] = M.predecir(est, pp.iloc[va][cols])
        meta4 = LogisticRegression(C=1.0, max_iter=1000).fit(np.hstack([_logit(v_oof[k]) for k in vistas]), ytr)
        e4 = meta4.predict_proba(np.hstack([_logit(v_va[k]) for k in vistas]))[:, 1]
        # --- LR3 (modelo minimo) y regla top como candidatos
        c3 = cj["V_MIN3"]
        lr3 = M.predecir(M.construir("LR", {}, c3).fit(pp.iloc[tr][c3], ytr), pp.iloc[va][c3])
        out = {**{f"base_{m}": base_va[m] for m in BASE}, "E1": e1, "E2": e2, "E3": e3, "E4": e4, "LR3": lr3,
               **{f"vista_{k}": v_va[k] for k in vistas}, "regla_top": -pp["num_top_lidar_points"].to_numpy(float)[va],
               "meta3_coef": meta3.coef_.ravel(), "meta4_coef": meta4.coef_.ravel()}
        # --- scores internos (OOF interno por segmento) de las filas de entrenamiento, para fijar umbrales y calibrar sin tocar el fold externo
        e1_in = np.mean([base_oof[m] for m in ("LR", "RF", "HGB")], axis=0)
        top_tr = -pp["num_top_lidar_points"].to_numpy(float)[tr]
        inner = {**{f"base_{m}": base_oof[m] for m in BASE}, "E1": e1_in, "E2": (rankdata(e1_in) + rankdata(top_tr)) / (2 * len(tr)),
                 "E3": meta3.predict_proba(np.hstack([_logit(base_oof[m]) for m in BASE]))[:, 1],
                 "E4": meta4.predict_proba(np.hstack([_logit(v_oof[k]) for k in vistas]))[:, 1],
                 "LR3": oof_interno(pp, tr, "LR", "V_MIN3", {}, cj), "regla_top": top_tr, **{f"vista_{k}": v_oof[k] for k in vistas}}
    joblib.dump({"fold": fold, "idx_val": va, "idx_tr": tr, "pred": out, "inner": inner, "segundos": time.time() - t0}, destino)
    return f"[ok {time.time() - t0:5.0f}s] {destino.name}"


def seg_auc(y, s, seg, minimo=20):
    d = pd.DataFrame({"y": y, "s": s, "g": seg})
    r = {}
    for g, x in d.groupby("g"):
        if x["y"].sum() >= minimo and (1 - x["y"]).sum() >= minimo:
            r[g] = roc_auc_score(x["y"], x["s"])
    return pd.Series(r)


def analisis(ver: dict[str, str]) -> None:
    plan = cargar_plan_v3(RAIZ)
    p6 = plan["P6"]["aporta"]
    pp = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = pp[pp["en_zona_principal"]].reset_index(drop=True)
    y, seg, fold = pp["sin_camara"].to_numpy(), pp["seg"].to_numpy(), pp[f"fold_s{SEMILLA_CV}"].to_numpy()
    res = [joblib.load(p) for p in sorted(glob.glob(str(CK4 / "f4_f?.pkl")))]
    assert len(res) == 5, "faltan folds de F4"
    nombres = [k for k in res[0]["pred"] if not k.endswith("_coef")]
    punt = {}
    for k in nombres:
        v = np.zeros(len(pp))
        for r in res:
            v[r["idx_val"]] = r["pred"][k]
        punt["Regla top" if k == "regla_top" else k.replace("base_", "")] = [v]
    conj = ConjuntoOOF(y, seg, punt)
    boot = conj.bootstrap(list(punt), 1000, 42)
    comp = {"E1": ["LR", "RF", "HGB"], "E2": ["E1", "Regla top"], "E3": list(BASE), "E4": ["vista_obs", "vista_tam", "vista_pos"]}
    auc = {k: conj.metricas(k)[0] for k in punt}
    filas = []
    for e, cs in comp.items():
        mejor = max(cs, key=lambda c: auc[c])
        i = 0
        dif = auc[e] - auc[mejor]
        lo, hi = ic95(boot[e][:, i] - boot[mejor][:, i])
        veredicto = "no aporta"
        if dif >= p6["diferencia_min"]:
            veredicto = "aporta" if lo > 0 else "indicio no concluyente"
        folds_g = sum(roc_auc_score(y[fold == k], punt[e][0][fold == k]) > roc_auc_score(y[fold == k], punt[mejor][0][fold == k]) for k in range(5))
        sa_e, sa_m = seg_auc(y, punt[e][0], seg), seg_auc(y, punt[mejor][0], seg)
        comunes = sa_e.index.intersection(sa_m.index)
        filas.append({"ensamble": e, "mejor_componente": mejor, "AUC_ensamble": auc[e], "AUC_mejor_componente": auc[mejor], "dif_AUC": dif, "dif_lo": lo, "dif_hi": hi,
                      "veredicto": veredicto, "folds_ganados_de_5": int(folds_g), "segmentos_ganados": int((sa_e[comunes] > sa_m[comunes]).sum()), "segmentos_comparados": int(len(comunes))})
    tab = pd.DataFrame(filas)
    tab.to_csv(REP / "f4_ensambles_aporta.csv", index=False)
    todas = []
    for k in punt:
        m = conj.metricas(k)
        fila = {"candidato": k}
        for j, nom in enumerate(METRICAS):
            lo, hi = ic95(boot[k][:, j])
            fila.update({nom: m[j], f"{nom}_lo": lo, f"{nom}_hi": hi})
        todas.append(fila)
    pd.DataFrame(todas).to_csv(REP / "f4_candidatos_metricas.csv", index=False)
    principal = "E1" if auc["E1"] >= auc["E4"] else "E4"
    pd.DataFrame({"fila_pp": np.arange(len(pp)), **{k: v[0] for k, v in punt.items()}}).to_parquet(RAIZ / "data/07_model_output_ep3/f4_oof.parquet", index=False)
    coef = {f"fold{r['fold']}": {"meta3": r["pred"]["meta3_coef"].tolist(), "meta4": r["pred"]["meta4_coef"].tolist()} for r in res}
    (REP / "f4_resumen.json").write_text(json.dumps({"ensamble_principal_declarado": principal, "AUC_E1": auc["E1"], "AUC_E4": auc["E4"], "veredictos_f3": ver,
                                                     "orden_base_stacking": list(BASE), "coef_meta": coef}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(tab.round(4).to_string(index=False))
    print("ensamble principal declarado:", principal)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--prueba", action="store_true")
    ap.add_argument("--solo-analisis", action="store_true")
    a = ap.parse_args()
    cargar_plan_v3(RAIZ)
    CK4.mkdir(parents=True, exist_ok=True)
    (RAIZ / "data/07_model_output_ep3").mkdir(parents=True, exist_ok=True)
    if not a.solo_analisis:
        t0 = time.time()
        for linea in joblib.Parallel(n_jobs=a.workers, return_as="generator_unordered")(joblib.delayed(tarea)(k, a.prueba) for k in range(5)):
            print(time.strftime("%H:%M:%S"), linea, flush=True)
        print(f"F4 listo en {(time.time() - t0) / 60:.1f} min", flush=True)
    if not a.prueba:
        analisis(veredictos())


if __name__ == "__main__":
    main()
