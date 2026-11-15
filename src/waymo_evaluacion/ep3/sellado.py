"""Validación externa sellada (P9): manifest con sha256, lista de segmentos congelada, candado de una sola evaluación.

Flujo:
  1. ``construir_manifest``  (F6, al congelar v3): sha256 de modelos, umbrales y parámetros del detector.
  2. ``congelar_lista``      (antes de abrir los segmentos nuevos): sha256 de la lista de segmentos y del manifest.
  3. ``evaluar_externo``     (una sola vez): verifica todos los hashes, crea el candado y calcula las comparaciones.
Nada de lo que se calcule aquí se usa para elegir o reajustar nada.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .detector_huecos import detectar_huecos, marcar_cajas_en_hueco, tasa_por_celda
from .inferencia import Artefactos
from .metricas import METRICAS, ConjuntoOOF, RankingDosPasos, ic95, pesos_bootstrap
from .plan import sha256_archivo

ARCHIVOS_CONGELADOS = ("modelo_final_v3.joblib", "umbrales_v3.json", "detector_params_v3.json")


class CandadoError(RuntimeError):
    """La evaluación externa ya se hizo (o los hashes no coinciden)."""


def construir_manifest(carpeta: Path, extras: dict[str, Any] | None = None) -> dict[str, Any]:
    """sha256 de los archivos congelados de ``carpeta`` más información adicional (versiones, notas)."""
    m: dict[str, Any] = {"version": "v3", "creado": time.strftime("%Y-%m-%dT%H:%M:%S"), "sha256": {}}
    for n in ARCHIVOS_CONGELADOS:
        m["sha256"][n] = sha256_archivo(carpeta / n)
    m.update(extras or {})
    return m


def verificar_manifest(carpeta: Path, manifest: dict[str, Any] | None = None) -> list[str]:
    """Lista de discrepancias entre ``manifest_v3.json`` y los archivos actuales (vacía si todo coincide)."""
    m = manifest or json.loads((carpeta / "manifest_v3.json").read_text(encoding="utf-8"))
    mal = []
    for n, h in m["sha256"].items():
        ruta = carpeta / n
        if not ruta.exists():
            mal.append(f"falta {n}")
        elif sha256_archivo(ruta) != h:
            mal.append(f"{n} cambió")
    return mal


def congelar_lista(lista_csv: Path, carpeta_modelos: Path, salida: Path) -> dict[str, Any]:
    """Congela la lista de segmentos nuevos y el manifest v3 en ``salida`` (``manifest_nuevos.json``)."""
    mal = verificar_manifest(carpeta_modelos)
    if mal:
        raise CandadoError("el manifest v3 no coincide: " + "; ".join(mal))
    lista = pd.read_csv(lista_csv, dtype=str)
    if "segment_id" not in lista.columns or lista.empty:
        raise ValueError("la lista debe tener la columna segment_id y al menos un segmento")
    man = {"lista_csv": lista_csv.name, "n_segmentos": int(len(lista)), "sha256_lista": sha256_archivo(lista_csv),
           "sha256_manifest_v3": sha256_archivo(carpeta_modelos / "manifest_v3.json"), "congelado": time.strftime("%Y-%m-%dT%H:%M:%S")}
    salida.write_text(json.dumps(man, indent=1), encoding="utf-8")
    return man


def verificar_sellado(lista_csv: Path, carpeta_modelos: Path, manifest_nuevos: Path) -> None:
    """Falla si cambió la lista, el manifest o algún archivo congelado."""
    man = json.loads(manifest_nuevos.read_text(encoding="utf-8"))
    mal = verificar_manifest(carpeta_modelos)
    if sha256_archivo(lista_csv) != man["sha256_lista"]:
        mal.append("la lista de segmentos cambió")
    if sha256_archivo(carpeta_modelos / "manifest_v3.json") != man["sha256_manifest_v3"]:
        mal.append("manifest_v3.json cambió")
    if mal:
        raise CandadoError("; ".join(mal))


def tomar_candado(ruta: Path, info: dict[str, Any]) -> None:
    """Crea el candado; si ya existe, se niega a continuar."""
    if ruta.exists():
        raise CandadoError(f"la evaluación externa ya se hizo ({ruta.name}). No se repite.")
    ruta.write_text(json.dumps({**info, "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1), encoding="utf-8")


def evaluar_externo(nuevos: pd.DataFrame, art: Artefactos, n_boot: int = 1000, semilla: int = 42) -> dict[str, pd.DataFrame]:
    """Comparaciones de P9 sobre segmentos nuevos: solución vs regla, brazo C vs A y tasa de celdas marcadas del detector (sin verdad externa: no es sensibilidad ni especificidad; DEV-3).

    Args:
        nuevos: tabla ingerida (``seg``, 16 variables, ``sin_camara``, ``en_zona_principal``, ``az_signed``, ``c1``..``c5``).
        art: artefactos congelados.
        n_boot: réplicas de bootstrap por segmentos.
        semilla: semilla del bootstrap.
    """
    det = art.detector
    camaras = sorted(det.rangos or {})
    tasa, nrango = tasa_por_celda(nuevos, det.rangos, camaras)
    huecos = detectar_huecos(tasa, nrango, det.medianas_ref, det.frac, det.min_cajas)
    nuevos = nuevos.copy()
    nuevos["en_hueco"] = marcar_cajas_en_hueco(nuevos, huecos, det.rangos).to_numpy()
    pp = nuevos[nuevos["en_zona_principal"]].reset_index(drop=True)
    y, seg = pp["sin_camara"].to_numpy(), pp["seg"].to_numpy()
    score = art.puntuador.puntuar(pp)
    regla = -pp["num_top_lidar_points"].to_numpy(dtype=float)
    aud = pp["en_hueco"].to_numpy()
    conj = ConjuntoOOF(y, seg, {"solucion": [score], "regla_top": [regla]})
    boot = conj.bootstrap(["solucion", "regla_top"], n_boot, semilla)
    filas = []
    for k in ("solucion", "regla_top"):
        m = conj.metricas(k)
        f = {"metodo": k}
        for j, nom in enumerate(METRICAS):
            lo, hi = ic95(boot[k][:, j])
            f.update({nom: m[j], f"{nom}_lo": lo, f"{nom}_hi": hi})
        filas.append(f)
    dif = {}
    for j, nom in enumerate(METRICAS):
        d = boot["solucion"][:, j] - boot["regla_top"][:, j]
        dif[nom] = {"dif": float(conj.metricas("solucion")[j] - conj.metricas("regla_top")[j]), "lo": ic95(d)[0], "hi": ic95(d)[1]}
    # puntos de operacion con umbrales congelados
    pesos = pesos_bootstrap(conj.seg_codes, n_boot, semilla)[:, conj.seg_codes]
    ops = []
    for et in ("A", "B"):
        fl = score >= art.umbrales[et]
        rec = [((pesos[b] * (fl & (y == 1))).sum() / max((pesos[b] * (y == 1)).sum(), 1e-12)) for b in range(n_boot)]
        pre = [((pesos[b] * (fl & (y == 1))).sum() / max((pesos[b] * fl).sum(), 1e-12)) for b in range(n_boot)]
        ops.append({"punto": et, "umbral": art.umbrales[et], "recall": float((fl & (y == 1)).sum() / max((y == 1).sum(), 1)), "recall_lo": ic95(np.array(rec))[0],
                    "recall_hi": ic95(np.array(rec))[1], "precision": float((fl & (y == 1)).sum() / max(fl.sum(), 1)), "precision_lo": ic95(np.array(pre))[0],
                    "precision_hi": ic95(np.array(pre))[1], "pct_revisar": float(fl.mean())})
    # brazo C vs A
    rc = RankingDosPasos(y, score, conj.tb, aud)
    cel_seg = huecos.sum(axis=1).reindex(conj.segmentos).fillna(0).to_numpy()
    mc, ma = rc.metricas(), conj.metricas("solucion")
    celdas = float(cel_seg.sum())
    brazos = pd.DataFrame([{"Fraccion_80_A": ma[3], "Fraccion_80_C": mc[1], "Captura@20_A": ma[2], "Captura@20_C": mc[0], "celdas_auditadas": int(celdas),
                            "equilibrio_cajas_por_auditoria": float(len(y) * (ma[3] - mc[1]) / celdas) if celdas > 0 else np.nan,
                            "positivos_en_auditoria": int((aud & (y == 1)).sum())}])
    # tasa de celdas marcadas del detector (no hay verdad externa: no se calculan sensibilidad ni especificidad)
    total = int(huecos.size)
    marcadas = int(huecos.to_numpy().sum())
    resp = []
    for b in range(n_boot):
        w = pesos_bootstrap(conj.seg_codes, 1, semilla + 1000 + b)[0]
        sw = pd.Series(w, index=conj.segmentos).reindex(huecos.index).fillna(0).to_numpy()
        resp.append((sw * huecos.sum(axis=1).to_numpy()).sum() / max(sw.sum() * huecos.shape[1], 1e-12))
    falsas = pd.DataFrame([{"celdas_totales": total, "celdas_marcadas": marcadas, "tasa_marcadas": marcadas / max(total, 1),
                            "tasa_lo": ic95(np.array(resp))[0], "tasa_hi": ic95(np.array(resp))[1], "segmentos": int(huecos.shape[0]),
                            "nota": "sin etiqueta de causa: no hay verdad externa: una celda marcada puede ser un hueco real o no; se reporta la tasa de celdas marcadas, no sensibilidad, especificidad ni precision"}])
    return {"metricas": pd.DataFrame(filas), "diferencias": pd.DataFrame(dif).T.reset_index(names="metrica"), "puntos": pd.DataFrame(ops), "brazos": brazos,
            "detector": falsas, "lista_A": pd.DataFrame([{"segmento": s, "camara": f"c{c}", "tasa": float(tasa.loc[s, f"c{c}"]), "cajas_en_rango": int(nrango.loc[s, f"c{c}"])}
                                                          for s in huecos.index for c in camaras if huecos.loc[s, f"c{c}"]])}
