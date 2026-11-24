"""F24: mide el Resumen en una ventana de EXACTAMENTE 1366 x 768 px, y comprueba que la primera pantalla muestre los indicadores, el titular y la lista de alertas (F29: la última fila de alerta
termina en 640 px o antes (un navegador real solo ofrece unos 650 px útiles).

Usa el mismo Chrome sin interfaz y la misma espera robusta que ``capturar_pagina.py`` (no instala nada). Escribe ``docs/ep3/f24_fold_resumen.json`` y las imágenes
``images/ep3/pagina/01_resumen_1366x768.png`` (solo lo que cabe en la ventana). Requiere la página corriendo en localhost.
Uso: .venv\\Scripts\\python scripts/ep3/f24_medir_resumen.py --puerto 8531
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

LIMITE_PX = 640
JS_MEDIDAS = """(() => {
  const r = e => { if (!e) return null; const b = e.getBoundingClientRect(); return {arriba: b.top, abajo: b.bottom, izquierda: b.left, derecha: b.right}; };
  const q = s => r(document.querySelector(s));
  const filas = Array.from(document.querySelectorAll('[class*="st-key-celda_"], [class*="st-key-celdasel_"]')).map(r);
  const titular = document.querySelector('.aud-titular');
  return JSON.stringify({kpis: q('.aud-kpis'), titular: q('.aud-titular'), subtitulo_titular: r(titular ? titular.parentElement.querySelector('.aud-descripcion') : null), filas_de_alerta: filas,
                         ultima_fila: filas.length ? filas[filas.length - 1] : null, anillo: q('.aud-anillo-bloque .aud-anillo'), leyenda: q('.aud-anillo-bloque .aud-leyenda'), panel: q('.st-key-panel_principal'),
                         lineas_titular: titular ? Math.round(titular.getBoundingClientRect().height / parseFloat(getComputedStyle(titular).lineHeight)) : null, tamano_titular: titular ? getComputedStyle(titular).fontSize : null,
                         alto_ventana: window.innerHeight, ancho_ventana: window.innerWidth, scroll_horizontal_px: document.documentElement.scrollWidth - window.innerWidth,
                         barra_lateral_desborde_px: (() => { const s = document.querySelector('[data-testid="stSidebarContent"]'); return s ? s.scrollHeight - s.clientHeight : null; })()});
})()"""


def medir(nav: C.Navegador, maximo: float) -> dict:
    ok, _, motivo, _, _ = C.esperar(nav, "Resumen", maximo, 2.0)
    if not ok:
        sys.exit(f"el Resumen no terminó de dibujarse: {motivo}")
    time.sleep(1.0)
    m = nav.js(JS_MEDIDAS)
    alto = m["alto_ventana"]

    def entra(k: str) -> bool:
        return bool(m.get(k)) and m[k]["arriba"] >= 0 and m[k]["abajo"] <= alto

    return {"modo": "normal", "viewport": [m["ancho_ventana"], alto], "limite_px": LIMITE_PX, "indicadores": m["kpis"], "titular": m["titular"], "filas_de_alerta": m["filas_de_alerta"],
            "ultima_fila_de_alerta": m["ultima_fila"], "panel_principal": m["panel"], "anillo": m["anillo"], "leyenda_anillo": m["leyenda"], "lineas_del_titular": m["lineas_titular"], "tamano_del_titular": m["tamano_titular"],
            "indicadores_visibles": entra("kpis"), "titular_visible": entra("titular"), "lista_de_alertas_visible": bool(m["ultima_fila"]) and m["ultima_fila"]["abajo"] <= alto,
            "panel_termina_en_px": round(m["ultima_fila"]["abajo"]) if m["ultima_fila"] else None, "panel_dentro_del_limite": bool(m["ultima_fila"]) and m["ultima_fila"]["abajo"] <= LIMITE_PX,
            "scroll_horizontal_px": m["scroll_horizontal_px"], "barra_lateral_desborde_px": m["barra_lateral_desborde_px"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8512)
    ap.add_argument("--debug", type=int, default=9334)
    ap.add_argument("--maximo", type=float, default=60.0)
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    salida: dict = {}
    try:
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=768, deviceScaleFactor=1, mobile=False)
        nav.cmd("Page.navigate", url=C.url(a.puerto, "Resumen"))
        for imagen in ("01_resumen_1366x768.png",):
            salida["normal"] = medir(nav, a.maximo)
            png = nav.cmd("Page.captureScreenshot", format="png", captureBeyondViewport=False)["data"]
            (RAIZ / "images/ep3/pagina" / imagen).write_bytes(base64.b64decode(png))
    finally:
        nav.cerrar()
    (RAIZ / "docs/ep3/f24_fold_resumen.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, v in salida.items():
        print(f"{k:13s} lista de alertas termina en {v['panel_termina_en_px']} px (límite {LIMITE_PX}); titular {v['lineas_del_titular']} líneas de {v['tamano_del_titular']}; "
              f"indicadores visibles: {v['indicadores_visibles']}; titular visible: {v['titular_visible']}; lista de alertas visible: {v['lista_de_alertas_visible']}; desborde de la barra lateral {v['barra_lateral_desborde_px']} px")
    if not all(v["panel_dentro_del_limite"] for v in salida.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
