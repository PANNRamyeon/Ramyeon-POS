<template>
  <div class="online-orders-page">
    <div class = "oo-contents">
        <div class = "oo-left">
          <div class="tab-headers">
            <ul class="nav-tabs">
              <li class="nav-item">
                <button :class="['nav-link', { active: activeTab === 'pending' }]" @click="activeTab = 'pending'">
                  Pending
                </button>
              </li>
              <li class="nav-item">
                <button :class="['nav-link', { active: activeTab === 'complete' }]" @click="activeTab = 'complete'">
                  Complete
                </button>
              </li>
            </ul>
          </div>
          <div class="tab-content">
            <div class="oocard" :class="{ selected: selectedOrder && selectedOrder.id === order.id }"
                  v-for="order in filteredOrders" :key="order.id" @click="selectOrder(order)">
              <div class="cardtop">
                  <h1>Order # {{ order.id }}</h1>
                  <h2>{{ order.timestamp }}</h2>
              </div>
              <div class="cardbot">    
                  <h2>Number of items: {{ order.quantity }}</h2>
 
                <div class="cdbot-right">
                  <h2>₱{{ order.total_price }}</h2>
                  <span :class="getBadgeClass(order.status)">
                    {{ getBadgeText(order.status) }}
                  </span>
                </div>
              </div> 
            </div>
        </div>
      </div>
      
      <div v-if="selectedOrder" class="oo-right">
        <!-- Keep your existing or-title -->
        <div class="or-title">
          <div class="title-left">
            <h1 style="font-weight: bold; font-size: 30px;">Order</h1>
            <h2># {{ selectedOrder.id }}</h2>
          </div>
          <button @click="selectedOrder = null" class="close-btn">
            <CircleX :size="24" />
          </button>
        </div>

        <div class="or-body">
          <div class="orb-header">
            <h3>item</h3>
            <h3>qty</h3>
            <h3></h3> <!-- Empty column for checkboxes -->
          </div>
          <div class="orb-body">
            <div v-for="items in selectedOrder.items" :key="items.id" class="orbb-card">
              <span class="item-name">{{ items.name }}</span>
              <span class="item-qty">{{ items.quantity }}</span>
              <input type="checkbox" v-model="items.completed" class="item-checkbox" />
            </div>
          </div>
        </div>

        <!-- Customer Location -->
        <div class="customer-section">
          <div class="location-row">
            <MapPin class="location-icon" />
            <div class="location-text">
              <p class="community">{{ selectedOrder.customer?.community || 'Bamboo bay community' }}</p>
              <p class="address">{{ selectedOrder.customer?.address || 'Hernan Cortes St., Subangdaku, Mandaue City' }}</p>
            </div>
          </div>
          
          <div class="phone-row">
            <span>{{ selectedOrder.customer?.phone || '+63 987 6543 210' }}</span>
          </div>
          
          <div class="notes-row">
            <p><strong>Notes:</strong> {{ selectedOrder.notes || 'Can wait at the front door' }}</p>
          </div>
        </div>

        <!-- Payment Toggle -->
        <div class="payment-section">
          <div class="payment-row">
            <span class="cash-label">Cash Received</span>
            <label class="toggle-switch">
              <input type="checkbox" v-model="selectedOrder.cashReceived" />
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <!-- Complete Button -->
        <div class="complete-section">
          <button class="complete-btn" :disabled="!canCompleteOrder" @click="completeOrder">
            Complete <ChevronRight />
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script>

export default {
  name: 'OnlineOrder',
  data() {
    return {
      activeTab: 'pending',
      selectedOrder: null,
      pendingItems: [
        { 
          id: '1101', 
          total_price: 99, 
          quantity: 4, 
          status: 'pending', 
          timestamp: '17:04',
          cashReceived: false,
          customer: {
            community: 'Bamboo bay community',
            address: 'Hernan Cortes St., Subangdaku, Mandaue City',
            phone: '+63 987 6543 210'
          },
          notes: 'Can wait at the front door',
          items: [
            { id: 1, name: 'Placeholder Item 1', quantity: 1, completed: false },
            { id: 2, name: 'Placeholder Item 2', quantity: 2, completed: false }
          ]
        },
         { 
          id: '1102', 
          total_price: 99, 
          quantity: 4, 
          status: 'success', 
          timestamp: '17:04',
          cashReceived: false,
          customer: {
            community: 'Bamboo bay community',
            address: 'Hernan Cortes St., Subangdaku, Mandaue City',
            phone: '+63 987 6543 210'
          },
          notes: 'Can wait at the front door',
          items: [
            { id: 1, name: 'Placeholder Item 1', quantity: 1, completed: false },
            { id: 2, name: 'Placeholder Item 2', quantity: 2, completed: false }
          ]
        },
        { 
          id: '1103', 
          total_price: 99, 
          quantity: 4, 
          status: 'pending', 
          timestamp: '17:04',
          cashReceived: false,
          customer: {
            community: 'Bamboo bay community',
            address: 'Hernan Cortes St., Subangdaku, Mandaue City',
            phone: '+63 987 6543 210'
          },
          notes: 'Can wait at the front door',
          items: [
            { id: 1, name: 'Placeholder Item 1', quantity: 1, completed: false },
            { id: 2, name: 'Placeholder Item 2', quantity: 2, completed: false }
          ]
        },
      ],
      cart:[

      ]
    }
  },
  computed:{
    filteredOrders() {
      if (this.activeTab === 'pending') {
        return this.pendingItems.filter(order => order.status === 'pending');
      } else if (this.activeTab === 'complete') {
        return this.pendingItems.filter(order => order.status === 'success');
      }
      return this.pendingItems;
    },
    canCompleteOrder() {
      if (!this.selectedOrder) return false;
      
      // Check if all items are completed
      const allItemsCompleted = this.selectedOrder.items.every(item => item.completed);
      
      // Check if cash is received
      const cashReceived = this.selectedOrder.cashReceived;
      
      return allItemsCompleted && cashReceived;
    }
  },

  methods: {
    selectOrder(order) {
      this.selectedOrder = order;
    },
    closeOrderPanel() {
      this.selectedOrder = null;
    },
    getBadgeClass(status) {
    return status === 'success' ? 'badge text-bg-success' : 'badge text-bg-secondary';
    },
    getBadgeText(status) {
      return status === 'success' ? 'Success' : 'Pending';
    },
    completeOrder() {
      if (this.canCompleteOrder) {
      // Change the order status to success
      this.selectedOrder.status = 'success';
      
      // Close the right panel
      this.selectedOrder = null;
      
      console.log('Order completed and moved to Complete tab');
      }
    }
  }
}
</script>

<style scoped>
.oo-contents {
  padding: 0;
  display: flex;
  height: 74vh;
  gap: 0.5rem;
}

/** Left side of the OO **/
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

/* Updated Card Styles */
.oocard {
  display: flex;
  flex-direction: column;
  padding: 20px;
  background-color: white;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  transition: all 0.2s ease;
  margin-top: 20px;
  height: auto;
  min-height: 100px;
  cursor: pointer;
}

.oocard:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #dee2e6;
  background-color: white;
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

.oocard.selected .badge {
  background-color: rgba(255, 255, 255, 0.2) !important;
  color: white !important;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* Top row - Order # and Time with space between */
.cardtop {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
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

/* Bottom row - Items count on left, Price + Badge grouped on right */
.cardbot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.cardbot h2 {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
  color: #6b7280;
}

/* Right side grouping - Price and Badge close together */
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
  flex-shrink: 0;
}

/* Badge color variations */
.text-bg-success {
  background-color: #10b981 !important;
  color: white !important;
}

.text-bg-secondary {
  background-color: #f59e0b !important;
  color: white !important;
}

/* Selected state adjustments */
.oocard.selected .cardtop h1,
.oocard.selected .cdbot-right h2 {
  color: white;
}

.oocard.selected .cardtop h2,
.oocard.selected .cardbot h2 {
  color: rgba(255, 255, 255, 0.8);
}

/**Right Side of the OO **/
.oo-right {
  width: 24%;
  height: 79vh;
  border-left: black;
  background-color: white;
  border-radius: 10px;
}

.or-title {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-right: 10px;
  margin-left: 20px;
}

.orb-header {
  display: flex;
  justify-content: space-between;
  margin-left: 25px;
  margin-right: 40px;
}

.orb-header h3 {
  font-size: 20px;
}

.orb-body {
  height: 30vh;
  overflow-y: scroll;
  width: 100%;
}

.orbb-card {
  background-color: #f8f9fa;
  height: 50px;
  width: 87%;
  margin-left: 25px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  margin-bottom: 0.5rem;
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

.item-name {
  flex: 1;
  font-size: 14px;
}

.item-qty {
  width: 30px;
  text-align: center;
  font-size: 14px;
}

.item-checkbox {
  width: 18px;
  height: 18px;
}

/* Customer section styles */
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
  margin-top: 0.2rem;
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

.complete-section {
  margin: 1rem;
}

.complete-btn {
  width: 100%;
  background-color: #f8f9fa;
  border: 1px solid #ddd;
  padding: 0.75rem;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.complete-btn:hover {
  background-color: #6f42c1;
  color: white;
}

.complete-btn:disabled {
  background-color: #e9ecef;
  color: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
}

.complete-btn:disabled:hover {
  background-color: #e9ecef;
  color: #6c757d;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .oo-contents {
    flex-direction: column;
    height: auto;
  }
  
  .oo-left {
    width: 100%;
  }
  
  .oo-right {
    width: 100%;
    height: auto;
  }
  
  .oocard {
    padding: 15px;
  }
  
  .cardtop {
    margin-bottom: 12px;
  }
  
  .cardtop h1 {
    font-size: 26px;
  }
  
  .cardtop h2 {
    font-size: 18px;
  }
  
  .cardbot h2 {
    font-size: 14px;
  }
  
  .cdbot-right h2 {
    font-size: 20px;
  }
  
  .cdbot-right {
    gap: 8px;
  }
}

@media (max-width: 480px) {
  .oocard {
    padding: 12px;
  }
  
  .cardtop h1 {
    font-size: 22px;
  }
  
  .cardtop h2 {
    font-size: 16px;
  }
  
  .cardbot {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .cdbot-right {
    align-self: flex-end;
  }
}
</style>