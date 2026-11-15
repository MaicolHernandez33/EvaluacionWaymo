# Guía de la validación externa sellada (segmentos nuevos)

*Escrita antes de abrir ningún dato nuevo. Nada de lo que se describe aquí se ha ejecutado todavía. Comandos para Windows con `.venv\Scripts\python`; el notebook va en Google Colab.*

## 0. La garantía de sellado: qué debe estar commiteado ANTES de ejecutar el Colab
El sellado vale solo si lo que se va a evaluar queda fijado **antes** de ver los datos nuevos. Haga el commit de:
1. **El modelo v3**: `data/06_models_ep3/manifest_v3.json` (sus hashes) **y su copia en `artefactos_ep3/manifest_v3.json`** (la carpeta `data/` está ignorada por git, por eso la copia versionable es la de `artefactos_ep3/`). Comprobar antes: `.venv\Scripts\python scripts\ep3\verificar_congelados_v3.py` (5 de 5).
2. **El plan de selección**: `docs/ep3/plan_seleccion_ep3.json` y `docs/ep3/plan_seleccion_ep3.sha256` (parámetros, cuotas, embudo y orden de candidatos por estrato, calculados sin descargar nada). Comprobar: `.venv\Scripts\python scripts\ep3\plan_seleccion_ep3.py --verificar` (debe decir «coincide»).
3. `docs/ep3/plan_v3.*`, `plan_v3_desviaciones.md` (DEV-1 a DEV-3) y `notebooks/00b_seleccion_segmentos_ep3.ipynb`.

Si algo de esto cambia después de abrir los segmentos nuevos, la validación deja de ser ciega.

## 1. Preparar el Colab
1. Abra `notebooks/00b_seleccion_segmentos_ep3.ipynb` en Google Colab (cuenta de Google que aceptó los términos del Waymo Open Dataset).
2. En el paso 3 suba **los 3 CSV** de `docs/seleccion_segmentos/`: `inventario_segmentos.csv`, `registro_verificacion_ep2.csv` y `diagnostico_lluvia_ep2.csv`. Opcional pero recomendado: suba también `plan_seleccion_ep3.json` y `plan_seleccion_ep3.sha256` (el notebook comprueba que su orden de candidatos coincide con el plan sellado).
3. Ejecute **de arriba abajo, una vez**. El notebook se detiene si el embudo no da 793, 786 y 746 (como EP2): en ese caso no siga y repórtelo.
4. Es reanudable: si Colab se reinicia, vuelva a ejecutar todo; repite la misma secuencia y salta lo ya medido (`registro_verificacion_ep3.csv`).

## 2. Qué hace el notebook
- Pool igual al de EP2 → se excluyen los 91 evaluados → 655 candidatos.
- **Cuotas de segmentos útiles** (total 26): Day/sf 8, Day/phx 4, Day/other 2, Night/sf 3, Night/phx 2, Dawn-Dusk/sf 3, Dawn-Dusk/phx 3, Dawn-Dusk/other 1. Evaluación secuencial por estrato en el orden fijado por la semilla 42 (por rondas entre estratos), tope de 55 evaluaciones, meta mínima de 15 útiles.
- Muestra por estrato cuántos **faltan** y por qué (cuota completa, estrato agotado o tope global). Descarga solo `lidar_box` y `camera_to_lidar_box_association` de los candidatos y conserva solo los útiles.
- Entrega `segmentos_nuevos_ep3.tar.gz` (con `segmentos_nuevos_ep3.csv`, el registro completo, `resumen_cuotas_ep3.csv` y los parámetros) y su sha256.

## 3. Qué hacer si salen menos de 15 útiles
**No se reajusta nada con los datos** (ni umbrales, ni cuotas, ni parámetros del detector). Opciones, en este orden:
1. Si el notebook paró por el **tope de 55 evaluaciones** con menos de 15 útiles: subir el tope es una desviación del plan de selección; regístrela (DEV-4, con fecha y motivo) en `docs/ep3/plan_v3_desviaciones.md` **antes** de seguir evaluando candidatos, y continúe con el mismo orden (el notebook no cambia de orden).
2. Si faltan por **estrato agotado** (lo esperable de noche; `Night / location_other` no tiene candidatos): se acepta; se reporta «faltan» por estrato y que la noche queda mal representada.
3. Si con todo hay menos de 15, la validación igual se corre y se reporta como **no concluyente** (con pocos segmentos los IC por segmentos son muy anchos); no se completa con segmentos elegidos a mano.

## 4. En el repositorio (una sola vez, en este orden)
1. Descomprima el paquete en `data/01_raw_nuevos/` (queda `data/01_raw_nuevos/segmentos_nuevos_ep3/`).
2. **Congelar la lista (antes de abrir los datos):**
   `.venv\Scripts\python scripts\ep3\evaluar_sellado.py congelar --lista data\01_raw_nuevos\segmentos_nuevos_ep3\segmentos_nuevos_ep3.csv`
   (escribe `data/06_models_ep3/manifest_nuevos.json` con el sha256 de la lista y del manifest v3).
3. **Ingerir:**
   `.venv\Scripts\python scripts\ep3\ingesta_nuevos.py --entrada data\01_raw_nuevos\segmentos_nuevos_ep3 --lista data\01_raw_nuevos\segmentos_nuevos_ep3\segmentos_nuevos_ep3.csv`
   (escribe `data/05_model_input_ep3/nuevos.parquet` y `data/08_reporting_ep3/nuevos_resumen.csv`).
4. **Evaluar, una sola vez** (toma el candado `data/08_reporting_ep3/evaluacion_externa.lock`; una segunda corrida se niega):
   `.venv\Scripts\python scripts\ep3\evaluar_sellado.py evaluar --lista data\01_raw_nuevos\segmentos_nuevos_ep3\segmentos_nuevos_ep3.csv`
   Escribe `data/08_reporting_ep3/externa_metricas.csv`, `externa_diferencias.csv` (solución contra regla), `externa_puntos.csv` (puntos A y B), `externa_brazos.csv` (dos pasos contra un paso), `externa_detector.csv` (celdas marcadas) y `externa_lista_A.csv`.

Todo lo que salga se reporta tal cual, incluso si es negativo, y **no se usa para elegir ni reajustar nada**.

## 5. Qué se mide y cómo interpretar los tres casos
No hay verdad externa sobre qué celdas son huecos reales (DEV-3), así que **no se miden sensibilidad ni especificidad del detector**. Se mide: (i) la **tasa de celdas marcadas** (`externa_detector.csv`: `celdas_marcadas` sobre `celdas_totales`, con IC por segmentos); (ii) su **estabilidad** frente a las 30 combinaciones de parámetros (repetir el detector con esas combinaciones sobre los segmentos nuevos y comparar el conjunto marcado); (iii) opcional y post hoc, el paso con `camera_box` (sección 6).

| Caso | Cómo se ve | Cómo leerlo |
|---|---|---|
| **A. C igual a A porque no hay huecos** | `celdas_marcadas = 0`; en `externa_brazos.csv`: `celdas_auditadas = 0` y `Fraccion_80_C = Fraccion_80_A` | El flujo en dos pasos no aporta nada en estos segmentos porque no hay celdas que auditar; **no** refuta ni confirma el detector (con estos datos pudo no haber huecos). Mirar solo solución contra regla. |
| **B. Huecos encontrados** | `celdas_marcadas > 0`; `Fraccion_80_C` menor que `Fraccion_80_A`; `equilibrio_cajas_por_auditoria` definido | Evidencia a favor de que el filtro 1 encuentra algo fuera de la muestra de desarrollo. Reportar la diferencia C menos A con su IC por segmentos y el punto de equilibrio, y que ahora sí son segmentos no usados para ajustar los parámetros. No decir «el detector acierta»: sigue sin haber verdad externa. |
| **C. Marcas sin verificar** | `celdas_marcadas > 0` pero no se hizo (o no se pudo hacer) el paso con `camera_box` | Se sabe cuántas celdas marca el detector y que auditarlas ayuda (o no) a encontrar positivos, pero **no** si son lagunas de asociación, de etiquetado o de datos. Se reporta como «marcas sin verificar»; la causa sigue desconocida. |

## 6. Paso opcional y post hoc: `camera_box` (laguna de asociación frente a laguna de etiquetado o de datos)
**Solo si existe el componente `camera_box` (cajas 2D de cámara) en Waymo v2.** No está en el plan v3: es **post hoc, no pre-declarado**.
1. Confirmar el nombre real del componente con un `gsutil ls` previo (no asumir):
   `gsutil ls gs://waymo_open_dataset_v_2_0_1/training/ | findstr /i camera_box` (en Colab: `!gsutil ls gs://waymo_open_dataset_v_2_0_1/training/ | grep -i camera_box`). Si no aparece, omitir el paso y dejar los casos como «marcas sin verificar».
2. Para cada celda marcada (segmento x cámara) descargar solo el archivo de ese segmento: `gsutil cp gs://waymo_open_dataset_v_2_0_1/training/camera_box/<segmento>.parquet .` y contar las filas de esa cámara (`key.camera_name`).
3. Lectura: si esa cámara **tiene cajas 2D** en el segmento pero las cajas 3D del rango de azimut no tienen par → **laguna de asociación** (el 2D existe, falta el cruce). Si esa cámara **no tiene ninguna caja 2D** → **laguna de etiquetado o de datos** (no se distingue entre ambas con estos archivos).
4. Reportar como hipótesis post hoc, con la cuenta por celda, sin cambiar ninguna decisión.

## 7. Qué NO se puede concluir de esta validación
- Que el detector tenga cierta sensibilidad o especificidad (no hay verdad externa).
- Que la solución sirva en la noche o en otras ciudades si esos estratos quedan incompletos.
- Que los huecos sean errores de etiquetado (solo la comprobación opcional con `camera_box` da una pista).
