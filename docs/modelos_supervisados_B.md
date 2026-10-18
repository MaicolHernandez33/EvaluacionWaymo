### Modelos supervisados para `sin_camara` (notebook 09)

Solo segmentos de train y los folds existentes; el test no se usó. Población principal: |azimut| ≤ 100° (64.509 filas de 68.555); la de 120° es sensibilidad. Criterios fijados antes de correr (celda inicial del notebook).

**Comparación fuera de fold, población principal (IC 95 % por segmentos)**

| modelo | AUC | PR-AUC | Captura@20% | Fraccion para 80% |
|---|---|---|---|---|
| Prevalencia (trivial) | 0.500 (0.500 a 0.500) | 0.207 (0.167 a 0.245) | 0.199 (0.194 a 0.202) | 0.802 (0.795 a 0.807) |
| Regla: menos puntos LiDAR | 0.858 (0.810 a 0.901) | 0.698 (0.580 a 0.778) | 0.646 (0.575 a 0.738) | 0.385 (0.275 a 0.471) |
| Regla: menos puntos top | 0.862 (0.814 a 0.906) | 0.704 (0.597 a 0.785) | 0.649 (0.580 a 0.741) | 0.378 (0.266 a 0.467) |
| Regla geometrica (azimut > 105 primero) | 0.858 (0.810 a 0.901) | 0.698 (0.580 a 0.778) | 0.646 (0.575 a 0.738) | 0.385 (0.275 a 0.471) |
| Modelo minimo (LR 3 variables) | 0.855 (0.800 a 0.906) | 0.702 (0.573 a 0.798) | 0.636 (0.555 a 0.741) | 0.384 (0.266 a 0.478) |
| Regresion logistica | 0.825 (0.774 a 0.883) | 0.657 (0.553 a 0.755) | 0.581 (0.500 a 0.708) | 0.437 (0.309 a 0.523) |
| HGB | 0.805 (0.753 a 0.871) | 0.655 (0.562 a 0.746) | 0.589 (0.498 a 0.709) | 0.529 (0.326 a 0.623) |
| Random Forest | 0.836 (0.779 a 0.893) | 0.690 (0.556 a 0.791) | 0.620 (0.532 a 0.719) | 0.430 (0.283 a 0.533) |

**Conclusión**

1. **Recomendación final: Regla: menos puntos top.** Ningún modelo es robusto frente al mejor baseline simple: el mejor modelo (Regresion logistica) no vale la pena en la población principal y no vale la pena en la de 120°. Se recomienda el baseline simple **Regla: menos puntos top** por simplicidad y explicabilidad; los modelos quedan como comparación. En la población principal el mejor modelo (Regresion logistica) tiene AUC 0,825, PR-AUC 0,657, Captura@20 % 58,1 % y Fracción para 80 % 43,7 %; el baseline (Regla: menos puntos top), AUC 0,862 y Fracción para 80 % 37,8 %. Diferencia modelo menos baseline: AUC -0.036 (IC -0.056 a -0.007) y Fracción para 80 % +5.8 puntos (IC -0.8 a +10.6).
2. Estabilidad del mejor modelo (Regresion logistica): AUC mínimo por fold 0,811 y mediana del AUC por segmento 0,888 → cumple los umbrales fijados.
3. Punto A (recall 0,80 fijado con train, mejor modelo Regresion logistica): recall 0,810 (IC 0,761 a 0,874), precisión 0,431, 38,9 % de los frames a revisar; el baseline (Regla: menos puntos top) con el mismo método revisa el 37,9 % para un recall de 0,806.
4. Calibración: ECE crudo 0,044; mejor versión Platt con ECE 0,013 (cumple el umbral de 0,05).
5. Interpretación: variables principales de la regresión logística `num_top_lidar_points`, `num_lidar_points`, `densidad_puntos`; del HGB `num_top_lidar_points`, `speed_mps`, `distancia_m`. La lectura no coincide del todo con el análisis de datos del 08.
6. Sensibilidad (población de 120°, 68.555 filas): mejor baseline simple Regla geometrica (azimut > 105 primero); modelos que valen la pena frente a él: ninguno; robustos: ninguno.
7. Diagnóstico (C.2): la brecha agrupada de AUC entre modelo y regla de puntos es mucho mayor que la brecha por fold y por segmento; por fold y por segmento los IC incluyen 0 para Regresion logistica, HGB, Random Forest, así que **el modelo no se distingue de la regla de puntos**. Frente al mejor baseline simple (Regla: menos puntos top): Regresion logistica: el modelo no se distingue de la regla; HGB: la evidencia es mixta (un IC incluye 0 y el otro no); Random Forest: el modelo no se distingue de la regla. El veredicto de los criterios fijados antes (frente al mejor baseline simple: Regresion logistica: no vale la pena, HGB: no vale la pena, Random Forest: no vale la pena) no cambia: lo que cambia es su alcance, porque «no vale la pena» no equivale a «es peor».

**Sensibilidad: población de 120°**

| metodo | poblacion | AUC | PR-AUC | Captura@20% | Fraccion para 80% |
|---|---|---|---|---|---|
| Prevalencia (trivial) | 120 (toda B) | 0.500 (0.500 a 0.500) | 0.232 (0.192 a 0.272) | 0.197 (0.190 a 0.204) | 0.802 (0.799 a 0.805) |
| Regla: menos puntos LiDAR | 120 (toda B) | 0.797 (0.748 a 0.847) | 0.661 (0.555 a 0.735) | 0.579 (0.507 a 0.665) | 0.505 (0.405 a 0.607) |
| Regla geometrica (azimut > 105 primero) | 120 (toda B) | 0.862 (0.821 a 0.900) | 0.689 (0.601 a 0.755) | 0.639 (0.571 a 0.726) | 0.368 (0.262 a 0.443) |
| Modelo minimo (LR 3 variables) | 120 (toda B) | 0.831 (0.775 a 0.889) | 0.689 (0.580 a 0.783) | 0.578 (0.493 a 0.685) | 0.437 (0.307 a 0.536) |
| Regla: menos puntos top | 120 (toda B) | 0.800 (0.751 a 0.852) | 0.668 (0.561 a 0.743) | 0.582 (0.510 a 0.669) | 0.499 (0.394 a 0.602) |
| Regresion logistica | 120 (toda B) | 0.826 (0.773 a 0.884) | 0.678 (0.574 a 0.779) | 0.576 (0.497 a 0.684) | 0.440 (0.313 a 0.529) |
| HGB | 120 (toda B) | 0.852 (0.807 a 0.901) | 0.724 (0.616 a 0.817) | 0.631 (0.557 a 0.728) | 0.415 (0.267 a 0.509) |
| Random Forest | 120 (toda B) | 0.850 (0.803 a 0.901) | 0.729 (0.623 a 0.816) | 0.630 (0.551 a 0.731) | 0.416 (0.262 a 0.512) |

**Puntos de operación (población principal, fuera de fold, umbrales fijados con train)**

| metodo | punto | TP | FP | FN | TN | recall | precision | F1 | pct_revisar |
|---|---|---|---|---|---|---|---|---|---|
| Regla: menos puntos top | A: recall objetivo 0,80 | 10774 | 13660 | 2594 | 37481 | 0.806 (0.760 a 0.869) | 0.441 (0.346 a 0.519) | 0.570 (0.483 a 0.637) | 0.379 (0.340 a 0.422) |
| Regla: menos puntos top | B: revisar 20 % | 8896 | 4666 | 4472 | 46475 | 0.665 (0.602 a 0.745) | 0.656 (0.510 a 0.744) | 0.661 (0.578 a 0.730) | 0.210 (0.182 a 0.244) |
| Regla: menos puntos top | referencia: maximo F1 | 8506 | 4213 | 4862 | 46928 | 0.636 (0.563 a 0.726) | 0.669 (0.523 a 0.764) | 0.652 (0.570 a 0.722) | 0.197 (0.175 a 0.225) |
| Regresion logistica | A: recall objetivo 0,80 | 10830 | 14269 | 2538 | 36872 | 0.810 (0.761 a 0.874) | 0.431 (0.339 a 0.516) | 0.563 (0.477 a 0.630) | 0.389 (0.352 a 0.438) |
| Regresion logistica | B: revisar 20 % | 8607 | 4553 | 4761 | 46588 | 0.644 (0.569 a 0.741) | 0.654 (0.511 a 0.749) | 0.649 (0.568 a 0.726) | 0.204 (0.177 a 0.234) |
| Regresion logistica | referencia: maximo F1 | 8265 | 4269 | 5103 | 46872 | 0.618 (0.533 a 0.720) | 0.659 (0.523 a 0.759) | 0.638 (0.557 a 0.714) | 0.194 (0.171 a 0.219) |
| HGB | A: recall objetivo 0,80 | 10688 | 14598 | 2680 | 36543 | 0.800 | 0.423 | 0.553 | 0.392 |
| HGB | B: revisar 20 % | 8627 | 4505 | 4741 | 46636 | 0.645 | 0.657 | 0.651 | 0.204 |
| HGB | referencia: maximo F1 | 7851 | 3330 | 5517 | 47811 | 0.587 | 0.702 | 0.640 | 0.173 |
| Random Forest | A: recall objetivo 0,80 | 10596 | 14400 | 2772 | 36741 | 0.793 | 0.424 | 0.552 | 0.387 |
| Random Forest | B: revisar 20 % | 8692 | 4821 | 4676 | 46320 | 0.650 | 0.643 | 0.647 | 0.209 |
| Random Forest | referencia: maximo F1 | 7926 | 4135 | 5442 | 47006 | 0.593 | 0.657 | 0.623 | 0.187 |

**Qué se lleva al 10**

- Se llevan al 10 los modelos ajustados sobre todo train en la población principal (`data/06_models/lr_B.joblib, hgb_B.joblib, calibrador_B.joblib, lr_minimo_B.joblib, rf_B.joblib`), el calibrador y los umbrales A, B y F1 fijados con train (en `hiperparametros_B.json`, para los modelos y para el baseline), **sin reajuste** en test.
- La recomendación final es **Regla: menos puntos top**; el mejor baseline simple (Regla: menos puntos top) y el modelo mínimo se evalúan en test como referencia obligatoria.
- El plan de evaluación del test queda congelado en `data/06_models/plan_evaluacion_test.json` y `docs/plan_evaluacion_test.md` (sección J), con las sumas de verificación de los modelos.

**Limitaciones**

- La etiqueta mide cobertura de etiquetado, no visibilidad física de la cámara.
- La población principal (|azimut| ≤ 100°) excluye 4.046 filas (5,9 %) cuya ausencia de par 2D es en buena parte geométrica; el borde de 100° es empírico y no se pudo confirmar con la calibración de las cámaras (`camera_calibration` no está disponible localmente).
- Los folds se estratificaron por `tiene_camara`, no por `sin_camara` en la zona de cámaras; la prevalencia varía entre folds.
- Pocos ciclistas (1.483 filas en la población principal): las métricas por clase son frágiles.
- La composición del test se conoce solo por conteos (8 segmentos, con un solo segmento Night y uno Dawn/Dusk); la equidad por momento del día se midió con los folds de train.
- SMOTE y SHAP no se usaron porque `imbalanced-learn` y `shap` no están instalados.
- La búsqueda de hiperparámetros es acotada: Regresion logistica: 16, 16, 16, 16, 16 configuraciones reales por fold (ajuste final: 16); HGB: 12, 12, 12, 12, 12 configuraciones reales por fold (ajuste final: 12); Random Forest: 6, 6, 6, 6, 6 configuraciones reales por fold (ajuste final: 6). Es una búsqueda aleatoria sobre un espacio limitado (con grilla para la regresión logística), no exhaustiva.
- El AUC agrupado mezcla cinco modelos distintos (uno por fold); por eso se agregó el diagnóstico por fold y por segmento (C.2): que un modelo «no valga la pena» frente al baseline según los criterios fijados no equivale a que sea peor.

**Preguntas abiertas para el 10**

- ¿Se sostiene en test la conclusión sobre el mejor baseline simple y los modelos, dado que el test tiene 8 segmentos con un etiquetado muy desigual?
- ¿Qué punto de operación (A, B o F1) se adopta, y con qué costo de revisión real (el supuesto de 20 s por revisión no es un dato)?
- ¿Se confirma el borde de 100° con la calibración de las cámaras (`camera_calibration`)?
- ¿Cómo se reporta la equidad por momento del día con un solo segmento Night y uno Dawn/Dusk en el test?
