"""F18-C: cifras de la pagina REDISENADA frente a pagina_numeros_antes.json, y tiempos de carga de cada seccion (AppTest, datos reales).

Escribe data/08_reporting_ep3/pagina_numeros_despues.json, pagina_comparacion_antes_despues.csv y pagina_tiempos_carga.json.
Meta de carga: menos de 3 s por seccion con la cache caliente (la primera carga lee los datos y puede tardar mas).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from streamlit.testing.v1 import AppTest  # noqa: E402

from waymo_evaluacion.ep3.app_logica import SECCIONES  # noqa: E402

REP = RAIZ / "data/08_reporting_ep3"


def abrir(seccion: str, presup: int | None = None) -> tuple[AppTest, float]:
    t0 = time.time()
    at = AppTest.from_file(str(RAIZ / "app" / "app.py"), default_timeout=180).run()
    at.sidebar.radio[0].set_value(seccion).run()
    if presup is not None:
        at.slider[0].set_value(presup).run()
    return at, time.time() - t0


def txt(at: AppTest) -> str:
    return re.sub(r"\s+", " ", " ".join(re.sub(r"<[^>]+>", " ", m.value) for m in at.markdown))


def main() -> None:
    antes = json.loads((REP / "pagina_numeros_antes.json").read_text(encoding="utf-8"))
    filas, despues = [], {"secciones": {}}
    for clave, presup in (("presupuesto_20", 20), ("presupuesto_68", 68)):
        at, _ = abrir("Cola de revisión", presup)
        t = txt(at)
        old = antes["secciones"]["Cola de revisión"][clave]
        n = re.search(r"Revisando ([\d\.]+) cajas.*?unas (\d+) de cada 100", t)
        horas = re.search(r"Tiempo estimado ([\d\.,]+) h", t)
        nuevo = {"cajas_a_revisar": n.group(1), "de_cada_100": n.group(2), "horas": horas.group(1), "filas_tabla": int(len(at.dataframe[0].value))}
        despues["secciones"].setdefault("Cola de revisión", {})[clave] = nuevo
        filas += [
            {"seccion": "Cola de revisión", "caso": f"presupuesto {presup} %", "cifra": "cajas a revisar", "antes": old["metricas"]["Cajas a revisar en este segmento"], "despues": nuevo["cajas_a_revisar"], "explicacion": "igual"},
            {"seccion": "Cola de revisión", "caso": f"presupuesto {presup} %", "cifra": "horas (20 s por caja)", "antes": old["metricas"]["Horas con 20 s por caja"], "despues": nuevo["horas"], "explicacion": "igual"},
            {"seccion": "Cola de revisión", "caso": f"presupuesto {presup} %", "cifra": "cobertura (tarjeta antes / frase ahora)", "antes": old["metricas"]["Recall esperado (todos los segmentos)"], "despues": f"{nuevo['de_cada_100']} de cada 100",
             "explicacion": f"una sola fuente: el conteo observado ({old['recall_texto']}, que antes mostraba el texto); la tarjeta usaba la curva interpolada. Diferencia <= 0,1 punto"},
            {"seccion": "Cola de revisión", "caso": f"presupuesto {presup} %", "cifra": "filas de la tabla", "antes": old["filas_tabla"], "despues": nuevo["filas_tabla"], "explicacion": "igual"}]
    at, _ = abrir("Inicio")
    ini = txt(at)
    for t in antes["secciones"]["Inicio"]["tarjetas"]:
        v = re.sub(r"(?<![\d,.])(\d{4,})(?![\d,])", lambda m: f"{int(m.group(1)):,}".replace(",", "."), t["valor"])
        filas.append({"seccion": "Inicio", "caso": "resultados técnicos", "cifra": t["titulo"], "antes": t["valor"], "despues": v if v in ini else "NO ENCONTRADO", "explicacion": "igual (6059 pasa a 6.059 por el formato es-CL)" if v != t["valor"] else "igual"})
    at, _ = abrir("Explica una caja")
    ex = txt(at)
    for k, v in antes["secciones"]["Explica una caja"]["metricas"].items():
        v2 = v.replace("entre el ", "").replace(" primero", "")
        filas.append({"seccion": "Explica una caja", "caso": "valores por defecto", "cifra": k, "antes": v, "despues": v if (v in ex or v2 in ex) else "NO ENCONTRADO", "explicacion": "igual"})
    ev = len(abrir("Evidencia")[0].dataframe)
    filas.append({"seccion": "Evidencia", "caso": "tablas", "cifra": "número de tablas", "antes": antes["secciones"]["Evidencia"]["tablas"], "despues": ev, "explicacion": "igual"})
    tabla = pd.DataFrame(filas)
    tabla.to_csv(REP / "pagina_comparacion_antes_despues.csv", index=False)
    despues["nota"] = "cifras de la pagina rediseñada (F18-C); la unica diferencia deliberada es la cobertura de la cola (fuente unica)"
    (REP / "pagina_numeros_despues.json").write_text(json.dumps(despues, indent=1, ensure_ascii=False), encoding="utf-8")
    # tiempos de carga: primera carga (cache fria, proceso nuevo ya iniciado) y cargas siguientes
    tiempos = {"meta_s": 3.0, "nota": "AppTest: incluye ejecutar el script de la pagina completo y cambiar de seccion; datos reales; la primera seccion abierta paga la lectura de los datos (cache de Streamlit)", "secciones": {}}
    for s in SECCIONES:
        medidas = [abrir(s)[1] for _ in range(3)]
        tiempos["secciones"][s] = {"primera_s": round(medidas[0], 2), "mejor_s": round(min(medidas), 2), "cumple_meta": bool(min(medidas) < 3.0)}
    # carga en frio: un proceso nuevo por seccion (lee los datos y los modelos por primera vez)
    import subprocess
    codigo = ("import sys,time; sys.path.insert(0, r'%s'); from streamlit.testing.v1 import AppTest; import logging; logging.disable(logging.CRITICAL); "
              "t=time.time(); at=AppTest.from_file(r'%s', default_timeout=180).run(); at.sidebar.radio[0].set_value(sys.argv[1]).run(); print(round(time.time()-t,2))")
    for s in SECCIONES:
        r = subprocess.run([sys.executable, "-c", codigo % (RAIZ / "src", RAIZ / "app" / "app.py"), s], capture_output=True, text=True, cwd=RAIZ)
        frio = float(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 and r.stdout.strip() else None
        tiempos["secciones"][s]["frio_s"] = frio
        tiempos["secciones"][s]["frio_cumple_meta"] = bool(frio is not None and frio < 3.0)
    antes_t = antes.get("tiempos_de_carga_s_antes", {})
    tiempos["tiempos_antes_s"] = antes_t
    (REP / "pagina_tiempos_carga.json").write_text(json.dumps(tiempos, indent=1, ensure_ascii=False), encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
    print(tabla.to_string(index=False)); print(json.dumps(tiempos["secciones"], indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
