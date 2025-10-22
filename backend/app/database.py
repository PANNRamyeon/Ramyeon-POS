from pymongo import MongoClient
from django.conf import settings
from bson import ObjectId
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        # Your existing initialization
        self.client = MongoClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_NAME]
        
        # Add offline sync capabilities
        self.local_uri = getattr(settings, 'MONGODB_LOCAL_URI', 'mongodb://localhost:27017')
        self.local_db_name = getattr(settings, 'MONGODB_LOCAL_DATABASE', 'pos_system_local')
        self.local_client = None
        self.local_db = None
        self.is_online = True
        self.current_db = self.db
        
        self._initialize_local_db()
    
    def _initialize_local_db(self):
        """Initialize local database for offline use"""
        try:
            self.local_client = MongoClient(self.local_uri, serverSelectionTimeoutMS=2000)
            self.local_db = self.local_client[self.local_db_name]
            self.local_client.admin.command('ismaster')
            logger.info("✅ Local MongoDB connection established")
        except Exception as e:
            logger.warning(f"⚠️ Local MongoDB unavailable: {e}")
    
    def _check_cloud_connection(self):
        """Check if cloud connection is available"""
        try:
            self.client.admin.command('ismaster')
            return True
        except:
            return False
    
    def get_collection(self, collection_name):
        """Enhanced get_collection with offline support"""
        # Check connectivity and switch if needed
        if not self._check_cloud_connection() and self.local_db:
            self.is_online = False
            self.current_db = self.local_db
            logger.info("🌐 Offline mode: Using local database")
        else:
            self.is_online = True
            self.current_db = self.db
        
        return self.current_db[collection_name]
    
    # Add new methods for offline sync
    def get_cloud_collection(self, collection_name):
        return self.db[collection_name]
    
    def get_local_collection(self, collection_name):
        if self.local_db:
            return self.local_db[collection_name]
        return None
    
    def is_cloud_available(self):
        return self._check_cloud_connection()
    
    # Keep your existing methods
    def convert_object_id(self, document):
        if document and '_id' in document:
            document['_id'] = str(document['_id'])
        return document
    
    def convert_object_ids(self, documents):
        return [self.convert_object_id(doc) for doc in documents]

# Maintain your existing global instance
db_service = DatabaseService()