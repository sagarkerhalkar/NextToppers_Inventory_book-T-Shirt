$ErrorActionPreference = "Stop"
$AppRoot = Split-Path $PSScriptRoot -Parent
Set-Location $AppRoot
Write-Host "Stopping local server on port 3458..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 3458 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (Test-Path "db.sqlite3") { New-Item -ItemType Directory -Path "backups" -Force | Out-Null; Copy-Item "db.sqlite3" "backups\before_phase3_$Stamp.sqlite3" -Force; Write-Host "Database backup created." -ForegroundColor Green }
$TempRoot = Join-Path $env:TEMP "NextToppersInventoryUpdate_$Stamp"
$ZipPath = "$TempRoot.zip"
$ExtractPath = "$TempRoot-extracted"
Invoke-WebRequest "https://github.com/sagarkerhalkar/NextToppers_Inventory_book-T-Shirt/archive/refs/heads/agent/initial-django-build.zip" -OutFile $ZipPath
Expand-Archive -Path $ZipPath -DestinationPath $ExtractPath -Force
$Source = Get-ChildItem $ExtractPath -Directory | Select-Object -First 1
if (-not $Source) { throw "Downloaded update package could not be opened." }
Write-Host "Copying updated application files while preserving your database and uploads..." -ForegroundColor Cyan
$Arguments = @($Source.FullName, $AppRoot, "/E", "/R:2", "/W:2", "/XD", ".venv", "media", "backups", "staticfiles", ".git", "/XF", "db.sqlite3", ".env")
& robocopy @Arguments | Out-Null
if ($LASTEXITCODE -ge 8) { throw "File update failed with Robocopy code $LASTEXITCODE." }
if (-not (Test-Path ".venv\Scripts\python.exe")) { throw "Local Python environment is missing. Run INSTALL_LOCAL_TEST.bat." }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip uninstall -y chardet 2>$null
& .\.venv\Scripts\python.exe manage.py makemigrations inventory --noinput
& .\.venv\Scripts\python.exe manage.py migrate --noinput
& .\.venv\Scripts\python.exe manage.py migrate_legacy_employees
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput
& .\.venv\Scripts\python.exe manage.py check
Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
Remove-Item $ExtractPath -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Phase 3 update installed. Existing database, media and login account were preserved." -ForegroundColor Green
