// services/api.js
import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
});

// Offline Queue Management
const OfflineQueue = {
  getQueue() {
    try {
      return JSON.parse(localStorage.getItem('offlineRequestQueue') || '[]');
    } catch {
      return [];
    }
  },

  addToQueue(config, data) {
    const queue = this.getQueue();
    const requestId = `offline-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const queuedRequest = {
      id: requestId,
      method: config.method,
      url: config.url,
      data: data,
      timestamp: new Date().toISOString(),
      attempts: 0,
      headers: config.headers
    };
    
    queue.push(queuedRequest);
    localStorage.setItem('offlineRequestQueue', JSON.stringify(queue));
    
    console.log('📦 Request queued for offline sync:', config.method, config.url);
    return requestId;
  },

  removeFromQueue(requestId) {
    const queue = this.getQueue();
    const updatedQueue = queue.filter(req => req.id !== requestId);
    localStorage.setItem('offlineRequestQueue', JSON.stringify(updatedQueue));
  },

  async processQueue() {
    if (!navigator.onLine) return { success: 0, failed: 0 };
    
    const queue = this.getQueue();
    if (queue.length === 0) return { success: 0, failed: 0 };
    
    console.log('🔄 Processing offline queue:', queue.length, 'requests');
    
    let successCount = 0;
    let failedCount = 0;
    
    for (const request of queue) {
      try {
        request.attempts++;
        
        // Execute the original request
        await api({
          method: request.method,
          url: request.url,
          data: request.data,
          headers: request.headers
        });
        
        this.removeFromQueue(request.id);
        successCount++;
        console.log('✅ Synced queued request:', request.method, request.url);
        
      } catch (error) {
        console.error('❌ Failed to sync request:', request.url, error);
        failedCount++;
        
        // Remove if too many attempts
        if (request.attempts >= 3) {
          this.removeFromQueue(request.id);
          console.warn('🚮 Removing request after 3 failed attempts:', request.url);
        }
      }
    }
    
    if (successCount > 0) {
      console.log(`✅ Successfully synced ${successCount} requests`);
    }
    
    return { success: successCount, failed: failedCount };
  }
};

// Data Caching System
const DataCache = {
  set(key, data, ttlMinutes = 30) {
    const cache = {
      data: data,
      timestamp: Date.now(),
      expiresAt: Date.now() + (ttlMinutes * 60 * 1000)
    };
    try {
      localStorage.setItem(`cache_${key}`, JSON.stringify(cache));
      return true;
    } catch (error) {
      console.error('❌ Cache set failed:', error);
      return false;
    }
  },

  get(key) {
    try {
      const cache = JSON.parse(localStorage.getItem(`cache_${key}`));
      if (cache && cache.expiresAt > Date.now()) {
        return cache.data;
      }
      // Remove expired cache
      localStorage.removeItem(`cache_${key}`);
      return null;
    } catch {
      return null;
    }
  },

  remove(key) {
    localStorage.removeItem(`cache_${key}`);
  },

  clearExpired() {
    const keys = Object.keys(localStorage).filter(key => key.startsWith('cache_'));
    keys.forEach(key => {
      this.get(key.replace('cache_', '')); // This will remove expired ones
    });
  }
};

// Request interceptor for authentication and offline handling
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
    
    // Mark if offline
    if (!navigator.onLine) {
      config._offline = true;
    }
    
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and offline sync
api.interceptors.response.use(
  (response) => {
    // If we're back online and have queued requests, trigger sync in background
    if (navigator.onLine) {
      setTimeout(() => {
        OfflineQueue.processQueue();
      }, 1000);
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Handle offline scenario
    if (!error.response && !navigator.onLine) {
      console.log('🔌 OFFLINE: No connection available');
      
      // If it's a GET request, try to return cached data
      if (originalRequest.method === 'get') {
        const cacheKey = originalRequest.url.replace(api.defaults.baseURL, '').replace(/\//g, '_');
        const cachedData = DataCache.get(cacheKey);
        if (cachedData) {
          console.log('📦 OFFLINE: Returning cached data for', originalRequest.url);
          return Promise.resolve({
            data: cachedData,
            status: 200,
            statusText: 'OK (Cached)',
            headers: {},
            config: originalRequest,
            offline: true
          });
        }
      } else if (originalRequest.method !== 'get') {
        // Queue non-GET requests for later sync
        const requestId = OfflineQueue.addToQueue(originalRequest, error.config?.data);
        return Promise.reject({
          message: 'Request queued for offline sync',
          offline: true,
          queued: true,
          requestId: requestId
        });
      }
      
      return Promise.reject({
        message: 'No internet connection',
        offline: true,
        config: originalRequest
      });
    }
    
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
      if (!navigator.onLine) {
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
          console.error('Not Found:', error.response.data);
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
  constructor() {
    this.syncInterval = null;
  }

  // Helper method to handle responses
  handleResponse(response) {
    // Cache successful GET responses
    if (response.config?.method === 'get' && response.config.url && !response.offline) {
      const cacheKey = response.config.url.replace(api.defaults.baseURL, '').replace(/\//g, '_');
      DataCache.set(cacheKey, response.data);
    }
    return response.data;
  }

  // Helper method to handle errors
  handleError(error) {
    const message = error.response?.data?.error || 
                   error.response?.data?.message || 
                   error.message || 
                   'An unexpected error occurred';
    
    // Don't throw for queued offline requests
    if (error.queued) {
      return { queued: true, requestId: error.requestId, message };
    }
    
    throw new Error(message);
  }

  // ================================================================
  // EMPLOYEE DATA CACHING FOR OFFLINE AUTHENTICATION
  // ================================================================

  async cacheEmployees(employees) {
    try {
      console.log('🔧 Starting employee cache process...');
      
      if (!employees || !Array.isArray(employees)) {
        console.warn('⚠️ Invalid employees data:', employees);
        return false;
      }

      console.log(`📥 ${employees.length} employees to cache:`, employees.map(e => ({
        email: e.email,
        role: e.role,
        status: e.status
      })));

      const cacheData = {
        employees: employees,
        cachedAt: new Date().toISOString(),
        count: employees.length,
        source: 'users_api'
      };
      
      localStorage.setItem('cachedEmployees', JSON.stringify(cacheData));
      console.log(`✅ Cached ${employees.length} employees for offline use`);
      
      // Verify the cache was saved
      const verifyCache = this.getCachedEmployees();
      console.log('🔍 Cache verification:', verifyCache ? `${verifyCache.length} employees` : 'No cache found');
      
      if (verifyCache) {
        console.log('📋 Cached employee emails:', verifyCache.map(e => e.email));
      }
      
      return true;
    } catch (error) {
      console.error('❌ Failed to cache employees:', error);
      return false;
    }
  }

  getCachedEmployees() {
    try {
      const cached = localStorage.getItem('cachedEmployees');
      if (!cached) return null;
      
      const data = JSON.parse(cached);
      // Check if cache is still valid (24 hours)
      const cacheTime = new Date(data.cachedAt).getTime();
      const currentTime = new Date().getTime();
      const cacheAge = currentTime - cacheTime;
      
      if (cacheAge > 24 * 60 * 60 * 1000) { // 24 hours
        console.log('🔄 Employee cache expired');
        localStorage.removeItem('cachedEmployees');
        return null;
      }
      
      return data.employees;
    } catch (error) {
      console.error('❌ Error getting cached employees:', error);
      return null;
    }
  }

  // ================================================================
  // OFFLINE AUTHENTICATION METHODS
  // ================================================================

  async offlineLogin(email, password, openingCash = 0) {
    try {
      console.log('🔌 OFFLINE MODE: Attempting offline login');
      
      // Check if we have cached employee data
      const cachedEmployees = this.getCachedEmployees();
      
      if (!cachedEmployees || cachedEmployees.length === 0) {
        throw new Error('No cached employee data available offline. Please login online first.');
      }

      // Find employee by email in cached data
      const employee = cachedEmployees.find(emp => 
        emp.email.toLowerCase() === email.toLowerCase() && 
        emp.role === 'employee' && 
        emp.status === 'active' &&
        emp.isDeleted !== true
      );

      if (!employee) {
        throw new Error('Employee not found or inactive in cached data');
      }

      console.log('✅ OFFLINE MODE: Employee found, proceeding with offline login');

      // Generate offline token and shift
      const offlineToken = this.generateOfflineToken();
      const offlineShift = await this.createOfflineShift(employee._id, employee, openingCash);
      
      // Store offline session
      const offlineSession = {
        user: {
          _id: employee._id,
          username: employee.username,
          email: employee.email,
          full_name: employee.full_name,
          role: employee.role,
          status: employee.status
        },
        token: offlineToken,
        shift: offlineShift,
        loggedInAt: new Date().toISOString(),
        offline: true
      };

      localStorage.setItem('offlineSession', JSON.stringify(offlineSession));

      return {
        success: true,
        offline: true,
        user: offlineSession.user,
        token: offlineToken,
        shift: offlineShift,
        message: 'Logged in offline successfully'
      };
      
    } catch (error) {
      console.error('❌ OFFLINE MODE: Login failed:', error);
      throw error;
    }
  }

  async createOfflineShift(userId, employeeData, openingCash) {
    const shiftId = `OFFLINE-SHIFT-${Date.now()}`;
    const shift = {
      _id: shiftId,
      shift_id: shiftId,
      cashier_id: userId,
      cashier_info: {
        _id: employeeData._id,
        username: employeeData.username,
        email: employeeData.email,
        full_name: employeeData.full_name,
        role: employeeData.role
      },
      opening_cash: parseFloat(openingCash) || 0,
      opening_time: new Date().toISOString(),
      status: 'active',
      offline: true,
      sales: [],
      total_sales: 0,
      total_cash: parseFloat(openingCash) || 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    // Store offline shift
    localStorage.setItem('activeOfflineShift', JSON.stringify(shift));
    localStorage.setItem('activeShiftId', shiftId);
    
    console.log('✅ Offline shift created:', shiftId);
    return shift;
  }

  getActiveOfflineShift() {
    try {
      const shift = localStorage.getItem('activeOfflineShift');
      return shift ? JSON.parse(shift) : null;
    } catch {
      return null;
    }
  }

  async cacheUserCredentials(userData, password) {
    try {
      const credentials = {
        email: userData.email,
        userId: userData.id || userData._id,
        userData: userData,
        password: password, // In production, hash this properly
        cachedAt: new Date().toISOString()
      };
      
      localStorage.setItem('offlineCredentials', JSON.stringify(credentials));
      console.log('✅ User credentials cached for offline use');
    } catch (error) {
      console.error('❌ Failed to cache credentials:', error);
    }
  }

  getCachedCredentials() {
    try {
      const cached = localStorage.getItem('offlineCredentials');
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      return null;
    }
  }

  getOfflineSession() {
    try {
      const session = localStorage.getItem('offlineSession');
      return session ? JSON.parse(session) : null;
    } catch {
      return null;
    }
  }

  clearOfflineSession() {
    localStorage.removeItem('offlineSession');
    localStorage.removeItem('activeOfflineShift');
    localStorage.removeItem('activeShiftId');
  }

  generateOfflineToken() {
    return `offline-token-${Date.now()}-${Math.random().toString(36).substr(2)}`;
  }

  // ================================================================
  // QUEUE MANAGEMENT METHODS
  // ================================================================

  async processOfflineQueue() {
    return await OfflineQueue.processQueue();
  }

  getQueuedRequests() {
    return OfflineQueue.getQueue();
  }

  clearQueue() {
    localStorage.setItem('offlineRequestQueue', '[]');
  }

  // ================================================================
  // DATA CACHING METHODS
  // ================================================================

  async cacheProducts(products) {
    return DataCache.set('products', products, 30); // 30 minutes
  }

  getCachedProducts() {
    return DataCache.get('products');
  }

  async cacheCategories(categories) {
    return DataCache.set('categories', categories, 60); // 60 minutes
  }

  getCachedCategories() {
    return DataCache.get('categories');
  }

  async cacheCustomers(customers) {
    return DataCache.set('customers', customers, 60); // 60 minutes
  }

  getCachedCustomers() {
    return DataCache.get('customers');
  }

  clearAllCache() {
    DataCache.clearExpired();
  }

  // ================================================================
  // CONNECTIVITY METHODS
  // ================================================================

  isOnline() {
    return navigator.onLine;
  }

  onConnectionChange(callback) {
    window.addEventListener('online', () => callback(true));
    window.addEventListener('offline', () => callback(false));
  }

  // ================================================================
  // BACKGROUND SYNC & DATA PRELOADING
  // ================================================================

  async preloadOfflineData() {
    if (!this.isOnline()) return;
    
    try {
      console.log('🔄 Preloading offline data...');
      
      // Preload employees data with proper filtering
      try {
        const usersResponse = await api.get('/users/');
        console.log('📋 Raw Users API Response:', usersResponse.data);
        
        if (usersResponse.data && usersResponse.data.users) {
          const users = usersResponse.data.users;
          console.log(`📊 Found ${users.length} total users`);
          
          // Filter for active employees - FIXED FILTER
          const activeEmployees = users.filter(user => {
            const isEmployee = user.role === 'employee';
            const isActive = user.status === 'active';
            const notDeleted = user.isDeleted !== true;
            
            console.log(`👤 User ${user.email}:`, {
              role: user.role,
              status: user.status, 
              isDeleted: user.isDeleted,
              passes: isEmployee && isActive && notDeleted
            });
            
            return isEmployee && isActive && notDeleted;
          });
          
          console.log(`👨‍💼 Found ${activeEmployees.length} active employees after filtering`);
          
          if (activeEmployees.length > 0) {
            await this.cacheEmployees(activeEmployees);
            console.log(`✅ Cached ${activeEmployees.length} employees for offline use`);
            
            // Log the cached employees for verification
            const cached = this.getCachedEmployees();
            console.log('🔍 Cached employees:', cached);
          } else {
            console.warn('⚠️ No active employees found to cache');
            
            // Debug: Check what users we have
            const userRoles = users.map(u => ({ 
              email: u.email, 
              role: u.role, 
              status: u.status,
              isDeleted: u.isDeleted 
            }));
            console.log('📝 All users roles:', userRoles);
          }
        } else {
          console.warn('⚠️ No users data in response:', usersResponse.data);
        }
      } catch (error) {
        console.warn('⚠️ Could not preload users:', error.message);
      }
      
      console.log('✅ Offline data preload completed');
    } catch (error) {
      console.error('❌ Failed to preload offline data:', error);
    }
  }

  startBackgroundSync(intervalMinutes = 30) {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    
    this.syncInterval = setInterval(async () => {
      if (this.isOnline()) {
        console.log('🔄 Background sync running...');
        await this.processOfflineQueue();
        
        // Refresh critical data
        try {
          await this.getProductsWithCache();
          await this.getCategoriesWithCache();
        } catch (error) {
          console.log('Background data refresh failed:', error);
        }
      }
    }, intervalMinutes * 60 * 1000);
  }

  stopBackgroundSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  // ================================================================
  // ENHANCED API METHODS WITH OFFLINE SUPPORT
  // ================================================================

  async getProductsWithCache() {
    // Try to return cached data first when offline
    if (!this.isOnline()) {
      const cached = this.getCachedProducts();
      if (cached) {
        console.log('📦 Returning cached products (offline)');
        return cached;
      }
      throw new Error('No cached products available offline');
    }
    
    // Online: fetch fresh data and cache it
    try {
      // Use your existing products endpoint
      const response = await api.get('/products/');
      await this.cacheProducts(response.data);
      return this.handleResponse(response);
    } catch (error) {
      // Fallback to cache even when online if request fails
      const cached = this.getCachedProducts();
      if (cached) {
        console.warn('⚠️ Using cached products due to API error');
        return cached;
      }
      this.handleError(error);
    }
  }

  async getCategoriesWithCache() {
    if (!this.isOnline()) {
      const cached = this.getCachedCategories();
      if (cached) {
        console.log('📦 Returning cached categories (offline)');
        return cached;
      }
      // Return empty array instead of throwing error
      return [];
    }
    
    try {
      // Use the correct endpoint: /category/display/ instead of /categories/
      const response = await api.get('/category/display/');
      await this.cacheCategories(response.data);
      return this.handleResponse(response);
    } catch (error) {
      // If endpoint doesn't exist, return empty array
      if (error.response?.status === 404) {
        console.log('ℹ️ Categories endpoint not available, returning empty array');
        return [];
      }
      
      const cached = this.getCachedCategories();
      if (cached) {
        console.warn('⚠️ Using cached categories due to API error');
        return cached;
      }
      // Return empty array instead of throwing
      return [];
    }
  }


  async getCustomersWithCache() {
    if (!this.isOnline()) {
      const cached = this.getCachedCustomers();
      if (cached) {
        console.log('📦 Returning cached customers (offline)');
        return cached;
      }
      throw new Error('No cached customers available offline');
    }
    
    try {
      const response = await api.get('/customers/');
      await this.cacheCustomers(response.data);
      return this.handleResponse(response);
    } catch (error) {
      const cached = this.getCachedCustomers();
      if (cached) {
        console.warn('⚠️ Using cached customers due to API error');
        return cached;
      }
      this.handleError(error);
    }
  }

  // ================================================================
  // AUTH METHODS (Enhanced)
  // ================================================================

  async login(email, password, opening_cash = 0) {
    try {
      console.log('📤 API: Sending login request');
      console.log('   Email:', email);
      console.log('   Opening Cash:', opening_cash);
      
      const payload = {
        email, 
        password,
        opening_cash: parseFloat(opening_cash) || 0
      };
      
      console.log('📤 API: Final payload:', payload);
      
      const response = await api.post('/auth/login/', payload);
      
      console.log('✅ API: Login response:', response.data);
      
      // Cache user credentials for offline use
      if (response.data.user) {
        await this.cacheUserCredentials(response.data.user, password);
      }
      
      // Pre-cache employees data for offline use
      try {
        const employeesResponse = await api.get('/users/');
        if (employeesResponse.data && employeesResponse.data.users) {
          await this.cacheEmployees(employeesResponse.data.users);
        }
      } catch (cacheError) {
        console.warn('⚠️ Could not cache employees data:', cacheError);
      }
      
      return this.handleResponse(response);
    } catch (error) {
      // If online login fails and we're offline, try offline login
      if (!this.isOnline()) {
        console.log('🔌 Online login failed, attempting offline login...');
        return await this.offlineLogin(email, password, opening_cash);
      }
      this.handleError(error);
    }
  }

  async logout(closingCash = 0) {
    try {
      console.log('📤 Logging out with closing cash:', closingCash);
      
      // Handle offline session cleanup
      const offlineSession = this.getOfflineSession();
      if (offlineSession) {
        console.log('🔌 Cleaning up offline session');
        
        // Close offline shift if exists
        const activeOfflineShift = this.getActiveOfflineShift();
        if (activeOfflineShift) {
          console.log('🔌 Closing offline shift:', activeOfflineShift._id);
          // Queue shift closure for sync when online
          OfflineQueue.addToQueue(
            { method: 'post', url: `/pos/shifts/${activeOfflineShift._id}/close/` },
            { closing_cash: closingCash }
          );
        }
        
        this.clearOfflineSession();
      }
      
      // Get active shift ID from localStorage
      const activeShiftId = localStorage.getItem('activeShiftId');
      
      // If there's an active shift, close it first
      if (activeShiftId && !activeShiftId.startsWith('OFFLINE-')) {
        console.log('   Closing active shift:', activeShiftId);
        await this.closeShift(activeShiftId, closingCash);
      }
      
      // Then call logout endpoint
      const response = await api.post('/auth/logout/', {
        closing_cash: closingCash
      });
      
      console.log('✅ Logout successful');
      return this.handleResponse(response);
      
    } catch (error) {
      console.error('❌ Logout failed:', error);
      
      // Even if API call fails, clear local session
      this.clearOfflineSession();
      localStorage.removeItem('authToken');
      localStorage.removeItem('userData');
      localStorage.removeItem('activeShiftId');
      
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
      // Check for offline session first
      if (!this.isOnline()) {
        const offlineSession = this.getOfflineSession();
        if (offlineSession) {
          return offlineSession.user;
        }
        throw new Error('No active session available offline');
      }
      
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

  // ================================================================
  // USER METHODS
  // ================================================================

  async getUsers() {
    try {
      const response = await api.get('/users/');
      
      // Cache employees for offline use
      if (response.data && response.data.users) {
        await this.cacheEmployees(response.data.users);
      }
      
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

  // ================================================================
  // CUSTOMER METHODS
  // ================================================================

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

  // ================================================================
  // SESSION METHODS
  // ================================================================

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

  // ================================================================
  // SYSTEM METHODS
  // ================================================================

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

  // ================================================================
  // SHIFT METHODS
  // ================================================================

  async startShift(cashierId, openingCash) {
    try {
      console.log('📤 Starting shift:', { cashierId, openingCash });
      
      // If offline, create offline shift
      if (!this.isOnline()) {
        console.log('🔌 OFFLINE: Creating offline shift');
        
        // Get employee data from cache
        const cachedEmployees = this.getCachedEmployees();
        const employee = cachedEmployees?.find(emp => emp._id === cashierId);
        
        if (!employee) {
          throw new Error('Employee data not found in cache for offline shift');
        }
        
        return await this.createOfflineShift(cashierId, employee, openingCash);
      }
      
      const response = await api.post('/pos/shifts/start/', {
        cashier_id: cashierId,
        opening_cash: openingCash
      });
      console.log('✅ Shift started:', response.data);
      return this.handleResponse(response);
    } catch (error) {
      console.error('❌ Start shift failed:', error);
      this.handleError(error);
    }
  }

  async getActiveShift(cashierId) {
    try {
      console.log('📤 Getting active shift for:', cashierId);
      
      // If offline, return offline shift
      if (!this.isOnline()) {
        const offlineShift = this.getActiveOfflineShift();
        if (offlineShift) {
          console.log('🔌 OFFLINE: Returning offline shift');
          return offlineShift;
        }
        throw new Error('No active shift available offline');
      }
      
      const response = await api.get('/pos/shifts/active/', {
        params: { cashier_id: cashierId }
      });
      console.log('✅ Active shift:', response.data);
      return this.handleResponse(response);
    } catch (error) {
      console.error('❌ Get active shift failed:', error);
      this.handleError(error);
    }
  }

  async closeShift(shiftId, closingCash) {
    try {
      console.log('📤 Closing shift:', { shiftId, closingCash });
      
      // Handle offline shift closure
      if (shiftId.startsWith('OFFLINE-SHIFT-')) {
        console.log('🔌 OFFLINE: Closing offline shift locally');
        const shift = this.getActiveOfflineShift();
        if (shift) {
          shift.closing_cash = closingCash;
          shift.closing_time = new Date().toISOString();
          shift.status = 'closed';
          
          // For offline shifts, we don't sync the closure - just close locally
          // The individual sales will be synced instead
          console.log('✅ Offline shift closed locally - sales will sync individually');
          
          this.clearOfflineSession();
          
          return { 
            ...shift, 
            message: 'Offline shift closed. Sales will sync when online.'
          };
        }
      }
      
      // ONLINE shift closure
      const response = await api.post(`/pos/shifts/${shiftId}/close/`, {
        closing_cash: closingCash
      });
      console.log('✅ Shift closed:', response.data);
      return this.handleResponse(response);
    } catch (error) {
      console.error('❌ Close shift failed:', error);
      
      // If closing fails, still clear the local session
      if (shiftId.startsWith('OFFLINE-SHIFT-')) {
        this.clearOfflineSession();
        return {
          success: true,
          message: 'Offline shift cleared locally despite sync error'
        };
      }
      
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

  // ================================================================
  // INITIALIZATION
  // ================================================================

  initialize() {
    // Start background sync
    this.startBackgroundSync();
    
    // Set up connection monitoring
    this.onConnectionChange((online) => {
      if (online) {
        console.log('🌐 Connection restored - starting sync and preloading data');
        this.processOfflineQueue();
        this.preloadOfflineData();
      } else {
        console.log('🔌 Connection lost - entering offline mode');
      }
    });
    
    // Preload data on startup if online
    if (this.isOnline()) {
      setTimeout(() => this.preloadOfflineData(), 2000);
    }
    
    // Clear expired cache on startup
    this.clearAllCache();
    
    console.log('✅ Offline-First API Service initialized');
  }
}

// Create and export singleton instance
const apiService = new ApiService();

// Initialize the service
apiService.initialize();

// Also export the axios instance for direct use if needed
export { api, OfflineQueue, DataCache };
export default apiService;