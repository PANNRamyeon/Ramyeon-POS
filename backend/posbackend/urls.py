"""
URL configuration for posbackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse, Http404
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.views import serve as staticfiles_serve
import os
from pathlib import Path
from app.views import FrontendView

def serve_static_files(request, path, full_path=None):
    """
    Custom static file handler that serves from STATICFILES_DIRS first,
    then falls back to STATIC_ROOT. This ensures static files are served
    with correct MIME types and never caught by the catch-all route.
    
    Args:
        request: Django request object
        path: Relative path from static directory (e.g., 'frontend/assets/index.js')
        full_path: Optional full path if path needs to include subdirectories
    """
    # Use full_path if provided, otherwise use path
    file_relative_path = full_path if full_path else path
    
    # Try to find file in STATICFILES_DIRS first (for standalone mode)
    if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        for static_dir in settings.STATICFILES_DIRS:
            file_path = Path(static_dir) / file_relative_path
            if file_path.exists() and file_path.is_file():
                # Use the directory containing the file as document_root
                # and the relative path from that directory
                doc_root = str(static_dir)
                return serve(request, file_relative_path, document_root=doc_root)
    
    # Fallback to STATIC_ROOT
    if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        file_path = Path(settings.STATIC_ROOT) / file_relative_path
        if file_path.exists() and file_path.is_file():
            return serve(request, file_relative_path, document_root=str(settings.STATIC_ROOT))
    
    # If file not found, return 404
    raise Http404(f"Static file '{file_relative_path}' not found")

def serve_static_assets(request, path):
    """Wrapper to serve assets from frontend/assets/ directory"""
    return serve_static_files(request, path, full_path=f'frontend/assets/{path}')

def serve_static_root(request, path):
    """Wrapper to serve files from frontend/ root directory"""
    return serve_static_files(request, path, full_path=f'frontend/{path}')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('app.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    
    # Explicit static files handling - MUST be before catch-all route
    # Only match actual static files (with extensions), not Vue routes
    # Pattern matches: /static/frontend/assets/*.js, /static/frontend/assets/*.css, etc.
    # The path captured includes the full path from static directory: 'frontend/assets/filename.js'
    re_path(r'^static/frontend/assets/(?P<path>.*\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot|map|json|webp|avif))$', 
            serve_static_assets, 
            name='static_assets'),
    re_path(r'^static/frontend/(?P<path>favicon\.ico|index\.html)$', 
            serve_static_root, 
            name='static_root'),
    
    # Handle /static/frontend/* routes that aren't static files (like /static/frontend/online-order)
    # These should serve index.html so Vue Router can handle them
    re_path(r'^static/frontend/.*$', FrontendView.as_view(), name='frontend_static_fallback'),
    
    # Catch-all: Serve Vue.js SPA for all other routes (including /online-order, etc.)
    # This must be last to allow API routes to work
    # Exclude static and media files from catch-all
    re_path(r'^(?!api/)(?!admin/)(?!static/)(?!media/).*', FrontendView.as_view(), name='frontend'),
]

# Serve static files in development (additional fallback)
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
