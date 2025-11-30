# Script to help install Inno Setup and rebuild the installer
# This restores the original build process

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PANN POS System - Installer Setup Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Inno Setup is already installed
$InnoPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    "C:\Program Files\Inno Setup 5\ISCC.exe"
)

$InnoFound = $null
foreach ($path in $InnoPaths) {
    if (Test-Path $path) {
        $InnoFound = $path
        break
    }
}

if ($InnoFound) {
    Write-Host "Inno Setup found at: $InnoFound" -ForegroundColor Green
    Write-Host ""
    Write-Host "Rebuilding installer with original build process..." -ForegroundColor Yellow
    Write-Host ""
    
    # Run the original build script
    & cmd /c "build_with_installer.bat"
    
} else {
    Write-Host "Inno Setup is not installed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To restore the original installer build process:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Download Inno Setup 6 from:" -ForegroundColor White
    Write-Host "   https://jrsoftware.org/isdl.php" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Install Inno Setup 6 (use default installation path)" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Run this script again, or run:" -ForegroundColor White
    Write-Host "   build_with_installer.bat" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "The installer.iss file is unchanged and ready to use." -ForegroundColor Green
    Write-Host "Once Inno Setup is installed, the build will work exactly as before." -ForegroundColor Green
    Write-Host ""
    
    # Offer to open download page
    $response = Read-Host "Would you like to open the Inno Setup download page? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Start-Process "https://jrsoftware.org/isdl.php"
    }
}

