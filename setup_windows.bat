@echo off
REM Setup script for Windows

echo ======================================
echo   OTibia Bot - Windows Setup Script
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Checking Python version...
python --version

echo.
echo [2/3] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/3] Checking Tesseract OCR...

set TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
if exist "%TESSERACT_PATH%" (
    echo [OK] Tesseract OCR found at: %TESSERACT_PATH%
) else (
    echo [WARNING] Tesseract OCR not found at default location
    echo Please download and install from:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Default installation path should be:
    echo C:\Program Files\Tesseract-OCR\tesseract.exe
)

echo.
echo ======================================
echo Setup complete!
echo ======================================
echo.
echo To run the bot:
echo   python StartBot.py
echo.
pause
