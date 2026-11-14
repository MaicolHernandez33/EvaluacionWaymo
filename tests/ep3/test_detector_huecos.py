"""Pruebas del detector de huecos por cámara (EP3).

Las unitarias usan datos sintéticos y escriben solo en ``tmp_path``. La de integración
lee los datos reales de EP2 (solo lectura) y se omite si faltan.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from waymo_evaluacion.ep3.detector_huecos import (
    ParametrosDetector,
    agregar_pares_camara,
    azimut_con_signo,
    calcular_medianas,
    calcular_rangos,
    detectar_huecos,
    marcar_cajas_en_hueco,
    resumen_celdas,
    tasa_por_celda,
)

R = Path(__file__).resolve().parents[2]
CAMARAS = [1, 2]


def _tablas_basicas() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cinco segmentos, cámara 1: dos con tasa 0 (uno con n=150 y otro con n=50)."""
    idx = pd.Index(["s1", "s2", "s3", "s4", "s5"], name="seg")
    tasa = pd.DataFrame({"c1": [0.0, 0.0, 0.7, 0.8, 0.9], "c2": [0.8] * 5}, index=idx)
    nrango = pd.DataFrame({"c1": [150, 50, 200, 200, 200], "c2": [200] * 5}, index=idx)
    return tasa, nrango


def test_azimut_con_signo() -> None:
    assert azimut_con_signo(1.0, 0.0) == pytest.approx(0.0)
    assert azimut_con_signo(0.0, 1.0) == pytest.approx(90.0)
    assert azimut_con_signo(-1.0, 0.0) == pytest.approx(180.0)
    assert azimut_con_signo(0.0, -1.0) == pytest.approx(-90.0)
    serie = azimut_con_signo(pd.Series([1.0, 0.0]), pd.Series([0.0, 1.0]))
    assert list(serie.round(6)) == [0.0, 90.0]


def test_rango_usa_solo_cajas_con_par_y_percentiles() -> None:
    az = np.arange(101, dtype=float)  # 0..100: p5 = 5 y p95 = 95
    cajas = pd.DataFrame({"az_signed": np.r_[az, [-170.0, 170.0]], "c1": np.r_[np.ones(101), [0, 0]]})
    assert calcular_rangos(cajas, [1]) == {1: (5.0, 95.0)}
    assert calcular_rangos(cajas, [1], p_inf=0, p_sup=100) == {1: (0.0, 100.0)}


def test_rango_sin_cajas_con_par_falla() -> None:
    cajas = pd.DataFrame({"az_signed": [1.0, 2.0], "c1": [0, 0]})
    with pytest.raises(ValueError):
        calcular_rangos(cajas, [1])


def test_hueco_con_tasa_cero_exige_n_minimo() -> None:
    tasa, nrango = _tablas_basicas()
    huecos = detectar_huecos(tasa, nrango)
    assert bool(huecos.loc["s1", "c1"]) is True       # tasa 0 y n = 150 >= 100
    assert bool(huecos.loc["s2", "c1"]) is False      # tasa 0 pero n = 50 < 100
    assert not huecos["c2"].any()
    assert bool(detectar_huecos(tasa, nrango, min_cajas=40).loc["s2", "c1"]) is True


def test_mediana_congelada_cambia_el_resultado() -> None:
    tasa, nrango = _tablas_basicas()
    recalculada = detectar_huecos(tasa, nrango)
    congelada_baja = detectar_huecos(tasa, nrango, medianas={"c1": 0.0, "c2": 0.8})
    congelada_alta = detectar_huecos(tasa, nrango, medianas={"c1": 0.95, "c2": 0.8})
    assert calcular_medianas(tasa)["c1"] == pytest.approx(0.7)
    assert list(recalculada["c1"]) == [True, False, False, False, False]
    assert not congelada_baja["c1"].any()             # umbral 0: nada es < 0
    assert list(congelada_alta["c1"]) == [True, False, False, False, False]
    assert not recalculada.equals(congelada_baja)
    # una mediana congelada alta marca un segmento que con la recalculada no se marcaba
    tasa2 = tasa.copy()
    tasa2.loc["s3", "c1"] = 0.2
    assert not bool(detectar_huecos(tasa2, nrango).loc["s3", "c1"])
    assert bool(detectar_huecos(tasa2, nrango, medianas={"c1": 0.95, "c2": 0.8}).loc["s3", "c1"])


def _cajas_sinteticas(tmp_path: Path) -> pd.DataFrame:
    """Tres segmentos de 300 cajas; en el segmento A la cámara 1 no tiene ningún par."""
    rng = np.random.default_rng(42)
    filas = []
    for letra, p1 in (("A", 0.0), ("B", 0.95), ("C", 0.95)):
        seg_id = f"{letra}" * 12 + "_0_000_20_000"
        n = 300
        az = rng.uniform(-50, 50, n)
        c1 = rng.random(n) < p1
        asoc = []
        for i in range(n):
            if c1[i]:
                asoc.append((i, 1, i))
            else:
                asoc.append((i, 2, i))                # sin par en la 1 pero sí en la 2
            if i % 10 == 0:
                asoc.append((i, 2, i))                # duplicado a propósito
        pd.DataFrame(asoc, columns=["key.frame_timestamp_micros", "key.camera_name", "key.laser_object_id"]).to_parquet(
            tmp_path / f"{seg_id}.parquet", index=False
        )
        filas.append(
            pd.DataFrame(
                {
                    "segment_id": seg_id, "seg": seg_id[:12], "grupo": "train", "location": "location_sf",
                    "time_of_day": "Day", "key.frame_timestamp_micros": np.arange(n),
                    "key.laser_object_id": np.arange(n), "sin_camara": 0, "az_signed": az,
                }
            )
        )
    return pd.concat(filas, ignore_index=True)


def test_flujo_sintetico_completo(tmp_path: Path) -> None:
    cajas = agregar_pares_camara(_cajas_sinteticas(tmp_path), tmp_path, CAMARAS)
    assert {"c1", "c2"} <= set(cajas.columns) and cajas[["c1", "c2"]].dtypes.eq(int).all()
    assert cajas.loc[cajas["seg"] == "A" * 12, "c1"].sum() == 0
    assert (cajas[["c1", "c2"]].sum(axis=1) > 0).all()

    rangos = calcular_rangos(cajas[cajas["grupo"] == "train"], CAMARAS)
    assert -50 <= rangos[1][0] < -40 and 40 < rangos[1][1] <= 50
    tasa, nrango = tasa_por_celda(cajas, rangos, CAMARAS)
    assert list(tasa.index) == ["A" * 12, "B" * 12, "C" * 12]
    assert tasa.loc["A" * 12, "c1"] == 0.0 and nrango.loc["A" * 12, "c1"] >= 100

    huecos = detectar_huecos(tasa, nrango)
    assert huecos["c1"].to_dict() == {"A" * 12: True, "B" * 12: False, "C" * 12: False}
    en = marcar_cajas_en_hueco(cajas, huecos, rangos)
    esperado = (cajas["seg"] == "A" * 12) & cajas["az_signed"].between(*rangos[1])
    assert en.equals(esperado.rename("en_hueco"))

    resumen = resumen_celdas(cajas, tasa, nrango, huecos)
    assert list(resumen.columns) == (
        ["grupo", "ubicacion", "momento", "cajas"] + [f"tasa_c{c}" for c in CAMARAS]
        + [f"n_rango_c{c}" for c in CAMARAS] + [f"hueco_c{c}" for c in CAMARAS] + ["algun_hueco"]
    )
    assert resumen["algun_hueco"].to_dict() == {"A" * 12: True, "B" * 12: False, "C" * 12: False}


def test_pares_inconsistentes_con_sin_camara_falla(tmp_path: Path) -> None:
    cajas = _cajas_sinteticas(tmp_path)
    cajas.loc[0, "sin_camara"] = 1                    # tiene par en la cámara 2, pero se declara sin cámara
    with pytest.raises(ValueError):
        agregar_pares_camara(cajas, tmp_path, CAMARAS)


def test_parametros_ida_y_vuelta_json() -> None:
    p = ParametrosDetector(
        frac=0.3, min_cajas=80, p_inf=2.5, p_sup=97.5,
        rangos={1: (-20.5, 20.25), 5: (-70.0, 3.125)}, medianas_ref={"c1": 0.88, "c5": 0.9},
    )
    texto = json.dumps(p.to_dict())
    assert ParametrosDetector.from_dict(json.loads(texto)) == p
    vacio = ParametrosDetector()
    assert ParametrosDetector.from_dict(json.loads(json.dumps(vacio.to_dict()))) == vacio


# ---------------------------------------------------------------- integración (solo lectura)
ENTRADAS = [
    "data/05_model_input/features_B.parquet", "data/05_model_input/test.parquet",
    "data/05_model_input/config_features_B.json", "data/08_reporting/08_azimut_por_camara_empirico.csv",
    "data/08_reporting/10_M_rangos_camara.csv", "data/08_reporting/10_M_tasa_segmento_camara.csv",
    "data/08_reporting/10_M_pares_con_hueco.csv", "data/01_raw/waymo/camera_to_lidar_box_association",
]
COLS_M = [
    "segment_id", "key.frame_timestamp_micros", "key.laser_object_id", "sin_camara", "azimut_abs_deg",
    "box_center_x", "box_center_y", "num_lidar_points", "num_top_lidar_points", "time_of_day", "location",
]


def _dif_max(a: pd.DataFrame | pd.Series | np.ndarray, b: pd.DataFrame | pd.Series | np.ndarray) -> float:
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    assert x.shape == y.shape
    assert np.array_equal(np.isnan(x), np.isnan(y)), "los NaN no coinciden"
    ok = ~np.isnan(x)
    assert np.allclose(x[ok], y[ok], rtol=1e-6, atol=1e-9)
    return float(np.abs(x[ok] - y[ok]).max()) if ok.any() else 0.0


@pytest.mark.skipif(not all((R / p).exists() for p in ENTRADAS), reason="faltan datos de EP2 en data/")
def test_integracion_reproduce_csv_de_ep2() -> None:
    entrada, rep = R / "data/05_model_input", R / "data/08_reporting"
    az_max = json.loads((entrada / "config_features_B.json").read_text(encoding="utf-8")).get("AZ_MAX", 100)
    tr = pd.read_parquet(entrada / "features_B.parquet", columns=COLS_M + ["en_zona_principal"])
    tr["en_zona_principal"] = tr["en_zona_principal"].astype(bool)
    tr["grupo"] = "train"
    te = pd.read_parquet(entrada / "test.parquet")
    te = te[te["object_type"].isin(["PEDESTRIAN", "CYCLIST"])].copy()
    te["sin_camara"] = 1 - te["tiene_camara"]
    te = te[te["azimut_abs_deg"] <= 120].reset_index(drop=True)          # pop120
    te["en_zona_principal"] = te["azimut_abs_deg"] <= az_max
    te = te[COLS_M + ["en_zona_principal"]].copy()
    te["grupo"] = "test"
    am = pd.concat([tr, te], ignore_index=True)
    am["seg"] = am["segment_id"].str[:12]
    am["az_signed"] = azimut_con_signo(am["box_center_x"], am["box_center_y"])
    cam_csv = pd.read_csv(rep / "08_azimut_por_camara_empirico.csv")
    nombres = {int(str(n).split()[0]): str(n) for n in cam_csv["camara"]}
    camaras = sorted(nombres)

    am = agregar_pares_camara(am, R / "data/01_raw/waymo/camera_to_lidar_box_association", camaras)
    rangos = calcular_rangos(am[am["grupo"] == "train"], camaras)
    tasa, nrango = tasa_por_celda(am, rangos, camaras)
    med = calcular_medianas(tasa)
    huecos = detectar_huecos(tasa, nrango)
    resumen = resumen_celdas(am, tasa, nrango, huecos)

    # 1) rangos y medianas
    ref_r = pd.read_csv(rep / "10_M_rangos_camara.csv")
    d_r = max(
        _dif_max(ref_r["az_p5"], [rangos[c][0] for c in camaras]),
        _dif_max(ref_r["az_p95"], [rangos[c][1] for c in camaras]),
        _dif_max(ref_r["mediana_tasa"], [med[f"c{c}"] for c in camaras]),
    )
    assert list(ref_r["camara"]) == [nombres[c] for c in camaras]

    # 2) tabla segmento por cámara (mismas columnas, mismo orden, mismos valores)
    ref_t = pd.read_csv(rep / "10_M_tasa_segmento_camara.csv", index_col=0, dtype={"seg": str})
    assert list(resumen.columns) == list(ref_t.columns)
    assert list(resumen.index) == list(ref_t.index)
    num = [c for c in ref_t.columns if c.startswith(("tasa_", "n_rango_"))] + ["cajas"]
    d_t = _dif_max(ref_t[num], resumen[num])
    exactas = [c for c in ref_t.columns if c.startswith("hueco_")] + ["algun_hueco", "grupo", "ubicacion", "momento"]
    assert (ref_t[exactas].to_numpy() == resumen[exactas].to_numpy()).all()

    # 3) pares con hueco: los dos esperados
    ref_p = pd.read_csv(rep / "10_M_pares_con_hueco.csv", dtype={"segmento": str})
    filas = [
        {"segmento": s, "camara": nombres[c], "tasa": tasa.loc[s, f"c{c}"], "mediana_camara": med[f"c{c}"],
         "umbral": 0.25 * med[f"c{c}"], "cajas_en_rango": nrango.loc[s, f"c{c}"]}
        for s in resumen.index for c in camaras if huecos.loc[s, f"c{c}"]
    ]
    pares = pd.DataFrame(filas)
    assert len(pares) == 2
    assert set(zip(pares["segmento"], pares["camara"])) == {("911012534050", "5 (lateral der.)"), ("257766998801", "3 (frontal der.)")}
    assert list(pares["segmento"]) == list(ref_p["segmento"]) and list(pares["camara"]) == list(ref_p["camara"])
    cols_p = ["tasa", "mediana_camara", "umbral", "cajas_en_rango"]
    d_p = _dif_max(ref_p[cols_p], pares[cols_p])

    print(f"\nDIFERENCIA MAXIMA ABSOLUTA: rangos_camara={d_r:.3e} | tasa_segmento_camara={d_t:.3e} | pares_con_hueco={d_p:.3e}")
