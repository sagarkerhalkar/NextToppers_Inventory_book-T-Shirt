$ErrorActionPreference = "Stop"
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "Next Toppers Inventory Server.lnk"
if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
    Write-Host "Automatic startup disabled." -ForegroundColor Yellow
} else {
    Write-Host "Automatic startup was already disabled." -ForegroundColor DarkGray
}
