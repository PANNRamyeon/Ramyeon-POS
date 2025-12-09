@echo off
echo ========================================
echo PANN POS System - Full Build with Installer
echo ========================================
echo.

REM Step 1: Build the executable
echo Building executable...
call build.bat
if errorlevel 1 (
    echo ERROR: Failed to build executable!
    pause
    exit /b 1
)

REM Step 2: Check if Inno Setup is installed
echo.
echo Checking for Inno Setup...
set INNOSETUP_PATH=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set INNOSETUP_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set INNOSETUP_PATH=C:\Program Files\Inno Setup 6\ISCC.exe
) else (
    echo WARNING: Inno Setup not found!
    echo.
    echo Please install Inno Setup 6 to create Windows installer:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo Executable is ready at: backend\dist\PANN_POS_System.exe
    pause
    exit /b 0
)

REM Step 3: Create installer
echo Found Inno Setup at: %INNOSETUP_PATH%
echo.
echo Creating Windows installer...
"%INNOSETUP_PATH%" installer.iss
if errorlevel 1 (
    echo ERROR: Failed to create installer!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo Output files:
echo   - Executable: backend\dist\PANN_POS_System.exe
echo   - Installer:   installer_output\PANN_POS_System_Setup.exe
echo.
echo Distribution package ready!
pause


