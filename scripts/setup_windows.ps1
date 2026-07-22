$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "Next Toppers Inventory - Windows Local Setup" -ForegroundColor Cyan
Write-Host "Application folder: $((Get-Location).Path)" -ForegroundColor DarkGray

if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Python Install Manager/Launcher is not installed. Install it from https://www.python.org/downloads/ and run this file again." }
function Test-PythonRuntime { param([string]$Selector); & cmd.exe /d /c "py $Selector -c ""import sys; print(sys.version)"" >nul 2>&1"; return ($LASTEXITCODE -eq 0) }
$PythonSelector = $null
foreach ($Candidate in @("-3.12", "-3.11")) { if (Test-PythonRuntime -Selector $Candidate) { $PythonSelector = $Candidate; break } }
if (-not $PythonSelector) {
    Write-Host "Python 3.12 is not installed. Installing it automatically..." -ForegroundColor Yellow
    $ManagerCommand = Get-Command pymanager -ErrorAction SilentlyContinue
    if (-not $ManagerCommand) { $ManagerCommand = Get-Command py -ErrorAction Stop }
    $InstallProcess = Start-Process -FilePath $ManagerCommand.Source -ArgumentList @("install", "3.12") -Wait -PassThru -NoNewWindow
    if ($InstallProcess.ExitCode -ne 0) { throw "Automatic Python 3.12 installation failed. Run: py install 3.12" }
    if (Test-PythonRuntime -Selector "-3.12") { $PythonSelector = "-3.12" } else { throw "Restart Windows and run the installer again." }
}
Write-Host "Using Python $PythonSelector" -ForegroundColor Green
$RecreateVenv = $false
if (Test-Path ".venv\Scripts\python.exe") { $ExistingVersion = (& .\.venv\Scripts\python.exe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim(); if ($ExistingVersion -notin @("3.11", "3.12")) { $RecreateVenv = $true } }
if ($RecreateVenv -and (Test-Path ".venv")) { Remove-Item ".venv" -Recurse -Force }
if (-not (Test-Path ".venv\Scripts\python.exe")) { & py $PythonSelector -m venv .venv }
Write-Host "Installing application packages..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip uninstall -y chardet 2>$null
if (-not (Test-Path ".env")) { Copy-Item .env.example .env }
Write-Host "Preparing and upgrading database..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe manage.py makemigrations inventory --noinput
& .\.venv\Scripts\python.exe manage.py migrate --noinput
& .\.venv\Scripts\python.exe manage.py migrate_legacy_employees
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput
$UserCountOutput = & .\.venv\Scripts\python.exe manage.py shell -c "from inventory.models import User; print(User.objects.count())"
$UserCountText = ($UserCountOutput | Select-Object -Last 1).ToString().Trim()
$UserCount = 0
[void][int]::TryParse($UserCountText, [ref]$UserCount)
if ($UserCount -eq 0) {
    Write-Host "Create the first Super Admin." -ForegroundColor Cyan
    $EmployeeId = Read-Host "Login User ID (example NXTTP0043)"
    $FullName = Read-Host "Full name"
    $Mobile = Read-Host "Mobile (+91XXXXXXXXXX)"
    $Email = Read-Host "Email (optional)"
    $SecurePassword = Read-Host "Temporary password (minimum 10 characters)" -AsSecureString
    $Password = [System.Net.NetworkCredential]::new('', $SecurePassword).Password
    & .\.venv\Scripts\python.exe manage.py bootstrap_system --employee-id $EmployeeId --full-name $FullName --mobile $Mobile --email $Email --password $Password
} else { Write-Host "Existing login-user database found. Account creation was skipped." -ForegroundColor Yellow }
$AppPath = (Get-Location).Path
$BackupScript = Join-Path $AppPath "scripts\backup_database.ps1"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$BackupScript`""
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
try { Register-ScheduledTask -TaskName "NextToppersInventoryDailyBackup" -Action $Action -Trigger $Trigger -Description "Daily Next Toppers inventory database backup" -Force | Out-Null } catch { Write-Warning "Automatic backup task was not created. Local testing can continue." }
Write-Host "Running installation verification..." -ForegroundColor Cyan
& .\scripts\verify_installation.ps1
Write-Host "Setup completed successfully. Double-click START_LOCAL_TEST.bat." -ForegroundColor Green
