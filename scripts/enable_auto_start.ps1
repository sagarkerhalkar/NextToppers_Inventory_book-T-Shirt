$ErrorActionPreference = "Stop"
$AppRoot = Split-Path $PSScriptRoot -Parent
$Launcher = Join-Path $AppRoot "scripts\start_server_silent.ps1"
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "Next Toppers Inventory Server.lnk"

if (-not (Test-Path $Launcher)) {
    throw "Auto-start launcher was not found: $Launcher"
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Launcher`""
$Shortcut.WorkingDirectory = $AppRoot
$Shortcut.Description = "Start Next Toppers Inventory server on port 3458 after Windows login"
$Shortcut.Save()

Write-Host "Automatic startup enabled." -ForegroundColor Green
Write-Host "The inventory server will start automatically after Windows login." -ForegroundColor Green
Write-Host "Startup shortcut: $ShortcutPath" -ForegroundColor DarkGray
