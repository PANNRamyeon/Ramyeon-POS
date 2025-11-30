# Build PANN_POS_System_Setup.exe using PowerShell
# Creates a self-extracting installer executable

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building PANN POS System Setup Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if executable exists
$ExePath = "backend\dist\PANN_POS_System.exe"
if (-not (Test-Path $ExePath)) {
    Write-Host "ERROR: Executable not found at $ExePath" -ForegroundColor Red
    Write-Host "Please run build.bat first to create the executable." -ForegroundColor Yellow
    exit 1
}

Write-Host "Found executable: $ExePath" -ForegroundColor Green
Write-Host ""

# Create output directory
$OutputDir = "installer_output"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Create the installer script that will be embedded
$InstallerScript = @'
# PANN POS System - Self-Extracting Installer
# This script is embedded in the installer executable

param(
    [switch]$ExtractOnly = $false
)

$ErrorActionPreference = "Stop"

# Get the directory where the installer is located
$InstallerDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TempDir = Join-Path $env:TEMP "PANN_POS_Setup_$(Get-Random)"
$AppName = "PANN POS System"
$InstallDir = "$env:ProgramFiles\PANN\POS_System"

# Extract files
function Extract-Files {
    Write-Host "Extracting files..." -ForegroundColor Yellow
    
    # Create temp directory
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    
    # The executable is embedded at the end of this script
    # We'll extract it using binary reading
    $ScriptPath = $MyInvocation.MyCommand.Path
    $ScriptBytes = [System.IO.File]::ReadAllBytes($ScriptPath)
    
    # Find the marker that indicates where the embedded file starts
    $Marker = [System.Text.Encoding]::ASCII.GetBytes("__EMBEDDED_FILE_START__")
    $MarkerIndex = -1
    
    for ($i = 0; $i -lt ($ScriptBytes.Length - $Marker.Length); $i++) {
        $match = $true
        for ($j = 0; $j -lt $Marker.Length; $j++) {
            if ($ScriptBytes[$i + $j] -ne $Marker[$j]) {
                $match = $false
                break
            }
        }
        if ($match) {
            $MarkerIndex = $i + $Marker.Length
            break
        }
    }
    
    if ($MarkerIndex -eq -1) {
        Write-Host "ERROR: Could not find embedded file!" -ForegroundColor Red
        exit 1
    }
    
    # Extract the embedded executable
    $EmbeddedBytes = $ScriptBytes[$MarkerIndex..($ScriptBytes.Length - 1)]
    $ExtractedExe = Join-Path $TempDir "PANN_POS_System.exe"
    [System.IO.File]::WriteAllBytes($ExtractedExe, $EmbeddedBytes)
    
    Write-Host "Files extracted to: $TempDir" -ForegroundColor Green
    return $ExtractedExe
}

if ($ExtractOnly) {
    $ExtractedExe = Extract-Files
    Write-Host "Extraction complete. Files are in: $TempDir" -ForegroundColor Green
    exit 0
}

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

# Extract files
$ExtractedExe = Extract-Files

# Create installation directory
Write-Host ""
Write-Host "Installing to: $InstallDir" -ForegroundColor Yellow
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Copy files
Write-Host "Copying files..." -ForegroundColor Yellow
Copy-Item $ExtractedExe -Destination "$InstallDir\PANN_POS_System.exe" -Force

# Create shortcuts
Write-Host "Creating shortcuts..." -ForegroundColor Yellow

$WshShell = New-Object -ComObject WScript.Shell

# Desktop shortcut
$DesktopShortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\$AppName.lnk")
$DesktopShortcut.TargetPath = "$InstallDir\PANN_POS_System.exe"
$DesktopShortcut.WorkingDirectory = $InstallDir
$DesktopShortcut.Description = $AppName
$DesktopShortcut.Save()

# Start menu shortcut
$StartMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\$AppName"
if (-not (Test-Path $StartMenuPath)) {
    New-Item -ItemType Directory -Path $StartMenuPath -Force | Out-Null
}

$StartMenuShortcut = $WshShell.CreateShortcut("$StartMenuPath\$AppName.lnk")
$StartMenuShortcut.TargetPath = "$InstallDir\PANN_POS_System.exe"
$StartMenuShortcut.WorkingDirectory = $InstallDir
$StartMenuShortcut.Description = $AppName
$StartMenuShortcut.Save()

# Create uninstaller
$UninstallScript = @"
# PANN POS System Uninstaller

Write-Host "Uninstalling $AppName..." -ForegroundColor Yellow

`$InstallDir = "$InstallDir"

# Remove files
if (Test-Path `$InstallDir) {
    Remove-Item -Path `$InstallDir -Recurse -Force
}

# Remove shortcuts
Remove-Item -Path "`$env:USERPROFILE\Desktop\$AppName.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "`$env:APPDATA\Microsoft\Windows\Start Menu\Programs\$AppName" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Uninstall complete!" -ForegroundColor Green
pause
"@

$UninstallScript | Out-File -FilePath "$InstallDir\Uninstall.ps1" -Encoding UTF8

# Registry entries for Add/Remove Programs
$RegistryPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
New-Item -Path $RegistryPath -Force | Out-Null
Set-ItemProperty -Path $RegistryPath -Name "DisplayName" -Value $AppName
Set-ItemProperty -Path $RegistryPath -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$InstallDir\Uninstall.ps1`""
Set-ItemProperty -Path $RegistryPath -Name "Publisher" -Value "PANN Systems"
Set-ItemProperty -Path $RegistryPath -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $RegistryPath -Name "NoModify" -Value 1 -Type DWord
Set-ItemProperty -Path $RegistryPath -Name "NoRepair" -Value 1 -Type DWord

# Cleanup temp files
Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "$AppName has been installed to:" -ForegroundColor Yellow
Write-Host $InstallDir -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the application:" -ForegroundColor Yellow
Write-Host "1. Double-click the desktop shortcut" -ForegroundColor White
Write-Host "2. Or go to Start Menu > $AppName" -ForegroundColor White
Write-Host ""
Write-Host "Access the application at: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
pause
'@

# Read the executable file
Write-Host "Reading executable file..." -ForegroundColor Yellow
$ExeBytes = [System.IO.File]::ReadAllBytes($ExePath)

# Create the installer executable by combining the script and the executable
Write-Host "Creating installer executable..." -ForegroundColor Yellow

# Convert installer script to bytes
$ScriptBytes = [System.Text.Encoding]::UTF8.GetBytes($InstallerScript)
$Marker = [System.Text.Encoding]::ASCII.GetBytes("__EMBEDDED_FILE_START__")

# Combine: script + marker + executable
$InstallerBytes = $ScriptBytes + $Marker + $ExeBytes

# Write the installer executable
$SetupExePath = Join-Path $OutputDir "PANN_POS_System_Setup.exe"
[System.IO.File]::WriteAllBytes($SetupExePath, $InstallerBytes)

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installer Created Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output: $SetupExePath" -ForegroundColor Cyan
Write-Host "Size: $([math]::Round($InstallerBytes.Length / 1MB, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "The installer is ready for distribution!" -ForegroundColor Green
Write-Host ""

