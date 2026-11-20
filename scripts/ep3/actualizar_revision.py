"""Regenera docs/ep3/revision/ con COPIAS de los archivos pequenos del estado final (nada por caja) y su INDICE.md.

Los originales no se mueven. La carpeta esta en .gitignore. Se conserva, al final del INDICE, la seccion «Respuestas» de la revision anterior si existe.
Escribe solo en docs/ep3/revision/.
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[2]
DEST = R / "docs/ep3/revision"
PROHIBIDAS = {"key.laser_object_id", "key.frame_timestamp_micros", "laser_object_id", "fila_id", "fila_pp"}
MAX_BYTES = 1_000_000
ORIGENES = [
    # docs
    "docs/ep3/ESTADO.md", "docs/ep3/informe_tecnico_EP3.md", "docs/ep3/README_EP3.md", "docs/ep3/plan_v3.md", "docs/ep3/plan_v3_desviaciones.md", "docs/ep3/plan_integracion_readme.md",
    "docs/ep3/despliegue.md", "docs/ep3/guion_presentacion.md", "docs/ep3/preguntas_cruzadas.md", "docs/ep3/PENDIENTES_PAGINA.md", "docs/ep3/auditoria_diseno_pagina.md", "docs/ep3/REPORTE_F20.md", "docs/ep3/REPORTE_F21.md", "docs/ep3/MAPA_DE_ARCHIVOS.md", "docs/ep3/verificacion_copia_limpia.md", "docs/ep3/GUIA_VALIDACION_EXTERNA.md", "docs/ep3/guia_estilo_pagina.md", "docs/ep3/pagina_guia_demo.md", "docs/ep3/plan_seleccion_ep3.json", "docs/ep3/plan_seleccion_ep3.sha256", "docs/ep3/REPORTE_F18.md", "docs/ep3/REPORTE_F19A.md", "docs/ep3/REPORTE_F19B.md", "docs/ep3/ensayo_validacion_externa.md",
    # resultados agregados (sin filas por caja)
    "data/08_reporting_ep3/lista_A_huecos.csv", "data/08_reporting_ep3/f1_resumen.json", "data/08_reporting_ep3/f2_resumen.json", "data/08_reporting_ep3/f3_defecto_vs_optimizado.csv",
    "data/08_reporting_ep3/f4_ensambles_aporta.csv", "data/08_reporting_ep3/f5_metricas_candidatos.csv", "data/08_reporting_ep3/f6_seleccion.json",
    "data/08_reporting_ep3/f12_auc_por_fold_brazos.csv", "data/08_reporting_ep3/f12_diferencia_C_menos_A.csv", "data/08_reporting_ep3/f12_equidad.csv", "data/08_reporting_ep3/f12_resumen.json",
    "data/08_reporting_ep3/f12b_hechos_brazoC.json", "data/08_reporting_ep3/f13_resumen.json", "data/08_reporting_ep3/f13_ari_diagnostico.csv", "data/08_reporting_ep3/f13_ari_diagnostico.json",
    "data/08_reporting_ep3/pruebas_ep3_conteo.json", "data/08_reporting_ep3/f12_eda_puntos_top_sin_huecos.csv", "data/08_reporting_ep3/f12_eda_puntos_top_resumen.json", "data/08_reporting_ep3/f13_auc_cluster_sin_huecos.csv", "data/08_reporting_ep3/f18_definiciones.json", "data/08_reporting_ep3/f18_seleccion_motivos.csv", "data/08_reporting_ep3/f18_seleccion_rendimiento.csv", "data/08_reporting_ep3/pagina_comparacion_antes_despues.csv", "data/08_reporting_ep3/pagina_tiempos_carga.json", "data/06_models_ep3/manifest_v3.json", "data/06_models_ep3/manifest_no_supervisado.json", "data/06_models_ep3/manifest_alternativas.json", "data/08_reporting_ep3/f19_alternativas_congeladas.json", "data/08_reporting_ep3/ensayo_resultado.json", "data/08_reporting_ep3/pagina_arranque.json", "data/08_reporting_ep3/capturas_resultado.json",
]


def ignorado(rel: str) -> str:
    """Segun .gitignore (`data/**` ignorado); no se consulta git."""
    return "sí (`data/**`)" if rel.startswith("data/") else "no"


def main() -> None:
    previo = ""
    if (DEST / "INDICE.md").exists():
        txt = (DEST / "INDICE.md").read_text(encoding="utf-8")
        if "## Respuestas" in txt:
            previo = txt[txt.index("## Respuestas"):]
    DEST.mkdir(parents=True, exist_ok=True)
    for f in DEST.iterdir():
        if f.is_file():
            f.unlink()
    filas = []
    for rel in ORIGENES:
        src = R / rel
        if not src.exists():
            raise SystemExit(f"falta {rel}")
        if src.stat().st_size > MAX_BYTES:
            raise SystemExit(f"{rel} pesa {src.stat().st_size} bytes: no es un archivo pequeno")
        if src.suffix == ".csv" and set(pd.read_csv(src, nrows=1).columns) & PROHIBIDAS:
            raise SystemExit(f"{rel} tiene columnas por caja")
        shutil.copy2(src, DEST / src.name)
        filas.append(f"| `{src.name}` | `{rel}` | {src.stat().st_size:,} | {ignorado(rel)} |".replace(",", "."))
    assert len({Path(r).name for r in ORIGENES}) == len(ORIGENES), "nombres repetidos"
    cab = f"""# Índice de la carpeta de revisión

Copias (no movidas) de {len(ORIGENES)} archivos, regeneradas el {time.strftime('%Y-%m-%d')} con `scripts/ep3/actualizar_revision.py` para reflejar el estado final. No se copiaron parquets ni datos por caja. Los originales siguen en su ruta; si se editan, esta carpeta queda desactualizada (volver a correr el script). La carpeta está en `.gitignore`.

| Archivo copiado | Ruta de origen | Tamaño (bytes) | ¿Origen ignorado por git? |
|---|---|---|---|
"""
    nota = "\n\n*(La sección «Respuestas» es de la revisión anterior y se conserva tal cual; los números de línea que cita pueden haberse movido.)*\n\n" if previo else ""
    (DEST / "INDICE.md").write_text(cab + "\n".join(filas) + "\n" + nota + previo, encoding="utf-8")
    print(f"{len(ORIGENES)} copias + INDICE.md en {DEST.relative_to(R)}")


if __name__ == "__main__":
    main()
