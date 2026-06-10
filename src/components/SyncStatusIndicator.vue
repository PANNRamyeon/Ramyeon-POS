<template>
  <div class="sync-status" :class="statusClass">
    <span class="status-icon">{{ statusIcon }}</span>
    <span class="status-text">{{ statusText }}</span>
    <span v-if="pendingCount > 0" class="pending-count">
      ({{ pendingCount }} pending)
    </span>
  </div>
</template>

<script>
import offlineManager from '../services/offlineManager.js'

export default {
  name: 'SyncStatusIndicator',
  data() {
    return {
      isOnline: navigator.onLine,
      isSyncing: false,
      pendingCount: 0,
      updateInterval: null
    }
  },
  computed: {
    statusClass() {
      if (!this.isOnline) return 'offline'
      if (this.isSyncing) return 'syncing'
      if (this.pendingCount > 0) return 'pending'
      return 'online'
    },
    statusIcon() {
      if (!this.isOnline) return '⚠️'
      if (this.isSyncing) return '🔄'
      if (this.pendingCount > 0) return '⏳'
      return '✅'
    },
    statusText() {
      if (!this.isOnline) return 'Offline'
      if (this.isSyncing) return 'Syncing...'
      if (this.pendingCount > 0) return 'Syncing...'
      return 'Online'
    }
  },
  mounted() {
    // Set up online/offline listeners
    window.addEventListener('online', this.handleOnline)
    window.addEventListener('offline', this.handleOffline)
    
    // Update pending count periodically
    this.updateInterval = setInterval(this.updatePendingCount, 2000)
    
    // Initial update
    this.updatePendingCount()
  },
  beforeUnmount() {
    window.removeEventListener('online', this.handleOnline)
    window.removeEventListener('offline', this.handleOffline)
    
    if (this.updateInterval) {
      clearInterval(this.updateInterval)
    }
  },
  methods: {
    handleOnline() {
      this.isOnline = true
      this.isSyncing = true
      
      console.log('🌐 Back online, syncing queued requests...')
      
      // Trigger sync
      offlineManager.syncQueuedRequests().then(results => {
        this.isSyncing = false
        this.updatePendingCount()
        console.log('✅ Sync complete:', results)
      }).catch(error => {
        this.isSyncing = false
        console.error('❌ Sync failed:', error)
      })
    },
    handleOffline() {
      this.isOnline = false
      console.log('📴 Gone offline')
    },
    updatePendingCount() {
      this.pendingCount = offlineManager.getQueueLength()
    }
  }
}
</script>

<style scoped>
.sync-status {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.sync-status.online {
  background-color: #d1fae5;
  color: #065f46;
  border: 1px solid #10b981;
}

.sync-status.offline {
  background-color: #fee2e2;
  color: #991b1b;
  border: 1px solid #ef4444;
}

.sync-status.syncing,
.sync-status.pending {
  background-color: #dbeafe;
  color: #1e40af;
  border: 1px solid #3b82f6;
  animation: pulse 2s infinite;
}

.status-icon {
  font-size: 1rem;
}

.status-text {
  white-space: nowrap;
}

.pending-count {
  font-size: 0.75rem;
  opacity: 0.8;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style>

