# app/management/commands/backfill_sales.py
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Backfill unsynced sales from local to cloud database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--collection',
            type=str,
            default='sales',
            help='Collection name to backfill (default: sales)'
        )
    
    def handle(self, *args, **options):
        collection_name = options['collection']
        
        self.stdout.write(self.style.SUCCESS(
            f"\nStarting backfill for {collection_name} collection\n"
        ))
        
        try:
            from app.services.sync_service import sync_service
            from app.database import db_manager
            
            # Ensure database is initialized
            if not db_manager._initialized:
                db_manager.initialize()
            
            # Run backfill
            results = sync_service.backfill_collection(collection_name)
            
            # Display summary
            self.stdout.write(self.style.SUCCESS("\n" + "="*60))
            self.stdout.write(self.style.SUCCESS("BACKFILL SUMMARY"))
            self.stdout.write(self.style.SUCCESS("="*60))
            self.stdout.write(self.style.SUCCESS(f"Collection: {collection_name}"))
            self.stdout.write(self.style.SUCCESS(f"Total Documents: {results['total']}"))
            self.stdout.write(self.style.SUCCESS(f"Synced: {results['synced']}"))
            self.stdout.write(self.style.SUCCESS(f"Skipped: {results['skipped']}"))
            self.stdout.write(self.style.SUCCESS(f"Failed: {results['failed']}"))
            self.stdout.write(self.style.SUCCESS("="*60 + "\n"))
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\nBackfill interrupted by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFatal error: {e}"))
            logger.error(f"Backfill fatal error: {e}")
            raise

