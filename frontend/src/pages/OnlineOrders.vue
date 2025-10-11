<template>
  <div class="online-orders-page surface-secondary transition-theme">
    <div class="oo-contents">
      <div class="oo-left">
        <div class="tab-headers">
          <ul class="nav-tabs border-bottom-theme">
            <li class="nav-item">
              <button 
                :class="['nav-link', 'text-secondary', 'transition-theme-fast', { active: activeTab === 'pending' }]" 
                @click="activeTab = 'pending'"
              >
                Pending
              </button>
            </li>
            <li class="nav-item">
              <button 
                :class="['nav-link', 'text-secondary', 'transition-theme-fast', { active: activeTab === 'complete' }]" 
                @click="activeTab = 'complete'"
              >
                Complete
              </button>
            </li>
          </ul>
        </div>
        <div class="tab-content">
          <div 
            class="oocard surface-primary border-theme shadow-sm transition-theme hover-lift"
            :class="{ selected: selectedOrder && selectedOrder.id === order.id }"
            v-for="order in filteredOrders" 
            :key="order.id" 
            @click="selectOrder(order)"
          >
            <div class="cardtop">
              <h1 class="text-primary">Order # {{ order.id }}</h1>
              <h2 class="text-secondary">{{ order.timestamp }}</h2>
            </div>
            <div class="cardbot">    
              <h2 class="text-secondary">Number of items: {{ order.quantity }}</h2>
              <div class="cdbot-right">
                <h2 class="text-primary">₱{{ order.total_price }}</h2>
                <span :class="getBadgeClass(order.status)">
                  {{ getBadgeText(order.status) }}
                </span>
              </div>
            </div> 
          </div>
        </div>
      </div>
      
      <div v-if="selectedOrder" class="oo-right surface-primary border-theme shadow-lg transition-theme">
        <!-- Order title -->
        <div class="or-title">
          <div class="title-left">
            <h1 class="text-primary" style="font-weight: bold; font-size: 30px;">Order</h1>
            <h2 class="text-secondary"># {{ selectedOrder.id }}</h2>
          </div>
          <button @click="selectedOrder = null" class="close-btn hover-accent transition-theme-fast">
            <CircleX :size="24" />
          </button>
        </div>

        <div class="or-body">
          <div class="orb-header">
            <h3 class="text-primary">item</h3>
            <h3 class="text-primary">qty</h3>
            <h3 class="text-primary"></h3> <!-- Empty column for checkboxes -->
          </div>
          <div class="orb-body">
            <div v-for="items in selectedOrder.items" :key="items.id" class="orbb-card surface-tertiary border-theme-subtle">
              <span class="item-name text-primary">{{ items.name }}</span>
              <span class="item-qty text-primary">{{ items.quantity }}</span>
              <input type="checkbox" v-model="items.completed" class="item-checkbox focus-theme" />
            </div>
          </div>
        </div>

        <!-- Customer Location -->
        <div class="customer-section surface-tertiary border-theme-subtle">
          <div class="location-row">
            <MapPin class="location-icon text-accent" />
            <div class="location-text">
              <p class="community text-primary">{{ selectedOrder.customer?.community || 'Bamboo bay community' }}</p>
              <p class="address text-secondary">{{ selectedOrder.customer?.address || 'Hernan Cortes St., Subangdaku, Mandaue City' }}</p>
            </div>
          </div>
          
          <div class="phone-row">
            <span class="text-primary">{{ selectedOrder.customer?.phone || '+63 987 6543 210' }}</span>
          </div>
          
          <div class="notes-row">
            <p class="text-primary"><strong>Notes:</strong> <span class="text-secondary">{{ selectedOrder.notes || 'Can wait at the front door' }}</span></p>
          </div>
        </div>

        <!-- Payment Toggle -->
        <div class="payment-section">
          <div class="payment-row">
            <span class="cash-label text-success">Cash Received</span>
            <label class="toggle-switch">
              <input type="checkbox" v-model="selectedOrder.cashReceived" />
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <!-- Complete Button -->
        <div class="complete-section">
          <button 
            class="complete-btn surface-tertiary border-theme text-primary transition-theme-fast hover-accent"
            :class="{ 'state-disabled': !canCompleteOrder }"
            :disabled="!canCompleteOrder" 
            @click="completeOrder"
          >
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
      cart:[]
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
      switch(status) {
        case 'success':
          return 'badge badge-complete';
        case 'pending':
          return 'badge badge-pending';
        case 'processing':
          return 'badge badge-processing';
        case 'cancelled':
          return 'badge badge-cancelled';
        default:
          return 'badge badge-inactive';
      }
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
  padding: 2rem 0 2rem 2rem; /* Add top and bottom padding */
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
  padding: 0;
  overflow-y: scroll;
  height: 100%;
}

/* Updated Card Styles */
.oocard {
  display: flex;
  flex-direction: column;
  padding: 20px;
  border-radius: 12px;
  margin-top: 20px;
  height: auto;
  min-height: 100px;
  cursor: pointer;
}

.oocard.selected {
  background-color: var(--primary) !important; 
  color: white !important; 
  border-color: var(--primary) !important;
  border-width: 3px;
}

.oocard.selected .text-primary,
.oocard.selected .text-secondary {
  color: white !important;
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
}

.cardtop h2 {
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

/**Right Side of the OO **/
.oo-right {
  width: 24%;
  height: 79vh;
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
  color: var(--text-secondary);
  padding: 0.25rem;
  border-radius: 50%;
}

.close-btn:hover {
  background-color: var(--state-hover);
  color: var(--error);
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
  border-radius: 10px;
}

.location-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.location-icon {
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

.complete-section {
  margin: 1rem;
}

.complete-btn {
  width: 100%;
  border: 1px solid var(--border-primary);
  padding: 0.75rem;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.complete-btn:hover:not(:disabled) {
  background-color: var(--primary) !important;
  color: white !important;
}

.complete-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .oo-contents {
    padding-top: 2rem;
    padding-bottom: 2rem;
    display: flex;
    height: 74vh;
    gap: 0.5rem;
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