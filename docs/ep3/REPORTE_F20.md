# Reporte de la tarea F20: rediseño de la página como herramienta de trabajo y cierre de documentos

*Generado por `scripts/ep3/generar_reporte_f20.py`; cifras de `data/08_reporting_ep3` (`pagina_arranque.json`, `pagina_arranque_f20.json`, `capturas_resultado.json`, `pruebas_ep3_conteo.json`, `captura_linea_tiempo_*.json`), de `docs/ep3/guion_presentacion.md` y de la misma lógica que usa la página. Decisiones: `ESTADO.md` (DEC-57 en adelante, sección F20). Las cifras de la página no cambiaron: se validan contra `pagina_numeros_antes.json` y la regresión de cifras. El zip y la copia limpia NO se rearmaron.*

## Resumen
La página pasó de parecer una landing de plantilla a una consola interna de revisión: navegación agrupada (`st.navigation`), wordmark propio, rol al pie, **un solo chip** de estado «Datos de desarrollo · sin validación externa» (con el texto completo de «en muestra» en su popover) y un sistema visual sobrio (un acento, bordes de 1 px, Segoe UI, cifras tabulares). La cola de revisión es ahora **maestro-detalle** (dos flujos a la vista, selección de fila con panel de detalle, vista por objeto y filtros). La causa del render incompleto de «Ética y límites» en la captura fue **la captura, no la página** (ver más abajo). Se hicieron dos pasadas de corrección con las capturas. Pruebas: 177 recolectadas en `tests/ep3` (32 nuevas de F20): `177 passed, 28 warnings in 58.27s` (código 0; 59 s). Capturas: 18 de 18 listas (la más lenta en estar completa: 2,9 s). Documentos: 21 revisados, 0 con problemas. Verificaciones: EP2 «Plan v2 congelado el 2026-10-18T13:42:13-03:00: coinciden 14 de 14 archivos»; v3 «v3 congelado el 2026-11-14T12:15:26 (candidato Regla top): coinciden 5 de 5 archivos»; no supervisado «no supervisado (k = 2, creado 2026-11-14T13:03:31): coinciden 1 de 1 archivos».

## Bloque P: la página
### P0. Auditoría previa (`auditoria_diseno_pagina.md`)
- **Qué encontré:** leí las 9 capturas de F19-B a 1366 px contra 12 patrones de plantilla (T1 a T12): portada de marketing, tarjetas KPI con borde de color, píldora de perfil y producto repetido, banner ámbar con acordeón en cada pantalla, aviso «Nada se guarda ni se envía» repetido, menú de radios, textos que hablan de la propia página, acordeones en todo, ninguna interacción de producto, títulos y cifras gigantes, pantallas vacías y tablas con encabezados cortados.
- **Qué cambié:** el documento lista, por sección, el defecto y lo que se haría; lo generó `scripts/ep3/generar_auditoria_diseno.py`.

### P1 y P2. Marco, navegación y sistema visual
- **Qué encontré:** `st.navigation` solo funciona con `AppTest` si las páginas son **archivos** (`switch_page` exige una ruta; con funciones falla): lo probé en un experimento aislado antes de escribir código (DEC-57).
- **Qué cambié:** `app/app.py` es ahora el marco (configuración, estilos, wordmark SVG propio con `st.logo`, navegación agrupada en Revisión / Calidad de datos / Análisis / Herramientas / Ayuda, rol y modo presentación al pie, pie único); cada sección es un archivo corto de `app/paginas/`. Solo se renombraron Inicio → Resumen y Evidencia → Validación. El rol cambia la página que se abre (con una bandera de sesión, porque `st.switch_page` no es fiable en un callback) y ordena primero su alerta. `?seccion=` sigue funcionando. Sin banners ámbar ni «¿Qué significa?»: el chip único cumple DEC-14 y cada cifra del flujo en dos pasos lleva «en muestra». Estilos en `app/estilos.py` (sin sombras, sin bordes de color, radio de 6 px, un solo acento, rojo solo para hueco y ámbar solo para «en muestra»; contraste ≥ 4,5:1 verificado).

### P3. Resumen
- Cuatro métricas compactas (cajas analizadas 80.571, 21,2 % sin pareja, 2 celdas marcadas, 41 segmentos) y «Impacto estimado»: barras de horas a 20 s por caja para encontrar el 80 %: **≈ 358 h** revisando sin orden, **≈ 200 h** solo cola (un paso; el titular, lo robusto) y **≈ 132 h** auditoría + cola (dos pasos, rotulada «en muestra»). Origen: `ie12__brazo_C_y_equilibrio` (= `f6_modelo_escogido.csv`) y el número de cajas; 200 h = fracción un paso × cajas × 20 s. Tres alertas con enlace (celdas marcadas, ciclistas con cifras de `f12_equidad.csv`, validación externa pendiente). Sin «Cómo funciona» ni «Empiece por aquí». Las cinco cifras de validación que estaban en un acordeón de Inicio pasaron a la pestaña Selección de Validación.

### P4. Cola de revisión (maestro-detalle)
- Barra de controles en una fila (segmento, flujo, modo, control con su unidad y «Volver al 20 %»), filtros por clase y cámara y «Agrupar por objeto» en la misma barra; el flujo por defecto sigue siendo «Auditoría + cola (dos pasos, en muestra)».
- La frase de resultado muestra **siempre ambos flujos**: «Con auditoría previa (en muestra): unas 70 de cada 100 · Solo cola: unas 62 de cada 100», más cajas a revisar y horas del flujo elegido (el valor de un paso es el conteo observado; coincide con la curva guardada con menos de 0,6 puntos; prueba).
- Pestañas «Curva de cobertura» y «Cola de cajas»; «Supuestos y confiabilidad» en un popover único.
- Tabla con selección de fila (`on_select="rerun"`): el panel de detalle (probabilidad calibrada, posición en la cola, tipo de caso, cámara, distancia, puntos, advertencia de ciclista) reutiliza la lógica de «Explica una caja». La columna «Prioridad» (barra saturada en 100) se reemplazó por la **probabilidad calibrada** (`prob_cal`); no cambió el orden ni las cifras. «Agrupar por objeto» deja una fila por objeto con su mejor posición y los fotogramas en la cola (el conteo de cajas no cambia; prueba). Los filtros solo cambian la vista («Filtrado: N cajas») y no las cifras globales. Encabezados con el ancho calculado (`formato.anchos_columnas`): ya no hay «Posició».

### P5 a P9
- **Auditoría de cámaras:** dos columnas (mapa en un contenedor de altura fija con desplazamiento; a la derecha métricas mínimas, Lista A con «Acción sugerida» y descarga), **una sola leyenda**, etiquetas de segmento de 6 dígitos (únicas en los 41; el id completo va en el tooltip), orden por defecto con las celdas marcadas primero y opción de ver solo celdas con datos suficientes; se conservan el rojo con X y el gris rayado (2 huecos y 94 de 205 celdas sin datos suficientes, igual que antes).
- **Explica una caja:** dos columnas (controles y resultado), tres ejemplos de un clic («Caja cercana y densa», «Caja lejana con pocos puntos», «Ciclista lejano») y el texto «Posición en la cola: 59 % (0 % es la primera caja; 100 %, la última)». Verifiqué el significado en `percentil_en_cola`: es la fracción de la cola que queda **antes** de la caja. Encontré además que el gráfico de «Detalle técnico» era una línea plana (variaba los puntos totales y la regla usa los del sensor superior): ahora muestra la probabilidad según los puntos del sensor superior con la selección marcada.
- **Validación:** cada pestaña abre con un gráfico leído de los CSV (mejora de PR-AUC con IC, diferencia de AUC con IC, AUC con IC por candidato y por pliegue, tasa por tipo de caso, brazos A, B y C con la etiqueta) y la tabla completa en un expander; «Pliegues» en lugar de «Folds»; Selección abre con el cuadro O1 a O4 (nadie cumple O2 ni O4). **Límite:** el AUC por pliegue trae 3 candidatos porque `f5_auc_por_fold.csv` no está completo en `data/09_app_ep3` y F20 no puede escribir ahí (anotado en `PENDIENTES_PAGINA.md`).
- **Puntuar datos nuevos:** «Archivo 1 (obligatorio)» y «Archivo 2 (opcional)», formato esperado como tabla, estado vacío sobrio, resumen en tabla (sin `st.json`) y **«Usar un segmento de desarrollo de ejemplo»**: sí era posible sin datos crudos de Waymo (se reconstruye un `lidar_box` mínimo desde las variables derivadas de `cajas_oof`; la prueba comprueba que el orden de la cola coincide con el de la página). No trae archivo de asociación (reconstruirlo sería inventar a qué cámara pertenece cada caja), así que el ejemplo no audita cámaras.
- **Ética y Ayuda:** ficha de sistema en dos columnas (6 bloques, las mismas cifras: 0,443 contra 0,806; 115 casos en 14 segmentos; AUC 0,823), glosario como tabla de dos columnas, una línea con el flujo de tres capas y preguntas frecuentes como acordeones.

### P10. Redacción
Revisé los textos de `app/` y `app_logica.py` (registro neutro, sin segunda persona de tutorial, sin avisos repetidos). Una prueba (`FRASES_PROHIBIDAS`) vigila «Empiece por aquí», «Cómo funciona», «la página se lo dice», «Mueva los controles», «vea qué pasa», «¿Qué significa?», «Primeros pasos», «Resultados técnicos» y «Pase el cursor», y que «Nada se guarda ni se envía» solo aparezca en Ayuda y Ética.

### P11. Capturas y control de calidad
- **Causa del render incompleto de «Ética y límites» (investigada):** **fue la captura, no un defecto de render.** La de 1366 px salió con 1 tarjeta y la de 1920 px, de la misma corrida, con las 5. Streamlit dibuja a medida que el script avanza y el criterio de F19-B (texto del primer elemento + sin spinner) no podía ver que el script seguía ejecutándose: en las líneas de tiempo en frío, el script estuvo ejecutándose en 46 muestras y el indicador del criterio antiguo apareció en 0 de ellas; en «Auditoría de cámaras» hubo 7 muestras con la página a medias. La precarga alarga la ventana (la primera visita espera los datos) pero no es la causa; en F20 cada sección carga el contexto antes de dibujar. Detalle en `auditoria_diseno_pagina.md`.
- **Espera nueva:** `data-test-script-state = notRunning`, DOM estable ≥ 2 s, **último** elemento clave y conteos (6 bloques en Ética), alto mínimo y pie; si no se cumple no guarda la imagen. Ya atrapó dos errores durante F20. Los 28 «404» de la consola son los pedidos internos de Streamlit a `/pagina/_stcore/...` y se cuentan aparte.
- **Capturas:** 8 secciones y el modo presentación a 1366 y 1920 px (18 imágenes en `images/ep3/pagina/`; las de F19-B, en `antes_f20/`). La cola se fotografía con «Cola de cajas» abierta y la primera fila elegida.
- **Dos pasadas de corrección** (detalle en `auditoria_diseno_pagina.md`): pasada 1, wordmark cortado, fuente con clave interna, Lista A desbordada, captura de la cola y modo presentación; pasada 2, chip cortado en modo presentación, «Tipo de caso» fuera de vista con el panel abierto, barra de desplazamiento de la barra lateral y conteos de la captura de Auditoría.

### P12. Pruebas y tiempos
- 32 pruebas nuevas en `tests/ep3/test_pagina_f20.py` y las anteriores adaptadas al nuevo esquema: humo de las 8 páginas x 3 roles x modo presentación, regresión de cifras contra `pagina_numeros_antes.json`, selección de fila y detalle, vista agrupada con el mismo conteo, frases prohibidas, ausencia de URLs externas, contraste, es-CL.
- **Tiempos de carga** (navegador sin interfaz y perfil nuevo, 2 arranques en frío por variante; `pagina_arranque.json` = F19-B, `pagina_arranque_f20.json` = F20; «completa» = script terminado y último elemento presente, sin contar los 2 s de estabilidad que pide la captura):

| | F19-B (antes) | F20 (después) |
|---|---|---|
| Con lanzador: primera visita (s) | 2,9 | 2,9 |
| Con lanzador: página más lenta después de la primera (s) | 1,2 a 1,3 | 1,3 |
| Sin lanzador: primera visita (s) | 3,3 a 4,1 | 4,3 |
| Servidor responde, con lanzador (s) | 3,1 a 3,2 | 3,2 |

| Página | F19-B, peor de los arranques con lanzador (s) | F20, peor de los arranques con lanzador (s) |
|---|---|---|
| Resumen | 1,2 | 1,3 |
| Cola de revisión | 0,4 | 1,1 |
| Explica una caja | 0,8 | 1,1 |
| Auditoría de cámaras | 1,3 | 1,1 |
| Validación | 0,8 | 1,3 |
| Puntuar datos nuevos | 1,2 | 1,1 |
| Ética y límites | 1,0 | 1,1 |
| Ayuda y glosario | 0,8 | 1,0 |

Lectura: con el lanzador la primera visita no cambió (2,9 s antes, 2,9 s ahora) y ninguna página pasa de 1,3 s después; sin el lanzador la primera visita fue de 4,3 s en F20 contra 3,3 a 4,1 s en F19-B (dentro de la dispersión de la medición). La carga en frío del servidor no depende del rediseño (la precarga es la misma de F19-B).

Meta «ninguna página más de 3 s tras el arranque»: se cumple con el lanzador. Es una medición de este equipo, no una garantía; la primera visita incluye la descarga del frontend de Streamlit por un navegador sin caché.

## Bloque D: los documentos
- **D1.** (C5) Nota en el anexo B y pregunta cruzada sobre el segmento `247562357599`, cámara 5: 184 positivos en 665 cajas con más de 100 puntos (27,7 %), la celda que aparece marcada con `frac` = 0,35 y que con los parámetros congelados **no** se marca; rotulada «post hoc, no pre-declarado, hipótesis no verificada» (`f12_eda_puntos_top_resumen.json`, `f12_sensibilidad_detector.csv`). (C6) Pregunta «¿por qué la solución contra la regla da diferencia cero fuera de muestra?» (la solución es `PuntuadorRegla`; qué se mide en su lugar; LR3 y XGBoost, DEV-4).
- **D2.** Cinco preguntas nuevas con respuesta, cifra y fuente: sellado, qué pasa si no hay huecos (caso A: con ≈ 70 celdas elegibles y 1,8 % en desarrollo se esperan ≈ 1,3 marcadas y la probabilidad de 0 es ≈ 27 %, estimación gruesa tipo Poisson, post hoc), por qué LR3 y XGBoost, cómo se eligieron los segmentos nuevos y su sesgo, y por qué el titular compara un paso contra el azar. Las preguntas cruzadas son ahora 77.
- **D3.** Las tablas del informe tomadas de CSV (sección 9 y anexos) pasan por `tabla_es`: coma decimal, miles con punto, encabezados legibles (sin snake_case ni «silhouette_muestra_20000») e intervalos de distancia con coma decimal y unidad («(2,26; 18,61] m»); el §14 se partió en cuatro subsecciones (sellado, qué se mide, alternativas, qué se medirá y casos de resultado) sin cambiar su contenido. Todas pasan el chequeo de tablas.
- **D4.** Guion: 985 palabras en 9:15 (≈ 106 palabras por minuto en promedio, antes ≈ 71); los bloques técnicos van entre 105 y 135 (con contenido nuevo de IE9 a IE12: diseño anidado, curvas de validación, bordes de grilla, leave-one-segment-out, brecha ajuste-validación, calibración y la regla de reserva DEV-2); la demo sigue el recorrido de la página rediseñada; se agregó el «Plan por resultado de la validación externa» (casos A a D).

| Tiempo | Bloque | Palabras | Palabras/min |
|---|---|---|---|
| 0:00 a 0:40 | El problema | 46 | 69 |
| 0:40 a 1:25 | La idea en dos pasos | 52 | 69 |
| 1:25 a 2:10 | Datos y plan | 97 | 129 |
| 2:10 a 2:50 | Filtro 1 | 88 | 132 |
| 2:50 a 4:15 | IE9 e IE10 | 154 | 109 |
| 4:15 a 5:45 | IE11 e IE12 | 182 | 121 |
| 5:45 a 6:10 | No supervisado | 51 | 122 |
| 6:10 a 7:45 | Demo de la página | 152 | 96 |
| 7:45 a 8:45 | Lo que sabemos, lo que no sabemos y cómo lo vamos a saber | 119 | 119 |
| 8:45 a 9:15 | Recomendaciones | 44 | 88 |

- **D5.** `REPORTE_F19A.md` dice ahora «al momento de F19-A: 116» y cita el conteo actual (`pruebas_ep3_conteo.json`: 177). Los reportes de F18 y F19-B son instantáneas de su fecha y no se regeneraron (usan los nombres Inicio y Evidencia).
- **D6.** Regenerados: informe, README_EP3, preguntas, guion, guía de demo, guía de estilo, pendientes de la página, mapa de archivos, auditoría de diseño, `docs/ep3/revision/` y los notebooks 11 a 15 (el 14 con la prueba de humo de las 8 páginas x 3 roles y el modo presentación). Los contadores de ESTADO y `plan_integracion_readme.md` se leen de `pruebas_ep3_conteo.json`.

## Verificaciones y reglas
- Congelados de EP2: **Plan v2 congelado el 2026-10-18T13:42:13-03:00: coinciden 14 de 14 archivos**. Solución v3: **v3 congelado el 2026-11-14T12:15:26 (candidato Regla top): coinciden 5 de 5 archivos**. No supervisado: **no supervisado (k = 2, creado 2026-11-14T13:03:31): coinciden 1 de 1 archivos**.
- Archivos sellados o protegidos con fecha de modificación posterior al inicio de F20: **ninguno**. EP2 solo se leyó; sin git (solo `status`, `diff` y `log`); sin paquetes instalados; sin bucket, gcloud ni Docker; la página no hace peticiones externas (una prueba lo vigila).

## Bloqueos
- Ninguno que detuviera el trabajo. Límites anotados con su motivo: el AUC por pliegue de Validación trae 3 candidatos (no se escribe en `data/09_app_ep3`); el ejemplo de «Puntuar» no trae asociación; el CSS depende de atributos internos de Streamlit 1.65 (`PENDIENTES_PAGINA.md`, sección h).

## Lo que te toca
1. Abrir la página con `scripts\ep3\arrancar_app.bat` y mirar las capturas de `images/ep3/pagina/` (1366 y 1920 px) y `auditoria_diseno_pagina.md`.
2. Probar con personas de cada rol y en otro equipo o navegador (sigue pendiente).
3. Decidir si el chip y la etiqueta «en muestra» te parecen suficientes para DEC-14 o prefieres algo más visible.
4. Revisar el guion y el «Plan por resultado» y repartir los bloques («Quién»).
5. Sigue pendiente lo de siempre: commit del sello antes del Colab, la validación externa y rearmar el zip y la copia limpia (otra tarea).
