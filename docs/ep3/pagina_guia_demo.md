# Guía de la demo de la página (recorrido exacto)

*Generada por `scripts/ep3/generar_docs_ep3.py`; coherente con `guion_presentacion.md` (bloque «Demo de la página», 1:35). Las cifras salen de `data/09_app_ep3` con la misma lógica que la página (`app_logica.py`) y de `data/08_reporting_ep3`. Todas son en muestra: en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos.*

## Antes de empezar
1. Abrir con `scripts\ep3\arrancar_app.bat` (usa `app\lanzar.py`, que carga la solución congelada y los datos antes de aceptar visitas: espere unos 3 s; se abre en http://localhost:8501 y solo es accesible desde este equipo).
2. Rol «Analista de revisión» (al pie de la barra lateral); modo presentación **apagado** al principio.
3. Tener a mano «Ayuda y glosario» por si preguntan un término.

## Recorrido (8 secciones; cada paso con sus clics y qué decir)
| # | Qué hacer (clics) | Qué decir | Qué se ve |
|---|---|---|---|
| 1 | **Resumen.** Señalar las 4 métricas y abrir el chip «Datos de desarrollo · sin validación externa» | «Esto es en muestra: el detector se ajustó con los mismos datos y aún no hay prueba ciega.» | 80.571 cajas, 21,2 % sin pareja, 2 celdas marcadas, 41 segmentos |
| 2 | Señalar las tres barras de «Impacto estimado» y las «Alertas» | «Ordenar la cola baja el tiempo para el 80 % de ≈ 358 h a ≈ 200 h; con auditoría previa, ≈ 132 h, en muestra.» | barras de horas (20 s por caja: supuesto), tres alertas con enlace a su sección |
| 3 | **Cola de revisión.** Segmento «Todos», flujo «Auditoría + cola (dos pasos, en muestra)», presupuesto 20 % (parte ahí) | «Con auditoría previa, unas 70 de cada 100 cajas sin pareja; solo con la cola, unas 62 de cada 100.» | frase con ambos flujos; 15.726 cajas, 87,4 h con 20 s por caja |
| 4 | Cambiar el flujo a «Solo cola (un paso)» y volver | «Con un paso se ordenan todas las cajas, sin auditoría previa.» | cajas a revisar y horas del flujo elegido |
| 5 | Modo «Meta» con 80 %; «Volver al 20 %» | «Si quiero encontrar el 80 %, la página dice cuánto revisar.» | porcentaje de la cola para la meta (curva guardada) |
| 6 | Abrir «Supuestos y confiabilidad» | «El intervalo es ancho (41 segmentos) y la ganancia de dos pasos sale de 2 celdas.» | segundos por caja editables, intervalos, texto de «en muestra» |
| 7 | Pestaña «Curva de cobertura», luego «Cola de cajas»; **seleccionar una fila** | «Cada fila abre su detalle: probabilidad calibrada, posición y tipo de caso.» | curva con intervalo sombreado; tabla con panel de detalle a la derecha |
| 8 | Activar «Agrupar por objeto» y filtrar la clase «Ciclista: poco confiable» | «Es solo una vista: el número de cajas a revisar no cambia. En ciclistas la regla es poco confiable.» | una fila por objeto con «Fotogramas en la cola»; «Filtrado: N cajas» |
| 9 | **Auditoría de cámaras.** Señalar el contorno rojo con X | «Dos celdas marcadas; no sabemos si es falta de etiquetas o de datos.» | mapa de calor (gris rayado = sin datos suficientes, no es 0 %), Lista A con «Acción sugerida» y «Cajas afectadas» |
| 10 | **Explica una caja.** Botón «Ciclista lejano» | «Pocos puntos y lejos: arriba en la cola. En ciclistas, advertencia: 0,443 contra 0,806 en peatones.» | probabilidad estimada, posición en la cola, tipo de caso, gráfico |
| 11 | **Validación.** Recorrer las pestañas | «Un gráfico por tema, leído de los CSV del informe; la tabla completa está en cada pestaña.» | mejora de PR-AUC, diferencia de AUC, AUC por candidato, criterios O1 a O4 |
| 12 | Activar el **modo presentación** | «Se ocultan los identificadores y se agranda la letra.» | métricas 2 x 2, tabla sin identificadores |
| 13 | **Puntuar datos nuevos** (solo mostrar) y «Usar un segmento de desarrollo de ejemplo» | «Todo en memoria; el ejemplo se reconstruye de los datos derivados, no son datos crudos de Waymo.» | formato de los archivos como tabla; listas A y B del ejemplo |

## Guion del video de 90 s (plan C)
- 0:00 a 0:10: Resumen con el chip «en muestra».
- 0:10 a 0:40: Cola de revisión: 20 %, frase con ambos flujos, selección de una fila y su detalle.
- 0:40 a 1:00: Auditoría de cámaras: las dos celdas marcadas.
- 1:00 a 1:20: Explica una caja con el ejemplo «Ciclista lejano».
- 1:20 a 1:30: modo presentación y cierre: «Una persona revisa y decide».

## Si algo falla
- La página no abre: `scripts\ep3\arrancar_app.bat` otra vez; si no, el notebook 14 (ya ejecutado) y el video.
- Pregunta por un término: «Ayuda y glosario».
