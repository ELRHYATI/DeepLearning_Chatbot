"""
Service for AI-powered suggestions while typing
"""
import re
from typing import List, Dict, Optional
from collections import Counter
import time

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

from app.utils.logger import get_logger
from sqlalchemy.orm import Session
from app.models import Message

logger = get_logger()


class SuggestionsService:
    """Service for generating AI-powered suggestions while typing"""
    
    def __init__(self):
        self.embedding_model = None
        self._load_embedding_model()
        self.common_phrases_cache = {}
        self.suggestion_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def _load_embedding_model(self):
        """Load embedding model for semantic suggestions"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(
                    'paraphrase-multilingual-MiniLM-L12-v2'
                )
                logger.info("Suggestions embedding model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}")
                self.embedding_model = None
    
    def get_grammar_suggestions(self, text: str, cursor_position: int) -> List[Dict]:
        """
        Get grammar suggestions for text at cursor position
        
        Args:
            text: Current text
            cursor_position: Cursor position in text
        
        Returns:
            List of grammar suggestions
        """
        suggestions = []
        
        try:
            # Validate inputs
            if not text or not isinstance(text, str):
                return suggestions
            
            # Normalize text - remove control characters except spaces
            text = ''.join(c for c in text if c.isprintable() or c.isspace())
            
            # Ensure cursor_position is within bounds
            cursor_position = max(0, min(cursor_position, len(text)))
            
            # Get word at cursor
            words = text[:cursor_position].split()
            if not words:
                return suggestions
            
            current_word = words[-1] if words else ""
            previous_words = ' '.join(words[-3:-1]) if len(words) > 1 else ""
        except Exception as e:
            logger.error(f"Error in get_grammar_suggestions input validation: {e}")
            return suggestions
        
        # Common French grammar patterns
        grammar_patterns = {
            # Accent corrections
            'a': ['à', 'â'],
            'ou': ['où'],
            'la': ['là'],
            'ce': ['c\'est', 'ceci', 'cela'],
            # Article corrections
            'le': ['l\'', 'les'],
            'de': ['d\'', 'des', 'du'],
            # Common mistakes
            'et': ['est', 'êtes'],
            'son': ['sont', 'sont'],
            'ses': ['ces', 'c\'est'],
        }
        
        # Check for common patterns
        if current_word.lower() in grammar_patterns:
            for suggestion in grammar_patterns[current_word.lower()]:
                suggestions.append({
                    'type': 'grammar',
                    'text': suggestion,
                    'replacement': current_word,
                    'confidence': 0.7,
                    'explanation': f'Correction grammaticale suggérée'
                })
        
        # Check for missing accents
        accent_corrections = {
            'a': 'à',
            'ou': 'où',
            'la': 'là',
        }
        
        if current_word.lower() in accent_corrections:
            suggestions.append({
                'type': 'grammar',
                'text': accent_corrections[current_word.lower()],
                'replacement': current_word,
                'confidence': 0.8,
                'explanation': 'Accent manquant'
            })
        
        return suggestions[:3]  # Return top 3
    
    def get_completion_suggestions(
        self, 
        text: str, 
        module_type: str,
        db: Session = None
    ) -> List[Dict]:
        """
        Get text completion suggestions based on context
        
        Args:
            text: Current text
            module_type: Type of module (grammar, qa, reformulation, general)
            db: Database session for context
        
        Returns:
            List of completion suggestions
        """
        suggestions = []
        
        if not text or len(text.strip()) < 3:
            return suggestions
        
        # Get last few words for context
        words = text.split()
        if len(words) < 2:
            return suggestions
        
        context = ' '.join(words[-5:])  # Last 5 words
        last_word = words[-1] if words else ""
        
        # Module-specific completions
        if module_type == 'qa':
            qa_completions = [
                'Qu\'est-ce que',
                'Comment',
                'Pourquoi',
                'Quand',
                'Où',
                'Qui',
                'Expliquez',
                'Définissez',
                'Comparez',
                'Analysez'
            ]
            
            # If text starts with a question word, suggest completions
            if any(text.lower().startswith(q.lower()) for q in qa_completions):
                for completion in qa_completions:
                    if completion.lower().startswith(last_word.lower()):
                        suggestions.append({
                            'type': 'completion',
                            'text': completion,
                            'confidence': 0.6,
                            'explanation': 'Suggestion de question'
                        })
        
        # Common French phrases
        common_phrases = {
            'je': ['je suis', 'je vais', 'je peux', 'je dois'],
            'il': ['il est', 'il a', 'il faut', 'il y a'],
            'nous': ['nous sommes', 'nous avons', 'nous devons'],
            'vous': ['vous êtes', 'vous avez', 'vous pouvez'],
            'c\'est': ['c\'est un', 'c\'est une', 'c\'est le', 'c\'est la'],
            'dans': ['dans le', 'dans la', 'dans les', 'dans un'],
            'pour': ['pour le', 'pour la', 'pour les', 'pour un'],
            'avec': ['avec le', 'avec la', 'avec les', 'avec un'],
        }
        
        if last_word.lower() in common_phrases:
            for phrase in common_phrases[last_word.lower()]:
                if phrase.startswith(last_word.lower()):
                    suggestions.append({
                        'type': 'completion',
                        'text': phrase,
                        'confidence': 0.7,
                        'explanation': 'Phrase courante'
                    })
        
        # Get suggestions from previous messages if database available
        if db:
            try:
                recent_messages = db.query(Message).filter(
                    Message.module_type == module_type,
                    Message.role == 'user'
                ).order_by(Message.created_at.desc()).limit(50).all()
                
                if recent_messages:
                    # Find similar contexts
                    similar_contexts = []
                    for msg in recent_messages:
                        msg_words = msg.content.split()
                        if len(msg_words) >= 2:
                            msg_context = ' '.join(msg_words[:5])
                            if context.lower() in msg_context.lower() or msg_context.lower() in context.lower():
                                # Get next word from message
                                if len(msg_words) > len(words):
                                    next_word = msg_words[len(words)]
                                    similar_contexts.append(next_word)
                    
                    # Count most common next words
                    if similar_contexts:
                        word_counts = Counter(similar_contexts)
                        for word, count in word_counts.most_common(3):
                            suggestions.append({
                                'type': 'completion',
                                'text': word,
                                'confidence': min(0.5 + (count / 10), 0.9),
                                'explanation': f'Basé sur {count} contexte(s) similaire(s)'
                            })
            except Exception as e:
                logger.error(f"Error getting suggestions from database: {e}")
        
        return suggestions[:5]  # Return top 5
    
    def get_reformulation_suggestions(self, text: str) -> List[Dict]:
        """
        Get reformulation style suggestions
        
        Args:
            text: Current text
        
        Returns:
            List of reformulation suggestions
        """
        suggestions = []
        
        if len(text) < 10:
            return suggestions
        
        # Academic style suggestions
        academic_phrases = [
            'Il est important de noter que',
            'Il convient de souligner que',
            'Il faut remarquer que',
            'Il est essentiel de',
            'Il est nécessaire de',
            'On peut observer que',
            'Il est intéressant de constater que',
        ]
        
        # Check if text could benefit from academic phrasing
        if not any(phrase in text for phrase in academic_phrases):
            suggestions.append({
                'type': 'reformulation',
                'text': 'Il est important de noter que',
                'confidence': 0.6,
                'explanation': 'Suggestion de style académique'
            })
        
        return suggestions[:2]
    
    def get_smart_suggestions(
        self,
        text: str,
        cursor_position: int,
        module_type: str = 'general',
        db: Session = None
    ) -> List[Dict]:
        """
        Get all types of suggestions combined
        
        Args:
            text: Current text
            cursor_position: Cursor position
            module_type: Type of module
            db: Database session
        
        Returns:
            Combined list of suggestions
        """
        all_suggestions = []
        
        try:
            # Validate inputs
            if not text or not isinstance(text, str):
                return []
            
            # Normalize text
            text = ''.join(c for c in text if c.isprintable() or c.isspace())
            
            # Ensure cursor_position is valid
            if not isinstance(cursor_position, int):
                cursor_position = len(text)
            cursor_position = max(0, min(cursor_position, len(text)))
            
            # Grammar suggestions
            try:
                grammar_suggestions = self.get_grammar_suggestions(text, cursor_position)
                all_suggestions.extend(grammar_suggestions)
            except Exception as e:
                logger.error(f"Error getting grammar suggestions: {e}")
            
            # Completion suggestions
            try:
                completion_suggestions = self.get_completion_suggestions(text, module_type, db)
                all_suggestions.extend(completion_suggestions)
            except Exception as e:
                logger.error(f"Error getting completion suggestions: {e}")
            
            # Reformulation suggestions (only if reformulation module)
            if module_type == 'reformulation':
                try:
                    reformulation_suggestions = self.get_reformulation_suggestions(text)
                    all_suggestions.extend(reformulation_suggestions)
                except Exception as e:
                    logger.error(f"Error getting reformulation suggestions: {e}")
            
            # Sort by confidence and remove duplicates
            seen_texts = set()
            unique_suggestions = []
            for suggestion in sorted(all_suggestions, key=lambda x: x.get('confidence', 0), reverse=True):
                text_key = suggestion.get('text', '')
                if text_key and text_key not in seen_texts:
                    seen_texts.add(text_key)
                    unique_suggestions.append(suggestion)
            
            return unique_suggestions[:5]  # Return top 5
        except Exception as e:
            logger.error(f"Error in get_smart_suggestions: {e}", exc_info=e)
            return []
    
    def get_semantic_suggestions(
        self,
        text: str,
        module_type: str,
        db: Session = None
    ) -> List[Dict]:
        """
        Get semantic suggestions using embeddings
        
        Args:
            text: Current text
            module_type: Type of module
            db: Database session
        
        Returns:
            List of semantic suggestions
        """
        if not self.embedding_model or not db:
            return []
        
        try:
            # Validate input
            if not text or not isinstance(text, str) or len(text.strip()) < 5:
                return []
            
            # Normalize text
            text = ''.join(c for c in text if c.isprintable() or c.isspace())
            
            # Get recent similar messages with error handling
            try:
                recent_messages = db.query(Message).filter(
                    Message.module_type == module_type,
                    Message.role == 'user'
                ).order_by(Message.created_at.desc()).limit(100).all()
            except Exception as e:
                logger.error(f"Error querying messages for semantic suggestions: {e}")
                return []
            
            if not recent_messages:
                return []
            
            # Encode current text
            try:
                text_embedding = self.embedding_model.encode([text])[0]
            except Exception as e:
                logger.error(f"Error encoding text for semantic suggestions: {e}")
                return []
            
            # Find similar messages
            similar_messages = []
            import numpy as np
            try:
                for msg in recent_messages:
                    if not msg.content or len(msg.content) < 10:
                        continue
                    
                    try:
                        # Normalize message content
                        msg_content = ''.join(c for c in msg.content if c.isprintable() or c.isspace())
                        if len(msg_content) < 10:
                            continue
                        
                        msg_embedding = self.embedding_model.encode([msg_content])[0]
                        
                        # Calculate cosine similarity
                        similarity = np.dot(text_embedding, msg_embedding) / (
                            np.linalg.norm(text_embedding) * np.linalg.norm(msg_embedding)
                        )
                        
                        if similarity > 0.7:  # High similarity threshold
                            # Extract next words from similar message
                            msg_words = msg_content.split()
                            text_words = text.split()
                            
                            if len(msg_words) > len(text_words):
                                next_words = ' '.join(msg_words[len(text_words):len(text_words)+3])
                                similar_messages.append({
                                    'text': next_words,
                                    'similarity': float(similarity),
                                    'source': msg_content[:50] + '...'
                                })
                    except Exception as e:
                        logger.debug(f"Error processing message for semantic suggestions: {e}")
                        continue
            except Exception as e:
                logger.error(f"Error in semantic suggestions loop: {e}", exc_info=e)
                return []
            
            # Return top suggestions
            similar_messages.sort(key=lambda x: x['similarity'], reverse=True)
            suggestions = []
            for msg in similar_messages[:3]:
                suggestions.append({
                    'type': 'semantic',
                    'text': msg['text'],
                    'confidence': msg['similarity'],
                    'explanation': 'Basé sur un contexte similaire'
                })
            
            return suggestions
        
        except Exception as e:
            logger.error(f"Error getting semantic suggestions: {e}")
            return []

