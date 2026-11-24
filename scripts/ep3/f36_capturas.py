"""F36: las 7 capturas de revisión (Ética y límites y Ayuda y glosario) a 1366 px, cada una con el estado que dice su nombre.

Usa el navegador sin interfaz de ``capturar_pagina.py`` (Chrome o Edge ya instalado, protocolo CDP; no instala nada ni hace conexiones externas). La captura del modo publicado arranca una segunda copia de la página en
otro puerto con ``EP3_ENTORNO=publicado`` (la variable manda sobre ``MODO_DESPLIEGUE``, que sigue en ``local`` en el código) y la cierra al terminar. Escribe
``images/ep3/pagina/para_revision_f36/<nombre>.png`` y ``docs/ep3/f36_capturas.json``.
Uso: .venv\\Scripts\\python scripts/ep3/f36_capturas.py --puerto 8531 --puerto-publicado 8532
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ / "src"))
import capturar_pagina as C  # noqa: E402
import f31_f33_capturas as F  # noqa: E402
import f34_f35_capturas as G  # noqa: E402

DESTINO = RAIZ / "images/ep3/pagina/para_revision_f36"
SALIDA = RAIZ / "docs/ep3/f36_capturas.json"
CLAVE_E = {"texto": "Dónde corre", "conteos": [(".aud-tf", 4), (".aud-hero", 1)]}
CLAVE_A = {"texto": "¿Cuánto tarda revisar una caja?", "conteos": [(".aud-gl", 1), (".aud-guia3", 3), ("[data-testid=stExpander]", 5)]}


def foto(nav: C.Navegador, nombre: str, y0: float, y1: float, hechas: list[dict]) -> None:
    G.foto_y(nav, nombre, y0, y1, [])
    ruta = DESTINO.parent / "para_revision_f34_f35" / f"{nombre}.png"          # foto_y escribe en la carpeta de F34/F35: se mueve a la de F36
    destino = DESTINO / f"{nombre}.png"
    DESTINO.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(ruta.read_bytes())
    ruta.unlink()
    hechas.append({"archivo": f"{nombre}.png", "ancho": F.ANCHO, "alto": int(min(y1 - y0, 2600))})


def tope(nav: C.Navegador) -> float:
    return float(nav.js("Math.ceil(document.querySelector('[data-testid=\"stMainBlockContainer\"]').getBoundingClientRect().bottom)"))


def esperar_puerto(puerto: int, maximo: float = 60.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < maximo:
        try:
            if urllib.request.urlopen(f"http://127.0.0.1:{puerto}/_stcore/health", timeout=2).status == 200:
                return True
        except Exception:  # noqa: BLE001
            time.sleep(1)
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8531)
    ap.add_argument("--puerto-publicado", type=int, default=8532)
    ap.add_argument("--debug", type=int, default=9391)
    a = ap.parse_args()
    hechas: list[dict] = []
    nav = C.Navegador(a.debug)
    try:
        # ------------------------------------------------------------------------------------ Ética y límites (modo local)
        F.abrir(nav, a.puerto, "Ética y límites", CLAVE_E)
        desemp = G.y_de(nav, "[class*=st-key-et_desempeno]", "Desempeño")
        limites = G.y_de(nav, "[class*=st-key-et_limites]", "Límites conocidos")
        foto(nav, "f36_01_etica_arriba", 0, desemp["bottom"] + 20, hechas)
        foto(nav, "f36_02_etica_abajo", limites["top"] - 16, tope(nav) + 30, hechas)
        # ------------------------------------------------------------------------------------ Ayuda y glosario
        F.abrir(nav, a.puerto, "Ayuda y glosario", CLAVE_A)
        pag = G.y_de(nav, "p.aud-card-t", "Glosario")
        foto(nav, "f36_04_ayuda_tres_pasos", 0, pag["top"] - 8, hechas)
        preg = G.y_de(nav, "p.aud-card-t", "Preguntas frecuentes")
        foto(nav, "f36_05_ayuda_glosario", pag["top"] - 8, preg["top"] - 8, hechas)
        # búsqueda: texto + grupo
        caja = nav.js(f"({F.JS_CENTRO})('input[placeholder^=Buscar]', '', 0)")
        F.clic(nav, caja["x"], caja["y"])
        for ch in "muestra":                                                   # teclas reales, una por una (así Streamlit recibe el texto)
            nav.cmd("Input.dispatchKeyEvent", type="keyDown", key=ch, text=ch, unmodifiedText=ch)
            nav.cmd("Input.dispatchKeyEvent", type="keyUp", key=ch)
        F.tecla(nav, "Enter", "Enter", 13)
        time.sleep(2.5)
        print("valor del buscador:", nav.js("document.querySelector('input[placeholder^=Buscar]').value"))
        nav.js(f"({F.JS_CLIC_TEXTO})('button', 'Rigor', true)")
        time.sleep(2.5)
        print("valor tras el grupo:", nav.js("document.querySelector('input[placeholder^=Buscar]').value"))
        pag = G.y_de(nav, "p.aud-card-t", "Glosario")
        preg = G.y_de(nav, "p.aud-card-t", "Preguntas frecuentes")
        foto(nav, "f36_06_ayuda_busqueda", pag["top"] - 8, preg["top"] - 8, hechas)
        # preguntas abiertas
        F.abrir(nav, a.puerto, "Ayuda y glosario", CLAVE_A)
        for _ in range(5):
            nav.js("(() => { const d = Array.from(document.querySelectorAll('details')).find(x => !x.open && x.getBoundingClientRect().height > 0); if (d) d.querySelector('summary').click(); return !!d; })()")
            time.sleep(0.6)
        F.estable(nav, "Ayuda y glosario", CLAVE_A, 1.5)
        preg = G.y_de(nav, "p.aud-card-t", "Preguntas frecuentes")
        foto(nav, "f36_07_ayuda_preguntas_abiertas", preg["top"] - 8, tope(nav) + 30, hechas)
        # ------------------------------------------------------------------------------------ modo publicado (copia de la página con EP3_ENTORNO=publicado)
        entorno = {**os.environ, "EP3_ENTORNO": "publicado", "PYTHONIOENCODING": "utf-8"}
        srv = subprocess.Popen([sys.executable, str(RAIZ / "app/lanzar.py"), "--server.address", "localhost", "--server.port", str(a.puerto_publicado), "--server.headless", "true",
                                "--browser.gatherUsageStats", "false"], env=entorno, cwd=str(RAIZ), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            if not esperar_puerto(a.puerto_publicado):
                raise RuntimeError("la copia del modo publicado no arrancó")
            F.abrir(nav, a.puerto_publicado, "Ética y límites", CLAVE_E)
            limites = G.y_de(nav, "[class*=st-key-et_limites]", "Límites conocidos")
            foto(nav, "f36_03_etica_modo_publicado", limites["bottom"] - 4, tope(nav) + 30, hechas)
        finally:
            subprocess.run(["taskkill", "/PID", str(srv.pid), "/F", "/T"], capture_output=True)
    finally:
        nav.cerrar()
    hechas.sort(key=lambda x: x["archivo"])
    SALIDA.write_text(json.dumps({"ancho": F.ANCHO, "capturas": hechas}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(hechas)} capturas en {DESTINO}")


if __name__ == "__main__":
    main()
