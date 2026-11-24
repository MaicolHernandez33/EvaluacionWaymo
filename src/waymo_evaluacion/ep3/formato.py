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
    "cajas": "Cajas", "positivos": "Cajas sin pareja", "modelo": "Modelo", "candidato": "Candidato", "ensamble": "Ensamble", "etapa": "Etapa", "veredicto": "Veredicto", "fold": "Partición",
    "k": "Número de grupos (k)", "cluster": "Grupo", "tipo_de_caso": "Tipo de caso", "variable": "Variable", "tramo": "Tramo", "celdas_con_hueco": "Celdas con hueco",
    "segmentos": "Segmentos", "prevalencia": "Proporción sin pareja", "tasa_sin_camara": "Proporción sin pareja", "ic_lo": "IC inferior", "ic_hi": "IC superior",
    "AUC": "AUC", "PR-AUC": "PR-AUC", "ECE_cal": "Error de calibración", "Brier_cal": "Brier", "AUC_min_fold": "AUC mínimo por partición", "AUC_mediana_segmento": "Mediana del AUC por segmento",
    "Captura@20": "Captura al revisar el 20 %", "Fraccion_80": "Fracción de cajas para el 80 %", "recall_A": "Recall en el punto A", "estable": "Estable",
    "mediana": "Mediana", "frac": "Fracción del umbral", "marcadas": "Celdas marcadas", "detecta_los_2": "Marca los 2 de referencia", "falsas_alarmas": "Celdas marcadas además de los 2 de referencia (sin verdad externa)",
}


_ACENTOS = {"hiperparametro": "hiperparámetro", "hiperparametros": "hiperparámetros", "validacion": "validación", "metricas": "métricas", "comparacion": "comparación", "generalizacion": "generalización",
            "seleccion": "selección", "calibracion": "calibración", "evaluacion": "evaluación", "camara": "cámara", "camaras": "cámaras", "posicion": "posición", "ensambles": "ensambles",
            "auc": "AUC", "ep2": "EP2", "ep3": "EP3", "ie9": "IE9", "ie10": "IE10", "ie11": "IE11", "ie12": "IE12", "defecto": "por defecto", "aportan": "aportan", "estabilidad": "estabilidad",
            "umbral": "umbral", "metodo": "método", "analisis": "análisis", "numero": "número", "diferencia": "diferencia", "tamano": "tamaño", "ubicacion": "ubicación", "tasa": "tasa", "fraccion": "fracción", "atipicos": "atípicos", "atipicas": "atípicas", "fold": "partición", "folds": "particiones", "seleccion": "selección", "platt": "Platt", "lidar": "LiDAR", "azimut": "azimut"}


def traducir_folds(texto: str) -> str:
    """Lenguaje de la página (F21-P4): «fuera de fold» pasa a «en validación cruzada por segmentos» y «fold(s)» a «partición(es)»; conserva la mayúscula inicial."""
    def frase(m: "re.Match[str]") -> str:
        return "En validación cruzada por segmentos" if m.group(0)[0].isupper() else "en validación cruzada por segmentos"

    def rep(m: "re.Match[str]") -> str:
        w = "particiones" if m.group(0).lower().endswith("s") else "partición"
        return w.capitalize() if m.group(0)[0].isupper() else w

    texto = re.sub(r"\bfuera de folds?\b", frase, texto, flags=re.IGNORECASE)
    return re.sub(r"\bfolds?\b", rep, texto, flags=re.IGNORECASE)


def acentuar(texto: str) -> str:
    """Pone tilde y mayúsculas conocidas a palabras sueltas de un nombre técnico (p. ej. «validacion» -> «validación»)."""
    return " ".join(_ACENTOS.get(w.lower(), w) for w in texto.split(" "))


def titulo_tabla(clave: str) -> str:
    """Título legible de una tabla de evidencia (``TITULOS_TABLAS`` o, si no está, a partir de su nombre: ``ie9__curvas_de_validacion`` -> «Curvas de validación»)."""
    if clave in TITULOS_TABLAS:
        return TITULOS_TABLAS[clave]
    t = acentuar(clave.split("__", 1)[-1].replace("_", " "))
    return t[:1].upper() + t[1:]


def nombre_columna(col: str) -> str:
    """Nombre legible para una columna de datos (nunca se muestra snake_case)."""
    if col in _DICCIONARIO:
        return _DICCIONARIO[col]
    t = col.replace("_lo", " (IC inf.)").replace("_hi", " (IC sup.)").replace("_def", " (por defecto)").replace("_opt", " (optimizado)").replace("_", " ").strip()
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
_ENCABEZADOS = {"min_grilla": "Mínimo de la grilla", "max_grilla": "Máximo de la grilla", "folds_en_min": "Particiones en el mínimo", "folds_en_max": "Particiones en el máximo", "borde": "Valor en el borde",
                "hiperparametro": "Hiperparámetro", "valor": "Valor probado", "ap_train": "PR-AUC en entrenamiento", "ap_val": "PR-AUC en validación", "q1": "Primer cuartil", "q3": "Tercer cuartil",
                "iqr": "Rango intercuartílico", "minimo": "Mínimo", "maximo": "Máximo", "medida": "Medida", "pct_nulos": "% de nulos", "pct_atipicos": "% de atípicos",
                "tasa_falsas_alarmas_sobre_celdas_con_n": "Tasa de celdas marcadas de más (sobre celdas con >= 100 cajas)", "marcadas_lista": "Celdas marcadas (lista)",
                "variante": "Variante", "metodo": "Método", "nota": "Nota", "fuente_EP2": "Fuente EP2", "fuente_EP3": "Fuente EP3",
                "silhouette_muestra_20000": "Silhouette (muestra de 20.000)", "BIC_GMM_muestra_15000": "BIC del GMM (muestra de 15.000)", "davies_bouldin": "Davies-Bouldin", "calinski_harabasz": "Calinski-Harabasz",
                "tamano_cluster_mas_chico": "Tamaño del cluster más chico", "ari_medio": "ARI medio", "ari_minimo": "ARI mínimo", "ari_p5": "ARI percentil 5", "folds_opt_gana_ap": "Particiones en que gana el optimizado",
                "detecta_911012534050_cam5": "Marca la celda 911012534050, cámara 5", "detecta_257766998801_cam3": "Marca la celda 257766998801, cámara 3", "mediana_distancia_m": "Mediana de la distancia (m)",
                "mediana_azimut_abs_deg": "Mediana del azimut absoluto (°)", "mediana_num_lidar_points": "Mediana de puntos del LiDAR", "mediana_num_top_lidar_points": "Mediana de puntos del sensor superior",
                "mediana_densidad_puntos": "Mediana de la densidad de puntos", "mediana_volumen_caja": "Mediana del volumen de la caja", "es_la_configuracion_de_EP2": "Es la configuración de EP2",
                "equilibrio_cajas_por_auditoria": "Equilibrio (cajas por auditoría)", "positivos_cubiertos_por_auditoria": "Cajas sin pareja cubiertas por la auditoría",
                "prop_replicas_C_mejor": "Proporción de réplicas en que C es mejor", "min_cajas": "Mínimo de cajas", "celdas_con_n_suficiente": "Celdas con cajas suficientes", "nivel_simplicidad": "Nivel de simplicidad",
                "cumple_O1_O3_O4": "Cumple O1, O3 y O4", "n_segmentos": "N.° de segmentos"}


_EVIDENCIA = {
    "pct_cajas_revisadas_A_C": "% de cajas revisadas en el punto A (dos pasos)", "pct_revisado_A": "% revisado en el punto A", "pct_revisar_A": "% a revisar en el punto A", "pct_revisar_B": "% a revisar en el punto B",
    "AUC_A": "AUC (un paso)", "AUC_B_celdas_sanas": "AUC (solo celdas sanas)", "AUC_ajuste": "AUC en el ajuste", "AUC_validacion": "AUC en validación", "PR-AUC_ajuste": "PR-AUC en el ajuste",
    "PR-AUC_validacion": "PR-AUC en validación", "AUC_ensamble": "AUC del ensamble", "AUC_mejor_componente": "AUC del mejor componente", "AUC_regla": "AUC de la regla",
    "AUC_regla_dentro_del_cluster": "AUC de la regla dentro del grupo", "AUC_regla_mas_cluster": "AUC de la regla más el grupo", "Brier_regla": "Brier de la regla", "Brier_regla_mas_cluster": "Brier de la regla más el grupo",
    "accuracy_A": "Accuracy en el punto A", "accuracy_B": "Accuracy en el punto B", "F1_A": "F1 en el punto A", "F1_B": "F1 en el punto B", "precision_A": "Precisión en el punto A", "precision_B": "Precisión en el punto B",
    "recall_B": "Recall en el punto B", "recall_A_lo": "Recall en el punto A (IC inf.)", "recall_A_hi": "Recall en el punto A (IC sup.)", "recall_B_lo": "Recall en el punto B (IC inf.)", "recall_B_hi": "Recall en el punto B (IC sup.)",
    "recall_A_proceso_C": "Recall en el punto A (dos pasos)", "recall_B_proceso_C": "Recall en el punto B (dos pasos)",
    "Captura@20_lo": "Captura al revisar el 20 % (IC inf.)", "Captura@20_hi": "Captura al revisar el 20 % (IC sup.)", "Captura@20_A": "Captura al revisar el 20 % (un paso)", "Captura@20_C": "Captura al revisar el 20 % (dos pasos)",
    "Captura@20_C_lo": "Captura al revisar el 20 % (dos pasos, IC inf.)", "Captura@20_C_hi": "Captura al revisar el 20 % (dos pasos, IC sup.)", "Captura20_A": "Captura al revisar el 20 % (un paso)",
    "Captura20_C": "Captura al revisar el 20 % (dos pasos)", "Captura@20_def": "Captura al revisar el 20 % (por defecto)", "Captura@20_def_lo": "Captura al revisar el 20 % (por defecto, IC inf.)",
    "Captura@20_def_hi": "Captura al revisar el 20 % (por defecto, IC sup.)", "Captura@20_opt": "Captura al revisar el 20 % (optimizado)", "Captura@20_opt_lo": "Captura al revisar el 20 % (optimizado, IC inf.)",
    "Captura@20_opt_hi": "Captura al revisar el 20 % (optimizado, IC sup.)",
    "Fraccion_80_lo": "Fracción para el 80 % (IC inf.)", "Fraccion_80_hi": "Fracción para el 80 % (IC sup.)", "Fraccion_80_A": "Fracción para el 80 % (un paso)", "Fraccion_80_C": "Fracción para el 80 % (dos pasos)",
    "Fraccion_80_C_lo": "Fracción para el 80 % (dos pasos, IC inf.)", "Fraccion_80_C_hi": "Fracción para el 80 % (dos pasos, IC sup.)", "Fraccion80_A": "Fracción para el 80 % (un paso)",
    "Fraccion80_B_celdas_sanas": "Fracción para el 80 % (solo celdas sanas)", "Fraccion80_C": "Fracción para el 80 % (dos pasos)", "Fraccion_80_def": "Fracción para el 80 % (por defecto)",
    "Fraccion_80_def_lo": "Fracción para el 80 % (por defecto, IC inf.)", "Fraccion_80_def_hi": "Fracción para el 80 % (por defecto, IC sup.)", "Fraccion_80_opt": "Fracción para el 80 % (optimizado)",
    "Fraccion_80_opt_lo": "Fracción para el 80 % (optimizado, IC inf.)", "Fraccion_80_opt_hi": "Fracción para el 80 % (optimizado, IC sup.)",
    "AUC_def": "AUC (por defecto)", "AUC_def_lo": "AUC (por defecto, IC inf.)", "AUC_def_hi": "AUC (por defecto, IC sup.)", "AUC_opt": "AUC (optimizado)", "AUC_opt_lo": "AUC (optimizado, IC inf.)", "AUC_opt_hi": "AUC (optimizado, IC sup.)",
    "PR-AUC_def": "PR-AUC (por defecto)", "PR-AUC_def_lo": "PR-AUC (por defecto, IC inf.)", "PR-AUC_def_hi": "PR-AUC (por defecto, IC sup.)", "PR-AUC_opt": "PR-AUC (optimizado)", "PR-AUC_opt_lo": "PR-AUC (optimizado, IC inf.)",
    "PR-AUC_opt_hi": "PR-AUC (optimizado, IC sup.)",
    "dif_lo": "Diferencia de AUC (IC inf.)", "dif_hi": "Diferencia de AUC (IC sup.)", "dif_AUC": "Diferencia de AUC", "dif_AUC_lo": "Diferencia de AUC (IC inf.)", "dif_AUC_hi": "Diferencia de AUC (IC sup.)",
    "dif_AUC_vs_regla": "Diferencia de AUC contra la regla", "dif_PR-AUC": "Diferencia de PR-AUC", "dif_PR-AUC_lo": "Diferencia de PR-AUC (IC inf.)", "dif_PR-AUC_hi": "Diferencia de PR-AUC (IC sup.)",
    "dif_Fraccion_80_vs_regla": "Diferencia de fracción para el 80 % contra la regla", "dif_Fraccion_80_lo": "Diferencia de fracción para el 80 % (IC inf.)", "dif_Fraccion_80_hi": "Diferencia de fracción para el 80 % (IC sup.)",
    "dif_C_menos_A": "Diferencia: dos pasos menos un paso", "dif_C_menos_A_Fraccion80": "Diferencia de fracción para el 80 %: dos pasos menos un paso",
    "prop_replicas_C_mejor": "Proporción de réplicas en que dos pasos es mejor", "replicas": "Réplicas", "equilibrio_cajas_por_auditoria": "Equilibrio (cajas por auditoría)",
    "equilibrio_lo": "Equilibrio (IC inf.)", "equilibrio_hi": "Equilibrio (IC sup.)", "positivos_cubiertos_por_auditoria": "Cajas sin pareja cubiertas por la auditoría", "cajas_en_hueco": "Cajas en celdas con hueco",
    "hueco_contenido": "Hueco contenido", "tasa_sin_camara_atipicas": "Proporción sin pareja (cajas atípicas)", "tasa_sin_camara_resto": "Proporción sin pareja (resto)",
    "prob_media_regla_platt": "Probabilidad media de la regla", "diferencia_tasa_menos_prob_regla": "Diferencia: proporción menos probabilidad de la regla", "segmentos_en_mediana": "Segmentos en la mediana",
    "segmentos_total": "Total de segmentos", "nota_AUC": "Nota sobre el AUC", "ECE_crudo": "Error de calibración (sin calibrar)", "ECE_cal": "Error de calibración (calibrado)", "mediana": "Mediana de referencia",
    "falsas_alarmas": "Celdas marcadas además de los 2 de referencia (sin verdad externa)", "brecha_AUC": "Brecha de AUC (ajuste menos validación)", "brecha_PR-AUC": "Brecha de PR-AUC (ajuste menos validación)",
    "PR-AUC_menos_prevalencia": "PR-AUC menos la prevalencia", "AUC_mediana_segmento": "Mediana del AUC por segmento", "segmentos_con_atipicos": "Segmentos con atípicos", "pct_cajas": "% de cajas",
}
TITULOS_TABLAS = {"ie12__brazo_C_y_equilibrio": "Dos pasos (auditoría + cola) y punto de equilibrio", "posthoc__auc_por_fold_y_brazos": "AUC por partición y por flujo", "posthoc__diferencia_C_menos_A": "Diferencia entre dos pasos y un paso",
                  "ie11__leave_one_segment_out_regla_top": "Dejando un segmento fuera: regla de puntos", "ie9__bordes_de_grilla": "Bordes de la grilla de búsqueda", "ie9__curvas_de_validacion": "Curvas de validación",
                  "ie9__defecto_vs_optimizado": "Por defecto contra optimizado", "ie10__ensambles_aportan": "¿Aportan los ensambles?", "ie10__todos_los_candidatos": "Todos los candidatos",
                  "ie11__brecha_LR3": "Brecha entre ajuste y validación: LR3", "ie11__brecha_XGB": "Brecha entre ajuste y validación: XGBoost", "ie11__brecha_regla_top": "Brecha entre ajuste y validación: regla de puntos",
                  "ie11__metricas_de_generalizacion": "Métricas de generalización", "ie12__modelo_escogido": "Modelo escogido", "ie12__tabla_de_seleccion": "Tabla de selección (O1 a O4)",
                  "nosup__clusters_k2": "Grupos con k = 2", "nosup__clusters_k4": "Grupos con k = 4", "nosup__aporte_sobre_la_regla": "Aporte de los grupos sobre la regla", "nosup__comparacion_ep2_ep3": "Comparación entre EP2 y EP3",
                  "nosup__estabilidad": "Estabilidad de los grupos", "nosup__isolation_forest": "Cajas atípicas (IsolationForest)", "nosup__seleccion_de_k": "Elección de k",
                  "posthoc__eda_calidad": "Calidad de los datos", "posthoc__eda_tasas": "Proporción sin pareja por tramo", "posthoc__equidad": "Equidad por grupo", "posthoc__sensibilidad_detector": "Sensibilidad del detector"}


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
        if str(c).startswith("fuente_"):                   # archivos de origen: se citan en el informe, no en pantalla (F21-P4)
            continue
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
                col = texto.str.replace("_", " ", regex=False).map(acentuar).map(nombre_visible)
        else:
            col = s
        nombre = ren.get(str(c)) or _EVIDENCIA.get(str(c)) or _ENCABEZADOS.get(str(c)) or nombre_columna(str(c))
        usados[nombre] = usados.get(nombre, 0) + 1
        out[nombre if usados[nombre] == 1 else f"{nombre} ({usados[nombre]})"] = col
    return out


NOMBRE_REGLA_VISIBLE = "regla de puntos del sensor superior"


def nombre_visible(texto: Any) -> Any:
    """Texto visible (F23): el candidato interno «Regla top» (clave de los datos, que no cambia) se muestra como «regla de puntos del sensor superior».

    Va con mayúscula inicial si abre el texto o la celda (o sigue a un punto o a una barra de tabla) y en minúscula dentro de una frase; se reconoce «Regla top» y «regla top». Un texto sin ese nombre sale igual; lo que no es texto, también.
    """
    if not isinstance(texto, str):
        return texto
    texto = re.sub(r"\bvista[ _](obs|tam|pos)\b", lambda m: NOMBRES_COMPONENTE["vista_" + m.group(1)], texto, flags=re.IGNORECASE)      # F34: «vista obs» se muestra «vista de observación»
    if "regla top" not in texto.lower():
        return texto

    def _cambiar(m: "re.Match[str]") -> str:
        antes = texto[:m.start()].rstrip(" \n")
        inicio = (not antes) or antes[-1] in ".!?|" or texto[:m.start()].rstrip(" ").endswith(chr(10))
        return NOMBRE_REGLA_VISIBLE[0].upper() + NOMBRE_REGLA_VISIBLE[1:] if inicio else NOMBRE_REGLA_VISIBLE

    return re.sub(r"regla top", _cambiar, texto, flags=re.IGNORECASE)


def sin_corte(texto: str) -> str:
    """Une cada «%» con su número con un espacio de no separación (F21): «79,8 %» no se parte entre dos líneas de un texto largo."""
    return re.sub(r"(?<=\d) %", "\u00a0%", texto)


NOMBRES_COMPONENTE = {"vista_obs": "vista de observación", "vista_tam": "vista de tamaño", "vista_pos": "vista de posición"}


def nombre_componente(x: Any) -> str:
    """Nombre legible de un componente de ensamble (F21-P4): «vista_obs» pasa a «vista de observación»; el resto cambia el guion bajo por espacio."""
    s = str(x)
    return nombre_visible(NOMBRES_COMPONENTE.get(s, s.replace("_", " ")))


PX_POR_CARACTER = 5.6       # ancho medio de un carácter del encabezado de la tabla (letra de 13 px; medido sobre las capturas de F21: 5,1 a 5,6 px)
PX_POR_CARACTER_CUERPO = 5.5   # ídem para el contenido de las celdas (medido: 5,6 px por carácter en «lejanos y poco densos»)
PX_MARGEN_ENCABEZADO = 35   # sangría izquierda (9 px) + espacio para el icono de ayuda y de orden
PX_MARGEN_CELDA = 20


def anchos_columnas(df: Any, minimo: int = 56, maximo: int = 460) -> dict[str, int]:
    """Ancho en píxeles de cada columna calculado con el largo del encabezado y del contenido más largo (F20-P4g): ningún encabezado queda cortado («Posició»)."""
    out: dict[str, int] = {}
    for c in df.columns:
        enc = len(str(c)) * PX_POR_CARACTER + PX_MARGEN_ENCABEZADO
        cuerpo = df[c].astype(str).str.len().max() if len(df) else 0
        cuerpo = 0 if cuerpo != cuerpo else cuerpo
        out[str(c)] = int(round(min(max(enc, cuerpo * PX_POR_CARACTER_CUERPO + PX_MARGEN_CELDA, minimo), maximo)))
    return out


# ------------------------------------------------------------------------------------------------------------ F34: signo menos único, identificador de segmento y textos visibles
MENOS = "−"       # «−» (U+2212): el único signo menos de tablas, ejes y gráficos de Validación y Puntuar


def menos(texto: str) -> str:
    """Cambia el guion de los números negativos por el signo menos («-0,011» -> «−0,011»); no toca guiones entre palabras ni rangos como «2-5»."""
    return re.sub(r"(?<![\w\d)])-(?=\d)", MENOS, str(texto))


def decimal_signado(x: Any, d: int = 3) -> str:
    """Diferencia con signo explícito: «+0,005», «−0,011» y «0,000» (el cero redondeado no lleva signo)."""
    s = decimal(x, d)
    if s == "—":
        return s
    if s.startswith("-"):
        return MENOS + s[1:]
    return s if float(s.replace(".", "").replace(",", ".")) == 0 else "+" + s


def segmento_corto(texto: Any) -> Any:
    """Identificador de segmento visible: «…534050» (los 6 últimos dígitos) en lugar de los 12. Es el formato del resto de las páginas; los CSV conservan el identificador completo."""
    if not isinstance(texto, str):
        return texto
    return re.sub(r"(?<!\d)\d{12}(?!\d)", lambda m: "…" + m.group(0)[-6:], texto)


_TILDES_VISIBLES = (("maximo", "máximo"), ("minimo", "mínimo"), ("Maximo", "Máximo"), ("Minimo", "Mínimo"), ("atipicas", "atípicas"), ("atipicos", "atípicos"), ("atipica", "atípica"),
                    ("camara", "cámara"), ("Camara", "Cámara"), ("analisis", "análisis"))


def texto_visible(texto: Any) -> Any:
    """Texto de una celda tal como se muestra: con las tildes que faltan en los datos («maximo» -> «máximo»), el identificador de segmento corto y el signo menos único.

    Solo cambia lo que se ve; los nombres de columnas y de archivos no se tocan."""
    if not isinstance(texto, str):
        return texto
    texto = re.sub(r"\bsin[_ ]camara\b", "sin pareja", texto)                       # el vocabulario de la página: «sin pareja», no el nombre interno de la columna
    for a, b in _TILDES_VISIBLES:
        texto = re.sub(rf"\b{a}\b", b, texto)
    return menos(segmento_corto(texto))
