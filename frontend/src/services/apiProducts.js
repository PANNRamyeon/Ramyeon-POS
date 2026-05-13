import { api } from './api.js';

const PRODUCT_CACHE_KEY = 'pann_products_v1'
const PRODUCT_CACHE_TTL = 60 * 60 * 1000 // 1 hour

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

  // Fetch one page of products (mirrors back office getAllProducts)
  async getAllProducts(filters = {}, pageToken = null) {
    try {
      const params = { page_size: 100 }
      if (filters.category_id) params.category_id = filters.category_id
      if (filters.status) params.status = filters.status
      if (filters.search) params.search = filters.search
      if (pageToken) params.page_token = pageToken

      const response = await api.get('/admin/products/', { params })
      return this.handleResponse(response)
    } catch (error) {
      this.handleError(error)
    }
  }

  // Fetch ALL products across all pages — same logic as back office
  async getAllProductsAllPages(filters = {}) {
    let allProducts = []
    let pageToken = null

    do {
      const response = await this.getAllProducts(filters, pageToken)
      const pageItems = response.data || []
      allProducts = allProducts.concat(pageItems)
      pageToken = response.next_page_token || null
    } while (pageToken)

    return this.transformProductData(allProducts)
  }

  async getProductsByCategory(categoryId, subcategoryName = null) {
    try {
        let url;

        if (subcategoryName) {
            url = `/admin/categories/${categoryId}/subcategories/${encodeURIComponent(subcategoryName)}/products/`;
        } else {
            url = `/admin/products/?category_id=${categoryId}`;
        }

        const response = await api.get(url);
        const data = this.handleResponse(response);

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
        
        // Back office uses product_name + SKU (uppercase); old used name + sku
        const displayName = product.product_name || product.name || ''
        const skuValue = product.SKU || product.sku || ''
        const price = product.selling_price || product.price || 0
        const imageUrl = product.image_url || product.image || this.generatePlaceholderImage(displayName)

        const transformed = {
            id: productId,
            _id: productId,
            name: displayName,
            product_name: displayName,
            price,
            selling_price: price,
            stock: stockValue,
            total_stock: stockValue,
            batch_stock: product.batch_stock,
            batches_count: product.batches_count || 0,
            image: imageUrl,
            sku: skuValue,
            SKU: skuValue,
            barcode: product.barcode || '',
            category: categoryId || product.category_id || product.category,
            category_id: categoryId || product.category_id || product.category,
            subcategory: product.subcategory_name || product.subcategory,
            subcategory_name: product.subcategory_name || product.subcategory,
            is_taxable: product.is_taxable !== false,
            isTaxable: product.is_taxable !== false,
            originalData: product
        }
        
        return transformed;
    });
  }

  generatePlaceholderImage() {
    return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f3f4f6'/%3E%3Crect x='55' y='60' width='90' height='80' rx='6' fill='%23e5e7eb'/%3E%3Ccircle cx='80' cy='88' r='10' fill='%23d1d5db'/%3E%3Cpolygon points='55,140 85,105 110,125 130,100 145,140' fill='%23d1d5db'/%3E%3C/svg%3E`;
  }

  async searchProducts(query) {
    try {
        const response = await api.get(`/admin/products/?search=${encodeURIComponent(query)}`);
        const data = this.handleResponse(response);

        return this.transformProductData(data.results || data.data || data);

    } catch (error) {
        this.handleError(error);
    }
  }

  _loadCachedProducts() {
    try {
      const raw = localStorage.getItem(PRODUCT_CACHE_KEY)
      if (!raw) return null
      const { data, expires } = JSON.parse(raw)
      if (Date.now() > expires) return null
      return data
    } catch {
      return null
    }
  }

  _saveProductsToCache(products) {
    try {
      localStorage.setItem(PRODUCT_CACHE_KEY, JSON.stringify({
        data: products,
        expires: Date.now() + PRODUCT_CACHE_TTL
      }))
    } catch {}
  }

  invalidateProductCache() {
    try { localStorage.removeItem(PRODUCT_CACHE_KEY) } catch {}
  }

  async getAllProductsAllPagesCached() {
    const cached = this._loadCachedProducts()
    if (cached) return cached
    const products = await this.getAllProductsAllPages()
    this._saveProductsToCache(products)
    return products
  }

  async getStockLevels() {
    try {
      const response = await api.get('/admin/products/stock/')
      return response.data?.data || []
    } catch {
      return []
    }
  }

  async getProductsBatch(productIds) {
    try {
        if (!productIds || productIds.length === 0) {
            return [];
        }

        // Fetch each product individually — no batch endpoint in back office
        const results = await Promise.allSettled(
            productIds.map(id => api.get(`/admin/products/${id}/`))
        )

        const products = results
            .filter(r => r.status === 'fulfilled')
            .map(r => r.value.data?.product || r.value.data?.data || r.value.data)
            .filter(Boolean)

        return this.transformProductData(products)

    } catch (error) {
        this.handleError(error);
    }
  }
  
}

const productAPIService = new ProductAPIService();

export default productAPIService;