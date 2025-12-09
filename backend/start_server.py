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
import socket
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import requests

# Add backend to path FIRST
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Explicitly import whitenoise to ensure PyInstaller includes it
# This MUST be done BEFORE Django settings are loaded
try:
    import whitenoise
    import whitenoise.middleware
    from whitenoise.middleware import WhiteNoiseMiddleware
    import whitenoise.storage
    from whitenoise.storage import CompressedManifestStaticFilesStorage
    import whitenoise.base
    import whitenoise.compress
    import whitenoise.responders
    import whitenoise.media_types
    import whitenoise.string_utils
    # Force import of all whitenoise submodules
    import pkgutil
    import whitenoise as wn_pkg
    if hasattr(wn_pkg, '__path__'):
        for importer, modname, ispkg in pkgutil.iter_modules(wn_pkg.__path__, wn_pkg.__name__ + "."):
            try:
                __import__(modname)
            except:
                pass
    # Store references to prevent garbage collection
    _whitenoise_refs = [
        whitenoise, WhiteNoiseMiddleware, CompressedManifestStaticFilesStorage
    ]
    print("✓ WhiteNoise imported successfully")
except ImportError as e:
    print(f"❌ ERROR: Could not import whitenoise: {e}")
    print("   This is required for static file serving.")
    print("   Please ensure whitenoise is installed: pip install whitenoise")
    sys.exit(1)

# Set Django settings module for standalone .exe (AFTER whitenoise import)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.standalone')

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

def check_hosts_file():
    """Check if pos.panntech is in hosts file, add if missing"""
    hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
    entry = '127.0.0.1    pos.panntech'
    
    try:
        with open(hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'pos.panntech' in content:
            return True
        
        # Try to add entry (will fail if not admin, that's okay)
        try:
            with open(hosts_path, 'a', encoding='utf-8') as f:
                f.write(f'\n{entry}\n')
            print("✓ Added pos.panntech to hosts file")
            return True
        except PermissionError:
            print("⚠ Could not automatically update hosts file (admin required)")
            print("  The app will still work, but you may need to manually add:")
            print(f"  {entry}")
            print("  to C:\\Windows\\System32\\drivers\\etc\\hosts")
            return False
    except Exception as e:
        print(f"⚠ Could not check hosts file: {e}")
        return False

def start_proxy_server():
    """Start the proxy server on port 80 (or 8080 as fallback) in a background thread"""
    proxy_port = None
    
    class ProxyHandler(BaseHTTPRequestHandler):
        """HTTP Proxy handler that forwards requests to Django"""
        
        def do_GET(self):
            self._proxy_request()
        
        def do_POST(self):
            self._proxy_request()
        
        def do_PUT(self):
            self._proxy_request()
        
        def do_DELETE(self):
            self._proxy_request()
        
        def do_PATCH(self):
            self._proxy_request()
        
        def do_OPTIONS(self):
            self._proxy_request()
        
        def _proxy_request(self):
            """Forward request to Django server"""
            try:
                # Build target URL
                target_url = f'http://127.0.0.1:8000{self.path}'
                if self.command == 'GET' and self.path == '/':
                    target_url = 'http://127.0.0.1:8000/'
                
                # Prepare headers
                headers = {}
                for header, value in self.headers.items():
                    # Skip hop-by-hop headers
                    if header.lower() not in ['connection', 'proxy-connection', 'keep-alive', 'transfer-encoding', 'host']:
                        headers[header] = value
                
                # Set Host header for Django
                headers['Host'] = '127.0.0.1:8000'
                
                # Preserve Origin header if present (important for CORS)
                # If Origin is pos.panntech, keep it so Django can validate CORS
                if 'Origin' in self.headers:
                    origin = self.headers['Origin']
                    # If origin is pos.panntech, preserve it
                    if 'pos.panntech' in origin:
                        headers['Origin'] = origin
                    else:
                        # Otherwise, set it to pos.panntech to match the proxy domain
                        headers['Origin'] = f'http://pos.panntech'
                else:
                    # Set Origin to pos.panntech if not present
                    headers['Origin'] = 'http://pos.panntech'
                
                # Get request body if present
                content_length = int(self.headers.get('Content-Length', 0))
                body = None
                if content_length > 0:
                    body = self.rfile.read(content_length)
                
                # Forward request using requests library
                try:
                    resp = requests.request(
                        method=self.command,
                        url=target_url,
                        headers=headers,
                        data=body,
                        timeout=30,
                        allow_redirects=False
                    )
                    
                    # Send response status
                    self.send_response(resp.status_code)
                    
                    # Send response headers
                    for header, value in resp.headers.items():
                        # Skip hop-by-hop headers
                        if header.lower() not in ['connection', 'transfer-encoding', 'content-encoding']:
                            self.send_header(header, value)
                    
                    self.end_headers()
                    
                    # Send response body
                    self.wfile.write(resp.content)
                    
                except requests.exceptions.RequestException as e:
                    print(f"Proxy error: {e}")
                    self.send_error(502, f"Bad Gateway: {e}")
                    
            except Exception as e:
                print(f"Proxy handler error: {e}")
                try:
                    self.send_error(500, f"Internal Server Error: {e}")
                except:
                    pass
        
        def log_message(self, format, *args):
            # Suppress proxy access logs to reduce noise
            pass
    
    def proxy_server_thread(port):
        """Run proxy server on specified port"""
        try:
            server_address = ('127.0.0.1', port)
            httpd = HTTPServer(server_address, ProxyHandler)
            httpd.serve_forever()
        except Exception as e:
            print(f"Proxy server error on port {port}: {e}")
    
    # Try port 80 first (default HTTP, no port in URL)
    for port in [80, 8080]:
        try:
            # Check if port is available
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.settimeout(1)
            result = test_sock.connect_ex(('127.0.0.1', port))
            test_sock.close()
            
            if result == 0:
                # Port is in use, assume proxy is already running
                proxy_port = port
                break
            
            # Try to bind to the port
            test_bind = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_bind.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                test_bind.bind(('127.0.0.1', port))
                test_bind.close()
                proxy_port = port
                break
            except OSError:
                test_bind.close()
                if port == 80:
                    # Port 80 failed, try 8080
                    continue
                else:
                    # Both ports failed
                    break
        except Exception:
            if port == 80:
                continue  # Try 8080
            break
    
    if proxy_port:
        # Start proxy in background thread
        proxy_thread = threading.Thread(target=proxy_server_thread, args=(proxy_port,))
        proxy_thread.daemon = True
        proxy_thread.start()
        time.sleep(1)  # Give proxy time to start
        
        if proxy_port == 80:
            print("✓ Proxy server started on port 80 (http://pos.panntech)")
        else:
            print(f"✓ Proxy server started on port {proxy_port} (http://pos.panntech:{proxy_port})")
            print("  Note: Port 80 requires admin privileges. Run as admin for cleaner URL.")
        return proxy_port
    else:
        print("⚠ Could not start proxy server (ports 80 and 8080 unavailable)")
        return None

def open_browser(proxy_port=None):
    """Wait for server to start then open browser"""
    time.sleep(5)  # Wait for server to start
    try:
        print()
        print("=" * 60)
        print("SERVER IS READY!")
        print("=" * 60)
        print()
        print("Opening browser...")
        # Use pos.panntech with appropriate port
        if proxy_port == 80:
            url = 'http://pos.panntech'
        elif proxy_port:
            url = f'http://pos.panntech:{proxy_port}'
        else:
            url = 'http://localhost:8000'
        
        webbrowser.open(url)
        print(f"✓ Browser opened at {url}")
        print()
    except Exception as e:
        print(f"Could not open browser: {e}")
        print()
        print("Please open your browser and navigate to:")
        if proxy_port == 80:
            print("  >>> http://pos.panntech <<<")
        elif proxy_port:
            print(f"  >>> http://pos.panntech:{proxy_port} <<<")
        else:
            print("  >>> http://localhost:8000 <<<")
        print()

def main():
    print("=" * 60)
    print("PANN POS System - Starting...")
    print("=" * 60)
    print()
    
    # Check and update hosts file
    print("Checking hosts file configuration...")
    hosts_ok = check_hosts_file()
    if not hosts_ok:
        print("⚠ Hosts file not updated. The app will still work at http://localhost:8000")
        print("  To use pos.panntech, manually add '127.0.0.1    pos.panntech' to hosts file")
    print()
    
    # Start proxy server
    print("Starting proxy server...")
    proxy_port = start_proxy_server()
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
            print("Local database has data - checking for mismatches...")
            
            # Smart sync: Find and sync only mismatched products and batches
            if db_manager.is_online:
                print("Running smart sync to fix any mismatches...")
                try:
                    from app.services.sync_service import smart_sync_products_startup, smart_sync_batches_startup
                    
                    # Sync products
                    product_result = smart_sync_products_startup()
                    
                    # Sync batches (critical for accurate stock levels)
                    batch_result = smart_sync_batches_startup()
                    
                    # Update product stocks after batch sync (to reflect expired batch changes)
                    try:
                        from app.services.POS.batch_service import BatchService
                        batch_service = BatchService()
                        
                        # Get all products and update their stock
                        products = list(batch_service.products_collection.find({'isDeleted': {'$ne': True}}))
                        stock_updated_count = 0
                        for product in products:
                            old_stock = product.get('total_stock', 0)
                            batch_service.update_product_total_stock(product['_id'], verbose=False)
                            updated_product = batch_service.products_collection.find_one({'_id': product['_id']})
                            new_stock = updated_product.get('total_stock', 0) if updated_product else old_stock
                            if old_stock != new_stock:
                                stock_updated_count += 1
                        
                        if stock_updated_count > 0:
                            print(f"  • Product stocks updated: {stock_updated_count} products")
                    except Exception as e:
                        print(f"  ⚠ Could not update product stocks: {e}")
                    
                    total_synced = product_result['total_synced'] + batch_result['total_synced']
                    
                    if total_synced > 0:
                        print(f"✓ Smart sync complete:")
                        if product_result['total_synced'] > 0:
                            print(f"  • Products: {product_result['total_synced']} synced")
                            print(f"    - Pushed to cloud: {product_result['pushed_to_cloud']}")
                            print(f"    - Pulled to local: {product_result['pulled_to_local']}")
                        if batch_result['total_synced'] > 0:
                            print(f"  • Batches: {batch_result['total_synced']} synced")
                            print(f"    - Pushed to cloud: {batch_result['pushed_to_cloud']}")
                            print(f"    - Pulled to local: {batch_result['pulled_to_local']}")
                            print(f"    - Merged: {batch_result['merged']}")
                        if product_result['failed'] > 0 or batch_result['failed'] > 0:
                            print(f"  ⚠ Failed: {product_result['failed'] + batch_result['failed']}")
                    else:
                        print("✓ No mismatches found - everything in sync")
                        
                except Exception as e:
                    print(f"⚠ Smart sync failed: {e}")
                    print("  System will continue, but data may be out of sync")
            else:
                print("⚠ Offline - skipping mismatch check (will sync when online)")
                
    except Exception as e:
        print(f"WARNING: Could not check/pull initial data: {e}")
    print()
    
    # Start server in a thread to allow browser opening
    print("Starting server on http://localhost:8000")
    if proxy_port == 80:
        print("Access the application at: http://pos.panntech")
    elif proxy_port:
        print(f"Access the application at: http://pos.panntech:{proxy_port}")
    else:
        print("Access the application at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    print("IMPORTANT: Use http:// (not https://) when accessing the application")
    print("=" * 60)
    print()
    
    # Open browser in separate thread (with longer delay to ensure server is ready)
    browser_thread = threading.Thread(target=open_browser, args=(proxy_port,))
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

