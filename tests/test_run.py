"""
This module contains integration tests for the Kedro project.
Tests should be placed in ``src/tests``, in modules that mirror your
project's structure, and in files named test_*.py.
"""
from pathlib import Path

import pytest
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

# La corrida completa necesita los datos crudos (CSV sintetico y parquet de Waymo), que no se distribuyen
# (licencia no comercial de Waymo; data/ esta en .gitignore). Sin ellos la prueba se omite.
_RAW_LIDAR = Path("data/01_raw/waymo/lidar_box")
_RAW_CSV = Path("data/01_raw/detecciones_waymo_like.csv")
_HAY_CRUDOS = _RAW_CSV.exists() and _RAW_LIDAR.exists() and any(_RAW_LIDAR.glob("*.parquet"))


@pytest.mark.skipif(not _HAY_CRUDOS, reason="faltan los datos crudos de Waymo y el CSV sintetico (no se distribuyen)")
class TestKedroRun:
    def test_kedro_run_completes_without_errors(self):
        # El proyecto ya tiene pipelines reales (preprocesamiento e
        # ingesta_waymo) registrados bajo __default__: session.run() debe
        # completar sin lanzar ninguna excepcion.
        bootstrap_project(Path.cwd())

        with KedroSession.create(project_path=Path.cwd()) as session:
            session.run()
