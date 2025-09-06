<template>
  <div class="history-container">
    <div class="history-contents">
      <h2 class="page-title">Order History</h2>
      
      <!-- Loading state -->
      <div v-if="loading" class="loading-state">
        <p>Loading transactions...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <p>Error: {{ error }}</p>
        <button @click="refreshData()" class="retry-btn">Retry</button>
      </div>

      <!-- No data state -->
      <div v-else-if="orders.length === 0" class="no-data-state">
        <p>No transactions found.</p>
      </div>

      <!-- Table -->
      <div v-else class="table-container">
        <table class="history-table">
          <thead>
            <tr>
              <th scope="col">ID</th>
              <th scope="col">Items</th>
              <th scope="col">Status</th>
              <th scope="col">Date</th>
              <th scope="col">Payment Method</th>
              <th scope="col">Sale Type</th>
              <th scope="col">Total</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody class="table-group-divider">
            <!-- Use orders directly, not paginatedOrders -->
            <tr v-for="order in orders" :key="order.id">
              <th scope="row">{{ order.id }}</th>
              <td>{{ order.itemCount }} items</td>
              <td>
                <span class="status-badge" :class="getStatusClass(order.status)">
                  {{ order.status }}
                </span>
              </td>
              <td>{{ formatDate(order.date) }}</td>
              <td>{{ order.paymentMethod }}</td>
              <td>{{ order.saleType }}</td>
              <td class="total-amount">₱{{ order.total.toFixed(2) }}</td>
              <td>
                <div class="action-buttons">
                  <button 
                    class="action-btn view-btn" 
                    title="View Order"
                    @click="viewOrder(order.id)"
                  >
                    👁️
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="pagination-container" v-if="totalPages > 1">
        <div class="pagination-info">
          <small>Showing {{ startItem }}-{{ endItem }} of {{ totalOrders }} orders</small>
        </div>
        <div class="pagination-controls">
          <button 
            class="page-btn" 
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
          >
            ←
          </button>
          
          <button 
            v-for="page in totalPages" 
            :key="page"
            class="page-btn"
            :class="{ active: page === currentPage }"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
          
          <button 
            class="page-btn" 
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
            →
          </button>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="orderModal" tabindex="-1" role="dialog" aria-labelledby="orderModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="orderModalLabel">Order Details</h5>
            <button type="button" class="close" data-bs-dismiss="modal" aria-label="Close">
              <span aria-hidden="true"><CircleX/></span>
            </button>
          </div>
          <div class="modal-body">
            <div v-if="selectedOrder">
              <div class="order-info">
                <!--<h6>Order Information</h6>-->
                <p><strong>Order ID:</strong> {{ selectedOrder.id }}</p>
                <p><strong>Status:</strong> 
                  <span class="status-badge" :class="getStatusClass(selectedOrder.status)">
                     {{ selectedOrder.status }}
                  </span>
                </p>
                <p><strong>Date:</strong> {{ formatDate(selectedOrder.date) }}</p>
                <p><strong>Payment Method:</strong> {{ selectedOrder.paymentMethod }}</p>
                <p><strong>Sale Type:</strong> {{ selectedOrder.saleType }}</p>
              </div>

              <!-- Items Details Section -->
              <div v-if="selectedOrder.originalData?.items" class="items-section">
                <h6>Items Ordered</h6>
                <div class="items-grid">
                  <div 
                    v-for="item in selectedOrder.originalData.items" 
                    :key="item.product_id"
                    class="item-tag"
                  >
                    {{ item.product_name }}
                    <span class="item-qty">({{ item.quantity }})</span>
                  </div>
                </div>
                
                <!-- Items Summary -->
                <div class="items-summary">
                  <div class="summary-row">
                    <span>Total Items:</span>
                    <strong>{{ getTotalItems(selectedOrder.originalData.items) }}</strong>
                  </div>
                  <div class="summary-row">
                    <span>Total Amount:</span>
                    <strong>₱{{ selectedOrder.total.toFixed(2) }}</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
           <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import historyAPIService from '@/services/apiHistory.js';

export default {
  name: 'History',
  data() {
    return {
      currentPage: 1,
      itemsPerPage: 8,
      orders: [],
      selectedOrder: null,
      loading: false,
      error: null,
      totalOrders: 0,
      totalPages: 0
    }
  },
  computed: {
    startItem() {
      return (this.currentPage - 1) * this.itemsPerPage + 1
    },
    endItem() {
      return Math.min(this.currentPage * this.itemsPerPage, this.totalOrders)
    }
  },
  async mounted() {
    await this.fetchHistory()
  },
  methods: {
    async fetchHistory() {
      try {
        this.loading = true
        this.error = null

        console.log('Fetching history...') // Debug log

        const result = await historyAPIService.loadHistory({
          page: this.currentPage,
          pageSize: this.itemsPerPage
        })

        console.log('API Result:', result) // Debug log

        this.orders = result.transactions
        this.totalOrders = result.totalCount
        this.totalPages = result.totalPages

        console.log('Orders set:', this.orders) // Debug log

      } catch (error) {
        console.error('Error loading history:', error)
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async goToPage(page) {
      if (page >= 1 && page <= this.totalPages && page !== this.currentPage) {
        this.currentPage = page
        await this.fetchHistory()
      }
    },

    getStatusClass(status) {
      const classes = {
        'Completed': 'status-completed',
        'Pending': 'status-pending',
        'Processing': 'status-processing',
        'Cancelled': 'status-cancelled',
        'Refunded': 'status-refunded'
      }
      return classes[status] || 'status-default'
    },

    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    },

    viewOrder(orderId) {
      this.selectedOrder = this.orders.find(order => order.id === orderId)
      const modalElement = document.getElementById('orderModal')
      if (modalElement && window.bootstrap) {
        const modal = new bootstrap.Modal(modalElement)
        modal.show()
      }
    },

    async refreshData() {
      await this.fetchHistory()
    },

    getTotalItems(items) {
      return items.reduce((sum, item) => sum + item.quantity, 0)
    },

    viewOrder(orderId) {
      this.selectedOrder = this.orders.find(order => order.id === orderId)
      console.log('Selected order with items:', this.selectedOrder) // Debug log
      const modalElement = document.getElementById('orderModal')
      if (modalElement && window.bootstrap) {
        const modal = new bootstrap.Modal(modalElement)
        modal.show()
      }
    }
  }
}
</script>

<style scoped>
.history-container {
  padding: 1.5rem;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.history-contents {
  background: white;
  border-radius: 0.75rem;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.page-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e2e8f0;
}

/* Loading, Error, No Data States */
.loading-state, .error-state, .no-data-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.retry-btn {
  background: #567cdc;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  margin-top: 1rem;
}

.table-container {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 1rem;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table thead {
  background-color: #567cdc;
  color: white;
}

.history-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  border: none;
}

.history-table td {
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.875rem;
}

.history-table tbody tr:hover {
  background-color: #f7fafc;
}

/* Status badges */
.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-completed {
  background-color: #10b981;
  color: white;
}

.status-pending {
  background-color: #f59e0b;
  color: white;
}

.status-processing {
  background-color: #3b82f6;
  color: white;
}

.status-cancelled {
  background-color: #ef4444;
  color: white;
}

.status-refunded {
  background-color: #6b7280;
  color: white;
}

.total-amount {
  font-weight: 600;
  color: #2d3748;
  text-align: right;
}

/* Action buttons */
.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  border: 1px solid #3b82f6;
  background: white;
  color: #3b82f6;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background-color: #3b82f6;
  color: white;
}

/* Pagination */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-top: 1px solid #e2e8f0;
}

.pagination-info {
  color: #6b7280;
  font-size: 0.875rem;
}

.pagination-controls {
  display: flex;
  gap: 0.25rem;
}

.page-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background-color: #f9fafb;
  border-color: #9ca3af;
}

.page-btn.active {
  background-color: #567cdc;
  border-color: #567cdc;
  color: white;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close {
  background: none;
  border: none;
  cursor: pointer;
  color: #6c757d;
  padding: 0.25rem;
  border-radius: 50%;
  transition: all 0.2s ease;
  margin-left: auto; /* This pushes it to the right */
}

.close:hover {
  background-color: #f8f9fa;
  color: #495057;
}

/* Items section styling */
.items-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.items-section h6 {
  margin-bottom: 1rem;
  color: #2d3748;
  font-weight: 600;
}

/* Grid layout for items - max 5 per row */
.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin: 1rem 0;
  max-width: 100%;
}

/* Individual item styling */
.item-tag {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  color: #495057;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.2s ease;
}

.item-tag:hover {
  background: #e9ecef;
  border-color: #567cdc;
}

.item-qty {
  background: #567cdc;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 0.5rem;
}

/* Items summary */
.items-summary {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 0.5rem;
  border-left: 4px solid #567cdc;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
  font-size: 0.9rem;
}

.summary-row:last-child {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #dee2e6;
  font-weight: 600;
  color: #2d3748;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .items-grid {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 0.5rem;
  }
  
  .item-tag {
    padding: 0.4rem 0.6rem;
    font-size: 0.8rem;
    flex-direction: column;
    text-align: center;
    gap: 0.25rem;
  }
  
  .item-qty {
    margin-left: 0;
  }
}

@media (max-width: 480px) {
  .items-grid {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }
}

/* Responsive */
@media (max-width: 768px) {
  .history-container {
    padding: 1rem;
  }
  
  .history-contents {
    padding: 1rem;
  }
  
  .pagination-container {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>