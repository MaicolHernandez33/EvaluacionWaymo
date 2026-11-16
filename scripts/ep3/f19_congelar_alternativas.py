r"""F19-A4b (DEV-4, post hoc respecto del plan v3): entrena y CONGELA LR3 y XGBoost con los 41 segmentos, ANTES de abrir segmentos nuevos.

Configuracion de XGBoost: la mas repetida entre los 5 folds externos de f3_config_por_fold.csv (etapa principal; empate: fold de menor indice). LR3 no tiene
hiperparametros que elegir (LR sin ajuste sobre V_MIN3). Escribe data/06_models_ep3/alternativas_v3.joblib y manifest_alternativas.json (archivos NUEVOS; se niega a
sobrescribir) y data/08_reporting_ep3/f19_alternativas_congeladas.json. NO toca manifest_v3.json ni la solucion elegida.
Uso: .venv\Scripts\python scripts/ep3/f19_congelar_alternativas.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.alternativas import cargar_alternativas, config_mas_frecuente, guardar_alternativas, verificar_alternativas  # noqa: E402
from waymo_evaluacion.ep3.candidatos import ajustar  # noqa: E402
from waymo_evaluacion.ep3.plan import verificar_plan_v3  # noqa: E402
from waymo_evaluacion.ep3.sellado import verificar_manifest  # noqa: E402

MOD, REP = RAIZ / "data/06_models_ep3", RAIZ / "data/08_reporting_ep3"


def main() -> None:
    verificar_plan_v3(RAIZ)
    assert not verificar_manifest(MOD), "manifest_v3.json no coincide: no se congelan alternativas"
    cfg = pd.read_csv(REP / "f3_config_por_fold.csv")
    variables, params, n_folds, total, regla = config_mas_frecuente(cfg, "XGB")
    pp = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = pp[pp["en_zona_principal"]].reset_index(drop=True)
    cj = json.loads((RAIZ / "data/05_model_input_ep3/conjuntos_variables.json").read_text(encoding="utf-8"))
    y, seg = pp["sin_camara"].to_numpy(), pp["seg"].to_numpy()
    alt = {"LR3": ajustar("LR3", pp, y, seg, cj), "XGB": ajustar("XGB", pp, y, seg, cj, {"XGB": (variables, params)}, n_jobs=6)}
    pred = {n: a.puntuar(pp) for n, a in alt.items()}
    extras = {"n_segmentos": int(pd.Series(seg).nunique()), "filas": int(len(pp)), "semilla": 42, "xgb_variables": variables, "xgb_hiperparametros": params,
              "xgb_folds_que_la_eligieron": f"{n_folds} de {total}", "xgb_regla_de_eleccion": f"{regla} (f3_config_por_fold.csv, etapa principal)",
              "lr3_variables": cj["V_MIN3"], "nota_eleccion": "distinta de config_final (mayor PR-AUC interno medio), que usan los candidatos de IE10; aqui se pidio la mas frecuente por fold"}
    man = guardar_alternativas(alt, MOD, extras)
    assert not verificar_alternativas(MOD)
    de_nuevo = cargar_alternativas(MOD)
    for n in alt:
        assert np.array_equal(de_nuevo[n].puntuar(pp), pred[n]), f"la recarga de {n} no reproduce los puntajes"
    resumen = {**extras, "sha256": man["sha256"], "recarga_identica": True,
               "nota": "no hay metricas de desempeno aqui (entrenadas con todos los datos); el desempeno fuera de fold de LR3 y XGB esta en f5_metricas_candidatos.csv"}
    (REP / "f19_alternativas_congeladas.json").write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
