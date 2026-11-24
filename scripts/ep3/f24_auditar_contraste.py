"""F24: mide el contraste REAL del texto de la página, no solo el de los tokens.

Para cada vista (las 8 secciones, las 6 pestañas de Validación y las dos de la Cola) abre la página en Chrome sin interfaz (el mismo ``capturar_pagina.py``, sin instalar nada) y:

1. **DOM**: para cada texto visible calcula su color efectivo (color, opacidad propia y de los ancestros) y su fondo (se apilan los fondos de los ancestros) y la razón WCAG. Incluye el texto de los
   gráficos (SVG). Lista todo lo que queda por debajo de 4,5:1. El texto de un ``st.dataframe`` se dibuja en un canvas y no entra en esta medición.
2. **Píxeles**: de las notas pequeñas (``st.caption``, la nota del empate, las notas de las cifras) recorta la captura, toma el color de fondo más frecuente y el píxel de texto más alejado de él, y calcula la razón.
   Es una estimación (el suavizado de bordes mezcla colores), pero contrasta lo que dice el CSS con lo que se ve.

Escribe ``docs/ep3/f24_contraste.json``. Requiere la página corriendo en localhost.
Uso: .venv\\Scripts\\python scripts/ep3/f24_auditar_contraste.py --puerto 8531
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import time
from collections import Counter
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capturar_pagina as C  # noqa: E402

UMBRAL = 4.5
JS_DOM = """(() => {
  const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', {willReadFrequently: true});
  const rgba = (c) => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const mezcla = (f, b) => [f[0] * f[3] + b[0] * (1 - f[3]), f[1] * f[3] + b[1] * (1 - f[3]), f[2] * f[3] + b[2] * (1 - f[3]), 1];
  const lum = (c) => { const v = c.slice(0, 3).map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const razon = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  const fondo = (el) => { const capas = []; let e = el; while (e && e.nodeType === 1) { const c = rgba(getComputedStyle(e).backgroundColor); if (c[3] > 0) { capas.push(c); if (c[3] >= 1) break; } e = e.parentElement; }
                          let base = [11, 18, 32, 1]; for (let i = capas.length - 1; i >= 0; i--) base = mezcla(capas[i], base); return base; };
  const opacidad = (el) => { let o = 1, e = el; while (e && e.nodeType === 1) { o *= parseFloat(getComputedStyle(e).opacity); e = e.parentElement; } return o; };
  const visible = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && opacidad(el) > 0.01; };
  const filas = [];
  const recorrer = (nodo) => {
    const t = nodo.nodeType === 3 ? nodo.textContent.trim() : '';
    if (nodo.nodeType === 3 && t) {
      const el = nodo.parentElement; if (!el || ['SCRIPT', 'STYLE', 'NOSCRIPT', 'OPTION'].includes(el.tagName) || !visible(el)) return;
      const cs = getComputedStyle(el); const esSvg = el.namespaceURI === 'http://www.w3.org/2000/svg';
      const color = rgba(esSvg ? cs.fill : cs.color); color[3] *= opacidad(el);
      const bg = fondo(el); const ef = mezcla(color, bg);
      const rect = el.getBoundingClientRect();
      filas.push({texto: t.slice(0, 60), razon: +razon(ef, bg).toFixed(2), color: '#' + ef.slice(0, 3).map(x => Math.round(x).toString(16).padStart(2, '0')).join(''),
                  fondo: '#' + bg.slice(0, 3).map(x => Math.round(x).toString(16).padStart(2, '0')).join(''), tamano: cs.fontSize, peso: cs.fontWeight, etiqueta: el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : ''),
                  y: Math.round(rect.top + window.scrollY), caja: {x: rect.left, y: rect.top, w: Math.min(rect.width, 520), h: rect.height}});
    }
    for (const h of nodo.childNodes) recorrer(h);
  };
  recorrer(document.body);
  return JSON.stringify(filas);
})()"""
JS_NOTAS = """(() => {
  const sel = '[data-testid="stCaptionContainer"] p, [data-testid="stMarkdownContainer"] .aud-nota, .aud-cifras td.k small, .aud-esfuerzo, .aud-metrica .no, .aud-pie, .aud-datos dt';
  return JSON.stringify(Array.from(document.querySelectorAll(sel)).filter(e => { const r = e.getBoundingClientRect(); return e.textContent.trim().length > 0 && r.width > 20 && r.height > 6 && r.top >= 0 && r.bottom <= window.innerHeight; }).slice(0, 12)
    .map(e => { const r = e.getBoundingClientRect(); return {texto: e.textContent.trim().slice(0, 50), x: r.left, y: r.top, w: Math.min(r.width, 520), h: r.height, color_css: getComputedStyle(e).color, opacidad_css: getComputedStyle(e).opacity}; }));
})()"""
VISTAS = ["Resumen", "Cola de revisión", "Cola de revisión|Cola de cajas", "Explica una caja", "Auditoría de cámaras", "Puntuar datos nuevos", "Ética y límites", "Ayuda y glosario"] + [f"Validación|{r}" for r, _, _ in C.PESTANAS_VALIDACION]


def hexa(c: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{v:02x}" for v in c)


def lum(c: tuple[int, int, int]) -> float:
    v = [x / 255 for x in c]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def razon(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def muestrear(nav: C.Navegador, notas: list[dict]) -> list[dict]:
    """Color de fondo más frecuente y píxel de texto más alejado, en el recorte de cada nota."""
    out = []
    for n in notas:
        clip = {"x": max(0, n["x"]), "y": max(0, n["y"]), "width": max(8, n["w"]), "height": max(8, n["h"]), "scale": 1}
        img = Image.open(io.BytesIO(base64.b64decode(nav.cmd("Page.captureScreenshot", format="png", clip=clip)["data"]))).convert("RGB")
        px = list(getattr(img, "get_flattened_data", img.getdata)())
        fondo = Counter(px).most_common(1)[0][0]
        texto = max(px, key=lambda p: sum((p[i] - fondo[i]) ** 2 for i in range(3)))
        out.append({"nota": n["texto"], "fondo_px": hexa(fondo), "texto_px": hexa(texto), "razon_px": round(razon(texto, fondo), 2), "color_css": n["color_css"], "opacidad_css": n["opacidad_css"]})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8512)
    ap.add_argument("--debug", type=int, default=9338)
    ap.add_argument("--ancho", type=int, default=1366)
    ap.add_argument("--maximo", type=float, default=60.0)
    ap.add_argument("--salida", default="docs/ep3/f24_contraste.json", help="archivo de resultados (F25 usa docs/ep3/f25_contraste.json para no pisar el de F24)")
    a = ap.parse_args()
    nav = C.Navegador(a.debug)
    paginas, todas_las_notas = [], []
    try:
        for vista in VISTAS:
            seccion, _, pestana = vista.partition("|")
            nav.cmd("Emulation.setDeviceMetricsOverride", width=a.ancho, height=900, deviceScaleFactor=1, mobile=False)
            nav.cmd("Page.navigate", url=C.url(a.puerto, seccion))
            clave_previa = C.CLAVE_PREVIA.get(seccion) if seccion == "Cola de revisión" else None
            ok, e, motivo, _, _ = C.esperar(nav, seccion, a.maximo, 2.0, clave_previa)
            if not ok:
                sys.exit(f"{vista}: no terminó de dibujarse: {motivo}")
            if pestana:
                nav.js(C.JS_PESTANA_ROTULO % json.dumps(pestana))
                time.sleep(2.0)
            alto = int(min(max(e.get("alto", 900) + 40, 700), 3600))
            nav.cmd("Emulation.setDeviceMetricsOverride", width=a.ancho, height=alto, deviceScaleFactor=1, mobile=False)
            time.sleep(1.2)
            filas = nav.js(JS_DOM) or []
            sospechosos = sorted((f for f in filas if f["razon"] < UMBRAL), key=lambda f: f["razon"])
            # el DOM no ve el fondo real de algunos controles (p. ej. el valor sobre un deslizador): se arbitra con los píxeles de la captura
            arbitrados = muestrear(nav, [{"texto": f["texto"], "x": f["caja"]["x"], "y": f["caja"]["y"], "w": f["caja"]["w"], "h": f["caja"]["h"], "color_css": f["color"], "opacidad_css": "1"} for f in sospechosos])
            for f, m in zip(sospechosos, arbitrados):
                f["razon_px"], f["texto_px"], f["fondo_px"] = m["razon_px"], m["texto_px"], m["fondo_px"]
            bajos = [f for f in sospechosos if f["razon_px"] < UMBRAL]
            falsos = [f for f in sospechosos if f["razon_px"] >= UMBRAL]
            notas = nav.js(JS_NOTAS) or []
            muestras = muestrear(nav, notas)
            todas_las_notas += [{**m, "vista": vista} for m in muestras]
            minimo = min((f["razon"] if f not in falsos else f["razon_px"] for f in filas), default=None)
            paginas.append({"vista": vista, "textos_medidos": len(filas), "razon_minima": minimo, "por_debajo_de_4_5": bajos[:15], "n_por_debajo": len(bajos),
                            "falsos_positivos_del_dom": [{"texto": f["texto"], "razon_dom": f["razon"], "razon_px": f["razon_px"]} for f in falsos]})
            print(f"{vista:42s} textos {len(filas):4d}  mínimo {paginas[-1]['razon_minima']}  por debajo de {UMBRAL}: {len(bajos)}  (descartados por píxeles: {len(falsos)})")
    finally:
        nav.cerrar()
    minimo_px = min((m["razon_px"] for m in todas_las_notas), default=None)
    resumen = {"umbral": UMBRAL, "vistas": len(paginas), "textos_medidos": sum(p["textos_medidos"] for p in paginas), "textos_por_debajo": sum(p["n_por_debajo"] for p in paginas),
               "falsos_positivos_del_dom_descartados_por_pixeles": sum(len(p["falsos_positivos_del_dom"]) for p in paginas),
               "razon_minima_dom": min(p["razon_minima"] for p in paginas if p["razon_minima"] is not None), "notas_muestreadas": len(todas_las_notas), "razon_minima_en_pixeles": minimo_px}
    (RAIZ / a.salida).write_text(json.dumps({"ancho": a.ancho, "resumen": resumen, "paginas": paginas, "notas_en_pixeles": todas_las_notas}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False))
    if resumen["textos_por_debajo"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
