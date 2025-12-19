import { useState, useEffect } from 'react'
import { Upload, FileText, Trash2, CheckCircle, XCircle, Shield, Loader2 } from 'lucide-react'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'

const DocumentManager = () => {
  const [documents, setDocuments] = useState([])
  const [uploading, setUploading] = useState(false)
  const [checkingPlagiarism, setCheckingPlagiarism] = useState(null)
  const [plagiarismResults, setPlagiarismResults] = useState(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      const response = await fetch('/api/documents/', {
        headers
      })
      if (response.ok) {
        const data = await response.json()
        setDocuments(data)
      }
    } catch (error) {
      console.error('Error loading documents:', error)
    }
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setUploading(true)
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        headers,
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setDocuments([data, ...documents])
      } else {
        alert('Erreur lors du téléchargement du document')
      }
    } catch (error) {
      console.error('Error uploading document:', error)
      alert('Erreur lors du téléchargement du document')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const deleteDocument = async (id) => {
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      const response = await fetch(`/api/documents/${id}`, {
        method: 'DELETE',
        headers
      })

      if (response.ok) {
        setDocuments(documents.filter(doc => doc.id !== id))
      }
    } catch (error) {
      console.error('Error deleting document:', error)
    }
  }

  const checkPlagiarism = async (documentId) => {
    setCheckingPlagiarism(documentId)
    setPlagiarismResults(null)
    
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
      const response = await fetch(`/api/plagiarism/check-document/${documentId}?min_similarity=0.7`, {
        headers
      })

      if (response.ok) {
        const data = await response.json()
        setPlagiarismResults({ documentId, ...data })
      } else {
        alert('Erreur lors de la vérification du plagiat')
      }
    } catch (error) {
      console.error('Error checking plagiarism:', error)
      alert('Erreur de connexion')
    } finally {
      setCheckingPlagiarism(null)
    }
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      <div className="border-b border-gray-200 dark:border-gray-700 p-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Gestion des Documents
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Téléchargez des documents pour améliorer les réponses du chatbot
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {/* Upload Area */}
        <div className="mb-6">
          <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Télécharger un document (PDF, TXT, DOCX)
          </label>
          <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center hover:border-primary-500 transition-colors">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".pdf,.txt,.docx"
              onChange={handleUpload}
              disabled={uploading}
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer flex flex-col items-center"
            >
              <Upload className="w-12 h-12 text-gray-400 mb-4" />
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {uploading ? 'Téléchargement...' : 'Cliquez pour télécharger ou glissez-déposez'}
              </p>
            </label>
          </div>
        </div>

        {/* Documents List */}
        <div className="space-y-3">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center gap-3 flex-1">
                <FileText className="w-8 h-8 text-primary-600" />
                <div className="flex-1">
                  <p className="font-medium text-gray-900 dark:text-white">
                    {doc.filename}
                  </p>
                  <div className="flex items-center gap-4 mt-1">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {doc.file_type.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {format(new Date(doc.uploaded_at), 'PPp', { locale: fr })}
                    </span>
                    {doc.processed ? (
                      <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                        <CheckCircle className="w-3 h-3" />
                        Traité
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-yellow-600 dark:text-yellow-400">
                        <XCircle className="w-3 h-3" />
                        En attente
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => checkPlagiarism(doc.id)}
                  disabled={checkingPlagiarism === doc.id || !doc.processed}
                  className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Vérifier le plagiat"
                >
                  {checkingPlagiarism === doc.id ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Shield className="w-5 h-5" />
                  )}
                </button>
                <button
                  onClick={() => deleteDocument(doc.id)}
                  className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded-lg transition-colors"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
          {documents.length === 0 && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>Aucun document téléchargé</p>
              <p className="text-sm">Téléchargez des documents pour améliorer les réponses</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DocumentManager

