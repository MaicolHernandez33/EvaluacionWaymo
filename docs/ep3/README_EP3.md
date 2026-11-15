# EP3: auditoría de cajas 3D sin par 2D en Waymo Open Dataset v2 (entrega final)

*Generado por `scripts/ep3/generar_docs_ep3.py`. EP2 sigue intacta (`README.md`, `docs/informe_tecnico_EP2.md`). Desviaciones: DEV-n; decisiones: DEC-n (`docs/ep3/ESTADO.md`).*

**En una frase.** Antes de revisar caja por caja, buscamos cámaras con huecos de pares por segmento (paso 1) y luego ordenamos las cajas de las celdas sanas con la regla «menos puntos LiDAR primero» (paso 2); una persona revisa y decide.

## Resultados clave (fuera de fold, 41 segmentos, IC 95 % por segmentos)
| Medida | Valor | Fuente |
|---|---|---|
| AUC de la regla elegida | 0,823 (0,725 a 0,900) | `f5_metricas_candidatos.csv` |
| Recall en el punto A (objetivo 0,80) | 0,798 (0,676 a 0,900) | idem |
| Captura al revisar el 20 % de las cajas | 61,9 % (53,3 % a 72,3 %) | idem |
| ¿Algún modelo o ensamble supera a la regla? | No de forma distinguible (E2 la contiene y empata; nadie cumple O2) | `f6_tabla_seleccion.csv` |
| ¿Algún ensamble aporta? | No | `f4_ensambles_aporta.csv` |
| Cajas para el 80 % de recall: un paso / dos pasos | 44,6 % / 29,6 % *(en muestra: 41 segmentos, parámetros del detector ajustados con los mismos datos; post hoc, no pre-declarado; sin validación con datos nuevos)* | `f5_brazoC.csv` |
| Dos pasos menos un paso (IC) *(en muestra)* | -0,150 (-0,490 a 0,000), no excluye 0 | `f12_diferencia_C_menos_A.csv` |
| ¿Mejoran los clusters la predicción? | No (descriptivo) | `f13_aporte_cluster.csv` |
| Pruebas | 98 en `tests/ep3` (EP2: 81; total 179) | `pruebas_ep3_conteo.json` (`pytest --collect-only`, sin ejecutar) |

**La ganancia del brazo C sale de 2 celdas cámara x segmento, una de ellas en el segmento donde se descubrió el hueco.**

## Estructura (todo lo nuevo en carpetas `*_ep3`)
| Carpeta | Contenido |
|---|---|
| `docs/ep3/` | plan v3 (congelado), informe, guion, preguntas, despliegue, ESTADO, desviaciones |
| `src/waymo_evaluacion/ep3/` | `detector_huecos`, `metricas`, `modelos`, `candidatos`, `inferencia`, `app_logica`, `sellado`, `plan`, `datos` |
| `scripts/ep3/` | `f1` a `f7`, `f12`, `f13`, `puntuar_segmento`, `evaluar_sellado`, `ingesta_nuevos`, verificaciones, `empaquetar_entrega_ep3` |
| `notebooks/` | `11` a `15` (ejecutados) y `00b` (Colab, sin ejecutar) |
| `app/` | página Streamlit |
| `artefactos_ep3/` | versionable (fuera de `data/`): manifests, umbrales, parámetros del detector, plan v3 y tablas agregadas |
| `data/*_ep3` | `05_model_input_ep3`, `06_models_ep3` (v3 congelado), `07_model_output_ep3`, `08_reporting_ep3`, `09_app_ep3` (ignoradas por git) |
| `tests/ep3/` | 98 pruebas |
| raíz | `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `requirements_app.txt`, `requirements_ep3.txt`, `constraints_ep3.txt` |

## Cómo reproducir
```
.venv\Scripts\pip install -r requirements.txt -r requirements_ep3.txt -c constraints_ep3.txt
python scripts/verificar_congelados.py              # EP2: 14 de 14
python scripts/ep3/verificar_congelados_v3.py       # plan v3 y solución v3
python scripts/ep3/verificar_no_supervisado.py
python scripts/ep3/f1_datos.py ; python scripts/ep3/f2_detector.py
python scripts/ep3/f3_tuning.py --etapa principal --ncfg 30 --workers 6   # horas
python scripts/ep3/f3_analisis.py ; python scripts/ep3/f4_ensambles.py
python scripts/ep3/f5_generalizacion.py ; python scripts/ep3/f6_seleccion.py ; python scripts/ep3/f5_loso_curva.py
python scripts/ep3/f6_final.py ; python scripts/ep3/f12_analisis_muestra.py ; python scripts/ep3/f13_no_supervisado.py ; python scripts/ep3/f7_preparar_app.py
python -m pytest tests/ep3 -q --no-cov -p no:cacheprovider
```
Para mirar sin recalcular: abrir los notebooks `11` a `15` (con `RECALCULAR = False` solo muestran artefactos).

## La página
`scripts\ep3\arrancar_app.bat` (o `python -m streamlit run app/app.py`) abre http://localhost:8501 y **escucha solo en localhost** (`.streamlit/config.toml`); no debe exponerse sin autenticación ni sin quitar los identificadores, ni publicarse en la nube con datos de Waymo. Docker: `docker compose up --build` (no probado; el puerto se publica solo en `127.0.0.1`). Detalles y guía de AWS (solo orientativa) en `docs/ep3/despliegue.md`.

## Qué falta
Validación con segmentos nuevos: `notebooks/00b_seleccion_segmentos_ep3.ipynb` en Colab, luego `evaluar_sellado.py congelar` y `evaluar` (una sola vez). Cómo dejar este archivo como README raíz: `docs/ep3/plan_integracion_readme.md`.
