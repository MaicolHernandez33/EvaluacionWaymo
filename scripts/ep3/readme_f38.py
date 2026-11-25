"""F38: bloques de EP3 del README (portada, mapa de la pauta, 8.1 a 8.3, 12.1, 16 y 17 y las notas de corrección). Los usa ``scripts/generar_readme.py``.

Ninguna cifra está escrita a mano: salen de ``artefactos_ep3/`` (copias versionables de las tablas de EP3), de ``data/06_models*`` y de las MISMAS funciones que usa la página
(``waymo_evaluacion.ep3.app_logica`` y ``validacion``), importadas. Si algo falta, el generador falla con un mensaje (no se rellena nada).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
ART = RAIZ / "artefactos_ep3"
sys.path.insert(0, str(RAIZ / "src"))

COMPONENTE = {"vista_obs": "la vista de observación", "Regla top": "la regla de puntos del sensor superior"}
T81 = "8.1 Optimización de hiperparámetros (IE9)"
T82 = "8.2 Técnicas de ensamble (IE10)"
T83 = "8.3 Capacidad de generalización (IE11)"
T121 = "12.1 Solución elegida y justificación (IE12)"
NOMBRE = {"LR": "Regresión logística (LR)", "RF": "Random Forest (RF)", "HGB": "HistGradientBoosting (HGB)", "XGB": "XGBoost (XGB)", "LGBM": "LightGBM (LGBM)", "LR3": "Regresión logística con 3 variables (LR3)",
          "Regla top": "Regla de puntos del sensor superior"}


# ------------------------------------------------------------------------------------------------------------ formato
def c(x, d=3, signo=False):
    s = f"{float(x):+.{d}f}" if signo else f"{float(x):.{d}f}"
    return s.replace(".", ",")


def p(x, d=1):
    return c(float(x) * 100, d) + " %"


def m(x):
    return f"{int(round(float(x))):,}".replace(",", ".")


def ic(lo, hi, d=3, signo=False):
    return f"{c(lo, d, signo)} a {c(hi, d, signo)}"


def csv(nombre):
    ruta = ART / nombre
    if not ruta.exists():
        sys.exit(f"ERROR (readme_f38): falta {ruta.relative_to(RAIZ)}")
    return pd.read_csv(ruta)


def jsn(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def tabla(filas, encabezado):
    out = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    for f in filas:
        assert len(f) == len(encabezado), f
        out.append("| " + " | ".join(str(x).replace("|", "/") for x in f) + " |")
    return "\n".join(out)


def det(titulo, cuerpo):
    return f"<details>\n<summary>{titulo}</summary>\n\n{cuerpo}\n\n</details>"


# ------------------------------------------------------------------------------------------------------------ datos de entrada y cifras de la app
def entradas():
    ruta = RAIZ / "docs/ep3/readme_entradas.json"
    return jsn(ruta) if ruta.exists() else {}


def despliegue():
    return jsn(RAIZ / "docs/despliegue.json")


_CIFRAS: dict = {}


def cifras_app():
    """Cifras de la página (Lente) calculadas con las mismas funciones de ``app_logica`` que usa la app."""
    if _CIFRAS:
        return _CIFRAS
    from waymo_evaluacion.ep3 import app_logica as A

    D = A.cargar_datos(RAIZ / "data/09_app_ep3")
    det_ = jsn(RAIZ / "data/06_models_ep3/detector_params_v3.json")
    rangos = {int(k): tuple(v) for k, v in det_["rangos"].items()}
    r = A.inicio_resumen(D)
    aud = A.resumen_auditoria(A.matriz_calor(D["celdas"], det_["min_cajas"]), D["lista_A"])
    _, en_cola = A.cola_prioritaria(D["cajas"], rangos)
    cic = A.datos_ciclistas(D["evidencia"].get("posthoc__equidad"))
    cajas, la = D["cajas"], D["lista_A"]
    test = cajas[cajas["grupo"] == "test"]
    fila_test = la[la["grupo"] == "test"].iloc[0]
    seg_anomalo = str(fila_test["segmento"])
    _CIFRAS.update(r, celdas_total=aud["celdas_total"], cajas_afectadas=aud["cajas_afectadas"], sin_pareja=aud["sin_pareja"], en_cola=int(en_cola), segundos=A.SUPUESTO_SEGUNDOS,
                   recall_ciclista=cic["ciclista"], recall_peaton=cic["peaton"], casos_ciclista=cic["positivos"], segmentos_ciclista=cic["segmentos"],
                   pos_test=int(test["sin_camara"].sum()), pos_seg_anomalo=int(test[test["seg"] == seg_anomalo]["sin_camara"].sum()), pos_celda_anomala=int(fila_test["positivos_afectados"]),
                   seg_anomalo=seg_anomalo, modo=A.MODO_DESPLIEGUE, paginas={k: v for k, v in A.DESCRIPCION_PAGINA.items()})
    return _CIFRAS


def rotulo():
    return f"en muestra: {cifras_app()['segmentos']} segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos"


def brazo_c():
    f = csv("f5_brazoC.csv")
    return f[f["candidato"] == "Regla top"].iloc[0]


# ------------------------------------------------------------------------------------------------------------ portada
def ficha(slug):
    e = entradas()
    manifest = jsn(ART / "manifest_v3.json")
    filas = [("Caso", e.get("caso_acordado") or "Waymo Open Dataset v2"), ("Equipo", "Maicol Hernández (rama `maicolhernandez`) y Francis Moya (rama `francismoya`)"),
             ("Solución", f"v3 congelada el {str(manifest.get('congelado', manifest.get('creado', '')))[:10]} (regla «menos puntos top» en dos pasos; hashes en [`artefactos_ep3/manifest_v3.json`](artefactos_ep3/manifest_v3.json))"),
             ("Aplicación", "Lente (Streamlit), sección [16](#" + slug("16. Lente: la aplicación y su despliegue") + ")")]
    return tabla(filas, ["Ficha del proyecto", "Dato"])


def en_breve(slug):
    a, b = cifras_app(), brazo_c()
    return f"""**En breve**

- **Problema.** Algunas cajas 3D de peatones y ciclistas no tienen su par 2D de cámara (`sin_camara`: {p(a['prevalencia'])} de las {m(a['cajas'])} cajas de {a['segmentos']} segmentos) y solo se sabe cuáles son revisándolas una por una.
- **Qué hace Lente.** Flujo en dos pasos: un detector marca las cámaras con hueco (se atienden aparte) y una regla ordena el resto de las cajas por menos puntos del sensor superior; una persona revisa y decide.
- **Resultado ({rotulo()}).** Para encontrar el 80 % de las cajas sin pareja se revisa el {p(b['Fraccion_80_C'])} de las cajas en dos pasos, en vez del {p(b['Fraccion_80_A'])} en uno; revisando el 20 %, se encuentran {c(b['Captura@20_C'] * 100, 1)} de cada 100 frente a {c(b['Captura@20_A'] * 100, 1)}. Con un supuesto de {a['segundos']} s por caja (supuesto, no medido): {m(a['horas_sin_orden'])} h sin orden, {m(a['horas_un_paso'])} h en un paso y {m(a['horas_dos_pasos'])} h en dos.
- **Límites.** El recall de la regla es {p(a['recall_peaton'])} en peatones y {p(a['recall_ciclista'])} en ciclistas ({m(a['casos_ciclista'])} casos en {m(a['segmentos_ciclista'])} segmentos); un segmento concentra el {p(a['pos_seg_anomalo'] / a['pos_test'])} de los positivos del test de EP2; los dos pasos se midieron en muestra; con 4 segmentos nuevos reales solo se probó que la aplicación funciona (1 de 4 trae un posible hueco; no se estima su frecuencia) y la validación externa sellada sigue sin ejecutarse.
"""


def siglas():
    return ("**Siglas.** IC: intervalo de confianza del 95 % (bootstrap por segmentos); AUC: área bajo la curva ROC; PR-AUC: área bajo la curva precisión-recall; LR: regresión logística; LR3: regresión logística con 3 variables; "
            "RF: Random Forest; HGB: HistGradientBoosting; XGB y LGBM: XGBoost y LightGBM; E1 a E4: ensambles (definidos en 8.2); ECE: error de calibración esperado; ARI: índice de Rand ajustado (concordancia entre agrupaciones); "
            "OOF: fuera de fold.")


def como_verlo():
    d = despliegue()
    despl = f"[{d['url']}]({d['url']})" if d.get("url") else "Despliegue en AWS Academy: en preparación"
    filas = [("Ejecutar la aplicación (Lente)", "`.venv\\Scripts\\python.exe app\\lanzar.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false` (o `scripts\\ep3\\arrancar_app.bat`) y abrir http://localhost:8501"),
             ("Reproducir el resultado oficial de EP2", "`.venv\\Scripts\\python.exe -X utf8 scripts\\verificar_congelados.py` y luego el notebook 10 con el kernel `ep2` (comandos completos en la sección 14)"),
             ("Correr las pruebas", "`.venv\\Scripts\\python.exe -m pytest tests/ep3 -q --no-cov -p no:cacheprovider` (EP3); `pytest -q` corre además las de EP2 y regenera README e informe de EP2"),
             ("Aplicación desplegada", despl)]
    return "**Cómo verlo**\n\n" + tabla(filas, ["Qué", "Cómo"])


def mapa_pauta(slug, ancla):
    """Las dos tablas del mapa de la pauta. ``ancla(titulo)`` devuelve el enlace interno de un encabezado."""
    A = [("Problema de negocio", "2", "07", "Tabla de KPIs de la sección 2"), ("Objetivos", "2", "07", "Balance de objetivos (sección 12)"), ("KPIs", "2", "07 y 10", "Tabla de KPIs de la sección 2"),
         ("Fuentes de datos", "4", "00, 02, 03", "Tabla de fuentes y herramientas de la sección 4"), ("Preparación y EDA", "5 y 6", "06 y 08", "Figuras 08 de la sección 5"),
         ("Metodología CRISP-DM", "7", "todos", "Tabla CRISP-DM de la sección 7"), ("Desarrollo de los modelos", "8", "09 y 09b", "Figura 09_comparacion_modelos"),
         ("Hiperparámetros y ensambles", "8.1 y 8.2", "12 (EP3)", "Tablas de `artefactos_ep3/f3_*` y `f4_*`"), ("Evaluación con métricas apropiadas", "8.3, 10 y 12.1", "10 y 13 (EP3)", "Tablas de `f5_*` y `f6_*`"),
         ("Conclusiones, limitaciones y recomendaciones", "12 y 15", "10", "Balance de objetivos y limitaciones")]
    destino = {"2": "contexto", "4": "datos", "5 y 6": "eda", "7": "metodologia", "8": "supervisados", "12 y 15": "recomendaciones"}
    tA = []
    for nombre, sec, nb, ev in A:
        if sec in ("8.1 y 8.2",):
            enlace = f"[8.1]({ancla(T81)}) y [8.2]({ancla(T82)})"
        elif sec == "8.3, 10 y 12.1":
            enlace = f"[8.3]({ancla(T83)}), [10](#{slug('10. Evaluación final en el test')}) y [12.1]({ancla(T121)})"
        elif sec == "12 y 15":
            enlace = f"[12](#{slug('12. Interpretación y recomendaciones')}) y [15](#{slug('15. Mapa de la pauta, referencias, equipo y limitaciones')})"
        elif sec == "5 y 6":
            enlace = f"[5](#{slug('5. EDA y calidad de datos')}) y [6](#{slug('6. Preparación y transformación')})"
        else:
            enlace = f"[{sec}](#{slug(ENC[sec])})"
        tA.append((nombre, enlace, nb, ev))
    B = [("IE1", "Fuentes de datos y herramientas colaborativas", 5, "", "4", "tabla"), ("IE2", "Manipulación de datos en Python", 5, "", "4", "notebook"), ("IE3", "EDA y calidad de datos", 5, "", "5", "figura"),
         ("IE4", "Sesgos, ética y privacidad", 5, "", "13", "tabla"), ("IE5", "Metodología", 10, "", "7", "tabla"), ("IE6", "Modelos supervisados", 10, "", "8", "figura y tabla"),
         ("IE7", "Aprendizaje no supervisado", 10, "", "9", "figura"), ("IE8", "Interpretación del desempeño", 10, "", "10 a 12", "figura y tabla"),
         ("IE9", "Optimización de hiperparámetros", 10, 20, "8.1", "tabla"), ("IE10", "Técnicas de ensamble", 10, 30, "8.2", "tabla"),
         ("IE11", "Capacidad de generalización", 10, 20, "8.3", "tabla y notebook"), ("IE12", "Selección de la solución óptima", 10, 30, "12.1", "tabla y prueba automática")]
    assert sum(x[2] for x in B) == 100 and sum(x[3] for x in B if x[3]) == 100
    link = {"8.1": ancla(T81), "8.2": ancla(T82), "8.3": ancla(T83), "12.1": ancla(T121), "10 a 12": f"#{slug('10. Evaluación final en el test')}"}
    tB = []
    for ie, nombre, eft, ep3, sec, nivel in B:
        url = link.get(sec) or f"#{slug(ENC[sec])}"
        tB.append((f"{ie}: {nombre}", f"{eft} %", f"{ep3} %" if ep3 else "—", f"[{sec}]({url})", nivel))
    return ("**A. Secciones mínimas del informe**\n\n" + tabla(tA, ["Sección pedida", "Dónde está", "Notebook", "Evidencia"]) + "\n\n**B. Indicadores de evaluación**\n\n" +
            tabla(tB, ["Indicador", "Peso en la EFT", "Peso en EP3", "Dónde se demuestra", "Nivel de evidencia"]))


ENC = {"2": "2. Contexto, valor de negocio, objetivos y KPIs", "4": "4. Datos", "5": "5. EDA y calidad de datos", "6": "6. Preparación y transformación", "7": "7. Metodología (CRISP-DM)",
       "8": "8. Modelos supervisados", "9": "9. Aprendizaje no supervisado", "13": "13. Ética, sesgos y privacidad", "10 a 12": "10. Evaluación final en el test"}


# ------------------------------------------------------------------------------------------------------------ 8.1 a 8.3
def sec_81():
    d, b = csv("f3_defecto_vs_optimizado.csv"), csv("f3_bordes.csv")
    hip = jsn(RAIZ / "data/06_models/hiperparametros_B.json")["final"]
    mejoran = [NOMBRE[x].split(" (")[0] for x in d[d["veredicto"] == "mejora"]["modelo"]]
    no = [NOMBRE[x].split(" (")[0] for x in d[d["veredicto"] != "mejora"]["modelo"]]
    filas = [(NOMBRE[r["modelo"]], f"{c(r['AUC_def'])} ({ic(r['AUC_def_lo'], r['AUC_def_hi'])})", f"{c(r['AUC_opt'])} ({ic(r['AUC_opt_lo'], r['AUC_opt_hi'])})",
              f"{c(r['Fraccion_80_def'])} a {c(r['Fraccion_80_opt'])}", f"{c(r['dif_PR-AUC'], 3, True)} ({ic(r['dif_PR-AUC_lo'], r['dif_PR-AUC_hi'], 3, True)})", r["veredicto"]) for _, r in d.iterrows()]
    bordes = b[b["borde"] != "no"]
    texto_bordes = "; ".join(f"{r['modelo']} `{r['hiperparametro']}` en el {'máximo' if r['borde'] == 'max' else 'mínimo'} de la grilla en {int(r['folds_en_' + r['borde']])} de 5 folds" for _, r in bordes.iterrows()) or "ninguno"
    xgb = csv("f6_tabla_seleccion.csv").set_index("candidato").loc["XGB"]
    return f"""### {T81}

{recuadro_cifras()}

> Optimizar mejora a {' y '.join(mejoran)} y no mejora a {', '.join(no[:-1])} ni a {no[-1]}; ni siquiera el XGBoost optimizado supera a la regla de una línea.

**Método.** Búsqueda aleatoria **anidada por segmento**: dentro de cada uno de los 5 folds externos (por segmento), la elección usa solo los segmentos de entrenamiento, con una validación interna `GroupKFold` de 3 y la PR-AUC como criterio de selección; el conjunto de variables cuenta como un hiperparámetro más. Fueron 30 configuraciones y 1 repetición, una desviación del plan (DEV-1, [`plan_v3_desviaciones.md`](artefactos_ep3/plan_v3_desviaciones.md)). «Mejora» exige subir la PR-AUC al menos 0,010 con un IC pareado por segmentos que excluya 0. Es como afinar un instrumento: ayuda si estaba desafinado y no si ya sonaba bien.

{tabla(filas, ['Modelo', 'AUC por defecto (IC)', 'AUC optimizado (IC)', 'Fracción para 80 %: defecto a optimizado', 'Dif. PR-AUC (IC)', 'Veredicto'])}

Fuente: [`artefactos_ep3/f3_defecto_vs_optimizado.csv`](artefactos_ep3/f3_defecto_vs_optimizado.csv) y [`f3_bordes.csv`](artefactos_ep3/f3_bordes.csv). Los IC son por bootstrap de segmentos.

**Bordes de la grilla.** Tocan el borde: {texto_bordes}. El plan permite una sola extensión de grilla y ya se usó en LightGBM `min_child_samples`: queda como limitación declarada.

**Qué decidimos y por qué.**
- **Regularizar fuerte.** Los tres modelos de EP2 terminaron regularizados: regresión logística con `C` = {c(hip['LR']['cfg']['C'], 3)} (penalización fuerte), HGB con `max_leaf_nodes` = {hip['HGB']['cfg']['max_leaf_nodes']} y `min_samples_leaf` = {hip['HGB']['cfg']['min_samples_leaf']}, Random Forest con `max_depth` = {hip['RF']['cfg']['max_depth']} y `min_samples_leaf` = {hip['RF']['cfg']['min_samples_leaf']}. Con pocos segmentos y variables muy correlacionadas (los puntos del LiDAR), un modelo simple generaliza mejor.
- **Optimizar no cambia la elección.** El mejor modelo único optimizado, XGBoost, queda {c(abs(xgb['dif_AUC_vs_regla']))} de AUC bajo la regla (IC {ic(xgb['dif_AUC_lo'], xgb['dif_AUC_hi'], 3, True)} de la diferencia modelo menos regla). La regla no tiene hiperparámetros que buscar: solo dos umbrales congelados.
- Hipótesis sin verificar: la búsqueda interna puede aprovechar particularidades de los segmentos de entrenamiento y no sostenerse en el fold de validación."""


def sec_82():
    from waymo_evaluacion.ep3.validacion import DESCRIPCION_CANDIDATOS as DC

    desc = {k: v for k, v, _ in DC}
    t = csv("f4_candidatos_metricas.csv").set_index("candidato")
    ens = csv("f4_ensambles_aporta.csv").set_index("ensamble")
    sel = csv("f6_tabla_seleccion.csv").set_index("candidato")
    filas = []
    for k, nombre, que in [("RF", "Random Forest (bagging)", "muchos árboles sobre muestras distintas de las filas; promedia sus votos"),
                           ("HGB", "HistGradientBoosting (boosting)", "árboles en secuencia: cada uno corrige el error del anterior"), ("XGB", "XGBoost (boosting)", "boosting regularizado de árboles"),
                           ("LGBM", "LightGBM (boosting)", "boosting de árboles por hojas"), ("E1", "E1 · voto suave", desc["E1"]), ("E2", "E2 · promedio de rangos con la regla", desc["E2"]),
                           ("E3", "E3 · apilamiento de cinco modelos", desc["E3"]), ("E4", "E4 · apilamiento por tres vistas", desc["E4"])]:
        r, s = t.loc[k], sel.loc[k]
        if k in ens.index:
            e = ens.loc[k]
            comp = f"{c(e['dif_AUC'], 3, True)} ({ic(e['dif_lo'], e['dif_hi'], 3, True)}) frente a {COMPONENTE.get(e['mejor_componente'], NOMBRE.get(e['mejor_componente'], e['mejor_componente']).split(' (')[0])}"
            veredicto = e["veredicto"]
        else:
            comp, veredicto = "—", "no vale la pena (O2)"
        filas.append((nombre, que, f"{c(r['AUC'])} ({ic(r['AUC_lo'], r['AUC_hi'])})", f"{c(r['Fraccion_80'])} ({ic(r['Fraccion_80_lo'], r['Fraccion_80_hi'])})", comp,
                      f"{c(s['dif_Fraccion_80_vs_regla'], 3, True)} ({ic(s['dif_Fraccion_80_lo'], s['dif_Fraccion_80_hi'], 3, True)})", veredicto))
    regla, xgb, e2 = t.loc["Regla top"], t.loc["XGB"], sel.loc["E2"]
    return f"""### {T82}

> Ningún ensamble aporta: E1 queda dentro del ruido sobre su mejor componente, E2 empata con la regla porque la contiene, y E3 y E4 quedan por debajo.

Promediar compañeros solo ayuda si se equivocan en cosas distintas; aquí todos miran lo mismo, los puntos del LiDAR. «Aporta» exige +0,010 de AUC sobre el mejor componente con un IC pareado por segmentos que excluya 0; «vale la pena» frente a la regla (O2) exige bajar la fracción para 80 % al menos 5 puntos y subir el AUC 0,03.

{tabla(filas, ['Técnica', 'Qué combina', 'AUC (IC)', 'Fracción para 80 % (IC)', 'Dif. AUC frente a su mejor componente (IC)', 'Dif. fracción para 80 % frente a la regla (IC)', '¿Vale la pena?'])}

Fuente: [`f4_candidatos_metricas.csv`](artefactos_ep3/f4_candidatos_metricas.csv), [`f4_ensambles_aporta.csv`](artefactos_ep3/f4_ensambles_aporta.csv) y [`f6_tabla_seleccion.csv`](artefactos_ep3/f6_tabla_seleccion.csv). Un valor positivo en la fracción significa revisar más cajas que la regla.

**Qué decidimos y por qué.** El mejor modelo único es XGBoost (AUC {c(xgb['AUC'])}) y la regla lo supera ({c(regla['AUC'])}). E2 tiene el AUC más alto ({c(t.loc['E2']['AUC'])}), pero su diferencia frente a la regla es {c(e2['dif_AUC_vs_regla'], 3, True)} (IC {ic(e2['dif_AUC_lo'], e2['dif_AUC_hi'], 3, True)}) y además la incluye como componente: no hay mejora distinguible y elegirlo costaría una pieza más. Mostramos el resultado negativo porque la rúbrica pide demostrar el aporte, y aquí el aporte medido es nulo. Detalle: [informe de EP3, sección 10.2](docs/ep3/informe_tecnico_EP3.md)."""


def sec_83():
    f = csv("f5_auc_por_fold.csv")
    cands = [x for x in ("Regla top", "LR3", "XGB", "E2") if x in set(f["candidato"])]
    filas = []
    for k in cands:
        g = f[f["candidato"] == k].sort_values("fold")
        filas.append([NOMBRE.get(k, k).split(" (")[0] if k != "E2" else "E2 · promedio de rangos"] + [c(x) for x in g["AUC"]] + [c(g["AUC"].min())])
    nf = int(f["fold"].nunique())
    loso = jsn(ART / "f5_loso_resumen_Regla_top.json")
    bre = csv("f5_brecha_XGB.csv")
    bre = bre[bre["n_segmentos"].isin([32, 34])]
    final = jsn(ART / "f12_resumen.json")
    bc, sel = brazo_c(), csv("f6_tabla_seleccion.csv").set_index("candidato").loc["Regla top"]
    return f"""### {T83}

> La regla se sostiene fuera de fold (AUC {c(loso['AUC'])}, IC {ic(*loso['AUC_ic'])}), y la única debilidad es un fold con un segmento sin pares en una cámara.

**Validación usada.** `StratifiedGroupKFold` de {nf} folds (estratificado por `sin_camara`, agrupado por segmento, semilla 42): un segmento son unos 20 segundos de video con casi 200 fotogramas parecidos entre sí, así que una escena repartida entre entrenamiento y prueba haría trampa. Los IC salen de remuestrear segmentos completos (1.000 réplicas) y la búsqueda de hiperparámetros va anidada (8.1). Con 41 segmentos los IC son anchos. Las cifras de esta sección no son las de la sección 8 (EP2 evaluó 33 segmentos): ver el recuadro de [8.1](#{ancla_81()}).

{tabla(filas, ['AUC por fold'] + [f'Fold {i}' for i in range(nf)] + ['Mínimo'])}

Fuente: [`f5_auc_por_fold.csv`](artefactos_ep3/f5_auc_por_fold.csv). El fold 0 es el más bajo de todos porque contiene el segmento `{final['C_en_fold_0_regla']['hueco'].split()[0]}`, con la cámara 3 sin pares. Con el brazo B (sin las celdas marcadas) el mínimo por fold sube a {c(final['B_AUC_min_fold']['Regla top'])} ({rotulo()}).

- **Por segmento** (dejando uno fuera, regla): mediana del AUC {c(loso['AUC_mediana_segmento'])}; de {loso['segmentos_evaluables']} segmentos evaluables, {loso['segmentos_con_AUC_menor_a_0_55']} quedan bajo 0,55 (mínimo {c(loso['AUC_min_segmento'])}).
- **Brecha ajuste-validación.** La regla no aprende, así que no tiene brecha real. XGBoost con todos los segmentos de entrenamiento: ajuste {c(bre['AUC_ajuste'].mean())}, validación {c(bre['AUC_validacion'].mean())}, brecha {c(bre['brecha_AUC'].mean())} que no se cierra con más segmentos ([`f5_brecha_XGB.csv`](artefactos_ep3/f5_brecha_XGB.csv)).
- **Calibración.** Con Platt, el ECE de la regla es {c(sel['ECE_cal'])}.
- **Uno frente a dos pasos** ({rotulo()}): revisar el {p(bc['Fraccion_80_C'])} de las cajas para el 80 % (IC {ic(bc['Fraccion_80_C_lo'] * 100, bc['Fraccion_80_C_hi'] * 100, 1)} %) en vez del {p(bc['Fraccion_80_A'])}; la ganancia sale de {int(bc['celdas_auditadas'])} celdas cámara por segmento ([`f5_brazoC.csv`](artefactos_ep3/f5_brazoC.csv)).
- **Test de EP2 y qué cambió.** En EP2 el test de 8 segmentos estuvo sellado. En EP3 los 41 segmentos (33 de entrenamiento y los 8 de test de EP2, {m(cifras_app()['cajas'])} cajas) son **datos de desarrollo** de la solución v3: ya los miramos varias veces. La única prueba ciega son los segmentos nuevos: la validación externa sellada ([`plan_seleccion_ep3.json`](artefactos_ep3/plan_seleccion_ep3.json)) está preparada y **no se ha ejecutado**. La prueba de la aplicación con 4 segmentos nuevos reales (sección 16) es una prueba de funcionamiento, no una validación estadística: no estima la frecuencia de los huecos ni reemplaza a la validación externa sellada."""


# ------------------------------------------------------------------------------------------------------------ 12.1
def sec_121():
    s = csv("f6_tabla_seleccion.csv")
    sel = jsn(ART / "f6_seleccion.json")
    a, bc = cifras_app(), brazo_c()
    nombres = {"Regla top": "Regla de una línea (puntos del sensor superior)", "LR3": "Regresión logística con 3 variables", "LR": "Regresión logística con 16 variables", "RF": "Random Forest", "HGB": "HistGradientBoosting",
               "XGB": "XGBoost", "LGBM": "LightGBM", "E1": "E1 · voto suave", "E2": "E2 · promedio de rangos con la regla", "E3": "E3 · apilamiento de cinco modelos", "E4": "E4 · apilamiento por tres vistas"}
    sn = lambda x: "sí" if bool(x) else "no"                                                                    # noqa: E731
    filas = []
    for _, r in s.iterrows():
        if r["candidato"] == "Regla top":
            ver = "elegida (la más simple)"
            difauc = "referencia"
        else:
            lo, hi = r["dif_AUC_lo"], r["dif_AUC_hi"]
            ver = "peor que la regla" if hi < 0 else ("mejor que la regla" if lo > 0 else "no distinguible de la regla")
            difauc = f"{c(r['dif_AUC_vs_regla'], 3, True)} ({ic(r['dif_AUC_lo'], r['dif_AUC_hi'], 3, True)})"
        filas.append((nombres[r["candidato"]], sn(r["O1"]), sn(r["O2"]), sn(r["O3"]), sn(r["O4"]), difauc, ver))
    filas.append(("Versión de un paso (brazo A)", "—", "—", "—", "—", "—", f"fracción para 80 %: {p(bc['Fraccion_80_A'])}"))
    filas.append(("Versión de dos pasos (brazo C)", "—", "—", "—", "—", "—", f"fracción para 80 %: {p(bc['Fraccion_80_C'])} ({rotulo().split(';')[0]})"))
    return f"""### {T121}

> La solución elegida es la regla «menos puntos top» en dos pasos (auditar cámaras y luego ordenar la cola), porque ninguna alternativa más compleja la supera de forma distinguible.

Los criterios se fijaron antes de ver resultados ([`plan_v3.md`](artefactos_ep3/plan_v3.md)): O1 AUC mínimo y PR-AUC sobre la prevalencia; O2 «vale la pena» frente a la regla; O3 recall mínimo en el punto A; O4 estabilidad por fold y calibración.

{tabla(filas, ['Alternativa', 'O1', 'O2', 'O3', 'O4', 'Dif. AUC frente a la regla (IC)', 'Veredicto'])}

Fuente: [`f6_tabla_seleccion.csv`](artefactos_ep3/f6_tabla_seleccion.csv) y [`f6_seleccion.json`](artefactos_ep3/f6_seleccion.json). Ningún candidato cumple O4 (el fold 0, ver 8.3) y ninguno cumple O2.

**Qué decidimos y por qué.** {sel['razon'][0].upper() + sel['razon'][1:]}. Aplicamos una regla de reserva (DEV-2, post hoc, no pre-declarada): el plan manda elegir entre los que cumplen O1, O3 y O4, pero nadie cumple O4, así que elegimos por simplicidad entre los que cumplen O1 y O3 y declaramos la estabilidad como limitación de todos.

**Por qué es la óptima.** Empata en desempeño con todo lo más complejo, se explica en una línea, no tiene hiperparámetros que se desajusten y es auditable caja por caja. Frente a los objetivos de negocio ({rotulo()}): con un presupuesto del 20 %, se encuentran {c(bc['Captura@20_C'] * 100, 1)} de cada 100 cajas sin pareja en dos pasos frente a {c(bc['Captura@20_A'] * 100, 1)} en uno, y para el 80 % se revisa el {p(bc['Fraccion_80_C'])} en vez del {p(bc['Fraccion_80_A'])}; con {a['segundos']} s por caja (supuesto) son {m(a['horas_dos_pasos'])} h en vez de {m(a['horas_sin_orden'])} h sin orden. El punto de equilibrio es {m(bc['equilibrio_cajas_por_auditoria'])} cajas por auditoría: no inventamos un costo de auditar.

**Por qué no un modelo más complejo.** Probamos cinco algoritmos, una regresión logística de tres variables y cuatro ensambles (uno de ellos con la regla): ninguno cumple O2 y todos salvo E2 quedan significativamente peores que la regla en AUC. Un modelo más complejo cuesta mantenimiento, explicación y riesgo de sobreajuste con 41 segmentos, sin una mejora medible que lo pague."""


# ------------------------------------------------------------------------------------------------------------ 16 y 17
PAGINAS = [("Resumen", "Estado de las cámaras del día y las primeras cajas de la cola", "quien abre la herramienta a diario", "Indicadores, alertas de cámara y cola prioritaria"),
           ("Auditoría de cámaras", None, "supervisores de cámaras", "Mapa de calor segmento por cámara y celdas marcadas"),
           ("Cola de revisión", None, "analistas que revisan cajas", "Curvas de captura y lista descargable en CSV"),
           ("Validación", None, "quien decide si se confía en la regla", "Resultados con IC, alternativas, ensambles y tablas de apoyo"),
           ("Explica una caja", None, "analistas que dudan de una caja", "Lugar que ocuparía la caja en la cola y si se revisaría"),
           ("Puntuar datos nuevos", "Puntúa un segmento nuevo en memoria y entrega sus celdas marcadas y su cola", "quien recibe segmentos nuevos", "Resultado descargable; no se guarda nada"),
           ("Ética y límites", None, "quien audita el uso del sistema", "Propósito, datos, desempeño, límites y dónde corre"),
           ("Ayuda y glosario", None, "quien usa la herramienta por primera vez", "Tres pasos, glosario con buscador y preguntas frecuentes")]


def sec_16(fig, slug):
    a = cifras_app()
    d = despliegue()
    paginas = a["paginas"]
    filas = [(n, (paginas.get(n) or q), quien, ev) for n, q, quien, ev in PAGINAS]
    cifras = [("Segmentos de desarrollo", m(a["segmentos"])), ("Cajas de peatones y ciclistas (población principal)", m(a["cajas"])), ("Celdas segmento × cámara", m(a["celdas_total"])),
              ("Celdas marcadas por el detector", m(a["celdas_marcadas"])), ("Cajas en las celdas marcadas", m(a["cajas_afectadas"])), ("Cajas en la cola", m(a["en_cola"]))]
    url_txt = f" Dirección: [{d['url']}]({d['url']})." if d.get("url") else ""
    return f"""## 16. Lente: la aplicación y su despliegue

> Lente convierte el resultado en una herramienta de trabajo: un supervisor ve qué cámaras tienen huecos, un analista revisa la cola en orden y una persona siempre decide.

**Qué es y para quién.** Una aplicación Streamlit para supervisores de cámaras y analistas que manejan cientos de segmentos al día. Sigue el flujo en dos pasos y no etiqueta ni borra nada:

```
 segmentos nuevos --> 1 · Filtro: detector de huecos --> celdas marcadas (se auditan aparte)
                              |
                              +--> 2 · Priorización: regla de puntos top --> cola ordenada --> una persona revisa y decide
```

{tabla(filas, ['Página', 'Qué responde', 'A quién sirve', 'Evidencia que muestra'])}

{fig('app/lente_resumen.png', 'Resumen de Lente: indicadores, alertas de cámara y cola prioritaria')}

{fig('app/lente_auditoria.png', 'Auditoría de cámaras: mapa de calor segmento por cámara y celdas marcadas')}

{fig('app/lente_cola.png', 'Cola de revisión: tarjetas, curva de captura y lista de cajas')}

{fig('app/lente_puntuar_ejemplo.png', 'Puntuar datos nuevos con el segmento de desarrollo de ejemplo y su celda marcada')}

**Cifras de la app** (calculadas por las mismas funciones que muestra la página; son de desarrollo, {rotulo()}):

{tabla(cifras, ['Cifra', 'Valor'])}

**Ejecutarla.** `.venv\\Scripts\\python.exe app\\lanzar.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false` (o `scripts\\ep3\\arrancar_app.bat`); escucha solo en `localhost`.

{sec_prueba_nuevos()}

**Despliegue en AWS Academy.** Estado: **{d['estado']}** (modo `{d['modo']}`, registrado el {d['fecha']}; archivo [`docs/despliegue.json`](docs/despliegue.json), que este README lee).{url_txt} La licencia de Waymo es no comercial y sin redistribución: antes de publicar hay que decidir qué datos viajan (la aplicación usa `cajas_oof.parquet`, derivado por caja con identificadores y marcas de tiempo; [`f36_verificacion_despliegue.json`](docs/ep3/f36_verificacion_despliegue.json)). Guía y textos del modo publicado: [`despliegue.md`](docs/ep3/despliegue.md).

**Fase 6 de CRISP-DM.** La aplicación es el despliegue de la sección [7](#{slug('7. Metodología (CRISP-DM)')}). Informe de la página: [`informe_tecnico_EP3.md`](docs/ep3/informe_tecnico_EP3.md), sección 13."""


def sec_17():
    e = entradas()
    t = [("En EP1 el target era `tiene_camara`", "En EP2 pasó a `sin_camara`, tras comparar cinco candidatas", "Notebook 07 y [sección 2](#2-contexto-valor-de-negocio-objetivos-y-kpis)"),
         ("EP2 sellaba un test de 8 segmentos con un plan congelado", "En EP3 el plan v3 se congeló antes de experimentar y la prueba ciega pasó a ser la validación externa sellada", "Sección 8.3; `artefactos_ep3/plan_v3.json` y `plan_seleccion_ep3.json`"),
         ("En EP2 ningún modelo superó a una regla de una línea", "En EP3 la regla es la solución elegida y se justifica con criterios fijados antes", "Sección [12.1](#121-solución-elegida-y-justificación-ie12)"),
         ("En EP2 un segmento concentró el problema (hallazgo post hoc)", "La auditoría por cámara pasó a ser el paso 1, con un detector de huecos de parámetros congelados", "Sección 11; `artefactos_ep3/detector_params_v3.json`"),
         ("EP2 comparó tres modelos con sus hiperparámetros, sin ensambles", "EP3 agrega XGBoost, LightGBM, búsqueda anidada y cuatro ensambles, con el resultado negativo declarado", "Secciones 8.1 y 8.2"),
         ("En EP2 el resultado vivía en notebooks e informe", "Lente: una aplicación con el flujo en dos pasos", "Sección 16")]
    recibidas = [(k, e[k]) for k in ("retroalimentacion_ep1", "retroalimentacion_ep2") if e.get(k)]
    extra = "".join(f"\n\n<details>\n<summary>Retroalimentación recibida sobre {k[-3:].upper()}</summary>\n\n{txt}\n\n</details>" for k, txt in recibidas)
    opciones = e.get("opciones_docente", "")
    if opciones:
        t.insert(4, ("El docente ofreció tres opciones ante el segmento anómalo: excluirlo, usarlo como filtro de errores o el esquema propuesto por el equipo", "El equipo adoptó su esquema: filtro de cámaras aparte con su lista de revisión (paso 1) y priorización sobre los segmentos normales (paso 2)",
                     "Secciones 11, 12 y 16; `artefactos_ep3/detector_params_v3.json`"))
    t.append(("La validación de la solución solo con segmentos de desarrollo", "Prueba de funcionamiento con 4 segmentos nuevos reales y validación externa sellada preparada", "Secciones 8.3 y 16; `docs/ep3/prueba_segmentos_nuevos.json`"))
    aviso = "\n\nEsta tabla recoge las mejoras documentadas en el repositorio y en `docs/log_trabajo_ep2.md`." + extra
    return f"""## 17. Mejoras incorporadas desde EP1 y EP2

> Cada cambio de EP3 responde a algo que detectamos en EP1 o EP2, y todos tienen su evidencia en el repositorio.

{tabla(t, ['Qué se detectó o se sugirió', 'Qué cambió', 'Dónde se ve'])}{aviso}"""


# ------------------------------------------------------------------------------------------------------------ notas y bloques sueltos
def nota_test_sellado():
    return (f"En EP3 esos {cifras_app()['segmentos']} segmentos (33 de entrenamiento y 8 de test de EP2, {m(cifras_app()['cajas'])} cajas) son datos de desarrollo de la solución v3; "
            "la única prueba ciega son los segmentos nuevos (sección 8.3).")


def nota_54_8():
    a = cifras_app()
    return (f"El {p(a['pos_seg_anomalo'] / a['pos_test'])} es la parte del segmento `{a['seg_anomalo']}` en los positivos del test ({m(a['pos_seg_anomalo'])} de {m(a['pos_test'])}); "
            f"solo la celda de la cámara 3 de ese segmento explica el {p(a['pos_celda_anomala'] / a['pos_test'])} ({m(a['pos_celda_anomala'])} de {m(a['pos_test'])}).")


def nota_k2():
    k = csv("f13_clusters_k2.csv")
    f = [f"{m(r['cajas'])} cajas con tasa de `sin_camara` de {p(r['tasa_sin_camara'])}" for _, r in k.iterrows()]
    return ("> **Dos resultados con k = 2, dos poblaciones.** Los de esta sección (EP2, notebook 08) se calcularon sobre las 68.555 filas de train con |azimut| de hasta 120°, con seis variables (incluida la oclusión). "
            f"La aplicación (Validación › Tipos de caso, notebook 15, post hoc, no pre-declarado) usa las {m(k['cajas'].sum())} cajas de la población principal (|azimut| hasta 100°) de los {cifras_app()['segmentos']} segmentos de desarrollo, con cinco variables (sin oclusión): "
            + " y ".join(f) + ". Para el informe de EP2 vale este; para la página, el de EP3.")


def bloque_herramientas():
    nb03 = (RAIZ / "notebooks/03_fuentes_y_colaboracion.ipynb").read_text(encoding="utf-8")
    assert "maicolhernandez" in nb03 and "francismoya" in nb03
    nb04 = (RAIZ / "notebooks/04_estructuras_y_almacenamiento.ipynb").read_text(encoding="utf-8")
    ahorro = re.search(r"Ahorro conseguido \| ([\d,]+)\s?%", nb04)
    csv_mb = re.search(r"Peso en CSV \(tipos optimizados\) \| ([\d,]+) MB", nb04)
    pq_mb = re.search(r"Peso en Parquet \(tipos optimizados\) \| ([\d,]+) MB", nb04)
    ie2 = (f"**Manipulación de datos en Python (IE2).** [Notebook 04](notebooks/04_estructuras_y_almacenamiento.ipynb): listas frente a NumPy, tipos de columna (ahorro de memoria de {ahorro.group(1)} %), "
           f"CSV frente a Parquet ({csv_mb.group(1)} MB frente a {pq_mb.group(1)} MB) y la ingesta con Kedro (`src/waymo_evaluacion/pipelines`).") if ahorro and csv_mb and pq_mb else ""
    filas = [("GitHub: ramas `main`, `maicolhernandez` y `francismoya`", "Trabajo en paralelo y revisión por rama (acuerdo del [notebook 03](notebooks/03_fuentes_y_colaboracion.ipynb), bloque 6)", "Deja historial revisable y evita pisarse; el acuerdo prohíbe empujar directo a `main`"),
             ("Bucket de Waymo v2 con `gsutil` desde Google Colab", "Descargar solo `lidar_box` y `camera_to_lidar_box_association` de cada segmento ([notebooks 00 y 00b](notebooks/00_exploracion_bucket_waymo.ipynb))", "Es donde publica Waymo; los archivos son grandes y solo hacen falta dos componentes"),
             ("Kedro", "Pipelines de ingesta y preprocesamiento (`kedro run`, [README de EP1](docs/README_EP1.md))", "Estructura reproducible por nodos; guarda en Parquet, que conserva tipos"),
             ("pytest", "Pruebas de pipelines, README, informe y página (sección 14)", "Detectan cifras que se desincronizan entre documentos"),
             ("sha256 de archivos congelados", "`scripts/verificar_congelados.py` y `verificar_congelados_v3.py`", "Prueba que modelos y planes no cambiaron antes de abrir el test"),
             ("Streamlit", "Lente, la aplicación (sección 16)", "Una página interactiva en Python, sin escribir front-end; probada con `AppTest`")]
    return f"""**Fuentes y herramientas colaborativas (IE1).**

{tabla(filas, ['Fuente o herramienta', 'Para qué la usamos', 'Por qué esa y no otra'])}

Reparto de ramas: `git branch -a` lista `main`, `maicolhernandez` y `francismoya` (también en `origin`). No usamos MLflow (decisión DEC-6 de [`ESTADO.md`](docs/ep3/ESTADO.md)); S3 solo aparece en la guía orientativa de despliegue ([`despliegue.md`](docs/ep3/despliegue.md)), que no se ejecutó.

{ie2}"""


def parrafo_etica_app():
    return ("**La aplicación (Lente).** Procesa tablas derivadas por caja (identificadores de objeto y marcas de tiempo, sin imágenes). «Puntuar datos nuevos» trabaja en memoria y no guarda los archivos que se suben; hoy corre solo en `localhost`. "
            "Al desplegarla cambia el supuesto: el servidor recibe los archivos, así que no deben subirse datos que no puedan compartirse con él, y la licencia no comercial de Waymo exige no redistribuir datos. "
            "Los textos para el modo publicado (`MODO_DESPLIEGUE`) son borradores sin activar. Decidir qué datos viajan sigue pendiente (sección 16).")


def parrafo_pruebas_ep3():
    conteo = jsn(RAIZ / "data/08_reporting_ep3/pruebas_ep3_conteo.json")
    res = RAIZ / "data/08_reporting_ep3/pruebas_ep3_resultado.json"
    ep2 = RAIZ / "data/08_reporting_ep3/pruebas_ep2_remedicion.json"
    previo = ""
    if ep2.exists():
        q = jsn(ep2)
        previo = (f"**Remedición de las pruebas de EP2** ({q['fecha']}, en una copia temporal del repositorio, `pytest --ignore=tests/ep3`): {q['pasadas']} pasadas, {q['falladas']} falladas, "
                  f"{q['omitidas']} omitidas. La cobertura de EP2 sigue siendo la medida en EP2, arriba: en la copia el paquete se importa del repositorio real y la medición no sería fiable.\n\n")
    base = previo + f"**Pruebas de EP3.** {m(conteo['recolectadas_ep3'])} pruebas recolectadas en `tests/ep3` (`scripts/ep3/contar_pruebas.py`)"
    if res.exists():
        r = jsn(res)
        return base + f"; última corrida ({r['fecha']}, `scripts/ep3/medir_pruebas_ep3.py`): {r['pasadas']} pasadas, {r['falladas']} falladas, {r['omitidas']} omitidas, cobertura de `src/waymo_evaluacion/ep3` {c(r['cobertura_total_pct'], 1)} %. Comando: `.venv\\Scripts\\python.exe -m pytest tests/ep3 -q --no-cov -p no:cacheprovider`."
    return base + ". Comando: `.venv\\Scripts\\python.exe -m pytest tests/ep3 -q --no-cov -p no:cacheprovider`."


# ------------------------------------------------------------------------------------------------------------ F40: prueba con segmentos nuevos, cifras EP2 frente a EP3, árbol y notebooks
def ancla_81() -> str:
    t_ = unicodedata.normalize("NFC", T81.lower())
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", t_).strip())


def prueba_nuevos() -> dict:
    ruta = RAIZ / "docs/ep3/prueba_segmentos_nuevos.json"
    if not ruta.exists():
        sys.exit("ERROR (readme_f38): falta docs/ep3/prueba_segmentos_nuevos.json (scripts/ep3/f40_prueba_segmentos_nuevos.py)")
    return jsn(ruta)


def sec_prueba_nuevos() -> str:
    d = prueba_nuevos()
    filas = []
    for s in d["segmentos"]:
        if s["celdas"]:
            z = s["celdas"][0]
            detalle = (f"{z['camara']}: {m(z['cajas_en_rango'])} cajas en el rango, {m(z['cajas_afectadas'])} afectadas, {m(s['sin_pareja_en_celdas_marcadas'])} sin pareja ({p(s['porcentaje_sin_pareja_en_celdas'])}), "
                       f"tasa de pares {p(z['tasa_de_pares'])} frente a una mediana de referencia de {p(z['mediana_de_referencia'])} (umbral {p(z['umbral'])})")
        else:
            detalle = "—"
        filas.append((f"`{s['segmento']}`", s["id_abreviado"], m(s["cajas_puntuadas"]), s["celdas_marcadas"], detalle))
    la = csv("lista_A_huecos.csv")
    dev = " y ".join(f"cámara {str(r['camara'])[0]} (segmento …{str(r['segmento'])[-6:]})" for _, r in la.iterrows())
    n_marc = sum(1 for s in d["segmentos"] if s["celdas_marcadas"])
    origen = d["origen"].get("split") or "validation"
    return f"""### Prueba con segmentos nuevos

Se puntuaron en la aplicación 4 segmentos reales **nuevos** (split `{origen}` del bucket de Waymo v2; los 41 de desarrollo y los candidatos del plan sellado son del split `training`), con sus archivos originales sin modificar. Los resultados salen de las mismas funciones que usa la página y están en [`docs/ep3/prueba_segmentos_nuevos.json`](docs/ep3/prueba_segmentos_nuevos.json), junto con el sha256 de cada archivo de entrada.

{tabla(filas, ['Segmento', 'ID en la página', 'Cajas puntuadas', 'Celdas marcadas', 'Detalle de la celda marcada'])}

- Es una **prueba de funcionamiento**, no una validación estadística. Con {len(d['segmentos'])} segmentos no se estima la frecuencia de los huecos.
- {n_marc} de {len(d['segmentos'])} segmentos nuevos trae un **posible hueco** de cámara, del mismo tipo que los dos casos de desarrollo ({dev}). Con estos archivos no se distingue si es un problema de etiquetado o de los datos de esa cámara.
- Los parámetros del detector son los congelados en v3 ([`detector_params_v3.json`](artefactos_ep3/detector_params_v3.json)); no se reajustaron. La validación externa sellada ([`plan_seleccion_ep3.json`](artefactos_ep3/plan_seleccion_ep3.json)) sigue sin ejecutarse; es independiente de esta prueba.

**Cómo se hace en vivo.** En «Puntuar datos nuevos» se cargan los dos archivos del segmento (el 1, `lidar_box`, y el 2, `camera_to_lidar_box_association`, en cualquier orden) y se pulsa **«Puntuar segmento»**. Sin el archivo 2 se puntúa igual, pero el paso «Revisar celdas marcadas» sale «omitido» y no se buscan huecos. Los archivos viven en `datos_demo/`, que no se versiona ni va en la imagen."""


def recuadro_cifras() -> str:
    from sklearn.metrics import roc_auc_score
    import pandas as pd

    cajas = pd.read_parquet(RAIZ / "data/09_app_ep3/cajas_oof.parquet", columns=["grupo", "sin_camara", "score"])
    auc = {g: roc_auc_score(x["sin_camara"], x["score"]) for g, x in (("train", cajas[cajas["grupo"] == "train"]), ("test", cajas[cajas["grupo"] == "test"]), ("todo", cajas))}
    c9 = pd.read_csv(RAIZ / "data/08_reporting/09_comparacion_modelos.csv").set_index("modelo")
    r10 = pd.read_csv(RAIZ / "data/08_reporting/10_resultado_principal.csv").set_index("metodo")
    primero = lambda s: str(s).split()[0]                                                                 # noqa: E731  ("0.862 (0.814 a 0.906)" -> "0.862")
    ep2_regla, ep2_lr, ep2_test = float(primero(c9.loc["Regla: menos puntos top", "AUC"])), float(primero(c9.loc["Regresion logistica", "AUC"])), float(primero(r10.loc["Regla: menos puntos top", "AUC"]))
    d = csv("f3_defecto_vs_optimizado.csv").set_index("modelo")
    hip = jsn(RAIZ / "data/06_models/hiperparametros_B.json")["final"]["LR"]["cfg"]["C"]
    filas = [("EP2: 33 segmentos de entrenamiento (test de 8 aparte)", "secciones [8](#8-modelos-supervisados) y [10](#10-evaluación-final-en-el-test)",
              f"regla {c(ep2_regla)} y regresión logística ajustada ({c(ep2_lr)}) en entrenamiento; regla {c(ep2_test)} en el test"),
             ("EP3: 41 segmentos de desarrollo (los 33 más los 8 del test de EP2)", f"secciones [8.1](#{ancla_81()}) a 8.3 y 12.1", f"regla {c(auc['todo'])}; regresión logística por defecto {c(d.loc['LR', 'AUC_def'])} y optimizada {c(d.loc['LR', 'AUC_opt'])}")]
    return (f"> **Por qué las cifras de esta sección no son las de la sección 8.** EP2 evaluó los 33 segmentos de entrenamiento, con folds estratificados por `tiene_camara`, y su regresión logística quedó ajustada (`C` = {c(hip, 3)}). "
            f"EP3 evalúa los 41 segmentos de desarrollo con `StratifiedGroupKFold` de 5 estratificado por `sin_camara`, y compara la regresión logística por defecto con la optimizada por una búsqueda anidada nueva. "
            f"Lo que más mueve a la regla (de {c(ep2_regla)} a {c(auc['todo'])}) es la población, no el método: la misma regla da {c(auc['train'])} fuera de fold sobre los 33 segmentos de entrenamiento y {c(auc['test'])} sobre los 8 de test, "
            f"que incluyen el segmento con la cámara 3 sin pares. Las dos series no son comparables una a una.\n\n" + tabla(filas, ["Serie", "Dónde está", "Cifras (AUC fuera de fold)"]))


def actualizacion_alcance() -> str:
    return ("> **Actualización de EP3 sobre el alcance.** El «alcance» de arriba es el de EP2. En EP3 el paso 1 (detector de huecos) se midió con los 41 segmentos de desarrollo y se probó en la aplicación con 4 segmentos nuevos reales: "
            "1 de 4 trae un posible hueco (sección [16](#16-lente-la-aplicación-y-su-despliegue)). Esa prueba de funcionamiento no valida el paso 1 estadísticamente; la validación externa sellada sigue sin ejecutarse.")


DIRS_RAIZ = {".streamlit/": "configuración y tema de la página", "app/": "la aplicación Lente (Streamlit)", "artefactos_ep3/": "tablas agregadas, manifests y planes de EP3 (versionables)",
             "conf/": "catálogo y parámetros de Kedro", "data/": "(fuera de git) 01_raw a 09_app_ep3: datos, modelos y tablas; 06_models hace de models/ (EP2 congelado, EP3 en 06_models_ep3)",
             "datos_demo/": "(fuera de git) segmentos nuevos reales para la demostración en vivo", "docs/": "informes, planes y guías; ep3/ (informe técnico, plan v3, estado) y seleccion_segmentos/",
             "images/": "figuras con el número del notebook que las genera; app/ (capturas del README) y ep3/", "notebooks/": "notebooks 00 a 15 (tabla siguiente)",
             "scripts/": "scripts de EP2 (informe, README, mediciones) y ep3/ (datos, detector, ajuste, página, demostración, README)", "src/": "paquete waymo_evaluacion (pipelines de Kedro y ep3/)",
             "tests/": "pruebas de EP1, EP2 y del README; ep3/ (página, detector, selección) y pipelines/"}
GRUPOS_ARCHIVOS = [(["Dockerfile", "docker-compose.yml", ".dockerignore", "requirements.txt", "requirements_app.txt", "requirements_ep3.txt", "constraints_ep3.txt", "pyproject.toml", ".gitignore"], "imagen de la aplicación, entornos (EP2, aplicación, EP3, versiones fijadas) y reglas de git"),
                   (["README.md", "CLAUDE.md", "entrega_EP2.zip", "entrega_EP3.zip", "entrega_EP3.sha256"], "este archivo (lo genera scripts/generar_readme.py), instrucciones del asistente y (fuera de git) los paquetes entregados")]


def arbol_repo() -> str:
    """Árbol de la raíz generado del sistema de archivos: si aparece una carpeta o un archivo sin descripción, el generador falla en vez de omitirlo."""
    ocultos = {".git", ".venv", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".viz", ".mypy_cache", "node_modules"}
    reales = [p for p in RAIZ.iterdir() if p.name not in ocultos and not p.name.startswith(".coverage") and p.name != "info.log"]      # restos de ejecutar pytest (cobertura y registro de Kedro), no del proyecto
    claves = {p.name + ("/" if p.is_dir() else "") for p in reales}
    agrupados = {a for g, _ in GRUPOS_ARCHIVOS for a in g}
    sin_desc = sorted(claves - set(DIRS_RAIZ) - agrupados)
    if sin_desc:
        sys.exit(f"ERROR (readme_f38): sin descripción en el árbol de la sección 14: {sin_desc}")
    lineas = ["```", "waymo-evaluacion/"]
    for d in sorted(k for k in DIRS_RAIZ if k in claves):
        lineas.append(f"├── {d:<14} {DIRS_RAIZ[d]}")
    for g, desc in GRUPOS_ARCHIVOS:
        presentes = [a for a in g if a in claves]
        if presentes:
            lineas.append(f"├── {', '.join(presentes)}: {desc}")
    lineas.append("```")
    return "\n".join(lineas)


NOTEBOOKS = {
    "00_exploracion_bucket_waymo": ("EP1", "explora el bucket de Waymo v2 con gsutil desde Colab y elige segmentos", "Colab; sin salidas guardadas (no se ejecuta aquí)"),
    "00b_seleccion_segmentos_ep2": ("EP2", "mide y selecciona los segmentos de EP2 (ampliación de 4 a 41)", "salidas guardadas (Colab)"),
    "00b_seleccion_segmentos_ep3": ("EP3", "selección sellada de los segmentos nuevos de la validación externa", "Colab; sin salidas guardadas: la validación externa no se ha ejecutado"),
    "01_exploracion_csv": ("EP1", "exploración y calidad del CSV sintético del docente", "salidas guardadas"),
    "02_exploracion_waymo": ("EP1", "exploración de datos reales de Waymo v2", "salidas guardadas"),
    "03_fuentes_y_colaboracion": ("EP1", "fuentes de datos, licencias y acuerdo de trabajo del equipo (IE1)", "salidas guardadas"),
    "04_estructuras_y_almacenamiento": ("EP1", "listas frente a NumPy, tipos de columna y CSV frente a Parquet (IE2)", "salidas guardadas"),
    "05_etica_sesgos_privacidad": ("EP1", "ética, sesgos y privacidad de las fuentes (IE4)", "salidas guardadas"),
    "06_eda_y_preparacion_modelamiento": ("EP1 a EP2", "EDA ampliado con los 41 segmentos; prepara EP2", "salidas guardadas"),
    "07_decision_target_ep2": ("EP2", "por qué EP2 usa `sin_camara` como target", "salidas guardadas"),
    "08_analisis_observabilidad_sin_camara": ("EP2", "variables, geometría de cámaras y aprendizaje no supervisado de EP2", "salidas guardadas"),
    "09_modelos_supervisados_sin_camara": ("EP2", "baselines y modelos con búsqueda anidada por segmento", "reentrenado en copia limpia: un umbral del Random Forest cambió en el último decimal (sección 14)"),
    "09b_enmiendas_plan_test_v2": ("EP2", "enmiendas al plan de evaluación del test (v2)", "salidas guardadas"),
    "10_evaluacion_final_sin_camara": ("EP2", "evaluación final en el test congelado y hallazgo post hoc", "verificado: reproducido en copia limpia con 15 CSV idénticos por sha256 (sección 14)"),
    "11_ep3_datos_y_deteccion": ("EP3", "datos de desarrollo (41 segmentos) y detector de huecos", "ejecutado con nbconvert (DEC-70 de `docs/ep3/ESTADO.md`)"),
    "12_ep3_tuning_y_ensambles": ("EP3", "hiperparámetros y ensambles (IE9 e IE10)", "ejecutado con nbconvert (DEC-70)"),
    "13_ep3_generalizacion_y_seleccion": ("EP3", "generalización y selección (IE11 e IE12)", "ejecutado con nbconvert (DEC-70)"),
    "14_ep3_dos_pasos_y_app": ("EP3", "solución en dos pasos y la aplicación", "ejecutado con nbconvert (DEC-70); no se puede volver a ejecutar en una copia (lee un lidar_box crudo)"),
    "15_ep3_no_supervisado": ("EP3", "aprendizaje no supervisado (descriptivo, post hoc)", "ejecutado con nbconvert (DEC-70)"),
}
ORDEN_NB = ["00_exploracion_bucket_waymo", "01_exploracion_csv", "02_exploracion_waymo", "03_fuentes_y_colaboracion", "04_estructuras_y_almacenamiento", "05_etica_sesgos_privacidad", "00b_seleccion_segmentos_ep2",
            "06_eda_y_preparacion_modelamiento", "07_decision_target_ep2", "08_analisis_observabilidad_sin_camara", "09_modelos_supervisados_sin_camara", "09b_enmiendas_plan_test_v2", "10_evaluacion_final_sin_camara",
            "11_ep3_datos_y_deteccion", "12_ep3_tuning_y_ensambles", "13_ep3_generalizacion_y_seleccion", "14_ep3_dos_pasos_y_app", "15_ep3_no_supervisado", "00b_seleccion_segmentos_ep3"]


def tabla_notebooks(puente_06: str) -> str:
    """Tabla de notebooks generada de los archivos reales de ``notebooks/`` (número, etapa, propósito, orden y qué consta sobre su ejecución)."""
    reales = sorted(p.stem for p in (RAIZ / "notebooks").glob("*.ipynb"))
    if set(reales) != set(NOTEBOOKS) or set(ORDEN_NB) != set(NOTEBOOKS):
        sys.exit(f"ERROR (readme_f38): los notebooks de notebooks/ no coinciden con la tabla: sobran {sorted(set(reales) - set(NOTEBOOKS))}, faltan {sorted(set(NOTEBOOKS) - set(reales))}")
    filas = []
    for stem in ORDEN_NB:
        d = jsn(RAIZ / "notebooks" / f"{stem}.ipynb")
        cod = [x for x in d["cells"] if x["cell_type"] == "code"]
        con = sum(1 for x in cod if x.get("outputs"))
        etapa, prop, ver = NOTEBOOKS[stem]
        if ver == "salidas guardadas":
            ver = f"salidas guardadas ({con} de {len(cod)} celdas); sin registro de re-ejecución"
        elif ver == "salidas guardadas (Colab)":
            ver = f"salidas guardadas ({con} de {len(cod)} celdas, Colab)"
        filas.append((ORDEN_NB.index(stem) + 1, f"[`{stem}.ipynb`](notebooks/{stem}.ipynb)", etapa, prop, ver))
    return (f"**Notebooks.** 00 a 05 (EP1), 06 ({puente_06}), 07 a 10 (EP2) y 11 a 15 (EP3), más dos «00b» de selección de segmentos que se corren en Colab. La columna «Orden» es el orden recomendado; para reproducir el resultado oficial de EP2 basta el 10 "
            f"(sección 14) y para EP3 los notebooks 11 a 15 leen lo que dejan `scripts/ep3/`.\n\n" + tabla(filas, ["Orden", "Notebook", "Etapa", "Qué hace", "Ejecución (según los archivos y los registros)"]))


def nota_kpi(slug) -> str:
    return (f"> **Cómo leer estos KPI en EP3.** Las metas de esta tabla son las de EP2, que evaluó 33 segmentos de entrenamiento. Las cifras de EP3 (41 segmentos, otra validación) están en la sección [8.1](#{ancla_81()}) "
            "y en las secciones 8.3 y 12; no son comparables una a una con las de la sección 8 (ver el recuadro de 8.1).")
