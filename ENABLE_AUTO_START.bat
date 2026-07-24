@echo off
title Next Toppers Inventory - Enable Auto Start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\enable_auto_start.ps1"
if errorlevel 1 (
  echo.
  echo AUTO START SETUP FAILED.
  pause
  exit /b 1
)
echo.
echo The server will start automatically after every Windows login.
pause
