"""F35: Puntuar datos nuevos rediseñada (tres pasos, entradas con el archivo 1 como acción principal, estado vacío corto, resultado en la misma página, errores claros en español, escala).

Cubre la lógica pura de ``puntuar.py`` (validación de archivos, pasos, tarjetas, tablas, CSV), la página con los datos de prueba y con los reales, y la prueba de escala con un parquet sintético de unas 100.000 cajas.
Todos los archivos sintéticos se crean en ``tmp_path``; nada se deja en el repositorio.
"""
from __future__ import annotations

import builtins
import inspect
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tests.ep3.test_app import ir_a, textos
from tests.ep3.test_pagina_f21 import HAY_REAL, REAL, _abrir_real
from tests.ep3.test_pagina_f24 import _abrir, _sin_css, entorno  # noqa: F401  (``entorno`` es la fixture del módulo de F24)

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "app"))
MODELOS = R / "data/06_models_ep3"
HAY_MODELOS = (MODELOS / "modelo_final_v3.joblib").exists()


def _parquet(df: pd.DataFrame, ruta: Path) -> bytes:
    df.to_parquet(ruta)
    return ruta.read_bytes()


def _lidar_sintetico(n: int, semilla: int = 42, segmentos: int = 1) -> pd.DataFrame:
    """Un lidar_box mínimo con ``n`` cajas de peatones y ciclistas (columnas con el prefijo del componente, como el parquet de Waymo)."""
    rng = np.random.default_rng(semilla)
    pre = "[LiDARBoxComponent]."
    seg = np.array([f"{257766998801 + 1000 * i}_1000_000_1020_000" for i in range(segmentos)])[rng.integers(0, segmentos, n)]
    return pd.DataFrame({"key.segment_context_name": seg, "key.frame_timestamp_micros": rng.integers(10 ** 15, 10 ** 15 + 20 * 10 ** 6, n), "key.laser_object_id": [f"obj{int(x):09d}" for x in rng.integers(0, max(n // 8, 10), n)],
                         pre + "type": rng.choice([2, 4], n, p=[0.95, 0.05]), pre + "box.center.x": rng.uniform(2, 80, n), pre + "box.center.y": rng.uniform(-40, 40, n), pre + "box.center.z": rng.uniform(0, 2, n),
                         pre + "box.size.x": rng.uniform(0.4, 1.0, n), pre + "box.size.y": rng.uniform(0.4, 1.0, n), pre + "box.size.z": rng.uniform(1.4, 2.0, n), pre + "box.heading": rng.uniform(-3.1, 3.1, n),
                         pre + "num_lidar_points_in_box": rng.integers(0, 400, n), pre + "num_top_lidar_points_in_box": rng.integers(0, 300, n), pre + "speed.x": rng.uniform(0, 3, n), pre + "speed.y": rng.uniform(0, 1, n)})


def _asoc_sintetica(lidar: pd.DataFrame, fraccion: float = 0.9, semilla: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    k = lidar.iloc[: int(len(lidar) * fraccion)][["key.segment_context_name", "key.frame_timestamp_micros", "key.laser_object_id"]].copy()
    k["key.camera_name"] = rng.integers(1, 6, len(k))
    return k


# ------------------------------------------------------------------------------------------------------------ errores claros (punto 8)
def test_un_archivo_que_no_es_parquet_da_un_mensaje_claro_y_no_un_traceback() -> None:
    from waymo_evaluacion.ep3 import puntuar as P

    for basura in (b"esto no es un parquet", b"PAR1" + b"\x00" * 20, b"\xff\xfe\x00"):
        df, msg = P.leer_parquet(basura, "datos.parquet")
        assert df is None and msg == "El archivo «datos.parquet» no es un parquet válido o está dañado. Se espera un archivo en formato parquet."


def test_un_archivo_vacio_o_sin_filas_da_su_propio_mensaje(tmp_path: Path) -> None:
    from waymo_evaluacion.ep3 import puntuar as P

    assert P.leer_parquet(b"", "v.parquet") == (None, "El archivo «v.parquet» está vacío (0 bytes).")
    sin_filas = _parquet(_lidar_sintetico(5).iloc[0:0], tmp_path / "sin_filas.parquet")
    df, msg = P.leer_parquet(sin_filas, "sin_filas.parquet")
    assert df is None and msg == "El archivo «sin_filas.parquet» no tiene filas: está vacío."
    ok, msg = P.leer_parquet(_parquet(_lidar_sintetico(5), tmp_path / "ok.parquet"), "ok.parquet")
    assert msg is None and len(ok) == 5


def test_las_columnas_que_faltan_se_dicen_todas() -> None:
    from waymo_evaluacion.ep3.app_logica import validar_asociacion, validar_lidar_box

    msg = validar_lidar_box(pd.DataFrame({"a": [1]}))
    assert msg and "faltan las columnas" in msg and "y otras" not in msg
    for c in ("box.center.x", "num_lidar_points_in_box", "num_top_lidar_points_in_box", "box.heading", "key.segment_context_name", "key.frame_timestamp_micros", "key.laser_object_id", "box.size.x", "box.center.y"):
        assert f"«{c}»" in msg, c                                                                       # se dicen todas, no solo las primeras
    asoc = validar_asociacion(pd.DataFrame({"key.camera_name": [1]}))
    assert asoc and all(f"«{c}»" in asoc for c in ("key.segment_context_name", "key.frame_timestamp_micros", "key.laser_object_id")) and "key.camera_name" not in asoc
    assert validar_lidar_box(_lidar_sintetico(3)) is None


def test_un_archivo_de_mas_de_500_mb_da_un_mensaje_claro() -> None:
    from waymo_evaluacion.ep3 import puntuar as P

    assert P.validar_tamano("a.parquet", 500 * 1024 * 1024) is None
    msg = P.validar_tamano("grande.parquet", 600 * 1024 * 1024)
    assert msg == "El archivo «grande.parquet» pesa 600 MB y el máximo es 500 MB. Use un archivo más pequeño (un segmento a la vez)."


def test_un_archivo_2_que_no_corresponde_al_archivo_1_da_un_mensaje_claro() -> None:
    from waymo_evaluacion.ep3 import puntuar as P

    lidar = _lidar_sintetico(50, segmentos=1)
    otra = _asoc_sintetica(_lidar_sintetico(50, semilla=3, segmentos=2).assign(**{"key.segment_context_name": "999999999999_x"}))
    msg = P.validar_correspondencia(lidar, otra)
    assert msg and msg.startswith("El archivo 2 no corresponde al archivo 1: ninguno de sus segmentos aparece en el archivo 1")
    mismo_segmento = _asoc_sintetica(lidar).assign(**{"key.laser_object_id": "otro_objeto"})
    msg = P.validar_correspondencia(lidar, mismo_segmento)
    assert msg and "comparten segmento, pero ninguna caja del archivo 2 está en el archivo 1" in msg
    assert P.validar_correspondencia(lidar, _asoc_sintetica(lidar)) is None


# ------------------------------------------------------------------------------------------------------------ pasos, tarjetas y tablas
def test_los_pasos_marcan_el_actual_y_los_hechos() -> None:
    from waymo_evaluacion.ep3 import puntuar as P
    import estilos as E

    assert [p[3] for p in P.estado_pasos(False)] == ["activo", "pendiente", "pendiente"] and [p[3] for p in P.estado_pasos(True)] == ["hecho", "hecho", "activo"]
    html = E.pasos_flujo(P.estado_pasos(True))
    assert html.count('aria-current="step"') == 1 and "paso actual" in html and html.count("hecho") >= 2 and [p[1] for p in P.estado_pasos(False)] == ["Cargar el segmento", "Revisar celdas marcadas", "Revisar la cola"]


def _vista(con_asoc: bool, marcadas: int = 1, cajas: int = 120) -> "object":
    from waymo_evaluacion.ep3 import puntuar as P

    cola = pd.DataFrame({"posicion_en_cola": np.arange(1, cajas + 1), "caja": [f"ab{i:02d}-01" for i in range(cajas)], "camara": "3 (frontal der.)", "clase": ["Ciclista" if i == 0 else "Peatón" for i in range(cajas)],
                         "prob_calibrada": np.linspace(0.9, 0.1, cajas), "num_top_lidar_points": np.arange(cajas)})
    la = pd.DataFrame({"segmento": ["257766998801"] * marcadas, "camara": ["3 (frontal der.)"] * marcadas, "tasa": [0.0] * marcadas, "mediana_referencia": [0.9] * marcadas, "umbral": [0.2] * marcadas,
                       "cajas_en_rango": [300] * marcadas, "cajas_afectadas": [268] * marcadas})
    resumen = {"cajas_vru_poblacion_principal": cajas + 268, "cajas_en_celdas_con_hueco": 268 * marcadas, "cajas_en_lista_B": cajas, "celdas_con_hueco": marcadas, "tiene_asociacion": con_asoc, "umbral_A": -32.0, "umbral_B": -11.0}
    if con_asoc:
        resumen.update({"positivos_total": 200, "positivos_en_celdas_con_hueco": 227 * marcadas})
    return P.Vista("archivo", "257766998801", 1, la if con_asoc else la.iloc[0:0], cola, cola.assign(**{"key.frame_timestamp_micros": 1}), resumen, [], cajas + 268, 5 if con_asoc else 0, con_asoc)


def test_las_tarjetas_con_archivo_2_son_x_de_n_afectadas_y_sin_pareja() -> None:
    from waymo_evaluacion.ep3 import puntuar as P

    t = {x["clave"]: x for x in P.tarjetas(_vista(True))}
    assert (t["celdas"]["valor"], t["celdas"]["sufijo"], t["afectadas"]["valor"], t["sin_pareja"]["valor"]) == ("1", "de 5", "268", "227") and "84,7" in t["sin_pareja"]["nota"].replace("\xa0", " ")
    t2 = {x["clave"]: x for x in P.tarjetas(_vista(True, marcadas=2))}
    assert t2["celdas"]["valor"] == "2" and t2["afectadas"]["valor"] == "536" and t2["sin_pareja"]["valor"] == "454"            # todo sale de la vista, nada fijo


def test_sin_archivo_2_las_tarjetas_dicen_que_no_se_buscaron_huecos() -> None:
    from waymo_evaluacion.ep3 import puntuar as P

    t = P.tarjetas(_vista(False))
    assert t[0]["valor"] == "—" and "falta el archivo 2" in t[0]["nota"] and [x["etiqueta"] for x in t[1:]] == ["Cajas puntuadas", "Cajas en la cola"] and P.tabla_celdas(_vista(False)) is None
    assert "no se buscaron" in P.TEXTO_CELDAS_NO_BUSCADAS.lower() and "no hay celdas marcadas ni cifras de cajas sin pareja" in P.ARCHIVO_2_AYUDA


def test_la_cola_formatea_solo_la_pagina_pedida_y_el_csv_es_la_lista_b_completa() -> None:
    from waymo_evaluacion.ep3 import puntuar as P
    from waymo_evaluacion.ep3.app_logica import CLASE_ADVERTENCIA
    from waymo_evaluacion.ep3.tablas_estandar import pagina, paginas

    v = _vista(True, cajas=1_000)
    t = P.tabla_cola(v)
    assert t.n_filas == 1_000 and paginas(t.n_filas, 50) == 20 and [c.encabezado for c in t.columnas] == ["Prioridad", "Caja", "Cámara", "Clase", "Prob. sin pareja", "Puntos sensor sup."]
    p1, p2 = pagina(t.filas, 1, 50), pagina(t.filas, 2, 50)
    assert len(p1) == len(p2) == 50 and p1[0][0] == "1" and p2[0][0] == "51" and p1[0][3] == CLASE_ADVERTENCIA and p1[1][3] == "Peatón"
    assert p1[0][4].replace("\xa0", " ") == "90,0 %" and p1[0][5] == "0"
    csv = pd.read_csv(pd.io.common.BytesIO(t.csv()))
    assert len(csv) == 1_000 and "key.frame_timestamp_micros" in csv.columns                                       # el CSV conserva todas las columnas de la Lista B


def test_el_zip_de_resultados_trae_las_dos_listas_con_el_contenido_de_siempre() -> None:
    import io
    import zipfile

    from waymo_evaluacion.ep3 import puntuar as P

    v = _vista(True)
    z = zipfile.ZipFile(io.BytesIO(P.zip_resultados(v)))
    assert sorted(z.namelist()) == ["lista_A_nueva.csv", "lista_B_nueva.csv"]
    assert z.read("lista_A_nueva.csv").decode("utf-8") == v.lista_A.to_csv(index=False) and z.read("lista_B_nueva.csv").decode("utf-8") == v.lista_B.to_csv(index=False)


def test_el_formato_de_los_archivos_lista_las_columnas_que_el_codigo_lee() -> None:
    from waymo_evaluacion.ep3 import inferencia, puntuar as P

    codigo = inspect.getsource(inferencia)
    nombres = [c.strip().split(" ")[0] for fila in P.COLUMNAS_ARCHIVO_1 + P.COLUMNAS_ARCHIVO_2 for c in fila[0].split(",")]
    for n in nombres:
        assert n in codigo or n == "type", n                                                                    # «type» se lee como el final «].type» del nombre con prefijo
    assert "].type" in codigo
    tabla = P.tabla_formato()
    assert tabla.n_filas == len(P.filas_formato()) == 8 and [c.encabezado for c in tabla.columnas] == ["Archivo", "Columnas", "Para qué sirve"]


# ------------------------------------------------------------------------------------------------------------ la página
def test_la_pagina_vacia_tiene_pasos_entradas_ejemplo_discreto_y_estado_vacio_corto(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    html = " ".join(m.value for m in at.markdown)
    t = _sin_css(textos(at))
    assert "Un segmento nuevo se puntúa con la solución congelada y se obtienen sus celdas marcadas y su cola de cajas." in t
    assert "Procesamiento local y en memoria" in t and "No se guarda nada" in t
    assert html.count('aria-current="step"') == 1 and "Cargar el segmento" in t and "paso actual" in t
    assert "Todavía no hay un segmento cargado" in t and "¿Solo desea ver cómo funciona?" in t
    assert "Sin el archivo 2" not in t and "sin este archivo se puntúan y ordenan igual todas las cajas, pero no hay celdas marcadas ni cifras de cajas sin pareja" in t
    assert [u.label for u in at.get("file_uploader")] == ["Archivo 1 (obligatorio): lidar_box", "Archivo 2 (opcional): camera_to_lidar_box_association"]


def test_la_etiqueta_cambia_con_el_entorno_para_no_decir_algo_falso(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    monkeypatch.setenv("EP3_ENTORNO", "servidor")
    t = _sin_css(textos(_abrir(entorno, monkeypatch, "Puntuar datos nuevos")))
    assert "Procesamiento en el servidor y en memoria" in t and "Procesamiento local y en memoria" not in t and "No se guardan los archivos" in t and "No se guarda nada" not in t


def test_con_el_ejemplo_el_resultado_sale_en_la_misma_pagina_y_cargar_otro_vuelve_al_vacio(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    next(b for b in at.button if b.label == "Usar un segmento de desarrollo de ejemplo").click().run()
    assert not at.exception
    html = " ".join(m.value for m in at.markdown)
    t = _sin_css(textos(at))
    assert "ejemplo de desarrollo" in html and "reconstruido desde las variables derivadas (no son datos crudos de Waymo)" in t and "Procesado en memoria con la solución congelada." in t
    assert html.count('aria-current="step"') == 1 and html.count("hecho") >= 2 and "Todavía no hay un segmento cargado" not in t
    assert [b.label for b in at.button][:2] == ["Cargar otro segmento", "Anterior"] or "Cargar otro segmento" in [b.label for b in at.button]
    assert len(at.get("file_uploader")) == 2 and "_pt_vista" in at.session_state                              # F39: con el resultado, los dos cargadores siguen (dentro del bloque plegable «Archivos del segmento»); vive solo en la memoria de la sesión
    assert [e.proto.expanded for e in at.expander if e.label == "Archivos del segmento"] == [False]
    ronda = at.session_state["pt_ronda"] if "pt_ronda" in at.session_state else 0
    next(b for b in at.button if b.label == "Cargar otro segmento").click().run()
    assert not at.exception and "_pt_vista" not in at.session_state and at.session_state["pt_ronda"] == ronda + 1
    t = _sin_css(textos(at))
    assert "Todavía no hay un segmento cargado" in t and len(at.get("file_uploader")) == 2 and not at.session_state["usar_ejemplo"] if "usar_ejemplo" in at.session_state else "Todavía no hay un segmento cargado" in t


@pytest.mark.skipif(not (HAY_REAL and HAY_MODELOS), reason="faltan los datos de la página o la solución congelada")
def test_regresion_con_el_segmento_de_ejemplo_las_celdas_y_la_cola_son_las_de_antes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Con el ejemplo, la Lista A y la Lista B que muestra y descarga la página son exactamente las de ``puntuar_segmento`` (la función de antes del rediseño), en el mismo orden."""
    import io
    import zipfile

    from waymo_evaluacion.ep3.app_logica import cargar_datos, ejemplo_lidar_box
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos, puntuar_segmento

    D = cargar_datos(REAL)
    seg = str(D["lista_A"]["segmento"].iloc[0])
    from waymo_evaluacion.ep3 import puntuar as P0

    esperado = P0.completar_ejemplo(puntuar_segmento(ejemplo_lidar_box(D["cajas"], seg), None, cargar_artefactos(MODELOS)), D["cajas"], D["lista_A"], D["celdas"], seg)     # F37: el ejemplo trae su celda marcada de desarrollo
    at = _abrir_real(monkeypatch, "Puntuar datos nuevos")
    next(b for b in at.button if b.label == "Usar un segmento de desarrollo de ejemplo").click().run()
    assert not at.exception
    v = at.session_state["_pt_vista"]
    pd.testing.assert_frame_equal(v.lista_B.reset_index(drop=True), esperado.lista_B.reset_index(drop=True))
    pd.testing.assert_frame_equal(v.lista_A.reset_index(drop=True), esperado.lista_A.reset_index(drop=True))
    assert v.resumen == esperado.resumen and v.advertencias == esperado.advertencias
    from waymo_evaluacion.ep3 import puntuar as P

    z = zipfile.ZipFile(io.BytesIO(P.zip_resultados(v)))
    assert z.read("lista_B_nueva.csv").decode("utf-8") == esperado.lista_B.to_csv(index=False) and z.read("lista_A_nueva.csv").decode("utf-8") == esperado.lista_A.to_csv(index=False)
    tabla = P.tabla_cola(v)
    assert tabla.n_filas == len(esperado.lista_B) and [f[0] for f in tabla.filas[0:5]] == ["1", "2", "3", "4", "5"]              # la cola se muestra en el mismo orden de la Lista B
    assert [f[4].replace("\xa0", " ") for f in tabla.filas[0:3]] == [F_pct(x) for x in esperado.lista_B["prob_calibrada"].iloc[0:3]]
    html = " ".join(m.value for m in at.markdown)
    assert f"Segmento …{seg[-6:]}" in html and f"segmento de desarrollo …{seg[-6:]}" in html                                     # el segmento de ejemplo es el de la app, no el de la maqueta
    assert any("Cajas afectadas" in m.value for m in at.markdown) and "Resumen del cálculo" in [e.label for e in at.expander]  # los elementos de antes se conservan


def F_pct(x: float) -> str:
    from waymo_evaluacion.ep3 import formato as F

    return F.menos(F.porcentaje(x, 1)).replace("\xa0", " ")


# ------------------------------------------------------------------------------------------------------------ nada se guarda
def test_la_pagina_de_puntuar_no_escribe_a_disco_ni_usa_cache(entorno: Path, monkeypatch: pytest.MonkeyPatch) -> None:   # noqa: F811
    """Respaldo de la etiqueta «No se guarda nada»: en el código no hay escrituras ni cachés persistentes, y durante un puntaje real no se abre ningún archivo para escribir."""
    fuentes = {p.name: p.read_text(encoding="utf-8") for p in (R / "app/secciones.py", R / "app/tablas.py", R / "src/waymo_evaluacion/ep3/puntuar.py")}
    for nombre, t in fuentes.items():
        assert not re.search(r"st\.cache|cache_data|cache_resource|lru_cache|shelve|pickle|joblib\.dump|\.to_parquet\(|tempfile|shutil|write_bytes|write_text", t), nombre
    escritos: list[str] = []
    abrir = builtins.open

    def espia(archivo, modo="r", *a, **k):  # noqa: ANN001
        if any(c in str(modo) for c in "wax+") and "scratchpad" not in str(archivo) and "pytest" not in str(archivo).lower():
            escritos.append(str(archivo))
        return abrir(archivo, modo, *a, **k)

    at = _abrir(entorno, monkeypatch, "Puntuar datos nuevos")
    monkeypatch.setattr(builtins, "open", espia)
    next(b for b in at.button if b.label == "Usar un segmento de desarrollo de ejemplo").click().run()
    assert not at.exception and not [e for e in escritos if "streamlit" not in e.lower()]                     # ningún archivo abierto para escribir durante el puntaje


def test_el_limite_de_subida_es_de_500_mb_tambien_al_lanzar_desde_la_raiz() -> None:
    """La página dice «hasta 500 MB»: las dos configuraciones (la de la raíz, que usa el lanzador, y la de ``app/``) deben poner ese límite."""
    for ruta in (R / ".streamlit/config.toml", R / "app/.streamlit/config.toml"):
        assert re.search(r"(?m)^maxUploadSize\s*=\s*500\s*$", ruta.read_text(encoding="utf-8")), ruta
    from waymo_evaluacion.ep3.puntuar import MAX_MB

    assert MAX_MB == 500


# ------------------------------------------------------------------------------------------------------------ escala (unas 100.000 cajas)
@pytest.mark.skipif(not HAY_MODELOS, reason="falta la solución congelada")
def test_con_100000_cajas_la_pagina_muestra_50_filas_por_vez_y_el_tiempo_es_razonable(tmp_path: Path) -> None:
    from waymo_evaluacion.ep3 import puntuar as P
    from waymo_evaluacion.ep3.app_logica import cargar_rangos, validar_lidar_box
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos, construir_variables, puntuar_segmento
    from waymo_evaluacion.ep3.tablas_estandar import pagina, paginas

    t0 = time.time()
    lidar = _lidar_sintetico(100_000, segmentos=3)
    lidar_bytes = _parquet(lidar, tmp_path / "grande.parquet")
    t_gen = time.time() - t0
    t0 = time.time()
    df, msg = P.leer_parquet(lidar_bytes, "grande.parquet")
    assert msg is None and len(df) == 100_000 and validar_lidar_box(df) is None
    t_leer = time.time() - t0
    art = cargar_artefactos(MODELOS)
    t0 = time.time()
    res = puntuar_segmento(df, None, art)
    t_puntuar = time.time() - t0
    t0 = time.time()
    az = construir_variables(df)[["segment_id", "key.frame_timestamp_micros", "key.laser_object_id", "az_signed"]]
    cola = P.preparar_cola_vista(res.lista_B, res.cajas, az, cargar_rangos(MODELOS))
    vista = P.Vista("archivo", str(res.cajas["seg"].iloc[0]), int(res.cajas["seg"].nunique()), res.lista_A, cola, res.lista_B, res.resumen, list(res.advertencias), len(res.cajas), 0, False)
    t = P.tabla_cola(vista)
    p1 = pagina(t.filas, 1, P.POR_PAGINA_COLA)
    t_tabla = time.time() - t0
    assert len(res.cajas) > 50_000 and t.n_filas == len(res.lista_B) and len(p1) == 50 and len(pagina(t.filas, paginas(t.n_filas, 50), 50)) <= 50
    assert [f[0] for f in p1[:3]] == ["1", "2", "3"] and all(f[2] != "" for f in p1)
    total = t_leer + t_puntuar + t_tabla
    assert total < 120, (t_leer, t_puntuar, t_tabla)                                                         # razonable para un segmento enorme; con un segmento real (≈ 2.000 cajas) son décimas de segundo
    (tmp_path / "tiempos.txt").write_text(f"generar={t_gen:.2f} leer={t_leer:.2f} puntuar={t_puntuar:.2f} tabla={t_tabla:.2f} cajas={len(res.cajas)}", encoding="utf-8")
