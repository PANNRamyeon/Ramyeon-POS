from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, date, time, timezone, timedelta
from django.http import HttpResponse
import csv
from ...services.POS.pos_sales_service import POSSalesService
from ...services.Backoffice.user_service import UserService
import traceback
import logging
from app.offline.sync_engine import SyncEngine
from app.offline.connectivity import Connectivity

logger = logging.getLogger(__name__)

class POSSalesCreateView(APIView):
    """
    POST /api/v1/pos/sales/create/
    Create a new POS sale (works offline + online)
    """ 
    def post(self, request):
        try:
            pos_service = POSSalesService()
            
            logger.info("🧾 Received sale request")
            logger.debug(f"Raw sale request: {request.data}")

            cashier_id = request.data.get('cashier_id')
            if not cashier_id:
                return Response({
                    'success': False,
                    'error': 'Cashier ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Validate required fields
            required_fields = ['items', 'total_amount', 'payment_method']
            missing_fields = [f for f in required_fields if f not in request.data]

            if missing_fields:
                return Response({
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            items = request.data.get('items', [])
            if not items:
                return Response({
                    'success': False,
                    'error': 'Sale must contain at least one item'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ Validate item structure
            for idx, item in enumerate(items):
                for field in ['product_id', 'quantity', 'unit_price', 'subtotal']:
                    if field not in item:
                        return Response({
                            'success': False,
                            'error': f'Item {idx + 1} missing required field: {field}'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ Prepare sale_data (include loyalty & promo)
            sale_data = {
                'items': items,
                'subtotal': request.data.get('subtotal', 0),
                'tax_amount': request.data.get('tax_amount', 0),
                'discount_amount': request.data.get('discount_amount', 0),
                'total_amount': request.data['total_amount'],
                'payment_method': request.data['payment_method'],
                'payment_details': request.data.get('payment_details', {}),
                'customer_id': request.data.get('customer_id'),
                'promotion_id': request.data.get('promotion_id'),
                'promotion_discount': request.data.get('promotion_discount', 0),
                'loyalty_points_used': request.data.get('loyalty_points_used', 0),
                'loyalty_points_earned': request.data.get('loyalty_points_earned', 0),
                'points_discount': request.data.get('points_discount', 0),
                'shift_id': request.data.get('shift_id')
            }

            logger.info(f"🛒 Preparing to create sale | Total ₱{sale_data['total_amount']:.2f}")

            # ✅ Create the sale (automatic offline fallback inside service)
            result = pos_service.create_sale(sale_data, cashier_id)

            sale_id = result.get('data', {}).get('_id')
            offline_flag = result.get('offline', False)

            if offline_flag:
                logger.warning(f"📴 Offline sale recorded locally: {sale_id}")
            else:
                logger.info(f"🌐 Online sale created successfully: {sale_id}")

            # ✅ Unified response for frontend
            return Response({
                'success': True,
                'offline': offline_flag,
                'message': result.get('message', 'Sale created successfully'),
                'data': result.get('data', {})
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            logger.error(f"❌ Validation error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"❌ Unexpected error creating sale: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': f'Failed to create sale: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class POSSalesDetailView(APIView):
    """GET /api/v1/pos/sales/{sale_id}/ - Get sale details"""
    
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
    """GET /api/v1/pos/sales/ - List sales with filters"""
  
    def get(self, request):
        try:
            pos_service = POSSalesService()
            
            limit = int(request.query_params.get('limit', 50))
            cashier_id = request.query_params.get('cashier_id')
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            shift_id = request.query_params.get('shift_id')
            status_filter = request.query_params.get('status')
            
            if shift_id:
                sales = pos_service.get_sales_by_shift(shift_id)
            elif start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = datetime.combine(end_date.date(), time(23, 59, 59))
                sales = pos_service.get_sales_by_date_range(start_date, end_date, cashier_id)
            else:
                sales = pos_service.get_recent_sales(limit, cashier_id)
            
            if status_filter:
                sales = [sale for sale in sales if sale.get('status') == status_filter]
            
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
            print(traceback.format_exc())
            return Response({
                'success': False,
                'error': f'Failed to retrieve sales: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class POSSalesVoidView(APIView):
    """POST /api/v1/pos/sales/{sale_id}/void/ - Void a sale"""
    
    def post(self, request, sale_id):
        try:
            pos_service = POSSalesService()
            user_service = UserService()
            
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
            
            manager = user_service.get_user_by_id(request.data['manager_id'])
            if not manager:
                return Response({
                    'success': False,
                    'error': 'Manager not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
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
    """GET /api/v1/pos/sales/daily-summary/ - Daily sales summary"""
    
    def get(self, request):
        try:
            pos_service = POSSalesService()
            
            date_str = request.query_params.get('date')
            if date_str:
                summary_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                summary_date = date.today()
            
            cashier_id = request.query_params.get('cashier_id')
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
    """GET /api/v1/pos/sales/shift-summary/{shift_id}/ - Shift sales summary"""
      
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


class POSSalesExportView(APIView):
    """GET /api/v1/pos/sales/export/ - Export sales to CSV"""
    
    def get(self, request):
        try:
            pos_service = POSSalesService()
            
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            cashier_id = request.query_params.get('cashier_id')
            shift_id = request.query_params.get('shift_id')
            
            if shift_id:
                sales = pos_service.get_sales_by_shift(shift_id)
            elif start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                sales = pos_service.get_sales_by_date_range(start_date, end_date, cashier_id)
            else:
                sales = pos_service.get_recent_sales(100, cashier_id)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="pos_sales_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Sale ID', 'Date', 'Cashier ID', 'Shift ID', 'Customer ID',
                'Subtotal', 'Tax', 'Discount', 'Total Amount', 'Payment Method',
                'Status', 'Items Count'
            ])
            
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
    """GET /api/v1/pos/sales/{sale_id}/receipt/ - Get receipt data"""
    
    def get(self, request, sale_id):
        try:
            pos_service = POSSalesService()
            sale = pos_service.get_sale_by_id(sale_id)

            if not sale:
                return Response({
                    'success': False,
                    'error': 'Sale not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # ✅ Convert UTC to Philippine Time (UTC+8)
            transaction_date_utc = sale.get('transaction_date')
            transaction_date_local = None

            if transaction_date_utc:
                try:
                    # Convert from string or naive datetime
                    if isinstance(transaction_date_utc, str):
                        # Ensure proper parsing with timezone awareness
                        transaction_date_utc = datetime.fromisoformat(
                            transaction_date_utc.replace("Z", "+00:00")
                        )
                    elif transaction_date_utc.tzinfo is None:
                        # Force UTC if missing timezone info
                        transaction_date_utc = transaction_date_utc.replace(tzinfo=timezone.utc)

                    # Convert UTC → Philippine time (+8)
                    ph_tz = timezone(timedelta(hours=8))
                    transaction_date_local = transaction_date_utc.astimezone(ph_tz).isoformat()

                except Exception as tz_err:
                    print(f"⚠️ Timezone conversion error: {tz_err}")
                    transaction_date_local = None

            # ✅ Build receipt data
            receipt_data = {
                'sale_id': sale.get('_id'),
                'transaction_date': transaction_date_local,
                'cashier': {
                    'id': sale.get('cashier_id'),
                    'shift_id': sale.get('shift_id')
                },
                'items': sale.get('items', []),
                'subtotal': sale.get('subtotal', 0),
                'tax_amount': sale.get('tax_amount', 0),
                'discount_amount': sale.get('discount_amount', 0),

                # ✅ Discount breakdown
                'discount_breakdown': sale.get('discount_breakdown', {
                    'promotion_discount': 0,
                    'points_discount': 0,
                    'total_discount': 0
                }),

                'total_amount': sale.get('total_amount', 0),
                'payment_method': sale.get('payment_method'),
                'payment_details': sale.get('payment_details', {}),
                'status': sale.get('status'),
                'customer_id': sale.get('customer_id'),

                # ✅ Loyalty points info
                'loyalty_points': sale.get('loyalty_points')
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

class ManualOfflineSyncView(APIView):
    """POST /api/v1/pos/offline/sync/ - Manually sync offline sales"""

    def post(self, request):
        try:
            net = Connectivity()
            sync_engine = SyncEngine(net)
            sync_engine.push_sales()

            return Response({
                "success": True,
                "message": "Offline data synced successfully (if any existed)."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Manual sync failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)