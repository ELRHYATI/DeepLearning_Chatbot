/**
 * Composant amélioré pour le drag & drop
 */
import { useState, useRef, useCallback } from 'react'
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react'

export const EnhancedDragDrop = ({ 
  onFileSelect, 
  acceptedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  maxSize = 10 * 1024 * 1024, // 10MB
  className = '',
  disabled = false,
  isDragging = false, // Prop pour contrôler la visibilité depuis le parent
  onDragStateChange = null // Callback pour notifier le parent du changement d'état
}) => {
  const [dragActive, setDragActive] = useState(false)
  const [dragCounter, setDragCounter] = useState(0)
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)
  
  // Utiliser isDragging du parent si fourni
  const isVisible = isDragging || dragActive || preview

  const validateFile = useCallback((file) => {
    setError(null)

    // Vérifier le type
    if (!acceptedTypes.includes(file.type)) {
      const types = acceptedTypes.map(t => {
        if (t.includes('pdf')) return 'PDF'
        if (t.includes('text')) return 'TXT'
        if (t.includes('wordprocessingml')) return 'DOCX'
        return t
      }).join(', ')
      
      setError(`Type de fichier non supporté. Types acceptés: ${types}`)
      return false
    }

    // Vérifier la taille
    if (file.size > maxSize) {
      const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(0)
      setError(`Le fichier est trop volumineux. Taille maximale: ${maxSizeMB}MB`)
      return false
    }

    return true
  }, [acceptedTypes, maxSize])

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragCounter(prev => prev + 1)
      if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
        const newDragActive = true
        setDragActive(newDragActive)
        if (onDragStateChange) {
          onDragStateChange(newDragActive)
        }
      }
    } else if (e.type === 'dragleave') {
      setDragCounter(prev => {
        const newCount = prev - 1
        if (newCount === 0) {
          setDragActive(false)
          if (onDragStateChange) {
            onDragStateChange(false)
          }
        }
        return newCount
      })
    }
  }, [onDragStateChange])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    setDragCounter(0)
    if (onDragStateChange) {
      onDragStateChange(false)
    }

    if (disabled) return

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0]
      
      if (validateFile(file)) {
        setPreview({
          name: file.name,
          size: file.size,
          type: file.type
        })
        onFileSelect(file)
      }
    }
  }, [disabled, validateFile, onFileSelect, onDragStateChange])

  const handleFileInput = useCallback((e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0]
      
      if (validateFile(file)) {
        setPreview({
          name: file.name,
          size: file.size,
          type: file.type
        })
        onFileSelect(file)
      }
    }
  }, [validateFile, onFileSelect])

  const clearPreview = useCallback(() => {
    setPreview(null)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [])

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getFileIcon = (type) => {
    if (type.includes('pdf')) return '📄'
    if (type.includes('text')) return '📝'
    if (type.includes('wordprocessingml')) return '📘'
    return '📎'
  }

  // Ne pas afficher le composant si pas de drag actif et pas de preview
  if (!isVisible) {
    return null
  }

  return (
    <div className={className}>
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-lg p-6 transition-all duration-200
          ${dragActive 
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 scale-[1.02]' 
            : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-600'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedTypes.join(',')}
          onChange={handleFileInput}
          className="hidden"
          disabled={disabled}
        />

        {!preview ? (
          <div 
            className="flex flex-col items-center justify-center text-center"
            onClick={() => !disabled && fileInputRef.current?.click()}
          >
            <div className={`
              w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-all
              ${dragActive 
                ? 'bg-primary-500 text-white scale-110' 
                : 'bg-gray-100 dark:bg-gray-800 text-gray-400'
              }
            `}>
              <Upload className={`w-8 h-8 ${dragActive ? 'animate-bounce' : ''}`} />
            </div>
            
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {dragActive ? 'Déposez le fichier ici' : 'Glissez-déposez un fichier'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              ou <span className="text-primary-600 dark:text-primary-400 font-medium">cliquez pour parcourir</span>
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
              PDF, TXT, DOCX (max {formatFileSize(maxSize)})
            </p>
          </div>
        ) : (
          <div className="flex items-center gap-4">
            <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-2xl">
              {getFileIcon(preview.type)}
            </div>
            
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                {preview.name}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {formatFileSize(preview.size)}
              </p>
            </div>

            <button
              onClick={clearPreview}
              className="flex-shrink-0 p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              aria-label="Supprimer le fichier"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        {/* Overlay pour le drag actif */}
        {dragActive && (
          <div className="absolute inset-0 bg-primary-500/10 dark:bg-primary-500/20 rounded-lg flex items-center justify-center pointer-events-none">
            <div className="flex flex-col items-center gap-2 text-primary-600 dark:text-primary-400">
              <Upload className="w-8 h-8 animate-bounce" />
              <p className="text-sm font-medium">Déposez ici</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

