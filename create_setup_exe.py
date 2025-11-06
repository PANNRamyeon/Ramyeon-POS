"""
Create professional .exe installer using pyinno-setup
This creates a proper Windows installer without needing Inno Setup installed
"""

import os
from pathlib import Path
from pyinno_setup import inno

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent
INSTALLER_OUTPUT = PROJECT_ROOT / "installer_output"
EXE_PATH = PROJECT_ROOT / "backend" / "dist" / "PANN_POS_System.exe"
ISS_PATH = PROJECT_ROOT / "installer.iss"

def main():
    print("=" * 60)
    print("Creating Windows Installer with pyinno-setup")
    print("=" * 60)
    print()
    
    # Check if executable exists
    if not EXE_PATH.exists():
        print(f"ERROR: Executable not found at {EXE_PATH}")
        print("Please run build.bat first to create the executable.")
        return 1
    
    # Read the existing .iss file
    if not ISS_PATH.exists():
        print(f"ERROR: Inno Setup script not found at {ISS_PATH}")
        return 1
    
    print("Found:")
    print(f"  + Executable: {EXE_PATH.name} ({EXE_PATH.stat().st_size / (1024*1024):.2f} MB)")
    print(f"  + Installer script: {ISS_PATH.name}")
    print()
    
    # Create output directory
    INSTALLER_OUTPUT.mkdir(exist_ok=True)
    
    print("Compiling installer with pyinno-setup...")
    print("(This embeds the entire Inno Setup compiler - takes 2-3 minutes)")
    print()
    
    # Compile the installer
    try:
        result = inno.build(
            str(ISS_PATH),
            str(INSTALLER_OUTPUT)
        )
        
        if result:
            print()
            print("=" * 60)
            print("SUCCESS: Installer Created Successfully!")
            print("=" * 60)
            print()
            print("Output location: installer_output")
            print()
            
            # Find the generated installer
            installers = list(INSTALLER_OUTPUT.glob("*.exe"))
            if installers:
                installer_size = installers[0].stat().st_size / (1024 * 1024)
                print(f"Installer: {installers[0].name}")
                print(f"Size: {installer_size:.2f} MB")
                print()
                print("Ready to distribute to clients!")
                print()
                print("Next steps:")
                print("  1. Send the installer .exe to your client")
                print("  2. They double-click to install")
                print("  3. No special steps needed - just works!")
            
            return 0
        else:
            print()
            print("ERROR: Failed to compile installer")
            return 1
            
    except Exception as e:
        print()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Troubleshooting:")
        print("1. Ensure the executable is built: run build.bat first")
        print("2. Check that installer.iss exists and is valid")
        return 1

if __name__ == "__main__":
    exit(main())

