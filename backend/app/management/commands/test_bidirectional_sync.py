# app/management/commands/test_bidirectional_sync.py
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from app.database import db_manager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test bidirectional product sync (simulates background auto-sync that runs every 5 minutes)'
    
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
        dry_run = not options.get('execute', False)
        verbose = options.get('verbose', False)
        
        self.stdout.write(self.style.SUCCESS(
            "\n" + "="*80 + "\n"
            f"BIDIRECTIONAL PRODUCT SYNC TEST" + (" (DRY-RUN)" if dry_run else " (EXECUTING)") + "\n"
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
                    "❌ Cloud database is not available. Cannot test sync.\n"
                ))
                return
            
            self.stdout.write(f"Connection Status: {'🟢 ONLINE' if db_manager.is_online else '🔴 OFFLINE'}\n")
            self.stdout.write(f"Sync Mode: Check ALL products for mismatches (runs every 5 minutes)\n\n")
            
            # Phase 1: Find ALL products with mismatches
            self.stdout.write("Phase 1: Finding product mismatches...\n")
            self.stdout.write("-"*80 + "\n")
            
            mismatches = self._find_all_product_mismatches(local_db, cloud_db)
            
            total_mismatches = (
                len(mismatches['stock_mismatches']) +
                len(mismatches['cloud_only']) +
                len(mismatches['local_only'])
            )
            
            self.stdout.write(f"Stock mismatches: {len(mismatches['stock_mismatches'])}\n")
            self.stdout.write(f"Cloud-only products: {len(mismatches['cloud_only'])}\n")
            self.stdout.write(f"Local-only products: {len(mismatches['local_only'])}\n")
            self.stdout.write(f"Total products to sync: {total_mismatches}\n\n")
            
            if total_mismatches == 0:
                self.stdout.write(self.style.SUCCESS(
                    "✅ No mismatches found. Everything is in sync.\n"
                ))
                return
            
            # Phase 2: Create sync plan
            self.stdout.write("Phase 2: Analyzing bidirectional sync...\n")
            self.stdout.write("-"*80 + "\n")
            
            sync_plan = self._create_bidirectional_sync_plan(
                mismatches, local_db, cloud_db, verbose
            )
            
            # Display sync plan
            self._display_sync_plan(sync_plan, verbose)
            
            # Phase 3: Execute sync (if not dry-run)
            if not dry_run:
                self.stdout.write("\n" + "="*80 + "\n")
                self.stdout.write("Phase 3: Executing bidirectional sync...\n")
                self.stdout.write("="*80 + "\n")
                
                results = self._execute_bidirectional_sync(sync_plan, local_db, cloud_db)
                
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
            self.stdout.write(f"Sync Frequency: Every 5 minutes (checks ALL products)\n")
            self.stdout.write(f"Local → Cloud: {len(sync_plan['push_to_cloud'])}\n")
            self.stdout.write(f"Cloud → Local: {len(sync_plan['pull_to_local'])}\n")
            self.stdout.write(f"Conflicts Resolved: {len(sync_plan['conflicts'])}\n")
            self.stdout.write(f"Already In Sync: {sync_plan['skipped']}\n")
            if not dry_run:
                self.stdout.write(f"Successfully Synced: {results.get('synced', 0)}\n")
                self.stdout.write(f"Failed: {results.get('failed', 0)}\n")
            self.stdout.write("="*80 + "\n\n")
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\nTest interrupted by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFatal error: {e}"))
            logger.error(f"Bidirectional sync test error: {e}", exc_info=True)
            raise
    
    def _find_all_product_mismatches(self, local_db, cloud_db):
        """Find ALL product mismatches (not just recent)"""
        # Get ALL products from both databases
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
                local_stock = local_prod.get('total_stock', 0)
                cloud_stock = cloud_prod.get('total_stock', 0)
                
                if local_stock != cloud_stock:
                    mismatches['stock_mismatches'].append({
                        'product_id': prod_id,
                        'local_product': local_prod,
                        'cloud_product': cloud_prod
                    })
            elif cloud_prod:
                mismatches['cloud_only'].append({
                    'product_id': prod_id,
                    'cloud_product': cloud_prod
                })
            elif local_prod:
                mismatches['local_only'].append({
                    'product_id': prod_id,
                    'local_product': local_prod
                })
        
        return mismatches
    
    def _parse_timestamp(self, document):
        """Parse timestamp from document"""
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
        
        return datetime(1970, 1, 1)
    
    def _create_bidirectional_sync_plan(self, mismatches, local_db, cloud_db, verbose):
        """Create bidirectional sync plan with conflict resolution"""
        from app.services.sync_service import sync_service
        
        sync_plan = {
            'push_to_cloud': [],
            'pull_to_local': [],
            'conflicts': [],
            'skipped': 0
        }
        
        # Process stock mismatches
        for mismatch in mismatches['stock_mismatches']:
            local_prod = mismatch['local_product']
            cloud_prod = mismatch['cloud_product']
            product_id = mismatch['product_id']
            
            local_time = self._parse_timestamp(local_prod)
            cloud_time = self._parse_timestamp(cloud_prod)
            local_stock = local_prod.get('total_stock', 0)
            cloud_stock = cloud_prod.get('total_stock', 0)
            
            if local_time > cloud_time:
                # Local is newer - push to cloud
                sync_plan['push_to_cloud'].append({
                    'product_id': product_id,
                    'product_name': local_prod.get('product_name', 'Unknown'),
                    'local_stock': local_stock,
                    'cloud_stock': cloud_stock,
                    'local_time': local_time,
                    'cloud_time': cloud_time,
                    'reason': 'local_newer'
                })
            elif cloud_time > local_time:
                # Cloud is newer - pull to local
                sync_plan['pull_to_local'].append({
                    'product_id': product_id,
                    'product_name': cloud_prod.get('product_name', 'Unknown'),
                    'local_stock': local_stock,
                    'cloud_stock': cloud_stock,
                    'local_time': local_time,
                    'cloud_time': cloud_time,
                    'reason': 'cloud_newer'
                })
            else:
                # Same timestamp but different stock - conflict
                sync_plan['conflicts'].append({
                    'product_id': product_id,
                    'product_name': local_prod.get('product_name', 'Unknown'),
                    'local_stock': local_stock,
                    'cloud_stock': cloud_stock,
                    'local_time': local_time,
                    'cloud_time': cloud_time,
                    'reason': 'same_time_diff_stock'
                })
                # Resolve: use local as source of truth
                sync_plan['push_to_cloud'].append({
                    'product_id': product_id,
                    'product_name': local_prod.get('product_name', 'Unknown'),
                    'local_stock': local_stock,
                    'cloud_stock': cloud_stock,
                    'local_time': local_time,
                    'cloud_time': cloud_time,
                    'reason': 'conflict_use_local'
                })
        
        # Process cloud-only products
        for item in mismatches['cloud_only']:
            cloud_prod = item['cloud_product']
            sync_plan['pull_to_local'].append({
                'product_id': item['product_id'],
                'product_name': cloud_prod.get('product_name', 'Unknown'),
                'local_stock': None,
                'cloud_stock': cloud_prod.get('total_stock', 0),
                'cloud_time': self._parse_timestamp(cloud_prod),
                'local_time': None,
                'reason': 'cloud_only'
            })
        
        # Process local-only products
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
        self.stdout.write(f"  → Local → Cloud: {len(sync_plan['push_to_cloud'])}\n")
        self.stdout.write(f"  → Cloud → Local: {len(sync_plan['pull_to_local'])}\n")
        if sync_plan['conflicts']:
            self.stdout.write(self.style.WARNING(
                f"  ⚠️  Conflicts: {len(sync_plan['conflicts'])} (will use local)\n"
            ))
        if sync_plan['skipped'] > 0:
            self.stdout.write(f"  ⊘ Skipped: {sync_plan['skipped']} (already in sync)\n")
        self.stdout.write("\n")
        
        if verbose:
            # Show push to cloud
            if sync_plan['push_to_cloud']:
                self.stdout.write("Products to push LOCAL → CLOUD:\n")
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
                self.stdout.write("Products to pull CLOUD → LOCAL:\n")
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
            
            # Show conflicts
            if sync_plan['conflicts']:
                self.stdout.write(self.style.WARNING("CONFLICTS (same timestamp, different stock):\n"))
                self.stdout.write("-"*80 + "\n")
                self.stdout.write(f"{'Product ID':<20} {'Name':<30} {'Local':<10} {'Cloud':<10} {'Resolution':<20}\n")
                self.stdout.write("-"*80 + "\n")
                for item in sync_plan['conflicts']:
                    prod_id = str(item['product_id'])[:18]
                    name = item['product_name'][:28]
                    local = str(item['local_stock'])
                    cloud = str(item['cloud_stock'])
                    self.stdout.write(f"{prod_id:<20} {name:<30} {local:<10} {cloud:<10} Use Local\n")
                self.stdout.write("\n")
    
    def _execute_bidirectional_sync(self, sync_plan, local_db, cloud_db):
        """Execute the bidirectional sync"""
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
                    cloud_db.products.replace_one(
                        {'_id': product_id},
                        local_prod,
                        upsert=True
                    )
                    sync_service.add_sync_log_to_document(
                        'products', product_id, 'synced', 'cloud',
                        {'action': 'bidirectional_sync', 'reason': item['reason']}
                    )
                    results['synced'] += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Local → Cloud: {item['product_name']} ({product_id})\n"
                    ))
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
                    local_db.products.replace_one(
                        {'_id': product_id},
                        cloud_prod,
                        upsert=True
                    )
                    sync_service.add_sync_log_to_document(
                        'products', product_id, 'synced', 'local',
                        {'action': 'bidirectional_sync', 'reason': item['reason']}
                    )
                    results['synced'] += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Cloud → Local: {item['product_name']} ({product_id})\n"
                    ))
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

