"""Secciones de la página «Auditor de etiquetas 3D». Cada función recibe el contexto ``ctx`` (datos, perfil, modo presentación, cachés) y dibuja una sección.

Los números salen de ``waymo_evaluacion.ep3.app_logica`` (lógica probada) y se formatean con ``waymo_evaluacion.ep3.formato`` (es-CL). Sin conexiones externas.
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
    ACCIONES_PERFIL, AVISO_CORTO, AVISO_EN_MUESTRA, CAMARAS, CLASE_ADVERTENCIA, GLOSARIO, REFERENCIAS, SUPUESTO_SEGUNDOS, curva_inversa, curvas_a_mostrar, explicacion_caja, formatear_kpi,
    info_tipo_de_caso, inicio_resumen, lectura_evidencia, lista_A_presentable, matriz_calor, nombre_curva_legible, ocultar_identificadores, percentil_en_cola, preguntas_frecuentes,
    recall_en_presupuesto, resumen_cola, tabla_cola, texto_resultado_cola, tipo_de_caso, validar_asociacion, validar_lidar_box, curva_dependencia,
)

NOMBRES_EVIDENCIA = {"ie9": "Hiperparámetros", "ie10": "Ensambles", "ie11": "Generalización", "ie12": "Selección", "nosup": "No supervisado", "posthoc": "En muestra"}
MODO_PRESUPUESTO = "Tengo un presupuesto (% de la cola)"
MODO_OBJETIVO = "Quiero encontrar X % de las cajas sin pareja"
ESTILO_GRAFICO = {"font": "sans-serif"}


def _html(x: str) -> None:
    st.markdown(x, unsafe_allow_html=True)


def aviso_en_muestra() -> None:
    """Aviso compacto y SIEMPRE visible (no un tooltip), con el texto completo en un expander."""
    st.warning(AVISO_CORTO)
    with st.expander("¿Qué significa?"):
        st.write(AVISO_EN_MUESTRA)
        st.write("Por eso las cifras de este flujo son optimistas y no deben leerse como una prueba ciega. La validación con segmentos nuevos está preparada y sellada, y todavía no se ha ejecutado.")


def _ir(seccion: str) -> None:
    st.session_state["seccion"] = seccion


# ------------------------------------------------------------------------------------------------------------ Inicio
def inicio(ctx: dict[str, Any]) -> None:
    D, K = ctx["D"], ctx["K"]
    r = inicio_resumen(D, st.session_state.get("segundos", SUPUESTO_SEGUNDOS))
    st.markdown("**Ordena las cajas 3D de peatones y ciclistas para que una persona revise primero las que más probablemente no tienen su par en ninguna cámara, y avisa antes qué cámaras tienen huecos.**")
    aviso_en_muestra()
    tarjetas = [("Cajas analizadas", F.entero(r["cajas"]), f"en {F.entero(r['segmentos'])} segmentos", ""),
                ("Cajas sin pareja", F.porcentaje(r["prevalencia"]), "no tienen par en ninguna cámara", ""),
                ("Cámaras con hueco detectadas", F.entero(r["celdas_marcadas"]), f"celdas (segmento × cámara) en {F.entero(r['segmentos_con_hueco'])} segmentos", "hueco")]
    if r["horas_ahorradas"] is not None:
        tarjetas.append(("Horas que se ahorrarían", f"≈ {F.horas(r['horas_ahorradas'], 0)}", "estimación: encontrar el 80 % frente a revisar sin orden; en muestra", "aviso"))
    _html(E.tarjetas(tarjetas))
    st.markdown("#### Cómo funciona")
    _html(E.pasos([("Auditar las cámaras", "Una celda (segmento × cámara) donde casi ninguna caja tiene pareja se marca y se atiende aparte, antes de revisar caja por caja."),
                   ("Revisar la cola", "Las cajas de las celdas sanas se ordenan: primero las que más probablemente no tienen pareja."),
                   ("Una persona decide", "La página solo ordena y avisa. Nunca etiqueta ni descarta nada por sí sola.")]))
    st.markdown("#### Empiece por aquí")
    acciones = ACCIONES_PERFIL[ctx["perfil"]]
    cols = st.columns(len(acciones))
    for c, (sec, texto) in zip(cols, acciones):
        c.button(texto, key=f"accion_{sec}", on_click=_ir, args=(sec,), type="primary" if sec == acciones[0][0] else "secondary", width="stretch")
    with st.expander("Primeros pasos"):
        st.markdown("1. Abra **Cola de revisión**, deje el presupuesto en 20 % y mire cuántas cajas sin pareja se encontrarían.\n"
                    "2. Abra **Auditoría de cámaras** para ver las celdas con hueco y qué hacer con ellas.\n"
                    "3. Si una caja le llama la atención, pruebe **Explica una caja**.\n"
                    "4. Ante cualquier término nuevo, vaya a **Ayuda y glosario**.")
    with st.expander("Resultados técnicos (fuera de fold, intervalo de confianza 95 % por segmentos)"):
        _html(E.tarjetas([(t["titulo"], formatear_kpi(t["valor"]), formatear_kpi(t.get("ic", "")), "") for t in K.get("tarjetas", [])]))
        st.caption(K.get("solucion_final", ""))


# ------------------------------------------------------------------------------------------------------------ Auditoría
def auditoria(ctx: dict[str, Any]) -> None:
    D = ctx["D"]
    la = D["lista_A"]
    st.markdown("Cada celda muestra la proporción de cajas dentro del rango de una cámara que tienen pareja. Una celda se **marca como hueco** cuando esa proporción es menor al 25 % de lo normal de la cámara y hay al menos 100 cajas.")
    tarj = [("Segmentos analizados", F.entero(D["celdas"]["seg"].nunique()), "", ""), ("Celdas marcadas", F.entero(len(la)), "segmento × cámara con hueco", "hueco")]
    if "cajas_afectadas_poblacion_principal" in la.columns:
        tarj += [("Cajas en celdas marcadas", F.entero(la["cajas_afectadas_poblacion_principal"].sum()), "se atienden aparte", ""), ("Cajas sin pareja en ellas", F.entero(la["positivos_afectados"].sum()), "de las cajas sin pareja del total", "aviso")]
    _html(E.tarjetas(tarj))
    grupo = st.radio("Grupo de segmentos", ["todos", "train", "test"], horizontal=True, format_func=lambda g: {"todos": "Todos", "train": "Desarrollo", "test": "Test de EP2"}[g])
    m = matriz_calor(D["celdas"])
    if grupo != "todos":
        m = m[m["grupo"] == grupo]
    m = m.assign(estado=np.where(m["hueco"], "Celda marcada como hueco", "Celda sana"), pares=m["tasa"].map(lambda v: F.porcentaje(v, 0)), cajas_rango=m["n_rango"].map(F.entero))
    base = alt.Chart(m).encode(x=alt.X("camara:N", title=None, sort=list(CAMARAS.values()), axis=alt.Axis(labelAngle=0)), y=alt.Y("seg:N", title="Segmento", sort=None))
    mapa = base.mark_rect(stroke="#FFFFFF", strokeWidth=1).encode(color=alt.Color("tasa:Q", scale=alt.Scale(domain=[0, 1], range=["#F2F5F9", "#1D4E89"]), title="Cajas con pareja", legend=alt.Legend(format=".0%")),
                                                                 tooltip=[alt.Tooltip("seg:N", title="Segmento"), alt.Tooltip("camara:N", title="Cámara"), alt.Tooltip("pares:N", title="Cajas con pareja"),
                                                                          alt.Tooltip("cajas_rango:N", title="Cajas en el rango"), alt.Tooltip("estado:N", title="Estado")])
    marco = base.transform_filter(alt.datum.hueco).mark_rect(fill=None, stroke=E.TOKENS["hueco"], strokeWidth=4)
    marcas = base.transform_filter(alt.datum.hueco).mark_text(text="X", color=E.TOKENS["hueco"], fontSize=18, fontWeight="bold")
    st.altair_chart((mapa + marco + marcas).properties(height=max(300, 16 * m["seg"].nunique())).configure_view(strokeWidth=0), width="stretch")
    st.caption("Cómo leerlo: azul oscuro = casi todas las cajas de esa cámara tienen pareja; casi blanco = casi ninguna. Un contorno rojo con una X marca una celda con hueco.")
    st.markdown("#### Celdas marcadas (Lista A)")
    st.dataframe(lista_A_presentable(la), width="stretch", hide_index=True)
    st.download_button("Descargar celdas marcadas (CSV)", lista_A_presentable(la).to_csv(index=False).encode("utf-8"), "celdas_marcadas.csv", "text/csv", icon=":material/download:")
    with st.expander("Qué es un hueco", expanded=True):
        st.markdown("Un hueco es una cámara que, en un segmento, casi no tiene pares para las cajas que debería ver. **No se sabe por qué:** puede faltar el etiquetado 2D de esa cámara o faltar sus datos, y con estos archivos no se distingue. "
                    "Es una hipótesis para revisar, no una conclusión. Las celdas se llaman **marcadas** porque no existe una verdad externa que confirme cuáles son huecos reales.")


# ------------------------------------------------------------------------------------------------------------ Cola
def _volver_a_20() -> None:
    st.session_state["presupuesto"] = 20


def cola(ctx: dict[str, Any]) -> None:
    D, K = ctx["D"], ctx["K"]
    aviso_en_muestra()
    sol = K.get("nombre_curva", "solucion")
    segs = ["Todos los segmentos"] + sorted(D["cajas"]["seg"].unique())
    c1, c2 = st.columns([1, 2])
    elegido = c1.selectbox("Segmento", segs)
    seg = "Todos" if elegido == segs[0] else elegido
    modo = c2.radio("¿Cómo quiere decidir?", [MODO_PRESUPUESTO, MODO_OBJETIVO], horizontal=True, key="modo_cola")
    st.session_state.setdefault("presupuesto", 20)
    st.session_state.setdefault("objetivo", 80)
    with st.expander("Supuestos"):
        segundos = st.number_input("Segundos por revisión de una caja (supuesto, no medido)", min_value=1, max_value=600, value=SUPUESTO_SEGUNDOS, step=5, key="segundos")
    if modo == MODO_PRESUPUESTO:
        b1, b2 = st.columns([4, 1])
        presup = b1.slider("Porcentaje de la cola que se revisa", 1, 100, key="presupuesto", format="%d") / 100
        b2.button("Volver al 20 %", on_click=_volver_a_20, width="stretch")
    else:
        objetivo = st.slider("Quiero encontrar este porcentaje de las cajas sin pareja", 10, 99, key="objetivo", format="%d") / 100
        presup = round(curva_inversa(D["curva"], sol, objetivo), 3)
        st.caption(f"Para encontrar {F.porcentaje(objetivo, 0)} habría que revisar {F.porcentaje(presup, 0)} de la cola (según la curva guardada).")
    r = resumen_cola(D["cajas"], D["curva"], sol, seg, presup, segundos)
    _html(E.resultado(E.md_a_html(texto_resultado_cola(r))))
    _html(E.tarjetas([("Cajas a revisar", F.entero(r["cajas_a_revisar"]), f"de {F.entero(r['cajas_cola_total'])} en la cola", ""), ("Tiempo estimado", F.horas(r["horas"], 1), f"con {F.entero(segundos)} s por caja (estimación)", "aviso"),
                      ("Celdas marcadas", F.entero(len(D["lista_A"])) if r["todos"] else "—", "se atienden aparte de la cola", "hueco")]))
    with st.expander("¿Qué tan confiable es esto?"):
        a = recall_en_presupuesto(D["curva"], "Solución elegida, un paso (A)", presup)["recall"] if D["curva"]["solucion"].eq("Solución elegida, un paso (A)").any() else None
        txt = (f"- **Intervalo de confianza:** {F.porcentaje(r['ic_lo'], 0)} a {F.porcentaje(r['ic_hi'], 0)} (95 %, remuestreando segmentos)." if r["todos"] else
               "- **Un solo segmento:** no hay intervalo de confianza por segmentos.")
        st.markdown(txt + "\n- **En muestra:** " + AVISO_EN_MUESTRA +
                    ("\n- **Un paso o dos pasos:** con un paso (solo ordenar la cola) y el mismo porcentaje se encontrarían unas " + F.de_cada_100(a) + " cajas sin pareja; con dos pasos (auditar las celdas marcadas y ordenar el resto), "
                     + F.de_cada_100(r["cobertura"]) + ". El porcentaje se mide sobre el total de cajas en un paso y sobre la cola de celdas sanas en dos pasos." if a is not None else "") +
                    "\n- La ganancia del flujo en dos pasos sale de 2 celdas cámara × segmento, una de ellas en el segmento donde se descubrió el hueco.")
    refs = [x for x in REFERENCIAS if D["curva"]["solucion"].str.startswith(x).any()]
    ref = "Ninguno"
    if refs:
        with st.expander("Comparar con un modelo de referencia"):
            ref = st.selectbox("Modelo de referencia", ["Ninguno", *refs])
    curva = curvas_a_mostrar(D["curva"], ref).assign(nombre=lambda d: d["solucion"].map(nombre_curva_legible))
    if ref != "Ninguno":
        er = recall_en_presupuesto(D["curva"], f"{ref} (referencia), un paso (A)", presup)
        st.caption(f"{ref} como referencia (un paso, fuera de fold): se encontrarían unas {F.de_cada_100(er['recall'])} con el mismo porcentaje (intervalo {F.porcentaje(er['lo'], 0)} a {F.porcentaje(er['hi'], 0)}). No se eligió por simplicidad; ver Evidencia.")
    x_enc = alt.X("presupuesto:Q", title="Fracción de cajas que se revisa", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1]))
    y_enc = alt.Y("recall:Q", title="Cajas sin pareja encontradas", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1]))
    color = alt.Color("nombre:N", title=None, legend=alt.Legend(orient="bottom"))
    banda = alt.Chart(curva).mark_area(opacity=0.15).encode(x=x_enc, y=alt.Y("lo:Q"), y2="hi:Q", color=color)
    linea = alt.Chart(curva).mark_line(strokeWidth=3).encode(x=x_enc, y=y_enc, color=color)
    azar = alt.Chart(pd.DataFrame({"presupuesto": [0, 1], "recall": [0, 1], "nombre": "Revisar al azar"})).mark_line(strokeDash=[6, 4], color="#4A5568").encode(x=x_enc, y=y_enc)
    etiqueta_azar = alt.Chart(pd.DataFrame({"presupuesto": [0.62], "recall": [0.56], "t": ["revisar al azar"]})).mark_text(color="#4A5568", angle=315, fontSize=12).encode(x="presupuesto:Q", y="recall:Q", text="t:N")
    punto = alt.Chart(pd.DataFrame({"presupuesto": [presup], "recall": [r["cobertura"]], "t": [f"Su elección: {F.porcentaje(presup, 0)} → {F.de_cada_100(r['cobertura'])}"]})).mark_point(size=200, filled=True, color=E.TOKENS["hueco"]).encode(
        x="presupuesto:Q", y="recall:Q", tooltip=[alt.Tooltip("t:N", title="")])
    st.altair_chart((banda + linea + azar + etiqueta_azar + punto).properties(height=340), width="stretch")
    st.markdown("#### Cola de cajas a revisar")
    tabla = tabla_cola(r["top"], r["cajas_cola_total"], ctx["rangos"], ctx["presentacion"])
    cfg = {"Prioridad": st.column_config.ProgressColumn("Prioridad", min_value=0, max_value=100, format="%d", help="100 = primera de la cola; baja hasta 0 en la última."),
           "Clase": st.column_config.TextColumn("Clase", help="La regla es poco confiable para ciclistas.")}
    st.dataframe(tabla, column_config=cfg, width="stretch", hide_index=True)
    if (tabla.get("Clase", pd.Series(dtype=str)) == CLASE_ADVERTENCIA).any():
        st.info("Hay ciclistas en esta lista: en ciclistas la regla es poco confiable; revíselos con más cuidado.")
    st.download_button("Descargar la cola (CSV)", tabla.to_csv(index=False).encode("utf-8"), "cola_de_revision.csv", "text/csv", icon=":material/download:")


# ------------------------------------------------------------------------------------------------------------ Explica una caja
def explica(ctx: dict[str, Any]) -> None:
    D = ctx["D"]
    try:
        art = ctx["artefactos"]()
    except FileNotFoundError:
        st.error("Falta la solución congelada en data/06_models_ep3 (la crea scripts/ep3/f6_final.py).")
        return
    from waymo_evaluacion.ep3.inferencia import V16

    st.markdown("Pocos puntos del sensor y mucha distancia suelen significar que la caja está lejos o tapada, y es más probable que ninguna cámara la haya etiquetado. Mueva los controles y vea qué pasa.")
    ref = D["cajas"]
    base = ref[V16].median().to_frame().T
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1.4])
    pts = c1.slider("Puntos del LiDAR en la caja", 1, 1000, 60)
    top_pts = c2.slider("Puntos del sensor superior", 1, 1000, min(pts, 50))
    dist = c3.slider("Distancia al sensor (m)", 1.0, 100.0, 25.0)
    clase = c4.radio("Clase", ["Peatón", "Ciclista"])
    fila = base.copy()
    fila["num_lidar_points"], fila["num_top_lidar_points"], fila["distancia_m"] = pts, top_pts, dist
    fila["densidad_puntos"] = pts / fila["volumen_caja"]
    if "es_ciclista" in fila.columns:
        fila["es_ciclista"] = 1 if clase == "Ciclista" else 0
    s = float(art.puntuador.puntuar(fila)[0])
    p = float(art.calibrador.calibrar(np.array([s]))[0]) if art.calibrador is not None else float("nan")
    pc = percentil_en_cola(s, ref)
    _html(f'<div class="aud-bloque"><p class="aud-grande">{F.porcentaje(p)}</p><p class="aud-eslogan">probabilidad estimada de no tener pareja en ninguna cámara</p></div>')
    _html(E.tarjetas([("Lugar en la cola", f"entre el {F.porcentaje(pc, 0)} primero", "0 % = primera de la cola; 100 % = última", "")]))
    st.markdown(explicacion_caja(top_pts, dist, clase == "Ciclista", pc, p))
    if clase == "Ciclista":
        _html('<div class="aud-caja-advertencia"><strong>Advertencia:</strong> en ciclistas la regla es poco confiable (' + F.decimal(ctx["ciclistas"]["ciclista"], 3) + " de los casos encontrados contra " + F.decimal(ctx["ciclistas"]["peaton"], 3) +
              " en peatones; " + F.entero(ctx["ciclistas"]["positivos"]) + " casos en " + F.entero(ctx["ciclistas"]["segmentos"]) + " segmentos). Revise estas cajas con más cuidado.</div>")
    ns = ctx["no_sup"]()
    if ns is not None:
        info = info_tipo_de_caso(tipo_de_caso(fila.copy(), ns), D["clusters"])
        st.info(f"**Tipo de caso:** {info['tipo_de_caso']}. En los 41 segmentos, ese tipo de caso tuvo {F.porcentaje(info['tasa'])} de cajas sin pareja "
                f"(intervalo 95 % por segmentos {F.porcentaje(info['ic_lo'])} a {F.porcentaje(info['ic_hi'])}; {F.entero(info['cajas'])} cajas). Es una descripción (post hoc) y no mejora la predicción de la regla.")
    with st.expander("Detalle técnico"):
        st.write(f"Puntaje de la regla: {F.decimal(s, 3)} (más alto = más arriba en la cola).")
        dep = curva_dependencia(art.puntuador, fila, "num_lidar_points", np.unique(np.round(np.geomspace(1, 1000, 60))))
        st.altair_chart(alt.Chart(dep).mark_line(strokeWidth=3).encode(x=alt.X("num_lidar_points:Q", scale=alt.Scale(type="log"), title="Puntos del LiDAR (escala logarítmica)"), y=alt.Y("score:Q", title="Puntaje")), width="stretch")
        st.caption("Las demás variables se dejan en la mediana de los datos. Es una ilustración del modelo, no una explicación causal.")


# ------------------------------------------------------------------------------------------------------------ Evidencia
def evidencia(ctx: dict[str, Any]) -> None:
    ev = ctx["D"]["evidencia"]
    lecturas = lectura_evidencia(ev)
    st.markdown("Cada tabla sale de un resultado guardado de EP3. Lo post hoc lo dice su texto.")
    tabs = st.tabs(list(NOMBRES_EVIDENCIA.values()))
    for tab, (pref, titulo) in zip(tabs, NOMBRES_EVIDENCIA.items()):
        with tab:
            st.markdown(f"**Lectura:** {lecturas.get(pref, '')}")
            hallados = {k: v for k, v in ev.items() if k.startswith(pref)}
            if not hallados:
                st.info("Todavía no hay tablas para esta pestaña.")
            for i, (k, v) in enumerate(hallados.items()):
                with st.expander(F.titulo_tabla(k), expanded=(i == 0)):
                    st.dataframe(F.tabla_legible(v), width="stretch", hide_index=True)


# ------------------------------------------------------------------------------------------------------------ Ética
def etica(ctx: dict[str, Any]) -> None:
    c = ctx["ciclistas"]
    tarjetas = [
        ("Decide una persona", "La solución ordena y avisa; no etiqueta ni borra nada. Nunca se debe usar para descartar cajas sin revisarlas. No es una prueba de seguridad del vehículo: mide si una caja 3D tiene pareja 2D, no si el peatón fue bien detectado."),
        ("Licencia y uso académico", "El Waymo Open Dataset es de uso no comercial y sus datos no se redistribuyen. Esta página sirve para el trabajo académico del curso."),
        ("Privacidad e identificadores", "Las tablas locales tienen identificadores de objeto y marcas de tiempo. El modo presentación los oculta en pantalla y en las descargas. Nada se guarda ni se envía."),
        ("Sesgos y ciclistas", f"La regla es poco confiable para ciclistas ({F.decimal(c['ciclista'], 3)} contra {F.decimal(c['peaton'], 3)} en peatones; {F.entero(c['positivos'])} casos en {F.entero(c['segmentos'])} segmentos). Hay más segmentos de día que de noche y tres ubicaciones."),
        ("Límites y dónde corre", "Todo es en muestra (41 segmentos, detector ajustado con los mismos datos) y sin prueba ciega; los hallazgos post hoc son hipótesis. La página corre solo en este equipo, sin conexión a internet; no debe exponerse en una red sin autenticación."),
    ]
    for titulo, texto in tarjetas:
        with st.container(border=True):
            st.markdown(f"**{titulo}**")
            st.write(texto)


# ------------------------------------------------------------------------------------------------------------ Puntuar datos nuevos
def puntuar(ctx: dict[str, Any]) -> None:
    st.markdown("Puntúe un segmento nuevo con la solución congelada. **Todo se hace en memoria: nada se guarda ni se envía.**")
    _html(E.pasos([("Suba los archivos", "El parquet de lidar_box de un segmento y, si lo tiene, el de camera_to_lidar_box_association."), ("Se validan las columnas", "Si falta algo, la página se lo dice en español."),
                   ("Reciba las listas", "Celdas marcadas (Lista A), cola de cajas (Lista B) y descargas.")]))
    with st.expander("Formato esperado"):
        st.markdown("- **lidar_box (.parquet):** el componente `lidar_box` de Waymo v2, con las columnas de caja (`box.center.x`, `box.center.y`, `box.size.x`…), puntos del LiDAR y del sensor superior, `key.segment_context_name`, `key.frame_timestamp_micros` y `key.laser_object_id`.\n"
                    "- **camera_to_lidar_box_association (.parquet), opcional:** con `key.camera_name`. Sin él no hay auditoría de cámaras.")
    try:
        art = ctx["artefactos"]()
    except FileNotFoundError:
        st.error("Falta la solución congelada en data/06_models_ep3 (la crea scripts/ep3/f6_final.py).")
        return
    f1 = st.file_uploader("Paso 1. lidar_box (.parquet)", type="parquet")
    f2 = st.file_uploader("Paso 1 (opcional). camera_to_lidar_box_association (.parquet)", type="parquet")
    if f1 is None:
        st.info("Todavía no hay archivos: suba un lidar_box para empezar.")
        return
    from waymo_evaluacion.ep3.inferencia import puntuar_segmento

    try:
        lidar = pd.read_parquet(f1)
        asoc = pd.read_parquet(f2) if f2 is not None else None
    except Exception:  # noqa: BLE001 - archivo ilegible: mensaje claro
        st.error("No pude leer el archivo: no parece un parquet válido.")
        return
    problema = validar_lidar_box(lidar) or (validar_asociacion(asoc) if asoc is not None else None)
    if problema:
        st.error(problema)
        return
    with st.spinner("Puntuando el segmento…"):
        try:
            res = puntuar_segmento(lidar, asoc, art)
        except (KeyError, ValueError) as e:
            st.error(f"No pude puntuar el archivo: {e}")
            return
    for a in res.advertencias:
        st.warning(a)
    rs = res.resumen
    _html(E.tarjetas([("Cajas puntuadas", F.entero(len(res.cajas)), "peatones y ciclistas en la población principal", ""), ("Celdas marcadas", F.entero(len(res.lista_A)), "Lista A", "hueco"),
                      ("Cajas en la cola", F.entero(len(res.lista_B)), "Lista B (celdas sanas)", "")]))
    with st.expander("Resumen técnico"):
        st.json(rs)
    st.markdown("#### Lista A: celdas marcadas")
    st.dataframe(F.tabla_legible(res.lista_A), width="stretch", hide_index=True)
    st.markdown("#### Lista B: cola de cajas (celdas sanas)")
    lb = ocultar_identificadores(res.lista_B, ctx["presentacion"])
    st.dataframe(F.tabla_legible(lb.head(500)), width="stretch", hide_index=True)
    d1, d2 = st.columns(2)
    d1.download_button("Descargar Lista A (CSV)", res.lista_A.to_csv(index=False).encode("utf-8"), "lista_A_nueva.csv", "text/csv", icon=":material/download:")
    d2.download_button("Descargar Lista B (CSV)", lb.to_csv(index=False).encode("utf-8"), "lista_B_nueva.csv", "text/csv", icon=":material/download:")


# ------------------------------------------------------------------------------------------------------------ Ayuda
def ayuda(ctx: dict[str, Any]) -> None:
    st.markdown("#### Primeros pasos")
    st.markdown("1. Elija su **perfil** en la barra lateral: cambia lo que se le sugiere primero.\n2. En **Cola de revisión** elija cuánto quiere revisar (o cuánto quiere encontrar) y descargue la lista.\n"
                "3. En **Auditoría de cámaras** vea qué celdas se marcaron como hueco y qué hacer con ellas.\n4. Active el **modo presentación** para ocultar identificadores y agrandar la letra.")
    st.markdown("#### Glosario")
    for t, d in GLOSARIO:
        with st.expander(t):
            st.write(d)
    st.markdown("#### Preguntas frecuentes")
    for q, a in preguntas_frecuentes(ctx["D"]["evidencia"].get("posthoc__equidad")):
        with st.expander(q):
            st.write(a)
    st.markdown("#### Versión")
    st.write(f"{ctx['version']}. Datos: Waymo Open Dataset v2, uso académico. Una persona revisa y decide; nada se guarda ni se envía.")
