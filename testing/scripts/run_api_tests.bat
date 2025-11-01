@echo off
REM API Test Runner for Investment Manager (Windows)
REM Tests all API endpoints and generates date-wise report

echo =========================================
echo Investment Manager - API Test Suite
echo Phase 4: Comprehensive API Testing
echo =========================================
echo.

REM Get to project root directory
cd /d "%~dp0\..\.."

REM Check if backend venv exists
if not exist "backend\venv\Scripts\activate.bat" (
    echo ERROR: Backend virtual environment not found!
    echo Please create backend venv first:
    echo   cd backend
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    exit /b 1
)

REM Activate backend virtual environment
echo Activating backend virtual environment...
call backend\venv\Scripts\activate.bat

REM Navigate to testing directory
cd testing

REM Check if pytest is installed in venv
python -m pytest --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing test dependencies in venv...
    pip install -r requirements.txt
)

echo Running API Tests...
echo.

REM Run all API tests
python -m pytest tests\test_all_apis_part1.py tests\test_all_apis_part2.py tests\test_all_apis_part3.py ^
    -c config\pytest.ini ^
    -v ^
    --tb=short ^
    > reports\test_run_raw.log 2>&1

set TEST_RESULT=%errorlevel%

REM Display the output
type reports\test_run_raw.log

echo.
echo =========================================

if %TEST_RESULT% equ 0 (
    echo All API tests passed!
) else (
    echo Some tests had issues
)

echo =========================================
echo.

REM Update TEST_REPORTS.md with results
echo Updating test report...
python scripts\update_test_report.py

echo.
echo Test Results saved to: reports\test_run_raw.log
echo Report updated in: reports\TEST_REPORTS.md
echo.

REM Deactivate virtual environment
call deactivate

REM Return to project root
cd ..

exit /b %TEST_RESULT%

