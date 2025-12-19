import { useEffect, useState } from 'react'
import { motion, useReducedMotion, AnimatePresence } from 'framer-motion'
import { Bot, Sparkles, MessageCircle, Send, BookOpen, Lightbulb, Zap } from 'lucide-react'

const ModernWelcomeAnimation = ({ onQuickReply }) => {
  const shouldReduceMotion = useReducedMotion()
  const [stage, setStage] = useState(0) // 0: initial, 1: character, 2: messages, 3: input
  const [showTypingIndicator, setShowTypingIndicator] = useState(false)

  useEffect(() => {
    // Stage 1: Initial Load (0-1.5s) - Background and container fade in (slower)
    const timer1 = setTimeout(() => setStage(1), 1500)
    
    // Stage 2: Character Introduction (1.5-3.75s) - Avatar bounce in (slower)
    const timer2 = setTimeout(() => {
      setStage(2)
      setShowTypingIndicator(true)
    }, 3750)
    
    // Stage 3: Welcome Messages (3.75-6s) - Typing indicator for 1.2s, then messages (slower)
    const timer3 = setTimeout(() => {
      setShowTypingIndicator(false)
    }, 4950) // 3.75s + 1.2s = 4.95s
    
    // Stage 4: Input Field Emphasis (6-7.5s) - Input glow and quick replies (slower)
    const timer4 = setTimeout(() => setStage(3), 6000)

    return () => {
      clearTimeout(timer1)
      clearTimeout(timer2)
      clearTimeout(timer3)
      clearTimeout(timer4)
    }
  }, [])

  // Sparkle particles component
  const SparkleParticles = ({ count = 12 }) => {
    return (
      <div className="absolute inset-0 pointer-events-none">
        {Array.from({ length: count }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1.5 h-1.5 bg-cyan-400 rounded-full"
            initial={{ 
              opacity: 0,
              scale: 0,
              x: '50%',
              y: '50%'
            }}
            animate={{
              opacity: [0, 1, 0],
              scale: [0, 1, 0],
              x: `${50 + (Math.random() - 0.5) * 100}%`,
              y: `${50 + (Math.random() - 0.5) * 100}%`,
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              delay: i * 0.2,
              ease: "easeInOut"
            }}
            style={{
              filter: 'blur(0.5px)'
            }}
          />
        ))}
      </div>
    )
  }

  // Typing indicator component
  const TypingIndicator = () => (
    <div className="flex items-center gap-1 px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-2xl border border-cyan-200/30 dark:border-cyan-700/30">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 bg-cyan-500 dark:bg-cyan-400 rounded-full"
          animate={{
            y: [0, -8, 0],
            opacity: [0.5, 1, 0.5]
          }}
          transition={{
            duration: 0.9,
            repeat: Infinity,
            delay: i * 0.3,
            ease: "easeInOut"
          }}
        />
      ))}
    </div>
  )

  // Quick reply buttons
  const quickReplies = [
    { text: "Correction de texte", icon: BookOpen, action: () => onQuickReply?.("Correction de texte") },
    { text: "Poser une question", icon: MessageCircle, action: () => onQuickReply?.("Poser une question") },
    { text: "Reformulation", icon: Lightbulb, action: () => onQuickReply?.("Reformulation") },
  ]

  // Ripple Button Component
  const RippleButton = ({ reply, index, variants }) => {
    const [ripple, setRipple] = useState({ x: 0, y: 0, active: false })
    const Icon = reply.icon
    
    const handleClick = (e) => {
      const rect = e.currentTarget.getBoundingClientRect()
      setRipple({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
        active: true
      })
      setTimeout(() => {
        setRipple({ x: 0, y: 0, active: false })
        reply.action()
      }, 300)
    }
    
    return (
      <motion.button
        custom={index}
        variants={variants}
        initial="hidden"
        animate="visible"
        whileHover="hover"
        whileTap={{ scale: 0.95 }}
                      onClick={handleClick}
                      className="relative flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-50 to-blue-50 dark:from-cyan-900/30 dark:to-blue-900/30 border border-cyan-300 dark:border-cyan-700 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:shadow-xl hover:shadow-cyan-500/20 hover:border-cyan-400 dark:hover:border-cyan-500 transition-all overflow-hidden"
                    >
        <AnimatePresence>
          {ripple.active && (
            <motion.span
              className="absolute rounded-full bg-cyan-500/40"
              initial={{ width: 0, height: 0, x: ripple.x, y: ripple.y }}
              animate={{ width: 200, height: 200, x: ripple.x - 100, y: ripple.y - 100 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              style={{ pointerEvents: 'none' }}
            />
          )}
        </AnimatePresence>
        <Icon className="w-4 h-4 relative z-10" />
        <span className="relative z-10">{reply.text}</span>
      </motion.button>
    )
  }

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: shouldReduceMotion ? 0 : 1.5,
        ease: "easeOut"
      }
    }
  }

  const chatWindowVariants = {
    hidden: { 
      scale: shouldReduceMotion ? 1 : 0.95,
      opacity: 0 
    },
    visible: {
      scale: 1,
      opacity: 1,
      transition: {
        duration: shouldReduceMotion ? 0 : 1.2,
        ease: "easeOut"
      }
    }
  }

  const avatarVariants = {
    hidden: { 
      y: shouldReduceMotion ? 0 : 100,
      opacity: 0,
      scale: 0.5
    },
    visible: {
      y: 0,
      opacity: 1,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: shouldReduceMotion ? 100 : 150,
        damping: shouldReduceMotion ? 20 : 18,
        duration: shouldReduceMotion ? 0.3 : 1.2
      }
    }
  }

  const waveVariants = {
    wave: {
      rotate: [0, 14, -8, 14, -4, 10, 0],
      transition: {
        duration: 0.8,
        delay: 1.2,
        ease: "easeInOut"
      }
    }
  }

  const messageVariants = {
    hidden: { 
      y: shouldReduceMotion ? 0 : 30,
      opacity: 0,
      scale: 0.9
    },
    visible: (i) => ({
      y: 0,
      opacity: 1,
      scale: 1,
      transition: {
        delay: i * 0.75,
        duration: shouldReduceMotion ? 0.2 : 0.7,
        ease: "easeOut"
      }
    })
  }

  const inputGlowVariants = {
    pulse: {
      boxShadow: [
        "0 0 0px rgba(6, 182, 212, 0)",
        "0 0 25px rgba(6, 182, 212, 0.5)",
        "0 0 0px rgba(6, 182, 212, 0)"
      ],
      transition: {
        duration: 2,
        repeat: 2,
        ease: "easeInOut"
      }
    }
  }

  const buttonVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: (i) => ({
      opacity: 1,
      y: 0,
      transition: {
        delay: 0.15 * i,
        duration: shouldReduceMotion ? 0.2 : 0.6,
        ease: "easeOut"
      }
    }),
    hover: {
      y: -2,
      transition: {
        duration: 0.3,
        ease: "easeOut"
      }
    }
  }

  return (
    <motion.div
      className="absolute inset-0 flex items-center justify-center overflow-hidden"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Stage 1: Gradient Background - Modern teal/cyan to indigo */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-br from-slate-900 via-cyan-900 to-indigo-900"
        animate={{
          background: stage >= 0 ? [
            "linear-gradient(to bottom right, rgb(15, 23, 42), rgb(22, 78, 99), rgb(55, 48, 163))",
            "linear-gradient(to bottom right, rgb(55, 48, 163), rgb(22, 78, 99), rgb(15, 23, 42))",
            "linear-gradient(to bottom right, rgb(22, 78, 99), rgb(55, 48, 163), rgb(15, 23, 42))"
          ] : undefined
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      {/* Chat Window Container */}
      <motion.div
        className="relative w-full max-w-4xl mx-auto px-4"
        variants={chatWindowVariants}
        initial="hidden"
        animate={stage >= 0 ? "visible" : "hidden"}
        style={{
          filter: stage >= 0 ? "drop-shadow(0 0 40px rgba(6, 182, 212, 0.4))" : "none"
        }}
      >
        <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-3xl p-8 shadow-2xl border border-white/20">
          
          {/* Stage 2: Character Avatar */}
          {stage >= 1 && (
            <motion.div
              className="flex justify-center mb-8 relative"
              variants={avatarVariants}
              initial="hidden"
              animate="visible"
            >
              <div className="relative">
                {/* Avatar Circle - Modern cyan/teal gradient */}
                <motion.div
                  className="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-500 via-blue-500 to-indigo-600 flex items-center justify-center shadow-2xl shadow-cyan-500/50"
                  whileHover={{ scale: 1.05 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <Bot className="w-12 h-12 text-white drop-shadow-lg" />
                </motion.div>
                
                {/* Wave Animation */}
                {stage >= 1 && (
                  <motion.div
                    className="absolute -right-2 top-0 text-2xl"
                    variants={waveVariants}
                    animate="wave"
                  >
                    👋
                  </motion.div>
                )}
                
                {/* Sparkle Particles */}
                <SparkleParticles count={12} />
              </div>
            </motion.div>
          )}

          {/* Stage 3: Welcome Messages */}
          {stage >= 2 && (
            <div className="space-y-4 mb-8">
              {/* Typing Indicator */}
              {showTypingIndicator && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex justify-start"
                >
                  <TypingIndicator />
                </motion.div>
              )}

              {/* Message Bubbles */}
              {!showTypingIndicator && (
                <>
                  <motion.div
                    custom={0}
                    variants={messageVariants}
                    initial="hidden"
                    animate="visible"
                    className="flex justify-start"
                  >
                    <motion.div
                      className="bg-gradient-to-br from-cyan-50 to-blue-50 dark:from-cyan-900/40 dark:to-blue-900/40 rounded-2xl px-4 py-3 max-w-md border border-cyan-200/50 dark:border-cyan-700/50 shadow-lg"
                      whileHover={{ scale: 1.02, boxShadow: "0 10px 25px rgba(6, 182, 212, 0.2)" }}
                      transition={{ type: "spring", stiffness: 400 }}
                    >
                      <p className="text-slate-800 dark:text-slate-100 font-medium">
                        👋 Bonjour ! Je suis votre assistant académique.
                      </p>
                    </motion.div>
                  </motion.div>

                  <motion.div
                    custom={1}
                    variants={messageVariants}
                    initial="hidden"
                    animate="visible"
                    className="flex justify-start"
                  >
                    <motion.div
                      className="bg-gradient-to-br from-cyan-50 to-blue-50 dark:from-cyan-900/40 dark:to-blue-900/40 rounded-2xl px-4 py-3 max-w-md border border-cyan-200/50 dark:border-cyan-700/50 shadow-lg"
                      whileHover={{ scale: 1.02, boxShadow: "0 10px 25px rgba(6, 182, 212, 0.2)" }}
                      transition={{ type: "spring", stiffness: 400 }}
                    >
                      <p className="text-slate-800 dark:text-slate-100 font-medium">
                        Je peux vous aider avec la correction, les questions et la reformulation de textes.
                      </p>
                    </motion.div>
                  </motion.div>

                  <motion.div
                    custom={2}
                    variants={messageVariants}
                    initial="hidden"
                    animate="visible"
                    className="flex justify-start"
                  >
                    <motion.div
                      className="bg-gradient-to-br from-cyan-50 to-blue-50 dark:from-cyan-900/40 dark:to-blue-900/40 rounded-2xl px-4 py-3 max-w-md border border-cyan-200/50 dark:border-cyan-700/50 shadow-lg"
                      whileHover={{ scale: 1.02, boxShadow: "0 10px 25px rgba(6, 182, 212, 0.2)" }}
                      transition={{ type: "spring", stiffness: 400 }}
                    >
                      <p className="text-slate-800 dark:text-slate-100 font-medium">
                        Commençons ! Tapez votre message ou choisissez une option ci-dessous.
                      </p>
                    </motion.div>
                  </motion.div>
                </>
              )}
            </div>
          )}

          {/* Stage 4: Input Field & Quick Replies */}
          {stage >= 3 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              {/* Input Field with Glow */}
              <motion.div
                className="relative mb-6"
                variants={inputGlowVariants}
                animate={stage === 3 ? "pulse" : "hidden"}
              >
                <motion.div
                  className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 rounded-2xl px-4 py-3 border-2 border-transparent focus-within:border-cyan-500 transition-all"
                  whileFocus={{ scale: 1.02 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <input
                    type="text"
                    placeholder="Tapez votre message..."
                    className="flex-1 bg-transparent outline-none text-slate-900 dark:text-slate-100 placeholder-slate-500"
                    autoFocus
                  />
                  <motion.button
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-xl shadow-lg shadow-cyan-500/50"
                  >
                    <Send className="w-5 h-5" />
                  </motion.button>
                </motion.div>
              </motion.div>

              {/* Quick Reply Buttons */}
              <div className="flex flex-wrap gap-3 justify-center">
                {quickReplies.map((reply, i) => (
                  <RippleButton
                    key={i}
                    reply={reply}
                    index={i}
                    variants={buttonVariants}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}

export default ModernWelcomeAnimation

