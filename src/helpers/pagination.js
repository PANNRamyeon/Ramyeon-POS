// utils/pagination.js

/**
 * Creates pagination state and methods
 * @param {Object} options - Configuration options
 * @returns {Object} Pagination utilities
 */
export function createPagination(options = {}) {
  const config = {
    itemsPerPage: options.itemsPerPage || 10,
    maxVisiblePages: options.maxVisiblePages || 5,
    ...options
  }

  return {
    // Calculate total pages
    getTotalPages(totalItems, itemsPerPage = config.itemsPerPage) {
      return Math.ceil(totalItems / itemsPerPage)
    },

    // Get items for current page
    getPaginatedItems(items, currentPage, itemsPerPage = config.itemsPerPage) {
      const start = (currentPage - 1) * itemsPerPage
      const end = start + itemsPerPage
      return items.slice(start, end)
    },

    // Get pagination info for display
    getPaginationInfo(currentPage, totalItems, itemsPerPage = config.itemsPerPage) {
      const start = totalItems === 0 ? 0 : (currentPage - 1) * itemsPerPage + 1
      const end = Math.min(currentPage * itemsPerPage, totalItems)
      const totalPages = this.getTotalPages(totalItems, itemsPerPage)
      
      return {
        start,
        end,
        total: totalItems,
        currentPage,
        totalPages,
        hasNext: currentPage < totalPages,
        hasPrevious: currentPage > 1
      }
    },

    // Get visible page numbers for pagination controls
    getVisiblePages(currentPage, totalPages, maxVisible = config.maxVisiblePages) {
      const pages = []
      let start = Math.max(1, currentPage - Math.floor(maxVisible / 2))
      let end = Math.min(totalPages, start + maxVisible - 1)
      
      // Adjust start if we're near the end
      if (end - start + 1 < maxVisible) {
        start = Math.max(1, end - maxVisible + 1)
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      
      return pages
    },

    // Validate and normalize page number
    normalizePage(page, totalPages) {
      const pageNum = parseInt(page)
      if (isNaN(pageNum) || pageNum < 1) return 1
      if (pageNum > totalPages) return Math.max(1, totalPages)
      return pageNum
    },

    // Get pagination controls data
    getPaginationControls(currentPage, totalPages, maxVisible = config.maxVisiblePages) {
      return {
        pages: this.getVisiblePages(currentPage, totalPages, maxVisible),
        hasNext: currentPage < totalPages,
        hasPrevious: currentPage > 1,
        nextPage: Math.min(currentPage + 1, totalPages),
        previousPage: Math.max(currentPage - 1, 1),
        firstPage: 1,
        lastPage: totalPages
      }
    }
  }
}

// Pre-configured instances for common use cases
export const tablePagination = createPagination({ itemsPerPage: 10, maxVisiblePages: 5 })
export const cardPagination = createPagination({ itemsPerPage: 12, maxVisiblePages: 7 })
export const listPagination = createPagination({ itemsPerPage: 20, maxVisiblePages: 3 })