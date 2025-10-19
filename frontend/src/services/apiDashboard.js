import { api } from './api.js';

class DashboardAPIService {
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

  // ================================================================
  // 1. DAILY TOP PRODUCTS
  // ================================================================

  async getDailyTopProducts(date = null, limit = 10) {
    try {
      const params = { limit };
      if (date) {
        params.date = date;
      }

      const response = await api.get('/pos/daily-top-products/', { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // 2. TOTAL ORDERS AND REVENUE
  // ================================================================

  async getTotalOrdersRevenue(startDate = null, endDate = null) {
    try {
      const params = {};
      if (startDate) {
        params.start_date = startDate;
      }
      if (endDate) {
        params.end_date = endDate;
      }

      const response = await api.get('/pos/total-orders-revenue/', { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // 3. CATEGORY STATISTICS
  // ================================================================

  async getCategoryStatistics(period = 'week') {
    try {
      const response = await api.get('/pos/category-statistics/', {
        params: { period }
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // 4. DASHBOARD DATA (Comprehensive)
  // ================================================================

  async getDashboardData() {
    try {
      const response = await api.get('/pos/dashboard/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // 5. CUSTOM RANGE ANALYTICS
  // ================================================================

  async getCustomRangeAnalytics(startDate, endDate) {
    try {
      const response = await api.get('/pos/custom-range/', {
        params: {
          start_date: startDate,
          end_date: endDate
        }
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // 6. REAL-TIME SALES DATA
  // ================================================================

  async getRealTimeSalesData() {
    try {
      const response = await api.get('/pos/real-time-sales/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // 7. PRODUCT PERFORMANCE
  // ================================================================

  async getProductPerformance(productId, days = 30) {
    try {
      const response = await api.get('/pos/product-performance/', {
        params: {
          product_id: productId,
          days: days
        }
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // 8. BATCH OPERATIONS (Multiple endpoints in one call)
  // ================================================================

  async getCompleteDashboardSnapshot() {
    try {
      // Get multiple data points in parallel for better performance
      const [dashboardData, realTimeData, categoryStats] = await Promise.all([
        this.getDashboardData(),
        this.getRealTimeSalesData(),
        this.getCategoryStatistics('week')
      ]);

      return {
        dashboard: dashboardData,
        realTime: realTimeData,
        categories: categoryStats,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // 9. UTILITY METHODS
  // ================================================================

  // Format date for API (YYYY-MM-DD)
  formatDate(date) {
    return date.toISOString().split('T')[0];
  }

  // Format datetime for API (ISO string)
  formatDateTime(date) {
    return date.toISOString();
  }

  // Get date range for common periods
  getDateRange(period) {
    const now = new Date();
    const start = new Date();

    switch (period) {
      case 'today':
        start.setHours(0, 0, 0, 0);
        return {
          start: this.formatDateTime(start),
          end: this.formatDateTime(now)
        };
      case 'yesterday':
        start.setDate(now.getDate() - 1);
        start.setHours(0, 0, 0, 0);
        const yesterdayEnd = new Date(start);
        yesterdayEnd.setHours(23, 59, 59, 999);
        return {
          start: this.formatDateTime(start),
          end: this.formatDateTime(yesterdayEnd)
        };
      case 'week':
        start.setDate(now.getDate() - 7);
        return {
          start: this.formatDateTime(start),
          end: this.formatDateTime(now)
        };
      case 'month':
        start.setMonth(now.getMonth() - 1);
        return {
          start: this.formatDateTime(start),
          end: this.formatDateTime(now)
        };
      default:
        return {
          start: this.formatDateTime(start),
          end: this.formatDateTime(now)
        };
    }
  }
}

// Create and export singleton instance
const dashboardAPIService = new DashboardAPIService();

export default dashboardAPIService;