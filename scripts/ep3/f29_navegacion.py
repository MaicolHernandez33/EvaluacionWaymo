"""F29: comprueba en el navegador real (Chrome sin interfaz, protocolo CDP; no instala nada) que los botones del Resumen navegan CON el contexto elegido.

- «Auditar» de la primera fila de alertas abre «Auditoría de cámaras» con ese segmento y esa cámara ya elegidos y su celda resaltada en el mapa.
- Elegir otra fila de alertas cambia el segmento del anillo y «Auditar» de esa fila abre la Auditoría con la otra celda.
- «Abrir» de la primera fila de la cola abre «Explica una caja» con los controles puestos con los valores de esa caja y el aviso «Valores cargados desde el Resumen» (F33).
Escribe ``docs/ep3/f29_navegacion.json`` y las imágenes ``images/ep3/pagina/f29_destino_auditar.png`` y ``f29_destino_abrir.png``. Requiere la página corriendo en localhost.
Uso: .venv\\Scripts\\python scripts/ep3/f29_navegacion.py --puerto 8531
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
SALIDA = RAIZ / "docs/ep3/f29_navegacion.json"
JS_BOTON = """((texto, n) => { const bs = Array.from(document.querySelectorAll('button')).filter(b => b.textContent.trim() === texto); const b = bs[n]; if (!b) return null; b.scrollIntoView({block: 'center'}); const r = b.getBoundingClientRect();
  return JSON.stringify({x: r.left + r.width / 2, y: r.top + r.height / 2, hay: bs.length}); })"""
JS_FILA = """((n) => { const bs = Array.from(document.querySelectorAll('[class*="st-key-sel_celda_"] button, button')).filter(b => /Segmento .+ · cámara \\d/.test(b.textContent.trim())); const b = bs[n]; if (!b) return null;
  b.scrollIntoView({block: 'center'}); const r = b.getBoundingClientRect(); return JSON.stringify({x: r.left + 40, y: r.top + r.height / 2, texto: b.textContent.trim(), hay: bs.length}); })"""
JS_ESTADO = """(() => { const t = document.body.innerText; const m = t.match(/Cámaras del segmento ([^\\n]+)/); const c = t.match(/Celda resaltada en el mapa:[^\\n]+/); const k = t.match(/Valores cargados desde el Resumen[^\\n]+/);
  const sel = Array.from(document.querySelectorAll('[data-testid="stSelectbox"]')).map(s => s.innerText.replace(/\\n/g, ' ').trim());
  return JSON.stringify({ruta: location.pathname, anillo: m ? m[1] : null, celda: c ? c[0] : null, caja: k ? k[0] : null, selectores: sel.slice(0, 6), titulo: (document.querySelector('h1') || {}).innerText}); })()"""


def clic(nav: C.Navegador, x: float, y: float) -> None:
    for tipo in ("mouseMoved", "mousePressed", "mouseReleased"):
        nav.cmd("Input.dispatchMouseEvent", type=tipo, x=x, y=y, button="left", clickCount=1)


def esperar_ruta(nav: C.Navegador, fragmento: str, maximo: float = 40.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < maximo:
        ruta = nav.js("location.pathname")
        if isinstance(ruta, str) and fragmento in ruta:
            time.sleep(4.0)
            return True
        time.sleep(0.4)
    return False


def foto(nav: C.Navegador, nombre: str) -> None:
    (IMG / nombre).write_bytes(base64.b64decode(nav.cmd("Page.captureScreenshot", format="png")["data"]))


def ir_al_resumen(nav: C.Navegador, puerto: int) -> None:
    nav.cmd("Page.navigate", url=C.url(puerto, "Resumen"))
    ok, _, motivo, _, _ = C.esperar(nav, "Resumen", 60.0, 2.0)
    if not ok:
        sys.exit(f"el Resumen no terminó de dibujarse: {motivo}")
    time.sleep(1.5)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8531)
    ap.add_argument("--debug", type=int, default=9352)
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    res: dict = {}
    try:
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=900, deviceScaleFactor=1, mobile=False)
        ir_al_resumen(nav, a.puerto)
        fila0 = nav.js(f"({JS_FILA})(0)")
        res["fila_0"] = fila0["texto"]
        res["estado_inicial"] = nav.js(JS_ESTADO)
        # 1) «Auditar» de la primera fila
        b = nav.js(f"({JS_BOTON})('Auditar', 0)")
        clic(nav, b["x"], b["y"])
        res["auditar_0_llego"] = esperar_ruta(nav, "auditoria")
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=1200, deviceScaleFactor=1, mobile=False)
        time.sleep(3.0)
        res["auditar_0"] = nav.js(JS_ESTADO)
        foto(nav, "f29_destino_auditar.png")
        # 2) elegir la otra fila y «Auditar»
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=900, deviceScaleFactor=1, mobile=False)
        ir_al_resumen(nav, a.puerto)
        otra = nav.js(f"({JS_FILA})(1)")
        res["fila_1"] = otra["texto"] if otra else None
        if otra:
            clic(nav, otra["x"], otra["y"])
            time.sleep(4.0)
            res["anillo_tras_elegir_fila_1"] = nav.js(JS_ESTADO)["anillo"]
            b = nav.js(f"({JS_BOTON})('Auditar', 1)")
            clic(nav, b["x"], b["y"])
            res["auditar_1_llego"] = esperar_ruta(nav, "auditoria")
            res["auditar_1"] = nav.js(JS_ESTADO)
        # 3) «Abrir» de la primera fila de la cola
        ir_al_resumen(nav, a.puerto)
        b = nav.js(f"({JS_BOTON})('Abrir', 0)")
        clic(nav, b["x"], b["y"])
        res["abrir_0_llego"] = esperar_ruta(nav, "explica")
        res["abrir_0"] = nav.js(JS_ESTADO)
        foto(nav, "f29_destino_abrir.png")
    finally:
        nav.cerrar()
    ok = bool(res.get("auditar_0_llego") and res["auditar_0"].get("celda") and res.get("abrir_0_llego") and res["abrir_0"].get("caja"))
    res["conclusion"] = "los botones navegan con el contexto elegido" if ok else "ALGÚN BOTÓN NO NAVEGÓ CON SU CONTEXTO"
    SALIDA.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1)[:2600])
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
