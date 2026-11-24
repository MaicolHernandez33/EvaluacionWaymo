"""F26: genera docs/ep3/REPORTE_F26.md. Las cifras se leen de sus archivos de origen (nada se copia a mano):

- docs/ep3/f26_marca.json               marca (¿cabe en la barra?), pie, título de la pestaña y favicon (scripts/ep3/f26_capturas_extra.py)
- docs/ep3/f24_fold_resumen.json        panel del Resumen a 1366 x 768, modo normal y presentación (scripts/ep3/f24_medir_resumen.py)
- docs/ep3/f26_contraste.json           contraste real del texto (DOM y píxeles) en 14 vistas (scripts/ep3/f24_auditar_contraste.py --salida docs/ep3/f26_contraste.json)
- docs/ep3/f25_ambar_en_el_dom.json     ámbar en el DOM de las 8 vistas
- docs/ep3/f25_barra_lateral.json       barra lateral a 1366 x 768
- docs/ep3/f26_resultado_suite.json     resultado de la suite de EP3 (scripts/ep3/f26_registrar_suite.py)
- docs/ep3/f26_sello_despues.json       integridad del sello (scripts/ep3/f23_integridad_sello.py --comprobar --etiqueta f26)
- data/08_reporting_ep3/capturas_resultado.json   las 30 capturas, su geometría y los errores de consola
- ``git status --short`` (solo lectura) para la lista de archivos

Uso: .venv\\Scripts\\python scripts/ep3/generar_reporte_f26.py
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
SALIDA = DOC / "REPORTE_F26.md"
INICIO_F26 = datetime(2026, 11, 22, 0, 0)               # F25 cerró el 2026-11-21: lo modificado desde este día es de F26


def cargar(ruta: Path) -> dict | list:
    return json.loads(ruta.read_text(encoding="utf-8"))


def coma(x: float | str, dec: int = 1) -> str:
    return (f"{x:.{dec}f}" if isinstance(x, (int, float)) else str(x)).replace(".", ",")


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def git_estado() -> list[tuple[str, str]]:
    salida = subprocess.run(["git", "status", "--short", "-uall"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=False).stdout
    return [(linea[:2].strip(), linea[3:].strip().strip('"')) for linea in salida.splitlines() if linea.strip()]


def lista_archivos() -> str:
    """Archivos con cambios en git y fecha de modificación de F26; las capturas y las copias de revisión se resumen por carpeta."""
    etiqueta = {"M": "modificado", "??": "nuevo", "D": "borrado", "A": "agregado"}
    sueltos: list[tuple[str, str]] = []
    grupos: dict[str, list[str]] = {}
    for st, ruta in git_estado():
        p = RAIZ / ruta
        if not p.exists() or datetime.fromtimestamp(p.stat().st_mtime) < INICIO_F26:
            continue
        if ruta.startswith("images/ep3/pagina/"):
            grupos.setdefault("images/ep3/pagina/ (capturas finales, recortes de la marca y del pie, vista del favicon a 16 px y Cola agrupada)", []).append(etiqueta.get(st, st))
        elif ruta.startswith("docs/ep3/revision/"):
            grupos.setdefault("docs/ep3/revision/ (copias de revisión de los documentos, regeneradas)", []).append(etiqueta.get(st, st))
        else:
            sueltos.append((st, ruta))
    L = [f"- `{ruta}`: {etiqueta.get(st, st)}" for st, ruta in sorted(sueltos, key=lambda x: x[1])]
    L += [f"- {clave}: {len(v)} archivos ({', '.join(sorted(set(v)))})" for clave, v in grupos.items()]
    return "\n".join(L)


def main() -> None:
    marca = cargar(DOC / "f26_marca.json")
    fold = cargar(DOC / "f24_fold_resumen.json")
    con = cargar(DOC / "f26_contraste.json")
    amb = cargar(DOC / "f25_ambar_en_el_dom.json")
    barra = {m["modo"]: m for m in cargar(DOC / "f25_barra_lateral.json")}
    suite = cargar(DOC / "f26_resultado_suite.json")
    sello = cargar(DOC / "f26_sello_despues.json")
    caps = cargar(RAIZ / "data/08_reporting_ep3/capturas_resultado.json")
    despues = suite["despues"]
    res = con["resumen"]
    listas = sum(1 for c in caps if c["listo"])
    geo = [c["geometria"] for c in caps if c.get("geometria")]
    scroll = max(g["scroll_horizontal_px"] for g in geo)
    errores = sum(len(c.get("errores_consola") or []) for c in caps)
    n_norm, n_pres = fold["normal"], fold["presentacion"]
    mn, mp = (json.loads(marca[k]) if isinstance(marca[k], str) else marca[k] for k in ("marca_normal", "marca_presentacion"))
    pie = json.loads(marca["pie"]) if isinstance(marca["pie"], str) else marca["pie"]
    n_ambar = len(amb["ambar"])
    md = f"""# Reporte de F26: marca propia (Lente), afirmación y pie, y ajustes de coherencia

*Generado por `scripts/ep3/generar_reporte_f26.py` desde sus archivos de origen. Decisiones: DEC-106 a DEC-109 en `ESTADO.md`; guía de estilo regenerada en `guia_estilo_pagina.md`. Sin commit: el usuario hace el commit.*

**En una línea.** La página se llama {A.NOMBRE_PRODUCTO}, tiene un símbolo propio, un título y una afirmación nuevos en el Resumen y un pie con la atribución del conjunto de datos; se quitó la pastilla «Datos de desarrollo»; los textos que dependen de dónde corre la página siguen la variable `EP3_ENTORNO`; y se corrigieron los desajustes de las capturas de F25. No cambiaron cálculos, cifras ni textos sellados.

## Qué se hizo

Pruebas: **{despues['pasaron']}** aprobadas, {despues['fallaron']} falladas, {despues['omitidas']} omitidas ({suite['comando']}, {coma(despues['duracion_s'])} s); antes de F26 había {suite['antes']['pasaron']}, y se agregaron {despues['nuevas_f26']} en `tests/ep3/test_pagina_f26.py`, que prueban las dos variantes de `EP3_ENTORNO` (`tests/ep3/conftest.py` quita la variable al empezar cada prueba para que no dependa del shell). Ningún límite subió. Sello: **{'intacto' if sello['intacto'] else 'CAMBIÓ'}** (`f26_sello_despues.json`: {sello['archivos_comparados']} archivos comparados; cambiados {len(sello['cambiados'])}).

| Código | Cambio | Estado | Qué quedó |
|---|---|---|---|
| A1 | Título del Resumen | Hecho | Título «{A.TITULO_RESUMEN}» y subtítulo «{A.SUBTITULO_RESUMEN}» (constantes). La etiqueta del menú sigue siendo «{A.SECCIONES[0]}». La pestaña del navegador dice «{mn['titulo']}» en todas las vistas (`NOMBRE_PRODUCTO`). |
| A2 | Quitar la pastilla | Hecho | Fuera de todas las vistas, con su CSS, `CHIP_CORTO` y `CHIP_ESTADO` (sin código muerto). Su menú traía tres frases que no estaban en otra parte («Por eso las cifras de este flujo son optimistas…», «preparada y sellada…» y «La ganancia del flujo en dos pasos sale de 2 celdas…»): quedaron, sin perderse, en Ayuda › «¿Qué significa «en muestra»?». La divulgación sigue visible en las oraciones con «(en muestra)», en la alerta «Validación externa pendiente» y en el pie. |
| A3 | Marca arriba a la izquierda | Hecho | Símbolo propio y original (cuadro de 28 px en panel alto con borde `#2A3A57` y mini anillo de cinco cuñas en acento `#6FA0FF` alrededor de un auto visto desde arriba; sin nada de Waymo), `{A.NOMBRE_PRODUCTO}` (14 px, 600) y `{A.SUBLINEA_MARCA}` (11 px, Texto 2). Cabe en la barra en modo normal ({mn['logo']['izquierda']} a {mn['logo']['derecha']} px de una barra de {mn['barra']['derecha']} px) y en presentación ({mp['logo']['izquierda']} a {mp['logo']['derecha']} px de {mp['barra']['derecha']} px). Favicon `app/assets/icono.png` (256 px) generado con Pillow desde la misma geometría (`scripts/ep3/generar_icono.py`; una prueba compara el PNG con lo que genera el script); la vista a 16 px está en `images/ep3/pagina/f26_favicon_16.png`. `PRODUCTO`, `set_page_config` y los docstrings de `app/` usan el nombre nuevo. |
| A4 | Afirmación del Resumen | Hecho | «{A.AFIRMACION_RESUMEN.format(huecos='k posibles huecos', segmentos='n segmentos')}» (singular «Se marcó 1 posible hueco de cámara…»; sin marcas «No se marcó ningún posible hueco…»), 22 px, peso 500, `text-wrap: balance`; «n segmentos» en acento y «k posibles huecos» en el rojo del hueco, con 600. Conserva «posibles» y «en la muestra». Pruebas y documentos adaptados. |
| A5 | Pie | Hecho | Dos líneas de {pie['parrafos'][0]['fuente_px']:.0f} px en `{pie['parrafos'][0]['color']}` (Texto 3), sin ámbar: la atribución (inglés, tal cual) y «Solución v3 congelada el 2026-11-14. Datos de desarrollo, 41 segmentos.». Cada línea ocupa {pie['parrafos'][0]['lineas']} línea a 1366 px. **La atribución es texto provisional** (ver abajo). |
| B1 | Textos según el entorno | Hecho | `EP3_ENTORNO` (por defecto `local`: los textos de siempre, sin cambio; `servidor`: la variante pedida) para «Dónde corre», «Consideraciones éticas», el subtítulo de Puntuar y la pregunta frecuente de los archivos (`TEXTOS_ENTORNO`). **Verificado en el código que los archivos cargados no se escriben a disco** (`pd.read_parquet` sobre el objeto cargado, que Streamlit guarda en memoria; `puntuar_segmento` no escribe; las descargas son bytes; `guardar` es de la solución congelada y la página no lo llama), así que la variante dice «no se guardan»; una prueba lo vigila. Probadas las dos variantes. Docker no se tocó. |
| B2 | Líneas huérfanas | Hecho | `text-wrap: balance` en títulos, subtítulos y frases de resumen y `pretty` en párrafos y notas. El subtítulo se cortaba a ~560 px porque vivía en una columna estrecha junto al chip (3,6 de 6,6); sin el chip ocupa todo el ancho. Revisadas en las capturas a 1366 px las seis que se veían (Resumen, Cola, Auditoría, Validación, Puntuar, Ética): ninguna queda con una palabra suelta. Un efecto colateral que se corrigió: `pretty` partía en dos líneas el valor del control deslizante («20»); ahora esos valores no se parten. |
| B3 | Resumen reordenado | Hecho | Panel principal; debajo, «Impacto estimado» (izquierda) y «Cifras de apoyo» (derecha); debajo, «Alertas» en tres columnas con su enlace cada una. Sin quitar ni cambiar contenido. Panel principal a 1366 × 768: termina en **{n_norm['panel_termina_en_px']} px** en modo normal y **{n_pres['panel_termina_en_px']} px** en presentación (límite {n_norm['limite_px']}); el modo presentación sigue con el interruptor a la vista ({barra['presentación']['interruptor']['abajo']} px) y sin desborde de la barra. Los colores por concepto de F25 no cambiaron. |
| B4 | «Puntaje: -50…» | Hecho | Dentro de «Cómo se calcula» (con su texto igual), bajo los tres pasos. Nada sellado lo impedía; se adaptaron tres pruebas que buscaban el texto sin importar dónde. |
| C1 | Porcentajes | Hecho | «Casos encontrados en peatones / ciclistas» muestra 80,6 % y 44,3 % (los mismos valores) y también lo dicen la alerta de ciclistas, los avisos del ciclista (Cola y Explica una caja), Ética y Ayuda, para que ninguna vista muestre 0,443 y otra 44,3 %. No es texto sellado. |
| C2 | Cola agrupada | Hecho (informe) | `images/ep3/pagina/f26_cola_agrupada.png`, con «Agrupar por objeto» activado con un clic real: la primera pantalla muestra 12 objetos distintos (prioridades 1, 4, 5, 9, 13…) en vez de 12 filas idénticas. El valor por defecto no cambió; usted decide si lo deja activado para la demostración. |

**Medidas y capturas.** Contraste: {miles(res['textos_medidos'])} textos en {res['vistas']} vistas, {res['textos_por_debajo']} por debajo de 4,5:1 (mínimo {coma(res['razon_minima_dom'], 2)} en el DOM y {coma(res['razon_minima_en_pixeles'], 2)} en los píxeles de las notas; `f26_contraste.json`). Ámbar `#F5B73B` en el DOM de las 8 vistas: {n_ambar} elemento (el punto de «Ciclistas»). {listas} capturas completas (15 a 1366 px y 15 a 1920 px), {errores} errores de consola, desplazamiento horizontal máximo {scroll} px. Revisadas una por una a 1366 px: Resumen (modo normal y presentación a 1366 × 768), Cola (curva y cajas), Explica una caja, Auditoría, Validación (En muestra y Selección), Puntuar, Ética, y los recortes de la marca (`f26_marca_normal.png`, `f26_marca_presentacion.png`) y del pie (`f26_pie.png`).

## Qué no se pudo y por qué

1. **La atribución de Waymo es provisional.** `ATRIBUCION_WAYMO` es el texto reconstruido de la licencia que traía el prompt; no se pudo contrastar con waymo.com/open/terms (esta tarea no hace peticiones externas). Hay que compararlo con la página antes de entregar; se cambia en una sola constante de `app_logica.py`.
2. **El nombre antiguo queda en documentos históricos.** «Auditor de etiquetas 3D» ya no está en lo visible de la página ni en `app/` ni en `app_logica.py` (una prueba lo vigila), pero sigue en `REPORTE_F18.md`, `plan_diseno_f23.md`, `ESTADO.md` (la bitácora, que cuenta lo que pasó), el notebook 14 y `scripts/ep3/crear_notebooks_ep3.py`. Esos archivos describen fases anteriores o son notebooks que esta tarea no regenera.
3. **`EP3_ENTORNO=servidor` no prueba nada fuera de la página.** El texto «no se guardan» es cierto para el código de la página; un proxy inverso o el registro de acceso del servidor pueden guardar otras cosas (nombres de archivo, direcciones IP). No se pudo comprobar porque Docker y el despliegue no se tocaron.
4. **El favicon se verificó como imagen, no en la pestaña de un navegador real.** El navegador sin interfaz declara el icono (`<link rel=icon>` apunta al PNG) y la vista a 16 px muestra el anillo y el auto; cómo lo pinte cada navegador en su pestaña no se pudo comprobar.
5. **El símbolo del auto se lee como un auto solo a tamaño grande.** A 16 px se distinguen el anillo y la silueta; la línea del parabrisas casi no se distingue. Es una limitación del tamaño, no de la geometría.
6. **«Cifras de apoyo» y «Alertas» cambiaron de lugar, no de contenido.** Si usted prefiere ver las alertas antes que las horas, es un intercambio de dos bloques en `resumen()`.

## Archivos modificados

Archivos con cambios en git y fecha de este trabajo (desde el {INICIO_F26:%Y-%m-%d}):

{lista_archivos()}
"""
    SALIDA.write_text(md, encoding="utf-8")
    print("escrito", SALIDA.relative_to(RAIZ))


if __name__ == "__main__":
    main()
