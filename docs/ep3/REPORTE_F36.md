# Reporte F36: Ética y límites, Ayuda y glosario, y modo de despliegue

Escrito para: la persona que pidió el rediseño y decidirá qué queda. Fecha: 2026-11-23. Los HTML de referencia están en `docs/referencias_diseno/` (`f36_etica_ayuda_propuesta.html`, `prompt_F36.md`).
Las cifras salen de las mismas funciones que usan Validación y el Resumen (ver «Cifras compartidas»). Las cifras de desempeño son **en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos**.
Capturas: `images/ep3/pagina/para_revision_f36/` (7 PNG a 1366 px). Línea base anterior: `images/ep3/pagina/antes_f36/` y `tests/ep3/datos_f36/textos_antes.json`.

## Qué decidir (resumen corto)
1. **Textos del modo «publicado».** Están redactados como borrador (con el rótulo «borrador: verificar» y el marcador `[nombre del servicio]`) y **no están activos**: `MODO_DESPLIEGUE` sigue en `local`. Hay que completarlos y revisarlos antes de publicar.
2. **Licencia de los datos derivados de Waymo.** `data/09_app_ep3/cajas_oof.parquet` (80.571 filas, 9,5 MB) trae identificadores de objeto y marcas de tiempo del Waymo Open Dataset. No decido si puede publicarse: es de quien publica (ver sección 3).
3. **Otras páginas que dicen «solo local».** Fuera de la lista de la sección 3, `app/secciones.py` dice «No hay modelo de tipos de caso en este equipo.» (Explica una caja) y los encabezados de `Dockerfile` y `docker-compose.yml` dicen que son para uso local. Solo informado, no se cambió.
4. **Enlaces sin flecha.** Los tres enlaces de «Cómo funciona» y «Ver Validación» no llevan flechas (regla de F23); la maqueta las traía.
5. **Tono.** La maqueta usa «tú» en algunos rótulos; la página usa «usted» y los textos nuevos son neutros. Si quiere «tú», es un cambio de constantes en `etica_ayuda.py`.

## Conteos de pruebas (`python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider`)
| Momento | Pruebas de EP3 | Resultado |
|---|---|---|
| Antes de F36 (después de F35) | 367 | 367 pasadas |
| Después de F36 (+11 en `test_pagina_f36.py`) | **378** | **378 pasadas, 0 falladas** (corrida completa final) |

Se adaptaron (sin borrar ninguna) las pruebas de F20 y F26 a la estructura nueva de las dos páginas. `pytest` sin ruta no se corrió. Congelados: EP2 14 de 14, v3 5 de 5; sello de la página: intacto (`f36_sello_despues.json`).

## Parte A · Ética y límites
**Qué cambió.** Primero el aviso «Decide siempre una persona.» con la frase «La solución ordena las cajas y avisa qué cámaras tienen huecos. No etiqueta ni borra nada.» y dos avisos de «nunca» («Nunca debe usarse para descartar cajas sin revisarlas.» y «No es una prueba de seguridad del vehículo…»). Después: Propósito (corto), Datos y licencia (tres puntos; el número de segmentos sale de `inicio_resumen`), Desempeño (tres tarjetas: AUC 0,823; recall en el punto A 79,8 %; captura al revisar el 20 % 61,9 %; etiqueta «en muestra», nota y enlace «Ver Validación»), Límites conocidos (barra peatones 80,6 % / ciclistas 44,3 % con los números escritos, «Casos encontrados · ciclistas: 115 casos en 14 segmentos.» y dos puntos), y dos tarjetas: Consideraciones éticas y Dónde corre.
**Accesibilidad.** Los iconos son decorativos (`aria-hidden`); la barra tiene descripción para lector de pantalla («Casos encontrados: peatones 80,6 %, ciclistas 44,3 %.») y los dos números en texto; el ámbar solo en el punto de ciclistas. Una prueba lo comprueba.
**Qué no se pudo / diferencias con la maqueta.**
- Los enlaces no llevan flecha (regla de F23).
- El fondo del aviso inicial («Decide siempre una persona.») usaba un degradado en la maqueta; aquí es un fondo plano (la única escala con degradado es la del mapa de la Auditoría, regla de F20).
- La etiqueta «en muestra» es neutra (no ámbar).
**Frases que se partieron para el diseño nuevo** (están en `FRASES_AJUSTADAS` de `etica_ayuda.py` y la prueba de regresión las acepta como excepciones documentadas):
1. «Decide siempre una persona: la solución no etiqueta ni borra nada y nunca debe usarse para descartar cajas sin revisarlas.» → título, frase y aviso «Nunca debe usarse…».
2. «No es una prueba de seguridad del vehículo: mide si…» → dos frases (los dos puntos pasan a punto).
3. «En validación cruzada por segmentos: AUC …, recall … y … de las cajas sin pareja…» → tres tarjetas con las mismas cifras.
4. «La regla es poco confiable para ciclistas (44,3 % contra 80,6 % en peatones; 115 casos en 14 segmentos).» → frase, barra y «Casos encontrados · ciclistas: N casos en M segmentos.».
5. La frase de los tres pasos de la ayuda → tres tarjetas numeradas.
6. **Ajuste para seguir siendo cierta:** «…editable en «Supuestos» de la cola de revisión» → «…editable en «Supuestos y confiabilidad» de la cola de revisión» (el desplegable se llama así desde F32).

## Parte B · Ayuda y glosario
**Qué cambió.** «Cómo funciona, en tres pasos» como tres tarjetas con su enlace (Auditoría de cámaras, Cola de revisión, Ética y límites). «Qué hace cada página» como seis tarjetas: los tres textos de antes (Rol, Auditoría de cámaras, Cola de revisión) sin tocar y tres nuevas con borde punteado (Validación, Explica una caja, Puntuar datos nuevos) cuyo texto es el subtítulo actual de cada página (verificado contra F31 a F35; para Puntuar sale de `texto_entorno`). Glosario como tarjetas con buscador y grupos Datos / Revisión / Rigor: las 11 definiciones son las de antes, palabra por palabra (prueba). Preguntas frecuentes: las mismas cinco, en desplegables.
**Buscador.** Sin distinguir mayúsculas ni tildes, en el término y en la definición, combinable con el grupo; sin coincidencias dice «Ningún término coincide con la búsqueda.» (con `role="status"`). Un término nuevo del glosario que no esté en ningún grupo aparece bajo «Otros» (ninguno hoy).
**Términos extra del glosario.** Ninguno: no se agregó ni se quitó ningún término.
**Qué no se pudo / diferencias.** Los enlaces de los pasos no llevan flecha. Se agregó una línea (`st.caption`) que explica el borde punteado de las tarjetas nuevas.
**Respuestas actuales de las preguntas frecuentes** (en modo `local`; todas iguales a las de antes salvo la última, ver frase 6):
- ¿El sistema decide qué cajas están mal? — «No. Solo ordena. Una persona revisa y decide; ninguna caja se descarta sin revisarla.»
- ¿Qué significa «en muestra»? — «Que el resultado se calculó con 41 segmentos y el detector de huecos se ajustó con esos mismos datos; todavía no hay una prueba con segmentos nuevos. Por eso las cifras de este flujo son optimistas y no deben leerse como una prueba ciega. La validación con segmentos nuevos está preparada y sellada, y todavía no se ejecutó. La ganancia del flujo en dos pasos sale de 2 celdas cámara x segmento, una de ellas en el segmento donde se descubrió el hueco.»
- ¿Qué pasa con los ciclistas? — «En ciclistas la regla es poco confiable: encuentra 44,3 % de los casos contra 80,6 % en peatones, con solo 115 casos en 14 segmentos. Conviene revisarlos con más cuidado.»
- ¿Se guardan o se envían los archivos? — «No. Nada se guarda ni se envía: «Puntuar datos nuevos» procesa el archivo en memoria y la aplicación no hace ninguna conexión a internet.»
- ¿Cuánto tarda revisar una caja? — «No se midió: se usa un supuesto de 20 segundos por caja, editable en «Supuestos y confiabilidad» de la cola de revisión.»

## Sección 3 · Modo de despliegue
**Qué se hizo.** Una sola constante, `MODO_DESPLIEGUE` en `app_logica.py` (`local` por defecto), gobierna cuatro textos y la etiqueta de Puntuar a través de `TEXTOS_ENTORNO` y `texto_entorno(clave)`: Consideraciones éticas, Dónde corre, la respuesta «¿Se guardan o se envían los archivos?» y las dos etiquetas de Puntuar (`puntuar_etiqueta`, `puntuar_etiqueta_2`; antes la segunda estaba escrita a mano en la página). Con `local` los textos son **exactamente los de antes** (prueba de regresión). La variable `EP3_ENTORNO` (`publicado` o `servidor`) reemplaza a la constante solo en el proceso donde se define; sirvió para capturar la variante sin tocar el código. La variante `publicado` está implementada con los borradores de la maqueta, marcados «borrador: verificar», y **no está activada**.
**Textos de la variante `publicado`:**
- Dónde corre: «En un servidor conectado a internet ([nombre del servicio]). Cualquiera que tenga el enlace puede abrir la aplicación. No se deben subir datos que no puedan compartirse con ese servicio.»
- Consideraciones éticas: «Las tablas tienen identificadores de objeto y marcas de tiempo. Los archivos que se suben en «Puntuar datos nuevos» se procesan en la memoria del servidor durante la sesión y no se guardan.»
- Preguntas frecuentes (archivos): «Los archivos que se suben se procesan en la memoria del servidor durante la sesión y no se guardan. Salen del equipo hacia el servidor, así que no se deben subir datos que no puedan compartirse con él.»

**Evidencia** (`docs/ep3/f36_verificacion_despliegue.json`, generada por `scripts/ep3/f36_verificar_despliegue.py`, que solo lee y reporta):
1. **Escrituras a disco o cachés persistentes.** `app/` no escribe nada ni usa `st.cache*`, pickle, tempfile ni registros. En el paquete `src/waymo_evaluacion/ep3` que viaja en la imagen hay escrituras en tres módulos: `alternativas.py` y `inferencia.py` (guardan modelos congelados) y `sellado.py` (sello de la validación externa). Son funciones de los scripts de entrenamiento y sellado; la página no las llama (no se encontraron llamadas desde `app/`; una prueba vigila que la página y `puntuar.py` no escriban).
2. **Archivos subidos.** Streamlit 1.65 los guarda en memoria (`memory_uploaded_file_manager.py` y `uploaded_file_manager.py` no abren archivos). `memory_media_file_storage.py` solo lee archivos de medios por ruta (`open(filename, "rb")`, línea 205): no escribe subidas. Con la configuración actual, además, la página corre en `localhost` y no hay carpeta temporal propia.
3. **Archivos que viajarían** (lo que copia el `Dockerfile` y lo que monta `docker-compose.yml` solo lectura): `app/` 17 archivos, 226 KB; `src/waymo_evaluacion/ep3` 22 archivos `.py`, 286 KB; `data/09_app_ep3` 32 archivos, 9,6 MB (de los cuales `cajas_oof.parquet` son 9,5 MB); `data/06_models_ep3` 8 archivos, 2,0 MB (`no_supervisado_v3.joblib` 1,98 MB).
4. **Datos del Waymo Open Dataset dentro.** Sí hay datos derivados: `cajas_oof.parquet` tiene 80.571 filas por caja con `seg`, `key.frame_timestamp_micros`, `key.laser_object_id`, centro y tamaño de la caja, azimut, distancia, puntos de LiDAR, velocidad y rumbo, más las predicciones (`score`, `prob_cal`). `celdas.csv` (41 filas por segmento y cámara) y `lista_A.csv` traen identificadores de segmento. **No decido si pueden publicarse**: depende de los términos de la licencia de Waymo (waymo.com/open/terms), que debe revisar quien publica. El pie de la página ya incluye la atribución provisional.
5. **Rutas del equipo, usuarios o credenciales.** El nombre de usuario del equipo y las rutas `C:\Users` / `C:/Users` no aparecen en ningún archivo que viajaría. Las coincidencias de la búsqueda son falsos positivos: la palabra «TOKEN» en comentarios y en `TOKENS` de `estilos.py` (tokens de diseño) y una cadena parecida a un correo (`2@G.tf`) dentro de los bytes comprimidos de `cajas_oof.parquet`, que no tiene columnas de texto con correos.

**Cómo se captura la variante.** `f36_03_etica_modo_publicado.png` sale de una segunda copia de la página lanzada con `EP3_ENTORNO=publicado` en otro puerto; la constante del código no se tocó, así que no hay que «volver a `local`».

## Cifras compartidas (no se escriben a mano)
- AUC 0,823, recall en el punto A 79,8 % y 61,9 % al revisar el 20 %: `EA.tarjetas_desempeno` sobre las tarjetas de `kpis.json` (las mismas de Validación y el Resumen).
- 80,6 % y 44,3 %, «115 casos en 14 segmentos»: `EA.comparacion_clases` sobre `datos_ciclistas` (las mismas de Validación y de la pregunta frecuente de los ciclistas).
- «41 segmentos»: `inicio_resumen` (el mismo del pie y de Validación).
Una prueba (`test_las_cifras_de_etica_son_las_de_validacion_y_del_resumen`) compara estas cifras con las otras páginas.

## Lo que solo se informa (no se cambió)
- **Modo presentación:** no queda ninguna mención en `app/` ni en `src/` (solo en documentos de fases anteriores, que cuentan su historia).
- **Nombres antiguos de las pestañas de Validación** (Hiperparámetros, Ensambles, Selección, No supervisado): no quedan como nombres de pestaña en la página; la palabra «Ensambles» aparece en una línea de evidencia («Ensambles que aportan sobre su mejor componente…»), que es el contenido y no un nombre de pestaña.
- **«Lista A» y «Lista B»:** ya no aparecen en textos que se vean en la página; siguen en comentarios y documentación del código y en nombres de archivos (`lista_A.csv`).
- **Páginas que dicen «solo local» fuera de la lista de la sección 3:** «No hay modelo de tipos de caso en este equipo.» (`app/secciones.py`, línea 651) y los encabezados del `Dockerfile` y de `docker-compose.yml`.

## Archivos
Nuevos: `src/waymo_evaluacion/ep3/etica_ayuda.py`, `tests/ep3/test_pagina_f36.py`, `tests/ep3/datos_f36/textos_antes.json`, `scripts/ep3/f36_exportar_textos.py`, `scripts/ep3/f36_capturas.py`, `scripts/ep3/f36_verificar_despliegue.py`, `docs/ep3/f36_verificacion_despliegue.json`, `docs/ep3/f36_capturas.json`, `docs/ep3/f36_sello_despues.json`, este reporte y `images/ep3/pagina/para_revision_f36/`.
Modificados: `app/secciones.py` (`etica`, `ayuda` y las etiquetas de Puntuar), `app/estilos.py` (bloque de CSS y ayudantes de F36), `src/waymo_evaluacion/ep3/app_logica.py` (`MODO_DESPLIEGUE`, `TEXTOS_ENTORNO`, `texto_entorno`, respuesta de «¿Cuánto tarda…?»), `scripts/ep3/capturar_pagina.py`, `tests/ep3/test_pagina_f20.py` y `test_pagina_f26.py`, y los generadores `generar_guia_estilo.py` y `generar_mapa.py`. No se tocaron `cola_segmento`, ninguna cifra de Validación ni el sello v3.
