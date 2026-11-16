# Preguntas cruzadas con respuesta, cifra y fuente

*Generado por `scripts/ep3/generar_docs_ep3.py`. 77 preguntas; cada cifra sale del archivo indicado (carpeta `data/08_reporting_ep3` salvo que se diga otra). Las referencias a secciones corresponden a `informe_tecnico_EP3.md`.*

**1. ¿Qué problema resuelve el proyecto?**
- Respuesta: Ayuda a una persona a decidir qué cajas 3D de peatones y ciclistas probablemente no tienen su pareja 2D de cámara, para revisarlas primero.
- Cifra: 80.571 cajas en la población principal; 21,2 % sin pareja
- Fuente: `f1_resumen.json`

**2. ¿Qué es `sin_camara`?**
- Respuesta: Es 1 si la caja 3D no tiene par en ninguna de las 5 cámaras. Es el target.
- Cifra: 17.102 positivos
- Fuente: `f1_resumen.json`

**3. ¿Por qué la población principal es |azimut| <= 100°?**
- Respuesta: Más allá la tasa de `sin_camara` sube mucho (EP2); la sensibilidad a 120° se estudió en EP2.
- Cifra: AZ_MAX = 100
- Fuente: `data/05_model_input/config_features_B.json`

**4. ¿Por qué validar por segmento?**
- Respuesta: Las cajas de un mismo segmento (20 s de video) se parecen; mezclarlas entre entrenamiento y validación infla el resultado.
- Cifra: segmentos repartidos entre folds: 0
- Fuente: `f1_resumen.json`

**5. ¿Por qué los 8 segmentos de test de EP2 ya no son ciegos?**
- Respuesta: Se abrieron 6 veces en EP2; ahora son material de desarrollo y la prueba ciega será con segmentos nuevos.
- Cifra: 41 = 33 + 8 segmentos
- Fuente: `plan_v3.md (P1), f1_resumen.json`

**6. ¿Qué hace el detector de huecos?**
- Respuesta: Mide, por segmento y cámara, la fracción de cajas con par dentro del rango de azimut de esa cámara; si es menor al 25 % de la mediana y hay >= 100 cajas, marca un hueco.
- Cifra: 2 celdas con hueco, iguales a EP2
- Fuente: `f2_resumen.json`

**7. ¿Qué contienen las celdas con hueco?**
- Respuesta: Una parte importante de los positivos, concentrada en pocas celdas.
- Cifra: 1.565 de 17.102 positivos (9,2 %)
- Fuente: `f2_resumen.json`

**8. ¿Es el hueco una conclusión firme?**
- Respuesta: No: es post hoc, no pre-declarado; puede ser etiquetado 2D faltante o datos de cámara ausentes, y con estos archivos no se distingue.
- Cifra: 2 celdas
- Fuente: `informe, sección 8`

**9. ¿Qué son las listas A y B?**
- Respuesta: A: celdas con hueco, se atienden aparte. B: cajas de celdas sanas, ordenadas por la regla.
- Cifra: A = 2 celdas
- Fuente: `lista_A_huecos.csv`

**10. ¿Cómo se optimizaron los hiperparámetros?**
- Respuesta: Búsqueda aleatoria anidada: la elección usa solo segmentos de entrenamiento (CV interna GroupKFold(3), criterio PR-AUC).
- Cifra: 30 configuraciones por modelo (DEV-1)
- Fuente: `f3_tuning.py, plan_v3.md (P5)`

**11. ¿Qué significa «mejora»?**
- Respuesta: Diferencia de PR-AUC >= +0,010 con IC pareado por segmentos que excluya 0.
- Cifra: mejoran XGB, LGBM
- Fuente: `f3_defecto_vs_optimizado.csv`

**12. ¿Por qué XGBoost y LightGBM sí mejoran?**
- Respuesta: Porque su configuración por defecto se sobreajusta y la búsqueda los regulariza; no porque terminen mejores que la regla.
- Cifra: XGB dif. PR-AUC 0,059; AUC optimizado 0,800 contra regla 0,823
- Fuente: `f3_defecto_vs_optimizado.csv, f5_metricas_candidatos.csv`

**13. ¿Se revisaron los bordes de la grilla?**
- Respuesta: Sí. Solo LightGBM `min_child_samples` quedó en el borde; se extendió una vez. Después `n_estimators` quedó en el máximo: limitación declarada.
- Cifra: LightGBM n_estimators = 200 en 5 de 5 folds
- Fuente: `f3_bordes.csv`

**14. ¿Qué muestran las curvas de validación?**
- Respuesta: Que al aumentar la complejidad el entrenamiento sube y la validación no; lo mejor está en lo más regularizado.
- Cifra: HGB validación 0,686 con 2 hojas y 0,663 con 31
- Fuente: `f3_curvas_validacion.csv`

**15. ¿Qué ensambles probaron?**
- Respuesta: E1 voting soft, E2 promedio de rangos con la regla, E3 stacking de 5 modelos, E4 stacking por vistas.
- Cifra: 4 ensambles
- Fuente: `plan_v3.md (P6)`

**16. ¿Por qué el stacking se hizo a mano?**
- Respuesta: El CV interno por defecto de scikit-learn mezcla segmentos y filtra información; usamos GroupKFold(3) por segmento dentro de cada fold externo.
- Cifra: GroupKFold(3)
- Fuente: `candidatos.py, f4_ensambles.py`

**17. ¿Aporta algún ensamble?**
- Respuesta: No. E1 queda cerca de 0 con IC que incluye 0; E3 y E4 quedan por debajo de su mejor componente.
- Cifra: E1 0,005 (IC -0,007 a 0,020); gana en 3 de 5 folds y 21 de 31 segmentos
- Fuente: `f4_ensambles_aporta.csv`

**18. ¿Por qué no ayuda promediar modelos?**
- Respuesta: Todos usan la misma señal (los puntos LiDAR) y se equivocan juntos.
- Cifra: E2 contra regla: 0,001
- Fuente: `f4_ensambles_aporta.csv`

**19. ¿Qué mide el AUC y qué la PR-AUC?**
- Respuesta: El AUC es la probabilidad de que una caja sin pareja puntúe más alto que una con pareja; la PR-AUC pondera la precisión cuando los positivos son una minoría.
- Cifra: AUC 0,823, PR-AUC 0,672
- Fuente: `f6_modelo_escogido.csv`

**20. ¿Qué es la Captura@20 %?**
- Respuesta: La fracción de positivos que aparece en el 20 % de cajas mejor ordenadas.
- Cifra: 61,9 % (al azar 20 %)
- Fuente: `f5_metricas_candidatos.csv`

**21. ¿Qué es la Fracción para 80 %?**
- Respuesta: La fracción de cajas que hay que revisar para encontrar el 80 % de los positivos.
- Cifra: 44,6 % en un paso; 29,6 % en dos pasos (en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos)
- Fuente: `f5_brazoC.csv`

**22. ¿Qué son los puntos A y B?**
- Respuesta: A: umbral que busca recall 0,80, fijado con scores internos de entrenamiento. B: umbral que revisa el 20 % de las cajas.
- Cifra: recall A 0,798; recall B 0,629
- Fuente: `f5_metricas_candidatos.csv`

**23. ¿Está calibrada la probabilidad?**
- Respuesta: Con Platt, el ECE queda bajo 0,05 en la regla.
- Cifra: ECE 0,044, Brier 0,112
- Fuente: `f5_metricas_candidatos.csv`

**24. ¿Es estable la solución?**
- Respuesta: Por segmento sí (mediana alta); por fold no cumple el criterio de 0,75 en ningún candidato, por el fold 0.
- Cifra: mediana por segmento 0,898; mínimo por fold 0,647
- Fuente: `f5_metricas_candidatos.csv`

**25. ¿Qué muestra el leave-one-segment-out?**
- Respuesta: Que dejar un segmento fuera casi no cambia el AUC global y que hay segmentos difíciles.
- Cifra: AUC LOSO 0,823; 2 de 22 segmentos con AUC < 0,55
- Fuente: `f5_loso_resumen_Regla_top.json`

**26. ¿Hay sobreajuste en los modelos de árboles?**
- Respuesta: Sí: la brecha de ajuste a validación es grande y no se cierra con más segmentos. La regla no tiene brecha porque no aprende.
- Cifra: XGB: ajuste 0,917, validación 0,815
- Fuente: `f5_brecha_XGB.csv`

**27. ¿Por qué se eligió la regla?**
- Respuesta: Por el plan: el más simple cuyo AUC queda a menos de 0,010 del mejor; nadie cumplió O4 y se aplicó una regla de reserva post hoc entre los que cumplen O1 y O3.
- Cifra: ningún candidato cumple O4 (regla de reserva DEV-2); entre los 11 candidatos que cumplen O1 y O3, el mejor AUC OOF es 0,824; los que quedan a menos de 0,010 son Regla top, E2; el más simple es Regla top
- Fuente: `f6_seleccion.json, plan_v3_desviaciones.md (DEV-2)`

**28. ¿Algún candidato «vale la pena» frente a la regla (O2)?**
- Respuesta: Ninguno.
- Cifra: mejor dif. de Fracción 80 %: -0,025 (E2, IC -0,048 a 0,008)
- Fuente: `f6_tabla_seleccion.csv`

**29. ¿Cuánto cuesta revisar?**
- Respuesta: Con el supuesto de 20 s por caja (no medido, editable en la página): horas para el 80 % de recall.
- Cifra: un paso 200 h; dos pasos 132 h (en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos); al azar 358 h
- Fuente: `f6_modelo_escogido.csv`

**30. ¿Qué es el punto de equilibrio?**
- Respuesta: El costo en cajas por auditoría con el que dos pasos empata con un paso; no inventamos un costo.
- Cifra: 6.059 cajas (IC 1.227 a 13.258) (en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos)
- Fuente: `f5_brazoC.csv`

**31. ¿Qué hace la página?**
- Respuesta: Es una consola de revisión con navegación agrupada: un resumen con el impacto estimado y alertas, la cola de revisión (cuánto revisar o cuánto encontrar, con ambos flujos, detalle por caja, vista por objeto y filtros), el mapa de huecos, la explicación de una caja con ejemplos de un clic, la validación con un gráfico por tema, la ficha de ética, el puntaje de segmentos nuevos y una ayuda con glosario.
- Cifra: 8 páginas, 3 roles
- Fuente: `app/app.py, app/secciones.py`

**32. ¿Cómo se despliega?**
- Respuesta: Local con Streamlit o con Docker (volumen de datos de solo lectura, sin datos en la imagen). Docker no se probó; AWS es solo una guía.
- Cifra: Docker 28.3.0 instalado, demonio apagado
- Fuente: `despliegue.md`

**33. ¿Qué pasa con la licencia y la privacidad?**
- Respuesta: Los datos de Waymo no salen del equipo; los identificadores se ocultan en modo presentación; el zip es solo para uso académico del docente.
- Cifra: sin red, sin datos en la imagen
- Fuente: `despliegue.md, informe sección 16`

**34. ¿Qué cambió respecto de EP2?**
- Respuesta: 41 segmentos juntos, + XGBoost y LightGBM, búsqueda anidada, ensambles, filtro 1 en el flujo, no supervisado, página y despliegue.
- Cifra: ver tabla de cambios
- Fuente: `informe_tecnico_EP3.md, sección 6`

**35. ¿Por qué no hay nodos de Kedro en EP2 y EP3?**
- Respuesta: El análisis vive en notebooks y scripts; los pipelines de Kedro son los de ingesta y preprocesamiento de EP1.
- Cifra: -
- Fuente: `informe_tecnico_EP3.md, sección 6`

**36. ¿Por qué 1 repetición y 30 configuraciones?**
- Respuesta: Regla de cómputo: la proyección con el plan completo superaba 4 horas (RF tarda 45 a 100 s por ajuste). Está registrado como DEV-1.
- Cifra: DEV-1
- Fuente: `plan_v3_desviaciones.md`

**37. ¿Qué son accuracy y F1 aquí?**
- Respuesta: Solo referencia en el cuadro «Modelo escogido»; no deciden nada.
- Cifra: F1 en A 0,511; accuracy en A 0,676
- Fuente: `f6_modelo_escogido.csv`

**38. ¿Qué falta?**
- Respuesta: Validación externa con segmentos nuevos (sellada), probar Docker y medir el tiempo real de revisión.
- Cifra: -
- Fuente: `informe_tecnico_EP3.md, sección 17`

**39. ¿Dónde está el Machine Learning si la solución final es una regla?**
- Respuesta: El ML son los 11 candidatos entrenados y comparados con búsqueda anidada y validación por segmento (LR, RF, HGB, XGBoost, LightGBM, cuatro ensambles, la regla y una LR de 3 variables), y ninguno la supera de forma distinguible; además el ML aporta la calibración Platt (una regresión logística) y el análisis no supervisado. El detector de huecos **no es ML**: son percentiles, una mediana y un umbral (estadística descriptiva). Concluir que una regla basta es un resultado del aprendizaje automático, no su ausencia.
- Cifra: 11 candidatos; AUC regla 0,823 contra el mejor modelo 0,808
- Fuente: `f5_metricas_candidatos.csv, f6_tabla_seleccion.csv`

**40. ¿Por qué no elegir E2 si tiene mejor PR-AUC?**
- Respuesta: Porque la diferencia no es distinguible y E2 contiene a la regla: AUC 0,824 contra 0,823, PR-AUC 0,696 contra 0,672, Fracción 80 % 0,421 contra 0,446 (IC de la diferencia -0,048 a 0,008). Además su ECE es 0,069 (> 0,05). El plan manda elegir el más simple dentro de 0,010 de AUC.
- Cifra: dif. AUC 0,001
- Fuente: `f6_tabla_seleccion.csv, f4_ensambles_aporta.csv`

**41. ¿Por qué RF empeora al optimizar?**
- Respuesta: No lo sabemos: es una hipótesis (no verificada) que la búsqueda interna, con 30 configuraciones y 41 segmentos, elige configuraciones que se ajustan a particularidades de los segmentos de entrenamiento y no se sostienen en el fold de validación. LR también empeora, con otra posible causa (el criterio interno puede preferir variables y regularización distintas).
- Cifra: RF dif. PR-AUC -0,040 (IC -0,077 a 0,003); LR -0,018
- Fuente: `f3_defecto_vs_optimizado.csv`

**42. ¿Por qué 1 repetición de la CV externa?**
- Respuesta: Porque Random Forest tarda 45 a 100 s por ajuste y el plan completo (3 repeticiones x 40 configuraciones) proyectaba unas 5 horas, sobre el límite de 4. Consecuencia: los IC reflejan una sola partición de segmentos en folds.
- Cifra: DEV-1
- Fuente: `plan_v3_desviaciones.md`

**43. ¿Qué pasa en el fold 0?**
- Respuesta: Contiene 7 segmentos y 14.968 cajas, entre ellos `257766998801` (cámara 3 sin pares). El AUC de la regla es 0,647 en el brazo A y 0,842 sobre celdas sanas: el fallo del criterio de estabilidad se debe a la celda con hueco. Post hoc.
- Cifra: AUC A 0,647; B 0,842
- Fuente: `f12_auc_por_fold_brazos.csv`

**44. ¿El 29,6 % no es circular?**
- Respuesta: En parte sí: los parámetros del detector se ajustaron con estos 41 segmentos y el hueco se descubrió en ellos, y la ganancia sale de 2 celdas cámara x segmento. Por eso se rotula en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos. La diferencia pareada con un paso es -0,150 con IC -0,490 a 0,000 (no excluye 0). La prueba no circular es la validación con segmentos nuevos.
- Cifra: 29,6 % contra 44,6 %
- Fuente: `f5_brazoC.csv, f12_diferencia_C_menos_A.csv`

**45. ¿Qué pasa si el hueco no existe en datos nuevos?**
- Respuesta: El detector no marcaría nada (o marcaría celdas sin verdad externa que lo confirme) y el flujo se reduce a la cola con la regla: dos pasos pasa a ser un paso, y la Fracción para 80 % vuelve a unos 44,6 %. Las celdas marcadas además de los 2 de referencia en la muestra van de 0 a 2 celdas según los parámetros; su tasa en datos nuevos se medirá en la validación externa (sin verdad externa, no es una tasa de error).
- Cifra: celdas marcadas extra 0 a 2
- Fuente: `f12_sensibilidad_detector.csv`

**46. ¿Qué muestran los clusters y qué no?**
- Respuesta: Muestran que los casos lejanos y poco densos tienen mucha más tasa de `sin_camara` (31,8 %) que los cercanos y densos (8,9 %). No muestran grupos naturales firmes (ARI KMeans–GMM: 0,008 con el GMM de covarianza `full` y 0,884 con el GMM esférico; el discrepante es el `full`) ni causalidad.
- Cifra: k = 2; silhouette 0,317
- Fuente: `f13_clusters_k2.csv, f13_resumen.json`

**47. ¿Mejoran los clusters la predicción?**
- Respuesta: No. Agregar el cluster a la probabilidad de la regla cambia el AUC en -0,0015 (IC -0,0055 a 0,0023) con k = 2 y en -0,0097 con k = 4 (IC -0,0150 a -0,0044: la empeora). El AUC base de esa comparación es 0,798 y no 0,823 porque usa la probabilidad con Platt de cada fold y una regresión logística adicional (informe §9). Sobre el acuerdo entre técnicas: (ARI KMeans–GMM: 0,008 con el GMM de covarianza `full` y 0,884 con el GMM esférico; el discrepante es el `full`).
- Cifra: dif. AUC k = 2: -0,0015
- Fuente: `f13_aporte_cluster.csv`

**48. ¿Por qué ese k?**
- Respuesta: Se elige k por el máximo silhouette entre 2 y 6: k = 2 (0,317); se explora también k = 4 como en EP2 (0,243). Con k = 4 la estabilidad por segmentos es baja (ARI mínimo 0,401) y los clusters empeoran la predicción. Sobre el acuerdo entre técnicas: (ARI KMeans–GMM: 0,008 con el GMM de covarianza `full` y 0,884 con el GMM esférico; el discrepante es el `full`).
- Cifra: silhouette k = 2: 0,317
- Fuente: `f13_seleccion_k.csv, f13_estabilidad.csv`

**49. ¿Qué sesgos mediste?**
- Respuesta: Descriptivamente, el recall de la regla en el punto A por ubicación, momento del día y clase. Con celdas con hueco: de día 0,760 y de noche 0,873; San Francisco 0,779; ciclistas 0,443 (solo 115 positivos). Sin pruebas de hipótesis; parte de la brecha desaparece al quitar las celdas con hueco.
- Cifra: recall A global 0,804
- Fuente: `f12_equidad.csv`

**50. ¿El ARI tan bajo entre KMeans y GMM es un error de código?**
- Respuesta: No. Las tres técnicas usan las mismas 15.000 filas en el mismo orden, el ARI recalculado coincide con el original y los GMM convergieron. KMeans coincide con el GMM esférico (0,884) y con el diagonal; el discrepante es el GMM de covarianza `full` (0,008), que parte la muestra 70/30 contra 47/53 de KMeans. En EP2 el 0,997 usó variables de oclusión discretas con covarianzas degeneradas (`docs/informe_tecnico_EP2.md:422`); hipótesis, no verificada: ese 0,997 probablemente estaba inflado y el 0,008 no es la anomalía.
- Cifra: ARI KMeans–GMM 0,008 (full) y 0,884 (esférico), k = 2
- Fuente: `f13_ari_diagnostico.csv, f13_ari_diagnostico.json, docs/informe_tecnico_EP2.md:408-429, data/08_reporting/08_no_supervisado_resumen.json:5-7`

**51. ¿El brazo C no es mejor que A por construcción?**
- Respuesta: En cajas revisadas, casi: la auditoría quita cajas de la cola sin costo por caja, así que C no puede ser peor que A; lo informativo es el punto de equilibrio (6.059 cajas por auditoría) y la tasa de celdas marcadas del detector (con su estabilidad), que solo se miden con datos nuevos. Rótulo: en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos.
- Cifra: dif. C menos A -0,150 (IC -0,490 a 0,000)
- Fuente: `f12_diferencia_C_menos_A.csv, f5_brazoC.csv`

**52. ¿Por qué el límite superior del IC de C menos A es exactamente 0?**
- Respuesta: Porque en las réplicas del bootstrap que no contienen ninguno de los 2 segmentos con hueco, C es igual a A. Con 41 segmentos muestreados con reemplazo la probabilidad exacta de ese evento es 12,87 % (((41-2)/41)^41) y se observó 11,9 % en 1.000 réplicas: es un efecto del diseño, no evidencia a favor ni en contra de C.
- Cifra: exacta 12,87 %; observada 11,9 %
- Fuente: `f12b_hechos_brazoC.json`

**53. ¿Qué muestra la página con «Todos» y 20 %, y por qué no coincide con el 61,9 %?**
- Respuesta: Muestra el brazo de dos pasos (C): «unas 70 de cada 100 cajas sin pareja» (70,3 %; intervalo 62,4 % a 78,9 %), 15.726 cajas y 87,4 h con 20 s por caja (en muestra). El 61,9 % es la captura del brazo de un paso (A) al revisar el 20 % y está en la pestaña Selección de Validación; son brazos distintos. **El «20 %» tampoco es el mismo:** la página toma el 20 % de la cola de celdas sanas (15.726 cajas) y el informe §12 el 20 % del total (16.115 cajas), por eso el brazo C da 70,2 % en la página y 70,9 % en el informe. Tras el rediseño la página usa una sola fuente (el conteo observado, 70,3 %); antes la tarjeta mostraba 70,2 % (curva interpolada) y el texto 70,3 %.
- Cifra: C 70,3 %; A 61,9 %
- Fuente: `data/09_app_ep3 (kpis.json, curva_cola.csv), f5_metricas_candidatos.csv, f18_definiciones.json`

**54. ¿La regla trata igual a todos los casos?**
- Respuesta: No. Con celdas con hueco, de día el recall es 0,760 y de noche 0,873; sin esas celdas, de día 0,920 y la brecha se invierte (era el hueco). San Francisco baja la brecha (0,779 a 0,866) pero queda. En ciclistas el recall es 0,443 contra 0,806 en peatones (115 positivos en 14 segmentos): poco confiable. Descriptivo, sin pruebas de hipótesis.
- Cifra: ciclistas 0,443
- Fuente: `f12_equidad.csv`

**55. ¿Se puede exponer la página en la red o publicarla en la nube?**
- Respuesta: No tal como está: escucha solo en localhost (`.streamlit/config.toml`), el compose publica el puerto solo en 127.0.0.1 y la página muestra identificadores de objeto. Para exponerla haría falta autenticación y quitar los identificadores, y los datos de Waymo no deben subirse a servicios de nube (licencia de uso no comercial). Una prueba vigila esa configuración.
- Cifra: address = localhost; 127.0.0.1:8501:8501
- Fuente: `.streamlit/config.toml, docker-compose.yml, tests/ep3/test_seguridad_pagina.py`

**56. ¿Qué recomiendas al negocio?**
- Respuesta: Usar la solución en tres capas (auditar cámaras primero, cola con la regla, persona que decide), monitorear el recall por segmento y por clase, medir el tiempo real de revisión y el costo de una auditoría, y validar con segmentos nuevos antes de confiar en el flujo en dos pasos.
- Cifra: punto de equilibrio 6.059 cajas (en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos)
- Fuente: `informe, sección 15; f5_brazoC.csv`

**57. ¿Por qué la regla ordena peor las cajas cercanas y densas? (post hoc)**
- Respuesta: Con k = 2, el AUC de la regla es 0,531 en las cercanas y densas y sube a 0,748 sin las cajas de las 2 celdas con hueco: buena parte de la pérdida viene del hueco (43 % de los positivos del cluster están ahí). Queda una brecha frente a las lejanas (0,842). Descriptivo, sin IC; post hoc, no pre-declarado.
- Cifra: AUC 0,531 a 0,748
- Fuente: `f13_auc_cluster_sin_huecos.csv, f13_clusters_k2.csv`

**58. ¿Por qué la tasa de sin_camara sube de 51–100 a más de 100 puntos? (post hoc)**
- Respuesta: Por las celdas con hueco: en el tramo > 100 hay 1.234 cajas de esas celdas con tasa 85,6 %. Con todas las cajas la tasa pasa de 5,7 % a 7,5 %; sin esas celdas va de 4,0 % a 2,3 % (decreciente). Hipótesis, no verificada: son cajas con muchos puntos cuya cámara no tiene etiquetas.
- Cifra: 7,5 % con hueco; 2,3 % sin hueco
- Fuente: `f12_eda_puntos_top_sin_huecos.csv, f12_eda_puntos_top_resumen.json`

**59. ¿Qué significa «30 de 30» en el detector? ¿Es sensibilidad?**
- Respuesta: No. Los 2 huecos de referencia los define el mismo detector con los parámetros de EP2, así que no hay verdad externa: «30 de 30» mide la estabilidad del conjunto marcado frente a los parámetros, no sensibilidad ni especificidad, y las celdas marcadas de más no son «falsas alarmas» comprobadas. Con segmentos nuevos se medirá la tasa de celdas marcadas y su estabilidad (DEV-3).
- Cifra: 30 de 30 combinaciones
- Fuente: `f12_sensibilidad_detector.csv, plan_v3_desviaciones.md (DEV-3)`

**60. ¿La selección de segmentos introdujo un sesgo?**
- Respuesta: Sí, a escala de segmento: EP2 evaluó 91 candidatos y descartó 50 (27 por asociación vacía, 21 por etiquetado ralo, 2 por pocas asociaciones); el rendimiento fue de 67 % de día y 29 % de noche. La causa (etiquetado o publicación) es desconocida y el detector solo se evaluó con etiquetado denso. Recomendación: un filtro 1 a nivel segmento (sin ML).
- Cifra: 50 de 91 descartados
- Fuente: `f18_seleccion_motivos.csv, f18_seleccion_rendimiento.csv, docs/seleccion_segmentos/registro_verificacion_ep2.csv`

**61. ¿Por qué recall objetivo 0,80?**
- Respuesta: Es una decisión heredada de EP2 (punto A), no validada con el negocio. La curva guardada da, con un paso, 28,0 %, 44,7 % y 68,4 % de las cajas para encontrar 70 %, 80 % y 90 % de las sin pareja; con dos pasos (en muestra) 19,8 %, 30,4 % y 48,5 % de la cola de celdas sanas.
- Cifra: fracción para 70/80/90 %: 28 %/45 %/68 % (un paso)
- Fuente: `data/09_app_ep3/curva_cola.csv`

**62. ¿Qué es la calibración de Platt?**
- Respuesta: Una regresión logística de una variable que convierte el puntaje de la regla en una probabilidad de no tener pareja. Se ajusta con puntajes internos del conjunto de entrenamiento de cada fold (DEC-7), no con el fold de validación. Resultado: ECE 0,044 (<= 0,05). No cambia el orden dentro de un fold.
- Cifra: ECE 0,044
- Fuente: `f5_metricas_candidatos.csv, f5_calibracion_bins.csv`

**63. ¿Cómo se evitó la fuga de datos?**
- Respuesta: Los folds se arman por segmento (ningún segmento en más de un fold: 0), la búsqueda de hiperparámetros es anidada (CV interna dentro del entrenamiento) y los umbrales y el calibrador se fijan con puntajes internos. Límites honestos: los parámetros del detector se ajustaron con los mismos 41 segmentos y los 8 de test de EP2 ya se habían mirado; por eso lo del brazo C es en muestra.
- Cifra: folds por segmento; búsqueda anidada
- Fuente: `f1_resumen.json, plan_v3.md (P1)`

**64. ¿Qué es el bootstrap por segmentos?**
- Respuesta: Se remuestrean segmentos completos con reemplazo (1.000 réplicas, semilla 42), se recalcula la métrica en cada réplica y el IC 95 % es el percentil 2,5 a 97,5. Respeta que las cajas de un segmento se parecen entre sí. Con 41 segmentos los IC son anchos.
- Cifra: 1.000 réplicas
- Fuente: `plan_v3.md (P1), metricas.py`

**65. ¿Por qué PR-AUC para optimizar y AUC para elegir?**
- Respuesta: Así lo fijó el plan v3: la búsqueda interna usa PR-AUC porque pesa más a la clase minoritaria (21,2 % sin pareja), y la comparación entre candidatos usa AUC porque no depende de la prevalencia, que cambia mucho entre segmentos. Ninguna de las dos reemplaza mirar la fracción de cajas para el recall objetivo.
- Cifra: prevalencia 21,2 %
- Fuente: `plan_v3.md (P1, P8)`

**66. ¿Por qué puntos del sensor superior y no los totales?**
- Respuesta: Es la regla heredada de EP2 y en los 41 segmentos es la mejor de las reglas simples, pero por poco: AUC 0,823 contra 0,820 con los puntos totales; esa diferencia no es un hallazgo firme.
- Cifra: AUC 0,823 vs 0,820
- Fuente: `f2_baselines_reglas_41.csv`

**67. ¿Qué pasa con la deriva de datos?**
- Respuesta: No se midió: el trabajo tiene 41 segmentos de 3 ubicaciones y una sola fuente. La solución está congelada; la recomendación es monitorear la tasa de celdas marcadas, la distribución de puntos del sensor superior y el recall por segmento, y reevaluar con la validación externa sellada.
- Cifra: sin medición
- Fuente: `informe, secciones 14 y 15`

**68. ¿Por qué no se elige E2 si gana en 5 de 5 folds?**
- Respuesta: Gana en 5 de 5 folds, pero por 0,0008 de AUC (IC -0,0048 a 0,0084), por debajo del umbral pre-declarado de 0,010 y con el IC incluyendo 0; además contiene a la regla y su ECE es 0,069. Con más repeticiones de la CV externa (hoy una, DEV-1) podría resolverse.
- Cifra: dif. AUC 0,0008; folds 5 de 5
- Fuente: `f4_ensambles_aporta.csv, plan_v3.md (P8)`

**69. ¿Cuál es la limitación principal de todo el trabajo?**
- Respuesta: Que todo es en muestra y sin prueba ciega: 41 segmentos, parámetros del detector ajustados con los mismos datos, y la ganancia del flujo en dos pasos sale de 2 celdas. Hasta correr la validación externa sellada no se puede decir que se sostenga.
- Cifra: 2 celdas; 41 segmentos
- Fuente: `informe, secciones 14 y 17`

**70. ¿Qué se haría con más tiempo?**
- Respuesta: (1) Correr la validación externa sellada; (2) medir el tiempo real de revisión y el costo de una auditoría; (3) averiguar la causa de los huecos (por ejemplo con `camera_box`); (4) más repeticiones de la CV externa y más ciclistas y segmentos de noche; (5) un filtro 1 a nivel segmento.
- Cifra: —
- Fuente: `informe, secciones 15 y 17`

**71. ¿Qué pasa con la celda `247562357599|cam5`, que aparece marcada cuando `frac` = 0,35? (post hoc, no pre-declarado, hipótesis no verificada)**
- Respuesta: El segmento `247562357599`, cámara 5, tiene 184 positivos en 665 cajas con más de 100 puntos del sensor superior (27,7 %) y es la celda que aparece marcada con `frac` = 0,35. Con los parámetros congelados (`frac` = 0,25) **no se marca**. Hipótesis (no verificada): podría ser un tercer hueco que el umbral de EP2 no alcanza a marcar; no hay verdad externa para decidirlo. No cambia el detector ni ninguna cifra.
- Cifra: 184 positivos en 665 cajas (27,7 %)
- Fuente: `f12_eda_puntos_top_resumen.json (top3_segmentos_positivos_mayor_100_sin_hueco), f12_sensibilidad_detector.csv (marcadas_lista)`

**72. ¿Por qué la solución contra la regla da diferencia cero fuera de muestra?**
- Respuesta: Porque la solución congelada v3 **es** la regla: su puntaje es `PuntuadorRegla(num_top_lidar_points)`, monótono con «menos puntos del sensor superior», así que la diferencia solución menos regla es 0 por construcción (no es un empate sorprendente). En su lugar se mide el desempeño de la regla fuera de muestra (AUC, PR-AUC, captura al 20 % y fracción para el 80 %, con intervalo por segmentos), su recall y precisión con los umbrales A = 32 y B = 11 congelados, el brazo C contra A y la tasa de celdas marcadas con dos denominadores. Para poder decir algo más se congelaron aparte dos alternativas, LR3 y XGBoost (DEV-4), que sí pueden compararse con la regla; no cambian la solución elegida.
- Cifra: diferencia solución menos regla = 0; alternativas: LR3 y XGBoost
- Fuente: `GUIA_VALIDACION_EXTERNA.md (sección 6), src/waymo_evaluacion/ep3/congelado.py, manifest_alternativas.json, plan_v3_desviaciones.md (DEV-4)`

**73. ¿Cómo se garantiza el sellado de la validación externa?**
- Respuesta: Con cuatro candados. (1) El orden de los candidatos nuevos queda fijado en `plan_seleccion_ep3.json` (sha256 en `plan_seleccion_ep3.sha256`) y el notebook 00b exige y verifica ese plan. (2) `evaluar_sellado.py congelar` guarda los sha256 de la lista de segmentos y de la solución v3 y de las alternativas **antes** de abrir los datos, y `copiar_sello_a_artefactos.py` los copia a `artefactos_ep3/`. (3) Commit y push previos, que hace la persona (los scripts nunca tocan git): el sello queda en el historial antes de la evaluación. (4) `evaluar` toma un candado de una sola evaluación y lo hace solo cuando el cálculo terminó; no se puede repetir con otros parámetros. Cualquier cambio posterior de código se declara como desviación con fecha y motivo.
- Cifra: 1 evaluación; 5 archivos de la solución v3 con sha256
- Fuente: `GUIA_VALIDACION_EXTERNA.md, docs/ep3/plan_seleccion_ep3.sha256, scripts/ep3/evaluar_sellado.py, data/06_models_ep3/manifest_v3.json`

**74. ¿Qué pasa si la validación externa no encuentra huecos? (caso A; estimación gruesa, post hoc)**
- Respuesta: Es el caso A: C es igual a A porque no hay celdas que auditar. **No refuta ni confirma el detector**: pudo no haber huecos. Con unas 70 celdas elegibles (≈ 26 segmentos × 5 cámaras × la fracción de celdas con ≥ 100 cajas en desarrollo, 111 de 205) y una tasa de 2 de 111 (1,8 %) en desarrollo, se esperarían ≈ 1,3 celdas marcadas, y la probabilidad de no marcar ninguna es del orden del 27 % (estimación gruesa tipo Poisson, exp(−1,3); post hoc, no pre-declarada). Por eso un resultado sin huecos es plausible y se interpreta con cautela; lo informativo seguiría siendo el desempeño de la regla fuera de muestra.
- Cifra: ≈ 1,3 celdas marcadas esperadas; probabilidad de ninguna ≈ 27 %
- Fuente: `GUIA_VALIDACION_EXTERNA.md (sección 7, caso A), plan_seleccion_ep3.json, f12_resumen.json`

**75. ¿Por qué se congelaron LR3 y XGBoost si la solución es la regla? (DEV-4)**
- Respuesta: Porque «solución contra regla» da 0 por construcción y no informa. Se congelaron antes de abrir datos (LR3 y XGBoost entrenadas con los 41 segmentos; XGBoost con la configuración más repetida entre los 5 folds, 2 de 5) para poder preguntar si algo más complejo mejora fuera de muestra. Son 4 comparaciones (diferencia de AUC y de fracción para el 80 %, para cada alternativa): un «gana» aislado es **exploratorio** (post hoc, sin corrección por comparaciones múltiples), no cambia la solución elegida y se usaría solo para decidir una validación nueva.
- Cifra: XGBoost: configuración elegida por 2 de 5; 4 comparaciones
- Fuente: `f19_alternativas_congeladas.json, manifest_alternativas.json, plan_v3_desviaciones.md (DEV-4)`

**76. ¿Cómo se eligieron los segmentos nuevos y qué sesgo tienen?**
- Respuesta: Se reconstruye el pool de EP2 (sin lluvia, al menos 190 frames, número de detecciones entre los percentiles 2.5 y 97.5), se excluyen los 91 evaluados por EP2 y se toman **cuotas fijas de 26 segmentos útiles** por momento del día y ubicación, con semilla 42 y un orden sellado. Sesgos: sobremuestreo de San Francisco de día (cuota 8 de 26, 313 candidatos), la noche mal representada (23 candidatos en San Francisco, 9 en Phoenix y ninguno en otras ubicaciones) y, como en EP2, solo segmentos con etiquetado no ralo. Por eso no se puede afirmar nada de la noche ni de otras ciudades.
- Cifra: 26 segmentos útiles; noche: 23 y 9 candidatos
- Fuente: `plan_seleccion_ep3.json, f18_seleccion_motivos.csv, f18_seleccion_rendimiento.csv`

**77. ¿Por qué el titular compara un paso contra el azar y el dos pasos va aparte?**
- Respuesta: Porque lo robusto es que ordenar la cola con la regla reduce el tiempo frente a revisar sin orden (de ≈ 358 h a ≈ 200 h, con 20 s por caja: supuesto), con un intervalo de captura al 20 % que queda lejos del azar (0,533 a 0,723 contra 0,20). El flujo en dos pasos (≈ 132 h) sale de 2 celdas y de parámetros ajustados con los mismos datos, con una diferencia pareada cuyo IC incluye 0 (-0,490 a 0,000): va como segunda barra rotulada «en muestra».
- Cifra: ≈ 358 h sin orden; ≈ 200 h un paso; ≈ 132 h dos pasos (en muestra)
- Fuente: `f6_modelo_escogido.csv, f5_brazoC.csv, f12_diferencia_C_menos_A.csv`
