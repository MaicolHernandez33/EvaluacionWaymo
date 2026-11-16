"""F19-C1 y C3: revisa los documentos Markdown de docs/ep3 (tablas con el mismo numero de celdas que su cabecera; sin caracteres de control) y las cadenas de los
generadores (rutas de Windows con \\a, \\t, \\f... sin escapar). Sale con codigo 1 si encuentra algo.
Uso: .venv\\Scripts\\python scripts/ep3/revisar_documentos.py
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.chequeo_md import constantes_con_control, revisar_carpeta  # noqa: E402


def main() -> None:
    mal = revisar_carpeta(RAIZ / "docs/ep3")
    fuentes = {str(p.relative_to(RAIZ)): constantes_con_control(p) for p in sorted((RAIZ / "scripts/ep3").glob("*.py"))}
    fuentes = {k: v for k, v in fuentes.items() if v}
    for archivo, ps in mal.items():
        print("MAL", archivo, *ps[:6], sep="\n   ")
    for archivo, ps in fuentes.items():
        print("CADENAS CON CARACTERES DE CONTROL en", archivo, *[str(x) for x in ps[:4]], sep="\n   ")
    print("documentos revisados:", len(list((RAIZ / "docs/ep3").glob("*.md"))), "| con problemas:", len(mal), "| scripts con cadenas sospechosas:", len(fuentes))
    sys.exit(1 if (mal or fuentes) else 0)


if __name__ == "__main__":
    main()
