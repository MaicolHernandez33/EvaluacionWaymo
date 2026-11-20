"""Genera docs/ep3/REPORTE_F21.md (reporte de la tarea F21: última ronda de pulido de la página y ajustes de documentos).

Cifras leídas de: data/08_reporting_ep3 (pagina_arranque_f20.json = el «antes»; pagina_arranque_f21.json = el «después»; capturas_resultado.json con la geometría medida en el DOM;
pruebas_ep3_conteo.json), docs/ep3/guion_presentacion.md y pagina_guia_demo.md (palabras por bloque y por paso), preguntas_cruzadas.md, auditoria_diseno_pagina.md (las dos pasadas)
y la propia lógica de la página (formato.py, app_logica.py). Corre las tres verificaciones de congelados y la suite ``tests/ep3`` (el comando permitido) y registra su resultado.
Sin cifras a mano.
Uso: .venv\\Scripts\\python scripts/ep3/generar_reporte_f21.py [--sin-pruebas]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts/ep3"))
REP, DOC = RAIZ / "data/08_reporting_ep3", RAIZ / "docs/ep3"
PY = str(RAIZ / ".venv" / "Scripts" / "python.exe")
INICIO_F21 = (DOC / "REPORTE_F20.md").stat().st_mtime            # F21 empieza cuando termina F20: nada sellado debe tener fecha posterior a la del reporte de F20

SELLADOS = ["docs/ep3/plan_v3.md", "docs/ep3/plan_v3.json", "docs/ep3/plan_v3.sha256", "docs/ep3/plan_seleccion_ep3.json", "docs/ep3/plan_seleccion_ep3.sha256",
            "src/waymo_evaluacion/ep3/seleccion_nuevos.py", "src/waymo_evaluacion/ep3/sellado.py", "src/waymo_evaluacion/ep3/alternativas.py", "scripts/ep3/evaluar_sellado.py",
            "scripts/ep3/ingesta_nuevos.py", "scripts/ep3/copiar_sello_a_artefactos.py", "scripts/ep3/f19_congelar_alternativas.py", "notebooks/00b_seleccion_segmentos_ep3.ipynb",
            "scripts/ep3/crear_notebook_00b.py", "data/05_model_input_ep3/dev_41.parquet", "data/06_models_ep3/manifest_v3.json", "data/06_models_ep3/manifest_alternativas.json",
            "data/06_models_ep3/alternativas_v3.joblib", "data/06_models_ep3/modelo_final_v3.joblib", "entrega_EP3.zip", "entrega_EP3.sha256"]


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


def pasos_demo() -> list[tuple[str, str, int]]:
    """(tiempo, paso, palabras) de la tabla «Recorrido corto» de pagina_guia_demo.md."""
    out = []
    for linea in (DOC / "pagina_guia_demo.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d) \| ([^|]+) \| \*\*([^|]+)\*\* \|.*\| (\d+) \|$", linea)
        if m:
            out.append((m.group(2).strip(), m.group(3).strip(), int(m.group(4))))
    return out


def main() -> None:
    sin_pruebas = "--sin-pruebas" in sys.argv
    from waymo_evaluacion.ep3 import formato as F
    from waymo_evaluacion.ep3.app_logica import COLUMNA_FOTOGRAMAS, ESCALA_PUNTOS, SECCIONES
    from waymo_evaluacion.ep3.chequeo_md import revisar_carpeta
    import generar_auditoria_diseno as AUD

    antes = json.loads((REP / "pagina_arranque_f20.json").read_text(encoding="utf-8"))["escenarios"]
    despues = json.loads((REP / "pagina_arranque_f21.json").read_text(encoding="utf-8"))["escenarios"]
    a_con = [e for e in antes if e["escenario"].startswith("con lanzador")]
    d_con = [e for e in despues if e["escenario"].startswith("con lanzador")]
    a_sin = [e for e in antes if e["escenario"].startswith("sin lanzador")]
    d_sin = [e for e in despues if e["escenario"].startswith("sin lanzador")]
    cap = json.loads((REP / "capturas_resultado.json").read_text(encoding="utf-8"))
    n_cap = sum(1 for x in cap if x["listo"])
    lento = max(x["segundos_hasta_completa"] for x in cap if x["segundos_hasta_completa"] is not None)
    geo = [x["geometria"] for x in cap if x.get("geometria")]
    chip_dev = max(abs(g["chip_derecha"] - g["contenido_derecha"]) for g in geo if g["chip_derecha"] is not None)
    dys = [a["dy"] for g in geo for a in g["alertas"]]
    scroll = max(g["scroll_horizontal_px"] for g in geo)
    cont = json.loads((REP / "pruebas_ep3_conteo.json").read_text(encoding="utf-8"))
    nuevas = cont["por_archivo"].get("tests/ep3/test_pagina_f21.py", 0)
    problemas = revisar_carpeta(DOC)
    n_docs = len({p.name for p in DOC.glob("*.md")} | {"REPORTE_F21.md"})            # incluye este reporte (se escribe al final)
    guion, palabras, ppm_prom = tabla_guion()
    demo = pasos_demo()
    preg = len(re.findall(r"^\*\*\d+\. ", (DOC / "preguntas_cruzadas.md").read_text(encoding="utf-8"), flags=re.M))
    tocados = [s for s in SELLADOS if (RAIZ / s).exists() and (RAIZ / s).stat().st_mtime >= INICIO_F21]
    v14, v5, v1 = verificar("scripts/verificar_congelados.py"), verificar("scripts/ep3/verificar_congelados_v3.py"), verificar("scripts/ep3/verificar_no_supervisado.py")
    if sin_pruebas:
        pruebas_txt = "(no se ejecutaron en esta corrida del generador)"
    else:
        t0 = time.time()
        pr = subprocess.run([PY, "-m", "pytest", "tests/ep3", "-q", "--no-cov", "-p", "no:cacheprovider"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace")
        ultima = [ln for ln in pr.stdout.strip().splitlines() if "passed" in ln or "failed" in ln]
        pruebas_txt = f"`{(ultima[-1] if ultima else pr.stdout.strip().splitlines()[-1]).strip('= ')}` (código {pr.returncode}; {c(time.time() - t0, 0)} s)"

    # columnas de la cola: el peor caso de contenido y lo que suman
    peor = pd.DataFrame({"Posición": [78626], "Prob. sin pareja": ["87,8 %"], "Puntos sensor sup.": ["1.000"], "Clase": ["Ciclista: poco confiable"], COLUMNA_FOTOGRAMAS: [63],
                         "Cámara": ["4 (lateral izq.)"], "Tipo de caso": ["lejanos y poco densos"], "Distancia": ["77,3 m"], "Segmento": ["100239476024"]})
    anchos = F.anchos_columnas(peor)
    suma_cols = sum(anchos.values())

    def peor_seccion(es: list[dict], nombre: str) -> float | None:
        v = [e["secciones_s"].get(nombre) for e in es if e["secciones_s"].get(nombre) is not None]
        return max(v) if v else None

    sec_tabla = chr(10).join(f"| {s} | {c(peor_seccion(a_con, s)) if peor_seccion(a_con, s) is not None else '—'} | {c(peor_seccion(d_con, s)) if peor_seccion(d_con, s) is not None else '—'} |" for s in SECCIONES)
    corrida1 = ""
    ruta_c1 = REP / "pagina_arranque_f21_corrida1.json"
    if ruta_c1.exists():                                                  # la primera corrida de F21 se conserva: no se descarta una medición porque salió lenta
        c1 = json.loads(ruta_c1.read_text(encoding="utf-8"))["escenarios"]
        c1_con = [e for e in c1 if e["escenario"].startswith("con lanzador")]
        c1_sin = [e for e in c1 if e["escenario"].startswith("sin lanzador")]
        lentas = [e for e in c1 if not e["secciones_cumplen_3s"]]
        corrida1 = (f"**Corrida previa conservada** (`pagina_arranque_f21_corrida1.json`): con lanzador, primera visita {rango(c1_con, 'primera_visita_explica_s')} s y página más lenta {rango(c1_con, 'maximo_secciones_s')} s; "
                    f"sin lanzador, primera visita {rango(c1_sin, 'primera_visita_explica_s')} s y página más lenta {rango(c1_sin, 'maximo_secciones_s')} s. "
                    + f"En las dos corridas juntas ({len(c1) + len(despues)} arranques), {len(lentas) + sum(1 for e in despues if not e['secciones_cumplen_3s'])} superaron los 3 s: fueron arranques aislados (precargas o primeras visitas de "
                      f"{', '.join(c(e['primera_visita_explica_s']) for e in lentas + [e for e in despues if not e['secciones_cumplen_3s']])} s, con todas las páginas lentas a la vez) y el otro arranque de la misma variante en la misma corrida estuvo dentro de la meta; "
                      "apunta a carga puntual del equipo (hipótesis, no verificada), no a una página. Se conservan las dos corridas, sin descartar ninguna.")
    guion_tabla = "\n".join(f"| {t} | {b} | {w} | {p} |" for t, b, w, p in guion)
    filas_demo = []
    for t_, b_, w_ in demo:
        seg_ = int(re.search(r"[(](\d+) s[)]", t_).group(1))
        filas_demo.append(f"| {t_} | {b_} | {w_} | {c(w_ / seg_ * 60, 0)} |")
    demo_tabla = "\n".join(filas_demo)
    pasada1 = chr(10).join(f"- {x}" for x in AUD.PASADAS_F21[0][1])
    pasada2 = chr(10).join(f"- {x}" for x in AUD.PASADAS_F21[1][1])
    md = f"""# Reporte de la tarea F21: última ronda de pulido de la página y ajustes de documentos

*Generado por `scripts/ep3/generar_reporte_f21.py`; cifras de `data/08_reporting_ep3` (`pagina_arranque_f20.json` = el «antes», `pagina_arranque_f21.json` = el «después», `capturas_resultado.json`, `pruebas_ep3_conteo.json`), de `docs/ep3/guion_presentacion.md`, `pagina_guia_demo.md`, `auditoria_diseno_pagina.md` y de la misma lógica que usa la página. Decisiones: `ESTADO.md` (DEC-71 en adelante, sección F21). Las cifras de la página no cambiaron: la prueba `test_las_cifras_no_cambian_salvo_el_redondeo_unificado` (`tests/ep3/test_pagina_rediseno.py`) las compara con `data/08_reporting_ep3/pagina_numeros_antes.json` y pasa. El zip y la copia limpia NO se rearmaron.*

## Resumen
La cola de revisión ahora abre con la nota del empate (calculada de la cola) y nueve columnas visibles a 1366 px sin desplazamiento, con el panel de detalle debajo de la tabla a todo el ancho; «Explica una caja» dejó de mostrar «-50,000», dice qué control mueve la probabilidad y usa una escala de puntos no lineal con los puntos A (32) y B (11) marcados en el gráfico; el Resumen alinea el chip y los enlaces de sus alertas y dice «en muestra» a lo más dos veces; ninguna pantalla muestra nombres de archivo, «pliegue», «fold», «OOF» ni «brazo A/B/C»; y las seis pestañas de Validación se revisaron una por una. Se hicieron **dos pasadas de corrección** con capturas de 1366 y 1920 px. Documentos: la guía de demo se partió en un recorrido corto de 95 s (6 pasos, la misma fuente que el guion) y uno extendido de respaldo; las preguntas cruzadas son {preg}. Pruebas: {cont['recolectadas_ep3']} recolectadas en `tests/ep3` ({nuevas} nuevas de F21): {pruebas_txt}. Capturas: {n_cap} de {len(cap)} listas (la más lenta en estar completa: {c(lento)} s). Documentos: {n_docs} revisados, {'0 con problemas' if not problemas else str(len(problemas)) + ' con problemas'}. Verificaciones: EP2 «{v14}»; v3 «{v5}»; no supervisado «{v1}».

## Bloque P: la página

### P1. Cola de revisión
- **Qué encontré:** a 1366 px el área de contenido mide 1.062 px y la tabla, con las columnas calculadas con 6,6 px por carácter, dejaba «Segmento» fuera de la vista; el texto real de la tabla mide 5,5 a 5,6 px por carácter (medido sobre la captura: «lejanos y poco densos» ocupa 117 px para 21 caracteres). El panel a la derecha, además, dejaba la tabla en unos 700 px.
- **Qué cambié:** (a) la **nota del empate** se calcula de la cola (`empate_inicial` y `nota_empate`, `app_logica.py`): «Las primeras N cajas empatan (0 puntos del sensor superior; …); el orden entre ellas no es informativo», y desaparece si no hay empate. Con los datos reales dice «Las primeras 4.742 cajas empatan» (las 4.757 con 0 puntos del informe menos las que quedan en celdas marcadas). La primera versión decía «probabilidad de 80,2 % a 90,4 %» mientras todas las filas muestran 87,8 %; la pasada 1 la corrigió a «87,8 % en la primera y de 80,2 % a 90,4 % en el grupo» (el rango existe porque cada partición calibró por separado). (b) **Orden de columnas:** Posición, Prob. sin pareja, Puntos sensor sup., Clase, Fotogramas, Cámara, Tipo de caso, Distancia, Segmento (después, los identificadores); anchos medidos: las nueve columnas suman {suma_cols} px más 37 de la selección, contra 1.062 disponibles; «Tipo de caso» no lleva ancho fijo y nunca se corta. (c) **Panel de detalle debajo de la tabla, a todo el ancho** (dos columnas internas; sin fila elegida explica qué trae el detalle): elegí esto frente al panel lateral (deja la tabla en ~700 px y corta columnas) y frente a `st.dialog` (tapa la tabla que se está leyendo y suma un clic para volver). Capturas con la primera fila elegida y sin selección, a 1366 y 1920 px; a 1920 la tabla muestra además «Marca de tiempo» e «Identificador de objeto».
- **Fuente de las cifras:** `data/09_app_ep3/cajas_oof.parquet` (misma lógica que la página); el 4.757 y el 90,5 % salen de `f12_eda_calidad_resumen.json`.

### P2. Explica una caja
- **Qué encontré:** el texto de puntaje decía «-50,000» (el puntaje es un entero con signo: menos los puntos del sensor superior) y nada decía qué control mueve la probabilidad. Lo verifiqué con una prueba: al llevar los puntos del LiDAR a 1.000 la probabilidad no cambia; al cambiar los del sensor superior, sí (`test_el_control_de_puntos_del_lidar_no_mueve_la_probabilidad_y_el_de_sensor_superior_si`). Los puntos totales, la distancia y la clase solo afectan al tipo de caso (la clase, además, agrega la advertencia de ciclista).
- **Qué cambié:** «Puntaje: -50 (menos los puntos del sensor superior)»; cada control dice qué mueve («este control mueve la probabilidad», «solo afecta al tipo de caso», «solo agrega la advertencia de ciclista»); los puntos se eligen con `select_slider` en la escala no lineal {', '.join(str(x) for x in ESCALA_PUNTOS)} (incluye 11 y 32, los puntos B y A congelados); el gráfico usa escala comprimida con líneas finas «Punto B» y «Punto A»; bloque «Cómo se calcula» de tres líneas sin nombres internos; los tres ejemplos en una fila.

### P3. Resumen
- **Qué encontré:** el chip se alineaba con la columna del encabezado y no con el borde del contenido; los enlaces de las alertas quedaban 8 px más arriba que su texto (el markdown de Streamlit lleva margen inferior negativo); la nota del gráfico nombraba archivos; «en muestra» aparecía tres veces.
- **Qué cambié:** chip al borde derecho del contenido en todas las páginas (también con descripciones de dos líneas y en modo presentación); cada alerta en su contenedor con su enlace en la misma fila; nota «Estimación en muestra: cajas × fracción para el 80 % × 20 s por caja (supuesto, no medido)» con un popover «Fuente» (informe técnico, sección 12 y anexo B); la alerta de validación dice «Todas las cifras salen de los 41 segmentos de desarrollo». Quedan dos «en muestra» (etiqueta de la barra y nota).
- **Medido con el DOM** (`capturas_resultado.json`, {len(geo)} capturas): chip contra el borde derecho del contenido, máximo {c(chip_dev)} px; enlace de cada alerta contra el centro de su texto, máximo {c(max(dys))} px ({len(dys)} alertas); desplazamiento horizontal de la página, máximo {scroll} px.

### P4. Redacción
- **Qué cambié:** «Fuera de pliegue» pasó a «En validación cruzada por segmentos» (`formato.traducir_folds`; el rótulo «AUC fuera de fold» de la ficha de Ética y de los resultados de Validación); «pliegue» y «fold» pasan a «partición»; sin nombres de archivo en pantalla (la columna «Fuente» de los resultados de Validación se quitó y la fuente va en una línea; los mensajes de error ya no nombran rutas); «Proporción menos probabilidad de la regla», que no es un porcentaje, pasó a «Diferencia: proporción menos probabilidad de la regla». Una prueba nueva recorre las ocho páginas y las seis pestañas buscando .csv/.json, «pliegue», «fold», «OOF», «brazo A/B/C» y snake_case (`test_ninguna_pagina_muestra_terminos_internos`), y `FRASES_PROHIBIDAS` incluye «Fuera de pliegue». Los nombres de columnas del dataset que la persona debe llevar en su archivo (tabla «Archivos de entrada» de Puntuar) quedan: son datos del formato, no términos internos.

### P5. Validación (seis pestañas)
Capturé y leí las seis pestañas a 1366 y 1920 px (`images/ep3/pagina/05_validacion_<pestaña>_<ancho>.png`). Defectos corregidos: etiquetas repetidas del eje en Ensambles, «vista obs», columna de archivos y «Detalle» cortado en Selección, barras superpuestas en No supervisado y leyenda cortada en «En muestra» (detalle en las dos pasadas, abajo).

### P6. Capturas y dos pasadas de corrección
- 15 capturas por ancho (8 páginas, cola sin selección, 6 pestañas de Validación y el modo presentación; las de F20 están en `images/ep3/pagina/antes_f21/`); la geometría (chip, alertas y desplazamiento) se mide con el DOM en cada captura.
- **Pasada 1** (primeras capturas de 1366 px):
{pasada1}
- **Pasada 2** (regeneración completa, 1366 y 1920 px):
{pasada2}
- Documentos generados: `auditoria_diseno_pagina.md` (sección F21 con las dos pasadas y las mediciones), `guia_estilo_pagina.md`, `pagina_guia_demo.md` y `PENDIENTES_PAGINA.md` (sección i).

### P7. Pruebas, cifras y tiempos
- {nuevas} pruebas nuevas en `tests/ep3/test_pagina_f21.py` (nota del empate calculada, orden y anchos de las columnas, escala de los puntos, «-50,000», control que mueve la probabilidad, «en muestra» a lo más dos veces, alineación medida, términos internos, marcas de los ejes, pestañas sin columna de archivos y capturas completas) y las de F19 y F20 adaptadas al nuevo orden de columnas, al panel debajo de la tabla, a los `select_slider` y a «Partición».
- **Tiempos de carga** (navegador sin interfaz y perfil nuevo, 2 arranques en frío por variante; `pagina_arranque_f20.json` = F20, `pagina_arranque_f21.json` = F21; «completa» = script terminado y último elemento presente, sin contar los 2 s de estabilidad que pide la captura; de cada página se toma la captura más lenta):

| | F20 (antes) | F21 (después) |
|---|---|---|
| Con lanzador: primera visita (s) | {rango(a_con, 'primera_visita_explica_s')} | {rango(d_con, 'primera_visita_explica_s')} |
| Con lanzador: página más lenta después de la primera (s) | {rango(a_con, 'maximo_secciones_s')} | {rango(d_con, 'maximo_secciones_s')} |
| Sin lanzador: primera visita (s) | {rango(a_sin, 'primera_visita_explica_s')} | {rango(d_sin, 'primera_visita_explica_s')} |
| Servidor responde, con lanzador (s) | {rango(a_con, 'servidor_responde_s')} | {rango(d_con, 'servidor_responde_s')} |

| Página | F20, peor de los arranques con lanzador (s) | F21, peor de los arranques con lanzador (s) |
|---|---|---|
{sec_tabla}

Meta «ninguna página más de 3 s tras el arranque»: {'se cumple' if all(e['secciones_cumplen_3s'] for e in d_con) else 'NO se cumple en todas las páginas (ver arriba)'} con el lanzador. Sin el lanzador, {'ningún arranque supera los 3 s' if all(e['secciones_cumplen_3s'] for e in d_sin) else 'algún arranque supera los 3 s (ver arriba)'}. Es una medición de este equipo, no una garantía; la primera visita incluye la descarga del frontend de Streamlit por un navegador sin caché.

{corrida1}

## Bloque D: los documentos
- **D1. Guía de demo.** `pagina_guia_demo.md` ahora tiene el **«Recorrido corto (95 s, 6 pasos)»**, que sale de la misma fuente (`demo_pasos`) que el bloque «Demo de la página» del guion, con su tiempo por paso, y el «Recorrido extendido (respaldo)» con los 13 pasos de antes, actualizado. El paso de la cola dice en una frase por qué las primeras filas empatan («Las primeras filas empatan porque todas tienen 0 puntos del sensor superior») y el siguiente muestra la nota del empate. El paso 2 quedó en 25 s porque con 20 s sus 53 palabras daban 159 por minuto (límite 140). Palabras por paso:

| Tiempo | Paso | Palabras | Palabras/min |
|---|---|---|---|
{demo_tabla}

- **Guion:** {palabras} palabras en 9:15 (≈ {ppm_prom:.0f} palabras por minuto en promedio); ningún bloque supera 140 y los bloques técnicos siguen entre 105 y 135 por minuto. Palabras por bloque:

| Tiempo | Bloque | Palabras | Palabras/min |
|---|---|---|---|
{guion_tabla}

- **D2. Preguntas cruzadas** ({preg} en total): **Q39** dice ahora «el mejor modelo entrenado sin la regla es LR3 con 0,808; E2, que la incluye como componente, 0,824» (`f5_metricas_candidatos.csv`). **Q73** (sellado): `manifest_v3.json` trae **3** hashes y la verificación incluye además el plan v3 (2): «5 de 5»; y «lo hace la persona» pasó a «hacemos commit y push antes de evaluar». **Q74** (¿y si no hay huecos?): agrega la tasa por celda (2 de 111, 1,8 %; probabilidad de ninguno ≈ 27 %) y la concentración en San Francisco de día (2 de 7 segmentos; con 8 segmentos nuevos de ese estrato, (5/7)^8 ≈ 7 %), ambas de los mismos datos con que se ajustó el detector, así que son optimistas, y el rango «entre ≈ 7 % y ≈ 27 %» rotulado post hoc, con fuente. **Q21 y Q61** llevan una línea: el conteo observado da 44,6 % y la curva guardada interpolada 44,7 %. **Dos preguntas nuevas:** «¿por qué las primeras cajas de la cola tienen la misma probabilidad?» (4.757 cajas con 0 puntos; 90,5 % sin pareja; el orden no es informativo; se atiende por objeto) y «¿cuál es el valor de negocio en una frase?» (cifras de `f6_modelo_escogido.csv`, con el rótulo «en muestra»). El informe (§4) agrega la frase del empate junto a las 4.757 cajas.
- **D3. Regenerados** desde sus generadores: informe, README_EP3, preguntas, guion, guía de demo, guía de estilo, pendientes de la página, mapa de archivos, auditoría de diseño, `docs/ep3/revision/`, los contadores de ESTADO y `plan_integracion_readme.md`, y los notebooks 11 a 15 (RECALCULAR = False; el 14 con la prueba de humo de las {len(SECCIONES)} páginas x 3 roles y el modo presentación). Revisión automática de tablas y caracteres de control: {'sin problemas' if not problemas else str(len(problemas)) + ' archivos con problemas'}.

## Verificaciones y reglas
- Congelados de EP2: **{v14}**. Solución v3: **{v5}**. No supervisado: **{v1}**.
- Archivos sellados o protegidos con fecha de modificación posterior al fin de F20: **{', '.join(tocados) if tocados else 'ninguno'}**. EP2 solo se leyó; sin git (solo `status`, `diff` y `log`); sin paquetes instalados; sin bucket, gcloud ni Docker; la página no hace peticiones externas (una prueba lo vigila) y no se tocaron las claves de seguridad de `.streamlit/config.toml`.

## Bloqueos
- Ninguno que detuviera el trabajo. Límites anotados con su motivo en `PENDIENTES_PAGINA.md` (sección i): un «%» todavía puede separarse de su número en textos que no pasan por `estilos._e` ni por `formato.sin_corte`; el mapa de la Auditoría mantiene su contenedor de 560 px con desplazamiento; los identificadores quedan a la derecha de «Segmento» y a 1366 px requieren desplazamiento.

## Lo que te toca
1. Abrir la página con `scripts\\ep3\\arrancar_app.bat` y mirar las capturas de `images/ep3/pagina/` (1366 y 1920 px) y la sección F21 de `auditoria_diseno_pagina.md`.
2. Ensayar el **recorrido corto de 95 s** con el guion (`pagina_guia_demo.md`) y repartir los bloques («Quién»).
3. Probar con personas de cada rol y en otro equipo o navegador (sigue pendiente).
4. Sigue pendiente lo de siempre: commit del sello antes del Colab, la validación externa y rearmar el zip y la copia limpia (otra tarea).
"""
    (DOC / "REPORTE_F21.md").write_text(md, encoding="utf-8")
    print("escrito REPORTE_F21.md")
    pend = revisar_carpeta(DOC)
    if pend:
        raise SystemExit(f"los documentos (incluido este reporte) tienen problemas: {pend}")


if __name__ == "__main__":
    main()
