import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCartStore = defineStore('cart', () => {
  // ================================================================
  // STATE
  // ================================================================
  
  const items = ref([])
  const cashierId = ref(null)
  const shiftId = ref(null)
  const discountAmount = ref(0)
  const discountType = ref(null)
  const discountDetails = ref({})
  
  // Tax configuration
  const TAX_RATE = 0.12
  
  // ================================================================
  // COMPUTED (Auto-calculated)
  // ================================================================
  
  const subtotal = computed(() => {
    return items.value.reduce((sum, item) => sum + item.subtotal, 0)
  })
  
  const taxableAmount = computed(() => {
    return items.value
      .filter(item => item.isTaxable !== false)
      .reduce((sum, item) => sum + item.subtotal, 0)
  })
  
  const taxAmount = computed(() => {
    const taxableAfterDiscount = Math.max(0, taxableAmount.value - discountAmount.value)
    return taxableAfterDiscount * TAX_RATE
  })
  
  const total = computed(() => {
    return subtotal.value - discountAmount.value + taxAmount.value
  })
  
  const itemCount = computed(() => {
    return items.value.reduce((sum, item) => sum + item.quantity, 0)
  })
  
  const isEmpty = computed(() => {
    return items.value.length === 0
  })
  
  // ================================================================
  // ACTIONS (Item Management)
  // ================================================================
  
  function initializeSession(cashier_id, shift_id) {
    cashierId.value = cashier_id
    shiftId.value = shift_id
    
    // Try to restore cart from localStorage
    const savedCart = localStorage.getItem('frontendCart')
    if (savedCart) {
      const parsed = JSON.parse(savedCart)
      items.value = parsed.items || []
      discountAmount.value = parsed.discountAmount || 0
      discountType.value = parsed.discountType || null
      discountDetails.value = parsed.discountDetails || {}
    }
  }
  
  function addItem(product) {
    console.log('🛒 Cart store - Adding item to cart:', product)
    console.log('🛒 Cart store - Current items count:', items.value.length)
    
    // Check if item already exists
    const existingItem = items.value.find(item => item.productId === product.id)
    
    if (existingItem) {
      existingItem.quantity += 1
      existingItem.subtotal = existingItem.price * existingItem.quantity
      console.log('   ➕ Increased quantity:', existingItem.quantity)
    } else {
      // ✅ ADD: Store category info with cart item
      const newItem = {
        productId: product.id,
        productName: product.name,
        sku: product.sku || '',
        price: product.price,
        quantity: 1,
        subtotal: product.price,
        isTaxable: product.isTaxable !== false,
        image: product.image,
        category: product.category,  // ✅ Store category
        subcategory: product.subcategory,  // ✅ Store subcategory
        addedAt: new Date().toISOString()
      }
      
      items.value.push(newItem)
      console.log('   ✅ New item added:', newItem)
      console.log('   ✅ Cart items after adding:', items.value.length)
    }
    
    saveToLocalStorage()
    console.log('🛒 Cart store - Final items count:', items.value.length)
  }
  
  function removeItem(productId) {
    items.value = items.value.filter(item => item.productId !== productId)
    saveToLocalStorage()
  }
  
  function updateQuantity(productId, newQuantity) {
    const item = items.value.find(item => item.productId === productId)
    
    if (!item) return
    
    if (newQuantity <= 0) {
      removeItem(productId)
    } else {
      item.quantity = newQuantity
      item.subtotal = item.price * newQuantity
      saveToLocalStorage()
    }
  }
  
  function increaseQuantity(productId) {
    const item = items.value.find(item => item.productId === productId)
    if (item) {
      item.quantity += 1
      item.subtotal = item.price * item.quantity
      saveToLocalStorage()
    }
  }
  
  function decreaseQuantity(productId) {
    const item = items.value.find(item => item.productId === productId)
    if (item) {
      if (item.quantity > 1) {
        item.quantity -= 1
        item.subtotal = item.price * item.quantity
        saveToLocalStorage()
      } else {
        removeItem(productId)
      }
    }
  }
  
  function clearCart() {
    items.value = []
    discountAmount.value = 0
    discountType.value = null
    discountDetails.value = {}
    localStorage.removeItem('frontendCart')
  }
  
  // ================================================================
  // DISCOUNT MANAGEMENT
  // ================================================================
  
  function applyDiscount(type, value, details = {}) {
    discountType.value = type
    discountDetails.value = details
    
    if (type === 'percentage') {
      discountAmount.value = (subtotal.value * value) / 100
    } else if (type === 'fixed') {
      discountAmount.value = Math.min(value, subtotal.value)
    } else if (type === 'promotion') {
      discountAmount.value = value
    }
    
    saveToLocalStorage()
  }
  
  function removeDiscount() {
    discountAmount.value = 0
    discountType.value = null
    discountDetails.value = {}
    saveToLocalStorage()
  }
  
  // ================================================================
  // PERSISTENCE
  // ================================================================
  
  function saveToLocalStorage() {
    const cartData = {
      items: items.value,
      discountAmount: discountAmount.value,
      discountType: discountType.value,
      discountDetails: discountDetails.value,
      savedAt: new Date().toISOString()
    }
    localStorage.setItem('frontendCart', JSON.stringify(cartData))
  }
  
  // ================================================================
  // CHECKOUT PREPARATION
  // ================================================================
  
  function getCheckoutData() {
    return {
      items: items.value.map(item => ({
        product_id: item.productId,
        product_name: item.productName,
        sku: item.sku,
        quantity: item.quantity,
        unit_price: item.price,
        subtotal: item.subtotal,
        is_taxable: item.isTaxable
      })),
      subtotal: subtotal.value,
      tax_amount: taxAmount.value,
      discount_amount: discountAmount.value,
      total_amount: total.value,
      cashier_id: cashierId.value,
      shift_id: shiftId.value,
      discount_type: discountType.value,
      discount_details: discountDetails.value
    }
  }
  
  return {
    // State
    items,
    cashierId,
    shiftId,
    discountAmount,
    discountType,
    discountDetails,
    
    // Computed
    subtotal,
    taxAmount,
    total,
    itemCount,
    isEmpty,
    
    // Actions
    initializeSession,
    addItem,
    removeItem,
    updateQuantity,
    increaseQuantity,
    decreaseQuantity,
    clearCart,
    applyDiscount,
    removeDiscount,
    getCheckoutData
  }
})