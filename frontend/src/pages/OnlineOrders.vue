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
            <div 
                class="oocard" :class="{ selected: selectedOrder && selectedOrder.id === pendingItems.id }"
                v-for="pendingItems in pendingItems" :key="pendingItems.id" @click="selectOrder(pendingItems)">
              <div class ="cardtop" >
                <div class ="cdtop-left">
                  <h1>Order # {{ pendingItems.id }}</h1>
                </div>
                <div class ="cdtop-right">
                  <h2>17:24</h2>
                </div>
              </div>
              <div class = "cardbot">
                <div class ="cdbot-left">
                  <h2>Number of items: {{ pendingItems.quantity }}</h2>
                </div>
                <div class ="cdbot-right">
                  <h2>₱{{ pendingItems.total_price }}</h2>
                  <span :class="getBadgeClass(pendingItems.status)">
                    {{ getBadgeText(pendingItems.status) }}
                  </span>
                </div>
              </div> 
            </div>
        </div>
      </div>
      
       <div  v-if="selectedOrder" class = "oo-right" >
        <div class ="or-title">
          <h1 style ="font-weight: bold; font-size: 30px;">Order</h1>
          <h2># {{ selectedOrder.id }}</h2>
          <button @click="closeOrderPanel" class="close-btn">
            <CircleX :size="24" />
          </button>
        </div>
        <div class = "or-body">
          <div class = "orb-header">
            <h3>item</h3>
            <h3>qty</h3>
          </div>
          <div class = "orb-body">
            <div class = "orbb-card">

            </div>
          </div>
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
        { id: '1101', name: 'Item', description: 'Placeholder', total_price: 99, quantity: 4, status: 'pending', timestamp: '17:04',},
        { id: '1102', name: 'Item', description: 'Placeholder', total_price: 99, quantity: 4, status: 'active', timestamp: '17:04' },
        { id: '1103', name: 'Item', description: 'Placeholder', total_price: 99, quantity: 4, status: 'active', timestamp: '17:04' },
        { id: '1104', name: 'Item', description: 'Placeholder', total_price: 99, quantity: 4, status: 'active', timestamp: '17:04' },
        { id: '1105', name: 'Item', description: 'Placeholder', total_price: 99, quantity: 4, status: 'active', timestamp: '17:04' },
        { id: '1106', name: 'Item', description: 'Placeholder', total_price: 99, quantity: 4, status: 'active', timestamp: '17:04' },
        { id: '1107', name: 'Item', description: 'Placeholder', total_price: 99, quantity: 4, status: 'active', timestamp: '17:04' },
        { id: '1108', name: 'Item', description: 'Placeholder', total_price: 99, quantity: 4, status: 'active', timestamp: '17:04' } 
      ],
      cart:[

      ]
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
    return status === 'active' ? 'badge text-bg-success' : 'badge text-bg-secondary';
    },
    getBadgeText(status) {
      return status === 'active' ? 'Active' : 'Pending';
    }
  }
}
</script>

<style scoped>

.oo-contents{
  padding: 0;
  display: flex;
  height: 74vh;
  gap:0.5rem;
}

/** Left side of the OO **/
.oo-left{
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

.oocard{
  height: 120px;
  background-color: white;
  text-align: left;
  width: 93%;  
  border-radius: 10px;
  margin-top: 15px;
  border-style: solid;
  border-width: 2px;
  margin-left: 30px;
  box-shadow: 0px 2px 4px;
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
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.cardtop{
   display: flex;
  justify-content: space-between;
  align-items: center; 
  margin-top: 5px;
  margin-left: 10px;
  margin-right: 10px; 
}
.cardbot{
   display: flex;
  justify-content: space-between;
  align-items: center; 
  margin-top: 30px;
  margin-left: 10px;
  margin-right: 10px; 
}

.cardtop h1, .cardbot h1{
  font-size: 25px;
}
.cardtop h2{
  font-size: 20px;
}

.cardbot h2{
  font-size: 15px;
  margin-top: 10px;
  margin-right: 100px;
}

.cdbot-right{
  display: flex;
  align-items: center; 
  gap: 0.5rem;
}

.cdbot-right h2 {
  margin: 0; 
  padding: 0;
  line-height: 1;
}

.badge{
  height: 20px;
  flex-shrink: 0;
}


/**Right Side of the OO **/
.oo-right{
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

.oocard.selected {
  border-color: #6f42c1;
  border-width: 3px;
}

.orb-header{
  display: flex;
  justify-content: space-between;
  margin-left: 25px;
  margin-right: 40px;
}

.orb-header h3{
    font-size: 20px;
}

.orb-body{
  height: 30vh;
  overflow-y: scroll;
  width: 100%;
}

.orbb-card{
  background-color: #f8f9fa;
  height: 50px;
  width: 87%;
  margin-left: 25px;
  border-radius: 10px;
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

</style>