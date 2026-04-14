$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

function Wait-HttpOk {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [int]$MaxAttempts = 60,
        [int]$DelaySeconds = 2
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "OK: $Name disponível em $Url"
                return
            }
        } catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    throw "Tempo esgotado aguardando $Name em $Url"
}

Write-Host "Iniciando Lotofacil Optimizer..."
docker compose up --build -d

Write-Host "Aguardando backend..."
Wait-HttpOk -Url "http://localhost:8000/health" -Name "Backend"

Write-Host "Aguardando frontend..."
Wait-HttpOk -Url "http://localhost:5173" -Name "Frontend"

Write-Host "Abrindo aplicação no navegador..."
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "Aplicação pronta."
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend:  http://localhost:8000"
