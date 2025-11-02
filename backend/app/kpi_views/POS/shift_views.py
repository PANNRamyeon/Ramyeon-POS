from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ...services.POS.shift_service import ShiftService
from datetime import datetime

def serialize_shift_datetime(dt):
    """Convert datetime to ISO string with UTC marker"""
    if dt and hasattr(dt, 'isoformat'):
        # Add 'Z' for UTC if no timezone info
        return dt.isoformat() + 'Z' if dt.tzinfo is None else dt.isoformat()
    return dt

def serialize_shift(shift):
    """Serialize shift document for JSON response"""
    if not shift:
        return shift
    
    serialized = dict(shift)
    
    # Convert datetime fields
    for field in ['start_time', 'end_time', 'last_transaction_time']:
        if field in serialized:
            serialized[field] = serialize_shift_datetime(serialized[field])
    
    return serialized

class ShiftActiveView(APIView):
    """
    GET /api/v1/pos/shifts/active/?cashier_id=USER-0001
    Get cashier's active shift
    """
    def get(self, request):
        try:
            cashier_id = request.query_params.get('cashier_id')
            
            if not cashier_id:
                return Response({
                    'success': False,
                    'error': 'cashier_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            shift_service = ShiftService()
            shift = shift_service.get_active_shift(cashier_id)
            
            if not shift:
                return Response({
                    'success': False,
                    'error': 'No active shift found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'shift': serialize_shift(shift)  # ✅ Changed 'data' to 'shift' for consistency
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ShiftStartView(APIView):
    """
    POST /api/v1/pos/shifts/start/
    Start a new shift
    
    Request body:
    {
        "cashier_id": "USER-0001",
        "opening_cash": 500.00
    }
    """
    def post(self, request):
        try:
            cashier_id = request.data.get('cashier_id')
            opening_cash = request.data.get('opening_cash')
            
            if not cashier_id:
                return Response({
                    'success': False,
                    'error': 'cashier_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if opening_cash is None:
                return Response({
                    'success': False,
                    'error': 'opening_cash is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                opening_cash = float(opening_cash)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'opening_cash must be a number'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if opening_cash < 0:
                return Response({
                    'success': False,
                    'error': 'opening_cash cannot be negative'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            shift_service = ShiftService()
            
            # Check if cashier already has active shift
            existing_shift = shift_service.get_active_shift(cashier_id)
            if existing_shift:
                return Response({
                    'success': False,
                    'error': f'Cashier already has an active shift: {existing_shift["_id"]}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Start new shift
            shift = shift_service.start_shift(cashier_id, opening_cash)
            
            return Response({
                'success': True,
                'message': 'Shift started successfully',
                'shift': serialize_shift(shift)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return Response({
                'success': False,
                'error': f'Failed to start shift: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ShiftCloseView(APIView):
    """
    POST /api/v1/pos/shifts/{shift_id}/close/
    Close an active shift
    
    Request body:
    {
        "closing_cash": 1234.56
    }
    """
    def post(self, request, shift_id):
        try:
            shift_service = ShiftService()
            
            # Validate closing_cash
            closing_cash = request.data.get('closing_cash')
            
            if closing_cash is None:
                return Response({
                    'success': False,
                    'error': 'closing_cash is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                closing_cash = float(closing_cash)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'closing_cash must be a number'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if closing_cash < 0:
                return Response({
                    'success': False,
                    'error': 'closing_cash cannot be negative'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"\n{'='*60}")
            print(f"🔒 Closing shift via API: {shift_id}")
            print(f"   Closing cash: ₱{closing_cash:.2f}")
            print(f"{'='*60}\n")
            
            # Close shift (will recalculate statistics)
            closed_shift = shift_service.end_shift(
                shift_id, 
                closing_cash, 
                recalculate=True  # ✅ Always recalculate for accuracy
            )
            
            if not closed_shift:
                return Response({
                    'success': False,
                    'error': 'Failed to close shift'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            print(f"\n✅ Shift closed successfully via API")
            print(f"   Shift ID: {closed_shift['_id']}")
            print(f"   Total Sales: ₱{closed_shift.get('total_sales', 0):.2f}")
            print(f"   Transactions: {closed_shift.get('total_transactions', 0)}")
            print(f"   Cash Variance: ₱{closed_shift.get('cash_variance', 0):.2f}\n")
            
            return Response({
                'success': True,
                'message': 'Shift closed successfully',
                'shift': serialize_shift(closed_shift)
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            print(f"❌ Validation error: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            import traceback
            print(f"❌ Error closing shift:")
            print(traceback.format_exc())
            return Response({
                'success': False,
                'error': f'Failed to close shift: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ShiftDetailView(APIView):
    """
    GET /api/v1/pos/shifts/{shift_id}/
    Get shift details by ID
    """
    def get(self, request, shift_id):
        try:
            shift_service = ShiftService()
            shift = shift_service.get_shift_by_id(shift_id)
            
            if not shift:
                return Response({
                    'success': False,
                    'error': 'Shift not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'shift': serialize_shift(shift)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ShiftListView(APIView):
    """
    GET /api/v1/pos/shifts/
    List shifts with optional filters
    
    Query params:
    - cashier_id: Filter by cashier
    - status: Filter by status (open/closed)
    - limit: Number of results (default 50)
    """
    def get(self, request):
        try:
            shift_service = ShiftService()
            
            cashier_id = request.query_params.get('cashier_id')
            status_filter = request.query_params.get('status')
            limit = int(request.query_params.get('limit', 50))
            
            if cashier_id:
                shifts = shift_service.get_cashier_shifts(cashier_id, limit)
            else:
                shifts = shift_service.get_all_shifts(status_filter, limit)
            
            return Response({
                'success': True,
                'shifts': [serialize_shift(shift) for shift in shifts] if shifts else [],
                'count': len(shifts) if shifts else 0
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'Invalid parameter: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)