"""Chequeos automáticos de los documentos Markdown generados (F19-C1 y C3).

* ``problemas_de_tablas``: en cada tabla (cabecera, separador y filas) todas las filas deben tener el mismo número de celdas que la cabecera. Las barras escapadas (``\\|``)
  no separan celdas; las barras SIN escapar sí, aunque estén dentro de comillas invertidas (así las trata GitHub), por eso un texto como ``(|azimut| <= 120)`` en una celda
  rompe la tabla.
* ``caracteres_de_control``: ningún texto debe traer caracteres de control (salvo el salto de línea): típico de una ruta de Windows con ``\\a``, ``\\t`` o ``\\f`` en una cadena
  no cruda (``scripts\\ep3\\arrancar_app.bat`` -> ``\\a`` es el carácter de campana).
* ``constantes_con_control``: lo mismo, pero mirando las cadenas de un script Python (para encontrar la causa en los generadores).
"""
from __future__ import annotations

import ast
import re
import warnings
from pathlib import Path

_SEPARADOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


def _celdas(linea: str) -> int:
    """Número de celdas de una fila de tabla (las barras escapadas no cuentan; las de los bordes tampoco)."""
    s = linea.strip()
    marcador = "\ue000"
    s = s.replace("\\|", marcador)
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return s.count("|") + 1


def problemas_de_tablas(texto: str) -> list[str]:
    """Lista de problemas (vacía si todas las tablas están bien). Ignora los bloques de código."""
    lineas = texto.splitlines()
    problemas: list[str] = []
    en_codigo = False
    i = 0
    while i < len(lineas):
        l = lineas[i]
        if l.strip().startswith("```"):
            en_codigo = not en_codigo
        if not en_codigo and l.strip().startswith("|") and i + 1 < len(lineas) and _SEPARADOR.match(lineas[i + 1]) and "|" in lineas[i + 1]:
            n = _celdas(l)
            if _celdas(lineas[i + 1]) != n:
                problemas.append(f"línea {i + 2}: el separador tiene {_celdas(lineas[i + 1])} celdas y la cabecera {n}: {l.strip()[:90]}")
            j = i + 2
            while j < len(lineas) and lineas[j].strip().startswith("|"):
                if _celdas(lineas[j]) != n:
                    problemas.append(f"línea {j + 1}: {_celdas(lineas[j])} celdas y la cabecera tiene {n}: {lineas[j].strip()[:90]}")
                j += 1
            i = j
            continue
        i += 1
    return problemas


def caracteres_de_control(texto: str) -> list[tuple[int, str]]:
    """(número de línea, código) de cada carácter de control distinto del salto de línea."""
    out = []
    for n, linea in enumerate(texto.split("\n"), 1):
        for c in linea:
            if ord(c) < 32:
                out.append((n, f"U+{ord(c):04X}"))
    return out


def constantes_con_control(ruta: Path) -> list[tuple[int, str]]:
    """Cadenas del script ``ruta`` que contienen caracteres de control (salvo el salto de línea): casi siempre una ruta de Windows mal escapada."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")                       # un «\S» suelto en un docstring no es un carácter de control: no ensuciar la salida
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    out = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            for c in nodo.value:
                if ord(c) < 32 and c != "\n":
                    out.append((nodo.lineno, f"U+{ord(c):04X} en {nodo.value[max(0, nodo.value.index(c) - 25):nodo.value.index(c) + 12]!r}"))
                    break
    return out


def revisar_carpeta(carpeta: Path) -> dict[str, list[str]]:
    """Revisa todos los .md de ``carpeta`` (tablas y caracteres de control); devuelve {archivo: problemas} solo con los que tienen problemas."""
    res: dict[str, list[str]] = {}
    for md in sorted(carpeta.glob("*.md")):
        t = md.read_text(encoding="utf-8")
        p = [f"tabla: {x}" for x in problemas_de_tablas(t)] + [f"carácter de control {c} en la línea {n}" for n, c in caracteres_de_control(t)]
        if p:
            res[md.name] = p
    return res
