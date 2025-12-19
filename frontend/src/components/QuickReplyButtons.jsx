import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../contexts/ThemeContext'

export const QuickReplyButtons = ({ 
  suggestions = [], 
  onSelect,
  visible = true 
}) => {
  const { isDark } = useTheme()
  
  if (!suggestions.length || !visible) return null
  
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
          className="flex flex-wrap gap-2 px-4 pb-2"
        >
          {suggestions.map((suggestion, index) => (
            <motion.button
              key={index}
              onClick={() => onSelect(suggestion)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                isDark
                  ? 'bg-[#2D3748] hover:bg-[#374151] text-gray-200'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
              }`}
              initial={{ opacity: 0, y: 10, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ 
                delay: index * 0.1,
                duration: 0.3,
                type: "spring",
                stiffness: 200
              }}
              whileHover={{ 
                scale: 1.05,
                y: -2,
                boxShadow: `0 4px 12px ${isDark ? 'rgba(139, 92, 246, 0.2)' : 'rgba(99, 102, 241, 0.2)'}`
              }}
              whileTap={{ scale: 0.95 }}
              onMouseDown={(e) => {
                // Morph animation: button becomes message bubble
                const button = e.currentTarget
                const rect = button.getBoundingClientRect()
                const messageArea = document.querySelector('[data-message-area]')
                
                if (messageArea) {
                  const messageRect = messageArea.getBoundingClientRect()
                  const x = messageRect.left - rect.left
                  const y = messageRect.top - rect.top
                  
                  // Create flying bubble effect
                  const bubble = button.cloneNode(true)
                  bubble.style.position = 'fixed'
                  bubble.style.left = `${rect.left}px`
                  bubble.style.top = `${rect.top}px`
                  bubble.style.width = `${rect.width}px`
                  bubble.style.pointerEvents = 'none'
                  document.body.appendChild(bubble)
                  
                  setTimeout(() => {
                    bubble.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)'
                    bubble.style.transform = `translate(${x}px, ${y}px) scale(0.8)`
                    bubble.style.opacity = '0'
                    
                    setTimeout(() => {
                      document.body.removeChild(bubble)
                    }, 500)
                  }, 10)
                }
              }}
            >
              {suggestion}
            </motion.button>
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

