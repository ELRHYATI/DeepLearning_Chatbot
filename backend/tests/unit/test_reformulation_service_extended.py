"""
Extended unit tests for Reformulation Service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.reformulation_service import ReformulationService


@pytest.mark.unit
class TestReformulationServiceExtended:
    """Extended test suite for Reformulation Service"""
    
    @patch('app.services.reformulation_service.AutoTokenizer')
    @patch('app.services.reformulation_service.AutoModelForSeq2SeqLM')
    @patch('app.services.reformulation_service.pipeline')
    def test_reformulation_service_initialization(self, mock_pipeline, mock_model, mock_tokenizer):
        """Test reformulation service initialization"""
        mock_tokenizer.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = MagicMock()
        mock_pipeline.return_value = MagicMock()
        
        service = ReformulationService()
        
        assert service.model_name is not None
        assert service.device in ["cuda", "cpu"]
    
    @patch('app.services.reformulation_service.ReformulationService._load_model')
    def test_reformulate_text_without_pipeline(self, mock_load):
        """Test reformulation when pipeline is not available"""
        service = ReformulationService()
        service.reformulation_pipeline = None
        
        result = service.reformulate_text("Test text", style="academic")
        
        assert isinstance(result, dict)
        assert "original_text" in result
        assert "reformulated_text" in result
    
    def test_reformulate_text_different_styles(self):
        """Test reformulation with different styles"""
        service = ReformulationService()
        service.reformulation_pipeline = None
        
        styles = ["academic", "formal", "simple", "paraphrase"]
        for style in styles:
            result = service.reformulate_text("Test text", style=style)
            assert isinstance(result, dict)
            assert "reformulated_text" in result

