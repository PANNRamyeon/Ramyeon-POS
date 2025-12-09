# app/services/sync_service.py
from datetime import datetime, timedelta
from ..database import db_manager
from ..models import SalesLog, Product, Customer
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

class SyncService:
    """
    Handles synchronization between local and cloud MongoDB databases.
    
    Two sync modes:
    1. Immediate: Called after each transaction (sales, stock updates)
    2. Background: Periodic sync every 30s for other entities
    """
    
    def __init__(self):
        self.local_db = None
        self.cloud_db = None
        
    def get_databases(self):
        """Get both local and cloud database connections"""
        # Always fetch fresh references to avoid caching issues
        local_db = db_manager.get_local_database()
        cloud_db = db_manager.get_cloud_database()
        return local_db, cloud_db
    
    def sync_transaction_immediate(self, collection_name, document):
        """
        Sync a single transaction to cloud immediately.
        
        Args:
            collection_name: Name of collection (e.g., 'sales', 'products')
            document: Document to sync
            
        Returns:
            bool: True if synced successfully, False if queued
        """
        if not db_manager.is_online:
            self.add_to_sync_queue(collection_name, document)
            return False
        
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                logger.warning("No cloud connection available")
                self.add_to_sync_queue(collection_name, document)
                return False
            
            # Insert into cloud database
            cloud_db[collection_name].insert_one(document)
            
            # Add sync log
            self.add_sync_log_to_document(collection_name, document.get('_id'), 'synced', 'cloud')
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to sync {collection_name}: {e}")
            self.add_to_sync_queue(collection_name, document)
            return False
    
    def sync_background(self):
        """
        Background sync process (called every 30 seconds when online).
        
        Operations:
        1. Sync recent batches bidirectionally (incremental, last 5 min)
        2. Sync ALL products bidirectionally (checks all, syncs mismatches)
        3. Process sync queue (push queued items to cloud)
        4. Bidirectional sync for customers, categories, promotions, online_transactions
        """
        if not db_manager.is_online:
            return
        
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                return
            
            # 1. Sync batches bidirectionally (admin creates in cloud, POS creates in local)
            self.mirror_batches_from_local()
            
            # 2. Sync products bidirectionally (checks all products for mismatches)
            self.sync_products_bidirectional()
            
            # 3. Process sync queue
            self.process_sync_queue()
            
            # 4. Bidirectional sync for other entities
            self.sync_bidirectional(['customers', 'categories', 'promotions', 'online_transactions'])
            
        except Exception as e:
            logger.error(f"❌ Background sync error: {e}")
    
    def sync_products_bidirectional(self):
        """
        Bidirectional product sync - checks ALL products for mismatches.
        Runs every 30 seconds as part of background sync.
        Uses timestamp-based conflict resolution (latest wins).
        """
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                return
            
            # Find all product mismatches
            local_products = list(local_db.products.find({}))
            cloud_products = list(cloud_db.products.find({}))
            
            local_dict = {p['_id']: p for p in local_products}
            cloud_dict = {p['_id']: p for p in cloud_products}
            
            all_product_ids = set(local_dict.keys()) | set(cloud_dict.keys())
            
            synced_count = 0
            
            for product_id in all_product_ids:
                local_prod = local_dict.get(product_id)
                cloud_prod = cloud_dict.get(product_id)
                
                try:
                    if local_prod and cloud_prod:
                        # Both exist - check for mismatch
                        local_stock = local_prod.get('total_stock', 0)
                        cloud_stock = cloud_prod.get('total_stock', 0)
                        
                        if local_stock != cloud_stock:
                            # Stock mismatch - use timestamp to resolve
                            local_time = self._parse_timestamp(local_prod)
                            cloud_time = self._parse_timestamp(cloud_prod)
                            
                            if local_time >= cloud_time:
                                # Local is newer or same - push to cloud
                                cloud_db.products.replace_one(
                                    {'_id': product_id},
                                    local_prod
                                )
                                synced_count += 1
                            else:
                                # Cloud is newer - pull to local
                                local_db.products.replace_one(
                                    {'_id': product_id},
                                    cloud_prod
                                )
                                synced_count += 1
                    
                    elif cloud_prod:
                        # Cloud-only - pull to local
                        local_db.products.insert_one(cloud_prod)
                        synced_count += 1
                    
                    elif local_prod:
                        # Local-only - push to cloud
                        cloud_db.products.insert_one(local_prod)
                        synced_count += 1
                
                except Exception as e:
                    logger.error(f"❌ Failed to sync product {product_id}: {e}")
            
            if synced_count > 0:
                logger.info(f"✓ Bidirectional product sync: {synced_count} products synced")
            
        except Exception as e:
            logger.error(f"❌ Bidirectional product sync error: {e}")
    
    def mirror_products_from_local(self):
        """
        DEPRECATED: Replaced by sync_products_bidirectional()
        Kept for backward compatibility.
        """
        # This method is no longer used but kept to avoid breaking existing code
        pass
    
    def mirror_batches_from_local(self):
        """
        Bidirectional sync for batches (admin creates in cloud, POS creates in local).
        Uses incremental sync: only syncs batches modified in the last 5 minutes.
        Conflict resolution: MERGE to prevent data loss.
        """
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                return
            
            # Get batches modified in last 5 minutes (for incremental sync)
            five_min_ago = datetime.utcnow() - timedelta(minutes=5)
            
            # Push local batches to cloud (merge if conflict)
            recent_local_batches = local_db.batches.find({
                'updated_at': {'$gte': five_min_ago}
            })
            
            for batch in recent_local_batches:
                batch_id = batch['_id']
                cloud_batch = cloud_db.batches.find_one({'_id': batch_id})
                
                if cloud_batch:
                    # Merge batches to prevent data loss
                    merged_batch = self._merge_batches(batch, cloud_batch)
                    cloud_db.batches.replace_one({'_id': batch_id}, merged_batch)
                else:
                    # Batch doesn't exist in cloud, insert it
                    cloud_db.batches.insert_one(batch)
            
            # Pull cloud batches to local (merge if conflict)
            recent_cloud_batches = cloud_db.batches.find({
                'updated_at': {'$gte': five_min_ago}
            })
            
            for batch in recent_cloud_batches:
                batch_id = batch['_id']
                local_batch = local_db.batches.find_one({'_id': batch_id})
                
                if local_batch:
                    # Merge batches to prevent data loss
                    merged_batch = self._merge_batches(local_batch, batch)
                    local_db.batches.replace_one({'_id': batch_id}, merged_batch)
                else:
                    # Batch doesn't exist in local, insert it
                    local_db.batches.insert_one(batch)
            
        except Exception as e:
            logger.error(f"❌ Batch sync error: {e}")
    
    def _merge_batches(self, batch1, batch2):
        """
        Merge two batch documents to prevent data loss.
        
        Strategy:
        - Merge usage_history from both batches
        - Recalculate quantity_remaining from merged history
        - Keep latest updated_at and status
        - Merge other fields intelligently
        
        Args:
            batch1: First batch document
            batch2: Second batch document
            
        Returns:
            Merged batch document
        """
        # Merge usage_history arrays from both batches
        usage_history1 = batch1.get('usage_history', [])
        usage_history2 = batch2.get('usage_history', [])
        merged_history = usage_history1 + usage_history2
        
        # Remove duplicates by timestamp and quantity_used
        # (in case same transaction appears in both)
        seen = set()
        unique_history = []
        for entry in merged_history:
            # Create unique key from timestamp, quantity, and adjustment_type
            key = (
                entry.get('timestamp'),
                entry.get('quantity_used'),
                entry.get('adjustment_type')
            )
            if key not in seen:
                seen.add(key)
                unique_history.append(entry)
        
        # Sort by timestamp to maintain chronological order
        unique_history.sort(key=lambda x: x.get('timestamp', datetime(1970, 1, 1)))
        
        # Recalculate quantity_remaining from merged history
        # Start with quantity_received and apply all usage_history entries
        quantity_received = batch1.get('quantity_received', batch2.get('quantity_received', 0))
        recalculated_remaining = quantity_received
        
        for entry in unique_history:
            quantity_used = entry.get('quantity_used', 0)
            # If quantity_used is negative, it's a restoration
            recalculated_remaining -= quantity_used
        
        # Ensure non-negative
        recalculated_remaining = max(0, recalculated_remaining)
        
        # Determine latest timestamp
        time1 = batch1.get('updated_at', datetime(1970, 1, 1))
        time2 = batch2.get('updated_at', datetime(1970, 1, 1))
        latest_time = time2 if time2 > time1 else time1
        
        # Check if batches are expired based on expiry_date
        def is_expired(batch):
            """Check if batch is expired"""
            expiry_date = batch.get('expiry_date')
            if expiry_date is None:
                return False
            
            # Handle both datetime objects and strings
            if isinstance(expiry_date, str):
                try:
                    expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return False
            
            # Compare with current date (UTC)
            now = datetime.utcnow()
            expiry_date_only = expiry_date.date() if hasattr(expiry_date, 'date') else expiry_date
            now_date_only = now.date() if hasattr(now, 'date') else now
            
            if isinstance(expiry_date_only, datetime):
                expiry_date_only = expiry_date_only.date()
            if isinstance(now_date_only, datetime):
                now_date_only = now_date_only.date()
            
            return expiry_date_only < now_date_only
        
        # Status priority: expired > depleted > active
        # Check both status field and actual expiry date
        status1 = batch1.get('status', 'active')
        status2 = batch2.get('status', 'active')
        expired1 = status1 == 'expired' or is_expired(batch1)
        expired2 = status2 == 'expired' or is_expired(batch2)
        
        if expired1 or expired2:
            merged_status = 'expired'
        elif recalculated_remaining == 0:
            merged_status = 'depleted'
        else:
            merged_status = 'active'
        
        # Create merged batch document
        merged_batch = {
            '_id': batch1['_id'],
            'product_id': batch1.get('product_id', batch2.get('product_id')),
            'batch_number': batch1.get('batch_number', batch2.get('batch_number')),
            'quantity_received': quantity_received,
            'quantity_remaining': recalculated_remaining,
            'cost_price': batch1.get('cost_price', batch2.get('cost_price', 0)),
            'expiry_date': batch1.get('expiry_date', batch2.get('expiry_date')),
            'expected_delivery_date': batch1.get('expected_delivery_date', batch2.get('expected_delivery_date')),
            'date_received': batch1.get('date_received', batch2.get('date_received')),
            'supplier_id': batch1.get('supplier_id', batch2.get('supplier_id')),
            'status': merged_status,
            'created_at': batch1.get('created_at', batch2.get('created_at')),
            'updated_at': latest_time,
            'notes': batch1.get('notes', batch2.get('notes', '')),
            'usage_history': unique_history,
            'sync_logs': batch1.get('sync_logs', batch2.get('sync_logs', []))
        }
        
        return merged_batch
    
    def process_sync_queue(self):
        """Process queued items from local to cloud"""
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                return
            
            # Get pending items from sync_queue collection
            pending_items = local_db.sync_queue.find({'status': 'pending'})
            processed_count = 0
            
            for item in pending_items:
                try:
                    collection_name = item['collection']
                    document = item['document']
                    
                    # Check if document already exists in cloud (could be synced already)
                    doc_id = document.get('_id')
                    existing_doc = cloud_db[collection_name].find_one({'_id': doc_id})
                    
                    if existing_doc:
                        # Document exists, update it
                        cloud_db[collection_name].replace_one({'_id': doc_id}, document)
                    else:
                        # Document doesn't exist, insert it
                        cloud_db[collection_name].insert_one(document)
                    
                    # Mark as synced
                    local_db.sync_queue.update_one(
                        {'_id': item['_id']},
                        {
                            '$set': {
                                'status': 'synced',
                                'synced_at': datetime.utcnow()
                            }
                        }
                    )
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to sync queued item: {e}")
                    # Retry later - keep as pending
                    local_db.sync_queue.update_one(
                        {'_id': item['_id']},
                        {
                            '$set': {
                                'status': 'failed',
                                'error': str(e),
                                'retry_at': datetime.utcnow()
                            }
                        }
                    )
            
        except Exception as e:
            logger.error(f"❌ Sync queue processing error: {e}")
    
    def sync_bidirectional(self, collection_names):
        """
        Bidirectional sync for specified collections.
        Uses last_updated timestamp for conflict resolution.
        """
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                return
            
            for collection_name in collection_names:
                self._sync_collection_bidirectional(collection_name, local_db, cloud_db)
                
        except Exception as e:
            logger.error(f"❌ Bidirectional sync error: {e}")
    
    def _parse_timestamp(self, document, fallback=None):
        """
        Extract a datetime timestamp from a document.
        
        Looks for a list of common timestamp fields and gracefully handles
        values stored as strings.
        """
        fallback = fallback or datetime(1970, 1, 1)
        timestamp_fields = [
            'last_updated',
            'updated_at',
            'date_updated',
            'order_date',
            'created_at',
            'timestamp'
        ]
        
        for field in timestamp_fields:
            value = document.get(field)
            if value is None:
                continue
            
            if isinstance(value, datetime):
                return value
            
            # Handle ISO-formatted strings
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    # Try parsing common datetime formats
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
        
        return fallback
    
    def _should_consider_document(self, document, sync_window):
        """
        Determine if a document should be considered for sync.
        
        We sync documents that:
          - Have no sync_logs (never synced)
          - Have an empty sync_logs array
          - Have been updated within the sync window
        """
        if document.get('sync_logs') in (None, []):
            return True
        
        doc_timestamp = self._parse_timestamp(document)
        return doc_timestamp >= sync_window
    
    def _sync_collection_bidirectional(self, collection_name, local_db, cloud_db):
        """
        Sync a single collection bidirectionally.
        
        Strategy:
          1. Push local changes/new documents to cloud
          2. Pull cloud changes/new documents to local
          3. Resolve conflicts using the most recent timestamp
        """
        try:
            sync_window = datetime.utcnow() - timedelta(minutes=5)
            
            # -------------------------------
            # 1. Local -> Cloud
            # -------------------------------
            local_candidates = local_db[collection_name].find({})
            for local_doc in local_candidates:
                if not self._should_consider_document(local_doc, sync_window):
                    continue
                
                doc_id = local_doc.get('_id')
                if doc_id is None:
                    continue
                
                cloud_doc = cloud_db[collection_name].find_one({'_id': doc_id})
                if cloud_doc:
                    local_time = self._parse_timestamp(local_doc)
                    cloud_time = self._parse_timestamp(cloud_doc)
                    
                    if local_time > cloud_time:
                        cloud_db[collection_name].replace_one({'_id': doc_id}, local_doc)
                else:
                    cloud_db[collection_name].insert_one(local_doc)
            
            # -------------------------------
            # 2. Cloud -> Local
            # -------------------------------
            cloud_candidates = cloud_db[collection_name].find({})
            for cloud_doc in cloud_candidates:
                if not self._should_consider_document(cloud_doc, sync_window):
                    continue
                
                doc_id = cloud_doc.get('_id')
                if doc_id is None:
                    continue
                
                local_doc = local_db[collection_name].find_one({'_id': doc_id})
                if local_doc:
                    local_time = self._parse_timestamp(local_doc)
                    cloud_time = self._parse_timestamp(cloud_doc)
                    
                    if cloud_time > local_time:
                        local_db[collection_name].replace_one({'_id': doc_id}, cloud_doc)
                else:
                    local_db[collection_name].insert_one(cloud_doc)
            
        except Exception as e:
            logger.error(f"❌ Bidirectional sync error for {collection_name}: {e}")
    
    def add_to_sync_queue(self, collection_name, document):
        """Add item to sync queue for later processing"""
        try:
            local_db, _ = self.get_databases()
            
            queue_item = {
                'collection': collection_name,
                'document': document,
                'status': 'pending',
                'created_at': datetime.utcnow(),
                'retry_count': 0
            }
            
            local_db.sync_queue.insert_one(queue_item)
            
        except Exception as e:
            logger.error(f"❌ Failed to add to sync queue: {e}")
    
    def add_sync_log_to_document(self, collection_name, doc_id, status, source, details=None):
        """
        Add sync log entry to a document's sync_logs array.
        Uses the existing sync_logs pattern from the codebase.
        """
        try:
            local_db, _ = self.get_databases()
            
            sync_log = {
                'timestamp': datetime.utcnow(),
                'source': source,
                'status': status,
                'details': details or {}
            }
            
            result = local_db[collection_name].update_one(
                {'_id': doc_id},
                {'$push': {'sync_logs': sync_log}}
            )
            
            if result.modified_count > 0:
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to add sync log: {e}")
            return False
    
    def get_sync_status(self):
        """Get current sync status"""
        try:
            local_db, _ = self.get_databases()
            
            # Count pending items in queue
            pending_count = local_db.sync_queue.count_documents({'status': 'pending'})
            
            return {
                'is_online': db_manager.is_online,
                'pending_syncs': pending_count,
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get sync status: {e}")
            return {
                'is_online': False,
                'pending_syncs': 0,
                'error': str(e)
            }
    
    def is_local_database_empty(self):
        """
        Check if local database is empty (first launch scenario).
        Checks key collections: products, categories, batches, customers.
        
        Returns:
            bool: True if local database appears empty, False otherwise
        """
        try:
            local_db, _ = self.get_databases()
            
            # Check key collections that should have data
            key_collections = ['products', 'categories', 'batches', 'customers']
            total_docs = 0
            
            for collection_name in key_collections:
                count = local_db[collection_name].count_documents({})
                total_docs += count
            
            # Consider database empty if total documents < 10 (arbitrary threshold)
            is_empty = total_docs < 10
            
            if is_empty:
                logger.info(f"📊 Local database appears empty (total docs: {total_docs})")
            
            return is_empty
            
        except Exception as e:
            logger.error(f"❌ Failed to check if local database is empty: {e}")
            return False  # Assume not empty on error
    
    def pull_all_from_cloud(self):
        """
        Pull all data from cloud to local (initial bootstrap).
        Only runs if local database is empty and cloud is available.
        
        Returns:
            dict: Summary of pulled data
        """
        if not db_manager.is_online:
            logger.warning("⚠️ Cannot pull from cloud - offline")
            return {'pulled': 0, 'failed': 0, 'collections': []}
        
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                logger.warning("⚠️ No cloud database available")
                return {'pulled': 0, 'failed': 0, 'collections': []}
            
            print("\n" + "=" * 60)
            print("INITIAL DATA PULL FROM CLOUD")
            print("=" * 60)
            print()
            
            # Get ALL collections from cloud database dynamically
            try:
                # List all collection names from cloud database
                collections_to_pull = cloud_db.list_collection_names()
                
                # Filter out MongoDB system collections
                system_collections = ['system.indexes', 'system.collections', 'system.profile']
                collections_to_pull = [c for c in collections_to_pull if c not in system_collections]
                
                print(f"Found {len(collections_to_pull)} collections in cloud database")
                
            except Exception as e:
                logger.error(f"Failed to list cloud collections: {e}")
                # Fallback to hardcoded list if listing fails
                collections_to_pull = [
                    'products', 'category', 'batches', 'customers', 'suppliers',
                    'promotions', 'users', 'sales', 'sales_log', 'shifts', 'carts',
                    'online_transactions', 'audit_logs', 'session_logs', 
                    'token_blacklist', 'notifications', 'loyalty_transactions'
                ]
                print(f"Using fallback list: {len(collections_to_pull)} collections")
            
            total_pulled = 0
            total_failed = 0
            collection_results = {}
            
            for collection_name in collections_to_pull:
                try:
                    # Get all documents from cloud
                    cloud_docs = list(cloud_db[collection_name].find({}))
                    cloud_count = len(cloud_docs)
                    
                    if cloud_count == 0:
                        print(f"   {collection_name}: No data in cloud (skipping)")
                        collection_results[collection_name] = {'pulled': 0, 'failed': 0}
                        continue
                    
                    print(f"   {collection_name}: Pulling {cloud_count} documents...")
                    
                    pulled_count = 0
                    failed_count = 0
                    
                    for doc in cloud_docs:
                        doc_id = doc.get('_id')
                        try:
                            # Check if document already exists locally
                            local_doc = local_db[collection_name].find_one({'_id': doc_id})
                            
                            if local_doc:
                                # Update existing document
                                local_db[collection_name].replace_one({'_id': doc_id}, doc)
                                pulled_count += 1
                            else:
                                # Insert new document
                                local_db[collection_name].insert_one(doc)
                                pulled_count += 1
                                
                        except Exception as e:
                            logger.error(f"Failed to pull {collection_name} {doc_id}: {e}")
                            failed_count += 1
                    
                    total_pulled += pulled_count
                    total_failed += failed_count
                    collection_results[collection_name] = {
                        'pulled': pulled_count,
                        'failed': failed_count,
                        'total': cloud_count
                    }
                    
                    print(f"   ✓ {collection_name}: {pulled_count} pulled, {failed_count} failed")
                    
                except Exception as e:
                    logger.error(f"❌ Error pulling {collection_name}: {e}")
                    collection_results[collection_name] = {'pulled': 0, 'failed': 0, 'error': str(e)}
            
            print()
            print("=" * 60)
            print(f"INITIAL PULL COMPLETE")
            print("=" * 60)
            print(f"Total pulled: {total_pulled}")
            print(f"Total failed: {total_failed}")
            print("=" * 60)
            print()
            
            return {
                'pulled': total_pulled,
                'failed': total_failed,
                'collections': collection_results
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to pull all data from cloud: {e}")
            return {'pulled': 0, 'failed': 0, 'error': str(e)}
    
    def backfill_collection(self, collection_name):
        """
        Backfill unsynced documents from local to cloud.
        Finds documents in local without sync_logs or with unsynced status.
        
        Args:
            collection_name: Name of collection to backfill (e.g., 'sales', 'products')
            
        Returns:
            dict: {'synced': count, 'failed': count, 'total': count}
        """
        print(f"\n[BACKFILL] Starting backfill for {collection_name}...")
        
        if not db_manager.is_online:
            print(f"[BACKFILL] Cannot backfill - offline")
            return {'synced': 0, 'failed': 0, 'total': 0, 'error': 'Offline'}
        
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                print(f"[BACKFILL] No cloud database available")
                return {'synced': 0, 'failed': 0, 'total': 0, 'error': 'No cloud connection'}
            
            # Find all local documents
            local_docs = list(local_db[collection_name].find({}))
            print(f"[BACKFILL] Found {len(local_docs)} documents in local {collection_name}")
            
            synced_count = 0
            failed_count = 0
            skipped_count = 0
            
            for doc in local_docs:
                doc_id = doc.get('_id')
                try:
                    # Check if document exists in cloud
                    cloud_doc = cloud_db[collection_name].find_one({'_id': doc_id})
                    
                    if cloud_doc:
                        print(f"[BACKFILL] {collection_name} {doc_id} already exists in cloud, skipping")
                        skipped_count += 1
                        continue
                    
                    # Insert into cloud
                    cloud_db[collection_name].insert_one(doc)
                    print(f"[BACKFILL] Synced {collection_name} {doc_id} to cloud")
                    
                    # Add sync log
                    self.add_sync_log_to_document(collection_name, doc_id, 'synced', 'cloud', 
                                                   {'backfilled': True, 'timestamp': datetime.utcnow().isoformat()})
                    synced_count += 1
                    
                except Exception as e:
                    print(f"[BACKFILL] Failed to sync {collection_name} {doc_id}: {e}")
                    failed_count += 1
            
            result = {
                'synced': synced_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'total': len(local_docs)
            }
            
            print(f"\n[BACKFILL] Results for {collection_name}:")
            print(f"   Total: {result['total']}")
            print(f"   Synced: {result['synced']}")
            print(f"   Skipped: {result['skipped']}")
            print(f"   Failed: {result['failed']}")
            
            return result
            
        except Exception as e:
            print(f"[BACKFILL] Error during backfill: {e}")
            return {'synced': 0, 'failed': 0, 'total': 0, 'error': str(e)}

    def smart_sync_products_startup(self):
        """
        Smart sync for startup: Only sync products with mismatches.
        Uses timestamp-based conflict resolution (latest wins).
        
        Returns:
            dict: Summary of sync results
        """
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                return {
                    'total_synced': 0,
                    'pushed_to_cloud': 0,
                    'pulled_to_local': 0,
                    'failed': 0,
                    'error': 'Cloud database not available'
                }
            
            # Find mismatches
            mismatches = self._find_product_mismatches_startup(local_db, cloud_db)
            
            total_mismatches = (
                len(mismatches['stock_mismatches']) +
                len(mismatches['cloud_only']) +
                len(mismatches['local_only'])
            )
            
            if total_mismatches == 0:
                return {
                    'total_synced': 0,
                    'pushed_to_cloud': 0,
                    'pulled_to_local': 0,
                    'failed': 0
                }
            
            # Create sync plan
            sync_plan = self._create_sync_plan_startup(mismatches, local_db, cloud_db)
            
            # Execute sync
            results = self._execute_sync_startup(sync_plan, local_db, cloud_db)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Smart sync startup error: {e}")
            return {
                'total_synced': 0,
                'pushed_to_cloud': 0,
                'pulled_to_local': 0,
                'failed': 0,
                'error': str(e)
            }
    
    def _find_product_mismatches_startup(self, local_db, cloud_db):
        """Find product mismatches for startup sync"""
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
    
    def _create_sync_plan_startup(self, mismatches, local_db, cloud_db):
        """Create sync plan with timestamp-based conflict resolution"""
        sync_plan = {
            'push_to_cloud': [],
            'pull_to_local': []
        }
        
        # Handle stock mismatches
        for mismatch in mismatches['stock_mismatches']:
            local_prod = mismatch['local_product']
            cloud_prod = mismatch['cloud_product']
            
            local_time = self._parse_timestamp(local_prod)
            cloud_time = self._parse_timestamp(cloud_prod)
            
            if local_time >= cloud_time:
                # Local is newer or same - push to cloud (local is source of truth)
                sync_plan['push_to_cloud'].append(mismatch['product_id'])
            else:
                # Cloud is newer - pull to local
                sync_plan['pull_to_local'].append(mismatch['product_id'])
        
        # Handle cloud-only products (pull to local)
        for item in mismatches['cloud_only']:
            sync_plan['pull_to_local'].append(item['product_id'])
        
        # Handle local-only products (push to cloud)
        for item in mismatches['local_only']:
            sync_plan['push_to_cloud'].append(item['product_id'])
        
        return sync_plan
    
    def _execute_sync_startup(self, sync_plan, local_db, cloud_db):
        """Execute the sync plan"""
        results = {
            'total_synced': 0,
            'pushed_to_cloud': 0,
            'pulled_to_local': 0,
            'failed': 0
        }
        
        # Push to cloud
        for product_id in sync_plan['push_to_cloud']:
            try:
                local_prod = local_db.products.find_one({'_id': product_id})
                if local_prod:
                    cloud_db.products.replace_one(
                        {'_id': product_id},
                        local_prod,
                        upsert=True
                    )
                    self.add_sync_log_to_document(
                        'products', product_id, 'synced', 'cloud',
                        {'action': 'smart_sync_startup'}
                    )
                    results['pushed_to_cloud'] += 1
                    results['total_synced'] += 1
            except Exception as e:
                logger.error(f"Failed to push {product_id}: {e}")
                results['failed'] += 1
        
        # Pull to local
        for product_id in sync_plan['pull_to_local']:
            try:
                cloud_prod = cloud_db.products.find_one({'_id': product_id})
                if cloud_prod:
                    local_db.products.replace_one(
                        {'_id': product_id},
                        cloud_prod,
                        upsert=True
                    )
                    self.add_sync_log_to_document(
                        'products', product_id, 'synced', 'local',
                        {'action': 'smart_sync_startup'}
                    )
                    results['pulled_to_local'] += 1
                    results['total_synced'] += 1
            except Exception as e:
                logger.error(f"Failed to pull {product_id}: {e}")
                results['failed'] += 1
        
        return results
    
    def smart_sync_batches_startup(self):
        """
        Smart sync for batches on startup: Sync all batches bidirectionally.
        Uses merge logic for conflicts to prevent data loss.
        
        Returns:
            dict: Summary of sync results
        """
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                return {
                    'total_synced': 0,
                    'pushed_to_cloud': 0,
                    'pulled_to_local': 0,
                    'merged': 0,
                    'failed': 0,
                    'error': 'Cloud database not available'
                }
            
            # Get ALL batches from both databases (not just recent ones)
            local_batches = list(local_db.batches.find({}))
            cloud_batches = list(cloud_db.batches.find({}))
            
            local_dict = {b['_id']: b for b in local_batches}
            cloud_dict = {b['_id']: b for b in cloud_batches}
            
            all_batch_ids = set(local_dict.keys()) | set(cloud_dict.keys())
            
            results = {
                'total_synced': 0,
                'pushed_to_cloud': 0,
                'pulled_to_local': 0,
                'merged': 0,
                'failed': 0
            }
            
            # Helper function to check if batch is expired
            def is_batch_expired(batch):
                """Check if batch is expired based on expiry_date"""
                expiry_date = batch.get('expiry_date')
                if expiry_date is None:
                    return False
                
                # Handle both datetime objects and strings
                if isinstance(expiry_date, str):
                    try:
                        expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        return False
                
                # Compare with current date (UTC)
                now = datetime.utcnow()
                expiry_date_only = expiry_date.date() if hasattr(expiry_date, 'date') else expiry_date
                now_date_only = now.date() if hasattr(now, 'date') else now
                
                if isinstance(expiry_date_only, datetime):
                    expiry_date_only = expiry_date_only.date()
                if isinstance(now_date_only, datetime):
                    now_date_only = now_date_only.date()
                
                return expiry_date_only < now_date_only
            
            # Sync each batch
            for batch_id in all_batch_ids:
                try:
                    local_batch = local_dict.get(batch_id)
                    cloud_batch = cloud_dict.get(batch_id)
                    
                    # Update status to 'expired' if batch is actually expired
                    if local_batch and is_batch_expired(local_batch) and local_batch.get('status') != 'expired':
                        local_batch['status'] = 'expired'
                        local_db.batches.update_one({'_id': batch_id}, {'$set': {'status': 'expired'}})
                    
                    if cloud_batch and is_batch_expired(cloud_batch) and cloud_batch.get('status') != 'expired':
                        cloud_batch['status'] = 'expired'
                        cloud_db.batches.update_one({'_id': batch_id}, {'$set': {'status': 'expired'}})
                    
                    if local_batch and cloud_batch:
                        # Both exist - merge to prevent data loss
                        merged_batch = self._merge_batches(local_batch, cloud_batch)
                        
                        # Update both databases with merged batch
                        local_db.batches.replace_one({'_id': batch_id}, merged_batch)
                        cloud_db.batches.replace_one({'_id': batch_id}, merged_batch)
                        
                        results['merged'] += 1
                        results['total_synced'] += 1
                        
                    elif local_batch:
                        # Local-only - push to cloud
                        cloud_db.batches.replace_one(
                            {'_id': batch_id},
                            local_batch,
                            upsert=True
                        )
                        results['pushed_to_cloud'] += 1
                        results['total_synced'] += 1
                        
                    elif cloud_batch:
                        # Cloud-only - pull to local
                        local_db.batches.replace_one(
                            {'_id': batch_id},
                            cloud_batch,
                            upsert=True
                        )
                        results['pulled_to_local'] += 1
                        results['total_synced'] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to sync batch {batch_id}: {e}")
                    results['failed'] += 1
            
            if results['total_synced'] > 0:
                logger.info(f"✓ Startup batch sync: {results['total_synced']} batches synced "
                          f"(pushed: {results['pushed_to_cloud']}, "
                          f"pulled: {results['pulled_to_local']}, "
                          f"merged: {results['merged']})")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Smart batch sync startup error: {e}")
            return {
                'total_synced': 0,
                'pushed_to_cloud': 0,
                'pulled_to_local': 0,
                'merged': 0,
                'failed': 0,
                'error': str(e)
            }

# Singleton instance
sync_service = SyncService()

# Export the startup function for easy import
def smart_sync_products_startup():
    """Wrapper function for startup smart sync"""
    return sync_service.smart_sync_products_startup()

def smart_sync_batches_startup():
    """Wrapper function for startup batch sync"""
    return sync_service.smart_sync_batches_startup()

