@echo off
echo ========================================
echo PANN POS System Build Script
echo ========================================
echo.

echo Step 1: Building Vue.js frontend...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)
echo Building frontend...
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed!
    pause
    exit /b 1
)
cd ..
echo Frontend built successfully.
echo.

echo Step 2: Creating static directory...
if not exist backend\static mkdir backend\static
echo.

echo Step 3: Setting up Python virtual environment...
if not exist backend\venv (
    echo Creating virtual environment...
    cd backend
    python -m venv venv
    cd ..
)
echo Activating virtual environment...
call backend\venv\Scripts\activate
echo.

echo Step 4: Installing Python dependencies...
cd backend
pip install -q --upgrade pip
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Python dependencies installation failed!
    pause
    exit /b 1
)
cd ..
echo Dependencies installed successfully.
echo.

echo Step 5: Collecting Django static files...
cd backend
python manage.py collectstatic --noinput --settings=settings.production
cd ..
echo Static files collected.
echo.

echo Step 6: Building executable with PyInstaller...
cd backend
pyinstaller build_exe.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)
cd ..
echo.

echo ========================================
echo Build complete!
echo ========================================
echo Executable located at: backend\dist\PANN_POS_System.exe
echo.
echo Next steps:
echo 1. Ensure MongoDB Community Edition is installed
echo 2. Run PANN_POS_System.exe
echo 3. Access application at http://localhost:8000
echo.
pause


