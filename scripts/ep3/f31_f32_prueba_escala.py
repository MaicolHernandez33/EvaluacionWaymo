"""F31 a F33: la página con 300 segmentos sintéticos (el real tiene 41). Mide cuánto tarda cada página con ese volumen y comprueba que siguen cargando sin error.

Los datos se generan en un directorio temporal (``escala_sintetica.py``); no se guarda nada en ``data/`` ni se toca el parquet real. Se cargan con ``AppTest`` (la página real, sin servidor) y se
mide cada página en frío (primera vista, con la precarga que hace la página) y en una segunda vista. Escribe ``docs/ep3/f31_f32_escala_sintetica.json``.
Uso: .venv\\Scripts\\python scripts/ep3/f31_f32_prueba_escala.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "app"))
SALIDA = RAIZ / "docs/ep3/f31_f32_escala_sintetica.json"
PAGINAS = ["Resumen", "Auditoría de cámaras", "Cola de revisión", "Explica una caja"]


def main() -> None:
    from streamlit.testing.v1 import AppTest

    from tests.ep3.test_app import _datos_sinteticos, _modelos_sinteticos, ir_a
    from waymo_evaluacion.ep3.app_logica import cargar_datos
    from waymo_evaluacion.ep3.escala_sintetica import cajas_sinteticas, celdas_sinteticas

    res: dict = {"segmentos": 300, "cajas_por_segmento": 40}
    with tempfile.TemporaryDirectory(prefix="escala_f31_") as tmp:
        base = Path(tmp)
        _datos_sinteticos(base / "datos")
        _modelos_sinteticos(base / "modelos")
        t0 = time.time()
        cajas = cajas_sinteticas(300, 40)
        celdas, lista = celdas_sinteticas(300)
        res["generar_datos_s"] = round(time.time() - t0, 2)
        cajas.to_parquet(base / "datos" / "cajas_oof.parquet")
        celdas.to_csv(base / "datos" / "celdas.csv", index=False)
        lista.to_csv(base / "datos" / "lista_A.csv", index=False)
        res["cajas"] = int(len(cajas))
        res["celdas_total"] = int(len(celdas) * 5)
        res["celdas_marcadas"] = int(len(lista))
        t0 = time.time()
        D = cargar_datos(base / "datos")
        res["cargar_datos_s"] = round(time.time() - t0, 2)
        os.environ["WAYMO_APP_DATA"] = str(base / "datos")
        os.environ["WAYMO_APP_MODELOS"] = str(base / "modelos")
        t0 = time.time()
        at = AppTest.from_file(str(RAIZ / "app" / "app.py"), default_timeout=180).run()
        res["primera_carga_s"] = round(time.time() - t0, 2)
        res["errores_primera_carga"] = [str(e.value)[:200] for e in at.exception]
        tiempos: dict = {}
        for pag in PAGINAS:
            medidas = []
            for _ in range(2):
                t0 = time.time()
                ir_a(at, pag)
                medidas.append(round(time.time() - t0, 2))
            tiempos[pag] = {"primera_vista_s": medidas[0], "segunda_vista_s": medidas[1], "errores": [str(e.value)[:200] for e in at.exception]}
            if pag == "Cola de revisión":
                tiempos[pag]["tablas"] = [len(d.value) for d in at.dataframe]
        res["paginas"] = tiempos
        res["todas_sin_error"] = not res["errores_primera_carga"] and all(not v["errores"] for v in tiempos.values())
        res["maximo_s"] = max(max(v["primera_vista_s"], v["segunda_vista_s"]) for v in tiempos.values())
        shutil.rmtree(base, ignore_errors=True)
    SALIDA.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
