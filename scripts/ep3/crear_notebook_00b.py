"""Genera notebooks/00b_seleccion_segmentos_ep3.ipynb (para correr en Colab; NO se ejecuta aqui).

F18-B: el notebook reproduce el pool de EP2 (sin lluvia -> n_frames >= 190 -> percentiles de n_detecciones -> SOLO DESPUES excluir los 91 evaluados),
usa cuotas fijas de segmentos utiles por estrato y copia, celda por celda, el codigo de src/waymo_evaluacion/ep3/seleccion_nuevos.py (funciones puras).
Las cifras del texto salen de docs/ep3/plan_seleccion_ep3.json y data/08_reporting_ep3/f18_seleccion_rendimiento.csv, no se escriben a mano.
"""
from __future__ import annotations

import json
from pathlib import Path

import nbformat as nbf
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
PLAN = json.loads((RAIZ / "docs/ep3/plan_seleccion_ep3.json").read_text(encoding="utf-8"))
REND = pd.read_csv(RAIZ / "data/08_reporting_ep3/f18_seleccion_rendimiento.csv").set_index(["corte", "grupo"])
FUENTE = (RAIZ / "src/waymo_evaluacion/ep3/seleccion_nuevos.py").read_text(encoding="utf-8")
nb = nbf.v4.new_notebook()
C = nb.cells


def md(t: str) -> None:
    C.append(nbf.v4.new_markdown_cell(t.strip("\n")))


def code(t: str) -> None:
    C.append(nbf.v4.new_code_cell(t.strip("\n")))


E, P, CU, CP = PLAN["embudo"], PLAN["parametros"], PLAN["cuotas_utiles"], PLAN["candidatos_por_estrato"]
n = lambda x: f"{x:,}".replace(",", ".")  # noqa: E731
noche = REND.loc[("momento_del_dia", "Night")]
cuotas_txt = "\n".join(f"| {k} | {q} | {n(CP[k])} |" for k, q in CU.items())

md(f"""
# 00b. Selección de segmentos nuevos para EP3 (validación externa sellada)

**Para correr en Google Colab, no en este repositorio.** Toma segmentos que EP2 nunca evaluó para probar la solución final una sola vez (plan v3, P9). Los pasos exactos están en `docs/ep3/GUIA_VALIDACION_EXTERNA.md`.

**Reglas de esta selección**
- Usa **solo metadatos** (hora del día, ubicación, número de frames, número de detecciones) y nunca `sin_camara` ni resultados de modelos. El orden de candidatos se calculó antes, sin descargar nada, y está en `docs/ep3/plan_seleccion_ep3.json` (sha256 en `plan_seleccion_ep3.sha256`).
- **Mismo pool que EP2** (`00b_seleccion_segmentos_ep2.ipynb`): sin lluvia ({E['sin_lluvia']}) → al menos {P['min_frames']} frames ({E['n_frames_>=190']}) → `n_detecciones` entre los percentiles {P['percentiles_detecciones'][0]} y {P['percentiles_detecciones'][1]} calculados sobre esos {E['n_frames_>=190']} ({n(round(E['limite_inferior_detecciones']))} a {n(round(E['limite_superior_detecciones']))}; pool de {E['n_detecciones_entre_percentiles']}) → **solo después** se excluyen los {E['evaluados_ep2_dentro_del_pool']} segmentos que EP2 ya evaluó ({E['candidatos_sin_los_evaluados_por_ep2']} candidatos). El notebook se detiene si el embudo no da {E['sin_lluvia']}, {E['n_frames_>=190']} y {E['n_detecciones_entre_percentiles']}.
- **Cuotas fijas de segmentos ÚTILES por estrato** (`time_of_day x location`), declaradas en la celda de parámetros:

| Estrato | Cuota de útiles | Candidatos disponibles |
|---|---|---|
{cuotas_txt}

  Total de la cuota: {PLAN['total_cuota']}. `Night / location_other` no tiene candidatos.
- **Evaluación secuencial por estrato** en el orden aleatorio fijado por la semilla {P['semilla']} (`numpy.random.default_rng`), hasta completar la cuota o agotar el estrato (queda registrado cuántos «faltan»). Los estratos se recorren por rondas para que el tope global de **{P['tope_evaluaciones']} evaluaciones** no deje sin evaluar a los últimos. **Meta mínima: {P['meta_utiles']} útiles.**
- Un candidato **se descarta** si: la asociación 2D está vacía; tiene menos de {P['min_asociaciones']} asociaciones; las asociaciones no cruzan con `lidar_box` (0 positivos); tiene menos de **{P['min_positivos']} positivos** (cajas LiDAR con par de cámara); o el etiquetado es ralo (menos de {P['min_tasa_etiquetada_pct']} % de las cajas LiDAR de los frames etiquetados tiene par). Son los criterios de EP2.
- Descarga solo `lidar_box` y `camera_to_lidar_box_association` (no imágenes).

**Por qué cuotas fijas y no proporcionales.** El desarrollo (EP2) tuvo cuotas por estrato, no proporcionales al tamaño; una asignación proporcional daría ~90 % de segmentos de día. **Hay sobremuestreo de San Francisco de día** ({CU['Day / location_sf']} útiles) porque ahí están las 2 celdas con hueco de EP2 (2 de los {int(REND.loc[('momento_x_ubicacion', 'Day / location_sf'), 'seleccionados'])} segmentos seleccionados de ese estrato): más segmentos de ese estrato permiten ver si el detector vuelve a marcar celdas. La elección usa solo metadatos y se declara antes de abrir datos.

**Limitación declarada: la noche queda mal representada.** De noche quedan {CP['Night / location_sf'] + CP['Night / location_phx']} candidatos ({CP['Night / location_sf']} en San Francisco, {CP['Night / location_phx']} en Phoenix, 0 en otras ubicaciones) y en EP2 solo {int(noche['seleccionados'])} de {int(noche['evaluados'])} candidatos nocturnos resultaron útiles ({100 * noche['rendimiento']:.0f} %): lo probable es que las cuotas de noche no se completen. El resultado no representa bien la noche.

**Nota de honestidad sobre el criterio de etiquetado.** Mide qué tan completo está el etiquetado 2D del segmento (pares sobre cajas LiDAR de todos los tipos, en frames etiquetados), igual que en EP2. No usa la tasa de `sin_camara` de peatones y ciclistas, pero sí deja fuera segmentos con etiquetado 2D muy escaso: el detector y la regla solo se prueban en segmentos con etiquetado denso (sesgo de selección documentado en el informe, §3).

**Licencia.** Los datos del Waymo Open Dataset son de uso no comercial y no se redistribuyen. El `.tar.gz` que produce este notebook es solo para su uso local en el curso.
""")

md("## 1. Parámetros y funciones de selección (fijados antes de mirar nada)\nLa celda siguiente es una **copia exacta** de `src/waymo_evaluacion/ep3/seleccion_nuevos.py` (una prueba del repositorio comprueba que coinciden). Aquí están las cuotas, los umbrales y la lógica del orden.")
code(FUENTE)
code("""
import hashlib, json, os, subprocess, tarfile, time
from pathlib import Path
import numpy as np
import pandas as pd

BUCKET = "gs://waymo_open_dataset_v_2_0_1/training"
TRABAJO = Path("/content/ep3_nuevos")          # carpeta de trabajo en Colab
SALIDA = TRABAJO / "salida"
(SALIDA / "lidar_box").mkdir(parents=True, exist_ok=True)
(SALIDA / "camera_to_lidar_box_association").mkdir(parents=True, exist_ok=True)
(TRABAJO / "tmp").mkdir(parents=True, exist_ok=True)
print("cuota total de utiles:", sum(CUOTAS.values()), "| tope de evaluaciones:", TOPE_EVALUACIONES, "| meta:", META_UTILES)
""")

md("""
## 2. Entorno y acceso al bucket (Colab)
Hay que haber aceptado la licencia del Waymo Open Dataset con su cuenta de Google. `gsutil` ya viene en Colab.
""")
code("""
try:
    from google.colab import auth, files
    auth.authenticate_user()
    EN_COLAB = True
except ImportError:
    EN_COLAB = False
    print("No es Colab: asegure gsutil autenticado y los archivos de metadatos en RUTA_META.")
print(subprocess.run(["gsutil", "version"], capture_output=True, text=True).stdout.splitlines()[:1])
""")

md("""
## 3. Metadatos de EP2 (suba los tres CSV de `docs/seleccion_segmentos/` y, si quiere comprobar el plan, `docs/ep3/plan_seleccion_ep3.json` y `.sha256`)
`inventario_segmentos.csv` (798 segmentos), `registro_verificacion_ep2.csv` (los 91 evaluados) y `diagnostico_lluvia_ep2.csv`.
""")
code("""
RUTA_META = TRABAJO / "meta"
RUTA_META.mkdir(exist_ok=True)
if EN_COLAB and not (RUTA_META / "inventario_segmentos.csv").exists():
    for nombre, contenido in files.upload().items():
        (RUTA_META / nombre).write_bytes(contenido)
inv = pd.read_csv(RUTA_META / "inventario_segmentos.csv", dtype={"segment_id": str})
reg = pd.read_csv(RUTA_META / "registro_verificacion_ep2.csv", dtype={"segment_id": str})
assert len(inv) == 798 and len(reg) == 91, (len(inv), len(reg))
print(f"inventario {len(inv)} | ya evaluados en EP2 {len(reg)}")
""")

md("## 4. Embudo, candidatos y orden por estrato (solo metadatos)")
code("""
# El paso «existe lidar_box y asociacion» de EP2 depende del bucket: se cuenta aqui y debe dar 793 (todos los sin lluvia).
def listar(componente):
    s = subprocess.run(["gsutil", "ls", f"{BUCKET}/{componente}/*.parquet"], capture_output=True, text=True).stdout
    return {Path(l).stem for l in s.splitlines() if l.endswith(".parquet")}
con_ambos = listar("lidar_box") & listar("camera_to_lidar_box_association")
sin_lluvia = set(inv.loc[inv["weather"] != "rain", "segment_id"])
print("sin lluvia:", len(sin_lluvia), "| con lidar_box y asociacion:", len(sin_lluvia & con_ambos))

candidatos, pasos = embudo(inv, reg["segment_id"])
print(json.dumps(pasos, indent=1))
assert (pasos["sin_lluvia"], pasos[f"n_frames_>={MIN_FRAMES}"], pasos["n_detecciones_entre_percentiles"]) == (793, 786, 746), "el embudo no coincide con EP2: NO seguir y reportarlo"
assert pasos["candidatos_sin_los_evaluados_por_ep2"] == 655, pasos
orden = orden_por_estrato(candidatos)
print({k: len(v) for k, v in orden.items()})
""")
code("""
# Comprobacion opcional contra el plan pre-declarado del repositorio (si subio los dos archivos)
rp, rh = RUTA_META / "plan_seleccion_ep3.json", RUTA_META / "plan_seleccion_ep3.sha256"
if rp.exists() and rh.exists():
    assert hashlib.sha256(rp.read_bytes()).hexdigest() == rh.read_text().split()[0], "el plan subido no coincide con su sha256"
    plan = json.loads(rp.read_text(encoding="utf-8"))
    assert plan["orden_por_estrato"] == orden, "el orden calculado aqui NO coincide con el plan pre-declarado"
    print("OK: el orden de candidatos coincide con docs/ep3/plan_seleccion_ep3.json (sha256", rh.read_text().split()[0][:16], "...)")
else:
    print("(plan no subido: no se compara; el orden queda guardado en el paquete de salida)")
""")

md("""
## 5. Evaluación de cada candidato
Se descargan solo las dos tablas necesarias. El criterio de «etiquetado ralo» se calcula como en EP2: cajas LiDAR con par de cámara (clave `frame + laser_object_id`) divididas por las cajas LiDAR de los frames que tienen al menos un par; los **positivos** son las cajas LiDAR con par. **No se calcula ni se mira `sin_camara` de peatones y ciclistas.** Es reanudable si Colab se reinicia: `seleccionar` repite la misma secuencia y salta lo ya medido.
""")
code("""
def gcopiar(ruta, destino):
    r = subprocess.run(["gsutil", "-q", "cp", ruta, str(destino)], capture_output=True, text=True)
    return r.returncode == 0

def evaluar(seg):
    t = TRABAJO / "tmp"
    m = dict(segment_id=seg, asoc_filas=0, lidar_disponible=True, lidar_filas=np.nan, frames_totales=np.nan, frames_etiquetados=np.nan, positivos=0, tasa_etiquetado_pct=np.nan, archivo_asoc_ausente=False)
    if not gcopiar(f"{BUCKET}/camera_to_lidar_box_association/{seg}.parquet", t / "asoc.parquet"):
        m["archivo_asoc_ausente"] = True
    else:
        a = pd.read_parquet(t / "asoc.parquet", columns=["key.frame_timestamp_micros", "key.laser_object_id"])
        m["asoc_filas"] = len(a)
        if len(a) >= MIN_ASOCIACIONES:                   # como en EP2: solo se baja lidar_box si la asociacion tiene filas suficientes
            if not gcopiar(f"{BUCKET}/lidar_box/{seg}.parquet", t / "lidar.parquet"):
                m["lidar_disponible"] = False
            else:
                l = pd.read_parquet(t / "lidar.parquet", columns=["key.frame_timestamp_micros", "key.laser_object_id"])
                par = l.merge(a.drop_duplicates().assign(_p=1), on=["key.frame_timestamp_micros", "key.laser_object_id"], how="left")
                par["_p"] = par["_p"].fillna(0)
                etiquetado = par.groupby("key.frame_timestamp_micros")["_p"].transform("max") > 0
                en_frames = par[etiquetado]
                m.update(lidar_filas=len(l), frames_totales=l["key.frame_timestamp_micros"].nunique(), frames_etiquetados=int(par.loc[etiquetado, "key.frame_timestamp_micros"].nunique()),
                         positivos=int(par["_p"].sum()), tasa_etiquetado_pct=round(100 * float(en_frames["_p"].sum()) / max(len(en_frames), 1), 3))
    m["resultado"], m["motivo"] = decidir(m)
    return m
""")
code("""
REGISTRO = TRABAJO / "registro_verificacion_ep3.csv"
hechos = pd.read_csv(REGISTRO, dtype={"segment_id": str}) if REGISTRO.exists() else pd.DataFrame()
previos = {r["segment_id"]: r for r in hechos.to_dict("records")}
meta = inv.set_index("segment_id")
t0 = time.time()

def evaluar_y_guardar(seg):
    r = evaluar(seg)
    r.update(time_of_day=meta.loc[seg, "time_of_day"], location=meta.loc[seg, "location"], n_frames_inventario=int(meta.loc[seg, "n_frames"]))
    if r["resultado"] == "util":                      # se conserva solo lo util
        for comp, arch in (("lidar_box", "lidar.parquet"), ("camera_to_lidar_box_association", "asoc.parquet")):
            (TRABAJO / "tmp" / arch).replace(SALIDA / comp / f"{seg}.parquet")
    pd.DataFrame([r]).to_csv(REGISTRO, mode="a", header=not REGISTRO.exists(), index=False)
    print(f"{seg[:12]} {r['resultado']:9s} {r['motivo']}  ({time.time()-t0:.0f} s)")
    return r

registro = seleccionar(orden, CUOTAS, evaluar_y_guardar, TOPE_EVALUACIONES, previos)
reg3 = pd.DataFrame(registro)
""")

md("## 6. Resultado de la selección")
code("""
n_util = int((reg3["resultado"] == "util").sum())
resumen = resumen_cuotas(registro, CUOTAS, orden)
print(f"evaluados {len(reg3)} (tope {TOPE_EVALUACIONES}) | utiles {n_util} (meta {META_UTILES}, cuota {sum(CUOTAS.values())}) | descartados {len(reg3) - n_util}")
display(resumen)
print(reg3["motivo"].str.replace(r"\\(.*\\)", "", regex=True).value_counts().to_string())
if n_util < META_UTILES:
    print(f"ATENCION: solo {n_util} utiles (< {META_UTILES}). No se reajusta nada con los datos: vea docs/ep3/GUIA_VALIDACION_EXTERNA.md (que hacer si salen menos de 15).")
""")

md("""
## 7. Exportar el paquete
Se escribe la lista de segmentos útiles, el registro completo (incluye descartados), el resumen por estrato («faltan») y los parámetros, y se empaqueta todo en un `.tar.gz` con su sha256. Descárguelo y llévelo al repositorio (por ejemplo a `data/01_raw_nuevos/`).
""")
code("""
utiles = reg3[reg3["resultado"] == "util"][["segment_id", "estrato", "time_of_day", "location", "n_frames_inventario", "asoc_filas", "lidar_filas", "positivos", "tasa_etiquetado_pct"]]
utiles.to_csv(SALIDA / "segmentos_nuevos_ep3.csv", index=False)
reg3.to_csv(SALIDA / "registro_verificacion_ep3.csv", index=False)
resumen.to_csv(SALIDA / "resumen_cuotas_ep3.csv", index=False)
params = dict(semilla=SEMILLA, meta_utiles=META_UTILES, tope_evaluaciones=TOPE_EVALUACIONES, min_frames=MIN_FRAMES, percentiles=list(PERCENTILES_DETECCIONES), min_asociaciones=MIN_ASOCIACIONES,
              min_positivos=MIN_POSITIVOS, min_tasa_etiquetada_pct=MIN_TASA_ETIQUETADA, cuotas={f"{a} / {b}": q for (a, b), q in CUOTAS.items()}, embudo=pasos, bucket=BUCKET,
              usa_sin_camara=False, evaluados=int(len(reg3)), utiles=int(len(utiles)), segmentos_utiles=sorted(utiles["segment_id"]), orden_por_estrato=orden)
(SALIDA / "parametros_seleccion_ep3.json").write_text(json.dumps(params, indent=1), encoding="utf-8")
paquete = TRABAJO / "segmentos_nuevos_ep3.tar.gz"
with tarfile.open(paquete, "w:gz") as tar:
    tar.add(SALIDA, arcname="segmentos_nuevos_ep3")
h = hashlib.sha256(paquete.read_bytes()).hexdigest()
print("paquete:", paquete, f"({paquete.stat().st_size/1e6:.1f} MB)\\nsha256:", h)
if EN_COLAB:
    files.download(str(paquete))
""")

md("""
## 8. Qué sigue (en el repositorio, en este orden; detalle en `docs/ep3/GUIA_VALIDACION_EXTERNA.md`)
1. Descomprima el paquete en `data/01_raw_nuevos/` (queda `segmentos_nuevos_ep3/`).
2. `.venv\\Scripts\\python scripts/ep3/evaluar_sellado.py congelar --lista data/01_raw_nuevos/segmentos_nuevos_ep3/segmentos_nuevos_ep3.csv` (congela lista y modelos con sha256, **antes** de abrir datos).
3. `.venv\\Scripts\\python scripts/ep3/ingesta_nuevos.py --entrada data/01_raw_nuevos/segmentos_nuevos_ep3 --lista <la misma lista>`.
4. `.venv\\Scripts\\python scripts/ep3/evaluar_sellado.py evaluar --lista <la misma lista>` (una sola vez; crea el candado).
Nada de lo que salga se usa para elegir ni reajustar.
""")

nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}, "colab": {"provenance": []}}
nbf.validate(nb)
destino = RAIZ / "notebooks" / "00b_seleccion_segmentos_ep3.ipynb"
nbf.write(nb, destino)
print("escrito y validado:", destino)
