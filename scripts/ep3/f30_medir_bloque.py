"""F30: mide el bloque «Alertas de cámara» del Resumen y dónde caen «Cola de revisión» y sus filtros en una ventana de EXACTAMENTE 1366 x 768 px (Chrome sin interfaz por CDP; no instala nada).

``--guardar-antes`` guarda la medida actual como «antes» en ``docs/ep3/f30_altura_bloque.json``; sin la opción mide el «después», lo agrega al mismo archivo y calcula la diferencia.
Meta de F30: que el título «Cola de revisión» y sus filtros se vean en la primera pantalla sin desplazarse (alto de la ventana: 768 px; un navegador real ofrece unos 650 px útiles: se informa también).
Requiere la página corriendo en localhost. Uso: .venv\\Scripts\\python scripts/ep3/f30_medir_bloque.py --puerto 8531 [--guardar-antes]
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

SALIDA = RAIZ / "docs/ep3/f30_altura_bloque.json"
UTILES = 650
JS = """(() => {
  const r = e => { if (!e) return null; const b = e.getBoundingClientRect(); return {arriba: Math.round(b.top), abajo: Math.round(b.bottom), alto: Math.round(b.height), izquierda: Math.round(b.left), derecha: Math.round(b.right)}; };
  const panel = document.querySelector('.st-key-panel_principal');
  const h3 = Array.from(document.querySelectorAll('h3')).find(e => e.textContent.trim().startsWith('Cola de revisión'));
  const filtros = ['res_clase', 'res_camara', 'res_segmento'].map(k => r(document.querySelector('.st-key-' + k)));
  const filas = Array.from(document.querySelectorAll('[class*="st-key-celda_"], [class*="st-key-celdasel_"]')).map(r);
  const ancla = panel ? panel.querySelector('[data-testid="stPageLink"]') : null;
  const anillo = panel ? panel.querySelector('.aud-anillo-bloque') : null;
  const titular = panel ? panel.querySelector('.aud-kicker') : null;
  return JSON.stringify({kpis: r(document.querySelector('.aud-kpis')), panel: r(panel), kicker: r(titular), filas_de_alerta: filas, anillo_y_leyenda: r(anillo), enlace_en_el_bloque: !!ancla,
                         tamano_del_anillo_px: panel && panel.querySelector('.aud-anillo') ? Math.round(panel.querySelector('.aud-anillo').getBoundingClientRect().width) : null,
                         rotulo_del_anillo: r(panel ? Array.from(panel.querySelectorAll('p')).find(p => p.textContent.startsWith('Cámaras del segmento')) : null),
                         titulo_cola: r(h3), filtros_de_la_cola: filtros, alto_ventana: window.innerHeight, ancho_ventana: window.innerWidth});
})()"""


def medir(puerto: int, debug: int) -> dict:
    nav = C.Navegador(debug)
    try:
        nav.cmd("Emulation.setDeviceMetricsOverride", width=1366, height=768, deviceScaleFactor=1, mobile=False)
        nav.cmd("Page.navigate", url=C.url(puerto, "Resumen"))
        ok, _, motivo, _, _ = C.esperar(nav, "Resumen", 60.0, 2.0)
        if not ok:
            sys.exit(f"el Resumen no terminó de dibujarse: {motivo}")
        time.sleep(1.5)
        m = nav.js(JS)
    finally:
        nav.cerrar()
    f = [x for x in m["filtros_de_la_cola"] if x]
    abajo_filtros = max((x["abajo"] for x in f), default=None)
    return {**m, "alto_del_bloque_px": m["panel"]["alto"], "titulo_de_la_cola_termina_en_px": m["titulo_cola"]["abajo"] if m["titulo_cola"] else None, "filtros_terminan_en_px": abajo_filtros,
            "titulo_y_filtros_visibles_en_768": bool(m["titulo_cola"]) and abajo_filtros is not None and abajo_filtros <= m["alto_ventana"],
            "titulo_y_filtros_visibles_en_650": bool(m["titulo_cola"]) and abajo_filtros is not None and abajo_filtros <= UTILES}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8531)
    ap.add_argument("--debug", type=int, default=9353)
    ap.add_argument("--guardar-antes", action="store_true")
    a = ap.parse_args()
    medida = medir(a.puerto, a.debug)
    datos = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    if a.guardar_antes:
        datos = {"antes": medida}
    else:
        datos["despues"] = medida
        if "antes" in datos:
            datos["diferencia_alto_del_bloque_px"] = medida["alto_del_bloque_px"] - datos["antes"]["alto_del_bloque_px"]
            datos["diferencia_filtros_terminan_en_px"] = (medida["filtros_terminan_en_px"] or 0) - (datos["antes"]["filtros_terminan_en_px"] or 0)
    SALIDA.write_text(json.dumps(datos, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{'antes' if a.guardar_antes else 'después'}: bloque de {medida['alto_del_bloque_px']} px; título de la cola termina en {medida['titulo_de_la_cola_termina_en_px']} px; "
          f"filtros terminan en {medida['filtros_terminan_en_px']} px; visibles en 768: {medida['titulo_y_filtros_visibles_en_768']}; en 650: {medida['titulo_y_filtros_visibles_en_650']}")


if __name__ == "__main__":
    main()
