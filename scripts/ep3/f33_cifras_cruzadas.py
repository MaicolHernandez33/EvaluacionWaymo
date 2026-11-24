"""F31 a F33, regla 9: las cifras que se repiten entre páginas salen de las mismas funciones y coinciden.

Abre el Resumen, la Auditoría de cámaras, la Cola de revisión y Explica una caja con los datos reales (``AppTest``, sin servidor), calcula cada cifra con la función de ``app_logica`` que la produce
y comprueba en qué páginas aparece y si el texto de cada página lleva exactamente ese valor. No cambia nada: escribe ``docs/ep3/f33_cifras_cruzadas.json``.
Uso: .venv\\Scripts\\python scripts/ep3/f33_cifras_cruzadas.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "app"))
SALIDA = RAIZ / "docs/ep3/f33_cifras_cruzadas.json"
PAGINAS = ["Resumen", "Auditoría de cámaras", "Cola de revisión", "Explica una caja"]


def texto(at) -> str:
    partes = [m.value for m in at.markdown] + [c.value for c in at.caption] + [e.label for e in at.expander]
    for d in at.dataframe:
        partes += d.value.astype(str).to_numpy().ravel().tolist()
    return re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", " ", " ".join(partes), flags=re.S)).replace("\xa0", " ")


def main() -> None:
    from streamlit.testing.v1 import AppTest

    from tests.ep3.test_app import ir_a
    from waymo_evaluacion.ep3 import formato as F
    from waymo_evaluacion.ep3.app_logica import cargar_datos, resumen_auditoria, resumen_cola

    os.environ.pop("WAYMO_APP_DATA", None)
    os.environ.pop("WAYMO_APP_MODELOS", None)
    D = cargar_datos(RAIZ / "data/09_app_ep3")
    sol = D["kpis"].get("nombre_curva", "solucion")
    r_dos = resumen_cola(D["cajas"], D["curva"], sol, "Todos", 0.2, 20, "dos")
    aud = resumen_auditoria(D["celdas"], D["lista_A"])
    esperadas = {
        "cajas a revisar (20 %, dos pasos)": F.entero(r_dos["cajas_a_revisar"]),
        "70 de cada 100 (dos pasos, en muestra)": F.de_cada_100(r_dos["cobertura_dos"]),
        "62 de cada 100 (un paso, en muestra)": F.de_cada_100(r_dos["cobertura_uno"]),
        "horas estimadas (20 s por caja, supuesto)": F.horas(r_dos["horas"], 1),
        "1.945 cajas afectadas": F.entero(aud["cajas_afectadas"]),
        "1.565 sin pareja": F.entero(aud["sin_pareja"]),
        "21,2 % de las cajas sin pareja (prevalencia, indicador del Resumen)": F.porcentaje(D["kpis"]["prevalencia"]),
        "80,5 % sin pareja entre las cajas afectadas (Auditoría)": F.porcentaje(aud["pct_sin_pareja"], 1),
        "tamaño de la cola (15.726 de 78.626)": F.entero(r_dos["cajas_cola_total"]),
        "4.742 cajas empatadas en la prioridad máxima (Cola y Explica)": F.entero(int((D["cajas"].loc[~D["cajas"]["en_hueco"], "score"] == D["cajas"].loc[~D["cajas"]["en_hueco"], "score"].max()).sum())),
    }
    at = AppTest.from_file(str(RAIZ / "app" / "app.py"), default_timeout=180).run()
    por_pagina: dict[str, str] = {}
    for p in PAGINAS:
        ir_a(at, p)
        por_pagina[p] = texto(at)
    filas = []
    for nombre, valor in esperadas.items():
        if valor is None:
            filas.append({"cifra": nombre, "valor_de_la_funcion": None, "paginas_donde_aparece": [], "ausente_en_todas": True})
            continue
        en = [p for p, t in por_pagina.items() if valor in t]
        filas.append({"cifra": nombre, "valor_de_la_funcion": valor, "paginas_donde_aparece": en})
    res = {"esperadas": esperadas, "filas": filas, "resumen_auditoria": {k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in aud.items()}}
    SALIDA.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
