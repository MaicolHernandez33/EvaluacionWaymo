"""F39: tiempos de «Puntuar datos nuevos» en el navegador real (uploader real, Chrome sin interfaz). ``--modo antes`` es el flujo anterior (se sube el archivo 2 y luego el 1, y el puntaje se dispara al terminar de subir
el 1; el tiempo corre desde que se sube el 1 hasta ver el resultado). ``--modo despues`` es el flujo nuevo (se suben los dos archivos, se espera a que terminen y el tiempo corre desde el clic en «Puntuar segmento»).
3 repeticiones por segmento; informa la mediana y el peor caso. Con la página corriendo en localhost.
Uso: .venv\Scripts\python scripts/ep3/f39_tiempos.py --modo antes --puerto 8531 --salida docs/ep3/f39_tiempos_antes.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "src"))
import capturar_pagina as C  # noqa: E402
import f31_f33_capturas as F  # noqa: E402
from f37_pruebas_ui import esperar, estado, subir  # noqa: E402


def abrir(nav, puerto: int) -> None:
    F.abrir(nav, puerto, "Puntuar datos nuevos", C.CLAVE["Puntuar datos nuevos"])


def clic_puntuar(nav) -> bool:
    return bool(nav.js("(() => { const b = Array.from(document.querySelectorAll('button')).find(x => x.textContent.trim() === 'Puntuar segmento' && !x.disabled); if (!b) return false; b.click(); return true; })()"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", choices=("antes", "despues"), required=True)
    ap.add_argument("--puerto", type=int, default=8531)
    ap.add_argument("--debug", type=int, default=9398)
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--repeticiones", type=int, default=3)
    a = ap.parse_args()
    base = RAIZ / "datos_demo/candidatos"
    out: dict = {"modo": a.modo, "casos": {}}
    nav = C.Navegador(a.debug)
    try:
        for carpeta in sorted(p for p in base.iterdir() if p.is_dir()):
            tiempos, subida, cajas = [], [], None
            for _ in range(a.repeticiones):
                abrir(nav, a.puerto)
                lid, aso = carpeta / "lidar_box.parquet", carpeta / "camera_to_lidar_box_association.parquet"
                if a.modo == "antes":
                    subir(nav, 1, aso)
                    time.sleep(2.5)
                    t0 = time.time()
                    subir(nav, 0, lid)
                    est, _ = esperar(nav)
                    tiempos.append(round(time.time() - t0, 2))
                else:
                    t_up = time.time()
                    subir(nav, 0, lid)
                    subir(nav, 1, aso)
                    time.sleep(3.0)
                    subida.append(round(time.time() - t_up, 2))
                    t0 = time.time()
                    if not clic_puntuar(nav):
                        raise RuntimeError("el botón Puntuar segmento no está habilitado")
                    est, _ = esperar(nav)
                    tiempos.append(round(time.time() - t0, 2))
                lineas = [x.strip() for x in est.get("texto", "").split("\n") if x.strip()]
                cajas = next((lineas[i + 1] for i, x in enumerate(lineas) if x in ("Cajas afectadas", "Cajas puntuadas")), None)
            out["casos"][carpeta.name] = {"segundos": tiempos, "mediana": statistics.median(tiempos), "peor": max(tiempos), "subida_s": subida, "lineas": lineas[:14]}
            print(carpeta.name, tiempos, "mediana", statistics.median(tiempos))
    finally:
        nav.cerrar()
    a.salida.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
