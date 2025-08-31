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
        <button class="cart-close" @click="closeCart"><X :size="20" /></button>
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
    
    <!-- Cart Toggle Button (when cart is closed) -->
    <button v-if="!showCart && cartItems.length > 0" class="cart-toggle" @click="openCart">
      <ShoppingCart :size="24" />
      <span class="cart-badge">{{ totalItems }}</span>
    </button>
  </div>
</template>

<script>
import { Minus, Plus, Trash2, X, ShoppingCart, Coffee, CookingPot, Package, Grid3X3, ShoppingBag, Utensils, MoreHorizontal } from 'lucide-vue-next'

export default {
  name: 'NewOrder',
  components: {
    Minus,
    Plus, 
    Trash2,
    X,
    ShoppingCart,
    Coffee,
    CookingPot,
    Package,
    Grid3X3,
    ShoppingBag,
    Utensils,
    MoreHorizontal
  },
  data() {
    return {
      showCart: true, 
      activeCategory: 'noodles',
      cartItems: [],
      categories: [
        { id: 'noodles', name: 'Noodles', icon: 'CookingPot' },
        { id: 'toppings', name: 'Toppings', icon: 'Package' },
        { id: 'drinks', name: 'Drinks', icon: 'Coffee' },
        { id: 'others', name: 'Others', icon: 'Grid3X3' },
        { id: 'placeholder1', name: 'Snacks', icon: 'ShoppingBag' },
        { id: 'placeholder2', name: 'Desserts', icon: 'Utensils' },
        { id: 'placeholder3', name: 'Combo', icon: 'MoreHorizontal' }
      ],
      products: [
        { id: 1, name: 'Chicken Ramen', description: 'Rich chicken broth with noodles', price: 150, category: 'noodles', image: 'https://via.placeholder.com/200x150/ff6b6b/white?text=Chicken+Ramen' },
        { id: 2, name: 'Pork Ramen', description: 'Savory pork broth ramen', price: 160, category: 'noodles', image: 'https://via.placeholder.com/200x150/4ecdc4/white?text=Pork+Ramen' },
        { id: 3, name: 'Beef Ramen', description: 'Hearty beef broth noodles', price: 180, category: 'noodles', image: 'https://via.placeholder.com/200x150/45b7d1/white?text=Beef+Ramen' },
        { id: 4, name: 'Veggie Ramen', description: 'Fresh vegetable ramen', price: 140, category: 'noodles', image: 'https://via.placeholder.com/200x150/f9ca24/white?text=Veggie+Ramen' },
        { id: 5, name: 'Spicy Ramen', description: 'Hot and spicy noodles', price: 170, category: 'noodles', image: 'https://via.placeholder.com/200x150/6c5ce7/white?text=Spicy+Ramen' },
        { id: 6, name: 'Seafood Ramen', description: 'Fresh seafood broth', price: 200, category: 'noodles', image: 'https://via.placeholder.com/200x150/a55eea/white?text=Seafood+Ramen' },
        { id: 7, name: 'Extra Egg', description: 'Soft-boiled egg topping', price: 25, category: 'toppings', image: 'https://via.placeholder.com/200x150/26de81/white?text=Extra+Egg' },
        { id: 8, name: 'Green Onions', description: 'Fresh green onion garnish', price: 15, category: 'toppings', image: 'https://via.placeholder.com/200x150/fd79a8/white?text=Green+Onions' },
        { id: 9, name: 'Coke', description: 'Ice cold Coca Cola', price: 45, category: 'drinks', image: 'https://via.placeholder.com/200x150/fdcb6e/white?text=Coke' },
        { id: 10, name: 'Iced Tea', description: 'Refreshing iced tea', price: 40, category: 'drinks', image: 'https://via.placeholder.com/200x150/ff7675/white?text=Iced+Tea' }
      ]
    }
  },
  computed: {
    filteredProducts() {
      return this.products.filter(product => product.category === this.activeCategory)
    },
    cartTotal() {
      return this.cartItems.reduce((total, item) => total + (item.price * item.quantity), 0)
    },
    totalItems() {
      return this.cartItems.reduce((total, item) => total + item.quantity, 0)
    }
  },
  methods: {
    checkout() {
      if (this.cartItems.length === 0) {
        alert('Your cart is empty!')
        return
      }

      console.log('Checkout clicked - Cart Items:', this.cartItems)
      console.log('Cart Total:', this.cartTotal)
      
      // Method 1: Using route params (current approach)
      this.$router.push({
        name: 'Checkout',
        params: {
          cartItems: JSON.stringify(this.cartItems), // Stringify to avoid reactivity issues
          cartTotal: this.cartTotal
        }
      })
      
      // Method 2: Using query parameters (alternative)
      /* 
      this.$router.push({
        name: 'Checkout',
        query: {
          cart: JSON.stringify(this.cartItems),
          total: this.cartTotal
        }
      })
      */
      
      // Method 3: Using localStorage (most reliable)
      /*
      localStorage.setItem('cartItems', JSON.stringify(this.cartItems))
      localStorage.setItem('cartTotal', this.cartTotal)
      this.$router.push({ name: 'Checkout' })
      */
    },

    selectCategory(categoryId) {
      this.activeCategory = categoryId
    },
    closeCart() {
      this.showCart = false 
    },
    openCart() {
      this.showCart = true 
    },
    addToCart(product) {
      const existingItem = this.cartItems.find(item => item.id === product.id)
      if (existingItem) {
        existingItem.quantity++
      } else {
        this.cartItems.push({ ...product, quantity: 1 })
      }
      this.showCart = true
      console.log('Added to cart:', product.name, 'Total items:', this.cartItems.length)
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

/* Cart Sidebar */
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