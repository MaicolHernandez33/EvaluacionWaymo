"""F36, regla 6: exporta TODOS los textos que muestran hoy «Ética y límites» y «Ayuda y glosario» (párrafos, fichas, uso, glosario, preguntas y respuestas) a un JSON, para la prueba de regresión de textos.

Abre cada página con ``AppTest`` (los datos reales de la página, sin servidor), junta lo que se ve (markdown, expanders con su contenido, tablas) y lo guarda como una lista de bloques y como una lista de frases.
Por defecto escribe ``tests/ep3/datos_f36/textos_antes.json`` (lo lee ``test_pagina_f36.py``); ``--salida`` permite escribirlo en otra parte (por ejemplo una carpeta temporal fuera del repositorio).
Uso: .venv\\Scripts\\python scripts/ep3/f36_exportar_textos.py [--salida ruta.json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "app"))
PAGINAS = ("Ética y límites", "Ayuda y glosario")


def limpiar(t: str) -> str:
    t = re.sub(r"<style>.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t).replace("\xa0", " ").replace("**", "")
    return re.sub(r"\s+", " ", t).strip()


def frases(bloque: str) -> list[str]:
    """Frases de un bloque (se corta en «. » y se conservan los signos); sirve para comprobar que cada frase de antes sigue en la página."""
    partes = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡«(])", bloque)
    return [p.strip() for p in partes if len(p.strip()) > 2]


def exportar() -> dict:
    from streamlit.testing.v1 import AppTest

    from tests.ep3.test_app import ir_a

    os.environ.pop("WAYMO_APP_DATA", None)
    os.environ.pop("WAYMO_APP_MODELOS", None)
    os.environ.pop("EP3_ENTORNO", None)
    at = AppTest.from_file(str(RAIZ / "app" / "app.py"), default_timeout=180).run()
    out: dict = {}
    for p in PAGINAS:
        ir_a(at, p)
        bloques = [limpiar(m.value) for m in at.markdown] + [limpiar(c.value) for c in at.caption] + [limpiar(e.label) for e in at.expander]
        for t in at.table:
            bloques += [limpiar(str(c)) for c in t.value.columns] + [limpiar(str(x)) for x in t.value.to_numpy().ravel()]
        for e in at.expander:
            bloques += [limpiar(m.value) for m in e.markdown]
        bloques = [b for b in dict.fromkeys(bloques) if b]
        out[p] = {"bloques": bloques, "frases": [f for b in bloques for f in frases(b)]}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=str(RAIZ / "tests/ep3/datos_f36/textos_antes.json"))
    a = ap.parse_args()
    datos = exportar()
    destino = Path(a.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, indent=1, ensure_ascii=False), encoding="utf-8")
    print({p: (len(v["bloques"]), len(v["frases"])) for p, v in datos.items()}, "->", destino)


if __name__ == "__main__":
    main()
