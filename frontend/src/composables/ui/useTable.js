// composables/ui/useTable.js
import { ref, computed, reactive, watch } from 'vue'

export const useTable = (options = {}) => {
  // Configuration options with defaults
  const config = reactive({
    itemsPerPage: options.itemsPerPage || 10,
    sortable: options.sortable !== false,
    filterable: options.filterable !== false,
    selectable: options.selectable !== false,
    ...options
  })

  // Core reactive state
  const state = reactive({
    data: ref([]),
    loading: ref(false),
    error: ref(null),
    currentPage: ref(1),
    searchQuery: ref(''),
    sortField: ref(''),
    sortDirection: ref('asc'), // 'asc' | 'desc'
    selectedItems: ref([]),
    filters: ref({})
  })

  // Computed properties
  const filteredData = computed(() => {
    let result = [...state.data]

    // Apply search filter
    if (state.searchQuery && config.filterable) {
      const query = state.searchQuery.toLowerCase()
      result = result.filter(item => 
        Object.values(item).some(value => 
          String(value).toLowerCase().includes(query)
        )
      )
    }

    // Apply custom filters
    if (Object.keys(state.filters).length > 0) {
      result = result.filter(item => {
        return Object.entries(state.filters).every(([key, filterValue]) => {
          if (!filterValue) return true
          
          const itemValue = item[key]
          
          // Handle different filter types
          if (typeof filterValue === 'object' && filterValue !== null) {
            if (filterValue.type === 'range') {
              const numValue = Number(itemValue)
              return numValue >= filterValue.min && numValue <= filterValue.max
            }
            if (filterValue.type === 'select') {
              return filterValue.values.includes(itemValue)
            }
          }
          
          // Default string contains filter
          return String(itemValue).toLowerCase().includes(String(filterValue).toLowerCase())
        })
      })
    }

    return result
  })

  const sortedData = computed(() => {
    if (!state.sortField || !config.sortable) {
      return filteredData.value
    }

    return [...filteredData.value].sort((a, b) => {
      const aValue = a[state.sortField]
      const bValue = b[state.sortField]

      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0
      if (aValue == null) return 1
      if (bValue == null) return -1

      // Handle different data types
      let comparison = 0
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        comparison = aValue - bValue
      } else if (aValue instanceof Date && bValue instanceof Date) {
        comparison = aValue.getTime() - bValue.getTime()
      } else {
        comparison = String(aValue).localeCompare(String(bValue), undefined, { numeric: true })
      }

      return state.sortDirection === 'desc' ? -comparison : comparison
    })
  })

  const paginatedData = computed(() => {
    const start = (state.currentPage - 1) * config.itemsPerPage
    const end = start + config.itemsPerPage
    return sortedData.value.slice(start, end)
  })

  const totalItems = computed(() => filteredData.value.length)
  const totalPages = computed(() => Math.ceil(totalItems.value / config.itemsPerPage))

  const paginationInfo = computed(() => {
    const start = totalItems.value === 0 ? 0 : (state.currentPage - 1) * config.itemsPerPage + 1
    const end = Math.min(state.currentPage * config.itemsPerPage, totalItems.value)
    
    return {
      start,
      end,
      total: totalItems.value,
      currentPage: state.currentPage,
      totalPages: totalPages.value
    }
  })

  const hasSelection = computed(() => state.selectedItems.length > 0)
  const isAllSelected = computed(() => 
    paginatedData.value.length > 0 && 
    paginatedData.value.every(item => state.selectedItems.includes(item.id))
  )
  const isPartiallySelected = computed(() => 
    hasSelection.value && !isAllSelected.value
  )

  // Methods
  const setData = (data) => {
    state.data = Array.isArray(data) ? data : []
    state.currentPage = 1 // Reset to first page when data changes
    clearSelection()
  }

  const updateData = (newData) => {
    state.data = [...state.data, ...newData]
  }

  const setLoading = (loading) => {
    state.loading = loading
  }

  const setError = (error) => {
    state.error = error
  }

  const clearError = () => {
    state.error = null
  }

  // Pagination methods
  const goToPage = (page) => {
    if (page >= 1 && page <= totalPages.value) {
      state.currentPage = page
    }
  }

  const nextPage = () => {
    if (state.currentPage < totalPages.value) {
      state.currentPage++
    }
  }

  const previousPage = () => {
    if (state.currentPage > 1) {
      state.currentPage--
    }
  }

  const setItemsPerPage = (itemsPerPage) => {
    config.itemsPerPage = itemsPerPage
    state.currentPage = 1 // Reset to first page
  }

  // Search methods
  const setSearchQuery = (query) => {
    state.searchQuery = query
    state.currentPage = 1 // Reset to first page when searching
  }

  const clearSearch = () => {
    state.searchQuery = ''
  }

  // Sort methods
  const sortBy = (field) => {
    if (state.sortField === field) {
      // Toggle direction if same field
      state.sortDirection = state.sortDirection === 'asc' ? 'desc' : 'asc'
    } else {
      // New field, default to ascending
      state.sortField = field
      state.sortDirection = 'asc'
    }
    state.currentPage = 1 // Reset to first page when sorting
  }

  const clearSort = () => {
    state.sortField = ''
    state.sortDirection = 'asc'
  }

  // Filter methods
  const setFilter = (key, value) => {
    if (value === null || value === undefined || value === '') {
      delete state.filters[key]
    } else {
      state.filters[key] = value
    }
    state.currentPage = 1 // Reset to first page when filtering
  }

  const clearFilter = (key) => {
    delete state.filters[key]
  }

  const clearAllFilters = () => {
    state.filters = {}
    clearSearch()
  }

  // Selection methods
  const selectItem = (itemId) => {
    if (!state.selectedItems.includes(itemId)) {
      state.selectedItems.push(itemId)
    }
  }

  const unselectItem = (itemId) => {
    const index = state.selectedItems.indexOf(itemId)
    if (index > -1) {
      state.selectedItems.splice(index, 1)
    }
  }

  const toggleItem = (itemId) => {
    if (state.selectedItems.includes(itemId)) {
      unselectItem(itemId)
    } else {
      selectItem(itemId)
    }
  }

  const selectAll = () => {
    const currentPageIds = paginatedData.value.map(item => item.id)
    currentPageIds.forEach(id => {
      if (!state.selectedItems.includes(id)) {
        state.selectedItems.push(id)
      }
    })
  }

  const unselectAll = () => {
    const currentPageIds = paginatedData.value.map(item => item.id)
    state.selectedItems = state.selectedItems.filter(id => !currentPageIds.includes(id))
  }

  const toggleSelectAll = () => {
    if (isAllSelected.value) {
      unselectAll()
    } else {
      selectAll()
    }
  }

  const clearSelection = () => {
    state.selectedItems = []
  }

  const getSelectedItems = () => {
    return state.data.filter(item => state.selectedItems.includes(item.id))
  }

  // Utility methods
  const refresh = () => {
    // Reset all state except data
    state.currentPage = 1
    state.searchQuery = ''
    state.sortField = ''
    state.sortDirection = 'asc'
    state.selectedItems = []
    state.filters = {}
    state.error = null
  }

  const reset = () => {
    // Reset everything including data
    refresh()
    state.data = []
    state.loading = false
  }

  // Watch for page changes when filtered data changes
  watch(filteredData, () => {
    if (state.currentPage > totalPages.value && totalPages.value > 0) {
      state.currentPage = totalPages.value
    }
  })

  // Return all the reactive state and methods
  return {
    // State
    ...state,
    config,
    
    // Computed
    filteredData,
    sortedData,
    paginatedData,
    totalItems,
    totalPages,
    paginationInfo,
    hasSelection,
    isAllSelected,
    isPartiallySelected,
    
    // Data methods
    setData,
    updateData,
    setLoading,
    setError,
    clearError,
    
    // Pagination methods
    goToPage,
    nextPage,
    previousPage,
    setItemsPerPage,
    
    // Search methods
    setSearchQuery,
    clearSearch,
    
    // Sort methods
    sortBy,
    clearSort,
    
    // Filter methods
    setFilter,
    clearFilter,
    clearAllFilters,
    
    // Selection methods
    selectItem,
    unselectItem,
    toggleItem,
    selectAll,
    unselectAll,
    toggleSelectAll,
    clearSelection,
    getSelectedItems,
    
    // Utility methods
    refresh,
    reset
  }
}