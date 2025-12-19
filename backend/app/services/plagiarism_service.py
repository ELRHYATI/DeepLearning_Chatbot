"""
Plagiarism detection service using text similarity analysis
"""
import re
from typing import Dict, List, Optional, Tuple
from collections import Counter
import hashlib
from difflib import SequenceMatcher
import numpy as np
from sqlalchemy.orm import Session

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

from app.models import Document, Message
from app.services.rag_service import RAGService
from app.utils.logger import get_logger

logger = get_logger()


class PlagiarismService:
    """Service for detecting plagiarism in documents"""
    
    def __init__(self):
        self.rag_service = RAGService()
        self.embedding_model = None
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load embedding model for semantic similarity"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(
                    'paraphrase-multilingual-MiniLM-L12-v2'
                )
                logger.info("Plagiarism embedding model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}")
                self.embedding_model = None
        else:
            logger.warning("Sentence transformers not available for plagiarism detection")
    
    def extract_ngrams(self, text: str, n: int = 3) -> List[str]:
        """Extract n-grams from text"""
        # Clean and normalize text
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        
        if len(words) < n:
            return [' '.join(words)]
        
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.append(ngram)
        
        return ngrams
    
    def calculate_ngram_similarity(self, text1: str, text2: str, n: int = 3) -> float:
        """Calculate similarity using n-gram overlap"""
        ngrams1 = set(self.extract_ngrams(text1, n))
        ngrams2 = set(self.extract_ngrams(text2, n))
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using embeddings"""
        if not self.embedding_model:
            return 0.0
        
        try:
            # Truncate if too long (embedding models have token limits)
            max_length = 512
            text1 = text1[:max_length] if len(text1) > max_length else text1
            text2 = text2[:max_length] if len(text2) > max_length else text2
            
            embeddings = self.embedding_model.encode([text1, text2])
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def find_similar_sections(
        self, 
        text: str, 
        reference_text: str, 
        min_length: int = 50
    ) -> List[Dict]:
        """Find similar sections between two texts"""
        similar_sections = []
        
        # Split into sentences
        sentences1 = re.split(r'[.!?]\s+', text)
        sentences2 = re.split(r'[.!?]\s+', reference_text)
        
        # Compare chunks of sentences
        chunk_size = 3
        for i in range(len(sentences1) - chunk_size + 1):
            chunk1 = ' '.join(sentences1[i:i+chunk_size])
            if len(chunk1) < min_length:
                continue
            
            best_match = None
            best_similarity = 0.0
            
            for j in range(len(sentences2) - chunk_size + 1):
                chunk2 = ' '.join(sentences2[j:j+chunk_size])
                if len(chunk2) < min_length:
                    continue
                
                # Calculate similarity
                similarity = SequenceMatcher(None, chunk1.lower(), chunk2.lower()).ratio()
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        'source_text': chunk1,
                        'reference_text': chunk2,
                        'similarity': similarity,
                        'source_start': i,
                        'reference_start': j
                    }
            
            if best_match and best_match['similarity'] > 0.6:  # Threshold
                similar_sections.append(best_match)
        
        return similar_sections
    
    def check_plagiarism(
        self,
        text: str,
        db: Session,
        user_id: Optional[int] = None,
        exclude_document_ids: Optional[List[int]] = None,
        min_similarity: float = 0.7
    ) -> Dict:
        """
        Check text for plagiarism against stored documents
        
        Args:
            text: Text to check
            db: Database session
            user_id: Optional user ID to filter documents
            exclude_document_ids: Document IDs to exclude from check
            min_similarity: Minimum similarity threshold (0-1)
        
        Returns:
            Dictionary with plagiarism analysis results
        """
        results = {
            'overall_similarity': 0.0,
            'plagiarism_detected': False,
            'matches': [],
            'total_documents_checked': 0,
            'similarity_breakdown': {
                'ngram_similarity': 0.0,
                'semantic_similarity': 0.0,
                'exact_matches': 0
            }
        }
        
        # Get documents to compare against
        query = db.query(Document).filter(Document.processed == True)
        
        if user_id:
            # Check against all documents (not just user's)
            # For academic integrity, we check against all documents
            pass
        
        if exclude_document_ids:
            query = query.filter(~Document.id.in_(exclude_document_ids))
        
        documents = query.all()
        results['total_documents_checked'] = len(documents)
        
        if not documents:
            return results
        
        all_matches = []
        max_similarity = 0.0
        
        # Process each document
        for doc in documents:
            try:
                # Extract text from document
                from app.services.document_processor import DocumentProcessor
                processor = DocumentProcessor()
                doc_text = processor.extract_text_from_document(doc.file_path, doc.file_type)
                
                if not doc_text or len(doc_text.strip()) < 50:
                    continue
                
                # Calculate similarities
                ngram_sim = self.calculate_ngram_similarity(text, doc_text, n=3)
                semantic_sim = self.calculate_semantic_similarity(text, doc_text)
                sequence_sim = SequenceMatcher(None, text.lower(), doc_text.lower()).ratio()
                
                # Combined similarity (weighted average)
                combined_similarity = (
                    ngram_sim * 0.4 +
                    semantic_sim * 0.4 +
                    sequence_sim * 0.2
                )
                
                if combined_similarity > max_similarity:
                    max_similarity = combined_similarity
                
                # Find similar sections if similarity is high enough
                if combined_similarity >= min_similarity:
                    similar_sections = self.find_similar_sections(text, doc_text)
                    
                    match = {
                        'document_id': doc.id,
                        'document_name': doc.filename,
                        'document_owner_id': doc.user_id,
                        'similarity': combined_similarity,
                        'ngram_similarity': ngram_sim,
                        'semantic_similarity': semantic_sim,
                        'sequence_similarity': sequence_sim,
                        'similar_sections': similar_sections[:5],  # Top 5 sections
                        'document_length': len(doc_text),
                        'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None
                    }
                    
                    all_matches.append(match)
                    
            except Exception as e:
                logger.error(f"Error checking document {doc.id}: {e}")
                continue
        
        # Sort matches by similarity (highest first)
        all_matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        results['matches'] = all_matches
        results['overall_similarity'] = max_similarity
        results['plagiarism_detected'] = max_similarity >= min_similarity
        
        # Calculate breakdown
        if all_matches:
            results['similarity_breakdown'] = {
                'ngram_similarity': sum(m['ngram_similarity'] for m in all_matches) / len(all_matches),
                'semantic_similarity': sum(m['semantic_similarity'] for m in all_matches) / len(all_matches),
                'exact_matches': len([m for m in all_matches if m['sequence_similarity'] > 0.95])
            }
        
        return results
    
    def check_document_plagiarism(
        self,
        document_id: int,
        db: Session,
        min_similarity: float = 0.7
    ) -> Dict:
        """
        Check a specific document for plagiarism
        
        Args:
            document_id: ID of document to check
            db: Database session
            min_similarity: Minimum similarity threshold
        
        Returns:
            Plagiarism analysis results
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Extract text from document
        from app.services.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        text = processor.extract_text_from_document(document.file_path, document.file_type)
        
        # Check against other documents (excluding itself)
        return self.check_plagiarism(
            text,
            db,
            exclude_document_ids=[document_id],
            min_similarity=min_similarity
        )
    
    def get_plagiarism_summary(self, results: Dict) -> Dict:
        """Get a summary of plagiarism results"""
        if not results['plagiarism_detected']:
            return {
                'status': 'clean',
                'message': 'Aucun plagiat détecté',
                'similarity_percentage': 0
            }
        
        max_similarity = results['overall_similarity']
        match_count = len(results['matches'])
        
        if max_similarity >= 0.9:
            status = 'high_risk'
            message = f'Risque élevé de plagiat détecté ({max_similarity*100:.1f}% de similarité)'
        elif max_similarity >= 0.7:
            status = 'medium_risk'
            message = f'Risque modéré de plagiat détecté ({max_similarity*100:.1f}% de similarité)'
        else:
            status = 'low_risk'
            message = f'Faible similarité détectée ({max_similarity*100:.1f}% de similarité)'
        
        return {
            'status': status,
            'message': message,
            'similarity_percentage': round(max_similarity * 100, 2),
            'match_count': match_count,
            'documents_checked': results['total_documents_checked']
        }

