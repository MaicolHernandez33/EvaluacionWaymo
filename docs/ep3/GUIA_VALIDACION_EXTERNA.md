# Guía de la validación externa sellada (segmentos nuevos)

*Escrita antes de abrir ningún dato nuevo (versión F19-A, 2026-11-15). Nada de lo que se describe aquí con segmentos nuevos se ha ejecutado todavía; lo que sí se ensayó (con datos de desarrollo) está en `ensayo_validacion_externa.md`. Comandos para Windows con `.venv\Scripts\python`; el notebook va en Google Colab.*

## 0. La garantía de sellado: qué debe estar commiteado ANTES de ejecutar el Colab
El sellado vale solo si lo que se va a evaluar queda fijado **antes** de ver los datos nuevos. Haga el commit de:
1. **El modelo v3 y las alternativas:** `artefactos_ep3/manifest_v3.json` y `artefactos_ep3/manifest_alternativas.json` (sus hashes; `data/` está ignorado por git, por eso las copias versionables están en `artefactos_ep3/`). Comprobar antes: `.venv\Scripts\python scripts\ep3\verificar_congelados_v3.py` (5 de 5) y que `data/06_models_ep3/manifest_alternativas.json` sea idéntico a la copia.
2. **El plan de selección:** `docs/ep3/plan_seleccion_ep3.json` y `docs/ep3/plan_seleccion_ep3.sha256` (parámetros, cuotas, embudo y orden de candidatos, calculados sin descargar nada). Comprobar: `.venv\Scripts\python scripts\ep3\plan_seleccion_ep3.py --verificar` (debe decir «coincide»).
3. `docs/ep3/plan_v3.*`, `plan_v3_desviaciones.md` (DEV-1 a DEV-4), el notebook `notebooks/00b_seleccion_segmentos_ep3.ipynb` y esta guía.

Si algo de esto cambia después de abrir los segmentos nuevos, la validación deja de ser ciega.

## 1. Ensayo general (antes de la corrida real)
Con **datos de desarrollo** (4 segmentos de `data/01_raw/waymo`; no son segmentos nuevos y sus resultados no valen nada) se prueba la tubería de punta a punta con el CLI real, sin tocar nada de lo real:
```
.venv\Scripts\python scripts\ep3\ensayo_validacion_externa.py
.venv\Scripts\python scripts\ep3\generar_ensayo_md.py
```
Arma la misma estructura que el notebook 00b en `C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos`, corre `congelar` (con `--manifest` alternativo), `ingesta_nuevos` (con `--salida` alternativa) y `evaluar --ensayo`, y comprueba que las variables ingeridas coinciden con `dev_41`, que el detector marca las 2 celdas de referencia y que se escriben todas las salidas `externa_*`. Debe terminar con `todo_ok: true`. Se puede repetir las veces que haga falta: el ensayo **no toma candado, no lee ni sobrescribe el `manifest_nuevos.json` real** y escribe en `data/08_reporting_ep3/ensayo_externa/`.

## 2. Preparar y correr el Colab
1. Abra `notebooks/00b_seleccion_segmentos_ep3.ipynb` en Google Colab (cuenta de Google que aceptó los términos del Waymo Open Dataset).
2. En el paso 3 suba **los 5 archivos, todos obligatorios:** los 3 CSV de `docs/seleccion_segmentos/` (`inventario_segmentos.csv`, `registro_verificacion_ep2.csv`, `diagnostico_lluvia_ep2.csv`) **y** `docs/ep3/plan_seleccion_ep3.json` y `docs/ep3/plan_seleccion_ep3.sha256`. Sin los cinco, o si el hash del plan no coincide o la versión no es `plan_seleccion_ep3_v1`, el notebook se detiene antes de tocar el bucket.
3. Ejecute **de arriba abajo, una vez.** El notebook usa el orden de candidatos **del plan** (verificado por hash) y recalcula el suyo para compararlo: si en Colab difiere (por ejemplo por la versión de numpy), imprime una **advertencia visible**, sigue con el del plan y lo deja anotado. Se detiene si el embudo no da 793, 786 y 746 (como EP2), si el paso «con `lidar_box` y asociación» no da 793, o si el embudo difiere en conteos del plan. En ese caso no siga y repórtelo.
4. Es reanudable: si Colab se reinicia, vuelva a ejecutar todo; repite la misma secuencia y salta lo ya medido (`registro_verificacion_ep3.csv`).
5. Al final entrega `segmentos_nuevos_ep3.tar.gz` y su sha256. **Guarde también `verificacion_colab.json`** (dentro del paquete): trae el hash del plan, las versiones de numpy, pandas y Python de Colab, el embudo, las cuotas y si el orden recalculado coincidió.

## 3. Qué hacer si salen menos de 15 útiles
**No se reajusta nada con los datos** (ni umbrales, ni cuotas, ni parámetros del detector). Opciones, en este orden:
1. Si el notebook paró por el **tope de 55 evaluaciones** con menos de 15 útiles: subir el tope es una desviación del plan de selección; regístrela (DEV-5, con fecha y motivo) en `docs/ep3/plan_v3_desviaciones.md` **antes** de seguir evaluando candidatos, y continúe con el mismo orden (el notebook no cambia de orden).
2. Si faltan por **estrato agotado** (lo esperable de noche; `Night / location_other` no tiene candidatos): se acepta; se reporta «faltan» por estrato y que la noche queda mal representada.
3. Si con todo hay menos de 15, la validación igual se corre y se reporta como **no concluyente** (con pocos segmentos los intervalos por segmentos son muy anchos); no se completa con segmentos elegidos a mano.

## 4. En el repositorio, en este orden (una sola vez)
1. Descomprima el paquete en `data/01_raw_nuevos/` (queda `data/01_raw_nuevos/segmentos_nuevos_ep3/`) y mire `verificacion_colab.json` (¿`orden_recalculado_coincide_con_el_plan`? ¿versiones?).
2. **Congelar la lista, antes de abrir los datos:**
   `.venv\Scripts\python scripts\ep3\evaluar_sellado.py congelar --lista data\01_raw_nuevos\segmentos_nuevos_ep3\segmentos_nuevos_ep3.csv`
   Escribe `data/06_models_ep3/manifest_nuevos.json` con el sha256 de la lista, de `manifest_v3.json` y de `manifest_alternativas.json`. Se niega a sobrescribir uno existente.
3. **Copiar el sello a `artefactos_ep3/` y COMMITEARLO antes de evaluar:**
   `.venv\Scripts\python scripts\ep3\copiar_sello_a_artefactos.py --lista data\01_raw_nuevos\segmentos_nuevos_ep3\segmentos_nuevos_ep3.csv`
   Verifica los hashes y copia `manifest_nuevos.json`, `manifest_alternativas.json`, `manifest_v3.json` y `segmentos_nuevos_ep3.csv` (la lista; no lleva datos por caja, solo una fila por segmento). **Haga el commit de esos archivos ahora.** Esa es la prueba de que el modelo, las alternativas y la lista estaban fijados antes de evaluar.
4. **Ingerir:**
   `.venv\Scripts\python scripts\ep3\ingesta_nuevos.py --entrada data\01_raw_nuevos\segmentos_nuevos_ep3 --lista data\01_raw_nuevos\segmentos_nuevos_ep3\segmentos_nuevos_ep3.csv`
   (escribe `data/05_model_input_ep3/nuevos.parquet` y `data/08_reporting_ep3/nuevos_resumen.csv`; se niega a sobrescribir un `nuevos.parquet` existente).
5. **Evaluar, una sola vez:**
   `.venv\Scripts\python scripts\ep3\evaluar_sellado.py evaluar --lista data\01_raw_nuevos\segmentos_nuevos_ep3\segmentos_nuevos_ep3.csv`
   Comprueba las entradas, verifica todos los hashes, calcula todo en memoria y **solo si el cálculo terminó bien** toma el candado (`data/08_reporting_ep3/evaluacion_externa.lock`) y escribe de inmediato `externa_metricas.csv`, `externa_diferencias.csv`, `externa_puntos.csv`, `externa_brazos.csv`, `externa_detector.csv`, `externa_lista_A.csv` y `externa_alternativas.csv`; los sha256 de esas salidas quedan **dentro del candado**.

Todo lo que salga se reporta tal cual, incluso si es negativo, y **no se usa para elegir ni reajustar nada**.

## 5. Si `evaluar` falla antes de tomar el candado
**No se consumió el único intento.** El mensaje empieza con `DETENIDO:` o es una excepción de Python; mire cuál:
- **«no existe la lista / el manifest / la tabla de segmentos nuevos»:** falta un paso (`congelar` o `ingesta_nuevos`) o una ruta; haga el paso que falta y repita el mismo comando. El mensaje enumera todo lo que falta.
- **«la lista de segmentos cambió», «manifest_v3.json cambió», «alternativas congeladas: … cambió», «manifest_alternativas.json apareció después de congelar la lista»:** algo se modificó después de sellar. **No vuelva a congelar para tapar la diferencia:** averigüe qué cambió (compare con las copias commiteadas de `artefactos_ep3/`); si fue un accidente, restaure el archivo desde el commit.
- **Excepción durante el cálculo:** es un error de código, no un resultado. Corríjalo (y si hay que tocar código, regístrelo como desviación con fecha y motivo), pruébelo con `evaluar --ensayo` sobre los datos de desarrollo y repita el mismo comando.
- Antes de gastar el intento, puede ensayar **con los datos reales** sin tomar candado: `evaluar --ensayo --lista … --manifest <copia de manifest_nuevos.json> --entrada data\05_model_input_ep3\nuevos.parquet` (escribe en `data/08_reporting_ep3/ensayo_externa/`). Verá los mismos números que luego saldrán de la corrida real, así que **mírelos solo para detectar errores, no para decidir nada**.

Si falló **después** de tomar el candado (por ejemplo, al escribir las salidas), el candado ya trae los sha256 que debían tener: repita el cálculo con `evaluar --ensayo --salida <otra carpeta>` (es determinista: semilla 42) y compare los sha256 de los archivos con los del candado.

## 6. Qué se mide: solución contra regla da 0 por construcción
El puntaje de la solución congelada v3 **es** la regla «menos puntos del sensor superior» (`PuntuadorRegla` en `src/waymo_evaluacion/ep3/congelado.py`, cargado por `inferencia.py`; una prueba lo comprueba). Por eso `externa_diferencias.csv` (solución menos regla) **da 0 por construcción**: no informa y no hay que leerlo como un empate sorprendente. Lo que sí se mide:
- el **desempeño de la regla fuera de muestra** (`externa_metricas.csv`: AUC, PR-AUC, captura al 20 % y fracción para el 80 %, con intervalo por segmentos);
- su **recall y precisión con los umbrales A = 32 y B = 11 congelados** (`externa_puntos.csv`; A y B son «32 puntos o menos» y «11 puntos o menos» en el sensor superior);
- el **brazo C contra A** (`externa_brazos.csv`: fracción para el 80 % con y sin auditar las celdas marcadas, punto de equilibrio);
- la **tasa de celdas marcadas** (`externa_detector.csv`) **con dos denominadores**, cada uno con su intervalo por segmentos: todas las celdas (segmento × cámara) y solo las celdas con ≥ 100 cajas en el rango (en desarrollo: 2 de 111);
- las **alternativas congeladas** LR3 y XGBoost contra la regla (`externa_alternativas.csv`: diferencia de AUC y de fracción para el 80 % con intervalo pareado por segmentos). Son DEV-4: post hoc respecto del plan v3, congeladas antes de abrir datos y **sin cambiar la solución elegida**. En AUC, una diferencia positiva favorece a la alternativa; en fracción para el 80 %, una negativa (revisa menos cajas).

## 7. Cómo se verá cada caso de resultado
No hay verdad externa sobre qué celdas son huecos reales (DEV-3): **no se miden sensibilidad ni especificidad del detector**; se mide la tasa de celdas marcadas, su estabilidad frente a las 30 combinaciones de parámetros (repetir el detector con esas combinaciones sobre los segmentos nuevos y comparar el conjunto marcado) y, opcionalmente, el paso con `camera_box` (sección 8).

| Caso | Cómo se ve | Cómo leerlo |
|---|---|---|
| **A. C igual a A porque no hay huecos** | `externa_detector.csv`: `celdas_marcadas = 0` en las dos filas; `externa_brazos.csv`: `celdas_auditadas = 0` y `Fraccion_80_C = Fraccion_80_A`; `externa_lista_A.csv` vacío | El flujo en dos pasos no aporta nada en estos segmentos porque no hay celdas que auditar; **no** refuta ni confirma el detector (pudo no haber huecos). Mirar el desempeño de la regla y las alternativas. |
| **B. Huecos encontrados** | `celdas_marcadas > 0`; `Fraccion_80_C` menor que `Fraccion_80_A`; `equilibrio_cajas_por_auditoria` definido | Evidencia a favor de que el filtro 1 encuentra algo fuera de la muestra de desarrollo. Reportar la diferencia con su intervalo por segmentos y el punto de equilibrio, y que ahora son segmentos no usados para ajustar los parámetros. Mirar la tasa con **ambos** denominadores: con 2 de 111 en desarrollo, una tasa nueva muy distinta dice que el detector se comporta distinto fuera de muestra. No decir «el detector acierta»: sigue sin haber verdad externa. |
| **C. Marcas sin verificar** | `celdas_marcadas > 0` pero no se hizo (o no se pudo hacer) el paso con `camera_box` | Se sabe cuántas celdas marca el detector y que auditarlas ayuda (o no) a encontrar positivos, pero **no** si son lagunas de asociación, de etiquetado o de datos. Se reporta como «marcas sin verificar»; la causa sigue desconocida. |
| **D. Una alternativa «gana»** | `externa_alternativas.csv`: `excluye_0 = True` con diferencia de AUC positiva (o de fracción negativa) | Es un hallazgo post hoc (DEV-4): se reporta, **no cambia la solución elegida** ni se usa para reajustar; sirve para decidir una EP4 o una validación nueva. Con pocos segmentos, lo más probable es `excluye_0 = False`: «no distinguible». |

## 8. Paso opcional y post hoc: `camera_box` (laguna de asociación frente a laguna de etiquetado o de datos)
**Solo si existe el componente `camera_box` (cajas 2D de cámara) en Waymo v2.** No está en el plan v3: es **post hoc, no pre-declarado**.
1. Confirmar el nombre real del componente con un `gsutil ls` previo (no asumir): `gsutil ls gs://waymo_open_dataset_v_2_0_1/training/ | findstr /i camera_box` (en Colab: `!gsutil ls gs://waymo_open_dataset_v_2_0_1/training/ | grep -i camera_box`). Si no aparece, omitir el paso y dejar los casos como «marcas sin verificar».
2. Para cada celda marcada (segmento × cámara) descargar solo el archivo de ese segmento: `gsutil cp gs://waymo_open_dataset_v_2_0_1/training/camera_box/<segmento>.parquet .` y contar las filas de esa cámara (`key.camera_name`).
3. Lectura: si esa cámara **tiene cajas 2D** en el segmento pero las cajas 3D del rango de azimut no tienen par → **laguna de asociación** (el 2D existe, falta el cruce). Si esa cámara **no tiene ninguna caja 2D** → **laguna de etiquetado o de datos** (no se distingue entre ambas con estos archivos).
4. Reportar como hipótesis post hoc, con la cuenta por celda, sin cambiar ninguna decisión.

## 9. Qué NO se puede concluir de esta validación
- Que el detector tenga cierta sensibilidad o especificidad (no hay verdad externa).
- Que «la solución supera a la regla»: la solución **es** la regla; solo las alternativas (DEV-4) pueden compararse con ella.
- Que la solución sirva en la noche o en otras ciudades si esos estratos quedan incompletos.
- Que los huecos sean errores de etiquetado (solo la comprobación opcional con `camera_box` da una pista).
