# Reporte de F30: ajustes del Resumen y fin del Modo presentación

*Generado por `scripts/ep3/generar_reporte_f30.py` desde sus archivos de origen. Decisiones: DEC-118 a DEC-121 en `ESTADO.md`. Sin commit: el usuario hace el commit. La referencia visual fue `f30_resumen_propuesto.html` y el prompt F30 que la acompañaba.*

**En una línea.** El bloque «Alertas de cámara» ahora mide lo que mide su contenido (de 465 a **337 px**), sin el enlace «Abrir la auditoría de cámaras» y con el anillo arriba a la derecha; el pie del Resumen ya no lleva la línea de validación pendiente; el Modo presentación dejó de existir (interfaz, textos, código, pruebas, capturas y documentos vigentes); y «Impacto estimado» pasó a ser una sección fija de Validación › En muestra con las mismas cifras y los mismos textos. No cambió ningún modelo, cálculo ni cifra.

## 1. Pruebas, sello y verificaciones

- Pruebas de EP3 (`python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider`): **antes 277 aprobadas; después 284 aprobadas**, 0 falladas, 0 omitidas, 52,8 s. Se agregaron 12 pruebas en `tests/ep3/test_pagina_f30.py`; las pruebas de cifras (`test_las_cifras_no_cambian_salvo_el_redondeo_unificado`, `test_las_horas_de_inicio_son_132_y_358…`, la regresión contra `pagina_numeros_antes.json`) siguen y pasan.
- Sello de la validación externa: **intacto** (`f30_sello_despues.json`: 121 archivos comparados; cambiados 0). Congelados de EP2 (14 de 14) y de v3 (5 de 5): ver el cierre de `ESTADO.md`.
- Contraste real: 1.236 textos en 14 vistas, **0 por debajo de 4,5:1** (mínimo 5,42 en el DOM y 5,67 en los píxeles; `f30_contraste.json`).
- Ámbar `#F5B73B` en el DOM de las 8 vistas: 0 elemento(s) (solo el punto de advertencia de ciclistas, que aparece cuando una fila de la cola es de ciclista).
- Navegación real: «Auditar» abrió la Auditoría con «Celda elegida: segmento …998801, cámara 3 (frontal der.): hueco (celda marcada).»; «Abrir» abrió «Explica una caja» con «Caja elegida desde el Resumen (segmento …196576, caja j8GQ-0…». Resultado: los botones navegan con el contexto elegido.
- Capturas: 28 de 28 completas (a 1366 y a 1920 px), 0 errores de consola, desplazamiento horizontal máximo 0 px. Barra lateral a 1366 × 768: desborde 0 px y el selector «Rol» a 753 px de 768 (visible: sí).

## 2. Altura del bloque «Alertas de cámara» (1366 × 768, medida con Chrome sin interfaz)

| Medida | Antes (F29) | Después (F30) | Diferencia |
|---|---|---|---|
| Alto del bloque | 465 px | 337 px | -128 px |
| Título «Cola de revisión» termina en | 728 px | 600 px | -128 px |
| Filtros de la cola terminan en | 803 px | 675 px | -128 px |
| Título y filtros visibles en una ventana de 768 px | no | **sí** | |
| Título y filtros visibles en 650 px (alto útil típico de un navegador real) | no | no | |

**Meta cumplida a 1366 × 768:** el título «Cola de revisión» y sus filtros se ven sin hacer scroll (los filtros terminan en 675 px de 768). **Si el navegador solo ofrece unos 650 px útiles (barras y pestañas incluidas), faltan 25 px**: los filtros quedarían justo bajo el borde. No lo cerré porque habría que tocar los indicadores (que el prompt dijo que no se tocaran) o apretar el espacio entre secciones hasta que se vea amontonado.

Cómo se logró: se quitó la cabecera aparte del bloque (que tenía el enlace y empujaba todo hacia abajo), se pasó a dos columnas independientes (izquierda: rótulo, titular, subtítulo y filas; derecha: rótulo del anillo, anillo de 240 px y leyenda, alineados arriba: el rótulo del anillo empieza a 16 px del borde superior del bloque) y se redujo el relleno del recuadro de `1.3rem 1.5rem 24px` a `1rem 1.4rem 1rem`. El recuadro ya no tiene el hueco bajo las filas: mide lo que mide su columna más alta (hoy la del anillo). Con 5 alertas crece la columna izquierda y el anillo sigue arriba.

## 3. Qué se hizo, punto por punto

**A) Bloque «Alertas de cámara».** (1) Se quitó el enlace «Abrir la auditoría de cámaras» y su constante `ENLACE_AUDITORIA`; cada fila conserva «Auditar» y la Auditoría sigue en el menú. (2) Recuadro ajustado y anillo arriba, como arriba. (3) Los cuatro indicadores no se tocaron. (4) Medición antes/después en la sección 2 (`scripts/ep3/f30_medir_bloque.py`, `f30_altura_bloque.json`; el «antes» se guardó con el código de F29 y antes de cambiar nada).

**B) Pie del Resumen.** (5) Se quitó solo la línea «Validación externa pendiente · las cifras salen de segmentos de desarrollo» con su enlace «Ver en Validación» (la función `_pie_resumen`, `E.estado_validacion`, el CSS `.aud-estado`/`.aud-punto.neutro` y las constantes `ESTADO_VALIDACION`/`ENLACE_VALIDACION`). Quedan la atribución de Waymo y «Solución v3 congelada el 2026-11-14. Datos de desarrollo, 41 segmentos.». Decisión registrada como DEC-119 en `ESTADO.md`: la divulgación de rigor sigue en Ética y límites, Validación, Ayuda y el pie global.

**C) Modo presentación fuera.** (6) Se quitó el interruptor y su ayuda de `app/app.py`; la barra lateral solo tiene «Rol». (7) Se eliminó todo lo que dependía del modo: la letra agrandada (`PRESENTACION` y el parámetro de `E.css`, el token `1.18`), la numeración de identificadores («Segmento 25», `#001`), el ocultamiento de identificadores (`ocultar_identificadores` e `IDENTIFICADORES`; los parámetros `presentacion` de `tabla_cola`, `tabla_por_objeto` y `E.metricas`), el `ocultar` de las descargas de «Puntuar datos nuevos», el texto «(oculto)» del segmento de ejemplo, la clave `presentacion` de `ctx` y de `session_state`, y las variantes de pantallas anchas del CSS (`.aud-metricas.pres`). Se buscaron «modo presentación», «modo_presentacion» y «presentacion» en `app/`, `src/`, `tests/`, `scripts/` y `docs/`; lo que queda está en la sección 5. (8) «Impacto estimado» (horas con y sin cola, su nota y el menú «Fuente») pasó, con las mismas cifras y los mismos textos, a una sección fija de **Validación › En muestra, debajo del gráfico** (`_impacto_estimado` en `app/secciones.py`). (9) Textos corregidos: Ética y límites («Las tablas locales tienen identificadores de objeto y marcas de tiempo. Nada se guarda ni se envía.», en las dos variantes de `EP3_ENTORNO`); Ayuda y glosario (se quitó la viñeta del modo y la del rol dice «cambia la página que se abre»); y los documentos vigentes que lo mencionaban (README_EP3, informe, guion, preguntas cruzadas, guía de demo, guía de estilo, mapa de archivos, pendientes y `despliegue.md`, a mano). (10) Pruebas adaptadas o quitadas sin tocar las de cifras (sección 4).

**D) Capturas y reporte.** (11) Se regeneraron todas las capturas (a 1366 y a 1920 px; la barra lateral cambió en todas), se quitó de `capturar_pagina.py` el paso del modo presentación y se borraron las capturas de ese modo. (12) La carpeta `images/ep3/pagina/para_revision/` se armó con `scripts/ep3/armar_para_revision.py` (la vacía antes de copiar): 16 capturas a 1366 px, una por página, más este reporte, 17 archivos en total. (13) Este reporte.

## 4. Pruebas: qué se quitó, qué se adaptó y qué se agregó

- **Quitadas** (verificaban el modo): `test_modo_presentacion_oculta_identificadores` (test_app) y `test_modo_presentacion_oculta_identificadores_en_la_cola` (rediseño; la parte que sigue valiendo, que la tabla de la página no lleva identificadores y el CSV sí, quedó como `test_la_tabla_de_la_cola_de_la_pagina_no_lleva_identificadores_pero_el_csv_si`), y `test_el_impacto_estimado_solo_se_muestra_con_el_modo_presentacion_y_trae_su_fuente` (F29, reemplazada por pruebas de F30).
- **Adaptadas:** la prueba de humo de 8 páginas × 3 roles ya no parametriza el modo (ni en test_app ni en rediseño); `test_el_css_cumple_el_sistema_visual…` (sin `.pres` ni `1.18`); la tira de cifras sin variante de presentación; el detalle de la cola siempre con segmento; `tabla_cola` y `tabla_por_objeto` sin el parámetro; el padding del panel (`1rem 1.4rem 1rem 1.4rem`); la barra lateral (selector de rol visible en lugar del interruptor); el cabe-en-640 px (solo modo normal); y las pruebas de capturas (14 por ancho en lugar de 15, sin capturas del modo). Las pruebas que buscaban las horas (358, 200 y 132 h) o las barras de colores de los flujos ahora las buscan en Validación.
- **Agregadas** (`test_pagina_f30.py`, 12): el modo no deja rastro en `app/`, `src/` ni en las capturas y scripts; la barra lateral solo tiene «Rol» y `session_state` no guarda estado del modo en ninguna de las 8 páginas; los identificadores siempre están en los datos descargables; Ética y Ayuda corregidas (incluidas las dos variantes de `EP3_ENTORNO`); Impacto estimado una sola vez, en Validación › En muestra, con su «Fuente» y debajo del gráfico; el Resumen sin el enlace de la Auditoría ni la línea de validación; anillo en la columna derecha con su rótulo encima; tamaño del anillo entre 240 y 260 px; medidas antes/después con la meta; y la carpeta `para_revision` con exactamente los 17 archivos.

## 5. Decisiones distintas del prompt (y por qué)

1. **Se mantuvieron el enlace «Abrir la cola completa» y los tres filtros de la cola.** El HTML de referencia no los dibuja, pero el prompt pedía que el título de la cola «y sus filtros» se vieran en la primera pantalla, y el enlace no estaba en la lista de lo que se quita.
2. **La opción `--ocultar-ids` de `scripts/ep3/puntuar_segmento.py` se conserva** (es una opción de línea de comandos del script, no del modo de la página); solo se corrigió su ayuda, que decía «modo presentacion».
3. **Los documentos y scripts históricos siguen diciendo «modo presentación»** porque cuentan lo que era cierto en su fase y el prompt pedía tocar solo lo vigente. Quedan (16 documentos): `docs/ep3/auditoria_diseno_pagina.md` (7), `docs/ep3/ESTADO.md` (13), `docs/ep3/guia_estilo_pagina.md` (1), `docs/ep3/MAPA_DE_ARCHIVOS.md` (2), `docs/ep3/PENDIENTES_PAGINA.md` (2), `docs/ep3/plan_diseno_f23.md` (1), `docs/ep3/REPORTE_F18.md` (4), `docs/ep3/REPORTE_F19B.md` (1), `docs/ep3/REPORTE_F20.md` (6), `docs/ep3/REPORTE_F21.md` (3), `docs/ep3/REPORTE_F23.md` (5), `docs/ep3/REPORTE_F24.md` (2), `docs/ep3/REPORTE_F25.md` (5), `docs/ep3/REPORTE_F26.md` (1), `docs/ep3/REPORTE_F29.md` (3), `docs/ep3/verificacion_copia_limpia.md` (1). Y en scripts (15): `scripts/ep3/f18_pagina_numeros_antes.py` (1), `scripts/ep3/generar_auditoria_diseno.py` (7), `scripts/ep3/generar_guia_estilo.py` (1), `scripts/ep3/generar_mapa.py` (2), `scripts/ep3/generar_pendientes_pagina.py` (2), `scripts/ep3/generar_plan_diseno_f23.py` (1), `scripts/ep3/generar_reporte_f18.py` (3), `scripts/ep3/generar_reporte_f19b.py` (1), `scripts/ep3/generar_reporte_f20.py` (6), `scripts/ep3/generar_reporte_f21.py` (3), `scripts/ep3/generar_reporte_f23.py` (5), `scripts/ep3/generar_reporte_f24.py` (2), `scripts/ep3/generar_reporte_f25.py` (5), `scripts/ep3/generar_reporte_f26.py` (1), `scripts/ep3/generar_reporte_f29.py` (3). En los generadores de reportes de F18 a F29 es texto de esos reportes; `ESTADO.md` conserva las decisiones antiguas (DEC-xx) tal como se escribieron.
4. **No se regeneró el cuaderno 14** (su prueba de humo todavía recorre el modo). Se corrigió su generador, `scripts/ep3/crear_notebooks_ep3.py`, para cuando se vuelva a generar; ejecutar notebooks está fuera de lo permitido en esta tarea.
5. **No se reempaquetó `entrega_EP3.zip` ni `artefactos_ep3/`.** Se corrigió el texto del paso a paso que `scripts/ep3/empaquetar_entrega_ep3.py` escribe en el zip (decía «active “Modo presentación”»), pero el zip ya generado conserva el texto anterior hasta que se vuelva a empaquetar.
6. **El tamaño del anillo es 240 px** (el HTML usa 236 y el prompt pedía de 240 a 260): el valor más bajo del rango, para que el bloque sea lo más bajo posible sin perder legibilidad.
7. **La meta de «sin scroll» se cumple a 768 px, no a 650 px** (sección 2).
8. **`verificacion_copia_limpia.md` no se tocó:** es el registro de una verificación hecha en una copia limpia en su momento (48 combinaciones con el modo) y no se vuelve a ejecutar aquí.

## 6. Lo que no se pudo hacer o queda pendiente

- Los 25 px que faltan para ver los filtros en un navegador de 650 px útiles (sección 2).
- Probar el Resumen con cientos o miles de segmentos: el diseño limita la lista de alertas a 5 filas (avisa cuántas más hay), pero solo se vio con 2 alertas.
- Regenerar el cuaderno 14 y reempaquetar la entrega (puntos 4 y 5 de la sección anterior).
- Los generadores `generar_reporte_f26.py`, `generar_reporte_f27.py` y `generar_reporte_f29.py` citan constantes y estructuras que cambiaron: no se pueden volver a ejecutar sin adaptarlos (sus reportes quedan como están).
- Las capturas de 1920 px se regeneraron pero no se enviaron a revisión (la carpeta pedida es solo de 1366).

## 7. Archivos modificados

Archivos con cambios en git y modificados después de cerrar F29 (los documentos generados salen de sus generadores):

- `CLAUDE.md`: modificado
- `app/app.py`: modificado
- `app/contexto.py`: modificado
- `app/estilos.py`: modificado
- `app/secciones.py`: modificado
- `docs/ep3/ESTADO.md`: modificado
- `docs/ep3/MAPA_DE_ARCHIVOS.md`: modificado
- `docs/ep3/PENDIENTES_PAGINA.md`: modificado
- `docs/ep3/README_EP3.md`: modificado
- `docs/ep3/REPORTE_F30.md`: nuevo
- `docs/ep3/despliegue.md`: modificado
- `docs/ep3/f24_fold_resumen.json`: nuevo
- `docs/ep3/f25_ambar_en_el_dom.json`: nuevo
- `docs/ep3/f25_barra_lateral.json`: nuevo
- `docs/ep3/f26_marca.json`: nuevo
- `docs/ep3/f29_navegacion.json`: nuevo
- `docs/ep3/f29_sello_despues.json`: nuevo
- `docs/ep3/f30_altura_bloque.json`: nuevo
- `docs/ep3/f30_contraste.json`: nuevo
- `docs/ep3/f30_resultado_suite.json`: nuevo
- `docs/ep3/f30_sello_despues.json`: nuevo
- `docs/ep3/guia_estilo_pagina.md`: modificado
- `docs/ep3/guion_presentacion.md`: modificado
- `docs/ep3/informe_tecnico_EP3.md`: modificado
- `docs/ep3/pagina_guia_demo.md`: modificado
- `docs/ep3/plan_integracion_readme.md`: modificado
- `docs/ep3/preguntas_cruzadas.md`: modificado
- `scripts/ep3/armar_para_revision.py`: nuevo
- `scripts/ep3/capturar_pagina.py`: modificado
- `scripts/ep3/crear_notebooks_ep3.py`: modificado
- `scripts/ep3/empaquetar_entrega_ep3.py`: modificado
- `scripts/ep3/f24_medir_resumen.py`: nuevo
- `scripts/ep3/f25_medir_barra.py`: nuevo
- `scripts/ep3/f26_capturas_extra.py`: nuevo
- `scripts/ep3/f30_medir_bloque.py`: nuevo
- `scripts/ep3/f30_registrar_suite.py`: nuevo
- `scripts/ep3/generar_docs_ep3.py`: modificado
- `scripts/ep3/generar_guia_estilo.py`: modificado
- `scripts/ep3/generar_mapa.py`: modificado
- `scripts/ep3/generar_pendientes_pagina.py`: modificado
- `scripts/ep3/generar_reporte_f30.py`: nuevo
- `scripts/ep3/puntuar_segmento.py`: modificado
- `src/waymo_evaluacion/ep3/app_logica.py`: modificado
- `tests/ep3/test_app.py`: modificado
- `tests/ep3/test_pagina_f20.py`: modificado
- `tests/ep3/test_pagina_f21.py`: modificado
- `tests/ep3/test_pagina_f24.py`: nuevo
- `tests/ep3/test_pagina_f25.py`: nuevo
- `tests/ep3/test_pagina_f26.py`: nuevo
- `tests/ep3/test_pagina_f29.py`: nuevo
- `tests/ep3/test_pagina_f30.py`: nuevo
- `tests/ep3/test_pagina_pulido.py`: modificado
- `tests/ep3/test_pagina_rediseno.py`: modificado
- images/ep3/pagina/ (capturas regeneradas con la barra lateral nueva y el bloque de alertas ajustado): 46 archivos (borrado, modificado, nuevo)
- images/ep3/pagina/para_revision/ (los 17 archivos que se envían a revisión): 17 archivos (nuevo)
- Capturas del modo presentación borradas: `09_inicio_modo_presentacion.png`, `09_resumen_modo_presentacion_1366.png`, `09_resumen_modo_presentacion_1920.png`, `09_inicio_modo_presentacion_1366.png`, `09_inicio_modo_presentacion_1920.png`, `09_resumen_modo_presentacion_1366.png`, `09_resumen_modo_presentacion_1920.png`
