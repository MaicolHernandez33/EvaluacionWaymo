# Reporte F31 a F33: Auditoría de cámaras, Cola de revisión y Explica una caja

Escrito para: la persona que pidió el rediseño y decidirá qué queda. Fecha: 2026-11-22. Los HTML de referencia están copiados en `docs/referencias_diseno/` (solo para mirar). Las cifras de este reporte salen de la página
con los datos reales (41 segmentos de desarrollo, en muestra, sin validación con datos nuevos) y de los archivos `docs/ep3/f3*_*.json`.

## Qué decidir (resumen corto)
1. **Orden de la Cola.** El orden nuevo (por la probabilidad que se muestra) no cambia qué cajas entran ni cuántas sin pareja contienen, pero **en esta muestra las primeras filas encuentran menos cajas sin pareja reales que el orden anterior** (en las primeras 100 filas: 76 contra 94). Ver «Orden de la Cola». ¿Se queda con el orden por probabilidad (coherente con la columna que ve) o vuelve al anterior?
2. **Flechas.** El prompt pidió «Explicar esta caja →», «Ir a la cola de revisión →» y «← Volver a …»; la regla de F23 prohíbe flechas. Las dejé solo en esos tres textos. ¿Se aceptan?
3. **Ningún ejemplo elegido al abrir «Explica una caja».** El HTML abre con uno elegido; la página sigue abriendo con los valores de siempre (50, 60, 25 m, peatón) para que la cifra registrada (10,1 %) no cambie. ¿Prefiere que abra con un ejemplo?
4. **«Explica una caja» ahora está en «Herramientas»** (antes en «2 · Priorización»). ¿Se queda ahí?

## Conteos de pruebas (`python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider`)
| Momento | Pruebas de EP3 | Resultado |
|---|---|---|
| Antes de F31 | 284 | verde |
| Después de F31 (+11 en `test_pagina_f31.py`) | 295 | verde |
| Después de F32 (+22 en `test_pagina_f32.py`) | 317 | verde |
| Después de F33 (+13 en `test_pagina_f33.py`) | **330** | **330 pasadas, 0 falladas** (corrida completa final) |

Los conteos de después de F31 y F32 salen de las pruebas agregadas por archivo (`pruebas_ep3_conteo.json` lista 11, 22 y 13); la corrida completa que quedó registrada es la final. Se adaptaron las pruebas de F20, F21, F23, F24, F25, F26, F27, F29,
pulido, rediseño y `test_app.py` a los textos y la estructura nuevos (no se borró ninguna). `pytest` sin ruta no se ejecutó (sigue vetado). Una prueba de tiempos (`test_tras_la_precarga_ninguna_seccion_tarda_mas_de_3_segundos`) es sensible a la carga
del equipo: pasó sola y en la corrida final; con la suite completa bajo carga falló una vez durante el trabajo.

## F31 · Auditoría de cámaras
**Qué cambió.** Titular «N posibles huecos de cámara en los últimos datos sin revisar» y definición breve; franja de indicadores (celdas, cajas afectadas, sin pareja; `resumen_auditoria`); una sola tabla «Celdas marcadas» (con «Descargar CSV»),
cuya fila elegida resalta su celda en el anillo «Celdas marcadas por cámara» y en el mapa; aviso de origen («Celda resaltada en el mapa: segmento …534050, cámara 5…»); mapa segmento × cámara con «Grupo de segmentos», «Orden» y «Solo celdas con datos suficientes»,
que empieza con 10 filas y agrega 50 por clic («Mostrar 50 más (N de M)»; con hasta 60 segmentos muestra todos) en orden de gravedad (`orden_gravedad`); leyenda en una línea; «¿Qué es un hueco?» plegado; botón «Ir a la cola de revisión →».
**Qué no se pudo / diferencias con el HTML.** No hay enlace «Ver detalle» en cada fila (la fila se elige con un clic y el detalle ya está al lado). Los números del HTML no se copiaron: salen de las funciones de la app.
**Decisiones.** DEC-122, DEC-123 (`ESTADO.md`). **Hallazgo.** La Auditoría y el Resumen leen la misma lista de celdas; «Auditar» del Resumen llega con la celda ya resaltada (verificado en el navegador real: `f29_navegacion.json`).

## F32 · Cola de revisión
**Qué cambió.** Plan de revisión arriba (flujo, presupuesto o meta, «Volver al 20 %»), que cambia las cifras de toda la página; tres tarjetas («Cajas a revisar», «Cajas sin pareja que se encuentran» con «en muestra» y la cifra del otro flujo debajo,
«Tiempo estimado» con «supuesto»); pestañas «Cola de cajas» (primera) y «Curva de priorización» con etiquetas directas, banda explicada, eje en porcentaje, marca en el presupuesto actual («Revisando el 20 %: 70 de cada 100 (dos pasos), 62 (un paso)», calculado) y «Comparar con»
como control pequeño; filtros de la lista (Segmento, Clase, Cámara, «Agrupar por objeto») que solo cambian la lista; tabla de 50 en 50 con selección y panel de detalle lateral con «Explicar esta caja →»; «Supuestos y confiabilidad» como desplegable al final
(20 s por caja como supuesto, cifras en muestra, ciclistas 44,3 % frente a 80,6 %).
**Diferencias con el HTML.** El filtro de segmento ya no mueve las tarjetas (el HTML decía que los filtros no cambian las cifras de arriba; antes el selector de segmento sí las cambiaba). El CSV descarga las filas filtradas (hasta 500) con todas sus columnas.
La tabla no tiene desplazamiento interno (la página pagina de 50 en 50: 315 páginas con la cola de 15.726 cajas).
**Decisiones.** DEC-124, DEC-127.

### Orden de la Cola (antes y después, `f32_orden_cola_antes_despues.json`)
El orden de la lista lo da `preparar_cola`: **reordena el mismo conjunto** que elige `cola_segmento` por (probabilidad calibrada, segmento, objeto, fotograma). Elegir el conjunto por probabilidad no se hizo porque cambiaría cuáles cajas entran (10.464 → 10.249 positivos con dos pasos y 20 %).

| Dos pasos, 20 % (15.726 cajas) | Orden anterior | Orden nuevo |
|---|---|---|
| Mismo conjunto de cajas | sí | sí |
| Cajas sin pareja en toda la lista | 10.464 | 10.464 |
| En las primeras 100 filas | 94 | 76 |
| En las primeras 500 filas | 490 | 406 |
| En las primeras 1.000 filas | 950 | 887 |
| En las primeras 5.000 filas | 4.452 | 4.524 |
| Probabilidad media de las primeras 1.000 filas | 86,3 % | 89,4 % |

Con un paso (16.115 cajas) el patrón es el mismo (94, 490, 950 y 4.458 antes; 76, 407, 888 y 4.525 después; 10.553 en total). Lectura: el orden nuevo ordena por la probabilidad que muestra la columna, así que es coherente y determinista; pero entre las 4.742 cajas empatadas en la prioridad máxima
(0 puntos del sensor superior, probabilidad 80,2 a 90,4 %) la probabilidad calibrada no separa mejor las cajas sin pareja reales que el orden en que venían los datos. El conjunto y las cifras de cobertura (70 y 62 de cada 100) no cambian. Es una decisión suya (arriba, punto 1); no es un efecto que se pueda asegurar fuera de esta muestra.

## F33 · Explica una caja
**Qué cambió.** Ejemplos como botones de selección (`st.pills`; «Caja cercana y densa», «Caja lejana con pocos puntos», «Ciclista lejano») con los valores exactos de siempre; «Datos de la caja» con **un solo control que decide** («Puntos del sensor superior», «decide la cola») separado de los que solo describen el tipo de caso
(«no cambia el lugar»: puntos del LiDAR, distancia y clase); resultado primero (probabilidad grande y veredicto «Se revisaría / No se revisaría con un presupuesto del N %», con el presupuesto y el flujo de la Cola); barra «Lugar en la cola»; «Cómo se calcula» en cuatro pasos con valores vivos;
gráfico con rótulos directos sobre las dos líneas finas (presupuesto actual y umbral para hallar el 80 % de las sin pareja) y el marcador «Esta caja: p %»; «Cajas parecidas» como tarjeta corta (tipo de caso, tasa, intervalo y número de cajas, nota post hoc); «Notas del modelo» plegado. Desde la Cola («Explicar esta caja →») y el Resumen («Abrir»)
se llega con los valores de la caja y el aviso «Valores cargados desde la Cola de revisión: caja X, prioridad N.» con «← Volver a la cola»; el aviso desaparece al mover un control. Menú: «Explica una caja» pasa a «Herramientas».
**Cifras de regresión (datos reales).** Por defecto: 10,1 %, lugar 59 %, «No se revisaría con un presupuesto del 20 %». Ejemplos: «cercana y densa» 2,8 % (lugar 89 %), «lejana con pocos puntos» 48,9 %. Con 0 puntos: 85,2 %, «Está entre las primeras 4.742 cajas», lugar «0 a 6 %».
**Diferencias con el HTML.** «Caja cercana y densa» muestra los valores reales (2,8 %) y no los del mockup; ninguna píldora elegida al abrir; el umbral del presupuesto es 10 puntos (de la cola de dos pasos al 20 %), no 11 (el 11 es el del artefacto B, un paso; el umbral A es 32). La etiqueta «Regla poco confiable» usa la constante de siempre.
**Decisiones.** DEC-125, DEC-126.

## Prueba con 300 segmentos sintéticos (`f31_f32_escala_sintetica.json`)
Datos generados en un directorio temporal (`escala_sintetica.py`; nada en `data/`): 300 segmentos, 12.000 cajas, 1.500 celdas, 22 marcadas. Tiempos con `AppTest` (ejecución del código de la página, sin dibujar en el navegador): carga de datos 0,10 s; primera carga de la app 1,9 s;
Resumen 0,06 s, Auditoría 0,31 s (primera vista) y 0,20 s (segunda), Cola 0,10 s (una tabla de 50 filas), Explica 0,09 s. Todas sin error; máximo 0,31 s. Es una medición del servidor de la página, no del navegador.

## Cifras que deben coincidir entre páginas (`f33_cifras_cruzadas.json`)
Todas salen de las mismas funciones (`resumen_cola`, `resumen_auditoria`, `kpis.json`) y cada página que las muestra lleva exactamente ese valor. Resultado: **15.726** cajas a revisar (Cola), **70 de cada 100** y **62 de cada 100** (Cola y su curva), **87,4 h** (Cola), **1.945** afectadas y **1.565** sin pareja (Auditoría),
**21,2 %** (indicador del Resumen), **78.626** cajas en la cola (Resumen y Cola), **4.742** cajas empatadas (Cola y Explica). No hay discrepancias. Ninguna página muestra hoy el 80,5 % (1.565 de 1.945): la Auditoría da los dos conteos y no el cociente; las cifras no se repiten en más de una página salvo las que se listan arriba.

## Respuesta: 300, 268 y 227 y «Grupo de segmentos»
- **300** = `cajas_en_rango`: todas las cajas (peatones y ciclistas) de la celda que caen en el rango de azimut de esa cámara; es el denominador de la tasa de cajas con par 2D (por eso «0 %» de 300 en la celda marcada).
- **268** = `cajas_afectadas_poblacion_principal`: de esas, las de la población principal (|azimut| ≤ 100°), es el `len(en)` de `scripts/ep3/f2_detector.py`; es la cifra «cajas afectadas» de la tabla y de la franja (1.677 de la otra celda + 268 = 1.945).
- **227** = `positivos_afectados`: de las 268, las que no tienen par en ninguna cámara (`sin_camara = 1`); 1.338 + 227 = 1.565.
- **Inconsistencia:** no hay contradicción, son tres conteos anidados con distinto denominador (300 ⊃ 268 ⊃ 227); lo que puede confundir es que el 300 incluye cajas fuera de la población principal y la página no lo dice. La franja y la tabla usan 268 y 227.
- **«Grupo de segmentos»** (selector del mapa): agrupa por `celdas["grupo"]`, que separa los segmentos de desarrollo de EP2 (`train`, 33) de los de test de EP2 (`test`, 8); «Todos» son los 41. No agrupa por cámara ni por ubicación.

## Hallazgos corregidos de paso
- `app/precarga.py` pasaba `False` a `tabla_cola` (resto de F30: el parámetro de presentación ya no existe) y el calentamiento fallaba con un aviso; se quitó el argumento.
- El botón «Anterior» deshabilitado de la Cola tenía 3,43:1; ahora se distingue por borde punteado y cursor y el texto queda a ≥ 4,5:1. Contraste real final: 1.226 textos en 14 vistas, **0 por debajo de 4,5:1** (`f33_contraste.json`; mínimo en píxeles 5,67:1).
- La numeración de capturas sigue el menú (Validación `04_`, Explica `05_`); se borraron las de la numeración anterior y las pruebas se actualizaron.
- Un foco o un clic podía desplazar el marco al capturar; el script de capturas lo corrige antes de cada foto.

## Solo informado (no se cambió, como pedía el prompt)
- El término «Lista A» aparece en textos de la página (Auditoría, Ayuda).
- La frase «Segmentos nuevos» del indicador del Resumen cuenta los segmentos cargados, no los nuevos.
- El texto de Ayuda sobre el rol aún menciona el Modo presentación (que ya no existe desde F30).
- Formatos del identificador de segmento: en pantalla siempre «…» y los 6 últimos dígitos (tablas, selectores, panel y eje del mapa); el de 12 dígitos va en los CSV y como valor interno de los selectores.

## Verificación
Congelados de EP2 14 de 14; v3 5 de 5; sello `f23_integridad_sello.py --comprobar --etiqueta f33`: **intacto** (sin archivos cambiados). Navegación en el navegador real (`f29_navegacion.json`): «Auditar», «Abrir» y «Explicar esta caja →» llevan con su contexto.
Barra lateral a 1366 x 768: desborde 0 px. Ámbar de interfaz: 0 hallazgos en las 8 vistas. No se hicieron conexiones externas ni se descargó nada. Sin commit ni push.

## Archivos tocados
**Código de la página:** `app/secciones.py`, `app/estilos.py`, `app/contexto.py`, `app/precarga.py`, `src/waymo_evaluacion/ep3/app_logica.py`; nuevo `src/waymo_evaluacion/ep3/escala_sintetica.py`.
**Pruebas:** nuevas `tests/ep3/test_pagina_f31.py` (11), `test_pagina_f32.py` (22), `test_pagina_f33.py` (13); adaptadas `test_app.py`, `test_pagina_f20.py`, `f21`, `f23`, `f24`, `f25`, `f26`, `f27`, `f29`, `test_pagina_pulido.py`, `test_pagina_rediseno.py`.
**Scripts nuevos:** `scripts/ep3/f31_f33_capturas.py`, `f31_f32_prueba_escala.py`, `f33_cifras_cruzadas.py`, `f32_comparar_orden_cola.py`; adaptados `capturar_pagina.py`, `f29_navegacion.py` y los generadores `generar_docs_ep3.py`, `generar_guia_estilo.py`, `generar_mapa.py`, `generar_pendientes_pagina.py`.
**Documentos:** escritos a mano `docs/ep3/ESTADO.md` (DEC-122 a DEC-129) y `CLAUDE.md`; regenerados `informe_tecnico_EP3.md`, `README_EP3.md`, `guion_presentacion.md`, `preguntas_cruzadas.md`, `guia_estilo_pagina.md`, `PENDIENTES_PAGINA.md`, `MAPA_DE_ARCHIVOS.md`, `revision/`; este reporte; `docs/referencias_diseno/` (los 4 HTML).
**Mediciones:** `docs/ep3/f31_f32_escala_sintetica.json`, `f31_f33_capturas.json`, `f32_orden_cola_antes_despues.json`, `f33_cifras_cruzadas.json`, `f33_contraste.json`, `f31_sello_despues.json`, `f33_sello_despues.json`.
**Imágenes:** `images/ep3/pagina/` (capturas a 1366 y 1920 px con la numeración nueva) y las 16 de `images/ep3/pagina/para_revision_f31_f33/`. El estado de git completo está en `estado_git.txt` de esa carpeta.
