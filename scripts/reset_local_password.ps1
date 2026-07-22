$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Application is not installed yet. Run INSTALL_LOCAL_TEST.bat first."
}

Write-Host "" 
Write-Host "Next Toppers Inventory - Reset Local Password" -ForegroundColor Cyan
Write-Host "This resets an existing account and activates it." -ForegroundColor DarkGray
Write-Host "" 

$EmployeeId = (Read-Host "Employee ID (example NXTTP0043)").Trim().ToUpper()
if ($EmployeeId -notmatch '^NXTTP\d{4}$') {
    throw "Invalid Employee ID. Use NXTTP followed by exactly four digits."
}

$SecurePassword = Read-Host "New password (minimum 10 characters)" -AsSecureString
$SecureConfirm = Read-Host "Enter the new password again" -AsSecureString
$Password = [System.Net.NetworkCredential]::new('', $SecurePassword).Password
$ConfirmPassword = [System.Net.NetworkCredential]::new('', $SecureConfirm).Password

if ($Password.Length -lt 10) {
    throw "Password must contain at least 10 characters."
}
if ($Password -ne $ConfirmPassword) {
    throw "The two passwords do not match."
}

$env:NXTTP_RESET_EMPLOYEE_ID = $EmployeeId
$env:NXTTP_RESET_PASSWORD = $Password

try {
    & .\.venv\Scripts\python.exe manage.py shell -c "import os; from inventory.models import User; eid=os.environ['NXTTP_RESET_EMPLOYEE_ID']; pwd=os.environ['NXTTP_RESET_PASSWORD']; u=User.objects.filter(employee_id=eid).first(); assert u is not None, f'Employee ID {eid} was not found'; u.set_password(pwd); u.is_active=True; u.must_change_password=False; u.save(update_fields=['password','is_active','must_change_password']); print(f'Password reset successfully for {u.employee_id} - {u.full_name}')"
    if ($LASTEXITCODE -ne 0) {
        throw "Password reset failed. Check that the Employee ID is correct."
    }
} finally {
    Remove-Item Env:NXTTP_RESET_EMPLOYEE_ID -ErrorAction SilentlyContinue
    Remove-Item Env:NXTTP_RESET_PASSWORD -ErrorAction SilentlyContinue
    $Password = $null
    $ConfirmPassword = $null
}

Write-Host "" 
Write-Host "PASSWORD RESET SUCCESSFULLY" -ForegroundColor Green
Write-Host "Login with Employee ID: $EmployeeId" -ForegroundColor Green
Write-Host "Open: http://localhost:3458" -ForegroundColor Cyan
