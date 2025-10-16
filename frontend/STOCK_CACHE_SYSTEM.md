# Stock Cache System

## Overview

The stock cache system ensures that product stock levels displayed in `NewOrder.vue` remain accurate and up-to-date, even when products are cached in localStorage for performance.

## Problem Solved

Previously, product data (including stock levels) was cached in localStorage for 24 hours to improve loading times. However, this meant stock levels would become outdated after transactions, showing incorrect inventory.

## Solution

A multi-layered approach to keep stock levels current:

1. **Immediate Updates After Transactions** - Stock is updated in cache immediately after checkout
2. **Periodic Background Refresh** - Stock levels refresh every 5 minutes while `NewOrder.vue` is open
3. **Smart Caching** - Product details remain cached (24h) while stock data refreshes frequently

## Architecture

### Components

#### 1. `useStockCache.js`
**Location:** `frontend/src/composables/data/useStockCache.js`

**Purpose:** Utility for managing stock updates in cache

**Methods:**
- `updateStockAfterSale(soldItems)` - Updates stock after a transaction
  - Decrements stock levels for sold items
  - Updates both localStorage and memory cache
  - Handles multiple cache entries (different categories/subcategories)

- `refreshStockForProducts(productIds, fetchProductFn)` - Refreshes stock from API
  - Fetches fresh stock data for specific products
  - Updates all cache entries containing those products
  - Used for periodic background refreshes

- `invalidateAllProductCaches()` - Nuclear option to clear all caches
  - Use sparingly, only when needed

#### 2. Transaction Hooks

**Checkout.vue:**
```javascript
handleSaleSuccess(result, paymentMethod) {
  // Update stock cache with sold items
  try {
    this.stockCache.updateStockAfterSale(this.cartItems)
    console.log('📦 Stock cache updated after sale')
  } catch (error) {
    console.error('⚠️ Failed to update stock cache:', error)
    // Don't block success flow if cache update fails
  }
  
  // ... rest of checkout flow
}
```

**PaymentCallback.vue:**
```javascript
const result = await apiSales.createSale(saleData)

// Update stock cache with sold items
try {
  this.stockCache.updateStockAfterSale(saleData.items)
  console.log('📦 Stock cache updated after e-wallet sale')
} catch (error) {
  console.error('⚠️ Failed to update stock cache:', error)
}
```

#### 3. Periodic Refresh in NewOrder.vue

**Startup:**
```javascript
async mounted() {
  // ... initialization code
  
  // Set up periodic stock refresh
  this.startStockRefresh()
}
```

**Cleanup:**
```javascript
beforeUnmount() {
  // Clean up stock refresh interval
  if (this.stockRefreshInterval) {
    clearInterval(this.stockRefreshInterval)
    this.stockRefreshInterval = null
  }
}
```

**Refresh Logic:**
```javascript
startStockRefresh() {
  console.log('🔄 Starting periodic stock refresh (every 5 minutes)')
  
  // Refresh immediately on start
  this.refreshStockLevels()
  
  // Then set up interval
  this.stockRefreshInterval = setInterval(() => {
    this.refreshStockLevels()
  }, this.stockRefreshIntervalMs) // 5 minutes
}

async refreshStockLevels() {
  // 1. Collect all product IDs currently visible/cached
  // 2. Fetch fresh stock data via batch API
  // 3. Update all cache entries with new stock levels
  // 4. Refresh current view to show updated data
}
```

## Data Flow

### Transaction Flow
```
User completes checkout
    ↓
Sale created in backend (stock decremented in DB)
    ↓
handleSaleSuccess() called
    ↓
stockCache.updateStockAfterSale() updates cache
    ↓
Stock displayed in UI is now accurate
```

### Periodic Refresh Flow
```
Every 5 minutes (while NewOrder.vue is open)
    ↓
refreshStockLevels() collects visible product IDs
    ↓
Batch fetch fresh stock from API
    ↓
Update all cache entries with new stock
    ↓
Reload current view with updated data
```

## Configuration

### Cache TTL Settings
Located in `NewOrder.vue` data:

```javascript
cacheTTLms: 24 * 60 * 60 * 1000,     // 24 hours for localStorage
memCacheTTLms: 30 * 60 * 1000,        // 30 minutes for in-memory cache
stockRefreshIntervalMs: 5 * 60 * 1000 // 5 minutes for stock refresh
```

### Adjusting Refresh Frequency

To change how often stock refreshes:

```javascript
// In NewOrder.vue data()
stockRefreshIntervalMs: 3 * 60 * 1000  // Change to 3 minutes
```

**Recommended values:**
- **High-traffic stores:** 2-3 minutes
- **Medium-traffic stores:** 5 minutes (default)
- **Low-traffic stores:** 10 minutes

## Performance Considerations

### Pros
✅ Product details (images, names, prices) remain cached for fast loading  
✅ Only stock numbers update, reducing data transfer  
✅ Batch API calls minimize server load  
✅ Immediate updates after transactions provide instant feedback  
✅ Background refresh is non-blocking

### Cons
⚠️ Stock may be up to 5 minutes stale (between refreshes)  
⚠️ Periodic API calls every 5 minutes per user  
⚠️ Additional complexity in cache management

### Optimization Tips

1. **Batch Size:** The system uses `getProductsBatch()` to fetch multiple products at once
2. **Smart Refresh:** Only refreshes products currently visible or in custom categories
3. **Error Handling:** Refresh failures don't crash the UI or block transactions
4. **Cleanup:** Intervals are properly cleared on unmount to prevent memory leaks

## Testing

### Test Scenarios

1. **Transaction Stock Update:**
   - Add products to cart in NewOrder
   - Complete checkout
   - Return to NewOrder
   - Verify stock decreased by purchased quantity

2. **Periodic Refresh:**
   - Open NewOrder page
   - Wait for console log: "📊 Refreshing stock levels from API..."
   - Check that fresh stock is displayed

3. **Cache Persistence:**
   - Navigate away from NewOrder
   - Return to NewOrder
   - Products should load instantly from cache
   - Stock should be up-to-date from last refresh

4. **Multi-Tab Behavior:**
   - Open NewOrder in two tabs
   - Complete transaction in Tab 1
   - Wait up to 5 minutes in Tab 2
   - Tab 2 should show updated stock after refresh

## Console Logs

The system provides detailed console logs for debugging:

```
🔄 Starting periodic stock refresh (every 5 minutes)
📊 Refreshing stock levels from API...
  📦 Refreshing stock for 42 products
  ✅ Fetched 42 products from API
    ✏️ Ice talk blue lemon: 15 → 13
    ✏️ Ice talk blueberry: 31 → 28
  ✅ Updated 8 cache entries
  ✅ Updated current view with fresh stock data
```

After transactions:
```
📦 Stock cache updated after sale
📦 Updating stock cache after sale: 2 items
📊 Stock changes: { "507f1f77bcf86cd799439011": 2, "507f1f77bcf86cd799439012": 1 }
🔑 Found 12 product cache keys
  ✏️ Ice talk blue lemon: 15 → 13 (-2)
  ✏️ Ice talk blueberry: 31 → 30 (-1)
✅ Updated 3 cache entries
```

## Troubleshooting

### Stock Not Updating After Purchase

**Symptoms:** Stock stays the same after checkout  
**Solution:**
1. Check console for "📦 Stock cache updated after sale"
2. If missing, verify `stockCache` is initialized in setup()
3. Check that `updateStockAfterSale()` is called in `handleSaleSuccess()`

### Stock Still Outdated After 5 Minutes

**Symptoms:** Stock doesn't refresh automatically  
**Solution:**
1. Check console for "📊 Refreshing stock levels from API..."
2. If missing, verify interval is set: `this.stockRefreshInterval`
3. Check for errors in `refreshStockLevels()` method
4. Ensure `beforeUnmount()` cleanup isn't being called prematurely

### Performance Issues

**Symptoms:** Page feels slow, lots of API calls  
**Solution:**
1. Increase `stockRefreshIntervalMs` to reduce refresh frequency
2. Check if batch API is being used (not individual calls)
3. Monitor network tab for excessive requests

## Future Enhancements

### Potential Improvements

1. **WebSocket Integration:**
   - Real-time stock updates from server
   - Eliminate need for polling
   - Instant updates across all tabs/devices

2. **Visibility API:**
   - Pause refresh when tab is hidden
   - Resume when tab becomes active
   - Save battery/bandwidth

3. **Differential Updates:**
   - Only fetch stock that changed
   - Reduce data transfer
   - Faster updates

4. **Smart Refresh:**
   - Refresh more frequently for low-stock items
   - Less frequently for high-stock items
   - Adaptive based on transaction velocity

## Related Files

- `frontend/src/composables/data/useStockCache.js` - Stock cache utility
- `frontend/src/composables/data/useLocalStorage.js` - localStorage wrapper
- `frontend/src/composables/data/useCache.js` - In-memory cache
- `frontend/src/pages/NewOrder.vue` - Main UI component
- `frontend/src/pages/Checkout.vue` - Cash payment handler
- `frontend/src/components/PaymentCallback.vue` - E-wallet payment handler
- `frontend/src/services/apiProducts.js` - Product API service

## Support

For issues or questions, check:
1. Console logs (detailed debugging info)
2. Network tab (API call success/failures)
3. localStorage (verify cache structure)
4. This documentation

---

**Last Updated:** October 15, 2025  
**Version:** 1.0  
**Author:** AI Assistant

