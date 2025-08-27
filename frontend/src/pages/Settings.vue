<template>
<div class = "settings-container">
  <div class = "contents-section">
  <h1> Profile</h1>
  <div class ="edit-section">
    <div class ="edit-header">
      <h2>Jane Doe</h2>
     <button type="button" class="btn btn-primary" @click="toggleEdit">{{ isEditing ? 'Save' : 'Edit' }}</button>
    </div>
    <div class = "edit-contents">
      <h2>Change Password</h2>
      <form class = "profile-form" >
         <input class="form-control" type="text" placeholder="Current Password" aria-label="Current Password" :disabled="!isEditing"/>
        <input class="form-control" type="text" placeholder="New Password" aria-label="New Password" :disabled="!isEditing" />
        <input class="form-control" type="text" placeholder="Confirm Password" aria-label="Confirm New Password" :disabled="!isEditing" /> 
      </form>
    </div>
    <div class = "theme">
      <h2>Theme</h2>
      <div class="form-check form-switch">
        <input class="form-check-input" type="checkbox" role="switch" id="switchCheckChecked" @click="toggleDark" :checked = "darkMode">
        <label class="form-check-label" for="switchCheckChecked">Switch to Dark Mode</label>
      </div>
    </div>
  </div>
  </div>
</div>  
</template>

<script>
export default {
  name: 'Settings',
  data() {
    return {
      isEditing: false,
      darkMode: false,
    }
  },
  methods: {
    toggleEdit() {
      this.isEditing = !this.isEditing;
    },
    toggleDark() {
      this.darkMode = !this.darkMode;

      if (this.darkMode) {
        document.body.classList.add('dark-mode');
      } else {
        document.body.classList.remove('dark-mode');
      }
    }
  },
  mounted() {
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
</style>