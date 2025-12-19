import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Hook for AI-powered suggestions while typing
 * 
 * @param {string} text - Current text input
 * @param {number} cursorPosition - Cursor position in text
 * @param {string} moduleType - Module type (grammar, qa, reformulation, general)
 * @param {boolean} enabled - Whether suggestions are enabled
 * @param {number} debounceMs - Debounce delay in milliseconds
 * @returns {Object} { suggestions, loading, error }
 */
export const useSuggestions = (
  text = '',
  cursorPosition = null,
  moduleType = 'general',
  enabled = true,
  debounceMs = 300
) => {
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const debounceTimerRef = useRef(null)
  const abortControllerRef = useRef(null)

  const fetchSuggestions = useCallback(async (textToCheck, position, module) => {
    // Don't fetch if text is too short
    if (!textToCheck || textToCheck.trim().length < 2) {
      setSuggestions([])
      return
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController()

    setLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem('token')
      const headers = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const params = new URLSearchParams({
        q: textToCheck,
        module_type: module || 'general'
      })
      
      if (position !== null && position !== undefined) {
        params.append('cursor_position', position.toString())
      }

      const response = await fetch(`/api/suggestions/?${params.toString()}`, {
        headers,
        signal: abortControllerRef.current.signal
      })

      if (response.ok) {
        const data = await response.json()
        setSuggestions(data || [])
      } else {
        // Don't set error for 4xx/5xx, just clear suggestions
        setSuggestions([])
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Error fetching suggestions:', err)
        setError(err.message)
        setSuggestions([])
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled) {
      setSuggestions([])
      return
    }

    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      const position = cursorPosition !== null ? cursorPosition : text.length
      fetchSuggestions(text, position, moduleType)
    }, debounceMs)

    // Cleanup
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [text, cursorPosition, moduleType, enabled, debounceMs, fetchSuggestions])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  return {
    suggestions,
    loading,
    error,
    clearSuggestions: () => setSuggestions([])
  }
}

