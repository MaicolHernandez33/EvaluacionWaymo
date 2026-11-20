"""F19-B9 y F20-P12: mide el arranque en frio de la pagina y el tiempo hasta estar lista de cada seccion (navegador sin interfaz real, no AppTest).

1) lanza ``app/lanzar.py`` (precarga en un hilo + servidor) en un puerto libre y mide hasta que el servidor responde y hasta que termina la precarga;
2) pide PRIMERO «Explica una caja» (el peor caso: carga el modelo) apenas el servidor responde, y luego las 8 secciones con ``capturar_pagina.py --sin-guardar``;
3) repite lo mismo con ``streamlit run app/app.py`` SIN lanzador (la precarga empieza con la primera visita) para comparar.
Meta: ninguna seccion tarda mas de 3 s tras el arranque. Escribe data/08_reporting_ep3/pagina_arranque.json.
F20: el tiempo de cada seccion es ``segundos_hasta_completa`` (cuando la pagina estuvo completa, sin contar la espera de 2 s de estabilidad que pide la captura) y el resultado va a
``pagina_arranque_f20.json`` (``pagina_arranque.json`` queda como la medicion de F19-B, el «antes»).
F21: el resultado va a ``pagina_arranque_f21.json`` (la de F20 queda como el «antes»); la cola y Validacion tienen varias capturas por pagina (con y sin fila, seis pestanas) y de cada
seccion se toma la mas lenta.
Uso: .venv\\Scripts\\python scripts/ep3/f19_medir_arranque.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PY = str(RAIZ / ".venv" / "Scripts" / "python.exe")
PUERTO = 8513
META_S = 3.0


def esperar_salud(t0: float, maximo: float = 90.0) -> float | None:
    while time.time() - t0 < maximo:
        try:
            if urllib.request.urlopen(f"http://localhost:{PUERTO}/_stcore/health", timeout=1).status == 200:
                return round(time.time() - t0, 2)
        except Exception:  # noqa: BLE001
            time.sleep(0.1)
    return None


def capturar(secciones: list[str] | None) -> list[dict]:
    args = [PY, "scripts/ep3/capturar_pagina.py", "--puerto", str(PUERTO), "--anchos", "1400", "--sin-guardar", "--debug", "9444"]
    if secciones:
        args += ["--secciones", *secciones]
    subprocess.run(args, cwd=RAIZ, capture_output=True, text=True)
    return [r for r in json.loads((RAIZ / "data/08_reporting_ep3/capturas_resultado.json").read_text(encoding="utf-8")) if r["seccion"] and not r["archivo"].startswith("09_")]


def escenario(nombre: str, comando: list[str]) -> dict:
    t0 = time.time()
    p = subprocess.Popen(comando, cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    marcas: dict = {}

    def leer():
        for linea in p.stdout:
            if "[precarga] terminada" in linea:
                marcas["precarga_s"] = round(time.time() - t0, 2)
                marcas["precarga_linea"] = linea.strip()

    threading.Thread(target=leer, daemon=True).start()
    try:
        servidor = esperar_salud(t0)
        peor = capturar(["Explica una caja"])                       # primera visita = peor caso
        secciones = capturar(None)
        time.sleep(1)
        out = {"escenario": nombre, "servidor_responde_s": servidor, "precarga_termina_s": marcas.get("precarga_s"), "linea_precarga": marcas.get("precarga_linea"),
               "primera_visita_explica_s": peor[0]["segundos_hasta_completa"] if peor else None,
               "secciones_s": {s: max(r["segundos_hasta_completa"] for r in secciones if r["seccion"] == s) for s in dict.fromkeys(r["seccion"] for r in secciones)},
               "capturas_medidas": len(secciones), "todas_listas": all(r["listo"] for r in secciones)}
        out["maximo_secciones_s"] = max(out["secciones_s"].values()) if out["secciones_s"] else None
        out["secciones_cumplen_3s"] = bool(out["maximo_secciones_s"] is not None and out["maximo_secciones_s"] <= META_S)           # tras la primera visita
        out["primera_visita_cumple_3s"] = bool((out["primera_visita_explica_s"] or 99) <= META_S)                                     # navegador nuevo (sin cache) + servidor recien arrancado
        return out
    finally:
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)


def main() -> None:
    ruta_capturas = RAIZ / "data/08_reporting_ep3/capturas_resultado.json"
    copia = ruta_capturas.read_text(encoding="utf-8") if ruta_capturas.exists() else None          # capturar_pagina.py lo sobrescribe en cada corrida: se restaura al final
    try:
        _medir()
    finally:
        if copia is not None:
            ruta_capturas.write_text(copia, encoding="utf-8")


def _medir() -> None:
    base = ["--server.port", str(PUERTO), "--server.headless", "true", "--server.address", "localhost", "--browser.gatherUsageStats", "false"]
    r = []
    for repeticion in (1, 2):                                      # dos arranques en frio de cada variante, para ver la dispersion
        e1 = escenario("con lanzador (precarga antes de abrir el servidor)", [PY, "app/lanzar.py", *base])
        e2 = escenario("sin lanzador (streamlit run; la precarga empieza con la primera visita)", [PY, "-m", "streamlit", "run", "app/app.py", *base])
        r += [{**e1, "repeticion": repeticion}, {**e2, "repeticion": repeticion}]
    res = {"meta_s": META_S, "nota": "navegador sin interfaz (CDP) en este equipo, con un perfil nuevo en cada medicion (sin cache); 'completa' = el script termino, esta el ultimo elemento clave de la seccion y los conteos de elementos; "
                                      "la primera visita incluye la descarga del frontend de Streamlit por un navegador sin cache y el arranque de la sesion", "escenarios": r}
    (RAIZ / "data/08_reporting_ep3/pagina_arranque_f21.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))
    sys.exit(0 if all(e["secciones_cumplen_3s"] for e in r) else 1)


if __name__ == "__main__":
    main()
