# PANN POS System - Windows Installer Summary

## Installer Features

### What the Installer Provides

**Professional Windows Setup:**
- ✅ Standard Windows installation wizard
- ✅ Installer/uninstaller in Programs and Features
- ✅ Desktop shortcut creation
- ✅ Start menu shortcuts
- ✅ Automatic MongoDB detection and warning
- ✅ Proper Windows registry entries
- ✅ Admin privileges handling
- ✅ Automatic .env file creation (preserves on uninstall)

### User Experience

**Installation Process:**
1. User double-clicks `PANN_POS_System_Setup.exe`
2. Standard Windows installer opens
3. Wizard guides through:
   - Welcome screen
   - Installation directory (default: `C:\Program Files\PANN\POS_System`)
   - Optional desktop icon creation
   - MongoDB detection check
4. Installation completes
5. Application can launch automatically
6. Shortcut appears on desktop (if selected)

**What Users Get:**
- Professional installation experience
- Uninstall capability through Control Panel
- Desktop shortcut for easy access
- Proper file organization in Program Files
- Data stored safely in user's home directory

## Build Options

### Option 1: Executable Only
```batch
build.bat
```
**Output:** `backend/dist/PANN_POS_System.exe`

**Distribution:** Just the .exe file
**User Action:** Double-click to run
**Pros:** Quick deployment, single file
**Cons:** No uninstaller, manual file management

### Option 2: Full Installer (Recommended)
```batch
build_with_installer.bat
```
**Output:**
- `backend/dist/PANN_POS_System.exe`
- `installer_output/PANN_POS_System_Setup.exe`

**Distribution:** Just the installer .exe
**User Action:** Run installer, follow wizard
**Pros:** Professional experience, proper Windows integration
**Cons:** Requires Inno Setup installed on build machine

## Installer Requirements

### For Building Installer:
- **Inno Setup 6** installed on development machine
  - Download: https://jrsoftware.org/isdl.php
  - Free and open-source

### For Running Installer:
- **Windows 10 or later** (x64)
- **Admin privileges** (first time)
- **MongoDB Community Edition** (recommended to install first)

## Installer Detection

The installer includes intelligent MongoDB detection:

**Checks for MongoDB in:**
- `C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe`
- `C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe`
- `C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe`
- `C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe`
- Custom installation paths

**If Not Found:**
- Warns user that MongoDB is required
- Provides download link
- Allows continuation if user prefers
- User can install MongoDB later

## Installation Directory

**Default Location:**
```
C:\Program Files\PANN\POS_System\
```

**User Data:**
```
C:\Users\[Username]\PANN_POS_Data\
```
- Database files
- Logs
- Configuration

**Separation:** Application and data are stored separately for proper backups.

## Uninstallation

**How to Uninstall:**
1. Open "Programs and Features" (Control Panel)
2. Find "PANN POS System"
3. Click "Uninstall"
4. Confirm uninstallation

**What Gets Removed:**
- Application files
- Desktop shortcuts
- Start menu shortcuts
- Registry entries
- **User data is preserved** (in PANN_POS_Data folder)

**Manual Cleanup:**
To fully remove user data:
- Delete: `C:\Users\[Username]\PANN_POS_Data\`

## Customization

### Editing Installer.iss

**Version Number:**
```iss
AppVersion=1.0.0
```

**Company Info:**
```iss
AppPublisher=PANN Systems
AppPublisherURL=https://www.pann.com
```

**Installation Path:**
```iss
DefaultDirName={autopf}\PANN\POS_System
```

**Add License File:**
```iss
LicenseFile=LICENSE.txt
```

**Add Icon:**
```iss
SetupIconFile=app_icon.ico
```

**Change Compression:**
```iss
Compression=lzma2/ultra  ; Maximum compression
; or
Compression=zip  ; Faster compression
```

## Troubleshooting

### Build Issues

**Error: "Inno Setup not found"**
- Install Inno Setup 6 from official website
- Restart command prompt
- Try build again

**Error: "installer.iss not found"**
- Ensure you're running `build_with_installer.bat` from project root
- Check file paths in installer.iss

**Error: "PANN_POS_System.exe not found"**
- Run `build.bat` first to create executable
- Check `backend/dist/PANN_POS_System.exe` exists

### Installation Issues

**Installer Won't Run:**
- Check if downloaded file is blocked
- Right-click → Properties → Unblock
- Run as Administrator

**"MongoDB Not Found" Warning:**
- Normal if MongoDB not installed
- Install MongoDB before or after POS installation
- Link provided in warning message

**Installation Fails:**
- Check Windows Event Viewer for errors
- Ensure you have admin privileges
- Try installing to different directory
- Disable antivirus temporarily

**Application Won't Start After Install:**
- Check MongoDB is installed and running
- View logs in: `C:\Users\[Username]\PANN_POS_Data\logs\`
- Run application as Administrator
- Check firewall isn't blocking port 8000

## Distribution Checklist

When distributing the installer:

- [ ] Build completed successfully
- [ ] Test installer on clean Windows machine
- [ ] Verify MongoDB detection works
- [ ] Test with MongoDB installed and not installed
- [ ] Verify shortcuts are created
- [ ] Test uninstallation
- [ ] Confirm user data is preserved
- [ ] Check installer size (should be ~200-250 MB)
- [ ] Upload to distribution location
- [ ] Create download instructions
- [ ] Update version numbers
- [ ] Prepare release notes

## Comparison: Installer vs Standalone

| Feature | Standalone .exe | Windows Installer |
|---------|----------------|-------------------|
| **User Experience** | Double-click to run | Professional wizard |
| **Uninstaller** | Manual deletion | Add/Remove Programs |
| **Shortcuts** | Manual creation | Automatic |
| **Registry** | None | Proper entries |
| **Updates** | Replace file | Run new installer |
| **Multi-user** | Shared location | Per-user data |
| **Cleanup** | Manual | Automatic |
| **Detection** | None | MongoDB check |
| **Professional Look** | No | Yes |
| **Windows Integration** | Minimal | Full |

## Recommendation

**Use the Installer for:**
- Production deployments
- Customer distribution
- Multi-user environments
- Long-term installations
- Professional appearance

**Use Standalone .exe for:**
- Quick testing
- Internal development
- Single-user systems
- Quick deployments
- Portability needs

## Next Steps

1. Install Inno Setup 6
2. Run `build_with_installer.bat`
3. Test installer on clean system
4. Create distribution package
5. Deploy to users

## Additional Resources

- **Inno Setup Documentation:** https://jrsoftware.org/ishelp/
- **Example Inno Scripts:** https://github.com/jrsoftware/issrc/tree/master/Examples
- **Build Script:** `build_with_installer.bat`
- **Installation Guide:** `EXE_INSTALLATION_GUIDE.md`


