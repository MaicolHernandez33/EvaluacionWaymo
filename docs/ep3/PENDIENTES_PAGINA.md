# Pendientes de la página: estado tras el rediseño (F18-C)

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
- La frase principal es «Revisando N cajas se encontrarían unas X de cada 100 cajas sin pareja» (`app/secciones.py:132`; texto en `src/waymo_evaluacion/ep3/app_logica.py:237`). La palabra «recall» ya no es titular (queda solo en el nombre técnico de las tablas de Evidencia).
- El bloque plegable «¿Qué tan confiable es esto?» (`app/secciones.py:135`) trae el intervalo, el aviso «en muestra» y la diferencia entre un paso y dos pasos.
- Control inverso «Quiero encontrar X % de las cajas sin pareja» (`app/secciones.py:24` y `app/secciones.py:129`; lógica en `src/waymo_evaluacion/ep3/app_logica.py:208`). Prueba: `test_control_inverso_es_consistente_con_la_curva`.
- Visible en modo presentación (el modo solo oculta identificadores y agranda la letra; prueba `test_humo_8_secciones_x_3_perfiles`).

## b) Con «Segmento: Todos» aparecían textos de segmento único: resuelto
- Textos distintos para «Todos los segmentos» (con intervalo por segmentos) y para un segmento (sin intervalo): `src/waymo_evaluacion/ep3/app_logica.py:237`. Prueba: `test_textos_distintos_para_todos_y_un_segmento`.

## c) Inconsistencia de redondeo entre la tarjeta y el texto: resuelto
- Antes: al 68 % la tarjeta decía 96,5 % y el texto 96,6 % (96,54 % de la curva interpolada contra 96,56 % del conteo observado); al 20 %, 70,2 % contra 70,3 %.
- Ahora hay **una sola fuente**, el conteo observado (`src/waymo_evaluacion/ep3/app_logica.py:222`): al 20 % la página dice «unas 70 de cada 100» (70,3 %) y al 68 % «unas 97 de cada 100» (96,6 %). La curva solo aporta el intervalo. Documentado en `data/08_reporting_ep3/pagina_comparacion_antes_despues.csv`. Prueba: `test_fuente_unica_de_la_cobertura`.

## d) Presupuesto por defecto: resuelto
- El código ya partía en 20 % (el 68 % que se vio una vez era un valor movido a mano); ahora el valor está en el estado de la página (`app/secciones.py:119`) y hay un botón «Volver al 20 %» (`app/secciones.py:106`). Prueba: `test_cola_control_inverso_y_boton_volver_al_20`.

## e) Pulido visual y contenido por perfil: resuelto salvo la prueba con personas
- Guía de estilo `guia_estilo_pagina.md`, tokens y contraste >= 4,5:1 (`app/estilos.py:10`; prueba `test_tokens_cumplen_contraste_y_coinciden_con_el_tema`), tema en `.streamlit/config.toml` y `app/.streamlit/config.toml`, encabezado y pie, tarjetas, pasos, íconos Material (sin emojis; prueba `test_la_pagina_no_usa_emojis`).
- El perfil decide la sección sugerida (`app/app.py:55`) y las acciones de Inicio (`src/waymo_evaluacion/ep3/app_logica.py:174`): analista de revisión, la cola; responsable de calidad de datos, la auditoría de cámaras; ingeniero consumidor de datos, puntuar datos nuevos.
- **Pendiente (motivo: requiere personas):** probar el rediseño con usuarios reales de cada perfil; hoy solo se verificó con pruebas automáticas y capturas (`images/ep3/pagina/`).

## f) Aviso de ciclistas: resuelto
- La regla es poco confiable para ciclistas: 0.443 contra 0.806 en peatones, con 115 positivos en 14 segmentos (`f12_equidad.csv`).
- Cola de revisión: columna «Clase» con la advertencia (`src/waymo_evaluacion/ep3/app_logica.py:179`) y un aviso bajo la tabla si hay ciclistas (`app/secciones.py:168`). Explica una caja: selector «Clase» y advertencia con las cifras (`app/secciones.py:189`). Prueba: `test_tabla_de_la_cola_oculta_identificadores_y_avisa_de_ciclistas`.

## Hallazgos nuevos
1. **Doble redondeo en la evidencia:** `f7_preparar_app.py` copiaba las tablas de evidencia con 4 decimales y la página las volvía a redondear a 3 (p. ej. recall de ciclistas 0,4435 → «0,444» en vez de 0,443). Corregido: se copian con 8 decimales (el resto de `data/09_app_ep3` quedó idéntico).
2. **Rótulos de k = 4:** los clusters 1 y 3 de k = 4 comparten rótulo (tasas 14,8 % y 10,7 %), pero la página usa k = 2 (`k_elegido` del artefacto congelado), por eso no hace falta diferenciarlos en pantalla.
3. **Enlace directo a una sección** (`?seccion=Cola de revisión`): agregado para las capturas (`app/app.py:64`).
4. **Pendiente (motivo: licencia y datos):** «Puntuar datos nuevos» se probó con archivos sintéticos y con la lógica sobre datos reales, pero no se subió un parquet crudo de `lidar_box` en un navegador (los datos crudos no se redistribuyen).
5. **Pendiente (motivo: no controlable desde el código):** los textos propios de Streamlit (por ejemplo «Browse files» del cargador de archivos) salen en inglés, y los números de las etiquetas de ejes y tooltips de los gráficos usan el formato del navegador; los textos y cifras de la página sí están en es-CL.
6. **Pendiente (motivo: medición en navegador):** los tiempos de carga (`pagina_tiempos_carga.json`) son de servidor con `AppTest`; no incluyen el dibujado en un navegador real.
