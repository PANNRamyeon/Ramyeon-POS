<template>
  <div class="app-layout surface-tertiary transition-theme">
    <!-- Sidebar Component -->
    <Sidebar 
      @menu-changed="handleMenuChange"
      @logout="handleLogout"
    />
    
    <!-- Main Content Area -->
    <main class="main-content">
      <!-- Header Bar -->
      <header class="content-header surface-primary border-bottom-theme shadow-sm transition-theme">
        <div class="header-content">
          <!-- Left Side - Date/Time and Page Title -->
          <div class="header-left">
            <div class="datetime-display text-secondary">
              {{ currentDateTime }}
            </div>
          </div>
        </div>
      </header>
      
      <!-- Page Content - This will now show the routed component -->
      <div class="page-content surface-tertiary transition-theme">
        <router-view />
      </div>
    </main>

    <!-- ✅ Logout Confirmation Modal with Closing Cash -->
    <div v-if="showLogoutModal" class="modal-overlay" @click="closeLogoutModal">
      <div class="modal-content" @click.stop>
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
                :disabled="logoutLoading"
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
            :disabled="logoutLoading"
          >
            Cancel
          </button>
          <button 
            @click="confirmLogout" 
            class="btn-confirm"
            :disabled="logoutLoading || !closingCash"
          >
            <span v-if="!logoutLoading">End Shift & Logout</span>
            <span v-else>
              <span class="spinner-small"></span> Ending Shift...
            </span>
          </button>
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
      closingCash: 0,
      logoutLoading: false,
      logoutError: null,
      shiftInfo: null
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
    }
  },
  
  methods: {
    handleMenuChange(menu) {
      console.log('Menu changed to:', menu)
      this.$router.push(`/${menu}`)
    },
    
    // ✅ NEW: Show modal and load shift info
    async handleLogout() {
      console.log('📤 Logout initiated')
      
      try {
        // Get user data
        const userData = JSON.parse(localStorage.getItem('userData') || '{}')
        const userRole = userData.role?.toLowerCase()
        const activeShiftId = localStorage.getItem('activeShiftId')
        
        console.log('👤 User role:', userRole)
        console.log('⏰ Active shift:', activeShiftId)
        
        // If user has an active shift, show modal to enter closing cash
        if ((userRole === 'cashier' || userRole === 'employee') && activeShiftId) {
          // Load shift info
          await this.loadShiftInfo(activeShiftId)
          
          // Pre-fill with opening cash as default
          this.closingCash = this.shiftInfo?.openingCash || 0
          
          // Show modal
          this.showLogoutModal = true
          return
        }
        
        // For admin or users without shifts, proceed with normal logout
        await this.performLogout(0)
        
      } catch (error) {
        console.error('❌ Logout initialization failed:', error)
        // Still allow logout even if shift info fails
        this.showLogoutModal = true
      }
    },
    
    // ✅ NEW: Load shift information
    async loadShiftInfo(shiftId) {
      try {
        const response = await apiService.getActiveShift(localStorage.getItem('userData') && JSON.parse(localStorage.getItem('userData')).user_id)
        
        if (response && response.shift) {
          this.shiftInfo = {
            shiftId: response.shift._id,
            openingCash: response.shift.opening_cash || 0,
            startTime: response.shift.start_time
          }
          console.log('✅ Shift info loaded:', this.shiftInfo)
        }
      } catch (error) {
        console.error('⚠️ Failed to load shift info:', error)
        this.shiftInfo = {
          shiftId: shiftId,
          openingCash: 0,
          startTime: null
        }
      }
    },
    
    // ✅ NEW: Confirm logout with closing cash
    async confirmLogout() {
      if (this.closingCash < 0) {
        this.logoutError = 'Closing cash cannot be negative'
        return
      }
      
      this.logoutError = null
      this.logoutLoading = true
      
      try {
        console.log('💰 Ending shift with closing cash:', this.closingCash)
        
        await this.performLogout(this.closingCash)
        
      } catch (error) {
        console.error('❌ Logout failed:', error)
        this.logoutError = error.message || 'Failed to end shift. Please try again.'
      } finally {
        this.logoutLoading = false
      }
    },
    
    // ✅ UPDATED: Perform logout with closing cash
    async performLogout(closingCash = 0) {
      try {
        console.log('🚪 Performing logout with closing cash:', closingCash)
        
        // Call logout API with closing cash
        await apiService.logout(closingCash)
        
        console.log('✅ Logout API successful')
        
      } catch (error) {
        console.error('⚠️ Logout API error:', error)
        // Continue with logout even if API fails
      } finally {
        // Clear all stored data
        localStorage.removeItem('authToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('userData')
        localStorage.removeItem('activeShiftId')
        localStorage.removeItem('currentCartId')
        
        console.log('🧹 Cleared localStorage')
        
        // Close modal if open
        this.showLogoutModal = false
        
        // Redirect to login
        this.$router.push('/login')
        
        console.log('✅ Logout complete')
      }
    },
    
    // ✅ NEW: Close modal
    closeLogoutModal() {
      if (!this.logoutLoading) {
        this.showLogoutModal = false
        this.closingCash = 0
        this.logoutError = null
        this.shiftInfo = null
      }
    },
    
    // ✅ NEW: Format currency
    formatCurrency(amount) {
      return parseFloat(amount || 0).toFixed(2)
    },
    
    // ✅ NEW: Format time
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
    
    updateTime() {
      this.currentTime = new Date()
    }
  },
  
  mounted() {
    // Start the time update interval
    this.timeInterval = setInterval(this.updateTime, 1000)
  },
  
  beforeUnmount() {
    // Clear the interval when component is destroyed
    if (this.timeInterval) {
      clearInterval(this.timeInterval)
    }
  },
  
  beforeRouteEnter(to, from, next) {
    // Check if user is authenticated
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
  height: 100vh;
  max-height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 0;
  overflow: hidden;
  display: flex;
}

.main-content {
  margin-left: 180px;
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-height: 100vh;
  min-width: 0;
  flex: 1;
  overflow: hidden;
}

.content-header {
  position: sticky;
  top: 0;
  z-index: 999;
  background: white;
  height: 70px;
  padding: 0 1.5rem;
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
  font-size: 0.8rem;
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
  padding: 0;
  overflow: hidden;
  width: 100%;
  min-width: 0;
  background-color: #f8f9fa;
  display: flex;
  flex-direction: column;
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
  .content-header {
    padding: 0 1.25rem;
    height: 65px;
  }
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }
  
  .content-header {
    padding: 0 1rem;
    height: 60px;
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

@media (max-width: 480px) {
  .content-header {
    padding: 0 0.75rem;
    height: 55px;
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