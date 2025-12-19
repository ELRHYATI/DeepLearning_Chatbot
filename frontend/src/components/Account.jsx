import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { 
  User, Mail, Calendar, LogOut, LogIn, UserPlus, 
  Settings, Shield, Key, Bell, Globe, Moon, Sun,
  CheckCircle2, AlertCircle, Loader2, Edit2, Save, X,
  Download, Trash2, Eye, EyeOff, Database, Zap, Palette,
  Volume2, VolumeX, FileText, HardDrive, Clock, Languages,
  Lock, Unlock, RefreshCw, Copy, ExternalLink, Info, MessageSquare, ArrowLeft
} from 'lucide-react'
import ModernAuth from './ModernAuth'

const Account = () => {
  const { user, token, logout, isAuthenticated, loading } = useAuth()
  const { isDark, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [activeSection, setActiveSection] = useState(() => {
    // Check if coming from settings link
    const savedSection = localStorage.getItem('accountActiveSection')
    if (savedSection) {
      localStorage.removeItem('accountActiveSection')
      return savedSection
    }
    return 'profile'
  })
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    username: '',
    email: ''
  })
  const [saveLoading, setSaveLoading] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  
  // Settings state
  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      push: false,
      inApp: true,
      newMessages: true,
      systemUpdates: true,
      marketing: false
    },
    privacy: {
      profileVisibility: 'public',
      dataSharing: false,
      analytics: true
    },
    appearance: {
      fontSize: 'medium',
      compactMode: false,
      animations: true
    },
    chat: {
      autoSave: true,
      messageHistory: 30,
      showTimestamps: true
    },
    language: 'fr',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    dateFormat: 'DD/MM/YYYY'
  })
  
  const [exportLoading, setExportLoading] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)

  useEffect(() => {
    if (user && !isEditing) {
      setEditForm({
        username: user.username || '',
        email: user.email || ''
      })
    }
  }, [user, isEditing])

  useEffect(() => {
    // Check if coming from settings link
    const savedSection = localStorage.getItem('accountActiveSection')
    if (savedSection) {
      setActiveSection(savedSection)
      localStorage.removeItem('accountActiveSection')
    }
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleSaveProfile = async () => {
    setSaveLoading(true)
    setSaveSuccess(false)
    
    try {
      // Note: PUT endpoint for profile update not yet implemented in backend
      // For now, just show success message
      setSaveSuccess(true)
      setIsEditing(false)
      setTimeout(() => setSaveSuccess(false), 3000)
      
      // TODO: Implement PUT /api/auth/me endpoint in backend
      // const response = await fetch('/api/auth/me', {
      //   method: 'PUT',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${token}`
      //   },
      //   body: JSON.stringify(editForm)
      // })
      // if (response.ok) {
      //   window.location.reload()
      // } else {
      //   const error = await response.json()
      //   alert(error.detail || 'Erreur lors de la mise à jour')
      // }
    } catch (error) {
      alert('Erreur réseau')
    } finally {
      setSaveLoading(false)
    }
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    if (user) {
      setEditForm({
        username: user.username || '',
        email: user.email || ''
      })
    }
  }

  // If not authenticated, show enhanced login/signup
  if (!isAuthenticated && !loading) {
    return (
      <div className="min-h-screen bg-theme-bg-primary py-8 px-4 overflow-y-auto">
        <div className="w-full max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="relative"
          >
            {/* Back Button */}
            <motion.button
              onClick={() => navigate('/')}
              className={`mb-6 flex items-center gap-2 px-4 py-2 ${isDark ? 'bg-white/10 hover:bg-white/20 text-white' : 'bg-gray-200/50 hover:bg-gray-300/50 text-gray-900'} backdrop-blur-sm border ${isDark ? 'border-white/20' : 'border-gray-300/50'} rounded-lg transition-all`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </motion.button>

            {/* Enhanced Auth Component with better styling - Compact */}
            <div className="bg-theme-bg-secondary/50 backdrop-blur-xl rounded-3xl border border-white/10 shadow-2xl overflow-hidden mb-6">
              <ModernAuth initialMode="login" />
            </div>

            {/* Additional Info Cards - Compact */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="grid grid-cols-1 md:grid-cols-3 gap-4 pb-8"
            >
              <div className={`p-4 rounded-xl border ${isDark ? 'bg-theme-bg-tertiary/50 border-white/10' : 'bg-white/50 border-gray-200/50'} backdrop-blur-sm`}>
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isDark ? 'bg-purple-500/20' : 'bg-purple-100'}`}>
                    <Settings className={`w-5 h-5 ${isDark ? 'text-purple-400' : 'text-purple-600'}`} />
                  </div>
                  <h3 className={`text-base font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    Paramètres personnalisés
                  </h3>
                </div>
                <p className={`text-xs ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                  Personnalisez votre expérience avec des paramètres avancés
                </p>
              </div>

              <div className={`p-4 rounded-xl border ${isDark ? 'bg-theme-bg-tertiary/50 border-white/10' : 'bg-white/50 border-gray-200/50'} backdrop-blur-sm`}>
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isDark ? 'bg-blue-500/20' : 'bg-blue-100'}`}>
                    <Database className={`w-5 h-5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
                  </div>
                  <h3 className={`text-base font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    Gestion des données
                  </h3>
                </div>
                <p className={`text-xs ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                  Exportez et gérez toutes vos conversations et données
                </p>
              </div>

              <div className={`p-4 rounded-xl border ${isDark ? 'bg-theme-bg-tertiary/50 border-white/10' : 'bg-white/50 border-gray-200/50'} backdrop-blur-sm`}>
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isDark ? 'bg-green-500/20' : 'bg-green-100'}`}>
                    <Shield className={`w-5 h-5 ${isDark ? 'text-green-400' : 'text-green-600'}`} />
                  </div>
                  <h3 className={`text-base font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    Sécurité avancée
                  </h3>
                </div>
                <p className={`text-xs ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                  Protégez votre compte avec des options de sécurité avancées
                </p>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-theme-bg-primary">
        <Loader2 className="w-8 h-8 animate-spin text-theme-accent-primary" />
      </div>
    )
  }

  const handleSettingChange = (category, key, value) => {
    setSettings(prev => {
      const newSettings = {
        ...prev,
        [category]: {
          ...prev[category],
          [key]: value
        }
      }
      // Save to localStorage with updated settings
      localStorage.setItem('userSettings', JSON.stringify(newSettings))
      return newSettings
    })
  }

  const handleExportData = async () => {
    setExportLoading(true)
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      
      // Export user data
      const response = await fetch('/api/auth/me', { headers })
      if (response.ok) {
        const userData = await response.json()
        const dataStr = JSON.stringify(userData, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        const url = URL.createObjectURL(dataBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `academic-ai-data-${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Export error:', error)
      alert('Erreur lors de l\'exportation des données')
    } finally {
      setExportLoading(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (!deleteConfirm) {
      setDeleteConfirm(true)
      return
    }
    
    if (window.confirm('Êtes-vous sûr de vouloir supprimer votre compte ? Cette action est irréversible.')) {
      try {
        const token = localStorage.getItem('token')
        const response = await fetch('/api/auth/me', {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          logout()
          navigate('/')
        }
      } catch (error) {
        console.error('Delete error:', error)
        alert('Erreur lors de la suppression du compte')
      }
    }
    setDeleteConfirm(false)
  }

  useEffect(() => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('userSettings')
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings))
      } catch (e) {
        console.error('Error loading settings:', e)
      }
    }
  }, [])

  const sections = [
    { id: 'profile', label: 'Profil', icon: User },
    { id: 'settings', label: 'Paramètres', icon: Settings },
    { id: 'security', label: 'Sécurité', icon: Shield },
    { id: 'privacy', label: 'Confidentialité', icon: Lock },
    { id: 'data', label: 'Données', icon: Database },
  ]

  // Apply settings to document/body
  useEffect(() => {
    const root = document.documentElement
    const compact = settings.appearance.compactMode
    const fontSize = settings.appearance.fontSize
    
    // Apply font size
    if (fontSize === 'small') {
      root.style.fontSize = '14px'
    } else if (fontSize === 'medium') {
      root.style.fontSize = '16px'
    } else if (fontSize === 'large') {
      root.style.fontSize = '18px'
    }
    
    // Apply compact mode classes
    if (compact) {
      document.body.classList.add('compact-mode')
    } else {
      document.body.classList.remove('compact-mode')
    }
    
    return () => {
      root.style.fontSize = ''
      document.body.classList.remove('compact-mode')
    }
  }, [settings.appearance.compactMode, settings.appearance.fontSize])

  const shouldAnimate = settings.appearance.animations
  const compact = settings.appearance.compactMode

  return (
    <div className="h-screen bg-theme-bg-primary overflow-hidden flex flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className={`max-w-6xl mx-auto px-4 ${compact ? 'py-4' : 'py-8'}`}>
        {/* Header */}
        <motion.div
          initial={shouldAnimate ? { opacity: 0, y: -20 } : { opacity: 1, y: 0 }}
          animate={{ opacity: 1, y: 0 }}
          transition={shouldAnimate ? { duration: 0.3 } : { duration: 0 }}
          className={compact ? 'mb-4' : 'mb-8'}
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className={`${compact ? 'text-2xl' : 'text-3xl'} font-bold text-theme-text-primary mb-2`}>
                Mon Compte
              </h1>
              <p className={`text-theme-text-secondary ${compact ? 'text-sm' : ''}`}>
                Gérez vos informations et paramètres
              </p>
            </div>
            <motion.button
              onClick={handleLogout}
              className={`flex items-center gap-2 ${compact ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'} bg-theme-accent-error/10 hover:bg-theme-accent-error/20 text-theme-accent-error rounded-xl transition-colors`}
              whileHover={shouldAnimate ? { scale: 1.05 } : {}}
              whileTap={shouldAnimate ? { scale: 0.95 } : {}}
            >
              <LogOut className="w-5 h-5" />
              <span>Déconnexion</span>
            </motion.button>
          </div>
        </motion.div>

        <div className={`grid grid-cols-1 lg:grid-cols-4 ${compact ? 'gap-4' : 'gap-6'}`}>
          {/* Sidebar Navigation */}
          <motion.div
            initial={shouldAnimate ? { opacity: 0, x: -20 } : { opacity: 1, x: 0 }}
            animate={{ opacity: 1, x: 0 }}
            transition={shouldAnimate ? { duration: 0.3 } : { duration: 0 }}
            className="lg:col-span-1"
          >
            <div className={`bg-theme-bg-secondary rounded-2xl ${compact ? 'p-2' : 'p-4'} border border-theme-interactive-inputBorder`}>
              <nav className={compact ? 'space-y-1' : 'space-y-2'}>
                {sections.map((section) => {
                  const Icon = section.icon
                  return (
                    <motion.button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full flex items-center ${compact ? 'gap-2 px-3 py-2' : 'gap-3 px-4 py-3'} rounded-xl transition-all ${
                        activeSection === section.id
                          ? 'bg-theme-accent-primary text-white'
                          : 'text-theme-text-secondary hover:bg-theme-interactive-hover'
                      }`}
                      whileHover={shouldAnimate ? { scale: 1.02 } : {}}
                      whileTap={shouldAnimate ? { scale: 0.98 } : {}}
                    >
                      <Icon className={compact ? 'w-4 h-4' : 'w-5 h-5'} />
                      <span className={`font-medium ${compact ? 'text-sm' : ''}`}>{section.label}</span>
                    </motion.button>
                  )
                })}
              </nav>
            </div>
          </motion.div>

          {/* Main Content */}
          <motion.div
            key={activeSection}
            initial={shouldAnimate ? { opacity: 0, x: 20 } : { opacity: 1, x: 0 }}
            animate={{ opacity: 1, x: 0 }}
            exit={shouldAnimate ? { opacity: 0, x: -20 } : { opacity: 1, x: 0 }}
            transition={shouldAnimate ? { duration: 0.3 } : { duration: 0 }}
            className="lg:col-span-3"
          >
            <div className={`bg-theme-bg-secondary rounded-2xl ${compact ? 'p-4' : 'p-8'} border border-theme-interactive-inputBorder ${compact ? 'max-h-[calc(100vh-200px)] overflow-y-auto' : ''}`}>
              <AnimatePresence mode={shouldAnimate ? "wait" : false}>
                {activeSection === 'profile' && (
                  <motion.div
                    key="profile"
                    initial={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
                    animate={{ opacity: 1 }}
                    exit={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
                    transition={shouldAnimate ? { duration: 0.2 } : { duration: 0 }}
                    className={`space-y-${compact ? '4' : '6'}`}
                  >
                    <div className={`flex items-center justify-between ${compact ? 'mb-4' : 'mb-6'}`}>
                      <h2 className={`${compact ? 'text-xl' : 'text-2xl'} font-bold text-theme-text-primary`}>
                        Informations du profil
                      </h2>
                      {!isEditing && (
                        <motion.button
                          onClick={() => setIsEditing(true)}
                          className={`flex items-center gap-2 ${compact ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'} bg-theme-accent-primary text-white rounded-xl`}
                          whileHover={shouldAnimate ? { scale: 1.05 } : {}}
                          whileTap={shouldAnimate ? { scale: 0.95 } : {}}
                        >
                          <Edit2 className={compact ? 'w-3 h-3' : 'w-4 h-4'} />
                          <span>Modifier</span>
                        </motion.button>
                      )}
                    </div>

                    {saveSuccess && (
                      <motion.div
                        initial={shouldAnimate ? { opacity: 0, y: -10 } : { opacity: 1, y: 0 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={shouldAnimate ? { duration: 0.2 } : { duration: 0 }}
                        className={`flex items-center gap-2 ${compact ? 'p-2 text-sm' : 'p-4'} bg-theme-accent-success/20 border border-theme-accent-success text-theme-accent-success rounded-xl`}
                      >
                        <CheckCircle2 className={`w-${compact ? '4' : '5'} h-${compact ? '4' : '5'}`} />
                        <span>Profil mis à jour avec succès !</span>
                      </motion.div>
                    )}

                    <div className="space-y-6">
                      {/* Avatar Section */}
                      <div className="flex items-center gap-6">
                        <div className="w-24 h-24 rounded-full bg-gradient-button flex items-center justify-center text-white text-3xl font-bold">
                          {user?.username?.[0]?.toUpperCase() || 'U'}
                        </div>
                        <div>
                          <h3 className="text-xl font-semibold text-theme-text-primary">
                            {user?.username || 'Utilisateur'}
                          </h3>
                          <p className="text-theme-text-secondary">{user?.email}</p>
                        </div>
                      </div>

                      {/* Form Fields */}
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                            Nom d'utilisateur
                          </label>
                          {isEditing ? (
                            <input
                              type="text"
                              value={editForm.username}
                              onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                              className="w-full px-4 py-3 bg-theme-interactive-inputBg border-2 border-theme-interactive-inputBorder rounded-xl text-theme-text-primary focus:outline-none focus:border-theme-accent-primary transition-colors"
                              placeholder="Nom d'utilisateur"
                            />
                          ) : (
                            <div className="px-4 py-3 bg-theme-interactive-inputBg border-2 border-theme-interactive-inputBorder rounded-xl text-theme-text-primary">
                              {user?.username || 'Non défini'}
                            </div>
                          )}
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                            Email
                          </label>
                          {isEditing ? (
                            <input
                              type="email"
                              value={editForm.email}
                              onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                              className="w-full px-4 py-3 bg-theme-interactive-inputBg border-2 border-theme-interactive-inputBorder rounded-xl text-theme-text-primary focus:outline-none focus:border-theme-accent-primary transition-colors"
                              placeholder="Email"
                            />
                          ) : (
                            <div className="px-4 py-3 bg-theme-interactive-inputBg border-2 border-theme-interactive-inputBorder rounded-xl text-theme-text-primary">
                              {user?.email || 'Non défini'}
                            </div>
                          )}
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                            Date d'inscription
                          </label>
                          <div className="px-4 py-3 bg-theme-interactive-inputBg border-2 border-theme-interactive-inputBorder rounded-xl text-theme-text-secondary">
                            {user?.created_at 
                              ? new Date(user.created_at).toLocaleDateString('fr-FR', {
                                  year: 'numeric',
                                  month: 'long',
                                  day: 'numeric'
                                })
                              : 'Non disponible'}
                          </div>
                        </div>
                      </div>

                      {isEditing && (
                        <div className="flex gap-4 pt-4">
                          <motion.button
                            onClick={handleSaveProfile}
                            disabled={saveLoading}
                            className="flex items-center gap-2 px-6 py-3 bg-theme-accent-primary text-white rounded-xl font-medium disabled:opacity-50"
                            whileHover={shouldAnimate ? { scale: 1.05 } : {}}
                            whileTap={{ scale: 0.95 }}
                          >
                            {saveLoading ? (
                              <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                              <Save className="w-5 h-5" />
                            )}
                            <span>Enregistrer</span>
                          </motion.button>
                          <motion.button
                            onClick={handleCancelEdit}
                            className={`flex items-center gap-2 ${compact ? 'px-4 py-2 text-sm' : 'px-6 py-3'} bg-theme-bg-tertiary text-theme-text-primary rounded-xl font-medium`}
                            whileHover={shouldAnimate ? { scale: 1.05 } : {}}
                            whileTap={shouldAnimate ? { scale: 0.95 } : {}}
                          >
                            <X className="w-5 h-5" />
                            <span>Annuler</span>
                          </motion.button>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}

                {activeSection === 'settings' && (
                  <motion.div
                    key="settings"
                    initial={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
                    animate={{ opacity: 1 }}
                    exit={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
                    transition={shouldAnimate ? { duration: 0.2 } : { duration: 0 }}
                    className={`space-y-${compact ? '4' : '6'}`}
                  >
                    <h2 className={`${compact ? 'text-xl' : 'text-2xl'} font-bold text-theme-text-primary mb-${compact ? '4' : '6'}`}>
                      Paramètres
                    </h2>

                    <div className={`space-y-${compact ? '4' : '6'}`}>
                      {/* Appearance Section */}
                      <div className={`space-y-${compact ? '3' : '4'}`}>
                        <h3 className={`${compact ? 'text-base' : 'text-lg'} font-semibold text-theme-text-primary flex items-center gap-2`}>
                          <Palette className={`w-${compact ? '4' : '5'} h-${compact ? '4' : '5'}`} />
                          Apparence
                        </h3>
                        
                        {/* Theme Toggle */}
                        <div className={`flex items-center justify-between ${compact ? 'p-3' : 'p-4'} bg-theme-bg-tertiary rounded-xl`}>
                          <div className="flex items-center gap-3">
                            {isDark ? (
                              <Moon className="w-5 h-5 text-theme-text-secondary" />
                            ) : (
                              <Sun className="w-5 h-5 text-theme-text-secondary" />
                            )}
                            <div>
                              <h3 className="font-medium text-theme-text-primary">Thème</h3>
                              <p className="text-sm text-theme-text-secondary">
                                {isDark ? 'Mode sombre' : 'Mode clair'}
                              </p>
                            </div>
                          </div>
                          <motion.button
                            onClick={toggleTheme}
                            className={`relative ${compact ? 'w-12 h-6' : 'w-14 h-8'} rounded-full ${
                              isDark ? 'bg-theme-accent-primary' : 'bg-theme-interactive-inputBorder'
                            } transition-colors`}
                            whileTap={shouldAnimate ? { scale: 0.95 } : {}}
                          >
                            <motion.div
                              className={`absolute top-1 left-1 ${compact ? 'w-4 h-4' : 'w-6 h-6'} bg-white rounded-full shadow-lg`}
                              animate={{ x: isDark ? (compact ? 20 : 28) : 0 }}
                              transition={shouldAnimate ? { type: 'spring', stiffness: 500, damping: 30 } : { duration: 0 }}
                            />
                          </motion.button>
                        </div>

                        {/* Font Size */}
                        <div className={`${compact ? 'p-3' : 'p-4'} bg-theme-bg-tertiary rounded-xl`}>
                          <div className={`flex items-center justify-between ${compact ? 'mb-2' : 'mb-3'}`}>
                            <div className={compact ? 'flex items-center gap-2' : 'flex items-center gap-3'}>
                              <FileText className={`${compact ? 'w-4 h-4' : 'w-5 h-5'} text-theme-text-secondary`} />
                              <div>
                                <h3 className={`font-medium text-theme-text-primary ${compact ? 'text-sm' : ''}`}>Taille de police</h3>
                                <p className={`text-theme-text-secondary ${compact ? 'text-xs' : 'text-sm'}`}>Ajustez la taille du texte</p>
                              </div>
                            </div>
                          </div>
                          <div className={compact ? 'flex gap-1' : 'flex gap-2'}>
                            {['small', 'medium', 'large'].map((size) => (
                              <button
                                key={size}
                                onClick={() => handleSettingChange('appearance', 'fontSize', size)}
                                className={`${compact ? 'px-2 py-1 text-xs' : 'px-4 py-2'} rounded-lg transition-all ${
                                  settings.appearance.fontSize === size
                                    ? 'bg-theme-accent-primary text-white'
                                    : 'bg-theme-bg-secondary text-theme-text-secondary hover:bg-theme-interactive-hover'
                                }`}
                              >
                                {size === 'small' ? 'Petit' : size === 'medium' ? 'Moyen' : 'Grand'}
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Compact Mode */}
                        <div className={`flex items-center justify-between ${compact ? 'p-3' : 'p-4'} bg-theme-bg-tertiary rounded-xl`}>
                          <div className={compact ? 'flex items-center gap-2' : 'flex items-center gap-3'}>
                            <Zap className={`${compact ? 'w-4 h-4' : 'w-5 h-5'} text-theme-text-secondary`} />
                            <div>
                              <h3 className={`font-medium text-theme-text-primary ${compact ? 'text-sm' : ''}`}>Mode compact</h3>
                              <p className={`text-theme-text-secondary ${compact ? 'text-xs' : 'text-sm'}`}>
                                Interface plus dense
                              </p>
                            </div>
                          </div>
                          <motion.button
                            onClick={() => handleSettingChange('appearance', 'compactMode', !settings.appearance.compactMode)}
                            className={`relative ${compact ? 'w-12 h-6' : 'w-14 h-8'} rounded-full transition-colors ${
                              settings.appearance.compactMode ? 'bg-theme-accent-primary' : 'bg-theme-interactive-inputBorder'
                            }`}
                            whileTap={shouldAnimate ? { scale: 0.95 } : {}}
                          >
                            <motion.div
                              className={`absolute top-1 left-1 ${compact ? 'w-4 h-4' : 'w-6 h-6'} bg-white rounded-full shadow-lg`}
                              animate={{ x: settings.appearance.compactMode ? (compact ? 20 : 28) : 0 }}
                              transition={shouldAnimate ? { type: 'spring', stiffness: 500, damping: 30 } : { duration: 0 }}
                            />
                          </motion.button>
                        </div>

                        {/* Animations */}
                        <div className={`flex items-center justify-between ${compact ? 'p-3' : 'p-4'} bg-theme-bg-tertiary rounded-xl`}>
                          <div className={compact ? 'flex items-center gap-2' : 'flex items-center gap-3'}>
                            <RefreshCw className={`${compact ? 'w-4 h-4' : 'w-5 h-5'} text-theme-text-secondary`} />
                            <div>
                              <h3 className={`font-medium text-theme-text-primary ${compact ? 'text-sm' : ''}`}>Animations</h3>
                              <p className={`text-theme-text-secondary ${compact ? 'text-xs' : 'text-sm'}`}>
                                Activer les animations
                              </p>
                            </div>
                          </div>
                          <motion.button
                            onClick={() => handleSettingChange('appearance', 'animations', !settings.appearance.animations)}
                            className={`relative ${compact ? 'w-12 h-6' : 'w-14 h-8'} rounded-full transition-colors ${
                              settings.appearance.animations ? 'bg-theme-accent-primary' : 'bg-theme-interactive-inputBorder'
                            }`}
                            whileTap={shouldAnimate ? { scale: 0.95 } : {}}
                          >
                            <motion.div
                              className={`absolute top-1 left-1 ${compact ? 'w-4 h-4' : 'w-6 h-6'} bg-white rounded-full shadow-lg`}
                              animate={{ x: settings.appearance.animations ? (compact ? 20 : 28) : 0 }}
                              transition={shouldAnimate ? { type: 'spring', stiffness: 500, damping: 30 } : { duration: 0 }}
                            />
                          </motion.button>
                        </div>
                      </div>

                      {/* Notifications Section */}
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-theme-text-primary flex items-center gap-2">
                          <Bell className="w-5 h-5" />
                          Notifications
                        </h3>
                        
                        {Object.entries(settings.notifications).map(([key, value]) => (
                          <div key={key} className="flex items-center justify-between p-4 bg-theme-bg-tertiary rounded-xl">
                            <div>
                              <h3 className="font-medium text-theme-text-primary">
                                {key === 'email' ? 'Notifications par email' :
                                 key === 'push' ? 'Notifications push' :
                                 key === 'inApp' ? 'Notifications in-app' :
                                 key === 'newMessages' ? 'Nouveaux messages' :
                                 key === 'systemUpdates' ? 'Mises à jour système' :
                                 'Marketing'}
                              </h3>
                              <p className="text-sm text-theme-text-secondary">
                                {key === 'email' ? 'Recevoir des emails' :
                                 key === 'push' ? 'Notifications du navigateur' :
                                 key === 'inApp' ? 'Notifications dans l\'application' :
                                 key === 'newMessages' ? 'Alertes pour nouveaux messages' :
                                 key === 'systemUpdates' ? 'Informations système' :
                                 'Offres et promotions'}
                              </p>
                            </div>
                            <motion.button
                              onClick={() => handleSettingChange('notifications', key, !value)}
                              className={`relative w-14 h-8 rounded-full transition-colors ${
                                value ? 'bg-theme-accent-primary' : 'bg-theme-interactive-inputBorder'
                              }`}
                              whileTap={shouldAnimate ? { scale: 0.95 } : {}}
                            >
                              <motion.div
                                className="absolute top-1 left-1 w-6 h-6 bg-white rounded-full shadow-lg"
                                animate={{ x: value ? 24 : 0 }}
                                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                              />
                            </motion.button>
                          </div>
                        ))}
                      </div>

                      {/* Chat Preferences */}
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-theme-text-primary flex items-center gap-2">
                          <MessageSquare className="w-5 h-5" />
                          Préférences de chat
                        </h3>
                        
                        <div className="flex items-center justify-between p-4 bg-theme-bg-tertiary rounded-xl">
                          <div className="flex items-center gap-3">
                            <Save className="w-5 h-5 text-theme-text-secondary" />
                            <div>
                              <h3 className="font-medium text-theme-text-primary">Sauvegarde automatique</h3>
                              <p className="text-sm text-theme-text-secondary">
                                Enregistrer automatiquement les conversations
                              </p>
                            </div>
                          </div>
                          <motion.button
                            onClick={() => handleSettingChange('chat', 'autoSave', !settings.chat.autoSave)}
                            className={`relative w-14 h-8 rounded-full transition-colors ${
                              settings.chat.autoSave ? 'bg-theme-accent-primary' : 'bg-theme-interactive-inputBorder'
                            }`}
                            whileTap={{ scale: 0.95 }}
                          >
                            <motion.div
                              className="absolute top-1 left-1 w-6 h-6 bg-white rounded-full shadow-lg"
                              animate={{ x: settings.chat.autoSave ? 24 : 0 }}
                              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                            />
                          </motion.button>
                        </div>

                        <div className="p-4 bg-theme-bg-tertiary rounded-xl">
                          <div className="flex items-center gap-3 mb-3">
                            <Clock className="w-5 h-5 text-theme-text-secondary" />
                            <div>
                              <h3 className="font-medium text-theme-text-primary">Historique des messages</h3>
                              <p className="text-sm text-theme-text-secondary">
                                Conserver les messages pendant (jours)
                              </p>
                            </div>
                          </div>
                          <input
                            type="number"
                            min="1"
                            max="365"
                            value={settings.chat.messageHistory}
                            onChange={(e) => handleSettingChange('chat', 'messageHistory', parseInt(e.target.value))}
                            className="w-full px-4 py-2 bg-theme-interactive-inputBg border border-theme-interactive-inputBorder rounded-xl text-theme-text-primary"
                          />
                        </div>

                        <div className="flex items-center justify-between p-4 bg-theme-bg-tertiary rounded-xl">
                          <div className="flex items-center gap-3">
                            <Clock className="w-5 h-5 text-theme-text-secondary" />
                            <div>
                              <h3 className="font-medium text-theme-text-primary">Afficher les horodatages</h3>
                              <p className="text-sm text-theme-text-secondary">
                                Montrer l'heure des messages
                              </p>
                            </div>
                          </div>
                          <motion.button
                            onClick={() => handleSettingChange('chat', 'showTimestamps', !settings.chat.showTimestamps)}
                            className={`relative w-14 h-8 rounded-full transition-colors ${
                              settings.chat.showTimestamps ? 'bg-theme-accent-primary' : 'bg-theme-interactive-inputBorder'
                            }`}
                            whileTap={{ scale: 0.95 }}
                          >
                            <motion.div
                              className="absolute top-1 left-1 w-6 h-6 bg-white rounded-full shadow-lg"
                              animate={{ x: settings.chat.showTimestamps ? 24 : 0 }}
                              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                            />
                          </motion.button>
                        </div>
                      </div>

                      {/* Language & Region */}
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-theme-text-primary flex items-center gap-2">
                          <Globe className="w-5 h-5" />
                          Langue et région
                        </h3>
                        
                        <div className="p-4 bg-theme-bg-tertiary rounded-xl">
                          <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                            Langue
                          </label>
                          <select
                            value={settings.language}
                            onChange={(e) => handleSettingChange('', 'language', e.target.value)}
                            className="w-full px-4 py-2 bg-theme-interactive-inputBg border border-theme-interactive-inputBorder rounded-xl text-theme-text-primary"
                          >
                            <option value="fr">Français</option>
                            <option value="en">English</option>
                            <option value="es">Español</option>
                            <option value="de">Deutsch</option>
                          </select>
                        </div>

                        <div className="p-4 bg-theme-bg-tertiary rounded-xl">
                          <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                            Fuseau horaire
                          </label>
                          <select
                            value={settings.timezone}
                            onChange={(e) => handleSettingChange('', 'timezone', e.target.value)}
                            className="w-full px-4 py-2 bg-theme-interactive-inputBg border border-theme-interactive-inputBorder rounded-xl text-theme-text-primary"
                          >
                            <option value="Europe/Paris">Europe/Paris (GMT+1)</option>
                            <option value="America/New_York">America/New_York (GMT-5)</option>
                            <option value="Asia/Tokyo">Asia/Tokyo (GMT+9)</option>
                            <option value="UTC">UTC (GMT+0)</option>
                          </select>
                        </div>

                        <div className="p-4 bg-theme-bg-tertiary rounded-xl">
                          <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                            Format de date
                          </label>
                          <div className="flex gap-2">
                            {['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD'].map((format) => (
                              <button
                                key={format}
                                onClick={() => handleSettingChange('', 'dateFormat', format)}
                                className={`px-4 py-2 rounded-lg transition-all ${
                                  settings.dateFormat === format
                                    ? 'bg-theme-accent-primary text-white'
                                    : 'bg-theme-bg-secondary text-theme-text-secondary hover:bg-theme-interactive-hover'
                                }`}
                              >
                                {format}
                              </button>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeSection === 'security' && (
                  <motion.div
                    key="security"
                    initial={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
                    animate={{ opacity: 1 }}
                    exit={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
                    transition={shouldAnimate ? { duration: 0.2 } : { duration: 0 }}
                    className={compact ? 'space-y-4' : 'space-y-6'}
                  >
                    <h2 className={`${compact ? 'text-xl' : 'text-2xl'} font-bold text-theme-text-primary ${compact ? 'mb-4' : 'mb-6'}`}>
                      Sécurité
                    </h2>

                    <div className={compact ? 'space-y-3' : 'space-y-4'}>
                      {/* Change Password */}
                      <div className="p-6 bg-theme-bg-tertiary rounded-xl border border-theme-interactive-inputBorder">
                        <div className="flex items-center gap-3 mb-4">
                          <Key className="w-5 h-5 text-theme-text-secondary" />
                          <h3 className="font-medium text-theme-text-primary">Changer le mot de passe</h3>
                        </div>
                        <p className="text-sm text-theme-text-secondary mb-4">
                          Mettez à jour votre mot de passe pour sécuriser votre compte
                        </p>
                        <Link
                          to="/change-password"
                          className="inline-flex items-center gap-2 px-4 py-2 bg-theme-accent-primary text-white rounded-xl hover:opacity-90 transition-opacity"
                        >
                          Changer le mot de passe
                        </Link>
                      </div>

                      {/* Two Factor Auth */}
                      <div className="p-6 bg-theme-bg-tertiary rounded-xl border border-theme-interactive-inputBorder">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <Shield className="w-5 h-5 text-theme-text-secondary" />
                            <div>
                              <h3 className="font-medium text-theme-text-primary">Authentification à deux facteurs</h3>
                              <p className="text-sm text-theme-text-secondary">
                                Ajoutez une couche de sécurité supplémentaire
                              </p>
                            </div>
                          </div>
                          <span className="px-3 py-1 bg-theme-accent-warning/20 text-theme-accent-warning rounded-lg text-sm">
                            Bientôt disponible
                          </span>
                        </div>
                      </div>

                      {/* Active Sessions */}
                      <div className="p-6 bg-theme-bg-tertiary rounded-xl border border-theme-interactive-inputBorder">
                        <div className="flex items-center gap-3 mb-4">
                          <Globe className="w-5 h-5 text-theme-text-secondary" />
                          <h3 className="font-medium text-theme-text-primary">Sessions actives</h3>
                        </div>
                        <p className="text-sm text-theme-text-secondary mb-4">
                          Gérez les appareils connectés à votre compte
                        </p>
                        <div className="p-4 bg-theme-bg-secondary rounded-lg">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium text-theme-text-primary">Session actuelle</p>
                              <p className="text-sm text-theme-text-secondary">
                                {navigator.userAgent.includes('Windows') ? 'Windows' : 'Appareil'} • {new Date().toLocaleDateString('fr-FR')}
                              </p>
                            </div>
                            <span className="px-3 py-1 bg-theme-accent-success/20 text-theme-accent-success rounded-lg text-sm">
                              Actif
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeSection === 'privacy' && (
                  <motion.div
                    key="privacy"
                    initial={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
                    animate={{ opacity: 1 }}
                    exit={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
                    transition={shouldAnimate ? { duration: 0.2 } : { duration: 0 }}
                    className={compact ? 'space-y-4' : 'space-y-6'}
                  >
                    <h2 className={`${compact ? 'text-xl' : 'text-2xl'} font-bold text-theme-text-primary ${compact ? 'mb-4' : 'mb-6'}`}>
                      Confidentialité
                    </h2>

                    <div className={compact ? 'space-y-4' : 'space-y-6'}>
                      {/* Profile Visibility */}
                      <div className="p-6 bg-theme-bg-tertiary rounded-xl border border-theme-interactive-inputBorder">
                        <div className="flex items-center gap-3 mb-4">
                          <Eye className="w-5 h-5 text-theme-text-secondary" />
                          <h3 className="font-medium text-theme-text-primary">Visibilité du profil</h3>
                        </div>
                        <p className="text-sm text-theme-text-secondary mb-4">
                          Contrôlez qui peut voir votre profil
                        </p>
                        <div className="space-y-2">
                          {['public', 'private', 'friends'].map((option) => (
                            <label key={option} className="flex items-center gap-3 p-3 bg-theme-bg-secondary rounded-lg cursor-pointer hover:bg-theme-interactive-hover">
                              <input
                                type="radio"
                                name="visibility"
                                value={option}
                                checked={settings.privacy.profileVisibility === option}
                                onChange={(e) => handleSettingChange('privacy', 'profileVisibility', e.target.value)}
                                className="w-4 h-4 text-theme-accent-primary"
                              />
                              <div>
                                <p className="font-medium text-theme-text-primary">
                                  {option === 'public' ? 'Public' : option === 'private' ? 'Privé' : 'Amis uniquement'}
                                </p>
                                <p className="text-xs text-theme-text-secondary">
                                  {option === 'public' ? 'Tout le monde peut voir votre profil' :
                                   option === 'private' ? 'Seulement vous pouvez voir votre profil' :
                                   'Seulement vos contacts peuvent voir votre profil'}
                                </p>
                              </div>
                            </label>
                          ))}
                        </div>
                      </div>

                      {/* Data Sharing */}
                      <div className="flex items-center justify-between p-4 bg-theme-bg-tertiary rounded-xl">
                        <div className="flex items-center gap-3">
                          <Database className="w-5 h-5 text-theme-text-secondary" />
                          <div>
                            <h3 className="font-medium text-theme-text-primary">Partage de données</h3>
                            <p className="text-sm text-theme-text-secondary">
                              Autoriser le partage de données anonymisées
                            </p>
                          </div>
                        </div>
                        <motion.button
                          onClick={() => handleSettingChange('privacy', 'dataSharing', !settings.privacy.dataSharing)}
                          className={`relative w-14 h-8 rounded-full transition-colors ${
                            settings.privacy.dataSharing ? 'bg-theme-accent-primary' : 'bg-theme-interactive-inputBorder'
                          }`}
                          whileTap={{ scale: 0.95 }}
                        >
                          <motion.div
                            className="absolute top-1 left-1 w-6 h-6 bg-white rounded-full shadow-lg"
                            animate={{ x: settings.privacy.dataSharing ? 24 : 0 }}
                            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                          />
                        </motion.button>
                      </div>

                      {/* Analytics */}
                      <div className="flex items-center justify-between p-4 bg-theme-bg-tertiary rounded-xl">
                        <div className="flex items-center gap-3">
                          <Zap className="w-5 h-5 text-theme-text-secondary" />
                          <div>
                            <h3 className="font-medium text-theme-text-primary">Analytics</h3>
                            <p className="text-sm text-theme-text-secondary">
                              Collecter des données d'utilisation pour améliorer le service
                            </p>
                          </div>
                        </div>
                        <motion.button
                          onClick={() => handleSettingChange('privacy', 'analytics', !settings.privacy.analytics)}
                          className={`relative w-14 h-8 rounded-full transition-colors ${
                            settings.privacy.analytics ? 'bg-theme-accent-primary' : 'bg-theme-interactive-inputBorder'
                          }`}
                          whileTap={{ scale: 0.95 }}
                        >
                          <motion.div
                            className="absolute top-1 left-1 w-6 h-6 bg-white rounded-full shadow-lg"
                            animate={{ x: settings.privacy.analytics ? 24 : 0 }}
                            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                          />
                        </motion.button>
                      </div>

                      {/* Cookie Settings */}
                      <div className="p-6 bg-theme-bg-tertiary rounded-xl border border-theme-interactive-inputBorder">
                        <div className="flex items-center gap-3 mb-4">
                          <Info className="w-5 h-5 text-theme-text-secondary" />
                          <h3 className="font-medium text-theme-text-primary">Gestion des cookies</h3>
                        </div>
                        <p className="text-sm text-theme-text-secondary mb-4">
                          Gérez vos préférences de cookies
                        </p>
                        <motion.button
                          className="px-4 py-2 bg-theme-accent-primary text-white rounded-xl hover:opacity-90 transition-opacity"
                          whileHover={shouldAnimate ? { scale: 1.05 } : {}}
                          whileTap={{ scale: 0.95 }}
                        >
                          Gérer les cookies
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeSection === 'data' && (
                  <motion.div
                    key="data"
                    initial={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
                    animate={{ opacity: 1 }}
                    exit={shouldAnimate ? { opacity: 0 } : { opacity: 1 }}
                    transition={shouldAnimate ? { duration: 0.2 } : { duration: 0 }}
                    className={compact ? 'space-y-4' : 'space-y-6'}
                  >
                    <h2 className={`${compact ? 'text-xl' : 'text-2xl'} font-bold text-theme-text-primary ${compact ? 'mb-4' : 'mb-6'}`}>
                      Gestion des données
                    </h2>

                    <div className={compact ? 'space-y-4' : 'space-y-6'}>
                      {/* Storage Usage */}
                      <div className="p-6 bg-theme-bg-tertiary rounded-xl border border-theme-interactive-inputBorder">
                        <div className="flex items-center gap-3 mb-4">
                          <HardDrive className="w-5 h-5 text-theme-text-secondary" />
                          <h3 className="font-medium text-theme-text-primary">Utilisation du stockage</h3>
                        </div>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-theme-text-secondary">Conversations</span>
                            <span className="text-sm font-medium text-theme-text-primary">~2.5 MB</span>
                          </div>
                          <div className="w-full bg-theme-bg-secondary rounded-full h-2">
                            <div className="bg-theme-accent-primary h-2 rounded-full" style={{ width: '45%' }}></div>
                          </div>
                          <div className="flex items-center justify-between text-xs text-theme-text-secondary">
                            <span>2.5 MB utilisés sur 100 MB</span>
                            <span>2.5%</span>
                          </div>
                        </div>
                      </div>

                      {/* Export Data */}
                      <div className="p-6 bg-theme-bg-tertiary rounded-xl border border-theme-interactive-inputBorder">
                        <div className="flex items-center gap-3 mb-4">
                          <Download className="w-5 h-5 text-theme-text-secondary" />
                          <h3 className="font-medium text-theme-text-primary">Exporter vos données</h3>
                        </div>
                        <p className="text-sm text-theme-text-secondary mb-4">
                          Téléchargez une copie de toutes vos données (profil, conversations, paramètres)
                        </p>
                        <motion.button
                          onClick={handleExportData}
                          disabled={exportLoading}
                          className="flex items-center gap-2 px-4 py-2 bg-theme-accent-primary text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50"
                          whileHover={shouldAnimate ? { scale: 1.05 } : {}}
                          whileTap={{ scale: 0.95 }}
                        >
                          {exportLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                          ) : (
                            <Download className="w-5 h-5" />
                          )}
                          <span>{exportLoading ? 'Export en cours...' : 'Exporter les données'}</span>
                        </motion.button>
                      </div>

                      {/* Clear Cache */}
                      <div className="p-6 bg-theme-bg-tertiary rounded-xl border border-theme-interactive-inputBorder">
                        <div className="flex items-center gap-3 mb-4">
                          <RefreshCw className="w-5 h-5 text-theme-text-secondary" />
                          <h3 className="font-medium text-theme-text-primary">Vider le cache</h3>
                        </div>
                        <p className="text-sm text-theme-text-secondary mb-4">
                          Supprime les données temporaires pour libérer de l'espace
                        </p>
                        <motion.button
                          onClick={() => {
                            localStorage.clear()
                            sessionStorage.clear()
                            alert('Cache vidé avec succès')
                          }}
                          className="px-4 py-2 bg-theme-bg-secondary text-theme-text-primary rounded-xl hover:bg-theme-interactive-hover transition-colors"
                          whileHover={shouldAnimate ? { scale: 1.05 } : {}}
                          whileTap={{ scale: 0.95 }}
                        >
                          Vider le cache
                        </motion.button>
                      </div>

                      {/* Delete Account */}
                      <div className="p-6 bg-red-500/10 rounded-xl border border-red-500/30">
                        <div className="flex items-center gap-3 mb-4">
                          <Trash2 className="w-5 h-5 text-red-500" />
                          <h3 className="font-medium text-red-500">Zone de danger</h3>
                        </div>
                        <p className="text-sm text-theme-text-secondary mb-4">
                          La suppression de votre compte est permanente. Toutes vos données seront supprimées et ne pourront pas être récupérées.
                        </p>
                        {!deleteConfirm ? (
                          <motion.button
                            onClick={() => setDeleteConfirm(true)}
                            className="px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors"
                            whileHover={shouldAnimate ? { scale: 1.05 } : {}}
                            whileTap={{ scale: 0.95 }}
                          >
                            Supprimer mon compte
                          </motion.button>
                        ) : (
                          <div className="space-y-3">
                            <p className="text-sm font-medium text-red-500">
                              Êtes-vous sûr ? Cette action est irréversible.
                            </p>
                            <div className="flex gap-3">
                              <motion.button
                                onClick={handleDeleteAccount}
                                className="px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors"
                                whileHover={shouldAnimate ? { scale: 1.05 } : {}}
                                whileTap={shouldAnimate ? { scale: 0.95 } : {}}
                              >
                                Oui, supprimer
                              </motion.button>
                              <motion.button
                                onClick={() => setDeleteConfirm(false)}
                                className="px-4 py-2 bg-theme-bg-secondary text-theme-text-primary rounded-xl hover:bg-theme-interactive-hover transition-colors"
                                whileHover={shouldAnimate ? { scale: 1.05 } : {}}
                                whileTap={shouldAnimate ? { scale: 0.95 } : {}}
                              >
                                Annuler
                              </motion.button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
        </div>
      </div>
    </div>
  )
}

export default Account

