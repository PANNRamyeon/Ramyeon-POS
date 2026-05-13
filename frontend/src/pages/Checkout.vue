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


    <div class="surface-primary shadow-sm rounded-4 p-4 d-flex flex-column" style="width: 380px; flex-shrink: 0; overflow-y: auto;">
      <div class="d-flex flex-column flex-fill">
        <h2 class="mb-2 fs-5 text-primary fw-semibold">Order Summary</h2>

        <!-- Customer Section -->
        <div class="mb-3 pb-2 border-bottom-theme">
          <h3 class="fs-6 fw-semibold mb-2 text-primary">Customer (Optional)</h3>

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
          <div v-if="selectedCustomer" class="surface-secondary rounded-3 p-2">
            <div class="d-flex justify-content-between align-items-start mb-1">
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
            <div class="surface-primary rounded-3 p-2 mb-1">
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <span class="fs-7 text-secondary">Available Points:</span>
                <span class="fs-6 fw-bold text-accent">{{ selectedCustomer.loyalty_points || 0 }} pts</span>
                <span class="fs-7 text-secondary">(₱{{ formatPrice((selectedCustomer.loyalty_points || 0) / 4) }})</span>
              </div>
            </div>

            <!-- Points Action Buttons -->
            <div class="d-flex gap-2 mb-1">
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

        <!-- Special Discounts -->
        <div class="mb-2 pb-2 border-bottom-theme">
          <h3 class="fs-6 fw-semibold mb-2 text-primary">Special Discounts</h3>
          <div class="d-flex flex-column gap-1">
            <!-- Drinks Promo Checkbox -->
            <label class="d-flex align-items-center cursor-pointer p-2 rounded-3 border border-theme hover-surface transition-theme">
              <input
                type="checkbox"
                v-model="isDrinksPromo"
                :disabled="isProcessing"
                class="me-2"
                style="accent-color: var(--primary); width: 16px; height: 16px;"
              >
              <span class="fs-7 text-primary">🥤 Drinks Promo</span>
            </label>

            <!-- PWD / Senior Citizen Discount (Single Checkbox) -->
            <label class="d-flex align-items-center cursor-pointer p-2 rounded-3 border border-theme hover-surface transition-theme">
              <input
                type="checkbox"
                v-model="isSpecialDiscount"
                :disabled="isProcessing"
                class="me-2"
                style="accent-color: var(--primary); width: 16px; height: 16px;"
              >
              <span class="fs-7 text-primary">🦽👴 PWD / Senior Citizen (20% off)</span>
            </label>
          </div>
        </div>

        <!-- Auto-Applied Promotions Display -->
        <div v-if="autoAppliedPromotions.length > 0" class="mb-2 pb-2 border-bottom-theme">
          <h3 class="fs-6 fw-semibold mb-1 text-primary">Applied Promotions</h3>
          <div v-for="promo in autoAppliedPromotions" :key="promo._id" class="mb-1">
            <div class="rounded-3 p-2" style="background: linear-gradient(135deg, #FFD700, #FFA500);">
              <div class="d-flex align-items-center gap-2">
                <span class="fs-4">🎉</span>
                <div class="d-flex flex-column flex-fill">
                  <span class="fs-6 fw-semibold text-dark">{{ promo.name }}</span>
                  <span class="fs-5 fw-bold text-success">Save ₱{{ formatPrice(promo.discountAmount) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Summary -->
        <div class="surface-secondary rounded-3 p-2 mb-2">
          <div class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary">
            <span class="fs-7 text-secondary">Subtotal:</span>
            <span class="fs-7 text-primary">₱{{ formatPrice(cartSubtotal) }}</span>
          </div>

          <!-- Auto-applied promotions -->
          <div v-for="promo in autoAppliedPromotions" :key="promo._id" class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary text-success">
            <span class="fs-7">{{ promo.name }}</span>
            <span class="fs-7 fw-semibold">-₱{{ formatPrice(promo.discountAmount) }}</span>
          </div>

          <!-- Drinks Promo Discount -->
          <div v-if="drinksPromoDiscount > 0" class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary text-success">
            <span class="fs-7">Drinks Promo</span>
            <span class="fs-7 fw-semibold">-₱{{ formatPrice(drinksPromoDiscount) }}</span>
          </div>

          <!-- PWD / Senior Citizen Discount -->
          <div v-if="specialDiscount > 0" class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary text-success">
            <span class="fs-7">PWD / Senior Citizen (20%)</span>
            <span class="fs-7 fw-semibold">-₱{{ formatPrice(specialDiscount) }}</span>
          </div>

          <!-- Points Discount -->
          <div v-if="appliedPointsDiscount > 0" class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary text-success">
            <span class="fs-7">Points Discount</span>
            <span class="fs-7 fw-semibold">-₱{{ formatPrice(appliedPointsDiscount) }}</span>
          </div>

          <div class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary">
            <span class="fs-7 text-secondary">Tax (12%):</span>
            <span class="fs-7 text-primary">₱{{ formatPrice(taxAmount) }}</span>
          </div>

          <div class="d-flex justify-content-between align-items-center pt-2 fw-bold">
            <strong class="fs-6 text-primary">TOTAL:</strong>
            <strong class="fs-6 text-primary">₱{{ formatPrice(grandTotal) }}</strong>
          </div>
        </div>
        
        <!-- Payment Method Selection -->
        <div class="mb-2">
          <h3 class="fs-6 fw-semibold mb-2 text-primary">Payment Method</h3>
          <div class="d-flex flex-column gap-1">
            <label class="d-flex align-items-center cursor-pointer p-2 rounded-3 border border-theme hover-surface transition-theme">
              <input
                type="radio"
                name="payment"
                value="cash"
                v-model="paymentMethod"
                :disabled="isProcessing"
                class="me-2"
                style="accent-color: var(--primary);"
              >
              <span class="fs-7 text-primary">💵 Cash</span>
            </label>

            <label class="d-flex align-items-center cursor-pointer p-2 rounded-3 border border-theme hover-surface transition-theme">
              <input
                type="radio"
                name="payment"
                value="gcash"
                v-model="paymentMethod"
                :disabled="isProcessing"
                class="me-2"
                style="accent-color: var(--primary);"
              >
              <span class="fs-7 text-primary">📱 GCash</span>
            </label>

            <label class="d-flex align-items-center cursor-pointer p-2 rounded-3 border border-theme hover-surface transition-theme">
              <input
                type="radio"
                name="payment"
                value="paymaya"
                v-model="paymentMethod"
                :disabled="isProcessing"
                class="me-2"
                style="accent-color: var(--primary);"
              >
              <span class="fs-7 text-primary">💳 Maya (PayMaya)</span>
            </label>
          </div>
        </div>

        <!-- Cash Payment Details -->
        <div v-if="paymentMethod === 'cash'" class="mt-2 p-2 surface-secondary rounded-3">
          <div class="mb-2">
            <label class="form-label fw-semibold text-primary mb-1 fs-7">Cash Tendered</label>

            <!-- Smart bill suggestions -->
            <div class="d-flex gap-1 flex-wrap mb-2">
              <button
                v-for="amount in cashSuggestions"
                :key="amount"
                type="button"
                class="btn btn-outline-secondary rounded-pill px-3 py-2 fw-semibold"
                style="font-size: 0.9rem;"
                :class="{ 'btn-primary text-white border-primary': cashTendered === amount }"
                @click="selectSuggestion(amount)"
                :disabled="isProcessing"
              >
                ₱{{ amount.toLocaleString() }}
              </button>
            </div>

            <div class="input-with-currency">
              <span class="currency-symbol text-primary">₱</span>
              <input
                type="number"
                v-model.number="cashTendered"
                placeholder="0.00"
                step="0.01"
                min="0"
                class="form-control input-theme rounded-3 fw-semibold"
                :disabled="isProcessing"
                @input="validateCashPayment"
              />
            </div>
            <small v-if="cashValidationError" class="d-block mt-1 text-danger fs-7">
              {{ cashValidationError }}
            </small>
          </div>

          <div v-if="changeAmount >= 0 && cashTendered > 0" class="d-flex justify-content-between align-items-center p-2 surface-primary rounded-3 border-2 border-success">
            <span class="fs-7 text-secondary">Change</span>
            <span class="fs-5 fw-bold text-success">₱{{ formatPrice(changeAmount) }}</span>
          </div>
        </div>

        <!-- GCash Payment Info -->
        <div v-else-if="paymentMethod === 'gcash'" class="mt-2">
          <div class="surface-secondary rounded-3 p-2 text-center">
            <div class="fs-4 mb-1">📱</div>
            <h4 class="fs-7 fw-semibold mb-0 text-primary">You will be redirected to GCash to complete your payment.</h4>
          </div>
        </div>

        <!-- Maya Payment Info -->
        <div v-else-if="paymentMethod === 'paymaya'" class="mt-2">
          <div class="surface-secondary rounded-3 p-2 text-center">
            <div class="fs-4 mb-1">💳</div>
            <h4 class="fs-7 fw-semibold mb-0 text-primary">You will be redirected to Maya to complete your payment.</h4>
          </div>
        </div>

        <!-- Place Order Button -->
        <button
          class="btn btn-primary w-100 py-3 rounded-3 fs-6 fw-semibold mt-auto hover-lift transition-theme"
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
          <button
            class="btn btn-primary flex-fill py-3 rounded-3 fw-semibold d-flex align-items-center justify-content-center gap-2"
            @click="startNewOrder"
            :disabled="stockSyncing"
          >
            <span v-if="stockSyncing" class="spinner-border spinner-border-sm" role="status"></span>
            {{ stockSyncing ? 'Syncing stock...' : 'New Order' }}
          </button>
        </div>
      </div>
    </div>

        <!-- Cash Payment Confirmation Modal -->
        <div v-if="showCashConfirmModal" class="modal-overlay" @click.self="cancelCashConfirm">
          <div class="modal-container cash-confirm-modal">
            <div class="modal-header">
              <h3 class="modal-title text-primary">💵 Confirm Cash Payment</h3>
            </div>
            <div class="p-4">
              <div class="payment-summary">
                <div class="summary-row">
                  <span class="summary-label">Total:</span>
                  <span class="summary-value text-primary">₱{{ formatPrice(grandTotal) }}</span>
                </div>
                <div class="summary-row">
                  <span class="summary-label">Cash:</span>
                  <span class="summary-value text-success">₱{{ formatPrice(cashTendered) }}</span>
                </div>
                <div class="summary-row change-row">
                  <span class="summary-label">Change:</span>
                  <span class="summary-value change-amount">₱{{ formatPrice(changeAmount) }}</span>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-outline-secondary" @click="cancelCashConfirm" :disabled="isProcessing">
                Cancel
              </button>
              <button class="btn btn-primary" @click="confirmCashPayment" :disabled="isProcessing">
                <span v-if="!isProcessing">Confirm Payment</span>
                <span v-else class="d-flex align-items-center gap-2">
                  Processing...
                  <span class="spinner-border spinner-border-sm" role="status"></span>
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- GCash Payment Confirmation Modal -->
        <div v-if="showGCashConfirmModal" class="modal-overlay" @click.self="cancelEWalletConfirm">
          <div class="modal-container ewallet-confirm-modal gcash-modal">
            <div class="modal-header">
              <h3 class="modal-title" style="color: #0070BA;">📱 Confirm GCash Payment</h3>
            </div>
            <div class="p-4">
              <div class="payment-summary">
                <div class="summary-row">
                  <span class="summary-label">Total:</span>
                  <span class="summary-value text-primary">₱{{ formatPrice(grandTotal) }}</span>
                </div>
              </div>
              <div class="ewallet-info-box">
                <div class="ewallet-icon">📱</div>
                <div class="ewallet-message">
                  <p class="mb-2">You will be redirected to <strong>GCash</strong> to complete your payment securely.</p>
                  <p class="text-secondary fs-7 mb-0">Make sure you have the GCash app or access to the GCash website ready.</p>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-outline-secondary" @click="cancelEWalletConfirm" :disabled="isProcessing">
                Cancel
              </button>
              <button class="btn btn-primary" style="background-color: #0070BA; border-color: #0070BA;" @click="confirmEWalletPayment('gcash')" :disabled="isProcessing">
                <span v-if="!isProcessing">Continue to GCash →</span>
                <span v-else class="d-flex align-items-center gap-2">
                  Creating payment link...
                  <span class="spinner-border spinner-border-sm" role="status"></span>
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- PayMaya Payment Confirmation Modal -->
        <div v-if="showPayMayaConfirmModal" class="modal-overlay" @click.self="cancelEWalletConfirm">
          <div class="modal-container ewallet-confirm-modal paymaya-modal">
            <div class="modal-header">
              <h3 class="modal-title" style="color: #00AFEF;">💳 Confirm Maya Payment</h3>
            </div>
            <div class="p-4">
              <div class="payment-summary">
                <div class="summary-row">
                  <span class="summary-label">Total:</span>
                  <span class="summary-value text-primary">₱{{ formatPrice(grandTotal) }}</span>
                </div>
              </div>
              <div class="ewallet-info-box">
                <div class="ewallet-icon">💳</div>
                <div class="ewallet-message">
                  <p class="mb-2">You will be redirected to <strong>Maya</strong> to complete your payment securely.</p>
                  <p class="text-secondary fs-7 mb-0">Make sure you have the Maya app or access to the Maya website ready.</p>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-outline-secondary" @click="cancelEWalletConfirm" :disabled="isProcessing">
                Cancel
              </button>
              <button class="btn btn-primary" style="background-color: #00AFEF; border-color: #00AFEF;" @click="confirmEWalletPayment('grab_pay')" :disabled="isProcessing">
                <span v-if="!isProcessing">Continue to Maya →</span>
                <span v-else class="d-flex align-items-center gap-2">
                  Creating payment link...
                  <span class="spinner-border spinner-border-sm" role="status"></span>
                </span>
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
import { formatDateTimePH } from '@/utils/dateTimeHelper.js'

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
      autoAppliedPromotions: [], // Auto-detected promotions (like Drinks Promo)
      availablePromotions: [], // All active promotions
      
      // Special Discounts
      isDrinksPromo: false, // Drinks Promo checkbox
      isSpecialDiscount: false, // PWD / Senior Citizen discount checkbox
      
      // Payment
      paymentMethod: 'cash', // 'cash', 'gcash', 'paymaya'
      cashTendered: 0,
      stockSyncing: false,
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
      },

      // Payment confirmation modals
      showCashConfirmModal: false,
      showGCashConfirmModal: false,
      showPayMayaConfirmModal: false,
    }
  },
  
  computed: {
    cartItems() {
      return this.cartStore.items
    },
    
    cartSubtotal() {
      // Use subtotal (sum of items), not total (which includes tax and discounts)
      return this.cartStore.subtotal
    },
    
    // Drinks Promo discount (only when checkbox is checked)
    drinksPromoDiscount() {
      if (!this.isDrinksPromo) return 0
      
      // Find Drinks Promo from available promotions
      const drinksPromo = this.availablePromotions.find(p => 
        p.name.toLowerCase().includes('drinks') || 
        p.name.toLowerCase().includes('drink')
      )
      
      if (!drinksPromo) return 0
      
      // Calculate discount using the same logic as before (only on drinks category items)
      return this.calculatePromotionDiscount(drinksPromo)
    },
    
    // Total discount from all auto-applied promotions (excluding Drinks Promo)
    totalPromoDiscount() {
      return this.autoAppliedPromotions.reduce((sum, promo) => sum + promo.discountAmount, 0)
    },
    
    // Total discount including Drinks Promo
    totalAllPromoDiscount() {
      return this.totalPromoDiscount + this.drinksPromoDiscount
    },
    
    // PWD / Senior Citizen Discount (20% on subtotal after promotions)
    specialDiscount() {
      if (!this.isSpecialDiscount) return 0
      const discountableAmount = this.cartSubtotal - this.totalAllPromoDiscount
      return Math.round(discountableAmount * 0.20 * 100) / 100
    },
    
    // Backward compatibility - combine into one discount
    pwdDiscount() {
      return this.specialDiscount
    },
    
    seniorCitizenDiscount() {
      return this.specialDiscount
    },
    
    // Helper computed properties for backward compatibility
    isPWD() {
      return this.isSpecialDiscount
    },
    
    isSeniorCitizen() {
      return this.isSpecialDiscount
    },
    
    subtotalAfterPromo() {
      return Math.max(0, this.cartSubtotal - this.totalAllPromoDiscount)
    },
    
    subtotalAfterAllDiscounts() {
      // Subtotal after promotions and special discount (PWD/Senior Citizen)
      return Math.max(0, this.subtotalAfterPromo - this.specialDiscount)
    },
    
    taxAmount() {
      // Tax is calculated on subtotal after all discounts (promotions, PWD, Senior Citizen) but before points
      const taxableAmount = this.subtotalAfterAllDiscounts - this.appliedPointsDiscount
      return Math.round(taxableAmount * 0.12 * 100) / 100
    },
    
    grandTotal() {
      return Math.max(0, this.subtotalAfterAllDiscounts - this.appliedPointsDiscount + this.taxAmount)
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
      const subtotalAfterPromo = Math.max(0, this.cartSubtotal - this.totalAllPromoDiscount)

      // Dynamic cap: max 20% of subtotalAfterPromo
      const maxDiscountAmount = subtotalAfterPromo * 0.20

      // Convert peso value to equivalent points
      const maxPointsFromSubtotal = Math.floor(maxDiscountAmount * pointsPerPeso)

      // Limit by customer’s actual points
      const customerPoints = this.selectedCustomer.loyalty_points || 0

      // Hard cap: Maximum 80 points (₱20) per transaction
      const ABSOLUTE_MAX_POINTS = 80

      // Final allowed redemption: min of (calculated max, customer points, absolute max)
      return Math.min(maxPointsFromSubtotal, customerPoints, ABSOLUTE_MAX_POINTS)
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
    
    cashSuggestions() {
      const total = this.grandTotal
      if (!total || total <= 0) return []

      const denominations = [50, 100, 200, 500, 1000]
      const exact = Math.ceil(total)
      const set = new Set([exact])

      for (const denom of denominations) {
        set.add(Math.ceil(total / denom) * denom)
      }

      // Always include one option comfortably above the total
      const base1000 = Math.ceil(total / 1000) * 1000
      set.add(base1000 + 1000)

      return [...set].sort((a, b) => a - b).filter(s => s >= exact).slice(0, 4)
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
  
  watch: {
    // Re-detect promotions when cart items change
    'cartStore.items': {
      handler() {
        if (this.cartItems.length > 0) {
          this.autoDetectAndApplyPromotions()
        } else {
          this.autoAppliedPromotions = []
        }
      },
      deep: true
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
        
        // ✅ STEP 2: Auto-detect and apply eligible promotions
        await this.autoDetectAndApplyPromotions()
        
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
        alert('Invalid points amount. Please enter between 40 and ' + this.maxRedeemablePoints + ' points.')
        return
      }
      
      // Enforce absolute max 80 points (₱20) per transaction
      if (this.pointsToRedeem > 80) {
        alert('Maximum points redemption is 80 points (₱20) per transaction')
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
    // AUTO-DETECT PROMOTIONS
    // ================================================================
    
    async autoDetectAndApplyPromotions() {
      if (this.cartItems.length === 0) {
        this.autoAppliedPromotions = []
        return
      }
      
      try {
        // Fetch active promotions
        const response = await api.get('/promotions/active/')
        let allPromotions = []
        
        if (response && response.data && response.data.success) {
          allPromotions = response.data.promotions || []
        }
        
        if (allPromotions.length === 0) {
          this.autoAppliedPromotions = []
          return
        }
        
        // Parse discount_config if needed
        allPromotions = allPromotions.map(promo => {
          if (typeof promo.discount_config === 'string') {
            try {
              promo.discount_config = JSON.parse(promo.discount_config)
            } catch (e) {
              promo.discount_config = {}
            }
          }
          if (!promo.discount_config) {
            promo.discount_config = {}
          }
          return promo
        })
        
        // Calculate discount for each promotion and auto-apply if applicable
        const applicablePromotions = []
        
        for (const promo of allPromotions) {
          // Skip PWD, Senior Citizen, and Drinks Promo - they're handled separately via checkboxes
          const promoNameLower = promo.name.toLowerCase()
          if (promoNameLower.includes('pwd') || 
              promoNameLower.includes('senior') ||
              promoNameLower.includes('drinks') ||
              promoNameLower.includes('drink')) {
            continue
          }
          
          const discount = this.calculatePromotionDiscount(promo)
          
          if (discount > 0) {
            applicablePromotions.push({
              ...promo,
              discountAmount: discount
            })
          }
        }
        
        // Sort by discount amount (highest first)
        applicablePromotions.sort((a, b) => b.discountAmount - a.discountAmount)
        
        this.autoAppliedPromotions = applicablePromotions
        this.availablePromotions = allPromotions
        
      } catch (error) {
        console.error('Error auto-detecting promotions:', error)
        this.autoAppliedPromotions = []
      }
    },
    
    calculatePromotionDiscount(promotion) {
      const discountConfig = promotion.discount_config || {}
      
      // If discount_config is empty or doesn't have target_type, return 0
      if (!discountConfig || Object.keys(discountConfig).length === 0 || !discountConfig.target_type) {
        if (!promotion.target_type) {
          return 0
        }
      }
      
      const targetType = promotion.target_type || discountConfig.target_type
      const targetIds = promotion.target_ids || discountConfig.target_ids || []
      const targetIdsArray = Array.isArray(targetIds) ? targetIds : []
      
      let eligibleAmount = 0
      
      if (targetType === 'all') {
        eligibleAmount = this.cartSubtotal
      } else if (targetType === 'categories') {
        const eligibleItems = this.cartItems.filter(item => {
          let productCategory = item.category || item.category_id
          
          if (!productCategory) {
            const product = this.products.find(p => p.id === item.productId)
            if (product) {
              productCategory = product.category_id || product.category
            }
          }
          
          if (!productCategory) {
            return false
          }
          
          const productCategoryStr = String(productCategory)
          const targetIdsStr = targetIdsArray.map(id => String(id))
          return targetIdsStr.includes(productCategoryStr) || targetIdsArray.includes(productCategory)
        })
        
        eligibleAmount = eligibleItems.reduce((sum, item) => sum + item.subtotal, 0)
      } else if (targetType === 'products') {
        const eligibleItems = this.cartItems.filter(item => {
          return targetIdsArray.includes(item.productId)
        })
        eligibleAmount = eligibleItems.reduce((sum, item) => sum + item.subtotal, 0)
      }
      
      if (eligibleAmount === 0) {
        return 0
      }
      
      let discount = 0
      
      if (promotion.type === 'percentage') {
        discount = eligibleAmount * (promotion.discount_value / 100)
      } else if (promotion.type === 'fixed' || promotion.type === 'fixed_amount') {
        discount = Math.min(promotion.discount_value, eligibleAmount)
      }
      
      return Math.round(discount * 100) / 100
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
    
    selectSuggestion(amount) {
      this.cashTendered = amount
      this.validateCashPayment()
    },

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
      
      // Show custom confirmation modal instead of browser confirm
      this.showCashConfirmModal = true
    },

    async executeCashPayment() {
      try {
        this.isProcessing = true
        this.isLoading = true
        this.loadingMessage = 'Processing cash payment...'
        this.showCashConfirmModal = false // Close modal immediately when processing starts
        
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
        
        console.log('[Checkout] createSale sending...')
        const result = await apiSales.createSale(saleData)
        console.log('[Checkout] createSale succeeded. sale_id:', result?.sale_id)
        this.handleSaleSuccess(result, 'cash')
        
      } catch (error) {
        alert(`Payment failed: ${error.message}`)
        this.showCashConfirmModal = false
      } finally {
        this.isProcessing = false
        this.isLoading = false
      }
    },
    
    // ----------------------------------------------------------------
    // QR PH PAYMENT (GCash/Maya via PayMongo)
    // ----------------------------------------------------------------
    
    async processEWalletPayment(type) {
      // Show custom confirmation modal instead of browser confirm
      if (type === 'gcash') {
        this.showGCashConfirmModal = true
      } else if (type === 'grab_pay') {
        this.showPayMayaConfirmModal = true
      }
    },

    async executeEWalletPayment(type) {
      const walletName = type === 'gcash' ? 'GCash' : 'Maya'
      
      try {
        this.isProcessing = true
        this.isLoading = true
        this.loadingMessage = `Creating ${walletName} payment link...`
        this.showGCashConfirmModal = false // Close modals immediately when processing starts
        this.showPayMayaConfirmModal = false
        
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
          promo_discount: this.totalPromoDiscount,
          pwd_discount: this.pwdDiscount,
          senior_citizen_discount: this.seniorCitizenDiscount,
          points_discount: this.appliedPointsDiscount,
          cart_items: this.cartStore.items,
          promotions: this.autoAppliedPromotions,
          is_pwd: this.isSpecialDiscount,
          is_senior_citizen: this.isSpecialDiscount,
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
      
      // Auto-applied promotions
      if (this.autoAppliedPromotions.length > 0) {
        saleData.promotions = this.autoAppliedPromotions.map(p => ({
          promotion_id: p._id,
          promotion_name: p.name,
          discount_amount: p.discountAmount
        }))
      }
      
      // Drinks Promo (if checked)
      if (this.isDrinksPromo && this.drinksPromoDiscount > 0) {
        const drinksPromo = this.availablePromotions.find(p => 
          p.name.toLowerCase().includes('drinks') || 
          p.name.toLowerCase().includes('drink')
        )
        if (drinksPromo) {
          if (!saleData.promotions) saleData.promotions = []
          saleData.promotions.push({
            promotion_id: drinksPromo._id,
            promotion_name: drinksPromo.name,
            discount_amount: this.drinksPromoDiscount
          })
        }
      }
      
      saleData.promotion_discount = this.totalAllPromoDiscount
      
      // PWD and Senior Citizen discounts
      saleData.pwd_discount = this.pwdDiscount
      saleData.senior_citizen_discount = this.seniorCitizenDiscount
      saleData.is_pwd = this.isSpecialDiscount
      saleData.is_senior_citizen = this.isSpecialDiscount
      
      if (this.appliedPointsDiscount > 0) {
        saleData.points_discount = this.appliedPointsDiscount
      } else {
        saleData.points_discount = 0
      }
      
      saleData.discount = this.totalAllPromoDiscount + this.pwdDiscount + this.seniorCitizenDiscount + this.appliedPointsDiscount
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

      // Fetch fresh stock — "New Order" button stays disabled until this
      // resolves. A 700ms delay lets DynamoDB propagate the UpdateItem before
      // the stock endpoint reads it (eventual consistency window).
      this.stockSyncing = true
      console.log('[Checkout] handleSaleSuccess: starting stock sync, disabling New Order button')
      apiProducts.getStockLevels()
        .then(stockData => {
          console.log('[Checkout] stock sync complete, got', stockData?.length, 'items')
          if (Array.isArray(stockData) && stockData.length > 0) {
            sessionStorage.setItem('prefetchedStockLevels', JSON.stringify({
              data: stockData,
              fetchedAt: Date.now()
            }))
            console.log('[Checkout] prefetchedStockLevels stored, enabling New Order button')
          } else {
            console.warn('[Checkout] stock sync returned empty')
          }
        })
        .catch(err => console.error('[Checkout] stock sync error:', err))
        .finally(() => { this.stockSyncing = false })
      
      
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
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://pos.panntech/api/v1'
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
      console.log('[Checkout] startNewOrder clicked — navigating to /new-order')
      console.log('[Checkout] prefetchedStockLevels in sessionStorage at navigation:', sessionStorage.getItem('prefetchedStockLevels') ? 'YES' : 'NO')
      this.cashTendered = 0
      this.paymentMethod = 'cash'
      this.stockSyncing = false
      
      sessionStorage.setItem('refreshStockAfterCheckout', 'full')
      
      this.$router.replace('/new-order')
    },

    // Cash Payment Confirmation Modal Methods
    showCashConfirm() {
      this.showCashConfirmModal = true
    },
    cancelCashConfirm() {
      this.showCashConfirmModal = false
      this.cashTendered = 0
      this.cashValidationError = null
    },
    async confirmCashPayment() {
      if (this.cashTendered < this.grandTotal) {
        alert(`Insufficient cash tendered. Need ₱${this.formatPrice(this.grandTotal - this.cashTendered)} more.`)
        return
      }

      this.showCashConfirmModal = false
      await this.executeCashPayment()
    },

    // E-Wallet Payment Confirmation Modal Methods
    cancelEWalletConfirm() {
      this.showGCashConfirmModal = false
      this.showPayMayaConfirmModal = false
    },
    async confirmEWalletPayment(type) {
      this.showGCashConfirmModal = false
      this.showPayMayaConfirmModal = false
      await this.executeEWalletPayment(type)
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
      return formatDateTimePH(dateString, { hour12: false })
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
/* Payment Confirmation Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-container {
  background: var(--surface-primary, #ffffff);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  animation: fadeIn 0.3s ease-out;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.btn-close:hover {
  background-color: var(--surface-secondary, #f5f5f5);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--border-color, #e0e0e0);
}

.cash-confirm-modal {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
}

.ewallet-confirm-modal {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
}

.gcash-modal .modal-header {
  border-bottom-color: rgba(0, 112, 186, 0.2);
}

.paymaya-modal .modal-header {
  border-bottom-color: rgba(0, 175, 239, 0.2);
}

.payment-summary {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--surface-secondary, #f8f9fa);
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.summary-row:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.summary-label {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary, #666);
}

.summary-value {
  font-size: 18px;
  font-weight: 600;
}

.change-row {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  border: 2px solid #28a745;
}

.change-amount {
  font-size: 24px;
  font-weight: 700;
  color: #155724;
}

.ewallet-info-box {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 1px solid var(--border-color, #dee2e6);
  margin-top: 20px;
}

.ewallet-icon {
  font-size: 48px;
  line-height: 1;
  flex-shrink: 0;
}

.ewallet-message {
  flex: 1;
}

.ewallet-message p {
  margin: 0;
  line-height: 1.6;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>