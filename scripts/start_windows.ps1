$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path ".venv\Scripts\waitress-serve.exe")) { throw "Run scripts\setup_windows.ps1 first." }

$PublicAddress = "156.156.40.51"
$PublicPort = 3458
$BackendPort = 3460

Write-Host ""
Write-Host "Next Toppers Inventory backend is starting behind Microsoft IIS..." -ForegroundColor Cyan
Write-Host "User address: http://${PublicAddress}:$PublicPort" -ForegroundColor Green
Write-Host "Private backend: http://127.0.0.1:$BackendPort" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Keep this window open only when automatic startup is disabled." -ForegroundColor Yellow
Write-Host "IIS must already be installed by the combined IIS deployment package." -ForegroundColor DarkGray
Write-Host ""

$Existing = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
if ($Existing) {
    Write-Host "The private backend is already running." -ForegroundColor Green
    exit 0
}

& .\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:$BackendPort --threads=8 --channel-timeout=120 nexttoppers_inventory.wsgi:application
