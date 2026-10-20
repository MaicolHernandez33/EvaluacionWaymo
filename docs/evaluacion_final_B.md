# Evaluación final en el test (`sin_camara`)

Generado por `notebooks/10_evaluacion_final_sin_camara.ipynb` aplicando el plan congelado v2 (`docs/plan_evaluacion_test.md`). Sin cambios al plan, modelos, umbrales, criterios ni métricas.

### Resumen ejecutivo (generado por código)

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

## Resultado principal

| metodo | AUC | PR-AUC | Captura@20% | Fraccion para 80% |
|---|---|---|---|---|
| Regresion logistica | 0.698 (0.503 a 0.961) | 0.565 (0.451 a 0.826) | 0.517 (0.364 a 0.887) | 0.774 (0.154 a 0.884) |
| Regla: menos puntos top | 0.684 (0.482 a 0.958) | 0.558 (0.430 a 0.795) | 0.503 (0.346 a 0.875) | 0.790 (0.148 a 0.883) |

**Caso del plan: `ningun_modelo_supera_al_mejor_baseline`.** Se reporta que ningun modelo cumple 'vale la pena' frente al mejor baseline simple y que el baseline es suficiente por simplicidad y explicabilidad. Si el IC por segmentos incluye 0 se escribe 'no se distingue del baseline', no 'es peor'. En test (población principal, 16.062 filas, 8 segmentos), Regresion logistica frente a Regla: menos puntos top: AUC 0,698 contra 0,684 (diferencia +0,014, IC 95 % -0,014 a +0,029) y Fracción para 80 % 77,4 % contra 79,0 % (diferencia -1,7 puntos, IC -4,2 a +4,1). El criterio 'vale la pena' (Fracción para 80 % baja ≥ 5 puntos con IC que excluye 0 y AUC sube ≥ 0,03) **no se cumple**. Los IC de ambas diferencias incluyen 0: **el modelo no se distingue del baseline**.

## Todos los métodos (población principal)

| metodo | AUC | PR-AUC | Captura@20% | Fraccion para 80% |
|---|---|---|---|---|
| Regla: menos puntos LiDAR | 0.683 (0.481 a 0.957) | 0.557 (0.429 a 0.793) | 0.502 (0.346 a 0.875) | 0.801 (0.153 a 0.884) |
| Regla: menos puntos top | 0.684 (0.482 a 0.958) | 0.558 (0.430 a 0.795) | 0.503 (0.346 a 0.875) | 0.790 (0.148 a 0.883) |
| Regla geometrica (azimut > 105 primero) | 0.683 (0.481 a 0.957) | 0.557 (0.429 a 0.793) | 0.502 (0.346 a 0.875) | 0.801 (0.153 a 0.884) |
| Modelo minimo (LR 3 variables) | 0.685 (0.487 a 0.957) | 0.556 (0.441 a 0.789) | 0.497 (0.347 a 0.867) | 0.786 (0.156 a 0.886) |
| Regresion logistica | 0.698 (0.503 a 0.961) | 0.565 (0.451 a 0.826) | 0.517 (0.364 a 0.887) | 0.774 (0.154 a 0.884) |
| HGB | 0.679 (0.514 a 0.953) | 0.578 (0.459 a 0.807) | 0.510 (0.348 a 0.865) | 0.821 (0.153 a 0.864) |
| Random Forest | 0.686 (0.512 a 0.955) | 0.586 (0.463 a 0.814) | 0.515 (0.346 a 0.841) | 0.760 (0.158 a 0.909) |

## Puntos de operación

| metodo | punto | umbral | TP | FP | FN | TN | recall | precision | F1 | pct_revisar | % revisado en train (OOF) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Regla: menos puntos LiDAR | A (recall objetivo 0,80) | -25 | 2214 | 3246 | 1520 | 9082 | 0.593 (0.387 a 0.931) | 0.405 (0.297 a 0.555) | 0.482 (0.338 a 0.680) | 0.340 (0.246 a 0.410) | 0.385 |
| Regla: menos puntos LiDAR | B (20 % de revision) | -10 | 1749 | 911 | 1985 | 11417 | 0.468 (0.329 a 0.781) | 0.658 (0.559 a 0.791) | 0.547 (0.414 a 0.755) | 0.166 (0.127 a 0.206) | 0.209 |
| Regla: menos puntos LiDAR | referencia: maximo F1 | -10 | 1749 | 911 | 1985 | 11417 | 0.468 (0.329 a 0.781) | 0.658 (0.559 a 0.791) | 0.547 (0.414 a 0.755) | 0.166 (0.127 a 0.206) | - |
| Regla: menos puntos top | A (recall objetivo 0,80) | -24 | 2202 | 3113 | 1532 | 9215 | 0.590 (0.383 a 0.924) | 0.414 (0.303 a 0.567) | 0.487 (0.340 a 0.689) | 0.331 (0.238 a 0.397) | 0.379 |
| Regla: menos puntos top | B (20 % de revision) | -10 | 1752 | 911 | 1982 | 11417 | 0.469 (0.331 a 0.783) | 0.658 (0.559 a 0.790) | 0.548 (0.414 a 0.757) | 0.166 (0.128 a 0.205) | 0.210 |
| Regla: menos puntos top | referencia: maximo F1 | -10 | 1752 | 911 | 1982 | 11417 | 0.469 (0.331 a 0.783) | 0.658 (0.559 a 0.790) | 0.548 (0.414 a 0.757) | 0.166 (0.128 a 0.205) | - |
| Regla geometrica (azimut > 105 primero) | A (recall objetivo 0,80) | -25 | 2214 | 3246 | 1520 | 9082 | 0.593 (0.387 a 0.931) | 0.405 (0.297 a 0.555) | 0.482 (0.338 a 0.680) | 0.340 (0.246 a 0.410) | 0.385 |
| Regla geometrica (azimut > 105 primero) | B (20 % de revision) | -10 | 1749 | 911 | 1985 | 11417 | 0.468 (0.329 a 0.781) | 0.658 (0.559 a 0.791) | 0.547 (0.414 a 0.755) | 0.166 (0.127 a 0.206) | 0.209 |
| Regla geometrica (azimut > 105 primero) | referencia: maximo F1 | -10 | 1749 | 911 | 1985 | 11417 | 0.468 (0.329 a 0.781) | 0.658 (0.559 a 0.791) | 0.547 (0.414 a 0.755) | 0.166 (0.127 a 0.206) | - |
| Modelo minimo (LR 3 variables) | A (recall objetivo 0,80) | 0.1611 | 2186 | 2837 | 1548 | 9491 | 0.585 (0.383 a 0.924) | 0.435 (0.327 a 0.587) | 0.499 (0.357 a 0.703) | 0.313 (0.225 a 0.401) | 0.364 |
| Modelo minimo (LR 3 variables) | B (20 % de revision) | 0.325 | 1659 | 791 | 2075 | 11537 | 0.444 (0.320 a 0.770) | 0.677 (0.603 a 0.804) | 0.537 (0.421 a 0.738) | 0.153 (0.115 a 0.214) | 0.203 |
| Modelo minimo (LR 3 variables) | referencia: maximo F1 | 0.3431 | 1604 | 696 | 2130 | 11632 | 0.430 (0.311 a 0.743) | 0.697 (0.626 a 0.820) | 0.532 (0.419 a 0.727) | 0.143 (0.107 a 0.204) | - |
| Regresion logistica | A (recall objetivo 0,80) | 0.1456 | 2320 | 3400 | 1414 | 8928 | 0.621 (0.413 a 0.958) | 0.406 (0.316 a 0.543) | 0.491 (0.362 a 0.685) | 0.356 (0.257 a 0.449) | 0.389 |
| Regresion logistica | B (20 % de revision) | 0.3214 | 1668 | 758 | 2066 | 11570 | 0.447 (0.305 a 0.776) | 0.688 (0.588 a 0.829) | 0.542 (0.413 a 0.742) | 0.151 (0.113 a 0.224) | 0.204 |
| Regresion logistica | referencia: maximo F1 | 0.3432 | 1588 | 642 | 2146 | 11686 | 0.425 (0.291 a 0.758) | 0.712 (0.611 a 0.846) | 0.533 (0.409 a 0.734) | 0.139 (0.104 a 0.213) | - |
| HGB | A (recall objetivo 0,80) | 0.129 | 2362 | 3397 | 1372 | 8931 | 0.633 (0.445 a 0.921) | 0.410 (0.338 a 0.476) | 0.498 (0.387 a 0.624) | 0.359 (0.288 a 0.414) | 0.392 |
| HGB | B (20 % de revision) | 0.2877 | 1656 | 734 | 2078 | 11594 | 0.443 (0.303 a 0.734) | 0.693 (0.609 a 0.797) | 0.541 (0.406 a 0.739) | 0.149 (0.117 a 0.190) | 0.204 |
| HGB | referencia: maximo F1 | 0.3032 | 1605 | 673 | 2129 | 11655 | 0.430 (0.295 a 0.727) | 0.705 (0.623 a 0.810) | 0.534 (0.402 a 0.735) | 0.142 (0.111 a 0.185) | - |
| Random Forest | A (recall objetivo 0,80) | 0.1266 | 2270 | 3098 | 1464 | 9230 | 0.608 (0.419 a 0.906) | 0.423 (0.343 a 0.506) | 0.499 (0.383 a 0.646) | 0.334 (0.258 a 0.392) | 0.387 |
| Random Forest | B (20 % de revision) | 0.3068 | 1604 | 616 | 2130 | 11712 | 0.430 (0.300 a 0.717) | 0.723 (0.658 a 0.812) | 0.539 (0.412 a 0.729) | 0.138 (0.107 a 0.182) | 0.209 |
| Random Forest | referencia: maximo F1 | 0.3134 | 1582 | 599 | 2152 | 11729 | 0.424 (0.296 a 0.715) | 0.725 (0.659 a 0.816) | 0.535 (0.409 a 0.732) | 0.136 (0.106 a 0.180) | - |

## Influencia

| variante | segmentos | filas | dAUC | IC dAUC | dFraccion80 (puntos) | IC dF80 | vale la pena |
|---|---|---|---|---|---|---|---|
| todos los segmentos | 8 | 16062 | 0.014 | -0.014 a +0.028 | -1.656 | -4,1 a +4,1 | False |
| sin 257766998801 | 7 | 9588 | -0.004 | -0.020 a +0.011 | 1.335 | -0,8 a +7,8 | False |
| sin 221704303323 | 7 | 11409 | 0.019 | -0.019 a +0.034 | -1.376 | -3,1 a +7,7 | False |
| sin los dos mas grandes | 6 | 4935 | -0.001 | -0.021 a +0.015 | 1.155 | -0,9 a +8,1 | False |
| leave-one-out: sin 102124064984 | 7 | 15211 | 0.015 | -0.017 a +0.032 | -2.373 | -4,0 a +5,8 | False |
| leave-one-out: sin 141430544948 | 7 | 14408 | 0.009 | -0.020 a +0.018 | -1.798 | -2,8 a +7,5 | False |
| leave-one-out: sin 167359384489 | 7 | 15866 | 0.013 | -0.017 a +0.030 | -1.311 | -3,8 a +5,4 | False |
| leave-one-out: sin 221704303323 | 7 | 11409 | 0.019 | -0.019 a +0.034 | -1.376 | -3,1 a +7,7 | False |
| leave-one-out: sin 257766998801 | 7 | 9588 | -0.004 | -0.020 a +0.011 | 1.335 | -0,8 a +7,8 | False |
| leave-one-out: sin 497181704156 | 7 | 15693 | 0.014 | -0.016 a +0.029 | -2.02 | -4,1 a +5,5 | False |
| leave-one-out: sin 645616575015 | 7 | 14352 | 0.02 | -0.002 a +0.033 | -2.313 | -4,0 a +0,8 | False |
| leave-one-out: sin 703836276130 | 7 | 15907 | 0.013 | -0.014 a +0.027 | -1.672 | -4,2 a +4,1 | False |

## Equidad descriptiva

| metodo | variable | grupo | segmentos | filas | sin_camara | AUC | recall A | precision A | % revisado A |
|---|---|---|---|---|---|---|---|---|---|
| Regresion logistica | location | location_other | 2 | 1850 | 258 | 0.979 | 0.992 | 0.573 | 0.242 |
| Regresion logistica | location | location_phx | 3 | 2234 | 464 | 0.862 | 0.899 | 0.333 | 0.56 |
| Regresion logistica | location | location_sf | 3 | 11978 | 3012 | 0.65 | 0.547 | 0.409 | 0.336 |
| Regresion logistica | time_of_day | Dawn/Dusk | 1 | 851 | 48 | nan | 1.0 | 0.623 | 0.09 |
| Regresion logistica | time_of_day | Day | 6 | 10558 | 2768 | 0.589 | 0.525 | 0.35 | 0.393 |
| Regresion logistica | time_of_day | Night | 1 | 4653 | 918 | 0.933 | 0.893 | 0.55 | 0.32 |
| Regresion logistica | object_type | CYCLIST | 2 | 332 | 3 | nan | 0.667 | 0.667 | 0.009 |
| Regresion logistica | object_type | PEDESTRIAN | 8 | 15730 | 3731 | 0.692 | 0.621 | 0.405 | 0.363 |
| Regla: menos puntos top | location | location_other | 2 | 1850 | 258 | 0.967 | 0.946 | 0.542 | 0.243 |
| Regla: menos puntos top | location | location_phx | 3 | 2234 | 464 | 0.878 | 0.879 | 0.392 | 0.466 |
| Regla: menos puntos top | location | location_sf | 3 | 11978 | 3012 | 0.637 | 0.515 | 0.405 | 0.319 |
| Regla: menos puntos top | time_of_day | Dawn/Dusk | 1 | 851 | 48 | nan | 1.0 | 0.762 | 0.074 |
| Regla: menos puntos top | time_of_day | Day | 6 | 10558 | 2768 | 0.568 | 0.495 | 0.348 | 0.372 |
| Regla: menos puntos top | time_of_day | Night | 1 | 4653 | 918 | 0.937 | 0.854 | 0.594 | 0.284 |
| Regla: menos puntos top | object_type | CYCLIST | 2 | 332 | 3 | nan | 0.667 | 0.4 | 0.015 |
| Regla: menos puntos top | object_type | PEDESTRIAN | 8 | 15730 | 3731 | 0.681 | 0.59 | 0.414 | 0.338 |

## Sensibilidad a 120°

| metodo | AUC | PR-AUC | Captura@20% | Fraccion para 80% |
|---|---|---|---|---|
| Regla: menos puntos LiDAR | 0.639 (0.449 a 0.876) | 0.534 (0.420 a 0.736) | 0.458 (0.318 a 0.770) | 0.833 (0.239 a 0.884) |
| Regla: menos puntos top | 0.640 (0.450 a 0.877) | 0.535 (0.420 a 0.738) | 0.459 (0.317 a 0.770) | 0.832 (0.234 a 0.882) |
| Regla geometrica (azimut > 105 primero) | 0.707 (0.530 a 0.951) | 0.541 (0.474 a 0.712) | 0.526 (0.401 a 0.879) | 0.770 (0.161 a 0.874) |
| Modelo minimo (LR 3 variables) | 0.687 (0.528 a 0.923) | 0.513 (0.442 a 0.697) | 0.433 (0.332 a 0.767) | 0.735 (0.218 a 0.884) |
| Regresion logistica | 0.712 (0.563 a 0.929) | 0.525 (0.466 a 0.751) | 0.445 (0.344 a 0.815) | 0.685 (0.188 a 0.877) |
| HGB | 0.726 (0.566 a 0.962) | 0.645 (0.537 a 0.838) | 0.532 (0.401 a 0.866) | 0.719 (0.157 a 0.822) |
| Random Forest | 0.722 (0.578 a 0.956) | 0.646 (0.543 a 0.837) | 0.528 (0.398 a 0.861) | 0.724 (0.164 a 0.842) |

| modelo | base | dAUC | dFraccion80 (puntos) | vale la pena |
|---|---|---|---|---|
| Regresion logistica | Regla geometrica (azimut > 105 primero) | +0.005 (-0.054 a +0.042) | -8,5 (-10,1 a +14,3) | no |
| Regresion logistica | Regla: menos puntos top | +0.072 (-0.012 a +0.124) | -14,7 (-20,7 a +2,4) | no |
| HGB | Regla geometrica (azimut > 105 primero) | +0.019 (+0.007 a +0.040) | -5,0 (-8,6 a +1,2) | no |
| HGB | Regla: menos puntos top | +0.085 (+0.062 a +0.117) | -11,3 (-18,3 a -4,2) | si |
| Random Forest | Regla geometrica (azimut > 105 primero) | +0.015 (+0.003 a +0.046) | -4,6 (-12,6 a +3,4) | no |
| Random Forest | Regla: menos puntos top | +0.082 (+0.057 a +0.130) | -10,8 (-20,0 a -2,1) | si |

## Test frente a train

| metodo | AUC test | AUC train (OOF) | dif AUC | F80 test | F80 train (OOF) | dif F80 | recall A test | recall A train | % revisado A test | % revisado A train |
|---|---|---|---|---|---|---|---|---|---|---|
| Regla: menos puntos LiDAR | 0.683 | 0.858 | -0.175 | 0.801 | 0.385 | 0.416 | 0.593 | 0.804 | 0.34 | 0.385 |
| Regla: menos puntos top | 0.684 | 0.862 | -0.177 | 0.79 | 0.378 | 0.412 | 0.59 | 0.806 | 0.331 | 0.379 |
| Regla geometrica (azimut > 105 primero) | 0.683 | 0.858 | -0.175 | 0.801 | 0.385 | 0.416 | 0.593 | 0.804 | 0.34 | 0.385 |
| Modelo minimo (LR 3 variables) | 0.685 | 0.855 | -0.17 | 0.786 | 0.384 | 0.401 | 0.585 | 0.799 | 0.313 | 0.364 |
| Regresion logistica | 0.698 | 0.825 | -0.128 | 0.774 | 0.437 | 0.337 | 0.621 | 0.81 | 0.356 | 0.389 |
| HGB | 0.679 | 0.805 | -0.127 | 0.821 | 0.529 | 0.292 | 0.633 | 0.8 | 0.359 | 0.392 |
| Random Forest | 0.686 | 0.836 | -0.15 | 0.76 | 0.43 | 0.33 | 0.608 | 0.793 | 0.334 | 0.387 |

## Conclusión técnica

**Caso del plan: `ningun_modelo_supera_al_mejor_baseline`.** Se reporta que ningun modelo cumple 'vale la pena' frente al mejor baseline simple y que el baseline es suficiente por simplicidad y explicabilidad. Si el IC por segmentos incluye 0 se escribe 'no se distingue del baseline', no 'es peor'. En test (población principal, 16.062 filas, 8 segmentos), Regresion logistica frente a Regla: menos puntos top: AUC 0,698 contra 0,684 (diferencia +0,014, IC 95 % -0,014 a +0,029) y Fracción para 80 % 77,4 % contra 79,0 % (diferencia -1,7 puntos, IC -4,2 a +4,1). El criterio 'vale la pena' (Fracción para 80 % baja ≥ 5 puntos con IC que excluye 0 y AUC sube ≥ 0,03) **no se cumple**. Los IC de ambas diferencias incluyen 0: **el modelo no se distingue del baseline**.

**Población de 120° (sensibilidad):** Regresion logistica no vale la pena frente a la regla geométrica; HGB no vale la pena frente a la regla geométrica; Random Forest no vale la pena frente a la regla geométrica. Frente a la regla por puntos top en 120°: Regresion logistica no vale la pena; HGB vale la pena; Random Forest vale la pena. Robustos: ninguno (lectura literal) y ninguno (baselines de train).

**Caso del plan `diferencias_con_train`.** El orden de los métodos por AUC en test (Regresion logistica > Random Forest > Modelo minimo (LR 3 variables) > Regla: menos puntos top > Regla: menos puntos LiDAR > Regla geometrica (azimut > 105 primero) > HGB) difiere del de train (Regla: menos puntos top > Regla: menos puntos LiDAR > Regla geometrica (azimut > 105 primero) > Modelo minimo (LR 3 variables) > Random Forest > Regresion logistica > HGB). Si el orden de los metodos en test difiere del de train, se reporta como hallazgo; no se reentrena ni se cambian umbrales.

**Influencia:** ningún segmento por sí solo cambia el veredicto. **Punto A de Regresion logistica:** recall 0,621 (no se sostiene con tolerancia 0,75).

## Recomendaciones (interpretación)

1. **Qué usar.** Se recomienda la Regla: menos puntos top, por simplicidad y explicabilidad (el modelo no cumple 'vale la pena' en test y no se distingue del baseline). En test, Regresion logistica frente a Regla: menos puntos top: Fracción para 80 % -1,7 puntos (IC -4,2 a +4,1) y AUC +0,014 (IC -0,014 a +0,029).

2. **Con qué punto de operación.** Punto A de Regla: menos puntos top (corte fijado con train): recall 0,590 (IC 95 % 0,383 a 0,924), precisión 0,414, 33,1 % de los frames a revisar (IC 23,8 % a 39,7 %); no se sostiene con la tolerancia del plan (recall ≥ 0,75). Punto B: recall 0,469 (IC 0,331 a 0,783) revisando 16,6 %.

3. **Cómo usarlo.** Para priorizar la revisión humana, no para reemplazarla: ordenar los frames por puntaje y revisar primero los de arriba hasta el corte elegido. En el punto A el recall observado en test fue 0,590 (el objetivo fijado con train era 0,80): quedan sin revisar el 41 % de las cajas sin par 2D, y el 59 % de lo que se revisa son cajas que sí tenían par 2D.

4. **Qué no se puede afirmar.** (i) Que `sin_camara` sea invisibilidad física: es la falta de etiqueta 2D de cámara (cobertura de etiquetado), no una medición de qué ve una cámara. (ii) Que el resultado generalice más allá de 8 segmentos de test (el IC del AUC de Regresion logistica va de 0,503 a 0,961). (iii) Nada sólido sobre ciclistas: 332 filas y 3 positivos en el test. (iv) Nada separable por momento del día para Dawn/Dusk y Night, que tienen un solo segmento cada uno.

5. **Riesgos de equidad medidos (descriptivos).** Recall al punto A de Regla: menos puntos top por momento del día: Day 0,495 (6 seg., 10.558 filas) frente a Dawn/Dusk 1,000 (1 seg., 851 filas); ubicación: location_sf 0,515 (3 seg., 11.978 filas) frente a location_other 0,946 (2 seg., 1.850 filas); clase: PEDESTRIAN 0,590 (8 seg., 15.730 filas) frente a CYCLIST 0,667 (2 seg., 332 filas). Son brechas descriptivas, sin pruebas de hipótesis.

6. **Datos que ayudarían.** `camera_calibration` para validar el borde de 100° (hoy es empírico); más segmentos de test; más ciclistas; y etiquetas por cámara para separar cobertura de etiquetado de visibilidad física.

7. **Monitoreo en producción.** Vigilar la deriva de la tasa de `sin_camara` y el recall por segmento (no solo el promedio), y reponer el corte si el recall por segmento cae por debajo de 0,75.

8. **Próximos pasos.** Si se adopta, fijar el corte con un presupuesto de revisión explícito; recolectar una muestra revisada manualmente para estimar precisión real; repetir esta evaluación cuando haya más segmentos.

**Matices (no cambian la recomendación formal).** El punto A de Regla: menos puntos top no se sostiene en test: recall 0,590 (IC 0,383 a 0,924) frente a la meta de 0,80 y la tolerancia de 0,75. El recall depende fuertemente de un segmento: en el segmento con más positivos (257766998801, 55 % de los positivos) el recall es 0,351 y sin él pasa de 0,590 a 0,879; entre los 4 segmentos con al menos 50 positivos, 3 alcanzan la tolerancia (recall de 0,351 a 0,945). Por eso se sugiere usarlo para priorizar la revisión humana, junto con un monitoreo del recall por segmento, y no como reemplazo de la revisión. (Detalle y diagnóstico post hoc en la sección L.)

## Limitación del IC de la Fracción para 80 % (K.2)

El IC 95 % por segmentos de la Fracción para 80 % de Regresion logistica (15,4 % a 88,4 %) es **bimodal**: en las 657 réplicas del bootstrap que incluyen el segmento 257766998801 la mediana es 83,4 % (rango 52,5 % a 89,0 %) y en las 343 que no lo incluyen es 23,1 % (rango 4,3 % a 46,3 %); los dos grupos no se solapan. La amplitud del intervalo refleja si la réplica incluye o no un segmento, no una incertidumbre gradual; por eso las conclusiones se apoyan en las diferencias pareadas contra la regla y no en el IC de la Fracción para 80 % de un método solo.

## Apéndice L (diagnóstico post hoc, no pre-declarado; no cambia la recomendación formal)

### Tasas por grupo

| variable | bin | tasa \| foco | tasa \| otros 7 de test | tasa \| train | n \| foco | n \| otros 7 de test | n \| train |
|---|---|---|---|---|---|---|---|
| azimut | 0-20 | 0.16 | 0.224 | 0.233 | 4027.0 | 4854.0 | 28873.0 |
| azimut | 20-40 | 0.692 | 0.147 | 0.18 | 1228.0 | 2015.0 | 15977.0 |
| azimut | 40-60 | 0.719 | 0.141 | 0.172 | 694.0 | 1015.0 | 8765.0 |
| azimut | 60-80 | 0.004 | 0.14 | 0.21 | 252.0 | 776.0 | 6043.0 |
| azimut | 80-100 | 0.19 | 0.055 | 0.206 | 273.0 | 928.0 | 4851.0 |
| puntos | 0-5 | 0.748 | 0.851 | 0.797 | 587.0 | 940.0 | 8722.0 |
| puntos | 6-10 | 0.323 | 0.566 | 0.393 | 541.0 | 592.0 | 4422.0 |
| puntos | 11-20 | 0.079 | 0.298 | 0.186 | 1005.0 | 976.0 | 8784.0 |
| puntos | 21-50 | 0.136 | 0.089 | 0.116 | 1483.0 | 2558.0 | 16578.0 |
| puntos | 51-100 | 0.191 | 0.019 | 0.051 | 1159.0 | 1780.0 | 10680.0 |
| puntos | >100 | 0.547 | 0.0 | 0.038 | 1699.0 | 2742.0 | 15323.0 |
| distancia | 0-10 | 0.235 | 0.004 | 0.111 | 319.0 | 523.0 | 2705.0 |
| distancia | 10-20 | 0.572 | 0.03 | 0.108 | 1428.0 | 1662.0 | 11304.0 |
| distancia | 20-30 | 0.354 | 0.054 | 0.144 | 735.0 | 1551.0 | 11528.0 |
| distancia | 30-40 | 0.05 | 0.139 | 0.167 | 956.0 | 1766.0 | 11289.0 |
| distancia | >40 | 0.279 | 0.32 | 0.3 | 3036.0 | 4086.0 | 27683.0 |
| clase | ciclista | nan | 0.009 | 0.076 | nan | 332.0 | 1483.0 |
| clase | peaton | 0.316 | 0.182 | 0.21 | 6474.0 | 9256.0 | 63026.0 |

### AUC por segmento de test

| segmento | filas | positivos | tasa | AUC regla top | AUC regresion logistica |
|---|---|---|---|---|---|
| 141430544948 | 1654 | 256 | 0.155 | 0.967 | 0.978 |
| 221704303323 | 4653 | 918 | 0.197 | 0.937 | 0.933 |
| 257766998801 | 6474 | 2046 | 0.316 | 0.443 | 0.459 |
| 645616575015 | 1710 | 445 | 0.26 | 0.87 | 0.836 |

### Sin par bien observadas

| grupo | cajas sin par | sin par con >= 100 puntos | % de las sin par | sin par con <= 5 puntos | % de las sin par (<= 5 puntos) | cajas con >= 100 puntos | tasa de sin par entre cajas con >= 100 puntos |
|---|---|---|---|---|---|---|---|
| foco | 2046 | 936 | 0.457 | 439 | 0.215 | 1708 | 0.548 |
| otros 7 de test | 1688 | 1 | 0.001 | 800 | 0.474 | 2760 | 0.0 |
| train | 13368 | 583 | 0.044 | 6954 | 0.52 | 15459 | 0.038 |

### Segmentos de train

| segmento | ubicacion | momento | filas | positivos | % sin_camara | AUC regla top | % de positivos con >= 100 puntos | positivos >= 50 |
|---|---|---|---|---|---|---|---|---|
| 911012534050 | location_sf | Day | 1715 | 316 | 0.184 | 0.408 | 0.617 | True |
| 102062935203 | location_phx | Night | 155 | 2 | 0.013 | 0.449 | 0.0 | False |
| 932016928997 | location_sf | Night | 513 | 97 | 0.189 | 0.661 | 0.0 | True |
| 364414530703 | location_other | Dawn/Dusk | 975 | 49 | 0.05 | 0.691 | 0.0 | False |
| 247562357599 | location_sf | Dawn/Dusk | 4218 | 1030 | 0.244 | 0.704 | 0.18 | True |
| 121745297692 | location_phx | Day | 2688 | 160 | 0.06 | 0.714 | 0.0 | True |
| 107240201159 | location_phx | Night | 369 | 43 | 0.117 | 0.798 | 0.093 | False |
| 143581920096 | location_phx | Dawn/Dusk | 368 | 82 | 0.223 | 0.8 | 0.134 | True |
| 158823431340 | location_sf | Day | 4469 | 665 | 0.149 | 0.825 | 0.026 | True |
| 182443342825 | location_sf | Night | 2058 | 600 | 0.292 | 0.833 | 0.025 | True |
| 569163609447 | location_phx | Night | 196 | 5 | 0.026 | 0.84 | 0.0 | False |
| 734453671207 | location_sf | Dawn/Dusk | 5411 | 1451 | 0.268 | 0.847 | 0.0 | True |
| 181366958272 | location_sf | Night | 6181 | 2228 | 0.36 | 0.88 | 0.026 | True |
| 104444542898 | location_sf | Day | 3891 | 846 | 0.217 | 0.887 | 0.018 | True |
| 102415087833 | location_phx | Night | 1497 | 374 | 0.25 | 0.894 | 0.019 | True |
| 164736138110 | location_sf | Dawn/Dusk | 1792 | 156 | 0.087 | 0.902 | 0.013 | True |
| 268278198029 | location_sf | Night | 3520 | 719 | 0.204 | 0.915 | 0.015 | True |
| 583504942360 | location_sf | Day | 6034 | 1045 | 0.173 | 0.93 | 0.005 | True |
| 198898761683 | location_sf | Day | 3806 | 833 | 0.219 | 0.931 | 0.005 | True |
| 369868552305 | location_other | Dawn/Dusk | 854 | 144 | 0.169 | 0.933 | 0.007 | True |
| 100239476024 | location_sf | Day | 6096 | 1174 | 0.193 | 0.951 | 0.029 | True |
| 701938586975 | location_other | Day | 697 | 216 | 0.31 | 0.953 | 0.0 | True |
| 147663847476 | location_phx | Dawn/Dusk | 415 | 1 | 0.002 | 0.966 | 0.0 | False |
| 854315837116 | location_phx | Dawn/Dusk | 97 | 4 | 0.041 | 0.97 | 0.0 | False |
| 341792825933 | location_other | Night | 792 | 11 | 0.014 | 0.972 | 0.0 | False |
| 234230089717 | location_phx | Day | 140 | 53 | 0.379 | 0.979 | 0.0 | True |
| 132384196576 | location_phx | Day | 259 | 28 | 0.108 | 0.981 | 0.0 | False |
| 851324105467 | location_phx | Night | 2725 | 797 | 0.292 | 0.982 | 0.024 | True |
| 161536078775 | location_other | Day | 921 | 120 | 0.13 | 0.993 | 0.0 | True |
| 656120676375 | location_phx | Dawn/Dusk | 487 | 96 | 0.197 | 0.993 | 0.0 | True |
| 147530897148 | location_phx | Night | 709 | 23 | 0.032 | 0.999 | 0.0 | False |
| 109649566170 | location_phx | Day | 312 | 0 | 0.0 | nan | nan | False |
| 130055621508 | location_phx | Dawn/Dusk | 149 | 0 | 0.0 | nan | nan | False |

### Sin el segmento (no reemplaza el resultado pre-declarado)

| resultado | metodo | filas | AUC | PR-AUC | Captura@20% | Fraccion para 80% |
|---|---|---|---|---|---|---|
| oficial (8 segmentos) | Regresion logistica | 16062 | 0.698 (0.503 a 0.961) | 0.565 (0.451 a 0.826) | 0.517 (0.364 a 0.887) | 0.774 (0.154 a 0.884) |
| oficial (8 segmentos) | Regla: menos puntos top | 16062 | 0.684 (0.482 a 0.958) | 0.558 (0.430 a 0.795) | 0.503 (0.346 a 0.875) | 0.790 (0.148 a 0.883) |
| sin el segmento (7 segmentos) | Regresion logistica | 9588 | 0.927 (0.880 a 0.990) | 0.729 (0.680 a 0.866) | 0.743 (0.625 a 0.998) | 0.234 (0.081 a 0.368) |
| sin el segmento (7 segmentos) | Regla: menos puntos top | 9588 | 0.931 (0.897 a 0.982) | 0.750 (0.692 a 0.820) | 0.758 (0.670 a 0.973) | 0.221 (0.083 a 0.311) |

| metodo | punto | recall oficial | recall sin el segmento | precision oficial | precision sin el segmento | % a revisar oficial | % a revisar sin el segmento | A sostenido (oficial \| sin el segmento) |
|---|---|---|---|---|---|---|---|---|
| Regla: menos puntos LiDAR | A | 0.593 (0.387 a 0.931) | 0.882 (0.859 a 0.966) | 0.405 (0.297 a 0.555) | 0.503 (0.326 a 0.572) | 0.340 (0.246 a 0.410) | 0.309 (0.211 a 0.432) | no \| si |
| Regla: menos puntos LiDAR | B | 0.468 (0.329 a 0.781) | 0.672 (0.613 a 0.846) | 0.658 (0.559 a 0.791) | 0.741 (0.639 a 0.803) | 0.166 (0.127 a 0.206) | 0.160 (0.090 a 0.226) | - |
| Regla: menos puntos top | A | 0.590 (0.383 a 0.924) | 0.879 (0.858 a 0.967) | 0.414 (0.303 a 0.567) | 0.516 (0.347 a 0.586) | 0.331 (0.238 a 0.397) | 0.300 (0.202 a 0.419) | no \| si |
| Regla: menos puntos top | B | 0.469 (0.331 a 0.783) | 0.675 (0.618 a 0.857) | 0.658 (0.559 a 0.790) | 0.741 (0.639 a 0.803) | 0.166 (0.128 a 0.205) | 0.160 (0.091 a 0.225) | - |
| Regla geometrica (azimut > 105 primero) | A | 0.593 (0.387 a 0.931) | 0.882 (0.859 a 0.966) | 0.405 (0.297 a 0.555) | 0.503 (0.326 a 0.572) | 0.340 (0.246 a 0.410) | 0.309 (0.211 a 0.432) | no \| si |
| Regla geometrica (azimut > 105 primero) | B | 0.468 (0.329 a 0.781) | 0.672 (0.613 a 0.846) | 0.658 (0.559 a 0.791) | 0.741 (0.639 a 0.803) | 0.166 (0.127 a 0.206) | 0.160 (0.090 a 0.226) | - |
| Modelo minimo (LR 3 variables) | A | 0.585 (0.383 a 0.924) | 0.870 (0.841 a 0.957) | 0.435 (0.327 a 0.587) | 0.518 (0.338 a 0.615) | 0.313 (0.225 a 0.401) | 0.296 (0.182 a 0.437) | no \| si |
| Modelo minimo (LR 3 variables) | B | 0.444 (0.320 a 0.770) | 0.632 (0.547 a 0.834) | 0.677 (0.603 a 0.804) | 0.724 (0.598 a 0.819) | 0.153 (0.115 a 0.214) | 0.154 (0.087 a 0.243) | - |
| Regresion logistica | A | 0.621 (0.413 a 0.958) | 0.913 (0.894 a 0.995) | 0.406 (0.316 a 0.543) | 0.472 (0.318 a 0.561) | 0.356 (0.257 a 0.449) | 0.341 (0.203 a 0.501) | no \| si |
| Regresion logistica | B | 0.447 (0.305 a 0.776) | 0.656 (0.586 a 0.836) | 0.688 (0.588 a 0.829) | 0.717 (0.556 a 0.843) | 0.151 (0.113 a 0.224) | 0.161 (0.085 a 0.264) | - |
| HGB | A | 0.633 (0.445 a 0.921) | 0.895 (0.848 a 0.950) | 0.410 (0.338 a 0.476) | 0.443 (0.263 a 0.486) | 0.359 (0.288 a 0.414) | 0.356 (0.254 a 0.438) | no \| si |
| HGB | B | 0.443 (0.303 a 0.734) | 0.648 (0.601 a 0.796) | 0.693 (0.609 a 0.797) | 0.755 (0.667 a 0.811) | 0.149 (0.117 a 0.190) | 0.151 (0.084 a 0.210) | - |
| Random Forest | A | 0.608 (0.419 a 0.906) | 0.873 (0.802 a 0.933) | 0.423 (0.343 a 0.506) | 0.457 (0.277 a 0.529) | 0.334 (0.258 a 0.392) | 0.337 (0.218 a 0.430) | no \| si |
| Random Forest | B | 0.430 (0.300 a 0.717) | 0.620 (0.567 a 0.779) | 0.723 (0.658 a 0.812) | 0.766 (0.677 a 0.826) | 0.138 (0.107 a 0.182) | 0.142 (0.079 a 0.205) | - |

### L.7 Recall del punto A sin el segmento, por momento del día y ubicación (post hoc)

| variable | grupo | metodo | segmentos (oficial) | positivos (oficial) | recall A (oficial) | % revisado A (oficial) | segmentos (sin el segmento) | positivos (sin el segmento) | recall A (sin el segmento) | % revisado A (sin el segmento) |
|---|---|---|---|---|---|---|---|---|---|---|
| time_of_day | Dawn/Dusk | Regla: menos puntos top | 1 | 48 | 1.0 | 0.074 | 1 | 48 | 1.0 | 0.074 |
| time_of_day | Dawn/Dusk | Regresion logistica | 1 | 48 | 1.0 | 0.09 | 1 | 48 | 1.0 | 0.09 |
| time_of_day | Day | Regla: menos puntos top | 6 | 2768 | 0.495 | 0.372 | 5 | 722 | 0.903 | 0.365 |
| time_of_day | Day | Regresion logistica | 6 | 2768 | 0.525 | 0.393 | 5 | 722 | 0.932 | 0.416 |
| time_of_day | Night | Regla: menos puntos top | 1 | 918 | 0.854 | 0.284 | 1 | 918 | 0.854 | 0.284 |
| time_of_day | Night | Regresion logistica | 1 | 918 | 0.893 | 0.32 | 1 | 918 | 0.893 | 0.32 |
| location | location_other | Regla: menos puntos top | 2 | 258 | 0.946 | 0.243 | 2 | 258 | 0.946 | 0.243 |
| location | location_other | Regresion logistica | 2 | 258 | 0.992 | 0.242 | 2 | 258 | 0.992 | 0.242 |
| location | location_phx | Regla: menos puntos top | 3 | 464 | 0.879 | 0.466 | 3 | 464 | 0.879 | 0.466 |
| location | location_phx | Regresion logistica | 3 | 464 | 0.899 | 0.56 | 3 | 464 | 0.899 | 0.56 |
| location | location_sf | Regla: menos puntos top | 3 | 3012 | 0.515 | 0.319 | 2 | 966 | 0.861 | 0.251 |
| location | location_sf | Regresion logistica | 3 | 3012 | 0.547 | 0.336 | 2 | 966 | 0.899 | 0.285 |

### Conclusión del apéndice (hipótesis)

**Hipótesis (post hoc, no pre-declarada).** Condición (i): las cajas sin par con al menos 100 puntos son 936 de 2.046 (45,7 %) en el foco frente a 1 de 1.688 (0,1 %) en los otros 7: se cumple. Condición (ii): AUC de la regla por puntos top dentro del segmento 0,443: se cumple. En las cámaras (regla de L.2), la cámara 3 (frontal der.) no tiene ningún par en el segmento (0 de 6.474 cajas del segmento; 2.090 cajas caen dentro de su rango de azimut). La causa puede ser etiquetado 2D faltante o ausencia de datos de esa cámara; con estos archivos no se distinguen. Ambas condiciones se cumplen: una parte importante de las cajas sin par del segmento son objetos bien observados, lo que **sugiere que el problema de este segmento no es la falta de observabilidad LiDAR sino la ausencia de pares en la cámara 3 (frontal der.); si la causa es etiquetado 2D faltante o ausencia de datos de esa cámara no se distingue con estos archivos**. Implicación para el uso de la regla: la regla por puntos sirve mientras la relación entre pocos puntos y ausencia de par 2D se mantenga; **no detecta huecos sistemáticos de etiquetado**, porque esos objetos están bien observados y la regla los ordena como si tuvieran par. Por eso conviene monitorear el recall por segmento. Sin el segmento, el resultado principal sigue sin cumplir 'vale la pena' y 7 de 7 métodos sostienen el punto A (oficial: 0); eso describe cuánto depende el resultado de un solo segmento y no reemplaza el resultado pre-declarado.

## Apéndice M (diagnóstico post hoc, no pre-declarado; auditoría por cámara en 41 segmentos)

### Pares (segmento, cámara) con hueco

| segmento | grupo | ubicacion | momento | camara | tasa | mediana_camara | umbral | cajas_en_rango |
|---|---|---|---|---|---|---|---|---|
| 911012534050 | train | location_sf | Day | 5 (lateral der.) | 0.0 | 0.914 | 0.228 | 300 |
| 257766998801 | test | location_sf | Day | 3 (frontal der.) | 0.0 | 0.917 | 0.229 | 1677 |

### Positivos en celdas con hueco

| index | train | test |
|---|---|---|
| segmentos | 33.0 | 8.0 |
| segmentos con algun hueco | 1.0 | 1.0 |
| cajas | 64509.0 | 16062.0 |
| % de las cajas en celdas con hueco | 0.004 | 0.104 |
| positivos | 13368.0 | 3734.0 |
| positivos en celdas con hueco | 227.0 | 1338.0 |
| % de los positivos | 0.017 | 0.358 |
| positivos con >= 100 puntos | 583.0 | 937.0 |
| de ellos en celdas con hueco | 192.0 | 884.0 |
| % de los positivos con >= 100 puntos | 0.329 | 0.943 |
| tasa de sin_camara dentro de celdas con hueco | 0.847 | 0.798 |
| tasa de sin_camara fuera de celdas con hueco | 0.205 | 0.167 |

### Tabla 2x2 exploratoria

| algun_hueco | AUC < 0,55 | AUC >= 0,55 |
|---|---|---|
| con hueco | 2 | 0 |
| sin hueco | 0 | 24 |

Test exacto de Fisher (exploratorio): p = 0.0031

### Conclusión del apéndice M (hipótesis)

**Hipótesis (post hoc, no pre-declarada).** Con los criterios fijados antes de calcular, **2 de 41 segmentos (5 %) tienen al menos una cámara con hueco** (1 de 33 de train y 1 de 8 de test), en 2 pares (segmento, cámara). Esas celdas reúnen el 1,7 % de los positivos de train y el 35,8 % de los de test de la población principal; es decir, 9,2 % del total de cajas sin par (1.565 de 17.102) se atribuye a unos pocos huecos de cámara y no a la falta de puntos. El segmento de train 911012534050 tiene hueco en 5 (lateral der.). En la tabla 2x2 exploratoria (p de Fisher = 0,003, n = 26), 2 de 2 segmentos con hueco tienen AUC < 0,55, frente a 0 de 24 sin hueco. **Implicación (hipótesis):** una auditoría por segmento y cámara (tasa de pares de cada cámara dentro de su rango de azimut) detecta lo que la regla por puntos no detecta: los huecos afectan a objetos bien observados, que la regla ordena como si tuvieran par. **Aclaración:** un 'hueco' puede ser de etiquetado o de los datos de esa cámara (por ejemplo, una cámara sin imágenes o sin etiquetas 2D en el segmento); con estos archivos no se puede distinguir. Los rangos de azimut son empíricos (de train), no calibración, y los criterios son los fijados antes de calcular. No cambia la recomendación formal ni el resultado pre-declarado.

### Cámaras

| segmento | cajas | 1 (frontal) | 2 (frontal izq.) | 3 (frontal der.) | 4 (lateral izq.) | 5 (lateral der.) | alguna camara |
|---|---|---|---|---|---|---|---|
| foco 257766998801 | 6474 | 0.563 | 0.048 | 0.0 | 0.011 | 0.072 | 0.684 |
| 102124064984 | 851 | 0.736 | 0.244 | 0.059 | 0.065 | 0.024 | 0.944 |
| 141430544948 | 1654 | 0.663 | 0.02 | 0.239 | 0.0 | 0.056 | 0.845 |
| 167359384489 | 196 | 0.719 | 0.235 | 0.0 | 0.102 | 0.0 | 0.99 |
| 221704303323 | 4653 | 0.378 | 0.299 | 0.086 | 0.112 | 0.036 | 0.803 |
| 497181704156 | 369 | 0.74 | 0.0 | 0.187 | 0.0 | 0.106 | 0.957 |
| 645616575015 | 1710 | 0.226 | 0.096 | 0.127 | 0.032 | 0.32 | 0.74 |
| 703836276130 | 155 | 0.155 | 0.387 | 0.0 | 0.497 | 0.0 | 0.981 |
| otros 7 de test (agrupado) | 9588 | 0.449 | 0.198 | 0.118 | 0.076 | 0.09 | 0.824 |
| train (agrupado) | 64509 | 0.388 | 0.185 | 0.169 | 0.081 | 0.05 | 0.793 |

| camara | rango | % con par en la camara \| foco | cajas en rango \| foco | % sin par en alguna camara de las cajas del rango \| foco | % de las cajas sin par que caen en este rango \| foco | % con par en la camara \| otros 7 de test | cajas en rango \| otros 7 de test | % sin par en alguna camara de las cajas del rango \| otros 7 de test | % de las cajas sin par que caen en este rango \| otros 7 de test | % con par en la camara \| train | cajas en rango \| train | % sin par en alguna camara de las cajas del rango \| train | % de las cajas sin par que caen en este rango \| train | razon foco / otros 7 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 (frontal) | -23 a 23 | 0.842 | 4264 | 0.157 | 0.328 | 0.784 | 5351 | 0.208 | 0.659 | 0.761 | 32225 | 0.228 | 0.55 | 1.075 |
| 2 (frontal izq.) | 19 a 67 | 0.936 | 326 | 0.049 | 0.008 | 0.853 | 2194 | 0.105 | 0.137 | 0.768 | 15212 | 0.206 | 0.235 | 1.097 |
| 3 (frontal der.) | -64 a -17 | 0.0 | 2090 | 0.644 | 0.658 | 0.668 | 1642 | 0.181 | 0.176 | 0.785 | 13642 | 0.14 | 0.143 | 0.0 |
| 4 (lateral izq.) | 61 a 112 | 1.0 | 63 | 0.0 | 0.0 | 0.913 | 756 | 0.06 | 0.027 | 0.756 | 6864 | 0.208 | 0.107 | 1.096 |
| 5 (lateral der.) | -110 a -52 | 0.742 | 623 | 0.258 | 0.079 | 0.824 | 1028 | 0.151 | 0.092 | 0.606 | 5220 | 0.19 | 0.074 | 0.9 |
