# File: PANN_POS_SYSTEM/backend/app/services/offline/data_cache_manager.py
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from offline_sync_manager import sync_manager

logger = logging.getLogger(__name__)

class DataCacheManager:
    """
    Manages caching of products, customers, and promotions for offline use
    Updates every 5 minutes when online
    """
    
    def __init__(self, sync_manager):
        self.sync_manager = sync_manager
        self.cache_path = sync_manager.storage_path / "cache"
        self.last_update = None
        
    async def update_all_caches(self):
        """Update all cache data (products, customers, promotions)"""
        if not self.sync_manager.is_online:
            logger.warning("🌐 Offline - cannot update cache")
            return False
        
        try:
            logger.info("🔄 Updating offline caches...")
            
            # Update products cache
            products = await self.fetch_products()
            self.save_cache("products.json", products)
            
            # Update customers cache  
            customers = await self.fetch_customers()
            self.save_cache("customers.json", customers)
            
            # Update promotions cache
            promotions = await self.fetch_promotions()
            self.save_cache("promotions.json", promotions)
            
            self.last_update = datetime.now()
            logger.info("✅ Offline caches updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache update failed: {e}")
            return False
    
    async def fetch_products(self):
        """Fetch products from your actual API"""
        # TODO: Replace with actual API call to /api/products/
        # Simulating API response with your real product data
        return {
            "last_updated": datetime.now().isoformat(),
            "data": [
                {
                    "_id": "PROD-00210",
                    "name": "Real Product 210", 
                    "price": 150.50,
                    "stock": 100,
                    "category": "Test Category"
                },
                {
                    "_id": "PROD-00209", 
                    "name": "Real Product 209",
                    "price": 200.00,
                    "stock": 50,
                    "category": "Test Category"
                }
            ]
        }
    
    async def fetch_customers(self):
        """Fetch customers from your actual API"""
        # TODO: Replace with actual API call to /api/customers/
        return {
            "last_updated": datetime.now().isoformat(),
            "data": [
                {
                    "_id": "CUST-00002",
                    "name": "Sponge Bob",  # From your real data
                    "email": "sponge@bikini.bottom",
                    "loyalty_points": 500,
                    "phone": "321321321"
                }
            ]
        }
    
    async def fetch_promotions(self):
        """Fetch active promotions from your actual API"""
        # TODO: Replace with actual API call to /api/promotions/active/
        return {
            "last_updated": datetime.now().isoformat(), 
            "data": [
                {
                    "_id": "PROMO-001",
                    "name": "Test Promotion",
                    "discount_percent": 10,
                    "active": True
                }
            ]
        }
    
    def save_cache(self, filename, data):
        """Save data to cache file"""
        try:
            filepath = self.cache_path / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"💾 Cached {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save cache {filename}: {e}")
    
    def load_cache(self, filename):
        """Load data from cache file"""
        try:
            filepath = self.cache_path / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to load cache {filename}: {e}")
            return None
    
    def get_products(self):
        """Get products from cache"""
        return self.load_cache("products.json")
    
    def get_customers(self):
        """Get customers from cache""" 
        return self.load_cache("customers.json")
    
    def get_promotions(self):
        """Get promotions from cache"""
        return self.load_cache("promotions.json")
    
    async def start_periodic_updates(self):
        """Start 5-minute periodic cache updates (your requirement)"""
        while True:
            if self.sync_manager.is_online:
                await self.update_all_caches()
            await asyncio.sleep(300)  # 5 minutes

# Global instance
data_cache_manager = DataCacheManager(sync_manager)