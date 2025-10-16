  <template>
    <aside class="sidebar surface-primary border-right-theme shadow-lg transition-theme">
      <!-- Logo Section -->
      <div class="logo-section">
        <div class="logo-placeholder">
          <img src="../assets/Logo_1.png" alt="Company Logo" class="logo-image" style="width: 65px; height: 90px;" />
        </div>
      </div>

      <!-- Navigation Menu -->
      <nav class="nav-menu">
        <!-- New Order -->
        <div class="nav-item transition-theme" @click="handleNavigation('new-order')" :class="{ active: currentPage === 'new-order' }">
          <div class="nav-icon-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
              <path d="M120-80v-800l60 60 60-60 60 60 60-60 60 60 60-60 60 60 60-60 60 60 60-60 60 60 60-60v800l-60-60-60 60-60-60-60 60-60-60-60 60-60-60-60 60-60-60-60 60-60-60-60 60Zm120-200h480v-80H240v80Zm0-160h480v-80H240v80Zm0-160h480v-80H240v80Zm-40 404h560v-568H200v568Zm0-568v568-568Z"/>
            </svg>
          </div>
          <span class="nav-label">New Order</span>
        </div>

        <!-- Dashboard - Active State -->
        <div class="nav-item transition-theme" @click="handleNavigation('dashboard')" :class="{ active: currentPage === 'dashboard' }">
          <div class="nav-icon-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
              <path d="M520-600v-240h320v240H520ZM120-440v-400h320v400H120Zm400 320v-400h320v400H520Zm-400 0v-240h320v240H120Zm80-400h160v-240H200v240Zm400 320h160v-240H600v240Zm0-480h160v-80H600v80ZM200-200h160v-80H200v80Zm160-320Zm240-160Zm0 240ZM360-280Z"/>
            </svg>
          </div>
          <span class="nav-label">Dashboard</span>
        </div>

        <!-- Online Order with Dynamic Notification -->
        <div class="nav-item" @click="handleNavigation('online-order')" :class="{ active: currentPage === 'online-order' }">
          <div class="nav-icon-placeholder">
            <svg v-if="pendingCount > 0" xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
              <!-- Bell with notification (filled) -->
              <path d="M480-80q-33 0-56.5-23.5T400-160h160q0 33-23.5 56.5T480-80Zm320-240v-240q0-116-77-198t-195-90v-22q0-17-11.5-28.5T488-910q-17 0-28.5 11.5T448-870v22q-118 8-195 90t-77 198v240l-80 80v40h784v-40l-80-80Zm-80 0H240v-240q0-92 64-156t156-64q92 0 156 64t64 156v240Z"/>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
              <!-- Inbox icon when none pending -->
              <path d="M160-160q-33 0-56.5-23.5T80-240v-480q0-33 23.5-56.5T160-800h640q33 0 56.5 23.5T880-720v480q0 33-23.5 56.5T800-160H160Zm0-80h153l47-80h240l47 80h153v-480H160v480Zm320-120q-50 0-85-35t-35-85h80q0 17 11.5 28.5T480-440q17 0 28.5-11.5T520-480h80q0 50-35 85t-85 35Z"/>
            </svg>
          </div>
          <span class="nav-label">Pending Order</span>
          <!-- ✅ Dynamic Badge -->
          <div v-if="pendingOrderCount > 0" class="notification-badge" :class="{ 'badge-pulse': pendingOrderCount > 0 }">
            {{ pendingOrderCount > 99 ? '99+' : pendingOrderCount }}
          </div>
        </div>

        <!-- History -->
        <div class="nav-item transition-theme" @click="handleNavigation('history')" :class="{ active: currentPage === 'history' }">
          <div class="nav-icon-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
              <path d="M480-120q-138 0-240.5-91.5T122-440h82q14 104 92.5 172T480-200q117 0 198.5-81.5T760-480q0-117-81.5-198.5T480-760q-69 0-129 32t-101 88h110v80H120v-240h80v94q51-64 124.5-99T480-840q75 0 140.5 28.5t114 77q48.5 48.5 77 114T840-480q0 75-28.5 140.5t-77 114q-48.5 48.5-114 77T480-120Zm112-192L440-464v-216h80v184l128 128-56 56Z"/>
            </svg>
          </div>
          <span class="nav-label">History</span>
        </div>

        <!-- Settings -->
        <div class="nav-item transition-theme" @click="handleNavigation('settings')" :class="{ active: currentPage === 'settings' }">
          <div class="nav-icon-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
              <path d="m370-80-16-128q-13-5-24.5-12T307-235l-119 50L78-375l103-78q-1-7-1-13.5v-27q0-6.5 1-13.5L78-585l110-190 119 50q11-8 23-15t24-12l16-128h220l16 128q13 5 24.5 12t22.5 15l119-50 110 190-103 78q1 7 1 13.5v27q0 6.5-2 13.5l103 78-110 190-118-50q-11 8-23 15t-24 12L590-80H370Zm70-80h79l14-106q31-8 57.5-23.5T639-327l99 41 39-68-86-65q5-14 7-29.5t2-31.5q0-16-2-31.5t-7-29.5l86-65-39-68-99 42q-22-23-48.5-38.5T533-694l-13-106h-79l-14 106q-31 8-57.5 23.5T321-633l-99-41-39 68 86 64q-5 15-7 30t-2 32q0 16 2 31t7 30l-86 65 39 68 99-42q22 23 48.5 38.5T427-266l13 106Zm42-180q58 0 99-41t41-99q0-58-41-99t-99-41q-59 0-99.5 41T342-480q0 58 40.5 99t99.5 41Zm-2-140Z"/>
            </svg>
          </div>
          <span class="nav-label">Settings</span>
        </div>

        <!-- Logout -->
        <div class="nav-item transition-theme" @click="handleLogout">
          <div class="nav-icon-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
              <path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h280v80H200v560h280v80H200Zm440-160-55-58 102-102H360v-80h327L585-622l55-58 200 200-200 200Z"/>
            </svg>
          </div>
          <span class="nav-label">Logout</span>
        </div>
      </nav>
    </aside>
  </template>

  <script>
  import onlineOrdersAPI from '@/services/apiOnlineOrder.js'
  import { api } from '@/services/api.js'

  export default {
    name: 'Sidebar',
    data() {
      return {
        currentPage: 'dashboard',
        pendingCount: 0,
        _pendingPoller: null,
        _originalTitle: document.title,
        _originalFaviconHref: null,
        pendingOrderCount: 0,
        refreshInterval: null
      }
    },
    
    async mounted() {
      // Initial fetch
      await this.fetchPendingOrderCount()
      
      // ✅ Auto-refresh every 30 seconds
      this.refreshInterval = setInterval(() => {
        this.fetchPendingOrderCount()
      }, 30000) // 30 seconds
    },
    
    beforeUnmount() {
      // ✅ Clean up interval when component is destroyed
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
      }
    },
    
    methods: {
      async fetchPendingOrderCount() {
        try {
          console.log('📦 Fetching pending order count...')
          
          // ✅ Fetch orders with pending/confirmed/processing status
          const response = await api.get('/online/orders/', {
            params: {
              limit: 1000 // Get all orders (or use pagination)
            }
          })
          
          console.log('📦 Orders response:', response.data)
          
          // ✅ Extract orders from response
          let orders = []
          if (response.data.success && response.data.data?.orders) {
            orders = response.data.data.orders
          } else if (response.data.orders) {
            orders = response.data.orders
          } else if (Array.isArray(response.data)) {
            orders = response.data
          }
          
          console.log('📦 Total orders found:', orders.length)
          
          // ✅ Count orders that are not completed or cancelled
          const pendingStatuses = ['pending', 'confirmed', 'processing', 'on_the_way']
          const pendingOrders = orders.filter(order => 
            pendingStatuses.includes(order.order_status?.toLowerCase())
          )
          
          this.pendingOrderCount = pendingOrders.length
          
          console.log('✅ Pending order count:', this.pendingOrderCount)
          console.log('   Breakdown:', {
            pending: orders.filter(o => o.order_status === 'pending').length,
            confirmed: orders.filter(o => o.order_status === 'confirmed').length,
            processing: orders.filter(o => o.order_status === 'processing').length,
            on_the_way: orders.filter(o => o.order_status === 'on_the_way').length
          })
          
        } catch (error) {
          console.error('❌ Failed to fetch pending orders:', error)
          // Don't show error to user, just silently fail
          this.pendingOrderCount = 0
        }
      },
      
      handleNavigation(page) {
        console.log(`Sidebar navigating to: ${page}`)
        this.currentPage = page
        
        // ✅ Refresh count when navigating to online-order page
        if (page === 'online-order') {
          this.fetchPendingOrderCount()
        }
        
        this.$emit('menu-changed', page)
      },

      handleLogout() {
        console.log('Sidebar logout clicked')
        this.$emit('logout')
      },

      async fetchPendingCount() {
        try {
          const data = await onlineOrdersAPI.getAllOrders({ status: 'pending' })
          console.log('[Sidebar] Pending orders raw response:', data)
          let count = 0
          let branch = 'none'
          if (Array.isArray(data)) {
            count = data.length
            branch = 'array'
          } else if (Array.isArray(data?.results)) {
            count = data.results.length
            branch = 'results[]'
          } else if (typeof data?.count === 'number') {
            count = data.count
            branch = 'count'
          } else if (Array.isArray(data?.orders)) {
            count = data.orders.length
            branch = 'orders[]'
          }
          console.log('[Sidebar] Parsed pending count:', count, 'via branch:', branch)
          this.pendingCount = count
          this.updateAppBadge(count)
        } catch (e) {
          console.error('[Sidebar] Failed to fetch pending orders count:', e)
        }
      },

      updateAppBadge(count) {
        const capped = count > 99 ? 99 : count
        // 1) Try App Badging API (PWA-capable browsers)
        if (navigator && 'setAppBadge' in navigator) {
          if (capped > 0) {
            navigator.setAppBadge(capped).catch(() => {})
          } else {
            navigator.clearAppBadge && navigator.clearAppBadge().catch(() => {})
          }
        }
        // 2) Update document title as fallback
        if (capped > 0) {
          document.title = `(${capped}) ${this._originalTitle}`
        } else {
          document.title = this._originalTitle
        }
        // 3) Favicon badge fallback
        this.updateFaviconBadge(capped)
      },

      updateFaviconBadge(count) {
        // find current favicon
        const linkEl = document.querySelector('link[rel="icon"]') || document.createElement('link')
        if (!this._originalFaviconHref) {
          this._originalFaviconHref = linkEl.href || '/favicon.ico'
        }
        if (count <= 0) {
          if (linkEl) {
            linkEl.rel = 'icon'
            linkEl.href = this._originalFaviconHref
            document.head.appendChild(linkEl)
          }
          return
        }
        const img = document.createElement('img')
        img.crossOrigin = 'anonymous'
        img.onload = () => {
          const size = 64
          const canvas = document.createElement('canvas')
          canvas.width = size
          canvas.height = size
          const ctx = canvas.getContext('2d')
          ctx.clearRect(0, 0, size, size)
          // draw base icon
          ctx.drawImage(img, 0, 0, size, size)
          // draw badge
          const badgeSize = 28
          const x = size - badgeSize
          const y = 0
          ctx.fillStyle = '#e11d48' // rose-600 like
          ctx.beginPath()
          ctx.arc(x + badgeSize/2, y + badgeSize/2, badgeSize/2, 0, Math.PI * 2)
          ctx.fill()
          // text
          ctx.fillStyle = '#fff'
          ctx.font = 'bold 18px sans-serif'
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          const label = count > 99 ? '99+' : String(count)
          ctx.fillText(label, x + badgeSize/2, y + badgeSize/2 + 1)
          // apply
          const url = canvas.toDataURL('image/png')
          linkEl.rel = 'icon'
          linkEl.href = url
          document.head.appendChild(linkEl)
        }
        img.src = this._originalFaviconHref || '/favicon.ico'
      }
    },
    mounted() {
      this.fetchPendingCount()
      this._pendingPoller = setInterval(this.fetchPendingCount, 15000)
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') this.fetchPendingCount()
      })
    },
    beforeUnmount() {
      if (this._pendingPoller) clearInterval(this._pendingPoller)
      // reset badge/title/favicon
      if (navigator && 'clearAppBadge' in navigator) {
        navigator.clearAppBadge().catch(() => {})
      }
      document.title = this._originalTitle
      const linkEl = document.querySelector('link[rel="icon"]')
      if (linkEl && this._originalFaviconHref) {
        linkEl.href = this._originalFaviconHref
      }
      
      // ✅ Method to manually refresh (can be called from parent)
      refreshNotifications() 
        this.fetchPendingOrderCount()
      
    }
  }
  </script>

  <style scoped>

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    width: 180px;
    min-width: 180px;
    flex-shrink: 0;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    padding: 1rem 0;
  }

  .logo-section {
    padding: 1rem;
    text-align: center;
    margin-bottom: 2rem;
  }

  .logo-placeholder {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  /* Navigation Menu */
  .nav-menu {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0 1rem;
    flex: 1;
  }

  .nav-item {
    display: flex;
    align-items: center;
    flex-direction: column;
    padding: 1rem 0.5rem;
    border-radius: 0.5rem;
    cursor: pointer;
    position: relative;
    color: var(--text-secondary);
    font-weight: 500;
    text-align: center;
  }

  /* Default state - use semantic colors */
  .nav-item .nav-icon-placeholder svg {
    fill: var(--text-secondary);
    transition: fill 0.2s ease;
  }

  /* Hover state */
  .nav-item:hover {
    background-color: var(--state-hover);
    color: var(--text-primary);
  }

  .nav-item:hover .nav-icon-placeholder svg {
    fill: var(--text-primary);
  }

  /* Active state */
  .nav-item.active {
    background-color: var(--primary);
    color: var(--text-inverse);
    box-shadow: var(--shadow-md);
  }

  .nav-item.active .nav-icon-placeholder svg {
    fill: var(--text-inverse);
  }

  .nav-icon-placeholder {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.5rem;
    font-size: 1.25rem;
    flex-shrink: 0;
  }

  .nav-label {
    font-size: 0.875rem;
    white-space: nowrap;
  }

  /* Notification Badge */
  .notification-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background-color: #dc3545;
    color: white;
    border-radius: 50%;
    min-width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: bold;
    background-color: var(--status-error);
    color: var(--text-inverse);
    box-shadow: var(--shadow-sm);
    border: 2px solid var(--surface-primary);
    line-height: 1;
    z-index: 1;
    padding: 0 4px;
    box-shadow: 0 2px 4px rgba(220, 53, 69, 0.4);
  }

  /* ✅ Pulse Animation for Badge */
  .badge-pulse {
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0% {
      box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7);
    }
    50% {
      box-shadow: 0 0 0 6px rgba(220, 53, 69, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(220, 53, 69, 0);
    }
  }

  @media (max-width: 768px) {
    .sidebar {
      position: relative;      
      width: 100%;
      min-width: auto;
      height: auto;
      border-right: none;
      border-bottom: 1px solid var(--border-secondary);
      padding: 0.5rem 0;
    }
    
    .nav-menu {
      flex-direction: row;
      overflow-x: auto;
      padding: 0.5rem 1rem;
      gap: 0.25rem;
    }
    
    .nav-item {
      flex-direction: column;
      min-width: 80px;
      padding: 0.5rem;
      text-align: center;
    }
    
    .nav-icon-placeholder {
      margin-bottom: 0.25rem;
    }
    
    .nav-label {
      font-size: 0.75rem;
    }
    
    .logo-section {
      display: none;
    }
    
    .notification-badge {
      top: 0.25rem;
      right: 0.25rem;
      min-width: 16px;
      height: 16px;
      font-size: 0.625rem;
    }
  }

  @media (max-width: 900px) {
    .sidebar {
      width: 120px;          
      min-width: 120px;
      padding: 0.75rem 0;     
    }
    
    .logo-section {
      padding: 0.75rem;
      margin-bottom: 1.5rem;
    }
    
    .logo-image {
      width: 50px !important; 
      height: 70px !important;
    }
    
    .nav-menu {
      padding: 0 0.75rem;      
      gap: 0.25rem;           
    }
    
    .nav-item {
      padding: 0.75rem 0.25rem; 
    }
    
    .nav-label {
      font-size: 0.75rem;    
    }
    
    .nav-icon-placeholder {
      margin-bottom: 0.25rem;  
    }
  }
  </style>