<template>
  <div class="online-orders-page surface-secondary transition-theme">
    <!-- Loading State -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading orders...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-banner">
      <span>{{ error }}</span>
      <button @click="loadOrders" class="retry-btn">Retry</button>
    </div>

    <div class="oo-contents">
      <!-- LEFT SIDE: Orders List -->
      <div class="oo-left">
        <div class="tab-headers">
          <ul class="nav-tabs">
            <li class="nav-item">
              <button 
                :class="['nav-link', { active: activeTab === 'pending' }]" 
                @click="activeTab = 'pending'"
              >
                Pending ({{ pendingCount }})
              </button>
            </li>
            <li class="nav-item">
              <button 
                :class="['nav-link', { active: activeTab === 'complete' }]" 
                @click="activeTab = 'complete'"
              >
                Complete ({{ completeCount }})
              </button>
            </li>
          </ul>
        </div>

        <div class="tab-content surface-tertiary transition-theme">
          <!-- No orders message -->
          <div v-if="filteredOrders.length === 0" class="no-orders">
            <p>No {{ activeTab }} orders</p>
          </div>

          <!-- Order Cards -->
          <div
            class="oocard surface-primary border-theme shadow-md transition-theme"
            :class="{ selected: selectedOrder && selectedOrder._id === order._id }"
            v-for="order in filteredOrders"
            :key="order._id"
            @click="selectOrder(order)"
          >
            <div class="cardtop">
              <h1 class="text-primary">Order # {{ order._id }}</h1>
              <h2 class="text-secondary">{{ order.timestamp }}</h2>
            </div>
            <div class="cardbot">
              <h2 class="text-secondary">Items: {{ order.quantity }}</h2>
              <div class="cdbot-right">
                <h2 class="text-primary">₱{{ order.total_price.toFixed(2) }}</h2>
                <span :class="getBadgeClass(order.order_status)">
                  {{ getBadgeText(order.order_status) }}
                </span>
              </div>
            </div> 
          </div>
        </div>
      </div>
      
      <!-- RIGHT SIDE: Order Details -->
      <div v-if="selectedOrder" class="oo-right surface-primary border-theme shadow-md transition-theme">
        <!-- Header -->
        <div class="or-title">
          <div class="title-left">
            <h1 class="text-primary" style="font-weight: bold; font-size: 24px;">Order</h1>
            <h2 class="text-secondary" style="font-size: 14px; margin-top: 0.35rem;"># {{ selectedOrder._id }}</h2>
          </div>
          <button @click="selectedOrder = null" class="close-btn text-secondary hover-accent transition-theme-fast">
            <CircleX :size="24" />
          </button>
        </div>

        <!-- Order Status Badge -->
        <div class="status-badge-container">
          <span :class="'status-badge status-' + selectedOrder.order_status">
            {{ formatStatus(selectedOrder.order_status) }}
          </span>
          <span v-if="selectedOrder.payment_method !== 'cod'" class="payment-badge">
            {{ selectedOrder.payment_method.replace('_paymongo', '').toUpperCase() }}
          </span>
        </div>

        <!-- Items List -->
        <div class="or-body">
          <div class="orb-header">
            <h3 class="text-tertiary">Item</h3>
            <h3 class="text-tertiary">Qty</h3>
          </div>
          <div class="orb-body">
            <div v-for="item in selectedOrder.items" :key="item.product_id" class="orbb-card surface-elevated border-theme-subtle transition-theme">
              <span class="item-name text-primary">{{ item.product_name }}</span>
              <span class="item-qty text-primary">{{ item.quantity }}</span>
            </div>
          </div>
        </div>

        <!-- Customer Info -->
        <div class="customer-section surface-elevated border-theme-subtle transition-theme">
          <div class="location-row">
            <MapPin class="location-icon text-secondary" :size="20" />
            <div class="location-text">
              <p class="community text-primary">{{ selectedOrder.customer.community }}</p>
              <p class="address text-secondary">{{ selectedOrder.customer.address }}</p>
            </div>
          </div>

          <div class="phone-row">
            <span class="text-primary">{{ selectedOrder.customer.phone }}</span>
          </div>

          <div class="notes-row">
            <p class="text-secondary"><strong>Notes:</strong> {{ selectedOrder.notes }}</p>
          </div>
        </div>

        <!-- Payment Section (COD only) -->
        <div v-if="selectedOrder.payment_method === 'cod'" class="payment-section">
          <div class="payment-row">
            <span class="cash-label text-success">Cash Received</span>
            <label class="toggle-switch">
              <input 
                type="checkbox" 
                v-model="selectedOrder.cashReceived"
                :disabled="selectedOrder.order_status === 'completed'"
              />
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <!-- Payment Confirmation (PayMongo) -->
        <div 
          v-if="selectedOrder.payment_method !== 'cod' && selectedOrder.payment_status === 'pending'" 
          class="payment-confirm-section"
        >
          <button class="confirm-payment-btn" @click="confirmPayment">
            Confirm Payment Received
          </button>
        </div>

        <!-- Action Buttons -->
        <div class="actions-section">
          <!-- Start Processing -->
          <button 
            v-if="['pending', 'confirmed'].includes(selectedOrder.order_status)"
            class="action-btn btn-start"
            @click="progressOrder"
          >
            Start Processing
          </button>
          
          <!-- Mark Ready for Delivery -->
          <button
            v-if="selectedOrder.order_status === 'processing'"
            class="action-btn btn-ready"
            @click="progressOrder"
          >
            Mark Ready for Delivery
          </button>
          
          <!-- Complete Order -->
          <button 
            v-if="selectedOrder.order_status === 'on_the_way'"
            class="complete-btn" 
            :disabled="!canCompleteOrder" 
            @click="completeOrder"
          >
            Complete <ChevronRight :size="20" />
          </button>

          <!-- Cancel Order -->
          <button 
            v-if="['pending', 'confirmed'].includes(selectedOrder.order_status)"
            class="action-btn btn-cancel"
            @click="cancelOrder"
          >
            Cancel Order
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiOnlineOrders from '@/services/apiOnlineOrder'
import { CircleX, MapPin, ChevronRight } from 'lucide-vue-next'

export default {
  name: 'OnlineOrder',
  components: {
    CircleX,
    MapPin,
    ChevronRight
  },
  data() {
    return {
      activeTab: 'pending',
      selectedOrder: null,
      orders: [],
      loading: false,
      error: null,
      currentUser: null,
      refreshInterval: null
    }
  },
  computed: {
    filteredOrders() {
      return this.orders.filter(order => {
        if (this.activeTab === 'pending') {
          return ['pending', 'confirmed', 'processing', 'on_the_way'].includes(order.order_status)
        } else if (this.activeTab === 'complete') {
          return order.order_status === 'completed'
        }
        return false
      })
    },
    
    pendingCount() {
      return this.orders.filter(order => 
        ['pending', 'confirmed', 'processing', 'on_the_way'].includes(order.order_status)
      ).length
    },

    completeCount() {
      return this.orders.filter(order => order.order_status === 'completed').length
    },

    canCompleteOrder() {
      if (!this.selectedOrder) return false

      const paymentReady = this.selectedOrder.payment_method === 'cod'
        ? this.selectedOrder.cashReceived
        : this.selectedOrder.payment_status === 'paid'
      const isOnTheWay = this.selectedOrder.order_status === 'on_the_way'

      return paymentReady && isOnTheWay
    }
  },

  async mounted() {
    this.currentUser = this.getCurrentUser()
    await this.loadOrders()
    
    // Auto-refresh every 30 seconds
    this.refreshInterval = setInterval(() => {
      this.loadOrders()
    }, 30000)
  },

  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  },

  methods: {
    async loadOrders() {
      try {
        this.loading = true
        this.error = null
        
        const response = await apiOnlineOrders.getAllOrders()
        
        if (response.success) {
          this.orders = response.data.orders.map(order => this.transformOrder(order))
        }
      } catch (error) {
        console.error('Error loading orders:', error)
        this.error = 'Failed to load orders. Please try again.'
      } finally {
        this.loading = false
      }
    },

    transformOrder(apiOrder) {
      return {
        ...apiOrder,
        id: apiOrder._id,
        total_price: apiOrder.total_amount,
        quantity: apiOrder.items.reduce((sum, item) => sum + item.quantity, 0),
        timestamp: this.formatTime(apiOrder.transaction_date),
        cashReceived: apiOrder.payment_status === 'paid',
        items: apiOrder.items,
        customer: {
          community: apiOrder.delivery_address.barangay || 'Not specified',
          address: `${apiOrder.delivery_address.street}, ${apiOrder.delivery_address.city}`,
          phone: apiOrder.delivery_address.recipient_phone || apiOrder.customer_phone
        },
        notes: apiOrder.delivery_address.delivery_notes || apiOrder.notes || 'No notes'
      }
    },

    formatTime(dateString) {
      const date = new Date(dateString)
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      })
    },

    formatStatus(status) {
      const statusMap = {
        'pending': 'Pending',
        'confirmed': 'Confirmed',
        'processing': 'Processing',
        'on_the_way': 'On the Way',
        'completed': 'Completed',
        'cancelled': 'Cancelled'
      }
      return statusMap[status] || status
    },

    selectOrder(order) {
      this.selectedOrder = JSON.parse(JSON.stringify(order))
    },

    getBadgeClass(status) {
      const classes = {
        'completed': 'badge text-bg-success',
        'cancelled': 'badge text-bg-danger',
        'pending': 'badge text-bg-warning',
        'confirmed': 'badge text-bg-info',
        'processing': 'badge text-bg-primary',
        'on_the_way': 'badge text-bg-secondary'
      }
      return classes[status] || 'badge text-bg-secondary'
    },

    getBadgeText(status) {
      return this.formatStatus(status)
    },

    getCurrentUser() {
      // TODO: Replace with actual auth
      const userData = localStorage.getItem('user')
      if (userData) {
        const user = JSON.parse(userData)
        return { id: user._id || user.id, name: user.username || user.name }
      }
      return { id: 'USER-0003', name: 'Cashier' }
    },

    async progressOrder() {
      if (!this.selectedOrder) return

      try {
        const orderId = this.selectedOrder._id
        const currentStatus = this.selectedOrder.order_status

        if (currentStatus === 'pending' || currentStatus === 'confirmed') {
          await this.startProcessing(orderId)
        } else if (currentStatus === 'processing') {
          await this.markReady(orderId)
        }

        await this.loadOrders()
        const updatedOrder = this.orders.find(o => o._id === orderId)
        if (updatedOrder) {
          this.selectedOrder = updatedOrder
        }

      } catch (error) {
        console.error('Error progressing order:', error)
        alert('Failed to update order status')
      }
    },

    async startProcessing(orderId) {
      await apiOnlineOrders.updateOrderStatus(
        orderId,
        'processing',
        this.currentUser.id,
        'Started preparing order'
      )
    },

    async markReady(orderId) {
      await apiOnlineOrders.markReadyForDelivery(
        orderId,
        this.currentUser.id,
        'Order packed and ready'
      )
    },

    async confirmPayment() {
      if (!this.selectedOrder) return

      try {
        await apiOnlineOrders.confirmPayment(
          this.selectedOrder._id,
          null, // No PayMongo reference needed
          this.currentUser.id
        )
        
        alert('Payment confirmed successfully!')
        await this.loadOrders()
        
        const updatedOrder = this.orders.find(o => o._id === this.selectedOrder._id)
        if (updatedOrder) {
          this.selectedOrder = updatedOrder
        }
      } catch (error) {
        console.error('Error confirming payment:', error)
        alert('Failed to confirm payment')
      }
    },

    async completeOrder() {
      if (!this.canCompleteOrder) return

      try {
        const deliveryPerson = prompt('Enter delivery person name (optional):') || null
        
        await apiOnlineOrders.completeOrder(
          this.selectedOrder._id,
          this.currentUser.id,
          deliveryPerson
        )
        
        alert('Order completed! Customer earned loyalty points.')
        await this.loadOrders()
        this.selectedOrder = null
        
      } catch (error) {
        console.error('Error completing order:', error)
        alert('Failed to complete order')
      }
    },

    async cancelOrder() {
      if (!this.selectedOrder) return

      const reason = prompt('Enter cancellation reason:')
      if (!reason) return

      if (!confirm('Are you sure you want to cancel this order? Stock and points will be restored.')) {
        return
      }

      try {
        await apiOnlineOrders.cancelOrder(
          this.selectedOrder._id,
          reason,
          this.currentUser.id
        )
        
        alert('Order cancelled. Stock and points have been restored.')
        await this.loadOrders()
        this.selectedOrder = null
        
      } catch (error) {
        console.error('Error cancelling order:', error)
        alert('Failed to cancel order')
      }
    }
  }
}
</script>

<style scoped>
/* Loading & Error States */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--surface-primary);
  opacity: 0.95;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.spinner {
  border: 4px solid var(--border-secondary);
  border-top: 4px solid var(--primary);
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-overlay p {
  color: var(--primary);
  font-weight: 600;
}

.error-banner {
  background-color: var(--error-light);
  color: var(--error-dark);
  padding: 1rem;
  margin: 1rem;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.retry-btn {
  background-color: var(--error);
  color: var(--text-inverse);
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.retry-btn:hover {
  background-color: var(--error-dark);
}

/* Main Layout */
.online-orders-page {
  padding: 0;
  overflow-x: hidden;
}

.oo-contents {
  padding: 2rem 1.5rem 2rem 2rem;
  display: flex;
  height: 74vh;
  gap: 1rem;
  border-bottom: 1px solid var(--border-secondary);
  max-width: 100vw;
  box-sizing: border-box;
  border-radius: 1rem;
}

/* Left Side */
.oo-left {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tab-headers {
  flex-shrink: 0;
}

.nav-tabs {
  display: flex;
  list-style: none;
  padding: 0;
  margin: 0;
  border-bottom: 2px solid var(--border-secondary);
}

.nav-item {
  margin-right: 1rem;
}

.nav-link {
  background: none;
  border: none;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
}

.nav-link:hover {
  color: var(--text-primary) !important;
}

.nav-link.active {
  color: var(--primary) !important;
  border-bottom-color: var(--primary);
  background-color: var(--surface-primary);
  border-radius: 0.5rem 0.5rem 0 0;
}

.tab-content {
  padding: 0.75rem;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  border-radius: 0 0.5rem 0.5rem 0.5rem;
}

.no-orders {
  text-align: center;
  padding: 3rem;
  color: var(--text-tertiary);
  font-size: 1.2rem;
}

/* Order Cards */
.oocard {
  display: flex;
  flex-direction: column;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 0.75rem;
  cursor: pointer;
}

.oocard:hover {
  box-shadow: var(--shadow-lg) !important;
  border-color: var(--border-accent) !important;
  transform: translateY(-2px);
}

.oocard.selected {
  background-color: var(--primary) !important;
  color: var(--text-inverse) !important;
  border-color: var(--primary) !important;
  border-width: 2px !important;
}

.oocard.selected h1,
.oocard.selected h2,
.oocard.selected .text-primary,
.oocard.selected .text-secondary {
  color: var(--text-inverse) !important;
}

.cardtop {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.cardtop h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cardtop h2 {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
  white-space: nowrap;
}

.cardbot {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cardbot h2 {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

.cdbot-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cdbot-right h2 {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}

.badge {
  height: 24px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  display: flex;
  align-items: center;
}

/* Right Side */
.oo-right {
  width: 320px;
  min-width: 280px;
  max-width: 350px;
  height: 100%;
  border-radius: 10px;
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
}

.or-title {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0 1rem;
  margin-bottom: 1rem;
}

.title-left {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
  min-width: 0;
  overflow: hidden;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background-color: var(--state-hover);
  color: var(--error);
}

/* Status Badges */
.status-badge-container {
  padding: 0 1rem;
  margin-bottom: 1rem;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.status-badge {
  padding: 0.4rem 0.75rem;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.status-pending {
  background-color: #ffc107;
  color: #000;
}

.status-confirmed {
  background-color: #17a2b8;
  color: white;
}

.status-processing {
  background-color: #007bff;
  color: white;
}

.status-on_the_way {
  background-color: #6f42c1;
  color: white;
}

.status-completed {
  background-color: #28a745;
  color: white;
}

.payment-badge {
  padding: 0.4rem 0.75rem;
  border-radius: 16px;
  font-size: 11px;
  font-weight: 600;
  background-color: var(--surface-elevated);
  color: var(--text-secondary);
  white-space: nowrap;
}

/* Items List */
.or-body {
  padding: 0 1rem;
}

.orb-header {
  display: flex;
  justify-content: space-between;
  padding: 0 1rem;
  margin-bottom: 0.5rem;
  gap: 1rem;
}

.orb-header h3:first-child {
  flex: 1;
  font-size: 13px;
}

.orb-header h3:last-child {
  width: 28px;
  text-align: center;
  font-size: 13px;
}

.orb-body {
  max-height: 30vh;
  overflow-y: auto;
  overflow-x: hidden;
}

.orbb-card {
  height: 45px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  margin-bottom: 0.5rem;
  gap: 1rem;
}

.item-name {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.item-qty {
  width: 28px;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

/* Customer Section */
.customer-section {
  margin: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
}

.location-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 0.5rem;
}

.location-icon {
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.location-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.location-text p {
  margin: 0.2rem 0;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.community {
  font-weight: 600;
  white-space: nowrap;
}

.phone-row {
  margin-bottom: 0.75rem;
  font-size: 13px;
  font-weight: 600;
  word-break: break-word;
}

.notes-row p {
  margin: 0;
  font-size: 12px;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* Payment Section */
.payment-section {
  padding: 0 1rem;
  margin-bottom: 1rem;
}

.payment-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.cash-label {
  font-weight: 600;
  font-size: 13px;
  flex: 1;
}

.toggle-switch {
  position: relative;
  width: 50px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--neutral-medium);
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--primary);
}

input:checked + .slider:before {
  transform: translateX(26px);
}

input:disabled + .slider {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Payment Confirmation */
.payment-confirm-section {
  padding: 0 1rem;
  margin-bottom: 1rem;
}

.confirm-payment-btn {
  width: 100%;
  background-color: #17a2b8;
  color: white;
  border: none;
  padding: 0.65rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  transition: all 0.2s ease;
}

.confirm-payment-btn:hover {
  background-color: #138496;
}

/* Action Buttons */
.actions-section {
  padding: 0 1rem;
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.action-btn {
  width: 100%;
  padding: 0.65rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  transition: all 0.2s ease;
}

.btn-start {
  background-color: #6f42c1;
  color: white;
}

.btn-start:hover {
  background-color: #5a32a3;
}

.btn-ready {
  background-color: #28a745;
  color: white;
}

.btn-ready:hover {
  background-color: #218838;
}

.btn-cancel {
  background-color: #dc3545;
  color: white;
}

.btn-cancel:hover {
  background-color: #c82333;
}

.complete-btn {
  width: 100%;
  background-color: #28a745;
  color: white;
  border: none;
  padding: 0.65rem;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 13px;
  transition: all 0.2s ease;
}

.complete-btn:hover:not(:disabled) {
  background-color: #218838;
}

.complete-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
}

/* Responsive */
@media (max-width: 1024px) {
  .oo-contents {
    flex-direction: column;
    height: auto;
    padding: 1.5rem;
  }

  .oo-left {
    width: 100%;
  }

  .oo-right {
    width: 100%;
    max-width: 100%;
    min-width: 100%;
  }
}
</style>