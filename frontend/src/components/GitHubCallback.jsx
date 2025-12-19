import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { clearAnonymousData } from '../utils/storage'
import { Loader2, CheckCircle2, XCircle } from 'lucide-react'

const GitHubCallback = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { loginWithGitHubCallback } = useAuth()
  const [status, setStatus] = useState('loading') // loading, success, error
  const [error, setError] = useState('')

  useEffect(() => {
    const code = searchParams.get('code')
    const errorParam = searchParams.get('error')
    
    if (errorParam) {
      setStatus('error')
      setError('L\'authentification GitHub a été annulée.')
      setTimeout(() => navigate('/login'), 3000)
      return
    }
    
    if (code) {
      handleGitHubCallback(code)
    } else {
      setStatus('error')
      setError('Code d\'autorisation manquant.')
      setTimeout(() => navigate('/login'), 3000)
    }
  }, [])

  const handleGitHubCallback = async (code) => {
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
        localStorage.setItem('token', data.access_token)
        setStatus('success')
        setTimeout(() => {
          navigate('/')
        }, 1500)
      } else {
        const errorData = await response.json()
        setStatus('error')
        setError(errorData.detail || 'Erreur lors de l\'authentification GitHub')
        setTimeout(() => navigate('/login'), 3000)
      }
    } catch (error) {
      console.error('GitHub callback error:', error)
      setStatus('error')
      setError('Erreur de connexion. Veuillez réessayer.')
      setTimeout(() => navigate('/login'), 3000)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-white/20">
        {status === 'loading' && (
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-12 h-12 text-purple-400 animate-spin" />
            <p className="text-white/90 text-lg">Authentification en cours...</p>
          </div>
        )}
        
        {status === 'success' && (
          <div className="flex flex-col items-center gap-4">
            <CheckCircle2 className="w-12 h-12 text-green-400" />
            <p className="text-white/90 text-lg">Authentification réussie!</p>
            <p className="text-white/70 text-sm">Redirection en cours...</p>
          </div>
        )}
        
        {status === 'error' && (
          <div className="flex flex-col items-center gap-4">
            <XCircle className="w-12 h-12 text-red-400" />
            <p className="text-white/90 text-lg">Erreur d'authentification</p>
            <p className="text-white/70 text-sm">{error}</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default GitHubCallback

