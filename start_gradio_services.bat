@echo off
echo ========================================
echo   CreativeAI - Backend + Gradio Frontend
echo ========================================
echo.

echo Starting Backend API on Port 8000...
start cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 5 /nobreak >nul

echo Starting Gradio Frontend on Port 7870...
start cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python gradio_app.py"

echo.
echo ========================================
echo   Services gestartet!
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:7870
echo ========================================
echo.
pause
