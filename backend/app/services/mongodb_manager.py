# app/services/mongodb_manager.py
import subprocess
import time
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self):
        self.mongod_path = self._find_mongod()
        self.data_path = Path.home() / "PANN_POS_Data" / "mongodb"
        self.log_path = self.data_path / "mongod.log"
        
    def _find_mongod(self):
        """Locate mongod.exe in common installation paths"""
        common_paths = [
            r"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe",
            r"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe",
            r"C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe",
            r"C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"Found MongoDB at: {path}")
                return path
        logger.warning("MongoDB not found in common installation paths")
        return None
    
    def is_mongodb_running(self):
        """Check if MongoDB is already running"""
        try:
            import pymongo
            client = pymongo.MongoClient(
                'mongodb://localhost:27017',
                serverSelectionTimeoutMS=2000
            )
            client.admin.command('ping')
            return True
        except Exception as e:
            logger.debug(f"MongoDB ping failed: {e}")
            return False
    
    def start_mongodb(self):
        """Start MongoDB if not running"""
        if self.is_mongodb_running():
            logger.info("MongoDB already running")
            return True
            
        if not self.mongod_path:
            logger.error("MongoDB not installed. Please install MongoDB Community Edition from https://www.mongodb.com/try/download/community")
            return False
        
        # Create data directory
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Starting MongoDB from: {self.mongod_path}")
            logger.info(f"Data directory: {self.data_path}")
            
            # Start MongoDB as subprocess
            subprocess.Popen(
                [
                    self.mongod_path,
                    '--dbpath', str(self.data_path),
                    '--logpath', str(self.log_path),
                    '--port', '27017'
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Wait for MongoDB to start (max 15 seconds)
            for i in range(15):
                time.sleep(1)
                if self.is_mongodb_running():
                    logger.info("MongoDB started successfully")
                    return True
                logger.debug(f"Waiting for MongoDB... ({i+1}/15)")
            
            logger.error("MongoDB failed to start within 15 seconds timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start MongoDB: {e}")
            return False

mongodb_manager = MongoDBManager()


