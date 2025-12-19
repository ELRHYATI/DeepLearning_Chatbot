"""
Service for interactive learning from user corrections
"""
import json
import re
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import MessageCorrection, Message
from app.utils.logger import get_logger
from collections import Counter
from difflib import SequenceMatcher

logger = get_logger()


class LearningService:
    """Service to learn from user corrections and improve responses"""
    
    def __init__(self):
        self.pattern_cache: Dict[str, List[Dict]] = {}
        self.similarity_threshold = 0.7
    
    def extract_correction_patterns(
        self, 
        db: Session, 
        module_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Extract common patterns from corrections
        
        Args:
            db: Database session
            module_type: Filter by module type (grammar, qa, reformulation, general)
            limit: Maximum number of corrections to analyze
        
        Returns:
            List of correction patterns with frequencies
        """
        query = db.query(MessageCorrection).filter(
            MessageCorrection.is_used_for_learning == True
        )
        
        if module_type:
            query = query.join(Message).filter(Message.module_type == module_type)
        
        corrections = query.order_by(MessageCorrection.created_at.desc()).limit(limit).all()
        
        if not corrections:
            return []
        
        patterns = []
        for correction in corrections:
            # Calculate similarity between original and corrected
            similarity = SequenceMatcher(None, correction.original_content, correction.corrected_content).ratio()
            
            # Extract key differences
            differences = self._extract_differences(
                correction.original_content,
                correction.corrected_content
            )
            
            if differences:
                patterns.append({
                    'original': correction.original_content[:200],  # Truncate for storage
                    'corrected': correction.corrected_content[:200],
                    'module_type': correction.correction_type,
                    'differences': differences,
                    'similarity': similarity,
                    'frequency': 1
                })
        
        # Group similar patterns
        grouped_patterns = self._group_similar_patterns(patterns)
        
        return sorted(grouped_patterns, key=lambda x: x.get('frequency', 1), reverse=True)
    
    def _extract_differences(self, original: str, corrected: str) -> List[Dict]:
        """Extract key differences between original and corrected text"""
        matcher = SequenceMatcher(None, original, corrected)
        differences = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                differences.append({
                    'type': tag,  # replace, delete, insert
                    'original_text': original[i1:i2],
                    'corrected_text': corrected[j1:j2],
                    'position': i1
                })
        
        return differences
    
    def _group_similar_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Group similar correction patterns together"""
        if not patterns:
            return []
        
        grouped = []
        used = set()
        
        for i, pattern in enumerate(patterns):
            if i in used:
                continue
            
            group = [pattern]
            used.add(i)
            
            # Find similar patterns
            for j, other_pattern in enumerate(patterns[i+1:], start=i+1):
                if j in used:
                    continue
                
                similarity = SequenceMatcher(
                    None,
                    pattern['original'],
                    other_pattern['original']
                ).ratio()
                
                if similarity > self.similarity_threshold:
                    group.append(other_pattern)
                    used.add(j)
            
            # Merge group
            merged = {
                'original': pattern['original'],
                'corrected': pattern['corrected'],
                'module_type': pattern['module_type'],
                'differences': pattern['differences'],
                'frequency': len(group),
                'examples': [p['original'] for p in group[:3]]  # Keep first 3 examples
            }
            grouped.append(merged)
        
        return grouped
    
    def apply_learned_corrections(
        self,
        text: str,
        module_type: str,
        db: Session
    ) -> Tuple[str, List[Dict]]:
        """
        Apply learned corrections to improve text
        
        Args:
            text: Text to improve
            module_type: Type of module (grammar, qa, reformulation, general)
            db: Database session
        
        Returns:
            Tuple of (improved_text, applied_corrections)
        """
        patterns = self.extract_correction_patterns(db, module_type, limit=50)
        
        if not patterns:
            return text, []
        
        improved_text = text
        applied_corrections = []
        
        for pattern in patterns[:10]:  # Use top 10 patterns
            # Check if pattern matches current text
            similarity = SequenceMatcher(None, text.lower(), pattern['original'].lower()).ratio()
            
            if similarity > 0.6:  # If similar enough
                # Try to apply correction
                corrected = self._apply_pattern(text, pattern)
                if corrected != text:
                    improved_text = corrected
                    applied_corrections.append({
                        'pattern_id': pattern.get('id'),
                        'original_pattern': pattern['original'],
                        'correction_applied': True
                    })
        
        return improved_text, applied_corrections
    
    def _apply_pattern(self, text: str, pattern: Dict) -> str:
        """Apply a correction pattern to text"""
        # Simple pattern matching and replacement
        # This is a basic implementation - can be enhanced with ML
        
        original_lower = pattern['original'].lower()
        text_lower = text.lower()
        
        if original_lower in text_lower:
            # Find position
            pos = text_lower.find(original_lower)
            if pos != -1:
                # Replace with corrected version
                corrected = pattern['corrected']
                return text[:pos] + corrected + text[pos + len(pattern['original']):]
        
        return text
    
    def get_learning_statistics(self, db: Session, user_id: Optional[int] = None) -> Dict:
        """
        Get statistics about learning from corrections
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by user
        
        Returns:
            Dictionary with learning statistics
        """
        query = db.query(MessageCorrection).filter(
            MessageCorrection.is_used_for_learning == True
        )
        
        if user_id:
            query = query.filter(MessageCorrection.user_id == user_id)
        
        corrections = query.all()
        
        if not corrections:
            return {
                'total_corrections': 0,
                'corrections_by_type': {},
                'corrections_by_user': {},
                'improvement_rate': 0.0,
                'most_corrected_patterns': []
            }
        
        # Count by type
        type_counter = Counter(c.correction_type for c in corrections)
        
        # Count by user
        user_counter = Counter(c.user_id for c in corrections)
        
        # Calculate improvement rate (simplified - could be enhanced)
        # Improvement rate = percentage of corrections that significantly differ
        improved_count = sum(
            1 for c in corrections
            if SequenceMatcher(None, c.original_content, c.corrected_content).ratio() < 0.9
        )
        improvement_rate = (improved_count / len(corrections)) * 100 if corrections else 0
        
        # Get most common patterns
        patterns = self.extract_correction_patterns(db, limit=10)
        
        return {
            'total_corrections': len(corrections),
            'corrections_by_type': dict(type_counter),
            'corrections_by_user': {str(k): v for k, v in user_counter.items()},
            'improvement_rate': round(improvement_rate, 2),
            'most_corrected_patterns': patterns[:5]  # Top 5 patterns
        }
    
    def prepare_training_data(
        self,
        db: Session,
        module_type: str,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Prepare training data from corrections for fine-tuning
        
        Args:
            db: Database session
            module_type: Type of module to prepare data for
            limit: Maximum number of corrections to include
        
        Returns:
            List of training examples
        """
        corrections = db.query(MessageCorrection).join(Message).filter(
            MessageCorrection.is_used_for_learning == True,
            Message.module_type == module_type
        ).order_by(MessageCorrection.created_at.desc()).limit(limit).all()
        
        training_data = []
        
        for correction in corrections:
            # Get the original user message if available
            user_message = db.query(Message).filter(
                Message.session_id == correction.message.session_id,
                Message.role == 'user',
                Message.created_at < correction.message.created_at
            ).order_by(Message.created_at.desc()).first()
            
            if module_type == 'grammar':
                training_data.append({
                    'input': correction.original_content,
                    'output': correction.corrected_content,
                    'type': 'correction'
                })
            elif module_type == 'qa':
                if user_message:
                    training_data.append({
                        'question': user_message.content,
                        'context': '',  # Could be enhanced
                        'answer': correction.corrected_content,
                        'type': 'correction'
                    })
            elif module_type == 'reformulation':
                training_data.append({
                    'input': correction.original_content,
                    'output': correction.corrected_content,
                    'type': 'correction'
                })
        
        return training_data

