$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path ".venv\Scripts\waitress-serve.exe")) { throw "Run scripts\setup_windows.ps1 first." }
& .\.venv\Scripts\waitress-serve.exe --listen=0.0.0.0:3458 nexttoppers_inventory.wsgi:application
