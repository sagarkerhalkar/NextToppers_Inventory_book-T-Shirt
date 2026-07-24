@echo off
setlocal
title Next Toppers Inventory - IIS Local Server
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { Start-Process '%~f0' -Verb RunAs; exit } else { & '%~dp0scripts\install_iis_reverse_proxy.ps1' -PublicIp '156.156.40.51' -PublicPort 3458 -BackendPort 3460 }"
if errorlevel 1 (
  echo.
  echo IIS SETUP FAILED.
  pause
  exit /b 1
)
echo.
echo IIS LOCAL SERVER SETUP COMPLETED.
pause
