import React from 'react'
import { AlertCircle } from 'lucide-react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    this.setState({
      error,
      errorInfo
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-theme-bg-primary p-4">
          <div className="max-w-2xl w-full bg-theme-bg-secondary rounded-2xl p-8 border border-theme-accent-error/20">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="w-8 h-8 text-theme-accent-error" />
              <h1 className="text-2xl font-bold text-theme-text-primary">
                Une erreur est survenue
              </h1>
            </div>
            <p className="text-theme-text-secondary mb-4">
              Désolé, une erreur inattendue s'est produite. Veuillez rafraîchir la page.
            </p>
            {this.state.error && (
              <details className="mt-4 p-4 bg-theme-bg-tertiary rounded-lg">
                <summary className="cursor-pointer text-theme-text-secondary mb-2">
                  Détails de l'erreur
                </summary>
                <pre className="text-xs text-theme-text-secondary overflow-auto">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              className="mt-6 px-6 py-3 bg-theme-accent-primary text-white rounded-xl hover:opacity-90 transition-opacity"
            >
              Rafraîchir la page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

