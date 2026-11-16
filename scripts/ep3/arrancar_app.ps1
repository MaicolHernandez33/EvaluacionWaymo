# Arranca la pagina de EP3 en local (Windows PowerShell). Uso: .\scripts\ep3\arrancar_app.ps1
$raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $raiz
$py = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { Write-Error "No encuentro .venv. Cree el entorno e instale requirements_app.txt (ver docs/ep3/despliegue.md)."; exit 1 }
if (-not (Test-Path "data\09_app_ep3\cajas_oof.parquet")) { Write-Warning "Faltan los datos de la pagina: ejecute python scripts\ep3\f7_preparar_app.py" }
& $py app\lanzar.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false
