@echo off
title Next Toppers Inventory - Enable LAN Access
echo ============================================================
echo   NEXT TOPPERS INVENTORY - ENABLE LAN ACCESS
echo ============================================================
echo.
echo This will open Windows Firewall port 3458 and show the
echo server IP address for phones, tablets and other computers.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\enable_lan_access.ps1"
if errorlevel 1 (
  echo.
  echo LAN SETUP FAILED.
  echo Take a screenshot of this window and send it in chat.
  pause
  exit /b 1
)
echo.
pause
