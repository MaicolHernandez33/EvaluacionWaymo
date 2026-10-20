# Plan de evaluación del test (congelado)

**Congelado el 2026-10-18T13:09:50-03:00.** Plan congelado antes de abrir el test. El test no se usa para elegir modelos, umbrales ni hiperparametros.

## Métodos a evaluar (lista cerrada)

| método | tipo | archivo | umbral A | umbral B | umbral F1 | sha256 |
|---|---|---|---|---|---|---|
| Regla: menos puntos LiDAR | regla | (regla, sin archivo) | -25 | -10 | -10 | - |
| Regla: menos puntos top | regla | (regla, sin archivo) | -24 | -10 | -10 | - |
| Regla geometrica (azimut > 105 primero) | regla (solo distinta de la de puntos en la poblacion de 120) | (regla, sin archivo) | -25 | -10 | -10 | - |
| Modelo minimo (LR 3 variables) | modelo minimo | data/06_models/lr_minimo_B.joblib | 0.1611 | 0.325 | 0.3431 | d5dabd6c6b074a28... |
| Regresion logistica | modelo | data/06_models/lr_B.joblib | 0.1456 | 0.3214 | 0.3432 | 993c2f2bbace25f0... |
| HGB | modelo | data/06_models/hgb_B.joblib | 0.129 | 0.2877 | 0.3032 | ac8328046919c4ad... |
| Random Forest | modelo | data/06_models/rf_B.joblib | 0.1266 | 0.3068 | 0.3134 | b990648ec16b3b5d... |

Los umbrales de las reglas son sobre su puntaje; los de los modelos, sobre la probabilidad predicha. Todos se fijaron con train.

## Poblaciones

- **Principal:** peatones y ciclistas con |azimut| <= 100 en frames etiquetados.
- **Sensibilidad:** toda B (|azimut| <= 120).
- los modelos congelados se entrenaron en la poblacion principal y se evaluan en ambas poblaciones sin reentrenar.

## Métricas e intervalos

- AUC
- PR-AUC
- Captura@20 %
- Fraccion para 80 %
- recall, precision y % de frames a revisar en el punto A (recall objetivo 0,80) y en el punto B (20 % de revision)

IC 95 % por bootstrap de segmentos de test (diferencias pareadas); con 8 segmentos los intervalos seran anchos y se reportaran como tales.

## Criterios (idénticos a los del 09)

- **valer la pena:** la Fraccion para 80 % del modelo baja >= 5 puntos frente al mejor baseline simple, con IC 95 % pareado que excluya 0, y el AUC sube >= 0,03
- **robusto:** vale la pena en la poblacion principal y en la de sensibilidad, cada una frente al mejor baseline simple de esa poblacion
- **mejor baseline simple:** el de mayor AUC entre Regla: menos puntos LiDAR, Regla geometrica (azimut > 105 primero), Modelo minimo (LR 3 variables), Regla: menos puntos top en la poblacion evaluada (empates por ese orden); ademas se muestra la comparacion contra el baseline elegido en train (Regla: menos puntos top)

**Lectura complementaria:** diagnostico por fold y por segmento del 09 (C.2): diferencia modelo menos regla de puntos por segmento de test (mediana, IQR, proporcion de segmentos donde el modelo supera, IC 95 % de la mediana). No reemplaza los criterios.

## Cómo se redactará la conclusión en cada caso

- **ningun modelo supera al mejor baseline:** Se reporta que ningun modelo cumple 'vale la pena' frente al mejor baseline simple y que el baseline es suficiente por simplicidad y explicabilidad. Si el IC por segmentos incluye 0 se escribe 'no se distingue del baseline', no 'es peor'.
- **algun modelo supera:** Se reporta el modelo y la magnitud (AUC y Fraccion para 80 % con IC), se comprueba si tambien es robusto en la otra poblacion y se compara contra el baseline elegido en train; se recomienda el modelo solo si es robusto.
- **discrepancia entre poblaciones:** Si el resultado difiere entre la poblacion principal y la de 120 grados, se reportan ambos sin elegir uno a conveniencia, y se explica la diferencia con la franja 100-120 (ausencia de par 2D en buena parte geometrica).
- **diferencias con train:** Si el orden de los metodos en test difiere del de train, se reporta como hallazgo; no se reentrena ni se cambian umbrales.

## Reglas

- El test no se usa para elegir modelos, umbrales ni hiperparametros.
- Los modelos, umbrales y calibrador se aplican tal como estan congelados, sin reajuste.
- Cualquier desviacion de este plan se documenta en el notebook 10 con su motivo.
- Las poblaciones, metricas y criterios son los de este plan; no se agregan metricas despues de ver el test.

## Composición conocida del test (solo conteos)

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

Totales: filas_B_120 = 17.297, sin_camara_120 = 4.378, filas_B_principal = 16.062, sin_camara_principal = 3.734, filas_en_franja = 1.235, sin_en_franja = 644.

## Sumas de verificación (sha256)

- `hiperparametros_B.json`: `dbf1c7d275dea216be9dea6e06bb1386c0bd646a9f9e73ff719591324aac43ba`
- `config_features_B.json`: `c81ed082c26b3d8618213c0e33a2aa02925c20514b5415fb9e8af6a8e637f2c1`
- `calibrador_B.joblib`: `685e46723e88e80e9390066e800258ac93d8d4de7819a09acdaff54b717e5a3f`
- `lr_minimo_B.joblib`: `d5dabd6c6b074a2865b413d9c25a0d9b4689d0973c8518e579b70a7ecc97e5b4`
- `lr_B.joblib`: `993c2f2bbace25f02b7e4e98bc4df1caf2e1b45bd37424e68107d6af67391c61`
- `hgb_B.joblib`: `ac8328046919c4ad9d4421260816ef4364805980d4786b1a0fcf9d9c414a8cdd`
- `rf_B.joblib`: `b990648ec16b3b5d9d10ae73e875436058349221ccc9d0163b8cfb12fdd86d09`
- `features_B.parquet`: `4cb6af91da2bc6b9bc70e291ee020ac6d5c435569f0a4a3b0f97b47bd78c4856`
