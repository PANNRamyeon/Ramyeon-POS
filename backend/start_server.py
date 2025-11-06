"""
Startup script for PANN POS System executable
Handles server startup, MongoDB check, and graceful shutdown
"""

import os
import sys
import subprocess
import threading
import webbrowser
import time
from pathlib import Path

# Set Django settings module for standalone .exe
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.standalone')

# Add backend to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

def check_mongodb():
    """Check if MongoDB is running"""
    try:
        import pymongo
        client = pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)
        client.server_info()  # Will raise exception if not connected
        return True
    except Exception:
        return False

def run_migrations():
    """Run Django migrations"""
    try:
        from django.core.management import execute_from_command_line
        
        # Change to backend directory
        os.chdir(BASE_DIR)
        
        # Run migrations
        sys.argv = ['manage.py', 'migrate', '--noinput']
        execute_from_command_line(sys.argv)
        
        return True
    except Exception as e:
        print(f"WARNING: Could not run migrations: {e}")
        return False

def start_server():
    """Start Django development server"""
    try:
        # Change to backend directory
        os.chdir(BASE_DIR)
        
        from django.core.management import execute_from_command_line
        
        # Start server with proper arguments
        sys.argv = ['manage.py', 'runserver', '0.0.0.0:8000', '--noreload']
        execute_from_command_line(sys.argv)
    except Exception as e:
        import traceback
        print(f"Error starting server: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

def open_browser():
    """Wait for server to start then open browser"""
    time.sleep(5)  # Wait for server to start
    try:
        print()
        print("=" * 60)
        print("SERVER IS READY!")
        print("=" * 60)
        print()
        print("Opening browser...")
        webbrowser.open('http://localhost:8000')
        print()
    except Exception as e:
        print(f"Could not open browser: {e}")
        print()
        print("Please open your browser and navigate to:")
        print("  >>> http://localhost:8000 <<<")
        print()

def main():
    print("=" * 60)
    print("PANN POS System - Starting...")
    print("=" * 60)
    print()
    
    # Check MongoDB
    print("Checking MongoDB...")
    if check_mongodb():
        print("MongoDB: Connected")
    else:
        print("WARNING: MongoDB not detected!")
        print("Please ensure MongoDB is installed and running.")
        print("Download: https://www.mongodb.com/try/download/community")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    print()
    
    # Run migrations before starting server
    print("Checking for unapplied migrations...")
    if run_migrations():
        print("Migrations: Up to date")
    else:
        print("Migrations: Warning - some migrations may have failed")
    print()
    
    # Check if local database is empty and pull initial data from cloud
    print("Checking if initial data pull is needed...")
    try:
        from app.database import db_manager
        from app.services.sync_service import sync_service
        
        # Initialize database connection
        if not db_manager._initialized:
            db_manager.initialize()
        
        # Check if local database is empty
        if sync_service.is_local_database_empty():
            print("Local database appears empty - pulling initial data from cloud...")
            if db_manager.is_online:
                result = sync_service.pull_all_from_cloud()
                if result.get('pulled', 0) > 0:
                    print(f"✓ Initial data pull complete: {result['pulled']} documents pulled")
                else:
                    print("⚠ Initial data pull: No data pulled (cloud may be empty or offline)")
            else:
                print("⚠ Cannot pull initial data - offline (will sync when online)")
        else:
            print("Local database has data - skipping initial pull")
    except Exception as e:
        print(f"WARNING: Could not check/pull initial data: {e}")
    print()
    
    # Start server in a thread to allow browser opening
    print("Starting server on http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    print("IMPORTANT: Use http:// (not https://) when accessing the application")
    print("=" * 60)
    print()
    
    # Open browser in separate thread (with longer delay to ensure server is ready)
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start server (this will block)
    try:
        start_server()
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("Server stopped. Goodbye!")
        print("=" * 60)

if __name__ == '__main__':
    main()

