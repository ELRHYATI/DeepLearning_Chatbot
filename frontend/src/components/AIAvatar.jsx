import { motion } from 'framer-motion'
import { Bot } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

const avatarVariants = {
  idle: {
    scale: [1, 1.02, 1],
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: "easeInOut"
    }
  },
  speaking: {
    scale: [1, 1.05, 1],
    rotate: [0, 5, -5, 0],
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: "easeInOut"
    }
  },
  thinking: {
    scale: [1, 1.03, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut"
    }
  },
  success: {
    scale: [1, 1.1, 1],
    transition: {
      duration: 0.5,
      ease: "easeOut"
    }
  }
}

export const AIAvatar = ({ state = 'idle', size = 40 }) => {
  const { isDark } = useTheme()
  
  return (
    <div className="relative">
      <motion.div
        className={`rounded-full p-2 ${
          isDark 
            ? 'bg-gradient-to-br from-purple-600/20 to-indigo-600/20' 
            : 'bg-gradient-to-br from-purple-100 to-indigo-100'
        }`}
        variants={avatarVariants}
        animate={state}
        style={{
          border: state === 'speaking' 
            ? `2px dashed ${isDark ? '#8B5CF6' : '#6366F1'}`
            : '2px solid transparent'
        }}
      >
        <Bot 
          className={`${isDark ? 'text-purple-400' : 'text-indigo-600'}`}
          size={size}
        />
      </motion.div>
      
      {/* Glow effect for success state */}
      {state === 'success' && (
        <motion.div
          className={`absolute inset-0 rounded-full ${
            isDark ? 'bg-purple-500/30' : 'bg-indigo-500/20'
          }`}
          initial={{ opacity: 0, scale: 1 }}
          animate={{ opacity: [0, 1, 0], scale: [1, 1.5, 1.5] }}
          transition={{ duration: 0.5 }}
        />
      )}
      
      {/* Particles for thinking state */}
      {state === 'thinking' && (
        <>
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className={`absolute w-1 h-1 rounded-full ${
                isDark ? 'bg-purple-400' : 'bg-indigo-500'
              }`}
              style={{
                top: '50%',
                left: '50%',
              }}
              animate={{
                x: [
                  0,
                  Math.cos((i * 2 * Math.PI) / 3) * 20,
                  Math.cos((i * 2 * Math.PI) / 3) * 20,
                  0
                ],
                y: [
                  0,
                  Math.sin((i * 2 * Math.PI) / 3) * 20,
                  Math.sin((i * 2 * Math.PI) / 3) * 20,
                  0
                ],
                opacity: [0, 1, 1, 0]
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut"
              }}
            />
          ))}
        </>
      )}
    </div>
  )
}

