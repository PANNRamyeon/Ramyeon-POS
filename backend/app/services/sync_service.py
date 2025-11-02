# app/services/sync_service.py
from datetime import datetime
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
        if self.local_db is None:
            self.local_db = db_manager.get_local_database()
        if self.cloud_db is None:
            self.cloud_db = db_manager.get_cloud_database()
        return self.local_db, self.cloud_db
    
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
            logger.info(f"📴 Offline: Queuing {collection_name} transaction")
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
            
            logger.info(f"✅ Synced {collection_name} transaction to cloud: {document.get('_id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to sync {collection_name}: {e}")
            self.add_to_sync_queue(collection_name, document)
            return False
    
    def sync_background(self):
        """
        Background sync process (called every 30 seconds when online).
        
        Operations:
        1. Pull products from cloud → local (stock mirroring)
        2. Process sync queue (push queued items to cloud)
        3. Bidirectional sync for customers, categories, promotions
        """
        if not db_manager.is_online:
            logger.debug("📴 Skipping background sync - offline")
            return
        
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                return
            
            logger.info("🔄 Starting background sync...")
            
            # 1. Mirror products from cloud to local
            self.mirror_products_from_cloud()
            
            # 2. Process sync queue
            self.process_sync_queue()
            
            # 3. Bidirectional sync for other entities
            self.sync_bidirectional(['customers', 'categories', 'promotions'])
            
            logger.info("✅ Background sync completed")
            
        except Exception as e:
            logger.error(f"❌ Background sync error: {e}")
    
    def mirror_products_from_cloud(self):
        """
        Pull all products from cloud to local (for stock mirroring).
        Products are completely replaced in local DB to ensure accuracy.
        """
        try:
            local_db, cloud_db = self.get_databases()
            if cloud_db is None:
                return
            
            logger.info("🔄 Mirroring products from cloud to local...")
            
            # Get all products from cloud
            cloud_products = cloud_db.products.find({})
            mirrored_count = 0
            
            for product in cloud_products:
                # Replace local product with cloud version (upsert)
                result = local_db.products.replace_one(
                    {'_id': product['_id']},
                    product,
                    upsert=True
                )
                mirrored_count += 1
            
            logger.info(f"✅ Mirrored {mirrored_count} products from cloud to local")
            
        except Exception as e:
            logger.error(f"❌ Product mirroring error: {e}")
    
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
                    
                    # Try to sync
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
                    logger.debug(f"✅ Synced queued {collection_name}: {document.get('_id')}")
                    
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
            
            if processed_count > 0:
                logger.info(f"✅ Processed {processed_count} queued items")
                
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
    
    def _sync_collection_bidirectional(self, collection_name, local_db, cloud_db):
        """Sync a single collection bidirectionally"""
        try:
            # Get local items modified since last sync
            # (In a real implementation, you'd track last_sync_time)
            local_items = local_db[collection_name].find({'sync_logs': {'$exists': False}})
            
            synced_count = 0
            for item in local_items:
                # Check if item exists in cloud
                cloud_item = cloud_db[collection_name].find_one({'_id': item['_id']})
                
                if cloud_item:
                    # Conflict resolution: most recent wins
                    local_time = item.get('last_updated', item.get('date_updated', datetime(1970, 1, 1)))
                    cloud_time = cloud_item.get('last_updated', cloud_item.get('date_updated', datetime(1970, 1, 1)))
                    
                    if local_time > cloud_time:
                        # Local is newer - push to cloud
                        cloud_db[collection_name].replace_one(
                            {'_id': item['_id']},
                            item
                        )
                        synced_count += 1
                else:
                    # New item - insert to cloud
                    cloud_db[collection_name].insert_one(item)
                    synced_count += 1
            
            if synced_count > 0:
                logger.debug(f"✅ Bidirectional sync {collection_name}: {synced_count} items")
                
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
            logger.debug(f"📝 Added to sync queue: {collection_name} - {document.get('_id')}")
            
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
                logger.debug(f"✅ Added sync log to {collection_name}: {doc_id}")
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

# Singleton instance
sync_service = SyncService()

