"""Genera notebooks/00b_seleccion_segmentos_ep3.ipynb (para correr en Colab; NO se ejecuta aqui)."""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

RAIZ = Path(__file__).resolve().parents[2]
nb = nbf.v4.new_notebook()
C = nb.cells


def md(t: str) -> None:
    C.append(nbf.v4.new_markdown_cell(t.strip("\n")))


def code(t: str) -> None:
    C.append(nbf.v4.new_code_cell(t.strip("\n")))


md("""
# 00b. Selección de segmentos nuevos para EP3 (validación externa sellada)

**Para correr en Google Colab, no en este repositorio.** Reconstruye la selección de EP2 y toma segmentos que EP2 nunca evaluó, para probar la solución final una sola vez (plan v3, P9).

**Reglas de esta selección**
- Usa **solo metadatos** (hora del día, ubicación, número de frames) para sortear. **Nunca usa `sin_camara`** ni ningún resultado de los modelos.
- Excluye los 91 segmentos que EP2 ya evaluó (`docs/seleccion_segmentos/registro_verificacion_ep2.csv`) y los 5 segmentos con lluvia.
- Muestreo estratificado por `time_of_day x location`, semilla 42.
- Descarta un segmento candidato si: (a) la asociación 2D está **vacía**; (b) tiene **menos de 50 asociaciones**; (c) el **etiquetado es ralo**: menos de 5,5 % de las cajas LiDAR de los frames etiquetados tiene par de cámara (misma definición que EP2, ver más abajo).
- Meta: **al menos 15 segmentos útiles**. Se evalúan 40 candidatos y, si hace falta, hasta 45.
- Descarga solo `lidar_box` y `camera_to_lidar_box_association` (no imágenes).

**Nota de honestidad sobre el criterio (c).** Mide qué tan completo está el etiquetado 2D del segmento (pares sobre cajas LiDAR de todos los tipos, en frames etiquetados), igual que en EP2. No usa la tasa de `sin_camara` de peatones y ciclistas, pero sí deja fuera segmentos con muy poco etiquetado 2D, así que la población nueva se parece a la de EP2 y no cubre ese caso extremo. Está declarado como limitación.

**Licencia.** Los datos del Waymo Open Dataset son de uso no comercial y no se redistribuyen. El `.tar.gz` que produce este notebook es solo para su uso local en el curso.
""")

md("## 1. Parámetros (fijados antes de mirar nada)")
code("""
import json, math, os, subprocess, hashlib, tarfile, time
from pathlib import Path
import numpy as np
import pandas as pd

SEMILLA = 42
META_UTILES = 15
N_EVALUAR = 40            # candidatos a evaluar en la primera tanda
N_EVALUAR_MAX = 45        # tope si faltan utiles
UMBRAL_TASA_ETIQUETADO = 5.5   # % de cajas LiDAR de frames etiquetados con par de camara
MIN_ASOCIACIONES = 50
BUCKET = "gs://waymo_open_dataset_v_2_0_1/training"
TRABAJO = Path("/content/ep3_nuevos")          # carpeta de trabajo en Colab
SALIDA = TRABAJO / "salida"
(SALIDA / "lidar_box").mkdir(parents=True, exist_ok=True)
(SALIDA / "camera_to_lidar_box_association").mkdir(parents=True, exist_ok=True)
(TRABAJO / "tmp").mkdir(parents=True, exist_ok=True)
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
    print("No es Colab: asegure gsutil autenticado y los CSV de metadatos en RUTA_META.")
print(subprocess.run(["gsutil", "version"], capture_output=True, text=True).stdout.splitlines()[:1])
""")

md("""
## 3. Metadatos de EP2 (suba los tres CSV de `docs/seleccion_segmentos/`)
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
lluvia = set(inv.loc[inv["weather"] == "rain", "segment_id"])
assert len(lluvia) == 5, len(lluvia)
print(f"inventario {len(inv)} | ya evaluados en EP2 {len(reg)} | lluvia {len(lluvia)}")
""")

md("## 4. Candidatos y muestreo estratificado (solo metadatos)")
code("""
excluidos = set(reg["segment_id"]) | lluvia
cand = inv[~inv["segment_id"].isin(excluidos)].copy()
cand["estrato"] = cand["time_of_day"] + " / " + cand["location"]
print(f"candidatos: {len(cand)}")
tam = cand.groupby("estrato").size()
print(tam.to_string())

def cuotas(n_h, total):
    exacto = total * n_h / n_h.sum()
    base = np.floor(exacto).astype(int)
    resto = int(total - base.sum())
    for h in (exacto - base).sort_values(ascending=False).index[:resto]:
        base[h] += 1
    return base

rng = np.random.default_rng(SEMILLA)
cu = cuotas(tam, N_EVALUAR)
primera, reserva = [], []
for h in sorted(tam.index):
    ids = cand.loc[cand["estrato"] == h, "segment_id"].sort_values().to_numpy()
    perm = rng.permutation(ids)
    primera += list(perm[: cu[h]])
    reserva += list(perm[cu[h]:])
reserva = list(rng.permutation(reserva))           # orden de reserva, tambien aleatorio y fijo
orden = primera + reserva
print(f"primera tanda: {len(primera)} | cuotas por estrato:", cu.to_dict())
""")

md("""
## 5. Evaluación de cada candidato
Se descargan solo las dos tablas necesarias. El criterio de «etiquetado ralo» se calcula como en EP2: cajas LiDAR con par de cámara (clave `frame + laser_object_id`) divididas por las cajas LiDAR de los frames que tienen al menos un par. **No se calcula ni se mira `sin_camara`.**
""")
code("""
def gcopiar(ruta, destino):
    r = subprocess.run(["gsutil", "-q", "cp", ruta, str(destino)], capture_output=True, text=True)
    return r.returncode == 0

def evaluar(seg):
    t = TRABAJO / "tmp"
    a_ok = gcopiar(f"{BUCKET}/camera_to_lidar_box_association/{seg}.parquet", t / "asoc.parquet")
    if not a_ok:
        return dict(segment_id=seg, asoc_filas=0, lidar_filas=np.nan, frames_totales=np.nan, frames_etiquetados=0, tasa_etiquetado_pct=np.nan,
                    resultado="descartado", motivo="asociacion vacia (archivo ausente)")
    a = pd.read_parquet(t / "asoc.parquet", columns=["key.frame_timestamp_micros", "key.laser_object_id"])
    if len(a) == 0:
        return dict(segment_id=seg, asoc_filas=0, lidar_filas=np.nan, frames_totales=np.nan, frames_etiquetados=0, tasa_etiquetado_pct=np.nan,
                    resultado="descartado", motivo="asociacion vacia")
    if len(a) < MIN_ASOCIACIONES:
        return dict(segment_id=seg, asoc_filas=len(a), lidar_filas=np.nan, frames_totales=np.nan, frames_etiquetados=np.nan, tasa_etiquetado_pct=np.nan,
                    resultado="descartado", motivo=f"pocas asociaciones ({len(a)} < {MIN_ASOCIACIONES})")
    if not gcopiar(f"{BUCKET}/lidar_box/{seg}.parquet", t / "lidar.parquet"):
        return dict(segment_id=seg, asoc_filas=len(a), resultado="descartado", motivo="lidar_box no disponible")
    l = pd.read_parquet(t / "lidar.parquet", columns=["key.frame_timestamp_micros", "key.laser_object_id"])
    par = l.merge(a.drop_duplicates().assign(_p=1), on=["key.frame_timestamp_micros", "key.laser_object_id"], how="left")
    par["_p"] = par["_p"].fillna(0)
    etiquetado = par.groupby("key.frame_timestamp_micros")["_p"].transform("max") > 0
    en_frames = par[etiquetado]
    tasa = 100 * en_frames["_p"].sum() / max(len(en_frames), 1)
    base = dict(segment_id=seg, asoc_filas=len(a), lidar_filas=len(l), frames_totales=l["key.frame_timestamp_micros"].nunique(),
                frames_etiquetados=int(par.loc[etiquetado, "key.frame_timestamp_micros"].nunique()), tasa_etiquetado_pct=round(float(tasa), 3))
    if tasa < UMBRAL_TASA_ETIQUETADO:
        return {**base, "resultado": "descartado", "motivo": f"etiquetado ralo ({tasa:.1f}% < {UMBRAL_TASA_ETIQUETADO}% en frames etiquetados)"}
    return {**base, "resultado": "util", "motivo": ""}
""")
code("""
REGISTRO = TRABAJO / "registro_verificacion_ep3.csv"
hechos = pd.read_csv(REGISTRO, dtype={"segment_id": str}) if REGISTRO.exists() else pd.DataFrame()   # reanudable si Colab se reinicia
filas = hechos.to_dict("records")
vistos = {f["segment_id"] for f in filas}
meta = inv.set_index("segment_id")
t0 = time.time()
for seg in orden:
    utiles = sum(f["resultado"] == "util" for f in filas)
    evaluados = len(filas)
    if evaluados >= N_EVALUAR_MAX or (evaluados >= N_EVALUAR and utiles >= META_UTILES):
        break
    if seg in vistos:
        continue
    r = evaluar(seg)
    r.update(time_of_day=meta.loc[seg, "time_of_day"], location=meta.loc[seg, "location"], n_frames_inventario=int(meta.loc[seg, "n_frames"]))
    if r["resultado"] == "util":                      # se conserva solo lo util
        for comp, arch in (("lidar_box", "lidar.parquet"), ("camera_to_lidar_box_association", "asoc.parquet")):
            (TRABAJO / "tmp" / arch).replace(SALIDA / comp / f"{seg}.parquet")
    filas.append(r)
    pd.DataFrame(filas).to_csv(REGISTRO, index=False)
    print(f"{len(filas):2d} {seg[:12]} {r['resultado']:9s} {r['motivo']}  ({time.time()-t0:.0f} s)")
reg3 = pd.DataFrame(filas)
""")

md("## 6. Resultado de la selección")
code("""
n_util = int((reg3["resultado"] == "util").sum())
print(f"evaluados {len(reg3)} | utiles {n_util} | descartados {len(reg3) - n_util}")
print(reg3["motivo"].str.replace(r"\\(.*\\)", "", regex=True).value_counts().to_string())
print(reg3[reg3["resultado"] == "util"].groupby(["location", "time_of_day"]).size().to_string())
assert n_util >= META_UTILES, f"solo {n_util} utiles: ampliar N_EVALUAR_MAX con la reserva o pedir mas segmentos"
""")

md("""
## 7. Exportar el paquete
Se escribe la lista de segmentos útiles, el registro completo (incluye descartados) y los parámetros, y se empaqueta todo en un `.tar.gz` con su sha256. Descárguelo y llévelo al repositorio (carpeta fuera de `data/01_raw`, por ejemplo `data/01_raw_nuevos/`, ignorada por git).
""")
code("""
utiles = reg3[reg3["resultado"] == "util"][["segment_id", "time_of_day", "location", "n_frames_inventario", "asoc_filas", "lidar_filas", "tasa_etiquetado_pct"]]
utiles.to_csv(SALIDA / "segmentos_nuevos_ep3.csv", index=False)
reg3.to_csv(SALIDA / "registro_verificacion_ep3.csv", index=False)
params = dict(semilla=SEMILLA, meta_utiles=META_UTILES, n_evaluar=N_EVALUAR, n_evaluar_max=N_EVALUAR_MAX, umbral_tasa_etiquetado_pct=UMBRAL_TASA_ETIQUETADO,
              min_asociaciones=MIN_ASOCIACIONES, bucket=BUCKET, candidatos=int(len(cand)), excluidos_ep2=int(len(reg)), excluidos_lluvia=int(len(lluvia)),
              estratos="time_of_day x location", usa_sin_camara=False, evaluados=int(len(reg3)), utiles=int(len(utiles)),
              segmentos_utiles=sorted(utiles["segment_id"]))
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
## 8. Qué sigue (en el repositorio, en este orden)
1. Descomprima el paquete en `data/01_raw_nuevos/` (queda `segmentos_nuevos_ep3/`).
2. `python scripts/ep3/evaluar_sellado.py congelar --lista data/01_raw_nuevos/segmentos_nuevos_ep3/segmentos_nuevos_ep3.csv` (congela lista y modelos con sha256, **antes** de abrir datos).
3. `python scripts/ep3/ingesta_nuevos.py --entrada data/01_raw_nuevos/segmentos_nuevos_ep3 --lista <la misma lista>`.
4. `python scripts/ep3/evaluar_sellado.py evaluar --lista <la misma lista>` (una sola vez; crea el candado).
Nada de lo que salga se usa para elegir ni reajustar.
""")

nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"},
               "colab": {"provenance": []}}
destino = RAIZ / "notebooks" / "00b_seleccion_segmentos_ep3.ipynb"
nbf.write(nb, destino)
print("escrito", destino)
