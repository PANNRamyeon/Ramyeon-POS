from django.apps import AppConfig
import threading


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    
    def ready(self):
        """Initialize database connections when Django starts"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Start MongoDB if not running (for offline mode)
            from .services.mongodb_manager import mongodb_manager
            if not mongodb_manager.start_mongodb():
                logger.warning("⚠️ MongoDB auto-start failed. The app may not work in offline mode.")
            
            from .database import db_manager
            db_manager.initialize()
            
            # Start background sync worker in a separate thread
            self._start_background_sync_worker()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize app: {e}")
            raise
    
    def _start_background_sync_worker(self):
        """Start background sync worker as daemon thread"""
        import logging
        logger = logging.getLogger(__name__)
        
        def sync_worker():
            """Background worker that calls sync every 30 seconds"""
            import time
            from .services.sync_service import sync_service
            
            while True:
                try:
                    time.sleep(30)  # Wait 30 seconds
                    sync_service.sync_background()
                except Exception as e:
                    logger.error(f"❌ Sync worker error: {e}")
                    time.sleep(30)  # Wait before retrying
        
        # Start as daemon thread (dies with main process)
        worker_thread = threading.Thread(target=sync_worker, daemon=True, name="BackgroundSyncWorker")
        worker_thread.start()