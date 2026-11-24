"""F39: flujo de «Puntuar datos nuevos» con los dos archivos: cargadores siempre a la vista, botón «Puntuar segmento» (deshabilitado sin el archivo 1), línea de ayuda según los archivos, resultado que se oculta
cuando cambian los archivos, paso 2 «omitido» sin archivo 2 y mensaje de segmentos distintos con los dos ids completos. Escribe solo en ``tmp_path``; no ejecuta ningún generador.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import pytest

from tests.ep3.test_app import ir_a
from tests.ep3.test_pagina_f24 import _abrir, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)
from tests.ep3.test_pagina_f37 import _vista

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))
sys.path.insert(0, str(R / "src"))
from waymo_evaluacion.ep3 import puntuar as P  # noqa: E402


# ------------------------------------------------------------------------------------------------------------ textos y lógica pura
def test_la_linea_de_ayuda_cambia_segun_los_archivos() -> None:
    assert P.ayuda_flujo(False, False) == "Agregue el archivo 1 para poder puntuar." and P.ayuda_flujo(False, True) == P.AYUDA_SIN_ARCHIVO_1
    assert P.ayuda_flujo(True, False) == "Todavía no agregó el archivo 2: se puntuará sin buscar huecos de cámara."
    assert P.ayuda_flujo(True, True) == "Listo para puntuar con búsqueda de huecos de cámara."
    assert P.AVISO_CAMBIARON == "Cambiaron los archivos: pulse Puntuar segmento para actualizar el resultado." and P.BOTON_PUNTUAR == "Puntuar segmento"


def test_la_firma_cambia_con_el_nombre_el_tamano_o_el_contenido() -> None:
    a = P.firma_archivo("lidar_box.parquet", b"abc")
    assert a == P.firma_archivo("lidar_box.parquet", b"abc") and a[1] == 3
    assert a != P.firma_archivo("otro.parquet", b"abc") and a != P.firma_archivo("lidar_box.parquet", b"abd") and a != P.firma_archivo("lidar_box.parquet", b"abcd")


def test_el_paso_2_sale_omitido_sin_archivo_2_y_no_lleva_el_check_de_hecho() -> None:
    import estilos as E

    assert [p[3] for p in P.estado_pasos(True, False)] == ["hecho", "omitido", "activo"] and [p[3] for p in P.estado_pasos(True)] == ["hecho", "hecho", "activo"]
    assert [p[3] for p in P.estado_pasos(False)] == ["activo", "pendiente", "pendiente"]
    html = E.pasos_flujo(P.estado_pasos(True, False))
    paso2 = html.split('class="omitido"')[1].split("</div>")[0]
    assert "omitido: falta el archivo 2" in paso2 and "✓" not in paso2 and "–" in paso2 and html.count("✓") == 1          # solo el paso 1 lleva el check
    assert html.count('aria-current="step"') == 1
    assert E.pasos_flujo(P.estado_pasos(True, True)).count("✓") == 2                                                       # con archivo 2, los pasos 1 y 2 llevan check


def _tablas(seg1: str, seg2: str):
    llaves = {"key.frame_timestamp_micros": [1, 2], "key.laser_object_id": ["a", "b"]}
    lidar = pd.DataFrame({"[LiDARBoxComponent].key.segment_context_name": [seg1, seg1], **llaves})
    asoc = pd.DataFrame({"key.segment_context_name": [seg2, seg2], "key.camera_name": [1, 1], **llaves})
    return lidar, asoc


def test_segmentos_distintos_el_mensaje_trae_los_dos_ids_completos_uno_por_linea() -> None:
    a, b = "16229547658178627464_380_000_400_000", "10689101165701914459_2072_300_2092_300"
    msg = P.validar_correspondencia(*_tablas(a, b))
    assert msg.startswith("El archivo 2 no corresponde al archivo 1: ninguno de sus segmentos aparece en el archivo 1")
    lineas = msg.split("\n")
    assert f"Archivo 1: {a}" in lineas and f"Archivo 2: {b}" in lineas and lineas[-1] == "Revise que ambos sean del mismo segmento."
    assert "1 segmento y 1" not in msg
    assert P.validar_correspondencia(*_tablas(a, a)) is None


def test_con_muchos_segmentos_el_mensaje_dice_cuantos_faltan() -> None:
    assert P._ids({"a", "b", "c"}) == "a, b, c" and P._ids({"a", "b", "c", "d", "e"}) == "a, b, c y 2 más"


# ------------------------------------------------------------------------------------------------------------ la página
def _botones(at, rotulo: str):
    return [b for b in at.button if b.label == rotulo]


def test_el_boton_puntuar_esta_deshabilitado_sin_archivo_1_y_los_dos_cargadores_estan_a_la_vista(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    assert not at.exception, at.exception
    boton = _botones(at, "Puntuar segmento")
    assert len(boton) == 1 and boton[0].disabled is True
    assert len(at.get("file_uploader")) == 2 and [e.proto.expanded for e in at.expander if e.label == "Archivos del segmento"] == [True]       # antes de puntuar, a la vista y abiertos
    html = " ".join(m.value for m in at.markdown)
    assert "Agregue el archivo 1 para poder puntuar." in html and "obligatorio" in html and "opcional" in html


def test_un_resultado_de_otros_archivos_no_se_muestra_y_la_pagina_pide_volver_a_puntuar(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    vieja = _vista(segmento="911012534050")
    vieja.firma = (("lidar_box.parquet", 10, "a" * 64), None)                  # se puntuó con unos archivos; ahora no hay ninguno cargado
    at.session_state["_pt_vista"] = vieja
    at.run()
    ir_a(at, "Puntuar datos nuevos")
    assert not at.exception, at.exception
    html = re.sub(r"<style>.*?</style>", "", " ".join(m.value for m in at.markdown), flags=re.S)                 # sin el CSS, que nombra las clases
    assert "Cambiaron los archivos: pulse Puntuar segmento para actualizar el resultado." in html
    assert 'class="aud-seg-t"' not in html and 'class="aud-kpis"' not in html and "Segmento …476024" not in html and "Celdas marcadas" not in html          # el resultado viejo no está en pantalla (ni sus tarjetas)
    assert [e.proto.expanded for e in at.expander if e.label == "Archivos del segmento"] == [False]                  # el bloque de archivos sigue plegado (ya hubo un resultado); el botón «Puntuar segmento» queda a la vista
    assert _botones(at, "Puntuar segmento") != []


def test_el_ejemplo_se_ve_aunque_no_haya_archivos_y_sigue_sin_registrarse_en_la_sesion(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    boton = _botones(at, "Usar un segmento de desarrollo de ejemplo")
    if not boton:
        pytest.skip("la fixture no trae datos para el ejemplo")
    boton[0].click().run()
    assert not at.exception, at.exception
    html = " ".join(m.value for m in at.markdown)
    assert "ejemplo de desarrollo" in html and "Cambiaron los archivos" not in html and P.CLAVE_SESION not in at.session_state
    assert [e.proto.expanded for e in at.expander if e.label == "Archivos del segmento"] == [False]
    assert _botones(at, "Puntuar segmento") == []                                                          # con un resultado fresco no se ofrece puntuar de nuevo
    _botones(at, "Cargar otro segmento")[0].click().run()
    assert not at.exception and "_pt_vista" not in at.session_state
    assert _botones(at, "Puntuar segmento")[0].disabled is True and len(at.get("file_uploader")) == 2


def test_la_pagina_ya_no_puntua_al_subir_un_archivo_el_codigo_solo_puntua_con_el_boton() -> None:
    fuente = (R / "app/secciones.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def puntuar("):fuente.index("Ética y límites\ndef etica(")]
    zona = fuente[fuente.index("def _zona_puntuar("):fuente.index("def _resultado(")]
    assert "_puntuar_archivos(" in zona and "if pulsado and f1 is not None" in zona                      # el cálculo de archivos vive solo bajo el botón
    assert "_puntuar_archivos(" not in cuerpo and "_calcular(ctx, art, lidar" not in cuerpo
