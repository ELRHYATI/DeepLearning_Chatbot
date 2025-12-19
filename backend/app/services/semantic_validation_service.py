"""
Service for semantic validation of model outputs
Uses embeddings to validate quality and coherence
"""
import re
from typing import Dict, Optional, List, Tuple
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

from app.utils.logger import get_logger

logger = get_logger()


class SemanticValidationService:
    """Service for semantic validation using embeddings"""
    
    def __init__(self):
        self.embedding_model = None
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load embedding model for semantic validation"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use multilingual model for French
                self.embedding_model = SentenceTransformer(
                    'paraphrase-multilingual-MiniLM-L12-v2'
                )
                logger.info("Semantic validation embedding model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}")
                self.embedding_model = None
        else:
            logger.warning("sentence-transformers not available for semantic validation")
    
    def validate_summary(
        self,
        original: str,
        summary: str,
        min_similarity: float = 0.3,
        max_similarity: float = 0.8
    ) -> Dict:
        """
        Validate a summary using semantic similarity
        
        Args:
            original: Original text
            summary: Generated summary
            min_similarity: Minimum semantic similarity (too different = bad)
            max_similarity: Maximum semantic similarity (too similar = not summarized)
        
        Returns:
            Dictionary with validation results
        """
        if not self.embedding_model:
            return {
                "valid": True,
                "score": 0.5,
                "reason": "Embedding model not available"
            }
        
        try:
            # Calculate semantic similarity
            embeddings = self.embedding_model.encode([original, summary])
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            # Check if summary is too short
            if len(summary.split()) < 10:
                return {
                    "valid": False,
                    "score": similarity,
                    "reason": "Summary too short",
                    "similarity": float(similarity)
                }
            
            # Check similarity range
            if similarity < min_similarity:
                return {
                    "valid": False,
                    "score": similarity,
                    "reason": f"Summary too different from original (similarity: {similarity:.2f})",
                    "similarity": float(similarity)
                }
            
            if similarity > max_similarity:
                return {
                    "valid": False,
                    "score": similarity,
                    "reason": f"Summary too similar to original (not summarized enough, similarity: {similarity:.2f})",
                    "similarity": float(similarity)
                }
            
            return {
                "valid": True,
                "score": similarity,
                "reason": "Summary is semantically appropriate",
                "similarity": float(similarity)
            }
        except Exception as e:
            logger.error(f"Error in semantic validation: {e}")
            return {
                "valid": True,
                "score": 0.5,
                "reason": f"Validation error: {str(e)}"
            }
    
    def validate_reformulation(
        self,
        original: str,
        reformulated: str,
        style: str = "academic",
        min_diversity: float = 0.2
    ) -> Dict:
        """
        Validate a reformulation using semantic similarity
        
        Args:
            original: Original text
            reformulated: Reformulated text
            style: Style of reformulation
            min_diversity: Minimum semantic diversity (should be different)
        
        Returns:
            Dictionary with validation results
        """
        if not self.embedding_model:
            return {
                "valid": True,
                "score": 0.5,
                "reason": "Embedding model not available"
            }
        
        try:
            # Calculate semantic similarity
            embeddings = self.embedding_model.encode([original, reformulated])
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            diversity = 1.0 - similarity
            
            # Check if reformulated is too similar (not reformulated)
            if similarity > 0.95:
                return {
                    "valid": False,
                    "score": similarity,
                    "reason": "Reformulation too similar to original",
                    "similarity": float(similarity),
                    "diversity": float(diversity)
                }
            
            # Check minimum diversity
            if diversity < min_diversity:
                return {
                    "valid": False,
                    "score": similarity,
                    "reason": f"Reformulation lacks diversity (diversity: {diversity:.2f})",
                    "similarity": float(similarity),
                    "diversity": float(diversity)
                }
            
            # Style-specific validation
            if style == "academic":
                # Check for academic vocabulary
                academic_terms = ['analyse', 'étude', 'recherche', 'méthode', 'théorie', 'concept']
                has_academic = any(term in reformulated.lower() for term in academic_terms)
                if not has_academic and len(reformulated.split()) > 20:
                    return {
                        "valid": True,  # Still valid, but could be better
                        "score": similarity,
                        "reason": "Reformulation valid but could use more academic vocabulary",
                        "similarity": float(similarity),
                        "diversity": float(diversity),
                        "warning": True
                    }
            
            return {
                "valid": True,
                "score": similarity,
                "reason": "Reformulation is semantically appropriate",
                "similarity": float(similarity),
                "diversity": float(diversity)
            }
        except Exception as e:
            logger.error(f"Error in semantic validation: {e}")
            return {
                "valid": True,
                "score": 0.5,
                "reason": f"Validation error: {str(e)}"
            }
    
    def validate_answer(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
        min_relevance: float = 0.3
    ) -> Dict:
        """
        Validate an answer using semantic relevance to question
        
        Args:
            question: The question
            answer: Generated answer
            context: Optional context
            min_relevance: Minimum relevance to question
        
        Returns:
            Dictionary with validation results
        """
        if not self.embedding_model:
            return {
                "valid": True,
                "score": 0.5,
                "reason": "Embedding model not available"
            }
        
        try:
            # Calculate relevance to question
            embeddings = self.embedding_model.encode([question, answer])
            relevance = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            # Check minimum relevance
            if relevance < min_relevance:
                return {
                    "valid": False,
                    "score": relevance,
                    "reason": f"Answer not relevant to question (relevance: {relevance:.2f})",
                    "relevance": float(relevance)
                }
            
            # If context provided, check answer relevance to context
            if context:
                context_embedding = self.embedding_model.encode([context])[0]
                answer_embedding = embeddings[1]
                context_relevance = np.dot(context_embedding, answer_embedding) / (
                    np.linalg.norm(context_embedding) * np.linalg.norm(answer_embedding)
                )
                
                if context_relevance < 0.2:
                    return {
                        "valid": False,
                        "score": relevance,
                        "reason": f"Answer not based on context (context relevance: {context_relevance:.2f})",
                        "relevance": float(relevance),
                        "context_relevance": float(context_relevance)
                    }
            
            return {
                "valid": True,
                "score": relevance,
                "reason": "Answer is semantically relevant",
                "relevance": float(relevance)
            }
        except Exception as e:
            logger.error(f"Error in semantic validation: {e}")
            return {
                "valid": True,
                "score": 0.5,
                "reason": f"Validation error: {str(e)}"
            }
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        if not self.embedding_model:
            return 0.5
        
        try:
            embeddings = self.embedding_model.encode([text1, text2])
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.5

