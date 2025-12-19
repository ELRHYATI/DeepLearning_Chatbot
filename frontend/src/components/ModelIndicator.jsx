import React from 'react';

/**
 * Component to display which AI model was used for the response
 */
const ModelIndicator = ({ model, modelType, enhancedBy, enhancementType, size = 'small' }) => {
  if (!model) return null;

  const getModelColor = (type) => {
    switch (type) {
      case 'ollama':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'huggingface':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'languagetool':
        return 'bg-green-500/20 text-green-300 border-green-500/30';
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  const getModelIcon = (type) => {
    switch (type) {
      case 'ollama':
        return '🦙'; // Llama emoji for Ollama
      case 'huggingface':
        return '🤗'; // Hugging Face emoji
      case 'languagetool':
        return '✓'; // Checkmark for LanguageTool
      default:
        return '🤖';
    }
  };

  const sizeClasses = {
    small: 'text-xs px-2 py-0.5',
    medium: 'text-sm px-3 py-1',
    large: 'text-base px-4 py-1.5'
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <div className={`inline-flex items-center gap-1.5 rounded-full border ${getModelColor(modelType)} ${sizeClasses[size]}`}>
        <span className="text-[10px]">{getModelIcon(modelType)}</span>
        <span className="font-medium">{model}</span>
      </div>
      {enhancedBy && enhancementType === 'ollama' && (
        <div className={`inline-flex items-center gap-1.5 rounded-full border bg-purple-500/10 text-purple-200 border-purple-500/20 ${sizeClasses[size]}`} title="Amélioré par Ollama">
          <span className="text-[10px]">✨</span>
          <span className="font-medium text-[10px]">Amélioré</span>
        </div>
      )}
    </div>
  );
};

export default ModelIndicator;

