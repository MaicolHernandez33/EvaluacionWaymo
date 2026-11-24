"""Genera docs/ep3/MAPA_DE_ARCHIVOS.md: una fila por archivo importante de EP3, con la lista tomada del sistema de archivos real.

La lista de archivos NO se escribe a mano: se recorre el disco (notebooks, scripts/ep3, docs/ep3, app, src/.../ep3, tests/ep3, artefactos_ep3, manifests, zip).
Lo unico escrito a mano es la descripcion de cada archivo (DESC). Si aparece un archivo nuevo sin descripcion, el script falla para que no quede fuera del mapa.
Los tiempos son aproximados: solo se dan cuando se midieron o constan en un archivo de resultados; si no, dice «no medido».
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# ruta -> (para que sirve, cuando se usa, se puede ejecutar / tiempo)
DESC: dict[str, tuple[str, str, str]] = {
    # ---- raiz
    "CLAUDE.md": ("Reglas y contexto del proyecto para quien trabaje con el asistente (EP2 solo lectura, sin commit, etc.).", "Al empezar a trabajar", "no (documento)"),
    "Dockerfile": ("Imagen de la página (python:3.10-slim; sin datos).", "Para correr la página en Docker", "sí, `docker compose up --build`; NO probado (Docker apagado)"),
    ".dockerignore": ("Lista blanca: deja `data/`, parquet y joblib fuera de la imagen.", "Al construir la imagen", "no (configuración)"),
    "docker-compose.yml": ("Levanta la página, puerto solo en 127.0.0.1, datos montados de solo lectura.", "Para correr en Docker", "sí; NO probado"),
    "requirements_app.txt": ("Paquetes mínimos de la página.", "Al crear un entorno solo para la página", "no (se instala con pip y `-c constraints_ep3.txt`)"),
    "requirements_ep3.txt": ("Paquetes extra de EP3 (xgboost, lightgbm, streamlit…).", "Al crear el entorno completo", "no (se instala con pip y `-c constraints_ep3.txt`)"),
    "constraints_ep3.txt": ("Versiones fijas que no se deben mover.", "Siempre que se instale algo", "no"),
    ".streamlit/config.toml": ("Seguridad de la página (escucha solo en localhost, sin telemetría, barra mínima) y, desde F24, el tema oscuro nativo (`[theme]` y `[theme.sidebar]`), generado desde los tokens de `app/estilos.py`.", "Se lee solo al lanzar `streamlit run` desde la raíz", "el bloque de tema se regenera con `generar_config_tema.py`; la seguridad la vigila una prueba"),
    "entrega_EP3.zip": ("Entrega completa (código, notebooks ejecutados, docs, datos derivados mínimos, `SHA256SUMS`, `LEEME_ENTREGA.md`).", "Para entregar o verificar en otra carpeta", "se genera con `empaquetar_entrega_ep3.py` (~1 min, no medido con precisión)"),
    "entrega_EP3.sha256": ("Hash del zip (queda fuera del zip: un archivo no puede contener su propio hash).", "Para comprobar que el zip no cambió", "no (se compara con `Get-FileHash`)"),
    # ---- notebooks
    "notebooks/00b_seleccion_segmentos_ep2.ipynb": ("Selección de segmentos de EP2 (original, solo lectura): de ahí sale el pool que reproduce el 00b de EP3.", "Solo como referencia", "no (EP2, solo lectura)"),
    "notebooks/00b_seleccion_segmentos_ep3.ipynb": ("Selecciona segmentos NUEVOS en Colab (validación externa sellada).", "Cuando se quiera la prueba ciega", "solo en Colab con acceso al bucket; NO se ha ejecutado"),
    "notebooks/11_ep3_datos_y_deteccion.ipynb": ("Datos, EDA, calidad y detector de huecos.", "Para ver los datos y el filtro 1", "sí; con `RECALCULAR = False` solo muestra artefactos (segundos)"),
    "notebooks/12_ep3_tuning_y_ensambles.ipynb": ("IE9 e IE10: optimización de hiperparámetros y ensambles.", "Para ver la evidencia de IE9 e IE10", "sí; con `RECALCULAR = False` segundos"),
    "notebooks/13_ep3_generalizacion_y_seleccion.ipynb": ("IE11 e IE12: generalización, selección, brazos A, B y C.", "Para ver la selección del modelo", "sí; con `RECALCULAR = False` segundos"),
    "notebooks/14_ep3_dos_pasos_y_app.ipynb": ("Flujo en dos pasos, página y prueba de humo de las 8 secciones.", "Plan B de la demo", "se entrega ejecutado; contiene una demostración con `lidar_box` crudo que no se puede repetir sin esos datos"),
    "notebooks/15_ep3_no_supervisado.ipynb": ("Aprendizaje no supervisado descriptivo (post hoc).", "Para ver clusters e IsolationForest", "sí; con `RECALCULAR = False` segundos"),
    # ---- scripts
    "scripts/ep3/f1_datos.py": ("F1: arma `dev_41.parquet` (41 segmentos) y los folds.", "Solo para reconstruir los datos", "NO ejecutar: reescribe `dev_41.parquet`, que está congelado"),
    "scripts/ep3/f2_detector.py": ("F2: detector de huecos, Lista A y reglas simples.", "Para reconstruir el filtro 1", "NO ejecutar: reescribe `detector_params_v3.json` (congelado)"),
    "scripts/ep3/f3_tuning.py": ("F3: búsqueda anidada de hiperparámetros (con checkpoints).", "Para repetir IE9", "sí, ~1 h con 6 núcleos; sobrescribe resultados"),
    "scripts/ep3/f3_analisis.py": ("F3: tablas de IE9 desde los checkpoints.", "Después de `f3_tuning.py`", "sí; no medido (minutos o menos)"),
    "scripts/ep3/f4_ensambles.py": ("F4: ensambles E1 a E4 y candidatos fuera de fold.", "Para repetir IE10", "sí, ~5 min; sobrescribe resultados"),
    "scripts/ep3/f5_generalizacion.py": ("F5: métricas de los 11 candidatos, brazos B y C, estabilidad.", "Para repetir IE11", "sí; no medido"),
    "scripts/ep3/f5_loso_curva.py": ("F5: leave-one-segment-out y curvas de ajuste (`--candidato`).", "Para repetir IE11", "sí, ~5 a 8 s por candidato (`f5_loso_resumen_*.json`)"),
    "scripts/ep3/f6_seleccion.py": ("F6: tabla de selección y regla de reserva DEV-2.", "Para repetir IE12", "sí; no medido"),
    "scripts/ep3/f6_final.py": ("F6: congela la solución v3 y escribe el manifest.", "Solo una vez al elegir", "NO ejecutar: reescribe `manifest_v3.json` (congelado)"),
    "scripts/ep3/f7_preparar_app.py": ("F7: arma `data/09_app_ep3` (datos de la página, fuera de fold).", "Antes de abrir la página", "sí; no medido"),
    "scripts/ep3/f12_analisis_muestra.py": ("Fase 12 (post hoc): brazos por fold, C menos A, sensibilidad del detector, equidad, EDA.", "Para repetir el análisis en muestra", "sí; no medido"),
    "scripts/ep3/f12b_hechos_brazoC.py": ("Probabilidad exacta de réplicas sin segmentos con hueco (por qué el IC de C menos A llega a 0).", "Para citar los hechos del brazo C", "sí, ~2 s (medido)"),
    "scripts/ep3/f13_no_supervisado.py": ("Fase 13 (post hoc): KMeans, GMM, Ward, IsolationForest y artefacto con manifest propio.", "Para repetir el no supervisado", "sí, ~2,5 min (141 s en `f13_resumen.json`)"),
    "scripts/ep3/f13b_diagnostico_ari.py": ("Diagnóstico del ARI bajo (mismas filas, covarianzas, convergencia).", "Para responder si el ARI era un error", "sí, ~20 s (medido); no toca el artefacto"),
    "scripts/ep3/verificar_congelados_v3.py": ("Comprueba los hashes de la solución v3 (5 de 5).", "Al inicio y al final de cada tarea", "sí, segundos"),
    "scripts/ep3/verificar_no_supervisado.py": ("Comprueba el hash del artefacto no supervisado (1 de 1).", "Idem", "sí, segundos"),
    "scripts/ep3/puntuar_segmento.py": ("Puntúa un segmento nuevo desde la línea de comandos.", "Para usar la solución con datos nuevos", "sí (necesita un `lidar_box` y su asociación)"),
    "scripts/ep3/ingesta_nuevos.py": ("Ingesta de segmentos nuevos para la validación externa.", "Solo en la validación sellada", "NO se ha ejecutado"),
    "scripts/ep3/evaluar_sellado.py": ("Congela y evalúa la validación externa (`congelar`, `evaluar`; una sola vez).", "Después de correr el notebook 00b", "NO se ha ejecutado; `evaluar` se corre una sola vez"),
    "scripts/ep3/contar_pruebas.py": ("Cuenta las pruebas de EP3 con `pytest --collect-only` (sin ejecutarlas).", "Antes de generar los documentos", "sí, ~22 s (medido)"),
    "scripts/ep3/generar_docs_ep3.py": ("Genera informe, README_EP3, guion y preguntas; sincroniza conteos en otros docs.", "Después de cambiar cualquier resultado", "sí, segundos"),
    "scripts/ep3/generar_pendientes_pagina.py": ("Genera `PENDIENTES_PAGINA.md` con archivo y línea de cada mejora.", "Si cambia `app/app.py`", "sí, segundos"),
    "scripts/ep3/generar_mapa.py": ("Genera este mapa desde el sistema de archivos.", "Al agregar o quitar archivos", "sí, segundos"),
    "scripts/ep3/crear_notebook_00b.py": ("Crea el notebook 00b.", "Solo si se rehace el 00b", "sí, segundos (no ejecuta el notebook)"),
    "scripts/ep3/crear_notebooks_ep3.py": ("Crea los notebooks 11 a 15 (no los ejecuta).", "Solo si se rehacen", "sí, segundos"),
    "scripts/ep3/f12c_eda_puntos_top_sin_huecos.py": ("F18-A3c (post hoc): tasa de sin_camara por tramo de puntos del sensor superior con y sin celdas con hueco.", "Para explicar por qué la tasa sube con más de 100 puntos", "sí, segundos"),
    "scripts/ep3/f13c_auc_cluster_sin_huecos.py": ("F18-A3b (post hoc): AUC de la regla dentro de cada cluster sin las celdas con hueco.", "Para ver si la regla pierde capacidad en cajas cercanas por el hueco", "sí, segundos"),
    "scripts/ep3/f18_verificar_definiciones.py": ("F18-A4: cómo se define el «20 %» en el informe y en la página, y por qué el AUC base de f13 es 0,798.", "Para citar la causa exacta de 70,9 % contra 70,2 %", "sí, segundos"),
    "scripts/ep3/f18_sesgo_seleccion.py": ("F18-A6: motivos de descarte y rendimiento de la selección de segmentos de EP2.", "Para el sesgo de selección del informe", "sí, segundos"),
    "scripts/ep3/plan_seleccion_ep3.py": ("F18-B4: calcula (sin descargar nada) el plan de selección de segmentos nuevos y su sha256; `--verificar` lo comprueba.", "Antes del Colab; el plan se declara una sola vez", "sí, segundos"),
    "scripts/ep3/f18_pagina_numeros_antes.py": ("F18-C: captura las cifras de la página ANTES del rediseño (una sola vez).", "Ya se corrió; no repetir con la página nueva", "no repetir (se niega si el archivo existe)"),
    "scripts/ep3/f18_pagina_comparacion.py": ("F18-C: cifras de la página rediseñada frente a las de antes, y tiempos de carga por sección.", "Después de cambiar la página", "sí, ~30 s"),
    "scripts/ep3/generar_guia_estilo.py": ("F18-C0: genera la guía de estilo desde los tokens de `app/estilos.py`.", "Si cambian los tokens", "sí, segundos"),
    "scripts/ep3/generar_icono_pagina.py": ("F18-C1: dibuja el ícono de la página (`app/assets/icono.png`).", "Si se quiere otro ícono", "sí, segundos"),
    "scripts/ep3/capturar_pagina.py": ("F18-C14: captura cada sección con el Chrome o Edge instalado en modo sin interfaz (no instala nada).", "Con la página corriendo, para las imágenes de `images/ep3/pagina/`", "sí, ~2 min"),
    "docs/ep3/GUIA_VALIDACION_EXTERNA.md": ("Pasos exactos de la validación externa sellada (Colab, comandos, casos y paso opcional con `camera_box`).", "Antes de abrir segmentos nuevos", "no (documento)"),
    "docs/ep3/plan_seleccion_ep3.json": ("Plan de selección de segmentos nuevos: parámetros, cuotas, embudo y orden de candidatos.", "Lo comprueba el notebook 00b; debe commitearse antes del Colab", "no (sellado)"),
    "docs/ep3/plan_seleccion_ep3.sha256": ("Hash del plan de selección.", "Idem", "no (sellado)"),
    "docs/ep3/guia_estilo_pagina.md": ("Guía de estilo de la página: producto, paleta con contraste, tipografía, componentes y redacción.", "Para cambiar o extender la página", "se regenera con `generar_guia_estilo.py`"),
    "docs/ep3/pagina_guia_demo.md": ("Recorrido exacto de la demo (clics y qué decir) y guion del video de 90 s.", "Para la presentación", "se regenera con `generar_docs_ep3.py`"),
    "docs/ep3/REPORTE_F18.md": ("Reporte final de la tarea F18 (correcciones, selección de segmentos nuevos y rediseño).", "Para ver qué cambió en F18", "no (documento)"),
    "app/secciones.py": ("Las 8 secciones de la página (una función por sección) y el encabezado (título y una línea; sin chip de estado desde F26).", "Lo importan los archivos de `app/paginas/`", "no se ejecuta solo"),
    "app/contexto.py": ("F20: carpetas de datos y modelos (se leen del entorno en cada llamada) y el diccionario `ctx` que reciben las secciones.", "Lo importa `app/secciones.py`", "no se ejecuta solo"),
    "app/estilos.py": ("Fuente única de los tokens de la piel oscura (color, tipografía, radios), contraste WCAG, CSS propio y componentes HTML de la página; de aquí salen también los dos `config.toml`.", "Lo importa `app/app.py`", "no se ejecuta solo"),
    "app/assets/icono.png": ("Ícono de la página (propio, sin marcas).", "Lo usa `st.set_page_config`", "no"),
    "images/ep3/pagina": ("Capturas de cada sección de la página (perfil analista; sin modo presentación desde F30); `para_revision/` trae las 17 de F30 y `para_revision_f31_f33/` las 16 de F31 a F33 (Auditoría, Cola y Explica).", "Para la presentación o el informe", "se regeneran con `capturar_pagina.py`"),
    "data/08_reporting_ep3/pagina_numeros_antes.json": ("Cifras que mostraba la página antes del rediseño (referencia de la prueba de regresión).", "Lo lee `tests/ep3/test_pagina_rediseno.py`", "no"),
    "scripts/ep3/generar_reporte_f18.py": ("Genera `REPORTE_F18.md` leyendo las cifras de los archivos de resultados.", "Al cerrar F18", "sí, segundos"),
    "scripts/ep3/f19_congelar_alternativas.py": ("F19-A4b (DEV-4): congela LR3 y XGBoost (entrenados con los 41 segmentos) ANTES de abrir datos nuevos, con su manifest aparte.", "Ya se corrió; se niega a sobrescribir", "no repetir (~4 s; se niega a sobrescribir)"),
    "scripts/ep3/ensayo_validacion_externa.py": ("F19-A3: ensayo general con 4 segmentos de desarrollo y el CLI real (congelar con manifest alternativo, ingesta, evaluar --ensayo).", "Antes de la corrida real, y tras cualquier cambio en la tubería", "sí, ~10 s; no toca manifest, nuevos.parquet ni candado reales"),
    "scripts/ep3/generar_ensayo_md.py": ("Genera `ensayo_validacion_externa.md` desde `ensayo_resultado.json`.", "Después del ensayo", "sí, segundos"),
    "scripts/ep3/copiar_sello_a_artefactos.py": ("F19-A5: verifica y copia a `artefactos_ep3/` los manifests y la lista de segmentos, para commitearlos antes de evaluar.", "Después de `congelar` y antes de `evaluar`", "sí, segundos"),
    "docs/ep3/ensayo_validacion_externa.md": ("Log del ensayo general (con datos de desarrollo: no es un resultado).", "Para ver qué se probó antes de la corrida real", "se regenera con `generar_ensayo_md.py`"),
    "docs/ep3/REPORTE_F19A.md": ("Reporte final de la tarea F19-A (preparar el sello antes del Colab).", "Para ver qué cambió en F19-A", "no (documento)"),
    "data/06_models_ep3/manifest_alternativas.json": ("Hash de las alternativas congeladas LR3 y XGBoost (aparte de `manifest_v3.json`).", "Lo verifican `congelar` y `evaluar`", "no (congelado)"),
    "scripts/ep3/f19_medir_arranque.py": ("F19-B9, F20-P12 y F21-P7: mide el arranque en frío de la página (con y sin lanzador) y el tiempo hasta estar lista cada sección, con un navegador sin interfaz.", "Para comprobar que la página abre rápido", "sí, ~3 min (4 arranques); escribe `pagina_arranque.json` y restaura `capturas_resultado.json`"),
    "scripts/ep3/revisar_documentos.py": ("F19-C1 y C3: revisa tablas Markdown y caracteres de control en los documentos de `docs/ep3` y en las cadenas de los scripts; sale con código 1 si hay problemas.", "Después de regenerar documentos", "sí, segundos"),
    "scripts/ep3/generar_reporte_f19b.py": ("Genera `REPORTE_F19B.md` leyendo los tiempos medidos, las capturas y el conteo de pruebas, y corriendo las tres verificaciones de congelados.", "Al cerrar F19-B", "sí, ~5 s"),
    "docs/ep3/REPORTE_F19B.md": ("Reporte final de la tarea F19-B (pulido de la página y corrección de documentos).", "Para ver qué cambió en F19-B", "no (documento)"),
    "app/paginas": ("F20: una página por archivo (resumen, cola, explica, auditoría, validación, puntuar, ética, ayuda); cada una solo llama a `secciones.ejecutar`. Es lo que registra `st.navigation` (con funciones, `AppTest` no puede cambiar de página).", "Las abre `st.navigation` en `app/app.py`", "no (se abren desde la página)"),
    "app/precarga.py": ("F19-B9: carga y calienta en un hilo los datos y la solución congelada (una vez por proceso, compartido con la página).", "Lo importa `app/app.py` y `app/lanzar.py`", "no (módulo)"),
    "app/lanzar.py": ("F19-B9: lanzador que inicia la precarga y ejecuta `streamlit run app/app.py` en el mismo proceso; lo usan `arrancar_app.bat` y `.ps1`.", "Para abrir la página con la precarga", "sí, `.venv\\Scripts\\python app\\lanzar.py --server.address localhost` (~3 s hasta responder)"),
    "scripts/ep3/generar_reporte_f19a.py": ("Genera `REPORTE_F19A.md` leyendo los resultados del ensayo y de las alternativas.", "Al cerrar F19-A", "sí, segundos"),
    "scripts/ep3/actualizar_revision.py": ("Regenera `docs/ep3/revision/` con copias de los archivos pequeños (nada por caja) e `INDICE.md`.", "Antes de empaquetar, para revisión externa", "sí, ~1 s"),
    "scripts/ep3/empaquetar_entrega_ep3.py": ("Arma `artefactos_ep3/` y `entrega_EP3.zip` con `SHA256SUMS`.", "Al cerrar la entrega", "sí, ~1 min"),
    "scripts/ep3/arrancar_app.bat": ("Abre la página en localhost:8501 (Windows).", "Para usar la página", "sí, doble clic; Ctrl+C para detener"),
    "scripts/ep3/arrancar_app.ps1": ("Igual que el .bat, en PowerShell.", "Idem", "sí"),
    "scripts/ep3/arrancar_docker.ps1": ("Levanta la página con Docker Compose.", "Para correr en Docker", "sí; NO probado"),
    # ---- docs
    "docs/ep3/ESTADO.md": ("Estado de fases, decisiones (DEC-n) y bloqueos.", "**Primero**: al retomar el trabajo", "no (documento)"),
    "docs/ep3/plan_v3.md": ("Plan v3 congelado antes de abrir segmentos nuevos.", "Para saber qué estaba pre-declarado", "no (congelado)"),
    "docs/ep3/plan_v3.json": ("Plan v3 en formato máquina.", "Lo lee `verificar_congelados_v3.py`", "no (congelado)"),
    "docs/ep3/plan_v3.sha256": ("Hash del plan v3.", "Idem", "no (congelado)"),
    "docs/ep3/plan_v3_desviaciones.md": ("Desviaciones del plan (DEV-1, DEV-2).", "Para saber qué se cambió y por qué", "no (documento)"),
    "docs/ep3/informe_tecnico_EP3.md": ("Informe técnico final (secciones 0 a 18 y anexos A y B).", "Para evaluar o estudiar el trabajo", "se regenera con `generar_docs_ep3.py` (~1 s)"),
    "docs/ep3/README_EP3.md": ("Resumen de EP3 (candidato a README raíz).", "Para una vista rápida", "se regenera con `generar_docs_ep3.py` (~1 s)"),
    "docs/ep3/guion_presentacion.md": ("Guion de 9:15 con cifras de la página.", "Para la presentación", "se regenera con `generar_docs_ep3.py` (~1 s)"),
    "docs/ep3/preguntas_cruzadas.md": ("Preguntas con respuesta, cifra y fuente.", "Para prepararse", "se regenera con `generar_docs_ep3.py` (~1 s)"),
    "docs/ep3/despliegue.md": ("Cómo correr la página (local, Docker, guía AWS no ejecutada) y seguridad.", "Para desplegar", "no (documento)"),
    "docs/ep3/plan_integracion_readme.md": ("Cómo dejar README_EP3 como README raíz sin romper las pruebas de EP2.", "Cuando se integre al README", "no (documento)"),
    "docs/ep3/verificacion_copia_limpia.md": ("Registro de la verificación en copia limpia.", "Para ver qué se probó y qué no", "no (documento)"),
    "data/08_reporting_ep3/pagina_arranque_f20.json": ("F20-P12: tiempos de arranque y de cada página (con y sin lanzador), medidos con un navegador sin interfaz.", "Para citar los tiempos de carga", "se regenera con `f19_medir_arranque.py` (varios minutos)"),
    "data/08_reporting_ep3/captura_linea_tiempo_etica_y_limites.json": ("F20-P11: línea de tiempo (cada 0,1 s) de la carga en frío de «Ética y límites», para la causa del render incompleto de la captura.", "Para ver cuándo está completa una página", "`capturar_pagina.py --linea-de-tiempo`"),
    "data/08_reporting_ep3/captura_linea_tiempo_auditoria_de_camaras.json": ("F20-P11: línea de tiempo de la carga en frío de «Auditoría de cámaras» (muestra una página a medias mientras el script se ejecuta).", "Idem", "`capturar_pagina.py --linea-de-tiempo`"),
    "docs/ep3/auditoria_diseno_pagina.md": ("F20-P0 y P11 y F21-P6: auditoría de las capturas contra los patrones de plantilla, causa del render incompleto de «Ética y límites», las dos pasadas de corrección de F20 y las dos de F21 con sus mediciones.", "Para ver qué se corrigió del diseño y por qué", "se regenera con `generar_auditoria_diseno.py`"),
    "data/08_reporting_ep3/pagina_arranque_f21.json": ("F21-P7: tiempos de arranque y de cada página después del pulido final (con y sin lanzador), medidos con un navegador sin interfaz.", "Para citar los tiempos de carga de F21", "se regenera con `f19_medir_arranque.py` (varios minutos)"),
    "data/08_reporting_ep3/pagina_arranque_f21_corrida1.json": ("F21-P7: primera corrida de la medición de tiempos, conservada junto a la repetición (en esa corrida un arranque sin lanzador salió lento).", "Para ver la dispersión de la medición", "se regenera con `f19_medir_arranque.py` (varios minutos); es una copia de una corrida pasada"),
    "docs/ep3/REPORTE_F21.md": ("Reporte final de la tarea F21 (última ronda de pulido de la página y ajustes de documentos).", "Para ver qué cambió en F21", "se regenera con `generar_reporte_f21.py`"),
    "scripts/ep3/generar_reporte_f21.py": ("Genera `REPORTE_F21.md` leyendo las capturas, los tiempos, el conteo de pruebas, el guion y las verificaciones.", "Al cerrar F21", "sí, ~1 min (corre las tres verificaciones)"),
    "docs/ep3/plan_diseno_f23.md": ("F23: plan de diseño escrito antes del código (color, tipografía, esquemas de Resumen, Cola y Auditoría, revisión contra los defaults, paleta de curvas).", "Para entender por qué la página se ve como se ve", "se regenera con `generar_plan_diseno_f23.py`"),
    "scripts/ep3/generar_plan_diseno_f23.py": ("Genera `plan_diseno_f23.md`; lee la validación de la paleta de curvas.", "Si cambia la intención de diseño", "sí, segundos"),
    "docs/ep3/REPORTE_F23.md": ("Reporte final de F23 (rediseño estructural): los seis cambios con su estado, paleta, medición 1366 x 768, pruebas, sello y lo que no quedó bien.", "Para ver qué cambió en F23", "se regenera con `generar_reporte_f23.py`"),
    "scripts/ep3/generar_reporte_f23.py": ("Genera `REPORTE_F23.md` leyendo la paleta, la medición, la suite, el sello y las capturas.", "Al cerrar F23", "sí, segundos"),
    "scripts/ep3/f23_integridad_sello.py": ("F23: calcula sha256 de todo lo sellado y mira `git status`, solo lectura; `--antes` registra y `--comprobar` compara.", "Antes y después de tocar la página", "sí, ~10 s"),
    "scripts/ep3/f23_medir_resumen.py": ("F23: mide el Resumen en una ventana de 1366 x 768 y escribe `f23_fold_resumen.json` y `01_resumen_1366x768.png`.", "Con la página corriendo, para comprobar que el anillo cabe sin desplazarse", "sí, ~30 s"),
    "scripts/ep3/f23_registrar_suite.py": ("F23: corre la suite de EP3 con el comando permitido y escribe `f23_resultado_suite.json`.", "Al cerrar F23", "sí, ~1,5 min"),
    "docs/ep3/f23_paleta_validacion.json": ("F23: salida de `validate_palette.js` (skill dataviz) para la paleta de curvas, antes y después.", "Fuente de los números de la paleta en el reporte", "no (dato registrado)"),
    "docs/ep3/f23_fold_resumen.json": ("F23: medidas del Resumen en 1366 x 768 (anillo, afirmación, panel, desplazamiento).", "Fuente de la comprobación «cabe sin desplazarse»", "se regenera con `f23_medir_resumen.py`"),
    "docs/ep3/f23_resultado_suite.json": ("F23: resultado de la suite de EP3 antes y después.", "Fuente del reporte", "se regenera con `f23_registrar_suite.py`"),
    "docs/ep3/f23_sello_antes.json": ("F23: sha256 de lo sellado antes de tocar la página.", "Para comprobar que el sello no cambió", "no (dato registrado)"),
    "docs/ep3/REPORTE_F24.md": ("Reporte final de F24 (cambio de piel oscura y 18 defectos): qué se hizo por defecto, qué no se pudo y por qué, archivos modificados.", "Para ver qué cambió en F24", "se regenera con `generar_reporte_f24.py`"),
    "scripts/ep3/generar_reporte_f24.py": ("Genera `REPORTE_F24.md` leyendo las mediciones, la paleta, el contraste, las capturas, la suite y el sello.", "Al cerrar F24", "sí, segundos"),
    "scripts/ep3/generar_config_tema.py": ("F24: escribe el bloque `[theme]` de los dos `config.toml` desde `TOKENS` de `app/estilos.py`; `--comprobar` falla si se desfasan.", "Al cambiar un token", "sí, segundos"),
    "scripts/ep3/f24_medir_resumen.py": ("F24: mide la primera pantalla del Resumen en 1366 x 768 y escribe `f24_fold_resumen.json` y una captura.", "Con la página corriendo, para comprobar que el panel termina a 640 px o menos", "sí, ~1 min"),
    "scripts/ep3/f24_auditar_contraste.py": ("F24: mide el contraste real del texto de las 14 vistas (DOM y píxeles) y escribe `f24_contraste.json`.", "Con la página corriendo, para comprobar que ningún texto baja de 4,5:1", "sí, ~3 min"),
    "docs/ep3/f24_paleta_validacion.json": ("F24: salida de `validate_palette.js` (modo oscuro, sobre el panel) para la paleta de curvas del prompt, la adoptada y la rampa del mapa de calor.", "Fuente de los números de la paleta", "no (dato registrado)"),
    "docs/ep3/f24_fold_resumen.json": ("F24: medidas de la primera pantalla del Resumen en 1366 x 768 (indicadores, titular y filas de alerta).", "Fuente de la comprobación del límite de 640 px", "se regenera con `f24_medir_resumen.py`"),
    "docs/ep3/f24_contraste.json": ("F24: contraste medido en el DOM y en los píxeles de cada vista.", "Fuente de la comprobación de 4,5:1", "se regenera con `f24_auditar_contraste.py`"),
    "scripts/ep3/f24_capturar_curvas.py": ("F24: captura la pestaña «Curva de priorización» en la piel oscura, sin referencia y con XGBoost y E2 (clics reales), en `images/ep3/pagina/02b_curvas_*`.", "Con la página corriendo, para ver la paleta de curvas", "sí, ~1 min"),
    "scripts/ep3/f24_registrar_suite.py": ("F24: corre la suite de EP3 con el comando permitido y escribe `f24_resultado_suite.json`.", "Al cerrar F24", "sí, ~1,5 min"),
    "docs/ep3/f24_resultado_suite.json": ("F24: resultado de la suite de EP3 antes y después.", "Fuente del reporte", "se regenera con `f24_registrar_suite.py`"),
    "docs/ep3/REPORTE_F25.md": ("Reporte final de F25 (la página como producto: sin avisos naranjas, un color por concepto, barra lateral y barra de herramientas): qué se hizo por número, qué no se pudo y archivos modificados.", "Para ver el cierre de F25", "se regenera con `generar_reporte_f25.py`"),
    "scripts/ep3/generar_reporte_f25.py": ("Genera `REPORTE_F25.md` leyendo las mediciones de F25 y `git status` (solo lectura).", "Para regenerar el reporte de F25", "sí, segundos"),
    "scripts/ep3/f25_validar_paleta.py": ("F25: valida con `validate_palette.js` el mapa único entidad -> color de los flujos y escribe `f25_paleta_validacion.json`.", "Con la ruta de `validate_palette.js` (skill dataviz), para validar los colores", "sí, segundos"),
    "scripts/ep3/f25_medir_barra.py": ("F25: mide la barra lateral a 1366 x 768 (¿queda a la vista el selector de rol?) y escribe `f25_barra_lateral.json` y una captura.", "Con la página corriendo, para comprobar la barra lateral", "sí, ~1 min"),
    "scripts/ep3/f25_comprobar_herramientas.py": ("F25: comprueba con el ratón real encima que los gráficos ya no muestran la barra de herramientas y las tablas sí; escribe `f25_barra_herramientas.json`.", "Con la página corriendo, para comprobar la barra de herramientas", "sí, ~1 min"),
    "scripts/ep3/f25_buscar_ambar.py": ("F25: busca el ámbar y los colores de sus antiguos fondo y borde en el DOM real de las 8 vistas; escribe `f25_ambar_en_el_dom.json`.", "Con la página corriendo, para comprobar que el ámbar solo está en el punto de ciclistas", "sí, ~2 min"),
    "scripts/ep3/f25_registrar_suite.py": ("F25: corre la suite de EP3 con el comando permitido y escribe `f25_resultado_suite.json`.", "Al cerrar F25", "sí, ~3 min"),
    "docs/ep3/REPORTE_F26.md": ("Reporte final de F26 (marca propia Lente, afirmación y pie, textos según el entorno y ajustes de coherencia): qué se hizo por código (A1…, B1…), qué no se pudo y archivos modificados.", "Para ver el cierre de F26", "se regenera con `generar_reporte_f26.py`"),
    "scripts/ep3/generar_reporte_f26.py": ("Genera `REPORTE_F26.md` leyendo las mediciones de F26 y `git status` (solo lectura).", "Para regenerar el reporte de F26", "sí, segundos"),
    "scripts/ep3/generar_icono.py": ("F26: genera el favicon `app/assets/icono.png` (y una vista a 16 px) con Pillow, desde la misma geometría del símbolo de la marca (`estilos.py`).", "Si cambia el símbolo o los colores de la marca", "sí, segundos"),
    "scripts/ep3/f26_capturas_extra.py": ("F26: recortes de la marca y del pie, título de la pestaña y favicon, y la Cola con «Agrupar por objeto» activado; escribe `f26_marca.json`.", "Con la página corriendo, para ver la marca y el pie", "sí, ~1 min"),
    "scripts/ep3/f26_registrar_suite.py": ("F26: corre la suite de EP3 con el comando permitido y escribe `f26_resultado_suite.json`.", "Al cerrar F26", "sí, ~2 min"),
    "docs/ep3/f26_marca.json": ("F26: medidas de la marca (¿cabe en la barra?), el pie, el título de la pestaña y el favicon.", "Fuente de la comprobación de la marca", "se regenera con `f26_capturas_extra.py`"),
    "docs/ep3/f26_contraste.json": ("F26: contraste medido en el DOM y en los píxeles de cada vista.", "Fuente de la comprobación de 4,5:1", "se regenera con `f24_auditar_contraste.py --salida docs/ep3/f26_contraste.json`"),
    "docs/ep3/f26_resultado_suite.json": ("F26: resultado de la suite de EP3 antes y después.", "Fuente del reporte", "se regenera con `f26_registrar_suite.py`"),
    "docs/ep3/f26_sello_despues.json": ("F26: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f26`"),
    "docs/ep3/REPORTE_F27.md": ("Reporte final de F27 (el Resumen en dos pasos, el menú en el orden del proceso y la vista de las primeras cajas de la cola): qué se hizo por código (E1…), qué no se hizo y archivos modificados.", "Para ver el cierre de F27", "sí, segundos"),
    "scripts/ep3/generar_reporte_f27.py": ("Genera `REPORTE_F27.md` leyendo las mediciones de F27 y `git status` (solo lectura).", "Para regenerar el reporte de F27", "sí, segundos"),
    "scripts/ep3/f27_registrar_suite.py": ("F27: corre la suite de EP3 con el comando permitido y escribe `f27_resultado_suite.json`.", "Al cerrar F27", "sí, ~2 min"),
    "docs/ep3/f27_contraste.json": ("F27: contraste medido en el DOM y en los píxeles de cada vista.", "Fuente de la comprobación de 4,5:1", "se regenera con `f24_auditar_contraste.py --salida docs/ep3/f27_contraste.json`"),
    "docs/ep3/f27_resultado_suite.json": ("F27: resultado de la suite de EP3 antes y después.", "Fuente del reporte", "se regenera con `f27_registrar_suite.py`"),
    "docs/ep3/f27_sello_despues.json": ("F27: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f27`"),
    "docs/ep3/REPORTE_F29.md": ("Reporte final de F29 (Resumen rediseñado para uso diario): qué se hizo por punto del prompt, criterios de aceptación, diferencias con la referencia, qué no se hizo y archivos modificados.", "Para ver el cierre de F29", "sí, segundos"),
    "scripts/ep3/generar_reporte_f29.py": ("Genera `REPORTE_F29.md` leyendo las mediciones de F29 y `git status` (solo lectura).", "Para regenerar el reporte de F29", "sí, segundos"),
    "scripts/ep3/f29_registrar_suite.py": ("F29: corre la suite de EP3 con el comando permitido y escribe `f29_resultado_suite.json`.", "Al cerrar F29", "sí, ~2 min"),
    "scripts/ep3/f29_navegacion.py": ("F29: comprueba en el navegador real que «Auditar» y «Abrir» del Resumen navegan con el contexto elegido; guarda `f29_navegacion.json` y las capturas de los destinos.", "Para comprobar la navegación del Resumen", "sí, ~1 min (con la página corriendo)"),
    "docs/ep3/f29_contraste.json": ("F29: contraste medido en el DOM y en los píxeles de cada vista.", "Fuente de la comprobación de 4,5:1", "se regenera con `f24_auditar_contraste.py --salida docs/ep3/f29_contraste.json`"),
    "docs/ep3/f29_resultado_suite.json": ("F29: resultado de la suite de EP3 antes y después.", "Fuente del reporte", "se regenera con `f29_registrar_suite.py`"),
    "docs/ep3/f29_sello_despues.json": ("F29: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f29`"),
    "scripts/ep3/f30_medir_bloque.py": ("F30: mide el bloque «Alertas de cámara» del Resumen y dónde caen «Cola de revisión» y sus filtros a 1366 x 768 (antes y después) y escribe `f30_altura_bloque.json`.", "Con la página corriendo, para comprobar la primera pantalla del Resumen", "sí, ~30 s"),
    "docs/referencias_diseno": ("Los HTML de referencia que pidió la persona para F30 a F33 (Resumen, Auditoría, Cola y Explica). Solo para mirar: la página no los carga.", "Para ver cómo se quería cada página", "no se regenera"),
    "src/waymo_evaluacion/ep3/escala_sintetica.py": ("Datos sintéticos (300 segmentos) para probar que la Auditoría y la Cola escalan; se generan en memoria o en un directorio temporal.", "Para pruebas de volumen", "no se regenera"),
    "scripts/ep3/f31_f33_capturas.py": ("F31 a F33: las 16 capturas a 1366 px de `images/ep3/pagina/para_revision_f31_f33/` (cada una con el estado que dice su nombre).", "Al cerrar una fase de estas páginas (con la página corriendo)", "sí, ~3 min"),
    "scripts/ep3/f31_f32_prueba_escala.py": ("F31 a F33: mide las páginas con 300 segmentos sintéticos y escribe `f31_f32_escala_sintetica.json`.", "Para comprobar que la página escala", "sí, segundos"),
    "scripts/ep3/f33_cifras_cruzadas.py": ("F31 a F33: comprueba en qué páginas aparece cada cifra compartida (cajas a revisar, 70 y 62 de cada 100, horas, 1.945, 1.565, 21,2 %) y que salen de la misma función.", "Para comprobar que las cifras coinciden entre páginas", "sí, segundos"),
    "docs/ep3/f31_f32_escala_sintetica.json": ("F31 a F33: tiempos de cada página con 300 segmentos sintéticos.", "Fuente del reporte", "se regenera con `f31_f32_prueba_escala.py`"),
    "docs/ep3/f33_cifras_cruzadas.json": ("F31 a F33: dónde aparece cada cifra compartida y su valor según la función de `app_logica.py`.", "Fuente del reporte", "se regenera con `f33_cifras_cruzadas.py`"),
    "docs/ep3/f31_f33_capturas.json": ("F31 a F33: qué se capturó en cada una de las 16 imágenes y su alto.", "Fuente del reporte", "se regenera con `f31_f33_capturas.py`"),
    "docs/ep3/f31_sello_despues.json": ("F31: resultado de comparar el sello con su registro inicial (al terminar la Auditoría).", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f31`"),
    "docs/ep3/f33_sello_despues.json": ("F33: resultado de comparar el sello con su registro inicial (al terminar F31 a F33).", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f33`"),
    "scripts/ep3/f32_comparar_orden_cola.py": ("F32: compara el orden de la Cola antes y después de `preparar_cola` (mismo conjunto y positivos; positivos en las primeras 100 a 5.000 filas) y escribe `f32_orden_cola_antes_despues.json`.", "Para comprobar que el orden nuevo no cambia el conjunto", "sí, segundos"),
    "docs/ep3/f32_orden_cola_antes_despues.json": ("F32: resultado de comparar el orden de la Cola antes y después, con dos pasos y un paso al 20 %.", "Fuente del reporte", "se regenera con `f32_comparar_orden_cola.py`"),
    "docs/ep3/f33_contraste.json": ("F31 a F33: contraste medido en el DOM y en los píxeles de cada vista.", "Fuente de la comprobación de 4,5:1", "se regenera con `f24_auditar_contraste.py --salida docs/ep3/f33_contraste.json`"),
    "docs/ep3/REPORTE_F31_F33.md": ("Reporte final de F31 a F33 (Auditoría, Cola y Explica): por parte, qué cambió, qué no se pudo, desviaciones, decisiones, hallazgos, archivos tocados y conteos de pruebas.", "Para saber qué se hizo y qué decidir", "no se regenera (se escribió a mano con las mediciones)"),
    "app/tablas.py": ("El componente único de tabla (F34): título, «Responde», tabla HTML paginada, conteo de filas y «Descargar CSV»; lo usan Validación y Puntuar.", "Para cualquier tabla nueva de la página", "no se regenera"),
    "src/waymo_evaluacion/ep3/tablas_estandar.py": ("Formato y paginación de la tabla estándar (F34), sin Streamlit: decimales por tipo, signo menos, intervalos en una columna y CSV sin redondear.", "Para probar o cambiar el formato de las tablas", "no se regenera"),
    "src/waymo_evaluacion/ep3/validacion.py": ("Lógica y textos de Validación (F34): titular calculado, conteos O1 a O4, puntos clave, tablas de apoyo con su especificación y la descripción de cada candidato (con su fuente).", "Para cambiar qué dice o muestra Validación", "no se regenera"),
    "src/waymo_evaluacion/ep3/puntuar.py": ("Lógica y textos de Puntuar datos nuevos (F35): validación de archivos con mensajes en español, pasos, tarjetas, tablas del resultado y CSV, todo en memoria.", "Para cambiar qué dice o muestra Puntuar", "no se regenera"),
    "scripts/ep3/f34_exportar_valores.py": ("F34: exporta los valores que mostraba Validación antes del rediseño (`tests/ep3/datos_f34/valores_antes_validacion.json`) para la prueba de regresión de cifras.", "Para regenerar la línea base de la regresión", "sí, segundos"),
    "scripts/ep3/f34_f35_capturas.py": ("F34 y F35: las 16 capturas a 1366 px de `images/ep3/pagina/para_revision_f34_f35/` (Validación y Puntuar; sube archivos de prueba creados en un directorio temporal).", "Al cerrar una fase de estas páginas (con la página corriendo)", "sí, ~3 min"),
    "scripts/ep3/f35_prueba_escala.py": ("F35: tiempos de Puntuar con un parquet sintético de 100.000 cajas y con uno de 2.000; escribe `f35_escala_sintetica.json`.", "Para comprobar que Puntuar escala", "sí, ~30 s"),
    "docs/ep3/f35_escala_sintetica.json": ("F35: tiempos de Puntuar con 100.000 y con 2.000 cajas sintéticas.", "Fuente del reporte", "se regenera con `f35_prueba_escala.py`"),
    "docs/ep3/f34_f35_capturas.json": ("F34 y F35: qué se capturó en cada una de las 16 imágenes y su alto.", "Fuente del reporte", "se regenera con `f34_f35_capturas.py`"),
    "docs/ep3/f35_contraste.json": ("F34 y F35: contraste medido en el DOM y en los píxeles de cada vista.", "Fuente de la comprobación de 4,5:1", "se regenera con `f24_auditar_contraste.py --salida docs/ep3/f35_contraste.json`"),
    "docs/ep3/f34_cifras_cruzadas.json": ("F34: dónde aparece cada cifra compartida entre páginas (AUC, cajas, 21,2 %, peatones y ciclistas, horas, 61,9 %, 44,6 % y 29,6 %) y su valor según la función de `app_logica.py`.", "Fuente del reporte", "se regenera con `f34_cifras_cruzadas.py`"),
    "scripts/ep3/f34_cifras_cruzadas.py": ("F34: comprueba en qué páginas aparece cada cifra compartida y que coinciden.", "Para comprobar que las cifras coinciden entre páginas", "sí, segundos"),
    "docs/ep3/f34_sello_despues.json": ("F34: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f34`"),
    "docs/ep3/f35_sello_despues.json": ("F35: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f35`"),
    "images/ep3/pagina/para_revision_f34_f35": ("Las 16 capturas de Validación y Puntuar, el reporte y `estado_git.txt`.", "Para revisar F34 y F35", "se regenera con `f34_f35_capturas.py`"),
    "docs/ep3/REPORTE_F34_F35.md": ("Reporte final de F34 y F35 (Validación y Puntuar): por parte, qué cambió, qué no se pudo, desviaciones, decisiones, hallazgos, regresión de cifras, investigación del ARI, comprobación de «No se guarda nada», tiempos de escala y archivos tocados.", "Para saber qué se hizo y qué decidir", "no se regenera (se escribió a mano con las mediciones)"),
    "src/waymo_evaluacion/ep3/etica_ayuda.py": ("Textos y lógica de Ética y límites y de Ayuda y glosario (F36): hero, desempeño, límites, tres pasos, grupos y buscador del glosario, y las frases ajustadas.", "Fuente de esas dos páginas", "los textos del glosario y de las preguntas siguen en `app_logica.py`"),
    "scripts/ep3/f36_exportar_textos.py": ("F36: exporta los textos visibles de Ética y Ayuda con AppTest (`--salida`); la línea base está en `tests/ep3/datos_f36/textos_antes.json`.", "Para la prueba de regresión de textos", "no se vuelve a correr salvo para rehacer la línea base"),
    "scripts/ep3/f36_capturas.py": ("F36: las 7 capturas de `images/ep3/pagina/para_revision_f36/`; la del modo publicado levanta una copia de la página con `EP3_ENTORNO=publicado` en otro puerto.", "Para revisar F36", "se regenera con `f36_capturas.py --puerto 8531`"),
    "scripts/ep3/f36_verificar_despliegue.py": ("F36, sección 3: solo lee y reporta qué escribe la página fuera de memoria, qué archivos viajarían en un despliegue y si hay datos derivados de Waymo, rutas o credenciales.", "Fuente de `f36_verificacion_despliegue.json`", "no decide la licencia"),
    "docs/ep3/f36_verificacion_despliegue.json": ("F36: resultado de `f36_verificar_despliegue.py` (escrituras, archivos con tamaños, columnas de las tablas, rutas y credenciales).", "Fuente de la sección 3 del reporte", "se regenera con `f36_verificar_despliegue.py`"),
    "docs/ep3/f36_capturas.json": ("F36: qué se capturó en cada una de las 7 imágenes y su alto.", "Fuente del reporte", "se regenera con `f36_capturas.py`"),
    "docs/ep3/f36_sello_despues.json": ("F36: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f36`"),
    "tests/ep3/datos_f36": ("Línea base de los textos de Ética y Ayuda anteriores a F36 (`textos_antes.json`).", "Para `test_pagina_f36.py`", "no editar a mano"),
    "images/ep3/pagina/para_revision_f36": ("Las 7 capturas de Ética y Ayuda, el reporte y `estado_git.txt`.", "Para revisar F36", "se regenera con `f36_capturas.py`"),
    "docs/ep3/REPORTE_F36.md": ("Reporte final de F36 (Ética y límites, Ayuda y glosario y modo de despliegue): por parte, qué cambió, qué no se pudo, decisiones y evidencia de la sección 3.", "Para revisar F36", "escrito a mano; se copia a `para_revision_f36/`"),
    "scripts/crear_demo_hueco.py": ("F37: fabrica, desde un segmento real, una variante con un hueco de cámara SIMULADO (borra al azar filas de una cámara en la asociación; copia el lidar_box byte a byte).", "Para la demostración en vivo", "el resultado siempre dice SIMULADO en el nombre del archivo y en su LEEME"),
    "scripts/ep3/f37_colab_descargar.py": ("F37: celdas para Google Colab que bajan segmentos reales NUEVOS del split validation (solo lidar_box y asociación) y los empaquetan.", "Paso 1 de F37", "no se puede correr aquí: pide la cuenta de Google que aceptó los términos de Waymo"),
    "scripts/ep3/f37_analizar.py": ("F37: mide segmentos con el código real de la página (`candidatos`) y prueba las fracciones del hueco simulado (`hueco`).", "Pasos 1 y 2 de F37", "solo lee"),
    "scripts/ep3/f37_armar_demo.py": ("F37: arma `datos_demo/` (A, B, C, D) desde los candidatos y escribe `LEEME_DEMO.md` y `MANIFIESTO.json` con cifras medidas.", "Paso 2 de F37", "se niega a sobrescribir carpetas existentes"),
    "scripts/ep3/f37_pruebas_ui.py": ("F37: pruebas de extremo a extremo de Puntuar y del bloque del Resumen con el uploader real y un navegador sin interfaz (tiempos, cambios de estado, errores, capturas).", "Paso 3 de F37", "sirve con el ensayo y con `datos_demo`"),
    "docs/ep3/f37_pruebas_ui_ensayo.json": ("F37: resultado de las pruebas de interfaz con SEGMENTOS DE DESARROLLO como ensayo (no son datos nuevos).", "Fuente del reporte", "se regenera con `f37_pruebas_ui.py`"),
    "docs/ep3/f37_hueco_ensayo.json": ("F37: ensayo de las fracciones del hueco simulado sobre un segmento de desarrollo.", "Fuente del reporte", "se regenera con `f37_analizar.py hueco`"),
    "docs/ep3/f37_candidatos_ensayo.json": ("F37: medidas del ensayo con cuatro segmentos de desarrollo.", "Fuente del reporte", "se regenera con `f37_analizar.py candidatos`"),
    "images/ep3/pagina/para_revision_f37": ("Las 7 capturas de la prueba de interfaz (ensayo con segmentos de desarrollo), el reporte y `estado_git.txt`.", "Para revisar F37", "se regenera con `f37_pruebas_ui.py`"),
    "docs/ep3/REPORTE_F37.md": ("Reporte de F37 (datos de demostración en vivo): reconocimiento, qué se pudo y qué falta, hallazgos de las pruebas de interfaz y el bloque del Resumen.", "Para revisar F37", "escrito a mano; se copia a `para_revision_f37/`"),
    "docs/ep3/f37_sello_despues.json": ("F37: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f37`"),
    "scripts/ep3/readme_f38.py": ("F38: bloques de EP3 del README (portada, mapa de la pauta, 8.1 a 8.3, 12.1, 16, 17 y las notas de corrección); las cifras salen de `artefactos_ep3/` y de las funciones de la página.", "Lo importa `scripts/generar_readme.py`", "no se ejecuta solo"),
    "scripts/ep3/medir_pruebas_ep3.py": ("F38: corre solo `tests/ep3` con cobertura y escribe `data/08_reporting_ep3/pruebas_ep3_resultado.json`, que cita el README.", "Antes de regenerar el README", "tarda unos 5 minutos"),
    "scripts/ep3/f38_capturas_app.py": ("F38: las 4 capturas de la aplicación de `images/app/` (sección 16 del README).", "Con la página corriendo", "se regenera con `f38_capturas_app.py --puerto 8531`"),
    "scripts/ep3/f38_capturas_readme.py": ("F38: renderiza el README a HTML y guarda 3 capturas (parte superior, sección 8.2 y mapa de la pauta).", "Para revisar el README", "se regenera sin la página corriendo"),
    "scripts/ep3/f38_diff_readme.py": ("F38: compara el README anterior con el nuevo por sección y lista las cifras y advertencias de antes frente a las de ahora.", "Para `diff_resumen.txt`", "solo lee"),
    "docs/despliegue.json": ("Estado del despliegue (estado, url, fecha, modo) que lee el generador del README: con la URL vacía el README dice «en preparación».", "Rafa lo edita al desplegar y regenera el README", "no inventar la URL"),
    "docs/ep3/readme_entradas.json": ("Datos que completa el equipo para el README (retroalimentación de EP1 y EP2, caso acordado); un campo vacío omite esa parte.", "Lo lee `scripts/generar_readme.py`", "hoy la retroalimentación está vacía"),
    "images/app": ("Las 4 capturas de la aplicación que usa la sección 16 del README.", "README", "se regenera con `f38_capturas_app.py`"),
    "images/ep3/readme/para_revision_f38": ("El README final, el reporte, el diff, los resultados de las pruebas y las capturas del README renderizado.", "Para revisar F38", "se arma al cerrar F38"),
    "docs/ep3/REPORTE_README.md": ("Reporte de F38 (README final): reconocimiento, qué se hizo por paso, correcciones, desviaciones y pendientes.", "Para revisar F38", "escrito a mano; se copia a `para_revision_f38/`"),
    "scripts/ep3/f39_regresion.py": ("F39: guarda y compara los hash de los CSV de resultados y las cifras de pantalla de los 4 segmentos reales (con y sin archivo 2) y del ejemplo, con la misma función de la página.", "Regresión de F39", "el ZIP lleva la hora de creación: se comparan los CSV de adentro"),
    "scripts/ep3/f39_tiempos.py": ("F39: tiempos de Puntuar en el navegador real (flujo anterior y flujo nuevo), 3 repeticiones por segmento.", "Para el reporte de F39", "con la página corriendo"),
    "scripts/ep3/f39_pruebas_ui.py": ("F39: pruebas de estado del flujo nuevo con los cargadores reales (11 casos) y las 8 capturas de revisión.", "Para el reporte de F39", "con la página corriendo; reemplaza a `f37_pruebas_ui.py`"),
    "docs/ep3/f39_regresion_antes.json": ("F39: resultados de los casos de regresión ANTES de cambiar el flujo.", "Fuente del reporte", "no se regenera"),
    "docs/ep3/f39_regresion_despues.json": ("F39: resultados de los mismos casos DESPUÉS de cambiar el flujo.", "Fuente del reporte", "se regenera con `f39_regresion.py --salida`"),
    "docs/ep3/f39_tiempos_antes.json": ("F39: tiempos del flujo anterior (el puntaje se disparaba al subir el archivo 1).", "Fuente del reporte", "no se regenera"),
    "docs/ep3/f39_tiempos_despues.json": ("F39: tiempos del flujo nuevo (clic en «Puntuar segmento»).", "Fuente del reporte", "se regenera con `f39_tiempos.py --modo despues`"),
    "docs/ep3/f39_pruebas_ui.json": ("F39: resultado de cada prueba de estado en el navegador y qué capturas se hicieron.", "Fuente del reporte", "se regenera con `f39_pruebas_ui.py`"),
    "docs/ep3/f39_sello_despues.json": ("F39: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f39`"),
    "docs/ep3/REPORTE_F39.md": ("Reporte de F39 (Puntuar datos nuevos: flujo con los dos archivos): reconocimiento, cambios, regresión, tiempos y pruebas de estado.", "Para revisar F39", "escrito a mano; se copia a `para_revision_f39/`"),
    "images/ep3/pagina/para_revision_f39": ("Las 8 capturas del flujo nuevo, el reporte, `estado_git.txt` y `resultado_pytest.txt`.", "Para revisar F39", "se regenera con `f39_pruebas_ui.py`"),
    "docs/ep3/f38_sello_despues.json": ("F38: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f38`"),
    "scripts/ep3/armar_para_revision.py": ("F30: arma la carpeta `images/ep3/pagina/para_revision/` con los 17 archivos que se envían a revisión (la vacía antes).", "Al cerrar una fase de la página, para enviar las capturas", "sí, segundos"),
    "scripts/ep3/generar_reporte_f30.py": ("Genera `REPORTE_F30.md` leyendo las mediciones de F30 y `git status` (solo lectura).", "Para regenerar el reporte de F30", "sí, segundos"),
    "scripts/ep3/f30_registrar_suite.py": ("F30: corre la suite de EP3 con el comando permitido y escribe `f30_resultado_suite.json`.", "Al cerrar F30", "sí, ~2 min"),
    "docs/ep3/REPORTE_F30.md": ("Reporte final de F30 (ajustes del Resumen y fin del modo presentación): archivos tocados, decisiones, pruebas, medidas y lo que no se pudo hacer.", "Para ver el cierre de F30", "sí, segundos"),
    "docs/ep3/f30_altura_bloque.json": ("F30: altura del bloque de alertas y posición del título de la cola y de sus filtros a 1366 x 768, antes y después.", "Fuente del reporte", "se regenera con `f30_medir_bloque.py`"),
    "docs/ep3/f30_contraste.json": ("F30: contraste medido en el DOM y en los píxeles de cada vista.", "Fuente de la comprobación de 4,5:1", "se regenera con `f24_auditar_contraste.py --salida docs/ep3/f30_contraste.json`"),
    "docs/ep3/f30_resultado_suite.json": ("F30: resultado de la suite de EP3 antes y después.", "Fuente del reporte", "se regenera con `f30_registrar_suite.py`"),
    "docs/ep3/f30_sello_despues.json": ("F30: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f30`"),
    "docs/ep3/f29_navegacion.json": ("F29: resultado de pulsar «Auditar» y «Abrir» en el navegador real.", "Fuente del reporte", "se regenera con `f29_navegacion.py`"),
    "docs/ep3/f25_paleta_validacion.json": ("F25: salida de `validate_palette.js` (modo oscuro, sobre el panel) para los colores de los flujos, el gris base y las curvas.", "Fuente de los números de la paleta", "se regenera con `f25_validar_paleta.py`"),
    "docs/ep3/f25_barra_lateral.json": ("F25: medidas de la barra lateral a 1366 x 768.", "Fuente de la comprobación del interruptor a la vista", "se regenera con `f25_medir_barra.py`"),
    "docs/ep3/f25_barra_herramientas.json": ("F25: barra de herramientas de Streamlit con el cursor sobre un gráfico y sobre una tabla.", "Fuente de la comprobación de la barra de herramientas", "se regenera con `f25_comprobar_herramientas.py`"),
    "docs/ep3/f25_ambar_en_el_dom.json": ("F25: elementos del DOM de las 8 vistas que usan el ámbar o sus antiguos fondo y borde.", "Fuente de la comprobación del ámbar", "se regenera con `f25_buscar_ambar.py`"),
    "docs/ep3/f25_contraste.json": ("F25: contraste medido en el DOM y en los píxeles de cada vista.", "Fuente de la comprobación de 4,5:1", "se regenera con `f24_auditar_contraste.py --salida docs/ep3/f25_contraste.json`"),
    "docs/ep3/f25_resultado_suite.json": ("F25: resultado de la suite de EP3 antes y después.", "Fuente del reporte", "se regenera con `f25_registrar_suite.py`"),
    "docs/ep3/f25_sello_despues.json": ("F25: resultado de comparar el sello con su registro inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f25`"),
    "docs/ep3/f24_sello_despues.json": ("F24: resultado de comparar el sello con su registro inicial (el mismo de F23).", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar --etiqueta f24`"),
    "docs/ep3/f23_sello_despues.json": ("F23: resultado de comparar el sello con su estado inicial.", "Fuente del reporte", "se regenera con `f23_integridad_sello.py --comprobar`"),
    "docs/ep3/REPORTE_F20.md": ("Reporte final de la tarea F20 (rediseño de la página y cierre de documentos).", "Para ver qué cambió en F20", "se regenera con `generar_reporte_f20.py`"),
    "scripts/ep3/generar_auditoria_diseno.py": ("Genera `auditoria_diseno_pagina.md` (patrones de plantilla, causa del render incompleto, pasadas de corrección).", "Al cambiar la página", "sí, segundos"),
    "scripts/ep3/generar_reporte_f20.py": ("Genera `REPORTE_F20.md` leyendo las capturas, los tiempos, el conteo de pruebas y las verificaciones.", "Al cerrar F20", "sí, ~1 min (corre las tres verificaciones)"),
    "docs/ep3/PENDIENTES_PAGINA.md": ("Mejoras pendientes de la página, con archivo y línea.", "Antes de pulir la página", "se regenera con `generar_pendientes_pagina.py`"),
    "docs/ep3/MAPA_DE_ARCHIVOS.md": ("Este mapa.", "Para orientarse", "se regenera con `generar_mapa.py`"),
    "docs/ep3/freeze_antes.txt": ("`pip freeze` antes de instalar (evidencia de que no se movieron versiones).", "Auditoría del entorno", "no"),
    "docs/ep3/freeze_despues.txt": ("`pip freeze` después de instalar xgboost y lightgbm.", "Idem", "no"),
    "docs/ep3/freeze_despues_f7.txt": ("`pip freeze` después de instalar streamlit.", "Idem", "no"),
    "docs/ep3/revision": ("Copias de los archivos pequeños para revisar sin abrir el repo (ignorada por git).", "Para revisión externa", "no; se regenera con `empaquetar_entrega_ep3.py`"),
    # ---- app y paquete
    "app/app.py": ("El marco de la página «Lente» (Streamlit): navegación agrupada con `st.navigation`, wordmark, rol al pie de la barra lateral y pie único; las secciones están en `secciones.py` (cada una se abre desde un archivo de `app/paginas/`) y los estilos en `estilos.py`.", "Para la demo y el uso diario", "sí, `scripts\\ep3\\arrancar_app.bat`"),
    "app/.streamlit/config.toml": ("Configuración de la imagen Docker; desde F24 lleva el mismo bloque de tema oscuro que el de la raíz (generado desde los tokens).", "Solo dentro del contenedor", "el bloque de tema se regenera con `generar_config_tema.py`"),
    "artefactos_ep3": ("Tablas agregadas y manifests versionables (sin filas por caja) + `README_artefactos.md`.", "Para revisar resultados sin los datos", "se regenera con `empaquetar_entrega_ep3.py`"),
    "data/06_models_ep3/manifest_v3.json": ("Hashes de la solución v3 congelada.", "Lo lee `verificar_congelados_v3.py`", "no (congelado)"),
    "data/06_models_ep3/manifest_no_supervisado.json": ("Hash del artefacto no supervisado.", "Lo lee `verificar_no_supervisado.py`", "no"),
}
GRUPOS = {
    "src/waymo_evaluacion/ep3/": ("Paquete de EP3 (plan, datos, detector, métricas, modelos, candidatos, inferencia, lógica de la página, sellado).", "Lo importan los scripts, la página y las pruebas", "no se ejecuta solo; se prueba con `tests/ep3`"),
    "tests/ep3/": ("Pruebas de EP3 (detector, inferencia, candidatos, sellado, página, seguridad).", "Antes de entregar", "sí, solo con `.venv\\Scripts\\python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider` (~1 min); `pytest` sin ruta está vetado"),
}


def tam(p: Path) -> str:
    n = p.stat().st_size
    return f"{n / 1e6:.1f} MB".replace(".", ",") if n >= 1e6 else f"{max(1, round(n / 1e3))} KB"


def main() -> None:
    reales: list[str] = []
    for patron in ("notebooks/00b_*.ipynb", "notebooks/1[1-5]_*.ipynb", "scripts/ep3/*.py", "scripts/ep3/*.bat", "scripts/ep3/*.ps1", "docs/ep3/*.md", "docs/ep3/*.json", "docs/ep3/*.sha256", "docs/ep3/*.txt",
                   "app/app.py", "app/secciones.py", "app/contexto.py", "app/estilos.py", "app/precarga.py", "app/lanzar.py", "app/assets/icono.png", "app/.streamlit/config.toml", "data/06_models_ep3/manifest*.json", "data/08_reporting_ep3/pagina_numeros_antes.json", "data/08_reporting_ep3/pagina_arranque_f20.json", "data/08_reporting_ep3/pagina_arranque_f21.json", "data/08_reporting_ep3/pagina_arranque_f21_corrida1.json", "data/08_reporting_ep3/captura_linea_tiempo_*.json", "docs/ep3/plan_seleccion*"):
        reales += [p.relative_to(RAIZ).as_posix() for p in sorted(RAIZ.glob(patron))]
    reales += [r for r in ("CLAUDE.md", "Dockerfile", ".dockerignore", "docker-compose.yml", "requirements_app.txt", "requirements_ep3.txt", "constraints_ep3.txt", ".streamlit/config.toml", "entrega_EP3.zip", "entrega_EP3.sha256")
               if (RAIZ / r).exists()]
    reales += [r for r in ("docs/ep3/revision", "artefactos_ep3", "images/ep3/pagina", "app/paginas") if (RAIZ / r).exists()]
    orden = ["CLAUDE", "Dockerfile", ".docker", "docker", "requirements", "constraints", ".streamlit", "entrega", "notebooks", "scripts", "docs", "app", "artefactos", "images", "data"]
    reales = sorted(set(reales), key=lambda r: (next(i for i, k in enumerate(orden) if r.startswith(k)), r))
    sin = [r for r in reales if r not in DESC]
    if sin:
        sys.exit("archivos sin descripcion en DESC (agregarlos a scripts/ep3/generar_mapa.py):\n  " + "\n  ".join(sin))
    faltan = [k for k in DESC if not (RAIZ / k).exists() and k not in ("docs/ep3/revision",)]
    if faltan:
        print("AVISO: descripciones de archivos que no existen (se omiten):", faltan)

    filas = []
    for r in reales:
        p = RAIZ / r
        a, b, c = DESC[r]
        if p.is_dir():
            n = sum(1 for x in p.rglob("*") if x.is_file())
            a = f"{a} ({n} archivos)"
            r = r + "/"
        elif r == "entrega_EP3.zip":
            a = f"{a} ({tam(p)})"
        filas.append(f"| `{r}` | {a} | {b} | {c} |")
    for g, (a, b, c) in GRUPOS.items():
        d = RAIZ / g
        n = len([x for x in d.glob("*.py") if x.name != "__init__.py"])
        filas.append(f"| `{g}` | {a} ({n} módulos) | {b} | {c} |")
    cont = json.loads((RAIZ / "data/08_reporting_ep3/pruebas_ep3_conteo.json").read_text(encoding="utf-8"))
    md = f"""# Mapa de archivos de EP3

*Generado por `scripts/ep3/generar_mapa.py`: la lista sale del sistema de archivos real (no se escribe a mano); solo las descripciones están en el script. Los tiempos son aproximados y solo se dan cuando se midieron.*

## Si llegas nuevo: orden de lectura (5 pasos)
1. **`docs/ep3/ESTADO.md`**: qué se hizo, qué decisiones se tomaron (DEC-n) y qué falta. Después `CLAUDE.md` (reglas).
2. **`docs/ep3/README_EP3.md`**: una página con los resultados clave y cómo reproducir.
3. **`docs/ep3/informe_tecnico_EP3.md`**: el informe completo; empieza por la capa ejecutiva (sección 0) y el mapa de la pauta (sección 1).
4. **Los notebooks `11` a `15`** (ya ejecutados) en ese orden: datos y detector, IE9/IE10, IE11/IE12, dos pasos y página, no supervisado.
5. **La página** (`scripts\\ep3\\arrancar_app.bat`) y, si se va a presentar, `docs/ep3/guion_presentacion.md` y `docs/ep3/preguntas_cruzadas.md`.

Verificaciones rápidas (segundos): `.venv\\Scripts\\python scripts\\verificar_congelados.py` (EP2, 14 de 14), `.venv\\Scripts\\python scripts\\ep3\\verificar_congelados_v3.py` (5 de 5) y `.venv\\Scripts\\python scripts\\ep3\\verificar_no_supervisado.py` (1 de 1). Pruebas de EP3: {cont['recolectadas_ep3']} recolectadas (`pruebas_ep3_conteo.json`).

## Tabla de archivos
| Ruta | Para qué sirve | Cuándo se usa | ¿Se puede ejecutar? (tiempo aproximado) |
|---|---|---|---|
{chr(10).join(filas)}
"""
    (RAIZ / "docs/ep3/MAPA_DE_ARCHIVOS.md").write_text(md, encoding="utf-8")
    print(f"{len(filas)} filas escritas en docs/ep3/MAPA_DE_ARCHIVOS.md")


if __name__ == "__main__":
    main()
