"""F39: regresión de resultados de «Puntuar datos nuevos». Para cada segmento de ``datos_demo/candidatos`` (con sus dos archivos y con solo el archivo 1) y para el ejemplo de desarrollo, calcula el
resultado con la MISMA función de la página (``secciones._calcular``) y guarda los hash (sha256) del ZIP de resultados (lo que descarga la persona), de cada CSV y de las cifras de pantalla.
Con ``--comparar antes.json despues.json`` dice, caso por caso, si son idénticos.
Uso: .venv\Scripts\python scripts/ep3/f39_regresion.py --salida docs/ep3/f39_regresion_antes.json
     .venv\Scripts\python scripts/ep3/f39_regresion.py --comparar docs/ep3/f39_regresion_antes.json docs/ep3/f39_regresion_despues.json
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "app"))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def calcular() -> dict:
    import pandas as pd

    import secciones as S
    from waymo_evaluacion.ep3 import puntuar as P
    from waymo_evaluacion.ep3.app_logica import cargar_datos, ejemplo_lidar_box
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos

    D = cargar_datos(RAIZ / "data/09_app_ep3")
    det = json.loads((RAIZ / "data/06_models_ep3/detector_params_v3.json").read_text(encoding="utf-8"))
    ctx = {"D": D, "rangos": {int(k): tuple(v) for k, v in det["rangos"].items()}}
    art = cargar_artefactos(RAIZ / "data/06_models_ep3")
    casos = {}

    def resumen(vista) -> dict:
        z = P.zip_resultados(vista)
        zf = zipfile.ZipFile(io.BytesIO(z))
        tarjetas = [(t["etiqueta"], t["valor"], t.get("sufijo", ""), t["nota"]) for t in P.tarjetas(vista)]
        return {"zip_sha256": sha(z), "csv_sha256": {n: sha(zf.read(n)) for n in zf.namelist()}, "tarjetas": tarjetas, "cajas": vista.n_cajas, "celdas_marcadas": int(len(vista.lista_A)), "n_celdas": vista.n_celdas,
                "tiene_asociacion": vista.tiene_asociacion, "cola": int(len(vista.lista_B)), "resumen": {k: (v if not isinstance(v, float) else round(v, 12)) for k, v in vista.resumen.items()}}

    base = RAIZ / "datos_demo/candidatos"
    for carpeta in sorted(p for p in base.iterdir() if p.is_dir()):
        lidar, _ = P.leer_parquet((carpeta / "lidar_box.parquet").read_bytes(), "lidar_box.parquet")
        asoc, _ = P.leer_parquet((carpeta / "camera_to_lidar_box_association.parquet").read_bytes(), "asoc.parquet")
        casos[f"{carpeta.name} · archivos 1 y 2"] = resumen(S._calcular(ctx, art, lidar, asoc, "archivo", ("lidar_box.parquet", "asoc.parquet")))
        casos[f"{carpeta.name} · solo archivo 1"] = resumen(S._calcular(ctx, art, lidar, None, "archivo", ("lidar_box.parquet", None)))
    cajas, la = D["cajas"], D["lista_A"]
    seg = str(la["segmento"].iloc[0]) if la is not None and len(la) else str(cajas["seg"].iloc[0])
    casos["ejemplo de desarrollo " + seg] = resumen(S._calcular(ctx, art, ejemplo_lidar_box(cajas, seg), None, "ejemplo", ("segmento de desarrollo " + seg, None)))
    return casos


def comparar(a: Path, b: Path) -> int:
    A, B = json.loads(a.read_text(encoding="utf-8")), json.loads(b.read_text(encoding="utf-8"))
    malos = 0
    print(f"{'caso':95s} lista_B antes -> despues")
    for k in A:
        ok = k in B and {x: y for x, y in A[k].items() if x != 'zip_sha256'} == {x: y for x, y in B[k].items() if x != 'zip_sha256'}          # el ZIP lleva la hora de creacion de cada archivo: se comparan los CSV de adentro (lo que se abre) y las cifras
        malos += not ok
        print(f"{k:95s} {A[k]['csv_sha256']['lista_B_nueva.csv'][:12]} -> {B.get(k, {}).get('csv_sha256', {}).get('lista_B_nueva.csv', 'FALTA')[:12]} {'IDENTICO' if ok else 'DIFERENTE'}")
    print(f"{len(A) - malos} de {len(A)} identicos")
    return 1 if malos else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", type=Path)
    ap.add_argument("--comparar", nargs=2, type=Path)
    a = ap.parse_args()
    if a.comparar:
        return comparar(*a.comparar)
    datos = calcular()
    a.salida.write_text(json.dumps(datos, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, v in datos.items():
        print(f"{k[:90]:90s} zip {v['zip_sha256'][:12]} cajas {v['cajas']} celdas {v['celdas_marcadas']} cola {v['cola']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
