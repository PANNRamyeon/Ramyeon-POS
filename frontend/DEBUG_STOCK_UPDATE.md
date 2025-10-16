# Debug: Stock Not Updating After Transaction

## Quick Troubleshooting Guide

### Step 1: Check Console Logs After Checkout

After completing a transaction, open your browser console (F12) and look for these logs in order:

#### ✅ Expected Logs (Success):

```
🎉 Sale completed successfully!
💳 Payment method: cash
🛒 Cart items to update stock for: [{productId: "...", quantity: 2, ...}]
🔄 Calling stockCache.updateStockAfterSale()...
📦 Updating stock cache after sale: 2 items
📋 Sold items structure: [{...full JSON...}]
  📌 Product 507f1f77bcf86cd799439011: -2
  📌 Product 507f1f77bcf86cd799439012: -1
📊 Stock changes: {507f1f77bcf86cd799439011: 2, 507f1f77bcf86cd799439012: 1}
🔑 Found 5 product cache keys: ["newOrder_products:1:__all__", ...]

🔍 Checking cache key: products:1:__all__
  📦 Found 24 products in this cache
  ✏️ UPDATING: Ice talk blue lemon (ID: 507f1f77bcf86cd799439011)
     Stock: 15 → 13 (-2)
  💾 Saving updated cache back to localStorage...
  ✅ Cache entry updated successfully

✅ SUMMARY:
   - Updated 3 cache entries
   - Checked 72 total products
   - Updated 2 products
✅ Stock cache update call completed
```

### Step 2: Diagnose Issues Based on Logs

#### Issue A: No "Calling stockCache.updateStockAfterSale()" log

**Cause:** Stock cache function not being called  
**Fix:**
```javascript
// Check in Checkout.vue setup():
setup() {
  const stockCache = useStockCache()  // ← Make sure this exists
  return { stockCache }               // ← Make sure it's returned
}
```

#### Issue B: "⚠️ No items to update stock for"

**Cause:** Cart items are empty or not passed correctly  
**Fix:** Check that cart items exist before calling:
```javascript
console.log('Cart items:', this.cartItems)  // Should show array with items
```

#### Issue C: "⚠️ No valid product IDs found in sold items"

**Cause:** Cart items don't have `productId` or `product_id` field  
**Check the cart item structure:**
```javascript
// Expected structure:
{
  productId: "507f1f77bcf86cd799439011",  // ← This must exist
  quantity: 2,
  productName: "Ice talk blue lemon",
  price: 65,
  ...
}
```

#### Issue D: "🔑 Found 0 product cache keys"

**Cause:** No products cached in localStorage yet  
**Solution:** 
1. Go to NewOrder page
2. Browse categories
3. Products will be cached
4. Try transaction again

#### Issue E: "ℹ️ No products matched in this cache entry"

**Cause:** Product IDs in cart don't match product IDs in cache  
**Debug:**
```javascript
// Check product ID format in cart:
console.log('Cart product IDs:', this.cartItems.map(i => i.productId))

// Check product ID format in cache:
// Open Application > Local Storage > newOrder_products:...
// Look at the "id" field in cached products
```

**Common mismatch:**
- Cart has: `"507f1f77bcf86cd799439011"` (string)
- Cache has: `507f1f77bcf86cd799439011` (number)
- Or vice versa

**Fix:** Ensure consistent ID format (use strict equality check)

#### Issue F: "⚠️ WARNING: No cache entries were updated!"

**This message provides hints:**
1. **Product IDs don't match** - Check ID format (string vs number)
2. **No caches exist** - Visit NewOrder page first to populate cache
3. **Products not in cached categories** - The sold products might be from categories not yet cached

### Step 3: Manual Verification

#### Check localStorage:

1. Open DevTools (F12)
2. Go to Application > Local Storage
3. Look for keys starting with `newOrder_products:`
4. Click on a key to see the cached products
5. Verify the stock values

#### Force Refresh:

If stock is still wrong, force a refresh:
```javascript
// In browser console on NewOrder page:
localStorage.removeItem('newOrder_products:1:__all__')  // Replace with your cache key
location.reload()
```

Or clear all product caches:
```javascript
// Clear all NewOrder caches
Object.keys(localStorage)
  .filter(key => key.startsWith('newOrder_'))
  .forEach(key => localStorage.removeItem(key))
location.reload()
```

### Step 4: Check Product ID Consistency

#### Verify ID format in cart:
```javascript
// In Checkout.vue, add console log:
console.log('Cart item IDs:', this.cartItems.map(i => ({
  id: i.productId,
  type: typeof i.productId
})))
```

#### Verify ID format in cache:
```javascript
// In NewOrder.vue, add console log after loading products:
console.log('Cached product IDs:', this.products.map(p => ({
  id: p.id,
  type: typeof p.id
})))
```

**They must match exactly!**

### Step 5: Test Periodic Refresh

The system should also refresh stock every 5 minutes.

#### Check periodic refresh logs:
```
📊 Refreshing stock levels from API...
  📦 Refreshing stock for 42 products
  ✅ Fetched 42 products from API
    ✏️ Ice talk blue lemon: 13 → 10
  ✅ Updated 3 cache entries
  ✅ Updated current view with fresh stock data
```

If you don't see these logs every 5 minutes:
1. Check that interval is set: `console.log(this.stockRefreshInterval)`
2. Check for errors in console
3. Verify `beforeUnmount()` isn't clearing interval prematurely

### Common Solutions

#### Solution 1: ID Type Mismatch

If product IDs are strings in cart but numbers in cache (or vice versa):

**Fix in useStockCache.js:**
```javascript
const updated = cached.map(product => {
  // Try both string and number versions
  const stockChange = stockChanges[product.id] || 
                      stockChanges[String(product.id)] ||
                      stockChanges[Number(product.id)]
  
  if (stockChange) {
    // ... update logic
  }
})
```

#### Solution 2: Force Consistent ID Format

**In apiProducts.js transformProductData():**
```javascript
return {
  id: String(productId),  // ← Force string
  // ... rest of fields
}
```

**In cart store addItem():**
```javascript
items.value.push({
  productId: String(product.id),  // ← Force string
  // ... rest of fields
})
```

#### Solution 3: Wait for Cache to Populate

If testing immediately after opening app:
1. Open NewOrder page
2. Click through a few categories
3. Wait for products to load (check localStorage)
4. Then try a transaction

### Testing Checklist

- [ ] Console shows "Calling stockCache.updateStockAfterSale()"
- [ ] Console shows cart items structure
- [ ] Console shows stock changes object
- [ ] Console shows cache keys found (> 0)
- [ ] Console shows products being updated
- [ ] Console shows "Updated X cache entries" (X > 0)
- [ ] localStorage shows updated stock values
- [ ] NewOrder page shows updated stock after refresh
- [ ] Stock decreases by exact amount purchased

### Still Not Working?

If stock still doesn't update:

1. **Share console logs** - Copy all logs from checkout through stock update
2. **Check localStorage** - Export `newOrder_products:*` entries
3. **Verify API** - Check if backend actually decreased stock
4. **Compare IDs** - Show cart product ID vs cached product ID side-by-side

### Quick Test Script

Run this in console after checkout:

```javascript
// Check if cache was updated
const cacheKeys = Object.keys(localStorage).filter(k => k.startsWith('newOrder_products:'))
console.log('Cache keys:', cacheKeys)

cacheKeys.forEach(key => {
  const data = JSON.parse(localStorage.getItem(key))
  console.log(`\n${key}:`)
  console.log('Cached at:', new Date(data.timestamp).toLocaleString())
  console.log('Products:', data.value.map(p => ({
    name: p.name,
    id: p.id,
    stock: p.stock
  })))
})
```

---

## Need More Help?

If you've gone through all steps and stock still doesn't update, provide:

1. Complete console logs from checkout
2. Screenshot of localStorage newOrder_products entries  
3. Cart item structure (console.log)
4. Cached product structure (localStorage)
5. Any error messages

This will help identify the exact issue.

