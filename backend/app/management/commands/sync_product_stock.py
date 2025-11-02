# app/management/commands/sync_product_stock.py
import logging
from django.core.management.base import BaseCommand
from app.database import db_manager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync all products total_stock with batch quantity_remaining sums'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "\n" + "="*60 + "\n"
            "SYNCING PRODUCT STOCK WITH BATCHES\n"
            "="*60 + "\n"
        ))
        
        try:
            from app.services.POS.batch_service import BatchService
            
            # Ensure database is initialized
            if not db_manager._initialized:
                db_manager.initialize()
            
            # Get batch service
            batch_service = BatchService()
            
            # Get all products
            products_collection = db_manager.get_database().products
            products = list(products_collection.find({}))
            
            self.stdout.write(f"Found {len(products)} products to sync...\n")
            
            synced_count = 0
            failed_count = 0
            
            for product in products:
                product_id = product.get('_id')
                product_name = product.get('product_name', 'Unknown')
                
                try:
                    # Sync using batch service
                    batch_service.update_product_total_stock(product_id)
                    synced_count += 1
                    self.stdout.write(f"  OK {product_name} ({product_id})")
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(
                        f"  FAIL {product_name} ({product_id}): {e}"
                    ))
            
            # Display summary
            self.stdout.write(self.style.SUCCESS("\n" + "="*60))
            self.stdout.write(self.style.SUCCESS("SYNC SUMMARY"))
            self.stdout.write(self.style.SUCCESS("="*60))
            self.stdout.write(self.style.SUCCESS(f"Total Products: {len(products)}"))
            self.stdout.write(self.style.SUCCESS(f"Synced: {synced_count}"))
            self.stdout.write(self.style.SUCCESS(f"Failed: {failed_count}"))
            self.stdout.write(self.style.SUCCESS("="*60 + "\n"))
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\nSync interrupted by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFatal error: {e}"))
            logger.error(f"Sync fatal error: {e}")
            raise

