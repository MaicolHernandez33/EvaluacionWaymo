# Reporte F34 y F35: Validación y Puntuar datos nuevos

Escrito para: la persona que pidió el rediseño y decidirá qué queda. Fecha: 2026-11-23. Los HTML de referencia están en `docs/referencias_diseno/`. Las cifras de este reporte salen de la página con los datos reales (41 segmentos de desarrollo, en muestra,
sin validación con datos nuevos) y de los archivos `docs/ep3/f34_*.json` y `f35_*.json`. F31 a F33 estaban aplicadas y no se tocaron (salvo dos arreglos de pruebas y de un script de captura, listados abajo).

## Qué decidir (resumen corto)
1. **Ámbar.** La maqueta pintaba de ámbar las etiquetas «En muestra» y «Sin validación con datos nuevos»; la regla de F25 reserva el ámbar para advertencias reales. Dejé esas dos etiquetas neutras y el ámbar solo como punto en «Ciclistas: regla poco confiable» y en los avisos con punto (el de O4 y el de «En muestra», que el prompt pidió ámbar). ¿Está bien así, o prefiere el ámbar de la maqueta?
2. **Tono.** Las maquetas hablan de «tú» («Sube un segmento», «¿Solo quieres ver cómo funciona?»); la página habla de «usted» y una prueba prohíbe verbos en imperativo. Puse «¿Solo desea ver cómo funciona?» y un subtítulo impersonal. ¿Se mantiene?
3. **Columnas que quedan solo en el CSV.** Para que ninguna tabla se salga de la pantalla, las columnas que no caben (por ejemplo medianas de los grupos, o la marca de tiempo y el identificador de objeto de la cola de Puntuar) van solo en la descarga, y el pie de cada tabla dice cuántas. La regresión de cifras comprueba que nada se perdió. ¿Se acepta, o prefiere ver más columnas con desplazamiento horizontal?
4. **El ejemplo de Puntuar no tiene celdas marcadas.** El segmento de ejemplo de la app (911012534050, el primero de la lista de celdas marcadas) se puntúa sin archivo 2, así que no puede mostrar celdas marcadas; la maqueta mostraba otro segmento con una celda. Las tarjetas lo dicen en vez de inventar cifras. Si quiere un ejemplo con celdas marcadas habría que reconstruir también el archivo de asociación, y eso sí sería inventar a qué cámara pertenece cada caja.
5. **Límite de subida.** Al lanzar desde la raíz, el límite real era 200 MB aunque la página decía 500 (hallazgo); lo dejé en 500 en la configuración de la raíz. Si prefiere mantener 200 MB, hay que cambiar el texto de la página.

## Conteos de pruebas (`python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider`)
| Momento | Pruebas de EP3 | Resultado |
|---|---|---|
| Antes de F34 (después de F31 a F33) | 330 | 330 pasadas |
| Después de F34 (+19 en `test_pagina_f34.py`) | 349 | 349 pasadas |
| Después de F35 (+18 en `test_pagina_f35.py`) | **367** | **367 pasadas, 0 falladas** (corrida completa final) |

Se adaptaron (sin borrar ninguna) las pruebas de F20, F21, F22, F23, F24, F26, F27, F29, F30, pulido y rediseño a los textos y la estructura nuevos. `pytest` sin ruta no se ejecutó. Verificado también: congelados de EP2 14 de 14, v3 5 de 5, sello `--etiqueta f34` y `--etiqueta f35` intactos.

## F34 · Validación
**Qué cambió.** Cabecera con el **veredicto calculado**, cuatro tarjetas (AUC con su intervalo, cajas analizadas con su % sin pareja, casos encontrados en peatones y en ciclistas; mismas fuentes que el Resumen) y tres etiquetas. **Cinco pestañas** (Modelo elegido, Generalización, Alternativas, Tipos de caso, En muestra) con la misma plantilla
(lectura sin tocar → un gráfico → puntos clave → «Tablas de apoyo (N)» cerradas, con un sub-desplegable por tabla). Modelo elegido: tarjetas O1 a O4 con «✓/✕ X de N» y el aviso de O4. Generalización: línea del AUC mínimo por partición (del plan v3), partición más débil rotulada y fila de la regla resaltada, con dos puntos clave calculados.
Alternativas: hiperparámetros (estado en texto al final de cada fila, aviso de bordes de grilla) y ensambles (valor y veredicto en texto). Tipos de caso: gráfico con valor y número de cajas, y tres puntos clave. En muestra: aviso, lectura, impacto estimado, el bloque nuevo «De dónde viene la mejora de la auditoría» y el gráfico con valores sobre las barras y el nombre del flujo debajo de cada valor.
Un solo componente de tabla para todas (ver «Estándar de tablas»). Teclas izquierda y derecha cambian de pestaña (comprobado en el navegador real).
**Qué no se pudo / diferencias con el HTML.**
- Los rótulos «En muestra…» y «Sin validación…» son neutros (decisión 1) y las etiquetas no tienen forma de píldora (una prueba de F20 prohíbe esos radios); tampoco uso peso 700 ni degradados lineales (pruebas de F23): las sombras de borde de las tablas usan degradados radiales y cónicos.
- La maqueta repite «Cifras aproximadas» en gráficos (los valores del gráfico de hiperparámetros y la posición de los rombos eran leídos de una captura): los gráficos de la página usan los datos reales.
- En la maqueta el nombre del flujo iba solo en la leyenda; aquí va además en texto sobre cada barra (el color no es lo único). El texto está alineado al borde izquierdo de la barra y no centrado (Altair 6 no permite centrar texto en barras agrupadas); es legible pero no es perfecto.
- «Tablas de apoyo» tiene más tablas que en la maqueta (5, 5, 3, 7 y 6) porque no se eliminó ningún análisis (decisión: cada tabla vive en la pestaña de su análisis).
- «Candidatos» (qué es cada uno) es una tabla de apoyo más de «Modelo elegido».
**Decisiones.** DEC-130 a DEC-135 en `ESTADO.md`.

### La regla de «mejora» de hiperparámetros (la pedida en el punto 6)
La app no la calculaba: leía la columna `veredicto` de la evidencia. Esa columna la produce `scripts/ep3/f3_analisis.py`: **«mejora» si el cambio de PR-AUC es de al menos 0,010 (plan v3, P5) y el límite inferior del intervalo pareado por segmentos queda sobre 0**. Se dice bajo el gráfico y una prueba comprueba que los 5 veredictos guardados cumplen esa regla (XGB y LGBM mejoran; LR, RF y HGB no).

### Investigación del ARI 0,007932 (EP3) frente a 0,997 (EP2)
**No se cambió el valor y no es un error de presentación.** Evidencia: (1) `data/08_reporting_ep3/f13_ari_diagnostico.json` (lo produce `scripts/ep3/f13b_diagnostico_ari.py`): las tres técnicas se comparan sobre las mismas 15.000 filas distintas y el ARI recalculado coincide exactamente con el de `f13_resumen.json` (0,007932166… con k = 2); todos los GMM convergieron.
(2) El informe técnico de EP3 («Diagnóstico del ARI bajo») muestra que KMeans coincide con el GMM esférico (ARI 0,884) y con el diagonal (0,729); **el discrepante es el GMM de covarianza completa**, que parte la muestra en 70 % y 30 % mientras KMeans la parte en 47 % y 53 %; por eso el ARI KMeans contra GMM debe leerse con los otros. (3) EP2 usó otras variables (con oclusión) y 33 segmentos; la diferencia es una hipótesis, no verificada, post hoc.
En pantalla se muestra 0,008 (3 decimales como las otras cifras de la tabla) con una nota que lo explica; la descarga trae 0,00793217 (la copia de la evidencia de la página redondea a 8 decimales; el valor completo está en `f13_resumen.json`).

### Estándar de tablas
Un componente (`app/tablas.py` + `src/waymo_evaluacion/ep3/tablas_estandar.py`) para las 26 tablas de Validación y las de Puntuar: sin desplazamiento vertical interno (hasta 25 filas todas; más, de 25 en 25; la cola de Puntuar, de 50 en 50); intervalos en una columna; encabezados cortos con `title`; números a la derecha con cifras tabulares; decimales fijos por tipo
(AUC, PR-AUC, Brier y diferencias con 3; porcentajes con 1; recuentos con punto de miles); «−» único y «+» en diferencias positivas; tildes corregidas («máximo», «mínimo», «atípicas»), «sin pareja» en lugar de `sin_camara` y `n_init` sin romper; título, «Responde: …», conteo de filas y «Descargar CSV» con todas las columnas sin redondear; primera columna fija y sombras de borde si hay más columnas.
«Ver tabla completa» ya no existe y el recuadro de foco solo aparece con el teclado (medido en el navegador: tras un clic, sin contorno; con Tab, contorno de 2 px). El encabezado no tapa la primera fila (se ve en `f34_09` y `f34_10`). Una excepción de redondeo: «Equilibrio» se muestra truncado (6.059, igual que las tarjetas de otras páginas); el CSV trae 6059,5.

### Regresión de cifras (regla 6)
Línea base: `scripts/ep3/f34_exportar_valores.py` exportó, antes de cambiar nada, las 26 tablas tal como las daba `tabla_legible` (4.450 celdas), los datos de cada gráfico, las lecturas, los resultados clave y las cifras del Resumen (copia fuera del repositorio en el directorio temporal de la sesión y copia en `tests/ep3/datos_f34/` para la prueba). Resultado de `test_regresion_de_cifras…`: **0 números perdidos**: cada número de antes se ve igual en la tabla nueva o está sin redondear en su CSV
(las tablas con más columnas de las que caben); mismas filas por tabla; los datos de los gráficos, las lecturas y los 5 resultados clave son idénticos. Cambios de formato conocidos: porcentajes antes en decimales (0,619 → 61,9 %), identificadores de segmento de 12 dígitos → «…534050» y las curvas de validación (175 filas) solo en descarga.

### Cifras entre páginas (regla 9, `f34_cifras_cruzadas.json`)
Todas salen de las mismas funciones y no hay discrepancias ni cifras sin aparecer. Dónde aparecen: AUC 0,823, 80.571 cajas, 358/200/132 h, 61,9 % y 44,6 %/29,6 % solo en Validación; 21,2 % en el Resumen y en Validación; peatones 80,6 % y ciclistas 44,3 % en la Cola y en Validación. No hay una cifra distinta de la de su función en ninguna página.

### Candidatos y vistas con su descripción (punto 10)
Fuente: `docs/ep3/plan_v3.md` (P6), `src/waymo_evaluacion/ep3/candidatos.py` y `datos.py`. «vista obs/tam/pos» se muestran como «vista de observación», «de tamaño» y «de posición».
- **E1:** ensamble de voto suave de LR, RF y HGB (plan P6, candidatos.py).
- **E2:** promedia los rangos de E1 y de la regla de puntos del sensor superior (plan P6).
- **E3:** apilamiento (stacking) de LR, RF, HGB, XGB y LGBM con una regresión logística final entrenada con predicciones fuera de partición (GroupKFold de 3 por segmento) (plan P6).
- **E4:** apilamiento de tres vistas (observación, tamaño y posición): un modelo por vista y una regresión logística final (plan P6, candidatos.py).
- **LR3:** regresión logística con 3 variables: puntos del LiDAR, puntos del sensor superior y azimut (`datos.py`, V_MIN3).
- Vista de observación: puntos del LiDAR, del sensor superior, densidad y distancia (V_OBS); de tamaño: largo, ancho, alto, volumen, si es ciclista y velocidad (V_TAMANO); de posición: centro, azimut, distancia y rumbo (V_POSICION).
- LR, RF, HGB, XGB y LGBM: nombres de los algoritmos con «las 16 variables por defecto» (candidatos.py, BASE).
Ninguno quedó sin descripción.

### Enlaces a pestañas (regla 10)
Ninguna página enlaza a una pestaña de Validación (Streamlit no admite enlaces profundos a una pestaña); `test_cada_pestana_nombrada_en_un_texto_existe` comprueba que todo texto que nombre una pestaña usa uno de los cinco nombres vigentes. No hay enlaces que actualizar.

## F35 · Puntuar datos nuevos
**Qué cambió.** Subtítulo nuevo (impersonal) y dos etiquetas («Procesamiento local y en memoria»; en la variante de servidor, «…en el servidor y en memoria» para no decir algo falso, y «No se guarda nada»). Tres pasos arriba con el actual marcado y los hechos con ✓. Archivo 1 con botón destacado («Elegir archivo»), archivo 2 con su etiqueta «opcional» y su línea; el ejemplo es un botón secundario junto a «¿Solo desea ver cómo funciona?».
Estado vacío corto con el anillo neutro. Con un segmento puntuado la página muestra solo el resultado: encabezado con el identificador («Segmento …534050», «ejemplo de desarrollo» si corresponde), «Cargar otro segmento» y «Descargar resultados (CSV)», tarjetas, «Celdas marcadas» con el anillo y su tabla, «Cola de cajas de este segmento» (50 por página, columnas de la Cola de revisión) y «Resumen del cálculo» plegado.
**Qué no se pudo / diferencias con el HTML.**
- Sin archivo 2 no existen celdas marcadas ni cajas sin pareja: las tarjetas son «Celdas marcadas —», «Cajas puntuadas» y «Cajas en la cola» (decisión 4). Con archivo 2: «Celdas marcadas X de N» (N = celdas segmento × cámara evaluadas), «Cajas afectadas» y «Sin pareja en esas celdas».
- «Descargar resultados (CSV)» entrega **un .zip con las dos listas en CSV** (el mismo contenido de las dos descargas de antes); además cada tabla tiene su «Descargar CSV» (la Lista A de las celdas; la Lista B completa de la cola). Elegí el zip para cumplir «un solo botón» sin mezclar dos tablas distintas en un CSV.
- Si el archivo supera 500 MB, el selector de Streamlit lo rechaza antes que nada y su mensaje está en inglés (no se puede traducir); la página tiene su propio mensaje en español para ese caso y dice el límite junto al selector. No probé un archivo real de más de 500 MB (probé el mensaje y la configuración).
- Con un segmento puntuado, los selectores de archivo desaparecen (la maqueta hace lo mismo): la página se vuelve a ejecutar una vez al terminar el puntaje.
**Decisiones.** DEC-136 y DEC-137.

### Texto real del archivo 2 (punto 3)
Comprobado en `inferencia.puntuar_segmento`: sin el archivo 2 se puntúan y ordenan igual todas las cajas, pero no se buscan huecos de cámara (no hay celdas marcadas ni cajas apartadas de la cola) y no se conoce cuáles cajas ya tienen pareja (no hay cifras de cajas sin pareja). Texto que puse: «camera_to_lidar_box_association · formato parquet, hasta 500 MB. Sirve para buscar huecos de cámara y conocer cuáles cajas ya tienen pareja; sin este archivo se puntúan y ordenan igual todas las cajas, pero no hay celdas marcadas ni cifras de cajas sin pareja.» (La suposición de la maqueta, «Sirve para marcar huecos de cámara», era incompleta.)

### «No se guarda nada» (punto 1)
Comprobación: (a) en el código de la página, de la tabla y de `puntuar.py` no hay escrituras a disco ni cachés persistentes (`st.cache*`, `lru_cache`, `pickle`, `tempfile`, `shutil`, `write_*`, `to_parquet`); (b) durante un puntaje real con el ejemplo no se abre ningún archivo para escribir (prueba con un espía de `open`); (c) los archivos subidos se leen con `pd.read_parquet(io.BytesIO(...))` y el CSV se arma en memoria. Lo que sí existe: el segmento puntuado
queda en la memoria de la sesión mientras se mira (`_pt_vista`), y «Cargar otro segmento» lo suelta; los archivos subidos los tiene Streamlit en memoria mientras el selector está en pantalla. La etiqueta es cierta con esa precisión; si prefiere una frase más exacta («Nada se escribe a disco»), es un cambio de texto.

### Elementos de Puntuar con resultado que existían y la maqueta no trae
Se conservaron: las advertencias de la puntuación (por ejemplo «sin archivo de asociación…», ahora con «sin pareja» en lugar de `sin_camara`), la nota de que el ejemplo se reconstruye de variables derivadas y no son datos crudos de Waymo, la tabla «Resumen» de medidas (ahora «Resumen del cálculo», plegada) con sus umbrales A y B, las cajas puntuadas y en la cola, la Lista A (celdas marcadas, mismas columnas y datos) y la Lista B completa (descarga). Cambiaron de lugar o de forma: las dos descargas pasaron a un zip y a un CSV por tabla;
la tabla de Lista B muestra 6 columnas (las de la Cola) y las otras (marca de tiempo, identificador de objeto, azimut, distancia, puntos del LiDAR, puntaje, posición) van en el CSV.

### Mensajes de error (punto 8, con archivos sintéticos en directorio temporal)
Archivo que no es parquet: «El archivo «x» no es un parquet válido o está dañado. Se espera un archivo en formato parquet.» · vacío: «…está vacío (0 bytes).» y sin filas: «…no tiene filas: está vacío.» · columnas que faltan: se dicen todas (antes «y otras») · más de 500 MB: «…pesa N MB y el máximo es 500 MB…» · archivo 2 que no corresponde: «El archivo 2 no corresponde al archivo 1: ninguno de sus segmentos aparece en el archivo 1 …» (o «comparten segmento, pero ninguna caja del archivo 2 está en el archivo 1»). Se muestran con el estilo de aviso de la app; ninguno muestra un traceback. Pruebas en `test_pagina_f35.py`.

### Prueba de escala (`f35_escala_sintetica.json`)
Con un parquet sintético de 100.000 cajas (9,8 MB; 90.044 puntuadas) y su archivo 2: leer 0,07 s, validar la correspondencia 0,08 s, **puntuar 6,8 s**, preparar la cola y formatear la primera página 0,1 s; **total 7,1 s**; la página muestra 50 filas por vez (la cola tiene 595 filas con esos datos aleatorios). Con un segmento de tamaño real (2.000 cajas): 0,19 s en total. La cola se formatea solo para la página pedida (con 100.000 cajas no se formatean todas).

## Lugares donde el identificador de segmento tiene otro formato
Elegí «…534050» (los 6 últimos dígitos) para Validación y Puntuar, que es el que ya usaban el Resumen, la Auditoría, la Cola, el panel de detalle y el eje del mapa. Un barrido de las 8 páginas (`f34_barrido`, texto visible, tablas y expanders) no encontró ningún identificador de 12 dígitos en pantalla. Dónde sigue completo: los CSV (todas las descargas), el nombre interno de los selectores (el valor del filtro de segmento de la Cola) y los datos de evidencia.

## Solo informado (no se cambió)
- «Segmentos nuevos» sigue siendo el nombre del indicador del Resumen y cuenta los segmentos cargados.
- Los términos «Lista A» y «Lista B» ya no aparecen en ninguna página; quedan en comentarios del código y en los nombres `lista_A_nueva.csv` y `lista_B_nueva.csv` del zip.
- No hay textos de Ayuda y glosario que describan las pestañas antiguas de Validación ni el Modo presentación (barrido de las 8 páginas).

## Hallazgos corregidos de paso
- `maxUploadSize`: ver decisión 5.
- «sin_camara» aparecía como texto crudo en la advertencia de Puntuar y en tablas de Validación; ahora se muestra «sin pareja».
- `F.nombre_visible` ahora también convierte «vista obs/tam/pos» y `texto_visible` corrige tildes que faltaban en los datos.
- `f31_f33_capturas.py` ahora hace clic en el primer elemento **visible** (antes podía hacer clic en uno de una pestaña oculta). Se actualizaron `capturar_pagina.py` (claves de las 5 pestañas y de Puntuar) y las pruebas que contaban capturas por la numeración de F33 (13 por ancho).
- Contraste real final: 3.667 textos en 13 vistas, **0 por debajo de 4,5:1** (`f35_contraste.json`; mínimo en píxeles 5,67:1). Barra lateral a 1366 x 768: desborde 0 px. Ámbar de interfaz en Validación: 3 puntos (ciclistas, aviso de O4, aviso de «En muestra»), todos advertencias.
- Contraste y tamaño de las etiquetas dentro de las barras del gráfico de «En muestra»: una primera versión (texto girado de 11 px dentro de la barra) fallaba la medición (1:1 y menos de 12 px); se reemplazó por texto de 12 px claro sobre el fondo oscuro, encima de cada barra.

## Archivos tocados
**Código de la página:** `app/secciones.py`, `app/estilos.py`, `app/precarga.py` (sin cambios nuevos), nuevo `app/tablas.py`; `src/waymo_evaluacion/ep3/app_logica.py` (descripción de Validación, textos de entorno de Puntuar, validadores), `formato.py`; nuevos `validacion.py`, `tablas_estandar.py`, `puntuar.py`; `.streamlit/config.toml` (límite de subida).
**Pruebas:** nuevas `tests/ep3/test_pagina_f34.py` (19), `test_pagina_f35.py` (18) y `tests/ep3/datos_f34/valores_antes_validacion.json`; adaptadas `test_pagina_f20.py`, `f21`, `f22`, `f23`, `f24`, `f26`, `f27`, `f29`, `f30`, `test_pagina_pulido.py` y `test_pagina_rediseno.py`.
**Scripts:** nuevos `scripts/ep3/f34_f35_capturas.py`, `f34_exportar_valores.py`, `f34_cifras_cruzadas.py`, `f35_prueba_escala.py`; adaptados `capturar_pagina.py`, `f31_f33_capturas.py` y los generadores `generar_docs_ep3.py`, `generar_guia_estilo.py`, `generar_mapa.py`, `generar_pendientes_pagina.py`.
**Documentos:** escritos a mano `ESTADO.md` (DEC-130 a DEC-138) y `CLAUDE.md`; regenerados `informe_tecnico_EP3.md`, `README_EP3.md`, `guion_presentacion.md`, `preguntas_cruzadas.md`, `guia_estilo_pagina.md`, `PENDIENTES_PAGINA.md`, `MAPA_DE_ARCHIVOS.md`, `revision/`; este reporte; los dos HTML en `docs/referencias_diseno/`.
**Mediciones:** `docs/ep3/f34_cifras_cruzadas.json`, `f35_escala_sintetica.json`, `f34_f35_capturas.json`, `f35_contraste.json`, `f34_sello_despues.json`, `f35_sello_despues.json`.
**Imágenes:** `images/ep3/pagina/` (capturas a 1366 y 1920 px, 13 por ancho) y las 16 de `images/ep3/pagina/para_revision_f34_f35/`; la línea base de antes del rediseño está en `images/ep3/pagina/antes_f34/` (Validación en sus pestañas con y sin tablas abiertas, y Puntuar vacía y con el ejemplo). El estado de git completo está en `estado_git.txt` de la carpeta de revisión.
