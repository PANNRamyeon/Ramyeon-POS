# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for PANN POS System

block_cipher = None

a = Analysis(
    ['start_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),  # Vue.js frontend build
        ('.env', '.'),  # Environment variables
        ('posbackend', 'posbackend'),
        ('app', 'app'),
        ('settings', 'settings'),
        ('settings/standalone.py', 'settings'),
        ('api', 'api'),
        ('notifications', 'notifications'),
        ('kpi', 'kpi'),
        ('proxy_server.py', '.'),  # Proxy server script
    ],
    hiddenimports=[
        # Core Django
        'django',
        'django.core',
        'django.core.wsgi',
        'django.core.management',
        'django.core.management.commands',
        'django.core.management.commands.runserver',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        
        # Django REST Framework
        'rest_framework',
        'rest_framework.authentication',
        'rest_framework.permissions',
        
        # Third-party packages
        'pymongo',
        'corsheaders',
        'decouple',
        'bcrypt',
        'cryptography',
        'jose',
        'passlib',
        'motor',
        'whitenoise',
        'whitenoise.middleware',
        'whitenoise.storage',
        'whitenoise.base',
        'whitenoise.compress',
        'whitenoise.responders',
        'whitenoise.media_types',
        'whitenoise.string_utils',
        
        # Project modules
        'posbackend',
        'posbackend.urls',
        'posbackend.wsgi',
        'app',
        'app.views',
        'app.urls',
        'api',
        'notifications',
        'kpi',
        'app.services.sync_service',
        'app.services.mongodb_manager',
        'app.database',
        
        # Settings
        'settings',
        'settings.base',
        'settings.local',
        'settings.production',
        'settings.standalone',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'tcl', '_tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PANN_POS_System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for now to see logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


