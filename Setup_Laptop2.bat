@echo off
title AutoTyper One-Time Setup
echo ============================================================
echo           AutoTyper - One-Time Setup for Laptop 2
echo ============================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your PATH!
    echo.
    echo Please do the following:
    echo 1. Download Python from https://www.python.org/downloads/
    echo 2. Run the installer and MUST CHECK: "Add python.exe to PATH"
    echo 3. Re-run this Setup script after installing.
    echo.
    pause
    exit /b 1
)

echo Python is detected:
python --version
echo.
echo Installing required library (pynput)...
echo.

python -m pip install --upgrade pip >nul 2>&1
python -m pip install pynput

if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Could not install pynput automatically.
    echo Please make sure you are connected to the internet and try again.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [SUCCESS] Setup is complete!
echo.
echo You can now double-click "Start_AutoTyper.bat" anytime.
echo ============================================================
echo.
pause
