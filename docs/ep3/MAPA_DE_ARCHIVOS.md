# Mapa de archivos de EP3

*Generado por `scripts/ep3/generar_mapa.py`: la lista sale del sistema de archivos real (no se escribe a mano); solo las descripciones están en el script. Los tiempos son aproximados y solo se dan cuando se midieron.*

## Si llegas nuevo: orden de lectura (5 pasos)
1. **`docs/ep3/ESTADO.md`**: qué se hizo, qué decisiones se tomaron (DEC-n) y qué falta. Después `CLAUDE.md` (reglas).
2. **`docs/ep3/README_EP3.md`**: una página con los resultados clave y cómo reproducir.
3. **`docs/ep3/informe_tecnico_EP3.md`**: el informe completo; empieza por la capa ejecutiva (sección 0) y el mapa de la pauta (sección 1).
4. **Los notebooks `11` a `15`** (ya ejecutados) en ese orden: datos y detector, IE9/IE10, IE11/IE12, dos pasos y página, no supervisado.
5. **La página** (`scripts\ep3\arrancar_app.bat`) y, si se va a presentar, `docs/ep3/guion_presentacion.md` y `docs/ep3/preguntas_cruzadas.md`.

Verificaciones rápidas (segundos): `.venv\Scripts\python scripts\verificar_congelados.py` (EP2, 14 de 14), `.venv\Scripts\python scripts\ep3\verificar_congelados_v3.py` (5 de 5) y `.venv\Scripts\python scripts\ep3\verificar_no_supervisado.py` (1 de 1). Pruebas de EP3: 415 recolectadas (`pruebas_ep3_conteo.json`).

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
| `.streamlit/config.toml` | Seguridad de la página (escucha solo en localhost, sin telemetría, barra mínima) y, desde F24, el tema oscuro nativo (`[theme]` y `[theme.sidebar]`), generado desde los tokens de `app/estilos.py`. | Se lee solo al lanzar `streamlit run` desde la raíz | el bloque de tema se regenera con `generar_config_tema.py`; la seguridad la vigila una prueba |
| `entrega_EP3.sha256` | Hash del zip (queda fuera del zip: un archivo no puede contener su propio hash). | Para comprobar que el zip no cambió | no (se compara con `Get-FileHash`) |
| `entrega_EP3.zip` | Entrega completa (código, notebooks ejecutados, docs, datos derivados mínimos, `SHA256SUMS`, `LEEME_ENTREGA.md`). (72,0 MB) | Para entregar o verificar en otra carpeta | se genera con `empaquetar_entrega_ep3.py` (~1 min, no medido con precisión) |
| `notebooks/00b_seleccion_segmentos_ep2.ipynb` | Selección de segmentos de EP2 (original, solo lectura): de ahí sale el pool que reproduce el 00b de EP3. | Solo como referencia | no (EP2, solo lectura) |
| `notebooks/00b_seleccion_segmentos_ep3.ipynb` | Selecciona segmentos NUEVOS en Colab (validación externa sellada). | Cuando se quiera la prueba ciega | solo en Colab con acceso al bucket; NO se ha ejecutado |
| `notebooks/11_ep3_datos_y_deteccion.ipynb` | Datos, EDA, calidad y detector de huecos. | Para ver los datos y el filtro 1 | sí; con `RECALCULAR = False` solo muestra artefactos (segundos) |
| `notebooks/12_ep3_tuning_y_ensambles.ipynb` | IE9 e IE10: optimización de hiperparámetros y ensambles. | Para ver la evidencia de IE9 e IE10 | sí; con `RECALCULAR = False` segundos |
| `notebooks/13_ep3_generalizacion_y_seleccion.ipynb` | IE11 e IE12: generalización, selección, brazos A, B y C. | Para ver la selección del modelo | sí; con `RECALCULAR = False` segundos |
| `notebooks/14_ep3_dos_pasos_y_app.ipynb` | Flujo en dos pasos, página y prueba de humo de las 8 secciones. | Plan B de la demo | se entrega ejecutado; contiene una demostración con `lidar_box` crudo que no se puede repetir sin esos datos |
| `notebooks/15_ep3_no_supervisado.ipynb` | Aprendizaje no supervisado descriptivo (post hoc). | Para ver clusters e IsolationForest | sí; con `RECALCULAR = False` segundos |
| `scripts/ep3/armar_para_revision.py` | F30: arma la carpeta `images/ep3/pagina/para_revision/` con los 17 archivos que se envían a revisión (la vacía antes). | Al cerrar una fase de la página, para enviar las capturas | sí, segundos |
| `scripts/ep3/arrancar_app.bat` | Abre la página en localhost:8501 (Windows). | Para usar la página | sí, doble clic; Ctrl+C para detener |
| `scripts/ep3/arrancar_app.ps1` | Igual que el .bat, en PowerShell. | Idem | sí |
| `scripts/ep3/arrancar_docker.ps1` | Levanta la página con Docker Compose. | Para correr en Docker | sí; NO probado |
| `scripts/ep3/capturar_pagina.py` | F18-C14: captura cada sección con el Chrome o Edge instalado en modo sin interfaz (no instala nada). | Con la página corriendo, para las imágenes de `images/ep3/pagina/` | sí, ~2 min |
| `scripts/ep3/contar_pruebas.py` | Cuenta las pruebas de EP3 con `pytest --collect-only` (sin ejecutarlas). | Antes de generar los documentos | sí, ~22 s (medido) |
| `scripts/ep3/copiar_sello_a_artefactos.py` | F19-A5: verifica y copia a `artefactos_ep3/` los manifests y la lista de segmentos, para commitearlos antes de evaluar. | Después de `congelar` y antes de `evaluar` | sí, segundos |
| `scripts/ep3/crear_notebook_00b.py` | Crea el notebook 00b. | Solo si se rehace el 00b | sí, segundos (no ejecuta el notebook) |
| `scripts/ep3/crear_notebooks_ep3.py` | Crea los notebooks 11 a 15 (no los ejecuta). | Solo si se rehacen | sí, segundos |
| `scripts/ep3/empaquetar_despliegue.py` | F43: arma `despliegue_lente.zip` (código, artefactos, configuración, Dockerfile y los datos mínimos que la página abre) para subirlo por scp a EC2; falla si encuentra datos crudos de Waymo, `datos_demo/` o `data/` fuera de la lista. | Despliegue en EC2 | el zip no se versiona (.gitignore) |
| `scripts/ep3/empaquetar_entrega_ep3.py` | Arma `artefactos_ep3/` y `entrega_EP3.zip` con `SHA256SUMS`. | Al cerrar la entrega | sí, ~1 min |
| `scripts/ep3/ensayo_validacion_externa.py` | F19-A3: ensayo general con 4 segmentos de desarrollo y el CLI real (congelar con manifest alternativo, ingesta, evaluar --ensayo). | Antes de la corrida real, y tras cualquier cambio en la tubería | sí, ~10 s; no toca manifest, nuevos.parquet ni candado reales |
| `scripts/ep3/evaluar_sellado.py` | Congela y evalúa la validación externa (`congelar`, `evaluar`; una sola vez). | Después de correr el notebook 00b | NO se ha ejecutado; `evaluar` se corre una sola vez |
| `scripts/ep3/f12_analisis_muestra.py` | Fase 12 (post hoc): brazos por fold, C menos A, sensibilidad del detector, equidad, EDA. | Para repetir el análisis en muestra | sí; no medido |
| `scripts/ep3/f12b_hechos_brazoC.py` | Probabilidad exacta de réplicas sin segmentos con hueco (por qué el IC de C menos A llega a 0). | Para citar los hechos del brazo C | sí, ~2 s (medido) |
| `scripts/ep3/f12c_eda_puntos_top_sin_huecos.py` | F18-A3c (post hoc): tasa de sin_camara por tramo de puntos del sensor superior con y sin celdas con hueco. | Para explicar por qué la tasa sube con más de 100 puntos | sí, segundos |
| `scripts/ep3/f13_no_supervisado.py` | Fase 13 (post hoc): KMeans, GMM, Ward, IsolationForest y artefacto con manifest propio. | Para repetir el no supervisado | sí, ~2,5 min (141 s en `f13_resumen.json`) |
| `scripts/ep3/f13b_diagnostico_ari.py` | Diagnóstico del ARI bajo (mismas filas, covarianzas, convergencia). | Para responder si el ARI era un error | sí, ~20 s (medido); no toca el artefacto |
| `scripts/ep3/f13c_auc_cluster_sin_huecos.py` | F18-A3b (post hoc): AUC de la regla dentro de cada cluster sin las celdas con hueco. | Para ver si la regla pierde capacidad en cajas cercanas por el hueco | sí, segundos |
| `scripts/ep3/f18_pagina_comparacion.py` | F18-C: cifras de la página rediseñada frente a las de antes, y tiempos de carga por sección. | Después de cambiar la página | sí, ~30 s |
| `scripts/ep3/f18_pagina_numeros_antes.py` | F18-C: captura las cifras de la página ANTES del rediseño (una sola vez). | Ya se corrió; no repetir con la página nueva | no repetir (se niega si el archivo existe) |
| `scripts/ep3/f18_sesgo_seleccion.py` | F18-A6: motivos de descarte y rendimiento de la selección de segmentos de EP2. | Para el sesgo de selección del informe | sí, segundos |
| `scripts/ep3/f18_verificar_definiciones.py` | F18-A4: cómo se define el «20 %» en el informe y en la página, y por qué el AUC base de f13 es 0,798. | Para citar la causa exacta de 70,9 % contra 70,2 % | sí, segundos |
| `scripts/ep3/f19_congelar_alternativas.py` | F19-A4b (DEV-4): congela LR3 y XGBoost (entrenados con los 41 segmentos) ANTES de abrir datos nuevos, con su manifest aparte. | Ya se corrió; se niega a sobrescribir | no repetir (~4 s; se niega a sobrescribir) |
| `scripts/ep3/f19_medir_arranque.py` | F19-B9, F20-P12 y F21-P7: mide el arranque en frío de la página (con y sin lanzador) y el tiempo hasta estar lista cada sección, con un navegador sin interfaz. | Para comprobar que la página abre rápido | sí, ~3 min (4 arranques); escribe `pagina_arranque.json` y restaura `capturas_resultado.json` |
| `scripts/ep3/f1_datos.py` | F1: arma `dev_41.parquet` (41 segmentos) y los folds. | Solo para reconstruir los datos | NO ejecutar: reescribe `dev_41.parquet`, que está congelado |
| `scripts/ep3/f23_integridad_sello.py` | F23: calcula sha256 de todo lo sellado y mira `git status`, solo lectura; `--antes` registra y `--comprobar` compara. | Antes y después de tocar la página | sí, ~10 s |
| `scripts/ep3/f23_medir_resumen.py` | F23: mide el Resumen en una ventana de 1366 x 768 y escribe `f23_fold_resumen.json` y `01_resumen_1366x768.png`. | Con la página corriendo, para comprobar que el anillo cabe sin desplazarse | sí, ~30 s |
| `scripts/ep3/f24_auditar_contraste.py` | F24: mide el contraste real del texto de las 14 vistas (DOM y píxeles) y escribe `f24_contraste.json`. | Con la página corriendo, para comprobar que ningún texto baja de 4,5:1 | sí, ~3 min |
| `scripts/ep3/f24_capturar_curvas.py` | F24: captura la pestaña «Curva de priorización» en la piel oscura, sin referencia y con XGBoost y E2 (clics reales), en `images/ep3/pagina/02b_curvas_*`. | Con la página corriendo, para ver la paleta de curvas | sí, ~1 min |
| `scripts/ep3/f24_medir_resumen.py` | F24: mide la primera pantalla del Resumen en 1366 x 768 y escribe `f24_fold_resumen.json` y una captura. | Con la página corriendo, para comprobar que el panel termina a 640 px o menos | sí, ~1 min |
| `scripts/ep3/f25_medir_barra.py` | F25: mide la barra lateral a 1366 x 768 (¿queda a la vista el selector de rol?) y escribe `f25_barra_lateral.json` y una captura. | Con la página corriendo, para comprobar la barra lateral | sí, ~1 min |
| `scripts/ep3/f25_validar_paleta.py` | F25: valida con `validate_palette.js` el mapa único entidad -> color de los flujos y escribe `f25_paleta_validacion.json`. | Con la ruta de `validate_palette.js` (skill dataviz), para validar los colores | sí, segundos |
| `scripts/ep3/f26_capturas_extra.py` | F26: recortes de la marca y del pie, título de la pestaña y favicon, y la Cola con «Agrupar por objeto» activado; escribe `f26_marca.json`. | Con la página corriendo, para ver la marca y el pie | sí, ~1 min |
| `scripts/ep3/f2_detector.py` | F2: detector de huecos, Lista A y reglas simples. | Para reconstruir el filtro 1 | NO ejecutar: reescribe `detector_params_v3.json` (congelado) |
| `scripts/ep3/f30_medir_bloque.py` | F30: mide el bloque «Alertas de cámara» del Resumen y dónde caen «Cola de revisión» y sus filtros a 1366 x 768 (antes y después) y escribe `f30_altura_bloque.json`. | Con la página corriendo, para comprobar la primera pantalla del Resumen | sí, ~30 s |
| `scripts/ep3/f31_f33_capturas.py` | F31 a F33: las 16 capturas a 1366 px de `images/ep3/pagina/para_revision_f31_f33/` (cada una con el estado que dice su nombre). | Al cerrar una fase de estas páginas (con la página corriendo) | sí, ~3 min |
| `scripts/ep3/f37_analizar.py` | F37: mide segmentos con el código real de la página (`candidatos`) y prueba las fracciones del hueco simulado (`hueco`). | Pasos 1 y 2 de F37 | solo lee |
| `scripts/ep3/f37_armar_demo.py` | F37: arma `datos_demo/` (A, B, C, D) desde los candidatos y escribe `LEEME_DEMO.md` y `MANIFIESTO.json` con cifras medidas. | Paso 2 de F37 | se niega a sobrescribir carpetas existentes |
| `scripts/ep3/f37_colab_descargar.py` | F37: celdas para Google Colab que bajan segmentos reales NUEVOS del split validation (solo lidar_box y asociación) y los empaquetan. | Paso 1 de F37 | no se puede correr aquí: pide la cuenta de Google que aceptó los términos de Waymo |
| `scripts/ep3/f37_pruebas_ui.py` | F37: pruebas de extremo a extremo de Puntuar y del bloque del Resumen con el uploader real y un navegador sin interfaz (tiempos, cambios de estado, errores, capturas). | Paso 3 de F37 | sirve con el ensayo y con `datos_demo` |
| `scripts/ep3/f39_pruebas_ui.py` | F39: pruebas de estado del flujo nuevo con los cargadores reales (11 casos) y las 8 capturas de revisión. | Para el reporte de F39 | con la página corriendo; reemplaza a `f37_pruebas_ui.py` |
| `scripts/ep3/f39_regresion.py` | F39: guarda y compara los hash de los CSV de resultados y las cifras de pantalla de los 4 segmentos reales (con y sin archivo 2) y del ejemplo, con la misma función de la página. | Regresión de F39 | el ZIP lleva la hora de creación: se comparan los CSV de adentro |
| `scripts/ep3/f39_tiempos.py` | F39: tiempos de Puntuar en el navegador real (flujo anterior y flujo nuevo), 3 repeticiones por segmento. | Para el reporte de F39 | con la página corriendo |
| `scripts/ep3/f3_analisis.py` | F3: tablas de IE9 desde los checkpoints. | Después de `f3_tuning.py` | sí; no medido (minutos o menos) |
| `scripts/ep3/f3_tuning.py` | F3: búsqueda anidada de hiperparámetros (con checkpoints). | Para repetir IE9 | sí, ~1 h con 6 núcleos; sobrescribe resultados |
| `scripts/ep3/f40_prueba_segmentos_nuevos.py` | F40: puntúa los 4 segmentos nuevos reales de `datos_demo/candidatos/` con las mismas funciones de la página y escribe `docs/ep3/prueba_segmentos_nuevos.json`. | Prueba de funcionamiento del README | necesita `datos_demo/` (no se versiona) |
| `scripts/ep3/f4_ensambles.py` | F4: ensambles E1 a E4 y candidatos fuera de fold. | Para repetir IE10 | sí, ~5 min; sobrescribe resultados |
| `scripts/ep3/f5_generalizacion.py` | F5: métricas de los 11 candidatos, brazos B y C, estabilidad. | Para repetir IE11 | sí; no medido |
| `scripts/ep3/f5_loso_curva.py` | F5: leave-one-segment-out y curvas de ajuste (`--candidato`). | Para repetir IE11 | sí, ~5 a 8 s por candidato (`f5_loso_resumen_*.json`) |
| `scripts/ep3/f6_final.py` | F6: congela la solución v3 y escribe el manifest. | Solo una vez al elegir | NO ejecutar: reescribe `manifest_v3.json` (congelado) |
| `scripts/ep3/f6_seleccion.py` | F6: tabla de selección y regla de reserva DEV-2. | Para repetir IE12 | sí; no medido |
| `scripts/ep3/f7_preparar_app.py` | F7: arma `data/09_app_ep3` (datos de la página, fuera de fold). | Antes de abrir la página | sí; no medido |
| `scripts/ep3/generar_auditoria_diseno.py` | Genera `auditoria_diseno_pagina.md` (patrones de plantilla, causa del render incompleto, pasadas de corrección). | Al cambiar la página | sí, segundos |
| `scripts/ep3/generar_config_tema.py` | F24: escribe el bloque `[theme]` de los dos `config.toml` desde `TOKENS` de `app/estilos.py`; `--comprobar` falla si se desfasan. | Al cambiar un token | sí, segundos |
| `scripts/ep3/generar_docs_ep3.py` | Genera informe, README_EP3, guion y preguntas; sincroniza conteos en otros docs. | Después de cambiar cualquier resultado | sí, segundos |
| `scripts/ep3/generar_ensayo_md.py` | Genera `ensayo_validacion_externa.md` desde `ensayo_resultado.json`. | Después del ensayo | sí, segundos |
| `scripts/ep3/generar_guia_estilo.py` | F18-C0: genera la guía de estilo desde los tokens de `app/estilos.py`. | Si cambian los tokens | sí, segundos |
| `scripts/ep3/generar_icono.py` | F26: genera el favicon `app/assets/icono.png` (y una vista a 16 px) con Pillow, desde la misma geometría del símbolo de la marca (`estilos.py`). | Si cambia el símbolo o los colores de la marca | sí, segundos |
| `scripts/ep3/generar_icono_pagina.py` | F18-C1: dibuja el ícono de la página (`app/assets/icono.png`). | Si se quiere otro ícono | sí, segundos |
| `scripts/ep3/generar_mapa.py` | Genera este mapa desde el sistema de archivos. | Al agregar o quitar archivos | sí, segundos |
| `scripts/ep3/generar_pendientes_pagina.py` | Genera `PENDIENTES_PAGINA.md` con archivo y línea de cada mejora. | Si cambia `app/app.py` | sí, segundos |
| `scripts/ep3/generar_reporte_f18.py` | Genera `REPORTE_F18.md` leyendo las cifras de los archivos de resultados. | Al cerrar F18 | sí, segundos |
| `scripts/ep3/generar_reporte_f19a.py` | Genera `REPORTE_F19A.md` leyendo los resultados del ensayo y de las alternativas. | Al cerrar F19-A | sí, segundos |
| `scripts/ep3/generar_reporte_f19b.py` | Genera `REPORTE_F19B.md` leyendo los tiempos medidos, las capturas y el conteo de pruebas, y corriendo las tres verificaciones de congelados. | Al cerrar F19-B | sí, ~5 s |
| `scripts/ep3/generar_reporte_f20.py` | Genera `REPORTE_F20.md` leyendo las capturas, los tiempos, el conteo de pruebas y las verificaciones. | Al cerrar F20 | sí, ~1 min (corre las tres verificaciones) |
| `scripts/ep3/generar_reporte_f21.py` | Genera `REPORTE_F21.md` leyendo las capturas, los tiempos, el conteo de pruebas, el guion y las verificaciones. | Al cerrar F21 | sí, ~1 min (corre las tres verificaciones) |
| `scripts/ep3/ingesta_nuevos.py` | Ingesta de segmentos nuevos para la validación externa. | Solo en la validación sellada | NO se ha ejecutado |
| `scripts/ep3/medir_pruebas_ep3.py` | F38: corre solo `tests/ep3` con cobertura y escribe `data/08_reporting_ep3/pruebas_ep3_resultado.json`, que cita el README. | Antes de regenerar el README | tarda unos 5 minutos |
| `scripts/ep3/plan_seleccion_ep3.py` | F18-B4: calcula (sin descargar nada) el plan de selección de segmentos nuevos y su sha256; `--verificar` lo comprueba. | Antes del Colab; el plan se declara una sola vez | sí, segundos |
| `scripts/ep3/puntuar_segmento.py` | Puntúa un segmento nuevo desde la línea de comandos. | Para usar la solución con datos nuevos | sí (necesita un `lidar_box` y su asociación) |
| `scripts/ep3/readme_f38.py` | F38: bloques de EP3 del README (portada, mapa de la pauta, 8.1 a 8.3, 12.1, 16, 17 y las notas de corrección); las cifras salen de `artefactos_ep3/` y de las funciones de la página. | Lo importa `scripts/generar_readme.py` | no se ejecuta solo |
| `scripts/ep3/verificar_congelados_v3.py` | Comprueba los hashes de la solución v3 (5 de 5). | Al inicio y al final de cada tarea | sí, segundos |
| `scripts/ep3/verificar_no_supervisado.py` | Comprueba el hash del artefacto no supervisado (1 de 1). | Idem | sí, segundos |
| `docs/ep3/ESTADO.md` | Estado de fases, decisiones (DEC-n) y bloqueos. | **Primero**: al retomar el trabajo | no (documento) |
| `docs/ep3/GUIA_VALIDACION_EXTERNA.md` | Pasos exactos de la validación externa sellada (Colab, comandos, casos y paso opcional con `camera_box`). | Antes de abrir segmentos nuevos | no (documento) |
| `docs/ep3/MAPA_DE_ARCHIVOS.md` | Este mapa. | Para orientarse | se regenera con `generar_mapa.py` |
| `docs/ep3/PENDIENTES_PAGINA.md` | Mejoras pendientes de la página, con archivo y línea. | Antes de pulir la página | se regenera con `generar_pendientes_pagina.py` |
| `docs/ep3/README_EP3.md` | Resumen de EP3 (candidato a README raíz). | Para una vista rápida | se regenera con `generar_docs_ep3.py` (~1 s) |
| `docs/ep3/REPORTE_F24.md` | Reporte final de F24 (cambio de piel oscura y 18 defectos): qué se hizo por defecto, qué no se pudo y por qué, archivos modificados. | Para ver qué cambió en F24 | se regenera con `generar_reporte_f24.py` |
| `docs/ep3/REPORTE_F30.md` | Reporte final de F30 (ajustes del Resumen y fin del modo presentación): archivos tocados, decisiones, pruebas, medidas y lo que no se pudo hacer. | Para ver el cierre de F30 | sí, segundos |
| `docs/ep3/REPORTE_F39.md` | Reporte de F39 (Puntuar datos nuevos: flujo con los dos archivos): reconocimiento, cambios, regresión, tiempos y pruebas de estado. | Para revisar F39 | escrito a mano; se copia a `para_revision_f39/` |
| `docs/ep3/auditoria_diseno_pagina.md` | F20-P0 y P11 y F21-P6: auditoría de las capturas contra los patrones de plantilla, causa del render incompleto de «Ética y límites», las dos pasadas de corrección de F20 y las dos de F21 con sus mediciones. | Para ver qué se corrigió del diseño y por qué | se regenera con `generar_auditoria_diseno.py` |
| `docs/ep3/despliegue.md` | Cómo correr la página (local, Docker, guía AWS no ejecutada) y seguridad. | Para desplegar | no (documento) |
| `docs/ep3/ensayo_validacion_externa.md` | Log del ensayo general (con datos de desarrollo: no es un resultado). | Para ver qué se probó antes de la corrida real | se regenera con `generar_ensayo_md.py` |
| `docs/ep3/f23_fold_resumen.json` | F23: medidas del Resumen en 1366 x 768 (anillo, afirmación, panel, desplazamiento). | Fuente de la comprobación «cabe sin desplazarse» | se regenera con `f23_medir_resumen.py` |
| `docs/ep3/f23_sello_antes.json` | F23: sha256 de lo sellado antes de tocar la página. | Para comprobar que el sello no cambió | no (dato registrado) |
| `docs/ep3/f24_contraste.json` | F24: contraste medido en el DOM y en los píxeles de cada vista. | Fuente de la comprobación de 4,5:1 | se regenera con `f24_auditar_contraste.py` |
| `docs/ep3/f24_fold_resumen.json` | F24: medidas de la primera pantalla del Resumen en 1366 x 768 (indicadores, titular y filas de alerta). | Fuente de la comprobación del límite de 640 px | se regenera con `f24_medir_resumen.py` |
| `docs/ep3/f24_paleta_validacion.json` | F24: salida de `validate_palette.js` (modo oscuro, sobre el panel) para la paleta de curvas del prompt, la adoptada y la rampa del mapa de calor. | Fuente de los números de la paleta | no (dato registrado) |
| `docs/ep3/f24_sello_despues.json` | F24: resultado de comparar el sello con su registro inicial (el mismo de F23). | Fuente del reporte | se regenera con `f23_integridad_sello.py --comprobar --etiqueta f24` |
| `docs/ep3/f25_barra_lateral.json` | F25: medidas de la barra lateral a 1366 x 768. | Fuente de la comprobación del interruptor a la vista | se regenera con `f25_medir_barra.py` |
| `docs/ep3/f25_paleta_validacion.json` | F25: salida de `validate_palette.js` (modo oscuro, sobre el panel) para los colores de los flujos, el gris base y las curvas. | Fuente de los números de la paleta | se regenera con `f25_validar_paleta.py` |
| `docs/ep3/f30_altura_bloque.json` | F30: altura del bloque de alertas y posición del título de la cola y de sus filtros a 1366 x 768, antes y después. | Fuente del reporte | se regenera con `f30_medir_bloque.py` |
| `docs/ep3/f36_verificacion_despliegue.json` | F36: resultado de `f36_verificar_despliegue.py` (escrituras, archivos con tamaños, columnas de las tablas, rutas y credenciales). | Fuente de la sección 3 del reporte | se regenera con `f36_verificar_despliegue.py` |
| `docs/ep3/f39_regresion_antes.json` | F39: resultados de los casos de regresión ANTES de cambiar el flujo. | Fuente del reporte | no se regenera |
| `docs/ep3/guia_estilo_pagina.md` | Guía de estilo de la página: producto, paleta con contraste, tipografía, componentes y redacción. | Para cambiar o extender la página | se regenera con `generar_guia_estilo.py` |
| `docs/ep3/guion_presentacion.md` | Guion de 9:15 con cifras de la página. | Para la presentación | se regenera con `generar_docs_ep3.py` (~1 s) |
| `docs/ep3/informe_tecnico_EP3.md` | Informe técnico final (secciones 0 a 18 y anexos A y B). | Para evaluar o estudiar el trabajo | se regenera con `generar_docs_ep3.py` (~1 s) |
| `docs/ep3/pagina_guia_demo.md` | Recorrido exacto de la demo (clics y qué decir) y guion del video de 90 s. | Para la presentación | se regenera con `generar_docs_ep3.py` |
| `docs/ep3/plan_diseno_f23.md` | F23: plan de diseño escrito antes del código (color, tipografía, esquemas de Resumen, Cola y Auditoría, revisión contra los defaults, paleta de curvas). | Para entender por qué la página se ve como se ve | se regenera con `generar_plan_diseno_f23.py` |
| `docs/ep3/plan_integracion_readme.md` | Cómo dejar README_EP3 como README raíz sin romper las pruebas de EP2. | Cuando se integre al README | no (documento) |
| `docs/ep3/plan_seleccion_ep3.json` | Plan de selección de segmentos nuevos: parámetros, cuotas, embudo y orden de candidatos. | Lo comprueba el notebook 00b; debe commitearse antes del Colab | no (sellado) |
| `docs/ep3/plan_seleccion_ep3.sha256` | Hash del plan de selección. | Idem | no (sellado) |
| `docs/ep3/plan_v3.json` | Plan v3 en formato máquina. | Lo lee `verificar_congelados_v3.py` | no (congelado) |
| `docs/ep3/plan_v3.md` | Plan v3 congelado antes de abrir segmentos nuevos. | Para saber qué estaba pre-declarado | no (congelado) |
| `docs/ep3/plan_v3.sha256` | Hash del plan v3. | Idem | no (congelado) |
| `docs/ep3/plan_v3_desviaciones.md` | Desviaciones del plan (DEV-1, DEV-2). | Para saber qué se cambió y por qué | no (documento) |
| `docs/ep3/preguntas_cruzadas.md` | Preguntas con respuesta, cifra y fuente. | Para prepararse | se regenera con `generar_docs_ep3.py` (~1 s) |
| `docs/ep3/prueba_segmentos_nuevos.json` | F40: resultado de la prueba con 4 segmentos nuevos reales (cajas, celdas marcadas, sha256 de los archivos de entrada). No es una validación estadística. | Fuente de la sección 16 del README | lo genera f40_prueba_segmentos_nuevos.py |
| `docs/ep3/readme_entradas.json` | Datos que completa el equipo para el README (retroalimentación de EP1 y EP2, caso acordado); un campo vacío omite esa parte. | Lo lee `scripts/generar_readme.py` | hoy la retroalimentación está vacía |
| `docs/ep3/revision/` | Copias de los archivos pequeños para revisar sin abrir el repo (ignorada por git). (32 archivos) | Para revisión externa | no; se regenera con `empaquetar_entrega_ep3.py` |
| `docs/ep3/verificacion_copia_limpia.md` | Registro de la verificación en copia limpia. | Para ver qué se probó y qué no | no (documento) |
| `app/.streamlit/config.toml` | Configuración de la imagen Docker; desde F24 lleva el mismo bloque de tema oscuro que el de la raíz (generado desde los tokens). | Solo dentro del contenedor | el bloque de tema se regenera con `generar_config_tema.py` |
| `app/app.py` | El marco de la página «Lente» (Streamlit): navegación agrupada con `st.navigation`, wordmark, rol al pie de la barra lateral y pie único; las secciones están en `secciones.py` (cada una se abre desde un archivo de `app/paginas/`) y los estilos en `estilos.py`. | Para la demo y el uso diario | sí, `scripts\ep3\arrancar_app.bat` |
| `app/assets/icono.png` | Ícono de la página (propio, sin marcas). | Lo usa `st.set_page_config` | no |
| `app/contexto.py` | F20: carpetas de datos y modelos (se leen del entorno en cada llamada) y el diccionario `ctx` que reciben las secciones. | Lo importa `app/secciones.py` | no se ejecuta solo |
| `app/estilos.py` | Fuente única de los tokens de la piel oscura (color, tipografía, radios), contraste WCAG, CSS propio y componentes HTML de la página; de aquí salen también los dos `config.toml`. | Lo importa `app/app.py` | no se ejecuta solo |
| `app/lanzar.py` | F19-B9: lanzador que inicia la precarga y ejecuta `streamlit run app/app.py` en el mismo proceso; lo usan `arrancar_app.bat` y `.ps1`. | Para abrir la página con la precarga | sí, `.venv\Scripts\python app\lanzar.py --server.address localhost` (~3 s hasta responder) |
| `app/paginas/` | F20: una página por archivo (resumen, cola, explica, auditoría, validación, puntuar, ética, ayuda); cada una solo llama a `secciones.ejecutar`. Es lo que registra `st.navigation` (con funciones, `AppTest` no puede cambiar de página). (8 archivos) | Las abre `st.navigation` en `app/app.py` | no (se abren desde la página) |
| `app/precarga.py` | F19-B9: carga y calienta en un hilo los datos y la solución congelada (una vez por proceso, compartido con la página). | Lo importa `app/app.py` y `app/lanzar.py` | no (módulo) |
| `app/secciones.py` | Las 8 secciones de la página (una función por sección) y el encabezado (título y una línea; sin chip de estado desde F26). | Lo importan los archivos de `app/paginas/` | no se ejecuta solo |
| `artefactos_ep3/` | Tablas agregadas y manifests versionables (sin filas por caja) + `README_artefactos.md`. (81 archivos) | Para revisar resultados sin los datos | se regenera con `empaquetar_entrega_ep3.py` |
| `images/ep3/pagina/` | Capturas de cada sección de la página (perfil analista; sin modo presentación desde F30); `para_revision/` trae las 17 de F30 y `para_revision_f31_f33/` las 16 de F31 a F33 (Auditoría, Cola y Explica). (77 archivos) | Para la presentación o el informe | se regeneran con `capturar_pagina.py` |
| `data/06_models_ep3/manifest_alternativas.json` | Hash de las alternativas congeladas LR3 y XGBoost (aparte de `manifest_v3.json`). | Lo verifican `congelar` y `evaluar` | no (congelado) |
| `data/06_models_ep3/manifest_no_supervisado.json` | Hash del artefacto no supervisado. | Lo lee `verificar_no_supervisado.py` | no |
| `data/06_models_ep3/manifest_v3.json` | Hashes de la solución v3 congelada. | Lo lee `verificar_congelados_v3.py` | no (congelado) |
| `data/08_reporting_ep3/captura_linea_tiempo_auditoria_de_camaras.json` | F20-P11: línea de tiempo de la carga en frío de «Auditoría de cámaras» (muestra una página a medias mientras el script se ejecuta). | Idem | `capturar_pagina.py --linea-de-tiempo` |
| `data/08_reporting_ep3/captura_linea_tiempo_etica_y_limites.json` | F20-P11: línea de tiempo (cada 0,1 s) de la carga en frío de «Ética y límites», para la causa del render incompleto de la captura. | Para ver cuándo está completa una página | `capturar_pagina.py --linea-de-tiempo` |
| `data/08_reporting_ep3/pagina_arranque_f20.json` | F20-P12: tiempos de arranque y de cada página (con y sin lanzador), medidos con un navegador sin interfaz. | Para citar los tiempos de carga | se regenera con `f19_medir_arranque.py` (varios minutos) |
| `data/08_reporting_ep3/pagina_arranque_f21.json` | F21-P7: tiempos de arranque y de cada página después del pulido final (con y sin lanzador), medidos con un navegador sin interfaz. | Para citar los tiempos de carga de F21 | se regenera con `f19_medir_arranque.py` (varios minutos) |
| `data/08_reporting_ep3/pagina_arranque_f21_corrida1.json` | F21-P7: primera corrida de la medición de tiempos, conservada junto a la repetición (en esa corrida un arranque sin lanzador salió lento). | Para ver la dispersión de la medición | se regenera con `f19_medir_arranque.py` (varios minutos); es una copia de una corrida pasada |
| `data/08_reporting_ep3/pagina_numeros_antes.json` | Cifras que mostraba la página antes del rediseño (referencia de la prueba de regresión). | Lo lee `tests/ep3/test_pagina_rediseno.py` | no |
| `src/waymo_evaluacion/ep3/` | Paquete de EP3 (plan, datos, detector, métricas, modelos, candidatos, inferencia, lógica de la página, sellado). (21 módulos) | Lo importan los scripts, la página y las pruebas | no se ejecuta solo; se prueba con `tests/ep3` |
| `tests/ep3/` | Pruebas de EP3 (detector, inferencia, candidatos, sellado, página, seguridad). (33 módulos) | Antes de entregar | sí, solo con `.venv\Scripts\python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider` (~1 min); `pytest` sin ruta está vetado |
