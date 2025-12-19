import { motion } from 'framer-motion'
import { useTheme } from '../contexts/ThemeContext'
import { Sparkles, BookOpen, FileText, MessageSquare, Lightbulb, Play, Check, ArrowUp, Brain, GraduationCap, Languages, Zap, LogIn, UserPlus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

const LandingPage = ({ onCreateSession }) => {
  const { isDark } = useTheme()
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const containerRef = useRef(null)
  const [scrollingTo, setScrollingTo] = useState(null)

  const handleGetStarted = () => {
    if (onCreateSession) {
      onCreateSession()
    }
  }

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId)
    
    if (!element) {
      console.error(`Element with id "${sectionId}" not found`)
      return
    }

    setScrollingTo(sectionId)
    
    const headerOffset = 100 // Account for fixed header
    
    // Try to find the scrollable container (could be window or a div)
    const container = containerRef.current
    const isContainerScrollable = container && container.scrollHeight > container.clientHeight
    
    let scrollElement, startPosition, targetScroll
    
    if (isContainerScrollable && container) {
      // Scroll the container
      const containerRect = container.getBoundingClientRect()
      const elementRect = element.getBoundingClientRect()
      startPosition = container.scrollTop
      const elementTopRelative = elementRect.top - containerRect.top
      targetScroll = startPosition + elementTopRelative - headerOffset
      scrollElement = container
    } else {
      // Scroll the window
      const elementRect = element.getBoundingClientRect()
      startPosition = window.pageYOffset || document.documentElement.scrollTop
      targetScroll = elementRect.top + startPosition - headerOffset
      scrollElement = window
    }

    const distance = targetScroll - startPosition
    const duration = 1000 // milliseconds
    let start = null
    let rafId = null

    // Easing function for smooth acceleration and deceleration
    const easeInOutCubic = (t) => {
      return t < 0.5 
        ? 4 * t * t * t 
        : 1 - Math.pow(-2 * t + 2, 3) / 2
    }

    const animateScroll = (currentTime) => {
      if (start === null) start = currentTime
      const timeElapsed = currentTime - start
      const progress = Math.min(timeElapsed / duration, 1)
      const ease = easeInOutCubic(progress)
      
      const newScroll = startPosition + distance * ease
      
      if (scrollElement === window) {
        window.scrollTo(0, newScroll)
      } else {
        scrollElement.scrollTop = newScroll
      }
      
      if (progress < 1) {
        rafId = requestAnimationFrame(animateScroll)
      } else {
        // Ensure we're exactly at the target position
        if (scrollElement === window) {
          window.scrollTo(0, targetScroll)
        } else {
          scrollElement.scrollTop = targetScroll
        }
        // Reset animation after scroll completes
        setTimeout(() => {
          setScrollingTo(null)
        }, 300)
      }
    }

    rafId = requestAnimationFrame(animateScroll)
  }

  // Central glowing sphere component with animated rings
  const GlowingSphere = () => {
    const sphereRef = useRef(null)
    
    useEffect(() => {
      const sphere = sphereRef.current
      if (!sphere) return

      // Create animated particles
      const particles = []
      for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div')
        particle.className = 'absolute w-1 h-1 bg-blue-400 rounded-full opacity-60'
        sphere.appendChild(particle)
        particles.push({
          element: particle,
          angle: (i / 20) * Math.PI * 2,
          radius: 80 + Math.random() * 40,
          speed: 0.01 + Math.random() * 0.02
        })
      }

      let animationFrame
      const animate = () => {
        particles.forEach((p, idx) => {
          p.angle += p.speed
          const x = Math.cos(p.angle) * p.radius
          const y = Math.sin(p.angle) * p.radius
          p.element.style.transform = `translate(${x}px, ${y}px)`
        })
        animationFrame = requestAnimationFrame(animate)
      }
      animate()

      return () => {
        if (animationFrame) cancelAnimationFrame(animationFrame)
        particles.forEach(p => p.element.remove())
      }
    }, [])

    return (
      <div className="relative w-96 h-96 mx-auto" ref={sphereRef}>
        {/* Outer glow layers */}
        <motion.div 
          className="absolute inset-0 rounded-full blur-3xl"
          style={{
            background: 'radial-gradient(circle, rgba(59, 130, 246, 0.4) 0%, rgba(139, 92, 246, 0.2) 50%, transparent 100%)'
          }}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3]
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        
        {/* Animated rings */}
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="absolute inset-0 rounded-full border"
            style={{
              borderColor: `rgba(59, 130, 246, ${0.3 - i * 0.1})`,
              borderWidth: '2px',
              top: `${i * 10}%`,
              left: `${i * 10}%`,
              width: `${100 - i * 20}%`,
              height: `${100 - i * 20}%`,
            }}
            animate={{
              rotate: (i % 2 === 0 ? 360 : -360),
              scale: [1, 1.1, 1],
            }}
            transition={{
              rotate: { duration: 20 + i * 5, repeat: Infinity, ease: "linear" },
              scale: { duration: 3 + i, repeat: Infinity, ease: "easeInOut" }
            }}
          />
        ))}
        
        {/* Inner core with pulsing effect */}
        <motion.div 
          className="absolute inset-0 flex items-center justify-center"
          animate={{
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <div 
            className="w-40 h-40 rounded-full"
            style={{
              background: 'radial-gradient(circle, rgba(59, 130, 246, 0.9) 0%, rgba(139, 92, 246, 0.7) 100%)',
              boxShadow: '0 0 60px rgba(59, 130, 246, 0.8), 0 0 120px rgba(139, 92, 246, 0.6), inset 0 0 60px rgba(59, 130, 246, 0.4)'
            }}
          />
        </motion.div>
      </div>
    )
  }

  // Connection line component
  const ConnectionLine = ({ from, to, delay = 0 }) => {
    const angle = Math.atan2(to.y - from.y, to.x - from.x) * 180 / Math.PI
    const distance = Math.sqrt(Math.pow(to.x - from.x, 2) + Math.pow(to.y - from.y, 2))
    
    return (
      <motion.svg
        className="absolute top-0 left-0 w-full h-full pointer-events-none z-0"
        style={{ overflow: 'visible' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay }}
      >
        <motion.line
          x1={`${from.x}%`}
          y1={`${from.y}%`}
          x2={`${to.x}%`}
          y2={`${to.y}%`}
          stroke="url(#gradient)"
          strokeWidth="2"
          strokeDasharray="5,5"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.5, delay, ease: "easeOut" }}
        />
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(59, 130, 246, 0.8)" />
            <stop offset="100%" stopColor="rgba(59, 130, 246, 0)" />
          </linearGradient>
        </defs>
      </motion.svg>
    )
  }

  // Module positions relative to center (50%, 50%)
  const centerPos = { x: 50, y: 50 }
  const modulePositions = {
    taskLists: { x: 20, y: 25 },
    analytics: { x: 80, y: 25 },
    workflows: { x: 20, y: 75 },
    insights: { x: 80, y: 75 }
  }

  return (
    <div 
      ref={containerRef}
      className="min-h-screen w-screen overflow-y-auto relative"
      style={{ 
        background: '#0A0E1A',
        backgroundImage: 'radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)'
      }}
    >
      {/* Header - Fixed at top */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="fixed top-0 left-0 right-0 flex items-center justify-between px-12 py-6 z-50 bg-[#0A0E1A]/80 backdrop-blur-md border-b border-gray-800/50"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/50">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl font-bold text-white">
            Academic AI
          </span>
        </div>
        
        <div className="flex items-center gap-4">
          <motion.button
            onClick={() => scrollToSection('features')}
            className="text-gray-300 hover:text-blue-400 transition-colors text-sm font-medium"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Features
          </motion.button>
          <motion.button
            onClick={() => scrollToSection('help')}
            className="text-gray-300 hover:text-blue-400 transition-colors text-sm font-medium"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Help
          </motion.button>
          <motion.button
            onClick={() => scrollToSection('examples')}
            className="text-gray-300 hover:text-blue-400 transition-colors text-sm font-medium"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Examples
          </motion.button>
          {!isAuthenticated ? (
            <>
              <motion.button
                onClick={() => navigate('/login')}
                className="px-5 py-2 text-gray-300 hover:text-white transition-colors text-sm font-medium flex items-center gap-2"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <LogIn className="w-4 h-4" />
                Login
              </motion.button>
              <motion.button
                onClick={() => navigate('/signup')}
                className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg shadow-blue-500/30 flex items-center gap-2"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <UserPlus className="w-4 h-4" />
                Register
              </motion.button>
            </>
          ) : (
            <motion.button
              onClick={handleGetStarted}
              className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg shadow-blue-500/30"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Get started
            </motion.button>
          )}
        </div>
      </motion.div>

      {/* Main Content - with top padding for fixed header */}
      <div className="flex flex-col items-center px-12 pt-28 pb-8 relative scroll-smooth">
        {/* Hero Section - Title and Subtitle */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="text-center mb-12 w-full max-w-4xl mx-auto"
        >
          <h1 className="text-5xl md:text-6xl font-bold mb-6 text-white leading-tight">
            Your AI assistant for{' '}
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-blue-400 bg-clip-text text-transparent">
              academic excellence
            </span>
          </h1>
          <p className="text-lg md:text-xl text-gray-300 leading-relaxed max-w-3xl mx-auto mb-8">
            Harness the power of AI to correct grammar, answer questions, reformulate texts, and enhance your academic writing — all in one intelligent platform.
          </p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <motion.button
              onClick={handleGetStarted}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold text-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg shadow-blue-500/30 flex items-center gap-3"
              whileHover={{ scale: 1.05, boxShadow: "0 10px 30px rgba(59, 130, 246, 0.4)" }}
              whileTap={{ scale: 0.95 }}
            >
              <MessageSquare className="w-6 h-6" />
              Start Chatting
            </motion.button>
            {!isAuthenticated && (
              <motion.button
                onClick={() => navigate('/signup')}
                className="px-8 py-4 text-white/90 bg-white/10 hover:bg-white/20 rounded-xl font-semibold text-lg transition-all border border-white/20 flex items-center gap-3"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <UserPlus className="w-6 h-6" />
                Sign Up Free
              </motion.button>
            )}
          </motion.div>
        </motion.div>

        {/* Central Glowing Sphere - Background Animation */}
        <div className="absolute top-[55%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-0 pointer-events-none">
          <GlowingSphere />
        </div>
        
        {/* Connection Lines */}
        <ConnectionLine from={modulePositions.taskLists} to={centerPos} delay={1} />
        <ConnectionLine from={modulePositions.analytics} to={centerPos} delay={1.1} />
        <ConnectionLine from={modulePositions.workflows} to={centerPos} delay={1.2} />
        <ConnectionLine from={modulePositions.insights} to={centerPos} delay={1.3} />

        {/* Modules Grid - Start immediately after header */}
        <div className="grid grid-cols-2 gap-6 relative z-30 w-full max-w-5xl">
            {/* Features Module - Top Left */}
            <motion.div
              id="features"
              initial={{ opacity: 0, x: -50 }}
              animate={{ 
                opacity: 1, 
                x: 0,
                scale: scrollingTo === 'features' ? 1.02 : 1,
              }}
              transition={{ delay: 0.3, duration: 0.6 }}
              className={`p-5 rounded-xl border backdrop-blur-md ${
                isDark 
                  ? 'bg-gray-900/70 border-gray-800/50' 
                  : 'bg-white/10 border-gray-700/30'
              } shadow-xl hover:shadow-blue-500/20 transition-all`}
              style={{ 
                boxShadow: scrollingTo === 'features' 
                  ? '0 0 40px rgba(59, 130, 246, 0.4)' 
                  : '0 0 20px rgba(59, 130, 246, 0.1)'
              }}
            >
              <h3 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-400" />
                Features
              </h3>
              <div className="space-y-2.5">
                {[
                  { text: 'Grammar correction', checked: true, icon: Languages },
                  { text: 'Q&A assistance', checked: true, icon: Brain },
                  { text: 'Text reformulation', checked: true, icon: FileText },
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7 + idx * 0.1 }}
                    className="flex items-center gap-2.5"
                  >
                    <item.icon className="w-4 h-4 text-blue-400 flex-shrink-0" />
                    <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all flex-shrink-0 ${
                      item.checked 
                        ? 'bg-blue-500 border-blue-500' 
                        : 'border-gray-600'
                    }`}>
                      {item.checked && <Check className="w-2.5 h-2.5 text-white" />}
                    </div>
                    <span className="text-sm text-gray-300">
                      {item.text}
                    </span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Recent Conversations Module - Top Right */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
              className={`p-5 rounded-xl border-l-4 border-blue-500 backdrop-blur-md ${
                isDark 
                  ? 'bg-gray-900/70 border-gray-800/50' 
                  : 'bg-white/10 border-gray-700/30'
              } shadow-xl hover:shadow-purple-500/20 transition-all`}
              style={{ boxShadow: '0 0 20px rgba(59, 130, 246, 0.1)' }}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-400" />
                  Recent Chats
                </h3>
                <span className="text-xs text-green-400 font-semibold">Active</span>
              </div>
              <div className="space-y-2.5">
                {[
                  { text: 'Grammar correction', time: '2 min ago', icon: Languages },
                  { text: 'Question about AI', time: '15 min ago', icon: Brain },
                  { text: 'Text reformulation', time: '1 hour ago', icon: FileText },
                  { text: 'Academic writing', time: '2 hours ago', icon: GraduationCap },
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 + idx * 0.1 }}
                    className="flex items-center gap-2.5 p-1.5 rounded-lg hover:bg-gray-800/30 transition-colors cursor-pointer"
                  >
                    <item.icon className="w-4 h-4 text-blue-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-300 truncate">{item.text}</p>
                      <p className="text-xs text-gray-500">{item.time}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Document Processing Module - Bottom Left */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5, duration: 0.6 }}
              className={`p-5 rounded-xl border-2 border-purple-500/50 backdrop-blur-md ${
                isDark 
                  ? 'bg-gray-900/70 border-purple-500/30' 
                  : 'bg-white/10 border-purple-500/20'
              } shadow-xl hover:shadow-purple-500/20 transition-all`}
              style={{ boxShadow: '0 0 20px rgba(139, 92, 246, 0.1)' }}
            >
              <h3 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-purple-400" />
                Document Processing
              </h3>
              <div className="space-y-2.5">
                {[
                  { text: 'Upload PDF document', icon: FileText, checked: true },
                  { text: 'AI analysis & correction', icon: Brain },
                  { text: 'Download improved version', icon: FileText },
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.9 + idx * 0.1 }}
                    className="flex items-center gap-2.5"
                  >
                    <item.icon className="w-4 h-4 text-purple-400 flex-shrink-0" />
                    {item.checked && <Check className="w-4 h-4 text-green-400 flex-shrink-0" />}
                    <span className="text-sm text-gray-300">
                      {item.text}
                    </span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Quick Tips Module - Bottom Right */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6, duration: 0.6 }}
              className={`p-5 rounded-xl border-2 border-yellow-500/50 backdrop-blur-md ${
                isDark 
                  ? 'bg-gray-900/70 border-yellow-500/30' 
                  : 'bg-white/10 border-yellow-500/20'
              } shadow-xl hover:shadow-yellow-500/20 transition-all`}
              style={{ boxShadow: '0 0 20px rgba(234, 179, 8, 0.1)' }}
            >
              <h3 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-yellow-400" />
                Quick Tips
              </h3>
              <div className="space-y-2.5">
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 1 }}
                  className="flex items-center gap-2.5"
                >
                  <ArrowUp className="w-4 h-4 text-green-400 flex-shrink-0" />
                  <span className="text-sm text-gray-300">
                    Use reformulation for plagiarism-free text
                  </span>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 1.1 }}
                  className="flex items-center gap-2.5"
                >
                  <GraduationCap className="w-4 h-4 text-blue-400 flex-shrink-0" />
                  <span className="text-sm text-gray-300">
                    Improve academic writing quality
                  </span>
                </motion.div>
              </div>
            </motion.div>
          </div>

        {/* Examples Section */}
        <motion.div 
          id="examples" 
          className="mt-16 mb-12 w-full max-w-4xl mx-auto"
          animate={{
            scale: scrollingTo === 'examples' ? 1.02 : 1,
          }}
          transition={{ duration: 0.3 }}
        >
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-10"
          >
            <h2 className="text-4xl font-bold text-white mb-3">See It in Action</h2>
            <p className="text-lg text-gray-400">Examples of what Academic AI can do for you</p>
          </motion.div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                title: 'Grammar Correction',
                description: 'Fix spelling and grammar errors in your text',
                icon: Languages,
                example: 'Before: "I has a good idea"\nAfter: "I have a good idea"'
              },
              {
                title: 'Q&A Assistant',
                description: 'Get instant answers to your academic questions',
                icon: Brain,
                example: 'Q: "What is machine learning?"\nA: Detailed explanation...'
              },
              {
                title: 'Text Reformulation',
                description: 'Rephrase text in different academic styles',
                icon: FileText,
                example: 'Transform your text into formal, academic, or simple style'
              }
            ].map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                className={`p-6 rounded-xl border backdrop-blur-md ${
                  isDark 
                    ? 'bg-gray-900/60 border-gray-800/50' 
                    : 'bg-white/10 border-gray-700/30'
                } hover:border-blue-500/50 transition-all cursor-pointer`}
              >
                <feature.icon className="w-8 h-8 text-blue-400 mb-3" />
                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-400 mb-3">{feature.description}</p>
                <pre className="text-xs text-gray-500 bg-gray-900/50 p-2 rounded overflow-x-auto">
                  {feature.example}
                </pre>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Call to Action Section - Login/Register */}
        {!isAuthenticated && (
          <motion.div
            id="help"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mt-20 mb-12 w-full max-w-3xl mx-auto text-center"
            animate={{
              scale: scrollingTo === 'help' ? 1.02 : 1,
            }}
            transition={{ duration: 0.3 }}
          >
            <div className={`p-8 rounded-2xl border-2 backdrop-blur-md ${
              isDark 
                ? 'bg-gradient-to-br from-blue-900/30 to-purple-900/30 border-blue-500/50' 
                : 'bg-gradient-to-br from-blue-50/50 to-purple-50/50 border-blue-300/50'
            } shadow-2xl`}>
              <h2 className="text-3xl font-bold text-white mb-4">
                Ready to Get Started?
              </h2>
              <p className="text-lg text-gray-300 mb-8">
                Create an account to save your conversations, access advanced features, and unlock the full power of Academic AI.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <motion.button
                  onClick={() => navigate('/signup')}
                  className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg shadow-blue-500/30 flex items-center gap-2"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <UserPlus className="w-5 h-5" />
                  Create Free Account
                </motion.button>
                <motion.button
                  onClick={() => navigate('/login')}
                  className="px-8 py-3 text-white/90 bg-white/10 hover:bg-white/20 rounded-lg font-semibold transition-all border border-white/20 flex items-center gap-2"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <LogIn className="w-5 h-5" />
                  Already have an account? Login
                </motion.button>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default LandingPage
