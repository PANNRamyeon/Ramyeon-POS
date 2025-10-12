<template>
  <div class="online-orders-page">
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

        <div class="tab-content">
          <!-- No orders message -->
          <div v-if="filteredOrders.length === 0" class="no-orders">
            <p>No {{ activeTab }} orders</p>
          </div>

          <!-- Order Cards -->
          <div 
            class="oocard" 
            :class="{ selected: selectedOrder && selectedOrder._id === order._id }"
            v-for="order in filteredOrders" 
            :key="order._id" 
            @click="selectOrder(order)"
          >
            <div class="cardtop">
              <h1>Order # {{ order._id }}</h1>
              <h2>{{ order.timestamp }}</h2>
            </div>
            <div class="cardbot">    
              <h2>Items: {{ order.quantity }}</h2>
              <div class="cdbot-right">
                <h2>₱{{ order.total_price.toFixed(2) }}</h2>
                <span :class="getBadgeClass(order.order_status)">
                  {{ getBadgeText(order.order_status) }}
                </span>
              </div>
            </div> 
          </div>
        </div>
      </div>
      
      <!-- RIGHT SIDE: Order Details -->
      <div v-if="selectedOrder" class="oo-right">
        <!-- Header -->
        <div class="or-title">
          <div class="title-left">
            <h1 style="font-weight: bold; font-size: 30px;">Order</h1>
            <h2># {{ selectedOrder._id }}</h2>
          </div>
          <button @click="selectedOrder = null" class="close-btn">
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
            <h3>Item</h3>
            <h3>Qty</h3>
            <h3>✓</h3>
          </div>
          <div class="orb-body">
            <div v-for="item in selectedOrder.items" :key="item.product_id" class="orbb-card">
              <span class="item-name">{{ item.product_name }}</span>
              <span class="item-qty">{{ item.quantity }}</span>
              <input 
                type="checkbox" 
                v-model="item.completed" 
                class="item-checkbox"
                :disabled="selectedOrder.order_status === 'completed'"
              />
            </div>
          </div>
        </div>

        <!-- Customer Info -->
        <div class="customer-section">
          <div class="location-row">
            <MapPin class="location-icon" :size="20" />
            <div class="location-text">
              <p class="community">{{ selectedOrder.customer.community }}</p>
              <p class="address">{{ selectedOrder.customer.address }}</p>
            </div>
          </div>
          
          <div class="phone-row">
            <span>{{ selectedOrder.customer.phone }}</span>
          </div>
          
          <div class="notes-row">
            <p><strong>Notes:</strong> {{ selectedOrder.notes }}</p>
          </div>
        </div>

        <!-- Payment Section (COD only) -->
        <div v-if="selectedOrder.payment_method === 'cod'" class="payment-section">
          <div class="payment-row">
            <span class="cash-label">Cash Received</span>
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
            :disabled="!allItemsChecked"
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

    allItemsChecked() {
      if (!this.selectedOrder) return false
      return this.selectedOrder.items.every(item => item.completed)
    },
    
    canCompleteOrder() {
      if (!this.selectedOrder) return false
      
      const allItemsCompleted = this.selectedOrder.items.every(item => item.completed)
      const paymentReady = this.selectedOrder.payment_method === 'cod' 
        ? this.selectedOrder.cashReceived 
        : this.selectedOrder.payment_status === 'paid'
      const isOnTheWay = this.selectedOrder.order_status === 'on_the_way'
      
      return allItemsCompleted && paymentReady && isOnTheWay
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
        items: apiOrder.items.map(item => ({
          ...item,
          completed: false
        })),
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
          if (!this.allItemsChecked) {
            alert('Please check off all items before marking ready for delivery')
            return
          }
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

      const reference = prompt('Enter PayMongo payment reference ID:')
      if (!reference) return

      try {
        await apiOnlineOrders.confirmPayment(
          this.selectedOrder._id,
          reference,
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
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #6f42c1;
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
  color: #6f42c1;
  font-weight: 600;
}

.error-banner {
  background-color: #f8d7da;
  color: #721c24;
  padding: 1rem;
  margin: 1rem;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.retry-btn {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
}

.retry-btn:hover {
  background-color: #c82333;
}

/* Main Layout */
.online-orders-page {
  padding: 0;
}

.oo-contents {
  padding: 0;
  display: flex;
  height: 74vh;
  gap: 0.5rem;
}

/* Left Side */
.oo-left {
  width: 74%;
  height: 100%;
}

.nav-tabs {
  display: flex;
  list-style: none;
  padding: 0;
  margin: 0;
  border-bottom: 2px solid #e9ecef;
}

.nav-item {
  margin-right: 1rem;
}

.nav-link {
  background: none;
  border: none;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  color: #6c757d;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: #495057;
}

.nav-link.active {
  color: #6f42c1;
  border-bottom-color: #6f42c1;
}

.tab-content {
  padding: 0;
  overflow-y: scroll;
  height: 100%;
}

.no-orders {
  text-align: center;
  padding: 3rem;
  color: #6c757d;
  font-size: 1.2rem;
}

/* Order Cards */
.oocard {
  display: flex;
  flex-direction: column;
  padding: 20px;
  background-color: white;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  transition: all 0.2s ease;
  margin-top: 20px;
  cursor: pointer;
}

.oocard:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #dee2e6;
}

.oocard.selected {
  background-color: #6f42c1;
  color: white;
  border-color: #6f42c1;
  border-width: 3px;
}

.oocard.selected h1,
.oocard.selected h2 {
  color: white;
}

.cardtop {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.cardtop h1 {
  font-size: 30px;
  font-weight: 600;
  margin: 0;
  color: #2d3748;
}

.cardtop h2 {
  color: #6b7280;
  font-size: 20px;
  font-weight: 500;
  margin: 0;
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
  color: #6b7280;
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
  color: #2d3748;
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
  width: 24%;
  height: 79vh;
  background-color: white;
  border-radius: 10px;
  overflow-y: auto;
}

.or-title {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-right: 10px;
  margin-left: 20px;
  margin-bottom: 1rem;
}

.title-left {
  display: flex;
  gap: 0.5rem;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #6c757d;
  padding: 0.25rem;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background-color: #f8f9fa;
  color: #dc3545;
}

/* Status Badges */
.status-badge-container {
  margin: 0 1rem 1rem 1rem;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
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
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  background-color: #f8f9fa;
  color: #495057;
}

/* Items List */
.or-body {
  margin: 0 1rem;
}

.orb-header {
  display: flex;
  justify-content: space-between;
  padding: 0 0.5rem;
  margin-bottom: 0.5rem;
}

.orb-header h3 {
  font-size: 16px;
  color: #6c757d;
}

.orb-body {
  max-height: 30vh;
  overflow-y: auto;
}

.orbb-card {
  background-color: #f8f9fa;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  margin-bottom: 0.5rem;
}

.item-name {
  flex: 1;
  font-size: 14px;
}

.item-qty {
  width: 30px;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
}

.item-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

/* Customer Section */
.customer-section {
  margin: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 10px;
}

.location-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.location-icon {
  color: #6f42c1;
  margin-right: 0.5rem;
  flex-shrink: 0;
}

.location-text p {
  margin: 0.2rem 0;
  font-size: 14px;
}

.community {
  font-weight: 600;
}

.address {
  color: #666;
}

.phone-row {
  margin-bottom: 1rem;
  font-size: 14px;
  font-weight: 600;
}

.notes-row p {
  margin: 0;
  font-size: 14px;
}

/* Payment Section */
.payment-section {
  margin: 1rem;
}

.payment-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cash-label {
  color: #28a745;
  font-weight: 600;
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
  background-color: #ccc;
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
  background-color: #6f42c1;
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
  margin: 1rem;
}

.confirm-payment-btn {
  width: 100%;
  background-color: #17a2b8;
  color: white;
  border: none;
  padding: 0.75rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.confirm-payment-btn:hover {
  background-color: #138496;
}

/* Action Buttons */
.actions-section {
  margin: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.action-btn {
  width: 100%;
  padding: 0.75rem;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  font-weight: 600;
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

.btn-ready:hover:not(:disabled) {
  background-color: #218838;
}

.btn-ready:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
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
  padding: 0.75rem;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
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
@media (max-width: 768px) {
  .oo-contents {
    flex-direction: column;
    height: auto;
  }
  
  .oo-left,
  .oo-right {
    width: 100%;
  }
}
</style>