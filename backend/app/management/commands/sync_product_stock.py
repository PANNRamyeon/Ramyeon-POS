# app/management/commands/sync_product_stock.py
import logging
from django.core.management.base import BaseCommand
from app.database import db_manager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync all products total_stock with batch quantity_remaining sums'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed batch information for each product',
        )
        parser.add_argument(
            '--mismatches-only',
            action='store_true',
            help='Only show products with mismatched stock',
        )
    
    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        mismatches_only = options.get('mismatches_only', False)
        
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
            mismatch_count = 0
            
            for product in products:
                product_id = product.get('_id')
                product_name = product.get('product_name', 'Unknown')
                old_stock = product.get('total_stock', 0)
                
                try:
                    # Get batches to calculate new stock
                    batches = list(batch_service.batches_collection.find({
                        'product_id': product_id
                    }))
                    
                    total_remaining = sum(batch.get('quantity_remaining', 0) for batch in batches)
                    
                    # Check for mismatch
                    is_mismatch = old_stock != total_remaining
                    
                    if is_mismatch:
                        mismatch_count += 1
                    
                    # Only process if verbose or showing mismatches or not filtering
                    should_show = verbose or (mismatches_only and is_mismatch) or not mismatches_only
                    
                    if should_show or is_mismatch:
                        # Sync using batch service
                        batch_service.update_product_total_stock(product_id, verbose=verbose and should_show)
                        
                        if not verbose:
                            if is_mismatch:
                                self.stdout.write(self.style.WARNING(
                                    f"  🔧 FIXED {product_name} ({product_id}): {old_stock} → {total_remaining}"
                                ))
                            elif not mismatches_only:
                                self.stdout.write(f"  ✓ {product_name} ({product_id})")
                    else:
                        # Silent sync without output
                        batch_service.update_product_total_stock(product_id, verbose=False)
                    
                    synced_count += 1
                    
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
            self.stdout.write(self.style.WARNING(f"Fixed Mismatches: {mismatch_count}"))
            self.stdout.write(self.style.ERROR(f"Failed: {failed_count}"))
            self.stdout.write(self.style.SUCCESS("="*60 + "\n"))
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\nSync interrupted by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFatal error: {e}"))
            logger.error(f"Sync fatal error: {e}")
            raise

