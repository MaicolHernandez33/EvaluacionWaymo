"""F32: compara el orden de la Cola ANTES (el de ``cola_segmento``: por puntaje, con los empates en el orden en que venían) y DESPUÉS (``preparar_cola``: por probabilidad, segmento, objeto y fotograma).

No cambia nada: lee los datos de la página y escribe ``docs/ep3/f32_orden_cola_antes_despues.json`` con, para dos pasos y un paso al 20 %: el número de cajas, si el conjunto es el mismo, los positivos totales
(idénticos) y los positivos reales (sin pareja) que caen entre las primeras 100, 500, 1.000 y 5.000 filas con cada orden.
Uso: .venv\\Scripts\\python scripts/ep3/f32_comparar_orden_cola.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.app_logica import cargar_datos, cargar_rangos, cola_segmento, preparar_cola  # noqa: E402

CLAVE = ["seg", "key.laser_object_id", "key.frame_timestamp_micros"]


def main() -> None:
    D = cargar_datos(RAIZ / "data/09_app_ep3")
    rangos = cargar_rangos(RAIZ / "data/06_models_ep3")
    out: dict = {}
    for flujo in ("dos", "uno"):
        top, _ = cola_segmento(D["cajas"], "Todos", 0.2, flujo)
        antes = top.reset_index(drop=True)
        despues = preparar_cola(top, D["cajas"], rangos).reset_index(drop=True)
        fila: dict = {"cajas": int(len(top)), "positivos_total_antes": int(antes["sin_camara"].sum()), "positivos_total_despues": int(despues["sin_camara"].sum())}
        for n in (100, 500, 1000, 5000):
            fila[f"positivos_en_las_primeras_{n}_antes"] = int(antes["sin_camara"].head(n).sum())
            fila[f"positivos_en_las_primeras_{n}_despues"] = int(despues["sin_camara"].head(n).sum())
        fila["prob_media_primeras_1000_antes"] = round(float(antes["prob_cal"].head(1000).mean()), 4)
        fila["prob_media_primeras_1000_despues"] = round(float(despues["prob_cal"].head(1000).mean()), 4)
        fila["mismo_conjunto"] = set(map(tuple, antes[CLAVE].to_numpy())) == set(map(tuple, despues[CLAVE].to_numpy()))
        out[flujo] = fila
    (RAIZ / "docs/ep3/f32_orden_cola_antes_despues.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
