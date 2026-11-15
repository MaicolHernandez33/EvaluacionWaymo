"""F18-A3(c) (post hoc, no pre-declarado): tasa de sin_camara por tramo de puntos del sensor superior, con todas las cajas, sin las celdas con hueco (Lista A)
y sin ellas ni la celda sin marcar de mayor tasa en el tramo > 100 (segmento 247562357599). Explica por que la tasa sube de 51 a 100 puntos a > 100 puntos.
Escribe data/08_reporting_ep3/f12_eda_puntos_top_sin_huecos.csv y f12_eda_puntos_top_resumen.json. IC por segmentos (1.000 replicas, semilla 42).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts" / "ep3"))
from f12_analisis_muestra import tasa_ic  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
SEG_EXTRA = "247562357599"  # segmento donde la celda cam5 se marca con frac = 0,35 (f12_sensibilidad_detector.csv)
TRAMOS = [-1, 5, 10, 20, 50, 100, 200, 500, np.inf]
ETIQ = ["0-5", "6-10", "11-20", "21-50", "51-100", "101-200", "201-500", ">500"]


def main() -> None:
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    h = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41_hueco.parquet").set_index("fila_id")["en_hueco"]
    pp = dev[dev["en_zona_principal"]].reset_index(drop=True)
    pp["en_hueco"] = h.loc[pp["fila_id"]].to_numpy().astype(bool)
    tr = pd.cut(pp["num_top_lidar_points"], TRAMOS, labels=ETIQ)
    variantes = {"todas las cajas": np.ones(len(pp), bool), "sin las celdas con hueco": ~pp["en_hueco"].to_numpy(),
                 f"sin las celdas con hueco ni el segmento {SEG_EXTRA}": (~pp["en_hueco"] & (pp["seg"] != SEG_EXTRA)).to_numpy()}
    tabs = []
    for nombre, m in variantes.items():
        sub = pp[m].reset_index(drop=True)
        t = tasa_ic(sub, tr[m].reset_index(drop=True), ETIQ)
        t.insert(0, "variante", nombre)
        tabs.append(t)
    out = pd.concat(tabs, ignore_index=True)
    out.to_csv(REP / "f12_eda_puntos_top_sin_huecos.csv", index=False)
    b = pp[pp["num_top_lidar_points"] > 100]
    por_seg = b.groupby("seg").agg(cajas=("sin_camara", "size"), positivos=("sin_camara", "sum")).assign(tasa=lambda d: d["positivos"] / d["cajas"]).sort_values("positivos", ascending=False)
    bs = b[~b["en_hueco"]]
    por_seg_sin = bs.groupby("seg").agg(cajas=("sin_camara", "size"), positivos=("sin_camara", "sum")).assign(tasa=lambda d: d["positivos"] / d["cajas"]).sort_values("positivos", ascending=False)
    res = {"nota": "post hoc, no pre-declarado; descriptivo", "tramo_mayor_100": {"cajas": int(len(b)), "positivos": int(b["sin_camara"].sum()), "tasa": float(b["sin_camara"].mean()),
                                                                                  "cajas_en_celdas_con_hueco": int(b["en_hueco"].sum()), "tasa_en_celdas_con_hueco": float(b.loc[b["en_hueco"], "sin_camara"].mean()),
                                                                                  "positivos_en_celdas_con_hueco": int(b.loc[b["en_hueco"], "sin_camara"].sum()),
                                                                                  "cajas_sin_hueco": int(len(bs)), "tasa_sin_hueco": float(bs["sin_camara"].mean())},
           "tramo_51_100": {"tasa": float(pp.loc[pp["num_top_lidar_points"].between(51, 100), "sin_camara"].mean()), "tasa_sin_hueco": float(pp.loc[pp["num_top_lidar_points"].between(51, 100) & ~pp["en_hueco"], "sin_camara"].mean())},
           "top3_segmentos_positivos_mayor_100": [{"seg": s, "cajas": int(r.cajas), "positivos": int(r.positivos), "tasa": float(r.tasa)} for s, r in por_seg.head(3).iterrows()],
           "top3_segmentos_positivos_mayor_100_sin_hueco": [{"seg": s, "cajas": int(r.cajas), "positivos": int(r.positivos), "tasa": float(r.tasa)} for s, r in por_seg_sin.head(3).iterrows()],
           "pct_positivos_mayor_100_en_celdas_con_hueco": float(b.loc[b["en_hueco"], "sin_camara"].sum() / b["sin_camara"].sum())}
    (REP / "f12_eda_puntos_top_resumen.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    pd.set_option("display.width", 220)
    print(out.round(3).to_string(index=False)); print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
