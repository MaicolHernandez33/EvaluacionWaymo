# Reporte F39: «Puntuar datos nuevos» con los dos archivos y un botón explícito

Escrito para: Rafa, que va a probar esto en vivo frente al docente. Fecha: 2026-11-24. Ningún número, modelo, regla ni umbral cambió: los resultados de los 4 segmentos reales, con y sin archivo 2, y del ejemplo son **idénticos byte a byte** (CSV) antes y después.

## Estado en una línea
Hecho todo lo del prompt (pasos 0 a 4). Falta solo que usted lo pruebe a mano en su navegador y lo mire: yo lo probé con un navegador real y los cargadores reales (11 casos, todos bien), pero no a mano con el selector de archivos de Windows.

## Qué decidir
1. **README (F38).** Su sección 16 todavía dice «archivo 2 primero y archivo 1 después». Ya no hace falta. No lo toqué (el prompt lo prohíbe); se arregla cambiando una frase en `scripts/ep3/readme_f38.py` y regenerando.
2. **Cargadores parejos y botón primario.** Para que los dos recuadros se vean iguales quité el color azul del botón «Elegir archivo» del archivo 1 (los dos son neutros) y el azul pasó a «Puntuar segmento», que ahora es la acción principal.
3. **Bloque «Archivos del segmento» siempre presente.** Antes de puntuar está abierto; después, cerrado. Es siempre el mismo bloque a propósito: con dos formas distintas de dibujarlo, el navegador no mostraba los archivos ya subidos.

## Reconocimiento (Paso 0)
1. **Dónde se disparaba el puntaje.** `app/secciones.py`, función `_entradas` (antes de F39, líneas 1030 a 1078): con `f1 is not None` (línea 1048) validaba y llamaba a `_calcular`, guardaba `_pt_vista` y hacía `st.rerun()` (líneas 1074 a 1077). El selector del archivo 2 desaparecía porque `puntuar()` (línea 1126 en adelante) solo dibujaba `_entradas` cuando `_pt_vista` era `None`; con el resultado guardado, los dos cargadores ya no se dibujaban.
2. **Textos que describían el flujo.** `puntuar.VACIO_TEXTO` («Con el archivo lidar_box (o el segmento de ejemplo) aparecerán aquí…», cambiado); el texto de «Formato de los archivos de entrada» (ahora `puntuar.FORMATO_INTRO`, agrega que se pueden subir en cualquier orden); `PASOS` y los rótulos de los cargadores (sin cambio); `ARCHIVO_2_AYUDA` (sin cambio, por pedido); `NOTA_SIN_ARCHIVO_2`, `TEXTO_CELDAS_NO_BUSCADAS` y las tarjetas «no se buscaron: falta el archivo 2» (describen el resultado, no el orden; sin cambio); el subtítulo de la página y la pregunta frecuente de los archivos (`TEXTOS_ENTORNO`, no describen el orden; sin cambio, como pide el prompt); la guía de estilo (generador, actualizado); `CLAUDE.md` (línea «Orden en vivo», actualizada) y `ESTADO.md` (DEC-146 queda reemplazada por DEC-151); el guion generado por `f37_armar_demo.py` (actualizado) y `datos_demo/LEEME_DEMO.md` (reescrito); `docs/ep3/REPORTE_F37.md` y el README conservan el flujo viejo (el primero es historia; el segundo, ver «Qué decidir» 1).
3. **Estado en `st.session_state`.** Antes: `_pt_vista` (el segmento puntuado), `usar_ejemplo`, `pt_ronda` (cambia la clave de los cargadores `pt_f1_<ronda>` y `pt_f2_<ronda>`), `pag_pt_*` (paginación de las tablas) y `_pt_sesion` (Resumen). «Cargar otro segmento» borraba `pt_f1_*`, `pt_f2_*`, `pag_pt_*`, `_pt_vista` y `usar_ejemplo` y sumaba 1 a `pt_ronda`. El bloque del Resumen lo escribe `puntuar.registrar_en_sesion` al guardar un resultado de archivos (una fila por segmento; reemplaza la fila del mismo segmento; no registra el ejemplo). Nuevo en F39: `_pt_error` (mensaje y firma) y `_pt_firmas` (caché en memoria de las firmas, sin el contenido de los archivos).

## Qué cambié, archivo por archivo
- `app/secciones.py`: reescribí el bloque de Puntuar. `_cargadores` (los dos cargadores, siempre en el bloque «Archivos del segmento»), `_firma`, `_puntuar_archivos` (validación y puntaje; las mismas validaciones y la misma `_calcular` de antes), `_zona_puntuar` (botón, ayuda, ejemplo y avisos), `_guardar_vista`, `_soltar_archivos`; `_calcular` guarda la firma y el nombre completo del segmento; `_aviso` respeta los saltos de línea; `_resultado` muestra el nombre completo bajo el título. `_entradas` desapareció.
- `src/waymo_evaluacion/ep3/puntuar.py`: textos nuevos (`BOTON_PUNTUAR`, `EXPANDER_ARCHIVOS`, `AYUDA_*`, `AVISO_CAMBIARON`, `PASO_OMITIDO`, `FORMATO_INTRO`, `VACIO_TEXTO` nuevo), `ayuda_flujo`, `firma_archivo`, `_ids`, mensaje de segmentos distintos con los dos ids, `estado_pasos(hay_resultado, con_huecos=True)` con el estado «omitido» y dos campos nuevos de `Vista` (`firma`, `nombre_segmento`).
- `app/estilos.py`: estado «omitido» del indicador de pasos (guion neutro con borde punteado, nunca el check), estilo parejo de los dos cargadores (mismo alto del texto de apoyo y mismo botón «Elegir archivo»), ayuda bajo el botón y el ejemplo pequeño a la derecha.
- Pruebas: `tests/ep3/test_pagina_f39.py` (9 nuevas) y adaptadas, sin borrar ninguna, `test_pagina_f35.py` (los cargadores siguen después del resultado, dentro del bloque cerrado), `test_pagina_f23.py` (el nombre de la función que dibuja los cargadores) y `test_pagina_f24.py` (la acción principal es «Puntuar segmento»).
- Herramientas: `scripts/ep3/f39_regresion.py`, `f39_tiempos.py` y `f39_pruebas_ui.py` (nuevos); `f37_pruebas_ui.py` queda marcado como obsoleto.
- Documentos: `datos_demo/LEEME_DEMO.md` (guion nuevo, no se versiona), `ESTADO.md` (DEC-151 a DEC-153), `CLAUDE.md`, el generador de la guía de estilo y el del mapa de archivos.
- No toqué: README ni su generador, modelo, regla, umbrales, `cola_segmento`, el Resumen (salvo que sigue recibiendo la fila) ni el sello.

## Comportamiento nuevo (lo que verá)
- **Inicio:** dos cargadores iguales, uno al lado del otro, con las etiquetas y el texto de apoyo de hoy; «Puntuar segmento» deshabilitado con «Agregue el archivo 1 para poder puntuar.»; el ejemplo es un botón pequeño a la derecha.
- **Solo archivo 1:** botón habilitado y «Todavía no agregó el archivo 2: se puntuará sin buscar huecos de cámara.»; **archivos 1 y 2:** «Listo para puntuar con búsqueda de huecos de cámara.».
- **Resultado:** tres pasos; si no hubo archivo 2, el paso 2 dice «omitido: falta el archivo 2» con un guion neutro. Los archivos quedan en «Archivos del segmento» (cerrado), donde se puede agregar, quitar o cambiar cualquiera.
- **Cambiaron los archivos:** el resultado desaparece y aparece «Cambiaron los archivos: pulse Puntuar segmento para actualizar el resultado.». La firma (nombre, tamaño y sha256) se calcula una vez por archivo subido.
- **Segmentos distintos:** «El archivo 2 no corresponde al archivo 1: ninguno de sus segmentos aparece en el archivo 1.», luego `Archivo 1: <id completo>`, `Archivo 2: <id completo>` en líneas separadas y «Revise que ambos sean del mismo segmento.». El error se queda mientras no cambien los archivos.
- **Resultado de un archivo:** bajo «Segmento …476581», el nombre completo `16229547658178627464_380_000_400_000`. En el ejemplo no se muestra (no viene de un archivo).

## Regresión de resultados (Paso 3.1)
Línea base guardada antes de editar (`docs/ep3/f39_regresion_antes.json`) y repetida después (`f39_regresion_despues.json`), con la misma función de la página (`secciones._calcular`). Se comparan los dos CSV que se descargan (`lista_A_nueva.csv` y `lista_B_nueva.csv`, byte a byte por sha256) y todas las cifras de pantalla (tarjetas y resumen del cálculo). El ZIP no se compara porque cada archivo adentro lleva la hora de creación y su hash cambia en cada corrida aunque el contenido sea el mismo.

| Caso | Cajas | Celdas marcadas | Cola | lista_B (sha256, 12) antes → después | lista_A antes → después | Cifras de pantalla | Resultado |
|---|---|---|---|---|---|---|---|
| 10689101165701914459_2072_300_2092_300 · archivos 1 y 2 | 938 | 0 | 938 | 125e681dd425 → 125e681dd425 | d511e38c6206 → d511e38c6206 | iguales | idéntico |
| 10689101165701914459_2072_300_2092_300 · solo archivo 1 | 938 | 0 | 938 | 3e9a615678f0 → 3e9a615678f0 | d511e38c6206 → d511e38c6206 | iguales | idéntico |
| 13356997604177841771_3360_000_3380_000 · archivos 1 y 2 | 7.854 | 0 | 7.854 | 15346cd481ce → 15346cd481ce | d511e38c6206 → d511e38c6206 | iguales | idéntico |
| 13356997604177841771_3360_000_3380_000 · solo archivo 1 | 7.854 | 0 | 7.854 | 37bdbf69af91 → 37bdbf69af91 | d511e38c6206 → d511e38c6206 | iguales | idéntico |
| 16229547658178627464_380_000_400_000 · archivos 1 y 2 | 3.161 | **1** | 2.964 | 523b5fd303db → 523b5fd303db | 6b30fd8638c1 → 6b30fd8638c1 | iguales | idéntico |
| 16229547658178627464_380_000_400_000 · solo archivo 1 | 3.161 | 0 | 3.161 | 8ba04ef106d5 → 8ba04ef106d5 | d511e38c6206 → d511e38c6206 | iguales | idéntico |
| 2551868399007287341_3100_000_3120_000 · archivos 1 y 2 | 5.314 | 0 | 5.314 | 2e94d45bd7b0 → 2e94d45bd7b0 | d511e38c6206 → d511e38c6206 | iguales | idéntico |
| 2551868399007287341_3100_000_3120_000 · solo archivo 1 | 5.314 | 0 | 5.314 | 0df44ec356ca → 0df44ec356ca | d511e38c6206 → d511e38c6206 | iguales | idéntico |
| ejemplo de desarrollo 911012534050 | 1.715 | 1 | 1.447 | 1455a510580f → 1455a510580f | a6f83069d736 → a6f83069d736 | iguales | idéntico |

**9 de 9 idénticos.** El segmento con hueco (`16229547658178627464_380_000_400_000`) da 1 celda marcada (cámara 5), 197 cajas afectadas, 175 sin pareja (88,8 %) y 2.964 cajas en la cola, como en el prompt (225 cajas en rango, tasa de pares 0,0 % frente a 91,4 % de mediana de referencia; se ve en la captura 4). El de 0 celdas (`10689101165701914459_2072_300_2092_300`) da 0 de 5.

## Tiempos (Paso 3.3)
Navegador real, cargadores reales, mediana de 3. «Antes»: el tiempo corre desde que termina de subirse el archivo 1 (el 2 ya estaba) hasta ver el resultado. «Después»: desde el clic en «Puntuar segmento» hasta ver el resultado (los archivos ya estaban subidos).

| Segmento | Cajas | Antes: 3 mediciones (s) | Antes: mediana | Después: 3 mediciones (s) | Después: mediana |
|---|---|---|---|---|---|
| 10689101165701914459_2072_300_2092_300 | 938 | 1,67 / 1,25 / 1,19 | 1,25 | 1,38 / 0,64 / 0,73 | 0,73 |
| 16229547658178627464_380_000_400_000 | 3.161 | 1,35 / 1,41 / 1,35 | 1,35 | 0,75 / 0,78 / 0,76 | 0,76 |
| 2551868399007287341_3100_000_3120_000 | 5.314 | 1,35 / 1,35 / 1,30 | 1,35 | 0,75 / 0,77 / 0,77 | 0,77 |
| 13356997604177841771_3360_000_3380_000 (el más grande) | 7.854 | 1,47 / 1,41 / 1,49 | 1,47 | 0,84 / 0,84 / 0,86 | 0,84 |

**No empeora; el clic tarda 0,7 a 0,9 s.** La mejora aparente es porque «antes» incluía la subida del archivo 1; la suma de subir y puntuar es parecida. La subida de los dos archivos no se cronometró aparte (el script espera 3 s fijos tras subirlos).

## Pruebas de estado en el navegador (Paso 3.2)
`scripts/ep3/f39_pruebas_ui.py`, una sola sesión sin recargar la página, con los cargadores reales y las cifras comparadas con la línea base. Resultados completos en `docs/ep3/f39_pruebas_ui.json`. **11 de 11 correctas.**

| Caso | Resultado |
|---|---|
| 0. Inicio | Dos cargadores a la vista en un bloque abierto; botón deshabilitado; ayuda «Agregue el archivo 1…». |
| 1. Archivo 1, luego 2, luego Puntuar (segmento con hueco) | Con solo el 1: botón habilitado y ayuda «Todavía no agregó…»; con el 2: «Listo para puntuar…»; no hay resultado hasta pulsar. Tras pulsar: 1 de 5, 197 afectadas, 175 sin pareja, paso 2 «hecho», nombre completo del segmento visible. |
| 2. Cargar otro segmento; archivo 2, luego 1, luego Puntuar (0 celdas) | Los cargadores y el resultado se limpian; 0 de 5, 938 cajas. |
| 3. Solo archivo 1, Puntuar | Paso 2 «omitido: falta el archivo 2» sin check; «Celdas marcadas —». |
| 4. Puntuar con solo el 1, luego agregar el 2 | El resultado desaparece y avisa «Cambiaron los archivos…»; al pulsar busca huecos (1 de 5). |
| 5. Quitar el 2 después de puntuar | Desaparece el resultado y avisa; al pulsar, sin huecos. |
| 6. Cambiar el 1 por otro segmento después de puntuar | Avisa; al pulsar con el 2 del otro segmento: error con los dos ids completos; al corregir el 2 y pulsar, resultado correcto y sin el error viejo. |
| 7. Archivo que no es parquet | «El archivo «no_es_parquet.parquet» no es un parquet válido o está dañado…», sin resultado. |
| 8. Cargar otro segmento y repetir (el más grande) | Resultado correcto (7.854 cajas), sin el error del caso anterior. |
| 9. Botón de ejemplo | 1 de 5, 268 afectadas, 227 sin pareja; etiqueta «ejemplo de desarrollo»; sin aviso de cambio. |
| 10. Resumen | «Segmentos puntuados en esta sesión» con una fila por segmento (tres filas: la repetida se reemplazó; el ejemplo no figura). |

## Pruebas automáticas y congelados (Paso 3.4)
Ver «Resultado de pytest» al pie. Congelados: EP2 14 de 14 y v3 5 de 5, antes y después. Sello intacto.

## Lo que NO pude verificar
- Con el selector de archivos real de Windows (arrastrar y soltar a mano, o «Elegir archivo» con el diálogo): usé el protocolo del navegador, que mete el archivo en el mismo campo.
- **Volver a elegir exactamente el mismo archivo** en un cargador al que se le quitó ese archivo: con el protocolo del navegador no se detecta el cambio (las pruebas usan una copia con otro nombre). No sé si a mano pasa lo mismo; si pasa, hay que quitar el archivo con la «x» y elegir otro, o recargar.
- **Pulsar «Puntuar segmento» mientras un archivo todavía sube** puntúa con lo que ya llegó al servidor; con archivos de 1 a 2 MB la subida es instantánea, pero con uno de cientos de MB habría que esperar a que termine.
- Otros anchos de pantalla: las capturas son a 1366 px; el texto de apoyo del archivo 2 puede ocupar 4 líneas en pantallas más angostas y desalinear un poco los recuadros.
- Navegadores distintos de Chrome; el idioma de «Elegir archivo» y «Arrastre el archivo aquí» lo pone Streamlit según el navegador (en mis capturas sale en inglés).

## Capturas (`images/ep3/pagina/para_revision_f39/`, 8 PNG a 1366 px)
`f39_01_inicio_dos_cargadores`, `f39_02_solo_archivo_1_antes_de_puntuar`, `f39_03_resultado_sin_archivo_2_paso_omitido`, `f39_04_resultado_con_ambos_archivos_1_celda`, `f39_05_aviso_cambiaron_los_archivos`, `f39_06_error_segmentos_distintos_dos_ids`, `f39_07_resultado_con_0_celdas`, `f39_08_ejemplo_de_desarrollo`.

## Resultado de pytest (suite completa, en copias temporales del repositorio)
| Momento | Resultado |
|---|---|
| **Antes** (estado de cierre de F38, antes de tocar nada) | 479 pasadas, 0 falladas (81 de EP2 y 398 de EP3) |
| Primera corrida **después** | 487 pasadas y 1 fallada: `test_pagina_f24` seguía exigiendo el botón «Elegir archivo» del archivo 1 en azul; se adaptó a «la acción principal es Puntuar segmento y los dos cargadores tienen el mismo estilo» |
| **Después** (final) | **488 pasadas, 0 falladas** (81 de EP2 y 407 de EP3: las 398 de antes y las 9 nuevas de `test_pagina_f39.py`) |

Pruebas nuevas: botón deshabilitado sin archivo 1 con los dos cargadores abiertos, textos de ayuda según los archivos, firma de archivos, paso 2 «omitido» sin check, mensaje con los dos ids completos (y «y N más»), resultado de otros archivos que no se muestra y pide volver a puntuar, ejemplo sin aviso y sin registrarse, y que el código solo puntúa archivos bajo el botón. Congelados: 14 de 14 y 5 de 5, antes y después; sello intacto.

**Un aviso:** en el repositorio real, `tests/ep3` da 406 pasadas y **1 fallada**: `test_readme_f38::test_el_numero_de_pruebas_de_ep3_del_readme_es_el_recolectado`. No es un error de F39: el README (F38) dice «398 pruebas recolectadas» y ahora son 407 por las pruebas nuevas. No regeneré el README (el prompt lo prohíbe). Para dejarlo al día, cuando F38 lo permita: `contar_pruebas.py` → `medir_pruebas_ep3.py` → `generar_readme.py` (y de paso cambiar en `readme_f38.py` la frase «archivo 2 primero y archivo 1 después» de la sección 16). En las copias temporales la suite completa pasa porque sus pruebas de EP2 regeneran el README de la copia.
