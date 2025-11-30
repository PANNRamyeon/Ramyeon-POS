# How to Rebuild PANN_POS_System_Setup.exe

## The Problem
The current installer file is not a proper Windows executable - it's a batch script. The original installer was built using **Inno Setup**, which creates proper Windows installers.

## Solution: Install Inno Setup and Rebuild

### Step 1: Download and Install Inno Setup
1. Download Inno Setup 6 from: https://jrsoftware.org/isdl.php
2. Run the installer and complete the installation
3. It will install to either:
   - `C:\Program Files (x86)\Inno Setup 6\` or
   - `C:\Program Files\Inno Setup 6\`

### Step 2: Rebuild the Installer
After installing Inno Setup, run this command:

```powershell
# Check which path Inno Setup is installed to
$InnoPath = if (Test-Path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe") {
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
} else {
    "C:\Program Files\Inno Setup 6\ISCC.exe"
}

# Build the installer
& $InnoPath installer.iss
```

Or simply run:
```batch
build_with_installer.bat
```

The installer will be created at: `installer_output\PANN_POS_System_Setup.exe`

## Alternative: Use PowerShell Installer
If you can't install Inno Setup, use the PowerShell installer that's already available:
- `installer_output\Install_PANN_POS_System.ps1`

This works without any additional software, but users need to right-click and select "Run with PowerShell".

