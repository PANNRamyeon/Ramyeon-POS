from datetime import datetime, timedelta
from ...database import db_manager
from ..Backoffice.product_service import ProductService
from .promotion_pos_service import PromotionService

class CartService:
    """
    Manages shopping carts for POS transactions
    Cart lifecycle: create → add items → apply discounts → checkout → clear
    """
    
    def __init__(self):
        self.db = db_manager.get_database()
        self.cart_collection = self.db.carts
        self.product_service = ProductService()
        self.promotion_service = PromotionService()
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
                'discount_type': None,  # 'percentage', 'fixed', 'promotion'
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
    # ITEM MANAGEMENT
    # ================================================================
    
    def add_item(self, cart_id, product_id, quantity=1):
        """Add item to cart or increase quantity if already exists"""
        try:
            # Get product details
            product = self.product_service.get_product_by_id(product_id)
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Check stock availability
            if product['stock'] < quantity:
                raise ValueError(f"Insufficient stock. Available: {product['stock']}")
            
            cart = self.get_cart(cart_id)
            
            # Check if item already in cart
            item_exists = False
            for item in cart['items']:
                if item['product_id'] == product_id:
                    # Update quantity
                    new_quantity = item['quantity'] + quantity
                    
                    # Check total stock needed
                    if product['stock'] < new_quantity:
                        raise ValueError(f"Insufficient stock. Available: {product['stock']}")
                    
                    item['quantity'] = new_quantity
                    item['subtotal'] = item['unit_price'] * new_quantity
                    item_exists = True
                    break
            
            # Add new item if doesn't exist
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
            
            # Update cart in database
            self.cart_collection.update_one(
                {'_id': cart_id},
                {'$set': {
                    'items': cart['items'],
                    'last_updated': datetime.utcnow()
                }}
            )
            
            # Recalculate totals
            return self._recalculate_cart(cart_id)
            
        except Exception as e:
            raise Exception(f"Error adding item to cart: {str(e)}")
    
    def remove_item(self, cart_id, product_id):
        """Remove item from cart completely"""
        try:
            cart = self.get_cart(cart_id)
            
            # Filter out the item
            cart['items'] = [item for item in cart['items'] if item['product_id'] != product_id]
            
            # Update cart
            self.cart_collection.update_one(
                {'_id': cart_id},
                {'$set': {
                    'items': cart['items'],
                    'last_updated': datetime.utcnow()
                }}
            )
            
            # Recalculate totals
            return self._recalculate_cart(cart_id)
            
        except Exception as e:
            raise Exception(f"Error removing item from cart: {str(e)}")
    
    def update_quantity(self, cart_id, product_id, new_quantity):
        """Update quantity of specific item"""
        try:
            if new_quantity <= 0:
                return self.remove_item(cart_id, product_id)
            
            # Check stock
            product = self.product_service.get_product_by_id(product_id)
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
            
            # Update cart
            self.cart_collection.update_one(
                {'_id': cart_id},
                {'$set': {
                    'items': cart['items'],
                    'last_updated': datetime.utcnow()
                }}
            )
            
            # Recalculate totals
            return self._recalculate_cart(cart_id)
            
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
            
            update_data = {
                'discount_type': 'percentage',
                'discount_details': {'percentage': percentage},
                'discount_amount': round(discount_amount, 2),
                'last_updated': datetime.utcnow()
            }
            
            self.cart_collection.update_one(
                {'_id': cart_id},
                {'$set': update_data}
            )
            
            return self._recalculate_cart(cart_id)
            
        except Exception as e:
            raise Exception(f"Error applying percentage discount: {str(e)}")
    
    def apply_fixed_discount(self, cart_id, amount):
        """Apply fixed amount discount (e.g., ₱50 off)"""
        try:
            cart = self.get_cart(cart_id)
            
            if amount > cart['subtotal']:
                raise ValueError("Discount cannot exceed subtotal")
            
            update_data = {
                'discount_type': 'fixed',
                'discount_details': {'amount': amount},
                'discount_amount': round(amount, 2),
                'last_updated': datetime.utcnow()
            }
            
            self.cart_collection.update_one(
                {'_id': cart_id},
                {'$set': update_data}
            )
            
            return self._recalculate_cart(cart_id)
            
        except Exception as e:
            raise Exception(f"Error applying fixed discount: {str(e)}")
    
    def remove_discount(self, cart_id):
        """Remove any applied discount"""
        try:
            update_data = {
                'discount_type': None,
                'discount_details': {},
                'discount_amount': 0,
                'last_updated': datetime.utcnow()
            }
            
            self.cart_collection.update_one(
                {'_id': cart_id},
                {'$set': update_data}
            )
            
            return self._recalculate_cart(cart_id)
            
        except Exception as e:
            raise Exception(f"Error removing discount: {str(e)}")
    
    # ================================================================
    # CALCULATION
    # ================================================================
    
    def _recalculate_cart(self, cart_id):
        """Recalculate all cart totals"""
        try:
            cart = self.get_cart(cart_id)
            
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
            
            # Update cart
            update_data = {
                'subtotal': round(subtotal, 2),
                'tax_amount': round(tax_amount, 2),
                'total': round(total, 2),
                'last_updated': datetime.utcnow()
            }
            
            self.cart_collection.update_one(
                {'_id': cart_id},
                {'$set': update_data}
            )
            
            return self.get_cart(cart_id)
            
        except Exception as e:
            raise Exception(f"Error recalculating cart: {str(e)}")
    
    # ================================================================
    # CHECKOUT PREPARATION
    # ================================================================
    
    def prepare_for_checkout(self, cart_id):
        """
        Validate cart and prepare data for sale creation
        Returns sale_data ready for POSSalesService
        """
        try:
            cart = self.get_cart(cart_id)
            
            # Validate cart has items
            if not cart['items']:
                raise ValueError("Cart is empty")
            
            # Validate stock availability for all items
            for item in cart['items']:
                product = self.product_service.get_product_by_id(item['product_id'])
                if product['stock'] < item['quantity']:
                    raise ValueError(
                        f"Insufficient stock for {item['product_name']}. "
                        f"Available: {product['stock']}, Requested: {item['quantity']}"
                    )
            
            # Prepare sale data
            sale_data = {
                'items': cart['items'],
                'subtotal': cart['subtotal'],
                'tax_amount': cart['tax_amount'],
                'discount_amount': cart['discount_amount'],
                'total_amount': cart['total'],
                'discount_details': cart.get('discount_details', {}),
                'cart_id': cart_id  # Reference to original cart
            }
            
            # Add promotion ID if promotion was applied
            if cart.get('discount_type') == 'promotion':
                sale_data['promotion_id'] = cart['discount_details'].get('promotion_id')
            
            return sale_data
            
        except Exception as e:
            raise Exception(f"Error preparing checkout: {str(e)}")
    
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
        """Delete abandoned carts older than specified hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
            
            result = self.cart_collection.delete_many({
                'last_updated': {'$lt': cutoff_time},
                'status': 'active'
            })
            
            return result.deleted_count
            
        except Exception as e:
            raise Exception(f"Error cleaning up old carts: {str(e)}")
    
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
                
                update_data = {
                    'discount_type': 'promotion',
                    'discount_amount': round(result['discount_amount'], 2),
                    'discount_details': {
                        'promotion_id': promotion_data['promotion_id'],
                        'promotion_name': promotion_data['name'],
                        'promotion_type': promotion_data['type'],
                        'affected_items': result.get('affected_items', [])
                    },
                    'last_updated': datetime.utcnow()
                }
                
                self.cart_collection.update_one(
                    {'_id': cart_id},
                    {'$set': update_data}
                )
                
                return self._recalculate_cart(cart_id)
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