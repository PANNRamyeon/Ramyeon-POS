// src/services/apiSales.js
import { api } from './api.js';

class SalesAPIService {
  
  // ================================================================
  // HELPER: Extract data from standard response format
  // ================================================================
  
  extractData(response, errorContext = 'Operation') {
    if (!response.data) {
      throw new Error(`${errorContext} failed: No response data`);
    }
    
    if (response.data.success === false) {
      throw new Error(response.data.message || response.data.error || `${errorContext} failed`);
    }
    
    if (response.data.data) {
      return response.data.data;
    }
    
    return response.data;
  }
  
  // ================================================================
  // SALE CREATION
  // ================================================================
  
    /**
   * Create a new POS sale
   * @param {Object} saleData - Complete sale data including payment details
   * @returns {Object} Created sale with sale_id
   */
  async createSale(saleData) {
    try {
      console.log('💳 API: Creating sale...', saleData)
      
      // ✅ Validate required fields
      if (!saleData.payment_method) {
        throw new Error('Payment method is required')
      }
      
      if (!saleData.cashier_id) {
        throw new Error('Cashier ID is required')
      }
      
      console.log('👤 Cashier ID:', saleData.cashier_id)
      console.log('⏰ Shift ID:', saleData.shift_id)
      console.log('💳 Payment method:', saleData.payment_method)
      
      // ✅ Send saleData as-is (it already has everything)
      const payload = saleData
      
      console.log('📤 Sending payload:', payload)
      
      const response = await api.post('/pos/sales/create/', payload)
      
      console.log('✅ Sale created:', response.data)
      
      // Extract sale data
      if (response.data.success && response.data.data) {
        return response.data.data
      }
      
      // Fallback if response format is different
      return response.data
      
    } catch (error) {
      console.error('❌ Create sale failed:', error)
      
      let errorMessage = 'Failed to create sale'
      
      if (error.response?.data) {
        errorMessage = error.response.data.error || 
                      error.response.data.message || 
                      errorMessage
      } else {
        errorMessage = error.message
      }
      
      throw new Error(errorMessage)
    }
  }
  
  // ================================================================
  // SALE RETRIEVAL
  // ================================================================
  
  /**
   * Get sale by ID
   */
  async getSaleById(saleId) {
    try {
      const response = await api.get(`/pos/sales/${saleId}/`);
      return this.extractData(response, 'Get sale');
    } catch (error) {
      console.error('❌ Get sale failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }
  
  /**
   * Get receipt data for printing
   */
  async getReceipt(saleId) {
    try {
      console.log('🧾 API: Fetching receipt for sale:', saleId);
      
      const response = await api.get(`/pos/sales/${saleId}/receipt/`);
      
      console.log('✅ Receipt data received:', response.data);
      
      return this.extractData(response, 'Get receipt');
      
    } catch (error) {
      console.error('❌ Get receipt failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }
  
  // ================================================================
  // SALE MANAGEMENT
  // ================================================================
  
  /**
   * Void a sale (requires manager approval)
   */
  async voidSale(saleId, reason, managerId) {
    try {
      const response = await api.post(`/pos/sales/${saleId}/void/`, {
        reason,
        manager_id: managerId
      });
      
      return this.extractData(response, 'Void sale');
      
    } catch (error) {
      console.error('❌ Void sale failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }
  
  // ================================================================
  // REPORTS
  // ================================================================
  
  /**
   * Get sales list with filters
   */
  async getSalesList(filters = {}) {
    try {
      const params = new URLSearchParams();
      
      if (filters.startDate) params.append('start_date', filters.startDate);
      if (filters.endDate) params.append('end_date', filters.endDate);
      if (filters.cashierId) params.append('cashier_id', filters.cashierId);
      if (filters.shiftId) params.append('shift_id', filters.shiftId);
      if (filters.status) params.append('status', filters.status);
      if (filters.limit) params.append('limit', filters.limit);
      
      const response = await api.get(`/pos/sales/?${params.toString()}`);
      return this.extractData(response, 'Get sales list');
      
    } catch (error) {
      console.error('❌ Get sales list failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }
  
  /**
   * Get daily summary
   */
  async getDailySummary(date, cashierId = null) {
    try {
      const params = new URLSearchParams({ date });
      if (cashierId) params.append('cashier_id', cashierId);
      
      const response = await api.get(`/pos/sales/daily-summary/?${params.toString()}`);
      return this.extractData(response, 'Get daily summary');
      
    } catch (error) {
      console.error('❌ Get daily summary failed:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }
}

export default new SalesAPIService();