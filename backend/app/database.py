# app/database.py
import pymongo
from django.conf import settings
from decouple import config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.cloud_client = None
        self.local_client = None
        self.current_client = None
        self.current_db = None
        
    def connect_to_cloud(self):
        """Connect to MongoDB Atlas"""
        try:
            uri = config('MONGODB_URI')
            database_name = config('MONGODB_DATABASE', default='pos_system')
            
            # Use short timeouts so we can fail over to local quickly when offline
            self.cloud_client = pymongo.MongoClient(
                uri,
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=1500,
                socketTimeoutMS=3000,
            )
            # Test connection
            self.cloud_client.admin.command('ping')
            self.current_client = self.cloud_client
            self.current_db = self.cloud_client[database_name]
            
            logger.info("Successfully connected to MongoDB Atlas")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {e}")
            return False
    
    def connect_to_local(self):
        """Fallback to local MongoDB"""
        try:
            uri = config('MONGODB_LOCAL_URI', default='mongodb://127.0.0.1:27017')
            # Prefer explicit database name if provided; default to the user's local db name
            database_name = config('MONGODB_LOCAL_DATABASE', default='pos_system_local')
            
            self.local_client = pymongo.MongoClient(
                uri,
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=1500,
                socketTimeoutMS=3000,
            )
            # Test connection
            self.local_client.admin.command('ping')
            self.current_client = self.local_client
            self.current_db = self.local_client[database_name]
            
            logger.info("Connected to local MongoDB")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to local MongoDB: {e}")
            return False
    
    def get_database(self):
        """Get current database connection with fallback"""
        force_local = config('FORCE_LOCAL_DB', default=False, cast=bool)

        if self.current_db is not None:  # ✅ Fixed: Compare with None
            # If currently cloud and ping fails → failover to local
            try:
                if not self.is_current_local():
                    self.current_client.admin.command('ping')
            except Exception:
                if self.connect_to_local():
                    return self.current_db

            # If currently local and we're allowed to use cloud, try to switch back
            if self.is_current_local() and not force_local:
                try:
                    cdb = self.get_cloud_database_optional()
                    if cdb is not None:
                        # Switch current to cloud client/db
                        self.current_client = self.cloud_client
                        self.current_db = cdb
                        return self.current_db
                except Exception:
                    pass  # stay on local

            return self.current_db
            
        # Allow forcing local DB first via env flag (temporary override)
        # Example: FORCE_LOCAL_DB=true python manage.py runserver
        if force_local:
            if self.connect_to_local():
                return self.current_db
            # If forcing local but it fails, do not silently fall back unless explicitly allowed
            raise Exception("FORCE_LOCAL_DB is set but local MongoDB connection failed")
        
        # Default behavior: Try cloud first
        if self.connect_to_cloud():
            return self.current_db
            
        # Fallback to local
        if self.connect_to_local():
            return self.current_db
            
        raise Exception("Could not connect to any database")

    # ===== Helper accessors for mirroring/sync =====
    def get_cloud_database_optional(self):
        """Return cloud DB if available; otherwise None. Does not switch current DB."""
        try:
            if not self.cloud_client:
                # Attempt connect silently
                uri = config('MONGODB_URI', default=None)
                if not uri:
                    return None
                database_name = config('MONGODB_DATABASE', default='pos_system')
                client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=1500)
                client.admin.command('ping')
                self.cloud_client = client
            db_name = config('MONGODB_DATABASE', default='pos_system')
            return self.cloud_client[db_name]
        except Exception:
            return None

    def get_local_database_optional(self):
        """Return local DB if available; otherwise None. Does not switch current DB."""
        try:
            if not self.local_client:
                uri = config('MONGODB_LOCAL_URI', default='mongodb://127.0.0.1:27017')
                database_name = config('MONGODB_LOCAL_DATABASE', default='pos_system_local')
                client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=1500)
                client.admin.command('ping')
                self.local_client = client
            db_name = config('MONGODB_LOCAL_DATABASE', default='pos_system_local')
            return self.local_client[db_name]
        except Exception:
            return None

    def is_current_local(self) -> bool:
        """True if current connection is the local client."""
        return self.current_client is not None and self.current_client is self.local_client

# Singleton instance
db_manager = DatabaseManager()