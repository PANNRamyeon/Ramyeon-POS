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
        
        // ✅ Pass categoryId to transformProductData so it can use it as fallback
        return this.transformProductData(data.products || data.data || data, categoryId);
        
    } catch (error) {
      console.error('Get all products error:', error.response?.data);
      this.handleError(error);
    }
  }

  transformProductData(products, fallbackCategoryId = null) {
    if (!Array.isArray(products)) return [];
    
    return products.map(product => {
        const productId = product._id || product.id || product.product_id
        
        // Debug: Log what fields are available in the raw product
        console.log(`🔍 Transforming product ${product.name || product.product_name}:`, {
          id: productId,
          total_stock: product.total_stock,
          batch_stock: product.batch_stock,
          stock: product.stock,
          availableFields: Object.keys(product)
        });
        
        // ✅ Use total_stock if available, otherwise fallback to batch_stock
        let stockValue;
        if (product.total_stock !== undefined && product.total_stock !== null && product.total_stock >= 0) {
            stockValue = product.total_stock
        } else if (product.batch_stock !== undefined && product.batch_stock !== null && product.batch_stock >= 0) {
            stockValue = product.batch_stock
        } else if (product.stock !== undefined && product.stock !== null && product.stock >= 0) {
            stockValue = product.stock
        } else {
            stockValue = 0  // Default to 0 instead of null
        }
        
        // ✅ FIX: Get category ID in correct format
        // Priority: product.category_id > product.category > fallbackCategoryId
        let categoryId = product.category_id || product.category || fallbackCategoryId
        
        // ✅ ENSURE: Category ID is a string (not a number)
        if (categoryId && typeof categoryId === 'number') {
            categoryId = `CTGY-${String(categoryId).padStart(3, '0')}`
        }
        
        console.log(`📦 Product: ${product.name}`)
        console.log(`   ID: ${productId}`)
        console.log(`   Category: ${categoryId}`)
        console.log(`   Stock: ${stockValue}`)
        
        const transformed = {
            id: productId,
            _id: productId,
            name: product.name || product.product_name,
            price: product.price || product.selling_price || 0,
            stock: stockValue,
            total_stock: stockValue, // Use the same value for both fields
            batch_stock: product.batch_stock,
            batches_count: product.batches_count || 0,
            image: product.image || product.image_url || this.generatePlaceholderImage(product.name || product.product_name),
            sku: product.sku || product.SKU || '',
            category: categoryId,  // ✅ This will now match promotion format
            subcategory: product.subcategory || product.subcategory_name,
            // ✅ ADD: Keep original data for debugging
            originalData: product
        }
        
        console.log(`🔍 Transformed product ${transformed.name}:`, {
          id: transformed.id,
          total_stock: transformed.total_stock,
          stock: transformed.stock
        });
        
        return transformed;
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
            return [];
        }
        
        // Join product IDs with comma
        const idsParam = productIds.join(',');
        
        // Call backend batch endpoint
        const response = await api.get(`/pos/products/batch/?ids=${idsParam}`);
        const data = this.handleResponse(response);
        
        // Extract products from response
        const products = data.data || data.products || data;
        
        // Debug: Log raw API response
        console.log('🔍 Raw API response for products batch:', products);
        if (Array.isArray(products) && products.length > 0) {
          console.log('🔍 First product from API:', products[0]);
          console.log('🔍 total_stock field:', products[0].total_stock);
        }
        
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