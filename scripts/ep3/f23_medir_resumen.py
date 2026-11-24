"""F23: mide el Resumen en una ventana de EXACTAMENTE 1366 x 768 px (sin ajustar el alto al contenido) y comprueba que el anillo de cámaras y la afirmación se ven completos sin desplazarse.

Usa el mismo Chrome sin interfaz y la misma espera robusta que ``capturar_pagina.py`` (no instala nada). Escribe ``docs/ep3/f23_fold_resumen.json`` y la imagen ``images/ep3/pagina/01_resumen_1366x768.png``
(solo lo que cabe en la ventana, sin desplazamiento). Requiere la página corriendo en localhost.
Uso: .venv\\Scripts\\python scripts/ep3/f23_medir_resumen.py --puerto 8531
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

JS_MEDIDAS = """(() => {
  const r = s => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return {arriba: b.top, abajo: b.bottom, izquierda: b.left, derecha: b.right}; };
  const scroller = document.querySelector('[data-testid="stMain"]') || document.documentElement;
  return JSON.stringify({anillo: r('.aud-anillo-bloque .aud-anillo'), leyenda: r('.aud-anillo-bloque .aud-leyenda'), afirmacion: r('.aud-afirmacion'), panel: r('.st-key-panel_principal'),
                         alto_ventana: window.innerHeight, ancho_ventana: window.innerWidth, scroll_horizontal_px: document.documentElement.scrollWidth - window.innerWidth,
                         alto_contenido: scroller.scrollHeight, fuente_afirmacion: (() => { const e = document.querySelector('.aud-afirmacion'); return e ? getComputedStyle(e).fontFamily + ' / ' + getComputedStyle(e).fontSize : null; })()});
})()"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8512)
    ap.add_argument("--debug", type=int, default=9334)
    ap.add_argument("--maximo", type=float, default=60.0)
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    try:
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=768, deviceScaleFactor=1, mobile=False)
        nav.cmd("Page.navigate", url=C.url(a.puerto, "Resumen"))
        ok, estado, motivo, _, _ = C.esperar(nav, "Resumen", a.maximo, 2.0)
        if not ok:
            sys.exit(f"el Resumen no terminó de dibujarse: {motivo}")
        time.sleep(1.0)
        m = nav.js(JS_MEDIDAS)
        alto = m["alto_ventana"]
        completo = lambda k: bool(m.get(k)) and m[k]["arriba"] >= 0 and m[k]["abajo"] <= alto           # noqa: E731
        salida = {"viewport": [m["ancho_ventana"], alto], "anillo": m["anillo"], "leyenda_anillo": m["leyenda"], "afirmacion": m["afirmacion"], "panel_principal": m["panel"],
                  "anillo_visible_completo": completo("anillo") and completo("leyenda"), "afirmacion_visible_completa": completo("afirmacion"), "panel_visible_completo": completo("panel"),
                  "scroll_horizontal_px": m["scroll_horizontal_px"], "alto_del_contenido": m["alto_contenido"], "fuente_de_la_afirmacion": m["fuente_afirmacion"]}
        (RAIZ / "docs/ep3/f23_fold_resumen.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
        png = nav.cmd("Page.captureScreenshot", format="png", captureBeyondViewport=False)["data"]
        (RAIZ / "images/ep3/pagina/01_resumen_1366x768.png").write_bytes(base64.b64decode(png))
        print(json.dumps(salida, indent=1, ensure_ascii=False))
        if not (salida["anillo_visible_completo"] and salida["afirmacion_visible_completa"]):
            sys.exit(1)
    finally:
        nav.cerrar()


if __name__ == "__main__":
    main()
