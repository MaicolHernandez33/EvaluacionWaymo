# Verificación en copia limpia con entorno nuevo (F18, 2026-11-15)

**Alcance honesto.** Se hizo **en el mismo equipo** (no en otra máquina), con un **entorno virtual nuevo** (`C:\Users\maico\tmp_verificacion_ep3\venv_f18`, Python 3.10.11) creado con `python -m venv` y distinto del `.venv` del repositorio. **No se ejecutó la suite completa de EP2 ni Docker.** El repositorio no se tocó durante la verificación; los congelados dan EP2 14 de 14, v3 5 de 5 y no supervisado 1 de 1 al inicio y al final.

## Qué se hizo
1. Venv nuevo y, solo allí: `pip install -r requirements.txt -r requirements_ep3.txt -c constraints_ep3.txt` (sin errores; instaló `streamlit` y `altair` desde `requirements_ep3.txt`, corregido en la verificación anterior).
2. Se descomprimió `entrega_EP3.zip` (sha256 en `entrega_EP3.sha256`, fuera del zip porque un archivo no puede contener su propio hash) en otra carpeta de `tmp_verificacion_ep3` y, desde esa copia y con el intérprete del venv nuevo, sin `PYTHONPATH`, se corrió todo. `PYTHONDONTWRITEBYTECODE=1`. Se comprobó que `waymo_evaluacion` se importa desde `src` de la copia.

## Resultado (zip verificado)
| Comprobación | Comando (desde la copia, con el python del venv nuevo) | Resultado |
|---|---|---|
| Integridad del zip | `SHA256SUMS`: recalcular cada archivo | **818 de 818** coinciden; el sha256 del zip coincide con `entrega_EP3.sha256` |
| Congelados de EP2 | `python scripts/verificar_congelados.py` | **14 de 14** |
| Solución v3 | `python scripts/ep3/verificar_congelados_v3.py` | **5 de 5** (candidato Regla top) |
| No supervisado | `python scripts/ep3/verificar_no_supervisado.py` | **1 de 1** (k = 2) |
| Plan de selección de segmentos nuevos | `python scripts/ep3/plan_seleccion_ep3.py --verificar` | **coincide** con su sha256 |
| Recolección de pruebas | `python -m pytest tests/ep3 --collect-only -q --no-cov -p no:cacheprovider` | **<!--n_ep3-->98<!--/n_ep3--> recolectadas** (EP2: <!--n_ep2-->81<!--/n_ep2-->; total <!--n_total-->179<!--/n_total-->) |
| Pruebas de EP3 | `python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider -rs` | **97 pasadas, 1 omitida** (~58 s) |
| Prueba de humo de la página | `AppTest` de **8 secciones x 3 perfiles x modo presentación activado y desactivado** con los datos reales de la copia | **48 combinaciones, 0 con falla**; el aviso «en muestra» está visible en Inicio y en Cola de revisión |

**La prueba omitida** (`tests/ep3/test_inferencia.py::test_variables_reales_coinciden_con_dev41`) necesita el parquet crudo de `lidar_box`, que la entrega no incluye por licencia. En el repositorio completo pasan las <!--n_ep3-->98<!--/n_ep3-->.

## Qué incluye la entrega
Código, notebooks ejecutados (el 00b es de Colab y no se ejecuta aquí), docs, images (incluidas las capturas de la página), app, `.streamlit/`, Dockerfile, compose, `requirements*`, `artefactos_ep3/` y los datos derivados mínimos (sin `lidar_box` originales). **Se excluyeron** `data/05_model_input/train.parquet` y los checkpoints `f4_ckpt` y `f5_ckpt` (se regeneran con `scripts/ep3/f4_ensambles.py` y `f5_loso_curva.py`); `f3_ckpt` sí va.

## Limitaciones
- Mismo equipo, mismo sistema operativo y misma red: no prueba otra máquina. El instalador usó la caché de pip del equipo.
- El notebook 14 trae ejecutada una demostración que lee un `lidar_box` crudo: se entrega ejecutado, pero no se puede volver a ejecutar en la copia.
- Los tiempos de carga de la página son de servidor (`AppTest`); no incluyen el dibujado en un navegador.
- Docker no se probó (el demonio estaba apagado); AWS no se ejecutó.
- Esta nota está dentro del zip: la copia verificada contenía la versión anterior de este archivo, y el zip final solo difiere de ella en los documentos de cierre (este archivo, `REPORTE_F18.md` y `ESTADO.md`) y en `SHA256SUMS`; el código y los datos son idénticos. El zip final lista **820** archivos en `SHA256SUMS` (los 818 verificados más `f18_verificacion.json`, en `data/08_reporting_ep3` y en `artefactos_ep3`, que registra este resultado); la segunda comprobación (zip final) está en el reporte del chat y repite SHA256SUMS, congelados, pruebas y humo.

**Licencia.** El zip contiene datos derivados del Waymo Open Dataset (uso no comercial): solo uso académico del docente; no redistribuir.
