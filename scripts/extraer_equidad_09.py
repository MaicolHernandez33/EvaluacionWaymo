"""Extrae una sola vez las brechas de equidad con IC del notebook 09 ya ejecutado.

Uso: .venv/Scripts/python.exe -X utf8 scripts/extraer_equidad_09.py
Lee la linea '<grupo A> menos <grupo B>: segmentos {...} | filas {...} | AUC x (IC a a b) | recall al punto A y (IC a c d)'
de las salidas del notebook 09 y escribe data/08_reporting/09_equidad_brechas.json. No reentrena nada.
Falla con un mensaje claro si no encuentra ninguna linea con ese formato.
"""
import json
import re
import sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
NB = R / "notebooks" / "09_modelos_supervisados_sin_camara.ipynb"
SALIDA = R / "data" / "08_reporting" / "09_equidad_brechas.json"
PATRON = re.compile(r"^(?P<a>[\w/]+) menos (?P<b>[\w/]+): segmentos \{[^}]*\} \| filas \{[^}]*\} \| AUC (?P<auc>[+\-][\d.]+) \(IC (?P<alo>[+\-][\d.]+) a (?P<ahi>[+\-][\d.]+)\) \| recall al punto A (?P<rec>[+\-][\d.]+) \(IC (?P<rlo>[+\-][\d.]+) a (?P<rhi>[+\-][\d.]+)\)", re.M)


def main():
    if not NB.exists():
        sys.exit(f"ERROR: no existe {NB.relative_to(R)}; ejecuta el notebook 09 primero.")
    texto = "\n".join("".join(o["text"]) for c in json.loads(NB.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code"
                      for o in c.get("outputs", []) if o["output_type"] == "stream")
    filas = []
    for m in PATRON.finditer(texto):
        g = m.groupdict()
        f = {k: float(g[k]) for k in ("auc", "alo", "ahi", "rec", "rlo", "rhi")}
        filas.append({"grupo": g["a"], "referencia": g["b"], "auc_dif": f["auc"], "auc_lo": f["alo"], "auc_hi": f["ahi"], "auc_incluye_0": f["alo"] <= 0 <= f["ahi"],
                      "recall_dif": f["rec"], "recall_lo": f["rlo"], "recall_hi": f["rhi"], "recall_incluye_0": f["rlo"] <= 0 <= f["rhi"]})
    if not filas:
        sys.exit("ERROR: no se encontro ninguna linea '<A> menos <B>: segmentos {...} | filas {...} | AUC ... | recall al punto A ...' en las salidas del notebook 09.")
    SALIDA.write_text(json.dumps({"fuente": "salidas de texto del notebook 09 (extraidas una vez, sin reentrenar)", "brechas": filas}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Escrito {SALIDA.relative_to(R)} con {len(filas)} brechas")


if __name__ == "__main__":
    main()
