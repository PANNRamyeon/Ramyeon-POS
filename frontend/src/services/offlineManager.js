// services/offlineManager.js
/**
 * Offline Manager
 * Handles request queuing and syncing when offline
 */

class OfflineManager {
  constructor() {
    this.queue = []
    this.maxQueueSize = 1000
    this.storageKey = 'offline_request_queue'
    this.loadQueue()
  }
  
  /**
   * Load queued requests from localStorage
   */
  loadQueue() {
    try {
      const stored = localStorage.getItem(this.storageKey)
      if (stored) {
        this.queue = JSON.parse(stored)
        console.log(`📦 Loaded ${this.queue.length} queued requests from storage`)
      }
    } catch (error) {
      console.error('❌ Failed to load offline queue:', error)
      this.queue = []
    }
  }
  
  /**
   * Save queued requests to localStorage
   */
  saveQueue() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.queue))
    } catch (error) {
      console.error('❌ Failed to save offline queue:', error)
    }
  }
  
  /**
   * Queue a request for later sync when online
   * @param {Object} requestConfig - Axios request config
   * @returns {Promise}
   */
  async queueRequest(requestConfig) {
    console.log('📴 Queuing request for offline sync:', requestConfig.url)
    
    const queueItem = {
      id: `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      config: requestConfig,
      timestamp: new Date().toISOString(),
      retries: 0
    }
    
    // Add to queue
    this.queue.push(queueItem)
    
    // Limit queue size
    if (this.queue.length > this.maxQueueSize) {
      console.warn('⚠️ Queue full, removing oldest items')
      this.queue = this.queue.slice(-this.maxQueueSize)
    }
    
    // Save to localStorage
    this.saveQueue()
    
    return Promise.resolve({
      offline: true,
      queued: true,
      queueId: queueItem.id,
      message: 'Request queued for sync when online'
    })
  }
  
  /**
   * Get queued requests count
   */
  getQueueLength() {
    return this.queue.length
  }
  
  /**
   * Process all queued requests when back online
   * @returns {Promise<Object>} Sync results
   */
  async syncQueuedRequests() {
    if (!navigator.onLine) {
      console.log('📴 Still offline, skipping sync')
      return { synced: 0, failed: 0, total: this.queue.length }
    }
    
    if (this.queue.length === 0) {
      console.log('✅ No queued requests to sync')
      return { synced: 0, failed: 0, total: 0 }
    }
    
    console.log(`🔄 Syncing ${this.queue.length} queued requests...`)
    
    const results = {
      synced: 0,
      failed: 0,
      total: this.queue.length
    }
    
    const remainingQueue = []
    
    for (const item of this.queue) {
      try {
        // Import axios dynamically to avoid circular dependencies
        const { api } = await import('./api.js')
        
        // Retry the original request
        await api(item.config)
        
        console.log(`✅ Synced queued request: ${item.config.url}`)
        results.synced++
        
      } catch (error) {
        console.error(`❌ Failed to sync queued request:`, error)
        
        // Increment retry count
        item.retries++
        
        // Keep in queue if retries < max
        if (item.retries < 3) {
          remainingQueue.push(item)
        } else {
          console.warn(`⚠️ Max retries reached for: ${item.config.url}`)
          results.failed++
        }
      }
    }
    
    // Update queue
    this.queue = remainingQueue
    this.saveQueue()
    
    console.log(`✅ Sync complete: ${results.synced} synced, ${results.failed} failed`)
    
    return results
  }
  
  /**
   * Clear the offline queue
   */
  clearQueue() {
    this.queue = []
    localStorage.removeItem(this.storageKey)
    console.log('🧹 Offline queue cleared')
  }
  
  /**
   * Get queue status
   */
  getQueueStatus() {
    return {
      length: this.queue.length,
      oldest: this.queue.length > 0 ? this.queue[0].timestamp : null,
      newest: this.queue.length > 0 ? this.queue[this.queue.length - 1].timestamp : null
    }
  }
}

// Export singleton instance
const offlineManager = new OfflineManager()
export default offlineManager

