import { motion } from 'framer-motion'
import { TrendingUp, AlertCircle, CheckCircle, Info } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

const ConfidenceIndicator = ({ confidence, showLabel = true, size = 'default' }) => {
  const { isDark } = useTheme()

  if (confidence === null || confidence === undefined) {
    return null
  }

  // Normalize confidence to 0-1 range
  const normalizedConfidence = typeof confidence === 'number' 
    ? Math.max(0, Math.min(1, confidence))
    : 0

  const percentage = Math.round(normalizedConfidence * 100)

  // Determine confidence level and colors
  const getConfidenceLevel = (conf) => {
    if (conf >= 0.8) return { level: 'very_high', label: 'Très élevée', color: 'green' }
    if (conf >= 0.6) return { level: 'high', label: 'Élevée', color: 'blue' }
    if (conf >= 0.4) return { level: 'medium', label: 'Modérée', color: 'yellow' }
    if (conf >= 0.2) return { level: 'low', label: 'Faible', color: 'orange' }
    return { level: 'very_low', label: 'Très faible', color: 'red' }
  }

  const { level, label, color } = getConfidenceLevel(normalizedConfidence)

  const getColorClasses = (colorName) => {
    const colors = {
      green: {
        bg: isDark ? 'bg-green-500/20' : 'bg-green-100',
        text: isDark ? 'text-green-400' : 'text-green-700',
        border: isDark ? 'border-green-500/50' : 'border-green-300',
        progress: 'bg-green-500',
        icon: 'text-green-500'
      },
      blue: {
        bg: isDark ? 'bg-blue-500/20' : 'bg-blue-100',
        text: isDark ? 'text-blue-400' : 'text-blue-700',
        border: isDark ? 'border-blue-500/50' : 'border-blue-300',
        progress: 'bg-blue-500',
        icon: 'text-blue-500'
      },
      yellow: {
        bg: isDark ? 'bg-yellow-500/20' : 'bg-yellow-100',
        text: isDark ? 'text-yellow-400' : 'text-yellow-700',
        border: isDark ? 'border-yellow-500/50' : 'border-yellow-300',
        progress: 'bg-yellow-500',
        icon: 'text-yellow-500'
      },
      orange: {
        bg: isDark ? 'bg-orange-500/20' : 'bg-orange-100',
        text: isDark ? 'text-orange-400' : 'text-orange-700',
        border: isDark ? 'border-orange-500/50' : 'border-orange-300',
        progress: 'bg-orange-500',
        icon: 'text-orange-500'
      },
      red: {
        bg: isDark ? 'bg-red-500/20' : 'bg-red-100',
        text: isDark ? 'text-red-400' : 'text-red-700',
        border: isDark ? 'border-red-500/50' : 'border-red-300',
        progress: 'bg-red-500',
        icon: 'text-red-500'
      }
    }
    return colors[colorName] || colors.blue
  }

  const colors = getColorClasses(color)

  const getIcon = () => {
    if (normalizedConfidence >= 0.7) return <CheckCircle className="w-4 h-4" />
    if (normalizedConfidence >= 0.4) return <Info className="w-4 h-4" />
    return <AlertCircle className="w-4 h-4" />
  }

  const sizeClasses = {
    small: 'text-xs px-2 py-1',
    default: 'text-sm px-3 py-1.5',
    large: 'text-base px-4 py-2'
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`
        inline-flex items-center gap-2 rounded-lg border
        ${colors.bg} ${colors.border} ${colors.text}
        ${sizeClasses[size]}
      `}
      title={`Confiance: ${label} (${percentage}%)`}
    >
      {/* Icon */}
      <div className={colors.icon}>
        {getIcon()}
      </div>

      {/* Progress Bar */}
      <div className="flex items-center gap-2 flex-1 min-w-[80px]">
        <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className={`h-full ${colors.progress} rounded-full`}
          />
        </div>
        <span className="font-semibold text-xs tabular-nums min-w-[35px] text-right">
          {percentage}%
        </span>
      </div>

      {/* Label */}
      {showLabel && (
        <span className="text-xs font-medium hidden sm:inline">
          {label}
        </span>
      )}
    </motion.div>
  )
}

// Compact version for inline display
export const CompactConfidenceIndicator = ({ confidence }) => {
  const { isDark } = useTheme()

  if (confidence === null || confidence === undefined) {
    return null
  }

  const normalizedConfidence = typeof confidence === 'number' 
    ? Math.max(0, Math.min(1, confidence))
    : 0

  const percentage = Math.round(normalizedConfidence * 100)

  const getColor = (conf) => {
    if (conf >= 0.8) return isDark ? 'text-green-400' : 'text-green-600'
    if (conf >= 0.6) return isDark ? 'text-blue-400' : 'text-blue-600'
    if (conf >= 0.4) return isDark ? 'text-yellow-400' : 'text-yellow-600'
    if (conf >= 0.2) return isDark ? 'text-orange-400' : 'text-orange-600'
    return isDark ? 'text-red-400' : 'text-red-600'
  }

  const getBgColor = (conf) => {
    if (conf >= 0.8) return isDark ? 'bg-green-500/20' : 'bg-green-100'
    if (conf >= 0.6) return isDark ? 'bg-blue-500/20' : 'bg-blue-100'
    if (conf >= 0.4) return isDark ? 'bg-yellow-500/20' : 'bg-yellow-100'
    if (conf >= 0.2) return isDark ? 'bg-orange-500/20' : 'bg-orange-100'
    return isDark ? 'bg-red-500/20' : 'bg-red-100'
  }

  return (
    <span
      className={`
        inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium
        ${getColor(normalizedConfidence)} ${getBgColor(normalizedConfidence)}
      `}
      title={`Confiance: ${percentage}%`}
    >
      <TrendingUp className="w-3 h-3" />
      {percentage}%
    </span>
  )
}

export default ConfidenceIndicator

