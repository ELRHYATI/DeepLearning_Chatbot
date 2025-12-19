"""
Unit tests for EnhancedQAService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.enhanced_qa_service import EnhancedQAService


@pytest.mark.unit
class TestEnhancedQAService:
    """Test suite for EnhancedQAService"""
    
    def test_enhanced_qa_service_initialization(self):
        """Test that EnhancedQAService can be initialized"""
        with patch('app.services.enhanced_qa_service.AutoTokenizer') as mock_tokenizer, \
             patch('app.services.enhanced_qa_service.AutoModelForQuestionAnswering') as mock_model, \
             patch('app.services.enhanced_qa_service.pipeline') as mock_pipeline:
            
            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            mock_pipeline.return_value = Mock()
            
            service = EnhancedQAService()
            assert service is not None
            assert service.device in ["cuda", "cpu"]
    
    def test_answer_question_ensemble_without_model(self):
        """Test answer_question_ensemble when model is not loaded"""
        # Create a service instance and manually set pipeline to None to simulate no model
        service = EnhancedQAService.__new__(EnhancedQAService)
        service.primary_pipeline = None
        service.device = "cpu"
        service.alternative_pipelines = {}
        
        result = service.answer_question_ensemble("Test question", "Test context")
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert "confidence" in result
        assert "sources" in result
        # When model is not available, should return error message
        assert result["confidence"] == 0.0
        assert "n'est pas disponible" in result["answer"]
    
    @patch('app.services.enhanced_qa_service.AutoTokenizer')
    @patch('app.services.enhanced_qa_service.AutoModelForQuestionAnswering')
    @patch('app.services.enhanced_qa_service.pipeline')
    def test_answer_question_ensemble_with_model(self, mock_pipeline, mock_model, mock_tokenizer):
        """Test answer_question_ensemble with loaded model"""
        # Setup mocks
        mock_tokenizer_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = {
            "answer": "Test answer",
            "score": 0.85
        }
        mock_pipeline.return_value = mock_pipeline_instance
        
        service = EnhancedQAService()
        
        # Test with good confidence
        result = service.answer_question_ensemble(
            "Qu'est-ce que la photosynthèse?",
            "La photosynthèse est le processus par lequel les plantes produisent de l'énergie."
        )
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert "confidence" in result
        assert result["confidence"] > 0
    
    @patch('app.services.enhanced_qa_service.AutoTokenizer')
    @patch('app.services.enhanced_qa_service.AutoModelForQuestionAnswering')
    @patch('app.services.enhanced_qa_service.pipeline')
    def test_answer_question_ensemble_low_confidence(self, mock_pipeline, mock_model, mock_tokenizer):
        """Test answer_question_ensemble with low confidence"""
        # Setup mocks
        mock_tokenizer_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = {
            "answer": "Short",
            "score": 0.3  # Low confidence
        }
        mock_pipeline.return_value = mock_pipeline_instance
        
        service = EnhancedQAService()
        
        context = "La photosynthèse est un processus complexe qui se produit dans les plantes."
        result = service.answer_question_ensemble(
            "Qu'est-ce que la photosynthèse?",
            context
        )
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert "confidence" in result
        # Should use context extraction for low confidence
        assert len(result["answer"]) > 0
    
    @patch('app.services.enhanced_qa_service.AutoTokenizer')
    @patch('app.services.enhanced_qa_service.AutoModelForQuestionAnswering')
    @patch('app.services.enhanced_qa_service.pipeline')
    def test_answer_question_ensemble_without_context(self, mock_pipeline, mock_model, mock_tokenizer):
        """Test answer_question_ensemble without context"""
        # Setup mocks
        mock_tokenizer_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = {
            "answer": "Test answer",
            "score": 0.4
        }
        mock_pipeline.return_value = mock_pipeline_instance
        
        service = EnhancedQAService()
        
        result = service.answer_question_ensemble("Test question", None)
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert "confidence" in result
    
    @patch('app.services.enhanced_qa_service.AutoTokenizer')
    @patch('app.services.enhanced_qa_service.AutoModelForQuestionAnswering')
    @patch('app.services.enhanced_qa_service.pipeline')
    def test_answer_question_ensemble_model_error(self, mock_pipeline, mock_model, mock_tokenizer):
        """Test answer_question_ensemble when model raises an error"""
        # Setup mocks
        mock_tokenizer_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.side_effect = Exception("Model error")
        mock_pipeline.return_value = mock_pipeline_instance
        
        service = EnhancedQAService()
        
        result = service.answer_question_ensemble(
            "Test question",
            "Test context"
        )
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert "confidence" in result
        # When model error occurs, should use context extraction or return fallback
        # Confidence might be 0.0 or a value from context extraction
        assert isinstance(result["confidence"], (int, float))
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_extract_answer_from_context(self):
        """Test _extract_answer_from_context method"""
        service = EnhancedQAService()
        
        question = "Qu'est-ce que la photosynthèse?"
        context = """
        La photosynthèse est le processus par lequel les plantes utilisent la lumière du soleil,
        l'eau et le dioxyde de carbone pour produire de l'oxygène et de l'énergie sous forme de glucose.
        Ce processus est essentiel pour la vie sur Terre.
        """
        
        result = service._extract_answer_from_context(
            question,
            context,
            "Fallback answer",
            0.3
        )
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert "confidence" in result
        assert len(result["answer"]) > 0
        assert result["confidence"] > 0
    
    def test_extract_answer_from_context_no_matches(self):
        """Test _extract_answer_from_context with no matching sentences"""
        service = EnhancedQAService()
        
        question = "Qu'est-ce que XYZ?"
        context = "This is completely unrelated text that doesn't match the question at all."
        
        result = service._extract_answer_from_context(
            question,
            context,
            "Fallback answer",
            0.2
        )
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert "confidence" in result
        # Should use fallback or context
        assert len(result["answer"]) > 0

