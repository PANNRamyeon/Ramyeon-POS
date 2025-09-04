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
                <input id="email"v-model="loginForm.email" type="email" class="form-input" placeholder="Enter your email" required :disabled="loading"/>
              </div>

              <!-- Password Field -->
              <div class="form-group">
                <label for="password" class="form-label">Password:</label>
                <input id="password" v-model="loginForm.password" type="password" class="form-input" placeholder="Enter your password" required :disabled="loading"/>
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
        password: ''
      },
      loading: false,
      error: null,
      successMessage: null,
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

        const response = await apiService.login(this.loginForm.email, this.loginForm.password)
       
        await this.handleLoginSuccess(response)

      } catch (error) {
        console.error('Login error:', error)
        this.error = error.message || 'An error occurred during login'
      } finally {
        this.loading = false
      }
    },

    async handleLoginSuccess(data) {
      this.successMessage = 'Login successful! Redirecting...'
      
      // Store authentication data in localStorage
      if (data.access_token) {
        localStorage.setItem('authToken', data.access_token)
      }

      if (data.user) {
        localStorage.setItem('userData', JSON.stringify(data.user))
        localStorage.setItem('userRole', data.user.role)
      }

      // Store login timestamp
      localStorage.setItem('loginTime', new Date().toISOString())

      console.log('Login successful:', data)

      // Navigate to dashboard using Vue Router
      setTimeout(() => {
        this.$router.push('/dashboard')  // THIS IS WHERE THE NAVIGATION HAPPENS
          .then(() => {
            console.log('Successfully navigated to dashboard')
          })
          .catch((error) => {
            console.error('Navigation error:', error)
            // Fallback: try to navigate to home
            this.$router.push('/home')
          })
      }, 1500) // Show success message for a bit longer
    },

    async handleLogout() {
      try {
        await apiService.logout()
      } catch (error) {
        console.error('Logout error:', error)
      }

      // Clear stored data
      localStorage.removeItem('authToken')
      localStorage.removeItem('userData')
      localStorage.removeItem('userRole')
      localStorage.removeItem('loginTime')
      
      // Reset form
      this.loginForm = { email: '', password: '' }
      this.error = null
      this.successMessage = null
      
      // Navigate back to login
      this.$router.push('/login')
      
      console.log('User logged out successfully')
    },

    handleForgotPassword() {
      // Show available demo credentials instead of actual forgot password
      alert('Please contact your administrator to reset your password.')
    },

    // Method to check if user is authenticated
    isAuthenticated() {
      const token = localStorage.getItem('authToken')
      return !!token
    },

    // Method to get stored user data
    getUserData() {
      const userData = localStorage.getItem('userData')
      return userData ? JSON.parse(userData) : null
    },

    // Method to get auth token
    getAuthToken() {
      return localStorage.getItem('authToken')
    }
  },

  mounted() {
    // Check if user is already authenticated
    if (this.isAuthenticated()) {
      const userData = this.getUserData()
      const userRole = userData?.role?.toLowerCase()
      
      if (userRole === 'admin') {
        this.$router.push('/admin/dashboard')
      } else if (userRole === 'employee') {
        this.$router.push('/pos/dashboard')
      } else {
        this.$router.push('/dashboard')
      }
    }
    
    console.log('Backend-integrated login component mounted')
  }
}
</script>

<style scoped>
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

/* Demo Credentials Section */
.demo-credentials {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
  font-size: 0.875rem;
  color: #64748b;
  text-align: center;
}

.demo-credentials h4 {
  margin: 0 0 0.5rem 0;
  color: #374151;
}

.demo-credentials p {
  margin: 0.25rem 0;
}

.demo-button {
  background-color: #10b981;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  cursor: pointer;
  margin-top: 0.5rem;
  transition: background-color 0.2s ease;
}

.demo-button:hover {
  background-color: #059669;
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