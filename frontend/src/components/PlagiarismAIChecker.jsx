import { useState } from 'react'
import { 
  FileText, Upload, Shield, Brain, AlertTriangle, 
  CheckCircle, XCircle, Loader2, Gauge, TrendingUp,
  AlertCircle, Sparkles, FileCheck
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'

const PlagiarismAIChecker = () => {
  const { isDark } = useTheme()
  const { user } = useAuth()
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [checkMode, setCheckMode] = useState('text') // 'text' or 'file'

  const handleCombinedCheck = async () => {
    if (!text.trim()) {
      setError('Veuillez entrer du texte à vérifier')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const token = localStorage.getItem('token')
      const headers = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('/api/plagiarism/check-with-ai-detection', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          text: text,
          min_similarity: 0.7
        })
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data)
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur lors de la vérification' }))
        setError(errorData.detail || 'Erreur lors de la vérification')
      }
    } catch (err) {
      console.error('Error checking:', err)
      setError('Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  const handleFileCheck = async (uploadedFile) => {
    if (!uploadedFile) {
      setError('Veuillez sélectionner un fichier')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const token = localStorage.getItem('token')
      const formData = new FormData()
      formData.append('file', uploadedFile)

      const headers = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      // First extract text, then check
      const uploadResponse = await fetch('/api/plagiarism/check-upload?min_similarity=0.7', {
        method: 'POST',
        headers,
        body: formData
      })

      if (uploadResponse.ok) {
        const plagiarismData = await uploadResponse.json()
        
        // Now check for AI (we need the text, so we'll extract it from file)
        // For now, we'll use a workaround - check AI separately
        const aiResponse = await fetch('/api/plagiarism/detect-ai', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...headers
          },
          body: JSON.stringify({
            text: text || 'Extracted text from file' // This would need file text extraction
          })
        })

        if (aiResponse.ok) {
          const aiData = await aiResponse.json()
          setResults({
            plagiarism: plagiarismData,
            ai_detection: aiData,
            combined: {
              overall_assessment: aiData.is_ai ? 'ai_detected' : 'clean',
              overall_message: aiData.message
            }
          })
        } else {
          setResults({
            plagiarism: plagiarismData,
            ai_detection: null
          })
        }
      } else {
        const errorData = await uploadResponse.json().catch(() => ({ detail: 'Erreur lors de la vérification' }))
        setError(errorData.detail || 'Erreur lors de la vérification')
      }
    } catch (err) {
      console.error('Error checking file:', err)
      setError('Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      // For file upload, we'd need to extract text first
      // For now, show error
      setError('L\'extraction de texte depuis le fichier sera disponible prochainement. Utilisez le mode texte.')
    }
  }

  const getAIColor = (probability) => {
    if (probability >= 0.8) return 'text-red-600 dark:text-red-400'
    if (probability >= 0.6) return 'text-orange-600 dark:text-orange-400'
    if (probability >= 0.4) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-green-600 dark:text-green-400'
  }

  const getAIBgColor = (probability) => {
    if (probability >= 0.8) return 'bg-red-500'
    if (probability >= 0.6) return 'bg-orange-500'
    if (probability >= 0.4) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getAIGaugeColor = (probability) => {
    if (probability >= 0.8) return '#ef4444' // red
    if (probability >= 0.6) return '#f97316' // orange
    if (probability >= 0.4) return '#eab308' // yellow
    return '#22c55e' // green
  }

  const AIGauge = ({ probability, size = 200 }) => {
    const radius = size / 2 - 20
    const circumference = 2 * Math.PI * radius
    const offset = circumference - (probability * circumference)
    const color = getAIGaugeColor(probability)
    
    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={isDark ? '#374151' : '#e5e7eb'}
            strokeWidth="12"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-1000"
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={`text-4xl font-bold ${getAIColor(probability)}`}>
            {Math.round(probability * 100)}%
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Probabilité IA
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
          <Shield className="w-8 h-8" />
          Vérification Plagiat & Détection IA
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Vérifiez le plagiat et détectez si le texte est généré par IA
        </p>
      </div>

      {/* Mode Selection */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => {
            setCheckMode('text')
            setResults(null)
            setError(null)
          }}
          className={`px-4 py-2 rounded-lg transition-colors ${
            checkMode === 'text'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
          }`}
        >
          Vérifier du Texte
        </button>
        <button
          onClick={() => {
            setCheckMode('file')
            setResults(null)
            setError(null)
          }}
          className={`px-4 py-2 rounded-lg transition-colors ${
            checkMode === 'file'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
          }`}
        >
          Vérifier un Fichier
        </button>
      </div>

      {/* Input Section */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
        {checkMode === 'text' ? (
          <div className="space-y-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Texte à vérifier
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Collez votre texte ici pour vérifier le plagiat et détecter l'IA..."
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       resize-none min-h-[200px]"
              autoFocus
            />
            <button
              onClick={handleCombinedCheck}
              disabled={loading || !text.trim()}
              className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg 
                       transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyse en cours...
                </>
              ) : (
                <>
                  <FileCheck className="w-5 h-5" />
                  Vérifier Plagiat & IA
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Fichier à vérifier (PDF, TXT, DOCX)
            </label>
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
              <input
                type="file"
                accept=".pdf,.txt,.docx"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer flex flex-col items-center gap-4"
              >
                <Upload className="w-12 h-12 text-gray-400" />
                <div>
                  <span className="text-blue-600 dark:text-blue-400 font-medium">
                    Cliquez pour téléverser
                  </span>
                  <span className="text-gray-500 dark:text-gray-400"> ou glissez-déposez</span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  PDF, TXT ou DOCX (max 10MB)
                </p>
              </label>
              {file && (
                <div className="mt-4 flex items-center justify-center gap-2">
                  <FileText className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{file.name}</span>
                </div>
              )}
            </div>
            {loading && (
              <div className="flex items-center justify-center gap-2 text-blue-600 dark:text-blue-400">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Analyse en cours...</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
        >
          <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
            <AlertTriangle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </motion.div>
      )}

      {/* Results */}
      <AnimatePresence>
        {results && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* AI Detection Gauge */}
            {results.ai_detection && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                      <Brain className="w-6 h-6" />
                      Détection IA
                    </h2>
                    <p className={`text-sm mt-1 ${getAIColor(results.ai_detection.ai_probability)}`}>
                      {results.ai_detection.message}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center justify-center gap-12">
                  {/* Gauge */}
                  <AIGauge probability={results.ai_detection.ai_probability} size={200} />
                  
                  {/* Details */}
                  <div className="space-y-4">
                    <div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                        Probabilité IA
                      </div>
                      <div className={`text-2xl font-bold ${getAIColor(results.ai_detection.ai_probability)}`}>
                        {(results.ai_detection.ai_probability * 100).toFixed(1)}%
                      </div>
                    </div>
                    
                    <div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                        Confiance
                      </div>
                      <div className="text-lg font-semibold text-gray-900 dark:text-white">
                        {(results.ai_detection.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                    
                    {results.ai_detection.details && (
                      <div className="space-y-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Perplexité: {results.ai_detection.details.perplexity}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Burstiness: {results.ai_detection.details.burstiness.toFixed(3)}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Répétition: {(results.ai_detection.details.repetition * 100).toFixed(1)}%
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Status Badge */}
                <div className="mt-6 flex justify-center">
                  <div className={`
                    px-4 py-2 rounded-lg flex items-center gap-2
                    ${results.ai_detection.is_ai 
                      ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200'
                      : 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-200'
                    }
                  `}>
                    {results.ai_detection.is_ai ? (
                      <>
                        <XCircle className="w-5 h-5" />
                        <span className="font-medium">Texte probablement généré par IA</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-5 h-5" />
                        <span className="font-medium">Texte probablement écrit par un humain</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Plagiarism Results */}
            {results.plagiarism && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <Shield className="w-6 h-6" />
                  Analyse de Plagiat
                </h2>
                
                {results.plagiarism.summary && (
                  <div className={`
                    p-4 rounded-lg mb-4 border-2
                    ${results.plagiarism.summary.status === 'clean' 
                      ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20' 
                      : results.plagiarism.summary.status === 'low_risk'
                      ? 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20'
                      : results.plagiarism.summary.status === 'medium_risk'
                      ? 'border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20'
                      : 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
                    }
                  `}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className={`font-medium ${
                          results.plagiarism.summary.status === 'clean' ? 'text-green-800 dark:text-green-200' :
                          results.plagiarism.summary.status === 'low_risk' ? 'text-yellow-800 dark:text-yellow-200' :
                          results.plagiarism.summary.status === 'medium_risk' ? 'text-orange-800 dark:text-orange-200' :
                          'text-red-800 dark:text-red-200'
                        }`}>
                          {results.plagiarism.summary.message}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {results.plagiarism.total_documents_checked} documents vérifiés
                        </p>
                      </div>
                      <div className="text-right">
                        <div className={`text-3xl font-bold ${
                          results.plagiarism.summary.status === 'clean' ? 'text-green-600' :
                          results.plagiarism.summary.status === 'low_risk' ? 'text-yellow-600' :
                          results.plagiarism.summary.status === 'medium_risk' ? 'text-orange-600' :
                          'text-red-600'
                        }`}>
                          {results.plagiarism.summary.similarity_percentage.toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">Similarité</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Matches */}
                {results.plagiarism.matches && results.plagiarism.matches.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Documents Similaires ({results.plagiarism.matches.length})
                    </h3>
                    <div className="space-y-3">
                      {results.plagiarism.matches.slice(0, 5).map((match, index) => (
                        <div
                          key={index}
                          className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <FileText className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                                <span className="font-medium text-gray-900 dark:text-white">
                                  {match.document_name}
                                </span>
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                Similarité: {(match.similarity * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Combined Assessment */}
            {results.combined && (
              <div className={`
                p-6 rounded-xl border-2
                ${results.combined.overall_assessment === 'clean' 
                  ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20' 
                  : results.combined.overall_assessment === 'ai_detected'
                  ? 'border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20'
                  : 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
                }
              `}>
                <div className="flex items-center gap-3 mb-3">
                  <Sparkles className={`w-6 h-6 ${
                    results.combined.overall_assessment === 'clean' 
                      ? 'text-green-600 dark:text-green-400'
                      : results.combined.overall_assessment === 'ai_detected'
                      ? 'text-orange-600 dark:text-orange-400'
                      : 'text-red-600 dark:text-red-400'
                  }`} />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Évaluation Globale
                  </h3>
                </div>
                <p className="text-gray-700 dark:text-gray-300">
                  {results.combined.overall_message}
                </p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default PlagiarismAIChecker

