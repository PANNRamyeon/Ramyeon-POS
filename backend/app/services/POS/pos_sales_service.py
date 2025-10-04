from datetime import datetime
from ...database import db_manager
from ..Backoffice.product_service import ProductService
from notifications.services import notification_service

class POSSalesService:
    """
    POS transaction processing - String ID version
    Handles ONLY POS sales (sales collection)
    """
    def __init__(self):
        self.db = db_manager.get_database()
        self.sales_collection = self.db.sales 
        self.products_collection = self.db.products
        self.product_service = ProductService()

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
    # CORE SALES OPERATIONS
    # ================================================================
    
    def create_sale(self, sale_data, cashier_id):
        """
        Create POS sale transaction
        
        Args:
            sale_data: {
                'items': [...],
                'subtotal': float,
                'tax_amount': float,
                'discount_amount': float,
                'total_amount': float,
                'payment_method': str,
                'customer_id': str (optional)
            }
            cashier_id: str (USER-#### format)
        """
        try:
            sale_id = self.generate_sale_id()
            
            sale_record = {
                '_id': sale_id,  # ✅ String ID
                'items': sale_data['items'],
                'subtotal': sale_data.get('subtotal', 0),
                'tax_amount': sale_data.get('tax_amount', 0),
                'discount_amount': sale_data.get('discount_amount', 0),
                'total_amount': sale_data['total_amount'],
                'payment_method': sale_data['payment_method'],
                'payment_details': sale_data.get('payment_details', {}),
                'cashier_id': cashier_id,
                'customer_id': sale_data.get('customer_id'),
                'promotion_applied': sale_data.get('promotion_applied'),
                'transaction_date': datetime.utcnow(),
                'status': 'completed',
                'source': 'pos',
                'created_at': datetime.utcnow()
            }

            # Insert sale
            self.sales_collection.insert_one(sale_record)
            
            # Update stock for each item
            for item in sale_data['items']:
                self.product_service.adjust_stock_for_sale(
                    item['product_id'],
                    item['quantity']
                )

            # Send notification
            self._send_sale_notification(sale_record, 'pos_sale_created')

            return {
                'success': True,
                'message': 'POS sale created successfully',
                'data': sale_record
            }

        except Exception as e:
            raise Exception(f"Error creating POS sale: {str(e)}")
    
    def get_sale_by_id(self, sale_id):
        """Get a POS sale by string ID"""
        try:
            # ✅ Direct string lookup - no ObjectId conversion
            sale = self.sales_collection.find_one({'_id': sale_id})
            return sale  # Already clean, no conversion needed
            
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
            
            return sales  # Already clean with string IDs
            
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
        Void a sale - requires manager approval
        Restores product stock
        """
        try:
            # Get original sale
            sale = self.get_sale_by_id(sale_id)
            if not sale:
                raise ValueError("Sale not found")
            
            if sale['status'] == 'voided':
                raise ValueError("Sale already voided")
            
            # Restore stock for each item
            for item in sale['items']:
                # Add stock back (opposite of adjust_stock_for_sale)
                self.product_service.restock_product(
                    item['product_id'],
                    item['quantity'],
                    {'reason': f'Sale void: {sale_id}'}
                )
            
            # Update sale status
            result = self.sales_collection.update_one(
                {'_id': sale_id},
                {
                    '$set': {
                        'status': 'voided',
                        'void_reason': reason,
                        'voided_by': manager_id,
                        'voided_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Send notification
                notification_service.create_notification(
                    title="Sale Voided",
                    message=f"Sale {sale_id} voided by manager",
                    priority="high",
                    notification_type="alert",
                    metadata={
                        'sale_id': sale_id,
                        'reason': reason,
                        'voided_by': manager_id
                    }
                )
                
                return self.get_sale_by_id(sale_id)
            
            return None
            
        except Exception as e:
            raise Exception(f"Error voiding sale: {str(e)}")

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