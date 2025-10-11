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
      console.error('Get all products error:', error.response?.data);
      this.handleError(error);
    }
  }

  transformProductData(products) {
    if (!Array.isArray(products)) {
        console.warn('⚠️ transformProductData received non-array:', products)
        return [];
    }
    
    return products.map(product => {
        // ✅ Extract ID with more options
        const productId = product._id || product.id || product.product_id
        
        console.log(`🔧 Transforming product:`, {
            original_id: product._id,
            transformed_id: productId,
            name: product.product_name || product.name
        })
        
        return {
            id: productId,  // ✅ Make sure this matches what cart uses
            _id: productId, // ✅ Keep both for compatibility
            name: product.name || product.product_name,
            description: product.description || '',
            price: product.price || product.selling_price || 0,
            category: product.category || product.category_id,
            subcategory: product.subcategory || product.subcategory_name || product.sub_category,
            image: product.image || product.image_url || this.generatePlaceholderImage(product.name || product.product_name),
            stock: product.stock_quantity || product.stock || 0,  // ✅ Backend uses "stock"
            sku: product.sku || product.SKU || ''
        }
    });
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

  async getProductsBatch(productIds) {
    try {
        if (!productIds || productIds.length === 0) {
            console.warn('⚠️ No product IDs provided to getProductsBatch');
            return [];
        }
        
        console.log('📦 Fetching batch products:', productIds);
        
        // Join product IDs with comma
        const idsParam = productIds.join(',');
        
        // Call backend batch endpoint
        const response = await api.get(`/pos/products/batch/?ids=${idsParam}`);
        const data = this.handleResponse(response);
        
        console.log('✅ Batch products fetched:', data);
        
        // Extract products from response
        const products = data.data || data.products || data;
        
        // Transform products to match frontend format
        return this.transformProductData(products);
        
    } catch (error) {
        console.error('❌ Get products batch failed:', error);
        this.handleError(error);
    }
  }
  
}

const productAPIService = new ProductAPIService();

export default productAPIService;