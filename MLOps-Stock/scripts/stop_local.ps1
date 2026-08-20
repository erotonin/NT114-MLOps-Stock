$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$compose = Join-Path $env:ProgramFiles "Docker\cli-plugins\docker-compose.exe"
if (-not (Test-Path $compose)) {
    throw "Docker Compose plugin not found at $compose."
}
& $compose down
