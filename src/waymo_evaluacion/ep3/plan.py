"""Acceso al plan v3 congelado: carga del JSON y verificación de su sha256."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ARCHIVOS_PLAN = ("plan_v3.md", "plan_v3.json")
RAIZ = Path(__file__).resolve().parents[3]


def sha256_archivo(ruta: Path) -> str:
    """Calcula el sha256 de un archivo leyéndolo por bloques."""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_hashes(carpeta: Path) -> dict[str, str]:
    """Lee ``plan_v3.sha256`` (líneas ``hash  nombre``) como diccionario nombre -> hash."""
    salida: dict[str, str] = {}
    for linea in (carpeta / "plan_v3.sha256").read_text(encoding="utf-8").splitlines():
        partes = linea.split()
        if len(partes) == 2:
            salida[partes[1]] = partes[0]
    return salida


def verificar_plan_v3(raiz: Path = RAIZ) -> dict[str, str]:
    """Verifica que el plan v3 no cambió desde que se congeló.

    Args:
        raiz: raíz del repositorio.

    Returns:
        Diccionario nombre -> sha256 verificado.

    Raises:
        RuntimeError: si falta un archivo o algún hash no coincide.
    """
    carpeta = raiz / "docs" / "ep3"
    esperados = leer_hashes(carpeta)
    for nombre in ARCHIVOS_PLAN:
        if nombre not in esperados:
            raise RuntimeError(f"{nombre} no figura en plan_v3.sha256")
        real = sha256_archivo(carpeta / nombre)
        if real != esperados[nombre]:
            raise RuntimeError(f"el plan v3 cambió: {nombre} ya no coincide con su sha256 congelado")
    return esperados


def cargar_plan_v3(raiz: Path = RAIZ) -> dict[str, Any]:
    """Verifica el hash y devuelve el contenido de ``plan_v3.json``."""
    verificar_plan_v3(raiz)
    return json.loads((raiz / "docs" / "ep3" / "plan_v3.json").read_text(encoding="utf-8"))
