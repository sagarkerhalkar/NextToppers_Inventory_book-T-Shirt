@echo off
setlocal
cd /d "%~dp0"
title Next Toppers Inventory - Verify Local Test

if not exist ".venv\Scripts\python.exe" (
    echo Application is not installed yet.
    echo First double-click INSTALL_LOCAL_TEST.bat
    echo.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\verify_installation.ps1"
if errorlevel 1 (
    echo.
    echo VERIFICATION FAILED.
    echo Please take a screenshot of this window and send it in chat.
    pause
    exit /b 1
)

echo.
echo ALL LOCAL TEST CHECKS PASSED.
pause
