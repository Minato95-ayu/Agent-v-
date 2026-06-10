@echo off
title V - Autonomous AI Assistant
cd /d "%~dp0"

echo ============================================
echo        V - Autonomous AI Assistant
echo        Starting all systems...
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.11+
    pause
    exit /b 1
)

REM Launch V (pythonw = no console window for clean background run)
REM Use python instead of pythonw for debugging (shows console output)
python launcher.py

echo.
echo V has shut down.
pause
