import { ref } from 'vue'

export function usePaymaya() {
  const loading = ref(false)
  const error = ref(null)
  const paymentStatus = ref(null)

  const config = {
    secretKey: import.meta.env.VITE_MAYA_SECRET_KEY,
    publicKey: import.meta.env.VITE_MAYA_PUBLIC_KEY,
    baseURL: import.meta.env.VITE_MAYA_MODE === 'live'
      ? 'https://pg.maya.ph'
      : 'https://pg-sandbox.maya.ph',
    mode: import.meta.env.VITE_MAYA_MODE || 'sandbox'
  }

  const getAuthHeader = () => `Basic ${btoa(config.secretKey + ':')}`

  /**
   * Create a Maya checkout session.
   * Returns { checkoutId, redirectUrl } — redirect the customer to redirectUrl.
   *
   * @param {number} amount - Total amount in PHP
   * @param {Array}  cartItems - Cart items from cartStore.items
   * @param {object} options - { referenceNumber, successUrl, failureUrl, cancelUrl, description, metadata }
   */
  const createCheckout = async (amount, cartItems = [], options = {}) => {
    loading.value = true
    error.value = null
    paymentStatus.value = 'creating_checkout'

    try {
      const requestReferenceNumber = options.referenceNumber || `POS-${Date.now()}`

      const items = cartItems.length > 0
        ? cartItems.map(item => ({
            name: item.productName || item.name,
            quantity: item.quantity,
            code: item.sku || item.productId || '',
            description: item.productName || item.name,
            amount: { value: parseFloat(item.price) },
            totalAmount: { value: parseFloat(item.subtotal) }
          }))
        : [{
            name: 'Order Payment',
            quantity: 1,
            code: requestReferenceNumber,
            description: options.description || 'Ramyeon Food Corner - Order Payment',
            amount: { value: parseFloat(amount) },
            totalAmount: { value: parseFloat(amount) }
          }]

      const body = {
        totalAmount: {
          value: parseFloat(amount),
          currency: 'PHP',
          details: { subtotal: parseFloat(amount) }
        },
        items,
        redirectUrl: {
          success: options.successUrl || `${window.location.origin}/pos/payment-callback?status=success`,
          failure: options.failureUrl || `${window.location.origin}/pos/payment-callback?status=failed`,
          cancel: options.cancelUrl || `${window.location.origin}/pos/payment-callback?status=failed`
        },
        requestReferenceNumber,
        metadata: options.metadata || {}
      }

      const response = await fetch(`${config.baseURL}/checkout/v1/checkouts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': getAuthHeader()
        },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (!response.ok) {
        const msg = data.message || data.error?.message || 'Failed to create Maya checkout'
        throw new Error(msg)
      }

      paymentStatus.value = 'checkout_created'
      return data // { checkoutId, redirectUrl }

    } catch (err) {
      error.value = err.message
      paymentStatus.value = 'error'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Retrieve a checkout session by ID.
   * Useful for verifying payment status on the callback page.
   *
   * @param {string} checkoutId
   */
  const getCheckout = async (checkoutId) => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${config.baseURL}/checkout/v1/checkouts/${checkoutId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': getAuthHeader()
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || 'Failed to retrieve Maya checkout')
      }

      paymentStatus.value = data.paymentStatus
      return data

    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearError = () => { error.value = null }
  const resetStatus = () => { paymentStatus.value = null; error.value = null }

  return {
    loading,
    error,
    paymentStatus,
    createCheckout,
    getCheckout,
    clearError,
    resetStatus,
    config: { ...config, secretKey: '***' }
  }
}
