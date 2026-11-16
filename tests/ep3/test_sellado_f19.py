"""F19-A2 y A4b: el candado se toma tarde, las entradas se comprueban antes, el ensayo no toca lo real, el detector usa dos denominadores y las alternativas se sellan. Solo tmp_path."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from waymo_evaluacion.ep3 import modelos as M
from waymo_evaluacion.ep3 import sellado
from waymo_evaluacion.ep3.alternativas import config_mas_frecuente, guardar_alternativas, verificar_alternativas
from waymo_evaluacion.ep3.congelado import PuntuadorModelo
from waymo_evaluacion.ep3.ingesta_nuevos import ingestar_directorio
from waymo_evaluacion.ep3.sellado import CandadoError, EntradasFaltantes, congelar_lista, ejecutar_evaluacion, evaluar_externo, verificar_sellado

from .test_inferencia import _artefactos
from .test_sellado import _carpeta_modelos, _segmentos_nuevos

R = Path(__file__).resolve().parents[2]


@pytest.fixture()
def escenario(tmp_path: Path) -> dict:
    mod = _carpeta_modelos(tmp_path)
    entrada = _segmentos_nuevos(tmp_path, 6)
    lista = tmp_path / "lista.csv"
    nuevos = tmp_path / "nuevos.parquet"
    ingestar_directorio(entrada, lista).to_parquet(nuevos, index=False)
    man = tmp_path / "manifest_nuevos_ensayo.json"
    congelar_lista(lista, mod, man)
    return {"mod": mod, "lista": lista, "nuevos": nuevos, "manifest": man, "candado": tmp_path / "evaluacion_externa.lock", "salida": tmp_path / "salida", "tmp": tmp_path}


def _correr(e: dict, **kw):
    return ejecutar_evaluacion(e["lista"], e["nuevos"], e["mod"], e["manifest"], e["salida"], e["candado"], n_boot=60, **kw)


def test_una_falla_de_calculo_no_consume_el_candado(escenario, monkeypatch: pytest.MonkeyPatch) -> None:
    def falla(*a, **k):
        raise RuntimeError("falla simulada del calculo")

    monkeypatch.setattr(sellado, "evaluar_externo", falla)
    with pytest.raises(RuntimeError, match="simulada"):
        _correr(escenario)
    assert not escenario["candado"].exists() and not escenario["salida"].exists()          # ni candado ni salidas a medias
    monkeypatch.undo()
    out = _correr(escenario)                                                                    # el unico intento sigue disponible
    assert escenario["candado"].exists() and (escenario["salida"] / "externa_metricas.csv").exists() and out["ensayo"] is False


def test_el_candado_guarda_los_sha256_de_las_salidas_y_una_segunda_corrida_se_niega(escenario) -> None:
    _correr(escenario)
    lock = json.loads(escenario["candado"].read_text(encoding="utf-8"))
    assert {"externa_metricas.csv", "externa_detector.csv", "externa_brazos.csv", "externa_puntos.csv", "externa_diferencias.csv", "externa_lista_A.csv"} <= set(lock["sha256_salidas"])
    for nombre, h in lock["sha256_salidas"].items():
        assert hashlib.sha256((escenario["salida"] / nombre).read_bytes()).hexdigest() == h
    assert lock["sha256_lista"] and lock["sha256_manifest_nuevos"] and "fecha" in lock
    antes = (escenario["salida"] / "externa_metricas.csv").read_bytes()
    with pytest.raises(CandadoError, match="ya se hizo"):
        _correr(escenario)
    assert (escenario["salida"] / "externa_metricas.csv").read_bytes() == antes             # lo escrito no se pisa


def test_faltan_entradas_da_un_mensaje_claro_y_no_toma_candado(escenario) -> None:
    escenario["nuevos"].unlink()
    with pytest.raises(EntradasFaltantes, match="ingesta_nuevos.py"):
        _correr(escenario)
    escenario["manifest"].unlink()
    with pytest.raises(EntradasFaltantes, match="congelar"):
        _correr(escenario)
    escenario["lista"].unlink()
    with pytest.raises(EntradasFaltantes) as e:
        _correr(escenario)
    assert "lista de segmentos" in str(e.value) and "manifest" in str(e.value) and "tabla de segmentos nuevos" in str(e.value)       # lista todos los problemas
    assert not escenario["candado"].exists()


def test_si_cambia_la_lista_se_detiene_antes_del_candado(escenario) -> None:
    pd.DataFrame({"segment_id": ["x"]}).to_csv(escenario["lista"], index=False)
    with pytest.raises(CandadoError, match="la lista"):
        _correr(escenario)
    assert not escenario["candado"].exists()


def test_ensayo_no_toma_candado_ni_toca_el_manifest_real(escenario) -> None:
    real = escenario["mod"] / "manifest_nuevos.json"
    real.write_text('{"real": true}', encoding="utf-8")
    antes = real.read_bytes()
    out = _correr(escenario, ensayo=True)
    assert out["ensayo"] is True and not escenario["candado"].exists() and real.read_bytes() == antes
    assert (escenario["salida"] / "externa_detector.csv").exists()
    _correr(escenario, ensayo=True)                                                                    # un ensayo se puede repetir
    assert not escenario["candado"].exists()


def test_cli_ensayo_exige_manifest_y_no_usa_el_real(escenario) -> None:
    script = R / "scripts" / "ep3" / "evaluar_sellado.py"
    base = [sys.executable, str(script), "evaluar", "--ensayo", "--lista", str(escenario["lista"]), "--entrada", str(escenario["nuevos"]), "--modelos", str(escenario["mod"]), "--n-boot", "40"]
    sin = subprocess.run(base, capture_output=True, text=True)
    assert sin.returncode != 0 and "--manifest" in (sin.stderr + sin.stdout)
    real = escenario["mod"] / "manifest_nuevos.json"
    mismo = subprocess.run(base + ["--manifest", str(real)], capture_output=True, text=True)
    assert mismo.returncode != 0 and "real" in (mismo.stderr + mismo.stdout)
    ok = subprocess.run(base + ["--manifest", str(escenario["manifest"]), "--salida", str(escenario["salida"])], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr[-500:]
    assert "ENSAYO" in ok.stdout and (escenario["salida"] / "externa_metricas.csv").exists() and not real.exists()


def test_el_detector_se_reporta_con_dos_denominadores(escenario) -> None:
    nuevos = pd.read_parquet(escenario["nuevos"])
    d = evaluar_externo(nuevos, _artefactos(), n_boot=80)["detector"]
    assert len(d) == 2 and d.iloc[0]["denominador"].startswith("todas las celdas") and "100" in d.iloc[1]["denominador"]
    a, b = d.iloc[0], d.iloc[1]
    assert a["celdas_totales"] == 6 * 5 and b["celdas_totales"] <= a["celdas_totales"] and a["celdas_marcadas"] == b["celdas_marcadas"]
    assert b["tasa_marcadas"] >= a["tasa_marcadas"]
    for r in (a, b):
        assert r["tasa_lo"] <= r["tasa_marcadas"] + 1e-9 and r["tasa_marcadas"] <= r["tasa_hi"] + 1e-9


def _lr3_sintetico(nuevos: pd.DataFrame) -> PuntuadorModelo:
    cols = ["num_lidar_points", "num_top_lidar_points", "azimut_abs_deg"]
    pp = nuevos[nuevos["en_zona_principal"]]
    return PuntuadorModelo(M.construir("LR", {}, cols).fit(pp[cols], pp["sin_camara"]), cols)


def test_las_alternativas_se_comparan_con_la_regla_y_se_sellan(escenario) -> None:
    nuevos = pd.read_parquet(escenario["nuevos"])
    guardar_alternativas({"LR3": _lr3_sintetico(nuevos)}, escenario["mod"], {"nota": "prueba"})
    assert verificar_alternativas(escenario["mod"]) == []
    man = escenario["tmp"] / "m2.json"
    congelar_lista(escenario["lista"], escenario["mod"], man)                                     # ahora el sello incluye el manifest de las alternativas
    assert json.loads(man.read_text(encoding="utf-8"))["sha256_manifest_alternativas"]
    escenario["manifest"] = man
    out = _correr(escenario)
    t = out["resultados"]["alternativas"]
    assert set(t["alternativa"]) == {"LR3"} and set(t["metrica"]) == {"AUC", "Fraccion_80"} and (t["ic_lo"] <= t["ic_hi"]).all()
    assert (escenario["salida"] / "externa_alternativas.csv").exists()
    assert "externa_alternativas.csv" in json.loads(escenario["candado"].read_text(encoding="utf-8"))["sha256_salidas"]


def test_si_cambian_las_alternativas_despues_de_congelar_se_detiene(escenario) -> None:
    nuevos = pd.read_parquet(escenario["nuevos"])
    guardar_alternativas({"LR3": _lr3_sintetico(nuevos)}, escenario["mod"], {})
    man = escenario["tmp"] / "m2.json"
    congelar_lista(escenario["lista"], escenario["mod"], man)
    (escenario["mod"] / "alternativas_v3.joblib").write_bytes(b"cambiado")
    escenario["manifest"] = man
    with pytest.raises(CandadoError, match="alternativas"):
        _correr(escenario)
    assert not escenario["candado"].exists()


def test_alternativas_que_aparecen_despues_de_congelar_la_lista_se_detectan(escenario) -> None:
    nuevos = pd.read_parquet(escenario["nuevos"])
    assert json.loads(escenario["manifest"].read_text(encoding="utf-8"))["sha256_manifest_alternativas"] is None
    guardar_alternativas({"LR3": _lr3_sintetico(nuevos)}, escenario["mod"], {})
    with pytest.raises(CandadoError, match="apareció"):
        verificar_sellado(escenario["lista"], escenario["mod"], escenario["manifest"])


def test_config_mas_frecuente_y_desempate() -> None:
    cfg = pd.DataFrame({"modelo": "XGB", "etapa": "principal", "fold": [0, 1, 2, 3, 4], "variables": ["A", "B", "B", "C", "D"], "max_depth": [4.0, 2.0, 2.0, 1.0, 3.0], "n_estimators": [200.0, 30.0, 30.0, 100.0, 100.0]})
    v, p, n, tot, regla = config_mas_frecuente(cfg, "XGB")
    assert (v, p, n, tot) == ("B", {"max_depth": 2, "n_estimators": 30}, 2, 5) and "más repetida" in regla and "empate" not in regla
    cfg2 = cfg.assign(variables=["A", "B", "C", "D", "E"], max_depth=[4.0, 2.0, 1.0, 3.0, 5.0])
    v2, _, n2, _, regla2 = config_mas_frecuente(cfg2, "XGB")
    assert v2 == "A" and n2 == 1 and "empate" in regla2                                                  # empate total: gana el fold de menor indice
    with pytest.raises(ValueError):
        config_mas_frecuente(cfg, "LGBM")


@pytest.mark.skipif(not (R / "data/06_models_ep3/manifest_alternativas.json").exists(), reason="las alternativas reales no estan congeladas")
def test_las_alternativas_reales_coinciden_con_su_manifest_y_no_tocan_el_manifest_v3() -> None:
    mod = R / "data/06_models_ep3"
    assert verificar_alternativas(mod) == []
    man = json.loads((mod / "manifest_alternativas.json").read_text(encoding="utf-8"))
    assert set(man["alternativas"]) == {"LR3", "XGB"} and man["xgb_folds_que_la_eligieron"] == "2 de 5"
    v3 = json.loads((mod / "manifest_v3.json").read_text(encoding="utf-8"))
    assert "alternativas_v3.joblib" not in v3["sha256"]


@pytest.mark.skipif(not (R / "data/06_models_ep3/modelo_final_v3.joblib").exists(), reason="falta la solucion congelada")
def test_la_solucion_congelada_es_la_regla_y_su_puntaje_es_monotono_con_ella() -> None:
    """F19-A4a: «solucion contra regla» da diferencia 0 por construccion porque el puntaje de v3 ES la regla (menos puntos del sensor superior)."""
    from waymo_evaluacion.ep3.congelado import PuntuadorRegla
    from waymo_evaluacion.ep3.inferencia import cargar_artefactos

    art = cargar_artefactos(R / "data/06_models_ep3")
    assert isinstance(art.puntuador, PuntuadorRegla) and art.puntuador.columna == "num_top_lidar_points"
    X = pd.DataFrame({"num_top_lidar_points": [0, 3, 3, 11, 32, 500]})
    s = art.puntuador.puntuar(X)
    assert (s == -X["num_top_lidar_points"].to_numpy(float)).all()
    assert art.umbrales == {"A": -32.0, "B": -11.0}


def test_copiar_sello_a_artefactos_verifica_y_copia(escenario) -> None:
    script = R / "scripts" / "ep3" / "copiar_sello_a_artefactos.py"
    destino = escenario["tmp"] / "artefactos"
    base = [sys.executable, str(script), "--modelos", str(escenario["mod"]), "--destino", str(destino)]
    ok = subprocess.run(base, capture_output=True, text=True)
    assert ok.returncode == 0 and (destino / "manifest_v3.json").exists() and not (destino / "manifest_nuevos.json").exists()
    shutil_copy = __import__("shutil").copy
    shutil_copy(escenario["manifest"], escenario["mod"] / "manifest_nuevos.json")
    sin_lista = subprocess.run(base, capture_output=True, text=True)
    assert sin_lista.returncode != 0 and "--lista" in (sin_lista.stderr + sin_lista.stdout)
    con = subprocess.run(base + ["--lista", str(escenario["lista"])], capture_output=True, text=True)
    assert con.returncode == 0 and (destino / "manifest_nuevos.json").exists() and (destino / "segmentos_nuevos_ep3.csv").exists()
    pd.DataFrame({"segment_id": ["otro"]}).to_csv(escenario["lista"], index=False)                    # si la lista cambio, no se copia
    mal = subprocess.run(base + ["--lista", str(escenario["lista"])], capture_output=True, text=True)
    assert mal.returncode != 0
