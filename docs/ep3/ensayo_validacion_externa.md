# Ensayo general de la validación externa (con datos de DESARROLLO)

**Esto es un ensayo con datos de desarrollo, no la validación externa.** Los 4 segmentos salen de `data/01_raw/waymo` (son parte de los 41 de desarrollo), así que **sus resultados no significan nada y no se usan para decidir nada**: el objetivo es probar la tubería de punta a punta (paquete del notebook 00b, `congelar`, `ingesta_nuevos`, `evaluar --ensayo`) antes de la corrida real. *Generado por `scripts/ep3/generar_ensayo_md.py` desde `data/08_reporting_ep3/ensayo_resultado.json` (lo escribe `scripts/ep3/ensayo_validacion_externa.py`).*

## Qué se armó
En `C:/Users/maico/tmp_verificacion_ep3/ensayo_nuevos/segmentos_nuevos_ep3/` la misma estructura que produce el notebook 00b: `lidar_box/`, `camera_to_lidar_box_association/` y `segmentos_nuevos_ep3.csv` con las columnas `segment_id`, `estrato`, `time_of_day`, `location`, `n_frames_inventario`, `asoc_filas`, `lidar_filas`, `positivos`, `tasa_etiquetado_pct` (las cifras se calculan con las mismas fórmulas que la celda de evaluación del notebook).

| Segmento | Estrato | Filas de asociación | Filas de lidar_box | Positivos | Tasa de etiquetado | Por qué se eligió |
|---|---|---|---|---|---|---|
| `257766998801` | Day / location_sf | 4.807 | 28.943 | 4.539 | 15,7 % | con hueco (camara 3) |
| `911012534050` | Day / location_sf | 1.522 | 7.005 | 1.399 | 26,0 % | con hueco (camara 5) |
| `102124064984` | Dawn/Dusk / location_sf | 973 | 13.421 | 817 | 6,1 % | normal y pequeno |
| `497181704156` | Day / location_phx | 410 | 3.251 | 355 | 21,9 % | normal y pequeno |

## Comandos reales (CLI) y medición
| Paso | Comando | Código de salida | Tiempo | Memoria máxima |
|---|---|---|---|---|
| 1. congelar (manifest alternativo) | `python scripts/ep3/evaluar_sellado.py congelar --lista C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos\segmentos_nuevos_ep3\segmentos_nuevos_ep3.csv --manifest C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos\manifest_nuevos_ensayo.json` | 0 | 1,0 s | 84 MB |
| 2. ingesta_nuevos (salida alternativa) | `python scripts/ep3/ingesta_nuevos.py --entrada C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos\segmentos_nuevos_ep3 --lista C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos\segmentos_nuevos_ep3\segmentos_nuevos_ep3.csv --salida C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos\nuevos_ensayo.parquet --resumen C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos\nuevos_resumen_ensayo.csv` | 0 | 1,0 s | 140 MB |
| 3. evaluar --ensayo | `python scripts/ep3/evaluar_sellado.py evaluar --ensayo --lista C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos\segmentos_nuevos_ep3\segmentos_nuevos_ep3.csv --manifest C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos\manifest_nuevos_ensayo.json --entrada C:\Users\maico\tmp_verificacion_ep3\ensayo_nuevos\nuevos_ensayo.parquet` | 0 | 3,8 s | 375 MB |

**Total: 5,8 s y 375 MB como máximo.** Con 4 segmentos pequeños; la corrida real (hasta 26 segmentos útiles) debería ser unas decenas de segundos (extrapolación, no medida).

## Comprobaciones
1. **Variables ingeridas contra `dev_41`** (llaves: segmento, marca de tiempo, objeto): 9.940 filas ingeridas y 9.940 en `dev_41`; solo en la ingesta: 0; solo en `dev_41`: 0; diferencia máxima en las 16 variables, `az_signed`, `c1` a `c5` y `sin_camara`: **0.0e+00** (tolerancia 1e-09); `en_zona_principal` igual: sí. **Coinciden: sí.**
2. **El detector marca las 2 celdas de referencia:** `257766998801|c3`, `911012534050|c5`. **Sí**; marcadas además de esas 2: 0.
3. **Salidas:** `externa_alternativas.csv`, `externa_brazos.csv`, `externa_detector.csv`, `externa_diferencias.csv`, `externa_lista_A.csv`, `externa_metricas.csv`, `externa_puntos.csv`; faltantes: 0. Incluye `externa_alternativas.csv` (las alternativas LR3 y XGBoost congeladas, DEV-4).
4. **Lo real quedó intacto:** `manifest_nuevos.json`, `nuevos.parquet` y el candado no se crearon ni modificaron: **sí**.
5. **Tasa de celdas marcadas con los dos denominadores** (con 4 segmentos; en desarrollo fue 2 de 111 celdas con >= 100 cajas):

| Denominador | Marcadas | Tasa | IC 95 % por segmentos |
|---|---|---|---|
| todas las celdas (segmento x camara) | 2 de 20 | 10,0 % | 0,0 % a 20,0 % |
| solo celdas con >= 100 cajas en el rango | 2 de 11 | 18,2 % | 0,0 % a 25,0 % |

## Qué se corrigió al preparar el ensayo (antes de la corrida final, que pasó sin excepciones)
- `scripts/ep3/ingesta_nuevos.py` escribía siempre en `data/05_model_input_ep3/nuevos.parquet` (el real): un ensayo lo habría pisado. Ahora acepta `--salida` y `--resumen` y se niega a sobrescribir un `nuevos.parquet` existente (salvo `--forzar`).
- `scripts/ep3/evaluar_sellado.py` tomaba el candado antes de calcular: una falla de cálculo habría gastado el único intento. Ahora calcula todo en memoria, toma el candado justo antes de escribir y guarda en él los sha256 de las salidas; comprueba antes las entradas con mensajes claros; y el modo `--ensayo` no toma candado ni toca el manifest real (exige `--manifest`).
- El notebook 00b: el plan sellado pasó a ser obligatorio, se comprueba su hash, y se simuló todo el flujo (con un `gsutil` simulado) en `tests/ep3/test_notebook_00b_simulado.py`.
- **No apareció ninguna excepción en el recorrido de punta a punta**; lo que se arregló fueron supuestos de diseño (rutas reales, orden del candado), no errores en ejecución.

## Lo que este ensayo NO prueba
- El acceso al bucket y las descargas reales de Colab (el notebook se probó con un `gsutil` simulado).
- Cómo se comporta el detector o la regla en segmentos nuevos (los datos son de desarrollo).
- Otra máquina u otro sistema operativo.
