# Guía de la demo de la página

*Generada por `scripts/ep3/generar_docs_ep3.py`; el «Recorrido corto» sale de la misma fuente (`demo_pasos`) que el bloque «Demo de la página» de `guion_presentacion.md` (1:35), así que dicen lo mismo. Las cifras salen de `data/09_app_ep3` con la misma lógica que la página (`app_logica.py`) y de `data/08_reporting_ep3`. Todas son en muestra: en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos.*

## Antes de empezar
1. Abrir con `scripts\ep3\arrancar_app.bat` (usa `app\lanzar.py`, que carga la solución congelada y los datos antes de aceptar visitas: espere unos 3 s; se abre en http://localhost:8501 y solo es accesible desde este equipo).
2. Rol «Analista de revisión» (al pie de la barra lateral).
3. Tener a mano «Ayuda y glosario» por si preguntan un término.

## Recorrido corto (95 s, 6 pasos)
Es el que se hace en la presentación: los seis pasos del bloque «Demo de la página» del guion, con su tiempo. Total 95 s; 191 palabras (121 por minuto; ningún paso supera 140).

| # | Tiempo | Paso | Qué hacer (clics) | Qué decir | Qué se ve | Palabras |
|---|---|---|---|---|---|---|
| 1 | 0:00 a 0:15 (15 s) | **Resumen y alertas** | Resumen, rol «Analista de revisión»; señalar los cuatro indicadores, el titular con las alertas de cámara y el anillo | «En el Resumen, tres filas: sin orden, unas 358 horas para encontrar el 80 %; solo con la cola, unas 200; con auditoría previa, unas 132, en muestra, con 20 segundos por caja.» | indicadores (21,2 % sin pareja, 2 cámaras con alerta); las dos alertas con su botón «Auditar» | 33 |
| 2 | 0:15 a 0:40 (25 s) | **Cola con ambos flujos** | Cola de revisión: «Todos», flujo «Auditoría + cola (dos pasos, en muestra)», presupuesto 20 % (parte ahí) | «En la cola, con todos los segmentos y el 20 %, con auditoría previa se encuentran unas 70 de cada 100 cajas sin pareja, en muestra, y solo con la cola unas 62 de cada 100: 15.726 cajas y 87,4 horas. Las primeras filas empatan porque todas tienen 0 puntos del sensor superior.» | frase con ambos flujos; 15.726 cajas, 87,4 h con 20 s por caja; la tabla abre con las cajas de 0 puntos | 53 |
| 3 | 0:40 a 0:55 (15 s) | **Selección de una fila y nota del empate** | Pestaña «Cola de cajas»; seleccionar la primera fila; leer la nota sobre la tabla | «Selecciono una fila y se llena el detalle: la probabilidad calibrada, la posición en la cola y el tipo de caso. La nota sobre la tabla lo confirma: el orden entre las empatadas no informa.» | panel de detalle a la derecha de la tabla, siempre visible; nota «Las primeras N cajas empatan (0 puntos del sensor superior…); el orden entre ellas no es informativo» | 35 |
| 4 | 0:55 a 1:10 (15 s) | **Auditoría** | Auditoría de cámaras: señalar el contorno rojo con X | «En la auditoría de cámaras vemos las dos celdas marcadas: no sabemos si faltan etiquetas o faltan datos.» | mapa de calor (gris plano = sin datos suficientes, no es 0 %); Lista A con «Acción sugerida» y «Cajas afectadas» | 18 |
| 5 | 1:10 a 1:25 (15 s) | **Explica con «Ciclista lejano»** | Explica una caja (menú «Herramientas»): ejemplo «Ciclista lejano» | «En «Explica una caja» uso el ejemplo «Ciclista lejano»: pocos puntos y lejos, arriba en la cola, y la página advierte que en ciclistas la regla es poco confiable.» | probabilidad estimada, posición en la cola, tipo de caso, gráfico con los puntos A y B; advertencia (0,443 contra 0,806 en peatones) | 29 |
| 6 | 1:25 a 1:35 (10 s) | **Validación** | Validación: recorrer las cinco pestañas | «Cierro en Validación: arriba el veredicto y cuatro cifras, y en cada pestaña la lectura, un gráfico y las tablas de apoyo cerradas.» | veredicto calculado, criterios O1 a O4 en tarjetas, AUC por candidato con el mínimo por partición, mejora de PR-AUC, diferencia de AUC, tipos de caso y el análisis en muestra | 23 |

## Recorrido extendido (respaldo; 8 secciones, cada paso con sus clics y qué decir)
Para una demo más larga o si preguntan por algo que el recorrido corto no toca.

| # | Qué hacer (clics) | Qué decir | Qué se ve |
|---|---|---|---|
| 1 | **Resumen.** Señalar los cuatro indicadores, el titular («Hay 2 posibles huecos de cámara…») y el anillo (la cámara con la X) | «Esto es en muestra: el detector se ajustó con los mismos datos y aún no hay prueba ciega.» | indicadores (41 segmentos, 2 cámaras con alerta, 21,2 % sin pareja), titular, filas de alerta con «Auditar» y anillo del segmento elegido |
| 2 | Pulsar «Auditar» en la primera alerta (abre la Auditoría con esa celda) y volver; en **Validación › En muestra**, señalar las tres filas de horas de «Impacto estimado» | «Ordenar la cola baja el tiempo para el 80 % de ≈ 358 h a ≈ 200 h; con auditoría previa, ≈ 132 h, en muestra.» | Auditoría con segmento y cámara ya elegidos y la celda resaltada; en Validación, tabla de horas con una barra fina por fila (20 s por caja: supuesto) |
| 3 | **Cola de revisión.** Segmento «Todos», flujo «Auditoría + cola (dos pasos, en muestra)», presupuesto 20 % (parte ahí) | «Con auditoría previa, unas 70 de cada 100 cajas sin pareja; solo con la cola, unas 62 de cada 100.» | frase con ambos flujos; 15.726 cajas, 87,4 h con 20 s por caja |
| 4 | Cambiar el flujo a «Solo cola (un paso)» y volver | «Con un paso se ordenan todas las cajas, sin auditoría previa.» | cajas a revisar y horas del flujo elegido |
| 5 | Modo «Meta» con 80 %; «Volver al 20 %» | «Si quiero encontrar el 80 %, la página dice cuánto revisar.» | porcentaje de la cola para la meta (curva guardada) |
| 6 | Abrir «Supuestos y confiabilidad» | «El intervalo es ancho (41 segmentos) y la ganancia de dos pasos sale de 2 celdas.» | segundos por caja editables, intervalos, texto de «en muestra» |
| 7 | Pestaña «Cola de cajas» (la primera), luego «Curva de priorización»; **seleccionar una fila** | «Cada fila llena el detalle de la derecha: probabilidad calibrada, posición y tipo de caso. Las primeras filas empatan: todas tienen 0 puntos del sensor superior y el orden entre ellas no informa.» | curva con intervalo sombreado; nota del empate sobre la tabla (calculada de la cola) y panel de detalle a la derecha, siempre visible |
| 8 | Activar «Agrupar por objeto» y filtrar la clase «Ciclista: poco confiable» | «Es solo una vista: el número de cajas a revisar no cambia. En ciclistas la regla es poco confiable.» | una fila por objeto con «Fotogramas en la cola»; «Filtrado: N cajas» |
| 9 | **Auditoría de cámaras.** Señalar el contorno rojo con X | «Dos celdas marcadas; no sabemos si es falta de etiquetas o de datos.» | mapa de calor (gris plano = sin datos suficientes, no es 0 %), Lista A con «Acción sugerida» y «Cajas afectadas» |
| 10 | **Explica una caja** (menú «Herramientas», o «Explicar esta caja →» desde la Cola). Ejemplo «Ciclista lejano» | «Pocos puntos y lejos: arriba en la cola. En ciclistas, advertencia: 0,443 contra 0,806 en peatones.» | probabilidad estimada, posición en la cola, tipo de caso, gráfico con los puntos A y B; solo el control del sensor superior mueve la probabilidad |
| 11 | **Validación.** Recorrer las cinco pestañas (Modelo elegido, Generalización, Alternativas, Tipos de caso, En muestra) | «Arriba el veredicto y cuatro cifras; en cada pestaña, la lectura, un gráfico y las tablas de apoyo, cerradas.» | mejora de PR-AUC, diferencia de AUC, AUC por candidato, criterios O1 a O4, grupos descriptivos, análisis en muestra |
| 12 | Volver al **Resumen** y señalar el titular, las dos alertas y la cola | «Una persona revisa y decide.» | titular, filas de alerta con «Auditar», cola de revisión con «Abrir» |
| 13 | **Puntuar datos nuevos** (solo mostrar) y «Usar un segmento de desarrollo de ejemplo» | «Todo en memoria; el ejemplo se reconstruye de los datos derivados, no son datos crudos de Waymo.» | formato de los archivos como tabla; listas A y B del ejemplo |

## Guion del video de 90 s (plan C)
- 0:00 a 0:10: Resumen, con el titular de las alertas de cámara.
- 0:10 a 0:40: Cola de revisión: 20 %, frase con ambos flujos, selección de una fila y su detalle.
- 0:40 a 1:00: Auditoría de cámaras: las dos celdas marcadas.
- 1:00 a 1:20: Explica una caja con el ejemplo «Ciclista lejano».
- 1:20 a 1:30: vuelta al Resumen y cierre: «Una persona revisa y decide».

## Si algo falla
- La página no abre: `scripts\ep3\arrancar_app.bat` otra vez; si no, el notebook 14 (ya ejecutado) y el video.
- Pregunta por un término: «Ayuda y glosario».
