import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { clearAnonymousData } from '../utils/storage'

const GoogleCallback = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState(null)

  useEffect(() => {
    const code = searchParams.get('code')
    if (code) {
      handleGoogleCallback(code)
    } else {
      setError('No authorization code received')
    }
  }, [searchParams])

  const handleGoogleCallback = async (code) => {
    try {
      const response = await fetch('/api/auth/google/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: code })
      })

      if (response.ok) {
        const data = await response.json()
        // Clear anonymous data when user logs in
        clearAnonymousData()
        localStorage.setItem('token', data.access_token)
        // Reload page to update auth context
        window.location.href = '/'
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Authentication failed')
      }
    } catch (error) {
      setError('Network error during authentication')
    }
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Authentication Error</h2>
          <p className="text-gray-600 dark:text-gray-400">{error}</p>
          <button
            onClick={() => navigate('/login')}
            className="mt-4 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
          >
            Return to Login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Completing authentication...</p>
      </div>
    </div>
  )
}

export default GoogleCallback

