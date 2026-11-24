"""F27: genera docs/ep3/REPORTE_F27.md (el Resumen en dos pasos y el menú en el orden del proceso). Las cifras se leen de sus archivos de origen (nada se copia a mano):

- docs/ep3/f24_fold_resumen.json        panel del Resumen a 1366 x 768, modo normal y presentación (scripts/ep3/f24_medir_resumen.py)
- docs/ep3/f25_barra_lateral.json       barra lateral a 1366 x 768 (scripts/ep3/f25_medir_barra.py)
- docs/ep3/f27_contraste.json           contraste real del texto (scripts/ep3/f24_auditar_contraste.py --salida docs/ep3/f27_contraste.json)
- docs/ep3/f25_ambar_en_el_dom.json     ámbar en el DOM de las 8 vistas (scripts/ep3/f25_buscar_ambar.py)
- docs/ep3/f27_resultado_suite.json     resultado de la suite de EP3 (scripts/ep3/f27_registrar_suite.py)
- docs/ep3/f27_sello_despues.json       integridad del sello (scripts/ep3/f23_integridad_sello.py --comprobar --etiqueta f27)
- data/08_reporting_ep3/capturas_resultado.json   las 30 capturas, su geometría y los errores de consola
- ``git status --short`` (solo lectura) para la lista de archivos

Uso: .venv\\Scripts\\python scripts/ep3/generar_reporte_f27.py
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
SALIDA = DOC / "REPORTE_F27.md"
LIMITE_F26 = datetime.fromtimestamp((DOC / "f26_sello_despues.json").stat().st_mtime)      # lo modificado después del último sello de F26 es de F27


def cargar(ruta: Path) -> dict | list:
    return json.loads(ruta.read_text(encoding="utf-8"))


def coma(x: float | str, dec: int = 1) -> str:
    return (f"{x:.{dec}f}" if isinstance(x, (int, float)) else str(x)).replace(".", ",")


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def lista_archivos() -> str:
    """Archivos con cambios en git y modificados después de cerrar F26; las capturas y las copias de revisión se resumen por carpeta."""
    salida = subprocess.run(["git", "status", "--short", "-uall"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=False).stdout
    etiqueta = {"M": "modificado", "??": "nuevo", "D": "borrado", "A": "agregado"}
    sueltos: list[tuple[str, str]] = []
    grupos: dict[str, list[str]] = {}
    for linea in salida.splitlines():
        if not linea.strip():
            continue
        st, ruta = linea[:2].strip(), linea[3:].strip().strip('"')
        p = RAIZ / ruta
        if st != "D" and (not p.exists() or datetime.fromtimestamp(p.stat().st_mtime) < LIMITE_F26):
            continue
        if ruta.startswith("images/ep3/pagina/"):
            if st == "D" or st == "??" or st == "M":
                grupos.setdefault("images/ep3/pagina/ (capturas con el menú nuevo; las de la numeración anterior se borraron)", []).append(etiqueta.get(st, st))
        elif ruta.startswith("docs/ep3/revision/"):
            grupos.setdefault("docs/ep3/revision/ (copias de revisión de los documentos, regeneradas)", []).append(etiqueta.get(st, st))
        elif st != "D":
            sueltos.append((st, ruta))
    L = [f"- `{ruta}`: {etiqueta.get(st, st)}" for st, ruta in sorted(sueltos, key=lambda x: x[1])]
    L += [f"- {clave}: {len(v)} archivos ({', '.join(sorted(set(v)))})" for clave, v in grupos.items()]
    return "\n".join(L)


def main() -> None:
    fold = cargar(DOC / "f24_fold_resumen.json")
    con = cargar(DOC / "f27_contraste.json")
    amb = cargar(DOC / "f25_ambar_en_el_dom.json")
    barra = {m["modo"]: m for m in cargar(DOC / "f25_barra_lateral.json")}
    suite = cargar(DOC / "f27_resultado_suite.json")
    sello = cargar(DOC / "f27_sello_despues.json")
    caps = cargar(RAIZ / "data/08_reporting_ep3/capturas_resultado.json")
    d, res = suite["despues"], con["resumen"]
    geo = [c["geometria"] for c in caps if c.get("geometria")]
    errores = sum(len(c.get("errores_consola") or []) for c in caps)
    n_norm, n_pres = fold["normal"], fold["presentacion"]
    bn, bp = barra["normal"], barra["presentación"]
    md = f"""# Reporte de F27: el Resumen en dos pasos y el menú en el orden del proceso

*Generado por `scripts/ep3/generar_reporte_f27.py` desde sus archivos de origen. Decisiones: DEC-110 a DEC-112 en `ESTADO.md`; guía de estilo regenerada en `guia_estilo_pagina.md`. Sin commit: el usuario hace el commit.*

**En una línea.** El proyecto tiene dos partes (filtrar las cámaras con posibles huecos y priorizar las cajas del resto) y la página solo contaba la primera en el Resumen. Ahora el Resumen se lee en dos pasos, el menú sigue ese orden y cada paso lleva a su página. No se creó una página nueva (la Cola de revisión ya es la página de la priorización) y no cambiaron cálculos, cifras ni textos sellados.

## Qué se hizo

Pruebas: **{d['pasaron']}** aprobadas, {d['fallaron']} falladas, {d['omitidas']} omitidas ({suite['comando']}, {coma(d['duracion_s'])} s); antes de F27 había {suite['antes']['pasaron']} y se agregaron {d['nuevas_f27']} en `tests/ep3/test_pagina_f27.py`. Sello: **{'intacto' if sello['intacto'] else 'CAMBIÓ'}** (`f27_sello_despues.json`: {sello['archivos_comparados']} archivos comparados; cambiados {len(sello['cambiados'])}).

| Código | Cambio | Qué quedó |
|---|---|---|
| E1 | Menú en el orden del proceso | Grupos «{'», «'.join(A.GRUPOS_NAV)}». Auditoría de cámaras (paso 1) va antes que Cola de revisión y Explica una caja (paso 2). Los nombres de las 8 secciones, sus direcciones y el rol no cambiaron; Resumen sigue siendo la página por defecto. |
| E2 | Resumen en dos pasos | Encabezado «1 · {A.PASO_1_TITULO}» (solo número y título; enlace «{A.PASO_1_ENLACE}») con el panel del anillo; y «2 · {A.PASO_2_TITULO}» (frase: «{A.PASO_2_FRASE}», enlace «{A.PASO_2_ENLACE}») con «Impacto estimado» y la vista de la cola. Debajo, «Cifras de apoyo» y las «Alertas» (una bajo otra, cada una con su enlace). Todos los textos son constantes de `app_logica.py`. |
| E3 | Vista de las primeras cajas de la cola | {A.FILAS_VISTA_RESUMEN} cajas con prioridad, probabilidad, cámara y clase, calculadas con la misma cola, el mismo flujo (dos pasos) y el mismo presupuesto ({int(A.PRESUPUESTO_VISTA_RESUMEN * 100)} %) con que abre «Cola de revisión»; una prueba compara ambas tablas. Dice el empate de las primeras cajas (el orden entre cajas empatadas no informa) y que es «en muestra». |
| E4 | Del paso 1 al paso 2 | Al final de la Auditoría, el enlace «{A.PASO_1_SIGUIENTE}» (sin flecha, como pide la regla de F23). |
| E5 | Barra lateral | Con seis grupos el menú desbordaba la barra (8 px en modo normal, 14 px en presentación, con el interruptor fuera de la vista). Se redujo la separación entre grupos (.7 rem) y, en presentación, el relleno de los enlaces; no se quitó ningún elemento. A 1366 × 768: desborde {bn['desborde_px']} px y {bp['desborde_px']} px; interruptor a {bn['interruptor']['abajo']} px y {bp['interruptor']['abajo']} px (límite 760). |

**Medidas y capturas.** Panel principal del Resumen a 1366 × 768: termina en **{n_norm['panel_termina_en_px']} px** en modo normal y **{n_pres['panel_termina_en_px']} px** en presentación (límite {n_norm['limite_px']}). Contraste: {miles(res['textos_medidos'])} textos en {res['vistas']} vistas, {res['textos_por_debajo']} por debajo de 4,5:1 (mínimo {coma(res['razon_minima_dom'], 2)} en el DOM y {coma(res['razon_minima_en_pixeles'], 2)} en los píxeles). Ámbar `#F5B73B` en el DOM de las 8 vistas: {len(amb['ambar'])} elemento (el punto de «Ciclistas»). {sum(1 for c in caps if c['listo'])} capturas completas (15 a 1366 px y 15 a 1920 px), {errores} errores de consola, desplazamiento horizontal máximo {max(g['scroll_horizontal_px'] for g in geo)} px.

## Qué no se hizo y por qué

1. **No se creó una página «Priorización» aparte.** La Cola de revisión ya es esa página; duplicarla habría repetido filtros y curva. Renombrarla habría tocado pruebas, documentos generados y capturas sin aportar más que el título.
2. **La vista de cajas del Resumen muestra empates, no un orden informativo.** Las primeras cajas de la cola comparten el mismo puntaje del sensor superior; por eso la vista lo dice debajo en vez de presentarlas como un orden fino.
3. **La Cola no tiene un enlace de «paso anterior» hacia la Auditoría.** Se dejó fuera para no recargar sus filtros; el menú numerado y el selector «Flujo» ya cuentan el orden.
4. **Las capturas de la numeración anterior se borraron** (`02_cola…`, `03_explica…`, `04_auditoria…`): el número de cada captura sigue el orden del menú, que cambió. Ningún documento las citaba.
5. **Los textos «Revisión» y «Calidad de datos» siguen en `auditoria_diseno_pagina.md` y en los reportes de F20 a F26**, que cuentan cómo era el menú entonces.

## Ajuste posterior a pedido del usuario (DEC-113): el Resumen sin el aviso «en muestra»

Se quitó del Resumen (y solo del Resumen): la frase del paso 1 («¿Qué cámaras tienen posibles huecos?…»), «en la muestra de» de la afirmación (ahora «{A.AFIRMACION_RESUMEN.format(huecos='k posibles huecos', segmentos='n segmentos')}»), «de desarrollo» del subtítulo, el «en muestra» de la nota bajo las primeras cajas, «Estimación en muestra» (ahora «Estimación: … (supuesto, no medido)»), el menú «Fuente» y la alerta «Validación externa pendiente». Las alertas quedan en dos (celdas marcadas y ciclistas) y el rol «Ingeniero consumidor de datos» abre con «Celdas marcadas». Una prueba vigila que el Resumen no vuelva a decirlo.

**Lo que se conservó y por qué.** Ninguna cifra cambió: siguen siendo de los 41 segmentos, con el detector ajustado con los mismos datos y sin validación con segmentos nuevos. Ese hecho sigue dicho en el pie, en la Cola, en Validación, en Ética y límites, en Ayuda y en Puntuar (el usuario pidió el Resumen, así que el resto no se tocó), y la regla de `CLAUDE.md` de rotular las cifras fuera de la página (informe, README, guion) sigue vigente. Si se quiere extender el cambio a otras vistas, es una decisión aparte.

## Archivos modificados

Archivos con cambios en git y modificados después de cerrar F26:

{lista_archivos()}
"""
    SALIDA.write_text(md, encoding="utf-8")
    print(f"escrito {SALIDA.relative_to(RAIZ)} ({len(md)} caracteres)")


if __name__ == "__main__":
    main()
