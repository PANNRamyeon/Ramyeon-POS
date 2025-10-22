from django.apps import AppConfig
import os
import atexit
import logging

logger = logging.getLogger(__name__)

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    background_tasks = None

    def ready(self):
        if os.environ.get('RUN_MAIN') or not self._is_server_process():
            return
            
        try:
            logger.info("🚀 Starting offline sync system...")
            from .offline.background_task import background_tasks
            background_tasks.start_all_tasks()
            self.background_tasks = background_tasks
            atexit.register(self._cleanup)
            logger.info("✅ Offline sync system started")
        except Exception as e:
            logger.error(f"❌ Failed to start sync system: {e}")

    def _is_server_process(self):
        import sys
        return 'runserver' in sys.argv

    def _cleanup(self):
        try:
            if self.background_tasks:
                self.background_tasks.stop_all_tasks()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")