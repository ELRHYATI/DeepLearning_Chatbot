import { useState, useEffect } from 'react'
import { 
  TrendingUp, Brain, Database, Users, BarChart3, 
  Sparkles, ArrowUpRight, ArrowDownRight, Loader2,
  FileDown, RefreshCw, Lightbulb
} from 'lucide-react'
import { motion } from 'framer-motion'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'

const LearningDashboard = () => {
  const { isDark } = useTheme()
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [patterns, setPatterns] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

      const [statsRes, patternsRes] = await Promise.all([
        fetch('/api/learning/stats', { headers }),
        fetch('/api/learning/patterns?limit=10', { headers })
      ])

      if (statsRes.ok) {
        const statsData = await statsRes.json()
        setStats(statsData)
      }

      if (patternsRes.ok) {
        const patternsData = await patternsRes.json()
        setPatterns(patternsData.patterns || [])
      }
    } catch (error) {
      console.error('Error fetching learning data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchData()
    setRefreshing(false)
  }

  const exportTrainingData = async (moduleType) => {
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      
      const response = await fetch(`/api/learning/training-data/${moduleType}?limit=100`, { headers })
      if (response.ok) {
        const data = await response.json()
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `training_data_${moduleType}_${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Error exporting training data:', error)
      alert('Erreur lors de l\'exportation des données')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Tableau de Bord d'Apprentissage
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Visualisez comment l'IA apprend de vos corrections
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Actualiser
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Corrections */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 text-white"
          >
            <div className="flex items-center justify-between mb-4">
              <Database className="w-8 h-8 opacity-80" />
              <ArrowUpRight className="w-5 h-5" />
            </div>
            <div className="text-3xl font-bold mb-1">{stats.total_corrections}</div>
            <div className="text-blue-100 text-sm">Corrections totales</div>
          </motion.div>

          {/* Improvement Rate */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="p-6 rounded-xl bg-gradient-to-br from-green-500 to-green-600 text-white"
          >
            <div className="flex items-center justify-between mb-4">
              <TrendingUp className="w-8 h-8 opacity-80" />
              <ArrowUpRight className="w-5 h-5" />
            </div>
            <div className="text-3xl font-bold mb-1">{stats.improvement_rate.toFixed(1)}%</div>
            <div className="text-green-100 text-sm">Taux d'amélioration</div>
          </motion.div>

          {/* Patterns Learned */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="p-6 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 text-white"
          >
            <div className="flex items-center justify-between mb-4">
              <Brain className="w-8 h-8 opacity-80" />
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="text-3xl font-bold mb-1">{patterns.length}</div>
            <div className="text-purple-100 text-sm">Modèles appris</div>
          </motion.div>

          {/* Corrections by Type */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="p-6 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 text-white"
          >
            <div className="flex items-center justify-between mb-4">
              <BarChart3 className="w-8 h-8 opacity-80" />
              <Users className="w-5 h-5" />
            </div>
            <div className="text-3xl font-bold mb-1">
              {Object.keys(stats.corrections_by_type || {}).length}
            </div>
            <div className="text-orange-100 text-sm">Types de corrections</div>
          </motion.div>
        </div>
      )}

      {/* Corrections by Type */}
      {stats && stats.corrections_by_type && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Corrections par Type
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stats.corrections_by_type).map(([type, count]) => (
              <div key={type} className="p-4 rounded-lg bg-gray-50 dark:bg-gray-700">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1 capitalize">
                  {type === 'grammar' ? 'Grammaire' :
                   type === 'qa' ? 'Questions' :
                   type === 'reformulation' ? 'Reformulation' : type}
                </div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">{count}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Learned Patterns */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Lightbulb className="w-5 h-5" />
            Modèles Appris
          </h2>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {patterns.length} modèles identifiés
          </span>
        </div>
        
        {patterns.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Brain className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Aucun modèle appris pour le moment</p>
            <p className="text-sm mt-2">Commencez à corriger des réponses pour que l'IA apprenne</p>
          </div>
        ) : (
          <div className="space-y-4">
            {patterns.slice(0, 5).map((pattern, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 capitalize">
                        {pattern.module_type}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        Fréquence: {pattern.frequency}x
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Original:</div>
                        <div className="text-sm text-gray-700 dark:text-gray-300 line-through">
                          {pattern.original.substring(0, 150)}
                          {pattern.original.length > 150 && '...'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Corrigé:</div>
                        <div className="text-sm text-gray-900 dark:text-white font-medium">
                          {pattern.corrected.substring(0, 150)}
                          {pattern.corrected.length > 150 && '...'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Training Data Export */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <FileDown className="w-5 h-5" />
          Export des Données d'Entraînement
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Exportez vos corrections au format JSON pour l'entraînement de modèles personnalisés
        </p>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => exportTrainingData('grammar')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <FileDown className="w-4 h-4" />
            Exporter Grammaire
          </button>
          <button
            onClick={() => exportTrainingData('qa')}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <FileDown className="w-4 h-4" />
            Exporter Q&A
          </button>
          <button
            onClick={() => exportTrainingData('reformulation')}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <FileDown className="w-4 h-4" />
            Exporter Reformulation
          </button>
        </div>
      </div>

      {/* Improvement Metrics */}
      {stats && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Métriques d'Amélioration
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                Taux d'amélioration global
              </div>
              <div className="flex items-baseline gap-2">
                <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {stats.improvement_rate.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  des corrections apportent des améliorations significatives
                </div>
              </div>
              <div className="mt-4 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${stats.improvement_rate}%` }}
                  transition={{ duration: 1, delay: 0.5 }}
                  className="h-full bg-gradient-to-r from-green-500 to-green-600"
                />
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                Corrections par utilisateur
              </div>
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                {Object.keys(stats.corrections_by_user || {}).length}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                utilisateurs ont contribué à l'apprentissage
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default LearningDashboard

