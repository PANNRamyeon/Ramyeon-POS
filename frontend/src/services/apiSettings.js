import { api } from './api.js';

class SettingsAPIService {
  // Helper method to handle errors
  handleError(error) {
    const message = error.response?.data?.error || 
                   error.response?.data?.message || 
                   error.message || 
                   'An unexpected error occurred';
    throw new Error(message);
  }

  async getCurrentUser() {
    try {
      const response = await api.get('/pos/auth/me/');
      const userData = response.data;
      
      // Transform the response to match your frontend needs
      return {
        id: userData.user_id,
        email: userData.email,
        role: userData.role,
        username: userData.user_data?.username || '',
        full_name: userData.user_data?.full_name || '',
        status: userData.user_data?.status || 'active',
        date_created: userData.user_data?.date_created,
        last_updated: userData.user_data?.last_updated
      };
      
    } catch (error) {
      console.error('Error fetching current user:', error);
      this.handleError(error);
    }
  }

  async updateUser(userId, userData) {
    try {
      const response = await api.put(`/admin/users/${userId}/`, userData);

      return { 
        success: true, 
        message: response.data.message || 'User updated successfully',
        data: response.data 
      };
      
    } catch (error) {
      console.error('Error updating user:', error);
      this.handleError(error);
    }
  }

  async verifyToken() {
    try {
      const response = await api.post('/pos/auth/verify/');
      return response.data;
      
    } catch (error) {
      console.error('Error verifying token:', error);
      this.handleError(error);
    }
  }

  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token found');
      }

      const response = await api.post('/pos/auth/refresh/', {
        refresh: refreshToken
      });

      const data = response.data;
      localStorage.setItem('access_token', data.access_token);
      
      return data;
      
    } catch (error) {
      console.error('Error refreshing token:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      this.handleError(error);
    }
  }
}

// Create and export singleton instance
const settingsAPIService = new SettingsAPIService();

export default settingsAPIService;