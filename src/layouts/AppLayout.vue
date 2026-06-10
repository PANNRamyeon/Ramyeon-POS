<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <ModernSidebar 
      @sidebar-toggled="handleSidebarToggle"
    />
    
    <!-- Main Content Area -->
    <main class="main-content" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- Page Content -->
      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script>
import ModernSidebar from '@/components/layouts/Sidebar.vue'

export default {
  name: 'AppLayout',
  components: {
    ModernSidebar
  },
  data() {
    return {
      sidebarCollapsed: false
    }
  },
  methods: {
    handleSidebarToggle(collapsed) {
      this.sidebarCollapsed = collapsed
    }
  },
  mounted() {
    // Load sidebar state from localStorage
    const savedState = localStorage.getItem('sidebar-collapsed')
    if (savedState !== null) {
      this.sidebarCollapsed = JSON.parse(savedState)
      
      // Emit the initial state to sync with sidebar
      this.$nextTick(() => {
        this.handleSidebarToggle(this.sidebarCollapsed)
      })
    }
  }
}
</script>

<style scoped>
/* App Layout Container */
.app-layout {
  height: 100vh;
  max-height: 100vh;
  overflow: hidden;
  background-color: var(--neutral-light);
  display: flex;
}

/* Main Content Area */
.main-content {
  margin-left: 280px; /* Default sidebar width */
  transition: margin-left 0.3s ease;
  height: 100vh;
  max-height: 100vh;
  min-width: 0; /* Prevent overflow issues */
  display: flex;
  flex-direction: column;
  flex: 1;
}

.main-content.sidebar-collapsed {
  margin-left: 80px; /* Collapsed sidebar width */
}

/* Page Content */
.page-content {
  background-color: var(--neutral-light);
  overflow: hidden;
  height: 100%;
  max-height: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0; /* Remove any default padding since your router-view should handle its own spacing */
}

/* Responsive Design */
@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
    width: 100vw;
  }
  
  .main-content.sidebar-collapsed {
    margin-left: 0;
    width: 100vw;
  }
}

/* Ensure smooth transitions and prevent content jumping */
* {
  box-sizing: border-box;
}
</style>