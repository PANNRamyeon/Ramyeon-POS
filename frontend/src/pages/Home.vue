<template>
  <div class="dashboard-page">
    <!-- Debug - remove after testing -->
  <!--  <div style="background: green; color: white; padding: 10px; margin-bottom: 10px;">
      DASHBOARD COMPONENT LOADED
    </div> Pwede rani ma remove, this is for debugging for me -Aliser-->
    
    <!-- Content Area -->
    <div class="dashboard-content">
      <!-- Top Stats Cards using KPI Component -->
      <div class="stats-section">
        <KpiCard
          title="Total Revenue"
          :value="'₱26,145'"
          subtitle="This month's total earnings"
          change=""
          changeType="positive"
          variant="profit"
        />
        
        <KpiCard
          title="Total Orders"
          :value="1039"
          subtitle="Orders processed this month"
          change=""
          changeType="positive"
          variant="orders"
        />
      </div>

      <!-- Main Content Grid -->
      <div class="content-grid">
        <!-- Left Column - Ordered Items Table -->
        <div class="content-section table-section">
          <h2>Ordered Items</h2>
          <div class="table-container">
            <table class="items-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Orders</th>
                  <th>PPU</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in orderedItems" :key="item.id">
                  <td>
                    <div class="item-info">
                      <div class="item-icon">🍜</div>
                      <span>{{ item.name }}</span>
                    </div>
                  </td>
                  <td>{{ item.orders }}</td>
                  <td>₱{{ item.ppu }}</td>
                  <td>₱{{ item.revenue }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Right Column - Statistics Charts -->
        <div class="content-section charts-section">
          <h2>Overall Statistics</h2>
          
          <!-- Time Period Tabs -->
          <div class="time-tabs">
            <button 
              v-for="period in timePeriods" 
              :key="period"
              :class="['tab', { active: activePeriod === period }]"
              @click="activePeriod = period"
            >
              {{ period }}
            </button>
          </div>

          <!-- Chart Sections -->
          <div class="chart-sections">
            <!-- Noodles Chart -->
            <div class="chart-item">
              <div class="chart-header">
                <div class="chart-icon">🍜</div>
                <span>Noodles</span>
              </div>
              <div class="chart-placeholder">
                <div class="bars">
                  <div class="bar" style="height: 40%"></div>
                  <div class="bar" style="height: 60%"></div>
                  <div class="bar" style="height: 80%"></div>
                  <div class="bar" style="height: 70%"></div>
                </div>
                <div class="chart-labels">
                  <span>Week 1</span>
                  <span>Week 2</span>
                  <span>Week 3</span>
                  <span>Week 4</span>
                </div>
              </div>
              <div class="chart-legend">
                <div class="legend-item"><span class="legend-color noodle1"></span>Noodle 1</div>
                <div class="legend-item"><span class="legend-color noodle2"></span>Noodle 4</div>
                <div class="legend-item"><span class="legend-color noodle3"></span>Noodle 2</div>
              </div>
            </div>

            <!-- Drinks Chart -->
            <div class="chart-item">
              <div class="chart-header">
                <div class="chart-icon">🥤</div>
                <span>Drinks</span>
              </div>
              <div class="chart-placeholder">
                <div class="bars">
                  <div class="bar" style="height: 35%"></div>
                  <div class="bar" style="height: 70%"></div>
                  <div class="bar" style="height: 60%"></div>
                  <div class="bar" style="height: 85%"></div>
                </div>
                <div class="chart-labels">
                  <span>Week 1</span>
                  <span>Week 2</span>
                  <span>Week 3</span>
                  <span>Week 4</span>
                </div>
              </div>
              <div class="chart-legend">
                <div class="legend-item"><span class="legend-color drink1"></span>Drink 2</div>
                <div class="legend-item"><span class="legend-color drink2"></span>Drink 3</div>
                <div class="legend-item"><span class="legend-color drink3"></span>Drink 1</div>
              </div>
            </div>

            <!-- Toppings Chart -->
            <div class="chart-item">
              <div class="chart-header">
                <div class="chart-icon">🧄</div>
                <span>Toppings</span>
              </div>
              <div class="chart-placeholder">
                <div class="bars">
                  <div class="bar" style="height: 45%"></div>
                  <div class="bar" style="height: 55%"></div>
                  <div class="bar" style="height: 75%"></div>
                  <div class="bar" style="height: 65%"></div>
                </div>
                <div class="chart-labels">
                  <span>Week 1</span>
                  <span>Week 2</span>
                  <span>Week 3</span>
                  <span>Week 4</span>
                </div>
              </div>
              <div class="chart-legend">
                <div class="legend-item"><span class="legend-color topping1"></span>Topping 1</div>
                <div class="legend-item"><span class="legend-color topping2"></span>Topping 2</div>
                <div class="legend-item"><span class="legend-color topping3"></span>Topping 3</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import KpiCard from '@/components/KPICard.vue'

export default {
  name: 'Dashboard',
  components: {
    KpiCard
  },
  data() {
    return {
      activePeriod: 'This week',
      timePeriods: ['This week', 'This month', 'This year'],
      orderedItems: [
        { id: 1, name: 'Noodle 1', orders: 42, ppu: 100, revenue: 4200 },
        { id: 2, name: 'Noodle 2', orders: 37, ppu: 100, revenue: 3700 },
        { id: 3, name: 'Noodle 3', orders: 28, ppu: 110, revenue: 3080 },
        { id: 4, name: 'Noodle 4', orders: 44, ppu: 90, revenue: 3960 },
        { id: 5, name: 'Drink 1', orders: 31, ppu: 115, revenue: 3565 },
        { id: 6, name: 'Drink 2', orders: 64, ppu: 60, revenue: 3840 },
        { id: 7, name: 'Drink 3', orders: 76, ppu: 50, revenue: 3800 }
      ]
    }
  },
  mounted() {
    console.log('Dashboard page loaded with KPI cards')
  }
}
</script>

<style scoped>
/* Add CSS variables that your KPI card needs */
:root {
  --primary: #6f42c1;
  --primary-light: rgba(111, 66, 193, 0.1);
  --primary-medium: #8b5cf6;
  --success: #10b981;
  --success-light: rgba(16, 185, 129, 0.1);
  --success-dark: #047857;
  --secondary: #f59e0b;
  --secondary-light: rgba(245, 158, 11, 0.1);
  --info: #3b82f6;
  --info-light: rgba(59, 130, 246, 0.1);
  --error: #ef4444;
  --error-light: rgba(239, 68, 68, 0.1);
  --error-dark: #dc2626;
  --neutral: #6b7280;
  --neutral-light: rgba(107, 114, 128, 0.1);
  --neutral-dark: #374151;
}

.dashboard-page {
  background-color: #f8f9fa;
  min-height: 100%;
  width: 100%;
}

.dashboard-content {
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

/* Stats Section - now uses KPI cards */
.stats-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 2rem;
}

.content-section {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.content-section h2 {
  margin: 0 0 1.5rem 0;
  color: #495057;
  font-size: 1.25rem;
  font-weight: 600;
}

/* Table Styles */
.table-container {
  overflow-x: auto;
}

.items-table {
  width: 100%;
  border-collapse: collapse;
}

.items-table th {
  text-align: left;
  padding: 0.75rem;
  border-bottom: 2px solid #e9ecef;
  color: #6c757d;
  font-weight: 600;
  font-size: 0.875rem;
}

.items-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #f8f9fa;
  color: #495057;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.item-icon {
  width: 32px;
  height: 32px;
  background: #f8f9fa;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

/* Charts Section */
.charts-section {
  display: flex;
  flex-direction: column;
}

.time-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.tab {
  padding: 0.5rem 1rem;
  border: 1px solid #e9ecef;
  background: white;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: #6c757d;
  transition: all 0.2s ease;
}

.tab.active {
  background: #6f42c1;
  color: white;
  border-color: #6f42c1;
}

.chart-sections {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.chart-item {
  border: 1px solid #f8f9fa;
  border-radius: 0.75rem;
  padding: 1rem;
  background: #fefefe;
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-weight: 500;
  color: #495057;
}

.chart-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  margin-bottom: 1rem;
}

.bars {
  display: flex;
  align-items: end;
  gap: 0.5rem;
  height: 80px;
  margin-bottom: 0.5rem;
}

.bar {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 0.25rem 0.25rem 0 0;
  min-height: 10px;
}

.chart-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #6c757d;
}

.chart-legend {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #6c757d;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.noodle1 { background: #667eea; }
.noodle2 { background: #764ba2; }
.noodle3 { background: #f093fb; }
.drink1 { background: #667eea; }
.drink2 { background: #764ba2; }
.drink3 { background: #f093fb; }
.topping1 { background: #667eea; }
.topping2 { background: #764ba2; }
.topping3 { background: #f093fb; }

/* Responsive Design */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-section {
    order: -1;
  }
}

@media (max-width: 768px) {
  .stats-section {
    grid-template-columns: 1fr;
  }
}
</style>