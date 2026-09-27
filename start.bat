@echo off
cd /d "%~dp0"

start "Math Bank Backend" cmd /k "cd /d "%~dp0backend" && ..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

start "Math Bank Frontend" cmd /k "cd /d "%~dp0frontend" && npm install && npm run dev"

echo Open http://localhost:5173
pause