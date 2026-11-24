"""F37: mide segmentos con el código REAL de la página (``inferencia.puntuar_segmento`` con la solución congelada), sin pasar por la interfaz. Solo lee; escribe un JSON de resultados.

Dos usos:
  candidatos  Para cada carpeta ``<base>/<segmento>/`` con ``lidar_box.parquet`` y ``camera_to_lidar_box_association.parquet``: cajas puntuadas, % sin pareja, celdas marcadas y, por cámara,
              las cajas en rango y la tasa de parejas (para ver qué cámara admite un hueco simulado: el detector exige >= 100 cajas en el rango).
  hueco       Para una carpeta y una cámara: prueba las fracciones 0,90 / 0,95 / 0,98 / 1,0 (con ``crear_demo_hueco.quitar_camara``, semilla 7) y dice cuál es la MENOR que marca exactamente
              esa celda y solo esa.

Uso: .venv\\Scripts\\python scripts/ep3/f37_analizar.py candidatos --base datos_demo/candidatos --salida docs/ep3/f37_candidatos.json
     .venv\\Scripts\\python scripts/ep3/f37_analizar.py hueco --carpeta datos_demo/candidatos/<segmento> --camara 3 --salida docs/ep3/f37_hueco.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.inferencia import cargar_artefactos, puntuar_segmento  # noqa: E402

FRACCIONES = (0.90, 0.95, 0.98, 1.0)
SEMILLA = 7


def _crear():
    spec = importlib.util.spec_from_file_location("crear_demo_hueco", RAIZ / "scripts/crear_demo_hueco.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _archivos(carpeta: Path) -> tuple[Path, Path | None]:
    lidar = carpeta / "lidar_box.parquet"
    asoc = sorted(carpeta.glob("camera_to_lidar_box_association*.parquet"))
    return lidar, (asoc[0] if asoc else None)


def medir(lidar: pd.DataFrame, asoc: pd.DataFrame | None, art) -> dict:
    r = puntuar_segmento(lidar, asoc, art)
    out = {"cajas_puntuadas": int(len(r.cajas)), "celdas_marcadas": int(len(r.lista_A)), "cajas_en_celdas_marcadas": int(r.resumen.get("cajas_en_celdas_con_hueco", 0)),
           "cajas_en_cola": int(len(r.lista_B)), "tiene_asociacion": bool(r.resumen.get("tiene_asociacion"))}
    if "positivos_total" in r.resumen:
        out["sin_pareja"] = int(r.resumen["positivos_total"])
        out["pct_sin_pareja"] = round(100 * r.resumen["positivos_total"] / max(len(r.cajas), 1), 2)
    if len(r.tasas):
        out["por_camara"] = {c: {"cajas_en_rango": int(r.tasas[("cajas_en_rango", c)].iloc[0]), "tasa": None if pd.isna(r.tasas[("tasa", c)].iloc[0]) else round(float(r.tasas[("tasa", c)].iloc[0]), 3)}
                             for c in r.tasas["tasa"].columns}
    out["celdas"] = r.lista_A[["camara", "tasa", "umbral", "cajas_en_rango", "cajas_afectadas"]].to_dict("records") if len(r.lista_A) else []
    return out


def candidatos(base: Path, salida: Path) -> None:
    art = cargar_artefactos(RAIZ / "data/06_models_ep3")
    res = {}
    for carpeta in sorted(p for p in base.iterdir() if p.is_dir()):
        lidar, asoc = _archivos(carpeta)
        if not lidar.exists() or asoc is None:
            print(f"(se omite {carpeta.name}: faltan archivos)")
            continue
        res[carpeta.name] = medir(pd.read_parquet(lidar), pd.read_parquet(asoc), art)
        m = res[carpeta.name]
        print(f"{carpeta.name}: cajas {m['cajas_puntuadas']}, sin pareja {m.get('pct_sin_pareja')} %, celdas marcadas {m['celdas_marcadas']}, en rango por cámara "
              f"{ {c: v['cajas_en_rango'] for c, v in m.get('por_camara', {}).items()} }")
    salida.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")


def hueco(carpeta: Path, camara: int, salida: Path) -> None:
    art = cargar_artefactos(RAIZ / "data/06_models_ep3")
    crear = _crear()
    lidar_p, asoc_p = _archivos(carpeta)
    lidar, asoc = pd.read_parquet(lidar_p), pd.read_parquet(asoc_p)
    base = medir(lidar, asoc, art)
    celda = f"c{camara}"
    intentos, elegida = [], None
    for f in FRACCIONES:
        m = medir(lidar, crear.quitar_camara(asoc, camara, f, SEMILLA), art)
        pc = m["por_camara"][celda]
        marcadas = [c["camara"] for c in m["celdas"]]
        exacta = m["celdas_marcadas"] == 1 and base["celdas_marcadas"] == 0
        intentos.append({"fraccion": f, "cajas_en_la_celda": pc["cajas_en_rango"], "tasa_de_parejas": pc["tasa"], "celdas_marcadas": marcadas, "marcada_exactamente_esa": bool(exacta),
                         "cajas_en_celdas_marcadas": m["cajas_en_celdas_marcadas"], "pct_sin_pareja": m.get("pct_sin_pareja"), "cajas_en_cola": m["cajas_en_cola"]})
        print(intentos[-1])
        if exacta and elegida is None:
            elegida = f
    out = {"carpeta": carpeta.name, "camara": camara, "antes": base, "intentos": intentos, "fraccion_elegida": elegida,
           "criterio": "la menor fraccion de {0,90; 0,95; 0,98; 1,0} que marca exactamente esa celda y solo esa (sin celdas marcadas antes)"}
    salida.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("fraccion elegida:", elegida)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("candidatos")
    a.add_argument("--base", type=Path, required=True)
    a.add_argument("--salida", type=Path, required=True)
    b = sub.add_parser("hueco")
    b.add_argument("--carpeta", type=Path, required=True)
    b.add_argument("--camara", type=int, required=True)
    b.add_argument("--salida", type=Path, required=True)
    n = ap.parse_args()
    if n.cmd == "candidatos":
        candidatos(n.base, n.salida)
    else:
        hueco(n.carpeta, n.camara, n.salida)


if __name__ == "__main__":
    main()
