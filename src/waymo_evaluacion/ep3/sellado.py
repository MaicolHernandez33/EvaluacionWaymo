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
    alt = carpeta_modelos / "manifest_alternativas.json"                     # F19-A4b: si hay alternativas congeladas, su manifest también queda sellado
    man["sha256_manifest_alternativas"] = sha256_archivo(alt) if alt.exists() else None
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
    alt = carpeta_modelos / "manifest_alternativas.json"
    esperado = man.get("sha256_manifest_alternativas")
    if esperado is None and alt.exists() and "sha256_manifest_alternativas" in man:
        mal.append("manifest_alternativas.json apareció después de congelar la lista")
    elif esperado is not None and (not alt.exists() or sha256_archivo(alt) != esperado):
        mal.append("manifest_alternativas.json cambió o falta")
    if mal:
        raise CandadoError("; ".join(mal))


def tomar_candado(ruta: Path, info: dict[str, Any]) -> None:
    """Crea el candado (de forma exclusiva); si ya existe, se niega a continuar."""
    if ruta.exists():
        raise CandadoError(f"la evaluación externa ya se hizo ({ruta.name}). No se repite.")
    try:
        with open(ruta, "x", encoding="utf-8") as f:                 # modo exclusivo: dos corridas a la vez no pasan las dos
            f.write(json.dumps({**info, "fecha": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
    except FileExistsError as e:
        raise CandadoError(f"la evaluación externa ya se hizo ({ruta.name}). No se repite.") from e


def evaluar_externo(nuevos: pd.DataFrame, art: Artefactos, n_boot: int = 1000, semilla: int = 42, alternativas: dict[str, Any] | None = None) -> dict[str, pd.DataFrame]:
    """Comparaciones de P9 sobre segmentos nuevos: solución vs regla, brazo C vs A y tasa de celdas marcadas del detector (sin verdad externa: no es sensibilidad ni especificidad; DEV-3).

    Args:
        nuevos: tabla ingerida (``seg``, 16 variables, ``sin_camara``, ``en_zona_principal``, ``az_signed``, ``c1``..``c5``).
        art: artefactos congelados.
        n_boot: réplicas de bootstrap por segmentos.
        semilla: semilla del bootstrap.
        alternativas: puntuadores congelados alternativos (nombre -> objeto con ``puntuar``); si se dan, se agrega la tabla ``alternativas``.

    Nota (F19-A4a): el puntaje de la solución congelada v3 es la propia regla (``PuntuadorRegla``: menos puntos del sensor superior, monótono con ella), así que
    ``solucion`` contra ``regla_top`` da diferencia 0 por construcción. Lo que de verdad se mide es el desempeño de la regla fuera de muestra, su recall y
    precisión con los umbrales A y B congelados, el brazo C contra A, la tasa de celdas marcadas y, si se dan, las alternativas congeladas.
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
    # tasa de celdas marcadas del detector (no hay verdad externa: no se calculan sensibilidad ni especificidad), con DOS denominadores:
    # (1) todas las celdas (segmento x camara) y (2) solo las celdas con >= min_cajas cajas en el rango (en desarrollo: 2 de 111)
    marc_seg = huecos.sum(axis=1).to_numpy().astype(float)
    n_suf = (nrango.reindex(index=huecos.index, columns=huecos.columns) >= det.min_cajas).fillna(False)
    suf_seg = n_suf.sum(axis=1).to_numpy().astype(float)
    todas_seg = np.full(len(huecos), float(huecos.shape[1]))
    nota = ("sin etiqueta de causa: no hay verdad externa: una celda marcada puede ser un hueco real o no; se reporta la tasa de celdas marcadas, no sensibilidad, especificidad ni precision")
    filas_det = []
    for etiqueta, den_seg in (("todas las celdas (segmento x camara)", todas_seg), (f"solo celdas con >= {det.min_cajas} cajas en el rango", suf_seg)):
        resp = []
        for b in range(n_boot):
            w = pesos_bootstrap(conj.seg_codes, 1, semilla + 1000 + b)[0]
            sw = pd.Series(w, index=conj.segmentos).reindex(huecos.index).fillna(0).to_numpy()
            resp.append((sw * marc_seg).sum() / max((sw * den_seg).sum(), 1e-12))
        tot = int(den_seg.sum())
        filas_det.append({"denominador": etiqueta, "celdas_totales": tot, "celdas_marcadas": int(marc_seg.sum()), "tasa_marcadas": float(marc_seg.sum() / max(tot, 1)),
                          "tasa_lo": ic95(np.array(resp))[0], "tasa_hi": ic95(np.array(resp))[1], "segmentos": int(huecos.shape[0]), "nota": nota})
    falsas = pd.DataFrame(filas_det)
    salida = {"metricas": pd.DataFrame(filas), "diferencias": pd.DataFrame(dif).T.reset_index(names="metrica"), "puntos": pd.DataFrame(ops), "brazos": brazos,
              "detector": falsas, "lista_A": pd.DataFrame([{"segmento": s, "camara": f"c{c}", "tasa": float(tasa.loc[s, f"c{c}"]), "cajas_en_rango": int(nrango.loc[s, f"c{c}"])}
                                                            for s in huecos.index for c in camaras if huecos.loc[s, f"c{c}"]])}
    if alternativas:
        salida["alternativas"] = comparar_alternativas(pp, regla, alternativas, n_boot, semilla)
    return salida


def comparar_alternativas(pp: pd.DataFrame, regla: np.ndarray, alternativas: dict[str, Any], n_boot: int, semilla: int) -> pd.DataFrame:
    """Cada alternativa congelada contra la regla: diferencia de AUC y de Fracción para 80 % con IC pareado por segmentos (mismos pesos que ``diferencias``).

    Diferencia = alternativa menos regla. En AUC un valor positivo favorece a la alternativa; en Fracción para 80 % un valor negativo la favorece (revisa menos cajas).
    """
    y, seg = pp["sin_camara"].to_numpy(), pp["seg"].to_numpy()
    puntajes = {n: np.asarray(a.puntuar(pp), dtype=float) for n, a in alternativas.items()}
    conj = ConjuntoOOF(y, seg, {"regla_top": [regla], **{n: [s] for n, s in puntajes.items()}})
    boot = conj.bootstrap(["regla_top", *puntajes], n_boot, semilla)
    filas = []
    for n in puntajes:
        for j, nom in enumerate(METRICAS):
            if nom not in ("AUC", "Fraccion_80"):
                continue
            d = boot[n][:, j] - boot["regla_top"][:, j]
            lo, hi = ic95(d)
            valor, base = float(conj.metricas(n)[j]), float(conj.metricas("regla_top")[j])
            filas.append({"alternativa": n, "metrica": nom, "alternativa_valor": valor, "regla_valor": base, "dif_alternativa_menos_regla": valor - base, "ic_lo": lo, "ic_hi": hi,
                          "excluye_0": bool(lo > 0 or hi < 0), "segmentos": int(len(np.unique(seg))),
                          "nota": "post hoc respecto del plan v3 (DEV-4): alternativas congeladas antes de abrir datos; no cambian la solucion elegida"})
    return pd.DataFrame(filas)



# ======================================================================================================================
# F19-A: ejecución completa de la evaluación externa (el CLI scripts/ep3/evaluar_sellado.py es una capa fina sobre esto)
# ======================================================================================================================
class EntradasFaltantes(CandadoError):
    """Faltan archivos necesarios; se detecta ANTES de tomar el candado."""


NOMBRES_SALIDA = ("metricas", "diferencias", "puntos", "brazos", "detector", "lista_A", "alternativas")


def comprobar_entradas(lista_csv: Path, manifest_nuevos: Path, nuevos_parquet: Path, carpeta_modelos: Path | None = None) -> list[str]:
    """Lista de problemas (mensajes claros, vacía si todo está) con las entradas de la evaluación; no toca nada."""
    faltan = []
    if not lista_csv.exists():
        faltan.append(f"no existe la lista de segmentos: {lista_csv}")
    if not manifest_nuevos.exists():
        faltan.append(f"no existe el manifest de la lista congelada: {manifest_nuevos} (¿corrió «congelar» antes de abrir los datos?)")
    if not nuevos_parquet.exists():
        faltan.append(f"no existe la tabla de segmentos nuevos: {nuevos_parquet} (¿corrió scripts/ep3/ingesta_nuevos.py?)")
    if carpeta_modelos is not None and not (carpeta_modelos / "manifest_v3.json").exists():
        faltan.append(f"no existe manifest_v3.json en {carpeta_modelos}")
    return faltan


def preparar_salidas(res: dict[str, pd.DataFrame]) -> dict[str, bytes]:
    """Contenido (bytes) de cada ``externa_*.csv``, calculado en memoria para conocer su sha256 antes de escribir nada."""
    return {f"externa_{k}.csv": v.to_csv(index=False).encode("utf-8") for k, v in res.items()}


def hashes_de(salidas: dict[str, bytes]) -> dict[str, str]:
    import hashlib

    return {n: hashlib.sha256(b).hexdigest() for n, b in salidas.items()}


def ejecutar_evaluacion(lista_csv: Path, nuevos_parquet: Path, carpeta_modelos: Path, manifest_nuevos: Path, carpeta_salida: Path, candado: Path, ensayo: bool = False,
                        n_boot: int = 1000, alternativas_manifest: Path | None = None) -> dict[str, Any]:
    """Evaluación externa de punta a punta, con el candado tomado lo más tarde posible.

    Orden: (1) comprobar entradas, (2) verificar hashes (lista, manifest v3, modelos y alternativas), (3) mirar si el candado ya existe, (4) calcular TODO en memoria,
    (5) solo si el cálculo terminó bien, tomar el candado con los sha256 de las salidas, (6) escribir las salidas de inmediato. Una falla en (1) a (4) no consume el
    único intento. En modo ``ensayo`` no se toma candado y las salidas van a ``carpeta_salida`` (que no debe ser la real).
    """
    from .inferencia import cargar_artefactos

    problemas = comprobar_entradas(lista_csv, manifest_nuevos, nuevos_parquet, carpeta_modelos)
    if problemas:
        raise EntradasFaltantes("; ".join(problemas))
    verificar_sellado(lista_csv, carpeta_modelos, manifest_nuevos)
    alternativas = None
    man_alt = alternativas_manifest if alternativas_manifest is not None else carpeta_modelos / "manifest_alternativas.json"
    if man_alt.exists():
        from .alternativas import cargar_alternativas, verificar_alternativas

        mal = verificar_alternativas(carpeta_modelos, man_alt)
        if mal:
            raise CandadoError("alternativas congeladas: " + "; ".join(mal))
        alternativas = cargar_alternativas(carpeta_modelos)
    if not ensayo and candado.exists():
        raise CandadoError(f"la evaluación externa ya se hizo ({candado.name}). No se repite.")
    nuevos = pd.read_parquet(nuevos_parquet)
    res = evaluar_externo(nuevos, cargar_artefactos(carpeta_modelos), n_boot=n_boot, alternativas=alternativas)      # si falla, nada se consumió
    salidas = preparar_salidas(res)
    sumas = hashes_de(salidas)
    if not ensayo:
        tomar_candado(candado, {"lista": lista_csv.name, "sha256_lista": sha256_archivo(lista_csv), "sha256_manifest_nuevos": sha256_archivo(manifest_nuevos),
                                "sha256_salidas": sumas, "alternativas": sorted(alternativas) if alternativas else []})
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    for nombre, contenido in salidas.items():
        (carpeta_salida / nombre).write_bytes(contenido)
    return {"resultados": res, "sha256_salidas": sumas, "ensayo": ensayo, "carpeta_salida": carpeta_salida}
