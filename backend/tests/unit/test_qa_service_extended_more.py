"""
Extended unit tests for QA Service - More coverage
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.qa_service import QAService


@pytest.mark.unit
class TestQAServiceExtended:
    """Extended test suite for QA Service"""
    
    @patch('app.services.qa_service.AutoTokenizer')
    @patch('app.services.qa_service.AutoModelForQuestionAnswering')
    @patch('app.services.qa_service.pipeline')
    def test_qa_service_initialization(self, mock_pipeline, mock_model, mock_tokenizer):
        """Test QA service initialization"""
        mock_tokenizer.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = MagicMock()
        mock_pipeline.return_value = MagicMock()
        
        service = QAService()
        
        assert service.model_name is not None
        assert service.device in ["cuda", "cpu"]
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_answer_question_without_pipeline(self, mock_load):
        """Test answering question when pipeline is not available"""
        service = QAService()
        service.qa_pipeline = None
        
        result = service.answer_question("Test question")
        
        assert "answer" in result
        assert "confidence" in result
        assert result["confidence"] == 0.0
    
    def test_answer_question_context_building(self):
        """Test context building for questions"""
        service = QAService()
        service.qa_pipeline = None  # Skip model loading
        
        # Test that method handles different question types
        question = "Qu'est-ce que l'IA?"
        result = service.answer_question(question, context="Test context")
        
        assert isinstance(result, dict)
        assert "question" in result
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_answer_question_with_rag_context(self, mock_load):
        """Test answering with RAG context"""
        service = QAService()
        service.qa_pipeline = None
        
        result = service.answer_question(
            "Test question",
            context="This is RAG context"
        )
        
        assert isinstance(result, dict)
        assert result["question"] == "Test question"

