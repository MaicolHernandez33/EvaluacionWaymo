# Mapa de archivos de EP3

*Generado por `scripts/ep3/generar_mapa.py`: la lista sale del sistema de archivos real (no se escribe a mano); solo las descripciones están en el script. Los tiempos son aproximados y solo se dan cuando se midieron.*

## Si llegas nuevo: orden de lectura (5 pasos)
1. **`docs/ep3/ESTADO.md`**: qué se hizo, qué decisiones se tomaron (DEC-n) y qué falta. Después `CLAUDE.md` (reglas).
2. **`docs/ep3/README_EP3.md`**: una página con los resultados clave y cómo reproducir.
3. **`docs/ep3/informe_tecnico_EP3.md`**: el informe completo; empieza por la capa ejecutiva (sección 0) y el mapa de la pauta (sección 1).
4. **Los notebooks `11` a `15`** (ya ejecutados) en ese orden: datos y detector, IE9/IE10, IE11/IE12, dos pasos y página, no supervisado.
5. **La página** (`scripts\ep3\arrancar_app.bat`) y, si se va a presentar, `docs/ep3/guion_presentacion.md` y `docs/ep3/preguntas_cruzadas.md`.

Verificaciones rápidas (segundos): `.venv\Scripts\python scripts\verificar_congelados.py` (EP2, 14 de 14), `.venv\Scripts\python scripts\ep3\verificar_congelados_v3.py` (5 de 5) y `.venv\Scripts\python scripts\ep3\verificar_no_supervisado.py` (1 de 1). Pruebas de EP3: 63 recolectadas (`pruebas_ep3_conteo.json`).

## Tabla de archivos
| Ruta | Para qué sirve | Cuándo se usa | ¿Se puede ejecutar? (tiempo aproximado) |
|---|---|---|---|
| `CLAUDE.md` | Reglas y contexto del proyecto para quien trabaje con el asistente (EP2 solo lectura, sin commit, etc.). | Al empezar a trabajar | no (documento) |
| `Dockerfile` | Imagen de la página (python:3.10-slim; sin datos). | Para correr la página en Docker | sí, `docker compose up --build`; NO probado (Docker apagado) |
| `.dockerignore` | Lista blanca: deja `data/`, parquet y joblib fuera de la imagen. | Al construir la imagen | no (configuración) |
| `docker-compose.yml` | Levanta la página, puerto solo en 127.0.0.1, datos montados de solo lectura. | Para correr en Docker | sí; NO probado |
| `requirements_app.txt` | Paquetes mínimos de la página. | Al crear un entorno solo para la página | no (se instala con pip y `-c constraints_ep3.txt`) |
| `requirements_ep3.txt` | Paquetes extra de EP3 (xgboost, lightgbm, streamlit…). | Al crear el entorno completo | no (se instala con pip y `-c constraints_ep3.txt`) |
| `constraints_ep3.txt` | Versiones fijas que no se deben mover. | Siempre que se instale algo | no |
| `.streamlit/config.toml` | Seguridad de la página: escucha solo en localhost, sin telemetría, barra mínima. | Se lee solo al lanzar `streamlit run` desde la raíz | no (configuración vigilada por una prueba) |
| `entrega_EP3.sha256` | Hash del zip (queda fuera del zip: un archivo no puede contener su propio hash). | Para comprobar que el zip no cambió | no (se compara con `Get-FileHash`) |
| `entrega_EP3.zip` | Entrega completa (código, notebooks ejecutados, docs, datos derivados mínimos, `SHA256SUMS`, `LEEME_ENTREGA.md`). (70,5 MB) | Para entregar o verificar en otra carpeta | se genera con `empaquetar_entrega_ep3.py` (~1 min, no medido con precisión) |
| `notebooks/00b_seleccion_segmentos_ep3.ipynb` | Selecciona segmentos NUEVOS en Colab (validación externa sellada). | Cuando se quiera la prueba ciega | solo en Colab con acceso al bucket; NO se ha ejecutado |
| `notebooks/11_ep3_datos_y_deteccion.ipynb` | Datos, EDA, calidad y detector de huecos. | Para ver los datos y el filtro 1 | sí; con `RECALCULAR = False` solo muestra artefactos (segundos) |
| `notebooks/12_ep3_tuning_y_ensambles.ipynb` | IE9 e IE10: optimización de hiperparámetros y ensambles. | Para ver la evidencia de IE9 e IE10 | sí; con `RECALCULAR = False` segundos |
| `notebooks/13_ep3_generalizacion_y_seleccion.ipynb` | IE11 e IE12: generalización, selección, brazos A, B y C. | Para ver la selección del modelo | sí; con `RECALCULAR = False` segundos |
| `notebooks/14_ep3_dos_pasos_y_app.ipynb` | Flujo en dos pasos, página y prueba de humo de las 7 secciones. | Plan B de la demo | se entrega ejecutado; contiene una demostración con `lidar_box` crudo que no se puede repetir sin esos datos |
| `notebooks/15_ep3_no_supervisado.ipynb` | Aprendizaje no supervisado descriptivo (post hoc). | Para ver clusters e IsolationForest | sí; con `RECALCULAR = False` segundos |
| `scripts/ep3/actualizar_revision.py` | Regenera `docs/ep3/revision/` con copias de los archivos pequeños (nada por caja) e `INDICE.md`. | Antes de empaquetar, para revisión externa | sí, ~1 s |
| `scripts/ep3/arrancar_app.bat` | Abre la página en localhost:8501 (Windows). | Para usar la página | sí, doble clic; Ctrl+C para detener |
| `scripts/ep3/arrancar_app.ps1` | Igual que el .bat, en PowerShell. | Idem | sí |
| `scripts/ep3/arrancar_docker.ps1` | Levanta la página con Docker Compose. | Para correr en Docker | sí; NO probado |
| `scripts/ep3/contar_pruebas.py` | Cuenta las pruebas de EP3 con `pytest --collect-only` (sin ejecutarlas). | Antes de generar los documentos | sí, ~22 s (medido) |
| `scripts/ep3/crear_notebook_00b.py` | Crea el notebook 00b. | Solo si se rehace el 00b | sí, segundos (no ejecuta el notebook) |
| `scripts/ep3/crear_notebooks_ep3.py` | Crea los notebooks 11 a 15 (no los ejecuta). | Solo si se rehacen | sí, segundos |
| `scripts/ep3/empaquetar_entrega_ep3.py` | Arma `artefactos_ep3/` y `entrega_EP3.zip` con `SHA256SUMS`. | Al cerrar la entrega | sí, ~1 min |
| `scripts/ep3/evaluar_sellado.py` | Congela y evalúa la validación externa (`congelar`, `evaluar`; una sola vez). | Después de correr el notebook 00b | NO se ha ejecutado; `evaluar` se corre una sola vez |
| `scripts/ep3/f12_analisis_muestra.py` | Fase 12 (post hoc): brazos por fold, C menos A, sensibilidad del detector, equidad, EDA. | Para repetir el análisis en muestra | sí; no medido |
| `scripts/ep3/f12b_hechos_brazoC.py` | Probabilidad exacta de réplicas sin segmentos con hueco (por qué el IC de C menos A llega a 0). | Para citar los hechos del brazo C | sí, ~2 s (medido) |
| `scripts/ep3/f13_no_supervisado.py` | Fase 13 (post hoc): KMeans, GMM, Ward, IsolationForest y artefacto con manifest propio. | Para repetir el no supervisado | sí, ~2,5 min (141 s en `f13_resumen.json`) |
| `scripts/ep3/f13b_diagnostico_ari.py` | Diagnóstico del ARI bajo (mismas filas, covarianzas, convergencia). | Para responder si el ARI era un error | sí, ~20 s (medido); no toca el artefacto |
| `scripts/ep3/f1_datos.py` | F1: arma `dev_41.parquet` (41 segmentos) y los folds. | Solo para reconstruir los datos | NO ejecutar: reescribe `dev_41.parquet`, que está congelado |
| `scripts/ep3/f2_detector.py` | F2: detector de huecos, Lista A y reglas simples. | Para reconstruir el filtro 1 | NO ejecutar: reescribe `detector_params_v3.json` (congelado) |
| `scripts/ep3/f3_analisis.py` | F3: tablas de IE9 desde los checkpoints. | Después de `f3_tuning.py` | sí; no medido (minutos o menos) |
| `scripts/ep3/f3_tuning.py` | F3: búsqueda anidada de hiperparámetros (con checkpoints). | Para repetir IE9 | sí, ~1 h con 6 núcleos; sobrescribe resultados |
| `scripts/ep3/f4_ensambles.py` | F4: ensambles E1 a E4 y candidatos fuera de fold. | Para repetir IE10 | sí, ~5 min; sobrescribe resultados |
| `scripts/ep3/f5_generalizacion.py` | F5: métricas de los 11 candidatos, brazos B y C, estabilidad. | Para repetir IE11 | sí; no medido |
| `scripts/ep3/f5_loso_curva.py` | F5: leave-one-segment-out y curvas de ajuste (`--candidato`). | Para repetir IE11 | sí, ~5 a 8 s por candidato (`f5_loso_resumen_*.json`) |
| `scripts/ep3/f6_final.py` | F6: congela la solución v3 y escribe el manifest. | Solo una vez al elegir | NO ejecutar: reescribe `manifest_v3.json` (congelado) |
| `scripts/ep3/f6_seleccion.py` | F6: tabla de selección y regla de reserva DEV-2. | Para repetir IE12 | sí; no medido |
| `scripts/ep3/f7_preparar_app.py` | F7: arma `data/09_app_ep3` (datos de la página, fuera de fold). | Antes de abrir la página | sí; no medido |
| `scripts/ep3/generar_docs_ep3.py` | Genera informe, README_EP3, guion y preguntas; sincroniza conteos en otros docs. | Después de cambiar cualquier resultado | sí, segundos |
| `scripts/ep3/generar_mapa.py` | Genera este mapa desde el sistema de archivos. | Al agregar o quitar archivos | sí, segundos |
| `scripts/ep3/generar_pendientes_pagina.py` | Genera `PENDIENTES_PAGINA.md` con archivo y línea de cada mejora. | Si cambia `app/app.py` | sí, segundos |
| `scripts/ep3/ingesta_nuevos.py` | Ingesta de segmentos nuevos para la validación externa. | Solo en la validación sellada | NO se ha ejecutado |
| `scripts/ep3/puntuar_segmento.py` | Puntúa un segmento nuevo desde la línea de comandos. | Para usar la solución con datos nuevos | sí (necesita un `lidar_box` y su asociación) |
| `scripts/ep3/verificar_congelados_v3.py` | Comprueba los hashes de la solución v3 (5 de 5). | Al inicio y al final de cada tarea | sí, segundos |
| `scripts/ep3/verificar_no_supervisado.py` | Comprueba el hash del artefacto no supervisado (1 de 1). | Idem | sí, segundos |
| `docs/ep3/ESTADO.md` | Estado de fases, decisiones (DEC-n) y bloqueos. | **Primero**: al retomar el trabajo | no (documento) |
| `docs/ep3/MAPA_DE_ARCHIVOS.md` | Este mapa. | Para orientarse | se regenera con `generar_mapa.py` |
| `docs/ep3/PENDIENTES_PAGINA.md` | Mejoras pendientes de la página, con archivo y línea. | Antes de pulir la página | se regenera con `generar_pendientes_pagina.py` |
| `docs/ep3/README_EP3.md` | Resumen de EP3 (candidato a README raíz). | Para una vista rápida | se regenera con `generar_docs_ep3.py` (~1 s) |
| `docs/ep3/despliegue.md` | Cómo correr la página (local, Docker, guía AWS no ejecutada) y seguridad. | Para desplegar | no (documento) |
| `docs/ep3/freeze_antes.txt` | `pip freeze` antes de instalar (evidencia de que no se movieron versiones). | Auditoría del entorno | no |
| `docs/ep3/freeze_despues.txt` | `pip freeze` después de instalar xgboost y lightgbm. | Idem | no |
| `docs/ep3/freeze_despues_f7.txt` | `pip freeze` después de instalar streamlit. | Idem | no |
| `docs/ep3/guion_presentacion.md` | Guion de 9:15 con cifras de la página. | Para la presentación | se regenera con `generar_docs_ep3.py` (~1 s) |
| `docs/ep3/informe_tecnico_EP3.md` | Informe técnico final (secciones 0 a 18 y anexos A y B). | Para evaluar o estudiar el trabajo | se regenera con `generar_docs_ep3.py` (~1 s) |
| `docs/ep3/plan_integracion_readme.md` | Cómo dejar README_EP3 como README raíz sin romper las pruebas de EP2. | Cuando se integre al README | no (documento) |
| `docs/ep3/plan_v3.json` | Plan v3 en formato máquina. | Lo lee `verificar_congelados_v3.py` | no (congelado) |
| `docs/ep3/plan_v3.md` | Plan v3 congelado antes de abrir segmentos nuevos. | Para saber qué estaba pre-declarado | no (congelado) |
| `docs/ep3/plan_v3.sha256` | Hash del plan v3. | Idem | no (congelado) |
| `docs/ep3/plan_v3_desviaciones.md` | Desviaciones del plan (DEV-1, DEV-2). | Para saber qué se cambió y por qué | no (documento) |
| `docs/ep3/preguntas_cruzadas.md` | Preguntas con respuesta, cifra y fuente. | Para prepararse | se regenera con `generar_docs_ep3.py` (~1 s) |
| `docs/ep3/revision/` | Copias de los archivos pequeños para revisar sin abrir el repo (ignorada por git). (31 archivos) | Para revisión externa | no; se regenera con `empaquetar_entrega_ep3.py` |
| `docs/ep3/verificacion_copia_limpia.md` | Registro de la verificación en copia limpia. | Para ver qué se probó y qué no | no (documento) |
| `app/.streamlit/config.toml` | Configuración de la imagen Docker (no se modifica). | Solo dentro del contenedor | no |
| `app/app.py` | La página (Streamlit, 7 secciones, 3 perfiles, modo presentación). | Para la demo y el uso diario | sí, `scripts\ep3\arrancar_app.bat` |
| `artefactos_ep3/` | Tablas agregadas y manifests versionables (sin filas por caja) + `README_artefactos.md`. (67 archivos) | Para revisar resultados sin los datos | se regenera con `empaquetar_entrega_ep3.py` |
| `data/06_models_ep3/manifest_no_supervisado.json` | Hash del artefacto no supervisado. | Lo lee `verificar_no_supervisado.py` | no |
| `data/06_models_ep3/manifest_v3.json` | Hashes de la solución v3 congelada. | Lo lee `verificar_congelados_v3.py` | no (congelado) |
| `src/waymo_evaluacion/ep3/` | Paquete de EP3 (plan, datos, detector, métricas, modelos, candidatos, inferencia, lógica de la página, sellado). (12 módulos) | Lo importan los scripts, la página y las pruebas | no se ejecuta solo; se prueba con `tests/ep3` |
| `tests/ep3/` | Pruebas de EP3 (detector, inferencia, candidatos, sellado, página, seguridad). (7 módulos) | Antes de entregar | sí, solo con `.venv\Scripts\python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider` (~1 min); `pytest` sin ruta está vetado |
