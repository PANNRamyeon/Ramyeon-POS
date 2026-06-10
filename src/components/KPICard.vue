<template>
  <div class="kpi-card" :class="variant">
    <div class="kpi-header">
      <h3>{{ title }}</h3>
      <span v-if="change" class="kpi-change" :class="changeType">{{ change }}</span>
    </div>
    <div class="kpi-value">{{ value }}</div>
    <div class="kpi-subtitle">{{ subtitle }}</div>
    
    <!-- Progress bar for target sales -->
    <div v-if="showProgress" class="progress-section">
      <div class="progress-bar">
        <div class="progress-fill" :style="`width: ${progressPercentage}%`"></div>
      </div>
      <div class="progress-info">
        <span class="progress-percentage">{{ progressPercentage }}%</span>
      </div>
      <button v-if="showButton" class="see-more-btn" @click="$emit('button-click')">
        {{ buttonText }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'KpiCard',
  props: {
    title: {
      type: String,
      required: true
    },
    value: {
      type: [String, Number],
      required: true
    },
    subtitle: {
      type: String,
      required: true
    },
    change: {
      type: String,
      default: null
    },
    changeType: {
      type: String,
      default: 'positive',
      validator: value => ['positive', 'negative', 'neutral'].includes(value)
    },
    variant: {
      type: String,
      default: 'default',
      validator: value => ['default', 'profit', 'products', 'income', 'sold', 'orders', 'target'].includes(value)
    },
    showProgress: {
      type: Boolean,
      default: false
    },
    progressPercentage: {
      type: Number,
      default: 0
    },
    showButton: {
      type: Boolean,
      default: false
    },
    buttonText: {
      type: String,
      default: 'See More'
    }
  },
  emits: ['button-click']
}
</script>

<style scoped>
.kpi-card {
  border-radius: 1rem;
  padding: 2rem;
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  min-height: 125px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

/* Different gradient styles for variants */
.kpi-card.profit {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.kpi-card.orders {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

.kpi-card.products {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.kpi-card.income {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.kpi-card.sold {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.kpi-card.target {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

.kpi-card.default {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  position: relative;
  z-index: 1;
}

.kpi-header h3 {
  color: white;
  font-size: 0.875rem;
  font-weight: 500;
  margin: 0;
  line-height: 1.4;
  flex: 1;
  padding-right: 1rem;
  opacity: 0.9;
}

.kpi-change {
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.5rem;
  line-height: 1.1;
  position: relative;
  z-index: 1;
}

.kpi-subtitle {
  color: white;
  font-size: 0.875rem;
  line-height: 1.5;
  margin-bottom: auto;
  position: relative;
  z-index: 1;
  opacity: 0.9;
}

.progress-section {
  margin-top: 1rem;
  position: relative;
  z-index: 1;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.6));
  border-radius: 5px;
  transition: width 0.6s ease;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-info {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.progress-percentage {
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
  opacity: 0.9;
}

.see-more-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
  backdrop-filter: blur(10px);
}

.see-more-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-1px);
}

.see-more-btn:active {
  transform: translateY(0);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .kpi-card {
    padding: 1.25rem;
    min-height: 110px;
  }
  
  .kpi-header {
    margin-bottom: 1rem;
  }
  
  .kpi-header h3 {
    font-size: 0.875rem;
  }
  
  .kpi-value {
    font-size: 1.75rem;
    margin-bottom: 0.5rem;
  }
  
  .kpi-subtitle {
    font-size: 0.8rem;
  }
  
  .progress-section {
    margin-top: 1rem;
  }
  
  .see-more-btn {
    padding: 0.625rem 1.25rem;
    font-size: 0.85rem;
  }
}

@media (max-width: 480px) {
  .kpi-card {
    padding: 1.25rem;
  }
  
  .kpi-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .kpi-header h3 {
    padding-right: 0;
  }
  
  .kpi-value {
    font-size: 1.75rem;
  }
}
</style>