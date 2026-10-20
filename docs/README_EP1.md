> **README de EP1, conservado tal como estaba al cerrar EP1 y durante la preparación de EP2** (incluye los bloques «Actualización de EP2» que se agregaron en el camino). Los enlaces relativos se ajustaron para que funcionen desde `docs/`. El README vigente de EP2 está en la raíz del repositorio.

# Waymo Evaluación

[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)

Proyecto de clasificación binaria sobre datos de percepción de vehículos autónomos, construido con Kedro 1.5.0 sobre un CSV sintético (esquema Waymo v2) y una muestra real descargada del Waymo Open Dataset v2.

<!-- EP2-RESUMEN:inicio (lo reescribe scripts/generar_informe_tecnico.py) -->
## EP2 en breve: auditoría de cajas 3D sin par 2D de cámara

**Qué es.** Proyecto Kedro sobre Waymo Open Dataset v2 (41 segmentos supervisados: 33 de train y 8 de test sellado).
El target de EP2 es `sin_camara`: una caja 3D etiquetada (`lidar_box`) de un peatón o ciclista, dentro de la zona de cámaras, que no tiene su par 2D.
Comparamos tres modelos (regresión logística, HGB, Random Forest) contra reglas simples basadas en puntos LiDAR.
La validación es por segmento y la evaluación final en test aplica un plan congelado con sha256 (`docs/plan_evaluacion_test.md`).
El análisis completo está en el [informe técnico](informe_tecnico_EP2.md).

**Resultado en 5 líneas.**

1. Train (fuera de fold, población principal): la `Regla: menos puntos top` logra AUC 0,862 y la regresión logística 0,825; ningún modelo supera a la regla con el criterio fijado antes.
2. Test (pre-declarado): AUC 0,698 del modelo frente a 0,684 de la regla; "vale la pena": no se cumple.
3. Punto A de la regla (recall 0,80 en train): recall 0,590 (IC 95 % 0,383 a 0,924) en test; no se sostiene frente a la tolerancia de 0,75.
4. Post hoc (no pre-declarado): un segmento concentra el 54,8 % de los positivos del test; sin él, el recall del punto A es 0,879.
5. Post hoc: la auditoría por cámara en 41 segmentos halló 2 pares (segmento, cámara) con hueco (en test, la cámara 3 (frontal der.)); recomendamos auditar por segmento y cámara y luego priorizar cajas con una persona en el circuito.

**Estructura de carpetas.**

- `conf/`: configuración de Kedro (catálogo y parámetros). `src/`: pipelines de Kedro. `tests/`: pruebas.
- `notebooks/`: notebooks 00 a 10 (y 09b). `scripts/`: `generar_informe_tecnico.py`.
- `data/`: datos y resultados por capa (`01_raw` a `08_reporting`); no está en git (ver `.gitignore`).
- `docs/`: informe técnico, plan de evaluación del test (`plan_evaluacion_test.md`), evaluación final (`evaluacion_final_B.md`), decisiones y log de trabajo.
- `images/`: figuras de los notebooks (prefijo con el número del notebook).

**Orden de ejecución.** `00_exploracion_bucket_waymo.ipynb`, `01_exploracion_csv.ipynb`, `02_exploracion_waymo.ipynb`, `03_fuentes_y_colaboracion.ipynb`, `04_estructuras_y_almacenamiento.ipynb`, `05_etica_sesgos_privacidad.ipynb`, `06_eda_y_preparacion_modelamiento.ipynb`, `07_decision_target_ep2.ipynb`, `08_analisis_observabilidad_sin_camara.ipynb`, `09_modelos_supervisados_sin_camara.ipynb`, `09b_enmiendas_plan_test_v2.ipynb`, `10_evaluacion_final_sin_camara.ipynb`; el 00 solo en Google Colab. Cada notebook usa los archivos que genera el anterior.

**Cómo regenerar el informe técnico** (reescribe `docs/informe_tecnico_EP2.md` y este bloque; requiere haber ejecutado los notebooks):

```
.venv/Scripts/python.exe -X utf8 scripts/generar_informe_tecnico.py
```

Enlaces: [informe técnico](informe_tecnico_EP2.md) · [plan de evaluación del test](plan_evaluacion_test.md) · [evaluación final](evaluacion_final_B.md).
<!-- EP2-RESUMEN:fin -->

## Notebooks del proyecto

| Actividad | Indicador | Notebook |
|-----------|-----------|---------|
| 1.1 Fuentes de datos y trabajo colaborativo | IE1 · 10% | [`03_fuentes_y_colaboracion.ipynb`](../notebooks/03_fuentes_y_colaboracion.ipynb) |
| 1.2 Estructuras de datos y almacenamiento | IE2 · 30% | [`04_estructuras_y_almacenamiento.ipynb`](../notebooks/04_estructuras_y_almacenamiento.ipynb) |
| 1.3 Análisis exploratorio de datos (EDA) | IE3 · 40% | [`01_exploracion_csv.ipynb`](../notebooks/01_exploracion_csv.ipynb) · [`02_exploracion_waymo.ipynb`](../notebooks/02_exploracion_waymo.ipynb) |
| 1.4 Impacto ético, sesgos y privacidad | IE4 · 20% | [`05_etica_sesgos_privacidad.ipynb`](../notebooks/05_etica_sesgos_privacidad.ipynb) |
| Exploración bucket Waymo | Complementario | [`00_exploracion_bucket_waymo.ipynb`](../notebooks/00_exploracion_bucket_waymo.ipynb) ⚠️ Solo ejecutar en Google Colab |

## Estructura de notebooks

| Notebook | Qué cubre |
|---|---|
| [`01_exploracion_csv.ipynb`](../notebooks/01_exploracion_csv.ipynb) | EDA completo del CSV sintético: calidad de datos, distribuciones, relaciones a conservar, tabla de decisiones con 12 defectos y limpieza en funciones puras. |
| [`02_exploracion_waymo.ipynb`](../notebooks/02_exploracion_waymo.ipynb) | EDA de los 4 segmentos reales de Waymo: estructura de `lidar_box`, construcción del target `tiene_camara` cruzando con `camera_to_lidar_box_association`, comparación contra el CSV sintético. |
| [`03_fuentes_y_colaboracion.ipynb`](../notebooks/03_fuentes_y_colaboracion.ipynb) | Clasificación de las fuentes de datos del proyecto (estructurada/semiestructurada, formato, licencia), checklist de privacidad por fuente, y el acuerdo de trabajo colaborativo del equipo. |
| [`04_estructuras_y_almacenamiento.ipynb`](../notebooks/04_estructuras_y_almacenamiento.ipynb) | Por qué el pipeline guarda los datos intermedios en Parquet y no en CSV, con memoria y velocidad medidas sobre los datos reales del proyecto (lista vs NumPy, tipos de columna, CSV vs Parquet). |
| [`05_etica_sesgos_privacidad.ipynb`](../notebooks/05_etica_sesgos_privacidad.ipynb) | Desarrollo en detalle de la sección 7: sesgo de muestreo, de procesamiento y de clase en el target, riesgo de reidentificación, y la ficha de dataset (datasheet) completa. |
| [`06_eda_y_preparacion_modelamiento.ipynb`](../notebooks/06_eda_y_preparacion_modelamiento.ipynb) | EDA y preparación para el modelamiento de `tiene_camara` (EP1): partición por segmentos, baselines y pruebas de modelos en train. |
| [`07_decision_target_ep2.ipynb`](../notebooks/07_decision_target_ep2.ipynb) | Decisión y justificación del target de EP2 (`sin_camara`) frente a otros candidatos, con criterios fijados a priori, problema de negocio y valor práctico. |
| [`08_analisis_observabilidad_sin_camara.ipynb`](../notebooks/08_analisis_observabilidad_sin_camara.ipynb) | Análisis de datos de `sin_camara`: observabilidad, geometría de cámaras, población principal (|azimut| ≤ 100°) y exportación de variables. |
| [`09_modelos_supervisados_sin_camara.ipynb`](../notebooks/09_modelos_supervisados_sin_camara.ipynb) | Modelos supervisados (regresión logística, HGB, Random Forest) frente a baselines, con validación anidada por segmentos, calibración, equidad y plan de evaluación del test congelado. |
| [`10_evaluacion_final_sin_camara.ipynb`](../notebooks/10_evaluacion_final_sin_camara.ipynb) | Evaluación final en el test (primera y única apertura) con el plan v2: resultado principal, puntos de operación, calibración, influencia, equidad, sensibilidad a 120°, test frente a train y recomendaciones. |

## 1. Descripción del problema de negocio

En un sistema de conducción autónoma, el sensor LiDAR detecta objetos en 3D a partir de nubes de puntos, pero esa detección puede incluir falsos positivos (ruido, reflejos, objetos fantasma). La cámara actúa como un validador independiente: si una detección LiDAR también aparece asociada a una detección de cámara, hay mayor certeza de que el objeto es real.

El problema de negocio es **predecir si una detección LiDAR va a tener correspondencia confirmada en cámara**, usando solo los atributos disponibles en el momento de la detección (posición, tamaño, velocidad, tipo de objeto, cantidad de puntos LiDAR). Un modelo que resuelva esto permite priorizar recursos computacionales (por ejemplo, aplicar validación adicional solo a las detecciones que el modelo marca como dudosas) y aumentar la confiabilidad del sistema de percepción sin encarecer el cómputo en tiempo real.

## 2. Objetivos del proyecto

**Objetivo general:** construir un pipeline reproducible de clasificación binaria sobre datos reales de Waymo Open Dataset v2, documentando cada decisión de calidad de datos y de modelamiento con evidencia cuantitativa.

**Objetivos específicos:**

- Realizar el EDA completo del CSV sintético (`detecciones_waymo_like.csv`), identificando y tratando los defectos de calidad inyectados a propósito.
- Realizar el EDA de una muestra real del Waymo Open Dataset v2, contrastando su estructura contra el CSV sintético.
- Comparar cuantitativamente el dataset sintético contra el real, para separar los defectos que son artefactos del generador sintético de los que son propiedades reales del dominio.
- Construir el target binario `tiene_camara` a partir del cruce entre cajas 3D etiquetadas (`lidar_box`) y asociaciones cámara-LiDAR.
- Identificar y documentar los sesgos del dataset (geográfico, climático, de clase) y sus implicaciones éticas antes de pasar a la etapa de modelamiento.

## 3. KPIs

| KPI | Umbral | Motivo |
|---|---|---|
| Recall clase positiva (`tiene_camara=1`) | ≥ 0.85 | Minimizar falsos negativos: una detección LiDAR real que el modelo descarta como "sin respaldo de cámara" es el error más costoso en un contexto de seguridad vial. |
| F1-score | ≥ 0.80 | Balancear precisión y recall dado el desbalance del target (15,7% de positivos con el criterio estricto por frame, ver sección 5). |
| AUC-ROC | ≥ 0.85 | Medir la separación entre clases sin depender de un umbral de decisión fijo, que puede variar por segmento o condición. |
| Brecha de F1 entre segmentos `sunny` y `rain` | ≤ 10 puntos porcentuales | Exigir equidad de desempeño por condición climática, dado que el clima afecta directamente la tasa de positivos del target (sección 7). |

## Actualización de EP2: target `sin_camara` y población principal

El target de EP2 es `sin_camara` (cajas 3D etiquetadas de peatones y ciclistas que no tienen su par 2D de cámara), no el `tiene_camara` de EP1: en train, vehículos y señales nunca son positivos, así que el target de EP1 mezclaba la clase del objeto con la cobertura de cámaras (notebook `07_decision_target_ep2.ipynb`).

**La población principal es |azimut| ≤ 100°** (64.509 de 68.555 filas de la población de 120°). La razón: en 100–120° la tasa de `sin_camara` es 62,2 %, frente a 20,7 % con azimut ≤ 100°, y en el último tramo de 5° (115–120°) llega a 100,0 % (1.133 filas), por lo que la ausencia de par 2D ahí es en buena parte geométrica y no una laguna de etiquetado (notebook `08_analisis_observabilidad_sin_camara.ipynb`, secciones A.6 y A.7). La franja reúne el 5,9 % de las filas. El target y el split no cambian; el borde de 100° es empírico y no se pudo confirmar con la calibración de las cámaras (`camera_calibration` no está en los datos locales).

**Resultado del notebook `09_modelos_supervisados_sin_camara.ipynb`.** En la población principal, el mejor baseline simple (Regla: menos puntos top) tiene AUC 0.862 y Fracción para 80 % 37,8 %; la regresión logística, 0.825 y 43,7 %, y el HGB, 0.805 y 52,9 %. Ningún modelo supera de forma robusta al mejor baseline simple (tampoco en la población de 120°, frente a la regla geométrica), por lo que la recomendación es **Regla: menos puntos top**, por simplicidad y explicabilidad.

## Resultado final en el test de EP2

El notebook [`10_evaluacion_final_sin_camara.ipynb`](../notebooks/10_evaluacion_final_sin_camara.ipynb) abre el test por primera vez y aplica, sin cambios, el plan de evaluación congelado v2 (`docs/plan_evaluacion_test.md`): modelos, umbrales, calibrador, poblaciones, métricas y criterios fijados con train. Se ejecutó 6 veces sobre el test (la primera fue la evaluación pre-declarada; las siguientes corrigieron textos o agregaron los apéndices post hoc L, M y L.7; los 15 CSV de resultados de la primera son idénticos por sha256 en todas). El informe completo está en `docs/evaluacion_final_B.md` y las predicciones en `data/07_model_output/pred_test_B.parquet`.

- **Resultado principal (pre-declarado, población principal, 16.062 filas, 8 segmentos de test):** Regresion logistica tiene AUC 0,698 (IC 0,503 a 0,961) y Fracción para 80 % 77,4 %; Regla: menos puntos top, 0,684 y 79,0 %. Diferencia de AUC +0,014 (IC -0,014 a +0,029); de Fracción para 80 % -1,7 puntos (IC -4,2 a +4,1). **"Vale la pena": no se cumple**; el modelo no se distingue del baseline.
- **Puntos de operación (umbrales congelados):** A de Regresion logistica: recall 0,621 (IC 0,413 a 0,958), precisión 0,406, 35,6 % a revisar; **no se sostiene** (recall ≥ 0,75). B: recall 0,447 con 15,1 % revisado.
- **Influencia (12 cálculos):** diferencia de AUC de -0,004 a +0,020; de Fracción para 80 % de -2,4 a +1,3 puntos. Ningún segmento por sí solo cambia el veredicto.
- **Sensibilidad a 120°:** robusto (lectura literal del plan): ningún modelo; con baselines de train: ningún modelo.
- **Calibración en test (Regresion logistica):** ECE 0,079 crudo y 0,080 con Platt congelado.
- **Equidad descriptiva (recall al punto A de Regla: menos puntos top, sección G):** momento del día: Day 0,495 (6 seg., 10.558 filas) frente a Dawn/Dusk 1,000 (1 seg., 851 filas); ubicación: location_sf 0,515 (3 seg., 11.978 filas) frente a location_other 0,946 (2 seg., 1.850 filas); clase: PEDESTRIAN 0,590 (8 seg., 15.730 filas) frente a CYCLIST 0,667 (2 seg., 332 filas). Con un solo segmento: Dawn/Dusk, Night.
- **Test frente a train:** orden por AUC distinto (hallazgo, sin reajustar).
- **Recomendación (interpretación):** Regla: menos puntos top. **Matices (no cambian la recomendación formal).** El punto A de Regla: menos puntos top no se sostiene en test: recall 0,590 (IC 0,383 a 0,924) frente a la meta de 0,80 y la tolerancia de 0,75. El recall depende fuertemente de un segmento: en el segmento con más positivos (257766998801, 55 % de los positivos) el recall es 0,351 y sin él pasa de 0,590 a 0,879; entre los 4 segmentos con al menos 50 positivos, 3 alcanzan la tolerancia (recall de 0,351 a 0,945). Por eso se sugiere usarlo para priorizar la revisión humana, junto con un monitoreo del recall por segmento, y no como reemplazo de la revisión. (Detalle y diagnóstico post hoc en la sección L.)

### Diagnóstico post hoc, no pre-declarado (sección L; no cambia la recomendación formal)

- El segmento `257766998801` tiene 6.474 filas y 2.046 positivos (54,8 % de los positivos de test); su tasa de `sin_camara` es 31,6 % (otros 7: 17,6 %; train: 20,7 %).
- AUC dentro del segmento: regla por puntos top 0,443 y regresión logística 0,459.
- Cajas sin par con ≥ 100 puntos: 45,7 % en el segmento, 0,1 % en los otros 7 y 4,4 % en train.
- Segmentos de train con AUC de la regla top < 0,55: 2 de 33 (1 con al menos 50 positivos).
- Sin el segmento (7 segmentos): AUC 0,927 (Regresion logistica) y 0,931 (Regla: menos puntos top); 'vale la pena' no se cumple; punto A de Regresion logistica: recall 0,913; 7 de 7 métodos sostienen el punto A (oficial: 0).
- Recall del punto A de Regla: menos puntos top de día (L.7): 0,495 oficial y 0,903 sin el segmento; en San Francisco 0,515 y 0,861.
- **Hipótesis (post hoc, no pre-declarada).** Condición (i): las cajas sin par con al menos 100 puntos son 936 de 2.046 (45,7 %) en el foco frente a 1 de 1.688 (0,1 %) en los otros 7: se cumple. Condición (ii): AUC de la regla por puntos top dentro del segmento 0,443: se cumple. En las cámaras (regla de L.2), la cámara 3 (frontal der.) no tiene ningún par en el segmento (0 de 6.474 cajas del segmento; 2.090 cajas caen dentro de su rango de azimut). La causa puede ser etiquetado 2D faltante o ausencia de datos de esa cámara; con estos archivos no se distinguen. Ambas condiciones se cumplen: una parte importante de las cajas sin par del segmento son objetos bien observados, lo que **sugiere que el problema de este segmento no es la falta de observabilidad LiDAR sino la ausencia de pares en la cámara 3 (frontal der.); si la causa es etiquetado 2D faltante o ausencia de datos de esa cámara no se distingue con estos archivos**. Implicación para el uso de la regla: la regla por puntos sirve mientras la relación entre pocos puntos y ausencia de par 2D se mantenga; **no detecta huecos sistemáticos de etiquetado**, porque esos objetos están bien observados y la regla los ordena como si tuvieran par. Por eso conviene monitorear el recall por segmento. Sin el segmento, el resultado principal sigue sin cumplir 'vale la pena' y 7 de 7 métodos sostienen el punto A (oficial: 0); eso describe cuánto depende el resultado de un solo segmento y no reemplaza el resultado pre-declarado.

### Diagnóstico post hoc M, no pre-declarado (auditoría por cámara en 41 segmentos; no cambia la recomendación formal)

- 2 de 41 segmentos tienen alguna cámara con hueco (1 de train, 1 de test), en 2 pares (segmento, cámara).
- Positivos de la población principal en celdas con hueco: 1,7 % en train y 35,8 % en test.
- Tabla 2x2 exploratoria (hueco frente a AUC de la regla top < 0,55, segmentos con al menos 50 positivos, n = 26): p de Fisher = 0,003 (exploratorio).
- **Hipótesis (post hoc, no pre-declarada).** Con los criterios fijados antes de calcular, **2 de 41 segmentos (5 %) tienen al menos una cámara con hueco** (1 de 33 de train y 1 de 8 de test), en 2 pares (segmento, cámara). Esas celdas reúnen el 1,7 % de los positivos de train y el 35,8 % de los de test de la población principal; es decir, 9,2 % del total de cajas sin par (1.565 de 17.102) se atribuye a unos pocos huecos de cámara y no a la falta de puntos. El segmento de train 911012534050 tiene hueco en 5 (lateral der.). En la tabla 2x2 exploratoria (p de Fisher = 0,003, n = 26), 2 de 2 segmentos con hueco tienen AUC < 0,55, frente a 0 de 24 sin hueco. **Implicación (hipótesis):** una auditoría por segmento y cámara (tasa de pares de cada cámara dentro de su rango de azimut) detecta lo que la regla por puntos no detecta: los huecos afectan a objetos bien observados, que la regla ordena como si tuvieran par. **Aclaración:** un 'hueco' puede ser de etiquetado o de los datos de esa cámara (por ejemplo, una cámara sin imágenes o sin etiquetas 2D en el segmento); con estos archivos no se puede distinguir. Los rangos de azimut son empíricos (de train), no calibración, y los criterios son los fijados antes de calcular. No cambia la recomendación formal ni el resultado pre-declarado.


## 4. Fuentes de datos

| Fuente | Descripción | Volumen | Licencia |
|---|---|---|---|
| `data/01_raw/detecciones_waymo_like.csv` | Dataset sintético, modelado sobre el esquema `lidar_box` de Waymo Open Dataset v2, proporcionado por el docente con defectos de calidad inyectados a propósito para la evaluación. | 40.680 filas × 16 columnas | Uso académico del curso. |
| Waymo Open Dataset v2 (`gs://waymo_open_dataset_v_2_0_1/`) | Datos reales de percepción: componentes `lidar_box` (cajas 3D etiquetadas, `lidar_box`) y `camera_to_lidar_box_association` (asociación entre cajas 3D etiquetadas y cámara). Se descargaron 4 segmentos, elegidos a propósito para maximizar contraste de clima, momento del día y ubicación. | 4 segmentos, 34.098 cajas 3D etiquetadas | No comercial (ver sección 7). |

## 5. Preparación y EDA

El EDA completo vive en dos notebooks; acá solo se resumen los hallazgos principales.

### `notebooks/01_exploracion_csv.ipynb` — CSV sintético

- El CSV crudo tiene 40.680 filas y 16 columnas, con defectos de calidad inyectados a propósito: categorías inconsistentes (`object_type` con 7 etiquetas para 4 clases reales, `weather` con 12 valores para un esquema real de solo `Sunny`/`Rain`), nulos ocultos (texto `"N/D"` en `timestamp_micros`, centinela `-1` en `num_lidar_points`), valores imposibles (`box_length` negativo, `box_height` en cero, velocidades sobre 180 m/s) y 680 filas duplicadas según `segment_id` + `timestamp_micros` + `id_interno`.
- Se detectó y descartó explícitamente la tentación de "limpiar de más": 608 filas de `VEHICLE` con `box_length` > 10 m corresponden a buses y camiones reales (ancho y alto coherentes), no a errores; se conservan.
- El pipeline de limpieza (sección 8 del notebook, implementado en Kedro, ver más abajo) deja el dataset en 39.800 filas y 18 columnas (97,84% del original), preservando 597 de esas 608 filas de vehículos grandes.

### `notebooks/02_exploracion_waymo.ipynb` — Datos reales de Waymo

- Los 4 segmentos reales no traen `weather` ni `time_of_day` como columna de cada caja etiquetada: son metadato de segmento completo. Esto confirma, por el esquema real, un defecto que ya se había identificado por evidencia indirecta en el sintético (ahí `weather`/`time_of_day` variaban dentro de un mismo segmento en el 100% de los 153 segmentos).
- El target `tiene_camara` se construye cruzando `lidar_box` con `camera_to_lidar_box_association` por `segment_id` + `frame_timestamp_micros` + `laser_object_id`, deduplicando primero la tabla de asociación (una misma caja 3D etiquetada puede ser vista por más de una cámara).
- El desbalance de clases de `object_type` es más extremo en datos reales (`CYCLIST` 1,02%) que en el sintético ya limpio (`CYCLIST` 1,95%): no es un artefacto del generador sintético.
- La hipótesis inicial de que `num_lidar_points_in_box` sería la variable más informativa para predecir `tiene_camara` no se sostiene con fuerza: la correlación de Pearson es -0,09 y la de Spearman +0,09 (débiles y de signo contrario). El tamaño de la caja (`box.size.x`, `box.size.y`) correlaciona más fuerte (-0,30/-0,31). Se documentó como hallazgo, no se forzó la hipótesis original.

### Pipeline de preprocesamiento (Kedro)

`src/waymo_evaluacion/pipelines/preprocesamiento` implementa 7 nodos secuenciales que reproducen, de forma reproducible, la limpieza del CSV sintético decidida en el notebook 01:

1. **`convertir_nulos_ocultos`** — castea `timestamp_micros` a numérico convirtiendo `"N/D"` en `NaN`, y convierte el centinela `-1` de `num_lidar_points` en `NaN`.
2. **`normalizar_categorias`** — unifica variantes de mayúscula/español en `object_type` y `weather` (`fog`/`niebla` se mantiene como categoría propia, no verificada contra el esquema real).
3. **`eliminar_columnas_sin_varianza`** — elimina columnas con un único valor (p. ej. `sensor_version`), protegiendo `weather` y `time_of_day` vía `params:preprocesamiento.columnas_protegidas` para que nunca se borren en silencio si su varianza cae a 0 en otro corte de datos.
4. **`eliminar_duplicados_logicos`** — elimina duplicados según `[segment_id, timestamp_micros, id_interno]`.
5. **`filtrar_valores_imposibles`** — elimina `box_length`/`box_height` ≤ 0, aplica un techo preventivo a `box_height` y convierte `speed_mps` por sobre el umbral en `NaN` sin descartar la fila.
6. **`crear_variables_derivadas`** — agrega `distancia_m`, `volumen_caja` y `densidad_puntos`.
7. **`resumen_calidad`** — compara dataset crudo vs. limpio y lo persiste como reporte.

Los umbrales (`altura_maxima_m=6.0`, `velocidad_maxima_mps=50.0`, `columnas_protegidas`) están en `conf/base/parameters.yml`, con comentarios que trazan cada valor a la celda del notebook 01 que lo justifica.

| Dataset del catálogo | Tipo | Ruta |
|---|---|---|
| `detecciones_crudas` | `pandas.CSVDataset` | `data/01_raw/detecciones_waymo_like.csv` |
| `detecciones_limpias` | `pandas.ParquetDataset` | `data/02_intermediate/detecciones_limpias.parquet` |
| `resumen_calidad` | `pandas.CSVDataset` | `data/08_reporting/resumen_calidad.csv` |

## 6. Metodología CRISP-DM

| Fase | Qué se hizo en este proyecto |
|---|---|
| **Business Understanding** | Definición del problema de negocio (sección 1): predecir si una detección LiDAR será confirmada por cámara, para priorizar recursos de validación en un sistema de percepción autónoma. |
| **Data Understanding** | EDA del CSV sintético (`01_exploracion_csv.ipynb`) y de los datos reales de Waymo (`02_exploracion_waymo.ipynb`), incluyendo comparación directa entre ambas fuentes. |
| **Data Preparation** | Pipeline de Kedro con 7 nodos (`preprocesamiento`), que limpia el CSV sintético de forma reproducible y deja funciones puras listas para reutilizarse sobre los datos reales. Construcción del target binario `tiene_camara` mediante el cruce `lidar_box` / `camera_to_lidar_box_association`. |
| **Modeling** | Pendiente para EP2. Propuesta: Random Forest o XGBoost como líneas base, con SMOTE (u otra técnica de sobremuestreo) para compensar el desbalance del target (15,7% de positivos) y de `object_type` (`CYCLIST` 1,02%). |
| **Evaluation** | KPIs definidos en la sección 3 (Recall, F1, AUC-ROC, brecha de equidad `sunny` vs. `rain`), a evaluar sobre un conjunto de prueba separado por segmento para evitar fuga de información entre frames del mismo objeto. |
| **Deployment** | Pipeline reproducible con Kedro (`kedro run`), catálogo de datos versionado en `conf/base/catalog.yml`, datos crudos de Waymo excluidos del repositorio vía `.gitignore` por su licencia no comercial (ver sección 7). |

## 7. Ética, sesgos y privacidad

Este proyecto usa una muestra pequeña y deliberadamente sesgada del Waymo Open Dataset v2, y es importante documentar esos sesgos con cifras antes de pasar a la etapa de modelamiento, para no heredar conclusiones que no se sostienen fuera de este contexto.

**Sesgo geográfico.** Los 798 segmentos del conjunto de entrenamiento de Waymo provienen de solo 3 ubicaciones: San Francisco (409 segmentos, 51,3%), Phoenix (284 segmentos, 35,6%) y una tercera categoría agregada como "location_other" (105 segmentos, 13,2%). Las tres son ciudades de Estados Unidos: no hay segmentos de Latinoamérica, Europa, ni de entornos con señalización, densidad de tráfico o comportamiento vial distintos al estadounidense. Un modelo entrenado exclusivamente sobre estos datos no debería asumirse transferible, sin validación adicional, a la conducción en Chile u otro país con infraestructura vial diferente.

**Sesgo de captura climático.** De los 798 segmentos, 793 (99,4%) tienen `weather = sunny`; solo 5 segmentos (0,6%) tienen lluvia. Esto no es un detalle menor para el problema de negocio de este proyecto: el segmento con lluvia de nuestra muestra tiene la menor tasa de asociación LiDAR-cámara (2,4%), contra 32,4% en el segmento `sunny`/`Day`/San Francisco. El clima afecta directamente al target que se busca predecir. Un modelo entrenado mayoritariamente en condiciones soleadas va a tener peor desempeño en lluvia, que es exactamente la condición en la que más se necesita un sistema de percepción confiable, porque la visibilidad de la cámara ya está degradada por el clima.

**Desbalance de clases.** En los datos reales, `CYCLIST` representa solo 1,02% de las cajas 3D etiquetadas; en el CSV sintético ya limpio, 1,95%. El desbalance es una propiedad real del dominio, no un artefacto del generador sintético, y es más extremo en los datos reales. Los ciclistas son uno de los grupos más vulnerables en el tráfico: un modelo que los clasifica mal, o que recibe menos señal de entrenamiento sobre ellos por su escasa representación, tiene consecuencias de seguridad directas y no solo un costo de métrica. El target binario `tiene_camara` también está desbalanceado (15,7% de positivos con el criterio estricto por frame), lo que exige atención en el diseño del modelo (técnicas de remuestreo, métricas apropiadas) y no solo maximizar accuracy.

**Privacidad.** Waymo aplica anonimización automática sobre las imágenes de cámara (`camera_image`): rostros y patentes quedan difuminados antes de la publicación del dataset. Los componentes que este proyecto usa (`lidar_box`, `camera_to_lidar_box_association`) son coordenadas 3D y metadatos de cajas etiquetadas, no contienen información directamente identificable de personas. Sin embargo, la trayectoria de un peatón a lo largo de varios frames de un mismo segmento sí podría, en principio, reconstruir un patrón de movimiento de una persona en un espacio público, incluso sin datos biométricos directos. Este riesgo es menor en nuestro alcance (4 segmentos, 20 segundos cada uno, sin identidad asociada), pero se documenta como consideración de diseño para cualquier extensión del proyecto que use más segmentos o los cruce con otras fuentes.

**Decisión técnica y licencia.** La licencia del Waymo Open Dataset es de uso no comercial y prohíbe explícitamente redistribuir los datos. Por eso `data/01_raw/waymo/` está excluido en `.gitignore`: no es solo una práctica de higiene de repositorio, es la forma en que este proyecto cumple con esa restricción de licencia sin dejar de ser reproducible (ver sección 9 para el procedimiento de descarga).

**Limitaciones del dataset.** La muestra de este proyecto son solo 4 segmentos, que no son representativos del dataset completo de Waymo; y el dataset completo de Waymo tampoco es representativo del mundo real, por los sesgos geográfico y climático ya descritos. No existe, dentro de los 798 segmentos de entrenamiento, ninguna combinación de noche con lluvia: la condición más exigente para un sistema de percepción no está cubierta. Los datos tienen fecha de 2019: la infraestructura vial, el volumen de tráfico y el comportamiento de otros actores viales han cambiado desde entonces, lo que limita la vigencia de cualquier conclusión de largo plazo basada solo en este dataset.

## 8. Herramientas colaborativas

| Herramienta | Uso en el proyecto | Justificación |
|---|---|---|
| **GitHub** | Repositorio con ramas separadas por integrante (`maicolhernandez`, `francismoya`) sobre `main`. | Permite trabajo paralelo sin bloquear a la otra persona, con historial de commits trazable por autor para la evaluación individual. |
| **Kedro 1.5.0** | Framework de pipeline: catálogo de datos declarativo (`conf/base/catalog.yml`), parámetros versionados (`conf/base/parameters.yml`) y nodos como funciones puras testeables. | Separa la lógica de transformación de la configuración (rutas, umbrales), y hace que la limpieza documentada en los notebooks sea ejecutable y reproducible con `kedro run`, no solo un ejercicio de exploración. |
| **Google Colab** | Exploración inicial del bucket de Waymo (`gs://waymo_open_dataset_v_2_0_1/`) y selección de los 4 segmentos de contraste. | Da acceso a cómputo y a las credenciales de Google Cloud necesarias para listar y descargar del bucket público de Waymo sin depender del entorno local. |

## 9. Instrucciones de reproducción

1. **Clonar el repositorio:**

   ```
   git clone <url-del-repositorio>
   cd waymo-evaluacion
   ```

2. **Instalar dependencias** (idealmente en un entorno virtual):

   ```
   pip install -r requirements.txt
   ```

3. **Aceptar los términos del Waymo Open Dataset** en `waymo.com/open` y descargar los 4 segmentos usados en este proyecto desde `gs://waymo_open_dataset_v_2_0_1/`, componentes `lidar_box` y `camera_to_lidar_box_association`:

   - `10206293520369375008_2796_800_2816_800`
   - `11017034898130016754_697_830_717_830`
   - `6791933003490312185_2607_000_2627_000`
   - `10023947602400723454_1120_000_1140_000`

   Ubicar los archivos descargados como:

   ```
   data/01_raw/waymo/lidar_box/<segment_id>.parquet
   data/01_raw/waymo/camera_to_lidar_box_association/<segment_id>.parquet
   ```

   Estos archivos no se distribuyen en este repositorio por la licencia no comercial de Waymo (ver sección 7); `data/01_raw/waymo/` está en `.gitignore` a propósito.

4. **Ejecutar el pipeline de preprocesamiento:**

   ```
   kedro run
   ```

   Esto genera `data/02_intermediate/detecciones_limpias.parquet` y `data/08_reporting/resumen_calidad.csv`.

5. **Ejecutar los notebooks, en este orden:**

   ```
   kedro jupyter notebook
   ```

   - `notebooks/00_exploracion_bucket_waymo.ipynb` (opcional — solo en Google Colab, documenta la selección de segmentos)
   - `notebooks/01_exploracion_csv.ipynb`
   - `notebooks/02_exploracion_waymo.ipynb`
   - `notebooks/03_fuentes_y_colaboracion.ipynb`
   - `notebooks/04_estructuras_y_almacenamiento.ipynb`
   - `notebooks/05_etica_sesgos_privacidad.ipynb`
