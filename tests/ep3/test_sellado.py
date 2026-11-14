"""Pruebas del sellado (P9), la ingesta de segmentos nuevos y la evaluación externa. Solo escriben en tmp_path."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from waymo_evaluacion.ep3.ingesta_nuevos import ingestar_directorio
from waymo_evaluacion.ep3.sellado import (
    CandadoError, congelar_lista, construir_manifest, evaluar_externo, tomar_candado, verificar_manifest, verificar_sellado,
)

from .test_inferencia import P, _artefactos, _asociacion, _lidar_box


def _carpeta_modelos(tmp_path: Path) -> Path:
    mod = tmp_path / "modelos"
    _artefactos().guardar(mod)
    (mod / "manifest_v3.json").write_text(json.dumps(construir_manifest(mod)), encoding="utf-8")
    return mod


def _segmentos_nuevos(tmp_path: Path, n_seg: int = 5) -> Path:
    entrada = tmp_path / "entrada"
    (entrada / "lidar_box").mkdir(parents=True)
    (entrada / "camera_to_lidar_box_association").mkdir()
    filas = []
    rng = np.random.default_rng(3)
    for i in range(n_seg):
        seg = f"{i:012d}_0_000_20_000"
        lb = _lidar_box(10, 120, seg)
        lb[P + "num_top_lidar_points_in_box"] = rng.integers(3, 300, len(lb))
        pts = lb[P + "num_top_lidar_points_in_box"]
        con_par = rng.random(len(lb)) < (pts / (pts + 40))                                              # menos puntos, menos pares
        asoc = _asociacion(lb, {1: (0, 0), 2: (10, 60), 4: (50, 100), 5: (-100, -50)})
        asoc = asoc[~asoc["key.laser_object_id"].isin(lb.loc[~con_par, "key.laser_object_id"])]
        if i == 0:                                                                                     # hueco total de la camara 3 no existe aqui; el hueco se simula en la camara 2
            asoc = asoc[asoc["key.camera_name"] != 2]
        lb.to_parquet(entrada / "lidar_box" / f"{seg}.parquet", index=False)
        asoc.to_parquet(entrada / "camera_to_lidar_box_association" / f"{seg}.parquet", index=False)
        filas.append({"segment_id": seg, "time_of_day": "Day", "location": "location_sf"})
    pd.DataFrame(filas).to_csv(tmp_path / "lista.csv", index=False)
    return entrada


def test_manifest_detecta_cambios(tmp_path: Path) -> None:
    mod = _carpeta_modelos(tmp_path)
    assert verificar_manifest(mod) == []
    (mod / "umbrales_v3.json").write_text(json.dumps({"A": 0, "B": 0}), encoding="utf-8")
    assert verificar_manifest(mod) == ["umbrales_v3.json cambió"]


def test_congelar_lista_y_verificar_sellado(tmp_path: Path) -> None:
    mod = _carpeta_modelos(tmp_path)
    lista = tmp_path / "lista.csv"
    pd.DataFrame({"segment_id": ["a", "b"]}).to_csv(lista, index=False)
    man = congelar_lista(lista, mod, mod / "manifest_nuevos.json")
    assert man["n_segmentos"] == 2
    verificar_sellado(lista, mod, mod / "manifest_nuevos.json")
    pd.DataFrame({"segment_id": ["a", "b", "c"]}).to_csv(lista, index=False)
    with pytest.raises(CandadoError, match="lista"):
        verificar_sellado(lista, mod, mod / "manifest_nuevos.json")


def test_congelar_falla_si_el_manifest_no_coincide(tmp_path: Path) -> None:
    mod = _carpeta_modelos(tmp_path)
    (mod / "detector_params_v3.json").write_text("{}", encoding="utf-8")
    lista = tmp_path / "lista.csv"
    pd.DataFrame({"segment_id": ["a"]}).to_csv(lista, index=False)
    with pytest.raises(CandadoError):
        congelar_lista(lista, mod, mod / "manifest_nuevos.json")


def test_candado_se_niega_a_correr_dos_veces(tmp_path: Path) -> None:
    c = tmp_path / "evaluacion_externa.lock"
    tomar_candado(c, {"lista": "x"})
    assert "fecha" in json.loads(c.read_text(encoding="utf-8"))
    with pytest.raises(CandadoError, match="ya se hizo"):
        tomar_candado(c, {"lista": "x"})


def test_ingesta_directorio_y_faltantes(tmp_path: Path) -> None:
    entrada = _segmentos_nuevos(tmp_path, 3)
    t = ingestar_directorio(entrada, tmp_path / "lista.csv")
    assert t["seg"].nunique() == 3 and (t["grupo"] == "nuevo").all() and {"c1", "c5", "sin_camara", "en_zona_principal"} <= set(t.columns)
    assert t["sin_camara"].isin([0, 1]).all() and 0 < t["sin_camara"].mean() < 1
    (entrada / "lidar_box" / f"{1:012d}_0_000_20_000.parquet").unlink()
    with pytest.raises(FileNotFoundError):
        ingestar_directorio(entrada, tmp_path / "lista.csv")


def test_evaluar_externo_devuelve_comparaciones_coherentes(tmp_path: Path) -> None:
    nuevos = ingestar_directorio(_segmentos_nuevos(tmp_path, 6), tmp_path / "lista.csv")
    res = evaluar_externo(nuevos, _artefactos(), n_boot=200)
    assert set(res) == {"metricas", "diferencias", "puntos", "brazos", "detector", "lista_A"}
    m = res["metricas"].set_index("metodo")
    assert m.loc["solucion", "AUC"] > 0.55                              # la regla de puntos acierta por construccion
    assert m.loc["solucion", "AUC_lo"] <= m.loc["solucion", "AUC"] <= m.loc["solucion", "AUC_hi"]
    d = res["detector"].iloc[0]
    assert d["celdas_totales"] == 6 * 5 and 0 <= d["celdas_marcadas"] <= d["celdas_totales"]
    assert d["tasa_marcadas"] == pytest.approx(d["celdas_marcadas"] / d["celdas_totales"])
    assert set(res["puntos"]["punto"]) == {"A", "B"} and res["puntos"]["recall"].between(0, 1).all()
    assert 0 < res["brazos"].loc[0, "Fraccion_80_C"] <= 1 and 0 < res["brazos"].loc[0, "Fraccion_80_A"] <= 1


def test_verificar_no_supervisado_detecta_cambios(tmp_path: Path) -> None:
    import subprocess
    import sys

    from waymo_evaluacion.ep3.plan import sha256_archivo

    (tmp_path / "no_supervisado_v3.joblib").write_bytes(b"artefacto de prueba")
    man = {"version": "no_supervisado_v3", "creado": "2026-11-14T00:00:00", "k_elegido": 2, "sha256": {"no_supervisado_v3.joblib": sha256_archivo(tmp_path / "no_supervisado_v3.joblib")}}
    (tmp_path / "manifest_no_supervisado.json").write_text(json.dumps(man), encoding="utf-8")
    script = Path(__file__).resolve().parents[2] / "scripts" / "ep3" / "verificar_no_supervisado.py"
    ok = subprocess.run([sys.executable, str(script), str(tmp_path)], capture_output=True, text=True)
    assert ok.returncode == 0 and "coinciden 1 de 1" in ok.stdout
    (tmp_path / "no_supervisado_v3.joblib").write_bytes(b"cambiado")
    mal = subprocess.run([sys.executable, str(script), str(tmp_path)], capture_output=True, text=True)
    assert mal.returncode == 1 and "DISTINTO" in mal.stdout
