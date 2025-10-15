
// Lightweight in-memory cache with TTL and simple LRU eviction
// API:
//   set(key, value, ttlMs?)
//   get(key, defaultValue?)
//   has(key)
//   delete(key)
//   clear()
//   size()
// Configure with: useCache({ maxEntries: 200 })

const defaultConfig = { maxEntries: 200 }

export function useCache(config = {}) {
  const settings = { ...defaultConfig, ...config }
  const store = new Map() // key -> { value, expiresAt }

  function set(key, value, ttlMs = null) {
    const expiresAt = ttlMs ? Date.now() + Number(ttlMs) : null
    if (store.has(key)) store.delete(key)
    store.set(key, { value, expiresAt })
    evictIfNeeded()
  }

  function get(key, defaultValue = null) {
    if (!store.has(key)) return defaultValue
    const entry = store.get(key)
    if (entry.expiresAt && Date.now() > entry.expiresAt) {
      store.delete(key)
      return defaultValue
    }
    // refresh LRU order
    store.delete(key)
    store.set(key, entry)
    return entry.value
  }

  function has(key) {
    if (!store.has(key)) return false
    const entry = store.get(key)
    if (entry.expiresAt && Date.now() > entry.expiresAt) {
      store.delete(key)
      return false
    }
    return true
  }

  function deleteKey(key) {
    store.delete(key)
  }

  function clear() {
    store.clear()
  }

  function size() {
    return store.size
  }

  function evictIfNeeded() {
    if (store.size <= settings.maxEntries) return
    const overflow = store.size - settings.maxEntries
    // delete oldest entries
    const keys = Array.from(store.keys())
    for (let i = 0; i < overflow; i++) {
      store.delete(keys[i])
    }
  }

  return { set, get, has, delete: deleteKey, clear, size }
}

export default useCache


