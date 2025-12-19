/**
 * Storage utilities for managing user data isolation
 * Handles localStorage and cookies with user-specific keys
 */

// Get a unique identifier for the current user (authenticated or anonymous)
export const getUserIdentifier = () => {
  // Try to get user ID from auth context or token
  const token = localStorage.getItem('token')
  if (token) {
    try {
      // Decode token to get user ID (simple base64 decode for JWT payload)
      const payload = JSON.parse(atob(token.split('.')[1]))
      return `user_${payload.sub || payload.user_id || payload.id || 'unknown'}`
    } catch (e) {
      // If token decode fails, use a fallback
      return `user_token_${token.substring(0, 10)}`
    }
  }
  
  // For anonymous users, use a persistent identifier from cookies
  return getOrCreateAnonymousId()
}

// Get or create an anonymous user ID stored in cookies
const getOrCreateAnonymousId = () => {
  const cookieName = 'anonymous_user_id'
  const cookies = document.cookie.split(';').reduce((acc, cookie) => {
    const [key, value] = cookie.trim().split('=')
    acc[key] = value
    return acc
  }, {})
  
  if (cookies[cookieName]) {
    return `anonymous_${cookies[cookieName]}`
  }
  
  // Create a new anonymous ID
  const anonymousId = `anon_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  // Store in cookie (expires in 1 year)
  const expiryDate = new Date()
  expiryDate.setFullYear(expiryDate.getFullYear() + 1)
  document.cookie = `${cookieName}=${anonymousId}; expires=${expiryDate.toUTCString()}; path=/; SameSite=Lax`
  
  return `anonymous_${anonymousId}`
}

// Clear anonymous ID when user logs in
export const clearAnonymousData = () => {
  // Clear anonymous user ID cookie
  document.cookie = 'anonymous_user_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
  
  // Clear all anonymous localStorage data
  const keysToRemove = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith('anonymous_')) {
      keysToRemove.push(key)
    }
  }
  keysToRemove.forEach(key => localStorage.removeItem(key))
}

// Get user-specific key for localStorage
export const getUserKey = (baseKey) => {
  const userIdentifier = getUserIdentifier()
  return `${userIdentifier}_${baseKey}`
}

// Save to localStorage with user isolation
export const saveToStorage = (key, value) => {
  const userKey = getUserKey(key)
  try {
    localStorage.setItem(userKey, JSON.stringify(value))
  } catch (e) {
    console.error('Error saving to localStorage:', e)
    // Fallback to cookies if localStorage is full
    saveToCookie(key, value)
  }
}

// Get from localStorage with user isolation
export const getFromStorage = (key, defaultValue = null) => {
  const userKey = getUserKey(key)
  try {
    const item = localStorage.getItem(userKey)
    return item ? JSON.parse(item) : defaultValue
  } catch (e) {
    console.error('Error reading from localStorage:', e)
    // Fallback to cookies
    return getFromCookie(key, defaultValue)
  }
}

// Remove from localStorage with user isolation
export const removeFromStorage = (key) => {
  const userKey = getUserKey(key)
  localStorage.removeItem(userKey)
}

// Save to cookies (for larger data or when localStorage fails)
export const saveToCookie = (key, value, days = 365) => {
  const userKey = getUserKey(key)
  const expiryDate = new Date()
  expiryDate.setTime(expiryDate.getTime() + (days * 24 * 60 * 60 * 1000))
  const expires = `expires=${expiryDate.toUTCString()}`
  
  try {
    // Cookies have a 4KB limit, so we might need to split large data
    const valueStr = JSON.stringify(value)
    if (valueStr.length > 4000) {
      // Split into multiple cookies
      const chunks = Math.ceil(valueStr.length / 4000)
      for (let i = 0; i < chunks; i++) {
        const chunk = valueStr.substring(i * 4000, (i + 1) * 4000)
        document.cookie = `${userKey}_${i}=${encodeURIComponent(chunk)}; ${expires}; path=/; SameSite=Lax`
      }
      document.cookie = `${userKey}_chunks=${chunks}; ${expires}; path=/; SameSite=Lax`
    } else {
      document.cookie = `${userKey}=${encodeURIComponent(valueStr)}; ${expires}; path=/; SameSite=Lax`
    }
  } catch (e) {
    console.error('Error saving to cookie:', e)
  }
}

// Get from cookies
export const getFromCookie = (key, defaultValue = null) => {
  const userKey = getUserKey(key)
  const cookies = document.cookie.split(';').reduce((acc, cookie) => {
    const [key, value] = cookie.trim().split('=')
    acc[key] = value
    return acc
  }, {})
  
  try {
    // Check if data is split across multiple cookies
    if (cookies[`${userKey}_chunks`]) {
      const chunks = parseInt(cookies[`${userKey}_chunks`])
      let valueStr = ''
      for (let i = 0; i < chunks; i++) {
        const chunk = cookies[`${userKey}_${i}`]
        if (chunk) {
          valueStr += decodeURIComponent(chunk)
        }
      }
      return valueStr ? JSON.parse(valueStr) : defaultValue
    } else if (cookies[userKey]) {
      return JSON.parse(decodeURIComponent(cookies[userKey]))
    }
  } catch (e) {
    console.error('Error reading from cookie:', e)
  }
  
  return defaultValue
}

// Remove from cookies
export const removeFromCookie = (key) => {
  const userKey = getUserKey(key)
  document.cookie = `${userKey}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`
  
  // Remove chunked cookies if they exist
  const cookies = document.cookie.split(';').reduce((acc, cookie) => {
    const [k] = cookie.trim().split('=')
    acc[k] = true
    return acc
  }, {})
  
  if (cookies[`${userKey}_chunks`]) {
    const chunks = parseInt(cookies[`${userKey}_chunks`])
    for (let i = 0; i < chunks; i++) {
      document.cookie = `${userKey}_${i}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`
    }
    document.cookie = `${userKey}_chunks=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`
  }
}

// Clear all user-specific data
export const clearUserData = () => {
  const userIdentifier = getUserIdentifier()
  const prefix = `${userIdentifier}_`
  
  // Clear localStorage
  const keysToRemove = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(prefix)) {
      keysToRemove.push(key)
    }
  }
  keysToRemove.forEach(key => localStorage.removeItem(key))
  
  // Clear cookies
  const cookies = document.cookie.split(';')
  cookies.forEach(cookie => {
    const [key] = cookie.trim().split('=')
    if (key && key.startsWith(prefix)) {
      document.cookie = `${key}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`
    }
  })
}

