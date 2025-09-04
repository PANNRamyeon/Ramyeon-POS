<template>
<div class="settings-container">
  <div class="contents-section">
    <h1>Profile</h1>
    
    <!-- Show error messages -->
    <div v-if="errorMessage" class="alert alert-error">
      {{ errorMessage }}
    </div>
    
    <!-- Success message -->
    <div v-if="successMessage" class="alert alert-success">
      {{ successMessage }}
    </div>
    
    <div v-if="loading" class="loading">
      <p>Loading user data...</p>
    </div>
    
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="loadUserData()" class="btn btn-secondary">Retry</button>
    </div>
    
    <div v-else class="edit-section">
      <div class="edit-header">
        <h2>{{ user.full_name || user.username || user.email || 'Loading...' }}</h2>
        <button type="button" class="btn btn-primary" @click="toggleEdit">
          {{ isEditing ? 'Save' : 'Edit' }}
        </button>
      </div>
      
      <div class="edit-contents">
        <h2>Change Password</h2>
        <form class="profile-form" @submit.prevent="handlePasswordUpdate">
          <input 
            class="form-control" 
            type="password" 
            placeholder="Current Password" 
            v-model="passwordForm.currentPassword" 
            aria-label="Current Password" 
            :disabled="!isEditing"
            @input="clearErrors"
          />
          
          <input 
            class="form-control" 
            type="password" 
            placeholder="New Password" 
            v-model="passwordForm.newPassword" 
            aria-label="New Password" 
            :disabled="!isEditing"
            @input="clearErrors"
          />
          
          <input 
            class="form-control" 
            type="password" 
            placeholder="Confirm Password" 
            v-model="passwordForm.confirmPassword" 
            aria-label="Confirm New Password" 
            :disabled="!isEditing"
            @input="validatePasswordMatch"
            :class="{ 'is-invalid': passwordMismatch }"
          />
          
          <!-- Show password match indicator -->
          <div v-if="passwordForm.confirmPassword && isEditing" class="password-feedback">
            <span v-if="passwordMismatch" class="text-danger">
              Passwords do not match
            </span>
            <span v-else class="text-success">
              Passwords match
            </span>
          </div>
        </form>
      </div>
      
      <!-- Theme section stays the same -->
      <div class="theme">
        <h2>Theme</h2>
        <div class="form-check form-switch">
          <input 
            class="form-check-input" 
            type="checkbox" 
            role="switch" 
            id="switchCheckChecked" 
            @click="toggleDark" 
            :checked="darkMode"
          >
          <label class="form-check-label" for="switchCheckChecked">
            Switch to Dark Mode
          </label>
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
      isEditing: false,
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
        // When switching from edit to view mode, save changes
        await this.saveChanges();
      } else {
        // When switching to edit mode, just enable editing
        this.isEditing = true;
      }
    },
    toggleDark() {
      this.darkMode = !this.darkMode;

      if (this.darkMode) {
        document.body.classList.add('dark-mode');
      } else {
        document.body.classList.remove('dark-mode');
      }
    },
    async loadUserData() {
      try {
        this.loading = true;
        this.error = null;
        
        this.user = await apiSettings.getCurrentUser();
        
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
    validatePasswordForm() {
      // Clear any previous error messages
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
      
      // Optional: Check if new password is same as current password
      if (this.passwordForm.newPassword === this.passwordForm.currentPassword) {
        this.errorMessage = 'New password must be different from current password';
        return false;
      }
      
      return true;
    },
    async handlePasswordUpdate() {
      try {
        if (!this.validatePasswordForm()) {
          return false;
        }

        // Create update data with current user info + password verification
        const updateData = {
          username: this.user.username,
          email: this.user.email,
          full_name: this.user.full_name,
          role: this.user.role,
          status: this.user.status,
          current_password: this.passwordForm.currentPassword,
          new_password: this.passwordForm.newPassword
        };

        // Use the single updateUser method
        const result = await apiSettings.updateUser(this.user.id, updateData);
        
        // Clear password form
        this.passwordForm = {
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        };
        
        this.successMessage = result.message || 'Password updated successfully';
        return true;
        
      } catch (error) {
        console.error('Password update error:', error);
        this.errorMessage = error.message;
        return false;
      }
    },
    async saveChanges() {
     try {
        // Save password changes if any fields are filled
        if (this.passwordForm.newPassword || this.passwordForm.currentPassword) {
          await this.handlePasswordUpdate();
        }
        
        // Only switch back to view mode if save was successful
        this.isEditing = false;
        
      } catch (error) {
        // Don't switch back to view mode if there was an error
        console.error('Error saving changes:', error);
        alert(`Failed to save changes: ${error.message}`);
      }
    },
    

  },
  async mounted() {
    await this.loadUserData();
    // Check if dark mode was previously enabled (optional)
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'true') {
      this.darkMode = true;
      document.body.classList.add('dark-mode');
    }

    
  }
}
</script>

<style scoped>
.setting-container{
 padding: 0;
}

.contents-section{
  background-color: white;
  background: white;
  border-radius: 0.5rem;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  min-height: 50vh;
}

.contents-section h1{
  color: grey;
}

.edit-header{
  display: flex;
  gap: 30px;

}

.edit-header h2{
  font-size: 25px;
  margin: 0;
}

.btn{
  font-size: 15px;
  height: 30px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.edit-contents{
  margin-top: 30px;
}
.edit-contents h2{
  font-size: 20px;
  color: grey;
}

.profile-form{
  width: 30%;
}

.form-control{
  margin-bottom: 10px;
}
.theme{
  margin-top: 30px;
}
.theme h2{
  font-size: 20px;
  color: grey;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  text-align: center;
  padding: 2rem;
  color: #dc3545;
}

.error button {
  margin-top: 1rem;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.alert {
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  border-radius: 0.375rem;
}

.alert-error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.alert-success {
  background-color: #d1edff;
  color: #0f5132;
  border: 1px solid #badbcc;
}

.form-control.is-invalid {
  border-color: #dc3545;
}

.password-feedback {
  margin-top: 0.25rem;
  font-size: 0.875rem;
}

.text-danger {
  color: #dc3545;
}

.text-success {
  color: #198754;
}
</style>