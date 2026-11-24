"""Textos y lógica de «Ética y límites» y de «Ayuda y glosario» (F36). Funciones puras (sin Streamlit).

Las frases de estas dos páginas viven aquí o en ``app_logica.py`` (glosario, preguntas frecuentes y los textos que dependen del modo de despliegue, ``TEXTOS_ENTORNO``); ``app/secciones.py`` solo las dibuja.
Cada frase que antes estaba en la página sigue existiendo con la misma redacción; las que se partieron en dos para el nuevo diseño están listadas en ``FRASES_AJUSTADAS`` (la prueba de regresión de textos las cita).
"""
from __future__ import annotations

import unicodedata
from typing import Any

from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.app_logica import GLOSARIO

# ------------------------------------------------------------------------------------------------------------ Ética y límites
HERO_TITULO = "Decide siempre una persona."
HERO_TEXTO = "La solución ordena las cajas y avisa qué cámaras tienen huecos. No etiqueta ni borra nada."
HERO_AVISOS = ("Nunca debe usarse para descartar cajas sin revisarlas.", "No es una prueba de seguridad del vehículo. Mide si una caja 3D tiene pareja 2D, no si el peatón fue bien detectado.")
PROPOSITO = ("Ordenar las cajas 3D de peatones y ciclistas para que una persona revise primero las que más probablemente no tienen su par 2D de cámara, y avisar qué cámaras tienen huecos.")
DATOS_PUNTOS = ("Waymo Open Dataset v2, {n} segmentos de desarrollo.", "El conjunto es de uso no comercial y sus datos no se redistribuyen.", "El trabajo es académico (curso MLY1101).")
DESEMPENO_INTRO = "En validación cruzada por segmentos."
DESEMPENO_ETIQUETA = "en muestra"
DESEMPENO_NOTA = "Todas las cifras son en muestra: {n} segmentos, detector ajustado con los mismos datos y sin prueba ciega. Los intervalos están en Validación."
DESEMPENO_TARJETAS = (("AUC fuera de fold", "AUC"), ("Recall en el punto A", "Recall en el punto A"), ("Captura al revisar el 20 %", "Cajas sin pareja que se encuentran al revisar el 20 %"))
ENLACE_VALIDACION = "Ver Validación"
LIMITES_INTRO = "La regla es poco confiable para ciclistas."
LIMITES_BARRA_DESCRIPCION = "Casos encontrados: peatones {p}, ciclistas {c}."
LIMITES_CASOS = "Casos encontrados · ciclistas: {casos} casos en {segmentos} segmentos."
LIMITES_PUNTOS = ("Hay más segmentos de día que de noche y tres ubicaciones.", "Un hueco es una hipótesis para revisar, no una conclusión; los hallazgos post hoc son hipótesis.")

# ------------------------------------------------------------------------------------------------------------ Ayuda y glosario
PASOS_TITULO = "Cómo funciona, en tres pasos"
PASOS = (("Detector de huecos", "Marca las celdas segmento × cámara donde casi ninguna caja tiene pareja. Se atienden aparte.", "Auditoría de cámaras"),
         ("Cola de cajas", "La regla «menos puntos del sensor superior» ordena las cajas restantes en una cola.", "Cola de revisión"),
         ("Una persona decide", "Una persona revisa y decide. La solución no etiqueta ni borra nada.", "Ética y límites"))
PAGINAS_TITULO = "Qué hace cada página"
USO_ROL = "El rol (pie de la barra lateral) cambia la página que se abre."
USO_COLA = "Se elige el segmento, el flujo y el presupuesto (o la meta); al seleccionar una fila se ve el detalle de la caja; la lista se descarga en CSV."
USO_AUDITORIA = "Muestra las celdas marcadas como hueco y qué hacer con ellas."
GLOSARIO_TITULO = "Glosario"
GLOSARIO_BUSCADOR = "Buscar un término…"
GLOSARIO_ETIQUETA_BUSCADOR = "Buscar un término del glosario"
GLOSARIO_SIN_RESULTADOS = "Ningún término coincide con la búsqueda."
GRUPO_TODOS = "Todos"
GRUPOS_GLOSARIO = {"Datos": ("Caja", "Par 2D", "Celda", "Hueco"), "Revisión": ("Cola", "Presupuesto", "Cobertura"), "Rigor": ("Intervalo de confianza", "Post hoc", "En muestra", "Sin prueba ciega")}
GRUPO_POR_DEFECTO = "Otros"                       # un término nuevo del glosario que no esté en ``GRUPOS_GLOSARIO`` se muestra bajo «Otros» (ninguno hoy)
PREGUNTAS_TITULO = "Preguntas frecuentes"

# Frases de antes que se partieron o se reescribieron en el diseño nuevo, con la razón (la prueba de regresión de textos las acepta como excepciones documentadas)
FRASES_AJUSTADAS = {
    "Decide siempre una persona: la solución no etiqueta ni borra nada y nunca debe usarse para descartar cajas sin revisarlas.": "partida: «Decide siempre una persona.» (título), «No etiqueta ni borra nada.» y el aviso «Nunca debe usarse para descartar cajas sin revisarlas.»",
    "No es una prueba de seguridad del vehículo: mide si una caja 3D tiene pareja 2D, no si el peatón fue bien detectado.": "partida en dos frases (los dos puntos pasan a punto)",
    "En validación cruzada por segmentos: AUC {auc}, recall en el punto A {recall} y {cap} de las cajas sin pareja al revisar el 20 % de las cajas (intervalos en «Validación»).": "reemplazada por tres tarjetas con las mismas cifras y el enlace «Ver Validación»",
    "La regla es poco confiable para ciclistas ({c} contra {p} en peatones; {casos} casos en {segmentos} segmentos).": "partida: la frase, la barra con los dos porcentajes y «Casos encontrados · ciclistas: N casos en M segmentos.»",
    "(1) el detector de huecos marca las celdas segmento × cámara donde casi ninguna caja tiene pareja y se atienden aparte; (2) la regla «menos puntos del sensor superior» ordena las cajas restantes en una cola; (3) una persona revisa y decide.":
        "partida en tres tarjetas numeradas (con la frase «La solución no etiqueta ni borra nada», que ya existía en Ética)",
    "No se midió: se usa un supuesto de 20 segundos por caja, editable en «Supuestos» de la cola de revisión.": "ajuste mínimo para seguir siendo cierta: el desplegable de la cola se llama «Supuestos y confiabilidad» desde F32",
}


def _norm(t: str) -> str:
    """Minúsculas y sin tildes, para buscar sin distinguir mayúsculas ni acentos."""
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(c) != "Mn")


def grupo_de(termino: str) -> str:
    """El grupo del glosario (Datos, Revisión o Rigor) al que pertenece un término; los que no estén en ``GRUPOS_GLOSARIO`` van a «Otros»."""
    return next((g for g, ts in GRUPOS_GLOSARIO.items() if termino in ts), GRUPO_POR_DEFECTO)


def grupos_del_glosario(glosario: list[tuple[str, str]] | None = None) -> list[str]:
    """«Todos» y los grupos que tienen términos (en el orden de ``GRUPOS_GLOSARIO``; «Otros» al final solo si hace falta)."""
    gl = glosario if glosario is not None else GLOSARIO
    usados = {grupo_de(t) for t, _ in gl}
    return [GRUPO_TODOS] + [g for g in (*GRUPOS_GLOSARIO, GRUPO_POR_DEFECTO) if g in usados]


def filtrar_glosario(busqueda: str = "", grupo: str | None = None, glosario: list[tuple[str, str]] | None = None) -> list[dict[str, str]]:
    """Términos que cumplen la búsqueda (en el término o en la definición, sin distinguir mayúsculas ni tildes) y el grupo («Todos» o ``None`` no filtra). Conserva el orden del glosario."""
    gl = glosario if glosario is not None else GLOSARIO
    q = _norm(busqueda).strip()
    out = []
    for termino, definicion in gl:
        g = grupo_de(termino)
        if grupo not in (None, "", GRUPO_TODOS) and g != grupo:
            continue
        if q and q not in _norm(termino + " " + definicion):
            continue
        out.append({"termino": termino, "grupo": g, "definicion": definicion})
    return out


def tarjetas_desempeno(claves_kpi: dict[str, str]) -> list[tuple[str, str]]:
    """Las tres tarjetas de Desempeño: (etiqueta, valor) con los valores de las tarjetas de ``kpis.json`` (las mismas que muestran Validación y el Resumen); las que falten se omiten."""
    return [(etiqueta, str(claves_kpi[clave])) for clave, etiqueta in DESEMPENO_TARJETAS if claves_kpi.get(clave)]


def comparacion_clases(ciclistas: dict[str, float]) -> dict[str, Any] | None:
    """Datos de la barra peatones/ciclistas: porcentajes y casos (de ``datos_ciclistas``, las mismas cifras de Validación); ``None`` si no están."""
    if not all(isinstance(ciclistas.get(k), float) and ciclistas[k] == ciclistas[k] for k in ("ciclista", "peaton", "positivos", "segmentos")):
        return None
    return {"peaton": ciclistas["peaton"], "ciclista": ciclistas["ciclista"], "peaton_txt": F.porcentaje(ciclistas["peaton"]), "ciclista_txt": F.porcentaje(ciclistas["ciclista"]),
            "casos": F.entero(ciclistas["positivos"]), "segmentos": F.entero(ciclistas["segmentos"])}
