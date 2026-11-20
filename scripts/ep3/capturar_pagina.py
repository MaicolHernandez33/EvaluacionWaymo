"""F18-C14 / F19-B1 / F20-P11: captura cada seccion de la pagina con un Chrome o Edge ya instalado en modo sin interfaz (protocolo CDP por websocket local). No instala nada.

Espera ROBUSTA (F20-P11). Una captura se da por lista solo cuando se cumplen TODAS estas condiciones a la vez:
  1. Streamlit no esta ejecutando el script (``data-test-script-state`` de ``[data-testid="stApp"]`` es ``notRunning``) y no hay esqueleto de carga ni spinner;
  2. el numero de nodos del DOM se mantiene estable al menos ``--estable`` segundos (2 s por defecto);
  3. aparece el ULTIMO elemento clave de la seccion (el ultimo texto que dibuja, no el primero) y se cumplen los conteos de elementos de ``CLAVE`` (por ejemplo, 6 bloques de la ficha de Etica);
  4. el alto del contenido supera el minimo de la seccion (``ALTO_MIN``).
Si pasa el tiempo maximo sin cumplirse, la captura NO se guarda como valida: se escribe el motivo y se sale con error. Registra las excepciones de la consola del navegador.
El viewport se ajusta al alto real del contenido (entre 700 y 3600 px) y se vuelve a esperar la estabilidad antes de fotografiar.

``--linea-de-tiempo SECCION`` (diagnostico): navega a la seccion y muestrea cada 0,1 s el estado de ejecucion, los nodos del DOM y los bloques clave, y guarda la linea de tiempo en
``data/08_reporting_ep3/captura_linea_tiempo_<seccion>.json`` para ver cuando la pagina esta realmente completa y que habria visto el criterio antiguo (texto del primer elemento + sin spinner).

Requiere la pagina corriendo en localhost (por ejemplo: .venv\\Scripts\\python app\\lanzar.py --server.port 8512 --server.headless true).
Escribe images/ep3/pagina/NN_seccion_<ancho>.png (rol Analista de revision, modo normal) y 09_resumen_modo_presentacion_<ancho>.png, y
data/08_reporting_ep3/capturas_resultado.json con el tiempo hasta estar lista cada captura.
Uso: .venv\\Scripts\\python scripts/ep3/capturar_pagina.py --puerto 8512 --anchos 1366 1920 [--secciones "Explica una caja"] [--sin-guardar] [--linea-de-tiempo "Ética y límites"]
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.request
from pathlib import Path

from websockets.sync.client import connect

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.app_logica import SECCIONES, URL_PAGINA  # noqa: E402

NAVEGADORES = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
# alto minimo (px) del contenido de cada seccion: una captura mas baja es una pagina incompleta (la de «Etica» salio con 1 bloque de 6)
ALTO_MIN = {"Resumen": 600, "Cola de revisión": 700, "Explica una caja": 600, "Auditoría de cámaras": 700, "Validación": 450, "Puntuar datos nuevos": 550, "Ética y límites": 450, "Ayuda y glosario": 900}
# el ULTIMO elemento que dibuja cada seccion (texto) y conteos de elementos que deben existir (selector CSS, minimo)
CLAVE = {"Resumen": {"texto": "Validación externa pendiente", "conteos": [(".aud-metrica", 4), (".vega-embed", 1)]},
         "Cola de revisión": {"texto": "Detalle de la caja en la posición 1", "conteos": [("[role=tab]", 2), ("[data-testid=stDataFrame]", 1)]},
         "Explica una caja": {"texto": "Es una ilustración del modelo", "conteos": [(".vega-embed", 1), ("[data-testid=stSlider]", 3)]},
         "Auditoría de cámaras": {"texto": "Las celdas se llaman", "conteos": [(".vega-embed", 1), (".aud-metrica", 4), ("[data-testid=stTable]", 1)]},
         "Validación": {"texto": "Ver tabla completa", "conteos": [(".vega-embed", 1), ("[role=tab]", 6)]},
         "Puntuar datos nuevos": {"texto": "Sin archivos cargados", "conteos": [("[data-testid=stFileUploader]", 2), ("[data-testid=stTable]", 1)]},
         "Ética y límites": {"texto": "No debe exponerse en una red sin autenticación", "conteos": [(".aud-ficha", 6)]},
         "Ayuda y glosario": {"texto": "¿Cuánto tarda revisar una caja?", "conteos": [(".aud-tabla", 1), ("[data-testid=stExpander]", 5)]}}
# la cola se fotografia con la pestana «Cola de cajas» abierta y la primera fila elegida (maestro-detalle): primero se espera la pagina base (clave previa), luego se prepara y se espera lo final
CLAVE_PREVIA = {"Cola de revisión": {"texto": "Solo cola: unas", "conteos": [("[role=tab]", 2), (".vega-embed", 1)]}}
JS_PESTANA = "(() => { const t = Array.from(document.querySelectorAll('[role=tab]')).find(x => x.textContent.includes('Cola de cajas')); if (t) t.click(); return !!t; })()"
JS_TABLA = "(() => { const d = document.querySelector('[data-testid=\"stDataFrame\"]'); if (!d) return null; const r = d.getBoundingClientRect(); return JSON.stringify({x: r.left, y: r.top, w: r.width, h: r.height}); })()"
# F21: variantes de una pagina que tambien se fotografian. Cola sin fila elegida; las seis pestanas de Validacion (cada una con su texto propio, que solo esta visible con la pestana abierta)
PESTANAS_VALIDACION = [("Hiperparámetros", "hiperparametros", "Cambio de PR-AUC al optimizar"), ("Ensambles", "ensambles", "Diferencia de AUC entre cada ensamble"), ("Generalización", "generalizacion", "Punto azul: AUC"),
                       ("Selección", "seleccion", "Resultados de la solución elegida"), ("No supervisado", "no_supervisado", "Proporción de cajas sin pareja en cada tipo de caso"),
                       ("En muestra", "en_muestra", "Fracción de las cajas que hay que revisar")]
CLAVE_COLA_SIN_FILA = {"texto": "Seleccione una fila", "conteos": [("[role=tab]", 2), ("[data-testid=stDataFrame]", 1)]}
JS_GEOMETRIA = """(() => {
  const q = s => document.querySelector(s);
  const chip = q('.st-key-chip_estado button'), cont = q('[data-testid="stMainBlockContainer"]');
  const r = chip ? chip.getBoundingClientRect() : null, c = cont ? cont.getBoundingClientRect() : null;
  const pad = cont ? parseFloat(getComputedStyle(cont).paddingRight) : 0;
  const alertas = Array.from(document.querySelectorAll('[class*="st-key-alerta_"]')).map(a => {
    const tx = a.querySelector('.aud-fila'), en = a.querySelector('a');
    if (!tx || !en) return null;
    const rt = tx.getBoundingClientRect(), re = en.getBoundingClientRect();
    return {texto_centro: (rt.top + rt.bottom) / 2, enlace_centro: (re.top + re.bottom) / 2, dy: Math.abs((rt.top + rt.bottom) / 2 - (re.top + re.bottom) / 2)};
  }).filter(x => x);
  const ancho_pagina = document.documentElement.scrollWidth, ancho_ventana = window.innerWidth;
  return JSON.stringify({chip_derecha: r && r.right, contenido_derecha: c && c.right - pad, alertas, scroll_horizontal_px: ancho_pagina - ancho_ventana});
})()"""
JS_PESTANA_ROTULO = "((rotulo) => { const t = Array.from(document.querySelectorAll('[role=tab]')).find(x => x.textContent.trim() === rotulo); if (t) t.click(); return !!t; })(%s)"
PIE = "Waymo Open Dataset v2, uso académico"            # el pie lo dibuja el marco DESPUES de la seccion: si esta, el script termino
JS_ESTADO = """((clave, pie, conteos) => {
  const app = document.querySelector('[data-testid="stApp"]');
  const estado = app ? app.getAttribute('data-test-script-state') : null;
  const b = document.body ? document.body.innerText : '';
  const spinner = !!document.querySelector('[data-testid="stSpinner"], .stSpinner');
  const esqueleto = !!document.querySelector('[data-testid="stSkeleton"], [class*="skeleton" i]');
  const viejo_ocupado = !!document.querySelector('[data-testid="stSpinner"], [data-testid="stStatusWidget"] [class*="running" i], .stSpinner');   // el indicador del criterio antiguo
  const bloque = document.querySelector('[data-testid="stMainBlockContainer"]');
  const alto = bloque ? Math.ceil(bloque.getBoundingClientRect().bottom + (document.querySelector('[data-testid="stMain"]') || document.documentElement).scrollTop) : 0;
  const cuentas = conteos.map(c => document.querySelectorAll(c[0]).length);
  return JSON.stringify({estado, spinner, esqueleto, viejo_ocupado, nodos: document.querySelectorAll('*').length, alto, largo: b.length,
                         tiene_clave: b.includes(clave), tiene_pie: b.includes(pie), cuentas, conteos_ok: conteos.every((c, i) => cuentas[i] >= c[1])});
})(%s, %s, %s)"""


def nombre_archivo(i: int, s: str) -> str:
    base = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode().replace(" ", "_")
    return f"{i:02d}_{base}"


def listo(e: dict, seccion: str, estable_s: float, clave: dict | None = None) -> tuple[bool, str]:
    """(lista?, motivo si no). ``estable_s`` = segundos que el numero de nodos lleva sin cambiar."""
    if e.get("estado") != "notRunning":
        return False, f"el script sigue ejecutandose (estado {e.get('estado')})"
    if e.get("spinner") or e.get("esqueleto"):
        return False, "hay spinner o esqueleto de carga"
    if not e.get("tiene_clave"):
        return False, "falta el ultimo elemento clave de la seccion"
    if not e.get("conteos_ok"):
        return False, f"faltan elementos: {e.get('cuentas')} (se esperaba {(clave or CLAVE[seccion])['conteos']})"
    if not e.get("tiene_pie"):
        return False, "falta el pie (el marco no termino)"
    if e.get("alto", 0) < ALTO_MIN[seccion]:
        return False, f"el contenido mide {e.get('alto')} px (minimo {ALTO_MIN[seccion]})"
    if estable_s < 2.0:
        return False, f"el DOM lleva {estable_s:.1f} s estable (se piden 2 s)"
    return True, ""


class Navegador:
    def __init__(self, puerto_debug: int) -> None:
        nav = next((n for n in NAVEGADORES if Path(n).exists()), None)
        if nav is None:
            sys.exit("no hay Chrome ni Edge instalados: no se capturan imagenes (no se instala nada)")
        self.perfil = tempfile.mkdtemp(prefix="perfil_captura_")
        self.proc = subprocess.Popen([nav, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-background-networking", "--disable-component-update", f"--remote-debugging-port={puerto_debug}",
                                      f"--user-data-dir={self.perfil}", "--force-color-profile=srgb", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        objetivos = []
        for _ in range(40):
            try:
                objetivos = json.load(urllib.request.urlopen(f"http://127.0.0.1:{puerto_debug}/json"))
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.5)
        self.ws = connect(next(o["webSocketDebuggerUrl"] for o in objetivos if o.get("type") == "page"), max_size=64 * 1024 * 1024)
        self.n = 0
        self.eventos: list[dict] = []
        for m in ("Runtime.enable", "Log.enable", "Page.enable"):
            self.cmd(m)

    def cmd(self, metodo: str, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": metodo, "params": params}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == self.n:
                return r.get("result", {})
            if "method" in r:
                self.eventos.append(r)

    def js(self, expresion: str):
        v = self.cmd("Runtime.evaluate", expression=expresion, returnByValue=True).get("result", {}).get("value")
        return json.loads(v) if isinstance(v, str) and v[:1] in "{[" else v

    def cerrar(self) -> None:
        try:
            self.ws.close()
        finally:
            self.proc.terminate()


def estado_pagina(nav: Navegador, seccion: str, clave: dict | None = None) -> dict:
    k = clave or CLAVE[seccion]
    return nav.js(JS_ESTADO % (json.dumps(k["texto"]), json.dumps(PIE), json.dumps(k["conteos"]))) or {}


def esperar(nav: Navegador, seccion: str, maximo: float, estable_s: float = 2.0, clave: dict | None = None) -> tuple[bool, dict, str, float, float | None]:
    """Sondea hasta que ``listo`` se cumple o se acaba el tiempo. Devuelve (ok, ultimo estado, motivo, segundos, segundos hasta que la pagina estuvo COMPLETA).

    El ultimo valor es el primer instante en que se cumplen todas las condiciones salvo la estabilidad del DOM: es el tiempo de carga real de la pagina (la captura espera ademas ``estable_s``).
    """
    t0 = time.time()
    nodos, desde = None, time.time()
    e: dict = {}
    motivo = "no se llego a medir"
    completa: float | None = None
    while time.time() - t0 < maximo:
        e = estado_pagina(nav, seccion, clave)
        if e.get("nodos") != nodos:
            nodos, desde = e.get("nodos"), time.time()
        if completa is None and listo(e, seccion, 99.0, clave)[0]:
            completa = round(time.time() - t0, 1)
        ok, motivo = listo(e, seccion, time.time() - desde, clave)
        if ok:
            return True, e, "", round(time.time() - t0, 1), completa
        time.sleep(0.2)
    return False, e, motivo, round(time.time() - t0, 1), completa


def url(puerto: int, seccion: str) -> str:
    return f"http://localhost:{puerto}/" + ("" if seccion == SECCIONES[0] else URL_PAGINA[seccion])      # la pagina por defecto (Resumen) se sirve en la raiz


def linea_de_tiempo(a: argparse.Namespace, seccion: str) -> None:
    """Diagnostico: muestrea cada 0,1 s durante ``--maximo`` segundos y compara con el criterio antiguo (primer texto + sin spinner)."""
    nav = Navegador(a.debug)
    try:
        nav.cmd("Emulation.setDeviceMetricsOverride", width=a.anchos[0], height=900, deviceScaleFactor=1, mobile=False)
        t0 = time.time()
        nav.cmd("Page.navigate", url=url(a.puerto, seccion))
        muestras = []
        n_bloques = dict(CLAVE[seccion]["conteos"]).get(".aud-ficha")
        while time.time() - t0 < min(a.maximo, 25):
            e = estado_pagina(nav, seccion)
            muestras.append({"t": round(time.time() - t0, 2), "estado": e.get("estado"), "nodos": e.get("nodos"), "cuentas": e.get("cuentas"), "tiene_clave": e.get("tiene_clave"),
                             "alto": e.get("alto"), "spinner": e.get("spinner"), "esqueleto": e.get("esqueleto"), "viejo_ocupado": e.get("viejo_ocupado")})
            time.sleep(0.1)
        salida = RAIZ / f"data/08_reporting_ep3/captura_linea_tiempo_{nombre_archivo(0, seccion)[3:]}.json"
        salida.write_text(json.dumps(muestras, indent=0, ensure_ascii=False), encoding="utf-8")
        estados = []
        for m in muestras:
            if not estados or estados[-1][1] != m["estado"]:
                estados.append((m["t"], m["estado"]))
        parcial = [m for m in muestras if m["estado"] == "running" and m["cuentas"] and any(c > 0 for c in m["cuentas"]) and not m["tiene_clave"]]
        print(f"linea de tiempo de «{seccion}»: {len(muestras)} muestras; transiciones de estado: {estados}")
        print(f"  muestras con la seccion A MEDIAS (script ejecutandose, algun bloque dibujado, falta el ultimo elemento): {len(parcial)}"
              + (f" (de t={parcial[0]['t']} s a t={parcial[-1]['t']} s; cuentas {parcial[0]['cuentas']} -> {parcial[-1]['cuentas']})" if parcial else ""))
        ciegas = [m for m in muestras if m["estado"] == "running" and not m["viejo_ocupado"]]
        print(f"  muestras en las que el script SE EJECUTABA pero el indicador del criterio antiguo (spinner / status widget) no lo mostraba: {len(ciegas)} de {sum(1 for m in muestras if m['estado'] == 'running')}")
        primera = next((m for m in muestras if m["cuentas"] and m["cuentas"][0] > 0), None)
        completa = next((m for m in muestras if m["estado"] == "notRunning" and m["tiene_clave"] and m["cuentas"] and all(c >= k[1] for c, k in zip(m["cuentas"], CLAVE[seccion]["conteos"]))), None)
        print(f"  primer bloque visible: {primera['t'] if primera else None} s; pagina completa y sin ejecutar: {completa['t'] if completa else None} s ({n_bloques} bloques esperados)")
        print("  escrito", salida.relative_to(RAIZ))
    finally:
        nav.cerrar()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8512)
    ap.add_argument("--maximo", type=float, default=60.0, help="segundos maximos de espera por seccion")
    ap.add_argument("--debug", type=int, default=9333)
    ap.add_argument("--anchos", type=int, nargs="+", default=[1366, 1920])
    ap.add_argument("--secciones", nargs="+", default=None)
    ap.add_argument("--estable", type=float, default=2.0, help="segundos que el DOM debe llevar estable")
    ap.add_argument("--sin-guardar", action="store_true", help="solo mide y registra; no escribe PNG")
    ap.add_argument("--linea-de-tiempo", default=None, help="DIAGNOSTICO: muestrea una seccion cada 0,1 s (ver la cabecera)")
    a = ap.parse_args()
    if a.linea_de_tiempo:
        linea_de_tiempo(a, a.linea_de_tiempo)
        return
    destino = RAIZ / "images/ep3/pagina"
    destino.mkdir(parents=True, exist_ok=True)
    nav = Navegador(a.debug)
    resultado: list[dict] = []
    fallo = False
    try:
        secs = [(i, s) for i, s in enumerate(SECCIONES, 1) if a.secciones is None or s in a.secciones]
        for ancho in a.anchos:
            trabajos: list[tuple[str, str, bool, str | None]] = []
            for i, s in secs:
                if s == "Validación":
                    trabajos += [(f"{nombre_archivo(i, s)}_{sufijo}", s, False, f"tab:{rotulo}|{texto}") for rotulo, sufijo, texto in PESTANAS_VALIDACION]
                else:
                    trabajos.append((nombre_archivo(i, s), s, False, "cola_con_fila" if s == "Cola de revisión" else None))
                    if s == "Cola de revisión":
                        trabajos.append((nombre_archivo(i, s) + "_sin_seleccion", s, False, "cola_sin_fila"))
            if a.secciones is None:
                trabajos.append(("09_resumen_modo_presentacion", "Resumen", True, None))
            for nombre, seccion, pres, variante in trabajos:
                nav.eventos.clear()
                geometria = None
                nav.cmd("Emulation.setDeviceMetricsOverride", width=ancho, height=900, deviceScaleFactor=1, mobile=False)
                nav.cmd("Page.navigate", url=url(a.puerto, seccion))
                t0 = time.time()
                previa = CLAVE_PREVIA.get(seccion) if variante and variante.startswith("cola") else None
                if variante and variante.startswith("tab:"):                 # Validacion: la pagina base (primera pestana) se espera con su clave normal
                    previa = None
                ok, e, motivo, _, completa = esperar(nav, seccion, a.maximo, a.estable, previa)
                if ok and variante and variante.startswith("cola"):          # cola: abre «Cola de cajas»; con fila, elige la primera con un clic real (el panel de detalle es parte del diseno)
                    nav.js(JS_PESTANA)
                    time.sleep(1.5)
                    if variante == "cola_con_fila":
                        caja = nav.js(JS_TABLA)
                        if caja:
                            for tipo in ("mousePressed", "mouseReleased"):
                                nav.cmd("Input.dispatchMouseEvent", type=tipo, x=caja["x"] + 19, y=caja["y"] + 50, button="left", clickCount=1)
                        ok, e, motivo, _, _c = esperar(nav, seccion, a.maximo, a.estable)
                    else:
                        ok, e, motivo, _, _c = esperar(nav, seccion, a.maximo, a.estable, CLAVE_COLA_SIN_FILA)
                if ok and variante and variante.startswith("tab:"):          # Validacion: abre la pestana y espera su texto propio
                    rotulo, texto = variante[4:].split("|", 1)
                    nav.js(JS_PESTANA_ROTULO % json.dumps(rotulo))
                    time.sleep(1.5)
                    clave_tab = {"texto": texto, "conteos": [("[role=tab]", 6)] + ([(".vega-embed", 1)] if rotulo != "Selección" else [("[data-testid=stDataFrame]", 1)])}
                    ok, e, motivo, _, _c = esperar(nav, seccion, a.maximo, a.estable, clave_tab)
                if ok and pres:
                    # clic REAL del raton sobre el interruptor del modo presentacion (al pie de la barra lateral): un label.click() de JavaScript no cambia el estado del interruptor
                    pos = nav.js("(() => { const l = document.querySelector('[data-testid=\"stSidebar\"] [data-testid=\"stCheckbox\"] label'); if (!l) return null; const r = l.getBoundingClientRect(); return JSON.stringify({x: r.left + 18, y: r.top + r.height / 2}); })()")
                    if pos:
                        for tipo in ("mousePressed", "mouseReleased"):
                            nav.cmd("Input.dispatchMouseEvent", type=tipo, x=pos["x"], y=pos["y"], button="left", clickCount=1)
                    t1 = time.time()
                    while time.time() - t1 < 15 and not nav.js("document.documentElement.outerHTML.includes('--escala: 1.18')"):      # el rerun es asincrono: primero se espera el cambio de estilos
                        time.sleep(0.3)
                    ok, e, motivo, _, _c = esperar(nav, seccion, a.maximo, a.estable)
                    if ok and not nav.js("document.documentElement.outerHTML.includes('--escala: 1.18')"):
                        ok, motivo = False, "el modo presentacion no se activo (falta --escala: 1.18)"
                clave_final = (CLAVE_COLA_SIN_FILA if variante == "cola_sin_fila" else
                               ({"texto": variante[4:].split("|", 1)[1], "conteos": [("[role=tab]", 6)] + ([(".vega-embed", 1)] if "Selección|" not in variante else [("[data-testid=stDataFrame]", 1)])} if variante and variante.startswith("tab:") else None))
                if ok:                                                    # ajusta el viewport al alto real del contenido y vuelve a esperar la estabilidad
                    alto = int(min(max(e.get("alto", 900) + 40, 700), 3600))
                    nav.cmd("Emulation.setDeviceMetricsOverride", width=ancho, height=alto, deviceScaleFactor=1, mobile=False)
                    ok, e, motivo, _, _c = esperar(nav, seccion, a.maximo, a.estable, clave_final)
                    alto = int(min(max(e.get("alto", alto) + 40, 700), 3600))
                    geometria = nav.js(JS_GEOMETRIA) if ok else None
                    if ok:
                        nav.cmd("Emulation.setDeviceMetricsOverride", width=ancho, height=alto, deviceScaleFactor=1, mobile=False)
                        time.sleep(0.6)
                listo_en = round(time.time() - t0, 1)
                todos = [x["params"].get("exceptionDetails", {}).get("text") or x["params"].get("entry", {}).get("text") or "" for x in nav.eventos
                         if x.get("method") == "Runtime.exceptionThrown" or (x.get("method") == "Log.entryAdded" and x["params"]["entry"].get("level") == "error")]
                # Streamlit pide /<pagina>/_stcore/health y /host-config relativos a la subruta y recibe 404 (lo resuelve solo): se cuentan aparte, no son errores de la pagina
                internos = [x for x in todos if "status of 404" in x]
                errores = [x for x in todos if x not in internos]
                fallo |= not ok
                resultado.append({"seccion": seccion, "ancho": ancho, "archivo": f"{nombre}_{ancho}.png", "listo": ok, "segundos_hasta_listo": listo_en, "segundos_hasta_completa": completa, "variante": variante, "geometria": geometria, "motivo_si_no": motivo, "estado_final": e,
                                  "errores_consola": errores, "404_internos_de_streamlit": len(internos)})
                if ok and not a.sin_guardar:
                    img = nav.cmd("Page.captureScreenshot", format="png")
                    (destino / f"{nombre}_{ancho}.png").write_bytes(base64.b64decode(img["data"]))
                print(("OK   " if ok else "FALLA"), f"{seccion:24s} {ancho} px  listo en {listo_en} s", motivo, f"errores de consola: {len(errores)}" if errores else "")
    finally:
        nav.cerrar()
    (RAIZ / "data/08_reporting_ep3/capturas_resultado.json").write_text(json.dumps(resultado, indent=1, ensure_ascii=False), encoding="utf-8")
    if fallo:
        sys.exit("ALGUNA CAPTURA NO SE COMPLETO (ver capturas_resultado.json): no se guardo como valida")


if __name__ == "__main__":
    main()
