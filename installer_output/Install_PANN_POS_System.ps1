# PANN POS System - Automated Installer
# Run this script to install PANN POS System

Write-Host "================================" -ForegroundColor Cyan
Write-Host "PANN POS System Installer" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This installer requires Administrator privileges." -ForegroundColor Red
    Write-Host "Please right-click and select 'Run as Administrator'" -ForegroundColor Red
    pause
    exit 1
}

# Check for MongoDB
Write-Host "Checking for MongoDB..." -ForegroundColor Yellow
$mongoFound = $false
$mongoPaths = @(
    "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe",
    "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe",
    "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe",
    "C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe"
)

foreach ($path in $mongoPaths) {
    if (Test-Path $path) {
        Write-Host "MongoDB found at: $path" -ForegroundColor Green
        $mongoFound = $true
        break
    }
}

if (-not $mongoFound) {
    Write-Host "WARNING: MongoDB Community Edition not found!" -ForegroundColor Yellow
    Write-Host "PANN POS System requires MongoDB to function." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install MongoDB Community Edition from:" -ForegroundColor Yellow
    Write-Host "https://www.mongodb.com/try/download/community" -ForegroundColor Cyan
    Write-Host ""
    $continue = Read-Host "Continue installation anyway? (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# Installation directory
$InstallDir = "$env:ProgramFiles\PANN\POS_System"
Write-Host ""
Write-Host "Installing to: $InstallDir" -ForegroundColor Yellow

# Create installation directory
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Copy files
Write-Host "Copying files..." -ForegroundColor Yellow
Copy-Item "PANN_POS_System.exe" -Destination $InstallDir -Force

# Create shortcuts
Write-Host "Creating shortcuts..." -ForegroundColor Yellow

# Desktop shortcut
$WshShell = New-Object -ComObject WScript.Shell
$DesktopShortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\PANN POS System.lnk")
$DesktopShortcut.TargetPath = "$InstallDir\PANN_POS_System.exe"
$DesktopShortcut.WorkingDirectory = $InstallDir
$DesktopShortcut.Description = "PANN POS System"
$DesktopShortcut.Save()

# Start menu shortcut
$StartMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\PANN POS System"
if (-not (Test-Path $StartMenuPath)) {
    New-Item -ItemType Directory -Path $StartMenuPath -Force | Out-Null
}

$StartMenuShortcut = $WshShell.CreateShortcut("$StartMenuPath\PANN POS System.lnk")
$StartMenuShortcut.TargetPath = "$InstallDir\PANN_POS_System.exe"
$StartMenuShortcut.WorkingDirectory = $InstallDir
$StartMenuShortcut.Description = "PANN POS System"
$StartMenuShortcut.Save()

# Create uninstaller
$UninstallScript = @"
# PANN POS System Uninstaller

Write-Host "Uninstalling PANN POS System..." -ForegroundColor Yellow

`$InstallDir = "$InstallDir"

# Remove files
if (Test-Path `$InstallDir) {
    Remove-Item -Path `$InstallDir -Recurse -Force
}

# Remove shortcuts
Remove-Item -Path "`$env:USERPROFILE\Desktop\PANN POS System.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "`$env:APPDATA\Microsoft\Windows\Start Menu\Programs\PANN POS System" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Uninstall complete!" -ForegroundColor Green
pause
"@

$UninstallScript | Out-File -FilePath "$InstallDir\Uninstall.ps1" -Encoding UTF8

# Done
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "PANN POS System has been installed to:" -ForegroundColor Yellow
Write-Host $InstallDir -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the application:" -ForegroundColor Yellow
Write-Host "1. Double-click the desktop shortcut" -ForegroundColor White
Write-Host "2. Or go to Start Menu > PANN POS System" -ForegroundColor White
Write-Host ""
Write-Host "Access the application at: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "To uninstall, run: $InstallDir\Uninstall.ps1" -ForegroundColor Yellow
Write-Host ""
pause
