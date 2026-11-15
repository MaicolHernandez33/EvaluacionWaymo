"""F18-A6 (post hoc, descriptivo): sesgo de seleccion a escala de segmento, desde docs/seleccion_segmentos/registro_verificacion_ep2.csv (solo lectura).

De los 91 segmentos evaluados en EP2, 41 se seleccionaron y 50 se descartaron (asociacion vacia, etiquetado ralo, pocas asociaciones). Escribe
data/08_reporting_ep3/f18_seleccion_motivos.csv y f18_seleccion_rendimiento.csv. La causa (etiquetado o publicacion) es desconocida.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
REP = RAIZ / "data/08_reporting_ep3"


def motivo_corto(m) -> str:
    if not isinstance(m, str) or not m:
        return "seleccionado"
    return "etiquetado ralo" if m.startswith("etiquetado ralo") else ("asociación vacía" if m.startswith("asociacion vacia") else ("pocas asociaciones" if m.startswith("pocas asociaciones") else m))


def main() -> None:
    r = pd.read_csv(RAIZ / "docs/seleccion_segmentos/registro_verificacion_ep2.csv")
    inv = pd.read_csv(RAIZ / "docs/seleccion_segmentos/inventario_segmentos.csv")
    r["motivo_corto"] = r["motivo"].map(motivo_corto)
    mot = r.groupby("motivo_corto").size().rename("segmentos").reset_index()
    mot["pct_de_los_91"] = mot["segmentos"] / len(r)
    mot.to_csv(REP / "f18_seleccion_motivos.csv", index=False)
    filas = []
    for nombre, claves in (("momento_del_dia", ["time_of_day"]), ("ubicacion", ["location"]), ("momento_x_ubicacion", ["time_of_day", "location"])):
        g = r.groupby(claves)
        t = pd.DataFrame({"evaluados": g.size(), "seleccionados": g["resultado"].apply(lambda s: int((s == "seleccionado").sum())), "descartados": g["resultado"].apply(lambda s: int((s == "descartado").sum())),
                          "asociacion_vacia": g["motivo_corto"].apply(lambda s: int((s == "asociación vacía").sum())), "etiquetado_ralo": g["motivo_corto"].apply(lambda s: int((s == "etiquetado ralo").sum())),
                          "pocas_asociaciones": g["motivo_corto"].apply(lambda s: int((s == "pocas asociaciones").sum()))})
        t["rendimiento"] = t["seleccionados"] / t["evaluados"]
        t = t.reset_index()
        t.insert(0, "corte", nombre)
        t["grupo"] = t[claves].astype(str).agg(" / ".join, axis=1)
        filas.append(t.drop(columns=claves))
    out = pd.concat(filas, ignore_index=True)[["corte", "grupo", "evaluados", "seleccionados", "descartados", "asociacion_vacia", "etiquetado_ralo", "pocas_asociaciones", "rendimiento"]]
    out.to_csv(REP / "f18_seleccion_rendimiento.csv", index=False)
    res = {"inventario": int(len(inv)), "evaluados": int(len(r)), "seleccionados": int((r["resultado"] == "seleccionado").sum()), "descartados": int((r["resultado"] == "descartado").sum()),
           "nota": "descriptivo; la causa (etiquetado o publicacion) es desconocida; el detector solo se evaluo en segmentos con etiquetado denso"}
    (REP / "f18_seleccion_resumen.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    pd.set_option("display.width", 220)
    print(mot.to_string(index=False)); print(out.round(3).to_string(index=False)); print(res)


if __name__ == "__main__":
    main()
