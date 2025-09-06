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
      products: [
        { id: 1, name: 'Chicken Ramen', description: 'Rich chicken broth with noodles', price: 150, category: 'noodles', image: 'https://via.placeholder.com/200x150/ff6b6b/white?text=Chicken+Ramen' },
        { id: 2, name: 'Pork Ramen', description: 'Savory pork broth ramen', price: 160, category: 'noodles', image: 'https://via.placeholder.com/200x150/4ecdc4/white?text=Pork+Ramen' },
        // Add more static products as needed for testing
      ]
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
      let products = this.products.filter(product => product.category === this.selectedSourceCategory);
      
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
        // Here you would load products from API
        // await this.loadProducts(categoryId);
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
    }
  }
}
</script>

<style scoped>
/* Existing styles remain the same... */
.new-order-page {
  display: flex;
  height: 100vh;
  background-color: #f8f9fa;
}

.main-area {
  flex: 1;
  overflow-y: auto;
}

.no-contents {
  background-color: white;
  min-height: 100%;
}

.header-top {
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.d-flex {
  display: flex;
}

.form-control {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  font-size: 1rem;
}

.me-2 {
  margin-right: 0.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: 1px solid #28a745;
  background: #28a745;
  color: white;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.btn:hover {
  background: #218838;
  border-color: #218838;
}

.header-bot {
  padding: 1.5rem 1rem;
  background-color: #f8f9fa;
}

.categories-container {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  padding: 0.5rem 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.categories-container::-webkit-scrollbar {
  display: none;
}

.cat-card {
  background: white;
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 120px;
  height: 100px;
  border: 2px solid #e9ecef;
  flex-shrink: 0;
  position: relative;
}

.cat-card:hover {
  border-color: #6f42c1;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(111, 66, 193, 0.2);
}

.cat-card.active {
  background: linear-gradient(135deg, #6f42c1 0%, #8b5cf6 100%);
  color: white;
  border-color: #6f42c1;
  box-shadow: 0 4px 8px rgba(111, 66, 193, 0.3);
}

.cat-card.add-category {
  border: 2px dashed #6f42c1;
  color: #6f42c1;
}

.cat-card.add-category:hover {
  background: #f8f6ff;
}

.delete-category-btn {
  position: absolute;
  top: -5px;
  right: -5px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #dc3545;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

.cat-icon {
  margin-bottom: 0.5rem;
  color: #6c757d;
}

.cat-card.active .cat-icon {
  color: white;
}

.cat-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
  color: #495057;
}

.cat-card.active .cat-label {
  color: white;
}

/* Add Options Container */
.add-options-container {
  display: contents; /* This makes the children appear as if they're direct children of the grid */
}

.add-options-container .add-item-card:first-child {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
  border: 2px solid #3498db;
}

.add-options-container .add-item-card:first-child:hover {
  background: linear-gradient(135deg, #2980b9 0%, #21618c 100%);
}

.add-options-container .add-item-card:last-child {
  border: 2px dashed #6f42c1;
  color: #6f42c1;
}

.add-options-container .add-item-card:last-child:hover {
  background: #f8f6ff;
}

/* Large Modal */
.large-modal {
  max-width: 800px;
  width: 95%;
  max-height: 90vh;
}

/* Product Selector Styles */
.product-selector-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  border-bottom: 2px solid #e9ecef;
  overflow-x: auto;
}

.tab-btn {
  padding: 0.75rem 1rem;
  border: none;
  background: none;
  cursor: pointer;
  color: #6c757d;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  white-space: nowrap;
  font-size: 0.875rem;
}

.tab-btn:hover {
  color: #495057;
  background: #f8f9fa;
}

.tab-btn.active {
  color: #6f42c1;
  border-bottom-color: #6f42c1;
}

.product-search {
  margin-bottom: 1rem;
}

.product-selection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 1rem;
  padding-right: 0.5rem;
}

.selectable-product {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.selectable-product:hover {
  border-color: #6f42c1;
  background: #f8f6ff;
}

.selectable-product.selected {
  border-color: #6f42c1;
  background: #f0ebff;
}

.selectable-product.already-added {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: #ced4da;
}

.selectable-product.already-added:hover {
  border-color: #ced4da;
  background: #f8f9fa;
}

.product-image-small {
  width: 50px;
  height: 50px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}

.product-image-small img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-details {
  flex: 1;
  min-width: 0;
}

.product-details h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #2d3748;
}

.product-details p {
  margin: 0 0 0.25rem 0;
  font-size: 0.875rem;
  color: #6f42c1;
  font-weight: 600;
}

.already-added-text {
  color: #6c757d;
  font-style: italic;
}

.selection-indicator {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkmark {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #6f42c1;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
}

.selection-summary {
  padding: 0.75rem;
  background: #f8f6ff;
  border-radius: 6px;
  border-left: 4px solid #6f42c1;
}

.selection-summary p {
  margin: 0;
  color: #6f42c1;
  font-weight: 600;
}

.error-text {
  color: #dc3545;
  font-size: 0.75rem;
  font-style: italic;
}

/* Scrollbar for product selection grid */
.product-selection-grid::-webkit-scrollbar {
  width: 6px;
}

.product-selection-grid::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.product-selection-grid::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.product-selection-grid::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Navigation Styles */
.breadcrumb-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: none;
  border: none;
  color: #6f42c1;
  cursor: pointer;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  transition: background-color 0.2s;
}

.breadcrumb-item:hover {
  background-color: #e9ecef;
}

/* Remove any CSS that might be adding "/" */
.breadcrumb-item::before,
.breadcrumb-item::after {
  content: none; /* Make sure no content is being added */
}

.category-search {
  padding: 1rem;
  background-color: white;
  border-bottom: 1px solid #e9ecef;
}

.search-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  font-size: 1rem;
}

.subcategory-indicator {
  color: #6f42c1;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

/* Pagination Styles */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  background-color: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.page-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #6f42c1;
  background: white;
  color: #6f42c1;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: #6f42c1;
  color: white;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #6c757d;
  font-size: 0.875rem;
}

/* Products Grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
  padding: 2rem;
}

.product-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.add-item-card {
  border: 2px dashed #6f42c1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #6f42c1;
}

.add-item-content {
  text-align: center;
}

.add-item-content p {
  margin: 0.5rem 0;
  font-weight: 600;
}

.add-item-content small {
  color: #6c757d;
}

.delete-product-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #dc3545;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.product-card:hover .delete-product-btn {
  opacity: 1;
}

.product-image {
  width: 100%;
  height: 150px;
  overflow: hidden;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-info {
  padding: 1rem;
  text-align: center;
}

.product-name {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: #495057;
}

.product-description {
  font-size: 0.875rem;
  color: #6c757d;
  margin: 0 0 0.75rem 0;
  line-height: 1.4;
}

.product-price {
  font-size: 1.25rem;
  font-weight: 700;
  color: #6f42c1;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  color: #2d3748;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #6c757d;
  padding: 0.25rem;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #374151;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #6f42c1;
  box-shadow: 0 0 0 3px rgba(111, 66, 193, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.icon-selector {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.5rem;
}

.icon-option {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem;
  border: 2px solid #e9ecef;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-option:hover {
  border-color: #6f42c1;
}

.icon-option.selected {
  border-color: #6f42c1;
  background: #f8f6ff;
  color: #6f42c1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e9ecef;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  border: none;
  background: #6f42c1;
  color: white;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

/* Cart Styles (keeping existing styles) */
.cart-sidebar {
  width: 400px;
  background: white;
  border-left: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  height: 100vh;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
}

.cart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.cart-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #495057;
  font-weight: 600;
}

.cart-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #6c757d;
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}

.cart-close:hover {
  background: #e9ecef;
  color: #495057;
}

.cart-items {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.empty-cart-message {
  text-align: center;
  padding: 2rem 1rem;
  color: #6c757d;
}

.empty-cart-message p {
  margin: 0.5rem 0;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  margin-bottom: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.cart-item-image {
  width: 50px;
  height: 50px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.cart-item-info {
  flex: 1;
  min-width: 0;
}

.cart-item-info h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.875rem;
  color: #495057;
  font-weight: 600;
}

.cart-item-info p {
  margin: 0;
  font-size: 0.75rem;
  color: #6c757d;
  line-height: 1.3;
}

.cart-item-price {
  font-weight: 600;
  color: #6f42c1;
  font-size: 0.875rem;
  margin-right: 0.5rem;
}

.cart-item-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.quantity-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all 0.2s ease;
}

.minus {
  background: #6c757d;
  color: white;
}

.plus {
  background: #6f42c1;
  color: white;
}

.quantity-btn:hover {
  opacity: 0.8;
  transform: scale(1.05);
}

.quantity {
  font-weight: 600;
  min-width: 20px;
  text-align: center;
  font-size: 0.875rem;
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  color: #dc3545;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.remove-btn:hover {
  background: #ffe6e6;
  transform: scale(1.1);
}

.cart-footer {
  padding: 1rem;
  border-top: 1px solid #e9ecef;
  background: white;
}

.cart-summary {
  background: #6f42c1;
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cart-info {
  color: white;
}

.item-count {
  font-size: 0.875rem;
  opacity: 0.9;
}

.cart-total {
  font-size: 1.25rem;
  font-weight: 700;
}

.pay-btn {
  background: white;
  color: #6f42c1;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pay-btn:hover:not(:disabled) {
  background: #f8f9fa;
  transform: translateY(-1px);
}

.pay-btn:disabled {
  background: #e9ecef;
  color: #6c757d;
  cursor: not-allowed;
}

/* Cart Toggle Button */
.cart-toggle {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: #6f42c1;
  color: white;
  border: none;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(111, 66, 193, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  z-index: 1000;
}

.cart-toggle:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(111, 66, 193, 0.5);
}

.cart-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #dc3545;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.breadcrumb-separator {
  margin: 0 0.5rem;
  color: #6c757d;
  font-weight: normal;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  color: #6f42c1;
  cursor: pointer;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  transition: background-color 0.2s;
}

.breadcrumb-item:hover {
  background-color: #e9ecef;
}

/* Responsive */
@media (max-width: 1200px) {
  .cart-sidebar {
    width: 350px;
  }
  
  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}

@media (max-width: 768px) {
  .new-order-page {
    flex-direction: column;
  }
  
  .cart-sidebar {
    width: 100%;
    height: 50vh;
  }
  
  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 1rem;
    padding: 1rem;
  }
}
</style>