"""Lógica y textos de la página «Validación» (F34): titular calculado, conteos de los criterios O1 a O4, puntos clave de cada pestaña y las tablas de apoyo con su especificación.

Todo sale de las tablas de evidencia (``data/09_app_ep3/evidencia``) y del plan v3 congelado (solo lectura); ninguna cifra se escribe a mano. Funciones puras (sin Streamlit).
"""
from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.app_logica import PLAN_V3, SECCIONES, criterios_seleccion
from waymo_evaluacion.ep3.tablas_estandar import Col, Tabla, construir_tabla, tabla_de_listas

# ------------------------------------------------------------------------------------------------------------ pestañas
PESTANAS = ("Modelo elegido", "Generalización", "Alternativas", "Tipos de caso", "En muestra")
CLAVES_PESTANA = {"Modelo elegido": ("ie12",), "Generalización": ("ie11",), "Alternativas": ("ie9", "ie10"), "Tipos de caso": ("nosup",), "En muestra": ("posthoc",)}
TITULAR_NINGUNA = "La regla simple se mantiene: ninguna de las {n} alternativas probadas «vale la pena» frente a ella."
TITULAR_ALGUNA = "{k} de las {n} alternativas probadas «vale la pena» frente a la regla (O2): {lista}."
ROTULO_MUESTRA = "En muestra: {n} segmentos de desarrollo"
ROTULO_SIN_VALIDACION = "Sin validación con datos nuevos"
SUB_ALTERNATIVAS = ("¿Ajustar los hiperparámetros ayuda?", "¿Combinar modelos ayuda?")
TITULO_GRAFICO = {"ie9": "Cambio de PR-AUC al optimizar frente a los valores por defecto", "ie10": "Diferencia de AUC entre cada ensamble y su mejor componente",
                  "ie11": "AUC de cada candidato en validación cruzada por segmentos", "nosup": "Proporción de cajas sin pareja en cada tipo de caso",
                  "posthoc": "Fracción de cajas a revisar para encontrar el 80 %, por candidato"}
DESCRIPCION_GRAFICO = {
    "ie9": "Cambio de PR-AUC al optimizar los hiperparámetros: positivo es mejora. Cada fila trae su intervalo de confianza 95 % por segmentos y su estado en texto.",
    "ie10": "Diferencia de AUC entre cada ensamble y su mejor componente: positivo es que el ensamble aporta. Cada fila trae su intervalo y su veredicto en texto.",
    "ie11": "AUC de cada candidato con su intervalo de confianza 95 % por segmentos; los rombos son el AUC de cada partición (regla de puntos, LR3 y XGB). Una línea marca el AUC mínimo por partición.",
    "nosup": "Proporción de cajas sin pareja en cada tipo de caso (k = 2) con su intervalo de confianza 95 % por segmentos.",
    "posthoc": "Fracción de las cajas que hay que revisar para encontrar el 80 % de las cajas sin pareja, para cada candidato y cada flujo; menos es mejor."}
LEYENDA_INTERVALO = "Línea clara: intervalo de confianza 95 % por segmentos."
NOTA_ARI = ("El ARI bajo de KMeans contra GMM (0,008 con k = 2; en EP2 fue 0,997) no es un error de filas: las tres técnicas se compararon sobre las mismas 15.000 filas y el cálculo se repitió con el mismo resultado; "
            "lo que cambia es el GMM de covarianza completa, que parte la muestra de otra forma. Detalle en el informe técnico de EP3 («Diagnóstico del ARI bajo»; post hoc, no pre-declarado).")
TEXTO_CSV_CURVAS = "Curvas de validación (una fila por partición y valor probado): solo en la descarga."

# ------------------------------------------------------------------------------------------------------------ candidatos: qué es cada uno (fuente: plan_v3.md P6, candidatos.py y datos.py)
DESCRIPCION_CANDIDATOS = (
    ("Regla top", "Regla de puntos del sensor superior: ordena las cajas por menos puntos del sensor superior (más arriba cuantos menos puntos tiene la caja).", "src/waymo_evaluacion/ep3/candidatos.py (PuntuadorRegla)"),
    ("LR3", "Regresión logística con 3 variables: puntos del LiDAR, puntos del sensor superior y azimut.", "src/waymo_evaluacion/ep3/datos.py (V_MIN3) y candidatos.py"),
    ("LR", "Regresión logística (con las 16 variables por defecto; la búsqueda de hiperparámetros puede elegir otro conjunto).", "src/waymo_evaluacion/ep3/candidatos.py (BASE)"),
    ("RF", "Bosque aleatorio (Random Forest), con las 16 variables por defecto.", "src/waymo_evaluacion/ep3/candidatos.py (BASE)"),
    ("HGB", "Gradient boosting por histogramas (HistGradientBoosting), con las 16 variables por defecto.", "src/waymo_evaluacion/ep3/candidatos.py (BASE)"),
    ("XGB", "XGBoost, con las 16 variables por defecto.", "src/waymo_evaluacion/ep3/candidatos.py (BASE)"),
    ("LGBM", "LightGBM, con las 16 variables por defecto.", "src/waymo_evaluacion/ep3/candidatos.py (BASE)"),
    ("E1", "Ensamble de voto suave de LR, RF y HGB.", "docs/ep3/plan_v3.md (P6) y candidatos.py"),
    ("E2", "Ensamble que promedia los rangos de E1 y de la regla de puntos del sensor superior.", "docs/ep3/plan_v3.md (P6) y candidatos.py"),
    ("E3", "Ensamble por apilamiento (stacking) de LR, RF, HGB, XGB y LGBM, con una regresión logística final entrenada con predicciones fuera de partición (GroupKFold de 3 por segmento).", "docs/ep3/plan_v3.md (P6) y candidatos.py"),
    ("E4", "Ensamble por apilamiento de tres vistas (observación, tamaño y posición): un modelo por vista y una regresión logística final.", "docs/ep3/plan_v3.md (P6) y candidatos.py"),
    ("vista obs", "Vista de observación: puntos del LiDAR, puntos del sensor superior, densidad de puntos y distancia.", "src/waymo_evaluacion/ep3/datos.py (V_OBS)"),
    ("vista tam", "Vista de tamaño: largo, ancho, alto, volumen de la caja, si es ciclista y velocidad.", "src/waymo_evaluacion/ep3/datos.py (V_TAMANO)"),
    ("vista pos", "Vista de posición: centro de la caja, azimut, distancia y rumbo.", "src/waymo_evaluacion/ep3/datos.py (V_POSICION)"),
)

# ------------------------------------------------------------------------------------------------------------ lecturas del plan v3 (solo lectura)


def _plan(plan: dict[str, Any] | None = None) -> dict[str, Any]:
    if plan is not None:
        return plan
    try:
        return json.loads(PLAN_V3.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def auc_minimo_particion(plan: dict[str, Any] | None = None) -> float | None:
    """AUC mínimo por partición que exige O4 (plan v3, ``P7.estabilidad.auc_min_fold``); ``None`` si el plan no está a mano."""
    try:
        return float(_plan(plan)["P7"]["estabilidad"]["auc_min_fold"])
    except (KeyError, TypeError, ValueError):
        return None


def ece_maximo(plan: dict[str, Any] | None = None) -> float | None:
    try:
        return float(_plan(plan)["P8"]["objetivos"]["O4"]["ece_max"])
    except (KeyError, TypeError, ValueError):
        return None


def regla_mejora_hiperparametros(plan: dict[str, Any] | None = None) -> str:
    """La regla con que EP3 decide «mejora» al optimizar (``f3_analisis.py``): el cambio de PR-AUC llega al mínimo del plan y el intervalo pareado por segmentos queda sobre 0."""
    try:
        d = float(_plan(plan)["P5"]["mejora"]["diferencia_min"])
        return f"«Mejora» cuando el cambio de PR-AUC es de al menos {F.decimal(d, 3)} y su intervalo de confianza queda por encima de 0."
    except (KeyError, TypeError, ValueError):
        return "«Mejora» cuando el intervalo de confianza del cambio queda por encima de 0."


# ------------------------------------------------------------------------------------------------------------ titular y criterios
def alternativas_probadas(t: pd.DataFrame, elegido: str) -> list[str]:
    """Los candidatos de la tabla de selección menos la propia regla elegida."""
    return [str(c) for c in t["candidato"] if str(c) != str(elegido)]


def titular_validacion(t: pd.DataFrame, elegido: str) -> dict[str, Any]:
    """Titular de Validación calculado de la tabla de selección: si NINGUNA alternativa cumple O2 («vale la pena» frente a la regla) afirma que la regla se mantiene; si alguna cumple, dice cuántas y cuáles."""
    if "candidato" not in t.columns or "O2" not in t.columns:
        return {"rama": "sin_datos", "texto": "", "n": 0, "cumplen": []}
    alt = alternativas_probadas(t, elegido)
    o2 = t.set_index("candidato")["O2"].astype(bool)
    cumplen = [c for c in alt if bool(o2.get(c, False))]
    if not cumplen:
        return {"rama": "ninguna", "texto": TITULAR_NINGUNA.format(n=F.entero(len(alt))), "n": len(alt), "cumplen": []}
    lista = ", ".join(F.nombre_visible(c) for c in cumplen)
    return {"rama": "alguna", "texto": TITULAR_ALGUNA.format(k=F.entero(len(cumplen)), n=F.entero(len(alt)), lista=lista), "n": len(alt), "cumplen": cumplen}


def conteos_criterios(t: pd.DataFrame, plan: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Una tarjeta por criterio O1 a O4: «✓ X de N» (si alguno cumple) o «✕ X de N» (si ninguno), con su nombre y su definición corta. X y N salen de la tabla de selección (todos los candidatos)."""
    total = int(len(t))
    out = []
    for k, nombre, definicion in criterios_seleccion(plan):
        x = int(t[k].astype(bool).sum()) if k in t.columns else 0
        out.append({"clave": k, "nombre": nombre, "cumplen": x, "total": total, "ok": x > 0, "texto": f"{'✓' if x > 0 else '✕'} {F.entero(x)} de {F.entero(total)}", "definicion": definicion})
    return out


def particion_debil(ev: dict[str, pd.DataFrame], candidato: str) -> dict[str, Any] | None:
    """La partición con menor AUC de un candidato (tabla ``posthoc__auc_por_fold_y_brazos``, sin la fila global)."""
    t = ev.get("posthoc__auc_por_fold_y_brazos")
    if t is None or t.empty or not {"candidato", "fold", "AUC_A"} <= set(t.columns):
        return None
    t = t.assign(fold=t["fold"].astype(str))
    f = t[(t["candidato"] == candidato) & (t["fold"] != "global")]
    if f.empty:
        return None
    r = f.loc[f["AUC_A"].idxmin()]
    return {"particion": str(r["fold"]), "auc": float(r["AUC_A"])}


def mejor_otro_en_particion(ev: dict[str, pd.DataFrame], particion: str, excluir: str) -> dict[str, Any] | None:
    """El candidato (distinto de ``excluir``) con mayor AUC en esa partición, entre los que trae la tabla de particiones."""
    t = ev.get("posthoc__auc_por_fold_y_brazos")
    if t is None or t.empty or not {"candidato", "fold", "AUC_A"} <= set(t.columns):
        return None
    t = t.assign(fold=t["fold"].astype(str))
    f = t[(t["fold"] == str(particion)) & (t["candidato"] != excluir)]
    if f.empty:
        return None
    r = f.loc[f["AUC_A"].idxmax()]
    return {"candidato": str(r["candidato"]), "auc": float(r["AUC_A"])}


def aviso_o4(t: pd.DataFrame, elegido: str, ev: dict[str, pd.DataFrame], plan: dict[str, Any] | None = None) -> str | None:
    """Aviso de que la propia regla tampoco cumple O4, con su AUC mínimo por partición y el mínimo exigido; ``None`` si la regla cumple O4."""
    if not {"candidato", "O4", "AUC_min_fold", "ECE_cal"} <= set(t.columns):
        return None
    fila = t[t["candidato"] == elegido]
    if fila.empty or bool(fila["O4"].iloc[0]):
        return None
    f = fila.iloc[0]
    req, ece_max = auc_minimo_particion(plan), ece_maximo(plan)
    deb = particion_debil(ev, elegido)
    auc_min = float(f["AUC_min_fold"])
    if req is not None and auc_min < req:
        donde = f" en la partición {deb['particion']}" if deb else " por partición"
        texto = f"La propia regla tampoco cumple O4: su AUC mínimo{donde} es {F.decimal(auc_min, 3)}, por debajo del mínimo exigido de {F.decimal(req, 2)}."
        if deb:
            texto += f" La partición {deb['particion']} también aparece como el punto débil en Generalización y en En muestra."
        return F.menos(texto)
    if ece_max is not None and float(f["ECE_cal"]) > ece_max:
        return f"La propia regla tampoco cumple O4: su error de calibración es {F.decimal(f['ECE_cal'], 3)}, por encima del máximo de {F.decimal(ece_max, 2)}."
    return "La propia regla tampoco cumple O4."


# ------------------------------------------------------------------------------------------------------------ puntos clave
def puntos_generalizacion(ev: dict[str, pd.DataFrame], elegido: str) -> list[str]:
    """Dos puntos clave de Generalización: el rango de la brecha de AUC de la regla y su partición más débil frente al mejor candidato en esa partición."""
    out: list[str] = []
    b = ev.get("ie11__brecha_regla_top")
    if b is not None and not b.empty and {"brecha_AUC", "n_segmentos"} <= set(b.columns):
        lo, hi = float(b["brecha_AUC"].min()), float(b["brecha_AUC"].max())
        out.append(F.menos(f"Brecha entre ajuste y validación (regla): de {F.decimal_signado(lo, 3)} a {F.decimal_signado(hi, 3)} de AUC según cuántos segmentos se usan para ajustar "
                           f"(de {F.entero(b['n_segmentos'].min())} a {F.entero(b['n_segmentos'].max())})."))
    deb = particion_debil(ev, elegido)
    if deb:
        otro = mejor_otro_en_particion(ev, deb["particion"], elegido)
        frase = f"La partición {deb['particion']} es la débil: {F.decimal(deb['auc'], 3)} para la regla"
        if otro:
            frase += f" y {F.decimal(otro['auc'], 3)} para el mejor candidato ({F.nombre_visible(otro['candidato'])})"
        out.append(frase + ".")
    return out


def aviso_bordes(ev: dict[str, pd.DataFrame]) -> str | None:
    """«N de M hiperparámetros terminan en el borde de la grilla»: cuántos y cuáles (con cuántas particiones y en qué valor), calculado de ``ie9__bordes_de_grilla``."""
    b = ev.get("ie9__bordes_de_grilla")
    if b is None or b.empty or not {"borde", "modelo", "hiperparametro", "folds_en_max", "folds_en_min", "max_grilla", "min_grilla"} <= set(b.columns):
        return None
    total = len(b)
    en = b[b["borde"].astype(str) != "no"]
    if en.empty:
        return f"Ningún hiperparámetro de {F.entero(total)} termina en el borde de la grilla de búsqueda."
    partes = []
    for _, r in en.iterrows():
        mx = str(r["borde"]) == "max"
        n = int(r["folds_en_max" if mx else "folds_en_min"])
        valor = r["max_grilla" if mx else "min_grilla"]
        partes.append(f"{F.nombre_visible(str(r['modelo']))}, {str(F.HIPERPARAMETROS.get(str(r['hiperparametro']), r['hiperparametro'])).lower()} "
                      f"({F.entero(n)} {'partición' if n == 1 else 'particiones'} en el {'máximo' if mx else 'mínimo'}, {F.numero_legible(valor)})")
    k = len(en)
    cola = f" Los otros {F.entero(total - k)} no." if total > k else ""
    cabeza = "Único hiperparámetro que termina en el borde de la grilla de búsqueda: " if k == 1 else f"{F.entero(k)} de {F.entero(total)} hiperparámetros terminan en el borde de la grilla de búsqueda: "
    return cabeza + "; ".join(partes) + "." + cola


def puntos_tipos_de_caso(ev: dict[str, pd.DataFrame]) -> list[str]:
    """Puntos clave de «Tipos de caso»: cajas y % por tipo (k = 2), qué pasa con k = 4 y, solo si la página existe, que son los tipos que muestra «Explica una caja»."""
    out: list[str] = []
    k2, k4, ap = ev.get("nosup__clusters_k2"), ev.get("nosup__clusters_k4"), ev.get("nosup__aporte_sobre_la_regla")
    if k2 is not None and not k2.empty and {"tipo_de_caso", "cajas", "pct_cajas", "tasa_sin_camara"} <= set(k2.columns):
        out.append(" ".join(f"{str(r['tipo_de_caso']).capitalize()}: {F.entero(r['cajas'])} cajas ({F.porcentaje(r['pct_cajas'])}), {F.porcentaje(r['tasa_sin_camara'])} sin pareja." for _, r in k2.iterrows()))
    if k4 is not None and not k4.empty and "tasa_sin_camara" in k4.columns:
        frase = f"Con {F.entero(len(k4))} grupos la tasa va de {F.porcentaje(k4['tasa_sin_camara'].min())} a {F.porcentaje(k4['tasa_sin_camara'].max())}"
        if ap is not None and not ap.empty and int(len(k4)) in set(ap["k"].astype(int)):
            r = ap[ap["k"].astype(int) == int(len(k4))].iloc[0]
            d = float(r["dif_AUC"])
            verbo = ("baja" if d < 0 else "sube") if bool(r["excluye_0"]) else "no cambia de forma distinguible"
            frase += (f", y agregarlos {verbo} el AUC en {F.decimal(abs(d), 3)} (intervalo {F.menos(F.decimal(r['ic_lo'], 3))} a {F.menos(F.decimal(r['ic_hi'], 3))})."
                      if verbo != "no cambia de forma distinguible" else f", y agregarlos no cambia de forma distinguible el AUC ({F.decimal_signado(d, 3)}; intervalo {F.decimal_signado(r['ic_lo'], 3)} a {F.decimal_signado(r['ic_hi'], 3)}).")
        else:
            frase += "."
        out.append(F.menos(frase))
    if "Explica una caja" in SECCIONES:
        out.append("Son los tipos de caso que muestra Explica una caja.")
    return out


# ------------------------------------------------------------------------------------------------------------ «De dónde viene la mejora de la auditoría»
_SOLO = re.compile(r"solo se audita (\d{12}) camara (\d)")


def nombre_variante(texto: str) -> str:
    """Variante legible: sin el prefijo «global:», con tilde y con el identificador de segmento corto («Solo se audita …534050, cámara 5 (la otra celda queda en la cola)»)."""
    t = re.sub(r"^global:\s*", "", str(texto))
    t = re.sub(r"(\d{12}) camara (\d)", r"\1, cámara \2", t)
    t = t.replace("del analisis", "del análisis")
    t = F.segmento_corto(t)
    return t[:1].upper() + t[1:]


def tabla_variantes(ev: dict[str, pd.DataFrame], candidato: str) -> pd.DataFrame | None:
    """Las filas de ``posthoc__diferencia_C_menos_A`` del candidato elegido (la tabla que ya existe); ``None`` si falta."""
    t = ev.get("posthoc__diferencia_C_menos_A")
    if t is None or t.empty or not {"candidato", "variante", "dif_C_menos_A", "Fraccion80_A", "Fraccion80_C"} <= set(t.columns):
        return None
    f = t[t["candidato"] == candidato]
    return f.reset_index(drop=True) if not f.empty else None


def frase_auditoria(ev: dict[str, pd.DataFrame], candidato: str) -> str | None:
    """Compara lo que aporta auditar solo la mejor celda con lo que aportan ambas, y con lo que aporta la otra celda; ``None`` si la tabla no trae al menos dos variantes de una sola celda."""
    f = tabla_variantes(ev, candidato)
    if f is None:
        return None
    glob = f[f["variante"].astype(str).str.startswith("global")]
    solo = [(m.group(1), m.group(2), r) for _, r in f.iterrows() if (m := _SOLO.search(str(r["variante"])))]
    if glob.empty or len(solo) < 2:
        return None
    total = abs(float(glob["dif_C_menos_A"].iloc[0])) * 100
    solo.sort(key=lambda x: float(x[2]["dif_C_menos_A"]))
    seg1, cam1, r1 = solo[0]
    seg2, cam2, r2 = solo[1]
    aporte1, aporte2 = abs(float(r1["dif_C_menos_A"])) * 100, abs(float(r2["dif_C_menos_A"])) * 100
    return (f"Auditar solo la cámara {cam1} del segmento {F.segmento_corto(seg1)} ya baja la fracción de {F.porcentaje(r1['Fraccion80_A'])} a {F.porcentaje(r1['Fraccion80_C'])}: "
            f"{F.decimal(aporte1, 1)} de los {F.decimal(total, 1)} puntos de la mejora total. Auditar solo la otra celda (cámara {cam2} del segmento {F.segmento_corto(seg2)}) aporta {F.decimal(aporte2, 1)} puntos.")


# ------------------------------------------------------------------------------------------------------------ tablas de apoyo
APOYO = {
    "Modelo elegido": ("ie10__todos_los_candidatos", "ie12__tabla_de_seleccion", "ie12__modelo_escogido", "ie12__brazo_C_y_equilibrio", "candidatos"),
    "Generalización": ("ie11__brecha_regla_top", "ie11__brecha_LR3", "ie11__brecha_XGB", "ie11__metricas_de_generalizacion", "ie11__leave_one_segment_out_regla_top"),
    "Alternativas": ("ie9__defecto_vs_optimizado", "ie10__ensambles_aportan", "ie9__bordes_de_grilla"),
    "Tipos de caso": ("nosup__aporte_sobre_la_regla", "nosup__clusters_k2", "nosup__clusters_k4", "nosup__estabilidad", "nosup__isolation_forest", "nosup__seleccion_de_k", "nosup__comparacion_ep2_ep3"),
    "En muestra": ("posthoc__diferencia_C_menos_A", "posthoc__auc_por_fold_y_brazos", "posthoc__eda_calidad", "posthoc__eda_tasas", "posthoc__equidad", "posthoc__sensibilidad_detector"),
}
SOLO_CSV = ("ie9__curvas_de_validacion",)          # sale de pantalla: queda en la descarga
TITULOS = {"ie12__tabla_de_seleccion": "Criterios por candidato (O1 a O4)", "ie12__modelo_escogido": "Modelo escogido", "candidatos": "Candidatos"}
RESPONDE = {
    "ie10__todos_los_candidatos": "¿Cómo rinde cada candidato en AUC, PR-AUC, captura al revisar el 20 % y fracción para el 80 %?",
    "ie12__tabla_de_seleccion": "¿Qué criterios cumple cada candidato y cuánto se aparta de la regla?",
    "ie12__modelo_escogido": "¿Qué cifras tiene la solución elegida, con uno y dos pasos?",
    "ie12__brazo_C_y_equilibrio": "¿Cuánto cuesta encontrar el 80 % con uno y dos pasos, y cuándo empatan?",
    "candidatos": "¿Qué es cada candidato?",
    "ie11__brecha_regla_top": "¿Rinde peor en datos que no vio al ajustarse? Brecha = ajuste menos validación.",
    "ie11__brecha_LR3": "¿Rinde peor LR3 en datos que no vio al ajustarse?",
    "ie11__brecha_XGB": "¿Rinde peor XGBoost en datos que no vio al ajustarse?",
    "ie11__metricas_de_generalizacion": "¿Cómo se comporta cada candidato en validación cruzada por segmentos?",
    "ie11__leave_one_segment_out_regla_top": "¿Cómo rinde la regla al dejar fuera un segmento a la vez?",
    "ie9__defecto_vs_optimizado": "¿Cuánto cambia el AUC al optimizar cada modelo?",
    "ie10__ensambles_aportan": "¿Aporta cada ensamble sobre su mejor componente?",
    "ie9__bordes_de_grilla": "¿Algún hiperparámetro quedó pegado al borde de lo que se probó?",
    "nosup__aporte_sobre_la_regla": "¿Agregar los grupos mejora la predicción de la regla?",
    "nosup__clusters_k2": "¿Cómo son los dos tipos de caso y cuántas cajas sin pareja tiene cada uno?",
    "nosup__clusters_k4": "¿Cómo son los cuatro grupos y cuántas cajas sin pareja tiene cada uno?",
    "nosup__estabilidad": "¿Se mantienen los grupos al remuestrear los segmentos?",
    "nosup__isolation_forest": "¿Qué tan distintas son las cajas atípicas?",
    "nosup__seleccion_de_k": "¿Cuántos grupos conviene usar?",
    "nosup__comparacion_ep2_ep3": "¿Qué cambió entre el análisis de EP2 y el de EP3?",
    "posthoc__diferencia_C_menos_A": "¿Cuánto aporta cada celda auditada a la mejora de los dos pasos?",
    "posthoc__auc_por_fold_y_brazos": "¿Cómo cambia el AUC de cada partición según el flujo?",
    "posthoc__eda_calidad": "¿Hay valores faltantes o atípicos en las variables?",
    "posthoc__eda_tasas": "¿Cómo cambia la proporción sin pareja según cada variable?",
    "posthoc__equidad": "¿Rinde igual la regla en todos los grupos?",
    "posthoc__sensibilidad_detector": "¿Cambia la detección de huecos si se mueven los parámetros del detector?",
}

_AUC, _PR = ("AUC (IC 95 %)", "PR-AUC (IC 95 %)")


def _c(clave: str, enc: str, tipo: str = "text", tip: str = "", lo: str | None = None, hi: str | None = None, extra: str | None = None) -> Col:
    return Col(clave, enc, tipo, tip or enc, lo, hi, extra)


_BRECHA = [_c("n_segmentos", "Segmentos", "plain", "Segmentos usados para ajustar"), _c("AUC_ajuste", "AUC ajuste", "auc", "AUC en los datos de ajuste"), _c("AUC_validacion", "AUC validación", "auc", "AUC en los datos de validación"),
           _c("brecha_AUC", "Brecha AUC", "dif", "Brecha de AUC (ajuste menos validación)"), _c("PR-AUC_ajuste", "PR-AUC ajuste", "auc", "PR-AUC en los datos de ajuste"),
           _c("PR-AUC_validacion", "PR-AUC validación", "auc", "PR-AUC en los datos de validación"), _c("brecha_PR-AUC", "Brecha PR-AUC", "dif", "Brecha de PR-AUC (ajuste menos validación)")]
_CLUSTER = [_c("k", "Grupos (k)", "plain", "Número de grupos"), _c("cluster", "Grupo", "plain"), _c("tipo_de_caso", "Tipo de caso"), _c("cajas", "Cajas", "int"), _c("pct_cajas", "% de cajas", "pct", "Porcentaje de las cajas"),
            _c("positivos", "Sin pareja", "int", "Cajas sin pareja"), _c("tasa_sin_camara", "Proporción sin pareja", "pct", "Proporción sin pareja (IC 95 %)", "ic_lo", "ic_hi"), _c("segmentos", "Segmentos", "plain")]
ESPECIFICACION: dict[str, list[Col]] = {
    "ie10__todos_los_candidatos": [_c("candidato", "Candidato", "cand"), _c("AUC", _AUC, "auc", "AUC en validación cruzada por segmentos", "AUC_lo", "AUC_hi"), _c("PR-AUC", _PR, "auc", "PR-AUC en validación cruzada por segmentos", "PR-AUC_lo", "PR-AUC_hi"),
                                   _c("Captura@20", "Captura 20 % (IC 95 %)", "pct", "Captura al revisar el 20 % de las cajas", "Captura@20_lo", "Captura@20_hi"),
                                   _c("Fraccion_80", "Fracción 80 % (IC 95 %)", "pct", "Fracción de cajas a revisar para encontrar el 80 %", "Fraccion_80_lo", "Fraccion_80_hi")],
    "ie12__tabla_de_seleccion": [_c("candidato", "Candidato", "cand"), _c("nivel_simplicidad", "Simplicidad", "plain", "Nivel de simplicidad (0 es el más simple)"), _c("AUC", _AUC, "auc", "AUC en validación cruzada por segmentos", "AUC_lo", "AUC_hi"),
                                 _c("dif_AUC_vs_regla", "Dif. AUC (IC 95 %)", "dif", "Diferencia de AUC contra la regla", "dif_AUC_lo", "dif_AUC_hi"),
                                 _c("dif_Fraccion_80_vs_regla", "Dif. fracción 80 %", "pts", "Diferencia de fracción para el 80 % contra la regla", "dif_Fraccion_80_lo", "dif_Fraccion_80_hi"),
                                 _c("O1", "O1", "bool", "O1 Discrimina"), _c("O2", "O2", "bool", "O2 Vale la pena frente a la regla"), _c("O3", "O3", "bool", "O3 Recall en el punto A"), _c("O4", "O4", "bool", "O4 Estable y calibrada"),
                                 _c("cumple_O1_O3_O4", "Cumple O1, O3, O4", "bool", "Cumple O1, O3 y O4")],
    "ie12__modelo_escogido": [_c("candidato", "Candidato", "cand"), _c("AUC", _AUC, "auc", "AUC", "AUC_lo", "AUC_hi"), _c("PR-AUC", _PR, "auc", "PR-AUC", "PR-AUC_lo", "PR-AUC_hi"), _c("Captura@20", "Captura 20 % (IC 95 %)", "pct", "Captura al revisar el 20 %", "Captura@20_lo", "Captura@20_hi"),
                              _c("Fraccion_80", "Fracción 80 % (IC 95 %)", "pct", "Fracción para el 80 % con un paso", "Fraccion_80_lo", "Fraccion_80_hi"),
                              _c("Fraccion_80_C", "Fracción 80 %, dos pasos", "pct", "Fracción para el 80 % con dos pasos (IC 95 %)", "Fraccion_80_C_lo", "Fraccion_80_C_hi"),
                              _c("recall_A", "Recall punto A (IC 95 %)", "pct", "Recall en el punto A", "recall_A_lo", "recall_A_hi"),
                              _c("equilibrio_cajas_por_auditoria", "Equilibrio (cajas)", "entrunc", "Cajas por auditoría en que dos pasos empata con uno", "equilibrio_lo", "equilibrio_hi"),
                              _c("ECE_cal", "Error calibración", "auc", "Error de calibración (calibrado)"), _c("Brier_cal", "Brier", "auc", "Brier (calibrado)"), _c("AUC_min_fold", "AUC mín. partición", "auc", "AUC mínimo por partición")],
    "ie12__brazo_C_y_equilibrio": [_c("candidato", "Candidato", "cand"), _c("Fraccion_80_A", "Un paso", "pct", "Fracción para el 80 % con un paso (solo cola)"),
                                   _c("Fraccion_80_C", "Dos pasos (IC 95 %)", "pct", "Fracción para el 80 % con dos pasos (auditoría + cola)", "Fraccion_80_C_lo", "Fraccion_80_C_hi"),
                                   _c("Captura@20_A", "Captura 20 %, un paso", "pct", "Captura al revisar el 20 % con un paso"), _c("Captura@20_C", "Captura 20 %, dos pasos", "pct", "Captura al revisar el 20 % con dos pasos (IC 95 %)", "Captura@20_C_lo", "Captura@20_C_hi"),
                                   _c("equilibrio_cajas_por_auditoria", "Equilibrio (cajas)", "entrunc", "Cajas por auditoría en que dos pasos empata con uno", "equilibrio_lo", "equilibrio_hi"),
                                   _c("celdas_auditadas", "Celdas auditadas", "plain"), _c("recall_A_proceso_C", "Recall A, dos pasos", "pct", "Recall en el punto A con dos pasos")],
    "ie11__brecha_regla_top": _BRECHA, "ie11__brecha_LR3": _BRECHA, "ie11__brecha_XGB": _BRECHA,
    "ie11__metricas_de_generalizacion": [_c("candidato", "Candidato", "cand"), _c("AUC", _AUC, "auc", "AUC", "AUC_lo", "AUC_hi"), _c("PR-AUC", _PR, "auc", "PR-AUC", "PR-AUC_lo", "PR-AUC_hi"),
                                         _c("Captura@20", "Captura 20 % (IC 95 %)", "pct", "Captura al revisar el 20 %", "Captura@20_lo", "Captura@20_hi"), _c("Fraccion_80", "Fracción 80 % (IC 95 %)", "pct", "Fracción para el 80 %", "Fraccion_80_lo", "Fraccion_80_hi"),
                                         _c("recall_A", "Recall punto A (IC 95 %)", "pct", "Recall en el punto A", "recall_A_lo", "recall_A_hi"), _c("AUC_min_fold", "AUC mín. partición", "auc", "AUC mínimo por partición"),
                                         _c("AUC_mediana_segmento", "AUC mediana segmento", "auc", "Mediana del AUC por segmento"), _c("ECE_cal", "Error calibración", "auc", "Error de calibración (calibrado)"),
                                         _c("Brier_cal", "Brier", "auc", "Brier (calibrado)"), _c("estable", "Estable", "bool", "Estable por partición")],
    "ie11__leave_one_segment_out_regla_top": [_c("seg", "Segmento", "seg"), _c("positivos", "Sin pareja", "int", "Cajas sin pareja"), _c("filas", "Cajas", "int"), _c("AUC", "AUC", "auc"), _c("PR-AUC", "PR-AUC", "auc")],
    "ie9__defecto_vs_optimizado": [_c("modelo", "Modelo", "cand"), _c("etapa", "Etapa", "etapa"), _c("AUC_def", "AUC por defecto (IC 95 %)", "auc", "AUC con los hiperparámetros por defecto", "AUC_def_lo", "AUC_def_hi"),
                                   _c("AUC_opt", "AUC optimizado (IC 95 %)", "auc", "AUC con los hiperparámetros optimizados", "AUC_opt_lo", "AUC_opt_hi"),
                                   _c("dif_PR-AUC", "Cambio PR-AUC (IC 95 %)", "dif", "Cambio de PR-AUC (optimizado menos por defecto)", "dif_PR-AUC_lo", "dif_PR-AUC_hi"),
                                   _c("veredicto", "Veredicto", "text"), _c("folds_opt_gana_ap", "Particiones a favor", "de5", "Particiones en que gana el optimizado")],
    "ie10__ensambles_aportan": [_c("ensamble", "Ensamble"), _c("mejor_componente", "Mejor componente", "comp"), _c("AUC_ensamble", "AUC ensamble", "auc"), _c("AUC_mejor_componente", "AUC componente", "auc", "AUC del mejor componente"),
                                _c("dif_AUC", "Diferencia AUC (IC 95 %)", "dif", "Diferencia de AUC (ensamble menos mejor componente)", "dif_lo", "dif_hi"), _c("veredicto", "Veredicto"),
                                _c("folds_ganados_de_5", "Particiones ganadas", "de5", "Particiones en que gana el ensamble"), _c("segmentos_ganados", "Segmentos ganados", "ratio", "Segmentos en que gana el ensamble", extra="segmentos_comparados")],
    "ie9__bordes_de_grilla": [_c("modelo", "Modelo", "cand"), _c("etapa", "Etapa", "etapa"), _c("hiperparametro", "Hiperparámetro", "hip"), _c("min_grilla", "Mínimo grilla", "num", "Mínimo de la grilla"),
                              _c("max_grilla", "Máximo grilla", "num", "Máximo de la grilla"), _c("folds_en_min", "Particiones en mínimo", "plain"), _c("folds_en_max", "Particiones en máximo", "plain"), _c("borde", "Borde", "etapa", "Valor en el borde")],
    "nosup__aporte_sobre_la_regla": [_c("k", "Grupos (k)", "plain", "Número de grupos"), _c("AUC_regla", "AUC regla", "auc"), _c("AUC_regla_mas_cluster", "AUC regla + grupo", "auc", "AUC de la regla más el grupo"),
                                     _c("dif_AUC", "Diferencia AUC (IC 95 %)", "dif", "Diferencia de AUC", "ic_lo", "ic_hi"), _c("Brier_regla", "Brier regla", "auc"), _c("Brier_regla_mas_cluster", "Brier regla + grupo", "auc"),
                                     _c("excluye_0", "Excluye 0", "sino", "El intervalo excluye 0")],
    "nosup__clusters_k2": _CLUSTER, "nosup__clusters_k4": _CLUSTER,
    "nosup__estabilidad": [_c("k", "Grupos (k)", "plain"), _c("remuestreos", "Remuestreos", "plain"), _c("ari_medio", "ARI medio", "auc"), _c("ari_minimo", "ARI mínimo", "auc"), _c("ari_p5", "ARI percentil 5", "auc")],
    "nosup__isolation_forest": [_c("cajas_atipicas", "Cajas atípicas", "int"), _c("porcentaje", "% de cajas", "pct"), _c("segmentos_con_atipicos", "Segmentos con atípicos", "ratio", "Segmentos con cajas atípicas", extra="segmentos_total"),
                                _c("tasa_sin_camara_atipicas", "Sin pareja (atípicas)", "pct", "Proporción sin pareja entre las atípicas"), _c("tasa_sin_camara_resto", "Sin pareja (resto)", "pct", "Proporción sin pareja en el resto")],
    "nosup__seleccion_de_k": [_c("k", "Grupos (k)", "plain"), _c("silhouette_muestra_20000", "Silhouette", "auc", "Silhouette (muestra de 20.000)"), _c("davies_bouldin", "Davies-Bouldin", "auc"), _c("calinski_harabasz", "Calinski-Harabasz", "int"),
                              _c("tamano_cluster_mas_chico", "Grupo más chico", "pct", "Tamaño del grupo más chico"), _c("BIC_GMM_muestra_15000", "BIC del GMM", "int", "BIC del GMM (muestra de 15.000)")],
    "posthoc__diferencia_C_menos_A": [_c("variante", "Variante", "text"), _c("Fraccion80_A", "Un paso", "pct", "Fracción para el 80 % con un paso"), _c("Fraccion80_C", "Dos pasos", "pct", "Fracción para el 80 % con dos pasos"),
                                      _c("dif_C_menos_A", "Cambio (IC 95 %)", "pts", "Cambio de la fracción: dos pasos menos un paso", "ic_lo", "ic_hi"), _c("excluye_0", "Excluye 0", "sino", "El intervalo excluye 0"),
                                      _c("prop_replicas_C_mejor", "Réplicas a favor", "pct", "Proporción de réplicas en que dos pasos es mejor"), _c("segmentos", "Segmentos", "plain"), _c("celdas_auditadas", "Celdas auditadas", "plain")],
    "posthoc__auc_por_fold_y_brazos": [_c("candidato", "Candidato", "cand"), _c("fold", "Partición", "text"), _c("cajas", "Cajas", "int"), _c("positivos", "Sin pareja", "int", "Cajas sin pareja"), _c("hueco_contenido", "Celda con hueco", "text"),
                                       _c("cajas_en_hueco", "Cajas en hueco", "int", "Cajas en celdas con hueco"), _c("AUC_A", "AUC un paso", "auc"), _c("AUC_B_celdas_sanas", "AUC celdas sanas", "auc", "AUC solo con celdas sanas"),
                                       _c("Fraccion80_A", "Fracción 80 %, un paso", "pct"), _c("Fraccion80_B_celdas_sanas", "Fracción 80 %, sanas", "pct", "Fracción para el 80 % solo con celdas sanas"), _c("Fraccion80_C", "Fracción 80 %, dos pasos", "pct")],
    "posthoc__eda_calidad": [_c("variable", "Variable", "texto_"), _c("nulos", "Nulos", "int"), _c("pct_nulos", "% de nulos", "pct"), _c("q1", "Primer cuartil", "num"), _c("q3", "Tercer cuartil", "num"), _c("iqr", "Rango intercuartílico", "num"),
                             _c("atipicos_bajos", "Atípicos bajos", "int"), _c("atipicos_altos", "Atípicos altos", "int"), _c("pct_atipicos", "% de atípicos", "pct"), _c("minimo", "Mínimo", "num"), _c("maximo", "Máximo", "num")],
    "posthoc__eda_tasas": [_c("variable", "Variable", "texto_"), _c("tramo", "Tramo"), _c("cajas", "Cajas", "int"), _c("positivos", "Sin pareja", "int", "Cajas sin pareja"), _c("tasa", "Proporción sin pareja (IC 95 %)", "pct", "Proporción sin pareja", "ic_lo", "ic_hi"),
                           _c("segmentos", "Segmentos", "plain")],
    "posthoc__equidad": [_c("variable", "Variable", "texto_"), _c("grupo", "Grupo", "texto_"), _c("celdas_con_hueco", "Celdas con hueco", "text"), _c("segmentos", "Segmentos", "plain"), _c("cajas", "Cajas", "int"),
                         _c("positivos", "Sin pareja", "int", "Cajas sin pareja"), _c("recall_A", "Recall punto A", "pct", "Recall en el punto A"), _c("pct_revisado_A", "% revisado punto A", "pct", "Porcentaje revisado en el punto A"),
                         _c("precision_A", "Precisión punto A", "pct", "Precisión en el punto A"), _c("AUC", "AUC", "auc"), _c("nota_AUC", "Nota sobre el AUC", "text")],
    "posthoc__sensibilidad_detector": [_c("frac", "Fracción de la mediana", "pct0"), _c("min_cajas", "Mínimo de cajas", "plain"), _c("mediana", "Mediana", "text"), _c("celdas_totales", "Celdas", "int", "Celdas en total"),
                                       _c("celdas_con_n_suficiente", "Con cajas suficientes", "int", "Celdas con cajas suficientes"), _c("marcadas", "Marcadas", "int", "Celdas marcadas"),
                                       _c("detecta_911012534050_cam5", "Marca …534050 c5", "sino", "Marca la celda …534050, cámara 5"), _c("detecta_257766998801_cam3", "Marca …998801 c3", "sino", "Marca la celda …998801, cámara 3"),
                                       _c("detecta_los_2", "Marca las 2", "sino", "Marca las 2 celdas de referencia"), _c("falsas_alarmas", "Marcadas de más", "int", "Celdas marcadas además de las 2 de referencia (sin verdad externa)"),
                                       _c("tasa_falsas_alarmas_sobre_celdas_con_n", "Tasa de más", "pct", "Tasa de celdas marcadas de más (sobre celdas con 100 cajas o más)"), _c("es_la_configuracion_de_EP2", "Es la de EP2", "sino", "Es la configuración de EP2")],
}
NOTAS_TABLA = {"nosup__aporte_sobre_la_regla": "Método: regresión logística sobre el logit de la probabilidad de la regla, con y sin indicadoras de grupo; GroupKFold de 5 por segmento; intervalo por segmentos (1.000 réplicas).",
               "nosup__estabilidad": "KMeans con n_init=3 en cada remuestreo (el modelo de referencia usa n_init=10); escalado fijo.",
               "nosup__comparacion_ep2_ep3": NOTA_ARI}


def _transformar(clave: str, df: pd.DataFrame) -> pd.DataFrame:
    """Reordenamientos y limpiezas de presentación de una tabla (no cambian ningún valor)."""
    if clave == "posthoc__diferencia_C_menos_A":
        out = df.copy()
        out["variante"] = out["variante"].map(nombre_variante)
        return out
    if clave == "posthoc__auc_por_fold_y_brazos":
        out = df.copy()
        out["hueco_contenido"] = out["hueco_contenido"].map(lambda x: F.segmento_corto(str(x).replace("camara", "cámara")))
        return out
    if clave == "ie11__brecha_regla_top" or clave.startswith("ie11__brecha"):
        return df
    return df


def comparacion_ep2_ep3(df: pd.DataFrame) -> Tabla:
    """«Comparación entre EP2 y EP3»: cada fila con su propio formato según lo que mide (porcentaje, recuento o 3 decimales), el ARI incluido; los valores sin redondear van en el CSV."""
    def fmt(medida: str, v: float) -> str:
        m = medida.lower()
        if "(%)" in m:
            return F.menos(F.porcentaje_valor(v, 1))
        if "segmentos que aportan" in m or m.startswith("k elegido"):
            return F.entero(v)
        return F.menos(F.decimal(v, 3))

    filas = [[str(F.texto_visible(r["medida"])), fmt(str(r["medida"]), r["EP2"]), fmt(str(r["medida"]), r["EP3"])] for _, r in df.iterrows()]
    cols = [_c("medida", "Medida"), _c("EP2", "EP2", "valor", "Valor en EP2"), _c("EP3", "EP3", "valor", "Valor en EP3")]
    return Tabla("nosup__comparacion_ep2_ep3", "Comparación entre EP2 y EP3", RESPONDE["nosup__comparacion_ep2_ep3"], cols, filas, df.to_csv(index=False).encode("utf-8"), NOTA_ARI, columnas_en_csv=2)


def tabla_candidatos() -> Tabla:
    """La tabla «Candidatos»: qué es cada uno (E1 a E4, LR3, los modelos base y las tres vistas)."""
    mayus = lambda s: s[:1].upper() + s[1:]                                                                       # noqa: E731
    filas = [[mayus(str(F.nombre_visible(c))), d] for c, d, _ in DESCRIPCION_CANDIDATOS]
    csv = pd.DataFrame([{"candidato": c, "descripcion": d, "fuente": f} for c, d, f in DESCRIPCION_CANDIDATOS])
    return tabla_de_listas("candidatos", TITULOS["candidatos"], RESPONDE["candidatos"], [_c("candidato", "Candidato"), _c("descripcion", "Qué es")], filas, csv)


def tabla_resultados(df: pd.DataFrame) -> Tabla:
    """«Resultados de la solución elegida»: las cinco filas de ``tabla_resultados_clave`` (resultado, valor y detalle) sin cambiar ningún valor."""
    filas = [[str(F.texto_visible(F.nombre_visible(r["Resultado"]))), str(F.nombre_visible(r["Valor"])), str(F.texto_visible(F.nombre_visible(r["Detalle"])))] for _, r in df.iterrows()]
    cols = [_c("Resultado", "Resultado"), _c("Valor", "Valor", "valor"), _c("Detalle", "Detalle")]
    return tabla_de_listas("resultados", "Resultados de la solución elegida", "¿Qué cifras tiene la solución elegida?", cols, filas, df.drop(columns=["Fuente"], errors="ignore"))


def tabla_apoyo(clave: str, ev: dict[str, pd.DataFrame]) -> Tabla | None:
    """La ``Tabla`` estándar de una tabla de evidencia (``None`` si no está en los datos)."""
    if clave == "candidatos":
        return tabla_candidatos()
    df = ev.get(clave)
    if df is None or df.empty:
        return None
    if clave == "nosup__comparacion_ep2_ep3":
        return comparacion_ep2_ep3(df)
    titulo = TITULOS.get(clave) or F.titulo_tabla(clave)
    return construir_tabla(clave, df, ESPECIFICACION[clave], titulo, RESPONDE.get(clave, ""), NOTAS_TABLA.get(clave, ""), transformar=lambda d: _transformar(clave, d))


def tablas_de_pestana(pestana: str, ev: dict[str, pd.DataFrame]) -> list[Tabla]:
    """Las tablas de apoyo de una pestaña (las que existen en los datos), en su orden."""
    return [t for t in (tabla_apoyo(k, ev) for k in APOYO[pestana]) if t is not None]


# ------------------------------------------------------------------------------------------------------------ cabecera: las 4 cifras
def kpis_validacion(K: dict[str, Any], r: dict[str, Any], ciclistas: dict[str, float], etiqueta_ciclista: str = "Regla poco confiable") -> list[dict[str, str]]:
    """Las cuatro tarjetas de la cabecera: AUC con su intervalo, cajas analizadas, casos encontrados en peatones y en ciclistas. Salen de las mismas fuentes que las «cifras de apoyo» de antes
    (tarjetas de ``kpis.json``, ``inicio_resumen`` y ``datos_ciclistas``), así que coinciden con el Resumen y la Cola."""
    claves = {t.get("titulo", ""): t for t in K.get("tarjetas", [])}
    auc = claves.get("AUC fuera de fold", {})
    m = re.search(r"(\d,\d+) a (\d,\d+)", str(auc.get("ic", "")))
    out = [{"clave": "auc", "etiqueta": "AUC en validación cruzada por segmentos", "valor": str(auc.get("valor", "—")), "nota": f"intervalo 95 %: {m.group(1)} a {m.group(2)}" if m else "validación cruzada por segmentos"},
           {"clave": "cajas", "etiqueta": "Cajas analizadas", "valor": F.entero(r["cajas"]), "nota": f"peatones y ciclistas · {F.porcentaje(r['prevalencia'])} sin pareja"}]
    if all(isinstance(ciclistas.get(k), float) and ciclistas[k] == ciclistas[k] for k in ("ciclista", "peaton")):
        out += [{"clave": "peatones", "etiqueta": "Casos encontrados en peatones", "valor": F.porcentaje(ciclistas["peaton"]), "nota": "de las cajas sin pareja"},
                {"clave": "ciclistas", "etiqueta": "Casos encontrados en ciclistas", "valor": F.porcentaje(ciclistas["ciclista"]), "nota": f"{etiqueta_ciclista.lower()} en ciclistas"}]
    return out


def negrita_inicio(texto: str) -> str:
    """HTML de un punto clave con el encabezado de cada frase en negrita («<b>Brecha entre ajuste y validación (regla):</b> de …»); el resto del texto se escapa."""
    from html import escape

    marcadas = [re.sub(r"^(?P<enc>[^:.]{3,70}):", lambda m: "[[B]]" + m.group("enc") + ":[[/B]]", p) for p in re.split(r"(?<=\.) ", texto)]
    return escape(" ".join(marcadas)).replace("[[B]]", "<b>").replace("[[/B]]", "</b>")
