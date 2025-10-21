# File: backend/services/offline/offline_integration.py
import logging
from datetime import datetime
import offline_pos_service

logger = logging.getLogger(__name__)

class OfflineIntegrationBridge:
    """
    Bridge between file-based offline system and your existing MongoDB services
    """
    
    def __init__(self, offline_service, original_pos_service=None, original_online_service=None):
        self.offline = offline_service
        self.original_pos = original_pos_service
        self.original_online = original_online_service
    
    async def create_sale(self, sale_data, cashier_id):
        """
        Unified sale creation - tries online first, falls back to offline
        """
        # First try original service if online
        if self.offline.sync_manager.is_online and self.original_pos:
            try:
                result = self.original_pos.create_sale(sale_data, cashier_id)
                if result.get("success"):
                    logger.info("✅ Sale created online successfully")
                    return result
            except Exception as e:
                logger.warning(f"Online sale failed, falling back to offline: {e}")
        
        # Fall back to offline
        logger.info("🔄 Using offline sale service")
        return await self.offline.create_sale_offline(sale_data, cashier_id)
    
    async def create_online_order(self, order_data, customer_id):
        """
        Unified online order creation
        """
        if self.offline.sync_manager.is_online and self.original_online:
            try:
                # Call your existing online order service
                result = self.original_online.create_online_order(order_data, customer_id)
                if result.get("success"):
                    return result
            except Exception as e:
                logger.warning(f"Online order service failed: {e}")
        
        # Use offline storage
        return await self.offline.create_online_order_offline(order_data, customer_id)
    
    def get_system_status(self):
        """Get combined online/offline system status"""
        offline_status = self.offline.get_offline_sales_status()
        
        return {
            "online_mode": self.offline.sync_manager.is_online,
            "offline_transactions_pending": offline_status["total_pending"],
            "pending_sales": offline_status["pending_sales_count"],
            "pending_orders": offline_status["pending_orders_count"],
            "storage_path": self.offline.sync_manager.storage_path,
            "timestamp": datetime.now().isoformat()
        }

# Create bridge instance
offline_bridge = OfflineIntegrationBridge(offline_pos_service)