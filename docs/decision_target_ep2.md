### Cambio de target para EP2: de `tiene_camara` a `sin_camara`

**Decisión.** Target elegido para EP2: B.

**Por qué.** En train, vehículos y señales no tienen ningún positivo (265.377 filas), así que `tiene_camara` en todos los objetos mezcla la clase del objeto con la cobertura de cámaras. Una regla de una línea alcanza AUC 0,975 y el modelo 0,992. Dentro de peatones y ciclistas en la zona de cámaras, `sin_camara` es la clase rara (23,2 %) y se predice con AUC 0,854 (IC 95 % 0,810–0,897), PR-AUC 0,747, AUC mínimo por fold 0,824.

**El problema.** En Waymo Open Dataset v2 los `lidar_box` son cajas 3D etiquetadas, no la salida de un detector; según nuestra lectura de la documentación, la asociación cámara-LiDAR los enlaza con su par 2D de cámara cuando existe. El problema es auditar qué cajas 3D etiquetadas no tienen su par 2D de cámara.

**Candidatas descartadas**

| candidata | motivo | evidencia |
|---|---|---|
| A: tiene_camara en todos los objetos | dominado por clase y zona de cámaras | regla R2 AUC 0,975; modelo 0,992 (+0,018, techo 0,025); PR-AUC +0,163; 0 positivos en 265.377 filas de vehículos y señales |
| C: desplazamiento a 2 s | la velocidad constante ya lo resuelve; el modelo no la mejora | error 0,28 m (velocidad constante) vs 0,29 m (modelo); mejora -2,4 %, IC 95 % inferior -11,6 %; gana en 2 de 5 folds |
| D: peatón vs ciclista | pocos ciclistas y bajo valor de negocio | 2,09 % ciclistas en 12 segmentos; folds sin ciclistas: 1 de 5; AUC 0,988 vs 0,703 del baseline simple |
| E: conflicto con el corredor a 2 s | eventos insuficientes | 68 casos, 5 objetos distintos, 2 segmentos, 2 de 5 folds |

**Valor práctico de B (versión previa, población de 120°).** Para encontrar el 80 % de las lagunas hay que revisar el 39,1 % de los frames con el modelo, el 50,5 % con la regla simple de menos puntos LiDAR primero y el 80,0 % al azar (diferencia modelo menos regla: -11.4 puntos, IC 95 % -19.0 a -6.1). En el tope de la lista (Captura@20 %) la ventaja sobre la regla es pequeña (+3.5 puntos, IC +0.2 a +7.4): el modelo aporta más en alta cobertura. A nivel de objeto casi no prioriza (el 83,0 % de los objetos es mixto), y la unidad sugerida es el frame. Las horas ahorradas dependen de un supuesto de 20 s por revisión que no es un dato medido.

**Actualización posterior al 08 y 09 (las cifras de arriba son de la versión previa, población de 120°).** La población principal pasó de 120° a |azimut| ≤ 100° porque en 100–120° la ausencia de par 2D es en buena parte geométrica (08). En la población principal (64.509 filas) el mejor baseline simple es Regla: menos puntos top (AUC 0,862, Fracción para 80 % 37,8 %) y la recomendación del 09 es **Regla: menos puntos top**. En la población de 120°, con los modelos reentrenados en el 09, el HGB menos la regla de puntos da -9.0 puntos en Fracción para 80 % (IC -20.0 a -2.0) y menos la regla geométrica +4.8 puntos (IC -1.3 a +9.1): la ventaja de -11.4 puntos frente a la regla de puntos de la versión previa **no se sostiene** al compararla con un baseline geométrico.

**Población principal.** La población de EP2 es |azimut| ≤ 100° (peatones y ciclistas); la franja 100–120° queda fuera porque la ausencia de par 2D ahí es en buena parte geométrica (notebook 08). El target (`sin_camara`) y el split no cambian.

> **Declaración del problema para el informe**
>
> **Problema.** El 23,2 % de las cajas 3D etiquetadas (`lidar_box`) de peatones y ciclistas dentro de la zona de cámaras no tiene su par 2D de cámara y hoy no se sabe cuáles son sin revisarlas. **Objetivo.** Estimar, con solo atributos de la caja 3D etiquetada, la probabilidad de que no tenga su par 2D y entregar una lista priorizada para revisión humana. **Métrica de éxito.** AUC-ROC y PR-AUC fuera de fold (versión previa, población de 120°: 0,854 y 0,747), y la fracción de frames que hay que revisar para cubrir el 80 % de las lagunas (versión previa, 120°: 39,1 % con el modelo, 50,5 % con la regla simple y 80,0 % al azar), con brecha entre grupos de día, noche y ubicación. **Alcance.** Peatones y ciclistas con |azimut| ≤ 100° (población principal; la versión previa usaba 120°) en frames con etiquetas de cámara, en 33 segmentos de train de Waymo Open Dataset v2. **Limitación principal.** El modelo captura cobertura de etiquetado y, sobre todo, la calidad de observación del LiDAR (sin puntos LiDAR el AUC cae a 0,654); `speed_mps` proviene de la etiqueta y su ablación casi no mueve el AUC (-0.004); el modelo no mide visibilidad física de la cámara ni sirve como alerta dentro del auto.

**Criterios fijados antes de calcular** (Sección 3 del notebook `07_decision_target_ep2.ipynb`), después de la exploración del notebook 06; los umbrales no se cambiaron al ver resultados.

**Limitaciones**

- B solo aplica a frames que ya tienen etiquetas de cámara.
- Pocos ciclistas (2.105 filas en train, en 12 segmentos).
- Muestra seleccionada por etiquetado denso (41 de 91 segmentos evaluados).
- Los folds se estratificaron por `tiene_camara`, no por `sin_camara` en la zona de cámaras.
- El valor es del lado de los datos, no del auto; el factor dominante son los puntos LiDAR (sin ellos AUC 0,654).
- Composición del test: 8 segmentos; los dos más grandes aportan el 68,0 % de las filas de B; Dawn/Dusk y Night tienen un solo segmento, por lo que la equidad por momento del día se mide con los folds de train y no con el test.
- El etiquetado varía mucho entre segmentos: la tasa de `sin_camara` va de 1,5 % a 33,6 % por segmento en el test y de 0,6 % a 39,5 % en train.

**KPIs a medir en el notebook 09** (sin cifras prometidas): AUC-ROC y PR-AUC fuera de fold; Captura@20 %, Fracción para 80 % y Lift@20 % (curva de captura, IC 95 % por segmentos); Recall y precisión en el punto de operación elegido; Brecha Day/Night y por ubicación; Estabilidad entre folds.
