# PANN POS System - Build Notes

## Quick Start Build

### Option 1: Build Executable Only
To build the executable, simply run:
```batch
build.bat
```

### Option 2: Build with Windows Installer
To build executable + Windows installer:
```batch
build_with_installer.bat
```

**Note:** Option 2 requires Inno Setup 6 to be installed. Download from: https://jrsoftware.org/isdl.php

### What Gets Built

**build.bat** creates:
- **Executable:** `backend/dist/PANN_POS_System.exe`

**build_with_installer.bat** creates:
- **Executable:** `backend/dist/PANN_POS_System.exe`
- **Installer:** `installer_output/PANN_POS_System_Setup.exe`

Both scripts will:
1. Build the Vue.js frontend to `backend/static/frontend/`
2. Install all Python dependencies
3. Collect Django static files
4. Package everything into a single .exe using PyInstaller
5. (Optional) Create professional Windows installer with Inno Setup

## Build Output

After successful build:
- **Executable:** `backend/dist/PANN_POS_System.exe`
- **Installer:** `installer_output/PANN_POS_System_Setup.exe` (if using build_with_installer.bat)
- **Size:** Approximately 200-250 MB (includes Python runtime)

## Manual Build Steps

If you need to build manually:

### 1. Frontend Build
```batch
cd frontend
npm install
npm run build
cd ..
```

### 2. Backend Setup
```batch
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py collectstatic --noinput --settings=settings.production
```

### 3. PyInstaller Build
```batch
pyinstaller build_exe.spec --clean --noconfirm
```

## Important Notes

### Environment Variables
- The `.env` file must be in the `backend/` directory
- It will be included in the .exe automatically
- Users need this file to configure cloud database connection

### MongoDB Auto-Start
- The system will auto-start MongoDB if not running
- Requires MongoDB Community Edition installed
- Looks for MongoDB in: `C:\Program Files\MongoDB\Server\[version]\bin\mongod.exe`

### Static Files
- Vue.js frontend is built to: `backend/static/frontend/`
- Django serves static files from: `backend/static/`
- All static assets are bundled in the .exe

### Production Settings
- Uses `settings.production` by default
- `DEBUG=False` for production
- Uses Whitenoise for static file serving

## Testing the Build

### Before Distribution
1. Test the .exe locally
2. Verify MongoDB auto-start works
3. Test offline mode
4. Verify cloud sync
5. Check all major features

### Test Checklist
- [ ] Application launches without errors
- [ ] MongoDB auto-starts (if not running as service)
- [ ] Can access web interface at http://localhost:8000
- [ ] Login works
- [ ] Can create sale in online mode
- [ ] Can create sale in offline mode
- [ ] Data syncs after reconnect
- [ ] Frontend UI loads correctly
- [ ] All API endpoints accessible
- [ ] Static files (CSS, JS, images) load

## Troubleshooting Build Issues

### Issue: "npm not found"
**Solution:** Install Node.js from https://nodejs.org/

### Issue: Frontend build fails
**Solution:** 
```batch
cd frontend
rm -rf node_modules
npm install
npm run build
```

### Issue: PyInstaller not found
**Solution:**
```batch
cd backend
venv\Scripts\activate
pip install pyinstaller==6.3.0
```

### Issue: Inno Setup not found (for installer)
**Solution:** Install Inno Setup 6 from https://jrsoftware.org/isdl.php

### Issue: Missing hidden imports
**Solution:** Add missing imports to `build_exe.spec` in the `hiddenimports` list

### Issue: Large .exe size
**Solution:** This is normal - Python + Django + all dependencies = ~200MB. Consider using --onedir mode for faster startup.

## Distribution Package

### Recommended Structure

**Without Installer:**
```
PANN_POS_System_v1.0.0/
├── PANN_POS_System.exe
├── README.txt (instructions)
├── EXE_INSTALLATION_GUIDE.md
└── MongoDB_Installation.pdf (if not included)
```

**With Installer (Recommended):**
```
PANN_POS_System_v1.0.0/
├── PANN_POS_System_Setup.exe  (Main installer)
├── README.txt
└── EXE_INSTALLATION_GUIDE.md
```

The installer automatically:
- Checks for MongoDB installation
- Creates desktop shortcuts
- Adds uninstaller to Programs and Features
- Manages installation directory
- Handles admin permissions

### Optional: MongoDB Installer
If distributing to users without MongoDB:
- Include MongoDB Community Edition installer
- Add installation instructions in installer
- Or use embedded MongoDB (more complex setup)

## Updates & Versioning

### Version Bump Process
1. Update version in code/readme
2. Rebuild .exe
3. Test thoroughly
4. Create distribution package
5. Document changes in CHANGELOG

### Incremental Updates
- Users can replace .exe file
- Data in `PANN_POS_Data` is preserved
- No migration needed for most updates

## Performance Tips

### Startup Speed
- First launch: ~10-15 seconds (MongoDB check)
- Subsequent launches: ~5-8 seconds
- Use --onedir mode to reduce startup time

### Memory Usage
- Typical usage: 200-400 MB RAM
- With large dataset: 500 MB - 1 GB RAM
- MongoDB: additional 200-300 MB RAM

## Security Considerations

### Included in Build
- All Python code is compiled (bytecode)
- Still needs .env for credentials
- No source code exposure

### Recommendations
- Users should keep .exe in a secure location
- Regular backups of `PANN_POS_Data`
- Don't share .env file
- Use strong SECRET_KEY in production

## Deployment Checklist

- [ ] Build completed successfully
- [ ] .exe tested on clean Windows machine
- [ ] MongoDB auto-start verified
- [ ] Offline mode tested
- [ ] Cloud sync verified
- [ ] Installation guide reviewed
- [ ] README updated
- [ ] Version number updated
- [ ] Changelog documented

## Contact & Support

For build issues or questions:
- Check this file first
- Review EXE_INSTALLATION_GUIDE.md
- Check application logs
- Contact development team

