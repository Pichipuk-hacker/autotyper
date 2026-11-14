@echo off
title AutoTyper Launcher
cd /d "%~dp0"

REM 1. Find Python executable
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
echo [ERROR] Python was not found on this computer!
echo ============================================================
echo Please install Python 3.10+ from:
echo https://www.python.org/downloads/
echo.
echo CRITICAL: During installation, tick the checkbox:
echo   [x] "Add python.exe to PATH"
echo ============================================================
echo.
pause
exit /b 1

:found_python
echo [AutoTyper] Using Python: %PY_CMD%

REM 2. Check if autotyper.py exists in the current folder
if not exist "%~dp0autotyper.py" (
    echo ============================================================
    echo [ERROR] autotyper.py was not found in this folder!
    echo ============================================================
    echo Did you extract the ZIP file?
    echo You cannot run this directly from inside the ZIP file.
    echo Please right-click the downloaded ZIP and select Extract All.
    echo ============================================================
    echo.
    pause
    exit /b 1
)

REM 3. Check if pynput is installed, auto-install if missing
"%PY_CMD%" -c "import pynput" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo [AutoTyper] First-time setup detected.
    echo Installing required library pynput... Please wait...
    echo ============================================================
    "%PY_CMD%" -m pip install pynput
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Could not install pynput automatically.
        echo Please check your internet connection or run:
        echo   %PY_CMD% -m pip install pynput
        echo ============================================================
        echo.
        pause
        exit /b 1
    )
    echo [AutoTyper] pynput installed successfully!
    echo.
)

REM 4. Launch AutoTyper
echo [AutoTyper] Starting AutoTyper...
echo.
"%PY_CMD%" "%~dp0autotyper.py" %*
if %errorlevel% neq 0 (
    echo.
    echo [AutoTyper] Process stopped or exited with code %errorlevel%.
)
pause
