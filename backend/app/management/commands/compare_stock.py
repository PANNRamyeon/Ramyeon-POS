# app/management/commands/compare_stock.py
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from app.database import db_manager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Compare stock between local and cloud databases with detailed mismatch reporting'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=str,
            help='Compare specific product by ID',
        )
        parser.add_argument(
            '--mismatches-only',
            action='store_true',
            help='Only show products with mismatched stock',
        )
        parser.add_argument(
            '--include-batches',
            action='store_true',
            help='Include batch-based stock calculation',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information including sync logs',
        )
    
    def handle(self, *args, **options):
        product_id = options.get('product_id')
        mismatches_only = options.get('mismatches_only', False)
        include_batches = options.get('include_batches', False)
        verbose = options.get('verbose', False)
        
        self.stdout.write(self.style.SUCCESS(
            "\n" + "="*80 + "\n"
            "STOCK COMPARISON: LOCAL vs CLOUD\n"
            "="*80 + "\n"
        ))
        
        try:
            # Ensure database is initialized
            if not db_manager._initialized:
                db_manager.initialize()
            
            local_db = db_manager.get_local_database()
            cloud_db = db_manager.get_cloud_database()
            
            if cloud_db is None:
                self.stdout.write(self.style.ERROR(
                    "❌ Cloud database is not available. Cannot compare.\n"
                ))
                return
            
            # Get batch service for batch calculations
            batch_service = None
            if include_batches:
                try:
                    from app.services.POS.batch_service import BatchService
                    batch_service = BatchService()
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  Could not load batch service: {e}\n"
                    ))
            
            # Fetch products
            if product_id:
                local_products = list(local_db.products.find({'_id': product_id}))
                cloud_products = list(cloud_db.products.find({'_id': product_id}))
            else:
                local_products = list(local_db.products.find({}))
                cloud_products = list(cloud_db.products.find({}))
            
            self.stdout.write(f"Found {len(local_products)} products in local DB\n")
            self.stdout.write(f"Found {len(cloud_products)} products in cloud DB\n\n")
            
            # Create lookup dictionaries
            local_dict = {p['_id']: p for p in local_products}
            cloud_dict = {p['_id']: p for p in cloud_products}
            
            # Get all unique product IDs
            all_product_ids = set(local_dict.keys()) | set(cloud_dict.keys())
            
            # Statistics
            stats = {
                'total': len(all_product_ids),
                'match': 0,
                'mismatch': 0,
                'local_only': 0,
                'cloud_only': 0,
                'batch_mismatch': 0
            }
            
            # Comparison results
            results = []
            
            for prod_id in sorted(all_product_ids):
                local_prod = local_dict.get(prod_id)
                cloud_prod = cloud_dict.get(prod_id)
                
                # Check if product exists in both
                if local_prod and cloud_prod:
                    local_stock = local_prod.get('total_stock', 0)
                    cloud_stock = cloud_prod.get('total_stock', 0)
                    
                    # Get batch-based stock if requested
                    batch_stock = None
                    if include_batches and batch_service:
                        try:
                            batches = list(batch_service.batches_collection.find({
                                'product_id': prod_id,
                                'status': 'active',
                                'quantity_remaining': {'$gt': 0}
                            }))
                            batch_stock = sum(b.get('quantity_remaining', 0) for b in batches)
                        except Exception as e:
                            batch_stock = f"Error: {e}"
                    
                    # Check for mismatch
                    is_mismatch = local_stock != cloud_stock
                    batch_mismatch = False
                    if batch_stock is not None and isinstance(batch_stock, int):
                        batch_mismatch = (local_stock != batch_stock) or (cloud_stock != batch_stock)
                    
                    # Get sync status
                    local_updated = local_prod.get('updated_at')
                    cloud_updated = cloud_prod.get('updated_at')
                    local_sync_logs = local_prod.get('sync_logs', [])
                    cloud_sync_logs = cloud_prod.get('sync_logs', [])
                    
                    # Get last sync time
                    last_sync = None
                    if local_sync_logs:
                        last_sync_entry = max(local_sync_logs, key=lambda x: x.get('timestamp', datetime(1970, 1, 1)))
                        last_sync = last_sync_entry.get('timestamp')
                    
                    # Determine status
                    if is_mismatch:
                        status = "MISMATCH"
                        stats['mismatch'] += 1
                    elif batch_mismatch:
                        status = "BATCH_MISMATCH"
                        stats['batch_mismatch'] += 1
                    else:
                        status = "MATCH"
                        stats['match'] += 1
                    
                    # Only show if not filtering or if there's a mismatch
                    if not mismatches_only or is_mismatch or batch_mismatch:
                        result = {
                            'product_id': prod_id,
                            'product_name': local_prod.get('product_name', 'Unknown'),
                            'local_stock': local_stock,
                            'cloud_stock': cloud_stock,
                            'batch_stock': batch_stock,
                            'status': status,
                            'local_updated': local_updated,
                            'cloud_updated': cloud_updated,
                            'last_sync': last_sync,
                            'local_sync_logs': local_sync_logs,
                            'cloud_sync_logs': cloud_sync_logs
                        }
                        results.append(result)
                
                elif local_prod:
                    stats['local_only'] += 1
                    if not mismatches_only:
                        results.append({
                            'product_id': prod_id,
                            'product_name': local_prod.get('product_name', 'Unknown'),
                            'local_stock': local_prod.get('total_stock', 0),
                            'cloud_stock': None,
                            'batch_stock': None,
                            'status': 'LOCAL_ONLY',
                            'local_updated': local_prod.get('updated_at'),
                            'cloud_updated': None,
                            'last_sync': None,
                            'local_sync_logs': local_prod.get('sync_logs', []),
                            'cloud_sync_logs': []
                        })
                
                elif cloud_prod:
                    stats['cloud_only'] += 1
                    if not mismatches_only:
                        results.append({
                            'product_id': prod_id,
                            'product_name': cloud_prod.get('product_name', 'Unknown'),
                            'local_stock': None,
                            'cloud_stock': cloud_prod.get('total_stock', 0),
                            'batch_stock': None,
                            'status': 'CLOUD_ONLY',
                            'local_updated': None,
                            'cloud_updated': cloud_prod.get('updated_at'),
                            'last_sync': None,
                            'local_sync_logs': [],
                            'cloud_sync_logs': cloud_prod.get('sync_logs', [])
                        })
            
            # Display results
            if results:
                self.stdout.write("\n" + "-"*80 + "\n")
                self.stdout.write(f"{'Product ID':<20} {'Name':<30} {'Local':<10} {'Cloud':<10}", ending='')
                if include_batches:
                    self.stdout.write(f" {'Batches':<10}", ending='')
                self.stdout.write(f" {'Status':<15}\n")
                self.stdout.write("-"*80 + "\n")
                
                for result in results:
                    prod_id = str(result['product_id'])[:18]
                    name = result['product_name'][:28]
                    local = str(result['local_stock']) if result['local_stock'] is not None else "N/A"
                    cloud = str(result['cloud_stock']) if result['cloud_stock'] is not None else "N/A"
                    batch = str(result['batch_stock']) if result['batch_stock'] is not None else "N/A"
                    status = result['status']
                    
                    # Color coding
                    if status == "MISMATCH":
                        style = self.style.ERROR
                    elif status == "BATCH_MISMATCH":
                        style = self.style.WARNING
                    elif status in ["LOCAL_ONLY", "CLOUD_ONLY"]:
                        style = self.style.WARNING
                    else:
                        style = self.style.SUCCESS
                    
                    self.stdout.write(style(
                        f"{prod_id:<20} {name:<30} {local:<10} {cloud:<10}"
                    ), ending='')
                    if include_batches:
                        self.stdout.write(f" {batch:<10}", ending='')
                    self.stdout.write(f" {status:<15}\n")
                    
                    # Verbose details
                    if verbose:
                        self.stdout.write(f"  └─ Local updated: {result['local_updated']}\n")
                        self.stdout.write(f"  └─ Cloud updated: {result['cloud_updated']}\n")
                        if result['last_sync']:
                            self.stdout.write(f"  └─ Last synced: {result['last_sync']}\n")
                        if result['local_sync_logs']:
                            self.stdout.write(f"  └─ Local sync logs: {len(result['local_sync_logs'])} entries\n")
                        if result['cloud_sync_logs']:
                            self.stdout.write(f"  └─ Cloud sync logs: {len(result['cloud_sync_logs'])} entries\n")
                        self.stdout.write("\n")
            else:
                self.stdout.write("No products to display.\n")
            
            # Summary
            self.stdout.write("\n" + "="*80 + "\n")
            self.stdout.write(self.style.SUCCESS("SUMMARY"))
            self.stdout.write("="*80 + "\n")
            self.stdout.write(f"Total Products: {stats['total']}\n")
            self.stdout.write(self.style.SUCCESS(f"✓ Matches: {stats['match']}\n"))
            self.stdout.write(self.style.ERROR(f"✗ Stock Mismatches: {stats['mismatch']}\n"))
            if include_batches:
                self.stdout.write(self.style.WARNING(f"⚠️  Batch Mismatches: {stats['batch_mismatch']}\n"))
            self.stdout.write(self.style.WARNING(f"⚠️  Local Only: {stats['local_only']}\n"))
            self.stdout.write(self.style.WARNING(f"⚠️  Cloud Only: {stats['cloud_only']}\n"))
            self.stdout.write("="*80 + "\n\n")
            
            # Recommendations
            if stats['mismatch'] > 0 or stats['batch_mismatch'] > 0:
                self.stdout.write(self.style.WARNING("RECOMMENDATIONS:\n"))
                if stats['mismatch'] > 0:
                    self.stdout.write("  • Run sync_product_stock to sync product total_stock with batches\n")
                    self.stdout.write("  • Check if products are being updated but not synced (updated_at issue)\n")
                if stats['batch_mismatch'] > 0:
                    self.stdout.write("  • Product total_stock doesn't match batch sum - run sync_product_stock\n")
                self.stdout.write("  • Use simulate_sync to test sync process\n")
                self.stdout.write("\n")
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\nComparison interrupted by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFatal error: {e}"))
            logger.error(f"Compare stock fatal error: {e}", exc_info=True)
            raise

