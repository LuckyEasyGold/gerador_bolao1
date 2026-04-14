$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "Parando Lotofacil Optimizer..."
docker compose down
Write-Host "Aplicação parada."
