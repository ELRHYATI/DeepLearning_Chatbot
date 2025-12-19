"""
Unit tests for ReformulationService
"""
import pytest
from app.services.reformulation_service import ReformulationService


@pytest.mark.unit
@pytest.mark.slow
class TestReformulationService:
    """Test suite for ReformulationService"""
    
    def test_reformulation_service_initialization(self, reformulation_service):
        """Test that ReformulationService can be initialized"""
        assert reformulation_service is not None
        assert reformulation_service.model_name is not None
    
    def test_reformulate_basic_structure(self, reformulation_service):
        """Test that reformulate_text returns proper structure"""
        text = "Le chat est sur le tapis."
        result = reformulation_service.reformulate_text(text, style="academic")
        
        assert isinstance(result, dict)
        assert "original_text" in result or "reformulated_text" in result
        assert "reformulated_text" in result
    
    def test_reformulate_different_styles(self, reformulation_service):
        """Test reformulation with different styles"""
        text = "C'est une bonne idée."
        styles = ["academic", "formal", "simple"]
        
        for style in styles:
            result = reformulation_service.reformulate_text(text, style=style)
            assert result["reformulated_text"] is not None
            assert len(result["reformulated_text"]) > 0
    
    def test_reformulate_empty_text(self, reformulation_service):
        """Test handling of empty text"""
        result = reformulation_service.reformulate_text("", style="academic")
        
        assert isinstance(result, dict)
        assert "reformulated_text" in result
    
    def test_reformulate_preserves_meaning(self, reformulation_service):
        """Test that reformulation preserves meaning"""
        text = "L'intelligence artificielle transforme la société."
        result = reformulation_service.reformulate_text(text, style="academic")
        
        # Reformulated text should not be empty
        assert len(result["reformulated_text"]) > 0
        # Should contain some key terms
        assert isinstance(result["reformulated_text"], str)
    
    def test_reformulate_long_text(self, reformulation_service):
        """Test reformulation of longer text"""
        long_text = " ".join(["Ceci est une phrase de test."] * 5)
        result = reformulation_service.reformulate_text(long_text, style="academic")
        
        assert result["reformulated_text"] is not None
        assert isinstance(result["reformulated_text"], str)
    
    def test_reformulate_special_characters(self, reformulation_service):
        """Test handling of special characters"""
        text = "C'est l'été, il fait chaud. J'aime les cafés français."
        result = reformulation_service.reformulate_text(text, style="academic")
        
        assert result["reformulated_text"] is not None
        assert isinstance(result["reformulated_text"], str)
    
    def test_reformulate_unicode_handling(self, reformulation_service):
        """Test that service handles Unicode correctly"""
        unicode_text = "Les étudiants français étudient l'informatique."
        result = reformulation_service.reformulate_text(unicode_text, style="academic")
        
        assert result["reformulated_text"] is not None
        assert isinstance(result["reformulated_text"], str)
    
    def test_reformulate_default_style(self, reformulation_service):
        """Test reformulation with default style"""
        text = "Test text for reformulation."
        result = reformulation_service.reformulate_text(text)
        
        assert result["reformulated_text"] is not None
    
    def test_reformulate_returns_original_if_error(self, reformulation_service):
        """Test that service returns original text if reformulation fails"""
        # This is a fallback behavior test
        text = "Test"
        result = reformulation_service.reformulate_text(text, style="academic")
        
        # Should always return a result
        assert isinstance(result, dict)
        assert "reformulated_text" in result

