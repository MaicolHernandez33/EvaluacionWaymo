"""F1: datos de desarrollo de EP3 (41 segmentos), pares por cámara, conjuntos de variables y folds.

Lee EP2 en solo lectura. Escribe en data/05_model_input_ep3 y data/08_reporting_ep3.
Verifica además que los modelos congelados de EP2 reproducen pred_test_B.parquet (tol. 1e-9).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.datos import (  # noqa: E402
    COLS_ID, V_MIN3, conjuntos_variables, construir_dev41, crear_folds, variables_v16,
)
from waymo_evaluacion.ep3.plan import verificar_plan_v3  # noqa: E402

OUT_IN = RAIZ / "data/05_model_input_ep3"
OUT_REP = RAIZ / "data/08_reporting_ep3"
NOMBRES = {
    "lr_B": "Regresion logistica", "hgb_B": "HGB", "rf_B": "Random Forest", "lr_minimo_B": "Modelo minimo (LR 3 variables)",
}


def main() -> None:
    verificar_plan_v3(RAIZ)
    OUT_IN.mkdir(parents=True, exist_ok=True)
    OUT_REP.mkdir(parents=True, exist_ok=True)
    dev = construir_dev41(RAIZ)
    folds = crear_folds(dev)
    dev = pd.concat([dev, folds], axis=1)
    dev.insert(0, "fila_id", np.arange(len(dev)))
    dev.to_parquet(OUT_IN / "dev_41.parquet", index=False)
    (OUT_IN / "conjuntos_variables.json").write_text(json.dumps(conjuntos_variables(RAIZ), ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- conteos
    pp = dev[dev["en_zona_principal"]]
    resumen = {
        "filas_total_120": int(len(dev)), "filas_principal": int(len(pp)), "positivos_principal": int(pp["sin_camara"].sum()),
        "prevalencia_principal": float(pp["sin_camara"].mean()), "segmentos": int(dev["seg"].nunique()),
        "segmentos_train": int(dev.loc[dev["grupo"] == "train", "seg"].nunique()), "segmentos_test": int(dev.loc[dev["grupo"] == "test", "seg"].nunique()),
        "test_principal": [int(((dev["grupo"] == "test") & dev["en_zona_principal"]).sum()), int(dev.loc[(dev["grupo"] == "test") & dev["en_zona_principal"], "sin_camara"].sum())],
        "test_120": [int((dev["grupo"] == "test").sum()), int(dev.loc[dev["grupo"] == "test", "sin_camara"].sum())],
        "pares_consistentes_con_sin_camara": True,
    }
    por_fold = {}
    for c in folds.columns:
        f = dev.loc[dev["en_zona_principal"], [c, "seg", "sin_camara"]]
        por_fold[c] = {"filas": f.groupby(c).size().to_dict(), "segmentos": f.groupby(c)["seg"].nunique().to_dict(),
                       "prevalencia": f.groupby(c)["sin_camara"].mean().round(4).to_dict()}
        grupos_en_varios = int((f.groupby("seg")[c].nunique() > 1).sum())
        por_fold[c]["segmentos_en_mas_de_un_fold"] = grupos_en_varios
    resumen["folds"] = {k: {kk: {str(a): b for a, b in vv.items()} if isinstance(vv, dict) else vv for kk, vv in v.items()} for k, v in por_fold.items()}

    # ---- reproduccion de pred_test_B con los modelos congelados
    pred = pd.read_parquet(RAIZ / "data/07_model_output/pred_test_B.parquet")
    te = dev[dev["grupo"] == "test"].merge(pred, on=COLS_ID, how="inner", suffixes=("", "_p"))
    assert len(te) == len(pred) == int((dev["grupo"] == "test").sum()), "las claves del test no coinciden con pred_test_B"
    filas = []
    v16 = variables_v16(RAIZ)
    for archivo, nombre in NOMBRES.items():
        m = joblib.load(RAIZ / f"data/06_models/{archivo}.joblib")
        cols = V_MIN3 if archivo == "lr_minimo_B" else v16
        p = m.predict_proba(te[cols])[:, 1]
        d = float(np.abs(p - te[f"score_{nombre}"].to_numpy()).max())
        filas.append({"modelo": nombre, "dif_max_abs": d, "ok_1e-9": d <= 1e-9})
    for nombre, col in (("Regla: menos puntos LiDAR", "num_lidar_points"), ("Regla: menos puntos top", "num_top_lidar_points")):
        d = float(np.abs(-te[col].to_numpy(dtype=float) - te[f"score_{nombre}"].to_numpy()).max())
        filas.append({"modelo": nombre, "dif_max_abs": d, "ok_1e-9": d <= 1e-9})
    rep = pd.DataFrame(filas)
    rep.to_csv(OUT_REP / "f1_reproduccion_pred_test.csv", index=False)
    resumen["reproduccion_pred_test_B"] = {"filas_comparadas": int(len(te)), "dif_max_abs": float(rep["dif_max_abs"].max()), "todos_ok": bool(rep["ok_1e-9"].all())}
    (OUT_REP / "f1_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in resumen.items() if k != "folds"}, ensure_ascii=False, indent=1))
    print(rep.to_string(index=False))


if __name__ == "__main__":
    main()
