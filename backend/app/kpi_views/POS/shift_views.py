from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ...services.POS.shift_service import ShiftService

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
                'data': shift
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)