# F37, Paso 1: descarga de segmentos NUEVOS REALES para la demostración en vivo. Para correr en Google Colab, celda por celda (cada «# %%» es una celda).
#
# Por qué en Colab: aquí `gcloud` y `gsutil` no están instalados y el bucket de Waymo v2 pide una cuenta de Google que aceptó los términos del dataset (la misma que usaron los notebooks 00 y 00b).
# Por qué el split «validation»: los 41 segmentos de desarrollo y los candidatos del plan sellado de la validación externa (plan_seleccion_ep3.json) son TODOS del split «training». Un segmento de
# «validation» no puede estar entre ellos ni gastar la validación ciega. La celda 3 lo comprueba contra el inventario y la lista de EP2 y se detiene si hay un solo id repetido.
# Solo baja dos componentes (lidar_box y camera_to_lidar_box_association), unos 1 MB y 25 KB por segmento. Nada de imágenes.
#
# Resultado: `demo_candidatos.tar.gz`. En su equipo: descomprimir en datos_demo\candidatos\ (queda datos_demo\candidatos\<segmento>\lidar_box.parquet y camera_to_lidar_box_association.parquet).

# %% 1. Acceso al bucket
from google.colab import auth  # noqa: E402

auth.authenticate_user()

# %% 2. Parámetros (no cambiar para que el resultado sea reproducible)
import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
import tarfile  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BUCKET = "gs://waymo_open_dataset_v_2_0_1"
SPLIT = "validation"
N_PRUEBA = 8            # segmentos de los que se baja solo lidar_box para mirar cuántos peatones y ciclistas tienen
N_FINAL = 4             # los que se quedan (más peatones y ciclistas) y de los que se baja también la asociación
SEMILLA = 42
# rangos de azimut de cada cámara y umbrales congelados (data/06_models_ep3/detector_params_v3.json)
RANGOS = {1: (-20.982388931852668, 20.062391902566524), 2: (20.3650179430934, 63.09623912133825), 3: (-60.510145082443096, -19.4964067944327),
          4: (64.39328639396926, 109.195549751222), 5: (-105.25017497375109, -57.55798059754393)}
MIN_CAJAS = 100
BASE = "/content/demo/candidatos"
os.makedirs(BASE, exist_ok=True)

# %% 3. Subir inventario_segmentos.csv y segmentos_ep2.csv (de docs/seleccion_segmentos/) y excluir cualquier id ya conocido
from google.colab import files  # noqa: E402

subidos = files.upload()
assert {"inventario_segmentos.csv", "segmentos_ep2.csv"} <= set(subidos), "faltan inventario_segmentos.csv o segmentos_ep2.csv"
conocidos = set(pd.read_csv("inventario_segmentos.csv", dtype=str)["segment_id"]) | set(pd.read_csv("segmentos_ep2.csv", dtype=str)["segment_id"])
print(f"ids ya conocidos (training de EP2/EP3): {len(conocidos)}")

# %% 4. Listar el split y elegir 8 al azar (semilla 42)
salida = subprocess.run(["gsutil", "ls", f"{BUCKET}/{SPLIT}/lidar_box/"], capture_output=True, text=True, check=True).stdout.split()
ids = sorted(os.path.basename(x)[:-len(".parquet")] for x in salida if x.endswith(".parquet"))
print(f"{len(ids)} segmentos en {SPLIT}/lidar_box")
repetidos = sorted(set(ids) & conocidos)
assert not repetidos, f"DETENIDO: estos ids del split {SPLIT} ya están en EP2/EP3: {repetidos[:5]}"
elegidos = [str(s) for s in np.random.default_rng(SEMILLA).permutation(np.array(ids, dtype=object))[:N_PRUEBA]]
print(elegidos)

# %% 5. Bajar solo lidar_box de esos 8 y contar peatones y ciclistas por cámara
filas = []
for seg in elegidos:
    carpeta = f"{BASE}/{seg}"
    os.makedirs(carpeta, exist_ok=True)
    subprocess.run(["gsutil", "-q", "cp", f"{BUCKET}/{SPLIT}/lidar_box/{seg}.parquet", f"{carpeta}/lidar_box.parquet"], check=True)
    df = pd.read_parquet(f"{carpeta}/lidar_box.parquet")
    tipo = next(c for c in df.columns if c.endswith("].type"))
    x = next(c for c in df.columns if c.endswith("box.center.x"))
    y = next(c for c in df.columns if c.endswith("box.center.y"))
    vru = df[df[tipo].isin([2, 4])].copy()
    vru["az"] = np.degrees(np.arctan2(vru[y], vru[x]))
    fila = {"segmento": seg, "cajas": len(df), "peatones_ciclistas": len(vru), "vru_hasta_100": int((vru["az"].abs() <= 100).sum())}
    for c, (lo, hi) in RANGOS.items():
        fila[f"cam{c}"] = int(vru["az"].between(lo, hi).sum())
    filas.append(fila)
tabla = pd.DataFrame(filas).sort_values("vru_hasta_100", ascending=False)
print(tabla.to_string(index=False))
print(f"\nUn hueco solo se puede marcar en una cámara con >= {MIN_CAJAS} peatones y ciclistas en su rango (columnas camN).")

# %% 6. Quedarse con los 4 que más peatones y ciclistas tienen y bajar su asociación
finales = list(tabla["segmento"].head(N_FINAL))
for seg in finales:
    subprocess.run(["gsutil", "-q", "cp", f"{BUCKET}/{SPLIT}/camera_to_lidar_box_association/{seg}.parquet", f"{BASE}/{seg}/camera_to_lidar_box_association.parquet"], check=True)
for seg in elegidos:
    if seg not in finales:
        for f in os.listdir(f"{BASE}/{seg}"):
            os.remove(f"{BASE}/{seg}/{f}")
        os.rmdir(f"{BASE}/{seg}")
print("candidatos:", finales)

# %% 7. Empaquetar y descargar (con la tabla y un registro de dónde salió cada archivo)
registro = {"bucket": BUCKET, "split": SPLIT, "semilla": SEMILLA, "elegidos_al_azar": elegidos, "candidatos": finales, "tabla": tabla.to_dict("records")}
with open("/content/demo/candidatos/REGISTRO_DESCARGA.json", "w", encoding="utf-8") as f:
    json.dump(registro, f, indent=1, ensure_ascii=False)
with tarfile.open("/content/demo_candidatos.tar.gz", "w:gz") as tar:
    tar.add("/content/demo/candidatos", arcname="candidatos")
print(subprocess.run(["sha256sum", "/content/demo_candidatos.tar.gz"], capture_output=True, text=True).stdout)
files.download("/content/demo_candidatos.tar.gz")
