import { api } from './api.js';

class ProductAPIService {
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

 async getProductsByCategory(categoryId, subcategoryName = null) {
    try {
        let url = `/products/category/${categoryId}/`;
        
        // Add subcategory parameter if provided
        if (subcategoryName) {
        url += `?subcategory=${encodeURIComponent(subcategoryName)}`;
        }
        const response = await api.get(url);
        const data = this.handleResponse(response);
        // Transform and return the products
        return this.transformProductData(data.products || data);
        
    } catch (error) {
        this.handleError(error);
    }
 }

 transformProductData(products) {
    if (!Array.isArray(products)) {
        return [];
    }
    
    return products.map(product => ({
        id: product.id || product._id,
        name: product.name || product.product_name,
        description: product.description || '',
        price: product.price || product.selling_price || 0,
        category: product.category,
        subcategory: product.subcategory,
        image: product.image || this.generatePlaceholderImage(product.name),
        stock: product.stock_quantity || 0,
        sku: product.sku || ''
    }));
 }

   async searchProducts(query) {
        try {
            // Use the search parameter in the API call
            const response = await api.get(`/products/?search=${encodeURIComponent(query)}`);
            const data = this.handleResponse(response);
            
            // Return the transformed data directly
            return this.transformProductData(data.results || data);
            
        } catch (error) {
            this.handleError(error);
        }
    }
  
}

const productAPIService = new ProductAPIService();

export default productAPIService;