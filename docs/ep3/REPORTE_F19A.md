# Reporte de la tarea F19-A: preparar el sello antes del Colab

*Generado por `scripts/ep3/generar_reporte_f19a.py`; cifras de `data/08_reporting_ep3/ensayo_resultado.json` y `f19_alternativas_congeladas.json`. Decisiones: `ESTADO.md` (DEC-41 a DEC-46, sección F19). El zip NO se rearmó (lo hace la tarea siguiente).*

## Resumen
Se preparó todo lo que hace falta **antes** de abrir segmentos nuevos: el notebook 00b exige y verifica el plan sellado; la evaluación toma el candado solo cuando el cálculo terminó bien; un ensayo general de punta a punta con datos de desarrollo pasó sin excepciones; se verificó y documentó que «solución contra regla» da 0 por construcción y, para que la validación diga algo, se congelaron dos alternativas (LR3 y XGBoost; DEV-4). Los congelados no cambiaron: EP2 14 de 14, v3 5 de 5, no supervisado 1 de 1. Pruebas de EP3 recolectadas al momento de F19-A: 116; hoy son 177 (`pruebas_ep3_conteo.json`: el rediseño de F19-B y F20 agregó pruebas).

## Tarea 1. Notebook 00b (`scripts/ep3/crear_notebook_00b.py`)
- **Qué encontré:** subir el plan era opcional; el orden que se usaba era el recalculado en Colab (dependiente de la versión de numpy); no había conteo de `lidar_box` y asociación; `gsutil ls` no comprobaba su código de salida; los temporales del candidato anterior podían quedar; la subida parcial de archivos no se reintentaba.
- **Qué cambié:** (a) los 5 archivos son obligatorios, con `assert` de existencia, sha256 y versión `plan_seleccion_ep3_v1`; (b) se **usa el orden del plan** y el recalculado solo se compara (si difiere: advertencia visible en rojo y se sigue con el del plan); el embudo debe coincidir con los conteos del plan y con 793, 786, 746, 655; (c) `verificacion_colab.json` (hash del plan, versiones de numpy, pandas y Python, embudo, cuotas, si el orden coincidió) se imprime y va en el paquete; (d) limpieza de temporales, reanudación, comprobación de `gsutil ls` y del 793. `seleccion_nuevos.py` no se tocó y su código embebido sigue idéntico (su prueba pasa).
- **Cómo lo probé:** `tests/ep3/test_notebook_00b_simulado.py` ejecuta todas las celdas del notebook con un `gsutil` simulado (los candidatos del plan se mapean a archivos locales de desarrollo): faltan archivos, hash que no coincide, flujo completo con paquete y reanudación sin descargar nada, y la rama del orden distinto.

## Tarea 2. Candado y CLI (`sellado.py`, `evaluar_sellado.py`, `ingesta_nuevos.py`)
- **Qué encontré:** `evaluar` tomaba el candado antes de calcular (una falla de cálculo gastaba el único intento) y no comprobaba las entradas; la ingesta escribía siempre en el `nuevos.parquet` real.
- **Qué cambié:** `ejecutar_evaluacion` comprueba entradas (mensajes claros, lista todo lo que falta), verifica hashes (incluidas las alternativas), calcula todo en memoria, **toma el candado (creación exclusiva) solo cuando el cálculo terminó** y escribe las salidas de inmediato guardando sus sha256 en el candado. `--ensayo` no toma candado, exige `--manifest` distinto del real y escribe en `data/08_reporting_ep3/ensayo_externa/`. `congelar` se niega a sobrescribir. La tasa de celdas marcadas sale con **dos denominadores** (todas las celdas; solo las de >= 100 cajas), cada una con su IC por segmentos. 14 pruebas nuevas (`test_sellado_f19.py`): una falla de cálculo no consume el candado, una segunda corrida se niega, el ensayo no toca lo real, faltan entradas, cambios en lista o alternativas, y el CLI.

## Tarea 3. Ensayo general (`ensayo_validacion_externa.md`)
Con 4 segmentos de desarrollo (2 con hueco y 2 pequeños) y el CLI real, **sin excepciones**. Es un ensayo con datos de desarrollo: sus resultados no valen nada.

| Paso | Tiempo | Memoria máxima | Código |
|---|---|---|---|
| 1. congelar (manifest alternativo) | 1,0 s | 84 MB | 0 |
| 2. ingesta_nuevos (salida alternativa) | 1,0 s | 140 MB | 0 |
| 3. evaluar --ensayo | 3,8 s | 375 MB | 0 |

- Variables ingeridas contra `dev_41`: 9940 filas contra 9940; diferencia máxima 0.0e+00 (tolerancia 1e-09): **coinciden**.
- El detector marca las 2 celdas de referencia: **sí**; salidas escritas: 7 (faltantes: 0); lo real quedó intacto: **sí**. Total 5,8 s y 375 MB.
- **Excepciones corregidas:** ninguna apareció en el recorrido; lo que se corrigió fueron supuestos de diseño (rutas reales en la ingesta, orden del candado).

## Tarea 4. Solución contra regla
- **4a.** El puntaje de la solución congelada es `PuntuadorRegla(num_top_lidar_points)` (menos el número de puntos del sensor superior): monótono con la regla, así que «solución contra regla» da **diferencia 0 por construcción**. Dicho en la guía, en el informe §14 (generador), en `evaluar_sellado.py` y en `evaluar_externo`; una prueba lo comprueba. Lo que se mide: el desempeño de la regla fuera de muestra, recall y precisión con A = 32 y B = 11, brazo C contra A y tasa de celdas marcadas.
- **4b. Decisión: se dejó, no se revirtió.** LR3 y XGBoost se entrenaron con los 41 segmentos y se guardaron en `data/06_models_ep3/alternativas_v3.joblib` con `manifest_alternativas.json` (sha256) aparte; `manifest_v3.json` no se tocó. **Cómo elegí la configuración de XGBoost:** la más repetida entre los 5 folds externos de `f3_config_por_fold.csv` (etapa principal): V_OBS, `max_depth` 2, `learning_rate` 0,1165, `n_estimators` 30, `reg_lambda` 29,5, `subsample` 0.7, `colsample_bytree` 0.8, `min_child_weight` 100, elegida por 2 de 5 folds (empate: fold de menor índice; es distinta de `config_final`, que usa IE10). LR3 no tiene hiperparámetros que elegir. `evaluar_externo` compara cada alternativa con la regla (AUC y fracción para el 80 %, IC pareado por segmentos) y escribe `externa_alternativas.csv`; `congelar` y `evaluar` verifican su hash. Quedó sólido y probado muy por debajo de las 3 horas. DEV-4 en `plan_v3_desviaciones.md`.

## Tarea 5. Guía (`GUIA_VALIDACION_EXTERNA.md`)
Reescrita con: los 5 archivos del Colab, el ensayo previo, copiar el sello a `artefactos_ep3/` con `scripts/ep3/copiar_sello_a_artefactos.py` y **commitear antes de evaluar** (lista sin datos por caja), qué hacer si `evaluar` falla antes de tomar el candado (y cómo recuperar si falla después), la aclaración de la tarea 4a y cómo se verá cada caso de resultado (A: sin huecos; B: huecos; C: marcas sin verificar; D: una alternativa «gana»).

## Tarea 6. Cierre
Documentos regenerados (informe, guía, MAPA, ESTADO, revisión) y verificaciones; el zip no se rearmó.

## Lo que te toca
1. Revisar y **commitear antes del Colab**: `artefactos_ep3/manifest_v3.json`, `artefactos_ep3/manifest_alternativas.json`, `docs/ep3/plan_seleccion_ep3.json` y `.sha256`, el notebook 00b y la guía (la carpeta `data/` está ignorada por git: las copias versionables están en `artefactos_ep3/`).
2. Correr el Colab con los 5 archivos y guardar `verificacion_colab.json`; luego `congelar`, `copiar_sello_a_artefactos.py`, **commit**, `ingesta_nuevos` y `evaluar` (una sola vez), siguiendo la guía.
3. Decidir si mantener las alternativas (DEV-4) o retirarlas antes de congelar la lista (el prompt siguiente rearma el zip).
