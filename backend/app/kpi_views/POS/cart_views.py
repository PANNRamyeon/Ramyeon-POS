from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ...services.POS.cart_service import CartService
from ...services.Backoffice.product_service import ProductService


class CartCreateView(APIView):
    """POST /api/v1/pos/carts/ - Create a new shopping cart"""
    
    def post(self, request):
        try:
            cart_service = CartService()
            
            cashier_id = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                cashier_id = getattr(request.user, 'username', None)
            
            if not cashier_id or cashier_id == '':
                cashier_id = request.data.get('cashier_id', 'USER-0001')
            
            shift_id = request.data.get('shift_id')
            cart = cart_service.create_cart(cashier_id, shift_id)
            
            return Response({
                'success': True,
                'message': 'Cart created successfully',
                'data': cart
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to create cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartView(APIView):
    """GET/DELETE /api/v1/pos/carts/{cart_id}/"""
    
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
            import traceback
            traceback.print_exc()
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
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to delete cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartAddItemView(APIView):
    """POST /api/v1/pos/carts/{cart_id}/items/ - Add item to cart"""
    
    def post(self, request, cart_id):
        try:
            cart_service = CartService()
            
            print(f"\n{'='*50}")
            print(f"📝 ADD ITEM REQUEST")
            print(f"{'='*50}")
            print(f"Cart ID: {cart_id}")
            print(f"Request data: {request.data}")
            
            product_id = request.data.get('product_id')
            quantity = request.data.get('quantity', 1)
            
            print(f"Product ID: {product_id}")
            print(f"Quantity: {quantity}")
            
            if not product_id:
                return Response(
                    {'success': False, 'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")
            except ValueError as e:
                return Response(
                    {'success': False, 'error': f'Invalid quantity: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print(f"✅ Calling cart_service.add_item()...")
            updated_cart = cart_service.add_item(cart_id, product_id, quantity)
            
            print(f"✅ Item added successfully")
            print(f"   Cart now has {len(updated_cart.get('items', []))} items")
            print(f"{'='*50}\n")
            
            return Response({
                'success': True,
                'message': 'Item added to cart',
                'data': updated_cart
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            print(f"❌ ValueError: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'success': False, 'error': f'Failed to add item: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CartItemView(APIView):
    """PUT/DELETE /api/v1/pos/carts/{cart_id}/items/{product_id}/"""
    
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
                'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
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
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to remove item: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartDiscountView(APIView):
    """POST/DELETE /api/v1/pos/carts/{cart_id}/discount/"""
    
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
                    'error': 'Invalid discount type'
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
            import traceback
            traceback.print_exc()
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
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to remove discount: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartPrepareCheckoutView(APIView):
    """POST /api/v1/pos/carts/{cart_id}/prepare-checkout/"""
    
    def post(self, request, cart_id):
        try:
            cart_service = CartService()
            cart = cart_service.get_cart(cart_id)
            
            print(f"📋 Preparing checkout for cart: {cart_id}")
            print(f"   Items: {len(cart.get('items', []))}")
            
            sale_data = cart_service.prepare_for_checkout(cart_id)
            print(f"✅ Checkout prepared")
            
            return Response({
                'success': True,
                'message': 'Cart ready for checkout',
                'sale_data': sale_data
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            print(f"❌ Validation error: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'success': False, 'error': f'Failed to prepare checkout: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CartClearView(APIView):
    """POST /api/v1/pos/carts/{cart_id}/clear/"""
    
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
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to clear cart: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartItemCountView(APIView):
    """GET /api/v1/pos/carts/{cart_id}/item-count/"""
    
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
    """POST /api/v1/pos/carts/{cart_id}/scan/"""
    
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
            
            product = None
            if barcode:
                products = product_service.get_all_products()
                product = next((p for p in products if p.get('barcode') == barcode), None)
            elif sku:
                product = product_service.get_product_by_sku(sku)
            
            if not product:
                return Response({
                    'success': False,
                    'error': 'Product not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
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
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to scan product: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)