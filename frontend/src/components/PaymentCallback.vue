<template>
  <div class="payment-callback-page">
    <div class="callback-container">
      <!-- Loading State -->
      <div v-if="isProcessing" class="processing-state">
        <div class="spinner-large"></div>
        <h2>{{ statusMessage }}</h2>
        <p>{{ subMessage }}</p>
        
        <div class="progress-steps">
          <div :class="['step', { active: currentStep >= 1 }]">
            <div class="step-icon">1</div>
            <span>Verifying Payment</span>
          </div>
          <div :class="['step', { active: currentStep >= 2 }]">
            <div class="step-icon">2</div>
            <span>Creating Order</span>
          </div>
          <div :class="['step', { active: currentStep >= 3 }]">
            <div class="step-icon">3</div>
            <span>Finalizing</span>
          </div>
        </div>
      </div>
      
      <!-- Success State -->
      <div v-else-if="paymentStatus === 'success'" class="success-state">
        <div class="success-icon-large">✓</div>
        <h2>Payment Successful!</h2>
        <p class="success-subtitle">Your {{ walletName }} payment has been confirmed</p>
        
        <div class="payment-summary">
          <div class="summary-item">
            <span class="label">Order ID</span>
            <span class="value">{{ saleDetails.saleId }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Amount Paid</span>
            <span class="value amount">₱{{ formatPrice(saleDetails.amount) }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Payment Method</span>
            <span class="value">{{ walletName }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Transaction Date</span>
            <span class="value">{{ formatDateTime(saleDetails.timestamp) }}</span>
          </div>
        </div>
        
        <div class="action-buttons">
          <button class="btn btn-secondary btn-lg" @click="printReceipt">
            <Printer :size="20" />
            Print Receipt
          </button>
          <button class="btn btn-primary btn-lg" @click="goToNewOrder">
            <ShoppingCart :size="20" />
            New Order
          </button>
        </div>
        
        <p class="redirect-note">Redirecting automatically in {{ countdown }} seconds...</p>
      </div>
      
      <!-- Failed State -->
      <div v-else-if="paymentStatus === 'failed'" class="failed-state">
        <div class="failed-icon-large">✕</div>
        <h2>Payment Failed</h2>
        <p class="error-message">{{ errorMessage }}</p>
        
        <div class="error-details">
          <div class="error-card">
            <h4>What happened?</h4>
            <ul>
              <li v-if="errorType === 'cancelled'">Payment was cancelled</li>
              <li v-else-if="errorType === 'expired'">Payment session expired</li>
              <li v-else-if="errorType === 'insufficient'">Insufficient funds</li>
              <li v-else>Payment could not be processed</li>
            </ul>
          </div>
          
          <div class="help-card">
            <h4>Need help?</h4>
            <p>Contact our support team if you were charged but the order wasn't created.</p>
            <p class="support-info">📞 Support: (032) 123-4567</p>
          </div>
        </div>
        
        <div class="action-buttons">
          <button class="btn btn-secondary btn-lg" @click="goToCheckout">
            <ArrowLeft :size="20" />
            Back to Checkout
          </button>
          <button class="btn btn-primary btn-lg" @click="tryAgain">
            <RefreshCw :size="20" />
            Try Again
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Printer, ShoppingCart, ArrowLeft, RefreshCw } from 'lucide-vue-next'
import { usePaymongo } from '@/composables/api/usePaymongo'
import { useCartStore } from '@/stores/cartStores'
import apiSales from '@/services/apiSales'
import { useStockCache } from '@/composables/data/useStockCache.js'

export default {
  name: 'PaymentCallback',
  
  components: {
    Printer,
    ShoppingCart,
    ArrowLeft,
    RefreshCw
  },
  
  setup() {
    const paymongo = usePaymongo()
    const cartStore = useCartStore()
    const stockCache = useStockCache()
    return { paymongo, cartStore, stockCache }
  },
  
  data() {
    return {
      isProcessing: true,
      paymentStatus: null, // 'success', 'failed'
      statusMessage: 'Verifying payment...',
      subMessage: 'Please wait while we confirm your payment with the payment gateway.',
      currentStep: 1,
      
      walletName: 'E-Wallet',
      errorMessage: null,
      errorType: null, // 'cancelled', 'expired', 'insufficient', 'error'
      
      saleDetails: {
        saleId: null,
        amount: 0,
        timestamp: null
      },
      
      countdown: 5,
      countdownTimer: null
    }
  },
  
  async mounted() {
    const status = this.$route.query.status
    const sourceId = this.$route.query.source_id
    
    console.log('📱 Payment callback received:', { status, sourceId })
    
    if (status === 'success') {
      await this.handleSuccessCallback(sourceId)
    } else {
      this.handleFailedCallback()
    }
  },
  
  beforeUnmount() {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer)
    }
  },
  
  methods: {
    async handleSuccessCallback(sourceId) {
      try {
        this.currentStep = 1
        this.statusMessage = 'Verifying payment...'
        this.subMessage = 'Confirming with payment gateway.'
        
        // Retrieve pending payment data
        const pendingData = sessionStorage.getItem('pendingEWalletPayment')
        
        if (!pendingData) {
          throw new Error('Payment session expired. Please contact support if you were charged.')
        }
        
        const pending = JSON.parse(pendingData)
        this.walletName = pending.wallet_name
        
        console.log('📦 Processing e-wallet payment:', pending)
        
        // Simulate verification delay
        await this.delay(1000)
        
        // Step 2: Create sale
        this.currentStep = 2
        this.statusMessage = 'Creating your order...'
        this.subMessage = 'Saving order details and updating inventory.'
        
        const paymentDetails = {
          method: pending.wallet_name.toLowerCase(),
          amount_paid: pending.amount,
          change: 0,
          status: 'completed',
          transaction_id: pending.source_id,
          source_id: pending.source_id,
          wallet_type: pending.wallet_name,
          timestamp: new Date().toISOString()
        }
        
        const saleData = {
          items: pending.cart_items.map(item => ({
            product_id: item.productId,
            product_name: item.productName,
            sku: item.sku || '',
            quantity: item.quantity,
            unit_price: item.price,
            subtotal: item.subtotal,
            is_taxable: item.isTaxable !== false
          })),
          subtotal: pending.subtotal,
          tax_amount: pending.tax,
          discount: pending.promo_discount + pending.points_discount,
          total_amount: pending.amount,
          cashier_id: pending.cashier_id,
          shift_id: pending.shift_id,
          payment_method: pending.payment_type,
          payment_details: paymentDetails
        }
        
        if (pending.customer) {
          saleData.customer_id = pending.customer._id
          saleData.loyalty_points_used = pending.points_redeemed
          saleData.loyalty_points_earned = pending.points_to_earn
        }
        
        if (pending.promotion) {
          saleData.promotion_id = pending.promotion._id
          saleData.promotion_discount = pending.promo_discount
        }
        
        if (pending.points_discount > 0) {
          saleData.points_discount = pending.points_discount
        }
        
        console.log('📝 Creating sale:', saleData)
        
        const result = await apiSales.createSale(saleData)
        
        // Update stock cache with sold items
        try {
          this.stockCache.updateStockAfterSale(saleData.items)
          console.log('📦 Stock cache updated after e-wallet sale')
        } catch (error) {
          console.error('⚠️ Failed to update stock cache:', error)
          // Don't block success flow if cache update fails
        }
        
        // Signal NewOrder to perform targeted stock refresh on return
        try {
          const affectedIds = (saleData.items || []).map(i => i.product_id).filter(Boolean)
          if (affectedIds.length > 0) {
            sessionStorage.setItem('refreshProductIds', JSON.stringify(affectedIds))
          }
          sessionStorage.setItem('refreshStockAfterCheckout', 'true')
        } catch (_) {}
        
        // Step 3: Finalize
        this.currentStep = 3
        this.statusMessage = 'Finalizing...'
        this.subMessage = 'Almost done!'
        
        await this.delay(800)
        
        // Clear session data
        sessionStorage.removeItem('pendingEWalletPayment')
        sessionStorage.removeItem('appliedPromotion')
        sessionStorage.removeItem('checkoutCustomer')
        this.cartStore.clearCart()
        
        // Store sale details
        this.saleDetails = {
          saleId: result._id || result.sale_id,
          amount: result.total_amount,
          timestamp: result.transaction_date || new Date().toISOString()
        }
        
        // Show success
        this.paymentStatus = 'success'
        this.isProcessing = false
        
        console.log('✅ E-wallet payment completed!')
        
        // Start countdown
        this.startCountdown()
        
      } catch (error) {
        console.error('❌ Payment callback failed:', error)
        this.paymentStatus = 'failed'
        this.isProcessing = false
        this.errorMessage = error.message
        this.errorType = 'error'
      }
    },
    
    handleFailedCallback() {
      this.isProcessing = false
      this.paymentStatus = 'failed'
      
      // Determine error type from query params or default
      const errorCode = this.$route.query.error_code
      
      if (errorCode === 'cancelled') {
        this.errorType = 'cancelled'
        this.errorMessage = 'Payment was cancelled. No charges were made to your account.'
      } else if (errorCode === 'expired') {
        this.errorType = 'expired'
        this.errorMessage = 'Payment session expired. Please try again.'
      } else {
        this.errorType = 'error'
        this.errorMessage = 'Payment could not be processed. Please try again or use a different payment method.'
      }
      
      // Clear pending payment
      sessionStorage.removeItem('pendingEWalletPayment')
    },
    
    startCountdown() {
      this.countdownTimer = setInterval(() => {
        this.countdown--
        if (this.countdown <= 0) {
          clearInterval(this.countdownTimer)
          this.goToNewOrder()
        }
      }, 1000)
    },
    
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms))
    },
    
    printReceipt() {
      if (this.countdownTimer) {
        clearInterval(this.countdownTimer)
      }
      
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const receiptUrl = `${baseUrl}/pos/sales/${this.saleDetails.saleId}/receipt/`
        
        const printWindow = window.open(receiptUrl, '_blank', 'width=800,height=600')
        
        if (printWindow) {
          printWindow.onload = () => {
            setTimeout(() => {
              printWindow.print()
            }, 500)
          }
        }
      } catch (error) {
        console.error('❌ Print receipt failed:', error)
        alert(`Failed to print receipt: ${error.message}`)
      }
    },
    
    goToNewOrder() {
      if (this.countdownTimer) {
        clearInterval(this.countdownTimer)
      }
      this.$router.replace('/new-order')
    },
    
    goToCheckout() {
      this.$router.replace('/checkout')
    },
    
    tryAgain() {
      this.$router.replace('/checkout')
    },
    
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
.payment-callback-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-medium) 0%, var(--secondary-medium) 100%);
  padding: 20px;
}

.callback-container {
  background: var(--surface-primary);
  border-radius: 24px;
  padding: 50px 40px;
  max-width: 600px;
  width: 100%;
  box-shadow: var(--shadow-2xl);
  animation: slideUp 0.4s ease;
}

/* ==========================================================================
   PROCESSING STATE
   ========================================================================== */

.processing-state {
  text-align: center;
}

.processing-state h2 {
  margin: 20px 0 10px;
  font-size: 28px;
  color: var(--text-primary);
  font-weight: 600;
}

.processing-state p {
  color: var(--text-secondary);
  font-size: 16px;
  margin: 10px 0 30px;
  line-height: 1.5;
}

.spinner-large {
  width: 80px;
  height: 80px;
  border: 6px solid var(--border-secondary);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 30px;
}

/* Progress Steps */
.progress-steps {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-top: 40px;
}

.step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  opacity: 0.4;
  transition: opacity 0.3s ease;
}

.step.active {
  opacity: 1;
}

.step-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: var(--surface-tertiary);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  transition: all 0.3s ease;
}

.step.active .step-icon {
  background: var(--primary);
  color: white;
  transform: scale(1.1);
}

.step span {
  font-size: 13px;
  color: var(--text-tertiary);
  text-align: center;
  font-weight: 500;
}

.step.active span {
  color: var(--text-primary);
  font-weight: 600;
}

/* ==========================================================================
   SUCCESS STATE
   ========================================================================== */

.success-state {
  text-align: center;
}

.success-icon-large {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--success);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 70px;
  font-weight: bold;
  margin: 0 auto 24px;
  animation: successPop 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.success-state h2 {
  margin: 0 0 8px;
  font-size: 32px;
  color: var(--text-primary);
  font-weight: 700;
}

.success-subtitle {
  color: var(--text-secondary);
  font-size: 16px;
  margin: 0 0 30px;
}

/* Payment Summary */
.payment-summary {
  background: var(--surface-secondary);
  border-radius: 16px;
  padding: 24px;
  margin: 30px 0;
  text-align: left;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-secondary);
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-item .label {
  color: var(--text-tertiary);
  font-size: 14px;
  font-weight: 500;
}

.summary-item .value {
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 600;
}

.summary-item .value.amount {
  color: var(--success);
  font-size: 20px;
}

.redirect-note {
  margin-top: 20px;
  color: var(--text-tertiary);
  font-size: 14px;
  font-style: italic;
}

/* ==========================================================================
   FAILED STATE
   ========================================================================== */

.failed-state {
  text-align: center;
}

.failed-icon-large {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--error);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 70px;
  font-weight: bold;
  margin: 0 auto 24px;
  animation: shakeX 0.6s ease;
}

.failed-state h2 {
  margin: 0 0 12px;
  font-size: 32px;
  color: var(--text-primary);
  font-weight: 700;
}

.error-message {
  color: var(--error);
  font-size: 16px;
  margin: 0 0 30px;
  line-height: 1.5;
}

/* Error Details */
.error-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin: 30px 0;
  text-align: left;
}

.error-card,
.help-card {
  background: var(--surface-secondary);
  border-radius: 12px;
  padding: 20px;
}

.error-card h4,
.help-card h4 {
  margin: 0 0 12px;
  font-size: 16px;
  color: var(--text-primary);
  font-weight: 600;
}

.error-card ul {
  margin: 0;
  padding-left: 20px;
  color: var(--text-secondary);
  font-size: 14px;
}

.error-card li {
  margin: 8px 0;
}

.help-card p {
  margin: 0 0 12px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.help-card p:last-child {
  margin-bottom: 0;
}

.support-info {
  color: var(--primary);
  font-weight: 600;
}

/* ==========================================================================
   ACTION BUTTONS
   ========================================================================== */

.action-buttons {
  display: flex;
  gap: 16px;
  margin-top: 32px;
}

.action-buttons .btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 24px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.action-buttons .btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* ==========================================================================
   ANIMATIONS
   ========================================================================== */

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes successPop {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes shakeX {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
  20%, 40%, 60%, 80% { transform: translateX(10px); }
}

/* ==========================================================================
   RESPONSIVE
   ========================================================================== */

@media (max-width: 768px) {
  .callback-container {
    padding: 40px 30px;
  }
  
  .processing-state h2,
  .success-state h2,
  .failed-state h2 {
    font-size: 24px;
  }
  
  .success-icon-large,
  .failed-icon-large {
    width: 100px;
    height: 100px;
    font-size: 60px;
  }
  
  .progress-steps {
    gap: 12px;
  }
  
  .step-icon {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  
  .step span {
    font-size: 11px;
  }
  
  .error-details {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 576px) {
  .callback-container {
    padding: 30px 20px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .action-buttons .btn {
    width: 100%;
  }
  
  .payment-summary {
    padding: 20px 16px;
  }
}
</style>