$ErrorActionPreference = "Stop"
$AppRoot = Split-Path $PSScriptRoot -Parent
$LogRoot = Join-Path $env:LOCALAPPDATA "NextToppersInventory\logs"
New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
$LogFile = Join-Path $LogRoot "server.log"
$BackendPort = 3460

# Google Drive and network folders may take a little time to become available after login.
for ($attempt = 1; $attempt -le 18; $attempt++) {
    if ((Test-Path (Join-Path $AppRoot "manage.py")) -and (Test-Path (Join-Path $AppRoot ".venv\Scripts\waitress-serve.exe"))) {
        break
    }
    Start-Sleep -Seconds 10
}

if (-not (Test-Path (Join-Path $AppRoot ".venv\Scripts\waitress-serve.exe"))) {
    "$(Get-Date -Format s) - Auto-start failed: application or virtual environment unavailable." | Out-File $LogFile -Append
    exit 1
}

$Existing = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
if ($Existing) {
    "$(Get-Date -Format s) - Backend already running on 127.0.0.1:$BackendPort." | Out-File $LogFile -Append
    exit 0
}

Set-Location $AppRoot
"$(Get-Date -Format s) - Starting private Next Toppers backend on 127.0.0.1:$BackendPort for IIS." | Out-File $LogFile -Append
& .\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:$BackendPort --threads=8 --channel-timeout=120 nexttoppers_inventory.wsgi:application *>> $LogFile
