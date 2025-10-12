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
        
        <!-- Customer Lookup & Points Section -->
        <div class="customer-section">
          <h4 class="section-title">Customer (Optional)</h4>
          
          <!-- Customer Search -->
          <div v-if="!selectedCustomer" class="customer-search">
            <input 
              type="text" 
              class="form-control" 
              placeholder="Enter customer username or email"
              v-model="customerSearchQuery"
              @keyup.enter="searchCustomer"
            />
            <button 
              class="btn btn-primary" 
              type="button" 
              @click="searchCustomer"
              :disabled="customerSearching || !customerSearchQuery.trim()"
            >
              {{ customerSearching ? 'Searching...' : 'Find' }}
            </button>
          </div>

          <!-- Customer Found -->
          <div v-if="selectedCustomer" class="customer-info-card">
            <div class="customer-header">
              <div class="customer-details">
                <h5>{{ selectedCustomer.full_name }}</h5>
                <p class="customer-username">@{{ selectedCustomer.username }}</p>
              </div>
              <button class="btn-remove" @click="clearCustomer" title="Remove customer">
                <X :size="16" />
              </button>
            </div>
            
            <!-- Loyalty Points Display -->
            <div class="loyalty-points-display">
              <div class="points-info">
                <span class="points-label">Available Points:</span>
                <span class="points-value">{{ selectedCustomer.loyalty_points || 0 }} pts</span>
                <span class="points-cash">(₱{{ formatPrice((selectedCustomer.loyalty_points || 0) / 4) }})</span>
              </div>
              
              <!-- Points Redemption -->
              <div v-if="selectedCustomer.loyalty_points >= 200" class="points-redemption">
                <div class="redemption-input-group">
                  <input 
                    type="number" 
                    class="form-control points-input" 
                    placeholder="Points to use"
                    v-model.number="pointsToRedeem"
                    :max="Math.min(selectedCustomer.loyalty_points, maxRedeemablePoints)"
                    min="0"
                    step="100"
                  />
                  <button 
                    class="btn btn-success btn-sm" 
                    @click="applyPointsDiscount"
                    :disabled="!canRedeemPoints"
                  >
                    Use Points
                  </button>
                </div>
                <small class="redemption-info">
                  Min: 200 pts (₱50) • Max: 50% of cart ({{ maxRedeemablePoints }} pts)
                </small>
              </div>
              
              <div v-else class="points-insufficient">
                <small>Need 200+ points to redeem (₱50 minimum)</small>
              </div>
            </div>

            <!-- Applied Points Discount -->
            <div v-if="appliedPointsDiscount > 0" class="applied-discount">
              <div class="discount-info">
                <span>Points Discount:</span>
                <span class="discount-amount">-₱{{ formatPrice(appliedPointsDiscount) }}</span>
              </div>
              <button class="btn-remove-discount" @click="removePointsDiscount">
                <X :size="14" />
              </button>
            </div>
          </div>

          <!-- Customer Search Error -->
          <div v-if="customerSearchError" class="alert alert-danger">
            {{ customerSearchError }}
          </div>
        </div>

        <!-- Promo Code Section -->
        <div class="promo-section">
          <h4 class="section-title">Promo Code</h4>
          <div class="input-group">
            <input 
              type="text" 
              class="form-control" 
              placeholder="Enter promo code"
              v-model="promoCode"
            />
            <button class="btn btn-primary" type="button" @click="applyPromotion">
              Apply
            </button>
          </div>
          <div v-if="appliedPromotion" class="alert alert-success mt-2">
            ✅ {{ appliedPromotion.name }} applied
            <button @click="removePromotion" class="btn-close"></button>
          </div>
        </div>

        <!-- Cart Summary -->
        <div class="cart-summary">
          <div class="summary-breakdown">
            <div class="cart-info">
            <div class="item-count">{{ totalItems }} items</div>
            <div class="cart-total">₱{{ formatPrice(cartTotal) }}</div>
          </div>
            <div v-if="appliedPointsDiscount > 0" class="summary-row discount-row">
              <span>Points Discount ({{ pointsRedeemed }} pts)</span>
              <span class="discount-text">-₱{{ formatPrice(appliedPointsDiscount) }}</span>
            </div>
            <div v-if="appliedPromotion" class="summary-row discount-row">
              <span>Promo Discount</span>
              <span class="discount-text">-₱{{ formatPrice(promoDiscount) }}</span>
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
      
      // Promo code
      promoCode: '',
      appliedPromotion: null,
      
      // Customer & Loyalty Points
      customerSearchQuery: '',
      customerSearching: false,
      customerSearchError: null,
      selectedCustomer: null,
      pointsToRedeem: 0,
      pointsRedeemed: 0,
      appliedPointsDiscount: 0,
      
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
    
    // Max redeemable points (50% of cart)
    maxRedeemablePoints() {
      const maxDiscount = this.cartSubtotal * 0.5
      const maxPoints = Math.floor(maxDiscount * 4)
      
      if (this.selectedCustomer) {
        return Math.min(maxPoints, this.selectedCustomer.loyalty_points)
      }
      return 0
    },
    
    // Can redeem points validation
    canRedeemPoints() {
      if (!this.pointsToRedeem || !this.selectedCustomer) return false
      if (this.pointsToRedeem < 200) return false
      if (this.pointsToRedeem > this.selectedCustomer.loyalty_points) return false
      if (this.pointsToRedeem > this.maxRedeemablePoints) return false
      return true
    },
    
    // Promo discount
    promoDiscount() {
      if (!this.appliedPromotion) return 0
      // Add your promo calculation logic here
      return 0
    },
    
    // Final total with all discounts
    finalTotal() {
      return Math.max(0, this.cartSubtotal - this.appliedPointsDiscount - this.promoDiscount)
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
    // CUSTOMER LOOKUP & LOYALTY POINTS
    // ================================================================
    
    async searchCustomer() {
      if (!this.customerSearchQuery.trim()) return
      
      try {
        this.customerSearching = true
        this.customerSearchError = null
        
        const query = this.customerSearchQuery.trim()
        
        const response = await api.get('/customers/search/', {
          params: { query }
        })
        
        if (response.data.success && response.data.data.customers.length > 0) {
          const customer = response.data.data.customers[0]
          this.selectedCustomer = customer
          this.customerSearchQuery = ''
          
          console.log('✅ Customer found:', customer.full_name)
        } else {
          this.customerSearchError = 'Customer not found. Please check the username/email.'
        }
        
      } catch (error) {
        console.error('❌ Customer search failed:', error)
        this.customerSearchError = error.response?.data?.message || 'Failed to search customer'
      } finally {
        this.customerSearching = false
      }
    },
    
    clearCustomer() {
      this.selectedCustomer = null
      this.customerSearchQuery = ''
      this.customerSearchError = null
      this.removePointsDiscount()
    },
    
    applyPointsDiscount() {
      if (!this.canRedeemPoints) {
        alert('Invalid points amount')
        return
      }
      
      const discount = this.pointsToRedeem / 4
      
      if (discount > this.cartSubtotal) {
        alert('Points discount cannot exceed cart total')
        return
      }
      
      this.pointsRedeemed = this.pointsToRedeem
      this.appliedPointsDiscount = discount
      this.pointsToRedeem = 0
      
      console.log(`✅ Applied ${this.pointsRedeemed} points (₱${discount.toFixed(2)} discount)`)
    },
    
    removePointsDiscount() {
      this.pointsRedeemed = 0
      this.appliedPointsDiscount = 0
      this.pointsToRedeem = 0
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
    
    applyPromotion() {
      // Add your promo code logic here
      console.log('Applying promo code:', this.promoCode)
    },
    
    removePromotion() {
      this.appliedPromotion = null
      this.promoCode = ''
    },
    
    checkout() {
      if (this.cartStore.isEmpty) {
        alert('Your cart is empty!')
        return
      }
      
      console.log('🛒 Proceeding to checkout...')
      
      // Store customer and points info for checkout page
      if (this.selectedCustomer) {
        sessionStorage.setItem('checkoutCustomer', JSON.stringify({
          customer_id: this.selectedCustomer._id,
          full_name: this.selectedCustomer.full_name,
          pointsRedeemed: this.pointsRedeemed,
          pointsDiscount: this.appliedPointsDiscount
        }))
      } else {
        sessionStorage.removeItem('checkoutCustomer')
      }
      
      this.$router.push('/checkout')
    },

    closeCart() {
      this.showCart = false
    },

    openCart() {
      this.showCart = true
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