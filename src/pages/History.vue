<template>
  <div class="history-container surface-secondary transition-theme">
    <div class="history-contents surface-primary border-theme shadow-md transition-theme">
      <!-- Page Header -->
      <div class="page-header border-bottom-theme">
        <h2 class="page-title text-primary">Transaction History</h2>
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
      <div class="filters-container surface-tertiary border-theme transition-theme">
        <div class="row g-3">
          <!-- Date Range -->
          <div class="col-md-3">
            <label class="form-label text-secondary">From Date</label>
            <input
              type="date"
              class="form-control input-theme"
              v-model="filters.dateFrom"
              @change="applyFilters"
            />
          </div>

          <div class="col-md-3">
            <label class="form-label text-secondary">To Date</label>
            <input
              type="date"
              class="form-control input-theme"
              v-model="filters.dateTo"
              :min="filters.dateFrom || undefined"
              @change="validateDateRange"
            />
          </div>

          <!-- Status Filter -->
         <div class="col-md-2">
            <label class="form-label text-secondary">Status</label>
            <select
              class="form-select input-theme"
              v-model="filters.status"
              @change="applyFilters"
            >
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="confirmed">Confirmed</option>
              <option value="on_the_way">On the Way</option>
              <option value="voided">Voided</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>


          <!-- Payment Method Filter -->
          <div class="col-md-2">
            <label class="form-label text-secondary">Payment</label>
            <select
              class="form-select input-theme"
              v-model="filters.paymentMethod"
              @change="applyFilters"
            >
              <option value="">All Methods</option>
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="gcash">GCash</option>
              <option value="paymaya">PayMaya</option>
              <option value="cod">Cash on Delivery</option>
              <option value="bank_transfer">Bank Transfer</option>
            </select>
          </div>
          <!-- Source Filter -->
          <div class="col-md-2">
            <label class="form-label text-secondary">Source</label>
            <select
              class="form-select input-theme"
              v-model="filters.source"
              @change="applyFilters"
            >
              <option value="">All Sources</option>
              <option value="POS">POS</option>
              <option value="Online">Online</option>
            </select>
          </div>
        </div>

        <!-- Search Bar -->
        <div class="row mt-3">
          <div class="col-md-6">
            <div class="search-box">
              <Search :size="18" class="search-icon text-tertiary" />
              <input
                type="text"
                class="form-control input-theme ps-5"
                placeholder="Search by Transaction ID..."
                v-model="filters.search"
                @input="debounceSearch"
              />
            </div>
          </div>
          <div class="col-md-6 d-flex align-items-center justify-content-end gap-3">
            <button
              class="btn btn-cancel"
              @click="clearFilters"
              :disabled="!hasActiveFilters"
            >
              <X :size="16" />
              Clear Filters
            </button>
            <span class="text-tertiary">
              <strong class="text-primary">{{ totalOrders }}</strong> total transactions
            </span>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state text-tertiary">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3 text-secondary">Loading transactions...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <AlertCircle :size="48" class="text-error mb-3" />
        <p class="text-error fw-bold">{{ error }}</p>
        <button @click="refreshData()" class="btn btn-primary mt-2">
          Try Again
        </button>
      </div>

      <!-- No Data State -->
      <div v-else-if="orders.length === 0" class="no-data-state">
        <ShoppingBag :size="64" class="text-tertiary mb-3" />
        <h5 class="text-secondary">No Transactions Found</h5>
        <p class="text-tertiary">
          {{ hasActiveFilters ? 'Try adjusting your filters' : 'No transactions have been recorded yet' }}
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
                <th scope="col">Transaction ID</th>
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
                  <span 
                    v-if="order.saleType === 'Online' && order.paymentStatus"
                    class="payment-status-badge"
                    :class="getPaymentStatusClass(order.paymentStatus)"
                  >
                    {{ order.paymentStatus }}
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
                  <span class="source-badge" :class="order.saleType === 'POS' ? 'source-pos' : 'source-online'">
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
                    <!---<button 
                      class="action-btn receipt-btn" 
                      title="View Receipt"
                      @click="viewReceipt(order.id)"
                      v-if="order.saleType === 'POS'"
                    >
                      <FileText :size="16" />
                    </button>-->
                    <button 
                      v-if="order.saleType === 'POS' && order.status === 'Completed'"
                      class="action-btn void-btn" 
                      title="Void Sale"
                      @click="initVoidSale(order)"
                    >
                      <ArchiveX :size="16" />
                    </button>
                    <button 
                      v-if="order.saleType === 'Online' && ['Pending', 'Confirmed', 'Processing'].includes(order.status)"
                      class="action-btn void-btn" 
                      title="Cancel Order"
                      @click="initCancelOrder(order)"
                    >
                      <X :size="16" />
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
            <small class="text-secondary">
              Showing <strong class="text-primary">{{ startItem }}</strong> - <strong class="text-primary">{{ endItem }}</strong> of <strong class="text-primary">{{ totalOrders }}</strong> transactions
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
              <h5 class="modal-title" id="orderModalLabel">
                {{ selectedOrder?.saleType === 'POS' ? 'Sale Details' : 'Order Details' }}
              </h5>
              <small class="text-tertiary" v-if="selectedOrder">{{ selectedOrder.id }}</small>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
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
                  <span class="source-badge" :class="selectedOrder.saleType === 'POS' ? 'source-pos' : 'source-online'">
                    {{ selectedOrder.saleType }}
                  </span>
                </div>

                <div class="info-card" v-if="selectedOrder.saleType === 'Online' && selectedOrder.paymentStatus">
                  <div class="info-label">Payment Status</div>
                  <span class="payment-status-badge" :class="getPaymentStatusClass(selectedOrder.paymentStatus)">
                    {{ selectedOrder.paymentStatus }}
                  </span>
                </div>

                <div class="info-card" v-if="selectedOrder.customer">
                  <div class="info-label">Customer</div>
                  <div class="info-value">
                    <Users :size="16" />
                    {{ selectedOrder.customer }}
                  </div>
                </div>
              </div>

              <!-- Delivery Address for Online Orders -->
              <div v-if="selectedOrder.saleType === 'Online' && selectedOrder.deliveryAddress" class="delivery-section">
                <h6 class="section-title">
                  <MapPin :size="18" />
                  Delivery Address
                </h6>
                <div class="delivery-address-card">
                  <p class="mb-1 text-primary"><strong>{{ selectedOrder.deliveryAddress.recipient_name }}</strong></p>
                  <p class="mb-1 text-secondary">{{ selectedOrder.deliveryAddress.phone }}</p>
                  <p class="mb-1 text-secondary">{{ selectedOrder.deliveryAddress.street }}, {{ selectedOrder.deliveryAddress.barangay }}</p>
                  <p class="mb-0 text-secondary">{{ selectedOrder.deliveryAddress.city }}, {{ selectedOrder.deliveryAddress.province }} {{ selectedOrder.deliveryAddress.postal_code }}</p>
                  <p class="text-tertiary small mb-0 mt-2" v-if="selectedOrder.deliveryAddress.notes">
                    Note: {{ selectedOrder.deliveryAddress.notes }}
                  </p>
                </div>
              </div>

              <!-- Items Section -->
              <div v-if="selectedOrder.originalData?.items" class="items-section">
                <h6 class="section-title">
                  <Package :size="18" />
                  Items {{ selectedOrder.saleType === 'POS' ? 'Sold' : 'Ordered' }}
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
                      ₱{{ formatCurrency(item.unit_price * item.quantity) }}
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
                  <div class="summary-row" v-if="selectedOrder.originalData.points_discount > 0">
                    <span class="text-success">Points Redeemed</span>
                    <strong class="text-success">-₱{{ formatCurrency(selectedOrder.originalData.points_discount) }}</strong>
                  </div>
                  <div class="summary-row" v-if="selectedOrder.originalData.tax_amount > 0">
                    <span>Tax (12%)</span>
                    <strong>₱{{ formatCurrency(selectedOrder.originalData.tax_amount) }}</strong>
                  </div>
                  <div class="summary-row" v-if="selectedOrder.originalData.delivery_fee > 0">
                    <span>Delivery Fee</span>
                    <strong>₱{{ formatCurrency(selectedOrder.originalData.delivery_fee) }}</strong>
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
                <div class="info-row" v-if="selectedOrder.originalData.shift_id">
                  <Clock :size="16" />
                  <span><strong>Shift:</strong> {{ selectedOrder.originalData.shift_id }}</span>
                </div>
                <div class="info-row" v-if="selectedOrder.originalData.loyalty_points_earned">
                  <Award :size="16" />
                  <span><strong>Points Earned:</strong> {{ selectedOrder.originalData.loyalty_points_earned }}</span>
                </div>
                <div class="info-row" v-if="selectedOrder.originalData.notes">
                  <FileText :size="16" />
                  <span><strong>Notes:</strong> {{ selectedOrder.originalData.notes }}</span>
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
           <!---<button 
              v-if="selectedOrder?.saleType === 'POS'" 
              type="button" 
              class="btn btn-primary"
              @click="viewReceipt(selectedOrder.id)"
            >
              <FileText :size="16" />
              View Receipt
            </button>--> 
          </div>
        </div>
      </div>
    </div>

    <!-- Void/Cancel Modal -->
    <div class="modal fade" id="voidModal" tabindex="-1" aria-labelledby="voidModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title text-danger" id="voidModalLabel">
              <AlertCircle :size="20" />
              {{ voidingOrder?.saleType === 'POS' ? 'Void Sale' : 'Cancel Order' }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="voidingOrder">
              <p class="text-secondary">
                Are you sure you want to {{ voidingOrder.saleType === 'POS' ? 'void sale' : 'cancel order' }}
                <strong class="text-primary">{{ voidingOrder.id }}</strong>?
              </p>
              
              <div class="mb-3">
                <label class="form-label">
                  {{ voidingOrder.saleType === 'POS' ? 'Manager Username or Email' : 'User ID' }} 
                  <span class="text-danger">*</span>
                </label>
                <input 
                  type="text" 
                  class="form-control input-theme" 
                  v-model="voidForm.managerId"
                  :placeholder="voidingOrder.saleType === 'POS' ? 'Enter manager username or email' : 'Enter your user ID'"
                  required
                />
              </div>

              <div class="mb-3">
                <label class="form-label">
                  Reason for {{ voidingOrder.saleType === 'POS' ? 'Void' : 'Cancellation' }}
                  <span class="text-danger">*</span>
                </label>
                <textarea 
                  class="form-control input-theme" 
                  rows="3"
                  v-model="voidForm.reason"
                  :placeholder="`Enter reason for ${voidingOrder.saleType === 'POS' ? 'voiding this sale' : 'cancelling this order'}`"
                  required
                ></textarea>
              </div>

              <div class="alert alert-warning" role="alert">
                <AlertCircle :size="16" />
                <strong>Warning:</strong> This action will restore inventory 
                {{ voidingOrder.saleType === 'Online' ? 'and refund points if applicable' : '' }}
                and cannot be undone.
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
              {{ voidLoading ? 'Processing...' : (voidingOrder?.saleType === 'POS' ? 'Void Sale' : 'Cancel Order') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import historyAPIService from '@/services/apiHistory.js';
import { formatDateTime12HourPH } from '@/utils/dateTimeHelper.js';

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
        status: '',
        paymentMethod: '',
        search: null,
        source: '' // NEW: Source filter
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
        this.loading = false
      }
    },

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

    validateDateRange() {
      if (this.filters.dateFrom && this.filters.dateTo) {
        if (this.filters.dateTo < this.filters.dateFrom) {
          alert('To Date cannot be before From Date. Please select a valid date range.')
          this.filters.dateTo = this.filters.dateFrom
          return
        }
      }
      this.applyFilters()
    },

    async clearFilters() {
      this.filters = {
        dateFrom: null,
        dateTo: null,
        status: '',
        paymentMethod: '',
        search: null,
        source: ''
      }
      this.currentPage = 1
      await this.fetchHistory()
    },

    getStatusClass(status) {
      const classes = {
        'Completed': 'status-completed',
        'Pending': 'status-pending',
        'Confirmed': 'status-confirmed',
        'Processing': 'status-processing',
        'On the Way': 'status-on-the-way',
        'Cancelled': 'status-cancelled',
        'Voided': 'status-cancelled',
        'Refunded': 'status-refunded'
      }
      return classes[status] || 'status-default'
    },

    getPaymentStatusClass(paymentStatus) {
      const classes = {
        'Paid': 'payment-paid',
        'Pending': 'payment-pending',
        'Failed': 'payment-failed',
        'Refunded': 'payment-refunded'
      }
      return classes[paymentStatus] || 'payment-pending'
    },

    formatDate(dateString) {
      return formatDateTime12HourPH(dateString)
    },

    formatCurrency(value) {
      // Handle null, undefined, or empty values
      if (value === null || value === undefined || value === '') {
        return '0.00';
      }
      
      // Convert to number and handle invalid cases
      const num = parseFloat(value);
      
      // Check if the conversion resulted in a valid number
      if (isNaN(num)) {
        console.warn('Invalid currency value:', value);
        return '0.00';
      }
      
      // Format to 2 decimal places
      return num.toFixed(2);
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

    initCancelOrder(order) {
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
        
        // Check if it's POS or Online
        if (this.voidingOrder.saleType === 'POS') {
          await historyAPIService.voidSale(
            this.voidingOrder.id,
            this.voidForm.reason,
            this.voidForm.managerId
          )
        } else if (this.voidingOrder.saleType === 'Online') {
          await historyAPIService.cancelOnlineOrder(
            this.voidingOrder.id,
            this.voidForm.reason,
            this.voidForm.managerId || 'USER-ADMIN'
          )
        }

        // Close modal
        const modalElement = document.getElementById('voidModal')
        const modal = bootstrap.Modal.getInstance(modalElement)
        if (modal) modal.hide()

        // Refresh data
        await this.fetchHistory()

        // Show success message
        const action = this.voidingOrder.saleType === 'POS' ? 'voided' : 'cancelled'
        alert(`Transaction ${action} successfully`)
        
      } catch (error) {
        console.error('Error voiding/cancelling:', error)
        this.error = error.message || 'Failed to process request'
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
  overflow-y: auto;
}

.history-contents {
  border-radius: 0.75rem;
  padding: 2rem;
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 600;
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

/* Button Styles */
.btn-refresh,
.btn-export,
.btn-cancel {
  background-color: var(--button-bg);
  border: 1px solid var(--button-border);
  color: var(--button-text);
  transition: all 0.2s ease;
}

.btn-refresh:hover:not(:disabled),
.btn-export:hover:not(:disabled),
.btn-cancel:hover:not(:disabled) {
  background-color: var(--state-hover);
  border-color: var(--border-accent);
}

.btn-refresh:disabled,
.btn-export:disabled,
.btn-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: var(--surface-tertiary);
  color: var(--text-disabled);
  border-color: var(--border-secondary);
}

/* Filters Container */
.filters-container {
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.search-box {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
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
}

.loading-state p,
.error-state p,
.no-data-state p {
  margin: 0;
}

/* Table Container */
.table-container {
  background: var(--surface-primary);
  border-radius: 0.75rem;
  box-shadow: var(--shadow-md);
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
  background: linear-gradient(135deg, var(--primary-medium) 0%, var(--primary) 100%);
  color: var(--text-inverse);
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
  border-bottom: 1px solid var(--border-secondary);
  font-size: 0.875rem;
  vertical-align: middle;
}

.history-table tbody tr:hover {
  background-color: var(--state-hover);
}

.history-table tbody tr:last-child td {
  border-bottom: none;
}

/* Table Cells */
.sale-id {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: var(--primary);
}

.item-count-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: var(--surface-tertiary);
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.813rem;
  color: var(--text-secondary);
}

.date-cell {
  color: var(--text-tertiary);
  white-space: nowrap;
}

.payment-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--text-secondary);
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
  background-color: var(--surface-tertiary);
  color: var(--primary);
  border: 1px solid var(--border-accent);
}

.source-online {
  background-color: var(--surface-tertiary);
  color: var(--success);
  border: 1px solid var(--success);
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
  background-color: var(--status-success-bg);
  color: var(--status-success);
  border: 1px solid var(--status-success);
}

.status-pending {
  background-color: var(--status-warning-bg);
  color: var(--status-warning);
  border: 1px solid var(--status-warning);
}

.status-confirmed {
  background-color: var(--status-info-bg);
  color: var(--status-info);
  border: 1px solid var(--status-info);
}

.status-processing {
  background-color: var(--status-info-bg);
  color: var(--status-info);
  border: 1px solid var(--status-info);
}

.status-on-the-way {
  background-color: var(--surface-tertiary);
  color: var(--secondary);
  border: 1px solid var(--secondary);
}

.status-cancelled {
  background-color: var(--status-error-bg);
  color: var(--status-error);
  border: 1px solid var(--status-error);
}

.status-refunded {
  background-color: var(--surface-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-secondary);
}

/* Payment Status Badges */
.payment-status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.688rem;
  font-weight: 600;
  margin-left: 0.5rem;
}

.payment-paid {
  background-color: var(--status-success-bg);
  color: var(--status-success);
  border: 1px solid var(--status-success);
}

.payment-pending {
  background-color: var(--status-warning-bg);
  color: var(--status-warning);
  border: 1px solid var(--status-warning);
}

.payment-failed {
  background-color: var(--status-error-bg);
  color: var(--status-error);
  border: 1px solid var(--status-error);
}

.payment-refunded {
  background-color: var(--surface-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-secondary);
}

/* Total Amount */
.total-amount {
  font-weight: 700;
  color: var(--text-primary);
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
  background: var(--surface-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-btn {
  color: var(--primary);
  border: 1px solid var(--primary);
}

.view-btn:hover {
  background-color: var(--primary);
  color: var(--text-inverse);
}

.receipt-btn {
  color: var(--secondary);
  border: 1px solid var(--secondary);
}

.receipt-btn:hover {
  background-color: var(--secondary);
  color: var(--text-inverse);
}

.void-btn {
  color: var(--error);
  border: 1px solid var(--error);
}

.void-btn:hover {
  background-color: var(--error);
  color: var(--text-inverse);
}

/* Pagination */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-top: 1px solid var(--border-secondary);
  background: var(--surface-tertiary);
}

.pagination-info {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.pagination-info strong {
  color: var(--text-primary);
}

.pagination-controls {
  display: flex;
  gap: 0.375rem;
}

.page-btn {
  min-width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-primary);
  background: var(--surface-primary);
  color: var(--text-primary);
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  padding: 0 0.5rem;
}

.page-btn:hover:not(:disabled) {
  background-color: var(--state-hover);
  border-color: var(--border-accent);
}

.page-btn.active {
  background-color: var(--primary);
  border-color: var(--primary);
  color: var(--text-inverse);
  font-weight: 600;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Modal Styles */
.modal-content {
  background-color: var(--surface-primary);
  border: 1px solid var(--border-primary);
  color: var(--text-primary);
}

.modal-header {
  border-bottom: 2px solid var(--border-secondary);
  padding: 1.25rem 1.5rem;
  background-color: var(--surface-secondary);
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
  background-color: var(--surface-primary);
}

.modal-footer {
  border-top: 2px solid var(--border-secondary);
  padding: 1rem 1.5rem;
  background-color: var(--surface-secondary);
}

/* Modal form controls */
.modal-body .form-control,
.modal-body .form-select,
.modal-body textarea {
  background-color: var(--input-bg);
  border: 1px solid var(--input-border);
  color: var(--input-text);
}

.modal-body .form-control::placeholder,
.modal-body textarea::placeholder {
  color: var(--input-placeholder);
}

.modal-body .form-control:focus,
.modal-body .form-select:focus,
.modal-body textarea:focus {
  border-color: var(--border-accent);
  background-color: var(--input-bg);
  color: var(--input-text);
}

.modal-body .form-label {
  color: var(--text-secondary);
}

.modal-body .text-muted {
  color: var(--text-tertiary) !important;
}

.modal-body small {
  color: var(--text-tertiary);
}

/* Order Info Grid */
.order-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-card {
  background: var(--surface-tertiary);
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border-secondary);
}

.info-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  font-weight: 600;
  margin-bottom: 0.5rem;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 0.938rem;
  color: var(--text-primary);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

/* Delivery Section */
.delivery-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px solid var(--border-secondary);
}

.delivery-address-card {
  background: var(--surface-tertiary);
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid var(--border-secondary);
}

/* Items Section */
.items-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px solid var(--border-secondary);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 1rem;
}

.items-list {
  background: var(--surface-tertiary);
  border-radius: 0.5rem;
  padding: 0.75rem;
  margin-bottom: 1rem;
}

.item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem;
  background: var(--surface-primary);
  border-radius: 0.375rem;
  margin-bottom: 0.5rem;
  border: 1px solid var(--border-secondary);
}

.item-row:last-child {
  margin-bottom: 0;
}

.item-info {
  flex: 1;
}

.item-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.item-details {
  font-size: 0.813rem;
  color: var(--text-tertiary);
}

.item-quantity {
  margin: 0 1rem;
}

.qty-badge {
  background: var(--surface-tertiary);
  color: var(--primary);
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-weight: 600;
  font-size: 0.875rem;
  border: 1px solid var(--border-accent);
}

.item-total {
  font-weight: 700;
  color: var(--text-primary);
  min-width: 100px;
  text-align: right;
}

/* Price Summary */
.price-summary {
  background: var(--surface-tertiary);
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid var(--border-secondary);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  color: var(--text-secondary);
}

.summary-row:not(:last-child) {
  border-bottom: 1px solid var(--border-secondary);
}

.total-row {
  margin-top: 0.5rem;
  padding-top: 0.75rem;
  border-top: 2px solid var(--border-primary) !important;
  font-size: 1.125rem;
}

.total-value {
  color: var(--primary);
  font-size: 1.25rem;
}

/* Additional Info */
.additional-info {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--surface-tertiary);
  border-radius: 0.5rem;
  border: 1px solid var(--border-secondary);
}

.info-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
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
    border-top: 1px solid var(--border-secondary);
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