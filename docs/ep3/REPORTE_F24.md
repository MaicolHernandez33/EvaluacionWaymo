# Reporte de F24: cambio de piel (tema oscuro) y defectos concretos

*Generado por `scripts/ep3/generar_reporte_f24.py` desde sus archivos de origen. Decisiones: DEC-97 a DEC-102 en `ESTADO.md`; guía de estilo regenerada en `guia_estilo_pagina.md`. Sin commit: el usuario hace los commits.*

**En una línea.** F24 cambió la piel (tema oscuro nativo de Streamlit, una sola familia sans, anillo como protagonista) y corrigió 18 defectos de maquetación **sin tocar la estructura, el contenido, las cifras ni los textos sellados**. Los tokens viven solo en `app/estilos.py` (de ahí salen el CSS y los dos `config.toml`).

## Qué se hizo

Mediciones de cierre (Chrome sin interfaz, solo localhost): panel del Resumen a 1366 x 768 termina en **540 px** en modo normal y en **613 px** en presentación (límite 640 px); contraste real de **1.124** textos en 14 vistas, **0** por debajo de 4,5:1 (mínimo 5,42:1 en el DOM; las notas pequeñas medidas en píxeles, mínimo 6,24:1); 30 capturas (15 a 1366 px y 15 a 1920 px), 30 completas; desplazamiento horizontal máximo 0 px; errores de consola 0.

| # | Defecto | Estado | Qué se hizo y cómo se comprobó |
|---|---|---|---|
| 1 | Blanco sobre blanco | Hecho | Tokens de la tabla del prompt: lienzo `#0B1220`, barra `#0E1729` (línea derecha `#1E2B45`), panel `#121C30` (borde `#22314D`, radio 14px), panel alto `#18253D` (borde `#2A3A57`, radio 8px). Una sola fuente (`TOKENS`); `generar_config_tema.py --comprobar` falla si un `config.toml` se desfasa y una prueba falla si aparece un hex fuera de `estilos.py`. |
| 2 | Pestañas | Hecho | Pestaña activa con subrayado de 2 px en el acento y peso 600 (Cola, Validación). |
| 3 | Notas más tenues que Texto 3 | Hecho | Se quitaron las opacidades de las notas: el texto más tenue es `texto_3` `#8696B0`. Medido en los tokens (pares de `PARES_CONTRASTE`) y en el DOM y los píxeles de las capturas (`f24_contraste.json`). |
| 4 | Afirmación del Resumen | Hecho | 3 líneas a 1366 px y 3 en presentación; tamaño 24px, peso 600; la columna de texto ocupa el 53 % del panel. «41 segmentos» va en el acento y «2 celdas» en el color del hueco; el color no reemplaza el texto ni la «X». |
| 5 | Lista de cámaras | Hecho | Ocupa todo el ancho de la columna, con líneas continuas y 25 px de aire bajo la última fila (medido). |
| 6 | Alertas del Resumen | Hecho | Una columna por alerta: título, texto y debajo un enlace visible, subrayado y en el acento («Ver en Auditoría de cámaras»). Geometría medida en las capturas: 12 de 12 alertas con el enlace bajo el texto, dentro de la alerta, subrayado y sin solape. |
| 7 | Barras de horas | Hecho | Barras de 10 px con extremos redondeados y el número alineado a la derecha. |
| 8 | Modo presentación a 1366 x 768 | Hecho | Panel (afirmación, anillo y lista) termina en 613 px (límite 640): afirmación de 1,38 rem en tres líneas, lista compacta y anillo de 250 px (300 px en modo normal). Medido también en modo normal (540 px). `f24_fold_resumen.json`. |
| 9 | Filtros Clase y Cámara | Hecho | Selectores en panel alto con texto principal: se ven activos. |
| 10 | Panel de detalle de la Cola | Hecho | Tabla y detalle en 64 % y 36 %; anillo de unos 120 px **encima** de la cifra grande; 20 px de relleno; la última fila no toca el borde. |
| 11 | Nota del empate | Hecho | Texto secundario con una regla ámbar suave a la izquierda. |
| 12 | Botones de ejemplo y deslizadores de Explica | Hecho | Botones con borde `#2A3A57`; pista del deslizador `#22314D` con relleno en el acento. |
| 13 | Etiquetas del gráfico de Explica | Hecho | Ejes y etiquetas en `texto_2`, 12 px o más; títulos en `texto`. |
| 14 | Mapa de calor de la Auditoría | Hecho | 41 filas de 16 px, sin desplazamiento interno. Rampa teal de un solo tono, más claro = más proporción con pareja. |
| 15 | Leyenda del mapa | Hecho | Una línea corta por estado (ver «Qué no se pudo» sobre el texto acortado). |
| 16 | «En muestra» de Validación | Hecho | Tres series con la paleta oscura (gris, azul medio y acento), valores en el color del texto y leyenda en una fila. |
| 17 | Selección | Hecho | «✓ Cumple» en el verde de lo sano y «✕ No cumple» en el color del texto, con íconos SVG propios (sin rojo ni ámbar); fila elegida en panel alto con la etiqueta «Elegida»; los textos no cambiaron. |
| 18 | Puntuar datos nuevos | Hecho | Botón de ejemplo primario (relleno del acento, texto `#0B1220`) y zonas de arrastre con borde punteado `#3A4B6B`. |

**Paleta de curvas (dataviz, modo oscuro, superficie `#121C30`).** El punto de partida del prompt (`#4C82F2`, `#C77B1E`, `#18A38A`, `#8478E8`, `#C2418B`) pasaba los pares adyacentes pero no todos los pares: el peor era #8478E8 contra #4C82F2, ΔE 1,7 para daltonismo y #8478E8 contra #4C82F2, ΔE 6,9 en visión normal. Se conservaron «Dos pasos» y «Un paso» y se ajustaron las otras tres hasta que **todos los pares** pasaron: `#4C82F2`, `#C77B1E`, `#0F7C55`, `#8F4AB4`, `#D75893`; peor par para daltonismo #0F7C55 contra #C77B1E, ΔE 9,4, en visión normal #D75893 contra #8F4AB4, ΔE 15,7. XGBoost sigue discontinuo y las curvas de referencia llevan etiqueta directa. Rampa del mapa (`#15655C`, `#187F74`, `#289A8C`, `#32B1A2`, `#3CC9B8`): pasa la validación ordinal (un solo tono, luminosidad monótona, escalones visibles). Todo en `f24_paleta_validacion.json`.

**Correcciones que salieron de revisar las capturas** (antes de la pasada final): las líneas de la lista de cámaras tenían cortes entre columnas (ahora son continuas); la leyenda del mapa decía «(más claro, más)» y quedó «Sana: más claro, más cajas con pareja»; dos notas decían «Línea negra» para un intervalo que ahora es claro; la «×» de «segmento × cámara» quedaba sola al inicio de una línea a 1920 px (ahora va unida a las dos palabras con espacios de no separación); los rombos y los intervalos del gráfico de Generalización se veían apagados sobre el fondo oscuro (más grandes y más opacos); la «X» de la muestra «Hueco» usaba peso 700 y la regla es 400 y 600.

**Capturas revisadas una por una (pasada final, con el código definitivo):** las 30 finales (15 a 1366 px y 15 a 1920 px: Resumen, Cola con y sin fila, Explica, Auditoría, las seis pestañas de Validación —incluidas «En muestra» y «Selección»—, Puntuar, Ética, Ayuda y Resumen en modo presentación), las dos del Resumen a 1366 x 768 y tres de la pestaña «Curva de priorización» (sin referencia, con XGBoost y con E2).

## Qué no se pudo y por qué

1. **Inter no está en el repositorio.** El prompt la deja opcional: si alguien pone `app/static/fonts/Inter-Variable.woff2` (licencia OFL, con su archivo de licencia), el tema la carga solo (`[[theme.fontFaces]]` y `server.enableStaticServing`; una prueba lo comprueba en una carpeta temporal). Hoy la página usa Segoe UI o la fuente del sistema, y no se descargó nada.
2. **`st.dataframe` no se puede estilizar con CSS** (se dibuja en un canvas). Solo se le aplicó el tema (`dataframeHeaderBackgroundColor` y compañía); la altura de fila, la barra de desplazamiento y la casilla de selección son las nativas, y su texto no entra en la auditoría de contraste del DOM (se revisó en las capturas).
3. **404 internos de Streamlit** (no se corrigen; vienen de que Streamlit pide `_stcore/health` y `_stcore/host-config` relativos a la ruta de cada página): 52 registros en 30 capturas, 14 URL distintas:
  - `localhost:8531/auditoria/_stcore/health` (2 veces)
  - `localhost:8531/auditoria/_stcore/host-config` (2 veces)
  - `localhost:8531/ayuda/_stcore/health` (2 veces)
  - `localhost:8531/ayuda/_stcore/host-config` (2 veces)
  - `localhost:8531/cola/_stcore/health` (4 veces)
  - `localhost:8531/cola/_stcore/host-config` (4 veces)
  - `localhost:8531/etica/_stcore/health` (2 veces)
  - `localhost:8531/etica/_stcore/host-config` (2 veces)
  - `localhost:8531/explica/_stcore/health` (2 veces)
  - `localhost:8531/explica/_stcore/host-config` (2 veces)
  - `localhost:8531/puntuar/_stcore/health` (2 veces)
  - `localhost:8531/puntuar/_stcore/host-config` (2 veces)
  - `localhost:8531/validacion/_stcore/health` (12 veces)
  - `localhost:8531/validacion/_stcore/host-config` (12 veces)
4. **Barra lateral a 1366 x 768.** Su contenido desborda la ventana en 47 px en modo normal y 129 px en presentación (la barra se desplaza sola). No se corrigió: el límite del prompt es el del panel del Resumen, y quitar elementos de la barra cambiaría el contenido.
5. **Textos que cambiaron por necesidad de la piel o de la maquetación** (ninguno es un texto sellado ni una cifra): la leyenda del mapa pasó a una línea corta por estado y las explicaciones largas al atributo `title` (defecto 15; `Sana: más claro, más cajas con pareja`); y las dos notas de Hiperparámetros y Ensambles que decían «Línea negra» dicen ahora «Línea clara», porque el intervalo se dibuja claro sobre fondo oscuro.
6. **Inconsistencia del prompt.** La tabla de tokens asigna el acento a la «curva Solo cola», pero su propia paleta de curvas da a «Un paso» (que es «solo cola») `#C77B1E`. El acento pinta «Solo cola (un paso)» en las barras de horas del Resumen; las curvas de la cola usan la paleta validada.
7. **«Puntaje: -50 (menos los puntos del sensor superior)»** en Explica no se tocó (decisión pendiente del usuario); solo recibió estilo.
8. **Alcance de la verificación.** Solo Chrome sin interfaz a 1366 y 1920 px (y 1366 x 768 para el Resumen); no probé otros navegadores, zoom, ni lector de pantalla. Los iconos de «Cumple» y «No cumple» son SVG propios porque la prueba de emojis de F20 prohíbe los caracteres ✓ y ✕ en `app/`.
9. **Docker y AWS:** fuera de alcance, no se tocaron ni se probaron. `requirements` sin cambios.

## Archivos modificados

Pruebas: **240** aprobadas, 0 fallidas, 0 omitidas (python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider, 166,7 s); antes de F24 había 219. Nuevas: `tests/ep3/test_pagina_f24.py` (21 pruebas); adaptadas, por fijar la piel clara de F23, las de F20, F21, F22, pulido, rediseño y F23.

`tests/ep3/conftest.py` desactiva durante las pruebas el escaneo de componentes de terceros que hace cada `AppTest` de Streamlit (1,3 a 2 s por prueba con `altair` importado; la página no usa componentes de terceros): sin eso la prueba de tiempo de «Validación» daba 3,3 s contra el límite de 3 s y la suite tardaba casi 280 s en vez de unos 165. El umbral no se tocó (DEC-102).

Sello: **intacto** (`f24_sello_despues.json`: 121 archivos comparados contra el registro de antes de F23; cambiados 0, faltan 0, nuevos 0); no se ejecutó `ingesta_nuevos.py` ni `evaluar_sellado.py`. `verificar_congelados.py` (14 de 14) y `verificar_congelados_v3.py` (5 de 5) se corrieron al final. Hashes de control: `plan_seleccion_ep3.sha256`, `plan_seleccion_ep3.json`, `manifest_v3.json` sin cambios.

Archivos con cambios en git y fecha de este trabajo (desde el 2026-11-21):

- `.streamlit/config.toml`: modificado
- `CLAUDE.md`: modificado
- `app/.streamlit/config.toml`: modificado
- `app/estilos.py`: modificado
- `app/secciones.py`: modificado
- `docs/ep3/ESTADO.md`: modificado
- `docs/ep3/MAPA_DE_ARCHIVOS.md`: modificado
- `docs/ep3/PENDIENTES_PAGINA.md`: modificado
- `docs/ep3/README_EP3.md`: modificado
- `docs/ep3/REPORTE_F24.md`: nuevo
- `docs/ep3/f24_contraste.json`: nuevo
- `docs/ep3/f24_fold_resumen.json`: nuevo
- `docs/ep3/f24_paleta_validacion.json`: nuevo
- `docs/ep3/f24_resultado_suite.json`: nuevo
- `docs/ep3/f24_sello_despues.json`: nuevo
- `docs/ep3/guia_estilo_pagina.md`: modificado
- `docs/ep3/guion_presentacion.md`: modificado
- `docs/ep3/informe_tecnico_EP3.md`: modificado
- `docs/ep3/pagina_guia_demo.md`: modificado
- `docs/ep3/plan_diseno_f23.md`: nuevo
- `docs/ep3/plan_integracion_readme.md`: modificado
- `docs/ep3/preguntas_cruzadas.md`: modificado
- `scripts/ep3/capturar_pagina.py`: modificado
- `scripts/ep3/f23_integridad_sello.py`: nuevo
- `scripts/ep3/f24_auditar_contraste.py`: nuevo
- `scripts/ep3/f24_capturar_curvas.py`: nuevo
- `scripts/ep3/f24_medir_resumen.py`: nuevo
- `scripts/ep3/f24_registrar_suite.py`: nuevo
- `scripts/ep3/generar_config_tema.py`: nuevo
- `scripts/ep3/generar_guia_estilo.py`: modificado
- `scripts/ep3/generar_mapa.py`: modificado
- `scripts/ep3/generar_plan_diseno_f23.py`: nuevo
- `scripts/ep3/generar_reporte_f24.py`: nuevo
- `tests/ep3/conftest.py`: modificado
- `tests/ep3/test_pagina_f20.py`: modificado
- `tests/ep3/test_pagina_f21.py`: modificado
- `tests/ep3/test_pagina_f22.py`: modificado
- `tests/ep3/test_pagina_f23.py`: nuevo
- `tests/ep3/test_pagina_f24.py`: nuevo
- `tests/ep3/test_pagina_pulido.py`: modificado
- `tests/ep3/test_pagina_rediseno.py`: modificado
- images/ep3/pagina/ (capturas finales, incluidas las curvas `02b_curvas_*`): 35 archivos (modificado, nuevo)
- images/ep3/pagina/antes_f24/ (cuatro capturas de la piel clara de F23, para comparar): 4 archivos (nuevo)
