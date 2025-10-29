// useBarcode Composable
// Provides barcode scanning functionality for POS system
import { ref, computed } from 'vue'
import { api } from '@/services/api.js'
import productsAPI from '@/services/apiProducts.js'

/**
 * useBarcode Composable
 * Manages barcode scanning, product lookup, and automatic cart addition
 * Used in NewOrder component for seamless barcode scanning experience
 */
export function useBarcode() {
  // ================================================================
  // API INSTANCE
  // ================================================================
  
  // productsAPI is already an instance from the import
  
  // ================================================================
  // LOCAL STORAGE SEARCH
  // ================================================================
  
  /**
   * Search for products by barcode in local storage
   * @param {string} barcode - The barcode to search for
   * @returns {Promise<Array>} Array of matching products
   */
  const searchLocalStorageByBarcode = async (barcode) => {
    try {
      console.log('🔍 Searching localStorage for barcode:', barcode)
      
      const results = []
      
      // Search through all localStorage keys that contain product data
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        
        // Skip non-product keys
        if (!key || !key.startsWith('products:')) continue
        
        try {
          const cached = JSON.parse(localStorage.getItem(key))
          
          if (Array.isArray(cached)) {
            // Search through products in this cache entry
            const matches = cached.filter(product => 
              product.barcode === barcode || 
              product.SKU === barcode ||
              product.sku === barcode
            )
            
            if (matches.length > 0) {
              console.log(`✅ Found ${matches.length} matches in cache key: ${key}`)
              results.push(...matches)
            }
          }
        } catch (error) {
          // Skip invalid JSON entries
          continue
        }
      }
      
      console.log(`🔍 Local storage search complete: ${results.length} matches`)
      return results
      
    } catch (error) {
      console.warn('Local storage search failed:', error.message)
      return []
    }
  }
  
  // ================================================================
  // REACTIVE STATE
  // ================================================================
  
  // Scanner state
  const isScanning = ref(false)
  const isProcessing = ref(false)
  const lastScannedCode = ref('')
  
  // Results and feedback
  const scanResult = ref(null)
  const scanError = ref(null)
  const scanSuccess = ref(false)
  
  // Configuration
  const scanTimeout = ref(3000) // 3 seconds timeout for processing
  const autoAddToCart = ref(true) // Automatically add found products to cart
  const showNotifications = ref(true) // Show success/error notifications
  
  // ================================================================
  // COMPUTED PROPERTIES
  // ================================================================
  
  const isReady = computed(() => !isScanning.value && !isProcessing.value)
  
  const hasRecentScan = computed(() => {
    return lastScannedCode.value && 
           Date.now() - (scanResult.value?.timestamp || 0) < 5000 // 5 seconds
  })
  
  // ================================================================
  // CORE SCANNING METHODS
  // ================================================================
  
  /**
   * Start barcode scanning mode
   * Sets up keyboard listener for barcode scanner input
   */
  const startScanning = () => {
    if (isScanning.value) return
    
    console.log('🔍 Starting barcode scanning mode')
    isScanning.value = true
    scanError.value = null
    scanSuccess.value = false
    
    // Set up keyboard listener for barcode scanner
    document.addEventListener('keydown', handleBarcodeInput)
    
    console.log('✅ Barcode scanner is now always listening')
  }
  
  /**
   * Stop barcode scanning mode
   */
  const stopScanning = () => {
    if (!isScanning.value) return
    
    // console.log('🛑 Stopping barcode scanning mode')
    isScanning.value = false
    
    // Remove keyboard listener
    document.removeEventListener('keydown', handleBarcodeInput)
  }
  
  /**
   * Handle barcode input from scanner or manual entry
   * @param {Event} event - Keyboard event
   */
  const handleBarcodeInput = (event) => {
    // Ignore if not in scanning mode
    if (!isScanning.value) return
    
    // Debug: Log all key presses to see if scanner is working
    console.log('🔍 Key pressed:', event.key, 'Type:', event.key.length)
    
    // Barcode scanners typically send Enter key after the code
    if (event.key === 'Enter') {
      event.preventDefault()
      
      // Get the barcode from the input field that was focused
      const activeElement = document.activeElement
      if (activeElement && activeElement.type === 'text') {
        const barcode = activeElement.value.trim()
        if (barcode) {
          console.log('>>', barcode)
          processBarcode(barcode)
          activeElement.value = '' // Clear the input
          console.log('←', barcode)
        }
      }
    }
    
    // Also handle direct barcode scanner input (when no input field is focused)
    // Barcode scanners often send characters rapidly followed by Enter
    if (event.key !== 'Enter' && event.key.length === 1) {
      // If we're not in an input field, start collecting barcode characters
      if (!document.activeElement || document.activeElement.type !== 'text') {
        event.preventDefault()
        
        // Start collecting barcode characters
        if (!window.barcodeBuffer) {
          window.barcodeBuffer = ''
        }
        
        window.barcodeBuffer += event.key
        
        // Clear buffer after 1 second of inactivity
        clearTimeout(window.barcodeTimeout)
        window.barcodeTimeout = setTimeout(() => {
          if (window.barcodeBuffer && window.barcodeBuffer.length > 3) {
            console.log('>>', window.barcodeBuffer)
            processBarcode(window.barcodeBuffer)
            console.log('←', window.barcodeBuffer)
          }
          window.barcodeBuffer = ''
        }, 100)
      }
    }
  }
  
  /**
   * Process scanned barcode
   * @param {string} barcode - The scanned barcode
   */
  const processBarcode = async (barcode) => {
    if (!barcode || isProcessing.value) return
    
    console.log('📦 Processing barcode:', barcode)
    
    try {
      isProcessing.value = true
      scanError.value = null
      scanSuccess.value = false
      lastScannedCode.value = barcode
      
      // Search for product by barcode/SKU
      const product = await findProductByBarcode(barcode)
      
      if (product) {
        scanResult.value = {
          product,
          barcode,
          timestamp: Date.now(),
          success: true
        }
        scanSuccess.value = true
        
        console.log('✅ Product found:', product.product_name || product.name)
        console.log('🛒 Product data:', product)
        console.log('🔍 Setting scanSuccess to true, scanResult:', scanResult.value)
        
        // Force trigger the cart addition by calling the watcher manually
        // This is a workaround for Vue reactivity issues
        setTimeout(() => {
          console.log('🔍 Manual trigger: scanSuccess is', scanSuccess.value)
          console.log('🔍 Manual trigger: scanResult is', scanResult.value)
          
          // Try to trigger the cart addition directly
          console.log('🔍 Attempting direct cart addition...')
          if (window.addToCartDirectly) {
            console.log('🔍 Calling window.addToCartDirectly')
            window.addToCartDirectly(product)
          } else {
            console.log('🔍 window.addToCartDirectly not available')
          }
        }, 100)
        
        // Return product for cart addition
        return product
        
      } else {
        console.warn('❌ Product not found for barcode:', barcode)
        scanError.value = `Product not found for barcode: ${barcode}`
        scanResult.value = {
          barcode,
          timestamp: Date.now(),
          success: false,
          error: `Product not found for barcode: ${barcode}`
        }
        return null
      }
      
    } catch (error) {
      console.error('❌ Barcode processing failed:', error)
      scanError.value = error.message
      scanResult.value = {
        barcode,
        timestamp: Date.now(),
        success: false,
        error: error.message
      }
      return null
      
    } finally {
      isProcessing.value = false
      // Keep scanner active - don't stop scanning
    }
  }
  
  /**
   * Find product by barcode/SKU
   * @param {string} barcode - The barcode to search for
   * @returns {Promise<Object|null>} Product object or null
   */
  const findProductByBarcode = async (barcode) => {
    try {
      console.log('🔍 Searching for product with barcode:', barcode)
      
      // Try multiple search strategies
      const searchStrategies = [
        // 1. Direct barcode search (if API supports it)
        () => searchByBarcode(barcode),
        
        // 2. Search by SKU
        () => searchBySku(barcode),
        
        // 3. General product search
        () => searchProducts(barcode)
      ]
      
      for (const strategy of searchStrategies) {
        try {
          const result = await strategy()
          if (result && result.length > 0) {
            // Return the first matching product
            const product = result[0]
            console.log('✅ Found product:', product.name)
            return product
          }
        } catch (error) {
          console.warn('Search strategy failed:', error.message)
          continue
        }
      }
      
      return null
      
    } catch (error) {
      console.error('❌ Product search failed:', error)
      throw error
    }
  }
  
  /**
   * Search products by barcode (if API supports it)
   * @param {string} barcode - The barcode
   * @returns {Promise<Array>} Search results
   */
  const searchByBarcode = async (barcode) => {
    try {
      // Search local storage first (much faster!)
      console.log('🔍 Searching local storage for barcode:', barcode)
      const localResults = await searchLocalStorageByBarcode(barcode)
      
      if (localResults.length > 0) {
        console.log('✅ Found product in local storage:', localResults[0].name)
        return localResults
      }
      
      // Fallback to backend API if not found locally
      console.log('🔍 Not found locally, trying backend API...')
      const response = await api.get(`/pos/barcode/${barcode}/`)
      const data = response.data
      
      console.log('🔍 Barcode endpoint response:', data)
      
      // Handle different response structures
      let product = null
      if (data && data.product && data.product._id) {
        product = data.product
      } else if (data && data._id) {
        product = data
      }
      
      if (product && product._id) {
        console.log('✅ Backend found product:', product.name || product.product_name)
        
        // Transform the product data to match our format
        const transformedProduct = {
          _id: product._id,
          id: product._id,
          name: product.name || product.product_name,
          product_name: product.product_name || product.name,
          price: product.price || product.selling_price || 0,
          selling_price: product.selling_price || product.price || 0,
          stock: product.total_stock || product.stock || 0,
          total_stock: product.total_stock || product.stock || 0,
          barcode: product.barcode || barcode,
          sku: product.sku || product.SKU || '',
          SKU: product.SKU || product.sku || '',
          category: product.category_id || product.category,
          category_id: product.category_id || product.category,
          subcategory: product.subcategory || product.subcategory_name,
          subcategory_name: product.subcategory_name || product.subcategory,
          is_taxable: product.is_taxable !== false,
          isTaxable: product.is_taxable !== false,
          image: product.image || product.image_url || '',
          originalData: product
        }
        
        console.log('🔍 Transformed barcode product:', transformedProduct)
        return [transformedProduct]
      }
      
      console.log('❌ Backend response structure issue:', {
        hasData: !!data,
        hasProduct: !!(data && data.product),
        hasId: !!(data && data._id),
        dataKeys: data ? Object.keys(data) : 'no data'
      })
      console.log('🔍 No product found for barcode:', barcode)
      return []
      
    } catch (error) {
      console.warn('Barcode search failed:', error.message)
      return []
    }
  }
  
  /**
   * Search products by SKU
   * @param {string} sku - The SKU
   * @returns {Promise<Array>} Search results
   */
  const searchBySku = async (sku) => {
    try {
      // Search by SKU using the general search endpoint
      const results = await productsAPI.searchProducts(sku)
      
      // Filter results that match the SKU exactly
      return results.filter(product => 
        product.SKU === sku || 
        product.sku === sku ||
        product.barcode === sku
      )
    } catch (error) {
      console.warn('SKU search failed:', error.message)
      return []
    }
  }
  
  /**
   * General product search
   * @param {string} query - Search query
   * @returns {Promise<Array>} Search results
   */
  const searchProducts = async (query) => {
    try {
      console.log('🔍 General search for query:', query)
      const results = await productsAPI.searchProducts(query)
      console.log('🔍 General search results:', results.length, 'products')
      console.log('🔍 General search results:', results)
      return results
    } catch (error) {
      console.warn('General search failed:', error.message)
      return []
    }
  }
  
  /**
   * Manual barcode entry
   * @param {string} barcode - Manually entered barcode
   */
  const enterBarcodeManually = (barcode) => {
    if (!barcode || !barcode.trim()) {
      scanError.value = 'Please enter a barcode'
      return
    }
    
    processBarcode(barcode.trim())
  }
  
  // ================================================================
  // UTILITY METHODS
  // ================================================================
  
  /**
   * Clear scan results and errors
   */
  const clearResults = () => {
    scanResult.value = null
    scanError.value = null
    scanSuccess.value = false
    lastScannedCode.value = ''
  }
  
  /**
   * Reset scanner to initial state
   */
  const reset = () => {
    stopScanning()
    clearResults()
    isProcessing.value = false
  }
  
  /**
   * Configure scanner settings
   * @param {Object} config - Configuration options
   */
  const configure = (config) => {
    if (config.autoAddToCart !== undefined) {
      autoAddToCart.value = config.autoAddToCart
    }
    if (config.showNotifications !== undefined) {
      showNotifications.value = config.showNotifications
    }
    if (config.scanTimeout !== undefined) {
      scanTimeout.value = config.scanTimeout
    }
  }
  
  /**
   * Get scanner status
   * @returns {Object} Current scanner status
   */
  const getStatus = () => {
    return {
      isScanning: isScanning.value,
      isProcessing: isProcessing.value,
      isReady: isReady.value,
      hasRecentScan: hasRecentScan.value,
      lastScannedCode: lastScannedCode.value,
      scanResult: scanResult.value,
      scanError: scanError.value,
      scanSuccess: scanSuccess.value
    }
  }
  
  // ================================================================
  // RETURN COMPOSABLE
  // ================================================================
  
  return {
    // State
    isScanning,
    isProcessing,
    isReady,
    scanResult,
    scanError,
    scanSuccess,
    lastScannedCode,
    hasRecentScan,
    
    // Configuration
    autoAddToCart,
    showNotifications,
    scanTimeout,
    
    // Core methods
    startScanning,
    stopScanning,
    processBarcode,
    enterBarcodeManually,
    
    // Utility methods
    clearResults,
    reset,
    configure,
    getStatus
  }
}
