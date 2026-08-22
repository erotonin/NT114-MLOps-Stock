$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Docker Desktop installations differ: some expose `docker compose`, while
# this verified laptop exposes the standalone Compose v5 plugin executable.
$compose = $null
$programFiles = $env:ProgramFiles
if ([string]::IsNullOrWhiteSpace($programFiles)) {
    $programFiles = [Environment]::GetFolderPath("ProgramFiles")
}
$plugin = Join-Path $programFiles "Docker\cli-plugins\docker-compose.exe"
if (Test-Path $plugin) {
    $compose = @($plugin)
}
if ($null -eq $compose) {
    $dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCommand) {
        try {
            & $dockerCommand.Source compose version 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $compose = @($dockerCommand.Source, "compose")
            }
        } catch {
            # Some Docker Desktop installations return a native-command error
            # when the compose subcommand is unavailable; try the plugin path.
        }
    }
}
if ($null -eq $compose) {
    throw "Docker Compose was not found. Install or repair Docker Desktop."
}

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & $compose @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose command failed: $($Arguments -join ' ')"
    }
}

function Test-ListeningPort {
    param([int]$Port)
    try {
        return (@(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).Count -gt 0)
    } catch {
        return $false
    }
}

$requestedPort = $env:ENSEMBLE_HOST_PORT
if ([string]::IsNullOrWhiteSpace($requestedPort)) {
    $ensembleHostPort = 8080
    if (Test-ListeningPort $ensembleHostPort) {
        $ensembleHostPort = $null
        foreach ($candidate in 18080..18089) {
            if (-not (Test-ListeningPort $candidate)) {
                $ensembleHostPort = $candidate
                break
            }
        }
        if ($null -eq $ensembleHostPort) {
            throw "Host port 8080 is busy and no fallback port in 18080..18089 is available."
        }
        Write-Warning "Host port 8080 is busy; using Ensemble host port $ensembleHostPort. Internal container port remains 8080."
    }
    $env:ENSEMBLE_HOST_PORT = [string]$ensembleHostPort
} else {
    $parsedPort = 0
    if (-not [int]::TryParse($requestedPort, [ref]$parsedPort) -or $parsedPort -lt 1 -or $parsedPort -gt 65535) {
        throw "ENSEMBLE_HOST_PORT must be an integer from 1 to 65535."
    }
    $ensembleHostPort = $parsedPort
}

Write-Host "Project root: $root"
Write-Host "Starting local-offline Compose stack. Model artifacts are read from .\models."
Write-Host "Ensemble host port: $ensembleHostPort (container port: 8080)"
Invoke-Compose config | Out-Null
Invoke-Compose up -d --build --remove-orphans
Invoke-Compose ps

$readiness = @(
    @{ Name = "Data API"; Url = "http://127.0.0.1:8001/health" },
    @{ Name = "TFT API"; Url = "http://127.0.0.1:8002/health" },
    @{ Name = "LightGBM API"; Url = "http://127.0.0.1:8003/health" },
    @{ Name = "Ensemble API"; Url = "http://127.0.0.1:$ensembleHostPort/health" },
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
    Invoke-Compose ps
    Write-Host "Inspect logs with: $($compose -join ' ') logs --tail=100 <service>"
} else {
    Write-Host "All service readiness checks passed."
    Write-Host "Run prediction smoke test: python scripts\smoke_test.py"
}

Write-Host "Dashboard: http://127.0.0.1:8081"
Write-Host "Ensemble API: http://127.0.0.1:$ensembleHostPort/docs"
Write-Host "Control API: http://127.0.0.1:8085/docs"
Write-Host "Optional MLflow profile: $($compose -join ' ') --profile mlflow up -d"
