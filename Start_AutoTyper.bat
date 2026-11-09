@echo off
set "SCRIPT_PATH=%~dp0autotyper.py"
if not exist "%SCRIPT_PATH%" set "SCRIPT_PATH=C:\AHI\autotyper.py"

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%SCRIPT_PATH%" %*
) else (
    python "%SCRIPT_PATH%" %*
)
pause
