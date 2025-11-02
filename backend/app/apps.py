from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    
    def ready(self):
        """Initialize database connections when Django starts"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from .database import db_manager
            db_manager.initialize()
            logger.info("🎉 App initialized with dual-mode database")
        except Exception as e:
            logger.error(f"❌ Failed to initialize app: {e}")
            raise