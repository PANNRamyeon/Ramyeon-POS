# app/management/commands/simulate_sync.py
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from app.database import db_manager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Simulate sync process to see what would be synced (dry-run mode)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would sync without actually syncing (default: True)',
        )
        parser.add_argument(
            '--product-id',
            type=str,
            help='Test sync for specific product ID',
        )
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='Force sync all products regardless of updated_at timestamp',
        )
        parser.add_argument(
            '--check-queue',
            action='store_true',
            help='Show items in sync queue',
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually execute the sync (not just simulate)',
        )
    
    def handle(self, *args, **options):
        dry_run = not options.get('execute', False)  # Default to dry-run unless --execute
        product_id = options.get('product_id')
        force_all = options.get('force_all', False)
        check_queue = options.get('check_queue', False)
        
        self.stdout.write(self.style.SUCCESS(
            "\n" + "="*80 + "\n"
            "SYNC SIMULATION" + (" (DRY-RUN)" if dry_run else " (EXECUTING)") + "\n"
            "="*80 + "\n"
        ))
        
        try:
            # Ensure database is initialized
            if not db_manager._initialized:
                db_manager.initialize()
            
            local_db = db_manager.get_local_database()
            cloud_db = db_manager.get_cloud_database()
            
            # Check connectivity
            is_online = db_manager.is_online
            self.stdout.write(f"Connection Status: {'🟢 ONLINE' if is_online else '🔴 OFFLINE'}\n")
            
            if not is_online and not check_queue:
                self.stdout.write(self.style.WARNING(
                    "⚠️  Offline mode - only sync queue will be checked\n"
                ))
            
            # Check sync queue
            if check_queue or not is_online:
                self.stdout.write("\n" + "-"*80 + "\n")
                self.stdout.write("SYNC QUEUE STATUS\n")
                self.stdout.write("-"*80 + "\n")
                
                queue_items = list(local_db.sync_queue.find({'status': 'pending'}))
                failed_items = list(local_db.sync_queue.find({'status': 'failed'}))
                
                self.stdout.write(f"Pending items: {len(queue_items)}\n")
                self.stdout.write(f"Failed items: {len(failed_items)}\n")
                
                if queue_items:
                    self.stdout.write("\nPending Queue Items:\n")
                    for item in queue_items[:10]:  # Show first 10
                        collection = item.get('collection', 'unknown')
                        doc_id = item.get('document', {}).get('_id', 'unknown')
                        created = item.get('created_at', 'unknown')
                        self.stdout.write(f"  • {collection}:{doc_id} (queued: {created})\n")
                    if len(queue_items) > 10:
                        self.stdout.write(f"  ... and {len(queue_items) - 10} more\n")
                
                if failed_items:
                    self.stdout.write("\nFailed Queue Items:\n")
                    for item in failed_items[:10]:  # Show first 10
                        collection = item.get('collection', 'unknown')
                        doc_id = item.get('document', {}).get('_id', 'unknown')
                        error = item.get('error', 'unknown error')
                        self.stdout.write(self.style.ERROR(
                            f"  • {collection}:{doc_id} - {error}\n"
                        ))
                    if len(failed_items) > 10:
                        self.stdout.write(f"  ... and {len(failed_items) - 10} more\n")
            
            if not is_online and not check_queue:
                self.stdout.write("\n⚠️  Cannot simulate sync - offline. Use --check-queue to see queued items.\n")
                return
            
            # Simulate product sync
            self.stdout.write("\n" + "-"*80 + "\n")
            self.stdout.write("PRODUCT SYNC SIMULATION\n")
            self.stdout.write("-"*80 + "\n")
            
            # Get sync window
            if force_all:
                sync_window = datetime(1970, 1, 1)  # Very old date to include all
                self.stdout.write("Mode: FORCE ALL (ignoring updated_at)\n")
            else:
                sync_window = datetime.utcnow() - timedelta(minutes=5)
                self.stdout.write(f"Mode: INCREMENTAL (last 5 minutes)\n")
                self.stdout.write(f"Sync window: {sync_window} to {datetime.utcnow()}\n")
            
            self.stdout.write("\n")
            
            # Get products to sync
            if product_id:
                query = {'_id': product_id}
                self.stdout.write(f"Testing specific product: {product_id}\n\n")
            else:
                query = {}
            
            # Get all local products
            all_local_products = list(local_db.products.find(query))
            
            # Filter by sync window
            products_to_sync = []
            products_skipped = []
            
            for product in all_local_products:
                updated_at = product.get('updated_at')
                
                # Check if should be synced
                if force_all:
                    should_sync = True
                    reason = "force-all flag"
                elif updated_at is None:
                    should_sync = True
                    reason = "no updated_at field"
                elif isinstance(updated_at, datetime):
                    should_sync = updated_at >= sync_window
                    reason = "updated_at within window" if should_sync else f"updated_at too old ({updated_at})"
                elif isinstance(updated_at, str):
                    try:
                        updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        should_sync = updated_dt >= sync_window
                        reason = "updated_at within window" if should_sync else f"updated_at too old ({updated_at})"
                    except:
                        should_sync = True
                        reason = "could not parse updated_at"
                else:
                    should_sync = True
                    reason = "unknown updated_at format"
                
                if should_sync:
                    products_to_sync.append((product, reason))
                else:
                    products_skipped.append((product, reason))
            
            # Display results
            self.stdout.write(f"Total products found: {len(all_local_products)}\n")
            self.stdout.write(self.style.SUCCESS(f"✓ Would sync: {len(products_to_sync)}\n"))
            self.stdout.write(self.style.WARNING(f"⊘ Would skip: {len(products_skipped)}\n\n"))
            
            # Show products that would sync
            if products_to_sync:
                self.stdout.write("Products that WOULD BE SYNCED:\n")
                self.stdout.write("-"*80 + "\n")
                self.stdout.write(f"{'Product ID':<20} {'Name':<30} {'Stock':<10} {'Updated':<20} {'Reason':<20}\n")
                self.stdout.write("-"*80 + "\n")
                
                for product, reason in products_to_sync[:50]:  # Show first 50
                    prod_id = str(product.get('_id', ''))[:18]
                    name = product.get('product_name', 'Unknown')[:28]
                    stock = product.get('total_stock', 0)
                    updated = product.get('updated_at', 'N/A')
                    if isinstance(updated, datetime):
                        updated = updated.strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.stdout.write(
                        f"{prod_id:<20} {name:<30} {stock:<10} {str(updated):<20} {reason[:18]:<20}\n"
                    )
                
                if len(products_to_sync) > 50:
                    self.stdout.write(f"... and {len(products_to_sync) - 50} more\n")
                
                # Execute sync if requested
                if not dry_run:
                    self.stdout.write("\n" + "="*80 + "\n")
                    self.stdout.write("EXECUTING SYNC...\n")
                    self.stdout.write("="*80 + "\n")
                    
                    from app.services.sync_service import sync_service
                    
                    synced_count = 0
                    failed_count = 0
                    
                    for product, reason in products_to_sync:
                        try:
                            prod_id = product.get('_id')
                            
                            if cloud_db:
                                # Replace cloud product with local version
                                result = cloud_db.products.replace_one(
                                    {'_id': prod_id},
                                    product,
                                    upsert=True
                                )
                                
                                # Add sync log
                                sync_service.add_sync_log_to_document(
                                    'products', prod_id, 'synced', 'cloud',
                                    {'simulated': False, 'reason': reason}
                                )
                                
                                synced_count += 1
                                self.stdout.write(self.style.SUCCESS(
                                    f"✓ Synced: {product.get('product_name', prod_id)}\n"
                                ))
                            else:
                                failed_count += 1
                                
                        except Exception as e:
                            failed_count += 1
                            self.stdout.write(self.style.ERROR(
                                f"✗ Failed: {product.get('product_name', prod_id)} - {e}\n"
                            ))
                    
                    self.stdout.write("\n" + "="*80 + "\n")
                    self.stdout.write("SYNC RESULTS\n")
                    self.stdout.write("="*80 + "\n")
                    self.stdout.write(self.style.SUCCESS(f"✓ Synced: {synced_count}\n"))
                    self.stdout.write(self.style.ERROR(f"✗ Failed: {failed_count}\n"))
                    self.stdout.write("="*80 + "\n\n")
                else:
                    self.stdout.write("\n" + self.style.WARNING(
                        "DRY-RUN MODE: No changes were made.\n"
                        "Use --execute to actually perform the sync.\n"
                    ))
            
            # Show products that would be skipped
            if products_skipped and not product_id:
                self.stdout.write("\n" + "-"*80 + "\n")
                self.stdout.write("Products that WOULD BE SKIPPED (outside sync window):\n")
                self.stdout.write("-"*80 + "\n")
                self.stdout.write(f"{'Product ID':<20} {'Name':<30} {'Updated':<30} {'Reason':<20}\n")
                self.stdout.write("-"*80 + "\n")
                
                for product, reason in products_skipped[:20]:  # Show first 20
                    prod_id = str(product.get('_id', ''))[:18]
                    name = product.get('product_name', 'Unknown')[:28]
                    updated = product.get('updated_at', 'N/A')
                    if isinstance(updated, datetime):
                        updated = updated.strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.stdout.write(
                        f"{prod_id:<20} {name:<30} {str(updated):<30} {reason[:18]:<20}\n"
                    )
                
                if len(products_skipped) > 20:
                    self.stdout.write(f"... and {len(products_skipped) - 20} more\n")
                
                self.stdout.write("\n" + self.style.WARNING(
                    f"💡 Tip: Use --force-all to sync all {len(products_skipped)} skipped products\n"
                ))
            
            # Summary
            self.stdout.write("\n" + "="*80 + "\n")
            self.stdout.write("SIMULATION SUMMARY\n")
            self.stdout.write("="*80 + "\n")
            self.stdout.write(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}\n")
            self.stdout.write(f"Total Products: {len(all_local_products)}\n")
            self.stdout.write(self.style.SUCCESS(f"Would Sync: {len(products_to_sync)}\n"))
            self.stdout.write(self.style.WARNING(f"Would Skip: {len(products_skipped)}\n"))
            self.stdout.write("="*80 + "\n\n")
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\nSimulation interrupted by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFatal error: {e}"))
            logger.error(f"Simulate sync fatal error: {e}", exc_info=True)
            raise

