<template>
   <div class="checkout-page">
        <div class="cp-left">
            <div class="cpl-header">
                <button @click="goBack" class="nav-btn">
                    <ChevronLeft :size="20"/> 
                </button>
                <h1>Checkout</h1>
                <button class="trash-btn" @click="clearCart">
                    <Trash2 :size="25"/> 
                </button>
            </div>
            
            <div class="cpl-contents">
                <div v-if="cartItems.length === 0" class="empty-cart">
                    <div class="empty-icon">🛒</div>
                    <h3>Your cart is empty</h3>
                    <p>Add some items to get started!</p>
                    <button @click="goBack" class="continue-shopping-btn">
                        Continue Shopping
                    </button>
                </div>
                
                <div v-else class="cart-items-container">
                    <div class="cart-item-card" v-for="item in cartItems" :key="item.id">
                        <div class="item-image">
                            <img :src="item.image" :alt="item.name" />
                        </div>
                        
                        <div class="item-info">
                            <h3 class="item-name">{{ item.name }}</h3>
                            <p class="item-description">{{ item.description }}</p>
                            <div class="item-price-unit">₱{{ item.price }} each</div>
                        </div>
                        
                        <div class="item-controls">
                            <div class="quantity-controls">
                                <button 
                                    class="quantity-btn decrease" 
                                    @click="decreaseQuantity(item)"
                                    :disabled="item.quantity <= 1"
                                >
                                    <Minus :size="16" />
                                </button>
                                <span class="quantity">{{ item.quantity }}</span>
                                <button class="quantity-btn increase" @click="increaseQuantity(item)">
                                    <Plus :size="16" />
                                </button>
                            </div>
                            
                            <div class="item-total-price">
                                ₱{{ (item.price * item.quantity).toFixed(2) }}
                            </div>
                            
                            <button class="remove-item" @click="removeItem(item)" title="Remove item">
                                <X :size="18" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="cp-right">
            <div class="checkout-summary">
                <h2>Order Summary</h2>
                
                <div class="summary-details">
                    <div class="summary-row">
                        <span>Items ({{ totalItems }})</span>
                        <span>₱{{ cartTotal.toFixed(2) }}</span>
                    </div>
                    <div class="summary-row">
                        <span>Tax (12%)</span>
                        <span>₱{{ tax.toFixed(2) }}</span>
                    </div>
                    <div class="summary-divider"></div>
                    <div class="summary-row total">
                        <span>Total</span>
                        <span>₱{{ totalWithTax.toFixed(2) }}</span>
                    </div>
                </div>
                
                <div class="payment-section">
                    <h3>Payment Method</h3>
                    <div class="payment-options">
                        <label class="payment-option">
                            <input type="radio" name="payment" value="cash" v-model="paymentMethod">
                            <span class="payment-label">💵 Cash</span>
                        </label>
                        <label class="payment-option">
                            <input type="radio" name="payment" value="card" v-model="paymentMethod">
                            <span class="payment-label">💳 Card</span>
                        </label>
                        <label class="payment-option">
                            <input type="radio" name="payment" value="qrph" v-model="paymentMethod">
                            <span class="payment-label">📱 QR PH</span>
                        </label>
                    </div>
                </div>
                
                <button 
                    class="place-order-btn" 
                    @click="placeOrder"
                    :disabled="cartItems.length === 0"
                >
                    Place Order - ₱{{ totalWithTax.toFixed(2) }}
                </button>
            </div>
        </div>  
    </div>

</template>

<script>

export default {
    name: 'Checkout',
    components: {
    
    },
    data() {
        return {
            // Static example cart items for testing
            cartItems: [
                {
                    id: 1,
                    name: 'Chicken Ramen',
                    description: 'Rich chicken broth with fresh noodles and vegetables',
                    price: 150,
                    quantity: 2,
                    image: 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=300&h=200&fit=crop&crop=center'
                },
                {
                    id: 2,
                    name: 'Pork Gyoza',
                    description: 'Pan-fried dumplings with savory pork filling',
                    price: 120,
                    quantity: 1,
                    image: 'https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=300&h=200&fit=crop&crop=center'
                },
                {
                    id: 3,
                    name: 'Miso Ramen',
                    description: 'Traditional miso-based ramen with soft-boiled egg',
                    price: 160,
                    quantity: 1,
                    image: 'https://images.unsplash.com/photo-1557872943-16a5ac26437e?w=300&h=200&fit=crop&crop=center'
                },
                {
                    id: 4,
                    name: 'Green Tea',
                    description: 'Hot Japanese green tea',
                    price: 45,
                    quantity: 3,
                    image: 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=300&h=200&fit=crop&crop=center'
                },
                {
                    id: 5,
                    name: 'Takoyaki',
                    description: 'Octopus balls with takoyaki sauce and mayo',
                    price: 80,
                    quantity: 2,
                    image: 'https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=300&h=200&fit=crop&crop=center'
                }
            ],
            paymentMethod: 'cash',
            
        }
    },
    computed: {
        cartTotal() {
            return this.cartItems.reduce((total, item) => total + (item.price * item.quantity), 0)
        },
        totalItems() {
            return this.cartItems.reduce((total, item) => total + item.quantity, 0)
        },
        tax() {
            return (this.cartTotal ) * 0.12
        },
        totalWithTax() {
            return this.cartTotal + this.tax
        }
    },
    created() {
        // You can still load from route params if available, but fall back to static data
        if (this.$route.params.cartItems && this.$route.params.cartItems.length > 0) {
            this.cartItems = this.$route.params.cartItems;
        }
        // If no route params, the static data above will be used
    },
    methods: {
        goBack() {
            // For testing, you can just show an alert or do nothing
            alert('Going back to previous page...')
            // this.$router.go(-1)
        },
        clearCart() {
            if (confirm('Are you sure you want to clear your cart?')) {
                this.cartItems = []
            }
        },
        increaseQuantity(item) {
            item.quantity++
        },
        decreaseQuantity(item) {
            if (item.quantity > 1) {
                item.quantity--
            }
        },
        removeItem(item) {
            if (confirm(`Remove ${item.name} from cart?`)) {
                const index = this.cartItems.findIndex(cartItem => cartItem.id === item.id)
                if (index > -1) {
                    this.cartItems.splice(index, 1)
                }
            }
        },
        placeOrder() {
            if (this.cartItems.length === 0) {
                alert('Your cart is empty!')
                return
            }
            
            const orderData = {
                items: this.cartItems,
                subtotal: this.cartTotal,
                deliveryFee: this.deliveryFee,
                tax: this.tax,
                total: this.totalWithTax,
                paymentMethod: this.paymentMethod,
                orderDate: new Date().toISOString()
            }
            
            console.log('Order placed:', orderData)
            alert(`Order placed successfully!\nTotal: ₱${this.totalWithTax.toFixed(2)}\nPayment: ${this.paymentMethod.toUpperCase()}\nItems: ${this.totalItems}`)
            
            // For testing, just clear the cart
            this.cartItems = []
        }
    }   
}
</script>


<style scoped>
.checkout-page {
    display: flex;
    gap: 15px;
    padding: 15px;
    background-color: #f5f7fa;
    min-height: 100vh;
}

.cp-left {
    flex: 1;
    background-color: white;
    border-radius: 16px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    overflow: hidden;
}

.cp-right {
    width: 400px;
    background-color: white;
    border-radius: 16px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    padding: 0;
}

/* Header Styles */
.cpl-header {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 20px 25px;
    border-bottom: 1px solid #e9ecef;
    background-color: white;
}

.nav-btn, .trash-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 10px;
    border-radius: 10px;
    transition: all 0.2s ease;
    color: #6c757d;
}

.nav-btn:hover, .trash-btn:hover {
    background-color: #f8f9fa;
    color: #495057;
}

.trash-btn {
    margin-left: auto;
    color: #dc3545;
}

.trash-btn:hover {
    background-color: #ffe6e6;
}

.cpl-header h1 {
    font-size: 28px;
    margin: 0;
    color: #2d3748;
    font-weight: 600;
}

/* Cart Contents */
.cpl-contents {
    height: calc(100vh - 100px);
    overflow-y: auto;
    padding: 20px 25px;
    background-color: white;
}

.cart-items-container {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

/* Empty Cart */
.empty-cart {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 60px 20px;
    color: #6c757d;
}

.empty-icon {
    font-size: 64px;
    margin-bottom: 20px;
    opacity: 0.6;
}

.empty-cart h3 {
    font-size: 24px;
    margin: 10px 0;
    color: #495057;
}

.empty-cart p {
    font-size: 16px;
    margin-bottom: 30px;
}

.continue-shopping-btn {
    background: #6f42c1;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s;
}

.continue-shopping-btn:hover {
    background: #5a359a;
}

/* Cart Item Cards - FIXED */
.cart-item-card {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    padding: 20px;
    background-color: white;
    border-radius: 12px;
    border: 1px solid #e9ecef;
    transition: all 0.2s ease;
}

.cart-item-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border-color: #dee2e6;
    background-color: white; /* FIXED: Keep white on hover */
}

.item-image {
    width: 80px;
    height: 80px;
    border-radius: 10px;
    overflow: hidden;
    flex-shrink: 0;
    background: white;
    border: 1px solid #dee2e6;
}

.item-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.item-info {
    flex: 1;
    min-width: 0;
}

.item-name {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 5px 0;
    color: #2d3748;
}

.item-description {
    font-size: 14px;
    color: #6c757d;
    margin: 0 0 8px 0;
    line-height: 1.4;
}

.item-price-unit {
    font-size: 14px;
    color: #6f42c1;
    font-weight: 500;
}

.item-controls {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
}

.quantity-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    background: white;
    border-radius: 20px;
    padding: 4px;
    border: 1px solid #dee2e6;
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
    transition: all 0.2s ease;
}

.quantity-btn.decrease {
    background: #6c757d;
    color: white;
}

.quantity-btn.decrease:disabled {
    background: #e9ecef;
    color: #adb5bd;
    cursor: not-allowed;
}

.quantity-btn.increase {
    background: #6f42c1;
    color: white;
}

.quantity-btn:hover:not(:disabled) {
    opacity: 0.8;
    transform: scale(1.05);
}

.quantity {
    font-weight: 600;
    min-width: 30px;
    text-align: center;
    font-size: 16px;
    color: #495057;
}

.item-total-price {
    font-size: 18px;
    font-weight: 700;
    color: #2d3748;
}

.remove-item {
    background: none;
    border: none;
    cursor: pointer;
    color: #dc3545;
    padding: 6px;
    border-radius: 6px;
    transition: all 0.2s ease;
}

.remove-item:hover {
    background-color: #ffe6e6;
    transform: scale(1.1);
}

/* Checkout Summary */
.checkout-summary {
    padding: 25px;
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: white;
}

.checkout-summary h2 {
    margin: 0 0 25px 0;
    font-size: 24px;
    color: #2d3748;
    font-weight: 600;
}

.summary-details {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
}

.summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    font-size: 16px;
}

.summary-row:not(:last-child) {
    border-bottom: 1px solid #e9ecef;
}

.summary-divider {
    height: 1px;
    background: #dee2e6;
    margin: 15px 0;
}

.summary-row.total {
    font-weight: 700;
    font-size: 20px;
    color: #2d3748;
    padding: 15px 0 0 0;
    border-bottom: none;
}

/* Payment Section */
.payment-section {
    margin-bottom: 25px;
}

.payment-section h3 {
    margin: 0 0 15px 0;
    font-size: 18px;
    color: #2d3748;
    font-weight: 600;
}

.payment-options {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.payment-option {
    display: flex;
    align-items: center;
    cursor: pointer;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    transition: all 0.2s ease;
    background-color: white;
}

.payment-option:hover {
    background-color: #f8f9fa;
    border-color: #6f42c1;
}

.payment-option input[type="radio"] {
    margin-right: 12px;
    accent-color: #6f42c1;
}

.payment-label {
    font-size: 16px;
    color: #495057;
}

/* Place Order Button */
.place-order-btn {
    width: 100%;
    background: #6f42c1;
    color: white;
    border: none;
    padding: 16px;
    border-radius: 12px;
    font-size: 18px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-top: auto;
}

.place-order-btn:hover:not(:disabled) {
    background: #5a359a;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(111, 66, 193, 0.3);
}

.place-order-btn:disabled {
    background: #e9ecef;
    color: #6c757d;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

/* Legacy styles for backwards compatibility */
.cpl-card {
    width: 89%;
    height: auto;
    border-radius: 20px;
    background-color: white;
    margin-left: 32px;
    padding: 20px;
    margin-bottom: 1rem;
}

.item-row {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.item-details {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.item-price {
    font-size: 1.125rem;
    font-weight: 700;
    color: #333;
}

/* Scrollbar Styling */
.cpl-contents::-webkit-scrollbar {
    width: 6px;
}

.cpl-contents::-webkit-scrollbar-track {
    background: #f8f9fa;
    border-radius: 3px;
}

.cpl-contents::-webkit-scrollbar-thumb {
    background: #dee2e6;
    border-radius: 3px;
}

.cpl-contents::-webkit-scrollbar-thumb:hover {
    background: #ced4da;
}

/* Animations */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.cart-item-card {
    animation: fadeIn 0.3s ease-out;
}

.empty-cart {
    animation: fadeIn 0.5s ease-out;
}

/* Loading state */
.loading {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    color: #6c757d;
}

.loading::after {
    content: '';
    width: 20px;
    height: 20px;
    border: 2px solid #e9ecef;
    border-top-color: #6f42c1;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-left: 10px;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Responsive Design */
@media (max-width: 1024px) {
    .checkout-page {
        flex-direction: column;
        gap: 15px;
    }
    
    .cp-right {
        width: 100%;
    }
    
    .cart-item-card {
        flex-direction: column;
        text-align: center;
    }
    
    .item-controls {
        align-items: center;
        flex-direction: row;
        justify-content: space-between;
        width: 100%;
    }
}

@media (max-width: 768px) {
    .checkout-page {
        padding: 10px;
        gap: 10px;
    }
    
    .cpl-header {
        padding: 15px 20px;
    }
    
    .cpl-header h1 {
        font-size: 24px;
    }
    
    .cpl-contents {
        padding: 15px 20px;
        height: calc(100vh - 80px);
    }
    
    .checkout-summary {
        padding: 20px;
    }
    
    .cart-item-card {
        padding: 15px;
        gap: 12px;
    }
    
    .item-image {
        width: 60px;
        height: 60px;
    }
    
    .item-name {
        font-size: 16px;
    }
    
    .item-total-price {
        font-size: 16px;
    }
    
    .quantity-controls {
        gap: 6px;
        padding: 3px;
    }
    
    .quantity-btn {
        width: 28px;
        height: 28px;
    }
    
    .summary-details {
        padding: 15px;
        margin-bottom: 20px;
    }
    
    .payment-section {
        margin-bottom: 20px;
    }
    
    .payment-option {
        padding: 10px 12px;
    }
    
    .place-order-btn {
        padding: 14px;
        font-size: 16px;
    }
}

@media (max-width: 480px) {
    .checkout-page {
        padding: 5px;
    }
    
    .cpl-header {
        padding: 10px 15px;
        gap: 10px;
    }
    
    .cpl-header h1 {
        font-size: 20px;
    }
    
    .cpl-contents {
        padding: 10px 15px;
    }
    
    .checkout-summary {
        padding: 15px;
    }
    
    .cart-item-card {
        padding: 12px;
        gap: 10px;
    }
    
    .item-image {
        width: 50px;
        height: 50px;
    }
    
    .item-name {
        font-size: 14px;
    }
    
    .item-description {
        font-size: 12px;
    }
    
    .item-price-unit {
        font-size: 12px;
    }
    
    .item-total-price {
        font-size: 14px;
    }
    
    .quantity-btn {
        width: 24px;
        height: 24px;
    }
    
    .quantity {
        font-size: 14px;
        min-width: 24px;
    }
}

/* Print styles (for receipts) */
@media print {
    .checkout-page {
        background: white;
        padding: 0;
        gap: 0;
        flex-direction: column;
    }
    
    .cp-left {
        box-shadow: none;
        border-radius: 0;
    }
    
    .cp-right {
        box-shadow: none;
        border-radius: 0;
        width: 100%;
    }
    
    .cpl-header, .nav-btn, .trash-btn {
        display: none;
    }
    
    .item-controls .remove-item,
    .quantity-controls {
        display: none;
    }
    
    .payment-section,
    .place-order-btn {
        display: none;
    }
}

/* Focus styles for accessibility */
.nav-btn:focus,
.trash-btn:focus,
.quantity-btn:focus,
.remove-item:focus,
.continue-shopping-btn:focus,
.place-order-btn:focus {
    outline: 2px solid #6f42c1;
    outline-offset: 2px;
}

.payment-option:focus-within {
    border-color: #6f42c1;
    box-shadow: 0 0 0 2px rgba(111, 66, 193, 0.2);
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    .cart-item-card {
        border: 2px solid #000;
    }
    
    .quantity-btn.decrease {
        background: #000;
    }
    
    .quantity-btn.increase {
        background: #000;
    }
    
    .place-order-btn {
        background: #000;
    }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    .cart-item-card,
    .empty-cart,
    .quantity-btn,
    .remove-item,
    .place-order-btn,
    .nav-btn,
    .trash-btn {
        animation: none;
        transition: none;
    }
    
    .quantity-btn:hover:not(:disabled),
    .remove-item:hover,
    .place-order-btn:hover:not(:disabled) {
        transform: none;
    }
}

/* REMOVED: Dark mode support that was overriding white backgrounds */
</style>