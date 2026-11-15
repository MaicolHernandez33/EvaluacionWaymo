"""Genera docs/ep3/PENDIENTES_PAGINA.md: estado de cada mejora de la pagina (resuelta, con archivo y linea, o pendiente con motivo) y hallazgos nuevos.

F18-C15: tras el rediseno de app/ casi todo esta resuelto; lo que no, queda con su motivo. Las lineas se buscan por texto ancla en el codigo actual
(si cambian app/ o app_logica.py, volver a correr este script). Las cifras salen de f12_equidad.csv y de la misma logica que usa la pagina.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.app_logica import cargar_datos, resumen_cola  # noqa: E402

APP = RAIZ / "app/app.py"
SEC = RAIZ / "app/secciones.py"
LOG = RAIZ / "src/waymo_evaluacion/ep3/app_logica.py"
EST = RAIZ / "app/estilos.py"
TST = RAIZ / "tests/ep3/test_pagina_rediseno.py"


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
    md = f"""# Pendientes de la página: estado tras el rediseño (F18-C)

*Generado por `scripts/ep3/generar_pendientes_pagina.py`. Las líneas se buscan por texto en el código actual; si `app/` cambia, volver a correr el script. Lo «resuelto» tiene archivo y línea y una prueba en `tests/ep3/test_pagina_rediseno.py`.*

| Ítem | Estado |
|---|---|
| a) «Recall esperado» como titular | **Resuelto** |
| b) Textos de un solo segmento con «Todos» | **Resuelto** |
| c) Redondeo distinto entre tarjeta y texto | **Resuelto** |
| d) Presupuesto por defecto | **Resuelto** (ya era 20 %; ahora explícito) |
| e) Pulido visual y contenido por perfil | **Resuelto** en lo que se puede verificar sin usuarios; queda una prueba con personas |
| f) Aviso de ciclistas | **Resuelto** |

## a) «Recall esperado (todos los segmentos)» no sirve como titular: resuelto
- La frase principal es «Revisando N cajas se encontrarían unas X de cada 100 cajas sin pareja» ({ref(SEC, "_html(E.resultado(E.md_a_html(texto_resultado_cola(r))))")}; texto en {ref(LOG, "def texto_resultado_cola")}). La palabra «recall» ya no es titular (queda solo en el nombre técnico de las tablas de Evidencia).
- El bloque plegable «¿Qué tan confiable es esto?» ({ref(SEC, 'with st.expander("¿Qué tan confiable es esto?")')}) trae el intervalo, el aviso «en muestra» y la diferencia entre un paso y dos pasos.
- Control inverso «Quiero encontrar X % de las cajas sin pareja» ({ref(SEC, "MODO_OBJETIVO = ")} y {ref(SEC, "presup = round(curva_inversa")}; lógica en {ref(LOG, "def curva_inversa")}). Prueba: `test_control_inverso_es_consistente_con_la_curva`.
- Visible en modo presentación (el modo solo oculta identificadores y agranda la letra; prueba `test_humo_8_secciones_x_3_perfiles`).

## b) Con «Segmento: Todos» aparecían textos de segmento único: resuelto
- Textos distintos para «Todos los segmentos» (con intervalo por segmentos) y para un segmento (sin intervalo): {ref(LOG, "def texto_resultado_cola")}. Prueba: `test_textos_distintos_para_todos_y_un_segmento`.

## c) Inconsistencia de redondeo entre la tarjeta y el texto: resuelto
- Antes: al 68 % la tarjeta decía 96,5 % y el texto 96,6 % ({pc(r68['cobertura_curva'], 2)} de la curva interpolada contra {pc(r68['cobertura'], 2)} del conteo observado); al 20 %, 70,2 % contra 70,3 %.
- Ahora hay **una sola fuente**, el conteo observado ({ref(LOG, "def resumen_cola")}): al 20 % la página dice «unas {round(100 * r20['cobertura'])} de cada 100» ({pc(r20['cobertura'])}) y al 68 % «unas {round(100 * r68['cobertura'])} de cada 100» ({pc(r68['cobertura'])}). La curva solo aporta el intervalo. Documentado en `data/08_reporting_ep3/pagina_comparacion_antes_despues.csv`. Prueba: `test_fuente_unica_de_la_cobertura`.

## d) Presupuesto por defecto: resuelto
- El código ya partía en 20 % (el 68 % que se vio una vez era un valor movido a mano); ahora el valor está en el estado de la página ({ref(SEC, 'st.session_state.setdefault("presupuesto", 20)')}) y hay un botón «Volver al 20 %» ({ref(SEC, "def _volver_a_20")}). Prueba: `test_cola_control_inverso_y_boton_volver_al_20`.

## e) Pulido visual y contenido por perfil: resuelto salvo la prueba con personas
- Guía de estilo `guia_estilo_pagina.md`, tokens y contraste >= 4,5:1 ({ref(EST, "TOKENS = ")}; prueba `test_tokens_cumplen_contraste_y_coinciden_con_el_tema`), tema en `.streamlit/config.toml` y `app/.streamlit/config.toml`, encabezado y pie, tarjetas, pasos, íconos Material (sin emojis; prueba `test_la_pagina_no_usa_emojis`).
- El perfil decide la sección sugerida ({ref(APP, "def al_cambiar_perfil")}) y las acciones de Inicio ({ref(LOG, "ACCIONES_PERFIL = ")}): analista de revisión, la cola; responsable de calidad de datos, la auditoría de cámaras; ingeniero consumidor de datos, puntuar datos nuevos.
- **Pendiente (motivo: requiere personas):** probar el rediseño con usuarios reales de cada perfil; hoy solo se verificó con pruebas automáticas y capturas (`images/ep3/pagina/`).

## f) Aviso de ciclistas: resuelto
- La regla es poco confiable para ciclistas: {ci['recall_A']:.3f} contra {pe['recall_A']:.3f} en peatones, con {int(ci['positivos'])} positivos en {int(ci['segmentos'])} segmentos (`f12_equidad.csv`).
- Cola de revisión: columna «Clase» con la advertencia ({ref(LOG, "CLASE_ADVERTENCIA = ")}) y un aviso bajo la tabla si hay ciclistas ({ref(SEC, "Hay ciclistas en esta lista")}). Explica una caja: selector «Clase» y advertencia con las cifras ({ref(SEC, 'clase = c4.radio("Clase"')}). Prueba: `test_tabla_de_la_cola_oculta_identificadores_y_avisa_de_ciclistas`.

## Hallazgos nuevos
1. **Doble redondeo en la evidencia:** `f7_preparar_app.py` copiaba las tablas de evidencia con 4 decimales y la página las volvía a redondear a 3 (p. ej. recall de ciclistas 0,4435 → «0,444» en vez de 0,443). Corregido: se copian con 8 decimales (el resto de `data/09_app_ep3` quedó idéntico).
2. **Rótulos de k = 4:** los clusters 1 y 3 de k = 4 comparten rótulo (tasas 14,8 % y 10,7 %), pero la página usa k = 2 (`k_elegido` del artefacto congelado), por eso no hace falta diferenciarlos en pantalla.
3. **Enlace directo a una sección** (`?seccion=Cola de revisión`): agregado para las capturas ({ref(APP, "st.query_params.get")}).
4. **Pendiente (motivo: licencia y datos):** «Puntuar datos nuevos» se probó con archivos sintéticos y con la lógica sobre datos reales, pero no se subió un parquet crudo de `lidar_box` en un navegador (los datos crudos no se redistribuyen).
5. **Pendiente (motivo: no controlable desde el código):** los textos propios de Streamlit (por ejemplo «Browse files» del cargador de archivos) salen en inglés, y los números de las etiquetas de ejes y tooltips de los gráficos usan el formato del navegador; los textos y cifras de la página sí están en es-CL.
6. **Pendiente (motivo: medición en navegador):** los tiempos de carga (`pagina_tiempos_carga.json`) son de servidor con `AppTest`; no incluyen el dibujado en un navegador real.
"""
    (RAIZ / "docs/ep3/PENDIENTES_PAGINA.md").write_text(md, encoding="utf-8")
    print("escrito PENDIENTES_PAGINA.md")


if __name__ == "__main__":
    main()
