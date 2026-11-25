"""Lógica pura de la página de EP3 (sin Streamlit), para poder probarla.

La app lee solo ``data/09_app_ep3`` (predicciones fuera de fold, es decir, honestas) y los artefactos
congelados de ``data/06_models_ep3``. Ningún dato sale del equipo.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

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
    },
    "Responsable de calidad de datos": {
        "pregunta": "¿Qué cámaras o segmentos tienen un problema sistemático?",
        "seccion": "Auditoría de cámaras",
        "mensaje": "Una cámara con tasa de pares muy baja suele ser un problema de etiquetado o de datos, no de cajas sueltas: se atiende aparte.",
    },
    "Ingeniero consumidor de datos": {
        "pregunta": "¿Se puede confiar en las etiquetas 2D de un segmento nuevo?",
        "seccion": "Puntuar datos nuevos",
        "mensaje": "Un segmento nuevo se puntúa en el equipo y entrega la lista de celdas sospechosas y la cola de cajas.",
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


def estado_camaras_segmento(m: pd.DataFrame, seg: str) -> dict[int, str]:
    """Estado de cada cámara en un segmento para el anillo del Resumen (F23): ``hueco``, ``sin_datos`` o ``sana``, los mismos tres estados del mapa de calor.

    ``m`` es la salida de ``matriz_calor``. No calcula nada nuevo: lee las columnas ``hueco`` y ``sin_datos`` que ya trae. Una cámara sin fila en ese segmento sale como ``sin_datos``.
    """
    fila = m[m["seg"] == seg]
    out: dict[int, str] = {}
    for cam, nombre in CAMARAS.items():
        f = fila[fila["camara"] == nombre]
        if f.empty:
            out[cam] = "sin_datos"
        elif bool(f["hueco"].iloc[0]):
            out[cam] = "hueco"
        elif bool(f["sin_datos"].iloc[0]):
            out[cam] = "sin_datos"
        else:
            out[cam] = "sana"
    return out


def camaras_con_celdas_marcadas(lista_a: pd.DataFrame) -> dict[int, int]:
    """Cuántas celdas marcadas (Lista A) tiene cada cámara, por número de cámara."""
    cuenta: dict[int, int] = {}
    if lista_a is not None and "camara" in lista_a.columns:
        for c in lista_a["camara"].astype(str):
            if c[:1].isdigit():
                cuenta[int(c[0])] = cuenta.get(int(c[0]), 0) + 1
    return cuenta


PLAN_V3 = Path(__file__).resolve().parents[3] / "docs" / "ep3" / "plan_v3.json"
CRITERIOS_SELECCION = (("O1", "Discrimina"), ("O2", "Vale la pena"), ("O3", "Recall en el punto A"), ("O4", "Estable y calibrada"))


def criterios_seleccion(plan: dict[str, Any] | None = None) -> list[tuple[str, str, str]]:
    """Los criterios de selección O1 a O4 con nombre propio y su definición (F23): (clave, nombre, definición).

    Los umbrales se leen del plan v3 congelado (``docs/ep3/plan_v3.json``, solo lectura); si el plan no está a mano, la definición sale sin números. No decide nada: el cumplimiento de cada
    candidato sale de la tabla de selección de EP3.
    """
    from waymo_evaluacion.ep3 import formato as F

    if plan is None:
        try:
            plan = json.loads(PLAN_V3.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            plan = {}
    try:
        o = plan["P8"]["objetivos"]
        e = plan["P7"]["estabilidad"]
        d = {
            "O1": f"AUC de al menos {F.decimal(o['O1']['auc_min'], 2)} y PR-AUC menos prevalencia de al menos {F.decimal(o['O1']['pr_auc_menos_prevalencia_min'], 2)}.",
            "O2": (f"La fracción de cajas para encontrar el 80 % baja al menos {F.entero(o['O2']['fraccion_80_baja_min_puntos'])} puntos frente a la regla, con intervalo pareado que excluye 0, "
                   f"y el AUC sube al menos {F.decimal(o['O2']['auc_sube_min'], 2)}."),
            "O3": f"Recall de al menos {F.decimal(o['O3']['recall_punto_A_min'], 2)} en el punto A.",
            "O4": f"AUC mínimo por partición de al menos {F.decimal(e['auc_min_fold'], 2)} y ECE de a lo sumo {F.decimal(o['O4']['ece_max'], 2)}.",
        }
    except (KeyError, TypeError):
        d = {"O1": "AUC y PR-AUC mínimos del plan.", "O2": "Vale la pena frente a la regla, según el plan.", "O3": "Recall mínimo en el punto A, según el plan.", "O4": "Estabilidad por partición y calibración, según el plan."}
    return [(k, nombre, d[k]) for k, nombre in CRITERIOS_SELECCION]


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

# F26: identidad de la página. Cada texto vive en UNA constante; se cambia aquí y la página, el favicon, la guía y los documentos lo siguen.
NOMBRE_PRODUCTO = "Lente"
SUBLINEA_MARCA = "Waymo Open Dataset v2"
TITULO_RESUMEN = "Estado de las cámaras"                       # título grande del Resumen; la etiqueta del menú sigue siendo SECCIONES[0] («Resumen»)
SUBTITULO_RESUMEN = "Etiquetas 2D de peatones y ciclistas en {n} segmentos."
# F29: Resumen para uso diario (indicadores, alertas de cámara, cola y segmentos prioritarios). La hipótesis sigue siendo «posible hueco», no «cámara defectuosa».
KICKER_ALERTAS = "Alertas de cámara"
TITULAR_ALERTAS = "Hay {huecos} en los últimos datos sin revisar."            # {huecos}: «N posibles huecos de cámara», en color de alerta
TITULAR_ALERTAS_UNO = "Hay {huecos} en los últimos datos sin revisar."
TITULAR_SIN_ALERTAS = "Todas las cámaras sanas."
SUBTITULO_ALERTAS = "Se revisaron {n} segmentos. Estas celdas se auditan aparte de la cola."
SUBTITULO_SIN_ALERTAS = "Última actualización de los datos: {hora}."
ACCION_AUDITAR = "Auditar"
ESTADO_HUECO = "Hueco"
TITULO_COLA_RESUMEN = "Cola de revisión"
SUBTITULO_COLA_RESUMEN = "Qué caja revisar primero, ordenadas por probabilidad de no tener par 2D en ninguna cámara."
ENLACE_COLA = "Abrir la cola completa"
ACCION_ABRIR = "Abrir"
ETIQUETA_CICLISTA = "Regla poco confiable"
NOTA_ORDEN_COLA = "Las cajas con igual probabilidad se ordenan por segmento y número de caja, para que la lista nunca repita filas idénticas."
TITULO_SEGMENTOS_PRIORITARIOS = "Segmentos con más cajas prioritarias"
SUBTITULO_SEGMENTOS_PRIORITARIOS = "Útil para repartir el trabajo del turno."
# F27: el menú sigue el orden del proceso (la hipótesis sigue siendo «posible hueco», no «cámara defectuosa»).
# F31: Auditoría de cámaras (franja de resumen, una sola tabla de celdas marcadas, anillo, mapa con las filas peores y desplegable de la definición).
AUD_DEFINICION = "Hueco: cámara que, en un segmento, tiene menos del {frac} de los pares 2D que le corresponden. Es una hipótesis para revisar, no una conclusión."
AUD_TITULAR = "{huecos} en los últimos datos sin revisar."                      # {huecos}: «N posibles huecos de cámara»
AUD_TITULAR_CERO = "Ninguna cámara tiene posibles huecos en los últimos datos sin revisar."
AUD_NOTA_DESARROLLO = "Las cifras salen de los {n} segmentos de desarrollo."
AUD_TITULO_TABLA = "Celdas marcadas"
AUD_AYUDA_TABLA = "Ordenadas por cajas afectadas. Qué hacer: completar las etiquetas 2D o reportar el dato faltante."
AUD_AVISO_CELDA = "Celda resaltada en el mapa: segmento {segmento}, cámara {camara} ({nombre}). {origen}"
AUD_ORIGEN_RESUMEN = "Llegó desde «Auditar» del Resumen o con un clic en esta fila."
AUD_ORIGEN_FILA = "Un clic en otra fila de la tabla resalta otra celda."
AUD_TITULO_ANILLO = "Celdas marcadas por cámara"
AUD_TITULO_MAPA = "Mapa segmento × cámara"
AUD_AYUDA_MAPA = "Sirve para ver si falla una cámara en muchos segmentos o solo una celda. Primero van los segmentos con celdas marcadas."
AUD_QUE_ES = "¿Qué es un hueco?"
ENLACE_COLA_DESDE_AUDITORIA = "Ir a la cola de revisión →"
# F32: Cola de revisión (plan arriba, tres tarjetas, «Cola de cajas» primero, tabla de 50 en 50, panel de detalle y supuestos plegados).
COLA_TAB_LISTA = "Cola de cajas"
COLA_TAB_CURVA = "Curva de priorización"
COLA_SUPUESTOS = "Supuestos y confiabilidad"
COLA_BOTON_EXPLICAR = "Explicar esta caja →"
COLA_TITULO_CURVA = "Cajas sin pareja que se encuentran según cuánto se revisa"
COLA_NOTA_BANDA = "Banda sombreada: intervalo del 95 % por segmentos (ancho porque son solo {n} segmentos)."
COLA_LLAMADA = "Revisando el {presupuesto}: {dos} (dos pasos), {uno} (un paso)"
FILAS_PAGINA_COLA = 50                                           # filas de la tabla por página (en vez de 500 con desplazamiento interno)
# F33: Explica una caja (ejemplos como botones, un solo control decide, resultado y veredicto primero, lugar en una barra, cuatro pasos con valores vivos, gráfico con rótulos directos).
EXP_VEREDICTO_SI = "Se revisaría con un presupuesto del {presupuesto}"
EXP_VEREDICTO_NO = "No se revisaría con un presupuesto del {presupuesto}"
EXP_DETALLE_SI = "Está dentro del {presupuesto} que se revisa primero."
EXP_DETALLE_NO = "Entraría si se revisara más del {posicion} de la cola."
EXP_LUGAR_TEXTO = "El {posicion} de las cajas de la cola queda antes que esta."
EXP_LUGAR_EMPATE = "Está entre las primeras {n} cajas de la cola: todas tienen {puntos} puntos del sensor superior y empatan en la prioridad máxima."
EXP_ROTULO_REVISA = "Se revisa hasta aquí"
EXP_ROTULO_80 = "Para hallar el 80 % de las sin pareja"
EXP_ETIQUETA_COLA = "De la cola · caja {caja}"
EXP_AVISO_ORIGEN = "Valores cargados desde {origen}: caja {caja}, prioridad {prioridad}."
EXP_ENLACE_VOLVER = "← Volver a {destino}"
EXP_PASOS = ("1 · Entrada", "2 · Puntaje", "3 · Probabilidad", "4 · Lugar")
EXP_PASOS_DETALLE = ("del sensor superior", "menos los puntos del sensor superior", "la calibración lo convierte en probabilidad", "fracción de las cajas que quedan antes")
EXP_AVISO_CICLISTA = "{etiqueta} en ciclistas."
FILAS_MAPA_INICIO = 10                                           # filas del mapa que se ven al abrir (las peores)
PASO_MAPA = 50                                                   # cuántas filas más se agregan por clic cuando hay muchos segmentos
UMBRAL_TODOS_MAPA = 60                                           # hasta este número de segmentos, un clic muestra todos
PRESUPUESTO_VISTA_RESUMEN = 0.20                                 # el mismo 20 % con que abre «Cola de revisión»
FILAS_COLA_RESUMEN = 5
FILAS_ALERTAS_RESUMEN = 5
SEGMENTOS_PRIORITARIOS_RESUMEN = 5
# Texto provisional de la licencia (reconstruido): contrastarlo con waymo.com/open/terms antes de entregar.
ATRIBUCION_WAYMO = ("This application was made using the Waymo Open Dataset, provided by Waymo LLC under the Waymo Dataset License Agreement for Non-Commercial Use "
                    "(see waymo.com/open/terms).")
PRODUCTO = NOMBRE_PRODUCTO
ESLOGAN = "Revisión priorizada de cajas 3D de peatones y ciclistas sin par 2D."
VERSION_PRODUCTO = "EP3"
AVISO_CORTO = "En muestra: 41 segmentos; el detector se ajustó con los mismos datos y aún no hay prueba ciega."
ETIQUETA_EN_MUESTRA = "en muestra"
# F20-P1: navegación agrupada (st.navigation). El orden de SECCIONES es el de la barra lateral.
# F27: el menú sigue el orden del proceso: primero el filtro de cámaras (paso 1) y después la priorización de cajas (paso 2). Los nombres de las secciones no cambian.
PASO_FILTRO = "1 · Filtro"
PASO_PRIORIZACION = "2 · Priorización"
GRUPOS_NAV = {"Visión general": ["Resumen"], PASO_FILTRO: ["Auditoría de cámaras"], PASO_PRIORIZACION: ["Cola de revisión"], "Análisis": ["Validación"],
              "Herramientas": ["Explica una caja", "Puntuar datos nuevos"], "Ayuda": ["Ética y límites", "Ayuda y glosario"]}          # F33: «Explica una caja» pasa a «Herramientas» (no es parte del recorrido diario; se entra desde la Cola)
SECCIONES = [s for g in GRUPOS_NAV.values() for s in g]
ICONOS = {"Resumen": ":material/dashboard:", "Cola de revisión": ":material/format_list_numbered:", "Explica una caja": ":material/manage_search:", "Auditoría de cámaras": ":material/videocam:",
          "Validación": ":material/fact_check:", "Puntuar datos nuevos": ":material/upload_file:", "Ética y límites": ":material/balance:", "Ayuda y glosario": ":material/help:"}
ARCHIVO_PAGINA = {"Resumen": "paginas/resumen.py", "Cola de revisión": "paginas/cola.py", "Explica una caja": "paginas/explica.py", "Auditoría de cámaras": "paginas/auditoria.py",
                  "Validación": "paginas/validacion.py", "Puntuar datos nuevos": "paginas/puntuar.py", "Ética y límites": "paginas/etica.py", "Ayuda y glosario": "paginas/ayuda.py"}
URL_PAGINA = {"Resumen": "resumen", "Cola de revisión": "cola", "Explica una caja": "explica", "Auditoría de cámaras": "auditoria", "Validación": "validacion",
              "Puntuar datos nuevos": "puntuar", "Ética y límites": "etica", "Ayuda y glosario": "ayuda"}
DESCRIPCION_PAGINA = {"Cola de revisión": "Qué cajas revisar y en qué orden. Se revisa de arriba hacia abajo.",
                      "Explica una caja": "Cambiando los datos de una caja se ve qué lugar ocuparía en la cola y si se revisaría.",
                      "Auditoría de cámaras": "Qué cámaras tienen huecos en qué segmentos; esas celdas se atienden aparte de la cola.",
                      "Validación": "Qué se probó para elegir la regla, qué tan bien funciona y qué falta por demostrar.",
                      "Ética y límites": "Ficha del sistema: propósito, datos, desempeño, límites, consideraciones éticas y entorno de ejecución.",
                      "Ayuda y glosario": "Flujo de revisión, glosario y preguntas frecuentes."}
# F26-B1 y F36: textos que dependen de cómo se despliega la página. UNA sola constante, ``MODO_DESPLIEGUE``, decide cuáles se muestran: ``local`` (por defecto) dice lo que es verdad en el equipo de la persona;
# ``publicado`` es la variante para la instancia EC2 de AWS Academy (F43: redactada contra cómo corre ahí). **No está activada** hasta que el equipo apruebe sus textos: mientras tanto llevan la marca visible «borrador: verificar» (clave ``borrador``), que hay que
# quitar (dejarla vacía) al aprobarlos. Para probarla sin tocar el archivo se puede fijar la variable de entorno ``EP3_ENTORNO=publicado`` (también acepta ``servidor``); la variable manda sobre la constante.
# Los archivos cargados NO se escriben a disco: ``puntuar_segmento`` trabaja en memoria y la página no llama a ``guardar`` (lo vigila una prueba).
MODO_DESPLIEGUE = "local"
MODOS_DESPLIEGUE = ("local", "publicado")
TEXTOS_ENTORNO = {
    "local": {
        "donde_corre": "Solo en este equipo (localhost), sin conexión a internet. No debe exponerse en una red sin autenticación.",
        "puntuar_subtitulo": "Un segmento nuevo se puntúa con la solución congelada y se obtienen sus celdas marcadas y su cola de cajas.",
        "puntuar_etiqueta": "Procesamiento local y en memoria",
        "puntuar_etiqueta_2": "No se guarda nada",
        "consideracion_etica": "Las tablas locales tienen identificadores de objeto y marcas de tiempo. Nada se guarda ni se envía.",
        "faq_archivos": "No. Nada se guarda ni se envía: «Puntuar datos nuevos» procesa el archivo en memoria y la aplicación no hace ninguna conexión a internet.",
        "borrador": "",
    },
    "publicado": {
        "donde_corre": "En un servidor de AWS (instancia EC2 de AWS Academy, región us-east-1), no en su equipo. La aplicación no tiene inicio de sesión: solo la abre quien llegue a su dirección, y el acceso lo restringe el grupo de seguridad de la instancia. La dirección es temporal y cambia si la instancia se detiene. No se deben subir datos que no puedan compartirse con ese servidor.",
        "puntuar_subtitulo": "Un segmento nuevo se puntúa con la solución congelada y se obtienen sus celdas marcadas y su cola de cajas; en esta página el procesamiento ocurre en el servidor.",
        "puntuar_etiqueta": "Procesamiento en el servidor y en memoria",
        "puntuar_etiqueta_2": "No se guardan los archivos",
        "consideracion_etica": "Las tablas de la página tienen identificadores de objeto y marcas de tiempo, sin imágenes. El servidor SÍ recibe los archivos que se suben en «Puntuar datos nuevos»: los procesa en memoria durante la sesión, no los escribe a disco y no registra su contenido. Salen de su equipo hacia el servidor: no se deben subir datos que no puedan compartirse con él.",
        "faq_archivos": "Los archivos que se suben salen de su equipo y llegan al servidor de la aplicación (una instancia de AWS). Allí se procesan en memoria durante la sesión: no se escriben a disco ni se registra su contenido, y se descartan al cerrar la sesión. No se deben subir datos que no puedan compartirse con ese servidor.",
        "borrador": "borrador: verificar",
    },
}


def entorno_pagina() -> str:
    """``local`` o ``publicado``: el valor de ``MODO_DESPLIEGUE`` salvo que la variable de entorno ``EP3_ENTORNO`` diga otra cosa (``publicado`` o ``servidor``, sin distinguir mayúsculas; ``local`` u otro valor da ``local``).
    Es el único lugar que decide el modo; se lee en cada llamada."""
    valor = os.environ.get("EP3_ENTORNO")
    if valor is None:
        return MODO_DESPLIEGUE if MODO_DESPLIEGUE in MODOS_DESPLIEGUE else "local"
    return "publicado" if valor.strip().lower() in ("publicado", "servidor") else "local"


def texto_entorno(clave: str) -> str:
    """Texto de ``TEXTOS_ENTORNO`` para el modo de despliegue actual."""
    return TEXTOS_ENTORNO[entorno_pagina()][clave]


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
        return (f"Con auditoría previa (en muestra): unas **{F.de_cada_100(r['cobertura_dos'])}** cajas sin pareja. Solo cola: unas **{F.de_cada_100(r['cobertura_uno'])}** "
                f"cajas sin pareja, en los {r['n_segmentos']} segmentos.")
    return (f"En el segmento {r['segmento']}: con auditoría previa (en muestra) se encontraron {F.entero(r['hallados_dos'])} de {F.entero(r['positivos_total'])} cajas sin pareja "
            f"({F.porcentaje(r['cobertura_dos'])}). Solo cola, {F.entero(r['hallados_uno'])} ({F.porcentaje(r['cobertura_uno'])}). Un solo segmento: no hay intervalo de confianza por segmentos.")


def texto_esfuerzo_cola(r: dict[str, Any]) -> str:
    """Segunda línea: cajas a revisar y horas del flujo elegido."""
    nombre = "Auditoría + cola" if r["flujo"] == "dos" else "Solo cola"
    return (f"{nombre}: {F.entero(r['cajas_a_revisar'])} cajas a revisar ({F.porcentaje(r['presupuesto'], 0)} de {F.entero(r['cajas_cola_total'])} en la cola). "
            f"{F.horas(r['horas'], 1)} con {F.entero(r['segundos'])} s por caja (supuesto).")


COLUMNA_FOTOGRAMAS = "Fotogramas"
NOTA_FOTOGRAMAS = ("Fotogramas del mismo objeto que hay en la cola: un mismo objeto (por ejemplo, un peatón que camina) aparece en varios fotogramas y cada fotograma es una caja distinta de la cola. "
                   "Cuenta cuántas filas de la cola son del mismo objeto: revisar una ayuda a revisar las otras. No cambia el orden de la cola.")


def tabla_cola(top: pd.DataFrame, cola_total: int, rangos: dict[int, tuple[float, float]], max_filas: int = 500) -> pd.DataFrame:
    """Tabla de la cola lista para mostrar (nombres legibles, formato es-CL).

    Orden de columnas (F21-P1b), pensado para que a 1366 px se vea lo que decide sin desplazar: posición, **probabilidad calibrada de no tener pareja**, puntos del sensor superior, clase,
    fotogramas del mismo objeto, cámara, tipo de caso, distancia y, al final, el segmento y los identificadores. No cambia el orden de las filas ni ninguna cifra. ``cola_total`` se conserva
    por compatibilidad.
    """
    t = top.head(max_filas).reset_index(drop=True)
    n = len(t)
    out = pd.DataFrame({"Posición": np.arange(1, n + 1)})
    out[COLUMNA_PROBABILIDAD] = t["prob_cal"].map(lambda v: F.porcentaje(v, 1)).to_numpy() if "prob_cal" in t.columns else "—"
    out["Puntos sensor sup."] = t["num_top_lidar_points"].map(F.entero).to_numpy() if "num_top_lidar_points" in t.columns else "—"
    if "es_ciclista" in t.columns:
        out["Clase"] = np.where(t["es_ciclista"].to_numpy() == 1, CLASE_ADVERTENCIA, CLASE_NORMAL)
    if "key.laser_object_id" in top.columns and "seg" in top.columns:
        # cuántas filas (fotogramas) de la cola tiene el mismo objeto; se cuenta sobre TODA la cola elegida, no solo sobre las filas que se muestran
        cuenta = top.groupby(["seg", "key.laser_object_id"])["seg"].transform("size").to_numpy()[:max_filas]
        out[COLUMNA_FOTOGRAMAS] = cuenta
    out["Cámara"] = camara_de_azimut(t["az_signed"], rangos).to_numpy() if "az_signed" in t.columns else "—"
    out["Tipo de caso"] = t["tipo_caso"].to_numpy() if "tipo_caso" in t.columns else "—"
    out["Distancia"] = t["distancia_m"].map(lambda v: f"{F.decimal(v, 1)} m").to_numpy() if "distancia_m" in t.columns else "—"
    out["Segmento"] = t["seg"].to_numpy()
    for col, nombre in (("key.frame_timestamp_micros", "Marca de tiempo"), ("key.laser_object_id", "Identificador de objeto")):
        if col in t.columns:
            out[nombre] = t[col].to_numpy()
    return out


COLUMNA_PROBABILIDAD = "Prob. sin pareja"
NOTA_AGRUPADO = "Vista agrupada: una fila por objeto. Es solo una vista; el conteo de cajas a revisar no cambia."


def tabla_por_objeto(top: pd.DataFrame, rangos: dict[int, tuple[float, float]] | None = None, max_filas: int = 500) -> pd.DataFrame:
    """Vista «Agrupar por objeto» (F20-P4f): una fila por objeto (segmento + identificador) con su mejor posición, su máxima probabilidad y los fotogramas en la cola.

    Solo reagrupa la cola que se le pasa: no cambia el orden ni el número de cajas a revisar.
    """
    if top.empty or "key.laser_object_id" not in top.columns:
        return pd.DataFrame(columns=["Objeto", "Mejor posición", COLUMNA_PROBABILIDAD + " máxima", COLUMNA_FOTOGRAMAS])
    t = top.reset_index(drop=True).assign(_pos=lambda d: np.arange(1, len(d) + 1))
    agg = {"pos": ("_pos", "min"), "n": ("_pos", "size")}
    for nombre, col, fn in (("prob", "prob_cal", "max"), ("ciclista", "es_ciclista", "max"), ("tipo", "tipo_caso", "first"), ("az", "az_signed", "first")):
        if col in t.columns:
            agg[nombre] = (col, fn)
    g = t.groupby(["seg", "key.laser_object_id"], sort=False).agg(**agg).reset_index().sort_values("pos").head(max_filas)
    out = pd.DataFrame({"Mejor posición": g["pos"].to_numpy()})
    out[COLUMNA_PROBABILIDAD + " máxima"] = g["prob"].map(lambda v: F.porcentaje(v, 1)).to_numpy() if "prob" in g.columns else "—"
    if "ciclista" in g.columns:
        out["Clase"] = np.where(g["ciclista"].to_numpy() == 1, CLASE_ADVERTENCIA, CLASE_NORMAL)
    out[COLUMNA_FOTOGRAMAS] = g["n"].to_numpy()
    if "az" in g.columns:
        out["Cámara"] = camara_de_azimut(g["az"].reset_index(drop=True), rangos or {}).to_numpy()
    out["Tipo de caso"] = g["tipo"].to_numpy() if "tipo" in g.columns else "—"
    out["Objeto"] = g["key.laser_object_id"].to_numpy()
    out["Segmento"] = g["seg"].to_numpy()
    return out


def empate_inicial(top: pd.DataFrame) -> dict[str, Any] | None:
    """Empate al inicio de la cola (F21-P1a): cuántas de las primeras cajas comparten el mismo puntaje de la regla. ``None`` si no hay empate (menos de 2).

    La cola está ordenada por puntaje descendente, así que los empates del principio son un bloque contiguo. Devuelve el número de cajas, los puntos del sensor superior (si son
    los mismos) y el rango de la probabilidad calibrada (cada partición de la validación cruzada calibró por separado, por eso puede variar un poco entre las cajas empatadas).
    """
    if top.empty or "score" not in top.columns:
        return None
    s = top["score"].to_numpy()
    n = int((s == s[0]).sum())
    if n < 2:
        return None
    g = top.iloc[:n]
    pts = g["num_top_lidar_points"].unique() if "num_top_lidar_points" in g.columns else []
    prob = g["prob_cal"] if "prob_cal" in g.columns else None
    return {"n": n, "toda_la_cola": n == len(top), "puntos": float(pts[0]) if len(pts) == 1 else None, "prob_primera": float(prob.iloc[0]) if prob is not None else None,
            "prob_min": float(prob.min()) if prob is not None else None, "prob_max": float(prob.max()) if prob is not None else None}


def nota_empate(top: pd.DataFrame) -> str | None:
    """Nota sobre la tabla de la cola: «Las primeras N cajas empatan (0 puntos del sensor superior, 87,8 %); el orden entre ellas no es informativo». Se calcula de la cola; ``None`` si no hay empate."""
    e = empate_inicial(top)
    if e is None:
        return None
    partes = []
    if e["puntos"] is not None:
        partes.append(f"{F.entero(e['puntos'])} puntos del sensor superior")
    if e["prob_min"] is not None:
        a, b, p0 = F.porcentaje(e["prob_min"], 1), F.porcentaje(e["prob_max"], 1), F.porcentaje(e["prob_primera"], 1)
        partes.append(a if a == b else f"{p0} en la primera y de {a} a {b} en el grupo")   # la tabla muestra la de cada caja; el rango dice cuánto varía dentro del empate
    sujeto = f"Las {F.entero(e['n'])} cajas de la cola empatan" if e["toda_la_cola"] else f"Las primeras {F.entero(e['n'])} cajas empatan"
    return f"{sujeto} ({'; '.join(partes)}); el orden entre ellas no es informativo." if partes else f"{sujeto}; el orden entre ellas no es informativo."


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


# ------------------------------------------------------------------------------------------------------------ F29: lógica del Resumen para uso diario
def segmentos_sin_revisar(D: dict[str, Any]) -> int:
    """Segmentos «sin revisar» del primer indicador. Mientras no exista un flujo en vivo es el total cargado; esta es la ÚNICA función que decide qué es «sin revisar» (cambiarla aquí cuando llegue ese flujo)."""
    return int(D["cajas"]["seg"].nunique())


def cambio_respecto_de_ayer(D: dict[str, Any]) -> float | None:
    """Cambio del % de cajas sin pareja respecto del corte anterior; ``None`` mientras no exista un corte anterior (hoy los datos son un solo corte: no se inventa la cifra)."""
    return None


def indicadores_resumen(D: dict[str, Any], r: dict[str, Any], cajas_en_cola: int) -> list[dict[str, str]]:
    """Los cuatro indicadores del Resumen (``r`` es la salida de ``inicio_resumen``; ``cajas_en_cola`` sale de ``cola_prioritaria``). Todas las cifras ya existían: solo cambian de lugar.

    El cambio respecto de ayer se agrega a la nota del último solo si ``cambio_respecto_de_ayer`` devuelve un valor (hoy no hay corte anterior y no se muestra nada).
    """
    k, n_seg = int(r["celdas_marcadas"]), int(r["segmentos_con_hueco"])
    if k == 0:
        nota_alerta = "ninguna requiere auditoría"
    else:
        nota_alerta = f"en {F.entero(n_seg)} {'segmento' if n_seg == 1 else 'segmentos'}, {'requiere' if k == 1 else 'requieren'} auditoría"
    cambio = cambio_respecto_de_ayer(D)
    nota_prev = "sin par en ninguna cámara" if cambio is None else f"{'+' if cambio >= 0 else '−'}{F.decimal(abs(cambio) * 100, 1)} puntos respecto de ayer"
    return [
        {"clave": "segmentos", "etiqueta": "Segmentos nuevos", "valor": F.entero(segmentos_sin_revisar(D)), "nota": "cargados, sin revisar", "tono": ""},
        {"clave": "camaras", "etiqueta": "Cámaras con alerta", "valor": F.entero(k), "nota": nota_alerta, "tono": "hueco" if k > 0 else ""},
        {"clave": "cola", "etiqueta": "Cajas en la cola", "valor": F.entero(cajas_en_cola), "nota": "peatones y ciclistas por revisar", "tono": ""},
        {"clave": "prevalencia", "etiqueta": "Cajas sin pareja", "valor": F.porcentaje(r["prevalencia"]), "nota": nota_prev, "tono": ""},
    ]


def preparar_cola(top: pd.DataFrame, cajas: pd.DataFrame, rangos: dict[int, tuple[float, float]]) -> pd.DataFrame:
    """La cola de una selección (``top``, tal como la elige ``cola_segmento``) en un orden DETERMINISTA y con las columnas que muestran el Resumen y la Cola.

    Orden: probabilidad calibrada descendente, luego segmento, luego identificador del objeto y luego fotograma. Solo reordena las cajas ya elegidas por la regla (no cambia cuáles ni cuántas: el conjunto y
    los positivos son los mismos para cualquier presupuesto y flujo). ``caja`` es el final del identificador del objeto y su número de fotograma dentro del segmento (única con el segmento, así que no
    hay filas idénticas); ``camara`` y ``clase`` son el texto que se muestra.
    """
    t = top.sort_values(["prob_cal", "seg", "key.laser_object_id", "key.frame_timestamp_micros"], ascending=[False, True, True, True], kind="stable").reset_index(drop=True)
    orden = cajas.groupby(["seg", "key.laser_object_id"])["key.frame_timestamp_micros"].rank(method="dense").astype(int)
    num = dict(zip(zip(cajas["seg"], cajas["key.laser_object_id"], cajas["key.frame_timestamp_micros"]), orden.to_numpy()))
    t["fotograma"] = [num[k] for k in zip(t["seg"], t["key.laser_object_id"], t["key.frame_timestamp_micros"])]
    t["caja"] = [f"{str(o)[-4:]}-{int(k):02d}" for o, k in zip(t["key.laser_object_id"], t["fotograma"])]
    t["camara"] = camara_de_azimut(t["az_signed"], rangos).to_numpy() if "az_signed" in t.columns else "—"
    t["clase"] = np.where(t["es_ciclista"].to_numpy() == 1, "Ciclista", "Peatón") if "es_ciclista" in t.columns else "Peatón"
    return t


def cola_prioritaria(cajas: pd.DataFrame, rangos: dict[int, tuple[float, float]], presupuesto: float = PRESUPUESTO_VISTA_RESUMEN) -> tuple[pd.DataFrame, int]:
    """La cola prioritaria del Resumen: las mismas cajas que elige ``cola_segmento`` (flujo en dos pasos, todos los segmentos, ``presupuesto`` de la cola) con el orden de ``preparar_cola``.

    Devuelve la tabla y el total de cajas de la cola (el de «Cajas en la cola»).
    """
    top, info = cola_segmento(cajas, "Todos", presupuesto, "dos")
    return preparar_cola(top, cajas, rangos), int(info["cajas_cola_total"])


def tarjetas_cola(r: dict[str, Any], segundos: float) -> list[dict[str, str]]:
    """Las tres tarjetas de la Cola (F32): cajas a revisar, cajas sin pareja que se encuentran (con «en muestra» y la cifra del otro flujo debajo) y tiempo estimado.

    ``r`` es la salida de ``resumen_cola`` para todos los segmentos. Son las mismas cifras que decían el párrafo largo y la línea de esfuerzo: salen de las mismas claves.
    """
    dos = r["flujo"] == "dos"
    propio, otro = (r["cobertura_dos"], r["cobertura_uno"]) if dos else (r["cobertura_uno"], r["cobertura_dos"])
    nota = f"solo cola: {F.de_cada_100(otro)}" if dos else f"con auditoría previa: {F.de_cada_100(otro)}"
    return [
        {"clave": "revisar", "etiqueta": "Cajas a revisar", "valor": F.entero(r["cajas_a_revisar"]), "nota": f"{F.porcentaje(r['presupuesto'], 0)} de las {F.entero(r['cajas_cola_total'])} de la cola"},
        {"clave": "encuentran", "etiqueta": "Cajas sin pareja que se encuentran", "en_muestra": True, "valor": F.entero(round(100 * propio)), "sufijo": "de cada 100", "nota": nota},
        {"clave": "tiempo", "etiqueta": "Tiempo estimado", "valor": F.horas(r["horas"], 1), "nota": f"{F.entero(segundos)} s por caja (supuesto)"},
    ]


def aviso_empate(top: pd.DataFrame) -> str | None:
    """Aviso sobre la tabla de la Cola: cuántas de las primeras cajas empatan en la prioridad máxima, con sus puntos y el rango real de probabilidad, y cómo se ordenan entre sí. ``None`` si no hay empate.

    ``top`` debe estar en el orden de la regla (el de ``cola_segmento``), que es el que define el empate.
    """
    e = empate_inicial(top)
    if e is None:
        return None
    detalle = []
    if e["puntos"] is not None:
        detalle.append(f"{F.entero(e['puntos'])} puntos del sensor superior")
    if e["prob_min"] is not None:
        a, b = F.porcentaje(e["prob_min"], 1), F.porcentaje(e["prob_max"], 1)
        detalle.append(a if a == b else f"entre {a} y {b}")
    sujeto = f"Las {F.entero(e['n'])} cajas de la cola empatan" if e["toda_la_cola"] else f"Las primeras {F.entero(e['n'])} cajas empatan"
    cuerpo = f" ({'; '.join(detalle)})" if detalle else ""
    return f"{sujeto} en la prioridad máxima{cuerpo}. Su orden entre sí no es informativo: se ordenan por probabilidad, segmento y caja."


def pagina_cola(total: int, pagina: int, por_pagina: int = FILAS_PAGINA_COLA) -> dict[str, int]:
    """Datos de la página ``pagina`` (desde 1) de una lista de ``total`` filas: la página corregida a [1, n], el rango «Mostrando X a Y de N» (base 1) y los índices de corte (base 0)."""
    n_paginas = max(1, -(-total // por_pagina))
    pagina = min(max(int(pagina), 1), n_paginas)
    ini = (pagina - 1) * por_pagina
    fin = min(ini + por_pagina, total)
    return {"pagina": pagina, "paginas": n_paginas, "desde": ini + 1 if total else 0, "hasta": fin, "ini": ini, "fin": fin, "total": total}


def clase_con_etiqueta(clase: str) -> str:
    """Texto de la columna «Clase» de la tabla: en ciclistas lleva «Regla poco confiable» en la propia fila."""
    return f"{clase} · {ETIQUETA_CICLISTA}" if clase == "Ciclista" else clase


def filtrar_cola_resumen(t: pd.DataFrame, clase: str = "Todas", camara: str = "Todas", segmento: str = "Todos") -> pd.DataFrame:
    """Filtra la cola prioritaria del Resumen por clase, cámara y segmento (cada uno acepta «Todas»/«Todos»). No cambia el orden."""
    out = t
    if clase != "Todas":
        out = out[out["clase"] == clase]
    if camara != "Todas":
        out = out[out["camara"] == camara]
    if segmento != "Todos":
        out = out[out["seg"] == segmento]
    return out


def segmentos_prioritarios(t: pd.DataFrame, n: int = SEGMENTOS_PRIORITARIOS_RESUMEN) -> list[tuple[str, int]]:
    """Los ``n`` segmentos con más cajas en la cola prioritaria (cuántas cajas de la cola tiene cada uno), de más a menos; a igual número, por segmento."""
    c = t.groupby("seg").size().reset_index(name="cajas").sort_values(["cajas", "seg"], ascending=[False, True], kind="stable").head(n)
    return [(str(s), int(k)) for s, k in zip(c["seg"], c["cajas"])]


def celdas_marcadas_lista(lista_a: pd.DataFrame) -> list[dict[str, Any]]:
    """Las celdas marcadas (Lista A) como filas de la lista de alertas del Resumen: más cajas afectadas primero y, a igual número, por segmento (orden determinista).

    Cada fila trae el segmento (completo y sus 6 últimos dígitos), el número y el nombre de la cámara, el estado «Hueco» y las cajas afectadas. Solo reordena y rotula la Lista A.
    """
    filas = []
    for r in lista_a.itertuples(index=False):
        cam = str(r.camara)
        num = int(cam[0]) if cam[:1].isdigit() else 0
        nombre = cam[cam.index("(") + 1:cam.rindex(")")] if "(" in cam and ")" in cam else cam
        v = getattr(r, "cajas_afectadas_poblacion_principal", 0)
        afectadas = int(v) if pd.notna(v) else 0
        sin = getattr(r, "positivos_afectados", 0)
        tasa, normal = getattr(r, "tasa", float("nan")), getattr(r, "mediana_camara", float("nan"))
        lugar = _UBICACION.get(getattr(r, "ubicacion", ""), getattr(r, "ubicacion", "")) or ""
        momento = _MOMENTO.get(getattr(r, "momento", ""), getattr(r, "momento", "")) or ""
        filas.append({"segmento": str(r.segmento), "seg_corto": str(r.segmento)[-6:], "camara": cam, "camara_num": num, "camara_nombre": nombre, "estado": ESTADO_HUECO, "cajas_afectadas": afectadas,
                      "sin_pareja": int(sin) if pd.notna(sin) else 0, "tasa": float(tasa) if pd.notna(tasa) else float("nan"), "normal": float(normal) if pd.notna(normal) else float("nan"),
                      "contexto": ", ".join(x for x in (lugar, str(momento).lower()) if x)})
    return sorted(filas, key=lambda f: (-f["cajas_afectadas"], f["segmento"], f["camara_num"]))


def valores_para_explicar(fila: Any) -> dict[str, Any]:
    """Los valores de una caja de la cola que «Explica una caja» recibe al pulsar «Abrir»: puntos del LiDAR y del sensor superior, distancia y clase."""
    return {"pts": int(fila["num_lidar_points"]), "top": int(fila["num_top_lidar_points"]), "dist": float(fila["distancia_m"]), "clase": "Ciclista" if fila["clase"] == "Ciclista" else "Peatón"}


def hora_de_los_datos(carpeta: Path) -> str | None:
    """Fecha y hora de la última modificación de los archivos de la página (para «Última actualización de los datos»); ``None`` si no se puede leer."""
    from datetime import datetime

    try:
        m = max((Path(carpeta) / a).stat().st_mtime for a in ARCHIVOS)
    except (OSError, ValueError):
        return None
    return datetime.fromtimestamp(m).strftime("%d-%m-%Y %H:%M")


# ------------------------------------------------------------------------------------------------------------ F31: lógica de la Auditoría de cámaras
def cargar_fraccion_hueco(carpeta: Path) -> float:
    """Fracción de la tasa normal de una cámara bajo la cual una celda es hueco (``frac`` del detector congelado; solo lectura; 0,25 si no está el archivo)."""
    ruta = Path(carpeta) / "detector_params_v3.json"
    if not ruta.exists():
        return 0.25
    return float(_json.loads(ruta.read_text(encoding="utf-8")).get("frac", 0.25))


def resumen_auditoria(m: pd.DataFrame, lista_a: pd.DataFrame) -> dict[str, Any]:
    """Cifras de la franja de la Auditoría: celdas (segmento × cámara) y cuántas están marcadas, cajas afectadas (población principal, dentro del rango de la cámara) y cuántas no tienen pareja.

    Solo suma lo que ya trae la Lista A y cuenta las filas de ``matriz_calor``: no calcula nada nuevo. Con una Lista A sin las columnas de cajas, ambas sumas son 0.
    """
    afectadas = int(lista_a["cajas_afectadas_poblacion_principal"].sum()) if "cajas_afectadas_poblacion_principal" in lista_a.columns else 0
    sin = int(lista_a["positivos_afectados"].sum()) if "positivos_afectados" in lista_a.columns else 0
    return {"celdas_total": int(len(m)), "celdas_marcadas": int(len(lista_a)), "cajas_afectadas": afectadas, "sin_pareja": sin, "pct_sin_pareja": (sin / afectadas) if afectadas else float("nan"),
            "segmentos": int(m["seg"].nunique()) if len(m) else 0}


def orden_gravedad(m: pd.DataFrame) -> list[str]:
    """Segmentos del mapa de lo más grave a lo menos: primero los que tienen más celdas marcadas, luego los de menor tasa de pares entre sus celdas con datos suficientes, luego por identificador.

    Es un orden determinista y barato (una pasada): sirve con cientos de segmentos.
    """
    if m.empty:
        return []
    g = m.groupby("seg").apply(lambda d: pd.Series({"marcadas": int(d["hueco"].sum()), "tasa_min": float(d.loc[~d["sin_datos"], "tasa"].min()) if (~d["sin_datos"]).any() else 1.0}), include_groups=False)
    g = g.reset_index().sort_values(["marcadas", "tasa_min", "seg"], ascending=[False, True, True], kind="stable")
    return [str(s) for s in g["seg"]]


def siguiente_filas_mapa(actual: int, total: int) -> int:
    """Cuántas filas del mapa se ven después del clic en el botón: con ``total`` hasta ``UMBRAL_TODOS_MAPA`` se pasa de las primeras a todas; con más, de a ``PASO_MAPA``; al llegar al final, se vuelve al inicio."""
    if actual >= total:
        return min(FILAS_MAPA_INICIO, total)
    return total if total <= UMBRAL_TODOS_MAPA else min(total, actual + PASO_MAPA)


def rotulo_boton_mapa(actual: int, total: int) -> str:
    """Texto del botón del mapa: «Ver los N segmentos», «Mostrar 50 más (X de N)» o «Ver solo las primeras filas»."""
    if actual >= total:
        return "Ver solo las primeras filas"
    siguiente = siguiente_filas_mapa(actual, total)
    return f"Ver los {F.entero(total)} segmentos" if siguiente >= total else f"Mostrar {PASO_MAPA} más ({F.entero(actual)} de {F.entero(total)})"


def titular_auditoria(k: int) -> str:
    """Texto del titular pequeño de la Auditoría, con «N posibles huecos de cámara» (singular y plural) o el de «ninguna»."""
    if k == 0:
        return AUD_TITULAR_CERO
    return AUD_TITULAR.format(huecos=f"{F.entero(k)} {'posible hueco' if k == 1 else 'posibles huecos'} de cámara")


def tabla_celdas_auditoria(celdas: list[dict[str, Any]]) -> pd.DataFrame:
    """La única tabla de celdas marcadas (segmento, cámara, cajas afectadas, sin pareja, cajas con par 2D frente a lo normal y contexto), en el orden de ``celdas_marcadas_lista``."""
    def par(c: dict[str, Any]) -> str:
        if c["tasa"] != c["tasa"]:
            return "—"
        return f"{F.porcentaje(c['tasa'], 0)} (normal {F.porcentaje(c['normal'], 0)})" if c["normal"] == c["normal"] else F.porcentaje(c["tasa"], 0)

    return pd.DataFrame({"Segmento": ["…" + c["seg_corto"] for c in celdas], "Cámara": [f"{c['camara_num']} · {c['camara_nombre']}" for c in celdas],
                         "Cajas afectadas": [c["cajas_afectadas"] for c in celdas], "Sin pareja": [c["sin_pareja"] for c in celdas],
                         "Cajas con par 2D (normal)": [par(c) for c in celdas], "Contexto": [c["contexto"] for c in celdas]})


def texto_umbral_hueco(lista_a: pd.DataFrame, frac: float, min_cajas: int) -> str:
    """Frase del desplegable «¿Qué es un hueco?» con el umbral real: la fracción de lo normal, el mínimo de cajas y el umbral de cada celda marcada (redondeado a 0 decimales)."""
    base = f"El umbral es el {F.porcentaje(frac, 0)} de lo normal de esa cámara, con al menos {F.entero(min_cajas)} cajas en el rango."
    if "umbral" in lista_a.columns and len(lista_a):
        us = sorted({round(float(u) * 100) for u in lista_a["umbral"]})
        base += f" En {'la celda marcada' if len(lista_a) == 1 else 'las celdas marcadas'} equivale a {' y '.join(str(u) + ' %' for u in us) if us else ''} de pares 2D.".replace("  ", " ")
    return base


# ------------------------------------------------------------------------------------------------------------ F33: lógica de «Explica una caja»
def referencia_cola(cajas: pd.DataFrame, flujo: str = "dos") -> np.ndarray:
    """Puntajes de la cola contra la que se compara una caja: la del flujo elegido (dos pasos: sin las cajas de celdas marcadas, que se auditan aparte; un paso: todas)."""
    base = cajas if flujo == "uno" else cajas[~cajas["en_hueco"]]
    return base["score"].to_numpy(dtype=float)


def empatadas_arriba(ref: np.ndarray) -> int:
    """Cuántas cajas de la cola tienen el puntaje máximo (empatan en la prioridad máxima)."""
    return int((ref == ref.max()).sum()) if len(ref) else 0


def umbral_presupuesto(ref: np.ndarray, presupuesto: float) -> dict[str, float]:
    """Puntaje y puntos del sensor superior del último lugar que entra con ``presupuesto`` (fracción de la cola): se calcula de la cola real con la misma regla que ``cola_segmento`` (se revisan las
    ``ceil(presupuesto × N)`` primeras). «Entra» una caja con puntaje mayor o igual; con los mismos puntos que el umbral puede quedar dentro o fuera según el desempate de la cola."""
    n = int(np.ceil(presupuesto * len(ref)))
    n = min(max(n, 1), len(ref))
    score = float(np.sort(ref)[::-1][n - 1])
    return {"cajas_a_revisar": n, "score": score, "puntos": int(round(-score))}


def veredicto_caja(score: float, ref: np.ndarray, presupuesto: float) -> dict[str, Any]:
    """Qué pasaría con una caja de puntaje ``score``: su lugar en la cola (fracción de cajas que quedan antes: 0 = primera, 1 = última, el mismo de ``percentil_en_cola``), si entra con el
    ``presupuesto`` actual, el umbral de puntos y si cae entre las cajas empatadas en la prioridad máxima."""
    u = umbral_presupuesto(ref, presupuesto)
    pos = float((ref > score).mean())
    empatada = bool(len(ref) and score == ref.max())
    return {"entra": bool(score >= u["score"]), "posicion": pos, "umbral_puntos": int(u["puntos"]), "cajas_a_revisar": int(u["cajas_a_revisar"]), "empatada": empatada, "empatadas": empatadas_arriba(ref),
            "puntos_empate": int(round(-ref.max())) if len(ref) else 0, "fraccion_empate": empatadas_arriba(ref) / max(len(ref), 1)}


def textos_veredicto(v: dict[str, Any], presupuesto: float) -> tuple[str, str]:
    """Texto del veredicto y su línea de detalle (con el presupuesto y el lugar formateados es-CL)."""
    pres = F.porcentaje(presupuesto, 0)
    if v["entra"]:
        return EXP_VEREDICTO_SI.format(presupuesto=pres), EXP_DETALLE_SI.format(presupuesto=pres)
    return EXP_VEREDICTO_NO.format(presupuesto=pres), EXP_DETALLE_NO.format(posicion=F.porcentaje(v["posicion"], 0))


def texto_lugar(v: dict[str, Any]) -> tuple[str, str]:
    """Valor y frase del «Lugar en la cola»: con la prioridad máxima empatada no se inventa un lugar exacto, se dice entre cuántas cajas está; si no, el porcentaje y cuántas quedan antes."""
    if v["empatada"]:
        return f"0 a {F.porcentaje(v['fraccion_empate'], 0)}", EXP_LUGAR_EMPATE.format(n=F.entero(v["empatadas"]), puntos=F.entero(v["puntos_empate"]))
    return F.porcentaje(v["posicion"], 0), EXP_LUGAR_TEXTO.format(posicion=F.porcentaje(v["posicion"], 0))


def opciones_puntos(extra: tuple[float, ...] = ()) -> list[int]:
    """Valores del control «Puntos del sensor superior»: una escala comprimida fina (cada paso multiplica los puntos) que incluye la de referencia, los umbrales y los valores de los ejemplos."""
    base = set(ESCALA_PUNTOS) | {int(round(x)) for x in np.geomspace(1, 2000, 60)} | {int(round(x)) for x in extra} | {e[k] for e in EJEMPLOS_CAJA.values() for k in ("pts", "top")}
    return sorted(base)


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


ESCALA_PUNTOS = [0, 1, 2, 5, 10, 11, 20, 32, 50, 60, 100, 200, 500, 1000, 2000]        # escala no lineal con valores de referencia; incluye 11 y 32 (puntos B y A) y 60 (el valor por defecto de siempre)
EJEMPLOS_CAJA = {"Caja cercana y densa": {"pts": 500, "top": 200, "dist": 8.0, "clase": "Peatón"},
                 "Caja lejana con pocos puntos": {"pts": 10, "top": 5, "dist": 70.0, "clase": "Peatón"},
                 "Ciclista lejano": {"pts": 20, "top": 10, "dist": 55.0, "clase": "Ciclista"}}
PASOS_DEL_CALCULO = ["La regla ordena las cajas por menos puntos del sensor superior: cuantos menos puntos, más arriba queda la caja en la cola.",
                     "La calibración convierte ese puntaje en la probabilidad de que la caja no tenga par en ninguna cámara.",
                     "La posición en la cola es la fracción de las cajas que quedan antes que esta."]


def texto_puntaje(puntaje: float) -> str:
    """Puntaje de la regla sin decimales y sin jerga (F21-P2a): «Puntaje: -50 (menos los puntos del sensor superior)»."""
    return f"Puntaje: {F.entero(puntaje)} (menos los puntos del sensor superior)"


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
        out["ie11"] = (f"La regla de puntos tiene AUC {F.decimal(r['AUC'], 3)} en validación cruzada por segmentos; ningún candidato alcanza el AUC mínimo por partición de 0,75 "
                       f"(el mejor llega a {F.decimal(t['AUC_min_fold'].max(), 3)}), por la partición 0.")
    except (KeyError, IndexError):
        out["ie11"] = "Métricas de los candidatos en validación cruzada por segmentos."
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
        out["posthoc"] = f"Con la celda con hueco fuera, el AUC de la regla en la partición 0 pasa de {F.decimal(f0['AUC_A'], 3)} a {F.decimal(f0['AUC_B_celdas_sanas'], 3)} (post hoc, en muestra, no pre-declarado)."
    except (KeyError, IndexError):
        out["posthoc"] = "Todo lo de esta pestaña es post hoc, no pre-declarado."
    return out


FLUJO_BRAZO_A = "Solo cola (un paso)"
FLUJO_BRAZO_B = "Solo celdas sanas, sin auditoría"
FLUJO_BRAZO_C = "Auditoría + cola (dos pasos)"


def datos_validacion(ev: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Tablas ya preparadas para el gráfico con que abre cada pestaña de «Validación» (F20-P7). Todo sale de los CSV de ``data/09_app_ep3/evidencia`` (copias de EP3):
    ``ie9`` de f3_defecto_vs_optimizado, ``ie10`` de f4_ensambles_aporta, ``ie11`` de f5_metricas_candidatos, ``ie11_particiones`` de f5_auc_por_fold (solo los candidatos que trae la copia),
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
        out["ie11_particiones"] = pd.DataFrame({"Candidato": pl["candidato"], "Partición": pl["fold"], "AUC": pl["AUC_A"]})
        g = t[t["fold"] == "global"]
        if not g.empty:
            out["brazos"] = pd.concat([
                pd.DataFrame({"Candidato": g["candidato"], "Flujo": FLUJO_BRAZO_A, "Fraccion": g["Fraccion80_A"]}),
                pd.DataFrame({"Candidato": g["candidato"], "Flujo": FLUJO_BRAZO_B, "Fraccion": g["Fraccion80_B_celdas_sanas"]}),
                pd.DataFrame({"Candidato": g["candidato"], "Flujo": FLUJO_BRAZO_C, "Fraccion": g["Fraccion80_C"]})], ignore_index=True)
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
    cámara pertenece cada caja, así que ``puntuar_segmento`` lo puntúa sin él; la página le suma después (``puntuar.completar_ejemplo``, F37) las celdas marcadas de desarrollo que ya tiene calculadas.
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
            ciclistas = (f"En ciclistas la regla es poco confiable: encuentra {F.porcentaje(c['recall_A'])} de los casos contra {F.porcentaje(p['recall_A'])} en peatones, "
                         f"con solo {F.entero(c['positivos'])} casos en {F.entero(c['segmentos'])} segmentos. Conviene revisarlos con más cuidado.")
        except (KeyError, IndexError):
            pass
    return [
        ("¿El sistema decide qué cajas están mal?", "No. Solo ordena. Una persona revisa y decide; ninguna caja se descarta sin revisarla."),
        ("¿Qué significa «en muestra»?", "Que el resultado se calculó con 41 segmentos y el detector de huecos se ajustó con esos mismos datos; todavía no hay una prueba con segmentos nuevos. "
         "Por eso las cifras de este flujo son optimistas y no deben leerse como una prueba ciega. La validación con segmentos nuevos está preparada y sellada, y todavía no se ejecutó. "
         "La ganancia del flujo en dos pasos sale de 2 celdas cámara x segmento, una de ellas en el segmento donde se descubrió el hueco."),
        ("¿Qué pasa con los ciclistas?", ciclistas),
        ("¿Se guardan o se envían los archivos?", texto_entorno("faq_archivos")),
        ("¿Cuánto tarda revisar una caja?", f"No se midió: se usa un supuesto de {SUPUESTO_SEGUNDOS} segundos por caja, editable en «{COLA_SUPUESTOS}» de la cola de revisión."),
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
        return ("Este archivo no parece un lidar_box de Waymo v2: faltan las columnas " + ", ".join(f"«{c}»" for c in faltan) +
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
