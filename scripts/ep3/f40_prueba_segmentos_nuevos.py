"""F40: reproduce la prueba con segmentos nuevos reales (los 4 de ``datos_demo/candidatos/``, del split ``validation`` de Waymo v2) con las MISMAS funciones que usa «Puntuar datos nuevos» y guarda
``docs/ep3/prueba_segmentos_nuevos.json``: segmento completo, id abreviado como lo muestra la página, cajas puntuadas, celdas marcadas (con cámara, cajas en rango, afectadas, sin pareja, tasa de pares,
mediana de referencia y umbral) y el sha256 de los dos archivos de entrada de cada segmento. Es una prueba de funcionamiento, no una validación estadística. No cambia ningún parámetro.
Uso: .venv\\Scripts\\python scripts/ep3/f40_prueba_segmentos_nuevos.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "app"))
SALIDA = RAIZ / "docs/ep3/prueba_segmentos_nuevos.json"
BASE = RAIZ / "datos_demo/candidatos"


def sha(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def main() -> int:
    import secciones as S
    from waymo_evaluacion.ep3 import puntuar as P
    from waymo_evaluacion.ep3.app_logica import cargar_datos
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos

    D = cargar_datos(RAIZ / "data/09_app_ep3")
    det = json.loads((RAIZ / "data/06_models_ep3/detector_params_v3.json").read_text(encoding="utf-8"))
    ctx = {"D": D, "rangos": {int(k): tuple(v) for k, v in det["rangos"].items()}}
    art = cargar_artefactos(RAIZ / "data/06_models_ep3")
    segmentos = []
    for carpeta in sorted(p for p in BASE.iterdir() if p.is_dir()):
        f1, f2 = carpeta / "lidar_box.parquet", carpeta / "camera_to_lidar_box_association.parquet"
        lidar, e1 = P.leer_parquet(f1.read_bytes(), f1.name)
        asoc, e2 = P.leer_parquet(f2.read_bytes(), f2.name)
        assert e1 is None and e2 is None, (carpeta.name, e1, e2)
        assert S.validar_lidar_box(lidar) is None and S.validar_asociacion(asoc) is None and P.validar_correspondencia(lidar, asoc) is None
        vista = S._calcular(ctx, art, lidar, asoc, "archivo", (f1.name, f2.name), P.firma_archivo(f1.name, f1.read_bytes()))
        assert vista is not None, carpeta.name
        celdas = []
        for _, r in vista.lista_A.iterrows():
            celdas.append({"camara": str(r["camara"]), "cajas_en_rango": int(r["cajas_en_rango"]), "cajas_afectadas": int(r["cajas_afectadas"]), "tasa_de_pares": float(r["tasa"]),
                           "mediana_de_referencia": float(r["mediana_referencia"]), "umbral": float(r["umbral"])})
        sin_pareja_celdas = int(vista.resumen.get("positivos_en_celdas_con_hueco", 0))
        afectadas = int(vista.resumen.get("cajas_en_celdas_con_hueco", 0))
        segmentos.append({"segmento": carpeta.name, "id_abreviado": "…" + vista.segmento[-6:], "id_12_digitos": vista.segmento, "cajas_puntuadas": int(vista.n_cajas), "celdas_evaluadas": int(vista.n_celdas),
                          "celdas_marcadas": int(len(vista.lista_A)), "cajas_en_celdas_marcadas": afectadas, "sin_pareja_en_celdas_marcadas": sin_pareja_celdas,
                          "porcentaje_sin_pareja_en_celdas": round(sin_pareja_celdas / afectadas, 4) if afectadas else None, "cajas_en_la_cola": int(len(vista.lista_B)), "celdas": celdas,
                          "sha256": {"lidar_box.parquet": sha(f1), "camera_to_lidar_box_association.parquet": sha(f2)}})
    registro = json.loads((BASE / "REGISTRO_DESCARGA.json").read_text(encoding="utf-8")) if (BASE / "REGISTRO_DESCARGA.json").exists() else {}
    out = {"nota": "Prueba de funcionamiento con 4 segmentos nuevos reales, no una validación estadística. Parámetros del detector y de la regla: los congelados de v3 (no se reajustaron).",
           "origen": {"bucket": registro.get("bucket"), "split": registro.get("split")}, "segmentos": segmentos}
    SALIDA.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for s in segmentos:
        print(f"{s['segmento']}  {s['id_abreviado']}  cajas {s['cajas_puntuadas']}  celdas marcadas {s['celdas_marcadas']}  {s['celdas']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
