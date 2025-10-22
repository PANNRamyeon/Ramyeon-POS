import threading
import time
import logging
from datetime import datetime, timedelta
from database import db_service
from .connection_checker import connection_checker
from .sync_service import sync_service

logger = logging.getLogger(__name__)

class BackgroundTasks:
    def __init__(self):
        self.is_running = False
        self.sync_thread = None
        self.cleanup_thread = None
        
    def start_all_tasks(self):
        """Start all background tasks"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start connection checker
        connection_checker.start()
        
        # Start sync task
        self.sync_thread = threading.Thread(target=self._sync_task, daemon=True)
        self.sync_thread.start()
        
        # Start cleanup task
        self.cleanup_thread = threading.Thread(target=self._cleanup_task, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("✅ All background tasks started")
    
    def stop_all_tasks(self):
        """Stop all background tasks"""
        self.is_running = False
        connection_checker.stop()
        
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
            
        logger.info("🛑 All background tasks stopped")
    
    def _sync_task(self):
        """Background synchronization task"""
        while self.is_running:
            try:
                # Sync only if online
                if connection_checker.get_current_status():
                    sync_service.sync_all_data()
                
                # Check every 30 seconds
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Sync task error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _cleanup_task(self):
        """Background cleanup task for old data"""
        while self.is_running:
            try:
                # Run cleanup once per day
                self._cleanup_old_data()
                
                # Sleep for 1 hour
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                time.sleep(3600)
    
    def _cleanup_old_data(self):
        """Clean up old synced data"""
        try:
            # Clean up old sessions (keep 30 days)
            local_sessions = db_service.get_local_collection('sessions')
            cutoff_date = datetime.now() - timedelta(days=30)
            
            result = local_sessions.delete_many({
                'last_activity': {'$lt': cutoff_date},
                'synced': True
            })
            
            if result.deleted_count > 0:
                logger.info(f"🧹 Cleaned up {result.deleted_count} old sessions")
                
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")

# Global background tasks instance
background_tasks = BackgroundTasks()