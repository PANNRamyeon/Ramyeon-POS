import logging
import time
from datetime import datetime
from bson import ObjectId
from database import db_service

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self):
        self.sync_in_progress = False
        self.last_sync_time = None
    
    def sync_all_data(self):
        """Main synchronization method"""
        if self.sync_in_progress:
            logger.info("Sync already in progress, skipping...")
            return False
        
        if not db_service.is_cloud_available():
            logger.warning("Cloud not available for sync")
            return False
        
        try:
            self.sync_in_progress = True
            logger.info("🔄 Starting data synchronization...")
            
            # Sync sequence - pull first, then push
            self._pull_from_cloud()
            self._push_to_cloud()
            
            self.last_sync_time = datetime.now()
            logger.info("✅ Data synchronization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return False
        finally:
            self.sync_in_progress = False
    
    def _pull_from_cloud(self):
        """Pull latest data from cloud to local"""
        logger.info("⬇️ Pulling data from cloud...")
        
        collections_to_sync = ['products', 'categories', 'promotions']
        
        for collection_name in collections_to_sync:
            self._sync_collection_from_cloud(collection_name)
        
        logger.info("✅ Data pull from cloud completed")
    
    def _sync_collection_from_cloud(self, collection_name):
        """Sync a specific collection from cloud to local"""
        try:
            cloud_collection = db_service.get_cloud_collection(collection_name)
            local_collection = db_service.get_local_collection(collection_name)
            
            if not cloud_collection:
                logger.warning(f"Cloud collection {collection_name} not available")
                return
            
            # Get all active documents from cloud (not deleted)
            cloud_docs = list(cloud_collection.find({"isDeleted": {"$ne": True}}))
            
            # Update or insert in local
            for doc in cloud_docs:
                doc_id = doc['_id']
                doc_copy = doc.copy()
                
                # Update local document
                local_collection.replace_one(
                    {'_id': doc_id},
                    doc_copy,
                    upsert=True
                )
            
            logger.info(f"✅ Synced {len(cloud_docs)} {collection_name} from cloud")
            
        except Exception as e:
            logger.error(f"❌ Error syncing {collection_name} from cloud: {e}")
    
    def _push_to_cloud(self):
        """Push local changes to cloud"""
        logger.info("⬆️ Pushing local changes to cloud...")
        
        # Sync sales transactions
        self._sync_sales_to_cloud()
        
        # Sync stock updates
        self._sync_stock_updates_to_cloud()
        
        # Sync shifts
        self._sync_shifts_to_cloud()
        
        logger.info("✅ Data push to cloud completed")
    
    def _sync_sales_to_cloud(self):
        """Sync sales transactions to cloud"""
        try:
            local_sales = db_service.get_local_collection('sales')
            cloud_sales = db_service.get_cloud_collection('sales')
            
            if not cloud_sales:
                return
            
            # Find unsynced sales (those without sync metadata or synced=False)
            unsynced_sales = list(local_sales.find({
                '$or': [
                    {'synced': {'$exists': False}},
                    {'synced': False}
                ]
            }))
            
            for sale in unsynced_sales:
                try:
                    sale_id = sale['_id']
                    
                    # Insert or update in cloud
                    cloud_sales.replace_one(
                        {'_id': sale_id},
                        sale,
                        upsert=True
                    )
                    
                    # Mark as synced in local
                    local_sales.update_one(
                        {'_id': sale_id},
                        {'$set': {
                            'synced': True,
                            'last_synced_at': datetime.now()
                        }}
                    )
                    
                except Exception as e:
                    logger.error(f"Error syncing sale {sale_id}: {e}")
            
            logger.info(f"✅ Synced {len(unsynced_sales)} sales to cloud")
            
        except Exception as e:
            logger.error(f"❌ Error syncing sales: {e}")
    
    def _sync_stock_updates_to_cloud(self):
        """Sync stock updates to cloud"""
        try:
            local_products = db_service.get_local_collection('products')
            cloud_products = db_service.get_cloud_collection('products')
            
            if not cloud_products:
                return
            
            # Find products with local changes
            changed_products = list(local_products.find({
                'has_local_changes': True
            }))
            
            for product in changed_products:
                try:
                    product_id = product['_id']
                    
                    # Update cloud with local stock values
                    cloud_products.update_one(
                        {'_id': product_id},
                        {'$set': {
                            'stock': product.get('stock'),
                            'total_stock': product.get('total_stock'),
                            'updated_at': datetime.now()
                        }}
                    )
                    
                    # Mark as synced in local
                    local_products.update_one(
                        {'_id': product_id},
                        {'$set': {
                            'has_local_changes': False,
                            'last_synced_at': datetime.now()
                        }}
                    )
                    
                except Exception as e:
                    logger.error(f"Error syncing stock for product {product_id}: {e}")
            
            logger.info(f"✅ Synced stock updates for {len(changed_products)} products")
            
        except Exception as e:
            logger.error(f"❌ Error syncing stock updates: {e}")
    
    def _sync_shifts_to_cloud(self):
        """Sync shift data to cloud"""
        try:
            local_shifts = db_service.get_local_collection('shifts')
            cloud_shifts = db_service.get_cloud_collection('shifts')
            
            if not cloud_shifts:
                return
            
            # Find unsynced shifts
            unsynced_shifts = list(local_shifts.find({
                '$or': [
                    {'synced': {'$exists': False}},
                    {'synced': False}
                ]
            }))
            
            for shift in unsynced_shifts:
                try:
                    shift_id = shift['_id']
                    
                    # Insert or update in cloud
                    cloud_shifts.replace_one(
                        {'_id': shift_id},
                        shift,
                        upsert=True
                    )
                    
                    # Mark as synced in local
                    local_shifts.update_one(
                        {'_id': shift_id},
                        {'$set': {
                            'synced': True,
                            'last_synced_at': datetime.now()
                        }}
                    )
                    
                except Exception as e:
                    logger.error(f"Error syncing shift {shift_id}: {e}")
            
            logger.info(f"✅ Synced {len(unsynced_shifts)} shifts to cloud")
            
        except Exception as e:
            logger.error(f"❌ Error syncing shifts: {e}")

# Global sync service instance
sync_service = SyncService()