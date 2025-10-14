<template>
  <div class="dashboard-page surface-secondary transition-theme">
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
        <div class="content-section surface-primary border-theme shadow-md transition-theme">
          <h2 class="text-primary">Ordered Items</h2>
          <div class="table-container">
            <table class="items-table">
              <thead>
                <tr>
                  <th class="text-secondary border-bottom-theme">Item</th>
                  <th class="text-secondary border-bottom-theme">Orders</th>
                  <th class="text-secondary border-bottom-theme">PPU</th>
                  <th class="text-secondary border-bottom-theme">Revenue</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in orderedItems" :key="item.id" class="hover-surface">
                  <td class="border-theme-subtle">
                    <div class="item-info">
                      <div class="item-icon surface-tertiary">🍜</div>
                      <span class="text-primary">{{ item.name }}</span>
                    </div>
                  </td>
                  <td class="text-primary border-theme-subtle">{{ item.orders }}</td>
                  <td class="text-primary border-theme-subtle">₱{{ item.ppu }}</td>
                  <td class="text-primary border-theme-subtle">₱{{ item.revenue }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Right Column - Statistics Charts -->
        <div class="content-section surface-primary border-theme shadow-md transition-theme">
          <h2 class="text-primary">Overall Statistics</h2>
          
          <!-- Time Period Tabs -->
          <div class="time-tabs">
            <button 
              v-for="period in timePeriods" 
              :key="period"
              :class="['tab', 'border-theme', 'surface-primary', 'text-secondary', 'transition-theme-fast', { 'active': activePeriod === period }]"
              @click="activePeriod = period"
            >
              {{ period }}
            </button>
          </div>

          <!-- Chart Sections -->
          <div class="chart-sections">
            <!-- Noodles Chart -->
            <div class="chart-item surface-elevated border-theme-subtle transition-theme">
              <div class="chart-header">
                <div class="chart-icon">🍜</div>
                <span class="text-primary">Noodles</span>
              </div>
              <div class="chart-placeholder">
                <div class="bars">
                  <div class="bar bar-noodle1" style="height: 40%"></div>
                  <div class="bar bar-noodle2" style="height: 60%"></div>
                  <div class="bar bar-noodle3" style="height: 80%"></div>
                  <div class="bar bar-noodle4" style="height: 70%"></div>
                </div>
                <div class="chart-labels">
                  <span class="text-tertiary">Week 1</span>
                  <span class="text-tertiary">Week 2</span>
                  <span class="text-tertiary">Week 3</span>
                  <span class="text-tertiary">Week 4</span>
                </div>
              </div>
              <div class="chart-legend">
                <div class="legend-item">
                  <span class="legend-color noodle1"></span>
                  <span class="text-secondary">Noodle 1</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color noodle2"></span>
                  <span class="text-secondary">Noodle 4</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color noodle3"></span>
                  <span class="text-secondary">Noodle 2</span>
                </div>
              </div>
            </div>

            <!-- Drinks Chart -->
            <div class="chart-item surface-elevated border-theme-subtle transition-theme">
              <div class="chart-header">
                <div class="chart-icon">🥤</div>
                <span class="text-primary">Drinks</span>
              </div>
              <div class="chart-placeholder">
                <div class="bars">
                  <div class="bar bar-drink1" style="height: 35%"></div>
                  <div class="bar bar-drink2" style="height: 70%"></div>
                  <div class="bar bar-drink3" style="height: 60%"></div>
                  <div class="bar bar-drink4" style="height: 85%"></div>
                </div>
                <div class="chart-labels">
                  <span class="text-tertiary">Week 1</span>
                  <span class="text-tertiary">Week 2</span>
                  <span class="text-tertiary">Week 3</span>
                  <span class="text-tertiary">Week 4</span>
                </div>
              </div>
              <div class="chart-legend">
                <div class="legend-item">
                  <span class="legend-color drink1"></span>
                  <span class="text-secondary">Drink 2</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color drink2"></span>
                  <span class="text-secondary">Drink 3</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color drink3"></span>
                  <span class="text-secondary">Drink 1</span>
                </div>
              </div>
            </div>

            <!-- Toppings Chart -->
            <div class="chart-item surface-elevated border-theme-subtle transition-theme">
              <div class="chart-header">
                <div class="chart-icon">🧄</div>
                <span class="text-primary">Toppings</span>
              </div>
              <div class="chart-placeholder">
                <div class="bars">
                  <div class="bar bar-topping1" style="height: 45%"></div>
                  <div class="bar bar-topping2" style="height: 55%"></div>
                  <div class="bar bar-topping3" style="height: 75%"></div>
                  <div class="bar bar-topping4" style="height: 65%"></div>
                </div>
                <div class="chart-labels">
                  <span class="text-tertiary">Week 1</span>
                  <span class="text-tertiary">Week 2</span>
                  <span class="text-tertiary">Week 3</span>
                  <span class="text-tertiary">Week 4</span>
                </div>
              </div>
              <div class="chart-legend">
                <div class="legend-item">
                  <span class="legend-color topping1"></span>
                  <span class="text-secondary">Topping 1</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color topping2"></span>
                  <span class="text-secondary">Topping 2</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color topping3"></span>
                  <span class="text-secondary">Topping 3</span>
                </div>
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
.dashboard-page {
  min-height: 100%;
  width: 100%;
}

.dashboard-content {
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  padding-top: 2rem;
  padding-bottom: 2rem;
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
  border-radius: 1rem;
  padding: 1.5rem;
}

.content-section h2 {
  margin: 0 0 1.5rem 0;
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
  border-bottom: 2px solid var(--border-primary);
  font-weight: 600;
  font-size: 0.875rem;
}

.items-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--border-secondary);
}

.item-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.item-icon {
  width: 32px;
  height: 32px;
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
  border: 1px solid var(--border-secondary);
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.tab.active {
  background-color: var(--primary) !important;
  color: white !important;
  border-color: var(--primary) !important;
}

.chart-sections {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.chart-item {
  border-radius: 0.75rem;
  padding: 1rem;
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-weight: 500;
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
  border-radius: 0.25rem 0.25rem 0 0;
  min-height: 10px;
}

/* Chart bar colors using theme variables */
.bar-noodle1 { background: var(--primary); }
.bar-noodle2 { background: var(--primary-medium); }
.bar-noodle3 { background: var(--secondary); }
.bar-noodle4 { background: var(--secondary-medium); }

.bar-drink1 { background: var(--success); }
.bar-drink2 { background: var(--success-medium); }
.bar-drink3 { background: var(--info); }
.bar-drink4 { background: var(--info-medium); }

.bar-topping1 { background: var(--tertiary); }
.bar-topping2 { background: var(--tertiary-medium); }
.bar-topping3 { background: var(--neutral-variant); }
.bar-topping4 { background: var(--neutral-variant-medium); }

.chart-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
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
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

/* Legend colors matching chart bars */
.noodle1 { background: var(--primary); }
.noodle2 { background: var(--primary-medium); }
.noodle3 { background: var(--secondary); }

.drink1 { background: var(--success); }
.drink2 { background: var(--success-medium); }
.drink3 { background: var(--info); }

.topping1 { background: var(--tertiary); }
.topping2 { background: var(--tertiary-medium); }
.topping3 { background: var(--neutral-variant); }

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