import { useState, useEffect } from 'react'
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts'
import { 
  MessageSquare, FileText, Users, TrendingUp, Activity, 
  Calendar, Clock, Share2, Loader2 
} from 'lucide-react'
import { format, parseISO, subDays } from 'date-fns'
import { fr } from 'date-fns/locale'
import { useTheme } from '../contexts/ThemeContext'

const COLORS = {
  general: '#3b82f6',
  grammar: '#10b981',
  qa: '#f59e0b',
  reformulation: '#ef4444',
  user: '#6366f1',
  assistant: '#8b5cf6'
}

const Dashboard = () => {
  const { isDark } = useTheme()
  const [stats, setStats] = useState(null)
  const [trends, setTrends] = useState(null)
  const [performance, setPerformance] = useState(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    fetchStatistics()
  }, [days])

  const fetchStatistics = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

      const [statsRes, trendsRes, perfRes] = await Promise.all([
        fetch(`/api/statistics/stats?days=${days}`, { headers }),
        fetch(`/api/statistics/stats/trends?days=${days}`, { headers }),
        fetch(`/api/statistics/stats/performance`, { headers })
      ])

      if (statsRes.ok) {
        const statsData = await statsRes.json()
        setStats(statsData)
      }

      if (trendsRes.ok) {
        const trendsData = await trendsRes.json()
        setTrends(trendsData)
      }

      if (perfRes.ok) {
        const perfData = await perfRes.json()
        setPerformance(perfData)
      }
    } catch (error) {
      console.error('Error fetching statistics:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    try {
      return format(parseISO(dateString), 'dd MMM', { locale: fr })
    } catch {
      return dateString
    }
  }

  const prepareDailyData = () => {
    if (!stats?.daily_messages || !stats?.daily_sessions) return []
    
    const messageMap = new Map(stats.daily_messages.map(d => [d.date, d.count]))
    const sessionMap = new Map(stats.daily_sessions.map(d => [d.date, d.count]))
    
    const allDates = new Set([...messageMap.keys(), ...sessionMap.keys()])
    return Array.from(allDates)
      .sort()
      .map(date => ({
        date: formatDate(date),
        messages: messageMap.get(date) || 0,
        sessions: sessionMap.get(date) || 0
      }))
  }

  const prepareModuleData = () => {
    if (!stats?.module_usage) return []
    return Object.entries(stats.module_usage).map(([name, value]) => ({
      name: name === 'general' ? 'Général' : 
            name === 'grammar' ? 'Grammaire' :
            name === 'qa' ? 'Questions' : 'Reformulation',
      value,
      color: COLORS[name] || '#6b7280'
    }))
  }

  const prepareRoleData = () => {
    if (!stats?.role_distribution) return []
    return Object.entries(stats.role_distribution).map(([name, value]) => ({
      name: name === 'user' ? 'Utilisateur' : 'Assistant',
      value,
      color: COLORS[name] || '#6b7280'
    }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500 dark:text-gray-400">Aucune donnée disponible</p>
      </div>
    )
  }

  const dailyData = prepareDailyData()
  const moduleData = prepareModuleData()
  const roleData = prepareRoleData()

  return (
    <div className="h-full overflow-y-auto p-6 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Tableau de Bord
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Statistiques d'utilisation et progression
          </p>
        </div>

        {/* Period Selector */}
        <div className="mb-6 flex gap-2">
          {[7, 30, 90, 365].map(period => (
            <button
              key={period}
              onClick={() => setDays(period)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                days === period
                  ? 'bg-primary-600 text-white'
                  : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              {period} jours
            </button>
          ))}
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricCard
            icon={<MessageSquare className="w-6 h-6" />}
            title="Messages"
            value={stats.total_messages || 0}
            subtitle={`${stats.recent_activity || 0} cette semaine`}
            color="blue"
          />
          <MetricCard
            icon={<FileText className="w-6 h-6" />}
            title="Conversations"
            value={stats.total_sessions || 0}
            subtitle={`${performance?.active_sessions || 0} actives`}
            color="green"
          />
          <MetricCard
            icon={<Share2 className="w-6 h-6" />}
            title="Partagées"
            value={stats.shared_sessions || 0}
            subtitle="Sessions publiques"
            color="purple"
          />
          <MetricCard
            icon={<Activity className="w-6 h-6" />}
            title="Documents"
            value={stats.total_documents || 0}
            subtitle="Fichiers uploadés"
            color="orange"
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Daily Activity */}
          <ChartCard title="Activité Quotidienne">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyData}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                <XAxis 
                  dataKey="date" 
                  stroke={isDark ? '#9ca3af' : '#6b7280'}
                  tick={{ fill: isDark ? '#9ca3af' : '#6b7280' }}
                />
                <YAxis 
                  stroke={isDark ? '#9ca3af' : '#6b7280'}
                  tick={{ fill: isDark ? '#9ca3af' : '#6b7280' }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: isDark ? '#1f2937' : '#fff',
                    border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                    borderRadius: '8px'
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="messages" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name="Messages"
                  dot={{ r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="sessions" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  name="Conversations"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Module Usage */}
          <ChartCard title="Utilisation par Module">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={moduleData}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                <XAxis 
                  dataKey="name" 
                  stroke={isDark ? '#9ca3af' : '#6b7280'}
                  tick={{ fill: isDark ? '#9ca3af' : '#6b7280' }}
                />
                <YAxis 
                  stroke={isDark ? '#9ca3af' : '#6b7280'}
                  tick={{ fill: isDark ? '#9ca3af' : '#6b7280' }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: isDark ? '#1f2937' : '#fff',
                    border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="value" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Module Distribution */}
          <ChartCard title="Répartition par Module">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={moduleData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {moduleData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: isDark ? '#1f2937' : '#fff',
                    border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                    borderRadius: '8px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Role Distribution */}
          <ChartCard title="Répartition Utilisateur/Assistant">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={roleData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {roleData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: isDark ? '#1f2937' : '#fff',
                    border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                    borderRadius: '8px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Performance Metrics */}
        {performance && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Métriques de Performance
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-5 h-5 text-primary-600" />
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Module le plus utilisé</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {performance.most_used_module === 'general' ? 'Général' :
                     performance.most_used_module === 'grammar' ? 'Grammaire' :
                     performance.most_used_module === 'qa' ? 'Questions' :
                     performance.most_used_module === 'reformulation' ? 'Reformulation' : 'N/A'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500">
                    {performance.most_used_module_count} messages
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <MessageSquare className="w-5 h-5 text-green-600" />
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Messages par conversation</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {performance.average_messages_per_session || 0}
                  </p>
                </div>
              </div>
              {stats.average_response_time_seconds && (
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-purple-600" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Temps moyen de réponse</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {Math.round(stats.average_response_time_seconds)}s
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const MetricCard = ({ icon, title, value, subtitle, color }) => {
  const { isDark } = useTheme()
  const colorClasses = {
    blue: 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    green: 'bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    purple: 'bg-purple-100 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
    orange: 'bg-orange-100 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400'
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow p-6 ${isDark ? 'border border-gray-700' : ''}`}>
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
      <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">{title}</h3>
      <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{value}</p>
      <p className="text-xs text-gray-500 dark:text-gray-500">{subtitle}</p>
    </div>
  )
}

const ChartCard = ({ title, children }) => {
  const { isDark } = useTheme()
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow p-6 ${isDark ? 'border border-gray-700' : ''}`}>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      {children}
    </div>
  )
}

export default Dashboard

