$ErrorActionPreference = "Stop"
$AppRoot = Split-Path $PSScriptRoot -Parent
$LogRoot = Join-Path $env:LOCALAPPDATA "NextToppersInventory\logs"
$LogFile = Join-Path $LogRoot "server.log"
$StdoutLog = Join-Path $LogRoot "backend_stdout.log"
$StderrLog = Join-Path $LogRoot "backend_stderr.log"
$PidFile = Join-Path $LogRoot "backend.pid"
$BackendPort = 3460

New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null

function Write-ServerLog {
    param([string]$Message)
    $line = "$(Get-Date -Format s) - $Message"
    Add-Content -Path $LogFile -Value $line -Encoding ASCII
}

# Google Drive and network folders may take time to become available after login.
for ($attempt = 1; $attempt -le 18; $attempt++) {
    if (
        (Test-Path (Join-Path $AppRoot "manage.py")) -and
        (Test-Path (Join-Path $AppRoot ".venv\Scripts\waitress-serve.exe"))
    ) {
        break
    }
    Start-Sleep -Seconds 10
}

$WaitressExe = Join-Path $AppRoot ".venv\Scripts\waitress-serve.exe"
if (-not (Test-Path $WaitressExe)) {
    Write-ServerLog "Auto-start failed: Waitress executable is unavailable."
    exit 1
}

$Existing = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
if ($Existing) {
    Write-ServerLog "Backend already listening on 127.0.0.1:$BackendPort."
    exit 0
}

Set-Location $AppRoot
Remove-Item $StdoutLog, $StderrLog -Force -ErrorAction SilentlyContinue
New-Item -ItemType File -Path $StdoutLog -Force | Out-Null
New-Item -ItemType File -Path $StderrLog -Force | Out-Null
Write-ServerLog "Starting Waitress directly on private address 127.0.0.1:$BackendPort."

# Django and WSGI are verified by the visible installer before this hidden launcher runs.
# Do not execute native Python preflight commands here: harmless dependency warnings are
# written to stderr and Windows PowerShell can incorrectly promote them to fatal errors.
$WaitressArguments = @(
    "--listen=127.0.0.1:$BackendPort",
    "--threads=8",
    "--channel-timeout=120",
    "nexttoppers_inventory.wsgi:application"
)

$Process = Start-Process `
    -FilePath $WaitressExe `
    -ArgumentList $WaitressArguments `
    -WorkingDirectory $AppRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError $StderrLog `
    -PassThru

$Process.Id | Set-Content $PidFile -Encoding ASCII
for ($attempt = 1; $attempt -le 40; $attempt++) {
    Start-Sleep -Seconds 1
    $Process.Refresh()
    if ($Process.HasExited) {
        Write-ServerLog "Private backend exited during startup with code $($Process.ExitCode). See $StderrLog"
        exit 1
    }
    $Listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
    if ($Listener) {
        Write-ServerLog "Private backend is listening successfully on 127.0.0.1:$BackendPort with PID $($Process.Id)."
        exit 0
    }
}

Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
Write-ServerLog "Private backend did not open port $BackendPort within 40 seconds. See $StderrLog"
exit 1
