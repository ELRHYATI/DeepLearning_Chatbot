/**
 * Hook pour les mises à jour optimistes
 */
import { useState, useCallback } from 'react'

export const useOptimisticUpdate = (initialData, updateFn) => {
  const [data, setData] = useState(initialData)
  const [pendingUpdates, setPendingUpdates] = useState(new Map())

  const optimisticUpdate = useCallback(async (optimisticData, updatePromise) => {
    const tempId = `temp_${Date.now()}_${Math.random()}`
    
    // Mise à jour optimiste immédiate
    setData(prev => {
      if (Array.isArray(prev)) {
        return [...prev, { ...optimisticData, id: tempId, _pending: true }]
      }
      return { ...prev, ...optimisticData, _pending: true }
    })

    // Stocker la promesse de mise à jour
    setPendingUpdates(prev => new Map(prev).set(tempId, updatePromise))

    try {
      // Attendre la réponse du serveur
      const serverData = await updatePromise

      // Remplacer les données optimistes par les données réelles
      setData(prev => {
        if (Array.isArray(prev)) {
          return prev.map(item => 
            item.id === tempId ? { ...serverData, _pending: false } : item
          )
        }
        return { ...prev, ...serverData, _pending: false }
      })

      // Nettoyer
      setPendingUpdates(prev => {
        const next = new Map(prev)
        next.delete(tempId)
        return next
      })

      return serverData
    } catch (error) {
      // En cas d'erreur, annuler la mise à jour optimiste
      setData(prev => {
        if (Array.isArray(prev)) {
          return prev.filter(item => item.id !== tempId)
        }
        return initialData
      })

      setPendingUpdates(prev => {
        const next = new Map(prev)
        next.delete(tempId)
        return next
      })

      throw error
    }
  }, [initialData])

  const rollback = useCallback((tempId) => {
    setData(prev => {
      if (Array.isArray(prev)) {
        return prev.filter(item => item.id !== tempId)
      }
      return initialData
    })
    setPendingUpdates(prev => {
      const next = new Map(prev)
      next.delete(tempId)
      return next
    })
  }, [initialData])

  return {
    data,
    optimisticUpdate,
    rollback,
    pendingUpdates: Array.from(pendingUpdates.keys())
  }
}

