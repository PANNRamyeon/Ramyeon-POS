from datetime import datetime, timedelta
from ...database import db_manager


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
    
    def validate_order_stock(self, items):
        """
        Validate stock availability for all items before order creation
        
        Args:
            items: list of {'product_id': str, 'quantity': int}
        
        Returns:
            dict: {
                'valid': bool,
                'errors': list,
                'stock_details': dict
            }
        """
        try:
            errors = []
            stock_details = {}
            
            for item in items:
                product_id = item['product_id']
                quantity = item['quantity']
                
                # Get product details
                product = self.products_collection.find_one({'_id': product_id})
                
                if not product:
                    errors.append(f"Product {product_id} not found")
                    continue
                
                # Check batch availability
                batch_check = self.batch_service.check_batch_availability(
                    product_id, 
                    quantity
                )
                
                stock_details[product_id] = {
                    'product_name': product.get('product_name', 'Unknown'),
                    'requested': quantity,
                    'available': batch_check['total_stock'],
                    'sufficient': batch_check['available']
                }
                
                if not batch_check['available']:
                    errors.append(
                        f"Insufficient stock for {product.get('product_name')}. "
                        f"Available: {batch_check['total_stock']}, Requested: {quantity}"
                    )
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'stock_details': stock_details
            }
            
        except Exception as e:
            logger.error(f"Stock validation error: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Stock validation failed: {str(e)}"],
                'stock_details': {}
            }
    
    # ================================================================
    # LOYALTY POINTS MANAGEMENT
    # ================================================================
    
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
    
    def deduct_customer_points(self, customer_id, points_to_deduct, order_id):
        """
        Deduct loyalty points from customer balance
        
        Args:
            customer_id: Customer ID
            points_to_deduct: Points to deduct
            order_id: Order ID for transaction history
        """
        try:
            customer = self.customers_collection.find_one({'_id': customer_id})
            
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            current_balance = customer.get('loyalty_points', 0)
            new_balance = current_balance - points_to_deduct
            
            # Create points transaction
            points_transaction = {
                'transaction_id': order_id,
                'transaction_type': 'redeemed',
                'points': -points_to_deduct,
                'balance_before': current_balance,
                'balance_after': new_balance,
                'description': f"Redeemed {points_to_deduct} points on order {order_id}",
                'created_at': datetime.utcnow()
            }
            
            # Update customer
            self.customers_collection.update_one(
                {'_id': customer_id},
                {
                    '$set': {'loyalty_points': new_balance},
                    '$push': {'points_transactions': points_transaction}
                }
            )
            
            logger.info(f"Deducted {points_to_deduct} points from {customer_id}")
            
        except Exception as e:
            logger.error(f"Error deducting points: {str(e)}")
            raise
    
    def award_loyalty_points(self, customer_id, points_to_award, order_id, order_amount):
        """
        Award loyalty points to customer when order is completed
        
        Args:
            customer_id: Customer ID
            points_to_award: Points to award
            order_id: Order ID
            order_amount: Order subtotal after discount
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
                'transaction_id': order_id,
                'transaction_type': 'earned',
                'points': points_to_award,
                'balance_before': current_balance,
                'balance_after': new_balance,
                'description': f"Earned from order {order_id} (₱{order_amount:.2f} purchase)",
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
                        'last_purchase': datetime.utcnow()
                    },
                    '$push': {'points_transactions': points_transaction}
                }
            )
            
            logger.info(f"Awarded {points_to_award} points to {customer_id}")
            
            # Send notification
            notification_service.create_notification(
                title="Loyalty Points Earned!",
                message=f"You earned {points_to_award} points from your order! New balance: {new_balance} points (₱{new_balance/4:.2f})",
                priority="low",
                notification_type="loyalty",
                metadata={
                    'customer_id': customer_id,
                    'order_id': order_id,
                    'points_earned': points_to_award,
                    'new_balance': new_balance
                }
            )
            
        except Exception as e:
            logger.error(f"Error awarding points: {str(e)}")
            raise
    
    def refund_customer_points(self, customer_id, points_to_refund, order_id):
        """
        Refund loyalty points when order is cancelled
        
        Args:
            customer_id: Customer ID
            points_to_refund: Points to refund
            order_id: Order ID
        """
        try:
            customer = self.customers_collection.find_one({'_id': customer_id})
            
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            current_balance = customer.get('loyalty_points', 0)
            new_balance = current_balance + points_to_refund
            
            # Create points transaction
            points_transaction = {
                'transaction_id': f"{order_id}-CANCEL",
                'transaction_type': 'refunded',
                'points': points_to_refund,
                'balance_before': current_balance,
                'balance_after': new_balance,
                'description': f"Refunded {points_to_refund} points from cancelled order {order_id}",
                'created_at': datetime.utcnow()
            }
            
            # Update customer
            self.customers_collection.update_one(
                {'_id': customer_id},
                {
                    '$set': {'loyalty_points': new_balance},
                    '$push': {'points_transactions': points_transaction}
                }
            )
            
            logger.info(f"Refunded {points_to_refund} points to {customer_id}")
            
        except Exception as e:
            logger.error(f"Error refunding points: {str(e)}")
            raise
    
    # ================================================================
    # CORE ORDER OPERATIONS
    # ================================================================
    
    def create_online_order(self, order_data, customer_id):
        """
        Create a new online order with FIFO batch deduction and usage_history tracking
        
        Args:
            order_data: Dictionary containing order information
            customer_id: Customer ID (CUST-##### format)
        
        Returns:
            Dictionary with success status and created order data
        """
        try:
            # Generate order ID
            order_id = self.generate_online_order_id()
            transaction_date = datetime.utcnow()
            
            print(f"\n{'='*60}")
            print(f"🛒 Creating Online Order: {order_id}")
            print(f"   Customer: {customer_id}")
            print(f"   Items: {len(order_data.get('items', []))}")
            print(f"{'='*60}\n")
            
            # Get customer details
            customer = self.customers_collection.find_one({'_id': customer_id})
            
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            # Step 1: Validate stock availability
            print("Step 1: Validating stock...")
            stock_validation = self.validate_order_stock(order_data.get('items', []))
            
            if not stock_validation['valid']:
                raise ValueError(f"Stock validation failed: {', '.join(stock_validation['errors'])}")
            
            print("✅ Stock validation passed\n")
            
            # Step 2: Calculate initial subtotal
            print("Step 2: Calculating pricing...")
            subtotal = 0
            items_with_prices = []
            
            for item in order_data.get('items', []):
                product = self.products_collection.find_one({'_id': item['product_id']})
                
                if not product:
                    raise ValueError(f"Product {item['product_id']} not found")
                
                unit_price = product.get('selling_price', 0)
                quantity = item['quantity']
                item_subtotal = unit_price * quantity
                
                items_with_prices.append({
                    'product_id': item['product_id'],
                    'product_name': product.get('product_name'),
                    'sku': product.get('SKU'),
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'subtotal': item_subtotal,
                    'is_taxable': product.get('is_taxable', True)
                })
                
                subtotal += item_subtotal
            
            print(f"   Subtotal: ₱{subtotal:.2f}")
            
            # Step 3: Apply points discount (if any)
            points_to_redeem = order_data.get('points_to_redeem', 0)
            points_discount = 0
            
            if points_to_redeem > 0:
                print(f"Step 3: Applying points discount ({points_to_redeem} points)...")
                
                # Validate points redemption
                points_validation = self.validate_points_redemption(
                    customer_id, 
                    points_to_redeem, 
                    subtotal
                )
                
                if not points_validation['valid']:
                    raise ValueError(points_validation['error'])
                
                points_discount = self.calculate_points_discount(points_to_redeem)
                
                # Deduct points from customer
                self.deduct_customer_points(customer_id, points_to_redeem, order_id)
                
                print(f"   Points discount: ₱{points_discount:.2f}")
            
            subtotal_after_discount = subtotal - points_discount
            print(f"   Subtotal after discount: ₱{subtotal_after_discount:.2f}")
            
            # Step 4: Calculate fees
            delivery_fee = 50.00
            payment_method = order_data.get('payment_method', 'cod')
            service_fee_data = self.calculate_service_fee(
                subtotal_after_discount,
                delivery_fee,
                payment_method
            )
            service_fee = service_fee_data['service_fee']
            
            print(f"   Delivery fee: ₱{delivery_fee:.2f}")
            print(f"   Service fee: ₱{service_fee:.2f}")
            
            # Step 5: Calculate total
            total_amount = subtotal_after_discount + delivery_fee + service_fee
            print(f"   TOTAL: ₱{total_amount:.2f}\n")
            
            # Step 6: Calculate loyalty points to be earned
            loyalty_points_earned = self.calculate_loyalty_points_earned(subtotal_after_discount)
            print(f"Step 4: Loyalty points to earn: {loyalty_points_earned} points\n")
            
            # Step 7: Build order record
            print("Step 5: Processing order items with FIFO...\n")
            
            order_record = {
                '_id': order_id,
                'customer_id': customer_id,
                'customer_name': customer.get('full_name'),
                'customer_email': customer.get('email'),
                'customer_phone': customer.get('phone'),
                'transaction_date': transaction_date,
                'delivery_address': order_data.get('delivery_address', {}),
                'items': [],  # Will be populated with batch tracking
                'subtotal': round(subtotal, 2),
                'points_redeemed': points_to_redeem,
                'points_discount': round(points_discount, 2),
                'subtotal_after_discount': round(subtotal_after_discount, 2),
                'delivery_fee': delivery_fee,
                'service_fee': service_fee,
                'service_fee_breakdown': service_fee_data['breakdown'],
                'total_amount': round(total_amount, 2),
                'payment_method': payment_method,
                'payment_status': 'pending',
                'payment_reference': None,
                'payment_confirmed_by': None,
                'payment_confirmed_at': None,
                'paymongo_payment_id': None,
                'order_status': 'pending',
                'status_history': [
                    {
                        'status': 'pending',
                        'timestamp': transaction_date,
                        'updated_by': 'system',
                        'notes': 'Order created'
                    }
                ],
                'loyalty_points_earned': loyalty_points_earned,
                'loyalty_points_used': points_to_redeem,
                'points_awarded': False,
                'is_cancelled': False,
                'cancellation_reason': None,
                'cancelled_by': None,
                'cancelled_at': None,
                'stock_restored': False,
                'points_refunded': False,
                'prepared_by': None,
                'ready_at': None,
                'delivered_at': None,
                'delivery_person': None,
                'source': 'online',
                'created_at': transaction_date,
                'updated_at': transaction_date,
                'notes': order_data.get('notes', '')
            }
            
            # Step 8: Process each item with FIFO batch deduction
            for item in items_with_prices:
                product_id = item['product_id']
                quantity_needed = item['quantity']
                
                print(f"📦 Processing: {item['product_name']} ({product_id}) x{quantity_needed}")
                
                # ✅ PREPARE TRANSACTION INFO FOR USAGE_HISTORY
                transaction_info = {
                    'transaction_id': order_id,
                    'adjusted_by': customer_id,
                    'source': 'online_order'
                }
                
                # ✅ Deduct from batches using FIFO with transaction tracking
                batch_deductions = self.batch_service.deduct_stock_fifo(
                    product_id,
                    quantity_needed,
                    transaction_date,
                    transaction_info=transaction_info  # ✅ Pass transaction info
                )
                
                # Add batches_used to item
                item['batches_used'] = batch_deductions
                
                # Add item to order
                order_record['items'].append(item)
                
                # Do not update product.stock; BatchService handles total_stock recomputation
            
            # Step 9: Insert order record
            self.online_transactions.insert_one(order_record)
            
            # Step 10: Auto-confirm COD orders
            if payment_method == 'cod':
                print("Step 6: Auto-confirming COD order...")
                self.update_order_status(order_id, 'confirmed', 'system')
            
            print(f"{'='*60}")
            print(f"✅ Online order created successfully: {order_id}")
            print(f"{'='*60}\n")
            
            # Step 11: Send notifications
            self._send_order_notification('new_order_created', order_id)
            
            return {
                'success': True,
                'message': 'Order created successfully',
                'data': {
                    'order': order_record,
                    'order_id': order_id,
                    'auto_confirmed': payment_method == 'cod'
                }
            }
            
        except ValueError as e:
            print(f"❌ Validation error: {str(e)}")
            
            # Rollback: Refund points if they were deducted
            if 'points_to_redeem' in locals() and points_to_redeem > 0:
                try:
                    self.refund_customer_points(customer_id, points_to_redeem, f"{order_id}-ROLLBACK")
                except:
                    pass
            
            raise
            
        except Exception as e:
            print(f"❌ Unexpected error creating online order: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Rollback: Refund points if they were deducted
            if 'points_to_redeem' in locals() and points_to_redeem > 0:
                try:
                    self.refund_customer_points(customer_id, points_to_redeem, f"{order_id}-ROLLBACK")
                except:
                    pass
            
            raise Exception(f"Error creating online order: {str(e)}")
    
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
                'updated_at': now
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
                'updated_at': now
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
                'updated_at': now
            },
             '$push': {'status_history': {'status': 'cancelled', 'timestamp': now}}}
        )
        return self.online_transactions.find_one({'_id': order_id})

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
