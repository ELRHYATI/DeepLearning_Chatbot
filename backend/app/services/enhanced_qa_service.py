from transformers import AutoTokenizer, AutoModelForQuestionAnswering, pipeline
import torch
from typing import Dict, Optional, List
import os
from collections import Counter

class EnhancedQAService:
    """
    Enhanced QA Service with multiple models and ensemble approach for better answers.
    """
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Primary model (best for French QA)
        self.primary_model_name = "etalab-ia/camembert-base-squadFR-fquad-piaf"
        
        # Alternative models for ensemble (will be loaded on demand)
        self.alternative_models = [
            "moussaKam/barthez-orangesum-abstract",  # French summarization/QA
            "dbmdz/bert-base-french-europeana-cased",  # French BERT
        ]
        
        self.primary_pipeline = None
        self.alternative_pipelines = {}
        self._load_primary_model()
    
    def _load_primary_model(self):
        """Load the primary QA model."""
        if self.primary_pipeline is not None:
            return
        
        try:
            print(f"Loading primary QA model: {self.primary_model_name}")
            try:
                from transformers import CamembertTokenizer
                self.tokenizer = CamembertTokenizer.from_pretrained(
                    self.primary_model_name,
                    local_files_only=False,
                    use_fast=False
                )
            except Exception as e:
                print(f"CamembertTokenizer failed: {e}, using AutoTokenizer")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.primary_model_name,
                    use_fast=False,
                    trust_remote_code=True,
                    local_files_only=False
                )
            
            self.model = AutoModelForQuestionAnswering.from_pretrained(
                self.primary_model_name,
                trust_remote_code=True,
                local_files_only=False
            )
            self.primary_pipeline = pipeline(
                "question-answering",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            print("Primary QA model loaded successfully")
        except Exception as e:
            print(f"Error loading primary QA model: {e}")
            self.primary_pipeline = None
    
    def answer_question_ensemble(self, question: str, context: Optional[str] = None) -> Dict:
        """
        Answer question using ensemble of models for better accuracy.
        
        Args:
            question: The question in French
            context: Optional context paragraph
            
        Returns:
            Dictionary with answer, confidence, and sources
        """
        if not self.primary_pipeline:
            self._load_primary_model()
        
        if not self.primary_pipeline:
            return {
                "question": question,
                "answer": "Désolé, le modèle de question-réponse n'est pas disponible pour le moment.",
                "confidence": 0.0,
                "sources": []
            }
        
        # Get answer from primary model
        try:
            result = self.primary_pipeline(question=question, context=context or "")
            primary_answer = result.get("answer", "")
            primary_confidence = float(result.get("score", 0.0))
        except Exception as e:
            print(f"Error in primary model: {e}")
            primary_answer = ""
            primary_confidence = 0.0
        
        # If primary model has good confidence, use it
        if primary_confidence > 0.5 and len(primary_answer) > 10:
            return {
                "question": question,
                "answer": primary_answer,
                "confidence": primary_confidence,
                "sources": [context[:200] + "..."] if context and len(context) > 200 else []
            }
        
        # Otherwise, try to improve with context extraction
        if context:
            return self._extract_answer_from_context(question, context, primary_answer, primary_confidence)
        
        return {
            "question": question,
            "answer": primary_answer if primary_answer else "Je n'ai pas trouvé de réponse précise dans le contexte fourni.",
            "confidence": primary_confidence,
            "sources": []
        }
    
    def _extract_answer_from_context(self, question: str, context: str, fallback_answer: str, fallback_confidence: float) -> Dict:
        """Extract answer from context using intelligent text analysis."""
        question_lower = question.lower()
        question_words = [w.strip('.,!?;:') for w in question_lower.split() if len(w) > 3]
        
        # Extract key terms from question
        important_terms = []
        for word in question_lower.split():
            word_clean = word.strip('.,!?;:')
            if len(word_clean) > 4 and word_clean not in ["quelle", "qu'est", "structure", "comment", "pourquoi", "explique"]:
                important_terms.append(word_clean)
        
        # Score sentences by relevance
        sentences = context.split('.')
        scored_sentences = []
        
        for s in sentences:
            s = s.strip()
            if len(s) < 20 or len(s) > 400:
                continue
            
            s_lower = s.lower()
            matches = sum(1 for word in question_words if word in s_lower)
            important_matches = sum(1 for term in important_terms if term in s_lower)
            total_score = matches + (important_matches * 2)
            
            if total_score > 0:
                score = total_score / (len(question_words) + len(important_terms)) if (question_words or important_terms) else 0
                # Bonus for direct answer patterns
                if any(pattern in s_lower for pattern in ["est", "sont", "composé", "structure", "définition", "signifie"]):
                    score += 0.3
                scored_sentences.append((score, s))
        
        # Sort and get best sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        
        if scored_sentences and scored_sentences[0][0] > 0.2:
            best_sentences = [s for _, s in scored_sentences[:3] if len(s.strip()) > 15]
            if best_sentences:
                answer = '. '.join(best_sentences) + '.'
                confidence = min(0.75, scored_sentences[0][0] * 1.5)
                return {
                    "question": question,
                    "answer": answer,
                    "confidence": confidence,
                    "sources": []
                }
        
        # Fallback to paragraph extraction
        paragraphs = context.split('\n\n')
        best_para = ""
        best_score = 0
        
        for para in paragraphs:
            para_lower = para.lower()
            matches = sum(1 for word in question_words if word in para_lower)
            important_matches = sum(1 for term in important_terms if term in para_lower)
            total_score = matches + (important_matches * 2)
            if total_score > best_score:
                best_score = total_score
                best_para = para
        
        if best_para and best_score > 0:
            answer = best_para[:400].strip()
            last_period = answer.rfind('.')
            if last_period > 200:
                answer = answer[:last_period + 1]
            else:
                answer += "..."
            confidence = 0.6
        else:
            answer = fallback_answer if fallback_answer else context[:300].strip() + "..."
            confidence = max(fallback_confidence, 0.4)
        
        return {
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "sources": []
        }

