<template>
  <div class="history-container">
    <div class="history-contents">
      <h2 class="page-title">Order History</h2>
      
      <div class="table-container">
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
            <tr v-for="order in paginatedOrders" :key="order.id">
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
                    data-toggle="modal" 
                    data-target="#orderModal"
                    @click="viewOrder(order.id)"
                  >
                    <Eye :size="14" />
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
            <ChevronLeft :size="16" />
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
            <ChevronRight :size="16" />
          </button>
        </div>
      </div>
    </div>

    <!-- Bootstrap Modal - Moved outside the table -->
    <div class="modal fade" id="orderModal" tabindex="-1" role="dialog" aria-labelledby="orderModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="orderModalLabel">Order Details</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <div v-if="selectedOrder">
              <div class="order-info">
                <h6>Order Information</h6>
                <p><strong>Order ID:</strong> {{ selectedOrder.id }}</p>
                <p><strong>Items:</strong> {{ selectedOrder.itemCount }} items</p>
                <p><strong>Status:</strong> 
                  <span class="status-badge" :class="getStatusClass(selectedOrder.status)">
                    {{ selectedOrder.status }}
                  </span>
                </p>
                <p><strong>Date:</strong> {{ formatDate(selectedOrder.date) }}</p>
                <p><strong>Payment Method:</strong> {{ selectedOrder.paymentMethod }}</p>
                <p><strong>Sale Type:</strong> {{ selectedOrder.saleType }}</p>
                <p><strong>Total:</strong> ₱{{ selectedOrder.total.toFixed(2) }}</p>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script> 

export default {
  name: 'History',
  components: {
  
  },
  data() {
    return {
      currentPage: 1,
      itemsPerPage: 8,
      orders: [
        { id: 1, itemCount: 3, status: 'Completed', date: '2024-03-15', paymentMethod: 'Cash', saleType: 'Dine In', total: 450.00 },
        { id: 2, itemCount: 2, status: 'Pending', date: '2024-03-14', paymentMethod: 'Card', saleType: 'Take Out', total: 320.00 },
        { id: 3, itemCount: 5, status: 'Cancelled', date: '2024-03-13', paymentMethod: 'GCash', saleType: 'Delivery', total: 680.00 },
        { id: 4, itemCount: 1, status: 'Completed', date: '2024-03-12', paymentMethod: 'Cash', saleType: 'Dine In', total: 150.00 },
        { id: 5, itemCount: 4, status: 'Processing', date: '2024-03-11', paymentMethod: 'Card', saleType: 'Take Out', total: 520.00 },
        { id: 6, itemCount: 2, status: 'Completed', date: '2024-03-10', paymentMethod: 'GCash', saleType: 'Delivery', total: 280.00 },
        { id: 7, itemCount: 3, status: 'Completed', date: '2024-03-09', paymentMethod: 'Cash', saleType: 'Dine In', total: 390.00 },
        { id: 8, itemCount: 6, status: 'Refunded', date: '2024-03-08', paymentMethod: 'Card', saleType: 'Take Out', total: 720.00 },
        { id: 9, itemCount: 2, status: 'Completed', date: '2024-03-07', paymentMethod: 'GCash', saleType: 'Delivery', total: 240.00 },
        { id: 10, itemCount: 1, status: 'Completed', date: '2024-03-06', paymentMethod: 'Cash', saleType: 'Dine In', total: 180.00 },
        { id: 11, itemCount: 4, status: 'Processing', date: '2024-03-05', paymentMethod: 'Card', saleType: 'Take Out', total: 480.00 },
        { id: 12, itemCount: 3, status: 'Completed', date: '2024-03-04', paymentMethod: 'GCash', saleType: 'Delivery', total: 360.00 }
      ]
    }
  },
  computed: {
    totalOrders() {
      return this.orders.length
    },
    totalPages() {
      return Math.ceil(this.totalOrders / this.itemsPerPage)
    },
    startItem() {
      return (this.currentPage - 1) * this.itemsPerPage + 1
    },
    endItem() {
      return Math.min(this.currentPage * this.itemsPerPage, this.totalOrders)
    },
    paginatedOrders() {
      const start = (this.currentPage - 1) * this.itemsPerPage
      const end = start + this.itemsPerPage
      return this.orders.slice(start, end)
    }
  },
  methods: {
    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page
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
        this.selectedOrder = this.orders.find(order => order.id === orderId);
        const modal = new bootstrap.Modal(this.$refs.orderModal);
        modal.show();
      },
    
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
  letter-spacing: 0.025em;
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

.history-table tbody tr:last-child td {
  border-bottom: none;
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
  border: 1px solid;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.view-btn {
  border-color: #3b82f6;
  color: #3b82f6;
}

.view-btn:hover {
  background-color: #3b82f6;
  color: white;
}

.edit-btn {
  border-color: #10b981;
  color: #10b981;
}

.edit-btn:hover {
  background-color: #10b981;
  color: white;
}

.delete-btn {
  border-color: #ef4444;
  color: #ef4444;
}

.delete-btn:hover {
  background-color: #ef4444;
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

/* Responsive */
@media (max-width: 768px) {
  .history-container {
    padding: 1rem;
  }
  
  .history-contents {
    padding: 1rem;
  }
  
  .history-table th,
  .history-table td {
    padding: 0.75rem 0.5rem;
    font-size: 0.8125rem;
  }
  
  .action-btn {
    width: 24px;
    height: 24px;
  }
  
  .pagination-container {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>