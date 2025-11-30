@echo off
REM PANN POS System Installer
REM This installer will install PANN POS System to Program Files

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

REM Get the directory where this installer is located
set "INSTALLER_DIR=%~dp0"
set "INSTALL_DIR=%ProgramFiles%\PANN\POS_System"

echo.
echo Installing to: %INSTALL_DIR%
echo.

REM Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy the executable
echo Copying files...
if exist "%INSTALLER_DIR%PANN_POS_System.exe" (
    copy /Y "%INSTALLER_DIR%PANN_POS_System.exe" "%INSTALL_DIR%\" >nul
    if %errorLevel% neq 0 (
        echo ERROR: Failed to copy executable!
        pause
        exit /b 1
    )
) else (
    echo ERROR: PANN_POS_System.exe not found in installer directory!
    echo Please ensure the executable is in the same folder as this installer.
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
$StartMenuShortcut.Save(); ^
$UninstallShortcut = $WshShell.CreateShortcut(\"$StartMenuPath\Uninstall.lnk\"); ^
$UninstallShortcut.TargetPath = 'powershell.exe'; ^
$UninstallShortcut.Arguments = '-ExecutionPolicy Bypass -File \"%INSTALL_DIR%\Uninstall.ps1\"'; ^
$UninstallShortcut.Description = 'Uninstall PANN POS System'; ^
$UninstallShortcut.Save()"

REM Create uninstaller script
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

REM Add to Add/Remove Programs
echo Registering in Add/Remove Programs...
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PANN POS System" /v DisplayName /t REG_SZ /d "PANN POS System" /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PANN POS System" /v UninstallString /t REG_SZ /d "powershell.exe -ExecutionPolicy Bypass -File \"%INSTALL_DIR%\Uninstall.ps1\"" /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PANN POS System" /v Publisher /t REG_SZ /d "PANN Systems" /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PANN POS System" /v DisplayVersion /t REG_SZ /d "1.0.0" /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PANN POS System" /v NoModify /t REG_DWORD /d 1 /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\PANN POS System" /v NoRepair /t REG_DWORD /d 1 /f >nul

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo PANN POS System has been installed to:
echo %INSTALL_DIR%
echo.
echo You can now run the application from:
echo - Desktop shortcut
echo - Start Menu ^> PANN POS System
echo.
echo Access the application at: http://localhost:8000
echo.
pause

