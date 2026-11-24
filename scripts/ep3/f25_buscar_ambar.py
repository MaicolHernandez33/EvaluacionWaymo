"""F25: busca el ámbar de interfaz (#F5B73B) y los colores de sus antiguos fondo y borde en el DOM REAL de las 8 vistas (estilos calculados: color, fondo, bordes, y los pseudo-elementos ::before y ::after).

Criterio de F25: el ámbar aparece solo en el punto de «Ciclistas: regla poco confiable» (y en el punto del aviso de ciclista de la Cola y de Explica una caja, que es la misma advertencia).
Escribe ``docs/ep3/f25_ambar_en_el_dom.json``. Requiere la página corriendo en localhost.
Uso: .venv\\Scripts\\python scripts/ep3/f25_buscar_ambar.py --puerto 8531
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capturar_pagina as C  # noqa: E402

SALIDA = RAIZ / "docs/ep3/f25_ambar_en_el_dom.json"
BUSCADOS = {"rgb(245, 183, 59)": "ámbar #F5B73B", "rgb(42, 33, 16)": "antiguo fondo ámbar #2A2110", "rgb(107, 83, 22)": "antiguo borde ámbar #6B5316", "rgb(58, 46, 18)": "antiguo hover ámbar #3A2E12"}
JS = """((buscados) => { const hallazgos = []; const props = ['color', 'backgroundColor', 'borderTopColor', 'borderRightColor', 'borderBottomColor', 'borderLeftColor', 'outlineColor', 'fill', 'stroke'];
  const desc = e => e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ').filter(c => c.startsWith('aud-') || c.startsWith('st-key')).join('.') : '') + ' «' + (e.textContent || '').trim().slice(0, 30) + '»';
  for (const e of document.querySelectorAll('body *')) { for (const pseudo of [null, '::before', '::after']) { const cs = getComputedStyle(e, pseudo);
      if (pseudo && cs.content === 'none') continue; for (const p of props) { const v = cs[p]; if (buscados[v]) hallazgos.push({elemento: desc(e), pseudo: pseudo || '', propiedad: p, color: buscados[v]}); } } }
  return JSON.stringify(hallazgos); })(%s)"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8512)
    ap.add_argument("--debug", type=int, default=9343)
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    vistas = []
    try:
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=900, deviceScaleFactor=1, mobile=False)
        for seccion in C.SECCIONES:
            nav.cmd("Page.navigate", url=C.url(a.puerto, seccion))
            ok, _, motivo, _, _ = C.esperar(nav, seccion, 60.0, 2.0, C.CLAVE_PREVIA.get(seccion))
            time.sleep(0.5)
            hallazgos = nav.js(JS % json.dumps(BUSCADOS)) if ok else None
            vistas.append({"vista": seccion, "completa": ok, "motivo": motivo, "hallazgos": hallazgos})
    finally:
        nav.cerrar()
    todos = [h for v in vistas for h in (v["hallazgos"] or [])]
    antiguos = [h for h in todos if h["color"] != "ámbar #F5B73B"]
    ambar = [dict(vista=v["vista"], **h) for v in vistas for h in (v["hallazgos"] or []) if h["color"] == "ámbar #F5B73B"]
    res = {"vistas": [{"vista": v["vista"], "completa": v["completa"], "hallazgos": len(v["hallazgos"] or [])} for v in vistas], "ambar": ambar, "antiguos_fondo_borde_hover": antiguos,
           "solo_en_puntos_de_ciclistas": all(h["pseudo"] == "::before" or h["propiedad"] == "backgroundColor" for h in ambar) and all("«Ciclista" in h["elemento"] or h["elemento"].startswith("span.aud-punto") or "aud-aviso" in h["elemento"] for h in ambar)}
    SALIDA.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
