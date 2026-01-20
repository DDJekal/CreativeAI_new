@echo off
REM HOC API Explorer - Quick Setup & Run
REM Windows Batch Script

echo ========================================
echo HOC API Explorer - Setup
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create venv
        pause
        exit /b 1
    )
    echo     - venv created
) else (
    echo [1/3] Virtual environment exists - skipping
)

echo.
echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install --quiet httpx python-dotenv
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo     - httpx installed
echo     - python-dotenv installed

echo.
echo [3/3] Checking .env file...
if not exist ".env" (
    echo WARNING: .env file not found!
    echo.
    echo Please create .env with:
    echo   HIRINGS_API_URL=https://...
    echo   HIRINGS_API_TOKEN=your_token_here
    echo.
    pause
    exit /b 1
)
echo     - .env exists

echo.
echo ========================================
echo Ready to explore!
echo ========================================
echo.
echo Running exploration script...
echo.

python scripts\explore_hoc_api.py

echo.
echo ========================================
echo Exploration complete!
echo ========================================
echo.
echo Check results:
echo   - docs\01_text_api_integration.md
echo   - docs\01_text_api_exploration_results.json
echo.
pause

