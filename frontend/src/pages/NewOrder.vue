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
              placeholder="Search products or scan barcode..."
              class="search-input input-complete focus-ring-theme"
              @keyup.enter="handleSearchEnter"
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

            <template v-if="isCustomCategory">
              <button
                class="edit-order-btn btn-complete focus-ring-theme"
                @click="openProductSelectorModal"
                title="Add products to this page"
              >
                <Plus :size="18" />
                <span>Add Products</span>
              </button>
              <button
                v-if="!editMode"
                class="edit-order-btn btn-complete focus-ring-theme"
                @click="toggleEditMode"
                title="Reorder products"
              >
                <GripVertical :size="18" />
                <span>Edit Page</span>
              </button>
              <template v-else>
                <button
                  class="delete-page-btn focus-ring-theme"
                  @click="deleteCategory(activeCategory)"
                  title="Delete this page"
                >
                  <Trash2 :size="18" />
                  <span>Delete Page</span>
                </button>
                <button
                  class="done-btn focus-ring-theme"
                  @click="toggleEditMode"
                  title="Exit edit mode"
                >
                  <span>Done</span>
                </button>
              </template>
            </template>

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

        <!-- Products Grid -->
        <div v-else :class="['products-grid', { 'custom-page': isCustomCategory && !categorySearch.trim(), 'edit-mode': editMode }]">
          <div
            v-for="(product, index) in paginatedProducts"
            :key="product.id"
            :class="[
              'product-card transition-theme',
              product.isBlank ? 'blank-slot' : 'card-complete',
              { 'hover-lift': !editMode && !product.isBlank },
              { 'sold-out': !editMode && !product.isBlank && !product.isSubcategory && (product.total_stock === null || product.total_stock <= 0) },
              { 'dragging': editMode && draggedIndex === index },
              { 'drag-over': editMode && dragOverIndex === index && draggedIndex !== index }
            ]"
            :draggable="editMode && isCustomCategory"
            @click="editMode ? null : handleProductClick(product)"
            @dragstart="editMode && dragStart($event, index)"
            @dragover="editMode && dragOver($event, index)"
            @drop="editMode && drop($event, index)"
            @dragend="dragEnd">

            <!-- BLANK SLOT -->
            <template v-if="product.isBlank">
              <div class="blank-slot-inner" />
            </template>

            <!-- PRODUCT content -->
            <template v-else>

            <!-- Drag handle (edit mode only) -->
            <div v-if="editMode && isCustomCategory" class="drag-handle">
              <GripVertical :size="20" />
            </div>

            <!-- Sold Out ribbon -->
            <div
              v-if="!editMode && !product.isSubcategory && (product.total_stock === null || product.total_stock <= 0)"
              class="sold-out-ribbon">
              Sold Out
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
                Stock: {{ product.total_stock ?? 0 }}
              </p>
              <div v-if="!product.isSubcategory" class="product-price text-accent">
                ₱{{ formatPrice(product.price) }}
              </div>
              <div v-else class="subcategory-indicator text-accent">
                <ChevronRight :size="16" /> View Items
              </div>
            </div>
            <button
              v-if="!editMode && !product.isSubcategory && isCustomCategory"
              class="delete-product-btn btn-complete"
              @click.stop="removeFromCategory(product.id)"
              title="Remove from page">
              <X :size="14" />
            </button>

            </template>
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
        <div class="modal-body selector-modal-body">

          <!-- Left: Browse -->
          <div class="selector-left">
            <!-- Category Tabs -->
            <div class="product-selector-tabs">
              <button
                v-for="category in availableSourceCategories"
                :key="category.id"
                :class="['tab-btn nav-link-theme hover-surface', { active: selectedSourceCategory === category.id }]"
                @click="selectedSourceCategory = category.id; productSearchQuery = ''">
                {{ category.name }} ({{ productCountsByCategory[category.id] || 0 }})
              </button>
            </div>

            <!-- Search -->
            <div class="product-search">
              <input
                type="text"
                v-model="productSearchQuery"
                placeholder="Search all products..."
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
                  <small v-if="isProductAlreadyInCategory(product.id)" class="already-added-text">Already added</small>
                </div>
                <div class="selection-indicator">
                  <div v-if="selectedProducts.includes(product.id)" class="checkmark">✓</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right: Preview -->
          <div class="selector-right">
            <div class="preview-panel">
              <div class="preview-header">
                <span class="preview-title">Selected</span>
                <span class="preview-count">{{ selectedProducts.length }}</span>
              </div>

              <div v-if="selectedProducts.length === 0" class="preview-empty text-secondary">
                <ShoppingBag :size="32" />
                <p>No products selected</p>
                <small>Click products on the left to add them</small>
              </div>

              <div v-else class="preview-list">
                <div
                  v-for="productId in selectedProducts"
                  :key="productId"
                  class="preview-item">
                  <img
                    :src="allProducts.find(p => p.id === productId)?.image"
                    :alt="allProducts.find(p => p.id === productId)?.name"
                    class="preview-item-img"
                    @error="handleImageError($event, allProducts.find(p => p.id === productId))"
                  />
                  <div class="preview-item-info">
                    <span class="preview-item-name">{{ allProducts.find(p => p.id === productId)?.name }}</span>
                    <span class="preview-item-price">₱{{ formatPrice(allProducts.find(p => p.id === productId)?.price) }}</span>
                  </div>
                  <button
                    class="preview-item-remove btn-complete"
                    @click="toggleProductSelection(allProducts.find(p => p.id === productId))">
                    <X :size="14" />
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>
        <div class="modal-footer">
          <button class="btn-secondary btn-complete" @click="closeProductSelectorModal">Cancel</button>
          <button 
            class="btn-primary btn-complete" 
            @click="addSelectedProductsToCategory" 
            :disabled="selectedProducts.length === 0">
            Add {{ selectedProducts.length }} Products
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

    <!-- Delete Page Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showDeletePageModal"
        class="modal-overlay"
        @click.self="showDeletePageModal = false; pendingDeleteCategoryId = null"
      >
        <div class="shift-modal">
          <div class="shift-modal-header">
            <div class="shift-modal-icon" style="color: var(--error)">
              <Trash2 :size="48" />
            </div>
            <h3 class="shift-modal-title">Delete Page?</h3>
            <p class="shift-modal-message">
              This will permanently delete the page and remove all product assignments from it.
              Products themselves will not be affected.
            </p>
          </div>
          <div class="shift-modal-footer">
            <button
              class="shift-modal-btn shift-modal-btn-cancel"
              @click="showDeletePageModal = false; pendingDeleteCategoryId = null"
            >
              Cancel
            </button>
            <button
              class="done-btn"
              style="background: var(--error); border-color: var(--error);"
              @click="confirmDeleteCategory"
            >
              Delete Page
            </button>
          </div>
        </div>
      </div>
    </Teleport>

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
import posPageAPI from '@/services/apiPosPages.js'
import { useStockCache } from '@/composables/data/useStockCache.js'
import { useBarcode } from '@/composables/useBarcode.js'
import { RefreshCw, GripVertical } from 'lucide-vue-next'

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
      stockPollInterval: null,
      
      // Cart UI state - always visible now
      showCart: true,
      
      // Modal states
      showCategoryModal: false,
      showProductSelectorModal: false,
      showShiftRequiredModal: false,
      showDeletePageModal: false,
      pendingDeleteCategoryId: null,
      
      // Navigation state
      viewMode: 'products',
      currentSubcategory: null,
      categorySearch: '',
      breadcrumbs: [],
      
      // Stock refresh state
      isRefreshingStock: false,

      // Edit mode (reorder products on custom pages)
      editMode: false,
      draggedIndex: null,
      dragOverIndex: null,

      // Promotion discount amount
      promoDiscount: 0,

      // Custom page creation
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
    
    await this.initializeSession()
    await this.loadCategories()
    await this.loadPosPages()

    // Poll stock levels every 45 seconds so multi-terminal stock stays in sync
    this.stockPollInterval = setInterval(() => this.pollStockLevels(), 45000)

    // Also refresh stock when the user returns to this tab
    this._onVisibilityChange = () => { if (!document.hidden) this.pollStockLevels() }
    document.addEventListener('visibilitychange', this._onVisibilityChange)

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
    if (this.stockPollInterval) clearInterval(this.stockPollInterval)
    if (this._onVisibilityChange) document.removeEventListener('visibilitychange', this._onVisibilityChange)
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
      if (this.isCustomCategory) {
        const products = this.customCategoryProducts[this.activeCategory] || []
        if (this.categorySearch.trim()) {
          // When searching, skip blank slots and filter by name
          return products.filter(p =>
            !p.isBlank && p.name?.toLowerCase().includes(this.categorySearch.toLowerCase())
          )
        }
        // Custom pages always preserve the user-defined order (including blank slots)
        return products
      }

      let products = this.products
      if (this.categorySearch.trim()) {
        products = products.filter(p =>
          p.name.toLowerCase().includes(this.categorySearch.toLowerCase())
        )
      }
      return products.sort((a, b) => {
        const aInStock = a.total_stock !== null && a.total_stock > 0
        const bInStock = b.total_stock !== null && b.total_stock > 0
        if (aInStock === bInStock) return 0
        return aInStock ? -1 : 1
      })
    },

    paginatedProducts() {
      return this.filteredProducts
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
      const query = this.productSearchQuery.trim().toLowerCase()

      if (query) {
        return this.allProducts.filter(product =>
          product.name.toLowerCase().includes(query)
        )
      }

      return this.allProducts.filter(product =>
        product.category === this.selectedSourceCategory
      )
    },

    allAvailableProductsCount() {
      const currentCategoryProducts = this.customCategoryProducts[this.activeCategory] || []
      const currentProductIds = currentCategoryProducts.map(p => p.originalId || p.id)
      
      return this.allProducts.filter(p => !currentProductIds.includes(p.id)).length
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
        if (this.activeCategory) {
          await this.loadProductsForCategory(this.activeCategory, this.currentSubcategory?.name)
        }
      } catch (error) {
        console.error('Stock refresh error:', error)
        alert('Failed to refresh products. Please try again.')
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

    openProductSelectorModal() {
      this.showProductSelectorModal = true
      if (this.availableSourceCategories.length > 0) {
        this.selectedSourceCategory = this.availableSourceCategories[0].id
      }
    },

    async loadCategories() {
      try {
        if (this.backendCategories.length === 0) this.loading = true
        this.error = null

        // Fetch categories and ALL products in parallel.
        // Products use localStorage cache (1-hour TTL) for instant load on return visits.
        const [categories, allProds] = await Promise.all([
          categoriesAPI.getActiveCategories(),
          productsAPI.getAllProductsAllPagesCached()
        ])

        this.backendCategories = Array.isArray(categories) ? categories : []
        this.allProducts = Array.isArray(allProds) ? allProds : []

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
      this.categorySearch = ''
      this.breadcrumbs = []
      this.currentSubcategory = null
      this.viewMode = 'products'
      this.editMode = false
      this.draggedIndex = null
      this.dragOverIndex = null

      const category = this.categories.find(cat => cat.id === categoryId)
      if (category && !category.isCustom) {
        await this.loadProductsForCategory(categoryId)
      }
    },

    async loadProductsForCategory(categoryId, subcategoryName = null) {
      await this.loadProducts(categoryId, subcategoryName)
    },

    async loadProducts(categoryId, subcategoryName = null) {
      if (this.isCustomCategory) return

      this.error = null

      // Filter from the in-memory cache — no API call, same as back office
      let filtered = this.allProducts.filter(p => {
        const cat = p.category_id || p.category
        return cat === categoryId
      })

      if (subcategoryName) {
        filtered = filtered.filter(p => {
          const sub = p.subcategory_name || p.subcategory
          return sub === subcategoryName
        })
      }

      this.products = filtered
    },

    async pollStockLevels() {
      try {
        const stockData = await productsAPI.getStockLevels()
        if (!stockData || stockData.length === 0) return

        // Build a lookup by both padded (PROD-00001) and stripped (00001) IDs
        const stockMap = {}
        stockData.forEach(item => {
          stockMap[item.product_id] = { stock: item.total_stock, status: item.status }
          const stripped = item.product_id.replace('PROD-', '')
          stockMap[stripped] = { stock: item.total_stock, status: item.status }
        })

        let changed = false
        this.allProducts = this.allProducts.map(p => {
          const entry = stockMap[p.id] || stockMap[p._id]
          if (!entry) return p
          if (entry.stock === p.total_stock && entry.status === p.status) return p
          changed = true
          return { ...p, stock: entry.stock, total_stock: entry.stock, status: entry.status }
        })

        if (changed && this.activeCategory) {
          await this.loadProducts(this.activeCategory, this.currentSubcategory?.name)
        }
      } catch {
        // Silent — polling failures should not surface errors to the user
      }
    },


    generateSubcategoryImage() {
      return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f3f4f6'/%3E%3Crect x='55' y='60' width='90' height='80' rx='6' fill='%23e5e7eb'/%3E%3Ccircle cx='80' cy='88' r='10' fill='%23d1d5db'/%3E%3Cpolygon points='55,140 85,105 110,125 130,100 145,140' fill='%23d1d5db'/%3E%3C/svg%3E`
    },
    getFallbackProductImage() {
      return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f3f4f6'/%3E%3Crect x='55' y='60' width='90' height='80' rx='6' fill='%23e5e7eb'/%3E%3Ccircle cx='80' cy='88' r='10' fill='%23d1d5db'/%3E%3Cpolygon points='55,140 85,105 110,125 130,100 145,140' fill='%23d1d5db'/%3E%3C/svg%3E`
    },

    async createCategory() {
      if (!this.newCategory.name.trim()) return

      try {
        const page = await posPageAPI.createPage(this.newCategory.name.trim(), this.newCategory.icon)
        const category = {
          id: page.page_id,
          name: page.page_name,
          icon: page.icon,
          isCustom: true,
          hasSubcategories: false,
          subcategories: [],
          productIds: []
        }
        this.customCategoryProducts[page.page_id] = Array.from({ length: 15 }, (_, i) => ({
          id: `blank-${page.page_id}-${i}`,
          isBlank: true
        }))
        this.customCategories.push(category)
        this.closeCategoryModal()
        this.selectCategory(page.page_id)
      } catch (error) {
        alert('Failed to create page. Please try again.')
      }
    },

    deleteCategory(categoryId) {
      this.pendingDeleteCategoryId = categoryId
      this.showDeletePageModal = true
    },

    async confirmDeleteCategory() {
      const categoryId = this.pendingDeleteCategoryId
      this.showDeletePageModal = false
      this.pendingDeleteCategoryId = null

      try {
        await posPageAPI.deletePage(categoryId)
        this.customCategories = this.customCategories.filter(cat => cat.id !== categoryId)
        delete this.customCategoryProducts[categoryId]

        if (this.activeCategory === categoryId) {
          this.activeCategory = this.categories[0]?.id
          if (this.activeCategory) this.selectCategory(this.activeCategory)
        }
      } catch (error) {
        alert('Failed to delete page. Please try again.')
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
    },

    toggleProductSelection(product) {
      if (this.isProductAlreadyInCategory(product.id)) return
      const index = this.selectedProducts.indexOf(product.id)
      if (index > -1) {
        this.selectedProducts.splice(index, 1)
      } else {
        this.selectedProducts.push(product.id)
      }
    },

    isProductAlreadyInCategory(productId) {
      if (this.isCustomCategory && this.customCategoryProducts[this.activeCategory]) {
        return this.customCategoryProducts[this.activeCategory].some(p => p.id === productId)
      }
      return false
    },

    async addSelectedProductsToCategory() {
      const productIds = [...this.selectedProducts]
      try {
        const slots = [...(this.customCategoryProducts[this.activeCategory] || [])]

        for (const pid of productIds) {
          if (slots.some(s => s.id === pid)) continue // already on page
          const product = this.allProducts.find(p => p.id === pid)
          if (!product) continue
          const blankIdx = slots.findIndex(s => s.isBlank)
          if (blankIdx >= 0) {
            slots[blankIdx] = product
          }
          // If no blank slots remain, product is silently skipped (grid is full)
        }

        this.customCategoryProducts[this.activeCategory] = slots
        await this.savePageOrder(slots.map(p => p.id))

        this.$forceUpdate()
        this.closeProductSelectorModal()
      } catch (error) {
        alert('Failed to add products to page. Please try again.')
      }
    },

    async removeFromCategory(productId) {
      try {
        const slots = [...(this.customCategoryProducts[this.activeCategory] || [])]
        const idx = slots.findIndex(p => p.id === productId)
        if (idx >= 0) {
          slots[idx] = { id: `blank-${this.activeCategory}-${Date.now()}`, isBlank: true }
        }
        this.customCategoryProducts[this.activeCategory] = slots
        await this.savePageOrder(slots.map(p => p.id))
        this.$forceUpdate()
      } catch (error) {
        alert('Failed to remove product from page. Please try again.')
      }
    },

    handleProductClick(product) {
      if (product.isBlank) return
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

    closeCart() {
      // Cart sidebar is always visible — no-op
    },

    // ================================================================
    // EDIT MODE — PRODUCT REORDERING
    // ================================================================

    toggleEditMode() {
      this.editMode = !this.editMode
      this.draggedIndex = null
      this.dragOverIndex = null
    },

    dragStart(event, index) {
      this.draggedIndex = index
      event.dataTransfer.effectAllowed = 'move'
    },

    dragOver(event, index) {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
      this.dragOverIndex = index
    },

    drop(event, index) {
      event.preventDefault()
      if (this.draggedIndex === null || this.draggedIndex === index) {
        this.draggedIndex = null
        this.dragOverIndex = null
        return
      }

      const products = [...(this.customCategoryProducts[this.activeCategory] || [])]
      // Swap the two positions so grid layout stays stable
      ;[products[this.draggedIndex], products[index]] = [products[index], products[this.draggedIndex]]
      this.customCategoryProducts[this.activeCategory] = products

      this.draggedIndex = null
      this.dragOverIndex = null

      this.savePageOrder(products.map(p => p.id))
    },

    dragEnd() {
      this.draggedIndex = null
      this.dragOverIndex = null
    },

    async savePageOrder(localIds) {
      // Convert local blank IDs (blank-xxx) to the 'BLANK' sentinel for the backend
      const backendIds = localIds.map(id =>
        typeof id === 'string' && id.startsWith('blank-') ? 'BLANK' : id
      )
      try {
        await posPageAPI.updatePage(this.activeCategory, { product_ids: backendIds })
      } catch (error) {
        console.error('Failed to save page order:', error)
      }
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
              const newStock = stockUpdates[product.id]
              
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
    // POS PAGES
    // ================================================================

    async loadPosPages() {
      try {
        const pages = await posPageAPI.getPages()

        this.customCategories = pages.map(page => ({
          id: page.page_id,
          name: page.page_name,
          icon: page.icon,
          isCustom: true,
          hasSubcategories: false,
          subcategories: [],
          productIds: page.product_ids || []
        }))

        const GRID_SIZE = 15
        pages.forEach(page => {
          let blankCount = 0
          const makeBlank = () => ({ id: `blank-${page.page_id}-${blankCount++}`, isBlank: true })
          const items = (page.product_ids || []).map(pid =>
            (!pid || pid === 'BLANK')
              ? makeBlank()
              : (this.allProducts.find(p => p.id === pid) || makeBlank())
          )
          while (items.length < GRID_SIZE) items.push(makeBlank())
          this.customCategoryProducts[page.page_id] = items.slice(0, GRID_SIZE)
        })
      } catch (error) {
        console.error('Failed to load POS pages:', error)
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
    
    async handleSearchEnter() {
      const input = this.categorySearch.trim()
      if (!input) return

      try {
        const product = await this.barcodeScanner.processBarcode(input)
        if (product) {
          this.addToCart(product)
          this.categorySearch = ''
        }
      } catch (error) {
        // Not a barcode match — keep as text search filter
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