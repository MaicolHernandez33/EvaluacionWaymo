# Reporte de F29: Resumen rediseñado para uso diario

*Generado por `scripts/ep3/generar_reporte_f29.py` desde sus archivos de origen. Decisiones: DEC-114 a DEC-117 en `ESTADO.md`. «F29» es el nombre en este repositorio del prompt «F27 — Rediseño del Resumen» del usuario (F27 ya era el Resumen en dos pasos y el menú). Sin commit: el usuario hace el commit.*

**En una línea.** El Resumen se lee ahora como una consola de inicio de turno, siguiendo la referencia visual del usuario: cuatro indicadores, el bloque «Alertas de cámara» con una fila por celda marcada (botón «Auditar») y el anillo del segmento elegido, la «Cola de revisión» con filtros, tabla y segmentos prioritarios (botón «Abrir»), y un pie con la divulgación de rigor. No cambió ningún modelo, cálculo ni cifra: las cifras que ya estaban solo cambiaron de lugar.

## Qué se hizo

Pruebas: **277** aprobadas, 0 falladas, 0 omitidas (python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider, 55,4 s); antes de F29 había 271 y se agregaron 18 en `tests/ep3/test_pagina_f29.py`. Sello: **intacto** (`f29_sello_despues.json`: 121 archivos comparados; cambiados 0).

| Punto del prompt | Qué quedó |
|---|---|
| 1. Franja de 4 indicadores | Segmentos nuevos («cargados, sin revisar»; una sola función decide qué es «sin revisar»: `segmentos_sin_revisar`), Cámaras con alerta (en rojo si es mayor que 0), Cajas en la cola (78.626 en los datos actuales: el total de la cola de dos pasos) y % de cajas sin pareja. El cambio respecto de ayer solo se muestra si `cambio_respecto_de_ayer` devuelve un valor; hoy no hay corte anterior y se omite (una prueba comprueba las dos ramas). |
| 2. «Alertas de cámara» | Rótulo, titular dinámico «Hay N posibles huecos de cámara en los últimos datos sin revisar.» (o «Todas las cámaras sanas.» con la hora de la última actualización de los datos), subtítulo, enlace «Abrir la auditoría de cámaras», una fila por celda marcada (hasta 5, las de más cajas afectadas primero) con segmento (6 últimos dígitos), cámara (número y nombre), estado «Hueco» en palabras e ícono, y «Auditar». La primera fila viene elegida; elegir otra cambia el anillo. «Auditar» abre la Auditoría con ese segmento y esa cámara ya elegidos (`session_state`) y su celda resaltada en el mapa. |
| 3. «Cola de revisión» | Filtros por clase, cámara y segmento; columnas Prioridad, Segmento, Caja, Cámara, Clase, Prob. sin pareja y Acción («Abrir» lleva a «Explica una caja» con los controles puestos con los valores de esa caja). Orden determinista: probabilidad descendente, segmento, identificador de objeto y fotograma; la columna Caja es única (identificador del objeto y número de fotograma), así que no hay filas idénticas. Etiqueta «Regla poco confiable» con punto ámbar en las filas de ciclista. Panel «Segmentos con más cajas prioritarias» con barras (los 5 segmentos con más cajas en la cola del 20 %). |
| 4. Lo que sale del Resumen | «Cifras de apoyo» pasó a Validación (mismas cifras). «Impacto estimado» con su menú «Fuente» solo se ve con el modo presentación. La alerta duplicada «Celdas marcadas» y la de ciclistas salieron (el rol ya no reordena alertas). |
| 5. Pie | «Validación externa pendiente · las cifras salen de segmentos de desarrollo» con el enlace «Ver en Validación»; la atribución de Waymo, con el texto exacto actual, sigue en el pie de toda la página. «Datos de ejemplo» no está. |

**Criterios de aceptación.**
- Con los datos actuales hay **2 alertas** y el titular dice 2.
- Primera pantalla a 1366 × 768, sin desplazarse: indicadores visibles **sí**, titular visible **sí** y lista de alertas visible **sí**; la última fila de alerta termina en **509 px** (modo normal) y **622 px** (presentación), con límite de 640 px.
- Ninguna cifra cambió de valor: cada cifra del Resumen se calcula con las funciones que ya existían y las pruebas de regresión de cifras están entre las 277 aprobadas (0 falladas).
- Navegación en el navegador real (`f29_navegacion.json`): «Auditar» abrió la Auditoría con «Celda elegida: segmento …998801, cámara 3 (frontal der.): hueco (celda marcada).»; elegir la segunda fila cambió el anillo a «…534050» y su «Auditar» abrió la otra celda; «Abrir» abrió «Explica una caja» con «Caja elegida desde el Resumen (segmento …196576, caja j8GQ-01). Valore…». Conclusión de la prueba: los botones navegan con el contexto elegido.

**Medidas y capturas.** Barra lateral a 1366 × 768: desborde 0 px y 0 px. Contraste: 1.240 textos en 14 vistas, 0 por debajo de 4,5:1 (mínimo 5,42 en el DOM y 5,67 en los píxeles). Ámbar `#F5B73B` en el DOM de las 8 vistas: 0 elemento. 30 capturas completas (15 a 1366 px y 15 a 1920 px), 0 errores de consola, desplazamiento horizontal máximo 0 px. Imágenes de los destinos: `f29_destino_auditar.png` y `f29_destino_abrir.png`.

## Diferencias con la referencia y por qué

1. **No se copiaron las cifras ni los textos inventados del mockup.** Faltan «Actualizado hoy 08:30», «desde ayer 18:00», «+1,4 puntos respecto de ayer», «Hueco detectado hoy 06:12» y «Datos de ejemplo del mockup»: los datos no traen horas ni un corte anterior. La fila de alerta dice «Hueco · N cajas afectadas» (dato real de la Lista A) en vez de la hora.
2. **Tipografía.** La referencia usa Inter desde Google Fonts; la página sigue con su única familia sans del sistema (sin CDN). El peso de las cifras grandes es 600 (la regla del proyecto admite 400, 500 y 600; el mockup usa 700).
3. **Mayúsculas pequeñas** en el rótulo «Alertas de cámara» y en el encabezado de la tabla de la cola, como en la referencia. Antes una prueba de F23 las prohibía; se cambió para permitir exactamente esos dos usos.
4. **La etiqueta «Regla poco confiable» no lleva caja con borde**, solo el punto ámbar y el texto (regla de F25: el ámbar solo marca advertencias reales y no se usa en cajas).
5. **«Prioridad» del Resumen no es la posición de «Cola de revisión».** El Resumen ordena con desempate determinista (probabilidad, segmento, caja); la página de la Cola conserva el orden de siempre, que entre cajas con el mismo puntaje no informa. Por eso la primera caja del Resumen tiene 90,4 % y la primera fila de la Cola 87,8 %: son cajas del mismo grupo empatado. No se cambió el orden de la Cola porque podría mover cuáles cajas entran en el corte del 20 % y alterar cifras.
6. **El menú «Fuente» solo existe junto al impacto estimado** (modo presentación), porque ya no hay otra cifra del Resumen que lo necesite.
7. **El nombre de cada caja** es el final del identificador del objeto y su fotograma (por ejemplo `j8GQ-01`), no un número secuencial como `#0412`; en modo presentación va numerada (`#001`) para no mostrar identificadores.

## Qué no se hizo y por qué

1. **No se probó con cientos o miles de segmentos.** El diseño limita la lista de alertas a 5 filas (avisa cuántas más hay), la cola a 5 y los segmentos prioritarios a 5; con 41 segmentos solo se vio con 2 alertas. La velocidad con muchos más datos no se midió.
2. **«Sin revisar» es el total cargado** (41), como pidió el prompt. No existe estado de revisión ni flujo en vivo; cuando exista, se cambia `segmentos_sin_revisar` en `app_logica.py`.
3. **Los generadores de los reportes de F26 y F27** (`generar_reporte_f26.py`, `generar_reporte_f27.py`) citan constantes que F29 quitó (la afirmación, los encabezados de paso): ya no se pueden volver a ejecutar. Sus reportes quedan como están; no se tocaron.
4. **Los documentos históricos** (reportes de F20 a F27 y `ESTADO.md`) siguen describiendo cómo era el Resumen en su momento.

## Archivos modificados

Archivos con cambios en git y modificados después de cerrar F27/F28:

- `CLAUDE.md`: modificado
- `app/app.py`: modificado
- `app/contexto.py`: modificado
- `app/estilos.py`: modificado
- `app/secciones.py`: modificado
- `docs/ep3/ESTADO.md`: modificado
- `docs/ep3/MAPA_DE_ARCHIVOS.md`: modificado
- `docs/ep3/PENDIENTES_PAGINA.md`: modificado
- `docs/ep3/README_EP3.md`: modificado
- `docs/ep3/REPORTE_F29.md`: nuevo
- `docs/ep3/f24_fold_resumen.json`: nuevo
- `docs/ep3/f25_ambar_en_el_dom.json`: nuevo
- `docs/ep3/f25_barra_lateral.json`: nuevo
- `docs/ep3/f26_marca.json`: nuevo
- `docs/ep3/f27_sello_despues.json`: nuevo
- `docs/ep3/f29_contraste.json`: nuevo
- `docs/ep3/f29_navegacion.json`: nuevo
- `docs/ep3/f29_resultado_suite.json`: nuevo
- `docs/ep3/f29_sello_despues.json`: nuevo
- `docs/ep3/guia_estilo_pagina.md`: modificado
- `docs/ep3/guion_presentacion.md`: modificado
- `docs/ep3/informe_tecnico_EP3.md`: modificado
- `docs/ep3/pagina_guia_demo.md`: modificado
- `docs/ep3/plan_integracion_readme.md`: modificado
- `docs/ep3/preguntas_cruzadas.md`: modificado
- `scripts/ep3/capturar_pagina.py`: modificado
- `scripts/ep3/f24_medir_resumen.py`: nuevo
- `scripts/ep3/f29_navegacion.py`: nuevo
- `scripts/ep3/f29_registrar_suite.py`: nuevo
- `scripts/ep3/generar_docs_ep3.py`: modificado
- `scripts/ep3/generar_guia_estilo.py`: modificado
- `scripts/ep3/generar_mapa.py`: modificado
- `scripts/ep3/generar_pendientes_pagina.py`: modificado
- `scripts/ep3/generar_reporte_f29.py`: nuevo
- `src/waymo_evaluacion/ep3/app_logica.py`: modificado
- `tests/ep3/test_pagina_f20.py`: modificado
- `tests/ep3/test_pagina_f21.py`: modificado
- `tests/ep3/test_pagina_f23.py`: nuevo
- `tests/ep3/test_pagina_f24.py`: nuevo
- `tests/ep3/test_pagina_f25.py`: nuevo
- `tests/ep3/test_pagina_f26.py`: nuevo
- `tests/ep3/test_pagina_f27.py`: nuevo
- `tests/ep3/test_pagina_f29.py`: nuevo
- `tests/ep3/test_pagina_pulido.py`: modificado
- `tests/ep3/test_pagina_rediseno.py`: modificado
- images/ep3/pagina/ (capturas del Resumen rediseñado y de los destinos de «Auditar» y «Abrir»): 51 archivos (borrado, modificado, nuevo)
