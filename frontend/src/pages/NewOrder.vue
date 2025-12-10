<template>
  <div class="new-order-page page-container transition-theme">
    <!-- Main Content Area -->
    <div class="main-area content-container with-sidebar">
      <div class="no-contents surface-primary text-primary transition-theme">
        <!-- Header Section -->
        <div class="no-header header-theme">
          <div class="category-search surface-primary border-bottom-theme transition-theme">
            <input 
              type="text" 
              v-model="categorySearch" 
              placeholder="Search products..." 
              class="search-input input-complete focus-ring-theme"
            />
            <button 
              class="refresh-stock-btn btn-complete focus-ring-theme" 
              @click="manualStockRefresh"
              :disabled="isRefreshingStock"
              title="Refresh stock levels"
            >
              <RefreshCw :size="18" :class="{ 'spinning': isRefreshingStock }" />
              <span v-if="!isRefreshingStock">Refresh</span>
              <span v-else>Refreshing...</span>
            </button>
            
          </div>
          
          <!-- Categories -->
          <div class="header-bot surface-secondary transition-theme">
            <div class="categories-container">
              <div 
                v-for="category in categories" 
                :key="category.id"
                :class="['cat-card card-complete hover-lift', { active: activeCategory === category.id }]"
                @click="selectCategory(category.id)">
                <div class="cat-icon">
                  <component :is="category.icon" />
                </div>
                <span class="cat-label">{{ category.name }}</span>
                <button 
                  v-if="category.isCustom"
                  class="delete-category-btn btn-complete"
                  @click.stop="deleteCategory(category.id)"
                  title="Delete Page">
                  <X :size="12" />
                </button>
              </div>
              
              <!-- Add Page Button -->
              <div class="cat-card add-category card-complete hover-lift" @click="showCategoryModal = true">
                <div class="cat-icon">
                  <Plus :size="24" />
                </div>
                <span class="cat-label">Add Page</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Navigation Breadcrumbs -->
        <div v-if="breadcrumbs.length > 0" class="breadcrumb-nav surface-secondary border-bottom-theme transition-theme">
          <button 
            v-for="(crumb, index) in breadcrumbs" 
            :key="index"
            class="breadcrumb-item nav-link-theme hover-surface focus-ring-theme"
            @click="navigateTo(crumb)">
            {{ crumb.name }}
            <ChevronRight v-if="index < breadcrumbs.length - 1" :size="16" />
          </button>
        </div>

        <!-- Manual Barcode Input (Always Available) -->
        <div class="manual-barcode-input-section surface-secondary border-bottom-theme transition-theme">
          <div class="barcode-input-container">
            <label class="barcode-label">Manual Barcode Entry:</label>
            <div class="barcode-input-group">
              <input 
                type="text" 
                v-model="manualBarcodeInput"
                placeholder="Enter barcode manually or scan with barcode scanner..."
                class="barcode-input input-complete focus-ring-theme"
                @keyup.enter="processManualBarcode"
                ref="barcodeInput"
              />
              <button 
                class="process-barcode-btn btn-primary btn-complete"
                @click="processManualBarcode"
                :disabled="!manualBarcodeInput.trim() || barcodeScanner.isProcessing"
              >
                Add Product
              </button>
            </div>
          </div>
        </div>
        

        <!-- Loading State -->
        <div v-if="loading || productsLoading" class="loading-state text-secondary">
          <div class="spinner"></div>
          <p>Loading...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state status-error">
          <p class="error-message">{{ error }}</p>
          <button class="btn-primary btn-complete" @click="retryLoad">Retry</button>
        </div>

        <!-- Products Grid with Infinite Scroll -->
        <div v-else class="products-grid" @scroll="handleProductsScroll">
          <div 
            v-for="product in paginatedProducts" 
            :key="product.id"
            :class="['product-card card-complete hover-lift transition-theme', { 'sold-out': !product.isSubcategory && (product.total_stock === null || product.total_stock <= 0) }]"
            @click="handleProductClick(product)">
            <!-- Sold Out Overlay -->
            <div v-if="!product.isSubcategory && (product.total_stock === null || product.total_stock <= 0)" class="sold-out-overlay">
              <div class="sold-out-badge">SOLD OUT</div>
              
              <!-- Hover Tooltip for Sold Out Products -->
              <div class="sold-out-tooltip">
                <div class="tooltip-content">
                  <div class="tooltip-header">
                    <h4 class="tooltip-title">{{ product.name }}</h4>
                    <div class="tooltip-price">₱{{ formatPrice(product.price) }}</div>
                  </div>
                  <div class="tooltip-details">
                    <div class="tooltip-stock">
                      <span class="stock-label">Stock:</span>
                      <span class="stock-value">{{ product.total_stock || 0 }}</span>
                    </div>
                    <div class="tooltip-description">
                      <small>This item is currently out of stock</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="product-image">
              <img 
                :src="product.image" 
                :alt="product.name" 
                loading="lazy"
                @error="handleImageError($event, product)"
                @load="handleImageLoad($event)"
              />
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <p v-if="!product.isSubcategory" class="product-description">
                Stock: {{ product.stock || 0 }}
              </p>
              <div v-if="!product.isSubcategory" class="product-price text-accent">
                ₱{{ formatPrice(product.price) }}
              </div>
              <div v-else class="subcategory-indicator text-accent">
                <ChevronRight :size="16" /> View Items
              </div>
            </div>
            <button 
              v-if="!product.isSubcategory && isCustomCategory" 
              class="delete-product-btn btn-complete" 
              @click.stop="removeFromCategory(product.id)" 
              title="Remove from page">
              <X :size="14" />
            </button>
          </div>
          
          <!-- Add Products Option (Custom Categories Only) -->
          <div 
            v-if="viewMode === 'products' && isCustomCategory && customCategoryItems.length < 8"
            class="product-card add-item-card card-complete hover-lift"
            @click="openProductSelectorModal()">
            <div class="add-item-content">
              <ShoppingBag :size="32" />
              <p>Add Products</p>
              <small>{{ allAvailableProductsCount }} available</small>
            </div>
          </div>
          
          <!-- Loading More Indicator -->
          <div v-if="hasMoreItems && paginatedProducts.length > 0" class="load-more-indicator text-secondary">
            <p>Scroll for more...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Page Creation Modal -->
    <div v-if="showCategoryModal" class="modal-overlay modal-overlay-theme" @click="closeCategoryModal">
      <div class="modal-content modal-theme transition-theme" @click.stop>
        <div class="modal-header header-theme">
          <h3>Create New Page</h3>
          <button class="close-btn btn-complete" @click="closeCategoryModal">
            <X :size="20" />
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Page Name</label>
            <input 
              type="text" 
              v-model="newCategory.name" 
              placeholder="Enter page name"
              class="form-input input-complete focus-ring-theme"
              maxlength="20"
            />
          </div>
          <div class="form-group">
            <label>Icon</label>
            <div class="icon-selector">
              <button 
                v-for="iconOption in iconOptions" 
                :key="iconOption.name"
                type="button"
                :aria-pressed="newCategory.icon === iconOption.name"
                :class="[
                  'icon-option card-complete hover-lift',
                  newCategory.icon === iconOption.name ? 'state-selected border-theme-accent text-accent selected' : ''
                ]"
                @click.stop.prevent="selectIcon(iconOption.name)">
                <component :is="iconOption.name" :size="20" />
              </button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary btn-complete" @click="closeCategoryModal">Cancel</button>
          <button 
            class="btn-primary btn-complete" 
            @click="createCategory" 
            :disabled="!newCategory.name.trim()">
            Create Page
          </button>
        </div>
      </div>
    </div>

    <!-- Product Selection Modal -->
    <div v-if="showProductSelectorModal" class="modal-overlay modal-overlay-theme" @click="closeProductSelectorModal">
      <div class="modal-content large-modal modal-theme transition-theme" @click.stop>
        <div class="modal-header header-theme">
          <h3>Add Products to {{ getCurrentCategoryName() }}</h3>
          <button class="close-btn btn-complete" @click="closeProductSelectorModal">
            <X :size="20" />
          </button>
        </div>
        <div class="modal-body">
          <!-- Category Tabs -->
          <div class="product-selector-tabs">
            <button 
              v-for="category in availableSourceCategories" 
              :key="category.id"
              :class="['tab-btn nav-link-theme hover-surface', { active: selectedSourceCategory === category.id }]"
              @click="selectedSourceCategory = category.id">
              {{ category.name }} ({{ productCountsByCategory[category.id] || 0 }})
            </button>
          </div>
          
          <!-- Search -->
          <div class="product-search">
            <input 
              type="text" 
              v-model="productSearchQuery" 
              placeholder="Search products..."
              class="search-input input-complete focus-ring-theme"
            />
          </div>
          
          <!-- Loading State -->
          <div v-if="productsLoading" class="loading-state text-secondary">
            <p>Loading products...</p>
          </div>
          
          <!-- Product Selection Grid -->
          <div v-else class="product-selection-grid">
            <div 
              v-for="product in availableProductsForSelection" 
              :key="product.id"
              :class="['selectable-product', { 
                selected: selectedProducts.includes(product.id),
                'already-added': isProductAlreadyInCategory(product.id)
              }]"
              @click="toggleProductSelection(product)">
              <div class="product-image-small">
                <img 
                  :src="product.image" 
                  :alt="product.name" 
                  loading="lazy"
                  @error="handleImageError($event, product)"
                />
              </div>
              <div class="product-details">
                <h4>{{ product.name }}</h4>
                <p>₱{{ formatPrice(product.price) }}</p>
                <small v-if="isProductAlreadyInCategory(product.id)" class="already-added-text">
                  Already added
                </small>
              </div>
              <div class="selection-indicator">
                <div v-if="selectedProducts.includes(product.id)" class="checkmark">
                  ✓
                </div>
              </div>
            </div>
          </div>
          
          <!-- Selection Summary -->
          <div v-if="selectedProducts.length > 0" class="selection-summary">
            <p>{{ selectedProducts.length }} product(s) selected</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary btn-complete" @click="closeProductSelectorModal">Cancel</button>
          <button 
            class="btn-primary btn-complete" 
            @click="addSelectedProductsToCategory" 
            :disabled="selectedProducts.length === 0 || wouldExceedLimit">
            Add {{ selectedProducts.length }} Products
            <span v-if="wouldExceedLimit" class="error-text">
              (Exceeds 8 item limit)
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- Shopping Cart Sidebar -->
    <div class="cart-sidebar sidebar-theme transition-theme">
      <div class="cart-header header-theme">
        <h2>New Order</h2>
        <button class="cart-close btn-complete" @click="closeCart">
          <X :size="20" />
        </button>
      </div>
      
      <div class="cart-items">
        <div v-if="cartItems.length === 0" class="empty-cart-message text-secondary">
          <ShoppingCart :size="48" class="empty-cart-icon" />
          <p>Your cart is empty</p>
          <p>Add items to get started!</p>
        </div>
        
        <div v-for="item in cartItems" :key="item.productId" class="cart-item surface-secondary border-theme-subtle transition-theme">
          <img :src="item.image" :alt="item.productName" class="cart-item-image" />
          <div class="cart-item-info">
            <h4>{{ item.productName }}</h4>
            <p class="item-price">₱{{ formatPrice(item.price) }}</p>
          </div>
          <div class="cart-item-controls">
            <button 
              @click="decreaseQuantity(item)" 
              class="quantity-btn minus btn-complete">
              <Minus :size="16" />
            </button>
            <span class="quantity">{{ item.quantity }}</span>
            <button 
              @click="increaseQuantity(item)" 
              class="quantity-btn plus btn-complete">
              <Plus :size="16" />
            </button>
          </div>
          <div class="cart-item-subtotal">
            ₱{{ formatPrice(item.subtotal) }}
          </div>
          <button 
            @click="removeFromCart(item)" 
            class="remove-btn btn-complete">
            <Trash2 :size="16" />
          </button>
        </div>
      </div>
      
      <!-- Cart Footer -->
      <div class="cart-footer surface-primary border-top-theme transition-theme">
        
        <!-- Cart Summary -->
        <div class="cart-summary card-elevated transition-theme">
          <!-- Subtotal -->
          <div class="cart-info">
            <div class="item-count">{{ totalItems }} items</div>
            <div class="cart-total">₱{{ formatPrice(finalTotal) }}</div>
          </div>
          
          <!-- Promo Discount -->
          <div v-if="promoDiscount > 0" class="discounts-section">
          </div>
          
          <button 
            class="pay-btn btn-complete focus-ring-theme" 
            @click="checkout"
            :disabled="cartItems.length === 0">
            <span>Checkout →</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Shift Required Modal -->
    <Teleport to="body">
      <div 
        v-if="showShiftRequiredModal"
        class="modal-overlay"
        @click.self="showShiftRequiredModal = false"
      >
        <div class="shift-modal">
          <div class="shift-modal-header">
            <div class="shift-modal-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            <h3 class="shift-modal-title">Shift Required</h3>
            <p class="shift-modal-message">
              You need to start a shift before placing a sale. Would you like to go to the Shift page now?
            </p>
          </div>
          
          <div class="shift-modal-footer">
            <button 
              class="shift-modal-btn shift-modal-btn-cancel" 
              @click="showShiftRequiredModal = false"
            >
              Cancel
            </button>
            <button 
              class="shift-modal-btn shift-modal-btn-primary" 
              @click="goToShiftPage"
            >
              Go to Shift
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import { useCartStore } from '@/stores/cartStores'
import categoriesAPI from '@/services/apiCategory.js'
import productsAPI from '@/services/apiProducts.js'
import apiService, { api } from '@/services/api.js'
import { useStockCache } from '@/composables/data/useStockCache.js'
import { useBarcode } from '@/composables/useBarcode.js'
import { RefreshCw } from 'lucide-vue-next'

export default {
  name: 'NewOrder',
  
  setup() {
    const cartStore = useCartStore()
    const stockCache = useStockCache()
    const barcodeScanner = useBarcode()
    return { cartStore, stockCache, barcodeScanner }
  },
  
  data() {
    return {
      // Loading and error states
      loading: false,
      productsLoading: false,
      error: null,
      
      // Categories (backend + custom)
      backendCategories: [],
      customCategories: [],
      activeCategory: null,
      
      // Products
      products: [],
      customCategoryProducts: {},
      allProducts: [],
      
      // Cart UI state - always visible now
      showCart: true,
      
      // Modal states
      showCategoryModal: false,
      showProductSelectorModal: false,
      showShiftRequiredModal: false,
      
      // Navigation state
      viewMode: 'products',
      currentSubcategory: null,
      categorySearch: '',
      breadcrumbs: [],
      
      // Infinite scroll
      displayedItemsCount: 38,
      itemsPerLoad: 12,
      
      // Custom category creation - will be loaded from localStorage
      nextCategoryId: 100,
      nextProductId: 1000,
      newCategory: {
        name: '',
        icon: 'Package'
      },
      
      // Product selection for custom categories
      selectedSourceCategory: null,
      selectedProducts: [],
      productSearchQuery: '',
      
      
      // Icon options for custom categories
      iconOptions: [
        { name: 'Package' },
        { name: 'Coffee' },
        { name: 'Pizza' },
        { name: 'Cake' },
        { name: 'Sandwich' },
        { name: 'IceCream' },
        { name: 'Cookie' },
        { name: 'Soup' },
        { name: 'ShoppingBag' },
        { name: 'Utensils' }
      ],
      
      // Barcode scanning
      manualBarcodeInput: '',
    }
  },

  async mounted() {
    
    // Check if returning from checkout
    const shouldRefreshStock = sessionStorage.getItem('refreshStockAfterCheckout')
    if (shouldRefreshStock === 'true') {
      sessionStorage.removeItem('refreshStockAfterCheckout')
    }
    
    // Read targeted product IDs to refresh (set by checkout/payment callback)
    let targetedProductIds = []
    try {
      const raw = sessionStorage.getItem('refreshProductIds')
      if (raw) {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed) && parsed.length > 0) {
          targetedProductIds = [...new Set(parsed)]
        }
      }
    } catch (_) {}
    
    // Load custom categories and products from localStorage
    this.loadCustomCategories()
    this.loadCustomCategoryProducts()
    this.loadIdCounters()
    
    await this.initializeSession()
    await this.loadCategories()
    
    // Start barcode scanner automatically
    this.startBarcodeScanner()
    
    // Set up global function for direct cart addition
    window.addToCartDirectly = (product) => {
      this.addToCart(product)
    }
    
    // If returning from checkout, refresh specific products
    if (shouldRefreshStock === 'true') {
      try {
        if (targetedProductIds.length > 0) {
          await this.refreshSpecificStockLevels(targetedProductIds)
        } else {
          // Reload current category
          if (this.activeCategory) {
            await this.loadProductsForCategory(this.activeCategory, this.currentSubcategory?.name)
          }
        }
      } finally {
        try { sessionStorage.removeItem('refreshProductIds') } catch (_) {}
      }
    }
  },

  beforeUnmount() {
    // Stop barcode scanner
    this.barcodeScanner.stopScanning()
  },

  watch: {
    
    // Watch barcode scanner results
    'barcodeScanner.scanSuccess': {
      handler(newVal, oldVal) {
        if (newVal && this.barcodeScanner.scanResult?.product) {
          this.watchBarcodeResults()
        }
      }
    },
    
    // Watch cart items
    'cartStore.items': {
      handler(newItems, oldItems) {
        this.watchCartItems()
      },
      deep: true
    }
  },

  computed: {
    // Combine backend and custom categories
    categories() {
      return [...this.backendCategories, ...this.customCategories]
    },

    // Cart items from store
    cartItems() {
      return this.cartStore.items
    },
    
    // Cart subtotal (without tax)
    cartSubtotal() {
      return this.cartStore.subtotal
    },
    
    // Total items from store
    totalItems() {
      return this.cartStore.itemCount
    },
    
    // Final total (no promotions in New Order page)
    finalTotal() {
      return this.cartSubtotal
    },

    filteredProducts() {
      if (this.viewMode === 'subcategories') {
        const category = this.categories.find(cat => cat.id === this.activeCategory)
        if (category && category.subcategories) {
          return category.subcategories.map(sub => ({
            id: sub.id,
            name: sub.name,
            description: `${sub.productCount} items available`,
            price: '',
            image: this.generateSubcategoryImage(sub.name),
            isSubcategory: true,
            subcategoryData: sub
          }))
        }
        return []
      }
      
      let products
      
      if (this.isCustomCategory) {
        products = this.customCategoryProducts[this.activeCategory] || []
      } else {
        products = this.products
      }
      
      if (this.categorySearch.trim()) {
        products = products.filter(product => 
          product.name.toLowerCase().includes(this.categorySearch.toLowerCase())
        )
      }
      
      // Sort products: in-stock first, sold-out last
      return products.sort((a, b) => {
        const aInStock = a.total_stock !== null && a.total_stock > 0
        const bInStock = b.total_stock !== null && b.total_stock > 0
        
        if (aInStock === bInStock) return 0
        return aInStock ? -1 : 1
      })
    },

    paginatedProducts() {
      if (this.viewMode === 'subcategories') {
        return this.filteredProducts
      }
      
      // Return items up to displayedItemsCount for infinite scroll
      return this.filteredProducts.slice(0, this.displayedItemsCount)
    },

    hasMoreItems() {
      return this.displayedItemsCount < this.filteredProducts.length
    },

    isCustomCategory() {
      const category = this.categories.find(cat => cat.id === this.activeCategory)
      return category && category.isCustom
    },

    customCategoryItems() {
      return this.filteredProducts
    },

    availableSourceCategories() {
      return this.backendCategories.filter(cat => cat.id !== this.activeCategory)
    },

    availableProductsForSelection() {
      let products = this.allProducts.filter(product => 
        product.category === this.selectedSourceCategory
      )
      
      if (this.productSearchQuery.trim()) {
        products = products.filter(product => 
          product.name.toLowerCase().includes(this.productSearchQuery.toLowerCase())
        )
      }
      
      return products
    },

    allAvailableProductsCount() {
      const currentCategoryProducts = this.customCategoryProducts[this.activeCategory] || []
      const currentProductIds = currentCategoryProducts.map(p => p.originalId || p.id)
      
      return this.allProducts.filter(p => !currentProductIds.includes(p.id)).length
    },

    wouldExceedLimit() {
      return this.customCategoryItems.length + this.selectedProducts.length > 8
    },

    // Count products by category for the product selector modal
    productCountsByCategory() {
      const counts = {}

      // Count products in each category
      this.allProducts.forEach(product => {
        if (product.category) {
          counts[product.category] = (counts[product.category] || 0) + 1
        }
      })

      return counts
    }
  },

  methods: {
    selectIcon(iconName) {
      this.newCategory.icon = iconName
    },
    
    // Image handlers and fallback for robustness
    handleImageLoad(event) {
      const img = event?.target
      if (img) img.dataset.loaded = 'true'
    },
    handleImageError(event, product) {
      const img = event?.target
      if (!img) return
      img.onerror = null
      const name = product?.name || 'Product'
      img.src = this.getFallbackProductImage(name)
    },
    
    // ================================================================
    // STOCK REFRESH
    // ================================================================
    
    async manualStockRefresh() {
      try {
        this.isRefreshingStock = true
        
        // Trigger startup sync (same as server startup)
        const syncAPI = await import('../services/apiSync.js')
        const result = await syncAPI.default.triggerStartupSync()
        
        if (result.success) {
          // Reload current category products with fresh data
          if (this.activeCategory) {
            await this.loadProductsForCategory(this.activeCategory, this.currentSubcategory?.name)
          }
          
          // Show success message
          const totalSynced = (result.data?.products?.total_synced || 0) + (result.data?.batches?.total_synced || 0)
          const stockUpdates = result.data?.stock_updates || 0
          
          if (totalSynced > 0 || stockUpdates > 0) {
            console.log(`✓ Sync complete: ${totalSynced} items synced, ${stockUpdates} products updated`)
          }
        }
      } catch (error) {
        console.error('Stock refresh error:', error)
        // Still try to reload products even if sync fails
        if (this.activeCategory) {
          try {
            await this.loadProductsForCategory(this.activeCategory, this.currentSubcategory?.name)
          } catch (e) {
            alert('Failed to refresh stock levels. Please try again.')
          }
        }
      } finally {
        this.isRefreshingStock = false
      }
    },
    
    async refreshSpecificStockLevels(productIds) {
      try {
        const uniqueIds = Array.from(new Set((productIds || []).filter(Boolean)))
        if (uniqueIds.length === 0) {
          return
        }
        
        // Fetch fresh data
        const freshProducts = await productsAPI.getProductsBatch(uniqueIds)
        if (!Array.isArray(freshProducts) || freshProducts.length === 0) {
          return
        }
        
        // Build updates map
        const stockUpdates = {}
        freshProducts.forEach(product => {
          const stockValue = product.total_stock !== undefined ? product.total_stock : product.batch_stock
          if (product.id) {
            stockUpdates[product.id] = stockValue
          }
        })
        
        // Update current in-memory view (products)
        if (Array.isArray(this.products) && this.products.length > 0) {
          this.products = this.products.map(p => {
            const newStock = stockUpdates[p.id]
            return newStock !== undefined ? { ...p, stock: newStock, total_stock: newStock } : p
          })
        }
        
        // Update custom category products with fresh stock data
        this.updateCustomCategoryProductsStock(stockUpdates)
        
      } catch (error) {
        // Targeted stock refresh failed
      }
    },
    
    // ================================================================
    // INITIALIZATION
    // ================================================================
    
    async initializeSession() {
      try {
        const userData = JSON.parse(localStorage.getItem('userData') || '{}')
        const cashierId = userData.user_id || userData.id || userData._id
        
        if (!cashierId) {
          throw new Error('No cashier ID found. Please log in again.')
        }
        
        const shiftId = localStorage.getItem('activeShiftId') || null
        this.cartStore.initializeSession(cashierId, shiftId)
        
      } catch (error) {
        this.error = error.message
        alert(`Failed to initialize session: ${error.message}\n\nPlease refresh the page or log in again.`)
      }
    },

    // FIX: Load ALL products when modal opens
    async openProductSelectorModal() {
      this.showProductSelectorModal = true
      
      // Always load products from all available categories
      await this.loadAllProductsForSelection()
      
      // Then select the first category
      if (this.availableSourceCategories.length > 0) {
        this.selectedSourceCategory = this.availableSourceCategories[0].id
      }
    },

    // FIX: New method to load all products at once
    async loadAllProductsForSelection() {
      try {
        this.productsLoading = true
        
        // Load from ALL available source categories (excluding current active category)
        // Fetch products directly from API
        const productPromises = this.availableSourceCategories.map(category => {
          return productsAPI.getProductsByCategory(category.id)
        })
        
        // Wait for all requests to complete
        const allCategoryProducts = await Promise.all(productPromises)
        
        // Flatten all products into a single array and filter valid entries
        this.allProducts = allCategoryProducts.flat().filter(p => p && typeof p === 'object')
        
      } catch (error) {
        this.error = error.message
      } finally {
        this.productsLoading = false
      }
    },

    async loadCategories() {
      try {
        // Only show loader if we don't already have categories hydrated
        if (this.backendCategories.length === 0) this.loading = true
        this.error = null
        
        // Fetch categories directly from API
        const categories = await categoriesAPI.getActiveCategories()
        this.backendCategories = Array.isArray(categories) ? categories : []
        
        if (this.backendCategories.length > 0 && !this.activeCategory) {
          this.activeCategory = this.backendCategories[0].id
          await this.selectCategory(this.backendCategories[0].id)
        }
        
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async selectCategory(categoryId) {
      this.activeCategory = categoryId
      this.displayedItemsCount = this.itemsPerLoad // Reset to initial load
      this.categorySearch = ''
      this.breadcrumbs = []
      this.currentSubcategory = null
      
      const category = this.categories.find(cat => cat.id === categoryId)
      
      if (category && !category.isCustom && category.hasSubcategories) {
        this.viewMode = 'subcategories'
        this.breadcrumbs = [
          { name: category.name, type: 'categories', categoryId: categoryId }
        ]
      } else {
        this.viewMode = 'products'
        if (!category.isCustom) {
          await this.loadProductsForCategory(categoryId)
        }
      }
    },

    async loadProductsForCategory(categoryId, subcategoryName = null) {
      await this.loadProducts(categoryId, subcategoryName)
    },

    async loadProducts(categoryId, subcategoryName = null) {
      try {
        this.error = null
        
        if (this.isCustomCategory) {
          this.productsLoading = false
          return
        }
        
        // Fetch products directly from API
        this.productsLoading = true
        const products = await productsAPI.getProductsByCategory(categoryId, subcategoryName)
        this.products = Array.isArray(products) ? products : []
        
      } catch (error) {
        this.error = error.message
        this.products = []
      } finally {
        this.productsLoading = false
      }
    },


    generateSubcategoryImage(subcategoryName) {
      return `https://ui-avatars.com/api/?name=${encodeURIComponent(subcategoryName)}&size=200&background=A07BE3&color=fff`
    },
    getFallbackProductImage(productName) {
      return `https://ui-avatars.com/api/?name=${encodeURIComponent(productName || 'Product')}&size=200&background=7392E2&color=fff`
    },

    createCategory() {
      if (!this.newCategory.name.trim()) return
      
      const categoryId = `custom_${this.nextCategoryId++}`
      const category = {
        id: categoryId,
        name: this.newCategory.name.trim(),
        icon: this.newCategory.icon,
        isCustom: true,
        hasSubcategories: false,
        subcategories: []
      }
      
      this.customCategoryProducts[categoryId] = []
      this.customCategories.push(category)
      
      // Save to localStorage for persistence
      this.saveCustomCategories()
      this.saveCustomCategoryProducts()
      this.saveIdCounters()
      
      this.closeCategoryModal()
      this.selectCategory(categoryId)
    },

    deleteCategory(categoryId) {
      if (confirm('Are you sure you want to delete this page and all its items?')) {
        this.customCategories = this.customCategories.filter(cat => cat.id !== categoryId)
        delete this.customCategoryProducts[categoryId]
        
        // Save to localStorage after deletion
        this.saveCustomCategories()
        this.saveCustomCategoryProducts()
        
        if (this.activeCategory === categoryId) {
          this.activeCategory = this.categories[0]?.id
          if (this.activeCategory) {
            this.selectCategory(this.activeCategory)
          }
        }
      }
    },

    closeCategoryModal() {
      this.showCategoryModal = false
      this.newCategory = { name: '', icon: 'Package' }
    },

    getCurrentCategoryName() {
      const category = this.categories.find(cat => cat.id === this.activeCategory)
      return category ? category.name : 'Category'
    },

    closeProductSelectorModal() {
      this.showProductSelectorModal = false
      this.selectedProducts = []
      this.productSearchQuery = ''
      this.selectedSourceCategory = null
      this.allProducts = []
    },

    toggleProductSelection(product) {
      if (this.isProductAlreadyInCategory(product.id)) return
      
      const index = this.selectedProducts.indexOf(product.id)
      if (index > -1) {
        this.selectedProducts.splice(index, 1)
      } else {
        if (this.customCategoryItems.length + this.selectedProducts.length < 8) {
          this.selectedProducts.push(product.id)
        }
      }
    },

    isProductAlreadyInCategory(productId) {
      if (this.isCustomCategory && this.customCategoryProducts[this.activeCategory]) {
        return this.customCategoryProducts[this.activeCategory].some(product => 
          product.originalId === productId || product.id === productId
        )
      }
      return false
    },

    addSelectedProductsToCategory() {
      const selectedProductData = this.allProducts.filter(product => 
        this.selectedProducts.includes(product.id)
      )
      
      if (!this.customCategoryProducts[this.activeCategory]) {
        this.customCategoryProducts[this.activeCategory] = []
      }
      
      selectedProductData.forEach(product => {
        const newProduct = {
          ...product,
          id: `custom_${this.nextProductId++}`,
          category: this.activeCategory,
          isReference: true,
          originalId: product.id
        }
        
        this.customCategoryProducts[this.activeCategory].push(newProduct)
      })
      
      // Save to localStorage after adding products
      this.saveCustomCategoryProducts()
      this.saveIdCounters()
      
      this.$forceUpdate()
      this.closeProductSelectorModal()
    },

    removeFromCategory(productId) {
      if (this.isCustomCategory && this.customCategoryProducts[this.activeCategory]) {
        this.customCategoryProducts[this.activeCategory] = 
          this.customCategoryProducts[this.activeCategory].filter(product => product.id !== productId)
        
        // Save to localStorage after removing product
        this.saveCustomCategoryProducts()
        
        this.$forceUpdate()
      }
    },

    handleProductClick(product) {
      if (product.isSubcategory) {
        this.selectSubcategory(product.subcategoryData)
      } else {
        // Prevent adding sold-out products to cart
        if (product.total_stock === null || product.total_stock <= 0) {
          return
        }
        this.addToCart(product)
      }
    },

    async selectSubcategory(subcategoryData) {
      this.currentSubcategory = subcategoryData
      this.viewMode = 'products'
      this.breadcrumbs.push({
        name: subcategoryData.name,
        type: 'products',
        data: subcategoryData
      })
      
      await this.loadProducts(this.activeCategory, subcategoryData.name)
    },

    async navigateTo(crumb) {
      if (crumb.type === 'categories') {
        this.viewMode = 'subcategories'
        this.currentSubcategory = null
        this.breadcrumbs = [crumb]
        await this.selectCategory(crumb.categoryId)
      } else if (crumb.type === 'products') {
        const crumbIndex = this.breadcrumbs.findIndex(b => b === crumb)
        this.breadcrumbs = this.breadcrumbs.slice(0, crumbIndex + 1)
        this.currentSubcategory = crumb.data
        await this.loadProducts(this.activeCategory, crumb.data.name)
      }
    },

    handleProductsScroll(event) {
      const container = event.target
      const scrollTop = container.scrollTop
      const scrollHeight = container.scrollHeight
      const clientHeight = container.clientHeight
      
      // Check if scrolled near bottom (within 100px)
      if (scrollTop + clientHeight >= scrollHeight - 100) {
        this.loadMoreItems()
      }
    },

    loadMoreItems() {
      if (!this.hasMoreItems) return
      
      // Load next batch of items
      this.displayedItemsCount += this.itemsPerLoad
    },

    resetInfiniteScroll() {
      this.displayedItemsCount = this.itemsPerLoad
    },

    retryLoad() {
      this.error = null
      if (this.activeCategory) {
        this.loadProducts(this.activeCategory)
      } else {
        this.loadCategories()
      }
    },

    // ================================================================
    // CART MANAGEMENT
    // ================================================================
    
    addToCart(product) {
      try {
        // Handle different product data formats
        const productId = product._id || product.id
        const productName = product.product_name || product.name
        const productPrice = product.selling_price || product.price
        const productStock = product.total_stock || product.stock
        
        // Debug: Check if this is PROD-00225
        if (productId === 'PROD-00225') {
          console.log('🔍 DEBUG: Adding PROD-00225 to cart')
          console.log('   Product ID:', productId)
          console.log('   Product Name:', productName)
          console.log('   Product Price:', productPrice)
        }
        
        if (!productId || !productName || !productPrice) {
          // console.error('❌ Invalid product data:', product)
          throw new Error('Invalid product data')
        }
        
        if (productStock <= 0) {
          // console.warn('⚠️ Product out of stock:', productName)
          alert(`${productName} is out of stock!`)
          return
        }
        
        // Create cart item with proper format
        const cartItem = {
          id: productId,
          name: productName,
          price: productPrice,
          stock: productStock,
          image: product.image || this.getFallbackProductImage(productName),
          category: product.category_id || product.category,
          sku: product.SKU || product.sku || '',
          barcode: product.barcode || '',
          isTaxable: product.is_taxable !== false
        }
        
        // Debug: Log cart item before adding to store
        if (productId === 'PROD-00225') {
          console.log('   Cart Item:', cartItem)
        }
        
        this.cartStore.addItem(cartItem)
        
      } catch (error) {
        alert(`Failed to add item: ${error.message}`)
      }
    },
    
    removeFromCart(item) {
      this.cartStore.removeItem(item.productId)
    },
    
    increaseQuantity(item) {
      this.cartStore.increaseQuantity(item.productId)
    },
    
    decreaseQuantity(item) {
      this.cartStore.decreaseQuantity(item.productId)
    },
    
    async checkout() {
      if (this.cartStore.isEmpty) {
        alert('Your cart is empty!')
        return
      }
      
      // Check if user has an active shift
      const userData = JSON.parse(localStorage.getItem('userData') || '{}')
      const userRole = userData.role?.toLowerCase()
      
      if (userRole === 'cashier' || userRole === 'employee') {
        const activeShiftId = localStorage.getItem('activeShiftId')
        if (!activeShiftId) {
          this.showShiftRequiredModal = true
          return
        }
      }
      
      // No longer storing promotion - will be auto-detected in checkout
      this.$router.push('/checkout')
    },

    goToShiftPage() {
      this.showShiftRequiredModal = false
      this.$router.push('/shift')
    },

    // Cart methods removed - sidebar is always visible now
    filterPromoSuggestions() {
      const searchQuery = this.promoCode.toLowerCase().trim()
      
      if (!searchQuery) {
        // Show all available promotions if input is empty
        this.filteredPromoSuggestions = this.availablePromotions
      } else {
        // Filter promotions by name or description
        this.filteredPromoSuggestions = this.availablePromotions.filter(promo => 
          promo.name.toLowerCase().includes(searchQuery) ||
          promo.description.toLowerCase().includes(searchQuery)
        )
      }
    },
    
    hidePromoSuggestionsDelayed() {
      // Delay hiding to allow click events to fire
      setTimeout(() => {
        this.showPromoSuggestions = false
      }, 200)
    },
    
    selectPromoFromSuggestion(promo) {
      this.promoCode = promo.name
      this.showPromoSuggestions = false
      this.applyPromotionById(promo._id)
    },
    
    formatPromotionValue(promo) {
      if (promo.type === 'percentage') {
        return `${promo.discount_value}% OFF`
      } else if (promo.type === 'fixed') {
        return `₱${this.formatPrice(promo.discount_value)} OFF`
      }
      return 'Discount'
    },
    
    formatPromotionTarget(promo) {
      const targetType = promo.discount_config?.target_type
      
      if (targetType === 'all') {
        return 'All items'
      } else if (targetType === 'categories') {
        const count = promo.discount_config?.target_ids?.length || 0
        return `${count} ${count === 1 ? 'category' : 'categories'}`
      } else if (targetType === 'products') {
        const count = promo.discount_config?.target_ids?.length || 0
        return `${count} ${count === 1 ? 'product' : 'products'}`
      }
      return 'Selected items'
    },
    
    // ================================================================
    // CUSTOM CATEGORY STOCK UPDATE
    // ================================================================
    
    updateCustomCategoryProductsStock(stockUpdates) {
      try {
        let updated = false
        
        // Update all custom category products with fresh stock data
        Object.keys(this.customCategoryProducts).forEach(categoryId => {
          const products = this.customCategoryProducts[categoryId]
          if (Array.isArray(products)) {
            products.forEach(product => {
              // Use originalId if available, otherwise use id
              const originalId = product.originalId || product.id
              const newStock = stockUpdates[originalId]
              
              if (newStock !== undefined && newStock !== product.total_stock) {
                product.stock = newStock
                product.total_stock = newStock
                updated = true
              }
            })
          }
        })
        
        if (updated) {
          // Save updated custom category products
          this.saveCustomCategoryProducts()
        }
        
      } catch (error) {
        // Failed to update custom category products stock
      }
    },

    // ================================================================
    // PERSISTENCE METHODS
    // ================================================================
    
    saveCustomCategories() {
      try {
        localStorage.setItem('customCategories', JSON.stringify(this.customCategories))
      } catch (error) {
        console.error('Failed to save custom categories:', error)
      }
    },
    
    loadCustomCategories() {
      try {
        const stored = localStorage.getItem('customCategories')
        if (stored) {
          const parsed = JSON.parse(stored)
          if (Array.isArray(parsed)) {
            this.customCategories = parsed
          }
        }
      } catch (error) {
        console.error('Failed to load custom categories:', error)
      }
    },
    
    saveCustomCategoryProducts() {
      try {
        localStorage.setItem('customCategoryProducts', JSON.stringify(this.customCategoryProducts))
      } catch (error) {
        console.error('Failed to save custom category products:', error)
      }
    },
    
    loadCustomCategoryProducts() {
      try {
        const stored = localStorage.getItem('customCategoryProducts')
        if (stored) {
          const parsed = JSON.parse(stored)
          if (parsed && typeof parsed === 'object') {
            this.customCategoryProducts = parsed
          }
        }
      } catch (error) {
        console.error('Failed to load custom category products:', error)
      }
    },
    
    saveIdCounters() {
      try {
        // Use direct localStorage (no expiration) for permanent storage of ID counters
        localStorage.setItem('nextCategoryId', this.nextCategoryId.toString())
        localStorage.setItem('nextProductId', this.nextProductId.toString())
      } catch (error) {
        console.error('Failed to save ID counters:', error)
      }
    },
    
    loadIdCounters() {
      try {
        // Load from localStorage directly (permanent storage, no expiration)
        const savedCategoryId = localStorage.getItem('nextCategoryId')
        const savedProductId = localStorage.getItem('nextProductId')
        
        if (savedCategoryId) {
          const parsed = parseInt(savedCategoryId, 10)
          if (!isNaN(parsed) && parsed > this.nextCategoryId) {
            this.nextCategoryId = parsed
          }
        }
        if (savedProductId) {
          const parsed = parseInt(savedProductId, 10)
          if (!isNaN(parsed) && parsed > this.nextProductId) {
            this.nextProductId = parsed
          }
        }
        
        // Default values if not found
        if (!savedCategoryId || !savedProductId) {
          // Use defaults
          if (this.nextCategoryId < 100) {
            this.nextCategoryId = oldCategoryId
            this.saveIdCounters() // Migrate to new format
          }
          if (oldProductId && typeof oldProductId === 'number' && oldProductId > this.nextProductId) {
            this.nextProductId = oldProductId
            this.saveIdCounters() // Migrate to new format
          }
        }
      } catch (error) {
        console.error('Failed to load ID counters:', error)
      }
    },
    
    // ================================================================
    // BARCODE SCANNING
    // ================================================================
    
    startBarcodeScanner() {
      this.barcodeScanner.startScanning()
      
      // Configure scanner to auto-add to cart
      this.barcodeScanner.configure({
        autoAddToCart: true,
        showNotifications: true
      })
    },
    
    async processManualBarcode() {
      if (!this.manualBarcodeInput.trim()) return
      
      try {
        // Process the barcode
        const product = await this.barcodeScanner.processBarcode(this.manualBarcodeInput.trim())
        
        if (product) {
          // Add to cart
          this.addToCart(product)
          
          // Clear input but keep scanner active
          this.manualBarcodeInput = ''
          
          // Focus back on input for next scan
          this.$nextTick(() => {
            if (this.$refs.barcodeInput) {
              this.$refs.barcodeInput.focus()
            }
          })
        }
      } catch (error) {
        // Manual barcode processing failed
      }
    },
    
    // Watch for barcode scanner results and auto-add to cart
    watchBarcodeResults() {
      // This will be called when barcode scanner finds a product
      if (this.barcodeScanner.scanSuccess && this.barcodeScanner.scanResult?.product) {
        const product = this.barcodeScanner.scanResult.product
        
        // Add to cart
        this.addToCart(product)
        
        // Clear scanner results after a delay but keep scanner active
        setTimeout(() => {
          this.barcodeScanner.clearResults()
        }, 1000)
      }
    },
    
    // Manual test function to trigger cart addition
    testCartAddition() {
      const testProduct = {
        _id: "PROD-00276",
        id: "PROD-00276",
        name: "7 UP bottle",
        product_name: "7 UP bottle",
        price: 25,
        selling_price: 25,
        stock: 160,
        total_stock: 160,
        barcode: "748485100401",
        sku: "7-UP-BOTT",
        SKU: "7-UP-BOTT",
        category: "CTGY-001",
        category_id: "CTGY-001",
        is_taxable: true,
        isTaxable: true
      }
      
      this.addToCart(testProduct)
    },
    
    // Watch cart items
    watchCartItems() {
      // Cart items changed
    },

    // ================================================================
    // UTILITIES
    // ================================================================
    
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2)
    }
  }
}
</script>

<style scoped>
@import '@/assets/styles/NewOrder.css';


@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.scanning {
  animation: scan 1s linear infinite;
}

@keyframes scan {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Manual Barcode Input Section */
.manual-barcode-input-section {
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  border: 1px solid;
}

.barcode-input-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.barcode-label {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.875rem;
  margin: 0;
}

.barcode-input-group {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

/* Manual Barcode Input */
.manual-barcode-input {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.barcode-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--neutral);
  border-radius: 0.5rem;
  font-size: 1rem;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  background: var(--surface-primary);
  color: var(--text-primary);
}

.barcode-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(115, 146, 226, 0.1);
}

.process-barcode-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  border: none;
  background: var(--primary);
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.process-barcode-btn:hover:not(:disabled) {
  background: var(--primary-dark);
}

.process-barcode-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}


/* Responsive Design */
@media (max-width: 768px) {
  .barcode-input-group {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .barcode-input {
    width: 100%;
  }
  
  .process-barcode-btn {
    width: 100%;
  }
  
}

/* Shift Required Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.shift-modal {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-width: 500px;
  width: 90%;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.shift-modal-header {
  padding: 2rem;
  text-align: center;
}

.shift-modal-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.shift-modal-icon svg {
  color: #6366f1;
  width: 48px;
  height: 48px;
}

.shift-modal-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.75rem 0;
}

.shift-modal-message {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.shift-modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.shift-modal-btn {
  padding: 0.625rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  outline: none;
}

.shift-modal-btn-cancel {
  background: white;
  color: #6b7280;
  border: 2px solid #e5e7eb;
}

.shift-modal-btn-cancel:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.shift-modal-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.shift-modal-btn-primary:hover {
  background: linear-gradient(135deg, #5568d3 0%, #653a8a 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.shift-modal-btn-primary:active {
  transform: translateY(0);
}

</style>