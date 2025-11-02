<template>
  <div class="d-flex gap-3 p-3 page-container" style="height: 100%; max-height: 100vh; overflow: hidden;">
    <!-- Loading Overlay -->
    <div v-if="isLoading" class="loading-overlay position-fixed top-0 start-0 end-0 bottom-0 d-flex flex-column align-items-center justify-content-center" style="background: rgba(255, 255, 255, 0.95); z-index: 9999;">
      <div class="spinner-border text-primary mb-3" role="status" style="width: 60px; height: 60px;">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="text-secondary fw-medium fs-5">{{ loadingMessage }}</p>
    </div>

    <div class="flex-fill surface-primary shadow-sm rounded-4 d-flex flex-column" style="min-height: 0; overflow: hidden;">
      <div class="d-flex align-items-center gap-3 p-4 border-bottom-theme flex-shrink-0">
        <button @click="goBack" class="btn btn-light rounded-3 p-2 hover-surface transition-theme" :disabled="isProcessing">
          <ChevronLeft :size="20"/>
        </button>
        <h1 class="m-0 fs-2 text-primary fw-semibold">Checkout</h1>
        <button class="btn btn-light rounded-3 p-2 ms-auto text-danger hover-lift transition-theme" @click="clearCart" :disabled="isProcessing">
          <Trash2 :size="25"/>
        </button>
      </div>

      <div class="p-4 overflow-auto flex-fill" style="min-height: 0;">
        <!-- Empty Cart State -->
        <div v-if="cartItems.length === 0" class="d-flex flex-column align-items-center justify-content-center text-center p-5 text-secondary">
          <div class="fs-1 mb-3" style="opacity: 0.6;">🛒</div>
          <h3 class="fs-4 mb-2 text-primary">Your cart is empty</h3>
          <p class="fs-6 mb-4">Add some items to get started!</p>
          <button @click="goBack" class="btn btn-primary px-4 py-2 rounded-3 fw-semibold">
            Continue Shopping
          </button>
        </div>

        <!-- Cart Items -->
        <div v-else class="d-flex flex-column gap-3">
          <div class="card-theme hover-lift transition-theme d-flex align-items-start gap-3 p-3 rounded-3" v-for="item in cartItems" :key="item.id">
            <div class="rounded-3 overflow-hidden border border-secondary" style="width: 80px; height: 80px; flex-shrink: 0;">
              <img :src="item.image" :alt="item.name" loading="lazy" class="w-100 h-100" style="object-fit: cover;" />
            </div>

            <div class="flex-fill">
              <h3 class="fs-5 fw-semibold mb-1 text-primary">{{ item.productName }}</h3>
              <p class="fs-6 text-secondary mb-2">SKU: {{ item.sku }}</p>
              <div class="fs-6 text-accent fw-medium">₱{{ formatPrice(item.price) }} each</div>
            </div>

            <div class="d-flex flex-column align-items-end gap-2">
              <div class="d-flex align-items-center gap-2 surface-primary border border-secondary rounded-pill p-1">
                <button
                  class="btn btn-sm btn-secondary rounded-circle p-0 d-flex align-items-center justify-content-center"
                  style="width: 32px; height: 32px;"
                  @click="decreaseQuantity(item)"
                  :disabled="item.quantity <= 1 || quantityUpdating"
                >
                  <Minus :size="16" />
                </button>
                <span class="fw-semibold text-primary px-2" style="min-width: 30px; text-align: center;">{{ item.quantity }}</span>
                <button
                  class="btn btn-sm btn-primary rounded-circle p-0 d-flex align-items-center justify-content-center"
                  style="width: 32px; height: 32px;"
                  @click="increaseQuantity(item)"
                  :disabled="quantityUpdating"
                >
                  <Plus :size="16" />
                </button>
              </div>

              <div class="fs-5 fw-bold text-primary">
                ₱{{ formatPrice(item.subtotal) }}
              </div>

              <button
                class="btn btn-link text-danger p-1 rounded-2 hover-lift transition-theme"
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


    <div class="surface-primary shadow-sm rounded-4 p-4 d-flex flex-column" style="width: 400px; min-height: 0; max-height: 100%; overflow-y: auto;">
      <div class="d-flex flex-column flex-fill">
        <h2 class="mb-4 fs-4 text-primary fw-semibold">Order Summary</h2>

        <!-- Customer Section -->
        <div class="mb-4 pb-4 border-bottom-theme">
          <h3 class="fs-6 fw-semibold mb-3 text-primary">Customer (Optional)</h3>

          <!-- Customer Search -->
          <div v-if="!selectedCustomer" class="d-flex gap-2">
            <input
              type="text"
              class="form-control input-theme rounded-3"
              placeholder="Enter email or username"
              v-model="customerSearchQuery"
              @keyup.enter="searchCustomer"
              :disabled="isProcessing"
            />
            <button
              class="btn btn-primary btn-sm rounded-3"
              @click="searchCustomer"
              :disabled="customerSearching || !customerSearchQuery.trim() || isProcessing"
            >
              {{ customerSearching ? 'Searching...' : 'Search' }}
            </button>
          </div>

          <!-- Customer Found -->
          <div v-if="selectedCustomer" class="surface-secondary rounded-3 p-3">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div>
                <h5 class="fs-6 fw-semibold mb-1">{{ selectedCustomer.full_name }}</h5>
                <p class="fs-6 text-secondary mb-1">@{{ selectedCustomer.username }}</p>
                <p v-if="selectedCustomer.email" class="fs-6 text-secondary mb-0">{{ selectedCustomer.email }}</p>
              </div>
              <button class="btn btn-link text-danger p-1 rounded-2" @click="clearCustomer" :disabled="isProcessing">
                <X :size="16" />
              </button>
            </div>

            <!-- Loyalty Points Display -->
            <div class="surface-primary rounded-3 p-2 mb-3">
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <span class="fs-7 text-secondary">Available Points:</span>
                <span class="fs-5 fw-bold text-accent">{{ selectedCustomer.loyalty_points || 0 }} pts</span>
                <span class="fs-7 text-secondary">(₱{{ formatPrice((selectedCustomer.loyalty_points || 0) / 4) }})</span>
              </div>
            </div>

            <!-- Points Action Buttons -->
            <div class="d-flex gap-2 mb-3">
              <button
                :class="pointsMode === 'earn' ? 'btn btn-primary flex-fill d-flex align-items-center gap-2 p-2 rounded-3' : 'btn btn-outline-secondary flex-fill d-flex align-items-center gap-2 p-2 rounded-3'"
                @click="setPointsMode('earn')"
                type="button"
                :disabled="isProcessing"
              >
                <div class="fs-5">✨</div>
                <div class="d-flex flex-column align-items-start flex-fill">
                  <span class="fs-7 fw-semibold">Earn Points</span>
                  <span class="fs-8" style="opacity: 0.8;">+{{ pointsWillEarn }} pts</span>
                </div>
              </button>

              <button
                v-if="selectedCustomer.loyalty_points >= 100"
                :class="pointsMode === 'use' ? 'btn btn-primary flex-fill d-flex align-items-center gap-2 p-2 rounded-3' : 'btn btn-outline-secondary flex-fill d-flex align-items-center gap-2 p-2 rounded-3'"
                @click="setPointsMode('use')"
                type="button"
                :disabled="isProcessing"
              >
                <div class="fs-5">🎁</div>
                <div class="d-flex flex-column align-items-start flex-fill">
                 <span class="fs-8" style="opacity: 0.8;">
                    Up to {{ maxRedeemablePoints }} pts (₱{{ formatPrice(maxRedeemablePoints / 4) }})
                  </span>

                </div>
              </button>

              <div v-else class="flex-fill d-flex align-items-center justify-content-center p-2 status-warning rounded-3 border-2 border-dashed">
                <small>💡 Need 100+ points to redeem</small>
              </div>
            </div>

            <!-- Points Redemption Panel -->
            <div v-if="pointsMode === 'use' && selectedCustomer.loyalty_points >= 40" class="points-redemption-panel">
              <div class="redemption-header">
                <h6>Redeem Points</h6>
                <button class="btn-text" @click="setPointsMode('earn')" :disabled="isProcessing">Cancel</button>
              </div>
              
              <div class="redemption-input-group">
                <input 
                  type="number" 
                  class="form-control points-input" 
                  placeholder="Enter points amount"
                  v-model.number="pointsToRedeem"
                  :max="Math.min(selectedCustomer.loyalty_points, maxRedeemablePoints)"
                  min="40"
                  step="20"
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
              
              <div class="redemption-info-box">
                <div class="info-row">
                  <span>Minimum:</span>
                  <span>40 pts (₱10)</span>
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
        <div v-if="appliedPromotion" class="mb-4 pb-4 border-bottom-theme">
          <h3 class="fs-6 fw-semibold mb-3 text-primary">Applied Promotion</h3>
          <div class="rounded-3 p-3" style="background: linear-gradient(135deg, #FFD700, #FFA500);">
            <div class="d-flex align-items-center gap-3">
              <span class="fs-4">🎉</span>
              <div class="d-flex flex-column flex-fill">
                <span class="fs-6 fw-semibold text-dark">{{ appliedPromotion.name }}</span>
                <span class="fs-5 fw-bold text-success">Save ₱{{ formatPrice(promoDiscount) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Summary -->
        <div class="surface-secondary rounded-3 p-3 mb-4">
          <div class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary">
            <span class="text-secondary">Subtotal:</span>
            <span class="text-primary">₱{{ formatPrice(cartSubtotal) }}</span>
          </div>

          <div v-if="promoDiscount > 0" class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary text-success">
            <span>{{ appliedPromotion.name }}</span>
            <span class="fw-semibold">-₱{{ formatPrice(promoDiscount) }}</span>
          </div>

          <div v-if="appliedPointsDiscount > 0" class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary text-success">
            <span>Points Discount</span>
            <span class="fw-semibold">-₱{{ formatPrice(appliedPointsDiscount) }}</span>
          </div>

          <div class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary">
            <span class="text-secondary">Tax (12%):</span>
            <span class="text-primary">₱{{ formatPrice(taxAmount) }}</span>
          </div>

          <div class="d-flex justify-content-between align-items-center pt-3 fw-bold fs-5">
            <strong class="text-primary">TOTAL:</strong>
            <strong class="text-primary">₱{{ formatPrice(grandTotal) }}</strong>
          </div>
        </div>
        
        <!-- Payment Method Selection -->
        <div class="mb-4">
          <h3 class="fs-6 fw-semibold mb-3 text-primary">Payment Method</h3>
          <div class="d-flex flex-column gap-2">
            <label class="d-flex align-items-center cursor-pointer p-3 rounded-3 border border-theme hover-surface transition-theme">
              <input
                type="radio"
                name="payment"
                value="cash"
                v-model="paymentMethod"
                :disabled="isProcessing"
                class="me-3"
                style="accent-color: var(--primary);"
              >
              <span class="fs-6 text-primary">💵 Cash</span>
            </label>

            <label class="d-flex align-items-center cursor-pointer p-3 rounded-3 border border-theme hover-surface transition-theme">
              <input
                type="radio"
                name="payment"
                value="gcash"
                v-model="paymentMethod"
                :disabled="isProcessing"
                class="me-3"
                style="accent-color: var(--primary);"
              >
              <span class="fs-6 text-primary">📱 GCash</span>
            </label>

            <label class="d-flex align-items-center cursor-pointer p-3 rounded-3 border border-theme hover-surface transition-theme">
              <input
                type="radio"
                name="payment"
                value="paymaya"
                v-model="paymentMethod"
                :disabled="isProcessing"
                class="me-3"
                style="accent-color: var(--primary);"
              >
              <span class="fs-6 text-primary">💳 Maya (PayMaya)</span>
            </label>
          </div>
        </div>

        <!-- Cash Payment Details -->
        <div v-if="paymentMethod === 'cash'" class="mt-3 p-3 surface-secondary rounded-3">
          <div class="mb-3">
            <label class="form-label fw-semibold text-primary mb-2">Cash Tendered</label>
            <div class="input-with-currency">
              <span class="currency-symbol text-primary">₱</span>
              <input
                type="number"
                v-model.number="cashTendered"
                placeholder="0.00"
                step="0.01"
                min="0"
                class="form-control input-theme rounded-3 fw-semibold fs-5"
                :disabled="isProcessing"
                @input="validateCashPayment"
              />
            </div>
            <small v-if="cashValidationError" class="d-block mt-2 text-danger fs-7">
              {{ cashValidationError }}
            </small>
          </div>

          <div v-if="changeAmount >= 0 && cashTendered > 0" class="d-flex justify-content-between align-items-center p-3 surface-primary rounded-3 border-2 border-success">
            <span class="text-secondary">Change</span>
            <span class="fs-4 fw-bold text-success">₱{{ formatPrice(changeAmount) }}</span>
          </div>
        </div>
        
        <!-- GCash Payment Info -->
        <div v-else-if="paymentMethod === 'gcash'" class="mt-3">
          <div class="surface-secondary rounded-3 p-3 text-center">
            <div class="fs-3 mb-2">📱</div>
            <h4 class="fs-6 fw-semibold mb-1 text-primary">GCash Payment</h4>
            <p class="text-secondary fs-7 mb-0">You will be redirected to GCash to complete your payment securely.</p>
          </div>
        </div>

        <!-- Maya Payment Info -->
        <div v-else-if="paymentMethod === 'paymaya'" class="mt-3">
          <div class="surface-secondary rounded-3 p-3 text-center">
            <div class="fs-3 mb-2">💳</div>
            <h4 class="fs-6 fw-semibold mb-1 text-primary">Maya (PayMaya) Payment</h4>
            <p class="text-secondary fs-7 mb-0">You will be redirected to Maya to complete your payment securely.</p>
          </div>
        </div>

        <!-- Place Order Button -->
        <button
          class="btn btn-primary w-100 py-3 rounded-3 fs-5 fw-semibold mt-auto hover-lift transition-theme"
          @click="placeOrder"
          :disabled="!canPlaceOrder"
        >
          <span v-if="!isProcessing">
            <span v-if="paymentMethod === 'cash'">Complete Cash Payment</span>
            <span v-else-if="paymentMethod === 'gcash'">Pay with GCash →</span>
            <span v-else-if="paymentMethod === 'paymaya'">Pay with Maya →</span>
            <span v-else>Place Order</span>
            - ₱{{ formatPrice(grandTotal) }}
          </span>
          <span v-else class="d-flex align-items-center justify-content-center gap-2">
            <span v-if="paymentMethod === 'cash'">Processing...</span>
            <span v-else>Redirecting to payment...</span>
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
          </span>
        </button>
      </div>
    </div>
    
    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="position-fixed top-0 start-0 end-0 bottom-0 d-flex align-items-center justify-content-center modal-overlay-theme" style="z-index: 10000;" @click="closeSuccessModal">
      <div class="modal-theme rounded-4 overflow-hidden success-modal" style="max-width: 500px; width: 90%;" @click.stop>
        <div class="text-center p-5 text-white position-relative" style="background: linear-gradient(135deg, #4ea87a 0%, #5eb488 100%);">
          <div class="d-flex align-items-center justify-content-center mx-auto mb-3 bg-white text-success rounded-circle shadow-lg" style="width: 80px; height: 80px; font-size: 48px; font-weight: bold; color: green;">
            ✓
          </div>
          <h3 class="fs-4 mb-0">Order Completed!</h3>
          <button class="btn btn-link text-white position-absolute top-0 end-0 m-3 p-2 rounded-circle" style="background: rgba(255, 255, 255, 0.2);" @click="closeSuccessModal">
            <X :size="20" />
          </button>
        </div>
        <div class="p-4">
          <div>
            <div class="d-flex justify-content-between py-3 border-bottom border-secondary">
              <span class="text-secondary">Sale ID:</span>
              <strong class="text-primary fw-semibold">{{ completedSale.saleId }}</strong>
            </div>
            <div class="d-flex justify-content-between py-3 border-bottom border-secondary">
              <span class="text-secondary">Date:</span>
              <strong class="text-primary fw-semibold">{{ formatDateTime(completedSale.transactionDate) }}</strong>
            </div>
            <div class="d-flex justify-content-between py-3 border-bottom border-secondary">
              <span class="text-secondary">Total Amount:</span>
              <strong class="text-success fw-bold fs-5">₱{{ formatPrice(completedSale.totalAmount) }}</strong>
            </div>
            <div class="d-flex justify-content-between py-3 border-bottom border-secondary">
              <span class="text-secondary">Payment Method:</span>
              <strong class="text-primary fw-semibold">{{ completedSale.paymentMethod.toUpperCase() }}</strong>
            </div>
            <div v-if="completedSale.shiftId" class="d-flex justify-content-between py-3 border-bottom border-secondary">
              <span class="text-secondary">Shift ID:</span>
              <strong class="text-primary fw-semibold">{{ completedSale.shiftId }}</strong>
            </div>
            <div v-if="completedSale.change > 0" class="d-flex justify-content-between py-3 surface-secondary rounded-3 px-3 mt-3">
              <span class="text-secondary">Change:</span>
              <strong class="text-success fw-bold fs-5">₱{{ formatPrice(completedSale.change) }}</strong>
            </div>
          </div>
        </div>
        <div class="d-flex gap-3 p-4 border-top border-secondary">
          <button class="btn btn-outline-secondary flex-fill d-flex align-items-center justify-content-center gap-2 py-3 rounded-3" @click="printReceipt">
            <Printer :size="18" /> Print Receipt
          </button>
          <button class="btn btn-primary flex-fill py-3 rounded-3 fw-semibold" @click="startNewOrder">
            New Order
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useCartStore } from '@/stores/cartStores'
import { usePaymongo } from '@/composables/api/usePaymongo'
import apiSales from '@/services/apiSales'
import apiProducts from '@/services/apiProducts'
import { api } from '@/services/api.js'
import { useStockCache } from '@/composables/data/useStockCache.js'

export default {
  name: 'Checkout',
  
  setup() {
    const cartStore = useCartStore()
    const paymongo = usePaymongo()
    const stockCache = useStockCache()
    
    return { 
      cartStore,
      paymongo,
      stockCache
    }
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
      paymentMethod: 'cash', // 'cash', 'gcash', 'paymaya'
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
    
    promoDiscount() {
      if (!this.appliedPromotion) {
        return 0
      }
      
      const promotion = this.appliedPromotion
      
      // SAFETY CHECK
      if (!promotion.discount_config) {
        return 0
      }
      
      const targetType = promotion.discount_config.target_type
      const targetIds = promotion.discount_config.target_ids || []
      
      let eligibleAmount = 0
      
      if (targetType === 'all') {
        eligibleAmount = this.cartSubtotal
        
      } else if (targetType === 'categories') {
        // Filter cart items by category
        const eligibleItems = this.cartItems.filter(item => {
          const product = this.products.find(p => p.id === item.productId)
          
          if (!product) {
            return false
          }
          
          const productCategory = product.category
          const isEligible = targetIds.includes(productCategory)
          
          return isEligible
        })
        
        eligibleAmount = eligibleItems.reduce((sum, item) => sum + item.subtotal, 0)
        
      } else if (targetType === 'products') {
        // Filter cart items by product ID
        const eligibleItems = this.cartItems.filter(item => {
          const isEligible = targetIds.includes(item.productId)
          
          return isEligible
        })
        
        eligibleAmount = eligibleItems.reduce((sum, item) => sum + item.subtotal, 0)
      }
      
      if (eligibleAmount === 0) {
        return 0
      }
      
      // Calculate discount
      let discount = 0
      
      if (promotion.type === 'percentage') {
        discount = eligibleAmount * (promotion.discount_value / 100)
      } else if (promotion.type === 'fixed') {
        discount = Math.min(promotion.discount_value, eligibleAmount)
      }
      
      const finalDiscount = Math.round(discount * 100) / 100
      
      return finalDiscount
    },
    
    subtotalAfterPromo() {
      return Math.max(0, this.cartSubtotal - this.promoDiscount)
    },
    
    taxAmount() {
      const taxableAmount = this.subtotalAfterPromo - this.appliedPointsDiscount
      return Math.round(taxableAmount * 0.12 * 100) / 100
    },
    
    grandTotal() {
      return Math.max(0, this.subtotalAfterPromo - this.appliedPointsDiscount + this.taxAmount)
    },
    
    totalItems() {
      return this.cartStore.itemCount
    },
    
    // Points calculations
    maxRedeemablePoints() {
      if (!this.selectedCustomer) return 0

      // 4 points = ₱1
      const pointsPerPeso = 4

      // Calculate subtotal after promotion discounts
      const subtotalAfterPromo = Math.max(0, this.cartSubtotal - this.promoDiscount)

      // Dynamic cap: max 20% of subtotalAfterPromo
      const maxDiscountAmount = subtotalAfterPromo * 0.20

      // Convert peso value to equivalent points
      const maxPointsFromSubtotal = Math.floor(maxDiscountAmount * pointsPerPeso)

      // Limit by customer’s actual points
      const customerPoints = this.selectedCustomer.loyalty_points || 0

      // Final allowed redemption
      return Math.min(maxPointsFromSubtotal, customerPoints)
    },

    
    canRedeemPoints() {
      if (!this.pointsToRedeem || !this.selectedCustomer) return false
      // Minimum ₱10 = 40 points
      if (this.pointsToRedeem < 40) return false
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
      
      if (this.paymentMethod === 'gcash' || this.paymentMethod === 'paymaya') {
        return true // Just need cart with items
      }
      
      return false
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
        
        if (promoData) {
          try {
            const parsedPromo = JSON.parse(promoData)
            
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
              } catch (e) {
                // Failed to parse discount_config
              }
            }
            
            // ✅ VERIFY: Ensure all required fields exist
            if (!promotion._id || !promotion.name || !promotion.type || !promotion.discount_value) {
              this.appliedPromotion = null
            } else {
              this.appliedPromotion = promotion
            }
            
          } catch (error) {
            this.appliedPromotion = null
          }
        }
        
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
          
        }
        
      } catch (error) {
        // Failed to load checkout data
      } finally {
        this.isLoading = false
      }
    },
    
    // ✅ NEW METHOD: Load products for promotion calculation
    async loadProductsForPromotion() {
      try {
        if (this.cartItems.length === 0) {
          return
        }
        
        // Get all unique product IDs from cart
        const productIds = [...new Set(this.cartItems.map(item => item.productId))]
        
        // Fetch products in batch
        const products = await apiProducts.getProductsBatch(productIds)
        
        // Store products in data for promotion calculation
        this.products = products
        
      } catch (error) {
        // Failed to load products
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
        
        const response = await api.get('/customers/', {
          params: { search: query }
        })
        
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
        
        if (customers && customers.length > 0) {
          const customer = customers.find(c => 
            c.username?.toLowerCase() === query ||
            c.email?.toLowerCase() === query ||
            c._id?.toLowerCase() === query
          )
          
          if (!customer) {
            this.customerSearchError = 'Customer not found. Please check the username/email.'
            return
          }
          
        this.selectedCustomer = {
          _id: customer._id,
          username: customer.username,
          full_name: customer.full_name,
          email: customer.email,
          phone: customer.phone,
          loyalty_points: customer.loyalty_points || 0
        }
        
        this.customerSearchQuery = ''
        
      } else {
        this.customerSearchError = 'Customer not found. Please check the username/email.'
      }
      
    } catch (error) {
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
      // Enforce absolute max ₱20 at apply time as well
      if (discount > 20) {
        alert('Maximum points discount per transaction is ₱20')
        return
      }
      
      if (discount > this.subtotalAfterPromo) {
        alert('Points discount cannot exceed cart total')
        return
      }
      
      this.pointsRedeemed = this.pointsToRedeem
      this.appliedPointsDiscount = discount
      this.pointsToRedeem = 0
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
    // PAYMENT PROCESSING
    // ================================================================
    
    async placeOrder() {
      if (!this.canPlaceOrder) {
        alert('Please complete payment details before placing order.')
        return
      }
      
      // Route to appropriate payment method
      if (this.paymentMethod === 'cash') {
        await this.processCashPayment()
      } else if (this.paymentMethod === 'gcash') {
        await this.processEWalletPayment('gcash')
      } else if (this.paymentMethod === 'paymaya') {
        await this.processEWalletPayment('grab_pay') // PayMongo uses 'grab_pay' for Maya
      }
    },
    
    // ----------------------------------------------------------------
    // CASH PAYMENT
    // ----------------------------------------------------------------
    
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
    
    async processCashPayment() {
      if (!this.validateCashPayment()) return
      
      const confirmMessage = `Confirm cash payment:\nTotal: ₱${this.formatPrice(this.grandTotal)}\n` +
        `Cash: ₱${this.formatPrice(this.cashTendered)}\nChange: ₱${this.formatPrice(this.changeAmount)}`
      
      if (!confirm(confirmMessage)) return
      
      try {
        this.isProcessing = true
        this.isLoading = true
        this.loadingMessage = 'Processing cash payment...'
        
        await this.validateStock()
        
        if (this.validationErrors.length > 0) {
          throw new Error('Stock validation failed')
        }
        
        const saleData = this.prepareSaleData('cash', {
          method: 'cash',
          amount_paid: this.cashTendered,
          change: this.changeAmount,
          status: 'completed',
          transaction_id: `CASH-${Date.now()}`,
          timestamp: new Date().toISOString()
        })
        
        const result = await apiSales.createSale(saleData)
        
        this.handleSaleSuccess(result, 'cash')
        
      } catch (error) {
        alert(`Payment failed: ${error.message}`)
      } finally {
        this.isProcessing = false
        this.isLoading = false
      }
    },
    
    // ----------------------------------------------------------------
    // QR PH PAYMENT (GCash/Maya via PayMongo)
    // ----------------------------------------------------------------
    
    async processEWalletPayment(type) {
      const walletName = type === 'gcash' ? 'GCash' : 'Maya'
      
      const confirmMessage = `Confirm ${walletName} payment:\nTotal: ₱${this.formatPrice(this.grandTotal)}\n\n` +
        `You will be redirected to ${walletName} to complete payment.`
      
      if (!confirm(confirmMessage)) return
      
      try {
        this.isProcessing = true
        this.isLoading = true
        this.loadingMessage = `Creating ${walletName} payment link...`
        
        await this.validateStock()
        
        if (this.validationErrors.length > 0) {
          throw new Error('Stock validation failed')
        }
        
        // Prepare order metadata (PayMongo requires all string values)
        const orderMetadata = {
          order_id: `ORDER-${Date.now()}`,
          customer_id: String(this.selectedCustomer?._id || 'guest'),
          customer_name: String(this.selectedCustomer?.full_name || 'Guest'),
          cashier_id: String(this.cartStore.cashierId || 'unknown'),
          shift_id: String(this.cartStore.shiftId || 'unknown'),
          items_count: String(this.totalItems),
          description: `Ramyeon Food Corner - ${this.totalItems} items`
        }
        
        // Create PayMongo source
        const source = await this.paymongo.createEWalletSource(
          this.grandTotal,
          type, // 'gcash' or 'grab_pay'
          {
            successUrl: `${window.location.origin}/pos/payment-callback?status=success`,
            failedUrl: `${window.location.origin}/pos/payment-callback?status=failed`,
            metadata: orderMetadata
          }
        )
        
        // Save pending transaction to sessionStorage
        const pendingPayment = {
          source_id: source.id,
          payment_type: type,
          wallet_name: walletName,
          amount: this.grandTotal,
          subtotal: this.cartSubtotal,
          tax: this.taxAmount,
          promo_discount: this.promoDiscount,
          points_discount: this.appliedPointsDiscount,
          cart_items: this.cartStore.items,
          promotion: this.appliedPromotion,
          customer: this.selectedCustomer,
          points_redeemed: this.pointsRedeemed,
          points_to_earn: this.pointsWillEarn,
          cashier_id: this.cartStore.cashierId,
          shift_id: this.cartStore.shiftId,
          timestamp: new Date().toISOString(),
          metadata: orderMetadata
        }
        
        sessionStorage.setItem('pendingEWalletPayment', JSON.stringify(pendingPayment))
        
        // Redirect to GCash/Maya
        this.loadingMessage = `Redirecting to ${walletName}...`
        
        setTimeout(() => {
          window.location.href = source.attributes.redirect.checkout_url
        }, 500)
        
      } catch (error) {
        alert(`${walletName} payment failed: ${error.message}`)
        this.isProcessing = false
        this.isLoading = false
      }
    },
    
    // ----------------------------------------------------------------
    // HELPER: PREPARE SALE DATA
    // ----------------------------------------------------------------
    
    prepareSaleData(paymentMethod, paymentDetails) {
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
      saleData.payment_method = paymentMethod
      saleData.payment_details = paymentDetails
      
      return saleData
    },
    
    // ----------------------------------------------------------------
    // HELPER: HANDLE SALE SUCCESS
    // ----------------------------------------------------------------
    
    handleSaleSuccess(result, paymentMethod) {
      // Calculate final change (from previous version)
      const backendChange = result?.payment_details?.change
      const snapshotChange = Math.max(0, (this.cashTendered || 0) - (result?.total_amount ?? this.grandTotal))
      const finalChange = paymentMethod === 'cash' 
        ? (typeof backendChange === 'number' ? backendChange : snapshotChange)
        : 0

      // Update stock cache with sold items
      try {
        this.stockCache.updateStockAfterSale(this.cartItems)
      } catch (error) {
        // Don't block success flow if cache update fails
      }
      
      // Signal NewOrder to perform targeted stock refresh on return
      try {
        const affectedIds = (this.cartItems || []).map(i => i.productId).filter(Boolean)
        if (affectedIds.length > 0) {
          sessionStorage.setItem('refreshProductIds', JSON.stringify(affectedIds))
        }
        sessionStorage.setItem('refreshStockAfterCheckout', 'true')
      } catch (_) {}
      
      this.cartStore.clearCart()
      sessionStorage.removeItem('appliedPromotion')
      sessionStorage.removeItem('checkoutCustomer')

      // Normalize transaction date: if backend didn't include timezone, assume UTC
      let transactionDateRaw = result.transaction_date_local || result.transaction_date
      if (typeof transactionDateRaw === 'string') {
        const hasTz = /Z$|[zZ]$|[+-]\d{2}:?\d{2}$/.test(transactionDateRaw)
        if (!hasTz) {
          transactionDateRaw = transactionDateRaw + 'Z'
        }
      }

      this.completedSale = {
        saleId: result._id || result.sale_id,
        transactionDate: result.payment_details?.timestamp || transactionDateRaw,
        totalAmount: result.total_amount,
        paymentMethod: paymentMethod,
        change: finalChange,
        shiftId: result.shift_id || this.cartStore.shiftId
      }
      
      this.showSuccessModal = true
    },
    
    // ================================================================
    // SUCCESS MODAL & RECEIPT
    // ================================================================
    
     async printReceipt() {
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
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
        alert(`Failed to print receipt: ${error.message}`)
      }
    },
    
    closeSuccessModal() {
      this.showSuccessModal = false
      this.startNewOrder()
    },
    
    startNewOrder() {
      this.cashTendered = 0
      this.paymentMethod = 'cash'
      
      // Signal NewOrder to refresh stock after transaction
      sessionStorage.setItem('refreshStockAfterCheckout', 'true')
      
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
      const source = new Date(dateString)
      try {
        const datePart = source.toLocaleDateString('en-US', {
          month: 'long',
          day: 'numeric',
          year: 'numeric',
          timeZone: 'Asia/Manila'
        })
        // Use 24-hour time like currentDateTime() from your snippet, forced to PH time
        const timePart = source.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
          timeZone: 'Asia/Manila'
        })
        return `${datePart} ${timePart}`
      } catch (error) {
        return source.toString()
      }
    }
  }
}
</script>

<style scoped>
/* Only truly custom styles that can't be replaced with semantic classes */

/* Inline currency symbol for payment inputs */
.input-with-currency {
  position: relative;
}

.currency-symbol {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  font-weight: 600;
  pointer-events: none;
}

.input-with-currency input {
  padding-left: 40px;
}

/* Removed payment flow steps styling - no longer needed */

/* Custom animations for success modal */
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.success-modal {
  animation: fadeIn 0.3s ease-out;
}
</style>