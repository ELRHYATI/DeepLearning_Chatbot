"""
Service for text summarization
Supports multiple summary lengths and styles
"""
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch
from typing import Dict, Optional
import os
import re
from app.services.semantic_validation_service import SemanticValidationService
from app.services.few_shot_service import FewShotLearningService
from app.services.adaptive_learning_service import AdaptiveLearningService

class SummarizationService:
    def __init__(self):
        # Primary model - upgraded to better model
        self.model_name = "moussaKam/barthez-orangesum-abstract"  # BART French - better quality than T5
        # Alternative models (fallback and ensemble)
        self.alternative_models = [
            "plguillou/t5-base-fr-sum-cnndm",  # T5 French as fallback
        ]
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.summarization_pipeline = None
        self.alternative_pipelines = {}
        self.use_ensemble = True  # Enable ensemble methods
        self.semantic_validator = SemanticValidationService()
        self.use_semantic_validation = True  # Enable semantic validation
        self.few_shot_service = FewShotLearningService()  # Few-shot learning service
        self.use_few_shot = True  # Enable few-shot learning
        self.adaptive_learning = AdaptiveLearningService()  # Adaptive learning service
        self.use_adaptive_learning = True  # Enable adaptive learning
        self._load_model()
    
    def _load_model(self):
        """Lazy load the model on first use"""
        if self.summarization_pipeline is not None:
            return
        
        try:
            print(f"Loading summarization model: {self.model_name}")
            # Ensure model_name is a string
            model_name_str = str(self.model_name) if self.model_name else "moussaKam/barthez-orangesum-abstract"
            
            # Check if it's a T5 model
            is_t5_model = "t5" in model_name_str.lower()
            
            if is_t5_model:
                # For T5 models, use T5Tokenizer
                from transformers import T5Tokenizer
                print("Using T5Tokenizer for T5 model")
                self.tokenizer = T5Tokenizer.from_pretrained(
                    model_name_str,
                    local_files_only=False
                )
            else:
                # For BART and other models, use AutoTokenizer
                print("Using AutoTokenizer for BART/other model")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name_str,
                    use_fast=False,
                    trust_remote_code=True,
                    local_files_only=False
                )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name_str,
                local_files_only=False
            )
            self.model.to(self.device)
            self.summarization_pipeline = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            print(f"Summarization model loaded successfully on {self.device}")
        except Exception as e:
            print(f"Error loading summarization model: {e}")
            self.summarization_pipeline = None
    
    def summarize_text(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 30,
        length_style: str = "medium",  # "short", "medium", "long", "detailed"
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Summarize text with different length options
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            length_style: Style of summary (short, medium, long, detailed)
        
        Returns:
            Dictionary with summary, original_length, summary_length, compression_ratio
        """
        if not text or len(text.strip()) < 50:
            return {
                "summary": text,
                "original_length": len(text),
                "summary_length": len(text),
                "compression_ratio": 1.0,
                "error": "Text too short to summarize (minimum 50 characters)"
            }
        
        # Adjust length based on style
        if length_style == "short":
            max_length = min(100, len(text.split()) // 4)
            min_length = 20
        elif length_style == "medium":
            max_length = min(150, len(text.split()) // 3)
            min_length = 30
        elif length_style == "long":
            max_length = min(250, len(text.split()) // 2)
            min_length = 50
        elif length_style == "detailed":
            max_length = min(400, len(text.split()) // 2)
            min_length = 80
        
        # Ensure reasonable limits
        max_length = max(50, min(max_length, 512))
        min_length = max(10, min(min_length, max_length - 20))
        
        if self.summarization_pipeline is None:
            return {
                "summary": text,
                "original_length": len(text),
                "summary_length": len(text),
                "compression_ratio": 1.0,
                "error": "Summarization model not available"
            }
        
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text(text)
            
            # Handle long texts by chunking
            if len(cleaned_text.split()) > 512:
                summary = self._summarize_long_text(cleaned_text, max_length, min_length)
            else:
                # Use ensemble method if enabled
                if self.use_ensemble:
                    summary = self._ensemble_summarize(cleaned_text, max_length, min_length)
                else:
                    # Optimized parameters for better summarization quality
                    result = self.summarization_pipeline(
                        cleaned_text,
                        max_length=max_length,
                        min_length=min_length,
                        do_sample=True,
                        num_beams=6,
                        early_stopping=True,
                        temperature=0.4,
                        top_p=0.90,
                        top_k=40,
                        repetition_penalty=1.3,
                        length_penalty=1.2,
                        no_repeat_ngram_size=3
                    )
                    summary = result[0]['summary_text'] if result else cleaned_text
            
            # Clean up summary
            summary = self._clean_summary(summary)
            
            # Semantic validation
            validation = None
            if self.use_semantic_validation:
                validation = self.semantic_validator.validate_summary(
                    text, summary, min_similarity=0.3, max_similarity=0.8
                )
                if not validation.get("valid", True):
                    # If validation fails, log warning but still return
                    print(f"Semantic validation warning: {validation.get('reason', 'Unknown issue')}")
            
            original_length = len(text)
            summary_length = len(summary)
            compression_ratio = summary_length / original_length if original_length > 0 else 1.0
            
            result_dict = {
                "summary": summary,
                "original_length": original_length,
                "summary_length": summary_length,
                "compression_ratio": compression_ratio,
                "length_style": length_style,
                "key_points": self._extract_key_points(text, summary),
                "validation": validation
            }
            
            # Record successful interaction for learning
            if self.use_adaptive_learning and user_id:
                # Only record if compression ratio is reasonable
                if 0.1 <= compression_ratio <= 0.8:
                    interaction_metadata = {
                        'length_style': length_style,
                        'original_length': original_length,
                        'summary_length': summary_length,
                        'compression_ratio': compression_ratio,
                        'generation_params': base_params if 'base_params' in locals() else {}
                    }
                    if metadata:
                        interaction_metadata.update(metadata)
                    
                    self.adaptive_learning.record_successful_interaction(
                        user_id=user_id,
                        task_type='summarization',
                        metadata=interaction_metadata
                    )
            
            return result_dict
        except Exception as e:
            print(f"Error in summarization: {e}")
            return {
                "summary": text,
                "original_length": len(text),
                "summary_length": len(text),
                "compression_ratio": 1.0,
                "error": str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean text before summarization"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might confuse the model
        text = text.strip()
        return text
    
    def _clean_summary(self, summary: str) -> str:
        """Clean summary output"""
        # Remove common artifacts
        summary = re.sub(r'^Résumé[:\s]*', '', summary, flags=re.IGNORECASE)
        summary = re.sub(r'^Summary[:\s]*', '', summary, flags=re.IGNORECASE)
        summary = summary.strip()
        return summary
    
    def _summarize_long_text(self, text: str, max_length: int, min_length: int) -> str:
        """Summarize long text by chunking"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            if current_length + sentence_length > 400:
                if current_chunk:
                    chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        summaries = []
        for chunk in chunks:
            try:
                result = self.summarization_pipeline(
                    chunk,
                    max_length=max_length // len(chunks) if len(chunks) > 1 else max_length,
                    min_length=min_length // len(chunks) if len(chunks) > 1 else min_length,
                    do_sample=False
                )
                if result:
                    summaries.append(result[0]['summary_text'])
            except Exception as e:
                print(f"Error summarizing chunk: {e}")
                summaries.append(chunk[:200] + "...")
        
        return ' '.join(summaries)
    
    def _extract_key_points(self, original: str, summary: str) -> list:
        """Extract key points from the summary"""
        # Simple extraction: split summary into sentences
        sentences = summary.split('. ')
        key_points = [s.strip() + '.' for s in sentences if len(s.strip()) > 20]
        return key_points[:5]  # Return top 5 key points
    
    def _ensemble_summarize(self, text: str, max_length: int, min_length: int) -> str:
        """
        Ensemble method: combine results from multiple models for better quality
        """
        results = []
        scores = []
        
        # Try primary model
        if self.summarization_pipeline:
            try:
                result = self.summarization_pipeline(
                    text,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=True,
                    num_beams=6,
                    early_stopping=True,
                    temperature=0.4,
                    top_p=0.90,
                    top_k=40,
                    repetition_penalty=1.3,
                    length_penalty=1.2,
                    no_repeat_ngram_size=3
                )
                if result and result[0].get('summary_text'):
                    summary = result[0]['summary_text']
                    score = self._score_summary(text, summary, max_length, min_length)
                    results.append(summary)
                    scores.append(score)
            except Exception as e:
                print(f"Error with primary model: {e}")
        
        # Try alternative models
        for alt_model_name in self.alternative_models:
            try:
                alt_pipeline = self._load_alternative_model(alt_model_name)
                if alt_pipeline:
                    result = alt_pipeline(
                        text,
                        max_length=max_length,
                        min_length=min_length,
                        do_sample=True,
                        num_beams=5,
                        early_stopping=True,
                        temperature=0.4,
                        repetition_penalty=1.2,
                        length_penalty=1.1
                    )
                    if result and result[0].get('summary_text'):
                        summary = result[0]['summary_text']
                        score = self._score_summary(text, summary, max_length, min_length)
                        results.append(summary)
                        scores.append(score)
            except Exception as e:
                print(f"Error with alternative model {alt_model_name}: {e}")
        
        # Select best result or combine
        if not results:
            return text
        
        if len(results) == 1:
            return results[0]
        
        # Use best scoring result, but also consider semantic validation
        if self.use_semantic_validation:
            # Re-score with semantic validation
            validated_scores = []
            for i, summary in enumerate(results):
                validation = self.semantic_validator.validate_summary(
                    text, summary, min_similarity=0.3, max_similarity=0.8
                )
                # Combine original score with validation score
                combined_score = scores[i] * 0.7 + (1.0 if validation.get("valid", True) else 0.3) * 0.3
                validated_scores.append(combined_score)
            best_idx = validated_scores.index(max(validated_scores))
        else:
            best_idx = scores.index(max(scores))
        
        return results[best_idx]
    
    def _load_alternative_model(self, model_name: str):
        """Load alternative model on demand"""
        if model_name in self.alternative_pipelines:
            return self.alternative_pipelines[model_name]
        
        try:
            from transformers import pipeline
            alt_pipeline = pipeline(
                "summarization",
                model=model_name,
                device=0 if self.device == "cuda" else -1
            )
            self.alternative_pipelines[model_name] = alt_pipeline
            return alt_pipeline
        except Exception as e:
            print(f"Could not load alternative model {model_name}: {e}")
            return None
    
    def _score_summary(self, original: str, summary: str, max_length: int, min_length: int) -> float:
        """Score a summary for quality"""
        if not summary or len(summary.strip()) < 10:
            return 0.0
        
        score = 0.5  # Base score
        
        # Length check
        summary_len = len(summary.split())
        if min_length <= summary_len <= max_length:
            score += 0.3
        elif min_length * 0.8 <= summary_len <= max_length * 1.2:
            score += 0.2
        
        # Compression ratio check
        orig_len = len(original.split())
        if orig_len > 0:
            ratio = summary_len / orig_len
            if 0.1 <= ratio <= 0.5:  # Good compression
                score += 0.2
        
        # Diversity check (should be different from original)
        if summary.lower() != original.lower():
            score += 0.1
        
        # Check for key information retention
        orig_words = set(original.lower().split())
        summary_words = set(summary.lower().split())
        overlap = len(orig_words.intersection(summary_words))
        if len(orig_words) > 0:
            retention = overlap / len(orig_words)
            if 0.3 <= retention <= 0.7:  # Good balance
                score += 0.1
        
        return min(1.0, score)

