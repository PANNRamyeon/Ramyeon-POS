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
                  title="Delete Category">
                  <X :size="12" />
                </button>
              </div>
              
              <!-- Add Category Button -->
              <div class="cat-card add-category card-complete hover-lift" @click="showCategoryModal = true">
                <div class="cat-icon">
                  <Plus :size="24" />
                </div>
                <span class="cat-label">Add Category</span>
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
                Stock: {{ product.total_stock || 0 }}
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
              title="Remove from category">
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

    <!-- Category Creation Modal -->
    <div v-if="showCategoryModal" class="modal-overlay modal-overlay-theme" @click="closeCategoryModal">
      <div class="modal-content modal-theme transition-theme" @click.stop>
        <div class="modal-header header-theme">
          <h3>Create New Category</h3>
          <button class="close-btn btn-complete" @click="closeCategoryModal">
            <X :size="20" />
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Category Name</label>
            <input 
              type="text" 
              v-model="newCategory.name" 
              placeholder="Enter category name"
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
            Create Category
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
        
       <!-- Manual Promo Code with Smart Suggestions -->
        <div class="promo-section">
          <h4 class="section-title">Have a Promo Code?</h4>
          
          <div class="promo-input-wrapper">
            <div class="input-group">
              <input 
                type="text" 
                class="form-control input-theme input-complete focus-ring-theme" 
                placeholder="Enter promo code or select below"
                v-model="promoCode"
                @focus="showPromoSuggestions = true"
                @blur="hidePromoSuggestionsDelayed"
                @input="filterPromoSuggestions"
              />
              <button 
                class="btn btn-primary btn-complete" 
                type="button" 
                @click="applyPromoCodeManually"
                :disabled="!promoCode.trim()"
              >
                Apply
              </button>
            </div>
            
            <!-- Promo Suggestions Dropdown -->
            <div 
              v-if="showPromoSuggestions && filteredPromoSuggestions.length > 0" 
              class="promo-suggestions-dropdown card-theme transition-theme"
            >
              <div class="suggestions-header">
                <span class="suggestions-title">✨ Available Promotions</span>
                <span class="suggestions-count">{{ filteredPromoSuggestions.length }}</span>
              </div>
              
              <div class="suggestions-list">
                <div 
                  v-for="promo in filteredPromoSuggestions" 
                  :key="promo._id"
                  class="suggestion-item"
                  @mousedown.prevent="selectPromoFromSuggestion(promo)"
                >
                  <div class="suggestion-icon">🎁</div>
                  <div class="suggestion-content">
                    <div class="suggestion-name">{{ promo.name }}</div>
                    <div class="suggestion-description">{{ promo.description }}</div>
                    <div class="suggestion-details">
                      <span class="suggestion-discount">
                        {{ formatPromotionValue(promo) }}
                      </span>
                      <span class="suggestion-target">
                        {{ formatPromotionTarget(promo) }}
                      </span>
                    </div>
                  </div>
                  <div class="suggestion-savings">
                    <div class="savings-label">Save</div>
                    <div class="savings-amount">₱{{ formatPrice(promo.calculatedDiscount) }}</div>
                  </div>
                </div>
              </div>
              
              <div v-if="availablePromotions.length === 0" class="no-suggestions">
                <span>🔍 No promotions available for your cart</span>
              </div>
            </div>
          </div>
          
          <!-- Applied Promo Display -->
          <div v-if="appliedPromotion" class="applied-promo-display">
            <div class="applied-promo-content">
              <span class="applied-icon">✅</span>
              <div class="applied-info">
                <span class="applied-name">{{ appliedPromotion.name }}</span>
                <span class="applied-savings">-₱{{ formatPrice(promoDiscount) }}</span>
              </div>
            </div>
            <button class="btn-remove-promo" @click="removePromotion">
              <X :size="16" />
            </button>
          </div>
        </div>

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
  </div>
</template>

<script>
import { useCartStore } from '@/stores/cartStores'
import categoriesAPI from '@/services/apiCategory.js'
import productsAPI from '@/services/apiProducts.js'
import { api } from '@/services/api.js'
import { useLocalStorage } from '@/composables/data/useLocalStorage.js'
import { useCache } from '@/composables/data/useCache.js'
import { useStockCache } from '@/composables/data/useStockCache.js'
import { RefreshCw } from 'lucide-vue-next'

export default {
  name: 'NewOrder',
  
  setup() {
    const cartStore = useCartStore()
    const stockCache = useStockCache()
    return { cartStore, stockCache }
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
      
      // Navigation state
      viewMode: 'products',
      currentSubcategory: null,
      categorySearch: '',
      breadcrumbs: [],
      
      // Infinite scroll
      displayedItemsCount: 24,
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
      
      // Promotions
      promoCode: '',
      appliedPromotion: null,
      availablePromotions: [],
      showOtherPromotions: false,
      showPromoSuggestions: false, 
      filteredPromoSuggestions: [],
      
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

      // Caching utilities
      cacheTTLms: 24 * 60 * 60 * 1000, // 24 hours for localStorage
      memCacheTTLms: 30 * 60 * 1000, // 30 minutes for in-memory cache
      storage: null,
      memCache: null,
      
      // Stock refresh
      stockRefreshInterval: null,
      stockRefreshIntervalMs: 5 * 60 * 1000, // 5 minutes
      isRefreshingStock: false,
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
    
    // initialize caches
    const ls = useLocalStorage()
    this.storage = ls.withPrefix('newOrder')
    this.memCache = useCache({ maxEntries: 300 })
    
    // Load custom categories and products from localStorage
    this.loadCustomCategories()
    this.loadCustomCategoryProducts()
    this.loadIdCounters()
    
    // Hydrate from localStorage immediately to avoid spinner on revisit
    try {
      const cachedCategories = this.storage.getItem('categories', null)
      if (Array.isArray(cachedCategories) && cachedCategories.length > 0) {
        this.backendCategories = cachedCategories
        const lastActive = this.storage.getItem('lastActiveCategory', null)
        const fallbackCat = cachedCategories[0]?.id
        const catId = cachedCategories.find(c => c.id === lastActive) ? lastActive : fallbackCat
        if (catId) {
          this.activeCategory = catId
          const cachedProducts = this.storage.getItem(`products:${catId}:__all__`, null)
          if (Array.isArray(cachedProducts)) {
            this.products = cachedProducts
          }
        }
      }
    } catch (_) {}
    await this.initializeSession()
    await this.loadCategories()
    
    // ✅ ADD: Debug log to verify category IDs
    console.log('\n📋 ========================================')
    console.log('   LOADED CATEGORIES')
    console.log('📋 ========================================')
    this.categories.forEach(cat => {
      console.log(`   ${cat.name}: ${cat.id}`)
    })
    console.log('📋 ========================================\n')
    
    // Set up periodic stock refresh (skip immediate auto-refresh if returning from checkout)
    this.startStockRefresh(shouldRefreshStock !== 'true')
    
    // Fetch promotions since cart is always visible
    this.fetchAvailablePromotions()
    
    // If returning from checkout, perform targeted refresh when possible, fallback to full refresh
    if (shouldRefreshStock === 'true') {
      try {
        if (targetedProductIds.length > 0) {
          await this.refreshSpecificStockLevels(targetedProductIds)
        } else {
          await this.refreshStockLevels()
        }
      } finally {
        try { sessionStorage.removeItem('refreshProductIds') } catch (_) {}
      }
    }
  },

  beforeUnmount() {
    // Clean up stock refresh interval
    if (this.stockRefreshInterval) {
      clearInterval(this.stockRefreshInterval)
      this.stockRefreshInterval = null
    }
  },

  watch: {
    // Watch cart changes to update available promotions
    'cartStore.items': {
      handler() {
        this.fetchAvailablePromotions()
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
    
    // Cart subtotal
    cartSubtotal() {
      return this.cartStore.total
    },
    
    // Total items from store
    totalItems() {
      return this.cartStore.itemCount
    },
    
    // Calculate promo discount
    promoDiscount() {
      if (!this.appliedPromotion) return 0
      
      const promotion = this.appliedPromotion
      const targetType = promotion.discount_config?.target_type
      const targetIds = promotion.discount_config?.target_ids || []
      
      let eligibleAmount = 0
      
      if (targetType === 'all') {
        eligibleAmount = this.cartSubtotal
      } else if (targetType === 'categories') {
        eligibleAmount = this.cartItems
          .filter(item => {
            const product = this.products.find(p => p.id === item.productId)
            return product && targetIds.includes(product.category)
          })
          .reduce((sum, item) => sum + item.subtotal, 0)
      } else if (targetType === 'products') {
        eligibleAmount = this.cartItems
          .filter(item => targetIds.includes(item.productId))
          .reduce((sum, item) => sum + item.subtotal, 0)
      }
      
      let discount = 0
      
      if (promotion.type === 'percentage') {
        discount = eligibleAmount * (promotion.discount_value / 100)
      } else if (promotion.type === 'fixed') {
        discount = Math.min(promotion.discount_value, eligibleAmount)
      }
      
      return Math.round(discount * 100) / 100
    },
    
    // Final total with discounts
    finalTotal() {
      return Math.max(0, this.cartSubtotal - this.promoDiscount)
    },
    
    // Best promotion (highest discount)
    bestPromotion() {
      if (this.availablePromotions.length === 0) return null
      
      return this.availablePromotions.reduce((best, current) => {
        return current.calculatedDiscount > best.calculatedDiscount ? current : best
      })
    },
    
    // Other promotions (excluding best)
    otherPromotions() {
      if (!this.bestPromotion) return this.availablePromotions
      
      return this.availablePromotions.filter(
        promo => promo._id !== this.bestPromotion._id
      )
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
    
    startStockRefresh(refreshImmediately = true) {
      if (refreshImmediately) {
        this.refreshStockLevels()
      }
      this.stockRefreshInterval = setInterval(() => {
        this.refreshStockLevels()
      }, this.stockRefreshIntervalMs)
    },
    
    async manualStockRefresh() {
      if (this.isRefreshingStock) return
      
      try {
        this.isRefreshingStock = true
        console.log('🔄 Manual stock refresh triggered')
        
        // Clear cache for current category to force fresh data
        if (this.activeCategory) {
          const cacheKey = `products:${this.activeCategory}:${this.currentSubcategory?.name || '__all__'}`
          this.storage?.removeItem(cacheKey)
          this.memCache?.delete(cacheKey)
          console.log('🗑️ Cleared cache for:', cacheKey)
        }
        
        await this.refreshStockLevels()
        
        // Force reload current category products
        if (this.activeCategory) {
          await this.loadProducts(this.activeCategory, this.currentSubcategory?.name)
        }
        
        // Show success feedback
        console.log('✅ Manual stock refresh completed')
        
      } catch (error) {
        console.error('❌ Manual stock refresh failed:', error)
        alert('Failed to refresh stock levels. Please try again.')
      } finally {
        this.isRefreshingStock = false
      }
    },
    
    async refreshStockLevels() {
      try {
        // Initialize stockUpdates at the beginning
        let stockUpdates = {}
        
        // Get all unique product IDs currently in cache
        const productIdsToRefresh = new Set()
        
        // Add products from current view
        this.products.forEach(p => productIdsToRefresh.add(p.id))
        
        // Add products from custom categories
        Object.values(this.customCategoryProducts).forEach(products => {
          products.forEach(p => {
            // Use originalId for custom category products
            if (p.originalId) productIdsToRefresh.add(p.originalId)
            else productIdsToRefresh.add(p.id)
          })
        })
        
        if (productIdsToRefresh.size === 0) {
          return
        }
        
        // Fetch fresh stock data in batch
        const productIds = Array.from(productIdsToRefresh)
        
        try {
          const freshProducts = await productsAPI.getProductsBatch(productIds)
          
          if (!Array.isArray(freshProducts) || freshProducts.length === 0) {
            return
          }
          
          // Build a map of productId -> fresh stock (use total_stock if available, otherwise null)
          stockUpdates = {}
          freshProducts.forEach(product => {
            // Use total_stock if available, otherwise fallback to batch_stock
            const stockValue = (product.total_stock !== undefined && product.total_stock !== null)
              ? product.total_stock
              : (product.batch_stock !== undefined && product.batch_stock !== null)
              ? product.batch_stock
              : null
            
            console.log(`🔄 Stock update for ${product.name}:`, {
              id: product.id,
              total_stock: product.total_stock,
              batch_stock: product.batch_stock,
              selectedValue: stockValue
            })
            
            if (product.id) {
              stockUpdates[product.id] = stockValue
            }
          })
          
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
            console.error('  ❌ Error reading localStorage keys:', error)
          }
          
          let updatedCount = 0
          allKeys.forEach(fullKey => {
            try {
              const key = fullKey.replace('newOrder_', '')
              const cached = this.storage?.getItem(key, null)
              
              if (!Array.isArray(cached)) return
              
              let wasUpdated = false
              const updated = cached.map(product => {
                const newStock = stockUpdates[product.id]
                
                if (newStock !== null && newStock !== product.total_stock) {
                  wasUpdated = true
                  return {
                    ...product,
                    total_stock: newStock
                  }
                }
                
                return product
              })
              
              if (wasUpdated) {
                this.storage?.setItem(key, updated, this.cacheTTLms)
                this.memCache?.set(key, updated, this.memCacheTTLms)
                updatedCount++
              }
              
            } catch (error) {
              console.error('  ❌ Error updating cache key', fullKey, ':', error)
            }
          })
          
          
          
        } catch (error) {
          console.error('  ❌ Failed to fetch products batch:', error)
          return
        }
        
        // Update custom category products with fresh stock data
        this.updateCustomCategoryProductsStock(stockUpdates)
        
        // Reload current view to show updated stock
        if (this.activeCategory) {
          const cacheKey = `products:${this.activeCategory}:${this.currentSubcategory?.name || '__all__'}`
          const refreshedProducts = this.storage?.getItem(cacheKey, null)
          if (Array.isArray(refreshedProducts)) {
            console.log('🔄 Reloading products after stock update:', refreshedProducts.length, 'products')
            // Log first few products to see their stock values
            refreshedProducts.slice(0, 3).forEach(p => {
              console.log(`  - ${p.name}: total_stock=${p.total_stock}`)
            })
            this.products = refreshedProducts
          }
        }
        
      } catch (error) {
        console.error('❌ Stock refresh failed:', error)
        // Don't throw - this is a background operation
      }
    },
    
    // Targeted stock refresh for specific product IDs
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
        
        // Build updates map (use total_stock if available, otherwise null)
        const stockUpdates = {}
        freshProducts.forEach(product => {
          const stockValue = (product.total_stock !== undefined && product.total_stock !== null)
            ? product.total_stock
            : (product.batch_stock !== undefined && product.batch_stock !== null)
            ? product.batch_stock
            : null
          if (product.id) {
            stockUpdates[product.id] = stockValue
          }
        })
        
        // Update current in-memory view (products)
        if (Array.isArray(this.products) && this.products.length > 0) {
          let changed = false
          const updated = this.products.map(p => {
            const newStock = stockUpdates[p.id]
            if (newStock !== null && newStock !== p.total_stock) {
              changed = true
              return { ...p, total_stock: newStock }
            }
            return p
          })
          if (changed) {
            this.products = updated
          }
        }
        
        // Update custom category products with fresh stock data
        this.updateCustomCategoryProductsStock(stockUpdates)
        
        // Update localStorage-backed caches for any categories that include these products
        const allKeys = []
        try {
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i)
            if (key && key.startsWith('newOrder_products:')) {
              allKeys.push(key)
            }
          }
        } catch (error) {
          console.error('  ❌ Error reading localStorage keys:', error)
        }
        
        let updatedCount = 0
        allKeys.forEach(fullKey => {
          try {
            const key = fullKey.replace('newOrder_', '')
            const cached = this.storage?.getItem(key, null)
            if (!Array.isArray(cached)) return
            let wasUpdated = false
            const updated = cached.map(product => {
              const newStock = stockUpdates[product.id]
              if (newStock !== undefined && newStock !== product.total_stock) {
                wasUpdated = true
                return { ...product, total_stock: newStock }
              }
              return product
            })
            if (wasUpdated) {
              this.storage?.setItem(key, updated, this.cacheTTLms)
              this.memCache?.set(key, updated, this.memCacheTTLms)
              updatedCount++
            }
          } catch (error) {
            console.error('  ❌ Error updating cache key', fullKey, ':', error)
          }
        })
        
        
        // Update custom category items in-memory if they reference affected products
        try {
          Object.keys(this.customCategoryProducts || {}).forEach(catId => {
            const items = this.customCategoryProducts[catId]
            if (!Array.isArray(items) || items.length === 0) return
            let changed = false
            const updated = items.map(item => {
              const baseId = item.originalId || item.id
              const newStock = stockUpdates[baseId]
              if (newStock !== undefined && newStock !== item.total_stock) {
                changed = true
                return { ...item, total_stock: newStock }
              }
              return item
            })
            if (changed) {
              this.customCategoryProducts[catId] = updated
            }
          })
        } catch (error) {
          console.error('  ❌ Error updating custom category items:', error)
        }
        
        // If current view is activeCategory, try to re-hydrate from cache to ensure consistency
        if (this.activeCategory) {
          const cacheKey = `products:${this.activeCategory}:${this.currentSubcategory?.name || '__all__'}`
          const refreshedProducts = this.storage?.getItem(cacheKey, null)
          if (Array.isArray(refreshedProducts)) {
            // Merge in-memory updates with cache to avoid flicker
            const merged = refreshedProducts.map(prod => {
              const newStock = stockUpdates[prod.id]
              return newStock !== undefined ? { ...prod, total_stock: newStock } : prod
            })
            this.products = merged
          }
        }
      } catch (error) {
        console.error('❌ Targeted stock refresh failed:', error)
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
        console.error('❌ Session initialization failed:', error)
        this.error = error.message
        alert(`Failed to initialize session: ${error.message}\n\nPlease refresh the page or log in again.`)
      }
    },

    // ✅ FIX: Load ALL products when modal opens
    async openProductSelectorModal() {
      this.showProductSelectorModal = true
      
      // Always load products from all available categories
      await this.loadAllProductsForSelection()
      
      // Then select the first category
      if (this.availableSourceCategories.length > 0) {
        this.selectedSourceCategory = this.availableSourceCategories[0].id
      }
    },

    // ✅ FIX: New method to load all products at once
    async loadAllProductsForSelection() {
      try {
        this.productsLoading = true
        
        // Load from ALL available source categories (excluding current active category)
        // This will use cache first, then localStorage, then API
        const productPromises = this.availableSourceCategories.map(category => {
          return this.getProductsCached(category.id)
        })
        
        // Wait for all requests to complete
        const allCategoryProducts = await Promise.all(productPromises)
        
        // Flatten all products into a single array
        this.allProducts = allCategoryProducts.flat()
        
      } catch (error) {
        console.error('Failed to load all products:', error)
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
        
        // Try cache first
        const cached = this.getCategoriesCached()
        if (cached) {
          this.backendCategories = cached
        } else {
          const fresh = await categoriesAPI.getActiveCategories()
          this.backendCategories = Array.isArray(fresh) ? fresh : []
          this.setCategoriesCache(this.backendCategories)
        }
        
        if (this.backendCategories.length > 0 && !this.activeCategory) {
          this.activeCategory = this.backendCategories[0].id
          await this.selectCategory(this.backendCategories[0].id)
        }
        
      } catch (error) {
        console.error('Failed to load categories:', error)
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
      // Persist last active category (24 hours)
      try { this.storage?.setItem('lastActiveCategory', categoryId, this.cacheTTLms) } catch (_) {}
      
      const category = this.categories.find(cat => cat.id === categoryId)
      
      if (category && !category.isCustom && category.hasSubcategories) {
        this.viewMode = 'subcategories'
        this.breadcrumbs = [
          { name: category.name, type: 'categories', categoryId: categoryId }
        ]
      } else {
        this.viewMode = 'products'
        if (!category.isCustom) {
          // Show cached products immediately if any
          const cachedProducts = this.storage?.getItem(`products:${categoryId}:__all__`, null)
          if (Array.isArray(cachedProducts)) {
            this.products = cachedProducts
          }
          await this.loadProducts(categoryId)
        }
      }
    },

    async loadProducts(categoryId, subcategoryName = null) {
      try {
        this.error = null
        
        if (this.isCustomCategory) {
          this.productsLoading = false
          return
        }
        
        // Try immediate cached read (no spinner, no network)
        const cacheKey = `products:${categoryId}:${subcategoryName || '__all__'}`
        const lsHit = this.storage?.getItem(cacheKey, null)
        if (Array.isArray(lsHit)) {
          this.products = lsHit
          return
        }
        
        // No cache: show loader and fetch
        this.productsLoading = true
        const products = await this.getProductsCached(categoryId, subcategoryName)
        this.products = products
        
      } catch (error) {
        console.error('Failed to load products:', error)
        this.error = error.message
        this.products = []
      } finally {
        this.productsLoading = false
      }
    },

    // Cached fetchers
    getCategoriesCached() {
      // in-memory first
      const k = 'categories'
      const memHit = this.memCache?.get(k, null)
      if (memHit) return memHit
      // localStorage next
      const lsHit = this.storage?.getItem(k, null)
      if (lsHit) {
        this.memCache?.set(k, lsHit, this.memCacheTTLms)
        return lsHit
      }
      return null
    },
    setCategoriesCache(categories) {
      const k = 'categories'
      this.memCache?.set(k, categories, this.memCacheTTLms)
      this.storage?.setItem(k, categories, this.cacheTTLms)
    },
    async getProductsCached(categoryId, subcategoryName = null) {
      const key = `products:${categoryId}:${subcategoryName || '__all__'}`
      const memHit = this.memCache?.get(key, null)
      if (memHit) return memHit
      const lsHit = this.storage?.getItem(key, null)
      if (lsHit) {
        this.memCache?.set(key, lsHit, this.memCacheTTLms)
        return lsHit
      }
      const fresh = await productsAPI.getProductsByCategory(categoryId, subcategoryName)
      const normalized = Array.isArray(fresh) ? fresh : []
      this.memCache?.set(key, normalized, this.memCacheTTLms)
      this.storage?.setItem(key, normalized, this.cacheTTLms)
      return normalized
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
      if (confirm('Are you sure you want to delete this category and all its items?')) {
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
    // PROMOTIONS
    // ================================================================
    
    async fetchAvailablePromotions() {
      if (this.cartItems.length === 0) {
        this.availablePromotions = []
        this.filteredPromoSuggestions = []
        return
      }
      
      try {
        console.log('🎟️ Fetching available promotions...')
        console.log('📦 Cart items:', this.cartItems.length)
        
        // ✅ Fetch active promotions from backoffice endpoint
        const response = await api.get('/promotions/active/')
        
        console.log('📦 Full response:', response)
        console.log('📦 Response data:', response.data)
        
        // ✅ LOG RAW PROMOTION DATA FOR DEBUGGING
        console.log('\n🔍 ========================================')
        console.log('   RAW PROMOTION DATA')
        console.log('🔍 ========================================')
        
        let allPromotions = []
        
        if (response && response.data) {
          if (response.data.success === true) {
            allPromotions = response.data.promotions || []
            
            // ✅ LOG EACH PROMOTION IN DETAIL
            allPromotions.forEach((promo, index) => {
              console.log(`\nPromotion ${index + 1}: ${promo.name}`)
              console.log('   Full object:', promo)
              console.log('   discount_config:', promo.discount_config)
              console.log('   discount_config type:', typeof promo.discount_config)
              
              // ✅ Check if it's a string that needs parsing
              if (typeof promo.discount_config === 'string') {
                console.log('   ⚠️ discount_config is a STRING, needs parsing!')
                try {
                  const parsed = JSON.parse(promo.discount_config)
                  console.log('   ✅ Parsed discount_config:', parsed)
                } catch (e) {
                  console.log('   ❌ Failed to parse:', e)
                }
              }
            })
            
          } else {
            console.warn('⚠️ Success is not true')
          }
        }
        
        console.log('🔍 ========================================\n')
        
        console.log('🔍 ========================================\n')
        
        
        if (!Array.isArray(allPromotions)) {
          console.error('❌ allPromotions is not an array:', typeof allPromotions)
          this.availablePromotions = []
          this.filteredPromoSuggestions = []
          return
        }
        
        if (allPromotions.length === 0) {
          console.warn('⚠️ No promotions found')
          this.availablePromotions = []
          this.filteredPromoSuggestions = []
          return
        }
        
        // ✅ FIX: Parse discount_config if it's a string
        allPromotions = allPromotions.map(promo => {
          // Check if discount_config is a string that needs parsing
          if (typeof promo.discount_config === 'string') {
            try {
              promo.discount_config = JSON.parse(promo.discount_config)
              console.log(`✅ Parsed discount_config for: ${promo.name}`, promo.discount_config)
            } catch (e) {
              console.error(`❌ Failed to parse discount_config for ${promo.name}:`, e)
              // Set default if parsing fails
              promo.discount_config = {
                target_type: 'all',
                target_ids: []
              }
            }
          }
          
          // ✅ ENSURE: discount_config exists
          if (!promo.discount_config) {
            console.warn(`⚠️ Missing discount_config for ${promo.name}, using default`)
            promo.discount_config = {
              target_type: 'all',
              target_ids: []
            }
          }
          
          // ✅ ENSURE: discount_config has required fields
          if (!promo.discount_config.target_type) {
            console.warn(`⚠️ Missing target_type for ${promo.name}, defaulting to 'all'`)
            promo.discount_config.target_type = 'all'
          }
          
          if (!promo.discount_config.target_ids) {
            console.warn(`⚠️ Missing target_ids for ${promo.name}, defaulting to []`)
            promo.discount_config.target_ids = []
          }
          
          return promo
        })
        
        console.log('✅ Promotions after parsing:', allPromotions)
        
        // Calculate discount for each promotion
        const applicablePromotions = []
        
        for (const promo of allPromotions) {
          try {
            const discount = this.calculatePromotionDiscount(promo)
            
            if (discount > 0) {
              applicablePromotions.push({
                ...promo,
                calculatedDiscount: discount,
                isApplicable: true
              })
            }
          } catch (calcError) {
            console.error(`❌ Error calculating discount for ${promo.name}:`, calcError)
          }
        }
        
        // Sort by discount amount (highest first)
        applicablePromotions.sort((a, b) => b.calculatedDiscount - a.calculatedDiscount)
        
        this.availablePromotions = applicablePromotions
        this.filteredPromoSuggestions = applicablePromotions
        
      } catch (error) {
        console.error('❌ Failed to fetch promotions:', error)
        console.error('❌ Error details:', error.response?.data)
        
        this.availablePromotions = []
        this.filteredPromoSuggestions = []
      }
    },
    
    calculatePromotionDiscount(promotion) {
      console.log('\n🎁 ========================================')
      console.log(`   Calculating discount for: ${promotion.name}`)
      console.log('🎁 ========================================')
      
      // ✅ SAFETY CHECK: Handle missing discount_config
      if (!promotion.discount_config) {
        console.warn(`⚠️ Promotion "${promotion.name}" missing discount_config!`)
        return 0
      }
      
      const targetType = promotion.discount_config.target_type
      const targetIds = promotion.discount_config.target_ids || []
      
      console.log(`   🎯 Type: ${promotion.type}`)
      console.log(`   🎯 Value: ${promotion.discount_value}${promotion.type === 'percentage' ? '%' : ' PHP'}`)
      console.log(`   🎯 Target Type: ${targetType}`)
      console.log(`   🎯 Target IDs:`, targetIds)
      console.log(`   📦 Cart Subtotal: ₱${this.cartSubtotal}`)
      console.log(`   📦 Cart Items: ${this.cartItems.length}`)
      
      let eligibleAmount = 0
      let eligibleItems = []
      
      if (targetType === 'all') {
        eligibleAmount = this.cartSubtotal
        console.log(`   💰 All items eligible: ₱${eligibleAmount}`)
      } else if (targetType === 'categories') {
        console.log('\n   🔍 Checking category matches...')
        console.log(`   🔍 Available products in memory:`, this.products.length)
        
        // Get eligible items from target categories
        eligibleItems = this.cartItems.filter(item => {
          const product = this.products.find(p => p.id === item.productId)
          
          if (!product) {
            console.log(`   ⚠️ Product not found: ${item.productId} (${item.productName})`)
            return false
          }
          
          const productCategory = product.category
          const isEligible = targetIds.includes(productCategory)
          
          console.log(`      ${isEligible ? '✅' : '❌'} ${product.name}`)
          console.log(`         Product Category: "${productCategory}"`)
          console.log(`         Target Categories:`, targetIds)
          console.log(`         Match: ${isEligible}`)
          console.log(`         Subtotal: ₱${item.subtotal}`)
          
          return isEligible
        })
        
        eligibleAmount = eligibleItems.reduce((sum, item) => sum + item.subtotal, 0)
        console.log(`   💰 Category items eligible: ₱${eligibleAmount}`)
      } else if (targetType === 'products') {
        console.log('\n   🔍 Checking product matches...')
        
        // Get eligible items from target products
        eligibleItems = this.cartItems.filter(item => {
          const isEligible = targetIds.includes(item.productId)
          
          console.log(`      ${isEligible ? '✅' : '❌'} ${item.productName}`)
          console.log(`         Product ID: "${item.productId}"`)
          console.log(`         Target IDs:`, targetIds)
          console.log(`         Match: ${isEligible}`)
          console.log(`         Subtotal: ₱${item.subtotal}`)
          
          return isEligible
        })
        
        eligibleAmount = eligibleItems.reduce((sum, item) => sum + item.subtotal, 0)
        console.log(`   💰 Product items eligible: ₱${eligibleAmount}`)
      }
      
      if (eligibleAmount === 0) {
        console.log(`   ❌ No eligible items found`)
        return 0
      }
      
      let discount = 0
      
      if (promotion.type === 'percentage') {
        discount = eligibleAmount * (promotion.discount_value / 100)
        console.log(`\n   💰 Calculation: ₱${eligibleAmount} × ${promotion.discount_value}% = ₱${discount}`)
      } else if (promotion.type === 'fixed') {
        discount = Math.min(promotion.discount_value, eligibleAmount)
        console.log(`\n   💰 Calculation: min(₱${promotion.discount_value}, ₱${eligibleAmount}) = ₱${discount}`)
      }
      
      const finalDiscount = Math.round(discount * 100) / 100
      console.log(`\n   ✅ FINAL DISCOUNT: ₱${finalDiscount}`)
      console.log('🎁 ========================================\n')
      
      return finalDiscount
    },
    
    async applyPromotionById(promotionId) {
      try {
        const promotion = this.availablePromotions.find(p => p._id === promotionId)
        
        if (!promotion) {
          alert('Promotion not found')
          return
        }
        
        // Validate promotion is still active
        const now = new Date()
        const startDate = new Date(promotion.start_date)
        const endDate = new Date(promotion.end_date)
        
        if (now < startDate) {
          alert('This promotion has not started yet')
          return
        }
        
        if (now > endDate) {
          alert('This promotion has expired')
          return
        }
        
        this.appliedPromotion = promotion
        
      } catch (error) {
        console.error('❌ Failed to apply promotion:', error)
        alert('Failed to apply promotion')
      }
    },
    
    async applyPromoCodeManually() {
      if (!this.promoCode.trim()) {
        alert('Please enter a promo code')
        return
      }
      
      try {
        // Find promotion by name/code in available promotions first
        const foundPromo = this.availablePromotions.find(
          p => p.name.toLowerCase() === this.promoCode.trim().toLowerCase()
        )
        
        if (foundPromo) {
          this.applyPromotionById(foundPromo._id)
          this.promoCode = ''
          return
        }
        
        // If not found in available, try API
        const response = await api.get('/promotions/active/')
        
        if (response.data.success) {
          const allPromotions = response.data.data.promotions || []
          const matchingPromo = allPromotions.find(
            p => p.name.toLowerCase() === this.promoCode.trim().toLowerCase()
          )
          
          if (matchingPromo) {
            // Check if it applies to cart
            const discount = this.calculatePromotionDiscount(matchingPromo)
            
            if (discount > 0) {
              this.appliedPromotion = matchingPromo
              this.promoCode = ''
            } else {
              alert('This promo code does not apply to items in your cart')
            }
          } else {
            alert('Invalid promo code')
          }
        }
        
      } catch (error) {
        console.error('❌ Manual promo failed:', error)
        alert('Failed to apply promo code')
      }
    },
    
    removePromotion() {
      this.appliedPromotion = null
      this.promoCode = ''
    },

    // ================================================================
    // CART MANAGEMENT
    // ================================================================
    
    addToCart(product) {
      try {
        if (!product.id || !product.name || !product.price) {
          throw new Error('Invalid product data')
        }
        
        if (product.total_stock <= 0) {
          alert(`${product.name} is out of stock!`)
          return
        }
        
        this.cartStore.addItem(product)
        
      } catch (error) {
        console.error('❌ Add to cart failed:', error)
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
    
    checkout() {
      if (this.cartStore.isEmpty) {
        alert('Your cart is empty!')
        return
      }
      
      // ✅ FIXED: Store complete promotion info for checkout
      if (this.appliedPromotion) {
        const promotionData = {
          promotion_id: this.appliedPromotion._id,
          promotion_name: this.appliedPromotion.name,
          type: this.appliedPromotion.type,
          discount_value: this.appliedPromotion.discount_value,
          discount_config: this.appliedPromotion.discount_config,
          discount_amount: this.promoDiscount
        }
        
        console.log('💾 Saving promotion to session:', promotionData)
        sessionStorage.setItem('appliedPromotion', JSON.stringify(promotionData))
      } else {
        sessionStorage.removeItem('appliedPromotion')
      }
      
      this.$router.push('/checkout')
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
                console.log(`🔄 Updating custom category product ${product.name}: ${product.total_stock} → ${newStock}`)
                product.total_stock = newStock
                updated = true
              }
            })
          }
        })
        
        if (updated) {
          // Save updated custom category products
          this.saveCustomCategoryProducts()
          console.log('✅ Updated custom category products with fresh stock data')
        }
        
      } catch (error) {
        console.error('❌ Failed to update custom category products stock:', error)
      }
    },

    // ================================================================
    // PERSISTENCE METHODS
    // ================================================================
    
    saveCustomCategories() {
      try {
        this.storage?.setItem('customCategories', this.customCategories, this.cacheTTLms)
        this.memCache?.set('customCategories', this.customCategories, this.memCacheTTLms)
      } catch (error) {
        console.error('❌ Failed to save custom categories:', error)
      }
    },
    
    loadCustomCategories() {
      try {
        // Try memory cache first
        const memHit = this.memCache?.get('customCategories', null)
        if (memHit) {
          this.customCategories = memHit
          return
        }
        
        // Try localStorage
        const lsHit = this.storage?.getItem('customCategories', null)
        if (Array.isArray(lsHit)) {
          this.customCategories = lsHit
          this.memCache?.set('customCategories', lsHit, this.memCacheTTLms)
        }
      } catch (error) {
        console.error('❌ Failed to load custom categories:', error)
      }
    },
    
    saveCustomCategoryProducts() {
      try {
        this.storage?.setItem('customCategoryProducts', this.customCategoryProducts, this.cacheTTLms)
        this.memCache?.set('customCategoryProducts', this.customCategoryProducts, this.memCacheTTLms)
      } catch (error) {
        console.error('❌ Failed to save custom category products:', error)
      }
    },
    
    loadCustomCategoryProducts() {
      try {
        // Try memory cache first
        const memHit = this.memCache?.get('customCategoryProducts', null)
        if (memHit) {
          this.customCategoryProducts = memHit
          return
        }
        
        // Try localStorage
        const lsHit = this.storage?.getItem('customCategoryProducts', null)
        if (lsHit && typeof lsHit === 'object') {
          this.customCategoryProducts = lsHit
          this.memCache?.set('customCategoryProducts', lsHit, this.memCacheTTLms)
        }
      } catch (error) {
        console.error('❌ Failed to load custom category products:', error)
      }
    },
    
    saveIdCounters() {
      try {
        this.storage?.setItem('nextCategoryId', this.nextCategoryId, this.cacheTTLms)
        this.storage?.setItem('nextProductId', this.nextProductId, this.cacheTTLms)
      } catch (error) {
        console.error('❌ Failed to save ID counters:', error)
      }
    },
    
    loadIdCounters() {
      try {
        const savedCategoryId = this.storage?.getItem('nextCategoryId', null)
        const savedProductId = this.storage?.getItem('nextProductId', null)
        
        if (savedCategoryId && savedCategoryId > this.nextCategoryId) {
          this.nextCategoryId = savedCategoryId
        }
        if (savedProductId && savedProductId > this.nextProductId) {
          this.nextProductId = savedProductId
        }
      } catch (error) {
        console.error('❌ Failed to load ID counters:', error)
      }
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
@import '@/assets/styles/NewOrder.css'

</style>