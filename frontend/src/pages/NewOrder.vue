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
        <div v-for="item in cartItems" :key="item.id" class="cart-item">
          <img :src="item.image" :alt="item.name" class="cart-item-image" />
          <div class="cart-item-info">
            <h4>{{ item.name }}</h4>
            <p class="item-price">₱{{ formatPrice(item.price) }}</p>
          </div>
          <div class="cart-item-controls">
            <button 
              @click="decreaseQuantity(item)" 
              class="quantity-btn minus"
              :disabled="quantityUpdating">
              <Minus :size="16" />
            </button>
            <span class="quantity">{{ item.quantity }}</span>
            <button 
              @click="increaseQuantity(item)" 
              class="quantity-btn plus"
              :disabled="quantityUpdating">
              <Plus :size="16" />
            </button>
          </div>
          <div class="cart-item-subtotal">
            ₱{{ formatPrice(item.subtotal) }}
          </div>
          <button 
            @click="removeFromCart(item)" 
            class="remove-btn"
            :disabled="quantityUpdating">
            <Trash2 :size="16" />
          </button>
        </div>
      </div>

      <!-- Cart Summary -->
      <div class="cart-footer">
        <div class="cart-summary">
  
          <div class="cart-info">
            <div class="item-count">{{ totalItems }} items</div>
            <div class="cart-total">₱{{ formatPrice(cartTotal) }}</div>
          </div>
          <button 
            class="pay-btn" 
            @click="checkout"
            :disabled="cartItems.length === 0 || checkoutProcessing">
            <span v-if="!checkoutProcessing">Checkout →</span>
            <span v-else>Processing...</span>
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
import categoriesAPI from '@/services/apiCategory.js';
import productsAPI from '@/services/apiProducts.js';
import cartAPI from '@/services/apiCart.js';

export default {
  name: 'NewOrder',
  
  data() {
    return {
      // Loading and error states
      loading: false,
      productsLoading: false,
      quantityUpdating: false,
      checkoutProcessing: false,
      error: null,
      
      // Categories (backend + custom)
      backendCategories: [],
      customCategories: [],
      activeCategory: null,
      
      // Products
      products: [],
      customCategoryProducts: {},
      allProducts: [],
      
      // Cart (backend integration)
      cartId: null,
      cartItems: [],
      cartSubtotal: 0,
      cartTax: 0,
      cartDiscount: 0,
      cartTotal: 0,
      showCart: false,
      
      // User context
      cashierId: null,
      shiftId: null,
      
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
    await this.initializeSession();
    await this.loadCategories();
  },

  watch: {
    selectedSourceCategory(newCategoryId) {
      if (newCategoryId) {
        this.loadProductsForSelection();
      }
    }
  },

  computed: {
    // Combine backend and custom categories
    categories() {
      return [...this.backendCategories, ...this.customCategories];
    },

    filteredProducts() {
      if (this.viewMode === 'subcategories') {
        const category = this.categories.find(cat => cat.id === this.activeCategory);
        if (category && category.subcategories) {
          return category.subcategories.map(sub => ({
            id: sub.id,
            name: sub.name,
            description: `${sub.productCount} items available`,
            price: '',
            image: this.generateSubcategoryImage(sub.name),
            isSubcategory: true,
            subcategoryData: sub
          }));
        }
        return [];
      }
      
      let products;
      
      if (this.isCustomCategory) {
        products = this.customCategoryProducts[this.activeCategory] || [];
      } else {
        products = this.products;
      }
      
      if (this.categorySearch.trim()) {
        products = products.filter(product => 
          product.name.toLowerCase().includes(this.categorySearch.toLowerCase())
        );
      }
      
      return products;
    },

    paginatedProducts() {
      if (this.viewMode === 'subcategories') {
        return this.filteredProducts;
      }
      
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.filteredProducts.slice(start, end);
    },

    totalPages() {
      if (this.viewMode === 'subcategories') return 1;
      return Math.ceil(this.filteredProducts.length / this.itemsPerPage);
    },

    totalItems() {
      return this.cartItems.reduce((total, item) => total + item.quantity, 0);
    },

    isCustomCategory() {
      const category = this.categories.find(cat => cat.id === this.activeCategory);
      return category && category.isCustom;
    },

    customCategoryItems() {
      return this.filteredProducts;
    },

    availableSourceCategories() {
      return this.backendCategories.filter(cat => cat.id !== this.activeCategory);
    },

    availableProductsForSelection() {
      let products = this.allProducts.filter(product => 
        product.category === this.selectedSourceCategory
      );
      
      if (this.productSearchQuery.trim()) {
        products = products.filter(product => 
          product.name.toLowerCase().includes(this.productSearchQuery.toLowerCase())
        );
      }
      
      return products;
    },

    allAvailableProductsCount() {
      const currentCategoryProducts = this.customCategoryProducts[this.activeCategory] || [];
      const currentProductIds = currentCategoryProducts.map(p => p.originalId || p.id);
      
      return this.allProducts.filter(p => !currentProductIds.includes(p.id)).length;
    },

    wouldExceedLimit() {
      return this.customCategoryItems.length + this.selectedProducts.length > 8;
    }
  },

  methods: {
    // ================================================================
    // INITIALIZATION
    // ================================================================
    
    async initializeSession() {
      try {
        console.log('🔄 Initializing session...');
        
        // Get cashier ID from auth token/localStorage
        const userData = JSON.parse(localStorage.getItem('userData') || '{}');
        this.cashierId = userData.user_id || userData.id || userData._id;
        
        console.log('👤 Cashier ID:', this.cashierId);
        
        if (!this.cashierId) {
          throw new Error('No cashier ID found. Please log in again.');
        }
        
        // Get active shift (if exists)
        this.shiftId = localStorage.getItem('activeShiftId') || null;
        console.log('⏰ Shift ID:', this.shiftId);
        
        // Check for existing cart
        const existingCartId = localStorage.getItem('currentCartId');
        console.log('🛒 Existing cart ID from storage:', existingCartId);
        
        if (existingCartId) {
          try {
            console.log('🔍 Attempting to restore existing cart:', existingCartId);
            const cart = await cartAPI.getCart(existingCartId);
            this.cartId = existingCartId;
            this.updateCartFromBackend(cart);
            console.log('✅ Cart restored successfully:', this.cartId);
          } catch (error) {
            console.warn('⚠️ Existing cart not found, creating new one:', error.message);
            localStorage.removeItem('currentCartId'); // Clean up invalid cart ID
            await this.createNewCart();
          }
        } else {
          console.log('📝 No existing cart, creating new one...');
          await this.createNewCart();
        }
        
        console.log('✅ Session initialized. Cart ID:', this.cartId);
        
      } catch (error) {
        console.error('❌ Session initialization failed:', error);
        this.error = error.message;
        
        // Show user-friendly error
        alert(`Failed to initialize session: ${error.message}\n\nPlease refresh the page or log in again.`);
      }
    },

    async createNewCart() {
      try {
        console.log('📝 Creating new cart...');
        console.log('   Cashier ID:', this.cashierId);
        console.log('   Shift ID:', this.shiftId);
        
        if (!this.cashierId) {
          throw new Error('Cannot create cart: No cashier ID available');
        }
        
        const cart = await cartAPI.createCart(this.cashierId, this.shiftId);
        
        console.log('✅ Cart created:', cart);
        
        if (!cart || !cart.id) {
          throw new Error('Cart creation returned invalid data');
        }
        
        this.cartId = cart.id;
        localStorage.setItem('currentCartId', this.cartId);
        this.updateCartFromBackend(cart);
        
        console.log('💾 Cart ID saved to localStorage:', this.cartId);
        
      } catch (error) {
        console.error('❌ Failed to create cart:', error);
        throw new Error(`Cart creation failed: ${error.message}`);
      }
    },

   updateCartFromBackend(cart) {
      console.log('🔄 Updating cart from backend:', cart);
      
      if (!cart) {
        console.warn('⚠️ Cart is null or undefined');
        return;
      }
      
      // Update cart items
      this.cartItems = cart.items || [];
      
      // Update totals
      this.cartSubtotal = cart.subtotal || 0;
      this.cartTax = cart.taxAmount || 0;
      this.cartDiscount = cart.discountAmount || 0;
      this.cartTotal = cart.total || 0;
      
      console.log('✅ Cart updated:', {
        items: this.cartItems.length,
        subtotal: this.cartSubtotal,
        tax: this.cartTax,
        total: this.cartTotal
      });
    },

    // ================================================================
    // CATEGORIES
    // ================================================================
    
    async loadCategories() {
      try {
        this.loading = true;
        this.error = null;
        
        this.backendCategories = await categoriesAPI.getActiveCategories();
        
        if (this.backendCategories.length > 0 && !this.activeCategory) {
          this.activeCategory = this.backendCategories[0].id;
          await this.selectCategory(this.backendCategories[0].id);
        }
        
      } catch (error) {
        console.error('Failed to load categories:', error);
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },

    async selectCategory(categoryId) {
      this.activeCategory = categoryId;
      this.currentPage = 1;
      this.categorySearch = '';
      this.breadcrumbs = [];
      this.currentSubcategory = null;
      
      const category = this.categories.find(cat => cat.id === categoryId);
      
      if (category && !category.isCustom && category.hasSubcategories) {
        this.viewMode = 'subcategories';
        this.breadcrumbs = [
          { name: category.name, type: 'categories', categoryId: categoryId }
        ];
      } else {
        this.viewMode = 'products';
        if (!category.isCustom) {
          await this.loadProducts(categoryId);
        }
      }
    },

    async loadProducts(categoryId, subcategoryName = null) {
      try {
        this.productsLoading = true;
        this.error = null;
        
        if (this.isCustomCategory) {
          this.productsLoading = false;
          return;
        }
        
        const products = await productsAPI.getProductsByCategory(categoryId, subcategoryName);
        this.products = products;
        
      } catch (error) {
        console.error('Failed to load products:', error);
        this.error = error.message;
        this.products = [];
      } finally {
        this.productsLoading = false;
      }
    },

    async loadProductsForSelection() {
      if (!this.selectedSourceCategory) return;
      
      try {
        this.productsLoading = true;
        const products = await productsAPI.getProductsByCategory(this.selectedSourceCategory);
        this.allProducts = products;
      } catch (error) {
        console.error('Failed to load products for selection:', error);
        this.error = error.message;
      } finally {
        this.productsLoading = false;
      }
    },

    generateSubcategoryImage(subcategoryName) {
      return `https://ui-avatars.com/api/?name=${encodeURIComponent(subcategoryName)}&size=200&background=A07BE3&color=fff`;
    },

    // ================================================================
    // CUSTOM CATEGORIES
    // ================================================================
    
    createCategory() {
      if (!this.newCategory.name.trim()) return;
      
      const categoryId = `custom_${this.nextCategoryId++}`;
      const category = {
        id: categoryId,
        name: this.newCategory.name.trim(),
        icon: this.newCategory.icon,
        isCustom: true,
        hasSubcategories: false,
        subcategories: []
      };
      
      this.customCategoryProducts[categoryId] = [];
      this.customCategories.push(category);
      this.closeCategoryModal();
      this.selectCategory(categoryId);
    },

    deleteCategory(categoryId) {
      if (confirm('Are you sure you want to delete this category and all its items?')) {
        this.customCategories = this.customCategories.filter(cat => cat.id !== categoryId);
        delete this.customCategoryProducts[categoryId];
        
        if (this.activeCategory === categoryId) {
          this.activeCategory = this.categories[0]?.id;
          if (this.activeCategory) {
            this.selectCategory(this.activeCategory);
          }
        }
      }
    },

    closeCategoryModal() {
      this.showCategoryModal = false;
      this.newCategory = { name: '', icon: 'Package' };
    },

    getCurrentCategoryName() {
      const category = this.categories.find(cat => cat.id === this.activeCategory);
      return category ? category.name : 'Category';
    },

    closeProductSelectorModal() {
      this.showProductSelectorModal = false;
      this.selectedProducts = [];
      this.productSearchQuery = '';
      this.selectedSourceCategory = null;
    },

    toggleProductSelection(product) {
      if (this.isProductAlreadyInCategory(product.id)) return;
      
      const index = this.selectedProducts.indexOf(product.id);
      if (index > -1) {
        this.selectedProducts.splice(index, 1);
      } else {
        if (this.customCategoryItems.length + this.selectedProducts.length < 8) {
          this.selectedProducts.push(product.id);
        }
      }
    },

    isProductAlreadyInCategory(productId) {
      if (this.isCustomCategory && this.customCategoryProducts[this.activeCategory]) {
        return this.customCategoryProducts[this.activeCategory].some(product => 
          product.originalId === productId || product.id === productId
        );
      }
      return false;
    },

    getProductCountForCategory(categoryId) {
      return this.allProducts.filter(product => product.category === categoryId).length;
    },

    addSelectedProductsToCategory() {
      const selectedProductData = this.allProducts.filter(product => 
        this.selectedProducts.includes(product.id)
      );
      
      if (!this.customCategoryProducts[this.activeCategory]) {
        this.customCategoryProducts[this.activeCategory] = [];
      }
      
      selectedProductData.forEach(product => {
        const newProduct = {
          ...product,
          id: `custom_${this.nextProductId++}`,
          category: this.activeCategory,
          isReference: true,
          originalId: product.id
        };
        
        this.customCategoryProducts[this.activeCategory].push(newProduct);
      });
      
      this.$forceUpdate();
      this.closeProductSelectorModal();
    },

    removeFromCategory(productId) {
      if (this.isCustomCategory && this.customCategoryProducts[this.activeCategory]) {
        this.customCategoryProducts[this.activeCategory] = 
          this.customCategoryProducts[this.activeCategory].filter(product => product.id !== productId);
        
        this.$forceUpdate();
      }
    },

    // ================================================================
    // NAVIGATION
    // ================================================================
    
    handleProductClick(product) {
      if (product.isSubcategory) {
        this.selectSubcategory(product.subcategoryData);
      } else {
        this.addToCart(product);
      }
    },

    async selectSubcategory(subcategoryData) {
      this.currentSubcategory = subcategoryData;
      this.viewMode = 'products';
      this.breadcrumbs.push({
        name: subcategoryData.name,
        type: 'products',
        data: subcategoryData
      });
      
      await this.loadProducts(this.activeCategory, subcategoryData.name);
    },

    async navigateTo(crumb) {
      if (crumb.type === 'categories') {
        this.viewMode = 'subcategories';
        this.currentSubcategory = null;
        this.breadcrumbs = [crumb];
        await this.selectCategory(crumb.categoryId);
      } else if (crumb.type === 'products') {
        const crumbIndex = this.breadcrumbs.findIndex(b => b === crumb);
        this.breadcrumbs = this.breadcrumbs.slice(0, crumbIndex + 1);
        this.currentSubcategory = crumb.data;
        await this.loadProducts(this.activeCategory, crumb.data.name);
      }
    },

    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page;
      }
    },

    retryLoad() {
      this.error = null;
      if (this.activeCategory) {
        this.loadProducts(this.activeCategory);
      } else {
        this.loadCategories();
      }
    },

    // ================================================================
    // CART MANAGEMENT (Backend Integration)
    // ================================================================
    
    async addToCart(product) {
      try {
        console.log('🛒 Adding to cart:', {
          cartId: this.cartId,
          productId: product.id,
          productName: product.name,
          price: product.price
        });
        
        // Validate cart exists
        if (!this.cartId) {
          throw new Error('No active cart. Please refresh the page.');
        }
        
        // Validate product
        if (!product.id) {
          throw new Error('Invalid product: missing ID');
        }
        
        // Show loading state
        this.showCart = true;
        
        // Call backend FIRST (no optimistic update)
        console.log('📡 Sending add item request to backend...');
        const updatedCart = await cartAPI.addItem(this.cartId, product.id, 1);
        
        console.log('✅ Backend returned updated cart:', updatedCart);
        
        // Update UI from backend response
        this.updateCartFromBackend(updatedCart);
        
        // Show success message (optional)
        console.log('✅ Item added successfully');
        
      } catch (error) {
        console.error('❌ Add to cart failed:', error);
        console.error('   Product:', product);
        console.error('   Cart ID:', this.cartId);
        
        // Show error to user
        alert(`Failed to add item: ${error.message}\n\nPlease try again or refresh the page.`);
      }
    },

    async removeFromCart(item) {
      try {
        console.log('🗑️ Removing from cart:', item);
        
        if (!this.cartId) {
          throw new Error('No active cart');
        }
        
        // Call backend
        const updatedCart = await cartAPI.removeItem(this.cartId, item.productId || item.id);
        
        // Update UI from backend
        this.updateCartFromBackend(updatedCart);
        
        console.log('✅ Item removed successfully');
        
      } catch (error) {
        console.error('❌ Remove from cart failed:', error);
        alert(`Failed to remove item: ${error.message}`);
      }
    },

    async increaseQuantity(item) {
      if (this.quantityUpdating) return;
      
      try {
        this.quantityUpdating = true;
        console.log('➕ Increasing quantity for:', item.name);
        
        const newQuantity = item.quantity + 1;
        
        // Call backend
        const updatedCart = await cartAPI.updateItemQuantity(
          this.cartId, 
          item.productId || item.id, 
          newQuantity
        );
        
        // Update UI from backend
        this.updateCartFromBackend(updatedCart);
        
        console.log('✅ Quantity increased');
        
      } catch (error) {
        console.error('❌ Increase quantity failed:', error);
        alert(`Failed to update quantity: ${error.message}`);
      } finally {
        this.quantityUpdating = false;
      }
    },

  async decreaseQuantity(item) {
    if (this.quantityUpdating) return;
    
    if (item.quantity <= 1) {
      await this.removeFromCart(item);
      return;
    }
    
    try {
      this.quantityUpdating = true;
      console.log('➖ Decreasing quantity for:', item.name);
      
      const newQuantity = item.quantity - 1;
      
      // Call backend
      const updatedCart = await cartAPI.updateItemQuantity(
        this.cartId, 
        item.productId || item.id, 
        newQuantity
      );
      
      // Update UI from backend
      this.updateCartFromBackend(updatedCart);
      
      console.log('✅ Quantity decreased');
      
    } catch (error) {
      console.error('❌ Decrease quantity failed:', error);
      alert(`Failed to update quantity: ${error.message}`);
    } finally {
      this.quantityUpdating = false;
    }
  },

    

    async checkout() {
      if (this.cartItems.length === 0) {
        alert('Your cart is empty!');
        return;
      }
      
      try {
        console.log('🛒 Starting checkout process...');
        console.log('   Cart ID:', this.cartId);
        console.log('   Items:', this.cartItems.length);
        
        // Validate cart ID exists
        if (!this.cartId) {
          throw new Error('No active cart found. Please refresh the page and try again.');
        }
        
        this.checkoutProcessing = true;
        
        // Prepare checkout with backend validation
        console.log('📋 Preparing checkout for cart:', this.cartId);
        const saleData = await cartAPI.prepareCheckout(this.cartId);
        
        console.log('✅ Checkout prepared:', saleData);
        
        // Validate sale data
        if (!saleData || typeof saleData.total_amount === 'undefined') {
          throw new Error('Invalid checkout data received from server');
        }
        
        // Navigate to checkout page with cart data
        this.$router.push({
          name: 'Checkout',
          params: { 
            cartId: this.cartId 
          },
          query: {
            subtotal: saleData.subtotal || 0,
            tax: saleData.tax_amount || 0,
            discount: saleData.discount_amount || 0,
            total: saleData.total_amount || 0
          }
        });
        
      } catch (error) {
        console.error('❌ Checkout failed:', error);
        
        // Show detailed error to user
        let errorMessage = error.message || 'Unknown error occurred';
        
        // Check for specific error types
        if (errorMessage.includes('not found')) {
          errorMessage = 'Cart session expired. Creating a new cart...';
          
          // Try to recover by creating new cart
          try {
            localStorage.removeItem('currentCartId');
            await this.createNewCart();
            alert('Cart was reset. Please add items again and try checkout.');
          } catch (recoveryError) {
            alert('Failed to recover cart. Please refresh the page.');
          }
        } else if (errorMessage.includes('stock')) {
          errorMessage = 'Some items are out of stock. Please review your cart.';
        } else {
          errorMessage = `Checkout failed: ${errorMessage}`;
        }
        
        alert(errorMessage);
        
      } finally {
        this.checkoutProcessing = false;
      }
    },
    
    async validateCart() {
      try {
        if (!this.cartId) {
          console.warn('⚠️ No cart ID available');
          return false;
        }
        
        const cart = await cartAPI.getCart(this.cartId);
        this.updateCartFromBackend(cart);
        return true;
        
      } catch (error) {
        console.error('❌ Cart validation failed:', error);
        localStorage.removeItem('currentCartId');
        this.cartId = null;
        return false;
      }
    },

    closeCart() {
      this.showCart = false;
    },

    openCart() {
      this.showCart = true;
    },

    // ================================================================
    // UTILITIES
    // ================================================================
    
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2);
    }
  }
}
</script>
<style scoped>
@import '@/assets/styles/NewOrder.css'



</style>