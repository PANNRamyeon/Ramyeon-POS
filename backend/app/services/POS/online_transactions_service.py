from datetime import datetime, timedelta
from ...database import db_manager
import logging

logger = logging.getLogger(__name__)

class OnlineTransactionService:
    """Service class handling all online order operations."""

    def __init__(self):
        self.db = db_manager.get_database()
        self.customers = self.db.customers
        self.online_transactions = self.db.online_transactions
        self.products = self.db.products  # assuming product stock is managed here

    # ================================================================
    # HELPER METHODS
    # ================================================================

    def _generate_order_id(self) -> str:
        count = self.online_transactions.count_documents({}) + 1
        return f"ONLINE-{count:06d}"

    def _compute_items(self, items):
        computed = []
        subtotal = 0.0
        for item in items or []:
            price = float(item.get('price', 0))
            qty = int(item.get('quantity', 1))
            line_subtotal = round(price * qty, 2)
            computed.append({
                'product_id': item.get('product_id') or item.get('id'),
                'product_name': item.get('name') or item.get('product_name'),
                'quantity': qty,
                'price': price,
                'subtotal': line_subtotal,
            })
            subtotal += line_subtotal
        return computed, round(subtotal, 2)

    def _compute_fees(self, delivery_type: str):
        delivery_fee = 50.0 if (delivery_type or '').lower() == 'delivery' else 0.0
        service_fee = 15.0
        return round(delivery_fee, 2), round(service_fee, 2)

    def _compute_points_discount(self, points_to_redeem: int, subtotal: float):
        try:
            pts = int(points_to_redeem or 0)
        except Exception:
            pts = 0
        discount = round(pts / 4.0, 2)  # 4 points = ₱1
        return float(min(discount, subtotal)), pts

    def _compute_points_earned(self, subtotal_after_discount: float) -> int:
        # Earn rate: 20% of order value
        return int(round(subtotal_after_discount * 0.20))

    # ================================================================
    # ORDER CREATION
    # ================================================================

    def create_online_order(self, order_data: dict, customer_id: str):
        if not customer_id:
            raise ValueError("customer_id is required")

        items_in = order_data.get('items', [])
        delivery_address = order_data.get('delivery_address', {})
        payment_method = order_data.get('payment_method', 'cod')
        delivery_type = order_data.get('delivery_type', 'delivery')
        points_to_redeem = int(order_data.get('points_to_redeem', 0) or 0)
        notes = order_data.get('notes', '')

        # Lookup customer (allow guest orders)
        customer = self.customers.find_one({'_id': customer_id}) if customer_id else None

        # Compute order values
        items, subtotal = self._compute_items(items_in)
        points_discount, pts_used = self._compute_points_discount(points_to_redeem, subtotal)
        subtotal_after_discount = round(subtotal - points_discount, 2)
        delivery_fee, service_fee = self._compute_fees(delivery_type)
        total_amount = round(subtotal_after_discount + delivery_fee + service_fee, 2)

        order_id = self._generate_order_id()
        now_utc = datetime.utcnow()
        now_local = now_utc + timedelta(hours=8)  # Asia/Manila

        order_record = {
            '_id': order_id,
            'customer_id': customer_id or 'GUEST',
            'customer_name': customer.get('full_name') if customer else 'Guest',
            'customer_email': customer.get('email') if customer else None,
            'transaction_date': now_utc,
            'transaction_date_local': now_local,
            'timezone': 'Asia/Manila',
            'delivery_address': delivery_address,
            'delivery_type': delivery_type,
            'items': items,
            'subtotal': subtotal,
            'points_redeemed': pts_used,
            'points_discount': points_discount,
            'subtotal_after_discount': subtotal_after_discount,
            'delivery_fee': delivery_fee,
            'service_fee': service_fee,
            'total_amount': total_amount,
            'payment_method': payment_method,
            'payment_status': 'pending',
            'order_status': 'pending',
            'status': 'pending',
            'notes': notes,
            'status_history': [{'status': 'pending', 'timestamp': now_utc}],
            'loyalty_points_earned': self._compute_points_earned(subtotal_after_discount),
            'created_at': now_utc,
            'updated_at': now_utc,
            'last_status_change': now_utc,  # Track when status was last changed
        }

        self.online_transactions.insert_one(order_record)
        return {'success': True, 'data': {'order_id': order_id, 'order': order_record}}

    # ================================================================
    # ORDER STATUS & PAYMENT UPDATES
    # ================================================================

    def update_order_status(self, order_id, new_status, updated_by, notes=''):
        order = self.online_transactions.find_one({'_id': order_id})
        if not order:
            raise ValueError(f"Order {order_id} not found")

        now = datetime.utcnow()
        self.online_transactions.update_one(
            {'_id': order_id},
            {'$set': {
                'order_status': new_status,
                'status': new_status,
                'updated_at': now,
                'last_status_change': now,  # Update status change timestamp
                'updated_by': updated_by,
                'notes': notes
            },
             '$push': {'status_history': {'status': new_status, 'timestamp': now}}}
        )
        return self.online_transactions.find_one({'_id': order_id})

    def update_payment_status(self, order_id, payment_status, payment_reference, confirmed_by):
        order = self.online_transactions.find_one({'_id': order_id})
        if not order:
            raise ValueError(f"Order {order_id} not found")

        now = datetime.utcnow()
        update_data = {
            'payment_status': payment_status,
            'payment_reference': payment_reference,
            'updated_at': now,
            'confirmed_by': confirmed_by
        }

        # Auto-confirm order when payment is successful
        if payment_status == 'paid' and order.get('order_status') == 'pending':
            update_data['order_status'] = 'confirmed'
            update_data['status'] = 'confirmed'
            update_data['last_status_change'] = now  # Update status change timestamp

        self.online_transactions.update_one({'_id': order_id}, {'$set': update_data})
        return self.online_transactions.find_one({'_id': order_id})

    # ================================================================
    # ORDER ACTIONS (READY, COMPLETE, CANCEL)
    # ================================================================

    def mark_ready_for_delivery(self, order_id, prepared_by, delivery_notes=''):
        order = self.online_transactions.find_one({'_id': order_id})
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.get('order_status') not in ['processing', 'confirmed']:
            raise ValueError(f"Cannot mark order {order_id} as ready-for-delivery from status {order.get('order_status')}")

        now = datetime.utcnow()
        self.online_transactions.update_one(
            {'_id': order_id},
            {'$set': {
                'order_status': 'on_the_way',
                'status': 'on_the_way',
                'prepared_by': prepared_by,
                'delivery_notes': delivery_notes,
                'updated_at': now,
                'last_status_change': now,  # Update status change timestamp
            },
             '$push': {'status_history': {'status': 'on_the_way', 'timestamp': now}}}
        )

        return self.online_transactions.find_one({'_id': order_id})

    def complete_order(self, order_id, completed_by, delivery_person=None):
        order = self.online_transactions.find_one({'_id': order_id})
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.get('order_status') not in ['on_the_way']:
            raise ValueError(f"Cannot complete order {order_id} from status {order.get('order_status')}")

        now = datetime.utcnow()
        self.online_transactions.update_one(
            {'_id': order_id},
            {'$set': {
                'order_status': 'completed',
                'status': 'completed',
                'completed_by': completed_by,
                'delivery_person': delivery_person,
                'updated_at': now,
                'last_status_change': now,  # Update status change timestamp
            },
             '$push': {'status_history': {'status': 'completed', 'timestamp': now}}}
        )

        return self.online_transactions.find_one({'_id': order_id})

    def cancel_online_order(self, order_id, reason, cancelled_by):
        order = self.online_transactions.find_one({'_id': order_id})
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.get('order_status') in ['completed', 'cancelled']:
            raise ValueError(f"Cannot cancel order {order_id} (already {order.get('order_status')})")

        now = datetime.utcnow()
        self.online_transactions.update_one(
            {'_id': order_id},
            {'$set': {
                'order_status': 'cancelled',
                'status': 'cancelled',
                'cancelled_by': cancelled_by,
                'cancellation_reason': reason,
                'updated_at': now,
                'last_status_change': now,  # Update status change timestamp
            },
             '$push': {'status_history': {'status': 'cancelled', 'timestamp': now}}}
        )
        return self.online_transactions.find_one({'_id': order_id})

    # ================================================================
    # AUTOMATIC CANCELLATION FOR STALE PENDING ORDERS
    # ================================================================

    def auto_cancel_stale_pending_orders(self, timeout_minutes=30):
        """
        Automatically cancel orders that have been in 'pending' status 
        for more than the specified timeout period.
        
        Args:
            timeout_minutes: Number of minutes after which pending orders should be auto-cancelled
            
        Returns:
            dict: Results of the auto-cancellation operation
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        # Find orders that are still pending and haven't had status change for more than timeout
        stale_orders = self.online_transactions.find({
            'order_status': 'pending',
            'last_status_change': {'$lt': cutoff_time}
        })
        
        cancelled_orders = []
        failed_cancellations = []
        
        for order in stale_orders:
            try:
                order_id = order['_id']
                logger.info(f"Auto-cancelling stale pending order: {order_id}")
                
                # Use the existing cancel method but with system as the canceller
                cancelled_order = self.cancel_online_order(
                    order_id=order_id,
                    reason=f"Automatically cancelled by system - order stuck in pending status for more than {timeout_minutes} minutes",
                    cancelled_by="system"
                )
                
                cancelled_orders.append({
                    'order_id': order_id,
                    'customer_id': order.get('customer_id'),
                    'total_amount': order.get('total_amount'),
                    'cancelled_at': datetime.utcnow()
                })
                
                logger.info(f"Successfully auto-cancelled order: {order_id}")
                
            except Exception as e:
                error_msg = f"Failed to auto-cancel order {order.get('_id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                failed_cancellations.append({
                    'order_id': order.get('_id'),
                    'error': str(e)
                })
        
        return {
            'success': True,
            'cancelled_count': len(cancelled_orders),
            'failed_count': len(failed_cancellations),
            'cancelled_orders': cancelled_orders,
            'failed_cancellations': failed_cancellations,
            'timestamp': datetime.utcnow()
        }

    def get_stale_pending_orders(self, timeout_minutes=30):
        """
        Get list of orders that are stuck in pending status beyond the timeout period.
        Useful for monitoring and manual review.
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        stale_orders = list(self.online_transactions.find({
            'order_status': 'pending',
            'last_status_change': {'$lt': cutoff_time}
        }).sort('last_status_change', 1))  # Sort by oldest first
        
        return {
            'count': len(stale_orders),
            'timeout_minutes': timeout_minutes,
            'cutoff_time': cutoff_time,
            'stale_orders': [
                {
                    'order_id': order['_id'],
                    'customer_id': order.get('customer_id'),
                    'customer_name': order.get('customer_name'),
                    'total_amount': order.get('total_amount'),
                    'last_status_change': order.get('last_status_change'),
                    'created_at': order.get('created_at'),
                    'minutes_stale': int((datetime.utcnow() - order.get('last_status_change')).total_seconds() / 60)
                }
                for order in stale_orders
            ]
        }

    # ================================================================
    # VALIDATION & REPORTING
    # ================================================================

    def validate_order_stock(self, items):
        unavailable = []
        for item in items:
            product_id = item.get('product_id')
            qty = int(item.get('quantity', 1))
            product = self.products.find_one({'_id': product_id})
            if not product or product.get('stock', 0) < qty:
                unavailable.append({'product_id': product_id, 'available': product.get('stock', 0) if product else 0})
        return {'unavailable': unavailable, 'valid': len(unavailable) == 0}

    def get_order_summary(self, start_date, end_date):
        cursor = self.online_transactions.find({
            'transaction_date': {'$gte': start_date, '$lte': end_date}
        })

        total_orders = 0
        total_sales = 0.0
        completed_orders = 0

        for doc in cursor:
            total_orders += 1
            total_sales += float(doc.get('total_amount', 0))
            if doc.get('order_status') == 'completed':
                completed_orders += 1

        return {
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'total_sales': round(total_sales, 2)
        }

    # ================================================================
    # DATA FETCH HELPERS
    # ================================================================

    def get_order_by_id(self, order_id):
        return self.online_transactions.find_one({'_id': order_id})

    def get_customer_orders(self, customer_id, status=None, limit=50):
        query = {'customer_id': customer_id}
        if status:
            query['status'] = status
        return list(self.online_transactions.find(query).sort('created_at', -1).limit(limit))

    def get_all_orders(self, filters=None, limit=100):
        filters = filters or {}
        query = {}
        if 'status' in filters:
            query['status'] = filters['status']
        if 'payment_status' in filters:
            query['payment_status'] = filters['payment_status']
        if 'customer_id' in filters:
            query['customer_id'] = filters['customer_id']

        if 'start_date' in filters or 'end_date' in filters:
            query['transaction_date'] = {}
            if 'start_date' in filters:
                query['transaction_date']['$gte'] = filters['start_date']
            if 'end_date' in filters:
                query['transaction_date']['$lte'] = filters['end_date']

        return list(self.online_transactions.find(query).sort('created_at', -1).limit(limit))