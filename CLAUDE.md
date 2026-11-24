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

## EP3: F19-A, sello antes del Colab (estado al 2026-11-15)
- La validación externa se prepara en `docs/ep3/GUIA_VALIDACION_EXTERNA.md`; el ensayo general con datos de desarrollo es `scripts/ep3/ensayo_validacion_externa.py` (no toma candado ni toca lo real). `evaluar_sellado.py` toma el candado solo cuando el cálculo terminó; `--ensayo` exige `--manifest` distinto del real.
- La solución v3 **es** la regla de puntos: «solución contra regla» da 0 por construcción. Las alternativas LR3 y XGBoost están congeladas aparte (`data/06_models_ep3/alternativas_v3.joblib`, `manifest_alternativas.json`; DEV-4). No sobrescribir ni tocar `manifest_v3.json`.
- No se edita `docs/ep3/plan_seleccion_ep3.json` (ni su `.sha256`) ni `src/waymo_evaluacion/ep3/seleccion_nuevos.py`: el notebook 00b embebe su código exacto y una prueba lo comprueba.

## EP3: F24, piel oscura de la página (estado al 2026-11-21)
- Los tokens de color, tipografía y radios viven **solo** en `app/estilos.py` (`TOKENS`). De ahí salen el CSS y el bloque `[theme]` de los dos `config.toml`: tras cambiar un token, correr `.venv\Scripts\python scripts/ep3/generar_config_tema.py` (`--comprobar` verifica). No escribir hex sueltos en `app/secciones.py`.
- Una sola familia sans (Inter opcional: solo si existe `app/static/fonts/Inter-Variable.woff2` con su licencia OFL; hoy no está). Sin CDN ni Google Fonts.
- Mediciones con la página corriendo en localhost: `f24_medir_resumen.py` (panel del Resumen a 1366 x 768, límite 640 px), `f24_auditar_contraste.py` (4,5:1) y `capturar_pagina.py`; reporte en `docs/ep3/REPORTE_F24.md`. El sello se comprueba con `f23_integridad_sello.py --comprobar --etiqueta f24`.

## EP3: F25, la página como producto (estado al 2026-11-21)
- El ámbar de interfaz (`aviso_texto`, `#F5B73B`) es **solo para advertencias reales** (hoy: el punto de «Ciclistas: regla poco confiable» y el del aviso del ciclista). No usarlo para «en muestra», chips ni filetes; los tokens `aviso_fondo`, `aviso_borde` y `aviso_hover` ya no existen. El chip del encabezado es neutro («Datos de desarrollo»; la frase completa va en su menú) y las oraciones conservan «en la muestra» / «(en muestra)»: no quitarlas.
- Un concepto, un color: `E.FLUJOS_COLORES` en `app/estilos.py` es el único mapa entidad -> color de los flujos (barras del Resumen, barras de «En muestra» y curvas). Si cambia un color, validar con `scripts/ep3/f25_validar_paleta.py --validador <ruta a validate_palette.js>` y revisar `f25_paleta_validacion.json`.
- Mediciones con la página corriendo en localhost: `f25_medir_barra.py` (barra lateral a 1366 x 768), `f25_comprobar_herramientas.py` (barra de herramientas de los gráficos), `f25_buscar_ambar.py` (ámbar en el DOM) y `f24_auditar_contraste.py --salida docs/ep3/f25_contraste.json`; reporte en `docs/ep3/REPORTE_F25.md` (generado por `generar_reporte_f25.py`). Sello: `f23_integridad_sello.py --comprobar --etiqueta f25`.


## EP3: F26, marca propia (Lente) y textos según el entorno (estado al 2026-11-22)
- La identidad de la página son **constantes de `src/waymo_evaluacion/ep3/app_logica.py`**: `NOMBRE_PRODUCTO` (`Lente`), `SUBLINEA_MARCA`, `TITULO_RESUMEN`, `SUBTITULO_RESUMEN`, `AFIRMACION_RESUMEN*` y `ATRIBUCION_WAYMO` (**texto provisional**: contrastarlo con waymo.com/open/terms antes de entregar). No repetir esos textos en otros archivos. El nombre antiguo «Auditor de etiquetas 3D» ya no va en `app/` ni en `app_logica.py` (una prueba lo vigila).
- El símbolo es propio (nada del logo ni de los colores de Waymo): su geometría está en `app/estilos.py` (`cunas_simbolo`) y el favicon `app/assets/icono.png` se regenera con `.venv\Scripts\python scripts/ep3/generar_icono.py` (una prueba compara el PNG con lo que genera el script).
- No hay chip de estado: la divulgación de rigor va en las oraciones («en la muestra», «(en muestra)»), en la alerta «Validación externa pendiente» y en el pie. No volver a agregar un chip ni a quitar esas oraciones.
- `EP3_ENTORNO` (`local` por defecto, `servidor`) elige los textos de `TEXTOS_ENTORNO` (Ética «Dónde corre» y «Consideraciones éticas», subtítulo de Puntuar y la pregunta frecuente de los archivos). Los archivos cargados no se escriben a disco; una prueba lo vigila. Si cambia ese comportamiento, cambiar también la variante `servidor`.
- Mediciones nuevas con la página corriendo: `scripts/ep3/f26_capturas_extra.py` (marca, pie y Cola agrupada); reporte en `docs/ep3/REPORTE_F26.md` (`generar_reporte_f26.py`). Pruebas de EP3: las de siempre más `tests/ep3/test_pagina_f26.py`; `tests/ep3/conftest.py` quita `EP3_ENTORNO` al empezar cada prueba y las de la variante `servidor` la fijan por sí mismas.

## EP3: F27, el Resumen en dos pasos y el menú en el orden del proceso (estado al 2026-11-22)
- El proyecto son dos pasos: **1 · Filtro** (celdas con posibles huecos de cámara, que se atienden aparte; página «Auditoría de cámaras») y **2 · Priorización** (la cola ordena el resto; páginas «Cola de revisión» y «Explica una caja»). No hay página «Priorización» aparte: la Cola ya lo es. El menú (`GRUPOS_NAV` en `app_logica.py`) sigue ese orden; los nombres de las 8 secciones y sus URL no cambian.
- Los textos de los pasos son constantes `PASO_*` de `app_logica.py` (no repetirlos en `app/`). El Resumen dibuja cada paso con `E.etapa` (clase `aud-etapa`, **no** `aud-paso`: una prueba de F20 prohíbe esa) y el enlace a su página en `_encabezado_paso`.
- «Primeras cajas de la cola» del Resumen usa `cola_segmento(cajas, "Todos", PRESUPUESTO_VISTA_RESUMEN, "dos")`: debe coincidir con lo que abre «Cola de revisión» por defecto (20 %, dos pasos); una prueba lo compara. Siempre dice el empate (`nota_empate`) y «en muestra».
- Sin flechas en enlaces ni botones (regla de F23). Redacción prudente: «posible hueco», nunca «cámara defectuosa».
- El número de cada captura de `images/ep3/pagina/` sigue el orden de `SECCIONES`: si el menú cambia de orden, borrar las capturas con la numeración anterior (`test_pagina_pulido` cuenta 15 a 1366 px).
- Con seis grupos en el menú, la barra lateral a 1366 x 768 queda justa: tras tocar el menú o su CSS correr `f25_medir_barra.py` (desborde 0 y interruptor a ≤ 760 px en los dos modos). Mediciones y reporte: `docs/ep3/REPORTE_F27.md` (`generar_reporte_f27.py`); suite: `f27_registrar_suite.py --antes 264`; sello: `f23_integridad_sello.py --comprobar --etiqueta f27`.

## EP3: F28, el Resumen sin el aviso «en muestra» (estado al 2026-11-22, a pedido del usuario)
- **Reemplaza** las reglas de F25 y F26 de este archivo que decían «no quitar «en la muestra» / «(en muestra)»» y «la divulgación va en la alerta «Validación externa pendiente» del Resumen»: el usuario pidió quitarlas **del Resumen**. Ya no están allí: la frase del paso 1, «en la muestra de», «de desarrollo» del subtítulo, «en muestra» de la nota de las primeras cajas, «Estimación en muestra», el menú «Fuente» y la alerta de validación pendiente (el Resumen tiene dos alertas: celdas marcadas y ciclistas). No volver a agregarlas sin que el usuario lo pida.
- Siguen diciéndolo, y no se tocaron: el pie, la Cola («(en muestra)» y su nota), Validación, Ética y límites, Ayuda y Puntuar. La regla de texto con 29,6 %, 44,6 %, 6.059 u horas del brazo C (rótulo «en muestra: 41 segmentos, … sin validación con datos nuevos») sigue valiendo para informe, README, guion y notas fuera de la página; el Resumen es la excepción pedida.
- Prueba de que el Resumen está limpio: `tests/ep3/test_pagina_f27.py` (sin `en (la )?muestra` ni «Validación externa pendiente»).

## EP3: F29, Resumen rediseñado para uso diario (estado al 2026-11-22, a pedido del usuario con su referencia visual)
- **Reemplaza** el Resumen de F26 (afirmación, selector de segmento) y de F27 (dos pasos con encabezados): hoy son 4 indicadores, el bloque «Alertas de cámara» (una fila por celda marcada con «Auditar» y el anillo de la fila elegida), la «Cola de revisión» (filtros, tabla con «Abrir» y panel «Segmentos con más cajas prioritarias») y el pie con la divulgación. Los textos y la lógica viven en `app_logica.py` (constantes y `indicadores_resumen`, `cola_prioritaria`, `celdas_marcadas_lista`…); no repetirlos en `app/`. Prueba: `tests/ep3/test_pagina_f29.py`.
- Reglas que siguen en pie: «Sin revisar» = total cargado, decidido SOLO en `segmentos_sin_revisar`; el cambio de ayer se omite mientras `cambio_respecto_de_ayer` devuelva `None` (no inventar cifras); no copiar del mockup horas, «Actualizado hoy» ni «Datos de ejemplo»; «Cifras de apoyo» vive en Validación; «Impacto estimado» solo con el modo presentación; la etiqueta «Regla poco confiable» lleva el punto ámbar sin caja.
- No tocar `cola_segmento` ni el orden de «Cola de revisión» para desempatar: la cola del Resumen solo reordena (probabilidad, segmento, objeto, fotograma) las mismas cajas. Un cambio ahí puede mover cuáles cajas entran en el corte del 20 % y cambiar cifras.
- «Auditar» y «Abrir» pasan el contexto por `session_state` (`_auditoria_celda`, `_explica_caja`) y el cambio de página lo hace `app.py` con `_ir` (`st.switch_page` no es fiable dentro de un callback). Verificarlos en el navegador real con `scripts/ep3/f29_navegacion.py`.
- Streamlit resta 15 px al texto de `st.markdown` dentro de filas de tabla (margen negativo en `stMarkdownContainer`): anularlo en cada contenedor nuevo con filas. La primera pantalla del Resumen se mide con `f24_medir_resumen.py` (la última fila de alerta termina en ≤ 640 px a 1366 x 768, en modo normal y en presentación).
- Mayúsculas pequeñas solo en el rótulo de las alertas y en el encabezado de la tabla de la cola; cifras grandes en peso 600. Los generadores `generar_reporte_f26.py` y `generar_reporte_f27.py` citan constantes que F29 quitó: ya no se pueden regenerar (sus reportes quedan como están).

## EP3: F30, Resumen ajustado y sin Modo presentación (estado al 2026-11-22, a pedido del usuario con `f30_resumen_propuesto.html`)
- **El Modo presentación ya no existe** (interfaz, textos, código, pruebas y capturas). No volver a agregar un interruptor, un parámetro `presentacion`, la numeración de identificadores ni el ocultamiento en descargas; los identificadores y las marcas de tiempo se muestran siempre en las tablas locales y en los CSV. Una prueba (`tests/ep3/test_pagina_f30.py`) busca «modo presentación», «presentacion» y `--escala: 1.18` en `app/`, `src/`, las capturas y los scripts de medición. Los reportes y documentos de fases anteriores lo siguen mencionando porque cuentan su historia: no editarlos.
- **Resumen:** el bloque «Alertas de cámara» son dos columnas (izquierda: rótulo, titular, subtítulo y filas con «Auditar»; derecha: anillo arriba de 240 a 260 px con su rótulo y su leyenda); sin enlace «Abrir la auditoría de cámaras» y sin la línea «Validación externa pendiente» en el pie (DEC-119: la divulgación está en Ética y límites, Validación, Ayuda y el pie global). Meta de la primera pantalla: título de la cola y filtros visibles a 1366 x 768 (`f30_medir_bloque.py`; con 650 px útiles faltan 25 px).
- **«Impacto estimado»** (horas, nota y «Fuente») es una sección fija de Validación › En muestra, debajo del gráfico: no volver a ponerlo en el Resumen.
- Para enviar capturas a revisión: `.venv\Scripts\python scripts/ep3/armar_para_revision.py` (vacía y rearma `images/ep3/pagina/para_revision/` con exactamente 17 archivos: 16 capturas a 1366 px y `REPORTE_F30.md`; correrlo después de regenerar capturas y reporte). Los generadores `generar_reporte_f26.py` a `generar_reporte_f29.py` ya no se pueden regenerar.

## EP3: F31 a F33, Auditoría, Cola y Explica rediseñadas (estado al 2026-11-22, a pedido del usuario con los HTML de `docs/referencias_diseno/`)
- **Reemplaza** de F27: «Explica una caja» ya no está en el grupo «2 · Priorización» sino en **«Herramientas»** (antes de «Puntuar datos nuevos»); los nombres de las 8 secciones y sus URL no cambian. El orden de `SECCIONES` cambia: Validación es la 4.ª y Explica la 5.ª, así que las capturas de `images/ep3/pagina/` se numeran `04_validacion_*` y `05_explica_una_caja_*` (se borraron las de la numeración anterior).
- **Auditoría (F31):** textos y lógica en `app_logica.py` (`AUD_*`, `resumen_auditoria`, `orden_gravedad`, `titular_auditoria`, `tabla_celdas_auditoria`, `siguiente_filas_mapa`, `rotulo_boton_mapa`). Una sola tabla de celdas marcadas; el mapa muestra 10 filas y agrega 50 por clic (con hasta 60 segmentos, todos). No repetir esos textos en `app/`.
- **Cola (F32):** `preparar_cola` **solo reordena** el conjunto que elige `cola_segmento` (por probabilidad, segmento, objeto, fotograma); no cambia qué cajas entran ni los positivos. Elegir el conjunto por probabilidad cambiaría las cifras (10.464 → 10.249 positivos con dos pasos y 20 %): no hacerlo. El plan (flujo, presupuesto o meta) cambia las tarjetas, la curva y la lista; los filtros solo la lista. La Cola deja su presupuesto y flujo en `st.session_state["_plan_cola"]`.
- **Explica (F33):** el umbral del presupuesto se calcula de la cola real (`umbral_presupuesto`, `veredicto_caja`), nunca fijo; con la prioridad máxima empatada dice «0 a N %» y entre cuántas cajas está (`texto_lugar`), no un lugar exacto. Un solo control decide (puntos del sensor superior). Llega con los valores de la caja desde la Cola («Explicar esta caja →») o el Resumen («Abrir») por `_explica_caja` (con `prioridad` y `origen`) y `_ir`; el aviso «Valores cargados desde …» sale al mover un control. Prueba: `tests/ep3/test_pagina_f33.py`. En AppTest, tras un cambio de página hecho por un botón, la siguiente ejecución vuelve a la página por defecto: volver a llamar `ir_a`.
- **Excepción puntual a la regla de F23 (sin flechas):** «Explicar esta caja →», «Ir a la cola de revisión →» y «← Volver a …» las pidió el prompt; sus textos viven en constantes de `app_logica.py` (`COLA_BOTON_EXPLICAR`, `ENLACE_COLA_DESDE_AUDITORIA`, `EXP_ENLACE_VOLVER`). Los demás enlaces y botones siguen sin flechas.
- Los datos de 300 segmentos son sintéticos (`escala_sintetica.py`, solo en memoria o en directorios temporales): `scripts/ep3/f31_f32_prueba_escala.py`. Las cifras compartidas entre páginas se comprueban con `scripts/ep3/f33_cifras_cruzadas.py`. Las 16 capturas de revisión salen de `scripts/ep3/f31_f33_capturas.py` (carpeta `images/ep3/pagina/para_revision_f31_f33/`). Reporte: `docs/ep3/REPORTE_F31_F33.md`; sello: `f23_integridad_sello.py --comprobar --etiqueta f33`.
- Un botón deshabilitado se distingue por el borde punteado y el cursor, no por un texto apagado (4,5:1). Quedan en el reporte, sin cambiar: el término «Lista A» en textos, «Segmentos nuevos» del Resumen y el texto de Ayuda sobre el rol y el Modo presentación.

## EP3: F34 y F35, Validación y Puntuar datos nuevas (estado al 2026-11-23, a pedido del usuario con `docs/referencias_diseno/f34_*.html` y `f35_*.html`)
- **Reemplaza** de F30: en Validación › «En muestra», «Impacto estimado» va **antes** del gráfico (orden de la maqueta de F34: aviso, lectura, impacto, «De dónde viene la mejora de la auditoría», gráfico). Las seis pestañas antiguas (Hiperparámetros, Ensambles, Selección, No supervisado…) son hoy cinco: **Modelo elegido, Generalización, Alternativas, Tipos de caso, En muestra**; las capturas se llaman `04_validacion_<pestaña>` con esos nombres.
- **Validación (F34):** lógica y textos en `src/waymo_evaluacion/ep3/validacion.py` (titular calculado con sus dos ramas, conteos O1 a O4, puntos clave, especificación de cada tabla de apoyo, `DESCRIPCION_CANDIDATOS` con su fuente); no repetir esos textos en `app/`. El titular afirma que la regla se mantiene SOLO si ninguna alternativa cumple O2; el mínimo por partición sale del plan v3 (`auc_minimo_particion`), nunca escrito a mano.
- **Una sola tabla:** `app/tablas.py` (`mostrar_tabla`, `tablas_de_apoyo`) y `src/waymo_evaluacion/ep3/tablas_estandar.py` (formato puro). Toda tabla nueva de Validación o Puntuar pasa por ahí (`Col`, `construir_tabla`, `tabla_de_listas`); las columnas que no caben van solo al CSV. El identificador de segmento se ve «…534050» (`F.segmento_corto`); el de 12 dígitos queda en los CSV. Signo menos único «−» (`F.menos`, `F.decimal_signado`) y «sin pareja» en lugar de `sin_camara` (`F.texto_visible`).
- **Reglas de estilo que la maqueta contradecía y se respetaron:** ámbar solo en un punto (ciclistas) y en los avisos con punto; sin radios de píldora (999px), sin peso 700 y sin más `linear-gradient` que la escala del mapa; sin caracteres «✓/✕» en `estilos.py` (van como escapes). Las flechas siguen prohibidas salvo las de F31 a F33.
- **Puntuar (F35):** lógica y textos en `src/waymo_evaluacion/ep3/puntuar.py`; el segmento puntuado vive solo en `st.session_state["_pt_vista"]` (nunca los archivos de entrada) y «Cargar otro segmento» lo suelta y cambia la clave de los selectores (`pt_ronda`). Sin archivo 2 no hay celdas marcadas ni cifras de cajas sin pareja: la página lo dice, no inventa. **«No se guarda nada» solo puede mostrarse mientras ni la página ni `puntuar.py` escriban a disco ni usen cachés persistentes** (lo vigilan `test_pagina_f35.py` y `test_pagina_f26.py`). `maxUploadSize = 500` está en las dos `config.toml` (la raíz no lo tenía: el límite real era 200 MB).
- Regresión de cifras de Validación: `scripts/ep3/f34_exportar_valores.py` regenera la línea base (`tests/ep3/datos_f34/valores_antes_validacion.json`, calculada con `tabla_legible`, que no cambió). Capturas de revisión: `scripts/ep3/f34_f35_capturas.py` (carpeta `images/ep3/pagina/para_revision_f34_f35/`). Escala: `f35_prueba_escala.py`. Cifras entre páginas: `f34_cifras_cruzadas.py`. Reporte: `docs/ep3/REPORTE_F34_F35.md`; sello: `f23_integridad_sello.py --comprobar --etiqueta f35`.

## EP3: F36, Ética y límites, Ayuda y glosario y modo de despliegue (estado al 2026-11-23, a pedido del usuario con `docs/referencias_diseno/f36_*.html` y `prompt_F36.md`)
- **Textos:** viven en `src/waymo_evaluacion/ep3/etica_ayuda.py` (Ética, pasos, grupos del glosario, `FRASES_AJUSTADAS`, buscador `filtrar_glosario`) y en `app_logica.py` (glosario, preguntas frecuentes y `TEXTOS_ENTORNO`); `app/secciones.py` solo los dibuja. No repetirlos en `app/`. Cada frase de antes sigue con su redacción: si se toca una, agregarla a `FRASES_AJUSTADAS` con la razón (`tests/ep3/test_pagina_f36.py` compara con `tests/ep3/datos_f36/textos_antes.json`).
- **Modo de despliegue:** una sola constante `MODO_DESPLIEGUE` (`local` por defecto) elige los textos de `TEXTOS_ENTORNO` por `texto_entorno(clave)` (Consideraciones éticas, Dónde corre, FAQ de archivos, etiquetas de Puntuar). `EP3_ENTORNO` (`publicado` o `servidor`) la reemplaza solo en el proceso donde se define. La variante `publicado` son borradores («borrador: verificar», `[nombre del servicio]`) y **no se activa**; antes de publicar hay que revisarlos y decidir la licencia de los datos derivados de Waymo (`data/09_app_ep3/cajas_oof.parquet`; evidencia en `docs/ep3/f36_verificacion_despliegue.json`).
- Clase CSS `aud-guia3` (no `aud-paso`: una prueba de F20 lo prohíbe); iconos decorativos con `aria-hidden`; la barra peatones/ciclistas lleva los dos números en texto y su descripción. Ámbar solo en el punto de ciclistas. Sin flechas en los enlaces nuevos.
- El glosario no tiene términos extra; el buscador no distingue mayúsculas ni tildes y se combina con el grupo. La respuesta de «¿Cuánto tarda revisar una caja?» cita «Supuestos y confiabilidad».
- Capturas: `scripts/ep3/f36_capturas.py --puerto 8531` (la del modo publicado lanza una copia con `EP3_ENTORNO=publicado` en otro puerto). Reporte: `docs/ep3/REPORTE_F36.md`; sello: `f23_integridad_sello.py --comprobar --etiqueta f36`. Suite de EP3: 378.

## EP3: F37, datos de la demostración en vivo (estado al 2026-11-23, a pedido del usuario con `prompt_F37_datos_demo.md`; parcial)
- **Faltan los segmentos reales nuevos**: no se pudo bajarlos (sin `gcloud`/`gsutil` ni cuenta). `datos_demo/` (ignorada por git y por `.dockerignore`) solo trae `LEEME_PENDIENTE.md`. Para completarlo: `scripts/ep3/f37_colab_descargar.py` (Colab, split `validation`: ningún id puede estar entre los 41 ni en el plan sellado, que son `training`) → `f37_armar_demo.py` → `f37_pruebas_ui.py`. Detalle en `docs/ep3/REPORTE_F37.md`. No usar segmentos de `training` fuera de los 41: podrían ser candidatos del plan sellado.
- **Resumen:** el bloque «Segmentos puntuados en esta sesión» (`puntuar.registrar_en_sesion`, `tabla_sesion`, `_bloque_sesion`; clave `_pt_sesion`) aparece solo tras puntuar un segmento nuevo, debajo de todo lo congelado; no registra los ejemplos de desarrollo y no debe cambiar ninguna cifra existente ni `cola_segmento`. Una prueba (`test_pagina_f37.py`) lo vigila; sin segmentos puntuados el Resumen es idéntico al de F30.
- **Orden en vivo:** ya no importa (F39): los dos archivos se suben en cualquier orden y se puntúa con «Puntuar segmento» (ver la sección F39 de abajo).
- `scripts/crear_demo_hueco.py` fabrica el hueco SIMULADO (el nombre del archivo y su LEEME lo dicen siempre; `lidar_box` idéntico byte a byte). Decirlo siempre como falla simulada sobre un segmento real, nunca como hallazgo.
- Las pruebas y capturas de `para_revision_f37/` son de ensayo con segmentos de desarrollo: regenerarlas con los datos reales. Pruebas de EP3: ver `pruebas_ep3_conteo.json`.
- **Ejemplo de Puntuar (a pedido, DEC-147):** muestra su celda marcada real vía `puntuar.completar_ejemplo` (usa `lista_A`, `celdas` y `cajas_oof` ya calculados; no reconstruye parejas por cámara). Si cambian esas tablas, la prueba de `test_pagina_f35.py` y `test_pagina_f37.py` lo avisan. Plan B de la demo: el botón de ejemplo sí muestra un hueco (de desarrollo, no nuevo).

## EP3: F38, README final (estado al 2026-11-24, a pedido del usuario con `prompt_F38_readme_final.md`)
- **Excepción autorizada a la regla de solo lectura de EP2:** `README.md` se regenera con `scripts/generar_readme.py` (EP3 agregó un módulo, `scripts/ep3/readme_f38.py`). Nunca editar `README.md` a mano. El informe de EP2 y `data/08_reporting/*` (incluido `pytest_resumen.json`) siguen de solo lectura. La suite completa (`pytest -q`) y `scripts/medir_pruebas.py` solo se corren en una **copia temporal** del repositorio (reescriben README, informe y parquets).
- Orden para regenerar el README: `contar_pruebas.py` → `medir_pruebas_ep3.py` (corre `tests/ep3`, ~5 min) → `generar_readme.py` → `tests/ep3/test_readme_f38.py`. El README cita el número de pruebas de `pruebas_ep3_conteo.json`: si se agregan pruebas, volver a contar y regenerar. Si falta alguna cifra o archivo, el generador falla (no rellena).
- El generador de EP2 ya no exige que `xgboost` esté ausente del entorno (el entorno de EP3 lo trae): comprueba solo `requirements.txt` y los notebooks 07 a 10. No volver a poner esa comprobación sobre el entorno.
- Estado del despliegue: `docs/despliegue.json` (hoy «en preparación», sin URL, modo `local`). Lo que completa el equipo: `docs/ep3/readme_entradas.json` (retroalimentación vacía: el README dice «Pendiente»). No inventar una URL ni retroalimentación.
- El README no puede llamar «En 30 segundos» a su resumen ni usar encabezados `##` sin número (pruebas de EP2); sus subtítulos 8.1 a 8.3 y 12.1 son `###`. Capturas de la aplicación: `scripts/ep3/f38_capturas_app.py` (carpeta `images/app/`).

## EP3: F39, Puntuar datos nuevos con un botón explícito (estado al 2026-11-24, a pedido del usuario con `prompt_F39_puntuar_flujo.md`)
- **Reemplaza** el flujo de F35 y F37: nada se puntúa al subir un archivo. Los dos cargadores van siempre en el bloque «Archivos del segmento» (abierto antes de puntuar, cerrado después; es SIEMPRE el mismo `st.expander` para que los cargadores no se vuelvan a montar) y el botón primario «Puntuar segmento» (`_zona_puntuar`, deshabilitado sin el archivo 1) es lo único que calcula archivos. El ejemplo de desarrollo es un botón pequeño a un lado (`pt_ejemplo`). Textos y lógica en `puntuar.py` (`BOTON_PUNTUAR`, `AYUDA_*`, `AVISO_CAMBIARON`, `ayuda_flujo`, `firma_archivo`, `estado_pasos(hay_resultado, con_huecos)`); no repetirlos en `app/`.
- **El resultado lleva su firma** (`Vista.firma`: nombre, tamaño y sha256 de los dos archivos; `None` en el ejemplo). Si la firma de los cargadores actuales no coincide, el resultado NO se muestra y aparece «Cambiaron los archivos…». Estado en `st.session_state`: `_pt_vista`, `_pt_error` (mensaje + firma, se muestra mientras los archivos no cambien), `_pt_firmas` (caché en memoria de firmas, sin contenido), `pt_ronda` (cambia la clave de los cargadores), `usar_ejemplo`, `_pt_sesion` (Resumen). No escribir a disco.
- Paso 2 «omitido: falta el archivo 2» (clase `omitido`, guion neutro `\u2013`, nunca el check); error de segmentos distintos con los dos ids completos (`puntuar._ids`); bajo el título del resultado, el nombre completo (`Vista.nombre_segmento`). Regresión de resultados: `scripts/ep3/f39_regresion.py` (compara los CSV de adentro del ZIP: el ZIP lleva la hora de creación). Pruebas de estado en el navegador: `f39_pruebas_ui.py` (en esta versión de Streamlit los archivos son `stFileChip` y su «x» `stFileChipDeleteBtn`; volver a elegir el MISMO archivo con el protocolo del navegador no dispara el cambio: usar una copia con otro nombre).
- Guion de la demo (no se versiona): `datos_demo/LEEME_DEMO.md`, con los 4 segmentos reales de `datos_demo/candidatos/` (split `validation`). El README (F38) todavía dice «archivo 2 primero» en la sección 16.
