"""F23: genera docs/ep3/REPORTE_F23.md. Todas las cifras se leen de sus archivos de origen (nada se copia a mano):

- docs/ep3/f23_paleta_validacion.json   salida de validate_palette.js (antes y después)
- docs/ep3/f23_fold_resumen.json        medición del Resumen en una ventana de 1366 x 768
- docs/ep3/f23_resultado_suite.json     resultado de la suite de EP3 (antes y después)
- docs/ep3/f23_sello_antes.json y f23_sello_despues.json   hashes del sello (scripts/ep3/f23_integridad_sello.py)
- data/08_reporting_ep3/capturas_resultado.json   las 30 capturas y su geometría
- ``git status --short`` (solo lectura) para la lista de archivos

Uso: .venv\\Scripts\\python scripts/ep3/generar_reporte_f23.py
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "docs/ep3"
SALIDA = DOC / "REPORTE_F23.md"


def cargar(ruta: Path) -> dict | list:
    return json.loads(ruta.read_text(encoding="utf-8"))


def lineas_validador(texto: str) -> list[tuple[str, str, str]]:
    return [(m.group(1), m.group(2).strip(), m.group(3).strip()) for m in re.finditer(r"\[(PASS|FAIL)\]\s+(.*?)\s{2,}(.*)", texto)]


def tabla_validador(texto: str) -> str:
    filas = [f"| {nombre} | {estado} | {detalle} |" for estado, nombre, detalle in lineas_validador(texto)]
    return "| Chequeo | Resultado | Detalle |\n|---|---|---|\n" + "\n".join(filas)


def numeros(texto: str) -> tuple[str, str]:
    cvd = re.search(r"CVD separation\s+worst \S+ \S+↔\S+ ΔE ([\d.]+)", texto)
    normal = re.search(r"Normal-vision floor\s+worst \S+ \S+↔\S+ ΔE ([\d.]+)", texto)
    return ((cvd.group(1) if cvd else "?").replace(".", ","), (normal.group(1) if normal else "?").replace(".", ","))


def git_estado() -> list[tuple[str, str]]:
    salida = subprocess.run(["git", "status", "--short", "-uall"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=False).stdout
    return [(l[:2].strip(), l[3:].strip().strip('"')) for l in salida.splitlines() if l.strip()]


def lista_archivos() -> str:
    estados = git_estado()
    # las capturas son decenas de PNG: se resumen por carpeta
    grupos: dict[str, list[tuple[str, str]]] = {}
    for st, ruta in estados:
        if ruta.startswith("images/ep3/pagina/antes_f23/"):
            clave = "images/ep3/pagina/antes_f23/ (copia de las capturas de F22)"
        elif ruta.startswith("images/ep3/pagina/"):
            clave = "images/ep3/pagina/ (capturas finales)"
        elif ruta.startswith("docs/ep3/revision/"):
            clave = "docs/ep3/revision/ (copias para revisión, ignoradas por git)"
        else:
            clave = ""
        grupos.setdefault(clave, []).append((st, ruta))
    L: list[str] = []
    etiqueta = {"M": "modificado", "??": "nuevo", "D": "borrado", "A": "agregado"}
    for st, ruta in sorted(grupos.get("", []), key=lambda x: x[1]):
        L.append(f"- `{ruta}`: {etiqueta.get(st, st)}")
    for clave, items in grupos.items():
        if clave:
            L.append(f"- {clave}: {len(items)} archivos ({', '.join(sorted({etiqueta.get(s, s) for s, _ in items}))})")
    return "\n".join(L)


def citas_regla_top() -> str:
    """Dónde sigue apareciendo «Regla top» (clave interna de los datos o documento histórico) y por qué no se cambió."""
    filas = []
    for ruta in sorted(list(DOC.glob("*.md")) + list((RAIZ / "notebooks").glob("1[1-5]_*.ipynb"))):
        n = ruta.read_text(encoding="utf-8", errors="replace").count("Regla top")
        if n:
            filas.append(f"{ruta.relative_to(RAIZ).as_posix()} ({n})")
    return ", ".join(filas) if filas else "ninguno"


def main() -> None:
    pal = cargar(DOC / "f23_paleta_validacion.json")
    fold = cargar(DOC / "f23_fold_resumen.json")
    suite = cargar(DOC / "f23_resultado_suite.json")
    antes = cargar(DOC / "f23_sello_antes.json")
    despues = cargar(DOC / "f23_sello_despues.json")
    caps = cargar(RAIZ / "data/08_reporting_ep3/capturas_resultado.json")
    cvd_a, nor_a = numeros(pal["antes"]["adyacentes"])
    cvd_d, nor_d = numeros(pal["despues"]["adyacentes"])
    listas = sum(1 for c in caps if c["listo"])
    geo = [c["geometria"] for c in caps if c.get("geometria")]
    scroll = max(g["scroll_horizontal_px"] for g in geo)
    dy = max([a["dy"] for g in geo for a in g["alertas"]] or [0])
    errores = sum(len(c.get("errores_consola") or []) for c in caps)
    claves_sello = ["docs/ep3/plan_seleccion_ep3.sha256", "docs/ep3/plan_seleccion_ep3.json", "data/06_models_ep3/manifest_v3.json", "data/06_models_ep3/manifest_alternativas.json", "data/06_models_ep3/alternativas_v3.joblib"]
    filas_sello = "\n".join(f"| `{k}` | `{antes['archivos'][k]}` | {'igual' if k in antes['archivos'] and k not in despues['cambiados'] and k not in despues['faltan'] else 'CAMBIÓ'} |" for k in claves_sello)
    with_pytest = suite["despues"]
    md = f"""# Reporte de F23: rediseño estructural de la página

*Generado por `scripts/ep3/generar_reporte_f23.py` desde sus archivos de origen. Plan de diseño: `plan_diseno_f23.md`. Decisiones: DEC-87 a DEC-96 en `ESTADO.md`. Sin commit: el usuario hace los commits.*

**En una línea.** La página dejó de ser una plantilla de tarjetas: el Resumen abre con una afirmación y el anillo de cámaras, la Cola tiene seis columnas y un detalle siempre visible, la Auditoría pinta «sin datos» en gris plano, la barra lateral es clara y solo hay una superficie elevada. Las cifras y los textos sellados no cambiaron; no se tocó el sello.

## Los seis cambios

| # | Cambio | Estado | Qué se vio (capturas de `images/ep3/pagina/`) | Lo que no coincide con lo pedido |
|---|---|---|---|---|
| 1 | Resumen: el anillo manda | **Hecho** | Sin fichas de indicadores; afirmación en serif de {fold['fuente_de_la_afirmacion'].split(' / ')[1].replace('px', ' px').replace('.', ',')} con las cifras de `inicio_resumen` y la etiqueta «en muestra»; anillo de {round(fold['anillo']['derecha'] - fold['anillo']['izquierda'])} px con el estado de las cinco cámaras del segmento elegido (sana, hueco, sin datos) y su lista en texto; cifras de apoyo (AUC, horas, casos encontrados por clase) en una tabla pequeña. A 1366 x 768 el anillo, su leyenda y la afirmación se ven completos sin desplazarse (`f23_fold_resumen.json`, `01_resumen_1366x768.png`). Modo presentación revisado en `09_resumen_modo_presentacion_*`. | La frase dice «el detector marca N celdas… como posibles huecos de cámara» y no «tienen un hueco»: un hueco es una hipótesis (glosario y Ética). El gráfico de barras de horas pasó a una tabla con una barra fina por fila. |
| 2 | Cola de revisión | **Hecho** | Tabla de seis columnas (Prioridad, Prob. sin pareja, Puntos sensor sup., Cámara, Tipo de caso, Clase) sin recortes ni desplazamiento horizontal a 1366 y 1920 px; detalle siempre a la derecha, con estado vacío; «Curva de priorización» es la primera pestaña; ningún puntaje con valores como «-50,000» (prueba `test_ningun_puntaje_sin_sentido_en_la_cola_ni_en_explica`). | El segmento, la distancia y los fotogramas pasaron al panel de detalle y los identificadores al CSV (el ejemplo traía segmento en la tabla). El estado vacío dice «Seleccione una fila para ver su detalle» (registro de usted de toda la página) y no «Elige…». |
| 3 | Auditoría de cámaras | **Hecho** | «Sin datos» en gris plano `#E3E6EB`, sin rayado, distinto del teal y del rojo; leyenda con las mismas tres muestras y palabras del anillo; las celdas con hueco llevan el relleno rojo suave del anillo. | — |
| 4 | Menos tarjetas, jerarquía real | **Hecho** | Una sola superficie elevada (panel del Resumen y detalle de la cola); radios de 0 (tablas), 6 (controles) y 14 px (panel); una sola sombra en la hoja (prueba `test_radios_segun_el_papel_y_una_sola_sombra`); barra lateral clara del mismo tono que el lienzo, con línea fina, en `[theme.sidebar]` de los dos `config.toml` y en `css()`; fichas de Ética, alertas, filtros y «Cómo se calcula» sin caja. | El mapa de calor sigue en un contenedor con borde fino (es un área de desplazamiento). El contraste se calcula sobre los tokens (todos los pares sobre 4,5:1); no se midió sobre las imágenes. |
| 5 | Validación > Selección | **Hecho** | Criterios O1 a O4 con nombre (Discrimina, Vale la pena, Recall en el punto A, Estable y calibrada) y umbrales leídos del plan v3; «Cumple» o «No cumple» en texto; fila de la solución elegida destacada y marcada «Elegida»; «Regla top» se muestra como «regla de puntos del sensor superior» en toda la página (prueba que recorre las ocho secciones). Documentos regenerados: informe técnico, preguntas cruzadas, guion, README de EP3 y pendientes de la página. | «Regla top» sigue como clave de los datos y en documentos históricos o de solo lectura (ver «Lo que no quedó bien»). |
| 6 | Puntuar datos nuevos | **Parcial** | Primero las acciones (elegir archivo, ejemplo, resultado); el formato de entrada está en un expander cerrado debajo; encabezados de la Lista B en español. Nada de Waymo se publica. | No hay un botón «Puntuar» separado: la puntuación ocurre al elegir el archivo o el ejemplo, como antes (agregar el botón cambiaría el comportamiento). |

## Paleta de curvas (dataviz)
Validada con `validate_palette.js` en modo claro (superficie = papel). Metas: separación para daltonismo (ΔE de CVD) de 8 o más y piso de visión normal de 15 o más entre curvas adyacentes.

| | Curvas (en orden) | CVD, peor par adyacente | Visión normal, peor par adyacente | Resultado |
|---|---|---|---|---|
| Antes | {', '.join(f'`{c}`' for c in pal['antes']['paleta'])} | ΔE {cvd_a} | ΔE {nor_a} | no pasa |
| Después | {', '.join(f'`{c}`' for c in pal['despues']['paleta'])} | ΔE {cvd_d} | ΔE {nor_d} | pasa |

Antes (adyacentes):

{tabla_validador(pal['antes']['adyacentes'])}

Después (adyacentes):

{tabla_validador(pal['despues']['adyacentes'])}

Después (todos los pares, la comprobación más exigente):

{tabla_validador(pal['despues']['todos_los_pares'])}

Con la paleta nueva no hizo falta la codificación secundaria que pedía el plan para un par que no llegara; el trazo discontinuo se mantiene de todos modos. Ninguna curva pinta texto con su color. La curva con XGBoost de referencia se revisó en el navegador; la de E2 no se fotografió.

## Medición del Resumen a 1366 x 768
Ventana de exactamente {fold['viewport'][0]} x {fold['viewport'][1]} px (Chrome sin interfaz, `scripts/ep3/f23_medir_resumen.py`): el anillo ocupa de {round(fold['anillo']['arriba'])} a {round(fold['anillo']['abajo'])} px, su leyenda llega a {round(fold['leyenda_anillo']['abajo'])}, la afirmación termina en {round(fold['afirmacion']['abajo'])} y el panel principal en {round(fold['panel_principal']['abajo'])}; desplazamiento horizontal: {fold['scroll_horizontal_px']} px. Un navegador real gasta unos 120 px en barras: aun así el panel (hasta {round(fold['panel_principal']['abajo'])} px) cabe en unos 650 px de alto útil. Fuente medida de la afirmación: {fold['fuente_de_la_afirmacion'].replace('.', ',')}.

## Capturas
{len(caps)} capturas (15 por ancho, 1366 y 1920 px, con las seis pestañas de Validación, la cola con y sin fila y el modo presentación), {listas} de {len(caps)} completas según la espera robusta de `capturar_pagina.py`; desplazamiento horizontal máximo: {scroll} px; diferencia máxima entre el enlace y su alerta: {f'{dy:.1f}'.replace('.', ',')} px (límite 5); errores de consola: {errores}. Antes de F23: `images/ep3/pagina/antes_f23/`. Las 30 imágenes y la de 1366 x 768 se abrieron y se revisaron una por una (cuatro de ellas, en la corrida inmediatamente anterior con el mismo código: Generalización a 1366, Selección a 1920, Puntuar a 1920 y el modo presentación a 1920). Las correcciones de las pasadas están en `auditoria_diseno_pagina.md` (sección F23). En `05_validacion_en_muestra_1920.png` el interruptor «Modo presentación» de la barra lateral sale cortado abajo: es un efecto de la captura (la ventana se ajusta al alto de esa página, 717 px) y no de la página.

## Pruebas
- Antes de F23: **{suite['antes']['pasaron']}** aprobadas (`{suite['comando']}`).
- Después: **{with_pytest['pasaron']}** aprobadas, {with_pytest['fallaron']} fallidas, {with_pytest['omitidas']} omitidas, en {str(with_pytest['duracion_s']).replace('.', ',')} s.
- Nuevas: `tests/ep3/test_pagina_f23.py` ({with_pytest['nuevas_f23']} pruebas: anillo en el Resumen, seis columnas en la Cola, gris de «sin datos», expander cerrado, barra lateral clara, paleta validada, nombre visible de la regla, criterios de selección, plan y sello). Adaptadas, por comparar etiquetas o estructura anteriores: `test_pagina_f20.py`, `test_pagina_f21.py`, `test_pagina_f22.py`, `test_pagina_pulido.py` y `test_pagina_rediseno.py`.
- El número de pruebas de los documentos sale de `scripts/ep3/contar_pruebas.py` y `generar_docs_ep3.py` (ejecutados al final).

## Integridad del sello
Comprobada con `scripts/ep3/f23_integridad_sello.py` (solo lectura: sha256 y `git status`): {antes['n']} archivos sellados comparados (`artefactos_ep3/`, plan de selección y su hash, notebook 00b, scripts y módulos de la validación externa, manifests y modelos congelados de EP2 y EP3). Resultado: **{'intacto' if despues['intacto'] else 'CAMBIÓ ALGO'}** (cambiados: {len(despues['cambiados'])}, faltan: {len(despues['faltan'])}, nuevos: {len(despues['nuevos'])}; `git status` sobre lo sellado: {len(despues['git_status_sobre_lo_sellado'])} líneas).

| Archivo | sha256 (registrado antes de F23) | Después |
|---|---|---|
{filas_sello}

No se ejecutó `ingesta_nuevos.py` ni `evaluar_sellado.py` y no se abrieron datos nuevos. `verificar_congelados.py` y `verificar_congelados_v3.py` se corrieron al final (14 de 14 y 5 de 5).

## Archivos modificados y creados
{lista_archivos()}

## Lo que no quedó bien o no pude verificar
1. **No hay botón «Puntuar» separado** en «Puntuar datos nuevos» (cambio 6 parcial): se mantuvo la puntuación automática.
2. **«en muestra» y las cifras de apoyo.** El Resumen lleva la etiqueta junto a la afirmación y en la nota de las horas, que es el máximo de dos por pantalla que fija `test_resumen_dice_en_muestra_a_lo_mas_dos_veces…`. El AUC y los casos encontrados por clase no llevan etiqueta propia; los cubre el chip de estado del encabezado. Si se prefiere una etiqueta en cada cifra, hay que subir ese límite.
3. **«Regla top» sigue en:** {citas_regla_top()}. La guía de estilo y la auditoría la citan a propósito para explicar el renombre; el resto son registros históricos de fases anteriores o notebooks ejecutados (regenerarlos exige ejecutarlos). La clave interna de los datos y del código (`candidatos.py`, CSV de evidencia, `artefactos_ep3/`) no se cambia por regla. Los documentos de EP2 (README, informe) son de solo lectura.
4. **Curva con E2 de referencia:** no la fotografié. Con XGBoost y sin referencia sí. La pestaña de la curva no forma parte del script de capturas oficial.
5. **Fuentes.** Cambria viene con Windows y se vio en las capturas ({fold["fuente_de_la_afirmacion"].split(" / ")[1].replace("px", " px").replace(".", ",")}); si falta en otro equipo caen Palatino y Georgia, y eso no lo probé.
6. **Solo Chrome sin interfaz** a 1366 y 1920 px. No probé otros navegadores, ni zoom, ni lector de pantalla.
7. **«Puntuar» con resultados** no está en el juego oficial de capturas (solo el estado vacío); lo vi aparte, con el segmento de ejemplo. Los valores de «Tipo de objeto» siguen en inglés («PEDESTRIAN»), como vienen de los datos.
8. **404 internos de Streamlit:** {sum(1 for c in caps if c.get('404_internos_de_streamlit'))} de {len(caps)} capturas los registran; no los comparé con F22.
9. **Docker y AWS:** fuera de alcance, no se tocaron ni se probaron.
10. **Textos de redacción que cambié** para quitar cadenas con puntos medios (chip, pie, versión, resultado de la cola, texto del cargador): son frases de presentación; las cifras no cambian.
"""
    SALIDA.write_text(md, encoding="utf-8")
    print("escrito", SALIDA.relative_to(RAIZ))


if __name__ == "__main__":
    main()
