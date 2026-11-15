"""Pruebas de la lógica de la página y prueba de humo con streamlit.testing.v1.AppTest (datos sintéticos en tmp_path)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from waymo_evaluacion.ep3.app_logica import (
    AVISO_EN_MUESTRA, PERFILES, cargar_datos, cargar_no_supervisado, curvas_a_mostrar, info_tipo_de_caso, tipo_de_caso, cola_segmento, curva_dependencia, horas_revision, matriz_calor, ocultar_identificadores, percentil_en_cola, recall_en_presupuesto,
)
from waymo_evaluacion.ep3.congelado import CalibradorPlatt, PuntuadorRegla
from waymo_evaluacion.ep3.detector_huecos import ParametrosDetector
from waymo_evaluacion.ep3.inferencia import V16, Artefactos

R = Path(__file__).resolve().parents[2]


def _datos_sinteticos(carpeta: Path) -> None:
    rng = np.random.default_rng(0)
    n = 600
    seg = np.repeat(["aaaaaaaaaaaa", "bbbbbbbbbbbb", "cccccccccccc"], n // 3)
    pts = rng.integers(3, 500, n)
    y = (rng.random(n) < 1 / (1 + pts / 40)).astype(int)
    cajas = pd.DataFrame({"seg": seg, "grupo": "train", "ubicacion": "location_sf", "momento": "Day",
                          "key.frame_timestamp_micros": np.arange(n), "key.laser_object_id": [f"id{i}" for i in range(n)]})
    for c in V16:
        cajas[c] = rng.uniform(1, 10, n)
    cajas["num_lidar_points"], cajas["num_top_lidar_points"] = pts, pts
    cajas["sin_camara"], cajas["score"] = y, -pts.astype(float)
    cajas["prob_cal"], cajas["en_hueco"] = 0.3, False
    cajas["tipo_caso"] = np.where(cajas["seg"] == "aaaaaaaaaaaa", "cercanos y densos", "lejanos y poco densos")
    carpeta.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"k": 2, "cluster": [0, 1], "cajas": [300, 300], "tasa_sin_camara": [0.09, 0.32], "ic_lo": [0.04, 0.25], "ic_hi": [0.15, 0.38], "tipo_de_caso": ["cercanos y densos", "lejanos y poco densos"]}).to_csv(carpeta / "clusters.csv", index=False)
    cajas.loc[:20, "en_hueco"] = True
    carpeta.mkdir(parents=True, exist_ok=True)
    cajas.to_parquet(carpeta / "cajas_oof.parquet", index=False)
    celdas = pd.DataFrame({"seg": ["aaaaaaaaaaaa", "bbbbbbbbbbbb"], "grupo": ["train", "test"], "ubicacion": "location_sf", "momento": "Day", "cajas": 200})
    for c in range(1, 6):
        celdas[f"tasa_c{c}"], celdas[f"n_rango_c{c}"], celdas[f"hueco_c{c}"] = 0.9, 150, False
    celdas.loc[0, "hueco_c3"], celdas.loc[0, "tasa_c3"] = True, 0.0
    celdas["algun_hueco"] = celdas[[f"hueco_c{c}" for c in range(1, 6)]].any(axis=1)
    celdas.to_csv(carpeta / "celdas.csv", index=False)
    pd.DataFrame([{"segmento": "aaaaaaaaaaaa", "camara": "3 (frontal der.)", "tasa": 0.0, "umbral": 0.2, "cajas_en_rango": 150}]).to_csv(carpeta / "lista_A.csv", index=False)
    g = np.linspace(0.01, 1, 100)
    base = pd.DataFrame({"solucion": "sol", "presupuesto": g, "recall": np.sqrt(g), "lo": np.sqrt(g) - 0.05, "hi": np.minimum(np.sqrt(g) + 0.05, 1)})
    ref = base.assign(solucion="XGB (referencia), un paso (A)", recall=lambda d: d["recall"] * 0.95)
    pd.concat([base, ref], ignore_index=True).to_csv(carpeta / "curva_cola.csv", index=False)
    (carpeta / "kpis.json").write_text(json.dumps({"nombre_curva": "sol", "solucion_final": "regla de prueba",
                                                   "tarjetas": [{"titulo": "AUC", "valor": "0,80", "ic": "IC 0,7 a 0,9", "fuente": "prueba"}]}), encoding="utf-8")
    (carpeta / "evidencia").mkdir(exist_ok=True)
    pd.DataFrame({"a": [1]}).to_csv(carpeta / "evidencia" / "ie9__tabla_de_prueba.csv", index=False)


def _modelos_sinteticos(carpeta: Path) -> None:
    lr = LogisticRegression().fit(np.array([[-1.0], [1.0], [-0.5], [0.5]]), [0, 1, 0, 1])
    Artefactos(PuntuadorRegla("num_top_lidar_points"), CalibradorPlatt(lr, "identidad"), {"A": -50.0, "B": -20.0},
               ParametrosDetector(rangos={1: (-30.0, 30.0)}, medianas_ref={"c1": 0.9})).guardar(carpeta)
    import joblib
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    cols = ["distancia_m", "azimut_abs_deg", "log_puntos", "log_densidad", "log_volumen"]
    Xs = np.random.default_rng(1).normal(size=(200, 5))
    sc = StandardScaler().fit(Xs)
    joblib.dump({"scaler": sc, "columnas": cols, "k_elegido": 2, "kmeans_k2": KMeans(2, n_init=3, random_state=42).fit(sc.transform(Xs))}, carpeta / "no_supervisado_v3.joblib")


def test_cargar_datos_y_faltantes(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        cargar_datos(tmp_path)
    _datos_sinteticos(tmp_path)
    d = cargar_datos(tmp_path)
    assert set(d) == {"cajas", "celdas", "lista_A", "curva", "kpis", "clusters", "evidencia"} and "ie9__tabla_de_prueba" in d["evidencia"]


def test_logica_cola_recall_y_horas(tmp_path: Path) -> None:
    _datos_sinteticos(tmp_path)
    d = cargar_datos(tmp_path)
    top, info = cola_segmento(d["cajas"], "aaaaaaaaaaaa", 0.2)
    assert info["cajas_a_revisar"] == len(top) == int(np.ceil(0.2 * info["cajas_cola_total"]))
    assert top["score"].is_monotonic_decreasing and not top["en_hueco"].any()
    assert info["recall_proceso"] >= info["positivos_en_cola"] / max(info["positivos_total"], 1)
    _, todos = cola_segmento(d["cajas"], "Todos", 1.0)
    assert todos["recall_proceso"] == pytest.approx(1.0)
    r = recall_en_presupuesto(d["curva"], "sol", 0.25)
    assert r["recall"] == pytest.approx(0.5, abs=0.02) and r["lo"] < r["recall"] < r["hi"]
    with pytest.raises(KeyError):
        recall_en_presupuesto(d["curva"], "no existe", 0.5)
    assert horas_revision(180, 20) == pytest.approx(1.0)


def test_modo_presentacion_oculta_identificadores(tmp_path: Path) -> None:
    _datos_sinteticos(tmp_path)
    c = cargar_datos(tmp_path)["cajas"].head(3)
    assert "key.laser_object_id" in ocultar_identificadores(c, False).columns
    oculto = ocultar_identificadores(c, True)
    assert "key.laser_object_id" not in oculto.columns and "key.frame_timestamp_micros" not in oculto.columns


def test_matriz_calor_y_percentil(tmp_path: Path) -> None:
    _datos_sinteticos(tmp_path)
    d = cargar_datos(tmp_path)
    m = matriz_calor(d["celdas"])
    assert len(m) == 10 and int(m["hueco"].sum()) == 1
    assert percentil_en_cola(d["cajas"]["score"].max() + 1, d["cajas"]) == 0.0
    dep = curva_dependencia(PuntuadorRegla("num_top_lidar_points"), d["cajas"][V16].median().to_frame().T, "num_top_lidar_points", np.array([10.0, 100.0]))
    assert dep["score"].tolist() == [-10.0, -100.0]
    assert len(PERFILES) == 3


@pytest.mark.parametrize("seccion", ["Inicio", "Auditoría de cámaras", "Cola de revisión", "Explica una caja", "Evidencia", "Ética y límites", "Puntuar datos nuevos", "Ayuda y glosario"])
def test_app_humo_cada_seccion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, seccion: str) -> None:
    at_mod = pytest.importorskip("streamlit.testing.v1")
    _datos_sinteticos(tmp_path / "datos")
    _modelos_sinteticos(tmp_path / "modelos")
    monkeypatch.setenv("WAYMO_APP_DATA", str(tmp_path / "datos"))
    monkeypatch.setenv("WAYMO_APP_MODELOS", str(tmp_path / "modelos"))
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=60).run()
    assert not at.exception, at.exception
    at.sidebar.radio[0].set_value(seccion).run()
    assert not at.exception, at.exception
    at.sidebar.toggle[0].set_value(True).run()                       # modo presentacion
    assert not at.exception, at.exception
    assert at.title[0].value == seccion
    if seccion in ("Inicio", "Cola de revisión"):          # aviso "en muestra" visible (no en un tooltip)
        at.sidebar.toggle[0].set_value(False).run()
        assert any("En muestra" in w.value for w in at.warning)
        assert any("2 celdas cámara x segmento" in m.value for m in at.markdown)          # texto completo, visible en el expander «¿Qué significa?»
    if seccion == "Cola de revisión":
        assert any(sb.label == "Modelo de referencia" for sb in at.selectbox)


def test_app_sin_datos_muestra_error_claro(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at_mod = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.setenv("WAYMO_APP_DATA", str(tmp_path / "vacio"))
    at = at_mod.AppTest.from_file(str(R / "app" / "app.py"), default_timeout=60).run()
    assert not at.exception and any("No encuentro los datos" in e.value for e in at.error)


def test_tipo_de_caso_curvas_de_referencia_y_aviso(tmp_path: Path) -> None:
    _datos_sinteticos(tmp_path / "d")
    _modelos_sinteticos(tmp_path / "m")
    d = cargar_datos(tmp_path / "d")
    ns = cargar_no_supervisado(tmp_path / "m")
    assert cargar_no_supervisado(tmp_path / "no_existe") is None
    fila = d["cajas"][V16].median().to_frame().T
    c = tipo_de_caso(fila, ns)
    assert c in (0, 1)
    inf = info_tipo_de_caso(c, d["clusters"])
    assert inf["tipo_de_caso"] in ("cercanos y densos", "lejanos y poco densos") and 0 < inf["tasa"] < 1
    assert info_tipo_de_caso(99, d["clusters"])["tipo_de_caso"] == "sin información"
    assert set(curvas_a_mostrar(d["curva"], "Ninguno")["solucion"]) == {"sol"}
    assert set(curvas_a_mostrar(d["curva"], "XGB")["solucion"]) == {"sol", "XGB (referencia), un paso (A)"}
    for frase in ("41 segmentos", "mismos datos", "post hoc, no pre-declarado", "sin validación con datos nuevos", "2 celdas cámara x segmento", "donde se descubrió el hueco"):
        assert frase in AVISO_EN_MUESTRA
