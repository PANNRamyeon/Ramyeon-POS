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

  // Transform POS transaction data
  transformPOSTransaction(transaction) {
    return {
      id: transaction._id,
      itemCount: transaction.items?.reduce((sum, item) => sum + item.quantity, 0) || 0,
      status: this.formatStatus(transaction.status),
      date: transaction.transaction_date_local || transaction.transaction_date || transaction.created_at,
      paymentMethod: this.formatPaymentMethod(transaction.payment_method),
      saleType: 'POS',
      source: 'POS',
      total: transaction.total_amount,
      originalData: transaction
    };
  }

  // Transform Online order data
  transformOnlineOrder(order) {
    return {
      id: order._id,
      itemCount: order.items?.reduce((sum, item) => sum + item.quantity, 0) || 0,
      status: this.formatOnlineStatus(order.order_status),
      date: order.order_date || order.created_at,
      paymentMethod: this.formatPaymentMethod(order.payment_method),
      paymentStatus: this.formatPaymentStatus(order.payment_status),
      saleType: 'Online',
      source: 'Online',
      total: order.total_amount,
      customer: order.customer_id,
      deliveryAddress: order.delivery_address,
      originalData: order
    };
  }

  // Format status to proper case
  formatStatus(status) {
    if (!status) return 'Unknown';
    const statusMap = {
      'completed': 'Completed',
      'pending': 'Pending',
      'voided': 'Voided',
      'cancelled': 'Cancelled',
      'refunded': 'Refunded'
    };
    return statusMap[status.toLowerCase()] || status.charAt(0).toUpperCase() + status.slice(1);
  }

  // Format online order status
  formatOnlineStatus(status) {
    if (!status) return 'Unknown';
    const statusMap = {
      'pending': 'Pending',
      'confirmed': 'Confirmed',
      'processing': 'Processing',
      'on_the_way': 'On the Way',
      'completed': 'Completed',
      'cancelled': 'Cancelled'
    };
    return statusMap[status.toLowerCase()] || status.charAt(0).toUpperCase() + status.slice(1);
  }

  // Format payment status
  formatPaymentStatus(paymentStatus) {
    if (!paymentStatus) return 'Unknown';
    const statusMap = {
      'pending': 'Pending',
      'paid': 'Paid',
      'failed': 'Failed',
      'refunded': 'Refunded'
    };
    return statusMap[paymentStatus.toLowerCase()] || paymentStatus.charAt(0).toUpperCase() + paymentStatus.slice(1);
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
      'paymaya': 'PayMaya',
      'cod': 'Cash on Delivery',
      'bank_transfer': 'Bank Transfer'
    };
    return methodMap[method.toLowerCase()] || method.charAt(0).toUpperCase() + method.slice(1);
  }

  /**
   * Load ALL transaction history (POS + Online) with filters and pagination
   * Fetches from both endpoints and merges results
   */
  async loadHistory(params = {}) {
    try {
      this.loading = true;
      this.error = null;

      // Determine which sources to fetch based on filter
      const fetchPOS = !params.source || params.source === '' || params.source === 'POS';
      const fetchOnline = !params.source || params.source === '' || params.source === 'Online';

      let allTransactions = [];

      // Fetch POS transactions
      if (fetchPOS) {
        try {
          const posData = await this.fetchPOSTransactions(params);
          allTransactions = allTransactions.concat(posData);
        } catch (error) {
          console.warn('Error fetching POS transactions:', error);
        }
      }

      // Fetch Online orders
      if (fetchOnline) {
        try {
          const onlineData = await this.fetchOnlineOrders(params);
          allTransactions = allTransactions.concat(onlineData);
        } catch (error) {
          console.warn('Error fetching online orders:', error);
        }
      }

      // Apply client-side status filter (works for both POS and Online)
      if (params.status && params.status !== '') {
        const normalizeStatus = (txn) => {
          // Prefer raw status from original data if available
          const raw = (txn.originalData?.status || txn.originalData?.order_status || txn.status || '').toString().toLowerCase();
          return raw;
        };
        const wanted = params.status.toLowerCase();
        allTransactions = allTransactions.filter(txn => normalizeStatus(txn) === wanted);
      }

      // Apply client-side payment method filter
      if (params.paymentMethod && params.paymentMethod !== '') {
        const normalizeMethod = (txn) => {
          // Prefer raw method from original data if available
          const raw = (txn.originalData?.payment_method || txn.paymentMethod || '').toString().toLowerCase();
          return raw;
        };
        const wantedMethod = params.paymentMethod.toLowerCase();
        allTransactions = allTransactions.filter(txn => normalizeMethod(txn) === wantedMethod || normalizeMethod(txn).includes(wantedMethod));
      }

      // Sort by date (newest first)
      allTransactions.sort((a, b) => new Date(b.date) - new Date(a.date));

      // Apply client-side search filter if provided
      if (params.search && params.search.trim() !== '') {
        const searchTerm = params.search.toLowerCase();
        allTransactions = allTransactions.filter(txn => 
          txn.id.toLowerCase().includes(searchTerm)
        );
      }

      // Calculate pagination
      const page = params.page || 1;
      const pageSize = params.pageSize || 20;
      const totalCount = allTransactions.length;
      const totalPages = Math.ceil(totalCount / pageSize);
      
      // Paginate results
      const startIndex = (page - 1) * pageSize;
      const endIndex = startIndex + pageSize;
      const paginatedTransactions = allTransactions.slice(startIndex, endIndex);

      return {
        transactions: paginatedTransactions,
        totalCount: totalCount,
        currentPage: page,
        totalPages: totalPages
      };

    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Fetch POS transactions only
   */
  async fetchPOSTransactions(params = {}) {
    const queryParams = new URLSearchParams({
      limit: 1000, // Fetch large amount for client-side pagination
      ...(params.dateFrom && { start_date: params.dateFrom }),
      ...(params.dateTo && { end_date: params.dateTo }),
      ...(params.status && { status: params.status }),
      // payment_method is currently not supported by backend POS list; filter client-side
      ...(params.cashierId && { cashier_id: params.cashierId }),
      ...(params.shiftId && { shift_id: params.shiftId })
    });

    const response = await api.get(`/pos/sales/?${queryParams}`);
    const data = this.handleResponse(response);

    const salesData = data.data?.sales || data.data || [];
    return Array.isArray(salesData) 
      ? salesData.map(t => this.transformPOSTransaction(t))
      : [];
  }

  /**
   * Fetch Online orders only
   */
  async fetchOnlineOrders(params = {}) {
    const queryParams = new URLSearchParams({
      limit: 1000,
      ...(params.dateFrom && { start_date: params.dateFrom }),
      ...(params.dateTo && { end_date: params.dateTo }),
      ...(params.status && { status: params.status })
    });

    const response = await api.get(`/pos/orders/online/?${queryParams}`);
    const data = this.handleResponse(response);

    // Back office returns orders directly or wrapped in data/orders
    const ordersData = data.data?.orders || data.orders || data.data || (Array.isArray(data) ? data : []);
    return Array.isArray(ordersData)
      ? ordersData.map(o => this.transformOnlineOrder(o))
      : [];
  }

  /**
   * Get single transaction details (works for both POS and Online)
   */
  async getSaleDetails(saleId) {
    try {
      // Try POS first
      try {
        const response = await api.get(`/pos/sales/${saleId}/`);
        const data = this.handleResponse(response);
        return this.transformPOSTransaction(data.data);
      } catch (posError) {
        // If POS fails, try Online
        const response = await api.get(`/pos/orders/online/${saleId}/`);
        const data = this.handleResponse(response);
        return this.transformOnlineOrder(data.data?.order || data.data || data);
      }
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Get daily sales summary
   */
  async getDailySummary(date, cashierId = null) {
    try {
      const params = new URLSearchParams({ period: 'today' });
      if (cashierId) params.append('cashier_id', cashierId);

      const response = await api.get(`/pos/reports/summary/?${params}`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Export sales to CSV (POS + Online)
   */
  async exportToCSV(params = {}) {
    try {
      // Fetch all transactions
      const allData = await this.loadHistory({
        ...params,
        page: 1,
        pageSize: 10000 // Get all records
      });

      // Convert to CSV
      const csvContent = this.convertToCSV(allData.transactions);
      
      // Create download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `transactions_export_${new Date().toISOString().split('T')[0]}.csv`);
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
   * Convert transactions to CSV format
   */
  convertToCSV(transactions) {
    const headers = ['Transaction ID', 'Date', 'Type', 'Status', 'Payment Method', 'Items', 'Total'];
    const rows = transactions.map(txn => [
      txn.id,
      (() => {
        try {
          const date = new Date(txn.date)
          const datePart = date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            timeZone: 'Asia/Manila'
          })
          const timePart = date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: 'Asia/Manila'
          })
          return `${datePart} ${timePart}`
        } catch {
          return txn.date || 'N/A'
        }
      })(),
      txn.saleType,
      txn.status,
      txn.paymentMethod,
      txn.itemCount,
      txn.total
    ]);

    const csvRows = [headers, ...rows];
    return csvRows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
  }

  /**
   * Void a POS sale (requires manager approval)
   */
  async voidSale(saleId, voidReason, managerId) {
    try {
      const response = await api.post(`/pos/sales/${saleId}/void/`, {
        reason: voidReason,    
        manager_id: managerId
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Cancel an online order
   */
  async cancelOnlineOrder(orderId, cancellationReason, cancelledBy) {
    try {
      const response = await api.post(`/pos/orders/${orderId}/cancel/`, {
        cancellation_reason: cancellationReason,
        cancelled_by: cancelledBy
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Get receipt data (POS only)
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