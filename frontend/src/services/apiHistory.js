import { api } from './api.js';

class HistoryAPIService {
  // Helper method to handle responses
  handleResponse(response) {
    return response.data;
  }

  // Helper method to handle errors
  handleError(error) {
    const message = error.response?.data?.error || 
                   error.response?.data?.message || 
                   error.message || 
                   'An unexpected error occurred';
    throw new Error(message);
  }

  // Transform transaction data to match frontend component structure
  transformTransaction(transaction) {
    return {
      id: transaction._id,
      itemCount: transaction.items?.reduce((sum, item) => sum + item.quantity, 0) || 0,
      status: this.formatStatus(transaction.status),
      date: transaction.transaction_date || transaction.created_at,
      paymentMethod: this.formatPaymentMethod(transaction.payment_method),
      saleType: transaction.source === 'pos' ? 'POS' : 'Manual',
      total: transaction.total_amount,
      // Keep original data for modal details
      originalData: transaction
    };
  }

  // Format status to proper case
  formatStatus(status) {
    if (!status) return 'Unknown';
    const statusMap = {
      'completed': 'Completed',
      'pending': 'Pending',
      'voided': 'Cancelled',
      'cancelled': 'Cancelled',
      'refunded': 'Refunded'
    };
    return statusMap[status.toLowerCase()] || status.charAt(0).toUpperCase() + status.slice(1);
  }

  // Format payment method to proper case
  formatPaymentMethod(method) {
    if (!method) return 'Unknown';
    const methodMap = {
      'cash': 'Cash',
      'card': 'Card',
      'credit_card': 'Credit Card',
      'debit_card': 'Debit Card',
      'gcash': 'GCash',
      'paymaya': 'PayMaya'
    };
    return methodMap[method.toLowerCase()] || method.charAt(0).toUpperCase() + method.slice(1);
  }

  /**
   * Load transaction history with optional filters and pagination
   * Uses: GET /api/v1/pos/sales/
   */
  async loadHistory(params = {}) {
    try {
      const queryParams = new URLSearchParams({
        page: params.page || 1,
        page_size: params.pageSize || 20,
        ...(params.dateFrom && { date_from: params.dateFrom }),
        ...(params.dateTo && { date_to: params.dateTo }),
        ...(params.status && { status: params.status }),
        ...(params.paymentMethod && { payment_method: params.paymentMethod }),
        ...(params.cashierId && { cashier_id: params.cashierId }),
        ...(params.shiftId && { shift_id: params.shiftId }),
        ...(params.search && { search: params.search })
      });

      // ✅ CORRECT ENDPOINT
      const response = await api.get(`/pos/sales/?${queryParams}`);
      const data = this.handleResponse(response);

      // Handle paginated response
      if (data.data && data.pagination) {
        return {
          transactions: data.data.map(t => this.transformTransaction(t)),
          totalCount: data.pagination.total_count,
          currentPage: data.pagination.current_page,
          totalPages: data.pagination.total_pages
        };
      }

      // Handle non-paginated response
      const salesData = Array.isArray(data.data) ? data.data : data.data?.sales || [];
      return {
        transactions: salesData.map(t => this.transformTransaction(t)),
        totalCount: salesData.length,
        currentPage: params.page || 1,
        totalPages: Math.ceil(salesData.length / (params.pageSize || 20))
      };

    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Get single sale details
   * Uses: GET /api/v1/pos/sales/{sale_id}/
   */
  async getSaleDetails(saleId) {
    try {
      const response = await api.get(`/pos/sales/${saleId}/`);
      const data = this.handleResponse(response);
      return this.transformTransaction(data.data);
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Get daily sales summary
   * Uses: GET /api/v1/pos/sales/daily-summary/
   */
  async getDailySummary(date, cashierId = null) {
    try {
      const params = new URLSearchParams({
        date: date,
        ...(cashierId && { cashier_id: cashierId })
      });

      const response = await api.get(`/pos/sales/daily-summary/?${params}`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Export sales to CSV
   * Uses: GET /api/v1/pos/sales/export/
   */
  async exportToCSV(params = {}) {
    try {
      const queryParams = new URLSearchParams({
        ...(params.dateFrom && { date_from: params.dateFrom }),
        ...(params.dateTo && { date_to: params.dateTo }),
        ...(params.status && { status: params.status }),
        ...(params.cashierId && { cashier_id: params.cashierId })
      });

      const response = await api.get(`/pos/sales/export/?${queryParams}`, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sales_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      return { success: true };
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Void a sale (requires manager approval)
   * Uses: POST /api/v1/pos/sales/{sale_id}/void/
   */
  async voidSale(saleId, voidReason, managerId) {
    try {
      const response = await api.post(`/pos/sales/${saleId}/void/`, {
        void_reason: voidReason,
        manager_id: managerId
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Get receipt data
   * Uses: GET /api/v1/pos/sales/{sale_id}/receipt/
   */
  async getReceipt(saleId) {
    try {
      const response = await api.get(`/pos/sales/${saleId}/receipt/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }
}

// Create and export singleton instance
const historyAPIService = new HistoryAPIService();

export default historyAPIService;