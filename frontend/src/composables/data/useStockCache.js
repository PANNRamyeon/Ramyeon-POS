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
      console.log('⚠️ No items to update stock for')
      return
    }

    console.log('📦 Updating stock cache after sale:', soldItems.length, 'items')
    console.log('📋 Sold items structure:', JSON.stringify(soldItems, null, 2))

    // Group items by product_id and sum quantities
    const stockChanges = {}
    soldItems.forEach(item => {
      const productId = item.product_id || item.productId
      const quantity = item.quantity || 0
      
      if (productId) {
        stockChanges[productId] = (stockChanges[productId] || 0) + quantity
        console.log(`  📌 Product ${productId}: -${quantity}`)
      } else {
        console.warn('⚠️ Item missing product ID:', item)
      }
    })

    console.log('📊 Stock changes:', stockChanges)
    
    if (Object.keys(stockChanges).length === 0) {
      console.warn('⚠️ No valid product IDs found in sold items')
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
      console.error('❌ Error reading localStorage keys:', error)
    }

    console.log('🔑 Found', allKeys.length, 'product cache keys:', allKeys)

    let updatedCount = 0
    let totalProductsChecked = 0
    let totalProductsUpdated = 0

    // Update each cache entry
    allKeys.forEach(fullKey => {
      try {
        // Extract the key without prefix
        const key = fullKey.replace('newOrder_', '')
        
        console.log(`\n🔍 Checking cache key: ${key}`)
        
        // Get cached products
        const cached = storage.getItem(key, null)
        
        if (!Array.isArray(cached)) {
          console.log(`  ⚠️ Cache entry is not an array, skipping`)
          return
        }

        console.log(`  📦 Found ${cached.length} products in this cache`)
        totalProductsChecked += cached.length

        // Update stock for affected products
        let wasUpdated = false
        const updated = cached.map(product => {
          const stockChange = stockChanges[product.id]
          
          if (stockChange) {
            wasUpdated = true
            totalProductsUpdated++
            const oldStock = product.total_stock || 0
            const newStock = Math.max(0, oldStock - stockChange)
            
            console.log(`  ✏️ UPDATING: ${product.name} (ID: ${product.id})`)
            console.log(`     Stock: ${oldStock} → ${newStock} (-${stockChange})`)
            
            return {
              ...product,
              total_stock: newStock
            }
          }
          
          return product
        })

        // Save back to cache if any changes were made
        if (wasUpdated) {
          const ttl = 24 * 60 * 60 * 1000 // 24 hours
          console.log(`  💾 Saving updated cache back to localStorage...`)
          storage.setItem(key, updated, ttl)
          
          // Also update memory cache
          memCache.set(key, updated, 30 * 60 * 1000) // 30 minutes
          
          updatedCount++
          console.log(`  ✅ Cache entry updated successfully`)
        } else {
          console.log(`  ℹ️ No products matched in this cache entry`)
        }
        
      } catch (error) {
        console.error('❌ Error updating cache key', fullKey, ':', error)
      }
    })

    console.log(`\n✅ SUMMARY:`)
    console.log(`   - Updated ${updatedCount} cache entries`)
    console.log(`   - Checked ${totalProductsChecked} total products`)
    console.log(`   - Updated ${totalProductsUpdated} products`)
    
    if (updatedCount === 0) {
      console.warn('⚠️ WARNING: No cache entries were updated!')
      console.warn('   This could mean:')
      console.warn('   1. Product IDs in cart don\'t match cached product IDs')
      console.warn('   2. No product caches exist yet')
      console.warn('   3. Products sold are not in any cached category')
    }
  }

  /**
   * Refresh stock levels for specific products from API
   * @param {Array} productIds - Array of product IDs to refresh
   * @param {Function} fetchProductFn - Function to fetch product data: (productId) => Promise<Product>
   */
  async function refreshStockForProducts(productIds, fetchProductFn) {
    if (!productIds || productIds.length === 0) return

    console.log('🔄 Refreshing stock for', productIds.length, 'products')

    const updates = {}

    // Fetch fresh data for each product
    for (const productId of productIds) {
      try {
        const freshProduct = await fetchProductFn(productId)
        if (freshProduct && freshProduct.id) {
          updates[freshProduct.id] = freshProduct.total_stock
          console.log(`  ✅ Fetched ${freshProduct.name}: total_stock = ${freshProduct.total_stock}`)
        }
      } catch (error) {
        console.error(`❌ Failed to fetch product ${productId}:`, error)
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
      console.error('❌ Error reading localStorage keys:', error)
    }

    allKeys.forEach(fullKey => {
      try {
        const key = fullKey.replace('newOrder_', '')
        const cached = storage.getItem(key, null)
        
        if (!Array.isArray(cached)) return

        let wasUpdated = false
        const updated = cached.map(product => {
          const newStock = updates[product.id]
          
          if (newStock !== undefined && newStock !== product.total_stock) {
            wasUpdated = true
            console.log(`  ✏️ ${product.name}: ${product.total_stock} → ${newStock}`)
            
            return {
              ...product,
              total_stock: newStock
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
        console.error('❌ Error updating cache key', fullKey, ':', error)
      }
    })

    console.log('✅ Stock refresh complete')
  }

  /**
   * Invalidate all product caches (nuclear option - use sparingly)
   */
  function invalidateAllProductCaches() {
    console.log('💥 Invalidating all product caches')

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
      console.error('❌ Error reading localStorage keys:', error)
    }

    keysToRemove.forEach(key => {
      try {
        localStorage.removeItem(key)
      } catch (error) {
        console.error('❌ Error removing key', key, ':', error)
      }
    })

    console.log(`✅ Removed ${keysToRemove.length} cache entries`)
  }

  return {
    updateStockAfterSale,
    refreshStockForProducts,
    invalidateAllProductCaches
  }
}

