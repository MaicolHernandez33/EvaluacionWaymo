# Guía de la demo de la página (recorrido exacto)

*Generada por `scripts/ep3/generar_docs_ep3.py`; coherente con `guion_presentacion.md` (bloque «Demo de la página», 1:50). Las cifras salen de `data/09_app_ep3` con la misma lógica que la página (`app_logica.py`) y de `data/08_reporting_ep3`. Todas son en muestra: en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos.*

## Antes de empezar
1. Abrir con `scripts\ep3rrancar_app.bat` (se abre en http://localhost:8501; solo accesible desde este equipo).
2. Perfil «Analista de revisión»; modo presentación **apagado** al principio.
3. Tener a mano la sección «Ayuda y glosario» por si preguntan un término.

## Recorrido (8 secciones; cada paso con sus clics y qué decir)
| # | Qué hacer (clics) | Qué decir | Qué se ve |
|---|---|---|---|
| 1 | **Inicio.** Señalar las 4 tarjetas y abrir «¿Qué significa?» | «Esto es en muestra: el detector se ajustó con los mismos datos y aún no hay prueba ciega.» | 80.571 cajas, 21,2 % sin pareja, 2 celdas con hueco, ≈ 226 h (estimación) |
| 2 | **Cola de revisión.** Segmento «Todos los segmentos»; presupuesto 20 % (parte ahí) | «Revisando el 20 % de la cola se encontrarían unas 70 de cada 100 cajas sin pareja.» | 15.726 cajas, 87,4 h con 20 s por caja; intervalo 62 % a 79 % |
| 3 | Abrir «¿Qué tan confiable es esto?» | «El intervalo es ancho (41 segmentos) y la ganancia de dos pasos sale de 2 celdas; con un paso serían unas 62 de cada 100.» | intervalo, aviso en muestra, un paso contra dos pasos |
| 4 | Cambiar a «Quiero encontrar X %» y dejar 80 % | «Si quiero encontrar el 80 %, la página dice cuánto revisar.» | porcentaje de la cola para el 80 % (interpolación de la curva guardada) |
| 5 | «Volver al 20 %» y mirar el gráfico | «El punto rojo es mi elección; la diagonal es revisar al azar.» | curva con intervalo sombreado |
| 6 | Bajar a la tabla; señalar la columna «Clase» | «Si hay un ciclista, la página lo avisa: la regla es poco confiable en ciclistas.» | columnas legibles, descarga CSV |
| 7 | **Auditoría de cámaras.** Señalar el contorno rojo con X | «Dos celdas marcadas; no sabemos si es falta de etiquetas o de datos.» | mapa de calor, Lista A con «Acción sugerida» |
| 8 | **Explica una caja.** Bajar los puntos del sensor; marcar «Ciclista» | «Pocos puntos y lejos: arriba en la cola. En ciclistas, advertencia: 0,443 contra 0,806 en peatones.» | probabilidad estimada, lugar en la cola, tipo de caso |
| 9 | Activar el **modo presentación** | «Se ocultan los identificadores y se agranda la letra.» | tarjetas y letra más grandes; tabla sin identificadores |
| 10 | **Puntuar datos nuevos** (solo mostrar) | «Todo en memoria: nada se guarda ni se envía.» | pasos de carga y formato esperado |

## Guion del video de 90 s (plan C)
- 0:00 a 0:10: Inicio con el aviso «en muestra».
- 0:10 a 0:40: Cola de revisión: 20 %, frase de resultado, «¿Qué tan confiable es esto?», modo «Quiero encontrar X %».
- 0:40 a 1:00: Auditoría de cámaras: las dos celdas marcadas.
- 1:00 a 1:20: Explica una caja con ciclista.
- 1:20 a 1:30: modo presentación y cierre: «Una persona revisa y decide».

## Si algo falla
- La página no abre: `scripts\ep3rrancar_app.bat` otra vez; si no, el notebook 14 (ya ejecutado) y el video.
- Pregunta por un término: «Ayuda y glosario».
