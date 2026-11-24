"""Genera docs/ep3/PENDIENTES_PAGINA.md: estado de cada mejora de la pagina (resuelta, con archivo y linea, o pendiente con motivo) y hallazgos nuevos.

F18-C15: tras el rediseno de app/ casi todo esta resuelto; lo que no, queda con su motivo. Las lineas se buscan por texto ancla en el codigo actual
(si cambian app/ o app_logica.py, volver a correr este script). Las cifras salen de f12_equidad.csv y de la misma logica que usa la pagina.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.app_logica import cargar_datos, resumen_cola  # noqa: E402
from waymo_evaluacion.ep3.formato import nombre_visible  # noqa: E402

APP = RAIZ / "app/app.py"
SEC = RAIZ / "app/secciones.py"
LOG = RAIZ / "src/waymo_evaluacion/ep3/app_logica.py"
EST = RAIZ / "app/estilos.py"
TST = RAIZ / "tests/ep3/test_pagina_rediseno.py"
FMT = RAIZ / "src/waymo_evaluacion/ep3/formato.py"
PRE = RAIZ / "app/precarga.py"
CAP = RAIZ / "scripts/ep3/capturar_pagina.py"
TPU = RAIZ / "tests/ep3/test_pagina_pulido.py"
TF20 = RAIZ / "tests/ep3/test_pagina_f20.py"
TF21 = RAIZ / "tests/ep3/test_pagina_f21.py"


def segundos(escenarios: list[dict], clave: str) -> str:
    """«2,9» o «3,3 a 4,1» (min a max de las repeticiones), con coma decimal."""
    v = [e[clave] for e in escenarios]
    return (f"{min(v):.1f}" if min(v) == max(v) else f"{min(v):.1f} a {max(v):.1f}").replace(".", ",")


def linea(archivo: Path, ancla: str) -> int:
    for i, l in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
        if ancla in l:
            return i
    raise KeyError(f"no encuentro {ancla!r} en {archivo.name}")


def ref(archivo: Path, ancla: str) -> str:
    return f"`{archivo.relative_to(RAIZ).as_posix()}:{linea(archivo, ancla)}`"


def pc(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f} %".replace(".", ",")


def main() -> None:
    D = cargar_datos(RAIZ / "data/09_app_ep3")
    sol = D["kpis"]["nombre_curva"]
    eq = pd.read_csv(RAIZ / "data/08_reporting_ep3/f12_equidad.csv")
    ci = eq[(eq["grupo"] == "CYCLIST") & (eq["celdas_con_hueco"] == "incluidas")].iloc[0]
    pe = eq[(eq["grupo"] == "PEDESTRIAN") & (eq["celdas_con_hueco"] == "incluidas")].iloc[0]
    r20 = resumen_cola(D["cajas"], D["curva"], sol, "Todos", 0.20, 20)
    r68 = resumen_cola(D["cajas"], D["curva"], sol, "Todos", 0.68, 20)
    # F19-B: cifras de las secciones nuevas, leidas de los mismos archivos que usa la pagina
    from waymo_evaluacion.ep3.app_logica import MIN_CAJAS_RANGO, inicio_resumen, matriz_calor

    mm = matriz_calor(D["celdas"], MIN_CAJAS_RANGO)
    n_celdas, n_sin, n_hueco = len(mm), int(mm["sin_datos"].sum()), int(mm["hueco"].sum())
    ini = inicio_resumen(D)
    ar = json.loads((RAIZ / "data/08_reporting_ep3/pagina_arranque.json").read_text(encoding="utf-8"))
    con = [e for e in ar["escenarios"] if e["escenario"].startswith("con lanzador")]
    sin = [e for e in ar["escenarios"] if e["escenario"].startswith("sin lanzador")]
    max_sec = f"{max(e['maximo_secciones_s'] for e in con):.1f}".replace(".", ",")
    cap = json.loads((RAIZ / "data/08_reporting_ep3/capturas_resultado.json").read_text(encoding="utf-8"))
    n_cap_ok = sum(1 for c in cap if c["listo"])
    ruta_f20 = RAIZ / "data/08_reporting_ep3/pagina_arranque_f20.json"
    ar20 = json.loads(ruta_f20.read_text(encoding="utf-8")) if ruta_f20.exists() else None
    con20 = [e for e in ar20["escenarios"] if e["escenario"].startswith("con lanzador")] if ar20 else []
    sin20 = [e for e in ar20["escenarios"] if e["escenario"].startswith("sin lanzador")] if ar20 else []
    ruta_f21 = RAIZ / "data/08_reporting_ep3/pagina_arranque_f21.json"
    ar21 = json.loads(ruta_f21.read_text(encoding="utf-8")) if ruta_f21.exists() else None
    con21 = [e for e in ar21["escenarios"] if e["escenario"].startswith("con lanzador")] if ar21 else []
    sin21 = [e for e in ar21["escenarios"] if e["escenario"].startswith("sin lanzador")] if ar21 else []
    if con21:
        aislados = sum(1 for e in con21 + sin21 if not e["secciones_cumplen_3s"])
        tiempos_f21 = (f"{aislados} de {len(con21) + len(sin21)} arranques salieron lentos de forma aislada (con todas las páginas lentas a la vez; carga puntual del equipo, hipótesis; ver el reporte de F21); el resto: con el lanzador, la primera visita a «Explica una caja» tarda {segundos([e for e in con21 if e['secciones_cumplen_3s']], 'primera_visita_explica_s')} s y la página más lenta {max(e['maximo_secciones_s'] for e in con21 if e['secciones_cumplen_3s']):.1f} s después; "
                       f"sin el lanzador, la primera visita tarda {segundos(sin21, 'primera_visita_explica_s')} s".replace(".", ","))
    else:
        tiempos_f21 = "medición pendiente (`scripts/ep3/f19_medir_arranque.py`)"
    tiempos_f20 = (f"con el lanzador, la primera visita a «Explica una caja» tarda {segundos(con20, 'primera_visita_explica_s')} s y ninguna página tarda más de {max(e['maximo_secciones_s'] for e in con20):.1f} s después; sin el lanzador, la primera visita tarda {segundos(sin20, 'primera_visita_explica_s')} s".replace(".", ",")
                   if con20 and sin20 else "sin medición (correr scripts/ep3/f19_medir_arranque.py)")
    md = f"""# Pendientes de la página: estado tras el rediseño (F18-C, F19-B y F20)

*Generado por `scripts/ep3/generar_pendientes_pagina.py`. Las líneas se buscan por texto en el código actual; si `app/` cambia, volver a correr el script. Lo «resuelto» tiene archivo y línea y una prueba en `tests/ep3/test_pagina_rediseno.py`.*

| Ítem | Estado |
|---|---|
| a) «Recall esperado» como titular | **Resuelto** |
| b) Textos de un solo segmento con «Todos» | **Resuelto** |
| c) Redondeo distinto entre tarjeta y texto | **Resuelto** |
| d) Presupuesto por defecto | **Resuelto** (ya era 20 %; ahora explícito) |
| e) Pulido visual y contenido por perfil | **Resuelto** en lo que se puede verificar sin usuarios; queda una prueba con personas |
| f) Aviso de ciclistas | **Resuelto** |
| g) F19-B: pulido de la página (B1 a B10) | **Resuelto** salvo lo que dice la sección «F19-B» (la prueba con personas sigue pendiente) |
| h) F20: rediseño como herramienta de trabajo (P1 a P12) | **Resuelto** con las limitaciones de la sección «F20» |

## a) «Recall esperado (todos los segmentos)» no sirve como titular: resuelto
- Desde F32 el resultado de la Cola son tres tarjetas («Cajas a revisar», «Cajas sin pareja que se encuentran» y «Tiempo estimado»; {ref(SEC, "tarjetas_cola(r, segundos)")}; lógica en {ref(LOG, "def tarjetas_cola")}); el párrafo «Revisando N cajas se encontrarían unas X de cada 100» ({ref(LOG, "def texto_resultado_cola")}) queda para otros usos. La palabra «recall» ya no es titular (queda solo en el nombre técnico de las tablas de Evidencia).
- El desplegable «Supuestos y confiabilidad» (F32: al final de la página; antes un popover y, antes, un acordeón «¿Qué tan confiable es esto?») ({ref(SEC, "with st.expander(COLA_SUPUESTOS):")}) trae el supuesto de 20 s por caja, el aviso «en muestra», el intervalo y el punto de ciclistas.
- Control inverso «Quiero encontrar X % de las cajas sin pareja» ({ref(SEC, "MODO_OBJETIVO = ")} y {ref(SEC, "presup = round(curva_inversa")}; lógica en {ref(LOG, "def curva_inversa")}). Prueba: `test_control_inverso_es_consistente_con_la_curva`.
- Visible con los tres roles (prueba `test_humo_8_secciones_x_3_perfiles`); desde F30 ya no existe el modo presentación.

## b) Con «Segmento: Todos» aparecían textos de segmento único: resuelto
- Textos distintos para «Todos los segmentos» (con intervalo por segmentos) y para un segmento (sin intervalo): {ref(LOG, "def texto_resultado_cola")}. Prueba: `test_textos_distintos_para_todos_y_un_segmento`.

## c) Inconsistencia de redondeo entre la tarjeta y el texto: resuelto
- Antes: al 68 % la tarjeta decía 96,5 % y el texto 96,6 % ({pc(r68['cobertura_curva'], 2)} de la curva interpolada contra {pc(r68['cobertura'], 2)} del conteo observado); al 20 %, 70,2 % contra 70,3 %.
- Ahora hay **una sola fuente**, el conteo observado ({ref(LOG, "def resumen_cola")}): al 20 % la página dice «unas {round(100 * r20['cobertura'])} de cada 100» ({pc(r20['cobertura'])}) y al 68 % «unas {round(100 * r68['cobertura'])} de cada 100» ({pc(r68['cobertura'])}). La curva solo aporta el intervalo. Documentado en `data/08_reporting_ep3/pagina_comparacion_antes_despues.csv`. Prueba: `test_fuente_unica_de_la_cobertura`.

## d) Presupuesto por defecto: resuelto
- El código ya partía en 20 % (el 68 % que se vio una vez era un valor movido a mano); ahora el valor está en el estado de la página ({ref(SEC, 'st.session_state.setdefault("presupuesto", 20)')}) y hay un botón «Volver al 20 %» ({ref(SEC, "def _volver_a_20")}). Prueba: `test_cola_control_inverso_y_boton_volver_al_20`.

## e) Pulido visual y contenido por perfil: resuelto salvo la prueba con personas
- Guía de estilo `guia_estilo_pagina.md`, tokens y contraste >= 4,5:1 ({ref(EST, "TOKENS = ")}; prueba `test_tokens_cumplen_contraste_y_coinciden_con_el_tema`), tema en `.streamlit/config.toml` y `app/.streamlit/config.toml`, encabezado y pie, tarjetas, pasos, íconos Material (sin emojis; prueba `test_la_pagina_no_usa_emojis`).
- El perfil decide la sección sugerida ({ref(APP, "def al_cambiar_rol")}) (en el Resumen ya no ordena alertas: F29) ({ref(LOG, "PERFILES = ")}): analista de revisión, la cola; responsable de calidad de datos, la auditoría de cámaras; ingeniero consumidor de datos, puntuar datos nuevos.
- **Pendiente (motivo: requiere personas):** probar el rediseño con usuarios reales de cada perfil; hoy solo se verificó con pruebas automáticas y capturas (`images/ep3/pagina/`).

## f) Aviso de ciclistas: resuelto
- La regla es poco confiable para ciclistas: {ci['recall_A']:.3f} contra {pe['recall_A']:.3f} en peatones, con {int(ci['positivos'])} positivos en {int(ci['segmentos'])} segmentos (`f12_equidad.csv`).
- Cola de revisión: columna «Clase» con la advertencia ({ref(LOG, "CLASE_ADVERTENCIA = ")}) y el panel de detalle trae la advertencia de ciclista ({ref(SEC, 'd["advertencia_ciclista"]')}). Explica una caja: selector «Clase» y advertencia con las cifras ({ref(SEC, 'clase = st.radio("Clase", ')}). Prueba: `test_tabla_de_la_cola_oculta_identificadores_y_avisa_de_ciclistas`.

## g) F19-B: pulido de la página (B1 a B10)
*Las cifras de la página no cambiaron: solo presentación, idioma y uso. Cada ítem tiene su prueba en `tests/ep3/test_pagina_pulido.py` (y en `test_pagina_rediseno.py`).*

| Ítem | Estado | Dónde |
|---|---|---|
| B1 «Explica una caja» en blanco en la captura | **Resuelto** (causa abajo) | {ref(CAP, "JS_ESTADO = ")}, {ref(PRE, "def iniciar")} |
| B2 Mapa de calor: «sin datos» distinto de «tasa 0 %» | **Resuelto** | {ref(LOG, "def matriz_calor")}, {ref(SEC, 'capas = [base.transform_filter(~alt.datum.sin_datos)')}, {ref(EST, "def leyenda_mapa")} |
| B3 Lista A y Cola: columnas clave sin desplazar a 1366 y 1920 px | **Resuelto** | {ref(LOG, "def lista_A_presentable")}, {ref(LOG, "def lista_A_detalle")}, {ref(SEC, "def _config_columnas_cola")} |
| B4 Columna «Fotogramas del mismo objeto en la cola» | **Resuelto** (en pantalla se rotula «Fotogramas») | {ref(LOG, "COLUMNA_FOTOGRAMAS = ")}, {ref(LOG, "def tabla_cola")} |
| B5 Formatos de la tabla de hiperparámetros y revisión de las pestañas de Evidencia | **Resuelto** | {ref(FMT, "HIPERPARAMETROS = ")}, {ref(FMT, "def tabla_legible")}, {ref(FMT, "def tabla_estandar") if False else ref(FMT, "def tabla_legible")} |
| B6 Cargador de archivos en español y «Paso 2 (opcional)» | **Resuelto** con CSS (ver el riesgo abajo) | {ref(SEC, "P.ARCHIVO_2_AYUDA")}, {ref(EST, "Arrastre el archivo")} |
| B7 Colores de «Dos pasos» y «Un paso» | **Resuelto** | {ref(EST, "CURVAS_NOMBRES = ")}, {ref(SEC, "bandas = [alt.Chart")} |
| B8 Titular de horas de Inicio | **Resuelto** | {ref(LOG, "horas_dos_pasos = horas_sin_orden = horas_un_paso = None")}, {ref(SEC, 'st.markdown(f"Ordenar la cola reduce')} |
| B9 Precarga de la solución congelada y los datos | **Resuelto** (medido en un navegador real) | {ref(PRE, "def iniciar")}, `app/lanzar.py`, {ref(APP, "PC.iniciar(")} |
| B10 Pruebas, capturas a 1366 y 1920 px y documentos | **Resuelto**: {n_cap_ok} capturas listas en `images/ep3/pagina/` | `data/08_reporting_ep3/capturas_resultado.json` |

- **B1, causa.** No era un error de la sección: la captura se tomó antes de que terminara la carga en frío (la página mostraba el esqueleto de carga, el texto del cuerpo tenía 0 caracteres y el PNG pesaba unos 9 KB); no hubo excepción en la consola del navegador ni en `AppTest`. «Explica una caja» es la sección que usa el modelo congelado y la más lenta en la primera visita en frío (B9), lo que la dejó más expuesta a la captura temprana (inferencia: no se probó con otra sección). Se corrigió en dos partes: la captura espera hasta que no haya indicador de carga y aparezca un texto propio de la sección (si no aparece, no guarda la imagen y sale con error), y la solución congelada y los datos se cargan y se calientan al arrancar ({ref(PRE, "def _calentar")}).
- **B2.** Con {MIN_CAJAS_RANGO} cajas como mínimo, {n_sin} de {n_celdas} celdas (segmento × cámara) salen «sin cajas o menos de {MIN_CAJAS_RANGO} en el rango» (gris rayado) y {n_hueco} son huecos (rojo con X); una tasa de 0 % con datos suficientes se ve como azul casi blanco. Se muestran todas las etiquetas de segmento. Cifras de `data/09_app_ep3/celdas.csv` y del umbral `min_cajas` de `detector_params_v3.json`.
- **B3.** Lista A: se ven «Acción sugerida» y «Cajas afectadas»; ubicación, momento del día y umbral pasaron a «Detalle de las celdas marcadas» ({ref(SEC, 'evento = st.dataframe(tabla, key="tabla_celdas"')}). Cola: «Clase» y «Tipo de caso» se ven sin desplazar a 1366 px (anchos fijos de columna); las nueve columnas caben a 1366 y 1920 px.
- **B4.** La columna cuenta, para cada caja de la cola, cuántos fotogramas de la cola son del mismo objeto; no cambia el orden ni ninguna cifra. El encabezado completo no cabe a 1366 px, por eso se rotula «Fotogramas» y el nombre completo queda en la ayuda de la columna, en la nota bajo la tabla y en el CSV de descarga.
- **B5.** Enteros sin decimales, C en notación científica (1,0e-5), nombres legibles de hiperparámetros y valores en español; se revisaron las seis pestañas de Evidencia y se corrigió además un «-0,000» engañoso y la distancia del control deslizante de «Explica una caja» («25.00» → «25»). Prueba: `test_ninguna_tabla_de_evidencia_tiene_formatos_enganosos`.
- **B6.** Streamlit no permite cambiar los textos del cargador por configuración: se ocultan con CSS (`font-size: 0`) y se escribe el texto en español con `::before`. **Riesgo:** depende de los nombres internos `data-testid` de Streamlit 1.65; si una versión futura los cambia, el cargador volvería a mostrar el texto en inglés (no se rompe nada más). Una prueba vigila que el CSS exista.
- **B7.** Azul continuo contra naranja discontinuo (se distinguen por el trazo y no solo por el color). **Causa del bug de leyenda:** con la banda sombreada codificada por el mismo campo con `legend=None`, Vega-Lite fusiona las leyendas y borra la de las líneas (se vio en el DOM); la banda ahora es una capa por curva con color fijo y la leyenda solo lista las curvas dibujadas.
- **B8.** Inicio muestra «≈ {ini['horas_dos_pasos']:.0f} h para encontrar el 80 %» contra «≈ {ini['horas_sin_orden']:.0f} h revisando sin orden», con la nota «Estimación en muestra, 20 s por caja (supuesto)»; las dos cifras salen de `inicio_resumen` ({ref(LOG, "def inicio_resumen")}), del mismo origen que antes (`ie12__brazo_C_y_equilibrio.csv` y la cola). La cifra anterior de ≈ 226 h ya no se muestra.
- **B9.** Tiempos medidos con un navegador sin interfaz y perfil nuevo (`data/08_reporting_ep3/pagina_arranque.json`, `scripts/ep3/f19_medir_arranque.py`, {len(con)} arranques en frío por variante): con el lanzador, el servidor responde y la precarga termina antes de la primera visita; la primera visita a «Explica una caja» tarda {segundos(con, "primera_visita_explica_s")} s y ninguna sección tarda más de {max_sec} s después; sin el lanzador (`streamlit run` directo) la primera visita tarda {segundos(sin, "primera_visita_explica_s")} s. La primera visita incluye la descarga del frontend de Streamlit por un navegador sin caché; es una medición de este equipo, no una garantía.

## h) F20: rediseño como herramienta de trabajo (P1 a P12)
*Las cifras de la página no cambiaron (se validan contra `data/08_reporting_ep3/pagina_numeros_antes.json`): cambió la presentación, la navegación y qué cifra va primero. Pruebas en `tests/ep3/test_pagina_f20.py` y en los archivos de pruebas anteriores, actualizados al nuevo esquema.*

| Ítem | Estado | Dónde |
|---|---|---|
| P0 Auditoría de diseño contra los patrones de plantilla | **Hecho** | `docs/ep3/auditoria_diseno_pagina.md` |
| P1 Marco: `st.navigation` agrupada, marca (símbolo y nombre), rol al pie; el chip de estado se quitó en F26 | **Hecho** (páginas de archivo: DEC-57) | {ref(APP, "pg = st.navigation(")}, {ref(SEC, "def encabezado")} |
| P2 Sistema visual (un acento, bordes de 1 px, radio 6 px, Segoe UI, cifras tabulares) | **Hecho** | {ref(EST, "def css")}, `guia_estilo_pagina.md` |
| P3 Resumen (F20; reestructurado en F23, F27 y F29: indicadores, alertas de cámara con anillo, cola prioritaria y segmentos prioritarios; cifras de apoyo en Validación; impacto estimado (358, 200 y 132 h) en Validación › En muestra) | **Hecho** | {ref(SEC, "def resumen")}, {ref(LOG, "def indicadores_resumen")} |
| P4 Cola como maestro-detalle (dos flujos, selección de fila, vista por objeto, filtros) | **Hecho** | {ref(SEC, "def cola")}, {ref(LOG, "def tabla_por_objeto")}, {ref(LOG, "def detalle_caja")}, {ref(LOG, "def filtrar_cola")} |
| P5 Auditoría en dos columnas, una leyenda, etiquetas de 6 dígitos | **Hecho** | {ref(SEC, "def auditoria")}, {ref(SEC, "def _mapa_calor")} |
| P6 Explica una caja con ejemplos de un clic y texto de posición corregido | **Hecho** | {ref(SEC, "def explica")}, {ref(LOG, "EJEMPLOS_CAJA = ")}, {ref(LOG, "def texto_posicion")} |
| P7 Validación: un gráfico por pestaña y tabla completa en un expander | **Hecho** (límite abajo) | {ref(SEC, "def validacion")}, {ref(LOG, "def datos_validacion")} |
| P8 Puntuar: archivos como tabla y segmento de desarrollo de ejemplo | **Hecho** (el ejemplo suma las celdas marcadas de desarrollo ya calculadas, F37) | {ref(SEC, "def puntuar")}, {ref(LOG, "def ejemplo_lidar_box")} |
| P9 Ética como ficha de 6 bloques y Ayuda con glosario en tabla | **Hecho** | {ref(SEC, "def etica")}, {ref(SEC, "def ayuda")} |
| P10 Pasada de redacción y prueba de frases prohibidas | **Hecho** | {ref(TF20, "FRASES_PROHIBIDAS = ")} |
| P11 Captura robusta, causa del render incompleto y dos pasadas de corrección | **Hecho** | {ref(CAP, "def esperar")}, {ref(CAP, "def linea_de_tiempo")}, `auditoria_diseno_pagina.md` |
| P12 Pruebas y tiempos por página con la precarga | **Hecho**: {tiempos_f20} | {ref(TF20, "def test_seleccionar_una_fila_abre_el_panel_de_detalle")}, `data/08_reporting_ep3/pagina_arranque_f20.json` |

**Limitaciones y pendientes de F20 (con su motivo):**
1. **Prueba con personas de cada rol y en otros equipos y navegadores** (motivo: requiere personas y equipos). Solo se verificó con pruebas automáticas, `AppTest` y capturas a 1366 y 1920 px.
2. **Validación, pestaña Generalización:** el AUC por partición solo trae 3 candidatos (Regla top, LR3 y XGB), porque la copia de la página (`data/09_app_ep3/evidencia/posthoc__auc_por_fold_y_brazos.csv`) solo los incluye; `f5_auc_por_fold.csv` tiene los 11. Ampliarla exige copiar ese CSV con `scripts/ep3/f7_preparar_app.py`, y `data/09_app_ep3` no está entre las carpetas donde F20 podía escribir. Una prueba comprueba que los 3 candidatos coinciden con `f5_auc_por_fold.csv`.
3. **CSS sobre atributos internos de Streamlit 1.65** (`data-testid` del cargador, de la barra lateral y de la tabla,): si una versión futura los cambia, la página sigue funcionando pero pierde ese estilo (el cargador volvería al inglés y el chip se vería como un botón normal).
4. **Selección de fila:** depende de `st.dataframe(on_select="rerun")` de Streamlit 1.65; las pruebas simulan la selección escribiendo `st.session_state["tabla_cola"]` (AppTest no puede hacer clic en una tabla); el clic real se verificó en las capturas.
5. **Ejemplo de «Puntuar datos nuevos»:** se reconstruye desde las variables derivadas de `cajas_oof` (no son datos crudos de Waymo) y no trae archivo de asociación (no se puede reconstruir a qué cámara pertenece cada caja sin inventarlo), así que no hay auditoría de cámaras en el ejemplo.
6. **Errores 404 internos de Streamlit en subrutas** (`/cola/_stcore/health`, `/cola/_stcore/host-config`): Streamlit los pide relativos a la subruta y se resuelve solo; la captura los cuenta aparte (`404_internos_de_streamlit`) y no son errores de la página.
7. **Idioma de los menús de los gráficos y de los mensajes del navegador:** los controla el navegador; los textos y cifras de la página sí están en es-CL.
8. **Nombre «Inicio» y «Evidencia»:** ya no existen (ahora «Resumen» y «Validación»); los documentos históricos de F18 y F19 (`REPORTE_F18.md`, `REPORTE_F19B.md`) conservan los nombres de su fecha.

## i) F21: última ronda de pulido (P1 a P7)
*Las cifras de la página no cambiaron (regresión contra `pagina_numeros_antes.json`: `test_las_cifras_no_cambian_salvo_el_redondeo_unificado` en `tests/ep3/test_pagina_rediseno.py`); cambiaron disposición, textos y formato. Pruebas en `tests/ep3/test_pagina_f21.py`. Detalle de las dos pasadas de diseño: `auditoria_diseno_pagina.md`.*

| Ítem | Estado | Dónde |
|---|---|---|
| P1 Cola: nota del empate calculada, orden de columnas, panel de detalle debajo de la tabla | **Hecho**: nueve columnas visibles a 1366 px sin desplazamiento; el panel va debajo porque a la derecha dejaba la tabla en unos 700 px | {ref(LOG, "def nota_empate")}, {ref(SEC, "def _panel_detalle")}, {ref(SEC, "def _config_columnas_cola")} |
| P2 Explica: puntaje sin «-50,000», controles que dicen qué mueven, escala no lineal con los puntos A y B, «Cómo se calcula», ejemplos en una fila | **Hecho**: solo el control del sensor superior mueve la probabilidad (se verificó) | {ref(SEC, "def explica")}, {ref(LOG, "ESCALA_PUNTOS = ")}, {ref(LOG, "def texto_puntaje")} |
| P3 Resumen: enlaces de alertas en su fila, nota sin archivos y popover «Fuente», «en muestra» a lo más dos veces (reemplazado por F29: filas de alerta con «Auditar», sin «en muestra») | **Hecho** (medido con el DOM en las capturas) | {ref(SEC, "def resumen")}, {ref(EST, "st-key-celda_")} |
| P4 Redacción: «En validación cruzada por segmentos» en lugar de «Fuera de pliegue»; sin archivos, «pliegue», «fold», «OOF» ni «brazo A/B/C» en pantalla | **Hecho** (una prueba recorre las ocho páginas) | {ref(FMT, "def traducir_folds")}, {ref(TF21, "def test_ninguna_pagina_muestra_terminos_internos")} |
| P5 Validación: seis pestañas revisadas con captura | **Hecho** (marcas del eje, nombres de componentes, tablas sin archivos, leyendas completas) | {ref(SEC, "def _grafico_validacion")}, {ref(SEC, "def _marcas_eje")} |
| P6 Capturas (8 páginas, cola sin selección y 6 pestañas; 1366 y 1920 px; sin el modo presentación desde F30) y dos pasadas de corrección | **Hecho** | {ref(CAP, "PESTANAS_VALIDACION")}, `auditoria_diseno_pagina.md` |
| P7 Pruebas, regresión de cifras y tiempos | **Hecho**: {tiempos_f21} | {ref(TF21, "def test_la_nota_del_empate_se_calcula_de_la_cola_y_desaparece_sin_empate")}, `data/08_reporting_ep3/pagina_arranque_f21.json` |

**Pendientes y límites de F21 (con su motivo):**
1. **Un «%» se separa de su número solo en los textos que no pasan por `estilos._e` ni por `formato.sin_corte`** (motivo: Streamlit no permite un espacio de no separación global; se aplicó donde las capturas mostraron el corte: Ética, Explica y los textos HTML). Una cola o una pregunta frecuente muy larga todavía podría partirse.
2. **El mapa de la Auditoría mantiene un contenedor de 560 px con desplazamiento** (41 segmentos × 20 px no caben): es un diseño de F20, no un defecto nuevo.
3. **Los identificadores («Marca de tiempo», «Identificador de objeto») quedan a la derecha de «Segmento» y a 1366 px requieren desplazamiento horizontal**: son datos de trabajo, no de lectura; van en el panel de detalle y en el CSV.
4. **Tiempos medidos con un navegador sin interfaz en este equipo** (motivo: no hay otros equipos ni personas); las pruebas con una persona de cada rol siguen pendientes (límite 1 de F20).

## Hallazgos nuevos
1. **Doble redondeo en la evidencia:** `f7_preparar_app.py` copiaba las tablas de evidencia con 4 decimales y la página las volvía a redondear a 3 (p. ej. recall de ciclistas 0,4435 → «0,444» en vez de 0,443). Corregido: se copian con 8 decimales (el resto de `data/09_app_ep3` quedó idéntico).
2. **Rótulos de k = 4:** los clusters 1 y 3 de k = 4 comparten rótulo (tasas 14,8 % y 10,7 %), pero la página usa k = 2 (`k_elegido` del artefacto congelado), por eso no hace falta diferenciarlos en pantalla.
3. **Enlace directo a una sección** (`?seccion=Cola de revisión`): agregado para las capturas ({ref(APP, "st.query_params.get")}).
4. **Pendiente (motivo: licencia y datos):** «Puntuar datos nuevos» se probó con archivos sintéticos y con la lógica sobre datos reales, pero no se subió un parquet crudo de `lidar_box` en un navegador (los datos crudos no se redistribuyen).
5. **Parcialmente resuelto (F19-B6):** el cargador de archivos ya sale en español (con CSS, ver el riesgo en B6). **Sigue pendiente (motivo: no controlable desde el código):** otros textos propios de Streamlit (menús de los gráficos, mensajes del navegador) y los números de las etiquetas de ejes y tooltips de los gráficos usan el idioma y el formato del navegador; los textos y cifras de la página sí están en es-CL.
6. **Resuelto (F19-B9):** los tiempos de carga ahora también se miden en un navegador real sin interfaz (`pagina_arranque.json`); los de `pagina_tiempos_carga.json` siguen siendo de servidor con `AppTest`. **Pendiente (motivo: requiere equipos y personas):** medir en otros equipos y navegadores.
"""
    (RAIZ / "docs/ep3/PENDIENTES_PAGINA.md").write_text(nombre_visible(md), encoding="utf-8")
    print("escrito PENDIENTES_PAGINA.md")


if __name__ == "__main__":
    main()
