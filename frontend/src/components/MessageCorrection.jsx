import { useState } from 'react'
import { Edit2, Check, X, Save, Loader2, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const MessageCorrection = ({ message, onSave, onCancel }) => {
  const [isEditing, setIsEditing] = useState(false)
  const [correctedContent, setCorrectedContent] = useState(message.content)
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleStartEdit = () => {
    setIsEditing(true)
    setCorrectedContent(message.content)
    setNotes('')
  }

  const handleCancel = () => {
    setIsEditing(false)
    setCorrectedContent(message.content)
    setNotes('')
    if (onCancel) onCancel()
  }

  const handleSave = async () => {
    if (!message.id || typeof message.id !== 'number') {
      console.warn('Cannot save correction: invalid message ID')
      return
    }

    if (correctedContent.trim() === message.content.trim()) {
      // No changes made
      setIsEditing(false)
      return
    }

    setSaving(true)

    try {
      const token = localStorage.getItem('token')
      const headers = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('/api/learning/corrections', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message_id: message.id,
          corrected_content: correctedContent,
          correction_notes: notes || undefined
        })
      })

      if (response.ok) {
        setSaved(true)
        setIsEditing(false)
        if (onSave) {
          onSave({
            ...message,
            content: correctedContent,
            corrected: true
          })
        }
        
        // Show success message
        setTimeout(() => {
          setSaved(false)
        }, 3000)
      } else {
        const error = await response.json().catch(() => ({ detail: 'Erreur lors de la sauvegarde' }))
        alert(error.detail || 'Erreur lors de la sauvegarde de la correction')
      }
    } catch (error) {
      console.error('Error saving correction:', error)
      alert('Erreur de connexion lors de la sauvegarde')
    } finally {
      setSaving(false)
    }
  }

  if (!isEditing) {
    return (
      <div className="flex items-center gap-2 mt-2">
        <button
          onClick={handleStartEdit}
          className="flex items-center gap-1 px-2 py-1 text-xs text-gray-500 hover:text-blue-500 transition-colors rounded hover:bg-gray-100 dark:hover:bg-gray-800"
          title="Corriger cette réponse pour améliorer l'IA"
        >
          <Edit2 className="w-3 h-3" />
          <span>Corriger</span>
        </button>
        {saved && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400"
          >
            <Check className="w-3 h-3" />
            <span>Correction enregistrée</span>
          </motion.div>
        )}
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="mt-3 p-4 border border-blue-200 dark:border-blue-800 rounded-lg bg-blue-50 dark:bg-blue-900/20"
    >
      <div className="flex items-start gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
            Aidez l'IA à apprendre en corrigeant cette réponse
          </p>
          <p className="text-xs text-blue-700 dark:text-blue-300">
            Votre correction sera utilisée pour améliorer les futures réponses
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Réponse corrigée
          </label>
          <textarea
            value={correctedContent}
            onChange={(e) => setCorrectedContent(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg 
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     resize-none min-h-[100px]"
            placeholder="Modifiez la réponse de l'IA..."
            autoFocus
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Notes (optionnel)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg 
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     resize-none min-h-[60px]"
            placeholder="Expliquez pourquoi vous avez fait cette correction..."
          />
        </div>

        <div className="flex items-center justify-end gap-2">
          <button
            onClick={handleCancel}
            disabled={saving}
            className="px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 
                     hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
          >
            <X className="w-4 h-4" />
            Annuler
          </button>
          <button
            onClick={handleSave}
            disabled={saving || correctedContent.trim() === message.content.trim()}
            className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white 
                     rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center gap-1"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Enregistrement...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Enregistrer la correction
              </>
            )}
          </button>
        </div>
      </div>
    </motion.div>
  )
}

export default MessageCorrection

