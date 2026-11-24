# Guía de estilo de la página

*Generada por `scripts/ep3/generar_guia_estilo.py` desde `app/estilos.py` y `src/waymo_evaluacion/ep3/app_logica.py`. Las pruebas `tests/ep3/test_pagina_rediseno.py`, `tests/ep3/test_pagina_pulido.py` y `tests/ep3/test_pagina_f20.py` , `tests/ep3/test_pagina_f22.py`, `tests/ep3/test_pagina_f23.py` y `tests/ep3/test_pagina_f24.py` exigen el contraste, que el tema de Streamlit use estos tokens y las reglas de gráficos, tablas y textos de abajo. Los tokens viven **solo** en `app/estilos.py`: de ahí salen el CSS y los dos `config.toml` (`scripts/ep3/generar_config_tema.py --comprobar` falla si se desfasan).*

## Producto y marco (F20)
- **Nombre y marca (F26):** Lente, con la sublínea «Waymo Open Dataset v2». Es neutro: no usa el logo, la tipografía ni los colores de marca de Waymo; «Waymo» aparece solo como fuente del dato. Aparece **una sola vez**, en la marca de la barra lateral: un **símbolo propio** (cuadro redondeado de 28 px en `panel_alto` con borde `panel_alto_borde` y un mini anillo de cinco cuñas en `acento` alrededor de la silueta de un auto visto desde arriba; SVG inline sin URL, que se lee a 28 y a 16 px), el nombre (14 px, 600) y la sublínea (11 px, `texto_2`). El favicon (`app/assets/icono.png`, 256 px) es el mismo símbolo, dibujado con Pillow por `scripts/ep3/generar_icono.py` desde la misma geometría (`E.cunas_simbolo`). Los textos de identidad son constantes de `app_logica.py` (`NOMBRE_PRODUCTO`, `SUBLINEA_MARCA`, `TITULO_RESUMEN`, `SUBTITULO_RESUMEN`, `AFIRMACION_RESUMEN*`, `ATRIBUCION_WAYMO`): se cambian en un solo lugar. La versión de la solución pasó al pie.
- **Descripción:** Revisión priorizada de cajas 3D de peatones y ciclistas sin par 2D.
- **Ícono de la pestaña:** `app/assets/icono.png`, dibujado por `scripts/ep3/generar_icono_pagina.py`.
- **Navegación** (`st.navigation` con páginas de archivo en `app/paginas/`; 8 páginas agrupadas):
- **Visión general:** Resumen
- **1 · Filtro:** Auditoría de cámaras
- **2 · Priorización:** Cola de revisión
- **Análisis:** Validación
- **Herramientas:** Explica una caja, Puntuar datos nuevos
- **Ayuda:** Ética y límites, Ayuda y glosario
- **Rol** (selector discreto al pie de la barra lateral, etiqueta «Rol»; 3 roles): cambiar de rol lleva a la página que sugiere. Sin píldora de perfil en el encabezado.
- **Encabezado de página:** título pequeño (1.6rem, no un H1 enorme) y una línea de descripción, a todo el ancho y con `text-wrap: balance`. **Sin chip de estado** (F26): desde F28 el Resumen ya no dice «en muestra» ni lleva la alerta «Validación externa pendiente»; la divulgación sigue en el pie, en Cola, Validación, Ética y límites y Ayuda; el texto que traía el menú del chip pasó a Ayuda, en «¿Qué significa «en muestra»?». El título del Resumen es «Estado de las cámaras» y su subtítulo «Etiquetas 2D de peatones y ciclistas en {n} segmentos.»; la etiqueta del menú sigue siendo «Resumen».
- **Pie único (F26):** dos líneas de 12 px en `texto_3`, sin ámbar: (1) la atribución del conjunto de datos, en inglés y tal cual (`ATRIBUCION_WAYMO`; **texto provisional**, reconstruido de la licencia: contrastarlo con waymo.com/open/terms antes de entregar) y (2) «Solución v3 congelada el <fecha>. Datos de desarrollo, <n> segmentos.». «Nada se guarda ni se envía» aparece solo en Ayuda y Ética.

## Paleta (tokens)
Dirección F24 («consola de control» oscura; es un cambio de piel sobre la estructura de F23, que no se tocó): **tema oscuro nativo de Streamlit** (`base = "dark"`) con tres planos de azul noche (lienzo, barra lateral y panel) que se distinguen por tono y por una línea fina, y una **sola superficie elevada** (el panel principal del Resumen y el detalle de la cola); lo demás es plano. **Acento azul claro** para la acción, **teal** para lo sano, **gris azulado plano** para «sin datos», **coral = hueco** y **ámbar = advertencia real de fiabilidad** (desde F25 solo el punto de «Ciclistas»; antes también marcaba «en muestra» y el chip). El anillo de cámaras es el protagonista. Radios según el papel: tablas 0, controles 8px, panel principal 14px; la única sombra de la hoja es la del panel (`0 10px 28px rgba(0, 0, 0, .35)`). Sin bordes superiores de color, sin franjas de acento, sin píldoras (salvo el chip de estado de F25), sin etiquetas en mayúsculas y sin degradados decorativos (el único degradado es la escala de la leyenda del mapa). Apta para daltonismo: el color de los huecos nunca va solo (siempre contorno grueso, una «X» y texto, en el mapa y en el anillo), y el estado de cada cámara también va en palabras («Sana», «Hueco», «Sin datos»). **Ningún texto baja de 4,5:1**: el más tenue es `texto_3` (notas), medido en los tokens y en los píxeles de las capturas (`f24_contraste.json`).

| Token | Valor | Uso |
|---|---|---|
| `fondo` | `#0B1220` | lienzo de la página |
| `barra` | `#0E1729` | barra lateral (un tono sobre el lienzo; la separa una línea fina a la derecha) |
| `barra_borde` | `#1E2B45` | línea derecha de la barra lateral |
| `panel` | `#121C30` | superficie principal: panel del Resumen, detalle de la cola, tablas y gráficos |
| `panel_borde` | `#22314D` | borde fino (1 px) del panel |
| `panel_alto` | `#18253D` | controles, encabezados de tabla y la fila elegida |
| `panel_alto_borde` | `#2A3A57` | borde de los controles y de los botones de ejemplo |
| `texto` | `#E8EEF8` | texto principal |
| `texto_2` | `#A9B8CF` | texto secundario |
| `texto_3` | `#8696B0` | notas: el mínimo permitido (ningún texto queda por debajo) |
| `acento` | `#6FA0FF` | enlaces, selección, ítem activo, relleno del botón primario |
| `acento_fondo` | `#1A2B4F` | tinte del acento: ítem activo de la barra y hover de botones |
| `acento_activo` | `#223A66` | botón pulsado |
| `acento_hover` | `#8CB4FF` | botón primario con el cursor encima |
| `sano` | `#3CC9B8` | trazo de lo sano y extremo claro de la rampa del mapa |
| `sano_relleno` | `#14535A` | relleno de la cuña sana del anillo |
| `hueco` | `#FF7A6B` | SOLO huecos de cámara (trazo y «X»), siempre con «X» y con texto |
| `hueco_fondo` | `#3A1A22` | relleno suave de la celda y de la cuña con hueco |
| `sin_datos` | `#1B2740` | relleno plano y neutro de «sin datos» (no es una alerta: sin rayado ni color) |
| `sin_datos_borde` | `#3A4B6B` | borde de «sin datos» y de las cuñas apagadas |
| `aviso_texto` | `#F5B73B` | ámbar: SOLO advertencias reales de fiabilidad (el punto de «Ciclistas: regla poco confiable» y el del aviso del ciclista); ya no es «en muestra» (F25) |

## Contraste (WCAG, mínimo 4,5:1 en texto)
| Par | Razón | Estado |
|---|---|---|
| texto sobre panel | 14,59:1 | cumple |
| texto_2 sobre panel | 8,46:1 | cumple |
| texto_3 sobre panel | 5,67:1 | cumple |
| acento sobre panel | 6,60:1 | cumple |
| sano sobre panel | 8,29:1 | cumple |
| hueco sobre panel | 6,68:1 | cumple |
| texto sobre panel_alto | 13,14:1 | cumple |
| texto_2 sobre panel_alto | 7,62:1 | cumple |
| texto_3 sobre panel_alto | 5,11:1 | cumple |
| acento sobre panel_alto | 5,94:1 | cumple |
| sano sobre panel_alto | 7,47:1 | cumple |
| texto sobre fondo | 16,06:1 | cumple |
| texto_2 sobre fondo | 9,31:1 | cumple |
| texto_3 sobre fondo | 6,24:1 | cumple |
| acento sobre fondo | 7,26:1 | cumple |
| sano sobre fondo | 9,13:1 | cumple |
| hueco sobre fondo | 7,35:1 | cumple |
| texto sobre barra | 15,36:1 | cumple |
| texto_2 sobre barra | 8,90:1 | cumple |
| texto_3 sobre barra | 5,97:1 | cumple |
| acento sobre barra | 6,95:1 | cumple |
| texto sobre acento_fondo | 11,99:1 | cumple |
| acento sobre acento_fondo | 5,42:1 | cumple |
| fondo sobre acento | 7,26:1 | cumple |
| aviso_texto sobre panel | 9,49:1 | cumple |
| aviso_texto sobre panel_alto | 8,55:1 | cumple |
| hueco sobre hueco_fondo | 6,11:1 | cumple |
| fondo sobre acento_hover | 8,99:1 | cumple |
| texto sobre acento_activo | 9,66:1 | cumple |

## Tipografía y espaciado
- **Una sola familia sans para todo**, títulos y afirmación incluidos: `"Inter", "Segoe UI Variable Text", "Segoe UI", system-ui, -apple-system, Arial, sans-serif`. Pesos 400, 500 y 600. Se quitó el serif (Cambria) de F23: junto al sans de los datos se leía como un documento de Word. **Sin CDN, sin Google Fonts, sin imágenes remotas:** la página funciona sin internet y una prueba falla si algún archivo de `app/` contiene `http://` o `https://` (la única excepción es la declaración de espacio de nombres del SVG propio).
- **Inter es opcional.** Si se deja `app/static/fonts/Inter-Variable.woff2` (licencia OFL, con su archivo de licencia al lado), el tema lo carga solo (`[[theme.fontFaces]]` en el `config.toml` y `server.enableStaticServing`); si falta, la página cae a Segoe UI (Windows) o a la fuente del sistema sin fallar. Hoy el archivo **no está** en el repositorio.
- Cifras con `font-variant-numeric: tabular-nums`. Escala (base 15 px): nota 0.78rem, secundario 0.86rem, cuerpo 1rem, destacado 1.12rem, titulo_pagina 1.6rem, titular 1.75rem; cifras de la tira de cifras 1.5rem; tablas compactas (filas de 30 px).
- Espaciado: xs = 0.25rem, s = 0.5rem, m = 1rem, l = 1.5rem, xl = 2rem (se aplican como márgenes y separaciones).
- Estados **hover** y **foco** visibles (contorno de 2 px en el acento) en botones, enlaces de la navegación y controles. **Transiciones de 150 ms** (`--t`) en botones, enlaces de la navegación, selectores, filas y pestañas; el único movimiento propio es la aparición del panel de detalle de la cola (240 ms), que responde a elegir una fila. `prefers-reduced-motion` lo apaga todo.

## Componentes
- **Panel principal** (`st.container(key="panel_principal")`, radio 14px, sombra): en el Resumen es el bloque «Alertas de cámara» (rótulo, titular, subtítulo, filas de alerta y anillo). El **detalle de la cola** (`panel_detalle`, `panel_vacio`) y el panel «Segmentos con más cajas prioritarias» (`panel_segmentos`) usan la misma superficie.
- **Indicadores** (`aud-kpis`, F29): una franja de cuatro tarjetas planas (segmentos sin revisar, cámaras con alerta, cajas en la cola, % de cajas sin pareja), en una sola fila; «Cámaras con alerta» va en el rojo del hueco si es mayor que 0 (el número y la nota siguen en el texto). Valor en 600 de 2,1 rem; el cambio respecto de ayer solo se muestra si existe un corte anterior (hoy no: no se inventa).
- **Tira de cifras** (`aud-metricas`, solo en Auditoría y Puntuar): una fila con líneas finas, sin fichas ni íconos; en pantallas angostas va 2 x 2 (nunca una cifra huérfana).
- **Cifras de apoyo** (`aud-cifras`): tabla pequeña (rótulo, valor y nota). Desde F29 vive en **Validación** (antes en el Resumen); las barras finas de las filas de horas son proporciones de cifras ya calculadas.
- **«en muestra» suelto** (`aud-muestra`, F25): texto simple en `texto_3` de 12 px, sin caja, sin borde y sin color de aviso; solo se usa donde ninguna oración vecina lo dice (hoy ninguna vista lo necesita: el Resumen y la Cola lo dicen en la oración).
- **Titular y filas de alerta** (F29): el titular (`aud-titular`, 1.75rem, peso 600) dice «Hay {huecos} en los últimos datos sin revisar.» con «N posibles huecos de cámara» en el rojo del hueco, o «Todas las cámaras sanas.»; debajo, una fila por celda marcada (hasta 5) con un ícono de cancelar, el segmento (6 últimos dígitos), la cámara (número y nombre), el estado «Hueco» **en palabras** y el botón «Auditar». La primera fila viene elegida (borde y relleno rojos, botón relleno) y el anillo muestra el segmento de la fila elegida; «Auditar» abre la Auditoría con esa celda ya elegida (`session_state`).
- **Cola del Resumen** (`cola_resumen`): tabla de 5 filas con Prioridad, Segmento, Caja, Cámara, Clase, Prob. sin pareja y «Abrir» (abre «Explica una caja» con esa caja); encabezado en mayúsculas pequeñas (uno de los dos únicos usos de mayúsculas, junto al rótulo de las alertas, a pedido del usuario). Orden determinista: probabilidad descendente, luego segmento y luego identificador de objeto y fotograma; la columna Caja es única, así que no hay filas idénticas. En ciclistas, la etiqueta «Regla poco confiable» lleva el punto ámbar. **Barras** de 10 px con los extremos redondeados en el panel de segmentos prioritarios (los 5 segmentos con más cajas en la cola del 20 %).
- **Ficha** (`aud-ficha`): título y texto separados por una línea fina, en dos columnas (Ética y límites); sin tarjetas.
- **Anillo de cámaras** (`aud-anillo`, `E.anillo_camaras`): la pieza propia de la página y el protagonista del Resumen. Un vehículo visto desde arriba con una cuña por cámara (1 frontal, 2 frontal izq., 3 frontal der., 4 lateral izq., 5 lateral der.; atrás no hay cámaras). Estados: **sana** (teal), **hueco** (relleno coral suave, contorno coral grueso y una «X»), **sin datos** (gris azulado plano), más **activa** (acento sólido: la cámara que ve la caja elegida) y **apagada** (contorno punteado, sin selección). En el detalle de la cola mide unos 120 px y va **encima** de la probabilidad. Los tres primeros son los del mapa de calor y la leyenda dice lo mismo en los dos sitios (`leyenda_estados`, `leyenda_mapa`). En el Resumen muestra el segmento elegido (`estado_camaras_segmento`, que lee las columnas `hueco` y `sin_datos` de `matriz_calor`) con su lista de cámaras en texto; en la Auditoría, las celdas marcadas por cámara; en el detalle de la cola, la cámara de la caja. SVG inline con texto alternativo; no agrega cifras.
- **Estados vacíos** (`aud-vacio`): un dibujo, qué falta y qué hacer. Panel de detalle de la cola sin fila («Seleccione una fila para ver su detalle»), cola sin cajas tras filtrar («Ninguna caja cumple los filtros») y «Puntuar datos nuevos» sin archivos. El cargador de archivos tiene una zona de arrastre con borde punteado (`sin_datos_borde`); el botón de ejemplo de «Puntuar datos nuevos» es el único botón primario de la página (relleno del acento, texto del color del lienzo).
- **Resultado** (`aud-resultado`): la frase principal de la cola, con ambos flujos, sin caja.
- **Tablas HTML** (`aud-tabla`) para textos largos (glosario) y para los criterios de selección: radio 0, el texto se ajusta a la celda. Las tablas de datos son `st.dataframe` compactos con anchos medidos para que entren sin desplazamiento; «Tipo de caso» no lleva ancho fijo y absorbe el espacio sobrante.

## Gráficos y mapas
- **Tema único de los gráficos** (`_grafico` en `app/secciones.py`): fondo transparente sobre el panel, rejilla `#22314D`, sin línea de eje ni marcas, ejes y etiquetas en `texto_2` (12 px o más), títulos en `texto`, sin marco, barras con el extremo redondeado (4 px) y la misma tipografía de la página. Los valores van en `texto`.
- **Mapa de calor de la Auditoría** (rampa de un solo tono teal, **más claro = más proporción de cajas con pareja**: `#15655C, #187F74, #289A8C, #32B1A2, #3CC9B8`, el último es `sano`; validada con `validate_palette.js --ordinal` contra el panel, en `f24_paleta_validacion.json`). Las 41 filas (16 px cada una) se ven **sin desplazamiento interno** y hay **una sola leyenda**, de una línea corta por estado (`leyenda_mapa`; las explicaciones largas pasaron al atributo `title`). Tiene **tres estados que no se confunden**:
  1. **sana**: teal según la proporción de cajas con pareja (con datos suficientes);
  2. **sin datos** («Sin cajas o menos de 100 en el rango»): **plano y neutro** (`#1B2740` con borde `#3A4B6B`), sin rayado: la ausencia de datos no debe llamar la atención como una alerta; significa «no se evalúa» y **no es lo mismo que una tasa de 0 %**;
  3. **hueco**: relleno coral suave, contorno coral grueso y una «X» (el color nunca va solo).
  Las etiquetas de segmento son los **últimos 6 dígitos** (el id completo va en el tooltip); por defecto los segmentos con celdas marcadas van primero y se puede ver solo las celdas con datos suficientes.
- **Curvas de la cola**: la línea lleva el color **y** el trazo (no solo el color), la banda sombreada es del mismo color con transparencia, y la leyenda sale de las líneas y lista solo las curvas dibujadas; ningún texto lleva el color de la serie. La paleta se validó con `validate_palette.js` (skill dataviz) en **modo oscuro sobre el panel**: partiendo de la propuesta del prompt de F24 (azul, naranja, verde, violeta y magenta), los pares adyacentes pasaban, pero el par azul–violeta (Dos pasos contra XGBoost) fallaba para todos los pares (ΔE 6,9 en visión normal y 1,7 con protanopia); se oscurecieron el verde y el violeta y se subió el magenta hasta que **todos los pares** pasaron (CVD de 8 o más y visión normal de 15 o más; números en `f24_paleta_validacion.json`). El trazo sigue distinto (discontinuo en «Un paso», la regla y XGBoost) y las curvas de referencia llevan **etiqueta directa** sobre la línea. Regla técnica: la banda no codifica el campo «nombre» (Vega-Lite fusionaría las leyendas y borraría la de las líneas), así que hay una banda por curva con color fijo.
- **Impacto estimado** (**Validación › En muestra**, sección fija debajo del gráfico; F30): una frase y una tabla pequeña de horas para encontrar el 80 % (sin orden, solo cola, auditoría + cola), con una barra fina por fila; debajo la nota «Estimación: cajas × fracción para el 80 % × 20 s por caja (supuesto, no medido)» y el menú «Fuente».

- **Explica una caja (F33)**: «Herramientas» en el menú (se entra desde «Explicar esta caja →» de la Cola o del Resumen). Los **ejemplos son botones de selección** (`st.pills`, ninguno elegido al abrir; al mover un control el botón se suelta). **Un solo control decide**: «Puntos del sensor superior» (`select_slider` en escala comprimida, con el umbral del presupuesto y el umbral A dentro de las opciones); «Puntos del LiDAR», distancia y clase solo describen el tipo de caso («no cambia el lugar»). El resultado va primero: probabilidad grande, veredicto con texto y color («Se revisaría / No se revisaría con un presupuesto del N %», el presupuesto y el flujo son los de la Cola, que los deja en `_plan_cola`), barra «Lugar en la cola» (con la prioridad máxima empatada dice «0 a N %» y entre cuántas cajas está, nunca un lugar exacto) y «Cómo se calcula» en cuatro pasos con valores vivos (el puntaje, «-50», vive en el paso 2). El gráfico usa escala comprimida (`symlog`), rótulos directos sobre las dos líneas finas (el presupuesto actual y el umbral para hallar el 80 % de las cajas sin pareja, ambos calculados de la cola real) y el marcador «Esta caja: p %». «Cajas parecidas» es una tarjeta corta con la nota de que es descriptiva (post hoc). Desde la Cola o el Resumen se llega con los valores de esa caja y un aviso («Valores cargados desde …») con enlace para volver; el aviso desaparece al mover un control.
- **Validación (F34)**: cabecera con el **veredicto calculado** («La regla simple se mantiene: ninguna de las N alternativas probadas «vale la pena» frente a ella» solo si ninguna alternativa cumple O2; si alguna cumple, un texto neutro con cuántas y cuáles; `validacion.titular_validacion`), cuatro tarjetas (AUC con su intervalo, cajas analizadas, casos encontrados en peatones y en ciclistas; mismas fuentes que el Resumen) y tres etiquetas neutras (la de ciclistas con el punto ámbar). **Cinco pestañas** con la misma plantilla (lectura → un gráfico → puntos clave → «Tablas de apoyo (N)» cerradas): «Modelo elegido» (tarjetas O1 a O4 con «✓/✕ X de N» calculado de la tabla de selección y el aviso de que la propia regla no cumple O4, solo si no lo cumple), «Generalización» (con la línea del AUC mínimo por partición del plan v3 y la partición más débil rotulada), «Alternativas» (hiperparámetros y ensambles con el estado en texto al final de cada fila), «Tipos de caso» y «En muestra» (aviso, lectura, «Impacto estimado», «De dónde viene la mejora de la auditoría» y el gráfico, con el flujo también en texto dentro de cada barra). La tabla «Curvas de validación» no se muestra (queda en la descarga). El candidato «Regla top» se muestra como «regla de puntos del sensor superior» y las vistas como «vista de observación», «de tamaño» y «de posición».
- **Tabla estándar (F34)**: un solo componente (`app/tablas.py` + `tablas_estandar.py`) para Validación y Puntuar: sin desplazamiento vertical interno (hasta 25 filas todas; con más, de 25 en 25; la cola de Puntuar, de 50 en 50), intervalos en una columna («0,797 (0,701–0,889)»), encabezados cortos con el nombre completo en `title`, números a la derecha con cifras tabulares, decimales fijos por tipo, signo menos único «−» y «+» en las diferencias positivas, primera columna fija y sombras de borde solo si hay más columnas, título, «Responde: …», conteo de filas y «Descargar CSV» con todas las columnas sin redondear. Las columnas que no caben van solo al CSV (el pie dice cuántas). El identificador de segmento se muestra «…534050» (como en el resto de las páginas); el de 12 dígitos queda en los CSV. Los desplegables solo muestran el recuadro de foco con el teclado.
- **Puntuar datos nuevos (F35)**: tres pasos arriba (el actual con `aria-current`), el archivo 1 como acción principal (botón destacado del selector), el ejemplo como botón discreto («¿Solo desea ver cómo funciona?»), estado vacío corto con el anillo neutro, y con un segmento el resultado en la misma página (encabezado con «Cargar otro segmento» y «Descargar resultados (CSV)», tarjetas, «Celdas marcadas» con el anillo, «Cola de cajas de este segmento» de 50 en 50 y «Resumen del cálculo» plegado). Los errores de archivo salen como avisos en español, sin traceback. Lógica y textos en `puntuar.py`.
- **Puntuar datos nuevos, flujo con los dos archivos (F39)**: los dos cargadores (el 1 obligatorio y el 2 opcional) quedan a la vista dentro del bloque «Archivos del segmento» (abierto antes de puntuar, cerrado después), con el mismo estilo y el mismo alto; nada se puntúa al subir un archivo: el botón primario «Puntuar segmento» (deshabilitado sin el archivo 1) calcula, con una línea de ayuda según los archivos. El resultado lleva la firma (nombre, tamaño y sha256) de los archivos: si cambian, desaparece y la página dice «Cambiaron los archivos: pulse Puntuar segmento para actualizar el resultado.». Sin archivo 2, el paso «Revisar celdas marcadas» sale «omitido: falta el archivo 2» con un guion neutro, no el check. El ejemplo de desarrollo es un botón pequeño a un lado.
- **Ética y límites y Ayuda y glosario (F36)**: tarjetas con icono decorativo (`aria-hidden`), el aviso «Decide siempre una persona.» como primer bloque y la barra peatones/ciclistas con los dos porcentajes escritos y una descripción para el lector de pantalla (el ámbar solo en el punto de ciclistas). Los textos viven en `etica_ayuda.py` y `app_logica.py`; los que dependen del despliegue, en `TEXTOS_ENTORNO` (constante `MODO_DESPLIEGUE`, `local` por defecto; `EP3_ENTORNO` la reemplaza solo para la copia que se captura). El glosario es de tarjetas con buscador (sin distinguir mayúsculas ni tildes) y grupos Datos, Revisión y Rigor; sin coincidencias dice «Ningún término coincide con la búsqueda.». Los bloques con borde punteado de «Qué hace cada página» son los que se agregaron.
- **Resumen: segmentos puntuados en la sesión (F37)**: debajo de todo lo congelado, solo después de puntuar un segmento nuevo en «Puntuar datos nuevos»; tabla estándar (segmento, celdas marcadas, cajas, sin pareja, hora), una fila por segmento y la línea «No forman parte de las cifras congeladas». Vive en la sesión (se pierde al recargar); los ejemplos de desarrollo no se registran. Sin esas filas el Resumen es idéntico al de siempre.

| Curva | Color | Trazo | Contraste sobre el panel |
|---|---|---|---|
| Dos pasos | `#4C82F2` | continuo | 4,68:1 |
| Un paso | `#C77B1E` | discontinuo (trazo 7, hueco 4) | 5,09:1 |
| Regla de puntos, un paso | `#0F7C55` | discontinuo (trazo 2, hueco 3) | 3,27:1 |
| XGBoost (referencia) | `#8F4AB4` | discontinuo (trazo 4, hueco 2) | 3,08:1 |
| Ensamble E2 (referencia) | `#D75893` | continuo | 4,62:1 |

## Tablas
- **Cola de revisión (maestro-detalle):** `st.dataframe` con selección de una fila (`on_select="rerun"`) y **seis columnas que sirven para decidir**: Prioridad, Prob. sin pareja, Puntos sensor sup., Cámara, Tipo de caso y Clase (la advertencia completa de ciclista va en el detalle y bajo la tabla). Distancia, segmento y fotogramas pasan al panel de detalle; los identificadores, al CSV. A 1366 px entran sin recortes ni desplazamiento horizontal (anchos medidos). El **panel de detalle está siempre visible a la derecha** de la tabla (relación de 64 % a 36 %); sin fila elegida muestra un estado vacío («Seleccione una fila para ver su detalle») y con una fila elegida aparece con un fundido corto. **La curva de priorización es la primera pestaña.** **Nota del empate** sobre la tabla, calculada de la cola: «Las primeras N cajas empatan (0 puntos del sensor superior; …); el orden entre ellas no es informativo»; desaparece si no hay empate. La columna **Prob. sin pareja** (probabilidad calibrada, en %) reemplaza a la antigua barra «Prioridad», que quedaba saturada en 100.
- **Fotogramas** (`Fotogramas`): un mismo objeto aparece en varios fotogramas y cada uno es una caja distinta de la cola; la vista «Agrupar por objeto» deja una fila por objeto sin cambiar el conteo de cajas a revisar.
- **Formatos (es-CL) de `tabla_legible`**: enteros sin decimales («3», «1.600»), proporciones como porcentaje, el parámetro de regularización C en notación científica («1,0e-5»), nombres legibles de hiperparámetros y valores en español («Partición» o «En validación cruzada por segmentos», nunca «Fold», «pliegue» ni «Fuera de pliegue»); nunca una columna con dos escalas distintas mezcladas («20» junto a «1.600» es lo esperado; «20,000» junto a «1.600» no) ni «-0,000».
- **Controles**: sin decimales con punto (la distancia de «Explica una caja» va de 1 en 1 m).

## Un concepto, un color (F25)
`E.FLUJOS_COLORES` (en `app/estilos.py`) es el **único mapa entidad -> color** de los flujos; lo usan las barras de horas del Resumen, las barras de «En muestra» de Validación y las curvas de la Cola (las curvas «Dos pasos» y «Un paso» leen de ahí). Validado con `validate_palette.js` (modo oscuro, superficie `#121C30`, todos los pares; `f25_paleta_validacion.json`).

| Entidad | Color | Dónde |
|---|---|---|
| Revisión sin orden | `#8696B0` | barras de horas del Resumen |
| Solo cola (un paso) | `#C77B1E` | barras de horas del Resumen, barras de «En muestra» y la curva «Un paso» |
| Auditoría + cola (dos pasos) | `#4C82F2` | barras de horas del Resumen, barras de «En muestra» y la curva «Dos pasos» |
| Solo celdas sanas, sin auditoría | `#B0508A` | barras de «En muestra» (Validación) |

El gris es la línea base neutra (el piso de croma de una paleta categórica no aplica a un gris; contrasta 5.7:1 con el panel y siempre lleva su rótulo). El color de «Solo celdas sanas, sin auditoría» no repite ninguno de los de las curvas ni de los tokens de estado; queda cerca del rosa de E2 (ΔE 7,8 en visión normal), pero no comparten gráfico. El color solo refuerza: cada barra y cada curva lleva su nombre.

**Ámbar de interfaz (F25):** solo advertencias reales. Queda un punto de 0,6 rem en la etiqueta «Regla poco confiable» de las filas de ciclista de la cola del Resumen y el del aviso del ciclista (Cola y Explica una caja); el filete de la nota de empate usa `sin_datos_borde`. Se comprueba en el DOM real (`f25_ambar_en_el_dom.json`).

**Auditoría de cámaras, Cola de revisión y Explica una caja (F31 a F33).** Las tres páginas siguen los HTML de `docs/referencias_diseno/` salvo lo que el reporte `REPORTE_F31_F33.md` lista como desviación. Reglas que quedan:
- **Auditoría (F31):** franja de indicadores (celdas, cajas afectadas y sin pareja), una sola tabla de celdas marcadas con la celda resaltada en el anillo, mapa de calor con «Mostrar 50 más (N de M)» (orden de gravedad; con hasta 60 segmentos se muestran todos) y «¿Qué es un hueco?» plegado. Las cifras salen de `resumen_auditoria`.
- **Cola (F32):** el plan (flujo, presupuesto o meta, «Volver al 20 %») va arriba y cambia todas las cifras; los filtros de la lista no cambian las tarjetas. Tres tarjetas («Cajas a revisar», «Cajas sin pareja que se encuentran», «Tiempo estimado»), «Cola de cajas» primero y la curva después, tabla de 50 en 50 con detalle lateral y «Explicar esta caja →», supuestos plegados al final. El orden de la cola (`preparar_cola`) solo reordena el mismo conjunto que elige `cola_segmento`: no cambia qué cajas entran ni los positivos.
- Las flechas «→» y «←» de «Explicar esta caja →», «Ir a la cola de revisión →» y «← Volver a …» las pidió el prompt de F31 a F33 (el texto vive en constantes de `app_logica.py`); la regla de F23 de no usar flechas sigue valiendo para el resto de enlaces y botones.
- Un botón deshabilitado (p. ej. «Anterior» en la primera página) se distingue por el borde punteado y el cursor, no por un texto apagado (4,5:1).

**Barra lateral (F25, ajustada en F27 y F30):** se quitaron los 6 rem vacíos que Streamlit deja bajo el último control y se redujo el aire entre los seis grupos del menú; a 1366 × 768 el selector «Rol» queda visible sin desplazar la barra (`f25_barra_lateral.json`). Desde F30 no hay interruptor de modo presentación.

**Barra de herramientas de los gráficos (F25):** se oculta solo en los gráficos (`div:has(> [data-testid="stVegaLiteChart"]) > [data-testid="stElementToolbar"]`, un selector por `data-testid`); la de las tablas se conserva. Tapaba el final de la oración de referencia de la Curva de priorización (`f25_barra_herramientas.json`).

## Afirmación, orden del Resumen y textos según el entorno (F26)
- **Divulgación de rigor (F30):** el Resumen ya no lleva la línea «Validación externa pendiente»; la divulgación sigue en Ética y límites, Validación, Ayuda y el pie global (atribución de Waymo y «Datos de desarrollo»). La etiqueta «Datos de ejemplo» del mockup no va en la página.
- **Orden del Resumen (F29):** franja de cuatro indicadores; bloque «Alertas de cámara» (titular, filas de alerta y anillo; el recuadro mide lo que mide su contenido más alto: a la izquierda rótulo, titular, subtítulo y filas de alerta, a la derecha el anillo arriba con su rótulo y su leyenda; la lista de alertas termina antes de 640 px a 1366 × 768); «Cola de revisión» con sus filtros por clase, cámara y segmento, la tabla y el panel «Segmentos con más cajas prioritarias»; y el pie global. «Impacto estimado» y «Cifras de apoyo» están en Validación.
- **Sin líneas huérfanas:** `text-wrap: balance` en títulos, subtítulos y frases de resumen, y `text-wrap: pretty` en párrafos y notas. El subtítulo de página ya no tiene un tope de ancho.
- **El puntaje de la regla («-50»)** (Explica una caja, F33) vive en el paso 2 de «Cómo se calcula», con «menos los puntos del sensor superior» debajo.
- **Casos encontrados por clase** se muestran como porcentaje (80,6 % y 44,3 %: los mismos valores 0,806 y 0,443) en las cifras de apoyo (Validación), en los avisos del ciclista, en Ética y en Ayuda.
- **Textos que dependen de dónde corre la página** (variable de entorno `EP3_ENTORNO`; por defecto `local`: los textos de siempre; `servidor`: la variante de una demostración desplegada). Viven en `TEXTOS_ENTORNO` de `app_logica.py`:

| Texto | `local` (por defecto) | `servidor` |
|---|---|---|
| donde_corre | Solo en este equipo (localhost), sin conexión a internet. No debe exponerse en una red sin autenticación. | En un servidor conectado a internet ([nombre del servicio]). Cualquiera que tenga el enlace puede abrir la aplicación. No se deben subir datos que no puedan compartirse con ese servicio. |
| puntuar_subtitulo | Un segmento nuevo se puntúa con la solución congelada y se obtienen sus celdas marcadas y su cola de cajas. | Un segmento nuevo se puntúa con la solución congelada y se obtienen sus celdas marcadas y su cola de cajas; en esta página el procesamiento ocurre en el servidor. |
| puntuar_etiqueta | Procesamiento local y en memoria | Procesamiento en el servidor y en memoria |
| puntuar_etiqueta_2 | No se guarda nada | No se guarda nada |
| consideracion_etica | Las tablas locales tienen identificadores de objeto y marcas de tiempo. Nada se guarda ni se envía. | Las tablas tienen identificadores de objeto y marcas de tiempo. Los archivos que se suben en «Puntuar datos nuevos» se procesan en la memoria del servidor durante la sesión y no se guardan. |
| faq_archivos | No. Nada se guarda ni se envía: «Puntuar datos nuevos» procesa el archivo en memoria y la aplicación no hace ninguna conexión a internet. | Los archivos que se suben se procesan en la memoria del servidor durante la sesión y no se guardan. Salen del equipo hacia el servidor, así que no se deben subir datos que no puedan compartirse con él. |
| borrador |  | borrador: verificar |

Los archivos cargados **no se escriben a disco**: `puntuar_segmento` trabaja en memoria, la página los lee con `pd.read_parquet` sobre el objeto cargado (Streamlit los guarda en memoria) y las descargas se arman como bytes; una prueba vigila que `app/` no escriba archivos.

## Cargador de archivos
Los textos propios de Streamlit («Drag and drop…», «Browse files», «500MB per file») no se pueden cambiar por configuración: se ocultan con CSS y se muestra el texto en español («Arrastre el archivo aquí. Formato parquet, hasta 500 MB», botón «Elegir archivo»). Riesgo: depende de los `data-testid` de Streamlit 1.65. Los cargadores se rotulan «Archivo 1 (obligatorio)» y «Archivo 2 (opcional)» (sin tarjetas numeradas).

## Arranque
`scripts/ep3/arrancar_app.bat` y `.ps1` abren la página con `app/lanzar.py`, que carga y calienta los datos y la solución congelada (`app/precarga.py`) antes de aceptar visitas; con `streamlit run app/app.py` directo la página funciona igual, pero la carga empieza en la primera visita. Medición: `data/08_reporting_ep3/pagina_arranque.json`.

## Íconos y direcciones
Material Icons de Streamlit (`:material/nombre:`), sin emojis (una prueba lo vigila). La página por defecto (Resumen) se sirve en la raíz; las demás, en la ruta indicada.

| Página | Ícono | Ruta |
|---|---|---|
| Resumen | `material/dashboard` | `/resumen` |
| Cola de revisión | `material/format_list_numbered` | `/cola` |
| Explica una caja | `material/manage_search` | `/explica` |
| Auditoría de cámaras | `material/videocam` | `/auditoria` |
| Validación | `material/fact_check` | `/validacion` |
| Puntuar datos nuevos | `material/upload_file` | `/puntuar` |
| Ética y límites | `material/balance` | `/etica` |
| Ayuda y glosario | `material/help` | `/ayuda` |

## Números y redacción
- **Formato es-CL** (`src/waymo_evaluacion/ep3/formato.py`, con pruebas): miles con punto (80.571), decimales con coma (87,4), porcentaje con espacio (70,3 %).
- **Registro neutro de herramienta interna** («Se muestran…», «Seleccione…»): sin frases que hablen de la propia página, sin tutorial en segunda persona, sin repetir avisos. Una prueba vigila las frases prohibidas («Empiece por aquí», «Cómo funciona», «la página se lo dice», «Mueva los controles», «vea qué pasa», «¿Qué significa?»).
- **Sin jerga** ni nombres de columna en snake_case en pantalla: las tablas pasan por `tabla_legible`. **Sin términos internos**: nada de nombres de archivo (.csv, .json), «pliegue», «fold», «OOF», «brazo A/B/C» ni «Fuera de pliegue» (una prueba recorre las ocho páginas y las seis pestañas de Validación). Un «%» no se separa de su número entre dos líneas (espacio de no separación). Se evita «recall» como titular: se dice «unas 70 de cada 100 cajas sin pareja».
- **Términos definidos** en «Ayuda y glosario» (tabla de dos columnas): caja, par 2D, celda, hueco, cola, presupuesto, cobertura, intervalo de confianza, post hoc, en muestra, sin prueba ciega.
- Las celdas que marca el detector se llaman **celdas marcadas** (DEV-3), nunca «falsas alarmas».
- Toda cifra del flujo en dos pasos dice «en muestra» en su propia oración o nota (sin etiqueta aparte); el supuesto de 20 s por caja se dice siempre como supuesto.
