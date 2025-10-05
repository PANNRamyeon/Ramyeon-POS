# backend/views/pos/promotion_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ...services.POS.promotion_pos_service import PromotionService
from ...services.POS.cart_service import CartService

class PromotionActiveListView(APIView):
    """
    GET /api/v1/pos/promotions/active/
    Get all currently active promotions
    """
    def get(self, request):
        try:
            promotion_service = PromotionService()
            result = promotion_service.get_active_promotions()
            
            if result['success']:
                return Response({
                    'success': True,
                    'data': result['promotions'],
                    'count': len(result['promotions'])
                }, status=status.HTTP_200_OK)
            
            return Response({
                'success': False,
                'error': result.get('message', 'Failed to get active promotions')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PromotionCalculateView(APIView):
    """
    POST /api/v1/pos/promotions/calculate/
    Calculate discount for specific cart items
    
    Body: {
        "promotion_id": "PROMO-00001",
        "items": [
            {
                "product_id": "PROD-00002",
                "quantity": 3,
                "unit_price": 156.00
            }
        ]
    }
    """
    def post(self, request):
        try:
            promotion_id = request.data.get('promotion_id')
            items = request.data.get('items', [])
            
            if not promotion_id:
                return Response({
                    'success': False,
                    'error': 'promotion_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not items:
                return Response({
                    'success': False,
                    'error': 'items array is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            promotion_service = PromotionService()
            
            # Get promotion
            promotion = promotion_service.collection.find_one({
                'promotion_id': promotion_id
            })
            
            if not promotion:
                return Response({
                    'success': False,
                    'error': f'Promotion {promotion_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Calculate discount
            result = promotion_service.calculate_promotion_discount(
                promotion, 
                items
            )
            
            return Response({
                'success': True,
                'data': {
                    'discount_amount': result['discount_amount'],
                    'affected_items': result['affected_items'],
                    'promotion_details': result.get('promotion_details', {})
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PromotionBestForCartView(APIView):
    """
    POST /api/v1/pos/promotions/best-for-cart/
    Find best promotion for given items (without applying)
    
    Body: {
        "items": [
            {
                "product_id": "PROD-00002",
                "quantity": 3,
                "unit_price": 156.00
            }
        ]
    }
    """
    def post(self, request):
        try:
            items = request.data.get('items', [])
            
            if not items:
                return Response({
                    'success': False,
                    'error': 'items array is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            promotion_service = PromotionService()
            result = promotion_service.apply_best_promotion_to_cart(items)
            
            return Response({
                'success': True,
                'data': {
                    'discount_amount': result['discount_amount'],
                    'promotion_applied': result['promotion_applied'],
                    'affected_items': result['affected_items']
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartPromotionAvailableView(APIView):
    """
    GET /api/v1/pos/carts/{cart_id}/promotions/available/
    Get list of promotions applicable to cart
    """
    def get(self, request, cart_id):
        try:
            cart_service = CartService()
            available_promotions = cart_service.get_available_promotions_for_cart(cart_id)
            
            return Response({
                'success': True,
                'data': available_promotions,
                'count': len(available_promotions)
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartPromotionView(APIView):
    """
    Combined view for cart promotion operations
    POST /api/v1/pos/carts/{cart_id}/promotion/ - Apply promotion
    DELETE /api/v1/pos/carts/{cart_id}/promotion/ - Remove promotion
    """
    
    def post(self, request, cart_id):
        """
        Apply promotion to cart
        Body: {
            "promotion_id": "PROMO-00001"  // Optional - auto-selects best if omitted
        }
        """
        try:
            promotion_id = request.data.get('promotion_id')
            
            cart_service = CartService()
            cart = cart_service.apply_promotion(cart_id, promotion_id)
            
            return Response({
                'success': True,
                'data': cart,
                'message': 'Promotion applied successfully'
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, cart_id):
        """Remove promotion from cart"""
        try:
            cart_service = CartService()
            cart = cart_service.remove_promotion(cart_id)
            
            return Response({
                'success': True,
                'data': cart,
                'message': 'Promotion removed successfully'
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)