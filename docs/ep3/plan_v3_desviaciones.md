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
