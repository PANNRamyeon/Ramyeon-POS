<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <!-- Logo Section -->
      <div class="logo-section">
        <div class="logo-placeholder">
           <img src="../assets/Logo_1.png" alt="Company Logo" class="logo-image" style="width: 120px; height: 150px;" />
        </div>
      </div>

      <!-- Navigation Menu -->
      <nav class="nav-menu">
        <!-- New Order -->
        <div class="nav-item" @click="handleNavigation('new-order')">
          <div class="nav-icon-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#000000"><path d="M120-80v-800l60 60 60-60 60 60 60-60 60 60 60-60 60 60 60-60 60 60 60-60 60 60 60-60v800l-60-60-60 60-60-60-60 60-60-60-60 60-60-60-60 60-60-60-60 60-60-60-60 60Zm120-200h480v-80H240v80Zm0-160h480v-80H240v80Zm0-160h480v-80H240v80Zm-40 404h560v-568H200v568Zm0-568v568-568Z"/></svg></div>
          <span class="nav-label">New Order</span>
        </div>

        <!-- Dashboard - Active State -->
        <div class="nav-item active" @click="handleNavigation('dashboard')">
          <div class="nav-icon-placeholder">
          <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#000000"><path d="M520-600v-240h320v240H520ZM120-440v-400h320v400H120Zm400 320v-400h320v400H520Zm-400 0v-240h320v240H120Zm80-400h160v-240H200v240Zm400 320h160v-240H600v240Zm0-480h160v-80H600v80ZM200-200h160v-80H200v80Zm160-320Zm240-160Zm0 240ZM360-280Z"/></svg></div>
          <span class="nav-label">Dashboard</span>
        </div>

        <!-- Online Order with Notification -->
        <div class="nav-item" @click="handleNavigation('online-order')">
          <div class="nav-icon-placeholder">
           <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#000000"><path d="m320-410 79-110h170L320-716v306ZM551-80 406-392 240-160v-720l560 440H516l144 309-109 51ZM399-520Z"/></svg>
          </div>
          <span class="nav-label">Online Order</span>
          <div class="notification-badge">1</div>
        </div>

        <!-- History -->
        <div class="nav-item" @click="handleNavigation('history')">
          <div class="nav-icon-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#000000"><path d="M480-120q-138 0-240.5-91.5T122-440h82q14 104 92.5 172T480-200q117 0 198.5-81.5T760-480q0-117-81.5-198.5T480-760q-69 0-129 32t-101 88h110v80H120v-240h80v94q51-64 124.5-99T480-840q75 0 140.5 28.5t114 77q48.5 48.5 77 114T840-480q0 75-28.5 140.5t-77 114q-48.5 48.5-114 77T480-120Zm112-192L440-464v-216h80v184l128 128-56 56Z"/></svg>
          </div>
          <span class="nav-label">History</span>
        </div>

        <!-- Settings -->
        <div class="nav-item" @click="handleNavigation('settings')">
          <div class="nav-icon-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#000000"><path d="m370-80-16-128q-13-5-24.5-12T307-235l-119 50L78-375l103-78q-1-7-1-13.5v-27q0-6.5 1-13.5L78-585l110-190 119 50q11-8 23-15t24-12l16-128h220l16 128q13 5 24.5 12t22.5 15l119-50 110 190-103 78q1 7 1 13.5v27q0 6.5-2 13.5l103 78-110 190-118-50q-11 8-23 15t-24 12L590-80H370Zm70-80h79l14-106q31-8 57.5-23.5T639-327l99 41 39-68-86-65q5-14 7-29.5t2-31.5q0-16-2-31.5t-7-29.5l86-65-39-68-99 42q-22-23-48.5-38.5T533-694l-13-106h-79l-14 106q-31 8-57.5 23.5T321-633l-99-41-39 68 86 64q-5 15-7 30t-2 32q0 16 2 31t7 30l-86 65 39 68 99-42q22 23 48.5 38.5T427-266l13 106Zm42-180q58 0 99-41t41-99q0-58-41-99t-99-41q-59 0-99.5 41T342-480q0 58 40.5 99t99.5 41Zm-2-140Z"/></svg>
          </div>
          <span class="nav-label">Settings</span>
        </div>

        <!-- Logout -->
        <div class="nav-item " @click="handleLogout">
          <div class="nav-icon-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#000000"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h280v80H200v560h280v80H200Zm440-160-55-58 102-102H360v-80h327L585-622l55-58 200 200-200 200Z"/></svg>
          </div>
          <span class="nav-label">Logout</span>
        </div>
      </nav>
    </aside>

    <!-- Main Content Area -->
    <main class="main-content">
      <div class="content-placeholder">
        <h2>Main Content Area</h2>
        <p>Current Page: {{ currentPage }}</p>
        <p>This is where your page content will go.</p>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'SidebarLayout',
  data() {
    return {
      currentPage: 'Dashboard'
    }
  },
  methods: {
    handleNavigation(page) {
      // Update current page
      this.currentPage = this.formatPageName(page)
      
      // Here you would handle actual navigation
      console.log(`Navigating to: ${page}`)
      
      // Example: this.$router.push(`/${page}`)
    },

    handleLogout() {
      // Clear stored data
      localStorage.removeItem('authToken')
      localStorage.removeItem('userData')
      localStorage.removeItem('loginTime')
      
      console.log('Logging out...')
      
      // Navigate back to login
      // this.$router.push('/login')
    },

    formatPageName(page) {
      return page.split('-').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ')
    }
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Sidebar Styles */
.sidebar {
  width: 200px;
  background-color: #f8f9fa;
  border-right: 1px solid #e9ecef;
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

.logo-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.logo-text {
  color: white;
  font-weight: bold;
  font-size: 0.875rem;
  letter-spacing: 1px;
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
  padding: 0.875rem 1rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  color: #6c757d;
  font-weight: 500;
}

/* Default state - dark icons */
.nav-item .nav-icon-placeholder svg {
  fill: #6c757d;
  transition: fill 0.2s ease;
}

/* Hover state - white text and icons */
.nav-item:hover {
  background-color: #e9ecef;
  color: #495057;
}

.nav-item:hover .nav-icon-placeholder svg {
  fill: #495057;
}

/* Active state - white text and icons */
.nav-item.active {
  background-color: #6f42c1;
  color: white;
  box-shadow: 0 2px 4px rgba(111, 66, 193, 0.3);
}

.nav-item.active .nav-icon-placeholder svg {
  fill: white;
}

/* Special styling for logout button */
.nav-item.logout {
  margin-top: auto;
  color: #dc3545;
}

.nav-item.logout .nav-icon-placeholder svg {
  fill: #dc3545;
}

.nav-item.logout:hover {
  background-color: #f8d7da;
  color: #721c24;
}

.nav-item.logout:hover .nav-icon-placeholder svg {
  fill: #721c24;
}

.nav-icon-placeholder {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.75rem;
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
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
}

/* Main Content */
.main-content {
  flex: 1;
  background-color: #ffffff;
  overflow-y: auto;
}

.content-placeholder {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.content-placeholder h2 {
  color: #495057;
  margin-bottom: 1rem;
}

.content-placeholder p {
  color: #6c757d;
  line-height: 1.6;
  margin-bottom: 0.5rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid #e9ecef;
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
    margin-right: 0;
    margin-bottom: 0.25rem;
  }
  
  .nav-label {
    font-size: 0.75rem;
  }
  
  .logo-section {
    display: none;
  }
  
  .content-placeholder {
    padding: 1rem;
  }
}

@media (max-width: 480px) {
  .nav-label {
    display: none;
  }
  
  .nav-item {
    min-width: 60px;
  }
}
</style>