"""F25: comprueba con el ratón REAL encima que la barra de herramientas de Streamlit ya no aparece en los gráficos de la Cola > Curva de priorización (tapaba el final de la oración de referencia)
y que la de las tablas (``st.dataframe``) sigue disponible.

Mide ``display`` y el rectángulo de cada barra de herramientas con el cursor sobre el gráfico y sobre la tabla, y el cruce con la oración «... No se eligió por simplicidad; ver Validación.».
Escribe ``docs/ep3/f25_barra_herramientas.json`` y ``images/ep3/pagina/f25_curva_cursor_encima.png``. Requiere la página corriendo en localhost.
Uso: .venv\\Scripts\\python scripts/ep3/f25_comprobar_herramientas.py --puerto 8531
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
from f24_capturar_curvas import JS_OPCIONES, JS_SELECTOR, clic  # noqa: E402

SALIDA_JSON = RAIZ / "docs/ep3/f25_barra_herramientas.json"
SALIDA_IMG = RAIZ / "images/ep3/pagina/f25_curva_cursor_encima.png"
JS_GRAFICO = """(() => { const g = document.querySelector('[data-testid="stVegaLiteChart"]'); if (!g) return null; const r = g.getBoundingClientRect(); return JSON.stringify({x: r.left + r.width / 2, y: r.top + r.height / 2, arriba: r.top, w: r.width, h: r.height}); })()"""
JS_TABLA = """(() => { const g = document.querySelector('[data-testid="stDataFrame"]'); if (!g) return null; const r = g.getBoundingClientRect(); return JSON.stringify({x: r.left + r.width / 2, y: r.top + r.height / 2}); })()"""
JS_BARRAS = """(() => JSON.stringify(Array.from(document.querySelectorAll('[data-testid="stElementToolbar"]')).map(t => { const cs = getComputedStyle(t); const r = t.getBoundingClientRect();
  const padre = t.parentElement; return {en_grafico: !!padre.querySelector(':scope > [data-testid="stVegaLiteChart"]'), en_tabla: !!t.closest('[data-testid="stDataFrame"]'), display: cs.display, opacidad: cs.opacity,
                                           ancho: Math.round(r.width), alto: Math.round(r.height)}; })))()"""
JS_ORACION = """(() => { const c = Array.from(document.querySelectorAll('[data-testid="stCaptionContainer"]')).find(x => x.textContent.includes('No se eligió por simplicidad')); if (!c) return null;
  const r = c.getBoundingClientRect(); return JSON.stringify({derecha: r.right, arriba: r.top, abajo: r.bottom, texto: c.textContent.slice(-40)}); })()"""


def mover(nav: C.Navegador, x: float, y: float) -> None:
    nav.cmd("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
    time.sleep(0.8)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8512)
    ap.add_argument("--debug", type=int, default=9342)
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    res: dict = {}
    try:
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=1100, deviceScaleFactor=1, mobile=False)
        nav.cmd("Page.navigate", url=C.url(a.puerto, "Cola de revisión"))
        ok, _, motivo, _, _ = C.esperar(nav, "Cola de revisión", 60.0, 2.0, C.CLAVE_PREVIA.get("Cola de revisión"))
        if not ok:
            sys.exit(f"la Cola no terminó de dibujarse: {motivo}")
        pos = nav.js(JS_SELECTOR % json.dumps("Comparar con un modelo de referencia"))
        clic(nav, pos["x"], pos["y"])
        time.sleep(1.0)
        ops = nav.js(JS_OPCIONES) or []
        elegida = next(o for o in ops if o["texto"].startswith("XGB"))
        clic(nav, elegida["x"], elegida["y"])
        time.sleep(4.0)
        mover(nav, 5, 5)
        res["oracion"] = nav.js(JS_ORACION)
        g = nav.js(JS_GRAFICO)
        mover(nav, g["x"], g["arriba"] + 12)                                  # cursor sobre el borde superior del gráfico, donde aparece la barra
        res["barras_con_el_cursor_sobre_el_grafico"] = [b for b in nav.js(JS_BARRAS) if b["en_grafico"]]
        SALIDA_IMG.write_bytes(base64.b64decode(nav.cmd("Page.captureScreenshot", format="png")["data"]))
        res["graficos"] = len([b for b in nav.js(JS_BARRAS) if b["en_grafico"]])
        pestana = nav.js("""(() => { const t = Array.from(document.querySelectorAll('[role=tab]')).find(x => x.textContent.includes('Cola de cajas')); const r = t.getBoundingClientRect(); return JSON.stringify({x: r.left + r.width / 2, y: r.top + r.height / 2}); })()""")
        clic(nav, pestana["x"], pestana["y"])
        time.sleep(4.0)
        t = nav.js(JS_TABLA)
        mover(nav, t["x"], t["y"])
        res["barras_con_el_cursor_sobre_la_tabla"] = [b for b in nav.js(JS_BARRAS) if b["en_tabla"]]
    finally:
        nav.cerrar()
    res["grafico_sin_barra"] = all(b["display"] == "none" for b in res.get("barras_con_el_cursor_sobre_el_grafico", [])) and res.get("graficos", 0) >= 1
    res["tabla_con_barra"] = any(b["display"] != "none" and b["ancho"] > 0 for b in res.get("barras_con_el_cursor_sobre_la_tabla", []))
    SALIDA_JSON.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
