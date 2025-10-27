<template>
  <div class="cart-sidebar">
    <h3>Cart ({{ cartCount }})</h3>
    
    <div v-for="item in cart" :key="item.cartId" class="cart-item">
      <span class="name">{{ item.name }}</span>
      <div class="quantity-controls">
        <button @click="updateQuantity(item.id, item.quantity - 1)">-</button>
        <span>{{ item.quantity }}</span>
        <button @click="updateQuantity(item.id, item.quantity + 1)">+</button>
      </div>
      <span class="price">${{ (item.price * item.quantity).toFixed(2) }}</span>
      <button @click="removeFromCart(item.id)" class="remove">×</button>
    </div>
    
    <div class="cart-total">
      Total: ${{ cartTotal.toFixed(2) }}
    </div>
    
    <button 
      @click="proceedToCheckout" 
      :disabled="cartCount === 0"
      class="checkout-btn"
    >
      Checkout
    </button>
  </div>
</template>

<script setup>
import { useOfflineCartStore } from '@/stores/offlineCartStore';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';

const router = useRouter();
const cartStore = useOfflineCartStore();

const { cart, cartCount, cartTotal } = storeToRefs(cartStore);

const updateQuantity = (productId, newQuantity) => {
  if (newQuantity < 1) {
    cartStore.removeFromCart(productId);
  } else {
    cartStore.updateQuantity(productId, newQuantity);
  }
};

const removeFromCart = (productId) => {
  cartStore.removeFromCart(productId);
};

const proceedToCheckout = () => {
  router.push('/checkout');
};
</script>