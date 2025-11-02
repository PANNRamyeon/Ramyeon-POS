<template>
  <div id="app">
    <!-- This will show either Login page or the main app based on authentication -->
    <router-view />
    
    <!-- Offline Modal -->
    <Teleport to="body">
      <div 
        v-if="showOfflineModal"
        class="offline-modal-overlay"
        @click.self="closeOfflineModal"
      >
        <div class="offline-modal">
          <div class="offline-modal-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.5 4.58a10 10 0 1 0 0 14.82M15 12h-3M15 12l-3 3M15 12l-3-3M2 22l20-20"/>
            </svg>
          </div>
          <h3 class="offline-modal-title">You're Offline</h3>
          <p class="offline-modal-message">
            No internet connection detected. The system will continue to work in offline mode and sync data when you reconnect.
          </p>
          <div class="offline-modal-footer">
            <button 
              class="offline-modal-btn offline-modal-btn-primary" 
              @click="closeOfflineModal"
            >
              Continue Offline
            </button>
          </div>
        </div>
      </div>
      
      <!-- Online Modal -->
      <div 
        v-if="showOnlineModal"
        class="offline-modal-overlay"
        @click.self="closeOnlineModal"
      >
        <div class="offline-modal">
          <div class="offline-modal-icon online-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          <h3 class="offline-modal-title">You're Back Online</h3>
          <p class="offline-modal-message">
            Internet connection restored. The system is now syncing any pending data.
          </p>
          <div class="offline-modal-footer">
            <button 
              class="offline-modal-btn offline-modal-btn-primary" 
              @click="closeOnlineModal"
            >
              Got it
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      showOfflineModal: false,
      showOnlineModal: false,
      wasOffline: false
    }
  },
  mounted() {
    // Check authentication status when app loads
    this.checkAuthStatus()
    
    // Set up offline/online listeners
    this.setupOfflineListener()
  },
  beforeUnmount() {
    // Clean up listeners
    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.handleOnline)
      window.removeEventListener('offline', this.handleOffline)
    }
  },
  methods: {
    checkAuthStatus() {
      const token = localStorage.getItem('authToken')  
      const currentPath = this.$route.path
      
      // If no token and not on login page, redirect to login
      if (!token && currentPath !== '/login') {
        this.$router.push('/login')
      }
      
      // If has token and on login page, redirect to dashboard
      if (token && currentPath === '/login') {
        this.$router.push('/dashboard')
      }
    },
    
    setupOfflineListener() {
      // Check initial status
      if (typeof navigator !== 'undefined') {
        if (!navigator.onLine) {
          this.handleOffline()
        }
        
        // Add event listeners
        window.addEventListener('offline', this.handleOffline)
        window.addEventListener('online', this.handleOnline)
      }
    },
    
    handleOffline() {
      this.wasOffline = true
      this.showOfflineModal = true
      
      // Sync offline manager
      import('./services/offlineManager.js').then(({ default: offlineManager }) => {
        offlineManager.loadQueue()
      }).catch(() => {
        // Silent fail
      })
    },
    
    handleOnline() {
      if (this.wasOffline) {
        this.showOnlineModal = true
        
        // Trigger backend sync (this will process the backend's sync_queue)
        import('./services/api.js').then(({ default: apiService }) => {
          apiService.triggerSync()
        }).catch(() => {
          // Silent fail
        })
        
        // Also sync frontend queued requests
        import('./services/offlineManager.js').then(({ default: offlineManager }) => {
          offlineManager.syncQueuedRequests()
        }).catch(() => {
          // Silent fail
        })
      }
      
      this.wasOffline = false
    },
    
    closeOfflineModal() {
      this.showOfflineModal = false
    },
    
    closeOnlineModal() {
      this.showOnlineModal = false
    }
  }
}
</script>

<style>
/* Global reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow-x: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--surface-secondary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}

#app {
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
}

/* Bootstrap overrides for dark mode compatibility */
.text-muted {
  color: var(--text-tertiary) !important;
}

.btn-close {
  filter: var(--bs-btn-close-filter, none);
}

:root[data-theme="dark"] .btn-close {
  filter: invert(1) grayscale(100%) brightness(200%);
}

/* Offline/Online Modal Styles */
.offline-modal-overlay {
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
  z-index: 10000;
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

.offline-modal {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  width: 90%;
  max-width: 450px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
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

.offline-modal-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1.5rem;
  color: #ff9800;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #fff3e0;
  padding: 1rem;
}

.offline-modal-icon.online-icon {
  color: #4caf50;
  background: #e8f5e9;
}

.offline-modal-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  text-align: center;
  margin: 0 0 1rem 0;
}

.offline-modal-message {
  font-size: 1rem;
  color: #666;
  text-align: center;
  line-height: 1.6;
  margin: 0 0 2rem 0;
}

.offline-modal-footer {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.offline-modal-btn {
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  outline: none;
}

.offline-modal-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.offline-modal-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.offline-modal-btn-primary:active {
  transform: translateY(0);
}

/* Dark mode support */
:root[data-theme="dark"] .offline-modal {
  background: #2a2a2a;
}

:root[data-theme="dark"] .offline-modal-title {
  color: #fff;
}

:root[data-theme="dark"] .offline-modal-message {
  color: #ccc;
}
</style>