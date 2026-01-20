@echo off
REM CreativeAI2 Setup mit uv
REM Installiert alle Dependencies aus pyproject.toml

echo ========================================
echo CreativeAI2 Setup (uv + pyproject.toml)
echo ========================================
echo.

REM Check if uv is installed
where uv >nul 2>nul
if errorlevel 1 (
    echo ERROR: uv not found!
    echo.
    echo Install uv first:
    echo   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    echo Or via pip:
    echo   pip install uv
    echo.
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
uv venv
if errorlevel 1 (
    echo ERROR: Failed to create venv
    pause
    exit /b 1
)
echo     - .venv created

echo.
echo [2/3] Installing dependencies from pyproject.toml...
echo     (This may take a moment on first run)
echo.
uv sync
if errorlevel 1 (
    echo ERROR: Failed to sync dependencies
    pause
    exit /b 1
)
echo     - All dependencies installed

echo.
echo [3/3] Checking .env file...
if not exist ".env" (
    echo WARNING: .env file not found!
    echo.
    echo Please create .env with:
    echo   HIRINGS_API_URL=https://...
    echo   HIRINGS_API_TOKEN=your_token_here
    echo   OPENAI_API_KEY=sk-...
    echo   BFL_API_KEY=...
    echo   PERPLEXITY_API_KEY=pplx-...
    echo   FIRECRAWL_API_KEY=fc-...
    echo.
    pause
    exit /b 1
)
echo     - .env exists

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Lock file: uv.lock (committed to git)
echo Virtual env: .venv\ (not in git)
echo.
echo Next steps:
echo   1. Test API: test_hoc_api_uv.bat
echo   2. Activate venv: .venv\Scripts\activate
echo   3. Run scripts: uv run python scripts\...
echo.
pause

