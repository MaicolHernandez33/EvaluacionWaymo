# F34 + F35 · Rediseño de Validación y de Puntuar datos nuevos

Eres el asistente de código del repositorio `waymo-evaluacion` (app Streamlit «Lente», EP3). Esta tarea tiene dos partes, que se hacen en orden: **F34 (Validación) → F35 (Puntuar datos nuevos)**. Es solo trabajo de interfaz y de presentación de tablas. Trabaja las dos partes sin esperar mi respuesta entre una y otra, pero si alguna regla de abajo se rompe, detente y repórtalo.

Esta tarea va después de F31, F32 y F33 (Auditoría, Cola, Explica una caja). No las rehagas ni las modifiques. Si alguna no está aplicada todavía, no la apliques aquí: anótalo en el reporte y sigue con lo tuyo.

## 0 · Material de referencia

Dos maquetas HTML son la referencia visual. Cópialas a `docs/referencias_diseno/` (ya existe si hiciste F31 a F33) y ábrelas en el navegador antes de empezar:

- `f34_validacion_puntuar_propuesta.html` → abre en **Validación** (las 5 pestañas funcionan). Para F34 mira solo esa página.
- `f35_puntuar_propuesta.html` → abre en **Puntuar datos nuevos**. Pulsa «Usar un segmento de desarrollo de ejemplo» para ver el estado con resultado. Para F35 mira solo esa página.

Cómo usarlas:

- **Gana el HTML** en jerarquía, orden de bloques, textos y comportamiento. Si este prompt y el HTML se contradicen, sigue el HTML, salvo en los puntos marcados con **«Ojo»**.
- **Los datos de las maquetas son en parte aproximados o inventados.** Nunca copies un número desde el HTML. Cada cifra sale de lo que la app ya calcula. En cada parte te digo qué es real y qué no.
- No copies el CSS tal cual. Usa el tema oscuro y los componentes de la app, y llega al mismo resultado visual.

## 1 · Reglas que valen para las dos partes

1. **No tocar** el modelo, la regla de priorización, la calibración, los datos, los umbrales, los resultados guardados ni ninguna cifra. Esto es rediseño. La solución v3 congelada (sello del 2026-11-14) debe seguir intacta: verifica que su sello no cambia.
2. **No hagas commit.** Deja los cambios sin confirmar.
3. **Antes de editar**, imprime la lista de archivos que vas a tocar, por parte. Después sigue sin esperar.
4. **Antes de empezar, captura el estado actual** de las dos páginas (Validación en sus 6 pestañas, con y sin tablas abiertas; Puntuar vacía y con el segmento de ejemplo cargado). Sirven para comparar antes y después, y para detectar elementos que hoy existen y la maqueta no muestra.
5. **Pruebas:** corre la suite completa antes de empezar y después de cada parte, y anota los conteos. Añade pruebas para la lógica nueva. Si una prueba que pasaba falla, detente.
6. **Regresión de cifras:** exporta antes de cambiar nada todos los valores que hoy muestra cada tabla y cada gráfico de Validación (a un archivo temporal fuera del repo) y compáralos después. Deben ser idénticos; solo puede cambiar el formato de presentación. Cualquier diferencia numérica es un error tuyo: corrígela o repórtala.
7. **Accesibilidad:** contraste ≥ 4,5:1 en todo texto, tamaño mínimo 12 px, foco visible (solo con teclado, sin recuadros gruesos en reposo), pestañas con `role="tab"` y estado seleccionado, el estado nunca solo por color (siempre texto o forma además), gráficos con descripción de texto.
8. **Lenguaje:** español, sin jerga. Conserva el vocabulario actual. Mantén el pie de página de Waymo y la línea «Solución v3 congelada…».
9. **Cifras que deben coincidir entre páginas** (compruébalo y repórtalo): AUC 0,823, 80.571 cajas, 21,2 % sin pareja, peatones 80,6 % y ciclistas 44,3 %, 358 h → 200 h → 132 h, 61,9 % de captura al revisar el 20 %, 44,6 % y 29,6 % de cajas a revisar para el 80 %. Deben salir de las mismas funciones en el Resumen, la Cola y Validación.
10. **Enlaces entre páginas:** si el Resumen u otra página enlaza a una pestaña de Validación por nombre («En muestra», «Selección»…), actualiza los enlaces a las pestañas nuevas y verifica que cada uno aterrice en el lugar correcto.

---

## PARTE F34 · Validación

**Qué es la página:** la página de rigor. Responde «¿puedo confiar en estas cifras?»: qué se probó para elegir la regla, qué tan bien funciona y qué falta por demostrar. Hoy tiene 6 pestañas (Hiperparámetros, Ensambles, Generalización, Selección, No supervisado, En muestra), cada una con una lectura, un gráfico y varias tablas largas abiertas tras «Ver tabla completa».

**Cifras reales hoy (solo para reconocerlas, no las pongas fijas):** AUC 0,823 (IC 95 % 0,725 a 0,900); 80.571 cajas; 21,2 % sin pareja; peatones 80,6 %; ciclistas 44,3 %; captura al revisar el 20 % = 61,9 %; cajas a revisar para el 80 % = 44,6 % en un paso y 29,6 % en dos pasos; 358 h, 200 h y 132 h con 20 s por caja (supuesto); punto de equilibrio de la auditoría 6.059 cajas; dos tipos de caso (8,9 % y 31,8 % sin pareja).

### Cambios (sigue `f34_validacion_puntuar_propuesta.html`, página Validación)

1. **Cabecera con veredicto + 4 tarjetas** en lugar de la lista «Cifras de apoyo»: AUC (con su intervalo), cajas analizadas (con % sin pareja), casos encontrados en peatones y casos encontrados en ciclistas (con «poco confiable»). Debajo, tres etiquetas siempre visibles: «En muestra: N segmentos de desarrollo» (N real), «Sin validación con datos nuevos», «Ciclistas: regla poco confiable».
   **Ojo:** el titular de la maqueta («La regla simple se mantiene: ninguna de las 10 alternativas probadas «vale la pena» frente a ella») **debe calcularse**. El «10» sale de contar las alternativas (todos los candidatos menos la regla) y la afirmación solo se muestra si ninguna cumple O2. Si alguna cumpliera, el titular cambia a un texto neutro que diga cuántas cumplen y cuáles. Escribe una prueba para las dos ramas.
2. **Pestañas: de 6 a 5, en este orden:** **Modelo elegido** (antes «Selección»), **Generalización**, **Alternativas** (antes «Hiperparámetros» y «Ensambles», como dos secciones con su propia lectura cada una), **Tipos de caso** (antes «No supervisado»), **En muestra**. No elimines ningún análisis: solo se reordena. Teclas izquierda y derecha cambian de pestaña.
3. **Plantilla común en cada pestaña:** lectura (las frases actuales, que ya vienen calculadas; no las reescribas) → un gráfico → puntos clave → «Tablas de apoyo» cerrada. La «Lectura» no se resume ni se cambia.
4. **Modelo elegido:** cuatro tarjetas O1 a O4 en lugar de la matriz de 11 filas × 5 columnas. Cada una muestra «✓ X de N» o «✕ X de N» (calculado desde la tabla de criterios) y su definición corta (la que hoy aparece bajo la tabla). Si la propia regla no cumple O4, un aviso lo dice con su AUC mínimo por partición y el mínimo exigido, calculados; si lo cumpliera, el aviso no aparece. Debajo, la tabla «Resultados de la solución elegida» (las 5 filas actuales, sin cambios de valor) y la línea de fuente. En apoyo: «Todos los candidatos» y «Criterios por candidato (O1 a O4)».
5. **Generalización:** el gráfico de puntos con intervalo y rombos por partición, con (a) una línea vertical en el AUC mínimo por partición de O4 (usa la constante de la app, no un 0,75 escrito a mano) rotulada «mínimo por partición: X», (b) la partición con menor AUC rotulada «partición N», y (c) la fila de la regla resaltada. Dos puntos clave calculados: el rango de la brecha de AUC entre ajuste y validación de la regla, y el AUC de la partición más débil de la regla frente al mejor candidato en esa partición. En apoyo, las dos tablas de brecha.
6. **Alternativas:**
   - Hiperparámetros: gráfico de cambio de PR-AUC con el estado en **texto** al final de cada fila («mejora» / «no mejora»), usando la misma regla que ya aplica la app para el color (conserva esa regla y dime cuál es). Un aviso calculado: cuántos hiperparámetros de cuántos terminan en el borde de la grilla y cuáles (hoy 1 de 13: LGBM, número de árboles).
   - Ensambles: gráfico con el valor de la diferencia y el veredicto en texto en cada fila.
   - En apoyo: «Por defecto contra optimizado», «¿Aportan los ensambles?» y «Bordes de la grilla de búsqueda».
7. **Tipos de caso:** gráfico con los dos tipos de caso y sus intervalos, y tres puntos clave calculados (cajas y % por tipo; qué pasa con k = 4; y que son los tipos que muestra Explica una caja, **solo si esa página existe**). En apoyo: aporte de los grupos, grupos con k = 2 y k = 4, estabilidad, cajas atípicas, comparación EP2/EP3.
8. **En muestra:** primero el aviso ámbar con el texto actual de «en muestra… sin validación con datos nuevos». Luego la lectura, «Impacto estimado» (las tres barras de horas, con «20 s por caja (supuesto)»), el bloque nuevo **«De dónde viene la mejora de la auditoría»** y el gráfico de fracción de cajas a revisar por candidato.
   - El bloque nuevo se construye con la tabla que ya existe «Diferencia entre dos pasos y un paso»: variante, un paso, dos pasos, cambio en puntos. Debajo, una frase calculada que compare lo que aporta auditar solo la mejor celda con lo que aportan ambas.
   - En el gráfico de barras agrupadas, deja la leyenda arriba, pon el valor sobre cada barra y no uses solo el color para distinguir los flujos.
9. **Lo que sale de pantalla (queda en la descarga CSV):** la tabla «Curvas de validación». «Comparación entre EP2 y EP3» queda dentro de las tablas de apoyo de «Tipos de caso».
10. **Candidatos con nombre entendible.** En la interfaz, «vista obs», «vista tam» y «vista pos» pasan a «vista de observación», «vista de tamaño» y «vista de posición». E1 a E4 y LR3 necesitan una línea de «qué es» (en una tabla «Candidatos» dentro de las tablas de apoyo de «Modelo elegido», o en tooltips). **Saca esas descripciones del código, de la configuración o del informe técnico de EP3; no las inventes.** Si no puedes establecer qué es alguno, déjalo sin descripción y dímelo.

### Ojo · una cifra a verificar

En «Comparación entre EP2 y EP3», la fila «ARI KMeans vs GMM (k elegido)» muestra 0,997 en EP2 y 0,007932 en EP3. Un salto así parece un error de cálculo, de escala o de etiqueta, y además es la única cifra de esa tabla sin redondear. **No cambies el valor.** Investiga de dónde sale (cálculo, etiqueta, unidad) y repórtalo con la evidencia. Si el problema es solo de formato, corrígelo en la presentación; si el valor parece incorrecto, déjalo y avísame.

### Estándar de tablas (aplícalo a TODAS las tablas de Validación y de Puntuar)

Hoy hay tablas con su propia barra de scroll dentro del scroll de la página, con la primera fila cortada bajo el encabezado, con columnas que quedan fuera de pantalla («Por defecto contra optimizado», «Ensambles», «Hueco contenido», «Mediana del…»), con encabezados muy largos, con IC inferior y superior en columnas separadas, y con cifras de distinto formato (0,007932 junto a 0,8149 y 0,823).

Crea **un solo componente de tabla** y úsalo en todas, con estas reglas:

1. **Sin scroll vertical interno.** Hasta 25 filas, se muestran todas. Con más, se pagina de 25 en 25. El scroll horizontal, si hace falta, ocurre dentro de un contenedor con la primera columna fija y un indicio visible de que hay más columnas.
2. **El encabezado no tapa la primera fila.** Verifica en cada tabla con una captura.
3. **Intervalos en una sola columna:** «0,797 (0,701–0,889)». Los valores separados (inferior, superior) quedan en la descarga CSV.
4. **Encabezados cortos:** tres palabras como máximo, con el nombre completo en un `title` o tooltip. Las unidades van en el encabezado.
5. **Números a la derecha, cifras tabulares.** Decimales fijos por tipo de columna: AUC, PR-AUC, Brier y diferencias con 3 decimales; porcentajes con 1; recuentos con punto de miles. Coma decimal.
6. **Signo menos único** («−», U+2212) en tablas, ejes y gráficos. Las diferencias llevan «+» cuando son positivas.
7. **Texto:** corrige las faltas de tilde («maximo» → «máximo», «minimo» → «mínimo») y los textos técnicos crudos («n init» → «n_init» en código o una descripción en palabras). Solo en lo que se muestra: no cambies nombres de columnas internas ni de archivos.
8. **Cada tabla** lleva título, una línea «Responde: …», conteo de filas y «Descargar CSV» (con todos los valores sin redondear).
9. **«Tablas de apoyo»** es un desplegable cerrado por defecto, con un contador. Cada tabla va en su propio sub-desplegable con un título claro. Reemplaza los «Ver tabla completa» actuales. El recuadro de foco azul grueso que hoy se ve en reposo en «Ver tabla completa» debe aparecer solo con foco de teclado.
10. **Identificadores de segmento:** hoy Validación muestra 12 dígitos (por ejemplo 257766998801) y otras páginas muestran la forma corta («…998801»). Elige **una** y aplícala en Validación y Puntuar. No cambies las demás páginas: lista en el reporte cada lugar donde difiera. Si hay una función de formato compartida, úsala.

### Pruebas específicas de F34

- Prueba del titular con sus dos ramas (ninguna cumple O2 / alguna cumple).
- Prueba de los conteos «X de N» de O1 a O4 con datos reales y con una tabla sintética distinta.
- Pruebas del componente de tabla: paginación, formato de decimales y signo menos, intervalos en una columna, orden de columnas, descarga con valores sin redondear.
- Prueba de regresión de cifras (regla 6): todos los valores de antes, iguales después.
- Prueba de que cada enlace a una pestaña de Validación (regla 10) llega a la pestaña correcta.

---

## PARTE F35 · Puntuar datos nuevos

**Qué es la página:** la única donde la solución trabaja sobre datos nuevos: el usuario sube un segmento y obtiene sus celdas marcadas y su cola de cajas. Todo el procesamiento es local y en memoria.

**Importante:** en las capturas que tengo, solo he visto la página **vacía**. No he visto cómo se ve con un segmento cargado. Antes de editar, captura ese estado con «Usar un segmento de desarrollo de ejemplo» y úsalo como línea base.

### Cambios (sigue `f35_puntuar_propuesta.html`)

1. **Cabecera:** subtítulo nuevo («Sube un segmento nuevo y obtén sus celdas marcadas y su cola de cajas con la solución congelada») y dos etiquetas: «Procesamiento local y en memoria» y «No se guarda nada».
   **Ojo:** verifica en el código que «no se guarda nada» es cierto: que el archivo subido no se escribe a disco ni a un caché persistente, y que `st.cache_*` no conserva datos del usuario entre sesiones. Si no es cierto, **no muestres esa etiqueta** y dime qué se guarda y dónde.
2. **Tres pasos arriba** (cargar el segmento, revisar celdas marcadas, revisar la cola), con el paso actual resaltado. Sin archivo, el paso 1 está activo. Con un segmento cargado, los pasos 1 y 2 quedan marcados como hechos y el 3 activo.
3. **Archivos de entrada:** «Elegir archivo» del archivo 1 es la acción principal (botón destacado). El archivo 2 conserva su nombre y sus límites (parquet, hasta 500 MB) y lleva una línea que explica para qué sirve.
   **Ojo:** la maqueta dice «Sirve para marcar huecos de cámara». Es una suposición mía. **Confírmalo en el código** y escribe lo que realmente ocurre sin ese archivo (qué no se calcula, qué se calcula distinto). Usa el texto real.
4. **«Usar un segmento de desarrollo de ejemplo»** pasa a ser un botón discreto con el texto «¿Solo quieres ver cómo funciona?» al lado.
5. **Estado vacío más corto:** «Todavía no hay un segmento cargado» y una línea de explicación, con un dibujo neutro del anillo de cámaras (sin números ni resaltados).
6. **Estado con resultado, en la misma página:** encabezado con el identificador del segmento (formato único, regla 10 de F34), una etiqueta «ejemplo de desarrollo» si corresponde, y los botones «Cargar otro segmento» y «Descargar resultados (CSV)»; tres tarjetas de resumen (celdas marcadas «X de N», cajas afectadas, cajas sin pareja en las celdas marcadas); tabla «Celdas marcadas» con el anillo de cámaras al lado, resaltando la cámara de la celda; tabla «Cola de cajas de este segmento» (paginada de 50 en 50, con las mismas columnas que la Cola de revisión: Prioridad, Caja, Cámara, Clase, Prob. sin pareja, Puntos sensor sup.) con «Descargar CSV».
   **Ojo:** si hoy la página con un segmento cargado muestra elementos que la maqueta no trae (advertencias, avisos de calidad, otras tablas, descargas), **consérvalos** y dime cuáles son. La maqueta no es la lista completa de lo que debe existir.
   **Ojo:** en la maqueta, los datos de la cola son inventados y la celda marcada (cámara 3, 1.677 cajas, 1.338 sin pareja) es la del segmento 257766998801, usada solo como ilustración. Calcula todo con la app. No supongas que el segmento de ejemplo de la app es ese.
7. **Contenido del CSV:** si hoy hay una descarga, conserva su contenido. Si no la hay, descarga las celdas marcadas y la cola en un solo archivo, o dos botones: decide tú y dime cuál elegiste.
8. **Errores claros, en español:** archivo que no es parquet, columnas que faltan (di cuáles), archivo vacío, archivo de más de 500 MB, y archivo 2 que no corresponde al archivo 1. Ninguno debe mostrar un traceback. La maqueta no los dibuja; usa el estilo de aviso de la app.
9. **«Formato de los archivos de entrada»** sigue plegado y ahora lista las columnas que necesita cada archivo, tomadas del código (no inventadas).
10. **«Cargar otro segmento»** restablece la página al estado vacío y libera lo que había en memoria.

### Pruebas específicas de F35

- **Regresión:** con el segmento de ejemplo, las celdas marcadas y la cola son idénticas a las de antes del rediseño.
- Cada error de la lista del punto 8, con archivos sintéticos creados en un directorio temporal (no los dejes en el repo).
- «Cargar otro segmento» vuelve al estado vacío.
- **Escala:** con un parquet sintético de unas 100.000 cajas (en directorio temporal), la página muestra como máximo 50 filas por vez y el tiempo de procesamiento es razonable. Anota el tiempo.
- La etiqueta «No se guarda nada» solo aparece si la comprobación del punto 1 lo respalda.

---

## 2 · Entrega

1. **Carpeta de revisión** `images/ep3/pagina/para_revision_f34_f35/`, con capturas a 1366 px de ancho, **máximo 16 PNG**, con estos nombres:
   - Validación (10): `f34_01_cabecera.png`, `f34_02_modelo_elegido.png`, `f34_03_generalizacion.png`, `f34_04_alternativas_hiperparametros.png`, `f34_05_alternativas_ensambles.png`, `f34_06_tipos_de_caso.png`, `f34_07_en_muestra_impacto.png`, `f34_08_en_muestra_grafico.png`, `f34_09_tablas_de_apoyo_abiertas.png`, `f34_10_tabla_paginada.png`
   - Puntuar (6): `f35_01_vacio.png`, `f35_02_error_de_archivo.png`, `f35_03_resultado_resumen.png`, `f35_04_resultado_celdas.png`, `f35_05_resultado_cola.png`, `f35_06_formato_abierto.png`
2. **`REPORTE_F34_F35.md`** en la misma carpeta, **sin límite de largo**. Por parte: qué cambió, qué no pudiste hacer y por qué, en qué se aparta del HTML y por qué, las decisiones que tomaste y lo que encontraste. Además: lista de archivos tocados; conteos de pruebas antes y después de cada parte; resultado de la regresión de cifras (regla 6); resultado de la comprobación de cifras cruzadas (regla 9); tu investigación sobre el ARI 0,007932; el resultado de la comprobación de «No se guarda nada»; el texto real que pusiste para el archivo 2; las descripciones de E1 a E4 y LR3 con su fuente; los lugares donde el identificador de segmento tiene otro formato; los tiempos de la prueba de escala; y los elementos de Puntuar con resultado que hoy existen y la maqueta no tiene.
3. **`estado_git.txt`** en esa carpeta, con la salida de `git status --short`.
4. Resume en tu respuesta final **en 10 líneas**: qué quedó hecho, qué no, y lo que debo decidir yo.

## 3 · Solo reporta, no cambies

Si ves cualquiera de estas cosas, anótalas en el reporte sin tocarlas: texto de «Ayuda y glosario» que describa las pestañas antiguas de Validación («Hiperparámetros», «Ensambles», «Selección», «No supervisado») o el Modo presentación; el término «Lista A» en algún texto; la frase «Segmentos nuevos» en el Resumen; cualquier otra página que muestre identificadores de segmento en un formato distinto.
