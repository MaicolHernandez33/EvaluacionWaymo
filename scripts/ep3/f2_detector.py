"""F2: detector de huecos (parametros de EP2) sobre los 41 segmentos, Lista A y baselines con IC.

Escribe en data/06_models_ep3 (parametros del detector), data/05_model_input_ep3 (marca por fila)
y data/08_reporting_ep3. Compara contra los CSV del apendice M de EP2 (solo lectura).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.detector_huecos import (  # noqa: E402
    ParametrosDetector, calcular_medianas, calcular_rangos, detectar_huecos, marcar_cajas_en_hueco, resumen_celdas, tasa_por_celda,
)
from waymo_evaluacion.ep3.metricas import METRICAS, ConjuntoOOF, ic95  # noqa: E402
from waymo_evaluacion.ep3.plan import cargar_plan_v3  # noqa: E402

SEED = 42


def main() -> None:
    plan = cargar_plan_v3(RAIZ)
    p3 = plan["P3"]
    in_dir, mod_dir, rep_dir = RAIZ / "data/05_model_input_ep3", RAIZ / "data/06_models_ep3", RAIZ / "data/08_reporting_ep3"
    for d in (mod_dir, rep_dir):
        d.mkdir(parents=True, exist_ok=True)
    dev = pd.read_parquet(in_dir / "dev_41.parquet")
    camaras = [1, 2, 3, 4, 5]
    nombres = {int(str(n).split()[0]): str(n) for n in pd.read_csv(RAIZ / "data/08_reporting/08_azimut_por_camara_empirico.csv")["camara"]}

    # ---- parametros del detector (P3): rango con train, mediana con los 41, sin recalcular criterios
    rangos = calcular_rangos(dev[dev["grupo"] == "train"], camaras, p3["rango_percentiles"][0], p3["rango_percentiles"][1])
    tasa, nrango = tasa_por_celda(dev, rangos, camaras)
    med = calcular_medianas(tasa)
    huecos = detectar_huecos(tasa, nrango, None, p3["frac"], p3["min_cajas"])
    par = ParametrosDetector(frac=p3["frac"], min_cajas=p3["min_cajas"], p_inf=p3["rango_percentiles"][0], p_sup=p3["rango_percentiles"][1],
                             rangos=rangos, medianas_ref=med.to_dict())
    (mod_dir / "detector_params_v3.json").write_text(json.dumps(par.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    resumen = resumen_celdas(dev, tasa, nrango, huecos)
    resumen.to_csv(rep_dir / "f2_tasa_segmento_camara.csv")

    # ---- reproduccion contra EP2 (solo lectura)
    rep = RAIZ / "data/08_reporting"
    ref_t = pd.read_csv(rep / "10_M_tasa_segmento_camara.csv", index_col=0, dtype={"seg": str})
    num = [c for c in ref_t.columns if c.startswith(("tasa_", "n_rango_"))] + ["cajas"]
    d_t = float(np.nanmax(np.abs(ref_t[num].to_numpy(float) - resumen.loc[ref_t.index, num].to_numpy(float))))
    ok_h = bool((ref_t[[c for c in ref_t.columns if c.startswith("hueco_")]].to_numpy() == resumen.loc[ref_t.index, [c for c in ref_t.columns if c.startswith("hueco_")]].to_numpy()).all())
    ref_r = pd.read_csv(rep / "10_M_rangos_camara.csv")
    d_r = float(max(np.abs(ref_r["az_p5"] - [rangos[c][0] for c in camaras]).max(), np.abs(ref_r["az_p95"] - [rangos[c][1] for c in camaras]).max(),
                    np.abs(ref_r["mediana_tasa"] - [med[f"c{c}"] for c in camaras]).max()))

    # ---- marca por fila y Lista A
    dev["en_hueco"] = marcar_cajas_en_hueco(dev, huecos, rangos).to_numpy()
    dev[["fila_id", "en_hueco"]].to_parquet(in_dir / "dev_41_hueco.parquet", index=False)
    filas = []
    ppal = dev[dev["en_zona_principal"]]
    for s in resumen.index:
        for c in camaras:
            if huecos.loc[s, f"c{c}"]:
                en = ppal[(ppal["seg"] == s) & ppal["az_signed"].between(*rangos[c])]
                filas.append({"segmento": s, "grupo": resumen.loc[s, "grupo"], "ubicacion": resumen.loc[s, "ubicacion"], "momento": resumen.loc[s, "momento"],
                              "camara": nombres[c], "tasa": tasa.loc[s, f"c{c}"], "mediana_camara": med[f"c{c}"], "umbral": p3["frac"] * med[f"c{c}"],
                              "cajas_en_rango": int(nrango.loc[s, f"c{c}"]), "cajas_afectadas_poblacion_principal": len(en), "positivos_afectados": int(en["sin_camara"].sum())})
    lista_a = pd.DataFrame(filas)
    lista_a.to_csv(rep_dir / "lista_A_huecos.csv", index=False)
    pares = {(r.segmento, r.camara) for r in lista_a.itertuples()}
    esperado = {("911012534050", "5 (lateral der.)"), ("257766998801", "3 (frontal der.)")}

    # ---- baselines sobre los 41 segmentos (reglas: no se ajustan, por eso no hay OOF)
    y = ppal["sin_camara"].to_numpy()
    reglas = {
        "Regla: menos puntos top": -ppal["num_top_lidar_points"].to_numpy(float),
        "Regla: menos puntos LiDAR": -ppal["num_lidar_points"].to_numpy(float),
        "Regla geometrica (azimut > 105 primero)": np.where(ppal["azimut_abs_deg"].to_numpy() > 105, 1e6, 0.0) - ppal["num_lidar_points"].to_numpy(float),
    }
    oof = ConjuntoOOF(y, ppal["seg"].to_numpy(), {k: [v] for k, v in reglas.items()}, SEED)
    boot = oof.bootstrap(list(reglas), 1000, SEED)
    tab = []
    for n in reglas:
        m = oof.metricas(n)
        fila = {"metodo": n}
        for i, k in enumerate(METRICAS):
            lo, hi = ic95(boot[n][:, i])
            fila.update({k: m[i], f"{k}_lo": lo, f"{k}_hi": hi})
        tab.append(fila)
    tab = pd.DataFrame(tab)
    tab.to_csv(rep_dir / "f2_baselines_reglas_41.csv", index=False)
    por_grupo = []
    for g in ("train", "test"):
        sub = ppal["grupo"].to_numpy() == g
        o2 = ConjuntoOOF(y[sub], ppal["seg"].to_numpy()[sub], {k: [v[sub]] for k, v in reglas.items()}, SEED)
        for n in reglas:
            m = o2.metricas(n)
            por_grupo.append({"grupo": g, "metodo": n, **dict(zip(METRICAS, m)), "filas": int(sub.sum()), "prevalencia": float(y[sub].mean())})
    pd.DataFrame(por_grupo).to_csv(rep_dir / "f2_baselines_reglas_por_grupo.csv", index=False)

    salida = {
        "n_pares_con_hueco": int(len(lista_a)), "pares": sorted(f"{a} | {b}" for a, b in pares), "pares_iguales_a_ep2": pares == esperado,
        "dif_max_tabla_vs_ep2": d_t, "huecos_iguales_a_ep2": ok_h, "dif_max_rangos_medianas_vs_ep2": d_r,
        "cajas_en_hueco_principal": int(dev.loc[dev["en_zona_principal"], "en_hueco"].sum()),
        "positivos_en_hueco_principal": int(dev.loc[dev["en_zona_principal"] & dev["en_hueco"], "sin_camara"].sum()),
        "prevalencia_principal": float(y.mean()), "filas_principal": int(len(y)),
    }
    (rep_dir / "f2_resumen.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(salida, ensure_ascii=False, indent=1))
    print(tab.round(3).to_string(index=False))
    print(lista_a.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
