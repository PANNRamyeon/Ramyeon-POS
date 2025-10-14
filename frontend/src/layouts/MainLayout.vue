<template>
  <div class="app-layout">
    <!-- Sidebar Component -->
    <Sidebar 
      @menu-changed="handleMenuChange"
      @logout="handleLogout"
    />
    
    <!-- Main Content Area -->
    <main class="main-content">
      <!-- Header Bar -->
      <header class="content-header">
        <div class="header-content">
          <!-- Left Side - Date/Time and Page Title -->
          <div class="header-left">
            <div class="datetime-display">
              {{ currentDateTime }}
            </div>
          </div>
        </div>
      </header>
      
      <!-- Page Content - This will now show the routed component -->
      <div class="page-content">
        <router-view />
      </div>
    </main>

    <!-- ✅ Logout Modal with TWO screens -->
    <div v-if="showLogoutModal" class="modal-overlay" @click="closeLogoutModal">
      <div class="modal-content" @click.stop>
        
        <!-- ✅ SCREEN 1: Enter Closing Cash (v-if="!showSummary") -->
        <div v-if="!showSummary">
          <div class="modal-header">
            <h3>End Shift & Logout</h3>
            <button class="close-btn" @click="closeLogoutModal" :disabled="logoutLoading">
              ×
            </button>
          </div>
          
          <div class="modal-body">
            <p class="text-muted mb-3">Please enter the closing cash amount for your shift.</p>
            
            <div class="shift-info" v-if="shiftInfo">
              <div class="info-row">
                <span>Shift ID:</span>
                <strong>{{ shiftInfo.shiftId }}</strong>
              </div>
              <div class="info-row">
                <span>Opening Cash:</span>
                <strong>₱{{ formatCurrency(shiftInfo.openingCash) }}</strong>
              </div>
              <div class="info-row">
                <span>Started:</span>
                <strong>{{ formatTime(shiftInfo.startTime) }}</strong>
              </div>
              <div class="info-row" v-if="shiftInfo.transactionCount > 0">
                <span>Transactions:</span>
                <strong>{{ shiftInfo.transactionCount }}</strong>
              </div>
              <div class="info-row" v-if="shiftInfo.totalSales > 0">
                <span>Total Sales:</span>
                <strong class="text-success">₱{{ formatCurrency(shiftInfo.totalSales) }}</strong>
              </div>
            </div>
            
            <div class="form-group">
              <label for="closingCash" class="form-label">Closing Cash Amount:</label>
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
                  :disabled="logoutLoading || processingLogout"
                  required
                  @keyup.enter="confirmLogout"
                />
              </div>
              <small class="helper-text">Count all cash in the drawer and enter the total amount</small>
            </div>
            
            <div v-if="logoutError" class="error-message mb-3">
              {{ logoutError }}
            </div>
          </div>
          
          <div class="modal-footer">
            <button 
              @click="closeLogoutModal" 
              class="btn-cancel"
              :disabled="logoutLoading || processingLogout"
            >
              Cancel
            </button>
            <button 
              @click="confirmLogout" 
              class="btn-confirm"
              :disabled="logoutLoading || processingLogout || !closingCash"
            >
              <span v-if="!logoutLoading && !processingLogout">Continue</span>
              <span v-else>
                <span class="spinner-small"></span> Processing...
              </span>
            </button>
          </div>
        </div>

        <!-- ✅ SCREEN 2: Show Summary (v-else) -->
        <div v-else>
          <div class="modal-header summary-header">
            <div>
              <h3>Shift Summary</h3>
              <p class="summary-subtitle" v-if="shiftSummary">{{ shiftSummary.shiftId }}</p>
            </div>
          </div>
          
          <div class="modal-body" v-if="shiftSummary">
            <!-- Shift Duration -->
            <div class="summary-section">
              <h4 class="section-title">
                <svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="currentColor">
                  <path d="m612-292 56-56-148-148v-184h-80v216l172 172ZM480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-400Zm0 320q133 0 226.5-93.5T800-480q0-133-93.5-226.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160Z"/>
                </svg>
                Shift Duration
              </h4>
              <div class="summary-grid">
                <div class="summary-card">
                  <div class="card-label">Started</div>
                  <div class="card-value">{{ formatTime(shiftSummary.startTime) }}</div>
                </div>
                <div class="summary-card">
                  <div class="card-label">Ended</div>
                  <div class="card-value">{{ formatTime(shiftSummary.endTime) }}</div>
                </div>
                <div class="summary-card highlight-card">
                  <div class="card-label">Duration</div>
                  <div class="card-value">{{ shiftSummary.duration }}</div>
                </div>
              </div>
            </div>

            <!-- Sales Performance -->
            <div class="summary-section">
              <h4 class="section-title">
                <svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="currentColor">
                  <path d="M280-280h80v-200h-80v200Zm160 0h80v-400h-80v400Zm160 0h80v-120h-80v120ZM200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"/>
                </svg>
                Sales Performance
              </h4>
              <div class="summary-grid">
                <div class="summary-card stat-card">
                  <div class="card-label">Total Sales</div>
                  <div class="card-value large">₱{{ formatCurrency(shiftSummary.totalSales) }}</div>
                </div>
                <div class="summary-card stat-card">
                  <div class="card-label">Transactions</div>
                  <div class="card-value large">{{ shiftSummary.totalTransactions }}</div>
                </div>
                <div class="summary-card stat-card">
                  <div class="card-label">Average Sale</div>
                  <div class="card-value">₱{{ formatCurrency(shiftSummary.averageSale) }}</div>
                </div>
              </div>
            </div>

            <!-- Cash Reconciliation -->
            <div class="summary-section">
              <h4 class="section-title">
                <svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="currentColor">
                  <path d="M540-80q-108 0-184-76t-76-184v-23q-86-14-143-80.5T80-600v-240h120v-40h80v160h-80v-40h-40v160q0 66 47 113t113 47q66 0 113-47t47-113v-160h-40v40h-80v-160h80v40h120v240q0 90-57 156.5T360-363v23q0 75 52.5 127.5T540-160q75 0 127.5-52.5T720-340v-67q-35-12-57.5-43T640-520q0-50 35-85t85-35q50 0 85 35t35 85q0 39-22.5 70T800-407v67q0 108-76 184T540-80Zm220-480q17 0 28.5-11.5T800-600q0-17-11.5-28.5T760-640q-17 0-28.5 11.5T720-600q0 17 11.5 28.5T760-560Z"/>
                </svg>
                Cash Reconciliation
              </h4>
              <div class="reconciliation-table">
                <div class="recon-row">
                  <span>Opening Cash</span>
                  <strong>₱{{ formatCurrency(shiftSummary.openingCash) }}</strong>
                </div>
                <div class="recon-row">
                  <span>Cash Sales</span>
                  <strong>₱{{ formatCurrency(shiftSummary.cashSales) }}</strong>
                </div>
                <div class="recon-row divider">
                  <span>Expected Cash</span>
                  <strong>₱{{ formatCurrency(shiftSummary.expectedCash) }}</strong>
                </div>
                <div class="recon-row highlight">
                  <span>Actual Closing Cash</span>
                  <strong>₱{{ formatCurrency(shiftSummary.closingCash) }}</strong>
                </div>
                <div class="recon-row" :class="varianceClass">
                  <span>Variance</span>
                  <strong>{{ variancePrefix }}₱{{ formatCurrency(Math.abs(shiftSummary.variance)) }}</strong>
                </div>
              </div>
            </div>

            <!-- Payment Breakdown -->
            <div class="summary-section" v-if="shiftSummary.paymentBreakdown">
              <h4 class="section-title">
                <svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="currentColor">
                  <path d="M560-440q-50 0-85-35t-35-85q0-50 35-85t85-35q50 0 85 35t35 85q0 50-35 85t-85 35ZM280-320q-33 0-56.5-23.5T200-400v-320q0-33 23.5-56.5T280-800h560q33 0 56.5 23.5T920-720v320q0 33-23.5 56.5T840-320H280Zm80-80h400q0-33 23.5-56.5T840-480v-160q-33 0-56.5-23.5T760-720H360q0 33-23.5 56.5T280-640v160q33 0 56.5 23.5T360-400Zm440 240H120q-33 0-56.5-23.5T40-240v-440h80v440h680v80ZM280-400v-320 320Z"/>
                </svg>
                Payment Methods
              </h4>
              <div class="payment-grid">
                <div class="payment-item" v-for="(amount, method) in shiftSummary.paymentBreakdown" :key="method">
                  <span class="payment-method">{{ formatPaymentMethod(method) }}</span>
                  <span class="payment-amount">₱{{ formatCurrency(amount) }}</span>
                </div>
              </div>
            </div>

            <!-- Variance Alert -->
            <div v-if="Math.abs(shiftSummary.variance) > 0" class="alert" :class="varianceAlertClass">
              <svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="currentColor">
                <path d="m40-120 440-760 440 760H40Zm138-80h604L480-720 178-200Zm302-40q17 0 28.5-11.5T520-280q0-17-11.5-28.5T480-320q-17 0-28.5 11.5T440-280q0 17 11.5 28.5T480-240Zm-40-120h80v-200h-80v200Zm40-100Z"/>
              </svg>
              <div>
                <strong>{{ Math.abs(shiftSummary.variance) > 10 ? 'Significant ' : '' }}Cash Variance Detected</strong>
                <p>{{ varianceMessage }}</p>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button 
              @click="finalizeLogout" 
              class="btn-confirm full-width"
              :disabled="logoutLoading"
            >
              <span v-if="!logoutLoading">Complete & Logout</span>
              <span v-else>
                <span class="spinner-small"></span> Logging out...
              </span>
            </button>
          </div>
        </div>
        
      </div>
    </div>
  </div>
</template>

<script>
import Sidebar from './Sidebar.vue'
import apiService from '../services/api.js'

export default {
  name: 'MainLayout',
  components: {
    Sidebar
  },
  data() {
    return {
      currentTime: new Date(),
      timeInterval: null,
      
      // Logout modal state
      showLogoutModal: false,
      showSummary: false,
      closingCash: 0,
      logoutLoading: false,
      logoutError: null,
      shiftInfo: null,
      shiftSummary: null,
      processingLogout: false
    }
  },
  
  computed: {
    currentPageTitle() {
      const titles = {
        '/dashboard': 'Dashboard',
        '/online-order': 'Online Order',
        '/new-order': 'New Order',
        '/history': 'History',
        '/settings': 'Settings',
      }
      return titles[this.$route.path] || 'Page'
    },
    
    currentDateTime() {
      const now = this.currentTime
      
      try {
        const options = {
          day: 'numeric',
          month: 'long', 
          year: 'numeric',
          weekday: 'long'
        }
        
        const dateStr = now.toLocaleDateString('en-US', options)
        const timeStr = now.toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: false
        })
        
        const parts = dateStr.split(', ')
        const weekday = parts[0]
        const monthDay = parts[1]
        const year = parts[2]
        
        return `${monthDay} ${year} ${weekday} | ${timeStr}`
      } catch (error) {
        console.error('Date formatting error:', error)
        return now.toString()
      }
    },

    varianceClass() {
      if (!this.shiftSummary) return ''
      const variance = this.shiftSummary.variance
      if (variance > 0) return 'variance-over'
      if (variance < 0) return 'variance-short'
      return 'variance-exact'
    },

    variancePrefix() {
      if (!this.shiftSummary) return ''
      return this.shiftSummary.variance > 0 ? '+' : ''
    },

    varianceAlertClass() {
      if (!this.shiftSummary) return ''
      const variance = Math.abs(this.shiftSummary.variance)
      if (variance > 10) return 'alert-danger'
      if (variance > 0) return 'alert-warning'
      return 'alert-success'
    },

    varianceMessage() {
      if (!this.shiftSummary) return ''
      const variance = this.shiftSummary.variance
      if (variance > 0) {
        return `You have ₱${this.formatCurrency(variance)} more than expected. Please verify your count.`
      } else if (variance < 0) {
        return `You are short ₱${this.formatCurrency(Math.abs(variance))}. Please recount or report the shortage.`
      }
      return 'Cash count matches expected amount perfectly!'
    }
  },
  
  methods: {
    handleMenuChange(menu) {
      console.log('Menu changed to:', menu)
      this.$router.push(`/${menu}`)
    },
    
    async handleLogout() {
      console.log('📤 Logout initiated')
      
      try {
        const userData = JSON.parse(localStorage.getItem('userData') || '{}')
        const userRole = userData.role?.toLowerCase()
        const activeShiftId = localStorage.getItem('activeShiftId')
        
        console.log('👤 User role:', userRole)
        console.log('⏰ Active shift:', activeShiftId)
        
        if ((userRole === 'cashier' || userRole === 'employee') && activeShiftId) {
          await this.loadShiftInfo(activeShiftId)
          this.closingCash = this.shiftInfo?.openingCash || 0
          this.showLogoutModal = true
          return
        }
        
        await this.performLogout(0)
        
      } catch (error) {
        console.error('❌ Logout initialization failed:', error)
        this.showLogoutModal = true
      }
    },
    
    async loadShiftInfo(shiftId) {
      try {
        const userData = JSON.parse(localStorage.getItem('userData') || '{}')
        const userId = userData.user_id || userData.id || userData._id
        
        const response = await apiService.getActiveShift(userId)
        
        if (response && response.shift) {
          try {
            const salesData = await apiService.getShiftSales(shiftId)
            
            let sales = []
            if (salesData.data?.sales) {
              sales = salesData.data.sales
            } else if (salesData.sales) {
              sales = salesData.sales
            } else if (Array.isArray(salesData)) {
              sales = salesData
            }
            
            const totalSales = sales.reduce((sum, sale) => sum + (sale.total_amount || 0), 0)
            
            this.shiftInfo = {
              shiftId: response.shift._id,
              openingCash: response.shift.opening_cash || 0,
              startTime: response.shift.start_time,
              transactionCount: sales.length,
              totalSales: totalSales
            }
            
            console.log('✅ Shift info loaded:', this.shiftInfo)
            
          } catch (salesError) {
            console.warn('⚠️ Could not load shift sales:', salesError)
            
            this.shiftInfo = {
              shiftId: response.shift._id,
              openingCash: response.shift.opening_cash || 0,
              startTime: response.shift.start_time,
              transactionCount: 0,
              totalSales: 0
            }
          }
        }
      } catch (error) {
        console.error('⚠️ Failed to load shift info:', error)
        this.shiftInfo = {
          shiftId: shiftId,
          openingCash: 0,
          startTime: null,
          transactionCount: 0,
          totalSales: 0
        }
      }
    },
    
    async confirmLogout() {
      // Prevent double-click
      if (this.processingLogout || this.logoutLoading) {
        console.log('⚠️ Already processing, ignoring duplicate call')
        return
      }
      
      if (this.closingCash < 0) {
        this.logoutError = 'Closing cash cannot be negative'
        return
      }
      
      this.logoutError = null
      this.logoutLoading = true
      this.processingLogout = true
      
      try {
        console.log('💰 Closing shift with cash:', this.closingCash)
        
        const response = await apiService.closeShift(
          this.shiftInfo.shiftId,
          this.closingCash
        )
        
        console.log('✅ Shift closed successfully')
        
        const shiftData = response.shift || response.data || response
        this.shiftSummary = this.calculateShiftSummary(shiftData)
        this.showSummary = true
        
        // Clear activeShiftId immediately after successful close
        localStorage.removeItem('activeShiftId')
        
      } catch (error) {
        console.error('❌ Failed to close shift:', error)
        
        // Handle "already closed" error gracefully
        if (error.message?.includes('already closed')) {
          console.log('⚠️ Shift already closed, clearing localStorage')
          localStorage.removeItem('activeShiftId')
          
          // Allow logout to continue anyway
          this.showSummary = false
          await this.performLogout(0)
        } else {
          this.logoutError = error.message || 'Failed to close shift. Please try again.'
        }
      } finally {
        this.logoutLoading = false
        this.processingLogout = false
      }
    },

    calculateShiftSummary(shiftData) {
      console.log('🧮 Calculating shift summary from:', shiftData)
      
      const openingCash = shiftData.opening_cash || 0
      const closingCash = shiftData.closing_cash || this.closingCash
      const totalSales = shiftData.total_sales || 0
      const cashSales = shiftData.cash_sales || totalSales
      
      const expectedCash = openingCash + cashSales
      const variance = closingCash - expectedCash
      
      const startTime = new Date(shiftData.start_time)
      const endTime = new Date(shiftData.end_time || new Date())
      const durationMs = endTime - startTime
      const hours = Math.floor(durationMs / (1000 * 60 * 60))
      const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60))
      
      const summary = {
        shiftId: shiftData._id,
        startTime: shiftData.start_time,
        endTime: shiftData.end_time || new Date().toISOString(),
        duration: `${hours}h ${minutes}m`,
        totalSales: totalSales,
        totalTransactions: shiftData.total_transactions || 0,
        averageSale: shiftData.total_transactions > 0 
          ? totalSales / shiftData.total_transactions 
          : 0,
        openingCash: openingCash,
        cashSales: cashSales,
        expectedCash: expectedCash,
        closingCash: closingCash,
        variance: variance,
        paymentBreakdown: shiftData.payment_breakdown || {
          cash: cashSales
        }
      }
      
      console.log('✅ Summary calculated:', summary)
      
      return summary
    },

    async finalizeLogout() {
      this.logoutLoading = true
      
      try {
        console.log('🎯 Finalizing logout...')
        await this.performLogout(0)
      } catch (error) {
        console.error('❌ Finalize logout failed:', error)
      } finally {
        this.logoutLoading = false
      }
    },

    async performLogout(closingCash = 0) {
      try {
        console.log('🚪 Performing logout')
        
        // Call auth logout endpoint (shift already closed)
        try {
          await apiService.logout(0)
          console.log('✅ Logout API successful')
        } catch (error) {
          console.error('⚠️ Logout API error:', error)
          // Continue with logout even if API fails
        }
        
      } catch (error) {
        console.error('⚠️ Logout error:', error)
      } finally {
        // Clear all stored data
        localStorage.removeItem('authToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('userData')
        localStorage.removeItem('activeShiftId')
        localStorage.removeItem('currentCartId')
        
        console.log('🧹 Cleared localStorage')
        
        // Close modal
        this.showLogoutModal = false
        this.showSummary = false
        
        // Redirect to login
        this.$router.push('/login')
        
        console.log('✅ Logout complete')
      }
    },
    
    closeLogoutModal() {
      if (!this.logoutLoading && !this.processingLogout) {
        this.showLogoutModal = false
        this.showSummary = false
        this.closingCash = 0
        this.logoutError = null
        this.shiftInfo = null
        this.shiftSummary = null
        this.processingLogout = false
      }
    },
    
    formatCurrency(amount) {
      return parseFloat(amount || 0).toFixed(2)
    },
    
    formatTime(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    },

    formatPaymentMethod(method) {
      const methods = {
        cash: 'Cash',
        card: 'Card',
        gcash: 'GCash',
        paymaya: 'PayMaya',
        qrph: 'QR PH'
      }
      return methods[method] || method
    },
    
    updateTime() {
      this.currentTime = new Date()
    }
  },
  
  mounted() {
    this.timeInterval = setInterval(this.updateTime, 1000)
  },
  
  beforeUnmount() {
    if (this.timeInterval) {
      clearInterval(this.timeInterval)
    }
  },
  
  beforeRouteEnter(to, from, next) {
    const token = localStorage.getItem('authToken')
    if (token) {
      next()
    } else {
      next('/login')
    }
  }
}
</script>


<style scoped>
/* Keep all your existing styles... */

.app-layout {
  min-height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 0;
}

.main-content {
  margin-left: 180px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-width: 0;
}

.content-header {
  position: sticky;
  top: 0;
  z-index: 999;
  background: white;
  height: 100px;
  padding: 0 2.5rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.datetime-display {
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.025em;
  line-height: 1.2;
}

.content-header h1 {
  font-size: 1.875rem;
  font-weight: 600;
  margin: 0;
}

.page-content {
  flex: 1;
  padding: 2.5rem;
  overflow-y: visible;
  overflow-x: hidden;
  width: 100%;
  min-width: 0;
  background-color: #f8f9fa;
}

/* ✅ NEW: Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: fadeIn 0.2s ease;
}

.modal-content {
  background: white;
  border-radius: 1rem;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: slideUp 0.3s ease;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.close-btn:hover:not(:disabled) {
  background: #f8f9fa;
  color: #495057;
}

.close-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-body {
  padding: 1.5rem;
}

.text-muted {
  color: #6b7280;
  font-size: 0.875rem;
  line-height: 1.5;
}

.mb-3 {
  margin-bottom: 1rem;
}

.shift-info {
  background: #f8f9fa;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  font-size: 0.875rem;
}

.info-row:not(:last-child) {
  border-bottom: 1px solid #e9ecef;
}

.info-row span {
  color: #6c757d;
}

.info-row strong {
  color: #1f2937;
  font-weight: 600;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.input-with-currency {
  position: relative;
  display: flex;
  align-items: center;
}

.currency-symbol {
  position: absolute;
  left: 1rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: #495057;
  pointer-events: none;
}

.form-input {
  width: 100%;
  padding: 0.875rem 1rem 0.875rem 2.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input:disabled {
  background-color: #f9fafb;
  cursor: not-allowed;
  opacity: 0.6;
}

.helper-text {
  display: block;
  margin-top: 0.5rem;
  color: #6c757d;
  font-size: 0.75rem;
  font-style: italic;
}

.error-message {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 1rem;
  background: #f8f9fa;
  border-radius: 0 0 1rem 1rem;
}

.btn-confirm,
.btn-cancel {
  flex: 1;
  padding: 0.875rem 1rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-confirm {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-confirm:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-cancel {
  background: #e5e7eb;
  color: #374151;
}

.btn-cancel:hover:not(:disabled) {
  background: #d1d5db;
}

.btn-cancel:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner-small {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive design */
@media (max-width: 1024px) {
  .page-content {
    padding: 2rem;
  }
  
  .content-header {
    padding: 0 2rem;
  }
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }
  
  .page-content {
    padding: 1.5rem;
  }
  
  .content-header {
    padding: 0 1.5rem;
    height: 80px;
    position: relative;
  }
  
  .content-header h1 {
    font-size: 1.5rem;
  }
  
  .datetime-display {
    font-size: 0.75rem;
  }
  
  .modal-content {
    width: 95%;
  }
  
  .modal-footer {
    flex-direction: column;
  }
  
  .btn-confirm,
  .btn-cancel {
    width: 100%;
  }
}

.summary-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.summary-header h3 {
  color: white;
}

.summary-subtitle {
  font-size: 0.875rem;
  opacity: 0.9;
  margin: 0.25rem 0 0 0;
}

.summary-section {
  margin-bottom: 2rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e5e7eb;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.summary-card {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.summary-card.highlight-card {
  background: linear-gradient(135deg, #fef3c7 0%, #fde047 100%);
  border-color: #fbbf24;
}

.summary-card.stat-card {
  background: linear-gradient(135deg, #dbeafe 0%, #93c5fd 100%);
  border-color: #3b82f6;
}

.card-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.card-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #1f2937;
}

.card-value.large {
  font-size: 1.5rem;
  color: #1e40af;
}

.reconciliation-table {
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid #e5e7eb;
}

.recon-row {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  font-size: 0.875rem;
}

.recon-row:not(:last-child) {
  border-bottom: 1px solid #e5e7eb;
}

.recon-row.divider {
  border-top: 2px solid #d1d5db;
  padding-top: 1rem;
  margin-top: 0.5rem;
}

.recon-row.highlight {
  background: #eff6ff;
  padding: 0.75rem 1rem;
  margin: 0.5rem -1rem;
  border-radius: 0.375rem;
}

.recon-row.variance-over {
  color: #059669;
  font-weight: 600;
}

.recon-row.variance-short {
  color: #dc2626;
  font-weight: 600;
}

.recon-row.variance-exact {
  color: #059669;
  font-weight: 600;
}

.alert {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-top: 1.5rem;
  align-items: flex-start;
}

.alert svg {
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.alert strong {
  display: block;
  margin-bottom: 0.25rem;
}

.alert p {
  margin: 0;
  font-size: 0.875rem;
}

.alert-success {
  background: #d1fae5;
  border: 1px solid #4ea87a;
  color: #065f46;
}

.alert-warning {
  background: #fef3c7;
  border: 1px solid #fbbf24;
  color: #92400e;
}

.alert-danger {
  background: #fecaca;
  border: 1px solid #dc2626;
  color: #991b1b;
}

.btn-confirm.full-width {
  width: 100%;
}

.text-success {
  color: #059669;
}

@media (max-width: 480px) {
  .page-content {
    padding: 1rem;
  }
  
  .content-header {
    padding: 0 1rem;
    height: 70px;
  }
  
  .content-header h1 {
    font-size: 1.25rem;
  }
  
  .datetime-display {
    font-size: 0.7rem;
  }
  
  .modal-header h3 {
    font-size: 1.25rem;
  }
}
</style>