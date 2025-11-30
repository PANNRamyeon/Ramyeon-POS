# Build PANN_POS_System_Setup.exe using IExpress (Windows built-in)
# Creates a proper Windows installer executable

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building PANN POS System Setup Installer" -ForegroundColor Cyan
Write-Host "Using Windows IExpress" -ForegroundColor Cyan
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

# Create temp directory for IExpress
$TempDir = Join-Path $env:TEMP "PANN_Installer_$(Get-Random)"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

try {
    # Copy executable to temp directory
    Copy-Item $ExePath -Destination $TempDir -Force
    
    # Create installation script
    $InstallScript = @"
@echo off
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
    if /i not "%CONTINUE%"=="y" exit /b 1
)

REM Installation directory
set INSTALL_DIR=%ProgramFiles%\PANN\POS_System
echo.
echo Installing to: %INSTALL_DIR%

REM Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy files
echo Copying files...
copy /Y "PANN_POS_System.exe" "%INSTALL_DIR%\" >nul

REM Create shortcuts using PowerShell
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $DesktopShortcut = $WshShell.CreateShortcut('$env:USERPROFILE\Desktop\PANN POS System.lnk'); $DesktopShortcut.TargetPath = '%INSTALL_DIR%\PANN_POS_System.exe'; $DesktopShortcut.WorkingDirectory = '%INSTALL_DIR%'; $DesktopShortcut.Description = 'PANN POS System'; $DesktopShortcut.Save()"

powershell -Command "if (-not (Test-Path '$env:APPDATA\Microsoft\Windows\Start Menu\Programs\PANN POS System')) { New-Item -ItemType Directory -Path '$env:APPDATA\Microsoft\Windows\Start Menu\Programs\PANN POS System' -Force | Out-Null }; $WshShell = New-Object -ComObject WScript.Shell; $StartMenuShortcut = $WshShell.CreateShortcut('$env:APPDATA\Microsoft\Windows\Start Menu\Programs\PANN POS System\PANN POS System.lnk'); $StartMenuShortcut.TargetPath = '%INSTALL_DIR%\PANN_POS_System.exe'; $StartMenuShortcut.WorkingDirectory = '%INSTALL_DIR%'; $StartMenuShortcut.Description = 'PANN POS System'; $StartMenuShortcut.Save()"

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
"@
    
    $InstallScript | Out-File -FilePath "$TempDir\install.cmd" -Encoding ASCII
    
    # Create IExpress SED file
    $SedFile = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%AppName% Installation
DisplayLicense=
FinishMessage=Installation complete. You can now run PANN POS System from the desktop shortcut or Start Menu.
TargetName=$OutputDir\PANN_POS_System_Setup.exe
FriendlyName=PANN POS System Setup
AppLaunched=install.cmd
PostInstallCmd=<None>
AdminQuietInstCmd=
UserQuietInstCmd=
SourceFiles=$TempDir\

[Strings]
AppName=PANN POS System
FILE0="PANN_POS_System.exe"
FILE1="install.cmd"
"@
    
    $SedFilePath = Join-Path $TempDir "installer.sed"
    $SedFile | Out-File -FilePath $SedFilePath -Encoding ASCII
    
    # Build using IExpress
    Write-Host "Building installer with IExpress..." -ForegroundColor Yellow
    $IExpressPath = "$env:SystemRoot\System32\iexpress.exe"
    
    if (-not (Test-Path $IExpressPath)) {
        Write-Host "ERROR: IExpress not found!" -ForegroundColor Red
        exit 1
    }
    
    # Run IExpress in silent mode
    $Process = Start-Process -FilePath $IExpressPath -ArgumentList "/N", $SedFilePath -Wait -PassThru -NoNewWindow
    
    if ($Process.ExitCode -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Installer Created Successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Output: $OutputDir\PANN_POS_System_Setup.exe" -ForegroundColor Cyan
        
        if (Test-Path "$OutputDir\PANN_POS_System_Setup.exe") {
            $Size = (Get-Item "$OutputDir\PANN_POS_System_Setup.exe").Length / 1MB
            Write-Host "Size: $([math]::Round($Size, 2)) MB" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "The installer is ready for distribution!" -ForegroundColor Green
        } else {
            Write-Host "WARNING: Installer file not found at expected location." -ForegroundColor Yellow
        }
    } else {
        Write-Host "ERROR: IExpress build failed with exit code: $($Process.ExitCode)" -ForegroundColor Red
        exit 1
    }
    
} finally {
    # Cleanup temp directory
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""

