<template>
  <div class="online-orders-page">
    <div class = "oo-contents">
      <div class = "oo-left">

      </div>
      <div class = "oo-right">

      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'OnlineOrder',
  data() {
    return {
      activeTab: 'pending',
      pendingItems: [],
    }
  }
}
</script>

<style scoped>

.oo-contents{
  padding: 0;
  display: flex;
}

.oo-left{
  background-color: #6c757d;
  width: 75%;
  height: 100vh;
}

.oo-right{
  width: 25%;
  height: 100vh;
  background-color: #6f42c1;
}

.nav-tabs {
  display: flex;
  list-style: none;
  padding: 0;
  margin: 0;
  border-bottom: 2px solid #e9ecef;
}

.nav-item {
  margin-right: 1rem;
}

.nav-link {
  background: none;
  border: none;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  color: #6c757d;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: #495057;
}

.nav-link.active {
  color: #6f42c1;
  border-bottom-color: #6f42c1;
}

.tab-content {
   padding: 0;
}

.oocard{
  height: 120px;
  background-color: white;
  text-align: left;
  width: 100%;  
  border-radius: 10px;
  margin-top: 15px;
  border-style: solid;
  border-width: 2px;
}

.cardtop{
  display: flex;
  margin-top: 5px;
  margin-left: 10px;
}
.cardbot{
  margin-top: 32px;
  display: flex;
  margin-left: 10px;
}
.cardtop h1, .cardbot h1{
  font-size: 25px;
}
.cardtop h2{
  font-size: 20px;
}

.cardbot h2{
  font-size: 15px;
  margin-top: 10px;
}



</style>