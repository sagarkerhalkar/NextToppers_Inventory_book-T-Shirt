@echo off
title Next Toppers Inventory - Disable Auto Start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\disable_auto_start.ps1"
if errorlevel 1 (
  echo.
  echo AUTO START REMOVAL FAILED.
  pause
  exit /b 1
)
echo.
pause
