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
        this.handleError(error);
    }
  }

  transformProductData(products, fallbackCategoryId = null) {
    if (!Array.isArray(products)) return [];
    
    return products.map(product => {
        const productId = product._id || product.id || product.product_id
        
        // ✅ FORCE: Always use batch_stock if available
        let stockValue;
        if (product.batch_stock !== undefined && product.batch_stock !== null) {
            stockValue = product.batch_stock
        } else if (product.stock_quantity !== undefined) {
            stockValue = product.stock_quantity
        } else {
            stockValue = product.stock || 0
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
        
        return {
            id: productId,
            _id: productId,
            name: product.name || product.product_name,
            price: product.price || product.selling_price || 0,
            stock: stockValue,
            batch_stock: product.batch_stock,
            batches_count: product.batches_count || 0,
            image: product.image || product.image_url || this.generatePlaceholderImage(product.name || product.product_name),
            sku: product.sku || product.SKU || '',
            category: categoryId,  // ✅ This will now match promotion format
            subcategory: product.subcategory || product.subcategory_name,
            // ✅ ADD: Keep original data for debugging
            originalData: product
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