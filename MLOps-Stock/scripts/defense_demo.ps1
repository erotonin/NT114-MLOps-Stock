$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$out = Join-Path $root "artifacts\defense_demo_evidence.txt"
"MLOps Stock defense demo evidence" | Set-Content $out
("Timestamp: {0}" -f (Get-Date -Format o)) | Add-Content $out

function Get-Endpoint([string]$Name, [string]$Url, [hashtable]$Headers = @{}) {
    ("--- {0} ---" -f $Name) | Add-Content $out
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -Headers $Headers -TimeoutSec 20
        ("HTTP={0}" -f $response.StatusCode) | Add-Content $out
        $response.Content | Add-Content $out
    } catch {
        ("ERROR={0}" -f $_.Exception.Message) | Add-Content $out
        if ($_.Exception.Response) {
            try {
                $reader = New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())
                ("ERROR_BODY={0}" -f $reader.ReadToEnd()) | Add-Content $out
            } catch {}
        }
    }
}

Get-Endpoint "Data health" "http://127.0.0.1:8001/health"
Get-Endpoint "TFT health" "http://127.0.0.1:8002/health"
Get-Endpoint "LightGBM health" "http://127.0.0.1:8003/health"
Get-Endpoint "Ensemble health" "http://127.0.0.1:8080/health"
Get-Endpoint "Dashboard health" "http://127.0.0.1:8081/health"
Get-Endpoint "Monitor health" "http://127.0.0.1:8084/health"
Get-Endpoint "Prometheus metrics" "http://127.0.0.1:8084/metrics"
Get-Endpoint "Control health" "http://127.0.0.1:8085/health"
Get-Endpoint "Registry" "http://127.0.0.1:8085/models" @{"X-Role"="viewer"}
Get-Endpoint "Audit" "http://127.0.0.1:8085/audit?limit=10" @{"X-Role"="viewer"}
Get-Endpoint "Retrain jobs" "http://127.0.0.1:8085/retrain/jobs?limit=10" @{"X-Role"="viewer"}
Get-Endpoint "Feature store catalog" "http://127.0.0.1:8085/features" @{"X-Role"="viewer"}
Get-Endpoint "FPT feature metadata" "http://127.0.0.1:8085/features/FPT" @{"X-Role"="viewer"}
Get-Endpoint "Invalid Ensemble ticker contract" "http://127.0.0.1:8080/predict/FPT-"
Get-Endpoint "Invalid Data days contract" "http://127.0.0.1:8001/fetch/FPT?days=5000"
"--- Viewer retrain denial ---" | Add-Content $out
try {
    $denyBody = '{"ticker":"FPT","horizon":3,"trigger_type":"manual","epochs":1}'
    $denyResponse = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8085/retrain" -Method Post -Headers @{"X-Role"="viewer"} -ContentType "application/json" -Body $denyBody -TimeoutSec 20
    ("UNEXPECTED_HTTP={0}" -f $denyResponse.StatusCode) | Add-Content $out
} catch {
    if ($_.Exception.Response) {
        ("EXPECTED_HTTP=" + [int]$_.Exception.Response.StatusCode) | Add-Content $out
    } else {
        ("ERROR={0}" -f $_.Exception.Message) | Add-Content $out
    }
}

"--- Official smoke test ---" | Add-Content $out
python scripts\smoke_test.py 2>&1 | Add-Content $out

Write-Output "Evidence written to $out"
Get-Content $out
