"""F37: «Segmentos puntuados en esta sesión» en el Resumen y el script que fabrica el hueco de cámara simulado para la demostración en vivo.

Escribe solo en ``tmp_path``. El Resumen congelado no puede cambiar: sin segmentos puntuados no hay bloque, y con ellos todo lo anterior queda igual.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tests.ep3.test_app import ir_a
from tests.ep3.test_pagina_f24 import _abrir, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))
sys.path.insert(0, str(R / "src"))
from waymo_evaluacion.ep3 import puntuar as P  # noqa: E402


def _vista(origen: str = "archivo", segmento: str = "911012534050", con_asoc: bool = True, celdas: int = 1, positivos: int = 30, cajas: int = 120) -> P.Vista:
    lista_a = pd.DataFrame({"camara": ["3 (frontal der.)"] * celdas})
    return P.Vista(origen, segmento, 1, lista_a, pd.DataFrame(), pd.DataFrame(), {"positivos_total": positivos} if con_asoc else {}, [], cajas, 5 if con_asoc else 0, con_asoc, ("a.parquet", None))


# ------------------------------------------------------------------------------------------------------------ lógica pura
def test_el_registro_guarda_cifras_pone_lo_nuevo_primero_y_reemplaza_el_mismo_segmento() -> None:
    estado: dict = {}
    P.registrar_en_sesion(estado, _vista(segmento="111111111111", celdas=0, positivos=12), "10:01")
    P.registrar_en_sesion(estado, _vista(segmento="222222222222", celdas=1, positivos=60), "10:02")
    assert [f["segmento"] for f in estado[P.CLAVE_SESION]] == ["222222222222", "111111111111"]
    P.registrar_en_sesion(estado, _vista(segmento="111111111111", celdas=2, positivos=24), "10:03")
    filas = estado[P.CLAVE_SESION]
    assert [f["segmento"] for f in filas] == ["111111111111", "222222222222"] and len(filas) == 2                    # una fila por segmento: se reemplaza y queda arriba
    assert filas[0]["celdas"] == 2 and filas[0]["cajas"] == 120 and filas[0]["sin_pareja"] == pytest.approx(0.2) and filas[0]["hora"] == "10:03"
    assert not any(hasattr(v, "shape") for f in filas for v in f.values())                                         # solo números y texto: ni archivos ni tablas


def test_el_ejemplo_de_desarrollo_no_se_registra_y_sin_archivo_2_las_cifras_de_pareja_son_guion() -> None:
    estado: dict = {}
    P.registrar_en_sesion(estado, _vista(origen="ejemplo"), "10:00")
    assert P.CLAVE_SESION not in estado
    P.registrar_en_sesion(estado, _vista(con_asoc=False), "10:05")
    t = P.tabla_sesion(estado[P.CLAVE_SESION])
    assert t.filas[0][0] == "…534050" and t.filas[0][1] == "—" and t.filas[0][3] == "—" and t.filas[0][2] == "120" and t.filas[0][4] == "10:05"
    assert [c.encabezado for c in t.columnas] == ["Segmento", "Celdas marcadas", "Cajas", "Sin pareja", "Hora"]


def test_puntuar_no_escribe_a_disco_con_el_registro_nuevo() -> None:
    codigo = (R / "src/waymo_evaluacion/ep3/puntuar.py").read_text(encoding="utf-8")
    assert not re.search(r"open\(|write_bytes|write_text|to_parquet\(|to_csv\(\s*[\"']|tempfile|st\.cache|pickle", codigo)


# ------------------------------------------------------------------------------------------------------------ Resumen
def test_el_resumen_no_cambia_sin_segmentos_y_con_ellos_agrega_solo_el_bloque_al_final(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Resumen")
    antes = [m.value for m in at.markdown] + [c.value for c in at.caption]
    assert not any(P.SESION_TITULO in x for x in antes) and "rs_sesion" not in " ".join(antes)
    at.session_state[P.CLAVE_SESION] = [{"segmento": "911012534050", "etiqueta": "Segmento …534050", "celdas": 1, "cajas": 120, "sin_pareja": 0.25, "hora": "10:02"}]
    at.run()
    ir_a(at, "Resumen")
    assert not at.exception, at.exception
    despues = [m.value for m in at.markdown] + [c.value for c in at.caption]
    nuevos = [x for x in despues if x not in antes]
    assert len(despues) > len(antes) and all(x in despues for x in antes)                                         # todo lo anterior sigue, igual
    unido = " ".join(nuevos)
    assert P.SESION_TITULO in unido and "…534050" in unido and "10:02" in unido and "25,0" in unido
    assert "No forman parte de las cifras congeladas (" in unido and "segmentos de desarrollo)." in unido
    assert not re.search(r"en (la )?muestra|Validación externa pendiente", unido)                                  # el Resumen sigue limpio de esas divulgaciones (F28)
    assert antes == despues[:len(antes)] or all(a in despues for a in antes)


def test_usar_el_ejemplo_no_agrega_nada_a_la_sesion(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    boton = [b for b in at.button if b.label == P.BOTON_EJEMPLO]
    if not boton:
        pytest.skip("la fixture no trae datos para el ejemplo")
    boton[0].click().run()
    assert not at.exception and P.CLAVE_SESION not in at.session_state


# ------------------------------------------------------------------------------------------------------------ crear_demo_hueco.py
def _crear():
    spec = importlib.util.spec_from_file_location("crear_demo_hueco", R / "scripts/crear_demo_hueco.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _tablas(seg: str = "123456789012_1_000_2_000") -> tuple[pd.DataFrame, pd.DataFrame]:
    n = 40
    lidar = pd.DataFrame({"key.segment_context_name": seg, "key.frame_timestamp_micros": np.arange(n), "key.laser_object_id": [f"o{i}" for i in range(n)]})
    filas = [(seg, 1 + k, i, f"o{i}") for i in range(n) for k in range(3)]
    asoc = pd.DataFrame(filas, columns=["key.segment_context_name", "key.camera_name", "key.frame_timestamp_micros", "key.laser_object_id"])
    asoc.index = np.tile(np.arange(n), 3)[:len(asoc)]                                                              # índice NO único, como el de algunos parquet crudos
    return lidar, asoc


def test_quitar_camara_solo_borra_filas_de_esa_camara_aun_con_indice_repetido() -> None:
    _, asoc = _tablas()
    sal = _crear().quitar_camara(asoc, 3, 0.9, 7)
    por = sal["key.camera_name"].value_counts().to_dict()
    assert por[1] == 40 and por[2] == 40 and por[3] == 4                                                           # 40 - round(40 * 0,9)
    assert _crear().quitar_camara(asoc, 3, 0.9, 7).equals(_crear().quitar_camara(asoc, 3, 0.9, 7))               # misma semilla, mismo resultado


def test_el_script_copia_el_lidar_box_byte_a_byte_y_rotula_el_archivo_como_simulado(tmp_path: Path) -> None:
    lidar, asoc = _tablas()
    ent = tmp_path / "ent"
    ent.mkdir()
    lidar.to_parquet(ent / "lidar_box.parquet", index=False)
    asoc.to_parquet(ent / "asoc.parquet")
    salida = tmp_path / "C"
    assert _crear().main(["--lidar-box", str(ent / "lidar_box.parquet"), "--asociacion", str(ent / "asoc.parquet"), "--camara", "3", "--fraccion", "0.9", "--salida", str(salida)]) == 0
    assert (salida / "lidar_box.parquet").read_bytes() == (ent / "lidar_box.parquet").read_bytes()
    archivos = sorted(p.name for p in salida.iterdir())
    assert archivos == ["LEEME_SIMULADO.txt", "camera_to_lidar_box_association__SIMULADO_hueco_cam3.parquet", "lidar_box.parquet"]
    assert "ARCHIVO MODIFICADO A PROPOSITO" in (salida / "LEEME_SIMULADO.txt").read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------------------------------ el ejemplo con su celda marcada
from tests.ep3.test_pagina_f21 import HAY_REAL, _abrir_real  # noqa: E402

MODELOS = R / "data/06_models_ep3"


@pytest.mark.skipif(not (HAY_REAL and (MODELOS / "modelo_final_v3.joblib").exists()), reason="faltan los datos de la página o la solución congelada")
def test_el_ejemplo_trae_la_celda_marcada_de_desarrollo_con_las_cifras_ya_calculadas() -> None:
    from waymo_evaluacion.ep3.app_logica import cargar_datos, ejemplo_lidar_box
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos, puntuar_segmento

    D = cargar_datos(R / "data/09_app_ep3")
    seg = str(D["lista_A"]["segmento"].iloc[0])
    sin = puntuar_segmento(ejemplo_lidar_box(D["cajas"], seg), None, cargar_artefactos(MODELOS))
    con = P.completar_ejemplo(sin, D["cajas"], D["lista_A"], D["celdas"], seg)
    a = D["lista_A"][D["lista_A"]["segmento"].astype(str) == seg]
    assert len(con.lista_A) == len(a) >= 1 and con.lista_A["camara"].tolist() == a["camara"].tolist()
    assert con.resumen["cajas_en_celdas_con_hueco"] == int(a["cajas_afectadas_poblacion_principal"].sum())          # 268 en la cámara 5 del segmento de ejemplo
    assert con.resumen["positivos_en_celdas_con_hueco"] == int(a["positivos_afectados"].sum())
    assert con.resumen["tiene_asociacion"] is True and con.resumen["cajas_en_lista_B"] == len(sin.cajas) - con.resumen["cajas_en_celdas_con_hueco"]
    assert not any(x.lower().startswith("sin archivo de asociación") for x in con.advertencias)
    assert not con.lista_B["en_hueco"].any() and con.lista_B["posicion_en_cola"].tolist() == list(range(1, len(con.lista_B) + 1))
    assert sin.resumen["tiene_asociacion"] is False                                                                   # puntuar_segmento no cambió: el ejemplo solo se completa en la página


def test_completar_ejemplo_no_cambia_nada_si_falta_el_segmento_o_las_tablas() -> None:
    from types import SimpleNamespace

    res = SimpleNamespace(cajas=pd.DataFrame({"seg": ["a"]}), resumen={}, advertencias=[])
    assert P.completar_ejemplo(res, None, None, None, "a") is res
    assert P.completar_ejemplo(res, pd.DataFrame({"seg": ["b"], "en_hueco": [False], "sin_camara": [0]}), pd.DataFrame(), pd.DataFrame({"seg": ["b"]}), "a") is res


@pytest.mark.skipif(not (HAY_REAL and (MODELOS / "modelo_final_v3.joblib").exists()), reason="faltan los datos de la página o la solución congelada")
def test_la_pagina_muestra_la_celda_marcada_del_ejemplo_y_no_lo_registra_en_la_sesion(monkeypatch: pytest.MonkeyPatch) -> None:
    at = _abrir_real(monkeypatch, "Puntuar datos nuevos")
    next(b for b in at.button if b.label == P.BOTON_EJEMPLO).click().run()
    assert not at.exception, at.exception
    v = at.session_state["_pt_vista"]
    assert v.tiene_asociacion and len(v.lista_A) >= 1 and v.n_celdas == 5
    texto = " ".join(m.value for m in at.markdown)
    assert "de 5" in texto and "falta el archivo 2" not in texto and "No hay celdas marcadas" not in texto
    assert "ya calculadas para este segmento" in texto and P.CLAVE_SESION not in at.session_state
