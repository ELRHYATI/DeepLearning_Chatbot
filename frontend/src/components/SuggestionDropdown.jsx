import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, CheckCircle, Lightbulb, Zap, Loader2 } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

const SuggestionDropdown = ({ 
  suggestions, 
  loading, 
  onSelect, 
  position = null,
  visible = true 
}) => {
  const { isDark } = useTheme()
  const [selectedIndex, setSelectedIndex] = useState(0)
  const dropdownRef = useRef(null)

  useEffect(() => {
    setSelectedIndex(0) // Reset selection when suggestions change
  }, [suggestions])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!visible || suggestions.length === 0) return

      // Tab key - accept first suggestion
      if (e.key === 'Tab' && !e.shiftKey) {
        e.preventDefault()
        if (suggestions[0]) {
          onSelect(suggestions[0])
        }
        return
      }

      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev => (prev + 1) % suggestions.length)
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => (prev - 1 + suggestions.length) % suggestions.length)
      } else if (e.key === 'Enter' && selectedIndex >= 0) {
        // Enter is handled by AnimatedInput to send message
        // Don't prevent default here, let it bubble up
        return
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onSelect(null) // Close dropdown
      }
    }

    if (visible && suggestions.length > 0) {
      window.addEventListener('keydown', handleKeyDown)
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [visible, suggestions, selectedIndex, onSelect])

  if (!visible || (!loading && suggestions.length === 0)) {
    return null
  }

  const getSuggestionIcon = (type) => {
    switch (type) {
      case 'grammar':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'completion':
        return <Zap className="w-4 h-4 text-blue-500" />
      case 'reformulation':
        return <Lightbulb className="w-4 h-4 text-purple-500" />
      case 'semantic':
        return <Sparkles className="w-4 h-4 text-yellow-500" />
      default:
        return <Sparkles className="w-4 h-4 text-gray-500" />
    }
  }

  const getSuggestionColor = (type) => {
    switch (type) {
      case 'grammar':
        return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
      case 'completion':
        return 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20'
      case 'reformulation':
        return 'border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-900/20'
      case 'semantic':
        return 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20'
      default:
        return 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
    }
  }

  return (
    <AnimatePresence>
      {(loading || suggestions.length > 0) && (
        <motion.div
          ref={dropdownRef}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="absolute bottom-full left-0 mb-2 w-full max-w-md z-50"
        >
          <div className={`
            rounded-lg border shadow-lg overflow-hidden
            ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}
          `}>
            {loading && suggestions.length === 0 ? (
              <div className="p-3 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Génération de suggestions...</span>
              </div>
            ) : (
              <div className="max-h-64 overflow-y-auto">
                {suggestions.map((suggestion, index) => (
                  <motion.button
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => onSelect(suggestion)}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={`
                      w-full text-left p-3 border-b last:border-b-0
                      transition-colors
                      ${selectedIndex === index 
                        ? isDark 
                          ? 'bg-gray-700' 
                          : 'bg-gray-100'
                        : isDark
                          ? 'bg-gray-800 hover:bg-gray-700'
                          : 'bg-white hover:bg-gray-50'
                      }
                      ${isDark ? 'border-gray-700' : 'border-gray-200'}
                    `}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-0.5">
                        {getSuggestionIcon(suggestion.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`
                            text-sm font-medium
                            ${isDark ? 'text-white' : 'text-gray-900'}
                          `}>
                            {suggestion.text}
                          </span>
                          {suggestion.confidence && (
                            <span className={`
                              text-xs px-1.5 py-0.5 rounded
                              ${isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600'}
                            `}>
                              {Math.round(suggestion.confidence * 100)}%
                            </span>
                          )}
                        </div>
                        {suggestion.explanation && (
                          <p className={`
                            text-xs
                            ${isDark ? 'text-gray-400' : 'text-gray-500'}
                          `}>
                            {suggestion.explanation}
                          </p>
                        )}
                      </div>
                    </div>
                  </motion.button>
                ))}
              </div>
            )}
            {suggestions.length > 0 && (
              <div className={`
                px-3 py-2 text-xs border-t
                ${isDark ? 'bg-gray-800 border-gray-700 text-gray-400' : 'bg-gray-50 border-gray-200 text-gray-500'}
              `}>
                <kbd className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700">↑↓</kbd> Naviguer • 
                <kbd className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 ml-1">Tab</kbd> Accepter • 
                <kbd className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 ml-1">Entrée</kbd> Sélectionner • 
                <kbd className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 ml-1">Esc</kbd> Fermer
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default SuggestionDropdown

