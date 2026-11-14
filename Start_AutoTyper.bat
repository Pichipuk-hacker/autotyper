@echo off
title AutoTyper Launcher
set "SCRIPT_PATH=%~dp0autotyper.py"
if not exist "%SCRIPT_PATH%" set "SCRIPT_PATH=C:\AHI\autotyper.py"

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ============================================================
    echo [ERROR] Python is not installed or not in your PATH!
    echo ============================================================
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo CRITICAL: Tick the box "Add python.exe to PATH" during install.
    echo ============================================================
    pause
    exit /b 1
)

:: 2. Auto-install pynput on first run if missing
python -c "import pynput" >nul 2>&1
if %errorlevel% neq 0 (
    echo ============================================================
    echo [AutoTyper] First-time setup detected.
    echo Installing required library (pynput)... Please wait...
    echo ============================================================
    python -m pip install pynput
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pynput. Please check your internet connection.
        pause
        exit /b 1
    )
    echo.
    echo [AutoTyper] Installation successful! Starting AutoTyper now...
    echo.
)

:: 3. Launch the AutoTyper
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%SCRIPT_PATH%" %*
) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%SCRIPT_PATH%" %*
) else (
    python "%SCRIPT_PATH%" %*
)
pause
