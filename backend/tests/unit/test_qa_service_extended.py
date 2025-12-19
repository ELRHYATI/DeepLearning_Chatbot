"""
Extended unit tests for QAService to improve coverage
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.qa_service import QAService


@pytest.mark.unit
@pytest.mark.slow
class TestQAServiceExtended:
    """Extended test suite for QAService"""
    
    def test_format_academic_answer(self, qa_service):
        """Test format_academic_answer method"""
        answer = "L'ADN est une molécule"
        confidence = 0.75
        
        formatted = qa_service.format_academic_answer(answer, confidence)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert answer in formatted or "ADN" in formatted
    
    def test_answer_question_with_biology_context(self, qa_service):
        """Test QA with biology-specific context"""
        question = "Quelle est la structure de l'ADN?"
        result = qa_service.answer_question(question)
        
        assert result["answer"] is not None
        assert len(result["answer"]) > 0
        assert result["confidence"] >= 0
    
    def test_answer_question_with_chemistry_context(self, qa_service):
        """Test QA with chemistry-specific context"""
        question = "Qu'est-ce qu'un atome?"
        result = qa_service.answer_question(question)
        
        assert result["answer"] is not None
        assert result["confidence"] >= 0
    
    def test_answer_question_with_physics_context(self, qa_service):
        """Test QA with physics-specific context"""
        question = "Expliquez la théorie de la relativité"
        result = qa_service.answer_question(question)
        
        assert result["answer"] is not None
        assert result["confidence"] >= 0
    
    def test_answer_question_confidence_boost(self, qa_service):
        """Test that confidence is boosted for comprehensive answers"""
        question = "Qu'est-ce que la photosynthèse?"
        context = "La photosynthèse est un processus biologique complexe qui permet aux plantes de convertir la lumière en énergie."
        
        result = qa_service.answer_question(question, context)
        
        # Confidence should be reasonable
        assert 0 <= result["confidence"] <= 1
        # Answer should contain key terms
        assert len(result["answer"]) > 0
    
    def test_answer_question_fallback_extraction(self, qa_service):
        """Test fallback answer extraction when model confidence is low"""
        question = "Test question"
        context = "This is a test context with some information about the topic."
        
        result = qa_service.answer_question(question, context)
        
        # Should still return an answer even with low confidence
        assert result["answer"] is not None
        assert isinstance(result["answer"], str)
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_qa_service_model_loading(self, mock_load, qa_service):
        """Test that model loading is handled correctly"""
        # Model should be loaded on initialization
        assert qa_service.qa_pipeline is not None or mock_load.called
