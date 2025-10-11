<template>
  <div class="history-container">
    <div class="history-contents">
      <!-- Page Header -->
      <div class="page-header">
        <h2 class="page-title">Order History</h2>
        <div class="header-actions">
          <button 
            class="btn btn-refresh btn-sm" 
            @click="refreshData()"
            :disabled="loading"
          >
            <RefreshCw :size="16" :class="{ 'spinning': loading }" />
            Refresh
          </button>
          <button 
            class="btn btn-export btn-sm" 
            @click="exportData()"
            :disabled="loading || orders.length === 0"
          >
            <Download :size="16" />
            Export CSV
          </button>
        </div>
      </div>

      <!-- Filters Section -->
      <div class="filters-container">
        <div class="row g-3">
          <!-- Date Range -->
          <div class="col-md-3">
            <label class="form-label">From Date</label>
            <input 
              type="date" 
              class="form-control" 
              v-model="filters.dateFrom"
              @change="applyFilters"
            />
          </div>
          
          <div class="col-md-3">
            <label class="form-label">To Date</label>
            <input 
              type="date" 
              class="form-control" 
              v-model="filters.dateTo"
              @change="applyFilters"
            />
          </div>

          <!-- Status Filter -->
          <div class="col-md-2">
            <label class="form-label">Status</label>
            <select 
              class="form-select" 
              v-model="filters.status"
              @change="applyFilters"
            >
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="voided">Voided</option>
            </select>
          </div>

          <!-- Payment Method Filter -->
          <div class="col-md-2">
            <label class="form-label">Payment</label>
            <select 
              class="form-select" 
              v-model="filters.paymentMethod"
              @change="applyFilters"
            >
              <option value="">All Methods</option>
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="gcash">GCash</option>
              <option value="paymaya">PayMaya</option>
            </select>
          </div>

          <!-- Clear Filters -->
          <div class="col-md-2 d-flex align-items-end">
            <button 
              class="btn btn-cancel w-100" 
              @click="clearFilters"
              :disabled="!hasActiveFilters"
            >
              <X :size="16" />
              Clear
            </button>
          </div>
        </div>

        <!-- Search Bar -->
        <div class="row mt-3">
          <div class="col-md-6">
            <div class="search-box">
              <Search :size="18" class="search-icon" />
              <input 
                type="text" 
                class="form-control ps-5" 
                placeholder="Search by Sale ID..."
                v-model="filters.search"
                @input="debounceSearch"
              />
            </div>
          </div>
          <div class="col-md-6 text-end">
            <span class="text-muted">
              <strong>{{ totalOrders }}</strong> total transactions found
            </span>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading transactions...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <AlertCircle :size="48" class="text-danger mb-3" />
        <p class="text-danger fw-bold">{{ error }}</p>
        <button @click="refreshData()" class="btn btn-primary mt-2">
          Try Again
        </button>
      </div>

      <!-- No Data State -->
      <div v-else-if="orders.length === 0" class="no-data-state">
        <ShoppingBag :size="64" class="text-muted mb-3" />
        <h5 class="text-muted">No Transactions Found</h5>
        <p class="text-muted">
          {{ hasActiveFilters ? 'Try adjusting your filters' : 'No sales have been recorded yet' }}
        </p>
        <button 
          v-if="hasActiveFilters" 
          @click="clearFilters" 
          class="btn btn-secondary mt-2"
        >
          Clear Filters
        </button>
      </div>

      <!-- Table -->
      <div v-else class="table-container">
        <div class="table-responsive">
          <table class="history-table">
            <thead>
              <tr>
                <th scope="col">Sale ID</th>
                <th scope="col">Items</th>
                <th scope="col">Status</th>
                <th scope="col">Date & Time</th>
                <th scope="col">Payment</th>
                <th scope="col">Source</th>
                <th scope="col" class="text-end">Total</th>
                <th scope="col" class="text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id" class="table-row">
                <th scope="row" class="sale-id">{{ order.id }}</th>
                <td>
                  <span class="item-count-badge">
                    <Package :size="14" />
                    {{ order.itemCount }} items
                  </span>
                </td>
                <td>
                  <span class="status-badge" :class="getStatusClass(order.status)">
                    {{ order.status }}
                  </span>
                </td>
                <td class="date-cell">{{ formatDate(order.date) }}</td>
                <td>
                  <span class="payment-badge">
                    <CreditCard :size="14" v-if="order.paymentMethod.toLowerCase().includes('card')" />
                    <Wallet :size="14" v-else />
                    {{ order.paymentMethod }}
                  </span>
                </td>
                <td>
                  <span class="source-badge" :class="order.saleType === 'POS' ? 'source-pos' : 'source-manual'">
                    {{ order.saleType }}
                  </span>
                </td>
                <td class="total-amount">₱{{ formatCurrency(order.total) }}</td>
                <td>
                  <div class="action-buttons">
                    <button 
                      class="action-btn view-btn" 
                      title="View Details"
                      @click="viewOrder(order.id)"
                    >
                      <Eye :size="16" />
                    </button>
                    <button 
                      class="action-btn receipt-btn" 
                      title="View Receipt"
                      @click="viewReceipt(order.id)"
                      v-if="order.saleType === 'POS'"
                    >
                      <FileText :size="16" />
                    </button>
                    <button 
                      class="action-btn void-btn" 
                      title="Void Sale"
                      @click="initVoidSale(order)"
                      v-if="order.status === 'Completed' && order.saleType === 'POS'"
                    >
                      <ArchiveX :size="16" />
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
            <small class="text-muted">
              Showing <strong>{{ startItem }}</strong> - <strong>{{ endItem }}</strong> of <strong>{{ totalOrders }}</strong> transactions
            </small>
          </div>
          <div class="pagination-controls">
            <button 
              class="page-btn" 
              :disabled="currentPage === 1"
              @click="goToPage(currentPage - 1)"
              title="Previous Page"
            >
              <ChevronLeft :size="16" />
            </button>
            
            <button 
              v-for="page in visiblePages" 
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
              title="Next Page"
            >
              <ChevronRight :size="16" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Order Details Modal -->
    <div class="modal fade" id="orderModal" tabindex="-1" aria-labelledby="orderModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <h5 class="modal-title" id="orderModalLabel">Order Details</h5>
              <small class="text-muted" v-if="selectedOrder">{{ selectedOrder.id }}</small>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body surface-primary">
            <div v-if="selectedOrder">
              <!-- Order Information -->
              <div class="order-info-grid">
                <div class="info-card">
                  <div class="info-label">Status</div>
                  <span class="status-badge" :class="getStatusClass(selectedOrder.status)">
                    {{ selectedOrder.status }}
                  </span>
                </div>

                <div class="info-card">
                  <div class="info-label">Date & Time</div>
                  <div class="info-value">{{ formatDate(selectedOrder.date) }}</div>
                </div>

                <div class="info-card">
                  <div class="info-label">Payment Method</div>
                  <div class="info-value">
                    <CreditCard :size="16" v-if="selectedOrder.paymentMethod.toLowerCase().includes('card')" />
                    <Wallet :size="16" v-else />
                    {{ selectedOrder.paymentMethod }}
                  </div>
                </div>

                <div class="info-card">
                  <div class="info-label">Source</div>
                  <span class="source-badge" :class="selectedOrder.saleType === 'POS' ? 'source-pos' : 'source-manual'">
                    {{ selectedOrder.saleType }}
                  </span>
                </div>
              </div>

              <!-- Items Section -->
              <div v-if="selectedOrder.originalData?.items" class="items-section">
                <h6 class="section-title">
                  <Package :size="18" />
                  Items Ordered
                </h6>
                
                <div class="items-list">
                  <div 
                    v-for="item in selectedOrder.originalData.items" 
                    :key="item.product_id"
                    class="item-row"
                  >
                    <div class="item-info">
                      <div class="item-name">{{ item.product_name }}</div>
                      <div class="item-details">
                        {{ item.product_id }} • ₱{{ formatCurrency(item.unit_price) }} each
                      </div>
                    </div>
                    <div class="item-quantity">
                      <span class="qty-badge">×{{ item.quantity }}</span>
                    </div>
                    <div class="item-total">
                      ₱{{ formatCurrency(item.total_price) }}
                    </div>
                  </div>
                </div>

                <!-- Price Summary -->
                <div class="price-summary">
                  <div class="summary-row">
                    <span>Subtotal</span>
                    <strong>₱{{ formatCurrency(selectedOrder.originalData.subtotal || 0) }}</strong>
                  </div>
                  <div class="summary-row" v-if="selectedOrder.originalData.discount_amount > 0">
                    <span class="text-success">Discount</span>
                    <strong class="text-success">-₱{{ formatCurrency(selectedOrder.originalData.discount_amount) }}</strong>
                  </div>
                  <div class="summary-row" v-if="selectedOrder.originalData.tax_amount > 0">
                    <span>Tax (12%)</span>
                    <strong>₱{{ formatCurrency(selectedOrder.originalData.tax_amount) }}</strong>
                  </div>
                  <div class="summary-row total-row">
                    <span>Total Amount</span>
                    <strong class="total-value">₱{{ formatCurrency(selectedOrder.total) }}</strong>
                  </div>
                </div>
              </div>

              <!-- Additional Info -->
              <div class="additional-info" v-if="selectedOrder.originalData">
                <div class="info-row" v-if="selectedOrder.originalData.cashier_id">
                  <User :size="16" />
                  <span><strong>Cashier:</strong> {{ selectedOrder.originalData.cashier_id }}</span>
                </div>
                <div class="info-row" v-if="selectedOrder.originalData.customer_id">
                  <Users :size="16" />
                  <span><strong>Customer:</strong> {{ selectedOrder.originalData.customer_id }}</span>
                </div>
                <div class="info-row" v-if="selectedOrder.originalData.shift_id">
                  <Clock :size="16" />
                  <span><strong>Shift:</strong> {{ selectedOrder.originalData.shift_id }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button 
              type="button" 
              class="btn btn-secondary" 
              data-bs-dismiss="modal"
            >
              Close
            </button>
            <button 
              v-if="selectedOrder?.saleType === 'POS'" 
              type="button" 
              class="btn btn-primary"
              @click="viewReceipt(selectedOrder.id)"
            >
              <FileText :size="16" />
              View Receipt
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Void Sale Modal -->
    <div class="modal fade" id="voidModal" tabindex="-1" aria-labelledby="voidModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title text-danger" id="voidModalLabel">
              <AlertCircle :size="20" />
              Void Sale
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="voidingOrder">
              <p class="text-muted">
                Are you sure you want to void sale <strong>{{ voidingOrder.id }}</strong>?
              </p>
              
              <div class="mb-3">
                <label class="form-label">Manager ID <span class="text-danger">*</span></label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="voidForm.managerId"
                  placeholder="Enter manager ID"
                  required
                />
              </div>

              <div class="mb-3">
                <label class="form-label">Reason for Void <span class="text-danger">*</span></label>
                <textarea 
                  class="form-control" 
                  rows="3"
                  v-model="voidForm.reason"
                  placeholder="Enter reason for voiding this sale"
                  required
                ></textarea>
              </div>

              <div class="alert alert-warning" role="alert">
                <AlertCircle :size="16" />
                <strong>Warning:</strong> This action will restore inventory and cannot be undone.
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button 
              type="button" 
              class="btn btn-secondary" 
              data-bs-dismiss="modal"
              :disabled="voidLoading"
            >
              Cancel
            </button>
            <button 
              type="button" 
              class="btn btn-danger"
              @click="confirmVoidSale"
              :disabled="voidLoading || !voidForm.managerId || !voidForm.reason"
            >
              <span v-if="voidLoading" class="spinner-border spinner-border-sm me-2"></span>
              {{ voidLoading ? 'Processing...' : 'Void Sale' }}
            </button>
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
  data() {
    return {
      currentPage: 1,
      itemsPerPage: 20,
      orders: [],
      selectedOrder: null,
      loading: false,
      error: null,
      totalOrders: 0,
      totalPages: 0,
      searchTimeout: null,
      filters: {
        dateFrom: null,
        dateTo: null,
        status: null,
        paymentMethod: null,
        search: null
      },
      voidingOrder: null,
      voidForm: {
        managerId: '',
        reason: ''
      },
      voidLoading: false
    }
  },
  computed: {
    startItem() {
      return (this.currentPage - 1) * this.itemsPerPage + 1
    },
    endItem() {
      return Math.min(this.currentPage * this.itemsPerPage, this.totalOrders)
    },
    hasActiveFilters() {
      return Object.values(this.filters).some(value => value !== null && value !== '')
    },
    visiblePages() {
      const pages = []
      const maxVisible = 5
      let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2))
      let end = Math.min(this.totalPages, start + maxVisible - 1)
      
      if (end - start < maxVisible - 1) {
        start = Math.max(1, end - maxVisible + 1)
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
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

        console.log('Fetching history with params:', {
          page: this.currentPage,
          pageSize: this.itemsPerPage,
          ...this.filters
        })

        const result = await historyAPIService.loadHistory({
          page: this.currentPage,
          pageSize: this.itemsPerPage,
          ...this.filters
        })

        console.log('API Result:', result)

        this.orders = result.transactions || []
        this.totalOrders = result.totalCount || 0
        this.totalPages = result.totalPages || 1

        console.log('Orders loaded:', this.orders.length)

      } catch (error) {
        console.error('Error loading history:', error)
        this.error = error.message || 'Failed to load transaction history'
      } finally {
        loading.value = false
      }
    }

    async goToPage(page) {
      if (page >= 1 && page <= this.totalPages && page !== this.currentPage) {
        this.currentPage = page
        window.scrollTo({ top: 0, behavior: 'smooth' })
        await this.fetchHistory()
      }
    },

    async applyFilters() {
      this.currentPage = 1
      await this.fetchHistory()
    },

    debounceSearch() {
      clearTimeout(this.searchTimeout)
      this.searchTimeout = setTimeout(() => {
        this.applyFilters()
      }, 500)
    },

    async clearFilters() {
      this.filters = {
        dateFrom: null,
        dateTo: null,
        status: null,
        paymentMethod: null,
        search: null
      }
      this.currentPage = 1
      await this.fetchHistory()
    },

    getStatusClass(status) {
      const classes = {
        'Completed': 'status-completed',
        'Pending': 'status-pending',
        'Processing': 'status-processing',
        'Cancelled': 'status-cancelled',
        'Voided': 'status-cancelled',
        'Refunded': 'status-refunded'
      }
      return classes[status] || 'badge-inactive'
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    formatCurrency(value) {
      return parseFloat(value).toFixed(2)
    },

    async viewOrder(orderId) {
      try {
        this.selectedOrder = this.orders.find(order => order.id === orderId)
        
        // If we don't have full details, fetch them
        if (!this.selectedOrder.originalData?.items) {
          const fullDetails = await historyAPIService.getSaleDetails(orderId)
          this.selectedOrder = fullDetails
        }
        
        console.log('Selected order:', this.selectedOrder)
        
        const modalElement = document.getElementById('orderModal')
        if (modalElement && window.bootstrap) {
          const modal = new bootstrap.Modal(modalElement)
          modal.show()
        }
      } catch (error) {
        console.error('Error fetching order details:', error)
        this.error = 'Failed to load order details'
      }
    },

    async viewReceipt(saleId) {
      try {
        const receipt = await historyAPIService.getReceipt(saleId)
        console.log('Receipt data:', receipt)
        // TODO: Implement receipt viewer
        alert('Receipt viewer coming soon!')
      } catch (error) {
        console.error('Error fetching receipt:', error)
        this.error = 'Failed to load receipt'
      }
    },

    initVoidSale(order) {
      this.voidingOrder = order
      this.voidForm = {
        managerId: '',
        reason: ''
      }
      
      const modalElement = document.getElementById('voidModal')
      if (modalElement && window.bootstrap) {
        const modal = new bootstrap.Modal(modalElement)
        modal.show()
      }
    },

    async confirmVoidSale() {
      try {
        this.voidLoading = true
        
        await historyAPIService.voidSale(
          this.voidingOrder.id,
          this.voidForm.reason,
          this.voidForm.managerId
        )

        // Close modal
        const modalElement = document.getElementById('voidModal')
        const modal = bootstrap.Modal.getInstance(modalElement)
        if (modal) modal.hide()

        // Refresh data
        await this.fetchHistory()

        // Show success message
        alert('Sale voided successfully')
        
      } catch (error) {
        console.error('Error voiding sale:', error)
        this.error = error.message || 'Failed to void sale'
      } finally {
        this.voidLoading = false
      }
    },

    async refreshData() {
      await this.fetchHistory()
    },

    async exportData() {
      try {
        await historyAPIService.exportToCSV(this.filters)
      } catch (error) {
        console.error('Error exporting data:', error)
        this.error = 'Failed to export data'
      }
    }
  }
}
</script>

<style scoped>
.history-container {
  padding: 1.5rem;
  min-height: 100vh;
}

.history-contents {
  border-radius: 0.75rem;
  overflow: hidden;
  padding: 0 2rem 2rem 2rem; /* Add padding: top right bottom left */
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e2e8f0;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: #2d3748;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Filters Container */
.filters-container {
  background: #f8f9fa;
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid #e2e8f0;
}

.search-box {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #6b7280;
}

.search-box input {
  padding-left: 2.5rem;
}

/* Loading, Error, No Data States */
.loading-state,
.error-state,
.no-data-state {
  text-align: center;
  padding: 3rem 2rem;
  color: #6b7280;
}

.loading-state p,
.error-state p,
.no-data-state p {
  margin: 0;
}

/* Table Container */
.table-container {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-responsive {
  overflow-x: auto;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
}

.history-table thead {
  background: linear-gradient(135deg, #567cdc 0%, #7392e2 100%);
  color: white;
}

.history-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  border: none;
  white-space: nowrap;
}

.history-table td {
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.875rem;
  vertical-align: middle;
}

.history-table tbody tr:hover {
  background-color: #f7fafc;
}

.history-table tbody tr:last-child td {
  border-bottom: none;
}

/* Table Cells */
.sale-id {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #567cdc;
}

.item-count-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: #f3f4f6;
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.813rem;
  color: #4b5563;
}

.date-cell {
  color: #6b7280;
  white-space: nowrap;
}

.payment-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: #4b5563;
}

.source-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.source-pos {
  background-color: #dbeafe;
  color: #1e40af;
}

.source-manual {
  background-color: #fef3c7;
  color: #92400e;
}

/* Status Badges */
.status-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-completed {
  background-color: #d1fae5;
  color: #065f46;
}

.status-pending {
  background-color: #fef3c7;
  color: #92400e;
}

.status-processing {
  background-color: #dbeafe;
  color: #1e40af;
}

.status-cancelled {
  background-color: #fee2e2;
  color: #991b1b;
}

.status-refunded {
  background-color: #e5e7eb;
  color: #374151;
}

/* Total Amount */
.total-amount {
  font-weight: 700;
  color: #1f2937;
  text-align: right;
  font-size: 0.938rem;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 0.375rem;
  justify-content: center;
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  border: none;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-btn {
  color: #3b82f6;
  border: 1px solid #3b82f6;
}

.view-btn:hover {
  background-color: #3b82f6;
  color: white;
}

.receipt-btn {
  color: #8b5cf6;
  border: 1px solid #8b5cf6;
}

.receipt-btn:hover {
  background-color: #8b5cf6;
  color: white;
}

.void-btn {
  color: #ef4444;
  border: 1px solid #ef4444;
}

.void-btn:hover {
  background-color: #ef4444;
  color: white;
}

/* Pagination */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  background: #f9fafb;
}

.pagination-info {
  color: #6b7280;
  font-size: 0.875rem;
}

.pagination-controls {
  display: flex;
  gap: 0.375rem;
}

.page-btn {
  min-width: 36px;
  height: 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  padding: 0 0.5rem;
}

.page-btn:hover:not(:disabled) {
  background-color: #f3f4f6;
  border-color: #9ca3af;
}

.page-btn.active {
  background-color: #567cdc;
  border-color: #567cdc;
  color: white;
  font-weight: 600;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Modal Styles */
.modal-header {
  border-bottom: 2px solid #e2e8f0;
  padding: 1.25rem 1.5rem;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  border-top: 2px solid #e2e8f0;
  padding: 1rem 1.5rem;
}

/* Order Info Grid */
.order-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-card {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.info-label {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
  font-weight: 600;
  margin-bottom: 0.5rem;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 0.938rem;
  color: #1f2937;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

/* Items Section */
.items-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px solid #e5e7eb;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  color: #1f2937;
  font-weight: 600;
  font-size: 1rem;
}

.items-list {
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 0.75rem;
  margin-bottom: 1rem;
}

.item-row {
  display: flex;
  justify-content: space-between;
  padding: 0.875rem;
  background: white;
  border-radius: 0.375rem;
  margin-bottom: 0.5rem;
  border: 1px solid #e5e7eb;
}

.item-row:last-child {
  margin-bottom: 0;
}

.item-info {
  flex: 1;
}

.item-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.item-details {
  font-size: 0.813rem;
  color: #6b7280;
}

.item-quantity {
  margin: 0 1rem;
}

.qty-badge {
  background: #e0e7ff;
  color: #3730a3;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-weight: 600;
  font-size: 0.875rem;
}

.item-total {
  font-weight: 700;
  color: #1f2937;
  min-width: 100px;
  text-align: right;
}

/* Price Summary */
.price-summary {
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid #e5e7eb;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  color: #4b5563;
}

.summary-row:not(:last-child) {
  border-bottom: 1px solid #e5e7eb;
}

.total-row {
  margin-top: 0.5rem;
  padding-top: 0.75rem;
  border-top: 2px solid #d1d5db !important;
  font-size: 1.125rem;
}

.total-value {
  color: #567cdc;
  font-size: 1.25rem;
}

/* Additional Info */
.additional-info {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #eff6ff;
  border-radius: 0.5rem;
  border: 1px solid #bfdbfe;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: #1e40af;
}

.info-row:last-child {
  margin-bottom: 0;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .history-table {
    font-size: 0.813rem;
  }

  .history-table th,
  .history-table td {
    padding: 0.75rem 0.5rem;
  }
}

@media (max-width: 768px) {
  .history-container {
    padding: 1rem;
  }

  .history-contents {
    padding: 1rem;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions button {
    flex: 1;
  }

  .filters-container .row {
    row-gap: 1rem;
  }

  .pagination-container {
    flex-direction: column;
    gap: 1rem;
  }

  .order-info-grid {
    grid-template-columns: 1fr;
  }

  .item-row {
    flex-wrap: wrap;
  }

  .item-quantity {
    margin: 0.5rem 0 0 0;
    width: 100%;
  }

  .item-total {
    width: 100%;
    text-align: left;
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid #e5e7eb;
  }
}

@media (max-width: 576px) {
  .page-title {
    font-size: 1.5rem;
  }

  .table-responsive {
    overflow-x: scroll;
  }

  .history-table {
    min-width: 800px;
  }
}
</style>