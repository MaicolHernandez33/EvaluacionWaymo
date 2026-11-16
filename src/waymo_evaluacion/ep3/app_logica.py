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
        "pregunta": "¿Qué se revisa primero y cuánto cuesta?",
        "seccion": "Cola de revisión",
        "mensaje": "La cola indica por dónde empezar; la decisión sobre cada caja es de la persona que revisa.",
        "alerta": "ciclistas",
    },
    "Responsable de calidad de datos": {
        "pregunta": "¿Qué cámaras o segmentos tienen un problema sistemático?",
        "seccion": "Auditoría de cámaras",
        "mensaje": "Una cámara con tasa de pares muy baja suele ser un problema de etiquetado o de datos, no de cajas sueltas: se atiende aparte.",
        "alerta": "celdas",
    },
    "Ingeniero consumidor de datos": {
        "pregunta": "¿Se puede confiar en las etiquetas 2D de un segmento nuevo?",
        "seccion": "Puntuar datos nuevos",
        "mensaje": "Un segmento nuevo se puntúa en el equipo y entrega la lista de celdas sospechosas y la cola de cajas.",
        "alerta": "validacion",
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


MIN_CAJAS_RANGO = 100        # el detector solo juzga una celda con al menos 100 cajas en el rango (detector_params_v3.json: min_cajas)


def cargar_min_cajas(carpeta: Path) -> int:
    """``min_cajas`` del detector congelado (solo lectura de ``detector_params_v3.json``); 100 si el archivo no está."""
    ruta = Path(carpeta) / "detector_params_v3.json"
    if ruta.exists():
        return int(json.loads(ruta.read_text(encoding="utf-8")).get("min_cajas", MIN_CAJAS_RANGO))
    return MIN_CAJAS_RANGO


def matriz_calor(celdas: pd.DataFrame, min_cajas: int = MIN_CAJAS_RANGO) -> pd.DataFrame:
    """Formato largo (segmento, cámara, tasa, hueco, n en rango) para el mapa de calor.

    ``sin_datos`` (F19-B2) marca las celdas SIN cajas o con menos de ``min_cajas`` en el rango: ahí el detector no juzga y la tasa no es comparable;
    no es lo mismo que una tasa de 0 % con cajas suficientes (eso es un hueco). ``seg_corto`` (F20-P5) son los últimos 6 dígitos del segmento (el id completo va en el tooltip).
    """
    filas = []
    for r in celdas.itertuples(index=False):
        d = r._asdict()
        for c, nombre in CAMARAS.items():
            n = d[f"n_rango_c{c}"]
            filas.append({"seg": d["seg"], "seg_corto": str(d["seg"])[-6:], "grupo": d["grupo"], "camara": nombre, "tasa": d[f"tasa_c{c}"], "n_rango": n,
                          "hueco": bool(d[f"hueco_c{c}"]), "sin_datos": bool(pd.isna(n) or n < min_cajas or pd.isna(d[f"tasa_c{c}"]))})
    return pd.DataFrame(filas)


def orden_segmentos(m: pd.DataFrame, marcadas_primero: bool = True) -> list[str]:
    """Orden de los segmentos (``seg_corto``) del mapa: con celdas marcadas primero (estable) o el orden original de los datos."""
    segs = list(dict.fromkeys(m["seg_corto"]))
    if not marcadas_primero:
        return segs
    con = set(m.loc[m["hueco"], "seg_corto"])
    return [s for s in segs if s in con] + [s for s in segs if s not in con]


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


def cola_segmento(cajas: pd.DataFrame, segmento: str | None, presupuesto: float, flujo: str = "dos") -> tuple[pd.DataFrame, dict[str, float]]:
    """Cola de un segmento (o de todos) y recall observado al revisar la fracción ``presupuesto``.

    ``flujo="dos"`` (por defecto): las cajas de celdas con hueco no entran a la cola, las atiende la auditoría (paso 1) y la cola ordena el resto.
    ``flujo="uno"``: solo cola; se ordenan TODAS las cajas y no hay auditoría previa.
    """
    d = cajas if segmento in (None, "Todos") else cajas[cajas["seg"] == segmento]
    base = d if flujo == "uno" else d[~d["en_hueco"]]
    sana = base.sort_values("score", ascending=False, kind="stable")
    n = int(np.ceil(presupuesto * len(sana)))
    top = sana.head(n)
    pos_total = int(d["sin_camara"].sum())
    pos_aud = 0 if flujo == "uno" else int(d.loc[d["en_hueco"], "sin_camara"].sum())
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
ESLOGAN = "Revisión priorizada de cajas 3D de peatones y ciclistas sin par 2D."
VERSION_PRODUCTO = "EP3"
CHIP_ESTADO = "Datos de desarrollo · sin validación externa"
AVISO_CORTO = "En muestra: 41 segmentos; el detector se ajustó con los mismos datos y aún no hay prueba ciega."
ETIQUETA_EN_MUESTRA = "en muestra"
# F20-P1: navegación agrupada (st.navigation). El orden de SECCIONES es el de la barra lateral.
GRUPOS_NAV = {"Revisión": ["Resumen", "Cola de revisión", "Explica una caja"], "Calidad de datos": ["Auditoría de cámaras"], "Análisis": ["Validación"],
              "Herramientas": ["Puntuar datos nuevos"], "Ayuda": ["Ética y límites", "Ayuda y glosario"]}
SECCIONES = [s for g in GRUPOS_NAV.values() for s in g]
ICONOS = {"Resumen": ":material/dashboard:", "Cola de revisión": ":material/format_list_numbered:", "Explica una caja": ":material/manage_search:", "Auditoría de cámaras": ":material/videocam:",
          "Validación": ":material/fact_check:", "Puntuar datos nuevos": ":material/upload_file:", "Ética y límites": ":material/balance:", "Ayuda y glosario": ":material/help:"}
ARCHIVO_PAGINA = {"Resumen": "paginas/resumen.py", "Cola de revisión": "paginas/cola.py", "Explica una caja": "paginas/explica.py", "Auditoría de cámaras": "paginas/auditoria.py",
                  "Validación": "paginas/validacion.py", "Puntuar datos nuevos": "paginas/puntuar.py", "Ética y límites": "paginas/etica.py", "Ayuda y glosario": "paginas/ayuda.py"}
URL_PAGINA = {"Resumen": "resumen", "Cola de revisión": "cola", "Explica una caja": "explica", "Auditoría de cámaras": "auditoria", "Validación": "validacion",
              "Puntuar datos nuevos": "puntuar", "Ética y límites": "etica", "Ayuda y glosario": "ayuda"}
DESCRIPCION_PAGINA = {"Cola de revisión": "Cajas 3D ordenadas por la probabilidad de no tener par 2D; se revisa de arriba hacia abajo.",
                      "Explica una caja": "Posición que ocupa una caja en la cola según sus puntos del sensor y su distancia.",
                      "Auditoría de cámaras": "Proporción de cajas con par 2D por segmento y cámara; las celdas con hueco se atienden aparte.",
                      "Validación": "Resultados guardados de EP3: hiperparámetros, ensambles, generalización, selección y análisis post hoc.",
                      "Puntuar datos nuevos": "Puntaje de un segmento nuevo con la solución congelada; el procesamiento es local y en memoria.",
                      "Ética y límites": "Ficha del sistema: propósito, datos, desempeño, límites, consideraciones éticas y entorno de ejecución.",
                      "Ayuda y glosario": "Flujo de revisión, glosario y preguntas frecuentes."}
CLASE_ADVERTENCIA = "Ciclista: poco confiable"
CLASE_NORMAL = "Peatón"
SUPUESTO_SEGUNDOS = 20
CURVA_UN_PASO = "Solución elegida, un paso (A)"
FLUJO_UNO = "Solo cola (un paso)"
FLUJO_DOS = "Auditoría + cola (dos pasos, en muestra)"
FLUJOS = {FLUJO_UNO: "uno", FLUJO_DOS: "dos"}


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


def resumen_cola(cajas: pd.DataFrame, curva: pd.DataFrame, solucion: str, segmento: str | None, presupuesto: float, segundos: float, flujo: str = "dos") -> dict[str, Any]:
    """Todo lo que muestra «Cola de revisión» con UNA sola fuente de valor: el conteo observado (``recall_proceso``). La curva solo aporta el IC.

    Devuelve SIEMPRE los dos flujos (F20-P4b): ``cobertura_dos`` (auditoría + cola, en muestra) y ``cobertura_uno`` (solo cola). ``top`` y las claves sin sufijo son las del ``flujo``
    elegido (por defecto, dos pasos, como antes).
    """
    top, info = cola_segmento(cajas, segmento, presupuesto, flujo)
    _, i2 = cola_segmento(cajas, segmento, presupuesto, "dos") if flujo != "dos" else (None, info)
    _, i1 = cola_segmento(cajas, segmento, presupuesto, "uno") if flujo != "uno" else (None, info)
    todos = segmento in (None, "Todos")
    nan = float("nan")

    def ic(nombre: str) -> tuple[float, float]:
        if not todos or not (curva["solucion"] == nombre).any():
            return nan, nan
        e = recall_en_presupuesto(curva, nombre, presupuesto)
        return e["lo"], e["hi"]

    sol_uno = CURVA_UN_PASO
    ic2, ic1 = ic(solucion), ic(sol_uno)
    esp = recall_en_presupuesto(curva, solucion, presupuesto)
    elegido = ic2 if flujo == "dos" else ic1
    return {"top": top, "todos": todos, "segmento": segmento, "presupuesto": presupuesto, "segundos": segundos, "flujo": flujo,
            "cobertura": info["recall_proceso"], "ic_lo": elegido[0], "ic_hi": elegido[1], "cobertura_curva": esp["recall"],
            "cobertura_dos": i2["recall_proceso"], "cobertura_uno": i1["recall_proceso"], "ic_dos": ic2, "ic_uno": ic1,
            "cajas_a_revisar_dos": i2["cajas_a_revisar"], "cajas_a_revisar_uno": i1["cajas_a_revisar"], "cajas_cola_total_dos": i2["cajas_cola_total"], "cajas_cola_total_uno": i1["cajas_cola_total"],
            "cajas_a_revisar": info["cajas_a_revisar"], "cajas_cola_total": info["cajas_cola_total"], "horas": horas_revision(info["cajas_a_revisar"], segundos),
            "hallados": info["positivos_auditoria"] + info["positivos_en_cola"], "hallados_dos": i2["positivos_auditoria"] + i2["positivos_en_cola"], "hallados_uno": i1["positivos_en_cola"],
            "positivos_total": info["positivos_total"], "positivos_auditoria": info["positivos_auditoria"],
            "n_segmentos": int(cajas["seg"].nunique()) if todos else 1}


def texto_resultado_cola(r: dict[str, Any]) -> str:
    """Frase principal (F20-P4b): SIEMPRE los dos flujos, el de dos pasos rotulado «en muestra». Distinta para todos los segmentos y para uno solo (sin IC)."""
    if r["todos"]:
        return (f"Con auditoría previa (en muestra): unas **{F.de_cada_100(r['cobertura_dos'])}** · Solo cola: unas **{F.de_cada_100(r['cobertura_uno'])}** "
                f"cajas sin pareja, en los {r['n_segmentos']} segmentos.")
    return (f"En el segmento {r['segmento']}: con auditoría previa (en muestra) se encontraron {F.entero(r['hallados_dos'])} de {F.entero(r['positivos_total'])} cajas sin pareja "
            f"({F.porcentaje(r['cobertura_dos'])}) · solo cola, {F.entero(r['hallados_uno'])} ({F.porcentaje(r['cobertura_uno'])}). Un solo segmento: no hay intervalo de confianza por segmentos.")


def texto_esfuerzo_cola(r: dict[str, Any]) -> str:
    """Segunda línea: cajas a revisar y horas del flujo elegido."""
    nombre = "Auditoría + cola" if r["flujo"] == "dos" else "Solo cola"
    return (f"{nombre}: {F.entero(r['cajas_a_revisar'])} cajas a revisar ({F.porcentaje(r['presupuesto'], 0)} de {F.entero(r['cajas_cola_total'])} en la cola) · "
            f"{F.horas(r['horas'], 1)} con {F.entero(r['segundos'])} s por caja (supuesto).")


COLUMNA_FOTOGRAMAS = "Fotogramas en la cola"
NOTA_FOTOGRAMAS = ("Un mismo objeto (por ejemplo, un peatón que camina) aparece en varios fotogramas y cada fotograma es una caja distinta de la cola. "
                   "La columna «" + COLUMNA_FOTOGRAMAS + "» cuenta cuántas filas de la cola son del mismo objeto: revisar una ayuda a revisar las otras. No cambia el orden de la cola.")


def tabla_cola(top: pd.DataFrame, cola_total: int, rangos: dict[int, tuple[float, float]], presentacion: bool, max_filas: int = 500) -> pd.DataFrame:
    """Tabla de la cola lista para mostrar (nombres legibles, formato es-CL). En modo presentación no lleva identificadores (ni el segmento).

    Orden de columnas: posición, segmento, cámara, **probabilidad calibrada de no tener pareja** (F20-P4e; reemplaza a «Prioridad», una barra saturada en 100), clase, tipo de caso,
    puntos, distancia, fotogramas del mismo objeto y, al final, los identificadores. No cambia el orden de las filas ni ninguna cifra. ``cola_total`` se conserva por compatibilidad.
    """
    t = top.head(max_filas).reset_index(drop=True)
    n = len(t)
    out = pd.DataFrame({"Posición": np.arange(1, n + 1)})
    if not presentacion:
        out["Segmento"] = t["seg"].to_numpy()
    out["Cámara"] = camara_de_azimut(t["az_signed"], rangos).to_numpy() if "az_signed" in t.columns else "—"
    out[COLUMNA_PROBABILIDAD] = t["prob_cal"].map(lambda v: F.porcentaje(v, 1)).to_numpy() if "prob_cal" in t.columns else "—"
    if "es_ciclista" in t.columns:
        out["Clase"] = np.where(t["es_ciclista"].to_numpy() == 1, CLASE_ADVERTENCIA, CLASE_NORMAL)
    out["Tipo de caso"] = t["tipo_caso"].to_numpy() if "tipo_caso" in t.columns else "—"
    out["Puntos sensor sup."] = t["num_top_lidar_points"].map(F.entero).to_numpy() if "num_top_lidar_points" in t.columns else "—"
    out["Distancia"] = t["distancia_m"].map(lambda v: f"{F.decimal(v, 1)} m").to_numpy() if "distancia_m" in t.columns else "—"
    if "key.laser_object_id" in top.columns and "seg" in top.columns:
        # cuántas filas (fotogramas) de la cola tiene el mismo objeto; se cuenta sobre TODA la cola elegida, no solo sobre las filas que se muestran
        cuenta = top.groupby(["seg", "key.laser_object_id"])["seg"].transform("size").to_numpy()[:max_filas]
        out[COLUMNA_FOTOGRAMAS] = cuenta
    if not presentacion:
        for col, nombre in (("key.frame_timestamp_micros", "Marca de tiempo"), ("key.laser_object_id", "Identificador de objeto")):
            if col in t.columns:
                out[nombre] = t[col].to_numpy()
    return out


COLUMNA_PROBABILIDAD = "Prob. sin pareja"
NOTA_AGRUPADO = "Vista agrupada: una fila por objeto. Es solo una vista; el conteo de cajas a revisar no cambia."


def tabla_por_objeto(top: pd.DataFrame, presentacion: bool, rangos: dict[int, tuple[float, float]] | None = None, max_filas: int = 500) -> pd.DataFrame:
    """Vista «Agrupar por objeto» (F20-P4f): una fila por objeto (segmento + identificador) con su mejor posición, su máxima probabilidad y los fotogramas en la cola.

    Solo reagrupa la cola que se le pasa: no cambia el orden ni el número de cajas a revisar. En modo presentación no hay identificadores (los objetos van numerados).
    """
    if top.empty or "key.laser_object_id" not in top.columns:
        return pd.DataFrame(columns=["Objeto", "Mejor posición", COLUMNA_PROBABILIDAD + " máxima", COLUMNA_FOTOGRAMAS])
    t = top.reset_index(drop=True).assign(_pos=lambda d: np.arange(1, len(d) + 1))
    agg = {"pos": ("_pos", "min"), "n": ("_pos", "size")}
    for nombre, col, fn in (("prob", "prob_cal", "max"), ("ciclista", "es_ciclista", "max"), ("tipo", "tipo_caso", "first"), ("az", "az_signed", "first")):
        if col in t.columns:
            agg[nombre] = (col, fn)
    g = t.groupby(["seg", "key.laser_object_id"], sort=False).agg(**agg).reset_index().sort_values("pos").head(max_filas)
    out = pd.DataFrame({"Objeto": np.arange(1, len(g) + 1) if presentacion else g["key.laser_object_id"].to_numpy()})
    if not presentacion:
        out.insert(0, "Segmento", g["seg"].to_numpy())
    out["Mejor posición"] = g["pos"].to_numpy()
    if "az" in g.columns:
        out["Cámara"] = camara_de_azimut(g["az"].reset_index(drop=True), rangos or {}).to_numpy()
    out[COLUMNA_PROBABILIDAD + " máxima"] = g["prob"].map(lambda v: F.porcentaje(v, 1)).to_numpy() if "prob" in g.columns else "—"
    if "ciclista" in g.columns:
        out["Clase"] = np.where(g["ciclista"].to_numpy() == 1, CLASE_ADVERTENCIA, CLASE_NORMAL)
    out["Tipo de caso"] = g["tipo"].to_numpy() if "tipo" in g.columns else "—"
    out[COLUMNA_FOTOGRAMAS] = g["n"].to_numpy()
    return out


def filtrar_cola(tabla: pd.DataFrame, clases: list[str] | None = None, camaras: list[str] | None = None) -> pd.DataFrame:
    """Filtra la TABLA (la vista) por clase y cámara. No toca las cifras globales de la cola: solo cambia qué filas se muestran (F20-P4h)."""
    out = tabla
    if clases and "Clase" in out.columns:
        out = out[out["Clase"].isin(clases)]
    if camaras and "Cámara" in out.columns:
        out = out[out["Cámara"].isin(camaras)]
    return out


def detalle_caja(top: pd.DataFrame, posicion: int, cola_total: int, rangos: dict[int, tuple[float, float]], ciclistas: dict[str, float] | None = None) -> dict[str, Any]:
    """Detalle de la caja de la fila ``posicion`` (1 = primera de la cola) para el panel de la cola; reutiliza ``explicacion_caja`` de «Explica una caja»."""
    f = top.iloc[posicion - 1]
    es_c = bool(f.get("es_ciclista", 0) == 1)
    prob = float(f["prob_cal"]) if "prob_cal" in f.index else float("nan")
    pc = (posicion - 1) / max(cola_total, 1)
    cam = camara_de_azimut(pd.Series([f["az_signed"]]), rangos).iloc[0] if "az_signed" in f.index else "—"
    pts_top = float(f["num_top_lidar_points"]) if "num_top_lidar_points" in f.index else float("nan")
    dist = float(f["distancia_m"]) if "distancia_m" in f.index else float("nan")
    return {"posicion": posicion, "cola_total": cola_total, "percentil": pc, "prob": prob, "camara": cam, "distancia": dist, "puntos_sup": pts_top,
            "puntos": float(f["num_lidar_points"]) if "num_lidar_points" in f.index else float("nan"), "es_ciclista": es_c, "tipo_caso": str(f.get("tipo_caso", "—")),
            "clase": CLASE_ADVERTENCIA if es_c else CLASE_NORMAL, "segmento": str(f.get("seg", "")), "texto": explicacion_caja(pts_top, dist, es_c, pc, prob),
            "advertencia_ciclista": es_c}


def inicio_resumen(D: dict[str, Any], segundos: float = SUPUESTO_SEGUNDOS) -> dict[str, Any]:
    """Cifras del Resumen. Horas = fracción de cajas para el 80 % × cajas × segundos / 3600: ESTIMACIÓN con un supuesto de segundos por caja, en muestra.

    ``horas_sin_orden`` = 80 % de las cajas; ``horas_un_paso`` = fracción un paso (``Fraccion_80_A``); ``horas_dos_pasos`` = fracción dos pasos (``Fraccion_80_C``).
    Todas salen de ``ie12__brazo_C_y_equilibrio`` (copia de f6_modelo_escogido / f5_brazoC) y del número de cajas.
    """
    cajas = D["cajas"]
    n = len(cajas)
    ev = D.get("evidencia", {}).get("ie12__brazo_C_y_equilibrio")
    horas = None
    frac_c = frac_a = None
    horas_dos_pasos = horas_sin_orden = horas_un_paso = None
    if ev is not None and not ev.empty:
        cand = D.get("kpis", {}).get("candidato")
        fila = ev[ev["candidato"] == cand].iloc[0] if cand in set(ev["candidato"]) else ev.iloc[0]
        frac_c = float(fila["Fraccion_80_C"])
        horas = max((0.8 - frac_c) * n * segundos / 3600.0, 0.0)
        horas_dos_pasos, horas_sin_orden = frac_c * n * segundos / 3600.0, 0.8 * n * segundos / 3600.0
        if "Fraccion_80_A" in fila.index:
            frac_a = float(fila["Fraccion_80_A"])
            horas_un_paso = frac_a * n * segundos / 3600.0
    return {"cajas": n, "prevalencia": float(cajas["sin_camara"].mean()), "celdas_marcadas": int(len(D["lista_A"])), "segmentos_con_hueco": int(D["lista_A"]["segmento"].nunique()),
            "horas_ahorradas": horas, "horas_dos_pasos": horas_dos_pasos, "horas_sin_orden": horas_sin_orden, "horas_un_paso": horas_un_paso, "fraccion_80_dos_pasos": frac_c,
            "fraccion_80_un_paso": frac_a, "segmentos": int(cajas["seg"].nunique())}


def alertas_resumen(r: dict[str, Any], ciclistas: dict[str, float], perfil: str | None = None) -> list[dict[str, str]]:
    """Las tres alertas del Resumen (F20-P3): celdas marcadas, ciclistas y validación externa pendiente. Primero la del rol; cada una con la sección a la que lleva."""
    c = ciclistas or {}
    hay = all(isinstance(c.get(k), float) and c[k] == c[k] for k in ("ciclista", "peaton", "positivos", "segmentos"))
    txt_c = (f"En ciclistas la regla encuentra {F.decimal(c['ciclista'], 3)} de los casos contra {F.decimal(c['peaton'], 3)} en peatones ({F.entero(c['positivos'])} casos en {F.entero(c['segmentos'])} segmentos)."
             if hay else "En ciclistas la regla es poco confiable.")
    alertas = {
        "celdas": {"clave": "celdas", "titulo": "Celdas marcadas", "texto": f"{F.entero(r['celdas_marcadas'])} celdas (segmento × cámara) en {F.entero(r['segmentos_con_hueco'])} segmentos se atienden aparte de la cola.",
                   "seccion": "Auditoría de cámaras", "tono": "hueco"},
        "ciclistas": {"clave": "ciclistas", "titulo": "Ciclistas: regla poco confiable", "texto": txt_c, "seccion": "Ética y límites", "tono": "aviso"},
        "validacion": {"clave": "validacion", "titulo": "Validación externa pendiente", "texto": "La validación con segmentos nuevos está preparada y sellada; todavía no se ejecutó. Todas las cifras son en muestra.",
                       "seccion": "Validación", "tono": "aviso"},
    }
    primera = PERFILES.get(perfil or "", {}).get("alerta")
    orden = ([primera] if primera in alertas else []) + [k for k in ("celdas", "ciclistas", "validacion") if k != primera]
    return [alertas[k] for k in orden]


ACCION_SUGERIDA = "Completar etiquetas 2D o reportar el dato faltante"
_UBICACION = {"location_sf": "San Francisco", "location_phx": "Phoenix", "location_other": "Otras"}
_MOMENTO = {"Day": "Día", "Night": "Noche", "Dawn/Dusk": "Amanecer o atardecer"}


def lista_A_presentable(lista_A: pd.DataFrame) -> pd.DataFrame:
    """Lista A para mostrar SIN desplazarse (F19-B3): encabezados cortos y la «Acción sugerida» breve; ubicación y mediana van en ``lista_A_detalle``."""
    cols = {"segmento": "Segmento", "camara": "Cámara", "tasa": "Tasa", "cajas_en_rango": "En el rango", "cajas_afectadas_poblacion_principal": "Cajas afectadas", "positivos_afectados": "Sin pareja"}
    out = pd.DataFrame()
    for c, nombre in cols.items():
        if c in lista_A.columns:
            v = lista_A[c]
            if c == "tasa":
                out[nombre] = v.map(lambda x: F.porcentaje(x, 0))
            elif c in ("cajas_en_rango", "cajas_afectadas_poblacion_principal", "positivos_afectados"):
                out[nombre] = v.map(F.entero)
            else:
                out[nombre] = v
    out["Acción sugerida"] = ACCION_SUGERIDA
    return out


def lista_A_detalle(lista_A: pd.DataFrame) -> pd.DataFrame:
    """Detalle de la Lista A que no cabe en la tabla principal: ubicación, momento del día, mediana de la cámara y umbral de hueco."""
    out = pd.DataFrame()
    for c, nombre in (("segmento", "Segmento"), ("camara", "Cámara")):
        if c in lista_A.columns:
            out[nombre] = lista_A[c]
    if "tasa" in lista_A.columns:
        out["Tasa"] = lista_A["tasa"].map(lambda x: F.porcentaje(x, 0))
    if "cajas_en_rango" in lista_A.columns:
        out["En el rango"] = lista_A["cajas_en_rango"].map(F.entero)
    if "ubicacion" in lista_A.columns:
        out["Ubicación"] = lista_A["ubicacion"].map(_UBICACION).fillna(lista_A["ubicacion"])
    if "momento" in lista_A.columns:
        out["Momento del día"] = lista_A["momento"].map(_MOMENTO).fillna(lista_A["momento"])
    if "mediana_camara" in lista_A.columns:
        out["Mediana de la cámara"] = lista_A["mediana_camara"].map(lambda x: F.porcentaje(x, 0))
    if "umbral" in lista_A.columns:
        out["Umbral de hueco"] = lista_A["umbral"].map(lambda x: F.porcentaje(x, 0))
    return out


EJEMPLOS_CAJA = {"Caja cercana y densa": {"pts": 400, "top": 300, "dist": 8.0, "clase": "Peatón"},
                 "Caja lejana con pocos puntos": {"pts": 8, "top": 6, "dist": 70.0, "clase": "Peatón"},
                 "Ciclista lejano": {"pts": 25, "top": 20, "dist": 55.0, "clase": "Ciclista"}}


def texto_posicion(percentil: float) -> str:
    """Significado exacto de ``percentil_en_cola``: fracción de la cola que queda ANTES de la caja (0 % = primera, 100 % = última)."""
    return f"Posición en la cola: {F.porcentaje(percentil, 0)} (0 % es la primera caja; 100 %, la última)"


def explicacion_caja(puntos_top: float, distancia: float, es_ciclista: bool, percentil: float, prob: float) -> str:
    """Una frase que explica el resultado de «Explica una caja» y del panel de detalle de la cola."""
    base = (f"Con {F.entero(puntos_top)} puntos del sensor superior y a {F.decimal(distancia, 0)} m, el {F.porcentaje(percentil, 0)} de las cajas de la cola queda antes que esta, "
            f"y la probabilidad estimada de que no tenga par en ninguna cámara es {F.porcentaje(prob)}.")
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
        out["ie11"] = (f"La regla de puntos tiene AUC {F.decimal(r['AUC'], 3)} fuera de pliegue; ningún candidato alcanza el AUC mínimo por pliegue de 0,75 "
                       f"(el mejor llega a {F.decimal(t['AUC_min_fold'].max(), 3)}), por el pliegue 0.")
    except (KeyError, IndexError):
        out["ie11"] = "Métricas fuera de pliegue de los candidatos."
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
        out["posthoc"] = f"Con la celda con hueco fuera, el AUC de la regla en el pliegue 0 pasa de {F.decimal(f0['AUC_A'], 3)} a {F.decimal(f0['AUC_B_celdas_sanas'], 3)} (post hoc, en muestra, no pre-declarado)."
    except (KeyError, IndexError):
        out["posthoc"] = "Todo lo de esta pestaña es post hoc, no pre-declarado."
    return out


def datos_validacion(ev: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Tablas ya preparadas para el gráfico con que abre cada pestaña de «Validación» (F20-P7). Todo sale de los CSV de ``data/09_app_ep3/evidencia`` (copias de EP3):
    ``ie9`` de f3_defecto_vs_optimizado, ``ie10`` de f4_ensambles_aporta, ``ie11`` de f5_metricas_candidatos, ``ie11_pliegues`` de f5_auc_por_fold (solo los candidatos que trae la copia),
    ``nosup`` de f13_clusters_k2 y ``brazos`` de f12_auc_por_fold_brazos (fila global). Las claves faltan si la tabla no está."""
    out: dict[str, pd.DataFrame] = {}
    if "ie9__defecto_vs_optimizado" in ev:
        t = ev["ie9__defecto_vs_optimizado"]
        out["ie9"] = pd.DataFrame({"Modelo": t["modelo"], "Mejora": t["dif_PR-AUC"], "lo": t["dif_PR-AUC_lo"], "hi": t["dif_PR-AUC_hi"], "Veredicto": t["veredicto"].map({"mejora": "mejora", "no mejora": "no mejora"})})
    if "ie10__ensambles_aportan" in ev:
        t = ev["ie10__ensambles_aportan"]
        out["ie10"] = pd.DataFrame({"Ensamble": t["ensamble"], "Mejora": t["dif_AUC"], "lo": t["dif_lo"], "hi": t["dif_hi"], "Veredicto": t["veredicto"], "Mejor componente": t["mejor_componente"]})
    if "ie11__metricas_de_generalizacion" in ev:
        t = ev["ie11__metricas_de_generalizacion"]
        out["ie11"] = pd.DataFrame({"Candidato": t["candidato"], "AUC": t["AUC"], "lo": t["AUC_lo"], "hi": t["AUC_hi"]})
    if "posthoc__auc_por_fold_y_brazos" in ev:
        t = ev["posthoc__auc_por_fold_y_brazos"]
        t = t.assign(fold=t["fold"].astype(str))
        pl = t[t["fold"] != "global"]
        out["ie11_pliegues"] = pd.DataFrame({"Candidato": pl["candidato"], "Pliegue": pl["fold"], "AUC": pl["AUC_A"]})
        g = t[t["fold"] == "global"]
        if not g.empty:
            out["brazos"] = pd.concat([
                pd.DataFrame({"Candidato": g["candidato"], "Brazo": "A: solo cola (un paso)", "Fraccion": g["Fraccion80_A"]}),
                pd.DataFrame({"Candidato": g["candidato"], "Brazo": "B: celdas sanas, sin auditoría", "Fraccion": g["Fraccion80_B_celdas_sanas"]}),
                pd.DataFrame({"Candidato": g["candidato"], "Brazo": "C: auditoría + cola (dos pasos)", "Fraccion": g["Fraccion80_C"]})], ignore_index=True)
    if "nosup__clusters_k2" in ev:
        t = ev["nosup__clusters_k2"]
        out["nosup"] = pd.DataFrame({"Tipo de caso": t["tipo_de_caso"], "Tasa": t["tasa_sin_camara"], "lo": t["ic_lo"], "hi": t["ic_hi"], "Cajas": t["cajas"]})
    return out


def tabla_resultados_clave(K: dict[str, Any]) -> pd.DataFrame:
    """Las cinco cifras de validación que antes estaban en «Resultados técnicos» de Inicio (``kpis.json``), como tabla: resultado, valor, detalle y archivo de origen."""
    filas = [{"Resultado": F.traducir_folds(x.get("titulo", "")), "Valor": formatear_kpi(x.get("valor", "")), "Detalle": F.traducir_folds(formatear_kpi(x.get("ic", ""))), "Fuente": x.get("fuente", "")}
             for x in K.get("tarjetas", [])]
    return pd.DataFrame(filas, columns=["Resultado", "Valor", "Detalle", "Fuente"])


def ejemplo_lidar_box(cajas: pd.DataFrame, segmento: str) -> pd.DataFrame:
    """Un lidar_box mínimo reconstruido desde las variables derivadas de ``cajas_oof`` para un segmento de desarrollo (F20-P8): no son datos crudos de Waymo.

    Trae solo lo que ``puntuar_segmento`` necesita (llaves, tipo, caja, puntos, rumbo y velocidad). El archivo de asociación con cámaras NO se puede reconstruir sin inventar a qué
    cámara pertenece cada caja, así que el ejemplo se puntúa sin él (no hay auditoría de cámaras).
    """
    d = cajas[cajas["seg"] == segmento]
    pre = "[LiDARBoxComponent]."
    return pd.DataFrame({
        "key.segment_context_name": d["seg"].to_numpy(), "key.frame_timestamp_micros": d["key.frame_timestamp_micros"].to_numpy(), "key.laser_object_id": d["key.laser_object_id"].to_numpy(),
        pre + "type": np.where(d["es_ciclista"].to_numpy() == 1, 4, 2),
        pre + "box.center.x": d["box_center_x"].to_numpy(), pre + "box.center.y": d["box_center_y"].to_numpy(), pre + "box.center.z": d["box_center_z"].to_numpy(),
        pre + "box.size.x": d["box_length"].to_numpy(), pre + "box.size.y": d["box_width"].to_numpy(), pre + "box.size.z": d["box_height"].to_numpy(),
        pre + "box.heading": np.arctan2(d["heading_sin"].to_numpy(), d["heading_cos"].to_numpy()),
        pre + "num_lidar_points_in_box": d["num_lidar_points"].to_numpy(), pre + "num_top_lidar_points_in_box": d["num_top_lidar_points"].to_numpy(),
        pre + "speed.x": d["speed_mps"].fillna(0.0).to_numpy(), pre + "speed.y": 0.0}).reset_index(drop=True)


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
    ciclistas = "En ciclistas la regla es poco confiable: conviene revisarlos con más cuidado."
    if equidad is not None and not equidad.empty:
        try:
            c = equidad[(equidad["grupo"] == "CYCLIST") & (equidad["celdas_con_hueco"] == "incluidas")].iloc[0]
            p = equidad[(equidad["grupo"] == "PEDESTRIAN") & (equidad["celdas_con_hueco"] == "incluidas")].iloc[0]
            ciclistas = (f"En ciclistas la regla es poco confiable: encuentra {F.decimal(c['recall_A'], 3)} de los casos contra {F.decimal(p['recall_A'], 3)} en peatones, "
                         f"con solo {F.entero(c['positivos'])} casos en {F.entero(c['segmentos'])} segmentos. Conviene revisarlos con más cuidado.")
        except (KeyError, IndexError):
            pass
    return [
        ("¿El sistema decide qué cajas están mal?", "No. Solo ordena. Una persona revisa y decide; ninguna caja se descarta sin revisarla."),
        ("¿Qué significa «en muestra»?", "Que el resultado se calculó con 41 segmentos y el detector de huecos se ajustó con esos mismos datos; todavía no hay una prueba con segmentos nuevos."),
        ("¿Qué pasa con los ciclistas?", ciclistas),
        ("¿Se guardan o se envían los archivos?", "No. Nada se guarda ni se envía: «Puntuar datos nuevos» procesa el archivo en memoria y la aplicación no hace ninguna conexión a internet."),
        ("¿Cuánto tarda revisar una caja?", f"No se midió: se usa un supuesto de {SUPUESTO_SEGUNDOS} segundos por caja, editable en «Supuestos» de la cola de revisión."),
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
                ". Se espera el parquet del componente lidar_box de un segmento.")
    return None


def validar_asociacion(df: pd.DataFrame) -> str | None:
    """Mensaje amigable si al archivo de asociación le faltan columnas; ``None`` si está completo."""
    faltan = [c for c in ("key.segment_context_name", "key.camera_name", "key.frame_timestamp_micros", "key.laser_object_id") if c not in df.columns]
    if faltan:
        return "Este archivo no parece camera_to_lidar_box_association: faltan las columnas " + ", ".join(f"«{c}»" for c in faltan) + ". Sin este archivo se puntúa igual, pero no hay auditoría de cámaras."
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
