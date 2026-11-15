# Desviaciones del plan v3

Archivo aparte para no alterar el hash de `plan_v3.md` y `plan_v3.json`. Cada entrada lleva fecha, motivo y efecto.


## DEV-1 (2026-11-14) Reducción de cómputo en F3 y F4 (regla 9 de las instrucciones)
- **Medición previa:** un ajuste de Random Forest de 200 árboles sobre 52.002 filas, con un hilo, tarda entre 45 y 100 s (HGB 1 a 5 s, XGBoost y LightGBM 1 a 2,5 s, LR 0,1 s). Fuente: medición en esta sesión, 2026-11-14.
- **Proyección con el plan completo** (3 repeticiones x 40 configuraciones x CV interna de 3 pliegues, solo RF): unas 17 horas de CPU, es decir cerca de 3 horas de reloj con 6 procesos, más el resto de F3 y F4: alrededor de 5 horas en total, sobre el límite de 4 horas.
- **Cambio:** 1 repetición de la CV externa (semilla 42, no 42/43/44) y 30 configuraciones por búsqueda aleatoria (no 40). La rejilla de LR no cambia (48 combinaciones: 8 valores de C x 2 class_weight x 3 conjuntos de variables).
- **Efecto:** los IC pareados por segmentos reflejan una sola partición de segmentos en pliegues; no se promedia entre particiones. Los criterios de decisión (umbrales, IC que excluye 0) no cambian.
- **Se mantiene:** CV interna GroupKFold(3) por segmento con PR-AUC, grillas más regularizadas que las de EP2, revisión de bordes de grilla con una extensión, 1000 réplicas de bootstrap por segmentos.

## DEV-2 (2026-11-14) Ningún candidato cumple O4 (estabilidad): regla de reserva, post hoc, no pre-declarada
- **Hecho (data/08_reporting_ep3/f5_metricas_candidatos.csv):** los 11 candidatos, incluida la regla de puntos, quedan con AUC mínimo por fold entre 0,641 y 0,685, bajo el criterio de 0,75; la mediana del AUC por segmento (0,848 a 0,908) sí supera 0,80 en todos. El fold 0 de la CV externa (semilla 42) tiene AUC bajo para todos los métodos (0,641 a 0,685), señal de que depende de qué segmentos cayeron en él y no del método.
- **Consecuencia:** la regla de elección de P8 («entre los que cumplen O1, O3 y O4…») no designa a nadie, y el plan solo prevé qué hacer cuando nadie cumple O2.
- **Decisión (tomada después de ver estos números, por eso es post hoc):** por analogía con lo que el plan dice para O2, se declara que nadie cumple O4 y se aplica la misma regla de simplicidad («el más simple cuyo AUC OOF quede a menos de 0,010 del mejor») entre los candidatos que cumplen O1 y O3. Los criterios O1 a O4 no se modifican. La estabilidad se reporta como limitación de todos los candidatos.
- **Implementación:** scripts/ep3/f6_seleccion.py (campo `fallback_O4` en f6_seleccion.json).
- **Complemento para IE11:** si el elegido no aprende nada (regla), el leave-one-segment-out y la curva de aprendizaje no tienen contenido; se calculan además para los dos mejores modelos aprendidos (LR3 y XGB) con `f5_loso_curva.py --candidato`.

## DEV-3 (2026-11-14) Terminología del detector: «celdas marcadas», no «falsas alarmas» (aclaración; no cambia ningún criterio)
- **Motivo:** el plan v3 (P9 y otros) habla de «falsas alarmas del detector». Los 2 huecos de referencia los define el mismo detector con los parámetros de EP2 y no existe una verdad externa sobre qué celdas son huecos reales; por lo tanto una celda marcada que no es una de las 2 de referencia no es una «falsa alarma» comprobada.
- **Cambio de lenguaje:** en todos los documentos y notebooks se dice «celdas marcadas además de los 2 de referencia (sin verdad externa)». El «30 de 30» mide la **estabilidad del conjunto marcado frente a los parámetros**; no es sensibilidad ni especificidad.
- **Qué se medirá con segmentos nuevos:** (i) tasa de celdas marcadas; (ii) su estabilidad frente a las 30 combinaciones de parámetros; (iii) opcional y post hoc, si existe el componente `camera_box` de Waymo v2, comprobar en cada celda marcada si esa cámara tiene cajas 2D en el rango sin pares (laguna de asociación) o no tiene ninguna (laguna de etiquetado o de datos).
- **No cambia:** los parámetros congelados del detector, los umbrales, la elección ni ninguna cifra. Los nombres de columna `falsas_alarmas` de `f12_sensibilidad_detector.csv` y `f12_resumen.json` se conservan por trazabilidad (no se regeneraron esos resultados).
- **El plan v3 congelado (`plan_v3.md`, `plan_v3.json`) no se edita:** conserva el término original; esta nota lo aclara.
