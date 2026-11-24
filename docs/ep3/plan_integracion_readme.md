# Plan para que `README_EP3.md` sea el README raíz (NO aplicado)

Este documento lista qué habría que cambiar. No se modificó ningún archivo de EP2: `README.md` y `docs/informe_tecnico_EP2.md` siguen como están.

## 1. Qué depende hoy del `README.md` raíz (verificado en el repositorio)
| Pieza | Dependencia |
|---|---|
| `scripts/generar_readme.py` | **Genera** `README.md` desde los CSV y JSON de EP2 (15 secciones, ninguna cifra a mano). El README de EP1 vive en `docs/README_EP1.md`. |
| `tests/test_readme.py` (17 pruebas) | Ejecutan el generador y leen `README.md`; revisan tablas Markdown de `README.md`. |
| `tests/test_sincronia_readme_informe.py` (9 pruebas) | Comparan cifras y frases entre `README.md` y `docs/informe_tecnico_EP2.md`. |
| `tests/test_ajustes_finales.py` (11 pruebas) | Leen `README.md` y el informe; una de ellas compara el total de pruebas recogidas con el del README y con `pytest_resumen.json` (81). |
| `scripts/medir_pruebas.py`, `data/08_reporting/pytest_resumen.json` | Fuente del conteo de pruebas (81 pasadas, 0 falladas, 0 omitidas) que el README cita. |
| `scripts/empaquetar_entrega.py` | Incluye `README.md` en `entrega_EP2.zip`. |
| `pyproject.toml` | `readme = "README.md"`. |

Consecuencia: si se reemplaza `README.md` a mano por `README_EP3.md`, las 37 pruebas anteriores fallan o, peor, el generador lo vuelve a sobrescribir.

## 2. Estrategia recomendada: EP2 pasa a `docs/README_EP2.md`
1. **Conservar el README de EP2** como `docs/README_EP2.md` (igual que ya se hizo con EP1).
2. En `scripts/generar_readme.py`: cambiar la ruta de salida de `README.md` a `docs/README_EP2.md`, y los enlaces relativos internos (`docs/...` pasan a `...`; `README de EP1` ya está en `docs/`).
3. En los tres archivos de pruebas anteriores: cambiar `R / "README.md"` por `R / "docs" / "README_EP2.md"` (3 líneas: `test_readme.py:32` y `:79`, `test_sincronia_readme_informe.py:29`, `test_ajustes_finales.py:28`).
4. Copiar `docs/ep3/README_EP3.md` a `README.md` (raíz). Ajustar sus enlaces relativos: los de `docs/ep3/...` pasan a `docs/ep3/...` sin el prefijo `../`, y agregar un enlace «Entrega anterior (EP2): `docs/README_EP2.md`».
5. Para la entrega de EP3 ya existe `scripts/ep3/empaquetar_entrega_ep3.py` (arma `artefactos_ep3/` y `entrega_EP3.zip`; verificado en copia limpia en `docs/ep3/verificacion_copia_limpia.md`). Si se quisiera unificar con `scripts/empaquetar_entrega.py`, habría que agregar en éste (no se modificó) `docs/ep3/`, `app/`, `Dockerfile`, `docker-compose.yml`, `requirements_app.txt`, `requirements_ep3.txt`, `constraints_ep3.txt`, `scripts/ep3/`, `src/waymo_evaluacion/ep3/`, `tests/ep3/`, `notebooks/00b…14`, `images/ep3/` y de `data/`: `data/05_model_input_ep3`, `data/06_models_ep3`, `data/08_reporting_ep3` (no `data/09_app_ep3` ni nada con filas por caja si se va a distribuir: ver límite de licencia).
6. Recalcular el conteo de pruebas oficial. Orden obligatorio que ya exige el propio proyecto: `scripts/medir_pruebas.py` → `scripts/generar_informe_tecnico.py` → `scripts/generar_readme.py`. Con `tests/ep3/` dentro del conteo (<!--n_ep3-->407<!--/n_ep3--> pruebas recolectadas con `scripts/ep3/contar_pruebas.py`, sin ejecutar), el total oficial pasa de <!--n_ep2-->81<!--/n_ep2--> a <!--n_total-->488<!--/n_total-->; quitar entonces `--ignore=tests/ep3` de `tests/test_ajustes_finales.py:174`.
7. `.gitignore`: `data/**` ignora todo lo de `data/*_ep3`. Si los resultados de EP3 deben quedar en git, agregar excepciones explícitas (por ejemplo `!data/08_reporting_ep3/` y `!data/06_models_ep3/manifest_v3.json`), sin incluir datos por caja.

## 3. Alternativa mínima (sin tocar el generador)
Dejar `README.md` de EP2 intacto y agregar al principio, manualmente, una línea «Entrega final EP3: ver `docs/ep3/README_EP3.md`». **No es compatible con los tests** si el generador vuelve a correr (lo sobrescribe), así que solo sirve como parche temporal y habría que modificar el generador para que la emita.

## 4. Validación en una copia limpia
```
git clone <repo> copia && cd copia && python -m venv .venv && .venv\Scripts\pip install -r requirements.txt -r requirements_ep3.txt -c constraints_ep3.txt
(copiar data/ desde el equipo original; está fuera de git)
python scripts/verificar_congelados.py              # 14 de 14
python scripts/ep3/verificar_congelados_v3.py       # v3 congelado
python -m pytest -q                                  # suite completa (solo en la copia)
```

## 5. Riesgos
- Regenerar README e informe actualiza fechas y marcas de tiempo: aparecen como cambios aunque no cambie ninguna cifra (pasó en EP2 al correr `pytest`).
- Cambiar rutas de salida del generador cambia los enlaces internos del informe de EP2 (`docs/informe_tecnico_EP2.md` enlaza al README).
- La entrega de EP2 (`entrega_EP2.zip`) debe quedar como está: es el paquete entregado.

## 6. Estado de la entrega de EP3 (2026-11-14)
- `artefactos_ep3/` (versionable, solo tablas agregadas y manifests) y `entrega_EP3.zip` (ignorado por git: `.gitignore` tiene `entrega_EP3.zip` y `docs/ep3/revision/`).
- Para que el README raíz sea `README_EP3.md` hay que seguir las secciones 2 a 5 de este documento; no se aplicó.
- Las referencias de `README_EP3.md` al informe usan la numeración nueva (secciones 0 a 18 y anexos A y B); si se copia a la raíz, las rutas `docs/ep3/...` ya son relativas a la raíz.
- Cierre (F16): el conteo de pruebas se recolecta con `scripts/ep3/contar_pruebas.py` (`pytest --collect-only`, sin ejecutar) y los documentos lo leen de `data/08_reporting_ep3/pruebas_ep3_conteo.json`: hoy EP2 <!--n_ep2-->81<!--/n_ep2--> + EP3 <!--n_ep3-->407<!--/n_ep3--> = <!--n_total-->488<!--/n_total-->. Antes de quitar `--ignore=tests/ep3` hay que volver a correr `scripts/medir_pruebas.py` (solo en una copia limpia).
- Si `README_EP3.md` pasa a ser el README raíz, conservar su aviso de seguridad (la página escucha solo en `localhost`; no exponerla sin autenticación) y la referencia a `docs/ep3/MAPA_DE_ARCHIVOS.md` como orden de lectura.
- Documentos generados (no editar a mano): `generar_docs_ep3.py`, `generar_pendientes_pagina.py`, `generar_mapa.py`, `actualizar_revision.py`.
