/**
 * Hook pour gérer le mode hors-ligne
 */
import { useState, useEffect } from 'react'
import { offlineManager } from '../utils/offlineManager'

export const useOffline = () => {
  const [isOnline, setIsOnline] = useState(offlineManager.isConnected())
  const [queueStats, setQueueStats] = useState(offlineManager.getQueueStats())

  useEffect(() => {
    const unsubscribe = offlineManager.addListener((online) => {
      setIsOnline(online)
      setQueueStats(offlineManager.getQueueStats())
    })

    // Mettre à jour les stats périodiquement
    const interval = setInterval(() => {
      setQueueStats(offlineManager.getQueueStats())
    }, 1000)

    return () => {
      unsubscribe()
      clearInterval(interval)
    }
  }, [])

  const queueRequest = (request) => {
    const id = offlineManager.queueRequest(request)
    setQueueStats(offlineManager.getQueueStats())
    return id
  }

  const clearQueue = () => {
    offlineManager.clearQueue()
    setQueueStats(offlineManager.getQueueStats())
  }

  return {
    isOnline,
    queueStats,
    queueRequest,
    clearQueue
  }
}

