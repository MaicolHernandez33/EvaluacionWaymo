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
    if s.startswith("-") and float(s.replace(",", "")) == 0:      # «-0,000» (negativo que se redondea a cero) es engañoso: se muestra «0,000»
        s = s[1:]
    return s.replace(",", "\ue000").replace(".", ",").replace("\ue000", ".")


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
    "cajas": "Cajas", "positivos": "Cajas sin pareja", "modelo": "Modelo", "candidato": "Candidato", "ensamble": "Ensamble", "etapa": "Etapa", "veredicto": "Veredicto", "fold": "Pliegue",
    "k": "Número de grupos (k)", "cluster": "Grupo", "tipo_de_caso": "Tipo de caso", "variable": "Variable", "tramo": "Tramo", "celdas_con_hueco": "Celdas con hueco",
    "segmentos": "Segmentos", "prevalencia": "Proporción sin pareja", "tasa_sin_camara": "Proporción sin pareja", "ic_lo": "IC inferior", "ic_hi": "IC superior",
    "AUC": "AUC", "PR-AUC": "PR-AUC", "ECE_cal": "Error de calibración", "Brier_cal": "Brier", "AUC_min_fold": "AUC mínimo por pliegue", "AUC_mediana_segmento": "Mediana del AUC por segmento",
    "Captura@20": "Captura al revisar el 20 %", "Fraccion_80": "Fracción de cajas para el 80 %", "recall_A": "Recall en el punto A", "estable": "Estable",
    "mediana": "Mediana", "frac": "Fracción del umbral", "marcadas": "Celdas marcadas", "detecta_los_2": "Marca los 2 de referencia", "falsas_alarmas": "Celdas marcadas además de los 2 de referencia (sin verdad externa)",
}


_ACENTOS = {"hiperparametro": "hiperparámetro", "hiperparametros": "hiperparámetros", "validacion": "validación", "metricas": "métricas", "comparacion": "comparación", "generalizacion": "generalización",
            "seleccion": "selección", "calibracion": "calibración", "evaluacion": "evaluación", "camara": "cámara", "camaras": "cámaras", "posicion": "posición", "ensambles": "ensambles",
            "auc": "AUC", "ep2": "EP2", "ep3": "EP3", "ie9": "IE9", "ie10": "IE10", "ie11": "IE11", "ie12": "IE12", "defecto": "por defecto", "aportan": "aportan", "estabilidad": "estabilidad",
            "umbral": "umbral", "metodo": "método", "analisis": "análisis", "numero": "número", "diferencia": "diferencia", "tamano": "tamaño", "ubicacion": "ubicación", "tasa": "tasa", "fraccion": "fracción", "atipicos": "atípicos", "atipicas": "atípicas", "fold": "pliegue", "folds": "pliegues", "seleccion": "selección", "platt": "Platt", "lidar": "LiDAR", "azimut": "azimut"}


def traducir_folds(texto: str) -> str:
    """«fold» y «folds» (inglés) pasan a «pliegue» y «pliegues» en los textos que se muestran (F20-P7); conserva la mayúscula inicial."""
    def rep(m: "re.Match[str]") -> str:
        w = "pliegues" if m.group(0).lower().endswith("s") else "pliegue"
        return w.capitalize() if m.group(0)[0].isupper() else w

    return re.sub(r"\bfolds?\b", rep, texto, flags=re.IGNORECASE)


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
    t = col.replace("_lo", " (IC inf.)").replace("_hi", " (IC sup.)").replace("_def", " por defecto").replace("_opt", " optimizado").replace("_", " ").strip()
    t = re.sub(r"\s+", " ", t)
    t = acentuar(t.replace("pct ", "% ").replace("num ", "n.° "))
    return t[:1].upper() + t[1:]


HIPERPARAMETROS = {
    "C": "C (regularización: menor = más)", "max_depth": "Profundidad máxima", "min_samples_leaf": "Mínimo de muestras por hoja", "max_features": "Variables por división", "max_leaf_nodes": "Máximo de hojas",
    "max_iter": "Iteraciones máximas", "l2_regularization": "Regularización L2", "learning_rate": "Tasa de aprendizaje", "n_estimators": "Número de árboles", "min_child_weight": "Peso mínimo por hoja",
    "reg_lambda": "Regularización lambda", "subsample": "Proporción de filas por árbol", "colsample_bytree": "Proporción de variables por árbol", "num_leaves": "Número de hojas",
    "min_child_samples": "Mínimo de muestras por hoja", "class_weight": "Ponderación de clases", "variables": "Conjunto de variables",
}
VALORES_TEXTO = {"principal": "búsqueda principal", "ext": "búsqueda ampliada", "min": "en el mínimo", "max": "en el máximo", "no": "no", "mejora": "mejora", "no mejora": "no mejora"}
RENOMBRES_POR_TABLA = {"posthoc__eda_tasas": {"tasa": "Proporción sin pareja", "cajas": "Cajas", "positivos": "Cajas sin pareja"},
                       "posthoc__sensibilidad_detector": {"tasa_falsas_alarmas_sobre_celdas_con_n": "Tasa de celdas marcadas de más (sobre celdas con >= 100 cajas)"}}
_ENCABEZADOS = {"min_grilla": "Mínimo de la grilla", "max_grilla": "Máximo de la grilla", "folds_en_min": "Pliegues en el mínimo", "folds_en_max": "Pliegues en el máximo", "borde": "Valor en el borde",
                "hiperparametro": "Hiperparámetro", "valor": "Valor probado", "ap_train": "PR-AUC en entrenamiento", "ap_val": "PR-AUC en validación", "q1": "Primer cuartil", "q3": "Tercer cuartil",
                "iqr": "Rango intercuartílico", "minimo": "Mínimo", "maximo": "Máximo", "medida": "Medida", "pct_nulos": "% de nulos", "pct_atipicos": "% de atípicos",
                "tasa_falsas_alarmas_sobre_celdas_con_n": "Tasa de celdas marcadas de más (sobre celdas con >= 100 cajas)", "marcadas_lista": "Celdas marcadas (lista)",
                "variante": "Variante", "metodo": "Método", "nota": "Nota", "fuente_EP2": "Fuente EP2", "fuente_EP3": "Fuente EP3",
                "silhouette_muestra_20000": "Silhouette (muestra de 20.000)", "BIC_GMM_muestra_15000": "BIC del GMM (muestra de 15.000)", "davies_bouldin": "Davies-Bouldin", "calinski_harabasz": "Calinski-Harabasz",
                "tamano_cluster_mas_chico": "Tamaño del cluster más chico", "ari_medio": "ARI medio", "ari_minimo": "ARI mínimo", "ari_p5": "ARI percentil 5", "folds_opt_gana_ap": "Pliegues en que gana el optimizado",
                "detecta_911012534050_cam5": "Marca la celda 911012534050, cámara 5", "detecta_257766998801_cam3": "Marca la celda 257766998801, cámara 3", "mediana_distancia_m": "Mediana de la distancia (m)",
                "mediana_azimut_abs_deg": "Mediana del azimut absoluto (°)", "mediana_num_lidar_points": "Mediana de puntos del LiDAR", "mediana_num_top_lidar_points": "Mediana de puntos del sensor superior",
                "mediana_densidad_puntos": "Mediana de la densidad de puntos", "mediana_volumen_caja": "Mediana del volumen de la caja", "es_la_configuracion_de_EP2": "Es la configuración de EP2",
                "equilibrio_cajas_por_auditoria": "Equilibrio (cajas por auditoría)", "positivos_cubiertos_por_auditoria": "Cajas sin pareja cubiertas por la auditoría",
                "prop_replicas_C_mejor": "Proporción de réplicas en que C es mejor", "min_cajas": "Mínimo de cajas", "celdas_con_n_suficiente": "Celdas con cajas suficientes", "nivel_simplicidad": "Nivel de simplicidad",
                "cumple_O1_O3_O4": "Cumple O1, O3 y O4", "n_segmentos": "N.° de segmentos"}


def numero_legible(v: Any) -> str:
    """Número de una celda de escala mezclada (hiperparámetros, estadísticos de variables distintas): enteros sin decimales, muy pequeños en notación científica con coma
    y el resto con 4 cifras significativas. Nunca «20,000» junto a «1.600» en la misma columna."""
    x = _num(v)
    if x is None:
        return "—"
    if x == round(x):
        return entero(x)
    if abs(x) < 1e-3:
        m, e = f"{x:.1e}".split("e")
        return f"{m.replace('.', ',')}e{int(e)}"
    if abs(x) >= 1000:
        return decimal(x, 1)
    s = f"{x:.4g}"
    return decimal(float(s), max(0, len(s.split('.')[1]) if '.' in s else 0))


def _es_porcentaje(nombre: str, df: Any) -> bool:
    n = str(nombre)
    if n.startswith(("dif", "diferencia")):
        return False
    if n.startswith(("pct_", "Fraccion", "prob_media", "prevalencia", "tasa", "prop_")):
        return True
    if n in ("ic_lo", "ic_hi"):
        return any(str(c).startswith(("tasa", "pct_")) for c in df.columns)
    return False


def tabla_legible(df: Any, decimales: int = 3, tabla: str = "") -> Any:
    """Copia de un DataFrame lista para mostrar: nombres legibles y números con formato es-CL (texto; las tablas de evidencia no se reordenan).

    Reglas (F19-B5): las columnas de proporciones (``pct_*``, ``Fraccion*``, ``tasa*``, ``prevalencia``) salen como porcentaje; las de escala mezclada (hay enteros y
    decimales y valores >= 10) salen con ``numero_legible``; los hiperparámetros, etapas y bordes se muestran con nombres en español. ``tabla`` permite renombres propios de
    una tabla (por ejemplo «tasa» es la proporción sin pareja en ``posthoc__eda_tasas``).
    """
    import pandas as pd

    out = pd.DataFrame(index=df.index)
    usados: dict[str, int] = {}
    ren = RENOMBRES_POR_TABLA.get(tabla, {})
    for c in df.columns:
        s = df[c]
        v = s.dropna() if s.dtype.kind in "fi" else None
        if pd.api.types.is_bool_dtype(s):
            col = s.map({True: "sí", False: "no"})
        elif pd.api.types.is_integer_dtype(s):
            col = s.map(entero)
        elif pd.api.types.is_float_dtype(s):
            enteros = (not v.empty) and v.eq(v.round()).all()
            mezcla = (not v.empty) and (v == v.round()).any() and (v != v.round()).any() and v.abs().max() >= 10
            if _es_porcentaje(c, df):
                col = s.map(lambda x: porcentaje(x, 1))
            elif enteros:
                col = s.map(entero)
            elif mezcla:
                col = s.map(numero_legible)
            else:
                col = s.map(lambda x: decimal(x, decimales))
        elif s.dtype == object:
            texto = s.fillna("").astype(str)
            if str(c) == "hiperparametro":
                col = texto.map(lambda x: HIPERPARAMETROS.get(x, x.replace("_", " ")))
            elif str(c) in ("etapa", "borde"):
                col = texto.map(lambda x: VALORES_TEXTO.get(x, x))
            else:
                col = texto.str.replace("_", " ", regex=False).map(acentuar)
        else:
            col = s
        nombre = ren.get(str(c)) or _ENCABEZADOS.get(str(c)) or nombre_columna(str(c))
        usados[nombre] = usados.get(nombre, 0) + 1
        out[nombre if usados[nombre] == 1 else f"{nombre} ({usados[nombre]})"] = col
    return out


PX_POR_CARACTER = 6.6       # ancho medio de un carácter de la letra de la tabla (13 px)
PX_MARGEN_ENCABEZADO = 30   # margen + icono de orden del encabezado
PX_MARGEN_CELDA = 16


def anchos_columnas(df: Any, minimo: int = 56, maximo: int = 460) -> dict[str, int]:
    """Ancho en píxeles de cada columna calculado con el largo del encabezado y del contenido más largo (F20-P4g): ningún encabezado queda cortado («Posició»)."""
    out: dict[str, int] = {}
    for c in df.columns:
        enc = len(str(c)) * PX_POR_CARACTER + PX_MARGEN_ENCABEZADO
        cuerpo = df[c].astype(str).str.len().max() if len(df) else 0
        cuerpo = 0 if cuerpo != cuerpo else cuerpo
        out[str(c)] = int(min(max(enc, cuerpo * PX_POR_CARACTER + PX_MARGEN_CELDA, minimo), maximo))
    return out
