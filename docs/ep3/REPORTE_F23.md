# Reporte de F23: rediseño estructural de la página

*Generado por `scripts/ep3/generar_reporte_f23.py` desde sus archivos de origen. Plan de diseño: `plan_diseno_f23.md`. Decisiones: DEC-87 a DEC-96 en `ESTADO.md`. Sin commit: el usuario hace los commits.*

**En una línea.** La página dejó de ser una plantilla de tarjetas: el Resumen abre con una afirmación y el anillo de cámaras, la Cola tiene seis columnas y un detalle siempre visible, la Auditoría pinta «sin datos» en gris plano, la barra lateral es clara y solo hay una superficie elevada. Las cifras y los textos sellados no cambiaron; no se tocó el sello.

## Los seis cambios

| # | Cambio | Estado | Qué se vio (capturas de `images/ep3/pagina/`) | Lo que no coincide con lo pedido |
|---|---|---|---|---|
| 1 | Resumen: el anillo manda | **Hecho** | Sin fichas de indicadores; afirmación en serif de 29,25 px con las cifras de `inicio_resumen` y la etiqueta «en muestra»; anillo de 300 px con el estado de las cinco cámaras del segmento elegido (sana, hueco, sin datos) y su lista en texto; cifras de apoyo (AUC, horas, casos encontrados por clase) en una tabla pequeña. A 1366 x 768 el anillo, su leyenda y la afirmación se ven completos sin desplazarse (`f23_fold_resumen.json`, `01_resumen_1366x768.png`). Modo presentación revisado en `09_resumen_modo_presentacion_*`. | La frase dice «el detector marca N celdas… como posibles huecos de cámara» y no «tienen un hueco»: un hueco es una hipótesis (glosario y Ética). El gráfico de barras de horas pasó a una tabla con una barra fina por fila. |
| 2 | Cola de revisión | **Hecho** | Tabla de seis columnas (Prioridad, Prob. sin pareja, Puntos sensor sup., Cámara, Tipo de caso, Clase) sin recortes ni desplazamiento horizontal a 1366 y 1920 px; detalle siempre a la derecha, con estado vacío; «Curva de priorización» es la primera pestaña; ningún puntaje con valores como «-50,000» (prueba `test_ningun_puntaje_sin_sentido_en_la_cola_ni_en_explica`). | El segmento, la distancia y los fotogramas pasaron al panel de detalle y los identificadores al CSV (el ejemplo traía segmento en la tabla). El estado vacío dice «Seleccione una fila para ver su detalle» (registro de usted de toda la página) y no «Elige…». |
| 3 | Auditoría de cámaras | **Hecho** | «Sin datos» en gris plano `#E3E6EB`, sin rayado, distinto del teal y del rojo; leyenda con las mismas tres muestras y palabras del anillo; las celdas con hueco llevan el relleno rojo suave del anillo. | — |
| 4 | Menos tarjetas, jerarquía real | **Hecho** | Una sola superficie elevada (panel del Resumen y detalle de la cola); radios de 0 (tablas), 6 (controles) y 14 px (panel); una sola sombra en la hoja (prueba `test_radios_segun_el_papel_y_una_sola_sombra`); barra lateral clara del mismo tono que el lienzo, con línea fina, en `[theme.sidebar]` de los dos `config.toml` y en `css()`; fichas de Ética, alertas, filtros y «Cómo se calcula» sin caja. | El mapa de calor sigue en un contenedor con borde fino (es un área de desplazamiento). El contraste se calcula sobre los tokens (todos los pares sobre 4,5:1); no se midió sobre las imágenes. |
| 5 | Validación > Selección | **Hecho** | Criterios O1 a O4 con nombre (Discrimina, Vale la pena, Recall en el punto A, Estable y calibrada) y umbrales leídos del plan v3; «Cumple» o «No cumple» en texto; fila de la solución elegida destacada y marcada «Elegida»; «Regla top» se muestra como «regla de puntos del sensor superior» en toda la página (prueba que recorre las ocho secciones). Documentos regenerados: informe técnico, preguntas cruzadas, guion, README de EP3 y pendientes de la página. | «Regla top» sigue como clave de los datos y en documentos históricos o de solo lectura (ver «Lo que no quedó bien»). |
| 6 | Puntuar datos nuevos | **Parcial** | Primero las acciones (elegir archivo, ejemplo, resultado); el formato de entrada está en un expander cerrado debajo; encabezados de la Lista B en español. Nada de Waymo se publica. | No hay un botón «Puntuar» separado: la puntuación ocurre al elegir el archivo o el ejemplo, como antes (agregar el botón cambiaría el comportamiento). |

## Paleta de curvas (dataviz)
Validada con `validate_palette.js` en modo claro (superficie = papel). Metas: separación para daltonismo (ΔE de CVD) de 8 o más y piso de visión normal de 15 o más entre curvas adyacentes.

| | Curvas (en orden) | CVD, peor par adyacente | Visión normal, peor par adyacente | Resultado |
|---|---|---|---|---|
| Antes | `#2457D6`, `#B45309`, `#6B7280`, `#0B6E69`, `#7C3AED` | ΔE 4,4 | ΔE 10,2 | no pasa |
| Después | `#2457D6`, `#B45309`, `#1C9B84`, `#8F81E8`, `#844A83` | ΔE 12,8 | ΔE 18,8 | pasa |

Antes (adyacentes):

| Chequeo | Resultado | Detalle |
|---|---|---|
| Lightness band | PASS | all 5 inside L 0.43–0.77 |
| Chroma floor | FAIL | below floor (reads gray): [["#6B7280",0.023],["#0B6E69",0.082]] |
| CVD separation | FAIL | worst adjacent #0B6E69↔#6B7280 ΔE 4.4 (protan) · tritan 8.8 |
| Normal-vision floor | FAIL | worst adjacent #0B6E69↔#6B7280 ΔE 10.2 (normal) — below 15, hard to tell apart even with full color vision |
| Contrast vs surface | PASS | all 5 >= 3:1 |

Después (adyacentes):

| Chequeo | Resultado | Detalle |
|---|---|---|
| Lightness band | PASS | all 5 inside L 0.43–0.77 |
| Chroma floor | PASS | all 5 >= 0.1 |
| CVD separation | PASS | worst adjacent #1C9B84↔#B45309 ΔE 12.8 (deutan) · tritan 9.1 |
| Normal-vision floor | PASS | worst adjacent #844A83↔#8F81E8 ΔE 18.8 (normal) |
| Contrast vs surface | PASS | all 5 >= 3:1 |

Después (todos los pares, la comprobación más exigente):

| Chequeo | Resultado | Detalle |
|---|---|---|
| Lightness band | PASS | all 5 inside L 0.43–0.77 |
| Chroma floor | PASS | all 5 >= 0.1 |
| CVD separation | PASS | worst all-pairs #1C9B84↔#B45309 ΔE 12.8 (deutan) · tritan 9.1 |
| Normal-vision floor | PASS | worst all-pairs #844A83↔#B45309 ΔE 17.8 (normal) |
| Contrast vs surface | PASS | all 5 >= 3:1 |

Con la paleta nueva no hizo falta la codificación secundaria que pedía el plan para un par que no llegara; el trazo discontinuo se mantiene de todos modos. Ninguna curva pinta texto con su color. La curva con XGBoost de referencia se revisó en el navegador; la de E2 no se fotografió.

## Medición del Resumen a 1366 x 768
Ventana de exactamente 1366 x 768 px (Chrome sin interfaz, `scripts/ep3/f23_medir_resumen.py`): el anillo ocupa de 188 a 476 px, su leyenda llega a 506, la afirmación termina en 272 y el panel principal en 583; desplazamiento horizontal: 0 px. Un navegador real gasta unos 120 px en barras: aun así el panel (hasta 583 px) cabe en unos 650 px de alto útil. Fuente medida de la afirmación: Cambria, "Palatino Linotype", "Book Antiqua", Georgia, serif / 29,25px.

## Capturas
30 capturas (15 por ancho, 1366 y 1920 px, con las seis pestañas de Validación, la cola con y sin fila y el modo presentación), 30 de 30 completas según la espera robusta de `capturar_pagina.py`; desplazamiento horizontal máximo: 0 px; diferencia máxima entre el enlace y su alerta: 3,3 px (límite 5); errores de consola: 0. Antes de F23: `images/ep3/pagina/antes_f23/`. Las 30 imágenes y la de 1366 x 768 se abrieron y se revisaron una por una (cuatro de ellas, en la corrida inmediatamente anterior con el mismo código: Generalización a 1366, Selección a 1920, Puntuar a 1920 y el modo presentación a 1920). Las correcciones de las pasadas están en `auditoria_diseno_pagina.md` (sección F23). En `05_validacion_en_muestra_1920.png` el interruptor «Modo presentación» de la barra lateral sale cortado abajo: es un efecto de la captura (la ventana se ajusta al alto de esa página, 717 px) y no de la página.

## Pruebas
- Antes de F23: **200** aprobadas (`python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider`).
- Después: **219** aprobadas, 0 fallidas, 0 omitidas, en 69,4 s.
- Nuevas: `tests/ep3/test_pagina_f23.py` (23 pruebas: anillo en el Resumen, seis columnas en la Cola, gris de «sin datos», expander cerrado, barra lateral clara, paleta validada, nombre visible de la regla, criterios de selección, plan y sello). Adaptadas, por comparar etiquetas o estructura anteriores: `test_pagina_f20.py`, `test_pagina_f21.py`, `test_pagina_f22.py`, `test_pagina_pulido.py` y `test_pagina_rediseno.py`.
- El número de pruebas de los documentos sale de `scripts/ep3/contar_pruebas.py` y `generar_docs_ep3.py` (ejecutados al final).

## Integridad del sello
Comprobada con `scripts/ep3/f23_integridad_sello.py` (solo lectura: sha256 y `git status`): 121 archivos sellados comparados (`artefactos_ep3/`, plan de selección y su hash, notebook 00b, scripts y módulos de la validación externa, manifests y modelos congelados de EP2 y EP3). Resultado: **intacto** (cambiados: 0, faltan: 0, nuevos: 0; `git status` sobre lo sellado: 0 líneas).

| Archivo | sha256 (registrado antes de F23) | Después |
|---|---|---|
| `docs/ep3/plan_seleccion_ep3.sha256` | `3fa5121725da8681898103f6c86badd4c3ce903af5da414f7914b0039d9b2039` | igual |
| `docs/ep3/plan_seleccion_ep3.json` | `862346e1317b8be3d03fbd6d7f9f17e7afe7e3e9fd02962f99775b4d966c5a10` | igual |
| `data/06_models_ep3/manifest_v3.json` | `06807ad082a3c87f26bbb4691a04bfca09344b80235fa61bb29c5a74acf0b972` | igual |
| `data/06_models_ep3/manifest_alternativas.json` | `d8a9dd319cd134ddc5b643401f8298e700b15beba8cf66c460eaa4345b7b3532` | igual |
| `data/06_models_ep3/alternativas_v3.joblib` | `60c9834f03cfbfffffc49910e32281ca3e194c9afefe96179d0b9c0ca10a48c5` | igual |

No se ejecutó `ingesta_nuevos.py` ni `evaluar_sellado.py` y no se abrieron datos nuevos. `verificar_congelados.py` y `verificar_congelados_v3.py` se corrieron al final (14 de 14 y 5 de 5).

## Archivos modificados y creados
- `.streamlit/config.toml`: modificado
- `app/.streamlit/config.toml`: modificado
- `app/app.py`: modificado
- `app/estilos.py`: modificado
- `app/secciones.py`: modificado
- `docs/ep3/ESTADO.md`: modificado
- `docs/ep3/MAPA_DE_ARCHIVOS.md`: modificado
- `docs/ep3/PENDIENTES_PAGINA.md`: modificado
- `docs/ep3/README_EP3.md`: modificado
- `docs/ep3/REPORTE_F23.md`: nuevo
- `docs/ep3/auditoria_diseno_pagina.md`: modificado
- `docs/ep3/f23_fold_resumen.json`: nuevo
- `docs/ep3/f23_paleta_validacion.json`: nuevo
- `docs/ep3/f23_resultado_suite.json`: nuevo
- `docs/ep3/f23_sello_antes.json`: nuevo
- `docs/ep3/f23_sello_despues.json`: nuevo
- `docs/ep3/guia_estilo_pagina.md`: modificado
- `docs/ep3/guion_presentacion.md`: modificado
- `docs/ep3/informe_tecnico_EP3.md`: modificado
- `docs/ep3/pagina_guia_demo.md`: modificado
- `docs/ep3/plan_diseno_f23.md`: nuevo
- `docs/ep3/plan_integracion_readme.md`: modificado
- `docs/ep3/preguntas_cruzadas.md`: modificado
- `scripts/ep3/capturar_pagina.py`: modificado
- `scripts/ep3/f23_integridad_sello.py`: nuevo
- `scripts/ep3/f23_medir_resumen.py`: nuevo
- `scripts/ep3/f23_registrar_suite.py`: nuevo
- `scripts/ep3/generar_auditoria_diseno.py`: modificado
- `scripts/ep3/generar_docs_ep3.py`: modificado
- `scripts/ep3/generar_guia_estilo.py`: modificado
- `scripts/ep3/generar_mapa.py`: modificado
- `scripts/ep3/generar_pendientes_pagina.py`: modificado
- `scripts/ep3/generar_plan_diseno_f23.py`: nuevo
- `scripts/ep3/generar_reporte_f23.py`: nuevo
- `src/waymo_evaluacion/ep3/app_logica.py`: modificado
- `src/waymo_evaluacion/ep3/formato.py`: modificado
- `tests/ep3/test_pagina_f20.py`: modificado
- `tests/ep3/test_pagina_f21.py`: modificado
- `tests/ep3/test_pagina_f22.py`: modificado
- `tests/ep3/test_pagina_f23.py`: nuevo
- `tests/ep3/test_pagina_pulido.py`: modificado
- `tests/ep3/test_pagina_rediseno.py`: modificado
- images/ep3/pagina/ (capturas finales): 31 archivos (modificado, nuevo)
- images/ep3/pagina/antes_f23/ (copia de las capturas de F22): 30 archivos (nuevo)

## Lo que no quedó bien o no pude verificar
1. **No hay botón «Puntuar» separado** en «Puntuar datos nuevos» (cambio 6 parcial): se mantuvo la puntuación automática.
2. **«en muestra» y las cifras de apoyo.** El Resumen lleva la etiqueta junto a la afirmación y en la nota de las horas, que es el máximo de dos por pantalla que fija `test_resumen_dice_en_muestra_a_lo_mas_dos_veces…`. El AUC y los casos encontrados por clase no llevan etiqueta propia; los cubre el chip de estado del encabezado. Si se prefiere una etiqueta en cada cifra, hay que subir ese límite.
3. **«Regla top» sigue en:** docs/ep3/auditoria_diseno_pagina.md (1), docs/ep3/ESTADO.md (2), docs/ep3/guia_estilo_pagina.md (1), docs/ep3/REPORTE_F20.md (2), docs/ep3/REPORTE_F21.md (2), docs/ep3/REPORTE_F23.md (3), docs/ep3/verificacion_copia_limpia.md (1), notebooks/12_ep3_tuning_y_ensambles.ipynb (2), notebooks/13_ep3_generalizacion_y_seleccion.ipynb (18). La guía de estilo y la auditoría la citan a propósito para explicar el renombre; el resto son registros históricos de fases anteriores o notebooks ejecutados (regenerarlos exige ejecutarlos). La clave interna de los datos y del código (`candidatos.py`, CSV de evidencia, `artefactos_ep3/`) no se cambia por regla. Los documentos de EP2 (README, informe) son de solo lectura.
4. **Curva con E2 de referencia:** no la fotografié. Con XGBoost y sin referencia sí. La pestaña de la curva no forma parte del script de capturas oficial.
5. **Fuentes.** Cambria viene con Windows y se vio en las capturas (29,25 px); si falta en otro equipo caen Palatino y Georgia, y eso no lo probé.
6. **Solo Chrome sin interfaz** a 1366 y 1920 px. No probé otros navegadores, ni zoom, ni lector de pantalla.
7. **«Puntuar» con resultados** no está en el juego oficial de capturas (solo el estado vacío); lo vi aparte, con el segmento de ejemplo. Los valores de «Tipo de objeto» siguen en inglés («PEDESTRIAN»), como vienen de los datos.
8. **404 internos de Streamlit:** 26 de 30 capturas los registran; no los comparé con F22.
9. **Docker y AWS:** fuera de alcance, no se tocaron ni se probaron.
10. **Textos de redacción que cambié** para quitar cadenas con puntos medios (chip, pie, versión, resultado de la cola, texto del cargador): son frases de presentación; las cifras no cambian.
