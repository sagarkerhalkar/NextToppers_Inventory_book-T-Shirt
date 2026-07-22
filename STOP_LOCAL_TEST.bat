@echo off
setlocal
title Next Toppers Inventory - Stop Local Test

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$connections = Get-NetTCPConnection -LocalPort 3458 -State Listen -ErrorAction SilentlyContinue; if (-not $connections) { Write-Host 'Application is not running.' -ForegroundColor Yellow; exit 0 }; $connections | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue; Write-Host ('Stopped process ' + $_) -ForegroundColor Green }"

echo.
echo Next Toppers Inventory local server has been stopped.
pause
