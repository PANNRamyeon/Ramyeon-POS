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
        let url;
        
        if (subcategoryName) {
            // Use subcategory-specific endpoint
            url = `/category/${categoryId}/subcategories/${encodeURIComponent(subcategoryName)}/products/`;
        } else {
            // Use category products report endpoint
            url = `/products/reports/by-category/${categoryId}/`;
        }
        
        const response = await api.get(url);
        const data = this.handleResponse(response);
        
        // Transform and return the products
        return this.transformProductData(data.products || data.data || data);
        
    } catch (error) {
        this.handleError(error);
    }
  }

  transformProductData(products) {
    if (!Array.isArray(products)) {
        return [];
    }
    
    return products.map(product => ({
        id: product._id || product.id,
        name: product.name || product.product_name,
        description: product.description || '',
        price: product.price || product.selling_price || 0,
        category: product.category || product.category_id,
        subcategory: product.subcategory || product.sub_category,
        image: product.image || product.image_url || this.generatePlaceholderImage(product.name || product.product_name),
        stock: product.stock_quantity || product.stock || 0,
        sku: product.sku || ''
    }));
  }

  generatePlaceholderImage(productName) {
    // Generate a placeholder image URL
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(productName || 'Product')}&size=200&background=7392E2&color=fff`;
  }

  async searchProducts(query) {
    try {
        // Use the search parameter in the API call
        const response = await api.get(`/products/?search=${encodeURIComponent(query)}`);
        const data = this.handleResponse(response);
        
        // Return the transformed data directly
        return this.transformProductData(data.results || data.data || data);
        
    } catch (error) {
        this.handleError(error);
    }
  }
  
}

const productAPIService = new ProductAPIService();

export default productAPIService;