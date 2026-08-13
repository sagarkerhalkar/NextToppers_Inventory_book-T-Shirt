@echo off
setlocal
cd /d "%~dp0"
title Next Toppers Inventory - Install Local Test

echo ============================================================
echo   NEXT TOPPERS INVENTORY - LOCAL TEST INSTALLATION
echo ============================================================
echo.
echo This will install the application on this computer.
echo Internet is required only during the first installation.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_windows.ps1"
if errorlevel 1 (
    echo.
    echo INSTALLATION FAILED.
    echo Please take a screenshot of this window and send it in chat.
    pause
    exit /b 1
)

echo.
echo INSTALLATION COMPLETED SUCCESSFULLY.
echo Now double-click START_LOCAL_TEST.bat
echo.
pause
