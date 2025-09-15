<template>
<div class="settings-container">
  <div class="surface-primary shadow-lg transition-theme">
    <div class="page-header border-bottom-theme">
      <h1 class="text-primary">Profile</h1>
    </div>
    
    <!-- Show error messages -->
    <div v-if="errorMessage" class="status-error transition-theme">
      {{ errorMessage }}
    </div>
    
    <!-- Success message -->
    <div v-if="successMessage" class="status-success transition-theme">
      {{ successMessage }}
    </div>
    
    <div v-if="loading" class="loading-state">
      <p class="text-secondary">Loading user data...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <p class="text-error">{{ error }}</p>
      <button @click="loadUserData()" class="btn btn-secondary">Retry</button>
    </div>
    
    <div v-else class="edit-section">
      <div class="edit-header">
        <h2 class="text-primary">{{ user.full_name || user.username || user.email || 'Loading...' }}</h2>
        <button type="button" class="btn btn-primary transition-theme" @click="toggleEdit">
          {{ isEditing ? 'Save' : 'Edit' }}
        </button>
      </div>
      
      <div class="edit-contents">
        <h2 class="text-secondary">Change Password</h2>
        <form class="profile-form" @submit.prevent="handlePasswordUpdate">
          <input 
            class="input-complete transition-theme" 
            type="password" 
            placeholder="Current Password" 
            v-model="passwordForm.currentPassword" 
            aria-label="Current Password" 
            :disabled="!isEditing"
            @input="clearErrors"
          />
          
          <input 
            class="input-complete transition-theme" 
            type="password" 
            placeholder="New Password" 
            v-model="passwordForm.newPassword" 
            aria-label="New Password" 
            :disabled="!isEditing"
            @input="clearErrors"
          />
          
          <input 
            class="input-complete transition-theme" 
            type="password" 
            placeholder="Confirm Password" 
            v-model="passwordForm.confirmPassword" 
            aria-label="Confirm New Password" 
            :disabled="!isEditing"
            @input="validatePasswordMatch"
            :class="{ 'border-error': passwordMismatch }"
          />
        </form>
        
        <!-- Move password feedback outside the form -->
        <div v-if="passwordForm.confirmPassword && isEditing" class="password-feedback">
          <span v-if="passwordMismatch" class="text-error">
            Passwords do not match
          </span>
          <span v-else class="text-success">
            Passwords match
          </span>
        </div>
      </div>
      
      <!-- Theme section -->
      <div class="theme-section">
        <h2 class="text-secondary">Theme</h2>
        <div class="theme-toggle">
          <div class="toggle-container">
            <span class="toggle-label">{{ isDarkMode ? 'Dark Mode' : 'Light Mode' }}</span>
            <div 
              class="custom-toggle"
              :class="{ 'active': isDarkMode }"
              @click="toggleDark"
              :title="isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
            >
              <div class="toggle-track"></div>
              <div class="toggle-thumb"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script>
import apiSettings from '@/services/apiSettings'

export default {
  name: 'Settings',
  data() {
    return {
      isEditing: false,
      loading: true,
      error: null,
      errorMessage: '',
      successMessage: '',
      passwordMismatch: false,
      isDarkMode: false, // Changed to reactive data property
      user: {
        id: '',
        email: '',
        username: '',
        full_name: '',
        role: '',
        status: ''
      },
      passwordForm: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
    }
  },
  methods: {
    async toggleEdit() {
      if (this.isEditing) {
        await this.saveChanges()
      } else {
        this.isEditing = true
      }
    },
    
    toggleDark() {
      console.log('toggleDark called')
      
      const currentTheme = document.documentElement.getAttribute('data-theme')
      console.log('Current theme before toggle:', currentTheme)
      
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark'
      console.log('New theme will be:', newTheme)
      
      // Set the theme
      document.documentElement.setAttribute('data-theme', newTheme)
      
      // Update reactive data property
      this.isDarkMode = newTheme === 'dark'
      
      // Save preference
      localStorage.setItem('theme', newTheme)
      
      console.log('Theme updated - isDarkMode:', this.isDarkMode, 'newTheme:', newTheme)
    },
    
    clearErrors() {
      this.errorMessage = ''
      this.successMessage = ''
    },
    
    validatePasswordMatch() {
      this.passwordMismatch = this.passwordForm.newPassword !== this.passwordForm.confirmPassword
      this.clearErrors()
    },
    
    async loadUserData() {
      try {
        this.loading = true
        this.error = null
        
        this.user = await apiSettings.getCurrentUser()
        
      } catch (error) {
        this.error = error.message
        
        if (error.message.includes('Authentication failed')) {
          this.$router.push('/login')
        }
        
      } finally {
        this.loading = false
      }
    },
    
    validatePasswordForm() {
      this.errorMessage = ''
      
      if (!this.passwordForm.currentPassword) {
        this.errorMessage = 'Current password is required'
        return false
      }
      
      if (!this.passwordForm.newPassword) {
        this.errorMessage = 'New password is required'
        return false
      }
      
      if (!this.passwordForm.confirmPassword) {
        this.errorMessage = 'Please confirm your new password'
        return false
      }
      
      if (this.passwordForm.newPassword !== this.passwordForm.confirmPassword) {
        this.errorMessage = 'New passwords do not match'
        return false
      }
      
      if (this.passwordForm.newPassword.length < 6) {
        this.errorMessage = 'New password must be at least 6 characters'
        return false
      }
      
      if (this.passwordForm.newPassword === this.passwordForm.currentPassword) {
        this.errorMessage = 'New password must be different from current password'
        return false
      }
      
      return true
    },
    
    async handlePasswordUpdate() {
      try {
        if (!this.validatePasswordForm()) {
          return false
        }

        const updateData = {
          username: this.user.username,
          email: this.user.email,
          full_name: this.user.full_name,
          role: this.user.role,
          status: this.user.status,
          current_password: this.passwordForm.currentPassword,
          new_password: this.passwordForm.newPassword
        }

        const result = await apiSettings.updateUser(this.user.id, updateData)
        
        this.passwordForm = {
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        }
        
        this.successMessage = result.message || 'Password updated successfully'
        return true
        
      } catch (error) {
        console.error('Password update error:', error)
        this.errorMessage = error.message
        return false
      }
    },
    
    async saveChanges() {
      try {
        if (this.passwordForm.newPassword || this.passwordForm.currentPassword) {
          await this.handlePasswordUpdate()
        }
        
        this.isEditing = false
        
      } catch (error) {
        console.error('Error saving changes:', error)
        alert(`Failed to save changes: ${error.message}`)
      }
    }
  },
  
  async mounted() {
    console.log('Settings component mounted')
    
    await this.loadUserData()
    
    // Load saved theme preference and set reactive property
    const savedTheme = localStorage.getItem('theme')
    console.log('Saved theme from localStorage:', savedTheme)
    
    if (savedTheme) {
      document.documentElement.setAttribute('data-theme', savedTheme)
      this.isDarkMode = savedTheme === 'dark'
      console.log('Applied saved theme:', savedTheme, 'isDarkMode:', this.isDarkMode)
    } else {
      // Check current theme attribute
      const currentTheme = document.documentElement.getAttribute('data-theme')
      this.isDarkMode = currentTheme === 'dark'
      console.log('No saved theme, using current:', currentTheme, 'isDarkMode:', this.isDarkMode)
    }
  }
}
</script>

<style scoped>
.surface-primary {
  border-radius: 1rem;
  overflow: hidden;
}

.settings-container {
  padding: 1.5rem;
  background-color: var(--surface-tertiary);
  min-height: 100vh;
}

.page-header {
  padding: 2rem 2rem 1rem 2rem;
}

.edit-section {
  padding: 1rem 2rem 2rem 2rem;
}

.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.edit-contents {
  margin-bottom: 2rem;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 400px;
  margin-top: 1rem;
}

.profile-form input {
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 0;
}

.password-feedback {
  margin-top: 0.5rem;
  font-size: 0.875rem;
}

.theme-section {
  border-top: 1px solid var(--border-secondary);
  padding-top: 2rem;
}

.theme-toggle {
  margin-top: 1rem;
}

.toggle-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.toggle-label {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.custom-toggle {
  position: relative;
  width: 48px;
  height: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-track {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--neutral-medium);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background-color: var(--surface-primary);
  border-radius: 50%;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-sm);
}

.custom-toggle.active .toggle-track {
  background-color: var(--secondary-medium);
}

.custom-toggle.active .toggle-thumb {
  transform: translateX(24px);
  background-color: var(--secondary-dark);
}

.custom-toggle:hover .toggle-track {
  opacity: 0.8;
}

.custom-toggle:hover .toggle-thumb {
  box-shadow: var(--shadow-md);
}

.toggle-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 0.5rem;
  border: none;
  background-color: transparent;
  color: var(--text-primary);
  cursor: pointer;
  padding: 0;
  outline: none;
}

.toggle-icon-btn:hover {
  background-color: transparent;
}

.toggle-icon-btn:active {
  background-color: transparent;
}

.toggle-icon-btn:focus {
  outline: none;
  box-shadow: none;
}

.toggle-icon-btn.dark-active {
  background-color: var(--surface-secondary);
  border-radius: 0.75rem;
}

.loading-state, .error-state {
  text-align: center;
  padding: 4rem 2rem;
}

.password-feedback {
  margin-top: 0.25rem;
  font-size: 0.875rem;
}

/* Responsive */
@media (max-width: 768px) {
  .settings-container {
    padding: 1.5rem;
    background-color: var(--surface-tertiary);
    min-height: 100vh;
  }
  
  .edit-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .profile-form {
    flex-direction: column;
  }

  .profile-form input {
    min-width: 100%;
  }
}
</style>