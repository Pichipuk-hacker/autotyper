@echo off
title AutoTyper One-Time Setup
cd /d "%~dp0"
echo ============================================================
echo           AutoTyper - One-Time Setup for Laptop 2
echo ============================================================
echo.

set "PY_CMD="

REM Check local virtualenv
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0.venv\Scripts\python.exe"
    goto :found_python
)

REM Check python on system PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :found_python
)

REM Check py launcher on system PATH
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :found_python
)

REM Search common Windows Python install folders
for %%V in (313 312 311 310 39) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :found_python
    )
    if exist "C:\Python%%V\python.exe" (
        set "PY_CMD=C:\Python%%V\python.exe"
        goto :found_python
    )
    if exist "%ProgramFiles%\Python%%V\python.exe" (
        set "PY_CMD=%ProgramFiles%\Python%%V\python.exe"
        goto :found_python
    )
)

:not_found
echo ============================================================
echo [ERROR] Python is not installed or not in your PATH!
echo ============================================================
echo 1. Download Python 3.10+ from https://www.python.org/downloads/
echo 2. During install, tick the checkbox: Add python.exe to PATH
echo ============================================================
echo.
pause
exit /b 1

:found_python
echo Python detected: %PY_CMD%
echo.
echo Installing required library pynput... Please wait...
echo.

"%PY_CMD%" -m pip install pynput

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install pynput. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [SUCCESS] Setup is complete!
echo You can now double-click Start_AutoTyper.bat anytime.
echo ============================================================
echo.
pause
