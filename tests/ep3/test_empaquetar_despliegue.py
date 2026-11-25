"""F43: el paquete de despliegue (``scripts/ep3/empaquetar_despliegue.py``) lleva exactamente la lista mínima y rechaza datos prohibidos.

Escribe solo en ``tmp_path`` (copia la lista mínima a una raíz temporal y arma ahí el zip); no crea ``despliegue_lente.zip`` en el repositorio ni toca ``data/``.
"""
from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

import pytest

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "scripts" / "ep3"))
import empaquetar_despliegue as E  # noqa: E402

HAY = (R / "data/09_app_ep3/cajas_oof.parquet").exists() and (R / "data/06_models_ep3/modelo_final_v3.joblib").exists() and (R / "docs/ep3/plan_v3.json").exists()
pytestmark = pytest.mark.skipif(not HAY, reason="faltan los datos de la página")


@pytest.fixture()
def raiz_temporal(tmp_path: Path) -> Path:
    """Una raíz con SOLO los archivos de la lista mínima (copiados), para poder ensuciarla sin tocar el repositorio."""
    raiz = tmp_path / "repo"
    for rel in E.lista_minima(R):
        destino = raiz / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(R / rel, destino)
    return raiz


def test_el_zip_contiene_exactamente_la_lista_minima(raiz_temporal: Path, tmp_path: Path) -> None:
    zip_ = E.armar(raiz_temporal, tmp_path / "salida.zip")
    with zipfile.ZipFile(zip_) as z:
        nombres = {n.removeprefix("lente/") for n in z.namelist()}
    esperado = set(E.lista_minima(R)) | {"LEEME_DESPLIEGUE.txt"}
    assert nombres == esperado
    assert all(n.startswith("lente/") for n in zipfile.ZipFile(zip_).namelist())
    data = sorted(n for n in nombres if n.startswith("data/"))
    assert {n for n in data if n.startswith("data/06_models_ep3/")} == {f"data/06_models_ep3/{x}" for x in E.MODELOS_06}
    assert all(n.startswith(("data/09_app_ep3/", "data/06_models_ep3/")) for n in data)
    for obligatorio in ("app/app.py", "Dockerfile", ".dockerignore", "requirements_app.txt", "constraints_ep3.txt", "docs/despliegue.json", "docs/ep3/plan_v3.json", "data/09_app_ep3/cajas_oof.parquet",
                        "src/waymo_evaluacion/__init__.py", "src/waymo_evaluacion/ep3/app_logica.py", ".streamlit/config.toml", "app/.streamlit/config.toml"):
        assert obligatorio in nombres, obligatorio
    assert not any(n.endswith(".pyc") or "__pycache__" in n for n in nombres)


def test_los_modelos_alternativos_y_los_datos_de_demo_no_viajan(raiz_temporal: Path, tmp_path: Path) -> None:
    (raiz_temporal / "data/06_models_ep3/alternativas_v3.joblib").write_bytes(b"x")                     # existe en el repositorio, pero la página no lo abre
    (raiz_temporal / "data/01_raw").mkdir(parents=True)
    (raiz_temporal / "data/01_raw/algo.csv").write_text("a", encoding="utf-8")
    (raiz_temporal / "datos_demo/candidatos/s").mkdir(parents=True)
    (raiz_temporal / "datos_demo/candidatos/s/lidar_box.parquet").write_bytes(b"x")                     # fuera de la lista: ni se recorre
    with zipfile.ZipFile(E.armar(raiz_temporal, tmp_path / "s.zip")) as z:
        nombres = " ".join(z.namelist())
    assert "alternativas_v3" not in nombres and "01_raw" not in nombres and "datos_demo" not in nombres


@pytest.mark.parametrize("ruta", ["app/lidar_box.parquet", "artefactos_ep3/camera_to_lidar_box_association.parquet", "app/datos_demo/s.txt", "artefactos_ep3/.venv/x.py", "app/.git/config",
                                  "artefactos_ep3/otro.zip", "app/llave.pem", "app/.env", "data/09_app_ep3/lidar_box_000.parquet", "data/09_app_ep3/otro.parquet", "artefactos_ep3/tests/x.py"])
def test_rechaza_lo_prohibido_y_no_escribe_el_zip(raiz_temporal: Path, tmp_path: Path, ruta: str) -> None:
    sucio = raiz_temporal / ruta
    sucio.parent.mkdir(parents=True, exist_ok=True)
    sucio.write_bytes(b"x")
    salida = tmp_path / "no_debe_existir.zip"
    with pytest.raises(E.DespliegueError):
        E.armar(raiz_temporal, salida)
    assert not salida.exists()


def test_rechaza_un_cajas_oof_con_columnas_de_un_lidar_box_crudo(raiz_temporal: Path, tmp_path: Path) -> None:
    import pandas as pd

    pd.DataFrame({"[LiDARBoxComponent].key.segment_context_name": ["s"], "x": [1]}).to_parquet(raiz_temporal / "data/09_app_ep3/cajas_oof.parquet")
    with pytest.raises(E.DespliegueError, match="lidar_box crudo"):
        E.armar(raiz_temporal, tmp_path / "x.zip")


def test_falla_si_falta_un_archivo_de_la_lista(raiz_temporal: Path, tmp_path: Path) -> None:
    (raiz_temporal / "data/06_models_ep3/modelo_final_v3.joblib").unlink()
    with pytest.raises(E.DespliegueError, match="falta"):
        E.armar(raiz_temporal, tmp_path / "x.zip")


def test_validar_solo_deja_pasar_data_de_la_lista() -> None:
    E.validar([f"data/06_models_ep3/{n}" for n in E.MODELOS_06] + ["data/09_app_ep3/kpis.json", "data/09_app_ep3/cajas_oof.parquet", "app/app.py"], R)
    for malo in ("data/01_raw/x.csv", "data/06_models/lr_B.joblib", "data/06_models_ep3/alternativas_v3.joblib", "data/05_model_input/features_B.parquet"):
        with pytest.raises(E.DespliegueError):
            E.validar(["app/app.py", malo], R)
