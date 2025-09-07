<template>
  <div class="new-order-page">
    <!-- Main Content Area -->
    <div class="main-area">
      <div class="no-contents">
        <!-- Header Section -->
        <div class="no-header">
          <div class="category-search">
            <input type="text" v-model="categorySearch" placeholder="search" class="search-input"/>
          </div>
          
          <!-- Categories -->
          <div class="header-bot">
            <div class="categories-container">
              <div v-for="category in categories" :key="category.id":class="['cat-card', { active: activeCategory === category.id }]"@click="selectCategory(category.id)">
                <div class="cat-icon">
                  <component :is="category.icon" />
                </div>
                <span class="cat-label">{{ category.name }}</span>
                <button v-if="category.isCustom"class="delete-category-btn"@click.stop="deleteCategory(category.id)"title="Delete Category">
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
        
        <!-- Navigation -->
        <div v-if="breadcrumbs.length > 0" class="breadcrumb-nav">
          <button v-for="(crumb, index) in breadcrumbs" :key="index"class="breadcrumb-item"@click="navigateTo(crumb)">
            {{ crumb.name }}
            <ChevronRight v-if="index < breadcrumbs.length - 1" :size="16" />
          </button>
        </div>

        <!-- Products Grid -->
        <div class="products-grid">
          <div v-for="product in paginatedProducts" :key="product.id"class="product-card"@click="handleProductClick(product)">
            <div class="product-image">
              <img :src="product.image" :alt="product.name" loading="lazy" />
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <p class="product-description">{{ product.description }}</p>
              <div v-if="!product.isSubcategory" class="product-price">
                ₱{{ product.price }}
              </div>
              <div v-else class="subcategory-indicator">
                <ChevronRight :size="16" /> View Items
              </div>
            </div>
            <button v-if="!product.isSubcategory && isCustomCategory" class="delete-product-btn" @click.stop="removeFromCategory(product.id)" title="Remove from category">
              <X :size="14" />
            </button>
          </div>
          
          <!-- Add Products Option (Custom Categories Only) -->
          <div 
              v-if="viewMode === 'products' && isCustomCategory && customCategoryItems.length < 8"
              class="product-card add-item-card"
              @click="showProductSelectorModal = true"
            >
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
            @click="goToPage(currentPage - 1)"
          >
            Previous
          </button>
          
          <span class="page-info">
            Page {{ currentPage }} of {{ totalPages }} ({{ filteredProducts.length }} items)
          </span>
          
          <button 
            class="page-btn" 
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
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
                @click="newCategory.icon = iconOption.name"
              >
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
            :disabled="!newCategory.name.trim()"
          >
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
              @click="selectedSourceCategory = category.id"
            >
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
          
          <!-- Product Selection Grid -->
          <div class="product-selection-grid">
            <div 
              v-for="product in availableProductsForSelection" 
              :key="product.id"
              :class="['selectable-product', { 
                selected: selectedProducts.includes(product.id),
                'already-added': isProductAlreadyInCategory(product.id)
              }]"
              @click="toggleProductSelection(product)"
            >
              <div class="product-image-small">
                <img :src="product.image" :alt="product.name" loading="lazy" />
              </div>
              <div class="product-details">
                <h4>{{ product.name }}</h4>
                <p>₱{{ product.price }}</p>
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
            :disabled="selectedProducts.length === 0 || wouldExceedLimit"
          >
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
          <p>Your cart is empty</p>
          <p>Add items to get started!</p>
        </div>
        <div v-for="item in cartItems" :key="item.id" class="cart-item">
          <img :src="item.image" :alt="item.name" class="cart-item-image" />
          <div class="cart-item-info">
            <h4>{{ item.name }}</h4>
            <p>{{ item.description }}</p>
          </div>
          <div class="cart-item-price">₱{{ item.price }}</div>
          <div class="cart-item-controls">
            <button @click="decreaseQuantity(item)" class="quantity-btn minus">
              <Minus :size="16" />
            </button>
            <span class="quantity">{{ item.quantity }}</span>
            <button @click="increaseQuantity(item)" class="quantity-btn plus">
              <Plus :size="16" />
            </button>
          </div>
          <button @click="removeFromCart(item)" class="remove-btn">
            <Trash2 :size="16" />
          </button>
        </div>
      </div>

      <div class="cart-footer">
        <div class="cart-summary">
          <div class="cart-info">
            <div class="item-count">{{ totalItems }} items</div>
            <div class="cart-total">₱{{ cartTotal }}</div>
          </div>
          <button 
            class="pay-btn" 
            @click="checkout"
            :disabled="cartItems.length === 0"
          >
            Checkout →
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

export default {
  name: 'NewOrder',
  components: {
    // Add your icon components here
  },
  data() {
    return {
      // Loading and error states
      loading: false,
      error: null,
      
      // Categories (backend + custom)
      backendCategories: [],
      customCategories: [],
      activeCategory: null,
      
      // Cart functionality
      showCart: false,
      cartItems: [],
      
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
      
      // Static products (will be replaced with API later)
      products: [],
      productsLoading: false,
    }
  },

  async mounted() {
    await this.loadCategories();
  },

  computed: {
    // Combine backend and custom categories
    categories() {
      return [...this.backendCategories, ...this.customCategories];
    },

    filteredProducts() {
      if (this.viewMode === 'subcategories') {
        // Show subcategories as product cards
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
      
      // Show products
      let products = this.products.filter(product => product.category === this.activeCategory);
      
      // Apply search filter
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

    cartTotal() {
      return this.cartItems.reduce((total, item) => total + (item.price * item.quantity), 0);
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
      // Load products when source category changes
      if (this.selectedSourceCategory && this.allProducts.length === 0) {
        this.loadProductsForSelection();
        return [];
      }
      
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
      return this.products.length;
    }
  },

  methods: {
    // Categories API integration
    async loadCategories() {
      try {
        this.loading = true;
        this.error = null;
        
        this.backendCategories = await categoriesAPI.getActiveCategories();
        
        console.log('Loaded categories:', this.backendCategories);
        
        // Set first category as active
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
          { name: category.name, type: 'categories' }
        ];
      } else {
        this.viewMode = 'products';
        // Load products from API
        await this.loadProducts(categoryId);
      }
    },

    generateSubcategoryImage(subcategoryName) {
      return `https://via.placeholder.com/200x150/9b59b6/white?text=${encodeURIComponent(subcategoryName)}`;
    },

    // Custom category management
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
      
      this.customCategories.push(category);
      this.closeCategoryModal();
      this.selectCategory(categoryId);
    },

    deleteCategory(categoryId) {
      if (confirm('Are you sure you want to delete this category and all its items?')) {
        this.customCategories = this.customCategories.filter(cat => cat.id !== categoryId);
        this.products = this.products.filter(product => product.category !== categoryId);
        
        if (this.activeCategory === categoryId) {
          this.activeCategory = this.categories[0]?.id;
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

    // Product selection for custom categories
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
      return this.products.some(product => 
        product.id === productId && product.category === this.activeCategory
      );
    },

    getProductCountForCategory(categoryId) {
      return this.products.filter(product => product.category === categoryId).length;
    },

    addSelectedProductsToCategory() {
      const selectedProductData = this.products.filter(product => 
        this.selectedProducts.includes(product.id)
      );
      
      selectedProductData.forEach(product => {
        const newProduct = {
          ...product,
          id: this.nextProductId++,
          category: this.activeCategory,
          isReference: true,
          originalId: product.id
        };
        this.products.push(newProduct);
      });
      
      this.closeProductSelectorModal();
    },

    // Navigation
    handleProductClick(product) {
      if (product.isSubcategory) {
        this.selectSubcategory(product.subcategoryData);
      } else {
        this.addToCart(product);
      }
    },

    selectSubcategory(subcategoryData) {
      console.log('Subcategory data:', subcategoryData); 
      this.currentSubcategory = subcategoryData;
      this.viewMode = 'products';
      this.breadcrumbs.push({
        name: subcategoryData.name,
        type: 'products',
        data: subcategoryData
      });
      console.log('Breadcrumbs after push:', this.breadcrumbs);
      // Here you would load subcategory products from API
    },

    navigateTo(crumb) {
      this.viewMode = crumb.type;
      if (crumb.type === 'subcategories') {
        this.currentSubcategory = null;
        this.breadcrumbs = this.breadcrumbs.slice(0, 1);
      } else if (crumb.type === 'categories') {
        this.breadcrumbs = [];
        this.currentSubcategory = null;
      }
    },

    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page;
      }
    },

    // Cart functionality
    closeCart() {
      this.showCart = false;
    },

    openCart() {
      this.showCart = true;
    },

    addToCart(product) {
      const existingItem = this.cartItems.find(item => item.id === product.id);
      if (existingItem) {
        existingItem.quantity++;
      } else {
        this.cartItems.push({ ...product, quantity: 1 });
      }
      this.showCart = true;
    },

    removeFromCart(item) {
      const index = this.cartItems.findIndex(cartItem => cartItem.id === item.id);
      if (index > -1) {
        this.cartItems.splice(index, 1);
      }
    },

    increaseQuantity(item) {
      item.quantity++;
    },

    decreaseQuantity(item) {
      if (item.quantity > 1) {
        item.quantity--;
      }
    },

    checkout() {
      if (this.cartItems.length === 0) {
        alert('Your cart is empty!');
        return;
      }
      console.log('Checkout clicked - Cart Items:', this.cartItems);
      this.$router.push('/Checkout');
    },

    async loadProducts(categoryId, subcategoryName = null) {
      try {
        this.productsLoading = true;
        
        if (this.isCustomCategory) {
          // Handle custom categories (keep existing logic)
          return;
        }
        
        const products = await productsAPI.getProductsByCategory(categoryId, subcategoryName);
        this.products = products;
        
        console.log('Loaded products:', products);
        
      } catch (error) {
        console.error('Failed to load products:', error);
        this.products = [];
      } finally {
        this.productsLoading = false;
      }
    },

    async selectSubcategory(subcategoryData) {
      console.log('Subcategory data:', subcategoryData); 
      this.currentSubcategory = subcategoryData;
      this.viewMode = 'products';
      this.breadcrumbs.push({
        name: subcategoryData.name,
        type: 'products',
        data: subcategoryData
      });
      
      // Load subcategory products
      await this.loadProducts(this.activeCategory, subcategoryData.name);
    },

    async loadProductsForSelection() {
      if (!this.selectedSourceCategory) return;
      
      try {
        const products = await productsAPI.getProductsByCategory(this.selectedSourceCategory);
        this.allProducts = products;
      } catch (error) {
        console.error('Failed to load products for selection:', error);
      }
    }

     
  }
}
</script>

<style scoped>
@import '@/assets/styles/NewOrder.css'

</style>