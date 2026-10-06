$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
$BackupDir = Join-Path $Root "backups"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Source = Join-Path $Root "db.sqlite3"
if (-not (Test-Path $Source)) { throw "Database not found: $Source" }
$Destination = Join-Path $BackupDir "nexttoppers_inventory_$Timestamp.sqlite3"
Copy-Item $Source $Destination
Get-ChildItem $BackupDir -Filter "*.sqlite3" | Where-Object LastWriteTime -LT (Get-Date).AddDays(-30) | Remove-Item -Force
Write-Host "Backup created: $Destination"
