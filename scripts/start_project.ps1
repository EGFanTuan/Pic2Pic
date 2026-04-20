$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "      Pic2Pic Smart Start (PowerShell)   " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan


# 0. Clean up existing processes
Write-Host "[CLEAN] Checking for existing Pic2Pic processes..." -ForegroundColor Yellow
$ports = @(5000, 5173)
foreach ($port in $ports) {
    $proc = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

# Define cleanup function for Ctrl+C
function Cleanup {
    Write-Host "`n[CLEAN] Shutting down services..." -ForegroundColor Yellow
    # Kill by port to be sure
    foreach ($port in $ports) {
        $proc = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "[DONE] Goodbye!" -ForegroundColor Green
    exit
}

# Register Ctrl+C handler
[console]::TreatControlCAsInput = $false
[void][System.Console]::add_CancelKeyPress({ Cleanup })

# 1. Basic Checks
try {
    python --version | Out-Null
    npm --version | Out-Null
} catch {
    Write-Error "Python or Node.js missing. Please install them."
    exit
}

# 2. Venv
if (-not (Test-Path "venv")) {
    Write-Host "[CONFIG] Creating venv..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "[CONFIG] Syncing dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
pip install -r web\backend\requirements.txt

# 3. GPU Check
Write-Host "[CONFIG] Checking GPU..." -ForegroundColor Yellow
$cudaAvailable = python -c "import torch; print(torch.cuda.is_available())"
if ($cudaAvailable -eq "False") {
    Write-Host "[WARN] No CUDA detected." -ForegroundColor Red
    nvidia-smi | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[REPAIR] NVIDIA GPU found! Installing CUDA torch..." -ForegroundColor Green
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 --force-reinstall
    }
} else {
    Write-Host "[SUCCESS] GPU is ready." -ForegroundColor Green
}

# 4. Frontend Install Check
if (-not (Test-Path "web\frontend\node_modules")) {
    Write-Host "[CONFIG] Installing frontend modules..." -ForegroundColor Yellow
    Push-Location web\frontend
    npm install
    Pop-Location
}

# 5. Start Backend
Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "      Starting Backend...                " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

Start-Process python -ArgumentList "web\backend\server.py" -NoNewWindow

Write-Host "Waiting for Backend models to load..." -ForegroundColor Yellow

# 6. Wait for Backend Ready
while ($true) {
    try {
        $statusResponse = Invoke-RestMethod -Uri "http://127.0.0.1:5000/status" -ErrorAction SilentlyContinue
        if ($statusResponse.status -eq "ready") {
            Write-Host "`n[SUCCESS] Backend is ready!" -ForegroundColor Green
            break
        }
    } catch {}
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 3
}

# 7. Start Frontend
Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "      Starting Frontend UI...            " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

Push-Location web\frontend
Start-Process cmd -ArgumentList "/c npm run dev" -NoNewWindow
Pop-Location

Write-Host "`nPic2Pic is now fully operational!" -ForegroundColor Green
Write-Host "Access URL: http://localhost:5173" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop all services."
Write-Host "=========================================" -ForegroundColor Cyan

# Keep alive loop
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Cleanup
}
