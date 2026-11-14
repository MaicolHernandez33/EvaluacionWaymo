# artefactos_ep3: lo versionable de EP3

Carpeta fuera de `data/` (que git ignora) con lo liviano y **agregado** de EP3: manifests con sha256, umbrales, parámetros del detector, el plan v3 congelado y las tablas de resultados por candidato, fold, cluster o segmento. **No hay tablas por caja ni identificadores de objeto.** Se regenera con `scripts/ep3/empaquetar_entrega_ep3.py`.

## Qué es cada archivo
- `manifest_v3.json`: sha256 de `modelo_final_v3.joblib`, `umbrales_v3.json` y `detector_params_v3.json` (la solución congelada v3: regla «menos puntos top», umbrales A y B, detector de huecos). `manifest_no_supervisado.json`: sha256 del scaler y KMeans descriptivos (post hoc).
- `umbrales_v3.json`, `detector_params_v3.json`: copia legible de esos parámetros (el verificador mira los de `data/06_models_ep3`, no estas copias).
- `plan_v3.md`, `plan_v3.json`, `plan_v3.sha256`: el plan congelado antes de experimentar (no se editan). `plan_v3_desviaciones.md`: DEV-1 y DEV-2.
- `lista_A_huecos.csv`: las 2 celdas (segmento x cámara) con hueco.
- `f1_` a `f6_`, `f12_`, `f12b_`, `f13_`: tablas y resúmenes de cada fase (F1 datos, F2 detector, F3 IE9, F4 IE10, F5 IE11, F6 IE12, F12 análisis en muestra, F13 no supervisado).

## Cómo verificarlo
1. Con el repositorio completo y `data/`: `python scripts/ep3/verificar_congelados_v3.py` y `python scripts/ep3/verificar_no_supervisado.py`.
2. Solo con esta carpeta: comparar el sha256 de cada archivo con la columna de abajo (por ejemplo `certutil -hashfile manifest_v3.json SHA256`), y el de los 3 archivos de la solución con `manifest_v3.json`.

## Qué falta para correr la página
Esta carpeta no alcanza: la página necesita `data/09_app_ep3/` (predicciones por caja fuera de fold) y `data/06_models_ep3/` (modelo y artefacto no supervisado). Van en `entrega_EP3.zip` (solo uso académico del docente, no redistribuir) o se regeneran con `scripts/ep3/f7_preparar_app.py`.

## Archivos
| Archivo | Origen | Bytes | sha256 (16 primeros) |
|---|---|---|---|
| `detector_params_v3.json` | `data/06_models_ep3/detector_params_v3.json` | 570 | `cf6f2980ba0afaff...` |
| `f12_auc_por_fold_brazos.csv` | `data/08_reporting_ep3/f12_auc_por_fold_brazos.csv` | 4.069 | `30b48161e2d5a5eb...` |
| `f12_diferencia_C_menos_A.csv` | `data/08_reporting_ep3/f12_diferencia_C_menos_A.csv` | 2.810 | `52ec49a4e4f1393c...` |
| `f12_eda_calidad.csv` | `data/08_reporting_ep3/f12_eda_calidad.csv` | 2.039 | `1893b639ff9fd26a...` |
| `f12_eda_calidad_resumen.json` | `data/08_reporting_ep3/f12_eda_calidad_resumen.json` | 403 | `12613cffc0b62f60...` |
| `f12_eda_tasas.csv` | `data/08_reporting_ep3/f12_eda_tasas.csv` | 1.830 | `9f50b65d0bf1c77b...` |
| `f12_equidad.csv` | `data/08_reporting_ep3/f12_equidad.csv` | 2.356 | `9a47b691d1b25bd3...` |
| `f12_resumen.json` | `data/08_reporting_ep3/f12_resumen.json` | 1.592 | `a8403bdc5bcf1ffe...` |
| `f12_sensibilidad_detector.csv` | `data/08_reporting_ep3/f12_sensibilidad_detector.csv` | 3.968 | `dd79e9dd130afe17...` |
| `f12b_hechos_brazoC.json` | `data/08_reporting_ep3/f12b_hechos_brazoC.json` | 836 | `2319f982c97912be...` |
| `f13_aporte_cluster.csv` | `data/08_reporting_ep3/f13_aporte_cluster.csv` | 704 | `e8677b5f27ca3fc0...` |
| `f13_ari_diagnostico.csv` | `data/08_reporting_ep3/f13_ari_diagnostico.csv` | 1.633 | `e09882c62df5e5df...` |
| `f13_ari_diagnostico.json` | `data/08_reporting_ep3/f13_ari_diagnostico.json` | 687 | `31d863b1fa7b7d98...` |
| `f13_clusters_k2.csv` | `data/08_reporting_ep3/f13_clusters_k2.csv` | 836 | `661b5e5d4671c833...` |
| `f13_clusters_k4.csv` | `data/08_reporting_ep3/f13_clusters_k4.csv` | 1.397 | `22655c2c64ef7564...` |
| `f13_comparacion_ep2_ep3.csv` | `data/08_reporting_ep3/f13_comparacion_ep2_ep3.csv` | 1.325 | `557058479c7f440e...` |
| `f13_estabilidad.csv` | `data/08_reporting_ep3/f13_estabilidad.csv` | 347 | `56621dd36fd2f54b...` |
| `f13_isolation_forest.csv` | `data/08_reporting_ep3/f13_isolation_forest.csv` | 184 | `9152d1168f6d8d49...` |
| `f13_resumen.json` | `data/08_reporting_ep3/f13_resumen.json` | 3.022 | `b75b665139ae1529...` |
| `f13_seleccion_k.csv` | `data/08_reporting_ep3/f13_seleccion_k.csv` | 796 | `9d151a0623d58dd8...` |
| `f1_reproduccion_pred_test.csv` | `data/08_reporting_ep3/f1_reproduccion_pred_test.csv` | 225 | `e7d522be5800e851...` |
| `f1_resumen.json` | `data/08_reporting_ep3/f1_resumen.json` | 1.594 | `4e1e7fa61ac799b9...` |
| `f2_baselines_reglas_41.csv` | `data/08_reporting_ep3/f2_baselines_reglas_41.csv` | 912 | `a913d6114b082c22...` |
| `f2_baselines_reglas_por_grupo.csv` | `data/08_reporting_ep3/f2_baselines_reglas_por_grupo.csv` | 890 | `8fac05cae6e35bb4...` |
| `f2_resumen.json` | `data/08_reporting_ep3/f2_resumen.json` | 447 | `9a42e8e76033c752...` |
| `f2_tasa_segmento_camara.csv` | `data/08_reporting_ep3/f2_tasa_segmento_camara.csv` | 6.755 | `fb639befd0604426...` |
| `f3_bordes.csv` | `data/08_reporting_ep3/f3_bordes.csv` | 646 | `040f168057658da2...` |
| `f3_config_por_fold.csv` | `data/08_reporting_ep3/f3_config_por_fold.csv` | 2.205 | `2cb15ba2b613076b...` |
| `f3_curvas_validacion.csv` | `data/08_reporting_ep3/f3_curvas_validacion.csv` | 10.571 | `d20ed7c6b28299bf...` |
| `f3_defecto_vs_optimizado.csv` | `data/08_reporting_ep3/f3_defecto_vs_optimizado.csv` | 3.490 | `50f0277a97d6a89a...` |
| `f3_por_fold.csv` | `data/08_reporting_ep3/f3_por_fold.csv` | 3.249 | `e2159fc4c86bc6af...` |
| `f4_candidatos_metricas.csv` | `data/08_reporting_ep3/f4_candidatos_metricas.csv` | 3.421 | `37dda7364011b179...` |
| `f4_ensambles_aporta.csv` | `data/08_reporting_ep3/f4_ensambles_aporta.csv` | 676 | `6bac43bb3bc9a73d...` |
| `f4_resumen.json` | `data/08_reporting_ep3/f4_resumen.json` | 1.676 | `05f589d663a1994a...` |
| `f5_auc_por_fold.csv` | `data/08_reporting_ep3/f5_auc_por_fold.csv` | 2.070 | `c0c0cf754d40727d...` |
| `f5_auc_por_segmento.csv` | `data/08_reporting_ep3/f5_auc_por_segmento.csv` | 8.981 | `8ed206a2c77d9801...` |
| `f5_brazoB.csv` | `data/08_reporting_ep3/f5_brazoB.csv` | 1.088 | `a37edb0d8ca16a61...` |
| `f5_brazoC.csv` | `data/08_reporting_ep3/f5_brazoC.csv` | 3.243 | `c9ca36d564cbcf23...` |
| `f5_brecha_LR3.csv` | `data/08_reporting_ep3/f5_brecha_LR3.csv` | 1.073 | `344dd5a7ea43cae6...` |
| `f5_brecha_Regla_top.csv` | `data/08_reporting_ep3/f5_brecha_Regla_top.csv` | 1.077 | `38063266c5b7a688...` |
| `f5_brecha_XGB.csv` | `data/08_reporting_ep3/f5_brecha_XGB.csv` | 1.048 | `31a1cbb3acaa1b76...` |
| `f5_calibracion_bins.csv` | `data/08_reporting_ep3/f5_calibracion_bins.csv` | 5.693 | `e37596b829f1849a...` |
| `f5_curva_aprendizaje_LR3.csv` | `data/08_reporting_ep3/f5_curva_aprendizaje_LR3.csv` | 8.007 | `a451f1e577c5db44...` |
| `f5_curva_aprendizaje_Regla_top.csv` | `data/08_reporting_ep3/f5_curva_aprendizaje_Regla_top.csv` | 8.015 | `a9bdbfe260d5e904...` |
| `f5_curva_aprendizaje_XGB.csv` | `data/08_reporting_ep3/f5_curva_aprendizaje_XGB.csv` | 7.998 | `5c37a8e41433d67b...` |
| `f5_loso_resumen_LR3.json` | `data/08_reporting_ep3/f5_loso_resumen_LR3.json` | 621 | `3709c9a44c8281f2...` |
| `f5_loso_resumen_Regla_top.json` | `data/08_reporting_ep3/f5_loso_resumen_Regla_top.json` | 630 | `664abef8a3e1cd12...` |
| `f5_loso_resumen_XGB.json` | `data/08_reporting_ep3/f5_loso_resumen_XGB.json` | 623 | `3ae0d28aecfe2be6...` |
| `f5_loso_segmentos_LR3.csv` | `data/08_reporting_ep3/f5_loso_segmentos_LR3.csv` | 2.413 | `c1f845f099f15f7c...` |
| `f5_loso_segmentos_Regla_top.csv` | `data/08_reporting_ep3/f5_loso_segmentos_Regla_top.csv` | 2.416 | `1c79186ec501b3bd...` |
| `f5_loso_segmentos_XGB.csv` | `data/08_reporting_ep3/f5_loso_segmentos_XGB.csv` | 2.382 | `18dcb16ff78202e7...` |
| `f5_metricas_candidatos.csv` | `data/08_reporting_ep3/f5_metricas_candidatos.csv` | 7.235 | `0a736fa20d0848d8...` |
| `f5_resumen.json` | `data/08_reporting_ep3/f5_resumen.json` | 193 | `a21fe9c8082c7c31...` |
| `f6_final_resumen.json` | `data/08_reporting_ep3/f6_final_resumen.json` | 222 | `35b963932aa3cad9...` |
| `f6_modelo_escogido.csv` | `data/08_reporting_ep3/f6_modelo_escogido.csv` | 1.259 | `2ae660fec4b0c997...` |
| `f6_seleccion.json` | `data/08_reporting_ep3/f6_seleccion.json` | 639 | `9684cb23a24d0db8...` |
| `f6_tabla_seleccion.csv` | `data/08_reporting_ep3/f6_tabla_seleccion.csv` | 4.719 | `978c7131f5979417...` |
| `lista_A_huecos.csv` | `data/08_reporting_ep3/lista_A_huecos.csv` | 357 | `eb079342be1e457a...` |
| `manifest_no_supervisado.json` | `data/06_models_ep3/manifest_no_supervisado.json` | 623 | `f0693e1a38cacdd5...` |
| `manifest_v3.json` | `data/06_models_ep3/manifest_v3.json` | 1.744 | `06807ad082a3c87f...` |
| `plan_v3.json` | `docs/ep3/plan_v3.json` | 4.160 | `cc3bcfb33e94180f...` |
| `plan_v3.md` | `docs/ep3/plan_v3.md` | 4.998 | `fff0a19898b1b003...` |
| `plan_v3.sha256` | `docs/ep3/plan_v3.sha256` | 156 | `01e0ccd660d9c560...` |
| `plan_v3_desviaciones.md` | `docs/ep3/plan_v3_desviaciones.md` | 2.857 | `ed28ca0429c934c6...` |
| `pruebas_ep3_conteo.json` | `data/08_reporting_ep3/pruebas_ep3_conteo.json` | 586 | `43659ea1b7971bb9...` |
| `umbrales_v3.json` | `data/06_models_ep3/umbrales_v3.json` | 31 | `3a9a893b4eda285c...` |
