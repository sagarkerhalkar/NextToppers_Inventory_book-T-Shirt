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
    "$(Get-Date -Format s) - $Message" | Out-File $LogFile -Append -Encoding utf8
}

# Google Drive and network folders may take time to become available after login.
for ($attempt = 1; $attempt -le 18; $attempt++) {
    if (
        (Test-Path (Join-Path $AppRoot "manage.py")) -and
        (Test-Path (Join-Path $AppRoot ".venv\Scripts\python.exe")) -and
        (Test-Path (Join-Path $AppRoot "scripts\run_waitress_backend.py"))
    ) {
        break
    }
    Start-Sleep -Seconds 10
}

$PythonExe = Join-Path $AppRoot ".venv\Scripts\python.exe"
$Runner = Join-Path $AppRoot "scripts\run_waitress_backend.py"
if (-not (Test-Path $PythonExe) -or -not (Test-Path $Runner)) {
    Write-ServerLog "Auto-start failed: Python environment or backend runner is unavailable."
    exit 1
}

$Existing = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
if ($Existing) {
    Write-ServerLog "Backend already listening on 127.0.0.1:$BackendPort."
    exit 0
}

Set-Location $AppRoot
Write-ServerLog "Running Django preflight before private backend startup."
& $PythonExe manage.py check *> $PreflightLog
if ($LASTEXITCODE -ne 0) {
    Write-ServerLog "Django preflight failed. See $PreflightLog"
    exit 1
}

Remove-Item $StdoutLog, $StderrLog -Force -ErrorAction SilentlyContinue
Write-ServerLog "Starting private backend through python.exe on 127.0.0.1:$BackendPort."
$Process = Start-Process `
    -FilePath $PythonExe `
    -ArgumentList "`"$Runner`"" `
    -WorkingDirectory $AppRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError $StderrLog `
    -PassThru

$Process.Id | Set-Content $PidFile -Encoding ascii
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
