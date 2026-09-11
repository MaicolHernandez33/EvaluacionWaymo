"""
This module contains integration tests for the Kedro project.
Tests should be placed in ``src/tests``, in modules that mirror your
project's structure, and in files named test_*.py.
"""
from pathlib import Path
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project


class TestKedroRun:
    def test_kedro_run_completes_without_errors(self):
        # El proyecto ya tiene pipelines reales (preprocesamiento e
        # ingesta_waymo) registrados bajo __default__: session.run() debe
        # completar sin lanzar ninguna excepcion.
        bootstrap_project(Path.cwd())

        with KedroSession.create(project_path=Path.cwd()) as session:
            session.run()
