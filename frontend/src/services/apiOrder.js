import { api } from './api.js';

class OrderAPIService {
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

  // Recommended API calls
async loadCategory(categoryId) {
  // First, get category with subcategory counts
  const category = await api.get(`/categories/${categoryId}`)
  
  // Decide navigation strategy based on product counts
  if (category.total_products > 25) {
    // Load subcategories only
    return category.sub_categories.map(sub => ({
      id: sub.id,
      name: sub.name,
      product_count: sub.products.length,
      type: 'subcategory'
    }))
  } else {
    // Load all products flattened
    return await api.get(`/categories/${categoryId}/products`)
  }
}
  

}

// Create and export singleton instance
const orderAPIService = new OrderAPIService();

export default orderAPIService;