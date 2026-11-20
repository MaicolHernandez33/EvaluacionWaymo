# Auditoría de diseño de la página (F20 y F21)

*Generado por `scripts/ep3/generar_auditoria_diseno.py`. P0: lectura de las capturas anteriores (`images/ep3/pagina/*_1366.png`, F19-B) contra la lista de patrones de plantilla. P11: causa del render incompleto de «Ética y límites» y pasadas de corrección.*

## Patrones de plantilla que se buscan

| Código | Patrón | Cómo se ve |
|---|---|---|
| T1 | Portada de marketing | eslogan en negrita, «Cómo funciona» con círculos numerados, «Empiece por aquí» con botones de llamada a la acción |
| T2 | Tarjetas KPI de plantilla | borde superior de color, cifras de 2 rem, tarjetas altas con la mitad vacía |
| T3 | Píldora de perfil y nombre del producto repetido | el producto aparece en la barra lateral y en el encabezado; el perfil como píldora azul |
| T4 | Banner ámbar por pantalla | el mismo aviso «En muestra» más un acordeón «¿Qué significa?» en cada sección |
| T5 | Avisos duplicados | «Nada se guarda ni se envía» en la barra lateral, el pie y el texto de la sección |
| T6 | Menú de botones de radio | ocho radios sin agrupar, sin jerarquía |
| T7 | Texto que habla de la propia página | «la página se lo dice en español», «Mueva los controles y vea qué pasa», «Pase el cursor sobre…» |
| T8 | Acordeones por todas partes | cada tabla, cada término del glosario y cada nota va en un expander |
| T9 | Sin interacción de producto | no hay selección de fila ni panel de detalle, filtros, estados ni vistas; solo deslizadores y una tabla |
| T10 | Títulos y cifras gigantes | H1 de 2,5 rem, cifra de probabilidad de 3 rem, mucho aire y poca información por pantalla |
| T11 | Pantalla vacía | más de la mitad de la página sin contenido |
| T12 | Tabla con defectos | encabezados cortados («Posició», «Folds en el máx»), barra «Prioridad» saturada en 100, columnas que no caben |

## P0. Auditoría previa por sección (capturas de F19-B a 1366 px)

### Inicio (se renombra Resumen)

Captura revisada: `images/ep3/pagina/01_inicio_1366.png`.

- T1: párrafo en negrita a modo de eslogan, «Cómo funciona» con tres círculos numerados y «Empiece por aquí» con dos botones grandes más un acordeón «Primeros pasos».
- T2: cuatro tarjetas con borde superior azul, azul, rojo y ámbar; cifras de 2 rem; las tres primeras quedan medio vacías porque la cuarta tiene dos cifras.
- T3 y T4: píldora «Perfil: Analista de revisión», nombre del producto en la barra lateral y en el encabezado, banner ámbar con acordeón «¿Qué significa?».
- T5: «Nada se guarda ni se envía» en la barra lateral y en el pie.
- T10: H1 de unos 2,5 rem; la información útil empieza a mitad de pantalla.
- Un acordeón de «Resultados técnicos» esconde las cinco cifras de validación.

**Qué se hará:** Se reemplaza por «Resumen»: franja de cuatro métricas compactas, «Impacto estimado» (barras de horas: sin orden, solo cola, auditoría + cola) y «Alertas» con enlaces. Sin portada, sin círculos, sin botones de acción. Las cinco cifras de validación pasan a «Validación».

### Auditoría de cámaras

Captura revisada: `images/ep3/pagina/02_auditoria_de_camaras_1366.png`.

- T2: cuatro tarjetas con borde de color. T7: «Pase el cursor sobre una celda…». T8: «Qué es un hueco» como acordeón abierto.
- Leyenda duplicada: la leyenda en palabras y, además, la barra de color de Altair («Cajas con pareja»).
- El mapa mide unos 900 px de alto a ancho completo y la Lista A queda al final, tras desplazarse; etiquetas de segmento de 12 dígitos en 10 px, ilegibles.
- No se puede ordenar por «con celdas marcadas primero»: los dos huecos están en filas 31 y 38.

**Qué se hará:** Dos columnas: mapa a la izquierda en un contenedor de altura fija con desplazamiento; a la derecha tarjetas mínimas, Lista A con «Acción sugerida» y descarga. Una sola leyenda. Etiquetas a 6 dígitos con el id completo en el tooltip; orden por defecto con celdas marcadas primero; opción de ver solo celdas con datos suficientes.

### Cola de revisión

Captura revisada: `images/ep3/pagina/03_cola_de_revision_1366.png`.

- T4: banner ámbar y «¿Qué significa?»; T8: cuatro acordeones («Qué significa», «Supuestos», «¿Qué tan confiable es esto?», «Comparar con un modelo de referencia»).
- T2: tres tarjetas con borde; la frase de resultado muestra solo el flujo en dos pasos y el de un paso queda escondido en un acordeón.
- T9: la tabla no se puede seleccionar; no hay detalle por caja, ni filtros, ni vista por objeto.
- T12: encabezado «Posició» cortado; la columna «Prioridad» es una barra saturada en 100 para todas las filas visibles; la columna de fotogramas lleva un texto de explicación que dice cómo desplazar la tabla (T7).
- Los controles ocupan tres filas (segmento, modo, supuestos, porcentaje).

**Qué se hará:** Maestro-detalle: barra de controles en una fila, frase con ambos flujos, pestañas «Curva de cobertura» y «Cola de cajas», tabla con selección de fila y panel de detalle, probabilidad calibrada en lugar de «Prioridad», vista «Agrupar por objeto», filtros por clase y cámara, anchos de columna calculados.

### Explica una caja

Captura revisada: `images/ep3/pagina/04_explica_una_caja_1366.png`.

- T7: «Mueva los controles y vea qué pasa». T10: probabilidad de 3 rem y tarjeta «entre el 59 % primero» de 2 rem; el texto «entre el 59 % primero» es ambiguo.
- T11: más de la mitad inferior de la pantalla está vacía; el gráfico de dependencia queda escondido en «Detalle técnico» (T8).
- T9: para la demostración hay que mover cuatro controles; no hay casos de ejemplo.

**Qué se hará:** Dos columnas (controles a la izquierda, resultado a la derecha), tres botones de ejemplo de un clic, texto «Posición en la cola: 59 % (0 % es la primera caja; 100 %, la última)» y el gráfico visible, sin pantalla vacía.

### Evidencia (se renombra Validación)

Captura revisada: `images/ep3/pagina/05_evidencia_1366.png`.

- T8: cada tabla en un expander, el primero abierto. T12: «Folds en el máx» cortado; «Folds» sin traducir; tablas de 33 columnas dentro de un acordeón.
- Sin ningún gráfico: seis pestañas de tablas; la lectura de una línea es lo único interpretado.

**Qué se hará:** Una pestaña por tema; cada una abre con un gráfico leído de los CSV (mejora de PR-AUC con IC, diferencia de AUC con IC, AUC con IC por candidato y por pliegue, tasa por tipo de caso, brazos A, B y C) y deja la tabla completa en un expander único; criterios O1 a O4 como tabla; «Pliegues».

### Ética y límites

Captura revisada: `images/ep3/pagina/06_etica_y_limites_1366.png`.

- La captura salió con una tarjeta completa y la segunda vacía: ver la sección «Causa del render incompleto» (es de la captura, no de la página).
- T2/T8: cinco tarjetas con borde apiladas, texto continuo; T5: repite «Nada se guarda ni se envía».

**Qué se hará:** «Ficha del sistema» en dos columnas (propósito, datos y licencia, desempeño, límites conocidos, consideraciones éticas, dónde corre) con las mismas cifras.

### Puntuar datos nuevos

Captura revisada: `images/ep3/pagina/07_puntuar_datos_nuevos_1366.png`.

- T1: tarjetas 1-2-3 que chocan con «Paso 1» y «Paso 2» de los cargadores. T7: «la página se lo dice en español». T8: «Formato esperado» en un acordeón y escrito como texto.
- Estado vacío azul que repite la instrucción; el resumen técnico usa `st.json` (volcado crudo).

**Qué se hará:** «Archivo 1 (obligatorio)» y «Archivo 2 (opcional)», formato esperado como tabla de columnas, estado vacío sobrio, resumen en tabla y un segmento de desarrollo de ejemplo reconstruido desde los datos derivados.

### Ayuda y glosario

Captura revisada: `images/ep3/pagina/08_ayuda_y_glosario_1366.png`.

- T8: once acordeones de glosario. T7: «Primeros pasos» escrito como tutorial. «Versión» repite el pie.

**Qué se hará:** Línea única con el flujo de tres capas, glosario como tabla de dos columnas, preguntas frecuentes como acordeones, sin sección «Versión».

### Transversal

- T3, T6: marco de la página: wordmark en la barra lateral, `st.navigation` con grupos (Revisión, Calidad de datos, Análisis, Herramientas, Ayuda), rol como selector discreto al pie.
- T4: un solo chip de estado persistente «Datos de desarrollo · sin validación externa» con popover; sin banners por pantalla.
- Sistema visual: bordes de 1 px, radio de 6 px, un solo acento azul oscuro, color semántico solo para estado, pila tipográfica del sistema con «Segoe UI» primero y cifras tabulares.

## Causa del render incompleto de «Ética y límites» en la captura

- **Qué se vio.** La captura de F19-B de «Ética y límites» a 1366 px salió con una tarjeta completa y la segunda como un marco vacío (`images/ep3/pagina/antes_f20/06_etica_y_limites_1366.png`); la de 1920 px, tomada en la misma corrida con el mismo código, salió con las cinco tarjetas (`antes_f20/06_etica_y_limites_1920.png`).
- **Conclusión: fue la captura, no un defecto de render.** Streamlit dibuja la página a medida que el script produce los elementos, de modo que existe una ventana en la que la página está a medias. El criterio de espera de F19-B daba la página por lista cuando aparecía el texto de la primera tarjeta y no había spinner, y falló por dos motivos: (1) la clave era el **primer** elemento, que aparece antes que los demás; (2) su indicador de ejecución (`stSpinner` y `stStatusWidget` con clase `running`) **no existe** en Streamlit 1.65 mientras el script corre: en las líneas de tiempo en frío (`data/08_reporting_ep3/captura_linea_tiempo_*.json`), el script estuvo ejecutándose en 23 muestras de «Ética y límites» y 23 de «Auditoría de cámaras» (cada 0,1 s) y ese indicador no apareció en ninguna (23 y 23 sin indicador). La señal fiable es el atributo `data-test-script-state` de `[data-testid="stApp"]` (`running` / `notRunning`).
- **Evidencia de páginas a medias.** En la carga en frío de «Auditoría de cámaras» hubo 7 muestras (0,70 s) con el script ejecutándose y las 4 métricas ya dibujadas pero sin el mapa ni las tablas; la página estuvo completa a los 2,91 s. «Ética y límites» (rediseñada: 6 bloques) se dibujó de una vez a los 2,89 s (0 muestras parciales): con tan pocos elementos la ventana es corta, lo que explica que en F19-B solo apareciera una vez (en el ancho de 1366 px).
- **¿Precarga? ¿Orden de ejecución?** La precarga no causa el defecto, pero alarga la ventana: la primera visita espera a los datos (`precarga.datos`) y durante ese tiempo la página está en ejecución (de 0,4 s a 2,89 s en la primera carga tras arrancar, con el hilo de precarga compitiendo por el procesador; con el servidor caliente, 1,0 s). Orden de ejecución: en F19-B el encabezado se dibujaba antes de cargar los datos y el contenido después; en F20 cada sección carga el contexto **antes** de dibujar (`secciones.ejecutar`), así que hay menos contenido a medias.
- **Qué cambió en la captura** (`scripts/ep3/capturar_pagina.py`): solo da la página por lista si se cumplen a la vez (1) `data-test-script-state = notRunning` y sin esqueleto ni spinner, (2) el número de nodos del DOM lleva ≥ 2 s estable, (3) aparece el **último** elemento clave de la sección y los conteos de elementos (por ejemplo, 6 bloques de la ficha de Ética, no 1), (4) el contenido supera un alto mínimo por sección y (5) está el pie. Si no se cumple en 60 s, no guarda la imagen y sale con error. Ya atrapó dos fallos de este tipo durante F20 (un alto mínimo mal fijado y el modo presentación que no se activaba). La prueba `test_la_espera_de_las_capturas_no_da_por_lista_una_pagina_a_medias` fija el caso de 1 bloque de 6.

## Pasadas de corrección (P11)

### Pasada 1: sobre las 9 capturas de 1366 px (tras el primer rediseño completo)

- T3 (wordmark): la línea de versión se cortaba («Solución v3 congelada el 2026-11-1»); ahora dice «Solución v3 · 2026-11-14».
- T7 y snake_case (Resumen): la nota de fuente citaba una clave interna de la evidencia (`ie12__brazo_C_y_equilibrio`); ahora solo los CSV de origen. El eje de horas tenía demasiadas marcas: 8.
- T12 (Auditoría): la Lista A y el detalle desbordaban en 590 px (7 y 8 columnas) y «Acción sugerida» quedaba oculta; la Lista A pasó a una tabla con el texto ajustado a la celda (5 columnas) y el detalle a una línea por celda marcada.
- T10/T11: la descripción de cada página quedaba pegada al contenido; más aire bajo la descripción.
- T9 (captura de la cola): fotografiaba solo la pestaña de la curva y no mostraba el maestro-detalle; ahora abre «Cola de cajas» y elige la primera fila con un clic real del ratón.
- Captura del modo presentación: el `click()` de JavaScript no cambiaba el interruptor; ahora es un clic real y se espera el cambio de estilos (`--escala: 1.18`) antes de fotografiar.

### Pasada 2: sobre las 18 capturas regeneradas (1366 y 1920 px)

- T4/T3 (modo presentación): el chip de estado se cortaba («…validación exter…») porque la letra es 18 % mayor; las columnas del encabezado pasaron de [5 | 2,4] a [3,6 | 3].
- T9/T12 (cola con el panel abierto): con la razón [2,7 | 1,3] «Tipo de caso» quedaba fuera de la vista; con [3,2 | 1,2] se ven la probabilidad, la clase y el tipo de caso junto al panel de detalle.
- Barra lateral en modo presentación: aparecía una barra de desplazamiento horizontal; `overflow-x: hidden`.
- Auditoría: la captura exigía dos tablas estáticas y ahora hay una más una lista; el conteo de elementos de la captura se corrigió (la espera lo detectó: no guardó la imagen hasta corregirlo).
- Verificación de que no quedan los patrones T1 a T12 en las capturas de 1366 y 1920 px: ver la tabla siguiente.

## F21: dos pasadas de corrección y mediciones

### F21, pasada 1: primeras capturas de 1366 px (cola con y sin fila, Explica, Resumen y las seis pestañas de Validación)

- Cola (T12): «Segmento» quedaba cortado a 1366 px porque el ancho de las columnas suponía 6,6 px por carácter y el texto real mide 5,5 a 5,6 (medido sobre la captura: «lejanos y poco densos» ocupa 117 px para 21 caracteres). Constantes medidas (`formato.PX_POR_CARACTER` = 5,6 de encabezado y 5,5 de contenido) y «Tipo de caso» sin ancho fijo: las nueve columnas quedan visibles sin desplazamiento.
- Cola: la nota del empate decía «probabilidad de 80,2 % a 90,4 %» mientras todas las filas visibles muestran 87,8 %. Ahora: «87,8 % en la primera y de 80,2 % a 90,4 % en el grupo» (el rango existe porque cada partición calibró por separado).
- Resumen (T9): los enlaces de las alertas quedaban 8 px más arriba que su texto, porque el markdown de Streamlit lleva margen inferior negativo y acorta la columna del texto. CSS que lo anula (`[class*="st-key-alerta_"]`); la diferencia medida baja a 3 o 4 px.
- Resumen: «en muestra» salía tres veces (etiqueta de la barra, nota y alerta); la alerta ahora dice «Todas las cifras salen de los 41 segmentos de desarrollo». Quedan dos.
- Validación, Ensambles: las etiquetas del eje se repetían (−0,04, −0,04, −0,03, −0,03…) por usar dos decimales con un paso de 0,005; las marcas se calculan (`_marcas_eje`). «E4 contra vista obs» pasó a «vista de observación».
- Validación, Selección (T12): la tabla de resultados tenía una columna «Fuente» con nombres de archivo (.csv) y «Detalle» cortado; se quitó la columna (la fuente va en una línea: informe técnico, sección 12 y anexo B) y «Detalle» usa su ancho. La tabla O1 a O4 tenía una fila vacía al pie (altura de 31 px por fila contra 30 reales).
- Validación, No supervisado: las dos barras se superponían y las etiquetas salían cortadas («lejanos y poco d…»); altura por categoría y etiquetas completas.
- Validación, En muestra: la leyenda salía cortada («Solo celdas sanas, sin aud…»); leyenda completa y valores sobre las barras.
- Tablas de evidencia: «Proporción menos probabilidad de la regla» no era un porcentaje; pasó a «Diferencia: proporción menos probabilidad de la regla» (la prueba de formatos engañosos lo detectó).

### F21, pasada 2: regeneración completa (8 páginas, cola sin selección, 6 pestañas de Validación y modo presentación; 1366 y 1920 px)

- Ética (1366 px): «79,8» y «%» quedaban en líneas distintas; Explica (1920 px): «20» y «% de las cajas». Los textos HTML (`estilos._e`) y los textos largos de Explica (`formato.sin_corte`) usan espacio de no separación entre el número y «%».
- Cola: con la nota más larga del empate, el final del texto («…no es informativo») quedaba bajo la barra de herramientas de la tabla (los iconos de descarga y búsqueda, que Streamlit dibuja sobre la esquina superior derecha); se acortó la frase («87,8 % en la primera y de 80,2 % a 90,4 % en el grupo») y la nota reserva ese espacio a la derecha (`padding-right`), de modo que si no cabe pasa a dos líneas.
- Mensajes de error con rutas internas (`data/06_models_ep3`, `scripts/ep3/f7_preparar_app.py`): la prueba nueva de términos internos los encontró; ahora dicen qué falta sin nombrar archivos.
- Aceptado sin cambio: la Auditoría mantiene el mapa en un contenedor de 560 px con desplazamiento (41 filas); en Validación y Auditoría la descripción ocupa dos líneas y el chip queda centrado en vertical, pero a la misma distancia del borde derecho; la tabla de Selección muestra su borde inferior.

### Mediciones sobre las capturas finales

Fuente: `data/08_reporting_ep3/capturas_resultado.json` (30 capturas; anchos 1366, 1920 px). Se mide con el DOM, no a ojo.

| Medida | Resultado | Exigido |
|---|---|---|
| Chip de estado contra el borde derecho del contenido (máximo en las capturas) | 0,0 px | ≤ 1,5 px |
| Enlace de cada alerta contra el centro de su texto (máximo, 12 alertas) | 3,3 px | ≤ 5 px |
| Desplazamiento horizontal de la página (máximo) | 0 px | ≤ 0 |

### Verificación final contra los patrones de plantilla

| Código | Estado en las capturas finales |
|---|---|
| T1 | Sin portada: el Resumen abre con métricas, impacto y alertas; no hay «Cómo funciona», círculos numerados ni botones de acción. |
| T2 | Métricas de 1,5 rem sin bordes de color, de la misma altura; en modo presentación, 2 x 2. |
| T3 | El producto aparece una vez (wordmark); el rol es un selector al pie; no hay píldora. |
| T4 | Un solo chip persistente con popover; sin banners ni «¿Qué significa?». |
| T5 | «Nada se guarda ni se envía» solo en Ética y en la pregunta frecuente de Ayuda (prueba). |
| T6 | Navegación agrupada con íconos y la página activa resaltada; sin radios. |
| T7 | Sin frases sobre la propia página ni tutorial en segunda persona (prueba de frases prohibidas). |
| T8 | Los acordeones quedan solo donde son útiles: preguntas frecuentes y «Ver tabla completa». |
| T9 | Cola con selección de fila y panel de detalle, vista por objeto, filtros y flujos; ejemplos de un clic en Explica. |
| T10 | Títulos de 1,5 rem; la información útil empieza en la primera pantalla. |
| T11 | Ninguna página queda con más de la mitad vacía (Explica ocupa la pantalla con controles, resultado y gráfico). |
| T12 | Encabezados con el ancho calculado (sin «Posició»), probabilidad calibrada en lugar de la barra «Prioridad», «Particiones» en vez de «Folds» (F21: nada de «pliegue»). |

Las capturas anteriores a F20 (F19-B) están en `images/ep3/pagina/antes_f20/` para comparar; las de F20, anteriores a F21, en `images/ep3/pagina/antes_f21/`.
