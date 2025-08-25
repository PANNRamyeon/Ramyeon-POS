<template>
<div class = "OOheaders">
   <ul class="nav nav-underline">
  <li class="nav-item">
    <a class="nav-link" @click="handleNavigation('online-orders')">Pending</a>
  </li>
  <li class="nav-item">
    <a class="nav-link active" aria-current="page" @click="handleNavigation('complete-orders')">Complete</a>
  </li>
</ul>
</div>

</template>

<script>
export default {
  name: 'Complete Orders',
  data() {
    return {
      activeTab: 'Completed' // Set initial active tab
    };
  }
}
</script>

<style scoped>

.tab-headers button.active {
  background-color: lightblue;
}

</style>