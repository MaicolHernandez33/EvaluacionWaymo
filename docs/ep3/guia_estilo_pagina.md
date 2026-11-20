# Guía de estilo de la página

*Generada por `scripts/ep3/generar_guia_estilo.py` desde `app/estilos.py` y `src/waymo_evaluacion/ep3/app_logica.py`. Las pruebas `tests/ep3/test_pagina_rediseno.py`, `tests/ep3/test_pagina_pulido.py` y `tests/ep3/test_pagina_f20.py` y `tests/ep3/test_pagina_f22.py` exigen el contraste, que el tema de Streamlit use estos tokens y las reglas de gráficos, tablas y textos de abajo.*

## Producto y marco (F20)
- **Nombre:** Auditor de etiquetas 3D (neutro: no usa la marca ni el logo de Waymo; la fuente de datos solo se cita en el pie: «Waymo Open Dataset v2, uso académico»). Aparece **una sola vez**, en el wordmark de la barra lateral (SVG propio e inline, sin URL, con la versión de la solución debajo).
- **Descripción:** Revisión priorizada de cajas 3D de peatones y ciclistas sin par 2D.
- **Ícono de la pestaña:** `app/assets/icono.png`, dibujado por `scripts/ep3/generar_icono_pagina.py`.
- **Navegación** (`st.navigation` con páginas de archivo en `app/paginas/`; 8 páginas agrupadas):
- **Revisión:** Resumen, Cola de revisión, Explica una caja
- **Calidad de datos:** Auditoría de cámaras
- **Análisis:** Validación
- **Herramientas:** Puntuar datos nuevos
- **Ayuda:** Ética y límites, Ayuda y glosario
- **Rol** (selector discreto al pie de la barra lateral, etiqueta «Rol»; 3 roles): cambiar de rol lleva a la página que sugiere y ordena primero su alerta en el Resumen. Sin píldora de perfil en el encabezado.
- **Encabezado de página:** título pequeño (1.65rem, no un H1 enorme), una línea de descripción y, a la derecha, **un solo chip de estado** «Datos de desarrollo · sin validación externa» (alineado al **borde derecho del área de contenido** en todas las páginas, también con descripciones de dos líneas y en modo presentación) que abre un popover con el texto completo de «en muestra». Es el que cumple la visibilidad exigida por DEC-14: no hay banners ámbar por pantalla ni acordeones «¿Qué significa?». Además, cada cifra del flujo en dos pasos lleva una etiqueta pequeña «en muestra».
- **Pie único:** versión de la solución, fuente de datos y «Datos de desarrollo». «Nada se guarda ni se envía» aparece solo en Ayuda y Ética.

## Paleta (tokens)
Dirección «mesa de luz de sensores» (F22, DEC-82): barra lateral de tinta oscura, lienzo gris azulado muy claro con tarjetas blancas elevadas, **cobalto** como acento principal y **verde azulado** para lo sano. El color semántico sigue reservado: **rojo = hueco**, **ámbar = etiqueta «en muestra»**. Bordes de 1 px, radio de 10px en contenedores y 8px en controles, sombra suave de dos capas solo en lo elevado (`0 1px 2px rgba(15, 27, 45, .06), 0 6px 16px rgba(15, 27, 45, .05)`); sin bordes superiores de color y sin píldoras. Apta para daltonismo: el rojo de los huecos nunca va solo (siempre con contorno grueso y una «X», en el mapa y en el anillo, y con texto), y las celdas sanas usan una escala de un solo tono (verde azulado).

| Token | Valor | Uso |
|---|---|---|
| `primario` | `#2457D6` | acento principal (cobalto): títulos de página, enlaces, selección, barras de datos y cámara activa del anillo |
| `primario_oscuro` | `#1B3F9E` | texto sobre el fondo de apoyo del cobalto y títulos de las fichas |
| `primario_fondo` | `#E8EEFC` | fondo de apoyo del cobalto: resultado de la cola, filas con el cursor y botones en hover |
| `texto` | `#14202F` | texto principal |
| `texto_suave` | `#4B586B` | texto secundario, notas y encabezados de tabla |
| `fondo` | `#F6F8FB` | lienzo de la página |
| `superficie` | `#EAEFF6` | controles, encabezados de tabla y paneles tenues |
| `tarjeta` | `#FFFFFF` | tarjetas elevadas (métricas, fichas, paneles, tablas) |
| `borde` | `#D8E0EB` | bordes de 1 px y separadores (decorativo) |
| `sano` | `#0B6B74` | verde azulado: celdas con pareja (escala del mapa) y cuñas sanas del anillo |
| `sano_fondo` | `#E3F3F4` | fondo de apoyo del verde azulado |
| `tinta` | `#0F1B2D` | fondo de la barra lateral |
| `tinta_2` | `#1B2D4A` | elemento activo y controles de la barra lateral |
| `tinta_texto` | `#E8EEF7` | texto de la barra lateral |
| `tinta_suave` | `#A8B7CC` | texto secundario y etiquetas de la barra lateral |
| `tinta_acento` | `#8DB0FF` | cobalto claro sobre la tinta: selección y foco en la barra lateral |
| `aviso_fondo` | `#FFF4D6` | SOLO la etiqueta «en muestra» y el chip de estado |
| `aviso_texto` | `#5C3D00` | texto de la etiqueta «en muestra» y del chip |
| `aviso_borde` | `#C98A00` | borde de la etiqueta «en muestra» y del chip (decorativo) |
| `hueco` | `#B42318` | SOLO huecos de cámara (rojo): contorno con X en el mapa y en el anillo, y cifra de celdas marcadas |
| `hueco_fondo` | `#FDECEA` | fondo de apoyo del rojo de hueco |

## Contraste (WCAG, mínimo 4,5:1 en texto)
| Par | Razón | Estado |
|---|---|---|
| texto sobre fondo | 15,45:1 | cumple |
| texto sobre tarjeta | 16,44:1 | cumple |
| texto sobre superficie | 14,23:1 | cumple |
| texto_suave sobre fondo | 6,79:1 | cumple |
| texto_suave sobre tarjeta | 7,22:1 | cumple |
| texto_suave sobre superficie | 6,25:1 | cumple |
| primario sobre fondo | 5,79:1 | cumple |
| primario sobre tarjeta | 6,16:1 | cumple |
| primario sobre superficie | 5,33:1 | cumple |
| primario_oscuro sobre primario_fondo | 8,02:1 | cumple |
| primario sobre primario_fondo | 5,30:1 | cumple |
| tarjeta sobre primario | 6,16:1 | cumple |
| sano sobre tarjeta | 6,23:1 | cumple |
| sano sobre sano_fondo | 5,46:1 | cumple |
| tinta_texto sobre tinta | 14,82:1 | cumple |
| tinta_suave sobre tinta | 8,49:1 | cumple |
| tinta_texto sobre tinta_2 | 11,84:1 | cumple |
| tinta_suave sobre tinta_2 | 6,78:1 | cumple |
| tinta_acento sobre tinta | 8,06:1 | cumple |
| aviso_texto sobre aviso_fondo | 9,03:1 | cumple |
| hueco sobre tarjeta | 6,57:1 | cumple |
| hueco sobre fondo | 6,18:1 | cumple |
| hueco sobre hueco_fondo | 5,75:1 | cumple |

## Tipografía y espaciado
- Pila del sistema con «Segoe UI Variable Text» y «Segoe UI» primero: `"Segoe UI Variable Text", "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif`. **Sin fuentes externas, sin CDN, sin imágenes remotas:** una prueba falla si algún archivo de `app/` contiene `http://` o `https://` (la única excepción es la declaración de espacio de nombres del SVG propio).
- Cifras con `font-variant-numeric: tabular-nums`. Escala: cuerpo 15 px; títulos con peso 680 y tracking ligeramente negativo; título de página 1.65rem; cifras de las métricas 1.75rem; tablas compactas (filas de 30 px); modo presentación multiplica la letra por 1,18.
- Espaciado: xs = 0.25rem, s = 0.5rem, m = 1rem, l = 1.5rem, xl = 2rem (se aplican como márgenes y separaciones).
- Estados **hover** y **foco** visibles (contorno de 2 px en cobalto; en la barra lateral, en cobalto claro) en botones, enlaces de la navegación y controles. **Transiciones de 150 ms** (`--t`) en botones, enlaces de la navegación, selectores, filas y pestañas; el único movimiento propio es la aparición del panel de detalle de la cola (240 ms), que responde a elegir una fila. `prefers-reduced-motion` lo apaga todo.

## Componentes
- **Métricas** (`aud-metrica`): franja de 4 cajas compactas de la misma altura (etiqueta, cifra de 1.75rem, nota), con un glifo de estado a la izquierda (caja en cobalto; caja con una X en rojo para huecos) y sombra suave. En modo presentación van 2 x 2 (nunca una tarjeta huérfana).
- **Etiqueta «en muestra»** (`aud-muestra`): pequeña, ámbar, junto a cada cifra del flujo en dos pasos.
- **Filas de alerta** (`aud-fila`): punto de color de estado, título, texto y, **en la misma fila**, el enlace a la sección (cada alerta vive en su contenedor con clave y el enlace se centra con su texto; se mide en las capturas: diferencia menor de 5 px).
- **Ficha** (`aud-ficha`): tarjetas de título pequeño y texto, en dos columnas (Ética y límites).
- **Anillo de cámaras** (`aud-anillo`, `E.anillo_camaras`): la pieza propia de la página. Un vehículo visto desde arriba con una cuña por cámara (1 frontal, 2 frontal izq., 3 frontal der., 4 lateral izq., 5 lateral der.; atrás no hay cámaras). Estados: **sana** (verde azulado), **hueco** (contorno rojo grueso y una «X»), **activa** (cobalto sólido: la cámara que ve la caja elegida) y **apagada** (gris). Aparece en el Resumen y en la Auditoría (celdas marcadas por cámara, desde la Lista A), en el detalle de la caja y en los estados vacíos. SVG inline con texto alternativo; no agrega cifras: solo dibuja los datos de la Lista A.
- **Estados vacíos** (`aud-vacio`): un dibujo, qué falta y qué hacer. Panel de detalle de la cola sin fila, cola sin cajas tras filtrar («Ninguna caja cumple los filtros») y «Puntuar datos nuevos» sin archivos. El cargador de archivos tiene una zona de arrastre con borde punteado en cobalto claro.
- **Resultado** (`aud-resultado`): la frase principal de la cola, con ambos flujos.
- **Tablas HTML** (`aud-tabla`) para textos largos (glosario): dos columnas, el texto se ajusta a la celda; las tablas de datos son `st.dataframe` compactos con el ancho de cada columna **calculado** con su encabezado y su contenido (`formato.anchos_columnas`, con 5,6 px por carácter de encabezado y 5,5 de contenido, medidos sobre las capturas), de modo que ningún encabezado queda cortado. «Tipo de caso» no lleva ancho fijo y absorbe el espacio sobrante.

## Gráficos y mapas
- **Tema único de los gráficos** (`_grafico` en `app/secciones.py`): rejilla fina (`#E3E9F1`), sin línea de eje ni marcas, etiquetas en gris suave, sin marco, barras con el extremo redondeado (4 px) y la misma tipografía de la página.
- **Mapa de calor de la Auditoría** (escala de un solo tono verde azulado, de casi blanco = 0 % a verde azulado oscuro = 100 %), dentro de un contenedor de altura fija con desplazamiento y **una sola leyenda** en palabras (`leyenda_mapa`). Tiene **tres estados que no se confunden**:
  1. celda con datos suficientes: verde azulado según la proporción de cajas con pareja;
  2. **«Sin cajas o menos de 100 en el rango»**: gris con rayado diagonal; significa «no se evalúa» y **no es lo mismo que una tasa de 0 %**;
  3. **hueco**: contorno rojo grueso con una «X» (el rojo nunca va solo).
  Las etiquetas de segmento son los **últimos 6 dígitos** (el id completo va en el tooltip); por defecto los segmentos con celdas marcadas van primero y se puede ver solo las celdas con datos suficientes.
- **Curvas de la cola**: la línea lleva el color **y** el trazo (no solo el color), la banda sombreada es del mismo color con transparencia, y la leyenda sale de las líneas y lista solo las curvas dibujadas. Regla técnica: la banda no codifica el campo «nombre» (Vega-Lite fusionaría las leyendas y borraría la de las líneas), así que hay una banda por curva con color fijo.
- **Impacto estimado** (Resumen): barras horizontales de horas para encontrar el 80 % (sin orden, solo cola, auditoría + cola); la tercera lleva «en muestra». Debajo, una nota sin nombres de archivo («Estimación en muestra: cajas × fracción para el 80 % × 20 s por caja (supuesto, no medido)») y un popover «Fuente» con la referencia al informe. **«en muestra» aparece a lo más dos veces por pantalla** (la etiqueta de la barra y la nota; el chip lo guarda en su popover).
- **Explica una caja**: los puntos se eligen con `select_slider` en una **escala no lineal** (0, 1, 2, 5, 10, **11** = punto B, 20, **32** = punto A, 50, 60, 100 a 2.000), porque casi todas las cajas tienen pocos puntos; el gráfico usa una escala comprimida (`symlog`) con líneas finas en el punto B (11) y el punto A (32). Cada control dice qué mueve: «(este control mueve la probabilidad)» solo en los puntos del sensor superior; los puntos del LiDAR y la distancia dicen «(solo afecta al tipo de caso)» y la clase «(solo agrega la advertencia de ciclista)». El puntaje se lee «Puntaje: -50 (menos los puntos del sensor superior)», nunca «-50,000». Un bloque «Cómo se calcula» de tres líneas, sin nombres internos. Los tres ejemplos van en una sola fila.
- **Validación** (seis pestañas): cada una abre con un gráfico de los resultados guardados de EP3 (barras con intervalo de confianza, puntos con intervalo y por partición, tasa por tipo de caso, flujos de uno y dos pasos con su valor sobre la barra) y deja la tabla completa en un solo expander; el eje usa coma decimal, sin etiquetas repetidas (marcas calculadas por `_marcas_eje`), con leyendas completas y barras sin superponer. «Selección» muestra el cuadro O1 a O4 y los resultados de la solución elegida **sin columna de archivos** (la fuente va en una línea: informe técnico, sección 12 y anexo B).

| Curva | Color | Trazo | Contraste sobre blanco |
|---|---|---|---|
| Dos pasos | `#2457D6` | continuo | 6,16:1 |
| Un paso | `#B45309` | discontinuo (trazo 7, hueco 4) | 5,02:1 |
| Regla de puntos, un paso | `#6B7280` | discontinuo (trazo 2, hueco 3) | 4,83:1 |
| XGBoost (referencia) | `#0B6E69` | discontinuo (trazo 4, hueco 2) | 6,09:1 |
| Ensamble E2 (referencia) | `#7C3AED` | continuo | 5,70:1 |

## Tablas
- **Cola de revisión (maestro-detalle):** `st.dataframe` con selección de una fila (`on_select="rerun"`); al elegirla se abre un **panel de detalle debajo de la tabla, a todo el ancho** (dos columnas internas: la explicación y los datos de la caja). Se eligió debajo y no a la derecha porque a 1366 px un panel lateral deja la tabla en unos 700 px y corta «Tipo de caso» y «Segmento»; debajo la tabla usa los 1.062 px y las nueve columnas se ven sin desplazamiento. Sin fila elegida, el panel explica qué trae el detalle. **Orden de columnas:** Posición, Prob. sin pareja, Puntos sensor sup., Clase, Fotogramas, Cámara, Tipo de caso, Distancia, Segmento (después, los identificadores). **Nota del empate** sobre la tabla, calculada de la cola: «Las primeras N cajas empatan (0 puntos del sensor superior; …); el orden entre ellas no es informativo»; desaparece si no hay empate. La columna **Prob. sin pareja** (probabilidad calibrada, en %) reemplaza a la antigua barra «Prioridad», que quedaba saturada en 100.
- **Fotogramas** (`Fotogramas`): un mismo objeto aparece en varios fotogramas y cada uno es una caja distinta de la cola; la vista «Agrupar por objeto» deja una fila por objeto sin cambiar el conteo de cajas a revisar.
- **Formatos (es-CL) de `tabla_legible`**: enteros sin decimales («3», «1.600»), proporciones como porcentaje, el parámetro de regularización C en notación científica («1,0e-5»), nombres legibles de hiperparámetros y valores en español («Partición» o «En validación cruzada por segmentos», nunca «Fold», «pliegue» ni «Fuera de pliegue»); nunca una columna con dos escalas distintas mezcladas («20» junto a «1.600» es lo esperado; «20,000» junto a «1.600» no) ni «-0,000».
- **Controles**: sin decimales con punto (la distancia de «Explica una caja» va de 1 en 1 m).

## Cargador de archivos
Los textos propios de Streamlit («Drag and drop…», «Browse files», «500MB per file») no se pueden cambiar por configuración: se ocultan con CSS y se muestra el texto en español («Arrastre el archivo aquí · Parquet, hasta 500 MB», botón «Elegir archivo»). Riesgo: depende de los `data-testid` de Streamlit 1.65. Los cargadores se rotulan «Archivo 1 (obligatorio)» y «Archivo 2 (opcional)» (sin tarjetas numeradas).

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
- Toda cifra del flujo en dos pasos lleva la etiqueta «en muestra»; el supuesto de 20 s por caja se dice siempre como supuesto.
