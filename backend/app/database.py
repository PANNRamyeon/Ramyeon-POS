# app/database.py
import pymongo
from django.conf import settings
from decouple import config
import logging
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.cloud_client = None
        self.local_client = None
        self.cloud_db = None
        self.local_db = None
        self.is_online = False
        self.last_connectivity_check = None
        self.connectivity_check_interval = 10  # seconds
        self._lock = threading.Lock()
        self._initialized = False
        
    def initialize(self):
        """Initialize dual-mode connections (call once on app startup)"""
        with self._lock:
            if self._initialized:
                return
                
            # Connect to local (required)
            local_success = self.connect_to_local()
            if not local_success:
                raise Exception("Failed to connect to local MongoDB - this is required for offline mode")
            
            # Try to connect to cloud (optional)
            cloud_success = self.connect_to_cloud()
            if cloud_success:
                self.is_online = True
            else:
                self.is_online = False
                
            self._initialized = True
            self.last_connectivity_check = datetime.utcnow()
        
    def connect_to_cloud(self):
        """Connect to MongoDB Atlas"""
        try:
            uri = config('MONGODB_URI')
            database_name = config('MONGODB_DATABASE', default='pos_system')
            
            # Short timeout for connectivity check
            self.cloud_client = pymongo.MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            
            # Test connection
            self.cloud_client.admin.command('ping')
            self.cloud_db = self.cloud_client[database_name]
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB Atlas: {e}")
            self.cloud_client = None
            self.cloud_db = None
            return False
    
    def connect_to_local(self):
        """Connect to local MongoDB"""
        try:
            uri = config('MONGODB_LOCAL_URI', default='mongodb://localhost:27017')
            database_name = config('MONGODB_LOCAL_DATABASE', default='pos_system_local')
            
            self.local_client = pymongo.MongoClient(
                uri,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            self.local_client.admin.command('ping')
            self.local_db = self.local_client[database_name]
            
            logger.info("✅ Connected to local MongoDB")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to local MongoDB: {e}")
            self.local_client = None
            self.local_db = None
            return False
    
    def get_database(self):
        """Get local database (primary for all operations)"""
        if not self._initialized:
            self.initialize()
            
        if self.local_db is None:
            raise Exception("Local database not connected")
            
        return self.local_db
    
    def get_local_database(self):
        """Explicitly get local database"""
        if not self._initialized:
            self.initialize()
            
        return self.local_db
    
    def get_cloud_database(self):
        """Get cloud database if online, None otherwise"""
        if not self._initialized:
            self.initialize()
            
        # Check if we need to verify connectivity
        self._check_connectivity_if_needed()
        
        return self.cloud_db if self.is_online else None
    
    def _check_connectivity_if_needed(self):
        """Check cloud connectivity if interval has passed"""
        now = datetime.utcnow()
        
        if self.last_connectivity_check is None:
            should_check = True
        else:
            elapsed = (now - self.last_connectivity_check).total_seconds()
            should_check = elapsed >= self.connectivity_check_interval
        
        if should_check:
            with self._lock:
                self.check_connectivity()
                self.last_connectivity_check = now
    
    def check_connectivity(self):
        """Check if cloud database is reachable"""
        try:
            if self.cloud_client is None:
                # Try to reconnect
                self.connect_to_cloud()
                
            if self.cloud_client is not None:
                # Ping to verify connection
                self.cloud_client.admin.command('ping', maxTimeMS=3000)
                
                # Restore cloud_db if it was None
                if self.cloud_db is None:
                    database_name = config('MONGODB_DATABASE', default='pos_system')
                    self.cloud_db = self.cloud_client[database_name]
                
                self.is_online = True
                return True
        except Exception as e:
            if self.is_online:
                pass  # Silent transition to offline
            
            self.is_online = False
            self.cloud_db = None
            return False
    
    def force_offline_mode(self):
        """Force offline mode (for testing)"""
        logger.warning("⚠️ Forcing offline mode")
        self.is_online = False
        self.cloud_db = None
    
    def get_connection_status(self):
        """Get current connection status"""
        return {
            'is_online': self.is_online,
            'local_connected': self.local_db is not None,
            'cloud_connected': self.cloud_db is not None,
            'last_check': self.last_connectivity_check.isoformat() if self.last_connectivity_check else None
        }

# Singleton instance
db_manager = DatabaseManager()