@echo off
title AutoTyper 1-Click Updater
cd /d "%~dp0"
echo ============================================================
echo           AutoTyper - 1-Click Automatic Updater
echo ============================================================
echo.
echo Fetching latest AutoTyper updates directly from GitHub...
echo.

powershell -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; try { Write-Host 'Downloading update package...'; Invoke-WebRequest -Uri 'https://github.com/Pichipuk-hacker/autotyper/archive/refs/heads/main.zip' -OutFile 'update_temp.zip'; Write-Host 'Extracting files...'; Expand-Archive -Path 'update_temp.zip' -DestinationPath 'update_temp_dir' -Force; Copy-Item -Path 'update_temp_dir\autotyper-main\*' -Destination '.' -Recurse -Force; Remove-Item 'update_temp.zip' -Force; Remove-Item 'update_temp_dir' -Recurse -Force; Write-Host 'SUCCESS' } catch { Write-Host 'ERROR:' $_.Exception.Message; exit 1 }"

if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo [ERROR] Could not update automatically.
    echo Please make sure you are connected to the internet.
    echo ============================================================
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [SUCCESS] AutoTyper has been updated to the latest version!
echo.
echo You can now double-click Start_AutoTyper.bat.
echo ============================================================
echo.
pause
