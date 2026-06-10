// src/services/apiPayment.js

class PaymentService {

  processCashPayment(totalAmount, cashTendered) {
    const change = cashTendered - totalAmount;
    if (change < 0) {
      throw new Error('Insufficient cash tendered');
    }
    return {
      method: 'cash',
      amount_paid: cashTendered,
      change: change,
      status: 'completed',
      transaction_id: `CASH-${Date.now()}`,
      timestamp: new Date().toISOString()
    };
  }

  validateCashPayment(totalAmount, cashTendered) {
    if (!cashTendered || cashTendered <= 0) {
      return { valid: false, error: 'Please enter cash tendered amount' };
    }
    if (cashTendered < totalAmount) {
      return {
        valid: false,
        error: `Insufficient amount. Need ₱${(totalAmount - cashTendered).toFixed(2)} more`
      };
    }
    return { valid: true, error: null };
  }
}

export default new PaymentService();
