"""F34 y F35: las 16 capturas que se envían a revisión (Validación y Puntuar datos nuevos) a 1366 px, cada una con el estado que dice su nombre.

Usa el navegador sin interfaz de ``capturar_pagina.py`` (Chrome o Edge ya instalado, protocolo CDP; no instala nada y no hace conexiones externas) y las funciones de ``f31_f33_capturas.py``.
Con la página corriendo en localhost. Los archivos de prueba de Puntuar (un lidar_box y su archivo de asociación sintéticos, y un archivo que no es parquet) se crean en un directorio temporal
que se borra al terminar. Escribe ``images/ep3/pagina/para_revision_f34_f35/<nombre>.png`` y ``docs/ep3/f34_f35_capturas.json``.
Uso: .venv\\Scripts\\python scripts/ep3/f34_f35_capturas.py --puerto 8531
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "src"))
import capturar_pagina as C  # noqa: E402
import f31_f33_capturas as F  # noqa: E402

DESTINO = RAIZ / "images/ep3/pagina/para_revision_f34_f35"
SALIDA = RAIZ / "docs/ep3/f34_f35_capturas.json"
CLAVE_V = {"texto": "Tablas de apoyo", "conteos": [("[role=tab]", 5), (".aud-kpi", 4)]}
CLAVE_P = {"texto": "Todavía no hay un segmento cargado", "conteos": [("[data-testid=stFileUploader]", 2), (".aud-flujo", 1)]}
JS_Y_TEXTO = """((sel, texto) => { const e = Array.from(document.querySelectorAll(sel)).find(x => x.textContent.includes(texto) && x.getBoundingClientRect().height > 0); if (!e) return null;
  return JSON.stringify({top: e.getBoundingClientRect().top + (window.scrollY || 0), bottom: e.getBoundingClientRect().bottom + (window.scrollY || 0)}); })"""


def y_de(nav: C.Navegador, selector: str, texto: str) -> dict:
    r = None
    for _ in range(5):
        r = nav.js(f"({JS_Y_TEXTO})({json.dumps(selector)}, {json.dumps(texto)})")
        if r:
            break
        time.sleep(1.0)
    if not r:
        raise RuntimeError(f"no encontré «{texto}» en {selector}")
    return r


def foto_y(nav: C.Navegador, nombre: str, y0: float, y1: float, hechas: list[dict]) -> None:
    nav.js("(() => { window.scrollTo(0, 0); document.querySelectorAll('*').forEach(e => { if (e.scrollLeft) e.scrollLeft = 0; }); return true; })()")
    time.sleep(0.4)
    alto = int(min(y1 - y0, 2600))
    datos = nav.cmd("Page.captureScreenshot", format="png", clip={"x": 0, "y": max(0, y0), "width": F.ANCHO, "height": alto, "scale": 1})["data"]
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / f"{nombre}.png").write_bytes(base64.b64decode(datos))
    print(f"OK   {nombre:42s} {F.ANCHO} x {alto} px")
    hechas.append({"archivo": f"{nombre}.png", "ancho": F.ANCHO, "alto": alto})


def pestana(nav: C.Navegador, puerto: int, rotulo: str) -> None:
    F.abrir(nav, puerto, "Validación", CLAVE_V)
    nav.js(C.JS_PESTANA_ROTULO % json.dumps(rotulo))
    F.estable(nav, "Validación", CLAVE_V, 2.0)


def abrir_resumen(nav: C.Navegador, texto: str) -> None:
    nav.js(f"({F.JS_CLIC_TEXTO})('summary', {json.dumps(texto)}, false)")
    time.sleep(1.2)


def subir(nav: C.Navegador, indice: int, ruta: Path) -> None:
    doc = nav.cmd("DOM.getDocument", depth=-1)
    ids = nav.cmd("DOM.querySelectorAll", nodeId=doc["root"]["nodeId"], selector="input[type=file]")["nodeIds"]
    nav.cmd("DOM.setFileInputFiles", files=[str(ruta)], nodeId=ids[indice])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8531)
    ap.add_argument("--debug", type=int, default=9371)
    a = ap.parse_args()
    from tests.ep3.test_pagina_f35 import _asoc_sintetica, _lidar_sintetico

    nav = C.Navegador(a.debug)
    hechas: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="capturas_f35_") as tmp:
        tmp_ = Path(tmp)
        lidar = _lidar_sintetico(2_000, segmentos=1)
        lidar.to_parquet(tmp_ / "lidar_box_prueba.parquet")
        _asoc_sintetica(lidar).to_parquet(tmp_ / "asociacion_prueba.parquet")
        (tmp_ / "datos_malos.parquet").write_text("esto no es un parquet", encoding="utf-8")
        try:
            # ------------------------------------------------------------------------------------ F34: Validación
            pestana(nav, a.puerto, "Modelo elegido")
            r = nav.js(f"({F.JS_RECT})(['[role=tablist]'], false)")
            foto_y(nav, "f34_01_cabecera", 0, r["bottom"] + 90, hechas)
            panel = nav.js(f"({F.JS_RECT})(['tabpanel'], false)")
            foto_y(nav, "f34_02_modelo_elegido", panel["top"] - 20, panel["bottom"] + 16, hechas)
            pestana(nav, a.puerto, "Generalización")
            panel = nav.js(f"({F.JS_RECT})(['tabpanel'], false)")
            foto_y(nav, "f34_03_generalizacion", panel["top"] - 20, panel["bottom"] + 16, hechas)
            pestana(nav, a.puerto, "Alternativas")
            panel = nav.js(f"({F.JS_RECT})(['tabpanel'], false)")
            mitad = y_de(nav, "p.aud-card-t", "¿Combinar modelos ayuda?")["top"]
            foto_y(nav, "f34_04_alternativas_hiperparametros", panel["top"] - 20, mitad - 8, hechas)
            foto_y(nav, "f34_05_alternativas_ensambles", mitad - 8, panel["bottom"] + 16, hechas)
            pestana(nav, a.puerto, "Tipos de caso")
            panel = nav.js(f"({F.JS_RECT})(['tabpanel'], false)")
            foto_y(nav, "f34_06_tipos_de_caso", panel["top"] - 20, panel["bottom"] + 16, hechas)
            pestana(nav, a.puerto, "En muestra")
            panel = nav.js(f"({F.JS_RECT})(['tabpanel'], false)")
            grafico = y_de(nav, "p.aud-card-t", "Fracción de cajas a revisar para encontrar")["top"]
            foto_y(nav, "f34_07_en_muestra_impacto", panel["top"] - 20, grafico - 8, hechas)
            foto_y(nav, "f34_08_en_muestra_grafico", grafico - 8, panel["bottom"] + 16, hechas)
            # tablas de apoyo abiertas (dos sub-desplegables) y una tabla paginada
            pestana(nav, a.puerto, "Modelo elegido")
            abrir_resumen(nav, "Tablas de apoyo")
            abrir_resumen(nav, "Criterios por candidato")
            abrir_resumen(nav, "Todos los candidatos")
            F.estable(nav, "Validación", CLAVE_V, 1.5)
            ap_ = y_de(nav, "details", "Tablas de apoyo")
            foto_y(nav, "f34_09_tablas_de_apoyo_abiertas", ap_["top"] - 16, ap_["bottom"] + 12, hechas)
            pestana(nav, a.puerto, "Generalización")
            abrir_resumen(nav, "Tablas de apoyo")
            abrir_resumen(nav, "Dejando un segmento fuera")
            F.estable(nav, "Validación", CLAVE_V, 1.5)
            seg = y_de(nav, "details", "Dejando un segmento fuera")
            foto_y(nav, "f34_10_tabla_paginada", seg["top"] - 16, seg["bottom"] + 12, hechas)
            # ------------------------------------------------------------------------------------ F35: Puntuar datos nuevos
            F.abrir(nav, a.puerto, "Puntuar datos nuevos", CLAVE_P)
            alto = nav.js("Math.ceil(document.querySelector('[data-testid=\"stMainBlockContainer\"]').getBoundingClientRect().bottom)")
            foto_y(nav, "f35_01_vacio", 0, alto + 30, hechas)
            subir(nav, 0, tmp_ / "datos_malos.parquet")
            time.sleep(4)
            F.estable(nav, "Puntuar datos nuevos", {"texto": "no es un parquet válido", "conteos": [("[data-testid=stFileUploader]", 2)]}, 1.5)
            alto = nav.js("Math.ceil(document.querySelector('[data-testid=\"stMainBlockContainer\"]').getBoundingClientRect().bottom)")
            foto_y(nav, "f35_02_error_de_archivo", 0, alto + 30, hechas)
            # resultado con el segmento de ejemplo (datos reales de desarrollo)
            F.abrir(nav, a.puerto, "Puntuar datos nuevos", CLAVE_P)
            nav.js(f"({F.JS_CLIC_TEXTO})('button', 'Usar un segmento de desarrollo de ejemplo', true)")
            time.sleep(8)
            clave_r = {"texto": "Resumen del cálculo", "conteos": [(".aud-flujo", 1), (".aud-kpi", 3)]}
            F.estable(nav, "Puntuar datos nuevos", clave_r, 2.0)
            cab = nav.js(f"({F.JS_RECT})(['.st-key-pt_resultado'], false)")
            foto_y(nav, "f35_03_resultado_resumen", 0, cab["bottom"] + 20, hechas)
            # resultado con los dos archivos (sintéticos): celdas marcadas y cola
            F.abrir(nav, a.puerto, "Puntuar datos nuevos", CLAVE_P)
            subir(nav, 1, tmp_ / "asociacion_prueba.parquet")
            time.sleep(2.5)
            subir(nav, 0, tmp_ / "lidar_box_prueba.parquet")
            time.sleep(10)
            F.estable(nav, "Puntuar datos nuevos", clave_r, 2.0)
            c = nav.js(f"({F.JS_RECT})(['.st-key-pt_celdas'], false)")
            foto_y(nav, "f35_04_resultado_celdas", c["top"] - 16, c["bottom"] + 16, hechas)
            k = nav.js(f"({F.JS_RECT})(['.st-key-pt_cola'], false)")
            foto_y(nav, "f35_05_resultado_cola", k["top"] - 16, k["bottom"] + 16, hechas)
            # formato abierto (estado vacío)
            F.abrir(nav, a.puerto, "Puntuar datos nuevos", CLAVE_P)
            abrir_resumen(nav, "Formato de los archivos de entrada")
            F.estable(nav, "Puntuar datos nuevos", CLAVE_P, 1.5)
            fo = y_de(nav, "details", "Formato de los archivos de entrada")
            foto_y(nav, "f35_06_formato_abierto", fo["top"] - 16, fo["bottom"] + 12, hechas)
        finally:
            nav.cerrar()
    SALIDA.write_text(json.dumps({"ancho": F.ANCHO, "capturas": hechas}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(hechas)} capturas en {DESTINO}")


if __name__ == "__main__":
    main()
