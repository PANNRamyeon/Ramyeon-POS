<template>
  <div class="dashboard-page surface-secondary transition-theme">
    <div class="dashboard-content">
      <!-- Top Stats Cards using KPI Component -->
      <div class="stats-section">
        <KpiCard
          title="Total Revenue"
          :value="totalRevenueDisplay"
          subtitle="Today's total revenue"
          :change="''"
          changeType="positive"
          variant="profit"
        />
        
        <KpiCard
          title="Total Orders"
          :value="totalOrders"
          subtitle="Orders processed today"
          :change="''"
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
              @click="changePeriod(period)"
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
                  <div 
                    v-for="(week, index) in noodlesChartData" 
                    :key="index"
                    class="bar bar-noodle" 
                    :style="{ height: week.height + '%' }"
                    :class="`bar-noodle${index + 1}`"
                  ></div>
                </div>
                <div class="chart-labels">
                  <span v-for="(week, index) in noodlesChartData" :key="index" class="text-tertiary">
                    Week {{ index + 1 }}
                  </span>
                </div>
              </div>
              <div class="chart-legend">
                <div class="legend-item" v-if="noodlesRevenue > 0">
                  <span class="legend-color noodle1"></span>
                  <span class="text-secondary">₱{{ noodlesRevenue.toLocaleString() }}</span>
                </div>
                <div class="legend-item" v-else>
                  <span class="text-tertiary">No data</span>
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
                  <div 
                    v-for="(week, index) in drinksChartData" 
                    :key="index"
                    class="bar bar-drink" 
                    :style="{ height: week.height + '%' }"
                    :class="`bar-drink${index + 1}`"
                  ></div>
                </div>
                <div class="chart-labels">
                  <span v-for="(week, index) in drinksChartData" :key="index" class="text-tertiary">
                    Week {{ index + 1 }}
                  </span>
                </div>
              </div>
              <div class="chart-legend">
                <div class="legend-item" v-if="drinksRevenue > 0">
                  <span class="legend-color drink1"></span>
                  <span class="text-secondary">₱{{ drinksRevenue.toLocaleString() }}</span>
                </div>
                <div class="legend-item" v-else>
                  <span class="text-tertiary">No data</span>
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
                  <div 
                    v-for="(week, index) in toppingsChartData" 
                    :key="index"
                    class="bar bar-topping" 
                    :style="{ height: week.height + '%' }"
                    :class="`bar-topping${index + 1}`"
                  ></div>
                </div>
                <div class="chart-labels">
                  <span v-for="(week, index) in toppingsChartData" :key="index" class="text-tertiary">
                    Week {{ index + 1 }}
                  </span>
                </div>
              </div>
              <div class="chart-legend">
                <div class="legend-item" v-if="toppingsRevenue > 0">
                  <span class="legend-color topping1"></span>
                  <span class="text-secondary">₱{{ toppingsRevenue.toLocaleString() }}</span>
                </div>
                <div class="legend-item" v-else>
                  <span class="text-tertiary">No data</span>
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
import dashboardAPIService from '@/services/apiDashboard'
import { useLocalStorage } from '@/composables/data/useLocalStorage.js'

export default {
  name: 'Dashboard',
  components: {
    KpiCard
  },
  data() {
    return {
      activePeriod: 'This week',
      // KPI state
      totalRevenue: 0,
      totalOrders: 0,
      lastUpdated: null,
      // cache helpers
      storage: null,
      cacheTTLms: 10 * 60 * 1000, // refresh every 10 minutes within the day
      timePeriods: ['This week', 'This month', 'This year'],
      // Real data from APIs
      orderedItems: [],
      // Chart data
      categoryStats: null,
      noodlesRevenue: 0,
      drinksRevenue: 0,
      toppingsRevenue: 0,
      noodlesChartData: Array(4).fill().map(() => ({ height: 0 })),
      drinksChartData: Array(4).fill().map(() => ({ height: 0 })),
      toppingsChartData: Array(4).fill().map(() => ({ height: 0 }))
    }
  },
  computed: {
    totalRevenueDisplay() {
      return `₱${this.totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 0 })}`
    }
  },
  async mounted() {
    const ls = useLocalStorage()
    this.storage = ls.withPrefix('dashboard')
    await this.refreshDashboardData()
    this._kpiTimer = setInterval(this.refreshDashboardData, 10 * 60 * 1000)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') this.refreshDashboardData()
    })
  },
  beforeUnmount() {
    if (this._kpiTimer) clearInterval(this._kpiTimer)
  },
  methods: {
    getTodayKey() {
      const d = new Date()
      const yyyy = d.getFullYear()
      const mm = String(d.getMonth() + 1).padStart(2, '0')
      const dd = String(d.getDate()).padStart(2, '0')
      return `${yyyy}-${mm}-${dd}`
    },

    async refreshDashboardData() {
      await Promise.all([
        this.refreshTodayKpis(),
        this.refreshTopProducts(),
        this.refreshCategoryStats()
      ])
    },

    async refreshTodayKpis() {
      try {
        const today = this.getTodayKey()
        const cached = this.storage.getItem(`kpi:${today}`, null)
        
        if (cached) {
          this.totalRevenue = Number(cached.totalRevenue || 0)
          this.totalOrders = Number(cached.totalOrders || 0)
          this.lastUpdated = cached.lastUpdated || null
        }

        // Use real-time sales data for today's KPIs
        const data = await dashboardAPIService.getRealTimeSalesData()
        if (data.success && data.data) {
          const revenueData = data.data.revenue_summary
          const totalRevenue = Number(revenueData?.successful_revenue || 0)
          const totalOrders = Number(revenueData?.successful_transactions || 0)
          
          this.totalRevenue = totalRevenue
          this.totalOrders = totalOrders
          this.lastUpdated = new Date().toISOString()
          
          this.storage.setItem(`kpi:${today}`, {
            totalRevenue,
            totalOrders,
            lastUpdated: this.lastUpdated
          }, this.cacheTTLms)
        }
      } catch (e) {
        console.error('Failed to refresh today KPIs:', e)
      }
    },

    async refreshTopProducts() {
      try {
        const today = new Date()
        const data = await dashboardAPIService.getDailyTopProducts(today, 10)
        
        if (data.success && data.data) {
          this.orderedItems = data.data.top_products.map((product, index) => ({
            id: product.product_id || index,
            name: product.product_name || `Product ${index + 1}`,
            orders: product.total_quantity || 0,
            ppu: product.unit_price || product.average_price || 0,
            revenue: product.total_revenue || 0
          }))
        }
      } catch (e) {
        console.error('Failed to refresh top products:', e)
        // Fallback to empty array
        this.orderedItems = []
      }
    },

    async refreshCategoryStats() {
      try {
        const period = this.getPeriodForAPI()
        const data = await dashboardAPIService.getCategoryStatistics(period)
        
        if (data.success && data.data) {
          this.categoryStats = data.data
          this.updateChartData()
        }
      } catch (e) {
        console.error('Failed to refresh category stats:', e)
      }
    },

    getPeriodForAPI() {
      switch (this.activePeriod) {
        case 'This week': return 'week'
        case 'This month': return 'month'
        case 'This year': return 'year'
        default: return 'week'
      }
    },

    updateChartData() {
      if (!this.categoryStats || !this.categoryStats.categories) {
        this.resetChartData()
        return
      }

      // Reset revenues
      this.noodlesRevenue = 0
      this.drinksRevenue = 0
      this.toppingsRevenue = 0

      // Calculate category revenues
      this.categoryStats.categories.forEach(category => {
        const categoryName = category.category_name?.toLowerCase() || ''
        const revenue = category.total_revenue || 0

        if (categoryName.includes('noodle')) {
          this.noodlesRevenue += revenue
        } else if (categoryName.includes('drink')) {
          this.drinksRevenue += revenue
        } else if (categoryName.includes('topping') || categoryName.includes('addon')) {
          this.toppingsRevenue += revenue
        }
      })

      // Update chart heights based on revenue (normalized for display)
      const maxRevenue = Math.max(this.noodlesRevenue, this.drinksRevenue, this.toppingsRevenue, 1)
      
      this.noodlesChartData = this.generateChartData(this.noodlesRevenue, maxRevenue)
      this.drinksChartData = this.generateChartData(this.drinksRevenue, maxRevenue)
      this.toppingsChartData = this.generateChartData(this.toppingsRevenue, maxRevenue)
    },

    generateChartData(revenue, maxRevenue) {
      // Create 4 weeks of data with the current revenue distributed
      const baseHeight = (revenue / maxRevenue) * 100
      return Array(4).fill().map((_, index) => ({
        height: Math.max(10, baseHeight * (0.7 + Math.random() * 0.3)) // Some variation
      }))
    },

    resetChartData() {
      this.noodlesRevenue = 0
      this.drinksRevenue = 0
      this.toppingsRevenue = 0
      this.noodlesChartData = Array(4).fill().map(() => ({ height: 0 }))
      this.drinksChartData = Array(4).fill().map(() => ({ height: 0 }))
      this.toppingsChartData = Array(4).fill().map(() => ({ height: 0 }))
    },

    async changePeriod(period) {
      this.activePeriod = period
      await this.refreshCategoryStats()
    }
  }
}
</script>

<style scoped>
/* Your existing styles remain exactly the same */
.dashboard-page {
  min-height: 100%;
  width: 100%;
  overflow-y: auto;
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
  font-weight: 600;
  font-size: 0.875rem;
}

.items-table td {
  padding: 0.75rem;
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
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.tab.active {
  background-color: var(--primary) !important;
  color: var(--text-inverse) !important;
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
  transition: height 0.5s ease;
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