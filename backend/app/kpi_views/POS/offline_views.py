from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from app.offline.local_sync import warm_catalog_to_local, push_pending_sales


class OfflineWarmupView(APIView):
    """
    POST /api/v1/offline/warmup/
    Warm local DB from cloud for essential catalogs.
    """
    def post(self, request):
        try:
            cols = request.data.get('collections')
            if isinstance(cols, list):
                collections = [str(c) for c in cols]
            else:
                collections = None
            summary = warm_catalog_to_local(collections)
            return Response({'success': True, 'summary': summary}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OfflinePushPendingView(APIView):
    """
    POST /api/v1/offline/push-pending/
    Manually trigger pushing pending local sales to cloud.
    """
    def post(self, request):
        try:
            limit = request.data.get('limit')
            summary = push_pending_sales(limit)
            return Response({'success': True, 'summary': summary}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



