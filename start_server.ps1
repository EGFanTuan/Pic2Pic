#!/usr/bin/env pwsh

# Pic2Pic startup script
# Starts both backend and frontend servers without opening new windows

Write-Host "=====================================" -ForegroundColor Green
Write-Host "Pic2Pic Startup Script" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Set environment variable to resolve OpenMP conflict
Write-Host "Setting environment variables..." -ForegroundColor Yellow
[System.Environment]::SetEnvironmentVariable('KMP_DUPLICATE_LIB_OK', 'TRUE', 'Process')
Write-Host "Environment variables set successfully" -ForegroundColor Green

# Start backend server as a background job
Write-Host "Starting backend server..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    cd "$using:PSScriptRoot"
    python server.py
}

# Wait for backend server to start
Write-Host "Waiting for backend server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check backend server status
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/status" -TimeoutSec 10
    Write-Host "Backend server started successfully!" -ForegroundColor Green
} catch {
    Write-Host "Backend server failed to start, please check logs" -ForegroundColor Red
    Receive-Job $backendJob
    Remove-Job $backendJob
    exit 1
}

# Start frontend development server as a background job
Write-Host "Starting frontend development server..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    cd "$using:PSScriptRoot\web"
    npm run dev
}

# Wait for frontend server to start
Write-Host "Waiting for frontend development server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Display startup information
Write-Host "" -ForegroundColor White
Write-Host "=====================================" -ForegroundColor Green
Write-Host "🎉 Services started successfully!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Backend server: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Frontend development server: http://localhost:5173" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "📝 Usage instructions:" -ForegroundColor Yellow
Write-Host "1. Open browser and visit http://localhost:5173" -ForegroundColor White
Write-Host "2. Draw content on the canvas" -ForegroundColor White
Write-Host "3. Select style and parameters" -ForegroundColor White
Write-Host "4. Click generate button" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "🔧 Stop services:" -ForegroundColor Yellow
Write-Host "- Press Ctrl+C to stop both servers" -ForegroundColor White
Write-Host "" -ForegroundColor White

# Monitor jobs and handle cleanup
Write-Host "Press Ctrl+C to stop services..." -ForegroundColor Yellow
try {
    while ($true) {
        Start-Sleep -Seconds 1
        
        # Check if backend job is still running
        if ($backendJob.State -eq 'Failed') {
            Write-Host "Backend server failed, checking logs..." -ForegroundColor Red
            Receive-Job $backendJob
            break
        }
        
        # Check if frontend job is still running
        if ($frontendJob.State -eq 'Failed') {
            Write-Host "Frontend server failed, checking logs..." -ForegroundColor Red
            Receive-Job $frontendJob
            break
        }
    }
} finally {
    # Clean up jobs
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Remove-Job $backendJob -Force -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -Force -ErrorAction SilentlyContinue
    Write-Host "Services stopped." -ForegroundColor Green
}
