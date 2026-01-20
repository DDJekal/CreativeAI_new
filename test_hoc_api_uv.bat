@echo off
REM Test HOC API Client mit uv
REM Nutzt automatisch .venv aus pyproject.toml

echo ========================================
echo HOC API Client Test (uv)
echo ========================================
echo.

REM Check if .venv exists
if not exist ".venv\" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Run setup first:
    echo   setup_uv.bat
    echo.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo.
    echo Create .env with:
    echo   HIRINGS_API_URL=https://...
    echo   HIRINGS_API_TOKEN=your_token_here
    echo.
    pause
    exit /b 1
)

echo [Running Test]
echo Using: .venv from pyproject.toml
echo.

REM uv run nutzt automatisch die .venv
uv run python scripts\test_hoc_api_client.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo Test failed!
    echo ========================================
    echo.
    echo Check:
    echo   - .env has correct credentials
    echo   - API is reachable
    echo   - Token is valid
    echo.
) else (
    echo.
    echo ========================================
    echo Test complete!
    echo ========================================
    echo.
)

pause

