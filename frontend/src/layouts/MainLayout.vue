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
            <h1>{{ currentPageTitle }}</h1>
          </div>
        </div>
      </header>
      <!-- Page Content - This will now show the routed component -->
      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from './Sidebar.vue'

export default {
  name: 'MainLayout',
  components: {
    Sidebar
  },
  data() {
    return {
      currentTime: new Date(),
      timeInterval: null
    }
  },
  computed: {
    currentPageTitle() {
      const titles = {
        '/dashboard': 'Dashboard',
        '/online-orders': 'Online Orders',
      }
      return titles[this.$route.path] || 'Page'
    },
    currentDateTime() {
      const now = this.currentTime
      
      try {
        // Format: "28 October 2021 Thursday | 17:30"
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
        
        // Rearrange the date format
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
    async handleLogout() {
      console.log('User logging out')
      
      try {
        // Call logout API
        const token = localStorage.getItem('authToken')
        if (token) {
          await fetch('http://localhost:8000/api/v1/auth/logout/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          })
        }
      } catch (error) {
        console.error('Logout API error:', error)
      } finally {
        // Clear stored data
        localStorage.removeItem('authToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('userData')
        
        // Redirect to login
        this.$router.push('/login')
      }
    },
    updateTime() {
      this.currentTime = new Date()
    }
  },
  mounted() {
    // Start the time update interval (update every second)
    this.timeInterval = setInterval(this.updateTime, 1000)
  },
  beforeUnmount() {
    // Clear the interval when component is destroyed
    if (this.timeInterval) {
      clearInterval(this.timeInterval)
    }
  },
  beforeRouteEnter(to, from, next) {
    // Check if user is authenticated before entering any protected route
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

.app-layout {
  min-height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 0;
  background-color: #f8f9fa;
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
  border-bottom: 1px solid #e9ecef;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
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
  color: #6c757d;
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.025em;
  line-height: 1.2;
}

.content-header h1 {
  color: #495057;
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
  
  .sidebar {
    position: relative;     
    height: auto;
    width: 100%;
    z-index: auto;
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
}
</style>