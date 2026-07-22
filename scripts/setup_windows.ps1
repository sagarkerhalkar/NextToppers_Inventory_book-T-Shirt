$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "Next Toppers Inventory - Windows Local Setup" -ForegroundColor Cyan
Write-Host "Application folder: $((Get-Location).Path)" -ForegroundColor DarkGray

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher is not installed. Install Python 3.12 (recommended) or Python 3.11, select 'Add Python to PATH', and run this file again."
}

$PythonSelector = $null
foreach ($Candidate in @("-3.12", "-3.11")) {
    & py $Candidate -c "import sys; print(sys.version)" *> $null
    if ($LASTEXITCODE -eq 0) {
        $PythonSelector = $Candidate
        break
    }
}

if (-not $PythonSelector) {
    throw "Python 3.12 or Python 3.11 is required. Python 3.13/3.14 is not used for this tested build. Install Python 3.12 and run again."
}

Write-Host "Using Python $PythonSelector" -ForegroundColor Green

$RecreateVenv = $false
if (Test-Path ".venv\Scripts\python.exe") {
    $ExistingVersion = (& .\.venv\Scripts\python.exe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
    if ($ExistingVersion -notin @("3.11", "3.12")) {
        Write-Warning "Existing virtual environment uses Python $ExistingVersion. It will be recreated with a supported Python version."
        $RecreateVenv = $true
    }
}

if ($RecreateVenv -and (Test-Path ".venv")) {
    Remove-Item ".venv" -Recurse -Force
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    & py $PythonSelector -m venv .venv
}

Write-Host "Installing application packages..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created local .env configuration file." -ForegroundColor Green
}

Write-Host "Preparing database..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe manage.py makemigrations inventory --noinput
& .\.venv\Scripts\python.exe manage.py migrate --noinput
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput

$UserCountOutput = & .\.venv\Scripts\python.exe manage.py shell -c "from inventory.models import User; print(User.objects.count())"
$UserCountText = ($UserCountOutput | Select-Object -Last 1).ToString().Trim()
$UserCount = 0
[void][int]::TryParse($UserCountText, [ref]$UserCount)

if ($UserCount -eq 0) {
    Write-Host "" 
    Write-Host "Create the first Super Admin." -ForegroundColor Cyan
    $EmployeeId = Read-Host "Employee ID (example NXTTP0043)"
    $FullName = Read-Host "Full name"
    $Mobile = Read-Host "Mobile (+91XXXXXXXXXX)"
    $Email = Read-Host "Email (optional)"
    $SecurePassword = Read-Host "Temporary password (minimum 10 characters)" -AsSecureString
    $Password = [System.Net.NetworkCredential]::new('', $SecurePassword).Password
    & .\.venv\Scripts\python.exe manage.py bootstrap_system --employee-id $EmployeeId --full-name $FullName --mobile $Mobile --email $Email --password $Password
} else {
    Write-Host "Existing user database found. Super Admin creation was skipped." -ForegroundColor Yellow
}

$AppPath = (Get-Location).Path
$BackupScript = Join-Path $AppPath "scripts\backup_database.ps1"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$BackupScript`""
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
try {
    Register-ScheduledTask -TaskName "NextToppersInventoryDailyBackup" -Action $Action -Trigger $Trigger -Description "Daily Next Toppers inventory database backup" -Force | Out-Null
    Write-Host "Daily backup task created for 2:00 AM." -ForegroundColor Green
} catch {
    Write-Warning "Automatic backup task was not created. This does not stop local testing. Run setup as Administrator later to create the scheduled task."
}

Write-Host "Running installation verification..." -ForegroundColor Cyan
& .\scripts\verify_installation.ps1

Write-Host "" 
Write-Host "Setup completed successfully." -ForegroundColor Green
Write-Host "Double-click START_LOCAL_TEST.bat to open the application." -ForegroundColor Green
