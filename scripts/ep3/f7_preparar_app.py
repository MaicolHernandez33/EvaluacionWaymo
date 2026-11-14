"""F7: prepara data/09_app_ep3 para la pagina (predicciones FUERA DE FOLD, es decir, honestas).

Archivos: cajas_oof.parquet (por caja; ids solo en esta tabla local), celdas.csv, lista_A.csv, curva_cola.csv,
kpis.json y evidencia/*.csv. Lee F2 a F6; no recalcula modelos. Todo local.
Uso: python scripts/ep3/f7_preparar_app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.app_logica import AVISO_EN_MUESTRA  # noqa: E402
from waymo_evaluacion.ep3.inferencia import V16  # noqa: E402
from waymo_evaluacion.ep3.metricas import desempate, ic95, pesos_bootstrap  # noqa: E402
from waymo_evaluacion.ep3.plan import verificar_plan_v3  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"
OUT = RAIZ / "data/09_app_ep3"
GRID = np.round(np.arange(0.01, 1.0001, 0.01), 2)


def coma(x: float, d: int = 3) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def pct(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f} %".replace(".", ",")


def curvas(y, seg_codes, score, regla, aud, nb=1000, incluir_regla=True, referencias=None):
    """Recall frente a presupuesto, con IC por segmentos (bootstrap pesado): un paso (A) y dos pasos (C)."""
    n = len(y)
    tb = desempate(n)
    pesos = pesos_bootstrap(seg_codes, nb, 42)
    salida = {}
    lista = [("Solución elegida, un paso (A)", score, False), ("Regla top, un paso (A)", regla, False), ("Solución elegida, dos pasos (C)", score, True)]
    lista += [(f"{k} (referencia), un paso (A)", v, False) for k, v in (referencias or {}).items()]
    for nombre, s, dos_pasos in lista:
        if nombre.startswith("Regla top") and not incluir_regla:        # si la elegida ya es la regla, la curva seria identica
            continue
        if dos_pasos:
            ss = np.where(aud, np.inf, s)
            o = np.lexsort((tb, -ss))
            gratis = aud[o]
        else:
            o = np.lexsort((tb, -s))
            gratis = np.zeros(n, bool)
        ys, seg_o = y[o].astype(float), seg_codes[o]
        res = np.zeros((nb + 1, len(GRID)))
        for b in range(nb + 1):
            w = np.ones(n) if b == 0 else pesos[b - 1][seg_o].astype(float)
            wp = w * ys
            P = wp.sum()
            if P == 0:
                res[b] = np.nan
                continue
            cum_pos = np.cumsum(wp) / P
            cost = np.cumsum(w * (~gratis))
            Wq = cost[-1]
            idx = np.minimum(np.searchsorted(cost, GRID * Wq), n - 1)
            res[b] = cum_pos[idx]
        punto = res[0]
        lo = np.nanquantile(res[1:], 0.025, axis=0)
        hi = np.nanquantile(res[1:], 0.975, axis=0)
        salida[nombre] = pd.DataFrame({"solucion": nombre, "presupuesto": GRID, "recall": punto, "lo": lo, "hi": hi})
    return pd.concat(salida.values(), ignore_index=True)


def main() -> None:
    verificar_plan_v3(RAIZ)
    sel = json.loads((REP / "f6_seleccion.json").read_text(encoding="utf-8"))
    elegido = sel["elegido"]
    if not elegido:
        sys.exit("DETENIDO: F6 no declaro un elegido.")
    (OUT / "evidencia").mkdir(parents=True, exist_ok=True)
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    hueco = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41_hueco.parquet").set_index("fila_id")["en_hueco"]
    pp = dev[dev["en_zona_principal"]].reset_index(drop=True)
    oof = pd.read_parquet(RAIZ / "data/07_model_output_ep3/f4_oof.parquet")
    pcal = pd.read_parquet(RAIZ / "data/07_model_output_ep3/f5_pcal.parquet")
    score = oof[elegido].to_numpy()
    aud = hueco.loc[pp["fila_id"]].to_numpy().astype(bool)
    cajas = pp[["seg", "grupo", "location", "time_of_day", "key.frame_timestamp_micros", "key.laser_object_id", "sin_camara", "az_signed"] + V16].rename(
        columns={"location": "ubicacion", "time_of_day": "momento"}).copy()
    cajas["score"], cajas["prob_cal"], cajas["en_hueco"] = score, pcal[f"pcal_{elegido}"].to_numpy(), aud
    f13 = json.loads((REP / "f13_resumen.json").read_text(encoding="utf-8"))
    k_el = int(f13["k_elegido"])
    cl = pd.read_csv(REP / f"f13_clusters_k{k_el}.csv")
    etiquetas = pd.read_parquet(RAIZ / "data/07_model_output_ep3/f13_clusters.parquet")[f"cluster_k{k_el}"].to_numpy()
    cajas["tipo_caso"] = pd.Series(etiquetas).map(dict(zip(cl["cluster"], cl["tipo_de_caso"]))).to_numpy()
    cl.to_csv(OUT / "clusters.csv", index=False)
    cajas.to_parquet(OUT / "cajas_oof.parquet", index=False)
    pd.read_csv(REP / "f2_tasa_segmento_camara.csv", dtype={"seg": str}).to_csv(OUT / "celdas.csv", index=False)
    pd.read_csv(REP / "lista_A_huecos.csv", dtype={"segmento": str}).to_csv(OUT / "lista_A.csv", index=False)

    seg_codes = pd.factorize(pp["seg"].to_numpy())[0]
    cur = curvas(pp["sin_camara"].to_numpy(), seg_codes, score, -pp["num_top_lidar_points"].to_numpy(float), aud, incluir_regla=(elegido != "Regla top"), referencias={"XGB": oof["XGB"].to_numpy(), "E2": oof["E2"].to_numpy()})
    cur.to_csv(OUT / "curva_cola.csv", index=False)

    # ---- KPIs
    esc = pd.read_csv(REP / "f6_modelo_escogido.csv").iloc[0]
    f5 = pd.read_csv(REP / "f5_metricas_candidatos.csv").set_index("candidato")
    reg = f5.loc["Regla top"]
    tarj = [
        {"titulo": "AUC fuera de fold", "valor": coma(esc["AUC"]), "ic": f"IC 95 % por segmentos: {coma(esc['AUC_lo'])} a {coma(esc['AUC_hi'])}; regla top {coma(reg['AUC'])}.", "fuente": "f5_metricas_candidatos.csv"},
        {"titulo": "Recall en el punto A", "valor": pct(esc["recall_A"]), "ic": f"IC: {pct(esc['recall_A_lo'])} a {pct(esc['recall_A_hi'])}; objetivo 80 %.", "fuente": "f5_metricas_candidatos.csv"},
        {"titulo": "Captura al revisar el 20 %", "valor": pct(esc["Captura@20"]), "ic": f"IC: {pct(esc['Captura@20_lo'])} a {pct(esc['Captura@20_hi'])}; al azar sería 20 %.", "fuente": "f5_metricas_candidatos.csv"},
        {"titulo": "Cajas a revisar para el 80 %", "valor": pct(esc["Fraccion_80"]), "ic": f"IC: {pct(esc['Fraccion_80_lo'])} a {pct(esc['Fraccion_80_hi'])}; en dos pasos {pct(esc['Fraccion_80_C'])} (en muestra; post hoc; sin validación con datos nuevos).", "fuente": "f5_metricas_candidatos.csv, f5_brazoC.csv"},
        {"titulo": "Punto de equilibrio de la auditoría (en muestra)", "valor": f"{esc['equilibrio_cajas_por_auditoria']:.0f} cajas".replace(",", "."),
         "ic": f"Dos pasos empata con un paso si cada auditoría cuesta {esc['equilibrio_cajas_por_auditoria']:.0f} cajas (IC {esc['equilibrio_lo']:.0f} a {esc['equilibrio_hi']:.0f}). No se inventó un costo.", "fuente": "f5_brazoC.csv"},
    ]
    kp = {"nombre_curva": "Solución elegida, dos pasos (C)", "candidato": elegido, "tarjetas": tarj,
          "solucion_final": f"Solución final en tres capas: (1) filtro 1, el detector de huecos por cámara (parámetros de EP2 congelados); (2) {elegido} para ordenar las cajas de las celdas sanas; "
                            "(3) una persona que revisa y decide. Cifras fuera de fold sobre 41 segmentos; no es una prueba ciega.",
          "prevalencia": sel["prevalencia"]}
    (OUT / "kpis.json").write_text(json.dumps(kp, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- evidencia
    copias = {"ie9__defecto_vs_optimizado": "f3_defecto_vs_optimizado.csv", "ie9__bordes_de_grilla": "f3_bordes.csv", "ie9__curvas_de_validacion": "f3_curvas_validacion.csv",
              "ie10__ensambles_aportan": "f4_ensambles_aporta.csv", "ie10__todos_los_candidatos": "f4_candidatos_metricas.csv",
              "ie11__metricas_de_generalizacion": "f5_metricas_candidatos.csv", "ie11__brecha_regla_top": "f5_brecha_Regla_top.csv", "ie11__brecha_LR3": "f5_brecha_LR3.csv", "ie11__brecha_XGB": "f5_brecha_XGB.csv", "ie11__leave_one_segment_out_regla_top": "f5_loso_segmentos_Regla_top.csv",
              "ie12__tabla_de_seleccion": "f6_tabla_seleccion.csv", "ie12__modelo_escogido": "f6_modelo_escogido.csv", "ie12__brazo_C_y_equilibrio": "f5_brazoC.csv",
              "nosup__seleccion_de_k": "f13_seleccion_k.csv", "nosup__clusters_k2": "f13_clusters_k2.csv", "nosup__clusters_k4": "f13_clusters_k4.csv", "nosup__aporte_sobre_la_regla": "f13_aporte_cluster.csv",
              "nosup__estabilidad": "f13_estabilidad.csv", "nosup__isolation_forest": "f13_isolation_forest.csv", "nosup__comparacion_ep2_ep3": "f13_comparacion_ep2_ep3.csv",
              "posthoc__auc_por_fold_y_brazos": "f12_auc_por_fold_brazos.csv", "posthoc__diferencia_C_menos_A": "f12_diferencia_C_menos_A.csv", "posthoc__sensibilidad_detector": "f12_sensibilidad_detector.csv",
              "posthoc__equidad": "f12_equidad.csv", "posthoc__eda_tasas": "f12_eda_tasas.csv", "posthoc__eda_calidad": "f12_eda_calidad.csv"}
    for dest, src in copias.items():
        if (REP / src).exists():
            pd.read_csv(REP / src).round(4).to_csv(OUT / "evidencia" / f"{dest}.csv", index=False)
    print("listo:", sorted(p.name for p in OUT.iterdir()), "| evidencia:", len(list((OUT / 'evidencia').glob('*.csv'))), "tablas")


if __name__ == "__main__":
    main()
