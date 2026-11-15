"""Selección de segmentos nuevos para la validación externa (F18-B). Funciones PURAS (sin red, sin bucket, sin escribir archivos).

El notebook `notebooks/00b_seleccion_segmentos_ep3.ipynb` (Colab) incluye el código fuente de estas mismas funciones (se copia con `inspect.getsource`;
una prueba comprueba que coinciden) y `docs/ep3/plan_seleccion_ep3.json` guarda el orden de candidatos que producen, calculado SIN descargar nada
con `docs/seleccion_segmentos/inventario_segmentos.csv` y `registro_verificacion_ep2.csv`. La elección usa solo metadatos y se declara antes de abrir datos.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd

SEMILLA = 42
MIN_FRAMES = 190                        # igual que el 00b de EP2
PERCENTILES_DETECCIONES = (2.5, 97.5)   # se calculan sobre los segmentos que pasan los filtros anteriores (igual que EP2)
MIN_ASOCIACIONES = 50
MIN_POSITIVOS = 30                      # igual que EP2 (motivo «pocos positivos»)
MIN_TASA_ETIQUETADA = 5.5               # % de cajas LiDAR de frames etiquetados con par de cámara
META_UTILES = 15
TOPE_EVALUACIONES = 55
# cuotas de segmentos ÚTILES por estrato (time_of_day, location); Night / location_other no tiene candidatos
CUOTAS: dict[tuple[str, str], int] = {
    ("Day", "location_sf"): 8, ("Day", "location_phx"): 4, ("Day", "location_other"): 2,
    ("Night", "location_sf"): 3, ("Night", "location_phx"): 2,
    ("Dawn/Dusk", "location_sf"): 3, ("Dawn/Dusk", "location_phx"): 3, ("Dawn/Dusk", "location_other"): 1,
}


def nombre_estrato(tod: str, loc: str) -> str:
    return f"{tod} / {loc}"


def embudo(inventario: pd.DataFrame, evaluados_ep2: Iterable[str]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Pool elegible como en el 00b de EP2 y SOLO DESPUÉS se excluyen los segmentos que EP2 ya evaluó.

    Pasos: sin lluvia -> al menos MIN_FRAMES frames -> n_detecciones entre los percentiles (calculados sobre el resultado del paso anterior)
    -> se excluyen los evaluados por EP2. (El paso «existe lidar_box y asociación» de EP2 depende del bucket: el notebook lo cuenta en Colab.)
    """
    pasos: dict[str, Any] = {"inventario": int(len(inventario))}
    c = inventario[inventario["weather"] != "rain"]
    pasos["sin_lluvia"] = int(len(c))
    c = c[c["n_frames"] >= MIN_FRAMES]
    pasos[f"n_frames_>={MIN_FRAMES}"] = int(len(c))
    bajo, alto = c["n_detecciones"].quantile([PERCENTILES_DETECCIONES[0] / 100, PERCENTILES_DETECCIONES[1] / 100])
    pool = c[(c["n_detecciones"] >= bajo) & (c["n_detecciones"] <= alto)]
    pasos["n_detecciones_entre_percentiles"] = int(len(pool))
    pasos["limite_inferior_detecciones"] = float(bajo)
    pasos["limite_superior_detecciones"] = float(alto)
    ev = set(evaluados_ep2)
    pasos["evaluados_ep2_dentro_del_pool"] = int(pool["segment_id"].isin(ev).sum())
    candidatos = pool[~pool["segment_id"].isin(ev)].copy()
    pasos["candidatos_sin_los_evaluados_por_ep2"] = int(len(candidatos))
    return candidatos, pasos


def orden_por_estrato(candidatos: pd.DataFrame, cuotas: dict[tuple[str, str], int] = CUOTAS, semilla: int = SEMILLA) -> dict[str, list[str]]:
    """Orden aleatorio fijo de los candidatos de cada estrato: ids ordenados y permutados con ``default_rng(semilla)`` (un generador nuevo por estrato,
    así cambiar la cuota de un estrato no altera el orden de los demás)."""
    out: dict[str, list[str]] = {}
    for (tod, loc) in cuotas:
        ids = sorted(candidatos.loc[(candidatos["time_of_day"] == tod) & (candidatos["location"] == loc), "segment_id"])
        out[nombre_estrato(tod, loc)] = [str(s) for s in np.random.default_rng(semilla).permutation(np.array(ids, dtype=object))] if ids else []
    return out


def decidir(m: dict[str, Any]) -> tuple[str, str]:
    """Aplica los criterios de «segmento útil» (mismos que EP2) a las métricas medidas de un candidato.

    ``m``: ``asoc_filas``, ``lidar_disponible`` (bool), ``positivos`` (cajas LiDAR con par de cámara) y ``tasa_etiquetado_pct``.
    Devuelve ``(resultado, motivo)``; resultado es «util» o «descartado».
    """
    if m.get("asoc_filas", 0) == 0:
        return "descartado", "asociacion vacia"
    if m["asoc_filas"] < MIN_ASOCIACIONES:
        return "descartado", f"pocas asociaciones ({m['asoc_filas']} < {MIN_ASOCIACIONES})"
    if not m.get("lidar_disponible", True):
        return "descartado", "lidar_box no disponible"
    if m.get("positivos", 0) == 0:
        return "descartado", "las asociaciones no cruzan con lidar_box"
    if m["positivos"] < MIN_POSITIVOS:
        return "descartado", f"pocos positivos ({m['positivos']} < {MIN_POSITIVOS})"
    if m["tasa_etiquetado_pct"] < MIN_TASA_ETIQUETADA:
        return "descartado", f"etiquetado ralo ({m['tasa_etiquetado_pct']:.1f}% < {MIN_TASA_ETIQUETADA}% en frames etiquetados)"
    return "util", ""


def seleccionar(orden: dict[str, list[str]], cuotas: dict[tuple[str, str], int], evaluar: Callable[[str], dict[str, Any]],
                tope: int = TOPE_EVALUACIONES, previos: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Evaluación secuencial por estrato, en el orden aleatorio fijo, hasta completar la cuota o agotar el estrato, con un tope global de evaluaciones.

    Los estratos se recorren por rondas (un candidato de cada estrato no completo por ronda, en el orden de ``cuotas``) para que el tope global no
    deje sin evaluar a los últimos estratos; dentro de cada estrato el orden es secuencial. ``previos`` permite reanudar (segmento -> registro ya medido).
    Devuelve el registro de evaluaciones (cada fila con ``segment_id``, ``estrato``, ``resultado`` y ``motivo``).
    """
    previos = previos or {}
    claves = [nombre_estrato(*h) for h in cuotas]
    cuota = {nombre_estrato(*h): q for h, q in cuotas.items()}
    util = {k: 0 for k in claves}
    pos = {k: 0 for k in claves}
    registro: list[dict[str, Any]] = []
    while len(registro) < tope:
        avanzo = False
        for k in claves:
            if len(registro) >= tope:
                break
            if util[k] >= cuota[k] or pos[k] >= len(orden.get(k, [])):
                continue
            seg = orden[k][pos[k]]
            pos[k] += 1
            r = dict(previos[seg]) if seg in previos else dict(evaluar(seg))
            r.update(segment_id=seg, estrato=k)
            registro.append(r)
            avanzo = True
            if r["resultado"] == "util":
                util[k] += 1
        if not avanzo:
            break
    return registro


def resumen_cuotas(registro: list[dict[str, Any]], cuotas: dict[tuple[str, str], int], orden: dict[str, list[str]]) -> pd.DataFrame:
    """Por estrato: cuota, evaluados, útiles, faltan, candidatos que quedaron sin evaluar y la razón (cuota completa / estrato agotado / tope global)."""
    filas = []
    for h, q in cuotas.items():
        k = nombre_estrato(*h)
        ev = [r for r in registro if r["estrato"] == k]
        u = sum(r["resultado"] == "util" for r in ev)
        quedan = len(orden.get(k, [])) - len(ev)
        razon = "cuota completa" if u >= q else ("estrato agotado" if quedan <= 0 else "tope global de evaluaciones")
        filas.append({"estrato": k, "cuota": q, "candidatos_en_el_estrato": len(orden.get(k, [])), "evaluados": len(ev), "utiles": u, "faltan": max(q - u, 0), "razon": razon})
    return pd.DataFrame(filas)


def construir_plan(inventario: pd.DataFrame, evaluados_ep2: Iterable[str], hashes_fuentes: dict[str, str] | None = None) -> dict[str, Any]:
    """Plan de selección pre-declarado: parámetros, cuotas, embudo y el orden de candidatos por estrato (sin descargar nada)."""
    cand, pasos = embudo(inventario, evaluados_ep2)
    orden = orden_por_estrato(cand)
    return {
        "version": "plan_seleccion_ep3_v1",
        "nota": "Elección con solo metadatos (inventario y registro de EP2); declarada antes de abrir datos. No usa sin_camara.",
        "parametros": {"semilla": SEMILLA, "min_frames": MIN_FRAMES, "percentiles_detecciones": list(PERCENTILES_DETECCIONES), "min_asociaciones": MIN_ASOCIACIONES, "min_positivos": MIN_POSITIVOS,
                       "min_tasa_etiquetada_pct": MIN_TASA_ETIQUETADA, "meta_utiles": META_UTILES, "tope_evaluaciones": TOPE_EVALUACIONES,
                       "generador": "numpy.random.default_rng(42).permutation(ids ordenados), un generador nuevo por estrato",
                       "recorrido": "por rondas entre estratos no completos; secuencial dentro de cada estrato"},
        "cuotas_utiles": {nombre_estrato(*h): q for h, q in CUOTAS.items()},
        "total_cuota": int(sum(CUOTAS.values())),
        "embudo": pasos,
        "candidatos_por_estrato": {k: len(v) for k, v in orden.items()},
        "orden_por_estrato": orden,
        "fuentes_sha256": hashes_fuentes or {},
    }
