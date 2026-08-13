param(
    [string]$PublicIp = "156.156.40.51",
    [int]$PublicPort = 3458,
    [int]$BackendPort = 3460
)

$ErrorActionPreference = "Stop"
$AppRoot = Split-Path $PSScriptRoot -Parent
Set-Location $AppRoot

function Test-Administrator {
    return ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
}

function Install-MicrosoftMsi {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Destination
    )
    Write-Host "Downloading $Name from Microsoft..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing
    $signature = Get-AuthenticodeSignature -FilePath $Destination
    if ($signature.Status -ne "Valid" -or $signature.SignerCertificate.Subject -notmatch "Microsoft") {
        throw "$Name did not have a valid Microsoft digital signature. Installation was stopped."
    }
    $process = Start-Process msiexec.exe -Wait -PassThru -ArgumentList @(
        "/i", "`"$Destination`"", "/qn", "/norestart"
    )
    if ($process.ExitCode -notin @(0, 3010, 1641)) {
        throw "$Name installation failed with MSI exit code $($process.ExitCode)."
    }
}

if (-not (Test-Administrator)) {
    throw "Run this IIS setup as Administrator."
}
if (-not (Test-Path ".venv\Scripts\waitress-serve.exe")) {
    throw "The inventory Python environment is missing. Install/update the application first."
}
if (-not (Get-NetIPAddress -AddressFamily IPv4 -IPAddress $PublicIp -ErrorAction SilentlyContinue)) {
    throw "IP address $PublicIp is not assigned to this Windows server. IIS cannot use the requested address until it exists on a server network adapter."
}

Write-Host "Installing required Windows IIS features..." -ForegroundColor Cyan
$features = @(
    "IIS-WebServerRole",
    "IIS-WebServer",
    "IIS-CommonHttpFeatures",
    "IIS-DefaultDocument",
    "IIS-StaticContent",
    "IIS-HttpErrors",
    "IIS-HttpLogging",
    "IIS-RequestFiltering",
    "IIS-HttpCompressionStatic",
    "IIS-ApplicationDevelopment",
    "IIS-NetFxExtensibility45",
    "IIS-ASPNET45",
    "IIS-ISAPIExtensions",
    "IIS-ISAPIFilter",
    "IIS-WebServerManagementTools",
    "IIS-ManagementConsole"
)
foreach ($feature in $features) {
    $item = Get-WindowsOptionalFeature -Online -FeatureName $feature -ErrorAction SilentlyContinue
    if ($item -and $item.State -ne "Enabled") {
        Enable-WindowsOptionalFeature -Online -FeatureName $feature -All -NoRestart | Out-Null
    }
}

$TempRoot = Join-Path $env:TEMP "NextToppersIIS"
New-Item -ItemType Directory -Path $TempRoot -Force | Out-Null
$RewriteMsi = Join-Path $TempRoot "rewrite_amd64_en-US.msi"
$ArrMsi = Join-Path $TempRoot "requestRouter_amd64.msi"

if (-not (Test-Path "$env:SystemRoot\System32\inetsrv\rewrite.dll")) {
    Install-MicrosoftMsi `
        -Name "Microsoft IIS URL Rewrite 2.1" `
        -Url "https://download.microsoft.com/download/1/2/8/128E2E22-C1B9-44A4-BE2A-5859ED1D4592/rewrite_amd64_en-US.msi" `
        -Destination $RewriteMsi
} else {
    Write-Host "Microsoft IIS URL Rewrite is already installed." -ForegroundColor Green
}

$ArrInstalled = Get-ChildItem "$env:ProgramFiles\IIS" -Filter requestRouter.dll -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $ArrInstalled) {
    Install-MicrosoftMsi `
        -Name "Microsoft IIS Application Request Routing 3.0" `
        -Url "https://download.microsoft.com/download/E/9/8/E9849D6A-020E-47E4-9FD0-A023E99B54EB/requestRouter_amd64.msi" `
        -Destination $ArrMsi
} else {
    Write-Host "Microsoft IIS Application Request Routing is already installed." -ForegroundColor Green
}

Import-Module WebAdministration -Force
$AppCmd = Join-Path $env:SystemRoot "System32\inetsrv\appcmd.exe"
if (-not (Test-Path $AppCmd)) {
    throw "IIS appcmd.exe was not found after enabling IIS. Restart Windows and run the installer again."
}

& $AppCmd set config /section:system.webServer/proxy /enabled:"True" /preserveHostHeader:"True" /reverseRewriteHostInResponseHeaders:"False" /commit:apphost | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "IIS ARR reverse-proxy mode could not be enabled."
}

$SiteName = "NextToppersInventory"
$PoolName = "NextToppersInventoryProxy"
$ProxyRoot = Join-Path $env:SystemDrive "inetpub\NextToppersInventoryProxy"
New-Item -ItemType Directory -Path $ProxyRoot -Force | Out-Null

$webConfig = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="Next Toppers Inventory Reverse Proxy" stopProcessing="true">
          <match url="(.*)" />
          <action type="Rewrite" url="http://127.0.0.1:$BackendPort/{R:1}" appendQueryString="true" logRewrittenUrl="true" />
        </rule>
      </rules>
    </rewrite>
    <httpErrors existingResponse="PassThrough" />
    <security>
      <requestFiltering removeServerHeader="true">
        <requestLimits maxAllowedContentLength="52428800" />
      </requestFiltering>
    </security>
    <httpProtocol>
      <customHeaders>
        <remove name="Content-Security-Policy" />
        <add name="Content-Security-Policy" value="default-src 'self'; img-src 'self' data: blob:; font-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'" />
        <remove name="Referrer-Policy" />
        <add name="Referrer-Policy" value="no-referrer" />
        <remove name="Permissions-Policy" />
        <add name="Permissions-Policy" value="camera=(), microphone=(), geolocation=(), payment=(), usb=()" />
      </customHeaders>
    </httpProtocol>
  </system.webServer>
</configuration>
"@
Set-Content -Path (Join-Path $ProxyRoot "web.config") -Value $webConfig -Encoding UTF8
Set-Content -Path (Join-Path $ProxyRoot "health.txt") -Value "Next Toppers IIS reverse proxy" -Encoding ASCII

if (Test-Path "IIS:\Sites\$SiteName") {
    Stop-Website -Name $SiteName -ErrorAction SilentlyContinue
    Remove-Website -Name $SiteName
}
if (-not (Test-Path "IIS:\AppPools\$PoolName")) {
    New-WebAppPool -Name $PoolName | Out-Null
}
Set-ItemProperty "IIS:\AppPools\$PoolName" -Name managedRuntimeVersion -Value ""
Set-ItemProperty "IIS:\AppPools\$PoolName" -Name managedPipelineMode -Value "Integrated"
Set-ItemProperty "IIS:\AppPools\$PoolName" -Name startMode -Value "AlwaysRunning"

$conflicts = Get-WebBinding -Protocol http | Where-Object {
    $_.bindingInformation -eq "${PublicIp}:${PublicPort}:" -or $_.bindingInformation -eq "*:${PublicPort}:"
}
if ($conflicts) {
    $details = ($conflicts | ForEach-Object { "$($_.ItemXPath) [$($_.bindingInformation)]" }) -join "; "
    throw "Another IIS site already uses port $PublicPort. Conflicting binding: $details"
}

New-Website `
    -Name $SiteName `
    -PhysicalPath $ProxyRoot `
    -ApplicationPool $PoolName `
    -IPAddress $PublicIp `
    -Port $PublicPort `
    -HostHeader "" | Out-Null

Set-Service W3SVC -StartupType Automatic
Start-Service W3SVC
Start-WebAppPool -Name $PoolName -ErrorAction SilentlyContinue
Start-Website -Name $SiteName

$RuleNames = @(
    "Next Toppers Inventory TCP 3458",
    "Next Toppers Inventory IIS TCP 3458"
)
foreach ($rule in $RuleNames) {
    Get-NetFirewallRule -DisplayName $rule -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue
}
New-NetFirewallRule `
    -DisplayName "Next Toppers Inventory IIS TCP 3458" `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalAddress $PublicIp `
    -LocalPort $PublicPort `
    -Profile Any | Out-Null

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}
$envLines = Get-Content ".env" | Where-Object {
    $_ -notmatch "^\s*DJANGO_ALLOWED_HOSTS\s*=" -and
    $_ -notmatch "^\s*DJANGO_CSRF_TRUSTED_ORIGINS\s*=" -and
    $_ -notmatch "^\s*DJANGO_DEBUG\s*="
}
$envLines += "DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,$PublicIp"
$envLines += "DJANGO_CSRF_TRUSTED_ORIGINS=http://${PublicIp}:$PublicPort,http://127.0.0.1:$BackendPort"
$envLines += "DJANGO_DEBUG=False"
Set-Content -Path ".env" -Value $envLines -Encoding UTF8

Write-Host "IIS reverse proxy configured successfully." -ForegroundColor Green
Write-Host "Public user address: http://${PublicIp}:$PublicPort" -ForegroundColor Yellow
Write-Host "Private Python backend: http://127.0.0.1:$BackendPort" -ForegroundColor DarkGray
