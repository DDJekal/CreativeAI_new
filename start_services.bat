@echo off
echo ========================================
echo   CreativeAI - Backend + Frontend
echo ========================================
echo.

echo Starting Backend API on Port 8000...
start cmd /k "cd /d %~dp0 && python src/api/main.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend on Port 3000...
start cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ========================================
echo   Services gestartet!
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo ========================================
echo.
pause
