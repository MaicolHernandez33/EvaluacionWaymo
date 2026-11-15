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


# =====================================================================================================================
# F18-C: rediseño de la página. Todo lo que sigue es lógica pura (sin Streamlit) para poder probarla; los números NO cambian,
# solo su presentación (formato es-CL, lenguaje simple, una sola fuente de valor entre tarjeta y texto).
# =====================================================================================================================
import json as _json  # noqa: E402

from waymo_evaluacion.ep3 import formato as F  # noqa: E402

PRODUCTO = "Auditor de etiquetas 3D"
ESLOGAN = "Revise primero las cajas que más probablemente no tienen su par en cámara."
AVISO_CORTO = "En muestra: 41 segmentos; el detector se ajustó con los mismos datos y aún no hay prueba ciega."
SECCIONES = ["Inicio", "Auditoría de cámaras", "Cola de revisión", "Explica una caja", "Evidencia", "Ética y límites", "Puntuar datos nuevos", "Ayuda y glosario"]
ICONOS = {"Inicio": ":material/home:", "Auditoría de cámaras": ":material/videocam:", "Cola de revisión": ":material/format_list_numbered:", "Explica una caja": ":material/help:",
          "Evidencia": ":material/science:", "Ética y límites": ":material/balance:", "Puntuar datos nuevos": ":material/upload_file:", "Ayuda y glosario": ":material/menu_book:"}
# qué acciones se le ofrecen a cada perfil en Inicio (sección, texto del botón)
ACCIONES_PERFIL = {
    "Analista de revisión": [("Cola de revisión", "Abrir la cola de revisión"), ("Explica una caja", "Entender una caja")],
    "Responsable de calidad de datos": [("Auditoría de cámaras", "Ver la auditoría de cámaras"), ("Evidencia", "Ver la evidencia")],
    "Ingeniero consumidor de datos": [("Puntuar datos nuevos", "Puntuar un segmento nuevo"), ("Ayuda y glosario", "Leer la ayuda")],
}
CLASE_ADVERTENCIA = "Ciclista: la regla es poco confiable"
CLASE_NORMAL = "Peatón"
SUPUESTO_SEGUNDOS = 20


def cargar_rangos(carpeta: Path) -> dict[int, tuple[float, float]]:
    """Rangos de azimut por cámara del detector congelado (solo lectura de ``detector_params_v3.json``; {} si no está)."""
    ruta = Path(carpeta) / "detector_params_v3.json"
    if not ruta.exists():
        return {}
    return {int(k): (float(v[0]), float(v[1])) for k, v in _json.loads(ruta.read_text(encoding="utf-8")).get("rangos", {}).items()}


def camara_de_azimut(az_signed: pd.Series, rangos: dict[int, tuple[float, float]]) -> pd.Series:
    """Cámara cuyo rango de azimut contiene a cada caja (si hay más de una, la de centro más cercano); «—» si ninguna."""
    if not rangos:
        return pd.Series("—", index=az_signed.index)
    az = az_signed.to_numpy(float)
    mejor = np.full(len(az), np.nan)
    dist = np.full(len(az), np.inf)
    for cam, (lo, hi) in rangos.items():
        dentro = (az >= lo) & (az <= hi)
        d = np.abs(az - (lo + hi) / 2)
        usar = dentro & (d < dist)
        mejor[usar] = cam
        dist[usar] = d[usar]
    return pd.Series([CAMARAS[int(c)] if not np.isnan(c) else "—" for c in mejor], index=az_signed.index)


def curva_inversa(curva: pd.DataFrame, solucion: str, objetivo: float) -> float:
    """Fracción de la cola que hay que revisar para encontrar ``objetivo`` (0 a 1) de las cajas sin pareja: interpolación inversa de la curva guardada."""
    c = curva[curva["solucion"] == solucion].sort_values("presupuesto")
    if c.empty:
        raise KeyError(f"la solución {solucion!r} no está en la curva")
    rec = np.maximum.accumulate(c["recall"].to_numpy(float))
    pres = c["presupuesto"].to_numpy(float)
    if objetivo >= rec[-1]:
        return float(pres[-1])
    if objetivo <= rec[0]:
        return float(pres[0])
    return float(np.interp(objetivo, rec, pres))


def resumen_cola(cajas: pd.DataFrame, curva: pd.DataFrame, solucion: str, segmento: str | None, presupuesto: float, segundos: float) -> dict[str, Any]:
    """Todo lo que muestra «Cola de revisión» con UNA sola fuente de valor: el conteo observado (``recall_proceso``). La curva solo aporta el IC.

    Antes la tarjeta usaba la curva interpolada y el texto el conteo observado (70,2 % contra 70,3 % con 20 %; 96,5 % contra 96,6 % con 68 %).
    """
    top, info = cola_segmento(cajas, segmento, presupuesto)
    esp = recall_en_presupuesto(curva, solucion, presupuesto)
    todos = segmento in (None, "Todos")
    return {"top": top, "todos": todos, "segmento": segmento, "presupuesto": presupuesto, "segundos": segundos,
            "cobertura": info["recall_proceso"], "ic_lo": esp["lo"] if todos else float("nan"), "ic_hi": esp["hi"] if todos else float("nan"), "cobertura_curva": esp["recall"],
            "cajas_a_revisar": info["cajas_a_revisar"], "cajas_cola_total": info["cajas_cola_total"], "horas": horas_revision(info["cajas_a_revisar"], segundos),
            "hallados": info["positivos_auditoria"] + info["positivos_en_cola"], "positivos_total": info["positivos_total"], "positivos_auditoria": info["positivos_auditoria"],
            "n_segmentos": int(cajas["seg"].nunique()) if todos else 1}


def texto_resultado_cola(r: dict[str, Any]) -> str:
    """Frase principal en lenguaje simple. Textos DISTINTOS para «Todos los segmentos» (con IC) y para un segmento (sin IC)."""
    if r["todos"]:
        return (f"Revisando {F.entero(r['cajas_a_revisar'])} cajas ({F.porcentaje(r['presupuesto'], 0)} de la cola) se encontrarían unas **{F.de_cada_100(r['cobertura'])}** cajas sin pareja "
                f"en los {r['n_segmentos']} segmentos (intervalo de confianza 95 % por segmentos: {F.porcentaje(r['ic_lo'], 0)} a {F.porcentaje(r['ic_hi'], 0)}; en muestra).")
    return (f"En el segmento {r['segmento']}, revisando {F.entero(r['cajas_a_revisar'])} cajas ({F.porcentaje(r['presupuesto'], 0)} de su cola) y atendiendo aparte las celdas marcadas, "
            f"se encontraron {F.entero(r['hallados'])} de {F.entero(r['positivos_total'])} cajas sin pareja ({F.porcentaje(r['cobertura'])}). Es un solo segmento: no hay intervalo de confianza por segmentos.")


def tabla_cola(top: pd.DataFrame, cola_total: int, rangos: dict[int, tuple[float, float]], presentacion: bool, max_filas: int = 500) -> pd.DataFrame:
    """Tabla de la cola lista para mostrar (nombres legibles, formato es-CL). En modo presentación no lleva identificadores (ni el segmento)."""
    t = top.head(max_filas).reset_index(drop=True)
    n = len(t)
    out = pd.DataFrame({"Posición": np.arange(1, n + 1)})
    if not presentacion:
        out["Segmento"] = t["seg"].to_numpy()
        for col, nombre in (("key.frame_timestamp_micros", "Marca de tiempo"), ("key.laser_object_id", "Identificador de objeto")):
            if col in t.columns:
                out[nombre] = t[col].to_numpy()
    out["Cámara"] = camara_de_azimut(t["az_signed"], rangos).to_numpy() if "az_signed" in t.columns else "—"
    out["Puntos del sensor superior"] = t["num_top_lidar_points"].map(F.entero).to_numpy() if "num_top_lidar_points" in t.columns else "—"
    out["Distancia"] = t["distancia_m"].map(lambda v: f"{F.decimal(v, 1)} m").to_numpy() if "distancia_m" in t.columns else "—"
    out["Prioridad"] = (100 * (1 - np.arange(n) / max(cola_total, 1))).round(1)
    if "es_ciclista" in t.columns:
        out["Clase"] = np.where(t["es_ciclista"].to_numpy() == 1, CLASE_ADVERTENCIA, CLASE_NORMAL)
    out["Tipo de caso"] = t["tipo_caso"].to_numpy() if "tipo_caso" in t.columns else "—"
    return out


def inicio_resumen(D: dict[str, Any], segundos: float = SUPUESTO_SEGUNDOS) -> dict[str, Any]:
    """Las 4 tarjetas de Inicio. Horas ahorradas = (80 % − fracción de cajas del flujo en dos pasos) × cajas × segundos / 3600: ESTIMACIÓN, en muestra."""
    cajas = D["cajas"]
    n = len(cajas)
    ev = D.get("evidencia", {}).get("ie12__brazo_C_y_equilibrio")
    horas = None
    frac_c = None
    if ev is not None and not ev.empty:
        cand = D.get("kpis", {}).get("candidato")
        fila = ev[ev["candidato"] == cand].iloc[0] if cand in set(ev["candidato"]) else ev.iloc[0]
        frac_c = float(fila["Fraccion_80_C"])
        horas = max((0.8 - frac_c) * n * segundos / 3600.0, 0.0)
    return {"cajas": n, "prevalencia": float(cajas["sin_camara"].mean()), "celdas_marcadas": int(len(D["lista_A"])), "segmentos_con_hueco": int(D["lista_A"]["segmento"].nunique()),
            "horas_ahorradas": horas, "fraccion_80_dos_pasos": frac_c, "segmentos": int(cajas["seg"].nunique())}


ACCION_SUGERIDA = "Completar las etiquetas 2D de esa cámara en el segmento o reportar el dato de cámara faltante."


def lista_A_presentable(lista_A: pd.DataFrame) -> pd.DataFrame:
    """Lista A con nombres legibles y la columna «Acción sugerida»."""
    cols = {"segmento": "Segmento", "ubicacion": "Ubicación", "momento": "Momento del día", "camara": "Cámara", "tasa": "Tasa de pares", "mediana_camara": "Mediana de la cámara",
            "cajas_en_rango": "Cajas en el rango", "cajas_afectadas_poblacion_principal": "Cajas afectadas", "positivos_afectados": "Cajas sin pareja"}
    out = pd.DataFrame()
    for c, nombre in cols.items():
        if c in lista_A.columns:
            v = lista_A[c]
            if c in ("tasa", "mediana_camara"):
                out[nombre] = v.map(lambda x: F.porcentaje(x, 0))
            elif c in ("cajas_en_rango", "cajas_afectadas_poblacion_principal", "positivos_afectados"):
                out[nombre] = v.map(F.entero)
            elif c == "ubicacion":
                out[nombre] = v.map({"location_sf": "San Francisco", "location_phx": "Phoenix", "location_other": "Otras"}).fillna(v)
            elif c == "momento":
                out[nombre] = v.map({"Day": "Día", "Night": "Noche", "Dawn/Dusk": "Amanecer o atardecer"}).fillna(v)
            else:
                out[nombre] = v
    out["Acción sugerida"] = ACCION_SUGERIDA
    return out


def explicacion_caja(puntos_top: float, distancia: float, es_ciclista: bool, percentil: float, prob: float) -> str:
    """Una frase que explica el resultado de «Explica una caja»."""
    base = (f"Con {F.entero(puntos_top)} puntos del sensor superior y a {F.decimal(distancia, 0)} m, la caja queda entre el {F.porcentaje(percentil, 0)} primero de la cola y la probabilidad "
            f"estimada de que no tenga par en ninguna cámara es {F.porcentaje(prob)}.")
    return base + (" Es un ciclista: en ciclistas la regla es poco confiable." if es_ciclista else "")


def lectura_evidencia(ev: dict[str, pd.DataFrame]) -> dict[str, str]:
    """Una línea de lectura por pestaña de Evidencia, calculada con las propias tablas (no se escriben cifras a mano)."""
    out: dict[str, str] = {}
    try:
        t = ev["ie9__defecto_vs_optimizado"]
        mejoran = [m for m, v in zip(t["modelo"], t["veredicto"]) if v == "mejora"]
        no = [m for m, v in zip(t["modelo"], t["veredicto"]) if v != "mejora"]
        out["ie9"] = f"Optimizar los hiperparámetros mejora a {', '.join(mejoran) or 'ningún modelo'} y no mejora a {', '.join(no) or 'ninguno'}: ayuda solo a los modelos que por defecto se sobreajustan."
    except (KeyError, IndexError):
        out["ie9"] = "Comparación de cada modelo con sus hiperparámetros por defecto y optimizados."
    try:
        t = ev["ie10__ensambles_aportan"]
        aportan = [e for e, v in zip(t["ensamble"], t["veredicto"]) if v == "aporta"]
        out["ie10"] = f"Ensambles que aportan sobre su mejor componente: {', '.join(aportan) if aportan else 'ninguno'}."
    except (KeyError, IndexError):
        out["ie10"] = "Comparación de cada ensamble con su mejor componente."
    try:
        t = ev["ie11__metricas_de_generalizacion"].set_index("candidato")
        r = t.loc["Regla top"]
        out["ie11"] = (f"La regla de puntos tiene AUC {F.decimal(r['AUC'], 3)} fuera de fold; ningún candidato alcanza el AUC mínimo por fold de 0,75 "
                       f"(el mejor llega a {F.decimal(t['AUC_min_fold'].max(), 3)}), por el fold 0.")
    except (KeyError, IndexError):
        out["ie11"] = "Métricas fuera de fold de los candidatos."
    try:
        t = ev["ie12__tabla_de_seleccion"]
        n2 = int(t["O2"].astype(bool).sum())
        out["ie12"] = f"Se eligió la regla «menos puntos del sensor superior» por simplicidad; {'ningún candidato cumple' if n2 == 0 else str(n2) + ' candidatos cumplen'} el criterio de «vale la pena» frente a la regla (O2)."
    except (KeyError, IndexError):
        out["ie12"] = "Tabla de selección con los criterios de EP2."
    try:
        t = ev["nosup__aporte_sobre_la_regla"]
        d = t.sort_values("k").iloc[0]
        out["nosup"] = f"Los grupos describen, no predicen: agregarlos a la regla cambia el AUC en {F.decimal(d['dif_AUC'], 4)} con k = {int(d['k'])} (descriptivo; post hoc)."
    except (KeyError, IndexError):
        out["nosup"] = "Análisis descriptivo; no mejora la predicción de la regla."
    try:
        t = ev["posthoc__auc_por_fold_y_brazos"]
        f0 = t[(t["candidato"] == "Regla top") & (t["fold"].astype(str) == "0")].iloc[0]
        out["posthoc"] = f"Con la celda con hueco fuera, el AUC de la regla en el fold 0 pasa de {F.decimal(f0['AUC_A'], 3)} a {F.decimal(f0['AUC_B_celdas_sanas'], 3)} (post hoc, en muestra, no pre-declarado)."
    except (KeyError, IndexError):
        out["posthoc"] = "Todo lo de esta pestaña es post hoc, no pre-declarado."
    return out


GLOSARIO = [
    ("Caja", "Un rectángulo 3D, medido con LiDAR, que rodea a un peatón o ciclista en un instante."),
    ("Par 2D", "La caja que otro equipo dibujó sobre la foto de una cámara para el mismo objeto. Si falta, la caja 3D «no tiene pareja»."),
    ("Celda", "Una combinación de segmento (20 s de video) y cámara."),
    ("Hueco", "Una celda donde casi ninguna caja tiene pareja (menos del 25 % de lo normal de esa cámara, con al menos 100 cajas). Se marca; no se sabe si es falta de etiquetas o de datos."),
    ("Cola", "La lista de cajas ordenada para revisar: primero las que más probablemente no tienen pareja."),
    ("Presupuesto", "El porcentaje de la cola que se decide revisar."),
    ("Cobertura", "De cada 100 cajas sin pareja, cuántas se encuentran al revisar el presupuesto elegido."),
    ("Intervalo de confianza", "El rango en que probablemente cae un resultado si se repitiera con otros segmentos. Aquí se calcula remuestreando segmentos completos; con 41 segmentos es ancho."),
    ("Post hoc", "Un análisis decidido después de ver los datos: es una hipótesis, no una conclusión confirmada."),
    ("En muestra", "Calculado con los mismos 41 segmentos con los que se ajustó el detector: probablemente optimista."),
    ("Sin prueba ciega", "Todavía no se probó con segmentos nuevos que nadie haya mirado; está preparada y sellada."),
]


def preguntas_frecuentes(equidad: pd.DataFrame | None = None) -> list[tuple[str, str]]:
    """Cinco preguntas frecuentes. Las cifras de ciclistas salen de ``f12_equidad.csv`` (si se entrega), no se escriben a mano."""
    ciclistas = "En ciclistas la regla es poco confiable: revíselos con más cuidado."
    if equidad is not None and not equidad.empty:
        try:
            c = equidad[(equidad["grupo"] == "CYCLIST") & (equidad["celdas_con_hueco"] == "incluidas")].iloc[0]
            p = equidad[(equidad["grupo"] == "PEDESTRIAN") & (equidad["celdas_con_hueco"] == "incluidas")].iloc[0]
            ciclistas = (f"En ciclistas la regla es poco confiable: encuentra {F.decimal(c['recall_A'], 3)} de los casos contra {F.decimal(p['recall_A'], 3)} en peatones, "
                         f"con solo {F.entero(c['positivos'])} casos en {F.entero(c['segmentos'])} segmentos. Revíselos con más cuidado.")
        except (KeyError, IndexError):
            pass
    return [
        ("¿La página decide qué cajas están mal?", "No. Solo ordena. Una persona revisa y decide; nunca se debe descartar una caja sin revisarla."),
        ("¿Por qué dice «en muestra» en todas partes?", "Porque los resultados se calcularon con 41 segmentos y el detector de huecos se ajustó con esos mismos datos; todavía no hay una prueba con segmentos nuevos."),
        ("¿Qué pasa con los ciclistas?", ciclistas),
        ("¿Se guardan o se envían mis archivos?", "No. «Puntuar datos nuevos» procesa el archivo en memoria y la página no hace ninguna conexión a internet."),
        ("¿Cuánto tarda revisar una caja?", f"No se midió: la página usa un supuesto de {SUPUESTO_SEGUNDOS} segundos por caja que usted puede cambiar en «Supuestos»."),
    ]


def version_pagina(carpeta_modelos: Path) -> str:
    """Texto de versión: solución congelada v3 y la fecha de su manifest (si existe)."""
    ruta = Path(carpeta_modelos) / "manifest_v3.json"
    fecha = ""
    if ruta.exists():
        fecha = str(_json.loads(ruta.read_text(encoding="utf-8")).get("creado", ""))[:10]
    return f"Solución v3 congelada{' el ' + fecha if fecha else ''}"


_NOMBRES_CURVA = {"Solución elegida, dos pasos (C)": "Dos pasos", "Solución elegida, un paso (A)": "Un paso", "Regla top, un paso (A)": "Regla de puntos, un paso",
                  "XGB (referencia), un paso (A)": "XGBoost (referencia)", "E2 (referencia), un paso (A)": "Ensamble E2 (referencia)"}


def nombre_curva_legible(solucion: str) -> str:
    """Nombre de una curva en español sencillo para la leyenda del gráfico."""
    return _NOMBRES_CURVA.get(solucion, solucion)


def formatear_kpi(texto: str) -> str:
    """Pone separador de miles es-CL a los enteros de 4 o más cifras de un texto de tarjeta (p. ej. «6059 cajas» -> «6.059 cajas»)."""
    import re

    return re.sub(r"(?<![\d,.])(\d{4,})(?![\d,])", lambda m: F.entero(int(m.group(1))), texto)


COLUMNAS_LIDAR_BOX = ["box.center.x", "box.center.y", "box.size.x", "num_lidar_points_in_box", "num_top_lidar_points_in_box", "box.heading", "key.segment_context_name", "key.frame_timestamp_micros", "key.laser_object_id"]


def validar_lidar_box(df: pd.DataFrame) -> str | None:
    """Mensaje amigable (en español) si al archivo de lidar_box le faltan columnas; ``None`` si está completo."""
    faltan = [c for c in COLUMNAS_LIDAR_BOX if not any(col.endswith(c) for col in df.columns)]
    if faltan:
        return ("Este archivo no parece un lidar_box de Waymo v2: faltan las columnas " + ", ".join(f"«{c}»" for c in faltan[:4]) + (" y otras" if len(faltan) > 4 else "") +
                ". Suba el parquet del componente lidar_box de un segmento.")
    return None


def validar_asociacion(df: pd.DataFrame) -> str | None:
    """Mensaje amigable si al archivo de asociación le faltan columnas; ``None`` si está completo."""
    faltan = [c for c in ("key.segment_context_name", "key.camera_name", "key.frame_timestamp_micros", "key.laser_object_id") if c not in df.columns]
    if faltan:
        return "Este archivo no parece camera_to_lidar_box_association: faltan las columnas " + ", ".join(f"«{c}»" for c in faltan) + ". Si no lo tiene, puede puntuar sin él (no habrá auditoría de cámaras)."
    return None


def datos_ciclistas(equidad: pd.DataFrame | None) -> dict[str, float]:
    """Cifras de la advertencia de ciclistas (recall en el punto A, casos y segmentos), leídas de ``f12_equidad.csv`` (copia en la evidencia de la página)."""
    vacio = {"ciclista": float("nan"), "peaton": float("nan"), "positivos": float("nan"), "segmentos": float("nan")}
    if equidad is None or equidad.empty:
        return vacio
    try:
        c = equidad[(equidad["grupo"] == "CYCLIST") & (equidad["celdas_con_hueco"] == "incluidas")].iloc[0]
        p = equidad[(equidad["grupo"] == "PEDESTRIAN") & (equidad["celdas_con_hueco"] == "incluidas")].iloc[0]
        return {"ciclista": float(c["recall_A"]), "peaton": float(p["recall_A"]), "positivos": float(c["positivos"]), "segmentos": float(c["segmentos"])}
    except (KeyError, IndexError):
        return vacio
