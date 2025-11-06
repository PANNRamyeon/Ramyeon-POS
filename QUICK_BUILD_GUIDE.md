# Quick Build Guide - PANN POS System

## 🚀 Fast Track Build

### Step 1: Install Prerequisites

**Required:**
- ✅ Node.js (https://nodejs.org/)
- ✅ Python 3.9+ (https://python.org/)
- ✅ MongoDB Community Edition (https://www.mongodb.com/try/download/community)

**Optional (for installer):**
- ✅ Inno Setup 6 (https://jrsoftware.org/isdl.php)

### Step 2: Build

**Choose one:**

**A) Executable Only:**
```batch
build.bat
```

**B) Full Installer:**
```batch
build_with_installer.bat
```

### Step 3: Distribute

**Output Files:**
- `backend/dist/PANN_POS_System.exe` - Standalone executable
- `installer_output/PANN_POS_System_Setup.exe` - Windows installer (if using Option B)

## 📦 What Users Get

### Option A: Standalone Executable
- Single `.exe` file (~200-250 MB)
- Double-click to run
- Portable - can run from any location
- Manual uninstallation

### Option B: Windows Installer ✅ RECOMMENDED
- Professional setup wizard
- Auto-creates shortcuts
- Proper Windows integration
- Clean uninstaller in Control Panel
- MongoDB detection and warnings

## 🎯 Build Comparison

| Feature | Standalone | Installer |
|---------|-----------|-----------|
| **Build Command** | `build.bat` | `build_with_installer.bat` |
| **Output File** | PANN_POS_System.exe | PANN_POS_System_Setup.exe |
| **User Action** | Double-click | Run installer wizard |
| **Shortcuts** | ❌ Manual | ✅ Automatic |
| **Uninstaller** | ❌ Manual delete | ✅ Control Panel |
| **Professional Look** | ⚠️ Basic | ✅ Professional |
| **Best For** | Quick testing | Production deployment |

## ⚙️ Build Process

Both scripts do the same thing:

1. **Build Frontend** → Vue.js to `backend/static/frontend/`
2. **Setup Python** → Create venv, install dependencies
3. **Collect Static** → Django static files
4. **Package** → PyInstaller creates .exe
5. **Installer (Option B)** → Inno Setup creates installer

**Total Time:** ~5-10 minutes

## 📝 Quick Checklist

**Before Building:**
- [ ] Node.js installed
- [ ] Python installed
- [ ] MongoDB installed (for testing)
- [ ] Git repository cloned
- [ ] `.env` file exists in `backend/`

**For Installer Build:**
- [ ] Inno Setup 6 installed

**After Building:**
- [ ] Test executable locally
- [ ] Verify MongoDB auto-start works
- [ ] Test offline mode
- [ ] Check sync functionality
- [ ] Test installer on clean system

## 🐛 Common Issues

**Build fails at npm step:**
- `cd frontend && npm install && npm run build`

**Build fails at Python step:**
- `cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt`

**PyInstaller not found:**
- `pip install pyinstaller==6.3.0`

**Inno Setup not found:**
- Download from https://jrsoftware.org/isdl.php
- Restart command prompt

**Build succeeds but app won't run:**
- Check MongoDB is installed
- View logs in `PANN_POS_Data/logs/app.log`
- Run as Administrator

## 📚 Documentation

- **Build Details:** `BUILD_NOTES.md`
- **Installer Info:** `INSTALLER_SUMMARY.md`
- **User Guide:** `EXE_INSTALLATION_GUIDE.md`
- **Main Readme:** `README.md`

## 🎉 That's It!

Run `build.bat` or `build_with_installer.bat` and you're done!

For detailed information, check the other documentation files.


