"""F18-C0 / F20-P2: genera docs/ep3/guia_estilo_pagina.md desde app/estilos.py (TOKENS, tipografia y contraste calculado) y src/.../app_logica.py (nombre, secciones, navegacion). Sin cifras a mano."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "app"))
import estilos as E  # noqa: E402

from waymo_evaluacion.ep3.app_logica import (  # noqa: E402
    CHIP_ESTADO, COLUMNA_FOTOGRAMAS, COLUMNA_PROBABILIDAD, ESLOGAN, GRUPOS_NAV, ICONOS, MIN_CAJAS_RANGO, PERFILES, PRODUCTO, SECCIONES, SUPUESTO_SEGUNDOS, URL_PAGINA,
)

USO = {"primario": "el único acento: títulos de página, enlaces, selección, barra de un paso y celdas sanas del mapa", "primario_oscuro": "texto sobre fondos de énfasis", "texto": "texto principal",
       "texto_suave": "texto secundario, notas y encabezados de tabla", "fondo": "fondo de la página", "superficie": "barra lateral, métricas y encabezados de tabla", "borde": "bordes de 1 px y separadores (decorativo)",
       "aviso_fondo": "SOLO la etiqueta «en muestra» y el chip de estado", "aviso_texto": "texto de la etiqueta «en muestra» y del chip", "aviso_borde": "borde de la etiqueta «en muestra» y del chip (decorativo)",
       "hueco": "SOLO huecos de cámara (rojo): contorno con X en el mapa y cifra de celdas marcadas", "hueco_fondo": "fondo de apoyo del rojo de hueco"}


def razon(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def main() -> None:
    filas = "\n".join(f"| `{k}` | `{v}` | {USO.get(k, '')} |" for k, v in E.TOKENS.items())
    contr = "\n".join(f"| {a} sobre {b} | {razon(E.contraste(E.TOKENS[a], E.TOKENS[b]))}:1 | {'cumple' if E.contraste(E.TOKENS[a], E.TOKENS[b]) >= 4.5 else 'NO CUMPLE'} |" for a, b in E.PARES_CONTRASTE)
    iconos = "\n".join(f"| {s} | `{i.strip(':')}` | `/{URL_PAGINA[s]}` |" for s, i in ICONOS.items())
    grupos = "\n".join(f"- **{g}:** {', '.join(ss)}" for g, ss in GRUPOS_NAV.items())
    esp = ", ".join(f"{k} = {v}" for k, v in E.ESPACIADO.items())

    def trazo(r: list[int]) -> str:
        return "continuo" if r[1] == 0 else f"discontinuo (trazo {r[0]}, hueco {r[1]})"

    curvas = "\n".join(f"| {n} | `{c}` | {trazo(r)} | {razon(E.contraste(c, '#FFFFFF'))}:1 |" for n, c, r in zip(E.CURVAS_NOMBRES, E.CURVAS_COLORES, E.CURVAS_RAYAS))
    md = f"""# Guía de estilo de la página

*Generada por `scripts/ep3/generar_guia_estilo.py` desde `app/estilos.py` y `src/waymo_evaluacion/ep3/app_logica.py`. Las pruebas `tests/ep3/test_pagina_rediseno.py`, `tests/ep3/test_pagina_pulido.py` y `tests/ep3/test_pagina_f20.py` exigen el contraste, que el tema de Streamlit use estos tokens y las reglas de gráficos, tablas y textos de abajo.*

## Producto y marco (F20)
- **Nombre:** {PRODUCTO} (neutro: no usa la marca ni el logo de Waymo; la fuente de datos solo se cita en el pie: «Waymo Open Dataset v2, uso académico»). Aparece **una sola vez**, en el wordmark de la barra lateral (SVG propio e inline, sin URL, con la versión de la solución debajo).
- **Descripción:** {ESLOGAN}
- **Ícono de la pestaña:** `app/assets/icono.png`, dibujado por `scripts/ep3/generar_icono_pagina.py`.
- **Navegación** (`st.navigation` con páginas de archivo en `app/paginas/`; {len(SECCIONES)} páginas agrupadas):
{grupos}
- **Rol** (selector discreto al pie de la barra lateral, etiqueta «Rol»; {len(PERFILES)} roles): cambiar de rol lleva a la página que sugiere y ordena primero su alerta en el Resumen. Sin píldora de perfil en el encabezado.
- **Encabezado de página:** título pequeño (1,5 rem, no un H1 enorme), una línea de descripción y, a la derecha, **un solo chip de estado** «{CHIP_ESTADO}» que abre un popover con el texto completo de «en muestra». Es el que cumple la visibilidad exigida por DEC-14: no hay banners ámbar por pantalla ni acordeones «¿Qué significa?». Además, cada cifra del flujo en dos pasos lleva una etiqueta pequeña «en muestra».
- **Pie único:** versión de la solución, fuente de datos y «Datos de desarrollo». «Nada se guarda ni se envía» aparece solo en Ayuda y Ética.

## Paleta (tokens)
Un solo acento (azul oscuro). El color semántico se reserva para el estado: **rojo = hueco**, **ámbar = etiqueta «en muestra»**. Bordes de 1 px, radio de 6 px, fondo blanco y gris muy claro; sin sombras, sin bordes superiores de color y sin píldoras. Apta para daltonismo: el rojo de los huecos nunca va solo (siempre con contorno grueso y una «X» en el mapa, y con texto), y las celdas sanas usan una escala de un solo tono (azul).

| Token | Valor | Uso |
|---|---|---|
{filas}

## Contraste (WCAG, mínimo 4,5:1 en texto)
| Par | Razón | Estado |
|---|---|---|
{contr}

## Tipografía y espaciado
- Pila del sistema con «Segoe UI» primero: `{E.PILA_TIPOGRAFICA}`. **Sin fuentes externas, sin CDN, sin imágenes remotas:** una prueba falla si algún archivo de `app/` contiene `http://` o `https://` (la única excepción es la declaración de espacio de nombres del SVG propio).
- Cifras con `font-variant-numeric: tabular-nums`. Escala: cuerpo 15 px; título de página {E.TAMANO_TITULO}; cifras de las métricas {E.TAMANO_METRICA}; tablas compactas (filas de 30 px); modo presentación multiplica la letra por 1,18.
- Espaciado: {esp} (se aplican como márgenes y separaciones).
- Estados **hover** y **foco** visibles (contorno de 2 px en el azul del acento) en botones, enlaces de la navegación y controles.

## Componentes
- **Métricas** (`aud-metrica`): franja de 4 cajas compactas de la misma altura (etiqueta, cifra de {E.TAMANO_METRICA}, nota), sin bordes de color. En modo presentación van 2 x 2 (nunca una tarjeta huérfana).
- **Etiqueta «en muestra»** (`aud-muestra`): pequeña, ámbar, junto a cada cifra del flujo en dos pasos.
- **Filas de alerta** (`aud-fila`): punto de color de estado, título, texto y enlace a la sección.
- **Ficha** (`aud-ficha`): bloques de título pequeño y texto, en dos columnas (Ética y límites).
- **Resultado** (`aud-resultado`): la frase principal de la cola, con ambos flujos.
- **Tablas HTML** (`aud-tabla`) para textos largos (glosario): dos columnas, el texto se ajusta a la celda; las tablas de datos son `st.dataframe` compactos con el ancho de cada columna **calculado** con su encabezado y su contenido (`formato.anchos_columnas`), de modo que ningún encabezado queda cortado.

## Gráficos y mapas
- **Mapa de calor de la Auditoría** (escala de un solo tono azul, de casi blanco = 0 % a azul oscuro = 100 %), dentro de un contenedor de altura fija con desplazamiento y **una sola leyenda** en palabras (`leyenda_mapa`). Tiene **tres estados que no se confunden**:
  1. celda con datos suficientes: azul según la proporción de cajas con pareja;
  2. **«Sin cajas o menos de {MIN_CAJAS_RANGO} en el rango»**: gris con rayado diagonal; significa «no se evalúa» y **no es lo mismo que una tasa de 0 %**;
  3. **hueco**: contorno rojo grueso con una «X» (el rojo nunca va solo).
  Las etiquetas de segmento son los **últimos 6 dígitos** (el id completo va en el tooltip); por defecto los segmentos con celdas marcadas van primero y se puede ver solo las celdas con datos suficientes.
- **Curvas de la cola**: la línea lleva el color **y** el trazo (no solo el color), la banda sombreada es del mismo color con transparencia, y la leyenda sale de las líneas y lista solo las curvas dibujadas. Regla técnica: la banda no codifica el campo «nombre» (Vega-Lite fusionaría las leyendas y borraría la de las líneas), así que hay una banda por curva con color fijo.
- **Impacto estimado** (Resumen): barras horizontales de horas para encontrar el 80 % (sin orden, solo cola, auditoría + cola); la tercera lleva «en muestra».
- **Validación**: cada pestaña abre con un gráfico leído de los CSV de origen (barras con intervalo de confianza, puntos con intervalo y por pliegue, tasa por tipo de caso, brazos A, B y C) y deja la tabla completa en un solo expander; el eje usa coma decimal.

| Curva | Color | Trazo | Contraste sobre blanco |
|---|---|---|---|
{curvas}

## Tablas
- **Cola de revisión (maestro-detalle):** `st.dataframe` con selección de una fila (`on_select="rerun"`); al elegirla se abre un panel de detalle a la derecha con la explicación de esa caja. La columna **{COLUMNA_PROBABILIDAD}** (probabilidad calibrada, en %) reemplaza a la antigua barra «Prioridad», que quedaba saturada en 100.
- **{COLUMNA_FOTOGRAMAS}** (`{COLUMNA_FOTOGRAMAS}`): un mismo objeto aparece en varios fotogramas y cada uno es una caja distinta de la cola; la vista «Agrupar por objeto» deja una fila por objeto sin cambiar el conteo de cajas a revisar.
- **Formatos (es-CL) de `tabla_legible`**: enteros sin decimales («3», «1.600»), proporciones como porcentaje, el parámetro de regularización C en notación científica («1,0e-5»), nombres legibles de hiperparámetros y valores en español («Pliegue», nunca «Fold»); nunca una columna con dos escalas distintas mezcladas («20» junto a «1.600» es lo esperado; «20,000» junto a «1.600» no) ni «-0,000».
- **Controles**: sin decimales con punto (la distancia de «Explica una caja» va de 1 en 1 m).

## Cargador de archivos
Los textos propios de Streamlit («Drag and drop…», «Browse files», «500MB per file») no se pueden cambiar por configuración: se ocultan con CSS y se muestra el texto en español («Arrastre el archivo aquí · Parquet, hasta 500 MB», botón «Elegir archivo»). Riesgo: depende de los `data-testid` de Streamlit 1.65. Los cargadores se rotulan «Archivo 1 (obligatorio)» y «Archivo 2 (opcional)» (sin tarjetas numeradas).

## Arranque
`scripts/ep3/arrancar_app.bat` y `.ps1` abren la página con `app/lanzar.py`, que carga y calienta los datos y la solución congelada (`app/precarga.py`) antes de aceptar visitas; con `streamlit run app/app.py` directo la página funciona igual, pero la carga empieza en la primera visita. Medición: `data/08_reporting_ep3/pagina_arranque.json`.

## Íconos y direcciones
Material Icons de Streamlit (`:material/nombre:`), sin emojis (una prueba lo vigila). La página por defecto (Resumen) se sirve en la raíz; las demás, en la ruta indicada.

| Página | Ícono | Ruta |
|---|---|---|
{iconos}

## Números y redacción
- **Formato es-CL** (`src/waymo_evaluacion/ep3/formato.py`, con pruebas): miles con punto (80.571), decimales con coma (87,4), porcentaje con espacio (70,3 %).
- **Registro neutro de herramienta interna** («Se muestran…», «Seleccione…»): sin frases que hablen de la propia página, sin tutorial en segunda persona, sin repetir avisos. Una prueba vigila las frases prohibidas («Empiece por aquí», «Cómo funciona», «la página se lo dice», «Mueva los controles», «vea qué pasa», «¿Qué significa?»).
- **Sin jerga** ni nombres de columna en snake_case en pantalla: las tablas pasan por `tabla_legible`. Se evita «recall» como titular: se dice «unas 70 de cada 100 cajas sin pareja».
- **Términos definidos** en «Ayuda y glosario» (tabla de dos columnas): caja, par 2D, celda, hueco, cola, presupuesto, cobertura, intervalo de confianza, post hoc, en muestra, sin prueba ciega.
- Las celdas que marca el detector se llaman **celdas marcadas** (DEV-3), nunca «falsas alarmas».
- Toda cifra del flujo en dos pasos lleva la etiqueta «en muestra»; el supuesto de {SUPUESTO_SEGUNDOS:.0f} s por caja se dice siempre como supuesto.
"""
    (RAIZ / "docs/ep3/guia_estilo_pagina.md").write_text(md, encoding="utf-8")
    print("escrita guia_estilo_pagina.md")


if __name__ == "__main__":
    main()
