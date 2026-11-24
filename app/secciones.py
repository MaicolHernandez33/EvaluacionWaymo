"""Secciones de la página (nombre y textos de marca: constantes de ``app_logica``; F20). Cada función recibe el contexto ``ctx`` (datos, rol, cachés) y dibuja una sección.

Los números salen de ``waymo_evaluacion.ep3.app_logica`` (lógica probada) y se formatean con ``waymo_evaluacion.ep3.formato`` (es-CL). Sin conexiones externas.
El marco (navegación, estilos, rol, pie) está en ``app/app.py``; cada archivo de ``app/paginas/`` llama a ``ejecutar(nombre_de_la_sección)``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import estilos as E
from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.app_logica import (
    ARCHIVO_PAGINA, AVISO_EN_MUESTRA, CAMARAS, camaras_con_celdas_marcadas, criterios_seleccion, estado_camaras_segmento, CLASE_ADVERTENCIA, CLASE_NORMAL, COLUMNA_FOTOGRAMAS, COLUMNA_PROBABILIDAD, CURVA_UN_PASO, DESCRIPCION_PAGINA, EJEMPLOS_CAJA,
    SUBTITULO_RESUMEN, TITULO_RESUMEN, texto_entorno, cola_segmento,
    ACCION_ABRIR, ACCION_AUDITAR, ENLACE_COLA, ESTADO_HUECO, ETIQUETA_CICLISTA, FILAS_ALERTAS_RESUMEN, FILAS_COLA_RESUMEN, KICKER_ALERTAS, NOTA_ORDEN_COLA,
    AUD_AVISO_CELDA, AUD_AYUDA_MAPA, AUD_AYUDA_TABLA, AUD_DEFINICION, AUD_NOTA_DESARROLLO, AUD_ORIGEN_FILA, AUD_ORIGEN_RESUMEN, AUD_QUE_ES, AUD_TITULO_ANILLO, AUD_TITULO_MAPA, AUD_TITULO_TABLA,
    ENLACE_COLA_DESDE_AUDITORIA, FILAS_MAPA_INICIO, orden_gravedad, resumen_auditoria, rotulo_boton_mapa, siguiente_filas_mapa, tabla_celdas_auditoria, texto_umbral_hueco, titular_auditoria,
    COLA_BOTON_EXPLICAR, COLA_LLAMADA, COLA_NOTA_BANDA, COLA_SUPUESTOS, COLA_TAB_CURVA, COLA_TAB_LISTA, COLA_TITULO_CURVA, FILAS_PAGINA_COLA, aviso_empate, clase_con_etiqueta, pagina_cola, preparar_cola, tarjetas_cola,
    EXP_AVISO_CICLISTA, EXP_AVISO_ORIGEN, EXP_ENLACE_VOLVER, EXP_PASOS, EXP_PASOS_DETALLE, EXP_ETIQUETA_COLA, EXP_ROTULO_80, EXP_ROTULO_REVISA, empatadas_arriba, opciones_puntos, referencia_cola, textos_veredicto, texto_lugar, veredicto_caja, umbral_presupuesto,
    SEGMENTOS_PRIORITARIOS_RESUMEN, SUBTITULO_ALERTAS, SUBTITULO_COLA_RESUMEN, SUBTITULO_SEGMENTOS_PRIORITARIOS, SUBTITULO_SIN_ALERTAS, TITULAR_ALERTAS, TITULAR_SIN_ALERTAS, TITULO_COLA_RESUMEN, TITULO_SEGMENTOS_PRIORITARIOS,
    celdas_marcadas_lista, cola_prioritaria, filtrar_cola_resumen, indicadores_resumen, segmentos_prioritarios, valores_para_explicar,
    FLUJO_DOS, FLUJOS, GLOSARIO, NOTA_AGRUPADO, NOTA_FOTOGRAMAS, REFERENCIAS, SUPUESTO_SEGUNDOS, curva_dependencia, curva_inversa, curvas_a_mostrar, datos_validacion, detalle_caja,
    ESCALA_PUNTOS, PASOS_DEL_CALCULO, ejemplo_lidar_box, explicacion_caja, nota_empate, texto_puntaje, filtrar_cola, info_tipo_de_caso, inicio_resumen, lectura_evidencia, lista_A_detalle, lista_A_presentable, matriz_calor, nombre_curva_legible,
    orden_segmentos, percentil_en_cola, preguntas_frecuentes, recall_en_presupuesto, resumen_cola, tabla_cola, tabla_por_objeto, tabla_resultados_clave, texto_esfuerzo_cola,
    texto_posicion, texto_resultado_cola, tipo_de_caso, validar_asociacion, validar_lidar_box,
)

import tablas as T  # noqa: E402  (componente único de tabla de F34)
from waymo_evaluacion.ep3 import etica_ayuda as EA  # noqa: E402
from waymo_evaluacion.ep3 import puntuar as P  # noqa: E402
from waymo_evaluacion.ep3 import validacion as V  # noqa: E402
from waymo_evaluacion.ep3.validacion import DESCRIPCION_GRAFICO  # noqa: E402
MODO_PRESUPUESTO = "Presupuesto"
MODO_OBJETIVO = "Meta"
MAX_FILAS_COLA = 500
MAX_FILAS_LISTA_A = 30
TAMANO_ANILLO_RESUMEN = 240                                                                     # px: legible y sin hacer alto el bloque de alertas
ESTILO_GRAFICO = {"font": E.PILA_SVG}
GRIS_GRAFICO = E.SERIE_GRIS


def _html(x: str) -> None:
    st.markdown(x, unsafe_allow_html=True)


def _tabla(df: pd.DataFrame, **kw: Any) -> Any:
    """``st.dataframe`` compacto con el ancho de cada columna calculado con su encabezado y su contenido (ningún encabezado cortado)."""
    anchos = F.anchos_columnas(df, maximo=kw.pop("ancho_max", 460))
    cfg = {c: st.column_config.Column(width=w) for c, w in anchos.items()}
    cfg.update(kw.pop("column_config", {}))
    return st.dataframe(df, width="stretch", hide_index=True, row_height=30, height=min(38 + 30 * len(df), kw.pop("alto_max", 420)), column_config=cfg, **kw)


def _grafico(ch: alt.Chart | alt.LayerChart, **kw: Any) -> None:
    """Tema único de los gráficos (F24, oscuro): fondo transparente, cuadrícula del panel, ejes y etiquetas en Texto 2 de 12 px como mínimo, títulos y leyendas en Texto."""
    t = E.TOKENS
    # una sola llamada a configure (cada configure_* copia y valida el gráfico completo: cinco llamadas costaban unos 75 ms por gráfico)
    cfg = ch.configure(background="transparent", font=ESTILO_GRAFICO["font"],
                       axis=alt.AxisConfig(labelFontSize=12, titleFontSize=12, titleColor=t["texto"], labelColor=t["texto_2"], gridColor=t["panel_borde"], domain=False, tickColor=t["panel_borde"], titleFontWeight=600),
                       view=alt.ViewConfig(strokeWidth=0, fill="transparent"),
                       legend=alt.LegendConfig(labelColor=t["texto"], labelFontSize=12, titleColor=t["texto"]),
                       title=alt.TitleConfig(color=t["texto"]))
    st.altair_chart(cfg, width="stretch", **kw)


def _estados_camaras(lista_a: pd.DataFrame) -> tuple[dict[int, str], dict[int, int]]:
    """Estado de cada cámara en el anillo de la Auditoría (``hueco`` si tiene celdas marcadas, si no ``sana``) y las celdas marcadas por cámara, desde la Lista A."""
    cuenta = camaras_con_celdas_marcadas(lista_a)
    return {cam: ("hueco" if cuenta.get(cam) else "sana") for cam in CAMARAS}, cuenta


def _texto_camaras(cuenta: dict[int, int]) -> str:
    if not cuenta:
        return "Ninguna cámara tiene celdas marcadas."
    return "\n".join(f"Cámara {CAMARAS[c]}: {F.entero(n)} {'celda marcada' if n == 1 else 'celdas marcadas'}." for c, n in sorted(cuenta.items()))


def _eje_decimal(d: int = 2) -> str:
    """Expresión de Vega para que las etiquetas del eje salgan con coma decimal (es-CL)."""
    return f"replace(replace(format(datum.value, '.{d}f'), '.', ','), '-', '\u2212')"          # coma decimal y signo menos único (F34)


def _marcas_eje(valores: list[float], objetivo: int = 9) -> tuple[list[float], int]:
    """Marcas «bonitas» para un eje de efectos (F21-P5): paso de 0,001 a 0,1 que deja unas nueve marcas, sin repetir etiquetas. Devuelve las marcas y los decimales."""
    lo, hi = min(min(valores), 0.0), max(max(valores), 0.0)
    paso = next((s for s in (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2) if (hi - lo) / s <= objetivo), 0.2)
    n0, n1 = int(np.floor(lo / paso + 1e-9)), int(np.ceil(hi / paso - 1e-9))
    return [round(i * paso, 6) for i in range(n0, n1 + 1)], (3 if paso < 0.01 else 2)


def encabezado(titulo: str, descripcion: str) -> None:
    """Encabezado de página: título y una línea de descripción. Sin chip de estado (F26): la divulgación de rigor («en muestra», «sin validación externa») está en las oraciones, en la alerta del Resumen y en el pie."""
    st.title(titulo)
    _html(f'<p class="aud-descripcion">{E._e(descripcion)}</p>')


# ------------------------------------------------------------------------------------------------------------ Resumen
def _elegir_celda(i: int) -> None:
    st.session_state["celda_resumen"] = i


def _ir_a_auditoria(celda: dict[str, Any]) -> None:
    """«Auditar»: la Auditoría de cámaras se abre con ese segmento y esa cámara ya elegidos. El cambio de página lo resuelve ``app.py`` con ``_ir`` (``st.switch_page`` no es fiable en un callback)."""
    st.session_state["_auditoria_celda"] = {"segmento": celda["segmento"], "camara": celda["camara"]}
    st.session_state["_ir"] = "Auditoría de cámaras"


def _ir_a_explica(valores: dict[str, Any], segmento: str, caja: str, prioridad: int = 0, origen: str = "Resumen") -> None:
    """«Abrir» (Resumen) o «Explicar esta caja →» (Cola): «Explica una caja» se abre con los valores de esa caja ya puestos y con el aviso de dónde vienen y cómo volver."""
    st.session_state["_explica_caja"] = {**valores, "segmento": segmento, "caja": caja, "prioridad": int(prioridad), "origen": origen}
    st.session_state["_ir"] = "Explica una caja"


def _cifras_de_apoyo(ctx: dict[str, Any], r: dict[str, Any]) -> list[tuple[str, str, str, float | None, str]]:
    """Filas de la tabla de cifras de apoyo: cajas, prevalencia, AUC y casos encontrados por clase. Todas salen de los módulos existentes (``inicio_resumen``, tarjetas de kpis, ``ciclistas``)."""
    filas: list[tuple[str, str, str, float | None, str]] = [("Cajas analizadas", F.entero(r["cajas"]), "peatones y ciclistas", None, ""), ("Cajas sin pareja", F.porcentaje(r["prevalencia"]), "sin par en ninguna cámara", None, "")]
    claves = {t.get("titulo", ""): t.get("valor", "") for t in ctx["K"].get("tarjetas", [])}
    if claves.get("AUC fuera de fold"):
        filas.append(("AUC", str(claves["AUC fuera de fold"]), "validación cruzada por segmentos", None, ""))
    c = ctx["ciclistas"] or {}
    if all(isinstance(c.get(k), float) and c[k] == c[k] for k in ("ciclista", "peaton")):
        filas += [("Casos encontrados en peatones", F.porcentaje(c["peaton"]), "", None, ""), ("Casos encontrados en ciclistas", F.porcentaje(c["ciclista"]), "la regla es poco confiable en ciclistas", None, "")]
    return filas


def _titular_alertas(n: int) -> str:
    """El titular del bloque de alertas: «Hay N posibles huecos de cámara en los últimos datos sin revisar.» (con «N posibles huecos de cámara» en el color de alerta) o, sin celdas marcadas, el titular de «todo sano»."""
    if n == 0:
        return E.titular(E._e(TITULAR_SIN_ALERTAS))
    huecos = f'<span class="alerta">{F.entero(n)} {"posible hueco" if n == 1 else "posibles huecos"} de cámara</span>'
    return E.titular(TITULAR_ALERTAS.format(huecos=huecos))


def resumen(ctx: dict[str, Any]) -> None:
    """Resumen para uso diario (F29, ajustado en F30): indicadores, alertas de cámara con su anillo, cola de revisión con segmentos prioritarios."""
    D = ctx["D"]
    segundos = st.session_state.get("segundos", SUPUESTO_SEGUNDOS)
    r = inicio_resumen(D, segundos)
    encabezado(TITULO_RESUMEN, SUBTITULO_RESUMEN.format(n=F.entero(r["segmentos"])))
    cola_tabla, cola_total = cola_prioritaria(D["cajas"], ctx["rangos"])
    _html(E.indicadores(indicadores_resumen(D, r, cola_total)))
    corto = lambda s: "…" + str(s)[-6:]                                                          # noqa: E731  (los 6 últimos dígitos del segmento)
    _bloque_alertas(ctx, r, matriz_calor(D["celdas"], ctx.get("min_cajas", 100)), celdas_marcadas_lista(D["lista_A"]), corto)
    _bloque_cola(cola_tabla, corto)
    _bloque_sesion(r["segmentos"])


def _bloque_sesion(n_desarrollo: Any) -> None:
    """«Segmentos puntuados en esta sesión» (F37): solo aparece después de puntuar un segmento nuevo en «Puntuar datos nuevos»; va debajo de todo lo congelado, que no cambia."""
    filas = st.session_state.get(P.CLAVE_SESION, [])
    if not filas:
        return
    with st.container(key="rs_sesion"):
        T.mostrar_tabla(P.tabla_sesion(filas), "rs_sesion", titulo=True)
        st.caption(P.SESION_NOTA.format(n=F.entero(n_desarrollo)))


def _bloque_alertas(ctx: dict[str, Any], r: dict[str, Any], m: pd.DataFrame, celdas: list[dict[str, Any]], corto: Any) -> None:
    """Bloque «Alertas de cámara» en dos columnas: a la izquierda rótulo, titular, subtítulo y filas de alerta; a la derecha el anillo, arriba, con su rótulo encima y la leyenda debajo.

    El recuadro mide lo que mide su contenido más alto (sin cabecera aparte ni hueco bajo las filas); con muchas alertas crece la columna izquierda y el anillo sigue arriba.
    """
    n = len(celdas)
    sel = int(st.session_state.get("celda_resumen", 0))
    if not 0 <= sel < max(n, 1):
        sel = st.session_state["celda_resumen"] = 0                                             # la primera fila viene elegida por defecto
    sub = SUBTITULO_ALERTAS.format(n=F.entero(r["segmentos"])) if n else SUBTITULO_SIN_ALERTAS.format(hora=ctx.get("hora_datos") or "sin dato")
    with st.container(key="panel_principal"):
        izq, der = st.columns([1.4, 1], gap="large", vertical_alignment="top")
        with izq:
            st.markdown(E.kicker(KICKER_ALERTAS) + _titular_alertas(n) + f'<p class="aud-descripcion">{E._e(sub)}</p>', unsafe_allow_html=True)
            if not n:
                _html(E.vacio("Sin celdas marcadas", "No hay celdas marcadas en los datos cargados."))
            for i, c in enumerate(celdas[:FILAS_ALERTAS_RESUMEN]):
                es_sel = i == sel
                with st.container(key=f"{'celdasel' if es_sel else 'celda'}_{i}"):
                    b1, b2 = st.columns([4, 1.15], vertical_alignment="center")
                    with b1:                                                                  # el rótulo es el control que elige la fila; el estado va en palabras debajo
                        st.button(f"Segmento {corto(c['segmento'])} · cámara {c['camara_num']}, {c['camara_nombre']}", key=f"sel_celda_{i}", type="tertiary", icon=":material/cancel:",
                                  on_click=_elegir_celda, args=(i,), width="stretch")
                        _html(E.celda_estado(ESTADO_HUECO, f"{F.entero(c['cajas_afectadas'])} cajas afectadas"))
                    b2.button(ACCION_AUDITAR, key=f"auditar_{i}", type="primary" if es_sel else "secondary", on_click=_ir_a_auditoria, args=(c,), width="stretch")
            if n > FILAS_ALERTAS_RESUMEN:
                st.caption(f"Se muestran las primeras {F.entero(FILAS_ALERTAS_RESUMEN)} de {F.entero(n)} celdas marcadas; el resto está en la auditoría de cámaras.")
        with der:
            seg = celdas[sel]["segmento"] if n else (str(m["seg"].iloc[0]) if len(m) else "")
            estados = estado_camaras_segmento(m, seg) if seg else {c: "sin_datos" for c in CAMARAS}
            _html(f'<p class="aud-descripcion aud-rotulo-anillo">Cámaras del segmento {E._e(corto(seg)) if seg else "—"}</p>')
            _html(E.bloque_anillo(estados, TAMANO_ANILLO_RESUMEN, "Estado de las cinco cámaras del segmento elegido: " + ", ".join(f"{c} {E.ROTULO_ESTADO[e].lower()}" for c, e in estados.items())))


def _bloque_cola(cola_tabla: pd.DataFrame, corto: Any) -> None:
    cab, enl = st.columns([4, 1.3], vertical_alignment="bottom")
    cab.markdown(f"### {TITULO_COLA_RESUMEN}")
    cab.markdown(f'<p class="aud-descripcion">{E._e(SUBTITULO_COLA_RESUMEN)}</p>', unsafe_allow_html=True)
    with enl.container(key="enlace_cola"):
        st.page_link(ARCHIVO_PAGINA["Cola de revisión"], label=ENLACE_COLA)
    prioritarios = segmentos_prioritarios(cola_tabla, n=10 ** 6)
    f1, f2, f3, _ = st.columns([1.1, 1.4, 1.5, 1.6])
    clase = f1.selectbox("Clase", ["Todas", "Peatón", "Ciclista"], key="res_clase", format_func=lambda x: f"Clase: {x.lower()}", label_visibility="collapsed")
    camara = f2.selectbox("Cámara", ["Todas", *CAMARAS.values()], key="res_camara", format_func=lambda x: f"Cámara: {x.lower() if x == 'Todas' else x}", label_visibility="collapsed")
    segmento = f3.selectbox("Segmento", ["Todos", *[s for s, _n in prioritarios]], key="res_segmento", format_func=lambda s: "Segmento: todos" if s == "Todos" else f"Segmento: {corto(s)}", label_visibility="collapsed")
    vista = filtrar_cola_resumen(cola_tabla, clase, camara, segmento).head(FILAS_COLA_RESUMEN)
    izq, der = st.columns([2.1, 1], gap="large")
    with izq:
        if vista.empty:
            _html(E.vacio("Ninguna caja cumple los filtros", "Quite un filtro para volver a ver la cola."))
        else:
            with st.container(key="cola_resumen"):
                with st.container(key="cola_cabecera"):
                    h1, h2 = st.columns([6.2, 1], vertical_alignment="center")
                    h1.markdown(E.cola_cabecera(), unsafe_allow_html=True)
                    h2.markdown('<div class="aud-cola-fila cab accion"><span>Acción</span></div>', unsafe_allow_html=True)
                for orden, (idx, f) in enumerate(vista.iterrows()):
                    caja = str(f["caja"])
                    with st.container(key=f"filacola_{orden}"):
                        c1, c2 = st.columns([6.2, 1], vertical_alignment="center")
                        c1.markdown(E.cola_fila(F.entero(int(idx) + 1), corto(f["seg"]), caja, str(f["camara"]), str(f["clase"]), F.porcentaje(f["prob_cal"], 1),
                                                ETIQUETA_CICLISTA if f["clase"] == "Ciclista" else ""), unsafe_allow_html=True)
                        c2.button(ACCION_ABRIR, key=f"abrir_{orden}", type="tertiary", on_click=_ir_a_explica, args=(valores_para_explicar(f), str(f["seg"]), caja, int(idx) + 1, "Resumen"))
        st.caption(NOTA_ORDEN_COLA)
    with der:
        with st.container(key="panel_segmentos"):
            st.markdown(f"**{TITULO_SEGMENTOS_PRIORITARIOS}**")
            st.caption(SUBTITULO_SEGMENTOS_PRIORITARIOS)
            _html(E.barras_segmentos([(corto(s), F.entero(k), k) for s, k in prioritarios[:SEGMENTOS_PRIORITARIOS_RESUMEN]]))


def _impacto_estimado(r: dict[str, Any], segundos: float) -> None:
    """«Impacto estimado» (horas con y sin cola): sección fija de Validación, pestaña «En muestra», debajo del gráfico."""
    st.markdown("#### Impacto estimado")
    if r["horas_un_paso"] is None or r["horas_dos_pasos"] is None:
        st.caption("No hay tabla de la validación del flujo en dos pasos en los datos de la página: no se puede estimar el impacto.")
        return
    h0, h1, h2 = r["horas_sin_orden"], r["horas_un_paso"], r["horas_dos_pasos"]
    st.markdown(f"Ordenar la cola reduce el tiempo para encontrar el 80 % de las cajas sin pareja de ≈ **{F.horas(h0, 0)}** a ≈ **{F.horas(h1, 0)}** ({F.porcentaje(1 - h1 / h0, 0)} menos). "
                f"Con auditoría previa de las celdas marcadas baja a ≈ {F.horas(h2, 0)}.")
    st.caption(f"Horas para encontrar el 80 % de las cajas sin pareja ({F.entero(segundos)} s por caja, supuesto).")
    _html(E.tabla_cifras([("Revisión sin orden", f"≈ {F.horas(h0, 0)}", "", 1.0, E.FLUJOS_COLORES["Revisión sin orden"]), ("Solo cola (un paso)", f"≈ {F.horas(h1, 0)}", "", h1 / h0, E.FLUJOS_COLORES["Solo cola (un paso)"]),
                          ("Auditoría + cola (dos pasos)", f"≈ {F.horas(h2, 0)}", "", h2 / h0, E.FLUJOS_COLORES["Auditoría + cola (dos pasos)"])]))
    n1, n2 = st.columns([3.2, 1], vertical_alignment="center")
    n1.caption(f"Estimación: {F.entero(r['cajas'])} cajas × fracción para el 80 % × {F.entero(segundos)} s por caja (supuesto, no medido).")
    with n2.popover("Fuente"):
        st.markdown("Informe técnico de EP3: sección 12 (cuadro «Modelo escogido»: fracción de cajas para el 80 % en un paso y en dos pasos) y anexo B (análisis en muestra). "
                    f"El número de cajas es el de la población principal ({F.entero(r['cajas'])}, {F.entero(r['segmentos'])} segmentos).")


# ------------------------------------------------------------------------------------------------------------ Cola de revisión
def _volver_a_20() -> None:
    st.session_state["presupuesto"] = 20


def _grafico_cobertura(D: dict[str, Any], r: dict[str, Any], presup: float, ref: str) -> None:
    """Curva de priorización legible (F32): etiquetas directas sobre las líneas (sin leyenda), eje en porcentaje con marcas cada 10 %, banda del intervalo y una marca en el presupuesto actual con la
    llamada «X de cada 100 (dos pasos), Y (un paso)», con las mismas cifras de las tarjetas."""
    curva = curvas_a_mostrar(D["curva"], ref).assign(nombre=lambda d: d["solucion"].map(nombre_curva_legible))
    presentes = set(curva["nombre"])
    orden = [i for i, n in enumerate(E.CURVAS_NOMBRES) if n in presentes]                     # solo las curvas que se dibujan
    nombres, colores, rayas = ([lista[i] for i in orden] for lista in (E.CURVAS_NOMBRES, E.CURVAS_COLORES, E.CURVAS_RAYAS))
    marcas = [i / 10 for i in range(11)]
    x_enc = alt.X("presupuesto:Q", title="Fracción de cajas que se revisa", axis=alt.Axis(format="%", values=marcas), scale=alt.Scale(domain=[0, 1]))
    y_enc = alt.Y("recall:Q", title="% de cajas sin pareja encontradas", axis=alt.Axis(format="%", values=marcas), scale=alt.Scale(domain=[0, 1]))
    trazo = alt.Stroke("nombre:N", title=None, scale=alt.Scale(domain=nombres, range=colores), legend=None)
    raya = alt.StrokeDash("nombre:N", scale=alt.Scale(domain=nombres, range=rayas), legend=None)
    # Una banda por curva con su color FIJO (sin codificar «nombre»): si la banda codifica el mismo campo con legend=None, Vega-Lite fusiona las leyendas y borra la de las líneas (F19-B7).
    bandas = [alt.Chart(curva[curva["nombre"] == n]).mark_area(opacity=0.13, color=c).encode(x=x_enc, y=alt.Y("lo:Q"), y2="hi:Q") for n, c in zip(nombres, colores) if (curva["nombre"] == n).any()]
    linea = alt.Chart(curva).mark_line(strokeWidth=3).encode(x=x_enc, y=y_enc, stroke=trazo, strokeDash=raya)
    azar = alt.Chart(pd.DataFrame({"presupuesto": [0, 1], "recall": [0, 1], "nombre": "Revisar al azar"})).mark_line(strokeDash=[2, 4], color=E.TOKENS["texto_2"]).encode(x=x_enc, y=y_enc)
    etiqueta_azar = alt.Chart(pd.DataFrame({"presupuesto": [0.62], "recall": [0.56], "t": ["revisar al azar"]})).mark_text(color=E.TOKENS["texto_2"], angle=315, fontSize=12).encode(x="presupuesto:Q", y="recall:Q", text="t:N")
    propios = {"Dos pasos": ("cobertura_dos", 0.05), "Un paso": ("cobertura_uno", -0.06)}                # etiqueta directa de las dos curvas de la solución, un poco sobre y bajo la línea
    directas = []
    for n, c in zip(nombres, colores):
        if n in propios:
            d = curva[curva["nombre"] == n].sort_values("presupuesto")
            directas.append({"presupuesto": 0.68, "recall": float(np.interp(0.68, d["presupuesto"], d["recall"])) + propios[n][1], "t": n, "color": c})
    capas_dir = []
    if directas:
        capas_dir = [alt.Chart(pd.DataFrame(directas)).mark_text(align="left", fontSize=13, fontWeight="bold").encode(x="presupuesto:Q", y="recall:Q", text="t:N", color=alt.Color("color:N", scale=None, legend=None))]
    puntos_et = []                                                                           # etiqueta directa en la curva de referencia (nombre en texto neutro, marcador del color de la serie)
    for n, c in zip(nombres, colores):
        if n.endswith("(referencia)"):
            d = curva[curva["nombre"] == n].sort_values("presupuesto")
            puntos_et.append({"presupuesto": 0.3, "recall": float(np.interp(0.3, d["presupuesto"], d["recall"])), "t": n, "color": c})
    capas_et = []
    if puntos_et:
        df_et = pd.DataFrame(puntos_et)
        capas_et = [alt.Chart(df_et).mark_point(shape="diamond", size=90, filled=True).encode(x="presupuesto:Q", y="recall:Q", color=alt.Color("color:N", scale=None, legend=None)),
                    alt.Chart(df_et).mark_text(align="left", dx=9, dy=26, fontSize=12, color=E.TOKENS["texto_2"]).encode(x="presupuesto:Q", y="recall:Q", text="t:N")]
    # marca del presupuesto actual: regla vertical, un punto por flujo y la llamada con las cifras de las tarjetas
    pts = [{"presupuesto": presup, "recall": r["cobertura_dos"], "c": E.CURVAS_COLORES[0], "t": f"Dos pasos: {F.porcentaje(presup, 0)} → {F.de_cada_100(r['cobertura_dos'])}"},
           {"presupuesto": presup, "recall": r["cobertura_uno"], "c": E.CURVAS_COLORES[1], "t": f"Un paso: {F.porcentaje(presup, 0)} → {F.de_cada_100(r['cobertura_uno'])}"}]
    alto = max(r["cobertura_dos"], r["cobertura_uno"])
    llamada = COLA_LLAMADA.format(presupuesto=F.porcentaje(presup, 0), dos=F.de_cada_100(r["cobertura_dos"]), uno=F.entero(round(100 * r["cobertura_uno"])))
    derecha = presup > 0.5
    capas_marca = [alt.Chart(pd.DataFrame({"presupuesto": [presup], "y0": [0], "y1": [alto]})).mark_rule(strokeDash=[3, 4], color=E.TOKENS["texto_2"]).encode(x="presupuesto:Q", y="y0:Q", y2="y1:Q"),
                   alt.Chart(pd.DataFrame(pts)).mark_point(size=150, filled=True, stroke=E.TOKENS["texto"], strokeWidth=2).encode(x="presupuesto:Q", y="recall:Q", color=alt.Color("c:N", scale=None, legend=None), tooltip=[alt.Tooltip("t:N", title="")]),
                   alt.Chart(pd.DataFrame({"presupuesto": [presup], "recall": [min(alto + 0.1, 0.97)], "t": [llamada]})).mark_text(align="right" if derecha else "left", dx=-12 if derecha else 12, fontSize=13, fontWeight="bold", fill=E.TOKENS["texto"]).encode(x="presupuesto:Q", y="recall:Q", text="t:N")]
    _grafico(alt.layer(*bandas, linea, azar, etiqueta_azar, *capas_dir, *capas_et, *capas_marca).properties(height=340))


def _panel_detalle(ctx: dict[str, Any], t: pd.DataFrame, posicion: int, cola_total: int, extra: dict[str, str] | None = None) -> None:
    """Panel lateral de la caja elegida (F32): su identificación, la probabilidad grande, el anillo con su cámara, sus datos (incluidos fotogramas, tipo de caso y distancia) y el botón «Explicar esta caja →»."""
    d = detalle_caja(t, posicion, cola_total, ctx["rangos"], ctx["ciclistas"])
    fila = t.iloc[posicion - 1]
    with st.container(key="panel_detalle"):
        st.markdown(f"**Caja {fila['caja']}**")
        st.caption(f"Prioridad {F.entero(d['posicion'])} de {F.entero(d['cola_total'])}")
        activa = int(str(d["camara"])[0]) if str(d["camara"])[:1].isdigit() else None                    # la cámara que ve la caja se ilumina en el anillo
        anillo = E.anillo_camaras({c: ("activa" if c == activa else "apagada") for c in CAMARAS}, 96, "Cámara de la caja: " + str(d["camara"]))
        _html(f'<div class="aud-detalle-cabeza">{anillo}<div><p class="aud-probabilidad">{F.porcentaje(d["prob"])}</p><p class="aud-descripcion">probabilidad de no tener par en ninguna cámara</p></div></div>')
        filas = [("Segmento", "…" + str(d["segmento"])[-6:]), ("Cámara", d["camara"]), ("Clase", d["clase"]), ("Puntos del sensor superior", F.entero(d["puntos_sup"])), ("Puntos del LiDAR", F.entero(d["puntos"])),
                 ("Distancia", f"{F.decimal(d['distancia'], 1)} m"), ("Tipo de caso", d["tipo_caso"])]
        filas += list((extra or {}).items())
        datos = "".join(f"<dt>{E._e(k)}</dt><dd>{E._e(v)}</dd>" for k, v in filas)
        _html(f'<div class="aud-detalle-datos"><dl class="aud-datos">{datos}</dl></div>')
        if d["advertencia_ciclista"]:
            c = ctx["ciclistas"]
            _html('<div class="aud-aviso"><strong>Ciclista:</strong> la regla es poco confiable (' + F.porcentaje(c["ciclista"]) + " de los casos encontrados contra " + F.porcentaje(c["peaton"]) +
                  " en peatones). Conviene revisar con más cuidado.</div>")
        st.button(COLA_BOTON_EXPLICAR, key="explicar_caja", type="primary", width="stretch", on_click=_ir_a_explica, args=(valores_para_explicar(fila), str(fila["seg"]), str(fila["caja"]), int(posicion), "Cola de revisión"))


AYUDA_COLUMNAS = {COLUMNA_PROBABILIDAD: "Probabilidad calibrada de que la caja no tenga par en ninguna cámara", COLUMNA_PROBABILIDAD + " máxima": "Mayor probabilidad calibrada entre los fotogramas del objeto",
                  "Puntos sensor sup.": "Puntos del LiDAR superior dentro de la caja: cuantos menos puntos, más arriba queda la caja", "Clase": "En ciclistas la regla es poco confiable.", COLUMNA_FOTOGRAMAS: NOTA_FOTOGRAMAS}
# Las seis columnas que sirven para decidir (F23). El resto (distancia, segmento, identificadores) va al panel de detalle y al CSV.
COLUMNAS_COLA = ["Posición", COLUMNA_PROBABILIDAD, "Puntos sensor sup.", "Cámara", "Tipo de caso", "Clase"]
COLUMNAS_COLA_OBJETO = ["Mejor posición", COLUMNA_PROBABILIDAD + " máxima", COLUMNA_FOTOGRAMAS, "Cámara", "Tipo de caso", "Clase"]
ANCHOS_COLA = {"Prioridad": 74, COLUMNA_PROBABILIDAD: 112, COLUMNA_PROBABILIDAD + " máxima": 150, "Puntos sensor sup.": 126, COLUMNA_FOTOGRAMAS: 96, "Cámara": 104, "Clase": 78}


def _vista_cola(mostrada: pd.DataFrame, agrupar: bool) -> pd.DataFrame:
    """La tabla que se dibuja: las seis columnas de decisión, con «Posición» rotulada «Prioridad» y la clase en una palabra (la advertencia completa va en el detalle y bajo la tabla).

    Es solo una vista de ``mostrada`` (mismo orden, mismas filas); el CSV y la selección siguen usando la tabla completa.
    """
    cols = [c for c in (COLUMNAS_COLA_OBJETO if agrupar else COLUMNAS_COLA) if c in mostrada.columns]
    v = mostrada[cols].rename(columns={"Posición": "Prioridad", "Mejor posición": "Prioridad"})
    if "Clase" in v.columns:
        v["Clase"] = v["Clase"].map(lambda x: "Ciclista" if x == CLASE_ADVERTENCIA else x)
    return v


def _config_columnas_cola(tabla: pd.DataFrame) -> dict[str, Any]:
    """Configuración de columnas de la tabla de la cola: anchos fijos medidos para que a 1366 px entren las seis sin desplazamiento horizontal, ayuda y formato de enteros."""
    cfg: dict[str, Any] = {}
    for c in tabla.columns:
        ayuda = AYUDA_COLUMNAS.get(c)
        if c == "Prioridad" or c == COLUMNA_FOTOGRAMAS:
            cfg[c] = st.column_config.NumberColumn(c, format="%d", width=ANCHOS_COLA.get(c, 84), help=ayuda)
        elif c == "Tipo de caso":                          # sin ancho fijo: absorbe el espacio sobrante de las pantallas anchas y nunca queda por debajo de su contenido
            cfg[c] = st.column_config.TextColumn(c, help=ayuda)
        else:
            cfg[c] = st.column_config.TextColumn(c, width=ANCHOS_COLA.get(c, 110), help=ayuda if c in (COLUMNA_PROBABILIDAD, "Puntos sensor sup.") else None)
    return cfg


def _filas_elegidas(clave: str) -> list[int]:
    """Filas elegidas de una tabla con selección, según el estado de la ejecución anterior (para decidir el diseño antes de dibujar la tabla). Vacío si no hay."""
    try:
        return [int(i) for i in st.session_state[clave]["selection"]["rows"]]
    except (KeyError, TypeError, AttributeError):
        return []


def _pagina_anterior() -> None:
    st.session_state["cola_pagina"] = max(1, int(st.session_state.get("cola_pagina", 1)) - 1)


def _pagina_siguiente() -> None:
    st.session_state["cola_pagina"] = int(st.session_state.get("cola_pagina", 1)) + 1


def _lista_cola(ctx: dict[str, Any], r: dict[str, Any], tabla_t: pd.DataFrame, plan: tuple) -> None:
    """Pestaña «Cola de cajas»: filtros que solo afectan la lista, aviso de empate, tabla de 50 en 50 con detalle lateral, paginador y descarga."""
    D = ctx["D"]
    rangos = ctx["rangos"]
    cola_total = r["cajas_cola_total"]
    with st.container(key="cola_lista"):
        f1, f2, f3, f4 = st.columns([1.4, 1.5, 1.7, 1.3], vertical_alignment="bottom")
        segmento = f1.selectbox("Segmento", ["Todos", *sorted(tabla_t["seg"].unique())], key="segmento_cola", format_func=lambda s: s if s == "Todos" else "…" + str(s)[-6:])
        clases = f2.multiselect("Clase", [CLASE_NORMAL.split(":")[0], "Ciclista"], key="filtro_clase", placeholder="Todas")
        camaras = f3.multiselect("Cámara", list(CAMARAS.values()), key="filtro_camara", placeholder="Todas")
        agrupar = f4.toggle("Agrupar por objeto", key="agrupar_objeto", help="Una fila por objeto con su mejor posición. Es solo una vista: el número de cajas a revisar no cambia.")
        aviso = aviso_empate(r["top"])                                                       # el empate lo define el orden de la regla (el de ``cola_segmento``)
        if aviso:
            _html(f'<p class="aud-banner">{E._e(aviso)}</p>')
        # ---- vista: una fila por caja (o por objeto) con los filtros aplicados
        if agrupar:
            vista = tabla_por_objeto(tabla_t, rangos, max_filas=len(tabla_t))
            vista = filtrar_cola(vista, [CLASE_ADVERTENCIA if c == "Ciclista" else CLASE_NORMAL for c in clases], camaras)
            if segmento != "Todos" and "Segmento" in vista.columns:
                vista = vista[vista["Segmento"] == segmento]
            col_pos, unidad = "Mejor posición", "objetos"
        else:
            mask = pd.Series(True, index=tabla_t.index)
            if clases:
                mask &= tabla_t["clase"].isin(clases)
            if camaras:
                mask &= tabla_t["camara"].isin(camaras)
            if segmento != "Todos":
                mask &= tabla_t["seg"] == segmento
            vista = tabla_t[mask]
            col_pos, unidad = "Posición", "cajas"
        firma = (plan, segmento, tuple(clases), tuple(camaras), bool(agrupar))
        if firma != st.session_state.get("_firma_cola"):                                      # cambió el plan o un filtro: vuelve a la primera página y se suelta la selección
            st.session_state["_firma_cola"] = firma
            st.session_state["cola_pagina"] = 1
            st.session_state.pop("tabla_cola", None)
        n = len(vista)
        filtrado = bool(clases or camaras or segmento != "Todos")
        st.caption((f"Filtrado: {F.entero(n)} {unidad} de {F.entero(len(tabla_t))} cajas de la cola. " if filtrado else "") + "Las cifras de arriba no cambian con los filtros." + (" " + NOTA_AGRUPADO if agrupar else ""))
        pag = pagina_cola(n, st.session_state.get("cola_pagina", 1))
        if pag["pagina"] != st.session_state.get("cola_pagina"):
            st.session_state["cola_pagina"] = pag["pagina"]
            st.session_state.pop("tabla_cola", None)
        if n == 0:
            _html(E.vacio("Ninguna caja cumple los filtros", "Quite una clase, una cámara o el segmento para volver a ver la cola."))
            return
        elegidas = _filas_elegidas("tabla_cola")
        con_detalle = bool(elegidas) and elegidas[0] < pag["fin"] - pag["ini"]
        izq, der = st.columns([2.15, 1], gap="medium") if con_detalle else (st.container(), None)       # sin selección, la tabla ocupa todo el ancho y el panel no ocupa espacio
        with izq:
            if agrupar:
                mostrada = vista.iloc[pag["ini"]:pag["fin"]].reset_index(drop=True)
                for ident in ("Marca de tiempo", "Objeto"):                                   # identificadores: texto, sin separador de miles
                    if ident in mostrada.columns:
                        mostrada[ident] = mostrada[ident].astype(str)
                tabla = _vista_cola(mostrada, True)
                evento = st.dataframe(tabla, key="tabla_cola", on_select="rerun", selection_mode="single-row", hide_index=True, width="stretch", row_height=30, height=min(40 + 31 * len(tabla), 410),
                                      column_config=_config_columnas_cola(tabla))
                st.caption(NOTA_AGRUPADO)
            else:
                pagina_df = vista.iloc[pag["ini"]:pag["fin"]]
                tabla = pd.DataFrame({"Prioridad": [int(i) + 1 for i in pagina_df.index], "Segmento": ["…" + s[-6:] for s in pagina_df["seg"]], "Caja": pagina_df["caja"].to_numpy(),
                                      "Cámara": pagina_df["camara"].to_numpy(), "Clase": [clase_con_etiqueta(c) for c in pagina_df["clase"]],
                                      COLUMNA_PROBABILIDAD: [F.porcentaje(v, 1) for v in pagina_df["prob_cal"]], "Puntos sensor sup.": [F.entero(v) for v in pagina_df["num_top_lidar_points"]]})
                evento = st.dataframe(tabla, key="tabla_cola", on_select="rerun", selection_mode="single-row", hide_index=True, width="stretch", row_height=30, height=38 + 30 * len(tabla) + 3,                  # las filas de la página caben enteras (sin desplazamiento interno)
                                      column_config={"Prioridad": st.column_config.NumberColumn(format="%d", width=72, help=AYUDA_COLUMNAS.get("Prioridad")), "Segmento": st.column_config.TextColumn(width=82),
                                                     "Caja": st.column_config.TextColumn(width=76), "Cámara": st.column_config.TextColumn(width=118), "Clase": st.column_config.TextColumn(),
                                                     COLUMNA_PROBABILIDAD: st.column_config.TextColumn(width=94, help=AYUDA_COLUMNAS[COLUMNA_PROBABILIDAD]), "Puntos sensor sup.": st.column_config.TextColumn(width=100, help=AYUDA_COLUMNAS["Puntos sensor sup."])})
            filas = list(evento.selection.rows) if evento is not None and getattr(evento, "selection", None) is not None else []
            # ---- paginador y descarga
            q1, q2, q3, q4, q5 = st.columns([2.2, 1.15, 1.15, 0.9, 1.9], vertical_alignment="center")
            q1.caption(f"Mostrando {F.entero(pag['desde'])} a {F.entero(pag['hasta'])} de {F.entero(n)} {unidad}" + (f" · página {F.entero(pag['pagina'])} de {F.entero(pag['paginas'])}" if pag["paginas"] > 1 else ""))
            if pag["paginas"] > 1:
                q2.button("Anterior", key="pag_anterior", on_click=_pagina_anterior, disabled=pag["pagina"] <= 1, width="stretch")
                q3.button("Siguiente", key="pag_siguiente", on_click=_pagina_siguiente, disabled=pag["pagina"] >= pag["paginas"], width="stretch")
                q4.number_input("Página", min_value=1, max_value=pag["paginas"], step=1, key="cola_pagina", label_visibility="collapsed")
            if agrupar:
                def datos_csv() -> bytes:
                    return vista.head(MAX_FILAS_COLA).to_csv(index=False).encode("utf-8")
            else:
                def datos_csv() -> bytes:                                                    # se arma al pulsar «Descargar» (la tabla completa de la cola puede tener decenas de miles de filas)
                    completa = tabla_cola(tabla_t, cola_total, rangos, max_filas=len(tabla_t))               # misma tabla de siempre (todas sus columnas)
                    return completa.loc[vista.index].head(MAX_FILAS_COLA).to_csv(index=False).encode("utf-8")        # solo las filas del filtro, hasta 500
            q5.download_button("Descargar la cola (CSV)", datos_csv, "cola_de_revision.csv", "text/csv", icon=":material/download:", width="stretch")
        if der is not None:
            with der:
                if filas and filas[0] < len(tabla):
                    if agrupar:
                        fila_g = mostrada.iloc[filas[0]]
                        _panel_detalle(ctx, tabla_t, int(fila_g[col_pos]), cola_total, {"Fotogramas del objeto": F.entero(fila_g[COLUMNA_FOTOGRAMAS])} if COLUMNA_FOTOGRAMAS in mostrada.columns else None)
                    else:
                        fila_t = pagina_df.iloc[filas[0]]
                        n_fotogramas = int(((tabla_t["seg"] == fila_t["seg"]) & (tabla_t["key.laser_object_id"] == fila_t["key.laser_object_id"])).sum())      # filas de la cola que son del mismo objeto
                        _panel_detalle(ctx, tabla_t, int(pagina_df.index[filas[0]]) + 1, cola_total, {"Fotogramas del objeto en la cola": F.entero(n_fotogramas)})


def cola(ctx: dict[str, Any]) -> None:
    """Cola de revisión (paso 2), rediseñada en F32: plan arriba (cambia todas las cifras), tres tarjetas, «Cola de cajas» primero y la curva en la segunda pestaña, y los supuestos plegados al final."""
    D, K = ctx["D"], ctx["K"]
    encabezado("Cola de revisión", DESCRIPCION_PAGINA["Cola de revisión"])
    sol = K.get("nombre_curva", "solucion")
    st.session_state.setdefault("presupuesto", 20)
    st.session_state.setdefault("objetivo", 80)
    with st.container(key="plan_revision"):
        c2, c3, c4, c5 = st.columns([2.3, 1.7, 2.6, 1.2], vertical_alignment="bottom")
        flujo_txt = c2.selectbox("Flujo", list(FLUJOS), index=1, key="flujo_cola", help="Un paso: se ordenan todas las cajas. Dos pasos: primero se auditan las celdas marcadas y la cola ordena el resto (en muestra).")
        flujo = FLUJOS[flujo_txt]
        sol_flujo = sol if flujo == "dos" or not (D["curva"]["solucion"] == CURVA_UN_PASO).any() else CURVA_UN_PASO
        modo = c3.radio("Decidir por", [MODO_PRESUPUESTO, MODO_OBJETIVO], horizontal=True, key="modo_cola", help="Presupuesto: se fija qué porcentaje de la cola se revisa. Meta: se fija qué porcentaje de las cajas sin pareja se quiere encontrar.")
        if modo == MODO_PRESUPUESTO:
            presup = c4.slider("Presupuesto (% de la cola)", 1, 100, key="presupuesto", format="%d") / 100
        else:
            objetivo = c4.slider("Meta (% de las cajas sin pareja)", 10, 99, key="objetivo", format="%d") / 100
            presup = round(curva_inversa(D["curva"], sol_flujo, objetivo), 3)
        c5.button("Volver al 20 %", on_click=_volver_a_20, width="stretch")
    segundos = st.session_state.get("segundos", SUPUESTO_SEGUNDOS)
    st.session_state["_plan_cola"] = {"presupuesto": presup, "flujo": flujo}                 # «Explica una caja» lee el mismo presupuesto y flujo que esta página
    r = resumen_cola(D["cajas"], D["curva"], sol, "Todos", presup, segundos, flujo)
    if modo == MODO_OBJETIVO:
        st.caption(f"Para encontrar {F.porcentaje(objetivo, 0)} habría que revisar {F.porcentaje(presup, 0)} de la cola (según la curva guardada del flujo elegido).")
    _html(E.indicadores(tarjetas_cola(r, segundos)))
    tabla_t = preparar_cola(r["top"], D["cajas"], ctx["rangos"])
    tab_lista, tab_curva = st.tabs([COLA_TAB_LISTA, COLA_TAB_CURVA])
    with tab_lista:
        _lista_cola(ctx, r, tabla_t, (flujo, round(presup, 3)))
    with tab_curva:
        h1, h2 = st.columns([3, 1.1], vertical_alignment="top")
        h1.markdown(f'<p class="aud-card-t">{E._e(COLA_TITULO_CURVA)}</p><p class="aud-card-a">Con el {F.porcentaje(presup, 0)} de la cola revisado, el flujo en dos pasos encuentra unas {F.de_cada_100(r["cobertura_dos"])} (en muestra).</p>', unsafe_allow_html=True)
        refs = [x for x in REFERENCIAS if D["curva"]["solucion"].str.startswith(x).any()]
        ref = h2.selectbox("Comparar con", ["Ninguno", *refs], key="ref_curva") if refs else "Ninguno"
        if ref != "Ninguno":
            er = recall_en_presupuesto(D["curva"], f"{ref} (referencia), un paso (A)", presup)
            st.caption(f"{ref} como referencia (un paso, validación cruzada por segmentos): unas {F.de_cada_100(er['recall'])} con el mismo porcentaje (intervalo {F.porcentaje(er['lo'], 0)} a {F.porcentaje(er['hi'], 0)}). No se eligió por simplicidad; ver Validación.")
        _grafico_cobertura(D, r, presup, ref)
        st.caption(COLA_NOTA_BANDA.format(n=F.entero(r["n_segmentos"])))
    with st.expander(COLA_SUPUESTOS):
        st.number_input("Segundos por revisión de una caja (supuesto, no medido)", min_value=1, max_value=600, value=SUPUESTO_SEGUNDOS, step=5, key="segundos")
        lines = [f"- **Segundos por caja:** {F.entero(segundos)} s es un supuesto, no una medición."]
        if r["todos"]:
            lines.append(f"- **Intervalo de confianza (95 %, remuestreando segmentos):** dos pasos {F.porcentaje(r['ic_dos'][0], 0)} a {F.porcentaje(r['ic_dos'][1], 0)}; solo cola {F.porcentaje(r['ic_uno'][0], 0)} a {F.porcentaje(r['ic_uno'][1], 0)}.")
        lines.append("- **En muestra:** " + AVISO_EN_MUESTRA)
        c = ctx["ciclistas"] or {}
        if all(isinstance(c.get(k), float) and c[k] == c[k] for k in ("ciclista", "peaton")):
            lines.append(f"- **Ciclistas:** la regla es poco confiable: encuentra {F.porcentaje(c['ciclista'])} de los casos, contra {F.porcentaje(c['peaton'])} en peatones.")
        lines.append("- **Qué se mide:** el porcentaje de la cola se calcula sobre el total de cajas en un paso y sobre la cola de celdas sanas en dos pasos; las celdas marcadas se auditan aparte.")
        st.markdown("\n".join(lines))


# ------------------------------------------------------------------------------------------------------------ Explica una caja
DEFECTO_CAJA = {"ex_top": 50, "ex_pts": 60, "ex_dist": 25.0, "ex_clase": "Peatón"}          # los valores con que abre la página desde siempre


def _aplicar_ejemplo() -> None:
    """Al elegir un ejemplo (o la caja de la cola) los controles toman sus valores; al volver a pulsar el elegido se suelta y los controles quedan como están."""
    nombre = st.session_state.get("ex_ejemplo")
    if nombre in EJEMPLOS_CAJA:
        e = EJEMPLOS_CAJA[nombre]
        st.session_state.update({"ex_pts": e["pts"], "ex_top": e["top"], "ex_dist": e["dist"], "ex_clase": e["clase"]})
    elif nombre and st.session_state.get("_explica_origen"):
        st.session_state.update(st.session_state["_explica_origen"]["ajustado"])


def _soltar_ejemplo() -> None:
    """Mover cualquier control deja de ser «el ejemplo»: el botón se suelta y el aviso de la caja de la cola desaparece."""
    st.session_state["ex_ejemplo"] = None


def _restablecer_caja() -> None:
    st.session_state.update({**DEFECTO_CAJA, "ex_ejemplo": None})


def explica(ctx: dict[str, Any]) -> None:
    """Explica una caja (herramienta), rediseñada en F33: ejemplos como botones, un solo control que decide (separado de los que solo describen), resultado y veredicto primero, lugar en una barra,
    cuatro pasos con valores vivos, gráfico con rótulos directos y «Cajas parecidas»."""
    D = ctx["D"]
    encabezado("Explica una caja", DESCRIPCION_PAGINA["Explica una caja"])
    try:
        art = ctx["artefactos"]()
    except FileNotFoundError:
        st.error("Falta la solución congelada, así que esta página no puede calcular. Avise a quien mantiene la página.")
        return
    from waymo_evaluacion.ep3.inferencia import V16

    ref = D["cajas"]
    base = ref[V16].median().to_frame().T
    pa = int(-art.umbrales["A"])                                                          # puntos del umbral que busca el 80 % de las cajas sin pareja (solución congelada)
    plan = st.session_state.get("_plan_cola", {"presupuesto": 0.2, "flujo": "dos"})        # el presupuesto y el flujo de la Cola (20 % y dos pasos por defecto)
    presup, flujo = float(plan["presupuesto"]), plan["flujo"]
    cola_ref = referencia_cola(ref, flujo)
    pb = umbral_presupuesto(cola_ref, presup)["puntos"]                                     # puntos del último lugar que entra: de la cola real, no fijo
    opciones = opciones_puntos((pa, pb))

    def cerca(v: float) -> int:
        return min(opciones, key=lambda o: abs(o - v))

    pendiente = st.session_state.pop("_explica_caja", None)
    if pendiente:                                                                           # viene de «Abrir» (Resumen) o de «Explicar esta caja →» (Cola): los controles toman el valor de esa caja
        ajustado = {"ex_top": cerca(pendiente["top"]), "ex_pts": cerca(pendiente["pts"]), "ex_dist": float(min(max(round(pendiente["dist"]), 1), 100)), "ex_clase": pendiente["clase"]}
        st.session_state["_explica_origen"] = {**pendiente, "ajustado": ajustado}
        st.session_state.update({**ajustado, "ex_ejemplo": EXP_ETIQUETA_COLA.format(caja=pendiente["caja"])})
    origen = st.session_state.get("_explica_origen")
    etiqueta_cola = EXP_ETIQUETA_COLA.format(caja=origen["caja"]) if origen else None
    botones = ([etiqueta_cola] if etiqueta_cola else []) + list(EJEMPLOS_CAJA)
    if st.session_state.get("ex_ejemplo") not in botones:
        st.session_state["ex_ejemplo"] = None
    for k, v in DEFECTO_CAJA.items():
        st.session_state.setdefault(k, v)
    # ejemplos: botones de selección (el elegido queda marcado)
    st.pills("Ejemplos", botones, selection_mode="single", key="ex_ejemplo", on_change=_aplicar_ejemplo)
    if origen and st.session_state.get("ex_ejemplo") == etiqueta_cola:
        a1, a2 = st.columns([4, 1], vertical_alignment="center")
        a1.markdown(f'<p class="aud-banner">{E._e(EXP_AVISO_ORIGEN.format(origen=("el Resumen" if origen["origen"] == "Resumen" else "la Cola de revisión"), caja=origen["caja"], prioridad=F.entero(origen["prioridad"])))}</p>', unsafe_allow_html=True)
        a2.page_link(ARCHIVO_PAGINA[origen["origen"]], label=EXP_ENLACE_VOLVER.format(destino="el Resumen" if origen["origen"] == "Resumen" else "la cola"))
    izq, der = st.columns([1, 1.7], gap="large")
    with izq, st.container(key="ex_datos"):
        st.markdown('<p class="aud-card-t">Datos de la caja</p>', unsafe_allow_html=True)
        _html(E.rotulo_control("Puntos del sensor superior", "decide la cola"))
        top_pts = st.select_slider("Puntos del sensor superior", options=opciones, key="ex_top", format_func=F.entero, label_visibility="collapsed", on_change=_soltar_ejemplo)
        st.caption("Escala comprimida: cada paso multiplica los puntos.")
        _html(E.rotulo_control("Para describir el tipo de caso", "no cambia el lugar", "m"))
        pts = st.select_slider("Puntos del LiDAR en la caja", options=opciones, key="ex_pts", format_func=F.entero, on_change=_soltar_ejemplo)
        dist = st.slider("Distancia al sensor, en m", 1.0, 100.0, step=1.0, format="%d", key="ex_dist", on_change=_soltar_ejemplo)      # sin «25.00» con punto decimal: la página usa es-CL
        clase = st.radio("Clase", ["Peatón", "Ciclista"], horizontal=True, key="ex_clase", on_change=_soltar_ejemplo)
        if clase == "Ciclista":
            c = ctx["ciclistas"]
            if all(isinstance(c.get(k), float) and c[k] == c[k] for k in ("ciclista", "peaton", "positivos", "segmentos")):
                _html('<div class="aud-aviso"><strong>' + EXP_AVISO_CICLISTA.format(etiqueta=ETIQUETA_CICLISTA) + '</strong> Encuentra ' + F.porcentaje(c["ciclista"]) + " de los casos sin pareja, contra " + F.porcentaje(c["peaton"]) +
                      " en peatones (" + F.entero(c["positivos"]) + " casos en " + F.entero(c["segmentos"]) + " segmentos).</div>")
            else:
                _html('<div class="aud-aviso"><strong>' + EXP_AVISO_CICLISTA.format(etiqueta=ETIQUETA_CICLISTA) + '</strong> Conviene revisar estas cajas con más cuidado.</div>')
        st.button("Restablecer", key="ex_restablecer", on_click=_restablecer_caja)
    fila = base.copy()
    fila["num_lidar_points"], fila["num_top_lidar_points"], fila["distancia_m"] = pts, top_pts, dist
    fila["densidad_puntos"] = pts / fila["volumen_caja"]
    if "es_ciclista" in fila.columns:
        fila["es_ciclista"] = 1 if clase == "Ciclista" else 0
    s = float(art.puntuador.puntuar(fila)[0])
    p = float(art.calibrador.calibrar(np.array([s]))[0]) if art.calibrador is not None else float("nan")
    v = veredicto_caja(s, cola_ref, presup)
    texto_ver, detalle_ver = textos_veredicto(v, presup)
    valor_lugar, frase_lugar = texto_lugar(v)
    with der:
        with st.container(key="ex_resultado"):                                              # el resultado primero: la probabilidad y qué pasaría con esta caja
            r1, r2 = st.columns([1, 1.2], vertical_alignment="center")
            r1.markdown(f'<p class="aud-prob-grande">{F.porcentaje(p)}</p><p class="aud-descripcion">probabilidad estimada de no tener pareja en ninguna cámara</p>', unsafe_allow_html=True)
            r2.markdown(E.veredicto(texto_ver, v["entra"]) + f'<p class="aud-descripcion">{E._e(detalle_ver)}</p>', unsafe_allow_html=True)
            _html(E.barra_lugar("Lugar en la cola", valor_lugar, presup, (v["fraccion_empate"] / 2) if v["empatada"] else v["posicion"],
                                f"zona sombreada: se revisa (presupuesto {F.porcentaje(presup, 0)})"))
            st.caption(frase_lugar + " El presupuesto se fija en la Cola de revisión.")
        with st.container(key="ex_pasos"):
            st.markdown('<p class="aud-card-t">Cómo se calcula</p>', unsafe_allow_html=True)
            valores_pasos = (f"{F.entero(top_pts)} {'punto' if top_pts == 1 else 'puntos'}", F.entero(s), F.porcentaje(p), valor_lugar)
            _html(E.pasos_calculo(list(zip(EXP_PASOS, valores_pasos, EXP_PASOS_DETALLE))))
        with st.container(key="ex_curva"):
            st.markdown('<p class="aud-card-t">Cómo baja la probabilidad al subir los puntos</p><p class="aud-card-a">Mientras más puntos del sensor superior, más probable es que la caja tenga pareja.</p>', unsafe_allow_html=True)
            valores = np.unique(np.concatenate([np.array(opciones, dtype=float), np.round(np.geomspace(1, 2000, 70))]))
            dep = curva_dependencia(art.puntuador, fila, "num_top_lidar_points", valores)
            dep["prob"] = art.calibrador.calibrar(dep["score"].to_numpy(dtype=float)) if art.calibrador is not None else np.nan
            marcas = [0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]
            x_enc = alt.X("num_top_lidar_points:Q", scale=alt.Scale(type="symlog", constant=1, domain=[0, 2000]), title="Puntos del sensor superior (escala comprimida)",
                          axis=alt.Axis(values=marcas, labelExpr="replace(format(datum.value, ','), ',', '.')"))
            y_enc = alt.Y("prob:Q", title="Probabilidad de no tener pareja", scale=alt.Scale(domain=[0, 1.25]), axis=alt.Axis(format="%", values=[0, 0.2, 0.4, 0.6, 0.8, 1.0]))       # la banda de arriba queda libre para los rótulos de las dos líneas
            marca = pd.DataFrame({"num_top_lidar_points": [top_pts], "prob": [p], "t": [f"Esta caja: {F.porcentaje(p)}"]})
            reglas = pd.DataFrame({"num_top_lidar_points": [pb, pa], "t": [EXP_ROTULO_REVISA, EXP_ROTULO_80], "u": [f"{F.porcentaje(presup, 0)} de la cola · ≤ {F.entero(pb)} puntos", f"≤ {F.entero(pa)} puntos"]})
            izq_r, der_r = reglas.iloc[[0]], reglas.iloc[[1]]
            capas = [alt.Chart(dep).mark_line(strokeWidth=3, color=E.TOKENS["acento"]).encode(x=x_enc, y=y_enc),
                     alt.Chart(reglas).mark_rule(color=GRIS_GRAFICO, strokeWidth=1, strokeDash=[3, 3]).encode(x=x_enc),
                     alt.Chart(izq_r).mark_text(align="right", dx=-6, baseline="top", fontSize=12.5, fontWeight="bold", color=E.TOKENS["texto"]).encode(x=x_enc, y=alt.value(4), text="t:N"),
                     alt.Chart(izq_r).mark_text(align="right", dx=-6, baseline="top", fontSize=12, color=E.TOKENS["texto_2"]).encode(x=x_enc, y=alt.value(20), text="u:N"),
                     alt.Chart(der_r).mark_text(align="left", dx=6, baseline="top", fontSize=12.5, fontWeight="bold", color=E.TOKENS["texto"]).encode(x=x_enc, y=alt.value(4), text="t:N"),
                     alt.Chart(der_r).mark_text(align="left", dx=6, baseline="top", fontSize=12, color=E.TOKENS["texto_2"]).encode(x=x_enc, y=alt.value(20), text="u:N"),
                     alt.Chart(marca).mark_point(size=150, filled=True, color=E.TOKENS["texto"], stroke=E.TOKENS["acento"], strokeWidth=2).encode(x=x_enc, y=y_enc, tooltip=[alt.Tooltip("t:N", title="")]),
                     alt.Chart(marca).mark_text(align="left" if top_pts < 300 else "right", dx=12 if top_pts < 300 else -12, dy=-14, fontSize=13, fontWeight="bold", color=E.TOKENS["texto"]).encode(x=x_enc, y=y_enc, text="t:N")]
            _grafico(alt.layer(*capas).properties(height=270))
            st.caption("Las demás variables quedan en la mediana de los datos. Es una ilustración del modelo, no una explicación causal.")
        with st.container(key="ex_tipo"):
            st.markdown('<p class="aud-card-t">Cajas parecidas</p>', unsafe_allow_html=True)
            ns = ctx["no_sup"]()
            if ns is not None:
                info = info_tipo_de_caso(tipo_de_caso(fila.copy(), ns), D["clusters"])
                st.markdown(f"**Tipo de caso:** {info['tipo_de_caso']}")
                st.markdown(F.sin_corte(f"En los 41 segmentos, ese tipo de caso tuvo {F.porcentaje(info['tasa'])} de cajas sin pareja (intervalo 95 % por segmentos: {F.porcentaje(info['ic_lo'])} a {F.porcentaje(info['ic_hi'])}; {F.entero(info['cajas'])} cajas)."))
                st.caption("Es una descripción (post hoc) y no mejora la predicción de la regla.")
            else:
                st.caption("No hay modelo de tipos de caso en este equipo.")
    with st.expander("Notas del modelo"):
        st.markdown(f"- Las dos marcas del gráfico son umbrales de la cola: con {F.entero(pb)} puntos o menos se revisa el {F.porcentaje(presup, 0)} de las cajas (el presupuesto de la Cola); con {F.entero(pa)} puntos o menos se busca encontrar el 80 % de las cajas sin pareja.\n"
                    f"- Las primeras {F.entero(empatadas_arriba(cola_ref))} cajas tienen {F.entero(v['puntos_empate'])} puntos y empatan en la prioridad máxima.\n"
                    "- Todas las cifras son en muestra (41 segmentos, sin prueba ciega).")


# ------------------------------------------------------------------------------------------------------------ Auditoría de cámaras
def _mapa_calor(m: pd.DataFrame, orden: list[str], solo_datos: bool, marcada: pd.DataFrame | None = None) -> alt.LayerChart:
    """Mapa de calor segmento × cámara de las filas que se le pasan (``orden`` es el orden de arriba hacia abajo; la celda ``marcada`` se contorna). El eje usa el segmento completo (sus 6 últimos dígitos
    solo en la etiqueta), así que dos segmentos con el mismo final no se mezclan."""
    n_seg = len(orden)
    rotulos = [f"{c} · {CAMARAS[c].split('(')[1].rstrip(')')}" for c in CAMARAS]
    x = alt.X("camara_rotulo:N", title=None, sort=rotulos, axis=alt.Axis(labelAngle=0, orient="top", labelFontSize=12, labelLimit=140))
    y = alt.Y("seg:N", title="Segmento (6 últimos dígitos)", sort=orden, axis=alt.Axis(labelOverlap=False, labelFontSize=11, labelExpr="'…' + slice(datum.value, -6)"))
    base = alt.Chart(m).encode(x=x, y=y)
    tip = [alt.Tooltip("seg:N", title="Segmento"), alt.Tooltip("camara:N", title="Cámara"), alt.Tooltip("pares:N", title="Cajas con pareja"), alt.Tooltip("cajas_rango:N", title="Cajas en el rango"), alt.Tooltip("estado:N", title="Estado")]
    sep = E.TOKENS["fondo"]                                                                      # una línea del color del lienzo separa las celdas
    capas = [base.transform_filter(~alt.datum.sin_datos).mark_rect(stroke=sep, strokeWidth=1.5).encode(
        color=alt.Color("tasa:Q", scale=alt.Scale(domain=[0, 1], range=E.RAMPA_SANA), legend=None), tooltip=tip)]
    if not solo_datos:                                                                           # «sin datos»: gris plano y neutro, sin rayado ni color de alerta
        capas += [base.transform_filter(alt.datum.sin_datos).mark_rect(fill=E.TOKENS["sin_datos"], stroke=sep, strokeWidth=1.5).encode(tooltip=tip)]
    capas += [base.transform_filter(alt.datum.hueco).mark_rect(fill=E.TOKENS["hueco_fondo"], stroke=E.TOKENS["hueco"], strokeWidth=3), base.transform_filter(alt.datum.hueco).mark_text(text="X", color=E.TOKENS["hueco"], fontSize=13, fontWeight="bold")]
    if marcada is not None and not marcada.empty:                                                # la celda de la fila elegida: contorno de acento
        capas += [alt.Chart(marcada).encode(x=x, y=y).mark_rect(fill="transparent", stroke=E.TOKENS["acento"], strokeWidth=3.5)]
    alto_fila = 24 if n_seg <= 15 else 16                                                        # con pocas filas, celdas más altas; con muchas, 16 px y sin desplazamiento interno
    return alt.layer(*capas).properties(height=alto_fila * max(n_seg, 1))


def auditoria(ctx: dict[str, Any]) -> None:
    """Auditoría de cámaras (paso 1), rediseñada en F31: franja de resumen, UNA tabla de celdas marcadas con el anillo al lado, mapa con las filas peores y la definición de hueco plegada."""
    D = ctx["D"]
    la = D["lista_A"]
    min_cajas = ctx.get("min_cajas", 100)
    frac = ctx.get("frac_hueco", 0.25)
    m_total = matriz_calor(D["celdas"], min_cajas)
    celdas = celdas_marcadas_lista(la)
    res = resumen_auditoria(m_total, la)
    encabezado("Auditoría de cámaras", AUD_DEFINICION.format(frac=F.porcentaje(frac, 0)))
    desde_resumen = False
    pendiente = st.session_state.pop("_auditoria_celda", None)
    if pendiente:                                                                                # viene de «Auditar» en el Resumen: esa fila ya viene elegida (antes de crear la tabla)
        idx0 = next((i for i, c in enumerate(celdas) if c["segmento"] == pendiente["segmento"] and c["camara"] == pendiente["camara"]), 0)
        st.session_state["aud_idx"], st.session_state["aud_desde_resumen"] = idx0, True
        st.session_state["tabla_celdas"] = {"selection": {"rows": [idx0], "columns": [], "cells": []}}
    # ---- franja de resumen y botón hacia la cola
    k_izq, k_der = st.columns([3, 1], gap="medium", vertical_alignment="top")
    with k_izq:
        _html(E.indicadores([
            {"clave": "celdas", "etiqueta": "Celdas marcadas", "valor": F.entero(res["celdas_marcadas"]), "sufijo": f"de {F.entero(res['celdas_total'])}", "nota": "segmento × cámara con hueco", "tono": "hueco" if res["celdas_marcadas"] else ""},
            {"clave": "afectadas", "etiqueta": "Cajas afectadas", "valor": F.entero(res["cajas_afectadas"]), "nota": "se atienden aparte de la cola"},
            {"clave": "sin_pareja", "etiqueta": "Sin pareja entre ellas", "valor": F.entero(res["sin_pareja"]), "sufijo": f"({F.porcentaje(res['pct_sin_pareja'], 0)})" if res["cajas_afectadas"] else "",
             "nota": f"de las {F.entero(res['cajas_afectadas'])} cajas afectadas"}]))
    with k_der, st.container(key="ir_cola"):
        st.page_link(ARCHIVO_PAGINA["Cola de revisión"], label=ENLACE_COLA_DESDE_AUDITORIA)
    st.markdown(f"**{titular_auditoria(res['celdas_marcadas'])}**")
    st.caption(AUD_NOTA_DESARROLLO.format(n=F.entero(res["segmentos"])))
    # ---- tabla de celdas marcadas y anillo
    izq, der = st.columns([2.2, 1], gap="large", vertical_alignment="top")
    idx = min(int(st.session_state.get("aud_idx", 0)), max(len(celdas) - 1, 0))
    with izq, st.container(key="aud_celdas"):
        c1, c2 = st.columns([3, 1], vertical_alignment="top")
        c1.markdown(f'<p class="aud-card-t">{E._e(AUD_TITULO_TABLA)}</p><p class="aud-card-a">{E._e(AUD_AYUDA_TABLA)}</p>', unsafe_allow_html=True)
        pres = lista_A_presentable(la)
        c2.download_button("Descargar CSV", pres.to_csv(index=False).encode("utf-8"), "celdas_marcadas.csv", "text/csv", icon=":material/download:", width="stretch")
        aviso = st.empty()
        if celdas:
            tabla = tabla_celdas_auditoria(celdas).assign(**{"Cajas afectadas": lambda d: d["Cajas afectadas"].map(F.entero), "Sin pareja": lambda d: d["Sin pareja"].map(F.entero)})      # miles con punto (es-CL)
            if "tabla_celdas" not in st.session_state:                                             # la primera fila viene elegida (resaltada), como en la referencia
                st.session_state["tabla_celdas"] = {"selection": {"rows": [idx], "columns": [], "cells": []}}
            evento = st.dataframe(tabla, key="tabla_celdas", on_select="rerun", selection_mode="single-row", hide_index=True, width="stretch", row_height=34, height=min(38 + 34 * len(tabla), 340))
            filas = list(evento.selection.rows) if evento is not None and getattr(evento, "selection", None) is not None else []
            if filas and filas[0] < len(celdas):
                idx = filas[0]
                if idx != st.session_state.get("aud_idx"):
                    st.session_state["aud_desde_resumen"] = False
                st.session_state["aud_idx"] = idx
            desde_resumen = bool(st.session_state.get("aud_desde_resumen"))
            c = celdas[idx]
            aviso.markdown(f'<p class="aud-banner" role="status">{E._e(AUD_AVISO_CELDA.format(segmento=chr(8230) + c["seg_corto"], camara=c["camara_num"], nombre=c["camara_nombre"], origen=AUD_ORIGEN_RESUMEN if desde_resumen else AUD_ORIGEN_FILA))}</p>', unsafe_allow_html=True)
        else:
            _html(E.vacio("Sin celdas marcadas", "No hay celdas marcadas en los datos cargados."))
    with der, st.container(key="aud_anillo"):
        estados, cuenta = _estados_camaras(la)
        _html(E.tarjeta_anillo_vertical(AUD_TITULO_ANILLO, _texto_camaras(cuenta), estados, 190, resaltar=celdas[idx]["camara_num"] if celdas else None))
    # ---- mapa de calor: las filas peores primero
    with st.container(key="aud_mapa"):
        st.markdown(f'<p class="aud-card-t">{E._e(AUD_TITULO_MAPA)}</p><p class="aud-card-a">{E._e(AUD_AYUDA_MAPA)}</p>', unsafe_allow_html=True)
        g1, g2, g3 = st.columns([1.2, 1.4, 1.4], vertical_alignment="bottom")
        grupo = g1.selectbox("Grupo de segmentos", ["todos", "train", "test"], format_func=lambda g: {"todos": "Todos", "train": "Desarrollo", "test": "Test de EP2"}[g], key="grupo_aud")
        orden_txt = g2.selectbox("Orden", ["Con celdas marcadas primero", "Orden de los datos"], key="orden_aud")
        solo = g3.toggle("Solo celdas con datos suficientes", key="solo_datos", help=f"Oculta las celdas con menos de {min_cajas} cajas en el rango (gris plano).")
        m = m_total if grupo == "todos" else m_total[m_total["grupo"] == grupo]
        estado = np.where(m["hueco"], "Hueco", np.where(m["sin_datos"], f"Sin cajas o menos de {min_cajas} en el rango", "Celda sana"))
        m = m.assign(estado=estado, pares=np.where(m["sin_datos"], "sin datos suficientes", m["tasa"].map(lambda v: F.porcentaje(v, 0))), cajas_rango=m["n_rango"].map(F.entero),
                     camara_rotulo=m["camara"].map(lambda c: f"{c.split(' ')[0]} · {c.split('(')[1].rstrip(')')}"))
        orden_todos = orden_gravedad(m) if orden_txt.startswith("Con celdas") else list(dict.fromkeys(m["seg"]))
        total = len(orden_todos)
        visibles = min(int(st.session_state.get("filas_mapa", FILAS_MAPA_INICIO)), total) if total else 0
        orden = orden_todos[:visibles]
        if solo:
            m = m[~m["sin_datos"]]
        m = m[m["seg"].isin(orden)]
        _html(E.leyenda_mapa(min_cajas))
        marcada = m[(m["seg"] == celdas[idx]["segmento"]) & (m["camara"] == celdas[idx]["camara"])] if celdas else None
        with st.container(key="mapa_calor"):
            _grafico(_mapa_calor(m, orden, solo, marcada))
        if total > FILAS_MAPA_INICIO:
            st.button(rotulo_boton_mapa(visibles, total), key="mapa_mas", on_click=lambda: st.session_state.update(filas_mapa=siguiente_filas_mapa(visibles, total)))
            st.caption(f"Se ven {F.entero(visibles)} de {F.entero(total)} segmentos, de los más graves a los menos graves.")
    # ---- definición plegada
    with st.expander(AUD_QUE_ES):
        st.markdown("Un hueco es una cámara que, en un segmento, casi no tiene pares para las cajas que debería ver. **No se sabe por qué:** puede faltar el etiquetado 2D de esa cámara o faltar sus datos, y con estos archivos no se distingue. "
                    "Es una hipótesis para revisar, no una conclusión. Las celdas se llaman **marcadas** porque no existe una verdad externa que confirme cuáles son huecos reales.")
        st.markdown(texto_umbral_hueco(la, frac, min_cajas))


# ------------------------------------------------------------------------------------------------------------ Validación
def _descripcion(ch: Any, texto: str) -> Any:
    """Texto alternativo del gráfico (se escribe en la propia especificación: lo leen los lectores de pantalla)."""
    return ch.properties(description=texto)


def _barras_con_ic(df: pd.DataFrame, y: str, titulo_x: str, descripcion: str, estados: list[str], ancho_texto: int = 170) -> alt.LayerChart:
    """Barras horizontales de un efecto con su intervalo de confianza (``Mejora``, ``lo``, ``hi``), una línea en cero y, al final de cada fila, su estado en TEXTO (el color nunca va solo)."""
    d = df.assign(Texto=lambda t: [F.menos(f"{F.decimal(v, 3)} (IC {F.decimal(lo, 3)} a {F.decimal(hi, 3)})") for v, lo, hi in zip(t["Mejora"], t["lo"], t["hi"])], Estado=estados)
    orden = list(d[y])
    marcas, dec = _marcas_eje(list(d["lo"]) + list(d["hi"]) + list(d["Mejora"]))
    d["xr"] = marcas[-1]
    dom = alt.Scale(domain=[marcas[0], marcas[-1]], nice=False)
    base = alt.Chart(d).encode(y=alt.Y(f"{y}:N", sort=orden, title=None, axis=alt.Axis(labelLimit=340, labelFontSize=12, labelOverlap=False)))
    buenos = ("mejora", "aporta")
    col = alt.Color("Veredicto:N", legend=None, scale=alt.Scale(domain=["mejora", "aporta", "no mejora", "no aporta"], range=[E.TOKENS["acento"], E.TOKENS["acento"], GRIS_GRAFICO, GRIS_GRAFICO])) if "Veredicto" in d else alt.value(E.TOKENS["acento"])
    xe = alt.X("Mejora:Q", title=titulo_x, scale=dom, axis=alt.Axis(values=marcas, labelExpr=_eje_decimal(dec)))
    barras = base.mark_bar(size=16, opacity=0.9, cornerRadiusEnd=3).encode(x=xe, color=col, tooltip=[alt.Tooltip(f"{y}:N", title=""), alt.Tooltip("Texto:N", title="Efecto")])
    ic = base.mark_rule(strokeWidth=2, color=E.TOKENS["texto"]).encode(x=alt.X("lo:Q", title=titulo_x, scale=dom), x2="hi:Q")
    cero = alt.Chart(pd.DataFrame({"x": [0.0]})).mark_rule(color=E.TOKENS["texto_2"], strokeDash=[3, 3]).encode(x=alt.X("x:Q", scale=dom))
    estado = base.mark_text(align="left", dx=12, fontSize=12.5, fontWeight=600, color=E.TOKENS["texto"]).encode(x=alt.X("xr:Q", scale=dom, axis=None), text="Estado:N")
    ch = (barras + ic + cero + estado).properties(height=max(150, 46 * len(d) + 30), padding={"left": 5, "right": ancho_texto, "top": 5, "bottom": 5})
    return _descripcion(ch, descripcion + " " + "; ".join(f"{a}: {e}" for a, e in zip(d[y], estados)) + ".")


def _grafico_generalizacion(datos: dict[str, pd.DataFrame], ev: dict[str, pd.DataFrame], elegido: str, minimo: float | None) -> None:
    d = datos["ie11"].assign(Candidato=lambda t: t["Candidato"].map(F.nombre_visible)).sort_values("AUC", ascending=False)
    orden = list(d["Candidato"])
    nombre_elegido = F.nombre_visible(elegido)
    d = d.assign(Texto=lambda t: [F.menos(f"AUC {F.decimal(a, 3)} (IC {F.decimal(lo, 3)} a {F.decimal(hi, 3)})") for a, lo, hi in zip(t["AUC"], t["lo"], t["hi"])])
    y = alt.Y("Candidato:N", sort=orden, title=None, axis=alt.Axis(labelFontSize=12, labelLimit=270, labelOverlap=False))
    dom = alt.Scale(domain=[0.55, 1])
    base = alt.Chart(d).encode(y=y)
    capas = [alt.Chart(pd.DataFrame({"Candidato": [nombre_elegido], "a": [0.55], "b": [1.0]})).mark_bar(opacity=0.14, color=E.TOKENS["acento"], size=28).encode(y=alt.Y("Candidato:N", sort=orden), x=alt.X("a:Q", scale=dom), x2="b:Q"),
             base.mark_rule(strokeWidth=3, color=E.TOKENS["acento"], opacity=0.8).encode(x=alt.X("lo:Q", title="AUC (validación cruzada por segmentos)", scale=dom, axis=alt.Axis(labelExpr=_eje_decimal(2))), x2="hi:Q"),
             base.mark_point(size=110, filled=True, color=E.TOKENS["acento"]).encode(x=alt.X("AUC:Q", scale=dom), tooltip=[alt.Tooltip("Candidato:N", title=""), alt.Tooltip("Texto:N", title="Global")])]
    if "ie11_particiones" in datos:
        pl = datos["ie11_particiones"].assign(Candidato=lambda t: t["Candidato"].map(F.nombre_visible)).assign(Texto=lambda t: [F.menos(f"Partición {p}: AUC {F.decimal(a, 3)}") for p, a in zip(t["Partición"], t["AUC"])])
        capas.append(alt.Chart(pl).mark_point(size=80, color=GRIS_GRAFICO, shape="diamond", filled=True).encode(y=alt.Y("Candidato:N", sort=orden), x=alt.X("AUC:Q", scale=dom), tooltip=[alt.Tooltip("Candidato:N", title=""), alt.Tooltip("Texto:N", title="")]))
    if minimo is not None:
        capas.append(alt.Chart(pd.DataFrame({"x": [minimo], "t": [f"mínimo por partición: {F.decimal(minimo, 2)}"]})).mark_rule(color=E.TOKENS["texto"], strokeDash=[5, 4], strokeWidth=1.6).encode(x=alt.X("x:Q", scale=dom)))
        capas.append(alt.Chart(pd.DataFrame({"x": [minimo], "t": [f"mínimo por partición: {F.decimal(minimo, 2)}"]})).mark_text(align="left", dx=6, fontSize=12.5, fontWeight=700, color=E.TOKENS["texto"]).encode(x=alt.X("x:Q", scale=dom), y=alt.value(-9), text="t:N"))
    deb = V.particion_debil(ev, elegido)
    if deb:
        capas.append(alt.Chart(pd.DataFrame({"Candidato": [nombre_elegido], "AUC": [deb["auc"]], "t": [f"partición {deb['particion']}"]})).mark_text(dy=-13, fontSize=12, color=E.TOKENS["texto"]).encode(y=alt.Y("Candidato:N", sort=orden), x=alt.X("AUC:Q", scale=dom), text="t:N"))
    desc = DESCRIPCION_GRAFICO["ie11"] + (f" La partición {deb['particion']} de la regla vale {F.decimal(deb['auc'], 3)}." if deb else "")
    _grafico(_descripcion(alt.layer(*capas).properties(height=max(240, 34 * len(d) + 40), padding={"top": 20, "left": 5, "right": 12, "bottom": 5}), F.menos(desc)))


def _grafico_tipos(datos: dict[str, pd.DataFrame]) -> None:
    d = datos["nosup"].assign(Texto=lambda t: [F.menos(f"{F.porcentaje(v)} (IC {F.porcentaje(lo)} a {F.porcentaje(hi)}); {F.entero(n)} cajas") for v, lo, hi, n in zip(t["Tasa"], t["lo"], t["hi"], t["Cajas"])])
    d["Tipo de caso"] = d["Tipo de caso"].map(lambda s: s[:1].upper() + s[1:])
    d["Etiqueta"] = [f"{F.porcentaje(v)} · {F.entero(n)} cajas" for v, n in zip(d["Tasa"], d["Cajas"])]
    tope = float(np.ceil(max(d["hi"]) * 20) / 20)
    d["xr"] = tope
    dom = alt.Scale(domain=[0, tope], nice=False)
    base = alt.Chart(d).encode(y=alt.Y("Tipo de caso:N", title=None, axis=alt.Axis(labelFontSize=12, labelLimit=260, labelOverlap=False)))
    ch = (base.mark_bar(size=26, color=E.TOKENS["acento"], opacity=0.9, cornerRadiusEnd=4).encode(x=alt.X("Tasa:Q", title="Proporción de cajas sin pareja", scale=dom, axis=alt.Axis(format="%", labelExpr="replace(format(datum.value * 100, '.0f'), '.', ',') + ' %'")),
                                                                                           tooltip=[alt.Tooltip("Tipo de caso:N", title=""), alt.Tooltip("Texto:N", title="")])
          + base.mark_rule(strokeWidth=2, color=E.TOKENS["texto"]).encode(x=alt.X("lo:Q", scale=dom), x2="hi:Q")
          + base.mark_text(align="left", dx=12, fontSize=12.5, fontWeight=600, color=E.TOKENS["texto"]).encode(x=alt.X("xr:Q", scale=dom, axis=None), text="Etiqueta:N")
          ).properties(height=alt.Step(70), padding={"left": 5, "right": 190, "top": 5, "bottom": 5})
    _grafico(_descripcion(ch, DESCRIPCION_GRAFICO["nosup"] + " " + "; ".join(f"{a}: {t}" for a, t in zip(d["Tipo de caso"], d["Texto"])) + "."))


def _grafico_brazos(datos: dict[str, pd.DataFrame]) -> None:
    d = datos["brazos"].assign(Candidato=lambda t: t["Candidato"].map(F.nombre_visible)).assign(Texto=lambda t: [F.porcentaje(v) for v in t["Fraccion"]])
    brazos = list(dict.fromkeys(d["Flujo"]))
    corto = {"Solo cola (un paso)": "un paso", "Solo celdas sanas, sin auditoría": "sin auditoría", "Auditoría + cola (dos pasos)": "dos pasos"}
    d["Rotulo"] = d["Flujo"].map(lambda f: corto.get(f, f))
    d["cero"] = 0.0
    barras = alt.Chart(d).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(x=alt.X("Candidato:N", title=None, scale=alt.Scale(paddingInner=0.1, paddingOuter=0.05), axis=alt.Axis(labelAngle=0, labelFontSize=12, labelLimit=300)), xOffset=alt.XOffset("Flujo:N", sort=brazos, scale=alt.Scale(paddingInner=0.04)),
                                            y=alt.Y("Fraccion:Q", title="Fracción de cajas a revisar", scale=alt.Scale(domain=[0, 0.6]), axis=alt.Axis(format="%", values=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6])),
                                            color=alt.Color("Flujo:N", title=None, sort=brazos, scale=alt.Scale(domain=brazos, range=[E.FLUJOS_COLORES[b] for b in brazos]),
                                                            legend=alt.Legend(orient="top", labelLimit=420, columnPadding=18, symbolType="square", columns=3)),
                                            tooltip=[alt.Tooltip("Candidato:N", title=""), alt.Tooltip("Flujo:N", title=""), alt.Tooltip("Texto:N", title="Fracción")])
    desplaz = alt.XOffset("Flujo:N", sort=brazos, scale=alt.Scale(paddingInner=0.04))
    # el valor y, debajo, el nombre corto del flujo sobre cada barra: el color no es lo único que distingue los flujos
    valores = alt.Chart(d).transform_calculate(Etiqueta="[datum.Texto, datum.Rotulo]").mark_text(baseline="bottom", dy=-9, align="left", fontSize=12, fontWeight=600, color=E.TOKENS["texto"]).encode(
        x=alt.X("Candidato:N", scale=alt.Scale(paddingInner=0.1, paddingOuter=0.05)), xOffset=desplaz, y=alt.Y("Fraccion:Q"), text="Etiqueta:N")
    desc = DESCRIPCION_GRAFICO["posthoc"] + " " + "; ".join(f"{c}, {f}: {t}" for c, f, t in zip(d["Candidato"], d["Rotulo"], d["Texto"])) + "."
    _grafico(_descripcion((barras + valores).properties(height=300), desc))


def _grafico_validacion(pref: str, datos: dict[str, pd.DataFrame], ev: dict[str, pd.DataFrame] | None = None, elegido: str = "Regla top") -> None:
    ev = ev or {}
    if pref == "ie9" and "ie9" in datos:
        d = datos["ie9"]
        _grafico(_barras_con_ic(d, "Modelo", "Cambio de PR-AUC (optimizado − por defecto)", DESCRIPCION_GRAFICO["ie9"], [str(v) for v in d["Veredicto"]], ancho_texto=110))
    elif pref == "ie10" and "ie10" in datos:
        d = datos["ie10"].assign(Comparación=lambda t: t["Ensamble"] + " contra " + t["Mejor componente"].map(F.nombre_componente).map(lambda c: c[:1].lower() + c[1:] if c.startswith("Regla") else c))
        _grafico(_barras_con_ic(d, "Comparación", "Diferencia de AUC (ensamble − mejor componente)", DESCRIPCION_GRAFICO["ie10"], [f"{F.decimal_signado(m, 3)} · {v}" for m, v in zip(d["Mejora"], d["Veredicto"])], ancho_texto=160))
    elif pref == "ie11" and "ie11" in datos:
        _grafico_generalizacion(datos, ev, elegido, V.auc_minimo_particion())
    elif pref == "nosup" and "nosup" in datos:
        _grafico_tipos(datos)
    elif pref == "posthoc" and "brazos" in datos:
        _grafico_brazos(datos)


def _kpis_html(items: list[dict[str, str]]) -> str:
    return E.indicadores([{**i, "tono": ""} for i in items])


def _puntos_clave(puntos: list[str]) -> None:
    if puntos:
        _html('<div class="aud-claves">' + "".join(f'<div class="aud-clave">{V.negrita_inicio(p)}</div>' for p in puntos) + "</div>")


def _lectura(texto: str) -> None:
    st.markdown(f"**Lectura:** {texto}")


def _tarjeta_grafico(titulo: str, pie: str = "") -> None:
    _html(f'<p class="aud-card-t">{E._e(titulo)}</p>')
    if pie:
        st.caption(pie)


def _boton_csv_curvas(ev: dict[str, pd.DataFrame]) -> None:
    if "ie9__curvas_de_validacion" in ev:
        st.caption(V.TEXTO_CSV_CURVAS)
        st.download_button("Descargar curvas de validación (CSV)", ev["ie9__curvas_de_validacion"].to_csv(index=False).encode("utf-8"), "ie9__curvas_de_validacion.csv", "text/csv", key="csv_curvas_validacion", icon=":material/download:")


def validacion(ctx: dict[str, Any]) -> None:
    """Validación (F34): veredicto y cuatro cifras arriba, cinco pestañas con la misma plantilla (lectura, un gráfico, puntos clave y «Tablas de apoyo» cerradas)."""
    ev = ctx["D"]["evidencia"]
    lecturas = lectura_evidencia(ev)
    datos = datos_validacion(ev)
    segundos = st.session_state.get("segundos", SUPUESTO_SEGUNDOS)
    r = inicio_resumen(ctx["D"], segundos)
    elegido = ctx["K"].get("candidato", "Regla top")
    sel = ev.get("ie12__tabla_de_seleccion")
    if sel is not None and not {"candidato", "O1", "O2", "O3", "O4"} <= set(sel.columns):
        sel = None                                                                           # los datos de prueba pueden traer menos columnas que los reales
    encabezado("Validación", DESCRIPCION_PAGINA["Validación"])
    with st.container(key="val_veredicto"):
        if sel is not None and not sel.empty and V.titular_validacion(sel, elegido)["texto"]:
            _html(f'<p class="aud-vt">{E._e(V.titular_validacion(sel, elegido)["texto"])}</p>')
        _html(_kpis_html(V.kpis_validacion(ctx["K"], r, ctx["ciclistas"] or {}, ETIQUETA_CICLISTA)))
        _html(E.chips([(V.ROTULO_MUESTRA.format(n=F.entero(r["segmentos"])), False), (V.ROTULO_SIN_VALIDACION, False), (f"Ciclistas: {ETIQUETA_CICLISTA[:1].lower()}{ETIQUETA_CICLISTA[1:]}", True)]))
    tabs = st.tabs(list(V.PESTANAS))
    # pestaña: Modelo elegido
    with tabs[0]:
        _lectura(lecturas.get("ie12", ""))
        if sel is not None and not sel.empty:
            _html('<p class="aud-card-t">Criterios de selección (O1 a O4)</p>')
            _html(E.criterios_tarjetas(V.conteos_criterios(sel)))
            aviso = V.aviso_o4(sel, elegido, ev)
            if aviso:
                _html(f'<div class="aud-aviso">{E._e(aviso)}</div>')
        T.mostrar_tabla(V.tabla_resultados(tabla_resultados_clave(ctx["K"])), "resultados", titulo=True)
        st.caption("Fuente: informe técnico de EP3, sección 12 (cuadro «Modelo escogido») y anexo B (análisis en muestra).")
        T.tablas_de_apoyo(V.tablas_de_pestana("Modelo elegido", ev))
    # pestaña: Generalización
    with tabs[1]:
        _lectura(lecturas.get("ie11", ""))
        if "ie11" in datos:
            _tarjeta_grafico(V.TITULO_GRAFICO["ie11"], "Punto azul: AUC con su intervalo de confianza 95 % por segmentos. Rombos grises: AUC de cada partición (regla de puntos, LR3 y XGB).")
            _grafico_validacion("ie11", datos, ev, elegido)
        _puntos_clave(V.puntos_generalizacion(ev, elegido))
        T.tablas_de_apoyo(V.tablas_de_pestana("Generalización", ev))
    # pestaña: Alternativas (hiperparámetros y ensambles)
    with tabs[2]:
        _html(f'<p class="aud-card-t">{E._e(V.SUB_ALTERNATIVAS[0])}</p>')
        _lectura(lecturas.get("ie9", ""))
        if "ie9" in datos:
            _tarjeta_grafico(V.TITULO_GRAFICO["ie9"], f"Positivo es mejora. {V.LEYENDA_INTERVALO} {V.regla_mejora_hiperparametros()}")
            _grafico_validacion("ie9", datos)
        borde = V.aviso_bordes(ev)
        if borde:
            _puntos_clave([borde])
        _html(f'<p class="aud-card-t">{E._e(V.SUB_ALTERNATIVAS[1])}</p>')
        _lectura(lecturas.get("ie10", ""))
        if "ie10" in datos:
            _tarjeta_grafico(V.TITULO_GRAFICO["ie10"], f"Positivo es que el ensamble aporta. {V.LEYENDA_INTERVALO}")
            _grafico_validacion("ie10", datos)
        T.tablas_de_apoyo(V.tablas_de_pestana("Alternativas", ev), extra=lambda: _boton_csv_curvas(ev))
    # pestaña: Tipos de caso
    with tabs[3]:
        _lectura(lecturas.get("nosup", ""))
        if "nosup" in datos:
            _tarjeta_grafico(V.TITULO_GRAFICO["nosup"], "Dos tipos de caso (k = 2), con intervalo de confianza 95 % por segmentos. Es descriptivo y post hoc.")
            _grafico_validacion("nosup", datos)
        _puntos_clave(V.puntos_tipos_de_caso(ev))
        T.tablas_de_apoyo(V.tablas_de_pestana("Tipos de caso", ev))
    # pestaña: En muestra
    with tabs[4]:
        _html(f'<div class="aud-aviso">{E._e(AVISO_EN_MUESTRA)}</div>')
        _lectura(lecturas.get("posthoc", ""))
        _impacto_estimado(r, segundos)
        var = V.tabla_variantes(ev, elegido)
        if var is not None:
            _html('<p class="aud-card-t">De dónde viene la mejora de la auditoría</p>')
            tv = V.tabla_apoyo("posthoc__diferencia_C_menos_A", {"posthoc__diferencia_C_menos_A": var})
            if tv is not None:
                T.mostrar_tabla(tv, "variantes")
            frase = V.frase_auditoria(ev, elegido)
            if frase:
                _puntos_clave([frase])
        if "brazos" in datos:
            _tarjeta_grafico(V.TITULO_GRAFICO["posthoc"], "Menos es mejor.")
            _grafico_validacion("posthoc", datos)
        T.tablas_de_apoyo(V.tablas_de_pestana("En muestra", ev))


# ------------------------------------------------------------------------------------------------------------ Puntuar datos nuevos
FORMATO_ARCHIVOS = pd.DataFrame(P.filas_formato(), columns=["Archivo", "Columnas", "Uso"])       # compatibilidad: la tabla ahora sale de ``puntuar.filas_formato`` (columnas tomadas del código)


def _ronda() -> int:
    return int(st.session_state.get("pt_ronda", 0))


def _soltar_archivos() -> None:
    """Suelta los archivos de los dos cargadores (cambian de clave) y el error que hubiera quedado de un intento anterior."""
    for k in [k for k in st.session_state if str(k).startswith(("pt_f1_", "pt_f2_"))] + ["_pt_error"]:
        st.session_state.pop(k, None)
    st.session_state["pt_ronda"] = _ronda() + 1


def _pedir_ejemplo() -> None:
    """«Usar un segmento de desarrollo de ejemplo»: suelta los archivos que hubiera y pide el ejemplo (se calcula en la siguiente ejecución)."""
    _soltar_archivos()
    st.session_state["usar_ejemplo"] = True


def _otro_segmento() -> None:
    """«Cargar otro segmento»: vuelve al inicio y suelta lo que había en memoria (el resultado, las tablas paginadas y los archivos de los dos cargadores)."""
    _soltar_archivos()
    for k in [k for k in st.session_state if str(k).startswith("pag_pt_")] + ["_pt_vista", "usar_ejemplo"]:
        st.session_state.pop(k, None)


def _aviso(texto: str) -> None:
    _html(f'<div class="aud-aviso" role="alert">{E._e(texto).replace(chr(10), "<br>")}</div>')                # los saltos de línea del mensaje (por ejemplo, los dos ids) se respetan


def _calcular(ctx: dict[str, Any], art: Any, lidar: pd.DataFrame, asoc: pd.DataFrame | None, origen: str, nombres: tuple[str, str | None], firma: tuple | None = None) -> P.Vista | None:
    """Puntúa el segmento en memoria y arma lo que se guarda para mostrarlo (nunca los archivos de entrada). Si falla, guarda el error (con la firma de los archivos) para mostrarlo mientras no cambien."""
    from waymo_evaluacion.ep3.inferencia import construir_variables, puntuar_segmento

    with st.spinner("Puntuando el segmento…"):
        try:
            res = puntuar_segmento(lidar, asoc, art)
        except (KeyError, ValueError) as e:
            st.session_state["_pt_error"] = {"firma": firma, "texto": f"No se pudo puntuar el archivo: {e}"}
            return None
        if origen == "ejemplo" and len(res.cajas):                                                   # el ejemplo no trae archivo 2: se le suman las celdas de desarrollo ya calculadas (F37)
            res = P.completar_ejemplo(res, ctx["D"].get("cajas"), ctx["D"].get("lista_A"), ctx["D"].get("celdas"), str(res.cajas["seg"].iloc[0]))
        az = construir_variables(lidar)[["segment_id", "key.frame_timestamp_micros", "key.laser_object_id", "az_signed"]]
        cola = P.preparar_cola_vista(res.lista_B, res.cajas, az, ctx["rangos"])
    segs = res.cajas["seg"].nunique() if len(res.cajas) else 0
    n_celdas = int(res.tasas["cajas_en_rango"].shape[0] * res.tasas["cajas_en_rango"].shape[1]) if len(res.tasas) else 0
    col = next((c for c in lidar.columns if c.endswith("key.segment_context_name")), None)
    nombre = str(lidar[col].iloc[0]) if origen == "archivo" and col is not None and lidar[col].nunique() == 1 else ""             # el nombre completo, tal como viene en el archivo
    return P.Vista(origen, str(res.cajas["seg"].iloc[0]) if len(res.cajas) else "—", int(segs), res.lista_A, cola, res.lista_B, res.resumen, list(res.advertencias), int(len(res.cajas)), n_celdas,
                   bool(res.resumen.get("tiene_asociacion")), nombres, res.tasas, firma, nombre)


def _cargadores(plegado: bool) -> tuple[Any, Any]:
    """Los dos cargadores, uno al lado del otro. Antes de puntuar están a la vista; después, en el bloque plegable «Archivos del segmento» (se puede agregar o cambiar el archivo 2)."""
    r = _ronda()
    with st.expander(P.EXPANDER_ARCHIVOS, expanded=not plegado):                                  # siempre el mismo bloque (abierto antes de puntuar, cerrado después): así los cargadores no se vuelven a montar y siguen mostrando sus archivos
        c1, c2 = st.columns(2, gap="medium")
        with c1, st.container(key="pt_up1"):
            _html(f'<p class="aud-dz-t">Archivo 1 <span class="etq obl">obligatorio</span></p><p class="aud-dz-a">{E._e(P.ARCHIVO_1_AYUDA)}</p>')
            f1 = st.file_uploader(P.ARCHIVO_1_ROTULO, type="parquet", key=f"pt_f1_{r}", label_visibility="collapsed")
        with c2, st.container(key="pt_up2"):
            _html(f'<p class="aud-dz-t">Archivo 2 <span class="etq">opcional</span></p><p class="aud-dz-a">{E._e(P.ARCHIVO_2_AYUDA)}</p>')
            f2 = st.file_uploader(P.ARCHIVO_2_ROTULO, type="parquet", key=f"pt_f2_{r}", label_visibility="collapsed")
    return f1, f2


def _firma(f1: Any, f2: Any) -> tuple | None:
    """Firma (nombre, tamaño y sha256) de los archivos actuales; ``None`` si no hay ninguno. Se calcula una vez por archivo subido y no guarda su contenido."""
    if f1 is None and f2 is None:
        return None
    cache = st.session_state.setdefault("_pt_firmas", {})

    def una(f: Any) -> tuple | None:
        if f is None:
            return None
        k = (f.file_id, f.size)
        if k not in cache:
            cache[k] = P.firma_archivo(f.name, f.getvalue())
        return cache[k]

    return (una(f1), una(f2))


def _puntuar_archivos(ctx: dict[str, Any], art: Any, f1: Any, f2: Any, firma: tuple) -> P.Vista | None:
    """Valida los archivos (tamaño, parquet, columnas y que el 2 sea del mismo segmento que el 1) y los puntúa. Con un problema guarda el mensaje y devuelve ``None``."""
    def falla(texto: str) -> None:
        st.session_state["_pt_error"] = {"firma": firma, "texto": texto}

    for f in (f1, f2):
        msg = P.validar_tamano(f.name, f.size) if f is not None else None
        if msg:
            return falla(msg)
    lidar, msg = P.leer_parquet(f1.getvalue(), f1.name)
    if msg:
        return falla(msg)
    asoc = None
    if f2 is not None:
        asoc, msg = P.leer_parquet(f2.getvalue(), f2.name)
        if msg:
            return falla(msg)
    problema = validar_lidar_box(lidar) or (validar_asociacion(asoc) if asoc is not None else None) or (P.validar_correspondencia(lidar, asoc) if asoc is not None else None)
    if problema:
        return falla(problema)
    return _calcular(ctx, art, lidar, asoc, "archivo", (f1.name, f2.name if f2 is not None else None), firma)


def _guardar_vista(vista: P.Vista) -> None:
    """Deja el segmento puntuado en la sesión (el Resumen lista sus cifras) y vuelve a dibujar la página con el resultado."""
    st.session_state["_pt_vista"] = vista
    st.session_state.pop("_pt_error", None)
    P.registrar_en_sesion(st.session_state, vista, datetime.now().strftime("%H:%M"))             # solo cifras: el Resumen las lista debajo de lo congelado
    st.rerun()


def _zona_puntuar(ctx: dict[str, Any], art: Any, f1: Any, f2: Any, firma: tuple | None, habia_resultado: bool) -> None:
    """El botón «Puntuar segmento» (deshabilitado sin el archivo 1), su línea de ayuda según los archivos, el ejemplo de desarrollo a un lado y los avisos (error de un intento, o archivos cambiados)."""
    izq, der = st.columns([3, 1.6], vertical_alignment="top")
    with izq:
        pulsado = st.button(P.BOTON_PUNTUAR, key="pt_puntuar", type="primary", disabled=f1 is None, width="content")
        _html(f'<p class="aud-ayuda-flujo" role="status">{E._e(P.ayuda_flujo(f1 is not None, f2 is not None))}</p>')
    with der, st.container(key="pt_ejemplo"):
        if ctx["D"].get("cajas") is not None:
            st.markdown(P.PREGUNTA_EJEMPLO)
            st.button(P.BOTON_EJEMPLO, on_click=_pedir_ejemplo, width="content",
                      help="Reconstruye un lidar_box mínimo desde las variables derivadas de un segmento de desarrollo (no son datos crudos de Waymo) y le suma sus celdas marcadas ya calculadas.")
    if pulsado and f1 is not None:
        vista = _puntuar_archivos(ctx, art, f1, f2, firma)
        if vista is not None:
            _guardar_vista(vista)
        st.rerun()                                                                                  # con un error, la siguiente ejecución lo muestra desde la sesión (mientras los archivos no cambien)
    error = st.session_state.get("_pt_error")
    if error and error.get("firma") == firma:
        _aviso(error["texto"])
    elif habia_resultado:
        _aviso(P.AVISO_CAMBIARON)                                                                   # nunca queda en pantalla un resultado que no corresponde a los archivos actuales


def _resultado(ctx: dict[str, Any], vista: P.Vista) -> None:
    with st.container(key="pt_resultado"):
        a, b, c = st.columns([2.4, 1, 1.4], vertical_alignment="center")
        etiqueta = f' <span class="etq">{E._e(P.ETIQUETA_EJEMPLO)}</span>' if vista.origen == "ejemplo" else ""
        ejemplo = f'<p class="aud-seg-a">{E._e(P.NOTA_EJEMPLO.format(segmento=F.segmento_corto(vista.segmento)))}</p>' if vista.origen == "ejemplo" else ""
        completo = f'<p class="aud-seg-a">{E._e(vista.nombre_segmento)}</p>' if vista.nombre_segmento else ""                  # nombre completo del segmento, para reconocerlo frente al de la carpeta
        a.markdown(f'<p class="aud-seg-t">{E._e(P.etiqueta_segmento(vista))}{etiqueta}</p>{completo}<p class="aud-seg-a">{E._e(P.NOTA_PROCESADO)}</p>{ejemplo}', unsafe_allow_html=True)
        b.button(P.BOTON_OTRO, on_click=_otro_segmento, width="stretch")
        c.download_button(P.BOTON_DESCARGA, lambda: P.zip_resultados(vista), "resultados_segmento.zip", "application/zip", type="primary", icon=":material/download:", width="stretch",
                          help="Un solo archivo con las dos listas en CSV (celdas marcadas y cola), con todas sus columnas.")
        _html(E.indicadores(P.tarjetas(vista)))
        for adv in vista.advertencias:
            _aviso(F.texto_visible(adv)[:1].upper() + F.texto_visible(adv)[1:])
    with st.container(key="pt_celdas"):
        _html(f'<p class="aud-card-t">{E._e(P.TITULO_CELDAS)}</p>')
        t = P.tabla_celdas(vista)
        anillo_estados = P.estados_anillo(vista.lista_A, CAMARAS) if vista.tiene_asociacion else P.estados_sin_busqueda(CAMARAS)
        marcada = next((int(str(x)[0]) for x in vista.lista_A["camara"].astype(str) if str(x)[:1].isdigit()), None) if len(vista.lista_A) else None
        if t is None:
            texto = P.TEXTO_SIN_CELDAS if vista.tiene_asociacion else P.TEXTO_CELDAS_NO_BUSCADAS
            _html(E.vacio(texto, P.NOTA_SIN_ARCHIVO_2 if not vista.tiene_asociacion else "Todas las cámaras de este segmento tienen cajas con par 2D en la proporción esperada.",
                          E.anillo_camaras(anillo_estados, 96, "Anillo de cámaras del segmento")))
        else:
            izq, der = st.columns([1, 3.4], vertical_alignment="center")
            izq.markdown(E.anillo_camaras(anillo_estados, 120, "Anillo de cámaras del segmento: las cámaras con celdas marcadas, resaltadas", resaltar=marcada), unsafe_allow_html=True)
            with der:
                T.mostrar_tabla(t, "pt_celdas")
    with st.container(key="pt_cola"):
        T.mostrar_tabla(P.tabla_cola(vista), "pt_cola", por_pagina=P.POR_PAGINA_COLA, titulo=True, nombre_csv="lista_B_nueva")
    with st.expander("Resumen del cálculo"):
        T.mostrar_tabla(P.tabla_resumen(vista), "pt_resumen")


def puntuar(ctx: dict[str, Any]) -> None:
    """Puntuar datos nuevos (F35, flujo de F39): los dos cargadores a la vista (el 1 obligatorio y el 2 opcional, en cualquier orden), el botón «Puntuar segmento» y, con un resultado, los archivos en un bloque plegable.

    Nada se puntúa al subir un archivo: se puntúa al pulsar el botón. El resultado lleva la firma de los archivos con que se calculó; si cambian, deja de mostrarse y la página pide volver a puntuar. El segmento
    puntuado se guarda solo en la memoria de la sesión (no los archivos de entrada); «Cargar otro segmento» lo suelta. No se escribe nada a disco.
    """
    encabezado("Puntuar datos nuevos", texto_entorno("puntuar_subtitulo"))
    _html(E.chips([(texto_entorno("puntuar_etiqueta"), False), (texto_entorno("puntuar_etiqueta_2"), False)]))
    try:
        art = ctx["artefactos"]()
    except FileNotFoundError:
        st.error("Falta la solución congelada, así que esta página no puede calcular. Avise a quien mantiene la página.")
        return
    if st.session_state.get("usar_ejemplo"):                                                         # el botón de ejemplo pidió el segmento de desarrollo
        st.session_state["usar_ejemplo"] = False
        cajas = ctx["D"].get("cajas")
        if cajas is not None:
            la = ctx["D"].get("lista_A")
            seg_ejemplo = str(la["segmento"].iloc[0]) if la is not None and len(la) else str(cajas["seg"].iloc[0])
            ejemplo = _calcular(ctx, art, ejemplo_lidar_box(cajas, seg_ejemplo), None, "ejemplo", ("segmento de desarrollo " + seg_ejemplo, None))
            if ejemplo is not None:
                _guardar_vista(ejemplo)
    vista = st.session_state.get("_pt_vista")
    pasos = st.empty()
    f1, f2 = _cargadores(plegado=vista is not None)
    firma = _firma(f1, f2)
    if vista is not None and vista.firma == firma:
        pasos.markdown(E.pasos_flujo(P.estado_pasos(True, vista.tiene_asociacion)), unsafe_allow_html=True)
        _resultado(ctx, vista)
    else:
        pasos.markdown(E.pasos_flujo(P.estado_pasos(False)), unsafe_allow_html=True)
        _zona_puntuar(ctx, art, f1, f2, firma, habia_resultado=vista is not None)
        if vista is None:
            _html(E.vacio(P.VACIO_TITULO, P.VACIO_TEXTO, E.anillo_camaras(P.estados_sin_busqueda(CAMARAS), 96, "Anillo de cámaras sin datos")))
    with st.expander("Formato de los archivos de entrada", expanded=False):
        st.markdown(f'<p class="tstd-resp">{E._e(P.FORMATO_INTRO.format(mb=P.MAX_MB))}</p>', unsafe_allow_html=True)
        T.mostrar_tabla(P.tabla_formato(), "pt_formato")


# ------------------------------------------------------------------------------------------------------------ Ética y límites
def etica(ctx: dict[str, Any]) -> None:
    """Ética y límites (F36): primero la regla de uso («Decide siempre una persona») y lo que nunca debe hacerse; luego propósito, datos, desempeño, límites, consideraciones éticas y dónde corre.
    Los textos viven en ``etica_ayuda.py`` y ``app_logica.py`` (los que dependen del modo de despliegue, en ``TEXTOS_ENTORNO``)."""
    encabezado("Ética y límites", DESCRIPCION_PAGINA["Ética y límites"])
    borrador = texto_entorno("borrador")
    n = F.entero(inicio_resumen(ctx["D"], st.session_state.get("segundos", SUPUESTO_SEGUNDOS))["segmentos"]) if ctx["D"].get("cajas") is not None else "—"
    _html(E.hero_decide(EA.HERO_TITULO, EA.HERO_TEXTO, EA.HERO_AVISOS))
    a, b = st.columns(2, gap="medium")
    a.markdown(E.tarjeta_icono("Propósito", f"<p>{E._e(EA.PROPOSITO)}</p>", "objetivo"), unsafe_allow_html=True)
    b.markdown(E.tarjeta_icono("Datos y licencia", E.lista_puntos([x.format(n=n) for x in EA.DATOS_PUNTOS]), "datos"), unsafe_allow_html=True)
    claves = {t.get("titulo", ""): t.get("valor", "") for t in ctx["K"].get("tarjetas", [])}
    with st.container(key="et_desempeno"):
        _html(E.cabecera_tarjeta("Desempeño", "medidor", EA.DESEMPENO_ETIQUETA))
        _html(f"<p>{E._e(EA.DESEMPENO_INTRO)}</p>")
        tarjetas = EA.tarjetas_desempeno(claves)
        if tarjetas:
            _html(E.estadisticas(tarjetas))
        _html(f"<p>{E._e(EA.DESEMPENO_NOTA.format(n=n))}</p>")
        st.page_link(ARCHIVO_PAGINA["Validación"], label=EA.ENLACE_VALIDACION)
    comp = EA.comparacion_clases(ctx["ciclistas"] or {})
    with st.container(key="et_limites"):
        _html(E.cabecera_tarjeta("Límites conocidos", "alerta"))
        _html(f"<p>{E._e(EA.LIMITES_INTRO)}</p>")
        if comp:
            _html(E.barra_comparacion([("Peatones", comp["peaton"], comp["peaton_txt"], False), ("Ciclistas", comp["ciclista"], comp["ciclista_txt"], True)], EA.LIMITES_BARRA_DESCRIPCION.format(p=comp["peaton_txt"], c=comp["ciclista_txt"])))
            st.caption(EA.LIMITES_CASOS.format(casos=comp["casos"], segmentos=comp["segmentos"]))
        _html(E.lista_puntos(list(EA.LIMITES_PUNTOS)))
    c, d = st.columns(2, gap="medium")
    consideraciones, donde = texto_entorno("consideracion_etica"), texto_entorno("donde_corre")
    c.markdown(E.tarjeta_icono("Consideraciones éticas", f"<p>{E._e(consideraciones)}</p>", "escudo", borrador=borrador), unsafe_allow_html=True)
    d.markdown(E.tarjeta_icono("Dónde corre", f"<p>{E._e(donde)}</p>", "servidor", borrador=borrador), unsafe_allow_html=True)


# ------------------------------------------------------------------------------------------------------------ Ayuda y glosario
def ayuda(ctx: dict[str, Any]) -> None:
    """Ayuda y glosario (F36): los tres pasos con su enlace, qué hace cada página, el glosario con buscador y grupos, y las preguntas frecuentes (las de siempre)."""
    encabezado("Ayuda y glosario", DESCRIPCION_PAGINA["Ayuda y glosario"])
    _html(f'<p class="aud-card-t">{E._e(EA.PASOS_TITULO)}</p>')
    cols = st.columns(3, gap="large")
    for i, (col, (titulo, texto, destino)) in enumerate(zip(cols, EA.PASOS), 1):
        with col, st.container(key=f"ay_paso_{i}"):
            _html(E.paso_ayuda(i, titulo, texto))
            st.page_link(ARCHIVO_PAGINA[destino], label=destino)
    _html(f'<p class="aud-card-t">{E._e(EA.PAGINAS_TITULO)}</p>')
    descripcion = DESCRIPCION_PAGINA
    _html(E.tarjetas_paginas([("Rol", EA.USO_ROL, False), ("Auditoría de cámaras", EA.USO_AUDITORIA, False), ("Cola de revisión", EA.USO_COLA, False),
                              ("Validación", descripcion["Validación"], True), ("Explica una caja", descripcion["Explica una caja"], True), ("Puntuar datos nuevos", texto_entorno("puntuar_subtitulo"), True)]))
    st.caption("Los bloques con borde punteado son los que se agregaron en el rediseño; los otros tres conservan su texto de siempre.")
    _html(f'<p class="aud-card-t">{E._e(EA.GLOSARIO_TITULO)}</p>')
    q, g = st.columns([2, 3], vertical_alignment="center")
    busqueda = q.text_input(EA.GLOSARIO_ETIQUETA_BUSCADOR, key="gl_busqueda", placeholder=EA.GLOSARIO_BUSCADOR, label_visibility="collapsed")
    with g:
        grupo = st.pills("Grupo del glosario", EA.grupos_del_glosario(), selection_mode="single", default=EA.GRUPO_TODOS, key="gl_grupo", label_visibility="collapsed")
    items = EA.filtrar_glosario(busqueda, grupo)
    if items:
        _html(E.tarjetas_glosario(items))
    else:
        _html(f'<p class="aud-gl-vacio" role="status">{E._e(EA.GLOSARIO_SIN_RESULTADOS)}</p>')
    _html(f'<p class="aud-card-t">{E._e(EA.PREGUNTAS_TITULO)}</p>')
    for q_, a_ in preguntas_frecuentes(ctx["D"]["evidencia"].get("posthoc__equidad")):
        with st.expander(q_):
            st.write(a_)


# ------------------------------------------------------------------------------------------------------------ despacho
SECCION_FN = {"Resumen": resumen, "Cola de revisión": cola, "Explica una caja": explica, "Auditoría de cámaras": auditoria, "Validación": validacion, "Puntuar datos nuevos": puntuar,
              "Ética y límites": etica, "Ayuda y glosario": ayuda}
NECESITA_DATOS = {"Resumen", "Cola de revisión", "Explica una caja", "Auditoría de cámaras", "Validación"}


def ejecutar(seccion: str) -> None:
    """Ejecuta una sección con el contexto compartido; si faltan los datos de la página, las secciones que los necesitan muestran un error claro."""
    import contexto as C

    ctx = C.contexto()
    if ctx["falta"] is not None and seccion in NECESITA_DATOS:
        encabezado(seccion, DESCRIPCION_PAGINA.get(seccion, ""))
        st.error(f"No se encuentran los datos de la página ({ctx['falta']}). Hay que prepararlos antes de abrir la página (ver el mapa de archivos de EP3).")
        return
    SECCION_FN[seccion](ctx)
