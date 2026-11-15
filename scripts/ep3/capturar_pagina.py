"""F18-C14: captura cada seccion de la pagina con un Chrome/Edge ya instalado en modo sin interfaz (protocolo CDP por websocket local). No instala nada.

Requiere la pagina corriendo en localhost (por ejemplo: .venv\Scripts\python -m streamlit run app\app.py --server.port 8512 --server.headless true).
Escribe images/ep3/pagina/NN_seccion.png (perfil Analista de revision, modo normal) y, con --presentacion, 09_inicio_presentacion.png.
Uso: .venv\Scripts\python scripts/ep3/capturar_pagina.py --puerto 8512
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from websockets.sync.client import connect

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.app_logica import SECCIONES  # noqa: E402

NAVEGADORES = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
ALTO = {"Inicio": 1500, "Auditoría de cámaras": 1900, "Cola de revisión": 2300, "Explica una caja": 1400, "Evidencia": 1100, "Ética y límites": 1100, "Puntuar datos nuevos": 1100, "Ayuda y glosario": 1500}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8512)
    ap.add_argument("--espera", type=float, default=9.0)
    ap.add_argument("--debug", type=int, default=9333)
    a = ap.parse_args()
    nav = next((n for n in NAVEGADORES if Path(n).exists()), None)
    if nav is None:
        sys.exit("no hay Chrome ni Edge instalados: no se capturan imagenes (no se instala nada)")
    destino = RAIZ / "images/ep3/pagina"
    destino.mkdir(parents=True, exist_ok=True)
    perfil = tempfile.mkdtemp(prefix="perfil_captura_")
    proc = subprocess.Popen([nav, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-background-networking", "--disable-component-update", f"--remote-debugging-port={a.debug}",
                             f"--user-data-dir={perfil}", "--force-color-profile=srgb", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                objetivos = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.debug}/json"))
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.5)
        ws_url = next(o["webSocketDebuggerUrl"] for o in objetivos if o.get("type") == "page")
        with connect(ws_url, max_size=64 * 1024 * 1024) as ws:
            n = [0]

            def cmd(metodo: str, **params):
                n[0] += 1
                ws.send(json.dumps({"id": n[0], "method": metodo, "params": params}))
                while True:
                    r = json.loads(ws.recv())
                    if r.get("id") == n[0]:
                        return r.get("result", {})

            trabajos = [(f"{i:02d}_{s.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('ó', 'o').replace('í', 'i').replace('ú', 'u')}", s, False) for i, s in enumerate(SECCIONES, 1)]
            trabajos.append(("09_inicio_modo_presentacion", "Inicio", True))
            for nombre, seccion, pres in trabajos:
                cmd("Emulation.setDeviceMetricsOverride", width=1400, height=ALTO[seccion], deviceScaleFactor=1, mobile=False)
                cmd("Page.navigate", url=f"http://localhost:{a.puerto}/?seccion={urllib.parse.quote(seccion)}")
                time.sleep(a.espera)
                if pres:   # activa el interruptor del modo presentacion
                    for tipo in ("mousePressed", "mouseReleased"):   # clic real sobre el interruptor (barra lateral)
                        cmd("Input.dispatchMouseEvent", type=tipo, x=36, y=204, button="left", clickCount=1)
                    time.sleep(4)
                img = cmd("Page.captureScreenshot", format="png")
                (destino / f"{nombre}.png").write_bytes(base64.b64decode(img["data"]))
                print("capturada", nombre)
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
