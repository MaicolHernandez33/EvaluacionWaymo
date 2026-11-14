"""Genera docs/ep3/PENDIENTES_PAGINA.md: lista de mejoras de la pagina con archivo y linea donde ocurre cada una. NO modifica app/.

Las lineas se buscan por texto ancla en app/app.py y src/waymo_evaluacion/ep3/app_logica.py (cambian si esos archivos cambian: volver a correr este script).
Las cifras salen de data/08_reporting_ep3/f12_equidad.csv y de la misma logica que usa la pagina (app_logica) sobre data/09_app_ep3.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.app_logica import cargar_datos, cola_segmento, recall_en_presupuesto  # noqa: E402

APP = RAIZ / "app/app.py"
LOG = RAIZ / "src/waymo_evaluacion/ep3/app_logica.py"


def linea(archivo: Path, ancla: str, desde: int = 1) -> int:
    for i, l in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
        if i >= desde and ancla in l:
            return i
    raise KeyError(f"no encuentro {ancla!r} en {archivo.name}")


def ref(archivo: Path, n: int) -> str:
    return f"`{archivo.relative_to(RAIZ).as_posix()}:{n}`"


def miles(x: float) -> str:
    return f"{int(round(x)):,}".replace(",", ".")


def pc(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f} %".replace(".", ",")


def main() -> None:
    D = cargar_datos(RAIZ / "data/09_app_ep3")
    sol = D["kpis"]["nombre_curva"]
    eq = pd.read_csv(RAIZ / "data/08_reporting_ep3/f12_equidad.csv")
    ci = eq[(eq["grupo"] == "CYCLIST") & (eq["celdas_con_hueco"] == "incluidas")].iloc[0]
    pe = eq[(eq["grupo"] == "PEDESTRIAN") & (eq["celdas_con_hueco"] == "incluidas")].iloc[0]
    esp68 = recall_en_presupuesto(D["curva"], sol, 0.68)["recall"]
    _, inf68 = cola_segmento(D["cajas"], "Todos", 0.68)
    esp20 = recall_en_presupuesto(D["curva"], sol, 0.20)["recall"]
    _, inf20 = cola_segmento(D["cajas"], "Todos", 0.20)
    L_metric = linea(APP, 'm1.metric("Recall esperado')
    L_m2 = linea(APP, 'm2.metric("Cajas a revisar en este segmento"')
    L_txt = linea(APP, "En el segmento elegido, el proceso completo")
    L_solo = linea(APP, "Es un solo segmento: no tiene IC por segmentos")
    L_slider = linea(APP, 'presup = c2.slider("Presupuesto')
    L_cols = linea(APP, 'cols = [c for c in ["seg", "key.frame_timestamp_micros"')
    L_expl = linea(APP, 'elif seccion == "Explica una caja"')
    L_sl_pts = linea(APP, 'pts = c1.slider("Puntos LiDAR en la caja"')
    L_perfil = linea(APP, 'perfil = st.sidebar.selectbox("Perfil"')
    L_sug = linea(APP, "sugerida = PERFILES[perfil]")
    L_inicio = linea(APP, 'if seccion == "Inicio"')
    L_perf_def = linea(LOG, "PERFILES = {")
    L_recall_fn = linea(LOG, "def recall_en_presupuesto")
    L_cola_fn = linea(LOG, "def cola_segmento")
    L_rec_proc = linea(LOG, '"recall_proceso"')
    L_mod = linea(APP, 'presentacion = st.sidebar.toggle("Modo presentación"')

    md = f"""# Pendientes de la página (no se corrigió nada; `app/` no se modificó)

*Generado por `scripts/ep3/generar_pendientes_pagina.py`. Las líneas se buscan por texto en el código actual; si `app/app.py` cambia, volver a correr el script. Cifras: `f12_equidad.csv` y la misma lógica de `app_logica.py` sobre `data/09_app_ep3`. Prioridad sugerida: c, d, b, f, a, e.*

## a) «Recall esperado (todos los segmentos)» no sirve como titular
- Dónde: {ref(APP, L_metric)} (tarjeta `m1`); el texto técnico (IC por segmentos, «fuera de fold») va en el `help`.
- Qué hacer: reemplazarlo por lenguaje simple dentro de un bloque plegable (`st.expander`) «¿Qué tan confiable es esto?» y agregar un **control inverso**: «quiero encontrar X %» y la página dice cuánto revisar (invertir la curva guardada con `numpy.interp` sobre `curva_cola.csv`; la función de ida está en {ref(LOG, L_recall_fn)}). Mantenerlo visible con el modo presentación activo ({ref(APP, L_mod)} solo oculta identificadores).

## b) Con «Segmento: Todos» aparecen textos de un solo segmento
- Dónde: {ref(APP, L_m2)} («Cajas a revisar en este segmento»), {ref(APP, L_txt)} («En el segmento elegido…») y {ref(APP, L_solo)} («Es un solo segmento: no tiene IC por segmentos»). El selector con «Todos» está en {ref(APP, linea(APP, 'seg = c1.selectbox("Segmento"'))}.
- Qué hacer: ramificar por `seg == "Todos"`: con «Todos», decir «en los 41 segmentos» y mostrar el IC por segmentos de la curva; con un segmento, el texto actual.

## c) Inconsistencia de redondeo entre la tarjeta y el texto
- Dónde: tarjeta {ref(APP, L_metric)} (usa la curva interpolada, {ref(LOG, L_recall_fn)}) y texto {ref(APP, L_txt)} (usa el conteo observado `recall_proceso`, {ref(LOG, L_rec_proc)} dentro de {ref(LOG, L_cola_fn)}).
- Evidencia (reproducida con la lógica de la página, «Todos»): al 68 % la tarjeta dice **{pc(esp68)}** y el texto **{pc(inf68['recall_proceso'])}** ({miles(inf68['positivos_auditoria'] + inf68['positivos_en_cola'])} de {miles(inf68['positivos_total'])}); al 20 % dice **{pc(esp20)}** y **{pc(inf20['recall_proceso'])}**. La diferencia (0,02 puntos) pasa a 0,1 al redondear a un decimal.
- Qué hacer: una sola fuente (la tarjeta y el texto deben leer el mismo valor) y un solo redondeo; si se quiere mostrar el valor observado y el esperado, rotularlos distinto.

## d) Presupuesto por defecto
- Se pidió que parta en 20 % (punto B del informe). **En el código ya parte en 20:** {ref(APP, L_slider)} (`st.slider(..., 1, 100, 20)`), y una corrida de `AppTest` hecha al preparar este documento lo confirma (valor 20 al abrir «Cola de revisión»). El 68 % que se vio en pantalla coincide con un valor movido a mano o con el estado del navegador, no con el valor por defecto; no se encontró otra causa en el código. Si se vuelve a ver, revisar el estado de sesión de Streamlit (recargar la página).
- Qué hacer (opcional): fijar `key="presupuesto"` y un botón «volver al 20 %» para que el valor por defecto sea explícito.

## e) Pulido visual y contenido por perfil
- Dónde: perfil en {ref(APP, L_perfil)}; sección sugerida en {ref(APP, L_sug)}; textos de cada perfil en {ref(LOG, L_perf_def)}; Inicio en {ref(APP, L_inicio)}.
- Hoy el perfil solo cambia la sección sugerida y un mensaje. Qué debería ver primero cada perfil:
  - **Analista de revisión:** la Cola de revisión con el presupuesto y el control inverso (a), los segundos por caja y la descarga de la cola.
  - **Responsable de calidad de datos:** la Auditoría de cámaras (mapa de calor y Lista A) y, debajo, qué significa un hueco y que la causa no se conoce.
  - **Ingeniero consumidor de datos:** «Puntuar datos nuevos» y, antes, la confiabilidad (aviso «en muestra», ciclistas, falsas alarmas del detector sin estimar).
- Pulido general: jerarquía de títulos, menos texto en Inicio, colores de las dos columnas del flujo, y el aviso «en muestra» más corto pero visible.

## f) Aviso de ciclistas
- Hecho a documentar: la regla es poco confiable para ciclistas: recall **{str(round(ci['recall_A'], 3)).replace('.', ',')}** contra **{str(round(pe['recall_A'], 3)).replace('.', ',')}** en peatones, con **{int(ci['positivos'])}** positivos en **{int(ci['segmentos'])}** segmentos (`f12_equidad.csv`).
- Dónde falta: (1) «Cola de revisión»: la tabla {ref(APP, L_cols)} no incluye la columna `es_ciclista`, que sí existe en `cajas_oof.parquet`; hay que mostrarla y avisar cuando la caja sea de un ciclista. (2) «Explica una caja» ({ref(APP, L_expl)}): los controles {ref(APP, L_sl_pts)} no tienen un selector de clase y la fila base usa la mediana (`es_ciclista` = 0), así que no puede avisar; agregar «¿Es ciclista?» y mostrar el aviso.
"""
    (RAIZ / "docs/ep3/PENDIENTES_PAGINA.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
