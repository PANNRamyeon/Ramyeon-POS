import { api } from './api.js';

class SyncAPIService {
  /**
   * Trigger startup sync (same as server startup)
   * Syncs products, batches, and updates stock levels
   */
  async triggerStartupSync() {
    try {
      const response = await api.post('/api/v1/sync/trigger-startup/');
      return response.data;
    } catch (error) {
      console.error('Trigger startup sync error:', error);
      throw error;
    }
  }

  /**
   * Get sync status
   */
  async getSyncStatus() {
    try {
      const response = await api.get('/api/v1/sync/status/');
      return response.data;
    } catch (error) {
      console.error('Get sync status error:', error);
      throw error;
    }
  }
}

export default new SyncAPIService();



