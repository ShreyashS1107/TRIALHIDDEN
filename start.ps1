# ==============================================================================
# PAIMANA Platform Local Development Startup Script
# Starts both the Next.js Frontend (3000) and FastAPI ML Engine (8000)
# ==============================================================================

[CmdletBinding()]
param()

$rootDir = $PSScriptRoot
$frontendDir = Join-Path $rootDir "FRONTEND"
$venvPython = Join-Path $rootDir ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "           PAIMANA Infrastructure Intelligence Platform          " -ForegroundColor Cyan
Write-Host "               Local Development Services Starter                " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Unblock Python binaries if Smart App Control / Zone.Identifier exists
if (Test-Path "$rootDir\.venv") {
    Get-ChildItem -Path "$rootDir\.venv" -Recurse -Filter *.pyd -ErrorAction SilentlyContinue | Unblock-File
}

# 2. Check and start FastAPI ML service (Port 8000)
$fastApiRunning = $false
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2 -ErrorAction Stop
    if ($health.status -eq "healthy") {
        $fastApiRunning = $true
        Write-Host "  [OK] FastAPI ML service is already running on http://127.0.0.1:8000" -ForegroundColor Green
    }
} catch {
    $fastApiRunning = $false
}

if (-not $fastApiRunning) {
    $port8000InUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($port8000InUse) {
        Write-Host "  [WARN] Port 8000 is occupied by process $($port8000InUse[0].OwningProcess)." -ForegroundColor Yellow
    } else {
        if (-not (Test-Path $venvPython)) {
            Write-Host "  [ERROR] Python virtual environment not found at $venvPython" -ForegroundColor Red
            exit 1
        }
        Write-Host "  Starting FastAPI ML microservice (port 8000)..." -ForegroundColor White
        Start-Process -FilePath "cmd.exe" -ArgumentList "/k `"$venvPython`" -m uvicorn BACKEND.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory $rootDir
    }
}

# 3. Check and start Next.js Frontend (Port 3000)
$nextRunning = $false
try {
    $nextRes = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($nextRes.StatusCode -eq 200) {
        $nextRunning = $true
        Write-Host "  [OK] Next.js frontend is already running on http://localhost:3000" -ForegroundColor Green
    }
} catch {
    $nextRunning = $false
}

if (-not $nextRunning) {
    $port3000InUse = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
    if ($port3000InUse) {
        Write-Host "  [WARN] Port 3000 is occupied by process $($port3000InUse[0].OwningProcess)." -ForegroundColor Yellow
    } else {
        Write-Host "  Starting Next.js frontend (port 3000)..." -ForegroundColor White
        # Using cmd.exe /k npm run dev bypasses PowerShell ExecutionPolicy restrictions on npm.ps1
        Start-Process -FilePath "cmd.exe" -ArgumentList "/k npm run dev" -WorkingDirectory $frontendDir
    }
}

# 4. Wait for services to be ready
Write-Host ""
Write-Host "  Verifying services readiness..." -ForegroundColor Gray

$maxRetries = 20
$fastApiReady = $false
$nextReady = $false

for ($i = 0; $i -lt $maxRetries; $i++) {
    if (-not $fastApiReady) {
        try {
            $h = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2 -ErrorAction Stop
            if ($h.status -eq "healthy") { $fastApiReady = $true }
        } catch {}
    }
    if (-not $nextReady) {
        try {
            $w = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($w.StatusCode -eq 200) { $nextReady = $true }
        } catch {}
    }
    if ($fastApiReady -and $nextReady) { break }
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "                  PAIMANA SERVICES OPERATIONAL                   " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  Next.js Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  FastAPI Backend:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  Health Endpoint:   http://127.0.0.1:8000/health" -ForegroundColor White
Write-Host "  Interactive Docs:  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
