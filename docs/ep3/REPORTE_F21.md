# Reporte de la tarea F21: última ronda de pulido de la página y ajustes de documentos

*Generado por `scripts/ep3/generar_reporte_f21.py`; cifras de `data/08_reporting_ep3` (`pagina_arranque_f20.json` = el «antes», `pagina_arranque_f21.json` = el «después», `capturas_resultado.json`, `pruebas_ep3_conteo.json`), de `docs/ep3/guion_presentacion.md`, `pagina_guia_demo.md`, `auditoria_diseno_pagina.md` y de la misma lógica que usa la página. Decisiones: `ESTADO.md` (DEC-71 en adelante, sección F21). Las cifras de la página no cambiaron: la prueba `test_las_cifras_no_cambian_salvo_el_redondeo_unificado` (`tests/ep3/test_pagina_rediseno.py`) las compara con `data/08_reporting_ep3/pagina_numeros_antes.json` y pasa. El zip y la copia limpia NO se rearmaron.*

## Resumen
La cola de revisión ahora abre con la nota del empate (calculada de la cola) y nueve columnas visibles a 1366 px sin desplazamiento, con el panel de detalle debajo de la tabla a todo el ancho; «Explica una caja» dejó de mostrar «-50,000», dice qué control mueve la probabilidad y usa una escala de puntos no lineal con los puntos A (32) y B (11) marcados en el gráfico; el Resumen alinea el chip y los enlaces de sus alertas y dice «en muestra» a lo más dos veces; ninguna pantalla muestra nombres de archivo, «pliegue», «fold», «OOF» ni «brazo A/B/C»; y las seis pestañas de Validación se revisaron una por una. Se hicieron **dos pasadas de corrección** con capturas de 1366 y 1920 px. Documentos: la guía de demo se partió en un recorrido corto de 95 s (6 pasos, la misma fuente que el guion) y uno extendido de respaldo; las preguntas cruzadas son 79. Pruebas: 190 recolectadas en `tests/ep3` (13 nuevas de F21): `190 passed, 28 warnings in 62.93s (0:01:02)` (código 0; 64 s). Capturas: 30 de 30 listas (la más lenta en estar completa: 3,1 s). Documentos: 22 revisados, 0 con problemas. Verificaciones: EP2 «Plan v2 congelado el 2026-10-18T13:42:13-03:00: coinciden 14 de 14 archivos»; v3 «v3 congelado el 2026-11-14T12:15:26 (candidato Regla top): coinciden 5 de 5 archivos»; no supervisado «no supervisado (k = 2, creado 2026-11-14T13:03:31): coinciden 1 de 1 archivos».

## Bloque P: la página

### P1. Cola de revisión
- **Qué encontré:** a 1366 px el área de contenido mide 1.062 px y la tabla, con las columnas calculadas con 6,6 px por carácter, dejaba «Segmento» fuera de la vista; el texto real de la tabla mide 5,5 a 5,6 px por carácter (medido sobre la captura: «lejanos y poco densos» ocupa 117 px para 21 caracteres). El panel a la derecha, además, dejaba la tabla en unos 700 px.
- **Qué cambié:** (a) la **nota del empate** se calcula de la cola (`empate_inicial` y `nota_empate`, `app_logica.py`): «Las primeras N cajas empatan (0 puntos del sensor superior; …); el orden entre ellas no es informativo», y desaparece si no hay empate. Con los datos reales dice «Las primeras 4.742 cajas empatan» (las 4.757 con 0 puntos del informe menos las que quedan en celdas marcadas). La primera versión decía «probabilidad de 80,2 % a 90,4 %» mientras todas las filas muestran 87,8 %; la pasada 1 la corrigió a «87,8 % en la primera y de 80,2 % a 90,4 % en el grupo» (el rango existe porque cada partición calibró por separado). (b) **Orden de columnas:** Posición, Prob. sin pareja, Puntos sensor sup., Clase, Fotogramas, Cámara, Tipo de caso, Distancia, Segmento (después, los identificadores); anchos medidos: las nueve columnas suman 999 px más 37 de la selección, contra 1.062 disponibles; «Tipo de caso» no lleva ancho fijo y nunca se corta. (c) **Panel de detalle debajo de la tabla, a todo el ancho** (dos columnas internas; sin fila elegida explica qué trae el detalle): elegí esto frente al panel lateral (deja la tabla en ~700 px y corta columnas) y frente a `st.dialog` (tapa la tabla que se está leyendo y suma un clic para volver). Capturas con la primera fila elegida y sin selección, a 1366 y 1920 px; a 1920 la tabla muestra además «Marca de tiempo» e «Identificador de objeto».
- **Fuente de las cifras:** `data/09_app_ep3/cajas_oof.parquet` (misma lógica que la página); el 4.757 y el 90,5 % salen de `f12_eda_calidad_resumen.json`.

### P2. Explica una caja
- **Qué encontré:** el texto de puntaje decía «-50,000» (el puntaje es un entero con signo: menos los puntos del sensor superior) y nada decía qué control mueve la probabilidad. Lo verifiqué con una prueba: al llevar los puntos del LiDAR a 1.000 la probabilidad no cambia; al cambiar los del sensor superior, sí (`test_el_control_de_puntos_del_lidar_no_mueve_la_probabilidad_y_el_de_sensor_superior_si`). Los puntos totales, la distancia y la clase solo afectan al tipo de caso (la clase, además, agrega la advertencia de ciclista).
- **Qué cambié:** «Puntaje: -50 (menos los puntos del sensor superior)»; cada control dice qué mueve («este control mueve la probabilidad», «solo afecta al tipo de caso», «solo agrega la advertencia de ciclista»); los puntos se eligen con `select_slider` en la escala no lineal 0, 1, 2, 5, 10, 11, 20, 32, 50, 60, 100, 200, 500, 1000, 2000 (incluye 11 y 32, los puntos B y A congelados); el gráfico usa escala comprimida con líneas finas «Punto B» y «Punto A»; bloque «Cómo se calcula» de tres líneas sin nombres internos; los tres ejemplos en una fila.

### P3. Resumen
- **Qué encontré:** el chip se alineaba con la columna del encabezado y no con el borde del contenido; los enlaces de las alertas quedaban 8 px más arriba que su texto (el markdown de Streamlit lleva margen inferior negativo); la nota del gráfico nombraba archivos; «en muestra» aparecía tres veces.
- **Qué cambié:** chip al borde derecho del contenido en todas las páginas (también con descripciones de dos líneas y en modo presentación); cada alerta en su contenedor con su enlace en la misma fila; nota «Estimación en muestra: cajas × fracción para el 80 % × 20 s por caja (supuesto, no medido)» con un popover «Fuente» (informe técnico, sección 12 y anexo B); la alerta de validación dice «Todas las cifras salen de los 41 segmentos de desarrollo». Quedan dos «en muestra» (etiqueta de la barra y nota).
- **Medido con el DOM** (`capturas_resultado.json`, 30 capturas): chip contra el borde derecho del contenido, máximo 0,0 px; enlace de cada alerta contra el centro de su texto, máximo 3,3 px (12 alertas); desplazamiento horizontal de la página, máximo 0 px.

### P4. Redacción
- **Qué cambié:** «Fuera de pliegue» pasó a «En validación cruzada por segmentos» (`formato.traducir_folds`; el rótulo «AUC fuera de fold» de la ficha de Ética y de los resultados de Validación); «pliegue» y «fold» pasan a «partición»; sin nombres de archivo en pantalla (la columna «Fuente» de los resultados de Validación se quitó y la fuente va en una línea; los mensajes de error ya no nombran rutas); «Proporción menos probabilidad de la regla», que no es un porcentaje, pasó a «Diferencia: proporción menos probabilidad de la regla». Una prueba nueva recorre las ocho páginas y las seis pestañas buscando .csv/.json, «pliegue», «fold», «OOF», «brazo A/B/C» y snake_case (`test_ninguna_pagina_muestra_terminos_internos`), y `FRASES_PROHIBIDAS` incluye «Fuera de pliegue». Los nombres de columnas del dataset que la persona debe llevar en su archivo (tabla «Archivos de entrada» de Puntuar) quedan: son datos del formato, no términos internos.

### P5. Validación (seis pestañas)
Capturé y leí las seis pestañas a 1366 y 1920 px (`images/ep3/pagina/05_validacion_<pestaña>_<ancho>.png`). Defectos corregidos: etiquetas repetidas del eje en Ensambles, «vista obs», columna de archivos y «Detalle» cortado en Selección, barras superpuestas en No supervisado y leyenda cortada en «En muestra» (detalle en las dos pasadas, abajo).

### P6. Capturas y dos pasadas de corrección
- 15 capturas por ancho (8 páginas, cola sin selección, 6 pestañas de Validación y el modo presentación; las de F20 están en `images/ep3/pagina/antes_f21/`); la geometría (chip, alertas y desplazamiento) se mide con el DOM en cada captura.
- **Pasada 1** (primeras capturas de 1366 px):
- Cola (T12): «Segmento» quedaba cortado a 1366 px porque el ancho de las columnas suponía 6,6 px por carácter y el texto real mide 5,5 a 5,6 (medido sobre la captura: «lejanos y poco densos» ocupa 117 px para 21 caracteres). Constantes medidas (`formato.PX_POR_CARACTER` = 5,6 de encabezado y 5,5 de contenido) y «Tipo de caso» sin ancho fijo: las nueve columnas quedan visibles sin desplazamiento.
- Cola: la nota del empate decía «probabilidad de 80,2 % a 90,4 %» mientras todas las filas visibles muestran 87,8 %. Ahora: «87,8 % en la primera y de 80,2 % a 90,4 % en el grupo» (el rango existe porque cada partición calibró por separado).
- Resumen (T9): los enlaces de las alertas quedaban 8 px más arriba que su texto, porque el markdown de Streamlit lleva margen inferior negativo y acorta la columna del texto. CSS que lo anula (`[class*="st-key-alerta_"]`); la diferencia medida baja a 3 o 4 px.
- Resumen: «en muestra» salía tres veces (etiqueta de la barra, nota y alerta); la alerta ahora dice «Todas las cifras salen de los 41 segmentos de desarrollo». Quedan dos.
- Validación, Ensambles: las etiquetas del eje se repetían (−0,04, −0,04, −0,03, −0,03…) por usar dos decimales con un paso de 0,005; las marcas se calculan (`_marcas_eje`). «E4 contra vista obs» pasó a «vista de observación».
- Validación, Selección (T12): la tabla de resultados tenía una columna «Fuente» con nombres de archivo (.csv) y «Detalle» cortado; se quitó la columna (la fuente va en una línea: informe técnico, sección 12 y anexo B) y «Detalle» usa su ancho. La tabla O1 a O4 tenía una fila vacía al pie (altura de 31 px por fila contra 30 reales).
- Validación, No supervisado: las dos barras se superponían y las etiquetas salían cortadas («lejanos y poco d…»); altura por categoría y etiquetas completas.
- Validación, En muestra: la leyenda salía cortada («Solo celdas sanas, sin aud…»); leyenda completa y valores sobre las barras.
- Tablas de evidencia: «Proporción menos probabilidad de la regla» no era un porcentaje; pasó a «Diferencia: proporción menos probabilidad de la regla» (la prueba de formatos engañosos lo detectó).
- **Pasada 2** (regeneración completa, 1366 y 1920 px):
- Ética (1366 px): «79,8» y «%» quedaban en líneas distintas; Explica (1920 px): «20» y «% de las cajas». Los textos HTML (`estilos._e`) y los textos largos de Explica (`formato.sin_corte`) usan espacio de no separación entre el número y «%».
- Cola: con la nota más larga del empate, el final del texto («…no es informativo») quedaba bajo la barra de herramientas de la tabla (los iconos de descarga y búsqueda, que Streamlit dibuja sobre la esquina superior derecha); se acortó la frase («87,8 % en la primera y de 80,2 % a 90,4 % en el grupo») y la nota reserva ese espacio a la derecha (`padding-right`), de modo que si no cabe pasa a dos líneas.
- Mensajes de error con rutas internas (`data/06_models_ep3`, `scripts/ep3/f7_preparar_app.py`): la prueba nueva de términos internos los encontró; ahora dicen qué falta sin nombrar archivos.
- Aceptado sin cambio: la Auditoría mantiene el mapa en un contenedor de 560 px con desplazamiento (41 filas); en Validación y Auditoría la descripción ocupa dos líneas y el chip queda centrado en vertical, pero a la misma distancia del borde derecho; la tabla de Selección muestra su borde inferior.
- Documentos generados: `auditoria_diseno_pagina.md` (sección F21 con las dos pasadas y las mediciones), `guia_estilo_pagina.md`, `pagina_guia_demo.md` y `PENDIENTES_PAGINA.md` (sección i).

### P7. Pruebas, cifras y tiempos
- 13 pruebas nuevas en `tests/ep3/test_pagina_f21.py` (nota del empate calculada, orden y anchos de las columnas, escala de los puntos, «-50,000», control que mueve la probabilidad, «en muestra» a lo más dos veces, alineación medida, términos internos, marcas de los ejes, pestañas sin columna de archivos y capturas completas) y las de F19 y F20 adaptadas al nuevo orden de columnas, al panel debajo de la tabla, a los `select_slider` y a «Partición».
- **Tiempos de carga** (navegador sin interfaz y perfil nuevo, 2 arranques en frío por variante; `pagina_arranque_f20.json` = F20, `pagina_arranque_f21.json` = F21; «completa» = script terminado y último elemento presente, sin contar los 2 s de estabilidad que pide la captura; de cada página se toma la captura más lenta):

| | F20 (antes) | F21 (después) |
|---|---|---|
| Con lanzador: primera visita (s) | 2,9 | 2,9 a 11,0 |
| Con lanzador: página más lenta después de la primera (s) | 1,3 | 1,5 a 5,4 |
| Sin lanzador: primera visita (s) | 4,3 | 4,1 a 4,2 |
| Servidor responde, con lanzador (s) | 3,2 | 3,1 a 3,2 |

| Página | F20, peor de los arranques con lanzador (s) | F21, peor de los arranques con lanzador (s) |
|---|---|---|
| Resumen | 1,3 | 5,0 |
| Cola de revisión | 1,1 | 5,4 |
| Explica una caja | 1,1 | 4,0 |
| Auditoría de cámaras | 1,1 | 4,3 |
| Validación | 1,3 | 3,1 |
| Puntuar datos nuevos | 1,1 | 1,1 |
| Ética y límites | 1,1 | 1,1 |
| Ayuda y glosario | 1,0 | 1,1 |

Meta «ninguna página más de 3 s tras el arranque»: NO se cumple en todas las páginas (ver arriba) con el lanzador. Sin el lanzador, ningún arranque supera los 3 s. Es una medición de este equipo, no una garantía; la primera visita incluye la descarga del frontend de Streamlit por un navegador sin caché.

**Corrida previa conservada** (`pagina_arranque_f21_corrida1.json`): con lanzador, primera visita 2,9 a 3,1 s y página más lenta 1,4 a 1,5 s; sin lanzador, primera visita 4,3 a 20,0 s y página más lenta 1,5 a 7,3 s. En las dos corridas juntas (8 arranques), 2 superaron los 3 s: fueron arranques aislados (precargas o primeras visitas de 20,0, 11,0 s, con todas las páginas lentas a la vez) y el otro arranque de la misma variante en la misma corrida estuvo dentro de la meta; apunta a carga puntual del equipo (hipótesis, no verificada), no a una página. Se conservan las dos corridas, sin descartar ninguna.

## Bloque D: los documentos
- **D1. Guía de demo.** `pagina_guia_demo.md` ahora tiene el **«Recorrido corto (95 s, 6 pasos)»**, que sale de la misma fuente (`demo_pasos`) que el bloque «Demo de la página» del guion, con su tiempo por paso, y el «Recorrido extendido (respaldo)» con los 13 pasos de antes, actualizado. El paso de la cola dice en una frase por qué las primeras filas empatan («Las primeras filas empatan porque todas tienen 0 puntos del sensor superior») y el siguiente muestra la nota del empate. El paso 2 quedó en 25 s porque con 20 s sus 53 palabras daban 159 por minuto (límite 140). Palabras por paso:

| Tiempo | Paso | Palabras | Palabras/min |
|---|---|---|---|
| 0:00 a 0:15 (15 s) | Resumen y chip | 33 | 132 |
| 0:15 a 0:40 (25 s) | Cola con ambos flujos | 53 | 127 |
| 0:40 a 0:55 (15 s) | Selección de una fila y nota del empate | 35 | 140 |
| 0:55 a 1:10 (15 s) | Auditoría | 18 | 72 |
| 1:10 a 1:25 (15 s) | Explica con «Ciclista lejano» | 29 | 116 |
| 1:25 a 1:35 (10 s) | Validación | 16 | 96 |

- **Guion:** 1029 palabras en 9:15 (≈ 111 palabras por minuto en promedio); ningún bloque supera 140 y los bloques técnicos siguen entre 105 y 135 por minuto. Palabras por bloque:

| Tiempo | Bloque | Palabras | Palabras/min |
|---|---|---|---|
| 0:00 a 0:40 | El problema | 46 | 69 |
| 0:40 a 1:25 | La idea en dos pasos | 52 | 69 |
| 1:25 a 2:10 | Datos y plan | 97 | 129 |
| 2:10 a 2:50 | Filtro 1 | 88 | 132 |
| 2:50 a 4:15 | IE9 e IE10 | 154 | 109 |
| 4:15 a 5:45 | IE11 e IE12 | 182 | 121 |
| 5:45 a 6:10 | No supervisado | 51 | 122 |
| 6:10 a 7:45 | Demo de la página | 196 | 124 |
| 7:45 a 8:45 | Lo que sabemos, lo que no sabemos y cómo lo vamos a saber | 119 | 119 |
| 8:45 a 9:15 | Recomendaciones | 44 | 88 |

- **D2. Preguntas cruzadas** (79 en total): **Q39** dice ahora «el mejor modelo entrenado sin la regla es LR3 con 0,808; E2, que la incluye como componente, 0,824» (`f5_metricas_candidatos.csv`). **Q73** (sellado): `manifest_v3.json` trae **3** hashes y la verificación incluye además el plan v3 (2): «5 de 5»; y «lo hace la persona» pasó a «hacemos commit y push antes de evaluar». **Q74** (¿y si no hay huecos?): agrega la tasa por celda (2 de 111, 1,8 %; probabilidad de ninguno ≈ 27 %) y la concentración en San Francisco de día (2 de 7 segmentos; con 8 segmentos nuevos de ese estrato, (5/7)^8 ≈ 7 %), ambas de los mismos datos con que se ajustó el detector, así que son optimistas, y el rango «entre ≈ 7 % y ≈ 27 %» rotulado post hoc, con fuente. **Q21 y Q61** llevan una línea: el conteo observado da 44,6 % y la curva guardada interpolada 44,7 %. **Dos preguntas nuevas:** «¿por qué las primeras cajas de la cola tienen la misma probabilidad?» (4.757 cajas con 0 puntos; 90,5 % sin pareja; el orden no es informativo; se atiende por objeto) y «¿cuál es el valor de negocio en una frase?» (cifras de `f6_modelo_escogido.csv`, con el rótulo «en muestra»). El informe (§4) agrega la frase del empate junto a las 4.757 cajas.
- **D3. Regenerados** desde sus generadores: informe, README_EP3, preguntas, guion, guía de demo, guía de estilo, pendientes de la página, mapa de archivos, auditoría de diseño, `docs/ep3/revision/`, los contadores de ESTADO y `plan_integracion_readme.md`, y los notebooks 11 a 15 (RECALCULAR = False; el 14 con la prueba de humo de las 8 páginas x 3 roles y el modo presentación). Revisión automática de tablas y caracteres de control: sin problemas.

## Verificaciones y reglas
- Congelados de EP2: **Plan v2 congelado el 2026-10-18T13:42:13-03:00: coinciden 14 de 14 archivos**. Solución v3: **v3 congelado el 2026-11-14T12:15:26 (candidato Regla top): coinciden 5 de 5 archivos**. No supervisado: **no supervisado (k = 2, creado 2026-11-14T13:03:31): coinciden 1 de 1 archivos**.
- Archivos sellados o protegidos con fecha de modificación posterior al fin de F20: **ninguno**. EP2 solo se leyó; sin git (solo `status`, `diff` y `log`); sin paquetes instalados; sin bucket, gcloud ni Docker; la página no hace peticiones externas (una prueba lo vigila) y no se tocaron las claves de seguridad de `.streamlit/config.toml`.

## Bloqueos
- Ninguno que detuviera el trabajo. Límites anotados con su motivo en `PENDIENTES_PAGINA.md` (sección i): un «%» todavía puede separarse de su número en textos que no pasan por `estilos._e` ni por `formato.sin_corte`; el mapa de la Auditoría mantiene su contenedor de 560 px con desplazamiento; los identificadores quedan a la derecha de «Segmento» y a 1366 px requieren desplazamiento.

## Lo que te toca
1. Abrir la página con `scripts\ep3\arrancar_app.bat` y mirar las capturas de `images/ep3/pagina/` (1366 y 1920 px) y la sección F21 de `auditoria_diseno_pagina.md`.
2. Ensayar el **recorrido corto de 95 s** con el guion (`pagina_guia_demo.md`) y repartir los bloques («Quién»).
3. Probar con personas de cada rol y en otro equipo o navegador (sigue pendiente).
4. Sigue pendiente lo de siempre: commit del sello antes del Colab, la validación externa y rearmar el zip y la copia limpia (otra tarea).
