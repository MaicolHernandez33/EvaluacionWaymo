"""Pruebas de la selección de segmentos nuevos (F18-B): lógica pura contra docs/ep3/plan_seleccion_ep3.json; no descarga nada ni escribe en data/."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nbformat
import pandas as pd
import pytest

from waymo_evaluacion.ep3 import seleccion_nuevos as sn

R = Path(__file__).resolve().parents[2]
CSV = R / "docs/seleccion_segmentos"
PLAN = R / "docs/ep3/plan_seleccion_ep3.json"


@pytest.fixture(scope="module")
def datos():
    inv = pd.read_csv(CSV / "inventario_segmentos.csv", dtype={"segment_id": str})
    reg = pd.read_csv(CSV / "registro_verificacion_ep2.csv", dtype={"segment_id": str})
    return inv, reg


def test_embudo_igual_al_de_ep2_y_91_excluidos_despues(datos):
    inv, reg = datos
    cand, e = sn.embudo(inv, reg["segment_id"])
    assert (e["sin_lluvia"], e["n_frames_>=190"], e["n_detecciones_entre_percentiles"]) == (793, 786, 746)
    assert e["evaluados_ep2_dentro_del_pool"] == 91 and e["candidatos_sin_los_evaluados_por_ep2"] == len(cand) == 655
    assert round(e["limite_inferior_detecciones"]) == 2027 and round(e["limite_superior_detecciones"]) == 33688


def test_plan_guardado_coincide_con_la_logica_y_con_su_hash(datos):
    inv, reg = datos
    plan = sn.construir_plan(inv, reg["segment_id"])
    guardado = json.loads(PLAN.read_text(encoding="utf-8"))
    for k in ("version", "parametros", "cuotas_utiles", "total_cuota", "embudo", "candidatos_por_estrato", "orden_por_estrato"):
        assert guardado[k] == plan[k], k
    assert (R / "docs/ep3/plan_seleccion_ep3.sha256").read_text(encoding="utf-8").split()[0] == hashlib.sha256(PLAN.read_bytes()).hexdigest()
    assert guardado["total_cuota"] == 26 == sum(sn.CUOTAS.values())
    assert guardado["fuentes_sha256"]["inventario_segmentos.csv"] == hashlib.sha256((CSV / "inventario_segmentos.csv").read_bytes()).hexdigest()


def test_orden_sin_solapes_ni_lluvia_ni_evaluados(datos):
    inv, reg = datos
    cand, _ = sn.embudo(inv, reg["segment_id"])
    orden = sn.orden_por_estrato(cand)
    todos = [s for v in orden.values() for s in v]
    assert len(todos) == len(set(todos))
    assert not set(todos) & set(reg["segment_id"])
    assert not set(todos) & set(inv.loc[inv["weather"] == "rain", "segment_id"])
    assert orden == sn.orden_por_estrato(cand)                      # determinista
    assert len(orden["Dawn/Dusk / location_other"]) == 1 and "Night / location_other" not in orden


def _evaluador(util_si):
    def ev(seg):
        u = util_si(seg)
        return {"resultado": "util" if u else "descartado", "motivo": "" if u else "etiquetado ralo"}
    return ev


def test_seleccionar_respeta_cuotas_tope_y_se_puede_reanudar(datos):
    inv, reg = datos
    cand, _ = sn.embudo(inv, reg["segment_id"])
    orden = sn.orden_por_estrato(cand)
    util = lambda s: int(hashlib.md5(s.encode()).hexdigest(), 16) % 10 < 5     # ~50 % útiles, determinista
    r = sn.seleccionar(orden, sn.CUOTAS, _evaluador(util), tope=55)
    assert len(r) <= 55
    res = sn.resumen_cuotas(r, sn.CUOTAS, orden).set_index("estrato")
    assert (res["utiles"] <= res["cuota"]).all()
    assert (res["razon"].isin({"cuota completa", "estrato agotado", "tope global de evaluaciones"})).all()
    # dentro de cada estrato se evalúa en el orden fijado
    for k, v in orden.items():
        vistos = [x["segment_id"] for x in r if x["estrato"] == k]
        assert vistos == v[: len(vistos)]
    # reanudar: con los primeros 20 ya medidos da exactamente la misma secuencia y no vuelve a evaluarlos
    previos = {x["segment_id"]: x for x in r[:20]}
    llamadas = []
    r2 = sn.seleccionar(orden, sn.CUOTAS, lambda s: (llamadas.append(s), _evaluador(util)(s))[1], tope=55, previos=previos)
    assert [x["segment_id"] for x in r2] == [x["segment_id"] for x in r]
    assert not set(llamadas) & set(previos)


def test_seleccionar_agota_un_estrato_y_lo_registra():
    orden = {"Dawn/Dusk / location_other": ["a"], "Day / location_sf": ["b", "c", "d"]}
    cuotas = {("Dawn/Dusk", "location_other"): 1, ("Day", "location_sf"): 2}
    r = sn.seleccionar(orden, cuotas, _evaluador(lambda s: s != "a"), tope=55)
    res = sn.resumen_cuotas(r, cuotas, orden).set_index("estrato")
    assert res.loc["Dawn/Dusk / location_other", "faltan"] == 1 and res.loc["Dawn/Dusk / location_other", "razon"] == "estrato agotado"
    assert res.loc["Day / location_sf", "utiles"] == 2 and res.loc["Day / location_sf", "evaluados"] == 2


@pytest.mark.parametrize("m,esperado", [
    ({"asoc_filas": 0}, "asociacion vacia"),
    ({"asoc_filas": 10}, "pocas asociaciones"),
    ({"asoc_filas": 500, "lidar_disponible": False}, "lidar_box no disponible"),
    ({"asoc_filas": 500, "positivos": 0}, "no cruzan"),
    ({"asoc_filas": 500, "positivos": 29, "tasa_etiquetado_pct": 20}, "pocos positivos"),
    ({"asoc_filas": 500, "positivos": 30, "tasa_etiquetado_pct": 5.4}, "etiquetado ralo"),
])
def test_criterios_de_descarte(m, esperado):
    res, motivo = sn.decidir(m)
    assert res == "descartado" and esperado in motivo


def test_decidir_acepta_un_segmento_util():
    assert sn.decidir({"asoc_filas": 500, "positivos": 30, "tasa_etiquetado_pct": 5.5}) == ("util", "")


def test_el_notebook_00b_contiene_el_codigo_fuente_exacto():
    nb = nbformat.read(R / "notebooks/00b_seleccion_segmentos_ep3.ipynb", as_version=4)
    nbformat.validate(nb)
    fuente = (R / "src/waymo_evaluacion/ep3/seleccion_nuevos.py").read_text(encoding="utf-8").strip("\n")
    assert any(c.cell_type == "code" and c.source == fuente for c in nb.cells)
    texto = "\n".join(c.source for c in nb.cells)
    assert "== (793, 786, 746)" in texto and "MIN_POSITIVOS" in texto and "plan_seleccion_ep3.json" in texto
