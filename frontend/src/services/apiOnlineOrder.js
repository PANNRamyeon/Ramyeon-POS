import { api } from './api.js'

export default {
  // ================================================================
  // ORDER RETRIEVAL
  // ================================================================
  
  /**
   * Get all orders with optional filters
   */
  async getAllOrders(filters = {}) {
    try {
      const params = new URLSearchParams()
      
      if (filters.status) params.append('status', filters.status)
      if (filters.payment_status) params.append('payment_status', filters.payment_status)
      if (filters.customer_id) params.append('customer_id', filters.customer_id)
      
      const response = await api.get(`/online/orders/?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error fetching orders:', error)
      throw error
    }
  },

  /**
   * Get single order by ID
   */
  async getOrder(orderId) {
    try {
      const response = await api.get(`/online/orders/${orderId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching order:', error)
      throw error
    }
  },

  // ================================================================
  // ORDER ACTIONS (Staff)
  // ================================================================

  /**
   * Update order status
   */
  async updateOrderStatus(orderId, newStatus, updatedBy, notes = '') {
    try {
      const response = await api.patch(
        `/online/orders/${orderId}/status/`,
        {
          new_status: newStatus,
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

  /**
   * Confirm payment (for PayMongo orders)
   */
  async confirmPayment(orderId, paymentReference, confirmedBy) {
    try {
      const response = await api.patch(
        `/online/orders/${orderId}/payment/`,
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

  /**
   * Mark order as ready for delivery
   */
  async markReadyForDelivery(orderId, preparedBy, deliveryNotes = '') {
    try {
      const response = await api.post(
        `/online/orders/${orderId}/ready-for-delivery/`,
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

  /**
   * Complete order (mark as delivered)
   */
  async completeOrder(orderId, completedBy, deliveryPerson = null) {
    try {
      const response = await api.post(
        `/online/orders/${orderId}/complete/`,
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

  /**
   * Cancel order
   */
  async cancelOrder(orderId, cancellationReason, cancelledBy) {
    try {
      const response = await api.post(
        `/online/orders/${orderId}/cancel/`,
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