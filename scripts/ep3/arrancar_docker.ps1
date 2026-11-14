# Construye y arranca la pagina en Docker (solo local). Requiere Docker Desktop encendido. Uso: .\scripts\ep3\arrancar_docker.ps1
$raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $raiz
docker compose up --build
