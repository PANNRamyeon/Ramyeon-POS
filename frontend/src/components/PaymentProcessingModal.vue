<template>
  <div v-if="show" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content processing-modal">
      <!-- Processing State -->
      <div v-if="status === 'processing'" class="modal-state">
        <div class="spinner-large"></div>
        <h3>{{ message }}</h3>
        <p>{{ subMessage }}</p>
      </div>
      
      <!-- Success State -->
      <div v-else-if="status === 'success'" class="modal-state">
        <div class="success-icon">✓</div>
        <h3>Payment Successful!</h3>
        <p>Your {{ walletType }} payment has been confirmed.</p>
        
        <div v-if="saleDetails" class="payment-details">
          <div class="detail-row">
            <span>Order ID:</span>
            <strong>{{ saleDetails.saleId }}</strong>
          </div>
          <div class="detail-row">
            <span>Amount:</span>
            <strong>₱{{ formatPrice(saleDetails.amount) }}</strong>
          </div>
          <div class="detail-row">
            <span>Payment Method:</span>
            <strong>{{ walletType }}</strong>
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="printReceipt">
            <Printer :size="18" /> Print Receipt
          </button>
          <button class="btn btn-primary" @click="continueToNewOrder">
            New Order
          </button>
        </div>
      </div>
      
      <!-- Failed State -->
      <div v-else-if="status === 'failed'" class="modal-state">
        <div class="failed-icon">✕</div>
        <h3>Payment Failed</h3>
        <p class="error-message">{{ errorMessage }}</p>
        
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModal">
            Close
          </button>
          <button class="btn btn-primary" @click="retryPayment">
            Try Again
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Printer } from 'lucide-vue-next'

export default {
  name: 'PaymentProcessingModal',
  
  components: {
    Printer
  },
  
  props: {
    show: {
      type: Boolean,
      default: false
    },
    status: {
      type: String,
      default: 'processing' // 'processing', 'success', 'failed'
    },
    message: {
      type: String,
      default: 'Processing payment...'
    },
    subMessage: {
      type: String,
      default: 'Please wait while we confirm your payment.'
    },
    walletType: {
      type: String,
      default: 'E-Wallet'
    },
    errorMessage: {
      type: String,
      default: 'Payment was not completed. Please try again.'
    },
    saleDetails: {
      type: Object,
      default: null
    }
  },
  
  emits: ['close', 'print-receipt', 'new-order', 'retry'],
  
  methods: {
    closeModal() {
      if (this.status !== 'processing') {
        this.$emit('close')
      }
    },
    
    printReceipt() {
      this.$emit('print-receipt')
    },
    
    continueToNewOrder() {
      this.$emit('new-order')
    },
    
    retryPayment() {
      this.$emit('retry')
    },
    
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2)
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease;
}

.modal-content.processing-modal {
  background: var(--surface-primary);
  border-radius: 20px;
  padding: 40px;
  max-width: 500px;
  width: 90%;
  box-shadow: var(--shadow-2xl);
  animation: slideUp 0.3s ease;
}

.modal-state {
  text-align: center;
}

.modal-state h3 {
  margin: 20px 0 10px;
  font-size: 24px;
  color: var(--text-primary);
}

.modal-state p {
  color: var(--text-secondary);
  font-size: 16px;
  margin: 10px 0;
  line-height: 1.5;
}

.error-message {
  color: var(--error);
}

/* Spinner */
.spinner-large {
  width: 80px;
  height: 80px;
  border: 6px solid var(--border-secondary);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

/* Success Icon */
.success-icon {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--success);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 60px;
  font-weight: bold;
  margin: 0 auto 20px;
  animation: scaleIn 0.4s ease;
}

/* Failed Icon */
.failed-icon {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--error);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 60px;
  font-weight: bold;
  margin: 0 auto 20px;
  animation: shakeX 0.5s ease;
}

/* Payment Details */
.payment-details {
  background: var(--surface-secondary);
  border-radius: 12px;
  padding: 20px;
  margin: 20px 0;
  text-align: left;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-secondary);
  font-size: 15px;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row span {
  color: var(--text-tertiary);
}

.detail-row strong {
  color: var(--text-primary);
  font-weight: 600;
}

/* Modal Actions */
.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.modal-actions .btn {
  flex: 1;
  padding: 12px;
  font-size: 16px;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes scaleIn {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes shakeX {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
  20%, 40%, 60%, 80% { transform: translateX(10px); }
}

/* Responsive */
@media (max-width: 576px) {
  .modal-content.processing-modal {
    padding: 30px 20px;
  }
  
  .modal-state h3 {
    font-size: 20px;
  }
  
  .success-icon,
  .failed-icon {
    width: 80px;
    height: 80px;
    font-size: 48px;
  }
  
  .modal-actions {
    flex-direction: column;
  }
}
</style>