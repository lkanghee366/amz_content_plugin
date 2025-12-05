@echo off
REM Startup script for Amazon Content Poster with ChatZai API
REM This script starts the ChatZai API server and then the Python poster

echo ========================================
echo Amazon Content Poster Startup Script
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Node.js and Python found
echo.

REM Check if chat_zai_api_playwright.js exists
if not exist "chat_zai_api_playwright.js" (
    echo [ERROR] chat_zai_api_playwright.js not found
    echo Please ensure the API file is in the current directory
    pause
    exit /b 1
)

echo [1/3] Starting ChatZai API server...
echo Starting Node.js server on http://localhost:3001
echo.

REM Start the API server in a new window
start "ChatZai API Server" cmd /k "node chat_zai_api_playwright.js"

REM Wait for the server to start
echo Waiting for API server to be ready...
timeout /t 3 /nobreak >nul

REM Health check loop
set /a attempts=0
set /a max_attempts=10

:healthcheck
set /a attempts+=1
echo [%attempts%/%max_attempts%] Checking API health...

REM Use PowerShell to check HTTP endpoint
powershell -Command "$response = try { Invoke-WebRequest -Uri 'http://localhost:3001/health' -TimeoutSec 2 -UseBasicParsing; $response.StatusCode } catch { 0 }; exit $response" >nul 2>nul

if %errorlevel% equ 200 (
    echo [OK] ChatZai API server is healthy and ready!
    echo.
    goto :start_python
)

if %attempts% geq %max_attempts% (
    echo [ERROR] API server failed to start after %max_attempts% attempts
    echo Please check the ChatZai API Server window for errors
    pause
    exit /b 1
)

timeout /t 2 /nobreak >nul
goto :healthcheck

:start_python
echo [2/3] ChatZai API server is running
echo.
echo [3/3] Starting Python poster...
echo.

REM Run the Python poster
python main.py

echo.
echo ========================================
echo Python poster finished
echo.
echo The ChatZai API server is still running in the background
echo You can close it manually or it will close when you close this window
echo ========================================
pause
