@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo   NEXT TOPPERS INVENTORY - SAFE LOCAL UPDATE
echo ============================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\update_local_test.ps1"
if errorlevel 1 (
  echo.
  echo UPDATE FAILED. Send a screenshot of this window in chat.
  pause
  exit /b 1
)
echo.
echo UPDATE COMPLETED SUCCESSFULLY.
echo Double-click START_LOCAL_TEST.bat.
pause
