"""Verifica el artefacto no supervisado (scaler y KMeans): sha256 contra manifest_no_supervisado.json.

Uso: python scripts/ep3/verificar_no_supervisado.py   (codigo de salida 1 si algo no coincide)
Independiente de manifest_v3.json y de verificar_congelados_v3.py. Descriptivo, post hoc, no pre-declarado.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MOD = RAIZ / "data/06_models_ep3"
if len(sys.argv) > 1:
    MOD = Path(sys.argv[1])


def main() -> None:
    ruta = MOD / "manifest_no_supervisado.json"
    if not ruta.exists():
        sys.exit(f"FALTA {ruta}")
    man = json.loads(ruta.read_text(encoding="utf-8"))
    mal = []
    for n, h in man["sha256"].items():
        f = MOD / n
        ok = f.exists() and hashlib.sha256(f.read_bytes()).hexdigest() == h
        print(("IGUAL    " if ok else "DISTINTO ") + n)
        if not ok:
            mal.append(n)
    print(f"no supervisado (k = {man['k_elegido']}, creado {man['creado']}): coinciden {len(man['sha256']) - len(mal)} de {len(man['sha256'])} archivos")
    if mal:
        sys.exit(1)


if __name__ == "__main__":
    main()
