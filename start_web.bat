@echo off
echo Starting YouTube Scraper Translator Web UI...
echo.

:: Check for node_modules
if not exist "frontend\node_modules\" (
    echo Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
)

:: Start Backend in background
echo [1/2] Starting FastAPI Backend on port 8000...
start cmd /c "python server.py"

:: Wait 2 seconds
timeout /t 2 /nobreak > nul

:: Start Frontend
echo [2/2] Starting Vite Frontend on port 5173...
cd frontend
npm run dev
