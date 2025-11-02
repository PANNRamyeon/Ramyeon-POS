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
        
        // ✅ Use total_stock if available, otherwise fallback to batch_stock
        let stockValue;
        if (product.total_stock !== undefined && product.total_stock !== null) {
            stockValue = product.total_stock
        } else if (product.batch_stock !== undefined && product.batch_stock !== null) {
            stockValue = product.batch_stock
        } else {
            stockValue = null
        }
        
        // ✅ FIX: Get category ID in correct format
        // Priority: product.category_id > product.category > fallbackCategoryId
        let categoryId = product.category_id || product.category || fallbackCategoryId
        
        // ✅ ENSURE: Category ID is a string (not a number)
        if (categoryId && typeof categoryId === 'number') {
            categoryId = `CTGY-${String(categoryId).padStart(3, '0')}`
        }
        
        const transformed = {
            id: productId,
            _id: productId,
            name: product.name || product.product_name,
            product_name: product.product_name || product.name, // Keep both for compatibility
            price: product.price || product.selling_price || 0,
            selling_price: product.selling_price || product.price || 0, // Keep both for compatibility
            stock: stockValue,
            total_stock: stockValue, // Use the same value for both fields
            batch_stock: product.batch_stock,
            batches_count: product.batches_count || 0,
            image: product.image || product.image_url || this.generatePlaceholderImage(product.name || product.product_name),
            sku: product.sku || product.SKU || '',
            SKU: product.SKU || product.sku || '', // Keep both for compatibility
            barcode: product.barcode || '', // ✅ CRITICAL: Add barcode field
            category: categoryId,  // ✅ This will now match promotion format
            category_id: categoryId, // Keep both for compatibility
            subcategory: product.subcategory || product.subcategory_name,
            subcategory_name: product.subcategory_name || product.subcategory, // Keep both for compatibility
            is_taxable: product.is_taxable !== false, // ✅ Add tax info
            isTaxable: product.is_taxable !== false, // Keep both for compatibility
            // ✅ ADD: Keep original data for debugging
            originalData: product
        }
        
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
        
        // Transform products to match frontend format
        return this.transformProductData(products);
        
    } catch (error) {
        this.handleError(error);
    }
  }
  
}

const productAPIService = new ProductAPIService();

export default productAPIService;