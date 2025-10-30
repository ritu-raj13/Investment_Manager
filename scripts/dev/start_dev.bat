@echo off
REM Investment Manager - Quick Start (Desktop Shortcut Compatible)
REM This file is in scripts/dev/ folder

title Investment Manager Launcher

REM Get script directory and navigate to project root (2 levels up)
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%..\.."

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   Investment Manager - Starting App...      ║
echo  ╚══════════════════════════════════════════════╝
echo.

REM Validate directories exist
if not exist "backend\app.py" (
    color 0C
    echo [ERROR] Cannot find backend\app.py
    echo Please make sure this script is in Investment_Manager\scripts\dev\ folder.
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    color 0C
    echo [ERROR] Cannot find frontend\package.json
    echo Please make sure this script is in Investment_Manager\scripts\dev\ folder.
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "backend\venv\Scripts\python.exe" (
    color 0E
    echo [WARNING] Virtual environment not found!
    echo Please run: cd backend ^&^& python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "frontend\node_modules" (
    color 0E
    echo [WARNING] Node modules not found!
    echo Please run: cd frontend ^&^& npm install
    echo.
    pause
    exit /b 1
)

color 0A
echo [✓] Backend found
echo [✓] Frontend found
echo [✓] Virtual environment ready
echo [✓] Node modules ready
echo.

REM Start Backend in background (same window)
echo ┌─────────────────────────────────────┐
echo │  Starting Backend Server...         │
echo └─────────────────────────────────────┘
echo.

REM Navigate to backend and start server in background
cd /d "%CD%\backend"
call venv\Scripts\activate

echo [✓] Virtual environment activated
echo [✓] Starting Flask backend in background...
echo.

REM Set environment variables and start backend with logs visible
set FLASK_ENV=development

REM Start backend in new window (visible for debugging)
start "Backend Server" python app.py

REM Wait for backend to initialize
echo Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak > nul

REM Navigate to frontend
cd /d "%CD%\..\frontend"

echo.
echo ┌─────────────────────────────────────┐
echo │  Starting Frontend (React)...       │
echo └─────────────────────────────────────┘
echo.

REM Success message
color 0B
echo ═══════════════════════════════════════════════════════
echo   Investment Manager Starting! 
echo ═══════════════════════════════════════════════════════
echo.
echo  📊 Application URLs:
echo     • Backend API:  http://127.0.0.1:5000
echo     • Frontend UI:  http://localhost:3000
echo.
echo  🔐 Login Credentials:
echo     • Check backend/.env file
echo     • Default: admin / changeme
echo.
echo  ℹ️  Servers running in separate windows:
echo     • Backend: Check "Backend Server" window for logs
echo     • Frontend: Starting in THIS window (browser will open)
echo.
echo  ⚠️  IMPORTANT: Keep BOTH windows open!
echo     Press Ctrl+C in each window to stop servers.
echo.
echo ═══════════════════════════════════════════════════════
echo.

REM Start frontend in foreground (blocks until stopped)
npm start

