"""
Service for detecting AI-generated text
"""
import re
from typing import Dict, List, Optional
import numpy as np
from collections import Counter

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

from app.utils.logger import get_logger

logger = get_logger()


class AIDetectionService:
    """Service for detecting AI-generated text"""
    
    def __init__(self):
        self.embedding_model = None
        self._load_embedding_model()
        
        # Features that indicate AI-generated text
        self.ai_indicators = {
            'perplexity_threshold': 15,  # Lower perplexity = more likely AI
            'burstiness_threshold': 0.5,  # Lower burstiness = more likely AI
            'repetition_threshold': 0.3,  # Higher repetition = more likely AI
        }
    
    def _load_embedding_model(self):
        """Load embedding model for text analysis"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(
                    'paraphrase-multilingual-MiniLM-L12-v2'
                )
                logger.info("AI detection embedding model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}")
                self.embedding_model = None
    
    def calculate_perplexity(self, text: str) -> float:
        """
        Calculate text perplexity (lower = more predictable = more likely AI)
        
        Args:
            text: Text to analyze
        
        Returns:
            Perplexity score
        """
        if not text or len(text.split()) < 5:
            return 0.0
        
        words = text.lower().split()
        word_counts = Counter(words)
        total_words = len(words)
        unique_words = len(word_counts)
        
        if unique_words == 0:
            return 0.0
        
        # Simple perplexity approximation
        # Higher diversity = higher perplexity = more human-like
        diversity = unique_words / total_words if total_words > 0 else 0
        
        # Calculate entropy
        entropy = 0.0
        for count in word_counts.values():
            probability = count / total_words
            if probability > 0:
                entropy -= probability * np.log2(probability)
        
        # Perplexity is 2^entropy
        perplexity = 2 ** entropy if entropy > 0 else 1.0
        
        return float(perplexity)
    
    def calculate_burstiness(self, text: str) -> float:
        """
        Calculate text burstiness (variation in sentence length)
        Lower burstiness = more uniform = more likely AI
        
        Args:
            text: Text to analyze
        
        Returns:
            Burstiness score (0-1)
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 2:
            return 0.5  # Neutral
        
        sentence_lengths = [len(s.split()) for s in sentences]
        
        if not sentence_lengths:
            return 0.5
        
        mean_length = np.mean(sentence_lengths)
        std_length = np.std(sentence_lengths) if len(sentence_lengths) > 1 else 0
        
        # Burstiness = coefficient of variation
        burstiness = std_length / mean_length if mean_length > 0 else 0
        
        # Normalize to 0-1 range
        normalized_burstiness = min(burstiness / 2.0, 1.0) if burstiness > 0 else 0
        
        return float(normalized_burstiness)
    
    def detect_repetition(self, text: str) -> float:
        """
        Detect repetitive patterns (AI text often has more repetition)
        
        Args:
            text: Text to analyze
        
        Returns:
            Repetition score (0-1)
        """
        words = text.lower().split()
        if len(words) < 10:
            return 0.0
        
        # Count n-gram repetitions
        bigrams = []
        for i in range(len(words) - 1):
            bigrams.append((words[i], words[i+1]))
        
        if not bigrams:
            return 0.0
        
        bigram_counts = Counter(bigrams)
        total_bigrams = len(bigrams)
        unique_bigrams = len(bigram_counts)
        
        # Repetition ratio
        repetition_ratio = 1 - (unique_bigrams / total_bigrams) if total_bigrams > 0 else 0
        
        return float(repetition_ratio)
    
    def detect_ai_patterns(self, text: str) -> Dict:
        """
        Detect common AI writing patterns
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with pattern detection results
        """
        patterns = {
            'excessive_formality': 0,
            'lack_of_contractions': 0,
            'overuse_of_transitions': 0,
            'generic_phrases': 0,
            'perfect_grammar': 0
        }
        
        text_lower = text.lower()
        
        # Excessive formality indicators
        formal_phrases = [
            'il est important de noter que',
            'il convient de souligner que',
            'il faut remarquer que',
            'il est essentiel de',
            'il est nécessaire de',
            'on peut observer que',
        ]
        formal_count = sum(1 for phrase in formal_phrases if phrase in text_lower)
        patterns['excessive_formality'] = min(formal_count / 3.0, 1.0)
        
        # Lack of contractions (AI often doesn't use contractions)
        contractions = ["c'est", "d'", "l'", "n'", "s'", "qu'", "j'"]
        contraction_count = sum(1 for c in contractions if c in text_lower)
        word_count = len(text.split())
        contraction_ratio = contraction_count / word_count if word_count > 0 else 0
        patterns['lack_of_contractions'] = max(0, 1 - (contraction_ratio * 10))
        
        # Overuse of transitions
        transitions = ['de plus', 'en outre', 'par ailleurs', 'en effet', 'ainsi', 'donc', 'par conséquent']
        transition_count = sum(1 for t in transitions if t in text_lower)
        patterns['overuse_of_transitions'] = min(transition_count / 5.0, 1.0)
        
        # Generic phrases
        generic_phrases = [
            'dans le monde',
            'de nos jours',
            'il est bien connu que',
            'comme on le sait',
        ]
        generic_count = sum(1 for phrase in generic_phrases if phrase in text_lower)
        patterns['generic_phrases'] = min(generic_count / 2.0, 1.0)
        
        # Perfect grammar (check for common mistakes that humans make)
        # This is a simplified check
        common_mistakes = ['a la', 'de le', 'a les']  # Should be "à la", "du", "aux"
        mistake_count = sum(1 for mistake in common_mistakes if mistake in text_lower)
        patterns['perfect_grammar'] = max(0, 1 - (mistake_count / 2.0))
        
        return patterns
    
    def detect_ai_text(
        self,
        text: str,
        include_details: bool = True
    ) -> Dict:
        """
        Detect if text is AI-generated
        
        Args:
            text: Text to analyze
            include_details: Whether to include detailed analysis
        
        Returns:
            Dictionary with AI detection results
        """
        if not text or len(text.strip()) < 20:
            return {
                'is_ai': False,
                'ai_probability': 0.0,
                'confidence': 0.0,
                'message': 'Texte trop court pour analyse'
            }
        
        # Calculate features
        perplexity = self.calculate_perplexity(text)
        burstiness = self.calculate_burstiness(text)
        repetition = self.detect_repetition(text)
        patterns = self.detect_ai_patterns(text)
        
        # Normalize perplexity (lower = more AI-like)
        # Typical human text: 20-50, AI text: 10-20
        normalized_perplexity = max(0, min(1, (20 - perplexity) / 20))
        
        # Combine features with weights
        ai_score = (
            normalized_perplexity * 0.3 +  # Lower perplexity = more AI
            (1 - burstiness) * 0.25 +      # Lower burstiness = more AI
            repetition * 0.2 +             # Higher repetition = more AI
            patterns['excessive_formality'] * 0.1 +
            patterns['lack_of_contractions'] * 0.1 +
            patterns['overuse_of_transitions'] * 0.05
        )
        
        # Clamp to 0-1
        ai_probability = max(0.0, min(1.0, ai_score))
        
        # Determine confidence
        feature_count = sum([
            perplexity > 0,
            burstiness > 0,
            repetition > 0,
            any(v > 0 for v in patterns.values())
        ])
        confidence = min(1.0, feature_count / 4.0)
        
        # Determine if AI
        is_ai = ai_probability > 0.6  # Threshold
        
        result = {
            'is_ai': is_ai,
            'ai_probability': round(ai_probability, 3),
            'confidence': round(confidence, 3),
            'message': self._get_ai_message(ai_probability, is_ai)
        }
        
        if include_details:
            result['details'] = {
                'perplexity': round(perplexity, 2),
                'burstiness': round(burstiness, 3),
                'repetition': round(repetition, 3),
                'patterns': patterns,
                'text_length': len(text),
                'word_count': len(text.split()),
                'sentence_count': len(re.split(r'[.!?]+', text))
            }
        
        return result
    
    def _get_ai_message(self, probability: float, is_ai: bool) -> str:
        """Get human-readable message based on AI probability"""
        if probability >= 0.8:
            return "Très probablement généré par IA"
        elif probability >= 0.6:
            return "Probablement généré par IA"
        elif probability >= 0.4:
            return "Possibilité de génération par IA"
        elif probability >= 0.2:
            return "Probablement écrit par un humain"
        else:
            return "Très probablement écrit par un humain"
    
    def combined_analysis(
        self,
        text: str,
        plagiarism_results: Optional[Dict] = None
    ) -> Dict:
        """
        Combined AI detection and plagiarism analysis
        
        Args:
            text: Text to analyze
            plagiarism_results: Optional plagiarism check results
        
        Returns:
            Combined analysis results
        """
        ai_results = self.detect_ai_text(text, include_details=True)
        
        result = {
            'ai_detection': ai_results,
            'plagiarism': plagiarism_results
        }
        
        # Overall assessment
        if ai_results['is_ai'] and plagiarism_results and plagiarism_results.get('plagiarism_detected'):
            result['overall_assessment'] = 'high_risk'
            result['overall_message'] = 'Texte probablement généré par IA avec similarités détectées'
        elif ai_results['is_ai']:
            result['overall_assessment'] = 'ai_detected'
            result['overall_message'] = 'Texte probablement généré par IA'
        elif plagiarism_results and plagiarism_results.get('plagiarism_detected'):
            result['overall_assessment'] = 'plagiarism_detected'
            result['overall_message'] = 'Similarités détectées avec d\'autres documents'
        else:
            result['overall_assessment'] = 'clean'
            result['overall_message'] = 'Texte semble original et humain'
        
        return result

