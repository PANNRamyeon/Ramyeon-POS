/**
 * Stock Cache Management
 * 
 * Handles updating stock levels in cache after transactions
 * without invalidating the entire product cache
 */

import { useLocalStorage } from './useLocalStorage.js'
import { useCache } from './useCache.js'

export function useStockCache() {
  const storage = useLocalStorage().withPrefix('newOrder')
  const memCache = useCache({ maxEntries: 300 })

  /**
   * Update stock levels for specific products after a transaction
   * @param {Array} soldItems - Array of items sold: [{ product_id, quantity }]
   */
  function updateStockAfterSale(soldItems) {
    if (!soldItems || soldItems.length === 0) {
      return
    }

    // Group items by product_id and sum quantities
    const stockChanges = {}
    soldItems.forEach(item => {
      const productId = item.product_id || item.productId
      const quantity = item.quantity || 0
      
      if (productId) {
        stockChanges[productId] = (stockChanges[productId] || 0) + quantity
      }
    })
    
    if (Object.keys(stockChanges).length === 0) {
      return
    }

    // Get all cached product keys from localStorage
    const allKeys = []
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('newOrder_products:')) {
          allKeys.push(key)
        }
      }
    } catch (error) {
      // Error reading localStorage keys
    }

    let updatedCount = 0
    let totalProductsChecked = 0
    let totalProductsUpdated = 0

    // Update each cache entry
    allKeys.forEach(fullKey => {
      try {
        // Extract the key without prefix
        const key = fullKey.replace('newOrder_', '')
        
        // Get cached products
        const cached = storage.getItem(key, null)
        
        if (!Array.isArray(cached)) {
          return
        }

        totalProductsChecked += cached.length

        // Update stock for affected products
        let wasUpdated = false
        const updated = cached.map(product => {
          const stockChange = stockChanges[product.id]
          
          if (stockChange) {
            wasUpdated = true
            totalProductsUpdated++
            const oldStock = product.stock || 0
            const newStock = Math.max(0, oldStock - stockChange)
            
            return {
              ...product,
              stock: newStock
            }
          }
          
          return product
        })

        // Save back to cache if any changes were made
        if (wasUpdated) {
          const ttl = 24 * 60 * 60 * 1000 // 24 hours
          storage.setItem(key, updated, ttl)
          
          // Also update memory cache
          memCache.set(key, updated, 30 * 60 * 1000) // 30 minutes
          
          updatedCount++
        }
        
      } catch (error) {
        // Error updating cache key
      }
    })
  }

  /**
   * Refresh stock levels for specific products from API
   * @param {Array} productIds - Array of product IDs to refresh
   * @param {Function} fetchProductFn - Function to fetch product data: (productId) => Promise<Product>
   */
  async function refreshStockForProducts(productIds, fetchProductFn) {
    if (!productIds || productIds.length === 0) return

    const updates = {}

    // Fetch fresh data for each product
    for (const productId of productIds) {
      try {
        const freshProduct = await fetchProductFn(productId)
        if (freshProduct && freshProduct.id) {
          updates[freshProduct.id] = freshProduct.stock
        }
      } catch (error) {
        // Failed to fetch product
      }
    }

    // Update all cache entries with fresh stock
    const allKeys = []
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('newOrder_products:')) {
          allKeys.push(key)
        }
      }
    } catch (error) {
      // Error reading localStorage keys
    }

    allKeys.forEach(fullKey => {
      try {
        const key = fullKey.replace('newOrder_', '')
        const cached = storage.getItem(key, null)
        
        if (!Array.isArray(cached)) return

        let wasUpdated = false
        const updated = cached.map(product => {
          const newStock = updates[product.id]
          
          if (newStock !== undefined && newStock !== product.stock) {
            wasUpdated = true
            
            return {
              ...product,
              stock: newStock
            }
          }
          
          return product
        })

        if (wasUpdated) {
          const ttl = 24 * 60 * 60 * 1000
          storage.setItem(key, updated, ttl)
          memCache.set(key, updated, 30 * 60 * 1000)
        }
        
      } catch (error) {
        // Error updating cache key
      }
    })
  }

  /**
   * Invalidate all product caches (nuclear option - use sparingly)
   */
  function invalidateAllProductCaches() {
    // Clear memory cache
    memCache.clear()

    // Clear localStorage product caches
    const keysToRemove = []
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('newOrder_products:')) {
          keysToRemove.push(key)
        }
      }
    } catch (error) {
      // Error reading localStorage keys
    }

    keysToRemove.forEach(key => {
      try {
        localStorage.removeItem(key)
      } catch (error) {
        // Error removing key
      }
    })
  }

  return {
    updateStockAfterSale,
    refreshStockForProducts,
    invalidateAllProductCaches
  }
}
