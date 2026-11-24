"""F30: arma la carpeta ``images/ep3/pagina/para_revision/`` con exactamente los 17 archivos que se envían a revisión: una captura por página a 1366 px (sin 1920, sin versiones antiguas y sin copias
repetidas) y ``docs/ep3/REPORTE_F30.md``. La carpeta se vacía antes de copiar. Falla si falta algún archivo (no deja una carpeta a medias).

Uso: .venv\\Scripts\\python scripts/ep3/armar_para_revision.py   (después de regenerar las capturas y el reporte)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
IMG = RAIZ / "images/ep3/pagina"
DESTINO = IMG / "para_revision"
CAPTURAS = ["01_resumen_1366.png", "01_resumen_1366x768.png", "02_auditoria_de_camaras_1366.png", "03_cola_de_revision_1366.png", "03_cola_de_revision_sin_seleccion_1366.png", "02b_curvas_sin_referencia.png",
            "04_explica_una_caja_1366.png", "05_validacion_hiperparametros_1366.png", "05_validacion_ensambles_1366.png", "05_validacion_generalizacion_1366.png", "05_validacion_seleccion_1366.png",
            "05_validacion_no_supervisado_1366.png", "05_validacion_en_muestra_1366.png", "06_puntuar_datos_nuevos_1366.png", "07_etica_y_limites_1366.png", "08_ayuda_y_glosario_1366.png"]
REPORTE = RAIZ / "docs/ep3/REPORTE_F30.md"


def main() -> None:
    faltan = [n for n in CAPTURAS if not (IMG / n).exists()] + ([] if REPORTE.exists() else ["docs/ep3/REPORTE_F30.md"])
    if faltan:
        sys.exit(f"faltan archivos para armar la carpeta: {faltan}")
    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True)
    for n in CAPTURAS:
        shutil.copy2(IMG / n, DESTINO / n)
    shutil.copy2(REPORTE, DESTINO / REPORTE.name)
    nombres = sorted(p.name for p in DESTINO.iterdir())
    assert len(nombres) == 17, nombres
    print(f"{DESTINO} ({len(nombres)} archivos)")
    for n in nombres:
        print(f"  {n}  {(DESTINO / n).stat().st_size:,} bytes".replace(",", "."))


if __name__ == "__main__":
    main()
