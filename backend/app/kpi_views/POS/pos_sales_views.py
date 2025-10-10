from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, date, time
from django.http import HttpResponse
import csv
from ...services.POS.pos_sales_service import POSSalesService
from ...services.Backoffice.user_service import UserService


class POSSalesCreateView(APIView):
    """
    POST /api/pos/sales/
    Create a new POS sale transaction
    """ 
    def post(self, request):
        try:
            pos_service = POSSalesService()
            
            # Get cashier_id from authenticated user
            cashier_id = request.user.username  # Assuming username is USER-#### format
            
            # Validate required fields
            required_fields = ['items', 'total_amount', 'payment_method']
            for field in required_fields:
                if field not in request.data:
                    return Response({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate items array
            if not request.data['items'] or len(request.data['items']) == 0:
                return Response({
                    'success': False,
                    'error': 'Sale must contain at least one item'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate each item has required fields
            for item in request.data['items']:
                item_required = ['product_id', 'quantity', 'unit_price', 'subtotal']
                for field in item_required:
                    if field not in item:
                        return Response({
                            'success': False,
                            'error': f'Item missing required field: {field}'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            # Prepare sale data
            sale_data = {
                'items': request.data['items'],
                'subtotal': request.data.get('subtotal', 0),
                'tax_amount': request.data.get('tax_amount', 0),
                'discount_amount': request.data.get('discount_amount', 0),
                'total_amount': request.data['total_amount'],
                'payment_method': request.data['payment_method'],
                'payment_details': request.data.get('payment_details', {}),
                'customer_id': request.data.get('customer_id'),
                'promotion_applied': request.data.get('promotion_applied'),
                'shift_id': request.data.get('shift_id')  # Optional shift tracking
            }
            
            # Create the sale
            result = pos_service.create_sale(sale_data, cashier_id)
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to create sale: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class POSSalesDetailView(APIView):
    """
    GET /api/pos/sales/{sale_id}/
    Get details of a specific sale
    """
    
    def get(self, request, sale_id):
        try:
            pos_service = POSSalesService()
            
            sale = pos_service.get_sale_by_id(sale_id)
            
            if not sale:
                return Response({
                    'success': False,
                    'error': 'Sale not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'data': sale
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to retrieve sale: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class POSSalesListView(APIView):
    """
    GET /api/v1/pos/sales/
    List POS sales with filtering and pagination
    """
  
    def get(self, request):
        try:
            pos_service = POSSalesService()
            
            # Get query parameters
            limit = int(request.query_params.get('limit', 50))
            cashier_id = request.query_params.get('cashier_id')
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            shift_id = request.query_params.get('shift_id')
            status_filter = request.query_params.get('status')
            
            # Determine which query to use based on parameters
            if shift_id:
                # Get sales by shift
                sales = pos_service.get_sales_by_shift(shift_id)
                
            elif start_date_str and end_date_str:
                # Parse dates and set time to cover full day
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                # Set end_date to end of day (23:59:59)
                from datetime import time
                end_date = datetime.combine(end_date.date(), time(23, 59, 59))
                
                print(f"DEBUG: Searching from {start_date} to {end_date}")  # Debug line
                
                # Get sales by date range
                sales = pos_service.get_sales_by_date_range(
                    start_date, 
                    end_date, 
                    cashier_id
                )
                
            else:
                # Get recent sales
                sales = pos_service.get_recent_sales(limit, cashier_id)
            
            # Apply status filter if provided
            if status_filter:
                sales = [sale for sale in sales if sale.get('status') == status_filter]
            
            # Debug: Print what we found
            print(f"DEBUG: Found {len(sales)} sales")
            if sales:
                print(f"DEBUG: First sale date: {sales[0].get('transaction_date')}")
            
            return Response({
                'success': True,
                'data': sales,
                'count': len(sales)
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'Invalid parameter: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            import traceback
            print(f"ERROR: {traceback.format_exc()}")  # Debug line
            return Response({
                'success': False,
                'error': f'Failed to retrieve sales: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class POSSalesVoidView(APIView):
    """
    POST /api/pos/sales/{sale_id}/void/
    Void a sale transaction (requires manager approval)
    
    Request Body:
    {
        "reason": "Customer return",
        "manager_id": "USER-0010"
    }
    """
    
    def post(self, request, sale_id):
        try:
            pos_service = POSSalesService()
            user_service = UserService()
            
            # Validate required fields
            if 'reason' not in request.data:
                return Response({
                    'success': False,
                    'error': 'Void reason is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if 'manager_id' not in request.data:
                return Response({
                    'success': False,
                    'error': 'Manager ID is required for approval'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify manager exists and has proper role
            manager = user_service.get_user_by_id(request.data['manager_id'])
            if not manager:
                return Response({
                    'success': False,
                    'error': 'Manager not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user has manager role (optional - add if you have roles)
            # if manager.get('role') not in ['manager', 'admin']:
            #     return Response({
            #         'success': False,
            #         'error': 'User does not have manager privileges'
            #     }, status=status.HTTP_403_FORBIDDEN)
            
            # Void the sale
            voided_sale = pos_service.void_sale(
                sale_id=sale_id,
                reason=request.data['reason'],
                manager_id=request.data['manager_id']
            )
            
            if not voided_sale:
                return Response({
                    'success': False,
                    'error': 'Failed to void sale'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'success': True,
                'message': 'Sale voided successfully',
                'data': voided_sale
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to void sale: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class POSSalesDailySummaryView(APIView):
    """
    GET /api/pos/sales/daily-summary/
    Get daily sales summary
    
    Query Parameters:
    - date: Date to summarize (YYYY-MM-DD, default: today)
    - cashier_id: Filter by specific cashier (optional)
    """
    
    def get(self, request):
        try:
            pos_service = POSSalesService()
            
            # Get date parameter or use today
            date_str = request.query_params.get('date')
            if date_str:
                summary_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                summary_date = date.today()
            
            # Get optional cashier filter
            cashier_id = request.query_params.get('cashier_id')
            
            # Get summary
            summary = pos_service.get_daily_summary(summary_date, cashier_id)
            
            return Response({
                'success': True,
                'date': summary_date.isoformat(),
                'cashier_id': cashier_id,
                'data': summary
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'Invalid date format. Use YYYY-MM-DD: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to get daily summary: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class POSSalesShiftSummaryView(APIView):
    """
    GET /api/pos/sales/shift-summary/{shift_id}/
    Get sales summary for a specific shift
    """
      
    def get(self, request, shift_id):
        try:
            pos_service = POSSalesService()
            
            summary = pos_service.get_shift_summary(shift_id)
            
            return Response({
                'success': True,
                'data': summary
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to get shift summary: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class POSSalesCreateView(APIView):
    """
    POST /api/pos/sales/
    Create a new POS sale transaction
    """ 
    def post(self, request):
        try:
            pos_service = POSSalesService()
            
            # ✅ FIX: Get cashier_id from request data (sent by frontend)
            # The frontend should send this from authenticated user data
            cashier_id = request.data.get('cashier_id')
            
            # If not provided, try to get from authenticated user
            if not cashier_id:
                # Try different authentication methods
                if hasattr(request, 'current_user'):
                    cashier_id = request.current_user.get('_id') or request.current_user.get('user_id')
                elif hasattr(request.user, 'username'):
                    cashier_id = request.user.username
                else:
                    return Response({
                        'success': False,
                        'error': 'Cashier ID is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate required fields
            required_fields = ['items', 'total_amount', 'payment_method']
            for field in required_fields:
                if field not in request.data:
                    return Response({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate items array
            if not request.data['items'] or len(request.data['items']) == 0:
                return Response({
                    'success': False,
                    'error': 'Sale must contain at least one item'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate each item has required fields
            for item in request.data['items']:
                item_required = ['product_id', 'quantity', 'unit_price', 'subtotal']
                for field in item_required:
                    if field not in item:
                        return Response({
                            'success': False,
                            'error': f'Item missing required field: {field}'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ Prepare sale data with cashier_id and shift_id
            sale_data = {
                'items': request.data['items'],
                'subtotal': request.data.get('subtotal', 0),
                'tax_amount': request.data.get('tax_amount', 0),
                'discount_amount': request.data.get('discount_amount', 0),
                'total_amount': request.data['total_amount'],
                'payment_method': request.data['payment_method'],
                'payment_details': request.data.get('payment_details', {}),
                'customer_id': request.data.get('customer_id'),
                'promotion_applied': request.data.get('promotion_applied'),
                'shift_id': request.data.get('shift_id')  # ✅ Get shift_id from request
            }
            
            # ✅ Log for debugging
            print(f"Creating sale with cashier_id: {cashier_id}, shift_id: {sale_data.get('shift_id')}")
            
            # Create the sale
            result = pos_service.create_sale(sale_data, cashier_id)
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            import traceback
            print(f"Error creating sale: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': f'Failed to create sale: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class POSSalesExportView(APIView):
    """
    GET /api/pos/sales/export/
    Export sales to CSV
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - cashier_id: Filter by cashier (optional)
    - shift_id: Filter by shift (optional)
    """
    
    def get(self, request):
        try:
            pos_service = POSSalesService()
            
            # Get query parameters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            cashier_id = request.query_params.get('cashier_id')
            shift_id = request.query_params.get('shift_id')
            
            # Get sales based on filters
            if shift_id:
                sales = pos_service.get_sales_by_shift(shift_id)
            elif start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                sales = pos_service.get_sales_by_date_range(start_date, end_date, cashier_id)
            else:
                # Default to recent sales
                sales = pos_service.get_recent_sales(100, cashier_id)
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="pos_sales_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            
            # Write header
            writer.writerow([
                'Sale ID',
                'Date',
                'Cashier ID',
                'Shift ID',
                'Customer ID',
                'Subtotal',
                'Tax',
                'Discount',
                'Total Amount',
                'Payment Method',
                'Status',
                'Items Count'
            ])
            
            # Write data rows
            for sale in sales:
                writer.writerow([
                    sale.get('_id'),
                    sale.get('transaction_date', '').strftime('%Y-%m-%d %H:%M:%S') if sale.get('transaction_date') else '',
                    sale.get('cashier_id', ''),
                    sale.get('shift_id', ''),
                    sale.get('customer_id', ''),
                    sale.get('subtotal', 0),
                    sale.get('tax_amount', 0),
                    sale.get('discount_amount', 0),
                    sale.get('total_amount', 0),
                    sale.get('payment_method', ''),
                    sale.get('status', ''),
                    len(sale.get('items', []))
                ])
            
            return response
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'Invalid parameter: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to export sales: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class POSSalesReceiptView(APIView):
    """
    GET /api/pos/sales/{sale_id}/receipt/
    Get formatted receipt data for printing
    """
    
    def get(self, request, sale_id):
        try:
            pos_service = POSSalesService()
            
            # Get sale
            sale = pos_service.get_sale_by_id(sale_id)
            
            if not sale:
                return Response({
                    'success': False,
                    'error': 'Sale not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # ✅ Format receipt data with IDs only (no names for security)
            receipt_data = {
                'sale_id': sale.get('_id'),
                'transaction_date': sale.get('transaction_date'),
                'cashier': {
                    'id': sale.get('cashier_id'),
                    'shift_id': sale.get('shift_id')
                },
                'items': sale.get('items', []),
                'subtotal': sale.get('subtotal', 0),
                'tax_amount': sale.get('tax_amount', 0),
                'discount_amount': sale.get('discount_amount', 0),
                'total_amount': sale.get('total_amount', 0),
                'payment_method': sale.get('payment_method'),
                'payment_details': sale.get('payment_details', {}),
                'status': sale.get('status'),
                'customer_id': sale.get('customer_id')
            }
            
            return Response({
                'success': True,
                'data': receipt_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to get receipt: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)