"""F34, regla 6: exporta TODOS los valores que mostraba Validación antes del rediseño (cada tabla de evidencia tal como la daba ``formato.tabla_legible``, los datos de cada gráfico, las lecturas, los resultados
clave y las cifras de apoyo) a un JSON, para compararlos con lo que muestra la página nueva.

Esas funciones no cambian en F34, así que el archivo se puede regenerar en cualquier momento. Por defecto escribe en ``tests/ep3/datos_f34/valores_antes_validacion.json`` (lo lee
``test_pagina_f34.py``); ``--salida`` permite escribirlo en otra parte (por ejemplo una carpeta temporal fuera del repositorio).
Uso: .venv\\Scripts\\python scripts/ep3/f34_exportar_valores.py [--salida ruta.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3 import formato as F  # noqa: E402
from waymo_evaluacion.ep3.app_logica import cargar_datos, datos_validacion, inicio_resumen, lectura_evidencia, tabla_resultados_clave  # noqa: E402


def exportar(carpeta: Path) -> dict:
    D = cargar_datos(carpeta)
    ev = D["evidencia"]
    tablas = {}
    for k, v in ev.items():
        legible = F.tabla_legible(v, tabla=k)
        tablas[k] = {"columnas": [str(c) for c in legible.columns], "filas": [[str(x) for x in fila] for fila in legible.to_numpy().tolist()]}
    graficos = {k: json.loads(v.to_json(orient="records")) for k, v in datos_validacion(ev).items()}
    r = inicio_resumen(D)
    cifras = {k: (float(v) if isinstance(v, (int, float)) and v is not None else v) for k, v in r.items()}
    return {"tablas": tablas, "graficos": graficos, "lecturas": lectura_evidencia(ev), "resultados_clave": tabla_resultados_clave(D["kpis"]).drop(columns="Fuente").astype(str).to_numpy().tolist(),
            "cifras_resumen": cifras}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--carpeta", default=str(RAIZ / "data/09_app_ep3"))
    ap.add_argument("--salida", default=str(RAIZ / "tests/ep3/datos_f34/valores_antes_validacion.json"))
    a = ap.parse_args()
    out = exportar(Path(a.carpeta))
    destino = Path(a.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    n = sum(len(t["filas"]) * len(t["columnas"]) for t in out["tablas"].values())
    print(f"{len(out['tablas'])} tablas, {n} celdas -> {destino}")


if __name__ == "__main__":
    main()
