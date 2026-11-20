"""Genera los notebooks 11 a 14 de EP3 (sin ejecutarlos). Luego se ejecutan con nbconvert.

Cada notebook explica y muestra artefactos ya calculados (data/08_reporting_ep3, data/09_app_ep3); con
RECALCULAR = True vuelven a lanzar los scripts correspondientes. Todas las cifras de las lecturas salen de los archivos.
Uso: python scripts/ep3/crear_notebooks_ep3.py [11 12 13 14]
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat as nbf

RAIZ = Path(__file__).resolve().parents[2]

SETUP = '''
from pathlib import Path
import json, subprocess, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Markdown, display

RAIZ = next((p for p in [Path.cwd(), *Path.cwd().parents] if (p / "conf").exists() and (p / "data").exists()), Path("C:/Users/maico/waymo-evaluacion"))
sys.path.insert(0, str(RAIZ / "src"))
REP, IMG, APP = RAIZ / "data/08_reporting_ep3", RAIZ / "images/ep3", RAIZ / "data/09_app_ep3"
IMG.mkdir(parents=True, exist_ok=True)
RECALCULAR = False          # True: vuelve a correr los scripts de esta fase (puede tardar mucho; escribe solo en *_ep3)
SEMILLA = 42
EN_MUESTRA = "en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos"
GANANCIA_C = "La ganancia del brazo C sale de 2 celdas cámara x segmento, una de ellas en el segmento donde se descubrió el hueco."
AZUL, NARANJA, GRIS, VERDE, ROJO = "#2a78d6", "#e07b39", "#8a8a8a", "#6a994e", "#c0392b"
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25})

from waymo_evaluacion.ep3.plan import verificar_plan_v3
print("Plan v3 verificado (sha256):", ", ".join(verificar_plan_v3(RAIZ)))


def coma(x, d=3):
    return f"{x:.{d}f}".replace(".", ",")


def pct(x, d=1):
    return f"{100 * x:.{d}f} %".replace(".", ",")


def miles(x):
    return f"{int(round(x)):,}".replace(",", ".")


def guardar_fig(fig, nombre):
    fig.savefig(IMG / f"{nombre}.png", dpi=130, bbox_inches="tight")


def correr(script, *args):
    r = subprocess.run([sys.executable, "-X", "utf8", str(RAIZ / "scripts/ep3" / script), *args], capture_output=True, text=True, cwd=RAIZ)
    print(r.stdout[-1500:], r.stderr[-800:])
    assert r.returncode == 0, f"{script} fallo"
'''


class NB:
    def __init__(self) -> None:
        self.nb = nbf.v4.new_notebook()

    def md(self, t: str) -> None:
        self.nb.cells.append(nbf.v4.new_markdown_cell(t.strip("\n")))

    def code(self, t: str) -> None:
        self.nb.cells.append(nbf.v4.new_code_cell(t.strip("\n")))

    def guardar(self, nombre: str) -> None:
        self.nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}
        nbf.write(self.nb, RAIZ / "notebooks" / nombre)
        print("escrito", nombre)


# ======================================================================================== 11
def nb11() -> None:
    n = NB()
    n.md("""
# 11. EP3: datos de desarrollo y detector de huecos (F1 y F2)

**Qué hacemos.** Juntamos los 41 segmentos de EP2 (33 de train y 8 de test) en una sola tabla de desarrollo, fijamos los folds y volvemos a correr el detector de huecos por cámara con los parámetros de EP2 sin recalcularlos.

**Analogía.** En EP2 guardamos 8 segmentos como examen sorpresa. Ya los miramos seis veces, así que en EP3 ya no son un examen ciego: los usamos como un tercio más de material de estudio, y el examen ciego de verdad serán segmentos nuevos que todavía no existen.

**Plan v3 (congelado antes de ver resultados):** población principal con |azimut| <= 100°, target `sin_camara`, CV externa StratifiedGroupKFold(5) por segmento, semilla 42.

Este notebook **muestra artefactos**: no recalcula nada salvo que `RECALCULAR = True`.
""")
    n.code(SETUP)
    n.code("""
if RECALCULAR:
    correr("f1_datos.py")
    correr("f2_detector.py")
dev = pd.read_parquet(RAIZ / "data/05_model_input_ep3/dev_41.parquet")
pp = dev[dev["en_zona_principal"]]
r1 = json.loads((REP / "f1_resumen.json").read_text(encoding="utf-8"))
print(f"Filas totales (<= 120 grados): {miles(r1['filas_total_120'])} | población principal: {miles(r1['filas_principal'])} filas, {miles(r1['positivos_principal'])} positivos ({pct(r1['prevalencia_principal'])})")
print(f"Segmentos: {r1['segmentos']} ({r1['segmentos_train']} train de EP2 + {r1['segmentos_test']} test de EP2)")
print("Test de EP2, principal (filas, positivos):", r1["test_principal"], "| 120 grados:", r1["test_120"], "(iguales a la tabla del plan de EP2)")
""")
    n.md("## 1. Los 41 segmentos: cuántas filas y cuántos positivos hay en cada uno")
    n.code("""
seg = pp.groupby("seg").agg(grupo=("grupo", "first"), ubicacion=("location", "first"), momento=("time_of_day", "first"), filas=("sin_camara", "size"), positivos=("sin_camara", "sum"))
seg["tasa"] = seg["positivos"] / seg["filas"]
seg = seg.sort_values("tasa")
fig, ax = plt.subplots(figsize=(9, 8))
ax.barh(seg.index, seg["tasa"], color=[AZUL if g == "train" else NARANJA for g in seg["grupo"]])
ax.axvline(pp["sin_camara"].mean(), color="k", ls="--", lw=1, label=f"prevalencia global {pct(pp['sin_camara'].mean())}")
ax.set_xlabel("proporción de cajas sin par de cámara (sin_camara = 1)"); ax.set_title("Tasa de sin_camara por segmento (azul: train de EP2, naranja: test de EP2)")
ax.legend(); ax.tick_params(axis="y", labelsize=6)
guardar_fig(fig, "11_tasa_por_segmento"); plt.show()
top = seg.sort_values("positivos", ascending=False).iloc[0]
display(Markdown(f"**Lectura (generada).** La tasa va de {pct(seg['tasa'].min())} a {pct(seg['tasa'].max())} según el segmento. El segmento `{top.name}` aporta {miles(int(top['positivos']))} positivos "
                 f"({pct(top['positivos'] / seg['positivos'].sum())} de todos): por eso la validación se hace por segmento y se reporta siempre cuántos segmentos gana cada método."))
""")
    n.md("""
## 2. Conjuntos de variables y folds
Tres conjuntos declarados en el plan (V16, V_OBS, V_OBS_TAM); el conjunto es un hiperparámetro de la búsqueda. Los folds se arman por segmento y se estratifican por `sin_camara` para que ningún segmento quede repartido entre entrenamiento y validación.
""")
    n.code("""
cj = json.loads((RAIZ / "data/05_model_input_ep3/conjuntos_variables.json").read_text(encoding="utf-8"))
display(pd.DataFrame({"conjunto": list(cj), "variables": [len(v) for v in cj.values()], "lista": [", ".join(v) for v in cj.values()]}))
f = r1["folds"]["fold_s42"]
display(pd.DataFrame({"filas": f["filas"], "segmentos": f["segmentos"], "prevalencia": f["prevalencia"]}))
print("Segmentos presentes en más de un fold (debe ser 0):", {k: v["segmentos_en_mas_de_un_fold"] for k, v in r1["folds"].items()})
""")
    n.md("## 3. Los modelos congelados de EP2 se reproducen (control de que reconstruimos bien los datos)")
    n.code("""
rep = pd.read_csv(REP / "f1_reproduccion_pred_test.csv")
display(rep)
print(f"Diferencia máxima absoluta contra pred_test_B.parquet de EP2: {rep['dif_max_abs'].max():.2e} (tolerancia 1e-9)")
""")
    n.md("""
## 4. Filtro 1: detector de huecos por cámara
Reglas de EP2, sin recalcular: el rango de azimut de cada cámara es el p5-p95 de las cajas con par en train; la mediana de la tasa por cámara se calcula con los 41 segmentos; una celda (segmento, cámara) tiene **hueco** si su tasa es menor al 25 % de la mediana y hay al menos 100 cajas en el rango.

**Analogía.** Es como revisar un cuaderno de recibos por cámara: si en un segmento una cámara casi no tiene recibos pareados aunque debería, no conviene revisar recibo por recibo, sino avisar que falta toda una caja de recibos.
""")
    n.code("""
par = json.loads((RAIZ / "data/06_models_ep3/detector_params_v3.json").read_text(encoding="utf-8"))
display(pd.DataFrame({"camara": list(par["rangos"]), "az_p5": [v[0] for v in par["rangos"].values()], "az_p95": [v[1] for v in par["rangos"].values()],
                      "mediana_tasa": [par["medianas_ref"][f"c{c}"] for c in par["rangos"]]}).round(3))
cel = pd.read_csv(REP / "f2_tasa_segmento_camara.csv", dtype={"seg": str})
cams = [1, 2, 3, 4, 5]
mat = cel[[f"tasa_c{c}" for c in cams]].to_numpy(float)
fig, ax = plt.subplots(figsize=(7.5, 10))
im = ax.imshow(np.ma.masked_invalid(mat), aspect="auto", cmap="viridis", vmin=0, vmax=1)
ax.set_xticks(range(5), [f"cámara {c}" for c in cams]); ax.set_yticks(range(len(cel)), [f"{s} | {g}" for s, g in zip(cel["seg"], cel["grupo"])], fontsize=6)
for i in range(len(cel)):
    for j, c in enumerate(cams):
        if cel.loc[i, f"hueco_c{c}"]:
            ax.text(j, i, "X", ha="center", va="center", color="red", fontweight="bold", fontsize=11)
fig.colorbar(im, ax=ax, shrink=0.5, label="tasa de cajas con par dentro del rango de la cámara"); ax.set_title("Tasa por segmento y cámara (X = hueco)"); ax.grid(False)
guardar_fig(fig, "11_mapa_de_calor_huecos"); plt.show()
lista = pd.read_csv(REP / "lista_A_huecos.csv", dtype={"segmento": str})
display(lista.round(3))
r2 = json.loads((REP / "f2_resumen.json").read_text(encoding="utf-8"))
display(Markdown(f"**Lectura (generada).** El detector marca {r2['n_pares_con_hueco']} celdas con hueco, {'las mismas que en EP2' if r2['pares_iguales_a_ep2'] else 'DISTINTAS a las de EP2'} "
                 f"(diferencia máxima contra los CSV de EP2: {r2['dif_max_tabla_vs_ep2']:.1e}). Esas celdas contienen {miles(r2['positivos_en_hueco_principal'])} de los {miles(r1['positivos_principal'])} positivos "
                 f"({pct(r2['positivos_en_hueco_principal'] / r1['positivos_principal'])}) en {miles(r2['cajas_en_hueco_principal'])} cajas de la población principal. **Post hoc, no pre-declarado** (el apéndice M de EP2 lo descubrió después de abrir el test)."))
""")
    n.md("## 5. Baselines simples (reglas), con IC 95 % por segmentos")
    n.code("""
b = pd.read_csv(REP / "f2_baselines_reglas_41.csv")
vista = pd.DataFrame({"método": b["metodo"]})
for k in ["AUC", "PR-AUC", "Captura@20", "Fraccion_80"]:
    vista[k] = [f"{coma(r[k])} ({coma(r[k + '_lo'])} a {coma(r[k + '_hi'])})" for _, r in b.iterrows()]
display(vista)
g = pd.read_csv(REP / "f2_baselines_reglas_por_grupo.csv")
display(g[g["metodo"] == "Regla: menos puntos top"].round(3))
display(Markdown("**Nota.** La regla geométrica (azimut > 105° primero) coincide con la de puntos LiDAR en la población principal porque ahí |azimut| <= 100°: nunca se activa. "
                 "Las reglas no se ajustan, así que no hay predicción fuera de fold: se evalúan sobre los 41 segmentos."))
""")
    n.md("""
## 6. EDA y calidad de datos (post hoc, descriptivo; fase 12.4)
Tasa de `sin_camara` por tramo de puntos del LiDAR superior, azimut, distancia (quintiles) y clase, con IC 95 % por segmentos, y revisión de nulos, duplicados y atípicos. **Lo que más explica `sin_camara` son los puntos del LiDAR.**
""")
    n.code("""
if RECALCULAR:
    correr("f12_analisis_muestra.py")
eda = pd.read_csv(REP / "f12_eda_tasas.csv")
vista = eda.assign(tasa=eda["tasa"].map(pct), IC=[f"{pct(a)} a {pct(b)}" for a, b in zip(eda["ic_lo"], eda["ic_hi"])])[["variable", "tramo", "cajas", "positivos", "tasa", "IC", "segmentos"]]
display(vista)
from IPython.display import Image
display(Image(filename=str(IMG / "12_eda_tasas.png")))
cal = pd.read_csv(REP / "f12_eda_calidad.csv"); cres = json.loads((REP / "f12_eda_calidad_resumen.json").read_text(encoding="utf-8"))
display(cal[["variable", "pct_nulos", "atipicos_bajos", "atipicos_altos", "pct_atipicos"]].round(3))
print(f"Nulos: {cres['nulos_total']} | llaves duplicadas: {cres['duplicados_por_llave_principal']} | cajas con 0 puntos LiDAR: {miles(cres['cajas_con_0_puntos_lidar'])} ({pct(cres['pct_cajas_con_0_puntos_lidar'])}) | con 0 puntos top: {miles(cres['cajas_con_0_puntos_top'])}, de las cuales {pct(cres['tasa_sin_camara_en_cajas_con_0_puntos_top'])} no tienen pareja")
pt = eda[eda["variable"] == "puntos_top"].set_index("tramo")
display(Markdown(f"**Lectura (generada, post hoc).** La tasa va de {pct(pt.loc['0-5', 'tasa'])} con 0 a 5 puntos del sensor superior a {pct(pt.loc['51-100', 'tasa'])} con 51 a 100. Sin nulos ni llaves duplicadas; los atípicos de puntos y densidad son cajas muy cercanas, no errores, y no se eliminaron."))
""")
    n.md("""
## 7. Sensibilidad del detector (post hoc; fase 12.2)
30 combinaciones de `frac` (0,15 a 0,35), `min_cajas` (50, 100, 200) y mediana (con los 41 segmentos o sin el segmento candidato). Celdas marcadas además de los 2 de referencia (sin verdad externa): las que no son uno de los 2 huecos de EP2; los 2 de referencia los define el mismo detector con los parámetros de EP2 (DEV-3). «30 de 30» mide la estabilidad del conjunto marcado frente a los parámetros, no sensibilidad ni especificidad.
""")
    n.code("""
sens = pd.read_csv(REP / "f12_sensibilidad_detector.csv")
res = sens.groupby(["mediana", "frac"]).agg(marcadas_min=("marcadas", "min"), marcadas_max=("marcadas", "max"), extra_min=("falsas_alarmas", "min"), extra_max=("falsas_alarmas", "max"), detecta_los_2=("detecta_los_2", "all")).reset_index()
display(res)
display(Markdown(f"**Lectura (generada, post hoc).** Los 2 huecos se detectan en {int(sens['detecta_los_2'].sum())} de {len(sens)} combinaciones; las celdas marcadas además de los 2 de referencia (sin verdad externa) van de {int(sens['falsas_alarmas'].min())} a {int(sens['falsas_alarmas'].max())}. "
                 "Como los parámetros se ajustaron con los mismos segmentos donde se evalúa, la tasa de celdas marcadas y su estabilidad solo se podrán medir bien con segmentos nuevos."))
""")
    n.md("""
## 8. Puntos del sensor superior > 100: por qué la tasa sube (post hoc, no pre-declarado; F18-A3c)
La tasa de `sin_camara` baja con los puntos y vuelve a subir con más de 100. Se separó por celdas con hueco (`f12_eda_puntos_top_sin_huecos.csv`).
""")
    n.code("""
pts = pd.read_csv(REP / "f12_eda_puntos_top_sin_huecos.csv")
res = json.loads((REP / "f12_eda_puntos_top_resumen.json").read_text(encoding="utf-8"))
display(pts.pivot(index="tramo", columns="variante", values="tasa").reindex(["0-5", "6-10", "11-20", "21-50", "51-100", "101-200", "201-500", ">500"]).round(3))
m = res["tramo_mayor_100"]
display(Markdown(f"**Lectura (generada, post hoc).** Con más de 100 puntos hay {miles(m['cajas_en_celdas_con_hueco'])} cajas dentro de las celdas con hueco, con tasa {pct(m['tasa_en_celdas_con_hueco'])}, y concentran {pct(res['pct_positivos_mayor_100_en_celdas_con_hueco'])} de los positivos del tramo. Sin esas celdas la tasa del tramo es {pct(m['tasa_sin_hueco'])}: la serie es decreciente. *Hipótesis (no verificada):* el alza era el hueco, no el sensor."))
""")
    n.guardar("11_ep3_datos_y_deteccion.ipynb")


# ======================================================================================== 12
def nb12() -> None:
    n = NB()
    n.md("""
# 12. EP3: optimización de hiperparámetros y ensambles (IE9 e IE10)

**IE9.** Cada modelo (LR, RF, HGB, XGBoost, LightGBM) se compara **por defecto** contra **optimizado** con una búsqueda aleatoria **anidada**: la búsqueda se hace solo con los segmentos de entrenamiento de cada fold externo, así que el fold de validación nunca influye en la elección de hiperparámetros. "Mejora" significa una diferencia de PR-AUC fuera de fold de al menos +0,010 con IC pareado por segmentos que excluya 0.

**IE10.** Ensambles E1 a E4. Uno "aporta" si supera en al menos 0,010 de AUC a su mejor componente y el IC pareado excluye 0.

**Analogía.** Afinar hiperparámetros es ajustar la dificultad de un examen de práctica con un profesor distinto cada vez; un ensamble es consultar a varios compañeros y promediar. Solo sirve si los compañeros se equivocan en cosas distintas.

**Desviación registrada (DEV-1):** por tiempo de cómputo se usó 1 repetición de la CV externa (semilla 42) y 30 configuraciones (el plan decía 3 y 40). Ver `docs/ep3/plan_v3_desviaciones.md`.
""")
    n.code(SETUP)
    n.code("""
if RECALCULAR:      # tarda horas: RF ajusta 200 arboles por configuracion
    correr("f3_tuning.py", "--etapa", "principal", "--semillas", "42", "--ncfg", "30", "--workers", "6")
    correr("f3_analisis.py")
    correr("f4_ensambles.py", "--workers", "5")
t9 = pd.read_csv(REP / "f3_defecto_vs_optimizado.csv")
vista = pd.DataFrame({"modelo": t9["modelo"], "etapa": t9["etapa"]})
for k in ["PR-AUC", "AUC"]:
    vista[f"{k} defecto"] = [f"{coma(r[k + '_def'])}" for _, r in t9.iterrows()]
    vista[f"{k} optimizado"] = [f"{coma(r[k + '_opt'])}" for _, r in t9.iterrows()]
vista["dif. PR-AUC (IC 95 %)"] = [f"{coma(r['dif_PR-AUC'], 3)} ({coma(r['dif_PR-AUC_lo'])} a {coma(r['dif_PR-AUC_hi'])})" for _, r in t9.iterrows()]
vista["folds donde gana"] = t9["folds_opt_gana_ap"].astype(str) + " de 5"
vista["veredicto"] = t9["veredicto"]
display(vista)
""")
    n.code("""
fig, ax = plt.subplots(figsize=(7, 3.6))
y = np.arange(len(t9))
ax.errorbar(t9["dif_PR-AUC"], y, xerr=[t9["dif_PR-AUC"] - t9["dif_PR-AUC_lo"], t9["dif_PR-AUC_hi"] - t9["dif_PR-AUC"]], fmt="o", color=AZUL, capsize=3)
ax.axvline(0, color="k", lw=1); ax.axvline(0.010, color=ROJO, ls="--", label="umbral de mejora +0,010")
ax.set_yticks(y, t9["modelo"]); ax.set_xlabel("PR-AUC optimizado menos defecto (IC 95 % por segmentos)"); ax.legend(); ax.set_title("IE9: ¿mejora optimizar?")
guardar_fig(fig, "12_ie9_mejora"); plt.show()
mej = t9[t9["veredicto"] == "mejora"]["modelo"].tolist()
no = t9[t9["veredicto"] != "mejora"]["modelo"].tolist()
display(Markdown(f"**Lectura (generada).** Mejoran con la búsqueda según el criterio del plan: {', '.join(mej) if mej else 'ninguno'}. No mejoran: {', '.join(no) if no else 'ninguno'}. "
                 "Un modelo puede ganar en el promedio y aun así 'no mejorar' si el IC incluye 0: con 41 segmentos y diferencias pequeñas, el intervalo manda."))
""")
    n.md("### Óptimos en el borde de la grilla y comprobación de regularización\nEn EP2 varios óptimos quedaron en el borde (HGB `max_leaf_nodes` 4 y `min_samples_leaf` 100; RF `min_samples_leaf` 200 y `max_features` sqrt). Aquí las grillas incluyen valores más regularizados, y si un óptimo cae en el borde se extiende la grilla una vez.")
    n.code("""
bd = pd.read_csv(REP / "f3_bordes.csv")
display(bd)
ext = json.loads((REP / "f3_bordes_extension.json").read_text(encoding="utf-8")) if (REP / "f3_bordes_extension.json").exists() else {}
hay_ext = sorted({p.name.split("_")[1] for p in (REP / "f3_ckpt").glob("ext_*.pkl")})
print("Modelos con óptimo en el borde en la etapa principal:", ext if ext else "ninguno")
print("Modelos para los que se repitió la búsqueda con grilla extendida:", hay_ext if hay_ext else "ninguno")
cfg = pd.read_csv(REP / "f3_config_por_fold.csv")
display(cfg.drop(columns=["etapa"]))
""")
    n.md("### Curvas de validación (un hiperparámetro clave por modelo; el resto por defecto, conjunto V16)\nSi la curva de entrenamiento sube y la de validación baja o se aplana, el modelo se está memorizando los segmentos de entrenamiento.")
    n.code("""
if (REP / "f3_curvas_validacion.csv").exists():
    cv = pd.read_csv(REP / "f3_curvas_validacion.csv")
    modelos = list(cv["modelo"].unique())
    fig, axes = plt.subplots(1, len(modelos), figsize=(3.4 * len(modelos), 3.2), sharey=True)
    for ax, m in zip(np.atleast_1d(axes), modelos):
        d = cv[cv["modelo"] == m].groupby("valor")[["ap_train", "ap_val"]].mean().sort_index()
        ax.plot(d.index, d["ap_train"], "o-", color=GRIS, label="entrenamiento"); ax.plot(d.index, d["ap_val"], "o-", color=AZUL, label="validación")
        if m in ("LR", "RF"):
            ax.set_xscale("log")
        ax.set_title(f"{m}: {cv[cv['modelo'] == m]['hiperparametro'].iloc[0]}", fontsize=9); ax.set_xlabel("valor")
    np.atleast_1d(axes)[0].set_ylabel("PR-AUC"); np.atleast_1d(axes)[0].legend(fontsize=7)
    fig.suptitle("IE9: curvas de validación (promedio de 5 folds)"); fig.tight_layout(); guardar_fig(fig, "12_ie9_curvas_validacion"); plt.show()
else:
    print("Las curvas de validación aún no se calcularon (scripts/ep3/f3_tuning.py --etapa curvas).")
""")
    n.md("## IE10: ensambles\nLos modelos base de los ensambles usan la configuración optimizada solo si IE9 dio 'mejora' para ese modelo; si no, el defecto.")
    n.code("""
t10 = pd.read_csv(REP / "f4_ensambles_aporta.csv")
v10 = pd.DataFrame({"ensamble": t10["ensamble"], "mejor componente": t10["mejor_componente"], "AUC ensamble": t10["AUC_ensamble"].map(coma), "AUC mejor comp.": t10["AUC_mejor_componente"].map(coma),
                    "diferencia (IC 95 %)": [f"{coma(r.dif_AUC)} ({coma(r.dif_lo)} a {coma(r.dif_hi)})" for r in t10.itertuples()],
                    "folds ganados": t10["folds_ganados_de_5"].astype(str) + " de 5", "segmentos ganados": t10["segmentos_ganados"].astype(str) + " de " + t10["segmentos_comparados"].astype(str),
                    "veredicto": t10["veredicto"]})
display(v10)
fig, ax = plt.subplots(figsize=(7, 3.2))
y = np.arange(len(t10))
ax.errorbar(t10["dif_AUC"], y, xerr=[t10["dif_AUC"] - t10["dif_lo"], t10["dif_hi"] - t10["dif_AUC"]], fmt="o", color=AZUL, capsize=3)
ax.axvline(0, color="k", lw=1); ax.axvline(0.010, color=ROJO, ls="--", label="umbral +0,010")
ax.set_yticks(y, t10["ensamble"]); ax.set_xlabel("AUC del ensamble menos su mejor componente"); ax.legend(); ax.set_title("IE10: ¿aporta el ensamble?")
guardar_fig(fig, "12_ie10_aporta"); plt.show()
res4 = json.loads((REP / "f4_resumen.json").read_text(encoding="utf-8"))
ap = t10[t10["veredicto"] == "aporta"]["ensamble"].tolist(); ind = t10[t10["veredicto"] == "indicio no concluyente"]["ensamble"].tolist()
display(Markdown(f"**Lectura (generada).** Aportan: {', '.join(ap) if ap else 'ninguno'}. Indicio no concluyente: {', '.join(ind) if ind else 'ninguno'}. "
                 f"El ensamble principal declarado en el plan (mayor AUC entre E1 y E4) es **{res4['ensamble_principal_declarado']}**."))
""")
    n.code("""
cand = pd.read_csv(REP / "f4_candidatos_metricas.csv")
orden = cand.sort_values("AUC")
fig, ax = plt.subplots(figsize=(7, 5))
ax.errorbar(orden["AUC"], range(len(orden)), xerr=[orden["AUC"] - orden["AUC_lo"], orden["AUC_hi"] - orden["AUC"]], fmt="o", color=AZUL, capsize=2)
ax.set_yticks(range(len(orden)), orden["candidato"]); ax.set_xlabel("AUC fuera de fold (IC 95 % por segmentos)"); ax.set_title("Todos los candidatos y componentes")
guardar_fig(fig, "12_candidatos_auc"); plt.show()
display(Markdown("**Cuidado al leer.** Los IC de cada candidato se solapan mucho porque comparten los mismos 41 segmentos; lo que decide es la diferencia **pareada**, no el solapamiento de las barras."))
""")
    n.md("""
**Sobre por qué LR y RF empeoran al optimizar: hipótesis, no verificada.** Con 41 segmentos y 30 configuraciones, la búsqueda interna puede elegir configuraciones que aprovechan particularidades de los segmentos de entrenamiento y no se sostienen en el fold de validación (sobreajuste de la búsqueda); en LR, el criterio interno (PR-AUC) podría preferir variables y regularización distintas de las que sirven en el fold externo. No lo probamos.

**Desviación DEV-1:** 1 repetición y 30 configuraciones por la regla de cómputo (ver `plan_v3_desviaciones.md`).
""")
    n.guardar("12_ep3_tuning_y_ensambles.ipynb")


# ======================================================================================== 13
def nb13() -> None:
    n = NB()
    n.md("""
# 13. EP3: generalización y selección (IE11 e IE12)

**IE11 (generalización).** ¿Se sostiene el resultado fuera de la muestra? Miramos la estabilidad por fold y por segmento, la calibración (¿la probabilidad dice la verdad?), un leave-one-segment-out del modelo elegido, una curva de aprendizaje por número de segmentos y la brecha entre ajuste y validación.

**IE12 (selección).** Aplicamos la regla del plan v3: entre los candidatos que cumplen O1, O3 y O4, el más simple cuyo AUC quede a menos de 0,010 del mejor. Si nadie cumple O2 ("vale la pena" frente a la regla), lo decimos igual.

**Analogía.** Elegir entre una calculadora, una hoja de cálculo y un sistema contable: si la hoja de cálculo ya da la cuenta con la precisión necesaria, no compramos el sistema contable.

Los umbrales de los puntos A (recall objetivo 0,80) y B (20 % de revisión) y el calibrador se fijan **solo** con scores internos de entrenamiento de cada fold.
""")
    n.code(SETUP)
    n.code("""
if RECALCULAR:
    correr("f5_generalizacion.py"); correr("f6_seleccion.py"); correr("f5_loso_curva.py")
m5 = pd.read_csv(REP / "f5_metricas_candidatos.csv")
sel = json.loads((REP / "f6_seleccion.json").read_text(encoding="utf-8"))
elegido = sel["elegido"]
cols = ["candidato", "AUC", "PR-AUC", "Captura@20", "Fraccion_80", "recall_A", "precision_A", "recall_B", "precision_B", "ECE_cal", "Brier_cal", "AUC_min_fold", "AUC_mediana_segmento", "estable"]
display(m5[cols].round(3))
print("Candidato elegido por la regla del plan:", elegido)
""")
    n.md("## Estabilidad: AUC por fold y por segmento\nCriterio del plan: AUC mínimo por fold >= 0,75 y mediana del AUC por segmento >= 0,80.")
    n.code("""
af = pd.read_csv(REP / "f5_auc_por_fold.csv")
asg = pd.read_csv(REP / "f5_auc_por_segmento.csv")
orden = m5.sort_values("AUC")["candidato"].tolist()
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
for i, c in enumerate(orden):
    d = af[af["candidato"] == c]["AUC"]
    axes[0].scatter(d, [i] * len(d), color=AZUL, s=22)
    s = asg[asg["candidato"] == c]["AUC"]
    axes[1].boxplot(s, positions=[i], vert=False, widths=0.6, showfliers=True)
axes[0].axvline(0.75, color=ROJO, ls="--", label="mínimo 0,75"); axes[1].axvline(0.80, color=ROJO, ls="--", label="mediana >= 0,80")
axes[0].set_yticks(range(len(orden)), orden); axes[0].set_xlabel("AUC por fold externo"); axes[1].set_xlabel("AUC por segmento (>= 100 cajas de cada clase)")
axes[0].legend(fontsize=8); axes[1].legend(fontsize=8); fig.suptitle("IE11: estabilidad"); fig.tight_layout(); guardar_fig(fig, "13_estabilidad"); plt.show()
inest = m5[~m5["estable"].astype(bool)]["candidato"].tolist()
display(Markdown(f"**Lectura (generada).** No cumplen el criterio de estabilidad: {', '.join(inest) if inest else 'ninguno'}. "
                 f"Un fold con pocos segmentos y una tasa distinta mueve mucho el AUC: por eso se reporta el mínimo y no solo el promedio."))
""")
    n.md("## Calibración (Platt, ajustada con scores internos de entrenamiento)\nUna probabilidad calibrada dice 'de cada 100 cajas con 30 %, unas 30 son positivas'.")
    n.code("""
cb = pd.read_csv(REP / "f5_calibracion_bins.csv")
fig, ax = plt.subplots(figsize=(5.2, 4.8))
ax.plot([0, 1], [0, 1], "k:", label="calibración perfecta")
for c, col in ((elegido, AZUL), ("Regla top", GRIS)):
    d = cb[cb["candidato"] == c]
    e = m5.set_index("candidato").loc[c, "ECE_cal"]
    ax.plot(d["pred"], d["obs"], "o-", color=col, label=f"{c} (ECE {coma(e)})")
ax.set_xlabel("probabilidad calibrada (media del decil)"); ax.set_ylabel("frecuencia observada de sin_camara"); ax.legend(fontsize=8); ax.set_title("Confiabilidad fuera de fold")
guardar_fig(fig, "13_calibracion"); plt.show()
""")
    n.md("""
## Leave-one-segment-out, curva de aprendizaje y brecha
Se calculan para el candidato elegido y, como complemento, para los dos mejores modelos que **aprenden** (LR3 y XGBoost): si el elegido es una regla, no hay nada que aprender y su curva es plana por construcción.
""")
    n.code("""
def sufijo(c):
    return "_" + c.replace(" ", "_")
asg_idx = asg.set_index(["candidato", "segmento"])["AUC"]
for cand in dict.fromkeys([elegido, "LR3", "XGB"]):
    f_res = REP / f"f5_loso_resumen{sufijo(cand)}.json"
    if not f_res.exists():
        print(f"{cand}: LOSO aún no calculado (scripts/ep3/f5_loso_curva.py --candidato '{cand}')"); continue
    rs = json.loads(f_res.read_text(encoding="utf-8"))
    lo = pd.read_csv(REP / f"f5_loso_segmentos{sufijo(cand)}.csv", dtype={"seg": str}).set_index("seg")
    oof = asg[asg["candidato"] == cand].set_index("segmento")["AUC"]
    comun = oof.index.intersection(lo.index)
    cur = pd.read_csv(REP / f"f5_curva_aprendizaje{sufijo(cand)}.csv")
    g = cur.groupby("n_segmentos")[["AUC_ajuste", "AUC_validacion"]].agg(["mean", "std"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].scatter(oof[comun], lo.loc[comun, "AUC"], color=AZUL, s=26); axes[0].plot([0.4, 1], [0.4, 1], "k:")
    axes[0].set_xlabel("AUC por segmento, CV de 5 folds"); axes[0].set_ylabel("AUC por segmento, leave-one-segment-out"); axes[0].set_title(f"{cand}: dos formas de dejar el segmento fuera")
    for c, col, nom in (("AUC_ajuste", GRIS, "ajuste (entrenamiento)"), ("AUC_validacion", AZUL, "validación")):
        axes[1].errorbar(g.index, g[(c, "mean")], yerr=g[(c, "std")].fillna(0), fmt="o-", color=col, capsize=3, label=nom)
    axes[1].set_xlabel("segmentos de entrenamiento"); axes[1].set_ylabel("AUC"); axes[1].legend(); axes[1].set_title(f"Curva de aprendizaje de {cand}")
    fig.tight_layout(); guardar_fig(fig, f"13_loso_curva_{cand.replace(' ', '_')}"); plt.show()
    br = pd.read_csv(REP / f"f5_brecha{sufijo(cand)}.csv")
    ult = br.iloc[-1]
    display(Markdown(f"**{cand} (lectura generada).** AUC global LOSO {coma(rs['AUC'])} (IC {coma(rs['AUC_ic'][0])} a {coma(rs['AUC_ic'][1])}); mediana por segmento {coma(rs['AUC_mediana_segmento'])}; "
                     f"mínimo por segmento {coma(rs['AUC_min_segmento'])}; {rs['segmentos_con_AUC_menor_a_0_55']} de {rs['segmentos_evaluables']} segmentos evaluables con AUC < 0,55. "
                     f"Brecha ajuste - validación con todos los segmentos de entrenamiento: {coma(ult['brecha_AUC'])} de AUC; la validación pasa de {coma(br.iloc[0]['AUC_validacion'])} con {int(br.iloc[0]['n_segmentos'])} segmentos "
                     f"a {coma(ult['AUC_validacion'])} con {int(ult['n_segmentos'])}. "
                     + ("**Una regla no aprende nada**: la curva es plana por construcción y las diferencias entre filas vienen de qué segmentos entran en cada submuestra, no de aprender (las dos últimas filas son el entrenamiento completo de folds con 32 y 34 segmentos). " if cand == "Regla top" else "")
                     + "Con 41 segmentos y pocos folds estas curvas son ruidosas."))
""")
    n.md("## IE12: tabla de selección (objetivos O1 a O4)")
    n.code("""
ts = pd.read_csv(REP / "f6_tabla_seleccion.csv")
v = ts[["candidato", "AUC", "PR-AUC_menos_prevalencia", "Fraccion_80", "recall_A", "ECE_cal", "estable"]].copy()
for o in ("O1", "O2", "O3", "O4"):
    v[o] = np.where(ts[o], "cumple", "no")
v["dif. Fracción 80 % vs regla (IC)"] = [f"{coma(r.dif_Fraccion_80_vs_regla)} ({coma(r.dif_Fraccion_80_lo)} a {coma(r.dif_Fraccion_80_hi)})" for r in ts.itertuples()]
display(v.round(3))
display(Markdown(f"**Regla de elección (plan v3):** {sel['razon']}. **Elegido: {elegido}.** {'(La regla de reserva DEV-2 se declaró después de ver que nadie cumple O4; es post hoc, no pre-declarada.) ' if sel.get('fallback_O4') else ''}"
                 f"{'Algún candidato cumple O2: ' + ', '.join(sel['candidatos_que_cumplen_O2']) + '.' if sel['O2_lo_cumple_alguien'] else 'Ningún candidato cumple O2 (vale la pena frente a la regla): se recomienda igualmente el más simple que cumple lo demás.'}"))
esc = pd.read_csv(REP / "f6_modelo_escogido.csv").iloc[0]
cuadro = pd.DataFrame({"medida": ["AUC", "PR-AUC", "Captura al revisar 20 %", "Fracción de cajas para 80 % de recall", "Recall en el punto A", "Precisión en el punto A", "Recall en el punto B (20 %)", "Precisión en el punto B",
                                  "ECE (Platt)", "Brier (Platt)", "AUC mínimo por fold", "Mediana del AUC por segmento", "F1 en A (solo referencia)", "Accuracy en A (solo referencia)"],
                       "valor": [coma(esc[k]) for k in ["AUC", "PR-AUC", "Captura@20", "Fraccion_80", "recall_A", "precision_A", "recall_B", "precision_B", "ECE_cal", "Brier_cal", "AUC_min_fold", "AUC_mediana_segmento", "F1_A", "accuracy_A"]]})
cuadro["IC 95 % por segmentos"] = ["(%s a %s)" % (coma(esc[k + "_lo"]), coma(esc[k + "_hi"])) if k + "_lo" in esc.index else "" for k in ["AUC", "PR-AUC", "Captura@20", "Fraccion_80", "recall_A", "precision_A", "recall_B", "precision_B", "ECE_cal", "Brier_cal", "AUC_min_fold", "AUC_mediana_segmento", "F1_A", "accuracy_A"]]
display(Markdown(f"### Cuadro «Modelo escogido»: {elegido}")); display(cuadro)
display(Markdown("Accuracy y F1 son solo referencia: con una clase minoritaria de ~21 %, un clasificador trivial ya tiene accuracy alto, y no deciden nada en el plan."))
""")
    n.md("""
## Sobre la elección: E2 y la regla
""")
    n.code("""
t6 = pd.read_csv(REP / "f6_tabla_seleccion.csv").set_index("candidato"); m5i = m5.set_index("candidato")
e2 = m5i.loc["E2"]; rg = m5i.loc["Regla top"]
display(Markdown(f"**E2** (promedio de rangos de E1 y la regla) tiene AUC {coma(e2['AUC'])} contra {coma(rg['AUC'])} de la regla, PR-AUC {coma(e2['PR-AUC'])} contra {coma(rg['PR-AUC'])}, Fracción para 80 % {coma(e2['Fraccion_80'])} contra {coma(rg['Fraccion_80'])} "
                 f"(IC de la diferencia {coma(t6.loc['E2', 'dif_Fraccion_80_lo'])} a {coma(t6.loc['E2', 'dif_Fraccion_80_hi'])}) y ECE {coma(e2['ECE_cal'])} (> 0,05); además **contiene a la regla**. No hay diferencia distinguible y la elección de la regla se hizo por simplicidad, como manda el plan. "
                 "**Ningún candidato supera a la regla de forma distinguible.**"))
""")
    n.md("""
## Análisis en muestra (post hoc, no pre-declarado; fase 12.1): ¿qué pasa en el fold 0?
*(en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos)*
""")
    n.code("""
if RECALCULAR:
    correr("f12_analisis_muestra.py")
f12 = pd.read_csv(REP / "f12_auc_por_fold_brazos.csv"); r12 = json.loads((REP / "f12_resumen.json").read_text(encoding="utf-8"))
reg = f12[f12["candidato"] == "Regla top"]
display(reg[["fold", "segmentos", "cajas", "celdas_con_hueco", "hueco_contenido", "AUC_A", "AUC_B_celdas_sanas", "Fraccion80_A", "Fraccion80_B_celdas_sanas", "Fraccion80_C"]].round(3))
d12 = pd.read_csv(REP / "f12_diferencia_C_menos_A.csv"); dr = d12[(d12["candidato"] == "Regla top")]
display(dr[["variante", "Fraccion80_A", "Fraccion80_C", "dif_C_menos_A", "ic_lo", "ic_hi", "excluye_0", "segmentos"]].round(3))
g = dr[dr["variante"].str.startswith("global")].iloc[0]
display(Markdown(f"**¿El brazo B cumple AUC mínimo por fold >= 0,75?** Sí: {coma(r12['B_AUC_min_fold']['Regla top'])} (regla); el brazo A no ({coma(r12['A_AUC_min_fold']['Regla top'])}): el fallo del fold 0 se debe a la celda con hueco. "
                 f"**¿Qué hace C en el fold 1?** Baja la Fracción para 80 % de {coma(r12['C_en_fold_1_regla']['Fraccion80_A'])} a {coma(r12['C_en_fold_1_regla']['Fraccion80_C'])}. "
                 f"**¿El IC de C menos A excluye 0?** No: {coma(g['dif_C_menos_A'])} con IC {coma(g['ic_lo'])} a {coma(g['ic_hi'])}; {pct(g['prop_replicas_C_mejor'])} de las réplicas favorece a C y el resto no contiene ningún segmento con hueco. {GANANCIA_C}"))
""")
    n.md("## Equidad descriptiva (post hoc; fase 12.3)\nRegla en el punto A por ubicación, momento del día y clase, con y sin las celdas con hueco; AUC solo con >= 200 cajas en cada clase. Sin pruebas de hipótesis.")
    n.code("""
eq = pd.read_csv(REP / "f12_equidad.csv")
display(eq[["variable", "grupo", "celdas_con_hueco", "segmentos", "cajas", "positivos", "recall_A", "pct_revisado_A", "AUC"]].round(3))
cic = eq[(eq["grupo"] == "CYCLIST") & (eq["celdas_con_hueco"] == "incluidas")].iloc[0]
display(Markdown(f"**Lectura (generada).** El recall de la regla en A en ciclistas es {coma(cic['recall_A'])} con solo {int(cic['positivos'])} positivos; parte de las brechas por momento del día y ubicación se achica al quitar las celdas con hueco."))
""")
    n.guardar("13_ep3_generalizacion_y_seleccion.ipynb")


# ======================================================================================== 14
def nb14() -> None:
    n = NB()
    n.md("""
# 14. EP3: solución en dos pasos y página (F6 y F7)

La solución final tiene **tres capas**: (1) el **filtro 1**, el detector de huecos por cámara; (2) el **modelo o regla** que ordena las cajas de las celdas sanas; (3) la **persona que revisa y decide**.

**Brazos comparados (plan v3, P4).** A: un paso, todas las cajas ordenadas. B: solo celdas sanas (sensibilidad). C: dos pasos, la Lista A se atiende aparte (sus positivos cuentan como hallados por la auditoría) y la Lista B ordena las cajas sanas. **No inventamos un costo por auditoría**: reportamos el costo en cajas con el que C empata con A (punto de equilibrio).

**Analogía.** Antes de revisar factura por factura, miramos si falta una carpeta completa de facturas de un mes; esa carpeta se pide una sola vez y no se revisa factura por factura.
""")
    n.code(SETUP)
    n.code("""
if RECALCULAR:
    correr("f7_preparar_app.py")
sel = json.loads((REP / "f6_seleccion.json").read_text(encoding="utf-8"))
elegido = sel["elegido"]
bc = pd.read_csv(REP / "f5_brazoC.csv").set_index("candidato")
bb = pd.read_csv(REP / "f5_brazoB.csv").set_index("candidato")
fila = bc.loc[elegido]
display(Markdown("**" + EN_MUESTRA + ". " + GANANCIA_C + "**"))
display(pd.DataFrame({"brazo": ["A (un paso)", "C (dos pasos)"], "Fracción de cajas para 80 % de recall": [fila["Fraccion_80_A"], fila["Fraccion_80_C"]],
                      "Captura al revisar 20 %": [fila["Captura@20_A"], fila["Captura@20_C"]]}).round(3))
display(Markdown(f"**Punto de equilibrio.** Dos pasos empata con un paso si cada auditoría de celda cuesta **{fila['equilibrio_cajas_por_auditoria']:.0f} cajas** "
                 f"(IC 95 % por segmentos {fila['equilibrio_lo']:.0f} a {fila['equilibrio_hi']:.0f}; {int(fila['celdas_auditadas'])} celdas auditadas). "
                 f"Los positivos que cubre la auditoría son {miles(int(fila['positivos_cubiertos_por_auditoria']))}. Si una auditoría cuesta menos que eso en tiempo de revisión, el flujo en dos pasos saldría a cuenta ({EN_MUESTRA}). {GANANCIA_C}"))
print("Brazo B (solo celdas sanas):", bb.loc[elegido, ["AUC", "PR-AUC", "Captura@20", "Fraccion_80"]].round(3).to_dict())
""")
    n.code("""
cur = pd.read_csv(APP / "curva_cola.csv")
fig, ax = plt.subplots(figsize=(7, 4.4))
for nombre, col in zip(cur["solucion"].unique(), (AZUL, GRIS, VERDE)):
    d = cur[cur["solucion"] == nombre]
    ax.plot(d["presupuesto"], d["recall"], color=col, label=nombre); ax.fill_between(d["presupuesto"], d["lo"], d["hi"], color=col, alpha=0.15)
ax.plot([0, 1], [0, 1], "k:", label="al azar")
ax.set_xlabel("fracción de la cola revisada"); ax.set_ylabel("recall esperado (bandas: IC 95 % por segmentos)"); ax.legend(fontsize=8); ax.set_title("Cuánto se encuentra según cuánto se revisa (en muestra; post hoc)", fontsize=10)
guardar_fig(fig, "14_curva_recall_presupuesto"); plt.show()
""")
    n.md("""
## Inferencia con la solución congelada (v3) sobre un segmento
Es una **demostración sobre un segmento de desarrollo** (no es una prueba ciega: el modelo final se entrenó con los 41 segmentos). Muestra cómo se obtienen las listas A y B desde `lidar_box` y la asociación.
""")
    n.code("""
from waymo_evaluacion.ep3.inferencia import cargar_artefactos, puntuar_segmento
art = cargar_artefactos(RAIZ / "data/06_models_ep3")
seg = "2577669988012459365_1640_000_1660_000"
lb = pd.read_parquet(RAIZ / f"data/01_raw/waymo/lidar_box/{seg}.parquet")
asoc = pd.read_parquet(RAIZ / f"data/01_raw/waymo/camera_to_lidar_box_association/{seg}.parquet")
r = puntuar_segmento(lb, asoc, art)
print(json.dumps(r.resumen, ensure_ascii=False, indent=1))
display(r.lista_A.round(3))
display(r.lista_B.drop(columns=["key.frame_timestamp_micros", "key.laser_object_id"]).head(5).round(3))
""")
    n.md("## La página «Auditor de etiquetas 3D» (Streamlit) y su prueba de humo\nSe ejecuta con `streamlit run app/app.py` (solo local; F20: consola de revisión con navegación agrupada, una página por archivo en `app/paginas/`). Aquí corremos **todas las páginas con cada rol**, y luego con el **modo presentación**, con `streamlit.testing.v1.AppTest` (`switch_page`) sobre los datos reales de `data/09_app_ep3` para comprobar que no hay errores. El número de páginas y de roles se lee del código de la página.")
    n.code("""
import logging
logging.getLogger("streamlit").setLevel(logging.ERROR)
from streamlit.testing.v1 import AppTest
from waymo_evaluacion.ep3.app_logica import ARCHIVO_PAGINA, PERFILES, SECCIONES
estado = {}
for perfil in PERFILES:
    for s in SECCIONES:
        at = AppTest.from_file(str(RAIZ / "app/app.py"), default_timeout=120).run()
        at.sidebar.selectbox[0].set_value(perfil).run()                 # el rol está al pie de la barra lateral
        at.switch_page(ARCHIVO_PAGINA[s]).run()
        estado.setdefault(s, {})[perfil] = "sin errores" if not at.exception else f"ERROR: {at.exception[0].value[:80]}"
for s in SECCIONES:                                                      # modo presentación (rol por defecto)
    at = AppTest.from_file(str(RAIZ / "app/app.py"), default_timeout=120).run()
    at.sidebar.toggle[0].set_value(True).run()
    at.switch_page(ARCHIVO_PAGINA[s]).run()
    estado.setdefault(s, {})["modo presentación"] = "sin errores" if not at.exception else f"ERROR: {at.exception[0].value[:80]}"
display(pd.DataFrame(estado).T)
print(f"{len(SECCIONES)} páginas x {len(PERFILES)} roles + modo presentación = {len(SECCIONES) * (len(PERFILES) + 1)} combinaciones; con error: {sum(v != 'sin errores' for d in estado.values() for v in d.values())}")
""")
    n.md("### Cifras de la página: antes y después del rediseño (F18-C)\nEl rediseño cambia el diseño y el lenguaje, no las cifras. La única diferencia deliberada es la **cobertura de la cola**: antes la tarjeta usaba la curva interpolada y el texto el conteo observado (70,2 % contra 70,3 %; 96,5 % contra 96,6 %); ahora hay una sola fuente (el conteo observado). Fuente: `pagina_comparacion_antes_despues.csv` y tiempos en `pagina_tiempos_carga.json` (AppTest, caché caliente, meta menor a 3 s).")
    n.code("""
comp = pd.read_csv(REP / "pagina_comparacion_antes_despues.csv")
display(comp[["seccion", "caso", "cifra", "antes", "despues"]])
tiempos = json.loads((REP / "pagina_tiempos_carga.json").read_text(encoding="utf-8"))
display(pd.DataFrame(tiempos["secciones"]).T)
for version in ("f20", "f21"):                      # F20-P12 y F21-P7: tiempos hasta página completa con un navegador sin interfaz (con y sin lanzador)
    ruta = REP / f"pagina_arranque_{version}.json"
    if ruta.exists():
        print(f"Tiempos de arranque, {version.upper()}:")
        ar = json.loads(ruta.read_text(encoding="utf-8"))
        display(pd.DataFrame([{"escenario": e["escenario"][:30], "repetición": e["repeticion"], "servidor (s)": e["servidor_responde_s"], "primera visita (s)": e["primera_visita_explica_s"], **e["secciones_s"]}
                              for e in ar["escenarios"]]))
""")
    n.md("""
## Validación externa sellada (P9) y despliegue
- Los segmentos nuevos **todavía no existen**. `notebooks/00b_seleccion_segmentos_ep3.ipynb` (para Colab) reconstruye la selección de EP2 y toma segmentos nunca evaluados.
- Antes de abrirlos: `scripts/ep3/evaluar_sellado.py congelar` guarda el sha256 de la lista y de los modelos; después `evaluar` corre **una sola vez** (candado) y compara solución elegida contra regla, dos pasos contra un paso; del detector se medirá la tasa de celdas marcadas y su estabilidad (sin verdad externa, DEV-3). Nada se selecciona con esos datos.
- Despliegue: local (`scripts/ep3/arrancar_app.bat`) y Docker (`docker compose up --build`, datos como volumen de solo lectura). Docker **no se probó** (Docker Desktop apagado). La guía de AWS (EC2 + S3 privado) es solo orientativa y advierte que los datos por caja de Waymo no deben salir del equipo. Ver `docs/ep3/despliegue.md`.
""")
    n.guardar("14_ep3_dos_pasos_y_app.ipynb")


# ======================================================================================== 15
def nb15() -> None:
    n = NB()
    n.md("""
# 15. EP3: aprendizaje no supervisado (fase 13; descriptivo, post hoc)

**Qué hacemos.** Agrupamos las cajas de la población principal según *cómo se ven* (distancia, azimut, puntos LiDAR, densidad y volumen) **sin mirar `sin_camara` ni nada del par 2D**, y después preguntamos si esos grupos se parecen a la tasa de cajas sin pareja y si aportan algo que la regla de puntos no tenga.

**Analogía.** Es como ordenar una caja de fotos por parecido (cercanas y nítidas, lejanas y borrosas) antes de saber cuáles fueron archivadas: después vemos si las borrosas se archivan menos.

**Rótulo:** no está en el plan v3, así que todo lo de este notebook es **post hoc, no pre-declarado**. EP2 usó además variables de oclusión que no están en `dev_41`, por lo que la comparación con EP2 no es idéntica.
""")
    n.code(SETUP)
    n.code("""
if RECALCULAR:
    correr("f13_no_supervisado.py")
r13 = json.loads((REP / "f13_resumen.json").read_text(encoding="utf-8"))
k_el = r13["k_elegido"]
selk = pd.read_csv(REP / "f13_seleccion_k.csv")
print(f"Cajas: {miles(r13['filas'])} | variables: {', '.join(r13['variables'])} | muestras: silhouette {miles(r13['muestras']['silhouette'])}, GMM y Ward {miles(r13['muestras']['gmm_y_ward'])}")
display(selk.round(3))
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
axes[0].plot(selk["k"], selk["silhouette_muestra_20000"], "o-", color=AZUL); axes[0].axvline(k_el, color=ROJO, ls="--", label=f"k elegido = {k_el}"); axes[0].set_xlabel("k"); axes[0].set_ylabel("silhouette"); axes[0].legend(); axes[0].set_title("Silhouette (muestra de 20.000)")
axes[1].plot(selk["k"], selk["davies_bouldin"], "o-", color=NARANJA); axes[1].set_xlabel("k"); axes[1].set_ylabel("Davies-Bouldin (menor es mejor)"); axes[1].set_title("Davies-Bouldin")
fig.tight_layout(); guardar_fig(fig, "15_seleccion_k"); plt.show()
display(Markdown(f"**Lectura (generada).** Entre k = 2 y 6 el máximo silhouette es k = {k_el} ({coma(selk.set_index('k').loc[k_el, 'silhouette_muestra_20000'])}); se explora también k = 4 como en EP2 ({coma(selk.set_index('k').loc[4, 'silhouette_muestra_20000'])})."))
""")
    n.md("## Estructura: ¿los grupos son firmes?\nAcuerdo entre técnicas (ARI de KMeans, GMM y Ward en una muestra de 15.000) y estabilidad al remuestrear segmentos (30 réplicas).")
    n.code("""
display(pd.DataFrame(r13["ari_entre_tecnicas"]).T.round(3))
display(pd.read_csv(REP / "f13_estabilidad.csv").round(3))
a2 = r13["ari_entre_tecnicas"]["k=2"]
display(Markdown(f"**Lectura (generada).** El acuerdo entre técnicas es bajo (KMeans contra GMM {coma(a2['KMeans vs GMM'])}, contra Ward {coma(a2['KMeans vs Ward'])} con k = 2): los grupos son una partición cómoda de un continuo, no grupos naturales firmes. La estabilidad al remuestrear segmentos es alta con k = 2 y baja con k = 4."))
""")
    n.md("## Cruce con `sin_camara`, perfil y comparación con la regla\nTasa de `sin_camara` por cluster con IC 95 % por segmentos; probabilidad media que predice la regla (Platt) contra la tasa observada.")
    n.code("""
for k in sorted({k_el, 4}):
    cl = pd.read_csv(REP / f"f13_clusters_k{k}.csv")
    display(Markdown(f"### k = {k}"))
    display(cl[["cluster", "tipo_de_caso", "cajas", "pct_cajas", "tasa_sin_camara", "ic_lo", "ic_hi", "segmentos", "mediana_distancia_m", "mediana_num_lidar_points", "mediana_densidad_puntos", "prob_media_regla_platt", "diferencia_tasa_menos_prob_regla", "AUC_regla_dentro_del_cluster"]].round(3))
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    ax.bar([f"{r.cluster}: {r.tipo_de_caso}" for r in cl.itertuples()], cl["tasa_sin_camara"], yerr=[cl["tasa_sin_camara"] - cl["ic_lo"], cl["ic_hi"] - cl["tasa_sin_camara"]], color=AZUL, capsize=3)
    ax.plot(range(len(cl)), cl["prob_media_regla_platt"], "o", color=NARANJA, label="lo que predice la regla"); ax.set_ylabel("tasa de sin_camara"); ax.tick_params(axis="x", labelsize=7, rotation=15); ax.legend(); ax.set_title(f"Tasa por cluster (k = {k})")
    fig.tight_layout(); guardar_fig(fig, f"15_clusters_k{k}"); plt.show()
""")
    n.md("## ¿Aportan algo que la regla no tenga?\nRegresión logística sobre el logit de la probabilidad de la regla, con y sin indicadoras de cluster; GroupKFold(5) por segmento e IC por segmentos.")
    n.code("""
ap = pd.read_csv(REP / "f13_aporte_cluster.csv")
display(ap.drop(columns=["metodo"]).round(4))
a = ap.set_index("k")
display(Markdown(f"**Lectura (generada).** Con k = 2 el cambio de AUC es {coma(a.loc[2, 'dif_AUC'], 4)} (IC {coma(a.loc[2, 'ic_lo'], 4)} a {coma(a.loc[2, 'ic_hi'], 4)}); con k = 4, {coma(a.loc[4, 'dif_AUC'], 4)} (IC {coma(a.loc[4, 'ic_lo'], 4)} a {coma(a.loc[4, 'ic_hi'], 4)}). **Los clusters no mejoran la predicción de la regla**; con k = 4 incluso la empeoran de forma distinguible."))
""")
    n.md("## IsolationForest (contaminación 1 %) y comparación con EP2")
    n.code("""
iso = r13["isolation_forest"]
print(f"Atípicas: {miles(iso['cajas_atipicas'])} ({pct(iso['porcentaje'])}) en {iso['segmentos_con_atipicos']} de {iso['segmentos_total']} segmentos | tasa de sin_camara: atípicas {pct(iso['tasa_sin_camara_atipicas'])} (IC {pct(iso['ic_atipicas'][0])} a {pct(iso['ic_atipicas'][1])}) contra resto {pct(iso['tasa_sin_camara_resto'])}")
display(pd.DataFrame(iso["top3_segmentos_aportan"]))
cn = pd.read_csv(REP / "f13_comparacion_ep2_ep3.csv")
display(cn.round(3))
display(Markdown("**Lectura (generada).** Los resultados **cambian** respecto de EP2 (silhouette, tasa del cluster de mayor tasa y tasa de los atípicos bajan). Una causa probable es que aquí no hay variables de oclusión y que se usan 41 segmentos en vez de 33; es una hipótesis, no verificada. Los atípicos siguen teniendo mucha más tasa de cajas sin pareja que el resto."))
""")
    n.md("## Artefacto y uso en la página")
    n.code("""
r = subprocess.run([sys.executable, "-X", "utf8", str(RAIZ / "scripts/ep3/verificar_no_supervisado.py")], capture_output=True, text=True, cwd=RAIZ)
print(r.stdout.strip())
display(Markdown("El scaler y el KMeans se guardan en `data/06_models_ep3/no_supervisado_v3.joblib` con su sha256 en `manifest_no_supervisado.json` (independiente de `manifest_v3.json`). **No se usan para puntuar**: la página solo muestra el «tipo de caso» de cada caja con su tasa histórica, y avisa que es una descripción y no mejora la predicción."))
""")
    n.md("""
## Diagnóstico del ARI y AUC por cluster sin celdas con hueco (post hoc, no pre-declarado; F18-A3 y A5)
`f13_ari_diagnostico.csv`: el ARI de 0,008 es del GMM de covarianza `full`; con GMM esférico y diagonal KMeans coincide (0,884 y 0,729). `f13_auc_cluster_sin_huecos.csv`: el AUC de la regla en los clusters cercanos sube al sacar las celdas con hueco.
""")
    n.code("""
diag = pd.read_csv(REP / "f13_ari_diagnostico.csv")
display(diag[diag["covarianza"].notna()][["k", "covarianza", "n_init", "converged", "n_iter", "tamanos", "ARI_vs_KMeans", "ARI_vs_Ward"]].round(3))
auc = pd.read_csv(REP / "f13_auc_cluster_sin_huecos.csv")
display(auc[["k", "cluster", "tipo_de_caso", "cajas", "cajas_en_celdas_con_hueco", "AUC_todas", "AUC_sin_celdas_con_hueco", "dif_AUC"]].round(3))
""")
    n.guardar("15_ep3_no_supervisado.ipynb")


if __name__ == "__main__":
    pedidos = set(sys.argv[1:]) or {"11", "12", "13", "14", "15"}
    for k, f in (("11", nb11), ("12", nb12), ("13", nb13), ("14", nb14), ("15", nb15)):
        if k in pedidos:
            f()
