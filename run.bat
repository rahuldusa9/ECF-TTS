@echo off
echo ========================================
echo    TTS Studio Setup and Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [2/3] Dependencies installed successfully
echo [3/3] Starting TTS Studio...
echo.
echo ========================================
echo Server will start at: http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

pause
