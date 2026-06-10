// src/services/apiCart.js
import { api } from './api.js';

class CartAPIService {
  
  // ================================================================
  // HELPER: Extract data from standard response format
  // ================================================================
  
  /**
   * Extract data from backend response
   * Backend format: { success: true, message: "...", data: {...} }
   */
  extractData(response, errorContext = 'Operation') {
    if (!response.data) {
      throw new Error(`${errorContext} failed: No response data`);
    }
    
    if (response.data.success === false) {
      throw new Error(response.data.message || `${errorContext} failed`);
    }
    
    if (!response.data.data) {
      throw new Error(`${errorContext} failed: No data in response`);
    }
    
    return response.data.data;
  }
  
  // ================================================================
  // CART LIFECYCLE
  // ================================================================
  
  /**
   * Create a new shopping cart
   */
  async createCart(cashierId, shiftId = null) {
    try {
      console.log('📝 API: Creating cart with:', { cashierId, shiftId });
      
      const response = await api.post('/pos/carts/', {
        cashier_id: cashierId,
        shift_id: shiftId
      });
      
      const cartData = this.extractData(response, 'Cart creation');
      const transformedCart = this.transformCartData(cartData);
      
      console.log('✅ Cart created:', transformedCart.id);
      return transformedCart;
      
    } catch (error) {
      console.error('❌ Create cart failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  /**
   * Get cart details by ID
   */
  async getCart(cartId) {
    try {
      const response = await api.get(`/pos/carts/${cartId}/`);
      const cartData = this.extractData(response, 'Get cart');
      return this.transformCartData(cartData);
    } catch (error) {
      console.error('❌ Get cart failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  /**
   * Delete cart
   */
  async deleteCart(cartId) {
    try {
      await api.delete(`/pos/carts/${cartId}/`);
      return true;
    } catch (error) {
      console.error('❌ Delete cart failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  /**
   * Clear all items from cart
   */
  async clearCart(cartId) {
    try {
      const response = await api.post(`/pos/carts/${cartId}/clear/`);
      const cartData = this.extractData(response, 'Clear cart');
      return this.transformCartData(cartData);
    } catch (error) {
      console.error('❌ Clear cart failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  // ================================================================
  // ITEM MANAGEMENT
  // ================================================================

  /**
   * Add item to cart
   */
  async addItem(cartId, productId, quantity = 1) {
    try {
      const response = await api.post(`/pos/carts/${cartId}/items/`, {
        product_id: productId,
        quantity: quantity
      });
      
      const cartData = this.extractData(response, 'Add item');
      return this.transformCartData(cartData);
      
    } catch (error) {
      console.error('❌ Add item failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  /**
   * Update item quantity
   */
  async updateItemQuantity(cartId, productId, quantity) {
    try {
      const response = await api.put(`/pos/carts/${cartId}/items/${productId}/`, {
        quantity: quantity
      });
      
      const cartData = this.extractData(response, 'Update quantity');
      return this.transformCartData(cartData);
      
    } catch (error) {
      console.error('❌ Update quantity failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  /**
   * Remove item from cart
   */
  async removeItem(cartId, productId) {
    try {
      const response = await api.delete(`/pos/carts/${cartId}/items/${productId}/`);
      const cartData = this.extractData(response, 'Remove item');
      return this.transformCartData(cartData);
    } catch (error) {
      console.error('❌ Remove item failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  /**
   * Scan product barcode
   */
  async scanProduct(cartId, barcode) {
    try {
      const response = await api.post(`/pos/carts/${cartId}/scan/`, {
        barcode: barcode
      });
      
      const cartData = this.extractData(response, 'Scan product');
      return this.transformCartData(cartData);
      
    } catch (error) {
      console.error('❌ Scan product failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  // ================================================================
  // PROMOTION MANAGEMENT
  // ================================================================

  /**
   * Apply promotion to cart
   */
  async applyPromotion(cartId, promotionId = null) {
    try {
      const response = await api.post(`/pos/carts/${cartId}/promotion/`, {
        promotion_id: promotionId
      });
      
      const cartData = this.extractData(response, 'Apply promotion');
      return this.transformCartData(cartData);
      
    } catch (error) {
      console.error('❌ Apply promotion failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  /**
   * Remove promotion from cart
   */
  async removePromotion(cartId) {
    try {
      const response = await api.delete(`/pos/carts/${cartId}/promotion/`);
      const cartData = this.extractData(response, 'Remove promotion');
      return this.transformCartData(cartData);
    } catch (error) {
      console.error('❌ Remove promotion failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  /**
   * Get available promotions for cart
   */
  async getAvailablePromotions(cartId) {
    try {
      const response = await api.get(`/pos/carts/${cartId}/promotions/available/`);
      
      // This endpoint might return different format
      if (response.data.promotions) {
        return response.data.promotions;
      }
      
      return this.extractData(response, 'Get promotions');
      
    } catch (error) {
      console.error('❌ Get promotions failed:', error);
      return [];
    }
  }

  // ================================================================
  // CHECKOUT
  // ================================================================

  /**
   * Prepare cart for checkout
   */
  async prepareCheckout(cartId) {
    try {
      console.log('📋 API: Preparing checkout for cart:', cartId);
      
      if (!cartId) {
        throw new Error('Cart ID is required for checkout');
      }
      
      const response = await api.post(`/pos/carts/${cartId}/prepare-checkout/`);
      
      console.log('✅ API: Checkout response:', response.data);
      
      // Extract sale_data from response
      if (response.data.sale_data) {
        return response.data.sale_data;
      }
      
      // Fallback: try to extract from standard format
      const data = this.extractData(response, 'Prepare checkout');
      return data.sale_data || data;
      
    } catch (error) {
      console.error('❌ API: Prepare checkout failed:', error);
      
      let errorMessage = 'Failed to prepare checkout';
      
      if (error.response?.data) {
        errorMessage = error.response.data.error || 
                       error.response.data.message || 
                       errorMessage;
      } else {
        errorMessage = error.message;
      }
      
      throw new Error(errorMessage);
    }
  }

  /**
   * Get item count in cart
   */
  async getItemCount(cartId) {
    try {
      const response = await api.get(`/pos/carts/${cartId}/item-count/`);
      
      if (response.data.item_count !== undefined) {
        return response.data.item_count;
      }
      
      const data = this.extractData(response, 'Get item count');
      return data.item_count || 0;
      
    } catch (error) {
      console.error('❌ Get item count failed:', error);
      return 0;
    }
  }

  // ================================================================
  // DATA TRANSFORMATION
  // ================================================================

  /**
   * Transform backend cart data to frontend format
   */
  transformCartData(cartData) {
    if (!cartData) {
      throw new Error('Cart data is null or undefined');
    }
    
    // Extract cart ID
    const cartId = cartData._id || cartData.cart_id || cartData.id;
    
    if (!cartId) {
      console.error('❌ No cart ID found in:', cartData);
      throw new Error('Cart data missing ID field');
    }
    
    return {
      id: cartId,
      cashierId: cartData.cashier_id || null,
      shiftId: cartData.shift_id || null,
      
      items: Array.isArray(cartData.items) ? cartData.items.map(item => ({
        id: item.product_id,
        productId: item.product_id,
        name: item.product_name || 'Unknown Product',
        sku: item.sku || '',
        price: parseFloat(item.unit_price || 0),
        quantity: parseInt(item.quantity || 0),
        subtotal: parseFloat(item.subtotal || 0),
        isTaxable: item.is_taxable !== false,
        addedAt: item.added_at,
        image: this.generatePlaceholderImage(item.product_name || 'Product')
      })) : [],
      
      subtotal: parseFloat(cartData.subtotal || 0),
      taxRate: parseFloat(cartData.tax_rate || 0.12),
      taxAmount: parseFloat(cartData.tax_amount || 0),
      discountAmount: parseFloat(cartData.discount_amount || 0),
      discountType: cartData.discount_type || null,
      discountDetails: cartData.discount_details || {},
      total: parseFloat(cartData.total || 0),
      
      status: cartData.status || 'active',
      createdAt: cartData.created_at,
      lastUpdated: cartData.last_updated
    };
  }

  /**
   * Generate placeholder image for products
   */
  generatePlaceholderImage(productName) {
    const name = encodeURIComponent(productName || 'Product');
    return `https://ui-avatars.com/api/?name=${name}&size=200&background=7392E2&color=fff`;
  }
}

export default new CartAPIService();