# Reporte de F25: la página como producto (sin avisos naranjas y un color por concepto)

*Generado por `scripts/ep3/generar_reporte_f25.py` desde sus archivos de origen. Decisiones: DEC-103 a DEC-105 en `ESTADO.md`; guía de estilo regenerada en `guia_estilo_pagina.md`. Sin commit: el usuario hace el commit.*

**En una línea.** El chip del encabezado es una pastilla neutra, las etiquetas «en muestra» con caja se quitaron (las oraciones conservan la divulgación), el ámbar quedó solo en la advertencia de los ciclistas, un concepto tiene un color en las tres vistas, el interruptor del modo presentación se ve a 1366 × 768 y la barra de herramientas ya no tapa la oración de referencia de la curva. No se cambió estructura, cálculos, cifras ni textos sellados.

## Qué se hizo

Pruebas: **249** aprobadas, 0 falladas, 0 omitidas (python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider, 48,0 s); antes de F25 había 240, y se agregaron 9 en `tests/ep3/test_pagina_f25.py`. Ningún límite de pruebas subió. Sello: **intacto** (`f25_sello_despues.json`: 121 archivos comparados; cambiados 0).

| N.º | Cambio | Estado | Qué quedó |
|---|---|---|---|
| 1 | Chip del encabezado | Hecho | Pastilla neutra: fondo `#18253D`, borde `#2A3A57`, texto `#A9B8CF`, un punto de 8 px en `#8696B0` y la etiqueta «Datos de desarrollo». El menú conserva la frase completa («Datos de desarrollo, sin validación externa») y lo que ya explicaba. Sin ámbar. |
| 2 | Etiquetas «en muestra» | Hecho | Quitadas del Resumen y de la Cola (las oraciones siguen diciendo «En la muestra de 41 segmentos» y «(en muestra)»). `aud-muestra` es texto simple en `#8696B0`, 12 px, sin caja ni borde; hoy ninguna vista lo necesita. `test_resumen_dice_en_muestra_a_lo_mas_dos_veces…` cuenta texto (límite de 2 sin cambios). |
| 3 | Ámbar de interfaz | Hecho | `#F5B73B` aparece en 1 elemento del DOM de las 8 vistas (Resumen (punto de ciclistas)); además, en el CSS, el punto del aviso del ciclista de la Cola y de Explica una caja (es la misma advertencia; solo aparece al elegir un ciclista). Se quitaron los tokens `aviso_fondo`, `aviso_borde` y `aviso_hover`; la nota de empate usa el filete `#3A4B6B` y «Validación externa pendiente» un punto en `#8696B0`. Búsqueda en el DOM real: `f25_ambar_en_el_dom.json` (antiguos fondo, borde y hover hallados: 0). |
| 4 | Un concepto, un color | Hecho | `E.FLUJOS_COLORES`: revisión sin orden `#8696B0`, solo cola `#C77B1E`, auditoría + cola `#4C82F2`, solo celdas sanas, sin auditoría `#B0508A`. Lo usan las barras de horas del Resumen, las barras de «En muestra» y las curvas de la Cola. El Resumen no tiene leyenda de colores (cada barra lleva su rótulo), así que no hubo leyenda que cambiar; la prueba del Resumen ahora comprueba el color de cada barra. |
| 5 | Barra lateral en modo presentación | Hecho | A 1366 × 768 el interruptor «Modo presentación» termina en **757 px** (antes 791 px, fuera de la ventana de 768 px) y la barra ya no se desplaza (desborde 0 px; antes 129 px). En modo normal el interruptor termina en 753 px (desborde 0 px; antes 47 px). No se quitó ningún elemento (8 enlaces del menú, rol e interruptor). |
| 6 | Barra de herramientas en la curva | Hecho | Oculta solo en los gráficos con `div:has(> [data-testid="stVegaLiteChart"]) > [data-testid="stElementToolbar"]` (por `data-testid`, no por clases generadas). Con el ratón real sobre el gráfico: `display: none`; sobre la tabla de la cola la barra sigue (111 × 47 px). Captura: `images/ep3/pagina/f25_curva_cursor_encima.png`. |

**Paleta (dataviz, modo oscuro, superficie `#121C30`, todos los pares).** Los tres colores cromáticos de los flujos pasan los cinco chequeos (peor par para daltonismo: #B0508A contra #4C82F2, ΔE 16,8; visión normal: #B0508A contra #C77B1E, ΔE 19,5). Las cinco curvas de la Cola, sin cambios, siguen pasando. El gris es la línea base neutra (contraste 5,7:1 con el panel; el piso de croma de una paleta categórica no aplica). Para el tercer color los verdes y los amarillos chocaban con el naranja para daltonismo y el cian con el azul; `#B0508A` fue el que pasó. Salida completa: `f25_paleta_validacion.json`.

**Medidas y capturas.** Contraste: 1.121 textos en 14 vistas, 0 por debajo de 4,5:1 (mínimo 5,42 en el DOM y 6,24 en los píxeles de las notas; `f25_contraste.json`). Panel del Resumen a 1366 × 768: 540 px en modo normal y 613 px en presentación (límite 640). 30 capturas completas (15 a 1366 px y 15 a 1920 px), 0 errores de consola, desplazamiento horizontal máximo 0 px. Revisadas una por una a 1366 px: Resumen, Cola (curva con XGBoost y cola de cajas), Validación (En muestra y Selección), la barra lateral a 1366 × 768 en los dos modos y el Resumen a 1366 × 768 en modo presentación (`09_resumen_modo_presentacion_1366x768.png`). Comparación con F24: `images/ep3/pagina/antes_f24/f24_final_01_resumen_1366.png` y `f24_final_05_validacion_en_muestra_1366.png`.

## Qué no se pudo y por qué

1. **El color de «solo celdas sanas» queda cerca del rosa de E2.** En la unión informativa de seis colores (flujos + curvas) falla el par `#D75893 contra #B0508A, ΔE 5,2` (daltonismo) y `#D75893 contra #B0508A, ΔE 7,8` (visión normal). Los dos colores nunca comparten gráfico (E2 solo se dibuja en la curva de la Cola; las barras de Validación llevan leyenda con rótulo), pero no hay un sexto color validado para todos los pares: los verdes y amarillos chocan con el naranja y el cian con el azul. Si se prefiere separarlos del todo, habría que cambiar el rosa de E2 (curva validada en F24).
2. **Ocultar la barra de herramientas quita también «pantalla completa» y «descargar» de los gráficos.** Streamlit no ofrece un ajuste para dejar solo algunas opciones. El selector va por `data-testid`, pero depende de que Streamlit siga poniendo la barra como hermana del gráfico; si una versión nueva cambia esa estructura, la barra volvería a verse (la prueba del CSS no lo detectaría; sí lo haría `f25_comprobar_herramientas.py`).
3. **El tono de «Validación externa pendiente» está en `app_logica.py`.** Para el punto gris hubo que cambiar el valor `tono` de `aviso` a `neutro` en `alertas_resumen` (solo presentación; ningún cálculo, cifra ni texto cambió). Se avisa porque el prompt de F24 dejaba `app_logica.py` intacto.
4. **El aviso del ciclista (Cola y Explica una caja) conserva el punto ámbar.** El criterio dice «solo en el punto de Ciclistas»; se interpretó que el aviso «Ciclista: la regla es poco confiable» es la misma advertencia. Solo aparece al elegir una caja de ciclista, por eso no sale en el DOM de las capturas por defecto; se vio con el aviso inyectado en la página. Si se prefiere sin ámbar ahí, basta quitar `.aud-aviso::before`.
5. **`st.dataframe` sigue dibujándose en un canvas.** El color de sus filas y su barra de herramientas no se pueden cambiar con CSS (no se tocó).

## Archivos modificados

Archivos con cambios en git y fecha de este trabajo (después del cierre de F24):

- `CLAUDE.md`: modificado
- `app/estilos.py`: modificado
- `app/secciones.py`: modificado
- `docs/ep3/ESTADO.md`: modificado
- `docs/ep3/MAPA_DE_ARCHIVOS.md`: modificado
- `docs/ep3/PENDIENTES_PAGINA.md`: modificado
- `docs/ep3/README_EP3.md`: modificado
- `docs/ep3/REPORTE_F25.md`: nuevo
- `docs/ep3/f24_fold_resumen.json`: nuevo
- `docs/ep3/f25_ambar_en_el_dom.json`: nuevo
- `docs/ep3/f25_barra_herramientas.json`: nuevo
- `docs/ep3/f25_barra_lateral.json`: nuevo
- `docs/ep3/f25_contraste.json`: nuevo
- `docs/ep3/f25_paleta_validacion.json`: nuevo
- `docs/ep3/f25_resultado_suite.json`: nuevo
- `docs/ep3/f25_sello_despues.json`: nuevo
- `docs/ep3/guia_estilo_pagina.md`: modificado
- `docs/ep3/guion_presentacion.md`: modificado
- `docs/ep3/informe_tecnico_EP3.md`: modificado
- `docs/ep3/pagina_guia_demo.md`: modificado
- `docs/ep3/plan_integracion_readme.md`: modificado
- `docs/ep3/preguntas_cruzadas.md`: modificado
- `scripts/ep3/f23_registrar_suite.py`: nuevo
- `scripts/ep3/f24_auditar_contraste.py`: nuevo
- `scripts/ep3/f25_buscar_ambar.py`: nuevo
- `scripts/ep3/f25_comprobar_herramientas.py`: nuevo
- `scripts/ep3/f25_medir_barra.py`: nuevo
- `scripts/ep3/f25_registrar_suite.py`: nuevo
- `scripts/ep3/f25_validar_paleta.py`: nuevo
- `scripts/ep3/generar_docs_ep3.py`: modificado
- `scripts/ep3/generar_guia_estilo.py`: modificado
- `scripts/ep3/generar_mapa.py`: modificado
- `scripts/ep3/generar_reporte_f25.py`: nuevo
- `src/waymo_evaluacion/ep3/app_logica.py`: modificado
- `tests/ep3/test_pagina_f20.py`: modificado
- `tests/ep3/test_pagina_f21.py`: modificado
- `tests/ep3/test_pagina_f23.py`: nuevo
- `tests/ep3/test_pagina_f24.py`: nuevo
- `tests/ep3/test_pagina_f25.py`: nuevo
- `tests/ep3/test_pagina_pulido.py`: modificado
- images/ep3/pagina/ (capturas finales, la de la barra lateral y la del cursor sobre el gráfico): 38 archivos (modificado, nuevo)
- images/ep3/pagina/antes_f24/ (dos capturas de la piel de F24 para comparar, con el prefijo `f24_final_`): 2 archivos (nuevo)
