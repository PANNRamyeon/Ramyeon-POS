<template>
  <div class="new-order-page">
    <!-- Main Content Area -->
    <div class="main-area">
      <div class="no-contents">
        <div class="no-header">
          <div class="header-top">
            <form class="d-flex" role="search">
              <input class="form-control me-2" type="search" placeholder="🔍 Search" aria-label="Search"/>
              <button class="btn btn-outline-success" type="submit">Search</button>
            </form>
          </div>
          <div class="header-bot">
            <div class="categories-container">
              <div 
                v-for="category in categories" 
                :key="category.id"
                :class="['cat-card', { active: activeCategory === category.id }]"
                @click="selectCategory(category.id)"
              >
                <div class="cat-icon">
                  <component :is="category.icon" />
                </div>
                <span class="cat-label">{{ category.name }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Products Grid -->
        <div class="products-grid">
          <div 
            v-for="product in filteredProducts" 
            :key="product.id"
            class="product-card"
            @click="addToCart(product)"
          >
            <div class="product-image">
              <img :src="product.image" :alt="product.name" />
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <p class="product-description">{{ product.description }}</p>
              <div class="product-price">₱{{ product.price }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Shopping Cart Sidebar -->
    <div v-if="showCart" class="cart-sidebar">
      <div class="cart-header">
        <h2>New Order</h2>
        <button class="cart-close" @click="closeCart"><Trash2 :size="20" /></button>
      </div>
      
      <div class="cart-items">
        <div 
          v-for="item in cartItems" 
          :key="item.id"
          class="cart-item"
        >
          <img :src="item.image" :alt="item.name" class="cart-item-image" />
          <div class="cart-item-info">
            <h4>{{ item.name }}</h4>
            <p>{{ item.description }}</p>
          </div>
          <div class="cart-item-price">₱{{ item.price }}</div>
          <div class="cart-item-controls">
            <button @click="decreaseQuantity(item)" class="quantity-btn minus"><Minus :size="20" /></button>
            <span class="quantity">{{ item.quantity }}</span>
            <button @click="increaseQuantity(item)" class="quantity-btn plus"><Plus :size="20" /></button>
          </div>
          <button @click="removeFromCart(item)" class="remove-btn"><Trash2 :size="20" /></button>
        </div>
      </div>

      <div class="cart-footer">
        <div class="cart-total">₱{{ cartTotal }}</div>
          <button class="pay-btn">Pay →</button>
        </div>
    </div>
  </div>
</template>

<script>


export default {
  name: 'NewOrder',
  components: {
  },
  data() {
    return {
      showCart: true, 
      activeCategory: 'noodles',
      cartItems: [
        { id: 1, name: 'Item', description: 'Placeholder', price: 99, quantity: 1, image: 'https://via.placeholder.com/60x40/ff6b6b/white?text=Item' },
        { id: 2, name: 'Item', description: 'Placeholder', price: 99, quantity: 1, image: 'https://via.placeholder.com/60x40/4ecdc4/white?text=Item' }
      ],
      categories: [
        { id: 'noodles', name: 'Noodles', icon: 'Soup' },
        { id: 'toppings', name: 'Toppings', icon: 'CookingPot' },
        { id: 'drinks', name: 'Drinks', icon: 'Coffee' },
        { id: 'others', name: 'Others', icon: 'Package' },
        { id: 'placeholder1', name: 'Placeholder', icon: 'Grid3X3' },
        { id: 'placeholder2', name: 'Placeholder', icon: 'ShoppingBag' },
        { id: 'placeholder3', name: 'Placeholder', icon: 'Utensils' },
        { id: 'placeholder4', name: 'Placeholder', icon: 'MoreHorizontal' }
      ],
      products: [
        { id: 1, name: 'Item', description: 'Placeholder', price: 99, category: 'noodles', image: 'https://via.placeholder.com/200x150/ff6b6b/white?text=Noodle+1' },
        { id: 2, name: 'Item', description: 'Placeholder', price: 99, category: 'noodles', image: 'https://via.placeholder.com/200x150/4ecdc4/white?text=Noodle+2' },
        { id: 3, name: 'Item', description: 'Placeholder', price: 99, category: 'noodles', image: 'https://via.placeholder.com/200x150/45b7d1/white?text=Noodle+3' },
        { id: 4, name: 'Item', description: 'Placeholder', price: 99, category: 'noodles', image: 'https://via.placeholder.com/200x150/f9ca24/white?text=Noodle+4' },
        { id: 5, name: 'Item', description: 'Placeholder', price: 99, category: 'noodles', image: 'https://via.placeholder.com/200x150/6c5ce7/white?text=Noodle+5' },
        { id: 6, name: 'Item', description: 'Placeholder', price: 99, category: 'noodles', image: 'https://via.placeholder.com/200x150/a55eea/white?text=Noodle+6' },
        { id: 7, name: 'Item', description: 'Placeholder', price: 99, category: 'noodles', image: 'https://via.placeholder.com/200x150/26de81/white?text=Noodle+7' },
        { id: 8, name: 'Item', description: 'Placeholder', price: 99, category: 'noodles', image: 'https://via.placeholder.com/200x150/fd79a8/white?text=Noodle+8' },
        { id: 9, name: 'Item', description: 'Placeholder', price: 99, category: 'noodles', image: 'https://via.placeholder.com/200x150/fdcb6e/white?text=Noodle+9' }
      ]
    }
  },
  computed: {
    filteredProducts() {
      return this.products.filter(product => product.category === this.activeCategory)
    },
    cartTotal() {
      return this.cartItems.reduce((total, item) => total + (item.price * item.quantity), 0)
    }
  },
  methods: {
    selectCategory(categoryId) {
      this.activeCategory = categoryId
    },
    closeCart() {
      this.showCart = false // Hide the sidebar
    },
    openCart() {
      this.showCart = true // Show the sidebar (optional method)
    },
    addToCart(product) {
      const existingItem = this.cartItems.find(item => item.id === product.id)
      if (existingItem) {
        existingItem.quantity++
      } else {
        this.cartItems.push({ ...product, quantity: 1 })
      }
      // Optionally auto-open cart when item is added
      this.showCart = true
    },
    removeFromCart(item) {
      const index = this.cartItems.findIndex(cartItem => cartItem.id === item.id)
      if (index > -1) {
        this.cartItems.splice(index, 1)
      }
    },
    increaseQuantity(item) {
      item.quantity++
    },
    decreaseQuantity(item) {
      if (item.quantity > 1) {
        item.quantity--
      }
    }
  }
}
</script>

<style scoped>
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
}

.d-flex {
  display: flex;
}

.form-control {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 0.375rem;
}

.me-2 {
  margin-right: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: 1px solid #28a745;
  background: transparent;
  color: #28a745;
  border-radius: 0.375rem;
  cursor: pointer;
}

.header-bot {
  padding: 1rem;
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

/* Products Grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
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
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
  margin: 0 0 0.25rem 0;
  color: #495057;
}

.product-description {
  font-size: 0.875rem;
  color: #6c757d;
  margin: 0 0 0.5rem 0;
}

.product-price {
  font-size: 1.125rem;
  font-weight: 700;
  color: #6f42c1;
}

/* Cart Sidebar */
.cart-sidebar {
  width: 400px;
  background: white;
  border-left: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.cart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.cart-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #495057;
}

.cart-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
}

.cart-items {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  margin-bottom: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.cart-item-image {
  width: 60px;
  height: 40px;
  object-fit: cover;
  border-radius: 4px;
}

.cart-item-info {
  flex: 1;
}

.cart-item-info h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.875rem;
  color: #495057;
}

.cart-item-info p {
  margin: 0;
  font-size: 0.75rem;
  color: #6c757d;
}

.cart-item-price {
  font-weight: 600;
  color: #495057;
  margin-right: 1rem;
}

.cart-item-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.quantity-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.minus {
  background: #6c757d;
  color: white;
}

.plus {
  background: #6f42c1;
  color: white;
}

.quantity {
  font-weight: 600;
  min-width: 20px;
  text-align: center;
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  color: #dc3545;
}

.cart-footer {
  padding: 0.7rem;
  border-radius: 20px;
  border-top: 1px solid #e9ecef;
  background: #6f42c1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cart-total {
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
}

.pay-btn {
  background: white;
  color: #6f42c1;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

/* Responsive */
@media (max-width: 1200px) {
  .cart-sidebar {
    width: 350px;
  }
  
  .products-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .products-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
    padding: 1rem;
  }
  
  .cart-sidebar {
    width: 300px;
  }
}
</style>