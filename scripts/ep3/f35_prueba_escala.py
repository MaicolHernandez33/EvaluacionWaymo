"""F35: tiempos de «Puntuar datos nuevos» con un parquet sintético de unas 100.000 cajas (y con uno de tamaño real, unos 2.000).

El archivo se crea en un directorio temporal (no queda nada en el repositorio) y se procesa con las mismas funciones que la página: lectura del parquet en memoria, ``puntuar_segmento``,
preparación de la cola y formato de la primera página de 50 filas. Escribe ``docs/ep3/f35_escala_sintetica.json``.
Uso: .venv\\Scripts\\python scripts/ep3/f35_prueba_escala.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))
SALIDA = RAIZ / "docs/ep3/f35_escala_sintetica.json"


def medir(n: int, tmp: Path) -> dict:
    from tests.ep3.test_pagina_f35 import _asoc_sintetica, _lidar_sintetico
    from waymo_evaluacion.ep3 import puntuar as P
    from waymo_evaluacion.ep3.app_logica import cargar_rangos
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos, construir_variables, puntuar_segmento
    from waymo_evaluacion.ep3.tablas_estandar import pagina

    modelos = RAIZ / "data/06_models_ep3"
    lidar = _lidar_sintetico(n, segmentos=3 if n > 10_000 else 1)
    ruta, ruta2 = tmp / f"lidar_{n}.parquet", tmp / f"asoc_{n}.parquet"
    lidar.to_parquet(ruta)
    _asoc_sintetica(lidar).to_parquet(ruta2)
    t = {"cajas_en_el_archivo": n, "tamano_archivo_1_mb": round(ruta.stat().st_size / 1024 / 1024, 1), "tamano_archivo_2_mb": round(ruta2.stat().st_size / 1024 / 1024, 1)}
    t0 = time.time()
    df, msg = P.leer_parquet(ruta.read_bytes(), ruta.name)
    asoc, msg2 = P.leer_parquet(ruta2.read_bytes(), ruta2.name)
    t["leer_s"] = round(time.time() - t0, 2)
    assert msg is None and msg2 is None
    t0 = time.time()
    msg3 = P.validar_correspondencia(df, asoc)
    t["validar_correspondencia_s"] = round(time.time() - t0, 2)
    art = cargar_artefactos(modelos)
    t0 = time.time()
    res = puntuar_segmento(df, asoc, art)
    t["puntuar_con_archivo_2_s"] = round(time.time() - t0, 2)
    t0 = time.time()
    az = construir_variables(df)[["segment_id", "key.frame_timestamp_micros", "key.laser_object_id", "az_signed"]]
    cola = P.preparar_cola_vista(res.lista_B, res.cajas, az, cargar_rangos(modelos))
    vista = P.Vista("archivo", str(res.cajas["seg"].iloc[0]), int(res.cajas["seg"].nunique()), res.lista_A, cola, res.lista_B, res.resumen, list(res.advertencias), len(res.cajas), 5, True)
    tabla = P.tabla_cola(vista)
    primera = pagina(tabla.filas, 1, P.POR_PAGINA_COLA)
    t["preparar_y_formatear_primera_pagina_s"] = round(time.time() - t0, 2)
    t0 = time.time()
    tarjetas = P.tarjetas(vista)
    zip_bytes = P.zip_resultados(vista)
    t["tarjetas_y_zip_s"] = round(time.time() - t0, 2)
    t.update({"cajas_puntuadas": int(len(res.cajas)), "filas_de_la_cola": int(tabla.n_filas), "filas_en_la_primera_pagina": len(primera), "celdas_marcadas": int(len(res.lista_A)), "mensaje_de_correspondencia": msg3,
              "tamano_zip_mb": round(len(zip_bytes) / 1024 / 1024, 1), "tarjetas": [x["valor"] for x in tarjetas],
              "total_s": round(t["leer_s"] + t["validar_correspondencia_s"] + t["puntuar_con_archivo_2_s"] + t["preparar_y_formatear_primera_pagina_s"], 2)})
    return t


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="escala_f35_") as tmp:
        salida = {"100000_cajas": medir(100_000, Path(tmp)), "2000_cajas": medir(2_000, Path(tmp))}
    SALIDA.write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(salida, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
