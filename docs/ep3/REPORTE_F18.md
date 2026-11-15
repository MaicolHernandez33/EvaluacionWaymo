# Reporte final de la tarea F18

*Generado por `scripts/ep3/generar_reporte_f18.py`; cada cifra sale de su archivo de `data/08_reporting_ep3` o `docs/ep3`. Decisiones: `ESTADO.md` (DEC-27 en adelante, sección F18).*

## Resumen
F18 tuvo cuatro fases: **A** correcciones de fondo y análisis post hoc; **B** selección de segmentos nuevos para la validación externa; **C** rediseño de la página; **D** cierre (guion, documentos, entrega y verificación). Los congelados no cambiaron en ninguna fase: EP2 14 de 14, v3 5 de 5 y no supervisado 1 de 1. Pruebas de EP3 recolectadas: 98 (antes de F18: 63).

## Fase A. Correcciones de fondo y análisis post hoc
- **A1. Terminología.** «Falsas alarmas» pasó a «celdas marcadas además de los 2 de referencia (sin verdad externa)» en informe, README, guion, preguntas, notebooks, artefactos, MAPA y en los textos de `sellado.py` y `evaluar_sellado.py`. «30 de 30» (30 de 30) mide la estabilidad del conjunto marcado frente a los parámetros, no sensibilidad ni especificidad. El informe §14 y `evaluar_sellado.py` dicen qué se medirá con segmentos nuevos: (i) tasa de celdas marcadas, (ii) su estabilidad frente a las 30 combinaciones y (iii) opcional y post hoc, con `camera_box`, si esa cámara tiene cajas 2D (laguna de asociación) o ninguna (laguna de etiquetado o de datos). Registrado como **DEV-3** en `plan_v3_desviaciones.md`. Los nombres de columna `falsas_alarmas` de `f12_*` y el texto congelado de `plan_v3.*` se conservan (no se regeneró F12).
- **A2. ¿Dónde está el ML?** Respuesta reescrita: el ML son los 11 candidatos con validación anidada, la calibración Platt (una regresión logística) y el análisis no supervisado; **el detector de huecos es estadística descriptiva** (percentiles, una mediana y un umbral).
- **A3. AUC de la regla dentro de cada cluster.** (a) Columna agregada a las tablas del informe §9: k = 2, 0,531 en «cercanos y densos» y 0,837 en «lejanos y poco densos»; la regla pierde capacidad de ordenar en cajas cercanas y densas. **(b) Sin las celdas con hueco** (`f13_auc_cluster_sin_huecos.csv`, post hoc, descriptivo): el AUC de los cercanos **sube de 0,531 a 0,748 (+0,217)**; con k = 4 (cluster 0) de 0,416 a 0,750 (+0,334); los lejanos casi no cambian (0,837 a 0,842). Las celdas con hueco tienen 1.772 cajas y 1.418 de los 3.285 positivos del cluster cercano: explican buena parte de la pérdida, no toda (queda una brecha de 0,748 contra 0,842). **(c) Puntos del sensor superior > 100** (`f12_eda_puntos_top_sin_huecos.csv`): la tasa sube de 5,7 % (51 a 100) a 7,5 % (> 100) por las celdas con hueco: 1.234 cajas con tasa 85,6 %, 71,9 % de los positivos del tramo; sin ellas la tasa del tramo es 2,3 % y la serie es decreciente (4,0 %, 3,1 %, 1,1 %, 1,8 %); queda una concentración residual en el segmento `247562357599`. Con preguntas cruzadas en `preguntas_cruzadas.md`.
- **A4. «20 %» en el informe y en la página** (`f18_definiciones.json`): el informe (`f5_generalizacion.py`, `RankingDosPasos`) toma el 20 % del **total** de cajas (80.571) = 16.115 cajas; la página (`app_logica.py`, `curva_cola.csv`) toma el 20 % de la **cola** de celdas sanas (78.626) = 15.726 cajas. Con esa diferencia de 389 cajas, el brazo C da 70,9 % en el informe, 70,2 % en la curva de la página y 70,3 % en el conteo observado (el resto, menos de 0,2 puntos, es desempate de empates e interpolación). El AUC base de `f13_aporte_cluster.csv` es 0,798 y no 0,823 porque usa la probabilidad con Platt de cada fold (0,809 al juntar los folds; dentro de cada fold el AUC es idéntico) más una regresión logística adicional con otra partición. Escrito en informe §9, §12 y §13 y en la pregunta sobre la página.
- **A5. ARI.** KMeans coincide con el GMM esférico (0,884) y con el diagonal (0,729); el discrepante es el GMM de covarianza `full` (0,008; partición 70/30 contra 47/53); Ward 0,426. Evidencia de EP2 (solo lectura): `docs/informe_tecnico_EP2.md:408` (variables de oclusión), `:428-429` (clusters «ocluidos» y «sin oclusores»), `:422` (covarianzas degeneradas, varianza mínima 1e-6 en `n_ocl`, `frac_cub` y `dist_ocl_f`) y `data/08_reporting/08_no_supervisado_resumen.json:5-7` (ARI 0,997). Hipótesis, no verificada: el 0,997 de EP2 probablemente estaba inflado por variables discretas; el 0,008 no es la anomalía. El BIC del GMM baja de 86.283 a 14.497 y no se usa para elegir k. Las preguntas sobre clusters y ARI citan siempre el 0,884 junto al 0,008. **La página usa k = 2** (`k_elegido`), así que los clusters 1 y 3 de k = 4 (mismo rótulo, tasas 14,8 % y 10,7 %) no se ven en la página y no hizo falta diferenciarlos.
- **A6. Sesgo de selección** (`f18_seleccion_*.csv`): 91 evaluados, 50 descartados (27 asociación vacía, 21 etiquetado ralo, 2 pocas asociaciones); rendimiento de día 67 %, amanecer o atardecer 50 % y noche 29 %. Agregado a informe §3 y §16 (limitación), §15 (recomendación: filtro 1 a nivel segmento, sin ML) y §17. La causa se declara desconocida. La tabla del detector (§8) indica la población de cada columna (300 cajas a ≤120° contra 268 a ≤100°).
- **A7. Preguntas cruzadas nuevas** (recall objetivo, Platt, fuga de datos, bootstrap por segmentos, PR-AUC y AUC, sensor superior, deriva, E2 en 5 de 5 folds, limitación principal, qué se haría con más tiempo, y las de A3 a A6): el archivo pasó a ser de **70 preguntas**.

## Fase B. Selección de segmentos nuevos (sin bucket)
- **B1. Embudo** (como el 00b de EP2; el notebook y `plan_seleccion_ep3.py` se detienen si no coincide): inventario 798 → sin lluvia **793** → 190 frames o más **786** → `n_detecciones` entre los percentiles 2,5 y 97,5 (2.027 a 33.688) **746** → solo después se excluyen los 91 evaluados por EP2 → **655** candidatos. Coincidió con EP2.
- **B2. Cuotas fijas de segmentos útiles** (total 26):

| Estrato | Cuota | Candidatos |
|---|---|---|
| Day / location_sf | 8 | 313 |
| Day / location_phx | 4 | 191 |
| Day / location_other | 2 | 81 |
| Night / location_sf | 3 | 23 |
| Night / location_phx | 2 | 9 |
| Dawn/Dusk / location_sf | 3 | 15 |
| Dawn/Dusk / location_phx | 3 | 22 |
| Dawn/Dusk / location_other | 1 | 1 |

  Evaluación secuencial por estrato en el orden de `default_rng(42)`, recorrida por rondas (decisión mía: con un tope global de 55 evaluaciones, ir estrato por estrato dejaría sin evaluar a los últimos), meta de 15 útiles. La justificación (cuotas por estrato como en el desarrollo, sobremuestreo de San Francisco de día por las 2 celdas con hueco, noche mal representada) está en el notebook.
- **B3.** Se agregó `MIN_POSITIVOS = 30` y el caso «las asociaciones no cruzan con lidar_box».
- **B4. Plan pre-declarado:** `docs/ep3/plan_seleccion_ep3.json` y `.sha256` (calculado sin descargar nada); la lógica está en `src/waymo_evaluacion/ep3/seleccion_nuevos.py`, el notebook incluye su código exacto y `tests/ep3/test_seleccion_nuevos.py` (13 pruebas) compara la lógica con el JSON.
- **B5.** `docs/ep3/GUIA_VALIDACION_EXTERNA.md` con los pasos, qué hacer si salen menos de 15 útiles, los comandos de `evaluar_sellado.py` e `ingesta_nuevos.py`, los tres casos, el paso opcional con `camera_box` (con `gsutil ls` previo) y la garantía de sellado: el modelo v3 (`manifest_v3.json`, copia en `artefactos_ep3/`) y el plan de selección deben quedar commiteados **antes** de ejecutar el Colab.

## Fase C. Rediseño de la página
- Producto «Auditor de etiquetas 3D» (`app/app.py`, `secciones.py`, `estilos.py`, `assets/icono.png`), **8 secciones**, 3 perfiles, modo presentación, tema en los dos `config.toml` (solo se agregó `[theme]`), formato es-CL, sin ninguna petición externa (una prueba falla si algún archivo contiene `http://` o `https://`) y sin emojis. Guía de estilo con contraste calculado (≥ 4,5:1 en todos los pares): `guia_estilo_pagina.md`. Demo: `pagina_guia_demo.md`. Pendientes: `PENDIENTES_PAGINA.md`.
- **Cifras antes y después** (`pagina_comparacion_antes_despues.csv`; las cifras no cambian, salvo la cobertura de la cola, que ahora tiene una sola fuente, el conteo observado):

| seccion | caso | cifra | antes | despues |
|---|---|---|---|---|
| Cola de revisión | presupuesto 20 % | cajas a revisar | 15.726 | 15.726 |
| Cola de revisión | presupuesto 20 % | horas (20 s por caja) | 87,4 | 87,4 |
| Cola de revisión | presupuesto 20 % | cobertura (tarjeta antes / frase ahora) | 70,2 % | 70 de cada 100 |
| Cola de revisión | presupuesto 20 % | filas de la tabla | 500 | 500 |
| Cola de revisión | presupuesto 68 % | cajas a revisar | 53.466 | 53.466 |
| Cola de revisión | presupuesto 68 % | horas (20 s por caja) | 297,0 | 297,0 |
| Cola de revisión | presupuesto 68 % | cobertura (tarjeta antes / frase ahora) | 96,5 % | 97 de cada 100 |
| Cola de revisión | presupuesto 68 % | filas de la tabla | 500 | 500 |
| Inicio | resultados técnicos | AUC fuera de fold | 0,823 | 0,823 |
| Inicio | resultados técnicos | Recall en el punto A | 79,8 % | 79,8 % |
| Inicio | resultados técnicos | Captura al revisar el 20 % | 61,9 % | 61,9 % |
| Inicio | resultados técnicos | Cajas a revisar para el 80 % | 44,6 % | 44,6 % |
| Inicio | resultados técnicos | Punto de equilibrio de la auditoría (en muestra) | 6059 cajas | 6.059 cajas |
| Explica una caja | valores por defecto | Puntaje | -50,000 | -50,000 |
| Explica una caja | valores por defecto | Lugar en la cola | entre el 59 % primero | entre el 59 % primero |
| Explica una caja | valores por defecto | Probabilidad calibrada de no tener pareja | 10,1 % | 10,1 % |
| Evidencia | tablas | número de tablas | 26 | 26 |

- **Tiempos de carga** (`pagina_tiempos_carga.json`, `AppTest`, datos reales; meta < 3 s). Con caché caliente cumplen las 8 secciones; **en frío cumplen 6 de 8** (las que cargan el modelo congelado, «Explica una caja» y «Puntuar datos nuevos», pasan de 3 s). No incluye el dibujado en un navegador.

| Sección | Caché caliente | En frío | Meta (caliente) | Meta (frío) |
|---|---|---|---|---|
| Inicio | 0,40 s | 2,40 s | sí | sí |
| Auditoría de cámaras | 0,44 s | 2,45 s | sí | sí |
| Cola de revisión | 0,50 s | 2,51 s | sí | sí |
| Explica una caja | 0,45 s | 3,44 s | sí | no |
| Evidencia | 0,59 s | 2,58 s | sí | sí |
| Ética y límites | 0,42 s | 2,40 s | sí | sí |
| Puntuar datos nuevos | 0,42 s | 3,20 s | sí | no |
| Ayuda y glosario | 0,44 s | 2,47 s | sí | sí |

- **Capturas:** no hay playwright; se usó el Chrome ya instalado en modo sin interfaz con el protocolo CDP (`scripts/ep3/capturar_pagina.py`, no se instaló nada). Se generaron las 8 secciones y el modo presentación en `images/ep3/pagina/`.
- Pruebas nuevas: `test_pagina_rediseno.py` (21: formatos es-CL, control inverso, textos «Todos» y segmento, fuente única, humo de 8 secciones x 3 perfiles x modo presentación, regresión de cifras, contraste, sin URLs y sin emojis) y `test_seleccion_nuevos.py` (13).

## Fase D. Cierre
- **D1. Guion** (9:15): frase corta de «en muestra», bloque final «lo que sabemos, lo que no sabemos y cómo lo vamos a saber», E2 gana en 5 de 5 folds pero bajo el umbral pre-declarado, palabras por bloque (ninguno supera 140 por minuto), columna «Quién» vacía, plan C (video de 90 s) y demo que sigue la página rediseñada con las cifras que muestra.
- **D2.** Informe, README_EP3, preguntas, guion, guía de demo, notebooks 11 a 15 (ejecutados con `RECALCULAR = False`; el 14 con las 8 secciones x 3 perfiles), MAPA, ESTADO, `plan_integracion_readme.md` y `docs/ep3/revision/` regenerados; los contadores de pruebas, preguntas, secciones y notebooks se leen del código.
- **D3 y D4.** `entrega_EP3.zip` y `entrega_EP3.sha256` rearmados (el tamaño y el hash no se escriben aquí porque el reporte va dentro del zip: están en `entrega_EP3.sha256` y en el reporte del chat). Venv nuevo de Python 3.10 en `C:/Users/maico/tmp_verificacion_ep3` (mismo equipo, no otra máquina): SHA256SUMS 818 de 818; EP2 14 de 14; v3 5 de 5; no supervisado 1 de 1; plan de selección coincide; `tests/ep3`: 97 pasadas y 1 omitida (falta el parquet crudo por licencia); página: 8 secciones x 3 perfiles x modo presentación = 48 combinaciones, 0 con falla. Detalle: `verificacion_copia_limpia.md`.
- **D5.** Congelados al final: ver el reporte del chat y `ESTADO.md`; EP2 14 de 14, v3 5 de 5 y no supervisado 1 de 1.

## Bloqueos y lo que te toca
- **Sin bloqueos.** Límites: Docker no se probó; AWS no se ejecutó; los tiempos son de servidor; el rediseño no se probó con personas.
- **Te toca:** (1) revisar y commitear (modelo v3 y plan de selección **antes** del Colab); (2) correr el Colab de segmentos nuevos y `evaluar_sellado` una sola vez, siguiendo `GUIA_VALIDACION_EXTERNA.md`; (3) revisar la guía de estilo y las capturas, y probar la página con alguien de cada perfil; (4) decidir si se precarga el modelo para bajar la carga en frío de las dos secciones lentas; (5) probar Docker con Docker Desktop encendido y una instalación en otra máquina; (6) el zip lleva datos derivados por caja: solo uso académico, no redistribuir.
