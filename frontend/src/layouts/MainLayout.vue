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

    <!-- Shift Required Modal -->
    <Teleport to="body">
      <div 
        v-if="showShiftRequiredModal"
        class="modal-overlay"
        @click.self="showShiftRequiredModal = false"
      >
        <div class="logout-modal">
          <div class="logout-modal-header">
            <div class="logout-modal-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4"/>
                <path d="M12 8h.01"/>
              </svg>
            </div>
            <h3 class="logout-modal-title">Close Shift Required</h3>
            <p class="logout-modal-message">
              You have an active shift that must be closed before logging out. Please go to the Shift page to close your shift.
            </p>
          </div>
          
          <div class="logout-modal-footer">
            <button 
              class="logout-modal-btn logout-modal-btn-primary" 
              @click="goToShiftPage"
            >
              Go to Shift Page
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Logout Confirmation Modal -->
    <Teleport to="body">
      <div 
        v-if="showLogoutConfirmModal"
        class="modal-overlay"
        @click.self="showLogoutConfirmModal = false"
      >
        <div class="logout-modal">
          <div class="logout-modal-header">
            <div class="logout-modal-icon logout-modal-icon-warning">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 11 12 14 22 4"/>
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
              </svg>
            </div>
            <h3 class="logout-modal-title">Confirm Logout</h3>
            <p class="logout-modal-message">
              Are you sure you want to log out?
            </p>
          </div>
          
          <div class="logout-modal-footer">
            <button 
              class="logout-modal-btn logout-modal-btn-cancel" 
              @click="showLogoutConfirmModal = false"
            >
              Cancel
            </button>
            <button 
              class="logout-modal-btn logout-modal-btn-primary" 
              @click="confirmLogout"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </Teleport>

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
      showShiftRequiredModal: false,
      showLogoutConfirmModal: false
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
        '/shift': 'Shift'
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
        return now.toString()
      }
    }
  },
  
  methods: {
    handleMenuChange(menu) {
      this.$router.push(`/${menu}`)
    },
    
    async handleLogout() {
      const userData = JSON.parse(localStorage.getItem('userData') || '{}')
      const userRole = userData.role?.toLowerCase()
      const activeShiftId = localStorage.getItem('activeShiftId')
      
      if ((userRole === 'cashier' || userRole === 'employee') && activeShiftId) {
        // Show modal requiring shift to be closed first
        this.showShiftRequiredModal = true
        return
      }
      
      // Show confirmation modal
      this.showLogoutConfirmModal = true
    },

    goToShiftPage() {
      this.showShiftRequiredModal = false
      this.$router.push('/shift')
    },

    async confirmLogout() {
      this.showLogoutConfirmModal = false
      await this.performLogout(0)
    },
    
    async performLogout(closingCash = 0) {
      try {
        // Call auth logout endpoint (shift already closed)
        try {
          await apiService.logout(0)
        } catch (error) {
          // Continue with logout even if API fails
        }
        
      } catch (error) {
        // Logout error
      } finally {
        // Clear all stored data
        localStorage.removeItem('authToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('userData')
        localStorage.removeItem('activeShiftId')
        localStorage.removeItem('currentCartId')
        
        // Redirect to login
        this.$router.push('/login')
      }
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

/* Logout Modals */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.logout-modal {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-width: 500px;
  width: 90%;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.logout-modal-header {
  padding: 2rem;
  text-align: center;
}

.logout-modal-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.logout-modal-icon svg {
  color: #ef4444;
  width: 48px;
  height: 48px;
}

.logout-modal-icon-warning svg {
  color: #f59e0b;
}

.logout-modal-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.75rem 0;
}

.logout-modal-message {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.logout-modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.logout-modal-btn {
  padding: 0.625rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  outline: none;
}

.logout-modal-btn-cancel {
  background: white;
  color: #6b7280;
  border: 2px solid #e5e7eb;
}

.logout-modal-btn-cancel:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.logout-modal-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.logout-modal-btn-primary:hover {
  background: linear-gradient(135deg, #5568d3 0%, #653a8a 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.logout-modal-btn-primary:active {
  transform: translateY(0);
}
</style>