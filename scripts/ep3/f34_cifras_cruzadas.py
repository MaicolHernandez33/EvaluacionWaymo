"""F34, regla 9: las cifras que se repiten entre el Resumen, la Cola y Validación salen de las mismas funciones y coinciden.

Abre las páginas con los datos reales (``AppTest``, sin servidor), calcula cada cifra con la función de ``app_logica`` que la produce y registra en qué páginas aparece y con qué texto exacto. Una cifra que aparece
con otro valor que el de su función cuenta como discrepancia. No cambia nada: escribe ``docs/ep3/f34_cifras_cruzadas.json``.
Uso: .venv\\Scripts\\python scripts/ep3/f34_cifras_cruzadas.py
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
SALIDA = RAIZ / "docs/ep3/f34_cifras_cruzadas.json"
PAGINAS = ["Resumen", "Auditoría de cámaras", "Cola de revisión", "Validación"]


def texto(at) -> str:
    partes = [m.value for m in at.markdown] + [c.value for c in at.caption] + [e.label for e in at.expander]
    for d in at.dataframe:
        partes += d.value.astype(str).to_numpy().ravel().tolist()
    return re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", " ", " ".join(partes), flags=re.S)).replace("\xa0", " ")


def main() -> None:
    from streamlit.testing.v1 import AppTest

    from tests.ep3.test_app import ir_a
    from waymo_evaluacion.ep3 import formato as F
    from waymo_evaluacion.ep3.app_logica import cargar_datos, datos_ciclistas, inicio_resumen

    os.environ.pop("WAYMO_APP_DATA", None)
    os.environ.pop("WAYMO_APP_MODELOS", None)
    D = cargar_datos(RAIZ / "data/09_app_ep3")
    r = inicio_resumen(D)
    ev = D["evidencia"]
    esc = ev["ie12__modelo_escogido"].iloc[0]
    cic = datos_ciclistas(ev.get("posthoc__equidad"))
    claves = {t["titulo"]: t["valor"] for t in D["kpis"]["tarjetas"]}
    esperadas = {
        "AUC 0,823": claves["AUC fuera de fold"],
        "80.571 cajas": F.entero(r["cajas"]),
        "21,2 % sin pareja": F.porcentaje(r["prevalencia"]),
        "peatones 80,6 %": F.porcentaje(cic["peaton"]),
        "ciclistas 44,3 %": F.porcentaje(cic["ciclista"]),
        "358 h sin orden": F.horas(r["horas_sin_orden"], 0),
        "200 h solo cola": F.horas(r["horas_un_paso"], 0),
        "132 h auditoría + cola": F.horas(r["horas_dos_pasos"], 0),
        "61,9 % de captura al revisar el 20 %": F.porcentaje(esc["Captura@20"]),
        "44,6 % de cajas a revisar para el 80 % (un paso)": F.porcentaje(r["fraccion_80_un_paso"]),
        "29,6 % de cajas a revisar para el 80 % (dos pasos)": F.porcentaje(r["fraccion_80_dos_pasos"]),
    }
    at = AppTest.from_file(str(RAIZ / "app" / "app.py"), default_timeout=180).run()
    por_pagina: dict[str, str] = {}
    for p in PAGINAS:
        ir_a(at, p)
        por_pagina[p] = texto(at)
    filas = [{"cifra": n, "valor_de_la_funcion": v, "paginas_donde_aparece": [p for p, t in por_pagina.items() if v in t]} for n, v in esperadas.items()]
    # discrepancias: la misma cifra con otro valor (p. ej. el AUC con otros decimales) en una página
    discrepancias = []
    for p, t in por_pagina.items():
        if "AUC" in t and esperadas["AUC 0,823"] not in t and re.search(r"AUC[^.]{0,40}0,8\d\d", t) and "0,823" not in t:
            discrepancias.append(f"{p}: AUC con otro valor")
    res = {"esperadas": esperadas, "filas": filas, "discrepancias": discrepancias, "sin_aparecer": [f["cifra"] for f in filas if not f["paginas_donde_aparece"]]}
    SALIDA.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
