"""F25: mide la barra lateral en una ventana de EXACTAMENTE 1366 x 768 px.

Lo que importa: que el selector «Rol» (lo último de la barra) quede VISIBLE sin desplazar la barra (su borde inferior dentro de la ventana) y que ningún elemento quede
recortado. Escribe ``docs/ep3/f25_barra_lateral.json`` y la imagen ``images/ep3/pagina/f25_barra_normal_1366x768.png``. Requiere la página corriendo en localhost.
Uso: .venv\Scripts\python scripts/ep3/f25_medir_barra.py --puerto 8531
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capturar_pagina as C  # noqa: E402

SALIDA_JSON = RAIZ / "docs/ep3/f25_barra_lateral.json"
SALIDA_IMG = RAIZ / "images/ep3/pagina"
JS_MEDIDAS = """(() => {
  const cont = document.querySelector('[data-testid="stSidebarContent"]'); const barra = document.querySelector('[data-testid="stSidebar"]');
  const caja = e => { if (!e) return null; const b = e.getBoundingClientRect(); return {arriba: Math.round(b.top), abajo: Math.round(b.bottom)}; };
  const rol = barra.querySelector('[data-testid="stSelectbox"]');
  const enlaces = Array.from(barra.querySelectorAll('[data-testid="stSidebarNavLink"]'));
  return JSON.stringify({alto_ventana: window.innerHeight, alto_contenido_barra: cont.scrollHeight, alto_visible_barra: cont.clientHeight, desborde_px: cont.scrollHeight - cont.clientHeight,
    rol: caja(rol), primer_enlace: caja(enlaces[0]), ultimo_enlace: caja(enlaces[enlaces.length - 1]), enlaces: enlaces.length, encabezado: caja(barra.querySelector('[data-testid="stSidebarHeader"]')),
    scroll_horizontal_px: document.documentElement.scrollWidth - window.innerWidth});
})()"""


def medir(nav: C.Navegador) -> dict:
    ok, _, motivo, _, _ = C.esperar(nav, "Resumen", 60.0, 2.0)
    if not ok:
        sys.exit(f"el Resumen no terminó de dibujarse: {motivo}")
    time.sleep(1.0)
    m = nav.js(JS_MEDIDAS)
    m["modo"] = "normal"
    m["rol_visible"] = bool(m["rol"]) and 0 <= m["rol"]["arriba"] and m["rol"]["abajo"] <= m["alto_ventana"]
    nombre = "f25_barra_normal_1366x768.png"
    (SALIDA_IMG / nombre).write_bytes(base64.b64decode(nav.cmd("Page.captureScreenshot", format="png")["data"]))
    m["imagen"] = nombre
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8512)
    ap.add_argument("--debug", type=int, default=9341)
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    resultados = []
    try:
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=768, deviceScaleFactor=1, mobile=False)
        nav.cmd("Page.navigate", url=C.url(a.puerto, "Resumen"))
        resultados.append(medir(nav))
    finally:
        nav.cerrar()
    SALIDA_JSON.write_text(json.dumps(resultados, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resultados, ensure_ascii=False))


if __name__ == "__main__":
    main()
