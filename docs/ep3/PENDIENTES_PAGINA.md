# Pendientes de la página (no se corrigió nada; `app/` no se modificó)

*Generado por `scripts/ep3/generar_pendientes_pagina.py`. Las líneas se buscan por texto en el código actual; si `app/app.py` cambia, volver a correr el script. Cifras: `f12_equidad.csv` y la misma lógica de `app_logica.py` sobre `data/09_app_ep3`. Prioridad sugerida: c, d, b, f, a, e.*

## a) «Recall esperado (todos los segmentos)» no sirve como titular
- Dónde: `app/app.py:134` (tarjeta `m1`); el texto técnico (IC por segmentos, «fuera de fold») va en el `help`.
- Qué hacer: reemplazarlo por lenguaje simple dentro de un bloque plegable (`st.expander`) «¿Qué tan confiable es esto?» y agregar un **control inverso**: «quiero encontrar X %» y la página dice cuánto revisar (invertir la curva guardada con `numpy.interp` sobre `curva_cola.csv`; la función de ida está en `src/waymo_evaluacion/ep3/app_logica.py:74`). Mantenerlo visible con el modo presentación activo (`app/app.py:60` solo oculta identificadores).

## b) Con «Segmento: Todos» aparecen textos de un solo segmento
- Dónde: `app/app.py:135` («Cajas a revisar en este segmento»), `app/app.py:137` («En el segmento elegido…») y `app/app.py:138` («Es un solo segmento: no tiene IC por segmentos»). El selector con «Todos» está en `app/app.py:125`.
- Qué hacer: ramificar por `seg == "Todos"`: con «Todos», decir «en los 41 segmentos» y mostrar el IC por segmentos de la curva; con un segmento, el texto actual.

## c) Inconsistencia de redondeo entre la tarjeta y el texto
- Dónde: tarjeta `app/app.py:134` (usa la curva interpolada, `src/waymo_evaluacion/ep3/app_logica.py:74`) y texto `app/app.py:137` (usa el conteo observado `recall_proceso`, `src/waymo_evaluacion/ep3/app_logica.py:105` dentro de `src/waymo_evaluacion/ep3/app_logica.py:90`).
- Evidencia (reproducida con la lógica de la página, «Todos»): al 68 % la tarjeta dice **96,5 %** y el texto **96,6 %** (16.513 de 17.102); al 20 % dice **70,2 %** y **70,3 %**. La diferencia (0,02 puntos) pasa a 0,1 al redondear a un decimal.
- Qué hacer: una sola fuente (la tarjeta y el texto deben leer el mismo valor) y un solo redondeo; si se quiere mostrar el valor observado y el esperado, rotularlos distinto.

## d) Presupuesto por defecto
- Se pidió que parta en 20 % (punto B del informe). **En el código ya parte en 20:** `app/app.py:126` (`st.slider(..., 1, 100, 20)`), y una corrida de `AppTest` hecha al preparar este documento lo confirma (valor 20 al abrir «Cola de revisión»). El 68 % que se vio en pantalla coincide con un valor movido a mano o con el estado del navegador, no con el valor por defecto; no se encontró otra causa en el código. Si se vuelve a ver, revisar el estado de sesión de Streamlit (recargar la página).
- Qué hacer (opcional): fijar `key="presupuesto"` y un botón «volver al 20 %» para que el valor por defecto sea explícito.

## e) Pulido visual y contenido por perfil
- Dónde: perfil en `app/app.py:59`; sección sugerida en `app/app.py:62`; textos de cada perfil en `src/waymo_evaluacion/ep3/app_logica.py:23`; Inicio en `app/app.py:79`.
- Hoy el perfil solo cambia la sección sugerida y un mensaje. Qué debería ver primero cada perfil:
  - **Analista de revisión:** la Cola de revisión con el presupuesto y el control inverso (a), los segundos por caja y la descarga de la cola.
  - **Responsable de calidad de datos:** la Auditoría de cámaras (mapa de calor y Lista A) y, debajo, qué significa un hueco y que la causa no se conoce.
  - **Ingeniero consumidor de datos:** «Puntuar datos nuevos» y, antes, la confiabilidad (aviso «en muestra», ciclistas, falsas alarmas del detector sin estimar).
- Pulido general: jerarquía de títulos, menos texto en Inicio, colores de las dos columnas del flujo, y el aviso «en muestra» más corto pero visible.

## f) Aviso de ciclistas
- Hecho a documentar: la regla es poco confiable para ciclistas: recall **0,443** contra **0,806** en peatones, con **115** positivos en **14** segmentos (`f12_equidad.csv`).
- Dónde falta: (1) «Cola de revisión»: la tabla `app/app.py:147` no incluye la columna `es_ciclista`, que sí existe en `cajas_oof.parquet`; hay que mostrarla y avisar cuando la caja sea de un ciclista. (2) «Explica una caja» (`app/app.py:152`): los controles `app/app.py:166` no tienen un selector de clase y la fila base usa la mediana (`es_ciclista` = 0), así que no puede avisar; agregar «¿Es ciclista?» y mostrar el aviso.
