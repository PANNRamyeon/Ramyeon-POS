# app/management/commands/smart_sync_products.py
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from app.database import db_manager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Smart sync: Only sync products with mismatches using timestamp-based conflict resolution'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=True,
            help='Show what would sync without actually syncing (default: True)',
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually execute the sync (not just simulate)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information for each product',
        )
    
    def handle(self, *args, **options):
        dry_run = not options.get('execute', False)  # Default to dry-run unless --execute
        verbose = options.get('verbose', False)
        
        self.stdout.write(self.style.SUCCESS(
            "\n" + "="*80 + "\n"
            "SMART PRODUCT SYNC" + (" (DRY-RUN)" if dry_run else " (EXECUTING)") + "\n"
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
                    "❌ Cloud database is not available. Cannot sync.\n"
                ))
                return
            
            self.stdout.write(f"Connection Status: {'🟢 ONLINE' if db_manager.is_online else '🔴 OFFLINE'}\n\n")
            
            # Phase 1: Find mismatches
            self.stdout.write("Phase 1: Finding product mismatches...\n")
            self.stdout.write("-"*80 + "\n")
            
            mismatches = self._find_product_mismatches(local_db, cloud_db)
            
            total_mismatches = (
                len(mismatches['stock_mismatches']) +
                len(mismatches['cloud_only']) +
                len(mismatches['local_only'])
            )
            
            self.stdout.write(f"Found {len(mismatches['stock_mismatches'])} stock mismatches\n")
            self.stdout.write(f"Found {len(mismatches['cloud_only'])} cloud-only products\n")
            self.stdout.write(f"Found {len(mismatches['local_only'])} local-only products\n")
            self.stdout.write(f"Total products to sync: {total_mismatches}\n\n")
            
            if total_mismatches == 0:
                self.stdout.write(self.style.SUCCESS("✅ No mismatches found! Everything is in sync.\n"))
                return
            
            # Phase 2: Show what would be synced
            self.stdout.write("Phase 2: Analyzing sync actions...\n")
            self.stdout.write("-"*80 + "\n")
            
            sync_plan = self._create_sync_plan(mismatches, local_db, cloud_db, verbose)
            
            # Display sync plan
            self._display_sync_plan(sync_plan, verbose)
            
            # Phase 3: Execute sync (if not dry-run)
            if not dry_run:
                self.stdout.write("\n" + "="*80 + "\n")
                self.stdout.write("Phase 3: Executing sync...\n")
                self.stdout.write("="*80 + "\n")
                
                results = self._execute_sync(sync_plan, local_db, cloud_db)
                
                # Display results
                self._display_sync_results(results)
            else:
                self.stdout.write("\n" + self.style.WARNING(
                    "DRY-RUN MODE: No changes were made.\n"
                    "Use --execute to actually perform the sync.\n"
                ))
            
            # Summary
            self.stdout.write("\n" + "="*80 + "\n")
            self.stdout.write("SUMMARY\n")
            self.stdout.write("="*80 + "\n")
            self.stdout.write(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTED'}\n")
            self.stdout.write(f"Stock Mismatches: {len(mismatches['stock_mismatches'])}\n")
            self.stdout.write(f"Cloud-Only Products: {len(mismatches['cloud_only'])}\n")
            self.stdout.write(f"Local-Only Products: {len(mismatches['local_only'])}\n")
            self.stdout.write(f"Total Products to Sync: {total_mismatches}\n")
            if not dry_run:
                self.stdout.write(f"Successfully Synced: {results.get('synced', 0)}\n")
                self.stdout.write(f"Failed: {results.get('failed', 0)}\n")
            self.stdout.write("="*80 + "\n\n")
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\nSync interrupted by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFatal error: {e}"))
            logger.error(f"Smart sync fatal error: {e}", exc_info=True)
            raise
    
    def _find_product_mismatches(self, local_db, cloud_db):
        """Find all product mismatches between local and cloud"""
        local_products = list(local_db.products.find({}))
        cloud_products = list(cloud_db.products.find({}))
        
        local_dict = {p['_id']: p for p in local_products}
        cloud_dict = {p['_id']: p for p in cloud_products}
        
        all_product_ids = set(local_dict.keys()) | set(cloud_dict.keys())
        
        mismatches = {
            'stock_mismatches': [],
            'cloud_only': [],
            'local_only': []
        }
        
        for prod_id in all_product_ids:
            local_prod = local_dict.get(prod_id)
            cloud_prod = cloud_dict.get(prod_id)
            
            if local_prod and cloud_prod:
                # Both exist - check for stock mismatch
                local_stock = local_prod.get('total_stock', 0)
                cloud_stock = cloud_prod.get('total_stock', 0)
                
                if local_stock != cloud_stock:
                    mismatches['stock_mismatches'].append({
                        'product_id': prod_id,
                        'local_product': local_prod,
                        'cloud_product': cloud_prod,
                        'local_stock': local_stock,
                        'cloud_stock': cloud_stock
                    })
            elif cloud_prod:
                # Cloud-only product
                mismatches['cloud_only'].append({
                    'product_id': prod_id,
                    'cloud_product': cloud_prod
                })
            elif local_prod:
                # Local-only product
                mismatches['local_only'].append({
                    'product_id': prod_id,
                    'local_product': local_prod
                })
        
        return mismatches
    
    def _parse_timestamp(self, document):
        """Parse timestamp from document (same logic as sync_service)"""
        timestamp_fields = [
            'last_updated',
            'updated_at',
            'date_updated',
            'created_at',
            'timestamp'
        ]
        
        for field in timestamp_fields:
            value = document.get(field)
            if value is None:
                continue
            
            if isinstance(value, datetime):
                return value
            
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        try:
                            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
                        except ValueError:
                            try:
                                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                            except ValueError:
                                continue
        
        return datetime(1970, 1, 1)  # Fallback to very old date
    
    def _create_sync_plan(self, mismatches, local_db, cloud_db, verbose):
        """Create sync plan with timestamp-based conflict resolution"""
        from app.services.sync_service import sync_service
        
        sync_plan = {
            'push_to_cloud': [],  # Local is newer or local-only
            'pull_to_local': [],  # Cloud is newer or cloud-only
            'conflicts': []  # Same timestamp (use local as source of truth)
        }
        
        # Handle stock mismatches
        for mismatch in mismatches['stock_mismatches']:
            local_prod = mismatch['local_product']
            cloud_prod = mismatch['cloud_product']
            
            local_time = self._parse_timestamp(local_prod)
            cloud_time = self._parse_timestamp(cloud_prod)
            
            if local_time > cloud_time:
                # Local is newer - push to cloud
                sync_plan['push_to_cloud'].append({
                    'product_id': mismatch['product_id'],
                    'product_name': local_prod.get('product_name', 'Unknown'),
                    'local_stock': mismatch['local_stock'],
                    'cloud_stock': mismatch['cloud_stock'],
                    'local_time': local_time,
                    'cloud_time': cloud_time,
                    'reason': 'local_newer'
                })
            elif cloud_time > local_time:
                # Cloud is newer - pull to local
                sync_plan['pull_to_local'].append({
                    'product_id': mismatch['product_id'],
                    'product_name': cloud_prod.get('product_name', 'Unknown'),
                    'local_stock': mismatch['local_stock'],
                    'cloud_stock': mismatch['cloud_stock'],
                    'local_time': local_time,
                    'cloud_time': cloud_time,
                    'reason': 'cloud_newer'
                })
            else:
                # Same timestamp - use local as source of truth
                sync_plan['conflicts'].append({
                    'product_id': mismatch['product_id'],
                    'product_name': local_prod.get('product_name', 'Unknown'),
                    'local_stock': mismatch['local_stock'],
                    'cloud_stock': mismatch['cloud_stock'],
                    'local_time': local_time,
                    'cloud_time': cloud_time,
                    'reason': 'same_timestamp_use_local'
                })
                # Add to push_to_cloud since we use local as source of truth
                sync_plan['push_to_cloud'].append({
                    'product_id': mismatch['product_id'],
                    'product_name': local_prod.get('product_name', 'Unknown'),
                    'local_stock': mismatch['local_stock'],
                    'cloud_stock': mismatch['cloud_stock'],
                    'local_time': local_time,
                    'cloud_time': cloud_time,
                    'reason': 'same_timestamp_use_local'
                })
        
        # Handle cloud-only products (pull to local)
        for item in mismatches['cloud_only']:
            cloud_prod = item['cloud_product']
            sync_plan['pull_to_local'].append({
                'product_id': item['product_id'],
                'product_name': cloud_prod.get('product_name', 'Unknown'),
                'cloud_stock': cloud_prod.get('total_stock', 0),
                'local_stock': None,
                'local_time': None,
                'cloud_time': self._parse_timestamp(cloud_prod),
                'reason': 'cloud_only'
            })
        
        # Handle local-only products (push to cloud)
        for item in mismatches['local_only']:
            local_prod = item['local_product']
            sync_plan['push_to_cloud'].append({
                'product_id': item['product_id'],
                'product_name': local_prod.get('product_name', 'Unknown'),
                'local_stock': local_prod.get('total_stock', 0),
                'cloud_stock': None,
                'local_time': self._parse_timestamp(local_prod),
                'cloud_time': None,
                'reason': 'local_only'
            })
        
        return sync_plan
    
    def _display_sync_plan(self, sync_plan, verbose):
        """Display what would be synced"""
        total_actions = (
            len(sync_plan['push_to_cloud']) +
            len(sync_plan['pull_to_local'])
        )
        
        self.stdout.write(f"Total sync actions: {total_actions}\n")
        self.stdout.write(f"  → Push to cloud: {len(sync_plan['push_to_cloud'])}\n")
        self.stdout.write(f"  → Pull to local: {len(sync_plan['pull_to_local'])}\n")
        if sync_plan['conflicts']:
            self.stdout.write(f"  → Conflicts (same timestamp): {len(sync_plan['conflicts'])}\n")
        self.stdout.write("\n")
        
        if verbose:
            # Show push to cloud
            if sync_plan['push_to_cloud']:
                self.stdout.write("Products to PUSH to cloud:\n")
                self.stdout.write("-"*80 + "\n")
                self.stdout.write(f"{'Product ID':<20} {'Name':<30} {'Local':<10} {'Cloud':<10} {'Reason':<20}\n")
                self.stdout.write("-"*80 + "\n")
                for item in sync_plan['push_to_cloud']:
                    prod_id = str(item['product_id'])[:18]
                    name = item['product_name'][:28]
                    local = str(item['local_stock']) if item['local_stock'] is not None else "N/A"
                    cloud = str(item['cloud_stock']) if item['cloud_stock'] is not None else "N/A"
                    reason = item['reason']
                    self.stdout.write(f"{prod_id:<20} {name:<30} {local:<10} {cloud:<10} {reason:<20}\n")
                self.stdout.write("\n")
            
            # Show pull to local
            if sync_plan['pull_to_local']:
                self.stdout.write("Products to PULL to local:\n")
                self.stdout.write("-"*80 + "\n")
                self.stdout.write(f"{'Product ID':<20} {'Name':<30} {'Local':<10} {'Cloud':<10} {'Reason':<20}\n")
                self.stdout.write("-"*80 + "\n")
                for item in sync_plan['pull_to_local']:
                    prod_id = str(item['product_id'])[:18]
                    name = item['product_name'][:28]
                    local = str(item['local_stock']) if item['local_stock'] is not None else "N/A"
                    cloud = str(item['cloud_stock']) if item['cloud_stock'] is not None else "N/A"
                    reason = item['reason']
                    self.stdout.write(f"{prod_id:<20} {name:<30} {local:<10} {cloud:<10} {reason:<20}\n")
                self.stdout.write("\n")
    
    def _execute_sync(self, sync_plan, local_db, cloud_db):
        """Execute the sync plan"""
        from app.services.sync_service import sync_service
        
        results = {
            'synced': 0,
            'failed': 0,
            'errors': []
        }
        
        # Push to cloud
        for item in sync_plan['push_to_cloud']:
            try:
                product_id = item['product_id']
                local_prod = local_db.products.find_one({'_id': product_id})
                
                if local_prod:
                    # Replace cloud product with local version
                    cloud_db.products.replace_one(
                        {'_id': product_id},
                        local_prod,
                        upsert=True
                    )
                    
                    # Add sync log
                    sync_service.add_sync_log_to_document(
                        'products', product_id, 'synced', 'cloud',
                        {'action': 'smart_sync', 'reason': item['reason']}
                    )
                    
                    results['synced'] += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Pushed to cloud: {item['product_name']} ({product_id})\n"
                    ))
                else:
                    results['failed'] += 1
                    error = f"Local product not found: {product_id}"
                    results['errors'].append(error)
                    self.stdout.write(self.style.ERROR(f"✗ {error}\n"))
                    
            except Exception as e:
                results['failed'] += 1
                error = f"Failed to push {item['product_id']}: {e}"
                results['errors'].append(error)
                self.stdout.write(self.style.ERROR(f"✗ {error}\n"))
        
        # Pull to local
        for item in sync_plan['pull_to_local']:
            try:
                product_id = item['product_id']
                cloud_prod = cloud_db.products.find_one({'_id': product_id})
                
                if cloud_prod:
                    # Replace local product with cloud version
                    local_db.products.replace_one(
                        {'_id': product_id},
                        cloud_prod,
                        upsert=True
                    )
                    
                    # Add sync log
                    sync_service.add_sync_log_to_document(
                        'products', product_id, 'synced', 'local',
                        {'action': 'smart_sync', 'reason': item['reason']}
                    )
                    
                    results['synced'] += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Pulled to local: {item['product_name']} ({product_id})\n"
                    ))
                else:
                    results['failed'] += 1
                    error = f"Cloud product not found: {product_id}"
                    results['errors'].append(error)
                    self.stdout.write(self.style.ERROR(f"✗ {error}\n"))
                    
            except Exception as e:
                results['failed'] += 1
                error = f"Failed to pull {item['product_id']}: {e}"
                results['errors'].append(error)
                self.stdout.write(self.style.ERROR(f"✗ {error}\n"))
        
        return results
    
    def _display_sync_results(self, results):
        """Display sync execution results"""
        self.stdout.write("\n" + "="*80 + "\n")
        self.stdout.write("SYNC RESULTS\n")
        self.stdout.write("="*80 + "\n")
        self.stdout.write(self.style.SUCCESS(f"✓ Successfully synced: {results['synced']}\n"))
        self.stdout.write(self.style.ERROR(f"✗ Failed: {results['failed']}\n"))
        
        if results['errors']:
            self.stdout.write("\nErrors:\n")
            for error in results['errors']:
                self.stdout.write(self.style.ERROR(f"  • {error}\n"))
        
        self.stdout.write("="*80 + "\n")

