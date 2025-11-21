<template>
  <div class="shift-summary-page">
    <div class="summary-container">
      <div class="summary-header" v-if="shiftSummary">
        <h1 class="page-title">Shift Summary</h1>
        <p class="shift-id">{{ shiftSummary.shiftId }}</p>
        <p class="shift-date">{{ formatDate(shiftSummary.endTime) }}</p>
      </div>

      <div class="summary-content" v-if="shiftSummary">
      <!-- Shift Duration Card -->
      <div class="summary-card">
        <h2 class="card-title">Shift Duration</h2>
        <div class="duration-info">
          <div class="info-item">
            <span class="info-label">Started:</span>
            <span class="info-value">{{ formatDateTime(shiftSummary.startTime) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Ended:</span>
            <span class="info-value">{{ formatDateTime(shiftSummary.endTime) }}</span>
          </div>
          <div class="info-item highlight">
            <span class="info-label">Duration:</span>
            <span class="info-value highlight-value">{{ shiftSummary.duration }}</span>
          </div>
        </div>
      </div>

      <!-- Cash Drawer Card -->
      <div class="summary-card">
        <h2 class="card-title cash-title">Cash drawer</h2>
        <div class="cash-info">
          <div class="cash-row">
            <span class="cash-label">Starting cash:</span>
            <span class="cash-value">₱{{ formatCurrency(shiftSummary.openingCash) }}</span>
          </div>
          <div class="cash-row">
            <span class="cash-label">Cash payments:</span>
            <span class="cash-value">₱{{ formatCurrency(shiftSummary.cashSales) }}</span>
          </div>
          <div class="cash-row">
            <span class="cash-label">Cash refunds:</span>
            <span class="cash-value">₱0.00</span>
          </div>
          <div class="cash-row total-row">
            <span class="cash-label">Expected cash amount:</span>
            <span class="cash-value total-value">₱{{ formatCurrency(shiftSummary.expectedCash) }}</span>
          </div>
          <div class="cash-row" :class="{'variance-positive': shiftSummary.cashVariance > 0, 'variance-negative': shiftSummary.cashVariance < 0}">
            <span class="cash-label">Cash variance:</span>
            <span class="cash-value" :class="{'variance-positive-value': shiftSummary.cashVariance > 0, 'variance-negative-value': shiftSummary.cashVariance < 0}">
              {{ shiftSummary.cashVariance >= 0 ? '+' : '' }}₱{{ formatCurrency(Math.abs(shiftSummary.cashVariance)) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Sales Summary Card -->
      <div class="summary-card">
        <h2 class="card-title sales-title">Sales summary</h2>
        <div class="sales-info">
          <div class="sales-row">
            <span class="sales-label">Gross sales:</span>
            <span class="sales-value">₱{{ formatCurrency(shiftSummary.totalSales) }}</span>
          </div>
          <div class="sales-row">
            <span class="sales-label">Refunds:</span>
            <span class="sales-value">₱0.00</span>
          </div>
          <div class="sales-row">
            <span class="sales-label">Discounts:</span>
            <span class="sales-value">₱0.00</span>
          </div>
          <div class="sales-row">
            <span class="sales-label">Net sales:</span>
            <span class="sales-value">₱{{ formatCurrency(shiftSummary.totalSales) }}</span>
          </div>
          <div class="sales-row divider">
            <span class="sales-label">Cash:</span>
            <span class="sales-value">₱{{ formatCurrency(shiftSummary.cashSales) }}</span>
          </div>
          <div class="sales-row">
            <span class="sales-label">Online Banking:</span>
            <span class="sales-value">₱{{ formatCurrency((shiftSummary.paymentBreakdown?.['online_banking'] || 0)) }}</span>
          </div>
        </div>
      </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button @click="printSummary" class="btn-print">Print Summary</button>
          <button @click="completeLogout" class="btn-continue">Continue Logout</button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading shift summary...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="$router.push('/history')" class="btn-close">Go Back</button>
    </div>
  </div>
</template>

<script>
import apiService, { api } from '@/services/api.js'
import { formatDateTime12HourPH, formatDatePH } from '@/utils/dateTimeHelper.js'

export default {
  name: 'ShiftSummary',
  data() {
    return {
      shiftSummary: null,
      loading: true,
      error: null,
      shiftId: null
    }
  },
  async created() {
    // Get shift ID from route params or localStorage
    this.shiftId = this.$route.params.shiftId || localStorage.getItem('activeShiftId')
    
    if (!this.shiftId) {
      this.error = 'No shift ID provided'
      this.loading = false
      return
    }

    // Try to get summary from route state first (if coming from logout modal)
    if (this.$route.query.summary) {
      try {
        this.shiftSummary = JSON.parse(decodeURIComponent(this.$route.query.summary))
        this.loading = false
        return
      } catch (e) {
        // If parsing fails, continue to fetch from API
      }
    }

    // Otherwise fetch from API
    await this.fetchShiftSummary()
  },
  methods: {
    async fetchShiftSummary() {
      try {
        this.loading = true
        this.error = null
        
        // This endpoint should exist in your backend
        const response = await api.get(`/pos/sales/shift-summary/${this.shiftId}/`)
        const data = response.data

        if (data.success && data.data) {
          this.shiftSummary = this.processSummaryData(data.data)
        } else {
          throw new Error(data.error || 'Failed to load shift summary')
        }
      } catch (error) {
        this.error = error.response?.data?.error || error.message || 'Failed to load shift summary'
      } finally {
        this.loading = false
      }
    },

    processSummaryData(data) {
      const openingCash = data.opening_cash || 0
      const cashSales = data.cash_sales || data.total_sales || 0
      const expectedCash = data.expected_cash || (openingCash + cashSales)
      const cashVariance = data.cash_variance || 0
      
      const startTime = new Date(data.start_time)
      const endTime = new Date(data.end_time || new Date())
      const durationMs = endTime - startTime
      const hours = Math.floor(durationMs / (1000 * 60 * 60))
      const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60))

      return {
        shiftId: data._id || data.shift_id,
        startTime: data.start_time,
        endTime: data.end_time || new Date().toISOString(),
        duration: `${hours}h ${minutes}m`,
        totalSales: data.total_sales || 0,
        totalTransactions: data.total_transactions || 0,
        averageSale: data.total_transactions > 0 
          ? (data.total_sales || 0) / data.total_transactions 
          : 0,
        openingCash: openingCash,
        cashSales: cashSales,
        expectedCash: expectedCash,
        cashVariance: cashVariance,
        paymentBreakdown: data.payment_breakdown || {
          cash: cashSales,
          online_banking: 0
        }
      }
    },

    formatCurrency(value) {
      return parseFloat(value || 0).toFixed(2)
    },

    formatDateTime(dateString) {
      return formatDateTime12HourPH(dateString)
    },

    formatDate(dateString) {
      return formatDatePH(dateString)
    },

    printSummary() {
      window.print()
    },

    async completeLogout() {
      try {
        // Logout session without closing shift (already closed)
        await apiService.logoutSession()
        // Redirect to login
        this.$router.push('/login')
      } catch (error) {
        // Continue with logout even if API fails
        localStorage.removeItem('authToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('userData')
        localStorage.removeItem('activeShiftId')
        localStorage.removeItem('currentCartId')
        this.$router.push('/login')
      }
    }
  }
}
</script>

<style scoped>
.shift-summary-page {
  height: 100vh;
  background: #f8f8f8;
  padding: 0.75rem;
  overflow: hidden;
}

.summary-container {
  max-width: 900px;
  margin: 0 auto;
  background: #eeeeee;
  border-radius: 8px;
  padding: 1rem;
  height: calc(100vh - 1.5rem);
  display: flex;
  flex-direction: column;
}

.summary-header {
  text-align: center;
  margin-bottom: 0.5rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.15rem;
}

.shift-id {
  font-size: 0.9rem;
  color: #333;
  margin: 0.1rem 0;
}

.shift-date {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  overflow: hidden;
}

.summary-card {
  background: white;
  border-radius: 10px;
  padding: 0.6rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.4rem;
}

.cash-title {
  color: #4CAF50;
}

.sales-title {
  color: #4CAF50;
}

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

.cash-row.variance-positive .cash-value,
.variance-positive-value {
  color: #4caf50;
}

.cash-row.variance-negative .cash-value,
.variance-negative-value {
  color: #f44336;
}

.sales-row.divider {
  border-top: 1px solid #e0e0e0;
  padding-top: 0.4rem;
  margin-top: 0.25rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.btn-print,
.btn-continue,
.btn-close {
  padding: 0.6rem 1.5rem;
  border-radius: 4px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-print {
  background: #f5f5f5;
  color: #333;
}

.btn-print:hover {
  background: #e0e0e0;
}

.btn-continue {
  background: #9c27b0;
  color: white;
}

.btn-continue:hover {
  background: #7b1fa2;
}

.btn-close {
  background: #f44336;
  color: white;
}

.btn-close:hover {
  background: #d32f2f;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 3rem;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #7b1fa2;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media print {
  .action-buttons {
    display: none;
  }
  
  .shift-summary-page {
    box-shadow: none;
  }
  
  .summary-container {
    background: white;
  }
}
</style>

