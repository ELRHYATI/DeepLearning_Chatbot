import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../contexts/ThemeContext'
import { Brain, Search, FileText, Sparkles, MessageSquare, Lightbulb, CheckCircle2 } from 'lucide-react'
import { useState, useEffect } from 'react'

// Different thinking stages with detailed messages
const thinkingStages = [
  {
    icon: MessageSquare,
    title: "Analyse de votre demande",
    description: "Je comprends que vous souhaitez...",
    details: "Analyse du contexte et de l'intention"
  },
  {
    icon: Search,
    title: "Recherche d'informations",
    description: "Consultation de mes connaissances et documents...",
    details: "Recherche dans la base de connaissances et vos documents"
  },
  {
    icon: FileText,
    title: "Traitement du contenu",
    description: "Analyse et structuration des informations trouvées...",
    details: "Extraction des informations pertinentes"
  },
  {
    icon: Brain,
    title: "Réflexion et synthèse",
    description: "Je réfléchis à la meilleure façon de répondre...",
    details: "Synthèse des informations et formulation de la réponse"
  },
  {
    icon: Sparkles,
    title: "Génération de la réponse",
    description: "Création de la réponse personnalisée...",
    details: "Mise en forme et finalisation"
  }
]

// Simulated internal "conversation" thoughts
const getInternalThoughts = (stage) => {
  // Ensure stage is a valid integer
  const safeStage = typeof stage === 'number' ? Math.max(0, Math.min(Math.floor(stage), 4)) : 0
  
  const thoughts = {
    0: [
      "L'utilisateur demande...",
      "Le contexte suggère...",
      "Je dois identifier le type de question..."
    ],
    1: [
      "Recherche dans les documents de l'utilisateur...",
      "Consultation de la base de connaissances...",
      "Vérification des sources disponibles..."
    ],
    2: [
      "Extraction des informations clés...",
      "Vérification de la pertinence...",
      "Organisation des données..."
    ],
    3: [
      "Comment structurer la réponse ?",
      "Quels points sont les plus importants ?",
      "Comment rendre cela clair et utile ?"
    ],
    4: [
      "Formulation de la réponse...",
      "Vérification de la cohérence...",
      "Finalisation..."
    ]
  }
  return thoughts[safeStage] || thoughts[0]
}

export const AdvancedThinkingIndicator = ({ stage = 0, userQuery = "" }) => {
  const { isDark } = useTheme()
  const [currentThoughtIndex, setCurrentThoughtIndex] = useState(0)
  const [showInternalThoughts, setShowInternalThoughts] = useState(false)
  
  // Ensure stage is a valid integer
  const safeStage = typeof stage === 'number' ? Math.max(0, Math.min(Math.floor(stage), thinkingStages.length - 1)) : 0
  const currentStage = thinkingStages[safeStage]
  const Icon = currentStage.icon
  const internalThoughts = getInternalThoughts(safeStage)
  
  // Ensure userQuery is a string
  const safeUserQuery = typeof userQuery === 'string' ? userQuery : (userQuery ? String(userQuery) : '')

  // Rotate through internal thoughts
  useEffect(() => {
    if (showInternalThoughts && internalThoughts.length > 0) {
      const interval = setInterval(() => {
        setCurrentThoughtIndex((prev) => (prev + 1) % internalThoughts.length)
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [showInternalThoughts, internalThoughts.length])

  // Show internal thoughts after a delay
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowInternalThoughts(true)
    }, 1000)
    return () => clearTimeout(timer)
  }, [safeStage])

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`w-full max-w-2xl rounded-2xl overflow-hidden ${
        isDark 
          ? 'bg-gradient-to-br from-purple-900/30 via-indigo-900/20 to-purple-900/30 border border-purple-500/30' 
          : 'bg-gradient-to-br from-purple-50 via-indigo-50 to-purple-50 border border-purple-200/50'
      }`}
      style={{
        boxShadow: isDark
          ? '0 8px 32px rgba(139, 92, 246, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
          : '0 8px 32px rgba(139, 92, 246, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.8)'
      }}
    >
      {/* Main thinking stage */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Animated icon */}
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
            <div className={`p-2 rounded-xl ${
              isDark 
                ? 'bg-purple-500/20' 
                : 'bg-purple-100'
            }`}>
              <Icon className={`w-5 h-5 ${
                isDark ? 'text-purple-400' : 'text-purple-600'
              }`} />
            </div>
          </motion.div>

          {/* Stage info */}
          <div className="flex-1 min-w-0">
            <motion.h4
              key={currentStage.title}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`text-sm font-semibold mb-1 ${
                isDark ? 'text-purple-300' : 'text-purple-700'
              }`}
            >
              {currentStage.title}
            </motion.h4>
            <motion.p
              key={currentStage.description}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`text-xs mb-2 ${
                isDark ? 'text-purple-400/80' : 'text-purple-600/80'
              }`}
            >
              {currentStage.description}
            </motion.p>
            <motion.p
              key={currentStage.details}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={`text-xs italic ${
                isDark ? 'text-gray-400' : 'text-gray-600'
              }`}
            >
              {currentStage.details}
            </motion.p>
          </div>
        </div>
      </div>

      {/* Internal thoughts section */}
      {showInternalThoughts && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className={`border-t ${
            isDark 
              ? 'border-purple-500/20 bg-purple-900/10' 
              : 'border-purple-200/50 bg-purple-50/50'
          }`}
        >
          <div className="p-3">
            <div className="flex items-center gap-2 mb-2">
              <Brain className={`w-3.5 h-3.5 ${
                isDark ? 'text-purple-400' : 'text-purple-600'
              }`} />
              <span className={`text-xs font-medium ${
                isDark ? 'text-purple-300' : 'text-purple-700'
              }`}>
                Processus de réflexion interne
              </span>
            </div>
            
            <AnimatePresence mode="wait">
              <motion.div
                key={currentThoughtIndex}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className={`text-xs ${
                  isDark ? 'text-gray-300' : 'text-gray-700'
                }`}
              >
                <div className="flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">•</span>
                  <span className="italic">{internalThoughts[currentThoughtIndex]}</span>
                </div>
              </motion.div>
            </AnimatePresence>

            {/* Progress dots */}
            <div className="flex items-center gap-1 mt-2">
              {internalThoughts.map((_, index) => (
                <motion.div
                  key={index}
                  className={`w-1.5 h-1.5 rounded-full ${
                    index === currentThoughtIndex
                      ? isDark ? 'bg-purple-400' : 'bg-purple-600'
                      : isDark ? 'bg-purple-400/30' : 'bg-purple-400/40'
                  }`}
                  animate={{
                    scale: index === currentThoughtIndex ? [1, 1.2, 1] : 1,
                    opacity: index === currentThoughtIndex ? [0.6, 1, 0.6] : 0.3
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* User query analysis (if provided) */}
      {safeUserQuery && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className={`border-t ${
            isDark 
              ? 'border-purple-500/20 bg-indigo-900/10' 
              : 'border-purple-200/50 bg-indigo-50/50'
          }`}
        >
          <div className="p-3">
            <div className="flex items-center gap-2 mb-2">
              <MessageSquare className={`w-3.5 h-3.5 ${
                isDark ? 'text-indigo-400' : 'text-indigo-600'
              }`} />
              <span className={`text-xs font-medium ${
                isDark ? 'text-indigo-300' : 'text-indigo-700'
              }`}>
                Votre demande
              </span>
            </div>
            <p className={`text-xs ${
              isDark ? 'text-gray-300' : 'text-gray-700'
            }`}>
              "{safeUserQuery.length > 100 
                ? safeUserQuery.substring(0, 100) + '...' 
                : safeUserQuery}"
            </p>
          </div>
        </motion.div>
      )}

      {/* Progress indicator */}
      <div className={`h-1 ${
        isDark ? 'bg-purple-900/50' : 'bg-purple-100'
      }`}>
        <motion.div
          className={`h-full ${
            isDark ? 'bg-gradient-to-r from-purple-500 to-indigo-500' : 'bg-gradient-to-r from-purple-400 to-indigo-400'
          }`}
          initial={{ width: '0%' }}
          animate={{ 
            width: `${((safeStage + 1) / thinkingStages.length) * 100}%` 
          }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </motion.div>
  )
}

export default AdvancedThinkingIndicator

