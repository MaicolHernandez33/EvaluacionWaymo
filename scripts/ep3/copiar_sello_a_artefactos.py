r"""F19-A5: copia a artefactos_ep3/ (carpeta versionable) los archivos del sello, para COMMITEARLOS antes de evaluar:
manifest_nuevos.json (tras `evaluar_sellado.py congelar`), manifest_alternativas.json, manifest_v3.json y la lista de segmentos (sin datos por caja).
Uso: .venv\Scripts\python scripts/ep3/copiar_sello_a_artefactos.py --lista CARPETA\segmentos_nuevos_ep3.csv
Comprueba los sha256 contra los manifests antes de copiar y se niega a copiar si algo no coincide. No escribe en data/.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.plan import sha256_archivo  # noqa: E402
from waymo_evaluacion.ep3.sellado import verificar_sellado  # noqa: E402

MOD, ART = RAIZ / "data/06_models_ep3", RAIZ / "artefactos_ep3"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lista", type=Path, help="segmentos_nuevos_ep3.csv (si ya hay manifest_nuevos.json)")
    ap.add_argument("--modelos", type=Path, default=MOD)
    ap.add_argument("--destino", type=Path, default=ART)
    a = ap.parse_args(argv)
    copias: list[tuple[Path, str]] = [(a.modelos / "manifest_v3.json", "manifest_v3.json")]
    alt = a.modelos / "manifest_alternativas.json"
    if alt.exists():
        copias.append((alt, "manifest_alternativas.json"))
    mn = a.modelos / "manifest_nuevos.json"
    if mn.exists():
        if a.lista is None:
            sys.exit("DETENIDO: existe manifest_nuevos.json; indique --lista para verificar y copiar tambien la lista de segmentos.")
        verificar_sellado(a.lista, a.modelos, mn)          # falla si algo cambio desde que se congelo
        copias += [(mn, "manifest_nuevos.json"), (a.lista, "segmentos_nuevos_ep3.csv")]
    elif a.lista is not None:
        sys.exit("DETENIDO: todavia no hay manifest_nuevos.json: corra primero `evaluar_sellado.py congelar`.")
    a.destino.mkdir(parents=True, exist_ok=True)
    for origen, nombre in copias:
        shutil.copy2(origen, a.destino / nombre)
        print(f"copiado {nombre}  sha256 {sha256_archivo(a.destino / nombre)[:16]}...")
    print("Ahora COMMITEE estos archivos de", a.destino, "ANTES de ejecutar `evaluar_sellado.py evaluar`.")


if __name__ == "__main__":
    main()
