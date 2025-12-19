import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles, FileText, RefreshCw, BookOpen, Plus, Trash2, Upload, X, Paperclip, Download, Share2, FileDown, ThumbsUp, ThumbsDown, Wifi, WifiOff, ChevronDown, Zap, Brain, Languages, Settings, Power, Sparkles as SparklesIcon, Search, Shuffle, Lightbulb, Globe, Cpu, FileMinus, ListOrdered } from 'lucide-react'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { MessageSkeleton } from './SkeletonLoader'
import { useOffline } from '../hooks/useOffline'
import { EnhancedDragDrop } from './EnhancedDragDrop'
import ModernWelcomeAnimation from './ModernWelcomeAnimation'
import { AnimatedMessageBubble, TypingIndicator } from './AnimatedMessageBubble'
import ThinkingIndicator from './ThinkingIndicator'
import AdvancedThinkingIndicator from './AdvancedThinkingIndicator'
import { AIAvatar } from './AIAvatar'
import { AnimatedInput } from './AnimatedInput'
import { QuickReplyButtons } from './QuickReplyButtons'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'
import { saveToStorage, getFromStorage, removeFromStorage } from '../utils/storage'
import AnimatedRobot from './AnimatedRobot'
import MessageCorrection from './MessageCorrection'
import { useSuggestions } from '../hooks/useSuggestions'
import SuggestionDropdown from './SuggestionDropdown'

// Component to render message content with download buttons
const MessageContent = ({ content, role }) => {
  // Ensure content is always a string
  const safeContent = typeof content === 'string' 
    ? content 
    : content?.content || content?.text || String(content || '')
  
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

  while ((match = downloadButtonRegex.exec(safeContent)) !== null) {
    // Add text before the button
    if (match.index > lastIndex) {
      const textBefore = safeContent.substring(lastIndex, match.index)
      if (textBefore.trim()) {
        parts.push({ type: 'text', content: textBefore })
      }
    }
    
    // Add button
    parts.push({ type: 'button', url: match[1] })
    lastIndex = match.index + match[0].length
  }

  // Add remaining text
  if (lastIndex < safeContent.length) {
    const remainingText = safeContent.substring(lastIndex)
    if (remainingText.trim()) {
      parts.push({ type: 'text', content: remainingText })
    }
  }

  // If no buttons found, just render the text
  if (parts.length === 0) {
    parts.push({ type: 'text', content: safeContent })
  }

  return (
    <div className="whitespace-pre-wrap leading-relaxed">
      {parts.map((part, index) => {
        if (part.type === 'button') {
          return (
            <div key={index} className="mt-4">
              <button
                onClick={() => handleDownload(part.url)}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors duration-200 font-medium shadow-sm hover:shadow-md"
              >
                <Download className="w-4 h-4" />
                Télécharger le document amélioré
              </button>
            </div>
          )
        } else {
          // Simple markdown-like rendering for bold text
          const text = part.content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
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

const ChatInterface = ({ sessionId, onSessionUpdate }) => {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [moduleType, setModuleType] = useState('general')
  const [reformulationStyle, setReformulationStyle] = useState('academic') // academic, formal, simple, paraphrase, simplification
  const [planType, setPlanType] = useState('academic') // academic, argumentative, analytical, comparative
  const [planStructure, setPlanStructure] = useState('classic') // classic, thematic
  const [selectedModel, setSelectedModel] = useState(null) // Selected Ollama model
  const [availableModels, setAvailableModels] = useState([]) // Available Ollama models
  const [modelRecommendations, setModelRecommendations] = useState({}) // Model recommendations by mode
  const [showModelSelector, setShowModelSelector] = useState(false) // Show/hide model selector dropdown
  const [showOllamaInfoModal, setShowOllamaInfoModal] = useState(false) // Show/hide Ollama info modal
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [messageFeedbacks, setMessageFeedbacks] = useState({}) // { messageId: { rating: 1|-1, loading: false } }
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [thinkingStage, setThinkingStage] = useState(0) // Stage of thinking process
  const [isThinking, setIsThinking] = useState(false) // Whether AI is thinking (before content arrives)
  const [isDraggingFile, setIsDraggingFile] = useState(false)
  const [showWelcomeAnimation, setShowWelcomeAnimation] = useState(true)
  const [welcomeAnimationCompleted, setWelcomeAnimationCompleted] = useState(false)
  const [showAIDropdown, setShowAIDropdown] = useState(false)
  const [quickActionMode, setQuickActionMode] = useState('search') // 'search', 'shuffle', 'suggestions'
  const [showModeModal, setShowModeModal] = useState(false)
  const [cursorPosition, setCursorPosition] = useState(null)
  const [showSuggestions, setShowSuggestions] = useState(true)
  const [useWebSearch, setUseWebSearch] = useState(false) // Web search toggle
  const cpuButtonRef = useRef(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)
  const aiDropdownRef = useRef(null)
  const inputContainerRef = useRef(null)
  const abortControllerRef = useRef(null) // For canceling requests
  const streamReaderRef = useRef(null) // For canceling stream reading
  const { isOnline, queueStats } = useOffline()
  const { user } = useAuth()
  const previousSessionIdRef = useRef(sessionId)
  
  // AI-powered suggestions
  const { suggestions, loading: suggestionsLoading } = useSuggestions(
    input,
    cursorPosition,
    moduleType,
    showSuggestions && input.length >= 2
  )

  // Fetch available Ollama models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch('/api/ollama/status')
        if (response.ok) {
          const data = await response.json()
          console.log('Ollama status data:', data) // Debug log
          if (data.models && Array.isArray(data.models)) {
            setAvailableModels(data.models)
            setModelRecommendations(data.recommendations || {})
            // Set default model based on recommendations for current mode
            if (!selectedModel && data.recommendations && data.recommendations[moduleType]) {
              const recommended = data.recommendations[moduleType].fast || data.recommendations[moduleType].balanced
              const availableIds = data.models.map(m => m.id)
              if (recommended && availableIds.includes(recommended)) {
                setSelectedModel(recommended)
              } else if (availableIds.length > 0) {
                setSelectedModel(availableIds[0])
              }
            } else if (!selectedModel && data.models.length > 0) {
              setSelectedModel(data.models[0].id)
            }
          }
        } else {
          console.error('Failed to fetch models:', response.status, response.statusText)
        }
      } catch (error) {
        console.error('Error fetching models:', error)
      }
    }
    fetchModels()
  }, []) // Fetch once on mount

  // Update selected model when module type changes (use best recommended model)
  useEffect(() => {
    if (modelRecommendations[moduleType] && availableModels.length > 0) {
      const availableIds = availableModels.map(m => m.id)
      // Try to use the "best" model first, then fallback to balanced, then fast
      const recommended = modelRecommendations[moduleType].best || 
                          modelRecommendations[moduleType].balanced || 
                          modelRecommendations[moduleType].fast
      if (recommended && availableIds.includes(recommended)) {
        setSelectedModel(recommended)
      } else if (availableIds.length > 0 && !selectedModel) {
        setSelectedModel(availableIds[0])
      }
    }
  }, [moduleType, modelRecommendations, availableModels])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (aiDropdownRef.current && !aiDropdownRef.current.contains(event.target)) {
        setShowAIDropdown(false)
      }
    }

    if (showAIDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showAIDropdown])

  useEffect(() => {
    // Réinitialiser l'animation quand on change de session ou qu'on crée une nouvelle session
    if (sessionId !== previousSessionIdRef.current) {
      setShowWelcomeAnimation(true)
      setWelcomeAnimationCompleted(false)
      previousSessionIdRef.current = sessionId
    }
    
    if (sessionId) {
      loadMessages()
    } else {
      setMessages([])
      setShowWelcomeAnimation(true)
      setWelcomeAnimationCompleted(false)
    }
  }, [sessionId])

  // Réinitialiser l'animation quand on rafraîchit ou qu'il n'y a pas de messages
  useEffect(() => {
    if (messages.length === 0 && !loadingMessages) {
      // Always show welcome screen when no messages and not loading
      setShowWelcomeAnimation(true)
      setWelcomeAnimationCompleted(false)
    } else if (messages.length > 0) {
      setShowWelcomeAnimation(false)
      setWelcomeAnimationCompleted(true)
    }
  }, [messages.length, loadingMessages])

  // Masquer l'animation quand l'utilisateur commence à taper
  const handleInputChange = (value) => {
    setInput(value)
    if (value.length > 0 && showWelcomeAnimation) {
      setShowWelcomeAnimation(false)
      setWelcomeAnimationCompleted(true)
    }
  }

  const handleInputSelectionChange = (e) => {
    // Track cursor position for suggestions
    const textarea = e.target
    setCursorPosition(textarea.selectionStart)
  }

  const handleSuggestionSelect = (suggestion) => {
    if (!suggestion) {
      setShowSuggestions(false)
      setTimeout(() => setShowSuggestions(true), 100)
      return
    }

    if (suggestion.type === 'grammar' && suggestion.replacement) {
      // Replace word with corrected version
      const words = input.split(' ')
      if (words.length > 0) {
        words[words.length - 1] = suggestion.text
        setInput(words.join(' ') + ' ')
      }
    } else {
      // Append suggestion to input
      const words = input.split(' ')
      if (words.length > 0 && words[words.length - 1].toLowerCase() === suggestion.text.split(' ')[0].toLowerCase()) {
        // Replace last word with full suggestion
        words[words.length - 1] = suggestion.text
        setInput(words.join(' ') + ' ')
      } else {
        // Append suggestion
        setInput(input + (input.endsWith(' ') ? '' : ' ') + suggestion.text + ' ')
      }
    }
    
    // Hide suggestions temporarily
    setShowSuggestions(false)
    setTimeout(() => setShowSuggestions(true), 500)
  }

  const handleSendMessage = () => {
    sendMessage()
  }

  const handleInputFocus = () => {
    if (showWelcomeAnimation) {
      setShowWelcomeAnimation(false)
      setWelcomeAnimationCompleted(true)
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleFileSelect = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await handleFileUpload(e.target.files[0])
    }
  }

  const handleFileUpload = async (file) => {
    if (!sessionId) {
      alert('Veuillez créer une session de chat d\'abord')
      return
    }

    const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (!allowedTypes.includes(file.type)) {
      alert('Type de fichier non supporté. Utilisez PDF, TXT ou DOCX.')
      return
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      alert('Le fichier est trop volumineux. Taille maximale: 10MB')
      return
    }

    setUploading(true)
    setUploadedFile(file)

    // Add user message immediately
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: `📄 Document uploadé: ${file.name}`,
      module_type: 'general',
      created_at: new Date().toISOString()
    }
    const initialMessages = [...messages, userMessage]
    setMessages(initialMessages)
          if (sessionId) {
            saveToStorage(`messages_${sessionId}`, initialMessages)
          }

    // Poll for thinking messages during processing
    let pollInterval = null
    let pollCount = 0
    const maxPollAttempts = 300 // Stop after 5 minutes (300 * 1 second)
    
    pollInterval = setInterval(async () => {
      pollCount++
      if (pollCount > maxPollAttempts) {
        clearInterval(pollInterval)
        return
      }
      
      try {
        const token = localStorage.getItem('token')
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
        const response = await fetch(`/api/chat/sessions/${sessionId}`, { headers })
        if (response.ok) {
          const data = await response.json()
          const sessionMessages = data.messages || []
          // Update messages with latest from server (including thinking messages)
          setMessages(sessionMessages)
          if (sessionId) {
            saveToStorage(`messages_${sessionId}`, sessionMessages)
          }
        }
      } catch (error) {
        console.error('Error polling messages:', error)
      }
    }, 1000) // Poll every second

    const formData = new FormData()
    formData.append('file', file)

    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      
      const response = await fetch(`/api/chat/sessions/${sessionId}/documents`, {
        method: 'POST',
        headers,
        body: formData
      })

      // Stop polling
      if (pollInterval) {
        clearInterval(pollInterval)
      }

      if (response.ok) {
        const data = await response.json()
        
        // Reload messages to get final response (thinking messages should be removed)
        const token = localStorage.getItem('token')
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
        const sessionResponse = await fetch(`/api/chat/sessions/${sessionId}`, { headers })
        if (sessionResponse.ok) {
          const sessionData = await sessionResponse.json()
          setMessages(sessionData.messages || [])
          if (sessionId) {
            saveToStorage(`messages_${sessionId}`, sessionData.messages || [])
          }
        } else {
          // Fallback: construct message if session fetch fails
          let aiContent = ''
          if (data.message && data.message.includes('partiellement')) {
            aiContent = `⚠️ **Document partiellement traité**\n\n📄 **Fichier:** ${file.name}\n\nLe texte a été extrait mais le traitement complet a rencontré des difficultés.`
          } else {
            aiContent = `✅ **Document traité avec succès!**\n\n📄 **Fichier original:** ${file.name}\n📝 **Fichier amélioré:** ${data.processed_filename || 'document_amélioré'}\n\n**Résumé:**\n• ${data.corrections_count || 0} correction(s) grammaticale(s)\n• Texte reformulé dans un style académique\n• ${data.statistics?.paragraphs_processed || 0} paragraphe(s) traité(s)\n\n`
            
            if (data.download_path) {
              aiContent += `DOWNLOAD_BUTTON:${data.download_path}`
            }
          }
          
          const aiMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content: aiContent,
            module_type: 'general',
            created_at: new Date().toISOString()
          }

          const updatedMessages = [...initialMessages, aiMessage]
          setMessages(updatedMessages)
          if (sessionId) {
            saveToStorage(`messages_${sessionId}`, updatedMessages)
          }
        }
        
        onSessionUpdate()
        setUploadedFile(null)
      } else {
        let errorMessage = 'Impossible de traiter le document'
        try {
          const error = await response.json()
          errorMessage = error.detail || error.message || errorMessage
        } catch (e) {
          errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`
        }
        alert(`Erreur: ${errorMessage}`)
        setUploadedFile(null)
      }
    } catch (error) {
      if (pollInterval) {
        clearInterval(pollInterval)
      }
      console.error('Error uploading file:', error)
      alert('Erreur lors du traitement du document')
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const loadMessages = async () => {
    setLoadingMessages(true)
    
    // Set a timeout to ensure loadingMessages doesn't get stuck
    const loadingTimeout = setTimeout(() => {
      setLoadingMessages(false)
    }, 5000) // 5 second timeout
    
    try {
      if (!sessionId) {
        // Load from local storage for local sessions
        const parsedMessages = getFromStorage(`messages_${sessionId}`, null)
        if (parsedMessages) {
          setMessages(parsedMessages)
          // Load local feedbacks
          await loadFeedbacksForMessages(parsedMessages)
        } else {
          setMessages([])
        }
        clearTimeout(loadingTimeout)
        setLoadingMessages(false)
        return
      }
      
      // Check if it's a local session (timestamp ID)
      if (sessionId > 1000000000000) {
        const parsedMessages = getFromStorage(`messages_${sessionId}`, null)
        if (parsedMessages) {
          setMessages(parsedMessages)
          // Load local feedbacks
          await loadFeedbacksForMessages(parsedMessages)
        } else {
          setMessages([])
        }
        clearTimeout(loadingTimeout)
        setLoadingMessages(false)
        return
      }
      
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      const response = await fetch(`/api/chat/sessions/${sessionId}`, {
        headers
      })
      if (response.ok) {
        const data = await response.json()
        const sessionMessages = data.messages || []
        setMessages(sessionMessages)
        if (sessionId) {
            saveToStorage(`messages_${sessionId}`, sessionMessages)
        }
        // Load feedbacks for assistant messages
        await loadFeedbacksForMessages(sessionMessages)
      } else {
        // If session not found or error, clear messages
        setMessages([])
      }
    } catch (error) {
      console.error('Error loading messages:', error)
      // Try local storage as fallback
      const parsedMessages = getFromStorage(`messages_${sessionId}`, null)
      if (parsedMessages) {
        setMessages(parsedMessages)
        // Load local feedbacks
        await loadFeedbacksForMessages(parsedMessages)
      } else {
        setMessages([])
      }
    } finally {
      clearTimeout(loadingTimeout)
      setLoadingMessages(false)
    }
  }

  const loadFeedbacksForMessages = async (messages) => {
    const feedbacks = {}
    
    // Load local feedbacks first (for unauthenticated users or local sessions)
    if (sessionId) {
      try {
        const localFeedbacks = JSON.parse(localStorage.getItem(`feedbacks_${sessionId}`) || '{}')
        Object.keys(localFeedbacks).forEach(messageId => {
          const messageIdNum = parseInt(messageId)
          if (!isNaN(messageIdNum)) {
            feedbacks[messageIdNum] = { rating: localFeedbacks[messageId].rating, loading: false }
          }
        })
      } catch (error) {
        console.error('Error loading local feedbacks:', error)
      }
    }
    
    // Load feedbacks from backend if authenticated
    const token = localStorage.getItem('token')
    if (token) {
      const assistantMessages = messages.filter(m => m.role === 'assistant' && m.id)
      
      for (const message of assistantMessages) {
        // Skip if already loaded from local storage
        if (feedbacks[message.id]) continue
        
        try {
          const response = await fetch(`/api/feedback/message/${message.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (response.ok) {
            const feedback = await response.json()
            if (feedback) {
              feedbacks[message.id] = { rating: feedback.rating, loading: false }
            }
          }
        } catch (error) {
          console.error(`Error loading feedback for message ${message.id}:`, error)
        }
      }
    }
    
    setMessageFeedbacks(feedbacks)
  }

  const handleFeedback = async (messageId, rating) => {
    // Check if messageId is valid (must be a number from database)
    if (!messageId || typeof messageId !== 'number' || messageId < 1) {
      console.warn('Invalid message ID for feedback:', messageId)
      // For local sessions or messages without DB ID, store locally
      if (sessionId > 1000000000000 || !messageId) {
        const localFeedbacks = JSON.parse(localStorage.getItem(`feedbacks_${sessionId}`) || '{}')
        localFeedbacks[messageId] = { rating }
        localStorage.setItem(`feedbacks_${sessionId}`, JSON.stringify(localFeedbacks))
        setMessageFeedbacks(prev => ({ ...prev, [messageId]: { rating, loading: false } }))
        return
      }
      return
    }
    
    // Optimistic update: show feedback immediately
    setMessageFeedbacks(prev => ({
      ...prev,
      [messageId]: { rating, loading: true }
    }))
    
    // Check if it's a local session (timestamp ID > 1 trillion)
    if (sessionId > 1000000000000) {
      // Store feedback locally for local sessions
      const localFeedbacks = JSON.parse(localStorage.getItem(`feedbacks_${sessionId}`) || '{}')
      localFeedbacks[messageId] = { rating }
      localStorage.setItem(`feedbacks_${sessionId}`, JSON.stringify(localFeedbacks))
      setMessageFeedbacks(prev => ({ ...prev, [messageId]: { rating, loading: false } }))
      return
    }
    
    // Try to send feedback to backend
    const token = localStorage.getItem('token')
    const headers = { 'Content-Type': 'application/json' }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    try {
      const response = await fetch('/api/feedback/', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message_id: messageId,
          rating: rating,
          comment: null
        })
      })
      
      if (response.ok) {
        const feedback = await response.json()
        setMessageFeedbacks(prev => ({
          ...prev,
          [messageId]: { rating: feedback.rating, loading: false }
        }))
      } else {
        // If not authenticated, store locally as fallback
        if (response.status === 401) {
          const localFeedbacks = JSON.parse(localStorage.getItem(`feedbacks_${sessionId}`) || '{}')
          localFeedbacks[messageId] = { rating }
          localStorage.setItem(`feedbacks_${sessionId}`, JSON.stringify(localFeedbacks))
          setMessageFeedbacks(prev => ({ ...prev, [messageId]: { rating, loading: false } }))
          // Feedback stored locally (user not authenticated)
          console.log('Feedback stored locally (not authenticated)')
        } else {
          // Revert on other errors
          setMessageFeedbacks(prev => {
            const updated = { ...prev }
            if (updated[messageId]) {
              updated[messageId].loading = false
            }
            return updated
          })
          console.error('Error submitting feedback:', response.status, await response.text().catch(() => ''))
        }
      }
    } catch (error) {
      console.error('Error submitting feedback:', error)
      // Handle connection errors gracefully
      if (error.name === 'TypeError' || error.message?.includes('ECONNRESET') || error.message?.includes('Failed to fetch')) {
        console.warn('Connection error, storing feedback locally:', error.message)
      }
      // Store locally as fallback for any error
      const localFeedbacks = JSON.parse(localStorage.getItem(`feedbacks_${sessionId}`) || '{}')
      localFeedbacks[messageId] = { rating }
      localStorage.setItem(`feedbacks_${sessionId}`, JSON.stringify(localFeedbacks))
      setMessageFeedbacks(prev => ({ ...prev, [messageId]: { rating, loading: false } }))
    }
  }

  // Function to cancel current request
  const cancelRequest = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    if (streamReaderRef.current) {
      streamReaderRef.current.cancel().catch(() => {})
      streamReaderRef.current = null
    }
    setLoading(false)
    
    // Update the last assistant message to show it was cancelled
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      if (lastMessage.role === 'assistant' && lastMessage.content) {
        const updatedMessages = [...messages]
        updatedMessages[updatedMessages.length - 1] = {
          ...lastMessage,
          content: lastMessage.content + '\n\n*Génération interrompue par l\'utilisateur*'
        }
        setMessages(updatedMessages)
        if (sessionId) {
          localStorage.setItem(`messages_${sessionId}`, JSON.stringify(updatedMessages))
        }
      }
    }
  }

  const sendMessage = async (e) => {
    if (e && typeof e.preventDefault === 'function') {
      e.preventDefault()
    }
    if (!input.trim() || loading || !sessionId) return

    // Cancel any existing request
    cancelRequest()

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
      module_type: moduleType,
      created_at: new Date().toISOString()
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    
    // Save to local storage immediately
    if (sessionId) {
      saveToStorage(`messages_${sessionId}`, newMessages)
    }
    
    const inputValue = input // Store input value before clearing
    setInput('')
    setLoading(true)

    // Check if it's a local session (timestamp ID > 1 trillion)
    const isLocalSession = sessionId > 1000000000000

    // Create new AbortController for this request
    const abortController = new AbortController()
    abortControllerRef.current = abortController

    try {
      if (!isLocalSession) {
        // Use streaming endpoint
        const token = localStorage.getItem('token')
        const headers = { 'Content-Type': 'application/json' }
        if (token) {
          headers['Authorization'] = `Bearer ${token}`
        }
        
          const requestBody = {
            content: inputValue,
            module_type: moduleType,
            use_web_search: useWebSearch  // Pass web search toggle to backend
          }
          
          // Add style metadata for reformulation
          if (moduleType === 'reformulation') {
            requestBody.metadata = { style: reformulationStyle }
          }
          
          // Add plan type and structure metadata for plan mode
          if (moduleType === 'plan') {
            requestBody.metadata = { 
              plan_type: planType,
              structure: planStructure
            }
          }
          
          // Add selected model to metadata for all modes
          if (selectedModel) {
            if (!requestBody.metadata) {
              requestBody.metadata = {}
            }
            requestBody.metadata.model = selectedModel
          }
          
          // Add quick action mode to metadata
          if (quickActionMode && quickActionMode !== 'search') {
            if (!requestBody.metadata) {
              requestBody.metadata = {}
            }
            requestBody.metadata.quick_action = quickActionMode
          }
          
          const response = await fetch(`/api/chat/sessions/${sessionId}/messages/stream`, {
            method: 'POST',
            headers,
            body: JSON.stringify(requestBody),
            signal: abortController.signal
          })

        if (!response.ok) {
          // Fallback to non-streaming endpoint
          const fallbackResponse = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              content: input,
              module_type: moduleType
            })
          })
          
          if (fallbackResponse.ok) {
            const data = await fallbackResponse.json()
            const updatedMessages = [...newMessages, data]
            setMessages(updatedMessages)
            saveToStorage(`messages_${sessionId}`, updatedMessages)
            
            // Update session title if it's the first user message
            if (newMessages.length === 0 && sessionId) {
              const titleFromContent = inputValue.trim().replace(/[#*_`]/g, '').replace(/\s+/g, ' ').substring(0, 50)
              if (titleFromContent) {
                try {
                  const token = localStorage.getItem('token')
                  const headers = { 'Content-Type': 'application/json' }
                  if (token) {
                    headers['Authorization'] = `Bearer ${token}`
                  }
                  await fetch(`/api/chat/sessions/${sessionId}`, {
                    method: 'PUT',
                    headers,
                    body: JSON.stringify({ title: titleFromContent.length > 50 ? titleFromContent.substring(0, 47) + '...' : titleFromContent })
                  })
                } catch (e) {
                  console.error('Error updating session title:', e)
                }
              }
            }
            
            onSessionUpdate()
            setLoading(false)
          } else {
            setLoading(false)
            throw new Error('Failed to send message')
          }
        } else {
          // Create assistant message for streaming
          const assistantMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content: '',
            module_type: moduleType,
            created_at: new Date().toISOString(),
            isThinking: true, // Mark as thinking initially
            userQuery: inputValue // Store user query for thinking indicator
          }
          
          const messagesWithAssistant = [...newMessages, assistantMessage]
          setMessages(messagesWithAssistant)

          // Start thinking indicator
          setIsThinking(true)
          setThinkingStage(0)
          
          // Progress through thinking stages
          let thinkingInterval = setInterval(() => {
            setThinkingStage((prev) => {
              if (prev < 4) return prev + 1
              return prev
            })
          }, 1500)

          // Read the stream
          const reader = response.body.getReader()
          streamReaderRef.current = reader
          const decoder = new TextDecoder()
          let buffer = ''
          let accumulatedContent = ''
          let hasReceivedContent = false // Track if we've received any content

          try {
            while (true) {
              // Check if request was cancelled
              if (abortController.signal.aborted) {
                reader.cancel()
                break
              }
              
              const { done, value } = await reader.read()
              if (done) break
              
              // Check again after read
              if (abortController.signal.aborted) {
                break
              }

              buffer += decoder.decode(value, { stream: true })
              const lines = buffer.split('\n')
              buffer = lines.pop() || ''

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6))
                    
                    if (data.type === 'chunk' || data.type === 'done') {
                      // Stop thinking indicator when first content arrives
                      if (!hasReceivedContent) {
                        hasReceivedContent = true
                        setIsThinking(false)
                        setThinkingStage(0)
                        if (thinkingInterval) {
                          clearInterval(thinkingInterval)
                          thinkingInterval = null
                        }
                      }
                      
                      // Ensure we have a string, not an object
                      let newContent = ''
                      
                      // Helper function to safely extract string from value
                      const extractString = (value) => {
                        if (value === null || value === undefined) return ''
                        if (typeof value === 'string') return value
                        if (typeof value === 'object') {
                          // If it's an object, try to extract a string property
                          if (value.text) return typeof value.text === 'string' ? value.text : ''
                          if (value.content) return typeof value.content === 'string' ? value.content : ''
                          // Don't stringify the object - log and return empty
                          console.warn('Received object in stream data instead of string:', value)
                          return ''
                        }
                        return String(value)
                      }
                      
                      if (data.accumulated !== undefined && data.accumulated !== null) {
                        newContent = extractString(data.accumulated)
                      } else if (data.content !== undefined && data.content !== null) {
                        // Append content to accumulated
                        const contentChunk = extractString(data.content)
                        accumulatedContent += contentChunk
                        newContent = accumulatedContent
                      } else {
                        // If neither exists, keep current content
                        newContent = accumulatedContent
                      }
                      
                      // Only update if we have valid content
                      if (newContent !== undefined && newContent !== null) {
                        // Ensure accumulatedContent is always a string
                        accumulatedContent = typeof newContent === 'string' 
                          ? newContent 
                          : String(newContent || '')
                        
                        // Update the assistant message content - ensure it's always a string
                        const safeContent = typeof accumulatedContent === 'string' 
                          ? accumulatedContent 
                          : String(accumulatedContent || '')
                        
                        const updatedMessages = [...newMessages, {
                          ...assistantMessage,
                          content: safeContent,
                          isThinking: false // Remove thinking flag when content arrives
                        }]
                        setMessages(updatedMessages)
                        
                        // Save to local storage
                        if (sessionId) {
                          saveToStorage(`messages_${sessionId}`, updatedMessages)
                        }
                      }
                      // If done is true, stop loading immediately
                      if (data.done === true || data.type === 'done') {
                        setLoading(false)
                      }
                    } else if (data.type === 'message_id') {
                      // Update message ID when received
                      assistantMessage.id = data.message_id
                      // Ensure content is a string
                      const safeContent = typeof accumulatedContent === 'string' 
                        ? accumulatedContent 
                        : String(accumulatedContent || '')
                      // Update messages with the new ID and metadata
                      const updatedMessagesWithId = [...newMessages, {
                        ...assistantMessage,
                        id: data.message_id,
                        content: safeContent,
                        metadata: data.metadata || null
                      }]
                      setMessages(updatedMessagesWithId)
                      
                      // Save to local storage
                      if (sessionId) {
                        saveToStorage(`messages_${sessionId}`, updatedMessagesWithId)
                      }
                      
                      // If done is true in message_id event, stop loading
                      if (data.done === true) {
                        setLoading(false)
                      }
                    }
                  } catch (e) {
                    console.error('Error parsing SSE data:', e, 'Line:', line)
                  }
                }
              }
            }

            // Final update - ensure content is always a string
            const safeFinalContent = typeof accumulatedContent === 'string' 
              ? accumulatedContent 
              : (accumulatedContent?.content || accumulatedContent?.text || String(accumulatedContent || ''))
            
            // Clear thinking indicator
            setIsThinking(false)
            setThinkingStage(0)
            if (thinkingInterval) {
              clearInterval(thinkingInterval)
            }
            
            const finalMessages = [...newMessages, {
              ...assistantMessage,
              content: safeFinalContent,
              isThinking: false
            }]
            setMessages(finalMessages)
            saveToStorage(`messages_${sessionId}`, finalMessages)
            
            // Update session title if it's the first user message
            if (newMessages.length === 0 && sessionId) {
              const titleFromContent = inputValue.trim().replace(/[#*_`]/g, '').replace(/\s+/g, ' ').substring(0, 50)
              if (titleFromContent) {
                try {
                  const token = localStorage.getItem('token')
                  const headers = { 'Content-Type': 'application/json' }
                  if (token) {
                    headers['Authorization'] = `Bearer ${token}`
                  }
                  await fetch(`/api/chat/sessions/${sessionId}`, {
                    method: 'PUT',
                    headers,
                    body: JSON.stringify({ title: titleFromContent.length > 50 ? titleFromContent.substring(0, 47) + '...' : titleFromContent })
                  })
                } catch (e) {
                  console.error('Error updating session title:', e)
                }
              }
            }
            
            onSessionUpdate()
            
            // Always set loading to false when stream completes
            setLoading(false)
            setIsThinking(false)
            setThinkingStage(0)
            if (thinkingInterval) {
              clearInterval(thinkingInterval)
            }
            abortControllerRef.current = null
            streamReaderRef.current = null
          } catch (streamError) {
            // Check if error is due to cancellation
            if (streamError.name === 'AbortError' || abortController.signal.aborted) {
              console.log('Request cancelled by user')
              setLoading(false)
              setIsThinking(false)
              setThinkingStage(0)
              if (thinkingInterval) {
                clearInterval(thinkingInterval)
              }
              abortControllerRef.current = null
              streamReaderRef.current = null
              return
            }
            
            console.error('Streaming error:', streamError)
            // Fallback to non-streaming if streaming fails
            const fallbackBody = {
              content: inputValue,
              module_type: moduleType,
              use_web_search: useWebSearch  // Pass web search toggle to backend
            }
            
            // Add style metadata for reformulation
            if (moduleType === 'reformulation') {
              fallbackBody.metadata = { style: reformulationStyle }
            }
            
            const fallbackResponse = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
              method: 'POST',
              headers,
              body: JSON.stringify(fallbackBody)
            })
            
            if (fallbackResponse.ok) {
              const data = await fallbackResponse.json()
              const updatedMessages = [...newMessages, data]
              setMessages(updatedMessages)
              saveToStorage(`messages_${sessionId}`, updatedMessages)
              onSessionUpdate()
            }
            
            // Always set loading to false even on error
            setLoading(false)
            abortControllerRef.current = null
            streamReaderRef.current = null
          } finally {
            // Ensure loading is always set to false
            setLoading(false)
            abortControllerRef.current = null
            streamReaderRef.current = null
          }
        }
      } else {
        // For local sessions, call API without session ID requirement
        const abortController = new AbortController()
        abortControllerRef.current = abortController
        
        try {
          const token = localStorage.getItem('token')
          const headers = { 'Content-Type': 'application/json' }
          if (token) {
            headers['Authorization'] = `Bearer ${token}`
          }
          
          // Try to get a default session or create response directly
          const response = await fetch('/api/chat/sessions', {
            method: 'POST',
            headers,
            body: JSON.stringify({ title: `Conversation ${new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}` }),
            signal: abortController.signal
          })
          
          if (response.ok) {
            const newSession = await response.json()
            // Now send message to this session
            const msgBody = {
              content: inputValue,
              module_type: moduleType,
              use_web_search: useWebSearch  // Pass web search toggle to backend
            }
            
            // Add style metadata for reformulation
            if (moduleType === 'reformulation') {
              msgBody.metadata = { style: reformulationStyle }
            }
            
            // Add quick action mode to metadata
            if (quickActionMode && quickActionMode !== 'search') {
              if (!msgBody.metadata) {
                msgBody.metadata = {}
              }
              msgBody.metadata.quick_action = quickActionMode
            }
            
            const msgResponse = await fetch(`/api/chat/sessions/${newSession.id}/messages`, {
              method: 'POST',
              headers,
              body: JSON.stringify(msgBody)
            })
            
            if (msgResponse.ok) {
              const data = await msgResponse.json()
              const updatedMessages = [...newMessages, data]
              setMessages(updatedMessages)
              saveToStorage(`messages_${sessionId}`, updatedMessages)
              onSessionUpdate()
            } else {
              throw new Error('Failed to send message')
            }
          } else {
            throw new Error('Failed to create session')
          }
        } catch (apiError) {
          // Check if error is due to cancellation
          if (apiError.name === 'AbortError' || abortController.signal.aborted) {
            console.log('Request cancelled by user')
            setLoading(false)
            abortControllerRef.current = null
            return
          }
          
          console.error('API error:', apiError)
          // Don't show generic message, show error instead
          const errorResponse = {
            id: Date.now() + 1,
            role: 'assistant',
            content: 'Désolé, une erreur est survenue lors de la connexion au serveur. Veuillez réessayer.',
            module_type: moduleType,
            created_at: new Date().toISOString()
          }
          const updatedMessages = [...newMessages, errorResponse]
          setMessages(updatedMessages)
          localStorage.setItem(`messages_${sessionId}`, JSON.stringify(updatedMessages))
          setLoading(false)
          inputRef.current?.focus()
        } finally {
          setLoading(false)
          abortControllerRef.current = null
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorResponse = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Désolé, une erreur est survenue. Veuillez réessayer.',
        module_type: moduleType,
        created_at: new Date().toISOString()
      }
      const updatedMessages = [...newMessages, errorResponse]
      setMessages(updatedMessages)
      if (sessionId) {
        localStorage.setItem(`messages_${sessionId}`, JSON.stringify(updatedMessages))
      }
    } finally {
      if (!isLocalSession) {
        setLoading(false)
        inputRef.current?.focus()
      }
    }
  }

  const [shareLink, setShareLink] = useState(null)
  const [isSharing, setIsSharing] = useState(false)

  const exportToMarkdown = async () => {
    if (!sessionId || sessionId > 1000000000000) return
    
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      
      const response = await fetch(`/api/chat/sessions/${sessionId}/export/markdown`, { headers })
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `conversation_${sessionId}_${new Date().toISOString().split('T')[0]}.md`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Error exporting markdown:', error)
      alert('Erreur lors de l\'export en Markdown')
    }
  }

  const exportToPDF = async () => {
    if (!sessionId || sessionId > 1000000000000) return
    
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      
      const response = await fetch(`/api/chat/sessions/${sessionId}/export/pdf`, { headers })
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `conversation_${sessionId}_${new Date().toISOString().split('T')[0]}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Error exporting PDF:', error)
      alert('Erreur lors de l\'export en PDF')
    }
  }

  const shareSession = async () => {
    if (!sessionId || sessionId > 1000000000000) return
    
    setIsSharing(true)
    try {
      const token = localStorage.getItem('token')
      const headers = { 'Content-Type': 'application/json' }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      
      const response = await fetch(`/api/chat/sessions/${sessionId}/share`, {
        method: 'POST',
        headers
      })
      
      if (response.ok) {
        const data = await response.json()
        setShareLink(data.share_link)
        // Copier le lien dans le presse-papiers
        await navigator.clipboard.writeText(data.share_link)
        alert('Lien de partage copié dans le presse-papiers!')
        onSessionUpdate()
      }
    } catch (error) {
      console.error('Error sharing session:', error)
      alert('Erreur lors du partage de la session')
    } finally {
      setIsSharing(false)
    }
  }

  const unshareSession = async () => {
    if (!sessionId || sessionId > 1000000000000) return
    
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      
      const response = await fetch(`/api/chat/sessions/${sessionId}/share`, {
        method: 'DELETE',
        headers
      })
      
      if (response.ok) {
        setShareLink(null)
        onSessionUpdate()
      }
    } catch (error) {
      console.error('Error unsharing session:', error)
    }
  }

  const moduleTypes = [
    { value: 'general', label: 'Général', icon: Sparkles },
    { value: 'grammar', label: 'Grammaire', icon: BookOpen },
    { value: 'qa', label: 'Questions', icon: FileText },
    { value: 'reformulation', label: 'Reformulation', icon: RefreshCw },
    { value: 'summarization', label: 'Résumé', icon: FileMinus },
    { value: 'plan', label: 'Plan', icon: ListOrdered },
    { value: 'ollama', label: 'Ollama AI', icon: Cpu }
  ]

  // Note: LandingPage is now shown when sessionId is null, so this check is handled in App.jsx
  // But we still need to handle the case where sessionId might be null for safety
  if (!sessionId) {
    return null // LandingPage will be shown by App.jsx
  }

  // Gestionnaires de drag pour détecter quand un fichier est glissé au-dessus de la zone
  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.dataTransfer.types.includes('Files')) {
      setIsDraggingFile(true)
    }
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    // Ne masquer que si on quitte vraiment le conteneur (pas un enfant)
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setIsDraggingFile(false)
    }
  }

  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.dataTransfer.types.includes('Files')) {
      setIsDraggingFile(true)
    }
  }

  const { isDark } = useTheme()
  
  return (
    <div 
      className="flex flex-col h-full"
      style={{ 
        background: isDark ? 'linear-gradient(180deg, #0A0E17 0%, #050810 100%)' : '#F8FAFC',
        backgroundImage: isDark 
          ? 'radial-gradient(circle at 20% 30%, rgba(0, 217, 255, 0.15) 0%, transparent 50%), radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.15) 0%, transparent 50%)'
          : 'radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.03) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(59, 130, 246, 0.03) 0%, transparent 50%)'
      }}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      {/* Header with Dropdown - Seamless */}
      <div 
        className="px-6 py-4"
        style={{ 
          background: 'transparent',
          border: 'none',
          boxShadow: 'none'
        }}
      >
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div className="flex items-center gap-4">
            <div className="relative" ref={aiDropdownRef}>
              <motion.button 
                onClick={() => setShowAIDropdown(!showAIDropdown)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border transition-all ${
                  isDark 
                    ? 'border-white/10 text-white/80 hover:border-white/20 hover:text-white hover:bg-white/5' 
                    : 'border-gray-300/30 text-gray-700 hover:border-gray-400 hover:text-gray-900 hover:bg-gray-100/30'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse"></div>
                <span className="text-sm font-semibold text-white">AI Assistant</span>
                <ChevronDown className={`w-4 h-4 text-white/70 transition-transform ${showAIDropdown ? 'rotate-180' : ''}`} />
              </motion.button>
              
              {/* Dropdown Menu */}
              {showAIDropdown && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className={`absolute top-full left-0 mt-2 w-64 rounded-lg border backdrop-blur-md z-50 overflow-hidden ${
                    isDark 
                      ? 'border-white/10 bg-black/20' 
                      : 'border-gray-300/30 bg-white/20'
                  }`}
                  style={{
                    boxShadow: isDark ? '0 4px 20px rgba(0, 0, 0, 0.3)' : '0 4px 20px rgba(0, 0, 0, 0.1)'
                  }}
                >
                  <div className="p-2">
                    <div className="px-3 py-2 text-xs font-semibold text-white/60 uppercase tracking-wider mb-1">
                      Modules
                    </div>
                    {moduleTypes.map(({ value, label, icon: Icon }) => (
                      <button
                        key={value}
                        onClick={() => {
                          if (value === 'ollama') {
                            // Show info modal for Ollama AI mode
                            setShowOllamaInfoModal(true)
                            setShowAIDropdown(false)
                          } else {
                            setModuleType(value)
                            setShowAIDropdown(false)
                          }
                        }}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                          moduleType === value
                            ? 'bg-theme-accent-primary/20 text-white'
                            : 'text-white/70 hover:bg-white/5 hover:text-white'
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                        <span>{label}</span>
                        {moduleType === value && (
                          <div className="ml-auto w-2 h-2 rounded-full bg-[#10B981]"></div>
                        )}
                      </button>
                    ))}
                  </div>
                  
                  {/* Model Selector - Show for all modes */}
                  {availableModels.length > 0 && (
                    <div className="p-2 border-t border-white/10">
                      <div className="px-3 py-2 text-xs font-semibold text-white/60 uppercase tracking-wider mb-1">
                        Modèle Ollama
                      </div>
                      <div className="relative">
                        <button
                          onClick={() => setShowModelSelector(!showModelSelector)}
                          className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-white/70 hover:bg-white/5 hover:text-white transition-all border border-white/10"
                        >
                          <span className="flex items-center gap-2">
                            <Cpu className="w-4 h-4" />
                            <span className="truncate">
                              {availableModels.length > 0 
                                ? (selectedModel ? availableModels.find(m => m.id === selectedModel)?.name || selectedModel : 'Sélectionner un modèle')
                                : 'Chargement des modèles...'}
                            </span>
                          </span>
                          <ChevronDown className={`w-4 h-4 transition-transform ${showModelSelector ? 'rotate-180' : ''}`} />
                        </button>
                        
                        {showModelSelector && (
                          <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="absolute top-full left-0 right-0 mt-1 rounded-lg border border-white/10 bg-black/40 backdrop-blur-md z-50 max-h-64 overflow-y-auto"
                          >
                            {availableModels.length === 0 ? (
                              <div className="p-3 text-sm text-white/60 text-center">
                                Chargement des modèles...
                              </div>
                            ) : (
                              <>
                                {modelRecommendations[moduleType] && (
                                  <div className="p-2 border-b border-white/10">
                                    <div className="text-xs font-semibold text-white/60 mb-1">Recommandé:</div>
                                    <div className="text-xs text-white/50 space-y-1">
                                      <div>⚡ Rapide: {modelRecommendations[moduleType].fast}</div>
                                      <div>⚖️ Équilibré: {modelRecommendations[moduleType].balanced}</div>
                                      <div>🎯 Qualité: {modelRecommendations[moduleType].quality}</div>
                                    </div>
                                  </div>
                                )}
                                {availableModels.map((model) => {
                              const isRecommended = modelRecommendations[moduleType] && (
                                modelRecommendations[moduleType].fast === model.id ||
                                modelRecommendations[moduleType].balanced === model.id ||
                                modelRecommendations[moduleType].quality === model.id ||
                                modelRecommendations[moduleType].best === model.id
                              )
                              const isBest = modelRecommendations[moduleType] && modelRecommendations[moduleType].best === model.id
                              const isSelected = selectedModel === model.id
                              return (
                                <button
                                  key={model.id}
                                  onClick={() => {
                                    setSelectedModel(model.id)
                                    setShowModelSelector(false)
                                  }}
                                  className={`w-full text-left px-3 py-2 text-sm transition-all border-b border-white/5 last:border-b-0 ${
                                    isSelected
                                      ? 'bg-teal-500/20 text-teal-400'
                                      : 'text-white/70 hover:bg-white/5 hover:text-white'
                                  }`}
                                >
                                  <div className="flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2">
                                        <span className="font-medium truncate">{model.name}</span>
                                        {isBest && (
                                          <span className="text-xs px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-300 font-semibold">
                                            ⭐ Meilleur
                                          </span>
                                        )}
                                        {isRecommended && !isBest && (
                                          <span className="text-xs px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300">
                                            ⭐
                                          </span>
                                        )}
                                      </div>
                                      <div className="text-xs text-white/50 mt-0.5">
                                        {model.speed} • {model.quality} • {model.size}
                                      </div>
                                    </div>
                                    {isSelected && (
                                      <div className="w-2 h-2 rounded-full bg-[#10B981] ml-2"></div>
                                    )}
                                  </div>
                                </button>
                              )
                            })}
                              </>
                            )}
                          </motion.div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  <div className="border-t border-transparent"></div>
                  <div className="p-2">
                    <button
                      onClick={() => {
                        navigate('/about')
                        setShowAIDropdown(false)
                        // Set active section to settings in localStorage, then navigate
                        localStorage.setItem('accountActiveSection', 'settings')
                        navigate('/account')
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/70 hover:bg-white/5 hover:text-white transition-all"
                    >
                      <Settings className="w-4 h-4" />
                      <span>Paramètres</span>
                    </button>
                    <button
                      onClick={() => {
                        setShowAIDropdown(false)
                        navigate('/about')
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/70 hover:bg-white/5 hover:text-white transition-all"
                    >
                      <SparklesIcon className="w-4 h-4" />
                      <span>À propos</span>
                    </button>
                  </div>
                </motion.div>
              )}
            </div>
            
            {/* Ollama Info Modal */}
            <AnimatePresence>
              {showOllamaInfoModal && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
                  onClick={() => setShowOllamaInfoModal(false)}
                >
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    onClick={(e) => e.stopPropagation()}
                    className={`relative w-full max-w-2xl mx-4 rounded-2xl border ${
                      isDark 
                        ? 'bg-[#1A1F2E] border-white/10' 
                        : 'bg-white border-gray-200'
                    } shadow-2xl overflow-hidden`}
                  >
                    {/* Header */}
                    <div className={`p-6 border-b ${
                      isDark ? 'border-white/10' : 'border-gray-200'
                    }`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 via-blue-500 to-purple-600 flex items-center justify-center">
                            <Cpu className="w-5 h-5 text-white" />
                          </div>
                          <div>
                            <h3 className={`text-xl font-bold ${
                              isDark ? 'text-white' : 'text-gray-900'
                            }`}>
                              Ollama AI - Comment ça fonctionne
                            </h3>
                            <p className={`text-sm ${
                              isDark ? 'text-white/60' : 'text-gray-600'
                            }`}>
                              Découvrez comment Ollama améliore chaque mode
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => setShowOllamaInfoModal(false)}
                          className={`p-2 rounded-lg transition-colors ${
                            isDark 
                              ? 'hover:bg-white/10 text-white/70 hover:text-white' 
                              : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
                          }`}
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="p-6 max-h-[60vh] overflow-y-auto">
                      {/* Model Selection Section */}
                      {availableModels.length > 0 ? (
                        <div className="mb-6">
                          <h4 className={`text-sm font-semibold mb-3 ${
                            isDark ? 'text-white' : 'text-gray-900'
                          }`}>
                            Sélectionnez un modèle Ollama
                          </h4>
                          <div className="space-y-2 max-h-[300px] overflow-y-auto">
                            {availableModels.map((model) => {
                              const isRecommended = modelRecommendations['ollama'] && (
                                modelRecommendations['ollama'].fast === model.id ||
                                modelRecommendations['ollama'].balanced === model.id ||
                                modelRecommendations['ollama'].quality === model.id ||
                                modelRecommendations['ollama'].best === model.id
                              )
                              const isBest = modelRecommendations['ollama'] && modelRecommendations['ollama'].best === model.id
                              const isSelected = selectedModel === model.id
                              
                              return (
                                <button
                                  key={model.id}
                                  onClick={() => {
                                    setSelectedModel(model.id)
                                  }}
                                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                                    isSelected
                                      ? isDark
                                        ? 'bg-teal-500/20 border-teal-500/50 text-teal-300'
                                        : 'bg-teal-50 border-teal-300 text-teal-700'
                                      : isDark
                                        ? 'bg-white/5 border-white/10 text-white/70 hover:bg-white/10 hover:text-white'
                                        : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                                  }`}
                                >
                                  <div className="flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="font-medium truncate">{model.name}</span>
                                        {isBest && (
                                          <span className={`text-xs px-2 py-0.5 rounded ${
                                            isDark 
                                              ? 'bg-yellow-500/20 text-yellow-300' 
                                              : 'bg-yellow-100 text-yellow-700'
                                          } font-semibold`}>
                                            ⭐ Meilleur
                                          </span>
                                        )}
                                        {isRecommended && !isBest && (
                                          <span className={`text-xs px-2 py-0.5 rounded ${
                                            isDark 
                                              ? 'bg-purple-500/20 text-purple-300' 
                                              : 'bg-purple-100 text-purple-700'
                                          }`}>
                                            ⭐
                                          </span>
                                        )}
                                      </div>
                                      <div className={`text-xs ${
                                        isDark ? 'text-white/50' : 'text-gray-500'
                                      }`}>
                                        {model.speed} • {model.quality} • {model.size}
                                      </div>
                                    </div>
                                    {isSelected && (
                                      <div className="ml-3 w-5 h-5 rounded-full bg-teal-500 flex items-center justify-center flex-shrink-0">
                                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                        </svg>
                                      </div>
                                    )}
                                  </div>
                                </button>
                              )
                            })}
                          </div>
                          
                          {modelRecommendations['ollama'] && (
                            <div className={`mt-4 p-3 rounded-lg ${
                              isDark ? 'bg-white/5' : 'bg-gray-50'
                            }`}>
                              <div className={`text-xs font-semibold mb-2 ${
                                isDark ? 'text-white/60' : 'text-gray-600'
                              }`}>
                                Recommandations pour Ollama AI:
                              </div>
                              <div className={`text-xs space-y-1 ${
                                isDark ? 'text-white/50' : 'text-gray-600'
                              }`}>
                                <div>⭐ Meilleur: <span className="font-medium">{modelRecommendations['ollama'].best}</span></div>
                                <div>⚡ Rapide: {modelRecommendations['ollama'].fast}</div>
                                <div>⚖️ Équilibré: {modelRecommendations['ollama'].balanced}</div>
                                <div>🎯 Qualité: {modelRecommendations['ollama'].quality}</div>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className={`p-4 rounded-lg mb-6 ${
                          isDark ? 'bg-yellow-500/10 border border-yellow-500/20' : 'bg-yellow-50 border border-yellow-200'
                        }`}>
                          <p className={`text-sm ${
                            isDark ? 'text-yellow-300' : 'text-yellow-700'
                          }`}>
                            Aucun modèle Ollama disponible. Veuillez télécharger des modèles en utilisant le script de téléchargement.
                          </p>
                        </div>
                      )}
                      
                      <div className="space-y-4">
                        {/* Ollama AI Mode */}
                        <div className={`p-4 rounded-xl border ${
                          isDark 
                            ? 'bg-teal-500/10 border-teal-500/20' 
                            : 'bg-teal-50 border-teal-200'
                        }`}>
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-teal-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <Cpu className="w-4 h-4 text-teal-400" />
                            </div>
                            <div className="flex-1">
                              <h4 className={`font-semibold mb-1 ${
                                isDark ? 'text-teal-300' : 'text-teal-700'
                              }`}>
                                Mode Ollama AI
                              </h4>
                              <p className={`text-sm ${
                                isDark ? 'text-white/80' : 'text-gray-700'
                              }`}>
                                Utilise Ollama directement pour toutes les opérations. Ollama analyse votre demande et choisit automatiquement la meilleure approche (questions, grammaire, reformulation, ou conversation générale).
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Questions Mode */}
                        <div className={`p-4 rounded-xl border ${
                          isDark 
                            ? 'bg-blue-500/10 border-blue-500/20' 
                            : 'bg-blue-50 border-blue-200'
                        }`}>
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <FileText className="w-4 h-4 text-blue-400" />
                            </div>
                            <div className="flex-1">
                              <h4 className={`font-semibold mb-1 ${
                                isDark ? 'text-blue-300' : 'text-blue-700'
                              }`}>
                                Mode Questions-Réponses
                              </h4>
                              <p className={`text-sm ${
                                isDark ? 'text-white/80' : 'text-gray-700'
                              }`}>
                                Ollama améliore les réponses du modèle Camembert. Il vérifie l'exactitude, améliore la clarté et la précision, et rend les réponses plus académiques et structurées.
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Reformulation Mode */}
                        <div className={`p-4 rounded-xl border ${
                          isDark 
                            ? 'bg-purple-500/10 border-purple-500/20' 
                            : 'bg-purple-50 border-purple-200'
                        }`}>
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <RefreshCw className="w-4 h-4 text-purple-400" />
                            </div>
                            <div className="flex-1">
                              <h4 className={`font-semibold mb-1 ${
                                isDark ? 'text-purple-300' : 'text-purple-700'
                              }`}>
                                Mode Reformulation
                              </h4>
                              <p className={`text-sm ${
                                isDark ? 'text-white/80' : 'text-gray-700'
                              }`}>
                                Ollama améliore les reformulations du modèle T5. Il valide les changements, améliore la qualité du texte reformulé et s'assure que le sens original est préservé.
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Grammar Mode */}
                        <div className={`p-4 rounded-xl border ${
                          isDark 
                            ? 'bg-yellow-500/10 border-yellow-500/20' 
                            : 'bg-yellow-50 border-yellow-200'
                        }`}>
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-yellow-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <BookOpen className="w-4 h-4 text-yellow-400" />
                            </div>
                            <div className="flex-1">
                              <h4 className={`font-semibold mb-1 ${
                                isDark ? 'text-yellow-300' : 'text-yellow-700'
                              }`}>
                                Mode Grammaire
                              </h4>
                              <p className={`text-sm ${
                                isDark ? 'text-white/80' : 'text-gray-700'
                              }`}>
                                Ollama améliore les corrections de LanguageTool. Il valide les corrections, identifie des erreurs supplémentaires et améliore la qualité globale du texte corrigé.
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* General Mode */}
                        <div className={`p-4 rounded-xl border ${
                          isDark 
                            ? 'bg-gray-500/10 border-gray-500/20' 
                            : 'bg-gray-50 border-gray-200'
                        }`}>
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-gray-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <Sparkles className="w-4 h-4 text-gray-400" />
                            </div>
                            <div className="flex-1">
                              <h4 className={`font-semibold mb-1 ${
                                isDark ? 'text-gray-300' : 'text-gray-700'
                              }`}>
                                Mode Général
                              </h4>
                              <p className={`text-sm ${
                                isDark ? 'text-white/80' : 'text-gray-700'
                              }`}>
                                Si un modèle Ollama est sélectionné, Ollama peut être utilisé pour les conversations générales, offrant des réponses plus intelligentes et contextuelles.
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Summarization Mode */}
                        <div className={`p-4 rounded-xl border ${
                          isDark 
                            ? 'bg-indigo-500/10 border-indigo-500/20' 
                            : 'bg-indigo-50 border-indigo-200'
                        }`}>
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <FileMinus className="w-4 h-4 text-indigo-400" />
                            </div>
                            <div className="flex-1">
                              <h4 className={`font-semibold mb-1 ${
                                isDark ? 'text-indigo-300' : 'text-indigo-700'
                              }`}>
                                Mode Résumé
                              </h4>
                              <p className={`text-sm ${
                                isDark ? 'text-white/80' : 'text-gray-700'
                              }`}>
                                Ollama améliore les résumés du modèle T5. Il valide la complétude, améliore la précision et s'assure que tous les points importants sont inclus dans le résumé.
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        {/* Plan Mode */}
                        <div className={`p-4 rounded-xl border ${
                          isDark 
                            ? 'bg-amber-500/10 border-amber-500/20' 
                            : 'bg-amber-50 border-amber-200'
                        }`}>
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <ListOrdered className="w-4 h-4 text-amber-400" />
                            </div>
                            <div className="flex-1">
                              <h4 className={`font-semibold mb-1 ${
                                isDark ? 'text-amber-300' : 'text-amber-700'
                              }`}>
                                Mode Plan
                              </h4>
                              <p className={`text-sm ${
                                isDark ? 'text-white/80' : 'text-gray-700'
                              }`}>
                                Ollama génère des plans structurés pour vos essais académiques. Il crée des plans détaillés avec introduction, développement et conclusion, adaptés au type d'essai choisi.
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Footer */}
                    <div className={`p-6 border-t ${
                      isDark ? 'border-white/10' : 'border-gray-200'
                    } flex items-center justify-end gap-3`}>
                      <button
                        onClick={() => setShowOllamaInfoModal(false)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                          isDark 
                            ? 'bg-white/10 text-white/70 hover:bg-white/20 hover:text-white' 
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        Fermer
                      </button>
                      <button
                        onClick={() => {
                          setModuleType('ollama')
                          setShowOllamaInfoModal(false)
                        }}
                        className="px-4 py-2 rounded-lg text-sm font-medium bg-gradient-to-r from-teal-500 to-blue-500 text-white hover:from-teal-600 hover:to-blue-600 transition-all shadow-lg shadow-teal-500/20"
                      >
                        Utiliser Ollama AI
                      </button>
                    </div>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
            
            {/* Offline indicator */}
            {!isOnline && (
              <div className="flex items-center gap-2 px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                <WifiOff className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
                <span className="text-xs font-medium text-yellow-700 dark:text-yellow-300">
                  Hors-ligne
                  {queueStats.count > 0 && ` (${queueStats.count} en attente)`}
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Export buttons */}
            {sessionId && sessionId <= 1000000000000 && (
              <>
                <button
                  onClick={exportToMarkdown}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  title="Exporter en Markdown"
                >
                  <FileDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </button>
                <button
                  onClick={exportToPDF}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  title="Exporter en PDF"
                >
                  <FileText className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </button>
                {shareLink ? (
                  <button
                    onClick={unshareSession}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    title="Arrêter le partage"
                  >
                    <Share2 className="w-5 h-5 text-primary-600" />
                  </button>
                ) : (
                  <button
                    onClick={shareSession}
                    disabled={isSharing}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
                    title="Partager la session"
                  >
                    <Share2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </button>
                )}
              </>
            )}
            {/* Reformulation style selector */}
            {moduleType === 'reformulation' && (
              <div className="flex gap-2 ml-2">
                <select
                  value={reformulationStyle}
                  onChange={(e) => setReformulationStyle(e.target.value)}
                  className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="academic">Académique</option>
                  <option value="formal">Formel</option>
                  <option value="simple">Simple</option>
                  <option value="paraphrase">Paraphrase (Anti-plagiat)</option>
                  <option value="simplification">Simplification</option>
                </select>
              </div>
            )}
            {/* Plan type and structure selectors */}
            {moduleType === 'plan' && (
              <div className="flex gap-2 ml-2">
                <select
                  value={planType}
                  onChange={(e) => setPlanType(e.target.value)}
                  className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="academic">Académique</option>
                  <option value="argumentative">Argumentatif</option>
                  <option value="analytical">Analytique</option>
                  <option value="comparative">Comparatif</option>
                </select>
                <select
                  value={planStructure}
                  onChange={(e) => setPlanStructure(e.target.value)}
                  className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="classic">Classique</option>
                  <option value="thematic">Thématique</option>
                  <option value="chronological">Chronologique</option>
                  <option value="problem-solution">Problème-Solution</option>
                </select>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div 
        className="flex-1 overflow-y-auto relative"
        style={{ 
          background: isDark ? 'linear-gradient(180deg, #0A0E17 0%, #050810 100%)' : '#FFFFFF',
          backgroundImage: isDark 
            ? 'radial-gradient(circle at 20% 30%, rgba(0, 217, 255, 0.15) 0%, transparent 50%), radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.15) 0%, transparent 50%)'
            : 'radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.03) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(59, 130, 246, 0.03) 0%, transparent 50%)'
        }}
      >
        {/* Welcome Screen with Central Sphere */}
        {messages.length === 0 && !loadingMessages && !loading && (
          <div className="flex flex-col items-center justify-center h-full relative">
            {/* Central Animated Robot */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-0 pointer-events-none">
              <AnimatedRobot />
            </div>
            
            {/* Welcome Message */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.6 }}
              className="relative z-10 text-center mb-8"
            >
              <h2 className="text-3xl font-semibold text-theme-text-primary mb-2">
                {new Date().getHours() < 12 ? 'Good Morning' : new Date().getHours() < 18 ? 'Good Afternoon' : 'Good Evening'}, {user?.username || 'User'}.
              </h2>
              <p className="text-lg text-theme-text-secondary">
                Can I help you with anything?
              </p>
            </motion.div>
            
            {/* Action Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.6 }}
              className="relative z-10 flex gap-3 mb-12"
            >
              <motion.button 
                onClick={() => {
                  setModuleType('grammar')
                  inputRef.current?.focus()
                }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border transition-all ${
                  isDark 
                    ? 'border-white/10 text-white/80 hover:border-white/20 hover:text-white hover:bg-white/5' 
                    : 'border-gray-300/30 text-gray-700 hover:border-gray-400 hover:text-gray-900 hover:bg-gray-100/30'
                }`}
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
              >
                <BookOpen className="w-4 h-4" />
                <span className="text-sm font-medium">Correct Grammar</span>
              </motion.button>
              <motion.button 
                onClick={() => {
                  setModuleType('qa')
                  inputRef.current?.focus()
                }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border transition-all ${
                  isDark 
                    ? 'border-white/10 text-white/80 hover:border-white/20 hover:text-white hover:bg-white/5' 
                    : 'border-gray-300/30 text-gray-700 hover:border-gray-400 hover:text-gray-900 hover:bg-gray-100/30'
                }`}
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
              >
                <Brain className="w-4 h-4" />
                <span className="text-sm font-medium">Ask Question</span>
              </motion.button>
            </motion.div>
            
            {/* Feature Modules */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.6 }}
              className="relative z-10 grid grid-cols-3 gap-4 max-w-4xl w-full px-6"
            >
              <div className={`p-5 rounded-xl border transition-all ${
                isDark 
                  ? 'border-white/10 hover:border-white/20' 
                  : 'border-gray-300/30 hover:border-gray-400/50'
              }`}>
                <div className="flex items-center gap-3 mb-3">
                  <Zap className={`w-5 h-5 ${isDark ? 'text-yellow-400' : 'text-yellow-600'}`} />
                  <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Smart Grammar</h3>
                </div>
                <p className={`text-sm ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                  Advanced grammar correction that adapts to your writing style, not the other way around
                </p>
              </div>
              
              <div className={`p-5 rounded-xl border transition-all ${
                isDark 
                  ? 'border-white/10 hover:border-white/20' 
                  : 'border-gray-300/30 hover:border-gray-400/50'
              }`}>
                <div className="flex items-center gap-3 mb-3">
                  <Brain className={`w-5 h-5 ${isDark ? 'text-[#6366F1]' : 'text-purple-600'}`} />
                  <h3 className={`text-lg font-semibold ${isDark ? 'text-[#F3F4F6]' : 'text-gray-900'}`}>Analytics</h3>
                </div>
                <p className={`text-sm ${isDark ? 'text-[#9CA3AF]' : 'text-gray-600'}`}>
                  Analytics empowers individuals and businesses to make smarter decisions with AI insights
                </p>
              </div>
              
              <div className={`p-5 rounded-xl border transition-all ${
                isDark 
                  ? 'border-white/10 hover:border-white/20' 
                  : 'border-gray-300/30 hover:border-gray-400/50'
              }`}>
                <div className="flex items-center gap-3 mb-3">
                  <Languages className={`w-5 h-5 ${isDark ? 'text-[#3B82F6]' : 'text-blue-600'}`} />
                  <h3 className={`text-lg font-semibold ${isDark ? 'text-[#F3F4F6]' : 'text-gray-900'}`}>Reformulation</h3>
                </div>
                <p className={`text-sm ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                  Reformulation is the way individuals and businesses enhance their academic writing
                </p>
              </div>
            </motion.div>
          </div>
        )}
        
        <div className="max-w-4xl mx-auto px-4 py-4 relative z-0">
          <div className="space-y-1" data-message-area>
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ 
                    duration: 0.4, 
                    delay: index * 0.05,
                    ease: "easeOut"
                  }}
                  className={`flex items-start gap-3 mb-4 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 mt-1">
                      <AIAvatar 
                        state={(loading && index === messages.length - 1) || message.isThinking ? 'thinking' : 'idle'}
                        size={40}
                      />
                    </div>
                  )}
                  <div className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'} max-w-[85%] md:max-w-[75%]`}>
                    {/* Show advanced thinking indicator if message is thinking and has no content */}
                    {message.role === 'assistant' && message.isThinking && (!message.content || message.content.trim() === '') && (
                      <AdvancedThinkingIndicator 
                        stage={thinkingStage} 
                        userQuery={message.userQuery || (messages[index - 1]?.content || '')}
                      />
                    )}
                    {/* Show message content if it exists */}
                    {(!message.isThinking || (message.content && message.content.trim() !== '')) && (
                      <AnimatedMessageBubble
                        message={message}
                        role={message.role}
                      onCopy={() => {
                        const content = typeof message === 'string' ? message : (message.content || message.text || '')
                        navigator.clipboard.writeText(content)
                      }}
                      onRegenerate={() => {
                        // Regenerate logic - to be implemented
                      }}
                      onFeedback={(rating) => {
                        if (message.id) {
                          handleFeedback(message.id, rating === 'like' ? 1 : -1)
                        }
                      }}
                      feedback={
                        messageFeedbacks[message.id]?.rating === 1 
                          ? 'like' 
                          : messageFeedbacks[message.id]?.rating === -1 
                            ? 'dislike' 
                            : null
                      }
                      />
                    )}
                    {/* Correction component for assistant messages */}
                    {message.role === 'assistant' && message.id && typeof message.id === 'number' && (
                      <MessageCorrection
                        message={message}
                        onSave={(correctedMessage) => {
                          // Update the message in the messages array
                          setMessages(prev => prev.map(m => 
                            m.id === correctedMessage.id 
                              ? { ...m, content: correctedMessage.content, corrected: true }
                              : m
                          ))
                        }}
                      />
                    )}
                  </div>
                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center mt-1">
                      <span className="text-sm font-medium text-white">U</span>
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            {loadingMessages && messages.length === 0 && (
              <div className="flex items-center justify-center h-full min-h-[400px]">
                <div className="space-y-4 w-full max-w-4xl">
                  <MessageSkeleton />
                  <MessageSkeleton />
                  <MessageSkeleton />
                </div>
              </div>
            )}
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-3 justify-start"
              >
                <div className="flex-shrink-0 mt-1">
                  <AIAvatar state="thinking" size={40} />
                </div>
                <div className={`rounded-2xl px-4 py-3 ${
                  isDark 
                    ? 'bg-[#2D3748] border border-gray-700' 
                    : 'bg-[#F1F5F9] border border-gray-200'
                }`}>
                  <TypingIndicator />
                </div>
              </motion.div>
            )}
          </div>
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div 
        className="border-t"
        style={{ 
          background: 'transparent',
          borderColor: 'transparent',
        }}
      >
        <div className="max-w-2xl mx-auto px-4 py-3 flex flex-col items-center">
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.docx"
            onChange={handleFileSelect}
            className="hidden"
          />
          
          {/* File indicator */}
          {uploadedFile && !uploading && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs mb-2 ${
                isDark 
                  ? 'bg-purple-500/20 text-purple-300' 
                  : 'bg-purple-100 text-purple-700'
              }`}
            >
              <FileText className="w-3 h-3" />
              <span className="truncate max-w-[200px]">{uploadedFile.name}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setUploadedFile(null)
                }}
                className="ml-1 p-0.5 hover:opacity-70 rounded"
              >
                <X className="w-3 h-3" />
              </button>
            </motion.div>
          )}

          {/* Quick Action Buttons */}
          <div className="mb-3 flex items-center gap-2 justify-center" style={{ background: 'transparent' }}>
            <motion.button
              onClick={() => setQuickActionMode('search')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                quickActionMode === 'search'
                  ? isDark
                    ? 'bg-teal-500/20 border border-teal-500/50 text-teal-400'
                    : 'bg-teal-100 border border-teal-300 text-teal-700'
                  : isDark
                    ? 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10'
                    : 'bg-gray-100 border border-gray-200 text-gray-600 hover:bg-gray-200'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Search className="w-3.5 h-3.5" />
              <span>Search</span>
            </motion.button>
            
            <motion.button
              onClick={() => setQuickActionMode('shuffle')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                quickActionMode === 'shuffle'
                  ? isDark
                    ? 'bg-teal-500/20 border border-teal-500/50 text-teal-400'
                    : 'bg-teal-100 border border-teal-300 text-teal-700'
                  : isDark
                    ? 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10'
                    : 'bg-gray-100 border border-gray-200 text-gray-600 hover:bg-gray-200'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Shuffle className="w-3.5 h-3.5" />
              <span>Shuffle</span>
            </motion.button>
            
            <motion.button
              onClick={() => setQuickActionMode('suggestions')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                quickActionMode === 'suggestions'
                  ? isDark
                    ? 'bg-teal-500/20 border border-teal-500/50 text-teal-400'
                    : 'bg-teal-100 border border-teal-300 text-teal-700'
                  : isDark
                    ? 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10'
                    : 'bg-gray-100 border border-gray-200 text-gray-600 hover:bg-gray-200'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Lightbulb className="w-3.5 h-3.5" />
              <span>Suggestions</span>
            </motion.button>
          </div>
          
          <div className="relative w-full" ref={inputContainerRef}>
            {/* Suggestions Dropdown */}
            {showSuggestions && (suggestions.length > 0 || suggestionsLoading) && (
              <SuggestionDropdown
                suggestions={suggestions}
                loading={suggestionsLoading}
                onSelect={handleSuggestionSelect}
                visible={showSuggestions && input.length >= 2}
              />
            )}
            
            <AnimatedInput
              value={input}
              onChange={handleInputChange}
              onSubmit={handleSendMessage}
              placeholder={quickActionMode === 'search' ? "Ask a follow-up" : quickActionMode === 'suggestions' ? "Ask for suggestions" : "Ask anything."}
              disabled={uploading}
              loading={loading}
              maxLength={2000}
              onFileClick={() => fileInputRef.current?.click()}
              onMicClick={() => {
                // Voice recording functionality - to be implemented
                console.log('Voice recording clicked')
              }}
              onGlobeClick={() => {
                // Toggle web search
                setUseWebSearch(prev => !prev)
              }}
              webSearchActive={useWebSearch}
              onCpuClick={() => {
                setShowModeModal(true)
              }}
              onSelectionChange={handleInputSelectionChange}
              onCancel={cancelRequest}
            />
            
            {/* Mode Selection Dropdown */}
          {showModeModal && (
            <>
              {/* Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-40"
                onClick={() => setShowModeModal(false)}
              />
              
              {/* Dropdown Menu - positioned near the input */}
              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className={`absolute bottom-full right-0 mb-2 w-64 rounded-xl shadow-2xl z-50 ${
                  isDark 
                    ? 'bg-[#1F2937] border border-white/10' 
                    : 'bg-white border border-gray-200'
                }`}
                style={{
                  boxShadow: isDark 
                    ? '0 10px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05)' 
                    : '0 10px 40px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05)'
                }}
              >
                <div className="p-2">
                  {/* Mode Options */}
                  {moduleTypes.map((module) => {
                    const Icon = module.icon
                    const isSelected = moduleType === module.value
                    return (
                      <motion.button
                        key={module.value}
                        onClick={() => {
                          setModuleType(module.value)
                          setShowModeModal(false)
                        }}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                          isSelected
                            ? isDark
                              ? 'bg-teal-500/20 text-teal-400'
                              : 'bg-teal-50 text-teal-600'
                            : isDark
                              ? 'text-white/80 hover:bg-white/5 hover:text-white'
                              : 'text-gray-700 hover:bg-gray-50'
                        }`}
                        whileHover={{ x: 2 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <Icon className={`w-4 h-4 ${isSelected ? (isDark ? 'text-teal-400' : 'text-teal-600') : ''}`} />
                        <span className="flex-1 text-left">{module.label}</span>
                        {isSelected && (
                          <motion.svg
                            initial={{ scale: 0, pathLength: 0 }}
                            animate={{ scale: 1, pathLength: 1 }}
                            transition={{ duration: 0.2 }}
                            className={`w-4 h-4 ${isDark ? 'text-teal-400' : 'text-teal-600'}`}
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={3}
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M5 13l4 4L19 7"
                            />
                          </motion.svg>
                        )}
                      </motion.button>
                    )
                  })}
                </div>
              </motion.div>
            </>
          )}
          </div>
          
          {/* Drag & Drop Zone - visible seulement lors du drag */}
          {!uploadedFile && (
            <div className="mt-2">
              <EnhancedDragDrop
                onFileSelect={handleFileUpload}
                disabled={loading || uploading}
                className="mb-2"
                isDragging={isDraggingFile}
                onDragStateChange={setIsDraggingFile}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
