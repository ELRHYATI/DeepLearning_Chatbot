import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../contexts/ThemeContext'
import { Brain, Sparkles, Loader2 } from 'lucide-react'
import { useState, useEffect } from 'react'

const thinkingMessages = [
  "Analyse de votre question...",
  "Recherche d'informations...",
  "Consultation des documents...",
  "Génération de la réponse...",
  "Finalisation..."
]

export const ThinkingIndicator = ({ stage = 0 }) => {
  const { isDark } = useTheme()
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)
  const [displayedMessage, setDisplayedMessage] = useState(thinkingMessages[0])

  useEffect(() => {
    if (stage >= thinkingMessages.length) {
      setDisplayedMessage(thinkingMessages[thinkingMessages.length - 1])
      return
    }
    
    setDisplayedMessage(thinkingMessages[stage] || thinkingMessages[0])
    
    // Auto-rotate messages every 2 seconds if still thinking
    const interval = setInterval(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % thinkingMessages.length)
    }, 2000)

    return () => clearInterval(interval)
  }, [stage])

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`flex items-center gap-3 px-4 py-3 rounded-2xl ${
        isDark 
          ? 'bg-gradient-to-r from-purple-900/20 to-indigo-900/20 border border-purple-500/20' 
          : 'bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200/50'
      }`}
      style={{
        boxShadow: isDark
          ? '0 4px 20px rgba(139, 92, 246, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
          : '0 4px 20px rgba(139, 92, 246, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.8)'
      }}
    >
      {/* Animated brain icon */}
      <motion.div
        animate={{
          rotate: [0, 5, -5, 0],
          scale: [1, 1.1, 1]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        className="flex-shrink-0"
      >
        <Brain className={`w-5 h-5 ${
          isDark ? 'text-purple-400' : 'text-purple-600'
        }`} />
      </motion.div>

      {/* Thinking message */}
      <div className="flex-1 min-w-0">
        <AnimatePresence mode="wait">
          <motion.div
            key={displayedMessage}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ duration: 0.3 }}
            className={`text-sm font-medium ${
              isDark ? 'text-purple-300' : 'text-purple-700'
            }`}
          >
            {displayedMessage}
          </motion.div>
        </AnimatePresence>
        
        {/* Animated dots */}
        <div className="flex items-center gap-1 mt-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className={`w-1.5 h-1.5 rounded-full ${
                isDark ? 'bg-purple-400' : 'bg-purple-500'
              }`}
              animate={{
                opacity: [0.3, 1, 0.3],
                scale: [0.8, 1, 0.8]
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut"
              }}
            />
          ))}
        </div>
      </div>

      {/* Spinning loader */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "linear"
        }}
        className="flex-shrink-0"
      >
        <Loader2 className={`w-4 h-4 ${
          isDark ? 'text-purple-400' : 'text-purple-600'
        }`} />
      </motion.div>
    </motion.div>
  )
}

export default ThinkingIndicator

