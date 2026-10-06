$ErrorActionPreference = "Stop"
$AppRoot = Split-Path $PSScriptRoot -Parent
Set-Location $AppRoot

$IsAdministrator = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $IsAdministrator) {
    Write-Host "Administrator permission is required to open Windows Firewall port 3458." -ForegroundColor Yellow
    Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$PSCommandPath`""
    )
    exit $LASTEXITCODE
}

$Addresses = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {
        $_.IPAddress -notlike "127.*" -and
        $_.IPAddress -notlike "169.254.*" -and
        $_.PrefixOrigin -ne "WellKnown"
    } |
    Select-Object -ExpandProperty IPAddress -Unique

if (-not $Addresses) {
    throw "No active local IPv4 address was found. Connect the server to Wi-Fi or LAN and run this file again."
}

$RuleName = "Next Toppers Inventory TCP 3458"
Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue
New-NetFirewallRule `
    -DisplayName $RuleName `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalPort 3458 `
    -Profile Any | Out-Null

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

$Existing = Get-Content ".env" |
    Where-Object {
        $_ -notmatch "^\s*DJANGO_ALLOWED_HOSTS\s*=" -and
        $_ -notmatch "^\s*DJANGO_CSRF_TRUSTED_ORIGINS\s*="
    }
$Hosts = @("127.0.0.1", "localhost") + $Addresses
$Origins = $Hosts | ForEach-Object { "http://${_}:3458" }
$Existing += "DJANGO_ALLOWED_HOSTS=$($Hosts -join ',')"
$Existing += "DJANGO_CSRF_TRUSTED_ORIGINS=$($Origins -join ',')"
Set-Content -Path ".env" -Value $Existing -Encoding UTF8

Write-Host "" 
Write-Host "LAN access is enabled successfully." -ForegroundColor Green
Write-Host "Windows Firewall TCP port 3458 is open." -ForegroundColor Green
Write-Host "" 
Write-Host "Start the application using START_LOCAL_TEST.bat." -ForegroundColor Cyan
Write-Host "Then open one of these addresses on another device connected to the same network:" -ForegroundColor Cyan
foreach ($Address in $Addresses) {
    Write-Host "  http://${Address}:3458" -ForegroundColor Yellow
}
Write-Host "" 
Write-Host "For stable access, reserve this server IP in your router or set a static IPv4 address." -ForegroundColor DarkGray
