/**
 * Date and Time Helper Utilities for Philippine Standard Time (PST/UTC+8)
 * 
 * This module provides centralized functions for converting UTC datetime strings
 * to Philippine Standard Time and formatting them for display.
 */

/**
 * Format a datetime string to Philippine Standard Time
 * @param {string|Date|null} dateString - ISO datetime string, Date object, or null
 * @param {Object} options - Formatting options
 * @returns {string} Formatted datetime string in Philippine time, or 'N/A' if invalid
 */
export function formatDateTimePH(dateString, options = {}) {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    
    if (isNaN(date.getTime())) {
      return 'N/A'
    }
    
    const defaultOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Manila',
      ...options
    }
    
    const datePart = date.toLocaleDateString('en-US', {
      year: defaultOptions.year,
      month: defaultOptions.month,
      day: defaultOptions.day,
      timeZone: 'Asia/Manila'
    })
    
    const timePart = date.toLocaleTimeString('en-US', {
      hour: defaultOptions.hour,
      minute: defaultOptions.minute,
      hour12: defaultOptions.hour12,
      timeZone: 'Asia/Manila'
    })
    
    return `${datePart} ${timePart}`
  } catch (error) {
    console.error('Error formatting datetime:', error)
    return 'N/A'
  }
}

/**
 * Format a datetime string to Philippine Standard Time (short format)
 * @param {string|Date|null} dateString - ISO datetime string, Date object, or null
 * @returns {string} Formatted datetime string (e.g., "Nov 22, 2025 05:47")
 */
export function formatDateTimeShortPH(dateString) {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    
    if (isNaN(date.getTime())) {
      return 'N/A'
    }
    
    const datePart = date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: 'Asia/Manila'
    })
    
    const timePart = date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Manila'
    })
    
    return `${datePart} ${timePart}`
  } catch (error) {
    console.error('Error formatting datetime:', error)
    return 'N/A'
  }
}

/**
 * Format a datetime string to Philippine Standard Time (12-hour format with AM/PM)
 * @param {string|Date|null} dateString - ISO datetime string, Date object, or null
 * @returns {string} Formatted datetime string (e.g., "Nov 22, 2025 05:47 AM")
 */
export function formatDateTime12HourPH(dateString) {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    
    if (isNaN(date.getTime())) {
      return 'N/A'
    }
    
    const datePart = date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: 'Asia/Manila'
    })
    
    const timePart = date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
      timeZone: 'Asia/Manila'
    })
    
    return `${datePart} ${timePart}`
  } catch (error) {
    console.error('Error formatting datetime:', error)
    return 'N/A'
  }
}

/**
 * Format only the date part in Philippine Standard Time
 * @param {string|Date|null} dateString - ISO datetime string, Date object, or null
 * @returns {string} Formatted date string (e.g., "Nov 22, 2025")
 */
export function formatDatePH(dateString) {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    
    if (isNaN(date.getTime())) {
      return 'N/A'
    }
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: 'Asia/Manila'
    })
  } catch (error) {
    console.error('Error formatting date:', error)
    return 'N/A'
  }
}

/**
 * Format only the time part in Philippine Standard Time
 * @param {string|Date|null} dateString - ISO datetime string, Date object, or null
 * @param {boolean} use12Hour - Whether to use 12-hour format (default: false)
 * @returns {string} Formatted time string (e.g., "05:47" or "05:47 AM")
 */
export function formatTimePH(dateString, use12Hour = false) {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    
    if (isNaN(date.getTime())) {
      return 'N/A'
    }
    
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: use12Hour,
      timeZone: 'Asia/Manila'
    })
  } catch (error) {
    console.error('Error formatting time:', error)
    return 'N/A'
  }
}

/**
 * Get current datetime in Philippine Standard Time as ISO string
 * @returns {string} Current datetime in Philippine timezone (ISO format)
 */
export function getPhilippineNowISO() {
  const now = new Date()
  // Convert to Philippine time and return ISO string
  const phTime = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Manila' }))
  return phTime.toISOString()
}

