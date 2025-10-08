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
        // Use the subcategory products endpoint
        url = `/category/${categoryId}/subcategories/${encodeURIComponent(subcategoryName)}/products/`;
      } else {
        // Use the products by category report endpoint
        url = `/products/reports/by-category/${categoryId}/`;
      }
      
      console.log('Fetching products from URL:', url);
      
      const response = await api.get(url);
      const data = this.handleResponse(response);
      
      console.log('Raw API response:', data);
      
      // Handle different possible response structures
      let products = [];
      if (Array.isArray(data)) {
        products = data;
      } else if (data.results && Array.isArray(data.results)) {
        products = data.results;
      } else if (data.products && Array.isArray(data.products)) {
        products = data.products;
      } else if (data.data && Array.isArray(data.data)) {
        products = data.data;
      } else {
        console.warn('Unexpected API response structure:', data);
        products = [];
      }
      
      // Transform and return the products
      return this.transformProductData(products);
      
    } catch (error) {
      console.error('API Error details:', error.response?.data);
      this.handleError(error);
    }
  }

  // Alternative method using POS catalog (try this if the above doesn't work)
  async getProductsByPOSCatalog(categoryId = null) {
    try {
      let url = '/pos/catalog/';
      
      // Add category filter as query parameter
      if (categoryId) {
        url += `?category=${categoryId}`;
      }
      
      console.log('Fetching from POS catalog:', url);
      
      const response = await api.get(url);
      const data = this.handleResponse(response);
      
      console.log('POS Catalog response:', data);
      
      // Handle response structure
      let products = [];
      if (Array.isArray(data)) {
        products = data;
      } else if (data.catalog && Array.isArray(data.catalog)) {
        products = data.catalog;
      } else if (data.products && Array.isArray(data.products)) {
        products = data.products;
      }
      
      // Filter by category if needed (client-side filtering as fallback)
      if (categoryId && products.length > 0) {
        products = products.filter(product => 
          product.category === categoryId || 
          product.category_id === categoryId
        );
      }
      
      return this.transformProductData(products);
      
    } catch (error) {
      console.error('POS Catalog API Error:', error.response?.data);
      this.handleError(error);
    }
  }

  // Fallback method - get all products and filter client-side
  async getAllProducts() {
    try {
      const response = await api.get('/products/');
      const data = this.handleResponse(response);
      
      console.log('All products response:', data);
      
      let products = [];
      if (Array.isArray(data)) {
        products = data;
      } else if (data.results && Array.isArray(data.results)) {
        products = data.results;
      } else if (data.products && Array.isArray(data.products)) {
        products = data.products;
      }
      
      return this.transformProductData(products);
      
    } catch (error) {
      console.error('Get all products error:', error.response?.data);
      this.handleError(error);
    }
  }

  // In your apiProducts.js transformProductData method
  transformProductData(products) {
    if (!Array.isArray(products)) {
        return [];
    }
    
    return products.map(product => {
        const imageUrl = this.getProductImage(product);
        
        return {
        id: product.id || product._id || product.product_id,
        name: product.name || product.product_name || 'Unknown Product',
        description: product.description || '',
        price: product.price || product.selling_price || 0,
        category: product.category || product.category_id,
        subcategory: product.subcategory || product.subcategory_name,
        // Use a placeholder immediately if no image URL
        image: imageUrl || '',
        stock: product.stock_quantity || product.stock || 0,
        sku: product.sku || product.product_code || ''
        };
    });
  }

  // Enhanced image handling method
  getProductImage(product) {
    const productName = product.name || product.product_name || 'Product';
    
    // Check for various image field possibilities
    const imageUrl = product.image || 
                    product.image_url || 
                    product.product_image || 
                    product.thumbnail || 
                    product.photo;
    
    // If we have an image URL, validate and return it
    if (imageUrl && imageUrl.trim() !== '') {
        // Handle relative URLs by making them absolute
        if (imageUrl.startsWith('/')) {
        return `${window.location.origin}${imageUrl}`;
        }
        
        // Handle full URLs
        if (imageUrl.startsWith('http')) {
        return imageUrl;
        }
        
        // Handle blob or data URLs
        if (imageUrl.startsWith('blob:') || imageUrl.startsWith('data:')) {
        return imageUrl;
        }
        
        // If it's just a filename, construct full path
        return `${window.location.origin}/media/products/${imageUrl}`;
    }
    
    // No valid image found, return null to let the error handler deal with it
    return null;
  }

  // Multiple placeholder image options
  generatePlaceholderImage(productName, style = 'default') {
    const encodedName = encodeURIComponent(productName);
    const color = this.getColorFromString(productName);
    
    switch (style) {
      case 'themed':
        // Use your app's primary color from the CSS variables
        return `https://via.placeholder.com/200x150/7392E2/white?text=${encodedName}`;
      
      case 'colorful':
        // Generate different colors based on product name
        return `https://via.placeholder.com/200x150/${color}/white?text=${encodedName}`;
      
      case 'neutral':
        // Neutral gray placeholder
        return `https://via.placeholder.com/200x150/CCCCCC/666666?text=${encodedName}`;
      
      case 'food':
        // Food-themed placeholder (good for restaurant POS)
        return `https://via.placeholder.com/200x150/FF6B6B/white?text=🍽️+${encodedName}`;
      
      default:
        // Default themed placeholder using your app colors
        return `https://via.placeholder.com/200x150/7392E2/white?text=${encodedName}`;
    }
  }

  // Generate a consistent color based on string input
  getColorFromString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // Convert to 6-digit hex color
    const color = Math.abs(hash).toString(16).substring(0, 6);
    return color.padEnd(6, '0');
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