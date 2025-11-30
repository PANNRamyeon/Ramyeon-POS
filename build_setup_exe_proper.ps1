# Build PANN_POS_System_Setup.exe as a proper batch file installer
# This creates a .bat file that can be renamed to .exe and will work

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

# Create installer batch file
$InstallerBatch = @'
@echo off
REM PANN POS System Installer
REM This is a self-extracting installer

setlocal enabledelayedexpansion

echo ========================================
echo PANN POS System Installer
echo ========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This installer requires Administrator privileges.
    echo Please right-click and select 'Run as Administrator'
    pause
    exit /b 1
)

REM Check for MongoDB
echo Checking for MongoDB...
set MONGO_FOUND=0
if exist "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe" set MONGO_FOUND=1
if exist "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" set MONGO_FOUND=1
if exist "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" set MONGO_FOUND=1
if exist "C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe" set MONGO_FOUND=1

if %MONGO_FOUND%==0 (
    echo WARNING: MongoDB Community Edition not found!
    echo PANN POS System requires MongoDB to function.
    echo.
    echo Please install MongoDB Community Edition from:
    echo https://www.mongodb.com/try/download/community
    echo.
    set /p CONTINUE="Continue installation anyway? (y/n): "
    if /i not "!CONTINUE!"=="y" exit /b 1
)

REM Get installer location and create temp directory
set "INSTALLER_PATH=%~f0"
set "TEMP_DIR=%TEMP%\PANN_POS_Setup_%RANDOM%"
mkdir "%TEMP_DIR%" >nul 2>&1

REM Installation directory
set "INSTALL_DIR=%ProgramFiles%\PANN\POS_System"
echo.
echo Installing to: %INSTALL_DIR%

REM Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Extract embedded executable
echo Extracting files...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$bytes = [System.IO.File]::ReadAllBytes('%INSTALLER_PATH%'); ^
$marker = [System.Text.Encoding]::ASCII.GetBytes('__EMBEDDED_EXE_START__'); ^
$markerIndex = -1; ^
for ($i = 0; $i -lt ($bytes.Length - $marker.Length); $i++) { ^
    $match = $true; ^
    for ($j = 0; $j -lt $marker.Length; $j++) { ^
        if ($bytes[$i + $j] -ne $marker[$j]) { $match = $false; break } ^
    }; ^
    if ($match) { $MarkerIndex = $i + $marker.Length; break } ^
}; ^
if ($MarkerIndex -ne -1) { ^
    $EmbeddedBytes = $bytes[$MarkerIndex..($bytes.Length - 1)]; ^
    [System.IO.File]::WriteAllBytes('%INSTALL_DIR%\PANN_POS_System.exe', $EmbeddedBytes) ^
} else { ^
    Write-Host 'ERROR: Could not extract embedded executable!' -ForegroundColor Red; ^
    exit 1 ^
}"

if %errorLevel% neq 0 (
    echo ERROR: Failed to extract files!
    pause
    exit /b 1
)

REM Create shortcuts using PowerShell
echo Creating shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$WshShell = New-Object -ComObject WScript.Shell; ^
$DesktopShortcut = $WshShell.CreateShortcut('$env:USERPROFILE\Desktop\PANN POS System.lnk'); ^
$DesktopShortcut.TargetPath = '%INSTALL_DIR%\PANN_POS_System.exe'; ^
$DesktopShortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
$DesktopShortcut.Description = 'PANN POS System'; ^
$DesktopShortcut.Save(); ^
$StartMenuPath = '$env:APPDATA\Microsoft\Windows\Start Menu\Programs\PANN POS System'; ^
if (-not (Test-Path $StartMenuPath)) { New-Item -ItemType Directory -Path $StartMenuPath -Force | Out-Null }; ^
$StartMenuShortcut = $WshShell.CreateShortcut(\"$StartMenuPath\PANN POS System.lnk\"); ^
$StartMenuShortcut.TargetPath = '%INSTALL_DIR%\PANN_POS_System.exe'; ^
$StartMenuShortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
$StartMenuShortcut.Description = 'PANN POS System'; ^
$StartMenuShortcut.Save()"

REM Create uninstaller
echo Creating uninstaller...
(
echo # PANN POS System Uninstaller
echo Write-Host "Uninstalling PANN POS System..." -ForegroundColor Yellow
echo $InstallDir = "%INSTALL_DIR%"
echo if ^(Test-Path $InstallDir^) { Remove-Item -Path $InstallDir -Recurse -Force }
echo Remove-Item -Path "$env:USERPROFILE\Desktop\PANN POS System.lnk" -Force -ErrorAction SilentlyContinue
echo Remove-Item -Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\PANN POS System" -Recurse -Force -ErrorAction SilentlyContinue
echo Write-Host "Uninstall complete!" -ForegroundColor Green
echo pause
) > "%INSTALL_DIR%\Uninstall.ps1"

REM Cleanup
rmdir /s /q "%TEMP_DIR%" >nul 2>&1

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo PANN POS System has been installed to:
echo %INSTALL_DIR%
echo.
echo Access the application at: http://localhost:8000
echo.
pause
'@

# Read the executable file
Write-Host "Reading executable file..." -ForegroundColor Yellow
$ExeBytes = [System.IO.File]::ReadAllBytes($ExePath)

# Convert installer batch to bytes
$BatchBytes = [System.Text.Encoding]::ASCII.GetBytes($InstallerBatch)
$Marker = [System.Text.Encoding]::ASCII.GetBytes("__EMBEDDED_EXE_START__")

# Combine: batch script + marker + executable
$InstallerBytes = $BatchBytes + $Marker + $ExeBytes

# Write the installer
$SetupExePath = Join-Path $OutputDir "PANN_POS_System_Setup.exe"
Write-Host "Creating installer executable..." -ForegroundColor Yellow
[System.IO.File]::WriteAllBytes($SetupExePath, $InstallerBytes)

# Create a .bat version as backup that definitely works
$SetupBatPath = Join-Path $OutputDir "PANN_POS_System_Setup.bat"
[System.IO.File]::WriteAllBytes($SetupBatPath, $InstallerBytes)

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installer Created Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output files:" -ForegroundColor Cyan
Write-Host "  - $SetupExePath" -ForegroundColor White
Write-Host "  - $SetupBatPath (backup - guaranteed to work)" -ForegroundColor White
Write-Host ""
Write-Host "Size: $([math]::Round($InstallerBytes.Length / 1MB, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: The .exe file is actually a batch script." -ForegroundColor Yellow
Write-Host "If Windows blocks it, use the .bat file instead, or:" -ForegroundColor Yellow
Write-Host "Right-click > Properties > Unblock > OK" -ForegroundColor Yellow
Write-Host ""

