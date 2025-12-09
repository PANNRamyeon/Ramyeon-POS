// services/api.js
import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://pos.panntech/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
});

// Request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage or sessionStorage
    const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add timestamp to prevent caching issues
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      };
    }
    
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 Unauthorized errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Attempt to refresh token
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await axios.post(`${import.meta.env.VITE_API_URL}/auth/refresh/`, {
            refresh_token: refreshToken
          });
          
          const { access_token } = response.data;
          localStorage.setItem('authToken', access_token);
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        sessionStorage.removeItem('authToken');
        
        // Redirect to login page
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message);
      
      // Check if it's an offline scenario
      if (!navigator.onLine || error.code === 'ECONNABORTED') {
        // Import and use offline manager
        import('./offlineManager.js').then(({ default: offlineManager }) => {
          offlineManager.queueRequest(originalRequest)
        }).catch(err => {
          console.error('Failed to queue offline request:', err)
        })
        
        return Promise.reject({
          message: 'No internet connection. Request will be synced when online.',
          offline: true,
          originalRequest: originalRequest
        });
      }
    }
    
    // Handle other error status codes
    if (error.response) {
      switch (error.response.status) {
        case 400:
          console.error('Bad Request:', error.response.data);
          break;
        case 403:
          console.error('Forbidden:', error.response.data);
          break;
        case 404:
          // 404s are handled individually by API methods, no need to log here
          break;
        case 500:
          console.error('Server Error:', error.response.data);
          break;
        default:
          console.error('API Error:', error.response.data);
      }
    }
    
    return Promise.reject(error);
  }
);

// API Service Class
class ApiService {
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

  // AUTH METHODS
  async login(email, password, opening_cash = 0) {
    try {
      const payload = {
        email, 
        password,
        opening_cash: parseFloat(opening_cash) || 0  // ✅ Ensure it's a number
      };
      
      const response = await api.post('/auth/login/', payload);
      
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async logout(closingCash = 0) {
    try {
      const activeShiftId = localStorage.getItem('activeShiftId');
      if (activeShiftId) {
        await this.closeShift(activeShiftId, closingCash);
      }

      const response = await api.post('/auth/logout/', {
        closing_cash: closingCash
      });

      // 🧹 Clear tokens and shift data
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('activeShiftId');
      sessionStorage.removeItem('authToken');

      // 🧭 Redirect to login page
      window.location.href = '/login';

      return this.handleResponse(response);

    } catch (error) {
      this.handleError(error);
    }
  }

  async logoutSession() {
    try {
      const response = await api.post('/auth/logout/', {
        closing_cash: 0
      });

      // 🧹 Clear tokens and shift data
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('activeShiftId');
      localStorage.removeItem('userData');
      localStorage.removeItem('currentCartId');
      sessionStorage.removeItem('authToken');

      return this.handleResponse(response);

    } catch (error) {
      throw error;
    }
  }


  async refreshToken(refreshToken) {
    try {
      const response = await api.post('/auth/refresh/', { refresh_token: refreshToken });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getCurrentUser() {
    try {
      const response = await api.get('/auth/me/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async verifyToken(token) {
    try {
      const response = await api.post('/auth/verify-token/', { token });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // USER METHODS
  async getUsers() {
    try {
      const response = await api.get('/users/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getUser(userId) {
    try {
      const response = await api.get(`/users/${userId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async createUser(userData) {
    try {
      const response = await api.post('/users/', userData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async updateUser(userId, userData) {
    try {
      const response = await api.put(`/users/${userId}/`, userData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async deleteUser(userId) {
    try {
      const response = await api.delete(`/users/${userId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getUserByEmail(email) {
    try {
      const response = await api.get(`/users/email/${email}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getUserByUsername(username) {
    try {
      const response = await api.get(`/users/username/${username}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // CUSTOMER METHODS
  async getCustomers() {
    try {
      console.log('Making API call to get customers...');
      const response = await api.get('/customers/');
      console.log('Customers API response:', response);
      return this.handleResponse(response);
    } catch (error) {
      console.error('Error in getCustomers:', error);
      this.handleError(error);
    }
  }

  async getCustomer(customerId) {
    try {
      const response = await api.get(`/customers/${customerId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async createCustomer(customerData) {
    try {
      const response = await api.post('/customers/', customerData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async updateCustomer(customerId, customerData) {
    try {
      const response = await api.put(`/customers/${customerId}/`, customerData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async deleteCustomer(customerId) {
    try {
      const response = await api.delete(`/customers/${customerId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // SESSION METHODS
  async getActiveSessions() {
    try {
      const response = await api.get('/sessions/active/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getUserSessions(userId) {
    try {
      const response = await api.get(`/sessions/user/${userId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getSessionStatistics() {
    try {
      const response = await api.get('/sessions/statistics/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getSessionLogs() {
    try {
      const response = await api.get('/session-logs/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // SYSTEM METHODS
  async getSystemStatus() {
    try {
      const response = await api.get('/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async healthCheck() {
    try {
      const response = await api.get('/health/');
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  // SHIFT METHODS
  async startShift(cashierId, openingCash) {
    try {
      const response = await api.post('/pos/shifts/start/', {
        cashier_id: cashierId,
        opening_cash: openingCash
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getActiveShift(cashierId) {
    try {
      const response = await api.get('/pos/shifts/active/', {
        params: { cashier_id: cashierId }
      });
      return this.handleResponse(response);
    } catch (error) {
      // 404 is expected when no active shift exists - return null instead of throwing
      if (error.response?.status === 404) {
        return null;
      }
      this.handleError(error);
    }
  }

  async closeShift(shiftId, closingCash) {
    try {
      const response = await api.post(`/pos/shifts/${shiftId}/close/`, {
        closing_cash: closingCash
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getShiftById(shiftId) {
    try {
      const response = await api.get(`/pos/shifts/${shiftId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getShiftSales(shiftId) {
    try {
      const response = await api.get('/pos/sales/', {
        params: {
          shift_id: shiftId,
          limit: 1000
        }
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getShifts(filters = {}) {
    try {
      const response = await api.get('/pos/shifts/', {
        params: filters
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error);
    }
  }

}

// Create and export singleton instance
const apiService = new ApiService();

// Also export the axios instance for direct use if needed
export { api };
export default apiService;