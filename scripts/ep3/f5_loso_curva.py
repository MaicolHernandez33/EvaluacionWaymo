"""F5 (IE11, parte 2): leave-one-segment-out, curva de aprendizaje por numero de segmentos y brecha ajuste-validacion
del candidato ELEGIDO en F6 (f6_seleccion.json).

Salidas en data/08_reporting_ep3: f5_loso_segmentos.csv, f5_loso_resumen.json, f5_curva_aprendizaje.csv, f5_brecha.csv.
Un hilo por proceso, 6 procesos. Reanudable por tarea (checkpoints en f5_ckpt).
"""
from __future__ import annotations

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

from sklearn.metrics import average_precision_score, roc_auc_score  # noqa: E402
from threadpoolctl import threadpool_limits  # noqa: E402

from waymo_evaluacion.ep3.candidatos import BASE, ajustar  # noqa: E402
from waymo_evaluacion.ep3.metricas import METRICAS, ConjuntoOOF, ic95  # noqa: E402
from waymo_evaluacion.ep3.plan import verificar_plan_v3  # noqa: E402
from waymo_evaluacion.ep3.seleccion import config_final, veredictos  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
CK = REP / "f5_ckpt"
SEM = 42
TAMANOS = [5, 10, 15, 20, 25, 30]


def _datos():
    pp = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = pp[pp["en_zona_principal"]].reset_index(drop=True)
    cj = json.loads((RAIZ / "data/05_model_input_ep3/conjuntos_variables.json").read_text(encoding="utf-8"))
    return pp, cj


def _cfgs():
    ver = veredictos(REP)
    return {m: config_final(REP, m, ver) for m in BASE}


def loso(elegido: str, seg: str) -> dict:
    destino = CK / f"loso_{elegido}_{seg}.pkl"
    if destino.exists():
        return joblib.load(destino)
    with threadpool_limits(1):
        pp, cj = _datos()
        tr, va = np.flatnonzero(pp["seg"] != seg), np.flatnonzero(pp["seg"] == seg)
        m = ajustar(elegido, pp.iloc[tr], pp["sin_camara"].to_numpy()[tr], pp["seg"].to_numpy()[tr], cj, _cfgs())
        s = m.puntuar(pp.iloc[va])
        y = pp["sin_camara"].to_numpy()[va]
        r = {"seg": seg, "idx": va, "score": s, "positivos": int(y.sum()), "filas": int(len(y)),
             "AUC": float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else np.nan, "PR-AUC": float(average_precision_score(y, s)) if y.sum() > 0 else np.nan}
    joblib.dump(r, destino)
    return r


def curva(elegido: str, fold: int, n_seg: int, rep: int) -> dict:
    destino = CK / f"curva_{elegido}_f{fold}_n{n_seg}_r{rep}.pkl"
    if destino.exists():
        return joblib.load(destino)
    with threadpool_limits(1):
        pp, cj = _datos()
        f = pp[f"fold_s{SEM}"].to_numpy()
        segs_tr = np.array(sorted(pp.loc[f != fold, "seg"].unique()))
        rng = np.random.default_rng(1000 * fold + 10 * n_seg + rep)
        sub = segs_tr if n_seg >= len(segs_tr) else rng.choice(segs_tr, n_seg, replace=False)
        tr, va = np.flatnonzero(pp["seg"].isin(sub) & (f != fold)), np.flatnonzero(f == fold)
        ytr, yva = pp["sin_camara"].to_numpy()[tr], pp["sin_camara"].to_numpy()[va]
        m = ajustar(elegido, pp.iloc[tr], ytr, pp["seg"].to_numpy()[tr], cj, _cfgs())
        s_tr, s_va = m.puntuar(pp.iloc[tr]), m.puntuar(pp.iloc[va])
        r = {"fold": fold, "n_segmentos": int(len(sub)), "rep": rep, "AUC_ajuste": float(roc_auc_score(ytr, s_tr)), "AUC_validacion": float(roc_auc_score(yva, s_va)),
             "PR-AUC_ajuste": float(average_precision_score(ytr, s_tr)), "PR-AUC_validacion": float(average_precision_score(yva, s_va))}
    joblib.dump(r, destino)
    return r


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--candidato", default=None, help="por defecto, el elegido en F6")
    a = ap.parse_args()
    verificar_plan_v3(RAIZ)
    elegido = a.candidato or json.loads((REP / "f6_seleccion.json").read_text(encoding="utf-8"))["elegido"]
    if not elegido:
        sys.exit("DETENIDO: F6 no declaro un elegido.")
    suf = "_" + elegido.replace(" ", "_")
    CK.mkdir(parents=True, exist_ok=True)
    pp, _ = _datos()
    segs = sorted(pp["seg"].unique())
    t0 = time.time()
    print(f"candidato elegido: {elegido} | LOSO en {len(segs)} segmentos", flush=True)
    res = joblib.Parallel(n_jobs=6, verbose=3)(joblib.delayed(loso)(elegido, s) for s in segs)
    tabla = pd.DataFrame([{k: v for k, v in r.items() if k not in ("idx", "score")} for r in res])
    tabla.to_csv(REP / f"f5_loso_segmentos{suf}.csv", index=False)
    score = np.zeros(len(pp))
    for r in res:
        score[r["idx"]] = r["score"]
    y = pp["sin_camara"].to_numpy()
    conj = ConjuntoOOF(y, pp["seg"].to_numpy(), {elegido: [score]})
    boot = conj.bootstrap([elegido], 1000, 42)[elegido]
    m = conj.metricas(elegido)
    validos = tabla[(tabla["positivos"] >= 100) & ((tabla["filas"] - tabla["positivos"]) >= 100)]
    resumen = {"candidato": elegido, **{k: float(m[i]) for i, k in enumerate(METRICAS)}, **{f"{k}_ic": list(ic95(boot[:, i])) for i, k in enumerate(METRICAS)},
               "AUC_min_segmento": float(validos["AUC"].min()), "AUC_mediana_segmento": float(validos["AUC"].median()), "segmentos_evaluables": int(len(validos)),
               "segmentos_con_AUC_menor_a_0_55": int((validos["AUC"] < 0.55).sum()), "segundos": time.time() - t0}
    (REP / f"f5_loso_resumen{suf}.json").write_text(json.dumps(resumen, indent=1), encoding="utf-8")
    print(json.dumps(resumen, indent=1))

    trabajos = [(elegido, k, n, r) for k in range(5) for n in TAMANOS + [99] for r in range(3 if n != 99 else 1)]
    res_c = joblib.Parallel(n_jobs=6, verbose=3)(joblib.delayed(curva)(*t) for t in trabajos)
    c = pd.DataFrame(res_c)
    c.to_csv(REP / f"f5_curva_aprendizaje{suf}.csv", index=False)
    g = c.groupby("n_segmentos")[["AUC_ajuste", "AUC_validacion", "PR-AUC_ajuste", "PR-AUC_validacion"]].mean()
    g["brecha_AUC"] = g["AUC_ajuste"] - g["AUC_validacion"]
    g["brecha_PR-AUC"] = g["PR-AUC_ajuste"] - g["PR-AUC_validacion"]
    g.reset_index().to_csv(REP / f"f5_brecha{suf}.csv", index=False)
    print(g.round(3).to_string())


if __name__ == "__main__":
    main()
