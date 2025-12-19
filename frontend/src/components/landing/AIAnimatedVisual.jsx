import { motion } from 'framer-motion'
import { MessageSquare, Sparkles, Brain } from 'lucide-react'

const AIAnimatedVisual = () => {
  // Simple floating particles
  const particles = Array.from({ length: 8 }, (_, i) => ({
    id: i,
    x: 20 + Math.random() * 60,
    y: 20 + Math.random() * 60,
    delay: Math.random() * 2,
    duration: 5 + Math.random() * 3
  }))

  return (
    <div className="w-full h-full relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-500/10 via-blue-500/10 to-purple-500/10 backdrop-blur-sm">
      {/* Subtle Background Glow */}
      <motion.div
        className="absolute inset-0 rounded-3xl"
        style={{
          background: `
            radial-gradient(circle at 40% 40%, rgba(0, 217, 255, 0.2) 0%, transparent 60%),
            radial-gradient(circle at 60% 60%, rgba(139, 92, 246, 0.15) 0%, transparent 60%)
          `
        }}
        animate={{
          opacity: [0.6, 0.9, 0.6]
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'easeInOut'
        }}
      />

      {/* Simple Floating Particles */}
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute w-1.5 h-1.5 rounded-full bg-cyan-400/40"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`
          }}
          animate={{
            y: [0, -30, 0],
            opacity: [0.3, 0.7, 0.3]
          }}
          transition={{
            duration: particle.duration,
            repeat: Infinity,
            delay: particle.delay,
            ease: 'easeInOut'
          }}
        />
      ))}

      {/* Central AI Brain Icon */}
      <motion.div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20"
        animate={{
          scale: [1, 1.05, 1]
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: 'easeInOut'
        }}
      >
        <div className="relative">
          {/* Glow effect */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-br from-cyan-400 to-purple-500 rounded-full blur-2xl opacity-30"
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.2, 0.4, 0.2]
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: 'easeInOut'
            }}
            style={{
              width: '100px',
              height: '100px',
              left: '50%',
              top: '50%',
              transform: 'translate(-50%, -50%)'
            }}
          />
          {/* Brain icon */}
          <div className="relative w-20 h-20 bg-gradient-to-br from-cyan-400 via-blue-500 to-purple-500 rounded-full flex items-center justify-center shadow-xl shadow-cyan-500/30">
            <Brain className="w-10 h-10 text-white" strokeWidth={2} />
          </div>
        </div>
      </motion.div>

      {/* Simple Pulsing Ring */}
      <motion.div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 border border-cyan-400/20 rounded-full"
        style={{
          width: '100px',
          height: '100px'
        }}
        animate={{
          scale: [1, 1.6, 1],
          opacity: [0.3, 0, 0.3]
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: 'easeOut'
        }}
      />

      {/* Floating Chat Badges - Simplified */}
      <motion.div
        className="absolute top-6 left-6 z-10"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.5 }}
      >
        <motion.div
          className="bg-white/10 backdrop-blur-md rounded-lg px-3 py-2 border border-white/20 shadow-md"
          animate={{
            y: [0, -5, 0]
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        >
          <div className="flex items-center gap-2">
            <MessageSquare className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-white text-xs font-medium">AI Assistant</span>
          </div>
        </motion.div>
      </motion.div>

      <motion.div
        className="absolute bottom-6 right-6 z-10"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.8 }}
      >
        <motion.div
          className="bg-gradient-to-br from-cyan-500/20 to-blue-500/20 backdrop-blur-md rounded-lg px-3 py-2 border border-cyan-400/30 shadow-md"
          animate={{
            y: [0, -5, 0]
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            delay: 0.5,
            ease: 'easeInOut'
          }}
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-cyan-300" />
            <span className="text-white text-xs font-medium">Smart AI</span>
          </div>
        </motion.div>
      </motion.div>

      {/* Text */}
      <motion.div
        className="absolute bottom-12 left-1/2 -translate-x-1/2 z-10 text-center"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
      >
        <p className="text-white/90 text-sm font-semibold mb-1">AI-Powered</p>
        <p className="text-cyan-400/70 text-xs">Intelligent Conversations</p>
      </motion.div>
    </div>
  )
}

export default AIAnimatedVisual
