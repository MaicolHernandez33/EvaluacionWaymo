"""Página de EP3: para qué sirve la solución y cómo funciona. Solo local: ningún dato sale del equipo.

Ejecutar:  streamlit run app/app.py
Variables de entorno opcionales: WAYMO_APP_DATA (por defecto data/09_app_ep3) y WAYMO_APP_MODELOS (por defecto data/06_models_ep3).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from waymo_evaluacion.ep3.app_logica import (  # noqa: E402
    AVISO_EN_MUESTRA, PERFILES, REFERENCIAS, cargar_datos, cargar_no_supervisado, cola_segmento, curva_dependencia, curvas_a_mostrar, horas_revision, info_tipo_de_caso,
    matriz_calor, ocultar_identificadores, percentil_en_cola, recall_en_presupuesto, tipo_de_caso,
)

CARPETA_DATOS = Path(os.environ.get("WAYMO_APP_DATA", RAIZ / "data/09_app_ep3"))
CARPETA_MODELOS = Path(os.environ.get("WAYMO_APP_MODELOS", RAIZ / "data/06_models_ep3"))
SECCIONES = ["Inicio", "Auditoría de cámaras", "Cola de revisión", "Explica una caja", "Evidencia", "Ética y límites", "Puntuar datos nuevos"]

st.set_page_config(page_title="Revisión de etiquetas 3D de Waymo", layout="wide")


@st.cache_data(show_spinner=False)
def datos(carpeta: str) -> dict:
    return cargar_datos(Path(carpeta))


@st.cache_resource(show_spinner=False)
def artefactos(carpeta: str):
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos

    return cargar_artefactos(Path(carpeta))


@st.cache_resource(show_spinner=False)
def no_sup(carpeta: str):
    return cargar_no_supervisado(Path(carpeta))


def pct(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f} %".replace(".", ",")


def miles(x: float) -> str:
    return f"{int(round(x)):,}".replace(",", ".")


# ------------------------------------------------------------------------------------------ barra lateral
st.sidebar.title("Revisión de etiquetas 3D")
perfil = st.sidebar.selectbox("Perfil", list(PERFILES), help="Cambia el texto de bienvenida y la sección sugerida.")
presentacion = st.sidebar.toggle("Modo presentación", value=False, help="Oculta los identificadores de cada caja (marca de tiempo e id del láser).")
segundos = st.sidebar.number_input("Segundos por revisión (supuesto, no medido)", min_value=1, max_value=600, value=20, step=5)
sugerida = PERFILES[perfil]["seccion"]
seccion = st.sidebar.radio("Sección", SECCIONES, index=SECCIONES.index(sugerida))
st.sidebar.caption("Datos: predicciones fuera de fold sobre 41 segmentos del Waymo Open Dataset v2 (uso académico). Nada se guarda ni se envía.")

try:
    D = datos(str(CARPETA_DATOS))
except FileNotFoundError as e:
    D = None
    falta = str(e)
K = D["kpis"] if D else {}

st.title("Revisión de etiquetas 3D de Waymo")
if D is None and seccion not in ("Ética y límites", "Puntuar datos nuevos"):
    st.error(f"No encuentro los datos de la página ({falta}). Genérelos con: python scripts/ep3/f7_preparar_app.py")
    st.stop()

# ------------------------------------------------------------------------------------------ 1. Inicio
if seccion == "Inicio":
    st.subheader("El problema, en simple")
    st.write(
        "Un auto autónomo etiqueta en 3D (con LiDAR) a peatones y ciclistas, y otro equipo etiqueta lo mismo en las fotos de las cámaras. "
        "Cuando una caja 3D no tiene su pareja en ninguna cámara, algo pudo fallar: falta la etiqueta 2D, o la cámara no tiene datos. "
        "Es como cuadrar una caja: conviene saber primero si una caja completa de recibos se perdió, antes de revisar recibo por recibo."
    )
    st.info(f"**{perfil}.** {PERFILES[perfil]['pregunta']} {PERFILES[perfil]['mensaje']}")
    c1, c2 = st.columns(2)
    c1.markdown("**Paso 1. Filtro 1 (detector de huecos).** Mira cada cámara en cada segmento. Si casi ninguna caja de su zona tiene pareja, la celda "
                "(segmento, cámara) va a la **Lista A** y se atiende aparte, de una vez.")
    c2.markdown("**Paso 2. Cola de revisión.** Las cajas de las celdas sanas se ordenan con la solución elegida (**Lista B**): primero las que más probablemente "
                "no tienen pareja. **Una persona revisa y decide**; la solución solo ordena.")
    st.subheader("Resultados (fuera de fold, con IC 95 % por segmentos)")
    st.warning(AVISO_EN_MUESTRA)
    cols = st.columns(len(K.get("tarjetas", [])) or 1)
    for col, t in zip(cols, K.get("tarjetas", [])):
        col.metric(t["titulo"], t["valor"], help=f"{t.get('ic', '')} Fuente: {t.get('fuente', '')}")
    st.caption(K.get("solucion_final", ""))

# ------------------------------------------------------------------------------------------ 2. Auditoría
elif seccion == "Auditoría de cámaras":
    st.subheader("Mapa de tasas por segmento y cámara")
    st.write("Cada celda muestra qué fracción de las cajas dentro del rango de la cámara tiene pareja. Una X marca un hueco: tasa menor al 25 % de la mediana "
             "de esa cámara y al menos 100 cajas en el rango. Los parámetros están congelados desde EP2.")
    grupo = st.radio("Grupo", ["todos", "train", "test"], horizontal=True)
    m = matriz_calor(D["celdas"])
    if grupo != "todos":
        m = m[m["grupo"] == grupo]
    base = alt.Chart(m).encode(x=alt.X("camara:N", title=None), y=alt.Y("seg:N", title="segmento", sort=None))
    mapa = base.mark_rect().encode(color=alt.Color("tasa:Q", scale=alt.Scale(domain=[0, 1]), title="tasa de pares"),
                                   tooltip=["seg", "camara", "tasa", "n_rango", "hueco"])
    marcas = base.transform_filter(alt.datum.hueco).mark_text(text="X", color="red", fontSize=16, fontWeight="bold")
    st.altair_chart((mapa + marcas).properties(height=max(300, 16 * m["seg"].nunique())), width="stretch")
    st.subheader("Lista A: celdas con hueco")
    la = D["lista_A"]
    st.dataframe(la, width="stretch", hide_index=True)
    st.download_button("Descargar Lista A (CSV)", la.to_csv(index=False).encode("utf-8"), "lista_A.csv", "text/csv")
    st.caption("Un hueco puede ser de etiquetado 2D o de datos de esa cámara; con estos archivos no se distingue. Es una hipótesis para revisar, no una conclusión.")

# ------------------------------------------------------------------------------------------ 3. Cola
elif seccion == "Cola de revisión":
    st.subheader("Cuánto revisar y cuánto se encuentra")
    st.warning(AVISO_EN_MUESTRA)
    segs = ["Todos"] + sorted(D["cajas"]["seg"].unique())
    c1, c2 = st.columns(2)
    seg = c1.selectbox("Segmento", segs)
    presup = c2.slider("Presupuesto: porcentaje de la cola que se revisa", 1, 100, 20) / 100
    sol = K.get("nombre_curva", "solucion")
    refs = [r for r in REFERENCIAS if D["curva"]["solucion"].str.startswith(r).any()]
    ref = st.selectbox("Comparar con modelo de referencia", ["Ninguno", *refs]) if refs else "Ninguno"
    esp = recall_en_presupuesto(D["curva"], sol, presup)
    top, info = cola_segmento(D["cajas"], seg, presup)
    horas = horas_revision(info["cajas_a_revisar"], segundos)
    m1, m2, m3 = st.columns(3)
    m1.metric("Recall esperado (todos los segmentos)", pct(esp["recall"]), help=f"IC 95 % por segmentos: {pct(esp['lo'])} a {pct(esp['hi'])}")
    m2.metric("Cajas a revisar en este segmento", miles(info['cajas_a_revisar']), help="De la cola de celdas sanas; la auditoría se atiende aparte.")
    m3.metric(f"Horas con {segundos} s por caja", f"{horas:.1f}".replace(".", ","), help="Supuesto editable; no se midió el tiempo real de revisión.")
    st.write(f"En el segmento elegido, el proceso completo (auditoría más cola) encontró {miles(info['positivos_auditoria'] + info['positivos_en_cola'])} de "
             f"{miles(info['positivos_total'])} cajas sin pareja ({pct(info['recall_proceso'])}). Es un solo segmento: no tiene IC por segmentos.")
    curva = curvas_a_mostrar(D["curva"], ref)
    if ref != "Ninguno":
        er = recall_en_presupuesto(D["curva"], f"{ref} (referencia), un paso (A)", presup)
        st.caption(f"{ref} como referencia (un paso, fuera de fold): recall esperado {pct(er['recall'])} (IC {pct(er['lo'])} a {pct(er['hi'])}) con el mismo presupuesto. No se eligió por simplicidad; ver Evidencia.")
    graf = alt.Chart(curva).mark_line().encode(x=alt.X("presupuesto:Q", title="fracción de la cola revisada"), y=alt.Y("recall:Q", title="recall"), color="solucion:N")
    banda = alt.Chart(curva).mark_area(opacity=0.15).encode(x="presupuesto:Q", y="lo:Q", y2="hi:Q", color="solucion:N")
    st.altair_chart(banda + graf, width="stretch")
    vista = ocultar_identificadores(top, presentacion)
    cols = [c for c in ["seg", "key.frame_timestamp_micros", "key.laser_object_id", "tipo_caso", "num_lidar_points", "distancia_m", "score", "prob_cal"] if c in vista.columns]
    st.dataframe(vista[cols].head(500), width="stretch", hide_index=True)
    st.download_button("Descargar cola (CSV)", vista[cols].to_csv(index=False).encode("utf-8"), "cola_revision.csv", "text/csv")

# ------------------------------------------------------------------------------------------ 4. Explica una caja
elif seccion == "Explica una caja":
    st.subheader("¿Por qué una caja queda arriba o abajo en la cola?")
    st.write("Pocos puntos LiDAR suelen significar que la caja está lejos o tapada, y es más probable que ninguna cámara la haya etiquetado. "
             "Mueva los controles y vea el puntaje, el lugar en la cola y la probabilidad calibrada.")
    try:
        art = artefactos(str(CARPETA_MODELOS))
    except FileNotFoundError:
        st.error("Falta la solución congelada en data/06_models_ep3 (la crea scripts/ep3/f6_final.py).")
        st.stop()
    from waymo_evaluacion.ep3.inferencia import V16

    ref = D["cajas"]
    base = ref[V16].median().to_frame().T
    c1, c2, c3 = st.columns(3)
    pts = c1.slider("Puntos LiDAR en la caja", 1, 1000, 60)
    top_pts = c2.slider("Puntos del LiDAR superior", 1, 1000, min(pts, 50))
    dist = c3.slider("Distancia al sensor (m)", 1.0, 100.0, 25.0)
    fila = base.copy()
    fila["num_lidar_points"], fila["num_top_lidar_points"], fila["distancia_m"] = pts, top_pts, dist
    fila["densidad_puntos"] = pts / fila["volumen_caja"]
    s = float(art.puntuador.puntuar(fila)[0])
    p = float(art.calibrador.calibrar(np.array([s]))[0]) if art.calibrador is not None else float("nan")
    pc = percentil_en_cola(s, ref)
    k1, k2, k3 = st.columns(3)
    k1.metric("Puntaje", f"{s:.3f}".replace(".", ","))
    k2.metric("Lugar en la cola", f"entre el {pct(pc, 0)} primero", help="0 % = primera de la cola; 100 % = última.")
    k3.metric("Probabilidad calibrada de no tener pareja", pct(p))
    ns = no_sup(str(CARPETA_MODELOS))
    if ns is not None:
        fila_nc = fila.copy()
        info = info_tipo_de_caso(tipo_de_caso(fila_nc, ns), D["clusters"])
        st.info(f"**Tipo de caso:** {info['tipo_de_caso']}. En los 41 segmentos, ese tipo de caso tuvo {pct(info['tasa'])} de cajas sin pareja "
                f"(IC 95 % por segmentos {pct(info['ic_lo'])} a {pct(info['ic_hi'])}; {miles(info['cajas'])} cajas). Es una descripción (post hoc), y no mejora la predicción de la regla.")
    dep = curva_dependencia(art.puntuador, fila, "num_lidar_points", np.unique(np.round(np.geomspace(1, 1000, 60))))
    st.altair_chart(alt.Chart(dep).mark_line().encode(x=alt.X("num_lidar_points:Q", scale=alt.Scale(type="log"), title="puntos LiDAR"), y=alt.Y("score:Q", title="puntaje")),
                    width="stretch")
    st.caption("Las demás variables se dejan en la mediana de los datos. Es una ilustración del modelo, no una explicación causal.")

# ------------------------------------------------------------------------------------------ 5. Evidencia
elif seccion == "Evidencia":
    st.subheader("Evidencia de los cuatro ejes")
    ev = D["evidencia"]
    nombres = {"ie9": "IE9 Hiperparámetros", "ie10": "IE10 Ensambles", "ie11": "IE11 Generalización", "ie12": "IE12 Selección",
               "nosup": "No supervisado (descriptivo)", "posthoc": "Análisis en muestra (post hoc)"}
    tabs = st.tabs(list(nombres.values()))
    for tab, (pref, titulo) in zip(tabs, nombres.items()):
        with tab:
            hallados = {k: v for k, v in ev.items() if k.startswith(pref)}
            if not hallados:
                st.info("Sin tablas todavía.")
            for k, v in hallados.items():
                st.markdown(f"**{k.split('__', 1)[-1].replace('_', ' ')}**")
                st.dataframe(v, width="stretch", hide_index=True)
    st.caption("Cada tabla sale de un CSV de data/08_reporting_ep3 (nombre en la barra de título del archivo). Lo post hoc lo dice su texto.")

# ------------------------------------------------------------------------------------------ 6. Ética
elif seccion == "Ética y límites":
    st.subheader("Ética y límites")
    st.markdown(
        "- **Una persona decide.** La solución ordena y avisa; no etiqueta ni borra nada. Nunca se debe usar para descartar cajas sin revisión.\n"
        "- **No es una prueba de seguridad.** Mide si una caja 3D tiene pareja 2D, no si el peatón fue detectado bien.\n"
        "- **Datos y licencia.** Waymo Open Dataset es de uso académico y no comercial; sus datos no se redistribuyen. Esta página corre solo en su equipo, "
        "no hornea datos en imágenes Docker y no envía nada a internet.\n"
        "- **Privacidad.** Hay identificadores de objeto y marcas de tiempo en las tablas locales; el *modo presentación* los oculta.\n"
        "- **Sesgos y alcance.** 41 segmentos, tres ubicaciones; mayoría de día. Los 8 segmentos de test de EP2 ya no son ciegos. La validación con segmentos nuevos queda pendiente.\n"
        "- **Hallazgos post hoc** (por ejemplo, los huecos de cámara) se rotulan *post hoc, no pre-declarado*: son hipótesis, no conclusiones.\n"
        "- **Tiempo de revisión.** Los segundos por caja son un supuesto editable, no una medición.")

# ------------------------------------------------------------------------------------------ 7. Puntuar
else:
    st.subheader("Puntuar datos nuevos (todo en memoria, nada se guarda)")
    st.write("Suba el parquet de **lidar_box** de un segmento y, si lo tiene, el de **camera_to_lidar_box_association**. Se usa la solución congelada.")
    try:
        art = artefactos(str(CARPETA_MODELOS))
    except FileNotFoundError:
        st.error("Falta la solución congelada en data/06_models_ep3 (la crea scripts/ep3/f6_final.py).")
        st.stop()
    f1 = st.file_uploader("lidar_box (.parquet)", type="parquet")
    f2 = st.file_uploader("camera_to_lidar_box_association (.parquet, opcional)", type="parquet")
    if f1 is not None:
        from waymo_evaluacion.ep3.inferencia import puntuar_segmento

        try:
            r = puntuar_segmento(pd.read_parquet(f1), pd.read_parquet(f2) if f2 is not None else None, art)
        except (KeyError, ValueError) as e:
            st.error(f"No pude puntuar el archivo: {e}")
            st.stop()
        for a in r.advertencias:
            st.warning(a)
        st.json(r.resumen)
        st.markdown("**Lista A: celdas con hueco**")
        st.dataframe(r.lista_A, width="stretch", hide_index=True)
        st.markdown("**Lista B: cola de cajas (celdas sanas)**")
        lb = ocultar_identificadores(r.lista_B, presentacion)
        st.dataframe(lb.head(500), width="stretch", hide_index=True)
        st.download_button("Descargar Lista A (CSV)", r.lista_A.to_csv(index=False).encode("utf-8"), "lista_A_nueva.csv", "text/csv")
        st.download_button("Descargar Lista B (CSV)", lb.to_csv(index=False).encode("utf-8"), "lista_B_nueva.csv", "text/csv")
