from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ...services.POS.online_transactions_service import OnlineTransactionService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CreateOnlineOrderView(APIView):
    """
    POST /api/online/orders/create/
    
    Create a new online order
    """
    
    def post(self, request):
        try:
            # Get service
            online_service = OnlineTransactionService()
            
            # Extract data
            customer_id = request.data.get('customer_id')
            items = request.data.get('items', [])
            delivery_address = request.data.get('delivery_address', {})
            payment_method = request.data.get('payment_method', 'cod')
            points_to_redeem = request.data.get('points_to_redeem', 0)
            notes = request.data.get('notes', '')
            
            # Validation
            if not customer_id:
                return Response({
                    'success': False,
                    'message': 'Customer ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not items or len(items) == 0:
                return Response({
                    'success': False,
                    'message': 'Order must contain at least one item'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not delivery_address:
                return Response({
                    'success': False,
                    'message': 'Delivery address is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate payment method
            valid_payment_methods = ['cod', 'gcash_paymongo', 'bank_paymongo']
            if payment_method not in valid_payment_methods:
                return Response({
                    'success': False,
                    'message': f'Invalid payment method. Must be one of: {valid_payment_methods}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Prepare order data
            order_data = {
                'items': items,
                'delivery_address': delivery_address,
                'payment_method': payment_method,
                'points_to_redeem': points_to_redeem,
                'notes': notes
            }
            
            # Create order
            result = online_service.create_online_order(order_data, customer_id)
            
            return Response({
                'success': True,
                'message': 'Order created successfully',
                'data': {
                    'order': result['data']['order'],
                    'order_id': result['data']['order_id']
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            logger.error(f"Validation error creating order: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error creating online order: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to create order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetOrderView(APIView):
    """
    GET /api/online/orders/{order_id}/
    
    Get single order by ID
    """
    
    def get(self, request, order_id):
        try:
            online_service = OnlineTransactionService()
            
            order = online_service.get_order_by_id(order_id)
            
            if not order:
                return Response({
                    'success': False,
                    'message': f'Order {order_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'data': {
                    'order': order
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching order: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to fetch order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetCustomerOrdersView(APIView):
    """
    GET /api/online/orders/customer/{customer_id}/
    
    Get all orders for a customer
    Query params: ?status=pending (optional)
    """
    
    def get(self, request, customer_id):
        try:
            online_service = OnlineTransactionService()
            
            # Get optional status filter
            status_filter = request.query_params.get('status', None)
            limit = int(request.query_params.get('limit', 50))
            
            orders = online_service.get_customer_orders(
                customer_id, 
                status=status_filter,
                limit=limit
            )
            
            return Response({
                'success': True,
                'data': {
                    'orders': orders,
                    'total_count': len(orders),
                    'customer_id': customer_id,
                    'status_filter': status_filter
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching customer orders: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to fetch orders: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetAllOrdersView(APIView):
    """
    GET /api/online/orders/
    
    Get all orders with optional filters (staff only)
    Query params:
        ?status=pending
        &payment_status=paid
        &start_date=2025-10-01
        &end_date=2025-10-31
        &customer_id=CUST-00002
        &limit=100
    """
    
    def get(self, request):
        try:
            online_service = OnlineTransactionService()
            
            # Build filters from query params
            filters = {}
            
            if request.query_params.get('status'):
                filters['status'] = request.query_params.get('status')
            
            if request.query_params.get('payment_status'):
                filters['payment_status'] = request.query_params.get('payment_status')
            
            if request.query_params.get('customer_id'):
                filters['customer_id'] = request.query_params.get('customer_id')
            
            if request.query_params.get('start_date'):
                try:
                    filters['start_date'] = datetime.fromisoformat(
                        request.query_params.get('start_date')
                    )
                except:
                    pass
            
            if request.query_params.get('end_date'):
                try:
                    filters['end_date'] = datetime.fromisoformat(
                        request.query_params.get('end_date')
                    )
                except:
                    pass
            
            limit = int(request.query_params.get('limit', 100))
            
            orders = online_service.get_all_orders(filters=filters, limit=limit)
            
            return Response({
                'success': True,
                'data': {
                    'orders': orders,
                    'total_count': len(orders),
                    'filters_applied': filters
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching all orders: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to fetch orders: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelOrderView(APIView):
    """
    POST /api/online/orders/{order_id}/cancel/
    
    Cancel an order and restore stock/points
    """
    
    def post(self, request, order_id):
        try:
            online_service = OnlineTransactionService()
            
            # Extract data
            cancellation_reason = request.data.get('cancellation_reason', 'No reason provided')
            cancelled_by = request.data.get('cancelled_by')
            
            if not cancelled_by:
                return Response({
                    'success': False,
                    'message': 'cancelled_by is required (CUST-#### or USER-####)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Cancel order
            updated_order = online_service.cancel_online_order(
                order_id,
                cancellation_reason,
                cancelled_by
            )
            
            return Response({
                'success': True,
                'message': 'Order cancelled successfully',
                'data': {
                    'order': updated_order,
                    'stock_restored': updated_order.get('stock_restored', False),
                    'points_refunded': updated_order.get('points_refunded', False)
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Validation error cancelling order: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to cancel order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateOrderStatusView(APIView):
    """
    PATCH /api/online/orders/{order_id}/status/
    
    Update order status (staff only)
    """
    
    def patch(self, request, order_id):
        try:
            online_service = OnlineTransactionService()
            
            # Extract data
            new_status = request.data.get('new_status')
            updated_by = request.data.get('updated_by')
            notes = request.data.get('notes', '')
            
            # Validation
            if not new_status:
                return Response({
                    'success': False,
                    'message': 'new_status is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not updated_by:
                return Response({
                    'success': False,
                    'message': 'updated_by is required (USER-#### or system)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Valid statuses
            valid_statuses = ['confirmed', 'processing', 'on_the_way', 'completed']
            if new_status not in valid_statuses:
                return Response({
                    'success': False,
                    'message': f'Invalid status. Must be one of: {valid_statuses}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update status
            updated_order = online_service.update_order_status(
                order_id,
                new_status,
                updated_by,
                notes
            )
            
            return Response({
                'success': True,
                'message': f'Order status updated to {new_status}',
                'data': {
                    'order': updated_order
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Validation error updating status: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to update status: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdatePaymentStatusView(APIView):
    """
    PATCH /api/online/orders/{order_id}/payment/
    
    Update payment status (for PayMongo confirmations)
    """
    
    def patch(self, request, order_id):
        try:
            online_service = OnlineTransactionService()
            
            # Extract data
            payment_status = request.data.get('payment_status')
            payment_reference = request.data.get('payment_reference', None)
            confirmed_by = request.data.get('confirmed_by')
            
            # Validation
            if not payment_status:
                return Response({
                    'success': False,
                    'message': 'payment_status is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            valid_payment_statuses = ['paid', 'failed', 'refunded']
            if payment_status not in valid_payment_statuses:
                return Response({
                    'success': False,
                    'message': f'Invalid payment status. Must be one of: {valid_payment_statuses}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update payment status
            updated_order = online_service.update_payment_status(
                order_id,
                payment_status,
                payment_reference,
                confirmed_by
            )
            
            # Check if order was auto-confirmed
            auto_confirmed = (
                payment_status == 'paid' and 
                updated_order['order_status'] == 'confirmed'
            )
            
            return Response({
                'success': True,
                'message': 'Payment status updated',
                'data': {
                    'order': updated_order,
                    'auto_confirmed': auto_confirmed
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Validation error updating payment: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error updating payment status: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to update payment: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarkReadyForDeliveryView(APIView):
    """
    POST /api/online/orders/{order_id}/ready-for-delivery/
    
    Mark order as ready for delivery (processing → on_the_way)
    """
    
    def post(self, request, order_id):
        try:
            online_service = OnlineTransactionService()
            
            # Extract data
            prepared_by = request.data.get('prepared_by')
            delivery_notes = request.data.get('delivery_notes', '')
            
            if not prepared_by:
                return Response({
                    'success': False,
                    'message': 'prepared_by is required (USER-####)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark ready
            updated_order = online_service.mark_ready_for_delivery(
                order_id,
                prepared_by,
                delivery_notes
            )
            
            return Response({
                'success': True,
                'message': 'Order marked as ready for delivery',
                'data': {
                    'order': updated_order
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Validation error marking ready: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error marking ready for delivery: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to mark ready: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompleteOrderView(APIView):
    """
    POST /api/online/orders/{order_id}/complete/
    
    Mark order as completed (delivered)
    """
    
    def post(self, request, order_id):
        try:
            online_service = OnlineTransactionService()
            
            # Extract data
            completed_by = request.data.get('completed_by')
            delivery_person = request.data.get('delivery_person', None)
            
            if not completed_by:
                return Response({
                    'success': False,
                    'message': 'completed_by is required (USER-####)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Complete order
            updated_order = online_service.complete_order(
                order_id,
                completed_by,
                delivery_person
            )
            
            return Response({
                'success': True,
                'message': 'Order completed successfully',
                'data': {
                    'order': updated_order,
                    'points_awarded': updated_order.get('loyalty_points_earned', 0)
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Validation error completing order: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error completing order: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to complete order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ValidateStockView(APIView):
    """
    POST /api/online/orders/validate-stock/
    
    Validate stock availability before checkout
    """
    
    def post(self, request):
        try:
            online_service = OnlineTransactionService()
            
            # Extract items
            items = request.data.get('items', [])
            
            if not items:
                return Response({
                    'success': False,
                    'message': 'items array is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate stock
            validation_result = online_service.validate_order_stock(items)
            
            return Response({
                'success': True,
                'data': validation_result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error validating stock: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to validate stock: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetOrderSummaryView(APIView):
    """
    GET /api/online/orders/summary/
    
    Get order summary/analytics for date range
    Query params: ?start_date=2025-10-01&end_date=2025-10-31
    """
    
    def get(self, request):
        try:
            online_service = OnlineTransactionService()
            
            # Parse dates
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            
            if not start_date_str or not end_date_str:
                return Response({
                    'success': False,
                    'message': 'start_date and end_date are required (YYYY-MM-DD format)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
            except:
                return Response({
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get summary
            summary = online_service.get_order_summary(start_date, end_date)
            
            return Response({
                'success': True,
                'data': summary
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting order summary: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to get summary: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================================================================
# LOYALTY POINTS VIEWS
# ================================================================

class GetCustomerPointsView(APIView):
    """
    GET /api/customers/{customer_id}/points/
    
    Get customer's loyalty points balance
    """
    
    def get(self, request, customer_id):
        try:
            from ...database import db_manager
            db = db_manager.get_database()
            customers_collection = db.customers
            
            customer = customers_collection.find_one({'_id': customer_id})
            
            if not customer:
                return Response({
                    'success': False,
                    'message': f'Customer {customer_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            total_points = customer.get('loyalty_points', 0)
            points_value = total_points / 4.0  # 4 points = ₱1
            
            # Get expiring points (within 30 days)
            expiring_soon = []
            points_transactions = customer.get('points_transactions', [])
            
            now = datetime.utcnow()
            thirty_days = now + timedelta(days=30)
            
            for txn in points_transactions:
                if txn.get('status') == 'active' and txn.get('expires_at'):
                    expires_at = txn['expires_at']
                    
                    if expires_at <= thirty_days and expires_at > now:
                        days_remaining = (expires_at - now).days
                        
                        expiring_soon.append({
                            'points': txn.get('points', 0),
                            'expires_at': expires_at.isoformat(),
                            'days_remaining': days_remaining
                        })
            
            return Response({
                'success': True,
                'data': {
                    'customer_id': customer_id,
                    'total_points': total_points,
                    'points_value': round(points_value, 2),
                    'expiring_soon': expiring_soon
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting customer points: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to get points: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetPointsHistoryView(APIView):
    """
    GET /api/customers/{customer_id}/points/history/
    
    Get customer's points transaction history
    """
    
    def get(self, request, customer_id):
        try:
            from ...database import db_manager
            db = db_manager.get_database()
            customers_collection = db.customers
            
            customer = customers_collection.find_one({'_id': customer_id})
            
            if not customer:
                return Response({
                    'success': False,
                    'message': f'Customer {customer_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            points_transactions = customer.get('points_transactions', [])
            
            # Calculate totals
            total_earned = sum(
                txn['points'] for txn in points_transactions 
                if txn.get('transaction_type') == 'earned'
            )
            
            total_redeemed = abs(sum(
                txn['points'] for txn in points_transactions 
                if txn.get('transaction_type') == 'redeemed'
            ))
            
            current_balance = customer.get('loyalty_points', 0)
            
            return Response({
                'success': True,
                'data': {
                    'customer_id': customer_id,
                    'transactions': points_transactions,
                    'total_earned': total_earned,
                    'total_redeemed': total_redeemed,
                    'current_balance': current_balance
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting points history: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to get history: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalculatePointsPreviewView(APIView):
    """
    POST /api/online/orders/calculate-points/
    
    Preview points calculation for an order
    """
    
    def post(self, request):
        try:
            online_service = OnlineTransactionService()
            
            subtotal = float(request.data.get('subtotal', 0))
            points_to_redeem = int(request.data.get('points_to_redeem', 0))
            
            if subtotal <= 0:
                return Response({
                    'success': False,
                    'message': 'subtotal must be greater than 0'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate discount
            points_discount = online_service.calculate_points_discount(points_to_redeem)
            subtotal_after_discount = subtotal - points_discount
            
            # Calculate points to earn
            points_will_earn = online_service.calculate_loyalty_points_earned(
                subtotal_after_discount
            )
            
            return Response({
                'success': True,
                'data': {
                    'subtotal': round(subtotal, 2),
                    'points_to_redeem': points_to_redeem,
                    'points_discount': round(points_discount, 2),
                    'subtotal_after_discount': round(subtotal_after_discount, 2),
                    'points_will_earn': points_will_earn
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error calculating points: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to calculate points: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)