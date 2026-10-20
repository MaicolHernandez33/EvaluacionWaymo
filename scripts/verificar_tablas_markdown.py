"""Cuenta las tablas Markdown con filas de distinto numero de celdas en uno o mas archivos .md.

Uso: .venv/Scripts/python.exe -X utf8 scripts/verificar_tablas_markdown.py docs/evaluacion_final_B.md [otro.md ...]

Una tabla es un bloque de lineas consecutivas que empiezan con '|'. Las barras escapadas (\\|) no cuentan como separador
y las barras dentro de `codigo` tampoco. Devuelve codigo de salida 1 si algun archivo tiene tablas desiguales.
"""
import re
import sys
from pathlib import Path


def celdas(linea):
    linea = linea.strip()
    linea = re.sub(r"`[^`]*`", "x", linea)          # barras dentro de codigo en linea
    linea = linea.replace("\\|", "")                 # barras escapadas
    n = linea.count("|")
    if linea.startswith("|"):
        n -= 1
    if linea.endswith("|") and len(linea) > 1:
        n -= 0
    return linea.count("|") - 1 if linea.startswith("|") and linea.endswith("|") else linea.count("|")


def tablas(texto):
    bloque, ini = [], 0
    for i, l in enumerate(texto.splitlines(), 1):
        if l.lstrip().startswith("|"):
            if not bloque:
                ini = i
            bloque.append(l)
        elif bloque:
            yield ini, bloque
            bloque = []
    if bloque:
        yield ini, bloque


def analizar(ruta):
    texto = Path(ruta).read_text(encoding="utf-8")
    total, malas = 0, []
    for ini, b in tablas(texto):
        total += 1
        n = {celdas(l) for l in b}
        if len(n) > 1:
            malas.append((ini, sorted(n)))
    return total, malas


if __name__ == "__main__":
    codigo = 0
    for ruta in sys.argv[1:]:
        total, malas = analizar(ruta)
        print(f"{ruta}: {total} tablas, {len(malas)} con filas de distinto numero de celdas")
        for ini, n in malas:
            print(f"  linea {ini}: celdas por fila {n}")
        codigo |= bool(malas)
    sys.exit(codigo)
