
// Simple localStorage helper with TTL support
// API:
//   setItem(key, value, ttlMs?)
//   getItem(key, defaultValue?)
//   removeItem(key)
//   clearWithPrefix(prefix)
//   withPrefix(prefix)

export function useLocalStorage() {
  function setItem(key, value, ttlMs = null) {
    try {
      const record = {
        v: value,
        e: ttlMs ? Date.now() + Number(ttlMs) : null
      }
      localStorage.setItem(key, JSON.stringify(record))
    } catch (e) {
      // Fallback: attempt to free some space and retry once
      try { localStorage.removeItem(key) } catch (_) {}
      try { localStorage.setItem(key, JSON.stringify({ v: value, e: null })) } catch (_) {}
    }
  }

  function getItem(key, defaultValue = null) {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) return defaultValue
      const parsed = JSON.parse(raw)
      if (parsed && parsed.e && Date.now() > parsed.e) {
        // expired
        localStorage.removeItem(key)
        return defaultValue
      }
      return parsed ? parsed.v : defaultValue
    } catch (_) {
      return defaultValue
    }
  }

  function removeItem(key) {
    try { localStorage.removeItem(key) } catch (_) {}
  }

  function clearWithPrefix(prefix) {
    try {
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const k = localStorage.key(i)
        if (k && k.startsWith(prefix)) localStorage.removeItem(k)
      }
    } catch (_) {}
  }

  function withPrefix(prefix) {
    return {
      setItem: (k, v, ttl) => setItem(`${prefix}:${k}`, v, ttl),
      getItem: (k, d) => getItem(`${prefix}:${k}`, d),
      removeItem: (k) => removeItem(`${prefix}:${k}`),
      clear: () => clearWithPrefix(prefix)
    }
  }

  return { setItem, getItem, removeItem, clearWithPrefix, withPrefix }
}

export default useLocalStorage


