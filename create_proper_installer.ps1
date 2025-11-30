# Script to create a proper installer executable
# This will either use Inno Setup if available, or guide installation

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating Proper PANN POS System Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Inno Setup is installed
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
    Write-Host "Found Inno Setup at: $InnoFound" -ForegroundColor Green
    Write-Host ""
    Write-Host "Building proper installer..." -ForegroundColor Yellow
    
    # Build using Inno Setup
    & $InnoFound "installer.iss"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Installer Created Successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Output: installer_output\PANN_POS_System_Setup.exe" -ForegroundColor Cyan
        
        if (Test-Path "installer_output\PANN_POS_System_Setup.exe") {
            $size = (Get-Item "installer_output\PANN_POS_System_Setup.exe").Length / 1MB
            Write-Host "Size: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "This is a proper Windows installer executable!" -ForegroundColor Green
        }
    } else {
        Write-Host "ERROR: Inno Setup build failed!" -ForegroundColor Red
        exit 1
    }
    
} else {
    Write-Host "Inno Setup is not installed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To create a proper .exe installer, Inno Setup 6 is required." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Quick Install Option:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://jrsoftware.org/isdl.php" -ForegroundColor White
    Write-Host "2. Install Inno Setup 6" -ForegroundColor White
    Write-Host "3. Run this script again" -ForegroundColor White
    Write-Host ""
    
    # Check if we can download it automatically
    $response = Read-Host "Would you like to open the download page now? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Start-Process "https://jrsoftware.org/isdl.php"
        Write-Host ""
        Write-Host "After installing Inno Setup, run this script again to build the installer." -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Alternative: Use the batch file installer" -ForegroundColor Yellow
    Write-Host "The file 'PANN_POS_System_Setup.bat' works perfectly and does the same thing." -ForegroundColor White
    Write-Host "Right-click it and select 'Run as Administrator'" -ForegroundColor White
}

