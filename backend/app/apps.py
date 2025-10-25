from django.apps import AppConfig

class AppMainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # Avoid circular import issues by importing inside the method
        try:
            from .offline.connectivity import Connectivity
            from .offline.sync_engine import SyncEngine

            # Start connectivity listener
            connectivity = Connectivity(interval_sec=3)
            connectivity.start()

            # Start periodic sync every 30 minutes
            syncer = SyncEngine(connectivity, interval_minutes=30)
            syncer.start()

            # Optional: store references for other parts of your app
            from django.conf import settings
            settings.CONNECTIVITY = connectivity
            settings.SYNC_ENGINE = syncer

            print("[Startup] Offline sync engine and connectivity listener initialized.")
        except Exception as e:
            print(f"[Startup Warning] Failed to start offline sync engine: {e}")
