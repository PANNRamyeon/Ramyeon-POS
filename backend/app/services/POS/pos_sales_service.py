from datetime import datetime, timedelta
from ...database import db_manager
from ..Backoffice.product_service import ProductService
from notifications.services import notification_service
from .batch_service import BatchService
import logging
logger = logging.getLogger(__name__)

class POSSalesService:
    """
    POS transaction processing - String ID version
    Handles ONLY POS sales (sales collection)
    """
    def __init__(self):
        self.db = db_manager.get_database()
        self.sales_collection = self.db.sales 
        self.products_collection = self.db.products
        self.customers_collection = self.db.customers
        self.users_collection = self.db.users
        self.shifts_collection = self.db.shifts  
        self.product_service = ProductService()
        self.batch_service = BatchService()

    # ================================================================
    # ID GENERATION
    # ================================================================
    
    def generate_sale_id(self):
        """Generate sequential SALE-###### ID"""
        try:
            pipeline = [
                {'$match': {'_id': {'$regex': '^SALE-'}}},
                {'$project': {
                    'numericPart': {'$toInt': {'$substr': ['$_id', 5, -1]}}
                }},
                {'$sort': {'numericPart': -1}},
                {'$limit': 1}
            ]
            
            result = list(self.sales_collection.aggregate(pipeline))
            next_number = result[0]['numericPart'] + 1 if result else 1
            
            return f"SALE-{next_number:06d}"
        except Exception:
            count = self.sales_collection.count_documents({}) + 1
            return f"SALE-{count:06d}"

    # ================================================================
    # LOYALTY POINTS MANAGEMENT
    # ================================================================
    
    def calculate_loyalty_points_earned(self, subtotal_after_discount):
        """
        Calculate loyalty points earned (20% of subtotal after discount)
        
        Args:
            subtotal_after_discount: Subtotal after all discounts
        
        Returns:
            int: Points to be earned
        """
        return int(subtotal_after_discount * 0.20)
    
    def calculate_points_discount(self, points_to_redeem):
        """
        Convert points to discount amount
        4 points = ₱1 discount
        
        Args:
            points_to_redeem: Number of points customer wants to use
        
        Returns:
            float: Discount amount in pesos
        """
        return points_to_redeem / 4.0
    
    def validate_points_redemption(self, customer_id, points_to_redeem, subtotal):
        """
        Validate loyalty points redemption
        
        Args:
            customer_id: Customer ID
            points_to_redeem: Points customer wants to use
            subtotal: Order subtotal
        
        Returns:
            dict: {'valid': bool, 'error': str}
        """
        try:
            if points_to_redeem == 0:
                return {'valid': True, 'error': None}
            
            # Minimum redemption: 40 points (₱10)
            if points_to_redeem < 40:
                return {
                    'valid': False,
                    'error': 'Minimum redemption is 40 points (₱10)'
                }
            
            # Get customer
            customer = self.customers_collection.find_one({'_id': customer_id})
            
            if not customer:
                return {'valid': False, 'error': 'Customer not found'}
            
            # Check if customer has enough points
            available_points = customer.get('loyalty_points', 0)
            
            if available_points < points_to_redeem:
                return {
                    'valid': False,
                    'error': f'Insufficient points. Available: {available_points}, Requested: {points_to_redeem}'
                }
            
            # Check max discount: min(₱20, 20% of subtotal)
            points_discount = self.calculate_points_discount(points_to_redeem)
            max_discount = min(20, subtotal * 0.20)
            
            if points_discount > max_discount:
                max_points = int(max_discount * 4)  # Convert back to points
                return {
                    'valid': False,
                    'error': f'Points discount exceeds cap. Maximum: {max_points} points (₱{max_discount:.2f})'
                }
            
            return {'valid': True, 'error': None}
            
        except Exception as e:
            logger.error(f"Points validation error: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    def deduct_customer_points(self, customer_id, points_to_deduct, sale_id):
        """
        Deduct loyalty points from customer balance
        
        Args:
            customer_id: Customer ID
            points_to_deduct: Points to deduct
            sale_id: Sale ID for transaction history
        """
        try:
            customer = self.customers_collection.find_one({'_id': customer_id})
            
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            current_balance = customer.get('loyalty_points', 0)
            new_balance = current_balance - points_to_deduct
            
            # Create points transaction
            points_transaction = {
                'transaction_id': sale_id,
                'transaction_type': 'redeemed',
                'points': -points_to_deduct,
                'balance_before': current_balance,
                'balance_after': new_balance,
                'description': f"Redeemed {points_to_deduct} points on sale {sale_id}",
                'created_at': datetime.utcnow()
            }
            
            # Update customer
            self.customers_collection.update_one(
                {'_id': customer_id},
                {
                    '$set': {
                        'loyalty_points': new_balance,
                        'last_updated': datetime.utcnow()
                    },
                    '$push': {'points_transactions': points_transaction}
                }
            )
            
            logger.info(f"✅ Deducted {points_to_deduct} points from {customer_id}")
            
        except Exception as e:
            logger.error(f"❌ Error deducting points: {str(e)}")
            raise
    
    def award_loyalty_points(self, customer_id, points_to_award, sale_id, order_amount):
        """
        Award loyalty points to customer when sale is completed
        
        Args:
            customer_id: Customer ID
            points_to_award: Points to award
            sale_id: Sale ID
            order_amount: Sale total amount after discount
        """
        try:
            customer = self.customers_collection.find_one({'_id': customer_id})
            
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            current_balance = customer.get('loyalty_points', 0)
            new_balance = current_balance + points_to_award
            
            # Points expire in 12 months
            expires_at = datetime.utcnow() + timedelta(days=365)
            
            # Create points transaction
            points_transaction = {
                'transaction_id': sale_id,
                'transaction_type': 'earned',
                'points': points_to_award,
                'balance_before': current_balance,
                'balance_after': new_balance,
                'description': f"Earned from sale {sale_id} (₱{order_amount:.2f} purchase)",
                'earned_at': datetime.utcnow(),
                'expires_at': expires_at,
                'status': 'active',
                'created_at': datetime.utcnow()
            }
            
            # Update customer
            self.customers_collection.update_one(
                {'_id': customer_id},
                {
                    '$set': {
                        'loyalty_points': new_balance,
                        'last_purchase': datetime.utcnow(),
                        'last_updated': datetime.utcnow()
                    },
                    '$push': {'points_transactions': points_transaction}
                }
            )
            
            logger.info(f"✅ Awarded {points_to_award} points to {customer_id}")
            
            
        except Exception as e:
            logger.error(f"❌ Error awarding points: {str(e)}")
            raise
    
    def refund_customer_points(self, customer_id, points_to_refund, sale_id):
        """
        Refund loyalty points when sale is voided
        
        Args:
            customer_id: Customer ID
            points_to_refund: Points to refund
            sale_id: Sale ID
        """
        try:
            customer = self.customers_collection.find_one({'_id': customer_id})
            
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            current_balance = customer.get('loyalty_points', 0)
            new_balance = current_balance + points_to_refund
            
            # Create points transaction
            points_transaction = {
                'transaction_id': f"{sale_id}-VOID",
                'transaction_type': 'refunded',
                'points': points_to_refund,
                'balance_before': current_balance,
                'balance_after': new_balance,
                'description': f"Refunded {points_to_refund} points from voided sale {sale_id}",
                'created_at': datetime.utcnow()
            }
            
            # Update customer
            self.customers_collection.update_one(
                {'_id': customer_id},
                {
                    '$set': {
                        'loyalty_points': new_balance,
                        'last_updated': datetime.utcnow()
                    },
                    '$push': {'points_transactions': points_transaction}
                }
            )
            
            logger.info(f"✅ Refunded {points_to_refund} points to {customer_id}")
            
        except Exception as e:
            logger.error(f"❌ Error refunding points: {str(e)}")
            raise

    # ================================================================
    # CORE SALES OPERATIONS
    # ================================================================
    
    def create_sale(self, sale_data, cashier_id):
        """
        Create a new POS sale transaction with FIFO batch deduction and loyalty points
        
        Args:
            sale_data: Dictionary containing sale information
            cashier_id: ID of the cashier (USER-#### format)
        
        Returns:
            Dictionary with success status and created sale data
        """
        try:
            # Generate sale ID
            sale_id = self.generate_sale_id()
            transaction_date = datetime.utcnow()
            
            print(f"\n{'='*60}")
            print(f"💰 Creating POS Sale: {sale_id}")
            print(f"   Cashier: {cashier_id}")
            print(f"   Total: ₱{sale_data.get('total_amount', 0):.2f}")
            print(f"   Items: {len(sale_data.get('items', []))}")
            print(f"{'='*60}\n")
            
            # ✅ Step 1: Get customer if provided
            customer_id = sale_data.get('customer_id')
            customer = None
            
            if customer_id:
                customer = self.customers_collection.find_one({'_id': customer_id})
                print(f"👤 Customer: {customer.get('full_name') if customer else 'Not found'}\n")
            
            # ✅ Step 2: Calculate initial subtotal and discount breakdown
            subtotal = sale_data.get('subtotal', 0)
            promotion_discount = sale_data.get('promotion_discount', 0)
            points_discount = sale_data.get('points_discount', 0)
            total_discount = promotion_discount + points_discount
            
            print(f"💵 Pricing Breakdown:")
            print(f"   Subtotal: ₱{subtotal:.2f}")
            if promotion_discount > 0:
                print(f"   Promo Discount: -₱{promotion_discount:.2f}")
            if points_discount > 0:
                print(f"   Points Discount: -₱{points_discount:.2f}")
            print(f"   Total Discount: -₱{total_discount:.2f}")
            
            # ✅ Step 3: Validate and deduct points if used
            points_to_redeem = sale_data.get('loyalty_points_used', 0)
            
            if customer_id and points_to_redeem > 0:
                print(f"\n🎁 Processing points redemption: {points_to_redeem} points")
                
                # Calculate subtotal after promotion discount for validation
                subtotal_after_promo = subtotal - promotion_discount
                
                print(f"   💰 Subtotal after promo: ₱{subtotal_after_promo:.2f}")
                print(f"   💰 Points discount requested: ₱{points_discount:.2f}")
                
                # Validate points redemption using subtotal AFTER promotion
                points_validation = self.validate_points_redemption(
                    customer_id,
                    points_to_redeem,
                    subtotal_after_promo  # ✅ FIXED: Use subtotal after promotion
                )
                
                if not points_validation['valid']:
                    raise ValueError(f"Points validation failed: {points_validation['error']}")
                
                # Deduct points from customer
                self.deduct_customer_points(customer_id, points_to_redeem, sale_id)
                print(f"   ✅ Points deducted successfully")
                print(f"   💳 Customer balance updated")
            
            # ✅ Step 4: Calculate loyalty points to be earned
            # Points earned on subtotal after ALL discounts (before tax)
            subtotal_after_all_discounts = subtotal - total_discount
            loyalty_points_earned = 0
            
            if customer_id:
                loyalty_points_earned = self.calculate_loyalty_points_earned(subtotal_after_all_discounts)
                print(f"\n✨ Loyalty points calculation:")
                print(f"   Subtotal: ₱{subtotal:.2f}")
                print(f"   Total discounts: -₱{total_discount:.2f}")
                print(f"   Base for points: ₱{subtotal_after_all_discounts:.2f}")
                print(f"   Points to earn: {loyalty_points_earned} points (20%)")
            
            # ✅ Step 5: Build sale record with loyalty tracking
            sale_record = {
                '_id': sale_id,
                'transaction_date': transaction_date,
                'cashier_id': cashier_id,
                'shift_id': sale_data.get('shift_id'),
                'customer_id': customer_id,
                'items': [],  # Will be populated with batch info
                'subtotal': subtotal,
                'tax_amount': sale_data.get('tax_amount', 0),
                'discount_amount': total_discount,
                
                # ✅ Discount breakdown
                'discount_breakdown': {
                    'promotion_discount': promotion_discount,
                    'points_discount': points_discount,
                    'total_discount': total_discount
                },
                
                'total_amount': sale_data.get('total_amount', 0),
                'payment_method': sale_data.get('payment_method'),
                'payment_details': sale_data.get('payment_details', {}),
                
                # ✅ Promotion info
                'promotion_id': sale_data.get('promotion_id'),
                'promotion_discount': promotion_discount if sale_data.get('promotion_id') else 0,
                
                # ✅ Loyalty points tracking
                'loyalty_points': {
                    'points_used': points_to_redeem,
                    'points_earned': loyalty_points_earned,
                    'points_discount_value': points_discount
                } if customer_id else None,
                
                'status': 'completed',
                'source': 'pos',
                'created_at': transaction_date,
                'updated_at': transaction_date,
                'is_voided': False,
                'points_awarded': False  # Will be set to True after awarding
            }
            
            # ✅ Step 6: Process each item with FIFO batch deduction
            print("\n📦 Processing items with FIFO batch deduction...\n")
            
            for item in sale_data.get('items', []):
                product_id = item.get('product_id')
                quantity_needed = item.get('quantity', 0)
                
                print(f"   Processing: {item.get('product_name')} ({product_id}) x{quantity_needed}")
                
                # Verify product exists
                product = self.products_collection.find_one({'_id': product_id})
                
                if not product:
                    raise ValueError(f"Product {product_id} not found")
                
                # Check stock availability
                stock_check = self.batch_service.check_batch_availability(
                    product_id,
                    quantity_needed
                )
                
                if not stock_check['available']:
                    raise ValueError(
                        f"Insufficient stock for {item.get('product_name')}. "
                        f"Available: {stock_check['total_stock']}, Requested: {quantity_needed}"
                    )
                
                # ✅ PREPARE TRANSACTION INFO FOR USAGE_HISTORY
                transaction_info = {
                    'transaction_id': sale_id,
                    'adjusted_by': cashier_id,
                    'source': 'pos_sale'
                }
                
                # ✅ Deduct from batches using FIFO with transaction tracking
                batch_deductions = self.batch_service.deduct_stock_fifo(
                    product_id, 
                    quantity_needed,
                    transaction_date,
                    transaction_info=transaction_info
                )
                
                # Add item to sale record with batch tracking
                sale_item = {
                    'product_id': product_id,
                    'product_name': item.get('product_name'),
                    'sku': item.get('sku'),
                    'quantity': quantity_needed,
                    'unit_price': item.get('unit_price'),
                    'subtotal': item.get('subtotal'),
                    'is_taxable': item.get('is_taxable', True),
                    'batches_used': batch_deductions
                }
                
                sale_record['items'].append(sale_item)
                
                # ✅ Update product total stock (cached)
                new_total_stock = product.get('stock', 0) - quantity_needed
                
                self.products_collection.update_one(
                    {'_id': product_id},
                    {
                        '$set': {
                            'stock': new_total_stock,
                            'updated_at': transaction_date
                        }
                    }
                )
                
                print(f"      Stock updated: {product.get('stock')} → {new_total_stock}")
            
            # ✅ Step 7: Insert sale record
            self.sales_collection.insert_one(sale_record)
            
            # ✅ Step 8: Award loyalty points to customer
            if customer_id and loyalty_points_earned > 0:
                print(f"\n✨ Awarding {loyalty_points_earned} points to customer...")
                
                self.award_loyalty_points(
                    customer_id,
                    loyalty_points_earned,
                    sale_id,
                    subtotal_after_all_discounts  # ✅ FIXED: Use subtotal after all discounts
                )
                
                # Mark points as awarded
                self.sales_collection.update_one(
                    {'_id': sale_id},
                    {'$set': {'points_awarded': True}}
                )
                
                print(f"   ✅ Points awarded successfully")
            
            print(f"\n{'='*60}")
            print(f"✅ POS Sale created successfully: {sale_id}")
            print(f"{'='*60}\n")
            
            # Get updated sale record
            sale_record = self.sales_collection.find_one({'_id': sale_id})
            
            return {
                'success': True,
                'message': 'Sale created successfully',
                'data': sale_record
            }
            
        except ValueError as e:
            print(f"❌ Validation error: {str(e)}")
            
            # Rollback: Refund points if they were deducted
            if 'points_to_redeem' in locals() and points_to_redeem > 0 and customer_id:
                try:
                    self.refund_customer_points(customer_id, points_to_redeem, f"{sale_id}-ROLLBACK")
                    print(f"   ↩️ Points refunded due to error")
                except:
                    pass
            
            raise
            
        except Exception as e:
            print(f"❌ Unexpected error creating POS sale: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Rollback: Refund points if they were deducted
            if 'points_to_redeem' in locals() and points_to_redeem > 0 and customer_id:
                try:
                    self.refund_customer_points(customer_id, points_to_redeem, f"{sale_id}-ROLLBACK")
                    print(f"   ↩️ Points refunded due to error")
                except:
                    pass
            
            raise Exception(f"Error creating POS sale: {str(e)}")
        
    def get_sale_by_id(self, sale_id):
        """Get a POS sale by string ID"""
        try:
            sale = self.sales_collection.find_one({'_id': sale_id})
            return sale
            
        except Exception as e:
            raise Exception(f"Error fetching POS sale: {str(e)}")
    
    def get_recent_sales(self, limit=50, cashier_id=None):
        """Get recent POS sales"""
        try:
            query = {'source': 'pos'}
            
            if cashier_id:
                query['cashier_id'] = cashier_id
            
            sales = list(
                self.sales_collection
                .find(query)
                .sort('transaction_date', -1)
                .limit(limit)
            )
            
            return sales
            
        except Exception as e:
            raise Exception(f"Error fetching recent sales: {str(e)}")
    
    def get_sales_by_date_range(self, start_date, end_date, cashier_id=None):
        """Get POS sales by date range"""
        try:
            query = {
                'transaction_date': {
                    '$gte': start_date,
                    '$lte': end_date
                },
                'source': 'pos'
            }
            
            if cashier_id:
                query['cashier_id'] = cashier_id
            
            sales = list(
                self.sales_collection
                .find(query)
                .sort('transaction_date', -1)
            )
            
            return sales
            
        except Exception as e:
            raise Exception(f"Error fetching sales by date range: {str(e)}")
    
    def get_sales_by_shift(self, shift_id):
        """Get all sales for a specific shift"""
        try:
            sales = list(
                self.sales_collection
                .find({'shift_id': shift_id})
                .sort('transaction_date', 1)
            )
            
            return sales
            
        except Exception as e:
            raise Exception(f"Error fetching sales by shift: {str(e)}")

    # ================================================================
    # VOID AND REFUND OPERATIONS
    # ================================================================
    
    def void_sale(self, sale_id, reason, manager_id):
        """
        Void sale and restore stock to batches with usage_history tracking
        ALSO refunds loyalty points if they were used
        
        Args:
            sale_id: Sale ID (SALE-######)
            reason: Reason for voiding
            manager_id: Manager who approved void
        
        Returns:
            Updated sale document
        """
        try:
            print(f"\n{'='*60}")
            print(f"🚫 Voiding Sale: {sale_id}")
            print(f"   Manager: {manager_id}")
            print(f"   Reason: {reason}")
            print(f"{'='*60}\n")
            
            # Get sale
            sale = self.get_sale_by_id(sale_id)
            
            if not sale:
                raise ValueError(f"Sale {sale_id} not found")
            
            if sale.get('is_voided'):
                raise ValueError(f"Sale {sale_id} is already voided")
            
            # ✅ VERIFY MANAGER AUTHORIZATION
            manager = self.users_collection.find_one({'_id': manager_id, 'role': 'admin', 'status': 'active'})
            if not manager:
                raise PermissionError(f"Manager ID {manager_id} is invalid or not authorized to void sales.")
            
            # ✅ PREPARE TRANSACTION INFO FOR RESTORATION
            transaction_info = {
                'transaction_id': f"{sale_id}-VOID",
                'adjusted_by': manager_id,
                'reason': f"Sale voided: {reason}"
            }
            
            # ✅ Restore stock to batches with tracking
            print("📦 Restoring stock to batches...\n")
            
            for item in sale.get('items', []):
                if 'batches_used' in item:
                    print(f"   Restoring: {item['product_name']} x{item['quantity']}")
                    
                    # Restore to batches using batch service
                    self.batch_service.restore_stock_to_batches(
                        item['batches_used'],
                        datetime.utcnow(),
                        transaction_info=transaction_info
                    )
                    
                    # Restore product total stock
                    product = self.products_collection.find_one({'_id': item['product_id']})
                    
                    if product:
                        new_stock = product.get('stock', 0) + item['quantity']
                        
                        self.products_collection.update_one(
                            {'_id': item['product_id']},
                            {
                                '$set': {
                                    'stock': new_stock,
                                    'updated_at': datetime.utcnow()
                                }
                            }
                        )
                        
                        print(f"      Stock restored: {product.get('stock')} → {new_stock}")
            
            print("\n✅ Stock restored to batches\n")
            
        
            # ✅ Refund loyalty points if used
            points_refunded = False
            customer_id = sale.get('customer_id')
            loyalty_info = sale.get('loyalty_points')
            points_used = 0

            if isinstance(loyalty_info, dict):
                points_used = loyalty_info.get('points_used', 0)

            if customer_id and points_used > 0:
                print(f"🎁 Refunding {points_used} loyalty points...")

                self.refund_customer_points(
                    customer_id,
                    points_used,
                    sale_id
                )

                points_refunded = True
                print("   ✅ Points refunded\n")

            
            # ✅ Mark sale as voided
            self.sales_collection.update_one(
                {'_id': sale_id},
                {
                    '$set': {
                        'is_voided': True,
                        'void_reason': reason,
                        'voided_by': manager_id,
                        'voided_at': datetime.utcnow(),
                        'status': 'voided',
                        'updated_at': datetime.utcnow(),
                        'points_refunded': points_refunded
                    }
                }
            )
            
            print(f"{'='*60}")
            print(f"✅ Sale voided successfully: {sale_id}")
            print(f"{'='*60}\n")
            
            return self.get_sale_by_id(sale_id)
            
        except Exception as e:
            logger.error(f"❌ Void sale failed: {str(e)}")
            raise

    # ================================================================
    # REPORTING AND ANALYTICS
    # ================================================================
    
    def get_daily_summary(self, date, cashier_id=None):
        """Get daily sales summary"""
        try:
            from datetime import time
            
            start_datetime = datetime.combine(date, time.min)
            end_datetime = datetime.combine(date, time.max)
            
            query = {
                'transaction_date': {
                    '$gte': start_datetime,
                    '$lte': end_datetime
                },
                'source': 'pos',
                'status': 'completed'
            }
            
            if cashier_id:
                query['cashier_id'] = cashier_id
            
            # Aggregation pipeline
            pipeline = [
                {'$match': query},
                {'$group': {
                    '_id': None,
                    'total_sales': {'$sum': '$total_amount'},
                    'total_transactions': {'$sum': 1},
                    'total_items_sold': {'$sum': {'$size': '$items'}},
                    'avg_transaction': {'$avg': '$total_amount'},
                    'payment_methods': {
                        '$push': {
                            'method': '$payment_method',
                            'amount': '$total_amount'
                        }
                    }
                }}
            ]
            
            result = list(self.sales_collection.aggregate(pipeline))
            
            if result:
                summary = result[0]
                summary.pop('_id', None)
                return summary
            
            return {
                'total_sales': 0,
                'total_transactions': 0,
                'total_items_sold': 0,
                'avg_transaction': 0,
                'payment_methods': []
            }
            
        except Exception as e:
            raise Exception(f"Error getting daily summary: {str(e)}")

    # ================================================================
    # HELPER METHODS
    # ================================================================
    
    def _send_sale_notification(self, sale_record, notification_type):
        """Send notification for sale creation"""
        try:
            total_amount = sale_record.get('total_amount', 0)
            
            title = "POS Sale Completed"
            message = f"New POS transaction completed for ₱{total_amount}"
            
            notification_service.create_notification(
                title=title,
                message=message,
                priority="low",
                notification_type="sales",
                metadata={
                    "sale_id": sale_record['_id'],
                    "total_amount": total_amount,
                    "source": "pos",
                    "payment_method": sale_record.get('payment_method', ''),
                    "cashier_id": sale_record.get('cashier_id', '')
                }
            )

        except Exception as notification_error:
            print(f"Failed to create sale notification: {notification_error}")

    def get_shift_summary(self, shift_id):
        """Get sales summary for a specific shift"""
        try:
            sales = self.get_sales_by_shift(shift_id)
            
            total_revenue = sum(sale['total_amount'] for sale in sales)
            total_transactions = len(sales)
            
            # Payment method breakdown
            payment_breakdown = {}
            for sale in sales:
                method = sale['payment_method']
                payment_breakdown[method] = payment_breakdown.get(method, 0) + sale['total_amount']
            
            return {
                'shift_id': shift_id,
                'total_revenue': round(total_revenue, 2),
                'total_transactions': total_transactions,
                'average_transaction': round(total_revenue / total_transactions, 2) if total_transactions else 0,
                'payment_breakdown': payment_breakdown,
                'transactions': sales
            }
            
        except Exception as e:
            raise Exception(f"Error getting shift summary: {str(e)}")
    
    def get_cashier_performance(self, cashier_id, start_date, end_date):
        """Get performance metrics for a cashier"""
        try:
            sales = self.get_sales_by_date_range(start_date, end_date, cashier_id)
            
            total_revenue = sum(sale['total_amount'] for sale in sales)
            total_transactions = len(sales)
            
            return {
                'cashier_id': cashier_id,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_revenue': round(total_revenue, 2),
                'total_transactions': total_transactions,
                'average_per_transaction': round(total_revenue / total_transactions, 2) if total_transactions else 0
            }
            
        except Exception as e:
            raise Exception(f"Error getting cashier performance: {str(e)}")
        
    def get_top_products(self, date, cashier_id=None, limit=10):
        """Get top selling products for a specific date"""
        try:
            from datetime import time
            
            start_datetime = datetime.combine(date, time.min)
            end_datetime = datetime.combine(date, time.max)
            
            query = {
                'transaction_date': {
                    '$gte': start_datetime,
                    '$lte': end_datetime
                },
                'source': 'pos',
                'status': 'completed'
            }
            
            if cashier_id:
                query['cashier_id'] = cashier_id
            
            # Aggregation pipeline for top products
            pipeline = [
                {'$match': query},
                {'$unwind': '$items'},
                {'$group': {
                    '_id': {
                        'product_id': '$items.product_id',
                        'product_name': '$items.product_name',
                        'sku': '$items.sku'
                    },
                    'total_quantity': {'$sum': '$items.quantity'},
                    'total_revenue': {'$sum': '$items.subtotal'},
                    'unit_price': {'$avg': '$items.unit_price'}
                }},
                {'$project': {
                    'product_id': '$_id.product_id',
                    'product_name': '$_id.product_name',
                    'sku': '$_id.sku',
                    'total_quantity': 1,
                    'total_revenue': 1,
                    'unit_price': 1,
                    'average_price': {'$round': ['$unit_price', 2]}
                }},
                {'$sort': {'total_revenue': -1}},
                {'$limit': limit}
            ]
            
            result = list(self.sales_collection.aggregate(pipeline))
            
            # Format the result
            formatted_products = []
            for product in result:
                formatted_products.append({
                    'id': product['product_id'],
                    'name': product['product_name'],
                    'sku': product.get('sku', ''),
                    'orders': product['total_quantity'],  # This is actually quantity sold
                    'ppu': product['average_price'],
                    'revenue': product['total_revenue']
                })
            
            return formatted_products
            
        except Exception as e:
            raise Exception(f"Error getting top products: {str(e)}")