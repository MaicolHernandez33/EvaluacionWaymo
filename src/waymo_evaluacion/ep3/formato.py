"""Formato de números y textos de la página en español de Chile: miles con punto, decimales con coma. Funciones puras (sin Streamlit).

Ejemplos: ``entero(80571) -> '80.571'``, ``decimal(87.4) -> '87,4'``, ``porcentaje(0.7025) -> '70,3 %'``.
"""
from __future__ import annotations

import math
import re
from typing import Any

NBSP = " "   # espacio normal entre el número y el símbolo %; los estilos usan white-space: nowrap en las cifras


def _num(x: Any) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) or math.isinf(v) else v


def entero(x: Any) -> str:
    """Entero con separador de miles de punto: 80571 -> '80.571'."""
    v = _num(x)
    return "—" if v is None else f"{int(round(v)):,}".replace(",", ".")


def decimal(x: Any, d: int = 1) -> str:
    """Decimal con coma y miles con punto: 1234.5 -> '1.234,5'."""
    v = _num(x)
    if v is None:
        return "—"
    s = f"{v:,.{d}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def porcentaje(x: Any, d: int = 1) -> str:
    """Fracción (0 a 1) como porcentaje: 0.7025 -> '70,3 %' (con espacio no separable)."""
    v = _num(x)
    return "—" if v is None else f"{decimal(100 * v, d)}{NBSP}%"


def porcentaje_valor(x: Any, d: int = 1) -> str:
    """Valor ya expresado en % (12,4 -> '12,4 %')."""
    v = _num(x)
    return "—" if v is None else f"{decimal(v, d)}{NBSP}%"


def horas(x: Any, d: int = 1) -> str:
    v = _num(x)
    return "—" if v is None else f"{decimal(v, d)}{NBSP}h"


def de_cada_100(frac: Any) -> str:
    """0.703 -> '70 de cada 100' (redondeado al entero)."""
    v = _num(frac)
    return "—" if v is None else f"{int(round(100 * v))} de cada 100"


_DICCIONARIO = {
    "seg": "Segmento", "segmento": "Segmento", "grupo": "Grupo", "ubicacion": "Ubicación", "momento": "Momento del día", "camara": "Cámara", "tasa": "Tasa de pares",
    "cajas": "Cajas", "positivos": "Cajas sin pareja", "modelo": "Modelo", "candidato": "Candidato", "ensamble": "Ensamble", "etapa": "Etapa", "veredicto": "Veredicto", "fold": "Fold",
    "k": "Número de grupos (k)", "cluster": "Grupo", "tipo_de_caso": "Tipo de caso", "variable": "Variable", "tramo": "Tramo", "celdas_con_hueco": "Celdas con hueco",
    "segmentos": "Segmentos", "prevalencia": "Proporción sin pareja", "tasa_sin_camara": "Proporción sin pareja", "ic_lo": "IC inferior", "ic_hi": "IC superior",
    "AUC": "AUC", "PR-AUC": "PR-AUC", "ECE_cal": "Error de calibración", "Brier_cal": "Brier", "AUC_min_fold": "AUC mínimo por fold", "AUC_mediana_segmento": "Mediana del AUC por segmento",
    "Captura@20": "Captura al revisar el 20 %", "Fraccion_80": "Fracción de cajas para el 80 %", "recall_A": "Recall en el punto A", "estable": "Estable",
    "mediana": "Mediana", "frac": "Fracción del umbral", "marcadas": "Celdas marcadas", "detecta_los_2": "Marca los 2 de referencia", "falsas_alarmas": "Celdas marcadas además de los 2 de referencia",
}


_ACENTOS = {"hiperparametro": "hiperparámetro", "hiperparametros": "hiperparámetros", "validacion": "validación", "metricas": "métricas", "comparacion": "comparación", "generalizacion": "generalización",
            "seleccion": "selección", "calibracion": "calibración", "evaluacion": "evaluación", "camara": "cámara", "camaras": "cámaras", "posicion": "posición", "ensambles": "ensambles",
            "auc": "AUC", "ep2": "EP2", "ep3": "EP3", "ie9": "IE9", "ie10": "IE10", "ie11": "IE11", "ie12": "IE12", "defecto": "por defecto", "aportan": "aportan", "estabilidad": "estabilidad",
            "umbral": "umbral", "metodo": "método", "analisis": "análisis", "numero": "número", "diferencia": "diferencia", "tamano": "tamaño", "ubicacion": "ubicación", "tasa": "tasa"}


def acentuar(texto: str) -> str:
    """Pone tilde y mayúsculas conocidas a palabras sueltas de un nombre técnico (p. ej. «validacion» -> «validación»)."""
    return " ".join(_ACENTOS.get(w.lower(), w) for w in texto.split(" "))


def titulo_tabla(clave: str) -> str:
    """Título legible de una tabla de evidencia a partir de su nombre de archivo (``ie9__curvas_de_validacion`` -> «Curvas de validación»)."""
    t = acentuar(clave.split("__", 1)[-1].replace("_", " "))
    return t[:1].upper() + t[1:]


def nombre_columna(col: str) -> str:
    """Nombre legible para una columna de datos (nunca se muestra snake_case)."""
    if col in _DICCIONARIO:
        return _DICCIONARIO[col]
    t = col.replace("_lo", " (IC inf.)").replace("_hi", " (IC sup.)").replace("_", " ").strip()
    t = re.sub(r"\s+", " ", t)
    t = acentuar(t.replace("pct ", "% ").replace("num ", "n.° "))
    return t[:1].upper() + t[1:]


def tabla_legible(df: Any, decimales: int = 3) -> Any:
    """Copia de un DataFrame lista para mostrar: nombres legibles y números con formato es-CL (texto; las tablas de evidencia no se reordenan)."""
    import pandas as pd

    out = pd.DataFrame(index=df.index)
    usados: dict[str, int] = {}
    for c in df.columns:
        s = df[c]
        if pd.api.types.is_bool_dtype(s):
            col = s.map({True: "sí", False: "no"})
        elif pd.api.types.is_integer_dtype(s):
            col = s.map(entero)
        elif pd.api.types.is_float_dtype(s):
            enteros = s.dropna().eq(s.dropna().round()).all() and not s.dropna().empty
            col = s.map(entero) if enteros else s.map(lambda v: decimal(v, decimales))
        else:
            col = s.fillna("").astype(str).str.replace("_", " ", regex=False).map(acentuar) if s.dtype == object else s
        nombre = nombre_columna(str(c))
        usados[nombre] = usados.get(nombre, 0) + 1
        out[nombre if usados[nombre] == 1 else f"{nombre} ({usados[nombre]})"] = col
    return out
