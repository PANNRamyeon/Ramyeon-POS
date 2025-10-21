from offline_sync_manager import sync_manager
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

class OfflinePOSSalesService:
    """
    REFACTORED: POS service with file-based offline capability
    No longer extends POSSalesService - standalone offline service
    """
    
    def __init__(self):
        self.sync_manager = sync_manager
    
    async def create_sale_offline(self, sale_data, cashier_id):
        """
        REFACTORED: Create sale with file-based offline storage
        """
        try:
            # Add offline metadata
            sale_data["_offline_created"] = True
            sale_data["cashier_id"] = cashier_id
            sale_data["created_at"] = sale_data.get("created_at") or datetime.utcnow().isoformat()
            
            # ✅ YOUR REQUIREMENT #1: Cache points but don't use offline
            if sale_data.get("loyalty_points_used", 0) > 0:
                logger.warning("⚠️ Points usage detected in offline mode - caching but not applying")
                sale_data["_points_pending_sync"] = True
                # Store the points data but don't deduct from local cache
                points_data = {
                    "customer_id": sale_data.get("customer_id"),
                    "points_used": sale_data.get("loyalty_points_used", 0),
                    "points_earned": sale_data.get("loyalty_points_earned", 0),
                    "sale_timestamp": sale_data["created_at"]
                }
                # Save points transaction separately
                self.sync_manager.save_offline_transaction("points_update", points_data)
            
            # ✅ YOUR REQUIREMENT #2: Sales write during offline
            # Save to file storage
            result = self.sync_manager.save_offline_transaction(
                transaction_type="pos_sale",
                data=sale_data
            )
            
            if not result["success"]:
                return result
            
            # ✅ YOUR REQUIREMENT #3: Try immediate sync if online
            if self.sync_manager.is_online:
                try:
                    sync_result = await self.sync_manager.sync_pending_files()
                    if sync_result["synced_count"] > 0:
                        return {
                            "success": True,
                            "message": "Sale created and synced immediately",
                            "file_id": result["file_id"],
                            "synced": True,
                            "offline_mode": False
                        }
                except Exception as e:
                    logger.warning(f"Immediate sync failed, sale saved offline: {e}")
            
            return {
                "success": True,
                "message": "Sale saved offline - will sync when connection restored",
                "file_id": result["file_id"],
                "synced": False,
                "offline_mode": True,
                "points_pending": sale_data.get("_points_pending_sync", False)
            }
            
        except Exception as e:
            logger.error(f"❌ Offline sale creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_online_order_offline(self, order_data, customer_id):
        """
        Handle online orders during offline mode
        """
        try:
            order_data["_offline_created"] = True
            order_data["customer_id"] = customer_id
            order_data["created_at"] = datetime.utcnow().isoformat()
            order_data["status"] = "pending_sync"
            
            # Save online order to offline storage
            result = self.sync_manager.save_offline_transaction(
                transaction_type="online_order",
                data=order_data
            )
            
            if not result["success"]:
                return result
            
            # Try immediate sync if online
            if self.sync_manager.is_online:
                try:
                    await self.sync_manager.sync_pending_files()
                except Exception as e:
                    logger.warning(f"Immediate online order sync failed: {e}")
            
            return {
                "success": True,
                "message": "Online order saved offline",
                "file_id": result["file_id"],
                "synced": self.sync_manager.is_online,
                "offline_mode": not self.sync_manager.is_online
            }
            
        except Exception as e:
            logger.error(f"❌ Offline online order creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_offline_sales_status(self):
        """Get status of offline sales files"""
        pending_sales = self.sync_manager.get_pending_files("pos_sale")
        pending_orders = self.sync_manager.get_pending_files("online_order")
        
        return {
            "is_online": self.sync_manager.is_online,
            "pending_sales_count": len(pending_sales),
            "pending_orders_count": len(pending_orders),
            "pending_sales": [f.name for f in pending_sales],
            "pending_orders": [f.name for f in pending_orders],
            "total_pending": len(pending_sales) + len(pending_orders)
        }
    
    def get_offline_transactions(self, limit=50):
        """Get recent offline transactions for display"""
        try:
            all_pending = self.sync_manager.get_pending_files()
            transactions = []
            
            for filepath in all_pending[:limit]:
                transaction_data = self.sync_manager.read_transaction_file(filepath)
                if transaction_data:
                    transactions.append({
                        "file_id": transaction_data["_metadata"]["file_id"],
                        "type": transaction_data["_metadata"]["type"],
                        "created_at": transaction_data["_metadata"]["created_at"],
                        "status": transaction_data["_metadata"]["sync_status"],
                        "data_preview": {
                            "items_count": len(transaction_data["data"].get("items", [])),
                            "total_amount": transaction_data["data"].get("total_amount", 0),
                            "customer_id": transaction_data["data"].get("customer_id")
                        }
                    })
            
            return transactions
            
        except Exception as e:
            logger.error(f"❌ Failed to get offline transactions: {e}")
            return []
    
    async def manual_sync_trigger(self):
        """
        Manual sync trigger for users or system events
        """
        try:
            if not self.sync_manager.is_online:
                return {
                    "success": False,
                    "message": "Cannot sync - no internet connection",
                    "offline_mode": True
                }
            
            sync_result = await self.sync_manager.sync_pending_files()
            
            return {
                "success": sync_result["success"],
                "message": f"Manual sync completed: {sync_result['synced_count']} files synced",
                "synced_count": sync_result["synced_count"],
                "failed_count": sync_result["failed_count"],
                "offline_mode": False
            }
            
        except Exception as e:
            logger.error(f"❌ Manual sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    def update_connection_status(self, is_online):
        """
        Update internet connection status and trigger auto-sync if coming online
        """
        previous_status = self.sync_manager.is_online
        self.sync_manager.is_online = is_online
        
        # If we just came online, trigger sync
        if is_online and not previous_status:
            logger.info("🌐 Internet connection restored - triggering auto-sync")
            asyncio.create_task(self.auto_sync_on_reconnect())
        
        return {
            "previous_status": previous_status,
            "current_status": is_online,
            "auto_sync_triggered": is_online and not previous_status
        }
    
    async def auto_sync_on_reconnect(self):
        """Auto-sync when internet connection is restored"""
        try:
            # Small delay to ensure stable connection
            await asyncio.sleep(2)
            
            sync_result = await self.sync_manager.sync_pending_files()
            
            if sync_result["synced_count"] > 0:
                logger.info(f"✅ Auto-sync completed: {sync_result['synced_count']} files synced")
            else:
                logger.info("ℹ️ Auto-sync: No files to sync or sync failed")
                
        except Exception as e:
            logger.error(f"❌ Auto-sync failed: {e}")

# Service instance for import
offline_pos_service = OfflinePOSSalesService()