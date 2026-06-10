<template>
  <div class="pagination-container surface-secondary border-theme" v-if="totalPages > 1">
    <div class="pagination-info">
      <small class="text-secondary">{{ infoText }}</small>
    </div>
    <div class="pagination-controls">
      <!-- First button -->
      <button 
        class="btn btn-sm btn-theme page-btn transition-theme" 
        :disabled="currentPage === 1"
        @click="$emit('page-changed', 1)"
        title="First page"
      >
        <ChevronLeft :size="14" />
        <ChevronLeft :size="14" />
      </button>
      
      <!-- Previous button -->
      <button 
        class="btn btn-sm btn-theme page-btn transition-theme" 
        :disabled="!hasPrevious"
        @click="$emit('page-changed', previousPage)"
        title="Previous page"
      >
        <ChevronLeft :size="14" />
      </button>
      
      <!-- Page numbers -->
      <button 
        v-for="page in visiblePages" 
        :key="page"
        class="btn btn-sm page-btn transition-theme"
        :class="page === currentPage ? 'btn-primary' : 'btn-theme'"
        @click="$emit('page-changed', page)"
      >
        {{ page }}
      </button>
      
      <!-- Next button -->
      <button 
        class="btn btn-sm btn-theme page-btn transition-theme" 
        :disabled="!hasNext"
        @click="$emit('page-changed', nextPage)"
        title="Next page"
      >
        <ChevronRight :size="14" />
      </button>
      
      <!-- Last button -->
      <button 
        class="btn btn-sm btn-theme page-btn transition-theme" 
        :disabled="currentPage === totalPages"
        @click="$emit('page-changed', totalPages)"
        title="Last page"
      >
        <ChevronRight :size="14" />
        <ChevronRight :size="14" />
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PaginationControls',
  props: {
    currentPage: { type: Number, required: true },
    totalPages: { type: Number, required: true },
    visiblePages: { type: Array, required: true },
    hasNext: { type: Boolean, required: true },
    hasPrevious: { type: Boolean, required: true },
    nextPage: { type: Number, required: true },
    previousPage: { type: Number, required: true },
    start: { type: Number, required: true },
    end: { type: Number, required: true },
    total: { type: Number, required: true },
    itemName: { type: String, default: 'items' }
  },
  emits: ['page-changed'],
  computed: {
    infoText() {
      return `Showing ${this.start}-${this.end} of ${this.total} ${this.itemName}`
    }
  }
}
</script>

<style scoped>
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
}

.pagination-controls {
  display: flex;
  gap: 0.25rem;
}

.page-btn {
  min-width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.125rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .pagination-container {
    flex-direction: column;
    gap: 1rem;
  }
  
  .pagination-controls {
    justify-content: center;
  }
}
</style>