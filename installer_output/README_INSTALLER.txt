PANN POS System Installer Files
================================

This directory contains the installer files for PANN POS System.

INSTALLER FILES:
----------------
1. PANN_POS_System_Setup.bat
   - Batch file installer (works immediately)
   - Right-click > Run as Administrator
   - This is the recommended installer if the .exe doesn't work

2. PANN_POS_System_Setup.exe
   - Windows installer executable
   - Right-click > Run as Administrator
   - Note: If Windows blocks this file, use the .bat file instead

3. Install_PANN_POS_System.ps1
   - PowerShell installer script
   - Right-click > Run with PowerShell
   - Alternative installer method

4. PANN_POS_System.exe
   - The main application executable
   - This is what gets installed by the installer

HOW TO USE:
-----------
Option 1 (Recommended): Use PANN_POS_System_Setup.bat
  1. Right-click on PANN_POS_System_Setup.bat
  2. Select "Run as Administrator"
  3. Follow the installation prompts

Option 2: Use PANN_POS_System_Setup.exe
  1. Right-click on PANN_POS_System_Setup.exe
  2. Select "Run as Administrator"
  3. If Windows shows a security warning, click "More info" > "Run anyway"
  4. Follow the installation prompts

Option 3: Use PowerShell installer
  1. Right-click on Install_PANN_POS_System.ps1
  2. Select "Run with PowerShell"
  3. Follow the installation prompts

INSTALLATION LOCATION:
----------------------
The application will be installed to:
C:\Program Files\PANN\POS_System

After installation, you can run the application from:
- Desktop shortcut
- Start Menu > PANN POS System

Access the application at: http://localhost:8000

NOTE:
-----
For a proper Windows installer executable (like the original), Inno Setup 6 
is required. The batch file installer works the same way but doesn't require 
Inno Setup to be installed.

