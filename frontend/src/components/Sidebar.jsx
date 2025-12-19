import { useState, useEffect, useRef, useMemo } from 'react'
import { motion } from 'framer-motion'
import { MessageSquare, Plus, FileText, Moon, Sun, Trash2, User, LogOut, LogIn, UserPlus, Search, X, Filter, Calendar, BarChart3, Home, BookOpen, Brain, Languages, Hash, ChevronLeft, ChevronRight, Menu, Sparkles, Shield } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate, useLocation } from 'react-router-dom'
import { format, isToday, isYesterday, differenceInDays, startOfDay } from 'date-fns'
import { fr } from 'date-fns/locale'

const Sidebar = ({ sessions, currentSession, onSelectSession, onCreateSession, onSessionsUpdate, onNavigateToLanding, isOpen = true, onToggle }) => {
  const { isDark, toggleTheme } = useTheme()
  const { user, logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [activeTab, setActiveTab] = useState(() => {
    if (location.pathname === '/dashboard') return 'dashboard'
    if (location.pathname === '/documents') return 'documents'
    if (location.pathname === '/account') return 'account'
    if (location.pathname === '/learning') return 'learning'
    if (location.pathname === '/plagiarism') return 'plagiarism'
    return 'chats'
  })
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [filters, setFilters] = useState({
    module_type: '',
    date_from: '',
    date_to: '',
    role: ''
  })
  const [showFilters, setShowFilters] = useState(false)
  const searchTimeoutRef = useRef(null)

  // Group sessions by date
  const groupedSessions = useMemo(() => {
    if (!sessions || sessions.length === 0) return {}
    
    const groups = {}
    const now = new Date()
    
    sessions.forEach(session => {
      const sessionDate = new Date(session.updated_at || session.created_at)
      const daysDiff = differenceInDays(now, startOfDay(sessionDate))
      
      let groupKey
      if (isToday(sessionDate)) {
        groupKey = 'Today'
      } else if (isYesterday(sessionDate)) {
        groupKey = 'Yesterday'
      } else if (daysDiff <= 7) {
        groupKey = `${daysDiff} days ago`
      } else if (daysDiff <= 30) {
        const weeks = Math.floor(daysDiff / 7)
        groupKey = `${weeks} week${weeks > 1 ? 's' : ''} ago`
      } else {
        const months = Math.floor(daysDiff / 30)
        groupKey = `${months} month${months > 1 ? 's' : ''} ago`
      }
      
      if (!groups[groupKey]) {
        groups[groupKey] = []
      }
      groups[groupKey].push(session)
    })
    
    // Sort sessions within each group by date (newest first)
    Object.keys(groups).forEach(key => {
      groups[key].sort((a, b) => {
        const dateA = new Date(a.updated_at || a.created_at)
        const dateB = new Date(b.updated_at || b.created_at)
        return dateB - dateA
      })
    })
    
    return groups
  }, [sessions])

  const [deletingSessionId, setDeletingSessionId] = useState(null)

  const deleteSession = async (sessionId, e) => {
    e.stopPropagation()
    e.preventDefault()
    
    // Add animation state
    setDeletingSessionId(sessionId)
    
    // Wait a bit for animation
    await new Promise(resolve => setTimeout(resolve, 300))
    
    const wasCurrentSession = currentSession === sessionId
    
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      const response = await fetch(`/api/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers
      })
      if (response.ok) {
        // Get remaining sessions (excluding the deleted one)
        const remainingSessions = sessions.filter(s => s.id !== sessionId)
        
        // If we deleted the current session, select another one or navigate to landing
        if (wasCurrentSession) {
          if (remainingSessions.length > 0) {
            // Select the first remaining session
            onSelectSession(remainingSessions[0].id)
          } else {
            // No more sessions - navigate to landing page
            if (onNavigateToLanding) {
              onNavigateToLanding()
            }
          }
        }
        
        // Update sessions list
        onSessionsUpdate()
      }
    } catch (error) {
      console.error('Error deleting session:', error)
    } finally {
      setDeletingSessionId(null)
    }
  }

  const performSearch = async () => {
    if (!searchQuery.trim() && !filters.module_type && !filters.date_from && !filters.date_to && !filters.role) {
      setSearchResults([])
      setShowSearch(false)
      return
    }

    setIsSearching(true)
    try {
      const token = localStorage.getItem('token')
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      }

      const searchRequest = {
        query: searchQuery.trim() || null,
        module_type: filters.module_type || null,
        date_from: filters.date_from || null,
        date_to: filters.date_to || null,
        role: filters.role || null,
        limit: 50,
        offset: 0
      }

      const response = await fetch('/api/chat/search/messages', {
        method: 'POST',
        headers,
        body: JSON.stringify(searchRequest)
      })

      if (response.ok) {
        const data = await response.json()
        setSearchResults(data.results || [])
        setShowSearch(true)
      }
    } catch (error) {
      console.error('Error searching:', error)
    } finally {
      setIsSearching(false)
    }
  }

  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    const hasSearchCriteria = searchQuery.trim() || filters.module_type || filters.date_from || filters.date_to || filters.role

    if (hasSearchCriteria) {
      searchTimeoutRef.current = setTimeout(() => {
        performSearch()
      }, 500)
    } else {
      setSearchResults([])
      setShowSearch(false)
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, filters.module_type, filters.date_from, filters.date_to, filters.role])

  const clearSearch = () => {
    setSearchQuery('')
    setFilters({
      module_type: '',
      date_from: '',
      date_to: '',
      role: ''
    })
    setSearchResults([])
    setShowSearch(false)
  }

  const handleSearchResultClick = (result) => {
    onSelectSession(result.session_id)
    clearSearch()
  }

  const navigationItems = [
    { id: 'home', label: 'Home', icon: Home, action: 'landing' },
    { id: 'grammar', label: 'Grammar', icon: BookOpen, action: 'module', module: 'grammar' },
    { id: 'qa', label: 'Q&A', icon: Brain, action: 'module', module: 'qa' },
    { id: 'reformulation', label: 'Reformulation', icon: Languages, action: 'module', module: 'reformulation' },
  ]

  return (
    <>
      {/* Toggle Button - Always visible */}
      <motion.button
        onClick={onToggle}
        className={`fixed z-50 p-2.5 backdrop-blur-md rounded-xl shadow-lg transition-all ${isDark ? 'border border-white/10' : 'border border-gray-300/50'}`}
        style={{
          backgroundColor: 'transparent',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)'
        }}
        initial={{ opacity: 0, x: -20 }}
        animate={{ 
          opacity: 1, 
          x: 0,
          left: isOpen ? 296 : 16,
          top: 16
        }}
        transition={{ duration: 0.3 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {isOpen ? (
          <ChevronLeft className={`w-5 h-5 ${isDark ? 'text-white/90' : 'text-gray-800'}`} />
        ) : (
          <Menu className={`w-5 h-5 ${isDark ? 'text-white/90' : 'text-gray-800'}`} />
        )}
      </motion.button>

      {/* Floating Sidebar with Glow */}
      <motion.div
        className="fixed left-2 top-4 bottom-4 z-40 flex flex-col overflow-hidden rounded-3xl"
        style={{
          width: isOpen ? '280px' : '0px',
          backgroundColor: isDark ? '#1A1F2E' : '#FFFFFF',
          background: isDark ? '#1A1F2E' : '#FFFFFF',
          backdropFilter: 'none',
          WebkitBackdropFilter: 'none',
          boxShadow: isDark && isOpen 
            ? '0 0 40px rgba(0, 217, 255, 0.2), 0 0 80px rgba(99, 102, 241, 0.15), 0 10px 40px rgba(0, 0, 0, 0.5)' 
            : isOpen
            ? '0 10px 40px rgba(0, 0, 0, 0.1)'
            : 'none',
          border: isDark && isOpen ? '1px solid rgba(0, 217, 255, 0.2)' : 'none'
        }}
        initial={false}
        animate={{
          width: isOpen ? 280 : 0,
          opacity: isOpen ? 1 : 0,
          x: 0
        }}
        transition={{
          duration: 0.3,
          ease: "easeInOut"
        }}
      >
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="flex flex-col h-full rounded-3xl"
            style={{
              backgroundColor: isDark ? '#1A1F2E' : '#FFFFFF',
              background: isDark ? '#1A1F2E' : '#FFFFFF'
            }}
          >
            {/* Logo Header */}
            <div className="p-4">
              <div className="flex items-center justify-between mb-6">
                <motion.div 
                  className="flex items-center gap-2 cursor-pointer"
                  onClick={() => onNavigateToLanding && onNavigateToLanding()}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-500 via-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/50">
                    <span className="text-white font-bold text-lg">A</span>
                  </div>
                  <h1 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    Academic AI
                  </h1>
                </motion.div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={onToggle}
                    className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10' : 'hover:bg-gray-200/50'}`}
                  >
                    <ChevronLeft className={`w-4 h-4 ${isDark ? 'text-white/70' : 'text-gray-700'}`} />
                  </button>
                  <button
                    onClick={toggleTheme}
                    className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10' : 'hover:bg-gray-200/50'}`}
                  >
                    {isDark ? (
                      <Sun className={`w-4 h-4 ${isDark ? 'text-white/70' : 'text-gray-700'}`} />
                    ) : (
                      <Moon className={`w-4 h-4 ${isDark ? 'text-white/70' : 'text-gray-700'}`} />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Search Bar */}
            <div className="p-3">
              <div className="relative">
                <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${isDark ? 'text-white/60' : 'text-gray-600'}`} />
                <input
                  type="text"
                  placeholder="Search chats"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`w-full pl-10 pr-10 py-2.5 text-sm rounded-xl focus:outline-none focus:ring-0 focus:border-transparent transition-all ${
                    isDark 
                      ? 'border-0 bg-transparent text-white placeholder-white/40' 
                      : 'border-0 bg-transparent text-gray-900 placeholder-gray-500'
                  }`}
                />
                <Hash className={`absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${isDark ? 'text-white/60' : 'text-gray-600'}`} />
              </div>
            </div>

            {/* Navigation */}
            <div className="px-3 py-2">
              {navigationItems.map((item) => (
                <motion.button
                  key={item.id}
                  onClick={() => {
                    if (item.action === 'landing' && onNavigateToLanding) {
                      onNavigateToLanding()
                    } else if (item.action === 'module' && item.module) {
                      // Create a new session with the selected module
                      onCreateSession && onCreateSession(item.module)
                    }
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors mb-1 ${
                    isDark 
                      ? 'text-white/80 hover:text-white hover:bg-white/5' 
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100/30'
                  }`}
                  whileHover={{ x: 2, scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <item.icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{item.label}</span>
                </motion.button>
              ))}
            </div>

            {/* Tabs */}
            <div className="flex px-3 py-2">
              <button
                onClick={() => {
                  setActiveTab('chats')
                  clearSearch()
                  navigate('/')
                }}
                className={`flex-1 px-3 py-2.5 text-xs font-medium transition-colors rounded-lg ${
                  activeTab === 'chats'
                    ? isDark
                      ? 'text-white bg-white/5'
                      : 'text-gray-900 bg-gray-100/50'
                    : isDark
                      ? 'text-white/60 hover:text-white hover:bg-white/5'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/30'
                }`}
              >
                <MessageSquare className="w-4 h-4 inline mr-1" />
                Chats
              </button>
              <button
                onClick={() => {
                  setActiveTab('dashboard')
                  clearSearch()
                  navigate('/dashboard')
                }}
                className={`flex-1 px-3 py-2.5 text-xs font-medium transition-colors rounded-lg ${
                  activeTab === 'dashboard'
                    ? isDark
                      ? 'text-white bg-white/5'
                      : 'text-gray-900 bg-gray-100/50'
                    : isDark
                      ? 'text-white/60 hover:text-white hover:bg-white/5'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/30'
                }`}
              >
                <BarChart3 className="w-4 h-4 inline mr-1" />
                Stats
              </button>
              <button
                onClick={() => {
                  setActiveTab('learning')
                  clearSearch()
                  navigate('/learning')
                }}
                className={`flex-1 px-3 py-2.5 text-xs font-medium transition-colors rounded-lg ${
                  activeTab === 'learning'
                    ? isDark
                      ? 'text-white bg-white/5'
                      : 'text-gray-900 bg-gray-100/50'
                    : isDark
                      ? 'text-white/60 hover:text-white hover:bg-white/5'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/30'
                }`}
              >
                <Sparkles className="w-4 h-4 inline mr-1" />
                Learning
              </button>
              <button
                onClick={() => {
                  setActiveTab('plagiarism')
                  clearSearch()
                  navigate('/plagiarism')
                }}
                className={`flex-1 px-3 py-2.5 text-xs font-medium transition-colors rounded-lg ${
                  activeTab === 'plagiarism'
                    ? isDark
                      ? 'text-white bg-white/5'
                      : 'text-gray-900 bg-gray-100/50'
                    : isDark
                      ? 'text-white/60 hover:text-white hover:bg-white/5'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/30'
                }`}
              >
                <Shield className="w-4 h-4 inline mr-1" />
                Plagiarism
              </button>
              <button
                onClick={() => {
                  setActiveTab('documents')
                  clearSearch()
                  navigate('/documents')
                }}
                className={`flex-1 px-3 py-2.5 text-xs font-medium transition-colors rounded-lg ${
                  activeTab === 'documents'
                    ? isDark
                      ? 'text-white bg-white/5'
                      : 'text-gray-900 bg-gray-100/50'
                    : isDark
                      ? 'text-white/60 hover:text-white hover:bg-white/5'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/30'
                }`}
              >
                <FileText className="w-4 h-4 inline mr-1" />
                Docs
              </button>
            </div>

            {/* Sessions List or Search Results */}
            <div className="flex-1 overflow-y-auto">
        {activeTab === 'chats' && (
          <>
            {showSearch ? (
              <div className="p-3 space-y-2">
                {isSearching ? (
                  <div className="text-center text-theme-text-secondary py-8">
                    <div className="animate-spin w-6 h-6 border-2 border-theme-accent-primary border-t-transparent rounded-full mx-auto mb-2"></div>
                    <p className="text-sm">Recherche en cours...</p>
                  </div>
                ) : searchResults.length > 0 ? (
                  <>
                    <div className={`text-xs mb-2 px-2 ${isDark ? 'text-white/60' : 'text-gray-600'}`}>
                      {searchResults.length} résultat(s) trouvé(s)
                    </div>
                    {searchResults.map((result) => (
                      <div
                        key={result.id}
                        onClick={() => handleSearchResultClick(result)}
                        className={`p-3 rounded-lg cursor-pointer transition-all duration-200 border border-transparent ${
                          isDark 
                            ? 'hover:bg-white/5 text-white' 
                            : 'hover:bg-gray-200/50 text-gray-900'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <div className="flex-1 min-w-0">
                            <p className={`font-medium text-xs mb-1 ${isDark ? 'text-purple-400' : 'text-purple-600'}`}>
                              {result.session_title}
                            </p>
                            <p className={`text-xs mb-1 ${isDark ? 'text-white/60' : 'text-gray-600'}`}>
                              {result.role === 'user' ? '👤 Vous' : '🤖 Assistant'} • {result.module_type}
                            </p>
                            <p className={`text-xs line-clamp-2 ${isDark ? 'text-white/80' : 'text-gray-800'}`}>
                              {result.highlight}
                            </p>
                            {result.created_at && (
                              <p className={`text-xs mt-1 ${isDark ? 'text-white/50' : 'text-gray-500'}`}>
                                {format(new Date(result.created_at), 'PPp', { locale: fr })}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </>
                ) : (
                  <div className={`text-center py-12 ${isDark ? 'text-white/60' : 'text-gray-600'}`}>
                    <Search className={`w-12 h-12 mx-auto mb-4 opacity-50 ${isDark ? 'text-white/50' : 'text-gray-400'}`} />
                    <p className={`text-sm ${isDark ? 'text-white/70' : 'text-gray-700'}`}>Aucun résultat</p>
                    <p className={`text-xs mt-1 ${isDark ? 'text-white/50' : 'text-gray-500'}`}>Essayez avec d'autres mots-clés</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-3">
                {Object.keys(groupedSessions).length > 0 ? (
                  Object.entries(groupedSessions).map(([groupKey, groupSessions]) => (
                    <div key={groupKey} className="mb-6">
                      <h3 className={`text-xs font-semibold uppercase tracking-wider mb-3 px-2 ${isDark ? 'text-white/80' : 'text-gray-700'}`}>
                        {groupKey}
                      </h3>
                      <div className="space-y-1">
                        {groupSessions.map((session) => (
                          <motion.div
                            key={session.id}
                            onClick={() => onSelectSession(session.id)}
                            className={`p-3 rounded-lg cursor-pointer transition-all duration-200 group relative ${
                              currentSession === session.id
                                ? isDark
                                  ? 'bg-white/5 text-white'
                                  : 'bg-gray-100/30 text-gray-900'
                                : isDark
                                  ? 'hover:bg-white/5 text-white/80'
                                  : 'hover:bg-gray-100/30 text-gray-700'
                            }`}
                            initial={{ opacity: 1, x: 0, scale: 1 }}
                            animate={deletingSessionId === session.id ? {
                              opacity: 0,
                              x: -100,
                              scale: 0.8
                            } : {
                              opacity: 1,
                              x: 0,
                              scale: 1
                            }}
                            exit={{ opacity: 0, x: -100, scale: 0.8 }}
                            transition={{ duration: 0.3, ease: "easeInOut" }}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <p className={`font-medium truncate text-sm mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{session.title}</p>
                                <p className={`text-xs line-clamp-1 ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                                  {session.title.length > 40 ? session.title.substring(0, 40) + '...' : session.title}
                                </p>
                              </div>
                              <motion.button
                                onClick={(e) => deleteSession(session.id, e)}
                                className={`opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 rounded-lg transition-all ${
                                  currentSession === session.id ? 'opacity-100' : ''
                                }`}
                                title="Supprimer"
                                whileHover={{ scale: 1.2, rotate: 10 }}
                                whileTap={{ scale: 0.9 }}
                                initial={{ scale: 1 }}
                                animate={deletingSessionId === session.id ? {
                                  scale: 1.3,
                                  rotate: 180
                                } : {}}
                                transition={{ duration: 0.3 }}
                              >
                                <Trash2 className="w-4 h-4 text-red-400" />
                              </motion.button>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className={`text-center py-12 ${isDark ? 'text-white/60' : 'text-gray-600'}`}>
                    <div className="mb-4 animate-pulse">
                      <MessageSquare className={`w-12 h-12 mx-auto opacity-50 ${isDark ? 'text-white/50' : 'text-gray-400'}`} />
                    </div>
                    <p className={`text-sm ${isDark ? 'text-white/70' : 'text-gray-700'}`}>Aucune conversation</p>
                    <p className={`text-xs mt-1 ${isDark ? 'text-white/50' : 'text-gray-500'}`}>Créez une nouvelle conversation</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
        {activeTab === 'documents' && (
          <div className={`text-center py-12 ${isDark ? 'text-white/60' : 'text-gray-600'}`}>
            <FileText className={`w-12 h-12 mx-auto mb-4 opacity-50 ${isDark ? 'text-white/50' : 'text-gray-400'}`} />
            <p className={`text-sm ${isDark ? 'text-white/70' : 'text-gray-700'}`}>Documents</p>
            <p className={`text-xs mt-1 ${isDark ? 'text-white/50' : 'text-gray-500'}`}>Gérez vos documents ici</p>
          </div>
        )}
        {activeTab === 'dashboard' && (
          <div className={`text-center py-12 ${isDark ? 'text-white/60' : 'text-gray-600'}`}>
            <BarChart3 className={`w-12 h-12 mx-auto mb-4 opacity-50 ${isDark ? 'text-white/50' : 'text-gray-400'}`} />
            <p className={`text-sm ${isDark ? 'text-white/70' : 'text-gray-700'}`}>Statistiques</p>
            <p className={`text-xs mt-1 ${isDark ? 'text-white/50' : 'text-gray-500'}`}>Voir vos statistiques</p>
          </div>
        )}
      </div>

            {/* User Section */}
            {isAuthenticated && user ? (
              <div className="p-3">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-theme-accent-primary to-theme-accent-secondary flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${isDark ? 'text-white' : 'text-gray-900'}`}>{user.username}</p>
                    <p className={`text-xs ${isDark ? 'text-white/60' : 'text-gray-600'}`}>En ligne</p>
                  </div>
                </div>
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-xl transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Déconnexion
                </button>
              </div>
            ) : (
              <div className="p-3 space-y-2">
                <motion.button
                  onClick={() => navigate('/login')}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-600/80 to-purple-600/80 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg shadow-blue-500/20 backdrop-blur-sm"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <LogIn className="w-4 h-4" />
                  Login
                </motion.button>
                <motion.button
                  onClick={() => navigate('/signup')}
                  className={`w-full flex items-center justify-center gap-2 px-3 py-2.5 text-sm font-medium rounded-xl transition-colors ${
                    isDark 
                      ? 'text-white/90 bg-white/5 hover:bg-white/10 border border-white/10' 
                      : 'text-gray-900 bg-gray-200/50 hover:bg-gray-300/50 border border-gray-300/50'
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <UserPlus className="w-4 h-4" />
                  Register
                </motion.button>
              </div>
            )}
          </motion.div>
        )}
      </motion.div>
    </>
  )
}

export default Sidebar
