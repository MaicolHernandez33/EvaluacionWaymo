# CLAUDE.md — waymo-evaluacion (EP3 en curso)

## Proyecto
Curso MLY1101 Machine Learning. Waymo Open Dataset v2 (bucket `gs://waymo_open_dataset_v_2_0_1/training/`).
Objetivo: lista priorizada para que una persona revise primero las cajas 3D (LiDAR) de peatones y ciclistas
que probablemente no tienen su par 2D de cámara. Siempre hay una persona que revisa y decide.
- **Target:** `sin_camara` (1 = la caja 3D no tiene par en ninguna de las 5 cámaras).
- **Población principal:** |azimut| <= 100° (`AZ_MAX` en `data/05_model_input/config_features_B.json`); 120° es solo sensibilidad.
- **EP2 (entregada):** 41 segmentos (33 train, 8 test), validación por segmento (GroupKFold), plan de test congelado.
- **EP3:** ensambles, hiperparámetros, generalización y selección. Se valida con un **plan v3 congelado antes de abrir segmentos nuevos**.

## Stack (venv `.venv`, Python 3.10.11)
pandas 2.3.3 · numpy 2.2.6 · scikit-learn 1.7.2 · scipy 1.15.3 · joblib 1.5.3 · pyarrow 25.0.1 · kedro 1.5.0
EP3 agrega xgboost 3.2.0 y lightgbm 4.7.0 (`requirements_ep3.txt`). Las versiones de arriba están fijadas en `constraints_ep3.txt`:
instalar siempre con `pip install ... -c constraints_ep3.txt` y detenerse si pip quiere cambiar alguna.
Semilla global: **42**. `requirements.txt` no se toca.

## Reglas estrictas
- Sin commit ni push. Sin `git clean`, `reset`, `checkout`, `restore` ni `stash`.
- Solo lectura sobre EP2: `data/06_models/*`, `data/05_model_input/*`, `data/08_reporting/*`, `plan_evaluacion_test*`,
  notebooks 00 a 10, `README.md`, `docs/informe_tecnico_EP2.md`.
- **No ejecutar `pytest`** hasta nuevo aviso: varios tests ejecutan `generar_readme.py` y `generar_informe_tecnico.py`
  y reescriben README, informe y parquets de `data/02_intermediate`. Tampoco notebooks ni scripts generadores.
- No descargar datos del bucket sin autorización explícita. `gcloud`/`gsutil` no están instalados.
- Si algo exige salirse de estas reglas, detenerse y preguntar.

## Archivos congelados de EP2 (14; `python scripts/verificar_congelados.py` debe decir 14 de 14)
- `data/06_models/`: `lr_B`, `hgb_B`, `rf_B`, `lr_minimo_B`, `calibrador_B`, `lr_B120`, `hgb_B120`, `rf_B120`,
  `lr_minimo_B120` (todos `.joblib`), `hiperparametros_B.json`, `hiperparametros_B120.json`, `plan_evaluacion_test_v1.json`
- `data/05_model_input/`: `features_B.parquet`, `config_features_B.json`
- El plan vigente es `data/06_models/plan_evaluacion_test.json` (v2). `10_hashes_ejecucion1.json` registra 16 hashes
  (15 de `data/08_reporting/10_*` y `pred_test_B.parquet`, que difiere por ruido de coma flotante de 3,3e-16; está en el log de EP2).

## Convenciones EP3
- Todo lo nuevo vive en carpetas `*_ep3` y solo en: `docs/ep3/`, `scripts/ep3/`, `src/waymo_evaluacion/ep3/`, `tests/ep3/`,
  `images/ep3/`, `data/05_model_input_ep3`, `data/06_models_ep3`, `data/07_model_output_ep3`, `data/08_reporting_ep3`,
  `requirements_ep3.txt`, `constraints_ep3.txt` y este archivo.
- `data/**` está en `.gitignore`: lo que quede en `data/*_ep3` no se versiona salvo que se cambie esa regla.
- Los tests de EP3 escriben solo en `tmp_path` (nunca en `data/` ni en `docs/`). `tests/ep3/` es paquete (`__init__.py`).
- `pytest` recoge `tests/` completo (sin `testpaths`) y `test_ajustes_finales.py` compara el total de pruebas con el README (81):
  agregar tests en `tests/ep3/` rompe esa comparación de EP2 (pendiente decidir cómo aislarlos).
- Los modelos congelados se cargan con `joblib.load` solo para leer; nunca se reentrenan ni se sobrescriben.
- Rutas con `pathlib`, `random_state=42`, validación siempre por segmento (`GroupKFold`/`groups=segment_id`).

## Dónde mirar
- README.md (visión general), `docs/informe_tecnico_EP2.md`, `docs/log_trabajo_ep2.md` (decisiones y hallazgos de EP2).
- Selección de segmentos: `docs/seleccion_segmentos/` (el código que la genera no está en el repo; no existe `00b`).
- Apéndice M (huecos por cámara): código suelto en las celdas 46 a 59 del notebook 10 (aún sin extraer a función).

## EP3 final (estado al 2026-11-14)
- Plan v3 congelado: `docs/ep3/plan_v3.md|json` con hash en `plan_v3.sha256`; cambios solo en `plan_v3_desviaciones.md` (D-1: 1 repetición y 30 configuraciones; D-2: regla de reserva porque nadie cumple O4, post hoc). Verificar con `python scripts/ep3/verificar_congelados_v3.py`.
- Resultado: la solución elegida es la regla «menos puntos top» en tres capas (detector de huecos, regla, persona). Ningún modelo ni ensamble la supera en AUC; nadie cumple O2.
- Estado de trabajo y decisiones: `docs/ep3/ESTADO.md`. Informe: `docs/ep3/informe_tecnico_EP3.md` (generado por `scripts/ep3/generar_docs_ep3.py`).
- Pruebas de EP3: solo `python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider` (57). `pytest` sin ruta sigue vetado (reescribe README, informe y parquets de EP2).
- La validación con segmentos nuevos está preparada y sellada (`notebooks/00b…`, `scripts/ep3/evaluar_sellado.py`) y NO se ha ejecutado.

## EP3: fases 12 a 15 (estado al 2026-11-14)
- Nomenclatura: desviaciones del plan = DEV-n (antes D-1 y D-2 en la sección de arriba), decisiones = DEC-n (`docs/ep3/ESTADO.md`).
- Pruebas de EP3: 59 (no 57); mismo comando, sigue vetado `pytest` sin ruta. Ejecutar con `.venv\Scripts\python` (el `python` del PATH puede no ser el del entorno).
- Análisis en muestra (post hoc): `scripts/ep3/f12_analisis_muestra.py`; no supervisado descriptivo: `scripts/ep3/f13_no_supervisado.py` (+ `verificar_no_supervisado.py`, manifest propio).
- Entrega: `artefactos_ep3/` (versionable, solo agregados) y `entrega_EP3.zip` (`scripts/ep3/empaquetar_entrega_ep3.py`); verificada en copia limpia (`docs/ep3/verificacion_copia_limpia.md`).
- Todo texto con el 29,6 %, 44,6 %, 6.059 o horas del brazo C debe llevar el rótulo «en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos».

## EP3: tarea de cierre (estado al 2026-11-14)
- El número de pruebas de EP3 ya no se escribe a mano: `scripts/ep3/contar_pruebas.py` lo recolecta (`pytest --collect-only`, sin ejecutar) en `data/08_reporting_ep3/pruebas_ep3_conteo.json`; las cifras de 57 y 59 de las secciones de arriba son anteriores y quedan reemplazadas por ese archivo.
- La página escucha solo en `localhost` (`.streamlit/config.toml`, `arrancar_app.bat`; el compose publica `127.0.0.1:8501:8501`); la vigila `tests/ep3/test_seguridad_pagina.py`. No exponerla sin autenticación ni sin quitar identificadores.
- El ARI bajo de la fase 13 no es un error (`scripts/ep3/f13b_diagnostico_ari.py`, `f13_ari_diagnostico.*`). Hechos del brazo C: `scripts/ep3/f12b_hechos_brazoC.py`. Pendientes de la página: `docs/ep3/PENDIENTES_PAGINA.md` (no se modificó `app/`). Orientación: `docs/ep3/MAPA_DE_ARCHIVOS.md`.
- Documentos generados: `generar_docs_ep3.py`, `generar_pendientes_pagina.py`, `generar_mapa.py`, `actualizar_revision.py`; no editarlos a mano.
