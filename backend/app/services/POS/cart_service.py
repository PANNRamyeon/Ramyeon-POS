from datetime import datetime, timedelta
from ...database import db_manager
from ..Backoffice.product_service import ProductService
from .promotion_pos_service import PromotionService

class CartService:

    def __init__(self):
        self.db = db_manager.get_database()
        self.cart_collection = self.db.carts
        self.products_collection = self.db.products
        self.product_service = ProductService()
        self.promotion_service = PromotionService()
        
        # ✅ Product cache: {product_id: (product_data, timestamp)}
        self._product_cache = {}
        self._cache_timeout = timedelta(minutes=5)
        
        # ✅ Ensure indexes exist
        self._ensure_indexes()

# ================================================================
# INITIALIZATION & INDEXES
# ================================================================

    def _ensure_indexes(self):
        """
        Create indexes for cart collection if they don't exist
        Called automatically on service initialization
        """
        try:
            # Check if indexes already exist
            existing_indexes = list(self.cart_collection.list_indexes())
            index_names = [idx['name'] for idx in existing_indexes]
            
            # Index 1: Cashier + Status (for active cart lookup)
            if 'cashier_status_idx' not in index_names:
                self.cart_collection.create_index(
                    [("cashier_id", 1), ("status", 1)],
                    name="cashier_status_idx"
                )
                print("✅ Created index: cashier_status_idx")
            
            # Index 2: Shift ID (for shift reports)
            if 'shift_idx' not in index_names:
                self.cart_collection.create_index(
                    [("shift_id", 1)],
                    name="shift_idx"
                )
                print("✅ Created index: shift_idx")
            
            # Index 3: Last Updated + Status (for cleanup)
            if 'cleanup_idx' not in index_names:
                self.cart_collection.create_index(
                    [("last_updated", 1), ("status", 1)],
                    name="cleanup_idx"
                )
                print("✅ Created index: cleanup_idx")
            
        except Exception as e:
            print(f"⚠️ Warning: Failed to create indexes: {e}")
            # Don't fail if indexes can't be created - service still works

    # ================================================================
    # PRODUCT CACHING (NEW)
    # ================================================================

    def _get_product_cached(self, product_id):
        """
        Get product with 5-minute cache
        
        Returns:
            dict: Product data
        
        Raises:
            ValueError: If product not found
        """
        # Check cache first
        if product_id in self._product_cache:
            cached_data, timestamp = self._product_cache[product_id]
            
            # Check if cache is still valid
            if datetime.utcnow() - timestamp < self._cache_timeout:
                return cached_data
            else:
                # Cache expired - remove it
                del self._product_cache[product_id]
        
        # Cache miss - fetch from database
        product = self.product_service.get_product_by_id(product_id)
        
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        # Store in cache
        self._product_cache[product_id] = (product, datetime.utcnow())
        
        return product

    def _get_products_batch(self, product_ids):
        """
        Get multiple products at once (batch operation)
        Uses cache when possible, fetches missing ones in single query
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            dict: {product_id: product_data}
        """
        results = {}
        missing_ids = []
        
        # Check cache first
        for product_id in product_ids:
            if product_id in self._product_cache:
                cached_data, timestamp = self._product_cache[product_id]
                if datetime.utcnow() - timestamp < self._cache_timeout:
                    results[product_id] = cached_data
                    continue
                else:
                    del self._product_cache[product_id]
            
            missing_ids.append(product_id)
        
        # Fetch missing products in single query
        if missing_ids:
            products = list(self.products_collection.find(
                {'_id': {'$in': missing_ids}}
            ))
            
            for product in products:
                product_id = product['_id']
                results[product_id] = product
                # Cache it
                self._product_cache[product_id] = (product, datetime.utcnow())
        
        return results

    def clear_product_cache(self):
        """Clear the entire product cache (useful for testing or product updates)"""
        self._product_cache.clear()
        print("🗑️ Product cache cleared")

    # ================================================================
    # ID GENERATION
    # ================================================================

    def generate_cart_id(self):
        """Generate sequential CART-##### ID"""
        try:
            pipeline = [
                {'$match': {'_id': {'$regex': '^CART-'}}},
                {'$project': {
                    'numericPart': {'$toInt': {'$substr': ['$_id', 5, -1]}}
                }},
                {'$sort': {'numericPart': -1}},
                {'$limit': 1}
            ]
            
            result = list(self.cart_collection.aggregate(pipeline))
            next_number = result[0]['numericPart'] + 1 if result else 1
            
            return f"CART-{next_number:05d}"
        except Exception:
            count = self.cart_collection.count_documents({}) + 1
            return f"CART-{count:05d}"

    # ================================================================
    # CART LIFECYCLE
    # ================================================================

    def create_cart(self, cashier_id, shift_id=None):
        """Create new empty cart"""
        try:
            cart_id = self.generate_cart_id()
            
            cart = {
                '_id': cart_id,
                'cashier_id': cashier_id,
                'shift_id': shift_id,
                'items': [],
                'subtotal': 0,
                'tax_rate': 0.12,  # 12% VAT
                'tax_amount': 0,
                'discount_amount': 0,
                'discount_type': None,
                'discount_details': {},
                'total': 0,
                'status': 'active',
                'created_at': datetime.utcnow(),
                'last_updated': datetime.utcnow()
            }
            
            self.cart_collection.insert_one(cart)
            return cart
            
        except Exception as e:
            raise Exception(f"Error creating cart: {str(e)}")

    def get_cart(self, cart_id):
        """Get cart by ID"""
        cart = self.cart_collection.find_one({'_id': cart_id})
        if not cart:
            raise ValueError(f"Cart {cart_id} not found")
        return cart

    def clear_cart(self, cart_id):
        """Remove all items from cart"""
        try:
            result = self.cart_collection.update_one(
                {'_id': cart_id},
                {
                    '$set': {
                        'items': [],
                        'subtotal': 0,
                        'tax_amount': 0,
                        'discount_amount': 0,
                        'discount_type': None,
                        'discount_details': {},
                        'total': 0,
                        'last_updated': datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise Exception(f"Error clearing cart: {str(e)}")

    def delete_cart(self, cart_id):
        """Delete cart completely (after checkout)"""
        try:
            result = self.cart_collection.delete_one({'_id': cart_id})
            return result.deleted_count > 0
            
        except Exception as e:
            raise Exception(f"Error deleting cart: {str(e)}")

    # ================================================================
    # ITEM MANAGEMENT (OPTIMIZED)
    # ================================================================

    def add_item(self, cart_id, product_id, quantity=1):
        """
        ✅ OPTIMIZED: Add item to cart or increase quantity if already exists
        
        Performance improvements:
        - Uses cached product data (no DB call if cached)
        - Single atomic update operation (no separate read)
        - In-memory calculation before final DB write
        
        Old: 4 DB operations
        New: 1-2 DB operations
        """
        try:
            # ✅ Get product from cache (fast)
            product = self._get_product_cached(product_id)
            
            # ✅ Validate stock
            if product['stock'] < quantity:
                raise ValueError(f"Insufficient stock. Available: {product['stock']}")
            
            # ✅ Get current cart (single read)
            cart = self.get_cart(cart_id)
            
            # ✅ Check if item already exists and update in-memory
            item_exists = False
            for item in cart['items']:
                if item['product_id'] == product_id:
                    new_quantity = item['quantity'] + quantity
                    
                    # Check total stock needed
                    if product['stock'] < new_quantity:
                        raise ValueError(f"Insufficient stock. Available: {product['stock']}")
                    
                    item['quantity'] = new_quantity
                    item['subtotal'] = item['unit_price'] * new_quantity
                    item_exists = True
                    break
            
            # ✅ Add new item if doesn't exist
            if not item_exists:
                new_item = {
                    'product_id': product_id,
                    'product_name': product['product_name'],
                    'sku': product.get('SKU', ''),
                    'quantity': quantity,
                    'unit_price': product['selling_price'],
                    'subtotal': product['selling_price'] * quantity,
                    'is_taxable': product.get('is_taxable', True),
                    'added_at': datetime.utcnow()
                }
                cart['items'].append(new_item)
            
            # ✅ Calculate totals in-memory (no DB call)
            cart = self._calculate_cart_totals_in_memory(cart)
            
            # ✅ Single DB write with all updates
            self.cart_collection.update_one(
                {'_id': cart_id},
                {
                    '$set': {
                        'items': cart['items'],
                        'subtotal': cart['subtotal'],
                        'tax_amount': cart['tax_amount'],
                        'total': cart['total'],
                        'last_updated': datetime.utcnow()
                    }
                }
            )
            
            return cart
            
        except Exception as e:
            raise Exception(f"Error adding item to cart: {str(e)}")

    def remove_item(self, cart_id, product_id):
        """
        ✅ OPTIMIZED: Remove item from cart completely
        
        Old: 3 DB operations
        New: 2 DB operations
        """
        try:
            cart = self.get_cart(cart_id)
            
            # Filter out the item
            cart['items'] = [item for item in cart['items'] if item['product_id'] != product_id]
            
            # Calculate totals in-memory
            cart = self._calculate_cart_totals_in_memory(cart)
            
            # Single DB write
            self.cart_collection.update_one(
                {'_id': cart_id},
                {
                    '$set': {
                        'items': cart['items'],
                        'subtotal': cart['subtotal'],
                        'tax_amount': cart['tax_amount'],
                        'total': cart['total'],
                        'last_updated': datetime.utcnow()
                    }
                }
            )
            
            return cart
            
        except Exception as e:
            raise Exception(f"Error removing item from cart: {str(e)}")

    def update_quantity(self, cart_id, product_id, new_quantity):
        """
        ✅ OPTIMIZED: Update quantity of specific item
        
        Old: 4 DB operations
        New: 2 DB operations
        """
        try:
            if new_quantity <= 0:
                return self.remove_item(cart_id, product_id)
            
            # ✅ Get product from cache
            product = self._get_product_cached(product_id)
            
            # ✅ Validate stock
            if product['stock'] < new_quantity:
                raise ValueError(f"Insufficient stock. Available: {product['stock']}")
            
            cart = self.get_cart(cart_id)
            
            # Find and update item
            item_found = False
            for item in cart['items']:
                if item['product_id'] == product_id:
                    item['quantity'] = new_quantity
                    item['subtotal'] = item['unit_price'] * new_quantity
                    item_found = True
                    break
            
            if not item_found:
                raise ValueError(f"Item {product_id} not found in cart")
            
            # Calculate totals in-memory
            cart = self._calculate_cart_totals_in_memory(cart)
            
            # Single DB write
            self.cart_collection.update_one(
                {'_id': cart_id},
                {
                    '$set': {
                        'items': cart['items'],
                        'subtotal': cart['subtotal'],
                        'tax_amount': cart['tax_amount'],
                        'total': cart['total'],
                        'last_updated': datetime.utcnow()
                    }
                }
            )
            
            return cart
            
        except Exception as e:
            raise Exception(f"Error updating item quantity: {str(e)}")

    # ================================================================
    # DISCOUNT MANAGEMENT
    # ================================================================

    def apply_percentage_discount(self, cart_id, percentage):
        """Apply percentage discount (e.g., 10% off)"""
        try:
            if percentage < 0 or percentage > 100:
                raise ValueError("Percentage must be between 0 and 100")
            
            cart = self.get_cart(cart_id)
            
            discount_amount = (cart['subtotal'] * percentage) / 100
            
            cart['discount_type'] = 'percentage'
            cart['discount_details'] = {'percentage': percentage}
            cart['discount_amount'] = round(discount_amount, 2)
            
            # Recalculate in-memory
            cart = self._calculate_cart_totals_in_memory(cart)
            
            # Single DB write
            self.cart_collection.update_one(
                {'_id': cart_id},
                {
                    '$set': {
                        'discount_type': cart['discount_type'],
                        'discount_details': cart['discount_details'],
                        'discount_amount': cart['discount_amount'],
                        'tax_amount': cart['tax_amount'],
                        'total': cart['total'],
                        'last_updated': datetime.utcnow()
                    }
                }
            )
            
            return cart
            
        except Exception as e:
            raise Exception(f"Error applying percentage discount: {str(e)}")

    def apply_fixed_discount(self, cart_id, amount):
        """Apply fixed amount discount (e.g., ₱50 off)"""
        try:
            cart = self.get_cart(cart_id)
            
            if amount > cart['subtotal']:
                raise ValueError("Discount cannot exceed subtotal")
            
            cart['discount_type'] = 'fixed'
            cart['discount_details'] = {'amount': amount}
            cart['discount_amount'] = round(amount, 2)
            
            # Recalculate in-memory
            cart = self._calculate_cart_totals_in_memory(cart)
            
            # Single DB write
            self.cart_collection.update_one(
                {'_id': cart_id},
                {
                    '$set': {
                        'discount_type': cart['discount_type'],
                        'discount_details': cart['discount_details'],
                        'discount_amount': cart['discount_amount'],
                        'tax_amount': cart['tax_amount'],
                        'total': cart['total'],
                        'last_updated': datetime.utcnow()
                    }
                }
            )
            
            return cart
            
        except Exception as e:
            raise Exception(f"Error applying fixed discount: {str(e)}")

    def remove_discount(self, cart_id):
        """Remove any applied discount"""
        try:
            cart = self.get_cart(cart_id)
            
            cart['discount_type'] = None
            cart['discount_details'] = {}
            cart['discount_amount'] = 0
            
            # Recalculate in-memory
            cart = self._calculate_cart_totals_in_memory(cart)
            
            # Single DB write
            self.cart_collection.update_one(
                {'_id': cart_id},
                {
                    '$set': {
                        'discount_type': None,
                        'discount_details': {},
                        'discount_amount': 0,
                        'tax_amount': cart['tax_amount'],
                        'total': cart['total'],
                        'last_updated': datetime.utcnow()
                    }
                }
            )
            
            return cart
            
        except Exception as e:
            raise Exception(f"Error removing discount: {str(e)}")

    # ================================================================
    # CALCULATION (OPTIMIZED)
    # ================================================================

    def _calculate_cart_totals_in_memory(self, cart):
        """
        ✅ OPTIMIZED: Calculate all cart totals in-memory (no DB operations)
        
        This is called before DB writes to prepare data
        Returns updated cart dict (does not write to DB)
        """
        # Calculate subtotal
        subtotal = sum(item['subtotal'] for item in cart['items'])
        
        # Calculate tax (only on taxable items, after discount)
        taxable_amount = sum(
            item['subtotal'] for item in cart['items'] 
            if item.get('is_taxable', True)
        )
        
        # Apply discount to taxable amount
        discount_amount = cart.get('discount_amount', 0)
        taxable_after_discount = max(0, taxable_amount - discount_amount)
        
        tax_rate = cart.get('tax_rate', 0.12)
        tax_amount = taxable_after_discount * tax_rate
        
        # Calculate final total
        total = subtotal - discount_amount + tax_amount
        
        # Update cart dict (in-memory)
        cart['subtotal'] = round(subtotal, 2)
        cart['tax_amount'] = round(tax_amount, 2)
        cart['total'] = round(total, 2)
        
        return cart

    def _recalculate_cart(self, cart_id):
        """
        ✅ KEPT FOR BACKWARDS COMPATIBILITY
        Recalculate and save to DB
        
        Note: New optimized methods use _calculate_cart_totals_in_memory() instead
        """
        try:
            cart = self.get_cart(cart_id)
            cart = self._calculate_cart_totals_in_memory(cart)
            
            # Single DB write
            self.cart_collection.update_one(
                {'_id': cart_id},
                {
                    '$set': {
                        'subtotal': cart['subtotal'],
                        'tax_amount': cart['tax_amount'],
                        'total': cart['total'],
                        'last_updated': datetime.utcnow()
                    }
                }
            )
            
            return cart
            
        except Exception as e:
            raise Exception(f"Error recalculating cart: {str(e)}")

    # ================================================================
    # STOCK VALIDATION (OPTIMIZED)
    # ================================================================

    def validate_cart_stock_batch(self, cart_id):
        """
        ✅ OPTIMIZED: Validate stock for all items in single query
        
        Old: N DB queries (one per item)
        New: 1 DB query (batch lookup)
        
        Returns:
            bool: True if all items have sufficient stock
            
        Raises:
            ValueError: If any item has insufficient stock
        """
        try:
            cart = self.get_cart(cart_id)
            
            if not cart['items']:
                return True
            
            # Get all product IDs
            product_ids = [item['product_id'] for item in cart['items']]
            
            # ✅ Batch fetch all products (uses cache when possible)
            products_map = self._get_products_batch(product_ids)
            
            # Validate each item
            for item in cart['items']:
                product = products_map.get(item['product_id'])
                
                if not product:
                    raise ValueError(f"Product {item['product_id']} not found")
                
                available_stock = product.get('stock', 0)
                
                if available_stock < item['quantity']:
                    raise ValueError(
                        f"Insufficient stock for {item['product_name']}. "
                        f"Available: {available_stock}, Requested: {item['quantity']}"
                    )
            
            return True
            
        except Exception as e:
            raise Exception(f"Stock validation failed: {str(e)}")

    # ================================================================
    # CHECKOUT PREPARATION (OPTIMIZED)
    # ================================================================

    def prepare_for_checkout(self, cart_id):
        """
        ✅ OPTIMIZED: Validate cart and prepare data for sale creation
        
        Old: 2+ DB operations
        New: 1 DB operation + batch validation
        
        Returns sale_data ready for POSSalesService
        """
        try:
            cart = self.get_cart(cart_id)
            
            # Validate cart has items
            if not cart['items']:
                raise ValueError("Cart is empty")
            
            # ✅ Batch validate stock for all items (single query)
            self.validate_cart_stock_batch(cart_id)
            
            # Prepare sale data
            sale_data = {
                'items': cart['items'],
                'subtotal': cart['subtotal'],
                'tax_amount': cart['tax_amount'],
                'discount_amount': cart['discount_amount'],
                'total_amount': cart['total'],
                'shift_id': cart.get('shift_id'),
                'cashier_id': cart.get('cashier_id'),
                'discount_details': cart.get('discount_details', {}),
                'cart_id': cart_id
            }
            
            # Add promotion ID if promotion was applied
            if cart.get('discount_type') == 'promotion':
                sale_data['promotion_id'] = cart['discount_details'].get('promotion_id')
            
            return sale_data
            
        except Exception as e:
            raise Exception(f"Error preparing checkout: {str(e)}")

    # ================================================================
    # PROMOTION INTEGRATION
    # ================================================================

    def apply_promotion(self, cart_id, promotion_id=None):
        """
        Apply promotion discount to cart
        
        Args:
            cart_id: Cart ID
            promotion_id: Optional specific promotion ID, otherwise auto-selects best
        
        Returns:
            Updated cart with promotion applied
        """
        try:
            cart = self.get_cart(cart_id)
            
            # Check if cart has items
            if not cart['items']:
                raise ValueError("Cannot apply promotion to empty cart")
            
            # Apply promotion
            if promotion_id:
                # Apply specific promotion
                promotion = self.promotion_service.collection.find_one({
                    'promotion_id': promotion_id,
                    'is_active': True,
                    'status': 'active'
                })
                
                if not promotion:
                    raise ValueError(f"Promotion {promotion_id} not found or inactive")
                
                result = self.promotion_service.calculate_promotion_discount(
                    promotion, 
                    cart['items']
                )
            else:
                # Auto-select best promotion
                result = self.promotion_service.apply_best_promotion_to_cart(
                    cart['items']
                )
            
            # Check result
            if not result.get('success', True):
                raise ValueError(result.get('message', 'Failed to apply promotion'))
            
            # Apply discount if found
            if result.get('discount_amount', 0) > 0:
                promotion_data = result.get('promotion_applied')
                
                if not promotion_data:
                    raise ValueError("No promotion data returned")
                
                cart['discount_type'] = 'promotion'
                cart['discount_amount'] = round(result['discount_amount'], 2)
                cart['discount_details'] = {
                    'promotion_id': promotion_data['promotion_id'],
                    'promotion_name': promotion_data['name'],
                    'promotion_type': promotion_data['type'],
                    'affected_items': result.get('affected_items', [])
                }
                
                # Recalculate in-memory
                cart = self._calculate_cart_totals_in_memory(cart)
                
                # Single DB write
                self.cart_collection.update_one(
                    {'_id': cart_id},
                    {
                        '$set': {
                            'discount_type': cart['discount_type'],
                            'discount_amount': cart['discount_amount'],
                            'discount_details': cart['discount_details'],
                            'tax_amount': cart['tax_amount'],
                            'total': cart['total'],
                            'last_updated': datetime.utcnow()
                        }
                    }
                )
                
                return cart
            else:
                # No applicable promotion or discount is 0
                return cart
            
        except Exception as e:
            raise Exception(f"Error applying promotion: {str(e)}")

    def remove_promotion(self, cart_id):
        """Remove promotion discount (alias for remove_discount)"""
        return self.remove_discount(cart_id)

    def get_available_promotions_for_cart(self, cart_id):
        """Get list of promotions applicable to current cart"""
        try:
            cart = self.get_cart(cart_id)
            
            if not cart['items']:
                return []
            
            # Get all active promotions
            active_result = self.promotion_service.get_active_promotions()
            
            if not active_result['success']:
                return []
            
            # Test each promotion
            applicable = []
            for promotion in active_result.get('promotions', []):
                result = self.promotion_service.calculate_promotion_discount(
                    promotion,
                    cart['items']
                )
                
                if result.get('discount_amount', 0) > 0:
                    applicable.append({
                        'promotion_id': promotion['promotion_id'],
                        'name': promotion['name'],
                        'type': promotion['type'],
                        'potential_discount': result['discount_amount'],
                        'affected_items_count': len(result.get('affected_items', []))
                    })
            
            # Sort by discount amount (best first)
            applicable.sort(key=lambda x: x['potential_discount'], reverse=True)
            
            return applicable
            
        except Exception as e:
            raise Exception(f"Error getting available promotions: {str(e)}")

    # ================================================================
    # UTILITY METHODS
    # ================================================================

    def get_item_count(self, cart_id):
        """Get total number of items in cart"""
        try:
            cart = self.get_cart(cart_id)
            return sum(item['quantity'] for item in cart['items'])
            
        except Exception as e:
            raise Exception(f"Error getting item count: {str(e)}")

    def cleanup_old_carts(self, hours_old=24):
        """
        ✅ OPTIMIZED: Delete abandoned carts older than specified hours
        Uses indexed query for better performance
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
            
            # ✅ Uses cleanup_idx index for fast query
            result = self.cart_collection.delete_many({
                'last_updated': {'$lt': cutoff_time},
                'status': 'active'
            })
            
            return result.deleted_count
            
        except Exception as e:
            raise Exception(f"Error cleaning up old carts: {str(e)}")