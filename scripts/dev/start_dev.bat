@echo off
REM Development startup script for Investment Manager (Windows)

echo ========================================
echo Investment Manager - Development Mode
echo ========================================
echo.

cd backend

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Set development environment variables
echo Setting development environment...
set FLASK_ENV=development
set SECRET_KEY=dev-secret-key-for-testing
set ADMIN_USERNAME=admin
set ADMIN_PASSWORD=admin123

echo.
echo Starting Flask backend (development mode)...
echo Backend will run on http://127.0.0.1:5000
echo.
echo To start frontend, open another terminal and run:
echo   cd frontend
echo   npm start
echo.
echo Login: admin / admin123
echo.

python app.py

