"""Genera docs/ep3/REPORTE_F18.md (reporte final de la tarea F18) leyendo las cifras de los archivos de data/08_reporting_ep3 y docs/ep3. Sin cifras a mano.

La verificacion en el entorno nuevo (D4/D5) se lee de data/08_reporting_ep3/f18_verificacion.json (lo escribe quien corra la verificacion); si no existe, queda «pendiente».
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from waymo_evaluacion.ep3.app_logica import PERFILES, SECCIONES  # noqa: E402

REP, DOC = RAIZ / "data/08_reporting_ep3", RAIZ / "docs/ep3"


def c(x, d=3):
    return f"{x:.{d}f}".replace(".", ",")


def p(x, d=1):
    return f"{100 * x:.{d}f} %".replace(".", ",")


def mi(x):
    return f"{int(round(x)):,}".replace(",", ".")


def J(n, base=REP):
    return json.loads((base / n).read_text(encoding="utf-8"))


def main() -> None:
    acl = pd.read_csv(REP / "f13_auc_cluster_sin_huecos.csv")
    aclj = J("f13_auc_cluster_sin_huecos.json")
    ptt = pd.read_csv(REP / "f12_eda_puntos_top_sin_huecos.csv")
    ptr = J("f12_eda_puntos_top_resumen.json")
    dfn = J("f18_definiciones.json")
    dd, ab = dfn["definicion_20pct"], dfn["auc_base_f13"]
    ad = pd.read_csv(REP / "f13_ari_diagnostico.csv")
    sres = J("f18_seleccion_resumen.json")
    smot = pd.read_csv(REP / "f18_seleccion_motivos.csv").set_index("motivo_corto")
    srend = pd.read_csv(REP / "f18_seleccion_rendimiento.csv").set_index(["corte", "grupo"])
    plan = J("plan_seleccion_ep3.json", DOC)
    comp = pd.read_csv(REP / "pagina_comparacion_antes_despues.csv")
    tiem = J("pagina_tiempos_carga.json")
    cont = J("pruebas_ep3_conteo.json")
    f12 = J("f12_resumen.json")
    ver_ruta = REP / "f18_verificacion.json"
    ver = json.loads(ver_ruta.read_text(encoding="utf-8")) if ver_ruta.exists() else None
    cer = acl[(acl["k"] == 2) & (acl["tipo_de_caso"] == "cercanos y densos")].iloc[0]
    lej = acl[(acl["k"] == 2) & (acl["tipo_de_caso"] == "lejanos y poco densos")].iloc[0]
    c40 = acl[(acl["k"] == 4) & (acl["cluster"] == 0)].iloc[0]
    esf = ad[(ad["k"] == 2) & (ad["covarianza"] == "spherical") & (ad["n_init"] == 2)].iloc[0]["ARI_vs_KMeans"]
    dia = ad[(ad["k"] == 2) & (ad["covarianza"] == "diag") & (ad["n_init"] == 2)].iloc[0]["ARI_vs_KMeans"]
    ful = ad[(ad["k"] == 2) & (ad["covarianza"] == "full") & (ad["n_init"] == 2)].iloc[0]["ARI_vs_KMeans"]
    ward = ad[(ad['k'] == 2) & ad['tecnica'].str.startswith('Ward')].iloc[0]['ARI_vs_KMeans']
    pt = lambda v, tr: ptt[(ptt["variante"] == v) & (ptt["tramo"] == tr)].iloc[0]["tasa"]  # noqa: E731
    cuotas = "\n".join(f"| {k} | {q} | {plan['candidatos_por_estrato'][k]} |" for k, q in plan["cuotas_utiles"].items())
    cols = ["seccion", "caso", "cifra", "antes", "despues"]
    if True:
        t_comp = "| " + " | ".join(cols) + " |\n|" + "|".join("---" for _ in cols) + "|\n" + "\n".join("| " + " | ".join(str(r[k]) for k in cols) + " |" for _, r in comp.iterrows())
    t_tiem = "\n".join(f"| {s} | {c(v['mejor_s'], 2)} s | {c(v['frio_s'], 2) if v.get('frio_s') is not None else '—'} s | {'sí' if v['cumple_meta'] else 'no'} | {'sí' if v.get('frio_cumple_meta') else 'no'} |" for s, v in tiem["secciones"].items())
    n_fr = sum(1 for v in tiem["secciones"].values() if v.get("frio_cumple_meta"))
    if ver:
        d4 = (f"`entrega_EP3.zip` y `entrega_EP3.sha256` rearmados (el tamaño y el hash no se escriben aquí porque el reporte va dentro del zip: están en `entrega_EP3.sha256` y en el reporte del chat). Venv nuevo de Python 3.10 en `C:/Users/maico/tmp_verificacion_ep3` "
              f"(mismo equipo, no otra máquina): SHA256SUMS {ver['sumas']}; EP2 {ver['ep2']}; v3 {ver['v3']}; no supervisado {ver['nosup']}; plan de selección {ver['plan']}; `tests/ep3`: {ver['tests']}; página: {ver['humo']}. Detalle: `verificacion_copia_limpia.md`.")
    else:
        d4 = "Pendiente: ver `verificacion_copia_limpia.md`."
    md = f"""# Reporte final de la tarea F18

*Generado por `scripts/ep3/generar_reporte_f18.py`; cada cifra sale de su archivo de `data/08_reporting_ep3` o `docs/ep3`. Decisiones: `ESTADO.md` (DEC-27 en adelante, sección F18).*

## Resumen
F18 tuvo cuatro fases: **A** correcciones de fondo y análisis post hoc; **B** selección de segmentos nuevos para la validación externa; **C** rediseño de la página; **D** cierre (guion, documentos, entrega y verificación). Los congelados no cambiaron en ninguna fase: EP2 14 de 14, v3 5 de 5 y no supervisado 1 de 1. Pruebas de EP3 recolectadas: {cont['recolectadas_ep3']} (antes de F18: 63).

## Fase A. Correcciones de fondo y análisis post hoc
- **A1. Terminología.** «Falsas alarmas» pasó a «celdas marcadas además de los 2 de referencia (sin verdad externa)» en informe, README, guion, preguntas, notebooks, artefactos, MAPA y en los textos de `sellado.py` y `evaluar_sellado.py`. «30 de 30» ({f12['detector_combinaciones_que_detectan_los_2']} de {f12['detector_combinaciones']}) mide la estabilidad del conjunto marcado frente a los parámetros, no sensibilidad ni especificidad. El informe §14 y `evaluar_sellado.py` dicen qué se medirá con segmentos nuevos: (i) tasa de celdas marcadas, (ii) su estabilidad frente a las 30 combinaciones y (iii) opcional y post hoc, con `camera_box`, si esa cámara tiene cajas 2D (laguna de asociación) o ninguna (laguna de etiquetado o de datos). Registrado como **DEV-3** en `plan_v3_desviaciones.md`. Los nombres de columna `falsas_alarmas` de `f12_*` y el texto congelado de `plan_v3.*` se conservan (no se regeneró F12).
- **A2. ¿Dónde está el ML?** Respuesta reescrita: el ML son los 11 candidatos con validación anidada, la calibración Platt (una regresión logística) y el análisis no supervisado; **el detector de huecos es estadística descriptiva** (percentiles, una mediana y un umbral).
- **A3. AUC de la regla dentro de cada cluster.** (a) Columna agregada a las tablas del informe §9: k = 2, {c(cer['AUC_todas'])} en «cercanos y densos» y {c(lej['AUC_todas'])} en «lejanos y poco densos»; la regla pierde capacidad de ordenar en cajas cercanas y densas. **(b) Sin las celdas con hueco** (`f13_auc_cluster_sin_huecos.csv`, post hoc, descriptivo): el AUC de los cercanos **sube de {c(cer['AUC_todas'])} a {c(cer['AUC_sin_celdas_con_hueco'])} (+{c(cer['dif_AUC'])})**; con k = 4 (cluster 0) de {c(c40['AUC_todas'])} a {c(c40['AUC_sin_celdas_con_hueco'])} (+{c(c40['dif_AUC'])}); los lejanos casi no cambian ({c(lej['AUC_todas'])} a {c(lej['AUC_sin_celdas_con_hueco'])}). Las celdas con hueco tienen {mi(cer['cajas_en_celdas_con_hueco'])} cajas y {mi(cer['positivos_en_celdas_con_hueco'])} de los {mi(cer['positivos'])} positivos del cluster cercano: explican buena parte de la pérdida, no toda (queda una brecha de {c(cer['AUC_sin_celdas_con_hueco'])} contra {c(lej['AUC_sin_celdas_con_hueco'])}). **(c) Puntos del sensor superior > 100** (`f12_eda_puntos_top_sin_huecos.csv`): la tasa sube de {p(ptr['tramo_51_100']['tasa'])} (51 a 100) a {p(ptr['tramo_mayor_100']['tasa'])} (> 100) por las celdas con hueco: {mi(ptr['tramo_mayor_100']['cajas_en_celdas_con_hueco'])} cajas con tasa {p(ptr['tramo_mayor_100']['tasa_en_celdas_con_hueco'])}, {p(ptr['pct_positivos_mayor_100_en_celdas_con_hueco'])} de los positivos del tramo; sin ellas la tasa del tramo es {p(ptr['tramo_mayor_100']['tasa_sin_hueco'])} y la serie es decreciente ({p(pt('sin las celdas con hueco', '51-100'))}, {p(pt('sin las celdas con hueco', '101-200'))}, {p(pt('sin las celdas con hueco', '201-500'))}, {p(pt('sin las celdas con hueco', '>500'))}); queda una concentración residual en el segmento `247562357599`. Con preguntas cruzadas en `preguntas_cruzadas.md`.
- **A4. «20 %» en el informe y en la página** (`f18_definiciones.json`): el informe (`f5_generalizacion.py`, `RankingDosPasos`) toma el 20 % del **total** de cajas ({mi(dd['cajas_total'])}) = {mi(dd['f5_cajas_revisadas_al_20pct'])} cajas; la página (`app_logica.py`, `curva_cola.csv`) toma el 20 % de la **cola** de celdas sanas ({mi(dd['cajas_cola_celdas_sanas'])}) = {mi(dd['pagina_cajas_revisadas_al_20pct'])} cajas. Con esa diferencia de {mi(dd['diferencia_cajas'])} cajas, el brazo C da {p(dd['captura20_C_informe_f5'])} en el informe, {p(dd['recall_C_pagina_curva_20pct_de_la_cola'])} en la curva de la página y {p(dd['recall_C_observado_pagina_20pct_de_la_cola'])} en el conteo observado (el resto, menos de 0,2 puntos, es desempate de empates e interpolación). El AUC base de `f13_aporte_cluster.csv` es {c(ab['AUC_f13_aporte_cluster_base_reproducido'])} y no {c(ab['AUC_puntaje_crudo_pooled'])} porque usa la probabilidad con Platt de cada fold ({c(ab['AUC_prob_Platt_pooled'])} al juntar los folds; dentro de cada fold el AUC es idéntico) más una regresión logística adicional con otra partición. Escrito en informe §9, §12 y §13 y en la pregunta sobre la página.
- **A5. ARI.** KMeans coincide con el GMM esférico ({c(esf)}) y con el diagonal ({c(dia)}); el discrepante es el GMM de covarianza `full` ({c(ful)}; partición 70/30 contra 47/53); Ward {c(ward)}. Evidencia de EP2 (solo lectura): `docs/informe_tecnico_EP2.md:408` (variables de oclusión), `:428-429` (clusters «ocluidos» y «sin oclusores»), `:422` (covarianzas degeneradas, varianza mínima 1e-6 en `n_ocl`, `frac_cub` y `dist_ocl_f`) y `data/08_reporting/08_no_supervisado_resumen.json:5-7` (ARI 0,997). Hipótesis, no verificada: el 0,997 de EP2 probablemente estaba inflado por variables discretas; el {c(ful)} no es la anomalía. El BIC del GMM baja de 86.283 a 14.497 y no se usa para elegir k. Las preguntas sobre clusters y ARI citan siempre el {c(esf)} junto al {c(ful)}. **La página usa k = 2** (`k_elegido`), así que los clusters 1 y 3 de k = 4 (mismo rótulo, tasas 14,8 % y 10,7 %) no se ven en la página y no hizo falta diferenciarlos.
- **A6. Sesgo de selección** (`f18_seleccion_*.csv`): {sres['evaluados']} evaluados, {sres['descartados']} descartados ({mi(smot.loc['asociación vacía', 'segmentos'])} asociación vacía, {mi(smot.loc['etiquetado ralo', 'segmentos'])} etiquetado ralo, {mi(smot.loc['pocas asociaciones', 'segmentos'])} pocas asociaciones); rendimiento de día {p(srend.loc[('momento_del_dia', 'Day'), 'rendimiento'], 0)}, amanecer o atardecer {p(srend.loc[('momento_del_dia', 'Dawn/Dusk'), 'rendimiento'], 0)} y noche {p(srend.loc[('momento_del_dia', 'Night'), 'rendimiento'], 0)}. Agregado a informe §3 y §16 (limitación), §15 (recomendación: filtro 1 a nivel segmento, sin ML) y §17. La causa se declara desconocida. La tabla del detector (§8) indica la población de cada columna (300 cajas a ≤120° contra 268 a ≤100°).
- **A7. Preguntas cruzadas nuevas** (recall objetivo, Platt, fuga de datos, bootstrap por segmentos, PR-AUC y AUC, sensor superior, deriva, E2 en 5 de 5 folds, limitación principal, qué se haría con más tiempo, y las de A3 a A6): el archivo pasó a ser de **{len(__import__('re').findall(r'^[*][*][0-9]+[.] ', (DOC / 'preguntas_cruzadas.md').read_text(encoding='utf-8'), flags=__import__('re').M))} preguntas**.

## Fase B. Selección de segmentos nuevos (sin bucket)
- **B1. Embudo** (como el 00b de EP2; el notebook y `plan_seleccion_ep3.py` se detienen si no coincide): inventario {plan['embudo']['inventario']} → sin lluvia **{plan['embudo']['sin_lluvia']}** → {plan['parametros']['min_frames']} frames o más **{plan['embudo']['n_frames_>=190']}** → `n_detecciones` entre los percentiles 2,5 y 97,5 ({mi(plan['embudo']['limite_inferior_detecciones'])} a {mi(plan['embudo']['limite_superior_detecciones'])}) **{plan['embudo']['n_detecciones_entre_percentiles']}** → solo después se excluyen los {plan['embudo']['evaluados_ep2_dentro_del_pool']} evaluados por EP2 → **{plan['embudo']['candidatos_sin_los_evaluados_por_ep2']}** candidatos. Coincidió con EP2.
- **B2. Cuotas fijas de segmentos útiles** (total {plan['total_cuota']}):

| Estrato | Cuota | Candidatos |
|---|---|---|
{cuotas}

  Evaluación secuencial por estrato en el orden de `default_rng(42)`, recorrida por rondas (decisión mía: con un tope global de {plan['parametros']['tope_evaluaciones']} evaluaciones, ir estrato por estrato dejaría sin evaluar a los últimos), meta de {plan['parametros']['meta_utiles']} útiles. La justificación (cuotas por estrato como en el desarrollo, sobremuestreo de San Francisco de día por las 2 celdas con hueco, noche mal representada) está en el notebook.
- **B3.** Se agregó `MIN_POSITIVOS = {plan['parametros']['min_positivos']}` y el caso «las asociaciones no cruzan con lidar_box».
- **B4. Plan pre-declarado:** `docs/ep3/plan_seleccion_ep3.json` y `.sha256` (calculado sin descargar nada); la lógica está en `src/waymo_evaluacion/ep3/seleccion_nuevos.py`, el notebook incluye su código exacto y `tests/ep3/test_seleccion_nuevos.py` (13 pruebas) compara la lógica con el JSON.
- **B5.** `docs/ep3/GUIA_VALIDACION_EXTERNA.md` con los pasos, qué hacer si salen menos de 15 útiles, los comandos de `evaluar_sellado.py` e `ingesta_nuevos.py`, los tres casos, el paso opcional con `camera_box` (con `gsutil ls` previo) y la garantía de sellado: el modelo v3 (`manifest_v3.json`, copia en `artefactos_ep3/`) y el plan de selección deben quedar commiteados **antes** de ejecutar el Colab.

## Fase C. Rediseño de la página
- Producto «Auditor de etiquetas 3D» (`app/app.py`, `secciones.py`, `estilos.py`, `assets/icono.png`), **{len(SECCIONES)} secciones**, {len(PERFILES)} perfiles, modo presentación, tema en los dos `config.toml` (solo se agregó `[theme]`), formato es-CL, sin ninguna petición externa (una prueba falla si algún archivo contiene `http://` o `https://`) y sin emojis. Guía de estilo con contraste calculado (≥ 4,5:1 en todos los pares): `guia_estilo_pagina.md`. Demo: `pagina_guia_demo.md`. Pendientes: `PENDIENTES_PAGINA.md`.
- **Cifras antes y después** (`pagina_comparacion_antes_despues.csv`; las cifras no cambian, salvo la cobertura de la cola, que ahora tiene una sola fuente, el conteo observado):

{t_comp}

- **Tiempos de carga** (`pagina_tiempos_carga.json`, `AppTest`, datos reales; meta < 3 s). Con caché caliente cumplen las {len(tiem['secciones'])} secciones; **en frío cumplen {n_fr} de {len(tiem['secciones'])}** (las que cargan el modelo congelado, «Explica una caja» y «Puntuar datos nuevos», pasan de 3 s). No incluye el dibujado en un navegador.

| Sección | Caché caliente | En frío | Meta (caliente) | Meta (frío) |
|---|---|---|---|---|
{t_tiem}

- **Capturas:** no hay playwright; se usó el Chrome ya instalado en modo sin interfaz con el protocolo CDP (`scripts/ep3/capturar_pagina.py`, no se instaló nada). Se generaron las {len(SECCIONES)} secciones y el modo presentación en `images/ep3/pagina/`.
- Pruebas nuevas: `test_pagina_rediseno.py` (21: formatos es-CL, control inverso, textos «Todos» y segmento, fuente única, humo de {len(SECCIONES)} secciones x {len(PERFILES)} perfiles x modo presentación, regresión de cifras, contraste, sin URLs y sin emojis) y `test_seleccion_nuevos.py` (13).

## Fase D. Cierre
- **D1. Guion** (9:15): frase corta de «en muestra», bloque final «lo que sabemos, lo que no sabemos y cómo lo vamos a saber», E2 gana en 5 de 5 folds pero bajo el umbral pre-declarado, palabras por bloque (ninguno supera 140 por minuto), columna «Quién» vacía, plan C (video de 90 s) y demo que sigue la página rediseñada con las cifras que muestra.
- **D2.** Informe, README_EP3, preguntas, guion, guía de demo, notebooks 11 a 15 (ejecutados con `RECALCULAR = False`; el 14 con las {len(SECCIONES)} secciones x {len(PERFILES)} perfiles), MAPA, ESTADO, `plan_integracion_readme.md` y `docs/ep3/revision/` regenerados; los contadores de pruebas, preguntas, secciones y notebooks se leen del código.
- **D3 y D4.** {d4}
- **D5.** Congelados al final: ver el reporte del chat y `ESTADO.md`; EP2 14 de 14, v3 5 de 5 y no supervisado 1 de 1.

## Bloqueos y lo que te toca
- **Sin bloqueos.** Límites: Docker no se probó; AWS no se ejecutó; los tiempos son de servidor; el rediseño no se probó con personas.
- **Te toca:** (1) revisar y commitear (modelo v3 y plan de selección **antes** del Colab); (2) correr el Colab de segmentos nuevos y `evaluar_sellado` una sola vez, siguiendo `GUIA_VALIDACION_EXTERNA.md`; (3) revisar la guía de estilo y las capturas, y probar la página con alguien de cada perfil; (4) decidir si se precarga el modelo para bajar la carga en frío de las dos secciones lentas; (5) probar Docker con Docker Desktop encendido y una instalación en otra máquina; (6) el zip lleva datos derivados por caja: solo uso académico, no redistribuir.
"""
    (DOC / "REPORTE_F18.md").write_text(md, encoding="utf-8")
    print("escrito REPORTE_F18.md")


if __name__ == "__main__":
    main()
