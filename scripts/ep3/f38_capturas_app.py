"""F38: las 4 capturas de la aplicación (Lente) que usa la sección 16 del README, en ``images/app/`` a 1366 px. Con la página corriendo en localhost.
Uso: .venv\Scripts\python scripts/ep3/f38_capturas_app.py --puerto 8531
"""
from __future__ import annotations

import argparse
import base64
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "src"))
import capturar_pagina as C  # noqa: E402
import f31_f33_capturas as F  # noqa: E402

DESTINO = RAIZ / "images/app"


def foto(nav, nombre: str, alto: int) -> None:
    nav.cmd("Emulation.setDeviceMetricsOverride", width=F.ANCHO, height=alto + 40, deviceScaleFactor=1, mobile=False)
    time.sleep(1.2)
    nav.js("(() => { window.scrollTo(0, 0); return true; })()")
    datos = nav.cmd("Page.captureScreenshot", format="png", clip={"x": 0, "y": 0, "width": F.ANCHO, "height": alto, "scale": 1})["data"]
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / f"{nombre}.png").write_bytes(base64.b64decode(datos))
    print(f"OK {nombre} {F.ANCHO} x {alto}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8531)
    ap.add_argument("--debug", type=int, default=9395)
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    try:
        for seccion, nombre, alto in (("Resumen", "lente_resumen", 1000), ("Auditoría de cámaras", "lente_auditoria", 900), ("Cola de revisión", "lente_cola", 1000)):
            F.abrir(nav, a.puerto, seccion, C.CLAVE_PREVIA.get(seccion, C.CLAVE[seccion]))
            time.sleep(1.5)
            foto(nav, nombre, alto)
        F.abrir(nav, a.puerto, "Puntuar datos nuevos", C.CLAVE["Puntuar datos nuevos"])
        nav.js(f"({F.JS_CLIC_TEXTO})('button', 'Usar un segmento de desarrollo de ejemplo', true)")
        time.sleep(8)
        foto(nav, "lente_puntuar_ejemplo", 1000)
    finally:
        nav.cerrar()


if __name__ == "__main__":
    main()
