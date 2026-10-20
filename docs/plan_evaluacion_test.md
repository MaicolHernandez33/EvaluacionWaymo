# Plan de evaluación del test (v2, congelado)

**Congelado el 2026-10-18T13:42:13-03:00.** Plan v2 congelado antes de abrir el test (enmienda del v1, conservado como plan_evaluacion_test_v1). El test no se usa para elegir modelos, umbrales, hiperparametros, la comparacion principal ni el baseline principal.

El plan v1 se conserva en `plan_evaluacion_test_v1.md` y `data/06_models/plan_evaluacion_test_v1.json`.

## Cambios entre v1 y v2 y por qué (todos hechos antes de abrir el test)

1. **Modelos de la sensibilidad a 120°.** En v1 la sensibilidad usaba los modelos entrenados en la población principal. Ahora hay modelos congelados entrenados sobre toda la población de 120° de train (`*_B120.joblib`), con los mismos hiperparámetros finales del 09 (sin nueva búsqueda) y umbrales fijados con predicciones internas fuera de fold de esa población. Motivo: que la sensibilidad compare modelos entrenados en la población que evalúa.
2. **Comparación principal pre-declarada.** Se declara una sola comparación principal: población principal (|azimut| ≤ 100°), modelo Regresion logistica (el mejor modelo aprendido según la prueba de elección del 09, leído de `hiperparametros_B.json`) frente a la Regla: menos puntos top (el mejor baseline simple elegido en train), con el criterio 'vale la pena' del 09. Todo lo demás es secundario. Motivo: evitar elegir la comparación después de ver el test.
3. **El mejor baseline del test sale del criterio principal.** En v1 el mejor baseline simple se elegía por AUC del test. Ahora el criterio principal usa el baseline elegido en train, y 'qué baseline habría sido el mejor en test' es un análisis de sensibilidad separado. Motivo: no usar el test para elegir contra qué se compara.
4. **Punto A sostenido.** El punto A se considera sostenido si el recall puntual en test es ≥ 0,75; se reporta además el % de frames revisados frente al de train. El punto B se reporta sin tolerancia. No se recalibra ni se mueve ningún umbral. Motivo: fijar de antemano qué se entiende por sostenido.
5. **Calibración en test.** Descriptiva: ECE, Brier y curva de confiabilidad del mejor modelo aprendido con el calibrador congelado. Motivo: saber si las probabilidades publicadas conservarían su significado.
6. **Análisis de influencia.** Se repite la comparación principal excluyendo cada uno de los dos segmentos más grandes, ambos, y leave-one-segment-out (8 resultados), con el rango. Motivo: con 8 segmentos y dos que concentran la mayor parte de las filas, el resultado puede depender de uno solo.
7. **Equidad descriptiva.** Por ubicación, momento del día y clase, con número de segmentos y filas, recall al punto A y AUC solo con ≥ 200 filas por clase, sin pruebas de hipótesis. Motivo: describir sin sobreinterpretar grupos de un solo segmento.
8. **Tabla de diferencias con train.** Para cada método: AUC, Fracción para 80 %, recall y % revisado en el punto A, en test frente al OOF de train. Motivo: ver qué cambia entre train y test y por qué.
9. **Congelamiento v2.** El plan v1 se conserva (`plan_evaluacion_test_v1.*`); este es el v2, con nuevos sha256 (incluidos los `*_B120.joblib`) y nuevo sello de fecha y hora.

**Contradicciones con el 09:** El 09 comparaba contra el mejor baseline simple de la poblacion evaluada; el plan v2 fija el baseline principal (regla por puntos top, elegido en train) y deja el mejor baseline de test como sensibilidad separada. Es un cambio de plan, no un cambio de resultados.

## 1. Comparación principal (pre-declarada)

- **poblacion:** principal: peatones y ciclistas con |azimut| <= 100
- **modelo:** Regresion logistica
- **archivo modelo:** data/06_models/lr_B.joblib
- **baseline:** Regla: menos puntos top
- **puntaje baseline:** -num_top_lidar_points
- **criterio vale la pena:** la Fraccion para 80 % del modelo baja >= 5 puntos frente al baseline, con IC 95 % pareado por bootstrap de segmentos de test que excluya 0, y el AUC sube >= 0,03 (identico al criterio del 09)
- **fuente del modelo:** campo recomendado_modelo de data/06_models/hiperparametros_B.json (resultado de la prueba de eleccion del 09; no se elige de nuevo)
- **todo lo demas:** secundario: otros modelos, la poblacion de 120 grados y otras metricas se reportan como secundarios

La conclusión principal del notebook 10 sale únicamente de esta comparación. Los demás modelos, la población de 120° y las demás métricas se reportan como **secundarios**.

## 2. Sensibilidad separada: qué baseline habría sido el mejor en test

analisis separado: que baseline simple habria sido el mejor en test (mayor AUC en cada poblacion) y como cambia la comparacion; no entra en el criterio principal.

## 3. Puntos de operación

- **A:** recall objetivo 0,80 fijado con train; se considera sostenido en test si el recall puntual es >= 0,75; se reporta tambien el % de frames revisados frente al de train
- **B:** revisar el 20 % mejor puntuado segun el corte fijado con train; se reporta sin tolerancia
- **regla:** no se recalibra ni se mueve ningun umbral

## 4. Calibración en test (descriptiva)

Modelo Regresion logistica con el calibrador congelado (`data/06_models/calibrador_B.joblib`, versión que ganó en train: Platt): ECE (10 bins por cuantiles), Brier y curva de confiabilidad. Descriptivo, sin umbral de aceptación.

## 5. Análisis de influencia

- Comparación: AUC y Fraccion para 80 % del modelo menos el baseline (poblacion principal).
- Segmentos más grandes: 257766998801, 221704303323 (filas y positivos en la población principal: 221704303323: 4653 y 918; 257766998801: 6474 y 2046).
- Variantes: excluir cada segmento grande; excluir ambos; leave-one-segment-out (8 resultados).
- Se reporta el rango de los resultados.
- solo en segmentos con >= 50 positivos en la poblacion principal: ['141430544948', '221704303323', '257766998801', '645616575015']; el resto cuenta solo en los agregados.

## 6. Equidad descriptiva

Numero de segmentos y filas por grupo, recall al punto a; auc solo si el grupo tiene >= 200 filas por clase. Sin pruebas de hipótesis.

**Night y Dawn/Dusk tienen un solo segmento cada uno en el test (segmentos por momento del dia: {'Dawn/Dusk': 1, 'Day': 6, 'Night': 1}); por ubicacion: {'location_other': 2, 'location_phx': 3, 'location_sf': 3}. La equidad por momento del dia es descriptiva de un segmento por grupo.**

## 7. Diferencias con train

Tabla a completar en el notebook 10: para cada método, AUC, Fracción para 80 %, recall y % revisado en el punto A, en test frente a la referencia de train (OOF de la población principal, abajo).

| metodo | AUC (OOF agrupado) | PR-AUC | Fraccion para 80 % | recall A | precision A | % revisado A | recall B | % revisado B |
|---|---|---|---|---|---|---|---|---|
| Regla: menos puntos LiDAR | 0.858 | 0.698 | 0.385 | 0.804 | 0.433 | 0.385 | 0.660 | 0.209 |
| Regla: menos puntos top | 0.862 | 0.704 | 0.378 | 0.806 | 0.441 | 0.379 | 0.665 | 0.210 |
| Regla geometrica (azimut > 105 primero) | 0.858 | 0.698 | 0.385 | 0.804 | 0.433 | 0.385 | 0.660 | 0.209 |
| Modelo minimo (LR 3 variables) | 0.855 | 0.702 | 0.384 | 0.799 | 0.455 | 0.364 | 0.654 | 0.203 |
| Regresion logistica | 0.825 | 0.657 | 0.437 | 0.810 | 0.431 | 0.389 | 0.644 | 0.204 |
| HGB | 0.805 | 0.655 | 0.529 | 0.800 | 0.423 | 0.392 | 0.645 | 0.204 |
| Random Forest | 0.836 | 0.690 | 0.430 | 0.793 | 0.424 | 0.387 | 0.650 | 0.209 |

En test cada modelo es unico y congelado (no hay mezcla de escalas entre folds), por lo que sus metricas agrupadas no sufren el sesgo del OOF agrupado de train (cinco modelos distintos, uno por fold). Esto puede hacer que los modelos se vean mejor en test que en el 09; la tabla de diferencias debe leerse con esa advertencia.

## 8. Métodos, archivos y umbrales

| método | tipo | archivo | umbral A | umbral B | umbral F1 | sha256 |
|---|---|---|---|---|---|---|
| Regla: menos puntos LiDAR | regla | (regla, sin archivo) | -25 | -10 | -10 | - |
| Regla: menos puntos top | regla | (regla, sin archivo) | -24 | -10 | -10 | - |
| Regla geometrica (azimut > 105 primero) | regla (solo distinta de la de puntos en la poblacion de 120) | (regla, sin archivo) | -25 | -10 | -10 | - |
| Modelo minimo (LR 3 variables) | modelo minimo | data/06_models/lr_minimo_B.joblib | 0.1611 | 0.325 | 0.3431 | d5dabd6c6b074a28... |
| Regresion logistica | modelo | data/06_models/lr_B.joblib | 0.1456 | 0.3214 | 0.3432 | 993c2f2bbace25f0... |
| HGB | modelo | data/06_models/hgb_B.joblib | 0.129 | 0.2877 | 0.3032 | ac8328046919c4ad... |
| Random Forest | modelo | data/06_models/rf_B.joblib | 0.1266 | 0.3068 | 0.3134 | b990648ec16b3b5d... |
| Regresion logistica (120 grados) | modelo (sensibilidad) | data/06_models/lr_B120.joblib | 0.1623 | 0.3663 | 0.3162 | f4c80b104d4a157e... |
| HGB (120 grados) | modelo (sensibilidad) | data/06_models/hgb_B120.joblib | 0.1359 | 0.3712 | 0.3702 | 37ea6400a7b32816... |
| Random Forest (120 grados) | modelo (sensibilidad) | data/06_models/rf_B120.joblib | 0.125 | 0.375 | 0.3664 | cd9a0fc66f8975a3... |
| Modelo minimo (120 grados) | modelo minimo (sensibilidad) | data/06_models/lr_minimo_B120.joblib | 0.1625 | 0.3722 | 0.3448 | 545bfac46ae29424... |

Umbrales de las reglas en la población de 120° (con train):

| regla | puntaje | umbral A | umbral B | umbral F1 |
|---|---|---|---|---|
| Regla: menos puntos LiDAR | -num_lidar_points | -39 | -11 | -10 |
| Regla: menos puntos top | -num_top_lidar_points | -38 | -10 | -10 |
| Regla geometrica (azimut > 105 primero) | 1e6*(azimut_abs_deg > 105) - num_lidar_points | -20 | -8 | -9 |

Los umbrales de las reglas son sobre su puntaje; los de los modelos, sobre la probabilidad predicha. Los modelos de la población principal se entrenaron y fijaron sus umbrales en la población principal; los `(120 grados)`, en toda la población de 120°.

## 9. Poblaciones, métricas, criterios y redacción

- **Principal:** peatones y ciclistas con |azimut| <= 100 en frames etiquetados.
- **Sensibilidad:** toda B (|azimut| <= 120); se evalúan los modelos `(120 grados)` y las reglas.
- **Métricas:** AUC; PR-AUC; Captura@20 %; Fraccion para 80 %; recall, precision y % de frames a revisar en el punto A (recall objetivo 0,80) y en el punto B (20 % de revision).
- **Intervalos:** IC 95 % por bootstrap de segmentos de test (diferencias pareadas); con 8 segmentos los intervalos seran anchos y se reportaran como tales.

**Criterios (idénticos a los del 09):**

- **valer la pena:** la Fraccion para 80 % del modelo baja >= 5 puntos frente al mejor baseline simple, con IC 95 % pareado que excluya 0, y el AUC sube >= 0,03
- **robusto:** vale la pena en la poblacion principal y en la de sensibilidad, cada una frente al mejor baseline simple de esa poblacion
- **mejor baseline simple:** el de mayor AUC entre Regla: menos puntos LiDAR, Regla geometrica (azimut > 105 primero), Modelo minimo (LR 3 variables), Regla: menos puntos top en la poblacion evaluada (empates por ese orden); ademas se muestra la comparacion contra el baseline elegido en train (Regla: menos puntos top)

**Lectura complementaria:** diagnostico por fold y por segmento del 09 (C.2): diferencia modelo menos regla de puntos por segmento de test (mediana, IQR, proporcion de segmentos donde el modelo supera, IC 95 % de la mediana). No reemplaza los criterios.

**Cómo se redactará la conclusión en cada caso:**

- **ningun modelo supera al mejor baseline:** Se reporta que ningun modelo cumple 'vale la pena' frente al mejor baseline simple y que el baseline es suficiente por simplicidad y explicabilidad. Si el IC por segmentos incluye 0 se escribe 'no se distingue del baseline', no 'es peor'.
- **algun modelo supera:** Se reporta el modelo y la magnitud (AUC y Fraccion para 80 % con IC), se comprueba si tambien es robusto en la otra poblacion y se compara contra el baseline elegido en train; se recomienda el modelo solo si es robusto.
- **discrepancia entre poblaciones:** Si el resultado difiere entre la poblacion principal y la de 120 grados, se reportan ambos sin elegir uno a conveniencia, y se explica la diferencia con la franja 100-120 (ausencia de par 2D en buena parte geometrica).
- **diferencias con train:** Si el orden de los metodos en test difiere del de train, se reporta como hallazgo; no se reentrena ni se cambian umbrales.

## 10. Reglas

- El test no se usa para elegir modelos, umbrales, hiperparametros, comparacion principal ni baseline principal.
- Los modelos, umbrales y calibrador se aplican tal como estan congelados, sin reajuste.
- Cualquier desviacion de este plan se documenta en el notebook 10 con su motivo.
- Las poblaciones, metricas y criterios son los de este plan; no se agregan metricas despues de ver el test.
- Los analisis secundarios y de sensibilidad se reportan como tales y no cambian la conclusion principal.

## 11. Composición conocida del test (solo conteos)

| segment_id | location | time_of_day | filas_B_120 | sin_camara_120 | filas_B_principal | sin_camara_principal | filas_en_franja | sin_en_franja |
|---|---|---|---|---|---|---|---|---|
| 102124064984 | location_sf | Dawn/Dusk | 882 | 65 | 851 | 48 | 31 | 17 |
| 141430544948 | location_other | Day | 1695 | 280 | 1654 | 256 | 41 | 24 |
| 167359384489 | location_other | Day | 203 | 3 | 196 | 2 | 7 | 1 |
| 221704303323 | location_sf | Night | 4932 | 1062 | 4653 | 918 | 279 | 144 |
| 257766998801 | location_sf | Day | 6837 | 2298 | 6474 | 2046 | 363 | 252 |
| 497181704156 | location_phx | Day | 384 | 29 | 369 | 16 | 15 | 13 |
| 645616575015 | location_phx | Day | 2170 | 631 | 1710 | 445 | 460 | 186 |
| 703836276130 | location_phx | Day | 194 | 10 | 155 | 3 | 39 | 7 |

Totales: filas_B_120 = 17.297, sin_camara_120 = 4.378, filas_B_principal = 16.062, sin_camara_principal = 3.734, filas_en_franja = 1.235, sin_en_franja = 644. Segmentos con ≥ 50 positivos en la población principal: 141430544948, 221704303323, 257766998801, 645616575015.

## 12. Sumas de verificación (sha256)

- `hiperparametros_B.json`: `dbf1c7d275dea216be9dea6e06bb1386c0bd646a9f9e73ff719591324aac43ba`
- `config_features_B.json`: `c81ed082c26b3d8618213c0e33a2aa02925c20514b5415fb9e8af6a8e637f2c1`
- `calibrador_B.joblib`: `685e46723e88e80e9390066e800258ac93d8d4de7819a09acdaff54b717e5a3f`
- `lr_minimo_B.joblib`: `d5dabd6c6b074a2865b413d9c25a0d9b4689d0973c8518e579b70a7ecc97e5b4`
- `lr_B.joblib`: `993c2f2bbace25f02b7e4e98bc4df1caf2e1b45bd37424e68107d6af67391c61`
- `hgb_B.joblib`: `ac8328046919c4ad9d4421260816ef4364805980d4786b1a0fcf9d9c414a8cdd`
- `rf_B.joblib`: `b990648ec16b3b5d9d10ae73e875436058349221ccc9d0163b8cfb12fdd86d09`
- `lr_B120.joblib`: `f4c80b104d4a157ee7a593ec963211583852f8cd4cdfc831695cc91647214e6e`
- `hgb_B120.joblib`: `37ea6400a7b328163b7c1fe2636bd3a0e1fae989a5db8ce24eb7de6a41b7dc8c`
- `rf_B120.joblib`: `cd9a0fc66f8975a38f10b01a0f9f1f23e9e96ab63d02a492032c05bd547e5479`
- `lr_minimo_B120.joblib`: `545bfac46ae294240068fa23d1799bfd6d7772a0a91293ebde3ff10fc4c0d3f7`
- `hiperparametros_B120.json`: `421ed63cf989c8d27cf51c56a11f6fe99f25e9a9fe3088f06f2007bd9de2adab`
- `features_B.parquet`: `4cb6af91da2bc6b9bc70e291ee020ac6d5c435569f0a4a3b0f97b47bd78c4856`
- `plan_evaluacion_test_v1.json`: `e4188b80a33fad5981a84d7dee8f756cd6c9bb43676454d328cf52f73e00a7a8`
