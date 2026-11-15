"""F18-C0: genera docs/ep3/guia_estilo_pagina.md desde app/estilos.py (TOKENS y contraste calculado) y src/.../app_logica.py (nombre, eslogan, secciones). Sin cifras a mano."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "app"))
import estilos as E  # noqa: E402

from waymo_evaluacion.ep3.app_logica import ESLOGAN, ICONOS, PRODUCTO, SECCIONES  # noqa: E402

USO = {"primario": "títulos, botón principal, enlaces, celdas sanas del mapa", "primario_oscuro": "texto sobre fondos de énfasis", "acento": "datos positivos y pasos", "texto": "texto principal",
       "texto_suave": "texto secundario y notas", "fondo": "fondo de la página", "superficie": "tarjetas y barra lateral", "borde": "bordes y separadores (decorativo)",
       "aviso_fondo": "fondo de los avisos «en muestra» y de las advertencias", "aviso_texto": "texto de los avisos", "aviso_borde": "borde de avisos (decorativo)", "hueco": "huecos de cámara (rojo)", "hueco_fondo": "fondo de las insignias de hueco"}


def main() -> None:
    filas = "\n".join(f"| `{k}` | `{v}` | {USO.get(k, '')} |" for k, v in E.TOKENS.items())
    contr = "\n".join(f"| {a} sobre {b} | {E.contraste(E.TOKENS[a], E.TOKENS[b]):.2f}:1 | {'cumple' if E.contraste(E.TOKENS[a], E.TOKENS[b]) >= 4.5 else 'NO CUMPLE'} |" for a, b in E.PARES_CONTRASTE)
    iconos = "\n".join(f"| {s} | `{i.strip(':')}` |" for s, i in ICONOS.items())
    esp = ", ".join(f"{k} = {v}" for k, v in E.ESPACIADO.items())
    md = f"""# Guía de estilo de la página

*Generada por `scripts/ep3/generar_guia_estilo.py` desde `app/estilos.py` y `src/waymo_evaluacion/ep3/app_logica.py`. La prueba `tests/ep3/test_pagina_rediseno.py` exige el contraste y que el tema de Streamlit use estos tokens.*

## Producto
- **Nombre:** {PRODUCTO} (neutro: no usa la marca ni el logo de Waymo; la fuente de datos solo se cita en el pie: «Waymo Open Dataset v2, uso académico»).
- **Eslogan:** {ESLOGAN}
- **Ícono:** `app/assets/icono.png`, dibujado por `scripts/ep3/generar_icono_pagina.py` (una caja 3D con una marca de verificación: una persona revisa).
- **Secciones ({len(SECCIONES)}):** {', '.join(SECCIONES)}.

## Paleta (tokens)
Azul profundo como color primario, un acento verde azulado, ámbar para avisos, rojo para huecos y grises neutros. Apta para daltonismo: el rojo de los huecos nunca va solo (siempre con contorno grueso y una «X» en el mapa, y con texto), y las celdas sanas usan una escala de un solo tono (azul).

| Token | Valor | Uso |
|---|---|---|
{filas}

## Contraste (WCAG, mínimo 4,5:1 en texto)
| Par | Razón | Estado |
|---|---|---|
{contr}

## Tipografía y espaciado
- Tipografía del sistema (`font = "sans serif"`; la fuente que incluye Streamlit en su paquete). **Sin fuentes externas, sin CDN, sin imágenes remotas:** una prueba falla si algún archivo de `app/` contiene `http://` o `https://`.
- Escala: cuerpo 1 rem; títulos de tarjeta 0,92 rem; cifras de tarjeta 2 rem; modo presentación multiplica por 1,18.
- Espaciado: {esp} (se aplican como márgenes y separaciones de las tarjetas y bloques).

## Componentes
- **Tarjeta de cifra** (`aud-tarjeta`): título, cifra grande, nota. Borde superior de color: azul (neutro), verde azulado, ámbar (estimaciones) o rojo (huecos).
- **Insignia** (`aud-insignia`): perfil activo, avisos.
- **Aviso «en muestra»**: compacto, siempre visible (no en un tooltip), con un expander «¿Qué significa?» con el texto completo.
- **Pasos** (`aud-paso`): «Cómo funciona» en 3 pasos dibujados con HTML y CSS propios.
- **Resultado destacado** (`aud-resultado`): la frase principal de la cola.
- **Pie**: versión de la solución, fuente de datos, «Una persona revisa y decide», «Nada se guarda ni se envía».

## Íconos
Material Icons de Streamlit (`:material/nombre:`), sin emojis (una prueba lo vigila).

| Sección | Ícono |
|---|---|
{iconos}

## Números y redacción
- **Formato es-CL** (`src/waymo_evaluacion/ep3/formato.py`, con pruebas): miles con punto (80.571), decimales con coma (87,4), porcentaje con espacio (70,3 %).
- **Sin jerga** ni nombres de columna en snake_case en pantalla: las tablas pasan por `tabla_legible`. Se evita «recall» como titular: se dice «unas 70 de cada 100 cajas sin pareja».
- **Términos definidos** en «Ayuda y glosario»: caja, par 2D, celda, hueco, cola, presupuesto, cobertura, intervalo de confianza, post hoc, en muestra, sin prueba ciega.
- Las celdas que marca el detector se llaman **celdas marcadas** (DEV-3), nunca «falsas alarmas».
- Toda cifra del flujo en dos pasos lleva el aviso «en muestra».
"""
    (RAIZ / "docs/ep3/guia_estilo_pagina.md").write_text(md, encoding="utf-8")
    print("escrita guia_estilo_pagina.md")


if __name__ == "__main__":
    main()
