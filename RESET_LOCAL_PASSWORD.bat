@echo off
setlocal
cd /d "%~dp0"
cls
echo ============================================================
echo   NEXT TOPPERS INVENTORY - RESET LOCAL PASSWORD
echo ============================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\reset_local_password.ps1"
if errorlevel 1 (
  echo.
  echo PASSWORD RESET FAILED.
  echo Please take a screenshot of this window and send it in chat.
  pause
  exit /b 1
)
echo.
pause
