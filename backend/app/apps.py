from django.apps import AppConfig

class AppMainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # Avoid circular import issues by importing inside the method
        try:
            from .offline.connectivity import Connectivity
            from .offline.sync_engine import SyncEngine
            from .offline.local_sync import push_pending_sales

            # Start connectivity listener
            connectivity = Connectivity(interval_sec=3)
            connectivity.start()

            # Start periodic sync every 30 minutes
            syncer = SyncEngine(connectivity, interval_minutes=30)
            syncer.start()

            print("[Startup] Offline sync engine and connectivity listener initialized.")
            
            # Store as instance variables instead of modifying settings
            self.connectivity = connectivity
            self.sync_engine = syncer
            
            # Also push local pending sales immediately when we detect online
            def _on_online_push():
                try:
                    summary = push_pending_sales()
                    print(f"[Sync] Local pending pushed: {summary}")
                except Exception as e:
                    print(f"[Sync Warning] Failed to push local pending: {e}")
            connectivity.on_online(_on_online_push)
            
        except Exception as e:
            print(f"[Startup Warning] Failed to start offline sync engine: {e}")