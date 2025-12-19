import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import ChatInterface from './components/ChatInterface'
import Sidebar from './components/Sidebar'
import DocumentManager from './components/DocumentManager'
import Dashboard from './components/Dashboard'
import Account from './components/Account'
import ModernAuth from './components/ModernAuth'
import GoogleCallback from './components/GoogleCallback'
import GitHubCallback from './components/GitHubCallback'
import AboutPage from './components/AboutPage'
import ProtectedRoute from './components/ProtectedRoute'
import LandingPage from './components/LandingPage'
import LandingPageNew from './components/LandingPageNew'
import LearningDashboard from './components/LearningDashboard'
import PlagiarismChecker from './components/PlagiarismChecker'
import PlagiarismAIChecker from './components/PlagiarismAIChecker'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'
import './App.css'

function App() {
  const [currentSession, setCurrentSession] = useState(null)
  const [sessions, setSessions] = useState([])
  const [isNavigatingToLanding, setIsNavigatingToLanding] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    // Load sessions on mount only if authenticated
    const token = localStorage.getItem('token')
    if (token) {
      fetchSessions()
    }
  }, [])

  const fetchSessions = async () => {
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      const response = await fetch('/api/chat/sessions', {
        headers
      })
      if (response.ok) {
        const data = await response.json()
        setSessions(data)
        if (data.length > 0 && !currentSession) {
          setCurrentSession(data[0].id)
        }
      }
    } catch (error) {
      console.error('Error fetching sessions:', error)
    }
  }

  const navigateToLanding = () => {
    setIsNavigatingToLanding(true)
    setTimeout(() => {
      setCurrentSession(null)
      setIsNavigatingToLanding(false)
    }, 300)
  }

  const createNewSession = async (moduleType = 'general') => {
    try {
      const token = localStorage.getItem('token')
      const headers = { 'Content-Type': 'application/json' }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      const moduleLabels = {
        'grammar': 'Grammar',
        'qa': 'Q&A',
        'reformulation': 'Reformulation',
        'general': 'General'
      }
      const title = moduleType !== 'general' 
        ? `${moduleLabels[moduleType]} - ${new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`
        : `Conversation ${new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`
      const response = await fetch('/api/chat/sessions', {
        method: 'POST',
        headers,
        body: JSON.stringify({ title })
      })
      if (response.ok) {
        const newSession = await response.json()
        setSessions([newSession, ...sessions])
        setCurrentSession(newSession.id)
      } else {
        const errorData = await response.json().catch(() => ({}))
        console.error('Failed to create session:', response.status, errorData)
        // Try to create a local session if API fails
        const localSession = {
          id: Date.now(),
          title: `Conversation ${new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 0
        }
        setSessions([localSession, ...sessions])
        setCurrentSession(localSession.id)
      }
    } catch (error) {
      console.error('Error creating session:', error)
      // Create local session as fallback
      const localSession = {
        id: Date.now(),
        title: `Conversation ${new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        message_count: 0
      }
      setSessions([localSession, ...sessions])
      setCurrentSession(localSession.id)
    }
  }

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <Router>
          <Routes>
            <Route path="/login" element={<ModernAuth initialMode="login" />} />
            <Route path="/signup" element={<ModernAuth initialMode="signup" />} />
            <Route path="/auth/callback/google" element={<GoogleCallback />} />
            <Route path="/auth/callback/github" element={<GitHubCallback />} />
            <Route path="/about" element={<AboutPage />} />
            <Route
              path="/*"
              element={
                <Routes>
                  <Route
                    path="/"
                    element={
                      currentSession ? (
                        <div className={`flex h-screen transition-all duration-300 ${isNavigatingToLanding ? 'opacity-0 scale-95' : 'opacity-100 scale-100'} relative`} style={{ background: '#0F1419' }}>
                          <Sidebar
                            sessions={sessions}
                            currentSession={currentSession}
                            onSelectSession={setCurrentSession}
                            onCreateSession={createNewSession}
                            onSessionsUpdate={fetchSessions}
                            onNavigateToLanding={navigateToLanding}
                            isOpen={sidebarOpen}
                            onToggle={() => setSidebarOpen(!sidebarOpen)}
                          />
                          <motion.div 
                            className="flex-1 flex flex-col overflow-hidden"
                            animate={{
                              marginLeft: sidebarOpen ? '296px' : '0px'
                            }}
                            transition={{
                              duration: 0.3,
                              ease: "easeInOut"
                            }}
                          >
                            <ChatInterface
                              sessionId={currentSession}
                              onSessionUpdate={fetchSessions}
                            />
                          </motion.div>
                        </div>
                      ) : (
                        <LandingPageNew onCreateSession={createNewSession} />
                      )
                    }
                  />
                  <Route
                    path="/dashboard"
                    element={
                      <div className="flex h-screen transition-colors relative" style={{ background: '#0F1419' }}>
                        <Sidebar
                          sessions={sessions}
                          currentSession={currentSession}
                          onSelectSession={setCurrentSession}
                          onCreateSession={createNewSession}
                          onSessionsUpdate={fetchSessions}
                          onNavigateToLanding={navigateToLanding}
                          isOpen={sidebarOpen}
                          onToggle={() => setSidebarOpen(!sidebarOpen)}
                        />
                        <motion.div 
                          className="flex-1 flex flex-col overflow-hidden"
                          animate={{
                            marginLeft: sidebarOpen ? '296px' : '0px'
                          }}
                          transition={{
                            duration: 0.3,
                            ease: "easeInOut"
                          }}
                        >
                          <Dashboard />
                        </motion.div>
                      </div>
                    }
                  />
                  <Route
                    path="/documents"
                    element={
                      <div className="flex h-screen transition-colors relative" style={{ background: '#0F1419' }}>
                        <Sidebar
                          sessions={sessions}
                          currentSession={currentSession}
                          onSelectSession={setCurrentSession}
                          onCreateSession={createNewSession}
                          onSessionsUpdate={fetchSessions}
                          onNavigateToLanding={navigateToLanding}
                          isOpen={sidebarOpen}
                          onToggle={() => setSidebarOpen(!sidebarOpen)}
                        />
                        <motion.div 
                          className="flex-1 flex flex-col overflow-hidden"
                          animate={{
                            marginLeft: sidebarOpen ? '296px' : '0px'
                          }}
                          transition={{
                            duration: 0.3,
                            ease: "easeInOut"
                          }}
                        >
                          <DocumentManager />
                        </motion.div>
                      </div>
                    }
                  />
                  <Route
                    path="/account"
                    element={
                      <div className="flex h-screen transition-colors relative" style={{ background: '#0F1419' }}>
                        <Sidebar
                          sessions={sessions}
                          currentSession={currentSession}
                          onSelectSession={setCurrentSession}
                          onCreateSession={createNewSession}
                          onSessionsUpdate={fetchSessions}
                          onNavigateToLanding={navigateToLanding}
                          isOpen={sidebarOpen}
                          onToggle={() => setSidebarOpen(!sidebarOpen)}
                        />
                        <motion.div 
                          className="flex-1 flex flex-col overflow-hidden"
                          animate={{
                            marginLeft: sidebarOpen ? '296px' : '0px'
                          }}
                          transition={{
                            duration: 0.3,
                            ease: "easeInOut"
                          }}
                        >
                          <Account />
                        </motion.div>
                      </div>
                    }
                  />
                  <Route
                    path="/learning"
                    element={
                      <div className="flex h-screen transition-colors relative" style={{ background: '#0F1419' }}>
                        <Sidebar
                          sessions={sessions}
                          currentSession={currentSession}
                          onSelectSession={setCurrentSession}
                          onCreateSession={createNewSession}
                          onSessionsUpdate={fetchSessions}
                          onNavigateToLanding={navigateToLanding}
                          isOpen={sidebarOpen}
                          onToggle={() => setSidebarOpen(!sidebarOpen)}
                        />
                        <motion.div 
                          className="flex-1 flex flex-col overflow-hidden overflow-y-auto"
                          animate={{
                            marginLeft: sidebarOpen ? '296px' : '0px'
                          }}
                          transition={{
                            duration: 0.3,
                            ease: "easeInOut"
                          }}
                        >
                          <LearningDashboard />
                        </motion.div>
                      </div>
                    }
                  />
                  <Route
                    path="/plagiarism"
                    element={
                      <div className="flex h-screen transition-colors relative" style={{ background: '#0F1419' }}>
                        <Sidebar
                          sessions={sessions}
                          currentSession={currentSession}
                          onSelectSession={setCurrentSession}
                          onCreateSession={createNewSession}
                          onSessionsUpdate={fetchSessions}
                          onNavigateToLanding={navigateToLanding}
                          isOpen={sidebarOpen}
                          onToggle={() => setSidebarOpen(!sidebarOpen)}
                        />
                        <motion.div 
                          className="flex-1 flex flex-col overflow-hidden overflow-y-auto"
                          animate={{
                            marginLeft: sidebarOpen ? '296px' : '0px'
                          }}
                          transition={{
                            duration: 0.3,
                            ease: "easeInOut"
                          }}
                        >
                          <PlagiarismAIChecker />
                        </motion.div>
                      </div>
                    }
                  />
                </Routes>
              }
            />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
    </ErrorBoundary>
  )
}

export default App

