<template>
  <div class="new-order-page">
    <!-- Main Content Area -->
    <div class="main-area">
      <div class="no-contents">
        <!-- Header Section -->
        <div class="no-header">
          <div class="category-search">
            <input 
              type="text" 
              v-model="categorySearch" 
              placeholder="Search products..." 
              class="search-input"
            />
          </div>
          
          <!-- Categories -->
          <div class="header-bot">
            <div class="categories-container">
              <div 
                v-for="category in categories" 
                :key="category.id"
                :class="['cat-card', { active: activeCategory === category.id }]"
                @click="selectCategory(category.id)">
                <div class="cat-icon">
                  <component :is="category.icon" />
                </div>
                <span class="cat-label">{{ category.name }}</span>
                <button 
                  v-if="category.isCustom"
                  class="delete-category-btn"
                  @click.stop="deleteCategory(category.id)"
                  title="Delete Category">
                  <X :size="12" />
                </button>
              </div>
              
              <!-- Add Category Button -->
              <div class="cat-card add-category" @click="showCategoryModal = true">
                <div class="cat-icon">
                  <Plus :size="24" />
                </div>
                <span class="cat-label">Add Category</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Navigation Breadcrumbs -->
        <div v-if="breadcrumbs.length > 0" class="breadcrumb-nav">
          <button 
            v-for="(crumb, index) in breadcrumbs" 
            :key="index"
            class="breadcrumb-item"
            @click="navigateTo(crumb)">
            {{ crumb.name }}
            <ChevronRight v-if="index < breadcrumbs.length - 1" :size="16" />
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading || productsLoading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <p class="error-message">{{ error }}</p>
          <button class="btn-primary" @click="retryLoad">Retry</button>
        </div>

        <!-- Products Grid -->
        <div v-else class="products-grid">
          <div 
            v-for="product in paginatedProducts" 
            :key="product.id"
            class="product-card"
            @click="handleProductClick(product)">
            <div class="product-image">
              <img :src="product.image" :alt="product.name" loading="lazy" />
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <p v-if="!product.isSubcategory" class="product-description">
                Stock: {{ product.stock || 0 }}
              </p>
              <div v-if="!product.isSubcategory" class="product-price">
                ₱{{ formatPrice(product.price) }}
              </div>
              <div v-else class="subcategory-indicator">
                <ChevronRight :size="16" /> View Items
              </div>
            </div>
            <button 
              v-if="!product.isSubcategory && isCustomCategory" 
              class="delete-product-btn" 
              @click.stop="removeFromCategory(product.id)" 
              title="Remove from category">
              <X :size="14" />
            </button>
          </div>
          
          <!-- Add Products Option (Custom Categories Only) -->
          <div 
            v-if="viewMode === 'products' && isCustomCategory && customCategoryItems.length < 8"
            class="product-card add-item-card"
            @click="showProductSelectorModal = true">
            <div class="add-item-content">
              <ShoppingBag :size="32" />
              <p>Add Products</p>
              <small>{{ allAvailableProductsCount }} available</small>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="viewMode === 'products' && totalPages > 1" class="pagination">
          <button 
            class="page-btn" 
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)">
            Previous
          </button>
          
          <span class="page-info">
            Page {{ currentPage }} of {{ totalPages }} ({{ filteredProducts.length }} items)
          </span>
          
          <button 
            class="page-btn" 
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)">
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Category Creation Modal -->
    <div v-if="showCategoryModal" class="modal-overlay" @click="closeCategoryModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Create New Category</h3>
          <button class="close-btn" @click="closeCategoryModal">
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
              class="form-input"
              maxlength="20"
            />
          </div>
          <div class="form-group">
            <label>Icon</label>
            <div class="icon-selector">
              <div 
                v-for="iconOption in iconOptions" 
                :key="iconOption.name"
                :class="['icon-option', { selected: newCategory.icon === iconOption.name }]"
                @click="newCategory.icon = iconOption.name">
                <component :is="iconOption.name" :size="20" />
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeCategoryModal">Cancel</button>
          <button 
            class="btn-primary" 
            @click="createCategory" 
            :disabled="!newCategory.name.trim()">
            Create Category
          </button>
        </div>
      </div>
    </div>

    <!-- Product Selection Modal -->
    <div v-if="showProductSelectorModal" class="modal-overlay" @click="closeProductSelectorModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>Add Products to {{ getCurrentCategoryName() }}</h3>
          <button class="close-btn" @click="closeProductSelectorModal">
            <X :size="20" />
          </button>
        </div>
        <div class="modal-body">
          <!-- Category Tabs -->
          <div class="product-selector-tabs">
            <button 
              v-for="category in availableSourceCategories" 
              :key="category.id"
              :class="['tab-btn', { active: selectedSourceCategory === category.id }]"
              @click="selectedSourceCategory = category.id">
              {{ category.name }} ({{ getProductCountForCategory(category.id) }})
            </button>
          </div>
          
          <!-- Search -->
          <div class="product-search">
            <input 
              type="text" 
              v-model="productSearchQuery" 
              placeholder="Search products..."
              class="search-input"
            />
          </div>
          
          <!-- Loading State -->
          <div v-if="productsLoading" class="loading-state">
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
                <img :src="product.image" :alt="product.name" loading="lazy" />
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
          <button class="btn-secondary" @click="closeProductSelectorModal">Cancel</button>
          <button 
            class="btn-primary" 
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
    <div v-if="showCart" class="cart-sidebar">
      <div class="cart-header">
        <h2>New Order</h2>
        <button class="cart-close" @click="closeCart">
          <X :size="20" />
        </button>
      </div>
      
      <div class="cart-items">
        <div v-if="cartItems.length === 0" class="empty-cart-message">
          <ShoppingCart :size="48" class="empty-cart-icon" />
          <p>Your cart is empty</p>
          <p>Add items to get started!</p>
        </div>
        
        <div v-for="item in cartItems" :key="item.productId" class="cart-item">
          <img :src="item.image" :alt="item.productName" class="cart-item-image" />
          <div class="cart-item-info">
            <h4>{{ item.productName }}</h4>
            <p class="item-price">₱{{ formatPrice(item.price) }}</p>
          </div>
          <div class="cart-item-controls">
            <button 
              @click="decreaseQuantity(item)" 
              class="quantity-btn minus">
              <Minus :size="16" />
            </button>
            <span class="quantity">{{ item.quantity }}</span>
            <button 
              @click="increaseQuantity(item)" 
              class="quantity-btn plus">
              <Plus :size="16" />
            </button>
          </div>
          <div class="cart-item-subtotal">
            ₱{{ formatPrice(item.subtotal) }}
          </div>
          <button 
            @click="removeFromCart(item)" 
            class="remove-btn">
            <Trash2 :size="16" />
          </button>
        </div>
      </div>
      
      <!-- Cart Footer -->
      <div class="cart-footer">
        
       <!-- Manual Promo Code with Smart Suggestions -->
        <div class="promo-section">
          <h4 class="section-title">Have a Promo Code?</h4>
          
          <div class="promo-input-wrapper">
            <div class="input-group">
              <input 
                type="text" 
                class="form-control" 
                placeholder="Enter promo code or select below"
                v-model="promoCode"
                @focus="showPromoSuggestions = true"
                @blur="hidePromoSuggestionsDelayed"
                @input="filterPromoSuggestions"
              />
              <button 
                class="btn btn-primary" 
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
              class="promo-suggestions-dropdown"
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
        <div class="cart-summary">
          <!-- Subtotal -->
          <div class="cart-info">
            <div class="item-count">{{ totalItems }} items</div>
            <div class="cart-total">₱{{ formatPrice(cartSubtotal) }}</div>
          </div>
          
          <!-- Promo Discount -->
          <div v-if="promoDiscount > 0" class="discounts-section">
            <div class="discount-row">
              <span class="discount-label">
                {{ appliedPromotion.name }}
              </span>
              <span class="discount-amount">-₱{{ formatPrice(promoDiscount) }}</span>
            </div>
            
            <div class="discount-divider"></div>
            
            <div class="final-total-row">
              <span class="final-label">Total</span>
              <span class="final-amount">₱{{ formatPrice(finalTotal) }}</span>
            </div>
          </div>
          
          <button 
            class="pay-btn" 
            @click="checkout"
            :disabled="cartItems.length === 0">
            <span>Checkout →</span>
          </button>
        </div>
      </div>
    </div>
        
    <!-- Cart Toggle Button -->
    <button v-if="!showCart && cartItems.length > 0" class="cart-toggle" @click="openCart">
      <ShoppingCart :size="24" />
      <span class="cart-badge">{{ totalItems }}</span>
    </button>
  </div>
</template>

<script>
import { useCartStore } from '@/stores/cartStores'
import categoriesAPI from '@/services/apiCategory.js'
import productsAPI from '@/services/apiProducts.js'
import { api } from '@/services/api.js'

export default {
  name: 'NewOrder',
  
  setup() {
    const cartStore = useCartStore()
    return { cartStore }
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
      
      // Cart UI state
      showCart: false,
      
      // Modal states
      showCategoryModal: false,
      showProductSelectorModal: false,
      
      // Navigation state
      viewMode: 'products',
      currentSubcategory: null,
      currentPage: 1,
      itemsPerPage: 12,
      categorySearch: '',
      breadcrumbs: [],
      
      // Custom category creation
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
    }
  },

  async mounted() {
    await this.initializeSession()
    await this.loadCategories()
  },

  watch: {
    selectedSourceCategory(newCategoryId) {
      if (newCategoryId) {
        this.loadProductsForSelection()
      }
    },
    
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
      
      return products
    },

    paginatedProducts() {
      if (this.viewMode === 'subcategories') {
        return this.filteredProducts
      }
      
      const start = (this.currentPage - 1) * this.itemsPerPage
      const end = start + this.itemsPerPage
      return this.filteredProducts.slice(start, end)
    },

    totalPages() {
      if (this.viewMode === 'subcategories') return 1
      return Math.ceil(this.filteredProducts.length / this.itemsPerPage)
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
    }
  },

  methods: {
    // ================================================================
    // INITIALIZATION
    // ================================================================
    
    async initializeSession() {
      try {
        console.log('🔄 Initializing session...')
        
        const userData = JSON.parse(localStorage.getItem('userData') || '{}')
        const cashierId = userData.user_id || userData.id || userData._id
        
        console.log('👤 Cashier ID:', cashierId)
        
        if (!cashierId) {
          throw new Error('No cashier ID found. Please log in again.')
        }
        
        const shiftId = localStorage.getItem('activeShiftId') || null
        console.log('⏰ Shift ID:', shiftId)
        
        this.cartStore.initializeSession(cashierId, shiftId)
        
        console.log('✅ Session initialized')
        
      } catch (error) {
        console.error('❌ Session initialization failed:', error)
        this.error = error.message
        alert(`Failed to initialize session: ${error.message}\n\nPlease refresh the page or log in again.`)
      }
    },

    // ================================================================
    // CATEGORIES
    // ================================================================
    
    async loadCategories() {
      try {
        this.loading = true
        this.error = null
        
        this.backendCategories = await categoriesAPI.getActiveCategories()
        
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
      this.currentPage = 1
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
          await this.loadProducts(categoryId)
        }
      }
    },

    async loadProducts(categoryId, subcategoryName = null) {
      try {
        this.productsLoading = true
        this.error = null
        
        if (this.isCustomCategory) {
          this.productsLoading = false
          return
        }
        
        const products = await productsAPI.getProductsByCategory(categoryId, subcategoryName)
        this.products = products
        
      } catch (error) {
        console.error('Failed to load products:', error)
        this.error = error.message
        this.products = []
      } finally {
        this.productsLoading = false
      }
    },

    async loadProductsForSelection() {
      if (!this.selectedSourceCategory) return
      
      try {
        this.productsLoading = true
        const products = await productsAPI.getProductsByCategory(this.selectedSourceCategory)
        this.allProducts = products
      } catch (error) {
        console.error('Failed to load products for selection:', error)
        this.error = error.message
      } finally {
        this.productsLoading = false
      }
    },

    generateSubcategoryImage(subcategoryName) {
      return `https://ui-avatars.com/api/?name=${encodeURIComponent(subcategoryName)}&size=200&background=A07BE3&color=fff`
    },

    // ================================================================
    // CUSTOM CATEGORIES
    // ================================================================
    
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
      this.closeCategoryModal()
      this.selectCategory(categoryId)
    },

    deleteCategory(categoryId) {
      if (confirm('Are you sure you want to delete this category and all its items?')) {
        this.customCategories = this.customCategories.filter(cat => cat.id !== categoryId)
        delete this.customCategoryProducts[categoryId]
        
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

    getProductCountForCategory(categoryId) {
      return this.allProducts.filter(product => product.category === categoryId).length
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
      
      this.$forceUpdate()
      this.closeProductSelectorModal()
    },

    removeFromCategory(productId) {
      if (this.isCustomCategory && this.customCategoryProducts[this.activeCategory]) {
        this.customCategoryProducts[this.activeCategory] = 
          this.customCategoryProducts[this.activeCategory].filter(product => product.id !== productId)
        
        this.$forceUpdate()
      }
    },

    // ================================================================
    // NAVIGATION
    // ================================================================
    
    handleProductClick(product) {
      if (product.isSubcategory) {
        this.selectSubcategory(product.subcategoryData)
      } else {
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

    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page
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
        
        // ✅ USE BACKOFFICE ENDPOINT
        const response = await api.get('/promotions/active/')
        
        console.log('📦 Full response:', response)
        console.log('📦 Response data:', response.data)
        
        // Parse response - Backoffice structure
        let allPromotions = []
        
        if (response && response.data) {
          if (response.data.success === true) {
            // Backoffice returns: { success: true, promotions: [...], count: n }
            allPromotions = response.data.promotions || []
            console.log('✅ Found promotions in response.data.promotions')
          } else {
            console.warn('⚠️ Success is not true')
          }
        }
        
        console.log('📋 Parsed promotions:', allPromotions)
        console.log('📋 Promotions count:', allPromotions.length)
        
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
        
        console.log('🔄 Calculating discounts for promotions...')
        console.log('📦 Current cart items:', this.cartItems)
        console.log('📦 Current products:', this.products)
        
        // Calculate discount for each promotion
        const applicablePromotions = []
        
        for (const promo of allPromotions) {
          try {
            console.log(`\n  🎁 Checking: ${promo.name}`)
            console.log(`     Type: ${promo.type} (${promo.discount_value}${promo.type === 'percentage' ? '%' : ' PHP'})`)
            console.log(`     Target: ${promo.discount_config?.target_type}`)
            console.log(`     Target IDs:`, promo.discount_config?.target_ids)
            
            const discount = this.calculatePromotionDiscount(promo)
            console.log(`     💰 Calculated discount: ₱${discount}`)
            
            if (discount > 0) {
              applicablePromotions.push({
                ...promo,
                calculatedDiscount: discount,
                isApplicable: true
              })
              console.log(`     ✅ APPLICABLE - Added to list`)
            } else {
              console.log(`     ❌ NOT APPLICABLE - Discount is 0`)
            }
          } catch (calcError) {
            console.error(`❌ Error calculating discount for ${promo.name}:`, calcError)
          }
        }
        
        // Sort by discount amount
        applicablePromotions.sort((a, b) => b.calculatedDiscount - a.calculatedDiscount)
        
        this.availablePromotions = applicablePromotions
        this.filteredPromoSuggestions = applicablePromotions
        
        console.log(`\n✅ FINAL RESULT: Found ${applicablePromotions.length} applicable promotions`)
        console.log('📊 Applicable promotions:', applicablePromotions)
        
      } catch (error) {
        console.error('❌ Failed to fetch promotions:', error)
        console.error('❌ Error details:', error.response?.data)
        
        this.availablePromotions = []
        this.filteredPromoSuggestions = []
      }
    },
    
    calculatePromotionDiscount(promotion) {
      // ✅ SAFETY CHECK: Handle missing discount_config
      if (!promotion.discount_config) {
        console.warn(`⚠️ Promotion "${promotion.name}" missing discount_config!`)
        console.warn('   Full promotion object:', promotion)
        return 0
      }
      
      const targetType = promotion.discount_config.target_type
      const targetIds = promotion.discount_config.target_ids || []
      
      console.log(`   🎯 Target Type: ${targetType}`)
      console.log(`   🎯 Target IDs:`, targetIds)
      
      let eligibleAmount = 0
      
      if (targetType === 'all') {
        eligibleAmount = this.cartSubtotal
        console.log(`   💰 All items eligible: ₱${eligibleAmount}`)
      } else if (targetType === 'categories') {
        // Get eligible items from target categories
        const eligibleItems = this.cartItems.filter(item => {
          const product = this.products.find(p => p.id === item.productId)
          const isEligible = product && targetIds.includes(product.category)
          
          if (isEligible) {
            console.log(`      ✅ ${product.name} (${product.category}) - ₱${item.subtotal}`)
          }
          
          return isEligible
        })
        
        eligibleAmount = eligibleItems.reduce((sum, item) => sum + item.subtotal, 0)
        console.log(`   💰 Category items eligible: ₱${eligibleAmount}`)
      } else if (targetType === 'products') {
        // Get eligible items from target products
        const eligibleItems = this.cartItems.filter(item => {
          const isEligible = targetIds.includes(item.productId)
          
          if (isEligible) {
            const product = this.products.find(p => p.id === item.productId)
            console.log(`      ✅ ${product?.name || item.productName} - ₱${item.subtotal}`)
          }
          
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
      } else if (promotion.type === 'fixed') {
        discount = Math.min(promotion.discount_value, eligibleAmount)
      }
      
      return Math.round(discount * 100) / 100
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
        console.log('✅ Applied promotion:', promotion.name)
        
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
        console.log('🎟️ Applying manual promo code:', this.promoCode)
        
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
              console.log('✅ Manual promo applied:', matchingPromo.name)
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
      console.log('🗑️ Promotion removed')
    },

    // ================================================================
    // CART MANAGEMENT
    // ================================================================
    
    addToCart(product) {
      try {
        console.log('🛒 Adding to cart:', product.name)
        
        if (!product.id || !product.name || !product.price) {
          throw new Error('Invalid product data')
        }
        
        if (product.stock <= 0) {
          alert(`${product.name} is out of stock!`)
          return
        }
        
        this.cartStore.addItem(product)
        this.showCart = true
        
        console.log('✅ Item added')
        
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
      
      console.log('🛒 Proceeding to checkout...')
      
      // Store promotion info for checkout
      if (this.appliedPromotion) {
        sessionStorage.setItem('appliedPromotion', JSON.stringify({
          promotion_id: this.appliedPromotion._id,
          promotion_name: this.appliedPromotion.name,
          discount_amount: this.promoDiscount
        }))
      } else {
        sessionStorage.removeItem('appliedPromotion')
      }
      
      this.$router.push('/checkout')
    },

    closeCart() {
      this.showCart = false
    },

    openCart() {
      this.showCart = true
      // Fetch promotions when cart opens
      this.fetchAvailablePromotions()
    },
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