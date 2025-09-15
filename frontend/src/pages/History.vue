<template>
  <div class="history-container">
    <div class="history-contents">
      <div class="page-header">
        <h2 class="page-title">Order History</h2>
        
        <div class="header-controls">
          <div class="search-box">
            <Search :size="16" />
            <input
              type="text"
              v-model="searchQuery"
              @input="handleSearch"
              placeholder="Search orders..."
              class="form-control"
            />
          </div>

          <select class="form-select" v-model="statusFilter" @change="handleFilter">
            <option value="">All Status</option>
            <option value="Completed">Completed</option>
            <option value="Pending">Pending</option>
            <option value="Processing">Processing</option>
            <option value="Cancelled">Cancelled</option>
            <option value="Refunded">Refunded</option>
          </select>

          <select class="form-select" v-model="paymentFilter" @change="handleFilter">
            <option value="">All Payment Methods</option>
            <option value="Cash">Cash</option>
            <option value="Card">Card</option>
            <option value="GCash">GCash</option>
          </select>

          <button class="btn btn-outline-secondary" @click="refreshData">
            <RefreshCw :size="16" />
            Refresh
          </button>
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="loading-state">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p>Loading transactions...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <div class="alert alert-danger">
          <strong>Error:</strong> {{ error }}
          <button @click="refreshData()" class="btn btn-sm btn-outline-danger ms-2">
            Retry
          </button>
        </div>
      </div>

      <!-- No data state -->
      <div v-else-if="filteredOrders.length === 0" class="no-data-state">
        <div class="empty-state">
          <ShoppingBag :size="48" class="text-muted mb-3" />
          <h5>No transactions found</h5>
          <p class="text-muted">Try adjusting your search or filters</p>
        </div>
      </div>

      <!-- Data Table using TableTemplate -->
      <TableTemplate
        v-else
        :current-page="currentPage"
        :items-per-page="itemsPerPage"
        :total-items="sortedOrders.length"
        :show-pagination="false"
      >
        <template #header>
          <tr>
            <th scope="col" @click="sortBy('id')" class="sortable">
              ID
              <span v-if="sortField === 'id'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th scope="col">Items</th>
            <th scope="col" @click="sortBy('status')" class="sortable">
              Status
              <span v-if="sortField === 'status'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th scope="col" @click="sortBy('date')" class="sortable">
              Date
              <span v-if="sortField === 'date'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th scope="col" @click="sortBy('paymentMethod')" class="sortable">
              Payment Method
              <span v-if="sortField === 'paymentMethod'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th scope="col">Sale Type</th>
            <th scope="col" @click="sortBy('total')" class="sortable">
              Total
              <span v-if="sortField === 'total'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th scope="col">Actions</th>
          </tr>
        </template>

        <template #body>
          <tr v-for="order in currentPageOrders" :key="order.id">
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

      <!-- Custom Pagination using PaginationControls -->
      <PaginationControls
        v-if="paginationInfo.totalPages > 1"
        :current-page="paginationInfo.currentPage"
        :total-pages="paginationInfo.totalPages"
        :start="paginationInfo.start"
        :end="paginationInfo.end"
        :total="paginationInfo.total"
        :visible-pages="paginationControls.pages"
        :has-next="paginationControls.hasNext"
        :has-previous="paginationControls.hasPrevious"
        :next-page="paginationControls.nextPage"
        :previous-page="paginationControls.previousPage"
        item-name="orders"
        @page-changed="goToPage"
      />
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
import { ref, computed, onMounted } from 'vue'
import { tablePagination } from '@/helpers/pagination.js'
import historyAPIService from '@/services/apiHistory.js'
import TableTemplate from '@/components/common/TableTemplate.vue'
import PaginationControls from '@/components/common/PaginationControls.vue'

export default {
  name: 'History',
  components: {
    TableTemplate,
    PaginationControls
  },
  setup() {
    // State
    const orders = ref([])
    const loading = ref(false)
    const error = ref(null)
    const selectedOrder = ref(null)
    const currentPage = ref(1)
    const itemsPerPage = ref(8)
    
    // Filters
    const searchQuery = ref('')
    const statusFilter = ref('')
    const paymentFilter = ref('')
    
    // Sorting
    const sortField = ref('')
    const sortDirection = ref('asc')

    // Computed: Apply filters and sorting
    const filteredOrders = computed(() => {
      let result = orders.value

      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(order => 
          order.id.toLowerCase().includes(query) ||
          order.status.toLowerCase().includes(query) ||
          order.paymentMethod.toLowerCase().includes(query)
        )
      }

      if (statusFilter.value) {
        result = result.filter(order => order.status === statusFilter.value)
      }

      if (paymentFilter.value) {
        result = result.filter(order => order.paymentMethod === paymentFilter.value)
      }

      return result
    })

    const sortedOrders = computed(() => {
      if (!sortField.value) return filteredOrders.value

      return [...filteredOrders.value].sort((a, b) => {
        const aValue = a[sortField.value]
        const bValue = b[sortField.value]

        let comparison = 0
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          comparison = aValue - bValue
        } else {
          comparison = String(aValue).localeCompare(String(bValue))
        }

        return sortDirection.value === 'desc' ? -comparison : comparison
      })
    })

    // Pagination using helper
    const currentPageOrders = computed(() => {
      return tablePagination.getPaginatedItems(
        sortedOrders.value, 
        currentPage.value, 
        itemsPerPage.value
      )
    })

    const paginationInfo = computed(() => {
      return tablePagination.getPaginationInfo(
        currentPage.value,
        sortedOrders.value.length,
        itemsPerPage.value
      )
    })

    const paginationControls = computed(() => {
      return tablePagination.getPaginationControls(
        currentPage.value,
        paginationInfo.value.totalPages
      )
    })

    // Methods
    const fetchHistory = async () => {
      try {
        loading.value = true
        error.value = null

        const result = await historyAPIService.loadHistory({
          page: 1,
          pageSize: 1000
        })

        orders.value = result.transactions || []
        
      } catch (err) {
        error.value = err.message
      } finally {
        loading.value = false
      }
    }

    const goToPage = (page) => {
      const normalizedPage = tablePagination.normalizePage(page, paginationInfo.value.totalPages)
      if (normalizedPage !== currentPage.value) {
        currentPage.value = normalizedPage
      }
    }

    const handleSearch = () => {
      currentPage.value = 1
    }

    const handleFilter = () => {
      currentPage.value = 1
    }

    const sortBy = (field) => {
      if (sortField.value === field) {
        sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
      } else {
        sortField.value = field
        sortDirection.value = 'asc'
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
      selectedOrder.value = orders.value.find(order => order.id === orderId)
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
      // State
      orders,
      loading,
      error,
      selectedOrder,
      currentPage,
      itemsPerPage,
      searchQuery,
      statusFilter,
      paymentFilter,
      sortField,
      sortDirection,
      
      // Computed
      filteredOrders,
      sortedOrders,
      currentPageOrders,
      paginationInfo,
      paginationControls,
      
      // Methods
      fetchHistory,
      goToPage,
      handleSearch,
      handleFilter,
      sortBy,
      refreshData,
      getStatusClass,
      formatDate,
      viewOrder,
      getTotalItems
    }
  }
}
</script>

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