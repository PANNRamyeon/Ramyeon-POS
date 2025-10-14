import { ref } from 'vue'

/**
 * PayMongo API Integration for PANN POS System
 * Handles payment processing for Card, GCash, and Maya payments
 * 
 * Test Mode Configuration:
 * - Use test API keys from PayMongo dashboard
 * - Test Card: 4343 4343 4343 4345
 * - All amounts in Philippine Pesos (PHP)
 */

export function usePaymongo() {
  // State management
  const loading = ref(false)
  const error = ref(null)
  const paymentStatus = ref(null)
  
  // Environment configuration
  const config = {
    publicKey: import.meta.env.VITE_PAYMONGO_PUBLIC_KEY,
    secretKey: import.meta.env.VITE_PAYMONGO_SECRET_KEY,
    baseURL: 'https://api.paymongo.com/v1',
    mode: import.meta.env.VITE_PAYMONGO_MODE || 'test'
  }

  /**
   * Create authorization header for PayMongo API
   * Uses Basic Auth with base64 encoded key
   */
  const getAuthHeader = (useSecretKey = false) => {
    const key = useSecretKey ? config.secretKey : config.publicKey
    return `Basic ${btoa(key + ':')}`
  }

  /**
   * Convert PHP amount to centavos (PayMongo requirement)
   * @param {number} amount - Amount in PHP
   * @returns {number} - Amount in centavos
   */
  const toCentavos = (amount) => {
    return Math.round(amount * 100)
  }

  /**
   * Convert centavos to PHP
   * @param {number} centavos - Amount in centavos
   * @returns {number} - Amount in PHP
   */
  const toPhp = (centavos) => {
    return centavos / 100
  }

  /**
   * Create a Payment Intent
   * First step in payment process - creates intent to charge customer
   * 
   * @param {number} amount - Amount in PHP
   * @param {string} description - Payment description
   * @param {object} metadata - Additional data (order_id, customer_id, etc.)
   * @returns {Promise<object>} - Payment Intent object
   */
  const createPaymentIntent = async (amount, description, metadata = {}) => {
    loading.value = true
    error.value = null
    paymentStatus.value = 'creating_intent'

    try {
      const response = await fetch(`${config.baseURL}/payment_intents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': getAuthHeader(true) // Use secret key
        },
        body: JSON.stringify({
          data: {
            attributes: {
              amount: toCentavos(amount),
              payment_method_allowed: ['card', 'gcash', 'paymaya'],
              payment_method_options: {
                card: {
                  request_three_d_secure: 'any' // 3D Secure for card security
                }
              },
              currency: 'PHP',
              description: description || 'Ramyeon Food Corner - Order Payment',
              statement_descriptor: 'RAMYEON FC', // Appears on customer's statement
              metadata: {
                ...metadata,
                store: 'Ramyeon Food Corner',
                location: 'Bislig City',
                payment_source: 'POS'
              }
            }
          }
        })
      })

      const data = await response.json()
      
      if (!response.ok) {
        const errorMessage = data.errors?.[0]?.detail || 'Failed to create payment intent'
        throw new Error(errorMessage)
      }

      paymentStatus.value = 'intent_created'
      return data.data

    } catch (err) {
      error.value = err.message
      paymentStatus.value = 'error'
      console.error('PayMongo Error (Create Intent):', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create Payment Method (Card)
   * Tokenizes card details securely
   * 
   * @param {object} cardDetails - Card information
   * @param {string} cardDetails.number - Card number (no spaces)
   * @param {string} cardDetails.expMonth - Expiry month (MM)
   * @param {string} cardDetails.expYear - Expiry year (YYYY)
   * @param {string} cardDetails.cvc - Card CVC/CVV
   * @returns {Promise<object>} - Payment Method object
   */
  const createPaymentMethod = async (cardDetails) => {
    loading.value = true
    error.value = null
    paymentStatus.value = 'creating_payment_method'

    try {
      // Validate card details
      if (!cardDetails.number || !cardDetails.expMonth || !cardDetails.expYear || !cardDetails.cvc) {
        throw new Error('Incomplete card details')
      }

      const response = await fetch(`${config.baseURL}/payment_methods`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': getAuthHeader(true) // Use secret key for security
        },
        body: JSON.stringify({
          data: {
            attributes: {
              type: 'card',
              details: {
                card_number: cardDetails.number.replace(/\s/g, ''), // Remove spaces
                exp_month: parseInt(cardDetails.expMonth),
                exp_year: parseInt(cardDetails.expYear),
                cvc: cardDetails.cvc
              },
              billing: cardDetails.billing || null // Optional billing details
            }
          }
        })
      })

      const data = await response.json()
      
      if (!response.ok) {
        const errorMessage = data.errors?.[0]?.detail || 'Invalid card details'
        throw new Error(errorMessage)
      }

      paymentStatus.value = 'payment_method_created'
      return data.data

    } catch (err) {
      error.value = err.message
      paymentStatus.value = 'error'
      console.error('PayMongo Error (Create Payment Method):', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Attach Payment Method to Payment Intent
   * Links the payment method to the intent and processes payment
   * 
   * @param {string} paymentIntentId - Payment Intent ID
   * @param {string} paymentMethodId - Payment Method ID
   * @param {string} clientKey - Client key from payment intent
   * @returns {Promise<object>} - Updated Payment Intent
   */
  const attachPaymentMethod = async (paymentIntentId, paymentMethodId, clientKey = null) => {
    loading.value = true
    error.value = null
    paymentStatus.value = 'processing_payment'

    try {
      const response = await fetch(`${config.baseURL}/payment_intents/${paymentIntentId}/attach`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': getAuthHeader(true)
        },
        body: JSON.stringify({
          data: {
            attributes: {
              payment_method: paymentMethodId,
              client_key: clientKey,
              return_url: `${window.location.origin}/payment/callback` // For 3D Secure
            }
          }
        })
      })

      const data = await response.json()
      
      if (!response.ok) {
        const errorMessage = data.errors?.[0]?.detail || 'Payment processing failed'
        throw new Error(errorMessage)
      }

      const status = data.data.attributes.status
      
      if (status === 'awaiting_next_action') {
        // 3D Secure required - redirect customer
        paymentStatus.value = '3ds_required'
        const nextAction = data.data.attributes.next_action
        if (nextAction?.redirect?.url) {
          return {
            ...data.data,
            requires_action: true,
            redirect_url: nextAction.redirect.url
          }
        }
      } else if (status === 'succeeded') {
        paymentStatus.value = 'success'
      } else if (status === 'processing') {
        paymentStatus.value = 'processing'
      }

      return data.data

    } catch (err) {
      error.value = err.message
      paymentStatus.value = 'error'
      console.error('PayMongo Error (Attach Payment):', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create E-Wallet Source (GCash/Maya)
   * Creates payment source for e-wallet payments
   * 
   * @param {number} amount - Amount in PHP
   * @param {string} type - 'gcash' or 'grab_pay' (Maya uses grab_pay)
   * @param {object} options - Additional options
   * @returns {Promise<object>} - Source object with redirect URL
   */
  const createEWalletSource = async (amount, type, options = {}) => {
    loading.value = true
    error.value = null
    paymentStatus.value = 'creating_ewallet_source'

    try {
      // Validate e-wallet type
      const validTypes = ['gcash', 'grab_pay', 'paymaya']
      if (!validTypes.includes(type)) {
        throw new Error(`Invalid e-wallet type: ${type}`)
      }

      const response = await fetch(`${config.baseURL}/sources`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': getAuthHeader(true)
        },
        body: JSON.stringify({
          data: {
            attributes: {
              amount: toCentavos(amount),
              redirect: {
                success: options.successUrl || `${window.location.origin}/payment/success`,
                failed: options.failedUrl || `${window.location.origin}/payment/failed`
              },
              type: type,
              currency: 'PHP',
              metadata: options.metadata || {}
            }
          }
        })
      })

      const data = await response.json()
      
      if (!response.ok) {
        const errorMessage = data.errors?.[0]?.detail || 'E-wallet source creation failed'
        throw new Error(errorMessage)
      }

      paymentStatus.value = 'ewallet_source_created'
      return data.data

    } catch (err) {
      error.value = err.message
      paymentStatus.value = 'error'
      console.error('PayMongo Error (E-Wallet Source):', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create Payment (Direct Charge via Source)
   * Creates payment using a source (for e-wallets after customer authorization)
   * 
   * @param {number} amount - Amount in PHP
   * @param {string} sourceId - Source ID from createEWalletSource
   * @param {object} metadata - Additional metadata
   * @returns {Promise<object>} - Payment object
   */
  const createPayment = async (amount, sourceId, metadata = {}) => {
    loading.value = true
    error.value = null
    paymentStatus.value = 'creating_payment'

    try {
      const response = await fetch(`${config.baseURL}/payments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': getAuthHeader(true)
        },
        body: JSON.stringify({
          data: {
            attributes: {
              amount: toCentavos(amount),
              source: {
                id: sourceId,
                type: 'source'
              },
              currency: 'PHP',
              description: 'Ramyeon Food Corner - Order Payment',
              statement_descriptor: 'RAMYEON FC',
              metadata
            }
          }
        })
      })

      const data = await response.json()
      
      if (!response.ok) {
        const errorMessage = data.errors?.[0]?.detail || 'Payment creation failed'
        throw new Error(errorMessage)
      }

      paymentStatus.value = data.data.attributes.status
      return data.data

    } catch (err) {
      error.value = err.message
      paymentStatus.value = 'error'
      console.error('PayMongo Error (Create Payment):', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Retrieve Payment Intent
   * Gets current status of payment intent
   * 
   * @param {string} paymentIntentId - Payment Intent ID
   * @returns {Promise<object>} - Payment Intent object
   */
  const getPaymentIntent = async (paymentIntentId) => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${config.baseURL}/payment_intents/${paymentIntentId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': getAuthHeader(true)
        }
      })

      const data = await response.json()
      
      if (!response.ok) {
        const errorMessage = data.errors?.[0]?.detail || 'Failed to retrieve payment intent'
        throw new Error(errorMessage)
      }

      paymentStatus.value = data.data.attributes.status
      return data.data

    } catch (err) {
      error.value = err.message
      console.error('PayMongo Error (Get Payment Intent):', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Retrieve Payment
   * Gets payment details and status
   * 
   * @param {string} paymentId - Payment ID
   * @returns {Promise<object>} - Payment object
   */
  const getPayment = async (paymentId) => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${config.baseURL}/payments/${paymentId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': getAuthHeader(true)
        }
      })

      const data = await response.json()
      
      if (!response.ok) {
        const errorMessage = data.errors?.[0]?.detail || 'Failed to retrieve payment'
        throw new Error(errorMessage)
      }

      paymentStatus.value = data.data.attributes.status
      return data.data

    } catch (err) {
      error.value = err.message
      console.error('PayMongo Error (Get Payment):', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Process Card Payment (All-in-one)
   * Convenience method that handles entire card payment flow
   * 
   * @param {number} amount - Amount in PHP
   * @param {object} cardDetails - Card details
   * @param {object} metadata - Order metadata
   * @returns {Promise<object>} - Payment result
   */
  const processCardPayment = async (amount, cardDetails, metadata = {}) => {
    try {
      // Step 1: Create Payment Intent
      const intent = await createPaymentIntent(amount, 'Order Payment', metadata)
      
      // Step 2: Create Payment Method
      const paymentMethod = await createPaymentMethod(cardDetails)
      
      // Step 3: Attach and Process
      const result = await attachPaymentMethod(
        intent.id, 
        paymentMethod.id, 
        intent.attributes.client_key
      )
      
      return {
        success: result.attributes.status === 'succeeded',
        status: result.attributes.status,
        paymentIntentId: result.id,
        amount: toPhp(result.attributes.amount),
        requires_action: result.requires_action || false,
        redirect_url: result.redirect_url || null
      }

    } catch (err) {
      return {
        success: false,
        error: err.message
      }
    }
  }

  /**
   * Clear error state
   */
  const clearError = () => {
    error.value = null
  }

  /**
   * Reset payment status
   */
  const resetStatus = () => {
    paymentStatus.value = null
    error.value = null
  }

  return {
    // State
    loading,
    error,
    paymentStatus,
    
    // Payment Intent Methods
    createPaymentIntent,
    getPaymentIntent,
    
    // Payment Method Methods
    createPaymentMethod,
    attachPaymentMethod,
    
    // E-Wallet Methods
    createEWalletSource,
    createPayment,
    getPayment,
    
    // Convenience Methods
    processCardPayment,
    
    // Utility Methods
    toCentavos,
    toPhp,
    clearError,
    resetStatus,
    
    // Config (read-only)
    config: { ...config, secretKey: '***' } // Hide secret key in exposed config
  }
}