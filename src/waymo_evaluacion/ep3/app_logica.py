"""Lógica pura de la página de EP3 (sin Streamlit), para poder probarla.

La app lee solo ``data/09_app_ep3`` (predicciones fuera de fold, es decir, honestas) y los artefactos
congelados de ``data/06_models_ep3``. Ningún dato sale del equipo.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

IDENTIFICADORES = ["key.frame_timestamp_micros", "key.laser_object_id"]
CAMARAS = {1: "1 (frontal)", 2: "2 (frontal izq.)", 3: "3 (frontal der.)", 4: "4 (lateral izq.)", 5: "5 (lateral der.)"}
ARCHIVOS = ("cajas_oof.parquet", "celdas.csv", "lista_A.csv", "curva_cola.csv", "kpis.json")
AVISO_EN_MUESTRA = (
    "En muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos. "
    "La ganancia del flujo en dos pasos sale de 2 celdas cámara x segmento, una de ellas en el segmento donde se descubrió el hueco."
)
REFERENCIAS = ("XGB", "E2")
PERFILES = {
    "Analista de revisión": {
        "pregunta": "¿Qué reviso primero y cuánto me cuesta?",
        "seccion": "Cola de revisión",
        "mensaje": "Usted decide qué cajas mirar. La cola le dice por dónde empezar; no reemplaza su criterio.",
    },
    "Responsable de calidad de datos": {
        "pregunta": "¿Qué cámaras o segmentos tienen un problema sistemático?",
        "seccion": "Auditoría de cámaras",
        "mensaje": "Una cámara con tasa de pares muy baja suele ser un problema de etiquetado o de datos, no de cajas sueltas: se atiende aparte.",
    },
    "Ingeniero consumidor de datos": {
        "pregunta": "¿Puedo confiar en las etiquetas 2D de un segmento nuevo?",
        "seccion": "Puntuar datos nuevos",
        "mensaje": "Suba el archivo de un segmento y obtenga la lista de celdas sospechosas y la cola de cajas, todo local.",
    },
}


def cargar_datos(carpeta: Path) -> dict[str, Any]:
    """Lee los archivos de la app. Lanza ``FileNotFoundError`` con la lista de los que faltan."""
    faltan = [a for a in ARCHIVOS if not (carpeta / a).exists()]
    if faltan:
        raise FileNotFoundError(f"faltan archivos en {carpeta}: {', '.join(faltan)}")
    return {
        "cajas": pd.read_parquet(carpeta / "cajas_oof.parquet"),
        "celdas": pd.read_csv(carpeta / "celdas.csv", dtype={"seg": str}),
        "lista_A": pd.read_csv(carpeta / "lista_A.csv", dtype={"segmento": str}),
        "curva": pd.read_csv(carpeta / "curva_cola.csv"),
        "kpis": json.loads((carpeta / "kpis.json").read_text(encoding="utf-8")),
        "clusters": pd.read_csv(carpeta / "clusters.csv") if (carpeta / "clusters.csv").exists() else pd.DataFrame(),
        "evidencia": {p.stem: pd.read_csv(p) for p in sorted((carpeta / "evidencia").glob("*.csv"))} if (carpeta / "evidencia").exists() else {},
    }


def ocultar_identificadores(df: pd.DataFrame, ocultar: bool) -> pd.DataFrame:
    """Modo presentación: quita ``laser_object_id`` y la marca de tiempo."""
    return df.drop(columns=[c for c in IDENTIFICADORES if c in df.columns]) if ocultar else df


def matriz_calor(celdas: pd.DataFrame) -> pd.DataFrame:
    """Formato largo (segmento, cámara, tasa, hueco, n en rango) para el mapa de calor."""
    filas = []
    for r in celdas.itertuples(index=False):
        d = r._asdict()
        for c, nombre in CAMARAS.items():
            filas.append({"seg": d["seg"], "grupo": d["grupo"], "camara": nombre, "tasa": d[f"tasa_c{c}"], "n_rango": d[f"n_rango_c{c}"],
                          "hueco": bool(d[f"hueco_c{c}"])})
    return pd.DataFrame(filas)


def recall_en_presupuesto(curva: pd.DataFrame, solucion: str, presupuesto: float) -> dict[str, float]:
    """Recall esperado (con IC) al revisar la fracción ``presupuesto`` de las cajas, interpolando la curva guardada.

    ``curva`` tiene las columnas ``solucion``, ``presupuesto``, ``recall``, ``lo`` y ``hi``.
    """
    c = curva[curva["solucion"] == solucion].sort_values("presupuesto")
    if c.empty:
        raise KeyError(f"la solución {solucion!r} no está en la curva")
    return {k: float(np.interp(presupuesto, c["presupuesto"], c[k])) for k in ("recall", "lo", "hi")}


def horas_revision(n_cajas: int, segundos_por_caja: float) -> float:
    """Horas de revisión bajo un supuesto editable de segundos por caja (no medido)."""
    return n_cajas * segundos_por_caja / 3600.0


def cola_segmento(cajas: pd.DataFrame, segmento: str | None, presupuesto: float) -> tuple[pd.DataFrame, dict[str, float]]:
    """Cola de un segmento (o de todos) y recall observado al revisar la fracción ``presupuesto``.

    Las cajas de celdas con hueco no entran a la cola: las atiende la auditoría (paso 1).
    """
    d = cajas if segmento in (None, "Todos") else cajas[cajas["seg"] == segmento]
    sana = d[~d["en_hueco"]].sort_values("score", ascending=False, kind="stable")
    n = int(np.ceil(presupuesto * len(sana)))
    top = sana.head(n)
    pos_total = int(d["sin_camara"].sum())
    pos_aud = int(d.loc[d["en_hueco"], "sin_camara"].sum())
    pos_cola = int(top["sin_camara"].sum())
    return top.reset_index(drop=True), {
        "cajas_cola_total": int(len(sana)), "cajas_a_revisar": int(n), "positivos_total": pos_total, "positivos_auditoria": pos_aud, "positivos_en_cola": pos_cola,
        "recall_solo_cola": pos_cola / max(int(sana["sin_camara"].sum()), 1),
        "recall_proceso": (pos_aud + pos_cola) / max(pos_total, 1),
    }


def percentil_en_cola(score: float, cajas: pd.DataFrame) -> float:
    """Posición relativa de un puntaje en la cola de referencia (0 % = primera de la cola, 100 % = última)."""
    ref = cajas.loc[~cajas["en_hueco"], "score"].to_numpy()
    return float((ref > score).mean())


def curva_dependencia(puntuador: Any, base: pd.DataFrame, variable: str, valores: np.ndarray) -> pd.DataFrame:
    """Puntaje del modelo al variar una variable y dejar el resto en los valores de ``base`` (una fila)."""
    X = pd.concat([base] * len(valores), ignore_index=True)
    X[variable] = valores
    return pd.DataFrame({variable: valores, "score": puntuador.puntuar(X)})


def cargar_no_supervisado(carpeta: Path) -> dict[str, Any] | None:
    """Scaler y KMeans del tipo de caso (descriptivo, post hoc). ``None`` si el archivo no existe."""
    ruta = carpeta / "no_supervisado_v3.joblib"
    if not ruta.exists():
        return None
    import joblib

    return joblib.load(ruta)


def tipo_de_caso(fila: pd.DataFrame, art: dict[str, Any]) -> int:
    """Cluster (tipo de caso) de una caja a partir de distancia, azimut, puntos, densidad y volumen (misma transformación que en la fase 13)."""
    X = pd.DataFrame({
        "distancia_m": fila["distancia_m"].to_numpy(float), "azimut_abs_deg": fila["azimut_abs_deg"].to_numpy(float),
        "log_puntos": np.log1p(fila["num_lidar_points"].to_numpy(float)), "log_densidad": np.log1p(fila["densidad_puntos"].to_numpy(float)),
        "log_volumen": np.log1p(fila["volumen_caja"].to_numpy(float)),
    })[art["columnas"]]
    return int(art[f"kmeans_k{art['k_elegido']}"].predict(art["scaler"].transform(X))[0])


def info_tipo_de_caso(cluster: int, clusters: pd.DataFrame) -> dict[str, Any]:
    """Nombre, tasa histórica de ``sin_camara`` e IC 95 % por segmentos de un tipo de caso."""
    if clusters.empty or cluster not in set(clusters["cluster"]):
        return {"tipo_de_caso": "sin información", "tasa": float("nan"), "ic_lo": float("nan"), "ic_hi": float("nan"), "cajas": 0}
    r = clusters[clusters["cluster"] == cluster].iloc[0]
    return {"tipo_de_caso": str(r["tipo_de_caso"]), "tasa": float(r["tasa_sin_camara"]), "ic_lo": float(r["ic_lo"]), "ic_hi": float(r["ic_hi"]), "cajas": int(r["cajas"])}


def curvas_a_mostrar(curva: pd.DataFrame, referencia: str | None) -> pd.DataFrame:
    """Curvas de la cola: las de la solución (sin las referencias) y, si se elige, la del modelo de referencia."""
    es_ref = curva["solucion"].str.contains("(referencia)", regex=False)
    base = curva[~es_ref]
    if referencia in (None, "Ninguno"):
        return base
    return pd.concat([base, curva[es_ref & curva["solucion"].str.startswith(referencia)]], ignore_index=True)
