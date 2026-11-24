"""F26: capturas y medidas de lo que cambió con la marca, el pie y la Cola agrupada. Requiere la página corriendo en localhost.

- Recortes de la marca (arriba a la izquierda de la barra lateral) (F30: solo el modo normal), a escala 2, y de su caja medida: ¿cabe en la barra? (``f26_marca_*.png``).
- Recorte del pie del Resumen (``f26_pie.png``) y su geometría (dos líneas de 12 px, color y ancho).
- Título de la pestaña del navegador y favicon declarado (``document.title`` y los ``<link rel=icon>``).
- C2: la Cola con «Agrupar por objeto» activado con un clic real (``f26_cola_agrupada.png``); no cambia el valor por defecto de la página.
Escribe ``docs/ep3/f26_marca.json``. Uso: .venv\\Scripts\\python scripts/ep3/f26_capturas_extra.py --puerto 8531
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

IMG = RAIZ / "images/ep3/pagina"
SALIDA = RAIZ / "docs/ep3/f26_marca.json"
JS_MARCA = """(() => { const r = e => { if (!e) return null; const b = e.getBoundingClientRect(); return {izquierda: Math.round(b.left), arriba: Math.round(b.top), derecha: Math.round(b.right), abajo: Math.round(b.bottom)}; };
  const barra = document.querySelector('[data-testid="stSidebar"]'), logo = document.querySelector('[data-testid="stSidebarLogo"]'), cab = document.querySelector('[data-testid="stSidebarHeader"]');
  return JSON.stringify({barra: r(barra), logo: r(logo), cabecera: r(cab), titulo: document.title, iconos: Array.from(document.querySelectorAll('link[rel~=icon]')).map(l => l.getAttribute('href').slice(0, 60)),
                         texto_alt: logo ? logo.getAttribute('alt') : null}); })()"""
JS_PIE = """(() => { const p = document.querySelector('.aud-pie'); if (!p) return null; const b = p.getBoundingClientRect(); const ps = Array.from(p.querySelectorAll('p')).map(x => { const cs = getComputedStyle(x);
  return {texto: x.textContent.slice(0, 50), fuente_px: parseFloat(cs.fontSize), color: cs.color, lineas: Math.round(x.getBoundingClientRect().height / parseFloat(cs.lineHeight))}; });
  return JSON.stringify({x: b.left, y: b.top + window.scrollY, w: b.width, h: b.height, parrafos: ps, ancho_ventana: window.innerWidth}); })()"""
JS_TOGGLE_AGRUPAR = """(() => { const l = Array.from(document.querySelectorAll('label')).find(x => x.textContent.includes('Agrupar por objeto')); if (!l) return null; const r = l.getBoundingClientRect(); return JSON.stringify({x: r.left + 18, y: r.top + r.height / 2}); })()"""


def recorte(nav: C.Navegador, ruta: Path, x: float, y: float, w: float, h: float, escala: float = 2.0) -> None:
    """Recorta una zona de la ventana actual a ``escala`` veces (con el factor de pixeles del navegador, no con ``clip.scale``, que desplaza el recorte)."""
    from io import BytesIO

    from PIL import Image

    nav.cmd("Emulation.setDeviceMetricsOverride", width=nav.ancho, height=nav.alto, deviceScaleFactor=escala, mobile=False)
    time.sleep(1.0)
    img = Image.open(BytesIO(base64.b64decode(nav.cmd("Page.captureScreenshot", format="png")["data"])))
    img.crop((int(x * escala), int(y * escala), int((x + w) * escala), int((y + h) * escala))).save(ruta)
    nav.cmd("Emulation.setDeviceMetricsOverride", width=nav.ancho, height=nav.alto, deviceScaleFactor=1, mobile=False)
    time.sleep(0.8)


def clic(nav: C.Navegador, x: float, y: float) -> None:
    for tipo in ("mouseMoved", "mousePressed", "mouseReleased"):
        nav.cmd("Input.dispatchMouseEvent", type=tipo, x=x, y=y, button="left", clickCount=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8512)
    ap.add_argument("--debug", type=int, default=9344)
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    res: dict = {}
    try:
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=768, deviceScaleFactor=1, mobile=False)
        nav.cmd("Page.navigate", url=C.url(a.puerto, "Resumen"))
        ok, _, motivo, _, _ = C.esperar(nav, "Resumen", 60.0, 2.0)
        if not ok:
            sys.exit(f"el Resumen no terminó de dibujarse: {motivo}")
        time.sleep(1.0)
        res["marca_normal"] = nav.js(JS_MARCA)
        nav.ancho, nav.alto = 1366, 768
        recorte(nav, IMG / "f26_marca_normal.png", 0, 0, 236, 72)
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=1500, deviceScaleFactor=1, mobile=False)
        time.sleep(1.2)
        pie = nav.js(JS_PIE)
        res["pie"] = pie
        nav.ancho, nav.alto = 1366, 1500
        recorte(nav, IMG / "f26_pie.png", pie["x"] - 4, pie["y"] - 6, pie["w"] + 8, pie["h"] + 14, 1.5)
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=768, deviceScaleFactor=1, mobile=False)
        time.sleep(1.0)
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=1250, deviceScaleFactor=1, mobile=False)
        nav.cmd("Page.navigate", url=C.url(a.puerto, "Cola de revisión"))
        ok, _, motivo, _, _ = C.esperar(nav, "Cola de revisión", 60.0, 2.0, C.CLAVE_PREVIA.get("Cola de revisión"))
        if not ok:
            sys.exit(f"la Cola no terminó de dibujarse: {motivo}")
        nav.js(C.JS_PESTANA)
        time.sleep(3.0)
        t = nav.js(JS_TOGGLE_AGRUPAR)
        clic(nav, t["x"], t["y"])
        time.sleep(5.0)
        nav.js(C.JS_PESTANA)
        time.sleep(2.5)
        (IMG / "f26_cola_agrupada.png").write_bytes(base64.b64decode(nav.cmd("Page.captureScreenshot", format="png")["data"]))
        res["cola_agrupada"] = {"archivo": "f26_cola_agrupada.png", "nota": "capturada con un clic real en «Agrupar por objeto»; el valor por defecto de la página no cambia"}
    finally:
        nav.cerrar()
    for k in ("marca_normal",):
        m = res[k]
        res[k] = {**m, "cabe_en_la_barra": m["logo"]["derecha"] <= m["barra"]["derecha"] - 4 and m["logo"]["izquierda"] >= 0 and m["logo"]["abajo"] <= m["cabecera"]["abajo"] + 1}
    SALIDA.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    main()
