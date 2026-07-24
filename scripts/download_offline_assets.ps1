$ErrorActionPreference = "Stop"
$AppRoot = Split-Path $PSScriptRoot -Parent
Set-Location $AppRoot

$BootstrapRoot = Join-Path $AppRoot "static\vendor\bootstrap"
New-Item -ItemType Directory -Path $BootstrapRoot -Force | Out-Null

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
    $content = Get-Content $download.Path -Raw
    if ($content -notmatch [regex]::Escape($download.Marker)) {
        throw "$($download.Name) content validation failed."
    }

    # Source maps are optional developer files. Remove their references so the
    # WhiteNoise production manifest does not require unnecessary .map files.
    $content = $content -replace '(?m)^\s*/\*# sourceMappingURL=.*?\*/\s*$', ''
    $content = $content -replace '(?m)^\s*//# sourceMappingURL=.*?\s*$', ''
    Set-Content -Path $download.Path -Value $content -Encoding UTF8 -NoNewline

    if ((Get-Content $download.Path -Raw) -match 'sourceMappingURL=') {
        throw "$($download.Name) still contains a source-map dependency after cleanup."
    }
    Write-Host "$($download.Name) is stored locally without development source-map references." -ForegroundColor Green
}

# Chart.js is intentionally not downloaded. The dashboard uses a lightweight
# local HTML/CSS/JavaScript chart implementation, avoiding another CDN/library.
$OldChartRoot = Join-Path $AppRoot "static\vendor\chartjs"
if (Test-Path $OldChartRoot) {
    Remove-Item $OldChartRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "All required browser assets are local. No Chart.js download is required." -ForegroundColor Green
