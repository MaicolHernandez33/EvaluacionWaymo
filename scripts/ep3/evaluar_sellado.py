"""Evaluacion externa sellada (P9). Se ejecuta UNA sola vez; se niega a correr una segunda.

Pasos (con segmentos nuevos; detalle en docs/ep3/GUIA_VALIDACION_EXTERNA.md):
  1) congelar:  python scripts/ep3/evaluar_sellado.py congelar --lista segmentos_nuevos_ep3.csv
     Verifica el manifest v3 y escribe data/06_models_ep3/manifest_nuevos.json con el sha256 de la lista, del manifest v3 y (si existe) del manifest de las alternativas.
     Debe hacerse ANTES de ingerir u abrir los segmentos nuevos. Se niega a sobrescribir un manifest_nuevos.json existente.
  2) evaluar:   python scripts/ep3/evaluar_sellado.py evaluar --lista segmentos_nuevos_ep3.csv
     Comprueba (con mensajes claros y ANTES de tomar el candado) que existen la lista, manifest_nuevos.json y data/05_model_input_ep3/nuevos.parquet; verifica todos los
     hashes; calcula TODO en memoria; solo si el calculo termino bien toma el candado (data/08_reporting_ep3/evaluacion_externa.lock) y escribe de inmediato
     data/08_reporting_ep3/externa_*.csv, guardando sus sha256 dentro del candado. Una falla antes de tomar el candado NO consume el unico intento.
  3) ensayo:    python scripts/ep3/evaluar_sellado.py evaluar --ensayo --lista L --manifest M --entrada N.parquet [--salida CARPETA]
     No toma candado, no lee ni sobrescribe el manifest_nuevos.json real y escribe en data/08_reporting_ep3/ensayo_externa/ (o en --salida).

Que se mide con segmentos nuevos (no hay verdad externa sobre cuales celdas son huecos reales; DEV-3):
  (i)   la tasa de celdas marcadas por el detector, con DOS denominadores (todas las celdas segmento x camara, y solo las celdas con >= 100 cajas en el rango;
        en desarrollo: 2 de 111), cada una con su IC por segmentos (externa_detector.csv),
  (ii)  su estabilidad frente a las 30 combinaciones de parametros del detector (se compara el conjunto marcado, no una «precision»),
  (iii) OPCIONAL y post hoc, solo si Waymo v2 trae el componente camera_box: en cada celda marcada, ver si esa camara tiene cajas 2D en el rango
        de azimut sin pares (laguna de asociacion) o no tiene ninguna (laguna de etiquetado o de datos). Ver docs/ep3/GUIA_VALIDACION_EXTERNA.md.
No se calculan sensibilidad ni especificidad del detector.

SOLUCION CONTRA REGLA (F19-A4a): el puntaje de la solucion congelada v3 es la propia regla «menos puntos del sensor superior» (PuntuadorRegla, monotono con ella),
asi que externa_diferencias.csv (solucion menos regla) da 0 POR CONSTRUCCION. Lo que se mide: el desempeno de la regla fuera de muestra (externa_metricas.csv),
su recall y precision con los umbrales A = 32 y B = 11 congelados (externa_puntos.csv), el brazo C contra A (externa_brazos.csv), la tasa de celdas marcadas y, si
existen, las alternativas congeladas LR3 y XGBoost contra la regla (externa_alternativas.csv; DEV-4, post hoc respecto del plan v3).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.plan import verificar_plan_v3  # noqa: E402
from waymo_evaluacion.ep3.sellado import CandadoError, congelar_lista, ejecutar_evaluacion  # noqa: E402

MOD = RAIZ / "data/06_models_ep3"
REP = RAIZ / "data/08_reporting_ep3"
NUEVOS = RAIZ / "data/05_model_input_ep3/nuevos.parquet"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["congelar", "evaluar"])
    ap.add_argument("--lista", required=True, type=Path)
    ap.add_argument("--ensayo", action="store_true", help="evaluar sin tomar candado ni tocar el manifest real (exige --manifest)")
    ap.add_argument("--manifest", type=Path, help="manifest_nuevos.json alternativo (obligatorio con --ensayo)")
    ap.add_argument("--entrada", type=Path, help="parquet de segmentos nuevos alternativo (por defecto data/05_model_input_ep3/nuevos.parquet)")
    ap.add_argument("--salida", type=Path, help="carpeta de salida del ensayo (por defecto data/08_reporting_ep3/ensayo_externa)")
    ap.add_argument("--modelos", type=Path, default=MOD, help="carpeta con la solucion congelada (por defecto data/06_models_ep3)")
    ap.add_argument("--n-boot", type=int, default=1000)
    a = ap.parse_args(argv)
    verificar_plan_v3(RAIZ)
    real = a.modelos / "manifest_nuevos.json"
    try:
        if a.accion == "congelar":
            destino = a.manifest or real
            if destino.exists() and not a.ensayo:
                sys.exit(f"DETENIDO: ya existe {destino}; la lista ya se congelo y no se vuelve a congelar.")
            man = congelar_lista(a.lista, a.modelos, destino)
            print("Lista congelada en", destino, ":", man)
            return
        if a.ensayo:
            if a.manifest is None:
                sys.exit("DETENIDO: con --ensayo hay que indicar --manifest (el ensayo no usa el manifest_nuevos.json real).")
            if a.manifest.resolve() == real.resolve():
                sys.exit("DETENIDO: --manifest apunta al manifest_nuevos.json real; use otro archivo para el ensayo.")
            salida = a.salida or REP / "ensayo_externa"
            if salida.resolve() == REP.resolve():
                sys.exit("DETENIDO: la salida del ensayo no puede ser data/08_reporting_ep3 (ahi van las salidas reales).")
            manifest, candado = a.manifest, REP / "evaluacion_externa.lock"
        else:
            manifest, salida, candado = a.manifest or real, REP, REP / "evaluacion_externa.lock"
        out = ejecutar_evaluacion(a.lista, a.entrada or NUEVOS, a.modelos, manifest, salida, candado, ensayo=a.ensayo, n_boot=a.n_boot)
    except CandadoError as e:
        sys.exit(f"DETENIDO: {e}")
    print("ENSAYO (no se tomo candado)" if a.ensayo else "EVALUACION REAL (candado tomado)", "| salidas en", out["carpeta_salida"])
    for k, v in out["resultados"].items():
        print(f"\n== {k}\n{v.round(4).to_string(index=False)}")


if __name__ == "__main__":
    main()
