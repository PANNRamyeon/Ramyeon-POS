from datetime import datetime
from ...database import db_manager
import logging
from ..POS.batch_service import BatchService

logger = logging.getLogger(__name__)

class POSCategoryService:
    """Lightweight service optimized specifically for POS operations"""
    
    def __init__(self):
        self.db = db_manager.get_database()
        self.category_collection = self.db.category
        self.product_collection = self.db.products
        self.batches_collection = self.db.batches
        self.batch_service = BatchService() 
        self._ensure_pos_indexes()

    def _ensure_pos_indexes(self):
        """Create indexes specifically optimized for POS operations"""
        try:
            # Essential POS indexes for string IDs
            pos_indexes = [
                # For category catalog loading
                [("status", 1), ("isDeleted", 1)],
                [("category_name", 1)],
                [("category_id", 1)],  # String-based category ID index
                
                # For subcategory product lookups
                [("sub_categories.products.product_id", 1)],
                [("sub_categories.name", 1)]
            ]
            
            for index_fields in pos_indexes:
                self.category_collection.create_index(index_fields, background=True)
            
            # Product collection indexes for string IDs
            product_indexes = [
                [("product_id", 1)],  # String-based product ID
                [("product_name", 1)],
                [("stock_quantity", 1)],
                [("barcode", 1)],
                [("product_code", 1)]
            ]
            
            for index_fields in product_indexes:
                self.product_collection.create_index(index_fields, background=True)
                
            logger.info("POS indexes created successfully")
        except Exception as e:
            logger.warning(f"Could not create POS indexes: {e}")

    def get_pos_catalog_structure(self):
        """
        Get lightweight catalog structure for POS display
        Returns active categories with subcategories and basic product info
        """
        try:
            categories = list(self.category_collection.find(
                {
                    "status": "active",
                    "isDeleted": {"$ne": True}
                },
                {
                    "category_id": 1,  # String ID
                    "category_name": 1,
                    "sub_categories.name": 1,
                    "sub_categories.products.product_id": 1,  # String product ID
                    "sub_categories.products.product_name": 1
                }
            ).sort("category_name", 1))
            
            return categories
            
        except Exception as e:
            logger.error(f"POS catalog structure failed: {e}")
            raise Exception(f"Failed to get POS catalog: {str(e)}")

    def get_products_for_pos_cart(self, product_ids):
        """
        Batch fetch multiple products for POS cart operations
        Optimized for speed with only essential cart fields
        """
        try:
            if not product_ids or not isinstance(product_ids, list):
                raise ValueError("product_ids must be a non-empty list")
            
            # ✅ No validation needed - accept product IDs as-is
            valid_ids = [str(pid).strip() for pid in product_ids if pid]
            
            if not valid_ids:
                raise ValueError("No valid product IDs provided")
            
            # ✅ Query using '_id' field (not 'product_id')
            products = list(self.product_collection.find(
                {'_id': {'$in': valid_ids}},  # ✅ CHANGED FROM 'product_id' to '_id'
                {
                    '_id': 1,
                    'product_name': 1,
                    'selling_price': 1,  # ✅ Your collection uses 'selling_price'
                    'total_stock': 1,
                    'SKU': 1,
                    'barcode': 1,
                    'category_id': 1,
                    'subcategory_name': 1,
                    'is_taxable': 1,
                    'image_url': 1,
                    'description': 1,
                    'unit': 1,
                    'status': 1
                }
            ))
            
            if not products:
                return []
            
            # ✅ Transform to standardized format
            pos_products = []
            for product in products:
                product_id = product['_id']
                
                # Calculate batch stock
                batch_stock = self._calculate_batch_stock(product_id)
                batch_details = self._get_batch_details(product_id)
                
                pos_product = {
                    '_id': product['_id'],
                    'id': product['_id'],
                    'product_id': product['_id'],
                    'product_name': product.get('product_name', 'Unknown'),
                    'name': product.get('product_name', 'Unknown'),
                    'selling_price': product.get('selling_price', 0),
                    'price': product.get('selling_price', 0),
                    
                    # ✅ Use batch stock
                    'total_stock': batch_stock,
                    'stock_quantity': batch_stock,
                    'batch_stock': batch_stock,
                    
                    'batches_count': batch_details['batches_count'],
                    'oldest_expiry': batch_details['oldest_expiry'],
                    
                    # ... other fields ...
                }
                
                pos_products.append(pos_product)
            
            return pos_products
            
        except Exception as e:
            logger.error(f"Error in get_products_for_pos_cart: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_products_by_subcategory_for_pos(self, category_id, subcategory_name):
        """Get all products in a subcategory with batch stock"""
        try:
            if not category_id:
                raise ValueError("Invalid category ID")
            
            # Get category and product IDs
            category = self.category_collection.find_one({
                '_id': category_id,
                'status': 'active',
                'isDeleted': {'$ne': True}
            }, {'sub_categories': 1})
            
            if not category:
                return []
            
            # Find subcategory products
            product_ids = []
            for subcategory in category.get('sub_categories', []):
                if subcategory['name'] == subcategory_name:
                    products = subcategory.get('products', [])
                    if products and isinstance(products[0], dict):
                        product_ids = [p['product_id'] for p in products]
                    break
            
            if not product_ids:
                return []
            
            # ✅ Use the method that calculates batch stock
            return self.get_products_for_pos_cart(product_ids)
            
        except Exception as e:
            logger.error(f"POS subcategory products fetch failed: {e}")
            raise Exception(f"Failed to get subcategory products: {str(e)}")

    def get_product_by_barcode_for_pos(self, barcode):
        """Quick product lookup by barcode with batch stock"""
        try:
            if not barcode or not barcode.strip():
                raise ValueError("Barcode is required")
            
            # Find product by barcode
            product = self.product_collection.find_one(
                {'barcode': barcode.strip()},
                {'_id': 1}
            )
            
            if not product:
                return None
            
            # ✅ Get full product data with batch stock
            products = self.get_products_for_pos_cart([product['_id']])
            
            return products[0] if products else None
            
        except Exception as e:
            logger.error(f"POS barcode lookup failed: {e}")
            raise Exception(f"Failed to get product by barcode: {str(e)}")

    def search_products_for_pos(self, search_term, limit=20):
        """Quick product search for POS with batch stock"""
        try:
            if not search_term or not search_term.strip():
                return []
            
            search_term = search_term.strip()
            regex_pattern = {'$regex': search_term, '$options': 'i'}
            
            # Find matching products
            products = list(self.product_collection.find(
                {
                    '$or': [
                        {'product_name': regex_pattern},
                        {'SKU': regex_pattern}
                    ]
                },
                {'_id': 1}
            ).limit(limit))
            
            if not products:
                return []
            
            # Get product IDs
            product_ids = [p['_id'] for p in products]
            
            # ✅ Use the method that calculates batch stock
            return self.get_products_for_pos_cart(product_ids)
            
        except Exception as e:
            logger.error(f"POS product search failed: {e}")
            raise Exception(f"Failed to search products: {str(e)}")

    def check_product_stock_for_pos(self, product_id, requested_quantity):
        """Quick stock check for POS before adding to cart"""
        try:
            if not product_id:
                return {'available': False, 'error': 'Invalid product ID'}
            
            # ✅ Use '_id' instead of 'product_id'
            product = self.product_collection.find_one(
                {'_id': product_id},
                {'total_stock': 1, 'product_name': 1}
            )
            
            if not product:
                return {'available': False, 'error': 'Product not found'}
            
            current_stock = product.get('total_stock', 0)
            
            return {
                'available': current_stock >= requested_quantity,
                'current_stock': current_stock,
                'requested_quantity': requested_quantity,
                'product_name': product.get('product_name', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"POS stock check failed: {e}")
            return {'available': False, 'error': str(e)}

    def get_low_stock_products_for_pos(self, threshold=10):
        """Get products with low stock for POS alerts"""
        try:
            products = list(self.product_collection.find(
                {'total_stock': {'$lte': threshold}},
                {
                    '_id': 1,
                    'product_name': 1,
                    'total_stock': 1,
                    'SKU': 1
                }
            ).sort('total_stock', 1).limit(50))
            
            return products
            
        except Exception as e:
            logger.error(f"POS low stock check failed: {e}")
            raise Exception(f"Failed to get low stock products: {str(e)}")

    def get_category_products_for_pos_display(self, category_id):
        """
        Get all products in a category organized by subcategory for POS display
        """
        try:
            if not category_id or not category_id.startswith('CTGY-'):
                raise ValueError("Invalid category ID - must be CTGY-### format")
            
            category = self.category_collection.find_one(
                {
                    'category_id': category_id,  # String ID
                    'status': 'active',
                    'isDeleted': {'$ne': True}
                }
            )
            
            if not category:
                return {
                    'category_id': category_id,
                    'category_name': 'Unknown',
                    'subcategories': []
                }
            
            subcategories_data = []
            
            for subcategory in category.get('sub_categories', []):
                products_data = []
                products = subcategory.get('products', [])
                
                # Get product IDs from combined format
                if products and isinstance(products[0], dict):
                    product_ids = [p['product_id'] for p in products]  # String IDs
                    
                    # Fetch full product details for POS
                    full_products = self.get_products_for_pos_cart(product_ids)
                    products_data = full_products
                
                subcategories_data.append({
                    'name': subcategory['name'],
                    'description': subcategory.get('description', ''),
                    'product_count': len(products_data),
                    'products': products_data
                })
            
            return {
                'category_id': category['category_id'],
                'category_name': category['category_name'],
                'description': category.get('description', ''),
                'subcategories': subcategories_data
            }
            
        except Exception as e:
            logger.error(f"POS category products display failed: {e}")
            raise Exception(f"Failed to get category products for POS: {str(e)}")

    def get_pos_quick_access_products(self, limit=20):
        """
        Get frequently sold or featured products for quick access in POS
        """
        try:
            # For now, return products with high stock or featured status
            # Could be enhanced with sales frequency data later
            products = list(self.product_collection.find(
                {
                    'total_stock': {'$gt': 0},  # Only in-stock items
                    '$or': [
                        {'is_featured': True},
                        {'total_stock': {'$gte': 50}}  # High stock items
                    ]
                },
                {
                    'product_id': 1,  # String ID
                    'product_name': 1,
                    'unit_price': 1,
                    'total_stock': 1,
                    'product_code': 1,
                    'barcode': 1,
                    'category_id': 1,  # String category ID
                    'subcategory_name': 1
                }
            ).limit(limit))
            
            return products
            
        except Exception as e:
            logger.error(f"POS quick access products failed: {e}")
            raise Exception(f"Failed to get quick access products: {str(e)}")
    
    def get_products_by_category_for_pos(self, category_id):
        """
        Get all products in a category with real-time batch stock
        """
        try:
            # Verify category exists
            category = self.category_collection.find_one({
                '_id': category_id,
                'is_deleted': False
            })
            
            if not category:
                raise ValueError(f"Category {category_id} not found")
            
            # Get all products in this category
            query = {
                'category_id': category_id,
                'is_deleted': False
            }
            
            products = list(self.product_collection.find(query).sort('product_name', 1))
            
            if not products:
                return []
            
            # ✅ Calculate batch stock for each product
            pos_products = []
            for product in products:
                product_id = product['_id']
                
                # Get batch availability
                batch_info = self.batch_service.check_batch_availability(product_id, 0)
                
                pos_products.append({
                    'product_id': product_id,
                    '_id': product_id,
                    'id': product_id,
                    'name': product.get('product_name'),
                    'product_name': product.get('product_name'),
                    'price': product.get('selling_price', 0),
                    'selling_price': product.get('selling_price', 0),
                    
                    # ✅ Use batch stock
                    'total_stock': batch_info['total_stock'],
                    'stock_quantity': batch_info['total_stock'],
                    'batch_stock': batch_info['total_stock'],
                    'batches_count': batch_info['batches_count'],
                    'oldest_expiry': batch_info.get('oldest_batch', {}).get('expiry_date'),
                    
                    'category_id': product.get('category_id'),
                    'subcategory': product.get('subcategory'),
                    'barcode': product.get('barcode'),
                    'SKU': product.get('SKU'),
                    'sku': product.get('SKU'),
                    'unit': product.get('unit', 'pcs'),
                    'image_url': product.get('image_url'),
                    'description': product.get('description', '')
                })
            
            return pos_products
            
        except ValueError as e:
            raise
        except Exception as e:
            raise Exception(f"Error fetching products by category: {str(e)}")

    def _calculate_batch_stock(self, product_id):
        """Calculate total available stock from active batches"""
        try:
            # Get all active batches
            batches = list(self.batches_collection.find({
                'product_id': product_id,
                'status': 'active',
                'quantity_remaining': {'$gt': 0}
            }))
            
            total_stock = 0
            for batch in batches:
                batch_qty = batch.get('quantity_remaining', 0)
                total_stock += batch_qty
            
            return total_stock
            
        except Exception as e:
            logger.error(f"Error calculating batch stock for {product_id}: {e}")
            return 0

    def _get_batch_details(self, product_id):
        """
        Get batch details for a product (for display/debugging)
        
        Returns:
            {
                'total_stock': int,
                'batches_count': int,
                'oldest_expiry': datetime or None
            }
        """
        try:
            batches = list(self.batches_collection.find({
                'product_id': product_id,
                'status': 'active',
                'quantity_remaining': {'$gt': 0}
            }).sort('expiry_date', 1))
            
            total_stock = sum(b.get('quantity_remaining', 0) for b in batches)
            oldest_expiry = batches[0].get('expiry_date') if batches else None
            
            return {
                'total_stock': total_stock,
                'batches_count': len(batches),
                'oldest_expiry': oldest_expiry
            }
            
        except Exception as e:
            logger.error(f"Error getting batch details: {e}")
            return {
                'total_stock': 0,
                'batches_count': 0,
                'oldest_expiry': None
            }
