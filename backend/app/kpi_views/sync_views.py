"""
Sync-related API views
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

class TriggerStartupSyncView(APIView):
    """
    POST /api/v1/sync/trigger-startup/
    Trigger the same sync that happens on startup
    """
    
    def post(self, request):
        try:
            from ...services.sync_service import smart_sync_products_startup, smart_sync_batches_startup
            from ...services.POS.batch_service import BatchService
            
            results = {
                'products': None,
                'batches': None,
                'stock_updates': 0
            }
            
            # Sync products
            try:
                product_result = smart_sync_products_startup()
                results['products'] = product_result
            except Exception as e:
                logger.error(f"Product sync error: {e}")
                results['products'] = {'error': str(e)}
            
            # Sync batches
            try:
                batch_result = smart_sync_batches_startup()
                results['batches'] = batch_result
            except Exception as e:
                logger.error(f"Batch sync error: {e}")
                results['batches'] = {'error': str(e)}
            
            # Update product stocks after batch sync
            try:
                batch_service = BatchService()
                products = list(batch_service.products_collection.find({'isDeleted': {'$ne': True}}))
                stock_updated_count = 0
                
                for product in products:
                    old_stock = product.get('total_stock', 0)
                    batch_service.update_product_total_stock(product['_id'], verbose=False)
                    updated_product = batch_service.products_collection.find_one({'_id': product['_id']})
                    new_stock = updated_product.get('total_stock', 0) if updated_product else old_stock
                    if old_stock != new_stock:
                        stock_updated_count += 1
                
                results['stock_updates'] = stock_updated_count
            except Exception as e:
                logger.error(f"Stock update error: {e}")
                results['stock_updates'] = {'error': str(e)}
            
            total_synced = 0
            if results['products'] and isinstance(results['products'], dict):
                total_synced += results['products'].get('total_synced', 0)
            if results['batches'] and isinstance(results['batches'], dict):
                total_synced += results['batches'].get('total_synced', 0)
            
            return Response({
                'success': True,
                'message': f'Sync completed: {total_synced} items synced, {results["stock_updates"]} products updated',
                'data': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Trigger startup sync error: {e}")
            return Response({
                'success': False,
                'message': f'Sync failed: {str(e)}',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



