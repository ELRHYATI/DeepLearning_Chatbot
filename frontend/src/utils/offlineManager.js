/**
 * Gestionnaire de mode hors-ligne
 */
class OfflineManager {
  constructor() {
    this.queue = []
    this.isOnline = navigator.onLine
    this.listeners = []
    
    // Écouter les changements de statut réseau
    window.addEventListener('online', () => {
      this.isOnline = true
      this.notifyListeners(true)
      this.processQueue()
    })
    
    window.addEventListener('offline', () => {
      this.isOnline = false
      this.notifyListeners(false)
    })
  }

  addListener(callback) {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback)
    }
  }

  notifyListeners(isOnline) {
    this.listeners.forEach(callback => callback(isOnline))
  }

  isConnected() {
    return this.isOnline
  }

  /**
   * Ajouter une requête à la queue pour traitement ultérieur
   */
  queueRequest(request) {
    const requestData = {
      id: `offline_${Date.now()}_${Math.random()}`,
      ...request,
      timestamp: Date.now()
    }
    
    this.queue.push(requestData)
    this.saveQueue()
    
    return requestData.id
  }

  /**
   * Traiter la queue de requêtes en attente
   */
  async processQueue() {
    if (!this.isOnline || this.queue.length === 0) {
      return
    }

    const requests = [...this.queue]
    this.queue = []
    this.saveQueue()

    for (const request of requests) {
      try {
        await this.executeRequest(request)
      } catch (error) {
        console.error('Error processing queued request:', error)
        // Remettre dans la queue si échec
        this.queue.push(request)
      }
    }

    this.saveQueue()
  }

  /**
   * Exécuter une requête
   */
  async executeRequest(request) {
    const { url, options, onSuccess, onError } = request

    try {
      const response = await fetch(url, options)
      
      if (response.ok) {
        const data = await response.json()
        if (onSuccess) {
          onSuccess(data)
        }
      } else {
        throw new Error(`Request failed: ${response.status}`)
      }
    } catch (error) {
      if (onError) {
        onError(error)
      }
      throw error
    }
  }

  /**
   * Sauvegarder la queue dans localStorage
   */
  saveQueue() {
    try {
      localStorage.setItem('offline_queue', JSON.stringify(this.queue))
    } catch (error) {
      console.error('Error saving offline queue:', error)
    }
  }

  /**
   * Charger la queue depuis localStorage
   */
  loadQueue() {
    try {
      const saved = localStorage.getItem('offline_queue')
      if (saved) {
        this.queue = JSON.parse(saved)
      }
    } catch (error) {
      console.error('Error loading offline queue:', error)
      this.queue = []
    }
  }

  /**
   * Obtenir les statistiques de la queue
   */
  getQueueStats() {
    return {
      count: this.queue.length,
      oldest: this.queue.length > 0 ? this.queue[0].timestamp : null
    }
  }

  /**
   * Vider la queue
   */
  clearQueue() {
    this.queue = []
    this.saveQueue()
  }
}

// Instance singleton
export const offlineManager = new OfflineManager()

// Charger la queue au démarrage
offlineManager.loadQueue()

// Traiter la queue si en ligne
if (offlineManager.isConnected()) {
  offlineManager.processQueue()
}

