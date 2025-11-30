# Script to wait for Inno Setup installation and then build the installer

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Inno Setup Installation Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Inno Setup is already installed
$InnoPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

$InnoFound = $null
foreach ($path in $InnoPaths) {
    if (Test-Path $path) {
        $InnoFound = $path
        break
    }
}

if ($InnoFound) {
    Write-Host "Inno Setup is already installed at: $InnoFound" -ForegroundColor Green
    Write-Host ""
    Write-Host "Building installer now..." -ForegroundColor Yellow
    Write-Host ""
    
    # Build the installer
    & $InnoFound "installer.iss"
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path "installer_output\PANN_POS_System_Setup.exe")) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Installer Created Successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        $setup = Get-Item "installer_output\PANN_POS_System_Setup.exe"
        Write-Host "Output: $($setup.FullName)" -ForegroundColor Cyan
        Write-Host "Size: $([math]::Round($setup.Length / 1MB, 2)) MB" -ForegroundColor Cyan
        Write-Host "Last Modified: $($setup.LastWriteTime)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "This is a proper Windows installer executable!" -ForegroundColor Green
        Write-Host "You can now distribute this installer." -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create installer!" -ForegroundColor Red
        Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
    
} else {
    Write-Host "Inno Setup is not installed yet." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Cyan
    Write-Host "1. Download Inno Setup 6 from: https://jrsoftware.org/isdl.php" -ForegroundColor White
    Write-Host "2. Install it (use default installation path)" -ForegroundColor White
    Write-Host "3. Run this script again: .\install_inno_and_build.ps1" -ForegroundColor White
    Write-Host ""
    
    # Open download page
    $response = Read-Host "Would you like to open the download page now? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Start-Process "https://jrsoftware.org/isdl.php"
        Write-Host ""
        Write-Host "After installing Inno Setup, run this script again to build the installer." -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Alternatively, you can manually build after installation:" -ForegroundColor Yellow
    Write-Host '  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss' -ForegroundColor Cyan
    Write-Host ""
}

