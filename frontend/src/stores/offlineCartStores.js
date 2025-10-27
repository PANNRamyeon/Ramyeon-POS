import { defineStore } from 'pinia';

export const useOfflineCartStore = defineStore('offlineCart', {
  state: () => ({
    cart: JSON.parse(localStorage.getItem('offline-cart') || '[]'),
    activeShift: JSON.parse(localStorage.getItem('active-offline-shift') || 'null'),
    pendingSales: JSON.parse(localStorage.getItem('pending-offline-sales') || '[]'),
    localStock: JSON.parse(localStorage.getItem('local-stock-cache') || '{}')
  }),

  getters: {
    cartCount: (state) => state.cart.reduce((total, item) => total + item.quantity, 0),
    cartTotal: (state) => state.cart.reduce((total, item) => total + (item.price * item.quantity), 0),
    hasActiveShift: (state) => !!state.activeShift,
    pendingSyncCount: (state) => state.pendingSales.length
  },

  actions: {
    // CART ACTIONS
    addToCart(product, quantity = 1) {
      const existing = this.cart.find(item => item.id === product.id);
      
      if (existing) {
        existing.quantity += quantity;
      } else {
        this.cart.push({
          ...product,
          quantity: quantity,
          cartId: Date.now().toString()
        });
      }
      this.saveCart();
    },

    removeFromCart(productId) {
      this.cart = this.cart.filter(item => item.id !== productId);
      this.saveCart();
    },

    updateQuantity(productId, quantity) {
      const item = this.cart.find(item => item.id === productId);
      if (item) {
        item.quantity = quantity;
        this.saveCart();
      }
    },

    clearCart() {
      this.cart = [];
      this.saveCart();
    },

    // OFFLINE SHIFT MANAGEMENT
    startOfflineShift(cashierId, openingCash) {
      this.activeShift = {
        id: `OFFLINE-SHIFT-${Date.now()}`,
        cashier_id: cashierId,
        opening_cash: openingCash,
        opening_time: new Date().toISOString(),
        status: 'active',
        offline: true
      };
      localStorage.setItem('active-offline-shift', JSON.stringify(this.activeShift));
    },

    closeOfflineShift(closingCash) {
      if (this.activeShift) {
        this.activeShift.closing_cash = closingCash;
        this.activeShift.closing_time = new Date().toISOString();
        this.activeShift.status = 'closed';
        
        // Queue for sync
        this.pendingSales.push({
          type: 'SHIFT_CLOSE',
          data: this.activeShift,
          timestamp: new Date().toISOString()
        });
        
        localStorage.removeItem('active-offline-shift');
        this.activeShift = null;
        this.savePendingSales();
      }
    },

    // OFFLINE SALES
    processOfflineSale(paymentData) {
      const sale = {
        id: `OFFLINE-SALE-${Date.now()}`,
        shift_id: this.activeShift?.id,
        items: this.cart.map(item => ({
          product_id: item.id,
          quantity: item.quantity,
          unit_price: item.price
        })),
        total_amount: this.cartTotal,
        payment_method: paymentData.method,
        created_at: new Date().toISOString(),
        offline: true
      };

      this.pendingSales.push({
        type: 'SALE',
        data: sale,
        timestamp: new Date().toISOString()
      });

      this.clearCart();
      this.savePendingSales();

      return sale;
    },

    // STOCK MANAGEMENT
    updateLocalStock(products) {
      products.forEach(product => {
        this.localStock[product.id] = product.stock_quantity;
      });
      localStorage.setItem('local-stock-cache', JSON.stringify(this.localStock));
    },

    getProductStock(productId) {
      return this.localStock[productId] || 0;
    },

    // PERSISTENCE
    saveCart() {
      localStorage.setItem('offline-cart', JSON.stringify(this.cart));
    },

    savePendingSales() {
      localStorage.setItem('pending-offline-sales', JSON.stringify(this.pendingSales));
    }
  }
});