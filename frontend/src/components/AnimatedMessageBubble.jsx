import { motion } from 'framer-motion'
import { useTheme } from '../contexts/ThemeContext'
import { Copy, RefreshCw, ThumbsUp, ThumbsDown, Download } from 'lucide-react'
import { useState } from 'react'
import ConfidenceIndicator from './ConfidenceIndicator'
import ModelIndicator from './ModelIndicator'

// MessageContent component for rendering content with download buttons
const MessageContent = ({ content, role }) => {
  // Ensure content is always a string
  const contentStr = typeof content === 'string' ? content : String(content || '')
  
  const handleDownload = (url) => {
    const token = localStorage.getItem('token')
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
    
    fetch(url, { headers })
      .then(response => {
        if (response.ok) {
          return response.blob()
        }
        throw new Error('Download failed')
      })
      .then(blob => {
        const downloadUrl = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = downloadUrl
        a.download = url.split('/').pop()
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(downloadUrl)
        document.body.removeChild(a)
      })
      .catch(error => {
        console.error('Download error:', error)
        alert('Erreur lors du téléchargement du document')
      })
  }

  // Parse content for download buttons and markdown
  const parts = []
  let lastIndex = 0
  const downloadButtonRegex = /DOWNLOAD_BUTTON:([^\n]+)/g
  let match

  while ((match = downloadButtonRegex.exec(contentStr)) !== null) {
    if (match.index > lastIndex) {
      const textBefore = contentStr.substring(lastIndex, match.index)
      if (textBefore.trim()) {
        parts.push({ type: 'text', content: textBefore })
      }
    }
    parts.push({ type: 'button', url: match[1] })
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < contentStr.length) {
    const remainingText = contentStr.substring(lastIndex)
    if (remainingText.trim()) {
      parts.push({ type: 'text', content: remainingText })
    }
  }
  
  // Clean up any unwanted line breaks in the middle of words in all text parts
  parts.forEach(part => {
    if (part.type === 'text' && part.content) {
      // Remove line breaks that are in the middle of words (fix "sa\nlut\ne" -> "salute")
      // Match any letter followed by newline followed by letter
      part.content = part.content.replace(/([a-zA-ZÀ-ÿ0-9])\s*\n+\s*([a-zA-ZÀ-ÿ0-9])/g, '$1$2')
      // Normalize multiple spaces to single space
      part.content = part.content.replace(/\s+/g, ' ').trim()
    }
  })

  if (parts.length === 0) {
    parts.push({ type: 'text', content: contentStr })
  }

  return (
    <div className="leading-relaxed break-words" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'break-word' }}>
      {parts.map((part, index) => {
        if (part.type === 'button') {
          return (
            <div key={index} className="mt-4">
              <button
                onClick={() => handleDownload(part.url)}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors duration-200 font-medium shadow-sm hover:shadow-md"
              >
                <Download className="w-4 h-4" />
                Télécharger le document amélioré
              </button>
            </div>
          )
        } else {
          // Ensure content is a string before calling replace
          let partContentStr = typeof part.content === 'string' ? part.content : String(part.content || '')
          // Remove unwanted line breaks in the middle of words (fix "sa\nlut\ne" -> "salute")
          partContentStr = partContentStr.replace(/([a-zA-ZÀ-ÿ0-9])\s*\n+\s*([a-zA-ZÀ-ÿ0-9])/g, '$1$2')
          // Normalize multiple spaces to single space
          partContentStr = partContentStr.replace(/\s+/g, ' ').trim()
          const text = partContentStr
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br />')
          return (
            <span
              key={index}
              dangerouslySetInnerHTML={{ __html: text }}
            />
          )
        }
      })}
    </div>
  )
}

// Animation variants for message bubbles
const bubbleVariants = {
  hidden: { 
    opacity: 0, 
    y: 20, 
    scale: 0.95 
  },
  visible: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: { 
      duration: 0.4, 
      ease: "easeOut" 
    }
  }
}

// Typing indicator dots
const dotVariants = {
  animate: {
    y: [0, -10, 0],
    transition: { 
      duration: 0.6, 
      repeat: Infinity,
      ease: "easeInOut",
      delay: 0
    }
  }
}

export const TypingIndicator = () => {
  const { isDark } = useTheme()
  
  return (
    <div className="flex items-center gap-1 px-4 py-2">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className={`w-2 h-2 rounded-full ${
            isDark ? 'bg-purple-500' : 'bg-indigo-500'
          }`}
          variants={dotVariants}
          animate="animate"
          style={{ 
            opacity: [0.4, 1, 0.4],
            transition: {
              duration: 0.6,
              repeat: Infinity,
              delay: i * 0.15,
              ease: "easeInOut"
            }
          }}
        />
      ))}
    </div>
  )
}

export const AnimatedMessageBubble = ({ 
  message, 
  role, 
  onCopy, 
  onRegenerate, 
  onFeedback,
  feedback 
}) => {
  const { isDark } = useTheme()
  const [showActions, setShowActions] = useState(false)
  const [copied, setCopied] = useState(false)
  
  const isUser = role === 'user'
  const isBot = role === 'assistant'
  
  const handleCopy = () => {
    if (onCopy) {
      onCopy()
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }
  
  return (
    <motion.div
      className="relative"
      variants={bubbleVariants}
      initial="hidden"
      animate="visible"
      onHoverStart={() => setShowActions(true)}
      onHoverEnd={() => setShowActions(false)}
      whileHover={{ 
        y: -2,
        transition: { duration: 0.2 }
      }}
    >
      <motion.div
        className={`relative rounded-2xl px-5 py-4 ${
          isUser 
            ? 'text-white' 
            : isDark 
              ? 'text-gray-100 bg-[#2D3748]' 
              : 'text-gray-900 bg-[#F1F5F9]'
        }`}
        style={{
          background: isUser 
            ? (isDark 
              ? 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)'
              : 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)')
            : undefined,
          boxShadow: isUser 
            ? `0 4px 12px ${isDark ? 'rgba(139, 92, 246, 0.3)' : 'rgba(99, 102, 241, 0.2)'}`
            : '0 2px 8px rgba(0, 0, 0, 0.1)',
          opacity: isBot ? 0.85 : 1  // Transparence pour les messages assistant
        }}
        animate={{
          filter: showActions ? 'brightness(1.05)' : 'brightness(1)',
          transition: { duration: 0.2 }
        }}
      >
        {/* Message content */}
        <div className="text-[15px] leading-relaxed break-words" style={{ wordBreak: 'break-word', overflowWrap: 'break-word', whiteSpace: 'pre-wrap' }}>
          <MessageContent 
            content={(() => {
              // Handle different message formats and ensure we always return a string
              if (typeof message === 'string') {
                return message
              }
              if (typeof message === 'object' && message !== null) {
                // Try to get content property first
                if (message.content !== undefined) {
                  const content = message.content
                  // If content is a string, return it
                  if (typeof content === 'string') {
                    return content
                  }
                  // If content is an object, try to extract text from it
                  if (typeof content === 'object' && content !== null) {
                    return content.text || content.content || JSON.stringify(content)
                  }
                  // Otherwise convert to string
                  return String(content || '')
                }
                // Fallback to text property
                if (message.text !== undefined) {
                  const text = message.text
                  return typeof text === 'string' ? text : String(text || '')
                }
                // Last resort: try to extract any string property or stringify
                console.warn('Message object without content/text property, attempting to extract:', message)
                // Try common property names
                const possibleContent = message.body || message.message || message.value
                if (possibleContent && typeof possibleContent === 'string') {
                  return possibleContent
                }
                // Don't stringify the entire object - return empty string instead
                return ''
              }
              return String(message || '')
            })()}
            role={role}
          />
        </div>
        
        {/* Model and Confidence Indicators for assistant messages */}
        {isBot && message && typeof message === 'object' && (
          <div className="mt-3 flex items-center gap-3 flex-wrap">
            {/* Model Indicator */}
            {message.metadata?.model && (
              <ModelIndicator 
                model={message.metadata.model}
                modelType={message.metadata.model_type || 'unknown'}
                enhancedBy={message.metadata.enhanced_by}
                enhancementType={message.metadata.enhancement_type}
                size="small"
              />
            )}
            {/* Confidence Indicator */}
            {message.metadata?.confidence && (
              <ConfidenceIndicator 
                confidence={message.metadata.confidence} 
                size="small"
                showLabel={true}
              />
            )}
          </div>
        )}
        
        {/* Timestamp */}
        {message && typeof message === 'object' && message.created_at && (
          <p className={`text-xs mt-2 ${
            isUser 
              ? 'text-white/70' 
              : isDark 
                ? 'text-gray-400' 
                : 'text-gray-500'
          }`}>
            {new Date(message.created_at).toLocaleTimeString('fr-FR', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </p>
        )}
        
        {/* Action buttons - fade in on hover */}
        {isBot && (
          <motion.div
            className="absolute -right-12 top-2 flex items-center gap-1"
            initial={{ opacity: 0, x: -10 }}
            animate={{ 
              opacity: showActions ? 1 : 0,
              x: showActions ? 0 : -10
            }}
            transition={{ duration: 0.2 }}
          >
            {onCopy && (
              <motion.button
                onClick={handleCopy}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 backdrop-blur-sm transition-colors"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                title={copied ? "Copié!" : "Copier"}
              >
                <Copy className={`w-4 h-4 ${copied ? 'text-green-400' : ''}`} />
              </motion.button>
            )}
            {onRegenerate && (
              <motion.button
                onClick={onRegenerate}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 backdrop-blur-sm transition-colors"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                title="Régénérer"
              >
                <RefreshCw className="w-4 h-4" />
              </motion.button>
            )}
            {onFeedback && (
              <div className="flex gap-1">
                <motion.button
                  onClick={() => onFeedback('like')}
                  className={`p-2 rounded-lg backdrop-blur-sm transition-colors ${
                    feedback === 'like' 
                      ? 'bg-green-500/30 text-green-400' 
                      : 'bg-white/10 hover:bg-white/20'
                  }`}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  title="J'aime"
                >
                  <ThumbsUp className="w-4 h-4" />
                </motion.button>
                <motion.button
                  onClick={() => onFeedback('dislike')}
                  className={`p-2 rounded-lg backdrop-blur-sm transition-colors ${
                    feedback === 'dislike' 
                      ? 'bg-red-500/30 text-red-400' 
                      : 'bg-white/10 hover:bg-white/20'
                  }`}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  title="Je n'aime pas"
                >
                  <ThumbsDown className="w-4 h-4" />
                </motion.button>
              </div>
            )}
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  )
}

