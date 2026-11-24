"""F23: integridad del sello. SOLO LECTURA sobre todo lo sellado (calcula sha256 y mira ``git status``); escribe unicamente ``docs/ep3/f23_sello_antes.json`` (con ``--antes``)
o ``docs/ep3/f23_sello_despues.json`` (con ``--comprobar``).

Cubre lo que la regla 2 de F23 declara intocable: ``artefactos_ep3/``, ``docs/ep3/plan_seleccion_ep3.json`` y ``.sha256``, ``notebooks/00b_*``, los scripts y modulos de la validacion externa,
y (por hash, sin tocarlos) los manifests y modelos congelados de ``data/06_models_ep3``, ``data/06_models`` (EP2) y ``data/05_model_input``.
No ejecuta ``ingesta_nuevos.py`` ni ``evaluar_sellado.py``. Uso:  .venv\\Scripts\\python scripts/ep3/f23_integridad_sello.py --antes | --comprobar
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ANTES = RAIZ / "docs/ep3/f23_sello_antes.json"
ETIQUETA_POR_DEFECTO = "f23"            # F24 usa --etiqueta f24: compara contra el mismo registro de F23 y escribe docs/ep3/f24_sello_despues.json

CARPETAS = ["artefactos_ep3", "data/06_models_ep3", "data/06_models", "data/05_model_input"]
ARCHIVOS = ["docs/ep3/plan_seleccion_ep3.json", "docs/ep3/plan_seleccion_ep3.sha256", "scripts/ep3/evaluar_sellado.py", "scripts/ep3/plan_seleccion_ep3.py", "scripts/ep3/copiar_sello_a_artefactos.py",
            "scripts/ep3/ingesta_nuevos.py", "src/waymo_evaluacion/ep3/sellado.py", "src/waymo_evaluacion/ep3/seleccion_nuevos.py", "src/waymo_evaluacion/ep3/ingesta_nuevos.py"]
PATRONES = ["notebooks/00b_*"]
PROHIBIDOS_GIT = tuple(CARPETAS) + ("artefactos_ep3/",) + tuple(ARCHIVOS) + ("notebooks/00b_",)


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def archivos_sellados() -> list[Path]:
    rutas: list[Path] = []
    for c in CARPETAS:
        base = RAIZ / c
        if base.exists():
            rutas += [p for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    rutas += [RAIZ / a for a in ARCHIVOS if (RAIZ / a).exists()]
    for patron in PATRONES:
        rutas += [p for p in RAIZ.glob(patron) if p.is_file()]
    return sorted(set(rutas))


def instantanea() -> dict[str, str]:
    return {p.relative_to(RAIZ).as_posix(): sha256(p) for p in archivos_sellados()}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=False, encoding="utf-8").stdout


def git_toca_lo_sellado() -> list[str]:
    """Lineas de ``git status --short`` que mencionan una ruta sellada (solo lectura)."""
    salida = git("status", "--short")
    return [linea for linea in salida.splitlines() if any(linea[3:].replace("\\", "/").startswith(p) for p in PROHIBIDOS_GIT)]


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--antes", action="store_true")
    g.add_argument("--comprobar", action="store_true")
    ap.add_argument("--etiqueta", default=ETIQUETA_POR_DEFECTO, help="prefijo del archivo de resultado (f23_sello_despues.json por defecto)")
    a = ap.parse_args()
    DESPUES = RAIZ / f"docs/ep3/{a.etiqueta}_sello_despues.json"
    ahora = instantanea()
    if a.antes:
        ANTES.write_text(json.dumps({"archivos": ahora, "n": len(ahora), "git_head": git("rev-parse", "--short", "HEAD").strip()}, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"escritos {len(ahora)} hashes en {ANTES.relative_to(RAIZ)}")
        return 0
    antes = json.loads(ANTES.read_text(encoding="utf-8"))["archivos"]
    cambiados = sorted(k for k in antes if k in ahora and ahora[k] != antes[k])
    faltan = sorted(k for k in antes if k not in ahora)
    nuevos = sorted(k for k in ahora if k not in antes)
    git_sellado = git_toca_lo_sellado()
    resultado = {"archivos_comparados": len(antes), "cambiados": cambiados, "faltan": faltan, "nuevos": nuevos, "git_status_sobre_lo_sellado": git_sellado,
                 "intacto": not (cambiados or faltan or nuevos or git_sellado)}
    DESPUES.write_text(json.dumps(resultado, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resultado, indent=1, ensure_ascii=False))
    return 0 if resultado["intacto"] else 1


if __name__ == "__main__":
    sys.exit(main())
