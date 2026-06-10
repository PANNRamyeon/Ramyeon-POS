import { api } from './api.js';

class DashboardAPIService {
  handleResponse(response) {
    return response.data;
  }

  handleError(error) {
    const message = error.response?.data?.error ||
                   error.response?.data?.message ||
                   error.message ||
                   'An unexpected error occurred';
    throw new Error(message);
  }

  // ================================================================
  // DASHBOARD (comprehensive)
  // ================================================================

  async getDashboardData() {
    try {
      const response = await api.get('/pos/reports/dashboard/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // SALES SUMMARY (replaces daily-top-products, total-orders-revenue)
  // ================================================================

  async getSalesSummary(period = 'today') {
    try {
      const response = await api.get('/pos/reports/summary/', { params: { period } });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getDailyTopProducts(date = null, limit = 10) {
    try {
      // Map to sales summary — top products not a dedicated endpoint; use summary
      const params = { period: 'today', limit };
      if (date) params.date = date;
      const response = await api.get('/pos/reports/summary/', { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getTotalOrdersRevenue(startDate = null, endDate = null) {
    try {
      const params = { period: 'today' };
      if (startDate && endDate) {
        params.period = 'custom';
        params.start_date = startDate;
        params.end_date = endDate;
      }
      const response = await api.get('/pos/reports/summary/', { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // CATEGORY STATISTICS
  // ================================================================

  async getCategoryStatistics(period = 'week') {
    try {
      const response = await api.get('/admin/reports/top-categories/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // CUSTOM RANGE / PERIOD
  // ================================================================

  async getCustomRangeAnalytics(startDate, endDate) {
    try {
      const response = await api.get('/pos/reports/by-period/', {
        params: {
          start_date: startDate,
          end_date: endDate,
          period: 'daily'
        }
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // REAL-TIME / COMPARISON
  // ================================================================

  async getRealTimeSalesData() {
    try {
      const response = await api.get('/pos/reports/summary/', { params: { period: 'today' } });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getSalesComparison(period = 'week') {
    try {
      const response = await api.get('/pos/reports/comparison/', { params: { period } });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getProductPerformance(productId, days = 30) {
    try {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - days);
      const response = await api.get('/pos/reports/by-period/', {
        params: {
          start_date: start.toISOString(),
          end_date: end.toISOString(),
          period: 'daily'
        }
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // BATCH SNAPSHOT
  // ================================================================

  async getCompleteDashboardSnapshot() {
    try {
      const [dashboardData, salesSummary, categoryStats] = await Promise.all([
        this.getDashboardData(),
        this.getSalesSummary('today'),
        this.getCategoryStatistics('week')
      ]);

      return {
        dashboard: dashboardData,
        realTime: salesSummary,
        categories: categoryStats,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      this.handleError(error);
    }
  }

  // ================================================================
  // UTILITY
  // ================================================================

  formatDate(date) {
    return date.toISOString().split('T')[0];
  }

  formatDateTime(date) {
    return date.toISOString();
  }

  getDateRange(period) {
    const now = new Date();
    const start = new Date();

    switch (period) {
      case 'today':
        start.setHours(0, 0, 0, 0);
        return { start: this.formatDateTime(start), end: this.formatDateTime(now) };
      case 'yesterday':
        start.setDate(now.getDate() - 1);
        start.setHours(0, 0, 0, 0);
        const yesterdayEnd = new Date(start);
        yesterdayEnd.setHours(23, 59, 59, 999);
        return { start: this.formatDateTime(start), end: this.formatDateTime(yesterdayEnd) };
      case 'week':
        start.setDate(now.getDate() - 7);
        return { start: this.formatDateTime(start), end: this.formatDateTime(now) };
      case 'month':
        start.setMonth(now.getMonth() - 1);
        return { start: this.formatDateTime(start), end: this.formatDateTime(now) };
      default:
        return { start: this.formatDateTime(start), end: this.formatDateTime(now) };
    }
  }
}

const dashboardAPIService = new DashboardAPIService();
export default dashboardAPIService;
