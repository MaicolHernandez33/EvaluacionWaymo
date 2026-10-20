"""Extrae una sola vez las cifras de aprendizaje no supervisado del notebook 08 ya ejecutado.

Uso (desde la raiz del repositorio):

    .venv/Scripts/python.exe -X utf8 scripts/extraer_no_supervisado_08.py

Lee las salidas de texto del notebook `notebooks/08_analisis_observabilidad_sin_camara.ipynb` (ya ejecutado) y escribe
`data/08_reporting/08_no_supervisado_resumen.json`. No reentrena nada y no reejecuta el notebook (reejecutarlo
reescribiria `features_B.parquet`, cuyo sha256 esta congelado en el plan de evaluacion del test).

Si alguna linea no se encuentra, termina con un error claro que dice cual y en que formato se esperaba.
"""
import ast
import json
import re
import sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
NB = R / "notebooks" / "08_analisis_observabilidad_sin_camara.ipynb"
SALIDA = R / "data" / "08_reporting" / "08_no_supervisado_resumen.json"

PATRONES = {
    "k_elegido": (r"k elegido por maximo silhouette de KMeans: (\d+)", "k elegido por maximo silhouette de KMeans: <entero>"),
    "ari_entre_tecnicas": (r"Concordancia entre tecnicas \(ARI\): (\{[^}]*\})", "Concordancia entre tecnicas (ARI): {<diccionario>}"),
    "estabilidad": (r"Estabilidad por segmento \((\d+) remuestreos\): ARI medio ([\d.]+) \| minimo ([\d.]+)", "Estabilidad por segmento (<n> remuestreos): ARI medio <x> | minimo <y>"),
    "isolation_forest": (r"IsolationForest: (\d+) cajas atipicas \((\d+)%\) en (\d+) segmentos \| tasa de sin_camara ([\d.]+) vs ([\d.]+) en el resto",
                         "IsolationForest: <n> cajas atipicas (<p>%) en <s> segmentos | tasa de sin_camara <a> vs <b> en el resto"),
    "diferencia_con_signo": (r"Diferencia con signo \(cluster 0 menos cluster 1\): ([\d.\-]+) puntos \(IC 95% por segmentos ([\d.\-]+) a ([\d.\-]+); excluye 0: (True|False)\)",
                             "Diferencia con signo (cluster 0 menos cluster 1): <x> puntos (IC 95% por segmentos <lo> a <hi>; excluye 0: <True|False>)"),
}


def texto_salidas():
    if not NB.exists():
        sys.exit(f"ERROR: no existe {NB.relative_to(R)}; ejecuta el notebook 08 primero.")
    nb = json.loads(NB.read_text(encoding="utf-8"))
    partes = []
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        for o in c.get("outputs", []):
            if o["output_type"] == "stream":
                partes.append("".join(o["text"]))
    return "\n".join(partes)


def extraer(texto):
    out, faltan = {}, []
    for clave, (patron, esperado) in PATRONES.items():
        m = re.search(patron, texto)
        if not m:
            faltan.append((clave, esperado))
        else:
            out[clave] = m.groups()
    if faltan:
        msg = "\n".join(f"  - {c}: no se encontro la linea '{e}' en las salidas del notebook 08" for c, e in faltan)
        sys.exit("ERROR: no se pudieron extraer las cifras de aprendizaje no supervisado:\n" + msg +
                 "\nRevisa que el notebook 08 este ejecutado y que no haya cambiado el formato de esas salidas.")
    g = out
    return {
        "fuente": "salidas de texto de notebooks/08_analisis_observabilidad_sin_camara.ipynb (extraidas una vez, sin reentrenar)",
        "k_elegido": int(g["k_elegido"][0]),
        "ari_entre_tecnicas": {k: float(v) for k, v in ast.literal_eval(g["ari_entre_tecnicas"][0]).items()},
        "estabilidad_por_segmento": {"remuestreos": int(g["estabilidad"][0]), "ari_medio": float(g["estabilidad"][1]), "ari_minimo": float(g["estabilidad"][2])},
        "isolation_forest": {"cajas_atipicas": int(g["isolation_forest"][0]), "porcentaje": int(g["isolation_forest"][1]), "segmentos": int(g["isolation_forest"][2]),
                             "tasa_sin_camara_atipicas": float(g["isolation_forest"][3]), "tasa_sin_camara_resto": float(g["isolation_forest"][4])},
        "diferencia_con_signo_clusters": {"puntos": float(g["diferencia_con_signo"][0]), "ic_lo": float(g["diferencia_con_signo"][1]), "ic_hi": float(g["diferencia_con_signo"][2]), "excluye_0": g["diferencia_con_signo"][3] == "True"},
    }


if __name__ == "__main__":
    datos = extraer(texto_salidas())
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Escrito {SALIDA.relative_to(R)}")
