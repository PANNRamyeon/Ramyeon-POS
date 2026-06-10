<template>
  <div class="shift-page">
    <div class="shift-header">
      <h1 class="page-title">Shift Management</h1>
    </div>

    <!-- Content Grid -->
    <div class="content-grid">
      <!-- Left Column -->
      <div class="left-column">
        <!-- Shift Status -->
        <div class="shift-status-card" :class="{ 'shift-open': isShiftOpen, 'shift-closed': !isShiftOpen }">
          <div class="status-indicator">
            <div class="status-dot"></div>
            <span class="status-text">{{ isShiftOpen ? 'Shift Open' : 'No Active Shift' }}</span>
          </div>
          <div v-if="isShiftOpen && activeShiftId" class="shift-id-display">
            ID: {{ activeShiftId }}
          </div>
        </div>

        <!-- Open Shift Section -->
        <div v-if="!isShiftOpen" class="action-card">
          <h2 class="section-title">Open Shift</h2>
          <p class="section-description">Start your cashier shift by entering the starting cash amount in the drawer.</p>
          
          <div class="form-group">
            <label for="openingCash" class="form-label">Starting Cash:</label>
            <div class="input-with-currency">
              <span class="currency-symbol">₱</span>
              <input 
                id="openingCash"
                v-model.number="openingCash" 
                type="number" 
                step="0.01"
                min="0"
                class="form-input" 
                placeholder="Enter starting cash amount"
                @keyup.enter="handleOpenShift"
              />
            </div>
            <small class="helper-text">Count all cash in the drawer</small>
          </div>

          <button 
            @click="handleOpenShift" 
            class="btn-primary"
            :disabled="isLoading || !openingCash || openingCash < 0"
          >
            <span v-if="!isLoading">Start Shift</span>
            <span v-else>
              <span class="spinner-small"></span> Opening...
            </span>
          </button>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>
        </div>

        <!-- Close Shift Section -->
        <div v-else class="action-card">
          <h2 class="section-title">Close Shift</h2>
          <p class="section-description">End your current shift by entering the closing cash amount.</p>
          
          <div class="form-group">
            <label for="closingCash" class="form-label">Closing Cash:</label>
            <div class="input-with-currency">
              <span class="currency-symbol">₱</span>
              <input 
                id="closingCash"
                v-model.number="closingCash" 
                type="number" 
                step="0.01"
                min="0"
                class="form-input" 
                placeholder="Enter closing cash amount"
                @keyup.enter="handleCloseShift"
              />
            </div>
            <small class="helper-text">Count all cash currently in the drawer</small>
          </div>

          <button 
            @click="handleCloseShift" 
            class="btn-primary"
            :disabled="isLoading || !closingCash || closingCash < 0"
          >
            <span v-if="!isLoading">Close Shift</span>
            <span v-else>
              <span class="spinner-small"></span> Closing...
            </span>
          </button>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>
        </div>
      </div>

      <!-- Right Column -->
      <div class="right-column">
        <!-- Real-time Shift Summary -->
        <div v-if="isShiftOpen" class="summary-card">
          <h2 class="section-title">Current Shift Summary</h2>
          
          <div v-if="!realtimeSummary" class="loading-state">
            <div class="spinner"></div>
            <p>Loading shift summary...</p>
          </div>

          <div v-else class="summary-content">
            <!-- Shift Duration -->
            <div class="duration-info">
              <div class="info-item">
                <span class="info-label">Started:</span>
                <span class="info-value">{{ formatDateTime(realtimeSummary.startTime) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Duration:</span>
                <span class="info-value highlight-value">{{ realtimeSummary.duration }}</span>
              </div>
            </div>

            <!-- Cash Drawer -->
            <div class="cash-info">
              <div class="cash-row">
                <span class="cash-label">Starting cash:</span>
                <span class="cash-value">₱{{ formatCurrency(realtimeSummary.openingCash) }}</span>
              </div>
              <div class="cash-row">
                <span class="cash-label">Cash payments:</span>
                <span class="cash-value">₱{{ formatCurrency(realtimeSummary.cashSales) }}</span>
              </div>
              <div class="cash-row">
                <span class="cash-label">Cash refunds:</span>
                <span class="cash-value">₱0.00</span>
              </div>
              <div class="cash-row total-row">
                <span class="cash-label">Expected cash amount:</span>
                <span class="cash-value total-value">₱{{ formatCurrency(realtimeSummary.expectedCash) }}</span>
              </div>
            </div>

            <!-- Sales Summary -->
            <div class="sales-info">
              <div class="sales-row">
                <span class="sales-label">Gross sales:</span>
                <span class="sales-value">₱{{ formatCurrency(realtimeSummary.grossSales) }}</span>
              </div>
              <div class="sales-row">
                <span class="sales-label">Refunds:</span>
                <span class="sales-value">₱0.00</span>
              </div>
              <div class="sales-row">
                <span class="sales-label">Discounts:</span>
                <span class="sales-value">₱{{ formatCurrency(realtimeSummary.discounts) }}</span>
              </div>
              <div class="sales-row">
                <span class="sales-label">Net sales:</span>
                <span class="sales-value">₱{{ formatCurrency(realtimeSummary.netSales) }}</span>
              </div>
              <div class="sales-row divider">
                <span class="sales-label">Cash:</span>
                <span class="sales-value">₱{{ formatCurrency(realtimeSummary.cashSales) }}</span>
              </div>
              <div class="sales-row">
                <span class="sales-label">Online Banking:</span>
                <span class="sales-value">₱{{ formatCurrency((realtimeSummary.paymentBreakdown?.['online_banking'] || 0)) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Last Closed Shift Summary -->
        <div v-if="!isShiftOpen && lastClosedShift" class="summary-card">
          <h2 class="section-title">Last Shift Summary</h2>
          
          <div v-if="!lastClosedShift" class="loading-state">
            <div class="spinner"></div>
            <p>Loading shift summary...</p>
          </div>

          <div v-else class="summary-content">
            <!-- Shift Duration -->
            <div class="duration-info">
              <div class="info-item">
                <span class="info-label">Started:</span>
                <span class="info-value">{{ formatDateTime(lastClosedShift.startTime) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Duration:</span>
                <span class="info-value highlight-value">{{ lastClosedShift.duration }}</span>
              </div>
            </div>

            <!-- Cash Drawer -->
            <div class="cash-info">
              <div class="cash-row">
                <span class="cash-label">Starting cash:</span>
                <span class="cash-value">₱{{ formatCurrency(lastClosedShift.openingCash) }}</span>
              </div>
              <div class="cash-row">
                <span class="cash-label">Cash payments:</span>
                <span class="cash-value">₱{{ formatCurrency(lastClosedShift.cashSales) }}</span>
              </div>
              <div class="cash-row">
                <span class="cash-label">Cash refunds:</span>
                <span class="cash-value">₱0.00</span>
              </div>
              <div class="cash-row total-row">
                <span class="cash-label">Expected cash amount:</span>
                <span class="cash-value total-value">₱{{ formatCurrency(lastClosedShift.expectedCash) }}</span>
              </div>
              <div class="cash-row" :class="{'variance-positive': lastClosedShift.cashVariance > 0, 'variance-negative': lastClosedShift.cashVariance < 0}">
                <span class="cash-label">Cash variance:</span>
                <span class="cash-value" :class="{'variance-positive-value': lastClosedShift.cashVariance > 0, 'variance-negative-value': lastClosedShift.cashVariance < 0}">
                  {{ lastClosedShift.cashVariance >= 0 ? '+' : '' }}₱{{ formatCurrency(Math.abs(lastClosedShift.cashVariance)) }}
                </span>
              </div>
            </div>

            <!-- Sales Summary -->
            <div class="sales-info">
              <div class="sales-row">
                <span class="sales-label">Gross sales:</span>
                <span class="sales-value">₱{{ formatCurrency(lastClosedShift.grossSales) }}</span>
              </div>
              <div class="sales-row">
                <span class="sales-label">Refunds:</span>
                <span class="sales-value">₱0.00</span>
              </div>
              <div class="sales-row">
                <span class="sales-label">Discounts:</span>
                <span class="sales-value">₱{{ formatCurrency(lastClosedShift.discounts) }}</span>
              </div>
              <div class="sales-row">
                <span class="sales-label">Net sales:</span>
                <span class="sales-value">₱{{ formatCurrency(lastClosedShift.netSales) }}</span>
              </div>
              <div class="sales-row divider">
                <span class="sales-label">Cash:</span>
                <span class="sales-value">₱{{ formatCurrency(lastClosedShift.cashSales) }}</span>
              </div>
              <div class="sales-row">
                <span class="sales-label">Online Banking:</span>
                <span class="sales-value">₱{{ formatCurrency((lastClosedShift.paymentBreakdown?.['online_banking'] || 0)) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiService, { api } from '@/services/api.js'
import { formatDateTimeShortPH } from '@/utils/dateTimeHelper.js'

export default {
  name: 'Shift',
  data() {
    return {
      isShiftOpen: false,
      activeShiftId: null,
      openingCash: 0,
      closingCash: 0,
      isLoading: false,
      error: null,
      realtimeSummary: null,
      lastClosedShift: null,
      refreshInterval: null
    }
  },
  async mounted() {
    await this.checkShiftStatus()
    if (this.isShiftOpen) {
      await this.loadRealtimeSummary()
      this.startAutoRefresh()
    }
  },
  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  },
  methods: {
    async checkShiftStatus() {
      try {
        const userData = JSON.parse(localStorage.getItem('userData') || '{}')
        const userId = userData.user_id || userData.id || userData._id
        
        const response = await apiService.getActiveShift(userId)
        
        if (response && response.shift) {
          this.isShiftOpen = true
          this.activeShiftId = response.shift._id
          localStorage.setItem('activeShiftId', this.activeShiftId)
        } else {
          this.isShiftOpen = false
          this.activeShiftId = null
          localStorage.removeItem('activeShiftId')
        }
      } catch (error) {
        this.isShiftOpen = false
      }
    },

    async handleOpenShift() {
      if (!this.openingCash || this.openingCash < 0) {
        this.error = 'Please enter a valid opening cash amount'
        return
      }

      this.isLoading = true
      this.error = null

      try {
        const userData = JSON.parse(localStorage.getItem('userData') || '{}')
        const userId = userData.user_id || userData.id || userData._id

        const response = await apiService.startShift(userId, this.openingCash)
        
        if (response && response.shift) {
          this.isShiftOpen = true
          this.activeShiftId = response.shift._id
          localStorage.setItem('activeShiftId', this.activeShiftId)
          this.openingCash = 0
          this.error = null
          
          await this.loadRealtimeSummary()
          this.startAutoRefresh()
        } else {
          this.error = 'Failed to open shift. Please try again.'
        }
      } catch (error) {
        this.error = error.message || 'Failed to open shift. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async handleCloseShift() {
      if (!this.closingCash || this.closingCash < 0) {
        this.error = 'Please enter a valid closing cash amount'
        return
      }

      this.isLoading = true
      this.error = null

      try {
        const response = await apiService.closeShift(this.activeShiftId, this.closingCash)
        
        if (response && response.shift) {
          const closedShiftId = response.shift._id
          
          this.isShiftOpen = false
          this.activeShiftId = null
          localStorage.removeItem('activeShiftId')
          this.closingCash = 0
          this.realtimeSummary = null
          this.error = null
          
          if (this.refreshInterval) {
            clearInterval(this.refreshInterval)
            this.refreshInterval = null
          }
          
          // Load full summary for the closed shift
          await this.loadLastClosedShiftSummary(closedShiftId)
        } else {
          this.error = 'Failed to close shift. Please try again.'
        }
      } catch (error) {
        this.error = error.message || 'Failed to close shift. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async loadRealtimeSummary() {
      if (!this.activeShiftId) return

      try {
        const response = await api.get(`/pos/sales/shift-summary/${this.activeShiftId}/`)
        const data = response.data

        if (data.success && data.data) {
          const summaryData = data.data
          const openingCash = summaryData.opening_cash || 0
          const cashSales = summaryData.cash_sales || summaryData.total_sales || 0
          const expectedCash = openingCash + cashSales
          
          const startTime = new Date(summaryData.start_time)
          const now = new Date()
          const durationMs = now - startTime
          const hours = Math.floor(durationMs / (1000 * 60 * 60))
          const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60))
          
          this.realtimeSummary = {
            startTime: summaryData.start_time,
            duration: `${hours}h ${minutes}m`,
            totalSales: summaryData.total_sales || 0,
            totalTransactions: summaryData.total_transactions || 0,
            openingCash: openingCash,
            cashSales: cashSales,
            expectedCash: expectedCash,
            paymentBreakdown: summaryData.payment_breakdown || {},
            grossSales: summaryData.total_sales || 0,
            discounts: 0,
            netSales: summaryData.total_sales || 0
          }
        }
      } catch (error) {
        // Error loading realtime summary
      }
    },

    async loadLastClosedShiftSummary(shiftId) {
      try {
        const response = await api.get(`/pos/sales/shift-summary/${shiftId}/`)
        const data = response.data

        if (data.success && data.data) {
          const summaryData = data.data
          const openingCash = summaryData.opening_cash || 0
          const cashSales = summaryData.cash_sales || summaryData.total_sales || 0
          const expectedCash = summaryData.expected_cash || (openingCash + cashSales)
          const cashVariance = summaryData.cash_variance || 0
          
          const startTime = new Date(summaryData.start_time)
          const endTime = summaryData.end_time ? new Date(summaryData.end_time) : new Date()
          const durationMs = endTime - startTime
          const hours = Math.floor(durationMs / (1000 * 60 * 60))
          const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60))
          
          this.lastClosedShift = {
            shiftId: shiftId,
            startTime: summaryData.start_time,
            endTime: summaryData.end_time,
            duration: `${hours}h ${minutes}m`,
            totalSales: summaryData.total_revenue || summaryData.total_sales || 0,
            totalTransactions: summaryData.total_transactions || 0,
            openingCash: openingCash,
            cashSales: cashSales,
            expectedCash: expectedCash,
            cashVariance: cashVariance,
            paymentBreakdown: summaryData.payment_breakdown || {},
            grossSales: summaryData.total_revenue || summaryData.total_sales || 0,
            discounts: 0,
            netSales: summaryData.total_revenue || summaryData.total_sales || 0
          }
        }
      } catch (error) {
        // Error loading closed shift summary
      }
    },

    startAutoRefresh() {
      // Refresh every 30 seconds
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
      }
      this.refreshInterval = setInterval(() => {
        if (this.isShiftOpen) {
          this.loadRealtimeSummary()
        }
      }, 30000)
    },

    formatCurrency(amount) {
      return parseFloat(amount || 0).toFixed(2)
    },

    formatDateTime(dateString) {
      return formatDateTimeShortPH(dateString)
    }
  }
}
</script>

<style scoped>
.shift-page {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.shift-header {
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: bold;
  color: #333;
  margin: 0;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.shift-status-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.shift-open .status-dot {
  background: #4caf50;
}

.shift-closed .status-dot {
  background: #9e9e9e;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.shift-id-display {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #666;
}

.action-card,
.summary-card,
.view-summary-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  margin: 0 0 0.5rem 0;
}

.section-description {
  color: #666;
  margin: 0 0 1.5rem 0;
  line-height: 1.5;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.input-with-currency {
  display: flex;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.3s;
}

.input-with-currency:focus-within {
  border-color: #7392E2;
}

.currency-symbol {
  padding: 0.75rem 1rem;
  background: #f5f5f5;
  font-weight: 600;
  color: #333;
}

.form-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 0.75rem 1rem;
  font-size: 1rem;
}

.helper-text {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #666;
}

.btn-primary,
.btn-secondary {
  width: 100%;
  padding: 0.875rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: #ffebee;
  border-left: 4px solid #f44336;
  color: #c62828;
  border-radius: 4px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  color: #666;
}

.spinner,
.spinner-small {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner {
  width: 40px;
  height: 40px;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.item-label {
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
}

.item-value {
  font-size: 1.75rem;
  font-weight: bold;
  color: #333;
}

.item-value.highlight {
  color: #667eea;
}

/* Shift Summary Rows */
.duration-info,
.cash-info,
.sales-info {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.info-item,
.cash-row,
.sales-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
}

.info-item.highlight {
  background: #e0f2f7;
  padding: 0.4rem;
  border-radius: 8px;
  margin-top: 0.25rem;
}

.highlight-value {
  color: #333;
  font-weight: 500;
}

.info-label,
.cash-label,
.sales-label {
  color: #333;
  font-size: 0.95rem;
}

.info-value,
.cash-value,
.sales-value {
  color: #333;
  font-weight: 400;
  text-align: right;
}

.cash-row.total-row {
  border-top: 1px solid #e0e0e0;
  padding-top: 0.4rem;
  margin-top: 0.25rem;
}

.cash-row.total-row .cash-label,
.cash-row.total-row .cash-value {
  font-weight: 600;
}

.sales-row.divider {
  border-top: 1px solid #e0e0e0;
  padding-top: 0.4rem;
  margin-top: 0.25rem;
}

.cash-row.variance-positive .cash-value,
.variance-positive-value {
  color: #4caf50;
}

.cash-row.variance-negative .cash-value,
.variance-negative-value {
  color: #f44336;
}

.card-title {
  font-size: 1.25rem;
  font-weight: bold;
  color: #333;
  margin: 0 0 1rem 0;
}

.shift-info {
  margin-bottom: 1rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #eee;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row span {
  color: #666;
}

.info-row strong {
  color: #333;
  font-weight: 600;
}

@media (max-width: 768px) {
  .shift-page {
    padding: 1rem;
  }
  
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
