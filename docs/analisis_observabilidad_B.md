### Análisis de observabilidad de `sin_camara` (notebook 08)

Solo segmentos de train y sus folds; el test no se usó. Criterios fijados antes de correr (Sección 0 del notebook).

**Qué produce `sin_camara`.** La tasa va de 80,5 % con 0-5 puntos a 9,4 % con >100. El cambio es gradual: el mejor corte único (7 puntos) logra AUC 0,665 frente a 0,797 de la regla continua y su ubicación varía entre folds. Dentro de un mismo objeto, el 80,0 % de los objetos mixtos tiene más puntos en los frames con par 2D (Wilcoxon p = 1.9e-29), aunque la distancia también cambia.

**Robustez.** La mediana del AUC por segmento del HGB es 0,864 (IQR 0,818–0,913, 16 segmentos evaluables) frente a 0,854 agrupado; la regla simple tiene 0,802 por segmento y 0,797 agrupado.

**Variables nuevas.** Ningún conjunto cumple el criterio fijado antes (ΔAUC ≥ 0,01 y fracción para 80 % −2 puntos con IC que excluya 0): la regla "pocos puntos" explica casi todo y el modelo agrega solo la parte ya medida en el 07. Mejor AUC: TODAS_B + ambos (0,861).

**No supervisado.** k = 2, silhouette 0,387, estabilidad ARI 0,953 (mínimo 0,301), rango de la tasa entre clusters 12,4 puntos y diferencia con signo de 12,4 puntos (IC 7,6 a 18,2): estructura útil según el criterio; las probabilidades del modelo ya siguen esas tasas, así que describe pero no agrega información predictiva.

**Qué llevar al 09.** Variables: `TODAS_B` (conjunto base, porque ningún conjunto ampliado cumplió el criterio). Modelos: la regresión logística y el HGB se comparan en el 09 (AUC agrupado HGB 0,854 contra regresión logística 0,838; mediana del AUC por segmento HGB 0,864 contra regresión logística 0,873), siempre contra la regla simple de menos puntos LiDAR primero (AUC 0,797), que es la alternativa realista; **la decisión se toma ahí**. Las variables quedan en `data/05_model_input/features_B.parquet` y los conjuntos en `config_features_B.json`.

**Variables nuevas evaluadas**

| conjunto | AUC | PR-AUC | Captura@20% | Fraccion para 80% | dAUC vs TODAS_B | dFraccion80 vs TODAS_B | ayuda (criterio) |
|---|---|---|---|---|---|---|---|
| TODAS_B | 0.854 (0.810 a 0.897) | 0.747 | 0.613 (0.542 a 0.702) | 0.391 (0.292 a 0.478) | - | - | - |
| TODAS_B + temporales | 0.852 (0.805 a 0.901) | 0.749 | 0.616 (0.539 a 0.714) | 0.400 (0.295 a 0.491) | -0.002 (-0.014 a +0.007) | +0.9 pp (-1.8 a +5.3) | no |
| TODAS_B + oclusion | 0.853 (0.807 a 0.897) | 0.746 | 0.611 (0.537 a 0.710) | 0.388 (0.288 a 0.475) | -0.001 (-0.009 a +0.006) | -0.4 pp (-1.9 a +1.5) | no |
| TODAS_B + ambos | 0.861 (0.816 a 0.907) | 0.757 | 0.617 (0.540 a 0.717) | 0.373 (0.271 a 0.447) | +0.007 (-0.002 a +0.015) | -1.8 pp (-4.3 a +1.5) | no |

**Hallazgos para el informe técnico**

1. La etiqueta `sin_camara` depende sobre todo de los puntos LiDAR: la tasa cae de 80,5 % con 0-5 puntos a 9,4 % con >100, y a distancia fija la diferencia entre pocos y muchos puntos va de 71,7 a 87,1 puntos porcentuales (A.1 y A.2).
2. Dentro de un mismo objeto, el 80,0 % de los 460 objetos mixtos tiene más puntos cuando la cámara sí lo confirma (A.4): el número de puntos acompaña el cambio de estado.
3. Una regla sin modelo (menos puntos LiDAR primero) ya da AUC 0,797; el HGB, 0,854. Para cubrir el 80 % de las lagunas hay que revisar el 39,1 % de los frames con el HGB y el 50,5 % con la regla (B y 07).
4. El AUC dentro de cada segmento (mediana 0,864, 16 segmentos evaluables) es parecido al agrupado (0,854): el resultado no depende de mezclar segmentos (B).
5. Las variables temporales y de oclusión no cumplen el criterio de mejora: la información de observabilidad ya está en los puntos LiDAR y la geometría (C).
6. Los ciclistas casi siempre tienen par 2D: `sin_camara` en 8,8 % de sus 1.516 filas, frente a 23,5 % en peatones (hallazgo no esperado; pocos ciclistas, ver limitaciones).
7. El 1 % de cajas más atípicas (IsolationForest, 686 cajas en 28 segmentos) tiene 80,3 % de `sin_camara`, frente a 22,6 % en el resto (D).
8. **La ausencia de par 2D en 100–120° es en buena parte geométrica:** la tasa de `sin_camara` es 20,7 % con |azimut| ≤ 100° y 62,2 % en la franja (que reúne el 5,9 % de las filas de B), y en el último bin de 5° llega a 100,0 % con 1.133 filas. Solo el 2,6 % de las cajas con par 2D en train está más allá de 100°. Sin la franja, el HGB deja de superar a la regla de puntos (AUC 0,835 contra 0,858; A.6 y A.7).

**Preguntas abiertas para el 09**

1. **Puntos de operación.** ¿Qué recall objetivo y qué fracción de frames revisar? El HGB captura el 61,3 % de las lagunas con el 20 % de los frames y exige revisar el 39,1 % para cubrir el 80 %; el punto concreto y su IC se definen en el 09.
2. **Calibración.** La probabilidad media predicha por el HGB fuera de fold es 0,221 frente a una prevalencia de 0,232. ¿Hace falta calibrar (curva de calibración, Brier) antes de fijar umbrales de probabilidad?
3. **Equidad.** AUC del HGB por momento del día: Dawn/Dusk 0,798, Day 0,873, Night 0,873; por ubicación: location_other 0,912, location_phx 0,866, location_sf 0,851. ¿Qué brecha es aceptable y cómo se mide si el test tiene un solo segmento Night y uno Dawn/Dusk (ver 07, Sección 11)?
4. **Unidad de revisión.** El 83,0 % de los objetos es mixto: ¿frame u objeto? A nivel de frame el modelo prioriza; a nivel de objeto casi no (ver 07, Sección 8.4).
5. **Variabilidad entre segmentos.** El AUC del HGB por segmento va de 0,626 a 0,971 y por fold de 0,824 a 0,888. ¿Cómo reportar la incertidumbre sin reducirla a un solo número?
6. **Modelo frente a la regla.** La regresión logística (0,838) y el HGB (0,854) superan a la regla simple (0,797); para cubrir el 80 % de las lagunas hay que revisar el 39,1 % de los frames con el HGB y el 50,5 % con la regla. ¿Qué regularización, pesos de clase y complejidad corresponden a cada modelo y cuál de los dos se prefiere?
7. **Ciclistas.** Solo 1.516 filas de ciclistas en B: ¿se reporta por clase y con qué cautela?
8. **Zona de cámaras (decisión tomada).** La población principal pasó de 120 a **100 grados** por el hallazgo de A.6: la franja 100–120° reúne el 5,9 % de las filas de B con 62,2 % de `sin_camara`, frente a 20,7 % con azimut ≤ 100°, y sin ella la Fracción para 80 % del HGB pasa de 39,1 % a 40,9 % y la diferencia HGB menos regla de -11.4 a +2.4 puntos. Queda abierto confirmar el borde con `camera_calibration` (no disponible localmente), que daría el yaw y el campo de visión de cada cámara.

**Limitaciones**

- La oclusión es una aproximación angular que ignora la altura de las cajas y la transparencia de señales; 77 % de las cajas tiene al menos un oclusor.
- Las variables temporales usan solo frames anteriores del mismo track.
- Los folds se estratificaron por `tiene_camara`, no por `sin_camara` en la zona de cámaras.
- Los resultados describen cobertura de etiquetado en 33 segmentos de train y no visibilidad física de la cámara.
