# Pendientes de la página: estado tras el rediseño (F18-C, F19-B y F20)

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
- Desde F32 el resultado de la Cola son tres tarjetas («Cajas a revisar», «Cajas sin pareja que se encuentran» y «Tiempo estimado»; `app/secciones.py:499`; lógica en `src/waymo_evaluacion/ep3/app_logica.py:689`); el párrafo «Revisando N cajas se encontrarían unas X de cada 100» (`src/waymo_evaluacion/ep3/app_logica.py:468`) queda para otros usos. La palabra «recall» ya no es titular (queda solo en el nombre técnico de las tablas de Evidencia).
- El desplegable «Supuestos y confiabilidad» (F32: al final de la página; antes un popover y, antes, un acordeón «¿Qué tan confiable es esto?») (`app/secciones.py:514`) trae el supuesto de 20 s por caja, el aviso «en muestra», el intervalo y el punto de ciclistas.
- Control inverso «Quiero encontrar X % de las cajas sin pareja» (`app/secciones.py:40` y `app/secciones.py:492`; lógica en `src/waymo_evaluacion/ep3/app_logica.py:422`). Prueba: `test_control_inverso_es_consistente_con_la_curva`.
- Visible con los tres roles (prueba `test_humo_8_secciones_x_3_perfiles`); desde F30 ya no existe el modo presentación.

## b) Con «Segmento: Todos» aparecían textos de segmento único: resuelto
- Textos distintos para «Todos los segmentos» (con intervalo por segmentos) y para un segmento (sin intervalo): `src/waymo_evaluacion/ep3/app_logica.py:468`. Prueba: `test_textos_distintos_para_todos_y_un_segmento`.

## c) Inconsistencia de redondeo entre la tarjeta y el texto: resuelto
- Antes: al 68 % la tarjeta decía 96,5 % y el texto 96,6 % (96,54 % de la curva interpolada contra 96,56 % del conteo observado); al 20 %, 70,2 % contra 70,3 %.
- Ahora hay **una sola fuente**, el conteo observado (`src/waymo_evaluacion/ep3/app_logica.py:436`): al 20 % la página dice «unas 70 de cada 100» (70,3 %) y al 68 % «unas 97 de cada 100» (96,6 %). La curva solo aporta el intervalo. Documentado en `data/08_reporting_ep3/pagina_comparacion_antes_despues.csv`. Prueba: `test_fuente_unica_de_la_cobertura`.

## d) Presupuesto por defecto: resuelto
- El código ya partía en 20 % (el 68 % que se vio una vez era un valor movido a mano); ahora el valor está en el estado de la página (`app/secciones.py:480`) y hay un botón «Volver al 20 %» (`app/secciones.py:255`). Prueba: `test_cola_control_inverso_y_boton_volver_al_20`.

## e) Pulido visual y contenido por perfil: resuelto salvo la prueba con personas
- Guía de estilo `guia_estilo_pagina.md`, tokens y contraste >= 4,5:1 (`app/estilos.py:18`; prueba `test_tokens_cumplen_contraste_y_coinciden_con_el_tema`), tema en `.streamlit/config.toml` y `app/.streamlit/config.toml`, encabezado y pie, tarjetas, pasos, íconos Material (sin emojis; prueba `test_la_pagina_no_usa_emojis`).
- El perfil decide la sección sugerida (`app/app.py:35`) (en el Resumen ya no ordena alertas: F29) (`src/waymo_evaluacion/ep3/app_logica.py:23`): analista de revisión, la cola; responsable de calidad de datos, la auditoría de cámaras; ingeniero consumidor de datos, puntuar datos nuevos.
- **Pendiente (motivo: requiere personas):** probar el rediseño con usuarios reales de cada perfil; hoy solo se verificó con pruebas automáticas y capturas (`images/ep3/pagina/`).

## f) Aviso de ciclistas: resuelto
- La regla es poco confiable para ciclistas: 0.443 contra 0.806 en peatones, con 115 positivos en 14 segmentos (`f12_equidad.csv`).
- Cola de revisión: columna «Clase» con la advertencia (`src/waymo_evaluacion/ep3/app_logica.py:389`) y el panel de detalle trae la advertencia de ciclista (`app/secciones.py:322`). Explica una caja: selector «Clase» y advertencia con las cifras (`app/secciones.py:601`). Prueba: `test_tabla_de_la_cola_oculta_identificadores_y_avisa_de_ciclistas`.

## g) F19-B: pulido de la página (B1 a B10)
*Las cifras de la página no cambiaron: solo presentación, idioma y uso. Cada ítem tiene su prueba en `tests/ep3/test_pagina_pulido.py` (y en `test_pagina_rediseno.py`).*

| Ítem | Estado | Dónde |
|---|---|---|
| B1 «Explica una caja» en blanco en la captura | **Resuelto** (causa abajo) | `scripts/ep3/capturar_pagina.py:77`, `app/precarga.py:82` |
| B2 Mapa de calor: «sin datos» distinto de «tasa 0 %» | **Resuelto** | `src/waymo_evaluacion/ep3/app_logica.py:69`, `app/secciones.py:681`, `app/estilos.py:870` |
| B3 Lista A y Cola: columnas clave sin desplazar a 1366 y 1920 px | **Resuelto** | `src/waymo_evaluacion/ep3/app_logica.py:925`, `src/waymo_evaluacion/ep3/app_logica.py:942`, `app/secciones.py:349` |
| B4 Columna «Fotogramas del mismo objeto en la cola» | **Resuelto** (en pantalla se rotula «Fotogramas») | `src/waymo_evaluacion/ep3/app_logica.py:484`, `src/waymo_evaluacion/ep3/app_logica.py:489` |
| B5 Formatos de la tabla de hiperparámetros y revisión de las pestañas de Evidencia | **Resuelto** | `src/waymo_evaluacion/ep3/formato.py:115`, `src/waymo_evaluacion/ep3/formato.py:210`, `src/waymo_evaluacion/ep3/formato.py:210` |
| B6 Cargador de archivos en español y «Paso 2 (opcional)» | **Resuelto** con CSS (ver el riesgo abajo) | `app/secciones.py:1050`, `app/estilos.py:568` |
| B7 Colores de «Dos pasos» y «Un paso» | **Resuelto** | `app/estilos.py:56`, `app/secciones.py:272` |
| B8 Titular de horas de Inicio | **Resuelto** | `src/waymo_evaluacion/ep3/app_logica.py:617`, `app/secciones.py:242` |
| B9 Precarga de la solución congelada y los datos | **Resuelto** (medido en un navegador real) | `app/precarga.py:82`, `app/lanzar.py`, `app/app.py:30` |
| B10 Pruebas, capturas a 1366 y 1920 px y documentos | **Resuelto**: 26 capturas listas en `images/ep3/pagina/` | `data/08_reporting_ep3/capturas_resultado.json` |

- **B1, causa.** No era un error de la sección: la captura se tomó antes de que terminara la carga en frío (la página mostraba el esqueleto de carga, el texto del cuerpo tenía 0 caracteres y el PNG pesaba unos 9 KB); no hubo excepción en la consola del navegador ni en `AppTest`. «Explica una caja» es la sección que usa el modelo congelado y la más lenta en la primera visita en frío (B9), lo que la dejó más expuesta a la captura temprana (inferencia: no se probó con otra sección). Se corrigió en dos partes: la captura espera hasta que no haya indicador de carga y aparezca un texto propio de la sección (si no aparece, no guarda la imagen y sale con error), y la solución congelada y los datos se cargan y se calientan al arrancar (`app/precarga.py:54`).
- **B2.** Con 100 cajas como mínimo, 94 de 205 celdas (segmento × cámara) salen «sin cajas o menos de 100 en el rango» (gris rayado) y 2 son huecos (rojo con X); una tasa de 0 % con datos suficientes se ve como azul casi blanco. Se muestran todas las etiquetas de segmento. Cifras de `data/09_app_ep3/celdas.csv` y del umbral `min_cajas` de `detector_params_v3.json`.
- **B3.** Lista A: se ven «Acción sugerida» y «Cajas afectadas»; ubicación, momento del día y umbral pasaron a «Detalle de las celdas marcadas» (`app/secciones.py:733`). Cola: «Clase» y «Tipo de caso» se ven sin desplazar a 1366 px (anchos fijos de columna); las nueve columnas caben a 1366 y 1920 px.
- **B4.** La columna cuenta, para cada caja de la cola, cuántos fotogramas de la cola son del mismo objeto; no cambia el orden ni ninguna cifra. El encabezado completo no cabe a 1366 px, por eso se rotula «Fotogramas» y el nombre completo queda en la ayuda de la columna, en la nota bajo la tabla y en el CSV de descarga.
- **B5.** Enteros sin decimales, C en notación científica (1,0e-5), nombres legibles de hiperparámetros y valores en español; se revisaron las seis pestañas de Evidencia y se corrigió además un «-0,000» engañoso y la distancia del control deslizante de «Explica una caja» («25.00» → «25»). Prueba: `test_ninguna_tabla_de_evidencia_tiene_formatos_enganosos`.
- **B6.** Streamlit no permite cambiar los textos del cargador por configuración: se ocultan con CSS (`font-size: 0`) y se escribe el texto en español con `::before`. **Riesgo:** depende de los nombres internos `data-testid` de Streamlit 1.65; si una versión futura los cambia, el cargador volvería a mostrar el texto en inglés (no se rompe nada más). Una prueba vigila que el CSS exista.
- **B7.** Azul continuo contra naranja discontinuo (se distinguen por el trazo y no solo por el color). **Causa del bug de leyenda:** con la banda sombreada codificada por el mismo campo con `legend=None`, Vega-Lite fusiona las leyendas y borra la de las líneas (se vio en el DOM); la banda ahora es una capa por curva con color fijo y la leyenda solo lista las curvas dibujadas.
- **B8.** Inicio muestra «≈ 132 h para encontrar el 80 %» contra «≈ 358 h revisando sin orden», con la nota «Estimación en muestra, 20 s por caja (supuesto)»; las dos cifras salen de `inicio_resumen` (`src/waymo_evaluacion/ep3/app_logica.py:606`), del mismo origen que antes (`ie12__brazo_C_y_equilibrio.csv` y la cola). La cifra anterior de ≈ 226 h ya no se muestra.
- **B9.** Tiempos medidos con un navegador sin interfaz y perfil nuevo (`data/08_reporting_ep3/pagina_arranque.json`, `scripts/ep3/f19_medir_arranque.py`, 2 arranques en frío por variante): con el lanzador, el servidor responde y la precarga termina antes de la primera visita; la primera visita a «Explica una caja» tarda 2,9 s y ninguna sección tarda más de 1,3 s después; sin el lanzador (`streamlit run` directo) la primera visita tarda 3,3 a 4,1 s. La primera visita incluye la descarga del frontend de Streamlit por un navegador sin caché; es una medición de este equipo, no una garantía.

## h) F20: rediseño como herramienta de trabajo (P1 a P12)
*Las cifras de la página no cambiaron (se validan contra `data/08_reporting_ep3/pagina_numeros_antes.json`): cambió la presentación, la navegación y qué cifra va primero. Pruebas en `tests/ep3/test_pagina_f20.py` y en los archivos de pruebas anteriores, actualizados al nuevo esquema.*

| Ítem | Estado | Dónde |
|---|---|---|
| P0 Auditoría de diseño contra los patrones de plantilla | **Hecho** | `docs/ep3/auditoria_diseno_pagina.md` |
| P1 Marco: `st.navigation` agrupada, marca (símbolo y nombre), rol al pie; el chip de estado se quitó en F26 | **Hecho** (páginas de archivo: DEC-57) | `app/app.py:45`, `app/secciones.py:97` |
| P2 Sistema visual (un acento, bordes de 1 px, radio 6 px, Segoe UI, cifras tabulares) | **Hecho** | `app/estilos.py:576`, `guia_estilo_pagina.md` |
| P3 Resumen (F20; reestructurado en F23, F27 y F29: indicadores, alertas de cámara con anillo, cola prioritaria y segmentos prioritarios; cifras de apoyo en Validación; impacto estimado (358, 200 y 132 h) en Validación › En muestra) | **Hecho** | `app/secciones.py:140`, `src/waymo_evaluacion/ep3/app_logica.py:643` |
| P4 Cola como maestro-detalle (dos flujos, selección de fila, vista por objeto, filtros) | **Hecho** | `app/secciones.py:475`, `src/waymo_evaluacion/ep3/app_logica.py:521`, `src/waymo_evaluacion/ep3/app_logica.py:591`, `src/waymo_evaluacion/ep3/app_logica.py:581` |
| P5 Auditoría en dos columnas, una leyenda, etiquetas de 6 dígitos | **Hecho** | `app/secciones.py:692`, `app/secciones.py:671` |
| P6 Explica una caja con ejemplos de un clic y texto de posición corregido | **Hecho** | `app/secciones.py:550`, `src/waymo_evaluacion/ep3/app_logica.py:964`, `src/waymo_evaluacion/ep3/app_logica.py:977` |
| P7 Validación: un gráfico por pestaña y tabla completa en un expander | **Hecho** (límite abajo) | `app/secciones.py:905`, `src/waymo_evaluacion/ep3/app_logica.py:1038` |
| P8 Puntuar: archivos como tabla y segmento de desarrollo de ejemplo | **Hecho** (el ejemplo suma las celdas marcadas de desarrollo ya calculadas, F37) | `app/secciones.py:1159`, `src/waymo_evaluacion/ep3/app_logica.py:1076` |
| P9 Ética como ficha de 6 bloques y Ayuda con glosario en tabla | **Hecho** | `app/secciones.py:1199`, `app/secciones.py:1233` |
| P10 Pasada de redacción y prueba de frases prohibidas | **Hecho** | `tests/ep3/test_pagina_f20.py:406` |
| P11 Captura robusta, causa del render incompleto y dos pasadas de corrección | **Hecho** | `scripts/ep3/capturar_pagina.py:163`, `scripts/ep3/capturar_pagina.py:190`, `auditoria_diseno_pagina.md` |
| P12 Pruebas y tiempos por página con la precarga | **Hecho**: con el lanzador, la primera visita a «Explica una caja» tarda 2,9 s y ninguna página tarda más de 1,3 s después; sin el lanzador, la primera visita tarda 4,3 s | `tests/ep3/test_pagina_f20.py:209`, `data/08_reporting_ep3/pagina_arranque_f20.json` |

**Limitaciones y pendientes de F20 (con su motivo):**
1. **Prueba con personas de cada rol y en otros equipos y navegadores** (motivo: requiere personas y equipos). Solo se verificó con pruebas automáticas, `AppTest` y capturas a 1366 y 1920 px.
2. **Validación, pestaña Generalización:** el AUC por partición solo trae 3 candidatos (regla de puntos del sensor superior, LR3 y XGB), porque la copia de la página (`data/09_app_ep3/evidencia/posthoc__auc_por_fold_y_brazos.csv`) solo los incluye; `f5_auc_por_fold.csv` tiene los 11. Ampliarla exige copiar ese CSV con `scripts/ep3/f7_preparar_app.py`, y `data/09_app_ep3` no está entre las carpetas donde F20 podía escribir. Una prueba comprueba que los 3 candidatos coinciden con `f5_auc_por_fold.csv`.
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
| P1 Cola: nota del empate calculada, orden de columnas, panel de detalle debajo de la tabla | **Hecho**: nueve columnas visibles a 1366 px sin desplazamiento; el panel va debajo porque a la derecha dejaba la tabla en unos 700 px | `src/waymo_evaluacion/ep3/app_logica.py:566`, `app/secciones.py:307`, `app/secciones.py:349` |
| P2 Explica: puntaje sin «-50,000», controles que dicen qué mueven, escala no lineal con los puntos A y B, «Cómo se calcula», ejemplos en una fila | **Hecho**: solo el control del sensor superior mueve la probabilidad (se verificó) | `app/secciones.py:550`, `src/waymo_evaluacion/ep3/app_logica.py:963`, `src/waymo_evaluacion/ep3/app_logica.py:972` |
| P3 Resumen: enlaces de alertas en su fila, nota sin archivos y popover «Fuente», «en muestra» a lo más dos veces (reemplazado por F29: filas de alerta con «Auditar», sin «en muestra») | **Hecho** (medido con el DOM en las capturas) | `app/secciones.py:140`, `app/estilos.py:426` |
| P4 Redacción: «En validación cruzada por segmentos» en lugar de «Fuera de pliegue»; sin archivos, «pliegue», «fold», «OOF» ni «brazo A/B/C» en pantalla | **Hecho** (una prueba recorre las ocho páginas) | `src/waymo_evaluacion/ep3/formato.py:79`, `tests/ep3/test_pagina_f21.py:192` |
| P5 Validación: seis pestañas revisadas con captura | **Hecho** (marcas del eje, nombres de componentes, tablas sin archivos, leyendas completas) | `app/secciones.py:864`, `app/secciones.py:89` |
| P6 Capturas (8 páginas, cola sin selección y 6 pestañas; 1366 y 1920 px; sin el modo presentación desde F30) y dos pasadas de corrección | **Hecho** | `scripts/ep3/capturar_pagina.py:55`, `auditoria_diseno_pagina.md` |
| P7 Pruebas, regresión de cifras y tiempos | **Hecho**: 1 de 4 arranques salieron lentos de forma aislada (con todas las páginas lentas a la vez; carga puntual del equipo, hipótesis; ver el reporte de F21); el resto: con el lanzador, la primera visita a «Explica una caja» tarda 2,9 s y la página más lenta 1,5 s después; sin el lanzador, la primera visita tarda 4,1 a 4,2 s | `tests/ep3/test_pagina_f21.py:72`, `data/08_reporting_ep3/pagina_arranque_f21.json` |

**Pendientes y límites de F21 (con su motivo):**
1. **Un «%» se separa de su número solo en los textos que no pasan por `estilos._e` ni por `formato.sin_corte`** (motivo: Streamlit no permite un espacio de no separación global; se aplicó donde las capturas mostraron el corte: Ética, Explica y los textos HTML). Una cola o una pregunta frecuente muy larga todavía podría partirse.
2. **El mapa de la Auditoría mantiene un contenedor de 560 px con desplazamiento** (41 segmentos × 20 px no caben): es un diseño de F20, no un defecto nuevo.
3. **Los identificadores («Marca de tiempo», «Identificador de objeto») quedan a la derecha de «Segmento» y a 1366 px requieren desplazamiento horizontal**: son datos de trabajo, no de lectura; van en el panel de detalle y en el CSV.
4. **Tiempos medidos con un navegador sin interfaz en este equipo** (motivo: no hay otros equipos ni personas); las pruebas con una persona de cada rol siguen pendientes (límite 1 de F20).

## Hallazgos nuevos
1. **Doble redondeo en la evidencia:** `f7_preparar_app.py` copiaba las tablas de evidencia con 4 decimales y la página las volvía a redondear a 3 (p. ej. recall de ciclistas 0,4435 → «0,444» en vez de 0,443). Corregido: se copian con 8 decimales (el resto de `data/09_app_ep3` quedó idéntico).
2. **Rótulos de k = 4:** los clusters 1 y 3 de k = 4 comparten rótulo (tasas 14,8 % y 10,7 %), pero la página usa k = 2 (`k_elegido` del artefacto congelado), por eso no hace falta diferenciarlos en pantalla.
3. **Enlace directo a una sección** (`?seccion=Cola de revisión`): agregado para las capturas (`app/app.py:53`).
4. **Pendiente (motivo: licencia y datos):** «Puntuar datos nuevos» se probó con archivos sintéticos y con la lógica sobre datos reales, pero no se subió un parquet crudo de `lidar_box` en un navegador (los datos crudos no se redistribuyen).
5. **Parcialmente resuelto (F19-B6):** el cargador de archivos ya sale en español (con CSS, ver el riesgo en B6). **Sigue pendiente (motivo: no controlable desde el código):** otros textos propios de Streamlit (menús de los gráficos, mensajes del navegador) y los números de las etiquetas de ejes y tooltips de los gráficos usan el idioma y el formato del navegador; los textos y cifras de la página sí están en es-CL.
6. **Resuelto (F19-B9):** los tiempos de carga ahora también se miden en un navegador real sin interfaz (`pagina_arranque.json`); los de `pagina_tiempos_carga.json` siguen siendo de servidor con `AppTest`. **Pendiente (motivo: requiere equipos y personas):** medir en otros equipos y navegadores.
