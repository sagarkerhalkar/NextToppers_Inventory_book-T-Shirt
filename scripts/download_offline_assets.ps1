$ErrorActionPreference = "Stop"
$AppRoot = Split-Path $PSScriptRoot -Parent
Set-Location $AppRoot

$BootstrapRoot = Join-Path $AppRoot "static\vendor\bootstrap"
$ChartRoot = Join-Path $AppRoot "static\vendor\chartjs"
New-Item -ItemType Directory -Path $BootstrapRoot -Force | Out-Null
New-Item -ItemType Directory -Path $ChartRoot -Force | Out-Null

$downloads = @(
    @{
        Name = "Bootstrap CSS"
        Url = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
        Path = Join-Path $BootstrapRoot "bootstrap.min.css"
        MinimumBytes = 200000
        Marker = "Bootstrap"
    },
    @{
        Name = "Bootstrap JavaScript bundle"
        Url = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
        Path = Join-Path $BootstrapRoot "bootstrap.bundle.min.js"
        MinimumBytes = 70000
        Marker = "Bootstrap"
    },
    @{
        Name = "Chart.js"
        Url = "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"
        Path = Join-Path $ChartRoot "chart.umd.min.js"
        MinimumBytes = 150000
        Marker = "Chart.js"
    }
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
foreach ($download in $downloads) {
    Write-Host "Downloading $($download.Name) for offline use..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $download.Url -OutFile $download.Path -UseBasicParsing
    $file = Get-Item $download.Path
    if ($file.Length -lt $download.MinimumBytes) {
        throw "$($download.Name) download is incomplete. File size: $($file.Length) bytes."
    }
    $sample = Get-Content $download.Path -Raw
    if ($sample -notmatch [regex]::Escape($download.Marker)) {
        throw "$($download.Name) content validation failed."
    }
    Write-Host "$($download.Name) is stored locally." -ForegroundColor Green
}

Write-Host "All browser CSS and JavaScript assets are now local to the inventory server." -ForegroundColor Green
