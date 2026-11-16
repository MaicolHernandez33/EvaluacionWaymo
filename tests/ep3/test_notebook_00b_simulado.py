"""Ejecuta las celdas de código del notebook 00b con un «gsutil» simulado (sin bucket, sin red): los candidatos del plan se hacen corresponder con archivos
locales de segmentos de desarrollo (solo se usan sus llaves, así que el contenido sirve). Comprueba el flujo completo: archivos obligatorios, hash del plan,
embudo, orden del plan, evaluación, reanudación, paquete y verificacion_colab.json. Solo escribe en tmp_path. Se omite si no están los parquet crudos (licencia)."""
from __future__ import annotations

import json
import shutil
import subprocess
import tarfile
from pathlib import Path
from types import SimpleNamespace

import nbformat
import pandas as pd
import pytest

R = Path(__file__).resolve().parents[2]
CRUDOS = R / "data/01_raw/waymo"
NB = R / "notebooks/00b_seleccion_segmentos_ep3.ipynb"
pytestmark = pytest.mark.skipif(not (CRUDOS / "lidar_box").exists() or len(list((CRUDOS / "lidar_box").glob("*.parquet"))) < 10, reason="faltan los parquet crudos (licencia)")


def _gsutil_simulado(inventario: set[str], local: dict[str, str]):
    """Devuelve un reemplazo de subprocess.run para `gsutil ls` y `gsutil -q cp`. ``local``: candidato -> segmento de desarrollo cuyo archivo se usa."""
    def run(cmd, *a, **k):
        if cmd[0] != "gsutil":
            return subprocess.run(cmd, *a, **k)
        if cmd[1] == "ls":
            ids = "\n".join(f"gs://b/training/x/{s}.parquet" for s in sorted(inventario))
            return SimpleNamespace(returncode=0, stdout=ids, stderr="")
        origen, destino = cmd[-2], Path(cmd[-1])
        comp = origen.split("/")[-2]
        seg = origen.split("/")[-1].replace(".parquet", "")
        if seg not in local:
            return SimpleNamespace(returncode=1, stdout="", stderr="no existe")
        fuente = CRUDOS / comp / f"{local[seg]}.parquet"
        if not fuente.exists():
            return SimpleNamespace(returncode=1, stdout="", stderr="no existe")
        shutil.copy(fuente, destino)
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    return run


def _ejecutar(tmp_path: Path, subir: list[str], local: dict[str, str], orden_distinto: bool = False) -> dict:
    nb = nbformat.read(NB, as_version=4)
    trabajo = tmp_path / "trabajo"
    meta = trabajo / "meta"
    meta.mkdir(parents=True)
    for n in subir:
        origen = R / ("docs/ep3" if n.startswith("plan_seleccion") else "docs/seleccion_segmentos") / n
        shutil.copy(origen, meta / n)
    inv = pd.read_csv(R / "docs/seleccion_segmentos/inventario_segmentos.csv", dtype={"segment_id": str})
    ns: dict = {"__name__": "nb", "files": None, "display": lambda *a, **k: None}
    import subprocess as sp_real

    for c in nb.cells:
        if c.cell_type != "code":
            continue
        src = c.source.replace('"/content/ep3_nuevos"', repr(str(trabajo)))
        if "from google.colab import auth" in src:
            ns["EN_COLAB"] = False
            continue
        if "subprocess.run" in src or "gcopiar" in src:
            ns["subprocess"] = SimpleNamespace(run=_gsutil_simulado(set(inv["segment_id"]), local), CalledProcessError=sp_real.CalledProcessError)
        exec(compile(src, "celda", "exec"), ns)
        if orden_distinto and "def orden_por_estrato" in src:     # simula otra version de numpy: el orden recalculado difiere
            real = ns["orden_por_estrato"]
            ns["orden_por_estrato"] = lambda *a, **k: {h: list(reversed(v)) for h, v in real(*a, **k).items()}
        if "import hashlib, json, os, subprocess" in src:     # tras importar: reemplazar subprocess por el simulado
            ns["subprocess"] = SimpleNamespace(run=_gsutil_simulado(set(inv["segment_id"]), local), CalledProcessError=sp_real.CalledProcessError)
    return ns


@pytest.fixture(scope="module")
def candidatos_locales() -> dict[str, str]:
    plan = json.loads((R / "docs/ep3/plan_seleccion_ep3.json").read_text(encoding="utf-8"))
    desarrollo = sorted(p.stem for p in (CRUDOS / "lidar_box").glob("*.parquet") if (CRUDOS / "camera_to_lidar_box_association" / p.name).exists())
    ids = [s for v in plan["orden_por_estrato"].values() for s in v]
    return {s: desarrollo[i % len(desarrollo)] for i, s in enumerate(ids)}


TODOS = ["inventario_segmentos.csv", "registro_verificacion_ep2.csv", "diagnostico_lluvia_ep2.csv", "plan_seleccion_ep3.json", "plan_seleccion_ep3.sha256"]


def test_el_notebook_se_detiene_si_faltan_el_plan_o_su_hash(tmp_path: Path, candidatos_locales) -> None:
    with pytest.raises(AssertionError, match="FALTAN ARCHIVOS OBLIGATORIOS"):
        _ejecutar(tmp_path, TODOS[:3], candidatos_locales)


def test_el_notebook_se_detiene_si_el_plan_no_coincide_con_su_hash(tmp_path: Path, candidatos_locales) -> None:
    from nbformat import read

    base = tmp_path / "trabajo" / "meta"
    base.mkdir(parents=True)
    for n in TODOS:
        shutil.copy(R / ("docs/ep3" if n.startswith("plan_seleccion") else "docs/seleccion_segmentos") / n, base / n)
    (base / "plan_seleccion_ep3.json").write_text((base / "plan_seleccion_ep3.json").read_text(encoding="utf-8").replace("26", "27", 1), encoding="utf-8")
    nb = read(NB, as_version=4)
    ns: dict = {"__name__": "nb", "EN_COLAB": False}
    celdas = [c.source.replace('"/content/ep3_nuevos"', repr(str(tmp_path / "trabajo"))) for c in nb.cells if c.cell_type == "code"]
    for s in celdas[:2]:
        if "google.colab" not in s:
            exec(compile(s, "celda", "exec"), ns)
    with pytest.raises(AssertionError, match="NO COINCIDE CON SU sha256"):
        exec(compile(celdas[3], "celda", "exec"), ns)


def test_flujo_completo_simulado_con_paquete_y_reanudacion(tmp_path: Path, candidatos_locales) -> None:
    ns = _ejecutar(tmp_path, TODOS, candidatos_locales)
    reg = ns["reg3"]
    assert len(reg) <= 55 and (reg["resultado"] == "util").sum() > 0
    assert set(reg["resultado"]) <= {"util", "descartado"}
    assert ns["ORDEN_COINCIDE"] is True
    paquete = tmp_path / "trabajo" / "segmentos_nuevos_ep3.tar.gz"
    assert paquete.exists()
    with tarfile.open(paquete) as tar:
        nombres = tar.getnames()
    assert any(n.endswith("verificacion_colab.json") for n in nombres) and any(n.endswith("segmentos_nuevos_ep3.csv") for n in nombres)
    ver = json.loads((tmp_path / "trabajo" / "salida" / "verificacion_colab.json").read_text(encoding="utf-8"))
    assert ver["plan_sha256"] == (R / "docs/ep3/plan_seleccion_ep3.sha256").read_text().split()[0]
    assert ver["orden_recalculado_coincide_con_el_plan"] is True and ver["embudo"]["candidatos_sin_los_evaluados_por_ep2"] == 655 and ver["numpy"] and ver["pandas"]
    lista = pd.read_csv(tmp_path / "trabajo" / "salida" / "segmentos_nuevos_ep3.csv", dtype=str)
    assert {"segment_id", "time_of_day", "location"} <= set(lista.columns) and len(lista) == int((reg["resultado"] == "util").sum())
    for s in lista["segment_id"]:
        assert (tmp_path / "trabajo" / "salida" / "lidar_box" / f"{s}.parquet").exists()
        assert (tmp_path / "trabajo" / "salida" / "camera_to_lidar_box_association" / f"{s}.parquet").exists()
    # cada estrato respeta su cuota de utiles
    res = ns["resumen"].set_index("estrato")
    assert (res["utiles"] <= res["cuota"]).all()
    # reanudar: segunda ejecucion en el mismo directorio de trabajo reproduce el mismo registro sin volver a evaluar
    primera = reg[["segment_id", "resultado"]].reset_index(drop=True)
    registro_csv = tmp_path / "trabajo" / "registro_verificacion_ep3.csv"
    assert registro_csv.exists() and len(pd.read_csv(registro_csv)) == len(reg)
    nb = nbformat.read(NB, as_version=4)
    ns2: dict = {"__name__": "nb", "files": None, "display": lambda *a, **k: None}
    for c in nb.cells:
        if c.cell_type != "code" or "google.colab" in c.source:
            if "google.colab" in c.source:
                ns2["EN_COLAB"] = False
            continue
        src = c.source.replace('"/content/ep3_nuevos"', repr(str(tmp_path / "trabajo")))
        if "def gcopiar" in src:
            ns2["subprocess"] = SimpleNamespace(run=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no debe descargar nada al reanudar")))
        exec(compile(src, "celda", "exec"), ns2)
        if "import hashlib, json, os, subprocess" in src:
            ns2["subprocess"] = SimpleNamespace(run=_gsutil_simulado(set(pd.read_csv(R / "docs/seleccion_segmentos/inventario_segmentos.csv", dtype=str)["segment_id"]), candidatos_locales))
    pd.testing.assert_frame_equal(primera, ns2["reg3"][["segment_id", "resultado"]].reset_index(drop=True))


def test_si_el_orden_recalculado_difiere_se_usa_el_del_plan_y_se_advierte(tmp_path: Path, candidatos_locales, capsys) -> None:
    ns = _ejecutar(tmp_path, TODOS, candidatos_locales, orden_distinto=True)
    plan = json.loads((R / "docs/ep3/plan_seleccion_ep3.json").read_text(encoding="utf-8"))
    assert ns["ORDEN_COINCIDE"] is False and ns["orden"] == plan["orden_por_estrato"]
    assert "ADVERTENCIA" in capsys.readouterr().out
    ver = json.loads((tmp_path / "trabajo" / "salida" / "verificacion_colab.json").read_text(encoding="utf-8"))
    assert ver["orden_recalculado_coincide_con_el_plan"] is False and ver["orden_usado"] == "el del plan sellado"
    primeros = [r["segment_id"] for r in ns["registro"] if r["estrato"] == "Day / location_sf"][:3]
    assert primeros == plan["orden_por_estrato"]["Day / location_sf"][:3]
