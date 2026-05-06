@echo off
echo ===================================================
echo   CampusGate Setup - NIT Jalandhar Edition
echo ===================================================
echo.

echo [1/3] Removing old database to avoid conflicts...
if exist campus.db del campus.db

echo [2/3] Seeding database with default NIT Jalandhar students...
set PYTHONIOENCODING=utf-8
python seed_data.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to seed the database!
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Starting the FastAPI server...
python -m uvicorn main:app --host 0.0.0.0 --port 8001

pause
