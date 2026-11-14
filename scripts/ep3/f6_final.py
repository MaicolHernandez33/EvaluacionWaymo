"""F6 (IE12), parte 2: entrena la solucion elegida con los 41 segmentos y CONGELA v3 en data/06_models_ep3.

Escribe modelo_final_v3.joblib, umbrales_v3.json, detector_params_v3.json y manifest_v3.json (con sha256).
Los umbrales A y B y el calibrador Platt se fijan con las predicciones fuera de fold (f4_oof.parquet) del elegido.
Uso: python scripts/ep3/f6_final.py
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

import sklearn  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

from waymo_evaluacion.ep3 import modelos as M  # noqa: E402
from waymo_evaluacion.ep3.candidatos import BASE, ajustar, entrada_calibrador  # noqa: E402
from waymo_evaluacion.ep3.congelado import CalibradorPlatt  # noqa: E402
from waymo_evaluacion.ep3.detector_huecos import ParametrosDetector  # noqa: E402
from waymo_evaluacion.ep3.inferencia import Artefactos, cargar_artefactos  # noqa: E402
from waymo_evaluacion.ep3.metricas import umbral_para_recall, umbral_para_revision  # noqa: E402
from waymo_evaluacion.ep3.plan import cargar_plan_v3, leer_hashes  # noqa: E402
from waymo_evaluacion.ep3.seleccion import config_final, veredictos  # noqa: E402
from waymo_evaluacion.ep3.sellado import construir_manifest  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
MOD = RAIZ / "data/06_models_ep3"
SEM = 42


def main() -> None:
    plan = cargar_plan_v3(RAIZ)
    sel = json.loads((REP / "f6_seleccion.json").read_text(encoding="utf-8"))
    elegido = sel["elegido"]
    if not elegido:
        sys.exit("DETENIDO: F6 no declaro un elegido (ningun candidato cumple O1, O3 y O4). Revisar f6_seleccion.json y decidir en ESTADO.md.")
    ver = veredictos(REP)
    cfgs = {m: config_final(REP, m, ver) for m in BASE}
    pp = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    pp = pp[pp["en_zona_principal"]].reset_index(drop=True)
    cj = json.loads((RAIZ / "data/05_model_input_ep3/conjuntos_variables.json").read_text(encoding="utf-8"))
    y, seg = pp["sin_camara"].to_numpy(), pp["seg"].to_numpy()
    print("elegido:", elegido, "| configs finales:", {k: v for k, v in cfgs.items() if v})
    puntuador = ajustar(elegido, pp, y, seg, cj, cfgs, n_jobs=6)

    oof = pd.read_parquet(RAIZ / "data/07_model_output_ep3/f4_oof.parquet")[elegido].to_numpy()
    entrada = entrada_calibrador(elegido)
    cal = CalibradorPlatt(LogisticRegression(C=1e6, max_iter=1000), entrada)
    cal.lr.fit(cal._feat(oof), y)
    umbrales = {"A": umbral_para_recall(y, oof, 0.80), "B": umbral_para_revision(oof, 0.20)}
    detector = ParametrosDetector.from_dict(json.loads((MOD / "detector_params_v3.json").read_text(encoding="utf-8")))
    desc = {"candidato": elegido, "configs_bases": {k: (list(v) if v else "defecto") for k, v in cfgs.items()}, "filas_entrenamiento": int(len(pp)), "segmentos": int(pp["seg"].nunique()),
            "calibrador": f"Platt sobre scores fuera de fold ({entrada})", "umbrales": "A: recall 0,80 y B: 20 % de revision, sobre scores fuera de fold",
            "nota_E2": "los puntajes de E2 son rangos dentro del lote puntuado" if elegido == "E2" else ""}
    Artefactos(puntuador, cal, umbrales, detector, desc).guardar(MOD)
    extras = {"candidato": elegido, "semilla": SEM, "plan_v3_sha256": leer_hashes(RAIZ / "docs/ep3"),
              "versiones": {"python": platform.python_version(), "scikit-learn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
              "descripcion": desc, "umbrales": umbrales}
    try:
        import lightgbm
        import xgboost
        extras["versiones"].update({"xgboost": xgboost.__version__, "lightgbm": lightgbm.__version__})
    except ImportError:
        pass
    (MOD / "manifest_v3.json").write_text(json.dumps(construir_manifest(MOD, extras), indent=1, ensure_ascii=False), encoding="utf-8")

    # ---- verificacion: se recarga y se compara
    art = cargar_artefactos(MOD)
    s = art.puntuador.puntuar(pp)
    info = {"candidato": elegido, "AUC_en_los_datos_de_ajuste (NO es desempeno)": float(roc_auc_score(y, s)), "AUC_fuera_de_fold": float(roc_auc_score(y, oof)),
            "umbrales": umbrales, "recarga_identica": bool(np.allclose(s, puntuador.puntuar(pp)))}
    (REP / "f6_final_resumen.json").write_text(json.dumps(info, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(info, indent=1, ensure_ascii=False))
    print("archivos congelados:", sorted(p.name for p in MOD.iterdir()))


if __name__ == "__main__":
    main()
