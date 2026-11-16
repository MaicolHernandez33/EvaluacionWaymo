"""Secciones de la página «Auditor de etiquetas 3D» (F20). Cada función recibe el contexto ``ctx`` (datos, rol, modo presentación, cachés) y dibuja una sección.

Los números salen de ``waymo_evaluacion.ep3.app_logica`` (lógica probada) y se formatean con ``waymo_evaluacion.ep3.formato`` (es-CL). Sin conexiones externas.
El marco (navegación, estilos, rol, pie) está en ``app/app.py``; cada archivo de ``app/paginas/`` llama a ``ejecutar(nombre_de_la_sección)``.
"""
from __future__ import annotations

from typing import Any

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import estilos as E
from waymo_evaluacion.ep3 import formato as F
from waymo_evaluacion.ep3.app_logica import (
    ARCHIVO_PAGINA, AVISO_EN_MUESTRA, CAMARAS, CHIP_ESTADO, CLASE_ADVERTENCIA, CLASE_NORMAL, COLUMNA_FOTOGRAMAS, COLUMNA_PROBABILIDAD, CURVA_UN_PASO, DESCRIPCION_PAGINA, EJEMPLOS_CAJA,
    FLUJO_DOS, FLUJOS, GLOSARIO, NOTA_AGRUPADO, NOTA_FOTOGRAMAS, REFERENCIAS, SUPUESTO_SEGUNDOS, alertas_resumen, curva_dependencia, curva_inversa, curvas_a_mostrar, datos_validacion, detalle_caja,
    ejemplo_lidar_box, explicacion_caja, filtrar_cola, info_tipo_de_caso, inicio_resumen, lectura_evidencia, lista_A_detalle, lista_A_presentable, matriz_calor, nombre_curva_legible,
    ocultar_identificadores, orden_segmentos, percentil_en_cola, preguntas_frecuentes, recall_en_presupuesto, resumen_cola, tabla_cola, tabla_por_objeto, tabla_resultados_clave, texto_esfuerzo_cola,
    texto_posicion, texto_resultado_cola, tipo_de_caso, validar_asociacion, validar_lidar_box,
)

NOMBRES_EVIDENCIA = {"ie9": "Hiperparámetros", "ie10": "Ensambles", "ie11": "Generalización", "ie12": "Selección", "nosup": "No supervisado", "posthoc": "En muestra"}
MODO_PRESUPUESTO = "Presupuesto"
MODO_OBJETIVO = "Meta"
MAX_FILAS_COLA = 500
MAX_FILAS_LISTA_A = 30
ESTILO_GRAFICO = {"font": "Segoe UI, system-ui, Arial, sans-serif"}
GRIS_GRAFICO = "#6B7280"


def _html(x: str) -> None:
    st.markdown(x, unsafe_allow_html=True)


def _tabla(df: pd.DataFrame, **kw: Any) -> Any:
    """``st.dataframe`` compacto con el ancho de cada columna calculado con su encabezado y su contenido (ningún encabezado cortado)."""
    anchos = F.anchos_columnas(df)
    cfg = {c: st.column_config.Column(width=w) for c, w in anchos.items()}
    cfg.update(kw.pop("column_config", {}))
    return st.dataframe(df, width="stretch", hide_index=True, row_height=30, height=min(40 + 31 * len(df), kw.pop("alto_max", 420)), column_config=cfg, **kw)


def _grafico(ch: alt.Chart | alt.LayerChart, **kw: Any) -> None:
    st.altair_chart(ch.configure(**{"font": ESTILO_GRAFICO["font"]}).configure_axis(labelFontSize=11, titleFontSize=11, titleColor=E.TOKENS["texto_suave"]).configure_view(strokeWidth=0), width="stretch", **kw)


def _eje_decimal(d: int = 2) -> str:
    """Expresión de Vega para que las etiquetas del eje salgan con coma decimal (es-CL)."""
    return f"replace(format(datum.value, '.{d}f'), '.', ',')"


def encabezado(titulo: str, descripcion: str) -> None:
    """Encabezado de página: título pequeño, una línea de descripción y, a la derecha, el chip de estado persistente con el texto completo de «en muestra»."""
    c1, c2 = st.columns([3.6, 3], vertical_alignment="center")                      # el chip no se corta ni en modo presentación (letra 18 % mayor)
    with c1:
        st.title(titulo)
        _html(f'<p class="aud-descripcion">{E._e(descripcion)}</p>')
    with c2:
        with st.popover(CHIP_ESTADO, key="chip_estado"):
            st.markdown("**En muestra**")
            st.write(AVISO_EN_MUESTRA)
            st.write("Por eso las cifras de este flujo son optimistas y no deben leerse como una prueba ciega. La validación con segmentos nuevos está preparada y sellada, y todavía no se ejecutó.")


# ------------------------------------------------------------------------------------------------------------ Resumen
def resumen(ctx: dict[str, Any]) -> None:
    D = ctx["D"]
    segundos = st.session_state.get("segundos", SUPUESTO_SEGUNDOS)
    r = inicio_resumen(D, segundos)
    encabezado("Resumen", f"Estado de las etiquetas 2D de peatones y ciclistas en {F.entero(r['segmentos'])} segmentos de desarrollo.")
    _html(E.metricas([("Cajas analizadas", F.entero(r["cajas"]), "peatones y ciclistas", ""), ("Cajas sin pareja", F.porcentaje(r["prevalencia"]), "sin par en ninguna cámara", ""),
                      ("Celdas marcadas", F.entero(r["celdas_marcadas"]), f"segmento × cámara, en {F.entero(r['segmentos_con_hueco'])} segmentos", "hueco"),
                      ("Segmentos", F.entero(r["segmentos"]), "de desarrollo", "")], ctx["presentacion"]))
    st.markdown("#### Impacto estimado")
    if r["horas_un_paso"] is None or r["horas_dos_pasos"] is None:
        st.caption("No hay tabla del brazo C en los datos de la página: no se puede estimar el impacto.")
    else:
        h0, h1, h2 = r["horas_sin_orden"], r["horas_un_paso"], r["horas_dos_pasos"]
        st.markdown(f"Ordenar la cola reduce el tiempo para encontrar el 80 % de las cajas sin pareja de ≈ **{F.horas(h0, 0)}** a ≈ **{F.horas(h1, 0)}** ({F.porcentaje(1 - h1 / h0, 0)} menos). "
                    f"Con auditoría previa de las celdas marcadas baja a ≈ {F.horas(h2, 0)} {E.etiqueta_muestra()}.", unsafe_allow_html=True)
        nombres = ["Revisión sin orden", "Solo cola (un paso)", "Auditoría + cola (dos pasos), en muestra"]
        df = pd.DataFrame({"Flujo": nombres, "Horas": [h0, h1, h2], "Texto": [f"≈ {F.horas(h, 0)}" for h in (h0, h1, h2)], "Detalle": [f"{F.decimal(h, 1)} h" for h in (h0, h1, h2)]})
        base = alt.Chart(df).encode(y=alt.Y("Flujo:N", sort=nombres, title=None, axis=alt.Axis(labelLimit=330, labelFontSize=12, labelOverlap=False)))
        barras = base.mark_bar(size=24).encode(x=alt.X("Horas:Q", title=f"Horas para encontrar el 80 % de las cajas sin pareja ({F.entero(segundos)} s por caja, supuesto)", scale=alt.Scale(domain=[0, h0 * 1.15]), axis=alt.Axis(tickCount=8)),
                                               color=alt.Color("Flujo:N", legend=None, scale=alt.Scale(domain=nombres, range=[GRIS_GRAFICO, E.TOKENS["primario"], "#7FA3CF"])),
                                               tooltip=[alt.Tooltip("Flujo:N", title="Flujo"), alt.Tooltip("Detalle:N", title="Horas")])
        texto = base.mark_text(align="left", dx=5, fontSize=12, fontWeight="bold", color=E.TOKENS["texto"]).encode(x="Horas:Q", text="Texto:N")
        _grafico((barras + texto).properties(height=180))
        st.caption(f"Estimación en muestra: {F.entero(r['cajas'])} cajas × fracción para el 80 % × {F.entero(segundos)} s por caja (supuesto, no medido). Fuente: f6_modelo_escogido.csv y f5_brazoC.csv.")
    st.markdown("#### Alertas")
    with st.container(border=True):
        for a in alertas_resumen(r, ctx["ciclistas"], ctx["perfil"]):
            c1, c2 = st.columns([7, 2], vertical_alignment="center")
            c1.markdown(E.fila_alerta(a["titulo"], a["texto"], a["tono"]), unsafe_allow_html=True)
            c2.page_link(ARCHIVO_PAGINA[a["seccion"]], label=a["seccion"], icon=":material/arrow_forward:")


# ------------------------------------------------------------------------------------------------------------ Cola de revisión
def _volver_a_20() -> None:
    st.session_state["presupuesto"] = 20


def _grafico_cobertura(D: dict[str, Any], r: dict[str, Any], presup: float, ref: str) -> None:
    curva = curvas_a_mostrar(D["curva"], ref).assign(nombre=lambda d: d["solucion"].map(nombre_curva_legible))
    presentes = set(curva["nombre"])
    orden = [i for i, n in enumerate(E.CURVAS_NOMBRES) if n in presentes]                     # la leyenda solo lista las curvas que se dibujan
    nombres, colores, rayas = ([lista[i] for i in orden] for lista in (E.CURVAS_NOMBRES, E.CURVAS_COLORES, E.CURVAS_RAYAS))
    x_enc = alt.X("presupuesto:Q", title="Fracción de cajas que se revisa", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1]))
    y_enc = alt.Y("recall:Q", title="Cajas sin pareja encontradas", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1]))
    trazo = alt.Stroke("nombre:N", title=None, scale=alt.Scale(domain=nombres, range=colores), legend=alt.Legend(orient="bottom", symbolType="stroke", symbolStrokeWidth=4, symbolSize=900))
    raya = alt.StrokeDash("nombre:N", scale=alt.Scale(domain=nombres, range=rayas), legend=None)
    # Una banda por curva con su color FIJO (sin codificar «nombre»): si la banda codifica el mismo campo con legend=None, Vega-Lite fusiona las leyendas y borra la de las líneas (F19-B7).
    bandas = [alt.Chart(curva[curva["nombre"] == n]).mark_area(opacity=0.13, color=c).encode(x=x_enc, y=alt.Y("lo:Q"), y2="hi:Q") for n, c in zip(nombres, colores) if (curva["nombre"] == n).any()]
    linea = alt.Chart(curva).mark_line(strokeWidth=3).encode(x=x_enc, y=y_enc, stroke=trazo, strokeDash=raya)
    azar = alt.Chart(pd.DataFrame({"presupuesto": [0, 1], "recall": [0, 1], "nombre": "Revisar al azar"})).mark_line(strokeDash=[2, 4], color=E.TOKENS["texto_suave"]).encode(x=x_enc, y=y_enc)
    etiqueta_azar = alt.Chart(pd.DataFrame({"presupuesto": [0.62], "recall": [0.56], "t": ["revisar al azar"]})).mark_text(color=E.TOKENS["texto_suave"], angle=315, fontSize=12).encode(x="presupuesto:Q", y="recall:Q", text="t:N")
    flujo_txt = "dos pasos" if r["flujo"] == "dos" else "un paso"
    punto = alt.Chart(pd.DataFrame({"presupuesto": [presup], "recall": [r["cobertura"]], "t": [f"Selección ({flujo_txt}): {F.porcentaje(presup, 0)} → {F.de_cada_100(r['cobertura'])}"]})).mark_point(
        size=160, filled=True, color=E.TOKENS["hueco"]).encode(x="presupuesto:Q", y="recall:Q", tooltip=[alt.Tooltip("t:N", title="")])
    _grafico(alt.layer(*bandas, linea, azar, etiqueta_azar, punto).properties(height=320))


def _panel_detalle(ctx: dict[str, Any], r: dict[str, Any], posicion: int) -> None:
    """Panel de detalle de la fila elegida de la cola: la misma explicación de «Explica una caja», con los datos de esa caja."""
    d = detalle_caja(r["top"], posicion, r["cajas_cola_total"], ctx["rangos"], ctx["ciclistas"])
    with st.container(border=True):
        st.markdown(f"**Caja en la posición {F.entero(d['posicion'])}** de {F.entero(d['cola_total'])}" + ("" if ctx["presentacion"] else f" · segmento {d['segmento']}"))
        _html(f'<p class="aud-probabilidad">{F.porcentaje(d["prob"])}</p><p class="aud-descripcion">probabilidad calibrada de no tener pareja en ninguna cámara</p>')
        st.markdown(texto_posicion(d["percentil"]))
        st.markdown(f"- Cámara: {d['camara']}\n- Distancia: {F.decimal(d['distancia'], 1)} m\n- Puntos del sensor superior: {F.entero(d['puntos_sup'])}\n- Puntos del LiDAR: {F.entero(d['puntos'])}\n"
                    f"- Clase: {d['clase']}\n- Tipo de caso: {d['tipo_caso']}")
        st.write(d["texto"])
        if d["advertencia_ciclista"]:
            c = ctx["ciclistas"]
            _html('<div class="aud-aviso"><strong>Ciclista:</strong> la regla es poco confiable (' + F.decimal(c["ciclista"], 3) + " de los casos encontrados contra " + F.decimal(c["peaton"], 3) +
                  " en peatones). Conviene revisar con más cuidado.</div>")


AYUDA_COLUMNAS = {COLUMNA_PROBABILIDAD: "Probabilidad calibrada de que la caja no tenga par en ninguna cámara", COLUMNA_PROBABILIDAD + " máxima": "Mayor probabilidad calibrada entre los fotogramas del objeto",
                  "Puntos sensor sup.": "Puntos del LiDAR superior dentro de la caja", "Clase": "En ciclistas la regla es poco confiable.", COLUMNA_FOTOGRAMAS: NOTA_FOTOGRAMAS}


def _config_columnas_cola(tabla: pd.DataFrame) -> dict[str, Any]:
    """Configuración de columnas de la tabla de la cola: ancho calculado con el encabezado y el contenido (ningún encabezado cortado), ayuda y formato de enteros."""
    anchos = F.anchos_columnas(tabla)
    cfg: dict[str, Any] = {}
    for c in tabla.columns:
        ayuda = AYUDA_COLUMNAS.get(c)
        if c in ("Posición", "Mejor posición") or c == COLUMNA_FOTOGRAMAS:
            cfg[c] = st.column_config.NumberColumn(c, format="%d", width=anchos[c], help=ayuda)
        else:
            cfg[c] = st.column_config.TextColumn(c, width=anchos[c], help=ayuda)
    return cfg


def cola(ctx: dict[str, Any]) -> None:
    D, K = ctx["D"], ctx["K"]
    encabezado("Cola de revisión", DESCRIPCION_PAGINA["Cola de revisión"])
    sol = K.get("nombre_curva", "solucion")
    segs = ["Todos"] + sorted(D["cajas"]["seg"].unique())
    st.session_state.setdefault("presupuesto", 20)
    st.session_state.setdefault("objetivo", 80)
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([1.5, 3.1, 1.8, 2.3, 1.2], vertical_alignment="bottom")
        elegido = c1.selectbox("Segmento", segs, key="segmento_cola")
        seg = "Todos" if elegido == segs[0] else elegido
        flujo_txt = c2.selectbox("Flujo", list(FLUJOS), index=1, key="flujo_cola", help="Un paso: se ordenan todas las cajas. Dos pasos: primero se auditan las celdas marcadas y la cola ordena el resto (en muestra).")
        flujo = FLUJOS[flujo_txt]
        sol_flujo = sol if flujo == "dos" or not (D["curva"]["solucion"] == CURVA_UN_PASO).any() else CURVA_UN_PASO
        modo = c3.radio("Modo de decisión", [MODO_PRESUPUESTO, MODO_OBJETIVO], horizontal=True, key="modo_cola", help="Presupuesto: se fija qué porcentaje de la cola se revisa. Meta: se fija qué porcentaje de las cajas sin pareja se quiere encontrar.")
        if modo == MODO_PRESUPUESTO:
            presup = c4.slider("Presupuesto (% de la cola)", 1, 100, key="presupuesto", format="%d") / 100
        else:
            objetivo = c4.slider("Meta (% de las cajas sin pareja)", 10, 99, key="objetivo", format="%d") / 100
            presup = round(curva_inversa(D["curva"], sol_flujo, objetivo), 3)
        c5.button("Volver al 20 %", on_click=_volver_a_20, width="stretch")
        f1, f2, f3, f5 = st.columns([1.7, 1.7, 1.5, 1.8], vertical_alignment="bottom")
        clases = f1.multiselect("Clase", [CLASE_NORMAL, CLASE_ADVERTENCIA], key="filtro_clase", placeholder="Todas")
        camaras = f2.multiselect("Cámara", list(CAMARAS.values()), key="filtro_camara", placeholder="Todas")
        agrupar = f3.toggle("Agrupar por objeto", key="agrupar_objeto", help="Una fila por objeto con su mejor posición. Es solo una vista: el número de cajas a revisar no cambia.")
        pop = f5.popover("Supuestos y confiabilidad")
        with pop:
            segundos = st.number_input("Segundos por revisión de una caja (supuesto, no medido)", min_value=1, max_value=600, value=SUPUESTO_SEGUNDOS, step=5, key="segundos")
    r = resumen_cola(D["cajas"], D["curva"], sol, seg, presup, segundos, flujo)
    if modo == MODO_OBJETIVO:
        st.caption(f"Para encontrar {F.porcentaje(objetivo, 0)} habría que revisar {F.porcentaje(presup, 0)} de la cola (según la curva guardada del flujo elegido).")
    _html(E.resultado(E.md_a_html(texto_resultado_cola(r))))
    _html(f'<p class="aud-esfuerzo">{E._e(texto_esfuerzo_cola(r))}{E.etiqueta_muestra() if flujo == "dos" else ""}</p>')
    with pop:
        lines = []
        if r["todos"]:
            lines.append(f"- **Intervalo de confianza (95 %, remuestreando segmentos):** dos pasos {F.porcentaje(r['ic_dos'][0], 0)} a {F.porcentaje(r['ic_dos'][1], 0)}; solo cola {F.porcentaje(r['ic_uno'][0], 0)} a {F.porcentaje(r['ic_uno'][1], 0)}.")
        else:
            lines.append("- **Un solo segmento:** no hay intervalo de confianza por segmentos.")
        lines.append("- **En muestra:** " + AVISO_EN_MUESTRA)
        lines.append("- **Qué se mide:** el porcentaje de la cola se calcula sobre el total de cajas en un paso y sobre la cola de celdas sanas en dos pasos; las celdas marcadas se auditan aparte.")
        st.markdown("\n".join(lines))
    tab_curva, tab_cola = st.tabs(["Curva de cobertura", "Cola de cajas"])
    with tab_curva:
        refs = [x for x in REFERENCIAS if D["curva"]["solucion"].str.startswith(x).any()]
        ref = "Ninguno"
        if refs:
            ref = st.columns([1.3, 3])[0].selectbox("Comparar con un modelo de referencia", ["Ninguno", *refs])
        if ref != "Ninguno":
            er = recall_en_presupuesto(D["curva"], f"{ref} (referencia), un paso (A)", presup)
            st.caption(f"{ref} como referencia (un paso, fuera de pliegue): unas {F.de_cada_100(er['recall'])} con el mismo porcentaje (intervalo {F.porcentaje(er['lo'], 0)} a {F.porcentaje(er['hi'], 0)}). No se eligió por simplicidad; ver Validación.")
        _grafico_cobertura(D, r, presup, ref)
    with tab_cola:
        con_filtro = bool(clases or camaras)
        top = r["top"]
        if agrupar:
            vista = tabla_por_objeto(top, ctx["presentacion"], ctx["rangos"], max_filas=len(top) if con_filtro else MAX_FILAS_COLA)
        else:
            vista = tabla_cola(top, r["cajas_cola_total"], ctx["rangos"], ctx["presentacion"], max_filas=len(top) if con_filtro else MAX_FILAS_COLA)
        vista = filtrar_cola(vista, clases, camaras)
        mostrada = vista.head(MAX_FILAS_COLA).reset_index(drop=True)
        unidad = "objetos" if agrupar else "cajas"
        n_total = len(vista) if con_filtro or agrupar else r["cajas_a_revisar"]
        st.caption((f"Filtrado: {F.entero(len(vista))} {unidad} de {F.entero(r['cajas_a_revisar'])} cajas de la cola. " if con_filtro else "") +
                   f"Se muestran las primeras {F.entero(len(mostrada))} de {F.entero(n_total)} {unidad}. Las cifras de arriba no cambian con los filtros." + (" " + NOTA_AGRUPADO if agrupar else ""))
        previa = st.session_state.get("tabla_cola")
        try:
            con_detalle = bool(previa and previa["selection"]["rows"])
        except (KeyError, TypeError, AttributeError):
            con_detalle = False
        izq, der = st.columns([3.2, 1.2], gap="medium") if con_detalle else (st.container(), None)       # el panel de detalle solo ocupa lugar cuando hay una fila elegida
        for ident in ("Marca de tiempo", "Objeto"):               # identificadores: texto, sin separador de miles
            if ident in mostrada.columns:
                mostrada[ident] = mostrada[ident].astype(str)
        cfg = _config_columnas_cola(mostrada)
        with izq:
            evento = st.dataframe(mostrada, key="tabla_cola", on_select="rerun", selection_mode="single-row", hide_index=True, width="stretch", row_height=30, height=min(40 + 31 * len(mostrada), 470), column_config=cfg)
        filas = list(evento.selection.rows) if evento is not None and getattr(evento, "selection", None) is not None else []
        col_pos = "Mejor posición" if agrupar else "Posición"
        if der is not None and filas and filas[0] < len(mostrada):
            with der:
                _panel_detalle(ctx, r, int(mostrada.iloc[filas[0]][col_pos]))
        elif not filas:
            st.caption("Seleccione una fila de la tabla para ver el detalle de esa caja.")
        if (mostrada.get("Clase", pd.Series(dtype=str)) == CLASE_ADVERTENCIA).any():
            st.caption("Hay ciclistas en esta lista: en ciclistas la regla es poco confiable y conviene revisarlos con más cuidado.")
        st.download_button("Descargar la cola (CSV)", mostrada.to_csv(index=False).encode("utf-8"), "cola_de_revision.csv", "text/csv", icon=":material/download:")


# ------------------------------------------------------------------------------------------------------------ Explica una caja
def _poner_ejemplo(nombre: str) -> None:
    e = EJEMPLOS_CAJA[nombre]
    st.session_state.update({"ex_pts": e["pts"], "ex_top": e["top"], "ex_dist": e["dist"], "ex_clase": e["clase"]})


def explica(ctx: dict[str, Any]) -> None:
    D = ctx["D"]
    encabezado("Explica una caja", DESCRIPCION_PAGINA["Explica una caja"])
    try:
        art = ctx["artefactos"]()
    except FileNotFoundError:
        st.error("Falta la solución congelada en data/06_models_ep3 (la crea scripts/ep3/f6_final.py).")
        return
    from waymo_evaluacion.ep3.inferencia import V16

    ref = D["cajas"]
    base = ref[V16].median().to_frame().T
    izq, der = st.columns([1, 1.5], gap="large")
    with izq:
        st.markdown("#### Parámetros de la caja")
        st.caption("Casos de ejemplo")
        for nombre in EJEMPLOS_CAJA:
            st.button(nombre, key=f"ej_{nombre}", on_click=_poner_ejemplo, args=(nombre,), width="stretch")
        pts = st.slider("Puntos del LiDAR en la caja", 1, 1000, 60, key="ex_pts")
        top_pts = st.slider("Puntos del sensor superior", 1, 1000, 50, key="ex_top")
        dist = st.slider("Distancia al sensor (m)", 1.0, 100.0, 25.0, step=1.0, format="%d", key="ex_dist")      # sin «25.00» con punto decimal: la página usa es-CL
        clase = st.radio("Clase", ["Peatón", "Ciclista"], horizontal=True, key="ex_clase")
    fila = base.copy()
    fila["num_lidar_points"], fila["num_top_lidar_points"], fila["distancia_m"] = pts, top_pts, dist
    fila["densidad_puntos"] = pts / fila["volumen_caja"]
    if "es_ciclista" in fila.columns:
        fila["es_ciclista"] = 1 if clase == "Ciclista" else 0
    s = float(art.puntuador.puntuar(fila)[0])
    p = float(art.calibrador.calibrar(np.array([s]))[0]) if art.calibrador is not None else float("nan")
    pc = percentil_en_cola(s, ref)
    with izq:
        st.caption(f"Puntaje de la regla: {F.decimal(s, 3)} (más alto = más arriba en la cola).")
    with der:
        _html(f'<p class="aud-probabilidad">{F.porcentaje(p)}</p><p class="aud-descripcion">probabilidad estimada de no tener pareja en ninguna cámara</p>')
        st.markdown(f"**{texto_posicion(pc)}**")
        st.write(explicacion_caja(top_pts, dist, clase == "Ciclista", pc, p))
        if clase == "Ciclista":
            c = ctx["ciclistas"]
            _html('<div class="aud-aviso"><strong>Ciclista:</strong> la regla es poco confiable (' + F.decimal(c["ciclista"], 3) + " de los casos encontrados contra " + F.decimal(c["peaton"], 3) +
                  " en peatones; " + F.entero(c["positivos"]) + " casos en " + F.entero(c["segmentos"]) + " segmentos). Conviene revisar estas cajas con más cuidado.</div>")
        ns = ctx["no_sup"]()
        if ns is not None:
            info = info_tipo_de_caso(tipo_de_caso(fila.copy(), ns), D["clusters"])
            st.markdown(f"**Tipo de caso:** {info['tipo_de_caso']}. En los 41 segmentos, ese tipo de caso tuvo {F.porcentaje(info['tasa'])} de cajas sin pareja "
                        f"(intervalo 95 % por segmentos {F.porcentaje(info['ic_lo'])} a {F.porcentaje(info['ic_hi'])}; {F.entero(info['cajas'])} cajas). Es una descripción (post hoc) y no mejora la predicción de la regla.")
        valores = np.unique(np.round(np.geomspace(1, 1000, 60)))
        dep = curva_dependencia(art.puntuador, fila, "num_top_lidar_points", valores)
        dep["prob"] = art.calibrador.calibrar(dep["score"].to_numpy(dtype=float)) if art.calibrador is not None else np.nan
        x_enc = alt.X("num_top_lidar_points:Q", scale=alt.Scale(type="log"), title="Puntos del sensor superior (escala logarítmica)", axis=alt.Axis(labelExpr="replace(format(datum.value, ','), ',', '.')"))
        y_enc = alt.Y("prob:Q", title="Probabilidad de no tener pareja", axis=alt.Axis(format="%"))
        marca = pd.DataFrame({"num_top_lidar_points": [top_pts], "prob": [p], "t": [f"Selección: {F.entero(top_pts)} puntos → {F.porcentaje(p)}"]})
        _grafico(alt.layer(alt.Chart(dep).mark_line(strokeWidth=3, color=E.TOKENS["primario"]).encode(x=x_enc, y=y_enc),
                           alt.Chart(marca).mark_point(size=150, filled=True, color=E.TOKENS["hueco"]).encode(x=x_enc, y=y_enc, tooltip=[alt.Tooltip("t:N", title="")])).properties(height=220))
        st.caption("Probabilidad estimada según los puntos del sensor superior; las demás variables quedan en la mediana de los datos. Es una ilustración del modelo, no una explicación causal.")


# ------------------------------------------------------------------------------------------------------------ Auditoría de cámaras
def _mapa_calor(m: pd.DataFrame, orden: list[str], solo_datos: bool) -> alt.LayerChart:
    n_seg = len(orden)
    x = alt.X("camara_corta:N", title="Cámara", sort=[str(c) for c in CAMARAS], axis=alt.Axis(labelAngle=0, orient="top", labelFontSize=12, titleFontSize=11))
    y = alt.Y("seg_corto:N", title="Segmento (6 últimos dígitos)", sort=orden, axis=alt.Axis(labelOverlap=False, labelFontSize=11))
    base = alt.Chart(m).encode(x=x, y=y)
    tip = [alt.Tooltip("seg:N", title="Segmento"), alt.Tooltip("camara:N", title="Cámara"), alt.Tooltip("pares:N", title="Cajas con pareja"), alt.Tooltip("cajas_rango:N", title="Cajas en el rango"), alt.Tooltip("estado:N", title="Estado")]
    capas = [base.transform_filter(~alt.datum.sin_datos).mark_rect(stroke="#FFFFFF", strokeWidth=1).encode(
        color=alt.Color("tasa:Q", scale=alt.Scale(domain=[0, 1], range=["#F2F5F9", E.TOKENS["primario"]]), legend=None), tooltip=tip)]
    if not solo_datos:
        capas += [base.transform_filter(alt.datum.sin_datos).mark_rect(fill="#D5DAE2", stroke="#FFFFFF", strokeWidth=1).encode(tooltip=tip),
                  base.transform_filter(alt.datum.sin_datos).mark_text(text="/ / / / / /", color="#7A8494", fontSize=9, baseline="middle")]
    capas += [base.transform_filter(alt.datum.hueco).mark_rect(fill=None, stroke=E.TOKENS["hueco"], strokeWidth=4), base.transform_filter(alt.datum.hueco).mark_text(text="X", color=E.TOKENS["hueco"], fontSize=18, fontWeight="bold")]
    return alt.layer(*capas).properties(height=max(300, 22 * n_seg))


def auditoria(ctx: dict[str, Any]) -> None:
    D = ctx["D"]
    la = D["lista_A"]
    min_cajas = ctx.get("min_cajas", 100)
    encabezado("Auditoría de cámaras", DESCRIPCION_PAGINA["Auditoría de cámaras"])
    izq, der = st.columns([4, 5], gap="medium")
    with izq:
        g1, g2 = st.columns(2)
        grupo = g1.selectbox("Grupo de segmentos", ["todos", "train", "test"], format_func=lambda g: {"todos": "Todos", "train": "Desarrollo", "test": "Test de EP2"}[g], key="grupo_aud")
        orden_txt = g2.selectbox("Orden", ["Con celdas marcadas primero", "Orden de los datos"], key="orden_aud")
        solo = st.toggle("Solo celdas con datos suficientes", key="solo_datos", help=f"Oculta las celdas con menos de {min_cajas} cajas en el rango (gris rayado).")
        m = matriz_calor(D["celdas"], min_cajas)
        if grupo != "todos":
            m = m[m["grupo"] == grupo]
        estado = np.where(m["hueco"], "Hueco", np.where(m["sin_datos"], f"Sin cajas o menos de {min_cajas} en el rango", "Celda sana"))
        m = m.assign(estado=estado, pares=np.where(m["sin_datos"], "sin datos suficientes", m["tasa"].map(lambda v: F.porcentaje(v, 0))), cajas_rango=m["n_rango"].map(F.entero),
                     camara_corta=m["camara"].str.split(" ").str[0])
        orden = orden_segmentos(m, orden_txt.startswith("Con celdas"))
        if solo:
            m = m[~m["sin_datos"]]
        _html(E.leyenda_mapa(min_cajas))
        with st.container(height=560, border=True):
            _grafico(_mapa_calor(m, orden, solo))
    with der:
        tarj = [("Segmentos analizados", F.entero(D["celdas"]["seg"].nunique()), "", ""), ("Celdas marcadas", F.entero(len(la)), "segmento × cámara con hueco", "hueco")]
        if "cajas_afectadas_poblacion_principal" in la.columns:
            tarj += [("Cajas en celdas marcadas", F.entero(la["cajas_afectadas_poblacion_principal"].sum()), "se atienden aparte", ""),
                     ("Cajas sin pareja en ellas", F.entero(la["positivos_afectados"].sum()), "del total de cajas sin pareja", "")]
        _html(E.metricas(tarj, True))
        st.markdown("#### Celdas marcadas (Lista A)")
        pres = lista_A_presentable(la)
        st.table(pres[[c for c in ("Segmento", "Cámara", "Cajas afectadas", "Sin pareja", "Acción sugerida") if c in pres.columns]].head(MAX_FILAS_LISTA_A))
        st.markdown("#### Detalle de las celdas marcadas")
        for _, f in lista_A_detalle(la).head(MAX_FILAS_LISTA_A).iterrows():
            st.markdown(f"- **{f.get('Segmento', '')} · {f.get('Cámara', '')}:** tasa {f.get('Tasa', '—')}, {f.get('En el rango', '—')} cajas en el rango; {f.get('Ubicación', '—')}, {str(f.get('Momento del día', '—')).lower()}; "
                        f"mediana de la cámara {f.get('Mediana de la cámara', '—')}, umbral de hueco {f.get('Umbral de hueco', '—')}.")
        st.download_button("Descargar celdas marcadas (CSV)", pres.to_csv(index=False).encode("utf-8"), "celdas_marcadas.csv", "text/csv", icon=":material/download:")
        st.markdown("#### Qué es un hueco")
        st.markdown("Un hueco es una cámara que, en un segmento, casi no tiene pares para las cajas que debería ver. **No se sabe por qué:** puede faltar el etiquetado 2D de esa cámara o faltar sus datos, y con estos archivos no se distingue. "
                    "Es una hipótesis para revisar, no una conclusión. Las celdas se llaman **marcadas** porque no existe una verdad externa que confirme cuáles son huecos reales.")


# ------------------------------------------------------------------------------------------------------------ Validación
def _barras_con_ic(df: pd.DataFrame, y: str, titulo_x: str, color: str | None = None, ancho_texto: int = 0) -> alt.LayerChart:
    """Barras horizontales de un efecto con su intervalo de confianza (``Mejora``, ``lo``, ``hi``) y una línea en cero."""
    d = df.assign(Texto=lambda t: [f"{F.decimal(v, 3)} (IC {F.decimal(lo, 3)} a {F.decimal(hi, 3)})" for v, lo, hi in zip(t["Mejora"], t["lo"], t["hi"])])
    orden = list(d[y])
    base = alt.Chart(d).encode(y=alt.Y(f"{y}:N", sort=orden, title=None, axis=alt.Axis(labelLimit=260, labelFontSize=12, labelOverlap=False)))
    veredictos = [v for v in ("mejora", "aporta", "no mejora", "no aporta") if "Veredicto" in d and v in set(d["Veredicto"])]
    col = alt.Color("Veredicto:N", legend=alt.Legend(orient="bottom", title=None), scale=alt.Scale(domain=veredictos, range=[E.TOKENS["primario"] if v in ("mejora", "aporta") else GRIS_GRAFICO for v in veredictos])) if "Veredicto" in d else alt.value(E.TOKENS["primario"])
    xe = alt.X("Mejora:Q", title=titulo_x, axis=alt.Axis(labelExpr=_eje_decimal(2)))
    barras = base.mark_bar(size=16, opacity=0.85).encode(x=xe, color=col, tooltip=[alt.Tooltip(f"{y}:N", title=""), alt.Tooltip("Texto:N", title="Efecto")])
    ic = base.mark_rule(strokeWidth=2, color=E.TOKENS["texto"]).encode(x=alt.X("lo:Q", title=titulo_x), x2="hi:Q")
    cero = alt.Chart(pd.DataFrame({"x": [0.0]})).mark_rule(color=E.TOKENS["texto_suave"], strokeDash=[3, 3]).encode(x="x:Q")
    return (barras + ic + cero).properties(height=max(150, 46 * len(d) + 30))


def _grafico_validacion(pref: str, datos: dict[str, pd.DataFrame]) -> None:
    if pref == "ie9" and "ie9" in datos:
        st.caption("Cambio de PR-AUC al optimizar los hiperparámetros frente a los valores por defecto (positivo = mejora). Línea negra: intervalo de confianza 95 % por segmentos.")
        _grafico(_barras_con_ic(datos["ie9"], "Modelo", "Cambio de PR-AUC (optimizado − por defecto)"))
    elif pref == "ie10" and "ie10" in datos:
        d = datos["ie10"].assign(Comparación=lambda t: t["Ensamble"] + " contra " + t["Mejor componente"].str.replace("_", " "))
        st.caption("Diferencia de AUC entre cada ensamble y su mejor componente (positivo = el ensamble aporta). Línea negra: intervalo de confianza 95 % por segmentos.")
        _grafico(_barras_con_ic(d, "Comparación", "Diferencia de AUC (ensamble − mejor componente)"))
    elif pref == "ie11" and "ie11" in datos:
        d = datos["ie11"].sort_values("AUC", ascending=False)
        orden = list(d["Candidato"])
        d = d.assign(Texto=lambda t: [f"AUC {F.decimal(a, 3)} (IC {F.decimal(lo, 3)} a {F.decimal(hi, 3)})" for a, lo, hi in zip(t["AUC"], t["lo"], t["hi"])])
        base = alt.Chart(d).encode(y=alt.Y("Candidato:N", sort=orden, title=None, axis=alt.Axis(labelFontSize=12, labelOverlap=False)))
        capas = [base.mark_rule(strokeWidth=3, color=E.TOKENS["primario"], opacity=0.55).encode(x=alt.X("lo:Q", title="AUC fuera de pliegue", scale=alt.Scale(domain=[0.55, 1]), axis=alt.Axis(labelExpr=_eje_decimal(2))), x2="hi:Q"),
                 base.mark_point(size=110, filled=True, color=E.TOKENS["primario"]).encode(x="AUC:Q", tooltip=[alt.Tooltip("Candidato:N", title=""), alt.Tooltip("Texto:N", title="Global")])]
        if "ie11_pliegues" in datos:
            pl = datos["ie11_pliegues"].assign(Texto=lambda t: [f"Pliegue {p}: AUC {F.decimal(a, 3)}" for p, a in zip(t["Pliegue"], t["AUC"])])
            capas.append(alt.Chart(pl).mark_point(size=45, color=GRIS_GRAFICO, shape="diamond", filled=True).encode(y=alt.Y("Candidato:N", sort=orden), x="AUC:Q", tooltip=[alt.Tooltip("Candidato:N", title=""), alt.Tooltip("Texto:N", title="")]))
        st.caption("Punto azul: AUC fuera de pliegue con su intervalo de confianza 95 % por segmentos. Rombos grises: AUC de cada pliegue (solo los candidatos que trae la copia de la página: Regla top, LR3 y XGB).")
        _grafico(alt.layer(*capas).properties(height=max(240, 34 * len(d) + 40)))
    elif pref == "nosup" and "nosup" in datos:
        d = datos["nosup"].assign(Texto=lambda t: [f"{F.porcentaje(v)} (IC {F.porcentaje(lo)} a {F.porcentaje(hi)}); {F.entero(n)} cajas" for v, lo, hi, n in zip(t["Tasa"], t["lo"], t["hi"], t["Cajas"])])
        base = alt.Chart(d).encode(y=alt.Y("Tipo de caso:N", title=None, axis=alt.Axis(labelFontSize=12)))
        st.caption("Proporción de cajas sin pareja en cada tipo de caso (k = 2), con intervalo de confianza 95 % por segmentos. Es descriptivo y post hoc.")
        _grafico((base.mark_bar(size=22, color=E.TOKENS["primario"], opacity=0.85).encode(x=alt.X("Tasa:Q", title="Proporción de cajas sin pareja", axis=alt.Axis(format="%", labelExpr="replace(format(datum.value * 100, '.0f'), '.', ',') + ' %'")),
                                                                                         tooltip=[alt.Tooltip("Tipo de caso:N", title=""), alt.Tooltip("Texto:N", title="")])
                  + base.mark_rule(strokeWidth=2, color=E.TOKENS["texto"]).encode(x="lo:Q", x2="hi:Q")).properties(height=110))
    elif pref == "posthoc" and "brazos" in datos:
        d = datos["brazos"].assign(Texto=lambda t: [F.porcentaje(v) for v in t["Fraccion"]])
        brazos = list(dict.fromkeys(d["Brazo"]))
        st.caption("Fracción de las cajas que hay que revisar para encontrar el 80 % de las cajas sin pareja (menos es mejor). En muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos.")
        _grafico(alt.Chart(d).mark_bar().encode(x=alt.X("Candidato:N", title=None, axis=alt.Axis(labelAngle=0, labelFontSize=12)), xOffset=alt.XOffset("Brazo:N", sort=brazos),
                                                y=alt.Y("Fraccion:Q", title="Fracción de cajas a revisar", axis=alt.Axis(format="%")),
                                                color=alt.Color("Brazo:N", title=None, sort=brazos, scale=alt.Scale(domain=brazos, range=[GRIS_GRAFICO, "#9DB7D5", E.TOKENS["primario"]]), legend=alt.Legend(orient="bottom")),
                                                tooltip=[alt.Tooltip("Candidato:N", title=""), alt.Tooltip("Brazo:N", title=""), alt.Tooltip("Texto:N", title="Fracción")]).properties(height=260))


def validacion(ctx: dict[str, Any]) -> None:
    ev = ctx["D"]["evidencia"]
    lecturas = lectura_evidencia(ev)
    datos = datos_validacion(ev)
    encabezado("Validación", DESCRIPCION_PAGINA["Validación"])
    tabs = st.tabs(list(NOMBRES_EVIDENCIA.values()))
    for tab, (pref, titulo) in zip(tabs, NOMBRES_EVIDENCIA.items()):
        with tab:
            st.markdown(f"**Lectura:** {lecturas.get(pref, '')}")
            hallados = {k: v for k, v in ev.items() if k.startswith(pref)}
            if not hallados:
                st.caption("Todavía no hay tablas para esta pestaña.")
            _grafico_validacion(pref, datos)
            if pref == "ie12" and "ie12__tabla_de_seleccion" in ev:
                t = ev["ie12__tabla_de_seleccion"]
                st.markdown("**Criterios de selección (O1 a O4)**")
                crit = pd.DataFrame({"Candidato": t["candidato"], "Simplicidad": t["nivel_simplicidad"].astype(int), "AUC": t["AUC"].map(lambda v: F.decimal(v, 3)), "O1": t["O1"].map({True: "sí", False: "no"}),
                                     "O2": t["O2"].map({True: "sí", False: "no"}), "O3": t["O3"].map({True: "sí", False: "no"}), "O4": t["O4"].map({True: "sí", False: "no"}),
                                     "Cumple O1, O3 y O4": t["cumple_O1_O3_O4"].map({True: "sí", False: "no"})})
                _tabla(crit)
                st.markdown("**Resultados de la solución elegida (fuera de pliegue)**")
                _tabla(tabla_resultados_clave(ctx["K"]), column_config={"Detalle": st.column_config.TextColumn("Detalle", width="large")}, alto_max=240)
            if hallados:
                with st.expander("Ver tabla completa"):
                    for k, v in hallados.items():
                        st.markdown(f"**{F.titulo_tabla(k)}**")
                        _tabla(F.tabla_legible(v, tabla=k))


# ------------------------------------------------------------------------------------------------------------ Puntuar datos nuevos
FORMATO_ARCHIVOS = pd.DataFrame([
    ("Archivo 1: lidar_box", "key.segment_context_name, key.frame_timestamp_micros, key.laser_object_id", "Segmento, fotograma y objeto de cada caja"),
    ("Archivo 1: lidar_box", "type", "Tipo de objeto (peatón o ciclista)"),
    ("Archivo 1: lidar_box", "box.center.x, box.center.y, box.center.z", "Centro de la caja 3D"),
    ("Archivo 1: lidar_box", "box.size.x, box.size.y, box.size.z, box.heading", "Dimensiones y rumbo de la caja"),
    ("Archivo 1: lidar_box", "num_lidar_points_in_box, num_top_lidar_points_in_box", "Puntos del LiDAR y del sensor superior dentro de la caja"),
    ("Archivo 2: camera_to_lidar_box_association", "key.camera_name y las tres llaves del archivo 1", "Cámara en la que la caja 3D tiene su par 2D; sin este archivo no hay auditoría de cámaras"),
], columns=["Archivo", "Columnas", "Uso"])


ETIQUETAS_RESUMEN = {"cajas_vru_poblacion_principal": "Cajas de peatones y ciclistas (población principal)", "cajas_en_celdas_con_hueco": "Cajas en celdas marcadas", "cajas_en_lista_B": "Cajas en la cola (Lista B)",
                     "celdas_con_hueco": "Celdas marcadas (Lista A)", "tiene_asociacion": "Archivo de asociación presente", "umbral_A": "Umbral de puntaje A", "umbral_B": "Umbral de puntaje B",
                     "positivos_total": "Cajas sin pareja", "positivos_en_celdas_con_hueco": "Cajas sin pareja en celdas marcadas"}


def _pedir_ejemplo() -> None:
    st.session_state["usar_ejemplo"] = True


def puntuar(ctx: dict[str, Any]) -> None:
    encabezado("Puntuar datos nuevos", DESCRIPCION_PAGINA["Puntuar datos nuevos"])
    try:
        art = ctx["artefactos"]()
    except FileNotFoundError:
        st.error("Falta la solución congelada en data/06_models_ep3 (la crea scripts/ep3/f6_final.py).")
        return
    st.markdown("#### Archivos de entrada")
    st.table(FORMATO_ARCHIVOS)
    c1, c2 = st.columns(2)
    f1 = c1.file_uploader("Archivo 1 (obligatorio): lidar_box", type="parquet")
    f2 = c2.file_uploader("Archivo 2 (opcional): camera_to_lidar_box_association", type="parquet")
    cajas = ctx["D"].get("cajas")
    seg_ejemplo = None
    if cajas is not None:
        la = ctx["D"].get("lista_A")
        seg_ejemplo = str(la["segmento"].iloc[0]) if la is not None and len(la) else str(cajas["seg"].iloc[0])
        st.button("Usar un segmento de desarrollo de ejemplo", on_click=_pedir_ejemplo, help="Reconstruye un lidar_box mínimo desde las variables derivadas de un segmento de desarrollo (no son datos crudos de Waymo).")
    if f1 is not None:
        st.session_state["usar_ejemplo"] = False
    from waymo_evaluacion.ep3.inferencia import puntuar_segmento

    if f1 is None and not (st.session_state.get("usar_ejemplo") and seg_ejemplo):
        st.caption("Sin archivos cargados.")
        return
    if f1 is not None:
        try:
            lidar = pd.read_parquet(f1)
            asoc = pd.read_parquet(f2) if f2 is not None else None
        except Exception:  # noqa: BLE001 - archivo ilegible: mensaje claro
            st.error("No se pudo leer el archivo: no parece un parquet válido.")
            return
        problema = validar_lidar_box(lidar) or (validar_asociacion(asoc) if asoc is not None else None)
        if problema:
            st.error(problema)
            return
    else:
        lidar, asoc = ejemplo_lidar_box(cajas, seg_ejemplo), None
        st.caption(f"Ejemplo: segmento de desarrollo {seg_ejemplo if not ctx['presentacion'] else '(oculto)'}, reconstruido desde las variables derivadas (no son datos crudos de Waymo). "
                   "Sin archivo de asociación no hay auditoría de cámaras; las celdas marcadas de este segmento figuran en «Auditoría de cámaras».")
    with st.spinner("Puntuando el segmento…"):
        try:
            res = puntuar_segmento(lidar, asoc, art)
        except (KeyError, ValueError) as e:
            st.error(f"No se pudo puntuar el archivo: {e}")
            return
    for a in res.advertencias:
        st.warning(a)
    _html(E.metricas([("Cajas puntuadas", F.entero(len(res.cajas)), "peatones y ciclistas, población principal", ""), ("Celdas marcadas", F.entero(len(res.lista_A)), "Lista A", "hueco"),
                      ("Cajas en la cola", F.entero(len(res.lista_B)), "Lista B, celdas sanas", ""), ("Cajas en celdas marcadas", F.entero(res.resumen.get("cajas_en_celdas_con_hueco", 0)), "se atienden aparte", "")], ctx["presentacion"]))
    resumen_t = pd.DataFrame({"Medida": [ETIQUETAS_RESUMEN.get(k, F.nombre_columna(k)) for k in res.resumen], "Valor": [("sí" if v is True else "no" if v is False else F.entero(v) if isinstance(v, (int, float)) and float(v).is_integer() else F.decimal(v, 3) if isinstance(v, float) else "—" if v is None else str(v))
                                                                                         for v in res.resumen.values()]})
    st.markdown("#### Resumen")
    _tabla(resumen_t, alto_max=330)
    st.markdown("#### Lista A: celdas marcadas")
    _tabla(F.tabla_legible(res.lista_A), alto_max=200)
    st.markdown("#### Lista B: cola de cajas (celdas sanas)")
    lb = ocultar_identificadores(res.lista_B, ctx["presentacion"])
    _tabla(F.tabla_legible(lb.head(500)))
    d1, d2 = st.columns(2)
    d1.download_button("Descargar Lista A (CSV)", res.lista_A.to_csv(index=False).encode("utf-8"), "lista_A_nueva.csv", "text/csv", icon=":material/download:")
    d2.download_button("Descargar Lista B (CSV)", lb.to_csv(index=False).encode("utf-8"), "lista_B_nueva.csv", "text/csv", icon=":material/download:")


# ------------------------------------------------------------------------------------------------------------ Ética y límites
def etica(ctx: dict[str, Any]) -> None:
    c = ctx["ciclistas"]
    encabezado("Ética y límites", DESCRIPCION_PAGINA["Ética y límites"])
    claves = {t.get("titulo", ""): t.get("valor", "") for t in ctx["K"].get("tarjetas", [])}
    auc, recall, cap = claves.get("AUC fuera de fold", ""), claves.get("Recall en el punto A", ""), claves.get("Captura al revisar el 20 %", "")
    desempeno = (f"Fuera de pliegue: AUC {auc}, recall en el punto A {recall} y {cap} de las cajas sin pareja al revisar el 20 % de las cajas (intervalos en «Validación»). " if auc else "") + \
        "Todas las cifras son en muestra: 41 segmentos, detector ajustado con los mismos datos y sin prueba ciega."
    izq, der = st.columns(2, gap="large")
    with izq:
        _html(E.ficha("Propósito", "Ordenar las cajas 3D de peatones y ciclistas para que una persona revise primero las que más probablemente no tienen su par 2D de cámara, y avisar qué cámaras tienen huecos. "
                      "Decide siempre una persona: la solución no etiqueta ni borra nada y nunca debe usarse para descartar cajas sin revisarlas. No es una prueba de seguridad del vehículo: mide si una caja 3D tiene pareja 2D, no si el peatón fue bien detectado."))
        _html(E.ficha("Datos y licencia", "Waymo Open Dataset v2, 41 segmentos de desarrollo. El conjunto es de uso no comercial y sus datos no se redistribuyen. El trabajo es académico (curso MLY1101)."))
        _html(E.ficha("Desempeño", desempeno))
    with der:
        _html(E.ficha("Límites conocidos", f"La regla es poco confiable para ciclistas ({F.decimal(c['ciclista'], 3)} contra {F.decimal(c['peaton'], 3)} en peatones; {F.entero(c['positivos'])} casos en {F.entero(c['segmentos'])} segmentos). "
                      "Hay más segmentos de día que de noche y tres ubicaciones. Un hueco es una hipótesis para revisar, no una conclusión; los hallazgos post hoc son hipótesis."))
        _html(E.ficha("Consideraciones éticas", "Las tablas locales tienen identificadores de objeto y marcas de tiempo. El modo presentación los oculta en pantalla y en las descargas. Nada se guarda ni se envía."))
        _html(E.ficha("Dónde corre", "Solo en este equipo (localhost), sin conexión a internet. No debe exponerse en una red sin autenticación."))


# ------------------------------------------------------------------------------------------------------------ Ayuda y glosario
def ayuda(ctx: dict[str, Any]) -> None:
    encabezado("Ayuda y glosario", DESCRIPCION_PAGINA["Ayuda y glosario"])
    st.markdown("**Flujo de tres capas:** (1) el detector de huecos marca las celdas segmento × cámara donde casi ninguna caja tiene pareja y se atienden aparte; (2) la regla «menos puntos del sensor superior» ordena las cajas restantes en una cola; "
                "(3) una persona revisa y decide.")
    st.markdown("#### Uso")
    st.markdown("- El **rol** (pie de la barra lateral) cambia la página que se abre y la alerta que se muestra primero.\n"
                "- **Cola de revisión:** se elige el segmento, el flujo y el presupuesto (o la meta); al seleccionar una fila se ve el detalle de la caja; la lista se descarga en CSV.\n"
                "- **Auditoría de cámaras:** muestra las celdas marcadas como hueco y qué hacer con ellas.\n"
                "- El **modo presentación** oculta los identificadores y agranda la letra y las métricas.")
    st.markdown("#### Glosario")
    _html(E.tabla_html(GLOSARIO, ("Término", "Definición")))
    st.markdown("#### Preguntas frecuentes")
    for q, a in preguntas_frecuentes(ctx["D"]["evidencia"].get("posthoc__equidad")):
        with st.expander(q):
            st.write(a)


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
        st.error(f"No se encuentran los datos de la página ({ctx['falta']}). Se generan con: python scripts/ep3/f7_preparar_app.py")
        return
    SECCION_FN[seccion](ctx)
