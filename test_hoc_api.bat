@echo off
REM Test HOC API Client
REM Quick-Start für Testing

echo ========================================
echo HOC API Client Test
echo ========================================
echo.

REM Check venv
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Run: python -m venv venv
    pause
    exit /b 1
)

echo [1/2] Activating venv...
call venv\Scripts\activate.bat

echo.
echo [2/2] Running test...
echo.

python scripts\test_hoc_api_client.py

echo.
echo ========================================
echo Test complete!
echo ========================================
echo.
pause

