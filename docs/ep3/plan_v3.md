# Plan v3 (EP3) - criterios fijados antes de ver resultados

Este documento se congela con su sha256 (`plan_v3.sha256`). Los criterios no se editan: cualquier cambio va en `plan_v3_desviaciones.md` (archivo aparte, con fecha y motivo), para no alterar el hash.

## P1 Desarrollo y validación
Los 41 segmentos (33 de train + 8 de test de EP2) en una tabla, población principal |azimut| <= 100°, target `sin_camara`. Se declara que los 8 de EP2 ya no son test ciego (se miraron 6 veces). Validación externa: ver P9.
- CV externa: StratifiedGroupKFold(5, shuffle=True) estratificada por `sin_camara`, grupos = segmento, semillas 42/43/44 (3 repeticiones).
- CV interna: GroupKFold(3) por segmento, criterio PR-AUC.
- IC: bootstrap por segmentos, 1000 réplicas (500 en cómputo pesado), diferencias pareadas.

## P2 Variables
Tres conjuntos declarados:
- V16: las 16 de EP2.
- V_OBS: num_lidar_points, num_top_lidar_points, densidad_puntos, distancia_m.
- V_OBS_TAM: V_OBS + box_length, box_width, box_height, volumen_caja, es_ciclista, speed_mps.
El conjunto es un hiperparámetro de la búsqueda.

## P3 Filtro 1 (detector)
Parámetros de EP2 congelados, sin recalcular: rango p5-p95 por cámara con los 33 de train, mediana por cámara con los 41, hueco si tasa < 0,25 x mediana y al menos 100 cajas en rango. Salida: Lista A (segmento, cámara, tasa, cajas afectadas).

## P4 Brazos
- A: un paso, todas las cajas.
- B: solo celdas sanas (sensibilidad).
- C: dos pasos: la Lista A se atiende aparte (sus positivos cuentan como encontrados por la auditoría) y la Lista B ordena las cajas de celdas sanas.
No se inventa un costo por auditoría: se reporta el costo (en cajas) por auditoría con el que C empata con A (punto de equilibrio).

## P5 IE9 (optimización de hiperparámetros)
Modelos: LR, RF, HGB, XGBoost, LightGBM, cada uno por defecto vs optimizado (búsqueda aleatoria anidada, 40 configuraciones; LR con rejilla de C de 1e-5 a 100 x class_weight). Las grillas deben incluir valores MÁS regularizados que los de EP2 (en EP2 varios óptimos quedaron en el borde: HGB max_leaf_nodes 4 y min_samples_leaf 100; RF min_samples_leaf 200 y max_features sqrt). Si un óptimo cae en el borde, se extiende la grilla una vez y se repite (se registra).
"Mejora" = diferencia de PR-AUC OOF (optimizado menos defecto) >= +0,010 con IC pareado por segmentos que excluya 0; si no, "no mejora".

## P6 IE10 (ensambles)
- E1: voting soft LR+RF+HGB.
- E2: promedio de rangos de E1 + la regla "menos puntos top".
- E3: stacking con meta-LR sobre predicciones fuera de fold calculadas con GroupKFold(3) por segmento dentro de cada fold externo (LR, RF, HGB, XGB, LGBM); implementado a mano o pasando cv por grupos, porque el CV interno por defecto de scikit-learn mezcla segmentos y filtra información.
- E4: stacking por vistas (un modelo con V_OBS, otro con variables de tamaño, otro con posición y azimut, y meta-LR).
Un ensamble "aporta" si su AUC OOF supera en >= 0,010 a su mejor componente y el IC pareado por segmentos excluye 0. Si la diferencia es >= 0,010 pero el IC incluye 0: "indicio no concluyente". Si no: "no aporta". Se reporta siempre en cuántos folds y cuántos segmentos gana. El ensamble principal queda declarado desde ya: el de mayor AUC OOF entre E1 y E4.

## P7 IE11 (generalización)
Métricas: AUC, PR-AUC, Captura@20 %, Fracción para 80 %, recall y precisión en el punto A (recall objetivo 0,80, umbral fijado con OOF interno) y en el punto B (20 % de revisión), ECE y Brier (con calibración Platt). Estabilidad: AUC mínimo por fold >= 0,75 y mediana del AUC por segmento >= 0,80. Además: leave-one-segment-out del modelo elegido, curva de aprendizaje por número de segmentos y brecha ajuste-validación. Accuracy y F1 solo como referencia en el cuadro "Modelo escogido" (no deciden nada).

## P8 IE12 (selección)
Candidatos: regla top, LR de 3 variables, LR, RF, HGB, XGB, LGBM, E1 a E4, con los brazos A y C.
Objetivos (los de EP2):
- O1: AUC >= 0,70 y PR-AUC menos prevalencia >= 0,10.
- O2 "vale la pena" frente a la regla: la Fracción para 80 % baja >= 5 puntos con IC pareado que excluye 0 y el AUC sube >= 0,03.
- O3: recall >= 0,75 en el punto A.
- O4: estabilidad (P7) y ECE <= 0,05.
Elección: entre los que cumplen O1, O3 y O4, el más simple cuyo AUC OOF quede a menos de 0,010 del mejor. Simplicidad: regla < LR 3 variables < LR < RF < HGB < XGB/LGBM < voting < stacking. Si ninguno cumple O2, se dice, y se recomienda igualmente el más simple que cumpla lo demás. La solución final se declara con sus tres capas: filtro 1, modelo o regla, y persona que revisa y decide.

## P9 Validación externa con segmentos nuevos (solo cuando existan)
Antes de abrirlos se congelan modelos, umbrales, parámetros del detector y lista de segmentos, con sha256. Se evalúa UNA sola vez, con candado. Comparaciones: solución elegida vs regla y C vs A. Además, falsas alarmas del detector (celdas marcadas / celdas totales). Nada se selecciona con ellos.
