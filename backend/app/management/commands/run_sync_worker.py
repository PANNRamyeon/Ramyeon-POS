# app/management/commands/run_sync_worker.py
import logging
import time
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run background sync worker for offline mode (30 second intervals)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Sync interval in seconds (default: 30)'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        
        self.stdout.write(self.style.SUCCESS(
            f"🚀 Starting background sync worker (interval: {interval}s)\n"
        ))
        
        try:
            from app.services.sync_service import sync_service
            from app.database import db_manager
            
            # Ensure database is initialized
            if not db_manager._initialized:
                db_manager.initialize()
            
            iteration = 0
            
            while True:
                iteration += 1
                self.stdout.write(
                    self.style.WARNING(f"\n[Iteration {iteration}] Running background sync...")
                )
                
                try:
                    # Run background sync
                    sync_service.sync_background()
                    
                    # Get sync status
                    status = sync_service.get_sync_status()
                    
                    # Display status
                    if status['is_online']:
                        if status['pending_syncs'] > 0:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  Status: Online | Pending: {status['pending_syncs']}"
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS("  Status: Online | All synced ✅")
                            )
                    else:
                        self.stdout.write(
                            self.style.ERROR("  Status: Offline ⚠️")
                        )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Sync error: {e}")
                    )
                    logger.error(f"Background sync error: {e}")
                
                # Wait before next iteration
                self.stdout.write(f"  Waiting {interval}s before next sync...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\n\n🛑 Sync worker stopped by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Fatal error: {e}"))
            logger.error(f"Sync worker fatal error: {e}")
            raise

