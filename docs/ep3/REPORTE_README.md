# Reporte F38: README final (informe técnico) para EP3 y la Evaluación Final Transversal

Escrito para: Rafa, que presenta mañana el repositorio y el README antes de pasar a la aplicación. Fecha: 2026-11-24. Alcance elegido: **repo real y suite en copia temporal** (el README y su generador se editaron aquí; la suite completa y `scripts/medir_pruebas.py` corrieron solo en copias, así que el informe de EP2, sus parquets y `pytest_resumen.json` del repo real no se tocaron).

## Estado en una línea
P0, P1 y P2 cerrados. El README quedó en **774 líneas** (la meta era 700), con 17 secciones, 4 capturas de Lente y ninguna cifra de antes perdida. **Pendiente de Rafa:** la retroalimentación del docente (vacía; el README lo declara), la URL del despliegue y la confirmación del caso.

## Qué decidir (resumen corto)
1. **Retroalimentación del docente (EP1 y EP2).** No hay ninguna en el repositorio ni en `docs/`. Pegarla en `docs/ep3/readme_entradas.json` (`retroalimentacion_ep1`, `retroalimentacion_ep2`) y regenerar; hoy la sección 17 dice «Pendiente: completar con la retroalimentación del docente».
2. **URL del despliegue.** Editar `docs/despliegue.json` (`url`, `estado`, `fecha`) y regenerar; vacía, el README dice «Despliegue en AWS Academy: en preparación».
3. **Autoría por rama.** `git shortlog -sn --all` muestra **un solo autor** (MaicolHernandez33, 45 commits, con dos correos); la rama `francismoya` existe en el remoto pero su único commit figura con el mismo autor. El README afirma solo que las tres ramas existen y cita el acuerdo del notebook 03. Conviene que Francis pueda explicar qué hizo en la defensa individual.
4. **Largo.** 774 líneas contra la meta de 700. Se puede acortar quitando los bloques `<details>`, pero se pierde legibilidad. Dígame si prefiere recortar secciones de EP2 (no lo hice: la regla 6 prohíbe borrar).
5. **Datos de la app al desplegar.** El párrafo de ética y la sección 16 dicen que antes de publicar hay que decidir qué datos viajan (`cajas_oof.parquet` trae identificadores y marcas de tiempo de Waymo). No decidí la licencia.

## Verificación
| Comprobación | Resultado |
|---|---|
| `scripts/verificar_congelados.py` | 14 de 14 antes y después |
| `scripts/ep3/verificar_congelados_v3.py` | 5 de 5 antes y después |
| Sello (`f23_integridad_sello.py --comprobar --etiqueta f38`) | intacto |
| `tests/ep3` en el repo real (`medir_pruebas_ep3.py`) | 398 pasadas, 0 falladas, cobertura de `src/waymo_evaluacion/ep3` 86,4 % |
| Suite completa **antes** (copia temporal del repo sin tocar) | 431 pasadas, 1 fallada (prueba de tiempo de la página, `test_tras_la_precarga…`, bajo carga) y **37 con error**: todas las pruebas de EP2 sobre README e informe, porque el generador no podía correr (ver «Hallazgo 1») |
| Suite completa **después** (copia temporal con el README nuevo) | **479 pasadas, 0 falladas, 0 con error** (81 de EP2 + 398 de EP3; son 10 pruebas más que antes: las de `test_readme_f38.py`). Las 37 de EP2 sobre README e informe pasan |
| Render del README (markdown-it) | tablas, bloques `<details>` e imágenes se ven bien; 3 capturas en `images/ep3/readme/para_revision_f38/` |

## Hallazgos que cambian cómo leer el repositorio
1. **El generador de EP2 estaba roto en el entorno de EP3.** `generar_readme.py` fallaba con «XGBoost o imbalanced-learn aparecen en el entorno…» porque comprobaba que `xgboost` NO estuviera instalado, y EP3 lo instaló. Por eso 37 pruebas de EP2 daban error antes de F38 (confirmado en la copia). **Cambio:** la comprobación mira ahora lo que la oración afirma sobre EP2 (su `requirements.txt` y sus notebooks 07 a 10); la oración dice «XGBoost no se entrenó en EP2 … En EP3 sí se entrena y se optimiza (secciones 8.1 y 8.2)». La prueba de EP2 que exigía `find_spec("xgboost") is None` se limitó a `imblearn` (las otras comprobaciones de `xgboost` en `requirements.txt` y notebooks siguen).
2. **`scripts/medir_pruebas.py` (EP2) cuenta también `tests/ep3`.** Corre `pytest -q` completo: en la copia dio 478 pasadas y 1 fallada (no 81), y esa cifra rompe la prueba `test_readme_e_informe_dicen_el_numero_actual_de_pruebas…` de EP2, que cuenta con `--ignore=tests/ep3`. Por eso no lo corrí en el repo real (reescribiría `pytest_resumen.json`, de EP2) y el README mantiene la oración de EP2 (81 pasadas, 92,7 % de cobertura) y agrega un párrafo de EP3 con su propia medición. Arreglo mínimo posible, no aplicado: que `medir_pruebas.py` pase `--ignore=tests/ep3`.
3. **El README ya no cabe en 520 líneas ni en 10 figuras.** Se adaptaron las pruebas de EP2 (sin borrar ninguna): tope de líneas 520 a 800, figuras hasta 14, títulos 1 a 17, anclas que incluyen los subtítulos `###`, ventana de la portada (antes las primeras 16 líneas) y lectura rápida (1, 8.1, 8.2, 8.3, 12.1 y 16).

## Lo que se hizo, por paso
- **Paso 1, portada.** Título «Lente · Auditoría de cajas 3D sin par 2D…», línea de curso y fecha, ficha del proyecto (caso, equipo, solución con enlace al manifest, aplicación), «En breve» con 4 viñetas (problema, qué hace Lente, resultado, límites), «Cómo verlo» (3 comandos y el despliegue), línea de siglas, índice y lectura rápida.
- **Paso 2, mapa de la pauta.** Tabla A (las 10 secciones mínimas con enlace, notebook y evidencia) y tabla B (IE1 a IE12 con peso en la EFT, peso en EP3 solo para IE9 a IE12: 20, 30, 20 y 30, y nivel de evidencia). La sección 15 conserva el mapa de EP2 con un puntero.
- **Paso 3.** 8.1, 8.2, 8.3 y 12.1, cada una con una frase de conclusión arriba, una tabla con IC, «qué decidimos y por qué» y enlace a la evidencia (`artefactos_ep3/…`).
- **Paso 4.** Sección 16 (Lente: flujo en dos pasos, tabla de 8 páginas, 4 capturas, cifras de la app, cómo ejecutarla, prueba en vivo, despliegue desde `docs/despliegue.json`, fase 6 de CRISP-DM) y sección 17 (mejoras). La fila 6 de CRISP-DM de la sección 7 menciona la aplicación.
- **Paso 5.** Las 8 correcciones (abajo).
- **Paso 6.** El balance de objetivos pasó a una tabla corta de cuatro columnas con el detalle en un bloque plegable; las tablas de hiperparámetros, odds ratios y equidad quedaron plegadas; las siglas se definen en una línea de la portada (HGB, ECE, ARI, LR3, OOF…).
- **Paso 7.** `tests/ep3/test_readme_f38.py` (10 pruebas): cifras de la portada y de la sección 16 contra las funciones de la página, enlaces, anclas e imágenes, comandos de «Cómo verlo» (y arranque real de la aplicación), `despliegue.json` con y sin URL, notas de corrección y número de pruebas. Capturas del README, `diff_resumen.txt` y resultados de pytest incluidos.

## Correcciones del Paso 5, una por una
1. **Test sellado.** Nota agregada en las secciones 1, 4 y 8.3: en EP3 los 41 segmentos (33 de entrenamiento y 8 de test de EP2, **80.571 cajas**) son datos de desarrollo; la única prueba ciega son los segmentos nuevos. No se tocaron la sección 7 (diagrama) ni la 10, donde «test sellado» describe EP2.
2. **54,8 % y 35,8 %** (verificados en `cajas_oof.parquet`): el test tiene **3.734** positivos; el segmento `257766998801` aporta **2.046** (**54,8 %**) y solo la celda de la cámara 3 de ese segmento **1.338** (**35,8 %**). Las notas están en las secciones 1 y 11 (**no en la 2**: el prompt decía «2 y 11» pero el 54,8 % aparece en 1 y 11; el 35,8 % no aparecía en el README viejo). Una prueba compara estos números con los datos.
3. **k = 2.** Nota en la sección 9. EP2 (README sección 9, notebook 08): clusters de 52.611 y 15.944 filas con tasas de 26,1 % y 13,6 %, calculados sobre las **68.555 filas de train con |azimut| ≤ 120°** y seis variables (con oclusión). La app (Validación › Tipos de caso, notebook 15, post hoc): **37.094 y 43.477 cajas** (8,9 % y 31,8 %), sobre las **80.571 cajas con |azimut| ≤ 100° de los 41 segmentos** y cinco variables (sin oclusión, que `dev_41` no tiene). Para el informe de EP2 vale el primero; para la página, el segundo. La suma de 80.571 cajas = 64.509 (train 100°) + 16.062 (test).
4. **Pruebas y cobertura (sección 14).** Se mantiene la medición oficial de EP2 (81 pasadas, 92,7 %) y se agrega «Pruebas de EP3»: 398 recolectadas, 398 pasadas, 0 falladas, cobertura de `src/waymo_evaluacion/ep3` 86,4 % (de `medir_pruebas_ep3.py`).
5. **Ética y despliegue.** Párrafo en la sección 13: datos que procesa Lente, «Puntuar datos nuevos» en memoria, qué cambia al desplegar (el servidor recibe los archivos; licencia no comercial sin redistribución), textos del modo publicado como borradores y decisión de qué datos viajan **pendiente**. Coherente con la frase «no debe redistribuirse ni publicarse» de las secciones 13 y 14.
6. **Herramientas colaborativas (IE1).** Tabla «Fuente o herramienta → para qué → por qué esa y no otra» en la sección 4 (GitHub y ramas, bucket con `gsutil` desde Colab, Kedro, pytest, sha256, Streamlit). No se mencionan MLflow ni S3 como usados (S3 aparece solo como guía de despliegue no ejecutada).
7. **Manipulación de datos (IE2).** Línea en la sección 4 con enlace al notebook 04 (listas frente a NumPy, tipos de columna con ahorro de 47,4 %, CSV 5,52 MB frente a Parquet 1,90 MB; cifras leídas del notebook) y a la ingesta con Kedro.
8. **Fechas y títulos.** El título ya no dice «Parcial N°2»; la línea «Evaluación» dice «EP3 y Evaluación Final Transversal (la base de EP2 sigue en las secciones 1 a 15)»; la línea de generación lleva la fecha y la hora reales.

## Desviaciones del prompt
- **«En 30 segundos» se llama «En breve»:** una prueba de EP2 prohíbe «30 segundos» (evita prometer un tiempo de lectura).
- **«Mapa de la pauta» es un título en negrita, no `##`:** las pruebas de EP2 exigen que todo `##` sea una sección numerada.
- **«70/100 frente a 62/100»:** el código da **70,9 frente a 61,9** (captura al revisar el 20 % de todas las cajas; la curva de la página, que usa el 20 % de la cola, da 70,2). El README usa 70,9 y 61,9.
- **Fecha del caso:** `CASO_ACORDADO` se usó tal cual («Waymo Open Dataset v2 (acordado con el docente)»); la fecha o medio de confirmación estaba vacía y se omitió.
- **Ficha sin fila de fecha:** la fecha está en la línea «Curso … Fecha» (una prueba de EP2 quita esa línea al comparar dos corridas).
- **Largo:** 774 líneas (meta 700).
- **Línea «Recomendación (en una frase)»** de la sección 1 cambió de etiqueta respecto del README viejo: viene del informe de EP2 ya regenerado antes de F38; el README no se había vuelto a generar.

## Reconocimiento (Paso 0)
1. **Ensambles reales.** Random Forest (bagging) y HGB (boosting, `HistGradientBoostingClassifier`), más XGBoost y LightGBM (boosting) y cuatro combinaciones con definición en `validacion.DESCRIPCION_CANDIDATOS` (fuente `docs/ep3/plan_v3.md`, P6, y `candidatos.py`): **E1** voto suave de LR, RF y HGB; **E2** promedio de rangos de E1 y la regla; **E3** apilamiento de LR, RF, HGB, XGB y LGBM con regresión logística final entrenada con `GroupKFold` de 3 por segmento; **E4** apilamiento de tres vistas (observación, tamaño, posición). Resultados (AUC con IC; fracción para 80 % con IC; diferencias frente a su mejor componente y frente a la regla; ¿vale la pena?):

   | Técnica | AUC (IC) | Fracción 80 % (IC) | Dif. AUC vs mejor componente (IC) | Dif. fracción 80 % vs regla (IC) | ¿Vale la pena? |
   |---|---|---|---|---|---|
   | RF | 0,798 (0,704 a 0,881) | 0,472 (0,318 a 0,720) | — | +0,026 (−0,029 a +0,085) | no (O2) |
   | HGB | 0,794 (0,706 a 0,872) | 0,494 (0,327 a 0,696) | — | +0,048 (−0,011 a +0,078) | no (O2) |
   | XGB | 0,800 (0,704 a 0,884) | 0,488 (0,294 a 0,766) | — | +0,042 (−0,022 a +0,105) | no (O2) |
   | LGBM | 0,794 (0,699 a 0,878) | 0,531 (0,294 a 0,762) | — | +0,084 (−0,006 a +0,136) | no (O2) |
   | E1 | 0,803 (0,704 a 0,890) | 0,462 (0,291 a 0,767) | +0,005 (−0,007 a +0,020) frente a RF | +0,016 (−0,032 a +0,062) | no aporta |
   | E2 | 0,824 (0,720 a 0,907) | 0,421 (0,271 a 0,702) | +0,001 (−0,005 a +0,008) frente a la regla | −0,025 (−0,048 a +0,008) | no aporta |
   | E3 | 0,789 (0,693 a 0,877) | 0,523 (0,310 a 0,815) | −0,011 (−0,021 a −0,000) frente a XGB | +0,077 (+0,012 a +0,128) | no aporta |
   | E4 | 0,773 (0,678 a 0,858) | 0,610 (0,326 a 0,840) | −0,019 (−0,038 a −0,003) frente a la vista de observación | +0,164 (+0,031 a +0,241) | no aporta |

   La regla de puntos: AUC 0,823 (0,725 a 0,900), fracción 0,446. El mejor modelo único es XGB (AUC 0,800). Fuente: `artefactos_ep3/f4_*`, `f6_tabla_seleccion.csv`. No existe un ensamble que aporte; es el resultado y el README lo dice.
2. **Hiperparámetros.** Búsqueda aleatoria anidada: 5 folds externos por segmento, `GroupKFold(3)` interno, PR-AUC como criterio, 30 configuraciones y 1 repetición (DEV-1; el plan decía 40 y 3). Defecto frente a optimizado (dif. PR-AUC): LR −0,018 (−0,051 a +0,018), RF −0,040 (−0,077 a +0,003), HGB +0,014 (−0,021 a +0,047) y los tres **no mejoran**; XGB +0,059 (+0,034 a +0,085) y LGBM +0,036 (+0,012 a +0,060) **mejoran**. Bordes de grilla: solo LGBM `n_estimators` en el máximo (5 de 5 folds) tras una extensión de LGBM `min_child_samples`. Valores finales de EP2: LR `C` = 0,001, HGB `max_leaf_nodes` = 4 y `min_samples_leaf` = 100, RF `max_depth` = 6 y `min_samples_leaf` = 200 (`hiperparametros_B.json`).
3. **Generalización.** `GroupKFold` de 5 por segmento con búsqueda anidada; AUC de la regla por fold 0,647 / 0,837 / 0,848 / 0,904 / 0,899 (el fold 0 contiene `257766998801`); mediana del AUC por segmento 0,898 con 22 segmentos evaluables y 2 bajo 0,55; bootstrap por segmentos de 1.000 réplicas (`metricas.py`); brecha de XGBoost 0,102; test sellado de EP2 y, en EP3, los dos pasos frente a uno (29,6 % frente a 44,6 %, en muestra). La validación externa con segmentos nuevos está sellada y sin ejecutar.
4. **Discrepancia del k = 2.** Resuelta en la corrección 3.
5. **Herramientas colaborativas.** `git branch -a`: `main`, `maicolhernandez`, `francismoya` y sus `origin/*`. `git shortlog -sn --all`: MaicolHernandez33, 45 commits; la rama `francismoya` tiene 1 commit (mismo autor) y `main` 13. Evidencia de Kedro (`conf/`, `src/waymo_evaluacion/pipelines`), pytest, `gsutil` y `google.colab.auth` en los notebooks 00, 00b y 03, Streamlit y Docker (preparado, build sin probar: ver `docs/ep3/despliegue.md`). No hay evidencia de MLflow (DEC-6) ni de S3 usado.
6. **Pruebas.** `scripts/medir_pruebas.py` (EP2): `pytest_resumen.json` del repo dice 81 pasadas, 0 falladas, 92,7 % de cobertura. Corrido en la copia (cuenta también EP3): 478 pasadas, 1 fallada (ver «Hallazgo 2»), 94,5 %. `tests/ep3`: 398 pasadas, 86,4 %. Qué verifican hoy las pruebas del README (EP2, 17 + 9 + 11): que los enlaces y anclas existan, que las tablas tengan celdas parejas, que el resumen coincida con los CSV, la estructura (una frase por sección), los comandos de la sección 14, los logaritmos, las pautas de EP2 y que README e informe digan lo mismo; más las 10 nuevas de F38.
7. **Retroalimentación del docente.** Búsqueda en `docs/*.md`, `docs/ep3/*.md` y el log de EP2: no hay ninguna registrada.
8. **Despliegue.** Existen `Dockerfile` y `docker-compose.yml` (solo local, `127.0.0.1`), `docs/ep3/despliegue.md` con una guía orientativa de EC2 y S3 **no ejecutada**, y `MODO_DESPLIEGUE = "local"` (modo `publicado` con borradores sin activar). No existe configuración de AWS Academy. Nuevo: `docs/despliegue.json`.
9. **Capturas existentes.** `images/*.png`: 42 figuras de EP2 (2026-10-16 a 2026-10-18); `images/ep3/`: figuras de EP3; `images/ep3/pagina/`: capturas de la página de 2026-11-23 (versión anterior a F36 en partes). Se hicieron 4 nuevas con la página de hoy en `images/app/`.

## Lo que no pude verificar
- Que el README se vea igual en GitHub (se probó con markdown-it, que cubre tablas y `<details>`).
- Las celdas de «Evidencia» de la tabla A: son punteros a secciones, notebooks y archivos, no se contrastaron con cada rúbrica.
- El texto «por qué esa y no otra» de la tabla de herramientas: se apoya en el acuerdo del notebook 03 y en las decisiones de `ESTADO.md`; las demás razones son descriptivas.
- La prueba en vivo con segmentos nuevos reales (F37, parcial): la sección 16 la describe como procedimiento, sin resultados.

## Pendiente para Rafa
Retroalimentación del docente en `docs/ep3/readme_entradas.json`; URL y estado en `docs/despliegue.json`; confirmación del caso (fecha o medio); regenerar con `contar_pruebas.py` → `medir_pruebas_ep3.py` → `generar_readme.py`; revisar la autoría por rama; decidir la licencia de los datos de la app antes de desplegar.

## Archivos tocados
Nuevos: `scripts/ep3/readme_f38.py`, `medir_pruebas_ep3.py`, `f38_capturas_app.py`, `f38_capturas_readme.py`, `f38_diff_readme.py`, `tests/ep3/test_readme_f38.py`, `docs/despliegue.json`, `docs/ep3/readme_entradas.json`, `docs/ep3/REPORTE_README.md`, `images/app/` (4 PNG), `images/ep3/readme/para_revision_f38/`.
Modificados: `scripts/generar_readme.py` y `README.md` (generado), `tests/test_readme.py` y `tests/test_ajustes_finales.py` (adaptaciones documentadas arriba), y los generadores `generar_mapa.py`; ESTADO.md y CLAUDE.md a mano. No se tocaron modelos, cifras, plan congelado, informe de EP2, `data/08_reporting/*`, notebooks ni el sello.

## Resultado de la suite después
En la copia, `scripts/medir_pruebas.py` dio 478 pasadas y 1 fallada (efecto del «Hallazgo 2»: reescribió el `pytest_resumen.json` de la copia con 479 pruebas y la prueba de EP2 que cuenta con `--ignore=tests/ep3` esperaba 81). Con el `pytest_resumen.json` de EP2 restaurado (81) y `pytest -q` completo: **479 pasadas, 0 falladas**. Detalle en `resultado_pytest.txt`.
