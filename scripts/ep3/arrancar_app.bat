@echo off
rem Arranca la pagina de EP3 en local (Windows). Doble clic o: scripts\ep3\arrancar_app.bat
rem Escucha solo en localhost (no se expone en la red) y sin telemetria. No cambie --server.address.
cd /d "%~dp0\..\.."
if not exist ".venv\Scripts\python.exe" (
  echo No encuentro .venv. Vea docs\ep3\despliegue.md
  exit /b 1
)
".venv\Scripts\python.exe" app\lanzar.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false
