# ESTADO de EP3

Se actualiza al terminar cada fase. Al retomar: leer `CLAUDE.md` y este archivo. Plan congelado: `plan_v3.md` / `plan_v3.json` (hash en `plan_v3.sha256`; desviaciones en `plan_v3_desviaciones.md`).

## Resumen de fases
| Fase | Estado | Archivos principales | Cifras clave (origen) |
|---|---|---|---|
| F0 Verificación y plan | hecha (2026-11-14) | plan_v3.md, plan_v3.json, plan_v3.sha256, ESTADO.md, src/.../ep3/plan.py | verificar_congelados 14 de 14 |
| F1 Datos de desarrollo | hecha | scripts/ep3/f1_datos.py, data/05_model_input_ep3/dev_41.parquet, conjuntos_variables.json | 41 segmentos (33+8); principal 80.571 filas, 17.102 positivos (21,2 %); test principal 16.062/3.734 y 120°: 17.297/4.378 = tabla del plan de EP2; modelos congelados reproducen pred_test_B con dif. máx. 5,6e-16 (data/08_reporting_ep3/f1_resumen.json, f1_reproduccion_pred_test.csv) |
| F2 Baselines y detector | hecha | scripts/ep3/f2_detector.py, data/06_models_ep3/detector_params_v3.json, data/08_reporting_ep3/lista_A_huecos.csv, f2_baselines_reglas_41.csv | el detector reproduce los 2 pares con hueco de EP2 (911012534050 cámara 5; 257766998801 cámara 3), dif. máx. 1,1e-16 (f2_resumen.json); regla top en los 41: AUC 0,823 (IC 0,725 a 0,900) (f2_baselines_reglas_41.csv) |
| F3 IE9 | hecha (DEV-1: 1 repetición, 30 configuraciones) | f3_tuning.py, f3_analisis.py, modelos.py | optimizar mejora XGB (+0,059, IC 0,034 a 0,085) y LGBM (+0,036, IC 0,012 a 0,060); no mejora LR, RF, HGB (f3_defecto_vs_optimizado.csv) |
| F4 IE10 | hecha | f4_ensambles.py | ningún ensamble aporta; E1 +0,005 (IC -0,007 a +0,020); E2 +0,001 vs regla; E3 y E4 por debajo (f4_ensambles_aporta.csv) |
| F5 IE11 | hecha | f5_generalizacion.py, f5_loso_curva.py | regla: AUC 0,823 (0,725 a 0,900), recall A 0,798, ECE 0,044; AUC mín. fold 0,647 (nadie >= 0,75); LOSO 0,823 (f5_metricas_candidatos.csv, f5_loso_resumen_Regla_top.json) |
| F6 IE12 | hecha | f6_seleccion.py, f6_final.py, verificar_congelados_v3.py, data/06_models_ep3/manifest_v3.json | elegida: regla «menos puntos top» (DEV-2); nadie cumple O2 ni O4; v3 congelado 5 de 5 (f6_seleccion.json, f6_tabla_seleccion.csv) |
| F7 Inferencia y página | hecha | inferencia.py, app_logica.py, congelado.py, app/app.py, f7_preparar_app.py, puntuar_segmento.py | 7 secciones ejecutan sin error con AppTest (notebook 14); <!--n_ep3-->63<!--/n_ep3--> pruebas en tests/ep3 (recolectadas) |
| F8 Despliegue | archivos listos; Docker NO probado | Dockerfile, .dockerignore, docker-compose.yml, requirements_app.txt, arrancar_*, despliegue.md | demonio de Docker apagado |
| F9 Segmentos nuevos (solo preparación) | listo, NO ejecutado | notebooks/00b…, ingesta_nuevos.py, evaluar_sellado.py, sellado.py | 702 candidatos; 40 a evaluar; meta >= 15 útiles |
| F10 Documentos | hecha | informe_tecnico_EP3.md, README_EP3.md, guion_presentacion.md, preguntas_cruzadas.md (39 preguntas), plan_integracion_readme.md; notebooks 11 a 14 ejecutados | generados por generar_docs_ep3.py desde los archivos de origen |
| F11 Cierre | hecha | este archivo | verificar_congelados 14 de 14; verificar_congelados_v3 5 de 5; tests/ep3: <!--n_ep3-->63<!--/n_ep3--> pruebas recolectadas |
| F12 Análisis en muestra (post hoc) | hecha | scripts/ep3/f12_analisis_muestra.py; f12_*.csv; images/ep3/12_eda_*.png | el brazo B cumple AUC mínimo por fold >= 0,75 (0,842; regla); en el fold 1 el brazo C baja la fracción de 0,315 a 0,174; dif. C menos A -0,150 con IC -0,490 a 0,000 (no excluye 0; f12_diferencia_C_menos_A.csv); el detector marca los 2 huecos en 30 de 30 combinaciones, falsas alarmas 0 a 2 (f12_sensibilidad_detector.csv); recall en ciclistas 0,443 (f12_equidad.csv) |
| F13 No supervisado (descriptivo, post hoc) | hecha | scripts/ep3/f13_no_supervisado.py, verificar_no_supervisado.py; data/06_models_ep3/no_supervisado_v3.joblib; notebook 15 | k = 2 por silhouette (0,317); ARI KMeans vs GMM 0,008 (revisado: no es un error, f13_ari_diagnostico.*); los clusters no mejoran la regla (k=2: -0,0015, IC -0,0055 a 0,0023; k=4: -0,0097, IC -0,0150 a -0,0044); IsolationForest: atípicas 68,1 % de sin_camara contra 20,8 % (f13_*.csv) |
| F14 Informe y documentos | hecha | informe_tecnico_EP3.md (secciones 0 a 18 y anexos A y B), README_EP3.md, guion (9:15, con las cifras de la página), preguntas_cruzadas.md, PENDIENTES_PAGINA.md, MAPA_DE_ARCHIVOS.md, notebooks 11 a 15 ejecutados | generados por scripts/ep3/generar_docs_ep3.py y crear_notebooks_ep3.py; app con aviso «en muestra», tipo de caso y selector de referencia (tests/ep3: <!--n_ep3-->63<!--/n_ep3--> pruebas recolectadas) |
| F15 Entrega y versionado | hecha (rearmada en F16) | artefactos_ep3/, scripts/ep3/empaquetar_entrega_ep3.py, entrega_EP3.zip y entrega_EP3.sha256 (tamaño y hash se leen de ahí, no se copian aquí), docs/ep3/verificacion_copia_limpia.md | resultados de la verificación en copia limpia: ver `docs/ep3/verificacion_copia_limpia.md` |
| F16 Cierre y verificación | hecha | f13b_diagnostico_ari.py, f12b_hechos_brazoC.py, contar_pruebas.py, generar_pendientes_pagina.py, generar_mapa.py, actualizar_revision.py, .streamlit/config.toml, tests/ep3/test_seguridad_pagina.py, PENDIENTES_PAGINA.md, MAPA_DE_ARCHIVOS.md | el ARI bajo no es un error (mismas 15.000 filas; GMM convergió); prob. exacta de réplicas sin los 2 segmentos con hueco 12,87 % contra 11,9 % observado (f12b_hechos_brazoC.json); la página con «Todos» y 20 % muestra 70,2 % (dos pasos) y el guion citaba 61,9 % (un paso): corregido; seguridad: solo localhost |

## Decisiones tomadas sin consulta
- DEC-1 (F0): las desviaciones del plan van en `plan_v3_desviaciones.md` (aparte), no dentro de `plan_v3.md`, para que el hash congelado no cambie.
- DEC-2 (F0): no existe el kernel `ep2`; los notebooks nuevos se ejecutan con el kernel `python3` del venv `.venv` (tiene todas las dependencias fijadas).
- DEC-3 (F0): el árbol ya traía una modificación autorizada antes de EP3 final: `tests/test_ajustes_finales.py` (línea 174: `--ignore=tests/ep3` para que el conteo de pruebas de EP2 no cuente `tests/ep3`). Se mantiene tal cual.
- DEC-4 (F0): CPU con 16 hilos lógicos; todo cómputo pesado usa `n_jobs=6`.

- DEC-5 (F3): desviación DEV-1 en `plan_v3_desviaciones.md`: 1 repetición (semilla 42) y 30 configuraciones por la regla de cómputo (RF 45 a 100 s por ajuste).
- DEC-6 (F3): no se instaló MLflow (se evita su cadena de dependencias, que puede mover versiones fijadas); el seguimiento de la búsqueda es por checkpoints y CSV/JSON en `data/08_reporting_ep3/f3_ckpt`.
- DEC-7 (F5): el umbral del punto A (recall 0,80) y del punto B (20 %) y el calibrador Platt se fijan con scores internos (OOF interno por segmento) de las filas de entrenamiento de cada fold externo.
- DEC-8 (F5/P4): brazo C = la Lista A se audita aparte (sus positivos cuentan como hallados, sin costo por caja) y el modelo ordena solo las celdas sanas; el costo se mide en cajas revisadas individualmente sobre el total de cajas; punto de equilibrio = (Fracción80_A - Fracción80_C) x cajas / celdas auditadas.
- DEC-9 (F4): los modelos base de los ensambles usan la configuración optimizada de F3 solo si IE9 dio "mejora" para ese modelo; las vistas de E4 usan un HGB con la regularización fuerte de EP2 (hiperparametros_B.json); meta-modelos: regresión logística C=1.
- DEC-10 (F6): si el modelo elegido es E2, su puntaje es un rango dentro del lote puntuado.

- DEC-11 (F12 y F13): las fases 12 y 13 son análisis en muestra y descriptivos, post hoc, no pre-declarados; no cambian la selección ni el plan v3.
- DEC-12 (F13): silhouette en una muestra de 20.000 cajas, GMM y Ward en 15.000, estabilidad con KMeans `n_init=3` y scaler fijo (costo de cómputo); k elegido por máximo silhouette entre 2 y 6 y se explora k = 4.
- DEC-13 (F13): el artefacto no supervisado (`no_supervisado_v3.joblib`) tiene manifest propio (`manifest_no_supervisado.json`) y verificación propia; no toca `manifest_v3.json` y no se usa para puntuar.
- DEC-14 (F14): el aviso «en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos» y la frase sobre las 2 celdas son visibles en Inicio y en Cola de revisión de la página (no en un tooltip) y rotulan toda mención de 29,6 %, 44,6 %, 6.059, horas y recall del brazo C.
- DEC-15 (F14): el selector «Comparar con modelo de referencia» usa las curvas fuera de fold de XGBoost y E2 ya existentes en `data/07_model_output_ep3/f4_oof.parquet`; no se generaron predicciones nuevas.
- DEC-16 (F15): el zip sigue la política de EP2 (sin `lidar_box` originales); se excluyen `train.parquet` de EP2 y los checkpoints `f4_ckpt` y `f5_ckpt` (regenerables); incluye datos derivados por caja de `data/05` a `09_*_ep3`: solo uso académico del docente.
- DEC-17 (F15): el número de pruebas de EP3 ya no se escribe a mano: `scripts/ep3/contar_pruebas.py` lo recolecta con `pytest --collect-only` (sin ejecutar) en `data/08_reporting_ep3/pruebas_ep3_conteo.json`; hoy son <!--n_ep3-->63<!--/n_ep3--> (EP2: <!--n_ep2-->81<!--/n_ep2-->; total <!--n_total-->144<!--/n_total-->). Los 57 y 59 que se citaron antes eran conteos manuales.
- DEC-18 (sesión): tras reiniciar la sesión, `python` del PATH dejó de ser el del `.venv`; todo se ejecuta con `.venv\Scripts\python` y los notebooks con el `.venv` primero en el PATH (si no, el kernel `python3` toma el Python del sistema, sin `joblib`).

- DEC-19 (F16, tarea 1): el ARI KMeans–GMM de 0,008 (EP2: 0,997) se revisó y **no es un error**: las tres técnicas usan las mismas 15.000 filas en el mismo orden, el ARI recalculado coincide con `f13_resumen.json` y todos los GMM convergieron (`f13_ari_diagnostico.csv`, `scripts/ep3/f13b_diagnostico_ari.py`). Con covarianza `diag` el ARI sube a 0,729 y con `spherical` a 0,884. Causa probable (hipótesis, post hoc): sin variables de oclusión los datos son un continuo y el GMM `full` corta distinto que KMeans. No se regeneró nada dependiente (no había error); el informe explica qué cambió respecto de EP2.
- DEC-20 (F16, tarea 3): hechos del brazo C en informe (IE12, limitaciones, anexo B.5), guion y preguntas. Probabilidad exacta de que una réplica del bootstrap (41 segmentos con reemplazo) no contenga ninguno de los 2 segmentos con hueco: ((41-2)/41)^41 = 12,87 %; observado 11,9 % en 1.000 réplicas (diferencia de 0,9 errores estándar); en esas réplicas C = A, por eso el límite superior del IC de C menos A es 0 (`f12b_hechos_brazoC.json`).
- DEC-21 (F16, tarea 5): el guion usa los números que muestra la página, calculados con `app_logica.py` sobre `data/09_app_ep3`. Discrepancia hallada: con «Todos» y 20 % la página muestra el brazo de dos pasos (C): 70,2 % (IC 62,4 a 78,9), 15.726 cajas y 87,4 h; el 61,9 % que citaba el guion es la captura del brazo de un paso (A) en la tarjeta de Inicio. El guion pasó a 9:15 (45 s de margen).
- DEC-22 (F16, tarea 6): `.streamlit/config.toml` en la raíz (address localhost, headless false, sin telemetría, toolbarMode minimal), `arrancar_app.bat/.ps1` con `--server.address localhost`, el compose ya publicaba `127.0.0.1:8501:8501` y `.dockerignore` sigue excluyendo `data/`; `app/.streamlit/config.toml` (usado solo dentro de la imagen) no se tocó porque `app/` no se modifica en esta tarea. Se verificó con una corrida real que solo escucha en localhost (sin Network URL ni External URL).
- DEC-23 (F16, tarea 7): `docs/ep3/PENDIENTES_PAGINA.md` con archivo y línea de cada ítem; no se tocó `app/`. Hallazgo: en el código el presupuesto por defecto ya es 20 % (`app/app.py:126`); el 68 % visto en pantalla coincide con un valor movido a mano (al 68 % la tarjeta da 96,5 % y el texto 96,6 %, que es la inconsistencia de redondeo).
- DEC-24 (F16, tareas 8 y 9): `generar_mapa.py` (lista tomada del sistema de archivos) y `actualizar_revision.py` (copias pequeñas, nada por caja); el empaquetador ahora incluye `.streamlit/`, `f12b_*` y `pruebas_ep3_conteo.json`. Tamaño y hash del zip ya no se escriben en este archivo (cambian en cada reconstrucción): se leen de `entrega_EP3.sha256`.
- DEC-25 (F16, tarea 10): verificación en un venv nuevo (Python 3.10, `C:/Users/maico/tmp_verificacion_ep3/venv_limpio`) instalado solo con `requirements.txt` + `requirements_ep3.txt` + `constraints_ep3.txt`; mismo equipo, no otra máquina. Resultado en `docs/ep3/verificacion_copia_limpia.md`.
- DEC-26 (F16, tarea 10): la primera pasada en el venv nuevo encontró dos faltantes que el `.venv` de desarrollo ocultaba: (1) `streamlit` y `altair` no estaban en `requirements_ep3.txt` (los usa `tests/ep3/test_app.py` y la página) y (2) `waymo_evaluacion` solo se importaba porque el `.venv` la tiene instalada en modo editable. Correcciones: `streamlit==1.65.0` y `altair==6.2.2` en `requirements_ep3.txt` (no se tocó `requirements.txt`) y `tests/ep3/conftest.py`, que agrega `src` al camino de búsqueda. Se repitió la verificación completa.

## Bloqueos
- Docker: el demonio no responde (Docker Desktop apagado); el build queda "no probado" (no se enciende Docker por iniciativa propia).
- Estabilidad (O4): ningún candidato cumple AUC mínimo por fold >= 0,75 (fold 0 difícil para todos); se resolvió con la regla de reserva DEV-2, no con un bloqueo.

## Notas de F0
- Git (solo lectura): rama `maicolhernandez`; modificado solo `tests/test_ajustes_finales.py`; sin seguimiento: CLAUDE.md, constraints_ep3.txt, requirements_ep3.txt, docs/ep3/, src/waymo_evaluacion/ep3/, tests/ep3/.
- Docker 28.3.0 instalado (build de F8 se podrá probar si el daemon responde).

## Registro de F3 (2026-11-14)
- IE9 (1 repetición, 30 configuraciones): optimizar **mejora** a XGBoost (dif. PR-AUC +0,059, IC 0,034 a 0,085) y LightGBM (+0,036, IC 0,012 a 0,060, tras la extensión); **no mejora** a LR (-0,018), RF (-0,040, IC -0,077 a +0,003) ni HGB (+0,014, IC -0,021 a +0,047). Fuente: data/08_reporting_ep3/f3_defecto_vs_optimizado.csv.
- Bordes de grilla: LightGBM `min_child_samples` quedó en el mínimo (20) en 3 de 5 folds; se extendió una vez (5 y 10) y se repitió (etapa ext). Tras la extensión, `n_estimators` quedó en el máximo (200) en 5 de 5 folds: **no se extendió otra vez** porque el plan permite una sola extensión; queda como limitación (f3_bordes.csv).

## Cierre F11 (2026-11-14)
**Modificado fuera de las carpetas nuevas:** solo `tests/test_ajustes_finales.py` (línea 174, `--ignore=tests/ep3`), autorizado antes de esta tarea. README.md, informe de EP2, notebooks 00 a 10, data de EP2: sin cambios.

**Archivos nuevos (sin seguimiento en git):** `CLAUDE.md`, `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `requirements_app.txt`, `requirements_ep3.txt`, `constraints_ep3.txt`, `app/`, `docs/ep3/`, `images/ep3/`, `scripts/ep3/`, `src/waymo_evaluacion/ep3/`, `tests/ep3/`, `notebooks/00b_seleccion_segmentos_ep3.ipynb`, `notebooks/11_…` a `14_…`. Los datos `data/*_ep3` están ignorados por `.gitignore` (`data/**`).

**Para correr la suite completa en una copia limpia** (no aquí: pytest sin ruta reescribe README, informe y parquets de EP2):
```
git clone <repo> copia ; cd copia
python -m venv .venv ; .venv\Scripts\pip install -r requirements.txt -r requirements_ep3.txt -c constraints_ep3.txt
(copiar data/ desde este equipo; está fuera de git)
python scripts/verificar_congelados.py
python scripts/ep3/verificar_congelados_v3.py
python -m pytest -q          # <!--n_ep2-->81<!--/n_ep2--> de EP2 + <!--n_ep3-->63<!--/n_ep3--> de EP3; si falla test_ajustes_finales por el conteo, ver plan_integracion_readme.md
```
