import { api } from './api.js'

export default {
  // ================================================================
  // ORDER RETRIEVAL
  // ================================================================

  async getAllOrders(filters = {}) {
    try {
      const params = new URLSearchParams()

      if (filters.status) params.append('status', filters.status)
      if (filters.payment_status) params.append('payment_status', filters.payment_status)
      if (filters.customer_id) params.append('customer_id', filters.customer_id)

      // 10s timeout — backend returns empty list within 8s if DynamoDB is slow
      const response = await api.get(`/pos/orders/online/?${params.toString()}`, { timeout: 10000 })
      return response.data
    } catch (error) {
      console.error('Error fetching orders:', error)
      return []
    }
  },

  async getOrder(orderId) {
    try {
      const response = await api.get(`/pos/orders/online/${orderId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching order:', error)
      throw error
    }
  },

  // ================================================================
  // ORDER ACTIONS (Staff)
  // ================================================================

  async updateOrderStatus(orderId, newStatus, updatedBy, notes = '') {
    try {
      const response = await api.post(
        `/pos/orders/${orderId}/status/`,
        {
          status: newStatus,
          updated_by: updatedBy,
          notes: notes
        }
      )
      return response.data
    } catch (error) {
      console.error('Error updating order status:', error)
      throw error
    }
  },

  async confirmPayment(orderId, paymentReference, confirmedBy) {
    try {
      const response = await api.post(
        `/pos/orders/${orderId}/payment/`,
        {
          payment_status: 'paid',
          payment_reference: paymentReference,
          confirmed_by: confirmedBy
        }
      )
      return response.data
    } catch (error) {
      console.error('Error confirming payment:', error)
      throw error
    }
  },

  async markReadyForDelivery(orderId, preparedBy, deliveryNotes = '') {
    try {
      const response = await api.post(
        `/pos/orders/${orderId}/ready/`,
        {
          prepared_by: preparedBy,
          delivery_notes: deliveryNotes
        }
      )
      return response.data
    } catch (error) {
      console.error('Error marking ready for delivery:', error)
      throw error
    }
  },

  async completeOrder(orderId, completedBy, deliveryPerson = null) {
    try {
      const response = await api.post(
        `/pos/orders/${orderId}/complete/`,
        {
          completed_by: completedBy,
          delivery_person: deliveryPerson
        }
      )
      return response.data
    } catch (error) {
      console.error('Error completing order:', error)
      throw error
    }
  },

  async cancelOrder(orderId, cancellationReason, cancelledBy) {
    try {
      const response = await api.post(
        `/pos/orders/${orderId}/cancel/`,
        {
          cancellation_reason: cancellationReason,
          cancelled_by: cancelledBy
        }
      )
      return response.data
    } catch (error) {
      console.error('Error cancelling order:', error)
      throw error
    }
  }
}
