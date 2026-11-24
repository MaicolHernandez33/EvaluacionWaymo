"""F38, Paso 7.4: renderiza ``README.md`` a HTML (markdown-it, con tablas y bloques ``<details>`` abiertos como en GitHub al expandirlos no hace falta) y guarda 3 capturas: la parte superior, la sección 8.2 y la tabla
del mapa de la pauta. Usa el navegador sin interfaz de ``capturar_pagina.py`` (Chrome o Edge ya instalado); no hace conexiones externas.
Uso: .venv\Scripts\python scripts/ep3/f38_capturas_readme.py --destino images/ep3/readme/para_revision_f38
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import tempfile
import time
from pathlib import Path

from markdown_it import MarkdownIt

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capturar_pagina as C  # noqa: E402

CSS = ("body{font:15px/1.5 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;max-width:1000px;margin:24px auto;padding:0 24px;color:#1f2328}h1,h2,h3{border-bottom:1px solid #d8dee4;padding-bottom:.3em}"
       "table{border-collapse:collapse;margin:12px 0;display:block;overflow:auto}th,td{border:1px solid #d0d7de;padding:5px 10px;vertical-align:top}th{background:#f6f8fa}tr:nth-child(2n){background:#f6f8fa}"
       "code{background:#eff1f3;padding:.1em .3em;border-radius:4px;font-size:90%}pre{background:#f6f8fa;padding:12px;overflow:auto}blockquote{border-left:4px solid #d0d7de;margin:0;padding:0 1em;color:#59636e}img{max-width:100%}"
       "details{border:1px solid #d0d7de;border-radius:6px;padding:6px 12px;margin:10px 0}summary{cursor:pointer;font-weight:600}")

JS_RECT = """((sel, texto, hasta) => { const els = Array.from(document.querySelectorAll(sel)).filter(e => e.textContent.includes(texto)); const e = els[0]; if (!e) return null;
  const r = e.getBoundingClientRect(); const top = r.top + window.scrollY; let bottom = r.bottom + window.scrollY;
  if (hasta) { const f = Array.from(document.querySelectorAll(hasta.sel)).filter(x => x.textContent.includes(hasta.texto) && (x.getBoundingClientRect().top + window.scrollY) > top)[0]; if (f) bottom = f.getBoundingClientRect().top + window.scrollY; }
  return JSON.stringify({top: top, bottom: bottom}); })"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", type=Path, required=True)
    ap.add_argument("--debug", type=int, default=9397)
    a = ap.parse_args()
    html = MarkdownIt("commonmark", {"html": True}).enable("table").render((RAIZ / "README.md").read_text(encoding="utf-8"))
    base = RAIZ.as_uri() + "/"
    with tempfile.TemporaryDirectory(prefix="readme_html_") as tmp:
        pagina = Path(tmp) / "README.html"
        pagina.write_text(f'<!doctype html><html><head><meta charset="utf-8"><base href="{base}"><style>{CSS}</style></head><body>{html}</body></html>', encoding="utf-8")
        nav = C.Navegador(a.debug)
        try:
            nav.cmd("Emulation.setDeviceMetricsOverride", width=1100, height=1000, deviceScaleFactor=1, mobile=False)
            nav.cmd("Page.navigate", url=pagina.as_uri())
            time.sleep(3)
            a.destino.mkdir(parents=True, exist_ok=True)
            cortes = {"readme_01_parte_superior": None,
                      "readme_02_seccion_8_2_ensambles": ("h3", "8.2 Técnicas de ensamble", {"sel": "h3", "texto": "8.3 Capacidad"}),
                      "readme_03_mapa_de_la_pauta": ("p", "Mapa de la pauta", {"sel": "p", "texto": "Índice:"})}
            for nombre, cfg in cortes.items():
                if cfg is None:
                    y0, y1 = 0, 1250
                else:
                    r = nav.js(f"({JS_RECT})({json.dumps(cfg[0])}, {json.dumps(cfg[1])}, {json.dumps(cfg[2])})")
                    if not r:
                        raise RuntimeError(f"no encontré {cfg[1]}")
                    y0, y1 = max(0, r["top"] - 10), r["bottom"] + 10
                alto = int(min(y1 - y0, 1900))
                nav.cmd("Emulation.setDeviceMetricsOverride", width=1100, height=int(y1) + 60, deviceScaleFactor=1, mobile=False)
                time.sleep(0.6)
                datos = nav.cmd("Page.captureScreenshot", format="png", clip={"x": 0, "y": y0, "width": 1100, "height": alto, "scale": 1})["data"]
                (a.destino / f"{nombre}.png").write_bytes(base64.b64decode(datos))
                print(f"OK {nombre} 1100 x {alto}")
        finally:
            nav.cerrar()


if __name__ == "__main__":
    main()
