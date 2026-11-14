"""F3: analisis de la busqueda anidada: defecto vs optimizado, veredicto P5 y revision de bordes de grilla.

Lee los checkpoints de data/08_reporting_ep3/f3_ckpt. Escribe tablas y JSON en data/08_reporting_ep3
y las predicciones fuera de fold (defecto y optimizado) en data/07_model_output_ep3/f3_oof.parquet.
Si existen checkpoints de la etapa ``ext`` para un modelo, esa etapa reemplaza a la principal.
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

from waymo_evaluacion.ep3 import modelos as M  # noqa: E402
from waymo_evaluacion.ep3.metricas import METRICAS, ConjuntoOOF, ic95  # noqa: E402
from waymo_evaluacion.ep3.plan import cargar_plan_v3  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
SEMILLA_CV = 42


def leer(etapa: str, modelo: str) -> list[dict]:
    return [joblib.load(p) for p in sorted(glob.glob(str(REP / "f3_ckpt" / f"{etapa}_{modelo}_s{SEMILLA_CV}_f*.pkl")))]


def main() -> None:
    plan = cargar_plan_v3(RAIZ)
    p5 = plan["P5"]["mejora"]
    pp = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = pp[pp["en_zona_principal"]].reset_index(drop=True)
    y, seg = pp["sin_camara"].to_numpy(), pp["seg"].to_numpy()
    punt: dict[str, list[np.ndarray]] = {}
    por_fold, bordes_tab, cfg_tab, usadas = [], [], [], {}
    for m in M.MODELOS:
        etapa = "ext" if leer("ext", m) else "principal"
        res = leer(etapa, m)
        if len(res) != 5:
            print(f"{m}: faltan tareas ({len(res)} de 5), se omite")
            continue
        usadas[m] = etapa
        for variante in ("def", "opt"):
            v = np.zeros(len(pp))
            for r in res:
                v[r["idx_val"]] = r[f"pred_{variante}"]
            punt[f"{m}_{variante}"] = [v]
        esp = M.ESPACIOS[m] if etapa == "principal" else None
        for r in res:
            por_fold.append({"modelo": m, "etapa": etapa, "fold": r["fold"], "ap_val_def": r["ap_val_def"], "ap_val_opt": r["ap_val_opt"], "ap_train_def": r["ap_train_def"],
                             "ap_train_opt": r["ap_train_opt"], "ap_interno_mejor": r["ap_interno_mejor"], "segundos": r["segundos"]})
            cfg_tab.append({"modelo": m, "etapa": etapa, "fold": r["fold"], **r["mejor_cfg"]})
        # bordes: valores de la grilla efectivamente usada (union de configuraciones muestreadas)
        todas = pd.DataFrame([c for r in res[:1] for c in r["cfgs"]])
        for hp in M.ORDENADOS[m]:
            vals = pd.to_numeric(todas[hp], errors="coerce").dropna()
            if vals.empty:
                continue
            lo, hi = float(vals.min()), float(vals.max())
            elegidos = pd.to_numeric(pd.DataFrame([r["mejor_cfg"] for r in res])[hp], errors="coerce")
            n_lo, n_hi = int((elegidos == lo).sum()), int((elegidos == hi).sum())
            bordes_tab.append({"modelo": m, "etapa": etapa, "hiperparametro": hp, "min_grilla": lo, "max_grilla": hi, "folds_en_min": n_lo, "folds_en_max": n_hi,
                               "borde": "max" if n_hi >= 3 else ("min" if n_lo >= 3 else "no")})
    ConjuntoOOF_ = ConjuntoOOF(y, seg, punt)
    boot = ConjuntoOOF_.bootstrap(list(punt), 1000, 42)
    filas = []
    for m in usadas:
        d, o = f"{m}_def", f"{m}_opt"
        md, mo = ConjuntoOOF_.metricas(d), ConjuntoOOF_.metricas(o)
        fila = {"modelo": m, "etapa": usadas[m]}
        for i, k in enumerate(METRICAS):
            lo, hi = ic95(boot[d][:, i])
            fila[f"{k}_def"], fila[f"{k}_def_lo"], fila[f"{k}_def_hi"] = md[i], lo, hi
            lo, hi = ic95(boot[o][:, i])
            fila[f"{k}_opt"], fila[f"{k}_opt_lo"], fila[f"{k}_opt_hi"] = mo[i], lo, hi
        for i, k in enumerate(("AUC", "PR-AUC")):
            lo, hi = ic95(boot[o][:, i] - boot[d][:, i])
            fila[f"dif_{k}"], fila[f"dif_{k}_lo"], fila[f"dif_{k}_hi"] = mo[i] - md[i], lo, hi
        dif, lo = fila["dif_PR-AUC"], fila["dif_PR-AUC_lo"]
        fila["veredicto"] = "mejora" if (dif >= p5["diferencia_min"] and lo > 0) else "no mejora"
        fila["folds_opt_gana_ap"] = int(sum(1 for r in por_fold if r["modelo"] == m and r["ap_val_opt"] > r["ap_val_def"]))
        filas.append(fila)
    tab = pd.DataFrame(filas)
    tab.to_csv(REP / "f3_defecto_vs_optimizado.csv", index=False)
    pd.DataFrame(por_fold).to_csv(REP / "f3_por_fold.csv", index=False)
    pd.DataFrame(cfg_tab).to_csv(REP / "f3_config_por_fold.csv", index=False)
    bt = pd.DataFrame(bordes_tab)
    bt.to_csv(REP / "f3_bordes.csv", index=False)
    ext = {}
    for r in bt[bt["borde"] != "no"].itertuples():
        if r.etapa == "principal":                      # una sola extension por modelo
            ext.setdefault(r.modelo, {})[r.hiperparametro] = r.borde
    (REP / "f3_bordes_extension.json").write_text(json.dumps(ext, indent=1), encoding="utf-8")
    out = RAIZ / "data/07_model_output_ep3"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"fila_pp": np.arange(len(pp)), **{k: v[0] for k, v in punt.items()}}).to_parquet(out / "f3_oof.parquet", index=False)
    print(tab[["modelo", "etapa", "PR-AUC_def", "PR-AUC_opt", "dif_PR-AUC", "dif_PR-AUC_lo", "dif_PR-AUC_hi", "AUC_def", "AUC_opt", "veredicto"]].round(4).to_string(index=False))
    print(bt[bt["borde"] != "no"].to_string(index=False))
    print("bordes a extender:", ext)


if __name__ == "__main__":
    main()
