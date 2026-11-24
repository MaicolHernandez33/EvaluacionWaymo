# Reporte de F27: el Resumen en dos pasos y el menú en el orden del proceso

*Generado por `scripts/ep3/generar_reporte_f27.py` desde sus archivos de origen. Decisiones: DEC-110 a DEC-112 en `ESTADO.md`; guía de estilo regenerada en `guia_estilo_pagina.md`. Sin commit: el usuario hace el commit.*

**En una línea.** El proyecto tiene dos partes (filtrar las cámaras con posibles huecos y priorizar las cajas del resto) y la página solo contaba la primera en el Resumen. Ahora el Resumen se lee en dos pasos, el menú sigue ese orden y cada paso lleva a su página. No se creó una página nueva (la Cola de revisión ya es la página de la priorización) y no cambiaron cálculos, cifras ni textos sellados.

## Qué se hizo

Pruebas: **271** aprobadas, 0 falladas, 0 omitidas (python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider, 52,8 s); antes de F27 había 264 y se agregaron 7 en `tests/ep3/test_pagina_f27.py`. Sello: **intacto** (`f27_sello_despues.json`: 121 archivos comparados; cambiados 0).

| Código | Cambio | Qué quedó |
|---|---|---|
| E1 | Menú en el orden del proceso | Grupos «Visión general», «1 · Filtro», «2 · Priorización», «Análisis», «Herramientas», «Ayuda». Auditoría de cámaras (paso 1) va antes que Cola de revisión y Explica una caja (paso 2). Los nombres de las 8 secciones, sus direcciones y el rol no cambiaron; Resumen sigue siendo la página por defecto. |
| E2 | Resumen en dos pasos | Encabezado «1 · Filtro de cámaras» (solo número y título; enlace «Abrir la auditoría de cámaras») con el panel del anillo; y «2 · Priorización de cajas» (frase: «Del resto, ¿qué caja se revisa primero? La cola ordena las cajas por la probabilidad de no tener par 2D en ninguna cámara.», enlace «Abrir la cola de revisión») con «Impacto estimado» y la vista de la cola. Debajo, «Cifras de apoyo» y las «Alertas» (una bajo otra, cada una con su enlace). Todos los textos son constantes de `app_logica.py`. |
| E3 | Vista de las primeras cajas de la cola | 5 cajas con prioridad, probabilidad, cámara y clase, calculadas con la misma cola, el mismo flujo (dos pasos) y el mismo presupuesto (20 %) con que abre «Cola de revisión»; una prueba compara ambas tablas. Dice el empate de las primeras cajas (el orden entre cajas empatadas no informa) y que es «en muestra». |
| E4 | Del paso 1 al paso 2 | Al final de la Auditoría, el enlace «Siguiente paso: ordenar el resto en la cola de revisión» (sin flecha, como pide la regla de F23). |
| E5 | Barra lateral | Con seis grupos el menú desbordaba la barra (8 px en modo normal, 14 px en presentación, con el interruptor fuera de la vista). Se redujo la separación entre grupos (.7 rem) y, en presentación, el relleno de los enlaces; no se quitó ningún elemento. A 1366 × 768: desborde 0 px y 0 px; interruptor a 753 px y 757 px (límite 760). |

**Medidas y capturas.** Panel principal del Resumen a 1366 × 768: termina en **538 px** en modo normal y **595 px** en presentación (límite 640). Contraste: 1.126 textos en 14 vistas, 0 por debajo de 4,5:1 (mínimo 5,42 en el DOM y 6,24 en los píxeles). Ámbar `#F5B73B` en el DOM de las 8 vistas: 1 elemento (el punto de «Ciclistas»). 30 capturas completas (15 a 1366 px y 15 a 1920 px), 0 errores de consola, desplazamiento horizontal máximo 0 px.

## Qué no se hizo y por qué

1. **No se creó una página «Priorización» aparte.** La Cola de revisión ya es esa página; duplicarla habría repetido filtros y curva. Renombrarla habría tocado pruebas, documentos generados y capturas sin aportar más que el título.
2. **La vista de cajas del Resumen muestra empates, no un orden informativo.** Las primeras cajas de la cola comparten el mismo puntaje del sensor superior; por eso la vista lo dice debajo en vez de presentarlas como un orden fino.
3. **La Cola no tiene un enlace de «paso anterior» hacia la Auditoría.** Se dejó fuera para no recargar sus filtros; el menú numerado y el selector «Flujo» ya cuentan el orden.
4. **Las capturas de la numeración anterior se borraron** (`02_cola…`, `03_explica…`, `04_auditoria…`): el número de cada captura sigue el orden del menú, que cambió. Ningún documento las citaba.
5. **Los textos «Revisión» y «Calidad de datos» siguen en `auditoria_diseno_pagina.md` y en los reportes de F20 a F26**, que cuentan cómo era el menú entonces.

## Ajuste posterior a pedido del usuario (DEC-113): el Resumen sin el aviso «en muestra»

Se quitó del Resumen (y solo del Resumen): la frase del paso 1 («¿Qué cámaras tienen posibles huecos?…»), «en la muestra de» de la afirmación (ahora «Se marcaron k posibles huecos de cámara en n segmentos.»), «de desarrollo» del subtítulo, el «en muestra» de la nota bajo las primeras cajas, «Estimación en muestra» (ahora «Estimación: … (supuesto, no medido)»), el menú «Fuente» y la alerta «Validación externa pendiente». Las alertas quedan en dos (celdas marcadas y ciclistas) y el rol «Ingeniero consumidor de datos» abre con «Celdas marcadas». Una prueba vigila que el Resumen no vuelva a decirlo.

**Lo que se conservó y por qué.** Ninguna cifra cambió: siguen siendo de los 41 segmentos, con el detector ajustado con los mismos datos y sin validación con segmentos nuevos. Ese hecho sigue dicho en el pie, en la Cola, en Validación, en Ética y límites, en Ayuda y en Puntuar (el usuario pidió el Resumen, así que el resto no se tocó), y la regla de `CLAUDE.md` de rotular las cifras fuera de la página (informe, README, guion) sigue vigente. Si se quiere extender el cambio a otras vistas, es una decisión aparte.

## Archivos modificados

Archivos con cambios en git y modificados después de cerrar F26:

- `CLAUDE.md`: modificado
- `app/estilos.py`: modificado
- `app/secciones.py`: modificado
- `docs/ep3/ESTADO.md`: modificado
- `docs/ep3/MAPA_DE_ARCHIVOS.md`: modificado
- `docs/ep3/PENDIENTES_PAGINA.md`: modificado
- `docs/ep3/README_EP3.md`: modificado
- `docs/ep3/REPORTE_F27.md`: nuevo
- `docs/ep3/f24_fold_resumen.json`: nuevo
- `docs/ep3/f25_ambar_en_el_dom.json`: nuevo
- `docs/ep3/f25_barra_lateral.json`: nuevo
- `docs/ep3/f26_marca.json`: nuevo
- `docs/ep3/f26_sello_despues.json`: nuevo
- `docs/ep3/f27_contraste.json`: nuevo
- `docs/ep3/f27_resultado_suite.json`: nuevo
- `docs/ep3/f27_sello_despues.json`: nuevo
- `docs/ep3/guia_estilo_pagina.md`: modificado
- `docs/ep3/guion_presentacion.md`: modificado
- `docs/ep3/informe_tecnico_EP3.md`: modificado
- `docs/ep3/pagina_guia_demo.md`: modificado
- `docs/ep3/plan_integracion_readme.md`: modificado
- `docs/ep3/preguntas_cruzadas.md`: modificado
- `scripts/ep3/capturar_pagina.py`: modificado
- `scripts/ep3/f27_registrar_suite.py`: nuevo
- `scripts/ep3/generar_docs_ep3.py`: modificado
- `scripts/ep3/generar_guia_estilo.py`: modificado
- `scripts/ep3/generar_mapa.py`: modificado
- `scripts/ep3/generar_reporte_f27.py`: nuevo
- `src/waymo_evaluacion/ep3/app_logica.py`: modificado
- `tests/ep3/test_pagina_f20.py`: modificado
- `tests/ep3/test_pagina_f21.py`: modificado
- `tests/ep3/test_pagina_f23.py`: nuevo
- `tests/ep3/test_pagina_f24.py`: nuevo
- `tests/ep3/test_pagina_f25.py`: nuevo
- `tests/ep3/test_pagina_f26.py`: nuevo
- `tests/ep3/test_pagina_f27.py`: nuevo
- `tests/ep3/test_pagina_pulido.py`: modificado
- images/ep3/pagina/ (capturas con el menú nuevo; las de la numeración anterior se borraron): 49 archivos (borrado, modificado, nuevo)
