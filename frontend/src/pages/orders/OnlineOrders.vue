<template>
<div class = "OOheaders">
   <ul class="nav nav-underline">
  <li class="nav-item">
    <a class="nav-link active" aria-current="page" @click="handleNavigation('online-orders')" >Pending</a>
  </li>
  <li class="nav-item">
    <a class="nav-link" @click="handleNavigation('complete-orders')" href = #>Complete</a>
  </li>
</ul>
</div>

</template>

<script>
export default {
  name: 'Online Orders',
  data() {
    return {
      activeTab: 'Pending' 
    };
  }
}
</script>

<style scoped>

.tab-headers button.active {
  background-color: lightblue;
}

</style>