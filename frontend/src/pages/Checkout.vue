<template>
  <div class="checkout-page">
    <!-- Loading Overlay -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner-large"></div>
      <p>{{ loadingMessage }}</p>
    </div>

    <div class="cp-left">
      <div class="cpl-header">
        <button @click="goBack" class="nav-btn" :disabled="isProcessing">
          <ChevronLeft :size="20"/> 
        </button>
        <h1>Checkout</h1>
        <button class="trash-btn" @click="clearCart" :disabled="isProcessing">
          <Trash2 :size="25"/> 
        </button>
      </div>
      
      <div class="cpl-contents">
        <!-- Empty Cart State -->
        <div v-if="cartItems.length === 0" class="empty-cart">
          <div class="empty-icon">🛒</div>
          <h3>Your cart is empty</h3>
          <p>Add some items to get started!</p>
          <button @click="goBack" class="continue-shopping-btn">
            Continue Shopping
          </button>
        </div>
        
        <!-- Cart Items -->
        <div v-else class="cart-items-container">
          <div class="cart-item-card" v-for="item in cartItems" :key="item.id">
            <div class="item-image">
              <img :src="item.image" :alt="item.name" loading="lazy" />
            </div>
            
            <div class="item-info">
              <h3 class="item-name">{{ item.productName }}</h3>
              <p class="item-description">SKU: {{ item.sku }}</p>
              <div class="item-price-unit">₱{{ formatPrice(item.price) }} each</div>
            </div>
            
            <div class="item-controls">
              <div class="quantity-controls">
                <button 
                  class="quantity-btn decrease" 
                  @click="decreaseQuantity(item)"
                  :disabled="item.quantity <= 1 || quantityUpdating"
                >
                  <Minus :size="16" />
                </button>
                <span class="quantity">{{ item.quantity }}</span>
                <button 
                  class="quantity-btn increase" 
                  @click="increaseQuantity(item)"
                  :disabled="quantityUpdating"
                >
                  <Plus :size="16" />
                </button>
              </div>
              
              <div class="item-total-price">
                ₱{{ formatPrice(item.subtotal) }}
              </div>
              
              <button 
                class="remove-item" 
                @click="removeItem(item)" 
                title="Remove item"
                :disabled="quantityUpdating"
              >
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
        
        <!-- Customer Section -->
        <div class="customer-section">
          <h3>Customer (Optional)</h3>
          
          <!-- Customer Search -->
          <div v-if="!selectedCustomer" class="customer-search">
            <input 
              type="text" 
              class="form-control" 
              placeholder="Enter email or username"
              v-model="customerSearchQuery"
              @keyup.enter="searchCustomer"
              :disabled="isProcessing"
            />
            <button 
              class="btn btn-primary btn-sm" 
              @click="searchCustomer"
              :disabled="customerSearching || !customerSearchQuery.trim() || isProcessing"
            >
              {{ customerSearching ? 'Searching...' : 'Search' }}
            </button>
          </div>

          <!-- Customer Found -->
          <div v-if="selectedCustomer" class="customer-info-card">
            <div class="customer-header">
              <div class="customer-details">
                <h5>{{ selectedCustomer.full_name }}</h5>
                <p class="customer-username">@{{ selectedCustomer.username }}</p>
                <p v-if="selectedCustomer.email" class="customer-email">{{ selectedCustomer.email }}</p>
              </div>
              <button class="btn-remove" @click="clearCustomer" :disabled="isProcessing">
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
            </div>

            <!-- Points Action Buttons -->
            <div class="points-action-buttons">
              <button 
                :class="['points-action-btn', { active: pointsMode === 'earn' }]"
                @click="setPointsMode('earn')"
                type="button"
                :disabled="isProcessing"
              >
                <div class="action-icon">✨</div>
                <div class="action-content">
                  <span class="action-title">Earn Points</span>
                  <span class="action-subtitle">+{{ pointsWillEarn }} pts</span>
                </div>
              </button>

              <!-- ✅ CHANGED: from >= 200 to >= 100 -->
              <button 
                v-if="selectedCustomer.loyalty_points >= 100"
                :class="['points-action-btn', { active: pointsMode === 'use' }]"
                @click="setPointsMode('use')"
                type="button"
                :disabled="isProcessing"
              >
                <div class="action-icon">🎁</div>
                <div class="action-content">
                  <span class="action-title">Use Points</span>
                  <span class="action-subtitle">Up to {{ maxRedeemablePoints }} pts</span>
                </div>
              </button>

              <!-- ✅ CHANGED: text from 200+ to 100+ -->
              <div v-else class="points-insufficient-notice">
                <small>💡 Need 100+ points to redeem</small>
              </div>
            </div>

            <!-- ✅ CHANGED: condition from >= 200 to >= 100 -->
            <!-- Points Redemption Panel -->
            <div v-if="pointsMode === 'use' && selectedCustomer.loyalty_points >= 100" class="points-redemption-panel">
              <div class="redemption-header">
                <h6>Redeem Points</h6>
                <button class="btn-text" @click="setPointsMode('earn')" :disabled="isProcessing">Cancel</button>
              </div>
              
              <div class="redemption-input-group">
                <!-- ✅ CHANGED: min from 200 to 100 -->
                <input 
                  type="number" 
                  class="form-control points-input" 
                  placeholder="Enter points amount"
                  v-model.number="pointsToRedeem"
                  :max="Math.min(selectedCustomer.loyalty_points, maxRedeemablePoints)"
                  min="100"
                  step="100"
                  :disabled="isProcessing"
                />
                <button 
                  class="btn btn-success" 
                  @click="applyPointsDiscount"
                  :disabled="!canRedeemPoints || isProcessing"
                >
                  Apply
                </button>
              </div>
              
              <!-- ✅ CHANGED: text from "200 pts (₱50)" to "100 pts (₱25)" -->
              <div class="redemption-info-box">
                <div class="info-row">
                  <span>Minimum:</span>
                  <span>100 pts (₱25)</span>
                </div>
                <div class="info-row">
                  <span>Maximum:</span>
                  <span>{{ maxRedeemablePoints }} pts (₱{{ formatPrice(maxRedeemablePoints / 4) }})</span>
                </div>
                <div class="info-row">
                  <span>Discount Value:</span>
                  <span class="highlight">4 pts = ₱1</span>
                </div>
              </div>
            </div>

            <!-- Earning Preview -->
            <div v-if="pointsMode === 'earn'" class="points-earning-panel">
              <div class="earning-preview">
                <div class="earning-icon-large">✨</div>
                <div class="earning-info-large">
                  <h6>You'll Earn</h6>
                  <div class="earning-amount-large">{{ pointsWillEarn }} points</div>
                  <div class="earning-value-large">Worth ₱{{ formatPrice(pointsWillEarn / 4) }}</div>
                </div>
              </div>
              
              <div class="balance-preview-box">
                <div class="balance-row">
                  <span>Current Balance:</span>
                  <span>{{ selectedCustomer.loyalty_points }} pts</span>
                </div>
                <div class="balance-row balance-after">
                  <span>After Purchase:</span>
                  <span class="highlight-green">{{ customerNewBalance }} pts (+{{ pointsWillEarn }})</span>
                </div>
              </div>
              
              <div class="earning-note">
                💡 Earn 20% of your purchase as loyalty points
              </div>
            </div>

            <!-- Applied Points Discount -->
            <div v-if="appliedPointsDiscount > 0" class="applied-discount-badge">
              <div class="discount-content">
                <span class="discount-icon">🎁</span>
                <div class="discount-info">
                  <span class="discount-label">Points Applied</span>
                  <span class="discount-details">{{ pointsRedeemed }} pts = ₱{{ formatPrice(appliedPointsDiscount) }} off</span>
                </div>
              </div>
              <button class="btn-remove-discount" @click="removePointsDiscount" :disabled="isProcessing">
                <X :size="14" />
              </button>
            </div>
          </div>

          <!-- Customer Search Error -->
          <div v-if="customerSearchError" class="alert alert-danger">
            {{ customerSearchError }}
          </div>
        </div>

        <!-- Promotion Display -->
        <div v-if="appliedPromotion" class="promotion-section">
          <h3>Applied Promotion</h3>
          <div class="promotion-card">
            <div class="promotion-content">
              <span class="promotion-icon">🎉</span>
              <div class="promotion-info">
                <span class="promotion-name">{{ appliedPromotion.name }}</span>
                <span class="promotion-savings">Save ₱{{ formatPrice(promoDiscount) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Summary -->
        <div class="summary-details">
          <div class="summary-row">
            <span>Subtotal:</span>
            <span>₱{{ formatPrice(cartSubtotal) }}</span>
          </div>
          
          <div v-if="promoDiscount > 0" class="summary-row discount-row">
            <span>
              <i class="lucide-tag"></i> {{ appliedPromotion.name }}
            </span>
            <span class="discount-amount">-₱{{ formatPrice(promoDiscount) }}</span>
          </div>

          <div v-if="appliedPointsDiscount > 0" class="summary-row discount-row">
            <span>
              <i class="lucide-gift"></i> Points Discount
            </span>
            <span class="discount-amount">-₱{{ formatPrice(appliedPointsDiscount) }}</span>
          </div>
          
          <div class="summary-row">
            <span>Tax (12%):</span>
            <span>₱{{ formatPrice(taxAmount) }}</span>
          </div>
          
          <div class="summary-row total">
            <strong>TOTAL:</strong>
            <strong>₱{{ formatPrice(grandTotal) }}</strong>
          </div>
        </div>
        
        <!-- Payment Method Selection -->
        <div class="payment-section">
          <h3>Payment Method</h3>
          <div class="payment-options">
            <label class="payment-option" :class="{ disabled: isProcessing }">
              <input 
                type="radio" 
                name="payment" 
                value="cash" 
                v-model="paymentMethod"
                :disabled="isProcessing"
              >
              <span class="payment-label">💵 Cash</span>
            </label>
            <label class="payment-option" :class="{ disabled: isProcessing }">
              <input 
                type="radio" 
                name="payment" 
                value="card" 
                v-model="paymentMethod"
                :disabled="isProcessing"
              >
              <span class="payment-label">💳 Card (PayMongo)</span>
              <small class="coming-soon">Coming Soon</small>
            </label>
            <label class="payment-option" :class="{ disabled: isProcessing }">
              <input 
                type="radio" 
                name="payment" 
                value="qrph" 
                v-model="paymentMethod"
                :disabled="isProcessing"
              >
              <span class="payment-label">📱 QR PH (GCash/PayMaya)</span>
              <small class="coming-soon">Coming Soon</small>
            </label>
          </div>
        </div>
        
        <!-- Cash Payment Details -->
        <div v-if="paymentMethod === 'cash'" class="cash-payment-section">
          <div class="form-group">
            <label>Cash Tendered</label>
            <div class="input-with-currency">
              <span class="currency-symbol">₱</span>
              <input 
                type="number" 
                v-model.number="cashTendered" 
                placeholder="0.00"
                step="0.01"
                min="0"
                class="form-input"
                :disabled="isProcessing"
                @input="validateCashPayment"
              />
            </div>
            <small v-if="cashValidationError" class="error-text">
              {{ cashValidationError }}
            </small>
          </div>
          
          <div v-if="changeAmount >= 0 && cashTendered > 0" class="change-display">
            <span>Change</span>
            <span class="change-amount">₱{{ formatPrice(changeAmount) }}</span>
          </div>
        </div>
        
        <!-- Card Payment Placeholder -->
        <div v-else-if="paymentMethod === 'card'" class="payment-placeholder">
          <p class="placeholder-text">
            💳 Card payment via PayMongo will be available soon!
          </p>
          <small>For now, please use cash payment.</small>
        </div>
        
        <!-- QR PH Payment Placeholder -->
        <div v-else-if="paymentMethod === 'qrph'" class="payment-placeholder">
          <p class="placeholder-text">
            📱 GCash/PayMaya payment via PayMongo will be available soon!
          </p>
          <small>For now, please use cash payment.</small>
        </div>
        
        <!-- Place Order Button -->
        <button 
          class="place-order-btn" 
          @click="placeOrder"
          :disabled="!canPlaceOrder"
        >
          <span v-if="!isProcessing">
            Place Order - ₱{{ formatPrice(grandTotal) }}
          </span>
          <span v-else>
            Processing... <span class="btn-spinner"></span>
          </span>
        </button>
      </div>
    </div>
    
    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="modal-overlay" @click="closeSuccessModal">
      <div class="modal-content success-modal" @click.stop>
        <div class="modal-header success-header">
          <div class="success-icon">✓</div>
          <h3>Order Completed!</h3>
          <button class="close-btn" @click="closeSuccessModal">
            <X :size="20" />
          </button>
        </div>
        <div class="modal-body">
          <div class="success-details">
            <div class="detail-row">
              <span>Sale ID:</span>
              <strong>{{ completedSale.saleId }}</strong>
            </div>
            <div class="detail-row">
              <span>Date:</span>
              <strong>{{ formatDateTime(completedSale.transactionDate) }}</strong>
            </div>
            <div class="detail-row">
              <span>Total Amount:</span>
              <strong class="total-highlight">₱{{ formatPrice(completedSale.totalAmount) }}</strong>
            </div>
            <div class="detail-row">
              <span>Payment Method:</span>
              <strong>{{ completedSale.paymentMethod.toUpperCase() }}</strong>
            </div>
            <div v-if="completedSale.shiftId" class="detail-row">
              <span>Shift ID:</span>
              <strong>{{ completedSale.shiftId }}</strong>
            </div>
            <div v-if="completedSale.change > 0" class="detail-row change-row">
              <span>Change:</span>
              <strong>₱{{ formatPrice(completedSale.change) }}</strong>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="printReceipt">
            <Printer :size="18" /> Print Receipt
          </button>
          <button class="btn-primary" @click="startNewOrder">
            New Order
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useCartStore } from '@/stores/cartStores'
import apiSales from '@/services/apiSales'
import apiProducts from '@/services/apiProducts'
import { api } from '@/services/api.js'

export default {
  name: 'Checkout',
  
  setup() {
    const cartStore = useCartStore()
    return { cartStore }
  },
  
  data() {
    return {
      // Loading states
      isLoading: false,
      loadingMessage: 'Loading...',
      isProcessing: false,
      
      // Products for promotion calculation
      products: [],
      
      // Stock validation
      validationErrors: [],
      quantityUpdating: false,
      
      // Customer & Points
      customerSearchQuery: '',
      customerSearching: false,
      customerSearchError: null,
      selectedCustomer: null,
      pointsMode: 'earn',
      pointsToRedeem: 0,
      pointsRedeemed: 0,
      appliedPointsDiscount: 0,
      
      // Promotions
      appliedPromotion: null,
      
      // Payment
      paymentMethod: 'cash',
      cashTendered: 0,
      cashValidationError: null,
      
      // Success modal
      showSuccessModal: false,
      completedSale: {
        saleId: null,
        transactionDate: null,
        totalAmount: 0,
        paymentMethod: '',
        change: 0,
        shiftId: null
      }
    }
  },
  
  computed: {
    cartItems() {
      return this.cartStore.items
    },
    
    cartSubtotal() {
      return this.cartStore.total
    },
    
    // Promo discount calculation
    promoDiscount() {
      if (!this.appliedPromotion) {
        console.log('⚠️ No promotion applied')
        return 0
      }
      
      const promotion = this.appliedPromotion
      console.log('\n💰 Calculating promo discount...')
      console.log('   Promotion:', promotion.name)
      console.log('   Type:', promotion.type)
      console.log('   Value:', promotion.discount_value)
      
      // ✅ SAFETY CHECK
      if (!promotion.discount_config) {
        console.warn('⚠️ Missing discount_config')
        return 0
      }
      
      const targetType = promotion.discount_config.target_type
      const targetIds = promotion.discount_config.target_ids || []
      
      console.log('   Target Type:', targetType)
      console.log('   Target IDs:', targetIds)
      console.log('   Cart Items:', this.cartItems.length)
      console.log('   Products Loaded:', this.products.length)
      
      let eligibleAmount = 0
      
      if (targetType === 'all') {
        eligibleAmount = this.cartSubtotal
        console.log('   ✅ ALL items eligible: ₱' + eligibleAmount)
        
      } else if (targetType === 'categories') {
        console.log('   🔍 Checking category matches...')
        
        // Filter cart items by category
        const eligibleItems = this.cartItems.filter(item => {
          const product = this.products.find(p => p.id === item.productId)
          
          if (!product) {
            console.log(`      ⚠️ Product not found: ${item.productId} (${item.productName})`)
            return false
          }
          
          const productCategory = product.category
          const isEligible = targetIds.includes(productCategory)
          
          console.log(`      ${isEligible ? '✅' : '❌'} ${product.name}`)
          console.log(`         Category: "${productCategory}"`)
          console.log(`         Targets:`, targetIds)
          console.log(`         Subtotal: ₱${item.subtotal}`)
          
          return isEligible
        })
        
        eligibleAmount = eligibleItems.reduce((sum, item) => sum + item.subtotal, 0)
        console.log(`   💰 Category total: ₱${eligibleAmount} (${eligibleItems.length} items)`)
        
      } else if (targetType === 'products') {
        console.log('   🔍 Checking product matches...')
        
        // Filter cart items by product ID
        const eligibleItems = this.cartItems.filter(item => {
          const isEligible = targetIds.includes(item.productId)
          
          console.log(`      ${isEligible ? '✅' : '❌'} ${item.productName}`)
          console.log(`         Product ID: "${item.productId}"`)
          console.log(`         Targets:`, targetIds)
          console.log(`         Subtotal: ₱${item.subtotal}`)
          
          return isEligible
        })
        
        eligibleAmount = eligibleItems.reduce((sum, item) => sum + item.subtotal, 0)
        console.log(`   💰 Products total: ₱${eligibleAmount} (${eligibleItems.length} items)`)
      }
      
      if (eligibleAmount === 0) {
        console.log('   ❌ No eligible items - Discount = ₱0')
        return 0
      }
      
      // Calculate discount
      let discount = 0
      
      if (promotion.type === 'percentage') {
        discount = eligibleAmount * (promotion.discount_value / 100)
        console.log(`   💰 Calculation: ₱${eligibleAmount} × ${promotion.discount_value}% = ₱${discount}`)
      } else if (promotion.type === 'fixed') {
        discount = Math.min(promotion.discount_value, eligibleAmount)
        console.log(`   💰 Calculation: min(₱${promotion.discount_value}, ₱${eligibleAmount}) = ₱${discount}`)
      }
      
      const finalDiscount = Math.round(discount * 100) / 100
      console.log(`   ✅ FINAL DISCOUNT: ₱${finalDiscount}\n`)
      
      return finalDiscount
    },
    
    // Subtotal after promo
    subtotalAfterPromo() {
      return Math.max(0, this.cartSubtotal - this.promoDiscount)
    },
    
    // Tax on discounted amount
    taxAmount() {
      const taxableAmount = this.subtotalAfterPromo - this.appliedPointsDiscount
      return Math.round(taxableAmount * 0.12 * 100) / 100
    },
    
    // Grand total
    grandTotal() {
      return Math.max(0, this.subtotalAfterPromo - this.appliedPointsDiscount + this.taxAmount)
    },
    
    totalItems() {
      return this.cartStore.itemCount
    },
    
    // Points calculations
    maxRedeemablePoints() {
      if (!this.selectedCustomer) return 0
      
      const baseAmount = this.subtotalAfterPromo
      const maxDiscountAmount = baseAmount * 0.5
      const maxPointsFromCart = Math.floor(maxDiscountAmount * 4)
      const customerPoints = this.selectedCustomer.loyalty_points || 0
      const finalMaxPoints = Math.min(maxPointsFromCart, customerPoints)
      
      return finalMaxPoints
    },
    
    canRedeemPoints() {
      if (!this.pointsToRedeem || !this.selectedCustomer) return false
      if (this.pointsToRedeem < 100) return false
      if (this.pointsToRedeem > this.selectedCustomer.loyalty_points) return false
      if (this.pointsToRedeem > this.maxRedeemablePoints) return false
      return true
    },
    
    pointsWillEarn() {
      if (!this.selectedCustomer || this.pointsMode !== 'earn') return 0
      const earnableAmount = this.grandTotal
      return Math.floor(earnableAmount * 0.20)
    },
    
    customerNewBalance() {
      if (!this.selectedCustomer) return 0
      const currentPoints = this.selectedCustomer.loyalty_points || 0
      const pointsUsed = this.pointsRedeemed
      const pointsEarned = this.pointsWillEarn
      return currentPoints - pointsUsed + pointsEarned
    },
    
    changeAmount() {
      if (this.paymentMethod !== 'cash') return 0
      return Math.max(0, this.cashTendered - this.grandTotal)
    },
    
    canPlaceOrder() {
      if (this.cartItems.length === 0) return false
      if (this.isProcessing) return false
      if (this.validationErrors.length > 0) return false
      
      if (this.paymentMethod === 'cash') {
        return this.cashTendered >= this.grandTotal
      }
      
      if (this.paymentMethod === 'card' || this.paymentMethod === 'qrph') {
        return false
      }
      
      return true
    }
  },
  
  async mounted() {
    await this.loadCheckoutData()
    await this.validateStock()
  },
  
  methods: {
    // ================================================================
    // LOAD CHECKOUT DATA
    // ================================================================
    
    async loadCheckoutData() {
      try {
        this.isLoading = true
        this.loadingMessage = 'Loading checkout data...'
        
        // ✅ STEP 1: Load products for promotion calculation
        await this.loadProductsForPromotion()
        
        // ✅ STEP 2: Load promotion from session
        const promoData = sessionStorage.getItem('appliedPromotion')
        console.log('\n🎟️ ========================================')
        console.log('   LOADING PROMOTION FROM SESSION')
        console.log('🎟️ ========================================')
        console.log('Raw sessionStorage data:', promoData)
        
        if (promoData) {
          try {
            const parsedPromo = JSON.parse(promoData)
            console.log('Parsed promotion object:', parsedPromo)
            console.log('Promotion structure check:')
            console.log('  - _id:', parsedPromo._id || parsedPromo.promotion_id)
            console.log('  - name:', parsedPromo.promotion_name || parsedPromo.name)
            console.log('  - type:', parsedPromo.type)
            console.log('  - discount_value:', parsedPromo.discount_value)
            console.log('  - discount_config:', parsedPromo.discount_config)
            
            // ✅ FIX: Handle both formats (from NewOrder.vue)
            const promotion = {
              _id: parsedPromo.promotion_id || parsedPromo._id,
              name: parsedPromo.promotion_name || parsedPromo.name,
              type: parsedPromo.type,
              discount_value: parsedPromo.discount_value,
              discount_config: parsedPromo.discount_config
            }
            
            // ✅ Parse discount_config if it's a string
            if (typeof promotion.discount_config === 'string') {
              try {
                promotion.discount_config = JSON.parse(promotion.discount_config)
                console.log('✅ Parsed discount_config:', promotion.discount_config)
              } catch (e) {
                console.error('❌ Failed to parse discount_config:', e)
              }
            }
            
            // ✅ VERIFY: Ensure all required fields exist
            if (!promotion._id || !promotion.name || !promotion.type || !promotion.discount_value) {
              console.error('❌ Incomplete promotion data:', promotion)
              console.error('❌ Missing required fields')
              this.appliedPromotion = null
            } else {
              this.appliedPromotion = promotion
              console.log('✅ Loaded promotion:', this.appliedPromotion.name)
              console.log('✅ Final promotion object:', this.appliedPromotion)
            }
            
          } catch (error) {
            console.error('❌ Failed to parse promotion data:', error)
            this.appliedPromotion = null
          }
        } else {
          console.log('⚠️ No promotion in session')
        }
        console.log('🎟️ ========================================\n')
        
        // ✅ STEP 3: Load customer from session
        const customerData = sessionStorage.getItem('checkoutCustomer')
        if (customerData) {
          const customer = JSON.parse(customerData)
          this.selectedCustomer = {
            _id: customer.customer_id,
            full_name: customer.full_name,
            username: customer.username || 'customer',
            email: customer.email,
            loyalty_points: customer.currentPoints || 0
          }
          
          if (customer.pointsRedeemed > 0) {
            this.pointsMode = 'use'
            this.pointsRedeemed = customer.pointsRedeemed
            this.appliedPointsDiscount = customer.pointsDiscount
          }
          
          console.log('✅ Loaded customer:', this.selectedCustomer.full_name)
        }
        
      } catch (error) {
        console.error('❌ Failed to load checkout data:', error)
      } finally {
        this.isLoading = false
      }
    },
    
    // ✅ NEW METHOD: Load products for promotion calculation
    async loadProductsForPromotion() {
      try {
        console.log('📦 Loading products for promotion calculation...')
        console.log('📦 Cart items:', this.cartItems.length)
        
        if (this.cartItems.length === 0) {
          console.warn('⚠️ No cart items to load products for')
          return
        }
        
        // Get all unique product IDs from cart
        const productIds = [...new Set(this.cartItems.map(item => item.productId))]
        console.log('📦 Product IDs to fetch:', productIds)
        
        // Fetch products in batch
        const products = await apiProducts.getProductsBatch(productIds)
        console.log('📦 Fetched products:', products)
        
        // Store products in data for promotion calculation
        this.products = products
        
        // ✅ VERIFY: Check if products have category IDs
        console.log('\n🔍 Product Categories:')
        products.forEach(p => {
          console.log(`   ${p.name}: ${p.category}`)
        })
        
        console.log('✅ Products loaded for promotion calculation')
        
      } catch (error) {
        console.error('❌ Failed to load products:', error)
      }
    },
    
    // ================================================================
    // CUSTOMER LOOKUP
    // ================================================================
    
    async searchCustomer() {
      if (!this.customerSearchQuery.trim()) return
      
      try {
        this.customerSearching = true
        this.customerSearchError = null
        
        const query = this.customerSearchQuery.trim().toLowerCase()
        console.log('🔍 Searching for customer:', query)
        
        const response = await api.get('/customers/', {
          params: { search: query }
        })
        
        console.log('📦 Raw API response:', response.data)
        
        const findCustomers = (obj) => {
          if (Array.isArray(obj)) {
            if (obj.length > 0 && obj[0]._id && obj[0]._id.startsWith('CUST-')) {
              return obj
            }
          }
          
          if (obj && typeof obj === 'object') {
            if (obj.customers && Array.isArray(obj.customers)) {
              return obj.customers
            }
            if (obj.data) {
              return findCustomers(obj.data)
            }
            if (obj._id && obj._id.startsWith('CUST-')) {
              return [obj]
            }
          }
          
          return []
        }
        
        const customers = findCustomers(response.data)
        
        console.log('👥 Found customers:', customers)
        
        if (customers && customers.length > 0) {
          const customer = customers.find(c => 
            c.username?.toLowerCase() === query ||
            c.email?.toLowerCase() === query ||
            c._id?.toLowerCase() === query
          )
          
          if (!customer) {
            console.warn('⚠️ No exact match found for query:', query)
            this.customerSearchError = 'Customer not found. Please check the username/email.'
            return
          }
          
          console.log('📋 Matched customer:', customer)
          
          this.selectedCustomer = {
            _id: customer._id,
            username: customer.username,
            full_name: customer.full_name,
            email: customer.email,
            phone: customer.phone,
            loyalty_points: customer.loyalty_points || 0
          }
          
          console.log('✅ Selected customer:', this.selectedCustomer.full_name)
          this.customerSearchQuery = ''
          
        } else {
          console.warn('⚠️ No customers found in response')
          this.customerSearchError = 'Customer not found. Please check the username/email.'
        }
        
      } catch (error) {
        console.error('❌ Customer search failed:', error)
        
        if (error.response?.status === 403) {
          this.customerSearchError = 'Permission denied. Contact administrator.'
        } else if (error.response?.status === 400) {
          this.customerSearchError = 'Invalid search query.'
        } else {
          this.customerSearchError = 'Failed to search customer. Please try again.'
        }
      } finally {
        this.customerSearching = false
      }
    },
    
    clearCustomer() {
      this.selectedCustomer = null
      this.customerSearchQuery = ''
      this.customerSearchError = null
      this.pointsMode = 'earn'
      this.removePointsDiscount()
    },
    
    setPointsMode(mode) {
      this.pointsMode = mode
      if (mode === 'earn' && this.appliedPointsDiscount > 0) {
        this.removePointsDiscount()
      }
    },
    
    applyPointsDiscount() {
      if (!this.canRedeemPoints) {
        alert('Invalid points amount. Please enter between 100 and ' + this.maxRedeemablePoints + ' points.')
        return
      }
      
      const discount = this.pointsToRedeem / 4
      
      if (discount > this.subtotalAfterPromo) {
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
    // STOCK VALIDATION
    // ================================================================
    
    async validateStock() {
      try {
        this.isLoading = true
        this.loadingMessage = 'Validating stock...'
        
        console.log('🔍 Validating stock for', this.cartItems.length, 'items...')
        
        if (this.cartItems.length === 0) {
          this.$router.replace('/new-order')
          return
        }
        
        const productIds = this.cartItems.map(item => item.productId)
        const products = await apiProducts.getProductsBatch(productIds)
        
        const productMap = {}
        products.forEach(product => {
          productMap[product.id || product._id] = product
        })
        
        const errors = []
        
        for (const item of this.cartItems) {
          const product = productMap[item.productId]
          
          if (!product) {
            errors.push(`Product "${item.productName}" not found`)
          } else {
            const availableStock = product.batch_stock || product.stock || 0
            
            if (availableStock < item.quantity) {
              errors.push(
                `Insufficient stock for "${item.productName}". ` +
                `Available: ${availableStock}, Requested: ${item.quantity}`
              )
            }
          }
        }
        
        if (errors.length > 0) {
          this.validationErrors = errors
          alert('Stock validation failed:\n\n' + errors.join('\n') + '\n\nPlease update your cart.')
          this.$router.replace('/new-order')
        } else {
          this.validationErrors = []
        }
        
      } catch (error) {
        console.error('❌ Stock validation failed:', error)
        alert(`Failed to validate stock: ${error.message}`)
        this.$router.replace('/new-order')
      } finally {
        this.isLoading = false
      }
    },
    
    // ================================================================
    // CART UPDATES
    // ================================================================
    
    increaseQuantity(item) {
      this.cartStore.increaseQuantity(item.productId)
    },
    
    decreaseQuantity(item) {
      this.cartStore.decreaseQuantity(item.productId)
    },
    
    async removeItem(item) {
      if (!confirm(`Remove ${item.productName} from cart?`)) return
      
      this.cartStore.removeItem(item.productId)
      
      if (this.cartStore.isEmpty) {
        alert('Cart is now empty. Returning to order page...')
        this.$router.replace('/new-order')
      }
    },
    
    async clearCart() {
      if (!confirm('Are you sure you want to clear your entire cart?')) return
      
      this.cartStore.clearCart()
      alert('Cart cleared. Returning to order page...')
      this.$router.replace('/new-order')
    },
    
    // ================================================================
    // PAYMENT
    // ================================================================
    
    validateCashPayment() {
      this.cashValidationError = null
      
      if (this.cashTendered <= 0) {
        this.cashValidationError = 'Please enter cash tendered amount'
        return false
      }
      
      if (this.cashTendered < this.grandTotal) {
        const shortage = this.grandTotal - this.cashTendered
        this.cashValidationError = `Insufficient. Need ₱${this.formatPrice(shortage)} more`
        return false
      }
      
      return true
    },
    
    async placeOrder() {
      if (!this.canPlaceOrder) {
        alert('Please complete payment details before placing order.')
        return
      }
      
      if (this.paymentMethod === 'cash' && !this.validateCashPayment()) {
        return
      }
      
      const confirmMessage = `Confirm order:\nTotal: ₱${this.formatPrice(this.grandTotal)}\n` +
        (this.appliedPromotion ? `Promo: -₱${this.formatPrice(this.promoDiscount)}\n` : '') +
        (this.appliedPointsDiscount > 0 ? `Points: -₱${this.formatPrice(this.appliedPointsDiscount)}\n` : '') +
        (this.paymentMethod === 'cash' ? `Cash: ₱${this.formatPrice(this.cashTendered)}\nChange: ₱${this.formatPrice(this.changeAmount)}` : '')
      
      if (!confirm(confirmMessage)) return
      
      try {
        this.isProcessing = true
        this.isLoading = true
        this.loadingMessage = 'Processing order...'
        
        await this.validateStock()
        
        if (this.validationErrors.length > 0) {
          throw new Error('Stock validation failed')
        }
        
        const saleData = this.cartStore.getCheckoutData()
        
        saleData.subtotal = this.cartSubtotal
        saleData.tax_amount = this.taxAmount
        saleData.total_amount = this.grandTotal
        
        if (this.selectedCustomer) {
          saleData.customer_id = this.selectedCustomer._id
          saleData.loyalty_points_used = this.pointsRedeemed
          saleData.loyalty_points_earned = this.pointsWillEarn
        }
        
        if (this.appliedPromotion) {
          saleData.promotion_id = this.appliedPromotion._id
          saleData.promotion_discount = this.promoDiscount
        } else {
          saleData.promotion_discount = 0
        }
        
        if (this.appliedPointsDiscount > 0) {
          saleData.points_discount = this.appliedPointsDiscount
        } else {
          saleData.points_discount = 0
        }
        
        saleData.discount = this.promoDiscount + this.appliedPointsDiscount
        
        saleData.payment_method = this.paymentMethod
        saleData.payment_details = {
          method: this.paymentMethod,
          amount_paid: this.paymentMethod === 'cash' ? this.cashTendered : this.grandTotal,
          change: this.paymentMethod === 'cash' ? this.changeAmount : 0,
          status: 'completed',
          transaction_id: `${this.paymentMethod.toUpperCase()}-${Date.now()}`,
          timestamp: new Date().toISOString()
        }
        
        console.log('📝 Final Sale Data:', saleData)
        
        const result = await apiSales.createSale(saleData)
        
        this.cartStore.clearCart()
        sessionStorage.removeItem('appliedPromotion')
        sessionStorage.removeItem('checkoutCustomer')
        
        this.completedSale = {
          saleId: result._id || result.sale_id,
          transactionDate: result.transaction_date || new Date().toISOString(),
          totalAmount: result.total_amount,
          paymentMethod: this.paymentMethod,
          change: this.changeAmount,
          shiftId: result.shift_id || saleData.shift_id
        }
        
        this.showSuccessModal = true
        console.log('🎉 Order completed successfully!')
        
      } catch (error) {
        console.error('❌ Place order failed:', error)
        alert(`Order failed: ${error.message}`)
      } finally {
        this.isProcessing = false
        this.isLoading = false
      }
    },
    
    // ================================================================
    // SUCCESS MODAL & RECEIPT
    // ================================================================
    
    async printReceipt() {
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const receiptUrl = `${baseUrl}/pos/sales/${this.completedSale.saleId}/receipt/`
        
        const printWindow = window.open(receiptUrl, '_blank', 'width=800,height=600')
        
        if (printWindow) {
          printWindow.onload = () => {
            setTimeout(() => {
              printWindow.print()
            }, 500)
          }
        }
      } catch (error) {
        console.error('❌ Print receipt failed:', error)
        alert(`Failed to print receipt: ${error.message}`)
      }
    },
    
    closeSuccessModal() {
      this.showSuccessModal = false
      this.startNewOrder()
    },
    
    startNewOrder() {
      this.$router.replace('/new-order')
    },
    
    // ================================================================
    // NAVIGATION
    // ================================================================
    
    goBack() {
      if (confirm('Return to order page? Your cart will be saved.')) {
        this.$router.push('/new-order')
      }
    },
    
    // ================================================================
    // UTILITIES
    // ================================================================
    
    formatPrice(price) {
      return parseFloat(price || 0).toFixed(2)
    },
    
    formatDateTime(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
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

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.spinner-large {
  width: 60px;
  height: 60px;
  border: 4px solid #e9ecef;
  border-top-color: #6f42c1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

.loading-overlay p {
  font-size: 18px;
  color: #495057;
  font-weight: 500;
}

/* Cash Payment Section */
.cash-payment-section {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.input-with-currency {
  position: relative;
  display: flex;
  align-items: center;
}

.currency-symbol {
  position: absolute;
  left: 15px;
  font-size: 18px;
  font-weight: 600;
  color: #495057;
  pointer-events: none;
}

.input-with-currency .form-input {
  padding-left: 40px;
  font-size: 18px;
  font-weight: 600;
}

.change-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: white;
  border-radius: 8px;
  margin-top: 15px;
  border: 2px solid #4ea87a;
}

.change-amount {
  font-size: 24px;
  font-weight: 700;
  color: #4ea87a;
}

/* Payment Placeholder */
.payment-placeholder {
  margin-top: 20px;
  padding: 20px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 12px;
  text-align: center;
}

.placeholder-text {
  font-size: 16px;
  color: #856404;
  margin-bottom: 10px;
}

.payment-placeholder small {
  color: #856404;
  font-size: 14px;
}

.coming-soon {
  display: block;
  font-size: 11px;
  color: #6c757d;
  margin-top: 4px;
  font-style: italic;
}

.payment-option.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Button Spinner */
.btn-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-left: 8px;
}

/* Success Modal */
.success-modal {
  max-width: 500px;
}

.success-header {
  background: linear-gradient(135deg, #4ea87a 0%, #5eb488 100%);
  color: white;
  padding: 30px;
  text-align: center;
  border-radius: 16px 16px 0 0;
  position: relative;
}

.success-icon {
  width: 80px;
  height: 80px;
  background: white;
  color: #4ea87a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  font-weight: bold;
  margin: 0 auto 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.success-header h3 {
  margin: 0;
  font-size: 24px;
}

.success-header .close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.success-header .close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.success-details {
  padding: 30px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #e9ecef;
  font-size: 16px;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row span {
  color: #6c757d;
}

.detail-row strong {
  color: #2d3748;
  font-weight: 600;
}

.total-highlight {
  font-size: 20px;
  color: #4ea87a !important;
}

.change-row {
  background: #f8f9fa;
  padding: 12px 15px;
  margin: 10px -30px 0;
  border-bottom: none;
}

.change-row strong {
  color: #4ea87a !important;
  font-size: 18px;
}

.success-modal .modal-footer {
  padding: 20px 30px;
  gap: 15px;
}

.success-modal .btn-secondary,
.success-modal .btn-primary {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  font-size: 16px;
}

/* Animations */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error text */
.error-text {
  color: #dc3545;
  font-size: 13px;
  display: block;
  margin-top: 6px;
}

/* Discount styling */
.summary-row.discount {
  color: #4ea87a;
}

.discount-amount {
  font-weight: 600;
}

/* Form Input */
.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.form-input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #6f42c1;
  box-shadow: 0 0 0 3px rgba(111, 66, 193, 0.1);
}

.form-input:disabled {
  background: #e9ecef;
  cursor: not-allowed;
}

/* Additional Customer & Points Styles */
.customer-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.customer-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #2d3748;
}

.customer-search {
  display: flex;
  gap: 0.5rem;
}

.customer-info-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
}

.customer-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.customer-details h5 {
  margin: 0 0 0.25rem 0;
  font-size: 16px;
  font-weight: 600;
}

.customer-username {
  margin: 0;
  font-size: 14px;
  color: #6c757d;
}

.loyalty-points-display {
  background: white;
  border-radius: 6px;
  padding: 0.75rem;
  margin-bottom: 1rem;
}

.points-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.points-label {
  font-size: 13px;
  color: #6c757d;
}

.points-value {
  font-size: 18px;
  font-weight: 700;
  color: #6f42c1;
}

.points-cash {
  font-size: 13px;
  color: #6c757d;
}

/* Points Action Buttons */
.points-action-buttons {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.points-action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: white;
  border: 2px solid #dee2e6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.points-action-btn:hover {
  border-color: #6f42c1;
}

.points-action-btn.active {
  background: linear-gradient(135deg, #6f42c1, #8b5ede);
  border-color: #6f42c1;
  color: white;
}

.action-icon {
  font-size: 20px;
}

.action-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.action-title {
  font-size: 13px;
  font-weight: 600;
}

.action-subtitle {
  font-size: 11px;
  opacity: 0.8;
}

.points-insufficient-notice {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem;
  background: #fff3cd;
  border: 2px dashed #ffc107;
  border-radius: 8px;
  font-size: 12px;
}

/* Points Redemption Panel */
.points-redemption-panel {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.redemption-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.redemption-header h6 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.btn-text {
  background: none;
  border: none;
  color: #6f42c1;
  cursor: pointer;
  font-size: 13px;
}

.redemption-input-group {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.points-input {
  flex: 1;
}

.redemption-info-box {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 0.75rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 0.25rem 0;
}

.info-row .highlight {
  color: #6f42c1;
  font-weight: 600;
}

/* Points Earning Panel */
.points-earning-panel {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 193, 7, 0.1));
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.earning-preview {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.earning-icon-large {
  font-size: 40px;
}

.earning-info-large h6 {
  margin: 0 0 0.25rem 0;
  font-size: 12px;
  text-transform: uppercase;
  color: #6c757d;
}

.earning-amount-large {
  font-size: 24px;
  font-weight: 700;
  color: #FFD700;
}

.earning-value-large {
  font-size: 13px;
  color: #6c757d;
}

.balance-preview-box {
  background: white;
  border-radius: 6px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}

.balance-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 0.25rem 0;
}

.balance-row.balance-after {
  border-top: 1px solid #e9ecef;
  padding-top: 0.5rem;
  margin-top: 0.5rem;
  font-weight: 600;
}

.highlight-green {
  color: #4ea87a;
}

.earning-note {
  text-align: center;
  font-size: 11px;
  color: #6c757d;
}

/* Applied Discount Badge */
.applied-discount-badge {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #4CAF50, #45a049);
  border-radius: 8px;
  padding: 0.75rem;
  margin-top: 1rem;
}

.discount-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: white;
}

.discount-icon {
  font-size: 20px;
}

.discount-info {
  display: flex;
  flex-direction: column;
}

.discount-label {
  font-size: 11px;
  text-transform: uppercase;
  opacity: 0.9;
}

.discount-details {
  font-size: 14px;
  font-weight: 600;
}

.btn-remove-discount {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
}

/* Promotion Section */
.promotion-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.promotion-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #2d3748;
}

.promotion-card {
  background: linear-gradient(135deg, #FFD700, #FFA500);
  border-radius: 8px;
  padding: 1rem;
}

.promotion-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.promotion-icon {
  font-size: 24px;
}

.promotion-info {
  display: flex;
  flex-direction: column;
}

.promotion-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.promotion-savings {
  font-size: 18px;
  font-weight: 700;
  color: #228B22;
}

/* Discount Rows */
.discount-row {
  color: #4ea87a;
}

.discount-amount {
  font-weight: 600;
}

.alert {
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 13px;
  margin-top: 0.5rem;
}

.alert-danger {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.btn-remove {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
}

.btn-remove:hover {
  background: #ffe6e6;
}
</style>