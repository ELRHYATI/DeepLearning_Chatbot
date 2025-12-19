import { motion } from 'framer-motion'
import { Send, Loader2, CheckCircle2, Plus, Mic, Globe, Cpu, Paperclip, X } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useState } from 'react'

export const AnimatedInput = ({
  value,
  onChange,
  onSubmit,
  placeholder = "Ask anything.",
  disabled = false,
  loading = false,
  success = false,
  maxLength = 2000,
  onFileClick,
  onMicClick,
  onGlobeClick,
  webSearchActive = false,
  onCpuClick,
  onSelectionChange,
  onCancel
}) => {
  const { isDark } = useTheme()
  const [focused, setFocused] = useState(false)
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (value.trim() && !disabled && !loading) {
      onSubmit()
    }
  }
  
  return (
    <form onSubmit={handleSubmit} className="relative w-full">
      <motion.div
        className={`relative flex items-center gap-2 px-3 py-2 rounded-2xl transition-all backdrop-blur-xl ${
          isDark 
            ? 'border border-white/10' 
            : 'border border-gray-300/30'
        }`}
        style={{
          background: isDark 
            ? 'linear-gradient(180deg, rgba(10, 14, 23, 0.8) 0%, rgba(5, 8, 16, 0.8) 100%)'
            : 'rgba(248, 250, 252, 0.8)',
          boxShadow: focused
            ? isDark
              ? '0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
              : '0 8px 32px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.8)'
            : isDark
              ? '0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.05)'
              : '0 4px 20px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.05)'
        }}
        animate={{
          scale: 1,
          y: focused ? -2 : 0,
        }}
        transition={{ duration: 0.2 }}
      >
        {/* Text input */}
        <textarea
          value={value}
          onChange={(e) => {
            onChange(e.target.value)
            // Track cursor position for suggestions
            if (onSelectionChange) {
              onSelectionChange(e)
            }
          }}
          onSelect={(e) => {
            // Track cursor position
            if (onSelectionChange) {
              onSelectionChange(e)
            }
          }}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onKeyDown={(e) => {
            // Tab key - handled by SuggestionDropdown to accept suggestions
            if (e.key === 'Tab') {
              // Let SuggestionDropdown handle Tab
              return
            }
            // Enter key - send message (Shift+Enter for new line)
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              if (value.trim() && !disabled && !loading) {
                handleSubmit(e)
              }
            }
            // Arrow keys - handled by SuggestionDropdown for navigation
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
              // Let SuggestionDropdown handle these
              return
            }
          }}
          placeholder={placeholder}
          disabled={disabled || loading}
          maxLength={maxLength}
          rows={1}
          className={`flex-1 resize-none outline-none bg-transparent ${
            isDark ? 'text-gray-100' : 'text-gray-900'
          } placeholder:${isDark ? 'text-gray-400' : 'text-gray-500'} text-sm`}
          style={{
            minHeight: '20px',
            maxHeight: '100px',
          }}
          onInput={(e) => {
            e.target.style.height = 'auto'
            e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`
          }}
        />
        
        {/* Right side buttons */}
        <div className="flex items-center gap-1.5">
          {/* Globe button */}
          {onGlobeClick && (
            <motion.button
              type="button"
              onClick={onGlobeClick}
              disabled={disabled || loading}
              className={`flex-shrink-0 p-1.5 rounded-lg transition-all border ${
                webSearchActive
                  ? isDark
                    ? 'text-teal-400 border-teal-500/50 bg-teal-500/10 hover:bg-teal-500/15'
                    : 'text-teal-600 border-teal-300 bg-teal-50 hover:bg-teal-100'
                  : isDark 
                    ? 'text-gray-300 hover:bg-gray-700 border-transparent'
                    : 'text-gray-600 hover:bg-gray-200 border-transparent'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              title={webSearchActive ? "Web Search Active" : "Enable Web Search"}
            >
              <Globe className="w-4 h-4" />
            </motion.button>
          )}

          {/* CPU/AI button */}
          {onCpuClick && (
            <div className="relative">
              <motion.button
                type="button"
                onClick={onCpuClick}
                disabled={disabled || loading}
                className={`flex-shrink-0 p-1.5 rounded-lg transition-all border ${
                  isDark 
                    ? 'text-teal-400 border-teal-500/50 hover:bg-teal-500/10' 
                    : 'text-teal-600 border-teal-300 hover:bg-teal-50'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                title="AI Mode"
              >
                <Cpu className="w-4 h-4" />
              </motion.button>
            </div>
          )}

          {/* File attachment button */}
          {onFileClick && (
            <motion.button
              type="button"
              onClick={onFileClick}
              disabled={disabled || loading}
              className={`flex-shrink-0 p-1.5 rounded-lg transition-all ${
                isDark 
                  ? 'text-gray-300 hover:bg-gray-700' 
                  : 'text-gray-600 hover:bg-gray-200'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              title="Attacher un fichier"
            >
              <Paperclip className="w-4 h-4" />
            </motion.button>
          )}
          
          {/* Microphone button */}
          {onMicClick && (
            <motion.button
              type="button"
              onClick={onMicClick}
              disabled={disabled || loading}
              className={`flex-shrink-0 p-1.5 rounded-lg transition-all ${
                isDark 
                  ? 'text-gray-300 hover:bg-gray-700' 
                  : 'text-gray-600 hover:bg-gray-200'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              title="Enregistrement vocal"
            >
              <Mic className="w-4 h-4" />
            </motion.button>
          )}
          
          {/* Stop button (show when loading) */}
          {loading && onCancel && (
            <motion.button
              type="button"
              onClick={onCancel}
              className="relative flex-shrink-0 p-1.5 rounded-lg transition-all overflow-hidden flex items-center justify-center"
              style={{
                background: isDark 
                  ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.2) 100%)'
                  : 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.15) 100%)',
                border: isDark 
                  ? '1px solid rgba(239, 68, 68, 0.3)'
                  : '1px solid rgba(239, 68, 68, 0.2)',
                boxShadow: isDark
                  ? '0 0 0 1px rgba(0, 0, 0, 0.2), inset 0 0 10px rgba(239, 68, 68, 0.08)'
                  : '0 0 0 1px rgba(0, 0, 0, 0.08), inset 0 0 10px rgba(239, 68, 68, 0.04)'
              }}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              title="Arrêter la génération"
            >
              {/* Concentric circles background effect - compact */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div 
                  className="absolute rounded-full"
                  style={{
                    width: '20px',
                    height: '20px',
                    background: isDark ? 'rgba(239, 68, 68, 0.08)' : 'rgba(239, 68, 68, 0.06)',
                    border: isDark ? '1px solid rgba(239, 68, 68, 0.15)' : '1px solid rgba(239, 68, 68, 0.12)'
                  }}
                />
                <div 
                  className="absolute rounded-full"
                  style={{
                    width: '14px',
                    height: '14px',
                    background: isDark ? 'rgba(239, 68, 68, 0.12)' : 'rgba(239, 68, 68, 0.1)',
                    border: isDark ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(239, 68, 68, 0.15)'
                  }}
                />
              </div>
              
              {/* White square stop icon - compact */}
              <div 
                className="relative z-10 rounded-sm"
                style={{
                  width: '6px',
                  height: '6px',
                  background: '#FFFFFF',
                  boxShadow: '0 0 2px rgba(0, 0, 0, 0.25)'
                }}
              />
            </motion.button>
          )}
          
          {/* Send button (only show when there's text and not loading) */}
          {value.trim() && !loading && (
            <motion.button
              type="submit"
              disabled={disabled}
              className={`relative flex-shrink-0 p-2 rounded-lg transition-all overflow-hidden ${
                isDark
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white'
                  : 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {success ? (
                <CheckCircle2 className="w-5 h-5" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </motion.button>
          )}
        </div>
      </motion.div>
    </form>
  )
}

