$ErrorActionPreference = "Stop"
$AppRoot = Split-Path $PSScriptRoot -Parent
$LogRoot = Join-Path $env:LOCALAPPDATA "NextToppersInventory\logs"
$LogFile = Join-Path $LogRoot "server.log"
$StdoutLog = Join-Path $LogRoot "backend_stdout.log"
$StderrLog = Join-Path $LogRoot "backend_stderr.log"
$PreflightLog = Join-Path $LogRoot "backend_preflight.log"
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
        (Test-Path (Join-Path $AppRoot ".venv\Scripts\python.exe")) -and
        (Test-Path (Join-Path $AppRoot ".venv\Scripts\waitress-serve.exe"))
    ) {
        break
    }
    Start-Sleep -Seconds 10
}

$PythonExe = Join-Path $AppRoot ".venv\Scripts\python.exe"
$WaitressExe = Join-Path $AppRoot ".venv\Scripts\waitress-serve.exe"
if (-not (Test-Path $PythonExe) -or -not (Test-Path $WaitressExe)) {
    Write-ServerLog "Auto-start failed: Python environment or Waitress executable is unavailable."
    exit 1
}

$Existing = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
if ($Existing) {
    Write-ServerLog "Backend already listening on 127.0.0.1:$BackendPort."
    exit 0
}

Set-Location $AppRoot
Write-ServerLog "Running Django and WSGI preflight before private backend startup."
$PreflightOutput = & $PythonExe manage.py check 2>&1
$PreflightExit = $LASTEXITCODE
$PreflightOutput | Set-Content -Path $PreflightLog -Encoding UTF8
if ($PreflightExit -ne 0) {
    Write-ServerLog "Django preflight failed. See $PreflightLog"
    exit 1
}

$WsgiOutput = & $PythonExe -c "from nexttoppers_inventory.wsgi import application; print('WSGI import successful')" 2>&1
$WsgiExit = $LASTEXITCODE
$WsgiOutput | Add-Content -Path $PreflightLog -Encoding UTF8
if ($WsgiExit -ne 0) {
    Write-ServerLog "WSGI import failed. See $PreflightLog"
    exit 1
}

Remove-Item $StdoutLog, $StderrLog -Force -ErrorAction SilentlyContinue
New-Item -ItemType File -Path $StdoutLog -Force | Out-Null
New-Item -ItemType File -Path $StderrLog -Force | Out-Null
Write-ServerLog "Starting Waitress directly on private address 127.0.0.1:$BackendPort."

# Important: start waitress-serve.exe directly. All arguments contain no spaces,
# so Windows cannot split the Google Drive application path incorrectly.
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
Write-ServerLog "Private backend did not open port $BackendPort within 40 seconds. See $StderrLog and $PreflightLog"
exit 1
