"""F24: captura la pestaña «Curva de priorización» de la Cola en la piel oscura, sin referencia y con cada modelo de referencia (XGBoost y E2).

El juego oficial de ``capturar_pagina.py`` abre «Cola de cajas» y por eso no muestra las curvas; aquí se ve la paleta validada (dos pasos, un paso, regla de puntos y las dos referencias)
con las etiquetas directas sobre la línea. Clics reales del ratón (un ``click()`` de JavaScript no abre los selectores de Streamlit). Escribe ``images/ep3/pagina/02b_curvas_*.png`` (a 1366 px; sin el ancho en el nombre para no entrar en la cuenta de 15 capturas por ancho).
Requiere la página corriendo en localhost. Uso: .venv\\Scripts\\python scripts/ep3/f24_capturar_curvas.py --puerto 8531
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

SALIDA = RAIZ / "images/ep3/pagina"
JS_SELECTOR = """((rotulo) => { const l = Array.from(document.querySelectorAll('label')).find(x => x.textContent.includes(rotulo)); if (!l) return null;
  const caja = l.closest('[data-testid="stSelectbox"]'); if (!caja) return null; const c = caja.querySelector('[role="combobox"]') || caja.querySelector('[data-baseweb="select"]'); const r = c ? c.getBoundingClientRect() : caja.getBoundingClientRect();
  return JSON.stringify({x: r.left + r.width / 2, y: r.top + r.height / 2}); })(%s)"""
JS_OPCIONES = """(() => JSON.stringify(Array.from(document.querySelectorAll('[role=option]')).map(o => { const r = o.getBoundingClientRect(); return {texto: o.textContent.trim(), x: r.left + r.width / 2, y: r.top + r.height / 2}; })))()"""
JS_GRAFICO = """(() => { const g = document.querySelector('.vega-embed'); if (!g) return null; const r = g.getBoundingClientRect(); return JSON.stringify({x: r.left, y: r.top + window.scrollY, w: r.width, h: r.height}); })()"""


def clic(nav: C.Navegador, x: float, y: float) -> None:
    for tipo in ("mouseMoved", "mousePressed", "mouseReleased"):
        nav.cmd("Input.dispatchMouseEvent", type=tipo, x=x, y=y, button="left", clickCount=1)


def foto(nav: C.Navegador, nombre: str, ancho: int) -> str:
    nav.cmd("Emulation.setDeviceMetricsOverride", width=ancho, height=1500, deviceScaleFactor=1, mobile=False)
    time.sleep(1.5)
    g = nav.js(JS_GRAFICO)
    alto = int(min(max((g["y"] + g["h"] + 200) if g else 900, 700), 1500))
    nav.cmd("Emulation.setDeviceMetricsOverride", width=ancho, height=alto, deviceScaleFactor=1, mobile=False)
    time.sleep(1.2)
    datos = nav.cmd("Page.captureScreenshot", format="png")["data"]
    ruta = SALIDA / f"{nombre}.png"                         # sin el ancho en el nombre: el juego oficial de 15 capturas por ancho se cuenta con *_1366.png y *_1920.png
    ruta.write_bytes(base64.b64decode(datos))
    return ruta.name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8512)
    ap.add_argument("--debug", type=int, default=9339)
    ap.add_argument("--ancho", type=int, default=1366)
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    hechas: list[dict] = []
    try:
        nav.cmd("Emulation.setDeviceMetricsOverride", width=a.ancho, height=900, deviceScaleFactor=1, mobile=False)
        nav.cmd("Page.navigate", url=C.url(a.puerto, "Cola de revisión"))
        ok, _, motivo, _, _ = C.esperar(nav, "Cola de revisión", 60.0, 2.0, C.CLAVE_PREVIA.get("Cola de revisión"))
        if not ok:
            sys.exit(f"la Cola no terminó de dibujarse: {motivo}")
        nav.js("(() => { const t = Array.from(document.querySelectorAll('[role=tab]')).find(x => x.textContent.includes('Curva de priorización')); if (t) t.click(); return !!t; })()")      # F32: la curva es la segunda pestaña
        time.sleep(2.5)
        hechas.append({"vista": "sin referencia", "archivo": foto(nav, "02b_curvas_sin_referencia", a.ancho)})
        opciones: list[str] = []
        for etiqueta, clave in (("XGB", "02b_curvas_con_xgboost"), ("E2", "02b_curvas_con_e2")):
            pos = nav.js(JS_SELECTOR % json.dumps("Comparar con"))
            if not pos:
                sys.exit("no se encontró el selector «Comparar con»")
            clic(nav, pos["x"], pos["y"])
            time.sleep(1.0)
            ops = nav.js(JS_OPCIONES) or []
            opciones = [o["texto"] for o in ops]
            elegida = next((o for o in ops if o["texto"].startswith(etiqueta)), None)
            if elegida is None:
                print(f"AVISO: no hay una opción que empiece por {etiqueta}; opciones: {opciones}")
                nav.cmd("Input.dispatchKeyEvent", type="keyDown", key="Escape")
                continue
            clic(nav, elegida["x"], elegida["y"])
            time.sleep(4.0)
            hechas.append({"vista": f"referencia {elegida['texto']}", "archivo": foto(nav, clave, a.ancho)})
    finally:
        nav.cerrar()
    print(json.dumps(hechas, ensure_ascii=False))


if __name__ == "__main__":
    main()
