import { api } from './api.js';

class TransactionsAPIService {
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

  
  

}

// Create and export singleton instance
const transactionsAPIService = new TransactionsAPIService();

export default transactionsAPIService;