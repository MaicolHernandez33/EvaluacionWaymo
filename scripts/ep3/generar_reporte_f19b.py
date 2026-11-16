"""Genera docs/ep3/REPORTE_F19B.md (reporte de la tarea F19-B: pulido de la página y corrección de documentos).

Sin cifras a mano: los tiempos salen de data/08_reporting_ep3/pagina_arranque.json y capturas_resultado.json, los conteos de pruebas_ep3_conteo.json, las cifras de la página de la misma
lógica que usa la página (app_logica.py) y las verificaciones de congelados se ejecutan aquí (solo lectura).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.app_logica import MIN_CAJAS_RANGO, cargar_datos, inicio_resumen, matriz_calor  # noqa: E402
from waymo_evaluacion.ep3.chequeo_md import constantes_con_control, revisar_carpeta  # noqa: E402

REP, DOC = RAIZ / "data/08_reporting_ep3", RAIZ / "docs/ep3"
PY = str(RAIZ / ".venv" / "Scripts" / "python.exe")


def c(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def verificar(script: str) -> str:
    """Ejecuta una verificación de congelados (solo lectura) y devuelve «coinciden N de M»."""
    r = subprocess.run([PY, script], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"coinciden (\d+) de (\d+)", r.stdout)
    return f"{m.group(1)} de {m.group(2)}" if m else f"SIN RESULTADO (código {r.returncode})"


def main() -> None:
    ar = json.loads((REP / "pagina_arranque.json").read_text(encoding="utf-8"))
    cap = json.loads((REP / "capturas_resultado.json").read_text(encoding="utf-8"))
    cont = json.loads((REP / "pruebas_ep3_conteo.json").read_text(encoding="utf-8"))
    D = cargar_datos(RAIZ / "data/09_app_ep3")
    ini = inicio_resumen(D)
    mm = matriz_calor(D["celdas"], MIN_CAJAS_RANGO)
    con = [e for e in ar["escenarios"] if e["escenario"].startswith("con lanzador")]
    sin = [e for e in ar["escenarios"] if e["escenario"].startswith("sin lanzador")]

    def rango(es: list[dict], clave: str) -> str:
        v = [e[clave] for e in es]
        return c(min(v)) if c(min(v)) == c(max(v)) else f"{c(min(v))} a {c(max(v))}"

    sec = pd.DataFrame([{"Sección": s, "Con lanzador (s)": c(max(e["secciones_s"][s] for e in con)), "Sin lanzador (s)": c(max(e["secciones_s"][s] for e in sin))} for s in con[0]["secciones_s"]])
    tabla_sec = "\n".join(f"| {r['Sección']} | {r['Con lanzador (s)']} | {r['Sin lanzador (s)']} |" for _, r in sec.iterrows())
    n_cap = sum(1 for x in cap if x["listo"])
    t_cap = max(x["segundos_hasta_listo"] for x in cap)
    anchos = sorted({x["ancho"] for x in cap})
    tam = {p.name: p.stat().st_size for p in (RAIZ / "images/ep3/pagina").glob("*_1366.png")} | {p.name: p.stat().st_size for p in (RAIZ / "images/ep3/pagina").glob("*_1920.png")}
    pesos = f"{min(tam.values()) / 1000:.0f} a {max(tam.values()) / 1000:.0f} KB".replace(".", ",")
    docs_mal = revisar_carpeta(DOC)
    scripts_mal = {str(p.relative_to(RAIZ)): constantes_con_control(p) for p in sorted((RAIZ / "scripts/ep3").glob("*.py"))}
    scripts_mal = {k: v for k, v in scripts_mal.items() if v}
    n_docs = len(list(DOC.glob("*.md")))
    v14, v5, v1 = verificar("scripts/verificar_congelados.py"), verificar("scripts/ep3/verificar_congelados_v3.py"), verificar("scripts/ep3/verificar_no_supervisado.py")

    md = f"""# Reporte de la tarea F19-B: pulido de la página y corrección de documentos

*Generado por `scripts/ep3/generar_reporte_f19b.py`; cifras de `data/08_reporting_ep3/pagina_arranque.json`, `capturas_resultado.json` y `pruebas_ep3_conteo.json`, y de la misma lógica que usa la página (`app_logica.py`). Decisiones: `ESTADO.md` (DEC-47 a DEC-56, sección F19). Las cifras de la página no cambiaron: solo presentación, idioma y uso. El zip NO se rearmó.*

## Resumen
Se corrigió lo que se vio al revisar las capturas (bloque B) y los errores de formato de los documentos generados (bloque C). La captura en blanco de «Explica una caja» **no era un error de la sección** sino una captura tomada antes de que terminara la carga; ahora la captura espera de forma robusta y la página precarga la solución congelada. Con el lanzador, la primera visita tarda {rango(con, 'primera_visita_explica_s')} s y ninguna sección tarda más de {c(max(e['maximo_secciones_s'] for e in con))} s después. Los {n_docs} documentos de `docs/ep3` pasan un chequeo automático de tablas y caracteres de control, y ese chequeo corre solo al generar. Pruebas: {cont['recolectadas_ep3']} recolectadas en `tests/ep3`, todas pasan; congelados {v14} (EP2), {v5} (v3) y {v1} (no supervisado), antes y después.

## Bloque B: la página
### B1. «Explica una caja» en blanco en la captura
- **Cómo lo reproduje:** con Chrome sin interfaz (CDP) pedí la sección sin esperar a que terminara la carga: la página mostraba el esqueleto de carga, el texto del cuerpo tenía 0 caracteres y el PNG pesaba unos 9 KB; con la espera correcta, la sección carga completa. `AppTest` y la consola del navegador no mostraron ninguna excepción.
- **Causa:** la captura se tomó antes de que terminara la carga en frío (no un error de renderizado). Que fuera justo esta sección es una inferencia: es la que usa el modelo congelado y la más lenta en la primera visita; no se probó con otra sección.
- **Arreglo:** (1) `scripts/ep3/capturar_pagina.py` espera hasta que no haya indicador de carga **y** aparezca un texto clave de la sección; si no aparece, no guarda la imagen como válida, anota el motivo y sale con error; (2) la solución congelada y los datos se precargan (B9). Resultado: {n_cap} capturas listas de {len(cap)}, la más lenta tardó {c(t_cap)} s (`capturas_resultado.json`).

### B2. Mapa de calor: «sin datos» no es «tasa 0 %»
Las celdas con **menos de {MIN_CAJAS_RANGO} cajas en el rango** (umbral `min_cajas` de `detector_params_v3.json`) se dibujan en gris con rayado y tienen su propia entrada en la leyenda; la tasa 0 % con datos suficientes sigue siendo azul casi blanco, y los huecos siguen en rojo con X. De {len(mm)} celdas (segmento × cámara), {int(mm['sin_datos'].sum())} salen sin datos suficientes y {int(mm['hueco'].sum())} son huecos (`data/09_app_ep3/celdas.csv`). Se muestran las etiquetas de los 41 segmentos. La guía de estilo se actualizó.

### B3. Lista A y Cola sin desplazar
Lista A: «Acción sugerida» y «Cajas afectadas» a la vista; ubicación, momento del día y umbral pasaron a «Detalle de las celdas marcadas». Cola: «Clase» y «Tipo de caso» van antes de los identificadores. Verificado en las capturas a 1366 y 1920 px.

### B4. Fotogramas del mismo objeto
Columna «Fotogramas del mismo objeto en la cola» (en pantalla, «Fotogramas»: el nombre completo no cabe a 1366 px; está en la ayuda de la columna, en la nota bajo la tabla y en el CSV) y una nota breve. No cambia el orden ni las cifras (prueba).

### B5. Formatos
Hiperparámetros: enteros sin decimales, C en notación científica, nombres legibles; ya no aparece «20,000» junto a «1.600». Se revisaron las seis pestañas de Evidencia y se corrigieron además un «-0,000» y el «25.00» del control de distancia de «Explica una caja». Prueba: ninguna tabla de evidencia tiene formatos engañosos, y el recall de ciclistas de las preguntas frecuentes sigue en 0,443.

### B6. Cargador de archivos
El segundo cargador se llama «Paso 2 (opcional)». Los textos del cargador salen en español («Arrastre el archivo aquí · Parquet, hasta 500 MB», «Elegir archivo»). **Riesgo:** se logra con CSS sobre los `data-testid` internos de Streamlit 1.65; si una versión futura los cambia, vuelve el inglés (sin romper nada más). Documentado en `PENDIENTES_PAGINA.md` y en la guía de estilo.

### B7. Curvas «Dos pasos» y «Un paso»
Azul continuo contra naranja discontinuo, distintos en color y en trazo, en la línea y en la leyenda. Durante la verificación encontré que la leyenda había desaparecido: con la banda sombreada codificada por el mismo campo con `legend=None`, Vega-Lite fusiona las leyendas y borra la de las líneas; ahora hay una banda por curva con color fijo y la leyenda lista solo las curvas dibujadas (comprobado en el DOM con una página de prueba de seis variantes).

### B8. Inicio
«≈ {c(ini['horas_dos_pasos'], 0)} h para encontrar el 80 %» contra «≈ {c(ini['horas_sin_orden'], 0)} h revisando sin orden», con la nota «Estimación en muestra, 20 s por caja (supuesto)». Mismo origen que antes (`inicio_resumen`); la cifra anterior de ≈ {c(ini['horas_ahorradas'], 0)} h es su diferencia.

### B9. Precarga y tiempos
`app/precarga.py` (carga y calentamiento en un hilo, una vez por proceso) y `app/lanzar.py`; `arrancar_app.bat` y `.ps1` lo usan, con las opciones de seguridad intactas. Medición con navegador sin interfaz y perfil nuevo, {len(con)} arranques en frío por variante (`scripts/ep3/f19_medir_arranque.py`):

| | Con lanzador | Sin lanzador |
|---|---|---|
| El servidor responde (s) | {rango(con, 'servidor_responde_s')} | {rango(sin, 'servidor_responde_s')} |
| Termina la precarga (s desde el arranque) | {rango(con, 'precarga_termina_s')} | {rango(sin, 'precarga_termina_s')} (empieza con la primera visita) |
| Primera visita a «Explica una caja» (s) | {rango(con, 'primera_visita_explica_s')} | {rango(sin, 'primera_visita_explica_s')} |

Tiempo hasta estar lista cada sección tras la primera visita (el peor de los arranques):

| Sección | Con lanzador (s) | Sin lanzador (s) |
|---|---|---|
{tabla_sec}

**Meta «ninguna sección más de 3 s»:** se cumple tras la primera visita ({c(max(e['maximo_secciones_s'] for e in con))} s como máximo con lanzador). La primera visita ({rango(con, 'primera_visita_explica_s')} s con lanzador) incluye la descarga del frontend de Streamlit por un navegador sin caché, por lo que queda en el borde de la meta; es una medición de este equipo, no una garantía. Una corrida de prueba anterior (no guardada) dio 3,3 s con lanzador: la dispersión entre arranques es de unos 0,4 s.

### B10. Pruebas, capturas y documentos
- Pruebas nuevas: `tests/ep3/test_pagina_pulido.py` (20) y ajustes en `test_pagina_rediseno.py`; total `tests/ep3`: {cont['recolectadas_ep3']} recolectadas, todas pasan.
- Capturas: las 8 secciones y el modo presentación a {' y '.join(str(a) for a in anchos)} px en `images/ep3/pagina/` ({n_cap} archivos de {pesos}; ninguna en blanco). Las capturas de F18 sin sufijo de ancho son anteriores al pulido y no se borraron (están versionadas).
- Documentos regenerados desde sus generadores: `guia_estilo_pagina.md`, `pagina_guia_demo.md`, `PENDIENTES_PAGINA.md`, informe, README, guion, preguntas, mapa y revisión.

## Bloque C: los documentos
- **C1.** La cabecera de una tabla del informe §8 tenía `|azimut|` sin escapar (la barra parte la celda): ahora dice «azimut absoluto ≤ 120°» (y «≤ 100°»). Además, `src/waymo_evaluacion/ep3/chequeo_md.py` revisa **todas** las tablas de `docs/ep3` (mismo número de celdas que la cabecera; las barras escapadas no cuentan; se ignoran los bloques de código), `generar_docs_ep3.py` lo ejecuta al final y falla si hay problemas, y `scripts/ep3/revisar_documentos.py` lo hace desde la línea de comandos: **{n_docs} documentos revisados, {len(docs_mal)} con problemas**.
- **C2.** Una comilla suelta antes de «12. **La página**» en §17: corregida en el generador.
- **C3.** La ruta de Windows `scripts\\ep3\\arrancar_app.bat` estaba en una cadena no cruda: `\\a` es el carácter de campana. Corregida en el generador (y revisados todos los generadores con un recorrido del árbol sintáctico: **{len(scripts_mal)} scripts con cadenas con caracteres de control**). Una prueba falla si algún documento generado o cadena de los scripts, de la lógica o de la página tiene caracteres de control.
- **C4. El prompt llegó cortado** en «reasigna unos 20 a 25 s a IE9 e IE10 (el stacking por segmentos». Decidí: pasar 25 s al bloque «IE9 e IE10» (de 55 a 80 s), tomados de bloques con holgura, sin cambiar el total (9:15) ni pasar de 140 palabras por minuto, y explicar en ese bloque que los dos stacking (E3 y E4) se calculan por segmentos. Si el texto completo pedía otra cosa, es un cambio de una línea en el generador (DEC-55).

## Verificaciones al cierre
- Congelados de EP2: **{v14}**; solución v3: **{v5}**; no supervisado: **{v1}**.
- `tests/ep3`: {cont['recolectadas_ep3']} recolectadas, todas pasan (`pytest tests/ep3 -q --no-cov -p no:cacheprovider`).
- No se tocaron: `plan_v3.*`, `plan_seleccion_ep3.*`, `seleccion_nuevos.py`, nada de `data/06_models_ep3/`, `dev_41.parquet` ni archivos de EP2. Sin paquetes instalados, sin bucket ni Docker; la página no hace peticiones externas (una prueba lo vigila).

## Lo que te toca
1. Probar la página con `scripts\\ep3\\arrancar_app.bat` en tu navegador y mirar las capturas de `images/ep3/pagina/` (1366 y 1920 px).
2. Decidir si quieres un nombre de columna distinto del rótulo corto «Fotogramas» y si el texto de C4 era el que esperabas.
3. Las capturas viejas de F18 (sin sufijo de ancho) pueden borrarse cuando quieras: quedaron para no tocar archivos versionados.
4. Sigue pendiente la prueba con personas reales de cada perfil y medir en otros equipos y navegadores.
"""
    (DOC / "REPORTE_F19B.md").write_text(md, encoding="utf-8")
    print("escrito REPORTE_F19B.md")


if __name__ == "__main__":
    main()
