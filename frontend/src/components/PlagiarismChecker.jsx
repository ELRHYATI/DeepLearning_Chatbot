import { useState } from 'react'
import { 
  FileText, Upload, AlertTriangle, CheckCircle, 
  XCircle, Loader2, FileCheck, TrendingUp, 
  AlertCircle, Shield, FileX
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'

const PlagiarismChecker = () => {
  const { isDark } = useTheme()
  const { user } = useAuth()
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [checkMode, setCheckMode] = useState('text') // 'text' or 'file'

  const handleTextCheck = async () => {
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

      const response = await fetch('/api/plagiarism/check-text', {
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
      console.error('Error checking plagiarism:', err)
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

      const response = await fetch('/api/plagiarism/check-upload?min_similarity=0.7', {
        method: 'POST',
        headers,
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data)
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur lors de la vérification' }))
        setError(errorData.detail || 'Erreur lors de la vérification')
      }
    } catch (err) {
      console.error('Error checking plagiarism:', err)
      setError('Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      handleFileCheck(selectedFile)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'clean':
        return 'text-green-600 dark:text-green-400'
      case 'low_risk':
        return 'text-yellow-600 dark:text-yellow-400'
      case 'medium_risk':
        return 'text-orange-600 dark:text-orange-400'
      case 'high_risk':
        return 'text-red-600 dark:text-red-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'clean':
        return <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
      case 'low_risk':
        return <AlertCircle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
      case 'medium_risk':
        return <AlertTriangle className="w-6 h-6 text-orange-600 dark:text-orange-400" />
      case 'high_risk':
        return <XCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
      default:
        return <Shield className="w-6 h-6" />
    }
  }

  const getSimilarityColor = (similarity) => {
    if (similarity >= 0.9) return 'text-red-600 dark:text-red-400'
    if (similarity >= 0.7) return 'text-orange-600 dark:text-orange-400'
    if (similarity >= 0.5) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-green-600 dark:text-green-400'
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
          <Shield className="w-8 h-8" />
          Détecteur de Plagiat
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Vérifiez vos documents contre le plagiat en comparant avec la base de données
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
              placeholder="Collez votre texte ici pour vérifier le plagiat..."
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       resize-none min-h-[200px]"
            />
            <button
              onClick={handleTextCheck}
              disabled={loading || !text.trim()}
              className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg 
                       transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Vérification en cours...
                </>
              ) : (
                <>
                  <FileCheck className="w-5 h-5" />
                  Vérifier le Plagiat
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
                <span>Vérification en cours...</span>
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
            {/* Summary Card */}
            <div className={`bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border-2 ${
              results.summary.status === 'clean' ? 'border-green-200 dark:border-green-800' :
              results.summary.status === 'low_risk' ? 'border-yellow-200 dark:border-yellow-800' :
              results.summary.status === 'medium_risk' ? 'border-orange-200 dark:border-orange-800' :
              'border-red-200 dark:border-red-800'
            }`}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {getStatusIcon(results.summary.status)}
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                      Résultat de la Vérification
                    </h2>
                    <p className={`text-sm ${getStatusColor(results.summary.status)}`}>
                      {results.summary.message}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-3xl font-bold ${getSimilarityColor(results.overall_similarity)}`}>
                    {results.summary.similarity_percentage.toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Similarité</div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-4">
                <div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {results.total_documents_checked}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Documents vérifiés</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {results.matches.length}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Correspondances</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {results.similarity_breakdown.exact_matches}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Correspondances exactes</div>
                </div>
              </div>
            </div>

            {/* Matches */}
            {results.matches.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Documents Similaires
                </h3>
                <div className="space-y-4">
                  {results.matches.map((match, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <FileText className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                            <span className="font-medium text-gray-900 dark:text-white">
                              {match.document_name}
                            </span>
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            Document ID: {match.document_id} • {match.document_length} caractères
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`text-xl font-bold ${getSimilarityColor(match.similarity)}`}>
                            {(match.similarity * 100).toFixed(1)}%
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">Similarité</div>
                        </div>
                      </div>

                      {/* Similarity Breakdown */}
                      <div className="grid grid-cols-3 gap-2 mb-3 text-xs">
                        <div>
                          <div className="text-gray-500 dark:text-gray-400">N-gram</div>
                          <div className="font-medium text-gray-700 dark:text-gray-300">
                            {(match.ngram_similarity * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-gray-500 dark:text-gray-400">Sémantique</div>
                          <div className="font-medium text-gray-700 dark:text-gray-300">
                            {(match.semantic_similarity * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-gray-500 dark:text-gray-400">Séquence</div>
                          <div className="font-medium text-gray-700 dark:text-gray-300">
                            {(match.sequence_similarity * 100).toFixed(1)}%
                          </div>
                        </div>
                      </div>

                      {/* Similar Sections */}
                      {match.similar_sections && match.similar_sections.length > 0 && (
                        <div className="mt-3 space-y-2">
                          <div className="text-xs font-medium text-gray-700 dark:text-gray-300">
                            Sections similaires:
                          </div>
                          {match.similar_sections.slice(0, 2).map((section, secIndex) => (
                            <div key={secIndex} className="p-2 bg-gray-50 dark:bg-gray-700 rounded text-xs">
                              <div className="text-gray-600 dark:text-gray-400 mb-1">
                                Similarité: {(section.similarity * 100).toFixed(1)}%
                              </div>
                              <div className="text-gray-800 dark:text-gray-200 italic">
                                "{section.source_text.substring(0, 150)}..."
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* No Matches */}
            {results.matches.length === 0 && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6 text-center">
                <CheckCircle className="w-12 h-12 text-green-600 dark:text-green-400 mx-auto mb-3" />
                <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-2">
                  Aucun Plagiat Détecté
                </h3>
                <p className="text-green-700 dark:text-green-300">
                  Votre document semble original. Aucune similarité significative n'a été trouvée.
                </p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default PlagiarismChecker

