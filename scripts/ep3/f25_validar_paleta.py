"""F25: valida con ``validate_palette.js`` (skill dataviz) el mapa único entidad -> color de los flujos y deja la salida en ``docs/ep3/f25_paleta_validacion.json``.

Modo oscuro, superficie = panel (``TOKENS["panel"]``), todos los pares. Valida: (a) los tres colores cromáticos de los flujos (solo cola, auditoría + cola, solo celdas sanas); (b) el gris de
«revisión sin orden» como línea base neutra (el piso de croma de una paleta categórica no aplica a un gris: se registra el contraste contra el panel); (c) las cinco curvas de la cola, que no cambian;
(d) la unión de ambas (informativa). Los colores salen de ``app/estilos.py``; la herramienta se pasa con ``--validador`` (la ruta de ``validate_palette.js`` dentro de la skill).
Uso: .venv\Scripts\python scripts/ep3/f25_validar_paleta.py --validador <ruta>/validate_palette.js
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
import estilos as E  # noqa: E402

SALIDA = RAIZ / "docs/ep3/f25_paleta_validacion.json"


def correr(validador: Path, colores: list[str], extra: list[str] | None = None) -> str:
    r = subprocess.run(["node", str(validador), ",".join(colores), "--mode", "dark", "--surface", E.TOKENS["panel"], *(extra or [])], capture_output=True, text=True, encoding="utf-8", check=False)
    return (r.stdout + r.stderr).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validador", type=Path, required=True)
    a = ap.parse_args()
    f = E.FLUJOS_COLORES
    cromaticos = [f["Solo cola (un paso)"], f["Auditoría + cola (dos pasos)"], f["Solo celdas sanas, sin auditoría"]]
    union = list(dict.fromkeys([*cromaticos, *E.CURVAS_COLORES]))
    datos = {
        "herramienta": "validate_palette.js de la skill dataviz (CVD Machado 2009, OKLab x100)", "modo": "dark", "superficie": E.TOKENS["panel"],
        "mapa_entidad_color": f,
        "flujos_cromaticos": {"paleta": cromaticos, "todos_los_pares": correr(a.validador, cromaticos, ["--pairs", "all"])},
        "gris_linea_base": {"color": f["Revisión sin orden"], "contraste_contra_el_panel": round(E.contraste(f["Revisión sin orden"], E.TOKENS["panel"]), 2),
                            "nota": "el gris es la línea base neutra: no entra a la prueba de croma de una paleta categórica; se distingue de los tres por croma y lleva rótulo en cada barra", "salida": correr(a.validador, [f["Revisión sin orden"]])},
        "curvas_de_la_cola_sin_cambios": {"paleta": E.CURVAS_COLORES, "todos_los_pares": correr(a.validador, E.CURVAS_COLORES, ["--pairs", "all"])},
        "union_informativa": {"paleta": union, "todos_los_pares": correr(a.validador, union, ["--pairs", "all"]),
                              "lectura": "el color de «solo celdas sanas» no repite ninguno de los de las curvas; queda cerca del rosa de E2 (ΔE 7,8 en visión normal), pero no comparten gráfico: E2 solo se dibuja en las curvas de la Cola y las barras de Validación llevan leyenda con rótulo"},
    }
    SALIDA.write_text(json.dumps(datos, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: (v if not isinstance(v, dict) else list(v)) for k, v in datos.items() if k != "herramienta"}, ensure_ascii=False)[:600])


if __name__ == "__main__":
    main()
