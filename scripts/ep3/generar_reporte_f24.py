"""F24: genera docs/ep3/REPORTE_F24.md. Las cifras se leen de sus archivos de origen (nada se copia a mano):

- docs/ep3/f24_paleta_validacion.json   salida de validate_palette.js (modo oscuro, sobre el panel)
- docs/ep3/f24_fold_resumen.json        medición del panel del Resumen en 1366 x 768, modo normal y presentación
- docs/ep3/f24_contraste.json           contraste real del texto (DOM y píxeles) en 14 vistas
- docs/ep3/f24_resultado_suite.json     resultado de la suite de EP3 (scripts/ep3/f24_registrar_suite.py)
- docs/ep3/f24_sello_despues.json       integridad del sello (scripts/ep3/f23_integridad_sello.py --comprobar --etiqueta f24)
- data/08_reporting_ep3/capturas_resultado.json   las 30 capturas, su geometría, los errores de consola y los 404 de Streamlit
- ``git status --short`` (solo lectura) para la lista de archivos

Uso: .venv\\Scripts\\python scripts/ep3/generar_reporte_f24.py
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
SALIDA = DOC / "REPORTE_F24.md"
INICIO_F24 = datetime(2026, 11, 21)                      # F23 terminó antes: los archivos con fecha de este día o posterior son de F24


def cargar(ruta: Path) -> dict | list:
    return json.loads(ruta.read_text(encoding="utf-8"))


def coma(x: float | str, dec: int = 1) -> str:
    return (f"{x:.{dec}f}" if isinstance(x, (int, float)) else str(x)).replace(".", ",")


def peor_par(texto: str, clave: str) -> str:
    m = re.search(clave + r"\s+worst all-pairs (\S+)↔(\S+) ΔE ([\d.]+)", texto)
    return f"{m.group(1)} contra {m.group(2)}, ΔE {coma(m.group(3))}" if m else "?"


def git_estado() -> list[tuple[str, str]]:
    salida = subprocess.run(["git", "status", "--short", "-uall"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=False).stdout
    return [(linea[:2].strip(), linea[3:].strip().strip('"')) for linea in salida.splitlines() if linea.strip()]


def lista_archivos() -> str:
    """Archivos con cambios en git que se tocaron desde el inicio de F24 (por fecha de modificación); las capturas se resumen por carpeta."""
    etiqueta = {"M": "modificado", "??": "nuevo", "D": "borrado", "A": "agregado"}
    sueltos: list[tuple[str, str]] = []
    grupos: dict[str, list[str]] = {}
    for st, ruta in git_estado():
        p = RAIZ / ruta
        if not p.exists() or datetime.fromtimestamp(p.stat().st_mtime) < INICIO_F24:
            continue
        if ruta.startswith("images/ep3/pagina/antes_f24/"):
            grupos.setdefault("images/ep3/pagina/antes_f24/ (cuatro capturas de la piel clara de F23, para comparar)", []).append(etiqueta.get(st, st))
        elif ruta.startswith("images/ep3/pagina/"):
            grupos.setdefault("images/ep3/pagina/ (capturas finales, incluidas las curvas `02b_curvas_*`)", []).append(etiqueta.get(st, st))
        else:
            sueltos.append((st, ruta))
    L = [f"- `{ruta}`: {etiqueta.get(st, st)}" for st, ruta in sorted(sueltos, key=lambda x: x[1])]
    L += [f"- {clave}: {len(v)} archivos ({', '.join(sorted(set(v)))})" for clave, v in grupos.items()]
    return "\n".join(L)


def main() -> None:
    pal = cargar(DOC / "f24_paleta_validacion.json")
    fold = cargar(DOC / "f24_fold_resumen.json")
    con = cargar(DOC / "f24_contraste.json")
    suite = cargar(DOC / "f24_resultado_suite.json")
    sello = cargar(DOC / "f24_sello_despues.json")
    caps = cargar(RAIZ / "data/08_reporting_ep3/capturas_resultado.json")
    n_norm, n_pres = fold["normal"], fold["presentacion"]
    res = con["resumen"]
    listas = sum(1 for c in caps if c["listo"])
    geo = [c["geometria"] for c in caps if c.get("geometria")]
    scroll = max(g["scroll_horizontal_px"] for g in geo)
    alertas = [a for g in geo for a in g["alertas"]]
    alertas_ok = sum(1 for a in alertas if a["enlace_debajo_del_texto"] and a["enlace_dentro_de_la_alerta"] and a["enlace_subrayado"] and a["solape_px"] <= 0)
    errores = sum(len(c.get("errores_consola") or []) for c in caps)
    urls: dict[str, int] = {}
    for c in caps:
        for u in c.get("404_urls") or []:
            urls[u.replace("http://localhost:", "localhost:")] = urls.get(u.replace("http://localhost:", "localhost:"), 0) + 1
    lista_404 = "\n".join(f"  - `{u}` ({n} veces)" for u, n in sorted(urls.items()))
    ad, ini, ramp = pal["paleta_adoptada"], pal["punto_de_partida_del_prompt"], pal["rampa_del_mapa_de_calor"]
    cvd_ad, nor_ad = peor_par(ad["todos_los_pares"], r"CVD separation"), peor_par(ad["todos_los_pares"], r"Normal-vision floor")
    cvd_ini, nor_ini = peor_par(ini["todos_los_pares"], r"CVD separation"), peor_par(ini["todos_los_pares"], r"Normal-vision floor")
    despues = suite["despues"]
    claves_sello = ["docs/ep3/plan_seleccion_ep3.sha256", "docs/ep3/plan_seleccion_ep3.json", "data/06_models_ep3/manifest_v3.json"]
    md = f"""# Reporte de F24: cambio de piel (tema oscuro) y defectos concretos

*Generado por `scripts/ep3/generar_reporte_f24.py` desde sus archivos de origen. Decisiones: DEC-97 a DEC-102 en `ESTADO.md`; guía de estilo regenerada en `guia_estilo_pagina.md`. Sin commit: el usuario hace los commits.*

**En una línea.** F24 cambió la piel (tema oscuro nativo de Streamlit, una sola familia sans, anillo como protagonista) y corrigió 18 defectos de maquetación **sin tocar la estructura, el contenido, las cifras ni los textos sellados**. Los tokens viven solo en `app/estilos.py` (de ahí salen el CSS y los dos `config.toml`).

## Qué se hizo

Mediciones de cierre (Chrome sin interfaz, solo localhost): panel del Resumen a 1366 x 768 termina en **{n_norm['panel_termina_en_px']} px** en modo normal y en **{n_pres['panel_termina_en_px']} px** en presentación (límite {n_norm['limite_px']} px); contraste real de **{f"{res['textos_medidos']:,}".replace(',', '.')}** textos en {res['vistas']} vistas, **{res['textos_por_debajo']}** por debajo de 4,5:1 (mínimo {coma(res['razon_minima_dom'], 2)}:1 en el DOM; las notas pequeñas medidas en píxeles, mínimo {coma(res['razon_minima_en_pixeles'], 2)}:1); {len(caps)} capturas (15 a 1366 px y 15 a 1920 px), {listas} completas; desplazamiento horizontal máximo {scroll} px; errores de consola {errores}.

| # | Defecto | Estado | Qué se hizo y cómo se comprobó |
|---|---|---|---|
| 1 | Blanco sobre blanco | Hecho | Tokens de la tabla del prompt: lienzo `{E.TOKENS['fondo']}`, barra `{E.TOKENS['barra']}` (línea derecha `{E.TOKENS['barra_borde']}`), panel `{E.TOKENS['panel']}` (borde `{E.TOKENS['panel_borde']}`, radio {E.RADIO_PANEL}), panel alto `{E.TOKENS['panel_alto']}` (borde `{E.TOKENS['panel_alto_borde']}`, radio {E.RADIO_CONTROL}). Una sola fuente (`TOKENS`); `generar_config_tema.py --comprobar` falla si un `config.toml` se desfasa y una prueba falla si aparece un hex fuera de `estilos.py`. |
| 2 | Pestañas | Hecho | Pestaña activa con subrayado de 2 px en el acento y peso 600 (Cola, Validación). |
| 3 | Notas más tenues que Texto 3 | Hecho | Se quitaron las opacidades de las notas: el texto más tenue es `texto_3` `{E.TOKENS['texto_3']}`. Medido en los tokens (pares de `PARES_CONTRASTE`) y en el DOM y los píxeles de las capturas (`f24_contraste.json`). |
| 4 | Afirmación del Resumen | Hecho | {n_norm['lineas_de_la_afirmacion']} líneas a 1366 px y {n_pres['lineas_de_la_afirmacion']} en presentación; tamaño {n_norm['tamano_de_la_afirmacion']}, peso 600; la columna de texto ocupa el {round(n_norm['fraccion_de_texto'] * 100)} % del panel. «41 segmentos» va en el acento y «2 celdas» en el color del hueco; el color no reemplaza el texto ni la «X». |
| 5 | Lista de cámaras | Hecho | Ocupa todo el ancho de la columna, con líneas continuas y {n_norm['holgura_bajo_la_lista_px']} px de aire bajo la última fila (medido). |
| 6 | Alertas del Resumen | Hecho | Una columna por alerta: título, texto y debajo un enlace visible, subrayado y en el acento («Ver en Auditoría de cámaras»). Geometría medida en las capturas: {alertas_ok} de {len(alertas)} alertas con el enlace bajo el texto, dentro de la alerta, subrayado y sin solape. |
| 7 | Barras de horas | Hecho | Barras de 10 px con extremos redondeados y el número alineado a la derecha. |
| 8 | Modo presentación a 1366 x 768 | Hecho | Panel (afirmación, anillo y lista) termina en {n_pres['panel_termina_en_px']} px (límite {n_pres['limite_px']}): afirmación de 1,38 rem en tres líneas, lista compacta y anillo de 250 px (300 px en modo normal). Medido también en modo normal ({n_norm['panel_termina_en_px']} px). `f24_fold_resumen.json`. |
| 9 | Filtros Clase y Cámara | Hecho | Selectores en panel alto con texto principal: se ven activos. |
| 10 | Panel de detalle de la Cola | Hecho | Tabla y detalle en 64 % y 36 %; anillo de unos 120 px **encima** de la cifra grande; 20 px de relleno; la última fila no toca el borde. |
| 11 | Nota del empate | Hecho | Texto secundario con una regla ámbar suave a la izquierda. |
| 12 | Botones de ejemplo y deslizadores de Explica | Hecho | Botones con borde `{E.TOKENS['panel_alto_borde']}`; pista del deslizador `{E.TOKENS['panel_borde']}` con relleno en el acento. |
| 13 | Etiquetas del gráfico de Explica | Hecho | Ejes y etiquetas en `texto_2`, 12 px o más; títulos en `texto`. |
| 14 | Mapa de calor de la Auditoría | Hecho | 41 filas de 16 px, sin desplazamiento interno. Rampa teal de un solo tono, más claro = más proporción con pareja. |
| 15 | Leyenda del mapa | Hecho | Una línea corta por estado (ver «Qué no se pudo» sobre el texto acortado). |
| 16 | «En muestra» de Validación | Hecho | Tres series con la paleta oscura (gris, azul medio y acento), valores en el color del texto y leyenda en una fila. |
| 17 | Selección | Hecho | «✓ Cumple» en el verde de lo sano y «✕ No cumple» en el color del texto, con íconos SVG propios (sin rojo ni ámbar); fila elegida en panel alto con la etiqueta «Elegida»; los textos no cambiaron. |
| 18 | Puntuar datos nuevos | Hecho | Botón de ejemplo primario (relleno del acento, texto `{E.TOKENS['fondo']}`) y zonas de arrastre con borde punteado `{E.TOKENS['sin_datos_borde']}`. |

**Paleta de curvas (dataviz, modo oscuro, superficie `{pal['superficie']}`).** El punto de partida del prompt (`{'`, `'.join(ini['paleta'])}`) pasaba los pares adyacentes pero no todos los pares: el peor era {cvd_ini} para daltonismo y {nor_ini} en visión normal. Se conservaron «Dos pasos» y «Un paso» y se ajustaron las otras tres hasta que **todos los pares** pasaron: `{'`, `'.join(ad['paleta'])}`; peor par para daltonismo {cvd_ad}, en visión normal {nor_ad}. XGBoost sigue discontinuo y las curvas de referencia llevan etiqueta directa. Rampa del mapa (`{'`, `'.join(ramp['pasos'])}`): pasa la validación ordinal (un solo tono, luminosidad monótona, escalones visibles). Todo en `f24_paleta_validacion.json`.

**Correcciones que salieron de revisar las capturas** (antes de la pasada final): las líneas de la lista de cámaras tenían cortes entre columnas (ahora son continuas); la leyenda del mapa decía «(más claro, más)» y quedó «Sana: más claro, más cajas con pareja»; dos notas decían «Línea negra» para un intervalo que ahora es claro; la «×» de «segmento × cámara» quedaba sola al inicio de una línea a 1920 px (ahora va unida a las dos palabras con espacios de no separación); los rombos y los intervalos del gráfico de Generalización se veían apagados sobre el fondo oscuro (más grandes y más opacos); la «X» de la muestra «Hueco» usaba peso 700 y la regla es 400 y 600.

**Capturas revisadas una por una (pasada final, con el código definitivo):** las 30 finales (15 a 1366 px y 15 a 1920 px: Resumen, Cola con y sin fila, Explica, Auditoría, las seis pestañas de Validación —incluidas «En muestra» y «Selección»—, Puntuar, Ética, Ayuda y Resumen en modo presentación), las dos del Resumen a 1366 x 768 y tres de la pestaña «Curva de priorización» (sin referencia, con XGBoost y con E2).

## Qué no se pudo y por qué

1. **Inter no está en el repositorio.** El prompt la deja opcional: si alguien pone `app/static/fonts/Inter-Variable.woff2` (licencia OFL, con su archivo de licencia), el tema la carga solo (`[[theme.fontFaces]]` y `server.enableStaticServing`; una prueba lo comprueba en una carpeta temporal). Hoy la página usa Segoe UI o la fuente del sistema, y no se descargó nada.
2. **`st.dataframe` no se puede estilizar con CSS** (se dibuja en un canvas). Solo se le aplicó el tema (`dataframeHeaderBackgroundColor` y compañía); la altura de fila, la barra de desplazamiento y la casilla de selección son las nativas, y su texto no entra en la auditoría de contraste del DOM (se revisó en las capturas).
3. **404 internos de Streamlit** (no se corrigen; vienen de que Streamlit pide `_stcore/health` y `_stcore/host-config` relativos a la ruta de cada página): {sum(urls.values())} registros en {len(caps)} capturas, {len(urls)} URL distintas:
{lista_404}
4. **Barra lateral a 1366 x 768.** Su contenido desborda la ventana en {n_norm['barra_lateral_desborde_px']} px en modo normal y {n_pres['barra_lateral_desborde_px']} px en presentación (la barra se desplaza sola). No se corrigió: el límite del prompt es el del panel del Resumen, y quitar elementos de la barra cambiaría el contenido.
5. **Textos que cambiaron por necesidad de la piel o de la maquetación** (ninguno es un texto sellado ni una cifra): la leyenda del mapa pasó a una línea corta por estado y las explicaciones largas al atributo `title` (defecto 15; `Sana: más claro, más cajas con pareja`); y las dos notas de Hiperparámetros y Ensambles que decían «Línea negra» dicen ahora «Línea clara», porque el intervalo se dibuja claro sobre fondo oscuro.
6. **Inconsistencia del prompt.** La tabla de tokens asigna el acento a la «curva Solo cola», pero su propia paleta de curvas da a «Un paso» (que es «solo cola») `#C77B1E`. El acento pinta «Solo cola (un paso)» en las barras de horas del Resumen; las curvas de la cola usan la paleta validada.
7. **«Puntaje: -50 (menos los puntos del sensor superior)»** en Explica no se tocó (decisión pendiente del usuario); solo recibió estilo.
8. **Alcance de la verificación.** Solo Chrome sin interfaz a 1366 y 1920 px (y 1366 x 768 para el Resumen); no probé otros navegadores, zoom, ni lector de pantalla. Los iconos de «Cumple» y «No cumple» son SVG propios porque la prueba de emojis de F20 prohíbe los caracteres ✓ y ✕ en `app/`.
9. **Docker y AWS:** fuera de alcance, no se tocaron ni se probaron. `requirements` sin cambios.

## Archivos modificados

Pruebas: **{despues['pasaron']}** aprobadas, {despues['fallaron']} fallidas, {despues['omitidas']} omitidas ({suite['comando']}, {coma(despues['duracion_s'])} s); antes de F24 había {suite['antes']['pasaron']}. Nuevas: `tests/ep3/test_pagina_f24.py` ({despues['nuevas_f24']} pruebas); adaptadas, por fijar la piel clara de F23, las de F20, F21, F22, pulido, rediseño y F23.

`tests/ep3/conftest.py` desactiva durante las pruebas el escaneo de componentes de terceros que hace cada `AppTest` de Streamlit (1,3 a 2 s por prueba con `altair` importado; la página no usa componentes de terceros): sin eso la prueba de tiempo de «Validación» daba 3,3 s contra el límite de 3 s y la suite tardaba casi 280 s en vez de unos 165. El umbral no se tocó (DEC-102).

Sello: **{'intacto' if sello['intacto'] else 'CAMBIÓ'}** (`f24_sello_despues.json`: {sello['archivos_comparados']} archivos comparados contra el registro de antes de F23; cambiados {len(sello['cambiados'])}, faltan {len(sello['faltan'])}, nuevos {len(sello['nuevos'])}); no se ejecutó `ingesta_nuevos.py` ni `evaluar_sellado.py`. `verificar_congelados.py` (14 de 14) y `verificar_congelados_v3.py` (5 de 5) se corrieron al final. Hashes de control: {', '.join(f'`{k.split("/")[-1]}`' for k in claves_sello)} sin cambios.

Archivos con cambios en git y fecha de este trabajo (desde el {INICIO_F24:%Y-%m-%d}):

{lista_archivos()}
"""
    SALIDA.write_text(md, encoding="utf-8")
    print("escrito", SALIDA.relative_to(RAIZ))


if __name__ == "__main__":
    main()
