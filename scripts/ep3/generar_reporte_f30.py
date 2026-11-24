"""F30: genera docs/ep3/REPORTE_F30.md (ajustes del Resumen y fin del modo presentación). Las cifras se leen de sus archivos de origen (nada se copia a mano):

- docs/ep3/f30_altura_bloque.json       altura del bloque «Alertas de cámara» y posición de «Cola de revisión» y sus filtros a 1366 x 768, antes y después (scripts/ep3/f30_medir_bloque.py)
- docs/ep3/f24_fold_resumen.json        primera pantalla del Resumen (scripts/ep3/f24_medir_resumen.py)
- docs/ep3/f25_barra_lateral.json       barra lateral a 1366 x 768 (scripts/ep3/f25_medir_barra.py)
- docs/ep3/f30_contraste.json           contraste real del texto (scripts/ep3/f24_auditar_contraste.py --salida docs/ep3/f30_contraste.json)
- docs/ep3/f25_ambar_en_el_dom.json     ámbar en el DOM de las 8 vistas
- docs/ep3/f29_navegacion.json          «Auditar» y «Abrir» en el navegador real (scripts/ep3/f29_navegacion.py)
- docs/ep3/f30_resultado_suite.json     resultado de la suite de EP3 (scripts/ep3/f30_registrar_suite.py)
- docs/ep3/f30_sello_despues.json       integridad del sello (scripts/ep3/f23_integridad_sello.py --comprobar --etiqueta f30)
- data/08_reporting_ep3/capturas_resultado.json   las capturas, su geometría y los errores de consola
- ``git status --short`` (solo lectura) y una búsqueda de «modo presentación» en el repositorio para las listas de archivos

Uso: .venv\\Scripts\\python scripts/ep3/generar_reporte_f30.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3 import app_logica as A  # noqa: E402

DOC = RAIZ / "docs/ep3"
SALIDA = DOC / "REPORTE_F30.md"
LIMITE_ANTERIOR = datetime.fromtimestamp((DOC / "f29_sello_despues.json").stat().st_mtime)      # lo modificado después del último sello de F29 es de F30
MODO = re.compile(r"modo[ _]presentaci[oó]n", re.I)


def cargar(ruta: Path) -> dict | list:
    return json.loads(ruta.read_text(encoding="utf-8"))


def coma(x: float | str, dec: int = 1) -> str:
    return (f"{x:.{dec}f}" if isinstance(x, (int, float)) else str(x)).replace(".", ",")


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def lista_archivos() -> str:
    """Archivos con cambios en git y modificados después de cerrar F29; las capturas y las copias de revisión se resumen por grupo (con lo borrado aparte)."""
    salida = subprocess.run(["git", "status", "--short", "-uall"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=False).stdout
    etiqueta = {"M": "modificado", "??": "nuevo", "D": "borrado", "A": "agregado"}
    sueltos: list[tuple[str, str]] = []
    grupos: dict[str, list[str]] = {}
    borradas: list[str] = []
    for linea in salida.splitlines():
        if not linea.strip():
            continue
        st, ruta = linea[:2].strip(), linea[3:].strip().strip('"')
        p = RAIZ / ruta
        if st == "D" and "presentacion" in ruta.lower():
            borradas.append(ruta)
            continue
        if st != "D" and (not p.exists() or datetime.fromtimestamp(p.stat().st_mtime) < LIMITE_ANTERIOR):
            continue
        if ruta.startswith("images/ep3/pagina/para_revision/"):
            grupos.setdefault("images/ep3/pagina/para_revision/ (los 17 archivos que se envían a revisión)", []).append(etiqueta.get(st, st))
        elif ruta.startswith("images/ep3/pagina/"):
            grupos.setdefault("images/ep3/pagina/ (capturas regeneradas con la barra lateral nueva y el bloque de alertas ajustado)", []).append(etiqueta.get(st, st))
        elif ruta.startswith("docs/ep3/revision/"):
            grupos.setdefault("docs/ep3/revision/ (copias de revisión de los documentos, regeneradas)", []).append(etiqueta.get(st, st))
        elif st != "D":
            sueltos.append((st, ruta))
    L = [f"- `{ruta}`: {etiqueta.get(st, st)}" for st, ruta in sorted(sueltos, key=lambda x: x[1])]
    L += [f"- {clave}: {len(v)} archivos ({', '.join(sorted(set(v)))})" for clave, v in grupos.items()]
    if borradas:
        L.append("- Capturas del modo presentación borradas: " + ", ".join(f"`{Path(b).name}`" for b in sorted(borradas)))
    return "\n".join(L)


def menciones_restantes() -> tuple[list[str], list[str]]:
    """Archivos que todavía dicen «modo presentación»: documentos y scripts (sin contar este reporte ni los de F30). Son historia: describen fases anteriores."""
    docs, scripts = [], []
    for p in sorted(DOC.glob("*.md")):
        if p.name in ("REPORTE_F30.md",):
            continue
        n = len(MODO.findall(p.read_text(encoding="utf-8")))
        if n:
            docs.append(f"`docs/ep3/{p.name}` ({n})")
    for p in sorted((RAIZ / "scripts/ep3").glob("*.py")):
        if "f30" in p.name or p.name == "armar_para_revision.py":
            continue
        n = len(MODO.findall(p.read_text(encoding="utf-8")))
        if n:
            scripts.append(f"`scripts/ep3/{p.name}` ({n})")
    return docs, scripts


def main() -> None:
    bl = cargar(DOC / "f30_altura_bloque.json")
    fold = cargar(DOC / "f24_fold_resumen.json")["normal"]
    con = cargar(DOC / "f30_contraste.json")
    amb = cargar(DOC / "f25_ambar_en_el_dom.json")
    barra = cargar(DOC / "f25_barra_lateral.json")[0]
    nav = cargar(DOC / "f29_navegacion.json")
    suite = cargar(DOC / "f30_resultado_suite.json")
    sello = cargar(DOC / "f30_sello_despues.json")
    caps = cargar(RAIZ / "data/08_reporting_ep3/capturas_resultado.json")
    d, res = suite["despues"], con["resumen"]
    a, z = bl["antes"], bl["despues"]
    geo = [c["geometria"] for c in caps if c.get("geometria")]
    errores = sum(len(c.get("errores_consola") or []) for c in caps)
    docs_hist, scripts_hist = menciones_restantes()
    falta_650 = z["filtros_terminan_en_px"] - 650
    md = f"""# Reporte de F30: ajustes del Resumen y fin del Modo presentación

*Generado por `scripts/ep3/generar_reporte_f30.py` desde sus archivos de origen. Decisiones: DEC-118 a DEC-121 en `ESTADO.md`. Sin commit: el usuario hace el commit. La referencia visual fue `f30_resumen_propuesto.html` y el prompt F30 que la acompañaba.*

**En una línea.** El bloque «Alertas de cámara» ahora mide lo que mide su contenido (de {a['alto_del_bloque_px']} a **{z['alto_del_bloque_px']} px**), sin el enlace «Abrir la auditoría de cámaras» y con el anillo arriba a la derecha; el pie del Resumen ya no lleva la línea de validación pendiente; el Modo presentación dejó de existir (interfaz, textos, código, pruebas, capturas y documentos vigentes); y «Impacto estimado» pasó a ser una sección fija de Validación › En muestra con las mismas cifras y los mismos textos. No cambió ningún modelo, cálculo ni cifra.

## 1. Pruebas, sello y verificaciones

- Pruebas de EP3 (`{suite['comando']}`): **antes {suite['antes']['pasaron']} aprobadas; después {d['pasaron']} aprobadas**, {d['fallaron']} falladas, {d['omitidas']} omitidas, {coma(d['duracion_s'])} s. Se agregaron {d['nuevas_f30']} pruebas en `tests/ep3/test_pagina_f30.py`; las pruebas de cifras (`test_las_cifras_no_cambian_salvo_el_redondeo_unificado`, `test_las_horas_de_inicio_son_132_y_358…`, la regresión contra `pagina_numeros_antes.json`) siguen y pasan.
- Sello de la validación externa: **{'intacto' if sello['intacto'] else 'CAMBIÓ'}** (`f30_sello_despues.json`: {sello['archivos_comparados']} archivos comparados; cambiados {len(sello['cambiados'])}). Congelados de EP2 (14 de 14) y de v3 (5 de 5): ver el cierre de `ESTADO.md`.
- Contraste real: {miles(res['textos_medidos'])} textos en {res['vistas']} vistas, **{res['textos_por_debajo']} por debajo de 4,5:1** (mínimo {coma(res['razon_minima_dom'], 2)} en el DOM y {coma(res['razon_minima_en_pixeles'], 2)} en los píxeles; `f30_contraste.json`).
- Ámbar `#F5B73B` en el DOM de las 8 vistas: {len(amb['ambar'])} elemento(s) (solo el punto de advertencia de ciclistas, que aparece cuando una fila de la cola es de ciclista).
- Navegación real: «Auditar» abrió la Auditoría con «{nav['auditar_0']['celda']}»; «Abrir» abrió «Explica una caja» con «{nav['abrir_0']['caja'][:60]}…». Resultado: {nav['conclusion']}.
- Capturas: {sum(1 for c in caps if c['listo'])} de {len(caps)} completas (a 1366 y a 1920 px), {errores} errores de consola, desplazamiento horizontal máximo {max(g['scroll_horizontal_px'] for g in geo)} px. Barra lateral a 1366 × 768: desborde {barra['desborde_px']} px y el selector «Rol» a {barra['rol']['abajo']} px de 768 (visible: {'sí' if barra['rol_visible'] else 'NO'}).

## 2. Altura del bloque «Alertas de cámara» (1366 × 768, medida con Chrome sin interfaz)

| Medida | Antes (F29) | Después (F30) | Diferencia |
|---|---|---|---|
| Alto del bloque | {a['alto_del_bloque_px']} px | {z['alto_del_bloque_px']} px | {z['alto_del_bloque_px'] - a['alto_del_bloque_px']} px |
| Título «Cola de revisión» termina en | {a['titulo_de_la_cola_termina_en_px']} px | {z['titulo_de_la_cola_termina_en_px']} px | {z['titulo_de_la_cola_termina_en_px'] - a['titulo_de_la_cola_termina_en_px']} px |
| Filtros de la cola terminan en | {a['filtros_terminan_en_px']} px | {z['filtros_terminan_en_px']} px | {bl['diferencia_filtros_terminan_en_px']} px |
| Título y filtros visibles en una ventana de 768 px | {'sí' if a['titulo_y_filtros_visibles_en_768'] else 'no'} | **{'sí' if z['titulo_y_filtros_visibles_en_768'] else 'no'}** | |
| Título y filtros visibles en 650 px (alto útil típico de un navegador real) | {'sí' if a['titulo_y_filtros_visibles_en_650'] else 'no'} | {'sí' if z['titulo_y_filtros_visibles_en_650'] else 'no'} | |

**Meta cumplida a 1366 × 768:** el título «Cola de revisión» y sus filtros se ven sin hacer scroll (los filtros terminan en {z['filtros_terminan_en_px']} px de 768). **Si el navegador solo ofrece unos 650 px útiles (barras y pestañas incluidas), faltan {falta_650} px**: los filtros quedarían justo bajo el borde. No lo cerré porque habría que tocar los indicadores (que el prompt dijo que no se tocaran) o apretar el espacio entre secciones hasta que se vea amontonado.

Cómo se logró: se quitó la cabecera aparte del bloque (que tenía el enlace y empujaba todo hacia abajo), se pasó a dos columnas independientes (izquierda: rótulo, titular, subtítulo y filas; derecha: rótulo del anillo, anillo de {z['tamano_del_anillo_px']} px y leyenda, alineados arriba: el rótulo del anillo empieza a {z['rotulo_del_anillo']['arriba'] - z['panel']['arriba']} px del borde superior del bloque) y se redujo el relleno del recuadro de `1.3rem 1.5rem 24px` a `1rem 1.4rem 1rem`. El recuadro ya no tiene el hueco bajo las filas: mide lo que mide su columna más alta (hoy la del anillo). Con 5 alertas crece la columna izquierda y el anillo sigue arriba.

## 3. Qué se hizo, punto por punto

**A) Bloque «Alertas de cámara».** (1) Se quitó el enlace «Abrir la auditoría de cámaras» y su constante `ENLACE_AUDITORIA`; cada fila conserva «Auditar» y la Auditoría sigue en el menú. (2) Recuadro ajustado y anillo arriba, como arriba. (3) Los cuatro indicadores no se tocaron. (4) Medición antes/después en la sección 2 (`scripts/ep3/f30_medir_bloque.py`, `f30_altura_bloque.json`; el «antes» se guardó con el código de F29 y antes de cambiar nada).

**B) Pie del Resumen.** (5) Se quitó solo la línea «Validación externa pendiente · las cifras salen de segmentos de desarrollo» con su enlace «Ver en Validación» (la función `_pie_resumen`, `E.estado_validacion`, el CSS `.aud-estado`/`.aud-punto.neutro` y las constantes `ESTADO_VALIDACION`/`ENLACE_VALIDACION`). Quedan la atribución de Waymo y «Solución v3 congelada el 2026-11-14. Datos de desarrollo, 41 segmentos.». Decisión registrada como DEC-119 en `ESTADO.md`: la divulgación de rigor sigue en Ética y límites, Validación, Ayuda y el pie global.

**C) Modo presentación fuera.** (6) Se quitó el interruptor y su ayuda de `app/app.py`; la barra lateral solo tiene «Rol». (7) Se eliminó todo lo que dependía del modo: la letra agrandada (`PRESENTACION` y el parámetro de `E.css`, el token `1.18`), la numeración de identificadores («Segmento 25», `#001`), el ocultamiento de identificadores (`ocultar_identificadores` e `IDENTIFICADORES`; los parámetros `presentacion` de `tabla_cola`, `tabla_por_objeto` y `E.metricas`), el `ocultar` de las descargas de «Puntuar datos nuevos», el texto «(oculto)» del segmento de ejemplo, la clave `presentacion` de `ctx` y de `session_state`, y las variantes de pantallas anchas del CSS (`.aud-metricas.pres`). Se buscaron «modo presentación», «modo_presentacion» y «presentacion» en `app/`, `src/`, `tests/`, `scripts/` y `docs/`; lo que queda está en la sección 5. (8) «Impacto estimado» (horas con y sin cola, su nota y el menú «Fuente») pasó, con las mismas cifras y los mismos textos, a una sección fija de **Validación › En muestra, debajo del gráfico** (`_impacto_estimado` en `app/secciones.py`). (9) Textos corregidos: Ética y límites («Las tablas locales tienen identificadores de objeto y marcas de tiempo. Nada se guarda ni se envía.», en las dos variantes de `EP3_ENTORNO`); Ayuda y glosario (se quitó la viñeta del modo y la del rol dice «cambia la página que se abre»); y los documentos vigentes que lo mencionaban (README_EP3, informe, guion, preguntas cruzadas, guía de demo, guía de estilo, mapa de archivos, pendientes y `despliegue.md`, a mano). (10) Pruebas adaptadas o quitadas sin tocar las de cifras (sección 4).

**D) Capturas y reporte.** (11) Se regeneraron todas las capturas (a 1366 y a 1920 px; la barra lateral cambió en todas), se quitó de `capturar_pagina.py` el paso del modo presentación y se borraron las capturas de ese modo. (12) La carpeta `images/ep3/pagina/para_revision/` se armó con `scripts/ep3/armar_para_revision.py` (la vacía antes de copiar): 16 capturas a 1366 px, una por página, más este reporte, 17 archivos en total. (13) Este reporte.

## 4. Pruebas: qué se quitó, qué se adaptó y qué se agregó

- **Quitadas** (verificaban el modo): `test_modo_presentacion_oculta_identificadores` (test_app) y `test_modo_presentacion_oculta_identificadores_en_la_cola` (rediseño; la parte que sigue valiendo, que la tabla de la página no lleva identificadores y el CSV sí, quedó como `test_la_tabla_de_la_cola_de_la_pagina_no_lleva_identificadores_pero_el_csv_si`), y `test_el_impacto_estimado_solo_se_muestra_con_el_modo_presentacion_y_trae_su_fuente` (F29, reemplazada por pruebas de F30).
- **Adaptadas:** la prueba de humo de 8 páginas × 3 roles ya no parametriza el modo (ni en test_app ni en rediseño); `test_el_css_cumple_el_sistema_visual…` (sin `.pres` ni `1.18`); la tira de cifras sin variante de presentación; el detalle de la cola siempre con segmento; `tabla_cola` y `tabla_por_objeto` sin el parámetro; el padding del panel (`1rem 1.4rem 1rem 1.4rem`); la barra lateral (selector de rol visible en lugar del interruptor); el cabe-en-640 px (solo modo normal); y las pruebas de capturas (14 por ancho en lugar de 15, sin capturas del modo). Las pruebas que buscaban las horas (358, 200 y 132 h) o las barras de colores de los flujos ahora las buscan en Validación.
- **Agregadas** (`test_pagina_f30.py`, {d['nuevas_f30']}): el modo no deja rastro en `app/`, `src/` ni en las capturas y scripts; la barra lateral solo tiene «Rol» y `session_state` no guarda estado del modo en ninguna de las 8 páginas; los identificadores siempre están en los datos descargables; Ética y Ayuda corregidas (incluidas las dos variantes de `EP3_ENTORNO`); Impacto estimado una sola vez, en Validación › En muestra, con su «Fuente» y debajo del gráfico; el Resumen sin el enlace de la Auditoría ni la línea de validación; anillo en la columna derecha con su rótulo encima; tamaño del anillo entre 240 y 260 px; medidas antes/después con la meta; y la carpeta `para_revision` con exactamente los 17 archivos.

## 5. Decisiones distintas del prompt (y por qué)

1. **Se mantuvieron el enlace «Abrir la cola completa» y los tres filtros de la cola.** El HTML de referencia no los dibuja, pero el prompt pedía que el título de la cola «y sus filtros» se vieran en la primera pantalla, y el enlace no estaba en la lista de lo que se quita.
2. **La opción `--ocultar-ids` de `scripts/ep3/puntuar_segmento.py` se conserva** (es una opción de línea de comandos del script, no del modo de la página); solo se corrigió su ayuda, que decía «modo presentacion».
3. **Los documentos y scripts históricos siguen diciendo «modo presentación»** porque cuentan lo que era cierto en su fase y el prompt pedía tocar solo lo vigente. Quedan ({len(docs_hist)} documentos): {', '.join(docs_hist) if docs_hist else 'ninguno'}. Y en scripts ({len(scripts_hist)}): {', '.join(scripts_hist) if scripts_hist else 'ninguno'}. En los generadores de reportes de F18 a F29 es texto de esos reportes; `ESTADO.md` conserva las decisiones antiguas (DEC-xx) tal como se escribieron.
4. **No se regeneró el cuaderno 14** (su prueba de humo todavía recorre el modo). Se corrigió su generador, `scripts/ep3/crear_notebooks_ep3.py`, para cuando se vuelva a generar; ejecutar notebooks está fuera de lo permitido en esta tarea.
5. **No se reempaquetó `entrega_EP3.zip` ni `artefactos_ep3/`.** Se corrigió el texto del paso a paso que `scripts/ep3/empaquetar_entrega_ep3.py` escribe en el zip (decía «active “Modo presentación”»), pero el zip ya generado conserva el texto anterior hasta que se vuelva a empaquetar.
6. **El tamaño del anillo es 240 px** (el HTML usa 236 y el prompt pedía de 240 a 260): el valor más bajo del rango, para que el bloque sea lo más bajo posible sin perder legibilidad.
7. **La meta de «sin scroll» se cumple a 768 px, no a 650 px** (sección 2).
8. **`verificacion_copia_limpia.md` no se tocó:** es el registro de una verificación hecha en una copia limpia en su momento (48 combinaciones con el modo) y no se vuelve a ejecutar aquí.

## 6. Lo que no se pudo hacer o queda pendiente

- Los {falta_650} px que faltan para ver los filtros en un navegador de 650 px útiles (sección 2).
- Probar el Resumen con cientos o miles de segmentos: el diseño limita la lista de alertas a {A.FILAS_ALERTAS_RESUMEN} filas (avisa cuántas más hay), pero solo se vio con 2 alertas.
- Regenerar el cuaderno 14 y reempaquetar la entrega (puntos 4 y 5 de la sección anterior).
- Los generadores `generar_reporte_f26.py`, `generar_reporte_f27.py` y `generar_reporte_f29.py` citan constantes y estructuras que cambiaron: no se pueden volver a ejecutar sin adaptarlos (sus reportes quedan como están).
- Las capturas de 1920 px se regeneraron pero no se enviaron a revisión (la carpeta pedida es solo de 1366).

## 7. Archivos modificados

Archivos con cambios en git y modificados después de cerrar F29 (los documentos generados salen de sus generadores):

{lista_archivos()}
"""
    SALIDA.write_text(md, encoding="utf-8")
    print(f"escrito {SALIDA.relative_to(RAIZ)} ({len(md)} caracteres)")


if __name__ == "__main__":
    main()
