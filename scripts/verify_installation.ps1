$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Virtual environment not found. Run scripts\setup_windows.ps1 first."
}

Write-Host "Running Django system check..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe manage.py check

Write-Host "Checking migrations..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
& .\.venv\Scripts\python.exe manage.py migrate --check

Write-Host "Running automated tests..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe manage.py test

Write-Host "Checking writable folders..." -ForegroundColor Cyan
foreach ($Folder in @("media", "backups", "staticfiles")) {
    if (-not (Test-Path $Folder)) { New-Item -ItemType Directory -Path $Folder | Out-Null }
    $Probe = Join-Path $Folder ".write_test"
    Set-Content -Path $Probe -Value "ok"
    Remove-Item $Probe -Force
}

Write-Host "Installation verification passed." -ForegroundColor Green
Write-Host "Start the app with scripts\start_windows.ps1 and open http://localhost:3458" -ForegroundColor Green
