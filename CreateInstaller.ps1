# PowerShell-based Installer Creator for PANN POS System
# Creates a simple installer without external dependencies

param(
    [string]$OutputDir = "installer_output"
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "PANN POS System Installer Creator" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if executable exists
$ExePath = "backend\dist\PANN_POS_System.exe"
if (-not (Test-Path $ExePath)) {
    Write-Host "Executable not found. Building application first..." -ForegroundColor Yellow
    Write-Host "Running build.bat..." -ForegroundColor Yellow
    Write-Host ""
    
    # Try to run build.bat
    $buildResult = Start-Process -FilePath "build.bat" -Wait -NoNewWindow -PassThru
    if ($buildResult.ExitCode -ne 0) {
        Write-Host "ERROR: Build failed!" -ForegroundColor Red
        Write-Host "Please manually run build.bat to see error details." -ForegroundColor Red
        exit 1
    }
    
    # Check again
    if (-not (Test-Path $ExePath)) {
        Write-Host "ERROR: Executable still not found after build." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host ""
}

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host "Creating installer package..." -ForegroundColor Yellow

# Create installer script
$InstallerScript = @'
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
'@

$InstallerScript | Out-File -FilePath "$OutputDir\Install_PANN_POS_System.ps1" -Encoding UTF8

# Copy executable to output directory
Write-Host "Copying executable..." -ForegroundColor Yellow
Copy-Item $ExePath -Destination $OutputDir -Force

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Installer Created Successfully!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output location: $OutputDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Files created:" -ForegroundColor Yellow
Write-Host "  - Install_PANN_POS_System.ps1 (installer script)" -ForegroundColor White
Write-Host "  - PANN_POS_System.exe (application)" -ForegroundColor White
Write-Host ""
Write-Host "To distribute:" -ForegroundColor Yellow
Write-Host "1. Zip the entire '$OutputDir' folder" -ForegroundColor White
Write-Host "2. Send to users" -ForegroundColor White
Write-Host "3. Users extract and run: Install_PANN_POS_System.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Note: Users must right-click installer and select 'Run with PowerShell'" -ForegroundColor Yellow
Write-Host ""

