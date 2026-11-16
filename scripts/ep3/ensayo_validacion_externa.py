"""F19-A3: ENSAYO GENERAL de la validacion externa con DATOS DE DESARROLLO (no son segmentos nuevos; sus resultados no se usan para decidir nada).

Arma en C:\\Users\\maico\\tmp_verificacion_ep3\\ensayo_nuevos la misma estructura que produce el notebook 00b (segmentos_nuevos_ep3/ con lidar_box/,
camera_to_lidar_box_association/ y segmentos_nuevos_ep3.csv con las mismas columnas) para 4 segmentos de data/01_raw/waymo: los 2 con hueco (257766998801 y
911012534050) y 2 normales y pequenos (102124064984 y 497181704156). Corre con el CLI real: congelar (manifest alternativo), ingesta_nuevos (salida alternativa) y
evaluar --ensayo, midiendo tiempo y memoria maxima. Comprueba: (i) las 16 variables ingeridas coinciden con dev_41 (tolerancia 1e-9), (ii) el detector marca las 2 celdas
de referencia, (iii) se escriben todas las salidas externa_*, (iv) tiempos y memoria. Escribe data/08_reporting_ep3/ensayo_resultado.json; el informe lo genera
scripts/ep3/generar_ensayo_md.py. No toca el manifest_nuevos.json real, ni nuevos.parquet real, ni el candado.
Uso: .venv\\Scripts\\python scripts/ep3/ensayo_validacion_externa.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

RAIZ = Path(__file__).resolve().parents[2]
BASE = Path(r"C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos")
PAQ = BASE / "segmentos_nuevos_ep3"
SEGS = {"257766998801": "con hueco (camara 3)", "911012534050": "con hueco (camara 5)", "102124064984": "normal y pequeno", "497181704156": "normal y pequeno"}
REF = {("257766998801", "c3"), ("911012534050", "c5")}
V16 = ["box_center_x", "box_center_y", "box_center_z", "azimut_abs_deg", "distancia_m", "box_length", "box_width", "box_height", "volumen_caja", "num_lidar_points", "num_top_lidar_points",
       "densidad_puntos", "speed_mps", "heading_sin", "heading_cos", "es_ciclista"]
LLAVE = ["key.frame_timestamp_micros", "key.laser_object_id"]
PY = RAIZ / ".venv" / "Scripts" / "python.exe"
ENS_SAL = RAIZ / "data/08_reporting_ep3/ensayo_externa"


def armar_paquete() -> pd.DataFrame:
    """Misma estructura y columnas que el notebook 00b; las cifras se calculan con las mismas formulas que su celda de evaluacion."""
    if BASE.exists():
        shutil.rmtree(BASE)
    (PAQ / "lidar_box").mkdir(parents=True)
    (PAQ / "camera_to_lidar_box_association").mkdir()
    inv = pd.read_csv(RAIZ / "docs/seleccion_segmentos/inventario_segmentos.csv", dtype={"segment_id": str}).set_index("segment_id")
    filas = []
    for corto in SEGS:
        completo = next(p.stem for p in (RAIZ / "data/01_raw/waymo/lidar_box").glob(f"{corto}*.parquet"))
        for comp in ("lidar_box", "camera_to_lidar_box_association"):
            shutil.copy(RAIZ / "data/01_raw/waymo" / comp / f"{completo}.parquet", PAQ / comp / f"{completo}.parquet")
        a = pd.read_parquet(PAQ / "camera_to_lidar_box_association" / f"{completo}.parquet", columns=["key.frame_timestamp_micros", "key.laser_object_id"])
        l = pd.read_parquet(PAQ / "lidar_box" / f"{completo}.parquet", columns=["key.frame_timestamp_micros", "key.laser_object_id"])
        par = l.merge(a.drop_duplicates().assign(_p=1), on=["key.frame_timestamp_micros", "key.laser_object_id"], how="left")
        par["_p"] = par["_p"].fillna(0)
        etiquetado = par.groupby("key.frame_timestamp_micros")["_p"].transform("max") > 0
        en_frames = par[etiquetado]
        m = inv.loc[completo]
        filas.append({"segment_id": completo, "estrato": f"{m['time_of_day']} / {m['location']}", "time_of_day": m["time_of_day"], "location": m["location"], "n_frames_inventario": int(m["n_frames"]),
                      "asoc_filas": len(a), "lidar_filas": len(l), "positivos": int(par["_p"].sum()), "tasa_etiquetado_pct": round(100 * float(en_frames["_p"].sum()) / max(len(en_frames), 1), 3)})
    lista = pd.DataFrame(filas)
    lista.to_csv(PAQ / "segmentos_nuevos_ep3.csv", index=False)
    return lista


def correr(nombre: str, args: list[str]) -> dict:
    """Corre un comando del CLI real midiendo el tiempo y la memoria maxima (RSS del proceso y sus hijos)."""
    t0 = time.time()
    p = subprocess.Popen([str(PY), "-X", "utf8", *args], cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    pico = [0]
    parar = threading.Event()

    def vigilar():
        try:
            pr = psutil.Process(p.pid)
        except psutil.NoSuchProcess:
            return
        while not parar.is_set():
            try:
                rss = pr.memory_info().rss + sum(c.memory_info().rss for c in pr.children(recursive=True))
                pico[0] = max(pico[0], rss)
            except psutil.Error:
                pass
            time.sleep(0.05)

    h = threading.Thread(target=vigilar, daemon=True)
    h.start()
    out, err = p.communicate()
    parar.set()
    h.join()
    return {"paso": nombre, "comando": " ".join(["python", *[a.replace(str(RAIZ) + "\\", "") for a in args]]), "codigo": p.returncode, "segundos": round(time.time() - t0, 1),
            "memoria_max_mb": round(pico[0] / 1e6), "stdout": out[-3500:], "stderr": err[-1500:]}


def main() -> None:
    lista = armar_paquete()
    csv = str(PAQ / "segmentos_nuevos_ep3.csv")
    manifest = str(BASE / "manifest_nuevos_ensayo.json")
    parquet = BASE / "nuevos_ensayo.parquet"
    real = RAIZ / "data/06_models_ep3/manifest_nuevos.json"
    nuevos_real = RAIZ / "data/05_model_input_ep3/nuevos.parquet"
    lock = RAIZ / "data/08_reporting_ep3/evaluacion_externa.lock"
    antes = {p: (p.exists(), p.stat().st_mtime if p.exists() else None) for p in (real, nuevos_real, lock)}
    if ENS_SAL.exists():
        shutil.rmtree(ENS_SAL)
    pasos = [correr("1. congelar (manifest alternativo)", ["scripts/ep3/evaluar_sellado.py", "congelar", "--lista", csv, "--manifest", manifest]),
             correr("2. ingesta_nuevos (salida alternativa)", ["scripts/ep3/ingesta_nuevos.py", "--entrada", str(PAQ), "--lista", csv, "--salida", str(parquet), "--resumen", str(BASE / "nuevos_resumen_ensayo.csv")]),
             correr("3. evaluar --ensayo", ["scripts/ep3/evaluar_sellado.py", "evaluar", "--ensayo", "--lista", csv, "--manifest", manifest, "--entrada", str(parquet)])]
    r: dict = {"nota": "ENSAYO con datos de DESARROLLO (4 segmentos de data/01_raw/waymo); no son segmentos nuevos y sus resultados no se usan para decidir nada", "segmentos": SEGS,
               "pasos": [{k: v for k, v in p.items() if k not in ("stdout", "stderr")} for p in pasos], "errores": [p["stderr"] for p in pasos if p["codigo"] != 0]}
    if any(p["codigo"] != 0 for p in pasos):
        r["stdout_ultimo"] = pasos[-1]["stdout"]
        (RAIZ / "data/08_reporting_ep3/ensayo_resultado.json").write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(r, indent=1, ensure_ascii=False)[:3000])
        sys.exit(1)
    # (i) variables ingeridas contra dev_41
    nu = pd.read_parquet(parquet)
    dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
    dev = dev[dev["seg"].isin(SEGS)]
    m = nu.merge(dev, on=["segment_id", *LLAVE], suffixes=("_n", "_d"), how="outer", indicator=True)
    cmp: dict = {"filas_ingeridas": int(len(nu)), "filas_dev_41": int(len(dev)), "filas_solo_en_ingesta": int((m["_merge"] == "left_only").sum()), "filas_solo_en_dev_41": int((m["_merge"] == "right_only").sum())}
    both = m[m["_merge"] == "both"]
    dif = {}
    for c in V16 + ["az_signed", "c1", "c2", "c3", "c4", "c5", "sin_camara"]:
        a, b = both[f"{c}_n"].to_numpy(float), both[f"{c}_d"].to_numpy(float)
        igual_nan = np.isnan(a) & np.isnan(b)
        d = np.where(igual_nan, 0.0, np.abs(a - b))
        dif[c] = float(np.nanmax(d)) if len(d) else 0.0
    zona = bool((both["en_zona_principal_n"] == both["en_zona_principal_d"]).all())
    cmp.update({"diferencia_maxima_por_variable": dif, "diferencia_maxima_global": max(dif.values()), "en_zona_principal_igual": zona, "tolerancia": 1e-9})
    cmp["coinciden"] = bool(cmp["filas_solo_en_ingesta"] == 0 and cmp["filas_solo_en_dev_41"] == 0 and cmp["diferencia_maxima_global"] <= 1e-9 and zona)
    # (ii) celdas de referencia y (iii) salidas
    la = pd.read_csv(ENS_SAL / "externa_lista_A.csv", dtype={"segmento": str})
    marcadas = {(s, c) for s, c in zip(la["segmento"], la["camara"])}
    salidas = sorted(p.name for p in ENS_SAL.glob("externa_*.csv"))
    esperadas = {"externa_metricas.csv", "externa_diferencias.csv", "externa_puntos.csv", "externa_brazos.csv", "externa_detector.csv", "externa_lista_A.csv", "externa_alternativas.csv"}
    det = pd.read_csv(ENS_SAL / "externa_detector.csv")
    intactos = all((p.exists(), p.stat().st_mtime if p.exists() else None) == antes[p] for p in antes)
    r.update({"variables_vs_dev_41": cmp, "celdas_marcadas": sorted(f"{s}|{c}" for s, c in marcadas), "marca_las_2_de_referencia": REF <= marcadas, "celdas_marcadas_ademas_de_las_2": sorted(f"{s}|{c}" for s, c in marcadas - REF),
              "salidas_escritas": salidas, "salidas_esperadas_faltantes": sorted(esperadas - set(salidas)), "detector": det.drop(columns=["nota"]).round(4).to_dict("records"),
              "lo_real_quedo_intacto": bool(intactos), "paquete_columnas": list(lista.columns), "lista": lista.to_dict("records"), "tiempo_total_s": round(sum(p["segundos"] for p in pasos), 1),
              "memoria_max_mb": max(p["memoria_max_mb"] for p in pasos)})
    r["todo_ok"] = bool(cmp["coinciden"] and r["marca_las_2_de_referencia"] and not r["salidas_esperadas_faltantes"] and r["lo_real_quedo_intacto"])
    (RAIZ / "data/08_reporting_ep3/ensayo_resultado.json").write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k not in ("lista",)}, indent=1, ensure_ascii=False)[:5000])
    print("\n--- stdout de evaluar (extracto) ---\n", pasos[-1]["stdout"][:1500])
    sys.exit(0 if r["todo_ok"] else 1)


if __name__ == "__main__":
    main()
