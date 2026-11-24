# Reporte de F26: marca propia (Lente), afirmación y pie, y ajustes de coherencia

*Generado por `scripts/ep3/generar_reporte_f26.py` desde sus archivos de origen. Decisiones: DEC-106 a DEC-109 en `ESTADO.md`; guía de estilo regenerada en `guia_estilo_pagina.md`. Sin commit: el usuario hace el commit.*

**En una línea.** La página se llama Lente, tiene un símbolo propio, un título y una afirmación nuevos en el Resumen y un pie con la atribución del conjunto de datos; se quitó la pastilla «Datos de desarrollo»; los textos que dependen de dónde corre la página siguen la variable `EP3_ENTORNO`; y se corrigieron los desajustes de las capturas de F25. No cambiaron cálculos, cifras ni textos sellados.

## Qué se hizo

Pruebas: **264** aprobadas, 0 falladas, 0 omitidas (python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider, 56,7 s); antes de F26 había 249, y se agregaron 15 en `tests/ep3/test_pagina_f26.py`, que prueban las dos variantes de `EP3_ENTORNO` (`tests/ep3/conftest.py` quita la variable al empezar cada prueba para que no dependa del shell). Ningún límite subió. Sello: **intacto** (`f26_sello_despues.json`: 121 archivos comparados; cambiados 0).

| Código | Cambio | Estado | Qué quedó |
|---|---|---|---|
| A1 | Título del Resumen | Hecho | Título «Estado de las cámaras» y subtítulo «Etiquetas 2D de peatones y ciclistas en {n} segmentos de desarrollo.» (constantes). La etiqueta del menú sigue siendo «Resumen». La pestaña del navegador dice «Lente» en todas las vistas (`NOMBRE_PRODUCTO`). |
| A2 | Quitar la pastilla | Hecho | Fuera de todas las vistas, con su CSS, `CHIP_CORTO` y `CHIP_ESTADO` (sin código muerto). Su menú traía tres frases que no estaban en otra parte («Por eso las cifras de este flujo son optimistas…», «preparada y sellada…» y «La ganancia del flujo en dos pasos sale de 2 celdas…»): quedaron, sin perderse, en Ayuda › «¿Qué significa «en muestra»?». La divulgación sigue visible en las oraciones con «(en muestra)», en la alerta «Validación externa pendiente» y en el pie. |
| A3 | Marca arriba a la izquierda | Hecho | Símbolo propio y original (cuadro de 28 px en panel alto con borde `#2A3A57` y mini anillo de cinco cuñas en acento `#6FA0FF` alrededor de un auto visto desde arriba; sin nada de Waymo), `Lente` (14 px, 600) y `Waymo Open Dataset v2` (11 px, Texto 2). Cabe en la barra en modo normal (35 a 231 px de una barra de 236 px) y en presentación (40 a 236 px de 276 px). Favicon `app/assets/icono.png` (256 px) generado con Pillow desde la misma geometría (`scripts/ep3/generar_icono.py`; una prueba compara el PNG con lo que genera el script); la vista a 16 px está en `images/ep3/pagina/f26_favicon_16.png`. `PRODUCTO`, `set_page_config` y los docstrings de `app/` usan el nombre nuevo. |
| A4 | Afirmación del Resumen | Hecho | «Se marcaron k posibles huecos de cámara en la muestra de n segmentos.» (singular «Se marcó 1 posible hueco de cámara…»; sin marcas «No se marcó ningún posible hueco…»), 22 px, peso 500, `text-wrap: balance`; «n segmentos» en acento y «k posibles huecos» en el rojo del hueco, con 600. Conserva «posibles» y «en la muestra». Pruebas y documentos adaptados. |
| A5 | Pie | Hecho | Dos líneas de 12 px en `rgb(134, 150, 176)` (Texto 3), sin ámbar: la atribución (inglés, tal cual) y «Solución v3 congelada el 2026-11-14. Datos de desarrollo, 41 segmentos.». Cada línea ocupa 1 línea a 1366 px. **La atribución es texto provisional** (ver abajo). |
| B1 | Textos según el entorno | Hecho | `EP3_ENTORNO` (por defecto `local`: los textos de siempre, sin cambio; `servidor`: la variante pedida) para «Dónde corre», «Consideraciones éticas», el subtítulo de Puntuar y la pregunta frecuente de los archivos (`TEXTOS_ENTORNO`). **Verificado en el código que los archivos cargados no se escriben a disco** (`pd.read_parquet` sobre el objeto cargado, que Streamlit guarda en memoria; `puntuar_segmento` no escribe; las descargas son bytes; `guardar` es de la solución congelada y la página no lo llama), así que la variante dice «no se guardan»; una prueba lo vigila. Probadas las dos variantes. Docker no se tocó. |
| B2 | Líneas huérfanas | Hecho | `text-wrap: balance` en títulos, subtítulos y frases de resumen y `pretty` en párrafos y notas. El subtítulo se cortaba a ~560 px porque vivía en una columna estrecha junto al chip (3,6 de 6,6); sin el chip ocupa todo el ancho. Revisadas en las capturas a 1366 px las seis que se veían (Resumen, Cola, Auditoría, Validación, Puntuar, Ética): ninguna queda con una palabra suelta. Un efecto colateral que se corrigió: `pretty` partía en dos líneas el valor del control deslizante («20»); ahora esos valores no se parten. |
| B3 | Resumen reordenado | Hecho | Panel principal; debajo, «Impacto estimado» (izquierda) y «Cifras de apoyo» (derecha); debajo, «Alertas» en tres columnas con su enlace cada una. Sin quitar ni cambiar contenido. Panel principal a 1366 × 768: termina en **505 px** en modo normal y **556 px** en presentación (límite 640); el modo presentación sigue con el interruptor a la vista (757 px) y sin desborde de la barra. Los colores por concepto de F25 no cambiaron. |
| B4 | «Puntaje: -50…» | Hecho | Dentro de «Cómo se calcula» (con su texto igual), bajo los tres pasos. Nada sellado lo impedía; se adaptaron tres pruebas que buscaban el texto sin importar dónde. |
| C1 | Porcentajes | Hecho | «Casos encontrados en peatones / ciclistas» muestra 80,6 % y 44,3 % (los mismos valores) y también lo dicen la alerta de ciclistas, los avisos del ciclista (Cola y Explica una caja), Ética y Ayuda, para que ninguna vista muestre 0,443 y otra 44,3 %. No es texto sellado. |
| C2 | Cola agrupada | Hecho (informe) | `images/ep3/pagina/f26_cola_agrupada.png`, con «Agrupar por objeto» activado con un clic real: la primera pantalla muestra 12 objetos distintos (prioridades 1, 4, 5, 9, 13…) en vez de 12 filas idénticas. El valor por defecto no cambió; usted decide si lo deja activado para la demostración. |

**Medidas y capturas.** Contraste: 1.107 textos en 14 vistas, 0 por debajo de 4,5:1 (mínimo 5,42 en el DOM y 6,24 en los píxeles de las notas; `f26_contraste.json`). Ámbar `#F5B73B` en el DOM de las 8 vistas: 1 elemento (el punto de «Ciclistas»). 30 capturas completas (15 a 1366 px y 15 a 1920 px), 0 errores de consola, desplazamiento horizontal máximo 0 px. Revisadas una por una a 1366 px: Resumen (modo normal y presentación a 1366 × 768), Cola (curva y cajas), Explica una caja, Auditoría, Validación (En muestra y Selección), Puntuar, Ética, y los recortes de la marca (`f26_marca_normal.png`, `f26_marca_presentacion.png`) y del pie (`f26_pie.png`).

## Qué no se pudo y por qué

1. **La atribución de Waymo es provisional.** `ATRIBUCION_WAYMO` es el texto reconstruido de la licencia que traía el prompt; no se pudo contrastar con waymo.com/open/terms (esta tarea no hace peticiones externas). Hay que compararlo con la página antes de entregar; se cambia en una sola constante de `app_logica.py`.
2. **El nombre antiguo queda en documentos históricos.** «Auditor de etiquetas 3D» ya no está en lo visible de la página ni en `app/` ni en `app_logica.py` (una prueba lo vigila), pero sigue en `REPORTE_F18.md`, `plan_diseno_f23.md`, `ESTADO.md` (la bitácora, que cuenta lo que pasó), el notebook 14 y `scripts/ep3/crear_notebooks_ep3.py`. Esos archivos describen fases anteriores o son notebooks que esta tarea no regenera.
3. **`EP3_ENTORNO=servidor` no prueba nada fuera de la página.** El texto «no se guardan» es cierto para el código de la página; un proxy inverso o el registro de acceso del servidor pueden guardar otras cosas (nombres de archivo, direcciones IP). No se pudo comprobar porque Docker y el despliegue no se tocaron.
4. **El favicon se verificó como imagen, no en la pestaña de un navegador real.** El navegador sin interfaz declara el icono (`<link rel=icon>` apunta al PNG) y la vista a 16 px muestra el anillo y el auto; cómo lo pinte cada navegador en su pestaña no se pudo comprobar.
5. **El símbolo del auto se lee como un auto solo a tamaño grande.** A 16 px se distinguen el anillo y la silueta; la línea del parabrisas casi no se distingue. Es una limitación del tamaño, no de la geometría.
6. **«Cifras de apoyo» y «Alertas» cambiaron de lugar, no de contenido.** Si usted prefiere ver las alertas antes que las horas, es un intercambio de dos bloques en `resumen()`.

## Archivos modificados

Archivos con cambios en git y fecha de este trabajo (desde el 2026-11-22):

- `CLAUDE.md`: modificado
- `app/app.py`: modificado
- `app/assets/icono.png`: modificado
- `app/estilos.py`: modificado
- `app/secciones.py`: modificado
- `docs/ep3/ESTADO.md`: modificado
- `docs/ep3/PENDIENTES_PAGINA.md`: modificado
- `docs/ep3/README_EP3.md`: modificado
- `docs/ep3/f24_fold_resumen.json`: nuevo
- `docs/ep3/f25_ambar_en_el_dom.json`: nuevo
- `docs/ep3/f25_barra_lateral.json`: nuevo
- `docs/ep3/f26_contraste.json`: nuevo
- `docs/ep3/f26_marca.json`: nuevo
- `docs/ep3/f26_resultado_suite.json`: nuevo
- `docs/ep3/f26_sello_despues.json`: nuevo
- `docs/ep3/guia_estilo_pagina.md`: modificado
- `docs/ep3/guion_presentacion.md`: modificado
- `docs/ep3/informe_tecnico_EP3.md`: modificado
- `docs/ep3/pagina_guia_demo.md`: modificado
- `docs/ep3/plan_integracion_readme.md`: modificado
- `docs/ep3/preguntas_cruzadas.md`: modificado
- `scripts/ep3/capturar_pagina.py`: modificado
- `scripts/ep3/f26_capturas_extra.py`: nuevo
- `scripts/ep3/f26_registrar_suite.py`: nuevo
- `scripts/ep3/generar_docs_ep3.py`: modificado
- `scripts/ep3/generar_guia_estilo.py`: modificado
- `scripts/ep3/generar_icono.py`: nuevo
- `scripts/ep3/generar_mapa.py`: modificado
- `scripts/ep3/generar_pendientes_pagina.py`: modificado
- `scripts/ep3/generar_reporte_f26.py`: nuevo
- `src/waymo_evaluacion/ep3/app_logica.py`: modificado
- `tests/ep3/conftest.py`: modificado
- `tests/ep3/test_app.py`: modificado
- `tests/ep3/test_pagina_f20.py`: modificado
- `tests/ep3/test_pagina_f21.py`: modificado
- `tests/ep3/test_pagina_f23.py`: nuevo
- `tests/ep3/test_pagina_f24.py`: nuevo
- `tests/ep3/test_pagina_f25.py`: nuevo
- `tests/ep3/test_pagina_f26.py`: nuevo
- `tests/ep3/test_pagina_pulido.py`: modificado
- `tests/ep3/test_pagina_rediseno.py`: modificado
- images/ep3/pagina/ (capturas finales, recortes de la marca y del pie, vista del favicon a 16 px y Cola agrupada): 42 archivos (modificado, nuevo)
