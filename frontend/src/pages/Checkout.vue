<template>
  <div class="checkout-page">
    <!-- Loading Overlay -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner-large"></div>
      <p>{{ loadingMessage }}</p>
    </div>

    <div class="cp-left">
      <div class="cpl-header">
        <button @click="goBack" class="nav-btn" :disabled="isProcessing">
          <ChevronLeft :size="20"/> 
        </button>
        <h1>Checkout</h1>
        <button class="trash-btn" @click="clearCart" :disabled="isProcessing">
          <Trash2 :size="25"/> 
        </button>
      </div>
      
      <div class="cpl-contents">
        <!-- Empty Cart State -->
        <div v-if="cartItems.length === 0" class="empty-cart">
          <div class="empty-icon">🛒</div>
          <h3>Your cart is empty</h3>
          <p>Add some items to get started!</p>
          <button @click="goBack" class="continue-shopping-btn">
            Continue Shopping
          </button>
        </div>
        
        <!-- Cart Items -->
        <div v-else class="cart-items-container">
          <div class="cart-item-card" v-for="item in cartItems" :key="item.id">
            <div class="item-image">
              <img :src="item.image" :alt="item.name" loading="lazy" />
            </div>
            
            <div class="item-info">
              <h3 class="item-name">{{ item.name }}</h3>
              <p class="item-description">SKU: {{ item.sku }}</p>
              <div class="item-price-unit">₱{{ formatPrice(item.price) }} each</div>
            </div>
            
            <div class="item-controls">
              <div class="quantity-controls">
                <button 
                  class="quantity-btn decrease" 
                  @click="decreaseQuantity(item)"
                  :disabled="item.quantity <= 1 || quantityUpdating"
                >
                  <Minus :size="16" />
                </button>
                <span class="quantity">{{ item.quantity }}</span>
                <button 
                  class="quantity-btn increase" 
                  @click="increaseQuantity(item)"
                  :disabled="quantityUpdating"
                >
                  <Plus :size="16" />
                </button>
              </div>
              
              <div class="item-total-price">
                ₱{{ formatPrice(item.subtotal) }}
              </div>
              
              <button 
                class="remove-item" 
                @click="removeItem(item)" 
                title="Remove item"
                :disabled="quantityUpdating"
              >
                <X :size="18" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="cp-right">
      <div class="checkout-summary">
        <h2>Order Summary</h2>
        
        <div class="summary-row">
          <span>Subtotal:</span>
          <span>₱{{ formatPrice(subtotal) }}</span>
        </div>
        
        <div v-if="appliedPromotion" class="summary-row text-success">
          <span>
            <i class="lucide-tag"></i> {{ appliedPromotion.name }}
          </span>
          <span>-₱{{ formatPrice(discountAmount) }}</span>
        </div>
        
        <div class="summary-row">
          <span>Tax (12%):</span>
          <span>₱{{ formatPrice(taxAmount) }}</span>
        </div>
        
        <div class="summary-row total">
          <strong>TOTAL:</strong>
          <strong>₱{{ formatPrice(totalAmount) }}</strong>
        </div>
       
        
        <!-- Payment Method Selection -->
        <div class="payment-section">
          <h3>Payment Method</h3>
          <div class="payment-options">
            <label class="payment-option" :class="{ disabled: isProcessing }">
              <input 
                type="radio" 
                name="payment" 
                value="cash" 
                v-model="paymentMethod"
                :disabled="isProcessing"
              >
              <span class="payment-label">💵 Cash</span>
            </label>
            <label class="payment-option" :class="{ disabled: isProcessing }">
              <input 
                type="radio" 
                name="payment" 
                value="card" 
                v-model="paymentMethod"
                :disabled="isProcessing"
              >
              <span class="payment-label">💳 Card (PayMongo)</span>
              <small class="coming-soon">Coming Soon</small>
            </label>
            <label class="payment-option" :class="{ disabled: isProcessing }">
              <input 
                type="radio" 
                name="payment" 
                value="qrph" 
                v-model="paymentMethod"
                :disabled="isProcessing"
              >
              <span class="payment-label">📱 QR PH (GCash/PayMaya)</span>
              <small class="coming-soon">Coming Soon</small>
            </label>
          </div>
        </div>
        
        <!-- Cash Payment Details -->
        <div v-if="paymentMethod === 'cash'" class="cash-payment-section">
          <div class="form-group">
            <label>Cash Tendered</label>
            <div class="input-with-currency">
              <span class="currency-symbol">₱</span>
              <input 
                type="number" 
                v-model.number="cashTendered" 
                placeholder="0.00"
                step="0.01"
                min="0"
                class="form-input"
                :disabled="isProcessing"
                @input="validateCashPayment"
              />
            </div>
            <small v-if="cashValidationError" class="error-text">
              {{ cashValidationError }}
            </small>
          </div>
          
          <div v-if="changeAmount >= 0 && cashTendered > 0" class="change-display">
            <span>Change</span>
            <span class="change-amount">₱{{ formatPrice(changeAmount) }}</span>
          </div>
        </div>
        
        <!-- Card Payment Placeholder -->
        <div v-else-if="paymentMethod === 'card'" class="payment-placeholder">
          <p class="placeholder-text">
            💳 Card payment via PayMongo will be available soon!
          </p>
          <small>For now, please use cash payment.</small>
        </div>
        
        <!-- QR PH Payment Placeholder -->
        <div v-else-if="paymentMethod === 'qrph'" class="payment-placeholder">
          <p class="placeholder-text">
            📱 GCash/PayMaya payment via PayMongo will be available soon!
          </p>
          <small>For now, please use cash payment.</small>
        </div>
        
        <!-- Place Order Button -->
        <button 
          class="place-order-btn" 
          @click="placeOrder"
          :disabled="!canPlaceOrder"
        >
          <span v-if="!isProcessing">
            Place Order - ₱{{ formatPrice(totalAmount) }}
          </span>
          <span v-else>
            Processing... <span class="btn-spinner"></span>
          </span>
        </button>
      </div>
    </div>
    
    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="modal-overlay" @click="closeSuccessModal">
      <div class="modal-content success-modal" @click.stop>
        <div class="modal-header success-header">
          <div class="success-icon">✓</div>
          <h3>Order Completed!</h3>
          <button class="close-btn" @click="closeSuccessModal">
            <X :size="20" />
          </button>
        </div>
        <div class="modal-body">
          <div class="success-details">
            <div class="detail-row">
              <span>Sale ID:</span>
              <strong>{{ completedSale.saleId }}</strong>
            </div>
            <div class="detail-row">
              <span>Date:</span>
              <strong>{{ formatDateTime(completedSale.transactionDate) }}</strong>
            </div>
            <div class="detail-row">
              <span>Total Amount:</span>
              <strong class="total-highlight">₱{{ formatPrice(completedSale.totalAmount) }}</strong>
            </div>
            <div class="detail-row">
              <span>Payment Method:</span>
              <strong>{{ completedSale.paymentMethod.toUpperCase() }}</strong>
            </div>
            <div v-if="completedSale.shiftId" class="detail-row">
              <span>Shift ID:</span>
              <strong>{{ completedSale.shiftId }}</strong>
            </div>
            <div v-if="completedSale.change > 0" class="detail-row change-row">
              <span>Change:</span>
              <strong>₱{{ formatPrice(completedSale.change) }}</strong>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="printReceipt">
            <Printer :size="18" /> Print Receipt
          </button>
          <button class="btn-primary" @click="startNewOrder">
            New Order
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useCartStore } from '@/stores/cartStores'
import apiSales from '@/services/apiSales'
import apiProducts from '@/services/apiProducts'

export default {
  name: 'Checkout',
  
  setup() {
    const cartStore = useCartStore()
    return { cartStore }
  },
  
  data() {
    return {
      // Loading states
      isLoading: false,
      loadingMessage: 'Loading...',
      isProcessing: false,
      
      // Stock validation
      validationErrors: [],
      quantityUpdating: false,
      // Payment
      paymentMethod: 'cash',
      cashTendered: 0,
      cashValidationError: null,
      
      // Success modal
      showSuccessModal: false,
      completedSale: {
        saleId: null,
        transactionDate: null,
        totalAmount: 0,
        paymentMethod: '',
        change: 0,
        shiftId: null
      }
    }
  },
  
  computed: {
    // ✅ All cart data from store
    cartItems() {
      return this.cartStore.items
    },
    
    subtotal() {
      return this.cartStore.subtotal
    },
    
    taxAmount() {
      return this.cartStore.taxAmount
    },
    
    discountAmount() {
      return this.cartStore.discountAmount
    },
    
    totalAmount() {
      return this.cartStore.total
    },
    
    totalItems() {
      return this.cartStore.itemCount
    },
    
    changeAmount() {
      if (this.paymentMethod !== 'cash') return 0
      return Math.max(0, this.cashTendered - this.totalAmount)
    },
    
    canPlaceOrder() {
      if (this.cartItems.length === 0) return false
      if (this.isProcessing) return false
      if (this.validationErrors.length > 0) return false
      
      // Validate based on payment method
      if (this.paymentMethod === 'cash') {
        return this.cashTendered >= this.totalAmount
      }
      
      // Card and QR PH not implemented yet
      if (this.paymentMethod === 'card' || this.paymentMethod === 'qrph') {
        return false
      }
      
      return true
    }
  },
  
  async mounted() {
    await this.validateStock()
  },
  
  methods: {
    // ================================================================
    // STOCK VALIDATION
    // ================================================================
    
    async validateStock() {
      try {
        this.isLoading = true
        this.loadingMessage = 'Validating stock...'
        
        console.log('🔍 Validating stock for', this.cartItems.length, 'items...')
        
        if (this.cartItems.length === 0) {
          console.warn('⚠️ Cart is empty')
          this.$router.replace('/new-order')
          return
        }
        
        // Get product IDs
        const productIds = this.cartItems.map(item => item.productId)
        
        console.log('📦 Product IDs to validate:', productIds)
        
        // ✅ Fetch products (now includes batch stock)
        const products = await apiProducts.getProductsBatch(productIds)
        
        console.log('✅ Products fetched with batch stock:', products)
        
        // Build product map
        const productMap = {}
        products.forEach(product => {
          const productId = product.id || product._id
          productMap[productId] = product
        })
        
        // Validate each item
        const errors = []
        
        for (const item of this.cartItems) {
          const product = productMap[item.productId]
          
          if (!product) {
            errors.push(`Product "${item.productName}" not found`)
          } else {
            // ✅ Use batch stock (real-time)
            const availableStock = product.batch_stock || product.stock || 0
            
            console.log(`📊 ${item.productName}: Batch stock=${availableStock}, Requested=${item.quantity}`)
            
            if (availableStock < item.quantity) {
              errors.push(
                `Insufficient stock for "${item.productName}". ` +
                `Available: ${availableStock}, Requested: ${item.quantity}`
              )
            }
            
            // ✅ Expiry warning
            if (product.oldest_expiry) {
              const daysUntilExpiry = Math.floor(
                (new Date(product.oldest_expiry) - new Date()) / (1000 * 60 * 60 * 24)
              )
              
              if (daysUntilExpiry <= 7 && daysUntilExpiry >= 0) {
                console.warn(`⚠️ ${item.productName} has items expiring in ${daysUntilExpiry} days`)
              }
            }
          }
        }
        
        if (errors.length > 0) {
          this.validationErrors = errors
          console.error('❌ Stock validation errors:', errors)
          alert('Stock validation failed:\n\n' + errors.join('\n') + '\n\nPlease update your cart.')
          this.$router.replace('/new-order')
        } else {
          console.log('✅ Stock validation passed (batch stock verified)')
          this.validationErrors = []
        }
        
      } catch (error) {
        console.error('❌ Stock validation failed:', error)
        alert(`Failed to validate stock: ${error.message}\n\nPlease try again.`)
        this.$router.replace('/new-order')
      } finally {
        this.isLoading = false
      }
    },
    
    // ================================================================
    // CART UPDATES (Store methods)
    // ================================================================
    
    increaseQuantity(item) {
      this.cartStore.increaseQuantity(item.productId)
    },
    
    decreaseQuantity(item) {
      this.cartStore.decreaseQuantity(item.productId)
    },
    
    async removeItem(item) {
      if (!confirm(`Remove ${item.productName} from cart?`)) return
      
      this.cartStore.removeItem(item.productId)
      
      // If cart is empty, redirect
      if (this.cartStore.isEmpty) {
        alert('Cart is now empty. Returning to order page...')
        this.$router.replace('/new-order')
      }
    },
    
    async clearCart() {
      if (!confirm('Are you sure you want to clear your entire cart?')) return
      
      this.cartStore.clearCart()
      alert('Cart cleared. Returning to order page...')
      this.$router.replace('/new-order')
    },
    
    // ================================================================
    // PAYMENT
    // ================================================================
    
    validateCashPayment() {
      this.cashValidationError = null
      
      if (this.cashTendered <= 0) {
        this.cashValidationError = 'Please enter cash tendered amount'
        return false
      }
      
      if (this.cashTendered < this.totalAmount) {
        const shortage = this.totalAmount - this.cashTendered
        this.cashValidationError = `Insufficient. Need ₱${this.formatPrice(shortage)} more`
        return false
      }
      
      return true
    },
    
    async placeOrder() {
      if (!this.canPlaceOrder) {
        alert('Please complete payment details before placing order.')
        return
      }
      
      // Final validation
      if (this.paymentMethod === 'cash' && !this.validateCashPayment()) {
        return
      }
      
      // Confirm order
      const confirmMessage = this.paymentMethod === 'cash' 
        ? `Confirm order:\nTotal: ₱${this.formatPrice(this.totalAmount)}\nCash: ₱${this.formatPrice(this.cashTendered)}\nChange: ₱${this.formatPrice(this.changeAmount)}`
        : `Confirm order:\nTotal: ₱${this.formatPrice(this.totalAmount)}\nPayment: ${this.paymentMethod.toUpperCase()}`
      
      if (!confirm(confirmMessage)) return
      
      try {
        this.isProcessing = true
        this.isLoading = true
        this.loadingMessage = 'Processing order...'
        
        console.log('💳 Processing order...')
        
        // ✅ Step 1: Re-validate stock (final check)
        await this.validateStock()
        
        if (this.validationErrors.length > 0) {
          throw new Error('Stock validation failed')
        }
        
        // ✅ Step 2: Get checkout data from store
        const saleData = this.cartStore.getCheckoutData()
        
        console.log('📋 Sale data prepared:', saleData)
        
        // ✅ Step 3: Add payment details to saleData
        saleData.payment_method = this.paymentMethod
        saleData.payment_details = {
          method: this.paymentMethod,
          amount_paid: this.paymentMethod === 'cash' ? this.cashTendered : this.totalAmount,
          change: this.paymentMethod === 'cash' ? this.changeAmount : 0,
          status: 'completed',
          transaction_id: `${this.paymentMethod.toUpperCase()}-${Date.now()}`,
          timestamp: new Date().toISOString()
        }
        
        console.log('💰 Payment details added:', saleData.payment_details)
        
        // ✅ Step 4: Create sale (pass ONLY saleData)
        console.log('📝 Creating sale...')
        const result = await apiSales.createSale(saleData)  // ✅ ONLY ONE PARAMETER
        
        console.log('✅ Sale created:', result)
        
        // ✅ Step 5: Clear frontend cart
        this.cartStore.clearCart()
        
        console.log('🗑️ Cart cleared')
        
        // ✅ Step 6: Show success modal
        this.completedSale = {
          saleId: result._id || result.sale_id,
          transactionDate: result.transaction_date || new Date().toISOString(),
          totalAmount: result.total_amount,
          paymentMethod: this.paymentMethod,
          change: this.changeAmount,
          shiftId: result.shift_id || saleData.shift_id
        }
        
        this.showSuccessModal = true
        
        console.log('🎉 Order completed successfully!')
        
      } catch (error) {
        console.error('❌ Place order failed:', error)
        
        let errorMessage = error.message || 'Unknown error occurred'
        
        if (errorMessage.includes('stock')) {
          errorMessage = 'Some items are out of stock. Please review your cart.'
          this.$router.replace('/new-order')
        } else if (errorMessage.includes('payment')) {
          errorMessage = `Payment failed: ${errorMessage}`
        }
        
        alert(`Order failed: ${errorMessage}\n\nPlease try again.`)
        
      } finally {
        this.isProcessing = false
        this.isLoading = false
      }
    },
    
    // ================================================================
    // SUCCESS MODAL & RECEIPT
    // ================================================================
    
  async printReceipt() {
    try {
      console.log('🖨️ Printing receipt for sale:', this.completedSale.saleId)
      
      // ✅ Use import.meta.env for Vite (NOT process.env)
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const receiptUrl = `${baseUrl}/pos/sales/${this.completedSale.saleId}/receipt/`
      
      console.log('📄 Opening receipt:', receiptUrl)
      
      const printWindow = window.open(receiptUrl, '_blank', 'width=800,height=600')
      
      if (printWindow) {
        printWindow.onload = () => {
          setTimeout(() => {
            printWindow.print()
          }, 500)
        }
      } else {
        alert('Please allow popups to print receipts.')
      }
      
    } catch (error) {
      console.error('❌ Print receipt failed:', error)
      alert(`Failed to print receipt: ${error.message}`)
    }
  },
    
    closeSuccessModal() {
      this.showSuccessModal = false
      this.startNewOrder()
    },
    
    startNewOrder() {
      console.log('🔄 Starting new order...')
      this.$router.replace('/new-order')
    },
    
    // ================================================================
    // NAVIGATION
    // ================================================================
    
    goBack() {
      if (confirm('Return to order page? Your cart will be saved.')) {
        this.$router.push('/new-order')
      }
    },
    
    // ================================================================
    // UTILITIES
    // ================================================================
    
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2)
    },
    
    formatDateTime(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.checkout-page {
    display: flex;
    gap: 15px;
    padding: 15px;
    background-color: #f5f7fa;
    min-height: 100vh;
}

.cp-left {
    flex: 1;
    background-color: white;
    border-radius: 16px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    overflow: hidden;
}

.cp-right {
    width: 400px;
    background-color: white;
    border-radius: 16px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    padding: 0;
}

/* Header Styles */
.cpl-header {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 20px 25px;
    border-bottom: 1px solid #e9ecef;
    background-color: white;
}

.nav-btn, .trash-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 10px;
    border-radius: 10px;
    transition: all 0.2s ease;
    color: #6c757d;
}

.nav-btn:hover, .trash-btn:hover {
    background-color: #f8f9fa;
    color: #495057;
}

.trash-btn {
    margin-left: auto;
    color: #dc3545;
}

.trash-btn:hover {
    background-color: #ffe6e6;
}

.cpl-header h1 {
    font-size: 28px;
    margin: 0;
    color: #2d3748;
    font-weight: 600;
}

/* Cart Contents */
.cpl-contents {
    height: calc(100vh - 100px);
    overflow-y: auto;
    padding: 20px 25px;
    background-color: white;
}

.cart-items-container {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

/* Empty Cart */
.empty-cart {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 60px 20px;
    color: #6c757d;
}

.empty-icon {
    font-size: 64px;
    margin-bottom: 20px;
    opacity: 0.6;
}

.empty-cart h3 {
    font-size: 24px;
    margin: 10px 0;
    color: #495057;
}

.empty-cart p {
    font-size: 16px;
    margin-bottom: 30px;
}

.continue-shopping-btn {
    background: #6f42c1;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s;
}

.continue-shopping-btn:hover {
    background: #5a359a;
}

/* Cart Item Cards - FIXED */
.cart-item-card {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    padding: 20px;
    background-color: white;
    border-radius: 12px;
    border: 1px solid #e9ecef;
    transition: all 0.2s ease;
}

.cart-item-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border-color: #dee2e6;
    background-color: white; /* FIXED: Keep white on hover */
}

.item-image {
    width: 80px;
    height: 80px;
    border-radius: 10px;
    overflow: hidden;
    flex-shrink: 0;
    background: white;
    border: 1px solid #dee2e6;
}

.item-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.item-info {
    flex: 1;
    min-width: 0;
}

.item-name {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 5px 0;
    color: #2d3748;
}

.item-description {
    font-size: 14px;
    color: #6c757d;
    margin: 0 0 8px 0;
    line-height: 1.4;
}

.item-price-unit {
    font-size: 14px;
    color: #6f42c1;
    font-weight: 500;
}

.item-controls {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
}

.quantity-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    background: white;
    border-radius: 20px;
    padding: 4px;
    border: 1px solid #dee2e6;
}

.quantity-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}

.quantity-btn.decrease {
    background: #6c757d;
    color: white;
}

.quantity-btn.decrease:disabled {
    background: #e9ecef;
    color: #adb5bd;
    cursor: not-allowed;
}

.quantity-btn.increase {
    background: #6f42c1;
    color: white;
}

.quantity-btn:hover:not(:disabled) {
    opacity: 0.8;
    transform: scale(1.05);
}

.quantity {
    font-weight: 600;
    min-width: 30px;
    text-align: center;
    font-size: 16px;
    color: #495057;
}

.item-total-price {
    font-size: 18px;
    font-weight: 700;
    color: #2d3748;
}

.remove-item {
    background: none;
    border: none;
    cursor: pointer;
    color: #dc3545;
    padding: 6px;
    border-radius: 6px;
    transition: all 0.2s ease;
}

.remove-item:hover {
    background-color: #ffe6e6;
    transform: scale(1.1);
}

/* Checkout Summary */
.checkout-summary {
    padding: 25px;
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: white;
}

.checkout-summary h2 {
    margin: 0 0 25px 0;
    font-size: 24px;
    color: #2d3748;
    font-weight: 600;
}

.summary-details {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
}

.summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    font-size: 16px;
}

.summary-row:not(:last-child) {
    border-bottom: 1px solid #e9ecef;
}

.summary-divider {
    height: 1px;
    background: #dee2e6;
    margin: 15px 0;
}

.summary-row.total {
    font-weight: 700;
    font-size: 20px;
    color: #2d3748;
    padding: 15px 0 0 0;
    border-bottom: none;
}

/* Payment Section */
.payment-section {
    margin-bottom: 25px;
}

.payment-section h3 {
    margin: 0 0 15px 0;
    font-size: 18px;
    color: #2d3748;
    font-weight: 600;
}

.payment-options {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.payment-option {
    display: flex;
    align-items: center;
    cursor: pointer;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    transition: all 0.2s ease;
    background-color: white;
}

.payment-option:hover {
    background-color: #f8f9fa;
    border-color: #6f42c1;
}

.payment-option input[type="radio"] {
    margin-right: 12px;
    accent-color: #6f42c1;
}

.payment-label {
    font-size: 16px;
    color: #495057;
}

/* Place Order Button */
.place-order-btn {
    width: 100%;
    background: #6f42c1;
    color: white;
    border: none;
    padding: 16px;
    border-radius: 12px;
    font-size: 18px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-top: auto;
}

.place-order-btn:hover:not(:disabled) {
    background: #5a359a;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(111, 66, 193, 0.3);
}

.place-order-btn:disabled {
    background: #e9ecef;
    color: #6c757d;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

/* Legacy styles for backwards compatibility */
.cpl-card {
    width: 89%;
    height: auto;
    border-radius: 20px;
    background-color: white;
    margin-left: 32px;
    padding: 20px;
    margin-bottom: 1rem;
}

.item-row {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.item-details {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.item-price {
    font-size: 1.125rem;
    font-weight: 700;
    color: #333;
}

/* Scrollbar Styling */
.cpl-contents::-webkit-scrollbar {
    width: 6px;
}

.cpl-contents::-webkit-scrollbar-track {
    background: #f8f9fa;
    border-radius: 3px;
}

.cpl-contents::-webkit-scrollbar-thumb {
    background: #dee2e6;
    border-radius: 3px;
}

.cpl-contents::-webkit-scrollbar-thumb:hover {
    background: #ced4da;
}

/* Animations */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.cart-item-card {
    animation: fadeIn 0.3s ease-out;
}

.empty-cart {
    animation: fadeIn 0.5s ease-out;
}

/* Loading state */
.loading {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    color: #6c757d;
}

.loading::after {
    content: '';
    width: 20px;
    height: 20px;
    border: 2px solid #e9ecef;
    border-top-color: #6f42c1;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-left: 10px;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Responsive Design */
@media (max-width: 1024px) {
    .checkout-page {
        flex-direction: column;
        gap: 15px;
    }
    
    .cp-right {
        width: 100%;
    }
    
    .cart-item-card {
        flex-direction: column;
        text-align: center;
    }
    
    .item-controls {
        align-items: center;
        flex-direction: row;
        justify-content: space-between;
        width: 100%;
    }
}

@media (max-width: 768px) {
    .checkout-page {
        padding: 10px;
        gap: 10px;
    }
    
    .cpl-header {
        padding: 15px 20px;
    }
    
    .cpl-header h1 {
        font-size: 24px;
    }
    
    .cpl-contents {
        padding: 15px 20px;
        height: calc(100vh - 80px);
    }
    
    .checkout-summary {
        padding: 20px;
    }
    
    .cart-item-card {
        padding: 15px;
        gap: 12px;
    }
    
    .item-image {
        width: 60px;
        height: 60px;
    }
    
    .item-name {
        font-size: 16px;
    }
    
    .item-total-price {
        font-size: 16px;
    }
    
    .quantity-controls {
        gap: 6px;
        padding: 3px;
    }
    
    .quantity-btn {
        width: 28px;
        height: 28px;
    }
    
    .summary-details {
        padding: 15px;
        margin-bottom: 20px;
    }
    
    .payment-section {
        margin-bottom: 20px;
    }
    
    .payment-option {
        padding: 10px 12px;
    }
    
    .place-order-btn {
        padding: 14px;
        font-size: 16px;
    }
}

@media (max-width: 480px) {
    .checkout-page {
        padding: 5px;
    }
    
    .cpl-header {
        padding: 10px 15px;
        gap: 10px;
    }
    
    .cpl-header h1 {
        font-size: 20px;
    }
    
    .cpl-contents {
        padding: 10px 15px;
    }
    
    .checkout-summary {
        padding: 15px;
    }
    
    .cart-item-card {
        padding: 12px;
        gap: 10px;
    }
    
    .item-image {
        width: 50px;
        height: 50px;
    }
    
    .item-name {
        font-size: 14px;
    }
    
    .item-description {
        font-size: 12px;
    }
    
    .item-price-unit {
        font-size: 12px;
    }
    
    .item-total-price {
        font-size: 14px;
    }
    
    .quantity-btn {
        width: 24px;
        height: 24px;
    }
    
    .quantity {
        font-size: 14px;
        min-width: 24px;
    }
}

/* Print styles (for receipts) */
@media print {
    .checkout-page {
        background: white;
        padding: 0;
        gap: 0;
        flex-direction: column;
    }
    
    .cp-left {
        box-shadow: none;
        border-radius: 0;
    }
    
    .cp-right {
        box-shadow: none;
        border-radius: 0;
        width: 100%;
    }
    
    .cpl-header, .nav-btn, .trash-btn {
        display: none;
    }
    
    .item-controls .remove-item,
    .quantity-controls {
        display: none;
    }
    
    .payment-section,
    .place-order-btn {
        display: none;
    }
}

/* Focus styles for accessibility */
.nav-btn:focus,
.trash-btn:focus,
.quantity-btn:focus,
.remove-item:focus,
.continue-shopping-btn:focus,
.place-order-btn:focus {
    outline: 2px solid #6f42c1;
    outline-offset: 2px;
}

.payment-option:focus-within {
    border-color: #6f42c1;
    box-shadow: 0 0 0 2px rgba(111, 66, 193, 0.2);
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    .cart-item-card {
        border: 2px solid #000;
    }
    
    .quantity-btn.decrease {
        background: #000;
    }
    
    .quantity-btn.increase {
        background: #000;
    }
    
    .place-order-btn {
        background: #000;
    }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    .cart-item-card,
    .empty-cart,
    .quantity-btn,
    .remove-item,
    .place-order-btn,
    .nav-btn,
    .trash-btn {
        animation: none;
        transition: none;
    }
    
    .quantity-btn:hover:not(:disabled),
    .remove-item:hover,
    .place-order-btn:hover:not(:disabled) {
        transform: none;
    }
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.spinner-large {
  width: 60px;
  height: 60px;
  border: 4px solid #e9ecef;
  border-top-color: #6f42c1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

.loading-overlay p {
  font-size: 18px;
  color: #495057;
  font-weight: 500;
}

/* Cash Payment Section */
.cash-payment-section {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.input-with-currency {
  position: relative;
  display: flex;
  align-items: center;
}

.currency-symbol {
  position: absolute;
  left: 15px;
  font-size: 18px;
  font-weight: 600;
  color: #495057;
  pointer-events: none;
}

.input-with-currency .form-input {
  padding-left: 40px;
  font-size: 18px;
  font-weight: 600;
}

.change-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: white;
  border-radius: 8px;
  margin-top: 15px;
  border: 2px solid #4ea87a;
}

.change-amount {
  font-size: 24px;
  font-weight: 700;
  color: #4ea87a;
}

/* Payment Placeholder */
.payment-placeholder {
  margin-top: 20px;
  padding: 20px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 12px;
  text-align: center;
}

.placeholder-text {
  font-size: 16px;
  color: #856404;
  margin-bottom: 10px;
}

.payment-placeholder small {
  color: #856404;
  font-size: 14px;
}

.coming-soon {
  display: block;
  font-size: 11px;
  color: #6c757d;
  margin-top: 4px;
  font-style: italic;
}

.payment-option.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Button Spinner */
.btn-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-left: 8px;
}

/* Success Modal */
.success-modal {
  max-width: 500px;
}

.success-header {
  background: linear-gradient(135deg, #4ea87a 0%, #5eb488 100%);
  color: white;
  padding: 30px;
  text-align: center;
  border-radius: 16px 16px 0 0;
  position: relative;
}

.success-icon {
  width: 80px;
  height: 80px;
  background: white;
  color: #4ea87a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  font-weight: bold;
  margin: 0 auto 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.success-header h3 {
  margin: 0;
  font-size: 24px;
}

.success-header .close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.success-header .close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.success-details {
  padding: 30px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #e9ecef;
  font-size: 16px;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row span {
  color: #6c757d;
}

.detail-row strong {
  color: #2d3748;
  font-weight: 600;
}

.total-highlight {
  font-size: 20px;
  color: #4ea87a !important;
}

.change-row {
  background: #f8f9fa;
  padding: 12px 15px;
  margin: 10px -30px 0;
  border-bottom: none;
}

.change-row strong {
  color: #4ea87a !important;
  font-size: 18px;
}

.success-modal .modal-footer {
  padding: 20px 30px;
  gap: 15px;
}

.success-modal .btn-secondary,
.success-modal .btn-primary {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  font-size: 16px;
}

/* Animations */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error text */
.error-text {
  color: #dc3545;
  font-size: 13px;
  display: block;
  margin-top: 6px;
}

/* Discount styling */
.summary-row.discount {
  color: #4ea87a;
}

.discount-amount {
  font-weight: 600;
}

/* Form Input */
.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.form-input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #6f42c1;
  box-shadow: 0 0 0 3px rgba(111, 66, 193, 0.1);
}

.form-input:disabled {
  background: #e9ecef;
  cursor: not-allowed;
}
</style>