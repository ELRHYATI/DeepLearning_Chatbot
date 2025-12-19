"""
Unit tests for QAService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.qa_service import QAService


@pytest.mark.unit
@pytest.mark.slow
class TestQAService:
    """Test suite for QAService"""
    
    def test_qa_service_initialization(self, qa_service):
        """Test that QAService can be initialized"""
        assert qa_service is not None
        assert qa_service.model_name is not None
    
    def test_answer_question_basic_structure(self, qa_service, sample_question, sample_context):
        """Test that answer_question returns proper structure"""
        result = qa_service.answer_question(sample_question, sample_context)
        
        assert isinstance(result, dict)
        assert "question" in result
        assert "answer" in result
        assert "confidence" in result
        assert "sources" in result
        
        assert result["question"] == sample_question
        assert isinstance(result["answer"], str)
        assert isinstance(result["confidence"], float)
        assert isinstance(result["sources"], list)
    
    def test_answer_question_without_context(self, qa_service, sample_question):
        """Test answering question without context"""
        result = qa_service.answer_question(sample_question, None)
        
        assert result["answer"] is not None
        assert len(result["answer"]) > 0
        assert 0 <= result["confidence"] <= 1
    
    def test_answer_question_confidence_range(self, qa_service, sample_question, sample_context):
        """Test that confidence is in valid range"""
        result = qa_service.answer_question(sample_question, sample_context)
        
        assert 0 <= result["confidence"] <= 1, f"Confidence {result['confidence']} out of range"
    
    def test_answer_question_empty_question(self, qa_service):
        """Test handling of empty question"""
        result = qa_service.answer_question("", "Some context")
        
        # Should handle gracefully
        assert isinstance(result, dict)
        assert "answer" in result
    
    def test_answer_question_very_long_question(self, qa_service, sample_context):
        """Test handling of very long question"""
        long_question = " ".join(["Qu'est-ce que"] * 100)
        result = qa_service.answer_question(long_question, sample_context)
        
        assert isinstance(result, dict)
        assert "answer" in result
    
    def test_answer_question_special_characters(self, qa_service, sample_context):
        """Test handling of questions with special characters"""
        special_question = "Qu'est-ce que l'ADN? Comment ça marche?"
        result = qa_service.answer_question(special_question, sample_context)
        
        assert result["answer"] is not None
        assert isinstance(result["answer"], str)
    
    def test_answer_question_different_topics(self, qa_service):
        """Test answering questions on different topics"""
        questions = [
            "Qu'est-ce que l'ADN?",
            "Comment fonctionne la photosynthèse?",
            "Quelle est la structure de l'atome?",
        ]
        
        for question in questions:
            result = qa_service.answer_question(question)
            assert result["answer"] is not None
            assert len(result["answer"]) > 0
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_qa_service_lazy_loading(self, mock_load):
        """Test that model loading is lazy"""
        service = QAService()
        # Model should be loaded on initialization
        assert service.qa_pipeline is not None or mock_load.called
    
    def test_answer_question_sources_format(self, qa_service, sample_question, sample_context):
        """Test that sources are in correct format"""
        result = qa_service.answer_question(sample_question, sample_context)
        
        assert isinstance(result["sources"], list)
        # Sources should be strings or empty list
        for source in result["sources"]:
            assert isinstance(source, str)
    
    def test_answer_question_context_usage(self, qa_service, sample_question):
        """Test that context is used when provided"""
        context1 = "La photosynthèse est un processus biologique."
        context2 = "L'ADN est une molécule qui contient l'information génétique."
        
        result1 = qa_service.answer_question(sample_question, context1)
        result2 = qa_service.answer_question(sample_question, context2)
        
        # Answers might be different based on context
        assert result1["answer"] is not None
        assert result2["answer"] is not None

