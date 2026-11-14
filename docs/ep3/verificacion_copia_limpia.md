# Verificación en copia limpia con entorno nuevo (2026-11-14)

**Alcance honesto.** Se hizo **en el mismo equipo** (no en otra máquina), con un **entorno virtual nuevo** (`C:\Users\maico\tmp_verificacion_ep3\venv_limpio`, Python 3.10.11) creado con el mismo Python 3.10 del equipo y distinto del `.venv` del repositorio. No prueba otro sistema operativo ni otra red. **No se ejecutó la suite completa de EP2 ni Docker.** El repositorio no se tocó: `git status` sigue mostrando solo `.gitignore` (las líneas autorizadas) y `tests/test_ajustes_finales.py` (cambio de antes) como modificados; `verificar_congelados.py` da 14 de 14 y `verificar_congelados_v3.py` 5 de 5 en el repositorio.

## Qué se hizo
1. Venv nuevo con `python -m venv` y, solo allí: `pip install -r requirements.txt -r requirements_ep3.txt -c constraints_ep3.txt` (versiones resultantes iguales a las de `constraints_ep3.txt`; `pip check`: sin requisitos rotos).
2. Se descomprimió `entrega_EP3.zip` (sha256 en `entrega_EP3.sha256`, fuera del zip porque un archivo no puede contener su propio hash) en otra carpeta de `tmp_verificacion_ep3` y, desde esa copia y con el intérprete del venv nuevo, se corrió todo. `PYTHONDONTWRITEBYTECODE=1`; sin `PYTHONPATH`. Se comprobó que `waymo_evaluacion` se importa desde `src` de la copia y no del repositorio.

## Hallazgos de la primera pasada (corregidos y repetidos)
La primera pasada **falló** por dos faltantes que el `.venv` de desarrollo ocultaba:
- `streamlit` y `altair` no estaban en `requirements_ep3.txt` (los usan `tests/ep3/test_app.py` y la página). Corregido: se agregaron (`streamlit==1.65.0`, `altair==6.2.2`). `requirements.txt` no se tocó.
- `waymo_evaluacion` solo se importaba porque el `.venv` la tiene instalada en modo editable; en el venv nuevo `tests/ep3` fallaba con `ModuleNotFoundError`. Corregido: `tests/ep3/conftest.py` agrega `src` al camino de búsqueda (no instala nada).

## Resultado de la segunda pasada (sobre el zip corregido)
| Comprobación | Comando (desde la copia, con el python del venv nuevo) | Resultado |
|---|---|---|
| Integridad del zip | `SHA256SUMS`: recalcular cada archivo | **760 de 760** coinciden; el sha256 del zip coincide con `entrega_EP3.sha256` |
| `LEEME_ENTREGA.md` | contar líneas | 12 líneas no vacías (máximo 15) |
| Congelados de EP2 | `python scripts/verificar_congelados.py` | **14 de 14** |
| Solución v3 | `python scripts/ep3/verificar_congelados_v3.py` | **5 de 5** (candidato Regla top) |
| No supervisado | `python scripts/ep3/verificar_no_supervisado.py` | **1 de 1** (k = 2) |
| Recolección de pruebas | `python -m pytest tests/ep3 --collect-only -q --no-cov -p no:cacheprovider` | **<!--n_ep3-->63<!--/n_ep3--> recolectadas** (EP2: <!--n_ep2-->81<!--/n_ep2-->; total <!--n_total-->144<!--/n_total-->) |
| Pruebas de EP3 | `python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider -rs` | **62 pasadas, 1 omitida** (~46 s) |
| Prueba de humo de la página | `streamlit.testing.v1.AppTest` de las 7 secciones con modo presentación | **7 de 7 sin errores**; el aviso «en muestra» está visible en Inicio y en Cola de revisión; con «Todos» y 20 % la Cola muestra recall esperado 70,2 % (dos pasos) |

**La prueba omitida** (`tests/ep3/test_inferencia.py::test_variables_reales_coinciden_con_dev41`) necesita el parquet crudo de `lidar_box`, que la entrega no incluye por licencia (igual que en EP2). En el repositorio completo pasan las <!--n_ep3-->63<!--/n_ep3-->.

## Qué incluye la entrega
Código, notebooks ejecutados, docs, images, app, `.streamlit/`, Dockerfile, compose, `requirements*`, `artefactos_ep3/` y los datos derivados mínimos: tablas de asociación de EP2 (sin `lidar_box` originales), `features_B.parquet`, `test.parquet`, modelos y plan congelados de EP2, resultados de EP2 y `data/05` a `09_*_ep3`. **Se excluyeron** `data/05_model_input/train.parquet` (32 MB; solo lo usan los notebooks de EP2) y los checkpoints `f4_ckpt` y `f5_ckpt` (se regeneran con `scripts/ep3/f4_ensambles.py`, unos 5 minutos, y `scripts/ep3/f5_loso_curva.py`); `f3_ckpt` sí va, porque la búsqueda tarda cerca de una hora.

## Limitaciones
- Mismo equipo, mismo sistema operativo y misma red: no prueba otra máquina. El zip descomprimido se verificó con un entorno nuevo, pero el instalador usó la caché de pip del equipo.
- El notebook 14 trae ejecutada una demostración que lee un `lidar_box` crudo: se entrega ejecutado, pero no se puede volver a ejecutar en la copia.
- Docker no se probó (el demonio estaba apagado); AWS no se ejecutó.
- Esta nota está dentro del zip: la copia verificada contenía la versión anterior de este archivo, y el zip final solo difiere de ella en este archivo y en `SHA256SUMS`.

**Licencia.** El zip contiene datos derivados del Waymo Open Dataset (uso no comercial): solo uso académico del docente; no redistribuir.
