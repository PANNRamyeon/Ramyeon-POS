<template>
  <div class="history-container">
    <div class="history-contents">
      <div class="page-header">
        <h2 class="page-title">Order History</h2>
        
        <!-- Inline action controls -->
        <div class="header-controls">
          <!-- Search -->
          <div class="search-box">
            <Search :size="16" />
            <input
              type="text"
              v-model="table.searchQuery"
              @input="table.setSearchQuery($event.target.value)"
              placeholder="Search orders..."
              class="form-control"
            />
          </div>

          <!-- Filters -->
          <select 
            class="form-select"
            @change="table.setFilter('status', $event.target.value)"
          >
            <option value="">All Status</option>
            <option value="Completed">Completed</option>
            <option value="Pending">Pending</option>
            <option value="Processing">Processing</option>
            <option value="Cancelled">Cancelled</option>
            <option value="Refunded">Refunded</option>
          </select>

          <select 
            class="form-select"
            @change="table.setFilter('paymentMethod', $event.target.value)"
          >
            <option value="">All Payment Methods</option>
            <option value="Cash">Cash</option>
            <option value="Card">Card</option>
            <option value="GCash">GCash</option>
          </select>

          <!-- Refresh button -->
          <button class="btn btn-outline-secondary" @click="refreshData">
            <RefreshCw :size="16" />
            Refresh
          </button>
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="table.loading" class="loading-state">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p>Loading transactions...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="table.error" class="error-state">
        <div class="alert alert-danger">
          <strong>Error:</strong> {{ table.error }}
          <button @click="refreshData()" class="btn btn-sm btn-outline-danger ms-2">
            Retry
          </button>
        </div>
      </div>

      <!-- No data state -->
      <div v-else-if="!table.data || table.data.length === 0" class="no-data-state">
        <div class="empty-state">
          <ShoppingBag :size="48" class="text-muted mb-3" />
          <h5>No transactions found</h5>
          <p class="text-muted">Try adjusting your search or filters</p>
        </div>
      </div>

      <!-- Data Table -->
      <TableTemplate
        v-else
        :current-page="table.currentPage"
        :items-per-page="table.config.itemsPerPage"
        :total-items="table.totalItems"
        :show-pagination="true"
        @page-changed="table.goToPage"
      >
        <template #header>
          <tr>
            <th scope="col" @click="table.sortBy('id')" class="sortable">
              ID
              <span v-if="table.sortField === 'id'">
                {{ table.sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th scope="col">Items</th>
            <th scope="col" @click="table.sortBy('status')" class="sortable">
              Status
              <span v-if="table.sortField === 'status'">
                {{ table.sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th scope="col" @click="table.sortBy('date')" class="sortable">
              Date
              <span v-if="table.sortField === 'date'">
                {{ table.sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th scope="col" @click="table.sortBy('paymentMethod')" class="sortable">
              Payment Method
              <span v-if="table.sortField === 'paymentMethod'">
                {{ table.sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th scope="col">Sale Type</th>
            <th scope="col" @click="table.sortBy('total')" class="sortable">
              Total
              <span v-if="table.sortField === 'total'">
                {{ table.sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th scope="col">Actions</th>
          </tr>
        </template>

        <template #body>
          <tr v-for="order in table.paginatedData" :key="order.id">
            <th scope="row">{{ order.id }}</th>
            <td>{{ order.itemCount }} items</td>
            <td>
              <span class="badge" :class="getStatusClass(order.status)">
                {{ order.status }}
              </span>
            </td>
            <td>{{ formatDate(order.date) }}</td>
            <td>{{ order.paymentMethod }}</td>
            <td>{{ order.saleType }}</td>
            <td class="text-end fw-bold">₱{{ order.total?.toFixed(2) || '0.00' }}</td>
            <td>
              <div class="d-flex gap-1">
                <button 
                  class="btn btn-sm btn-outline-primary action-btn action-btn-view" 
                  title="View Order"
                  @click="viewOrder(order.id)"
                >
                  <Eye :size="14" />
                </button>
              </div>
            </td>
          </tr>
        </template>
      </TableTemplate>
    </div>

    <!-- Order Details Modal -->
    <div class="modal fade" id="orderModal" tabindex="-1" role="dialog" aria-labelledby="orderModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="orderModalLabel">Order Details</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="selectedOrder">
              <div class="order-info">
                <div class="row">
                  <div class="col-md-6">
                    <p><strong>Order ID:</strong> {{ selectedOrder.id }}</p>
                    <p><strong>Date:</strong> {{ formatDate(selectedOrder.date) }}</p>
                    <p><strong>Payment Method:</strong> {{ selectedOrder.paymentMethod }}</p>
                  </div>
                  <div class="col-md-6">
                    <p><strong>Status:</strong> 
                      <span class="badge" :class="getStatusClass(selectedOrder.status)">
                        {{ selectedOrder.status }}
                      </span>
                    </p>
                    <p><strong>Sale Type:</strong> {{ selectedOrder.saleType }}</p>
                    <p><strong>Total:</strong> <span class="fw-bold">₱{{ selectedOrder.total?.toFixed(2) || '0.00' }}</span></p>
                  </div>
                </div>
              </div>

              <!-- Items Details Section -->
              <div v-if="selectedOrder.originalData?.items" class="items-section">
                <h6>Items Ordered</h6>
                <div class="items-grid">
                  <div 
                    v-for="item in selectedOrder.originalData.items" 
                    :key="item.product_id"
                    class="item-card"
                  >
                    <div class="item-name">{{ item.product_name }}</div>
                    <span class="badge bg-secondary">{{ item.quantity }}</span>
                  </div>
                </div>
                
                <!-- Items Summary -->
                <div class="items-summary">
                  <div class="d-flex justify-content-between">
                    <span>Total Items:</span>
                    <strong>{{ getTotalItems(selectedOrder.originalData.items) }}</strong>
                  </div>
                  <hr>
                  <div class="d-flex justify-content-between">
                    <span>Total Amount:</span>
                    <strong>₱{{ selectedOrder.total?.toFixed(2) || '0.00'}}</strong>
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
import { onMounted, ref } from 'vue'
import { useTable } from '@/composables/ui/useTable.js'
import historyAPIService from '@/services/apiHistory.js'
import TableTemplate from '@/components/common/TableTemplate.vue'

export default {
  name: 'History',
  components: {
    TableTemplate
  },
  setup() {
    // Initialize table
    const table = useTable({
      itemsPerPage: 8,
      sortable: true,
      filterable: true,
      selectable: false
    })

    const selectedOrder = ref(null)

    // Load data
    const fetchHistory = async () => {
      try {
        table.setLoading(true)
        table.clearError()

        const result = await historyAPIService.loadHistory({
          page: table.currentPage,
          pageSize: table.config.itemsPerPage
        })

        // Transform the raw transaction data
        const transformedTransactions = (result.transactions || []).map(transaction => ({
          id: transaction.id,
          itemCount: transaction.originalData?.items?.length || 0,
          status: transaction.status || 'Unknown',
          date: transaction.transaction_date || transaction.date,
          paymentMethod: transaction.paymentMethod || 'Unknown',
          saleType: transaction.saleType || 'In Store',
          total: parseFloat(transaction.total_amount || transaction.total || 0),
          originalData: transaction // Keep reference to original data for modal
        }))

        console.log('Transformed transactions:', transformedTransactions)
        
        table.setData(transformedTransactions)
        table.setTotalCount(result.totalCount || transformedTransactions.length)
        
      } catch (error) {
        console.error('Error loading history:', error)
        table.setError(error.message)
      } finally {
        table.setLoading(false)
      }
    }

    const refreshData = async () => {
      await fetchHistory()
    }

    const getStatusClass = (status) => {
      const classes = {
        'Completed': 'bg-success',
        'Pending': 'bg-warning text-dark',
        'Processing': 'bg-info',
        'Cancelled': 'bg-danger',
        'Refunded': 'bg-secondary'
      }
      return classes[status] || 'bg-light text-dark'
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const viewOrder = (orderId) => {
      selectedOrder.value = table.data.find(order => order.id === orderId)
      const modalElement = document.getElementById('orderModal')
      if (modalElement && window.bootstrap) {
        const modal = new bootstrap.Modal(modalElement)
        modal.show()
      }
    }

    const getTotalItems = (items) => {
    return items ? items.reduce((total, item) => total + (item.quantity || 0), 0) : 0
  }

    onMounted(async () => {
      await fetchHistory()
    })

    return {
      table,
      selectedOrder,
      fetchHistory,
      refreshData,
      getStatusClass,
      formatDate,
      viewOrder,
      getTotalItems
    }
  }
}
</script>

<!-- YOUR EXISTING STYLES - UNCHANGED -->
<style scoped>
.history-container {
  padding: 1.5rem;
  background-color: var(--surface-tertiary);
  min-height: 100vh;
}

.history-contents {
  background: var(--surface-primary);
  border-radius: 0.75rem;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem;
  border-bottom: 1px solid var(--border-secondary);
  flex-wrap: wrap;
  gap: 1rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  min-width: 250px;
}

.search-box svg {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
  z-index: 2;
}

.search-box input {
  padding-left: 2.5rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border-secondary);
  background: var(--surface-primary);
}

.form-select {
  min-width: 140px;
  border-radius: 0.5rem;
  border: 1px solid var(--border-secondary);
  background: var(--surface-primary);
}

/* States */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: var(--text-secondary);
}

.loading-state .spinner-border {
  margin-bottom: 1rem;
  color: var(--primary);
}

.error-state {
  padding: 2rem;
}

.no-data-state {
  padding: 4rem 2rem;
}

.empty-state {
  text-align: center;
  color: var(--text-secondary);
}

/* Sortable headers */
.sortable {
  cursor: pointer;
  user-select: none;
  position: relative;
  padding-right: 1.5rem !important;
  transition: background-color 0.2s ease;
}

.sortable:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.sortable span {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.75rem;
}

/* Items section in modal */
.items-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-secondary);
}

.items-section h6 {
  margin-bottom: 1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
  margin: 1rem 0;
}

.item-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--surface-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}

.item-card:hover {
  background: var(--state-hover);
  border-color: var(--primary);
}

.item-name {
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
  margin-right: 0.5rem;
}

.items-summary {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--surface-secondary);
  border-radius: 0.5rem;
  border-left: 4px solid var(--primary);
}

/* Responsive */
@media (max-width: 1024px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-controls {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .history-container {
    padding: 1rem;
  }
  
  .page-header {
    padding: 1.5rem;
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .header-controls {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .search-box {
    min-width: 100%;
  }
  
  .form-select {
    min-width: 100%;
  }
  
  .items-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .page-header {
    padding: 1rem;
  }
}
</style>