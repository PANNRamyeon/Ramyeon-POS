<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <!-- Left Side - Logo Section -->
        <div class="logo-section">
          <div class="logo-placeholder">
              <img src="../assets/Logo_1.png" alt="PANN Logo" class="logo-image" />
          </div>
          <h2 class="brand-title">POS System</h2>
          <p class="brand-subtitle">Point of Sale Management</p>
        </div>

        <!-- Right Side - Login Form -->
        <div class="form-section">
          <div class="form-container">
            <h1 class="sign-in-title">Sign In</h1>
            
            <form @submit.prevent="handleLogin" class="login-form">
              <!-- Email Field -->
              <div class="form-group">
                <label for="email" class="form-label">Email:</label>
                <input 
                  id="email"
                  v-model="loginForm.email" 
                  type="email" 
                  class="form-input" 
                  placeholder="Enter your email" 
                  required 
                  :disabled="loading"
                />
              </div>

              <!-- Password Field -->
              <div class="form-group">
                <label for="password" class="form-label">Password:</label>
                <input 
                  id="password" 
                  v-model="loginForm.password" 
                  type="password" 
                  class="form-input" 
                  placeholder="Enter your password" 
                  required 
                  :disabled="loading"
                />
              </div>

              <!-- Opening Cash Field - ALWAYS SHOW -->
              <div class="form-group">
                <label for="openingCash" class="form-label">
                  Opening Cash:
                  <span class="optional-text"></span>
                </label>
                <input 
                  id="openingCash"
                  v-model.number="loginForm.openingCash" 
                  type="number" 
                  step="0.01"
                  min="0"
                  class="form-input" 
                  placeholder="Enter opening cash (leave 0 if admin)" 
                  :disabled="loading"
                />
              </div>

              <!-- Error Message -->
              <div v-if="error" class="error-message">
                {{ error }}
              </div>

              <!-- Success Message -->
              <div v-if="successMessage" class="success-message">
                {{ successMessage }}
              </div>

              <!-- Login Button -->
              <button type="submit" class="login-button" :disabled="loading">
                {{ loading ? 'Signing In...' : 'Login' }}
              </button>
            </form>

            <!-- Additional Options -->
            <div class="form-footer">
              <a href="#" class="forgot-password" @click.prevent="handleForgotPassword">
                Forgot Password?
              </a>
            </div>

          </div>
        </div>
      </div>
    </div>

    <!-- Logout Confirmation Modal -->
    <div v-if="showLogoutModal" class="modal-overlay" @click="closeLogoutModal">
      <div class="modal-content" @click.stop>
        <h3>End Shift & Logout</h3>
        <p class="text-muted mb-3">Please enter the closing cash amount for your shift.</p>
        
        <div class="form-group">
          <label for="closingCash" class="form-label">Closing Cash:</label>
          <input 
            id="closingCash"
            v-model.number="closingCash" 
            type="number" 
            step="0.01"
            min="0"
            class="form-input" 
            placeholder="Enter closing cash amount"
            required
          />
        </div>
        
        <div v-if="logoutError" class="error-message mb-3">
          {{ logoutError }}
        </div>
        
        <div class="modal-actions">
          <button 
            @click="confirmLogout" 
            class="btn-confirm"
            :disabled="logoutLoading"
          >
            {{ logoutLoading ? 'Ending Shift...' : 'End Shift & Logout' }}
          </button>
          <button 
            @click="closeLogoutModal" 
            class="btn-cancel"
            :disabled="logoutLoading"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiService from '../services/api.js'

export default {
  name: 'LoginPage',
  data() {
    return {
      loginForm: {
        email: '',
        password: '',
        openingCash: 0
      },
      loading: false,
      error: null,
      successMessage: null,
      showLogoutModal: false,
      closingCash: 0,
      logoutLoading: false,
      logoutError: null
    }
  },
  methods: {
    async handleLogin() {
      // Reset state
      this.error = null
      this.successMessage = null
      this.loading = true

      try {
        // Validate form
        if (!this.loginForm.email || !this.loginForm.password) {
          throw new Error('Please fill in all fields')
        }

        // Send login request WITH opening_cash
        const response = await apiService.login(
          this.loginForm.email, 
          this.loginForm.password,
          this.loginForm.openingCash || 0  // Default to 0 if not provided
        )
       
        await this.handleLoginSuccess(response)

      } catch (error) {
        console.error('Login error:', error)
        this.error = error.message || 'An error occurred during login'
      } finally {
        this.loading = false
      }
    },

    async handleLoginSuccess(response) {
      try {
        console.log('✅ Processing login success...', response);
        
        // ✅ Save auth token (check multiple possible fields)
        const token = response.token || response.access_token;
        if (token) {
          localStorage.setItem('authToken', token);
          console.log('🔑 Auth token saved');
        } else {
          console.warn('⚠️ No token found in response');
        }
        
        // ✅ Save user data
        if (response.user) {
          localStorage.setItem('userData', JSON.stringify(response.user));
          console.log('👤 User data saved:', response.user);
        } else {
          console.warn('⚠️ No user data in response');
        }
        
        // ✅ Save shift ID (check both top-level and nested)
        let shiftId = null;
        
        // Try top-level first
        if (response.shift_id) {
          shiftId = response.shift_id;
          console.log('⏰ Found shift_id at top level:', shiftId);
        } 
        // Fallback to nested shift.shift_id
        else if (response.shift && response.shift.shift_id) {
          shiftId = response.shift.shift_id;
          console.log('⏰ Found shift_id in nested shift object:', shiftId);
        }
        // Another fallback for shift._id
        else if (response.shift && response.shift._id) {
          shiftId = response.shift._id;
          console.log('⏰ Found _id in nested shift object:', shiftId);
        }
        
        if (shiftId) {
          localStorage.setItem('activeShiftId', shiftId);
          console.log('✅ Shift ID saved to localStorage:', shiftId);
        } else {
          console.warn('⚠️ No shift ID in login response - user may be admin or shift creation failed');
        }
        
        // ✅ Show success message
        this.successMessage = 'Login successful! Redirecting...';
        
        // ✅ Redirect to POS
        setTimeout(() => {
          this.$router.push('/new-order');
        }, 500);
        
      } catch (error) {
        console.error('❌ Login success handler error:', error);
        this.error = 'Login succeeded but session setup failed. Please try again.';
        throw error;
      }
    },

    navigateToDashboard(userRole) {
      let route = '/dashboard'

      if (userRole === 'admin') {
        route = '/dashboard'
      } else if (userRole === 'cashier' || userRole === 'employee') {
        route = '/dashboard'
      }

      this.$router.push(route)
        .then(() => {
          console.log(`Successfully navigated to ${route}`)
        })
        .catch((error) => {
          console.error('Navigation error:', error)
          this.$router.push('/dashboard')
        })
    },

    async handleLogout() {
      const userRole = localStorage.getItem('userRole')?.toLowerCase()
      const activeShiftId = localStorage.getItem('activeShiftId')

      // If user has an active shift, show modal to enter closing cash
      if ((userRole === 'cashier' || userRole === 'employee') && activeShiftId) {
        this.showLogoutModal = true
        // Pre-fill with opening cash as default
        const openingCash = localStorage.getItem('openingCash')
        this.closingCash = openingCash ? parseFloat(openingCash) : 0
        return
      }

      // Otherwise, proceed with normal logout
      await this.performLogout()
    },

    async confirmLogout() {
      this.logoutError = null
      this.logoutLoading = true

      try {
        // Validate closing cash
        if (this.closingCash < 0) {
          throw new Error('Closing cash cannot be negative')
        }

        // Perform logout with closing cash
        const response = await apiService.logout(this.closingCash)
        
        console.log('Logout response:', response)
        
        this.showLogoutModal = false
        await this.performLogout()
        
      } catch (error) {
        console.error('Error during logout:', error)
        this.logoutError = error.message || 'Failed to end shift. Please try again.'
      } finally {
        this.logoutLoading = false
      }
    },

    async performLogout() {
      // Clear all stored data
      localStorage.removeItem('authToken')
      localStorage.removeItem('userData')
      localStorage.removeItem('userRole')
      localStorage.removeItem('loginTime')
      localStorage.removeItem('activeShiftId')
      localStorage.removeItem('shiftStartTime')
      localStorage.removeItem('openingCash')
      
      // Reset form
      this.loginForm = { 
        email: '', 
        password: '',
        openingCash: 0
      }
      this.error = null
      this.successMessage = null
      this.closingCash = 0
      this.logoutError = null
      
      // Navigate back to login
      this.$router.push('/login')
      
      console.log('User logged out successfully')
    },

    closeLogoutModal() {
      if (!this.logoutLoading) {
        this.showLogoutModal = false
        this.closingCash = 0
        this.logoutError = null
      }
    },

    handleForgotPassword() {
      alert('Please contact your administrator to reset your password.')
    },

    isAuthenticated() {
      const token = localStorage.getItem('authToken')
      return !!token
    },

    getUserData() {
      const userData = localStorage.getItem('userData')
      return userData ? JSON.parse(userData) : null
    },

    getAuthToken() {
      return localStorage.getItem('authToken')
    }
  },

  mounted() {
    // Check if user is already authenticated
    if (this.isAuthenticated()) {
      const userData = this.getUserData()
      const userRole = userData?.role?.toLowerCase()
      
      this.$router.push('/dashboard')
    }
    
    console.log('Backend-integrated login component with shift management mounted')
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 1rem;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-content h3 {
  margin: 0 0 0.5rem 0;
  color: #1f2937;
  font-size: 1.5rem;
}

.text-muted {
  color: #6b7280;
  font-size: 0.875rem;
}

.mb-3 {
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-confirm,
.btn-cancel {
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-confirm {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-confirm:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-cancel {
  background: #e5e7eb;
  color: #374151;
}

.btn-cancel:hover:not(:disabled) {
  background: #d1d5db;
}

.btn-cancel:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.optional-text {
  font-size: 0.75rem;
  font-weight: 400;
  color: #9ca3af;
  font-style: italic;
  margin-left: 0.25rem;
}

/* Keep all previous styles */
.login-page {
  min-height: 100vh;
  background-color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  padding: 2rem;
  width: 100vw;
}

.login-container {
  width: 100vw;
  max-width: 900px;
}

.login-card {
  background: white;
  border-radius: 1.5rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 500px;
  animation: fadeIn 0.6s ease-out;
}

/* Left Side - Logo Section */
.logo-section {
  background: white;
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: white;
}

.logo-placeholder {
  margin-bottom: 2rem;
}

.brand-title {
  font-size: 1.75rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: rgb(68, 68, 68);
}

.brand-subtitle {
  font-size: 1rem;
  opacity: 0.9;
  margin: 0;
  color: grey;
}

/* Right Side - Form Section */
.form-section {
  padding: 3rem 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-container {
  width: 100%;
  max-width: 350px;
}

.sign-in-title {
  font-size: 2.25rem;
  font-weight: 700;
  color: #1f2937;
  text-align: center;
  margin: 0 0 2rem 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin: 0;
}

.form-input {
  padding: 0.875rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: all 0.2s ease;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input:disabled {
  background-color: #f9fafb;
  cursor: not-allowed;
  opacity: 0.6;
}

.form-input::placeholder {
  color: #9ca3af;
}

.error-message {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  text-align: center;
}

.success-message {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #16a34a;
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  text-align: center;
}

.login-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 0.5rem;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.login-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.form-footer {
  text-align: center;
  margin-top: 1.5rem;
}

.forgot-password {
  color: #667eea;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.2s ease;
}

.forgot-password:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* Animation */
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

/* Responsive Design */
@media (max-width: 768px) {
  .login-page {
    padding: 1rem;
  }
  
  .login-card {
    grid-template-columns: 1fr;
    max-width: 480px;
  }
  
  .logo-section {
    padding: 2rem 1.5rem;
  }
  
  .brand-title {
    font-size: 1.5rem;
  }
  
  .form-section {
    padding: 2rem 1.5rem;
  }
  
  .sign-in-title {
    font-size: 1.75rem;
  }
}

@media (max-width: 480px) {
  .login-page {
    padding: 0.5rem;
  }
  
  .form-section {
    padding: 1.5rem 1rem;
  }
  
  .logo-section {
    padding: 1.5rem 1rem;
  }
  
  .form-container {
    max-width: none;
  }
}
</style>