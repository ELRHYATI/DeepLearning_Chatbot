import { useState, useRef, useEffect, useCallback, memo } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { 
  Mail, Lock, User, Eye, EyeOff, Check, X, 
  Chrome, Github, Bot, LogIn, UserPlus, Loader2,
  CheckCircle2, AlertCircle, ArrowLeft, Home, Sparkles, MessageCircle
} from 'lucide-react'

// Input Component - Extracted outside to prevent re-creation on every render
const InputField = memo(({ 
  id, 
  label, 
  type, 
  placeholder,
  value, 
  onChange, 
  error,
  showToggle = false,
  onToggle,
  showValue,
  compact = false
}) => {
  return (
    <div className={compact ? "mb-2" : "mb-3"}>
      <label htmlFor={id} className={`block text-white/90 font-medium ${compact ? 'text-xs mb-1' : 'text-sm mb-2'}`}>
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={showToggle && !showValue ? 'password' : type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full ${compact ? 'px-3 py-2 text-sm' : 'px-4 py-2.5'} bg-gray-900/40 border rounded-2xl text-white/90 placeholder-gray-500/60 focus:outline-none focus:ring-2 focus:ring-purple-500/30 focus:border-purple-500/50 transition-all ${
            error ? 'border-red-500/50' : 'border-gray-700/50'
          }`}
        />
        {showToggle && (
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onToggle()
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
          >
            {showValue ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        )}
      </div>
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-1 text-sm text-red-400"
        >
          {error}
        </motion.p>
      )}
    </div>
  )
})

InputField.displayName = 'InputField'

const ModernAuth = ({ initialMode = 'login' }) => {
  const shouldReduceMotion = useReducedMotion()
  const [mode, setMode] = useState(initialMode) // 'login' or 'signup'
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [acceptTerms, setAcceptTerms] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [errors, setErrors] = useState({})
  const [passwordStrength, setPasswordStrength] = useState(0)
  const [isExiting, setIsExiting] = useState(false)
  
  const { login, register, loginWithGoogle, loginWithGitHub } = useAuth()
  const navigate = useNavigate()
  const rippleRef = useRef(null)

  // Form state
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  })

  // Calculate password strength
  const calculatePasswordStrength = (password) => {
    let strength = 0
    if (password.length >= 6) strength++
    if (password.length >= 8) strength++
    if (/[A-Z]/.test(password)) strength++
    if (/[0-9]/.test(password)) strength++
    if (/[^A-Za-z0-9]/.test(password)) strength++
    return Math.min(strength, 4)
  }

  const handleInputChange = useCallback((field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setErrors(prev => ({ ...prev, [field]: '' }))
    
    if (field === 'password') {
      setPasswordStrength(calculatePasswordStrength(value))
    }
  }, [])

  // Create stable handlers for each field to prevent re-renders
  const handleUsernameChange = useCallback((value) => handleInputChange('username', value), [handleInputChange])
  const handleEmailChange = useCallback((value) => handleInputChange('email', value), [handleInputChange])
  const handlePasswordChange = useCallback((value) => handleInputChange('password', value), [handleInputChange])
  const handleConfirmPasswordChange = useCallback((value) => handleInputChange('confirmPassword', value), [handleInputChange])

  const validateForm = () => {
    const newErrors = {}
    
    if (mode === 'signup' && !formData.username.trim()) {
      newErrors.username = 'Le nom d\'utilisateur est requis'
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'L\'email est requis'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email invalide'
    }
    
    if (!formData.password) {
      newErrors.password = 'Le mot de passe est requis'
    } else if (formData.password.length < 6) {
      newErrors.password = 'Le mot de passe doit contenir au moins 6 caractères'
    }
    
    if (mode === 'signup') {
      if (!formData.confirmPassword) {
        newErrors.confirmPassword = 'Veuillez confirmer le mot de passe'
      } else if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Les mots de passe ne correspondent pas'
      }
      
      if (!acceptTerms) {
        newErrors.terms = 'Vous devez accepter les conditions'
      }
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) return
    
    setLoading(true)
    setSuccess(false)
    
    try {
      let result
      if (mode === 'login') {
        result = await login(formData.email, formData.password)
      } else {
        result = await register(formData.username, formData.email, formData.password)
      }
      
      if (result.success) {
        setSuccess(true)
        setTimeout(() => {
          navigate('/')
        }, 1000)
      } else {
        setErrors({ submit: result.error || 'Une erreur est survenue' })
      }
    } catch (error) {
      setErrors({ submit: 'Une erreur est survenue' })
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleLogin = () => {
    loginWithGoogle()
  }

  const handleGitHubLogin = () => {
    loginWithGitHub()
  }

  const toggleMode = () => {
    setMode(prev => prev === 'login' ? 'signup' : 'login')
    setErrors({})
    setFormData({ username: '', email: '', password: '', confirmPassword: '' })
  }

  // Ensure mode is synced with initialMode on mount
  useEffect(() => {
    if (initialMode && initialMode !== mode) {
      setMode(initialMode)
    }
  }, [])

  // Step indicators for signup
  const steps = [
    { number: 1, label: 'Sign up your account', active: mode === 'signup' },
    { number: 2, label: 'Set up your workspace', active: false },
    { number: 3, label: 'Set up your profile', active: false }
  ]

  return (
    <div className="flex items-center justify-center min-h-screen w-screen relative overflow-hidden py-8" style={{ background: '#0F1419' }}>
      {/* Back Button */}
      <motion.button
        onClick={() => navigate('/')}
        className="absolute top-6 left-6 z-50 flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 rounded-lg text-white transition-all"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.3 }}
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="hidden sm:inline">Back</span>
      </motion.button>

      <div className={`w-full max-w-6xl mx-auto flex flex-col lg:flex-row items-stretch gap-4 lg:gap-6`}>
        {/* Left Panel - Gradient with Steps */}
        <motion.div
          className={`hidden lg:flex flex-col ${mode === 'signup' ? 'justify-start' : 'justify-between'} p-8 relative overflow-hidden rounded-3xl flex-1`}
          style={{ 
            minHeight: mode === 'signup' ? '650px' : '550px',
            height: '100%'
          }}
          style={{
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.6) 0%, rgba(118, 75, 162, 0.5) 50%, rgba(26, 31, 46, 0.7) 100%)',
            boxShadow: '0 10px 40px rgba(0, 217, 255, 0.15), 0 0 20px rgba(0, 217, 255, 0.1)'
          }}
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Animated background elements - more faded */}
          <div className="absolute inset-0 overflow-hidden">
            {Array.from({ length: 10 }).map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-32 h-32 rounded-full bg-white/3"
                initial={{
                  x: Math.random() * 100 + '%',
                  y: Math.random() * 100 + '%',
                }}
                animate={{
                  x: [null, Math.random() * 100 + '%'],
                  y: [null, Math.random() * 100 + '%'],
                  scale: [1, 1.2, 1],
                }}
                transition={{
                  duration: 10 + Math.random() * 10,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
            ))}
          </div>

          <div className="relative z-10">
            {/* Logo */}
            <motion.div
              className="flex items-center gap-3 mb-8"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="w-12 h-12 bg-white/15 backdrop-blur-sm rounded-2xl flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white/90" />
              </div>
              <span className="text-2xl font-bold text-white/90">Academic AI</span>
            </motion.div>

            {/* Animated Robot */}
            <motion.div
              className={`flex flex-col items-center ${mode === 'signup' ? 'mb-4' : 'mb-8'}`}
              initial={{ opacity: 0, scale: 0.5, y: 50 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ delay: 0.4, type: "spring", stiffness: 200 }}
            >
              {/* Robot Body */}
              <motion.div
                className="relative mb-4"
                animate={{
                  y: [0, -10, 0],
                  rotate: [0, 2, -2, 0]
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                {/* Robot Head */}
                <motion.div
                  className={`${mode === 'signup' ? 'w-24 h-24' : 'w-32 h-32'} bg-white/20 backdrop-blur-md rounded-3xl flex items-center justify-center border-2 border-white/30 relative`}
                  style={{
                    boxShadow: "0 8px 32px rgba(139, 92, 246, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.1) inset"
                  }}
                  animate={{
                    boxShadow: [
                      "0 8px 32px rgba(139, 92, 246, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.1) inset",
                      "0 12px 48px rgba(139, 92, 246, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.15) inset",
                      "0 8px 32px rgba(139, 92, 246, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.1) inset"
                    ]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  {/* Robot Eyes */}
                  <div className={`flex ${mode === 'signup' ? 'gap-3' : 'gap-4'}`}>
                    <motion.div
                      className={`${mode === 'signup' ? 'w-4 h-4' : 'w-6 h-6'} bg-purple-400 rounded-full`}
                      animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.8, 1, 0.8]
                      }}
                      transition={{
                        duration: 1.5,
                        repeat: Infinity,
                        delay: 0
                      }}
                    />
                    <motion.div
                      className={`${mode === 'signup' ? 'w-4 h-4' : 'w-6 h-6'} bg-purple-400 rounded-full`}
                      animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.8, 1, 0.8]
                      }}
                      transition={{
                        duration: 1.5,
                        repeat: Infinity,
                        delay: 0.2
                      }}
                    />
                  </div>
                  {/* Robot Mouth */}
                  <motion.div
                    className={`absolute ${mode === 'signup' ? 'bottom-4 w-10 h-2.5' : 'bottom-6 w-12 h-3'} bg-purple-400/60 rounded-full`}
                    animate={{
                      width: [48, 56, 48],
                      opacity: [0.6, 0.8, 0.6]
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity
                    }}
                  />
                </motion.div>
                
                {/* Robot Antenna */}
                <motion.div
                  className="absolute -top-4 left-1/2 -translate-x-1/2 w-2 h-8 bg-white/30 rounded-full"
                  animate={{
                    scaleY: [1, 1.1, 1],
                    opacity: [0.5, 0.8, 0.5]
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity
                  }}
                >
                  <motion.div
                    className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 bg-purple-300 rounded-full"
                    animate={{
                      scale: [1, 1.3, 1],
                      opacity: [0.7, 1, 0.7]
                    }}
                    transition={{
                      duration: 1,
                      repeat: Infinity
                    }}
                  />
                </motion.div>
              </motion.div>

              {/* Speech Bubble with Hello */}
              <motion.div
                className={`relative bg-white/20 backdrop-blur-md rounded-2xl border border-white/30 ${mode === 'signup' ? 'px-4 py-2' : 'px-6 py-3'}`}
                style={{
                  boxShadow: "0 4px 16px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(255, 255, 255, 0.1) inset"
                }}
                initial={{ opacity: 0, scale: 0, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ delay: 0.8, type: "spring", stiffness: 200, damping: 15 }}
              >
                <motion.div
                  className="flex items-center gap-2"
                  animate={{
                    scale: [1, 1.05, 1]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  <MessageCircle className={`${mode === 'signup' ? 'w-4 h-4' : 'w-5 h-5'} text-white/90`} />
                  <span className={`text-white/90 font-semibold ${mode === 'signup' ? 'text-base' : 'text-lg'}`}>
                    {mode === 'login' ? 'Hello again! 👋' : 'Hello! Welcome! 👋'}
                  </span>
                </motion.div>
                {/* Speech bubble tail */}
                <div 
                  className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-white/20 backdrop-blur-md border-l border-b border-white/30 transform rotate-45"
                  style={{
                    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)"
                  }}
                />
              </motion.div>
            </motion.div>

            {/* Heading */}
            <motion.h1
              className={`font-bold text-white/90 ${mode === 'signup' ? 'text-3xl mb-2' : 'text-4xl mb-4'}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              {mode === 'login' ? 'Welcome Back!' : 'Get Started with Us'}
            </motion.h1>
            <motion.p
              className={`text-white/70 ${mode === 'signup' ? 'text-base mb-6' : 'text-lg mb-12'}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              {mode === 'login' 
                ? 'Sign in to continue to your academic assistant' 
                : 'Complete these easy steps to register your account.'}
            </motion.p>
          </div>

          {/* Steps (only for signup) */}
          {mode === 'signup' && (
            <motion.div
              className="relative z-10 space-y-2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              {steps.map((step, index) => (
                <motion.div
                  key={step.number}
                  className={`flex items-center gap-3 p-3 rounded-xl transition-all backdrop-blur-sm ${
                    step.active
                      ? 'bg-white/25 text-white'
                      : 'bg-white/8 text-white/60'
                  }`}
                  style={{
                    boxShadow: step.active 
                      ? "0 4px 16px rgba(255, 255, 255, 0.1), 0 0 0 1px rgba(255, 255, 255, 0.2) inset"
                      : "0 2px 8px rgba(0, 0, 0, 0.1)"
                  }}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + index * 0.1, ease: "easeOut" }}
                  whileHover={{ 
                    scale: 1.02, 
                    x: 5,
                    boxShadow: "0 6px 20px rgba(255, 255, 255, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.25) inset"
                  }}
                >
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-sm ${
                      step.active
                        ? 'bg-purple-500/80 text-white'
                        : 'bg-white/15 text-white/70'
                    }`}
                  >
                    {step.number}
                  </div>
                  <span className="font-medium text-sm">{step.label}</span>
                </motion.div>
              ))}
            </motion.div>
          )}

          {/* Login mode content */}
          {mode === 'login' && (
            <motion.div
              className="relative z-10"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <motion.button
                onClick={toggleMode}
                className="px-6 py-3 bg-white/10 hover:bg-white/15 border border-white/20 rounded-2xl text-white/90 transition-all backdrop-blur-sm"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Don't have an account? Sign up
              </motion.button>
            </motion.div>
          )}
        </motion.div>

        {/* Right Panel - Form */}
        <motion.div
          className={`flex flex-col ${mode === 'signup' ? 'justify-start' : 'justify-center'} p-6 lg:p-8 bg-[#1A1F2E] rounded-3xl backdrop-blur-sm flex-1 overflow-y-auto`}
          style={{
            boxShadow: '0 10px 40px rgba(99, 102, 241, 0.15), 0 0 20px rgba(99, 102, 241, 0.1), inset 0 0 100px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.05)',
            minHeight: mode === 'signup' ? '650px' : '550px',
            height: '100%'
          }}
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <AnimatePresence mode="wait">
            {mode === 'login' ? (
              <motion.div
                key="login"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <h2 className="text-3xl font-bold text-white mb-2">Login Account</h2>
                <p className="text-gray-400 mb-8">Enter your credentials to access your account.</p>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <AnimatePresence>
                    {errors.submit && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="bg-red-500/20 border border-red-500 text-red-200 px-3 py-2 rounded-lg flex items-center gap-2 text-sm mb-2"
                      >
                        <AlertCircle className="w-4 h-4" />
                        {errors.submit}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <InputField
                    id="login-email"
                    label="Email"
                    type="email"
                    placeholder="eg. johnfrans@gmail.com"
                    value={formData.email}
                    onChange={handleEmailChange}
                    error={errors.email}
                  />

                  <InputField
                    id="login-password"
                    label="Password"
                    type="password"
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handlePasswordChange}
                    error={errors.password}
                    showToggle
                    onToggle={() => setShowPassword(!showPassword)}
                    showValue={showPassword}
                  />

                  <div className="flex items-center justify-between mb-4">
                    <label className="flex items-center gap-2 text-gray-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-purple-500 focus:ring-purple-500"
                      />
                      <span className="text-sm">Remember me</span>
                    </label>
                    <a href="#" className="text-sm text-purple-400 hover:text-purple-300">
                      Forgot password?
                    </a>
                  </div>

                  <motion.button
                    type="submit"
                    disabled={loading || success}
                    className="w-full py-3 bg-gradient-to-r from-purple-600/80 to-indigo-600/80 text-white rounded-2xl font-semibold shadow-lg shadow-purple-500/20 disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm"
                    whileHover={{ scale: loading ? 1 : 1.02 }}
                    whileTap={{ scale: loading ? 1 : 0.98 }}
                  >
                    {loading ? (
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Logging in...</span>
                      </div>
                    ) : success ? (
                      <div className="flex items-center justify-center gap-2">
                        <CheckCircle2 className="w-5 h-5" />
                        <span>Success!</span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center gap-2">
                        <LogIn className="w-5 h-5" />
                        <span>Login</span>
                      </div>
                    )}
                  </motion.button>

                  <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-700"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-4 bg-[#1A1F2E] text-gray-400">Or</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <motion.button
                      type="button"
                      onClick={handleGoogleLogin}
                      className="flex items-center justify-center gap-2 py-3 bg-gray-800/40 hover:bg-gray-800/60 border border-gray-700/50 rounded-2xl text-white/90 transition-all backdrop-blur-sm"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Chrome className="w-5 h-5" />
                      <span>Google</span>
                    </motion.button>
                    <motion.button
                      type="button"
                      onClick={handleGitHubLogin}
                      className="flex items-center justify-center gap-2 py-3 bg-gray-800/40 hover:bg-gray-800/60 border border-gray-700/50 rounded-2xl text-white/90 transition-all backdrop-blur-sm"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Github className="w-5 h-5" />
                      <span>Github</span>
                    </motion.button>
                  </div>

                  <p className="text-center text-gray-400 text-sm mt-6">
                    Don't have an account?{' '}
                    <button
                      type="button"
                      onClick={toggleMode}
                      className="text-purple-400 hover:text-purple-300 font-medium"
                    >
                      Sign up
                    </button>
                  </p>
                </form>
              </motion.div>
            ) : (
              <motion.div
                key="signup"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <h2 className="text-2xl lg:text-3xl font-bold text-white mb-1">Sign Up Account</h2>
                <p className="text-gray-400 text-sm mb-3">Enter your personal data to create your account.</p>

                <form onSubmit={handleSubmit} className="space-y-2.5 flex-1 flex flex-col">
                  <AnimatePresence>
                    {errors.submit && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="bg-red-500/20 border border-red-500 text-red-200 px-3 py-2 rounded-lg flex items-center gap-2 text-sm mb-2"
                      >
                        <AlertCircle className="w-4 h-4" />
                        {errors.submit}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div className="grid grid-cols-2 gap-2">
                    <InputField
                      id="signup-username"
                      label="Username"
                      type="text"
                      placeholder="eg. john_doe"
                      value={formData.username}
                      onChange={handleUsernameChange}
                      error={errors.username}
                      compact={true}
                    />

                    <InputField
                      id="signup-email"
                      label="Email"
                      type="email"
                      placeholder="eg. johnfrans@gmail.com"
                      value={formData.email}
                      onChange={handleEmailChange}
                      error={errors.email}
                      compact={true}
                    />
                  </div>

                  <InputField
                    id="signup-password"
                    label="Password"
                    type="password"
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handlePasswordChange}
                    error={errors.password}
                    showToggle
                    onToggle={() => setShowPassword(!showPassword)}
                    showValue={showPassword}
                    compact={true}
                  />

                  <InputField
                    id="signup-confirm-password"
                    label="Confirm Password"
                    type="password"
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={handleConfirmPasswordChange}
                    error={errors.confirmPassword}
                    showToggle
                    onToggle={() => setShowConfirmPassword(!showConfirmPassword)}
                    showValue={showConfirmPassword}
                    compact={true}
                  />

                  {formData.password && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-xs text-gray-500/70 -mt-1 mb-1"
                    >
                      Must be at least 8 characters.
                    </motion.p>
                  )}

                  <label className="flex items-center gap-2 text-gray-400 cursor-pointer mb-1">
                    <input
                      type="checkbox"
                      checked={acceptTerms}
                      onChange={(e) => setAcceptTerms(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-purple-500 focus:ring-purple-500"
                    />
                    <span className="text-xs">I agree to the terms and conditions</span>
                  </label>

                  <motion.button
                    type="submit"
                    disabled={loading || success}
                    className="w-full py-2.5 bg-gradient-to-r from-purple-600/80 to-indigo-600/80 text-white rounded-2xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm relative overflow-hidden text-sm"
                    style={{
                      boxShadow: "0 4px 16px rgba(139, 92, 246, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.1) inset"
                    }}
                    whileHover={{ 
                      scale: loading ? 1 : 1.02,
                      boxShadow: "0 6px 24px rgba(139, 92, 246, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.15) inset"
                    }}
                    whileTap={{ scale: loading ? 1 : 0.98 }}
                    transition={{ duration: 0.2 }}
                  >
                    {loading ? (
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Creating account...</span>
                      </div>
                    ) : success ? (
                      <div className="flex items-center justify-center gap-2">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Account created!</span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center gap-2">
                        <UserPlus className="w-4 h-4" />
                        <span>Sign Up</span>
                      </div>
                    )}
                  </motion.button>

                  <div className="relative my-2">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-700"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-4 bg-[#1A1F2E] text-gray-400">Or</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <motion.button
                      type="button"
                      onClick={handleGoogleLogin}
                      className="flex items-center justify-center gap-2 py-2 bg-gray-800/40 hover:bg-gray-800/60 border border-gray-700/50 rounded-2xl text-white/90 transition-all backdrop-blur-sm text-sm"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Chrome className="w-4 h-4" />
                      <span>Google</span>
                    </motion.button>
                    <motion.button
                      type="button"
                      onClick={handleGitHubLogin}
                      className="flex items-center justify-center gap-2 py-2 bg-gray-800/40 hover:bg-gray-800/60 border border-gray-700/50 rounded-2xl text-white/90 transition-all backdrop-blur-sm text-sm"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Github className="w-4 h-4" />
                      <span>Github</span>
                    </motion.button>
                  </div>

                  <p className="text-center text-gray-400 text-xs mt-2 mb-0">
                    Already have an account?{' '}
                    <button
                      type="button"
                      onClick={toggleMode}
                      className="text-purple-400 hover:text-purple-300 font-medium"
                    >
                      Login
                    </button>
                  </p>
                </form>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  )
}

export default ModernAuth
