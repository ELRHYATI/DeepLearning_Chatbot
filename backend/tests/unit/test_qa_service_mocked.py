"""
Unit tests for QAService with mocks to improve coverage without loading models
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.qa_service import QAService


@pytest.mark.unit
class TestQAServiceMocked:
    """Test suite for QAService with mocked models"""
    
    @patch('app.services.qa_service.AutoModelForQuestionAnswering')
    @patch('app.services.qa_service.AutoTokenizer')
    @patch('app.services.qa_service.pipeline')
    def test_answer_question_with_mock(self, mock_pipeline, mock_tokenizer, mock_model):
        """Test answering question with mocked pipeline"""
        # Setup mock
        mock_qa_result = {
            "answer": "L'ADN est une molécule",
            "score": 0.85
        }
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.return_value = [mock_qa_result]
        mock_pipeline.return_value = mock_pipeline_instance
        
        service = QAService()
        service.qa_pipeline = mock_pipeline_instance
        
        result = service.answer_question("Qu'est-ce que l'ADN?", "L'ADN est une molécule.")
        
        assert result["answer"] is not None
        assert result["confidence"] > 0
    
    def test_format_academic_answer_high_confidence(self):
        """Test formatting answer with high confidence"""
        service = QAService()
        service.qa_pipeline = None  # Don't load model
        
        formatted = service.format_academic_answer("Test answer", 0.85)
        
        assert "très élevée" in formatted
        assert "Test answer" in formatted
    
    def test_format_academic_answer_medium_confidence(self):
        """Test formatting answer with medium confidence"""
        service = QAService()
        service.qa_pipeline = None
        
        formatted = service.format_academic_answer("Test answer", 0.55)
        
        assert "élevée" in formatted or "modérée" in formatted
    
    def test_format_academic_answer_low_confidence(self):
        """Test formatting answer with low confidence"""
        service = QAService()
        service.qa_pipeline = None
        
        formatted = service.format_academic_answer("Test answer", 0.25)
        
        assert "modérée" in formatted or "faible" in formatted
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_service_initialization(self, mock_load):
        """Test service initialization"""
        service = QAService()
        assert service is not None
        assert service.model_name is not None

