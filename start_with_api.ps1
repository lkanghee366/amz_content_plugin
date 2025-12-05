# PowerShell Startup script for Amazon Content Poster with ChatZai API
# This script starts the ChatZai API server and then the Python poster

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Amazon Content Poster Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Node.js and Python found" -ForegroundColor Green
Write-Host ""

# Check if chat_zai_api_playwright.js exists
if (-not (Test-Path "chat_zai_api_playwright.js")) {
    Write-Host "[ERROR] chat_zai_api_playwright.js not found" -ForegroundColor Red
    Write-Host "Please ensure the API file is in the current directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/3] Starting ChatZai API server..." -ForegroundColor Yellow
Write-Host "Starting Node.js server on http://localhost:3001" -ForegroundColor Gray
Write-Host ""

# Start the API server in background
$apiProcess = Start-Process -FilePath "node" -ArgumentList "chat_zai_api_playwright.js" -PassThru -WindowStyle Normal

# Wait for the server to start
Start-Sleep -Seconds 3

# Health check loop
$attempts = 0
$maxAttempts = 10
$serverReady = $false

while ($attempts -lt $maxAttempts) {
    $attempts++
    Write-Host "[$attempts/$maxAttempts] Checking API health..." -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3001/health" -TimeoutSec 2 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] ChatZai API server is healthy and ready!" -ForegroundColor Green
            Write-Host ""
            $serverReady = $true
            break
        }
    }
    catch {
        # Server not ready yet
    }
    
    Start-Sleep -Seconds 2
}

if (-not $serverReady) {
    Write-Host "[ERROR] API server failed to start after $maxAttempts attempts" -ForegroundColor Red
    Write-Host "Please check the API server for errors" -ForegroundColor Yellow
    Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[2/3] ChatZai API server is running" -ForegroundColor Green
Write-Host ""
Write-Host "[3/3] Starting Python poster..." -ForegroundColor Yellow
Write-Host ""

# Run the Python poster
python main.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Python poster finished" -ForegroundColor Cyan
Write-Host ""
Write-Host "Stopping ChatZai API server..." -ForegroundColor Yellow
Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
Write-Host "API server stopped" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
