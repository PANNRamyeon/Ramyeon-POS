<template>
<div class="settings-container">
  <div class="contents-section">
    <h1>Profile Settings</h1>
    
    <!-- Show error messages -->
    <div v-if="errorMessage" class="alert alert-error">
      <span>{{ errorMessage }}</span>
      <button class="close-btn" @click="errorMessage = ''">×</button>
    </div>
    
    <!-- Success message -->
    <div v-if="successMessage" class="alert alert-success">
      <span>{{ successMessage }}</span>
      <button class="close-btn" @click="successMessage = ''">×</button>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading user data...</p>
    </div>
    
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="loadUserData()" class="btn btn-secondary">Retry</button>
    </div>
    
    <div v-else class="settings-content">
      <!-- Profile Information Section -->
      <div class="settings-section">
        <div class="section-header">
          <h2>Profile Information</h2>
          <button type="button" class="btn btn-primary" @click="toggleEditProfile">
            {{ isEditingProfile ? 'Cancel' : 'Edit Profile' }}
          </button>
        </div>
        
        <div class="profile-info">
          <div class="info-row">
            <label>Full Name</label>
            <input 
              v-if="isEditingProfile"
              class="form-control" 
              type="text" 
              v-model="editForm.full_name"
              placeholder="Enter full name"
            />
            <span v-else class="info-value">{{ user.full_name || 'Not set' }}</span>
          </div>
          
          <div class="info-row">
            <label>Username</label>
            <input 
              v-if="isEditingProfile"
              class="form-control" 
              type="text" 
              v-model="editForm.username"
              placeholder="Enter username"
            />
            <span v-else class="info-value">{{ user.username }}</span>
          </div>
          
          <div class="info-row">
            <label>Email</label>
            <input 
              v-if="isEditingProfile"
              class="form-control" 
              type="email" 
              v-model="editForm.email"
              placeholder="Enter email"
            />
            <span v-else class="info-value">{{ user.email }}</span>
          </div>
          
          <div class="info-row">
            <label>Role</label>
            <span class="info-value">
              <span class="badge" :class="getRoleBadgeClass(user.role)">
                {{ formatRole(user.role) }}
              </span>
            </span>
          </div>
          
          <div class="info-row">
            <label>Status</label>
            <span class="info-value">
              <span class="badge" :class="getStatusBadgeClass(user.status)">
                {{ formatStatus(user.status) }}
              </span>
            </span>
          </div>
          
          <div v-if="isEditingProfile" class="action-buttons">
            <button type="button" class="btn btn-secondary" @click="cancelProfileEdit">
              Cancel
            </button>
            <button type="button" class="btn btn-primary" @click="saveProfileChanges">
              Save Changes
            </button>
          </div>
        </div>
      </div>
      
      <!-- Change Password Section -->
      <div class="settings-section">
        <div class="section-header">
          <h2>Change Password</h2>
          <button type="button" class="btn btn-primary" @click="toggleEditPassword">
            {{ isEditingPassword ? 'Cancel' : 'Change Password' }}
          </button>
        </div>
        
        <form v-if="isEditingPassword" class="password-form" @submit.prevent="handlePasswordUpdate">
          <div class="form-group">
            <label>Current Password</label>
            <input 
              class="form-control" 
              type="password" 
              placeholder="Enter current password" 
              v-model="passwordForm.currentPassword" 
              @input="clearErrors"
            />
          </div>
          
          <div class="form-group">
            <label>New Password</label>
            <input 
              class="form-control" 
              type="password" 
              placeholder="Enter new password" 
              v-model="passwordForm.newPassword" 
              @input="clearErrors"
            />
            <small class="form-text">Password must be at least 6 characters</small>
          </div>
          
          <div class="form-group">
            <label>Confirm New Password</label>
            <input 
              class="form-control" 
              type="password" 
              placeholder="Confirm new password" 
              v-model="passwordForm.confirmPassword" 
              @input="validatePasswordMatch"
              :class="{ 'is-invalid': passwordMismatch && passwordForm.confirmPassword }"
            />
            
            <!-- Show password match indicator -->
            <div v-if="passwordForm.confirmPassword" class="password-feedback">
              <span v-if="passwordMismatch" class="text-danger">
                <X :size="14" /> Passwords do not match
              </span>
              <span v-else class="text-success">
                <Check :size="14" /> Passwords match
              </span>
            </div>
          </div>
          
          <div class="action-buttons">
            <button type="button" class="btn btn-secondary" @click="cancelPasswordChange">
              Cancel
            </button>
            <button type="submit" class="btn btn-primary" :disabled="!isPasswordFormValid">
              Update Password
            </button>
          </div>
        </form>
        
        <div v-else class="password-placeholder">
          <p>Click "Change Password" to update your password</p>
        </div>
      </div>
      
      <!-- Theme Section -->
      <div class="settings-section">
        <div class="section-header">
          <h2>Appearance</h2>
        </div>
        
        <div class="theme-content">
          <div class="theme-option">
            <div class="theme-info">
              <h3>Dark Mode</h3>
              <p>Switch between light and dark theme</p>
            </div>
            <div class="form-check form-switch">
              <input 
                class="form-check-input" 
                type="checkbox" 
                role="switch" 
                id="switchCheckChecked" 
                @change="toggleDark" 
                v-model="darkMode"
              >
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script>
import apiSettings from '@/services/apiSettings';

export default {
  name: 'Settings',
  data() {
    return {
      isEditingProfile: false,
      isEditingPassword: false,
      darkMode: false,
      loading: true,
      error: null,
      errorMessage: '',
      successMessage: '',
      passwordMismatch: false,
      user: {
        id: '',
        email: '',
        username: '',
        full_name: '',
        role: '',
        status: ''
      },
      editForm: {
        full_name: '',
        username: '',
        email: ''
      },
      passwordForm: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
    }
  },
  computed: {
    isPasswordFormValid() {
      return this.passwordForm.currentPassword &&
             this.passwordForm.newPassword &&
             this.passwordForm.confirmPassword &&
             !this.passwordMismatch &&
             this.passwordForm.newPassword.length >= 6;
    }
  },
  methods: {
    toggleEditProfile() {
      this.isEditingProfile = !this.isEditingProfile;
      if (this.isEditingProfile) {
        // Copy current user data to edit form
        this.editForm = {
          full_name: this.user.full_name,
          username: this.user.username,
          email: this.user.email
        };
      }
    },
    
    toggleEditPassword() {
      this.isEditingPassword = !this.isEditingPassword;
      if (!this.isEditingPassword) {
        this.resetPasswordForm();
      }
    },
    
    cancelProfileEdit() {
      this.isEditingProfile = false;
      this.editForm = {
        full_name: this.user.full_name,
        username: this.user.username,
        email: this.user.email
      };
    },
    
    cancelPasswordChange() {
      this.isEditingPassword = false;
      this.resetPasswordForm();
    },
    
    resetPasswordForm() {
      this.passwordForm = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      };
      this.passwordMismatch = false;
      this.clearErrors();
    },
    
    async saveProfileChanges() {
      try {
        this.errorMessage = '';
        this.successMessage = '';
        
        // Validate form
        if (!this.editForm.username || !this.editForm.email) {
          this.errorMessage = 'Username and email are required';
          return;
        }
        
        const updateData = {
          username: this.editForm.username,
          email: this.editForm.email,
          full_name: this.editForm.full_name,
          role: this.user.role,
          status: this.user.status
        };
        
        const result = await apiSettings.updateUser(this.user.id, updateData);
        
        // Update local user data
        this.user.full_name = this.editForm.full_name;
        this.user.username = this.editForm.username;
        this.user.email = this.editForm.email;
        
        this.successMessage = 'Profile updated successfully';
        this.isEditingProfile = false;
        
        // Clear success message after 3 seconds
        setTimeout(() => {
          this.successMessage = '';
        }, 3000);
        
      } catch (error) {
        console.error('Profile update error:', error);
        this.errorMessage = error.message;
      }
    },
    
    toggleDark() {
      this.darkMode = !this.darkMode;

      if (this.darkMode) {
        document.body.classList.add('dark-mode');
        document.documentElement.setAttribute('data-theme', 'dark');
      } else {
        document.body.classList.remove('dark-mode');
        document.documentElement.setAttribute('data-theme', 'light');
      }
      
      // Save preference to localStorage
      localStorage.setItem('darkMode', this.darkMode);
    },
    
    async loadUserData() {
      try {
        this.loading = true;
        this.error = null;
        
        this.user = await apiSettings.getCurrentUser();
        
        // Initialize edit form with user data
        this.editForm = {
          full_name: this.user.full_name,
          username: this.user.username,
          email: this.user.email
        };
        
      } catch (error) {
        this.error = error.message;
        
        // Handle authentication errors
        if (error.message.includes('Authentication failed')) {
          this.$router.push('/login');
        }
        
      } finally {
        this.loading = false;
      }
    },
    
    clearErrors() {
      this.errorMessage = '';
    },
    
    validatePasswordMatch() {
      if (this.passwordForm.confirmPassword) {
        this.passwordMismatch = this.passwordForm.newPassword !== this.passwordForm.confirmPassword;
      }
    },
    
    validatePasswordForm() {
      this.errorMessage = '';
      
      if (!this.passwordForm.currentPassword) {
        this.errorMessage = 'Current password is required';
        return false;
      }
      
      if (!this.passwordForm.newPassword) {
        this.errorMessage = 'New password is required';
        return false;
      }
      
      if (!this.passwordForm.confirmPassword) {
        this.errorMessage = 'Please confirm your new password';
        return false;
      }
      
      if (this.passwordForm.newPassword !== this.passwordForm.confirmPassword) {
        this.errorMessage = 'New passwords do not match';
        return false;
      }
      
      if (this.passwordForm.newPassword.length < 6) {
        this.errorMessage = 'New password must be at least 6 characters';
        return false;
      }
      
      if (this.passwordForm.newPassword === this.passwordForm.currentPassword) {
        this.errorMessage = 'New password must be different from current password';
        return false;
      }
      
      return true;
    },
    
    async handlePasswordUpdate() {
      try {
        // Clear any existing messages first
        this.errorMessage = '';
        this.successMessage = '';
        
        if (!this.validatePasswordForm()) {
          return false;
        }

        const updateData = {
          username: this.user.username,
          email: this.user.email,
          full_name: this.user.full_name,
          role: this.user.role,
          status: this.user.status,
          current_password: this.passwordForm.currentPassword,
          new_password: this.passwordForm.newPassword
        };
        
        const result = await apiSettings.updateUser(this.user.id, updateData);
        
        // Reset form BEFORE showing message
        this.resetPasswordForm();
        this.isEditingPassword = false;
        
        // Show success message
        this.successMessage = result.message || 'Password updated successfully';
        
        // Clear success message after 5 seconds
        setTimeout(() => {
          this.successMessage = '';
        }, 5000);
        
        return true;
        
      } catch (error) {
        console.error('Password update error:', error);
        this.errorMessage = error.message || 'Failed to update password';
        return false;
      }
    },
    
    formatRole(role) {
      if (!role) return 'N/A';
      return role.charAt(0).toUpperCase() + role.slice(1);
    },
    
    formatStatus(status) {
      if (!status) return 'N/A';
      return status.charAt(0).toUpperCase() + status.slice(1);
    },
    
    getRoleBadgeClass(role) {
      const roleClasses = {
        'admin': 'badge-admin',
        'manager': 'badge-manager',
        'cashier': 'badge-cashier',
        'staff': 'badge-staff'
      };
      return roleClasses[role?.toLowerCase()] || 'badge-default';
    },
    
    getStatusBadgeClass(status) {
      const statusClasses = {
        'active': 'badge-active',
        'inactive': 'badge-inactive',
        'suspended': 'badge-suspended'
      };
      return statusClasses[status?.toLowerCase()] || 'badge-default';
    }
  },
  
  async mounted() {
    await this.loadUserData();
    
    // Check if dark mode was previously enabled
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'true') {
      this.darkMode = true;
      document.body.classList.add('dark-mode');
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }
}
</script>

<style scoped>
.settings-container {
  padding: 0;
  max-width: 1200px;
  margin: 0 auto;
}

.contents-section {
  background-color: var(--bg-secondary);
  border-radius: 0.75rem;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  min-height: 50vh;
}

.contents-section h1 {
  color: var(--tertiary-dark);
  font-size: 1.875rem;
  font-weight: 600;
  margin-bottom: 2rem;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.settings-section {
  background: var(--bg-light);
  border-radius: 0.5rem;
  padding: 1.5rem;
  border: 1px solid var(--neutral);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--neutral-light);
}

.section-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--tertiary-dark);
  margin: 0;
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-row {
  display: grid;
  grid-template-columns: 150px 1fr;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 0;
}

.info-row label {
  font-weight: 500;
  color: var(--tertiary-medium);
  font-size: 0.9375rem;
}

.info-value {
  color: var(--tertiary-dark);
  font-size: 0.9375rem;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.8125rem;
  font-weight: 500;
}

.badge-admin {
  background-color: var(--error-light);
  color: var(--error-dark);
}

.badge-manager {
  background-color: var(--primary-light);
  color: var(--primary-dark);
}

.badge-cashier {
  background-color: var(--success-light);
  color: var(--success-dark);
}

.badge-staff {
  background-color: var(--secondary-light);
  color: var(--secondary-dark);
}

.badge-active {
  background-color: var(--success-light);
  color: var(--success-dark);
}

.badge-inactive {
  background-color: var(--neutral-light);
  color: var(--neutral-dark);
}

.badge-suspended {
  background-color: var(--error-light);
  color: var(--error-dark);
}

.badge-default {
  background-color: var(--neutral-light);
  color: var(--tertiary-dark);
}

.password-form,
.password-placeholder {
  max-width: 500px;
}

.password-placeholder {
  padding: 2rem;
  text-align: center;
  color: var(--tertiary-medium);
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 500;
  color: var(--tertiary-dark);
  margin-bottom: 0.5rem;
  font-size: 0.9375rem;
}

.form-control {
  width: 100%;
  padding: 0.625rem 0.875rem;
  border: 1px solid var(--neutral);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(115, 146, 226, 0.1);
}

.form-control.is-invalid {
  border-color: var(--error);
}

.form-control.is-invalid:focus {
  box-shadow: 0 0 0 3px rgba(229, 57, 53, 0.1);
}

.form-text {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.8125rem;
  color: var(--tertiary-medium);
}

.password-feedback {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.text-danger {
  color: var(--error);
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.text-success {
  color: var(--success);
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.5rem 1.25rem;
  font-size: 0.9375rem;
  font-weight: 500;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-dark);
}

.btn-secondary {
  background-color: var(--neutral-medium);
  color: var(--tertiary-dark);
}

.btn-secondary:hover {
  background-color: var(--neutral-dark);
  color: white;
}

.theme-content {
  max-width: 600px;
}

.theme-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: white;
  border-radius: 0.5rem;
  border: 1px solid var(--neutral);
}

.theme-info h3 {
  font-size: 1rem;
  font-weight: 500;
  color: var(--tertiary-dark);
  margin: 0 0 0.25rem 0;
}

.theme-info p {
  font-size: 0.875rem;
  color: var(--tertiary-medium);
  margin: 0;
}

.form-check-input {
  width: 3rem;
  height: 1.5rem;
  cursor: pointer;
}

.form-check-input:checked {
  background-color: var(--primary);
  border-color: var(--primary);
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--tertiary-medium);
}

.spinner {
  border: 3px solid var(--neutral-light);
  border-top: 3px solid var(--primary);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  text-align: center;
  padding: 2rem;
  color: var(--error);
}

.error button {
  margin-top: 1rem;
}

.alert {
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
  border-radius: 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.alert-error {
  background-color: var(--error-light);
  color: var(--error-dark);
  border: 1px solid var(--error);
}

.alert-success {
  background-color: var(--success-light);
  color: var(--success-dark);
  border: 1px solid var(--success);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.close-btn:hover {
  opacity: 1;
}

/* Responsive Design */
@media (max-width: 768px) {
  .contents-section {
    padding: 1.5rem;
  }
  
  .info-row {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .info-row label {
    font-weight: 600;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .section-header .btn {
    width: 100%;
  }
}
</style>