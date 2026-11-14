"""Hechos del brazo C (post hoc, no pre-declarado; en muestra). Escribe data/08_reporting_ep3/f12b_hechos_brazoC.json.

Por que el IC de C menos A tiene limite superior 0: en las replicas del bootstrap por segmentos que no contienen ninguno de los 2 segmentos con hueco,
la Lista A queda vacia y C es igual a A. Se calcula (a) la proporcion observada en las mismas 1.000 replicas de f12_analisis_muestra.py
(mismos pesos: pesos_bootstrap(codigos, 1000, 42)) y (b) la probabilidad exacta del diseno: se muestrean N segmentos con reemplazo entre N,
asi que P(ninguno de los 2) = ((N-2)/N)^N.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.metricas import pesos_bootstrap  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
NB = 1000


def main() -> None:
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = dev[dev["en_zona_principal"]].reset_index(drop=True)
    cod, segs = pd.factorize(pp["seg"])
    N = len(segs)
    lista = pd.read_csv(REP / "lista_A_huecos.csv", dtype={"segmento": str})
    huecos = sorted(set(lista["segmento"]))
    ids = [int(np.flatnonzero(segs == s)[0]) for s in huecos]
    w = pesos_bootstrap(cod, NB, 42)
    ninguno = (w[:, ids].sum(axis=1) == 0)
    uno = ((w[:, ids] > 0).sum(axis=1) == 1)
    ambos = ((w[:, ids] > 0).sum(axis=1) == 2)
    dif = pd.read_csv(REP / "f12_diferencia_C_menos_A.csv")
    g = dif[(dif["candidato"] == "Regla top") & dif["variante"].str.startswith("global")].iloc[0]
    k = len(huecos)
    exacta = ((N - k) / N) ** N
    ep = float(np.sqrt(exacta * (1 - exacta) / NB))
    res = {"segmentos_con_hueco": huecos, "segmentos_total": int(N), "replicas": NB, "diseno": f"{N} segmentos muestreados con reemplazo entre {N} (conteos multinomiales)",
           "prob_exacta_ninguno_de_los_2": exacta, "formula": f"(({N}-{k})/{N})^{N}", "error_estandar_con_1000_replicas": ep,
           "proporcion_observada_ninguno_de_los_2": float(ninguno.mean()), "proporcion_observada_solo_uno": float(uno.mean()), "proporcion_observada_ambos": float(ambos.mean()),
           "proporcion_replicas_donde_C_no_es_mejor_que_A": float(1 - g["prop_replicas_C_mejor"]),
           "z_observado_menos_exacto": float((ninguno.mean() - exacta) / ep),
           "lectura": "La proporcion observada es compatible con la probabilidad exacta del diseno (dentro de ~1 error estandar). En esas replicas C es igual a A, por eso el limite superior del IC es 0.",
           "nota": "post hoc, no pre-declarado; en muestra"}
    (REP / "f12b_hechos_brazoC.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
