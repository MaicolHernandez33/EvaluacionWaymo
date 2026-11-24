"""F27: el menú sigue el orden del proceso (filtro de cámaras y priorización de cajas) y la Auditoría termina con el enlace al paso siguiente.
(El Resumen en dos pasos de F27 lo reemplazó el rediseño de F29: ver ``test_pagina_f29.py``.) Escribe solo en ``tmp_path``."""
from __future__ import annotations

import sys
from pathlib import Path

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))


def test_el_menu_sigue_el_orden_del_proceso_y_los_nombres_de_las_secciones_no_cambian() -> None:
    import waymo_evaluacion.ep3.app_logica as A

    grupos = list(A.GRUPOS_NAV)
    assert grupos[:3] == ["Visión general", A.PASO_FILTRO, A.PASO_PRIORIZACION]
    assert A.GRUPOS_NAV[A.PASO_FILTRO] == ["Auditoría de cámaras"] and A.GRUPOS_NAV[A.PASO_PRIORIZACION] == ["Cola de revisión"] and A.GRUPOS_NAV["Herramientas"] == ["Explica una caja", "Puntuar datos nuevos"]          # F33: «Explica una caja» pasó a «Herramientas»
    assert A.SECCIONES.index("Auditoría de cámaras") < A.SECCIONES.index("Cola de revisión") and A.SECCIONES[0] == "Resumen"          # el filtro va antes que la cola; Resumen sigue siendo la página por defecto
    assert len(A.SECCIONES) == 8 and len(set(A.SECCIONES)) == 8


def test_la_auditoria_lleva_a_la_cola_con_un_boton_visible_arriba() -> None:
    import waymo_evaluacion.ep3.app_logica as A

    fuente = (R / "app" / "secciones.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def auditoria("):fuente.index("def _barras_con_ic(")]
    assert 'with k_der, st.container(key="ir_cola"):' in cuerpo and 'st.page_link(ARCHIVO_PAGINA["Cola de revisión"], label=ENLACE_COLA_DESDE_AUDITORIA)' in cuerpo
    assert cuerpo.index("ir_cola") < cuerpo.index('key="aud_celdas"')                                                       # F31: el botón va en la franja de arriba, no suelto al final
    assert A.ENLACE_COLA_DESDE_AUDITORIA == "Ir a la cola de revisión →" and A.ENLACE_COLA_DESDE_AUDITORIA not in fuente