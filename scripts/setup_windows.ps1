$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python is not installed. Install Python 3.11 or 3.12 and select 'Add Python to PATH'."
}

if (-not (Test-Path ".venv")) { py -3 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt

if (-not (Test-Path ".env")) { Copy-Item .env.example .env }
& .\.venv\Scripts\python.exe manage.py makemigrations inventory --noinput
& .\.venv\Scripts\python.exe manage.py migrate --noinput
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput

Write-Host ""
Write-Host "Create the first Super Admin." -ForegroundColor Cyan
$EmployeeId = Read-Host "Employee ID (example NXTTP0043)"
$FullName = Read-Host "Full name"
$Mobile = Read-Host "Mobile (+91XXXXXXXXXX)"
$Email = Read-Host "Email (optional)"
$SecurePassword = Read-Host "Temporary password (minimum 10 characters)" -AsSecureString
$Password = [System.Net.NetworkCredential]::new('', $SecurePassword).Password
& .\.venv\Scripts\python.exe manage.py bootstrap_system --employee-id $EmployeeId --full-name $FullName --mobile $Mobile --email $Email --password $Password

$AppPath = (Get-Location).Path
$BackupScript = Join-Path $AppPath "scripts\backup_database.ps1"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$BackupScript`""
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
try {
    Register-ScheduledTask -TaskName "NextToppersInventoryDailyBackup" -Action $Action -Trigger $Trigger -Description "Daily Next Toppers inventory database backup" -Force | Out-Null
    Write-Host "Daily backup task created for 2:00 AM." -ForegroundColor Green
} catch {
    Write-Warning "Could not create the scheduled backup task. Run PowerShell as Administrator and execute this setup again if required."
}
Write-Host "Setup complete. Run scripts\start_windows.ps1" -ForegroundColor Green
