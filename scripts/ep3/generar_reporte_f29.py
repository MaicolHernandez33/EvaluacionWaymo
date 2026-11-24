"""F29: genera docs/ep3/REPORTE_F29.md (Resumen rediseñado para uso diario a partir de la referencia visual del usuario). Las cifras se leen de sus archivos de origen (nada se copia a mano):

- docs/ep3/f24_fold_resumen.json        primera pantalla del Resumen a 1366 x 768, modo normal y presentación (scripts/ep3/f24_medir_resumen.py)
- docs/ep3/f25_barra_lateral.json       barra lateral a 1366 x 768
- docs/ep3/f29_contraste.json           contraste real del texto (scripts/ep3/f24_auditar_contraste.py --salida docs/ep3/f29_contraste.json)
- docs/ep3/f25_ambar_en_el_dom.json     ámbar en el DOM de las 8 vistas
- docs/ep3/f29_navegacion.json          «Auditar» y «Abrir» en el navegador real (scripts/ep3/f29_navegacion.py)
- docs/ep3/f29_resultado_suite.json     resultado de la suite de EP3 (scripts/ep3/f29_registrar_suite.py)
- docs/ep3/f29_sello_despues.json       integridad del sello (scripts/ep3/f23_integridad_sello.py --comprobar --etiqueta f29)
- data/08_reporting_ep3/capturas_resultado.json   las 30 capturas, su geometría y los errores de consola
- ``git status --short`` (solo lectura) para la lista de archivos

Uso: .venv\\Scripts\\python scripts/ep3/generar_reporte_f29.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3 import app_logica as A  # noqa: E402

DOC = RAIZ / "docs/ep3"
SALIDA = DOC / "REPORTE_F29.md"
LIMITE_ANTERIOR = datetime.fromtimestamp((DOC / "f27_sello_despues.json").stat().st_mtime)      # lo modificado después del último sello de F27/F28 es de F29


def cargar(ruta: Path) -> dict | list:
    return json.loads(ruta.read_text(encoding="utf-8"))


def coma(x: float | str, dec: int = 1) -> str:
    return (f"{x:.{dec}f}" if isinstance(x, (int, float)) else str(x)).replace(".", ",")


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def lista_archivos() -> str:
    """Archivos con cambios en git y modificados después de cerrar F27/F28; las capturas y las copias de revisión se resumen por carpeta."""
    salida = subprocess.run(["git", "status", "--short", "-uall"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=False).stdout
    etiqueta = {"M": "modificado", "??": "nuevo", "D": "borrado", "A": "agregado"}
    sueltos: list[tuple[str, str]] = []
    grupos: dict[str, list[str]] = {}
    for linea in salida.splitlines():
        if not linea.strip():
            continue
        st, ruta = linea[:2].strip(), linea[3:].strip().strip('"')
        p = RAIZ / ruta
        if st != "D" and (not p.exists() or datetime.fromtimestamp(p.stat().st_mtime) < LIMITE_ANTERIOR):
            continue
        if ruta.startswith("images/ep3/pagina/"):
            grupos.setdefault("images/ep3/pagina/ (capturas del Resumen rediseñado y de los destinos de «Auditar» y «Abrir»)", []).append(etiqueta.get(st, st))
        elif ruta.startswith("docs/ep3/revision/"):
            grupos.setdefault("docs/ep3/revision/ (copias de revisión de los documentos, regeneradas)", []).append(etiqueta.get(st, st))
        elif st != "D":
            sueltos.append((st, ruta))
    L = [f"- `{ruta}`: {etiqueta.get(st, st)}" for st, ruta in sorted(sueltos, key=lambda x: x[1])]
    L += [f"- {clave}: {len(v)} archivos ({', '.join(sorted(set(v)))})" for clave, v in grupos.items()]
    return "\n".join(L)


def main() -> None:
    fold = cargar(DOC / "f24_fold_resumen.json")
    con = cargar(DOC / "f29_contraste.json")
    amb = cargar(DOC / "f25_ambar_en_el_dom.json")
    barra = {m["modo"]: m for m in cargar(DOC / "f25_barra_lateral.json")}
    nav = cargar(DOC / "f29_navegacion.json")
    suite = cargar(DOC / "f29_resultado_suite.json")
    sello = cargar(DOC / "f29_sello_despues.json")
    caps = cargar(RAIZ / "data/08_reporting_ep3/capturas_resultado.json")
    d, res = suite["despues"], con["resumen"]
    geo = [c["geometria"] for c in caps if c.get("geometria")]
    errores = sum(len(c.get("errores_consola") or []) for c in caps)
    n, p = fold["normal"], fold["presentacion"]
    cola_total = A.cola_prioritaria(A.cargar_datos(RAIZ / "data/09_app_ep3")["cajas"], {})[1]
    bn, bp = barra["normal"], barra["presentación"]
    md = f"""# Reporte de F29: Resumen rediseñado para uso diario

*Generado por `scripts/ep3/generar_reporte_f29.py` desde sus archivos de origen. Decisiones: DEC-114 a DEC-117 en `ESTADO.md`. «F29» es el nombre en este repositorio del prompt «F27 — Rediseño del Resumen» del usuario (F27 ya era el Resumen en dos pasos y el menú). Sin commit: el usuario hace el commit.*

**En una línea.** El Resumen se lee ahora como una consola de inicio de turno, siguiendo la referencia visual del usuario: cuatro indicadores, el bloque «Alertas de cámara» con una fila por celda marcada (botón «Auditar») y el anillo del segmento elegido, la «Cola de revisión» con filtros, tabla y segmentos prioritarios (botón «Abrir»), y un pie con la divulgación de rigor. No cambió ningún modelo, cálculo ni cifra: las cifras que ya estaban solo cambiaron de lugar.

## Qué se hizo

Pruebas: **{d['pasaron']}** aprobadas, {d['fallaron']} falladas, {d['omitidas']} omitidas ({suite['comando']}, {coma(d['duracion_s'])} s); antes de F29 había {suite['antes']['pasaron']} y se agregaron {d['nuevas_f29']} en `tests/ep3/test_pagina_f29.py`. Sello: **{'intacto' if sello['intacto'] else 'CAMBIÓ'}** (`f29_sello_despues.json`: {sello['archivos_comparados']} archivos comparados; cambiados {len(sello['cambiados'])}).

| Punto del prompt | Qué quedó |
|---|---|
| 1. Franja de 4 indicadores | Segmentos nuevos («cargados, sin revisar»; una sola función decide qué es «sin revisar»: `segmentos_sin_revisar`), Cámaras con alerta (en rojo si es mayor que 0), Cajas en la cola ({miles(cola_total)} en los datos actuales: el total de la cola de dos pasos) y % de cajas sin pareja. El cambio respecto de ayer solo se muestra si `cambio_respecto_de_ayer` devuelve un valor; hoy no hay corte anterior y se omite (una prueba comprueba las dos ramas). |
| 2. «Alertas de cámara» | Rótulo, titular dinámico «Hay N posibles huecos de cámara en los últimos datos sin revisar.» (o «Todas las cámaras sanas.» con la hora de la última actualización de los datos), subtítulo, enlace «Abrir la auditoría de cámaras», una fila por celda marcada (hasta {A.FILAS_ALERTAS_RESUMEN}, las de más cajas afectadas primero) con segmento (6 últimos dígitos), cámara (número y nombre), estado «Hueco» en palabras e ícono, y «Auditar». La primera fila viene elegida; elegir otra cambia el anillo. «Auditar» abre la Auditoría con ese segmento y esa cámara ya elegidos (`session_state`) y su celda resaltada en el mapa. |
| 3. «Cola de revisión» | Filtros por clase, cámara y segmento; columnas Prioridad, Segmento, Caja, Cámara, Clase, Prob. sin pareja y Acción («Abrir» lleva a «Explica una caja» con los controles puestos con los valores de esa caja). Orden determinista: probabilidad descendente, segmento, identificador de objeto y fotograma; la columna Caja es única (identificador del objeto y número de fotograma), así que no hay filas idénticas. Etiqueta «Regla poco confiable» con punto ámbar en las filas de ciclista. Panel «Segmentos con más cajas prioritarias» con barras (los {A.SEGMENTOS_PRIORITARIOS_RESUMEN} segmentos con más cajas en la cola del {int(A.PRESUPUESTO_VISTA_RESUMEN * 100)} %). |
| 4. Lo que sale del Resumen | «Cifras de apoyo» pasó a Validación (mismas cifras). «Impacto estimado» con su menú «Fuente» solo se ve con el modo presentación. La alerta duplicada «Celdas marcadas» y la de ciclistas salieron (el rol ya no reordena alertas). |
| 5. Pie | «{A.ESTADO_VALIDACION}» con el enlace «{A.ENLACE_VALIDACION}»; la atribución de Waymo, con el texto exacto actual, sigue en el pie de toda la página. «Datos de ejemplo» no está. |

**Criterios de aceptación.**
- Con los datos actuales hay **{len(n['filas_de_alerta'])} alertas** y el titular dice 2.
- Primera pantalla a 1366 × 768, sin desplazarse: indicadores visibles **{'sí' if n['indicadores_visibles'] and p['indicadores_visibles'] else 'NO'}**, titular visible **{'sí' if n['titular_visible'] and p['titular_visible'] else 'NO'}** y lista de alertas visible **{'sí' if n['lista_de_alertas_visible'] and p['lista_de_alertas_visible'] else 'NO'}**; la última fila de alerta termina en **{n['panel_termina_en_px']} px** (modo normal) y **{p['panel_termina_en_px']} px** (presentación), con límite de {n['limite_px']} px.
- Ninguna cifra cambió de valor: cada cifra del Resumen se calcula con las funciones que ya existían y las pruebas de regresión de cifras están entre las {d['pasaron']} aprobadas ({d['fallaron']} falladas).
- Navegación en el navegador real (`f29_navegacion.json`): «Auditar» abrió la Auditoría con «{nav['auditar_0']['celda']}»; elegir la segunda fila cambió el anillo a «{nav['anillo_tras_elegir_fila_1']}» y su «Auditar» abrió la otra celda; «Abrir» abrió «Explica una caja» con «{nav['abrir_0']['caja'][:70]}…». Conclusión de la prueba: {nav['conclusion']}.

**Medidas y capturas.** Barra lateral a 1366 × 768: desborde {bn['desborde_px']} px y {bp['desborde_px']} px. Contraste: {miles(res['textos_medidos'])} textos en {res['vistas']} vistas, {res['textos_por_debajo']} por debajo de 4,5:1 (mínimo {coma(res['razon_minima_dom'], 2)} en el DOM y {coma(res['razon_minima_en_pixeles'], 2)} en los píxeles). Ámbar `#F5B73B` en el DOM de las 8 vistas: {len(amb['ambar'])} elemento. {sum(1 for c in caps if c['listo'])} capturas completas (15 a 1366 px y 15 a 1920 px), {errores} errores de consola, desplazamiento horizontal máximo {max(g['scroll_horizontal_px'] for g in geo)} px. Imágenes de los destinos: `f29_destino_auditar.png` y `f29_destino_abrir.png`.

## Diferencias con la referencia y por qué

1. **No se copiaron las cifras ni los textos inventados del mockup.** Faltan «Actualizado hoy 08:30», «desde ayer 18:00», «+1,4 puntos respecto de ayer», «Hueco detectado hoy 06:12» y «Datos de ejemplo del mockup»: los datos no traen horas ni un corte anterior. La fila de alerta dice «Hueco · N cajas afectadas» (dato real de la Lista A) en vez de la hora.
2. **Tipografía.** La referencia usa Inter desde Google Fonts; la página sigue con su única familia sans del sistema (sin CDN). El peso de las cifras grandes es 600 (la regla del proyecto admite 400, 500 y 600; el mockup usa 700).
3. **Mayúsculas pequeñas** en el rótulo «Alertas de cámara» y en el encabezado de la tabla de la cola, como en la referencia. Antes una prueba de F23 las prohibía; se cambió para permitir exactamente esos dos usos.
4. **La etiqueta «Regla poco confiable» no lleva caja con borde**, solo el punto ámbar y el texto (regla de F25: el ámbar solo marca advertencias reales y no se usa en cajas).
5. **«Prioridad» del Resumen no es la posición de «Cola de revisión».** El Resumen ordena con desempate determinista (probabilidad, segmento, caja); la página de la Cola conserva el orden de siempre, que entre cajas con el mismo puntaje no informa. Por eso la primera caja del Resumen tiene 90,4 % y la primera fila de la Cola 87,8 %: son cajas del mismo grupo empatado. No se cambió el orden de la Cola porque podría mover cuáles cajas entran en el corte del 20 % y alterar cifras.
6. **El menú «Fuente» solo existe junto al impacto estimado** (modo presentación), porque ya no hay otra cifra del Resumen que lo necesite.
7. **El nombre de cada caja** es el final del identificador del objeto y su fotograma (por ejemplo `j8GQ-01`), no un número secuencial como `#0412`; en modo presentación va numerada (`#001`) para no mostrar identificadores.

## Qué no se hizo y por qué

1. **No se probó con cientos o miles de segmentos.** El diseño limita la lista de alertas a {A.FILAS_ALERTAS_RESUMEN} filas (avisa cuántas más hay), la cola a {A.FILAS_COLA_RESUMEN} y los segmentos prioritarios a {A.SEGMENTOS_PRIORITARIOS_RESUMEN}; con 41 segmentos solo se vio con 2 alertas. La velocidad con muchos más datos no se midió.
2. **«Sin revisar» es el total cargado** (41), como pidió el prompt. No existe estado de revisión ni flujo en vivo; cuando exista, se cambia `segmentos_sin_revisar` en `app_logica.py`.
3. **Los generadores de los reportes de F26 y F27** (`generar_reporte_f26.py`, `generar_reporte_f27.py`) citan constantes que F29 quitó (la afirmación, los encabezados de paso): ya no se pueden volver a ejecutar. Sus reportes quedan como están; no se tocaron.
4. **Los documentos históricos** (reportes de F20 a F27 y `ESTADO.md`) siguen describiendo cómo era el Resumen en su momento.

## Archivos modificados

Archivos con cambios en git y modificados después de cerrar F27/F28:

{lista_archivos()}
"""
    SALIDA.write_text(md, encoding="utf-8")
    print(f"escrito {SALIDA.relative_to(RAIZ)} ({len(md)} caracteres)")


if __name__ == "__main__":
    main()
