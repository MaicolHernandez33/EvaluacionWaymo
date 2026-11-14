"""F3 (IE9): optimizacion de hiperparametros con busqueda aleatoria anidada, reanudable.

Por cada (semilla de CV externa, fold externo, modelo) se hace una tarea:
  1. modelo por defecto -> predicciones del fold de validacion (OOF);
  2. busqueda interna (GroupKFold(3) por segmento, criterio PR-AUC) sobre ``--ncfg`` configuraciones;
  3. refit de la mejor configuracion -> predicciones del fold de validacion (OOF).
Cada tarea guarda un checkpoint en data/08_reporting_ep3/f3_ckpt; si se interrumpe, se reanuda
sin repetir lo hecho (tambien por configuracion dentro de la tarea). Usa un hilo por proceso.

Uso:  python scripts/ep3/f3_tuning.py --etapa principal --semillas 42 --ncfg 30 --workers 6
      python scripts/ep3/f3_tuning.py --etapa ext      (extiende una vez las grillas con optimo en el borde)
      python scripts/ep3/f3_tuning.py --etapa curvas   (curvas de validacion de un hiperparametro por modelo)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import joblib
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from sklearn.metrics import average_precision_score  # noqa: E402
from sklearn.model_selection import GroupKFold  # noqa: E402
from threadpoolctl import threadpool_limits  # noqa: E402

from waymo_evaluacion.ep3 import modelos as M  # noqa: E402
from waymo_evaluacion.ep3.plan import verificar_plan_v3  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
CKPT = REP / "f3_ckpt"
ORDEN_TAREAS = ("RF", "HGB", "XGB", "LGBM", "LR")        # lo mas pesado primero


def cargar() -> tuple[pd.DataFrame, dict[str, list[str]]]:
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = dev[dev["en_zona_principal"]].reset_index(drop=True)
    cj = json.loads((RAIZ / "data/05_model_input_ep3/conjuntos_variables.json").read_text(encoding="utf-8"))
    return pp, cj


def espacio_extendido(modelo: str, bordes: dict) -> dict:
    """Extiende una vez, hacia el lado del borde, los hiperparametros con optimo en el borde."""
    esp = dict(M.ESPACIOS[modelo])
    for hp, lado in bordes.items():
        vals = list(esp[hp])
        num = [v for v in vals if isinstance(v, (int, float)) and v is not None]
        if lado == "max":
            nuevos = [type(num[-1])(num[-1] * 2), type(num[-1])(num[-1] * 4)]
            esp[hp] = vals + nuevos
        else:
            base = num[0]
            piso = 2 if hp in ("max_leaf_nodes", "num_leaves") else 1
            if isinstance(base, int):
                nuevos = {max(base // 2, piso), max(base // 4, piso)}
            else:
                nuevos = {base / 2, base / 4}
            esp[hp] = sorted(nuevos - set(vals)) + vals
    return esp


def tarea(etapa: str, semilla: int, fold: int, modelo: str, ncfg: int, espacio_ext: dict | None) -> str:
    """Una tarea reanudable; devuelve una linea de log."""
    destino = CKPT / f"{etapa}_{modelo}_s{semilla}_f{fold}.pkl"
    if destino.exists():
        return f"[omitida] {destino.name}"
    t0 = time.time()
    with threadpool_limits(1):
        pp, cj = cargar()
        f = pp[f"fold_s{semilla}"].to_numpy()
        tr, va = np.flatnonzero(f != fold), np.flatnonzero(f == fold)
        ytr, yva = pp["sin_camara"].to_numpy()[tr], pp["sin_camara"].to_numpy()[va]
        Xtr_all, Xva_all = pp.iloc[tr], pp.iloc[va]
        cols = cj["V16"]

        # 1) por defecto
        m0 = M.construir(modelo, M.DEFECTOS[modelo], cols).fit(Xtr_all[cols], ytr)
        pred_def, tr_def = M.predecir(m0, Xva_all[cols]), M.predecir(m0, Xtr_all[cols])
        ap_def_tr = float(average_precision_score(ytr, tr_def))

        # 2) busqueda interna
        cfgs = M.configuraciones(modelo, ncfg, M.SEMILLA if etapa == "principal" else M.SEMILLA + 1, espacio_ext)
        parcial = CKPT / f"{etapa}_{modelo}_s{semilla}_f{fold}.parcial.json"
        hechos = json.loads(parcial.read_text(encoding="utf-8")) if parcial.exists() else {}
        cv = list(GroupKFold(n_splits=3).split(np.zeros(len(tr)), ytr, pp["seg"].to_numpy()[tr]))
        for i, cfg in enumerate(cfgs):
            if str(i) in hechos:
                continue
            vname, p = M.separar(cfg)
            c = cj[vname]
            oof = np.zeros(len(tr))
            for a, b in cv:
                est = M.construir(modelo, p, c).fit(Xtr_all.iloc[a][c], ytr[a])
                oof[b] = M.predecir(est, Xtr_all.iloc[b][c])
            hechos[str(i)] = float(average_precision_score(ytr, oof))
            parcial.write_text(json.dumps(hechos), encoding="utf-8")
        scores = np.array([hechos[str(i)] for i in range(len(cfgs))])
        mejor = int(np.argmax(scores))

        # 3) refit de la mejor
        vname, p = M.separar(cfgs[mejor])
        c = cj[vname]
        m1 = M.construir(modelo, p, c).fit(Xtr_all[c], ytr)
        pred_opt, tr_opt = M.predecir(m1, Xva_all[c]), M.predecir(m1, Xtr_all[c])
        res = {
            "etapa": etapa, "semilla": semilla, "fold": fold, "modelo": modelo, "idx_val": va, "pred_def": pred_def, "pred_opt": pred_opt,
            "mejor_cfg": M.a_json(cfgs[mejor]), "ap_interno_mejor": float(scores[mejor]), "ap_interno_todas": scores.tolist(),
            "cfgs": [M.a_json(x) for x in cfgs], "ap_train_def": ap_def_tr, "ap_train_opt": float(average_precision_score(ytr, tr_opt)),
            "ap_val_def": float(average_precision_score(yva, pred_def)), "ap_val_opt": float(average_precision_score(yva, pred_opt)),
            "segundos": time.time() - t0,
        }
    joblib.dump(res, destino)
    if parcial.exists():
        parcial.unlink()
    return f"[ok {time.time() - t0:6.0f}s] {destino.name}  AP val def {res['ap_val_def']:.3f} -> opt {res['ap_val_opt']:.3f}  mejor={res['mejor_cfg']}"


# ------------------------------------------------------------------------------------ curvas de validacion
CURVAS = {
    "LR": ("C", [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0]),
    "RF": ("min_samples_leaf", [20, 50, 100, 200, 400, 800, 1600]),
    "HGB": ("max_leaf_nodes", [2, 3, 4, 6, 8, 15, 31]),
    "XGB": ("max_depth", [1, 2, 3, 4, 6, 8]),
    "LGBM": ("num_leaves", [2, 3, 4, 7, 15, 31, 63]),
}


def curva(semilla: int, fold: int, modelo: str, valor) -> dict:
    destino = CKPT / f"curva_{modelo}_s{semilla}_f{fold}_{valor}.json"
    if destino.exists():
        return json.loads(destino.read_text(encoding="utf-8"))
    hp, _ = CURVAS[modelo]
    with threadpool_limits(1):
        pp, cj = cargar()
        f = pp[f"fold_s{semilla}"].to_numpy()
        tr, va = np.flatnonzero(f != fold), np.flatnonzero(f == fold)
        cols = cj["V16"]
        est = M.construir(modelo, {hp: valor}, cols).fit(pp.iloc[tr][cols], pp["sin_camara"].to_numpy()[tr])
        r = {"modelo": modelo, "hiperparametro": hp, "valor": valor, "fold": fold,
             "ap_train": float(average_precision_score(pp["sin_camara"].to_numpy()[tr], M.predecir(est, pp.iloc[tr][cols]))),
             "ap_val": float(average_precision_score(pp["sin_camara"].to_numpy()[va], M.predecir(est, pp.iloc[va][cols])))}
    destino.write_text(json.dumps(r), encoding="utf-8")
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--etapa", default="principal", choices=["principal", "ext", "curvas"])
    ap.add_argument("--semillas", default="42")
    ap.add_argument("--ncfg", type=int, default=30)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--modelos", default=",".join(M.MODELOS))
    a = ap.parse_args()
    verificar_plan_v3(RAIZ)
    CKPT.mkdir(parents=True, exist_ok=True)
    semillas = [int(s) for s in a.semillas.split(",")]
    modelos = [m for m in ORDEN_TAREAS if m in a.modelos.split(",")]
    t0 = time.time()
    if a.etapa == "curvas":
        trabajos = [(s, k, m, v) for m in modelos for v in CURVAS[m][1] for s in semillas for k in range(5)]
        res = joblib.Parallel(n_jobs=a.workers, verbose=5)(joblib.delayed(curva)(*t) for t in trabajos)
        pd.DataFrame(res).to_csv(REP / "f3_curvas_validacion.csv", index=False)
        print(f"curvas listas en {time.time() - t0:.0f} s")
        return
    ext = {}
    if a.etapa == "ext":
        ext = json.loads((REP / "f3_bordes_extension.json").read_text(encoding="utf-8"))
        modelos = [m for m in modelos if m in ext]
    trabajos = []
    for m in modelos:
        esp = espacio_extendido(m, ext[m]) if a.etapa == "ext" else None
        for s in semillas:
            for k in range(5):
                trabajos.append((a.etapa, s, k, m, a.ncfg, esp))
    print(f"{len(trabajos)} tareas, {a.workers} procesos, ncfg={a.ncfg}", flush=True)
    for linea in joblib.Parallel(n_jobs=a.workers, return_as="generator_unordered")(joblib.delayed(tarea)(*t) for t in trabajos):
        print(time.strftime("%H:%M:%S"), linea, flush=True)
    print(f"etapa {a.etapa} lista en {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
