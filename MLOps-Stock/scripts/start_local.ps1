$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$compose = Join-Path $env:ProgramFiles "Docker\cli-plugins\docker-compose.exe"
if (-not (Test-Path $compose)) {
    throw "Docker Compose plugin not found at $compose. Install or repair Docker Desktop."
}

Write-Host "Project root: $root"
Write-Host "Starting Docker Compose stack. First build may take several minutes because TFT/PyTorch and MLflow images are large."
& $compose config --quiet
& $compose up -d --build
& $compose ps

$urls = @(
    "http://127.0.0.1:8001/docs",
    "http://127.0.0.1:8002/docs",
    "http://127.0.0.1:8003/docs",
    "http://127.0.0.1:8080/docs",
    "http://127.0.0.1:8081/",
    "http://127.0.0.1:8085/health"
)

Write-Host "Waiting for service health checks..."
Start-Sleep -Seconds 10
foreach ($url in $urls) {
    try {
        Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10 | Out-Null
        Write-Host "OK $url"
    } catch {
        Write-Warning "NOT READY $url — run docker compose logs or check the service status."
    }
}

Write-Host "Dashboard: http://127.0.0.1:8081"
Write-Host "Ensemble API: http://127.0.0.1:8080/docs"
Write-Host "Control API: http://127.0.0.1:8085/docs"
