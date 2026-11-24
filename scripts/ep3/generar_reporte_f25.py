"""F25: genera docs/ep3/REPORTE_F25.md. Las cifras se leen de sus archivos de origen (nada se copia a mano):

- docs/ep3/f25_paleta_validacion.json     salida de validate_palette.js (modo oscuro, sobre el panel) del mapa único entidad -> color
- docs/ep3/f25_ambar_en_el_dom.json       elementos del DOM de las 8 vistas que usan el ámbar o sus antiguos fondo y borde
- docs/ep3/f25_barra_lateral.json         barra lateral a 1366 x 768, modo normal y presentación
- docs/ep3/f25_barra_herramientas.json    barra de herramientas de los gráficos y de las tablas con el cursor encima
- docs/ep3/f25_contraste.json             contraste real del texto (DOM y píxeles) en 14 vistas
- docs/ep3/f24_fold_resumen.json          panel del Resumen a 1366 x 768 (lo regenera f24_medir_resumen.py)
- docs/ep3/f25_resultado_suite.json       resultado de la suite de EP3 (scripts/ep3/f25_registrar_suite.py)
- docs/ep3/f25_sello_despues.json         integridad del sello (scripts/ep3/f23_integridad_sello.py --comprobar --etiqueta f25)
- data/08_reporting_ep3/capturas_resultado.json   las 30 capturas, su geometría, los errores de consola
- ``git status --short`` (solo lectura) para la lista de archivos

Uso: .venv\\Scripts\\python scripts/ep3/generar_reporte_f25.py
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
import estilos as E  # noqa: E402

DOC = RAIZ / "docs/ep3"
SALIDA = DOC / "REPORTE_F25.md"
INICIO_F25 = datetime(2026, 11, 21, 20, 30)               # F24 cerró a las 20:22 de ese día: lo modificado después es de F25
ANTES = {"normal": {"interruptor_abajo": 725, "desborde": 47}, "presentación": {"interruptor_abajo": 791, "desborde": 129}}      # medido con f25_medir_barra.py al empezar F25 (piel de F24)


def cargar(ruta: Path) -> dict | list:
    return json.loads(ruta.read_text(encoding="utf-8"))


def coma(x: float | str, dec: int = 1) -> str:
    return (f"{x:.{dec}f}" if isinstance(x, (int, float)) else str(x)).replace(".", ",")


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def peor_par(texto: str, clave: str) -> str:
    m = re.search(clave + r"\s+worst all-pairs (\S+)↔(\S+) ΔE ([\d.]+)", texto)
    return f"{m.group(1)} contra {m.group(2)}, ΔE {coma(m.group(3))}" if m else "?"


def git_estado() -> list[tuple[str, str]]:
    salida = subprocess.run(["git", "status", "--short", "-uall"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=False).stdout
    return [(linea[:2].strip(), linea[3:].strip().strip('"')) for linea in salida.splitlines() if linea.strip()]


def lista_archivos() -> str:
    """Archivos con cambios en git y fecha de modificación posterior al cierre de F24; las capturas se resumen por carpeta."""
    etiqueta = {"M": "modificado", "??": "nuevo", "D": "borrado", "A": "agregado"}
    sueltos: list[tuple[str, str]] = []
    grupos: dict[str, list[str]] = {}
    for st, ruta in git_estado():
        p = RAIZ / ruta
        if not p.exists() or datetime.fromtimestamp(p.stat().st_mtime) < INICIO_F25:
            continue
        if ruta.startswith("images/ep3/pagina/antes_f24/"):
            grupos.setdefault("images/ep3/pagina/antes_f24/ (dos capturas de la piel de F24 para comparar, con el prefijo `f24_final_`)", []).append(etiqueta.get(st, st))
        elif ruta.startswith("images/ep3/pagina/"):
            grupos.setdefault("images/ep3/pagina/ (capturas finales, la de la barra lateral y la del cursor sobre el gráfico)", []).append(etiqueta.get(st, st))
        elif ruta.startswith("docs/ep3/revision/"):
            grupos.setdefault("docs/ep3/revision/ (copias de revisión de los documentos, regeneradas)", []).append(etiqueta.get(st, st))
        else:
            sueltos.append((st, ruta))
    L = [f"- `{ruta}`: {etiqueta.get(st, st)}" for st, ruta in sorted(sueltos, key=lambda x: x[1])]
    L += [f"- {clave}: {len(v)} archivos ({', '.join(sorted(set(v)))})" for clave, v in grupos.items()]
    return "\n".join(L)


def main() -> None:
    pal = cargar(DOC / "f25_paleta_validacion.json")
    amb = cargar(DOC / "f25_ambar_en_el_dom.json")
    barra = {m["modo"]: m for m in cargar(DOC / "f25_barra_lateral.json")}
    herr = cargar(DOC / "f25_barra_herramientas.json")
    con = cargar(DOC / "f25_contraste.json")
    fold = cargar(DOC / "f24_fold_resumen.json")
    suite = cargar(DOC / "f25_resultado_suite.json")
    sello = cargar(DOC / "f25_sello_despues.json")
    caps = cargar(RAIZ / "data/08_reporting_ep3/capturas_resultado.json")
    despues = suite["despues"]
    res = con["resumen"]
    listas = sum(1 for c in caps if c["listo"])
    geo = [c["geometria"] for c in caps if c.get("geometria")]
    scroll = max(g["scroll_horizontal_px"] for g in geo)
    errores = sum(len(c.get("errores_consola") or []) for c in caps)
    n_norm, n_pres = fold["normal"], fold["presentacion"]
    f = E.FLUJOS_COLORES
    cvd, nor = peor_par(pal["flujos_cromaticos"]["todos_los_pares"], r"CVD separation"), peor_par(pal["flujos_cromaticos"]["todos_los_pares"], r"Normal-vision floor")
    cvd_u, nor_u = peor_par(pal["union_informativa"]["todos_los_pares"], r"CVD separation"), peor_par(pal["union_informativa"]["todos_los_pares"], r"Normal-vision floor")
    claves_sello = ["docs/ep3/plan_seleccion_ep3.sha256", "docs/ep3/plan_seleccion_ep3.json", "data/06_models_ep3/manifest_v3.json"]
    n_amb = len(amb["ambar"])
    ambar_en = ", ".join(sorted({f"{a['vista']} (punto de ciclistas)" for a in amb["ambar"]})) or "ninguna vista"
    ba = barra["normal"], barra["presentación"]
    md = f"""# Reporte de F25: la página como producto (sin avisos naranjas y un color por concepto)

*Generado por `scripts/ep3/generar_reporte_f25.py` desde sus archivos de origen. Decisiones: DEC-103 a DEC-105 en `ESTADO.md`; guía de estilo regenerada en `guia_estilo_pagina.md`. Sin commit: el usuario hace el commit.*

**En una línea.** El chip del encabezado es una pastilla neutra, las etiquetas «en muestra» con caja se quitaron (las oraciones conservan la divulgación), el ámbar quedó solo en la advertencia de los ciclistas, un concepto tiene un color en las tres vistas, el interruptor del modo presentación se ve a 1366 × 768 y la barra de herramientas ya no tapa la oración de referencia de la curva. No se cambió estructura, cálculos, cifras ni textos sellados.

## Qué se hizo

Pruebas: **{despues['pasaron']}** aprobadas, {despues['fallaron']} falladas, {despues['omitidas']} omitidas ({suite['comando']}, {coma(despues['duracion_s'])} s); antes de F25 había {suite['antes']['pasaron']}, y se agregaron {despues['nuevas_f25']} en `tests/ep3/test_pagina_f25.py`. Ningún límite de pruebas subió. Sello: **{'intacto' if sello['intacto'] else 'CAMBIÓ'}** (`f25_sello_despues.json`: {sello['archivos_comparados']} archivos comparados; cambiados {len(sello['cambiados'])}).

| N.º | Cambio | Estado | Qué quedó |
|---|---|---|---|
| 1 | Chip del encabezado | Hecho | Pastilla neutra: fondo `{E.TOKENS['panel_alto']}`, borde `{E.TOKENS['panel_alto_borde']}`, texto `{E.TOKENS['texto_2']}`, un punto de 8 px en `{E.TOKENS['texto_3']}` y la etiqueta «Datos de desarrollo». El menú conserva la frase completa («Datos de desarrollo, sin validación externa») y lo que ya explicaba. Sin ámbar. |
| 2 | Etiquetas «en muestra» | Hecho | Quitadas del Resumen y de la Cola (las oraciones siguen diciendo «En la muestra de 41 segmentos» y «(en muestra)»). `aud-muestra` es texto simple en `{E.TOKENS['texto_3']}`, 12 px, sin caja ni borde; hoy ninguna vista lo necesita. `test_resumen_dice_en_muestra_a_lo_mas_dos_veces…` cuenta texto (límite de 2 sin cambios). |
| 3 | Ámbar de interfaz | Hecho | `{E.TOKENS['aviso_texto']}` aparece en {n_amb} elemento del DOM de las 8 vistas ({ambar_en}); además, en el CSS, el punto del aviso del ciclista de la Cola y de Explica una caja (es la misma advertencia; solo aparece al elegir un ciclista). Se quitaron los tokens `aviso_fondo`, `aviso_borde` y `aviso_hover`; la nota de empate usa el filete `{E.TOKENS['sin_datos_borde']}` y «Validación externa pendiente» un punto en `{E.TOKENS['texto_3']}`. Búsqueda en el DOM real: `f25_ambar_en_el_dom.json` (antiguos fondo, borde y hover hallados: {len(amb['antiguos_fondo_borde_hover'])}). |
| 4 | Un concepto, un color | Hecho | `E.FLUJOS_COLORES`: revisión sin orden `{f['Revisión sin orden']}`, solo cola `{f['Solo cola (un paso)']}`, auditoría + cola `{f['Auditoría + cola (dos pasos)']}`, solo celdas sanas, sin auditoría `{f['Solo celdas sanas, sin auditoría']}`. Lo usan las barras de horas del Resumen, las barras de «En muestra» y las curvas de la Cola. El Resumen no tiene leyenda de colores (cada barra lleva su rótulo), así que no hubo leyenda que cambiar; la prueba del Resumen ahora comprueba el color de cada barra. |
| 5 | Barra lateral en modo presentación | Hecho | A 1366 × 768 el interruptor «Modo presentación» termina en **{ba[1]['interruptor']['abajo']} px** (antes {ANTES['presentación']['interruptor_abajo']} px, fuera de la ventana de 768 px) y la barra ya no se desplaza (desborde {ba[1]['desborde_px']} px; antes {ANTES['presentación']['desborde']} px). En modo normal el interruptor termina en {ba[0]['interruptor']['abajo']} px (desborde {ba[0]['desborde_px']} px; antes {ANTES['normal']['desborde']} px). No se quitó ningún elemento ({ba[1]['enlaces']} enlaces del menú, rol e interruptor). |
| 6 | Barra de herramientas en la curva | Hecho | Oculta solo en los gráficos con `div:has(> [data-testid="stVegaLiteChart"]) > [data-testid="stElementToolbar"]` (por `data-testid`, no por clases generadas). Con el ratón real sobre el gráfico: `display: {herr['barras_con_el_cursor_sobre_el_grafico'][0]['display']}`; sobre la tabla de la cola la barra sigue ({herr['barras_con_el_cursor_sobre_la_tabla'][0]['ancho']} × {herr['barras_con_el_cursor_sobre_la_tabla'][0]['alto']} px). Captura: `images/ep3/pagina/f25_curva_cursor_encima.png`. |

**Paleta (dataviz, modo oscuro, superficie `{pal['superficie']}`, todos los pares).** Los tres colores cromáticos de los flujos pasan los cinco chequeos (peor par para daltonismo: {cvd}; visión normal: {nor}). Las cinco curvas de la Cola, sin cambios, siguen pasando. El gris es la línea base neutra (contraste {coma(pal['gris_linea_base']['contraste_contra_el_panel'])}:1 con el panel; el piso de croma de una paleta categórica no aplica). Para el tercer color los verdes y los amarillos chocaban con el naranja para daltonismo y el cian con el azul; `{f['Solo celdas sanas, sin auditoría']}` fue el que pasó. Salida completa: `f25_paleta_validacion.json`.

**Medidas y capturas.** Contraste: {miles(res['textos_medidos'])} textos en {res['vistas']} vistas, {res['textos_por_debajo']} por debajo de 4,5:1 (mínimo {coma(res['razon_minima_dom'], 2)} en el DOM y {coma(res['razon_minima_en_pixeles'], 2)} en los píxeles de las notas; `f25_contraste.json`). Panel del Resumen a 1366 × 768: {n_norm['panel_termina_en_px']} px en modo normal y {n_pres['panel_termina_en_px']} px en presentación (límite {n_norm['limite_px']}). {listas} capturas completas (15 a 1366 px y 15 a 1920 px), {errores} errores de consola, desplazamiento horizontal máximo {scroll} px. Revisadas una por una a 1366 px: Resumen, Cola (curva con XGBoost y cola de cajas), Validación (En muestra y Selección), la barra lateral a 1366 × 768 en los dos modos y el Resumen a 1366 × 768 en modo presentación (`09_resumen_modo_presentacion_1366x768.png`). Comparación con F24: `images/ep3/pagina/antes_f24/f24_final_01_resumen_1366.png` y `f24_final_05_validacion_en_muestra_1366.png`.

## Qué no se pudo y por qué

1. **El color de «solo celdas sanas» queda cerca del rosa de E2.** En la unión informativa de seis colores (flujos + curvas) falla el par `{cvd_u}` (daltonismo) y `{nor_u}` (visión normal). Los dos colores nunca comparten gráfico (E2 solo se dibuja en la curva de la Cola; las barras de Validación llevan leyenda con rótulo), pero no hay un sexto color validado para todos los pares: los verdes y amarillos chocan con el naranja y el cian con el azul. Si se prefiere separarlos del todo, habría que cambiar el rosa de E2 (curva validada en F24).
2. **Ocultar la barra de herramientas quita también «pantalla completa» y «descargar» de los gráficos.** Streamlit no ofrece un ajuste para dejar solo algunas opciones. El selector va por `data-testid`, pero depende de que Streamlit siga poniendo la barra como hermana del gráfico; si una versión nueva cambia esa estructura, la barra volvería a verse (la prueba del CSS no lo detectaría; sí lo haría `f25_comprobar_herramientas.py`).
3. **El tono de «Validación externa pendiente» está en `app_logica.py`.** Para el punto gris hubo que cambiar el valor `tono` de `aviso` a `neutro` en `alertas_resumen` (solo presentación; ningún cálculo, cifra ni texto cambió). Se avisa porque el prompt de F24 dejaba `app_logica.py` intacto.
4. **El aviso del ciclista (Cola y Explica una caja) conserva el punto ámbar.** El criterio dice «solo en el punto de Ciclistas»; se interpretó que el aviso «Ciclista: la regla es poco confiable» es la misma advertencia. Solo aparece al elegir una caja de ciclista, por eso no sale en el DOM de las capturas por defecto; se vio con el aviso inyectado en la página. Si se prefiere sin ámbar ahí, basta quitar `.aud-aviso::before`.
5. **`st.dataframe` sigue dibujándose en un canvas.** El color de sus filas y su barra de herramientas no se pueden cambiar con CSS (no se tocó).

## Archivos modificados

Archivos con cambios en git y fecha de este trabajo (después del cierre de F24):

{lista_archivos()}
"""
    SALIDA.write_text(md, encoding="utf-8")
    print("escrito", SALIDA.relative_to(RAIZ))


if __name__ == "__main__":
    main()
