Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "     Running Automated Tests           " -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# 1. Activate Venv
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Error "Virtual environment not found in venv\"
    pause
    exit
}
& ".\venv\Scripts\Activate.ps1"

# 2. Dependencies
Write-Host "[1/2] Installing testing dependencies..." -ForegroundColor Yellow
pip install -r test\requirements-test.txt

# 3. Pytest
Write-Host "[2/2] Executing Tests (Skipping slow real-model tests)..." -ForegroundColor Yellow
pytest test/ -v -m "not slow"

Write-Host "`nIf you want to run the slow real-model tests, run:"
Write-Host "pytest test/test_pipeline_real.py -v" -ForegroundColor Gray

Write-Host "`nPress any key to exit..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null
