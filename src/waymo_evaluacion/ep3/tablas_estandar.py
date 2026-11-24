"""Tabla estándar de la página (F34): una sola forma de armar y formatear las tablas de Validación y de Puntuar. Funciones puras (sin Streamlit).

Reglas (prompt de F34): hasta 25 filas se muestran todas y, con más, se pagina de 25 en 25; los intervalos van en UNA columna («0,797 (0,701–0,889)») y los valores separados quedan en el CSV;
encabezados de tres palabras como máximo con el nombre completo en un ``title``; números a la derecha con decimales fijos por tipo (AUC, PR-AUC, Brier y diferencias con 3; porcentajes con 1;
recuentos con punto de miles; coma decimal); signo menos único («−») y «+» en las diferencias positivas; el CSV lleva TODAS las columnas con los valores sin redondear.

``construir_tabla`` recibe el DataFrame crudo de la evidencia y su especificación (lista de ``Col``); ``columnas_de_pantalla`` son las que se ven y el CSV trae las demás.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd

from waymo_evaluacion.ep3 import formato as F

POR_PAGINA = 25
DERECHA = {"auc", "dif", "pct", "pct0", "pts", "int", "entrunc", "num", "plain", "dec1", "ratio", "de5", "valor"}      # tipos que se alinean a la derecha (con cifras tabulares)
SI, NO = "✓ Sí", "✕ No"                          # símbolo y texto: el estado nunca va solo por color


@dataclass(frozen=True)
class Col:
    """Una columna de pantalla: ``clave`` de los datos, encabezado corto, nombre completo (``tip``), tipo de formato y, si lleva intervalo, las claves de su límite inferior y superior."""

    clave: str
    encabezado: str
    tipo: str = "text"
    tip: str = ""
    lo: str | None = None
    hi: str | None = None
    extra: str | None = None          # segunda clave para ``ratio`` («21 de 31»)


@dataclass
class Tabla:
    clave: str
    titulo: str
    responde: str
    columnas: list[Col]
    filas: Any                          # lista de filas ya formateadas, o una secuencia que formatea solo la página pedida (``len`` y rebanadas)
    csv: Any                            # bytes, o una función sin argumentos que los arma al pulsar «Descargar CSV»
    nota: str = ""
    columnas_en_csv: int = 0           # cuántas columnas de los datos solo van en la descarga

    @property
    def n_filas(self) -> int:
        return len(self.filas)

    def derecha(self, i: int) -> bool:
        return self.columnas[i].tipo in DERECHA


def _vacio(v: Any) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, str) and v == "")


def _un(tipo: str, v: Any) -> str:
    """Un valor ya formateado según su tipo; sin dato, «—»."""
    if _vacio(v):
        return "—"
    if tipo == "auc":
        return F.menos(F.decimal(v, 3))
    if tipo == "dif":
        return F.decimal_signado(v, 3)
    if tipo == "pct":
        return F.menos(F.porcentaje(v, 1))
    if tipo == "pct0":
        return F.menos(F.porcentaje(v, 0))
    if tipo == "pts":                                   # una diferencia de fracciones, en puntos porcentuales: «−15,0 puntos»
        return F.decimal_signado(100 * float(v), 1) + " puntos"
    if tipo == "int":
        return F.menos(F.entero(v))
    if tipo == "plain":
        return str(int(round(float(v))))
    if tipo == "num":
        return F.menos(F.numero_legible(v))
    if tipo == "dec1":
        return F.menos(F.decimal(v, 1))
    if tipo == "bool":
        return SI if bool(v) else NO
    if tipo == "sino":
        return "sí" if bool(v) else "no"
    if tipo == "cand":
        return str(F.texto_visible(F.nombre_visible(str(v))))
    if tipo == "comp":
        return str(F.texto_visible(F.nombre_componente(v)))
    if tipo == "hip":
        return F.HIPERPARAMETROS.get(str(v), str(v).replace("_", " "))
    if tipo == "etapa":
        return F.VALORES_TEXTO.get(str(v), str(v))
    if tipo == "seg":
        return str(F.segmento_corto(str(int(v)) if isinstance(v, (int, float)) and float(v) == int(float(v)) else str(v)))
    if tipo == "entrunc":                               # recuento que se muestra sin decimales truncando (6.059,5 -> 6.059), igual que las tarjetas de otras páginas
        return F.entero(math.floor(float(v)))
    if tipo == "valor":
        return str(F.texto_visible(str(v)))
    return str(F.texto_visible(str(v).replace("_", " ")))


def _con_intervalo(tipo: str, v: Any, lo: Any, hi: Any) -> str:
    """«valor (inferior–superior)»; con signo (diferencias) el rango lleva «a» para no confundir el guion con el signo menos."""
    if _vacio(v):
        return "—"
    if tipo == "pct":
        return f"{_un(tipo, v)} ({F.menos(F.decimal(100 * float(lo), 1))}–{F.menos(F.decimal(100 * float(hi), 1))})"
    if tipo == "pts":
        return f"{_un(tipo, v)} ({F.decimal_signado(100 * float(lo), 1)} a {F.decimal_signado(100 * float(hi), 1)})"
    if tipo == "entrunc":
        return f"{_un(tipo, v)} ({_un(tipo, lo)}–{_un(tipo, hi)})"
    if tipo == "dif":
        return f"{_un(tipo, v)} ({_un(tipo, lo)} a {_un(tipo, hi)})"
    return f"{_un(tipo, v)} ({_un(tipo, lo)}–{_un(tipo, hi)})"


def celda(col: Col, fila: pd.Series) -> str:
    v = fila[col.clave]
    if col.tipo == "ratio":
        return "—" if _vacio(v) else (f"{F.entero(v)} de {F.entero(fila[col.extra])}" if col.extra else F.entero(v))
    if col.tipo == "de5":
        return "—" if _vacio(v) else f"{int(v)} de 5"
    if col.lo and col.hi:
        return _con_intervalo(col.tipo, v, fila[col.lo], fila[col.hi])
    return _un(col.tipo, v)


def construir_tabla(clave: str, df: pd.DataFrame, columnas: list[Col], titulo: str, responde: str, nota: str = "", transformar: Callable[[pd.DataFrame], pd.DataFrame] | None = None) -> Tabla:
    """Arma la ``Tabla`` de pantalla y su CSV (con todas las columnas y los valores sin redondear). ``transformar`` puede reordenar o filtrar las filas antes de formatear."""
    base = transformar(df) if transformar else df
    presentes = []
    for c in columnas:                              # las columnas que no están en los datos se omiten; un intervalo sin sus límites se muestra solo con el valor
        if c.clave not in base.columns:
            continue
        lo, hi = (c.lo, c.hi) if c.lo in base.columns and c.hi in base.columns else (None, None)
        presentes.append(Col(c.clave, c.encabezado, c.tipo, c.tip, lo, hi, c.extra if c.extra in base.columns else None))
    columnas = presentes
    filas = [[celda(c, r) for c in columnas] for _, r in base.iterrows()]
    usadas = {c.clave for c in columnas} | {c.lo for c in columnas if c.lo} | {c.hi for c in columnas if c.hi} | {c.extra for c in columnas if c.extra}
    return Tabla(clave, titulo, responde, columnas, filas, df.to_csv(index=False).encode("utf-8"), nota, columnas_en_csv=len([c for c in df.columns if c not in usadas]))


def tabla_de_listas(clave: str, titulo: str, responde: str, columnas: list[Col], filas: list[list[str]], csv_df: pd.DataFrame | None = None, nota: str = "") -> Tabla:
    """Tabla ya formateada (por ejemplo la de resultados clave o la de candidatos); el CSV es ``csv_df`` o las propias filas."""
    datos = csv_df if csv_df is not None else pd.DataFrame(filas, columns=[c.encabezado for c in columnas])
    return Tabla(clave, titulo, responde, columnas, [[str(F.menos(x)) for x in f] for f in filas], datos.to_csv(index=False).encode("utf-8"), nota)


def paginas(n_filas: int, por_pagina: int = POR_PAGINA) -> int:
    """Cuántas páginas de ``por_pagina`` filas hay (siempre al menos una)."""
    return max(1, -(-n_filas // por_pagina))


def pagina(filas: list[list[str]], numero: int, por_pagina: int = POR_PAGINA) -> list[list[str]]:
    """Las filas de la página ``numero`` (desde 1; se acota al rango válido)."""
    n = min(max(1, numero), paginas(len(filas), por_pagina))
    return filas[(n - 1) * por_pagina:n * por_pagina]


def texto_filas(t: Tabla, por_pagina: int = POR_PAGINA) -> str:
    """«N filas» o «Filas 1 a 25 de 41» según haga falta paginar (el número exacto de la página lo pone la interfaz)."""
    return f"{F.entero(t.n_filas)} {'fila' if t.n_filas == 1 else 'filas'}"


def texto_rango(t: Tabla, numero: int, por_pagina: int = POR_PAGINA) -> str:
    n = min(max(1, numero), paginas(t.n_filas, por_pagina))
    ini, fin = (n - 1) * por_pagina + 1, min(n * por_pagina, t.n_filas)
    return f"Filas {F.entero(ini)} a {F.entero(fin)} de {F.entero(t.n_filas)}"
