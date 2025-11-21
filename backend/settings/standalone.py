from .production import *
from pathlib import Path
import os
import sys

# Override production settings for standalone .exe deployment
# This file is for local/hosted executable deployment

# Security settings for standalone .exe (disable HTTPS requirements)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Debug mode - read from .env, default to False for production
DEBUG = config('DEBUG', default=False, cast=bool)

# Add more hosts for local access
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '::1', 'pos.panntech']

# CORS settings for standalone .exe (allow requests from proxy domain)
CORS_ALLOWED_ORIGINS = [
    "http://pos.panntech",
    "http://pos.panntech:80",
    "http://pos.panntech:8080",
    "http://localhost:5173",  # Vite dev server (if needed)
    "http://127.0.0.1:5173",
]

# Allow credentials for CORS
CORS_ALLOW_CREDENTIALS = True

# Override production database settings for standalone
# Keep using local MongoDB
MONGODB_SETTINGS = {
    'host': 'mongodb://localhost:27017',
    'database': 'pos_system_local'
}

# Fix BASE_DIR for PyInstaller bundled .exe
# PyInstaller uses _MEIPASS for temp directory
if hasattr(sys, '_MEIPASS'):
    # Running as .exe
    BASE_DIR = Path(sys._MEIPASS)
    
    # Update template and static directories to point to bundled files
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [BASE_DIR / 'static' / 'frontend'],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]
    
    # Only add STATICFILES_DIRS if the directory exists
    static_dir = BASE_DIR / 'static'
    if static_dir.exists():
        STATICFILES_DIRS = [
            static_dir,
        ]
    else:
        STATICFILES_DIRS = []
    
    # Ensure STATIC_ROOT exists for PyInstaller
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    
    # Create staticfiles directory if it doesn't exist (for WhiteNoise)
    if not STATIC_ROOT.exists():
        try:
            STATIC_ROOT.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass  # If we can't create it, WhiteNoise will handle it gracefully
    
    # For standalone builds, use simpler WhiteNoise storage that doesn't require pre-collected files
    # WhiteNoise will serve files directly from STATICFILES_DIRS
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Additional standalone-specific settings
USE_TZ = True
TIME_ZONE = 'Asia/Manila'  # Adjust as needed

