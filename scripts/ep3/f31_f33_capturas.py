"""F31 a F33: las 16 capturas que se envían a revisión (Auditoría de cámaras, Cola de revisión y Explica una caja) a 1366 px, cada una con el estado que su nombre dice.

Usa el navegador sin interfaz de ``capturar_pagina.py`` (Chrome o Edge ya instalado, protocolo CDP; no instala nada y no hace conexiones externas). Con la página corriendo en localhost.
Cada captura se recorta a la región que interesa (ancho completo de 1366 px) y solo se guarda si la página terminó de dibujarse. Escribe
``images/ep3/pagina/para_revision_f31_f33/<nombre>.png`` y ``docs/ep3/f31_f33_capturas.json`` (qué se capturó, el alto recortado y si estaba lista).
Uso: .venv\\Scripts\\python scripts/ep3/f31_f33_capturas.py --puerto 8531
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
sys.path.insert(0, str(RAIZ / "src"))
import capturar_pagina as C  # noqa: E402
from waymo_evaluacion.ep3.app_logica import AUD_QUE_ES, COLA_SUPUESTOS, COLA_TAB_CURVA, COLA_TAB_LISTA  # noqa: E402

DESTINO = RAIZ / "images/ep3/pagina/para_revision_f31_f33"
SALIDA = RAIZ / "docs/ep3/f31_f33_capturas.json"
ANCHO = 1366
ALTO_MAXIMO_RECORTE = 1500

JS_RECT = """((sels, desdeArriba) => {
  let top = null, bottom = null;
  for (const s of sels) {
    let els = [];
    if (s.startsWith('details:')) { els = Array.from(document.querySelectorAll('details')).filter(d => d.querySelector('summary') && d.querySelector('summary').textContent.includes(s.slice(8))); }
    else if (s.startsWith('tabpanel')) { els = Array.from(document.querySelectorAll('[role=tabpanel]')).filter(p => p.getBoundingClientRect().height > 0); }
    else els = Array.from(document.querySelectorAll(s));
    for (const e of els) { const r = e.getBoundingClientRect(); if (r.height <= 0) continue; top = top === null ? r.top : Math.min(top, r.top); bottom = bottom === null ? r.bottom : Math.max(bottom, r.bottom); }
  }
  if (top === null) return null;
  const sy = window.scrollY || 0;
  return JSON.stringify({top: top + sy, bottom: bottom + sy, desdeArriba});
})"""
JS_CLIC_TEXTO = """((sel, texto, exacto) => { const es = Array.from(document.querySelectorAll(sel)).filter(e => (exacto ? e.textContent.trim() === texto : e.textContent.includes(texto)) && e.getBoundingClientRect().height > 0); const e = es[0]; if (!e) return false; e.scrollIntoView({block: 'center'}); e.click(); return true; })"""
JS_CENTRO = """((sel, texto, n) => { const es = Array.from(document.querySelectorAll(sel)).filter(e => !texto || e.textContent.includes(texto)); const e = es[n || 0]; if (!e) return null; e.scrollIntoView({block: 'center'}); const r = e.getBoundingClientRect(); return JSON.stringify({x: r.left + r.width / 2, y: r.top + r.height / 2, l: r.left, t: r.top, w: r.width, h: r.height}); })"""


def clic(nav: C.Navegador, x: float, y: float) -> None:
    for tipo in ("mouseMoved", "mousePressed", "mouseReleased"):
        nav.cmd("Input.dispatchMouseEvent", type=tipo, x=x, y=y, button="left", clickCount=1)


def tecla(nav: C.Navegador, key: str, code: str, vk: int) -> None:
    for tipo in ("keyDown", "keyUp"):
        nav.cmd("Input.dispatchKeyEvent", type=tipo, key=key, code=code, windowsVirtualKeyCode=vk)


def estable(nav: C.Navegador, seccion: str, clave: dict, espera: float = 1.2) -> dict:
    """Espera a que la página termine, ajusta el viewport al alto real del contenido y vuelve a esperar."""
    time.sleep(espera)
    ok, e, motivo, _, _ = C.esperar(nav, seccion, 60.0, 2.0, clave)
    if not ok:
        raise RuntimeError(f"{seccion}: la página no terminó de dibujarse ({motivo})")
    alto = int(min(max(e.get("alto", 900) + 60, 700), 3600))
    nav.cmd("Emulation.setDeviceMetricsOverride", width=ANCHO, height=alto, deviceScaleFactor=1, mobile=False)
    ok, e, motivo, _, _ = C.esperar(nav, seccion, 60.0, 2.0, clave)
    if not ok:
        raise RuntimeError(f"{seccion}: la página no se estabilizó ({motivo})")
    time.sleep(0.6)
    return e


def abrir(nav: C.Navegador, puerto: int, seccion: str, clave: dict | None = None) -> dict:
    nav.cmd("Emulation.setDeviceMetricsOverride", width=ANCHO, height=900, deviceScaleFactor=1, mobile=False)
    nav.cmd("Page.navigate", url=C.url(puerto, seccion))
    return estable(nav, seccion, clave or C.CLAVE[seccion], 0.5)


def foto(nav: C.Navegador, nombre: str, selectores: list[str], desde_arriba: bool = False, extra_abajo: int = 0, pad: int = 16, alto_max: int = ALTO_MAXIMO_RECORTE) -> dict:
    nav.js("(() => { window.scrollTo(0, 0); document.querySelectorAll('*').forEach(e => { if (e.scrollLeft) e.scrollLeft = 0; }); return true; })()")        # un foco o un clic pueden haber desplazado el marco a un lado
    time.sleep(0.4)
    r = nav.js(f"({JS_RECT})({json.dumps(selectores)}, {json.dumps(desde_arriba)})")
    if not r:
        raise RuntimeError(f"{nombre}: no encontré {selectores}")
    top = 0 if desde_arriba else max(0, r["top"] - pad)
    bottom = r["bottom"] + pad + extra_abajo
    alto = int(min(bottom - top, alto_max))
    clip = {"x": 0, "y": top, "width": ANCHO, "height": alto, "scale": 1}
    datos = nav.cmd("Page.captureScreenshot", format="png", clip=clip)["data"]
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / f"{nombre}.png").write_bytes(base64.b64decode(datos))
    print(f"OK   {nombre:34s} {ANCHO} x {alto} px")
    return {"archivo": f"{nombre}.png", "ancho": ANCHO, "alto": alto, "selectores": selectores}


def clic_fila_tabla(nav: C.Navegador, contenedor: str, fila: int) -> None:
    """Un clic real en la fila ``fila`` (0 = primera) de la tabla de ``contenedor``: la tabla es un lienzo, así que se cliquea en la columna de selección."""
    c = nav.js(f"({JS_CENTRO})({json.dumps(contenedor + ' [data-testid=stDataFrame]')}, '', 0)")
    if not c:
        raise RuntimeError(f"no encontré la tabla de {contenedor}")
    clic(nav, c["l"] + 19, c["t"] + 50 + 35 * fila)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8531)
    ap.add_argument("--debug", type=int, default=9334)
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    hechas: list[dict] = []
    try:
        # ---------------------------------------------------------------------------------------- F31: Auditoría de cámaras
        clave_a = C.CLAVE["Auditoría de cámaras"]
        abrir(nav, a.puerto, "Auditoría de cámaras")
        hechas.append(foto(nav, "f31_01_resumen_franja", [".aud-kpi"], desde_arriba=True, pad=24))
        hechas.append(foto(nav, "f31_02_celdas_marcadas", [".st-key-aud_celdas"]))
        clic_fila_tabla(nav, ".st-key-aud_celdas", 1)
        estable(nav, "Auditoría de cámaras", clave_a, 1.5)
        hechas.append(foto(nav, "f31_03_fila_seleccionada", [".st-key-aud_celdas", ".st-key-aud_anillo"]))
        hechas.append(foto(nav, "f31_04_mapa_calor", [".st-key-aud_mapa"]))
        nav.js(f"({JS_CLIC_TEXTO})('summary', {json.dumps(AUD_QUE_ES)}, false)")
        estable(nav, "Auditoría de cámaras", clave_a, 1.0)
        hechas.append(foto(nav, "f31_05_que_es_un_hueco", ["details:" + AUD_QUE_ES]))
        # ---------------------------------------------------------------------------------------- F32: Cola de revisión
        clave_c = C.CLAVE_COLA_SIN_FILA
        abrir(nav, a.puerto, "Cola de revisión", C.CLAVE_PREVIA["Cola de revisión"])
        nav.js(C.JS_PESTANA)
        estable(nav, "Cola de revisión", clave_c, 1.5)
        hechas.append(foto(nav, "f32_01_cola_de_cajas", [".st-key-cola_lista"], desde_arriba=True))
        hechas.append(foto(nav, "f32_03_filtros", [".st-key-plan_revision", ".st-key-cola_lista"], alto_max=620))
        clic_fila_tabla(nav, ".st-key-cola_lista", 0)
        estable(nav, "Cola de revisión", C.CLAVE["Cola de revisión"], 1.5)
        hechas.append(foto(nav, "f32_02_fila_seleccionada", [".st-key-cola_lista", ".st-key-panel_detalle"], alto_max=900))
        # ciclista: filtro de clase + primera fila (el panel de detalle trae la advertencia de ciclista)
        nav.js(f"({JS_CLIC_TEXTO})('[role=tab]', {json.dumps(COLA_TAB_LISTA)}, false)")
        centro = nav.js(f"({JS_CENTRO})('.st-key-filtro_clase input', '', 0)")
        if centro:
            clic(nav, centro["x"], centro["y"])
            time.sleep(0.8)
            opcion = nav.js(f"({JS_CENTRO})('[role=option]', 'Ciclista', 0)")
            if opcion:
                clic(nav, opcion["x"], opcion["y"])
                time.sleep(0.5)
                tecla(nav, "Escape", "Escape", 27)                                                    # cierra la lista de opciones para que el siguiente clic llegue a la tabla
        estable(nav, "Cola de revisión", clave_c, 2.0)
        for _intento in range(3):
            clic_fila_tabla(nav, ".st-key-cola_lista", 0)
            time.sleep(2.0)
            if "Explicar esta caja" in str(nav.js("document.body.innerText")):
                break
        estable(nav, "Cola de revisión", C.CLAVE["Cola de revisión"], 1.5)
        hechas.append(foto(nav, "f32_05_ciclista", [".st-key-cola_lista", ".st-key-panel_detalle"], alto_max=900))
        # curva y supuestos
        abrir(nav, a.puerto, "Cola de revisión", C.CLAVE_PREVIA["Cola de revisión"])
        nav.js(f"({JS_CLIC_TEXTO})('[role=tab]', {json.dumps(COLA_TAB_CURVA)}, false)")
        estable(nav, "Cola de revisión", {"texto": "Supuestos y confiabilidad", "conteos": [("[role=tab]", 2), (".vega-embed", 1)]}, 2.0)
        hechas.append(foto(nav, "f32_04_curva", ["tabpanel"], alto_max=1100))
        nav.js(f"({JS_CLIC_TEXTO})('summary', {json.dumps(COLA_SUPUESTOS)}, false)")
        estable(nav, "Cola de revisión", {"texto": "Supuestos y confiabilidad", "conteos": [("[role=tab]", 2)]}, 1.0)
        hechas.append(foto(nav, "f32_06_supuestos", ["details:" + COLA_SUPUESTOS]))
        # ---------------------------------------------------------------------------------------- F33: Explica una caja
        clave_e = C.CLAVE["Explica una caja"]
        for nombre, pildora in (("f33_01_cercana_y_densa", "Caja cercana y densa"), ("f33_02_lejana", "Caja lejana con pocos puntos"), ("f33_03_ciclista", "Ciclista lejano")):
            abrir(nav, a.puerto, "Explica una caja")
            nav.js(f"({JS_CLIC_TEXTO})('button', {json.dumps(pildora)}, true)")
            estable(nav, "Explica una caja", clave_e, 1.5)
            hechas.append(foto(nav, nombre, [".st-key-ex_curva"], desde_arriba=True))
        # cero puntos: el control que decide, al mínimo (Inicio en el teclado)
        abrir(nav, a.puerto, "Explica una caja")
        if not nav.js("(() => { const i = document.querySelector('[data-testid=stSlider] input[type=range]'); if (!i) return false; i.focus(); return document.activeElement === i; })()"):
            raise RuntimeError("no encontré el control de puntos del sensor superior")
        tecla(nav, "Home", "Home", 36)
        estable(nav, "Explica una caja", clave_e, 1.5)
        texto0 = nav.js("document.body.innerText")
        if "Está entre las primeras" not in (texto0 or ""):
            for _ in range(70):                                                           # respaldo: flecha izquierda hasta el mínimo
                tecla(nav, "ArrowLeft", "ArrowLeft", 37)
            estable(nav, "Explica una caja", clave_e, 2.0)
        hechas.append(foto(nav, "f33_04_cero_puntos", [".st-key-ex_curva"], desde_arriba=True))
        # desde la cola: fila elegida y «Explicar esta caja →»
        abrir(nav, a.puerto, "Cola de revisión", C.CLAVE_PREVIA["Cola de revisión"])
        nav.js(C.JS_PESTANA)
        estable(nav, "Cola de revisión", clave_c, 1.5)
        clic_fila_tabla(nav, ".st-key-cola_lista", 2)
        estable(nav, "Cola de revisión", C.CLAVE["Cola de revisión"], 1.5)
        boton = nav.js(f"({JS_CENTRO})('button', 'Explicar esta caja', 0)")
        if not boton:
            raise RuntimeError("no encontré «Explicar esta caja →»")
        clic(nav, boton["x"], boton["y"])
        t0 = time.time()
        while time.time() - t0 < 40 and "/explica" not in str(nav.js("location.pathname")):
            time.sleep(0.4)
        estable(nav, "Explica una caja", clave_e, 2.0)
        hechas.append(foto(nav, "f33_05_desde_la_cola", [".st-key-ex_curva"], desde_arriba=True))
    finally:
        nav.cerrar()
    SALIDA.write_text(json.dumps({"ancho": ANCHO, "capturas": hechas}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(hechas)} capturas en {DESTINO}")


if __name__ == "__main__":
    main()
