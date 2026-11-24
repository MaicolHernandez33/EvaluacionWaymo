"""Lógica y textos de «Puntuar datos nuevos» (F35): validación de los archivos con mensajes claros en español, estado de los tres pasos, tarjetas de resumen, las tablas de resultado y el CSV.

Funciones puras (sin Streamlit). Todo el procesamiento es en memoria: ninguna función de este módulo escribe a disco (una prueba lo vigila). La puntuación en sí es ``inferencia.puntuar_segmento``;
aquí solo se preparan los archivos de entrada y se presenta el resultado.
"""
from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.app_logica import CLASE_ADVERTENCIA, CLASE_NORMAL, COLUMNAS_LIDAR_BOX, camara_de_azimut
from waymo_evaluacion.ep3.tablas_estandar import Col, Tabla

MAX_MB = 500
MAX_BYTES = MAX_MB * 1024 * 1024
LLAVES = ("key.segment_context_name", "key.frame_timestamp_micros", "key.laser_object_id")
COLUMNAS_ASOCIACION = ("key.segment_context_name", "key.camera_name", "key.frame_timestamp_micros", "key.laser_object_id")

# ------------------------------------------------------------------------------------------------------------ textos
SUBTITULO = "Un segmento nuevo se puntúa con la solución congelada y se obtienen sus celdas marcadas y su cola de cajas."
PASOS = (("Cargar el segmento", "archivo lidar_box"), ("Revisar celdas marcadas", "huecos de cámara"), ("Revisar la cola", "cajas en orden"))
ARCHIVO_1_ROTULO = "Archivo 1 (obligatorio): lidar_box"
ARCHIVO_2_ROTULO = "Archivo 2 (opcional): camera_to_lidar_box_association"
ARCHIVO_1_AYUDA = f"lidar_box · formato parquet, hasta {MAX_MB} MB"
# Qué pasa sin el archivo 2 (comprobado en ``inferencia.puntuar_segmento``): se puntúan y ordenan todas las cajas igual, pero no se buscan huecos de cámara (no hay celdas marcadas ni cajas apartadas) y no se conoce
# cuáles cajas ya tienen pareja (no hay cifras de cajas sin pareja).
ARCHIVO_2_AYUDA = (f"camera_to_lidar_box_association · formato parquet, hasta {MAX_MB} MB. Sirve para buscar huecos de cámara y conocer cuáles cajas ya tienen pareja; "
                   "sin este archivo se puntúan y ordenan igual todas las cajas, pero no hay celdas marcadas ni cifras de cajas sin pareja.")
PREGUNTA_EJEMPLO = "¿Solo desea ver cómo funciona?"
BOTON_EJEMPLO = "Usar un segmento de desarrollo de ejemplo"
VACIO_TITULO = "Todavía no hay un segmento cargado"
VACIO_TEXTO = "Agregue el archivo 1 (y, si lo tiene, el archivo 2) y pulse «Puntuar segmento»: aquí aparecerán la lista de celdas marcadas y la cola de cajas de ese segmento."
# F39: el puntaje ya no se dispara al subir un archivo: los dos cargadores quedan a la vista, en cualquier orden, y se puntúa con un botón
BOTON_PUNTUAR = "Puntuar segmento"
EXPANDER_ARCHIVOS = "Archivos del segmento"
AYUDA_SIN_ARCHIVO_1 = "Agregue el archivo 1 para poder puntuar."
AYUDA_SOLO_1 = "Todavía no agregó el archivo 2: se puntuará sin buscar huecos de cámara."
AYUDA_AMBOS = "Listo para puntuar con búsqueda de huecos de cámara."
AVISO_CAMBIARON = "Cambiaron los archivos: pulse Puntuar segmento para actualizar el resultado."
PASO_OMITIDO = "omitido: falta el archivo 2"
FORMATO_INTRO = ("Dos archivos en formato parquet, hasta {mb} MB cada uno: lidar_box (obligatorio) y camera_to_lidar_box_association (opcional). Se pueden agregar en cualquier orden y el segmento se puntúa "
                 "al pulsar «Puntuar segmento». Columnas que necesita cada uno:")
BOTON_OTRO = "Cargar otro segmento"
BOTON_DESCARGA = "Descargar resultados (CSV)"
ETIQUETA_EJEMPLO = "ejemplo de desarrollo"
NOTA_PROCESADO = "Procesado en memoria con la solución congelada."
NOTA_EJEMPLO = ("Ejemplo: segmento de desarrollo {segmento}, reconstruido desde las variables derivadas (no son datos crudos de Waymo). Sus celdas marcadas y cajas sin pareja son las ya calculadas para este segmento "
                  "con su archivo de asociación; aquí no se vuelven a calcular.")
NOTA_SIN_ARCHIVO_2 = "Sin el archivo 2 no se buscaron huecos de cámara ni se conoce cuáles cajas tienen pareja; las cajas sí se puntuaron y ordenaron."
TITULO_CELDAS = "Celdas marcadas"
TITULO_COLA = "Cola de cajas de este segmento"
NOTA_COLA = "Se revisa de arriba hacia abajo."
TEXTO_SIN_CELDAS = "No hay celdas marcadas en este segmento."
TEXTO_CELDAS_NO_BUSCADAS = "No se buscaron huecos de cámara: falta el archivo 2."
RESPONDE_CELDAS = "¿Qué cámaras de este segmento tienen un posible hueco?"
RESPONDE_COLA = "¿Qué cajas conviene revisar primero en este segmento?"
POR_PAGINA_COLA = 50
ETIQUETAS_RESUMEN = {"cajas_vru_poblacion_principal": "Cajas de peatones y ciclistas (población principal)", "cajas_en_celdas_con_hueco": "Cajas en celdas marcadas", "cajas_en_lista_B": "Cajas en la cola",
                     "celdas_con_hueco": "Celdas marcadas", "tiene_asociacion": "Archivo de asociación presente", "umbral_A": "Umbral de puntaje A", "umbral_B": "Umbral de puntaje B",
                     "positivos_total": "Cajas sin pareja", "positivos_en_celdas_con_hueco": "Cajas sin pareja en celdas marcadas"}

# Columnas de cada archivo (la fuente es ``inferencia.construir_variables`` y ``agregar_asociacion``; una prueba comprueba que siguen en esas funciones)
COLUMNAS_ARCHIVO_1 = (("key.segment_context_name, key.frame_timestamp_micros, key.laser_object_id", "Segmento, fotograma y objeto de cada caja"), ("type", "Tipo de objeto (peatón o ciclista)"),
                      ("box.center.x, box.center.y, box.center.z", "Centro de la caja 3D"), ("box.size.x, box.size.y, box.size.z, box.heading", "Dimensiones y rumbo de la caja"),
                      ("num_lidar_points_in_box, num_top_lidar_points_in_box", "Puntos del LiDAR y del sensor superior dentro de la caja"),
                      ("speed.x, speed.y (opcionales)", "Velocidad de la caja; si faltan, la velocidad queda sin dato"))
COLUMNAS_ARCHIVO_2 = (("key.segment_context_name, key.frame_timestamp_micros, key.laser_object_id", "Las tres llaves del archivo 1: así se une cada caja con su par"), ("key.camera_name", "Cámara en la que la caja 3D tiene su par 2D"))
NOTA_FORMATO = "Los nombres de columna pueden llevar un prefijo del componente (por ejemplo «[LiDARBoxComponent].»); la página lo reconoce por el final del nombre."


def filas_formato() -> list[list[str]]:
    """Las filas de la tabla «Formato de los archivos de entrada»: archivo, columnas y para qué sirven."""
    return ([["Archivo 1: lidar_box", c, u] for c, u in COLUMNAS_ARCHIVO_1] + [["Archivo 2: camera_to_lidar_box_association", c, u] for c, u in COLUMNAS_ARCHIVO_2])


# ------------------------------------------------------------------------------------------------------------ validación de los archivos
def validar_tamano(nombre: str, tamano: int) -> str | None:
    """Mensaje si el archivo pesa más de 500 MB; ``None`` si cabe."""
    if tamano > MAX_BYTES:
        return f"El archivo «{nombre}» pesa {F.decimal(tamano / 1024 / 1024, 0)} MB y el máximo es {MAX_MB} MB. Use un archivo más pequeño (un segmento a la vez)."
    return None


def leer_parquet(contenido: bytes, nombre: str) -> tuple[pd.DataFrame | None, str | None]:
    """Lee un parquet en memoria. Devuelve (tabla, mensaje de error): un archivo que no es parquet, está dañado o está vacío da un mensaje claro y nunca un traceback."""
    if not contenido:
        return None, f"El archivo «{nombre}» está vacío (0 bytes)."
    try:
        df = pd.read_parquet(io.BytesIO(contenido))
    except Exception:  # noqa: BLE001 - cualquier fallo de lectura es «no es un parquet válido»
        return None, f"El archivo «{nombre}» no es un parquet válido o está dañado. Se espera un archivo en formato parquet."
    if len(df) == 0:
        return None, f"El archivo «{nombre}» no tiene filas: está vacío."
    return df, None


def columnas_faltantes_lidar(df: pd.DataFrame) -> list[str]:
    return [c for c in COLUMNAS_LIDAR_BOX if not any(col.endswith(c) for col in df.columns)]


def _ids(segmentos: set[str], tope: int = 3) -> str:
    """Los identificadores completos de segmento (``key.segment_context_name``), ordenados; con más de ``tope`` dice cuántos faltan."""
    lista = sorted(segmentos)
    return ", ".join(lista[:tope]) + (f" y {F.entero(len(lista) - tope)} más" if len(lista) > tope else "")


def firma_archivo(nombre: str, contenido: bytes) -> tuple[str, int, str]:
    """Firma de un archivo subido (nombre, tamaño y sha256): con ella la página sabe si el resultado en pantalla corresponde a los archivos actuales. No guarda el contenido."""
    return (nombre, len(contenido), hashlib.sha256(contenido).hexdigest())


def ayuda_flujo(hay_archivo_1: bool, hay_archivo_2: bool) -> str:
    """La línea de ayuda bajo el botón «Puntuar segmento», según qué archivos hay."""
    if not hay_archivo_1:
        return AYUDA_SIN_ARCHIVO_1
    return AYUDA_AMBOS if hay_archivo_2 else AYUDA_SOLO_1


def validar_correspondencia(lidar: pd.DataFrame, asoc: pd.DataFrame) -> str | None:
    """Mensaje si el archivo 2 no corresponde al archivo 1: ninguno de sus segmentos o ninguna de sus cajas aparece en el archivo 1. ``None`` si se corresponden."""
    col1 = next((c for c in lidar.columns if c.endswith(LLAVES[0])), None)
    if col1 is None or LLAVES[0] not in asoc.columns:
        return None
    s1, s2 = set(lidar[col1].astype(str)), set(asoc[LLAVES[0]].astype(str))
    if not (s1 & s2):
        return ("El archivo 2 no corresponde al archivo 1: ninguno de sus segmentos aparece en el archivo 1.\n"
                f"Archivo 1: {_ids(s1)}\nArchivo 2: {_ids(s2)}\nRevise que ambos sean del mismo segmento.")
    k1 = {c: next((x for x in lidar.columns if x.endswith(c)), None) for c in LLAVES}
    if None in k1.values() or any(c not in asoc.columns for c in LLAVES):
        return None
    claves1 = pd.MultiIndex.from_frame(lidar[[k1[c] for c in LLAVES]].astype({k1[LLAVES[0]]: str}).set_axis(LLAVES, axis=1))
    claves2 = pd.MultiIndex.from_frame(asoc[list(LLAVES)].astype({LLAVES[0]: str}))
    if not claves2.isin(claves1).any():
        return "El archivo 2 no corresponde al archivo 1: comparten segmento, pero ninguna caja del archivo 2 está en el archivo 1. Revise que ambos sean del mismo segmento."
    return None


# ------------------------------------------------------------------------------------------------------------ pasos y tarjetas
def estado_pasos(hay_resultado: bool, con_huecos: bool = True) -> list[tuple[str, str, str, str]]:
    """Los tres pasos con su estado: (número, título, detalle, ``activo``/``hecho``/``omitido``/``pendiente``). Sin segmento, el 1 está activo; con segmento, el 1 está hecho, el 2 está hecho si se buscaron
    huecos de cámara (había archivo 2) y **omitido** si no, y el 3 activo."""
    estados = ("hecho", "hecho" if con_huecos else "omitido", "activo") if hay_resultado else ("activo", "pendiente", "pendiente")
    return [(str(i + 1), t, d, e) for i, ((t, d), e) in enumerate(zip(PASOS, estados))]


@dataclass
class Vista:
    """Lo que la página guarda en memoria de un segmento puntuado (no guarda los archivos de entrada)."""

    origen: str                         # «archivo» o «ejemplo»
    segmento: str                       # identificador del segmento (el primero, si el archivo trae varios)
    n_segmentos: int
    lista_A: pd.DataFrame
    cola: pd.DataFrame                  # Lista B con las columnas de presentación (caja, cámara, clase)
    lista_B: pd.DataFrame               # tal como la devuelve ``puntuar_segmento`` (el CSV conserva todas sus columnas)
    resumen: dict[str, Any]
    advertencias: list[str]
    n_cajas: int
    n_celdas: int                       # celdas (segmento × cámara) evaluadas; 0 si no se buscaron huecos
    tiene_asociacion: bool
    nombres_archivos: tuple[str, str | None] = ("", None)
    tasas: pd.DataFrame = field(default_factory=pd.DataFrame)
    firma: tuple | None = None          # F39: firma de los archivos con que se puntuó (None en el ejemplo): si cambian, el resultado deja de mostrarse
    nombre_segmento: str = ""           # ``key.segment_context_name`` tal como viene en el archivo (vacío en el ejemplo)


def etiqueta_segmento(vista: Vista) -> str:
    """«Segmento …998801» o, si el archivo trae varios, «5 segmentos»."""
    return f"Segmento {F.segmento_corto(vista.segmento)}" if vista.n_segmentos == 1 else f"{F.entero(vista.n_segmentos)} segmentos"


def tarjetas(vista: Vista) -> list[dict[str, str]]:
    """Las tarjetas de resumen del resultado. Con el archivo 2: celdas marcadas «X de N», cajas afectadas y cajas sin pareja en las celdas marcadas. Sin él no se buscaron huecos, así que esas tres cifras no
    existen: se dice con todas las letras y se muestran las cajas puntuadas y las de la cola."""
    r = vista.resumen
    if vista.tiene_asociacion and vista.n_celdas:
        afectadas = int(r.get("cajas_en_celdas_con_hueco", 0))
        out = [{"clave": "celdas", "etiqueta": "Celdas marcadas", "valor": F.entero(len(vista.lista_A)), "sufijo": f"de {F.entero(vista.n_celdas)}", "nota": "segmento × cámara con posible hueco", "tono": "hueco" if len(vista.lista_A) else ""},
               {"clave": "afectadas", "etiqueta": "Cajas afectadas", "valor": F.entero(afectadas), "nota": "en las celdas marcadas", "tono": ""}]
        if "positivos_en_celdas_con_hueco" in r:
            sin = int(r["positivos_en_celdas_con_hueco"])
            out.append({"clave": "sin_pareja", "etiqueta": "Sin pareja en esas celdas", "valor": F.entero(sin), "nota": f"{F.porcentaje(sin / afectadas, 1)} de las cajas de esas celdas" if afectadas else "no hay cajas en celdas marcadas", "tono": ""})
        else:
            out.append({"clave": "sin_pareja", "etiqueta": "Sin pareja en esas celdas", "valor": "—", "nota": "el archivo 2 no trae las cajas con pareja", "tono": ""})
        return out
    return [{"clave": "celdas", "etiqueta": "Celdas marcadas", "valor": "—", "nota": "no se buscaron: falta el archivo 2", "tono": ""},
            {"clave": "puntuadas", "etiqueta": "Cajas puntuadas", "valor": F.entero(vista.n_cajas), "nota": "peatones y ciclistas, población principal", "tono": ""},
            {"clave": "cola", "etiqueta": "Cajas en la cola", "valor": F.entero(len(vista.lista_B)), "nota": "todas las puntuadas, sin celdas apartadas", "tono": ""}]


def estados_anillo(lista_A: pd.DataFrame, camaras: dict[int, str]) -> dict[int, str]:
    """Estado de cada cámara en el anillo del resultado: «hueco» si alguna celda marcada es de esa cámara, si no «sana»."""
    marcadas = {int(str(c)[0]) for c in lista_A["camara"].astype(str) if str(c)[:1].isdigit()} if len(lista_A) and "camara" in lista_A.columns else set()
    return {c: ("hueco" if c in marcadas else "sana") for c in camaras}


def estados_sin_busqueda(camaras: dict[int, str]) -> dict[int, str]:
    return {c: "apagada" for c in camaras}


# ------------------------------------------------------------------------------------------------------------ vista de presentación de la cola
def preparar_cola_vista(lista_B: pd.DataFrame, cajas: pd.DataFrame, lidar_az: pd.DataFrame | None, rangos: dict[int, tuple[float, float]]) -> pd.DataFrame:
    """Lista B con las columnas de presentación: ``caja`` (final del identificador del objeto y su fotograma), ``camara`` (por azimut, como en la Cola de revisión) y ``clase``. No cambia el orden ni las filas.

    ``cajas`` es el conjunto de cajas puntuadas (para numerar los fotogramas) y ``lidar_az`` trae ``az_signed`` por llave (``None`` si no se pudo calcular: la cámara queda «—»).
    """
    t = lista_B.reset_index(drop=True).copy()
    o, ts = "key.laser_object_id", "key.frame_timestamp_micros"
    rango = cajas.groupby(["seg", o])[ts].rank(method="dense").astype(int)
    num = dict(zip(zip(cajas["seg"], cajas[o], cajas[ts]), rango.to_numpy()))
    t["fotograma"] = [num.get(k, 1) for k in zip(t["seg"], t[o], t[ts])]
    t["caja"] = [f"{str(x)[-4:]}-{int(k):02d}" for x, k in zip(t[o], t["fotograma"])]
    if lidar_az is not None and len(lidar_az):
        t = t.merge(lidar_az, on=["segment_id", ts, o], how="left")
        t["camara"] = camara_de_azimut(t["az_signed"], rangos).to_numpy() if rangos else "—"
    else:
        t["camara"] = "—"
    t["clase"] = np.where(t["object_type"].astype(str).str.upper().str.startswith("CYCLIST"), "Ciclista", "Peatón")
    return t


class FilasPerezosas:
    """Las filas de la cola ya formateadas pero calculadas solo para la página que se pide (con 100.000 cajas no se formatea todo: se ven 50 por vez)."""

    def __init__(self, cola: pd.DataFrame) -> None:
        self.c = cola

    def __len__(self) -> int:
        return len(self.c)

    def __getitem__(self, idx: slice) -> list[list[str]]:
        t = self.c.iloc[idx]
        pos = t["posicion_en_cola"].map(lambda v: F.entero(v)).to_numpy()
        prob = t["prob_calibrada"].map(lambda v: F.menos(F.porcentaje(v, 1))).to_numpy()
        pts = t["num_top_lidar_points"].map(F.entero).to_numpy()
        clase = [CLASE_ADVERTENCIA if c == "Ciclista" else CLASE_NORMAL for c in t["clase"]]
        return [[a, b, str(c), d, e, f] for a, b, c, d, e, f in zip(pos, t["caja"], t["camara"], clase, prob, pts)]

    def __iter__(self):
        return iter(self[0:len(self)])


def tabla_cola(vista: Vista, rangos: dict[int, tuple[float, float]] | None = None) -> Tabla:
    """La cola del segmento con las columnas de la Cola de revisión (Prioridad, Caja, Cámara, Clase, Prob. sin pareja, Puntos sensor sup.). El CSV es la Lista B completa, como antes."""
    cols = [Col("posicion_en_cola", "Prioridad", "int"), Col("caja", "Caja"), Col("camara", "Cámara"), Col("clase", "Clase"),
            Col("prob_calibrada", "Prob. sin pareja", "pct", "Probabilidad estimada de no tener pareja"), Col("num_top_lidar_points", "Puntos sensor sup.", "int", "Puntos del LiDAR superior dentro de la caja")]
    return Tabla("pt_cola", TITULO_COLA, RESPONDE_COLA, cols, FilasPerezosas(vista.cola), lambda: vista.lista_B.to_csv(index=False).encode("utf-8"), NOTA_COLA, 0)  # type: ignore[arg-type]


def tabla_celdas(vista: Vista) -> Tabla | None:
    """La tabla «Celdas marcadas» con los mismos datos de la Lista A (segmento, cámara, tasa de pares, mediana, umbral, cajas en rango y afectadas); ``None`` si no hay."""
    la = vista.lista_A
    if la is None or la.empty:
        return None
    cols = [Col("segmento", "Segmento", "seg"), Col("camara", "Cámara"), Col("cajas_en_rango", "Cajas en rango", "int", "Cajas de la celda dentro del rango de la cámara"), Col("cajas_afectadas", "Cajas afectadas", "int", "Cajas de la población principal en la celda"),
            Col("tasa", "Tasa de pares", "pct", "Proporción de cajas con par 2D en la celda"), Col("mediana_referencia", "Mediana de referencia", "pct", "Tasa de pares normal de esa cámara"), Col("umbral", "Umbral de hueco", "pct", "Tasa bajo la cual la celda se marca")]
    from waymo_evaluacion.ep3.tablas_estandar import construir_tabla

    return construir_tabla("pt_celdas", la, cols, TITULO_CELDAS, RESPONDE_CELDAS)


def zip_resultados(vista: Vista) -> bytes:
    """Un solo archivo con los dos CSV de siempre (Lista A y Lista B, con el mismo contenido que antes), en memoria."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("lista_A_nueva.csv", vista.lista_A.to_csv(index=False))
        z.writestr("lista_B_nueva.csv", vista.lista_B.to_csv(index=False))
    return buf.getvalue()


def tabla_resumen(vista: Vista) -> Tabla:
    """«Resumen del cálculo»: las medidas de siempre (cajas de la población principal, celdas, umbrales, cajas sin pareja si se conocen), con su nombre en español."""
    def valor(v: Any) -> str:
        if v is True:
            return "sí"
        if v is False:
            return "no"
        if v is None:
            return "—"
        if isinstance(v, (int, float)) and float(v).is_integer():
            return F.menos(F.entero(v))
        return F.menos(F.decimal(v, 3)) if isinstance(v, float) else str(v)

    filas = [[ETIQUETAS_RESUMEN.get(k, F.nombre_columna(k)), valor(v)] for k, v in vista.resumen.items()]
    csv = pd.DataFrame({"medida": list(vista.resumen), "valor": list(vista.resumen.values())})
    from waymo_evaluacion.ep3.tablas_estandar import tabla_de_listas

    return tabla_de_listas("pt_resumen", "Resumen del cálculo", "¿Qué cifras salieron del cálculo de este segmento?", [Col("medida", "Medida"), Col("valor", "Valor", "valor")], filas, csv)


def tabla_formato() -> Tabla:
    """«Formato de los archivos de entrada»: archivo, columnas que necesita y para qué sirven, tomadas de ``COLUMNAS_ARCHIVO_1`` y ``COLUMNAS_ARCHIVO_2`` (el código)."""
    from waymo_evaluacion.ep3.tablas_estandar import tabla_de_listas

    return tabla_de_listas("pt_formato", "Formato de los archivos de entrada", "¿Qué columnas necesita cada archivo?", [Col("archivo", "Archivo"), Col("columnas", "Columnas"), Col("uso", "Para qué sirve")], filas_formato(),
                           None, NOTA_FORMATO)


# ------------------------------------------------------------------------------------------------------------ segmentos puntuados en la sesión (F37)
CLAVE_SESION = "_pt_sesion"
SESION_TITULO = "Segmentos puntuados en esta sesión"
SESION_RESPONDE = "¿Qué segmentos nuevos se puntuaron en esta sesión?"
SESION_NOTA = "No forman parte de las cifras congeladas ({n} segmentos de desarrollo). Se pierden al recargar la página."


def registrar_en_sesion(estado: Any, vista: Vista, ahora: str) -> None:
    """Agrega a ``estado[CLAVE_SESION]`` una fila del segmento recién puntuado (solo cifras, no los archivos). Si el segmento ya estaba, se reemplaza su fila; la más reciente queda primero.
    Los ejemplos de desarrollo no se registran: no son segmentos nuevos. ``estado`` es ``st.session_state`` (o un diccionario)."""
    if vista.origen != "archivo":
        return
    r = vista.resumen
    con = vista.tiene_asociacion and vista.n_celdas > 0
    fila = {"segmento": vista.segmento, "etiqueta": etiqueta_segmento(vista), "celdas": len(vista.lista_A) if con else None, "cajas": int(vista.n_cajas),
            "sin_pareja": (r["positivos_total"] / vista.n_cajas if con and "positivos_total" in r and vista.n_cajas else None), "hora": ahora}
    previas = [f for f in estado.get(CLAVE_SESION, []) if f["segmento"] != fila["segmento"] or f["etiqueta"] != fila["etiqueta"]]
    estado[CLAVE_SESION] = [fila] + previas


def tabla_sesion(filas: list[dict[str, Any]]) -> Tabla:
    """La tabla pequeña del Resumen: segmento, celdas marcadas, cajas, cajas sin pareja y hora; «—» donde no se buscaron huecos (sin archivo 2)."""
    from waymo_evaluacion.ep3.tablas_estandar import tabla_de_listas

    datos = [[(F.segmento_corto(f["segmento"]) if f["etiqueta"].startswith("Segmento ") else f["etiqueta"]), "—" if f["celdas"] is None else F.entero(f["celdas"]), F.entero(f["cajas"]),
              "—" if f["sin_pareja"] is None else F.porcentaje(f["sin_pareja"], 1), f["hora"]] for f in filas]
    cols = [Col("segmento", "Segmento"), Col("celdas", "Celdas marcadas", "valor"), Col("cajas", "Cajas", "valor"), Col("sin_pareja", "Sin pareja", "valor", "Cajas sin pareja 2D sobre las cajas puntuadas"), Col("hora", "Hora", "valor")]
    return tabla_de_listas("rs_sesion", SESION_TITULO, SESION_RESPONDE, cols, datos, None)


# ------------------------------------------------------------------------------------------------------------ el ejemplo con su celda marcada (F37)
def completar_ejemplo(res: Any, cajas: pd.DataFrame, lista_A: pd.DataFrame | None, celdas: pd.DataFrame | None, segmento: str) -> Any:
    """Al resultado de puntuar el ejemplo (sin archivo 2) le agrega lo que la página YA tiene calculado para ese segmento de desarrollo con su archivo de asociación real: las celdas marcadas
    (``lista_A.csv``), las tasas y cajas en rango por cámara (``celdas.csv``) y, por caja, si está en una celda marcada y si no tiene pareja (``cajas_oof``). No se reconstruyen ni se inventan
    parejas por cámara: son los valores de desarrollo tal cual. La cola se vuelve a armar sin las cajas de las celdas marcadas, igual que con dos archivos.
    Si falta alguna de las tres tablas o el segmento no está en ellas, devuelve ``res`` sin cambios (el ejemplo sin celdas de antes)."""
    from dataclasses import replace

    if cajas is None or celdas is None or lista_A is None or "en_hueco" not in cajas.columns or "sin_camara" not in cajas.columns:
        return res
    necesarias = ({"seg", "key.frame_timestamp_micros", "key.laser_object_id"} <= set(cajas.columns) and {"segmento", "camara", "tasa", "mediana_camara", "umbral", "cajas_en_rango", "cajas_afectadas_poblacion_principal"} <= set(lista_A.columns)
                  and {"seg"} | {f"tasa_c{n}" for n in range(1, 6)} | {f"n_rango_c{n}" for n in range(1, 6)} <= set(celdas.columns))
    if not necesarias:
        return res
    fila = celdas[celdas["seg"].astype(str) == str(segmento)]
    d = cajas[cajas["seg"].astype(str) == str(segmento)]
    if fila.empty or d.empty or res.cajas.empty:
        return res
    llave = ["key.frame_timestamp_micros", "key.laser_object_id"]
    ppal = res.cajas.copy()
    m = ppal[llave].merge(d[llave + ["en_hueco", "sin_camara"]].drop_duplicates(llave), on=llave, how="left")
    ppal["en_hueco"] = m["en_hueco"].fillna(False).astype(bool).to_numpy()
    ppal["sin_camara"] = m["sin_camara"].fillna(0).astype(int).to_numpy()
    cola = ppal[~ppal["en_hueco"]].sort_values("score", ascending=False, kind="stable")
    ppal["posicion_en_cola"] = np.nan
    ppal.loc[cola.index, "posicion_en_cola"] = np.arange(1, len(cola) + 1)
    ppal["percentil_en_cola"] = ppal["posicion_en_cola"] / max(len(cola), 1)
    lista_b = ppal.loc[cola.index].sort_values("posicion_en_cola")
    a = lista_A[lista_A["segmento"].astype(str) == str(segmento)]
    nueva_a = pd.DataFrame({"segmento": a["segmento"].astype(str).to_numpy(), "camara": a["camara"].to_numpy(), "tasa": a["tasa"].astype(float).to_numpy(), "mediana_referencia": a["mediana_camara"].astype(float).to_numpy(),
                            "umbral": a["umbral"].astype(float).to_numpy(), "cajas_en_rango": a["cajas_en_rango"].astype(int).to_numpy(), "cajas_afectadas": a["cajas_afectadas_poblacion_principal"].astype(int).to_numpy()})
    f = fila.iloc[0]
    tasas = pd.concat({"tasa": pd.DataFrame({f"c{n}": [float(f[f"tasa_c{n}"])] for n in range(1, 6)}, index=[str(segmento)]),
                       "cajas_en_rango": pd.DataFrame({f"c{n}": [int(f[f"n_rango_c{n}"])] for n in range(1, 6)}, index=[str(segmento)])}, axis=1)
    resumen = dict(res.resumen)
    resumen.update({"cajas_en_celdas_con_hueco": int(ppal["en_hueco"].sum()), "cajas_en_lista_B": int(len(lista_b)), "celdas_con_hueco": int(len(nueva_a)), "tiene_asociacion": True,
                    "positivos_total": int(ppal["sin_camara"].sum()), "positivos_en_celdas_con_hueco": int(ppal.loc[ppal["en_hueco"], "sin_camara"].sum())})
    adv = [x for x in res.advertencias if not x.lower().startswith("sin archivo de asociación")]
    return replace(res, cajas=ppal, lista_A=nueva_a, lista_B=lista_b[list(ppal.columns)], tasas=tasas, resumen=resumen, advertencias=adv)
