@echo off
REM Investment Manager - Verbose Mode (Shows Backend Logs in Same Window)
REM This file is in scripts/dev/ folder

title Investment Manager - Verbose Mode

REM Get script directory and navigate to project root (2 levels up)
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%..\.."

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   Investment Manager - Verbose Mode         ║
echo  ╚══════════════════════════════════════════════╝
echo.

REM Validate directories exist
if not exist "backend\app.py" (
    color 0C
    echo [ERROR] Cannot find backend\app.py
    pause
    exit /b 1
)

if not exist "backend\venv\Scripts\python.exe" (
    color 0E
    echo [WARNING] Virtual environment not found!
    pause
    exit /b 1
)

color 0A
echo [✓] Backend found
echo [✓] Virtual environment ready
echo.

REM Start Backend with logs visible
echo ┌─────────────────────────────────────┐
echo │  Starting Backend Server...         │
echo └─────────────────────────────────────┘
echo.

cd /d "%CD%\backend"
call venv\Scripts\activate

echo [✓] Virtual environment activated
echo.
echo ═══════════════════════════════════════════════════════
echo   Backend Running - Logs Visible Below
echo ═══════════════════════════════════════════════════════
echo.
echo  Backend API:  http://127.0.0.1:5000
echo.
echo  ⚠️  You'll need to start frontend separately:
echo     Open another terminal and run: cd frontend ^&^& npm start
echo.
echo  Press Ctrl+C to stop backend server.
echo.
echo ═══════════════════════════════════════════════════════
echo.

REM Set environment and run backend in foreground (logs visible)
set FLASK_ENV=development
python app.py

REM This line only executes if backend stops
echo.
echo Backend stopped.
pause

