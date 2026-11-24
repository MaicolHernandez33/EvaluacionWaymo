"""Carga y calentamiento de la pagina (F19-B9): los datos y la solucion congelada se cargan UNA vez por proceso, en un hilo, para que ninguna seccion pague la carga fria.

Las funciones ``datos``, ``artefactos``, ``no_sup`` y ``rangos`` guardan su resultado por carpeta con un candado por clave (si el hilo de calentamiento y una visita piden lo mismo
a la vez, se carga una sola vez). ``iniciar`` lanza el calentamiento en un hilo (una sola vez por par de carpetas): lee los datos, carga los modelos y ejecuta una vez cada camino
costoso (puntuar una caja, el tipo de caso, la cola) para que no se pague en la primera visita. No hace ninguna conexion externa. ``app/lanzar.py`` lo arranca antes de abrir
el servidor; con ``streamlit run app/app.py`` empieza con la primera visita.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from waymo_evaluacion.ep3.app_logica import cargar_datos, cargar_min_cajas, cargar_no_supervisado, cargar_rangos

_cache: dict[tuple, Any] = {}
_candados: dict[tuple, threading.Lock] = defaultdict(threading.Lock)
_hilos: dict[tuple, threading.Thread] = {}
_estado: dict[str, Any] = {"segundos": None, "error": None, "listo": threading.Event()}
_guarda = threading.Lock()


def _una_vez(clave: tuple, fabrica: Callable[[], Any]) -> Any:
    with _candados[clave]:
        if clave not in _cache:
            _cache[clave] = fabrica()
        return _cache[clave]


def datos(carpeta: str) -> dict:
    return _una_vez(("datos", carpeta), lambda: cargar_datos(Path(carpeta)))


def artefactos(carpeta: str):
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos

    return _una_vez(("artefactos", carpeta), lambda: cargar_artefactos(Path(carpeta)))


def no_sup(carpeta: str):
    return _una_vez(("no_sup", carpeta), lambda: cargar_no_supervisado(Path(carpeta)))


def rangos(carpeta: str) -> dict:
    return _una_vez(("rangos", carpeta), lambda: cargar_rangos(Path(carpeta)))


def min_cajas(carpeta: str) -> int:
    return _una_vez(("min_cajas", carpeta), lambda: cargar_min_cajas(Path(carpeta)))


def _calentar(carpeta_datos: str, carpeta_modelos: str) -> None:
    import numpy as np

    from waymo_evaluacion.ep3.app_logica import resumen_cola, tabla_cola, tipo_de_caso
    from waymo_evaluacion.ep3.inferencia import V16

    t0 = time.time()
    try:
        D = datos(carpeta_datos)
        rg = rangos(carpeta_modelos)
        resumen = resumen_cola(D["cajas"], D["curva"], D["kpis"].get("nombre_curva", "solucion"), "Todos", 0.2, 20)
        tabla_cola(resumen["top"], resumen["cajas_cola_total"], rg)
        art = artefactos(carpeta_modelos)
        fila = D["cajas"][V16].median().to_frame().T
        s = art.puntuador.puntuar(fila)
        if art.calibrador is not None:
            art.calibrador.calibrar(np.asarray(s, dtype=float))
        ns = no_sup(carpeta_modelos)
        if ns is not None:
            tipo_de_caso(fila.copy(), ns)
    except Exception as e:  # noqa: BLE001 - el calentamiento es una ayuda: si falla, las secciones cargan por su cuenta y muestran su propio error
        _estado["error"] = f"{type(e).__name__}: {e}"
    finally:
        _estado["segundos"] = round(time.time() - t0, 2)
        _estado["listo"].set()
        print(f"[precarga] terminada en {_estado['segundos']} s" + (f" (con aviso: {_estado['error']})" if _estado["error"] else ""), flush=True)


def iniciar(carpeta_datos: str, carpeta_modelos: str) -> threading.Thread:
    """Lanza el calentamiento en un hilo si todavia no se lanzo para este par de carpetas; devuelve el hilo."""
    clave = (carpeta_datos, carpeta_modelos)
    with _guarda:
        if clave not in _hilos:
            h = threading.Thread(target=_calentar, args=clave, name="precarga", daemon=True)
            _hilos[clave] = h
            h.start()
        return _hilos[clave]


def estado() -> dict[str, Any]:
    """Segundos que tardo el calentamiento, aviso si fallo, y si ya termino."""
    return {"segundos": _estado["segundos"], "error": _estado["error"], "listo": _estado["listo"].is_set()}
