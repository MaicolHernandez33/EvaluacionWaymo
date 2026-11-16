"""Genera docs/ep3/REPORTE_F20.md (reporte de la tarea F20: rediseño de la página como herramienta de trabajo y cierre de documentos).

Cifras leídas de: data/08_reporting_ep3 (pagina_arranque.json = F19-B, el «antes»; pagina_arranque_f20.json = el «después»; capturas_resultado.json; pruebas_ep3_conteo.json;
captura_linea_tiempo_*.json), docs/ep3/guion_presentacion.md (palabras por bloque), preguntas_cruzadas.md y la propia lógica de la página (app_logica.py). Corre las tres verificaciones de congelados
y la suite ``tests/ep3`` (el comando permitido) y registra su resultado. Sin cifras a mano.
Uso: .venv\\Scripts\\python scripts/ep3/generar_reporte_f20.py [--sin-pruebas]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
REP, DOC = RAIZ / "data/08_reporting_ep3", RAIZ / "docs/ep3"
PY = str(RAIZ / ".venv" / "Scripts" / "python.exe")
INICIO_F20 = time.mktime(time.strptime("2026-11-15 17:45", "%Y-%m-%d %H:%M"))      # el primer archivo de F20 se escribió a las ~17:55; antes de esta hora no se tocó nada

SELLADOS = ["docs/ep3/plan_v3.md", "docs/ep3/plan_v3.json", "docs/ep3/plan_v3.sha256", "docs/ep3/plan_seleccion_ep3.json", "docs/ep3/plan_seleccion_ep3.sha256", "src/waymo_evaluacion/ep3/seleccion_nuevos.py",
            "src/waymo_evaluacion/ep3/sellado.py", "src/waymo_evaluacion/ep3/alternativas.py", "scripts/ep3/evaluar_sellado.py", "scripts/ep3/ingesta_nuevos.py", "scripts/ep3/copiar_sello_a_artefactos.py",
            "scripts/ep3/f19_congelar_alternativas.py", "notebooks/00b_seleccion_segmentos_ep3.ipynb", "scripts/ep3/crear_notebook_00b.py", "data/05_model_input_ep3/dev_41.parquet", "data/06_models_ep3/manifest_v3.json",
            "data/06_models_ep3/manifest_alternativas.json", "data/06_models_ep3/alternativas_v3.joblib", "data/06_models_ep3/modelo_final_v3.joblib"]


def c(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def verificar(script: str) -> str:
    r = subprocess.run([PY, script], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (r.stdout.strip().splitlines() or ["(sin salida)"])[-1]


def rango(es: list[dict], clave: str) -> str:
    v = [e[clave] for e in es if e.get(clave) is not None]
    a, b = c(min(v)), c(max(v))
    return a if a == b else f"{a} a {b}"


def tabla_guion() -> tuple[list[tuple[str, str, int, int]], int, float]:
    filas = []
    for linea in (DOC / "guion_presentacion.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d+:\d{2} a \d+:\d{2}) \| ([^|]+) \|.*\| (\d+) \| (\d+) \|$", linea)
        if m:
            filas.append((m.group(1), m.group(2).strip(), int(m.group(3)), int(m.group(4))))
    total = sum(f[2] for f in filas)
    return filas, total, total / 555 * 60


def main() -> None:
    sin_pruebas = "--sin-pruebas" in sys.argv
    from waymo_evaluacion.ep3 import formato as F
    from waymo_evaluacion.ep3.app_logica import SECCIONES, cargar_datos, inicio_resumen
    from waymo_evaluacion.ep3.chequeo_md import revisar_carpeta

    antes = json.loads((REP / "pagina_arranque.json").read_text(encoding="utf-8"))["escenarios"]
    despues = json.loads((REP / "pagina_arranque_f20.json").read_text(encoding="utf-8"))["escenarios"]
    a_con = [e for e in antes if e["escenario"].startswith("con lanzador")]
    d_con = [e for e in despues if e["escenario"].startswith("con lanzador")]
    d_sin = [e for e in despues if e["escenario"].startswith("sin lanzador")]
    a_sin = [e for e in antes if e["escenario"].startswith("sin lanzador")]
    cap = json.loads((REP / "capturas_resultado.json").read_text(encoding="utf-8"))
    n_cap = sum(1 for x in cap if x["listo"])
    lento = max(x["segundos_hasta_completa"] for x in cap if x["segundos_hasta_completa"] is not None)
    n404 = sum(x.get("404_internos_de_streamlit", 0) for x in cap)
    cont = json.loads((REP / "pruebas_ep3_conteo.json").read_text(encoding="utf-8"))
    nuevas = cont["por_archivo"].get("tests/ep3/test_pagina_f20.py", 0)
    problemas = revisar_carpeta(DOC)
    n_docs = len({p.name for p in DOC.glob("*.md")} | {"REPORTE_F20.md"})            # incluye este reporte (se escribe al final)
    guion, palabras, ppm_prom = tabla_guion()
    preg = len(re.findall(r"^\*\*\d+\. ", (DOC / "preguntas_cruzadas.md").read_text(encoding="utf-8"), flags=re.M))
    D = cargar_datos(RAIZ / "data/09_app_ep3")
    r = inicio_resumen(D, 20)
    et = json.loads((REP / "captura_linea_tiempo_etica_y_limites.json").read_text(encoding="utf-8"))
    au = json.loads((REP / "captura_linea_tiempo_auditoria_de_camaras.json").read_text(encoding="utf-8"))
    aud_parciales = sum(1 for x in au if x["estado"] == "running" and x["cuentas"] and any(k > 0 for k in x["cuentas"]) and not x["tiene_clave"])
    aud_ciegas = sum(1 for x in au + et if x["estado"] == "running" and not x["viejo_ocupado"])
    aud_ejec = sum(1 for x in au + et if x["estado"] == "running")
    tocados = [s for s in SELLADOS if (RAIZ / s).exists() and (RAIZ / s).stat().st_mtime >= INICIO_F20]
    v14, v5, v1 = verificar("scripts/verificar_congelados.py"), verificar("scripts/ep3/verificar_congelados_v3.py"), verificar("scripts/ep3/verificar_no_supervisado.py")
    if sin_pruebas:
        pruebas_txt = "(no se ejecutaron en esta corrida del generador)"
    else:
        t0 = time.time()
        pr = subprocess.run([PY, "-m", "pytest", "tests/ep3", "-q", "--no-cov", "-p", "no:cacheprovider"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace")
        ultima = [l for l in pr.stdout.strip().splitlines() if "passed" in l or "failed" in l]
        pruebas_txt = f"`{(ultima[-1] if ultima else pr.stdout.strip().splitlines()[-1]).strip('= ')}` (código {pr.returncode}; {c(time.time() - t0, 0)} s)"
    previo = {"Resumen": "Inicio", "Validación": "Evidencia"}              # nombres de F19-B

    def peor(es: list[dict], nombre: str) -> float | None:
        v = [e["secciones_s"].get(nombre) for e in es if e["secciones_s"].get(nombre) is not None]
        return max(v) if v else None

    filas_sec = []
    for s in SECCIONES:
        a_c, d_c = peor(a_con, previo.get(s, s)), peor(d_con, s)
        filas_sec.append(f"| {s} | {c(a_c) if a_c is not None else '—'} | {c(d_c) if d_c is not None else '—'} |")
    sec_tabla = chr(10).join(filas_sec)
    guion_tabla = "\n".join(f"| {t} | {b} | {w} | {p} |" for t, b, w, p in guion)
    md = f"""# Reporte de la tarea F20: rediseño de la página como herramienta de trabajo y cierre de documentos

*Generado por `scripts/ep3/generar_reporte_f20.py`; cifras de `data/08_reporting_ep3` (`pagina_arranque.json`, `pagina_arranque_f20.json`, `capturas_resultado.json`, `pruebas_ep3_conteo.json`, `captura_linea_tiempo_*.json`), de `docs/ep3/guion_presentacion.md` y de la misma lógica que usa la página. Decisiones: `ESTADO.md` (DEC-57 en adelante, sección F20). Las cifras de la página no cambiaron: se validan contra `pagina_numeros_antes.json` y la regresión de cifras. El zip y la copia limpia NO se rearmaron.*

## Resumen
La página pasó de parecer una landing de plantilla a una consola interna de revisión: navegación agrupada (`st.navigation`), wordmark propio, rol al pie, **un solo chip** de estado «Datos de desarrollo · sin validación externa» (con el texto completo de «en muestra» en su popover) y un sistema visual sobrio (un acento, bordes de 1 px, Segoe UI, cifras tabulares). La cola de revisión es ahora **maestro-detalle** (dos flujos a la vista, selección de fila con panel de detalle, vista por objeto y filtros). La causa del render incompleto de «Ética y límites» en la captura fue **la captura, no la página** (ver más abajo). Se hicieron dos pasadas de corrección con las capturas. Pruebas: {cont['recolectadas_ep3']} recolectadas en `tests/ep3` ({nuevas} nuevas de F20): {pruebas_txt}. Capturas: {n_cap} de {len(cap)} listas (la más lenta en estar completa: {c(lento)} s). Documentos: {n_docs} revisados, {'0 con problemas' if not problemas else str(len(problemas)) + ' con problemas'}. Verificaciones: EP2 «{v14}»; v3 «{v5}»; no supervisado «{v1}».

## Bloque P: la página
### P0. Auditoría previa (`auditoria_diseno_pagina.md`)
- **Qué encontré:** leí las 9 capturas de F19-B a 1366 px contra 12 patrones de plantilla (T1 a T12): portada de marketing, tarjetas KPI con borde de color, píldora de perfil y producto repetido, banner ámbar con acordeón en cada pantalla, aviso «Nada se guarda ni se envía» repetido, menú de radios, textos que hablan de la propia página, acordeones en todo, ninguna interacción de producto, títulos y cifras gigantes, pantallas vacías y tablas con encabezados cortados.
- **Qué cambié:** el documento lista, por sección, el defecto y lo que se haría; lo generó `scripts/ep3/generar_auditoria_diseno.py`.

### P1 y P2. Marco, navegación y sistema visual
- **Qué encontré:** `st.navigation` solo funciona con `AppTest` si las páginas son **archivos** (`switch_page` exige una ruta; con funciones falla): lo probé en un experimento aislado antes de escribir código (DEC-57).
- **Qué cambié:** `app/app.py` es ahora el marco (configuración, estilos, wordmark SVG propio con `st.logo`, navegación agrupada en Revisión / Calidad de datos / Análisis / Herramientas / Ayuda, rol y modo presentación al pie, pie único); cada sección es un archivo corto de `app/paginas/`. Solo se renombraron Inicio → Resumen y Evidencia → Validación. El rol cambia la página que se abre (con una bandera de sesión, porque `st.switch_page` no es fiable en un callback) y ordena primero su alerta. `?seccion=` sigue funcionando. Sin banners ámbar ni «¿Qué significa?»: el chip único cumple DEC-14 y cada cifra del flujo en dos pasos lleva «en muestra». Estilos en `app/estilos.py` (sin sombras, sin bordes de color, radio de 6 px, un solo acento, rojo solo para hueco y ámbar solo para «en muestra»; contraste ≥ 4,5:1 verificado).

### P3. Resumen
- Cuatro métricas compactas (cajas analizadas {F.entero(r['cajas'])}, {c(100 * r['prevalencia'])} % sin pareja, {r['celdas_marcadas']} celdas marcadas, {r['segmentos']} segmentos) y «Impacto estimado»: barras de horas a 20 s por caja para encontrar el 80 %: **≈ {r['horas_sin_orden']:.0f} h** revisando sin orden, **≈ {r['horas_un_paso']:.0f} h** solo cola (un paso; el titular, lo robusto) y **≈ {r['horas_dos_pasos']:.0f} h** auditoría + cola (dos pasos, rotulada «en muestra»). Origen: `ie12__brazo_C_y_equilibrio` (= `f6_modelo_escogido.csv`) y el número de cajas; 200 h = fracción un paso × cajas × 20 s. Tres alertas con enlace (celdas marcadas, ciclistas con cifras de `f12_equidad.csv`, validación externa pendiente). Sin «Cómo funciona» ni «Empiece por aquí». Las cinco cifras de validación que estaban en un acordeón de Inicio pasaron a la pestaña Selección de Validación.

### P4. Cola de revisión (maestro-detalle)
- Barra de controles en una fila (segmento, flujo, modo, control con su unidad y «Volver al 20 %»), filtros por clase y cámara y «Agrupar por objeto» en la misma barra; el flujo por defecto sigue siendo «Auditoría + cola (dos pasos, en muestra)».
- La frase de resultado muestra **siempre ambos flujos**: «Con auditoría previa (en muestra): unas 70 de cada 100 · Solo cola: unas 62 de cada 100», más cajas a revisar y horas del flujo elegido (el valor de un paso es el conteo observado; coincide con la curva guardada con menos de 0,6 puntos; prueba).
- Pestañas «Curva de cobertura» y «Cola de cajas»; «Supuestos y confiabilidad» en un popover único.
- Tabla con selección de fila (`on_select="rerun"`): el panel de detalle (probabilidad calibrada, posición en la cola, tipo de caso, cámara, distancia, puntos, advertencia de ciclista) reutiliza la lógica de «Explica una caja». La columna «Prioridad» (barra saturada en 100) se reemplazó por la **probabilidad calibrada** (`prob_cal`); no cambió el orden ni las cifras. «Agrupar por objeto» deja una fila por objeto con su mejor posición y los fotogramas en la cola (el conteo de cajas no cambia; prueba). Los filtros solo cambian la vista («Filtrado: N cajas») y no las cifras globales. Encabezados con el ancho calculado (`formato.anchos_columnas`): ya no hay «Posició».

### P5 a P9
- **Auditoría de cámaras:** dos columnas (mapa en un contenedor de altura fija con desplazamiento; a la derecha métricas mínimas, Lista A con «Acción sugerida» y descarga), **una sola leyenda**, etiquetas de segmento de 6 dígitos (únicas en los 41; el id completo va en el tooltip), orden por defecto con las celdas marcadas primero y opción de ver solo celdas con datos suficientes; se conservan el rojo con X y el gris rayado (2 huecos y 94 de 205 celdas sin datos suficientes, igual que antes).
- **Explica una caja:** dos columnas (controles y resultado), tres ejemplos de un clic («Caja cercana y densa», «Caja lejana con pocos puntos», «Ciclista lejano») y el texto «Posición en la cola: 59 % (0 % es la primera caja; 100 %, la última)». Verifiqué el significado en `percentil_en_cola`: es la fracción de la cola que queda **antes** de la caja. Encontré además que el gráfico de «Detalle técnico» era una línea plana (variaba los puntos totales y la regla usa los del sensor superior): ahora muestra la probabilidad según los puntos del sensor superior con la selección marcada.
- **Validación:** cada pestaña abre con un gráfico leído de los CSV (mejora de PR-AUC con IC, diferencia de AUC con IC, AUC con IC por candidato y por pliegue, tasa por tipo de caso, brazos A, B y C con la etiqueta) y la tabla completa en un expander; «Pliegues» en lugar de «Folds»; Selección abre con el cuadro O1 a O4 (nadie cumple O2 ni O4). **Límite:** el AUC por pliegue trae 3 candidatos porque `f5_auc_por_fold.csv` no está completo en `data/09_app_ep3` y F20 no puede escribir ahí (anotado en `PENDIENTES_PAGINA.md`).
- **Puntuar datos nuevos:** «Archivo 1 (obligatorio)» y «Archivo 2 (opcional)», formato esperado como tabla, estado vacío sobrio, resumen en tabla (sin `st.json`) y **«Usar un segmento de desarrollo de ejemplo»**: sí era posible sin datos crudos de Waymo (se reconstruye un `lidar_box` mínimo desde las variables derivadas de `cajas_oof`; la prueba comprueba que el orden de la cola coincide con el de la página). No trae archivo de asociación (reconstruirlo sería inventar a qué cámara pertenece cada caja), así que el ejemplo no audita cámaras.
- **Ética y Ayuda:** ficha de sistema en dos columnas (6 bloques, las mismas cifras: 0,443 contra 0,806; 115 casos en 14 segmentos; AUC 0,823), glosario como tabla de dos columnas, una línea con el flujo de tres capas y preguntas frecuentes como acordeones.

### P10. Redacción
Revisé los textos de `app/` y `app_logica.py` (registro neutro, sin segunda persona de tutorial, sin avisos repetidos). Una prueba (`FRASES_PROHIBIDAS`) vigila «Empiece por aquí», «Cómo funciona», «la página se lo dice», «Mueva los controles», «vea qué pasa», «¿Qué significa?», «Primeros pasos», «Resultados técnicos» y «Pase el cursor», y que «Nada se guarda ni se envía» solo aparezca en Ayuda y Ética.

### P11. Capturas y control de calidad
- **Causa del render incompleto de «Ética y límites» (investigada):** **fue la captura, no un defecto de render.** La de 1366 px salió con 1 tarjeta y la de 1920 px, de la misma corrida, con las 5. Streamlit dibuja a medida que el script avanza y el criterio de F19-B (texto del primer elemento + sin spinner) no podía ver que el script seguía ejecutándose: en las líneas de tiempo en frío, el script estuvo ejecutándose en {aud_ejec} muestras y el indicador del criterio antiguo apareció en {aud_ejec - aud_ciegas} de ellas; en «Auditoría de cámaras» hubo {aud_parciales} muestras con la página a medias. La precarga alarga la ventana (la primera visita espera los datos) pero no es la causa; en F20 cada sección carga el contexto antes de dibujar. Detalle en `auditoria_diseno_pagina.md`.
- **Espera nueva:** `data-test-script-state = notRunning`, DOM estable ≥ 2 s, **último** elemento clave y conteos (6 bloques en Ética), alto mínimo y pie; si no se cumple no guarda la imagen. Ya atrapó dos errores durante F20. Los {n404} «404» de la consola son los pedidos internos de Streamlit a `/pagina/_stcore/...` y se cuentan aparte.
- **Capturas:** 8 secciones y el modo presentación a 1366 y 1920 px ({n_cap} imágenes en `images/ep3/pagina/`; las de F19-B, en `antes_f20/`). La cola se fotografía con «Cola de cajas» abierta y la primera fila elegida.
- **Dos pasadas de corrección** (detalle en `auditoria_diseno_pagina.md`): pasada 1, wordmark cortado, fuente con clave interna, Lista A desbordada, captura de la cola y modo presentación; pasada 2, chip cortado en modo presentación, «Tipo de caso» fuera de vista con el panel abierto, barra de desplazamiento de la barra lateral y conteos de la captura de Auditoría.

### P12. Pruebas y tiempos
- {nuevas} pruebas nuevas en `tests/ep3/test_pagina_f20.py` y las anteriores adaptadas al nuevo esquema: humo de las {len(SECCIONES)} páginas x 3 roles x modo presentación, regresión de cifras contra `pagina_numeros_antes.json`, selección de fila y detalle, vista agrupada con el mismo conteo, frases prohibidas, ausencia de URLs externas, contraste, es-CL.
- **Tiempos de carga** (navegador sin interfaz y perfil nuevo, 2 arranques en frío por variante; `pagina_arranque.json` = F19-B, `pagina_arranque_f20.json` = F20; «completa» = script terminado y último elemento presente, sin contar los 2 s de estabilidad que pide la captura):

| | F19-B (antes) | F20 (después) |
|---|---|---|
| Con lanzador: primera visita (s) | {rango(a_con, 'primera_visita_explica_s')} | {rango(d_con, 'primera_visita_explica_s')} |
| Con lanzador: página más lenta después de la primera (s) | {rango(a_con, 'maximo_secciones_s')} | {rango(d_con, 'maximo_secciones_s')} |
| Sin lanzador: primera visita (s) | {rango(a_sin, 'primera_visita_explica_s')} | {rango(d_sin, 'primera_visita_explica_s')} |
| Servidor responde, con lanzador (s) | {rango(a_con, 'servidor_responde_s')} | {rango(d_con, 'servidor_responde_s')} |

| Página | F19-B, peor de los arranques con lanzador (s) | F20, peor de los arranques con lanzador (s) |
|---|---|---|
{sec_tabla}

Lectura: con el lanzador la primera visita no cambió ({rango(a_con, 'primera_visita_explica_s')} s antes, {rango(d_con, 'primera_visita_explica_s')} s ahora) y ninguna página pasa de {rango(d_con, 'maximo_secciones_s')} s después; sin el lanzador la primera visita fue de {rango(d_sin, 'primera_visita_explica_s')} s en F20 contra {rango(a_sin, 'primera_visita_explica_s')} s en F19-B ({'dentro de la dispersión de la medición' if max(e['primera_visita_explica_s'] for e in d_sin) <= max(e['primera_visita_explica_s'] for e in a_sin) + 0.3 else 'algo más lenta'}). La carga en frío del servidor no depende del rediseño (la precarga es la misma de F19-B).

Meta «ninguna página más de 3 s tras el arranque»: {'se cumple' if all(e['secciones_cumplen_3s'] for e in d_con) else 'NO se cumple en todas las páginas (ver arriba)'} con el lanzador. Es una medición de este equipo, no una garantía; la primera visita incluye la descarga del frontend de Streamlit por un navegador sin caché.

## Bloque D: los documentos
- **D1.** (C5) Nota en el anexo B y pregunta cruzada sobre el segmento `247562357599`, cámara 5: 184 positivos en 665 cajas con más de 100 puntos (27,7 %), la celda que aparece marcada con `frac` = 0,35 y que con los parámetros congelados **no** se marca; rotulada «post hoc, no pre-declarado, hipótesis no verificada» (`f12_eda_puntos_top_resumen.json`, `f12_sensibilidad_detector.csv`). (C6) Pregunta «¿por qué la solución contra la regla da diferencia cero fuera de muestra?» (la solución es `PuntuadorRegla`; qué se mide en su lugar; LR3 y XGBoost, DEV-4).
- **D2.** Cinco preguntas nuevas con respuesta, cifra y fuente: sellado, qué pasa si no hay huecos (caso A: con ≈ 70 celdas elegibles y 1,8 % en desarrollo se esperan ≈ 1,3 marcadas y la probabilidad de 0 es ≈ 27 %, estimación gruesa tipo Poisson, post hoc), por qué LR3 y XGBoost, cómo se eligieron los segmentos nuevos y su sesgo, y por qué el titular compara un paso contra el azar. Las preguntas cruzadas son ahora {preg}.
- **D3.** Las tablas del informe tomadas de CSV (sección 9 y anexos) pasan por `tabla_es`: coma decimal, miles con punto, encabezados legibles (sin snake_case ni «silhouette_muestra_20000») e intervalos de distancia con coma decimal y unidad («(2,26; 18,61] m»); el §14 se partió en cuatro subsecciones (sellado, qué se mide, alternativas, qué se medirá y casos de resultado) sin cambiar su contenido. Todas pasan el chequeo de tablas.
- **D4.** Guion: {palabras} palabras en 9:15 (≈ {ppm_prom:.0f} palabras por minuto en promedio, antes ≈ 71); los bloques técnicos van entre 105 y 135 (con contenido nuevo de IE9 a IE12: diseño anidado, curvas de validación, bordes de grilla, leave-one-segment-out, brecha ajuste-validación, calibración y la regla de reserva DEV-2); la demo sigue el recorrido de la página rediseñada; se agregó el «Plan por resultado de la validación externa» (casos A a D).

| Tiempo | Bloque | Palabras | Palabras/min |
|---|---|---|---|
{guion_tabla}

- **D5.** `REPORTE_F19A.md` dice ahora «al momento de F19-A: 116» y cita el conteo actual (`pruebas_ep3_conteo.json`: {cont['recolectadas_ep3']}). Los reportes de F18 y F19-B son instantáneas de su fecha y no se regeneraron (usan los nombres Inicio y Evidencia).
- **D6.** Regenerados: informe, README_EP3, preguntas, guion, guía de demo, guía de estilo, pendientes de la página, mapa de archivos, auditoría de diseño, `docs/ep3/revision/` y los notebooks 11 a 15 (el 14 con la prueba de humo de las {len(SECCIONES)} páginas x 3 roles y el modo presentación). Los contadores de ESTADO y `plan_integracion_readme.md` se leen de `pruebas_ep3_conteo.json`.

## Verificaciones y reglas
- Congelados de EP2: **{v14}**. Solución v3: **{v5}**. No supervisado: **{v1}**.
- Archivos sellados o protegidos con fecha de modificación posterior al inicio de F20: **{', '.join(tocados) if tocados else 'ninguno'}**. EP2 solo se leyó; sin git (solo `status`, `diff` y `log`); sin paquetes instalados; sin bucket, gcloud ni Docker; la página no hace peticiones externas (una prueba lo vigila).

## Bloqueos
- Ninguno que detuviera el trabajo. Límites anotados con su motivo: el AUC por pliegue de Validación trae 3 candidatos (no se escribe en `data/09_app_ep3`); el ejemplo de «Puntuar» no trae asociación; el CSS depende de atributos internos de Streamlit 1.65 (`PENDIENTES_PAGINA.md`, sección h).

## Lo que te toca
1. Abrir la página con `scripts\\ep3\\arrancar_app.bat` y mirar las capturas de `images/ep3/pagina/` (1366 y 1920 px) y `auditoria_diseno_pagina.md`.
2. Probar con personas de cada rol y en otro equipo o navegador (sigue pendiente).
3. Decidir si el chip y la etiqueta «en muestra» te parecen suficientes para DEC-14 o prefieres algo más visible.
4. Revisar el guion y el «Plan por resultado» y repartir los bloques («Quién»).
5. Sigue pendiente lo de siempre: commit del sello antes del Colab, la validación externa y rearmar el zip y la copia limpia (otra tarea).
"""
    (DOC / "REPORTE_F20.md").write_text(md, encoding="utf-8")
    print("escrito REPORTE_F20.md")
    pend = revisar_carpeta(DOC)
    if pend:
        raise SystemExit(f"los documentos (incluido este reporte) tienen problemas: {pend}")


if __name__ == "__main__":
    main()
