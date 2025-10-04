from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ...services.POS.cart_service import CartService
from ...services.Backoffice.product_service import ProductService


class CartCreateView(APIView):
    """
    POST /api/v1/pos/carts/
    Create a new shopping cart
    """
    
    
    def post(self, request):
        try:
            cart_service = CartService()
            
            # Get cashier_id
            cashier_id = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                cashier_id = getattr(request.user, 'username', None)
            
            if not cashier_id or cashier_id == '':
                cashier_id = request.data.get('cashier_id', 'USER-0001')
            
            # Get optional shift_id
            shift_id = request.data.get('shift_id')
            
            # Create cart
            cart = cart_service.create_cart(cashier_id, shift_id)
            
            return Response({
                'success': True,
                'message': 'Cart created successfully',
                'data': cart
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to create cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartDetailView(APIView):
    """
    GET /api/v1/pos/carts/{cart_id}/
    Get cart details
    """
    
    
    def get(self, request, cart_id):
        try:
            cart_service = CartService()
            
            cart = cart_service.get_cart(cart_id)
            
            return Response({
                'success': True,
                'data': cart
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to retrieve cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartAddItemView(APIView):
    """
    POST /api/v1/pos/carts/{cart_id}/items/
    Add item to cart
    
    Body:
    {
        "product_id": "PROD-00001",
        "quantity": 2
    }
    """
    
    
    def post(self, request, cart_id):
        try:
            cart_service = CartService()
            
            # Validate required fields
            if 'product_id' not in request.data:
                return Response({
                    'success': False,
                    'error': 'product_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            product_id = request.data['product_id']
            quantity = request.data.get('quantity', 1)
            
            # Validate quantity
            if quantity <= 0:
                return Response({
                    'success': False,
                    'error': 'Quantity must be greater than 0'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Add item to cart
            cart = cart_service.add_item(cart_id, product_id, quantity)
            
            return Response({
                'success': True,
                'message': 'Item added to cart',
                'data': cart
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to add item: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartUpdateItemView(APIView):
    """
    PUT /api/v1/pos/carts/{cart_id}/items/{product_id}/
    Update item quantity in cart
    
    Body:
    {
        "quantity": 5
    }
    """
    
    
    def put(self, request, cart_id, product_id):
        try:
            cart_service = CartService()
            
            # Validate quantity
            if 'quantity' not in request.data:
                return Response({
                    'success': False,
                    'error': 'quantity is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            new_quantity = request.data['quantity']
            
            # Update quantity (will remove item if quantity = 0)
            cart = cart_service.update_quantity(cart_id, product_id, new_quantity)
            
            message = 'Item removed from cart' if new_quantity == 0 else 'Item quantity updated'
            
            return Response({
                'success': True,
                'message': message,
                'data': cart
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to update item: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartRemoveItemView(APIView):
    """
    DELETE /api/v1/pos/carts/{cart_id}/items/{product_id}/
    Remove item from cart completely
    """
    
    
    def delete(self, request, cart_id, product_id):
        try:
            cart_service = CartService()
            
            cart = cart_service.remove_item(cart_id, product_id)
            
            return Response({
                'success': True,
                'message': 'Item removed from cart',
                'data': cart
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to remove item: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartApplyDiscountView(APIView):
    """
    POST /api/v1/pos/carts/{cart_id}/discount/
    Apply discount to cart
    
    Body for percentage discount:
    {
        "type": "percentage",
        "value": 10
    }
    
    Body for fixed discount:
    {
        "type": "fixed",
        "value": 50
    }
    
    Body for promotion:
    {
        "type": "promotion",
        "promotion_id": "PROMO-00001"
    }
    """
    
    
    def post(self, request, cart_id):
        try:
            cart_service = CartService()
            
            # Validate discount type
            if 'type' not in request.data:
                return Response({
                    'success': False,
                    'error': 'Discount type is required (percentage, fixed, or promotion)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            discount_type = request.data['type']
            
            if discount_type == 'percentage':
                if 'value' not in request.data:
                    return Response({
                        'success': False,
                        'error': 'Percentage value is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                cart = cart_service.apply_percentage_discount(
                    cart_id, 
                    request.data['value']
                )
                
            elif discount_type == 'fixed':
                if 'value' not in request.data:
                    return Response({
                        'success': False,
                        'error': 'Fixed amount value is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                cart = cart_service.apply_fixed_discount(
                    cart_id, 
                    request.data['value']
                )
                
            elif discount_type == 'promotion':
                promotion_id = request.data.get('promotion_id')
                cart = cart_service.apply_promotion(cart_id, promotion_id)
                
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid discount type. Use: percentage, fixed, or promotion'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': f'{discount_type.capitalize()} discount applied',
                'data': cart
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to apply discount: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartRemoveDiscountView(APIView):
    """
    DELETE /api/v1/pos/carts/{cart_id}/discount/
    Remove any applied discount
    """
    
    
    def delete(self, request, cart_id):
        try:
            cart_service = CartService()
            
            cart = cart_service.remove_discount(cart_id)
            
            return Response({
                'success': True,
                'message': 'Discount removed',
                'data': cart
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to remove discount: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartPrepareCheckoutView(APIView):
    """
    POST /api/v1/pos/carts/{cart_id}/prepare-checkout/
    Validate cart and prepare data for checkout
    """
    
    
    def post(self, request, cart_id):
        try:
            cart_service = CartService()
            
            # Prepare checkout data
            sale_data = cart_service.prepare_for_checkout(cart_id)
            
            return Response({
                'success': True,
                'message': 'Cart ready for checkout',
                'data': sale_data
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to prepare checkout: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartClearView(APIView):
    """
    POST /api/v1/pos/carts/{cart_id}/clear/
    Clear all items from cart (but keep the cart)
    """
    
    
    def post(self, request, cart_id):
        try:
            cart_service = CartService()
            
            success = cart_service.clear_cart(cart_id)
            
            if success:
                cart = cart_service.get_cart(cart_id)
                return Response({
                    'success': True,
                    'message': 'Cart cleared',
                    'data': cart
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to clear cart'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to clear cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartDeleteView(APIView):
    """
    DELETE /api/v1/pos/carts/{cart_id}/
    Delete cart completely (after checkout)
    """
    
    
    def delete(self, request, cart_id):
        try:
            cart_service = CartService()
            
            success = cart_service.delete_cart(cart_id)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Cart deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Cart not found or already deleted'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to delete cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartItemCountView(APIView):
    """
    GET /api/v1/pos/carts/{cart_id}/item-count/
    Get total item count in cart
    """
    
    
    def get(self, request, cart_id):
        try:
            cart_service = CartService()
            
            count = cart_service.get_item_count(cart_id)
            
            return Response({
                'success': True,
                'cart_id': cart_id,
                'item_count': count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to get item count: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartScanProductView(APIView):
    """
    POST /api/v1/pos/carts/{cart_id}/scan/
    Scan product by barcode or SKU
    
    Body:
    {
        "barcode": "7UPIN001197266"
    }
    OR
    {
        "sku": "7-UP-IN-001"
    }
    """
   
    def post(self, request, cart_id):
        try:
            cart_service = CartService()
            product_service = ProductService()
            
            barcode = request.data.get('barcode')
            sku = request.data.get('sku')
            
            if not barcode and not sku:
                return Response({
                    'success': False,
                    'error': 'Either barcode or SKU is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find product by barcode or SKU
            product = None
            if barcode:
                # Assuming ProductService has this method
                products = product_service.get_all_products()
                product = next((p for p in products if p.get('barcode') == barcode), None)
            elif sku:
                product = product_service.get_product_by_sku(sku)
            
            if not product:
                return Response({
                    'success': False,
                    'error': 'Product not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Add to cart (quantity 1 for each scan)
            cart = cart_service.add_item(cart_id, product['_id'], 1)
            
            return Response({
                'success': True,
                'message': f'Added {product["product_name"]} to cart',
                'product': {
                    'id': product['_id'],
                    'name': product['product_name'],
                    'price': product['selling_price']
                },
                'data': cart
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to scan product: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CartView(APIView):
    """
    GET /api/v1/pos/carts/{cart_id}/
    DELETE /api/v1/pos/carts/{cart_id}/
    """

    def get(self, request, cart_id):
        try:
            cart_service = CartService()
            cart = cart_service.get_cart(cart_id)
            
            return Response({
                'success': True,
                'data': cart
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            # Cart not found
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            # Log the full error
            import traceback
            print(f"ERROR in CartView.get: {traceback.format_exc()}")
            
            return Response({
                'success': False,
                'error': f'Failed to retrieve cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, cart_id):
        try:
            cart_service = CartService()
            success = cart_service.delete_cart(cart_id)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Cart deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Cart not found or already deleted'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            import traceback
            print(f"ERROR in CartView.delete: {traceback.format_exc()}")
            
            return Response({
                'success': False,
                'error': f'Failed to delete cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CartItemView(APIView):
    """
    PUT /api/v1/pos/carts/{cart_id}/items/{product_id}/
    DELETE /api/v1/pos/carts/{cart_id}/items/{product_id}/
    """
    
    
    def put(self, request, cart_id, product_id):
        try:
            cart_service = CartService()
            if 'quantity' not in request.data:
                return Response({
                    'success': False,
                    'error': 'quantity is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            new_quantity = request.data['quantity']
            cart = cart_service.update_quantity(cart_id, product_id, new_quantity)
            message = 'Item removed from cart' if new_quantity == 0 else 'Item quantity updated'
            
            return Response({
                'success': True,
                'message': message,
                'data': cart
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to update item: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, cart_id, product_id):
        try:
            cart_service = CartService()
            cart = cart_service.remove_item(cart_id, product_id)
            return Response({
                'success': True,
                'message': 'Item removed from cart',
                'data': cart
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to remove item: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartDiscountView(APIView):
    """
    POST /api/v1/pos/carts/{cart_id}/discount/
    DELETE /api/v1/pos/carts/{cart_id}/discount/
    """
    
    
    def post(self, request, cart_id):
        try:
            cart_service = CartService()
            
            if 'type' not in request.data:
                return Response({
                    'success': False,
                    'error': 'Discount type is required (percentage, fixed, or promotion)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            discount_type = request.data['type']
            
            if discount_type == 'percentage':
                if 'value' not in request.data:
                    return Response({
                        'success': False,
                        'error': 'Percentage value is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                cart = cart_service.apply_percentage_discount(cart_id, request.data['value'])
                
            elif discount_type == 'fixed':
                if 'value' not in request.data:
                    return Response({
                        'success': False,
                        'error': 'Fixed amount value is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                cart = cart_service.apply_fixed_discount(cart_id, request.data['value'])
                
            elif discount_type == 'promotion':
                promotion_id = request.data.get('promotion_id')
                cart = cart_service.apply_promotion(cart_id, promotion_id)
                
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid discount type. Use: percentage, fixed, or promotion'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': f'{discount_type.capitalize()} discount applied',
                'data': cart
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to apply discount: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, cart_id):
        try:
            cart_service = CartService()
            cart = cart_service.remove_discount(cart_id)
            return Response({
                'success': True,
                'message': 'Discount removed',
                'data': cart
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to remove discount: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)