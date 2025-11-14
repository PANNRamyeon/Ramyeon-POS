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
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '::1']

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
    
    STATICFILES_DIRS = [
        BASE_DIR / 'static',
    ]

# Additional standalone-specific settings
USE_TZ = True
TIME_ZONE = 'Asia/Manila'  # Adjust as needed

