@echo off
setlocal
cd /d "%~dp0"
title Next Toppers Inventory - Start Local Test

if not exist ".venv\Scripts\waitress-serve.exe" (
    echo Application is not installed yet.
    echo First double-click INSTALL_LOCAL_TEST.bat
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%P in ('powershell -NoProfile -Command "(Get-NetTCPConnection -LocalPort 3458 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess)"') do set APPPID=%%P
if defined APPPID (
    echo Application is already running.
    start "" "http://localhost:3458"
    exit /b 0
)

echo Starting Next Toppers Inventory on http://localhost:3458
start "Next Toppers Inventory Server" powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_windows.ps1"

timeout /t 5 /nobreak >nul
start "" "http://localhost:3458"

echo.
echo Browser opened. Keep the server window open while testing.
timeout /t 3 /nobreak >nul
