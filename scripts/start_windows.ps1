$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path ".venv\Scripts\waitress-serve.exe")) { throw "Run scripts\setup_windows.ps1 first." }

$LanAddresses = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {
        $_.IPAddress -notlike "127.*" -and
        $_.IPAddress -notlike "169.254.*" -and
        $_.PrefixOrigin -ne "WellKnown"
    } |
    Select-Object -ExpandProperty IPAddress -Unique

Write-Host "" 
Write-Host "Next Toppers Inventory server is starting..." -ForegroundColor Cyan
Write-Host "This computer: http://localhost:3458" -ForegroundColor Green
foreach ($Address in $LanAddresses) {
    Write-Host "Other devices: http://${Address}:3458" -ForegroundColor Green
}
Write-Host "" 
Write-Host "Keep this window open while the application is in use." -ForegroundColor Yellow
Write-Host "Run ENABLE_LAN_ACCESS.bat once if another device cannot connect." -ForegroundColor DarkGray
Write-Host "" 

& .\.venv\Scripts\waitress-serve.exe --listen=0.0.0.0:3458 --threads=8 --channel-timeout=120 nexttoppers_inventory.wsgi:application
