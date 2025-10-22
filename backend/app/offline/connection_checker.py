import time
import threading
import socket
import logging
from django.conf import settings
from database import db_service

logger = logging.getLogger(__name__)

class ConnectionChecker:
    def __init__(self):
        self.check_interval = getattr(settings, 'SYNC_INTERVAL_SECONDS', 5)
        self.is_running = False
        self.thread = None
        self.last_status = False
        
    def start(self):
        """Start the connection checker in background thread"""
        if self.is_running:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._check_loop, daemon=True)
        self.thread.start()
        logger.info("🔍 Connection checker started")
    
    def stop(self):
        """Stop the connection checker"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("🔍 Connection checker stopped")
    
    def _check_loop(self):
        """Main checking loop"""
        while self.is_running:
            try:
                previous_status = self.last_status
                current_status = self._perform_connectivity_check()
                
                # Log status changes
                if previous_status != current_status:
                    if current_status:
                        logger.info("🔗 Internet connection restored")
                    else:
                        logger.warning("🌐 Internet connection lost")
                
                self.last_status = current_status
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Connection check error: {e}")
                time.sleep(self.check_interval)
    
    def _perform_connectivity_check(self):
        """Perform actual connectivity check using multiple methods"""
        # Method 1: Check cloud database connection (primary method)
        if db_service.is_cloud_available():
            return True
        
        # Method 2: Check DNS resolution (secondary method)
        if self._check_dns_connectivity():
            return True
        
        # Method 3: Check socket connection to common ports
        if self._check_socket_connectivity():
            return True
            
        return False
    
    def _check_dns_connectivity(self):
        """Check internet connectivity via DNS resolution"""
        try:
            # Try to resolve a common domain
            socket.gethostbyname("www.google.com")
            return True
        except socket.gaierror:
            return False
    
    def _check_socket_connectivity(self):
        """Check connectivity by attempting socket connection"""
        try:
            # Try to connect to Google's DNS server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(("8.8.8.8", 53))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_current_status(self):
        """Get current connection status"""
        return self.last_status

# Global connection checker instance
connection_checker = ConnectionChecker()