@echo off
setlocal enabledelayedexpansion
title AutoTyper Sender (Laptop 1)
cd /d "%~dp0"

echo ============================================================
echo         AutoTyper - Send Code to Laptop 2 (Sender)
echo ============================================================
echo.

set "ROOM=autotyper-pichipuk-sync"
set "CODEFILE=code.txt"

:: If a file was dragged onto this batch file, use it directly
if not "%~1"=="" (
    set "CODEFILE=%~1"
    goto :DO_SEND
)

:: If code.txt doesn't exist, create a template
if not exist "%CODEFILE%" (
    echo # Paste your code here and save this file. > "%CODEFILE%"
    echo def solve(): >> "%CODEFILE%"
    echo     print("Code sent from Laptop 1!") >> "%CODEFILE%"
)

echo Opening "%CODEFILE%" in Notepad...
echo 1. Paste your code into Notepad
echo 2. Press Ctrl+S to save
echo 3. Close Notepad to send to Laptop 2
echo.
start /wait notepad "%CODEFILE%"

:DO_SEND
echo.
echo [1/2] Sending code to Cloud Room: %ROOM% ...

:: Find Python
set "PY_CMD="
if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if not errorlevel 1 set "PY_CMD=python"
)

if defined PY_CMD (
    "%PY_CMD%" autotyper.py send "%CODEFILE%" --room "%ROOM%"
) else (
    powershell -NoProfile -Command "$content = Get-Content -Raw -Encoding UTF8 '%CODEFILE%'; Invoke-RestMethod -Uri 'https://ntfy.sh/%ROOM%?title=AutoTyper+Code' -Method Post -Body $content; Write-Host 'Code delivered successfully!'"
)

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to send code. Please check your internet connection.
) else (
    echo.
    echo ============================================================
    echo [SUCCESS] Code delivered to Laptop 2!
    echo Laptop 2 has loaded this code and is ready.
    echo On Laptop 2: Click inside the target window and press F8!
    echo ============================================================
)

echo.
pause
