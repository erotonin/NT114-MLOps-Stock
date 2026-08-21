$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$compose = Join-Path $env:ProgramFiles "Docker\cli-plugins\docker-compose.exe"
if (-not (Test-Path $compose)) {
    throw "Docker Compose plugin not found at $compose. Install or repair Docker Desktop."
}

Write-Host "Project root: $root"
Write-Host "Starting local-offline Compose stack. Model artifacts are read from .\models."
& $compose config --quiet
if ($LASTEXITCODE -ne 0) { throw "docker-compose.yml validation failed." }
& $compose up -d --build --remove-orphans
& $compose ps

$readiness = @(
    @{ Name = "Data API"; Url = "http://127.0.0.1:8001/health" },
    @{ Name = "TFT API"; Url = "http://127.0.0.1:8002/health" },
    @{ Name = "LightGBM API"; Url = "http://127.0.0.1:8003/health" },
    @{ Name = "Ensemble API"; Url = "http://127.0.0.1:8080/health" },
    @{ Name = "Monitor API"; Url = "http://127.0.0.1:8084/health" },
    @{ Name = "Control API"; Url = "http://127.0.0.1:8085/health" },
    @{ Name = "Dashboard"; Url = "http://127.0.0.1:8081/health" }
)

Write-Host "Waiting for service readiness..."
$deadline = (Get-Date).AddMinutes(3)
$pending = @($readiness)
while ($pending.Count -gt 0 -and (Get-Date) -lt $deadline) {
    $next = @()
    foreach ($item in $pending) {
        try {
            $response = Invoke-WebRequest -Uri $item.Url -UseBasicParsing -TimeoutSec 8
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host ("OK  {0}: {1}" -f $item.Name, $item.Url)
            } else {
                $next += $item
            }
        } catch {
            $next += $item
        }
    }
    $pending = $next
    if ($pending.Count -gt 0) { Start-Sleep -Seconds 5 }
}

if ($pending.Count -gt 0) {
    Write-Warning "Some services are not ready: $($pending.Name -join ', ')"
    & $compose ps
    Write-Host "Inspect logs with: $compose logs --tail=100 <service>"
} else {
    Write-Host "All service readiness checks passed."
    Write-Host "Run prediction smoke test: python scripts\smoke_test.py"
}

Write-Host "Dashboard: http://127.0.0.1:8081"
Write-Host "Ensemble API: http://127.0.0.1:8080/docs"
Write-Host "Control API: http://127.0.0.1:8085/docs"
Write-Host "Optional MLflow profile: $compose --profile mlflow up -d"
