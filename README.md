# Waymo Evaluación

[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)

Proyecto de clasificación binaria sobre datos de percepción de vehículos autónomos, construido con Kedro 1.5.0 sobre un CSV sintético (esquema Waymo v2) y una muestra real descargada del Waymo Open Dataset v2.

## Estructura de notebooks

| Notebook | Qué cubre |
|---|---|
| [`01_exploracion_csv.ipynb`](notebooks/01_exploracion_csv.ipynb) | EDA completo del CSV sintético: calidad de datos, distribuciones, relaciones a conservar, tabla de decisiones con 12 defectos y limpieza en funciones puras. |
| [`02_exploracion_waymo.ipynb`](notebooks/02_exploracion_waymo.ipynb) | EDA de los 4 segmentos reales de Waymo: estructura de `lidar_box`, construcción del target `tiene_camara` cruzando con `camera_to_lidar_box_association`, comparación contra el CSV sintético. |
| [`03_fuentes_y_colaboracion.ipynb`](notebooks/03_fuentes_y_colaboracion.ipynb) | Clasificación de las fuentes de datos del proyecto (estructurada/semiestructurada, formato, licencia), checklist de privacidad por fuente, y el acuerdo de trabajo colaborativo del equipo. |
| [`04_estructuras_y_almacenamiento.ipynb`](notebooks/04_estructuras_y_almacenamiento.ipynb) | Por qué el pipeline guarda los datos intermedios en Parquet y no en CSV, con memoria y velocidad medidas sobre los datos reales del proyecto (lista vs NumPy, tipos de columna, CSV vs Parquet). |
| [`05_etica_sesgos_privacidad.ipynb`](notebooks/05_etica_sesgos_privacidad.ipynb) | Desarrollo en detalle de la sección 7: sesgo de muestreo, de procesamiento y de clase en el target, riesgo de reidentificación, y la ficha de dataset (datasheet) completa. |
| `06_presentacion.ipynb` | Resumen visual de cierre del proyecto (pendiente, todavía no creado). |

## 1. Descripción del problema de negocio

En un sistema de conducción autónoma, el sensor LiDAR detecta objetos en 3D a partir de nubes de puntos, pero esa detección puede incluir falsos positivos (ruido, reflejos, objetos fantasma). La cámara actúa como un validador independiente: si una detección LiDAR también aparece asociada a una detección de cámara, hay mayor certeza de que el objeto es real.

El problema de negocio es **predecir si una detección LiDAR va a tener correspondencia confirmada en cámara**, usando solo los atributos disponibles en el momento de la detección (posición, tamaño, velocidad, tipo de objeto, cantidad de puntos LiDAR). Un modelo que resuelva esto permite priorizar recursos computacionales (por ejemplo, aplicar validación adicional solo a las detecciones que el modelo marca como dudosas) y aumentar la confiabilidad del sistema de percepción sin encarecer el cómputo en tiempo real.

## 2. Objetivos del proyecto

**Objetivo general:** construir un pipeline reproducible de clasificación binaria sobre datos reales de Waymo Open Dataset v2, documentando cada decisión de calidad de datos y de modelamiento con evidencia cuantitativa.

**Objetivos específicos:**

- Realizar el EDA completo del CSV sintético (`detecciones_waymo_like.csv`), identificando y tratando los defectos de calidad inyectados a propósito.
- Realizar el EDA de una muestra real del Waymo Open Dataset v2, contrastando su estructura contra el CSV sintético.
- Comparar cuantitativamente el dataset sintético contra el real, para separar los defectos que son artefactos del generador sintético de los que son propiedades reales del dominio.
- Construir el target binario `tiene_camara` a partir del cruce entre detecciones LiDAR y asociaciones cámara-LiDAR.
- Identificar y documentar los sesgos del dataset (geográfico, climático, de clase) y sus implicaciones éticas antes de pasar a la etapa de modelamiento.

## 3. KPIs

| KPI | Umbral | Motivo |
|---|---|---|
| Recall clase positiva (`tiene_camara=1`) | ≥ 0.85 | Minimizar falsos negativos: una detección LiDAR real que el modelo descarta como "sin respaldo de cámara" es el error más costoso en un contexto de seguridad vial. |
| F1-score | ≥ 0.80 | Balancear precisión y recall dado el desbalance del target (15,7% de positivos con el criterio estricto por frame, ver sección 5). |
| AUC-ROC | ≥ 0.85 | Medir la separación entre clases sin depender de un umbral de decisión fijo, que puede variar por segmento o condición. |
| Brecha de F1 entre segmentos `sunny` y `rain` | ≤ 10 puntos porcentuales | Exigir equidad de desempeño por condición climática, dado que el clima afecta directamente la tasa de positivos del target (sección 7). |

## 4. Fuentes de datos

| Fuente | Descripción | Volumen | Licencia |
|---|---|---|---|
| `data/01_raw/detecciones_waymo_like.csv` | Dataset sintético, modelado sobre el esquema `lidar_box` de Waymo Open Dataset v2, proporcionado por el docente con defectos de calidad inyectados a propósito para la evaluación. | 40.680 filas × 16 columnas | Uso académico del curso. |
| Waymo Open Dataset v2 (`gs://waymo_open_dataset_v_2_0_1/`) | Datos reales de percepción: componentes `lidar_box` (cajas 3D detectadas por LiDAR) y `camera_to_lidar_box_association` (asociación entre detecciones LiDAR y cámara). Se descargaron 4 segmentos, elegidos a propósito para maximizar contraste de clima, momento del día y ubicación. | 4 segmentos, 34.098 detecciones LiDAR | No comercial (ver sección 7). |

## 5. Preparación y EDA

El EDA completo vive en dos notebooks; acá solo se resumen los hallazgos principales.

### `notebooks/01_exploracion_csv.ipynb` — CSV sintético

- El CSV crudo tiene 40.680 filas y 16 columnas, con defectos de calidad inyectados a propósito: categorías inconsistentes (`object_type` con 7 etiquetas para 4 clases reales, `weather` con 12 valores para un esquema real de solo `Sunny`/`Rain`), nulos ocultos (texto `"N/D"` en `timestamp_micros`, centinela `-1` en `num_lidar_points`), valores imposibles (`box_length` negativo, `box_height` en cero, velocidades sobre 180 m/s) y 680 filas duplicadas según `segment_id` + `timestamp_micros` + `id_interno`.
- Se detectó y descartó explícitamente la tentación de "limpiar de más": 608 filas de `VEHICLE` con `box_length` > 10 m corresponden a buses y camiones reales (ancho y alto coherentes), no a errores; se conservan.
- El pipeline de limpieza (sección 8 del notebook, implementado en Kedro, ver más abajo) deja el dataset en 39.800 filas y 18 columnas (97,84% del original), preservando 597 de esas 608 filas de vehículos grandes.

### `notebooks/02_exploracion_waymo.ipynb` — Datos reales de Waymo

- Los 4 segmentos reales no traen `weather` ni `time_of_day` como columna de la detección individual: son metadato de segmento completo. Esto confirma, por el esquema real, un defecto que ya se había identificado por evidencia indirecta en el sintético (ahí `weather`/`time_of_day` variaban dentro de un mismo segmento en el 100% de los 153 segmentos).
- El target `tiene_camara` se construye cruzando `lidar_box` con `camera_to_lidar_box_association` por `segment_id` + `frame_timestamp_micros` + `laser_object_id`, deduplicando primero la tabla de asociación (una misma detección puede ser vista por más de una cámara).
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

**Desbalance de clases.** En los datos reales, `CYCLIST` representa solo 1,02% de las detecciones; en el CSV sintético ya limpio, 1,95%. El desbalance es una propiedad real del dominio, no un artefacto del generador sintético, y es más extremo en los datos reales. Los ciclistas son uno de los grupos más vulnerables en el tráfico: un modelo que los clasifica mal, o que recibe menos señal de entrenamiento sobre ellos por su escasa representación, tiene consecuencias de seguridad directas y no solo un costo de métrica. El target binario `tiene_camara` también está desbalanceado (15,7% de positivos con el criterio estricto por frame), lo que exige atención en el diseño del modelo (técnicas de remuestreo, métricas apropiadas) y no solo maximizar accuracy.

**Privacidad.** Waymo aplica anonimización automática sobre las imágenes de cámara (`camera_image`): rostros y patentes quedan difuminados antes de la publicación del dataset. Los componentes que este proyecto usa (`lidar_box`, `camera_to_lidar_box_association`) son coordenadas 3D y metadatos de detección, no contienen información directamente identificable de personas. Sin embargo, la trayectoria de un peatón a lo largo de varios frames de un mismo segmento sí podría, en principio, reconstruir un patrón de movimiento de una persona en un espacio público, incluso sin datos biométricos directos. Este riesgo es menor en nuestro alcance (4 segmentos, 20 segundos cada uno, sin identidad asociada), pero se documenta como consideración de diseño para cualquier extensión del proyecto que use más segmentos o los cruce con otras fuentes.

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

   - `notebooks/01_exploracion_csv.ipynb`
   - `notebooks/02_exploracion_waymo.ipynb`
   - `notebooks/03_fuentes_y_colaboracion.ipynb`
   - `notebooks/04_estructuras_y_almacenamiento.ipynb`
   - `notebooks/05_etica_sesgos_privacidad.ipynb`
