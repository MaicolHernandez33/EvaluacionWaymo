"""F19-C1 a C3: tablas Markdown bien formadas, sin caracteres de control (rutas de Windows mal escapadas) y sin comillas sueltas en los documentos generados."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from waymo_evaluacion.ep3.chequeo_md import caracteres_de_control, constantes_con_control, problemas_de_tablas, revisar_carpeta

R = Path(__file__).resolve().parents[2]
CAMPANA = chr(7)          # lo que resulta de «\a» en una cadena no cruda


def test_una_tabla_bien_formada_no_da_problemas() -> None:
    md = "| a | b | c |\n|---|---|---|\n| 1 | 2 | 3 |\n| 4 | 5 | 6 |\n\ntexto\n"
    assert problemas_de_tablas(md) == []


def test_barras_sin_escapar_en_una_celda_rompen_la_tabla_y_las_escapadas_no() -> None:
    mal = "| segmento | Cajas en el rango (|azimut| ≤ 120°) |\n|---|---|\n| 1 | 300 |\n"
    p = problemas_de_tablas(mal)
    assert p and "separador" in p[0]
    assert any("línea 3" in x for x in p)
    bien = "| segmento | Cajas en el rango (\\|azimut\\| ≤ 120°) |\n|---|---|\n| 1 | 300 |\n"
    assert problemas_de_tablas(bien) == []
    assert problemas_de_tablas("| a | b |\n|---|---|\n| 1 | 2 | 3 |\n")                    # una fila con una celda de más
    assert problemas_de_tablas("| a | b |\n|---|---|\n| 1 |\n")                             # una fila con una celda de menos


def test_los_bloques_de_codigo_se_ignoran_y_dos_tablas_seguidas_se_revisan_por_separado() -> None:
    md = "```\n| a | b |\n|---|---|\n| 1 |\n```\n\n| x | y |\n|---|---|\n| 1 | 2 |\n\n| p | q | r |\n|---|---|---|\n| 1 | 2 |\n"
    p = problemas_de_tablas(md)
    assert len(p) == 1 and "línea 13" in p[0]


def test_detecta_caracteres_de_control_de_una_ruta_mal_escapada() -> None:
    ruta_mala = "scripts" + chr(92) + "ep3" + CAMPANA + "rrancar_app.bat"          # «scripts\ep3» + campana + «rrancar_app.bat»: lo que da «\a» sin escapar
    assert caracteres_de_control(f"abre {ruta_mala}\nlinea 2") == [(1, "U+0007")]
    assert caracteres_de_control("scripts" + chr(92) + "ep3" + chr(92) + "arrancar_app.bat\n" + chr(9) + "sangria") == [(2, "U+0009")]   # la ruta bien escrita no da nada; el tabulador sí
    assert caracteres_de_control("todo bien\nsin control\n") == []


def test_todos_los_documentos_de_docs_ep3_estan_limpios() -> None:
    mal = revisar_carpeta(R / "docs/ep3")
    assert not mal, {k: v[:3] for k, v in mal.items()}


def test_ningun_script_tiene_cadenas_con_caracteres_de_control() -> None:
    """Causa de raíz de C3: una ruta de Windows en una cadena no cruda. Se revisan los scripts, la lógica de la página y la propia página."""
    malos = {}
    for carpeta in ("scripts/ep3", "src/waymo_evaluacion/ep3", "app"):
        for p in sorted((R / carpeta).glob("*.py")):
            c = constantes_con_control(p)
            if c:
                malos[str(p.relative_to(R))] = c[:3]
    assert not malos, malos


def test_la_guia_de_la_demo_trae_la_ruta_del_arranque_bien_escrita() -> None:
    guia = R / "docs/ep3/pagina_guia_demo.md"
    if not guia.exists():
        pytest.skip("no hay guía de demo generada")
    t = guia.read_text(encoding="utf-8")
    assert "scripts" + chr(92) + "ep3" + chr(92) + "arrancar_app.bat" in t and CAMPANA not in t


def test_el_informe_no_tiene_comillas_sueltas_ni_barras_sin_escapar_en_sus_tablas() -> None:
    informe = R / "docs/ep3/informe_tecnico_EP3.md"
    if not informe.exists():
        pytest.skip("no hay informe generado")
    t = informe.read_text(encoding="utf-8")
    assert not re.search(r'^"\d+\. ', t, flags=re.M), "una línea numerada empieza con una comilla suelta"
    assert not [l for l in t.splitlines() if l.startswith("|") and "(|azimut|" in l]            # las barras sin escapar rompen la tabla de §8
    assert re.search(r"^12\. \*\*La página\*\*", t, flags=re.M)
    assert "azimut absoluto ≤ 120°" in t


def test_el_generador_revisa_sus_propios_documentos() -> None:
    fuente = (R / "scripts/ep3/generar_docs_ep3.py").read_text(encoding="utf-8")
    assert "revisar_carpeta(DOC)" in fuente and "SystemExit" in fuente
