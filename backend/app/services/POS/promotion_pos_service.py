# backend/services/pos/promotion_service.py

from datetime import datetime
from ...database import db_manager
from ..Backoffice.product_service import ProductService

class PromotionService:
    """
    Handles promotion/discount logic for POS
    Calculates discounts based on categories and products
    """
    
    def __init__(self):
        self.db = db_manager.get_database()
        self.promotions_collection = self.db.promotions
        self.categories_collection = self.db.categories
        self.product_service = ProductService()
    
    def generate_promotion_id(self):
        """Generate PROMO-##### ID"""
        pipeline = [
            {'$match': {'_id': {'$regex': '^PROMO-'}}},
            {'$project': {'numericPart': {'$toInt': {'$substr': ['$_id', 6, -1]}}}},
            {'$sort': {'numericPart': -1}},
            {'$limit': 1}
        ]
        result = list(self.promotions_collection.aggregate(pipeline))
        next_number = result[0]['numericPart'] + 1 if result else 1
        return f"PROMO-{next_number:05d}"
    
    def get_active_promotions(self):
        """Get all currently active promotions"""
        try:
            now = datetime.utcnow()
            promotions = list(self.promotions_collection.find({
                'status': 'active',
                'start_date': {'$lte': now},
                'end_date': {'$gte': now},
                'isDeleted': {'$ne': True}
            }))
            return promotions
        except Exception as e:
            raise Exception(f"Error getting active promotions: {str(e)}")
    
    def calculate_discount(self, cart_items, promotion_id=None):
        """
        Calculate discount for cart based on promotion
        
        Args:
            cart_items: List of items from cart
            promotion_id: Optional specific promotion to apply
        
        Returns:
            {
                'discount_amount': float,
                'promotion_applied': str,
                'affected_items': list
            }
        """
        try:
            if not promotion_id:
                # Auto-detect best promotion
                promotion = self._find_best_promotion(cart_items)
            else:
                promotion = self.promotions_collection.find_one({
                    '_id': promotion_id,
                    'status': 'active'
                })
            
            if not promotion:
                return {
                    'discount_amount': 0,
                    'promotion_applied': None,
                    'affected_items': []
                }
            
            # Get affected categories/products
            affected_categories = self._get_affected_categories(promotion)
            
            total_discount = 0
            affected_items = []
            
            for item in cart_items:
                product = self.product_service.get_product_by_id(item['product_id'])
                
                if not product:
                    continue
                
                # Check if product is in promotion
                if self._is_product_in_promotion(product, affected_categories):
                    item_total = item['unit_price'] * item['quantity']
                    
                    # Calculate discount
                    if promotion['discount_type'] == 'percentage':
                        discount = item_total * (promotion['discount_value'] / 100)
                    elif promotion['discount_type'] == 'fixed':
                        discount = min(promotion['discount_value'], item_total)
                    else:
                        discount = 0
                    
                    total_discount += discount
                    affected_items.append({
                        'product_id': item['product_id'],
                        'product_name': product['product_name'],
                        'discount_applied': discount
                    })
            
            return {
                'discount_amount': round(total_discount, 2),
                'promotion_applied': promotion['_id'],
                'promotion_name': promotion['promotion_name'],
                'affected_items': affected_items
            }
            
        except Exception as e:
            raise Exception(f"Error calculating discount: {str(e)}")
    
    def _get_affected_categories(self, promotion):
        """Get all categories/subcategories affected by promotion"""
        applicable_products = promotion.get('applicable_products', [])
        affected = []
        
        for category_name in applicable_products:
            category = self.categories_collection.find_one({
                'category_name': category_name,
                'isDeleted': {'$ne': True}
            })
            
            if category:
                # Add all subcategories
                for subcat in category.get('sub_categories', []):
                    affected.append(subcat.get('sub_category_name'))
        
        return affected
    
    def _is_product_in_promotion(self, product, affected_categories):
        """Check if product is in any of the affected categories"""
        product_subcat = product.get('subcategory_name')
        return product_subcat in affected_categories
    
    def _find_best_promotion(self, cart_items):
        """Find promotion that gives maximum discount"""
        active_promotions = self.get_active_promotions()
        
        best_promotion = None
        max_discount = 0
        
        for promo in active_promotions:
            result = self.calculate_discount(cart_items, promo['_id'])
            if result['discount_amount'] > max_discount:
                max_discount = result['discount_amount']
                best_promotion = promo
        
        return best_promotion