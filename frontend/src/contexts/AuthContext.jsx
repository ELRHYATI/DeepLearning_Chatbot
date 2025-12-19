import { createContext, useContext, useState, useEffect } from 'react'
import { clearAnonymousData } from '../utils/storage'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    if (token) {
      fetchUserInfo()
    } else {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const fetchUserInfo = async () => {
    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Token invalid, clear it
        logout()
      }
    } catch (error) {
      console.error('Error fetching user info:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, username: email })
      })
      
      if (response.ok) {
        const data = await response.json()
        // Clear anonymous data when user logs in
        clearAnonymousData()
        setToken(data.access_token)
        setUser(data.user)
        localStorage.setItem('token', data.access_token)
        return { success: true }
      } else {
        const error = await response.json()
        return { success: false, error: error.detail || 'Login failed' }
      }
    } catch (error) {
      return { success: false, error: 'Network error' }
    }
  }

  const register = async (username, email, password) => {
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
      })
      
      if (response.ok) {
        const userData = await response.json()
        // Auto login after registration
        const loginResult = await login(email, password)
        return loginResult
      } else {
        try {
          const error = await response.json()
          return { success: false, error: error.detail || error.message || `Registration failed (${response.status})` }
        } catch (e) {
          return { success: false, error: `Registration failed: ${response.status} ${response.statusText}` }
        }
      }
    } catch (error) {
      console.error('Registration error:', error)
      return { success: false, error: `Network error: ${error.message}` }
    }
  }

  const loginWithGoogle = async () => {
    try {
      const response = await fetch('/api/auth/google/url')
      if (response.ok) {
        const data = await response.json()
        window.location.href = data.auth_url
      } else {
        const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }))
        console.error('Google OAuth error:', error)
        const errorMessage = error.detail || 'Erreur lors de la connexion avec Google'
        
        // Message plus détaillé selon l'erreur
        if (errorMessage.includes('pas configurée') || errorMessage.includes('not configured')) {
          alert('⚠️ Google OAuth n\'est pas configuré.\n\nVeuillez configurer GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET dans le fichier backend/.env\n\nConsultez OAUTH_SETUP_GUIDE.md pour les instructions détaillées.')
        } else {
          alert(`Erreur: ${errorMessage}\n\nVérifiez:\n1. Que le backend est démarré\n2. Que les variables d'environnement sont configurées\n3. Que l'URL de callback correspond dans Google Cloud Console`)
        }
      }
    } catch (error) {
      console.error('Error getting Google auth URL:', error)
      alert('Erreur de connexion au serveur.\n\nVérifiez que le backend est démarré sur http://localhost:8000')
    }
  }

  const loginWithGitHub = async () => {
    try {
      const response = await fetch('/api/auth/github/url')
      if (response.ok) {
        const data = await response.json()
        window.location.href = data.auth_url
      } else {
        const error = await response.json().catch(() => ({ detail: 'Erreur inconnue' }))
        console.error('GitHub OAuth error:', error)
        const errorMessage = error.detail || 'Erreur lors de la connexion avec GitHub'
        
        // Message plus détaillé selon l'erreur
        if (errorMessage.includes('pas configurée') || errorMessage.includes('not configured')) {
          alert('⚠️ GitHub OAuth n\'est pas configuré.\n\nVeuillez configurer GITHUB_CLIENT_ID et GITHUB_CLIENT_SECRET dans le fichier backend/.env\n\nConsultez OAUTH_SETUP_GUIDE.md pour les instructions détaillées.')
        } else {
          alert(`Erreur: ${errorMessage}\n\nVérifiez:\n1. Que le backend est démarré\n2. Que les variables d'environnement sont configurées\n3. Que l'URL de callback correspond dans GitHub OAuth App`)
        }
      }
    } catch (error) {
      console.error('Error getting GitHub auth URL:', error)
      alert('Erreur de connexion au serveur.\n\nVérifiez que le backend est démarré sur http://localhost:8000')
    }
  }

  const loginWithGitHubCallback = async (code) => {
    try {
      const response = await fetch('/api/auth/github/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: code })
      })
      
      if (response.ok) {
        const data = await response.json()
        // Clear anonymous data when user logs in
        clearAnonymousData()
        setToken(data.access_token)
        setUser(data.user)
        localStorage.setItem('token', data.access_token)
        return { success: true }
      } else {
        const error = await response.json()
        return { success: false, error: error.detail || 'GitHub authentication failed' }
      }
    } catch (error) {
      return { success: false, error: 'Network error' }
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
  }

  const value = {
    user,
    token,
    loading,
    login,
    register,
    loginWithGoogle,
    loginWithGitHub,
    loginWithGitHubCallback,
    logout,
    isAuthenticated: !!token && !!user
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

