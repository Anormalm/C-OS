param(
    [switch]$SkipInstall,
    [switch]$SkipLint,
    [switch]$SkipTests,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Get-PythonExe {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py"
    }
    throw "Python executable not found in PATH."
}

function Invoke-ApiJson {
    param(
        [string]$Method,
        [string]$Url,
        [object]$Body = $null
    )
    if ($null -eq $Body) {
        return Invoke-RestMethod -Method $Method -Uri $Url -TimeoutSec 20
    }

    $json = $Body | ConvertTo-Json -Depth 10 -Compress
    return Invoke-RestMethod -Method $Method -Uri $Url -ContentType "application/json" -Body $json -TimeoutSec 20
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$pythonExe = Get-PythonExe
if ($pythonExe -eq "py") {
    $pythonArgsPrefix = @("-3")
} else {
    $pythonArgsPrefix = @()
}

Write-Host "== C-OS Local Smoke Test =="
Write-Host "Repo: $repoRoot"
Write-Host "Python: $pythonExe"

if (-not $SkipInstall) {
    Write-Host "[1/5] Installing dependencies..."
    & $pythonExe @pythonArgsPrefix -m pip install -e ".[dev]"
}

if (-not $SkipLint) {
    Write-Host "[2/5] Running lint..."
    & $pythonExe @pythonArgsPrefix -m ruff check .
}

if (-not $SkipTests) {
    Write-Host "[3/5] Running tests..."
    & $pythonExe @pythonArgsPrefix -m pytest -q
}

$serverProcess = $null
$baseUrl = "http://127.0.0.1:$Port"

try {
    Write-Host "[4/5] Starting local API server..."
    $serverArgs = @()
    $serverArgs += $pythonArgsPrefix
    $serverArgs += @("-m", "uvicorn", "cos.app:app", "--host", "127.0.0.1", "--port", "$Port")
    $serverProcess = Start-Process -FilePath $pythonExe -ArgumentList $serverArgs -PassThru -WindowStyle Hidden

    $healthy = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $health = Invoke-ApiJson -Method "GET" -Url "$baseUrl/health"
            if ($health.status -eq "ok") {
                $healthy = $true
                break
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }

    if (-not $healthy) {
        throw "API health check failed. Server did not become ready."
    }

    Write-Host "[5/5] Running endpoint smoke checks..."
    $starter = Invoke-ApiJson -Method "POST" -Url "$baseUrl/onboarding/starter-pack" -Body @{}
    $retrieve = Invoke-ApiJson -Method "POST" -Url "$baseUrl/query/retrieve" -Body @{
        query = "What does Atlas use?"
        query_type = "factual"
        top_k = 3
    }
    $coach = Invoke-ApiJson -Method "POST" -Url "$baseUrl/coach/advice" -Body @{
        persona = "general"
        focus = "consistency"
    }
    $nextStep = Invoke-ApiJson -Method "POST" -Url "$baseUrl/coach/next-step" -Body @{
        persona = "general"
        focus = "consistency"
    }
    $weekly = Invoke-ApiJson -Method "POST" -Url "$baseUrl/summary/weekly" -Body @{
        persona = "general"
        days = 7
    }
    $eval = Invoke-ApiJson -Method "POST" -Url "$baseUrl/evaluation/run" -Body @{
        top_k = 3
        dataset = "default"
    }
    $quality = Invoke-ApiJson -Method "GET" -Url "$baseUrl/quality/dashboard"

    Write-Host "Smoke checks passed."
    Write-Host ("- Starter notes ingested: " + $starter.ingested)
    Write-Host ("- Retrieval results: " + ($retrieve | Measure-Object).Count)
    Write-Host ("- Coach advice items: " + ($coach.advice | Measure-Object).Count)
    Write-Host ("- Coach next-step title: " + $nextStep.title)
    Write-Host ("- Weekly highlights: " + ($weekly.highlights | Measure-Object).Count)
    Write-Host ("- Eval hybrid Hit@3: " + $eval.hybrid_hit_at_k)
    Write-Host ("- Quality recommendations: " + ($quality.recommendations | Measure-Object).Count)
} finally {
    if ($null -ne $serverProcess -and -not $serverProcess.HasExited) {
        Write-Host "Stopping local API server..."
        Stop-Process -Id $serverProcess.Id -Force
    }
}

Write-Host "Done."
