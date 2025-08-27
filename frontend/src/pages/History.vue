<template>
  <div class = "History-container">
    <div class = "history-contents">
      <div class = "table-container">
        <table class="history-table">
          <thead>
            <tr>
              <th scope="col">ID</th>
              <th scope="col">Items</th>
              <th scope="col">Status</th>
              <th scope="col">Date</th>
              <th scope="col">Payment Method</th>
              <th scope="col">Sale Type</th>
              <th scope="col">Total</th>
              <th scope="col"></th>
            </tr>
          </thead>
          <tbody class="table-group-divider">
            <tr>
              <th scope="row">1</th>
              <td>Mark</td>
              <td>Otto</td>
              <td>@mdo</td>
              <td>@mdo</td>
              <td>@mdo</td>
              <td>@mdo</td>
              <td><button class="btn btn-outline-primary action-btn action-btn-edit" title="Edit"> <Edit :size="14" /></button></td>
            </tr>
            <tr>
              <th scope="row">2</th>
              <td>Jacob</td>
              <td>Thornton</td>
              <td>@fat</td>
              <td>@fat</td>
              <td>@fat</td>
              <td>@fat</td>
              <td><button class="btn btn-outline-primary action-btn action-btn-edit" title="Edit"> <Edit :size="14" /></button></td>
            </tr>
            <tr>
              <th scope="row">3</th>
              <td>John</td>
              <td>Doe</td>
              <td>@social</td>
              <td>@social</td>
              <td>@social</td>
              <td>@social</td>
              <td><button class="btn btn-outline-primary action-btn action-btn-edit" title="Edit"> <Edit :size="14" /></button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import {Edit } from 'lucide-vue-next'
export default {
  name: 'History',
  components:{
    Edit
  },
  data() {
    return {
    }
  }
}
</script>

<style scoped>
.History-container{
  padding: 0;
}

.history-contents{
  background: white;
  border-radius: 0.5rem;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  min-height: 100vh;
}

.table-container {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.history-table thead {
  background-color: #567cdc;
  color: white;
}

.history-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  letter-spacing: 0.025em;
  border-bottom: 1px solid #e2e8f0;
}

.history-table td {
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.875rem;
  transition: background-color 0.2s ease;
}
</style>