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
    const transformed = {
      id: transaction._id,
      itemCount: transaction.items?.reduce((sum, item) => sum + item.quantity, 0) || 0,
      status: transaction.status?.charAt(0).toUpperCase() + transaction.status?.slice(1) || 'Unknown',
      date: transaction.transaction_date,
      paymentMethod: transaction.payment_method?.charAt(0).toUpperCase() + transaction.payment_method?.slice(1) || 'Unknown',
      saleType: 'In Store',
      total: transaction.total_amount || 0,
      originalData: transaction
    };
    return transformed;
  }

  // Load transaction history with optional filters and pagination
  async loadHistory(params = {}) {
    try {
      const queryParams = new URLSearchParams({
        page: params.page || 1,
        page_size: params.pageSize || 20,
        ...(params.dateFrom && { date_from: params.dateFrom }),
        ...(params.dateTo && { date_to: params.dateTo }),
        ...(params.status && { status: params.status }),
        ...(params.paymentMethod && { payment_method: params.paymentMethod }),
        ...(params.search && { search: params.search })
      });

      const response = await api.get(`/sales-report/transactions/?${queryParams}`);
      const data = this.handleResponse(response);

      return {
        transactions: data.transactions.map(this.transformTransaction),
        totalCount: data.total_count || data.transactions.length,
        currentPage: params.page || 1,
        totalPages: Math.ceil((data.total_count || data.transactions.length) / (params.pageSize || 20))
      };

    } catch (error) {
      this.handleError(error);
    }
  }
  

}

// Create and export singleton instance
const historyAPIService = new HistoryAPIService();

export default historyAPIService;