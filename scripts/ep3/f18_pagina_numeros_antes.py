"""F18-C (previo): captura las cifras clave que muestra CADA seccion de la pagina ANTES del rediseno y las guarda en
data/08_reporting_ep3/pagina_numeros_antes.json. Se corre una sola vez, con el app/app.py original (usa streamlit.testing.v1.AppTest).
Despues del rediseno, tests/ep3/test_pagina_cifras.py compara las cifras nuevas con este archivo (solo cambia el redondeo unificado, que se documenta alli).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from streamlit.testing.v1 import AppTest  # noqa: E402

SALIDA = RAIZ / "data/08_reporting_ep3/pagina_numeros_antes.json"
SECC = ["Inicio", "Auditoría de cámaras", "Cola de revisión", "Explica una caja", "Evidencia", "Ética y límites", "Puntuar datos nuevos"]


def abrir(seccion: str) -> AppTest:
    at = AppTest.from_file(str(RAIZ / "app" / "app.py"), default_timeout=180).run()
    at.sidebar.radio[0].set_value(seccion).run()
    return at


def main() -> None:
    if SALIDA.exists():
        raise SystemExit("ya existe pagina_numeros_antes.json (se captura una sola vez, con la pagina original)")
    out: dict = {"nota": "cifras que mostraba la pagina original (app/app.py antes de F18-C), capturadas con AppTest, perfil por defecto, modo presentacion apagado", "secciones": {}}
    t = {}
    t0 = time.time(); at = abrir("Inicio"); t["Inicio"] = time.time() - t0
    out["secciones"]["Inicio"] = {"tarjetas": [{"titulo": m.label, "valor": m.value} for m in at.metric]}
    t0 = time.time(); at = abrir("Auditoría de cámaras"); t["Auditoría de cámaras"] = time.time() - t0
    out["secciones"]["Auditoría de cámaras"] = {"tablas": [{"filas": int(len(d.value))} for d in at.dataframe]}
    for nombre, presup in (("presupuesto_20", 20), ("presupuesto_68", 68)):
        t0 = time.time(); at = abrir("Cola de revisión")
        if presup != 20:
            at.slider[0].set_value(presup).run()
        t[f"Cola de revisión {presup}"] = time.time() - t0
        txt = next(m.value for m in at.markdown if "proceso completo" in m.value)
        nums = re.findall(r"([\d\.]+) de ([\d\.]+) cajas sin pareja \(([\d,]+) %\)", txt)[0]
        out["secciones"].setdefault("Cola de revisión", {})[nombre] = {"metricas": {m.label: m.value for m in at.metric}, "hallados": nums[0], "positivos_total": nums[1], "recall_texto": nums[2] + " %", "filas_tabla": int(len(at.dataframe[0].value))}
    t0 = time.time(); at = abrir("Explica una caja"); t["Explica una caja"] = time.time() - t0
    out["secciones"]["Explica una caja"] = {"metricas": {m.label: m.value for m in at.metric}}
    t0 = time.time(); at = abrir("Evidencia"); t["Evidencia"] = time.time() - t0
    out["secciones"]["Evidencia"] = {"tablas": int(len(at.dataframe)), "filas_por_tabla": [int(len(d.value)) for d in at.dataframe]}
    t0 = time.time(); at = abrir("Ética y límites"); t["Ética y límites"] = time.time() - t0
    t0 = time.time(); at = abrir("Puntuar datos nuevos"); t["Puntuar datos nuevos"] = time.time() - t0
    out["tiempos_de_carga_s_antes"] = {k: round(v, 2) for k, v in t.items()}
    SALIDA.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
